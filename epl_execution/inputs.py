"""Reconcile the complete frozen 84-rule and 56-rule original accounts.

No model is fitted and no historical bet is inferred from a summary. Both
saved prediction inventories must agree on their entire 2025 overlap, and
every original account is checked against its native opportunities, quotes,
probabilities, date cashflows and recorded metrics before a new replay.
"""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import numpy as np
import pandas as pd

from epl_strategy.metrics import enrich_bets
from epl_strategy_lab.inputs import (PROBABILITY_COLUMNS, SOURCE_FILES as LAB_SOURCE_FILES,
                                     load_inputs as load_single)
from epl_strategy_validation.inputs import (LAB_EXPORT_RELATIVE, SEASONS,
    SOURCE_FILES as ROLLING_SOURCE_FILES, compatible_catalog, load_inputs as load_rolling,
    project_root)


TEMPORAL_EXPORT_RELATIVE = Path("epl_strategy_validation/results/20261015_temporal_selection")
INITIAL = 100000.0
ALL_IDS = [f"S{i:03d}" for i in range(1, 85)]
COMPATIBLE_IDS = [f"S{i:03d}" for i in range(17, 73)]
CONFIG_FIELDS = ("model_key", "selection_rule", "odds_mode", "staking", "cash_only", "min_edge",
                 "kelly_fraction", "max_bet_fraction", "date_cap_fraction", "fixed_stake", "bankroll_fraction",
                 "allowed_outcomes", "min_odds", "max_odds", "consensus_min", "consensus_model_keys")


def source_paths(root: Path) -> list[Path]:
    """Return the complete frozen data/report inventory before anything loads.

    Include inputs consumed later by the combined report and the two closing
    diagnostic source tables. The caller separately hashes imported module
    code and current-stage documents. No mutable latest-report copy is read.
    """
    root = project_root(root)
    paths = [root / item for item in (*LAB_SOURCE_FILES, *ROLLING_SOURCE_FILES)]
    lab, temporal = root / LAB_EXPORT_RELATIVE, root / TEMPORAL_EXPORT_RELATIVE
    paths += [lab / name for name in ("catalog.json", "metrics.parquet", "bets.parquet", "equity.parquet", "manifest.json")]
    paths += [temporal / name for name in (
        "catalog.json", "compatible_catalog.json", "metrics_continuous.parquet", "metrics_seasonal.parquet",
        "bets_continuous.parquet", "equity_continuous.parquet", "bets_seasonal.parquet", "equity_seasonal.parquet",
        "season_stability.parquet", "selection_comparison.parquet", "selection_global.parquet",
        "graph_equity_continuous.csv", "figures/all_strategies_4seasons_100k.png",
        "figures/all_84_strategies_2025_100k.png", "manifest.json")]
    paths += [root / "epl_data/data/processed/football_data" / name for name in (
        "match_odds_1x2_long.parquet", "matches_current_cohort.parquet")]
    return sorted(set(paths))


def _required(frame, columns, label):
    missing = sorted(set(columns) - set(frame))
    if missing:
        raise ValueError(label + " missing columns: " + str(missing))


def _near(left, right, label):
    if not np.allclose(np.asarray(left, float), np.asarray(right, float), atol=1e-6, rtol=1e-10, equal_nan=True):
        raise ValueError(label + " identity does not reconcile")


def _matching_config(metric, config):
    for name in CONFIG_FIELDS:
        if name not in metric:
            raise ValueError("Original metric lacks frozen config field " + name)
        saved, expected = metric[name], config[name]
        if isinstance(expected, (list, dict)):
            if isinstance(saved, str):
                saved = json.loads(saved)
            if saved != expected:
                raise ValueError("Original metric changes frozen config field " + name)
        elif expected is None:
            if saved is not None and not pd.isna(saved):
                raise ValueError("Original metric changes frozen config field " + name)
        elif saved != expected:
            raise ValueError("Original metric changes frozen config field " + name)


