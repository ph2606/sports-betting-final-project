"""Independent cashflow checks and equivalence to the frozen legacy ledgers."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from .inputs import ABLATION_MODELS, load_inputs


def audit_export(output_dir: Path, root: Path | None = None) -> dict:
    """Audit saved outputs without invoking the strategy engine or metric builder.

    In particular, the original 38 policies must reproduce the already frozen
    trade selections and cashflows at exactly 100 times their earlier funding.
    """
    output_dir = Path(output_dir).resolve()
    root = Path(root).resolve() if root else Path(__file__).resolve().parents[1]
    catalog = json.loads((output_dir / "catalog.json").read_text(encoding="utf-8"))
    metrics = pd.read_parquet(output_dir / "metrics.parquet").set_index("strategy_id")
    bets = pd.read_parquet(output_dir / "bets.parquet")
    equity = pd.read_parquet(output_dir / "equity.parquet")
    graph = pd.read_csv(output_dir / "graph_equity.csv")
    models, opportunities, _ = load_inputs(root)
    dates = pd.DatetimeIndex(opportunities.match_date.unique()).sort_values()
    source = opportunities.set_index("match_id")
    ids = [item["strategy_id"] for item in catalog]
    if len(ids) != 84 or len(set(ids)) != 84:
        raise AssertionError("The complete catalog must contain 84 unique IDs")
    for frame in (metrics.reset_index(), equity, graph):
        if set(frame.strategy_id) != set(ids):
            raise AssertionError("A saved strategy population differs from the catalog")
    if not set(bets.strategy_id).issubset(ids):
        raise AssertionError("The ledger contains an unknown strategy")
    if len(metrics) != 84:
        raise AssertionError("Duplicate metric rows")
    first = pd.read_parquet(root / "epl_modeling/results/bets.parquet")
    first = first.loc[first.split.eq("test")]
    rolling = pd.read_parquet(root / "epl_modeling/ablation_results/bets.parquet")
    rolling = rolling.loc[rolling.outer_season.eq("2025-26")]
    inverse = {key: pair for pair, key in ABLATION_MODELS.items()}
    checks = 0
    legacy_checks = 0
    largest_legacy_cashflow_error = 0.0

    def near(actual, expected, label):
        nonlocal checks
        left, right = np.asarray(actual, dtype=float), np.asarray(expected, dtype=float)
        if not np.allclose(left, right, atol=1e-6, rtol=1e-10, equal_nan=False):
            raise AssertionError(label)
        checks += max(left.size, right.size)

    for config in catalog:
        sid = config["strategy_id"]
        positions = bets.loc[bets.strategy_id.eq(sid)].sort_values("match_id").reset_index(drop=True)
        curve = equity.loc[equity.strategy_id.eq(sid)].sort_values("match_date").reset_index(drop=True)
        chart = graph.loc[graph.strategy_id.eq(sid)].sort_values("match_date").reset_index(drop=True)
        metric = metrics.loc[sid]
        if positions.match_id.duplicated().any() or len(curve) != 113 or len(chart) != 114:
            raise AssertionError(sid + " duplicate bets or incomplete date path")
        if not pd.DatetimeIndex(pd.to_datetime(curve.match_date)).equals(dates):
            raise AssertionError(sid + " date universe differs")
        if pd.Timestamp(chart.match_date.iloc[0]) != dates[0] - pd.Timedelta(days=1):
            raise AssertionError(sid + " missing common starting anchor")
        near(chart.end_bankroll.iloc[0], 100000, sid + " initial graph balance")
        near(chart.end_bankroll.iloc[1:], curve.end_bankroll, sid + " graph cash path")
        if not curve.episode_id.eq("2025-26").all():
            raise AssertionError(sid + " account episode changed")
        grouped = positions.assign(match_date=pd.to_datetime(positions.match_date)).groupby("match_date")
        daily = grouped.agg(stake=("stake", "sum"), profit=("profit", "sum"), count=("match_id", "size"))
        daily = daily.reindex(dates, fill_value=0)
        expected_start = 100000 + daily.profit.cumsum().shift(fill_value=0)
        expected_end = expected_start + daily.profit
        near(curve.start_bankroll, expected_start, sid + " continuous start cash")
        near(curve.end_bankroll, expected_end, sid + " continuous end cash")
        near(curve.turnover, daily.stake, sid + " date wager commitment")
        near(curve.bet_count, daily["count"], sid + " date trade count")
        cap = config.get("date_cap_fraction")
        available = expected_start if cap is None else expected_start * float(cap)
        if (daily.stake.to_numpy() > available.to_numpy() + 1e-6).any():
            raise AssertionError(sid + " unfunded date commitment")
        if (expected_end < -1e-6).any():
            raise AssertionError(sid + " negative cash account")
        near(metric.bet_count, len(positions), sid + " metric count")
        near(metric.profit, positions.profit.sum(), sid + " metric net profit")
        near(metric.turnover, positions.stake.sum(), sid + " metric turnover")
        near(metric.final_capital_sum_units, expected_end.iloc[-1], sid + " final capital")
        near(metric.initial_capital_sum_units, 100000, sid + " metric initial capital")
        near(metric.bankroll_reset_episodes, 1, sid + " one uninterrupted account")
        near(metric.trading_frequency, len(positions) / 374, sid + " trading frequency")
        near(metric.return_on_initial_capital, positions.profit.sum() / 100000, sid + " capital return")
        peak = np.maximum.accumulate(np.r_[100000.0, expected_end.to_numpy()])
        dd = 1 - np.r_[100000.0, expected_end.to_numpy()] / peak
        near(metric.max_drawdown, dd.max(), sid + " initial-capital drawdown")
        if len(positions):
            near(metric.hit_ratio, positions.won.mean(), sid + " hit ratio")
            near(positions.gross_return, positions.stake * positions.odds * positions.won.astype(float), sid + " gross returns")
            near(positions.profit, positions.gross_return - positions.stake, sid + " stake principal")
            near(metric.expected_gain_total_units,
                 (positions.probability * positions.stake * (positions.odds - 1)).sum(), sid + " expected positive payoff")
            near(metric.expected_loss_total_units,
                 ((1 - positions.probability) * positions.stake).sum(), sid + " expected loss magnitude")
            p = models[config["model_key"]].set_index("match_id")
            for outcome in "HDA":
                chosen = positions.loc[positions.selection.eq(outcome)]
                if chosen.empty:
                    continue
                near(chosen.probability, p.loc[chosen.match_id, "p_" + outcome], sid + " source probabilities")
                prefix = "ref_" if config["odds_mode"] == "reference" else ""
                near(chosen.odds, source.loc[chosen.match_id, prefix + "odds_" + outcome], sid + " source prices")
            native = source.loc[positions.match_id]
            if not np.array_equal(positions.won.to_numpy(bool), positions.selection.to_numpy() == native.result.to_numpy()):
                raise AssertionError(sid + " wager settlement outcome")
        elif not pd.isna(metric.hit_ratio):
            raise AssertionError(sid + " a no-trade hit ratio must be undefined")

        if config["origin"] != "legacy":
            continue
        legacy_checks += 1
        if config.get("cash_only"):
            if len(positions):
                raise AssertionError(sid + " frozen primary cash policy traded")
            continue
        old_staking = "fixed" if config["staking"] == "fixed" else "kelly"
        if config["model_key"].startswith("first_"):
            branch = config["model_key"].removeprefix("first_")
            mode = "bet365_reference" if config["odds_mode"] == "reference" else "best_individual_book"
            old = first.loc[first.branch.eq(branch) & first.staking.eq(old_staking) & first.odds_mode.eq(mode)]
        else:
            group, model = inverse[config["model_key"]]
            old = rolling.loc[rolling.feature_group.eq(group) & rolling.model_type.eq(model) & rolling.staking.eq(old_staking)]
        old = old.sort_values("match_id").reset_index(drop=True)
        if not np.array_equal(positions.match_id.to_numpy(), old.match_id.to_numpy()):
            raise AssertionError(sid + " changed a frozen legacy trade population")
        if not np.array_equal(positions.selection.to_numpy(), old.selection.to_numpy()):
            raise AssertionError(sid + " changed a frozen legacy selection")
        for column in ("stake", "gross_return", "profit"):
            near(positions[column], old[column] * 100, sid + " scaled original " + column)
            if len(old):
                largest_legacy_cashflow_error = max(largest_legacy_cashflow_error,
                    float(np.max(np.abs(positions[column].to_numpy() - old[column].to_numpy() * 100))))
    if legacy_checks != 38:
        raise AssertionError("All 38 original policies must pass the frozen-ledger comparison")
    return {
        "status": "passed", "strategies": len(ids), "common_matches": len(opportunities),
        "matched_dates_per_strategy": len(dates), "graph_points_per_strategy": 114,
        "numeric_values_compared": checks, "original_policies_checked": legacy_checks,
        "legacy_scale_factor": 100, "largest_legacy_cashflow_absolute_error": largest_legacy_cashflow_error,
        "method": "Saved-ledger cash identities and source checks without engine calls; original 38 rules compared with frozen earlier trade ledgers at 100x funding.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    print(json.dumps(audit_export(args.output_dir), indent=2))


if __name__ == "__main__":
    main()
