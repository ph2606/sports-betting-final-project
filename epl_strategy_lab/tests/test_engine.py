from __future__ import annotations

from copy import deepcopy

import numpy as np
import pandas as pd
import pytest

from epl_strategy.metrics import summarize_strategy
from epl_strategy_lab.catalog import build_catalog
from epl_strategy_lab.engine import simulate_strategy


def config(**changes):
    value = deepcopy(build_catalog()[4])
    value.update(model_key="model", min_edge=.05, fixed_stake=1000., cash_only=False)
    value.update(changes)
    return value


def data(dates, *, probabilities=(.7, .2, .1), odds=(2., 3., 4.), results=None):
    n = len(dates)
    opportunities = pd.DataFrame({"match_id": [f"m{i}" for i in range(n)],
        "match_date": pd.to_datetime(dates), "season": "2025-26",
        "result": results if results is not None else ["H"] * n,
        "snapshot_type": "preclosing", "reference_bookmaker": "Bet365"})
    for label, price in zip("HDA", odds):
        opportunities[f"odds_{label}"] = price
        opportunities[f"ref_odds_{label}"] = price
        opportunities[f"bookmaker_{label}"] = "BestBook"
    frame = pd.DataFrame({"match_id": opportunities.match_id})
    frame[["p_H", "p_D", "p_A"]] = probabilities
    return {"model": frame.copy(), "baseline_market_only": frame.copy()}, opportunities


def test_catalog_preserves_all_declared_families_and_cash_controls():
    catalog = build_catalog()
    assert [row["strategy_id"] for row in catalog] == [f"S{i:03}" for i in range(1, 85)]
    assert sum(row["origin"] == "legacy" for row in catalog) == 38
    assert sum(row["origin"] == "legacy_diagnostic" for row in catalog) == 12
    assert sum(row["origin"] == "new" for row in catalog) == 34
    assert sum(row["cash_only"] for row in catalog) == 8
    catalog[0]["allowed_outcomes"].clear()
    assert build_catalog()[0]["allowed_outcomes"] == ["H", "D", "A"]


def test_date_batched_fixed_requests_cannot_reuse_same_date_winnings():
    models, opportunities = data(["2025-08-15"] * 3 + ["2025-08-16"], results=["H", "H", "D", "D"])
    bets, equity = simulate_strategy(config(fixed_stake=100.), models, opportunities, initial_bankroll=100.)
    np.testing.assert_allclose(bets.stake.iloc[:3], [100 / 3] * 3)
    np.testing.assert_allclose(bets.date_start_bankroll.iloc[:3], 100.)
    assert equity.requested_stakes.iloc[0] == 300.
    assert equity.commitment_scale.iloc[0] == pytest.approx(1 / 3)
    assert equity.end_bankroll.iloc[0] == pytest.approx(400 / 3)
    assert bets.stake.iloc[3] == 100.
    assert equity.start_bankroll.iloc[1] == pytest.approx(400 / 3)
    assert equity.end_bankroll.iloc[1] == pytest.approx(100 / 3)


def test_dynamic_fraction_uses_shared_date_start_and_changes_on_next_date_only():
    models, opportunities = data(["2025-08-15", "2025-08-15", "2025-08-16"])
    bets, equity = simulate_strategy(config(staking="dynamic_fraction", bankroll_fraction=.01), models, opportunities)
    np.testing.assert_allclose(bets.stake, [1000., 1000., 1020.])
    np.testing.assert_allclose(equity.start_bankroll, [100000., 102000.])
    assert equity.end_bankroll.iloc[-1] == 103020.


def test_kelly_per_bet_and_aggregate_date_caps_are_both_enforced():
    models, opportunities = data(["2025-08-15"] * 3, probabilities=(.6, .2, .2), odds=(3., 3., 3.))
    bets, equity = simulate_strategy(config(staking="kelly", kelly_fraction=.25,
        max_bet_fraction=.02, date_cap_fraction=.05), models, opportunities)
    np.testing.assert_allclose(bets.full_kelly_fraction, .4)
    np.testing.assert_allclose(bets.requested_stake, 2000.)
    np.testing.assert_allclose(bets.stake, 5000 / 3)
    assert equity.turnover.iloc[0] == pytest.approx(5000.)
    assert equity.commitment_scale.iloc[0] == pytest.approx(5 / 6)
    assert equity.end_bankroll.iloc[0] == pytest.approx(110000.)


def test_candidate_filters_precede_argmax_and_bounds_are_inclusive():
    models, opportunities = data(["2025-08-15"], probabilities=(.3, .4, .3), odds=(2., 5., 10.))
    bets, _ = simulate_strategy(config(min_odds=1.5, max_odds=5.), models, opportunities)
    assert bets.selection.tolist() == ["D"]
    assert bets.odds.tolist() == [5.]
    opportunities.loc[:, "odds_H"] = 1.5
    bets, _ = simulate_strategy(config(allowed_outcomes=["H"], min_odds=1.5,
        max_odds=5., min_edge=None), models, opportunities)
    assert bets.selection.tolist() == ["H"]
    assert bets.odds.tolist() == [1.5]
    assert bets.edge.iloc[0] < 0


def test_edge_threshold_is_strict_and_equal_scores_resolve_h_then_d_then_a():
    models, opportunities = data(["2025-08-15"], probabilities=(.625, .25, .125), odds=(2., 2., 2.))
    bets, _ = simulate_strategy(config(min_edge=.25), models, opportunities)
    assert bets.empty
    bets, _ = simulate_strategy(config(min_edge=.249), models, opportunities)
    assert bets.selection.tolist() == ["H"]
    models["model"][["p_H", "p_D", "p_A"]] = [.4, .4, .2]
    for outcome in "HDA":
        opportunities[f"odds_{outcome}"] = 3.
    bets, _ = simulate_strategy(config(), models, opportunities)
    assert bets.selection.tolist() == ["H"]