def _metric_population(frame, expected_ids, *, seasonal=False):
    _required(frame, ["strategy_id"], "Original metrics")
    keys = ["strategy_id", "season"] if seasonal else ["strategy_id"]
    _required(frame, keys, "Original metrics")
    if frame.duplicated(keys).any() or set(frame.strategy_id) != set(expected_ids):
        raise ValueError("Original metric strategy population is missing, repeated or changed")
    expected_count = len(expected_ids) * (len(SEASONS) if seasonal else 1)
    if len(frame) != expected_count:
        raise ValueError("Original metric account count changed")
    if seasonal and (set(frame.season) != set(SEASONS) or not frame.groupby("strategy_id").size().eq(4).all()):
        raise ValueError("Original seasonal metric population changed")


def _frame_membership(frame, ids, label):
    _required(frame, ["strategy_id", "episode_id", "match_date"], label)
    if frame.strategy_id.isna().any() or not set(frame.strategy_id).issubset(set(ids)):
        raise ValueError(label + " contains an unknown strategy")
    if frame.episode_id.isna().any():
        raise ValueError(label + " contains a missing original episode")


def _check_account(config, metric, bets, equity, opportunities, models, episode):
    """Check a saved original account without regenerating its policy choices."""
    _matching_config(metric, config)
    sid, native = config["strategy_id"], opportunities.set_index("match_id")
    for count in ("prediction_count", "matched_valid_odds_count"):
        _near(metric[count], len(native), "Original " + count)
    _near(metric["initial_capital_sum_units"], INITIAL, "Original initial funding")
    _near(metric["bankroll_reset_episodes"], 1, "Original account episode count")
    if not equity.strategy_id.eq(sid).all() or not equity.episode_id.eq(episode).all():
        raise ValueError("Original equity account identity changed")
    dates = pd.DatetimeIndex(opportunities.match_date.unique()).sort_values()
    if len(equity) != len(dates) or equity.match_date.duplicated().any() or not pd.DatetimeIndex(equity.match_date).equals(dates):
        raise ValueError("Original equity omits or repeats a native priced date")
    positions = enrich_bets(bets)
    if positions.match_id.duplicated().any() or not positions.match_id.isin(native.index).all():
        raise ValueError("Original bet identities are repeated or absent from priced opportunities")
    if not positions.strategy_id.eq(sid).all() or not positions.episode_id.eq(episode).all():
        raise ValueError("Original bet account identity changed")
    _required(positions, ["selection", "result", "bookmaker"], "Original bets")
    for column in ("match_date", "result", "season"):
        if column in positions and not positions[column].eq(positions.match_id.map(native[column])).all():
            raise ValueError("Original bet " + column + " conflicts with native opportunity")
    if "season" in equity:
        season_by_date = opportunities[["match_date", "season"]].drop_duplicates().set_index("match_date").season
        if not equity.season.eq(equity.match_date.map(season_by_date)).all():
            raise ValueError("Original equity season conflicts with native opportunity")
    if len(positions):
        aligned = native.reindex(positions.match_id)
        label = positions.selection.map({label: i for i, label in enumerate("HDA")}).to_numpy(int)
        prefix = "ref_" if config["odds_mode"] == "reference" else ""
        prices = aligned[[f"{prefix}odds_{outcome}" for outcome in "HDA"]].to_numpy(float)[np.arange(len(positions)), label]
        _near(positions.odds, prices, "Original selected quote")
        model = models[config["model_key"]].set_index("match_id").reindex(positions.match_id)
        selected_p = model[PROBABILITY_COLUMNS].to_numpy(float)[np.arange(len(positions)), label]
        _near(positions.probability, selected_p, "Original selected model probability")
        books = np.repeat("Bet365", len(positions)) if prefix else aligned[[f"bookmaker_{outcome}" for outcome in "HDA"]].to_numpy()[np.arange(len(positions)), label]
        if not positions.bookmaker.eq(books).all():
            raise ValueError("Original selected bookmaker conflicts with native quote")
    curve = equity.set_index("match_date")
    daily = positions.groupby("match_date").agg(bet_count=("match_id", "size"), turnover=("stake", "sum"), profit=("profit", "sum"))
    daily = daily.reindex(dates, fill_value=0)
    _near(curve.matched_matches, opportunities.groupby("match_date").size().reindex(dates), "Original date opportunity count")
    for column in ("bet_count", "turnover", "profit"):
        _near(curve[column], daily[column], "Original date " + column)
    starts = INITIAL + daily.profit.cumsum().shift(fill_value=0)
    ends = INITIAL + daily.profit.cumsum()
    _near(curve.start_bankroll, starts, "Original date starting cash")
    _near(curve.end_bankroll, ends, "Original date closing cash")
    if (curve.turnover > curve.start_bankroll + 1e-6).any() or curve.end_bankroll.lt(-1e-6).any():
        raise ValueError("An original account is not self financing")
    for field, expected in (("bet_count", len(positions)), ("profit", positions.profit.sum()),
        ("turnover", positions.stake.sum()), ("gross_return", positions.gross_return.sum()),
        ("expected_gain_total_units", positions.expected_gain_units.sum()),
        ("expected_loss_total_units", positions.expected_loss_units.sum()),
        ("expected_net_profit_total_units", positions.expected_net_profit_units.sum()),
        ("final_capital_sum_units", ends.iloc[-1]), ("return_on_initial_capital", positions.profit.sum() / INITIAL),
        ("trading_frequency", len(positions) / len(native))):
        _near(metric[field], expected, "Original metric " + field)
    expected_hit = float(positions.won.mean()) if len(positions) else np.nan
    _near(metric["hit_ratio"], expected_hit, "Original hit ratio")
    expected_roi = float(positions.profit.sum() / positions.stake.sum()) if len(positions) else np.nan
    _near(metric["roi"], expected_roi, "Original ROI")
    wealth = np.r_[INITIAL, ends.to_numpy(float)]
    drawdown = 1 - wealth / np.maximum.accumulate(wealth)
    _near(metric["max_drawdown"], drawdown.max(), "Original max drawdown")
    _near(curve.drawdown, drawdown[1:], "Original date drawdown")


