"""Audited trade-level expectations, realized payoffs, activity and reset-aware risk."""
from __future__ import annotations

import math

import numpy as np
import pandas as pd


BET_FIELDS = ("match_id", "match_date", "probability", "odds", "stake", "won", "gross_return", "profit")
EQUITY_FIELDS = ("episode_id", "match_date", "matched_matches", "bet_count", "turnover", "profit",
                 "start_bankroll", "end_bankroll", "daily_return")
EQUITY_COLUMNS = list(EQUITY_FIELDS) + ["running_peak", "drawdown", "log_growth"]


def _require(frame, columns, label):
    missing = sorted(set(columns) - set(frame.columns))
    if missing:
        raise ValueError(f"{label} missing columns: {missing}")


def _dates(values):
    result = pd.to_datetime(values.astype("string").str[:10], format="%Y-%m-%d", errors="raise")
    if result.isna().any():
        raise ValueError("A match date is missing")
    return result.dt.normalize()


def _near(left, right, label):
    if not np.allclose(np.asarray(left, dtype=float), np.asarray(right, dtype=float), rtol=1e-10, atol=1e-7):
        raise ValueError(label + " identity does not reconcile")


def _bets(frame):
    _require(frame, BET_FIELDS, "Bet ledger")
    out = frame.copy()
    out["match_date"] = _dates(out.match_date)
    if out.match_id.isna().any():
        raise ValueError("A bet match_id is missing")
    for column in ("probability", "odds", "stake", "gross_return", "profit", "won"):
        out[column] = pd.to_numeric(out[column], errors="coerce")
    values = out[["probability", "odds", "stake", "gross_return", "profit", "won"]].to_numpy(float)
    if not np.isfinite(values).all():
        raise ValueError("Bet values must be finite")
    if not out.probability.between(0, 1).all() or not out.odds.gt(1).all() or not out.stake.gt(0).all():
        raise ValueError("Probabilities, decimal odds or positive stakes are invalid")
    if not out.won.isin([0, 1]).all():
        raise ValueError("Won must be a boolean or zero/one indicator")
    out["won"] = out.won.astype(bool)
    if {"selection", "result"}.issubset(out):
        if not out.selection.isin(["H", "D", "A"]).all() or not out.result.isin(["H", "D", "A"]).all():
            raise ValueError("Selection/result must be H, D or A")
        if not out.won.eq(out.selection.eq(out.result)).all():
            raise ValueError("Won flag conflicts with selection/result identity")
    _near(out.gross_return, out.won.astype(float) * out.stake * out.odds, "Gross return")
    _near(out.profit, out.gross_return - out.stake, "Net profit")
    return out


def enrich_bets(frame):
    """Keep winning net profit distinct from gross proceeds and model expectation."""
    out = _bets(frame)
    out["winning_net_payoff_units"] = out.stake * (out.odds - 1)
    out["losing_loss_units"] = out.stake
    out["expected_gain_units"] = out.probability * out.winning_net_payoff_units
    out["expected_loss_units"] = (1 - out.probability) * out.losing_loss_units
    out["expected_net_profit_units"] = out.expected_gain_units - out.expected_loss_units
    out["realized_return_per_unit_staked"] = out.profit / out.stake
    out["model_expected_return_per_unit_staked"] = out.probability * out.odds - 1
    return out


