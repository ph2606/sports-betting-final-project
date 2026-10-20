from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import pandas as pd
import pytest

from epl_live import collect, ledger
from epl_prospective import settlement


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


@pytest.fixture
def capture(tmp_path, monkeypatch):
    root = tmp_path / "project"
    membership_path = root / "epl_data/metadata/current_teams.csv"
    membership_path.parent.mkdir(parents=True)
    expected = pd.read_csv(settlement.PROJECT / "epl_data/metadata/current_teams.csv")
    expected.to_csv(membership_path, index=False)
    teams = [{"id": int(row.fpl_team_id), "code": int(row.fpl_team_code), "name": row.fpl_name} for row in expected.itertuples(index=False)]
    home, away = expected.iloc[0], expected.iloc[1]
    bootstrap = {"teams": teams, "events": [{"deadline_time": "2026-08-21T17:00:00Z"}, {"deadline_time": "2027-05-30T13:00:00Z"}],
                 "elements": [{"id": 1, "team": int(home.fpl_team_id), "element_type": 2}]}
    native = [{"id": 64, "team_h": int(home.fpl_team_id), "team_a": int(away.fpl_team_id),
               "kickoff_time": "2026-10-17T14:00:00Z", "finished": True, "started": True,
               "team_h_score": 2, "team_a_score": 1, "minutes": 90}]
    snapshot = root / "epl_live/snapshots/capture"
    snapshot.mkdir(parents=True)
    manifest = {"snapshot_id": "capture", "season": "2026-27", "snapshot_started_at_utc": "2026-10-20T12:00:00Z",
        "snapshot_completed_at_utc": "2026-10-20T12:00:03Z", "manifest_written_at_utc": "2026-10-20T12:00:04Z",
        "membership_valid": True, "fpl_schedule_valid": True, "usable": True,
        "expected_membership_reference": {"sha256": digest(membership_path)}, "current_clubs": sorted(expected.team), "requests": []}
    contents = {"fpl_bootstrap": json.dumps(bootstrap).encode(), "fpl_fixtures": json.dumps(native).encode(),
        "football_data_e0": f"Div,Date,HomeTeam,AwayTeam,FTHG,FTAG,FTR\nE0,17/10/2026,{home.team},{away.team},2,1,H\n".encode()}
    for key, content in contents.items():
        relative, url = settlement.REQUIRED_REQUESTS[key]
        target = snapshot / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        manifest["requests"].append({"source_key": key, "path": relative, "url": url,
            "request_started_at_utc": "2026-10-20T12:00:01Z", "request_completed_at_utc": "2026-10-20T12:00:02Z",
            "response_observed_at_utc": "2026-10-20T12:00:02Z", "status": "downloaded", "http_status": 200,
            "sha256": digest(target), "bytes": len(content)})
    names = {int(row.fpl_team_id): row.team for row in expected.itertuples(index=False)}
    normalized = collect._fixtures_table(native, names, "2026-10-20T12:00:02Z", pd.Timestamp("2026-10-20T12:00:03Z"))
    (snapshot / "normalized").mkdir()
    normalized.to_parquet(snapshot / "normalized/fixtures.parquet", index=False)
    write_json(snapshot / "manifest.json", manifest)
    forecast = {"match_id": "fpl_2026-27_64", "home_team": home.team, "away_team": away.team, "season": "2026-27",
        "kickoff_utc": "2026-10-17T14:00:00Z", "model_id": "frozen_logistic_team", "model_sha256": "a" * 64,
        "code_sha256": "b" * 64, "protocol_sha256": "c" * 64, "created_at_utc": "2026-10-14T09:00:00Z",
        "source_snapshots": [{"sha256": "d" * 64, "source": "initial_capture", "observed_at_utc": "2026-10-14T08:59:00Z"}],
        "features": {}, "probabilities": {"H": .6, "D": .2, "A": .2}, "forecast_type": "team_only",
        "target_match_date": "2026-10-17", "latest_feature_match_dates": {}}
    forecasts_path = root / "epl_live/forecasts.jsonl"
    monkeypatch.setattr(ledger, "_utc_now", lambda: datetime(2026, 10, 14, 9, tzinfo=timezone.utc))
    ledger.append_forecasts(forecasts_path, [forecast])
    return {"root": root, "snapshot": snapshot, "manifest": manifest, "raw": native, "names": names,
            "forecast": forecast, "forecasts": forecasts_path, "outcomes": root / "epl_live/outcomes.jsonl"}


def save_manifest(capture):
    write_json(capture["snapshot"] / "manifest.json", capture["manifest"])


def replace_source(capture, key, content, *, normalize=False):
    request = next(row for row in capture["manifest"]["requests"] if row["source_key"] == key)
    path = capture["snapshot"] / request["path"]
    path.write_bytes(content)
    request.update(sha256=digest(path), bytes=path.stat().st_size)
    save_manifest(capture)
    if normalize:
        raw = json.loads((capture["snapshot"] / "raw/fpl/fixtures.json").read_bytes())
        frame = collect._fixtures_table(raw, capture["names"], "2026-10-20T12:00:02Z", pd.Timestamp("2026-10-20T12:00:03Z"))
        frame.to_parquet(capture["snapshot"] / "normalized/fixtures.parquet", index=False)


