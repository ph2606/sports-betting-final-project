"""Run the initial EPL accuracy-versus-calibration study from the saved snapshot.

From the repository root: python -m epl_modeling.experiment --trials 12
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import time
import warnings

import joblib
import numpy as np
import optuna
import pandas as pd
from scipy.special import softmax
from sklearn.ensemble import RandomForestClassifier
from sklearn.exceptions import ConvergenceWarning
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

from .backtest import build_odds_panel, simulate_bets
from .features import build_features
from .metrics import CLASSES, TemperatureCalibrator, classification_metrics, encode_results, estimator_logits, reliability_bins
from .selection import filter_features, forward_select

ROOT = Path(__file__).resolve().parent
SPLITS = {
    "train": [f"{y}-{str(y+1)[-2:]}" for y in range(2014, 2021)],
    "tune": ["2021-22"], "calibration": ["2022-23"],
    "model_selection": ["2023-24"], "strategy_validation": ["2024-25"],
    "test": ["2025-26"], "monitoring": ["2026-27"],
}
FAMILIES = ("logistic_regression", "random_forest", "svm", "mlp")
THRESHOLDS = (0, 0.025, 0.05, 0.075, 0.10, 0.15, 0.20)


def json_default(value):
    if isinstance(value, (np.integer, np.floating)):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (pd.Timestamp, Path)):
        return str(value)
    raise TypeError(type(value).__name__)


def write_json(path, value):
    # Convert non-finite scalar results into portable JSON nulls.
    def sanitize(item):
        if isinstance(item, dict):
            return {str(k): sanitize(v) for k, v in item.items()}
        if isinstance(item, (list, tuple)):
            return [sanitize(v) for v in item]
        if isinstance(item, (float, np.floating)) and not np.isfinite(item):
            return None
        return item
    path.write_text(json.dumps(sanitize(value), indent=2, default=json_default, allow_nan=False) + "\n", encoding="utf-8")


def save_table(frame, output, name):
    frame.to_csv(output / (name + ".csv"), index=False)
    frame.to_parquet(output / (name + ".parquet"), index=False)


def trial_parameters(trial, family):
    if family == "logistic_regression":
        return {"C": trial.suggest_float("C", 0.001, 30, log=True)}
    if family == "random_forest":
        return {"max_depth": trial.suggest_categorical("max_depth", [3, 5, 8, None]),
                "min_samples_leaf": trial.suggest_int("min_samples_leaf", 5, 40),
                "max_features": trial.suggest_float("max_features", 0.5, 1.0)}
    if family == "svm":
        return {"C": trial.suggest_float("C", 0.03, 30, log=True),
                "gamma": trial.suggest_float("gamma", 0.001, 0.3, log=True)}
    if family == "mlp":
        return {"hidden_units": trial.suggest_categorical("hidden_units", [8, 16, 32, 64]),
                "alpha": trial.suggest_float("alpha", 0.0001, 1, log=True),
                "learning_rate_init": trial.suggest_float("learning_rate_init", 0.0003, 0.01, log=True)}
    raise ValueError(family)


def make_estimator(family, params, seed):
    if family == "logistic_regression":
        classifier = LogisticRegression(**params, max_iter=1500, random_state=seed)
    elif family == "random_forest":
        classifier = RandomForestClassifier(**params, n_estimators=200, n_jobs=2, random_state=seed)
    elif family == "svm":
        classifier = SVC(**params, kernel="rbf", probability=False, decision_function_shape="ovr",
                         break_ties=True, random_state=seed)
    elif family == "mlp":
        params = dict(params)
        params["hidden_layer_sizes"] = (params.pop("hidden_units"),)
        classifier = MLPClassifier(**params, max_iter=400, early_stopping=False,
                                   n_iter_no_change=25, random_state=seed)
    else:
        raise ValueError(family)
    return make_pipeline(SimpleImputer(strategy="median", add_indicator=True), StandardScaler(), classifier)


def fit_recording_warnings(estimator, x, y):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", ConvergenceWarning)
        estimator.fit(x, y)
    return [str(w.message) for w in caught if issubclass(w.category, ConvergenceWarning)]


def predict_frame(frame, estimator, features, calibrator):
    p = calibrator.predict_proba(estimator_logits(estimator, frame[features]))
    result = frame[["match_id", "season", "match_date", "home_team", "away_team", "result"]].copy()
    for k, label in enumerate(CLASSES):
        result["p_" + label] = p[:, k]
    return result


def assert_split_chronology(frame):
    rows, previous = [], None
    for name, seasons in SPLITS.items():
        subset = frame.loc[frame.season.isin(seasons)]
        if subset.empty:
            raise ValueError("No observations in split " + name)
        first, last = subset.match_date.min(), subset.match_date.max()
        if previous is not None and first <= previous:
            raise ValueError("Experimental splits overlap in calendar time")
        previous = last
        rows.append({"split": name, "seasons": ",".join(seasons), "n_matches": len(subset),
                     "date_min": first, "date_max": last, "H": int(subset.result.eq("H").sum()),
                     "D": int(subset.result.eq("D").sum()), "A": int(subset.result.eq("A").sum())})
    return pd.DataFrame(rows)


def reference_panel(odds):
    result = odds.copy()
    for label in CLASSES:
        result["odds_" + label] = result["ref_odds_" + label]
        result["bookmaker_" + label] = "Bet365"
    return result


def choose_threshold(predictions, odds):
    records = []
    for threshold in THRESHOLDS:
        bets, _, summary = simulate_bets(predictions, odds, threshold=threshold, staking="fixed", bootstrap_samples=0)
        turnover = float(bets.stake.sum()) if len(bets) else 0
        profit = float(bets.profit.sum()) if len(bets) else 0
        roi = profit / turnover if turnover else np.nan
        records.append({"threshold": threshold, "n_bets": len(bets), "turnover": turnover,
                        "profit": profit, "roi": roi, "eligible": len(bets) >= 30 and profit > 0})
    audit = pd.DataFrame(records)
    eligible = audit.loc[audit.eligible]
    if eligible.empty:
        return 1e6, audit, "no_admissible_positive_validation_strategy"
    selected = eligible.sort_values(["roi", "threshold"], ascending=[False, True]).iloc[0]
    return float(selected.threshold), audit, "validation_fixed_stake_roi_with_at_least_30_bets"


def paired_metric_intervals(a, b, seed, n_bootstrap=1000):
    if not a.match_id.equals(b.match_id):
        raise ValueError("Paired comparison requires identical ordered matches")
    y = encode_results(a.result)
    pa = a[["p_H", "p_D", "p_A"]].to_numpy()
    pb = b[["p_H", "p_D", "p_A"]].to_numpy()
    days = a.match_date.to_numpy()
    unique = np.unique(days)
    groups = [np.flatnonzero(days == day) for day in unique]
    rng = np.random.default_rng(seed)
    names = ["accuracy", "classwise_ece_10", "log_loss", "brier_score"]
    ma, mb = classification_metrics(y, pa), classification_metrics(y, pb)
    samples = {name: [] for name in names}
    for _ in range(n_bootstrap):
        positions = np.concatenate([groups[i] for i in rng.integers(0, len(groups), len(groups))])
        ca = classification_metrics(y[positions], pa[positions])
        cb = classification_metrics(y[positions], pb[positions])
        for name in names:
            samples[name].append(cb[name] - ca[name])
    return pd.DataFrame([{"metric": name, "difference_calibration_minus_accuracy": mb[name] - ma[name],
                          "ci_lower": float(np.quantile(samples[name], 0.025)),
                          "ci_upper": float(np.quantile(samples[name], 0.975)),
                          "bootstrap_unit": "match_calendar_date", "n_bootstrap": n_bootstrap} for name in names])


def run(args):
    start = time.perf_counter()
    output = Path(args.output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    data_root = Path(args.data_root).resolve()
    print("Building historical features", flush=True)
    frame, feature_metadata = build_features(data_root)
    frame["match_date"] = pd.to_datetime(frame.match_date).dt.normalize()
    frame = frame.loc[frame.season.ge("2014-15") & frame.result.isin(CLASSES)].sort_values(
        ["match_date", "match_id"]
    ).reset_index(drop=True)
    frame["split"] = None
    for name, seasons in SPLITS.items():
        frame.loc[frame.season.isin(seasons), "split"] = name
    frame = frame.loc[frame.split.notna()].reset_index(drop=True)
    if frame.match_id.duplicated().any():
        raise ValueError("Duplicate modeling matches")
    splits = assert_split_chronology(frame)
    save_table(frame, output, "modeling_matches")
    save_table(splits, output, "chronological_splits")
    write_json(output / "feature_metadata.json", feature_metadata)
    train = frame.loc[frame.split.eq("train")].copy()
    tune = frame.loc[frame.split.eq("tune")].copy()
    refit = frame.loc[frame.split.isin(["train", "tune"])].copy()
    calibration = frame.loc[frame.split.eq("calibration")].copy()
    selection = frame.loc[frame.split.eq("model_selection")].copy()
    candidates, filter_audit = filter_features(train)
    save_table(filter_audit, output, "feature_filter_audit")
    print(f"Training filters: {len(candidates)} / {len(filter_audit)} predictors retained", flush=True)
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    fit_log, tuning_log, selection_rows, selected_features = [], [], [], {}
    models = {}
    for branch in ("accuracy", "calibration"):
        print("Forward feature selection: " + branch, flush=True)
        features, sfs_audit = forward_select(train, candidates, objective=branch,
                                            max_features=args.sfs_features, candidate_limit=args.candidate_limit)
        selected_features[branch] = features
        save_table(sfs_audit, output, "forward_selection_" + branch)
        for family_index, family in enumerate(FAMILIES):
            print(f"TPE tuning: {branch}/{family} ({args.trials} trials)", flush=True)
            sampler = optuna.samplers.TPESampler(seed=args.seed + family_index, n_startup_trials=min(4, args.trials))
            study = optuna.create_study(direction="minimize", sampler=sampler)

            def objective(trial):
                params = trial_parameters(trial, family)
                estimator = make_estimator(family, params, args.seed)
                convergence = fit_recording_warnings(estimator, train[features], encode_results(train.result))
                probabilities = softmax(estimator_logits(estimator, tune[features]), axis=1)
                metrics = classification_metrics(encode_results(tune.result), probabilities)
                value = -metrics["accuracy"] if branch == "accuracy" else metrics["classwise_ece_10"]
                tuning_log.append({"branch": branch, "family": family, "trial": trial.number,
                                   "objective": value, "params_json": json.dumps(params),
                                   "convergence_warning": " | ".join(convergence), **metrics})
                return value

            study.optimize(objective, n_trials=args.trials)
            estimator = make_estimator(family, study.best_params, args.seed)
            convergence = fit_recording_warnings(estimator, refit[features], encode_results(refit.result))
            calibrator = TemperatureCalibrator().fit(estimator_logits(estimator, calibration[features]),
                                                      encode_results(calibration.result))
            predictions = predict_frame(selection, estimator, features, calibrator)
            metrics = classification_metrics(encode_results(predictions.result), predictions[["p_H", "p_D", "p_A"]])
            selection_rows.append({"branch": branch, "family": family, "temperature": calibrator.temperature,
                                   "n_features": len(features), "params_json": json.dumps(study.best_params), **metrics})
            fit_log.append({"branch": branch, "family": family, "convergence_warnings": convergence})
            models[(branch, family)] = (estimator, features, calibrator)
    model_selection = pd.DataFrame(selection_rows)
    save_table(model_selection, output, "model_selection_scores")
    save_table(pd.DataFrame(tuning_log), output, "hyperparameter_trials")
    write_json(output / "selected_features.json", selected_features)
    winners = {}
    # Choices are fixed here, exclusively using 2023-24; test labels are not read by selection.
    for branch, metric, ascending in [("accuracy", "accuracy", False), ("calibration", "classwise_ece_10", True)]:
        row = model_selection.loc[model_selection.branch.eq(branch)].sort_values(
            [metric, "log_loss", "family"], ascending=[ascending, True, True]
        ).iloc[0]
        winners[branch] = row.family
    print("Locked branch winners: " + json.dumps(winners), flush=True)
    odds, odds_audit = build_odds_panel(data_root, snapshot="preclosing", require_reference=True)
    odds["match_date"] = pd.to_datetime(odds.match_date).dt.normalize()
    save_table(odds, output, "bookmaker_odds_panel")
    write_json(output / "odds_audit.json", odds_audit)
    prediction_rows, metric_rows, reliability_rows = [], [], []
    bet_rows, equity_rows, betting_rows, threshold_rows = [], [], [], []
    locked_thresholds = {}
    test_predictions = {}
    train_prior = np.bincount(encode_results(refit.result), minlength=3) / len(refit)
    all_evaluation = frame.loc[frame.split.isin(["model_selection", "strategy_validation", "test", "monitoring"])]
    for branch, family in winners.items():
        estimator, features, calibrator = models[(branch, family)]
        predictions = predict_frame(all_evaluation, estimator, features, calibrator)
        predictions["split"] = all_evaluation.split.to_numpy()
        predictions["branch"], predictions["family"] = branch, family
        prediction_rows.append(predictions)
        strategy_predictions = predictions.loc[predictions.split.eq("strategy_validation")]
        threshold, threshold_audit, reason = choose_threshold(strategy_predictions, odds)
        locked_thresholds[branch] = {"threshold": threshold, "reason": reason,
                                     "selection_season": "2024-25", "minimum_validation_bets": 30}
        threshold_audit["branch"] = branch
        threshold_rows.append(threshold_audit)
        joblib.dump({"estimator": estimator, "features": features, "calibrator": calibrator,
                     "classes": CLASSES, "branch": branch, "family": family,
                     "threshold": threshold, "fit_seasons": SPLITS["train"] + SPLITS["tune"],
                     "calibration_seasons": SPLITS["calibration"]}, output / ("model_" + branch + ".joblib"))
        for split, subset in predictions.groupby("split", sort=False):
            y = encode_results(subset.result)
            p = subset[["p_H", "p_D", "p_A"]].to_numpy()
            metric_rows.append({"model": branch, "family": family, "split": split,
                                "scope": "all_cohort_matches", **classification_metrics(y, p)})
            matched = subset.merge(odds[["match_id"]], on="match_id", validate="one_to_one")
            if len(matched):
                metric_rows.append({"model": branch, "family": family, "split": split,
                                    "scope": "matched_bookmaker_coverage", **classification_metrics(
                                        encode_results(matched.result), matched[["p_H", "p_D", "p_A"]])})
            if split == "test":
                test_predictions[branch] = subset.reset_index(drop=True)
                reliability_rows.extend([{**row, "model": branch} for row in reliability_bins(y, p)])
            if split not in ("strategy_validation", "test", "monitoring"):
                continue
            policies = {"validation_selected": threshold, "predeclared_5pct": 0.05}
            for policy, edge in policies.items():
                for odds_mode, panel in [("best_individual_book", odds), ("bet365_reference", reference_panel(odds))]:
                    for staking in ("fixed", "kelly"):
                        bets, equity, summary = simulate_bets(subset, panel, threshold=edge, staking=staking,
                                                               bootstrap_samples=1000 if split == "test" else 0,
                                                               random_state=args.seed)
                        labels = {"branch": branch, "family": family, "split": split, "policy": policy,
                                  "odds_mode": odds_mode, "staking": staking, "threshold": edge}
                        for name, value in labels.items():
                            bets[name], equity[name] = value, value
                        bet_rows.append(bets)
                        equity_rows.append(equity)
                        betting_rows.append({**summary, **labels})
    # Frequency and de-vigged bookmaker baselines are evaluated on the same matches.
    for split, subset in all_evaluation.groupby("split", sort=False):
        y = encode_results(subset.result)
        metric_rows.append({"model": "training_class_frequency", "family": "baseline", "split": split,
                            "scope": "all_cohort_matches", **classification_metrics(y, np.tile(train_prior, (len(y), 1)))})
        matched = subset.merge(odds[["match_id", "ref_p_H", "ref_p_D", "ref_p_A"]], on="match_id", validate="one_to_one")
        if len(matched):
            metric_rows.append({"model": "bet365_devig", "family": "market_baseline", "split": split,
                                "scope": "matched_bookmaker_coverage", **classification_metrics(encode_results(matched.result),
                                                                                               matched[["ref_p_H", "ref_p_D", "ref_p_A"]])})
            metric_rows.append({"model": "training_class_frequency", "family": "baseline", "split": split,
                                "scope": "matched_bookmaker_coverage", **classification_metrics(encode_results(matched.result),
                                                                                               np.tile(train_prior, (len(matched), 1)))})
            if split == "test":
                reliability_rows.extend([{**row, "model": "bet365_devig"} for row in reliability_bins(
                    encode_results(matched.result), matched[["ref_p_H", "ref_p_D", "ref_p_A"]])])
    predictions = pd.concat(prediction_rows, ignore_index=True)
    metrics = pd.DataFrame(metric_rows)
    bets = pd.concat(bet_rows, ignore_index=True)
    equity = pd.concat(equity_rows, ignore_index=True)
    betting = pd.DataFrame(betting_rows)
    for name, table in [("predictions", predictions), ("classification_scores", metrics), ("reliability_bins", pd.DataFrame(reliability_rows)),
                        ("bets", bets), ("daily_equity", equity), ("betting_summary", betting),
                        ("threshold_validation", pd.concat(threshold_rows, ignore_index=True))]:
        save_table(table, output, name)
    intervals = paired_metric_intervals(test_predictions["accuracy"], test_predictions["calibration"], args.seed)
    save_table(intervals, output, "paired_test_metric_intervals")
    write_json(output / "locked_choices.json", {"families": winners, "thresholds": locked_thresholds})
    packages = {}
    for name in ("numpy", "pandas", "scipy", "scikit-learn", "optuna", "matplotlib", "pyarrow", "joblib"):
        packages[name] = importlib.metadata.version(name)
    source_hashes = {str(p.relative_to(ROOT.parent)): hashlib.sha256(p.read_bytes()).hexdigest()
                     for p in sorted(ROOT.glob("*.py"))}
    inputs = [data_root / "metadata" / "acquisition_summary.json",
              data_root / "data" / "processed" / "football_data" / "matches_current_cohort.parquet",
              data_root / "data" / "processed" / "football_data" / "match_odds_1x2_long.parquet"]
    input_hashes = {str(p.relative_to(data_root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}
    metadata = {"study": "Initial EPL accuracy versus calibration experiment", "data_snapshot_as_of": "2026-10-06",
                "run_date": "2026-10-13", "seed": args.seed, "trials_per_family_per_branch": args.trials,
                "families": FAMILIES, "splits": SPLITS, "selected_features": selected_features,
                "frozen_choices": {"families": winners, "thresholds": locked_thresholds},
                "fit_warnings": fit_log, "python": platform.python_version(), "packages": packages,
                "source_sha256": source_hashes, "input_sha256": input_hashes,
                "duration_seconds": time.perf_counter() - start,
                "limitations": ["Archived price replay; quote clocks and feature publication times are unverified",
                                "Current-club historical cohort has survivor bias; not the full historical Premier League",
                                "2026-27 monitoring is only the 50 completed matches in the October 6 snapshot",
                                "Small TPE/SFS search budget; one untouched test season; no executable arbitrage claims"]}
    write_json(output / "run_metadata.json", metadata)
    from .reporting import build_report
    build_report(output)
    print("Completed experiment in " + str(round(time.perf_counter() - start, 1)) + " seconds", flush=True)
    return metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", default=str(ROOT.parent / "epl_data"))
    parser.add_argument("--output", default=str(ROOT / "results"))
    parser.add_argument("--trials", type=int, default=12)
    parser.add_argument("--sfs-features", type=int, default=8)
    parser.add_argument("--candidate-limit", type=int, default=18)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    if args.trials < 1 or args.sfs_features < 1 or args.candidate_limit < 1:
        parser.error("Search budgets must be positive")
    run(args)


if __name__ == "__main__":
    main()
