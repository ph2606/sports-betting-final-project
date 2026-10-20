"""Score the fixed first prospective release without promoting a winner.

Inputs are primitive records returned by the verified ledger readers. This
module does not authenticate ledger hashes, append records, fetch outcomes or
release forecasts. Four predictions for one fixture remain one shared outcome.
"""
from __future__ import annotations

from collections.abc import Mapping
from itertools import combinations
from statistics import NormalDist

import numpy as np
import pandas as pd

from epl_modeling.metrics import classification_metrics, encode_results


CLASSES = ("H", "D", "A")
BOOTSTRAP_SAMPLES = 9999
BOOTSTRAP_SEED = 20261020
CONFIDENCE_LEVEL = .95
SCORE_KEYS = ("accuracy", "log_loss", "brier_score", "classwise_ece_5", "classwise_ece_10", "classwise_ece_15")
INTERPRETATION = (
    "Descriptive first-release scores on shared resolved fixtures; the sample is tiny, "
    "intervals are not multiplicity-adjusted and no model is selected or promoted. "
    "Four model predictions of one result are not four independent fixtures."
)


def _text(record, field, label):
    value = record.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} requires a nonempty {field}")
    return value


def _utc(value, field):
    try:
        timestamp = pd.Timestamp(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"Invalid {field}") from error
    if pd.isna(timestamp) or timestamp.tzinfo is None:
        raise ValueError(f"{field} must be an explicit timezone-aware UTC timestamp")
    if timestamp.utcoffset().total_seconds() != 0:
        raise ValueError(f"{field} must use UTC")
    return timestamp.tz_convert("UTC")


def _identity(record, label):
    identity = tuple(_text(record, field, label) for field in ("season", "home_team", "away_team"))
    if identity[0] != "2026-27" or identity[1] == identity[2]:
        raise ValueError(f"{label} has an invalid original-season fixture identity")
    kickoff = _utc(record.get("kickoff_utc"), f"{label}.kickoff_utc")
    return (*identity, kickoff)


def _probabilities(record):
    values = record.get("probabilities")
    if not isinstance(values, Mapping) or set(values) != set(CLASSES):
        raise ValueError("Original forecast probabilities must contain exactly H/D/A")
    if any(isinstance(values[key], (bool, np.bool_)) for key in CLASSES):
        raise ValueError("Probabilities must be numeric values, not booleans")
    try:
        p = np.array([values[key] for key in CLASSES], dtype=np.float64)
    except (TypeError, ValueError) as error:
        raise ValueError("Original forecast probabilities must be numeric") from error
    if not np.isfinite(p).all() or (p < 0).any() or (p > 1).any() or not np.isclose(p.sum(), 1, atol=1e-10, rtol=0):
        raise ValueError("Original forecast probabilities must be finite, normalized and in [0,1]")
    return p


def wilson_accuracy_interval(correct: int, count: int) -> tuple[float, float]:
    """A two-sided 95% Wilson interval using the number of distinct fixtures."""
    if isinstance(correct, bool) or isinstance(count, bool) or not isinstance(correct, (int, np.integer)) or not isinstance(count, (int, np.integer)) or count < 0 or not 0 <= correct <= count:
        raise ValueError("Wilson interval requires integer successes and fixture count")
    if count == 0:
        return np.nan, np.nan
    z = NormalDist().inv_cdf(.975)
    p, z2 = correct / count, z * z
    center = (p + z2 / (2 * count)) / (1 + z2 / count)
    half = z * np.sqrt(p * (1 - p) / count + z2 / (4 * count * count)) / (1 + z2 / count)
    return float(max(0., center - half)), float(min(1., center + half))


def _interval(values, indices):
    if len(values) == 0:
        return np.nan, np.nan
    means = np.asarray(values, dtype=float)[indices].mean(axis=1)
    bounds = np.quantile(means, [.025, .975], method="linear")
    return float(bounds[0]), float(bounds[1])


