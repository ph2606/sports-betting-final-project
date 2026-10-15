"""Catch cash, opening-funding, attribution and graph defects independently."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from epl_execution.audit import (UNFUNDED_WITHHELD, _audit_account, _audit_attribution,
                                 _audit_fixed_identity, _audit_graph, _audit_reference_identity)


def funded_example():
    bets = pd.DataFrame({"match_id": ["m1", "m2"], "match_date": ["2025-08-15", "2025-08-16"],
        "selection": ["H", "A"], "result": ["H", "H"], "probability": [.6, .6],
        "odds": [2., 2.], "stake": [1000., 1000.], "won": [True, False],
        "gross_return": [2000., 0.], "profit": [1000., -1000.]})
    equity = pd.DataFrame({"match_date": ["2025-08-15", "2025-08-16"], "matched_matches": [1, 1],
        "bet_count": [1, 1], "turnover": [1000., 1000.], "profit": [1000., -1000.],
        "start_bankroll": [100000., 101000.], "end_bankroll": [101000., 100000.],
        "drawdown": [0., 1 - 100000 / 101000]})
    metric = {"execution_mode": "reference_replay", "funding_feasible": True,
        "initial_capital_sum_units": 100000., "final_capital_sum_units": 100000.,
        "return_on_initial_capital": 0., "max_drawdown": 1 - 100000 / 101000,
        "bet_count": 2, "winning_bet_count": 1, "losing_bet_count": 1, "hit_ratio": .5,
        "profit": 0., "turnover": 2000., "gross_return": 2000., "roi": 0.,
        "matched_valid_odds_count": 2, "prediction_count": 2, "trading_frequency": 1.,
        "trade_rate_all_predictions": 1., "expected_gain_total_units": 1200.,
        "expected_loss_total_units": 800., "expected_net_profit_total_units": 400.,
        "expected_roi": .2, "expected_gain_per_trade_units": 600., "expected_loss_per_trade_units": 400.,
        "realized_expectancy_per_trade_units": 0., "avg_winning_gain_units": 1000., "avg_losing_loss_units": 1000.}
    return metric, bets, equity


def test_hand_cash_account_reconciles_with_native_identities():
    metric, bets, equity = funded_example()
    native = bets[["match_id", "match_date", "result"]].assign(season="2025-26")
    assert _audit_account(metric, bets, equity, opportunities=native) == {
        "bet_count": 2, "funding_feasible": True, "profit": 0.}


@pytest.mark.parametrize("column,new_value", [("profit", [1001., -1000.]),
    ("won", [False, False]), ("gross_return", [1000., 0.])])
def test_audit_rejects_falsified_trade_cashflow(column, new_value):
    metric, bets, equity = funded_example()
    bets[column] = new_value
    with pytest.raises(AssertionError):
        _audit_account(metric, bets, equity)


def test_audit_rejects_trading_frequency_with_wrong_population_denominator():
    metric, bets, equity = funded_example()
    metric["trading_frequency"] = .5
    with pytest.raises(AssertionError, match="trading_frequency"):
        _audit_account(metric, bets, equity)


def test_audit_rejects_intraday_financing_even_when_closing_cash_is_positive():
    metric, bets, equity = funded_example()
    # Both bets settle on the same date; a second stake cannot use first-bet proceeds.
    bets["match_date"] = "2025-08-15"
    bets["stake"] = 60000.
    bets["gross_return"] = [120000., 0.]
    bets["profit"] = [60000., -60000.]
    equity = pd.DataFrame({"match_date": ["2025-08-15"], "matched_matches": [2], "bet_count": [2],
        "turnover": [120000.], "profit": [0.], "start_bankroll": [100000.], "end_bankroll": [100000.]})
    metric.update({"turnover": 120000., "gross_return": 120000., "expected_gain_total_units": 72000.,
        "expected_loss_total_units": 48000., "expected_net_profit_total_units": 24000.,
        "expected_gain_per_trade_units": 36000., "expected_loss_per_trade_units": 24000.,
        "avg_winning_gain_units": 60000., "avg_losing_loss_units": 60000.})
    with pytest.raises(AssertionError, match="funding flag"):
        _audit_account(metric, bets, equity)


def shadow_example():
    metric, bets, equity = funded_example()
    # Lose on date one, win on date two: all closing balances are positive,
    # yet the second 60,000 commitment exceeds its 40,000 opening cash.
    bets["selection"] = ["A", "H"]
    bets["result"] = ["H", "H"]
    bets["probability"] = .5
    bets["stake"] = 60000.
    bets["won"] = [False, True]
    bets["gross_return"] = [0., 120000.]
    bets["profit"] = [-60000., 60000.]
    equity["turnover"] = 60000.
    equity["profit"] = [-60000., 60000.]
    equity["start_bankroll"] = [100000., 40000.]
    equity["end_bankroll"] = [40000., 100000.]
    equity["shadow_start_balance"] = [100000., 40000.]
    equity["shadow_end_balance"] = [40000., 100000.]
    equity["funding_shortfall_units"] = [0., 20000.]
    equity["date_funding_feasible"] = [True, False]
    equity["drawdown"] = np.nan
    metric.update({"execution_mode": "fixed_exposure_reference", "funding_feasible": False,
        "turnover": 120000., "gross_return": 120000., "expected_gain_total_units": 60000.,
        "expected_loss_total_units": 60000., "expected_net_profit_total_units": 0., "expected_roi": 0.,
        "expected_gain_per_trade_units": 30000., "expected_loss_per_trade_units": 30000.,
        "avg_winning_gain_units": 60000., "avg_losing_loss_units": 60000.,
        "max_funding_shortfall_units": 20000., "minimum_additional_opening_cash_units": 20000.,
        "funding_breach_dates": 1, "shadow_final_balance": 100000., "shadow_min_balance": 40000.,
        "shadow_max_drawdown": .6})
    metric.update({key: np.nan for key in UNFUNDED_WITHHELD})
    return metric, bets, equity


def test_shadow_gap_uses_opening_commitment_not_closing_deficit():
    metric, bets, equity = shadow_example()
    assert equity.end_bankroll.min() > 0
    assert _audit_account(metric, bets, equity)["funding_feasible"] is False
    metric["max_funding_shortfall_units"] = 0
    with pytest.raises(AssertionError, match="max_funding_shortfall"):
        _audit_account(metric, bets, equity)


@pytest.mark.parametrize("key", ["max_drawdown", "final_capital_sum_units", "roi_ci_low"])
def test_unfunded_shadow_must_withhold_capital_risk_and_intervals(key):
    metric, bets, equity = shadow_example()
    metric[key] = .1
    with pytest.raises(AssertionError, match="withhold"):
        _audit_account(metric, bets, equity)


def test_native_opportunity_result_conflict_is_rejected():
    metric, bets, equity = funded_example()
    native = bets[["match_id", "match_date", "result"]].assign(season="2025-26")
    native.loc[0, "result"] = "D"
    with pytest.raises(AssertionError, match="Native bet result conflict"):
        _audit_account(metric, bets, equity, opportunities=native)


def test_attribution_independently_checks_both_probability_and_price_identities():
    frame = pd.DataFrame({"account_id": ["a"], "actual_profit": [70.], "model_expected_profit": [45.],
        "market_implied_expected_profit": [10.], "model_probability_premium": [35.],
        "outcome_residual": [60.], "payoff_forecast_error": [25.],
        "archived_ref_fixed_bet_profit": [50.], "realized_price_uplift_vs_reference": [20.]})
    _audit_attribution(frame)
    frame["realized_price_uplift_vs_reference"] = 21.
    with pytest.raises(AssertionError, match="Price contribution"):
        _audit_attribution(frame)


def test_graph_has_all_curves_shared_100k_anchor_and_metric_endpoint():
    graph = pd.DataFrame({"strategy_id": ["S1", "S1", "S2", "S2"],
        "match_date": ["2022-08-04", "2026-05-24"] * 2,
        "end_bankroll": [100000., 101000., 100000., 99000.], "is_initial": [True, False] * 2})
    metrics = pd.DataFrame({"strategy_id": ["S1", "S2"], "profit": [1000., -1000.]})
    _audit_graph(graph, metrics, {"S1", "S2"}, dates_per_account=2)
    graph.loc[2, "end_bankroll"] = 99999.
    with pytest.raises(AssertionError, match="initial capital"):
        _audit_graph(graph, metrics, {"S1", "S2"}, dates_per_account=2)


def test_graph_rejects_different_calendar_dates_across_strategies():
    graph = pd.DataFrame({"strategy_id": ["S1", "S1", "S2", "S2"],
        "match_date": ["2022-08-04", "2026-05-24", "2022-08-04", "2026-05-23"],
        "end_bankroll": [100000., 101000., 100000., 99000.], "is_initial": [True, False] * 2})
    metrics = pd.DataFrame({"strategy_id": ["S1", "S2"], "profit": [1000., -1000.]})
    with pytest.raises(AssertionError, match="share all calendar"):
        _audit_graph(graph, metrics, {"S1", "S2"}, dates_per_account=2)


def test_already_reference_identity_rejects_different_stakes_even_with_same_trade_count():
    _, bets, equity = funded_example()
    _audit_reference_identity(bets, equity, bets.copy(), equity.copy())
    changed = bets.copy()
    changed.loc[0, "stake"] = 999.
    with pytest.raises(AssertionError, match="Already-reference bet stake"):
        _audit_reference_identity(bets, equity, changed, equity.copy())


def test_fixed_exposure_keeps_expected_and_realized_price_contributions_separate():
    _, bets, _ = funded_example()
    original = bets.copy()
    original["odds"] = [2.2, 2.4]
    original["gross_return"] = [2200., 0.]
    original["profit"] = [1200., -1000.]
    # Realized improvement: only the winning bet's 0.2*1000 =200.
    # Expected improvement: .6*1000*(.2+.4)=360.
    _audit_fixed_identity(original, bets, {"actual_quote_uplift_units": 200., "model_expected_quote_uplift_units": 360.})
    with pytest.raises(AssertionError, match="model_expected_quote_uplift"):
        _audit_fixed_identity(original, bets, {"actual_quote_uplift_units": 200., "model_expected_quote_uplift_units": 200.})
