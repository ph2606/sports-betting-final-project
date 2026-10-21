"""Chronological isolation, explicit feature contracts and frozen future models."""
from copy import deepcopy
import json
from pathlib import Path
import shutil

import joblib
import numpy as np
import pandas as pd
import pytest

from epl_modeling.ablation import TEAM_PERFORMANCE, TEAM_FLAGS
from epl_player_models import models


@pytest.fixture
def inputs():
    coverage = list(models.SHARED_COVERAGE)
    team = TEAM_PERFORMANCE + TEAM_FLAGS + coverage
    form = coverage + ["feat_player_home_form"]
    squad = form + ["feat_player_home_depth"]
    groups = {"team_control": team, "player_form": form, "player_squad": squad,
              "team_player_squad": team + [column for column in squad if column not in team]}
    rng = np.random.default_rng(52)
    rows = []
    for year in range(2016, 2027):
        for i in range(9):
            date = pd.Timestamp(year=year, month=8, day=1) + pd.Timedelta(days=i)
            row = {"match_id": f"{year}-{i}", "match_date": date,
                   "season": models.season(year), "result": models.CLASSES[i % 3]}
            row.update({column: rng.normal() for column in groups["team_player_squad"]})
            for column in coverage:
                row[column] = 5.0 if "observed" in column else 0.0
            row["audit_player_home_latest_source_date"] = date - pd.Timedelta(days=1)
            row["audit_player_away_latest_source_date"] = date - pd.Timedelta(days=2)
            rows.append(row)
    return pd.DataFrame(rows), groups


@pytest.fixture
def tiny_training(monkeypatch):
    """Exercise the complete fitting flow with a deliberately small test budget."""
    original = models._estimator

    def tiny(kind, parameter):
        estimator = original(kind, parameter)
        if kind == "hist_boost":
            estimator.set_params(max_iter=4, min_samples_leaf=2)
        return estimator

    monkeypatch.setattr(models, "OUTER_YEARS", (2025,))
    monkeypatch.setattr(models, "LOGIT_C_GRID", (0.3,))
    monkeypatch.setattr(models, "BOOST_LEAF_GRID", (3,))
    monkeypatch.setattr(models, "_estimator", tiny)


def test_declared_estimator_parameters_and_empty_feature_handling():
    boost = models._estimator("hist_boost", 7)
    assert boost.max_leaf_nodes == 7 and boost.max_iter == 150
    assert boost.learning_rate == 0.05 and boost.min_samples_leaf == 40
    assert boost.l2_regularization == 10 and boost.early_stopping is False
    assert boost.random_state == 42 and boost.categorical_features is None
    logistic = models._estimator("logistic", 0.3)
    assert logistic[-1].C == 0.3 and logistic[-1].solver == "lbfgs"
    assert logistic[0].keep_empty_features and logistic[0].add_indicator
    x = pd.DataFrame({"all_missing": [np.nan] * 9, "observed": np.arange(9)})
    logistic.fit(x, np.arange(9) % 3)
    p = logistic.predict_proba(x)
    assert p.shape == (9, 3)
    np.testing.assert_allclose(p.sum(axis=1), 1)


@pytest.mark.parametrize("corruption", ["duplicate_match", "forbidden_feature", "missing_shared_coverage",
                                        "pure_player_team_stat", "combined_extra_feature", "nonprior_evidence",
                                        "season_date_disagreement", "infinite_feature"])
def test_invalid_identity_feature_or_evidence_rejected(inputs, corruption):
    frame, groups = inputs
    frame, groups = frame.copy(), deepcopy(groups)
    if corruption == "duplicate_match":
        frame.loc[1, "match_id"] = frame.loc[0, "match_id"]
    elif corruption == "forbidden_feature":
        frame["feat_target_minutes"] = 80
        groups["player_form"].append("feat_target_minutes")
    elif corruption == "missing_shared_coverage":
        groups["player_form"].remove(models.SHARED_COVERAGE[0])
    elif corruption == "pure_player_team_stat":
        groups["player_form"].append(TEAM_PERFORMANCE[0])
    elif corruption == "combined_extra_feature":
        frame["feat_unregistered_extra"] = 1
        groups["team_player_squad"].append("feat_unregistered_extra")
    elif corruption == "nonprior_evidence":
        frame.loc[0, "audit_player_home_latest_source_date"] = frame.loc[0, "match_date"]
    elif corruption == "season_date_disagreement":
        frame.loc[0, "match_date"] = pd.Timestamp("2020-09-01")
    elif corruption == "infinite_feature":
        frame.loc[0, "feat_player_home_form"] = np.inf
    with pytest.raises(ValueError):
        models._prepare(frame, groups)


def test_fold_roles_have_no_overlap_and_refuse_missing_outcome_class(inputs):
    frame, groups = inputs
    prepared, _ = models._prepare(frame, groups)
    roles = models.fold_roles(2022)
    blocks, audit = models._blocks(prepared, roles)
    assert set(blocks["train"].season) == {"2016-17", "2017-18", "2018-19", "2019-20"}
    assert blocks["train"].match_date.max() < blocks["tune"].match_date.min()
    assert blocks["tune"].match_date.max() < blocks["calibration"].match_date.min()
    assert blocks["calibration"].match_date.max() < blocks["evaluation"].match_date.min()
    bad_roles = deepcopy(roles)
    bad_roles["tune"] = roles["train"]
    with pytest.raises(ValueError, match="overlap"):
        models._blocks(prepared, bad_roles)
    prepared.loc[prepared.season == "2020-21", "result"] = "H"
    with pytest.raises(ValueError, match="all three outcomes"):
        models._blocks(prepared, roles)


