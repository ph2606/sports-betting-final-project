"""Hand-calculated payoffs, opportunity coverage and reset-aware risk checks."""
import math

import pandas as pd
import pytest

from epl_strategy.metrics import reconstruct_equity, summarize_strategy


def bet(match_id, match_date, stake, odds, probability, *, won):
    gross = stake * odds if won else 0.0
    return {"match_id": match_id, "match_date": match_date, "stake": stake, "odds": odds,
            "probability": probability, "won": won, "gross_return": gross, "profit": gross - stake,
            "selection": "H", "result": "H" if won else "A"}


def sample():
    # The second date contains offsetting bets: its date-close profit is zero.
    positions = pd.DataFrame([
        bet("m1", "2025-01-01", 10.0, 3.0, 0.5, won=True),
        bet("m2", "2025-01-03", 20.0, 2.0, 0.7, won=False),
        bet("m3", "2025-01-03", 5.0, 5.0, 0.2, won=True),
    ])
    positions["date_start_bankroll"] = [1000.0, 1020.0, 1020.0]
    positions["date_end_bankroll"] = 1020.0
    opportunities = pd.DataFrame({"match_id": ["m1", "m2", "m3", "m4"],
                                  "match_date": ["2025-01-01", "2025-01-03", "2025-01-03", "2025-01-14"]})
    return positions, opportunities


def summary(positions, opportunities, *, predictions=5, **kwargs):
    equity = reconstruct_equity(positions, opportunities)
    return summarize_strategy(positions, equity, prediction_count=predictions,
                              matched_valid_odds_count=len(opportunities), bootstrap_samples=0, **kwargs)


def test_nonuniform_probabilities_and_stakes_distinguish_all_payoff_definitions():
    positions, opportunities = sample()
    actual = summary(positions, opportunities)
    assert actual["bet_count"] == 3
    assert actual["winning_bet_count"] == 2
    assert actual["losing_bet_count"] == 1
    assert actual["hit_ratio"] == pytest.approx(2 / 3)
    assert actual["avg_winning_gain_units"] == pytest.approx(20.0)
    assert actual["avg_losing_loss_units"] == pytest.approx(20.0)
    assert actual["gross_return"] == pytest.approx(55.0)
    assert actual["gross_winning_profit_units"] == pytest.approx(40.0)
    assert actual["gross_losing_loss_units"] == pytest.approx(20.0)
    assert actual["profit"] == pytest.approx(20.0)
    assert actual["turnover"] == pytest.approx(35.0)
    assert actual["roi"] == pytest.approx(20 / 35)
    assert actual["profit_factor"] == pytest.approx(2.0)
    assert actual["payoff_ratio"] == pytest.approx(1.0)
    assert actual["realized_expectancy_per_trade_units"] == pytest.approx(20 / 3)
    # Expected winning components: 10+14+4; losing components: 5+6+4.
    assert actual["expected_gain_total_units"] == pytest.approx(28.0)
    assert actual["expected_loss_total_units"] == pytest.approx(15.0)
    assert actual["expected_net_profit_total_units"] == pytest.approx(13.0)
    assert actual["expected_net_profit_per_trade_units"] == pytest.approx(13 / 3)
    assert actual["expected_roi"] == pytest.approx(13 / 35)
    # Averaging each bet's return differs from profit/turnover when stakes vary.
    assert actual["avg_realized_return_per_unit_staked"] == pytest.approx(5 / 3)
    assert actual["avg_realized_return_per_unit_staked"] != pytest.approx(actual["roi"])


def test_activity_uses_all_priced_opportunities_and_inclusive_calendar_span():
    positions, opportunities = sample()
    actual = summary(positions, opportunities)
    assert actual["trading_frequency"] == pytest.approx(3 / 4)
    assert actual["trade_rate_all_predictions"] == pytest.approx(3 / 5)
    assert actual["active_betting_dates"] == 2
    assert actual["matched_match_dates"] == 3
    assert actual["active_date_fraction"] == pytest.approx(2 / 3)
    assert actual["calendar_days_in_reset_scopes"] == 14
    assert actual["bets_per_calendar_week"] == pytest.approx(1.5)
    assert actual["price_coverage"] == pytest.approx(4 / 5)


def test_equity_batches_same_date_and_retains_no_trade_opportunity_date():
    positions, opportunities = sample()
    equity = reconstruct_equity(positions, opportunities)
    assert equity.bet_count.tolist() == [1, 2, 0]
    assert equity.matched_matches.tolist() == [1, 2, 1]
    assert equity.turnover.tolist() == [10.0, 25.0, 0.0]
    assert equity.profit.tolist() == [20.0, 0.0, 0.0]
    assert equity.start_bankroll.tolist() == [1000.0, 1020.0, 1020.0]
    assert equity.end_bankroll.tolist() == [1020.0, 1020.0, 1020.0]
    assert equity.drawdown.eq(0).all()
    assert summary(positions, opportunities)["max_drawdown"] == 0.0