def reconstruct_equity(bets, opportunities, *, initial_bankroll=1000.0, episode_id="episode"):
    """Reconstruct date-close cashflows, including every priced opportunity date.

    This uses recorded stakes, never new Kelly sizing or a chronological replay
    of individual same-date settlements. Saved per-bet bankrolls are checked.
    """
    if not np.isfinite(initial_bankroll) or initial_bankroll <= 0:
        raise ValueError("Initial bankroll must be positive and finite")
    _require(opportunities, ["match_id", "match_date"], "Opportunity table")
    eligible = opportunities[["match_id", "match_date"]].copy()
    eligible["match_date"] = _dates(eligible.match_date)
    if eligible.match_id.isna().any() or eligible.match_id.duplicated().any():
        raise ValueError("Opportunity match IDs must be present and unique")
    positions = _bets(bets)
    if positions.match_id.duplicated().any():
        raise ValueError("Duplicate bet match identity within an episode")
    if "episode_id" in positions and not positions.episode_id.eq(episode_id).all():
        raise ValueError("Bet episode does not match reconstruction episode")
    dates = eligible.set_index("match_id").match_date
    if not positions.match_id.isin(dates.index).all() or not positions.match_date.eq(positions.match_id.map(dates)).all():
        raise ValueError("Bet identity/date absent from priced opportunities")
    if eligible.empty:
        return pd.DataFrame(columns=EQUITY_COLUMNS)
    base = eligible.groupby("match_date").size().rename("matched_matches").to_frame()
    cash = positions.groupby("match_date").agg(bet_count=("match_id", "size"), turnover=("stake", "sum"), profit=("profit", "sum"))
    base = base.join(cash).fillna({"bet_count": 0, "turnover": 0.0, "profit": 0.0}).sort_index()
    base["bet_count"] = base.bet_count.astype(int)
    base["start_bankroll"] = initial_bankroll + base.profit.cumsum().shift(fill_value=0)
    base["end_bankroll"] = initial_bankroll + base.profit.cumsum()
    if (base.start_bankroll.lt(-1e-7) | base.end_bankroll.lt(-1e-7)).any():
        raise ValueError("Recorded cashflows create negative bankroll")
    if base.turnover.gt(base.start_bankroll + 1e-7).any():
        raise ValueError("Recorded same-date stakes exceed date-start capital")
    base.loc[base.start_bankroll.abs().lt(1e-9), "start_bankroll"] = 0.0
    base.loc[base.end_bankroll.abs().lt(1e-9), "end_bankroll"] = 0.0
    base["daily_return"] = np.divide(base.profit, base.start_bankroll,
                                      out=np.zeros(len(base), dtype=float), where=base.start_bankroll.to_numpy(float) > 0)
    wealth = np.concatenate(([initial_bankroll], base.end_bankroll.to_numpy(float)))
    base["running_peak"] = np.maximum.accumulate(wealth)[1:]
    base["drawdown"] = 1 - base.end_bankroll / base.running_peak
    base["log_growth"] = np.log(base.end_bankroll / initial_bankroll, where=base.end_bankroll.to_numpy(float) > 0,
                                 out=np.full(len(base), -math.inf))
    for saved, reconstructed in (("date_start_bankroll", "start_bankroll"), ("date_end_bankroll", "end_bankroll")):
        if saved in positions:
            _near(positions[saved], positions.match_date.map(base[reconstructed]), saved)
    base["episode_id"] = episode_id
    return base.reset_index()[EQUITY_COLUMNS]


