"""Validate captured result evidence before invoking the frozen evaluator.

Validation is read only. Fresh result prices never become forecast prices, and
no betting P&L is inferred from forecasts lacking contemporaneous quotes.
"""
from __future__ import annotations

import argparse
from contextlib import redirect_stdout
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path

import numpy as np
import pandas as pd

from epl_live import collect, evaluate as frozen_evaluate, ledger


PROJECT = Path(__file__).resolve().parents[1]
REQUIRED_REQUESTS = {
    "fpl_bootstrap": ("raw/fpl/bootstrap-static.json", "https://fantasy.premierleague.com/api/bootstrap-static/"),
    "fpl_fixtures": ("raw/fpl/fixtures.json", "https://fantasy.premierleague.com/api/fixtures/"),
    "football_data_e0": ("raw/football_data/E0.csv", "https://www.football-data.co.uk/mmz4281/2627/E0.csv"),
}
CRITICAL_FIELDS = ["match_id", "fpl_fixture_id", "season", "home_team", "away_team", "kickoff_utc", "match_date",
                   "finished", "started", "home_goals", "away_goals", "observed_at_utc", "eligibility_checked_at_utc", "target_eligible"]


def _sha(path):
    value = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def _utc(value, field):
    if not isinstance(value, str) or not value.endswith(("Z", "+00:00")):
        raise ValueError(field + " must have an explicit UTC observation clock")
    try:
        result = pd.Timestamp(value)
    except (ValueError, TypeError) as error:
        raise ValueError(field + " has an invalid clock") from error
    if result.tzinfo is None or result.utcoffset().total_seconds() != 0:
        raise ValueError(field + " must use UTC")
    return result


def _inside(snapshot, relative):
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise ValueError("A captured source path must be relative to its snapshot")
    target = (snapshot / relative).resolve()
    if snapshot not in target.parents:
        raise ValueError("Captured source path escapes its snapshot")
    return target


def _goal(value, label):
    if isinstance(value, (bool, np.bool_)):
        raise ValueError(label + " must be a nonnegative integer")
    try:
        number = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError(label + " must be a nonnegative integer") from error
    if not np.isfinite(number) or number < 0 or number != np.floor(number):
        raise ValueError(label + " must be a nonnegative integer")
    return int(number)


def _identity(row):
    fields = ("season", "home_team", "away_team")
    if any(not isinstance(row.get(field), str) or not row[field].strip() for field in fields):
        raise ValueError("Complete season/home/away fixture identity is required")
    return tuple(row[field] for field in fields)


def _membership(root):
    path = root / "epl_data/metadata/current_teams.csv"
    expected = pd.read_csv(path)
    if not {"team", "fpl_name", "fpl_team_code", "season"}.issubset(expected) or len(expected) != 20 or expected.team.nunique() != 20 or set(expected.season) != {collect.SEASON}:
        raise ValueError("Settlement requires the saved twenty-club 2026-27 membership")
    aliases = {str(value).strip().casefold(): row.team for row in expected.itertuples(index=False) for value in (row.team, row.fpl_name)}
    aliases.update({name.casefold(): canonical for name, canonical in collect.EXTRA_ALIASES.items()})
    return expected, aliases, path


def _check_hashes(inputs):
    for name, expected in inputs.items():
        path = Path(name)
        actual = _sha(path) if path.is_file() else None
        if actual != expected:
            raise ValueError("A validated settlement input changed: " + name)


