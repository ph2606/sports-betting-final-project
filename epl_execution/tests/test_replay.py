from copy import deepcopy

import numpy as np
import pandas as pd
import pytest

from epl_execution.replay import fixed_exposure_reference, reference_replay
from epl_strategy.metrics import summarize_strategy
from epl_strategy_lab.catalog import build_catalog
from epl_strategy_lab.engine import simulate_strategy


def config(**changes):
    value = deepcopy(build_catalog()[16])
    value.update(model_key="model", min_edge=.05, fixed_stake=1000., cash_only=False)
    value.update(changes)
    return value


def data(dates, *, probabilities=(.7, .2, .1), best=(3., 4., 5.), reference=(2., 3., 4.), results=None, seasons=None):
    count = len(dates)
    opportunities = pd.DataFrame({"match_id": [f"m{i}" for i in range(count)],
        "match_date": pd.to_datetime(dates), "season": seasons or ["2025-26"] * count,
        "result": results or ["H"] * count, "snapshot_type": "preclosing", "reference_bookmaker": "Bet365"})
    for label, b, r in zip("HDA", best, reference):
        opportunities[f"odds_{label}"] = b
        opportunities[f"ref_odds_{label}"] = r
        opportunities[f"bookmaker_{label}"] = "BestBook"
    prediction = pd.DataFrame({"match_id": opportunities.match_id})
    prediction[["p_H", "p_D", "p_A"]] = probabilities
    return {"model": prediction.copy(), "baseline_market_only": prediction.copy()}, opportunities


def ledger(opportunities, *, stakes, odds=None, probabilities=None, selected=None):
    rows = []
    for index, row in enumerate(opportunities.itertuples()):
        outcome = selected[index] if selected else "H"
        price = odds[index] if odds else getattr(row, "odds_" + outcome)
        stake = stakes[index]
        won = outcome == row.result
        rows.append({"strategy_id": "S017", "match_id": row.match_id, "match_date": row.match_date,
                     "selection": outcome, "result": row.result, "probability": probabilities[index] if probabilities else .7,
                     "odds": price, "stake": stake, "won": won, "gross_return": won * stake * price,
                     "profit": won * stake * price - stake, "episode_id": "source_account"})
    return pd.DataFrame(rows)


def test_reference_replay_reselects_outcome_and_preserves_inputs():
    models, opportunities = data(["2025-08-15"], probabilities=(.5, .3, .2), best=(2.8, 6., 6.), reference=(2.5, 3., 4.))
    settings = config()
    before = deepcopy(settings)
    original_models = {key: frame.copy(deep=True) for key, frame in models.items()}
    original_prices = opportunities.copy(deep=True)
    old, _ = simulate_strategy(settings, models, opportunities)
    new, equity = reference_replay(settings, models, opportunities, scope="single", episode_id="test")
    assert old.selection.tolist() == ["D"]
    assert new.selection.tolist() == ["H"]
    assert new.odds.tolist() == [2.5]
    assert new.bookmaker.tolist() == ["Bet365"]
    assert new.strategy_id.tolist() == ["S017"]
    assert new.episode_id.tolist() == ["test"] and equity.episode_id.tolist() == ["test"]
    assert settings == before
    pd.testing.assert_frame_equal(opportunities, original_prices)
    for key in models:
        pd.testing.assert_frame_equal(models[key], original_models[key])


def test_reference_replay_reapplies_edge_eligibility():
    models, opportunities = data(["2025-08-15"], probabilities=(.5, .3, .2), best=(3., 3., 4.), reference=(2., 3., 4.))
    old, _ = simulate_strategy(config(), models, opportunities)
    new, equity = reference_replay(config(), models, opportunities, scope="single", episode_id="test")
    assert len(old) == 1 and new.empty
    assert equity.end_bankroll.tolist() == [100000.]


def test_reference_replay_date_and_kelly_caps_apply_before_settlement():
    models, opportunities = data(["2025-08-15"] * 3, probabilities=(.6, .2, .2), reference=(3., 3., 3.))
    bets, equity = reference_replay(config(staking="kelly", kelly_fraction=.25,
        max_bet_fraction=.02, date_cap_fraction=.05), models, opportunities, scope="single", episode_id="test")
    np.testing.assert_allclose(bets.stake, 5000 / 3)
    assert equity.turnover.iloc[0] == pytest.approx(5000.)
    assert equity.end_bankroll.iloc[0] == pytest.approx(110000.)


