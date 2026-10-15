"""Separate a new price-dependent policy replay from fixed-exposure attribution.

Reference replays reselect and resize using the existing frozen cash engine.
Fixed-exposure calculations preserve the original wagers, even if their new
cashflows cannot finance later commitments. Those cases remain shadow paths,
with no ordinary account-risk or confidence-interval performance claims.
"""
from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
import math

import numpy as np
import pandas as pd

from epl_strategy.metrics import enrich_bets, summarize_strategy
from epl_strategy_lab.engine import simulate_strategy
from epl_strategy_validation.inputs import validate_opportunities
from epl_strategy_validation.replay import replay as rolling_replay


OUTCOMES = ("H", "D", "A")
TOLERANCE = 1e-7
INTERVAL_NAMES = ("roi", "hit_ratio", "realized_expectancy_per_trade_units", "trading_frequency")


def _positive_initial(value):
    if isinstance(value, (bool, np.bool_)):
        raise ValueError("Initial bankroll must be positive and finite")
    try:
        value = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError("Initial bankroll must be positive and finite") from error
    if not math.isfinite(value) or value <= 0:
        raise ValueError("Initial bankroll must be positive and finite")
    return value


def _episode(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("A nonempty explicit episode_id is required")
    return value


def _near(left, right, label):
    if not np.allclose(np.asarray(left, dtype=float), np.asarray(right, dtype=float), rtol=1e-10, atol=TOLERANCE):
        raise ValueError(label + " identity does not reconcile")


def _config(config):
    if not isinstance(config, Mapping) or not isinstance(config.get("strategy_id"), str) or not config["strategy_id"]:
        raise ValueError("A strategy config with a nonempty strategy_id is required")
    return deepcopy(dict(config))


def reference_replay(config, models, opportunities, *, scope, episode_id, initial_bankroll=100000.0):
    """Change only ``odds_mode`` to reference before selection and allocation.

    Original probabilities, filters, consensus votes, sizing parameters and
    strategy identities remain unchanged. All requests on a date use its
    opening capital; the frozen engines enforce both stake and date caps.
    """
    native = validate_opportunities(opportunities)
    episode_id, initial = _episode(episode_id), _positive_initial(initial_bankroll)
    changed = _config(config)
    changed["odds_mode"] = "reference"
    if scope in {"single", "single_2025_26", "single_2025"}:
        if not native.season.eq("2025-26").all():
            raise ValueError("A single-season replay requires native 2025-26 identities")
        bets, equity = simulate_strategy(changed, models, native, initial_bankroll=initial)
        bets["episode_id"], equity["episode_id"] = episode_id, episode_id
        bets["season"] = bets.match_id.map(native.set_index("match_id").season)
        equity["season"] = equity.match_date.map(native[["match_date", "season"]].drop_duplicates().set_index("match_date").season)
    elif scope in {"continuous", "seasonal"}:
        if scope == "seasonal" and native.season.nunique() != 1:
            raise ValueError("A seasonal replay must contain exactly one native season")
        bets, equity = rolling_replay(changed, models, native, initial_bankroll=initial, episode_id=episode_id)
    else:
        raise ValueError("scope must be single, continuous or seasonal")
    for frame in (bets, equity):
        frame["view"] = "reference_replay"
        frame["funding_feasible"] = True
    return bets, equity


def _ratio(numerator, denominator):
    return float(numerator / denominator) if denominator > 0 else None


def _unfunded_descriptive_metrics(positions, curve, initial, bootstrap_samples):
    """Keep trade cashflow statistics while withholding funded-account claims."""
    n, wins = len(positions), int(positions.won.sum())
    losses = n - wins
    positive = positions.loc[positions.profit.gt(0), "profit"]
    negative = -positions.loc[positions.profit.lt(0), "profit"]
    gain, loss = float(positive.sum()), float(negative.sum())
    mean_gain = float(positive.mean()) if len(positive) else None
    mean_loss = float(negative.mean()) if len(negative) else None
    profit, turnover = float(positions.profit.sum()), float(positions.stake.sum())
    egain, eloss = float(positions.expected_gain_units.sum()), float(positions.expected_loss_units.sum())
    expected = egain - eloss
    matched, dates = int(curve.matched_matches.sum()), len(curve)
    active = int(curve.bet_count.gt(0).sum())
    days = int((curve.match_date.max() - curve.match_date.min()).days + 1)
    factor = gain / loss if loss > 0 else math.inf if gain > 0 else None
    result = {
        "metric_status": "unfunded_shadow_cashflow_only", "bet_count": n,
        "winning_bet_count": wins, "losing_bet_count": losses, "hit_ratio": _ratio(wins, n),
        "avg_winning_gain_units": mean_gain, "avg_losing_loss_units": mean_loss,
        "avg_winning_return_per_unit_staked": float(positions.loc[positions.won, "realized_return_per_unit_staked"].mean()) if wins else None,
        "avg_losing_return_per_unit_staked": float(-positions.loc[~positions.won, "realized_return_per_unit_staked"].mean()) if losses else None,
        "empirical_gain_component_per_trade_units": _ratio(gain, n),
        "empirical_loss_component_per_trade_units": _ratio(loss, n),
        "realized_expectancy_per_trade_units": _ratio(profit, n),
        "expected_gain_total_units": egain, "expected_loss_total_units": eloss,
        "expected_net_profit_total_units": expected,
        "expected_gain_per_trade_units": _ratio(egain, n), "expected_loss_per_trade_units": _ratio(eloss, n),
        "expected_net_profit_per_trade_units": _ratio(expected, n), "expected_roi": _ratio(expected, turnover),
        "prediction_count": matched, "matched_valid_odds_count": matched,
        "predictions_without_valid_prices": 0, "price_coverage": _ratio(matched, matched),
        "trading_frequency": _ratio(n, matched), "trade_rate_all_predictions": _ratio(n, matched),
        "matched_match_dates": dates, "active_betting_dates": active,
        "active_date_fraction": _ratio(active, dates), "bets_per_matched_match_date": _ratio(n, dates),
        "calendar_days_in_reset_scopes": days, "bets_per_calendar_week": _ratio(7 * n, days),
        "profit": profit, "turnover": turnover, "gross_return": float(positions.gross_return.sum()),
        "gross_winning_profit_units": gain, "gross_losing_loss_units": loss,
        "roi": _ratio(profit, turnover), "profit_factor": float(factor) if factor is not None else None,
        "profit_factor_status": "finite" if loss > 0 else "infinite_no_observed_losses" if gain > 0 else "undefined_no_trades",
        "payoff_ratio": _ratio(mean_gain, mean_loss) if mean_gain is not None and mean_loss is not None else None,
        "empirical_break_even_hit_ratio": _ratio(mean_loss, mean_gain + mean_loss) if mean_gain is not None and mean_loss is not None else None,
        "avg_stake_units": float(positions.stake.mean()) if n else None,
        "min_stake_units": float(positions.stake.min()) if n else None,
        "max_stake_units": float(positions.stake.max()) if n else None,
        "avg_selected_probability": float(positions.probability.mean()) if n else None,
        "avg_decimal_odds": float(positions.odds.mean()) if n else None,
        "avg_model_expected_return_per_unit_staked": float(positions.model_expected_return_per_unit_staked.mean()) if n else None,
        "avg_realized_return_per_unit_staked": float(positions.realized_return_per_unit_staked.mean()) if n else None,
        "bankroll_reset_episodes": 1, "initial_capital_sum_units": initial,
        "final_capital_sum_units": None, "return_on_initial_capital": None, "max_drawdown": None,
        "risk_basis": "unfunded_fixed_exposure_shadow_path; no self_financing_account_risk_statistics",
        "min_episode_log_growth": None, "mean_episode_log_growth": None,
        "date_return_mean": None, "date_return_sample_std": None,
        "date_return_mean_to_std_unannualized": None,
        "max_date_capital_exposure": None, "mean_date_capital_exposure": None,
        "uncertainty_method": "withheld_for_unfunded_fixed_exposure_shadow_cashflows",
        "expectation_basis": "model_implied_probability_weighted_cash_components_at_original_stakes_and_reference_odds",
        "calendar_frequency_basis": "inclusive first-to-last priced-match calendar span for this original account",
        "empirical_break_even_basis": "descriptive mean-loss/(mean-win+mean-loss) for observed payoff mix",
        "bootstrap_samples": 0, "requested_bootstrap_samples": int(bootstrap_samples),
        "bootstrap_valid_roi_samples": 0,
    }
    result.update({name + "_ci_" + bound: None for name in INTERVAL_NAMES for bound in ("low", "high")})
    return result


def fixed_exposure_reference(config, original_bets, opportunities, *, episode_id,
                             initial_bankroll=100000.0, bootstrap_samples=1000):
    """Reprice every original wager without rerunning eligibility or sizing.

    A stake may violate the original Kelly cap or qualify at a negative new
    edge: retaining it is necessary to isolate the price contribution. The
    maximum date-opening commitment gap is the additional opening cash needed
    to fund this recorded path, which can exceed its worst closing deficit.
    """
    original_config = _config(config)
    initial, episode_id = _positive_initial(initial_bankroll), _episode(episode_id)
    if not isinstance(bootstrap_samples, (int, np.integer)) or isinstance(bootstrap_samples, (bool, np.bool_)) or bootstrap_samples < 0:
        raise ValueError("bootstrap_samples must be a nonnegative integer")
    native = validate_opportunities(opportunities)
    required = [f"ref_odds_{label}" for label in OUTCOMES] + ["reference_bookmaker"]
    if not set(required).issubset(native):
        raise ValueError("Reference quote panel is incomplete")
    values = native[[f"ref_odds_{label}" for label in OUTCOMES]].apply(pd.to_numeric, errors="coerce").to_numpy(float)
    if not np.isfinite(values).all() or not (values > 1).all():
        raise ValueError("Reference odds must be complete, finite and above one")
    if not native.reference_bookmaker.eq("Bet365").all():
        raise ValueError("The reference quote bookmaker must be Bet365")
    positions = enrich_bets(original_bets)
    if not {"selection", "result"}.issubset(positions):
        raise ValueError("Original bets require explicit selection and result identities")
    if positions.match_id.duplicated().any():
        raise ValueError("Duplicate original bet match identity")
    if "strategy_id" in positions and not positions.strategy_id.eq(original_config["strategy_id"]).all():
        raise ValueError("Original bets belong to a different strategy")
    if "episode_id" in positions and (positions.episode_id.isna().any() or positions.episode_id.nunique() > 1):
        raise ValueError("Fixed exposure requires exactly one original account episode")
    by_id = native.set_index("match_id")
    if not positions.match_id.isin(by_id.index).all():
        raise ValueError("An original bet is absent from the opportunity universe")
    for column in ("match_date", "result"):
        if not positions[column].eq(positions.match_id.map(by_id[column])).all():
            raise ValueError("Original bet " + column + " conflicts with priced fixture identity")
    if "season" in positions and not positions.season.eq(positions.match_id.map(by_id.season)).all():
        raise ValueError("Original bet season conflicts with native priced fixture identity")
    positions = positions.sort_values(["match_date", "match_id"], kind="stable").reset_index(drop=True)
    positions["original_odds"], positions["original_profit"] = positions.odds.copy(), positions.profit.copy()
    positions["original_expected_net_profit_units"] = positions.expected_net_profit_units.copy()
    if "bookmaker" in positions:
        positions["original_bookmaker"] = positions.bookmaker.copy()
    if "episode_id" in positions:
        positions["original_episode_id"] = positions.episode_id.copy()
    positions["episode_id"] = episode_id
    if len(positions):
        aligned = by_id.reindex(positions.match_id)
        labels = positions.selection.map({label: i for i, label in enumerate(OUTCOMES)}).to_numpy(int)
        reference = aligned[[f"ref_odds_{label}" for label in OUTCOMES]].to_numpy(float)[np.arange(len(positions)), labels]
    else:
        reference = np.array([], dtype=float)
    positions["odds"] = reference
    positions["bookmaker"] = "Bet365"
    positions["odds_mode"] = "reference"
    positions["view"] = "fixed_exposure_reference"
    positions["season"] = positions.match_id.map(by_id.season)
    positions["edge"] = positions.probability * positions.odds - 1
    if "full_kelly_fraction" in positions:
        positions["original_full_kelly_fraction"] = positions.full_kelly_fraction.copy()
        positions["full_kelly_fraction"] = np.maximum(0., positions.edge / (positions.odds - 1))
    positions["exposure_basis"] = "original_allocated_stakes_preserved_without_new_price_requalification_or_resizing"
    positions["gross_return"] = positions.won.astype(float) * positions.stake * positions.odds
    positions["profit"] = positions.gross_return - positions.stake
    positions["actual_quote_uplift_units"] = positions.won.astype(float) * positions.stake * (positions.original_odds - positions.odds)
    positions["model_expected_quote_uplift_units"] = positions.probability * positions.stake * (positions.original_odds - positions.odds)
    positions = enrich_bets(positions)
    _near(positions.original_profit - positions.profit, positions.actual_quote_uplift_units, "Realized quote attribution")
    _near(positions.original_expected_net_profit_units - positions.expected_net_profit_units,
          positions.model_expected_quote_uplift_units, "Model quote attribution")
    if (positions.original_odds < positions.odds - TOLERANCE).any():
        raise ValueError("Original best/reference odds are below the reference price")

    curve = native.groupby("match_date", sort=True).agg(matched_matches=("match_id", "size"), season=("season", "first"))
    daily = positions.groupby("match_date").agg(bet_count=("match_id", "size"), turnover=("stake", "sum"), profit=("profit", "sum"))
    curve = curve.join(daily).fillna({"bet_count": 0, "turnover": 0., "profit": 0.})
    curve["bet_count"] = curve.bet_count.astype(int)
    curve["shadow_start_balance"] = initial + curve.profit.cumsum().shift(fill_value=0)
    curve["shadow_end_balance"] = initial + curve.profit.cumsum()
    curve["funding_shortfall_units"] = (curve.turnover - curve.shadow_start_balance).clip(lower=0)
    curve["date_funding_feasible"] = curve.funding_shortfall_units <= TOLERANCE
    feasible = bool(curve.date_funding_feasible.all())
    curve["funding_feasible"] = feasible
    curve["episode_id"], curve["strategy_id"] = episode_id, original_config["strategy_id"]
    curve["view"] = "fixed_exposure_reference"
    curve["curve_status"] = "fundable_fixed_exposure_attribution" if feasible else "unfunded_shadow_cashflow_only"
    # Standard columns permit audited funded summarization. For an unfunded
    # path these cash columns are shadow balances and every return/risk column
    # is withheld; explicit shadow aliases and status travel with every row.
    curve["start_bankroll"], curve["end_bankroll"] = curve.shadow_start_balance, curve.shadow_end_balance
    wealth = np.r_[initial, curve.shadow_end_balance.to_numpy(float)]
    peaks = np.maximum.accumulate(wealth)
    shadow_dd = 1 - wealth / peaks
    curve["shadow_running_peak"] = peaks[1:]
    curve["shadow_drawdown"] = shadow_dd[1:]
    curve["daily_return"] = np.divide(curve.profit, curve.shadow_start_balance,
        out=np.zeros(len(curve), dtype=float), where=curve.shadow_start_balance.to_numpy(float) > 0) if feasible else np.nan
    curve["running_peak"] = peaks[1:] if feasible else np.nan
    curve["drawdown"] = shadow_dd[1:] if feasible else np.nan
    curve["log_growth"] = np.log(curve.shadow_end_balance / initial,
        where=curve.shadow_end_balance.to_numpy(float) > 0, out=np.full(len(curve), -math.inf)) if feasible else np.nan
    for saved, column in (("date_start_bankroll", "shadow_start_balance"), ("date_end_bankroll", "shadow_end_balance"),
                          ("start_bankroll", "shadow_start_balance"), ("end_bankroll", "shadow_end_balance")):
        if saved in positions:
            positions["original_" + saved] = positions[saved].copy()
        positions[saved] = positions.match_date.map(curve[column])
    positions["shadow_date_start_balance"] = positions.match_date.map(curve.shadow_start_balance)
    positions["shadow_date_end_balance"] = positions.match_date.map(curve.shadow_end_balance)
    positions["funding_feasible"] = feasible
    curve = curve.reset_index()
    if feasible:
        metrics = summarize_strategy(positions, curve, prediction_count=len(native), matched_valid_odds_count=len(native),
            initial_bankroll=initial, bootstrap_samples=bootstrap_samples, random_state=42)
        metrics["metric_status"] = "fundable_fixed_exposure_attribution" if len(positions) else "no_trades"
    else:
        metrics = _unfunded_descriptive_metrics(positions, curve, initial, bootstrap_samples)
    first = curve.loc[~curve.date_funding_feasible, "match_date"]
    metrics.update({
        "view": "fixed_exposure_reference", "initial_bankroll": initial,
        "analysis_type": "fixed_original_selections_stakes_probabilities_reference_price_attribution",
        "selection_basis": "all original selections retained; no edge, odds-band or consensus requalification",
        "staking_basis": "original allocated stakes retained; no Kelly, capital-fraction or date-cap resizing",
        "funding_feasible": feasible, "funding_breach_dates": int((~curve.date_funding_feasible).sum()),
        "first_shortfall_date": str(first.iloc[0].date()) if len(first) else None,
        "max_funding_shortfall_units": float(curve.funding_shortfall_units.max()),
        "minimum_additional_opening_cash_units": float(curve.funding_shortfall_units.max()),
        "shadow_min_balance": float(wealth.min()), "shadow_final_balance": float(wealth[-1]),
        "shadow_return": float((wealth[-1] - initial) / initial),
        "shadow_max_drawdown": float(shadow_dd.max()),
        "actual_quote_uplift_units": float(positions.actual_quote_uplift_units.sum()),
        "model_expected_quote_uplift_units": float(positions.model_expected_quote_uplift_units.sum()),
        "original_profit": float(positions.original_profit.sum()),
        "original_expected_net_profit": float(positions.original_expected_net_profit_units.sum()),
        "shadow_path_can_require_external_funding": not feasible,
        "is_policy_replay": False,
    })
    return metrics, positions, curve
