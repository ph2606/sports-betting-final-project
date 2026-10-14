"""Settle released forecasts from an immutable source capture and report scores."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

import numpy as np
import pandas as pd

from epl_modeling.experiment import save_table, write_json
from epl_modeling.metrics import CLASSES, classification_metrics, encode_results
from .features import read_table
from .ledger import append_outcomes, earliest_forecasts, read_forecasts, read_outcomes, verify_ledger
from .train import ROOT


def _fixture_identity(record, source):
    fields = ("season", "home_team", "away_team")
    if any(not isinstance(record.get(field), str) or not record[field].strip() for field in fields):
        raise ValueError(f"{source} requires complete season/home/away fixture identity")
    return tuple(record[field] for field in fields)


def _settlements_by_match(outcomes):
    settlement = {}
    for outcome in outcomes:
        key = outcome["match_id"]
        if key in settlement:
            raise ValueError("Duplicate settlement match identity; do not select a result by row order")
        settlement[key] = outcome
    return settlement


def settle_from_snapshot(snapshot, forecasts_path=ROOT / "forecasts.jsonl", outcomes_path=ROOT / "outcomes.jsonl"):
    snapshot = Path(snapshot)
    manifest = json.loads((snapshot / "manifest.json").read_text(encoding="utf-8"))
    if not manifest.get("membership_valid") or not manifest.get("fpl_schedule_valid"):
        raise ValueError("Settlement requires a verified current-league FPL fixture capture")
    forecasts = earliest_forecasts(read_forecasts(forecasts_path))
    identities = {}
    for forecast in forecasts:
        key = forecast["match_id"]
        identity = _fixture_identity(forecast, "Released forecast")
        if key in identities and identities[key] != identity:
            raise ValueError("Released forecasts disagree on fixture identity")
        identities[key] = identity
    existing = _settlements_by_match(read_outcomes(outcomes_path))
    for key, outcome in existing.items():
        if key in identities and _fixture_identity(outcome, "Existing settlement") != identities[key]:
            raise ValueError("Existing settlement identity conflicts with the forecast; preserve the ledger and investigate")
    records = []
    for fixture in read_table(snapshot, "fixtures").to_dict("records"):
        key = fixture["match_id"]
        if key not in identities or not fixture["finished"]:
            continue
        identity = _fixture_identity(fixture, "Settlement source")
        if identities[key] != identity:
            raise ValueError("Settlement source identity conflicts with the forecast")
        goals = np.array([fixture["home_goals"], fixture["away_goals"]], dtype=float)
        if not np.isfinite(goals).all() or (goals < 0).any() or not np.equal(goals, np.floor(goals)).all():
            raise ValueError("Finished source fixture has invalid goals")
        result = "H" if goals[0] > goals[1] else "A" if goals[0] < goals[1] else "D"
        if key in existing:
            old = existing[key]
            if old["result"] != result or old.get("home_goals") != int(goals[0]) or old.get("away_goals") != int(goals[1]):
                raise ValueError("A settled result changed; preserve and investigate the revision without overwriting the ledger")
            continue
        record = {"match_id": key, "season": fixture["season"], "home_team": fixture["home_team"],
                  "away_team": fixture["away_team"], "result": result,
                  "home_goals": int(goals[0]), "away_goals": int(goals[1]),
                  "kickoff_utc": str(fixture["kickoff_utc"]), "settled_at_utc": fixture["observed_at_utc"],
                  "snapshot_id": manifest["snapshot_id"],
                  "settlement_time_semantics": "UTC time the finished result was observed, not an inferred final-whistle time"}
        records.append(record)
    return append_outcomes(outcomes_path, records) if records else {"appended": 0, "total_records": len(existing)}


def score_forecasts(forecasts, outcomes):
    forecasts = earliest_forecasts(forecasts)
    settlement = _settlements_by_match(outcomes)
    rows = []
    for forecast in forecasts:
        if forecast["match_id"] not in settlement:
            continue
        outcome = settlement[forecast["match_id"]]
        if _fixture_identity(outcome, "Scoring settlement") != _fixture_identity(forecast, "Scored forecast"):
            raise ValueError("Scoring settlement identity conflicts with the forecast")
        if pd.Timestamp(outcome["settled_at_utc"]) < pd.Timestamp(forecast["kickoff_utc"]):
            raise ValueError("Observed settlement predates the forecasted kickoff")
        rows.append({"match_id": forecast["match_id"], "model_id": forecast["model_id"], "result": outcome["result"],
                     "feature_group": forecast.get("feature_group", "market_only"), "created_at_utc": forecast["created_at_utc"],
                     "kickoff_utc": forecast["kickoff_utc"], **{"p_"+label: forecast["probabilities"][label] for label in CLASSES}})
    predictions = pd.DataFrame(rows, columns=["match_id", "model_id", "result", "feature_group", "created_at_utc", "kickoff_utc", "p_H", "p_D", "p_A"])
    metrics = []
    for model_id, group in predictions.groupby("model_id"):
        metrics.append({"model_id": model_id, "scope": "available_released_forecasts",
                        **classification_metrics(encode_results(group.result), group[["p_H", "p_D", "p_A"]])})
    return predictions, pd.DataFrame(metrics, columns=["model_id", "scope", "n_matches", "accuracy", "classwise_ece_10", "classwise_ece_5", "classwise_ece_15", "log_loss", "brier_score"])


def evaluate(snapshot, forecasts_path=ROOT / "forecasts.jsonl", outcomes_path=ROOT / "outcomes.jsonl"):
    settlement = settle_from_snapshot(snapshot, forecasts_path, outcomes_path)
    forecasts = read_forecasts(forecasts_path)
    outcomes = read_outcomes(outcomes_path)
    predictions, scores = score_forecasts(forecasts, outcomes)
    now = datetime.now(timezone.utc)
    output = ROOT / "evaluations" / now.strftime("%Y%m%dT%H%M%S.%fZ")
    output.mkdir(parents=True, exist_ok=False)
    save_table(predictions, output, "resolved_predictions")
    save_table(scores, output, "prospective_scores")
    summary = {"evaluated_at_utc": now.isoformat(), "forecast_records": len(forecasts),
               "settled_fixtures": len(outcomes), "resolved_prediction_count": len(predictions),
               "pending_forecast_count": len(earliest_forecasts(forecasts)) - len(predictions),
               "outcomes_append": settlement, "prospective_performance_available": bool(len(predictions)),
               "scope": "Model-specific available forecasts; no common-population superiority claim",
               "no_observed_outcomes_is_not_zero_error_or_zero_profit": True}
    if Path(forecasts_path).exists():
        summary["forecast_ledger"] = verify_ledger(forecasts_path, "forecast")
    if Path(outcomes_path).exists():
        summary["outcome_ledger"] = verify_ledger(outcomes_path, "outcome")
    write_json(output / "evaluation_summary.json", summary)
    status = "No released forecast has a resolved outcome. No prospective accuracy, loss or profit is reported." if not len(predictions) else "Scores describe the released records resolved so far; differing model populations are not a fair superiority comparison."
    (output / "STATUS.md").write_text("# Prospective evaluation status\n\n" + status + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, required=True)
    args = parser.parse_args()
    evaluate(args.snapshot)


if __name__ == "__main__":
    main()
