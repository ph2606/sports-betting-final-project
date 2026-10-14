"""Exploratory rolling-origin team/xG/player ablations; preserve the first study.

Run from repository root: python -m epl_modeling.ablation
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import time

import joblib
import numpy as np
import pandas as pd
from scipy.special import softmax
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .backtest import build_odds_panel, simulate_bets
from .experiment import save_table, write_json
from .fpl_reconciliation import build_reconciled_features, reconcile_fpl_opponents
from .market_residual import MarketResidualClassifier
from .metrics import CLASSES, TemperatureCalibrator, classification_metrics, encode_results, estimator_logits

ROOT = Path(__file__).resolve().parent
OUTER_YEARS = (2022, 2023, 2024, 2025)
C_GRID = (0.03, 0.3, 3.0)
TEAM_PERFORMANCE = [
    "feat_diff_std_goals_diff", "feat_diff_roll10_goals_diff",
    "feat_diff_std_shots_on_target_diff", "feat_diff_roll10_shots_on_target_diff",
    "feat_diff_std_corners_diff", "feat_diff_roll10_points",
    "feat_home_prior_season_win_pct", "feat_away_prior_season_win_pct", "feat_diff_rest_days",
]
TEAM_FLAGS = [f"feat_{side}_{field}" for side in ("home", "away")
              for field in ("prior_season_missing", "promoted_from_outside_epl")]
SOURCE_COVERAGE = [f"feat_{side}_{field}" for side in ("home", "away")
                   for field in ("us_roll10_observed_matches", "fpl_roll10_observed_matches",
                                 "us_history_missing", "fpl_history_missing")]
XG_PERFORMANCE = [f"feat_diff_{period}_us_xg_{direction}"
                  for period in ("std", "roll10") for direction in ("for", "against")]
PLAYER_PERFORMANCE = [f"feat_diff_roll10_fpl_{field}"
                      for field in ("total_points", "bps", "assists", "saves", "influence", "creativity", "threat")]
BASE_FEATURES = TEAM_PERFORMANCE + TEAM_FLAGS + SOURCE_COVERAGE
FEATURE_GROUPS = {
    "team": BASE_FEATURES,
    "team_xg": BASE_FEATURES + XG_PERFORMANCE,
    "team_player": BASE_FEATURES + PLAYER_PERFORMANCE,
    "combined": BASE_FEATURES + XG_PERFORMANCE + PLAYER_PERFORMANCE,
}


def season(year):
    return f"{year}-{str(year+1)[-2:]}"


def fold_roles(year):
    if year < 2022:
        raise ValueError("Outer year must leave at least four training seasons")
    return {"train": [season(y) for y in range(2016, year - 2)],
            "tune": [season(year - 2)], "calibration": [season(year - 1)],
            "evaluation": [season(year)]}


def complete_history_mask(frame):
    present = frame[TEAM_PERFORMANCE + XG_PERFORMANCE + PLAYER_PERFORMANCE].notna().all(axis=1)
    for side in ("home", "away"):
        for source in ("us", "fpl"):
            present &= frame[f"feat_{side}_{source}_roll10_observed_matches"].ge(8)
    return present


def get_market(frame):
    return frame[["ref_p_H", "ref_p_D", "ref_p_A"]].to_numpy(float)


def estimator(kind, C):
    if kind == "market_residual":
        return MarketResidualClassifier(C=C)
    if kind == "logistic":
        return make_pipeline(SimpleImputer(strategy="median", add_indicator=True, keep_empty_features=True),
                             StandardScaler(), LogisticRegression(C=C, max_iter=2000, random_state=42))
    raise ValueError(kind)


def fit_model(model, kind, frame, features):
    y = encode_results(frame.result)
    if kind == "market_residual":
        model.fit(frame[features], get_market(frame), y)
    else:
        model.fit(frame[features], y)
    return model


def logits(model, kind, frame, features):
    if kind == "market_residual":
        return model.decision_function(frame[features], get_market(frame))
    return estimator_logits(model, frame[features])


def prediction_table(frame, probabilities, group, kind, outer_season):
    result = frame[["match_id", "match_date", "season", "result", "complete_source_history"]].copy()
    for k, outcome in enumerate(CLASSES):
        result["p_" + outcome] = probabilities[:, k]
    result["feature_group"], result["model_type"], result["outer_season"] = group, kind, outer_season
    return result


def date_stratified_paired_intervals(candidate, reference, *, seed=42, n_bootstrap=1000):
    """Paired proper-score differences; sample complete dates within each season."""
    keys = ["outer_season", "match_id"]
    joined = candidate.merge(reference, on=keys, validate="one_to_one", suffixes=("", "_reference"))
    if len(joined) != len(candidate) or len(joined) != len(reference):
        raise ValueError("Paired predictions must have identical fixture populations")
    if not joined.result.equals(joined.result_reference) or not joined.match_date.equals(joined.match_date_reference):
        raise ValueError("Paired settlement/date identities disagree")
    y = encode_results(joined.result)
    a = joined[["p_H", "p_D", "p_A"]].to_numpy(float)
    b = joined[["p_H_reference", "p_D_reference", "p_A_reference"]].to_numpy(float)
    target = np.eye(3)[y]
    differences = np.column_stack([
        -np.log(np.clip(a[np.arange(len(y)), y], 1e-12, 1)) + np.log(np.clip(b[np.arange(len(y)), y], 1e-12, 1)),
        np.sum((a-target)**2, axis=1) - np.sum((b-target)**2, axis=1),
        (a.argmax(axis=1) == y).astype(float) - (b.argmax(axis=1) == y).astype(float),
    ])
    values = pd.DataFrame(differences, columns=["log_loss", "brier_score", "accuracy"])
    values["outer_season"], values["match_date"], values["count"] = joined.outer_season.to_numpy(), joined.match_date.to_numpy(), 1
    by_date = values.groupby(["outer_season", "match_date"], sort=True).sum()
    rng = np.random.default_rng(seed)
    boot_totals = np.zeros((n_bootstrap, 3))
    boot_counts = np.zeros(n_bootstrap)
    for _, group in by_date.groupby(level=0, sort=True):
        sampled = rng.integers(0, len(group), size=(n_bootstrap, len(group)))
        boot_totals += group[["log_loss", "brier_score", "accuracy"]].to_numpy()[sampled].sum(axis=1)
        boot_counts += group["count"].to_numpy()[sampled].sum(axis=1)
    scores = boot_totals / boot_counts[:, None]
    return [{"metric": metric, "difference": float(differences[:, k].mean()),
             "ci_lower": float(np.quantile(scores[:, k], 0.025)), "ci_upper": float(np.quantile(scores[:, k], 0.975)),
             "n_matches": len(joined), "n_bootstrap": n_bootstrap, "ci_level": 0.95,
             "bootstrap_unit": "whole_match_date_stratified_by_outer_season"}
            for k, metric in enumerate(["log_loss", "brier_score", "accuracy"])]


def summarize_predictions(predictions, *, seed):
    scores, pairs, exclusions = [], [], []
    variants = list(predictions[["feature_group", "model_type"]].drop_duplicates().itertuples(index=False, name=None))
    for outer_season in sorted(predictions.outer_season.unique()) + ["pooled"]:
        population = predictions if outer_season == "pooled" else predictions.loc[predictions.outer_season.eq(outer_season)]
        for scope in ("common_odds_matches", "complete_source_history"):
            part = population if scope == "common_odds_matches" else population.loc[population.complete_source_history]
            for group, kind in variants:
                one = part.loc[part.feature_group.eq(group) & part.model_type.eq(kind)]
                if len(one) < 30 or one.result.nunique() < 3:
                    exclusions.append({"outer_season": outer_season, "scope": scope,
                                       "feature_group": group, "model_type": kind,
                                       "n_matches": len(one), "n_outcome_classes": one.result.nunique(),
                                       "reason": "fewer_than_30_matches_or_missing_outcome_class"})
                    continue
                metrics = classification_metrics(encode_results(one.result), one[["p_H", "p_D", "p_A"]])
                scores.append({"outer_season": outer_season, "scope": scope, "feature_group": group,
                               "model_type": kind, **metrics})
                references = [("market_only", "baseline")]
                if kind in ("logistic", "market_residual") and group != "team":
                    references.append(("team", kind))
                if kind == "market_residual":
                    references.append(("market_only", "market_temperature"))
                for ref_group, ref_kind in references:
                    if (group, kind) == (ref_group, ref_kind):
                        continue
                    reference = part.loc[part.feature_group.eq(ref_group) & part.model_type.eq(ref_kind)]
                    intervals = date_stratified_paired_intervals(one, reference, seed=seed)
                    pairs.extend([{**row, "outer_season": outer_season, "scope": scope,
                                   "feature_group": group, "model_type": kind,
                                   "reference_group": ref_group, "reference_model_type": ref_kind}
                                  for row in intervals])
    exclusion_columns = ["outer_season", "scope", "feature_group", "model_type", "n_matches", "n_outcome_classes", "reason"]
    return pd.DataFrame(scores), pd.DataFrame(pairs), pd.DataFrame(exclusions, columns=exclusion_columns)


def snapshot_preservation():
    paths = [p for p in (ROOT / "results").glob("*") if p.is_file()]
    paths += [ROOT / "02_epl_modeling_results.ipynb", ROOT / "features.py", ROOT / "experiment.py",
              ROOT / "metrics.py", ROOT / "selection.py", ROOT / "reporting.py", ROOT / "backtest.py"]
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def run(args):
    started = time.perf_counter()
    output = Path(args.output).resolve()
    if output == (ROOT / "results").resolve() or (ROOT / "results").resolve() in output.parents:
        raise ValueError("The first experiment's results directory is immutable for this runner")
    output.mkdir(parents=True, exist_ok=True)
    preserved = snapshot_preservation()
    protocol_path = ROOT / "ABLATION_PROTOCOL.md"
    if not protocol_path.exists():
        raise FileNotFoundError("Save the explicit ablation protocol before fitting models")
    protocol_sha = hashlib.sha256(protocol_path.read_bytes()).hexdigest()
    write_json(output / "protocol_lock.json", {"sha256": protocol_sha, "locked_before_model_fitting": True,
                                              "outer_years": OUTER_YEARS, "C_grid": C_GRID,
                                              "feature_groups": FEATURE_GROUPS})
    data_root = Path(args.data_root).resolve()
    print("Reconciling FPL identities and building the separate feature frame", flush=True)
    reconciliation = reconcile_fpl_opponents(data_root)
    _, reconciliation_audit, reconciliation_metadata = reconciliation
    frame, feature_metadata = build_reconciled_features(data_root, reconciliation=reconciliation)
    frame["match_date"] = pd.to_datetime(frame.match_date).dt.normalize()
    frame["feat_diff_rest_days"] = frame.feat_home_rest_days - frame.feat_away_rest_days
    frame = frame.loc[frame.season.ge("2016-17") & frame.result.isin(CLASSES)].copy()
    missing = sorted(set(FEATURE_GROUPS["combined"]) - set(frame))
    if missing:
        raise ValueError("Predeclared features unavailable: " + str(missing))
    frame["complete_source_history"] = complete_history_mask(frame)
    odds, odds_audit = build_odds_panel(data_root, snapshot="preclosing", require_reference=True)
    odds["match_date"] = pd.to_datetime(odds.match_date).dt.normalize()
    native_dates = odds.set_index("match_id").match_date
    matched = frame.match_id.isin(native_dates.index)
    if not frame.loc[matched, "match_date"].eq(frame.loc[matched, "match_id"].map(native_dates)).all():
        raise ValueError("Feature and odds dates disagree")
    frame = frame.merge(odds[["match_id", "ref_p_H", "ref_p_D", "ref_p_A"]], on="match_id", validate="one_to_one")
    save_table(frame, output, "modeling_matches")
    save_table(reconciliation_audit, output, "fpl_identity_reconciliation")
    write_json(output / "source_reconciliation_summary.json", reconciliation_metadata)
    write_json(output / "feature_metadata.json", feature_metadata)
    write_json(output / "feature_groups.json", FEATURE_GROUPS)
    write_json(output / "odds_audit.json", odds_audit)
    roles, trials, fits, predictions = [], [], [], []
    for year in OUTER_YEARS:
        label = season(year)
        split = fold_roles(year)
        blocks = {role: frame.loc[frame.season.isin(seasons)].sort_values(["match_date", "match_id"]).reset_index(drop=True)
                  for role, seasons in split.items()}
        previous = None
        for role, one in blocks.items():
            if one.empty or one.result.nunique() != 3:
                raise ValueError("Insufficient chronological training/evaluation block")
            if previous is not None and one.match_date.min() <= previous:
                raise ValueError("Rolling-origin fold dates overlap")
            previous = one.match_date.max()
            roles.append({"outer_season": label, "role": role, "seasons": ",".join(split[role]),
                          "n_matches": len(one), "date_min": one.match_date.min(), "date_max": one.match_date.max(),
                          "complete_history_matches": int(one.complete_source_history.sum())})
        refit = pd.concat([blocks["train"], blocks["tune"]], ignore_index=True)
        calibration, evaluation = blocks["calibration"], blocks["evaluation"]
        print("Outer season " + label, flush=True)
        for group, features in FEATURE_GROUPS.items():
            for kind in ("logistic", "market_residual"):
                values = []
                for C in C_GRID:
                    model = fit_model(estimator(kind, C), kind, blocks["train"], features)
                    p = softmax(logits(model, kind, blocks["tune"], features), axis=1)
                    metrics = classification_metrics(encode_results(blocks["tune"].result), p)
                    values.append((metrics["log_loss"], C))
                    trials.append({"outer_season": label, "feature_group": group, "model_type": kind,
                                   "C": C, "n_features": len(features), **metrics})
                _, best_C = sorted(values)[0]
                model = fit_model(estimator(kind, best_C), kind, refit, features)
                calibrator = TemperatureCalibrator().fit(logits(model, kind, calibration, features), encode_results(calibration.result))
                p = calibrator.predict_proba(logits(model, kind, evaluation, features))
                predictions.append(prediction_table(evaluation, p, group, kind, label))
                fits.append({"outer_season": label, "feature_group": group, "model_type": kind,
                             "C": best_C, "temperature": calibrator.temperature, "n_features": len(features),
                             "fit_seasons": ",".join(split["train"] + split["tune"]),
                             "calibration_season": split["calibration"][0]})
                joblib.dump({"model": model, "calibrator": calibrator, "features": features,
                             "outer_season": label, "model_type": kind, "feature_group": group,
                             "classes": CLASSES, "study_status": "exploratory_retrospective"},
                            output / f"model_{label}_{kind}_{group}.joblib")
        raw_market = get_market(evaluation)
        market_calibrator = TemperatureCalibrator().fit(np.log(get_market(calibration)), encode_results(calibration.result))
        calibrated_market = market_calibrator.predict_proba(np.log(raw_market))
        prior = np.bincount(encode_results(refit.result), minlength=3) / len(refit)
        predictions.extend([
            prediction_table(evaluation, raw_market, "market_only", "baseline", label),
            prediction_table(evaluation, calibrated_market, "market_only", "market_temperature", label),
            prediction_table(evaluation, np.tile(prior, (len(evaluation), 1)), "class_frequency", "baseline", label),
        ])
        fits.append({"outer_season": label, "feature_group": "market_only", "model_type": "market_temperature",
                     "C": None, "temperature": market_calibrator.temperature, "n_features": 0,
                     "fit_seasons": "", "calibration_season": split["calibration"][0]})
    predictions = pd.concat(predictions, ignore_index=True)
    print("Scoring fixed feature groups and paired date-bootstrap comparisons", flush=True)
    scores, comparisons, exclusions = summarize_predictions(predictions, seed=args.seed)
    save_table(predictions, output, "predictions")
    save_table(scores, output, "classification_scores")
    save_table(comparisons, output, "paired_comparisons")
    save_table(exclusions, output, "metric_exclusion_audit")
    save_table(pd.DataFrame(roles), output, "chronological_roles")
    save_table(pd.DataFrame(trials), output, "tuning_trials")
    save_table(pd.DataFrame(fits), output, "fitted_choices")
    betting = []
    ledgers = []
    for keys, one in predictions.groupby(["outer_season", "feature_group", "model_type"], sort=False):
        outer_season, group, kind = keys
        for staking in ("fixed", "kelly"):
            bets, _, summary = simulate_bets(one, odds, threshold=0.05, staking=staking, bootstrap_samples=0, random_state=args.seed)
            labels = {"outer_season": outer_season, "feature_group": group, "model_type": kind,
                      "policy": "predeclared_5pct", "odds_mode": "best_individual_book", "staking": staking}
            betting.append({**summary, **labels})
            for key, value in labels.items():
                bets[key] = value
            ledgers.append(bets)
    save_table(pd.DataFrame(betting), output, "betting_summary")
    nonempty_ledgers = [p for p in ledgers if len(p)]
    save_table(pd.concat(nonempty_ledgers, ignore_index=True) if nonempty_ledgers else ledgers[0].copy(), output, "bets")
    if preserved != snapshot_preservation():
        raise AssertionError("First-experiment artifacts changed")
    if hashlib.sha256(protocol_path.read_bytes()).hexdigest() != protocol_sha:
        raise AssertionError("Ablation protocol changed after model fitting began")
    write_json(output / "first_experiment_integrity.json", {"preserved": True, "sha256": preserved})
    metadata = {"study_status": "exploratory_retrospective_not_a_fresh_holdout",
                "run_date": "2026-10-13", "data_snapshot_as_of": "2026-10-06", "seed": args.seed,
                "cohort": "20 current 2026/27 clubs; target fixtures have at least one eligible club",
                "seasons": [season(y) for y in OUTER_YEARS], "C_grid": C_GRID,
                "feature_groups": FEATURE_GROUPS, "feature_group_counts": {k: len(v) for k, v in FEATURE_GROUPS.items()},
                "folds": {season(y): fold_roles(y) for y in OUTER_YEARS}, "n_models": 32,
                "n_tuning_trials": len(trials), "first_experiment_preserved": True,
                "common_sample_matches": int(predictions[["outer_season", "match_id"]].drop_duplicates().shape[0]),
                "complete_source_history_definition": "Evaluation subset only: both clubs have >=8 observed xG and FPL slots in prior10 E0 matches; all fixed performance inputs nonmissing",
                "bootstrap": "1000 whole-calendar-date draws per season; pooled comparisons stratified by season; descriptive conditional intervals, no multiplicity adjustment",
                "publication_and_price_clocks_verified": False, "executable_arbitrage_claimed": False,
                "excluded_metric_blocks": len(exclusions), "frozen_protocol_sha256": protocol_sha,
                "source_sha256": {str(p.relative_to(ROOT.parent)): hashlib.sha256(p.read_bytes()).hexdigest()
                                  for p in sorted(ROOT.glob("*.py"))},
                "duration_seconds": time.perf_counter() - started,
                "limitations": ["2025/26 outcomes were inspected in the earlier study; this is exploratory historical research",
                                "All feature groups share source-coverage flags; team group is not independent of source availability metadata",
                                "FPL aggregates summarize earlier contributions, not prospectively known player availability",
                                "Current-club survivor bias, incomplete noncohort player histories, archival revisions and unverified quote clocks remain",
                                "Betting rules are fixed exploratory summaries, not freshly validated production policies"]}
    write_json(output / "run_metadata.json", metadata)
    from .ablation_reporting import build_ablation_report
    build_ablation_report(output)
    print(f"Ablation experiment completed in {time.perf_counter()-started:.1f} seconds", flush=True)
    return metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", default=str(ROOT.parent / "epl_data"))
    parser.add_argument("--output", default=str(ROOT / "ablation_results"))
    parser.add_argument("--seed", type=int, default=42)
    run(parser.parse_args())


if __name__ == "__main__":
    main()