def test_rolling_fit_calibration_ignore_evaluation_outcomes_and_future_rows(inputs, tiny_training, tmp_path):
    frame, groups = inputs
    original = frame.copy(deep=True)
    first = models.train_rolling(frame, groups, tmp_path / "a")
    changed = frame.copy(deep=True)
    mask = changed.season == "2025-26"
    changed.loc[mask, "result"] = changed.loc[mask, "result"].map({"H": "D", "D": "A", "A": "H"})
    changed.loc[changed.season == "2026-27", groups["team_player_squad"]] = 9000
    second = models.train_rolling(changed, groups, tmp_path / "b")
    columns = ["p_H", "p_D", "p_A", "p_raw_H", "p_raw_D", "p_raw_A"]
    np.testing.assert_array_equal(first["predictions"][columns], second["predictions"][columns])
    pd.testing.assert_frame_equal(first["tuning_trials"], second["tuning_trials"])
    np.testing.assert_array_equal(first["fitted_choices"].temperature, second["fitted_choices"].temperature)
    assert len(first["predictions"]) == 8 * 9
    assert first["models_metadata"]["n_models"] == 8
    assert len(first["model_metrics_pooled"]) == 8
    assert len(first["model_metrics_seasonal"]) == 8
    assert len(first["paired_feature_comparisons"]) == 36  # six candidate/control pairs ×3 metrics ×season/pooled
    np.testing.assert_allclose(first["predictions"][["p_H", "p_D", "p_A"]].sum(axis=1), 1)
    assert not first["predictions"].duplicated(["match_id", "feature_group", "model_type"]).any()
    assert len(first["logistic_coefficients"]) > 0
    pd.testing.assert_frame_equal(frame, original)
    for row in first["models_metadata"]["artifacts"]:
        assert "2025-26" not in row["refit_seasons"]
        assert row["calibration_seasons"] == ["2024-25"]


def test_future_models_never_fit_2026_and_predictions_are_hash_guarded(inputs, tiny_training, tmp_path):
    frame, groups = inputs
    metadata = models.fit_future(frame, groups, tmp_path / "a")
    target = frame.loc[frame.season == "2026-27"].drop(columns="result").copy()
    prediction = models.predict_future(metadata, target)
    assert len(prediction) == 8 * len(target)
    assert "result" not in prediction
    assert metadata["roles"]["train"] == [models.season(year) for year in range(2016, 2024)]
    assert metadata["roles"]["tune"] == ["2024-25"]
    assert metadata["roles"]["calibration"] == ["2025-26"]
    assert metadata["outcomes_from_2026_27_used_for_fitting"] is False
    assert prediction.model_artifact_sha256.nunique() == 8
    changed = frame.copy(deep=True)
    changed.loc[changed.season == "2026-27", groups["team_player_squad"]] = -700
    changed.loc[changed.season == "2026-27", "result"] = "H"
    second_metadata = models.fit_future(changed, groups, tmp_path / "b")
    second = models.predict_future(second_metadata, target)
    np.testing.assert_array_equal(prediction[["p_H", "p_D", "p_A"]], second[["p_H", "p_D", "p_A"]])
    with pytest.raises(ValueError, match="restricted"):
        models.predict_future(metadata, frame.loc[frame.season == "2025-26"])
    artifact = metadata["artifacts"][0]
    with open(artifact["artifact_path"], "ab") as stream:
        stream.write(b"changed")
    with pytest.raises(ValueError, match="hash changed"):
        models.predict_future(metadata, target)


def test_future_metadata_identity_cannot_omit_or_duplicate_models(inputs, tiny_training, tmp_path):
    frame, groups = inputs
    metadata = models.fit_future(frame, groups, tmp_path)
    target = frame.loc[frame.season == "2026-27"].drop(columns="result")
    invalid = deepcopy(metadata)
    invalid["artifacts"][1] = deepcopy(invalid["artifacts"][0])
    with pytest.raises(ValueError, match="identities"):
        models.predict_future(invalid, target)


def test_future_bundle_relocation_preserves_probabilities_and_hashes(inputs, tiny_training, tmp_path):
    frame, groups = inputs
    metadata = models.fit_future(frame, groups, tmp_path / "original")
    target = frame.loc[frame.season == "2026-27"].drop(columns="result")
    expected = models.predict_future(metadata, target)
    relocation = tmp_path / "different_clone" / "future_models"
    relocation.mkdir(parents=True)
    for row in metadata["artifacts"]:
        source = Path(row["artifact_path"])
        assert row["artifact_name"] == source.name
        shutil.copy2(source, relocation / row["artifact_name"])
    relocated_metadata = deepcopy(metadata)
    for row in relocated_metadata["artifacts"]:
        row["artifact_path"] = str(tmp_path / "absent_original_machine" / row["artifact_name"])
    actual = models.predict_future(relocated_metadata, target, artifact_root=relocation)
    pd.testing.assert_frame_equal(actual, expected)
    assert actual.model_artifact_sha256.tolist() == expected.model_artifact_sha256.tolist()
    unsafe = deepcopy(relocated_metadata)
    unsafe["artifacts"][0]["artifact_name"] = "../outside.joblib"
    with pytest.raises(ValueError, match="safe artifact_name"):
        models.predict_future(unsafe, target, artifact_root=relocation)
