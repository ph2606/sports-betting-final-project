"""Timestamp, preservation, integrity and writer-coordination checks."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import json
from threading import Event

import pytest

from epl_live import ledger


NOW = datetime(2026, 10, 14, 9, tzinfo=timezone.utc)


@pytest.fixture(autouse=True)
def fixed_clock(monkeypatch):
    monkeypatch.setattr(ledger, "_utc_now", lambda: NOW)


def forecast(match_id="fixture-1", *, market=False):
    value = {"match_id": match_id, "home_team": "Arsenal", "away_team": "Chelsea",
             "season": "2026-27", "kickoff_utc": "2026-10-17T14:00:00Z",
             "model_id": "frozen-logistic-team", "model_sha256": "a" * 64,
             "code_sha256": "b" * 64, "protocol_sha256": "c" * 64,
             "created_at_utc": "2026-10-14T09:00:00Z",
             "source_snapshots": [{"sha256": "d" * 64,
                                    "observed_at_utc": "2026-10-14T08:59:00Z",
                                    "source": "saved-match-snapshot"}],
             "features": {"goals_diff": 0.5, "unavailable_history": None},
             "probabilities": {"H": 0.5, "D": 0.25, "A": 0.25},
             "forecast_type": "market_residual" if market else "team_only",
             "target_match_date": "2026-10-17",
             "latest_feature_match_dates": {"E0": "2026-10-03", "FPL": None}}
    if market:
        value["market_quote"] = {"bookmaker": "paper-reference",
                                 "odds": {"H": 2.1, "D": 3.4, "A": 3.8},
                                 "observed_at_utc": "2026-10-14T08:30:00Z"}
    return value


def change(record, path, value):
    names = path.split(".")
    item = record
    for name in names[:-1]:
        item = item[int(name)] if isinstance(item, list) else item[name]
    item[names[-1]] = value


def independent_hash(envelope):
    body = {key: value for key, value in envelope.items() if key != "record_hash"}
    raw = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()
    return hashlib.sha256(raw).hexdigest()


def test_roundtrip_chain_preserves_records_and_explicit_unknown_publication(tmp_path):
    path = tmp_path / "forecasts.jsonl"
    records = [forecast(), forecast("fixture-2", market=True)]
    original = deepcopy(records)
    summary = ledger.append_forecasts(path, records)
    assert summary["appended"] == summary["total_records"] == 2
    assert summary["max_quote_age_seconds"] == 3600
    assert records == original
    envelopes = [json.loads(line) for line in path.read_text().splitlines()]
    assert envelopes[0]["previous_hash"] is None
    assert envelopes[1]["previous_hash"] == envelopes[0]["record_hash"]
    assert [line["sequence"] for line in envelopes] == [1, 2]
    assert all(independent_hash(line) == line["record_hash"] for line in envelopes)
    assert summary["head_hash"] == envelopes[-1]["record_hash"]
    loaded = ledger.read_forecasts(path)
    assert loaded[0]["features"]["unavailable_history"] is None
    assert loaded[0]["latest_feature_match_dates"]["FPL"] is None
    assert loaded[1]["market_quote"]["publication_time_verified"] is False
    assert "published_at_utc" not in loaded[1]["market_quote"]
    assert all(r["source_snapshots"][0]["publication_time_verified"] is False for r in loaded)
    assert ledger.verify_ledger(path, "forecast")["valid"] is True
    assert not ledger.ledger_lock_path(path).exists()


@pytest.mark.parametrize("field,value", [
    ("created_at_utc", "2026-10-14T09:00:00"),
    ("created_at_utc", "2026-10-14T05:00:00-04:00"),
    ("created_at_utc", "2026-10-14T09:00:01Z"),
    ("source_snapshots.0.observed_at_utc", "2026-10-14T09:00:01Z"),
    ("source_snapshots.0.observed_at_utc", "2026-10-14T08:59:00"),
    ("source_snapshots.0.sha256", "not-a-digest"),
    ("source_snapshots.0.publication_time_verified", True),
    ("source_snapshots", []),
    ("source_snapshots", None),
    ("features", []),
    ("features.goals_diff", float("inf")),
    ("probabilities.H", float("nan")),
    ("probabilities.H", 0.4),
    ("probabilities.H", True),
    ("probabilities", {"H": -0.1, "D": 0.7, "A": 0.4}),
    ("latest_feature_match_dates.E0", "2026-10-17"),
    ("latest_feature_match_dates", []),
    ("target_match_date", "2026-10-18"),
    ("season", "2025-26"),
    ("model_sha256", "a" * 63),
    ("update_version", 0),
    ("forecast_type", "unknown"),
])
def test_invalid_forecasts_never_write_records(tmp_path, field, value):
    path = tmp_path / "forecasts.jsonl"
    record = forecast()
    change(record, field, value)
    with pytest.raises(ledger.LedgerValidationError):
        ledger.append_forecasts(path, [record])
    assert not path.exists()
    assert not ledger.ledger_lock_path(path).exists()


@pytest.mark.parametrize("field,value", [
    ("market_quote", None),
    ("market_quote.odds", {"H": 2.1, "D": 3.4}),
    ("market_quote.odds.H", 1.0),
    ("market_quote.observed_at_utc", "2026-10-14T07:59:59Z"),
    ("market_quote.observed_at_utc", "2026-10-14T09:00:01Z"),
    ("market_quote.published_at_utc", "2026-10-14T08:30:01Z"),
    ("market_quote.publication_time_verified", True),
])
def test_market_residual_requires_complete_observed_quote(tmp_path, field, value):
    record = forecast(market=True)
    change(record, field, value)
    with pytest.raises(ledger.LedgerValidationError):
        ledger.append_forecasts(tmp_path / "forecasts.jsonl", [record])


def test_quote_boundary_and_known_publication_are_not_confused(tmp_path):
    record = forecast(market=True)
    record["market_quote"].update(observed_at_utc="2026-10-14T08:00:00Z",
                                  published_at_utc="2026-10-13T07:00:00Z")
    path = tmp_path / "forecasts.jsonl"
    ledger.append_forecasts(path, [record])
    quote = ledger.read_forecasts(path)[0]["market_quote"]
    assert quote["observed_at_utc"] == "2026-10-14T08:00:00Z"
    assert quote["published_at_utc"] == "2026-10-13T07:00:00Z"
    assert quote["publication_time_verified"] is False
    # Only observation age is bounded: an old publication clock is preserved.


def test_fake_later_printed_date_cannot_admit_fixture_day_features(tmp_path):
    record = forecast()
    record["target_match_date"] = "2026-10-18"
    record["latest_feature_match_dates"]["E0"] = "2026-10-17"
    with pytest.raises(ledger.LedgerValidationError, match="UTC kickoff date"):
        ledger.append_forecasts(tmp_path / "forecasts.jsonl", [record])


def test_window_kickoff_boundary_and_actual_append_cutoff(tmp_path, monkeypatch):
    record = forecast()
    record.update(kickoff_utc="2026-10-14T04:00:00Z", target_match_date="2026-10-14",
                  created_at_utc="2026-10-14T03:00:00Z")
    record["source_snapshots"][0]["observed_at_utc"] = "2026-10-14T02:59:00Z"
    monkeypatch.setattr(ledger, "_utc_now", lambda: datetime(2026, 10, 14, 3, tzinfo=timezone.utc))
    ledger.append_forecasts(tmp_path / "boundary.jsonl", [record])
    before = deepcopy(record)
    before.update(kickoff_utc="2026-10-14T03:59:59Z")
    with pytest.raises(ledger.LedgerValidationError, match="window"):
        ledger.append_forecasts(tmp_path / "too-early.jsonl", [before])
    monkeypatch.setattr(ledger, "_utc_now", lambda: datetime(2026, 10, 17, 14, tzinfo=timezone.utc))
    with pytest.raises(ledger.LedgerValidationError, match="strictly before kickoff"):
        ledger.append_forecasts(tmp_path / "late-backfill.jsonl", [forecast()])


def test_identical_retry_is_idempotent_even_after_kickoff(tmp_path, monkeypatch):
    path = tmp_path / "forecasts.jsonl"
    record = forecast()
    ledger.append_forecasts(path, [record])
    original = path.read_bytes()
    monkeypatch.setattr(ledger, "_utc_now", lambda: datetime(2026, 10, 18, tzinfo=timezone.utc))
    result = ledger.append_forecasts(path, [record])
    assert result["appended"] == 0
    assert result["skipped_duplicates"] == 1
    assert path.read_bytes() == original


def test_changed_duplicate_cannot_replace_earliest_forecast(tmp_path):
    path = tmp_path / "forecasts.jsonl"
    record = forecast()
    ledger.append_forecasts(path, [record])
    original = path.read_bytes()
    record["probabilities"] = {"H": 0.6, "D": 0.2, "A": 0.2}
    with pytest.raises(ledger.DuplicateForecastError):
        ledger.append_forecasts(path, [record])
    assert path.read_bytes() == original


def test_explicit_update_is_preserved_and_primary_is_version_one(tmp_path, monkeypatch):
    path = tmp_path / "forecasts.jsonl"
    first = forecast()
    ledger.append_forecasts(path, [first])
    later = deepcopy(first)
    later.update(update_version=2, created_at_utc="2026-10-14T09:01:00Z",
                 probabilities={"H": 0.6, "D": 0.2, "A": 0.2})
    monkeypatch.setattr(ledger, "_utc_now", lambda: NOW + timedelta(minutes=2))
    ledger.append_forecasts(path, [later])
    records = ledger.read_forecasts(path)
    assert [r["update_version"] for r in records] == [1, 2]
    assert ledger.earliest_forecasts(records)[0]["probabilities"] == first["probabilities"]
    assert ledger.append_forecasts(path, [later])["skipped_duplicates"] == 1
    invalid = deepcopy(later)
    invalid.update(update_version=3, model_sha256="e" * 64, created_at_utc="2026-10-14T09:02:00Z")
    with pytest.raises(ledger.DuplicateForecastError, match="model_sha256"):
        ledger.append_forecasts(path, [invalid])
    assert ledger.verify_ledger(path)["total_records"] == 2


@pytest.mark.parametrize("version,created", [(2, "2026-10-14T09:00:00Z"), (3, "2026-10-14T09:01:00Z")])
def test_updates_need_next_version_and_later_creation(tmp_path, monkeypatch, version, created):
    path = tmp_path / "forecasts.jsonl"
    ledger.append_forecasts(path, [forecast()])
    record = forecast()
    record.update(update_version=version, created_at_utc=created)
    monkeypatch.setattr(ledger, "_utc_now", lambda: NOW + timedelta(minutes=2))
    with pytest.raises(ledger.DuplicateForecastError):
        ledger.append_forecasts(path, [record])


def test_entire_batch_is_validated_before_any_append(tmp_path):
    path = tmp_path / "forecasts.jsonl"
    ledger.append_forecasts(path, [forecast()])
    old = path.read_bytes()
    invalid = forecast("invalid")
    invalid["probabilities"]["H"] = 0.9
    with pytest.raises(ledger.LedgerValidationError):
        ledger.append_forecasts(path, [forecast("otherwise-valid"), invalid])
    assert path.read_bytes() == old


def test_same_batch_duplicate_is_recorded_once(tmp_path):
    summary = ledger.append_forecasts(tmp_path / "forecasts.jsonl", [forecast(), forecast()])
    assert summary["appended"] == summary["skipped_duplicates"] == summary["total_records"] == 1


@pytest.mark.parametrize("corruption", ["payload", "order", "duplicate", "tail", "invalid-json"])
def test_corrupted_chain_fails_reads_and_future_appends(tmp_path, corruption):
    path = tmp_path / "forecasts.jsonl"
    ledger.append_forecasts(path, [forecast(), forecast("fixture-2")])
    lines = path.read_bytes().splitlines(keepends=True)
    if corruption == "payload":
        envelope = json.loads(lines[0])
        envelope["record"]["features"]["goals_diff"] = 100.0
        lines[0] = json.dumps(envelope).encode() + b"\n"
    elif corruption == "order":
        lines.reverse()
    elif corruption == "duplicate":
        lines.append(lines[0])
    elif corruption == "tail":
        lines[-1] = lines[-1].rstrip(b"\n")
    else:
        lines.append(b"{not-json}\n")
    damaged = b"".join(lines)
    path.write_bytes(damaged)
    with pytest.raises(ledger.LedgerIntegrityError):
        ledger.read_forecasts(path)
    with pytest.raises(ledger.LedgerIntegrityError):
        ledger.append_forecasts(path, [forecast("fixture-3")])
    assert path.read_bytes() == damaged


def test_duplicate_json_keys_are_not_silently_accepted(tmp_path):
    path = tmp_path / "forecasts.jsonl"
    ledger.append_forecasts(path, [forecast()])
    text = path.read_text()
    path.write_text(text.replace('"sequence":1', '"sequence":1,"sequence":1'))
    with pytest.raises(ledger.LedgerIntegrityError, match="Duplicate JSON key"):
        ledger.verify_ledger(path)


def test_quote_policy_cannot_be_relaxed_or_changed_inside_ledger(tmp_path):
    path = tmp_path / "forecasts.jsonl"
    with pytest.raises(ledger.LedgerValidationError, match="one hour"):
        ledger.append_forecasts(path, [forecast()], max_quote_age=timedelta(hours=2))
    ledger.append_forecasts(path, [forecast()])
    with pytest.raises(ledger.LedgerValidationError, match="locked"):
        ledger.append_forecasts(path, [forecast("fixture-2")], max_quote_age=timedelta(minutes=10))


def test_forecasts_and_settlements_stay_separate_and_immutable(tmp_path, monkeypatch):
    forecasts, outcomes = tmp_path / "forecasts.jsonl", tmp_path / "outcomes.jsonl"
    ledger.append_forecasts(forecasts, [forecast()])
    original = forecasts.read_bytes()
    monkeypatch.setattr(ledger, "_utc_now", lambda: datetime(2026, 10, 17, 18, tzinfo=timezone.utc))
    outcome = {"match_id": "fixture-1", "result": "H", "settled_at_utc": "2026-10-17T17:00:00Z",
               "kickoff_utc": "2026-10-17T14:00:00Z", "home_goals": 2, "away_goals": 1}
    ledger.append_outcomes(outcomes, [outcome])
    assert ledger.read_outcomes(outcomes) == [outcome]
    assert ledger.append_outcomes(outcomes, [outcome])["skipped_duplicates"] == 1
    changed = {**outcome, "result": "A", "home_goals": 1, "away_goals": 2}
    with pytest.raises(ledger.DuplicateOutcomeError):
        ledger.append_outcomes(outcomes, [changed])
    with pytest.raises(ledger.LedgerIntegrityError, match="separate"):
        ledger.append_outcomes(forecasts, [outcome])
    with pytest.raises(ledger.LedgerIntegrityError, match="separate"):
        ledger.read_forecasts(outcomes)
    assert forecasts.read_bytes() == original
    assert ledger.verify_ledger(outcomes)["total_records"] == 1


@pytest.mark.parametrize("changed", [
    {"settled_at_utc": "2026-10-18T00:00:00Z"},
    {"settled_at_utc": "2026-10-17T17:00:00"},
    {"settled_at_utc": "2026-10-17T13:00:00Z"},
    {"result": "D"},
    {"home_goals": -1},
])
def test_invalid_settlements_are_rejected(tmp_path, monkeypatch, changed):
    monkeypatch.setattr(ledger, "_utc_now", lambda: datetime(2026, 10, 17, 18, tzinfo=timezone.utc))
    outcome = {"match_id": "fixture-1", "result": "H", "settled_at_utc": "2026-10-17T17:00:00Z",
               "kickoff_utc": "2026-10-17T14:00:00Z", "home_goals": 2, "away_goals": 1}
    outcome.update(changed)
    with pytest.raises(ledger.LedgerValidationError):
        ledger.append_outcomes(tmp_path / "outcomes.jsonl", [outcome])


def test_existing_lock_is_never_removed_by_competing_writer(tmp_path):
    path = tmp_path / "forecasts.jsonl"
    lock = ledger.ledger_lock_path(path)
    lock.write_text("original writer")
    with pytest.raises(ledger.LedgerLockedError):
        ledger.append_forecasts(path, [forecast()])
    assert lock.read_text() == "original writer"
    assert not path.exists()


def test_concurrent_writer_cannot_interleave_hash_chain(tmp_path, monkeypatch):
    path = tmp_path / "forecasts.jsonl"
    ready, release = Event(), Event()
    original_writer = ledger._write_batch
    def blocked_writer(target, payload):
        ready.set()
        if not release.wait(timeout=5):
            raise RuntimeError("Test writer release timed out")
        original_writer(target, payload)
    monkeypatch.setattr(ledger, "_write_batch", blocked_writer)
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(ledger.append_forecasts, path, [forecast()])
        assert ready.wait(timeout=5)
        try:
            second = pool.submit(ledger.append_forecasts, path, [forecast("fixture-2")])
            with pytest.raises(ledger.LedgerLockedError):
                second.result(timeout=5)
        finally:
            release.set()
        assert first.result(timeout=5)["appended"] == 1
    ledger.append_forecasts(path, [forecast("fixture-2")])
    assert ledger.verify_ledger(path)["total_records"] == 2
    assert [r["match_id"] for r in ledger.read_forecasts(path)] == ["fixture-1", "fixture-2"]


def test_partial_os_writes_are_completed_before_commit(tmp_path, monkeypatch):
    original = ledger.os.write
    monkeypatch.setattr(ledger.os, "write", lambda fd, data: original(fd, data[:17]))
    path = tmp_path / "forecasts.jsonl"
    ledger.append_forecasts(path, [forecast()])
    assert ledger.verify_ledger(path)["total_records"] == 1


def test_reader_cannot_bypass_verification(tmp_path):
    with pytest.raises(ledger.LedgerValidationError, match="verify"):
        ledger.read_forecasts(tmp_path / "missing.jsonl", verify=False)