def load_inputs(root: Path) -> dict:
    root = project_root(root)
    sources = source_paths(root)
    for path in sources:
        if not path.is_file():
            raise FileNotFoundError(path)
    single_models, single_opportunities, single_sources = load_single(root)
    rolling_models, opportunities, rolling_sources = load_rolling(root)
    if not set(single_sources + rolling_sources).issubset(set(sources)):
        raise ValueError("A leaf loader consumed an unlisted frozen source")
    overlap = opportunities.loc[opportunities.season.eq("2025-26")].reset_index(drop=True)
    if set(overlap.columns) != set(single_opportunities.columns):
        raise ValueError("Single and rolling 2025 price-panel columns disagree")
    for column in overlap:
        left, right = overlap[column].reset_index(drop=True), single_opportunities[column].reset_index(drop=True)
        equal = left.eq(right) | (left.isna() & right.isna())
        if len(left) != len(right) or not equal.fillna(False).all():
            raise ValueError("Single and rolling 2025 opportunity " + column + " disagree")
    if len(single_models) != 16 or len(rolling_models) != 14 or set(single_models) - set(rolling_models) != {"first_accuracy", "first_calibration"}:
        raise ValueError("Expected fourteen rolling and two single-season first-study series")
    for key, frame in rolling_models.items():
        recent = frame.set_index("match_id").reindex(overlap.match_id)
        single = single_models[key].set_index("match_id").reindex(overlap.match_id)
        _near(recent[PROBABILITY_COLUMNS], single[PROBABILITY_COLUMNS], "Single/rolling 2025 " + key)
    models = {**rolling_models, **{key: frame for key, frame in single_models.items() if key.startswith("first_")}}
    catalog, compatible = compatible_catalog(root)
    temporal = root / TEMPORAL_EXPORT_RELATIVE
    if json.loads((temporal / "catalog.json").read_text(encoding="utf-8")) != catalog or json.loads((temporal / "compatible_catalog.json").read_text(encoding="utf-8")) != compatible:
        raise ValueError("The temporal study changes the frozen catalog or compatible membership")
    lab = root / LAB_EXPORT_RELATIVE
    tables = {"single": {name: pd.read_parquet(lab / (name + ".parquet")) for name in ("metrics", "bets", "equity")}}
    tables.update({scope: {name: pd.read_parquet(temporal / f"{name}_{scope}.parquet") for name in ("metrics", "bets", "equity")}
                   for scope in ("continuous", "seasonal")})
    for scope, group in tables.items():
        ids = ALL_IDS if scope == "single" else COMPATIBLE_IDS
        _metric_population(group["metrics"], ids, seasonal=scope == "seasonal")
        for kind in ("bets", "equity"):
            frame = group[kind]
            _frame_membership(frame, ids, "Original " + scope + " " + kind)
            frame["match_date"] = pd.to_datetime(frame.match_date.astype("string").str[:10], format="%Y-%m-%d", errors="raise")
            if frame.match_date.isna().any():
                raise ValueError("Original ledger contains missing dates")
        keys = ["strategy_id", "episode_id", "match_id"]
        if group["bets"].duplicated(keys).any() or group["equity"].duplicated(keys[:2] + ["match_date"]).any():
            raise ValueError("Original ledgers repeat an account/fixture or account/date identity")
    accounts = []
    for scope in ("single", "continuous", "seasonal"):
        group = tables[scope]
        candidates = catalog if scope == "single" else compatible
        for config in candidates:
            sid = config["strategy_id"]
            seasons = SEASONS if scope == "seasonal" else ("2025-26",) if scope == "single" else ("2022-26",)
            for season in seasons:
                selected = group["metrics"].loc[group["metrics"].strategy_id.eq(sid)]
                if scope == "seasonal": selected = selected.loc[selected.season.eq(season)]
                metric = selected.iloc[0].to_dict()
                episode = "2025-26" if scope == "single" else metric["episode_id"]
                if episode != ("continuous_2022_26" if scope == "continuous" else season):
                    raise ValueError("Original account episode no longer matches its declared scope")
                universe = opportunities if scope == "continuous" else opportunities.loc[opportunities.season.eq(season)].copy()
                bets = group["bets"].loc[group["bets"].strategy_id.eq(sid) & group["bets"].episode_id.eq(episode)].copy()
                equity = group["equity"].loc[group["equity"].strategy_id.eq(sid) & group["equity"].episode_id.eq(episode)].copy().sort_values("match_date").reset_index(drop=True)
                _check_account(config, metric, bets, equity, universe, models, episode)
                accounts.append({"config": deepcopy(config), "scope": scope, "season": season, "episode_id": episode,
                    "account_id": f"{scope}:{sid}:{season}", "opportunities": universe,
                    "original_metrics": metric, "original_bets": bets, "original_equity": equity})
    if len(accounts) != 364 or len({a["account_id"] for a in accounts}) != 364:
        raise ValueError("Expected exactly 364 unique original accounts")
    # Every ledger row must belong to an account; an extra episode cannot hide
    # merely because the per-account filters above never selected it.
    for scope, group in tables.items():
        accepted = {(a["config"]["strategy_id"], a["episode_id"]) for a in accounts if a["scope"] == scope}
        for kind in ("bets", "equity"):
            present = set(group[kind][["strategy_id", "episode_id"]].itertuples(index=False, name=None))
            if not present.issubset(accepted):
                raise ValueError("Original ledger contains an unknown account episode")
    return {"catalog": deepcopy(catalog), "models": models, "opportunities": opportunities,
            "accounts": accounts, "source_paths": sources}