def test_validated_preflight_is_read_only_and_prices_remain_unavailable(capture):
    before = {p: digest(p) for p in capture["root"].rglob("*") if p.is_file()}
    audit = settlement.validate_snapshot_for_settlement(capture["snapshot"], root=capture["root"])
    assert audit["status"] == "passed" and audit["crosschecked_finished_fixtures"] == 1
    assert audit["preflight_resolved_prediction_count"] == 1 and audit["preflight_pending_prediction_count"] == 0
    assert len(audit["proposed_outcomes"]) == 1
    assert audit["proposed_outcomes"][0]["settled_at_utc"] == "2026-10-20T12:00:02Z"
    assert audit["result_crosschecks"][0]["source_agreement"] is True
    assert audit["quote_covered_prediction_records"] == 0 and audit["prospective_trading_performance_available"] is False
    assert audit["preflight_scores"][0]["log_loss"] == pytest.approx(-__import__("math").log(.6))
    json.dumps(audit, allow_nan=False)
    assert not capture["outcomes"].exists()
    assert before == {p: digest(p) for p in capture["root"].rglob("*") if p.is_file()}


@pytest.mark.parametrize("problem", ["raw_hash", "escaped_path", "http_failure", "clock", "membership", "duplicate_request",
                                    "normalized_score", "truthy_finished", "native_id", "fd_score", "fd_result", "fd_missing"])
def test_altered_or_inconsistent_evidence_is_rejected_before_any_settlement(capture, problem):
    path = capture["snapshot"]
    if problem == "raw_hash": (path / "raw/fpl/fixtures.json").write_bytes(b"[]")
    elif problem == "escaped_path": capture["manifest"]["requests"][0]["path"] = "../../outside.json"; save_manifest(capture)
    elif problem == "http_failure": capture["manifest"]["requests"][0]["http_status"] = 500; save_manifest(capture)
    elif problem == "clock": capture["manifest"]["requests"][0]["response_observed_at_utc"] = "2026-10-20T12:00:01Z"; save_manifest(capture)
    elif problem == "membership": capture["manifest"]["expected_membership_reference"]["sha256"] = "0" * 64; save_manifest(capture)
    elif problem == "duplicate_request": capture["manifest"]["requests"].append(capture["manifest"]["requests"][0]); save_manifest(capture)
    elif problem in {"normalized_score", "truthy_finished", "native_id"}:
        frame = pd.read_parquet(path / "normalized/fixtures.parquet")
        if problem == "normalized_score": frame["home_goals"] = 9.
        elif problem == "truthy_finished": frame["finished"] = "False"
        else: frame["match_id"] = "fpl_2026-27_999"
        frame.to_parquet(path / "normalized/fixtures.parquet", index=False)
    elif problem in {"fd_score", "fd_result", "fd_missing"}:
        fd = (path / "raw/football_data/E0.csv").read_text()
        if problem == "fd_score": fd = fd.replace(",2,1,H", ",3,1,H")
        elif problem == "fd_result": fd = fd.replace(",2,1,H", ",2,1,A")
        else: fd = fd.replace("17/10/2026", "18/10/2026")
        replace_source(capture, "football_data_e0", fd.encode())
    before_forecast = capture["forecasts"].read_bytes()
    with pytest.raises(ValueError):
        settlement.validate_snapshot_for_settlement(path, root=capture["root"])
    assert capture["forecasts"].read_bytes() == before_forecast
    assert not capture["outcomes"].exists()


@pytest.mark.parametrize("problem", ["finished_not_boolean", "not_started", "negative_goals", "fractional_goals", "observed_before_kickoff"])
def test_finished_source_requires_real_status_valid_goals_and_elapsed_kickoff(capture, problem):
    raw = deepcopy(capture["raw"])
    if problem == "finished_not_boolean": raw[0]["finished"] = "true"
    elif problem == "not_started": raw[0]["started"] = False
    elif problem == "negative_goals": raw[0]["team_h_score"] = -1
    elif problem == "fractional_goals": raw[0]["team_h_score"] = 1.5
    elif problem == "observed_before_kickoff": raw[0]["kickoff_time"] = "2026-10-21T14:00:00Z"
    replace_source(capture, "fpl_fixtures", json.dumps(raw).encode(), normalize=True)
    with pytest.raises(ValueError):
        settlement.validate_snapshot_for_settlement(capture["snapshot"], root=capture["root"])
    assert not capture["outcomes"].exists()


