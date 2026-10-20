"""Small known outcomes verify cohort isolation, paired inference and clocks."""
from __future__ import annotations

from copy import deepcopy
import math

import numpy as np
import pandas as pd
import pytest

from epl_prospective.analysis import (BOOTSTRAP_SAMPLES, BOOTSTRAP_SEED,
                                    build_analysis, wilson_accuracy_interval)


def cohort():
    probabilities = {
        "model_a": {"H": .6, "D": .2, "A": .2},
        "model_b": {"H": .2, "D": .6, "A": .2},
        "model_c": {"H": .2, "D": .2, "A": .6},
        "model_d": {"H": .4, "D": .35, "A": .25},
    }
    forecasts, outcomes = [], []
    for index in range(10):
        result = "HDA"[index % 3]
        identity = {"match_id": f"fpl_2026-27_{61 + index}", "season": "2026-27",
                    "home_team": f"Home{index}", "away_team": f"Away{index}",
                    "kickoff_utc": f"2026-10-17T{12 + index:02d}:00:00+00:00"}
        for model, p in probabilities.items():
            forecasts.append({**identity, "model_id": model, "probabilities": p.copy(),
                "created_at_utc": "2026-10-14T09:00:00+00:00", "target_match_date": "2026-10-17",
                "fpl_fixture_id": 61 + index, "feature_group": "group_" + model,
                "forecast_type": "team_only", "update_version": 1,
                "protocol_committed_at_utc": "2026-10-13T09:00:00+00:00",
                "source_snapshots": [{"observed_at_utc": "2026-10-14T08:00:00+00:00"}],
                "latest_feature_match_dates": {"team": "2026-10-12"}})
        hg, ag = {"H": (2, 1), "D": (1, 1), "A": (0, 1)}[result]
        outcomes.append({**identity, "result": result, "home_goals": hg, "away_goals": ag,
                         "settled_at_utc": "2026-10-20T08:00:00+00:00"})
    return forecasts, outcomes


def analyze(forecasts=None, outcomes=None):
    original_forecasts, original_outcomes = cohort()
    return build_analysis(original_forecasts if forecasts is None else forecasts,
        original_outcomes if outcomes is None else outcomes,
        original_match_ids={row["match_id"] for row in original_forecasts},
        original_model_ids={row["model_id"] for row in original_forecasts})


def test_known_accuracy_losses_brier_and_distinct_fixture_counts():
    tables = analyze()
    assert {name: len(frame) for name, frame in tables.items()} == {
        "forecast_outcome_audit": 40, "model_scores": 4, "pairwise_scores": 6, "fixture_outcomes": 10}
    scores = tables["model_scores"].set_index("model_id")
    a = scores.loc["model_a"]
    assert a.n_matches == a.independent_fixture_count == 10
    assert a.accuracy == .4
    assert a.log_loss == pytest.approx(-.4 * math.log(.6) - .6 * math.log(.2))
    # Brier is the unscaled sum over H/D/A: .24 on H, 1.04 otherwise.
    assert a.brier_score == pytest.approx(.4 * .24 + .6 * 1.04)
    assert a.accuracy_ci_low == pytest.approx(.16818032970623614)
    assert a.accuracy_ci_high == pytest.approx(.6873262302663417)
    assert scores.n_matches.sum() == 40
    assert tables["fixture_outcomes"].independent_fixture_count.sum() == 10
    assert tables["fixture_outcomes"].all_models_forecasted.all()
    assert tables["forecast_outcome_audit"].status.eq("settled").all()
    assert scores.no_selected_winner.all()
    assert scores.not_multiplicity_adjusted.all()
    assert not any("roi" in name.lower() for name in scores.columns)


