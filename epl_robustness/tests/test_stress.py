"""Known fixed-exposure cost identities and infeasible funding paths."""
import math

import numpy as np
import pandas as pd
import pytest

from epl_robustness.stress import SCENARIOS, stress_group
from epl_strategy.metrics import reconstruct_equity, summarize_strategy


def bet(match_id, date, stake, odds, p, won):
    gross = stake * odds if won else 0.0
    return {"match_id": match_id, "match_date": date, "stake": stake, "odds": odds,
            "probability": p, "won": won, "gross_return": gross, "profit": gross-stake,
            "selection": "H", "result": "H" if won else "A"}


def sample():
    positions = pd.DataFrame([bet("m1", "2025-01-01", 10., 3., .5, True),
                              bet("m2", "2025-01-03", 20., 2., .7, False),
                              bet("m3", "2025-01-03", 5., 5., .2, True)])
    opportunities = pd.DataFrame({"match_id": ["m1", "m2", "m3", "m4"],
                                  "match_date": ["2025-01-01", "2025-01-03", "2025-01-03", "2025-01-14"]})
    equity = reconstruct_equity(positions, opportunities)
    original = summarize_strategy(positions, equity, prediction_count=5,
                                   matched_valid_odds_count=4, bootstrap_samples=0)
    return positions, equity, original


def scenario(name="custom", *, fee=0., haircut=0.):
    return {"scenario_id": name, "fee_rate": fee, "payout_haircut": haircut}


def test_zero_cost_matches_the_frozen_strategy_without_reselection():
    positions, equity, original = sample()
    rows, funding = stress_group(positions, equity, original, bootstrap_samples=0)
    assert len(rows) == len(SCENARIOS) == 9
    baseline = next(row for row in rows if row["scenario_id"] == "baseline")
    for key in ("bet_count", "winning_bet_count", "hit_ratio", "avg_winning_gain_units", "avg_losing_loss_units",
                "expected_gain_total_units", "expected_loss_total_units", "expected_net_profit_total_units",
                "expected_net_profit_per_trade_units", "realized_expectancy_per_trade_units", "expected_roi",
                "profit", "turnover", "gross_return", "roi", "profit_factor", "payoff_ratio",
                "trading_frequency", "trade_rate_all_predictions", "active_date_fraction", "max_drawdown"):
        assert baseline[key] == pytest.approx(original[key])
    assert baseline["funding_feasible"] is True
    assert baseline["required_additional_initial_capital_units"] == 0.0
    assert funding.loc[funding.scenario_id.eq("baseline"), "funding_breach_dates"].sum() == 0
    assert all(row["bet_count"] == 3 and row["hit_ratio"] == pytest.approx(2/3) for row in rows)
    assert all(row["trading_frequency"] == .75 for row in rows)


def test_haircut_targets_winning_net_payout_and_fee_applies_to_every_stake():
    positions, equity, original = sample()
    rows, _ = stress_group(positions, equity, original, bootstrap_samples=0,
                            scenarios=[scenario(fee=.1, haircut=.25)])
    row = rows[0]
    # Winning profits 20 and 20 become 14 and 14.5; the losing stake costs 22.
    assert row["profit"] == pytest.approx(6.5)
    assert row["gross_return"] == pytest.approx(45.)
    assert row["turnover"] == 35.
    assert row["fee_units"] == pytest.approx(3.5)
    assert row["profit"] == pytest.approx(row["gross_return"]-row["turnover"]-row["fee_units"])
    assert row["cash_outlay"] == pytest.approx(38.5)
    assert row["roi"] == pytest.approx(6.5/35)
    assert row["roi_on_cash_outlay"] == pytest.approx(6.5/38.5)
    assert row["avg_winning_gain_units"] == pytest.approx(14.25)
    assert row["avg_losing_loss_units"] == pytest.approx(22.)
    assert row["expected_gain_total_units"] == pytest.approx(19.)
    assert row["expected_loss_total_units"] == pytest.approx(16.5)
    assert row["expected_net_profit_total_units"] == pytest.approx(2.5)
    assert row["expected_roi"] == pytest.approx(2.5/35)
    assert row["funding_feasible"] is True
    assert row["max_drawdown"] == pytest.approx(7.5/1014)
    assert row["remaining_signed_break_even_fee_rate_at_haircut"] == pytest.approx(10/35)
    # This is total allowable fee at the haircut, not incremental headroom.
    assert row["remaining_signed_break_even_fee_rate_at_haircut"]-row["fee_rate"] == pytest.approx(row["roi"])