@pytest.mark.parametrize("rule,expected", [("model_favorite", "H"), ("market_favorite", "D"),
                                           ("market_underdog", "H"), ("max_edge", "A")])
def test_distinct_selection_rules_do_not_silently_use_maximum_edge(rule, expected):
    models, opportunities = data(["2025-08-15"], probabilities=(.45, .35, .2), odds=(1.5, 4., 9.))
    models["baseline_market_only"][["p_H", "p_D", "p_A"]] = [.2, .5, .3]
    bets, _ = simulate_strategy(config(selection_rule=rule, min_edge=None), models, opportunities)
    assert bets.selection.tolist() == [expected]
    if rule == "model_favorite":
        assert bets.edge.iloc[0] < 0


def test_selected_outcome_consensus_is_a_veto_and_does_not_search_an_alternative():
    models, opportunities = data(["2025-08-15"], probabilities=(.2, .3, .5), odds=(2., 3., 4.))
    for i in range(8):
        models[f"v{i}"] = models["model"].copy()
        models[f"v{i}"][["p_H", "p_D", "p_A"]] = [.3, .5, .2]
    settings = config(consensus_min=6, consensus_model_keys=[f"v{i}" for i in range(8)])
    bets, _ = simulate_strategy(settings, models, opportunities)
    assert bets.empty  # All voters prefer a positive-edge D; selected A fails.
    for i in range(6):
        models[f"v{i}"][["p_H", "p_D", "p_A"]] = [.3, .4, .3]
    bets, _ = simulate_strategy(settings, models, opportunities)
    assert bets.selection.tolist() == ["A"]
    assert bets.consensus_votes.tolist() == [6]


def test_future_settlement_cannot_change_selections_or_earlier_stakes():
    models, opportunities = data(["2025-08-15", "2025-08-16", "2025-08-17"])
    untouched_models = {key: value.copy(deep=True) for key, value in models.items()}
    untouched_prices = opportunities.copy(deep=True)
    settings = config(staking="kelly")
    bets, equity = simulate_strategy(settings, models, opportunities)
    changed = opportunities.copy()
    changed.loc[2, "result"] = "A"
    changed_bets, changed_equity = simulate_strategy(settings, models, changed)
    pd.testing.assert_frame_equal(bets[["match_id", "selection", "stake", "probability"]],
                                  changed_bets[["match_id", "selection", "stake", "probability"]])
    pd.testing.assert_frame_equal(equity.iloc[:2], changed_equity.iloc[:2])
    assert equity.end_bankroll.iloc[-1] != changed_equity.end_bankroll.iloc[-1]
    pd.testing.assert_frame_equal(opportunities, untouched_prices)
    for key in models:
        pd.testing.assert_frame_equal(models[key], untouched_models[key])


def test_reference_quotes_are_used_instead_of_best_quotes():
    models, opportunities = data(["2025-08-15"])
    opportunities["ref_odds_H"] = 1.5
    settings = config(selection_rule="fixed_outcome", allowed_outcomes=["H"], min_edge=None, odds_mode="reference")
    bets, _ = simulate_strategy(settings, models, opportunities)
    assert bets.odds.tolist() == [1.5]
    assert bets.bookmaker.tolist() == ["Bet365"]
    assert bets.profit.tolist() == [500.]


def test_cash_policy_keeps_every_date_and_frozen_metrics_undefined_conditional_ratios():
    models, opportunities = data(["2025-08-15", "2025-08-16", "2025-08-17"])
    bets, equity = simulate_strategy(config(cash_only=True), models, opportunities)
    assert bets.empty and len(equity) == 3
    np.testing.assert_array_equal(equity.start_bankroll, 100000.)
    np.testing.assert_array_equal(equity.end_bankroll, 100000.)
    summary = summarize_strategy(bets, equity, prediction_count=3, matched_valid_odds_count=3,
                                 initial_bankroll=100000., bootstrap_samples=0)
    assert summary["profit"] == 0 and summary["trading_frequency"] == 0
    assert summary["hit_ratio"] is None and summary["roi"] is None
    assert summary["initial_capital_sum_units"] == summary["final_capital_sum_units"] == 100000.
    assert summary["bankroll_reset_episodes"] == 1


def test_bankruptcy_stops_positive_stakes_without_deleting_future_opportunity_dates():
    models, opportunities = data(["2025-08-15", "2025-08-16"], results=["D", "H"])
    bets, equity = simulate_strategy(config(fixed_stake=100.), models, opportunities, initial_bankroll=100.)
    assert len(bets) == 1 and len(equity) == 2
    np.testing.assert_allclose(equity.end_bankroll, [0., 0.])
    assert equity.bet_count.tolist() == [1, 0]
    assert equity.drawdown.max() == 1.


@pytest.mark.parametrize("change,error", [({"date_cap_fraction": 1.01}, "date_cap_fraction"),
    ({"min_odds": 5., "max_odds": 2.}, "min_odds exceeds"),
    ({"consensus_min": 6, "consensus_model_keys": ["model"]}, "consensus_min")])
def test_invalid_budget_or_rule_contracts_reject(change, error):
    models, opportunities = data(["2025-08-15"])
    with pytest.raises(ValueError, match=error):
        simulate_strategy(config(**change), models, opportunities)