def test_pairwise_resamples_shared_fixture_differences_not_independent_models():
    tables = analyze()
    pair = tables["pairwise_scores"].query("model_a == 'model_a' and model_b == 'model_b'").iloc[0]
    # Ten native fixture IDs are numerically ordered in this synthetic example.
    difference = np.array([1, -1, 0, 1, -1, 0, 1, -1, 0, 1], dtype=float)
    indices = np.random.default_rng(20261020).integers(0, 10, size=(9999, 10))
    expected_interval = np.quantile(difference[indices].mean(axis=1), [.025, .975])
    assert pair.accuracy_diff == pytest.approx(.1)
    assert pair.accuracy_diff_ci_low == pytest.approx(expected_interval[0])
    assert pair.accuracy_diff_ci_high == pytest.approx(expected_interval[1])
    assert pair.log_loss_diff == pytest.approx(-.1 * math.log(3))
    assert pair.difference_direction == "model_a_minus_model_b"
    assert pair.common_fixture_count == 10
    assert pair.bootstrap_samples == BOOTSTRAP_SAMPLES == 9999
    assert pair.bootstrap_seed == BOOTSTRAP_SEED == 20261020


def test_pending_results_are_unscored_and_shared_population_reconciles():
    _, outcomes = cohort()
    tables = analyze(outcomes=outcomes[:3])
    scores, audit = tables["model_scores"], tables["forecast_outcome_audit"]
    assert scores.forecast_count.eq(10).all()
    assert scores.settled_count.eq(3).all()
    assert scores.pending_count.eq(7).all()
    assert scores.n_matches.eq(3).all()
    assert scores.common_settled_fixture_count.eq(3).all()
    assert tables["pairwise_scores"].common_fixture_count.eq(3).all()
    pending = audit.loc[audit.status.eq("pending")]
    assert len(pending) == 28
    assert pending[["correct", "log_loss", "brier_score"]].isna().all().all()
    assert pending.actual_result.isna().all()


def test_no_outcomes_has_no_zero_error_or_zero_accuracy_claim():
    tables = analyze(outcomes=[])
    scores = tables["model_scores"]
    assert scores.n_matches.eq(0).all()
    assert scores.pending_count.eq(10).all()
    assert scores[["accuracy", "log_loss", "brier_score", "accuracy_ci_low", "log_loss_ci_high"]].isna().all().all()
    assert scores.bootstrap_valid_samples.eq(0).all()
    assert tables["pairwise_scores"][["accuracy_diff", "log_loss_diff", "brier_score_diff"]].isna().all().all()


def test_future_cohorts_models_and_later_updates_do_not_contaminate_first_release():
    original, outcomes = cohort()
    changed = deepcopy(original[0])
    changed.update(update_version=2, probabilities={"H": 0., "D": 0., "A": 1.})
    extra_model = deepcopy(original[0])
    extra_model.update(model_id="future_model", probabilities={"invalid": 5.})
    future_fixture = deepcopy(original[0])
    future_fixture.update(match_id="fpl_2026-27_999", probabilities={"invalid": 5.})
    expected = analyze(original, outcomes)
    actual = analyze([changed, extra_model, future_fixture, *original], [*outcomes, {"match_id": "future"}])
    for name in expected:
        pd.testing.assert_frame_equal(actual[name], expected[name])


def test_mandatory_original_grid_missing_version_one_fails_closed():
    forecasts, outcomes = cohort()
    forecasts[0]["update_version"] = 2
    with pytest.raises(ValueError, match="mandatory original"):
        analyze(forecasts, outcomes)


def test_duplicate_original_version_or_outcome_fails_instead_of_choosing_row_order():
    forecasts, outcomes = cohort()
    with pytest.raises(ValueError, match="Duplicate original forecast"):
        analyze([*forecasts, forecasts[0]], outcomes)
    with pytest.raises(ValueError, match="Duplicate original outcome"):
        analyze(forecasts, [*outcomes, outcomes[0]])


@pytest.mark.parametrize("probabilities", [
    {"H": .5, "D": .5}, {"H": .5, "D": .5, "A": .5},
    {"H": float("nan"), "D": .3, "A": .3}, {"H": 1.1, "D": -.1, "A": 0.},
    {"H": True, "D": 0., "A": 0.},
])
def test_invalid_or_incomplete_probabilities_rejected(probabilities):
    forecasts, outcomes = cohort()
    forecasts[0]["probabilities"] = probabilities
    with pytest.raises(ValueError, match="[Pp]robabilities"):
        analyze(forecasts, outcomes)


