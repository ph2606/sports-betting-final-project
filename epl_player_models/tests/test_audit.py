"""Independent qualifier, allocation, model-probability and graph audits."""
from copy import deepcopy

import numpy as np
import pandas as pd
import pytest
from sklearn.linear_model import LogisticRegression
from scipy.special import softmax

from epl_modeling.metrics import TemperatureCalibrator
from epl_player_models.audit import _audit_policy, _audit_graph, _verify_bundle_probabilities


def _policy_case(staking="fixed", odds_mode="best"):
    dates = pd.to_datetime(["2025-08-15", "2025-08-15", "2025-08-16"])
    opportunities = pd.DataFrame({"match_id": ["a", "b", "c"], "match_date": dates,
        "season": "2025-26", "result": ["H", "D", "A"],
        "odds_H": [2.5, 2.5, 2], "odds_D": [5, 5, 3], "odds_A": [3, 3, 3],
        "ref_odds_H": [2.5, 2.5, 2], "ref_odds_D": [5, 5, 3], "ref_odds_A": [3, 3, 3],
        "bookmaker_H": "BestH", "bookmaker_D": "BestD", "bookmaker_A": "BestA", "reference_bookmaker": "Bet365"})
    probabilities = opportunities[["match_id", "match_date", "season", "result"]].copy()
    probabilities["model_key"] = "new_model"
    probabilities[["p_H", "p_D", "p_A"]] = [0.5, 0.25, 0.25]
    stake = 750.0 if staking == "fixed" else 30.0  # Kelly .25*.25/1.5, capped at2% of1500
    bets = pd.DataFrame({"match_id": ["a", "b"], "match_date": dates[:2], "selection": "H",
        "probability": 0.5, "odds": 2.5, "stake": stake,
        "bookmaker": "Bet365" if odds_mode == "reference" else "BestH"})
    equity = pd.DataFrame({"match_date": pd.to_datetime(["2025-08-15", "2025-08-16"]),
        "start_bankroll": [1500.0, 1500 + stake * 0.5], "qualified_matches": [2, 0]})
    return {"model_key": "new_model", "staking": staking, "odds_mode": odds_mode}, probabilities, opportunities, bets, equity


@pytest.mark.parametrize("staking,odds_mode", [("fixed", "best"), ("kelly", "best"), ("fixed", "reference"), ("kelly", "reference")])
def test_native_max_edge_ties_price_mode_and_opening_cash_allocation(staking, odds_mode):
    assert _audit_policy(*_policy_case(staking, odds_mode)) == 2


@pytest.mark.parametrize("change", ["missed_bet", "incorrect_selection", "future_cash_sizing", "wrong_price", "wrong_probability", "wrong_book", "result_conflict"])
def test_native_qualification_or_allocation_corruption_is_rejected(change):
    config, probabilities, opportunities, bets, equity = _policy_case()
    if change == "missed_bet": bets = bets.iloc[:1]
    elif change == "incorrect_selection": bets.loc[0, "selection"] = "D"
    elif change == "future_cash_sizing": bets.loc[0, "stake"] = 1000.0
    elif change == "wrong_price": bets.loc[0, "odds"] = 3.0
    elif change == "wrong_probability": bets.loc[0, "probability"] = 0.6
    elif change == "wrong_book": bets.loc[0, "bookmaker"] = "Other"
    elif change == "result_conflict": probabilities.loc[0, "result"] = "D"
    with pytest.raises(AssertionError):
        _audit_policy(config, probabilities, opportunities, bets, equity)


def _graph_case():
    dates = pd.to_datetime(["2025-08-15", "2025-08-16"])
    old = pd.DataFrame([{"strategy_id": sid, "match_date": day, "end_bankroll": 100000 + i * 100}
                        for sid in ["S001", "S002"] for i, day in enumerate(dates)])
    new = pd.DataFrame([{"strategy_id": f"P{sid:03d}", "match_date": day, "end_bankroll": 100000 - i * sid}
                        for sid in range(1, 33) for i, day in enumerate(dates)])
    all_points = pd.concat([old, new], ignore_index=True)
    all_points["is_initial"] = False
    initial = pd.DataFrame({"strategy_id": all_points.strategy_id.unique(), "match_date": pd.Timestamp("2025-08-14"),
                            "end_bankroll": 100000., "is_initial": True})
    graph = pd.concat([initial, all_points], ignore_index=True)
    return graph, new, old


def test_every_graph_money_point_is_checked_including_frozen_originals():
    assert _audit_graph(*_graph_case(), anchor_date="2025-08-14", n_old=2, points_per_curve=3) == 102


@pytest.mark.parametrize("change", ["old_point", "new_point", "missing_curve", "wrong_anchor", "duplicate_date"])
def test_graph_corruption_is_rejected(change):
    graph, new, old = _graph_case()
    if change == "old_point": graph.loc[(graph.strategy_id == "S001") & ~graph.is_initial, "end_bankroll"] += 1
    elif change == "new_point": graph.loc[(graph.strategy_id == "P001") & ~graph.is_initial, "end_bankroll"] += 1
    elif change == "missing_curve": graph = graph.loc[graph.strategy_id != "P032"]
    elif change == "wrong_anchor": graph.loc[graph.is_initial, "end_bankroll"] = 99999
    elif change == "duplicate_date": graph.loc[0, "match_date"] = pd.Timestamp("2025-08-15")
    with pytest.raises(AssertionError):
        _audit_graph(graph, new, old, anchor_date="2025-08-14", n_old=2, points_per_curve=3)


def test_bundle_predictions_recomputed_with_class_order_and_temperature():
    frame = pd.DataFrame({"match_id": [f"m{i}" for i in range(12)], "feature": np.arange(12)})
    model = LogisticRegression().fit(frame[["feature"]], np.arange(12) % 3)
    calibrator = TemperatureCalibrator(temperature=2.5)
    bundle = {"features": ["feature"], "model": model, "calibrator": calibrator, "temperature": 2.5}
    logits = np.log(model.predict_proba(frame[["feature"]]))
    predicted = frame[["match_id"]].copy()
    predicted[["p_H", "p_D", "p_A"]] = softmax(logits / 2.5, axis=1)
    predicted[["p_raw_H", "p_raw_D", "p_raw_A"]] = softmax(logits, axis=1)
    _verify_bundle_probabilities(bundle, frame, predicted)
    changed = predicted.copy()
    changed.loc[0, "p_H"] += 0.01
    with pytest.raises(AssertionError, match="calibrated"):
        _verify_bundle_probabilities(bundle, frame, changed)
    changed_bundle = deepcopy(bundle)
    changed_bundle["temperature"] = 1.0
    with pytest.raises(AssertionError, match="temperature"):
        _verify_bundle_probabilities(changed_bundle, frame, predicted)
