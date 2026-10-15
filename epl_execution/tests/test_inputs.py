from collections import Counter
from copy import deepcopy
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from epl_execution import inputs
from epl_strategy.metrics import reconstruct_equity, summarize_strategy
from epl_strategy_lab.catalog import build_catalog
from epl_strategy_lab.inputs import load_inputs as load_single
from epl_strategy_validation.inputs import load_inputs as load_rolling


ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def frozen_leaves():
    return load_single(ROOT), load_rolling(ROOT)


@pytest.fixture(scope="module")
def complete():
    return inputs.load_inputs(ROOT)


def test_complete_inventory_preserves_all_real_accounts_and_prediction_histories(complete):
    assert len(complete["catalog"]) == 84
    assert Counter(account["scope"] for account in complete["accounts"]) == {"single": 84, "continuous": 56, "seasonal": 224}
    assert len({account["account_id"] for account in complete["accounts"]}) == 364
    assert len(complete["opportunities"]) == 1470
    assert complete["opportunities"].match_date.nunique() == 453
    assert len(complete["models"]) == 16
    for key, model in complete["models"].items():
        assert len(model) == (374 if key.startswith("first_") else 1470)
    for account in complete["accounts"]:
        config = account["config"]
        assert account["account_id"] == f"{account['scope']}:{config['strategy_id']}:{account['season']}"
        assert account["original_equity"].episode_id.eq(account["episode_id"]).all()
        assert len(account["opportunities"]) == account["original_metrics"]["prediction_count"]
        assert len(account["original_bets"]) == account["original_metrics"]["bet_count"]
        if account["scope"] != "single":
            assert not config["model_key"].startswith("first_")
    cash = [account for account in complete["accounts"] if account["config"]["cash_only"]]
    assert len(cash) == 8 and all(account["original_bets"].empty for account in cash)


def test_source_inventory_is_complete_unique_and_excludes_mutable_latest_copies():
    paths = inputs.source_paths(ROOT)
    assert len(paths) == 30 and len(paths) == len(set(paths))
    assert all(path.is_file() and ROOT in path.parents for path in paths)
    assert not any("reports/latest" in path.as_posix() for path in paths)
    for name in ("match_odds_1x2_long.parquet", "matches_current_cohort.parquet",
                 "selection_comparison.parquet", "selection_global.parquet",
                 "all_strategies_4seasons_100k.png", "all_84_strategies_2025_100k.png"):
        assert any(path.name == name for path in paths)
    assert inputs.source_paths(ROOT.parent) == paths


def _copy_leaves(frozen_leaves):
    single, rolling = frozen_leaves
    return (({key: frame.copy(deep=True) for key, frame in single[0].items()}, single[1].copy(deep=True), single[2]),
            ({key: frame.copy(deep=True) for key, frame in rolling[0].items()}, rolling[1].copy(deep=True), rolling[2]))


@pytest.mark.parametrize("problem", ["price", "probability", "model_membership", "unlisted_source"])
def test_two_studies_cannot_disagree_on_the_same_2025_fixture(monkeypatch, frozen_leaves, problem):
    single, rolling = _copy_leaves(frozen_leaves)
    if problem == "price": single[1].loc[0, "odds_H"] += .1
    elif problem == "probability": single[0]["logit_team_only"].loc[0, "p_H"] += .01
    elif problem == "model_membership": single[0].pop("first_accuracy")
    elif problem == "unlisted_source": single = (single[0], single[1], [ROOT / "absent_source.parquet"])
    monkeypatch.setattr(inputs, "load_single", lambda root: single)
    monkeypatch.setattr(inputs, "load_rolling", lambda root: rolling)
    with pytest.raises(ValueError, match="disagree|Expected fourteen|unlisted frozen source|does not reconcile"):
        inputs.load_inputs(ROOT)


