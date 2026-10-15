"""Protect the native source population and account equivalence to frozen work."""
from copy import deepcopy
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from epl_strategy import metrics as frozen_metrics
from epl_strategy_validation import inputs
from epl_strategy_validation.inputs import compatible_catalog, load_inputs
from epl_strategy_validation import replay as replay_module


ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def loaded():
    return load_inputs(ROOT)


@pytest.fixture(scope="module")
def catalog():
    return compatible_catalog(ROOT)


def test_complete_source_populations_and_fixed_probability_ensembles(loaded):
    models, opportunities, paths = loaded
    assert len(models) == 14
    assert len(opportunities) == 1470
    assert opportunities.match_date.nunique() == 453
    assert opportunities.groupby("season").size().to_dict() == inputs.SEASON_MATCH_COUNTS
    assert opportunities.groupby("season").match_date.nunique().to_dict() == inputs.SEASON_DATE_COUNTS
    assert paths == [ROOT / relative for relative in inputs.SOURCE_FILES]
    assert not any(key.startswith("first_") for key in models)
    for key, frame in models.items():
        assert frame.match_id.tolist() == opportunities.match_id.tolist()
        np.testing.assert_allclose(frame[inputs.PROBABILITY_COLUMNS].sum(axis=1), 1, rtol=0, atol=1e-10)
    for key, members in inputs.ENSEMBLE_MEMBERS.items():
        expected = np.mean(np.stack([models[member][inputs.PROBABILITY_COLUMNS].to_numpy(float)
                                    for member in members]), axis=0)
        np.testing.assert_array_equal(models[key][inputs.PROBABILITY_COLUMNS].to_numpy(float), expected)


def test_catalog_is_frozen_and_compatible_copy_is_independent(catalog):
    original, eligible = catalog
    assert len(original) == 84
    assert [row["strategy_id"] for row in eligible] == [f"S{i:03d}" for i in range(17, 73)]
    assert all(not row["model_key"].startswith("first_") for row in eligible)
    all84, copied = compatible_catalog(ROOT)
    copied[0]["allowed_outcomes"].append("changed")
    assert all84 == original


def test_catalog_tamper_is_rejected(tmp_path, catalog):
    changed = deepcopy(catalog[0])
    changed[16]["min_edge"] = 0.04
    path = tmp_path / inputs.CATALOG_RELATIVE
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(changed), encoding="utf-8")
    with pytest.raises(ValueError, match="catalog differs"):
        compatible_catalog(tmp_path)


@pytest.mark.parametrize("damage", ["missing_match", "duplicate_match", "wrong_result", "wrong_season",
                                     "bad_probability", "bad_odds", "bad_market", "missing_book"])
def test_source_conflicts_are_never_silently_dropped(monkeypatch, damage):
    predictions = pd.read_parquet(ROOT / inputs.SOURCE_FILES[0])
    prices = pd.read_parquet(ROOT / inputs.SOURCE_FILES[1])
    if damage == "missing_match":
        predictions = predictions.drop(predictions.index[0])
    elif damage == "duplicate_match":
        predictions = pd.concat([predictions, predictions.iloc[[0]]], ignore_index=True)
    elif damage == "wrong_result":
        predictions.loc[predictions.index[0], "result"] = "D" if predictions.result.iloc[0] != "D" else "A"
    elif damage == "wrong_season":
        predictions.loc[predictions.index[0], "outer_season"] = "2025-26"
    elif damage == "bad_probability":
        predictions.loc[predictions.index[0], "p_H"] = 2
    else:
        index = prices.index[prices.season.eq("2022-23")][0]
        if damage == "bad_odds":
            prices.loc[index, "odds_H"] = np.nan
        elif damage == "bad_market":
            prices.loc[index, "ref_p_H"] = 0
        else:
            prices.loc[index, "bookmaker_H"] = None
    frames = {inputs.SOURCE_FILES[0]: predictions, inputs.SOURCE_FILES[1]: prices}

    def read(path):
        return frames[Path(path).relative_to(ROOT).as_posix()].copy(deep=True)

    monkeypatch.setattr(inputs.pd, "read_parquet", read)
    with pytest.raises(ValueError):
        load_inputs(ROOT)


def _two_seasons(config):
    opportunities = pd.DataFrame({
        "match_id": ["old", "new"], "match_date": pd.to_datetime(["2022-08-05", "2023-08-11"]),
        "season": ["2022-23", "2023-24"], "result": ["H", "A"],
        "odds_H": [2.0, 2.0], "odds_D": [3.0, 3.0], "odds_A": [4.0, 4.0],
        "snapshot_type": ["preclosing", "preclosing"],
        "bookmaker_H": ["book", "book"], "bookmaker_D": ["book", "book"], "bookmaker_A": ["book", "book"],
    })
    model = pd.DataFrame({"match_id": ["old", "new"], "p_H": [0.8, 0.8],
                          "p_D": [0.1, 0.1], "p_A": [0.1, 0.1]})
    return {config["model_key"]: model}, opportunities