def _prepare(bets, equity, initial_bankroll):
    positions = enrich_bets(bets)
    curve = equity.copy()
    if "episode_id" not in curve:
        curve["episode_id"] = "episode"
    _require(curve, EQUITY_FIELDS, "Date equity")
    curve["match_date"] = _dates(curve.match_date)
    if curve.episode_id.isna().any() or curve.duplicated(["episode_id", "match_date"]).any():
        raise ValueError("Equity episode/date keys must be present and unique")
    episodes = curve.episode_id.drop_duplicates().tolist()
    if "episode_id" not in positions:
        if len(episodes) > 1 and len(positions):
            raise ValueError("Pooled bets require explicit episode IDs")
        positions["episode_id"] = episodes[0] if episodes else "episode"
    if positions.episode_id.isna().any() or positions.duplicated(["episode_id", "match_id"]).any():
        raise ValueError("Duplicate or missing episode/match bet identity")
    if not set(positions.episode_id).issubset(set(episodes)):
        raise ValueError("A bet episode is absent from the equity universe")
    for column in EQUITY_FIELDS[2:]:
        curve[column] = pd.to_numeric(curve[column], errors="coerce")
    if not np.isfinite(curve[list(EQUITY_FIELDS[2:])].to_numpy(float)).all():
        raise ValueError("Equity cashflow values must be finite")
    for column in ("matched_matches", "bet_count"):
        if not curve[column].ge(0).all() or not np.equal(curve[column], np.floor(curve[column])).all():
            raise ValueError("Date opportunity and trade counts must be nonnegative integers")
    if curve.bet_count.gt(curve.matched_matches).any():
        raise ValueError("Date trade count exceeds eligible match count")
    if curve.turnover.lt(-1e-7).any():
        raise ValueError("Date turnover is negative")
    curve = curve.sort_values(["episode_id", "match_date"]).reset_index(drop=True)
    daily = positions.groupby(["episode_id", "match_date"]).agg(
        check_bet_count=("match_id", "size"), check_turnover=("stake", "sum"), check_profit=("profit", "sum"),
        wins=("won", "sum"), positive_profit=("profit", lambda s: s.clip(lower=0).sum()),
        absolute_loss=("profit", lambda s: -s.clip(upper=0).sum()))
    curve = curve.merge(daily, on=["episode_id", "match_date"], how="left", validate="one_to_one")
    for column in daily:
        curve[column] = curve[column].fillna(0)
    _near(curve.bet_count, curve.check_bet_count, "Date bet count")
    _near(curve.turnover, curve.check_turnover, "Date turnover")
    _near(curve.profit, curve.check_profit, "Date profit")
    _near(curve.bet_count.sum(), len(positions), "Total bet count")
    risks = []
    for episode, part in curve.groupby("episode_id", sort=False):
        starts = initial_bankroll + part.profit.cumsum().shift(fill_value=0)
        ends = initial_bankroll + part.profit.cumsum()
        _near(part.start_bankroll, starts, "Episode start bankroll")
        _near(part.end_bankroll, ends, "Episode end bankroll")
        if part.start_bankroll.lt(-1e-7).any() or part.end_bankroll.lt(-1e-7).any():
            raise ValueError("Negative bankroll in recorded equity")
        if part.turnover.gt(part.start_bankroll + 1e-7).any():
            raise ValueError("Date commitment exceeds available bankroll")
        returns = np.divide(part.profit, part.start_bankroll, out=np.zeros(len(part)), where=part.start_bankroll.to_numpy(float) > 0)
        _near(part.daily_return, returns, "Date return")
        wealth = np.concatenate(([initial_bankroll], part.end_bankroll.to_numpy(float)))
        peaks = np.maximum.accumulate(wealth)
        dd = 1 - wealth / peaks
        if "drawdown" in part:
            _near(part.drawdown, dd[1:], "Date drawdown")
        growth = float(math.log(wealth[-1] / initial_bankroll)) if wealth[-1] > 0 else -math.inf
        risks.append({"episode": episode, "max_drawdown": float(dd.max()), "final_bankroll": float(wealth[-1]),
                      "log_growth": growth, "calendar_days": int((part.match_date.max() - part.match_date.min()).days + 1)})
    return positions, curve, risks


def _ratio(numerator, denominator):
    return float(numerator / denominator) if denominator > 0 else None


def _interval(values):
    finite = np.asarray(values, dtype=float)
    finite = finite[np.isfinite(finite)]
    return tuple(np.quantile(finite, [0.025, 0.975])) if len(finite) else (None, None)


def _bootstrap(curve, samples, seed):
    """Whole-date cashflow bootstrap, independently stratified by reset episode."""
    names = ("roi", "hit_ratio", "realized_expectancy_per_trade_units", "trading_frequency")
    empty = {name + "_ci_" + bound: None for name in names for bound in ("low", "high")}
    if samples == 0 or curve.empty:
        return {**empty, "bootstrap_samples": int(samples), "bootstrap_valid_roi_samples": 0}
    rng = np.random.default_rng(seed)
    totals = np.zeros((samples, 5), dtype=float)
    for _, group in curve.groupby("episode_id", sort=True):
        values = group[["profit", "turnover", "bet_count", "wins", "matched_matches"]].to_numpy(float)
        indices = rng.integers(0, len(values), size=(samples, len(values)))
        totals += values[indices].sum(axis=1)
    profit, turnover, count, wins, matched = totals.T
    numerators = (profit, wins, profit, count)
    denominators = (turnover, count, count, matched)
    result = {}
    for name, numerator, denominator in zip(names, numerators, denominators):
        estimates = np.divide(numerator, denominator, out=np.full(samples, np.nan), where=denominator > 0)
        low, high = _interval(estimates)
        result[name + "_ci_low"], result[name + "_ci_high"] = low, high
    return {**result, "bootstrap_samples": int(samples), "bootstrap_valid_roi_samples": int((turnover > 0).sum())}


