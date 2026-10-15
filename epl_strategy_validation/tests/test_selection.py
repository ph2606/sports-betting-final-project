"""Accounting guards and statistical invariances for the conditional audit."""
from copy import deepcopy
import hashlib
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from epl_strategy_validation.selection import (
    _bootstrap_deviations, _circular_indices, _summarize_family,
    _validated_paths, run_selection_audit,
)


def _inputs():
    dates = pd.date_range("2025-08-15", periods=4)
    catalog = [{"strategy_id": "cash", "name": "Cash", "cash_only": True},
               {"strategy_id": "favorite", "name": "Favorite", "cash_only": False},
               {"strategy_id": "other", "name": "Other", "cash_only": False}]
    bets, equity, metrics = [], [], []
    for j, config in enumerate(catalog):
        capital, total = 100000.0, 0.0
        for i, date in enumerate(dates):
            win = (i + j) % 2 == 0
            stake = 0.0 if j == 0 else 100.0
            profit = 0.0 if j == 0 else stake if win else -stake
            equity.append({"strategy_id": config["strategy_id"], "match_date": date,
                           "matched_matches": 1, "bet_count": int(j != 0), "turnover": stake,
                           "profit": profit, "start_bankroll": capital, "end_bankroll": capital + profit})
            if j:
                bets.append({"strategy_id": config["strategy_id"], "match_id": f"m{i}",
                             "match_date": date, "result": "H", "selection": "H" if win else "A",
                             "won": win, "stake": stake, "odds": 2.0,
                             "gross_return": 2 * stake if win else 0.0, "profit": profit})
            total += profit
            capital += profit
        metrics.append({"strategy_id": config["strategy_id"], "initial_bankroll": 100000.0,
                        "profit": total, "bet_count": 0 if j == 0 else 4,
                        "matched_valid_odds_count": 4, "matched_match_dates": 4,
                        "final_capital_sum_units": capital})
    return catalog, pd.DataFrame(metrics), pd.DataFrame(bets), pd.DataFrame(equity)


def test_accounting_and_common_date_paths():
    pnl, counts, names = _validated_paths(*_inputs())
    assert pnl.shape == (4, 3)
    assert counts.tolist() == [1, 1, 1, 1]
    assert (pnl["cash"] == 0).all()
    assert (pnl.favorite == -pnl.other).all()
    assert names["favorite"] == "Favorite"


@pytest.mark.parametrize("kind", ["duplicate_equity", "missing_date", "different_counts", "conflicting_result", "duplicate_bet", "unfunded", "metric_profit", "cash_traded"])
def test_identity_and_cashflow_corruption_rejected(kind):
    catalog, metrics, bets, equity = _inputs()
    if kind == "duplicate_equity":
        equity = pd.concat([equity, equity.iloc[[0]]], ignore_index=True)
    elif kind == "missing_date":
        equity = equity.drop(index=0)
    elif kind == "different_counts":
        equity.loc[0, "matched_matches"] = 2
    elif kind == "conflicting_result":
        bets.loc[0, "result"] = "D"
    elif kind == "duplicate_bet":
        bets = pd.concat([bets, bets.iloc[[0]]], ignore_index=True)
    elif kind == "unfunded":
        equity.loc[4, "turnover"] = 200000
    elif kind == "metric_profit":
        metrics.loc[0, "profit"] = 1
    elif kind == "cash_traded":
        catalog[1]["cash_only"] = True
    with pytest.raises(ValueError):
        _validated_paths(catalog, metrics, bets, equity)


def test_circular_blocks_wrap_and_keep_the_original_date_count():
    actual = _circular_indices(np.random.default_rng(41), 7, 8, 3)
    starts = np.random.default_rng(41).integers(0, 7, (8, 3))
    expected = ((starts[:, :, None] + np.arange(3)) % 7).reshape(8, -1)[:, :7]
    np.testing.assert_array_equal(actual, expected)
    assert actual.shape == (8, 7)


def test_centering_matches_literal_bootstrap_mean_minus_original_mean():
    values = np.arange(27, dtype=float).reshape(9, 3) ** 2
    ids = _circular_indices(np.random.default_rng(5), 9, 127, 3)
    expected = values[ids].mean(axis=1) - values.mean(axis=0)
    actual = _bootstrap_deviations(values, block_length=3, bootstrap_samples=127, seed=5)
    np.testing.assert_allclose(actual, expected, atol=1e-12)


def test_duplicate_and_permutation_do_not_change_the_maximum_family():
    values = np.array([[10, -40], [30, 20], [-20, 10], [80, -50]], dtype=float)
    dev = _bootstrap_deviations(values, block_length=2, bootstrap_samples=513, seed=4)
    base = _summarize_family(values.mean(axis=0), dev)
    duplicated_values = np.column_stack([values, values[:, 0]])
    dup = _summarize_family(duplicated_values.mean(axis=0),
                           _bootstrap_deviations(duplicated_values, block_length=2, bootstrap_samples=513, seed=4))
    perm = _summarize_family(values[:, ::-1].mean(axis=0),
                            _bootstrap_deviations(values[:, ::-1], block_length=2, bootstrap_samples=513, seed=4))
    assert base["global_p"] == dup["global_p"] == perm["global_p"]
    assert base["critical"] == dup["critical"] == perm["critical"]
    np.testing.assert_array_equal(base["adjusted_p"], dup["adjusted_p"][:2])
    np.testing.assert_array_equal(base["adjusted_p"], perm["adjusted_p"][::-1])