def test_reference_replay_retains_native_four_year_epochs_without_resets():
    models, opportunities = data(["2022-08-05", "2023-08-11", "2024-08-16", "2025-08-15"],
                                seasons=["2022-23", "2023-24", "2024-25", "2025-26"])
    bets, equity = reference_replay(config(staking="dynamic_fraction", bankroll_fraction=.01), models, opportunities,
                                    scope="continuous", episode_id="four_year")
    assert bets.season.tolist() == opportunities.season.tolist()
    assert equity.season.tolist() == opportunities.season.tolist()
    np.testing.assert_allclose(equity.start_bankroll, [100000., 101000., 102010., 103030.1])
    assert bets.episode_id.eq("four_year").all()
    assert equity.episode_id.eq("four_year").all()


def test_reference_replay_rejects_earlier_first_study_models_and_bad_scope():
    models, opportunities = data(["2022-08-05"], seasons=["2022-23"])
    with pytest.raises(ValueError, match="First-study"):
        reference_replay(config(model_key="first_accuracy"), models, opportunities, scope="continuous", episode_id="x")
    with pytest.raises(ValueError, match="2025-26"):
        reference_replay(config(), models, opportunities, scope="single", episode_id="x")
    with pytest.raises(ValueError, match="scope"):
        reference_replay(config(), models, opportunities, scope="unknown", episode_id="x")


def test_reference_replay_single_first_study_probability_series_is_supported():
    models, opportunities = data(["2025-08-15"])
    models["first_accuracy"] = models["model"]
    bets, _ = reference_replay(config(model_key="first_accuracy"), models, opportunities, scope="single", episode_id="one")
    assert bets.probability.tolist() == [.7]


def test_fixed_exposure_matches_exact_actual_and_model_quote_uplift():
    _, opportunities = data(["2025-08-15", "2025-08-16", "2025-08-17"], results=["H", "D", "H"])
    old = ledger(opportunities, stakes=[1000., 2000., 500.], probabilities=[.7, .6, .8])
    untouched = old.copy(deep=True)
    metric, bets, curve = fixed_exposure_reference(config(), old, opportunities, episode_id="price_only", bootstrap_samples=20)
    assert metric["actual_quote_uplift_units"] == 1500.
    assert metric["model_expected_quote_uplift_units"] == 2300.
    assert metric["original_profit"] - metric["profit"] == pytest.approx(1500.)
    assert metric["original_expected_net_profit"] - metric["expected_net_profit_total_units"] == pytest.approx(2300.)
    assert metric["funding_feasible"]
    np.testing.assert_allclose(bets.stake, old.stake)
    assert bets.selection.tolist() == old.selection.tolist()
    assert bets.probability.tolist() == old.probability.tolist()
    assert metric["bet_count"] == 3 and metric["hit_ratio"] == pytest.approx(2 / 3)
    assert metric["expected_gain_total_units"] == 2300.
    assert metric["expected_loss_total_units"] == 1200.
    assert curve.episode_id.eq("price_only").all()
    pd.testing.assert_frame_equal(old, untouched)


def test_fixed_exposure_never_requalifies_negative_reference_edge_or_resizes_kelly():
    _, opportunities = data(["2025-08-15"], reference=(1.1, 3., 4.))
    old = ledger(opportunities, stakes=[5000.], probabilities=[.2])
    old["full_kelly_fraction"] = .3
    metric, bets, _ = fixed_exposure_reference(config(staking="kelly", max_bet_fraction=.01), old,
                                               opportunities, episode_id="fixed", bootstrap_samples=0)
    assert metric["bet_count"] == 1 and not metric["is_policy_replay"]
    assert bets.stake.iloc[0] == 5000.
    assert bets.edge.iloc[0] == pytest.approx(-.78)
    assert bets.full_kelly_fraction.iloc[0] == 0.
    assert bets.original_full_kelly_fraction.iloc[0] == .3


def test_fixed_exposure_funding_checked_before_same_date_winning_proceeds():
    _, opportunities = data(["2025-08-15", "2025-08-16"], reference=(1.5, 3., 4.))
    opportunities.loc[1, "ref_odds_H"] = 2.
    old = ledger(opportunities, stakes=[100., 200.])
    metric, bets, curve = fixed_exposure_reference(config(), old, opportunities,
        episode_id="shadow", initial_bankroll=100., bootstrap_samples=10)
    assert not metric["funding_feasible"]
    assert metric["first_shortfall_date"] == "2025-08-16"
    assert metric["shadow_final_balance"] == 350.
    assert metric["shadow_min_balance"] == 100.
    assert metric["max_funding_shortfall_units"] == 50.
    assert metric["minimum_additional_opening_cash_units"] == 50.
    assert metric["max_funding_shortfall_units"] > max(0., -metric["shadow_min_balance"])
    assert curve.funding_shortfall_units.tolist() == [0., 50.]
    assert bets.stake.tolist() == [100., 200.]
    assert metric["profit"] == 250. and metric["roi"] == pytest.approx(250 / 300)
    assert metric["hit_ratio"] == 1. and metric["trading_frequency"] == 1.
    assert metric["expected_gain_total_units"] == pytest.approx(175.)
    assert metric["expected_loss_total_units"] == pytest.approx(90.)
    for name in ("final_capital_sum_units", "return_on_initial_capital", "max_drawdown", "date_return_mean",
                 "max_date_capital_exposure", "roi_ci_low", "hit_ratio_ci_high", "min_episode_log_growth"):
        assert metric[name] is None
    assert curve.daily_return.isna().all() and curve.drawdown.isna().all()
    assert metric["bootstrap_samples"] == 0 and metric["requested_bootstrap_samples"] == 10