def validate_snapshot_for_settlement(snapshot, *, root=PROJECT):
    """Return evidence, proposed outcomes and score preflight without writing.

    The normalized schedule is reproduced from hash-verified raw FPL bytes.
    Every finished released fixture must also match Football-Data by canonical
    teams, printed date, goals and result. Source failures unrelated to result
    identity are recorded separately from the narrower settlement gate.
    """
    root, snapshot = Path(root).resolve(), Path(snapshot).resolve()
    manifest_path = snapshot / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("season") != collect.SEASON or manifest.get("membership_valid") is not True or manifest.get("fpl_schedule_valid") is not True:
        raise ValueError("Settlement requires a validated current-season FPL schedule")
    if not isinstance(manifest.get("snapshot_id"), str) or not manifest["snapshot_id"]:
        raise ValueError("Snapshot identity is missing")
    start = _utc(manifest["snapshot_started_at_utc"], "snapshot start")
    cutoff = _utc(manifest["snapshot_completed_at_utc"], "snapshot cutoff")
    written = _utc(manifest["manifest_written_at_utc"], "manifest creation")
    now = pd.Timestamp(datetime.now(timezone.utc))
    if not start <= cutoff <= written <= now:
        raise ValueError("Snapshot clocks are inconsistent or in the future")
    expected, aliases, membership_path = _membership(root)
    if manifest.get("expected_membership_reference", {}).get("sha256") != _sha(membership_path):
        raise ValueError("Snapshot membership reference hash changed")
    inputs = {str(manifest_path): _sha(manifest_path), str(membership_path): _sha(membership_path)}
    requests, seen_paths, downloaded, failed = {}, set(), 0, 0
    for request in manifest.get("requests", []):
        key = request.get("source_key")
        if not isinstance(key, str) or key in requests:
            raise ValueError("Snapshot source request identities are missing or repeated")
        requests[key] = request
        target = _inside(snapshot, request.get("path"))
        if target in seen_paths:
            raise ValueError("Source requests reuse a captured response path")
        seen_paths.add(target)
        requested = _utc(request["request_started_at_utc"], key + " request start")
        completed = _utc(request["request_completed_at_utc"], key + " request completion")
        if not start <= requested <= completed <= cutoff:
            raise ValueError("Captured request clock lies outside its snapshot")
        if request.get("status") == "downloaded":
            observed = _utc(request.get("response_observed_at_utc"), key + " observed")
            if observed != completed or not isinstance(request.get("http_status"), int) or not 200 <= request["http_status"] < 300:
                raise ValueError("Successful source lacks a consistent HTTP status/observation")
            if not target.is_file() or _sha(target) != request.get("sha256") or target.stat().st_size != request.get("bytes"):
                raise ValueError("Captured source response bytes/hash do not match the manifest")
            inputs[str(target)] = request["sha256"]
            downloaded += 1
        else:
            failed += 1
            if key in REQUIRED_REQUESTS:
                raise ValueError("A required settlement source was not downloaded: " + key)
    for key, (relative, url) in REQUIRED_REQUESTS.items():
        if key not in requests or requests[key].get("path") != relative or requests[key].get("url") != url or requests[key].get("status") != "downloaded":
            raise ValueError("Required settlement source provenance is incomplete: " + key)
    bootstrap = json.loads((snapshot / REQUIRED_REQUESTS["fpl_bootstrap"][0]).read_bytes())
    raw_fixtures = json.loads((snapshot / REQUIRED_REQUESTS["fpl_fixtures"][0]).read_bytes())
    errors = []
    names, member_valid, schedule_valid = collect._validate_fpl(bootstrap, raw_fixtures, expected, aliases, errors)
    if not member_valid or not schedule_valid or errors:
        raise ValueError("Raw FPL source fails independent membership/schedule validation: " + "; ".join(errors))
    if sorted(manifest.get("current_clubs", [])) != sorted(expected.team.tolist()):
        raise ValueError("Snapshot club inventory does not match the verified membership")
    for raw in raw_fixtures:
        if type(raw.get("finished")) is not bool:
            raise ValueError("Raw FPL finished status must be an explicit boolean")
        if raw["finished"]:
            if raw.get("started") is not True:
                raise ValueError("A finished FPL fixture must have actually started")
            _goal(raw.get("team_h_score"), "Finished FPL home goals")
            _goal(raw.get("team_a_score"), "Finished FPL away goals")
    observed = requests["fpl_fixtures"]["response_observed_at_utc"]
    reconstructed = collect._fixtures_table(raw_fixtures, names, observed, cutoff)
    normalized_path = snapshot / "normalized/fixtures.parquet"
    inputs[str(normalized_path)] = _sha(normalized_path)
    normalized = pd.read_parquet(normalized_path)
    if not set(CRITICAL_FIELDS).issubset(normalized) or normalized.match_id.isna().any() or normalized.match_id.duplicated().any() or set(normalized.match_id) != set(reconstructed.match_id):
        raise ValueError("Normalized fixtures have missing, duplicated or changed native identities")
    actual = normalized.set_index("match_id", drop=False).reindex(reconstructed.match_id)
    for column in CRITICAL_FIELDS:
        left, right = actual[column].reset_index(drop=True), reconstructed[column].reset_index(drop=True)
        if column in {"finished", "started", "target_eligible"}:
            if any(not isinstance(value, (bool, np.bool_)) for value in left):
                raise ValueError("Normalized fixture boolean status is malformed: " + column)
        equal = left.eq(right) | (left.isna() & right.isna())
        if not equal.fillna(False).all():
            raise ValueError("Normalized fixture disagrees with verified raw evidence: " + column)

    fd = collect._parse_csv((snapshot / REQUIRED_REQUESTS["football_data_e0"][0]).read_bytes())
    if not {"Div", "Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG", "FTR"}.issubset(fd) or not fd.Div.eq("E0").all():
        raise ValueError("Football-Data result source has an invalid EPL schema")
    fd_dates = collect._season_dates(fd.Date.tolist(), "Football-Data results", errors, dayfirst=True)
    if errors:
        raise ValueError("Football-Data date validation failed: " + "; ".join(errors))
    fd = fd.assign(home_team=fd.HomeTeam.map(lambda value: collect._canonical(value, aliases)),
                   away_team=fd.AwayTeam.map(lambda value: collect._canonical(value, aliases)), match_date=fd_dates.dt.strftime("%Y-%m-%d"))
    if fd[["home_team", "away_team", "match_date"]].isna().any().any() or fd.duplicated(["home_team", "away_team", "match_date"]).any():
        raise ValueError("Football-Data result identities are missing or repeated")
    fd = fd.set_index(["home_team", "away_team", "match_date"])
    forecasts_path, outcomes_path = root / "epl_live/forecasts.jsonl", root / "epl_live/outcomes.jsonl"
    inputs[str(forecasts_path)] = _sha(forecasts_path)
    inputs[str(outcomes_path)] = _sha(outcomes_path) if outcomes_path.is_file() else None
    forecast_validation = ledger.verify_ledger(forecasts_path, "forecast")
    forecasts = ledger.read_forecasts(forecasts_path)
    earliest = ledger.earliest_forecasts(forecasts)
    existing = ledger.read_outcomes(outcomes_path)
    existing_by_match = frozen_evaluate._settlements_by_match(existing)
    envelopes = [json.loads(line) for line in forecasts_path.read_text(encoding="utf-8").splitlines()]
    append_times = {(item["record"]["model_id"], item["record"]["match_id"], item["record"].get("update_version", 1)): item["appended_at_utc"] for item in envelopes}
    fixtures_by_id = normalized.set_index("match_id")
    identities, released_by_match = {}, {}
    for forecast in earliest:
        key, identity = forecast["match_id"], _identity(forecast)
        if key in identities and identities[key] != identity:
            raise ValueError("Released forecasts disagree on fixture identity")
        identities[key] = identity
        released_by_match.setdefault(key, []).append(forecast)
        if key not in fixtures_by_id.index or _identity(fixtures_by_id.loc[key].to_dict()) != identity:
            raise ValueError("Released forecast does not match a native captured fixture")
        actual_kickoff = _utc(fixtures_by_id.loc[key, "kickoff_utc"], "Actual fixture kickoff")
        append = append_times[(forecast["model_id"], key, forecast.get("update_version", 1))]
        if not _utc(forecast["created_at_utc"], "Forecast creation") < actual_kickoff or not _utc(append, "Actual forecast append") < actual_kickoff:
            raise ValueError("A forecast was not actually released before the captured fixture kickoff")
    for key, old in existing_by_match.items():
        if key in identities and _identity(old) != identities[key]:
            raise ValueError("Existing settlement conflicts with the released fixture identity")
        if key in identities and not bool(fixtures_by_id.loc[key, "finished"]):
            raise ValueError("A previously settled source fixture is no longer finished; preserve and investigate")
    proposals, crosschecks = [], []
    for fixture in normalized.to_dict("records"):
        key = fixture["match_id"]
        if key not in identities or fixture["finished"] is not True:
            continue
        kickoff = _utc(fixture["kickoff_utc"], "Finished fixture kickoff")
        settled = _utc(fixture["observed_at_utc"], "Observed finished result")
        if not kickoff < settled:
            raise ValueError("Finished result observation must follow actual kickoff")
        h, a = _goal(fixture["home_goals"], "FPL home goals"), _goal(fixture["away_goals"], "FPL away goals")
        result = "H" if h > a else "A" if h < a else "D"
        fd_key = (fixture["home_team"], fixture["away_team"], fixture["match_date"])
        if fd_key not in fd.index:
            raise ValueError("A finished released fixture has no matching Football-Data result")
        other = fd.loc[fd_key]
        if _goal(other.FTHG, "Football-Data home goals") != h or _goal(other.FTAG, "Football-Data away goals") != a or other.FTR != result:
            raise ValueError("FPL and Football-Data disagree on the finished result")
        crosschecks.append({"match_id": key, "season": fixture["season"], "home_team": fixture["home_team"], "away_team": fixture["away_team"],
                            "match_date": fixture["match_date"], "kickoff_utc": fixture["kickoff_utc"], "home_goals": h, "away_goals": a,
                            "result": result, "football_data_result": other.FTR, "source_agreement": True})
        if key in existing_by_match:
            old = existing_by_match[key]
            if old.get("result") != result or old.get("home_goals") != h or old.get("away_goals") != a:
                raise ValueError("A previously settled result changed; preserve and investigate")
            continue
        proposals.append({"match_id": key, "season": fixture["season"], "home_team": fixture["home_team"], "away_team": fixture["away_team"],
            "result": result, "home_goals": h, "away_goals": a, "kickoff_utc": str(fixture["kickoff_utc"]),
            "settled_at_utc": fixture["observed_at_utc"], "snapshot_id": manifest["snapshot_id"],
            "settlement_time_semantics": "UTC time the finished result was observed, not an inferred final-whistle time"})
    # Preflight the exact data the frozen evaluator will score, before any
    # outcome is committed. A forecast's original kickoff check is preserved.
    predictions, scores = frozen_evaluate.score_forecasts(forecasts, [*existing, *proposals])
    _check_hashes(inputs)
    quote_count = sum(forecast.get("market_quote") is not None for forecast in earliest)
    return {"status": "passed", "validated_at_utc": datetime.now(timezone.utc).isoformat(), "snapshot_id": manifest["snapshot_id"],
        "snapshot_path": str(snapshot), "forecast_ledger": forecast_validation, "forecast_ledger_sha256": inputs[str(forecasts_path)],
        "outcome_ledger_sha256_before": inputs[str(outcomes_path)], "forecast_records": len(forecasts),
        "earliest_prediction_records": len(earliest), "released_unique_fixtures": len(identities),
        "verified_downloaded_responses": downloaded, "unrelated_failed_requests": failed,
        "reconstructed_fixture_count": len(reconstructed), "crosschecked_finished_fixtures": len(crosschecks),
        "existing_outcomes": len(existing), "proposed_outcomes": proposals, "result_crosschecks": crosschecks,
        "preflight_resolved_prediction_count": len(predictions), "preflight_pending_prediction_count": len(earliest) - len(predictions),
        "preflight_scores": scores.to_dict("records"), "quote_covered_prediction_records": quote_count,
        "prospective_trading_performance_available": False,
        "trading_status": "No trading settlement is implemented; result-capture prices never replace missing forecast-time quotes",
        "input_sha256": inputs,
        "clock_semantics": "settled_at is the captured observation of a finished result, not final-whistle time",
        "unchanged_during_preflight": True}