def test_existing_identical_settlement_is_not_reproposed_and_revision_fails(capture, monkeypatch):
    audit = settlement.validate_snapshot_for_settlement(capture["snapshot"], root=capture["root"])
    monkeypatch.setattr(ledger, "_utc_now", lambda: datetime(2026, 10, 20, 13, tzinfo=timezone.utc))
    ledger.append_outcomes(capture["outcomes"], audit["proposed_outcomes"])
    before = capture["outcomes"].read_bytes()
    repeated = settlement.validate_snapshot_for_settlement(capture["snapshot"], root=capture["root"])
    assert repeated["proposed_outcomes"] == [] and repeated["preflight_resolved_prediction_count"] == 1
    assert capture["outcomes"].read_bytes() == before
    raw = deepcopy(capture["raw"])
    raw[0]["team_h_score"] = 3
    replace_source(capture, "fpl_fixtures", json.dumps(raw).encode(), normalize=True)
    fd = (capture["snapshot"] / "raw/football_data/E0.csv").read_text().replace(",2,1,H", ",3,1,H")
    replace_source(capture, "football_data_e0", fd.encode())
    with pytest.raises(ValueError, match="previously settled result changed"):
        settlement.validate_snapshot_for_settlement(capture["snapshot"], root=capture["root"])
    assert capture["outcomes"].read_bytes() == before


def test_scoring_failure_occurs_during_preflight_before_evaluator_is_called(capture, monkeypatch):
    monkeypatch.setattr(settlement.frozen_evaluate, "ROOT", capture["root"] / "epl_live")
    calls = []
    monkeypatch.setattr(settlement.frozen_evaluate, "evaluate", lambda *args, **kwargs: calls.append(True))
    def fail(*args, **kwargs): raise ValueError("invalid scoring data")
    monkeypatch.setattr(settlement.frozen_evaluate, "score_forecasts", fail)
    with pytest.raises(ValueError, match="invalid scoring data"):
        settlement.evaluate_validated(capture["snapshot"], root=capture["root"])
    assert calls == [] and not capture["outcomes"].exists()


def test_validated_evaluator_rejects_changed_inputs_before_mutation(capture, monkeypatch):
    audit = settlement.validate_snapshot_for_settlement(capture["snapshot"], root=capture["root"])
    monkeypatch.setattr(settlement.frozen_evaluate, "ROOT", capture["root"] / "epl_live")
    monkeypatch.setattr(settlement, "validate_snapshot_for_settlement", lambda *args, **kwargs: audit)
    (capture["snapshot"] / "raw/fpl/fixtures.json").write_bytes(b"[]")
    calls = []
    monkeypatch.setattr(settlement.frozen_evaluate, "evaluate", lambda *args, **kwargs: calls.append(True))
    with pytest.raises(ValueError, match="validated settlement input changed"):
        settlement.evaluate_validated(capture["snapshot"], root=capture["root"])
    assert calls == [] and not capture["outcomes"].exists()


def test_default_frozen_output_root_cannot_write_production_from_a_test_root(capture):
    with pytest.raises(ValueError, match="output root must match"):
        settlement.evaluate_validated(capture["snapshot"], root=capture["root"])
    assert not capture["outcomes"].exists()


def test_successful_wrapper_publishes_only_new_temporary_evaluation_and_audit(capture, monkeypatch):
    # The frozen evaluator operates only inside this test's temporary project.
    # No production ledger or output path can be reached through its ROOT.
    monkeypatch.setattr(settlement.frozen_evaluate, "ROOT", capture["root"] / "epl_live")
    monkeypatch.setattr(ledger, "_utc_now", lambda: datetime(2026, 10, 20, 13, tzinfo=timezone.utc))
    before = capture["forecasts"].read_bytes()
    result = settlement.evaluate_validated(capture["snapshot"], root=capture["root"])
    output = Path(result["evaluation_path"])
    assert capture["root"] in output.parents
    assert result["resolved_prediction_count"] == 1 and result["outcomes_append"]["appended"] == 1
    assert capture["forecasts"].read_bytes() == before
    validation = json.loads((output / "settlement_validation.json").read_text())
    manifest = json.loads((output / "settlement_manifest.json").read_text())
    assert validation["forecast_ledger_sha256"] == digest(capture["forecasts"])
    assert manifest["outcome_ledger"]["total_records"] == 1
    for name, expected in manifest["output_sha256"].items():
        assert digest(output / name) == expected


def test_cli_defaults_to_read_only_validation(capture, capsys):
    result = settlement.main(["--snapshot", str(capture["snapshot"]), "--root", str(capture["root"])])
    printed = json.loads(capsys.readouterr().out)
    assert printed == result and result["action"] == "read_only_preflight"
    assert result["proposed_outcomes"] == 1 and "evaluation_path" not in result
    assert not capture["outcomes"].exists()


def test_cli_requires_explicit_evaluate_flag_for_the_mutating_api(capture, monkeypatch, capsys):
    audit = settlement.validate_snapshot_for_settlement(capture["snapshot"], root=capture["root"])
    calls = []
    def fake(snapshot, *, root):
        calls.append((snapshot, root))
        print("preserved evaluator's verbose output")
        return {"validation": audit, "evaluation_path": "test_evaluation", "outcomes_append": {"appended": 1}}
    monkeypatch.setattr(settlement, "evaluate_validated", fake)
    result = settlement.main(["--snapshot", str(capture["snapshot"]), "--root", str(capture["root"]), "--evaluate"])
    assert json.loads(capsys.readouterr().out) == result
    assert result["evaluation_path"] == "test_evaluation" and result["action"] == "evaluated"
    assert len(calls) == 1 and not capture["outcomes"].exists()