def test_unfunded_metrics_have_every_frozen_summary_field():
    _, opportunities = data(["2025-08-15", "2025-08-16"], reference=(1.5, 3., 4.))
    old = ledger(opportunities, stakes=[100., 200.])
    unfunded, _, _ = fixed_exposure_reference(config(), old, opportunities, episode_id="x", initial_bankroll=100., bootstrap_samples=0)
    funded, bets, curve = fixed_exposure_reference(config(), old, opportunities, episode_id="x", initial_bankroll=1000., bootstrap_samples=0)
    frozen = summarize_strategy(bets, curve, prediction_count=2, matched_valid_odds_count=2,
                                initial_bankroll=1000., bootstrap_samples=0)
    assert set(frozen).issubset(unfunded)
    assert set(frozen).issubset(funded)


def test_fixed_exposure_cash_retains_all_dates_and_defined_zero_totals():
    models, opportunities = data(["2025-08-15", "2025-08-17"])
    settings = config(cash_only=True)
    old, _ = simulate_strategy(settings, models, opportunities)
    metric, bets, curve = fixed_exposure_reference(settings, old, opportunities, episode_id="cash", bootstrap_samples=0)
    assert bets.empty and len(curve) == 2
    assert metric["funding_feasible"] and metric["metric_status"] == "no_trades"
    assert metric["profit"] == 0. and metric["turnover"] == 0.
    assert metric["expected_gain_total_units"] == 0. and metric["expected_loss_total_units"] == 0.
    assert metric["hit_ratio"] is None and metric["roi"] is None
    assert metric["trading_frequency"] == 0.
    assert metric["shadow_final_balance"] == 100000. and metric["return_on_initial_capital"] == 0.
    assert metric["actual_quote_uplift_units"] == 0.


def test_already_reference_identity_control_has_exactly_zero_uplift():
    models, opportunities = data(["2025-08-15", "2025-08-16"], results=["H", "D"])
    settings = config(odds_mode="reference")
    old, old_equity = simulate_strategy(settings, models, opportunities)
    metric, bets, curve = fixed_exposure_reference(settings, old, opportunities, episode_id="identity", bootstrap_samples=0)
    assert metric["actual_quote_uplift_units"] == metric["model_expected_quote_uplift_units"] == 0.
    np.testing.assert_allclose(bets.profit, old.profit)
    np.testing.assert_allclose(curve.end_bankroll, old_equity.end_bankroll)


@pytest.mark.parametrize("problem", ["duplicate", "missing_match", "bad_date", "bad_result", "mixed_episode", "missing_episode", "bad_season", "bad_probability", "bad_ref", "best_below_ref"])
def test_invalid_fixed_ledger_or_quote_identity_cannot_enter_attribution(problem):
    _, opportunities = data(["2025-08-15", "2025-08-16"])
    old = ledger(opportunities, stakes=[100., 100.])
    if problem == "duplicate": old = pd.concat([old, old.iloc[[0]]], ignore_index=True)
    elif problem == "missing_match": old.loc[0, "match_id"] = "absent"
    elif problem == "bad_date": old.loc[0, "match_date"] = pd.Timestamp("2025-08-17")
    elif problem == "bad_result":
        opportunities.loc[0, "result"] = "A"
    elif problem == "mixed_episode": old.loc[0, "episode_id"] = "other"
    elif problem == "missing_episode": old.loc[0, "episode_id"] = None
    elif problem == "bad_season": old["season"] = "2024-25"
    elif problem == "bad_probability": old.loc[0, "probability"] = np.nan
    elif problem == "bad_ref": opportunities.loc[0, "ref_odds_H"] = 1.
    elif problem == "best_below_ref": opportunities.loc[0, "ref_odds_H"] = 4.
    with pytest.raises(ValueError):
        fixed_exposure_reference(config(), old, opportunities, episode_id="bad")
