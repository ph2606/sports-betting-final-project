"""Prevent correct-looking fixture IDs from settling different clubs/seasons."""
from datetime import datetime, timezone
import json
import math

import pandas as pd
import pytest

from epl_live import ledger
from epl_live.evaluate import score_forecasts, settle_from_snapshot


def forecast():
    return {"match_id": "fpl_2026-27_70", "home_team": "Tottenham Hotspur", "away_team": "Coventry City",
            "season": "2026-27", "kickoff_utc": "2026-10-19T19:00:00Z", "target_match_date": "2026-10-19",
            "model_id": "frozen_team", "model_sha256": "a" * 64, "code_sha256": "b" * 64,
            "protocol_sha256": "c" * 64, "created_at_utc": "2026-10-14T09:00:00Z",
            "source_snapshots": [{"sha256": "d" * 64, "observed_at_utc": "2026-10-14T08:59:00Z", "source": "test capture"}],
            "features": {"goal_diff": 0.5}, "latest_feature_match_dates": {"E0": "2026-10-12"},
            "probabilities": {"H": 0.6, "D": 0.2, "A": 0.2}, "forecast_type": "team_only"}


def outcome():
    return {"match_id": "fpl_2026-27_70", "home_team": "Tottenham Hotspur", "away_team": "Coventry City",
            "season": "2026-27", "kickoff_utc": "2026-10-19T19:00:00Z", "settled_at_utc": "2026-10-19T21:00:00Z",
            "result": "H", "home_goals": 2, "away_goals": 1}


@pytest.mark.parametrize("field,value", [("season", "2025-26"), ("home_team", "Arsenal"), ("away_team", "Chelsea")])
def test_correct_match_id_cannot_score_different_fixture_identity(field, value):
    wrong = outcome()
    wrong[field] = value
    with pytest.raises(ValueError, match="identity conflicts"):
        score_forecasts([forecast()], [wrong])


@pytest.mark.parametrize("field", ["season", "home_team", "away_team"])
def test_missing_outcome_identity_cannot_be_inferred_from_match_id(field):
    incomplete = outcome()
    incomplete.pop(field)
    with pytest.raises(ValueError, match="complete.*identity"):
        score_forecasts([forecast()], [incomplete])


def test_duplicate_outcomes_cannot_choose_settlement_by_last_row():
    first, second = outcome(), outcome()
    second.update(result="A", home_goals=1, away_goals=2)
    with pytest.raises(ValueError, match="Duplicate settlement"):
        score_forecasts([forecast()], [first, second])


def settlement_capture(tmp_path, monkeypatch, existing=None, *, finished=True):
    forecasts, outcomes = tmp_path / "forecasts.jsonl", tmp_path / "outcomes.jsonl"
    monkeypatch.setattr(ledger, "_utc_now", lambda: datetime(2026, 10, 14, 9, tzinfo=timezone.utc))
    ledger.append_forecasts(forecasts, [forecast()])
    monkeypatch.setattr(ledger, "_utc_now", lambda: datetime(2026, 10, 19, 22, tzinfo=timezone.utc))
    if existing is not None:
        ledger.append_outcomes(outcomes, [existing])
    snapshot = tmp_path / "snapshot"
    (snapshot / "normalized").mkdir(parents=True)
    (snapshot / "manifest.json").write_text(json.dumps({"membership_valid": True, "fpl_schedule_valid": True,
                                                       "snapshot_id": "test-settlement-capture"}))
    row = {**outcome(), "finished": finished, "observed_at_utc": "2026-10-19T21:00:00Z"}
    pd.DataFrame([row]).to_parquet(snapshot / "normalized" / "fixtures.parquet", index=False)
    return snapshot, forecasts, outcomes


@pytest.mark.parametrize("field,value", [("season", "2025-26"), ("home_team", "Arsenal"), ("away_team", "Chelsea")])
def test_existing_settlement_with_same_result_and_goals_cannot_keep_wrong_identity(tmp_path, monkeypatch, field, value):
    wrong = outcome()
    wrong[field] = value
    snapshot, forecasts, outcomes = settlement_capture(tmp_path, monkeypatch, wrong)
    before = (forecasts.read_bytes(), outcomes.read_bytes())
    with pytest.raises(ValueError, match="Existing settlement identity conflicts"):
        settle_from_snapshot(snapshot, forecasts, outcomes)
    assert (forecasts.read_bytes(), outcomes.read_bytes()) == before
    assert not ledger.ledger_lock_path(outcomes).exists()


def test_existing_identity_is_checked_even_without_new_finished_fixture(tmp_path, monkeypatch):
    wrong = outcome()
    wrong["home_team"] = "Arsenal"
    snapshot, forecasts, outcomes = settlement_capture(tmp_path, monkeypatch, wrong, finished=False)
    with pytest.raises(ValueError, match="Existing settlement identity conflicts"):
        settle_from_snapshot(snapshot, forecasts, outcomes)


def test_matching_identity_settles_once_without_touching_forecasts(tmp_path, monkeypatch):
    snapshot, forecasts, outcomes = settlement_capture(tmp_path, monkeypatch)
    before = forecasts.read_bytes()
    assert settle_from_snapshot(snapshot, forecasts, outcomes)["appended"] == 1
    settled = outcomes.read_bytes()
    assert settle_from_snapshot(snapshot, forecasts, outcomes)["appended"] == 0
    assert outcomes.read_bytes() == settled
    assert forecasts.read_bytes() == before
    predictions, metrics = score_forecasts(ledger.read_forecasts(forecasts), ledger.read_outcomes(outcomes))
    assert len(predictions) == 1
    assert metrics.iloc[0].log_loss == pytest.approx(-math.log(0.6))


def test_result_revision_still_fails_without_overwriting_settlement(tmp_path, monkeypatch):
    old = outcome()
    old.update(result="A", home_goals=1, away_goals=2)
    snapshot, forecasts, outcomes = settlement_capture(tmp_path, monkeypatch, old)
    before = outcomes.read_bytes()
    with pytest.raises(ValueError, match="settled result changed"):
        settle_from_snapshot(snapshot, forecasts, outcomes)
    assert outcomes.read_bytes() == before
