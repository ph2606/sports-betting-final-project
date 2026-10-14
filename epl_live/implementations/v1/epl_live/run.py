"""One manual source-capture and auditable forecast-release cycle."""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import subprocess

import joblib
import numpy as np
import pandas as pd

from epl_modeling.ablation import logits
from epl_modeling.experiment import save_table, write_json
from epl_modeling.metrics import CLASSES
from .collect import collect_snapshot
from .features import build_live_features, read_table
from .ledger import append_forecasts, read_forecasts, verify_ledger
from .train import fit_candidates, sha256, ROOT, PROJECT, PROTOCOL

OPERATIONAL_PROTOCOL = ROOT / "OPERATIONAL_PROTOCOL.md"


def _json_number(value):
    return float(value) if pd.notna(value) and np.isfinite(value) else None


def _protocol_commit_time():
    result = subprocess.run(["git", "-C", str(PROJECT), "log", "-1", "--format=%cI", "--", "epl_modeling/PROSPECTIVE_PROTOCOL.md"],
                            capture_output=True, text=True, check=True)
    return pd.Timestamp(result.stdout.strip()).tz_convert("UTC").isoformat()


def _source_references(snapshot, manifest, model_dir):
    rows = []
    for request in manifest.get("requests", []):
        if request.get("status") != "downloaded":
            continue
        if str(request.get("source_key", "")).startswith("fpl_element_"):
            continue
        rows.append({"source": request.get("url") or request.get("source_key"),
                     "sha256": request["sha256"], "observed_at_utc": request["response_observed_at_utc"],
                     "publication_time_verified": False})
    rows.append({"source": "Immutable snapshot manifest including each player-history response hash and capture clock",
                 "sha256": sha256(snapshot / "manifest.json"),
                 "observed_at_utc": manifest["manifest_written_at_utc"], "publication_time_verified": False})
    historical_sha = sha256(PROJECT / "epl_modeling/ablation_results/modeling_matches.parquet")
    rows.append({"source": "Frozen historical feature table and archived source provenance",
                 "sha256": historical_sha, "observed_at_utc": datetime.now(timezone.utc).isoformat(), "publication_time_verified": False})
    model_sha = sha256(model_dir / "manifest.json")
    rows.append({"source": "Frozen model manifest", "sha256": model_sha,
                 "observed_at_utc": datetime.now(timezone.utc).isoformat(), "publication_time_verified": False})
    for name in ("fixtures", "player_history", "understat_matches", "individual_odds"):
        path = snapshot / "normalized" / (name + ".parquet")
        if path.exists():
            digest = sha256(path)
            rows.append({"source": "Normalized snapshot table: " + name, "sha256": digest,
                         "observed_at_utc": datetime.now(timezone.utc).isoformat(), "publication_time_verified": False})
    return rows


