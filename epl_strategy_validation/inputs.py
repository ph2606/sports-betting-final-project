"""Reconcile four frozen rolling seasons without fitting or selecting models."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from epl_strategy_lab.catalog import build_catalog
from epl_strategy_lab.inputs import ABLATION_MODELS, PROBABILITY_COLUMNS


SEASONS = ("2022-23", "2023-24", "2024-25", "2025-26")
SEASON_MATCH_COUNTS = dict(zip(SEASONS, (368, 360, 368, 374)))
SEASON_DATE_COUNTS = dict(zip(SEASONS, (117, 116, 107, 113)))
SEASON_DATE_WINDOWS = {
    "2022-23": ("2022-08-05", "2023-05-28"),
    "2023-24": ("2023-08-11", "2024-05-19"),
    "2024-25": ("2024-08-16", "2025-05-25"),
    "2025-26": ("2025-08-15", "2026-05-24"),
}
EXPECTED_MATCH_COUNT = 1470
EXPECTED_DATE_COUNT = 453
LAB_EXPORT_RELATIVE = Path("epl_strategy_lab/results/20261015T040052Z_100k84")
CATALOG_RELATIVE = LAB_EXPORT_RELATIVE / "catalog.json"
SOURCE_FILES = (
    "epl_modeling/ablation_results/predictions.parquet",
    "epl_modeling/results/bookmaker_odds_panel.parquet",
)
ENSEMBLE_MEMBERS = {
    "ensemble_logit4": [f"logit_{name}" for name in ("team_only", "team_xg", "team_players", "combined")],
    "ensemble_learned8": [f"{family}_{name}" for family in ("logit", "residual")
                          for name in ("team_only", "team_xg", "team_players", "combined")],
    "ensemble_market_blend": ["logit_combined", "baseline_market_only"],
}


def project_root(root: Path) -> Path:
    root = Path(root).resolve()
    if not (root / "epl_modeling").is_dir() and (root / "final_project/epl_modeling").is_dir():
        root = root / "final_project"
    return root


def _required(frame: pd.DataFrame, columns: list[str], label: str) -> None:
    missing = sorted(set(columns) - set(frame))
    if missing:
        raise ValueError(f"{label} missing columns: {missing}")


def validate_opportunities(frame: pd.DataFrame, *, exact_population: bool = False) -> pd.DataFrame:
    """Return validated real identities; never relabel a season for the engine.

    Exact population checking is used for the source reconciliation. A replay
    may instead use any nonempty subset of these four real season windows.
    """
    _required(frame, ["match_id", "match_date", "season", "result"], "Opportunities")
    native = frame.copy(deep=True)
    if native.empty:
        raise ValueError("Opportunities must be nonempty")
    native["match_id"] = native.match_id.astype("string")
    if native.match_id.isna().any() or native.match_id.str.strip().eq("").any() or native.match_id.duplicated().any():
        raise ValueError("Opportunity match IDs must be present and unique")
    native["match_date"] = pd.to_datetime(native.match_date.astype("string").str[:10],
                                           format="%Y-%m-%d", errors="raise")
    if native.match_date.isna().any() or not native.result.isin(list("HDA")).all():
        raise ValueError("Missing match dates or invalid H/D/A results")
    if not native.season.isin(SEASONS).all():
        raise ValueError("Opportunity seasons must be the four frozen rolling evaluation seasons")
    for season, part in native.groupby("season", sort=False):
        first, last = SEASON_DATE_WINDOWS[season]
        if not part.match_date.between(first, last).all():
            raise ValueError(f"Opportunity date conflicts with its real season {season}")
    if native.groupby("match_date").season.nunique().gt(1).any():
        raise ValueError("A calendar date cannot belong to multiple seasons")
    native = native.sort_values(["match_date", "match_id"], kind="stable").reset_index(drop=True)
    if exact_population:
        if native.groupby("season").size().to_dict() != SEASON_MATCH_COUNTS:
            raise ValueError("The frozen 368/360/368/374 season populations changed")
        if native.groupby("season").match_date.nunique().to_dict() != SEASON_DATE_COUNTS:
            raise ValueError("The frozen 117/116/107/113 season date populations changed")
        if len(native) != EXPECTED_MATCH_COUNT or native.match_date.nunique() != EXPECTED_DATE_COUNT:
            raise ValueError("Expected exactly 1,470 fixtures and 453 match dates")
        for season, part in native.groupby("season"):
            observed = (str(part.match_date.min().date()), str(part.match_date.max().date()))
            if observed != SEASON_DATE_WINDOWS[season]:
                raise ValueError(f"Frozen date endpoints changed for {season}")
    return native


def _probabilities(frame: pd.DataFrame, columns: list[str], label: str) -> np.ndarray:
    _required(frame, columns, label)
    try:
        values = frame[columns].to_numpy(dtype=float)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{label} contains nonnumeric probabilities") from error
    if not np.isfinite(values).all() or not ((values >= 0) & (values <= 1)).all():
        raise ValueError(f"{label} contains invalid probabilities")
    if not np.allclose(values.sum(axis=1), 1.0, atol=1e-10, rtol=0):
        raise ValueError(f"{label} probabilities do not sum to one")
    return values


def compatible_catalog(root: Path) -> tuple[list[dict], list[dict]]:
    """Read all frozen rules and retain precisely S017--S072, unchanged.

    The 28 excluded first-study rules use model choices informed by earlier
    seasons. Their 2025 artifact is preserved, rather than backfilled with
    models that would have seen the earlier evaluation outcomes.
    """
    path = project_root(root) / CATALOG_RELATIVE
    frozen = json.loads(path.read_text(encoding="utf-8"))
    if frozen != build_catalog():
        raise ValueError("The saved 84-rule catalog differs from the declared frozen laboratory catalog")
    eligible = [row for row in frozen if not row["model_key"].startswith("first_")]
    if [row["strategy_id"] for row in eligible] != [f"S{i:03d}" for i in range(17, 73)]:
        raise ValueError("Expected exactly the unchanged compatible rules S017--S072")
    # Independent objects protect all84 when downstream callers annotate a row.
    return frozen, json.loads(json.dumps(eligible, allow_nan=False))


def load_inputs(root: Path) -> tuple[dict[str, pd.DataFrame], pd.DataFrame, list[Path]]:
    """Return 14 aligned probability series and all 1,470 native quote rows.

    Every original series must have exactly every quoted fixture in all four
    years. No inner join can silently discard an absent or conflicting match.
    The returned inventory contains only the two source files actually read.
    """
    root = project_root(root)
    source_paths = [root / relative for relative in SOURCE_FILES]
    for path in source_paths:
        if not path.is_file():
            raise FileNotFoundError(path)
    predictions, prices = [pd.read_parquet(path) for path in source_paths]
    _required(predictions, ["match_id", "match_date", "season", "outer_season", "result",
                             "feature_group", "model_type", *PROBABILITY_COLUMNS], "Rolling predictions")
    _required(prices, ["season"], "Price panel")
    if not predictions.season.eq(predictions.outer_season).all() or set(predictions.outer_season) != set(SEASONS):
        raise ValueError("Rolling prediction season and outer-season identities changed")
    variants = set(predictions[["feature_group", "model_type"]].itertuples(index=False, name=None))
    if variants != set(ABLATION_MODELS):
        raise ValueError("The eleven frozen rolling prediction identities changed")
    opportunities = validate_opportunities(prices.loc[prices.season.isin(SEASONS)], exact_population=True)
    odds_columns = [f"{prefix}odds_{outcome}" for prefix in ("", "ref_") for outcome in "HDA"]
    _required(opportunities, odds_columns + ["snapshot_type", "reference_bookmaker"] +
              [f"bookmaker_{outcome}" for outcome in "HDA"], "Price panel")
    try:
        odds_values = opportunities[odds_columns].to_numpy(float)
    except (TypeError, ValueError) as error:
        raise ValueError("Price panel contains nonnumeric odds") from error
    if not np.isfinite(odds_values).all() or not (odds_values > 1).all():
        raise ValueError("Price panel contains incomplete or invalid decimal odds")
    if not opportunities.snapshot_type.eq("preclosing").all():
        raise ValueError("The rolling replay requires the saved preclosing price panel")
    if not opportunities.reference_bookmaker.eq("Bet365").all():
        raise ValueError("The reference bookmaker must remain Bet365")
    for column in [f"bookmaker_{outcome}" for outcome in "HDA"]:
        if opportunities[column].isna().any() or opportunities[column].astype(str).str.strip().eq("").any():
            raise ValueError("An individual-book quote lacks its bookmaker identity")
    models = {}
    for (group, family), key in ABLATION_MODELS.items():
        frame = validate_opportunities(predictions.loc[
            predictions.feature_group.eq(group) & predictions.model_type.eq(family)], exact_population=True)
        _probabilities(frame, PROBABILITY_COLUMNS, key)
        if set(frame.match_id) != set(opportunities.match_id):
            raise ValueError(f"{key} differs from the complete quoted match population")
        aligned = frame.set_index("match_id").reindex(opportunities.match_id).reset_index()
        for column in ("match_date", "season", "result"):
            if not aligned[column].reset_index(drop=True).eq(opportunities[column]).all():
                raise ValueError(f"{key} {column} conflicts with the native price panel")
        models[key] = aligned[["match_id", *PROBABILITY_COLUMNS]].copy()
    reference = _probabilities(opportunities, [f"ref_p_{outcome}" for outcome in "HDA"], "Reference market")
    if not np.allclose(models["baseline_market_only"][PROBABILITY_COLUMNS].to_numpy(float),
                       reference, atol=1e-12, rtol=0):
        raise ValueError("Raw market predictions differ from the native reference probabilities")
    for key, members in ENSEMBLE_MEMBERS.items():
        combined = pd.DataFrame({"match_id": opportunities.match_id})
        combined[PROBABILITY_COLUMNS] = np.mean(np.stack([
            models[member][PROBABILITY_COLUMNS].to_numpy(float) for member in members]), axis=0)
        _probabilities(combined, PROBABILITY_COLUMNS, key)
        models[key] = combined
    if len(models) != 14 or any(key.startswith("first_") for key in models):
        raise AssertionError("The source inventory must contain eleven rolling series and three ensembles")
    return models, opportunities, source_paths
