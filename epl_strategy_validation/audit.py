"""Audit every account and reproduce the frozen fresh-season comparison."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from .inputs import LAB_EXPORT_RELATIVE, SEASONS, SEASON_MATCH_COUNTS, SEASON_DATE_COUNTS


def audit_export(output: Path, root: Path) -> dict:
    output, root = Path(output), Path(root)
    catalog = json.loads((output / "compatible_catalog.json").read_text())
    ids = [c["strategy_id"] for c in catalog]
    old = root / LAB_EXPORT_RELATIVE
    old_bets = pd.read_parquet(old / "bets.parquet")
    old_equity = pd.read_parquet(old / "equity.parquet")
    old_metrics = pd.read_parquet(old / "metrics.parquet").set_index("strategy_id")
    comparisons, greatest_error = 0, 0.

    def near(left, right, label):
        nonlocal comparisons, greatest_error
        a, b = np.asarray(left, float), np.asarray(right, float)
        if not np.allclose(a, b, atol=1e-6, rtol=1e-10):
            raise AssertionError(label)
        if a.size and b.size:
            greatest_error = max(greatest_error, float(np.max(np.abs(a - b))))
        comparisons += max(a.size, b.size)

    accounts = 0
    for scope in ("continuous", "seasonal"):
        metrics = pd.read_parquet(output / f"metrics_{scope}.parquet")
        bets = pd.read_parquet(output / f"bets_{scope}.parquet")
        equity = pd.read_parquet(output / f"equity_{scope}.parquet")
        expected = 56 if scope == "continuous" else 224
        if len(metrics) != expected or set(metrics.strategy_id) != set(ids):
            raise AssertionError("Account metric population differs")
        if bets.duplicated(["strategy_id", "episode_id", "match_id"]).any():
            raise AssertionError("Duplicate funded trade identity")
        for _, metric in metrics.iterrows():
            sid, episode = metric.strategy_id, metric.episode_id
            trades = bets.loc[bets.strategy_id.eq(sid) & bets.episode_id.eq(episode)]
            curve = equity.loc[equity.strategy_id.eq(sid) & equity.episode_id.eq(episode)].sort_values("match_date")
            accounts += 1
            expected_dates = 453 if scope == "continuous" else SEASON_DATE_COUNTS[metric.season]
            expected_matches = 1470 if scope == "continuous" else SEASON_MATCH_COUNTS[metric.season]
            if len(curve) != expected_dates or curve.match_date.duplicated().any():
                raise AssertionError("An account is missing a priced date")
            near(curve.matched_matches.sum(), expected_matches, "Opportunity coverage")
            near(metric.initial_capital_sum_units, 100000, "Initial funding")
            near(metric.bankroll_reset_episodes, 1, "One account episode")
            near(curve.start_bankroll.iloc[0], 100000, "First date funding")
            near(curve.start_bankroll.iloc[1:], curve.end_bankroll.iloc[:-1], "Continuous date cash")
            cash = trades.groupby("match_date").agg(stake=("stake", "sum"), profit=("profit", "sum"))
            cash = cash.reindex(pd.DatetimeIndex(curve.match_date), fill_value=0)
            near(curve.turnover, cash.stake, "Date stakes")
            near(curve.profit, cash.profit, "Date profit")
            near(curve.end_bankroll, curve.start_bankroll + cash.profit.to_numpy(), "Date principal accounting")
            if (curve.turnover > curve.start_bankroll + 1e-6).any() or (curve.end_bankroll < -1e-6).any():
                raise AssertionError("Unfunded account")
            near(metric.profit, trades.profit.sum(), "Account profit")
            near(metric.turnover, trades.stake.sum(), "Account turnover")
            near(metric.final_capital_sum_units, 100000 + trades.profit.sum(), "Final capital")
            near(metric.trading_frequency, len(trades) / expected_matches, "Trade frequency")
            near(metric.expected_gain_total_units,
                 (trades.probability * trades.stake * (trades.odds - 1)).sum(), "Expected positive payoff")
            near(metric.expected_loss_total_units,
                 ((1 - trades.probability) * trades.stake).sum(), "Expected loss magnitude")
            if scope == "seasonal" and metric.season == "2025-26":
                ordered = trades.sort_values("match_id")
                previous = old_bets.loc[old_bets.strategy_id.eq(sid)].sort_values("match_id")
                if ordered.match_id.tolist() != previous.match_id.tolist() or ordered.selection.tolist() != previous.selection.tolist():
                    raise AssertionError("A frozen 2025 selection changed")
                for field in ("probability", "odds", "stake", "gross_return", "profit"):
                    near(ordered[field], previous[field], "Frozen 2025 " + field)
                original_curve = old_equity.loc[old_equity.strategy_id.eq(sid)].sort_values("match_date")
                near(curve.end_bankroll, original_curve.end_bankroll, "Frozen 2025 cash path")
                for field in ("profit", "turnover", "hit_ratio", "trading_frequency", "roi", "max_drawdown"):
                    near(metric[field], old_metrics.loc[sid, field], "Frozen 2025 " + field)
    graph = pd.read_csv(output / "graph_equity_continuous.csv")
    if set(graph.strategy_id) != set(ids) or not graph.groupby("strategy_id").size().eq(454).all():
        raise AssertionError("The complete graph lost an account/date")
    if not graph.loc[graph.is_initial].end_bankroll.eq(100000).all():
        raise AssertionError("Graph initial funding changed")
    selected = pd.read_parquet(output / "selection_comparison.parquet")
    global_ = pd.read_parquet(output / "selection_global.parquet")
    if len(selected) != 672 or len(global_) != 8:
        raise AssertionError("Selection sensitivity family coverage changed")
    if not selected.family_adjusted_one_sided_p.between(0, 1).all():
        raise AssertionError("Invalid adjusted p-value")
    if not (selected.family_adjusted_one_sided_p + 1e-12 >= selected.raw_one_sided_p).all():
        raise AssertionError("Adjusted p-value below its own-column p-value")
    return {"status": "passed", "accounts_checked": accounts, "four_season_strategies": 56,
            "frozen_2025_strategies_reproduced": 56, "numeric_values_compared": comparisons,
            "largest_absolute_rounding_error": greatest_error,
            "selection_rows": len(selected), "selection_families": len(global_),
            "interpretation": "Historical identities and conditional recorded-cashflow checks; not a new untouched test."}