def summarize_strategy(bets, equity, *, prediction_count, matched_valid_odds_count,
                       initial_bankroll=1000.0, bootstrap_samples=1000, random_state=42):
    """Flat statistics for one policy/scope, preserving separately funded episodes.

    Model expected components condition on recorded probabilities, odds and
    actual allocated stakes. Empirical conditional payoffs use realized net P&L.
    Neither is a claim about executable or future trading performance.
    """
    if not np.isfinite(initial_bankroll) or initial_bankroll <= 0:
        raise ValueError("Initial bankroll must be positive and finite")
    if not isinstance(bootstrap_samples, (int, np.integer)) or bootstrap_samples < 0:
        raise ValueError("Bootstrap samples must be a nonnegative integer")
    for count in (prediction_count, matched_valid_odds_count):
        if not isinstance(count, (int, np.integer)) or count < 0:
            raise ValueError("Opportunity counts must be nonnegative integers")
    if matched_valid_odds_count > prediction_count:
        raise ValueError("Matched priced fixtures exceed prediction count")
    positions, curve, risks = _prepare(bets, equity, initial_bankroll)
    n = len(positions)
    if n > matched_valid_odds_count:
        raise ValueError("Trade count exceeds matched priced fixtures")
    _near(curve.matched_matches.sum(), matched_valid_odds_count, "Matched priced fixture count")
    if prediction_count and curve.empty and matched_valid_odds_count:
        raise ValueError("Matched fixtures have no equity date universe")
    wins = int(positions.won.sum())
    losses = n - wins
    positive = positions.loc[positions.profit.gt(0), "profit"]
    negative = -positions.loc[positions.profit.lt(0), "profit"]
    win_gain = float(positive.mean()) if len(positive) else None
    loss_size = float(negative.mean()) if len(negative) else None
    profit, turnover = float(positions.profit.sum()), float(positions.stake.sum())
    gains, losses_total = float(positive.sum()), float(negative.sum())
    expected_gain = float(positions.expected_gain_units.sum())
    expected_loss = float(positions.expected_loss_units.sum())
    expected_net = expected_gain - expected_loss
    _near(expected_net, (positions.stake * (positions.probability * positions.odds - 1)).sum(), "Expected net payoff")
    episodes = len(risks)
    initial_capital = initial_bankroll * episodes
    final_capital = sum(item["final_bankroll"] for item in risks)
    _near(final_capital - initial_capital, profit, "Reset-aware capital profit")
    active_dates = int(curve.bet_count.gt(0).sum())
    dates = len(curve)
    calendar_days = sum(item["calendar_days"] for item in risks)
    factor = gains / losses_total if losses_total > 0 else math.inf if gains > 0 else None
    exposures = np.divide(curve.turnover, curve.start_bankroll, out=np.zeros(len(curve)), where=curve.start_bankroll.to_numpy(float) > 0)
    date_std = float(curve.daily_return.std(ddof=1)) if len(curve) > 1 else None
    date_mean = float(curve.daily_return.mean()) if len(curve) else None
    result = {
        "metric_status": "settled_archived_replay" if n else "no_trades",
        "bet_count": n, "winning_bet_count": wins, "losing_bet_count": losses,
        "hit_ratio": _ratio(wins, n),
        "avg_winning_gain_units": win_gain, "avg_losing_loss_units": loss_size,
        "avg_winning_return_per_unit_staked": float(positions.loc[positions.won, "realized_return_per_unit_staked"].mean()) if wins else None,
        "avg_losing_return_per_unit_staked": float(-positions.loc[~positions.won, "realized_return_per_unit_staked"].mean()) if losses else None,
        "empirical_gain_component_per_trade_units": _ratio(gains, n),
        "empirical_loss_component_per_trade_units": _ratio(losses_total, n),
        "realized_expectancy_per_trade_units": _ratio(profit, n),
        "expected_gain_total_units": expected_gain, "expected_loss_total_units": expected_loss,
        "expected_net_profit_total_units": expected_net,
        "expected_gain_per_trade_units": _ratio(expected_gain, n),
        "expected_loss_per_trade_units": _ratio(expected_loss, n),
        "expected_net_profit_per_trade_units": _ratio(expected_net, n),
        "expected_roi": _ratio(expected_net, turnover),
        "prediction_count": int(prediction_count), "matched_valid_odds_count": int(matched_valid_odds_count),
        "predictions_without_valid_prices": int(prediction_count - matched_valid_odds_count),
        "price_coverage": _ratio(matched_valid_odds_count, prediction_count),
        "trading_frequency": _ratio(n, matched_valid_odds_count),
        "trade_rate_all_predictions": _ratio(n, prediction_count),
        "matched_match_dates": dates, "active_betting_dates": active_dates,
        "active_date_fraction": _ratio(active_dates, dates), "bets_per_matched_match_date": _ratio(n, dates),
        "calendar_days_in_reset_scopes": calendar_days, "bets_per_calendar_week": _ratio(7 * n, calendar_days),
        "profit": profit, "turnover": turnover, "gross_return": float(positions.gross_return.sum()),
        "gross_winning_profit_units": gains, "gross_losing_loss_units": losses_total,
        "roi": _ratio(profit, turnover), "profit_factor": float(factor) if factor is not None else None,
        "profit_factor_status": "finite" if losses_total > 0 else "infinite_no_observed_losses" if gains > 0 else "undefined_no_trades",
        "payoff_ratio": _ratio(win_gain, loss_size) if win_gain is not None and loss_size is not None else None,
        "empirical_break_even_hit_ratio": _ratio(loss_size, win_gain + loss_size) if win_gain is not None and loss_size is not None else None,
        "avg_stake_units": float(positions.stake.mean()) if n else None,
        "min_stake_units": float(positions.stake.min()) if n else None,
        "max_stake_units": float(positions.stake.max()) if n else None,
        "avg_selected_probability": float(positions.probability.mean()) if n else None,
        "avg_decimal_odds": float(positions.odds.mean()) if n else None,
        "avg_model_expected_return_per_unit_staked": float(positions.model_expected_return_per_unit_staked.mean()) if n else None,
        "avg_realized_return_per_unit_staked": float(positions.realized_return_per_unit_staked.mean()) if n else None,
        "bankroll_reset_episodes": episodes,
        "initial_capital_sum_units": float(initial_capital), "final_capital_sum_units": float(final_capital),
        "return_on_initial_capital": _ratio(profit, initial_capital),
        "max_drawdown": max((item["max_drawdown"] for item in risks), default=None),
        "risk_basis": "worst_episode_date_close_drawdown_with_initial_capital",
        "min_episode_log_growth": min((item["log_growth"] for item in risks), default=None),
        "mean_episode_log_growth": float(np.mean([item["log_growth"] for item in risks])) if episodes else None,
        "date_return_mean": date_mean, "date_return_sample_std": date_std,
        "date_return_mean_to_std_unannualized": _ratio(date_mean, date_std) if date_std is not None and date_mean is not None else None,
        "max_date_capital_exposure": float(exposures.max()) if len(exposures) else None,
        "mean_date_capital_exposure": float(exposures.mean()) if len(exposures) else None,
        "uncertainty_method": "95% whole-matched-match-date percentile bootstrap stratified by bankroll-reset episode; recorded bets/stakes fixed; no refitting or multiple-comparison adjustment",
        "expectation_basis": "model_implied_probability_weighted_net_cash_components_at_recorded_allocated_stakes",
        "calendar_frequency_basis": "sum of inclusive first-to-last priced-match calendar spans per reset episode; no off-season gap between episodes",
        "empirical_break_even_basis": "descriptive mean-loss/(mean-win+mean-loss) for the observed payoff mix; not a universal odds threshold",
    }
    result.update(_bootstrap(curve, bootstrap_samples, random_state))
    return result