def test_analytic_break_even_fee_and_haircut_produce_zero_realized_profit():
    positions, equity, original = sample()
    definitions = [scenario("fee_break_even", fee=20/35), scenario("haircut_break_even", haircut=20/40)]
    rows, _ = stress_group(positions, equity, original, bootstrap_samples=0, scenarios=definitions)
    for row in rows:
        assert row["profit"] == pytest.approx(0., abs=1e-12)
        assert row["baseline_signed_break_even_fee_rate"] == pytest.approx(20/35)
        assert row["baseline_signed_break_even_payout_haircut"] == pytest.approx(.5)


def test_winning_outcome_can_lose_cash_without_changing_outcome_hit_ratio():
    positions = pd.DataFrame([bet("m1", "2025-01-01", 10., 1.5, .8, True)])
    equity = reconstruct_equity(positions, positions[["match_id", "match_date"]])
    original = {"prediction_count": 1, "matched_valid_odds_count": 1, "initial_capital_sum_units": 1000.}
    rows, _ = stress_group(positions, equity, original, bootstrap_samples=0,
                            scenarios=[scenario(fee=1.)])
    row = rows[0]
    assert row["hit_ratio"] == 1.
    assert row["winning_bet_count"] == 1
    assert row["profitable_trade_share"] == 0.
    assert row["loss_making_trade_count"] == 1
    assert row["profit"] == -5.
    assert row["avg_winning_gain_units"] is None
    assert row["avg_losing_loss_units"] == 5.
    assert row["avg_winning_outcome_net_payoff_units"] == -5.
    # If correct: -5; if incorrect: -20. Both possible payoffs are negative.
    assert row["expected_gain_total_units"] == 0.
    assert row["expected_loss_total_units"] == pytest.approx(8.)
    assert row["expected_net_profit_total_units"] == pytest.approx(-8.)
    assert row["roi_on_cash_outlay"] == -.25


def test_complete_winning_payout_haircut_returns_stake_without_inventing_a_loss():
    positions = pd.DataFrame([bet("m1", "2025-01-01", 10., 1.5, .8, True)])
    equity = reconstruct_equity(positions, positions[["match_id", "match_date"]])
    rows, _ = stress_group(positions, equity, {"prediction_count": 1, "matched_valid_odds_count": 1},
                            bootstrap_samples=0, scenarios=[scenario(haircut=1.)])
    row = rows[0]
    assert row["gross_return"] == 10.
    assert row["profit"] == row["roi"] == 0.
    assert row["hit_ratio"] == 1.
    assert row["profitable_trade_count"] == row["loss_making_trade_count"] == 0
    assert row["avg_winning_gain_units"] is row["avg_losing_loss_units"] is None
    assert row["expected_net_profit_total_units"] == pytest.approx(-2.)


def test_no_trades_keep_cash_zero_and_per_trade_ratios_undefined_in_all_scenarios():
    positions, equity, original = sample()
    opportunities = pd.DataFrame({"match_id": ["m1", "m2"], "match_date": ["2025-01-01", "2025-01-14"]})
    empty = positions.iloc[:0]
    equity = reconstruct_equity(empty, opportunities)
    rows, funding = stress_group(empty, equity, {"prediction_count": 3, "matched_valid_odds_count": 2}, bootstrap_samples=0)
    for row in rows:
        for key in ("bet_count", "profit", "turnover", "fee_units", "expected_gain_total_units", "expected_loss_total_units",
                    "expected_net_profit_total_units", "trading_frequency", "trade_rate_all_predictions", "max_drawdown"):
            assert row[key] == 0
        for key in ("hit_ratio", "roi", "expected_roi", "avg_winning_gain_units", "avg_losing_loss_units",
                    "expected_net_profit_per_trade_units", "realized_expectancy_per_trade_units"):
            assert row[key] is None
        assert row["funding_feasible"] is True
        assert row["metric_status"] == "no_trades"
    assert funding.funding_breach_dates.sum() == 0


def test_upfront_fee_can_make_a_profitable_positive_cash_path_unfundable():
    positions = pd.DataFrame([bet("m1", "2025-01-01", 1000., 3., .6, True)])
    equity = reconstruct_equity(positions, positions[["match_id", "match_date"]])
    rows, funding = stress_group(positions, equity, {"prediction_count": 1, "matched_valid_odds_count": 1},
                                  bootstrap_samples=0, scenarios=[scenario(fee=.01)])
    row = rows[0]
    assert row["profit"] == 1990.
    assert row["funding_feasible"] is False
    assert row["max_drawdown"] is None
    assert row["shadow_max_drawdown"] == 0.
    assert row["required_additional_initial_capital_units"] == 10.
    assert funding.iloc[0].first_funding_breach_date == "2025-01-01"