def run_cycle(snapshot=None, *, lookahead_days=7):
    if lookahead_days <= 0:
        raise ValueError("lookahead_days must be positive")
    model_dir = fit_candidates()
    snapshot = Path(snapshot).resolve() if snapshot else collect_snapshot(ROOT / "snapshots", include_players=True)
    manifest = json.loads((snapshot / "manifest.json").read_text(encoding="utf-8"))
    model_manifest = json.loads((model_dir / "manifest.json").read_text(encoding="utf-8"))
    fixtures = read_table(snapshot, "upcoming_targets")
    now = datetime.now(timezone.utc)
    if len(fixtures):
        kickoff = pd.to_datetime(fixtures.kickoff_utc, utc=True)
        fixtures = fixtures.loc[kickoff.gt(now) & kickoff.le(now + timedelta(days=lookahead_days))].copy()
        fixtures["match_date"] = pd.to_datetime(fixtures.match_date).dt.normalize()
    # A capture/run report is new, and an existing run report is never replaced.
    run_id = now.strftime("%Y%m%dT%H%M%S.%fZ")
    output = ROOT / "runs" / run_id
    output.mkdir(parents=True, exist_ok=False)
    coverage, records = [], []
    gates = []
    if not manifest.get("usable", False):
        gates.append("snapshot_membership_season_or_core_source_validation_failed")
    if not manifest.get("fpl_player_summaries_complete", False):
        gates.append("current_player_summary_registry_incomplete")
    feature_metadata = {}
    features = pd.DataFrame()
    if not gates and len(fixtures):
        try:
            features, feature_metadata = build_live_features(PROJECT / "epl_data", snapshot, fixtures)
            if feature_metadata["past_due_unfinished_fpl_fixtures"]:
                gates.append("past_due_unfinished_fixtures_require_source_quality_resolution")
        except (ValueError, KeyError) as error:
            gates.append("feature_snapshot_validation_failed")
            feature_metadata["feature_build_error"] = str(error)
    references = _source_references(snapshot, manifest, model_dir)
    code_files = [Path(__file__), ROOT / "features.py", ROOT / "ledger.py", ROOT / "collect.py", ROOT / "train.py"]
    code_files += [PROJECT / "epl_modeling" / name for name in
                   ("features.py", "fpl_reconciliation.py", "ablation.py", "market_residual.py", "metrics.py")]
    code_sha = hashlib.sha256(json.dumps({str(p.relative_to(PROJECT)): sha256(p) for p in code_files}, sort_keys=True).encode()).hexdigest()
    quote_table = read_table(snapshot, "individual_odds")
    quoted = quote_table.loc[quote_table.source_prefix.eq("B365")].copy() if len(quote_table) else pd.DataFrame()
    if len(quoted) and quoted.match_id.duplicated().any():
        raise ValueError("Ambiguous contemporaneous reference triplets")
    quotes = {row["match_id"]: row for row in quoted.to_dict("records")}
    protocol_commit = _protocol_commit_time()
    already = {(record["model_id"], record["match_id"]) for record in read_forecasts(ROOT / "forecasts.jsonl")}
    for target in fixtures.to_dict("records"):
        target_frame = features.loc[features.match_id.eq(target["match_id"])] if len(features) else pd.DataFrame()
        quote_row = quotes.get(target["match_id"])
        quote = None
        if quote_row:
            age = (pd.Timestamp(datetime.now(timezone.utc)) - pd.Timestamp(quote_row["observed_at_utc"])).total_seconds()
            if 0 <= age <= 3600:
                quote = {"bookmaker": "Bet365", "odds": {label: float(quote_row["odds_"+label]) for label in CLASSES},
                         "observed_at_utc": quote_row["observed_at_utc"], "publication_time_verified": False}
        for item in model_manifest["models"]:
            reason = ";".join(gates)
            if not reason and item["model_type"] == "market_residual" and quote is None:
                reason = "no_complete_recently_observed_bet365_triplet"
            if not reason and (item["model_id"], target["match_id"]) in already:
                reason = "earliest_forecast_already_released"
            if reason:
                coverage.append({"match_id": target["match_id"], "model_id": item["model_id"], "status": "withheld", "reason": reason})
                continue
            bundle = joblib.load(model_dir / item["file"])
            model_input = target_frame.copy()
            if quote:
                inverse = np.array([1 / quote["odds"][label] for label in CLASSES])
                for index, label in enumerate(CLASSES):
                    model_input["ref_p_" + label] = inverse[index] / inverse.sum()
            probabilities = bundle["calibrator"].predict_proba(logits(bundle["model"], bundle["model_type"], model_input, bundle["features"]))[0]
            creation = datetime.now(timezone.utc).isoformat()
            record = {"match_id": target["match_id"], "fpl_fixture_id": target["fpl_fixture_id"],
                      "home_team": target["home_team"], "away_team": target["away_team"], "season": target["season"],
                      "kickoff_utc": str(target["kickoff_utc"]), "target_match_date": target["match_date"].strftime("%Y-%m-%d"),
                      "model_id": item["model_id"], "model_sha256": item["sha256"], "code_sha256": code_sha,
                      "protocol_sha256": model_manifest["protocol_sha256"], "protocol_committed_at_utc": protocol_commit,
                      "operational_protocol_sha256": sha256(OPERATIONAL_PROTOCOL), "created_at_utc": creation,
                      "source_snapshots": references, "features": {name: _json_number(model_input.iloc[0][name]) for name in bundle["features"]},
                      "probabilities": {label: float(probabilities[index]) for index, label in enumerate(CLASSES)},
                      "latest_feature_match_dates": {name: pd.Timestamp(model_input.iloc[0][name]).strftime("%Y-%m-%d") if pd.notna(model_input.iloc[0][name]) else None
                                                     for name in model_input if name.startswith("audit_") and name.endswith("_date")},
                      "forecast_type": "market_residual" if item["model_type"] == "market_residual" else "team_only",
                      "feature_group": item["feature_group"], "market_quote": quote, "snapshot_id": manifest["snapshot_id"],
                      "data_quality": feature_metadata, "update_version": 1}
            records.append(record)
            coverage.append({"match_id": target["match_id"], "model_id": item["model_id"], "status": "prepared", "reason": ""})
        for baseline in ("raw", "temperature"):
            model_id = "prospective_v1_market_" + baseline
            reason = ";".join(gates)
            if not reason and quote is None:
                reason = "no_complete_recently_observed_bet365_triplet"
            if not reason and (model_id, target["match_id"]) in already:
                reason = "earliest_forecast_already_released"
            if reason:
                coverage.append({"match_id": target["match_id"], "model_id": model_id, "status": "withheld", "reason": reason})
                continue
            inverse = np.array([1 / quote["odds"][label] for label in CLASSES])
            probabilities = inverse / inverse.sum()
            definition = {"method": "proportional_de_vig_complete_Bet365_triplet", "classes": list(CLASSES)}
            model_sha = hashlib.sha256(json.dumps(definition, sort_keys=True).encode()).hexdigest()
            if baseline == "temperature":
                calibrator = joblib.load(model_dir / "market_temperature.joblib")
                probabilities = calibrator.predict_proba(np.log(probabilities[None, :]))[0]
                model_sha = model_manifest["market_temperature_sha256"]
            records.append({"match_id": target["match_id"], "fpl_fixture_id": target["fpl_fixture_id"],
                            "home_team": target["home_team"], "away_team": target["away_team"], "season": target["season"],
                            "kickoff_utc": str(target["kickoff_utc"]), "target_match_date": target["match_date"].strftime("%Y-%m-%d"),
                            "model_id": model_id, "model_sha256": model_sha, "code_sha256": code_sha,
                            "protocol_sha256": model_manifest["protocol_sha256"], "protocol_committed_at_utc": protocol_commit,
                            "operational_protocol_sha256": sha256(OPERATIONAL_PROTOCOL), "created_at_utc": datetime.now(timezone.utc).isoformat(),
                            "source_snapshots": references, "features": {}, "latest_feature_match_dates": {},
                            "probabilities": {label: float(probabilities[index]) for index, label in enumerate(CLASSES)},
                            "forecast_type": "market_baseline", "feature_group": "market_only", "market_quote": quote,
                            "model_definition": definition, "snapshot_id": manifest["snapshot_id"], "update_version": 1})
            coverage.append({"match_id": target["match_id"], "model_id": model_id, "status": "prepared", "reason": ""})
    if records:
        appended = append_forecasts(ROOT / "forecasts.jsonl", records)
    else:
        appended = {"appended": 0, "skipped_duplicates": 0, "total_records": len(read_forecasts(ROOT / "forecasts.jsonl"))}
    coverage_frame = pd.DataFrame(coverage, columns=["match_id", "model_id", "status", "reason"])
    save_table(coverage_frame, output, "forecast_coverage")
    save_table(fixtures, output, "target_fixtures")
    summary = {"run_id": run_id, "run_date": "2026-10-14", "snapshot_id": manifest["snapshot_id"],
               "snapshot_path": str(snapshot.relative_to(PROJECT)), "models_path": str(model_dir.relative_to(PROJECT)),
               "created_at_utc": datetime.now(timezone.utc).isoformat(), "lookahead_days": lookahead_days,
               "target_fixture_count": len(fixtures), "source_gates": gates, "feature_metadata": feature_metadata,
               "ledger_append": appended, "source_capture_usable": manifest.get("usable", False),
               "source_errors": manifest.get("errors", []), "freshness": manifest.get("freshness", {}),
               "observed_reference_quote_matches": len(quotes), "provider_price_publication_times_verified": False,
               "prospective_outcomes_observed": 0, "forecasts_not_live_execution_claims": True}
    if (ROOT / "forecasts.jsonl").exists():
        summary["ledger_integrity"] = verify_ledger(ROOT / "forecasts.jsonl", "forecast")
    write_json(output / "run_summary.json", summary)
    lines = ["# Forecast release status", "", "Run date: October 14, 2026.", "",
             f"Future fixtures within seven days: **{len(fixtures)}**. Newly appended forecasts: **{appended['appended']}**.", "",
             "Source gates: " + (", ".join(gates) if gates else "passed"), "",
             "All captured sources and exclusions are archived. A recent retrieval is not proof of a recent provider update or executable price. "
             "There are no resolved prospective games in this release, so no prospective accuracy, loss or profit estimate is reported.", "",
             "Inspect `run_summary.json`, `forecast_coverage.csv`, the source manifest and the independently committed forecast ledger.", ""]
    (output / "STATUS.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, help="Use a previously captured immutable snapshot; never pretend its observation time is new")
    parser.add_argument("--lookahead-days", type=int, default=7)
    args = parser.parse_args()
    run_cycle(args.snapshot, lookahead_days=args.lookahead_days)


if __name__ == "__main__":
    main()
