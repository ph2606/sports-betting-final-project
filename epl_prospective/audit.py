"""Independently reconcile released probabilities, outcomes and score tables."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from epl_live.ledger import read_forecasts, read_outcomes, verify_ledger

ORIGINAL_SHA256 = "f828b68d2a3deb44457c0b92629d3e7c6655cfa8d8eb8f69ff30607b73680214"


def near(left, right, name):
    if not np.allclose(np.asarray(left, float), np.asarray(right, float), atol=1e-10, rtol=1e-9, equal_nan=True):
        raise AssertionError(name + " does not reconcile")


def audit_export(output):
    """Compute score identities directly; do not call the analysis builder."""
    output = Path(output)
    status = json.loads((output / "prospective_status.json").read_text())
    original_bytes = (output / "original_forecast_ledger.jsonl").read_bytes()
    if hashlib.sha256(original_bytes).hexdigest() != ORIGINAL_SHA256:
        raise AssertionError("The anchored original forecast ledger changed")
    if not (output / "forecast_ledger_as_of.jsonl").read_bytes().startswith(original_bytes):
        raise AssertionError("The as-of ledger rewrote its original forecast prefix")
    original = read_forecasts(output / "original_forecast_ledger.jsonl")
    current = read_forecasts(output / "forecast_ledger_as_of.jsonl")
    outcomes = read_outcomes(output / "outcome_ledger_as_of.jsonl")
    for name, kind in (("original_forecast_ledger", "forecast"), ("forecast_ledger_as_of", "forecast"),
            ("outcome_ledger_as_of", "outcome")):
        verify_ledger(output / (name + ".jsonl"), kind)
    records = {(r["model_id"], r["match_id"]): r for r in original}
    results = {r["match_id"]: r for r in outcomes}
    if len(original) != 40 or len(records) != 40 or len({r["match_id"] for r in original}) != 10:
        raise AssertionError("Expected four original predictions for each of ten fixtures")
    frame = pd.read_parquet(output / "forecast_outcome_audit.parquet")
    if len(frame) != 40 or frame.duplicated(["model_id", "match_id"]).any() or set(frame[["model_id", "match_id"]].itertuples(index=False, name=None)) != set(records):
        raise AssertionError("The original forecast grid is missing, repeated or changed")
    expected = {}
    for row in frame.to_dict("records"):
        released = records[row["model_id"], row["match_id"]]
        p = np.array([released["probabilities"][k] for k in "HDA"], dtype=float)
        near([row["p_" + k] for k in "HDA"], p, "Released probabilities")
        for key in ("home_team", "away_team", "kickoff_utc", "created_at_utc"):
            if key.endswith("_utc"):
                if pd.Timestamp(row[key]) != pd.Timestamp(released[key]): raise AssertionError("Changed released " + key)
            elif row[key] != released[key]: raise AssertionError("Changed released " + key)
        if pd.Timestamp(released["created_at_utc"]) >= pd.Timestamp(released["kickoff_utc"]):
            raise AssertionError("A release was not before kickoff")
        outcome = results.get(row["match_id"])
        if outcome is None:
            if row["status"] != "pending" or not pd.isna(row["log_loss"]) or not pd.isna(row["brier_score"]):
                raise AssertionError("A pending fixture was scored")
            continue
        if row["status"] not in {"settled", "resolved"} or row["result"] != outcome["result"]:
            raise AssertionError("Observed outcome changed")
        for key in ("home_team", "away_team"):
            if outcome[key] != released[key]: raise AssertionError("Outcome fixture identity changed")
        if pd.Timestamp(outcome["settled_at_utc"]) < pd.Timestamp(released["kickoff_utc"]):
            raise AssertionError("Result observation predates kickoff")
        y = "HDA".index(outcome["result"])
        pick = int(p.argmax())
        loss = -np.log(np.clip(p[y], np.finfo(float).eps, 1. - np.finfo(float).eps))
        brier = float(np.square(p - np.eye(3)[y]).sum())
        near(row["correct"], float(pick == y), "Forecast correctness")
        near(row["log_loss"], loss, "Per-fixture log loss")
        near(row["brier_score"], brier, "Per-fixture Brier score")
        if row["predicted_outcome"] != "HDA"[pick]: raise AssertionError("Argmax outcome changed")
        expected[row["model_id"], row["match_id"]] = (float(pick == y), loss, brier)
    models = pd.read_parquet(output / "model_scores.parquet")
    original_models = {r["model_id"] for r in original}
    if len(models) != 4 or models.model_id.duplicated().any() or set(models.model_id) != original_models:
        raise AssertionError("Model score coverage changed")
    for row in models.to_dict("records"):
        values = np.array([v for (mid, _), v in expected.items() if mid == row["model_id"]], dtype=float).reshape(-1, 3)
        near(row["n_matches"], len(values), "Independent model fixture count")
        for index, name in enumerate(("accuracy", "log_loss", "brier_score")):
            mean = float(values[:, index].mean()) if len(values) else np.nan
            near(row[name], mean, "Aggregate " + name)
            if len(values) and not row[name + "_ci_low"] <= mean <= row[name + "_ci_high"]:
                raise AssertionError("An uncertainty interval excludes its own point estimate")
        if len(values):
            n, z = len(values), 1.959963984540054
            rate = float(values[:, 0].mean())
            middle = (rate + z * z / (2*n)) / (1 + z*z/n)
            radius = z * np.sqrt(rate*(1-rate)/n + z*z/(4*n*n)) / (1+z*z/n)
            near(row["accuracy_ci_low"], max(0., middle-radius), "Wilson lower interval")
            near(row["accuracy_ci_high"], min(1., middle+radius), "Wilson upper interval")
    pairs = pd.read_parquet(output / "pairwise_scores.parquet")
    if len(pairs) != 6 or pairs.duplicated(["model_a", "model_b"]).any():
        raise AssertionError("The complete six-comparison family changed")
    for row in pairs.to_dict("records"):
        a, b = row["model_a"], row["model_b"]
        matches = sorted({m for model, m in expected if model == a} & {m for model, m in expected if model == b})
        near(row["common_fixture_count"], len(matches), "Matched pair sample size")
        if matches:
            differences = np.array([expected[a, m] for m in matches]) - np.array([expected[b, m] for m in matches])
            for index, name in enumerate(("accuracy_diff", "log_loss_diff", "brier_score_diff")):
                near(row[name], differences[:, index].mean(), "Paired " + name)
    fixture_table = pd.read_parquet(output / "fixture_outcomes.parquet")
    if len(fixture_table) != 10 or fixture_table.match_id.duplicated().any():
        raise AssertionError("Fixture summary must contain ten distinct targets")
    for row in fixture_table.to_dict("records"):
        outcome = results.get(row["match_id"])
        if outcome is not None:
            for key in ("result", "home_goals", "away_goals"):
                if row[key] != outcome[key]: raise AssertionError("Fixture summary outcome conflict")
    next_frame = pd.read_parquet(output / "next_forecasts.parquet")
    all_pairs = {(r["model_id"], r["match_id"]): r for r in current}
    if next_frame.duplicated(["model_id", "match_id"]).any() or not next_frame.status.eq("pending").all():
        raise AssertionError("Future releases are duplicated or prematurely resolved")
    for row in next_frame.to_dict("records"):
        record = all_pairs[row["model_id"], row["match_id"]]
        if row["match_id"] in {r["match_id"] for r in original}:
            raise AssertionError("A future release contaminates the original target cohort")
        near([row["p_" + k] for k in "HDA"], [record["probabilities"][k] for k in "HDA"], "New released probabilities")
        if pd.Timestamp(record["created_at_utc"]) >= pd.Timestamp(record["kickoff_utc"]):
            raise AssertionError("New forecast time is after kickoff")
        for date in record.get("latest_feature_match_dates", {}).values():
            if date is not None and pd.Timestamp(date).date() >= pd.Timestamp(record["target_match_date"]).date():
                raise AssertionError("A live feature uses the target date or later")
    near(status["resolved_original_forecasts"], len(expected), "Resolved status count")
    near(status["pending_original_forecasts"], 40-len(expected), "Pending status count")
    near(status["new_pending_forecasts"], len(next_frame), "New pending release count")
    if status["recorded_trade_count"] != 0 or status["prospective_betting_performance_available"] or status["prospective_roi"] is not None:
        raise AssertionError("Probability forecasts were converted into trading performance")
    fresh = pd.read_parquet(output / "source_freshness.parquet")
    if len(fresh) != 6 or not fresh.source_capture_valid.all():
        raise AssertionError("Missing or invalid source captures")
    return {"status": "passed", "original_forecasts_checked": 40, "independent_original_fixtures": 10,
        "resolved_original_records": len(expected), "model_score_rows": len(models), "paired_comparisons": len(pairs),
        "new_pending_forecasts_checked": len(next_frame), "original_prefix_preserved": True,
        "forecast_outcome_chains_valid": True, "prospective_trades_inferred": False}
