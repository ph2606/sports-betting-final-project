"""Fixed-exposure friction sensitivity with explicit pre-settlement funding checks.

No bet is resized, removed, requalified, or selected using the stressed result.
An unfundable shadow path is a counterfactual cashflow calculation, not a
self-financing Kelly replay. Fees are hypothetical charges on every wager.
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd

from epl_strategy.metrics import _prepare, _near


SCENARIOS = [
    {"scenario_id": "baseline", "fee_rate": 0.0, "payout_haircut": 0.0},
    {"scenario_id": "fee_0p25pct", "fee_rate": 0.0025, "payout_haircut": 0.0},
    {"scenario_id": "fee_0p5pct", "fee_rate": 0.005, "payout_haircut": 0.0},
    {"scenario_id": "fee_1pct", "fee_rate": 0.01, "payout_haircut": 0.0},
    {"scenario_id": "fee_2pct", "fee_rate": 0.02, "payout_haircut": 0.0},
    {"scenario_id": "haircut_1pct", "fee_rate": 0.0, "payout_haircut": 0.01},
    {"scenario_id": "haircut_2p5pct", "fee_rate": 0.0, "payout_haircut": 0.025},
    {"scenario_id": "haircut_5pct", "fee_rate": 0.0, "payout_haircut": 0.05},
    {"scenario_id": "combined_fee1pct_haircut2p5pct", "fee_rate": 0.01, "payout_haircut": 0.025},
]
LABELS = ("study", "scope", "strategy_id", "episode_id", "branch", "family", "model_type", "feature_group",
          "split", "outer_season", "policy", "odds_mode", "staking", "threshold", "is_tuning_diagnostic")


def _ratio(numerator, denominator):
    return float(numerator / denominator) if denominator > 0 else None


def _bounds(values):
    values = np.asarray(values, dtype=float)
    finite = values[np.isfinite(values)]
    return tuple(np.quantile(finite, [0.025, 0.975])) if len(finite) else (None, None)


def _bootstrap_totals(curve, samples, seed):
    # The same date draws are reused across scenarios for matched comparisons.
    totals = np.zeros((samples, 6), dtype=float)
    rng = np.random.default_rng(seed)
    for _, part in curve.groupby("episode_id", sort=True):
        values = part[["profit", "turnover", "positive_profit", "bet_count", "wins", "matched_matches"]].to_numpy(float)
        indices = rng.integers(0, len(values), size=(samples, len(values)))
        totals += values[indices].sum(axis=1)
    return totals


def _funding(curve, *, initial, fee, haircut, labels, scenario_id):
    episodes = []
    for episode, part in curve.groupby("episode_id", sort=True):
        part = part.sort_values("match_date")
        pnl = part.profit.to_numpy(float) - haircut * part.positive_profit.to_numpy(float) - fee * part.turnover.to_numpy(float)
        start = initial + np.concatenate(([0.0], np.cumsum(pnl)[:-1]))
        end = initial + np.cumsum(pnl)
        required = (1 + fee) * part.turnover.to_numpy(float)
        shortfall = np.maximum(required - start, 0)
        breached = shortfall > 1e-7
        wealth = np.concatenate(([initial], end))
        peaks = np.maximum.accumulate(wealth)
        drawdown = 1 - wealth / peaks
        dates = part.match_date.dt.strftime("%Y-%m-%d").to_numpy()
        episodes.append({**labels, "scenario_id": scenario_id, "fee_rate": fee, "payout_haircut": haircut,
                         "diagnostic_episode_id": str(episode), "initial_capital_units": float(initial),
                         "final_shadow_bankroll_units": float(end[-1]), "min_shadow_bankroll_units": float(wealth.min()),
                         "shadow_max_drawdown": float(drawdown.max()),
                         "funding_feasible": bool(not breached.any()), "funding_breach_dates": int(breached.sum()),
                         "first_funding_breach_date": str(dates[np.flatnonzero(breached)[0]]) if breached.any() else None,
                         "required_additional_initial_capital_units": float(shortfall.max(initial=0)),
                         "shadow_path_can_require_external_funding": bool(breached.any()),
                         "episode_log_growth": float(math.log(end[-1] / initial)) if not breached.any() and end[-1] > 0 else None})
    return episodes


def stress_group(bets, equity, original, *, bootstrap_samples=1000, random_state=42, scenarios=None):
    """Return scenario metrics and per-episode funding summaries for one scope.

    Turnover remains original base wagers; fee-inclusive cash outlay is a
    separate denominator. Outcome hit ratio remains correct selections / bets;
    profitable-trade share is supplied separately if costs turn a winner into
    a loss. Expectations split economic positive/negative outcome cashflows.
    """
    if not isinstance(bootstrap_samples, (int, np.integer)) or bootstrap_samples < 0:
        raise ValueError("Bootstrap samples must be a nonnegative integer")
    raw_equity = equity.copy()
    if "episode_id" not in raw_equity:
        raw_equity["episode_id"] = "episode"
    episode_count = raw_equity.episode_id.nunique()
    initial = float(original.get("initial_bankroll", original.get("initial_capital_sum_units", 1000.0) / max(episode_count, 1)))
    if not np.isfinite(initial) or initial <= 0:
        raise ValueError("Initial episode capital must be positive and finite")
    positions, curve, _ = _prepare(bets, raw_equity, initial)
    count = len(positions)
    predictions = int(original["prediction_count"])
    matched = int(original["matched_valid_odds_count"])
    if not 0 <= count <= matched <= predictions:
        raise ValueError("Trade/opportunity counts conflict")
    _near(curve.matched_matches.sum(), matched, "Priced opportunity count")
    labels = {name: original.get(name, "") for name in LABELS}
    p, s, odds = (positions[name].to_numpy(float) for name in ("probability", "stake", "odds"))
    won = positions.won.to_numpy(bool)
    win_before = s * (odds - 1)
    profit_before, turnover = float(positions.profit.sum()), float(s.sum())
    winning_gain_before = float(win_before[won].sum())
    expected_win_before = float((p * win_before).sum())
    expected_profit_before = float((s * (p * odds - 1)).sum())
    totals = _bootstrap_totals(curve, bootstrap_samples, random_state) if bootstrap_samples else np.zeros((0, 6))
    rows, funding = [], []
    definitions = SCENARIOS if scenarios is None else scenarios
    if len({item["scenario_id"] for item in definitions}) != len(definitions):
        raise ValueError("Scenario IDs must be unique")
    for scenario in definitions:
        fee, haircut = float(scenario["fee_rate"]), float(scenario["payout_haircut"])
        if not np.isfinite([fee, haircut]).all() or fee < 0 or not 0 <= haircut <= 1:
            raise ValueError("Fee must be nonnegative; net-winning-payout haircut must lie in [0,1]")
        winning_net = (1 - haircut) * win_before - fee * s
        losing_net = -(1 + fee) * s
        realized = np.where(won, winning_net, losing_net)
        expected_positive = p * np.maximum(winning_net, 0) + (1 - p) * np.maximum(losing_net, 0)
        expected_negative = p * np.maximum(-winning_net, 0) + (1 - p) * np.maximum(-losing_net, 0)
        expected_gain, expected_loss = float(expected_positive.sum()), float(expected_negative.sum())
        profit = float(realized.sum())
        expected_net = expected_gain - expected_loss
        _near(profit, profit_before - haircut * winning_gain_before - fee * turnover, "Fixed-stake stressed profit")
        _near(expected_net, expected_profit_before - haircut * expected_win_before - fee * turnover, "Stressed model expectation")
        gains, losses = realized[realized > 0], -realized[realized < 0]
        win_mean, loss_mean = (float(gains.mean()) if len(gains) else None), (float(losses.mean()) if len(losses) else None)
        gross_return = float(np.where(won, s + (1 - haircut) * win_before, 0).sum())
        fees = fee * turnover
        _near(profit, gross_return - turnover - fees, "Fee-aware cash settlement")
        episodes = _funding(curve, initial=initial, fee=fee, haircut=haircut, labels=labels, scenario_id=scenario["scenario_id"])
        funding.extend(episodes)
        feasible = all(item["funding_feasible"] for item in episodes)
        shadow_dd = max((item["shadow_max_drawdown"] for item in episodes), default=None)
        roi_samples = np.divide(totals[:, 0] - haircut * totals[:, 2] - fee * totals[:, 1], totals[:, 1],
                                out=np.full(len(totals), np.nan), where=totals[:, 1] > 0)
        hit_samples = np.divide(totals[:, 4], totals[:, 3], out=np.full(len(totals), np.nan), where=totals[:, 3] > 0)
        freq_samples = np.divide(totals[:, 3], totals[:, 5], out=np.full(len(totals), np.nan), where=totals[:, 5] > 0)
        expectancy_samples = np.divide(totals[:, 0] - haircut * totals[:, 2] - fee * totals[:, 1], totals[:, 3],
                                       out=np.full(len(totals), np.nan), where=totals[:, 3] > 0)
        row = {**labels, **scenario,
               "analysis_type": "fixed_recorded_exposure_cashflow_sensitivity",
               "bet_count": count, "winning_bet_count": int(won.sum()), "hit_ratio": _ratio(won.sum(), count),
               "profitable_trade_count": len(gains), "loss_making_trade_count": len(losses),
               "profitable_trade_share": _ratio(len(gains), count), "profitable_trade_ratio": _ratio(len(gains), count),
               "avg_winning_gain_units": win_mean, "avg_losing_loss_units": loss_mean,
               "avg_winning_outcome_net_payoff_units": float(realized[won].mean()) if won.any() else None,
               "expected_gain_total_units": expected_gain, "expected_loss_total_units": expected_loss,
               "expected_gain_per_trade_units": _ratio(expected_gain, count),
               "expected_loss_per_trade_units": _ratio(expected_loss, count),
               "expected_net_profit_total_units": expected_net, "expected_net_profit_per_trade_units": _ratio(expected_net, count),
               "realized_expectancy_per_trade_units": _ratio(profit, count),
               "expected_roi": _ratio(expected_net, turnover), "profit": profit, "turnover": turnover,
               "gross_return": gross_return, "fee_units": fees, "cash_outlay": turnover + fees,
               "roi": _ratio(profit, turnover), "roi_on_cash_outlay": _ratio(profit, turnover + fees),
               "profit_factor": float(gains.sum() / losses.sum()) if losses.sum() > 0 else math.inf if gains.sum() > 0 else None,
               "payoff_ratio": _ratio(win_mean, loss_mean) if win_mean is not None and loss_mean is not None else None,
               "prediction_count": predictions, "matched_valid_odds_count": matched,
               "trading_frequency": _ratio(count, matched), "trade_rate_all_predictions": _ratio(count, predictions),
               "active_date_fraction": _ratio(int(curve.bet_count.gt(0).sum()), len(curve)),
               "funding_feasible": feasible, "funding_breach_dates": sum(item["funding_breach_dates"] for item in episodes),
               "infeasible_episode_count": sum(not item["funding_feasible"] for item in episodes),
               "required_additional_initial_capital_units": sum(item["required_additional_initial_capital_units"] for item in episodes),
               "min_shadow_bankroll_units": min((item["min_shadow_bankroll_units"] for item in episodes), default=None),
               "shadow_max_drawdown": shadow_dd, "max_drawdown": shadow_dd if feasible else None,
               "risk_basis": "worst_separate_episode_shadow_date_close_path; conventional_drawdown_available_only_if_fundable",
               "bankroll_reset_episodes": len(episodes), "initial_capital_sum_units": initial * len(episodes),
               "final_shadow_capital_sum_units": sum(item["final_shadow_bankroll_units"] for item in episodes),
               "return_on_initial_capital": _ratio(profit, initial * len(episodes)),
               "baseline_profit": profit_before, "baseline_winning_net_gains": winning_gain_before,
               "realized_profit_reduction_units": profit_before - profit,
               "model_expected_profit_reduction_units": expected_profit_before - expected_net,
               "baseline_signed_break_even_fee_rate": _ratio(profit_before, turnover),
               "baseline_signed_break_even_payout_haircut": _ratio(profit_before, winning_gain_before),
               "remaining_signed_break_even_fee_rate_at_haircut": _ratio(profit_before - haircut * winning_gain_before, turnover),
               "bootstrap_samples": int(bootstrap_samples), "bootstrap_valid_roi_samples": int(np.isfinite(roi_samples).sum()),
               "uncertainty_basis": "same whole-date draws reused across shocks, stratified by reset episode; recorded bets/stakes fixed; no refit or multiplicity adjustment",
               "fee_basis": "hypothetical fraction of original stake charged on every winning or losing wager",
               "haircut_basis": "fraction of winning net payout stake*(odds-1), not of full decimal odds",
               "selection_basis": "original recorded selections and stakes; no requalification, resizing or dropping later bets",
               "expectation_basis": "probability-weighted positive/negative outcome cashflows at recorded allocated stakes; not predicted terminal wealth",
               "metric_status": "no_trades" if not count else "fundable_fixed_exposure_stress" if feasible else "unfundable_shadow_cashflow_only"}
        for name, samples in (("roi", roi_samples), ("hit_ratio", hit_samples), ("trading_frequency", freq_samples),
                              ("realized_expectancy_per_trade_units", expectancy_samples)):
            row[name + "_ci_low"], row[name + "_ci_high"] = _bounds(samples)
        rows.append(row)
    return rows, pd.DataFrame(funding)