def test_insolvent_shadow_path_never_clips_cash_resizes_stakes_or_drops_later_bets():
    positions = pd.DataFrame([bet("m1", "2025-01-01", 999., 2., .6, False),
                              bet("m2", "2025-01-02", .5, 2., .6, True)])
    equity = reconstruct_equity(positions, positions[["match_id", "match_date"]])
    rows, funding = stress_group(positions, equity, {"prediction_count": 2, "matched_valid_odds_count": 2},
                                  bootstrap_samples=0, scenarios=[scenario(fee=.02)])
    row = rows[0]
    assert row["bet_count"] == 2
    assert row["turnover"] == 999.5
    assert row["profit"] == pytest.approx(-1018.49)
    assert row["final_shadow_capital_sum_units"] == pytest.approx(-18.49)
    assert row["min_shadow_bankroll_units"] == pytest.approx(-18.98)
    assert row["required_additional_initial_capital_units"] == pytest.approx(19.49)
    assert row["funding_breach_dates"] == 2
    assert row["funding_feasible"] is False
    assert row["max_drawdown"] is None
    assert row["shadow_max_drawdown"] == pytest.approx(1.01898)
    assert row["metric_status"] == "unfundable_shadow_cashflow_only"
    assert funding.iloc[0].episode_log_growth is None


def test_pooled_extra_capital_is_sum_of_independent_episode_shortfalls():
    first = pd.DataFrame([bet("shared", "2024-01-01", 1000., 3., .6, True)])
    second = pd.DataFrame([bet("shared", "2025-01-01", 1000., 2., .6, False)])
    first["episode_id"], second["episode_id"] = "A", "B"
    # The loss exhausts B's baseline capital: log growth is intentionally -inf.
    with np.errstate(divide="ignore"):
        equity = pd.concat([reconstruct_equity(first, first[["match_id", "match_date"]], episode_id="A"),
                            reconstruct_equity(second, second[["match_id", "match_date"]], episode_id="B")], ignore_index=True)
    positions = pd.concat([first, second], ignore_index=True)
    rows, funding = stress_group(positions, equity, {"prediction_count": 2, "matched_valid_odds_count": 2,
                                  "initial_capital_sum_units": 2000.}, bootstrap_samples=0,
                                  scenarios=[scenario(fee=.01)])
    row = rows[0]
    assert row["bankroll_reset_episodes"] == 2
    assert row["initial_capital_sum_units"] == 2000.
    assert row["required_additional_initial_capital_units"] == 20.
    assert row["infeasible_episode_count"] == 2
    assert row["max_drawdown"] is None
    assert row["shadow_max_drawdown"] == pytest.approx(1.01)
    assert sorted(funding.diagnostic_episode_id) == ["A", "B"]


def test_negative_break_even_rate_is_preserved_instead_of_claiming_cost_capacity():
    positions = pd.DataFrame([bet("m1", "2025-01-01", 10., 1.5, .5, True),
                              bet("m2", "2025-01-02", 20., 2., .5, False)])
    equity = reconstruct_equity(positions, positions[["match_id", "match_date"]])
    rows, _ = stress_group(positions, equity, {"prediction_count": 2, "matched_valid_odds_count": 2},
                            bootstrap_samples=0, scenarios=[scenario()])
    assert rows[0]["baseline_signed_break_even_fee_rate"] == -.5
    assert rows[0]["baseline_signed_break_even_payout_haircut"] == -3.


def test_same_date_bootstrap_draws_are_reused_for_exact_fee_only_roi_shift():
    positions, equity, original = sample()
    original = summarize_strategy(positions, equity, prediction_count=5,
                                   matched_valid_odds_count=4, bootstrap_samples=100, random_state=42)
    rows, _ = stress_group(positions, equity, original, bootstrap_samples=100, random_state=42,
                            scenarios=[scenario("baseline"), scenario("fee", fee=.01)])
    baseline, fee = rows
    for bound in ("low", "high"):
        assert baseline["roi_ci_"+bound] == pytest.approx(original["roi_ci_"+bound])
        assert fee["roi_ci_"+bound] == pytest.approx(baseline["roi_ci_"+bound]-.01)
        assert fee["hit_ratio_ci_"+bound] == baseline["hit_ratio_ci_"+bound]
        assert fee["trading_frequency_ci_"+bound] == baseline["trading_frequency_ci_"+bound]
    assert fee["bootstrap_valid_roi_samples"] == baseline["bootstrap_valid_roi_samples"]


@pytest.mark.parametrize("definition", [scenario(fee=-.1), scenario(fee=float("nan")),
                                       scenario(haircut=-.1), scenario(haircut=1.1), scenario(haircut=math.inf)])
def test_invalid_cost_definitions_are_rejected(definition):
    positions, equity, original = sample()
    with pytest.raises(ValueError):
        stress_group(positions, equity, original, bootstrap_samples=0, scenarios=[definition])


def test_duplicate_scenario_id_is_rejected():
    positions, equity, original = sample()
    with pytest.raises(ValueError, match="unique"):
        stress_group(positions, equity, original, bootstrap_samples=0, scenarios=[scenario(), scenario(fee=.01)])