def test_currency_scaling_seed_reproducibility_and_adjustment_monotonicity():
    values = np.array([[0, 10, -50], [0, 30, 20], [0, -20, 10], [0, 80, -40]], dtype=float)
    args = dict(block_length=2, bootstrap_samples=513, seed=87)
    dev = _bootstrap_deviations(values, **args)
    np.testing.assert_array_equal(dev, _bootstrap_deviations(values, **args))
    base = _summarize_family(values.mean(axis=0), dev)
    scaled = _summarize_family(8 * values.mean(axis=0), _bootstrap_deviations(8 * values, **args))
    np.testing.assert_array_equal(base["adjusted_p"], scaled["adjusted_p"])
    np.testing.assert_array_equal(base["raw_p"], scaled["raw_p"])
    assert base["global_p"] == scaled["global_p"]
    assert scaled["critical"] == 8 * base["critical"]
    assert (base["adjusted_p"] >= base["raw_p"]).all()
    assert (base["critical"] >= base["pointwise"]).all()
    assert base["structural_zero"][0]
    assert base["raw_p"][0] == base["adjusted_p"][0] == 1
    assert (base["raw_p"] >= 1 / 514).all()


def test_paired_benchmark_self_is_exactly_zero_with_identical_indices():
    values = np.array([[2, 9], [7, -3], [-8, 15], [11, 6]], dtype=float)
    dev = _bootstrap_deviations(values, block_length=2, bootstrap_samples=300, seed=50)
    differences = dev - dev[:, [1]]
    observed = values.mean(axis=0) - values[:, 1].mean()
    result = _summarize_family(observed, differences)
    assert observed[1] == 0
    assert (differences[:, 1] == 0).all()
    assert result["raw_p"][1] == result["adjusted_p"][1] == 1
    assert result["structural_zero"][1]


def test_all_negative_advantages_cannot_reject_global_null():
    result = _summarize_family(np.array([-1.0, -2.0]), np.array([[2.0, -4], [-2, 4], [0, 0]]))
    assert result["global_p"] == 1
    assert (result["adjusted_p"] == 1).all()


@pytest.mark.parametrize("kwargs", [dict(block_length=0, bootstrap_samples=10),
                                  dict(block_length=5, bootstrap_samples=10),
                                  dict(block_length=1, bootstrap_samples=0),
                                  dict(block_length=True, bootstrap_samples=10)])
def test_invalid_bootstrap_dimensions_rejected(kwargs):
    with pytest.raises(ValueError):
        _bootstrap_deviations(np.ones((4, 2)), seed=2, **kwargs)


def test_frozen_84_rule_audit_roundtrip_and_source_immutability(tmp_path):
    repo = Path(__file__).resolve().parents[2]
    legacy = repo / "epl_strategy_lab/results/20261015T040052Z_100k84"
    files = [legacy / name for name in ("catalog.json", "metrics.parquet", "bets.parquet", "equity.parquet")]
    before = [hashlib.sha256(path.read_bytes()).hexdigest() for path in files]
    method = run_selection_audit(legacy, tmp_path, bootstrap_samples=79, seed=123)
    comparison = pd.read_parquet(tmp_path / "selection_comparison.parquet")
    global_ = pd.read_parquet(tmp_path / "selection_global.parquet")
    assert comparison.shape[0] == 672 and global_.shape[0] == 8
    assert method["matched_match_dates"] == 113 and method["matched_fixtures"] == 374
    assert method["distinct_recorded_paths"] == 75
    assert set(comparison.block_length) == {1, 3, 5, 10}
    assert comparison.groupby(["benchmark_id", "block_length"]).strategy_id.nunique().eq(84).all()
    np.testing.assert_allclose(comparison.period_excess_profit_units, 113 * comparison.mean_date_excess_profit_units)
    np.testing.assert_allclose(comparison.excess_return_on_initial_capital, comparison.period_excess_profit_units / 100000)
    zero = comparison.loc[comparison.structural_zero_comparison]
    assert len(zero) == 36  # eight cash/cash rules and market-favorite/self, four blocks
    assert zero.family_adjusted_one_sided_p.eq(1).all()
    assert zero.simultaneous_ci_low_mean_date_units.eq(0).all()
    assert zero.simultaneous_ci_high_mean_date_units.eq(0).all()
    assert (comparison.family_adjusted_one_sided_p >= comparison.raw_one_sided_p).all()
    after = [hashlib.sha256(path.read_bytes()).hexdigest() for path in files]
    assert before == after