def _select_original(forecasts, match_ids, model_ids):
    selected, versions = {}, set()
    for record in forecasts:
        if not isinstance(record, Mapping):
            raise ValueError("Forecast records must be mappings")
        if record.get("match_id") not in match_ids or record.get("model_id") not in model_ids:
            continue
        version = record.get("update_version", 1)
        if isinstance(version, bool) or not isinstance(version, (int, np.integer)) or version < 1:
            raise ValueError("Forecast update_version must be a positive integer")
        key = (record["model_id"], record["match_id"])
        full_key = (*key, int(version))
        if full_key in versions:
            raise ValueError("Duplicate original forecast model/fixture/version identity")
        versions.add(full_key)
        if version == 1:
            selected[key] = record
    expected = {(model_id, match_id) for model_id in model_ids for match_id in match_ids}
    if set(selected) != expected:
        raise ValueError("The mandatory original 4-by-10 version-1 forecast grid is incomplete")
    return selected


def build_analysis(forecasts: list[dict], outcomes: list[dict], *, original_match_ids: set[str],
                   original_model_ids: set[str]) -> dict[str, pd.DataFrame]:
    """Return four auditable tables for the original four-by-ten release only.

    Every original model/fixture pair must retain its version-1 record. Later
    versions and forecasts outside the supplied fixed cohort never change its
    scores. Outcomes may be pending. Model and pairwise scores use the same
    intersection of resolved original fixtures, sorted by native match ID; the
    9,999 bootstrap draws resample fixture indices jointly for all four models.
    """
    match_ids, model_ids = set(original_match_ids), set(original_model_ids)
    if len(match_ids) != 10 or len(model_ids) != 4 or any(not isinstance(value, str) or not value.strip() for value in match_ids | model_ids):
        raise ValueError("The first release requires exactly ten match IDs and four model IDs")
    selected = _select_original(forecasts, match_ids, model_ids)
    identities, validated = {}, {}
    for (model_id, match_id), record in sorted(selected.items()):
        identity = _identity(record, "Original forecast")
        if match_id in identities and identities[match_id] != identity:
            raise ValueError("Original models disagree on the native fixture identity or kickoff")
        identities[match_id] = identity
        created = _utc(record.get("created_at_utc"), "created_at_utc")
        if not created < identity[3]:
            raise ValueError("Forecast creation must be strictly before the original kickoff")
        target_date = record.get("target_match_date")
        if target_date is not None and target_date != identity[3].strftime("%Y-%m-%d"):
            raise ValueError("Target match date conflicts with the original UTC kickoff")
        if record.get("protocol_committed_at_utc") is not None and _utc(record["protocol_committed_at_utc"], "protocol_committed_at_utc") > created:
            raise ValueError("Protocol commitment follows forecast creation")
        for source in record.get("source_snapshots", []):
            if not isinstance(source, Mapping) or _utc(source.get("observed_at_utc"), "source observation") > created:
                raise ValueError("A forecast source observation follows its creation")
        feature_dates = record.get("latest_feature_match_dates", {})
        if not isinstance(feature_dates, Mapping):
            raise ValueError("Latest feature match dates must be a mapping")
        for value in feature_dates.values():
            if value is not None and (pd.isna(pd.Timestamp(value)) or pd.Timestamp(value).date() >= identity[3].date()):
                raise ValueError("A feature match date is not strictly before the target date")
        if record.get("fpl_fixture_id") is not None and match_id.startswith("fpl_2026-27_"):
            if str(record["fpl_fixture_id"]) != match_id.removeprefix("fpl_2026-27_"):
                raise ValueError("FPL fixture ID conflicts with its native match ID")
        validated[(model_id, match_id)] = (record, identity, created, _probabilities(record))
    settlements = {}
    for outcome in outcomes:
        if not isinstance(outcome, Mapping):
            raise ValueError("Outcome records must be mappings")
        match_id = outcome.get("match_id")
        if match_id not in match_ids:
            continue
        if match_id in settlements:
            raise ValueError("Duplicate original outcome match identity")
        identity = _identity(outcome, "Observed outcome")
        if identity != identities[match_id]:
            raise ValueError("Observed outcome conflicts with the original native fixture identity or kickoff")
        observed = _utc(outcome.get("settled_at_utc"), "settled_at_utc")
        if observed < identity[3]:
            raise ValueError("Observed outcome precedes its original kickoff")
        goals = [outcome.get("home_goals"), outcome.get("away_goals")]
        if any(isinstance(goal, (bool, np.bool_)) or not isinstance(goal, (int, np.integer)) or goal < 0 for goal in goals):
            raise ValueError("Observed outcomes require both nonnegative integer goal counts")
        actual = "H" if goals[0] > goals[1] else "A" if goals[1] > goals[0] else "D"
        if outcome.get("result") != actual:
            raise ValueError("Observed result conflicts with the supplied goals")
        settlements[match_id] = (outcome, observed, actual)
    common_ids = sorted(settlements)
    # Reconcile the intersection explicitly even though a complete first-release
    # grid is mandatory: future extensions cannot silently score unequal sets.
    resolved_by_model = {model: {match for candidate_model, match in validated if candidate_model == model and match in settlements}
                         for model in model_ids}
    intersection = set.intersection(*(resolved_by_model[model] for model in sorted(model_ids)))
    if intersection != set(common_ids):
        raise ValueError("Original model resolved-fixture populations do not reconcile")
    rows = []
    eps = np.finfo(np.float64).eps
    for (model_id, match_id), (record, identity, created, p) in sorted(validated.items()):
        settled = settlements.get(match_id)
        predicted = CLASSES[int(p.argmax())]
        outcome, observed, actual = settled if settled is not None else ({}, pd.NaT, None)
        if actual is not None:
            y = CLASSES.index(actual)
            loss = float(-np.log(np.clip(p[y], eps, 1 - eps)))
            brier = float(np.square(p - np.eye(3)[y]).sum())
        else:
            loss, brier = np.nan, np.nan
        rows.append({"model_id": model_id, "match_id": match_id, "season": identity[0],
            "home_team": identity[1], "away_team": identity[2], "kickoff_utc": identity[3],
            "created_at_utc": created, "target_match_date": identity[3].strftime("%Y-%m-%d"),
            "feature_group": record.get("feature_group"), "forecast_type": record.get("forecast_type"),
            "fpl_fixture_id": record.get("fpl_fixture_id"), "model_sha256": record.get("model_sha256"),
            "code_sha256": record.get("code_sha256"), "protocol_sha256": record.get("protocol_sha256"),
            "forecast_snapshot_id": record.get("snapshot_id"), "forecast_update_version": 1,
            **{f"p_{label}": float(p[index]) for index, label in enumerate(CLASSES)},
            "predicted_outcome": predicted, "actual_result": actual,
            "home_goals": outcome.get("home_goals"), "away_goals": outcome.get("away_goals"),
            "outcome_observed_at_utc": observed, "outcome_snapshot_id": outcome.get("snapshot_id"),
            "outcome_observation_semantics": outcome.get("settlement_time_semantics", "UTC result-observation time, not inferred final-whistle time"),
            "status": "settled" if settled is not None else "pending",
            "correct": int(predicted == actual) if actual is not None else np.nan,
            "log_loss": loss, "brier_score": brier, "in_common_scored_population": match_id in intersection,
            "forecast_created_before_kickoff": True, "first_release_only": True,
            "ledger_hash_authentication_performed_here": False})
    audit = pd.DataFrame(rows).sort_values(["kickoff_utc", "match_id", "model_id"], kind="stable").reset_index(drop=True)
    indices = np.random.default_rng(BOOTSTRAP_SEED).integers(0, len(common_ids), size=(BOOTSTRAP_SAMPLES, len(common_ids))) if common_ids else np.empty((0, 0), dtype=int)
    model_rows, vectors = [], {}
    for model in sorted(model_ids):
        whole = audit.loc[audit.model_id.eq(model)]
        scored = whole.loc[whole.in_common_scored_population].set_index("match_id").reindex(common_ids)
        if len(scored):
            metrics = classification_metrics(encode_results(scored.actual_result), scored[["p_H", "p_D", "p_A"]].to_numpy(float))
            low, high = wilson_accuracy_interval(int(scored.correct.sum()), len(scored))
            # Keep individual losses and the frozen aggregate definition aligned.
            if not np.isclose(metrics["log_loss"], scored.log_loss.mean(), atol=1e-12, rtol=0):
                raise ValueError("Per-fixture and frozen aggregate log loss disagree")
        else:
            metrics = {"n_matches": 0, **{name: np.nan for name in SCORE_KEYS}}
            low, high = np.nan, np.nan
        vector = {"accuracy": scored.correct.to_numpy(float), "log_loss": scored.log_loss.to_numpy(float), "brier_score": scored.brier_score.to_numpy(float)}
        vectors[model] = vector
        ll_low, ll_high = _interval(vector["log_loss"], indices)
        brier_low, brier_high = _interval(vector["brier_score"], indices)
        groups = whole.feature_group.dropna().unique()
        if len(groups) > 1:
            raise ValueError("One original model ID has conflicting feature-group identities")
        model_rows.append({"model_id": model, "feature_group": groups[0] if len(groups) else None,
            "scope": "original_first_release_common_resolved_fixtures", "forecast_count": len(whole),
            "original_fixture_count": len(match_ids), "settled_count": int(whole.status.eq("settled").sum()),
            "pending_count": int(whole.status.eq("pending").sum()),
            "common_settled_fixture_count": len(common_ids), **metrics,
            "accuracy_ci_low": low, "accuracy_ci_high": high,
            "accuracy_interval_method": "95% Wilson score interval over distinct fixtures",
            "log_loss_ci_low": ll_low, "log_loss_ci_high": ll_high,
            "brier_score_ci_low": brier_low, "brier_score_ci_high": brier_high,
            "bootstrap_samples": BOOTSTRAP_SAMPLES, "bootstrap_valid_samples": BOOTSTRAP_SAMPLES if len(scored) else 0,
            "bootstrap_seed": BOOTSTRAP_SEED, "confidence_level": CONFIDENCE_LEVEL,
            "bootstrap_unit": "one shared fixture outcome; the same resample indices are used for every model",
            "loss_interval_method": "two-sided percentile bootstrap of per-fixture mean losses; linear quantiles",
            "independent_fixture_count": len(scored), "no_selected_winner": True,
            "not_multiplicity_adjusted": True, "interpretation": INTERPRETATION})
    pair_rows = []
    for model_a, model_b in combinations(sorted(model_ids), 2):
        row = {"model_a": model_a, "model_b": model_b, "scope": "original_first_release_common_resolved_fixtures",
            "common_fixture_count": len(common_ids), "difference_direction": "model_a_minus_model_b",
            "bootstrap_samples": BOOTSTRAP_SAMPLES, "bootstrap_valid_samples": BOOTSTRAP_SAMPLES if common_ids else 0,
            "bootstrap_seed": BOOTSTRAP_SEED, "confidence_level": CONFIDENCE_LEVEL,
            "bootstrap_unit": "paired shared fixture; same indices for both models and all six pairs",
            "interval_method": "two-sided percentile bootstrap of paired per-fixture score differences; linear quantiles",
            "not_multiplicity_adjusted": True, "no_selected_winner": True, "interpretation": INTERPRETATION}
        for name in ("accuracy", "log_loss", "brier_score"):
            differences = vectors[model_a][name] - vectors[model_b][name]
            low, high = _interval(differences, indices)
            row[name + "_diff"] = float(differences.mean()) if len(differences) else np.nan
            row[name + "_diff_ci_low"], row[name + "_diff_ci_high"] = low, high
        pair_rows.append(row)
    fixture_rows = []
    for match_id in sorted(match_ids):
        identity, settled = identities[match_id], settlements.get(match_id)
        outcome, observed, actual = settled if settled is not None else ({}, pd.NaT, None)
        fixture_rows.append({"match_id": match_id, "season": identity[0], "home_team": identity[1],
            "away_team": identity[2], "kickoff_utc": identity[3], "actual_result": actual,
            "home_goals": outcome.get("home_goals"), "away_goals": outcome.get("away_goals"),
            "outcome_observed_at_utc": observed, "outcome_snapshot_id": outcome.get("snapshot_id"),
            "status": "settled" if settled is not None else "pending", "model_forecast_count": len(model_ids),
            "model_scored_count": len(model_ids) if settled is not None else 0,
            "all_models_forecasted": True, "in_common_scored_population": match_id in intersection,
            "independent_fixture_count": 1})
    fixture_frame = pd.DataFrame(fixture_rows).sort_values(["kickoff_utc", "match_id"], kind="stable").reset_index(drop=True)
    return {"forecast_outcome_audit": audit, "model_scores": pd.DataFrame(model_rows),
            "pairwise_scores": pd.DataFrame(pair_rows), "fixture_outcomes": fixture_frame}
