"""Publish the first observed forecast cohort without changing its predictions."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import platform
import shutil
import subprocess

import numpy as np
import pandas as pd

from epl_live.ledger import earliest_forecasts, read_forecasts, read_outcomes, verify_ledger
from epl_strategy_validation.build import publish_latest

ROOT = Path(__file__).resolve().parents[1]
ANCHOR_COMMIT = "8d1dc519b7fceb52247a240435424e12ca1b9708"
ORIGINAL_SHA256 = "f828b68d2a3deb44457c0b92629d3e7c6655cfa8d8eb8f69ff30607b73680214"
EXECUTION = ROOT / "epl_execution/results/20261015_quote_sensitivity"
ORIGINAL_RUN = ROOT / "epl_live/runs/20261014T092230.366245Z"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False, default=str) + "\n", encoding="utf-8")


def save(output, name, frame):
    frame.to_csv(output / (name + ".csv"), index=False)
    frame.to_parquet(output / (name + ".parquet"), index=False)


def original_ledger_bytes(root=ROOT):
    original = subprocess.check_output(["git", "-C", str(root), "show", ANCHOR_COMMIT + ":epl_live/forecasts.jsonl"])
    if hashlib.sha256(original).hexdigest() != ORIGINAL_SHA256 or len(original.splitlines()) != 40:
        raise AssertionError("The committed original forecast anchor differs")
    return original


def verify_original_prefix(current, original):
    if not current.startswith(original):
        raise AssertionError("Original forecast bytes changed or moved in the append-only ledger")
    if original and not original.endswith(b"\n"):
        raise AssertionError("The original ledger must end on a complete record boundary")


def code_paths():
    return sorted(p for p in Path(__file__).parent.rglob("*") if p.is_file()
        and p.suffix in {".py", ".md", ".txt"} and "results" not in p.relative_to(Path(__file__).parent).parts)


def verified_snapshot_sources(snapshot):
    snapshot = Path(snapshot).resolve()
    manifest = json.loads((snapshot / "manifest.json").read_text())
    files = [snapshot / "manifest.json", snapshot / "snapshot_header.json", snapshot / "request_log.jsonl"]
    for record in manifest["requests"]:
        path = (snapshot / record["path"]).resolve()
        if snapshot not in path.parents:
            raise AssertionError("A request path escapes its immutable snapshot")
        if record["status"] != "downloaded" or sha(path) != record["sha256"]:
            raise AssertionError("A captured response is missing, failed or changed")
        files.append(path)
    files.extend((snapshot / "normalized").glob("*"))
    return sorted(set(p for p in files if p.is_file()))


def source_freshness(snapshot, role):
    manifest = json.loads((snapshot / "manifest.json").read_text())
    requests = {record["source_key"]: record for record in manifest["requests"]}
    rows = []
    for label, source, key in (("FPL", "fpl_fixtures", "fpl_last_completed_match_date"),
            ("Football-Data", "football_data_e0", "football_data_last_completed_match_date"),
            ("Understat", "understat_league", "understat_last_completed_match_date")):
        record = requests[source]
        rows.append({"source": label, "observed_at_utc": record["response_observed_at_utc"],
            "latest_completed_match_date": manifest["freshness"].get(key),
            "source_capture_valid": manifest["usable"], "snapshot_id": manifest["snapshot_id"],
            "snapshot_role": role, "core_source_status": record["status"],
            "source_url": record["url"], "provider_publication_time_verified": False})
    return pd.DataFrame(rows)


def next_forecast_frame(forecasts, run):
    targets = pd.read_parquet(run / "target_fixtures.parquet")
    summary = json.loads((run / "run_summary.json").read_text())
    cutoff = pd.Timestamp(summary["created_at_utc"])
    rows = []
    for record in earliest_forecasts(forecasts):
        if record["match_id"] not in set(targets.match_id) or pd.Timestamp(record["created_at_utc"]) > cutoff:
            continue
        rows.append({k: record[k] for k in ("match_id", "model_id", "feature_group", "home_team", "away_team",
            "kickoff_utc", "created_at_utc", "model_sha256", "snapshot_id")} | {
            "p_" + key: record["probabilities"][key] for key in "HDA"} | {
            "status": "pending", "recorded_trade": False, "quote_available_at_release": record.get("market_quote") is not None})
    columns = ["match_id", "model_id", "feature_group", "home_team", "away_team", "kickoff_utc", "created_at_utc",
        "model_sha256", "snapshot_id", "p_H", "p_D", "p_A", "status", "recorded_trade", "quote_available_at_release"]
    frame = pd.DataFrame(rows, columns=columns)
    if len(frame) and (pd.to_datetime(frame.created_at_utc, utc=True) >= pd.to_datetime(frame.kickoff_utc, utc=True)).any():
        raise AssertionError("A new forecast was created after its target kickoff")
    return frame


def build(output, *, results_snapshot, player_snapshot, evaluation, next_run, update_latest=False):
    from .analysis import build_analysis
    from .audit import audit_export
    start = datetime.now(timezone.utc)
    output = Path(output).resolve()
    if (ROOT / "epl_prospective/results").resolve() not in output.parents or output.exists():
        raise ValueError("Use a new directory below epl_prospective/results; existing runs are immutable")
    results_snapshot, player_snapshot, evaluation, next_run = [Path(p).resolve()
        for p in (results_snapshot, player_snapshot, evaluation, next_run)]
    original = original_ledger_bytes()
    ledger_path, outcomes_path = ROOT / "epl_live/forecasts.jsonl", ROOT / "epl_live/outcomes.jsonl"
    verify_original_prefix(ledger_path.read_bytes(), original)
    sources = verified_snapshot_sources(results_snapshot) + verified_snapshot_sources(player_snapshot)
    sources += [ledger_path, outcomes_path]
    for folder in (evaluation, next_run, ORIGINAL_RUN, EXECUTION):
        sources.extend(p for p in folder.rglob("*") if p.is_file())
    execution_registry = json.loads((EXECUTION / "report/report_manifest.json").read_text())["inputs"]
    sources += [ROOT / name for name in execution_registry]
    sources += [p for p in (ROOT / "epl_live/models/e82cad876a650c66").rglob("*") if p.is_file()]
    dependencies = [p for package in ("epl_live", "epl_execution", "epl_strategy_validation", "epl_strategy_lab", "epl_strategy")
        for p in (ROOT / package).glob("*.py")]
    dependencies += [ROOT / "epl_modeling/metrics.py", ROOT / "epl_modeling/PROSPECTIVE_PROTOCOL.md",
        ROOT / "epl_live/OPERATIONAL_PROTOCOL.md", ROOT / "epl_data/metadata/current_teams.csv"]
    protected = sorted(set(sources + dependencies + code_paths()))
    before, inventory = {p: sha(p) for p in protected}, set(code_paths())
    output.mkdir(parents=True)
    (output / "original_forecast_ledger.jsonl").write_bytes(original)
    for source, name in ((ledger_path, "forecast_ledger_as_of.jsonl"), (outcomes_path, "outcome_ledger_as_of.jsonl")):
        shutil.copyfile(source, output / name)
    original_forecasts = read_forecasts(output / "original_forecast_ledger.jsonl")
    forecasts, outcomes = read_forecasts(output / "forecast_ledger_as_of.jsonl"), read_outcomes(output / "outcome_ledger_as_of.jsonl")
    models, match_ids = {f["model_id"] for f in original_forecasts}, {f["match_id"] for f in original_forecasts}
    if any(f.get("market_quote") is not None for f in original_forecasts):
        raise AssertionError("The original no-price release definition changed")
    tables = build_analysis(original_forecasts, outcomes, original_match_ids=match_ids, original_model_ids=models)
    for name in ("forecast_outcome_audit", "fixture_outcomes"):
        tables[name]["result"] = tables[name].actual_result
        tables[name]["settled_at_utc"] = tables[name].outcome_observed_at_utc
    tables["source_freshness"] = pd.concat([source_freshness(results_snapshot, "results"),
        source_freshness(player_snapshot, "player_refresh")], ignore_index=True)
    tables["next_forecasts"] = next_forecast_frame(forecasts, next_run)
    tables["next_forecast_coverage"] = pd.read_parquet(next_run / "forecast_coverage.parquet")
    tables["original_forecast_coverage"] = pd.read_parquet(ORIGINAL_RUN / "forecast_coverage.parquet")
    for name, frame in tables.items(): save(output, name, frame)
    resolved = tables["forecast_outcome_audit"].actual_result.isin(list("HDA"))
    current = json.loads((next_run / "run_summary.json").read_text())
    player = json.loads((player_snapshot / "manifest.json").read_text())
    if not player["fpl_player_summaries_complete"] or not player["usable"]:
        raise AssertionError("The player refresh does not satisfy the full registry gate")
    status = {"as_of_utc": start.isoformat(), "report_date_new_york": "2026-10-20",
        "results_snapshot": results_snapshot.relative_to(ROOT).as_posix(),
        "player_snapshot": player_snapshot.relative_to(ROOT).as_posix(),
        "evaluation_path": evaluation.relative_to(ROOT).as_posix(), "next_run_path": next_run.relative_to(ROOT).as_posix(),
        "original_forecast_count": len(original_forecasts), "original_fixture_count": len(match_ids),
        "original_model_count": len(models), "resolved_original_forecasts": int(resolved.sum()),
        "pending_original_forecasts": int((~resolved).sum()),
        "resolved_original_fixtures": int(tables["forecast_outcome_audit"].loc[resolved].match_id.nunique()),
        "new_forecasts_released": current["ledger_append"]["appended"], "new_target_fixtures": current["target_fixture_count"],
        "new_pending_forecasts": len(tables["next_forecasts"]),
        "original_withheld_variants": int(tables["original_forecast_coverage"].status.eq("withheld").sum()),
        "new_withheld_variants": int(tables["next_forecast_coverage"].status.eq("withheld").sum()),
        "fpl_player_summaries_requested": player["fpl_player_summaries_requested"],
        "fpl_player_summaries_downloaded": player["fpl_player_summaries_downloaded"],
        "current_completed_match_count": int(pd.read_parquet(player_snapshot / "normalized/fixtures.parquet").finished.eq(True).sum()),
        "models_refitted": False, "winner_selected": False, "recorded_trade_count": 0,
        "prospective_betting_performance_available": False, "prospective_roi": None,
        "prospective_expected_gain": None, "prospective_expected_loss": None,
        "prospective_capital_path_available": False,
        "missing_prices_reason": "Original release contained no pre-match quote or trading ledger; later archived prices cannot create prospective trades.",
        "independent_fixture_count": len(match_ids), "original_anchor_commit": ANCHOR_COMMIT,
        "original_forecast_ledger_sha256": ORIGINAL_SHA256}
    write_json(output / "prospective_status.json", status)
    integrity = {"original": verify_ledger(output / "original_forecast_ledger.jsonl", "forecast"),
        "forecast_as_of": verify_ledger(output / "forecast_ledger_as_of.jsonl", "forecast"),
        "outcome_as_of": verify_ledger(output / "outcome_ledger_as_of.jsonl", "outcome"),
        "original_bytes_unchanged_prefix": True, "anchor_commit": ANCHOR_COMMIT, "original_sha256": ORIGINAL_SHA256}
    write_json(output / "ledger_integrity.json", integrity)
    versions = {name: version(name) for name in ("numpy", "pandas", "scipy", "scikit-learn", "pyarrow", "matplotlib",
        "plotly", "reportlab", "python-docx", "XlsxWriter", "pypdf")}
    provenance = {"started_at_utc": start.isoformat(), "python": platform.python_version(), "versions": versions,
        "inputs_and_code_sha256": {p.relative_to(ROOT).as_posix(): value for p, value in before.items()},
        "original_forecast_anchor": {"commit": ANCHOR_COMMIT, "sha256": ORIGINAL_SHA256, "records": 40},
        "models_refitted": False, "independent_fixture_count": 10}
    write_json(output / "source_provenance.json", provenance)
    write_json(output / "independent_audit.json", audit_export(output))
    from .report import build_report
    report = build_report(output)
    changed = [p.relative_to(ROOT).as_posix() for p, value in before.items() if not p.exists() or sha(p) != value]
    if changed or inventory != set(code_paths()):
        raise RuntimeError("A consumed source or implementation changed during build: " + str(changed))
    manifest = {**provenance, "completed_at_utc": datetime.now(timezone.utc).isoformat(), "protected_hashes_unchanged": True,
        "report": report, "row_counts": {name: len(frame) for name, frame in tables.items()},
        "output_sha256": {p.relative_to(output).as_posix(): sha(p) for p in sorted(output.rglob("*")) if p.is_file()}}
    write_json(output / "manifest.json", manifest)
    if update_latest: publish_latest(output)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("output", "results-snapshot", "player-snapshot", "evaluation", "next-run"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--update-latest", action="store_true")
    args = parser.parse_args()
    result = build(args.output, results_snapshot=args.results_snapshot, player_snapshot=args.player_snapshot,
        evaluation=args.evaluation, next_run=args.next_run, update_latest=args.update_latest)
    print(json.dumps({"completed_at_utc": result["completed_at_utc"], "rows": result["row_counts"], "report": result["report"]}, indent=2))


if __name__ == "__main__": main()
