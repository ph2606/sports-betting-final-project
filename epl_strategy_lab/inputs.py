"""Read and reconcile frozen 2025--26 predictions without fitting any model."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


SEASON = "2025-26"
EXPECTED_MATCH_COUNT = 374
PROBABILITY_COLUMNS = ["p_H", "p_D", "p_A"]
SOURCE_FILES = (
    "epl_modeling/results/predictions.parquet",
    "epl_modeling/ablation_results/predictions.parquet",
    "epl_modeling/results/bookmaker_odds_panel.parquet",
    "epl_modeling/results/run_metadata.json",
    "epl_modeling/results/locked_choices.json",
    "epl_modeling/results/threshold_validation.csv",
    "epl_modeling/results/bets.parquet",
    "epl_modeling/ablation_results/bets.parquet",
)
ABLATION_MODELS = {
    ("team", "logistic"): "logit_team_only",
    ("team_xg", "logistic"): "logit_team_xg",
    ("team_player", "logistic"): "logit_team_players",
    ("combined", "logistic"): "logit_combined",
    ("team", "market_residual"): "residual_team_only",
    ("team_xg", "market_residual"): "residual_team_xg",
    ("team_player", "market_residual"): "residual_team_players",
    ("combined", "market_residual"): "residual_combined",
    ("class_frequency", "baseline"): "baseline_class_frequency",
    ("market_only", "baseline"): "baseline_market_only",
    ("market_only", "market_temperature"): "market_temperature",
}


def _required(frame: pd.DataFrame, columns: list[str], label: str) -> None:
    missing = sorted(set(columns) - set(frame))
    if missing:
        raise ValueError(f"{label} missing columns: {missing}")


def _identity(frame: pd.DataFrame, label: str) -> pd.DataFrame:
    _required(frame, ["match_id", "match_date", "season", "result"], label)
    result = frame.copy()
    if result.match_id.isna().any() or result.match_id.astype(str).str.strip().eq("").any():
        raise ValueError(f"{label} contains missing match IDs")
    if result.match_id.duplicated().any():
        raise ValueError(f"{label} contains duplicate match IDs")
    result["match_date"] = pd.to_datetime(
        result.match_date.astype("string").str[:10], format="%Y-%m-%d", errors="raise"
    )
    if result.match_date.isna().any() or not result.season.eq(SEASON).all():
        raise ValueError(f"{label} contains missing dates or a different season")
    if not result.result.isin(list("HDA")).all():
        raise ValueError(f"{label} contains invalid results")
    if not result.match_date.between("2025-08-15", "2026-05-24").all():
        raise ValueError(f"{label} contains dates outside the common season window")
    return result


def _probabilities(frame: pd.DataFrame, label: str) -> None:
    _required(frame, PROBABILITY_COLUMNS, label)
    try:
        values = frame[PROBABILITY_COLUMNS].to_numpy(dtype=float)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} contains nonnumeric probabilities") from exc
    if not np.isfinite(values).all() or not ((values >= 0) & (values <= 1)).all():
        raise ValueError(f"{label} contains invalid probabilities")
    if not np.allclose(values.sum(axis=1), 1.0, atol=1e-10, rtol=0):
        raise ValueError(f"{label} probabilities do not sum to one")


def _align(frame: pd.DataFrame, opportunities: pd.DataFrame, label: str) -> pd.DataFrame:
    frame = _identity(frame, label)
    _probabilities(frame, label)
    if set(frame.match_id) != set(opportunities.match_id):
        missing = set(opportunities.match_id) - set(frame.match_id)
        extra = set(frame.match_id) - set(opportunities.match_id)
        raise ValueError(f"{label} population differs: {len(missing)} missing and {len(extra)} extra matches")
    native = frame.set_index("match_id").reindex(opportunities.match_id).reset_index()
    for column in ("match_date", "season", "result"):
        if not native[column].reset_index(drop=True).eq(opportunities[column].reset_index(drop=True)).all():
            raise ValueError(f"{label} {column} conflicts with the price panel")
    return native[["match_id", *PROBABILITY_COLUMNS]].copy()


def load_inputs(root: Path) -> tuple[dict[str, pd.DataFrame], pd.DataFrame, list[Path]]:
    """Return 16 aligned series, their common price panel, and immutable sources.

    Source match IDs, result labels and printed calendar dates must agree across
    all 13 original series. The three ensembles are deterministic averages of
    saved probabilities. No intersection silently drops problematic matches.
    """
    root = Path(root).resolve()
    if not (root / "epl_modeling").is_dir() and (root / "final_project/epl_modeling").is_dir():
        root = root / "final_project"
    source_paths = [root / relative for relative in SOURCE_FILES]
    for path in source_paths:
        if not path.is_file():
            raise FileNotFoundError(path)
    first, ablation, prices = [pd.read_parquet(path) for path in source_paths[:3]]
    locks = json.loads(source_paths[3].read_text(encoding="utf-8"))
    _required(first, ["season", "split", "branch", "family"], "First-study predictions")
    _required(ablation, ["season", "outer_season", "feature_group", "model_type"], "Ablation predictions")
    _required(prices, ["season"], "Price panel")
    opportunities = _identity(prices.loc[prices.season.eq(SEASON)], "Price panel")
    opportunities = opportunities.sort_values(["match_date", "match_id"], kind="stable").reset_index(drop=True)
    if len(opportunities) != EXPECTED_MATCH_COUNT:
        raise ValueError(f"Expected {EXPECTED_MATCH_COUNT} common season matches, found {len(opportunities)}")
    odds_columns = [f"{prefix}odds_{outcome}" for prefix in ("", "ref_") for outcome in "HDA"]
    _required(opportunities, odds_columns + ["snapshot_type", "reference_bookmaker"] +
              [f"bookmaker_{outcome}" for outcome in "HDA"], "Price panel")
    try:
        odds_values = opportunities[odds_columns].to_numpy(float)
    except (TypeError, ValueError) as exc:
        raise ValueError("Price panel contains nonnumeric odds") from exc
    if not np.isfinite(odds_values).all() or not (odds_values > 1).all():
        raise ValueError("Price panel contains incomplete or invalid decimal odds")
    if not opportunities.snapshot_type.eq("preclosing").all():
        raise ValueError("The common replay requires the saved preclosing price panel")
    if not opportunities.reference_bookmaker.eq("Bet365").all():
        raise ValueError("The saved reference bookmaker must be Bet365")
    for column in [f"bookmaker_{outcome}" for outcome in "HDA"]:
        if opportunities[column].isna().any() or opportunities[column].astype(str).str.strip().eq("").any():
            raise ValueError("A selected bookmaker identity is missing")
    first = first.loc[first.season.eq(SEASON) & first.split.eq("test")]
    if set(first.branch) != {"accuracy", "calibration"}:
        raise ValueError("Both frozen first-study test branches must be present")
    frozen = locks.get("frozen_choices", {})
    if json.loads(source_paths[4].read_text(encoding="utf-8")) != frozen:
        raise ValueError("The saved locked choices and run metadata disagree")
    if frozen.get("families") != {"accuracy": "svm", "calibration": "mlp"}:
        raise ValueError("First-study selected model identities changed")
    for branch in ("accuracy", "calibration"):
        lock = frozen.get("thresholds", {}).get(branch, {})
        if lock.get("reason") != "no_admissible_positive_validation_strategy" or lock.get("threshold") != 1000000.0:
            raise ValueError("The frozen primary no-bet threshold lock changed")
    diagnostics = pd.read_csv(source_paths[5])
    _required(diagnostics, ["branch", "threshold"], "Historical threshold diagnostics")
    expected_diagnostics = {(branch, threshold) for branch in ("accuracy", "calibration")
                            for threshold in (0.0, 0.025, 0.05, 0.075, 0.1, 0.15, 0.2)}
    if diagnostics.duplicated(["branch", "threshold"]).any() or set(
            diagnostics[["branch", "threshold"]].itertuples(index=False, name=None)) != expected_diagnostics:
        raise ValueError("The historical threshold diagnostic rule identities changed")
    models: dict[str, pd.DataFrame] = {}
    for branch, family in frozen["families"].items():
        frame = first.loc[first.branch.eq(branch)]
        if not frame.family.eq(family).all():
            raise ValueError(f"First-study {branch} family differs from its frozen identity")
        models[f"first_{branch}"] = _align(frame, opportunities, f"First-study {branch}")
    affected = ablation.season.eq(SEASON) | ablation.outer_season.eq(SEASON)
    ablation = ablation.loc[affected]
    if not (ablation.season.eq(SEASON) & ablation.outer_season.eq(SEASON)).all():
        raise ValueError("Ablation season and outer-season identities disagree")
    variants = set(ablation[["feature_group", "model_type"]].itertuples(index=False, name=None))
    if variants != set(ABLATION_MODELS):
        raise ValueError("The eleven frozen ablation model identities changed")
    for (group, family), key in ABLATION_MODELS.items():
        frame = ablation.loc[ablation.feature_group.eq(group) & ablation.model_type.eq(family)]
        models[key] = _align(frame, opportunities, f"Ablation {group}/{family}")
    reference_columns = [f"ref_p_{outcome}" for outcome in "HDA"]
    _required(opportunities, reference_columns, "Price panel")
    if not np.allclose(models["baseline_market_only"][PROBABILITY_COLUMNS].to_numpy(float),
                       opportunities[reference_columns].to_numpy(float), atol=1e-12, rtol=0):
        raise ValueError("Raw-market predictions differ from the saved reference probabilities")
    groups = {
        "ensemble_logit4": [f"logit_{name}" for name in ("team_only", "team_xg", "team_players", "combined")],
        "ensemble_learned8": [f"{family}_{name}" for family in ("logit", "residual")
                               for name in ("team_only", "team_xg", "team_players", "combined")],
        "ensemble_market_blend": ["logit_combined", "baseline_market_only"],
    }
    for key, members in groups.items():
        combined = pd.DataFrame({"match_id": opportunities.match_id})
        combined[PROBABILITY_COLUMNS] = np.mean(
            np.stack([models[member][PROBABILITY_COLUMNS].to_numpy(float) for member in members]), axis=0
        )
        _probabilities(combined, key)
        models[key] = combined
    return models, opportunities, source_paths
