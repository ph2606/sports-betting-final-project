"""Season diagnostics for four separately funded seasonal accounts."""
from __future__ import annotations

import numpy as np
import pandas as pd


SEASONS = ("2022-23", "2023-24", "2024-25", "2025-26")


def season_stability(seasonal: pd.DataFrame, continuous: pd.DataFrame) -> pd.DataFrame:
    required = {"strategy_id", "season", "profit", "turnover", "initial_capital_sum_units",
                "return_on_initial_capital", "bankroll_reset_episodes"}
    if not required.issubset(seasonal):
        raise ValueError("Seasonal metrics are missing required account fields")
    if seasonal.duplicated(["strategy_id", "season"]).any():
        raise ValueError("Duplicate seasonal strategy account")
    if not seasonal.initial_capital_sum_units.eq(100000).all() or not seasonal.bankroll_reset_episodes.eq(1).all():
        raise ValueError("Season stability requires separately funded 100000 seasonal accounts")
    if continuous.strategy_id.duplicated().any() or set(continuous.strategy_id) != set(seasonal.strategy_id):
        raise ValueError("Continuous and seasonal strategy populations differ")
    result = []
    linked = continuous.set_index("strategy_id")
    for sid, group in seasonal.groupby("strategy_id", sort=True):
        if len(group) != 4 or set(group.season) != set(SEASONS):
            raise ValueError("Each strategy requires all four seasonal accounts")
        ordered = group.set_index("season").reindex(SEASONS)
        profit = ordered.profit.to_numpy(float)
        turnover = ordered.turnover.to_numpy(float)
        returns = ordered.return_on_initial_capital.to_numpy(float)
        if not np.isfinite(np.r_[profit, turnover, returns]).all() or (turnover < 0).any():
            raise ValueError("Seasonal cash metrics must be finite with nonnegative turnover")
        if not np.allclose(returns, profit / 100000, atol=1e-10, rtol=0):
            raise ValueError("Seasonal return does not reconcile with fresh capital")
        remaining_turnover = turnover.sum() - turnover
        loo = np.divide(profit.sum() - profit, remaining_turnover,
                        out=np.full(4, np.nan), where=remaining_turnover > 0)
        observed = loo[np.isfinite(loo)]
        row = {
            "strategy_id": sid, "positive_seasons": int((profit > 0).sum()),
            "negative_seasons": int((profit < 0).sum()), "zero_profit_seasons": int((profit == 0).sum()),
            "worst_season_return": float(returns.min()), "best_season_return": float(returns.max()),
            "return_std": float(returns.std(ddof=1)),
            "pooled_reset_profit": float(profit.sum()), "pooled_reset_turnover": float(turnover.sum()),
            "pooled_reset_starting_capital": 400000.0,
            "pooled_reset_capital_return": float(profit.sum() / 400000),
            "pooled_reset_roi": float(profit.sum() / turnover.sum()) if turnover.sum() else np.nan,
            "loo_min_reset_roi": float(observed.min()) if len(observed) else np.nan,
            "loo_max_reset_roi": float(observed.max()) if len(observed) else np.nan,
            "loo_basis": "omit one independently funded seasonal account's recorded profit and turnover; not a continuous-Kelly rerun",
        }
        for season, value, roi in zip(SEASONS, returns, loo):
            row["season_return_" + season.replace("-", "_")] = float(value)
            row["omit_" + season.replace("-", "_") + "_reset_roi"] = float(roi)
        for field in ("name", "model_key", "staking", "bet_count", "hit_ratio", "roi",
                      "return_on_initial_capital", "final_capital_sum_units", "max_drawdown"):
            if field in linked:
                row["continuous_" + field] = linked.loc[sid, field]
        result.append(row)
    return pd.DataFrame(result)
