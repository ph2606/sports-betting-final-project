"""Check that independent reconciliation rejects corrupted score exports."""
import json
from pathlib import Path

import pandas as pd
import pytest

from epl_live.ledger import append_outcomes, read_forecasts, read_outcomes
from epl_prospective.analysis import build_analysis
from epl_prospective.audit import audit_export
from epl_prospective.build import original_ledger_bytes

ROOT = Path(__file__).resolve().parents[2]
CAPTURE = ROOT / "epl_live/snapshots/20261020T223027.384077Z_34ff62be24"


@pytest.fixture
def completed_export(tmp_path):
    original = original_ledger_bytes()
    for name in ("original_forecast_ledger", "forecast_ledger_as_of"):
        (tmp_path / (name + ".jsonl")).write_bytes(original)
    forecasts = read_forecasts(tmp_path / "original_forecast_ledger.jsonl")
    ids = {r["match_id"] for r in forecasts}
    fixture = pd.read_parquet(CAPTURE / "normalized/fixtures.parquet")
    outcomes = []
    for row in fixture.loc[fixture.match_id.isin(ids)].to_dict("records"):
        h, a = int(row["home_goals"]), int(row["away_goals"])
        outcomes.append({key: row[key] for key in ("match_id", "season", "home_team", "away_team", "kickoff_utc")} | {
            "home_goals": h, "away_goals": a, "result": "H" if h > a else "A" if h < a else "D",
            "settled_at_utc": row["observed_at_utc"], "snapshot_id": CAPTURE.name})
    append_outcomes(tmp_path / "outcome_ledger_as_of.jsonl", outcomes)
    tables = build_analysis(forecasts, read_outcomes(tmp_path / "outcome_ledger_as_of.jsonl"),
        original_match_ids=ids, original_model_ids={r["model_id"] for r in forecasts})
    for name in ("forecast_outcome_audit", "fixture_outcomes"):
        tables[name]["result"] = tables[name].actual_result
        tables[name]["settled_at_utc"] = tables[name].outcome_observed_at_utc
    tables["next_forecasts"] = pd.DataFrame(columns=["match_id", "model_id", "status"])
    tables["source_freshness"] = pd.DataFrame({"source_capture_valid": [True]*6})
    for name, table in tables.items(): table.to_parquet(tmp_path / (name + ".parquet"), index=False)
    (tmp_path / "prospective_status.json").write_text(json.dumps({"resolved_original_forecasts": 40,
        "pending_original_forecasts": 0, "new_pending_forecasts": 0, "recorded_trade_count": 0,
        "prospective_betting_performance_available": False, "prospective_roi": None}))
    return tmp_path


def test_audit_reconciles_ten_real_fixture_outcomes_with_committed_probabilities(completed_export):
    result = audit_export(completed_export)
    assert result["status"] == "passed"
    assert result["original_forecasts_checked"] == 40
    assert result["independent_original_fixtures"] == 10


@pytest.mark.parametrize("problem", ["released_probability", "individual_loss", "model_denominator", "paired_denominator", "invented_roi", "fixture_goals"])
def test_audit_rejects_forecast_score_denominator_and_trading_corruption(completed_export, problem):
    folder = completed_export
    if problem == "invented_roi":
        path = folder / "prospective_status.json"
        value = json.loads(path.read_text()); value["prospective_roi"] = .05
        path.write_text(json.dumps(value))
    else:
        name, column, change = {
            "released_probability": ("forecast_outcome_audit", "p_H", .01),
            "individual_loss": ("forecast_outcome_audit", "log_loss", .1),
            "model_denominator": ("model_scores", "n_matches", 30),
            "paired_denominator": ("pairwise_scores", "common_fixture_count", 30),
            "fixture_goals": ("fixture_outcomes", "home_goals", 1),
        }[problem]
        path = folder / (name + ".parquet")
        table = pd.read_parquet(path); table.loc[0, column] += change
        table.to_parquet(path, index=False)
    with pytest.raises(AssertionError): audit_export(folder)
