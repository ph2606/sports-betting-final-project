"""Independent exported-account, model, forecast and complete-graph checks."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from scipy.special import softmax
from threadpoolctl import threadpool_limits

from epl_execution.audit import _audit_account, _near, _require
from epl_live.ledger import read_forecasts, verify_ledger


ROOT = Path(__file__).resolve().parents[1]
SEASON_COUNTS = {"2022-23": 368, "2023-24": 360, "2024-25": 368, "2025-26": 374}
GROUPS = ("team_control", "player_form", "player_squad", "team_player_squad")
FAMILIES = ("logistic", "hist_boost")
OLD_SINGLE = Path("epl_strategy_lab/results/20261015T040052Z_100k84")
OLD_CONTINUOUS = Path("epl_strategy_validation/results/20261015_temporal_selection")


def _date(values):
    values = pd.to_datetime(values, errors="raise", utc=True).dt.tz_convert(None).dt.normalize()
    if values.isna().any():
        raise AssertionError("Missing exported date")
    return values


def _audit_policy(config, predictions, opportunities, bets, equity):
    """Recompute qualifiers and stake requests directly, without calling replay."""
    native = opportunities.copy()
    native["match_date"] = _date(native.match_date)
    p = predictions.loc[predictions.model_key == config["model_key"]].copy()
    if p.match_id.duplicated().any() or set(p.match_id) != set(native.match_id):
        raise AssertionError("Policy probabilities do not exactly cover its opportunity universe")
    p = p.set_index("match_id").reindex(native.match_id)
    for column in ("result", "season"):
        if not np.array_equal(p[column], native[column]):
            raise AssertionError("Policy prediction/native identity conflict")
    if not np.array_equal(_date(p.match_date).to_numpy(), native.match_date.to_numpy()):
        raise AssertionError("Policy prediction date conflict")
    probabilities = p[["p_H", "p_D", "p_A"]].to_numpy(float)
    prefix = "ref_odds_" if config["odds_mode"] == "reference" else "odds_"
    odds = native[[prefix + outcome for outcome in "HDA"]].to_numpy(float)
    if not np.isfinite(probabilities).all() or not np.isfinite(odds).all() or (odds <= 1).any():
        raise AssertionError("Nonfinite or invalid native probability/price")
    _near(probabilities.sum(axis=1), 1, "H/D/A probability mass", atol=1e-8)
    edges = probabilities * odds - 1
    selection = np.argmax(edges, axis=1)
    n = np.arange(len(native))
    native["expected_selection"] = np.array(list("HDA"))[selection]
    native["expected_probability"] = probabilities[n, selection]
    native["expected_odds"] = odds[n, selection]
    native["expected_edge"] = edges[n, selection]
    native["qualified"] = native.expected_edge > 0.05
    if config["odds_mode"] == "reference":
        native["expected_bookmaker"] = native.reference_bookmaker
    else:
        native["expected_bookmaker"] = native[["bookmaker_" + o for o in "HDA"]].to_numpy()[n, selection]
    recorded_bets = bets.copy()
    recorded_bets["match_date"] = _date(recorded_bets.match_date)
    curve = equity.copy()
    curve["match_date"] = _date(curve.match_date)
    curve = curve.set_index("match_date")
    checked = 0
    for date, panel in native.groupby("match_date", sort=True):
        cash = float(curve.loc[date, "start_bankroll"])
        panel = panel.loc[panel.qualified].copy()
        if config["staking"] == "fixed":
            requests = np.full(len(panel), 1000.0 if cash > 0 else 0.0)
        elif config["staking"] == "kelly":
            requests = cash * np.minimum(0.02, 0.25 * panel.expected_edge.to_numpy() / (panel.expected_odds.to_numpy() - 1))
        else:
            raise AssertionError("Unexpected new-player stake rule")
        scale = min(1.0, cash / requests.sum()) if requests.sum() > 0 else 1.0
        panel["expected_stake"] = requests * scale
        panel = panel.loc[panel.expected_stake > 0].sort_values("match_id")
        actual = recorded_bets.loc[recorded_bets.match_date == date].sort_values("match_id")
        if panel.match_id.tolist() != actual.match_id.tolist():
            raise AssertionError("Recorded trade identities disagree with strict max-edge qualification/funding")
        if panel.expected_selection.tolist() != actual.selection.tolist():
            raise AssertionError("Maximum-edge H/D/A selection or deterministic tie order changed")
        for expected, column in (("expected_probability", "probability"), ("expected_odds", "odds"), ("expected_stake", "stake")):
            _near(panel[expected], actual[column], "Independent policy " + column)
        if "bookmaker" in actual and panel.expected_bookmaker.astype(str).tolist() != actual.bookmaker.astype(str).tolist():
            raise AssertionError("Recorded bookmaker differs from native selected outcome")
        if "qualified_matches" in curve:
            _near(curve.loc[date, "qualified_matches"], int(native.loc[native.match_date == date, "qualified"].sum()), "Qualified match count")
        checked += len(actual)
    return checked


def _audit_graph(graph, new_equity, original, *, anchor_date, n_old, points_per_curve):
    graph = graph.copy()
    _require(graph, ["strategy_id", "match_date", "end_bankroll", "is_initial"], "Combined graph")
    graph["match_date"] = _date(graph.match_date)
    if graph.is_initial.dtype != bool:
        values = graph.is_initial.astype(str).str.lower()
        if not values.isin(["true", "false"]).all():
            raise AssertionError("Invalid graph initial flag")
        graph["is_initial"] = values.eq("true")
    expected = pd.concat([original[["strategy_id", "match_date", "end_bankroll"]],
                          new_equity[["strategy_id", "match_date", "end_bankroll"]]], ignore_index=True)
    expected["match_date"] = _date(expected.match_date)
    if original.strategy_id.nunique() != n_old or new_equity.strategy_id.nunique() != 32:
        raise AssertionError("Incorrect old/new graph population")
    if graph.strategy_id.nunique() != n_old + 32 or len(graph) != (n_old + 32) * points_per_curve:
        raise AssertionError("Combined graph omits strategies or dates")
    if graph.duplicated(["strategy_id", "match_date"]).any() or set(graph.strategy_id) != set(expected.strategy_id):
        raise AssertionError("Duplicate or unknown graph identity")
    if not np.isfinite(graph.end_bankroll).all() or (graph.end_bankroll < -1e-6).any():
        raise AssertionError("Invalid graph money amount")
    common_dates = None
    for sid, curve in graph.groupby("strategy_id"):
        curve = curve.sort_values("match_date")
        if len(curve) != points_per_curve or curve.is_initial.sum() != 1 or not curve.is_initial.iloc[0]:
            raise AssertionError("A graph curve lacks exactly one leading capital anchor")
        if curve.match_date.iloc[0] != pd.Timestamp(anchor_date):
            raise AssertionError("Incorrect graph anchor date")
        _near(curve.end_bankroll.iloc[0], 100000, "Graph initial 100K")
        if common_dates is None:
            common_dates = curve.match_date.to_numpy()
        elif not np.array_equal(common_dates, curve.match_date.to_numpy()):
            raise AssertionError("Graph curves use different date universes")
        native = expected.loc[expected.strategy_id == sid].sort_values("match_date")
        real = curve.loc[~curve.is_initial]
        if not np.array_equal(native.match_date.to_numpy(), real.match_date.to_numpy()):
            raise AssertionError("Graph dates differ from complete saved account dates")
        _near(real.end_bankroll, native.end_bankroll, "Every graph point, including frozen original strategies")
    return len(graph)


def _audit_predictions(predictions, opportunities, model_catalog):
    _require(predictions, ["match_id", "model_key", "match_date", "season", "result", "p_H", "p_D", "p_A"], "Predictions")
    if len(predictions) != 19110 or predictions.model_key.nunique() != 13 or predictions.duplicated(["model_key", "match_id"]).any():
        raise AssertionError("Expected 13 complete prediction series on 1470 fixtures")
    keys = {row["model_key"] for row in model_catalog["models"]}
    if len(keys) != 8 or not keys.issubset(predictions.model_key):
        raise AssertionError("New model prediction identities missing")
    by_id = opportunities.set_index("match_id")
    for key, one in predictions.groupby("model_key"):
        if set(one.match_id) != set(opportunities.match_id):
            raise AssertionError("Prediction families have unequal fixture coverage")
        p = one[["p_H", "p_D", "p_A"]].to_numpy(float)
        if not np.isfinite(p).all() or (p < 0).any() or (p > 1).any():
            raise AssertionError("Invalid model probabilities")
        _near(p.sum(axis=1), 1, "Prediction mass", atol=1e-8)
        native = by_id.reindex(one.match_id)
        for column in ("season", "result"):
            if one[column].tolist() != native[column].tolist():
                raise AssertionError("Prediction settlement identity conflict")
        if not np.array_equal(_date(one.match_date).to_numpy(), _date(native.match_date).to_numpy()):
            raise AssertionError("Prediction target date conflict")
    return keys


def _audit_scores(output, predictions):
    checked = 0
    for stem, expected in (("model_metrics_pooled", 8), ("model_metrics_seasonal", 32)):
        table = pd.read_parquet(output / "rolling_models" / f"{stem}.parquet")
        if len(table) != expected or table.duplicated(["feature_group", "model_type", "outer_season"]).any():
            raise AssertionError("Incomplete model metric population")
        for row in table.to_dict("records"):
            key = f"pm_{row['model_type']}_{row['feature_group']}"
            part = predictions.loc[predictions.model_key == key]
            if row["outer_season"] != "pooled":
                part = part.loc[part.season == row["outer_season"]]
            p = part[["p_H", "p_D", "p_A"]].to_numpy(float)
            y = part.result.map({"H": 0, "D": 1, "A": 2}).to_numpy(int)
            target = np.eye(3)[y]
            _near(row["n_matches"], len(part), "Model score match count")
            _near(row["accuracy"], (p.argmax(axis=1) == y).mean(), "Model accuracy")
            _near(row["log_loss"], -np.log(np.clip(p[np.arange(len(y)), y], np.finfo(float).eps, 1)).mean(), "Model log loss")
            _near(row["brier_score"], np.square(p - target).sum(axis=1).mean(), "Model Brier score")
            for count in (5, 10, 15):
                class_errors = []
                for k in range(3):
                    bins = np.minimum((p[:, k] * count).astype(int), count - 1)
                    error = 0.0
                    for bin_id in range(count):
                        mask = bins == bin_id
                        if mask.any():
                            error += mask.mean() * abs(p[mask, k].mean() - (y[mask] == k).mean())
                    class_errors.append(error)
                _near(row[f"classwise_ece_{count}"], np.mean(class_errors), "Model classwise ECE")
            checked += 1
    return checked


def _verify_bundle_probabilities(bundle, frame, predictions):
    by_id = frame.set_index("match_id")
    if not predictions.match_id.isin(by_id.index).all():
        raise AssertionError("Model prediction lacks saved feature identity")
    features = by_id.reindex(predictions.match_id)[bundle["features"]]
    model = bundle["model"]
    with threadpool_limits(limits=1):
        raw = model.predict_proba(features)
    classes = list(model.classes_)
    if set(classes) != {0, 1, 2}:
        raise AssertionError("Fitted estimator lacks H/D/A class alignment")
    logits = np.log(np.clip(raw[:, [classes.index(k) for k in (0, 1, 2)]], 1e-12, 1))
    temperature = float(bundle["calibrator"].temperature)
    _near(temperature, bundle["temperature"], "Saved scalar calibration temperature")
    _near(predictions[["p_H", "p_D", "p_A"]], softmax(logits / temperature, axis=1), "Independent bundle-calibrated predictions")
    if set(("p_raw_H", "p_raw_D", "p_raw_A")).issubset(predictions):
        _near(predictions[["p_raw_H", "p_raw_D", "p_raw_A"]], softmax(logits, axis=1), "Uncalibrated model predictions")


def _audit_models(output, features, future_features, predictions, future_predictions, model_catalog):
    checked = 0
    future_by_key = {}
    for directory, metadata_name, expected_count in (("rolling_models", "models_metadata.json", 32),
                                                      ("future_models", "future_models_metadata.json", 8)):
        metadata = json.loads((output / directory / metadata_name).read_text(encoding="utf-8"))
        if metadata["n_models"] != expected_count or len(metadata["artifacts"]) != expected_count:
            raise AssertionError("Incorrect saved model bundle population")
        seen = set()
        for row in metadata["artifacts"]:
            name = row["artifact_name"]
            if Path(name).name != name:
                raise AssertionError("Unsafe saved artifact name")
            artifact = output / directory / name
            if hashlib.sha256(artifact.read_bytes()).hexdigest() != row["artifact_sha256"]:
                raise AssertionError("Saved model bundle hash changed")
            bundle = joblib.load(artifact)
            group, family = row["feature_group"], row["model_type"]
            if group not in GROUPS or family not in FAMILIES or bundle["features"] != model_catalog["groups"][group]:
                raise AssertionError("Fitted model group/features identity conflict")
            key = f"pm_{family}_{group}"
            outer = row.get("outer_season")
            identity = (outer, group, family)
            if identity in seen:
                raise AssertionError("Duplicate fitted model identity")
            seen.add(identity)
            if directory == "rolling_models":
                year = int(outer[:4])
                train = [f"{y}-{str(y+1)[-2:]}" for y in range(2016, year - 2)]
                tune = [f"{year-2}-{str(year-1)[-2:]}"]
                calibration = [f"{year-1}-{str(year)[-2:]}"]
                part = predictions.loc[(predictions.model_key == key) & (predictions.season == outer)]
                frame = features
            else:
                train = [f"{y}-{str(y+1)[-2:]}" for y in range(2016, 2024)]
                tune, calibration = ["2024-25"], ["2025-26"]
                part = future_predictions.loc[future_predictions.model_key == key]
                frame = future_features
                future_by_key[key] = row
            for field, expected in (("train_seasons", train), ("tune_seasons", tune),
                                     ("refit_seasons", train + tune), ("calibration_seasons", calibration)):
                if row[field] != expected or bundle[field] != expected:
                    raise AssertionError("Fitted chronological roles changed: " + field)
            if bundle["classes"] != ["H", "D", "A"] or bundle["feature_group"] != group or bundle["model_type"] != family:
                raise AssertionError("Bundle model identity or class order changed")
            if part.empty:
                raise AssertionError("A declared model has no exported predictions")
            _verify_bundle_probabilities(bundle, frame, part)
            checked += 1
    return checked, future_by_key


def _audit_forecasts(output, future_predictions, future_features, future_models):
    ledger = output / "forecasts.jsonl"
    verification = verify_ledger(ledger, "forecast")
    records = read_forecasts(ledger)
    if len(records) != 80 or len(future_predictions) != 80 or future_predictions.duplicated(["model_key", "match_id"]).any():
        raise AssertionError("Expected exactly 80 separate new future records")
    if not future_predictions.status.eq("pending").all() or future_predictions.model_key.nunique() != 8 or future_predictions.match_id.nunique() != 10:
        raise AssertionError("Future predictions must remain complete, pending and unscored")
    indexed = future_predictions.set_index(["model_key", "match_id"])
    feature_rows = future_features.set_index("match_id")
    seen = set()
    for record in records:
        identity = (record["model_id"], record["match_id"])
        if identity in seen or identity not in indexed.index:
            raise AssertionError("Forecast/model/fixture identity mismatch")
        seen.add(identity)
        row = indexed.loc[identity]
        artifact = future_models[record["model_id"]]
        if record["model_sha256"] != artifact["artifact_sha256"]:
            raise AssertionError("Forecast points to a different saved model hash")
        _near([record["probabilities"][outcome] for outcome in "HDA"], row[["p_H", "p_D", "p_A"]], "Forecast probabilities")
        if record["forecast_type"] != "team_only" or record.get("market_quote") is not None:
            raise AssertionError("New player candidates must not imply a quoted wager")
        if record.get("feature_group") != artifact["feature_group"]:
            raise AssertionError("Future player feature group identity changed")
        if set(record["features"]) != set(artifact["features"]):
            raise AssertionError("Forecast feature inventory differs from its model")
        target = feature_rows.loc[record["match_id"]]
        for column, value in record["features"].items():
            if pd.isna(target[column]):
                if value is not None:
                    raise AssertionError("Missing future feature was silently replaced")
            else:
                _near(value, target[column], "Forecast feature value")
    return verification


def audit_export(output: Path) -> dict:
    output = Path(output)
    catalog = json.loads((output / "new_strategy_catalog.json").read_text(encoding="utf-8"))
    if [row["strategy_id"] for row in catalog] != [f"P{i:03d}" for i in range(1, 33)]:
        raise AssertionError("The complete P001-P032 catalog is required")
    old_catalog = json.loads((ROOT / OLD_SINGLE / "catalog.json").read_text(encoding="utf-8"))
    all_catalog = json.loads((output / "all_strategy_catalog.json").read_text(encoding="utf-8"))
    if all_catalog != old_catalog + catalog:
        raise AssertionError("Combined appendix catalog changed or omitted old/new strategy definitions")
    model_catalog = json.loads((output / "model_catalog.json").read_text(encoding="utf-8"))
    opportunities = pd.read_parquet(output / "opportunities.parquet")
    if len(opportunities) != 1470 or opportunities.match_id.duplicated().any() or opportunities.groupby("season").size().to_dict() != SEASON_COUNTS:
        raise AssertionError("Native 1470 opportunity population changed")
    predictions = pd.read_parquet(output / "predictions.parquet")
    new_keys = _audit_predictions(predictions, opportunities, model_catalog)
    tables = {}
    checked_accounts, checked_bets = 0, 0
    all_accounts = set()
    for scope, count in (("single", 32), ("continuous", 32), ("seasonal", 128)):
        metrics, bets, equity = [pd.read_parquet(output / f"{stem}_{scope}.parquet") for stem in ("metrics", "bets", "equity")]
        tables[scope] = (metrics, bets, equity)
        if len(metrics) != count or metrics.account_id.duplicated().any() or not metrics.scope.eq(scope).all():
            raise AssertionError("Incomplete/duplicate metric account scopes")
        if set(metrics.strategy_id) != {row["strategy_id"] for row in catalog}:
            raise AssertionError("Metrics omit a new strategy")
        if scope == "seasonal" and metrics.groupby("season").size().to_dict() != {label: 32 for label in SEASON_COUNTS}:
            raise AssertionError("Annual strategy scopes incomplete")
        if set(equity.account_id) != set(metrics.account_id) or not set(bets.account_id).issubset(metrics.account_id):
            raise AssertionError("Saved financial ledgers contain unknown/missing accounts")
        by_strategy = {row["strategy_id"]: row for row in catalog}
        for metric in metrics.to_dict("records"):
            aid = metric["account_id"]
            if aid in all_accounts or aid != f"{scope}:{metric['strategy_id']}:{metric['season']}":
                raise AssertionError("Account identity conflict across scopes")
            all_accounts.add(aid)
            if metric["execution_mode"] != "new_player_model_replay" or not bool(metric["funding_feasible"]):
                raise AssertionError("New account funding/execution status changed")
            b, e = [frame.loc[frame.account_id == aid].copy() for frame in (bets, equity)]
            for frame in (b, e):
                if not frame.strategy_id.eq(metric["strategy_id"]).all():
                    raise AssertionError("Financial ledger strategy/account conflict")
            native = opportunities if scope == "continuous" else opportunities.loc[opportunities.season == metric["season"]]
            _audit_account(metric, b, e, opportunities=native)
            config = by_strategy[metric["strategy_id"]]
            p = predictions.loc[(predictions.model_key == config["model_key"]) & predictions.match_id.isin(native.match_id)]
            checked_bets += _audit_policy(config, p, native, b, e)
            checked_accounts += 1
    graph_rows = {}
    for scope, stem, original_path, old_count, anchor, points in (
        ("single", "graph_equity_2025_all", ROOT / OLD_SINGLE / "equity.parquet", 84, "2025-08-14", 114),
        ("continuous", "graph_equity_continuous_all", ROOT / OLD_CONTINUOUS / "equity_continuous.parquet", 56, "2022-08-04", 454)):
        graph_rows[scope] = _audit_graph(pd.read_csv(output / f"{stem}.csv"), tables[scope][2], pd.read_parquet(original_path),
                                       anchor_date=anchor, n_old=old_count, points_per_curve=points)
    features, future_features = [pd.read_parquet(output / name) for name in ("features.parquet", "future_features.parquet")]
    if len(features) != 3410 or features.match_id.duplicated().any() or len(future_features) != 10 or future_features.match_id.duplicated().any():
        raise AssertionError("Historical/future feature populations changed")
    for frame in (features, future_features):
        for column in [c for c in frame if c.startswith("audit_player_") and c.endswith("_source_date")]:
            dates = pd.to_datetime(frame[column], utc=True, errors="raise").dt.tz_convert(None).dt.normalize()
            if (dates.notna() & dates.ge(_date(frame.match_date))).any():
                raise AssertionError("Target/future player evidence entered exported features")
    future_predictions = pd.read_parquet(output / "future_predictions.parquet")
    model_count, future_models = _audit_models(output, features, future_features, predictions, future_predictions, model_catalog)
    score_count = _audit_scores(output, predictions)
    forecast_summary = _audit_forecasts(output, future_predictions, future_features, future_models)
    provenance = json.loads((output / "source_provenance.json").read_text(encoding="utf-8"))["inputs_and_code_sha256"]
    for relative, expected in provenance.items():
        path = (ROOT / relative).resolve()
        if not path.is_relative_to(ROOT) or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise AssertionError("Source/code preservation hash changed: " + relative)
    if not {"epl_live/forecasts.jsonl", "epl_live/outcomes.jsonl"}.issubset({key.replace("\\", "/") for key in provenance}):
        raise AssertionError("Original prospective ledgers lack preservation hashes")
    return {"status": "passed", "checked_cashflow_accounts": checked_accounts,
        "checked_qualified_and_sized_bets": checked_bets, "new_strategy_count": 32,
        "new_model_series": len(new_keys), "prediction_rows": len(predictions), "native_opportunities": len(opportunities),
        "checked_model_bundles_and_probabilities": model_count, "new_pending_forecasts": 80,
        "independently_recomputed_model_metric_rows": score_count,
        "complete_graph_rows": graph_rows, "preserved_source_and_code_files": len(provenance),
        "forecast_chain": forecast_summary,
        "interpretation": "Independent identities, chronology, selected probabilities/prices/stakes, cashflows and all curve points; no executable-fill or new predictive-edge claim"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    print(json.dumps(audit_export(parser.parse_args().output), indent=2))
