"""Adapt the frozen laboratory cash engine to validated native season metadata."""
from __future__ import annotations

import numpy as np
import pandas as pd

from epl_strategy_lab.engine import simulate_strategy
from .inputs import validate_opportunities


def replay(config, models, opportunities, *, initial_bankroll=100000.0,
           episode_id="continuous_2022_26") -> tuple[pd.DataFrame, pd.DataFrame]:
    """Replay one uninterrupted account, retaining each fixture's real season.

    The old engine's optional season assertion was specific to its original
    one-season report. After checking the real season/date identities here,
    omit that optional metadata column for the engine call, then restore it by
    exact fixture/date identity. Dates, quotes, outcomes and probabilities are
    never relabeled. Passing all four years at once carries capital without a
    reset; a fresh seasonal account requires a separate explicit call.
    """
    if not isinstance(episode_id, str) or not episode_id.strip():
        raise ValueError("A nonempty explicit account episode_id is required")
    if str(config.get("model_key", "")).startswith("first_"):
        raise ValueError("First-study models cannot be backfilled into earlier rolling evaluation seasons")
    native = validate_opportunities(opportunities)
    bets, equity = simulate_strategy(config, models, native.drop(columns="season"),
                                    initial_bankroll=initial_bankroll)
    bets["episode_id"] = episode_id
    equity["episode_id"] = episode_id
    season_by_id = native.set_index("match_id").season
    bets["season"] = bets.match_id.map(season_by_id)
    season_by_date = native[["match_date", "season"]].drop_duplicates().set_index("match_date").season
    equity["season"] = equity.match_date.map(season_by_date)
    if bets.season.isna().any() or equity.season.isna().any():
        raise AssertionError("The engine returned an identity absent from the native season map")
    expected_dates = pd.DatetimeIndex(native.match_date.unique()).sort_values()
    if not pd.DatetimeIndex(equity.match_date).equals(expected_dates):
        raise AssertionError("Every native quoted date must be present exactly once")
    if not equity.episode_id.eq(episode_id).all() or not bets.episode_id.eq(episode_id).all():
        raise AssertionError("The replay must retain one chosen account episode")
    if not np.isclose(float(equity.start_bankroll.iloc[0]), initial_bankroll, atol=1e-8, rtol=0):
        raise AssertionError("The replay changed its initial capital")
    if len(equity) > 1 and not np.allclose(equity.start_bankroll.iloc[1:].to_numpy(float),
                                         equity.end_bankroll.iloc[:-1].to_numpy(float),
                                         atol=1e-8, rtol=1e-12):
        raise AssertionError("The replay introduced a capital reset or transfer")
    return bets, equity