def test_first_date_loss_is_measured_against_initial_capital():
    positions = pd.DataFrame([bet("m1", "2025-01-01", 100.0, 2.0, 0.6, won=False)])
    opportunities = positions[["match_id", "match_date"]]
    actual = summary(positions, opportunities, predictions=1)
    assert actual["max_drawdown"] == pytest.approx(0.1)
    assert actual["return_on_initial_capital"] == pytest.approx(-0.1)


def test_no_trades_have_zero_cash_totals_but_no_conditional_payoff_or_hit_estimate():
    positions, opportunities = sample()
    positions = positions.iloc[:0]
    actual = summary(positions, opportunities)
    for key in ("bet_count", "winning_bet_count", "losing_bet_count", "profit", "turnover", "gross_return",
                "expected_gain_total_units", "expected_loss_total_units", "expected_net_profit_total_units",
                "trading_frequency", "trade_rate_all_predictions", "active_date_fraction", "bets_per_calendar_week",
                "max_drawdown", "return_on_initial_capital"):
        assert actual[key] == 0
    for key in ("hit_ratio", "avg_winning_gain_units", "avg_losing_loss_units", "expected_net_profit_per_trade_units",
                "realized_expectancy_per_trade_units", "expected_roi", "roi", "profit_factor", "payoff_ratio"):
        assert actual[key] is None
    assert actual["metric_status"] == "no_trades"


def test_no_price_coverage_is_unavailable_frequency_not_zero_opportunity_rate():
    positions, opportunities = sample()
    equity = reconstruct_equity(positions.iloc[:0], opportunities.iloc[:0])
    actual = summarize_strategy(positions.iloc[:0], equity, prediction_count=5,
                                matched_valid_odds_count=0, bootstrap_samples=0)
    assert actual["trading_frequency"] is None
    assert actual["active_date_fraction"] is None
    assert actual["bets_per_calendar_week"] is None
    assert actual["trade_rate_all_predictions"] == 0.0
    assert actual["price_coverage"] == 0.0
    assert actual["max_drawdown"] is None


def test_no_observed_losses_does_not_invent_a_conditional_mean_loss():
    positions = pd.DataFrame([bet("m1", "2025-01-01", 10.0, 3.0, 0.5, won=True)])
    actual = summary(positions, positions[["match_id", "match_date"]], predictions=1)
    assert actual["hit_ratio"] == 1.0
    assert actual["avg_winning_gain_units"] == 20.0
    assert actual["avg_losing_loss_units"] is None
    assert actual["payoff_ratio"] is None
    assert math.isinf(actual["profit_factor"]) and actual["profit_factor"] > 0
    assert actual["profit_factor_status"] == "infinite_no_observed_losses"


def test_no_observed_wins_still_has_a_defined_negative_empirical_expectancy():
    positions = pd.DataFrame([bet("m1", "2025-01-01", 10.0, 3.0, 0.5, won=False)])
    actual = summary(positions, positions[["match_id", "match_date"]], predictions=1)
    assert actual["hit_ratio"] == 0.0
    assert actual["avg_winning_gain_units"] is None
    assert actual["avg_losing_loss_units"] == 10.0
    assert actual["payoff_ratio"] is None
    assert actual["profit_factor"] == 0.0
    assert actual["realized_expectancy_per_trade_units"] == -10.0
    assert actual["expected_net_profit_per_trade_units"] == 5.0


def test_pooled_risk_preserves_capital_resets_and_episode_fixture_identity():
    # A finishes at 200; B starts with new capital of 100 and finishes at 90.
    # Concatenating their balances would invent a 55% drawdown; B's loss is 10%.
    first = pd.DataFrame([bet("m1", "2024-01-01", 50.0, 3.0, 0.5, won=True)])
    second = pd.DataFrame([bet("m1", "2025-01-01", 10.0, 2.0, 0.6, won=False)])
    first["episode_id"], second["episode_id"] = "A", "B"
    first_opp = pd.DataFrame({"match_id": ["m1", "m2"], "match_date": ["2024-01-01", "2024-01-07"]})
    second_opp = pd.DataFrame({"match_id": ["m1", "m2"], "match_date": ["2025-01-01", "2025-01-07"]})
    equity = pd.concat([reconstruct_equity(first, first_opp, initial_bankroll=100.0, episode_id="A"),
                        reconstruct_equity(second, second_opp, initial_bankroll=100.0, episode_id="B")], ignore_index=True)
    positions = pd.concat([first, second], ignore_index=True)
    actual = summarize_strategy(positions, equity, prediction_count=4, matched_valid_odds_count=4,
                                initial_bankroll=100.0, bootstrap_samples=0)
    assert actual["bankroll_reset_episodes"] == 2
    assert actual["initial_capital_sum_units"] == 200.0
    assert actual["final_capital_sum_units"] == 290.0
    assert actual["profit"] == 90.0
    assert actual["return_on_initial_capital"] == pytest.approx(0.45)
    assert actual["max_drawdown"] == pytest.approx(0.1)
    assert actual["risk_basis"] == "worst_episode_date_close_drawdown_with_initial_capital"
    assert actual["trading_frequency"] == 0.5
    assert actual["calendar_days_in_reset_scopes"] == 14
    # Removing episode IDs would make identical fixture IDs ambiguous.
    with pytest.raises(ValueError, match="explicit episode"):
        summarize_strategy(positions.drop(columns="episode_id"), equity, prediction_count=4,
                           matched_valid_odds_count=4, initial_bankroll=100.0, bootstrap_samples=0)