def test_adapter_carries_actual_seasons_and_cash_without_resets(catalog, monkeypatch):
    config = deepcopy(next(row for row in catalog[1] if row["strategy_id"] == "S024"))
    models, opportunities = _two_seasons(config)
    before = opportunities.copy(deep=True)
    engine = replay_module.simulate_strategy
    seen = []

    def spy(config, models, native, **kwargs):
        assert "season" not in native
        pd.testing.assert_series_equal(native.match_date, before.match_date)
        seen.append(native.match_id.tolist())
        return engine(config, models, native, **kwargs)

    monkeypatch.setattr(replay_module, "simulate_strategy", spy)
    bets, equity = replay_module.replay(config, models, opportunities, episode_id="one_account")
    assert seen == [["old", "new"]]
    assert bets.season.tolist() == ["2022-23", "2023-24"]
    assert equity.season.tolist() == ["2022-23", "2023-24"]
    assert bets.episode_id.eq("one_account").all() and equity.episode_id.eq("one_account").all()
    np.testing.assert_allclose(bets.stake, [2000, 2040])
    np.testing.assert_allclose(equity.start_bankroll, [100000, 102000])
    np.testing.assert_allclose(equity.end_bankroll, [102000, 99960])
    pd.testing.assert_frame_equal(opportunities, before)


def test_explicit_seasonal_calls_restart_independent_capital(catalog):
    config = next(row for row in catalog[1] if row["strategy_id"] == "S024")
    models, opportunities = _two_seasons(config)
    balances, stakes = [], []
    for season, frame in opportunities.groupby("season"):
        bets, equity = replay_module.replay(config, models, frame, episode_id=f"independent_{season}")
        assert equity.start_bankroll.iloc[0] == 100000
        assert equity.season.eq(season).all()
        stakes.append(bets.stake.iloc[0])
        balances.append(equity.end_bankroll.iloc[-1])
    assert stakes == [2000, 2000]
    assert balances == [102000, 98000]


def test_replay_rejects_misdated_seasons_and_first_study_backfills(catalog):
    config = deepcopy(catalog[1][0])
    models, opportunities = _two_seasons(config)
    invalid = opportunities.copy()
    invalid.loc[0, "season"] = "2025-26"
    with pytest.raises(ValueError, match="date conflicts"):
        replay_module.replay(config, models, invalid)
    config["model_key"] = "first_accuracy"
    with pytest.raises(ValueError, match="cannot be backfilled"):
        replay_module.replay(config, models, opportunities)


def test_every_fresh_2025_account_matches_frozen_56_strategy_ledgers(loaded, catalog):
    models, opportunities, _ = loaded
    native = opportunities.loc[opportunities.season.eq("2025-26")].copy()
    original = ROOT / inputs.LAB_EXPORT_RELATIVE
    frozen_bets = pd.read_parquet(original / "bets.parquet")
    frozen_equity = pd.read_parquet(original / "equity.parquet")
    frozen_rows = pd.read_parquet(original / "metrics.parquet").set_index("strategy_id")
    bet_fields = ["strategy_id", "match_id", "match_date", "result", "selection", "probability", "odds",
                  "bookmaker", "stake", "won", "gross_return", "profit", "date_start_bankroll", "date_end_bankroll"]
    equity_fields = ["strategy_id", "match_date", "matched_matches", "qualified_matches", "bet_count",
                     "turnover", "profit", "start_bankroll", "end_bankroll", "drawdown"]
    for config in catalog[1]:
        strategy = config["strategy_id"]
        bets, equity = replay_module.replay(config, models, native, episode_id="independent_2025_26")
        expected_bets = frozen_bets.loc[frozen_bets.strategy_id.eq(strategy)]
        expected_equity = frozen_equity.loc[frozen_equity.strategy_id.eq(strategy)]
        pd.testing.assert_frame_equal(bets[bet_fields].reset_index(drop=True),
                                      expected_bets[bet_fields].reset_index(drop=True),
                                      check_dtype=False, check_exact=False, rtol=1e-12, atol=1e-7)
        pd.testing.assert_frame_equal(equity[equity_fields].reset_index(drop=True),
                                      expected_equity[equity_fields].reset_index(drop=True),
                                      check_dtype=False, check_exact=False, rtol=1e-12, atol=1e-7)
        summary = frozen_metrics.summarize_strategy(bets, equity, prediction_count=374,
                  matched_valid_odds_count=374, initial_bankroll=100000, bootstrap_samples=0)
        for field in ("profit", "roi", "hit_ratio", "max_drawdown", "trading_frequency"):
            left, right = summary[field], frozen_rows.loc[strategy, field]
            if left is None or pd.isna(left):
                assert pd.isna(right)
            else:
                assert np.isclose(left, right, rtol=1e-10, atol=1e-7), (strategy, field, left, right)