def evaluate_validated(snapshot, *, root=PROJECT):
    """Mutating entry point: run read-only preflight, then the frozen evaluator."""
    root = Path(root).resolve()
    if (root / "epl_live").resolve() != Path(frozen_evaluate.ROOT).resolve():
        raise ValueError("Frozen evaluator output root must match the requested project root")
    validation = validate_snapshot_for_settlement(snapshot, root=root)
    _check_hashes(validation["input_sha256"])
    forecasts_path, outcomes_path = root / "epl_live/forecasts.jsonl", root / "epl_live/outcomes.jsonl"
    summary = frozen_evaluate.evaluate(snapshot, forecasts_path=forecasts_path, outcomes_path=outcomes_path)
    at = datetime.fromisoformat(summary["evaluated_at_utc"])
    output = root / "epl_live/evaluations" / at.strftime("%Y%m%dT%H%M%S.%fZ")
    if not output.is_dir():
        raise ValueError("Frozen evaluator did not publish the expected immutable output directory")
    if _sha(forecasts_path) != validation["forecast_ledger_sha256"]:
        raise ValueError("The forecast ledger changed during settlement")
    for name, expected in validation["input_sha256"].items():
        if Path(name) != outcomes_path and _sha(name) != expected:
            raise ValueError("A captured settlement input changed during evaluation")
    if summary["resolved_prediction_count"] != validation["preflight_resolved_prediction_count"] or summary["outcomes_append"]["appended"] != len(validation["proposed_outcomes"]):
        raise ValueError("Committed settlement differs from its validated preflight")
    committed = frozen_evaluate._settlements_by_match(ledger.read_outcomes(outcomes_path))
    if len(committed) != validation["existing_outcomes"] + len(validation["proposed_outcomes"]):
        raise ValueError("Committed outcome ledger has an unexpected settlement population")
    for proposal in validation["proposed_outcomes"]:
        if committed.get(proposal["match_id"]) != proposal:
            raise ValueError("Committed outcome record differs from its validated proposal")
    audit_path = output / "settlement_validation.json"
    with audit_path.open("x", encoding="utf-8") as handle:
        json.dump(validation, handle, indent=2, allow_nan=False)
        handle.write("\n")
    provenance = {"completed_at_utc": datetime.now(timezone.utc).isoformat(), "settlement_wrapper_sha256": _sha(__file__),
        "frozen_evaluator_sha256": _sha(frozen_evaluate.__file__), "forecast_ledger_sha256_unchanged": _sha(forecasts_path),
        "outcome_ledger": ledger.verify_ledger(outcomes_path, "outcome") if outcomes_path.exists() else None,
        "output_sha256": {path.relative_to(output).as_posix(): _sha(path) for path in sorted(output.rglob("*")) if path.is_file()}}
    with (output / "settlement_manifest.json").open("x", encoding="utf-8") as handle:
        json.dump(provenance, handle, indent=2, allow_nan=False)
        handle.write("\n")
    return {**summary, "evaluation_path": str(output), "validation": validation}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, required=True, help="A completed immutable source capture")
    parser.add_argument("--root", type=Path, default=PROJECT, help="Project root; defaults to this repository")
    parser.add_argument("--evaluate", action="store_true", help="Append validated outcomes and create a new evaluation; default is read-only validation")
    args = parser.parse_args(argv)
    if args.evaluate:
        # The preserved evaluator prints its full legacy summary. The new CLI
        # exposes one concise JSON document while keeping that module intact.
        with redirect_stdout(io.StringIO()):
            result = evaluate_validated(args.snapshot, root=args.root)
        audit = result["validation"]
    else:
        result = None
        audit = validate_snapshot_for_settlement(args.snapshot, root=args.root)
    summary = {"action": "evaluated" if args.evaluate else "read_only_preflight", "status": audit["status"],
        "snapshot_id": audit["snapshot_id"], "forecast_records": audit["forecast_records"],
        "released_unique_fixtures": audit["released_unique_fixtures"],
        "crosschecked_finished_fixtures": audit["crosschecked_finished_fixtures"],
        "proposed_outcomes": len(audit["proposed_outcomes"]),
        "resolved_prediction_count": audit["preflight_resolved_prediction_count"],
        "pending_prediction_count": audit["preflight_pending_prediction_count"],
        "quote_covered_prediction_records": audit["quote_covered_prediction_records"],
        "prospective_trading_performance_available": audit["prospective_trading_performance_available"]}
    if result is not None:
        summary["evaluation_path"] = result["evaluation_path"]
        summary["appended_outcomes"] = result["outcomes_append"]["appended"]
    print(json.dumps(summary, indent=2, allow_nan=False))
    return summary


if __name__ == "__main__":
    main()