@pytest.mark.parametrize("problem", ["missing_strategy", "duplicate_strategy", "missing_season", "extra_episode"])
def test_source_account_populations_cannot_be_silently_reduced_or_extended(monkeypatch, frozen_leaves, problem):
    single, rolling = frozen_leaves
    monkeypatch.setattr(inputs, "load_single", lambda root: single)
    monkeypatch.setattr(inputs, "load_rolling", lambda root: rolling)
    original_reader = pd.read_parquet

    def reader(path, *args, **kwargs):
        frame = original_reader(path, *args, **kwargs)
        name = Path(path).name
        if problem == "missing_strategy" and name == "metrics_continuous.parquet": return frame.iloc[1:].copy()
        if problem == "duplicate_strategy" and name == "metrics_continuous.parquet": return pd.concat([frame, frame.iloc[[0]]], ignore_index=True)
        if problem == "missing_season" and name == "metrics_seasonal.parquet": return frame.iloc[1:].copy()
        if problem == "extra_episode" and name == "bets_continuous.parquet":
            extra = frame.iloc[[0]].copy()
            extra["episode_id"] = "invented_episode"
            return pd.concat([frame, extra], ignore_index=True)
        return frame

    monkeypatch.setattr(pd, "read_parquet", reader)
    with pytest.raises(ValueError, match="population|count changed|unknown account episode"):
        inputs.load_inputs(ROOT)


def small_account():
    config = deepcopy(build_catalog()[16])
    config["model_key"] = "model"
    dates = pd.to_datetime(["2025-08-15", "2025-08-16"])
    native = pd.DataFrame({"match_id": ["a", "b"], "match_date": dates,
                           "season": "2025-26", "result": ["H", "D"]})
    for outcome, odds in zip("HDA", [3., 4., 5.]):
        native[f"odds_{outcome}"] = odds
        native[f"ref_odds_{outcome}"] = odds - 1
        native[f"bookmaker_{outcome}"] = "BestBook"
    native["reference_bookmaker"] = "Bet365"
    bets = pd.DataFrame({"strategy_id": "S017", "episode_id": "one", "match_id": ["a", "b"],
        "match_date": dates, "selection": "H", "result": ["H", "D"], "probability": .5,
        "odds": 3., "stake": 1000., "won": [True, False], "gross_return": [3000., 0.],
        "profit": [2000., -1000.], "bookmaker": "BestBook"})
    equity = reconstruct_equity(bets, native, initial_bankroll=100000., episode_id="one")
    equity["strategy_id"] = "S017"
    metric = {**{key: json.dumps(value) if isinstance(value, list) else value for key, value in config.items()},
              **summarize_strategy(bets, equity, prediction_count=2, matched_valid_odds_count=2,
                                   initial_bankroll=100000., bootstrap_samples=0)}
    model = pd.DataFrame({"match_id": ["a", "b"], "p_H": .5, "p_D": .3, "p_A": .2})
    return config, metric, bets, equity, native, {"model": model}, "one"


def test_original_account_audit_accepts_recorded_quote_probability_and_date_cashflows():
    inputs._check_account(*small_account())


@pytest.mark.parametrize("problem", ["model_probability", "quote", "bookmaker", "cash_continuity", "funding",
                                     "missing_date", "metric_profit", "metric_expectation", "config", "wrong_season"])
def test_original_account_audit_rejects_false_forecast_quote_metric_or_funding(problem):
    config, metric, bets, equity, native, models, episode = small_account()
    if problem == "model_probability": models["model"].loc[0, "p_H"] = .6
    elif problem == "quote": native.loc[0, "odds_H"] = 4.
    elif problem == "bookmaker": bets.loc[0, "bookmaker"] = "OtherBook"
    elif problem == "cash_continuity": equity.loc[1, "start_bankroll"] += 500.
    elif problem == "funding":
        bets["stake"] = 200000.
        bets["gross_return"] = [600000., 0.]
        bets["profit"] = [400000., -200000.]
        equity["turnover"] = 200000.
        equity["profit"] = [400000., -200000.]
        equity["start_bankroll"] = [100000., 500000.]
        equity["end_bankroll"] = [500000., 300000.]
    elif problem == "missing_date": equity = equity.iloc[:1]
    elif problem == "metric_profit": metric["profit"] += 10.
    elif problem == "metric_expectation": metric["expected_gain_total_units"] += 10.
    elif problem == "config": metric["min_edge"] = .15
    elif problem == "wrong_season": bets["season"] = "2024-25"
    with pytest.raises(ValueError):
        inputs._check_account(config, metric, bets, equity, native, models, episode)
