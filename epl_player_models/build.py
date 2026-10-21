"""Fit the locked player-model study and publish complete auditable outputs."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import platform
import subprocess

import numpy as np
import pandas as pd

from epl_live.ledger import append_forecasts, read_forecasts, verify_ledger
from epl_modeling.ablation import date_stratified_paired_intervals
from epl_modeling.metrics import classification_metrics, encode_results
from epl_strategy_validation.analysis import season_stability
from epl_strategy_validation.build import publish_latest

from .catalog import build_catalog, model_key, model_members
from .inputs import LIVE_RUN, LIVE_SNAPSHOT, PRIOR, source_paths, load_base, merge_player_features
from .trading import run_accounts, combined_graphs

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = Path(__file__).with_name("PROTOCOL.md")


def sha(path):
    value = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024*1024), b""): value.update(chunk)
    return value.hexdigest()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False, default=str) + "\n", encoding="utf-8")


def save(output, name, frame, *, csv=True):
    clean = frame.copy(deep=False); clean.attrs = {}
    if csv: clean.to_csv(output / (name + ".csv"), index=False)
    clean.to_parquet(output / (name + ".parquet"), index=False)


def code_paths():
    folder = Path(__file__).parent
    return sorted(p for p in folder.rglob("*") if p.is_file() and p.suffix in {".py", ".md", ".txt"}
        and "results" not in p.relative_to(folder).parts)


def protocol_commit():
    text = subprocess.check_output(["git", "-C", str(ROOT), "log", "-1", "--format=%H%n%cI", "--", "epl_player_models/PROTOCOL.md"]).decode().strip().splitlines()
    if len(text) != 2: raise ValueError("Commit the explicit player-model protocol before fitting")
    recorded = subprocess.check_output(["git", "-C", str(ROOT), "show", text[0] + ":epl_player_models/PROTOCOL.md"])
    if recorded != PROTOCOL.read_bytes(): raise ValueError("The working protocol differs from its pre-fitting commitment")
    return {"commit": text[0], "committed_at_utc": pd.Timestamp(text[1]).tz_convert("UTC").isoformat(), "sha256": sha(PROTOCOL)}


def scored_tables(predictions):
    pooled, seasonal = [], []
    for label in ["pooled"] + sorted(predictions.outer_season.unique()):
        part = predictions if label == "pooled" else predictions.loc[predictions.outer_season.eq(label)]
        for key, group in part.groupby("model_key", sort=False):
            first = group.iloc[0]
            row = {"model_key": key, "label": first.label, "feature_group": first.feature_group,
                "model_type": first.model_type, "outer_season": label,
                **classification_metrics(encode_results(group.result), group[["p_H", "p_D", "p_A"]])}
            (pooled if label == "pooled" else seasonal).append(row)
    return pd.DataFrame(pooled), pd.DataFrame(seasonal)


def coverage_summary(details, historical):
    coverage = details["target_coverage"].loc[details["target_coverage"].match_id.isin(historical.match_id)].copy()
    rows = []
    for (season, side), part in coverage.groupby(["season", "side"], sort=True):
        rows.append({"season": season, "side": side, "target_sides": len(part),
            "history_available_fraction": float(part.observed_matches10.gt(0).mean()),
            "mean_observed_matches5": float(part.observed_matches5.mean()),
            "mean_observed_matches10": float(part.observed_matches10.mean()),
            "full_projected_xi_fraction": float(part.xi_selected_players.eq(11).mean()),
            "mean_projected_players": float(part.xi_selected_players.mean()),
            "mean_missing_xi_slots": float(part.xi_missing_slots.mean()),
            "known_transfer_candidates_excluded": int(part.known_transfer_candidates_excluded.sum())})
    return coverage, pd.DataFrame(rows)


def market_comparisons(primary, combined):
    rows = []
    for label in ["pooled"] + sorted(primary.outer_season.unique()):
        part = primary if label == "pooled" else primary.loc[primary.outer_season.eq(label)]
        refs = combined.loc[combined.model_key.eq("benchmark_market")]
        if label != "pooled": refs = refs.loc[refs.outer_season.eq(label)]
        for (group, family), candidate in part.groupby(["feature_group", "model_type"], sort=False):
            rows.extend({**row, "feature_group": group, "model_type": family, "reference_group": "market_only",
                "reference_model_type": "baseline", "outer_season": label, "sample_scope": "all_common_quoted_fixtures",
                "inference_status": "descriptive_conditional_no_multiplicity_adjustment"}
                for row in date_stratified_paired_intervals(candidate, refs, seed=42, n_bootstrap=1000))
    return pd.DataFrame(rows)


def release_future(output, predictions, future_features, future_metadata, catalog, commitment):
    features = future_features.set_index("match_id")
    artifacts = {(r["feature_group"], r["model_type"]): r for r in future_metadata["artifacts"]}
    labels = {r["model_key"]: r["label"] for r in catalog["models"]}
    code_sha = hashlib.sha256(json.dumps({p.relative_to(ROOT).as_posix(): sha(p) for p in code_paths()}, sort_keys=True).encode()).hexdigest()
    observed = datetime.now(timezone.utc).isoformat()
    source_records = [
        {"source": (LIVE_SNAPSHOT / "manifest.json").as_posix(), "sha256": sha(ROOT / LIVE_SNAPSHOT / "manifest.json"),
            "observed_at_utc": json.loads((ROOT / LIVE_SNAPSHOT / "manifest.json").read_text())["manifest_written_at_utc"], "publication_time_verified": False},
        {"source": "Saved strictly lagged player-model future feature frame", "sha256": sha(output / "future_features.parquet"),
            "observed_at_utc": observed, "publication_time_verified": False},
        {"source": "New frozen player-model bundle metadata", "sha256": sha(output / "future_models/future_models_metadata.json"),
            "observed_at_utc": observed, "publication_time_verified": False},
    ]
    records = []
    for row in predictions.to_dict("records"):
        native = features.loc[row["match_id"]]
        artifact = artifacts[row["feature_group"], row["model_type"]]
        created = datetime.now(timezone.utc).isoformat()
        if pd.Timestamp(created) >= pd.Timestamp(native.kickoff_utc): raise ValueError("A new player forecast target has started")
        values = {column: float(native[column]) if pd.notna(native[column]) else None for column in artifact["features"]}
        dates = {column: pd.Timestamp(native[column]).strftime("%Y-%m-%d") if pd.notna(native[column]) else None
            for column in native.index if column.startswith("audit_") and (column.endswith("_date") or column.endswith("_prior_date"))}
        records.append({"match_id": row["match_id"], "fpl_fixture_id": int(native.fpl_fixture_id), "season": "2026-27",
            "home_team": native.home_team, "away_team": native.away_team, "kickoff_utc": native.kickoff_utc,
            "target_match_date": pd.Timestamp(native.match_date).strftime("%Y-%m-%d"), "model_id": row["model_key"],
            "model_sha256": artifact["artifact_sha256"], "code_sha256": code_sha, "protocol_sha256": commitment["sha256"],
            "protocol_committed_at_utc": commitment["committed_at_utc"], "protocol_commit": commitment["commit"],
            "created_at_utc": created, "source_snapshots": source_records, "features": values,
            "probabilities": {key: float(row["p_" + key]) for key in "HDA"},
            "latest_feature_match_dates": dates, "forecast_type": "team_only", "feature_group": row["feature_group"],
            "model_type": row["model_type"], "market_quote": None, "snapshot_id": LIVE_SNAPSHOT.name, "update_version": 1,
            "data_quality": {"player_source_rows": int(catalog["player_source_metadata"]["player_rows"]), "feature_latest_date_violations": 0,
                "source_publication_times_verified": False, "target_lineup_used": False},
            "forecast_definition": "New separate non-market-input player study; feature_group identifies player-only or team/player inputs"})
    result = append_forecasts(output / "forecasts.jsonl", records)
    released = read_forecasts(output / "forecasts.jsonl")
    saved = {(r["model_id"], r["match_id"]): r for r in released}
    frame = predictions.copy()
    frame["created_at_utc"] = [saved[row.model_key, row.match_id]["created_at_utc"] for row in frame.itertuples()]
    frame["kickoff_utc"] = frame.match_id.map(features.kickoff_utc)
    frame["status"], frame["label"] = "pending", frame.model_key.map(labels)
    write_json(output / "forecast_release.json", {"ledger": verify_ledger(output / "forecasts.jsonl", "forecast"),
        "append_result": result, "source_snapshot": LIVE_SNAPSHOT.as_posix(), "new_model_count": 8,
        "new_target_fixtures": len(features), "new_pending_predictions": len(frame), "no_existing_ledger_modified": True,
        "prospective_trading_performance_available": False})
    return frame


def build(output, *, update_latest=False, bootstrap_samples=1000):
    from .features import load_player_history, build_player_features
    from .models import train_rolling, fit_future, predict_future
    from .audit import audit_export
    start = datetime.now(timezone.utc)
    output = Path(output).resolve()
    parent = (ROOT / "epl_player_models/results").resolve()
    if parent not in output.parents or output.exists(): raise ValueError("Use a new immutable directory below epl_player_models/results")
    commitment = protocol_commit()
    dependencies = [p for package in ("epl_modeling", "epl_live", "epl_prospective", "epl_execution", "epl_strategy", "epl_strategy_lab", "epl_strategy_validation")
        for p in (ROOT / package).glob("*.py")]
    protected = sorted(set(source_paths(ROOT) + dependencies + code_paths()))
    before, inventory = {p: sha(p) for p in protected}, set(code_paths())
    old_live = {name: sha(ROOT / "epl_live" / name) for name in ("forecasts.jsonl", "outcomes.jsonl")}
    output.mkdir(parents=True)
    write_json(output / "protocol_lock.json", {**commitment, "locked_before_full_fitting": True, "locked_at_utc": start.isoformat()})
    print("Loading full native player histories and frozen common fixtures", flush=True)
    base, targets, opportunities, benchmarks, _ = load_base(ROOT)
    players, source_metadata, loaded = load_player_history(ROOT / "epl_data", live_snapshot=ROOT / LIVE_SNAPSHOT)
    if not set(Path(p).resolve() for p in loaded).issubset(before): raise AssertionError("Player loader read a source outside the prehashed inventory")
    save(output, "player_history", players, csv=False)
    all_targets = pd.concat([base[["match_id", "season", "match_date", "home_team", "away_team"]],
        targets[["match_id", "season", "match_date", "home_team", "away_team"]]], ignore_index=True)
    print(f"Building strictly prior player features for {len(all_targets)} targets", flush=True)
    player_features, feature_metadata, details = build_player_features(players, all_targets)
    features, future_features, groups = merge_player_features(base, targets, player_features, feature_metadata)
    catalog = {"groups": groups, "models": model_members(groups), "protocol": commitment,
        "player_source_metadata": source_metadata, "feature_metadata": feature_metadata,
        "study_status": "exploratory_previously_inspected_history_not_fresh_holdout"}
    new_strategies = build_catalog()
    old_catalog = json.loads((ROOT / "epl_strategy_lab/results/20261015T040052Z_100k84/catalog.json").read_text())
    write_json(output / "model_catalog.json", catalog)
    write_json(output / "new_strategy_catalog.json", new_strategies)
    write_json(output / "all_strategy_catalog.json", old_catalog + new_strategies)
    for name, frame in (("features", features), ("future_features", future_features), ("opportunities", opportunities)):
        save(output, name, frame)
    for name, frame in details.items(): save(output, name, frame)
    _, coverage = coverage_summary(details, features)
    save(output, "feature_coverage", coverage)
    versions = {name: version(name) for name in ("numpy", "pandas", "scipy", "scikit-learn", "pyarrow", "joblib", "matplotlib", "plotly", "reportlab", "python-docx", "XlsxWriter", "pypdf")}
    provenance = {"started_at_utc": start.isoformat(), "python": platform.python_version(), "versions": versions,
        "protocol_commitment": commitment, "original_live_ledger_sha256": old_live,
        "inputs_and_code_sha256": {p.relative_to(ROOT).as_posix(): value for p, value in before.items()},
        "historical_evaluation_is_new_holdout": False, "current_outcomes_used_for_fitting": False}
    write_json(output / "source_provenance.json", provenance)
    print("Fitting eight fixed model variants over four chronological folds", flush=True)
    learned = train_rolling(features, groups, output / "rolling_models")
    primary = learned["predictions"].copy()
    primary["model_key"] = [model_key(g, f) for g, f in zip(primary.feature_group, primary.model_type)]
    labels = {r["model_key"]: r["label"] for r in catalog["models"]}
    primary["label"] = primary.model_key.map(labels)
    predictions = pd.concat([primary, benchmarks], ignore_index=True)
    save(output, "predictions", predictions)
    pooled, seasonal = scored_tables(predictions)
    save(output, "model_metrics_pooled", pooled); save(output, "model_metrics_seasonal", seasonal)
    pairs = pd.concat([learned["paired_feature_comparisons"], market_comparisons(primary, predictions)], ignore_index=True)
    save(output, "paired_feature_comparisons", pairs)
    for name in ("tuning_trials", "fitted_choices", "chronological_roles", "logistic_coefficients"):
        save(output, name, learned[name])
    observed = details["target_coverage"].groupby("match_id").agg(min_prior=("observed_matches5", "min"), min_xi=("xi_selected_players", "min"))
    complete = set(observed.index[observed.min_prior.ge(3) & observed.min_xi.ge(9)])
    sensitivity = predictions.loc[predictions.match_id.isin(complete)]
    subset_pool, subset_season = scored_tables(sensitivity)
    save(output, "coverage_subset_scores", pd.concat([subset_pool, subset_season], ignore_index=True))
    print("Fitting separate future bundles without 2026 fitting outcomes", flush=True)
    future_metadata = fit_future(features, groups, output / "future_models")
    future = predict_future(future_metadata, future_features, artifact_root=output / "future_models")
    future["model_key"] = [model_key(g, f) for g, f in zip(future.feature_group, future.model_type)]
    future = release_future(output, future, future_features, future_metadata, catalog, commitment)
    save(output, "future_predictions", future)
    print("Replaying every new strategy with complete gain/loss/frequency metrics", flush=True)
    tables = run_accounts(new_strategies, primary, opportunities, bootstrap_samples=bootstrap_samples)
    for name, frame in tables.items(): save(output, name, frame)
    save(output, "season_stability", season_stability(tables["metrics_seasonal"], tables["metrics_continuous"]))
    for name, graph in combined_graphs(tables, ROOT).items(): graph.to_csv(output / (name + ".csv"), index=False)
    status = {"as_of_utc": datetime.now(timezone.utc).isoformat(), "protocol": commitment,
        "new_model_variants": 8, "player_based_variants": 6, "matched_team_controls": 2,
        "rolling_model_bundles": 32, "future_model_bundles": 8, "tuning_trials": 96,
        "historical_player_rows": int(players.season.lt("2026-27").sum()), "player_history_rows": len(players),
        "historical_feature_rows": len(features), "evaluation_matches": 1470, "new_strategies": 32,
        "all_single_season_strategies": 116, "all_continuous_strategies": 88,
        "new_metric_rows": 192, "new_future_predictions": len(future), "new_future_fixtures": len(targets),
        "future_outcomes_scored": 0, "existing_live_ledgers_unchanged": True,
        "historical_results_are_exploratory": True, "new_betting_rule_selected": False,
        "prospective_trading_performance_available": False, "position_publication_times_verified": False}
    write_json(output / "study_status.json", status)
    write_json(output / "independent_audit.json", audit_export(output))
    from .report import build_report
    report = build_report(output)
    changed = [p.relative_to(ROOT).as_posix() for p, value in before.items() if not p.exists() or sha(p) != value]
    if changed or inventory != set(code_paths()): raise RuntimeError("A protected source or implementation changed during the build: " + str(changed))
    manifest = {**provenance, "completed_at_utc": datetime.now(timezone.utc).isoformat(), "protected_hashes_unchanged": True,
        "report": report, "row_counts": {name: len(frame) for name, frame in tables.items()},
        "prediction_rows": len(predictions), "new_forecast_count": len(future),
        "output_sha256": {p.relative_to(output).as_posix(): sha(p) for p in sorted(output.rglob("*")) if p.is_file()}}
    write_json(output / "manifest.json", manifest)
    if update_latest: publish_latest(output)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--bootstrap-samples", type=int, default=1000)
    parser.add_argument("--update-latest", action="store_true")
    args = parser.parse_args()
    result = build(args.output, update_latest=args.update_latest, bootstrap_samples=args.bootstrap_samples)
    print(json.dumps({"completed_at_utc": result["completed_at_utc"], "new_forecasts": result["new_forecast_count"],
        "rows": result["row_counts"], "report": result["report"]}, indent=2))


if __name__ == "__main__": main()