def test_zero_one_probabilities_match_frozen_sklearn_clipping_without_infinity():
    forecasts, outcomes = cohort()
    for forecast in forecasts:
        if forecast["model_id"] == "model_a":
            forecast["probabilities"] = {"H": 1., "D": 0., "A": 0.}
    tables = analyze(forecasts, outcomes)
    a = tables["model_scores"].set_index("model_id").loc["model_a"]
    eps = np.finfo(np.float64).eps
    assert a.log_loss == pytest.approx(-.4 * math.log(1 - eps) - .6 * math.log(eps))
    assert np.isfinite(tables["forecast_outcome_audit"].log_loss).all()


def test_ties_use_fixed_h_then_d_then_a_order():
    forecasts, outcomes = cohort()
    for forecast in forecasts:
        forecast["probabilities"] = {"H": 1 / 3, "D": 1 / 3, "A": 1 / 3}
    tables = analyze(forecasts, outcomes)
    assert tables["forecast_outcome_audit"].predicted_outcome.eq("H").all()
    assert tables["model_scores"].accuracy.eq(.4).all()


@pytest.mark.parametrize("field,value,message", [
    ("created_at_utc", "2026-10-17T12:00:00+00:00", "strictly before"),
    ("created_at_utc", "2026-10-14T09:00:00", "timezone-aware"),
    ("target_match_date", "2026-10-18", "Target match date"),
    ("fpl_fixture_id", 999, "FPL fixture ID"),
])
def test_forecast_timing_and_native_id_controls(field, value, message):
    forecasts, outcomes = cohort()
    forecasts[0][field] = value
    with pytest.raises(ValueError, match=message):
        analyze(forecasts, outcomes)


def test_original_model_fixture_identities_must_agree():
    forecasts, outcomes = cohort()
    forecasts[1]["home_team"] = "AnotherClub"
    with pytest.raises(ValueError, match="models disagree"):
        analyze(forecasts, outcomes)


def test_outcome_clocks_scores_and_native_identities_must_agree():
    forecasts, outcomes = cohort()
    changed = deepcopy(outcomes)
    changed[0]["home_team"] = "AnotherClub"
    with pytest.raises(ValueError, match="native fixture"):
        analyze(forecasts, changed)
    changed = deepcopy(outcomes)
    changed[0]["settled_at_utc"] = "2026-10-17T11:00:00+00:00"
    with pytest.raises(ValueError, match="precedes"):
        analyze(forecasts, changed)
    changed = deepcopy(outcomes)
    changed[0]["result"] = "A"
    with pytest.raises(ValueError, match="supplied goals"):
        analyze(forecasts, changed)


def test_source_and_feature_timing_cannot_follow_prediction_cutoff():
    forecasts, outcomes = cohort()
    forecasts[0]["source_snapshots"][0]["observed_at_utc"] = "2026-10-14T10:00:00+00:00"
    with pytest.raises(ValueError, match="source observation"):
        analyze(forecasts, outcomes)
    forecasts, outcomes = cohort()
    forecasts[0]["latest_feature_match_dates"]["team"] = "2026-10-17"
    with pytest.raises(ValueError, match="feature match date"):
        analyze(forecasts, outcomes)


def test_wilson_interval_uses_ten_not_forty_outcomes_and_rejects_invalid_counts():
    low, high = wilson_accuracy_interval(4, 10)
    low_40, high_40 = wilson_accuracy_interval(16, 40)
    assert low < low_40 < high_40 < high
    assert wilson_accuracy_interval(0, 0)[0] is np.nan or np.isnan(wilson_accuracy_interval(0, 0)[0])
    with pytest.raises(ValueError):
        wilson_accuracy_interval(11, 10)