@pytest.mark.parametrize("field,value", [
    ("stake", 0.0), ("stake", -10.0), ("stake", float("inf")),
    ("probability", -0.1), ("probability", 1.1), ("probability", float("nan")),
    ("odds", 1.0), ("gross_return", 31.0), ("profit", 21.0), ("won", False),
    ("result", "A"), ("selection", "unknown"),
    ("date_start_bankroll", 999.0), ("date_end_bankroll", 1019.0),
])
def test_inconsistent_trade_values_are_rejected(field, value):
    positions, opportunities = sample()
    positions.loc[0, field] = value
    with pytest.raises(ValueError):
        reconstruct_equity(positions, opportunities)


def test_duplicate_bet_match_within_episode_is_rejected():
    positions, opportunities = sample()
    duplicate = pd.concat([positions, positions.iloc[[0]]], ignore_index=True)
    with pytest.raises(ValueError, match="Duplicate bet"):
        reconstruct_equity(duplicate, opportunities)


@pytest.mark.parametrize("kind", ["missing", "date", "duplicate"])
def test_trade_requires_unique_matching_priced_opportunity_identity(kind):
    positions, opportunities = sample()
    if kind == "missing":
        opportunities = opportunities.loc[opportunities.match_id.ne("m1")]
    elif kind == "date":
        opportunities.loc[0, "match_date"] = "2025-01-02"
    else:
        opportunities = pd.concat([opportunities, opportunities.iloc[[0]]], ignore_index=True)
    with pytest.raises(ValueError):
        reconstruct_equity(positions, opportunities)


def test_winning_trade_cannot_use_future_winnings_to_fund_excess_same_date_stake():
    positions = pd.DataFrame([bet("m1", "2025-01-01", 1001.0, 2.0, 0.6, won=True)])
    with pytest.raises(ValueError, match="date-start capital"):
        reconstruct_equity(positions, positions[["match_id", "match_date"]])


@pytest.mark.parametrize("predictions,matched", [(2, 4), (5, 2), (5, 5), (-1, 4), (5, 4.0)])
def test_summary_count_denominators_must_reconcile_to_equity(predictions, matched):
    positions, opportunities = sample()
    equity = reconstruct_equity(positions, opportunities)
    with pytest.raises(ValueError):
        summarize_strategy(positions, equity, prediction_count=predictions,
                           matched_valid_odds_count=matched, bootstrap_samples=0)


@pytest.mark.parametrize("field", ["profit", "turnover", "bet_count", "start_bankroll", "end_bankroll", "daily_return", "drawdown"])
def test_summary_rejects_corrupted_date_cash_or_risk_identity(field):
    positions, opportunities = sample()
    equity = reconstruct_equity(positions, opportunities)
    equity.loc[0, field] += 1
    with pytest.raises(ValueError):
        summarize_strategy(positions, equity, prediction_count=5,
                           matched_valid_odds_count=4, bootstrap_samples=0)


def test_whole_date_bootstrap_does_not_separate_offsetting_same_date_trades():
    positions, _ = sample()
    positions = positions.drop(columns=["date_start_bankroll", "date_end_bankroll"])
    positions["match_date"] = "2025-01-01"
    opportunities = positions[["match_id", "match_date"]]
    equity = reconstruct_equity(positions, opportunities)
    actual = summarize_strategy(positions, equity, prediction_count=3, matched_valid_odds_count=3,
                                bootstrap_samples=100, random_state=7)
    for metric in ("roi", "hit_ratio", "realized_expectancy_per_trade_units", "trading_frequency"):
        assert actual[metric + "_ci_low"] == pytest.approx(actual[metric])
        assert actual[metric + "_ci_high"] == pytest.approx(actual[metric])
    assert actual["bootstrap_valid_roi_samples"] == 100


def test_bootstrap_is_reproducible_for_the_predeclared_seed():
    positions, opportunities = sample()
    equity = reconstruct_equity(positions, opportunities)
    first = summarize_strategy(positions, equity, prediction_count=5, matched_valid_odds_count=4,
                               bootstrap_samples=100, random_state=42)
    second = summarize_strategy(positions, equity, prediction_count=5, matched_valid_odds_count=4,
                                bootstrap_samples=100, random_state=42)
    assert first == second
