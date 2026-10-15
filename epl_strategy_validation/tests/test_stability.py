from copy import deepcopy

import numpy as np
import pandas as pd
import pytest

from epl_strategy_validation.analysis import SEASONS, season_stability


def frames():
    values = [10000., -20000., 30000., 0.]
    seasonal = pd.DataFrame([dict(strategy_id="S017", season=s, profit=p, turnover=t,
        initial_capital_sum_units=100000., bankroll_reset_episodes=1,
        return_on_initial_capital=p / 100000) for s, p, t in zip(SEASONS, values, [100000., 200000., 300000., 400000.])])
    continuous = pd.DataFrame([dict(strategy_id="S017", final_capital_sum_units=123456.,
                                    return_on_initial_capital=.23456)])
    return seasonal, continuous


def test_reset_diagnostics_keep_capital_denominator_and_loo_accounts_distinct():
    seasonal, continuous = frames()
    before = deepcopy(seasonal)
    row = season_stability(seasonal, continuous).iloc[0]
    assert row.positive_seasons == 2 and row.negative_seasons == 1 and row.zero_profit_seasons == 1
    assert row.pooled_reset_starting_capital == 400000.
    assert row.pooled_reset_capital_return == .05
    assert row.pooled_reset_roi == .02
    assert row.loo_min_reset_roi == pytest.approx(-10000 / 700000)
    assert row.loo_max_reset_roi == pytest.approx(40000 / 800000)
    assert row.worst_season_return == -.2 and row.best_season_return == .3
    assert row.continuous_final_capital_sum_units == 123456.
    pd.testing.assert_frame_equal(before, seasonal)


@pytest.mark.parametrize("bad", ["missing", "duplicate", "carried_capital", "false_return"])
def test_invalid_seasonal_accounts_cannot_be_treated_as_fresh_100k(bad):
    seasonal, continuous = frames()
    if bad == "missing": seasonal = seasonal.iloc[:3]
    elif bad == "duplicate": seasonal = pd.concat([seasonal, seasonal.iloc[[0]]])
    elif bad == "carried_capital": seasonal.loc[1, "initial_capital_sum_units"] = 110000.
    else: seasonal.loc[0, "return_on_initial_capital"] = .9
    with pytest.raises(ValueError): season_stability(seasonal, continuous)


def test_no_turnover_preserves_undefined_roi_and_zero_capital_return():
    seasonal, continuous = frames()
    seasonal[["profit", "turnover", "return_on_initial_capital"]] = 0.
    row = season_stability(seasonal, continuous).iloc[0]
    assert row.pooled_reset_capital_return == 0
    assert np.isnan(row.pooled_reset_roi) and np.isnan(row.loo_min_reset_roi)
