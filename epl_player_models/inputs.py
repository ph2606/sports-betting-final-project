"""Frozen common fixtures, complete player-source inventory and future targets."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from epl_live.ledger import read_forecasts
from epl_modeling.ablation import TEAM_PERFORMANCE, TEAM_FLAGS
from epl_strategy_validation.inputs import load_inputs as load_frozen_rolling

ROOT = Path(__file__).resolve().parents[1]
LIVE_SNAPSHOT = Path("epl_live/snapshots/20261020T223053.930369Z_299021e7c7")
LIVE_RUN = Path("epl_live/runs/20261020T223825.164001Z")
PRIOR = Path("epl_prospective/results/20261020_first_outcomes")
TEAM_COLUMNS = TEAM_PERFORMANCE + TEAM_FLAGS
FEATURE_SOURCE = Path("epl_modeling/ablation_results/modeling_matches.parquet")
BENCHMARKS = {
    ("market_only", "baseline"): ("benchmark_market", "Raw de-vigged Bet365 market"),
    ("market_only", "market_temperature"): ("benchmark_market_temperature", "Temperature-calibrated market"),
    ("class_frequency", "baseline"): ("benchmark_class_frequency", "Historical fitting-class frequency"),
    ("team", "logistic"): ("benchmark_legacy_team", "Legacy team logistic with original source controls"),
    ("team_player", "logistic"): ("benchmark_legacy_team_player", "Legacy team + seven FPL aggregates logistic"),
}


def source_paths(root=ROOT):
    root = Path(root)
    files = [root / FEATURE_SOURCE, root / "epl_modeling/ablation_results/predictions.parquet",
        root / "epl_modeling/results/bookmaker_odds_panel.parquet", root / "epl_live/forecasts.jsonl",
        root / "epl_live/outcomes.jsonl", root / "epl_data/metadata/current_teams.csv"]
    archive = root / "epl_data/data/raw/fpl_archive"
    for pattern in ("*/gws/merged_gw.csv", "*/teams.csv", "*/fixtures.csv", "*/players_raw.csv"):
        files.extend(archive.glob(pattern))
    files.extend((root / "epl_data/data/raw/football_data").glob("*/E0.csv"))
    files.extend(p for p in (root / LIVE_SNAPSHOT).rglob("*") if p.is_file())
    files.extend(p for p in (root / LIVE_RUN).rglob("*") if p.is_file())
    prior = root / PRIOR
    files.extend(p for p in prior.rglob("*") if p.is_file())
    registry = json.loads((prior / "report/report_manifest.json").read_text(encoding="utf-8"))["inputs"]
    files.extend(root / path for path in registry)
    for folder, names in (("epl_strategy_lab/results/20261015T040052Z_100k84", ("catalog.json", "equity.parquet", "metrics.parquet")),
            ("epl_strategy_validation/results/20261015_temporal_selection", ("equity_continuous.parquet", "metrics_continuous.parquet"))):
        files.extend(root / folder / name for name in names)
    return sorted(set(files))


def load_base(root=ROOT):
    root = Path(root)
    base = pd.read_parquet(root / FEATURE_SOURCE)
    base["match_date"] = pd.to_datetime(base.match_date).dt.normalize()
    base = base.loc[base.season.between("2016-17", "2025-26")].copy()
    if base.match_id.duplicated().any() or not base.result.isin(list("HDA")).all():
        raise ValueError("Invalid historical modeling identities")
    _, opportunities, _ = load_frozen_rolling(root)
    recent = base.loc[base.season.ge("2022-23")].set_index("match_id").reindex(opportunities.match_id)
    if len(recent) != 1470 or recent.season.isna().any(): raise ValueError("Player study changes the common 1,470-fixture population")
    for column in ("match_date", "season", "result"):
        if not recent[column].reset_index(drop=True).equals(opportunities[column].reset_index(drop=True)):
            raise ValueError("Frozen historical identity differs: " + column)
    # The frozen price panel stores native match IDs, dates and results; club
    # names come from its exact identity join to the saved modeling frame.
    for column in ("home_team", "away_team"):
        opportunities[column] = recent[column].to_numpy()
    targets = pd.read_parquet(root / LIVE_RUN / "target_fixtures.parquet")
    targets["match_date"] = pd.to_datetime(targets.match_date).dt.normalize()
    if len(targets) != 10 or targets.match_id.duplicated().any(): raise ValueError("The new forecast cohort requires ten native future targets")
    run = json.loads((root / LIVE_RUN / "run_summary.json").read_text())
    records = [record for record in read_forecasts(root / "epl_live/forecasts.jsonl")
        if record["model_id"] == "prospective_v1_logistic_team" and record["match_id"] in set(targets.match_id)
        and pd.Timestamp(record["created_at_utc"]) <= pd.Timestamp(run["created_at_utc"])]
    if len(records) != 10 or len({r["match_id"] for r in records}) != 10:
        raise ValueError("Saved pre-kickoff team inputs do not cover the exact new future cohort")
    by_id = {r["match_id"]: r for r in records}
    for row in targets.to_dict("records"):
        saved = by_id[row["match_id"]]
        for name in ("home_team", "away_team", "season", "kickoff_utc"):
            if saved[name] != row[name]: raise ValueError("Saved future team input identity differs")
        if pd.Timestamp(saved["created_at_utc"]) >= pd.Timestamp(saved["kickoff_utc"]):
            raise ValueError("Future team inputs were not recorded before kickoff")
    for column in TEAM_COLUMNS:
        targets[column] = targets.match_id.map({mid: record["features"][column] for mid, record in by_id.items()})
    # Preserve FD evidence clocks independently of the new player feature clocks.
    for side in ("home", "away"):
        column = f"audit_{side}_fd_latest_prior_date"
        targets[column] = targets.match_id.map({mid: record["latest_feature_match_dates"].get(column) for mid, record in by_id.items()})
        latest = pd.to_datetime(targets[column])
        if (latest.notna() & latest.ge(targets.match_date)).any(): raise ValueError("Non-prior saved team context")
    old = pd.read_parquet(root / "epl_modeling/ablation_results/predictions.parquet")
    benchmarks = []
    for (group, family), (key, label) in BENCHMARKS.items():
        one = old.loc[old.feature_group.eq(group) & old.model_type.eq(family)].copy()
        one["model_key"], one["label"] = key, label
        if len(one) != 1470 or one.match_id.duplicated().any(): raise ValueError("Incomplete frozen benchmark " + key)
        one["match_date"] = pd.to_datetime(one.match_date)
        benchmarks.append(one)
    return base, targets, opportunities, pd.concat(benchmarks, ignore_index=True), by_id


def merge_player_features(base, targets, player_features, metadata):
    coverage = list(metadata["feature_groups"]["coverage"])
    form = list(dict.fromkeys(coverage + metadata["feature_groups"]["player_form"]))
    squad = list(dict.fromkeys(coverage + metadata["feature_groups"]["player_squad"]))
    groups = {"team_control": TEAM_COLUMNS + coverage, "player_form": form,
        "player_squad": squad, "team_player_squad": TEAM_COLUMNS + squad}
    if {key: len(value) for key, value in groups.items()} != {"team_control": 19, "player_form": 96, "player_squad": 222, "team_player_squad": 235}:
        raise AssertionError("Feature dimensions differ from the pre-fitting committed protocol")
    if player_features.match_id.duplicated().any() or set(player_features.match_id) != set(base.match_id) | set(targets.match_id):
        raise AssertionError("Player engineering omits, duplicates or adds target identities")
    columns = [column for column in player_features if column.startswith(("feat_player_", "audit_player_"))]
    addition = player_features[["match_id"] + columns]
    identity = player_features.set_index("match_id")
    results = []
    for frame in (base, targets):
        for column in ("season", "match_date", "home_team", "away_team"):
            if not frame[column].reset_index(drop=True).equals(identity.reindex(frame.match_id)[column].reset_index(drop=True)):
                raise AssertionError("Engineered player identity conflict: " + column)
        keep = [column for column in ("match_id", "season", "match_date", "home_team", "away_team", "result", "kickoff_utc", "fpl_fixture_id",
            "audit_home_fd_latest_prior_date", "audit_away_fd_latest_prior_date", "ref_p_H", "ref_p_D", "ref_p_A") if column in frame]
        merged = frame[keep + TEAM_COLUMNS].merge(addition, on="match_id", validate="one_to_one")
        for column in columns:
            if column.startswith("audit_player_"):
                latest = pd.to_datetime(merged[column])
                if (latest.notna() & latest.ge(merged.match_date)).any(): raise AssertionError("A player feature uses the target date or later")
        results.append(merged)
    return *results, groups
