"""Fixed-family rolling H/D/A models with separate chronological calibration.

Only explicitly declared numeric feature lists enter estimators. Historical
experiments are exploratory, and prospective bundles never fit 2026 outcomes.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from scipy.special import softmax
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits

from epl_modeling.ablation import TEAM_PERFORMANCE, TEAM_FLAGS, fold_roles, season, date_stratified_paired_intervals
from epl_modeling.metrics import CLASSES, TemperatureCalibrator, classification_metrics, encode_results, estimator_logits


GROUPS = ("team_control", "player_form", "player_squad", "team_player_squad")
MODEL_TYPES = ("logistic", "hist_boost")
OUTER_YEARS = (2022, 2023, 2024, 2025)
LOGIT_C_GRID = (0.03, 0.3, 3.0)
BOOST_LEAF_GRID = (3, 7, 15)
RANDOM_STATE = 42
SHARED_COVERAGE = tuple(f"feat_player_{side}_{field}" for side in ("home", "away")
                        for field in ("observed_matches5", "observed_matches10", "history_missing"))
STUDY_STATUS = "exploratory_retrospective_previously_inspected_outcomes_not_fresh_holdout"


def _save(frame, directory, stem):
    frame.to_csv(directory / f"{stem}.csv", index=False)
    frame.to_parquet(directory / f"{stem}.parquet", index=False)


def _write_json(path, data):
    path.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def _check_groups(frame, feature_groups):
    if set(feature_groups) != set(GROUPS):
        raise ValueError(f"Declare exactly these four feature groups: {GROUPS}")
    groups = {}
    for group in GROUPS:
        columns = feature_groups[group]
        if not isinstance(columns, (list, tuple)) or not columns or len(set(columns)) != len(columns):
            raise ValueError("Features must be nonempty explicit unique lists")
        for column in columns:
            if not isinstance(column, str) or not column.startswith("feat_") or column.startswith(("feat_target_", "feat_current_")) or any(token in column.lower() for token in ("target_minutes", "target_starts", "_current", "_result", "_xg", "_us_", "odds", "ref_p_")):
                raise ValueError(f"Forbidden feature: {column}")
        if not set(columns).issubset(frame.columns):
            raise ValueError(f"Missing fixed features in {group}: {sorted(set(columns) - set(frame.columns))}")
        if not set(SHARED_COVERAGE).issubset(columns):
            raise ValueError("Every group must share the six player coverage controls")
        groups[group] = list(columns)
    expected_control = set(TEAM_PERFORMANCE + TEAM_FLAGS) | set(SHARED_COVERAGE)
    if set(groups["team_control"]) != expected_control:
        raise ValueError("team_control must contain only the 13 fixed team inputs and shared player coverage")
    for group in ("player_form", "player_squad"):
        if set(groups[group]).intersection(TEAM_PERFORMANCE + TEAM_FLAGS):
            raise ValueError("Pure player groups cannot include team-performance inputs")
    if not set(groups["player_form"]).issubset(groups["player_squad"]):
        raise ValueError("player_squad must retain the player_form block")
    if set(groups["team_player_squad"]) != set(groups["team_control"]) | set(groups["player_squad"]):
        raise ValueError("Combined features must be exactly the team/player union")
    return groups


def _prepare(frame, feature_groups, *, historical=True):
    required = {"match_id", "match_date", "season"} | ({"result"} if historical else set())
    if not required.issubset(frame.columns):
        raise ValueError(f"Missing match identity columns: {sorted(required - set(frame.columns))}")
    native = frame.copy(deep=True)
    groups = _check_groups(native, feature_groups)
    if native.match_id.isna().any() or native.match_id.duplicated().any() or native.season.isna().any():
        raise ValueError("Match identities must be nonmissing and globally unique")
    native["match_date"] = pd.to_datetime(native.match_date, errors="raise", utc=True).dt.tz_convert(None).dt.normalize()
    if native.match_date.isna().any():
        raise ValueError("Match dates cannot be missing")
    years = native.season.astype(str).str.extract(r"^(\d{4})-\d{2}$", expand=False)
    if years.isna().any():
        raise ValueError("Use season labels YYYY-YY")
    for year, label in zip(years.astype(int), native.season.astype(str)):
        if label != season(year):
            raise ValueError("Invalid season identity")
    if not ((native.match_date.dt.year == years.astype(int)) | (native.match_date.dt.year == years.astype(int) + 1)).all():
        raise ValueError("Match date and season identity disagree")
    for column in sorted({column for columns in groups.values() for column in columns}):
        native[column] = pd.to_numeric(native[column], errors="raise").astype(float)
        if np.isinf(native[column].to_numpy()).any():
            raise ValueError("Infinite feature values are invalid; missing values may remain NaN")
    for column in ("audit_player_home_latest_source_date", "audit_player_away_latest_source_date",
                   "audit_player_home_xi_latest_source_date", "audit_player_away_xi_latest_source_date"):
        if column in native:
            latest = pd.to_datetime(native[column], errors="raise", utc=True).dt.tz_convert(None).dt.normalize()
            if (latest.notna() & latest.ge(native.match_date)).any():
                raise ValueError(f"Non-prior player evidence: {column}")
    return native.sort_values(["match_date", "match_id"]).reset_index(drop=True), groups


def _blocks(frame, roles):
    blocks, rows = {}, []
    previous = None
    used = set()
    for role, seasons in roles.items():
        block = frame.loc[frame.season.isin(seasons)].sort_values(["match_date", "match_id"]).reset_index(drop=True)
        if block.empty or set(block.result) != set(CLASSES):
            raise ValueError(f"Each chronological {role} block must contain all three outcomes")
        if previous is not None and block.match_date.min() <= previous:
            raise ValueError("Chronological train/tune/calibration/evaluation dates overlap")
        if used.intersection(block.match_id):
            raise ValueError("A fixture entered multiple chronological roles")
        used.update(block.match_id)
        previous = block.match_date.max()
        blocks[role] = block
        rows.append({"role": role, "seasons": ",".join(seasons), "n_matches": len(block),
                     "date_min": str(block.match_date.min().date()), "date_max": str(previous.date())})
    return blocks, rows


def _estimator(kind, parameter):
    if kind == "logistic":
        return make_pipeline(SimpleImputer(strategy="median", add_indicator=True, keep_empty_features=True),
                             StandardScaler(), LogisticRegression(C=parameter, solver="lbfgs", max_iter=2000, random_state=RANDOM_STATE))
    if kind == "hist_boost":
        return HistGradientBoostingClassifier(max_leaf_nodes=int(parameter), max_iter=150, learning_rate=0.05,
            min_samples_leaf=40, l2_regularization=10.0, early_stopping=False, categorical_features=None,
            random_state=RANDOM_STATE)
    raise ValueError(f"Unknown model family: {kind}")


def _fit_one(blocks, features, kind):
    grid = LOGIT_C_GRID if kind == "logistic" else BOOST_LEAF_GRID
    parameter_name = "C" if kind == "logistic" else "max_leaf_nodes"
    trials = []
    with threadpool_limits(limits=1):
        for parameter in grid:
            model = _estimator(kind, parameter).fit(blocks["train"][features], encode_results(blocks["train"].result))
            p = softmax(estimator_logits(model, blocks["tune"][features]), axis=1)
            score = classification_metrics(encode_results(blocks["tune"].result), p)
            trials.append({"parameter_name": parameter_name, "parameter_value": parameter, "n_features": len(features), **score})
        best = min(trials, key=lambda row: (row["log_loss"], row["parameter_value"]))
        refit = pd.concat([blocks["train"], blocks["tune"]], ignore_index=True)
        model = _estimator(kind, best["parameter_value"]).fit(refit[features], encode_results(refit.result))
        calibrator = TemperatureCalibrator().fit(estimator_logits(model, blocks["calibration"][features]), encode_results(blocks["calibration"].result))
    return model, calibrator, trials, best


def _bundle(model, calibrator, features, group, kind, roles, best, artifact):
    metadata = {"feature_group": group, "model_type": kind, "features": list(features),
        "parameter_name": best["parameter_name"], "parameter_value": best["parameter_value"],
        "temperature": float(calibrator.temperature), "tuning_log_loss": float(best["log_loss"]),
        "train_seasons": roles["train"], "tune_seasons": roles["tune"],
        "refit_seasons": roles["train"] + roles["tune"], "calibration_seasons": roles["calibration"],
        "classes": list(CLASSES), "n_features": len(features), "study_status": STUDY_STATUS,
        "artifact_path": str(artifact.resolve()), "artifact_name": artifact.name}
    joblib.dump({"model": model, "calibrator": calibrator, **metadata}, artifact)
    metadata["artifact_sha256"] = hashlib.sha256(artifact.read_bytes()).hexdigest()
    return metadata


def _predictions(block, model, calibrator, features, group, kind, outer_season):
    with threadpool_limits(limits=1):
        logits = estimator_logits(model, block[features])
    raw, calibrated = softmax(logits, axis=1), calibrator.predict_proba(logits)
    columns = [column for column in ("match_id", "match_date", "season", "result", "home_team", "away_team") if column in block]
    result = block[columns].copy()
    for k, outcome in enumerate(CLASSES):
        result[f"p_{outcome}"] = calibrated[:, k]
        result[f"p_raw_{outcome}"] = raw[:, k]
    result["outer_season"] = outer_season
    result["feature_group"], result["model_type"] = group, kind
    result["study_status"] = STUDY_STATUS
    return result


def _logit_coefficients(model, features, group, outer_season):
    if not hasattr(model, "named_steps"):
        return []
    names = model[0].get_feature_names_out(features)
    classifier = model[-1]
    rows = []
    for i, encoded_class in enumerate(classifier.classes_):
        for name, coefficient in zip(names, classifier.coef_[i]):
            rows.append({"outer_season": outer_season, "feature_group": group, "model_type": "logistic",
                         "outcome": CLASSES[int(encoded_class)], "transformed_feature": name,
                         "standardized_logit_coefficient": float(coefficient),
                         "interpretation": "conditional fitted association on train+tune; not a causal or raw-unit effect"})
        rows.append({"outer_season": outer_season, "feature_group": group, "model_type": "logistic",
                     "outcome": CLASSES[int(encoded_class)], "transformed_feature": "__intercept__",
                     "standardized_logit_coefficient": float(classifier.intercept_[i]),
                     "interpretation": "uncalibrated fitted multinomial intercept"})
    return rows


def _scores_and_pairs(predictions):
    seasonal, pooled, pairs = [], [], []
    labels = list(predictions.outer_season.unique()) + ["pooled"]
    for label in labels:
        part = predictions if label == "pooled" else predictions.loc[predictions.outer_season == label]
        for (group, kind), candidate in part.groupby(["feature_group", "model_type"], sort=False):
            metrics = classification_metrics(encode_results(candidate.result), candidate[["p_H", "p_D", "p_A"]])
            row = {"feature_group": group, "model_type": kind, "outer_season": label, **metrics, "study_status": STUDY_STATUS}
            (pooled if label == "pooled" else seasonal).append(row)
            if group != "team_control":
                reference = part.loc[(part.feature_group == "team_control") & (part.model_type == kind)]
                intervals = date_stratified_paired_intervals(candidate, reference, seed=RANDOM_STATE, n_bootstrap=1000)
                pairs.extend({**interval, "feature_group": group, "model_type": kind,
                    "reference_group": "team_control", "reference_model_type": kind, "outer_season": label,
                    "sample_scope": "all_common_quoted_fixtures", "inference_status": "descriptive_conditional_no_multiplicity_adjustment"} for interval in intervals)
    return pd.DataFrame(pooled), pd.DataFrame(seasonal), pd.DataFrame(pairs)


def train_rolling(frame, feature_groups, output_dir) -> dict:
    """Fit 32 frozen models, saving explicit chronology and all eight series."""
    native, groups = _prepare(frame, feature_groups)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    predictions, trials, fits, role_rows, coefficients = [], [], [], [], []
    artifacts = []
    for year in OUTER_YEARS:
        label, roles = season(year), fold_roles(year)
        blocks, rows = _blocks(native, roles)
        role_rows.extend({"outer_season": label, **row} for row in rows)
        for group in GROUPS:
            for kind in MODEL_TYPES:
                model, calibrator, tuning, best = _fit_one(blocks, groups[group], kind)
                trials.extend({"outer_season": label, "feature_group": group, "model_type": kind, **row} for row in tuning)
                artifact = output / f"model_{label}_{group}_{kind}.joblib"
                metadata = _bundle(model, calibrator, groups[group], group, kind, roles, best, artifact)
                metadata["outer_season"] = label
                artifacts.append(metadata)
                fits.append({key: value for key, value in metadata.items() if key not in ("features", "classes", "train_seasons", "tune_seasons", "refit_seasons", "calibration_seasons")})
                predictions.append(_predictions(blocks["evaluation"], model, calibrator, groups[group], group, kind, label))
                if kind == "logistic":
                    coefficients.extend(_logit_coefficients(model, groups[group], group, label))
    predictions = pd.concat(predictions, ignore_index=True)
    if predictions.duplicated(["match_id", "feature_group", "model_type"]).any():
        raise AssertionError("Duplicate rolling predictions")
    pooled, seasonal, pairs = _scores_and_pairs(predictions)
    tables = {"predictions": predictions, "model_metrics_pooled": pooled, "model_metrics_seasonal": seasonal,
              "paired_feature_comparisons": pairs, "tuning_trials": pd.DataFrame(trials),
              "fitted_choices": pd.DataFrame(fits), "chronological_roles": pd.DataFrame(role_rows),
              "logistic_coefficients": pd.DataFrame(coefficients)}
    for stem, table in tables.items():
        _save(table, output, stem)
    metadata = {"study_status": STUDY_STATUS, "n_models": len(artifacts), "n_tuning_trials": len(trials),
        "n_prediction_rows": len(predictions), "n_evaluation_matches": int(predictions.match_id.nunique()),
        "classes": list(CLASSES), "feature_groups": groups, "seed": RANDOM_STATE,
        "outer_years": list(OUTER_YEARS), "logit_C_grid": list(LOGIT_C_GRID), "hist_boost_leaf_grid": list(BOOST_LEAF_GRID),
        "hist_boost_fixed_parameters": {"max_iter": 150, "learning_rate": 0.05, "min_samples_leaf": 40,
                                        "l2_regularization": 10.0, "early_stopping": False},
        "paired_interval_status": "descriptive whole-date bootstrap within each outer season, 1000 draws; no multiplicity adjustment",
        "calibration": "temperature fit only on separate preceding season, after train+tune refit",
        "artifacts": artifacts}
    _write_json(output / "models_metadata.json", metadata)
    return {**tables, "models_metadata": metadata}


def fit_future(frame, feature_groups, output_dir) -> dict:
    """Fit eight bundles through 2024, calibrating on 2025; never fit 2026."""
    native, groups = _prepare(frame, feature_groups)
    roles = {"train": [season(year) for year in range(2016, 2024)], "tune": ["2024-25"], "calibration": ["2025-26"]}
    blocks, role_rows = _blocks(native, roles)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    artifacts, trials, coefficients = [], [], []
    for group in GROUPS:
        for kind in MODEL_TYPES:
            model, calibrator, tuning, best = _fit_one(blocks, groups[group], kind)
            artifact = output / f"future_{group}_{kind}.joblib"
            metadata = _bundle(model, calibrator, groups[group], group, kind, roles, best, artifact)
            artifacts.append(metadata)
            trials.extend({"feature_group": group, "model_type": kind, **row} for row in tuning)
            if kind == "logistic":
                coefficients.extend(_logit_coefficients(model, groups[group], group, "future_frozen_through_2025_26_calibration"))
    metadata = {"study_status": "new_player_model_forecast_candidates_not_existing_prospective_ledger", "n_models": len(artifacts),
        "n_tuning_trials": len(trials), "roles": roles, "chronological_roles": role_rows, "feature_groups": groups,
        "classes": list(CLASSES), "artifacts": artifacts,
        "latest_model_fit_date": max(row["date_max"] for row in role_rows if row["role"] in ("train", "tune")),
        "latest_calibration_date": max(row["date_max"] for row in role_rows if row["role"] == "calibration"),
        "outcomes_from_2026_27_used_for_fitting": False}
    _save(pd.DataFrame(trials), output, "future_tuning_trials")
    _save(pd.DataFrame(coefficients), output, "future_logistic_coefficients")
    _write_json(output / "future_models_metadata.json", metadata)
    return metadata


def predict_future(models_metadata, target_frame, *, artifact_root=None) -> pd.DataFrame:
    """Load hash-verified new-model bundles; do not alter any prospective ledger."""
    if not isinstance(models_metadata, dict) or models_metadata.get("n_models") != 8:
        raise ValueError("Eight declared future model bundles are required")
    native, groups = _prepare(target_frame, models_metadata["feature_groups"], historical=False)
    if not native.season.eq("2026-27").all():
        raise ValueError("Future candidates are restricted to 2026-27 targets")
    if native.match_date.le(pd.Timestamp(models_metadata["latest_calibration_date"])).any():
        raise ValueError("Targets must follow the frozen calibration period")
    artifacts = models_metadata.get("artifacts", [])
    if len(artifacts) != 8 or {(row["feature_group"], row["model_type"]) for row in artifacts} != {(group, kind) for group in GROUPS for kind in MODEL_TYPES}:
        raise ValueError("Future bundle identities are incomplete or duplicated")
    predictions = []
    for row in artifacts:
        if artifact_root is None:
            path = Path(row["artifact_path"])
        else:
            name = row.get("artifact_name")
            if not isinstance(name, str) or Path(name).name != name or name in ("", ".", ".."):
                raise ValueError("Future bundle requires a safe artifact_name for relocation")
            path = Path(artifact_root) / name
        if hashlib.sha256(path.read_bytes()).hexdigest() != row["artifact_sha256"]:
            raise ValueError("Frozen future bundle hash changed")
        bundle = joblib.load(path)
        group, kind = row["feature_group"], row["model_type"]
        if bundle["features"] != groups[group] or bundle["feature_group"] != group or bundle["model_type"] != kind or bundle["classes"] != list(CLASSES):
            raise ValueError("Future model metadata identity conflict")
        if any(label.startswith("2026") for label in bundle["refit_seasons"] + bundle["calibration_seasons"]):
            raise ValueError("Future model included 2026 fitting/calibration outcomes")
        predicted = _predictions(native, bundle["model"], bundle["calibrator"], groups[group], group, kind, "2026-27")
        predicted["study_status"] = models_metadata["study_status"]
        predicted["model_artifact_sha256"] = row["artifact_sha256"]
        predictions.append(predicted)
    return pd.concat(predictions, ignore_index=True)
