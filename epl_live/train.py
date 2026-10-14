"""Fit the eight declared prospective candidates without using 2026/27 outcomes."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from scipy.special import softmax

from epl_modeling.ablation import C_GRID, FEATURE_GROUPS, estimator, fit_model, logits, season
from epl_modeling.experiment import save_table, write_json
from epl_modeling.metrics import CLASSES, TemperatureCalibrator, classification_metrics, encode_results

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parent
PROTOCOL = PROJECT / "epl_modeling" / "PROSPECTIVE_PROTOCOL.md"


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def fit_candidates(output_root: Path = ROOT / "models") -> Path:
    protocol_sha = sha256(PROTOCOL)
    destination = Path(output_root) / protocol_sha[:16]
    manifest_path = destination / "manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest["protocol_sha256"] != protocol_sha:
            raise ValueError("Existing model protocol does not match")
        for item in manifest["models"]:
            if sha256(destination / item["file"]) != item["sha256"]:
                raise ValueError("A frozen model file changed")
        return destination
    if destination.exists():
        raise FileExistsError("Incomplete model directory exists; do not overwrite it")
    frame_path = PROJECT / "epl_modeling" / "ablation_results" / "modeling_matches.parquet"
    frame = pd.read_parquet(frame_path)
    frame["match_date"] = pd.to_datetime(frame.match_date)
    train_seasons = [season(year) for year in range(2016, 2024)]
    train = frame.loc[frame.season.isin(train_seasons)].copy()
    tune = frame.loc[frame.season.eq("2024-25")].copy()
    calibration = frame.loc[frame.season.eq("2025-26")].copy()
    if not train.match_date.max() < tune.match_date.min() or not tune.match_date.max() < calibration.match_date.min():
        raise ValueError("Prospective fitting blocks overlap")
    if any(block.empty or block.result.nunique() != 3 for block in (train, tune, calibration)):
        raise ValueError("Missing prospective fitting/calibration observations")
    refit = pd.concat([train, tune], ignore_index=True)
    destination.mkdir(parents=True, exist_ok=False)
    trials, choices, artifacts = [], [], []
    for group, features in FEATURE_GROUPS.items():
        for kind in ("logistic", "market_residual"):
            values = []
            for C in C_GRID:
                model = fit_model(estimator(kind, C), kind, train, features)
                probabilities = softmax(logits(model, kind, tune, features), axis=1)
                metrics = classification_metrics(encode_results(tune.result), probabilities)
                values.append((metrics["log_loss"], C))
                trials.append({"feature_group": group, "model_type": kind, "C": C, **metrics})
            _, chosen_C = sorted(values)[0]
            model = fit_model(estimator(kind, chosen_C), kind, refit, features)
            calibrator = TemperatureCalibrator().fit(logits(model, kind, calibration, features), encode_results(calibration.result))
            model_id = f"prospective_v1_{kind}_{group}"
            name = model_id + ".joblib"
            joblib.dump({"model": model, "calibrator": calibrator, "features": features,
                         "model_id": model_id, "model_type": kind, "feature_group": group,
                         "protocol_sha256": protocol_sha, "classes": CLASSES}, destination / name)
            item = {"model_id": model_id, "model_type": kind, "feature_group": group,
                    "file": name, "sha256": sha256(destination / name), "n_features": len(features),
                    "C": chosen_C, "temperature": calibrator.temperature}
            choices.append(item)
            artifacts.append(item)
    market_calibrator = TemperatureCalibrator().fit(
        np.log(calibration[["ref_p_H", "ref_p_D", "ref_p_A"]].to_numpy(float)),
        encode_results(calibration.result))
    joblib.dump(market_calibrator, destination / "market_temperature.joblib")
    save_table(pd.DataFrame(trials), destination, "tuning_trials")
    save_table(pd.DataFrame(choices), destination, "frozen_model_choices")
    created = datetime.now(timezone.utc).isoformat()
    source_paths = [Path(__file__), PROJECT / "epl_modeling/ablation.py", PROJECT / "epl_modeling/market_residual.py",
                    PROJECT / "epl_modeling/metrics.py"]
    manifest = {"schema_version": 1, "protocol_sha256": protocol_sha, "trained_at_utc": created,
                "input_feature_table_sha256": sha256(frame_path), "input_feature_table": str(frame_path.relative_to(PROJECT)),
                "train_seasons": train_seasons, "tuning_season": "2024-25", "calibration_season": "2025-26",
                "refit_seasons": train_seasons + ["2024-25"], "target_season": "2026-27",
                "training_matches": len(train), "tuning_matches": len(tune), "calibration_matches": len(calibration),
                "models": artifacts, "market_temperature": market_calibrator.temperature,
                "market_temperature_sha256": sha256(destination / "market_temperature.joblib"),
                "class_prior": (np.bincount(encode_results(refit.result), minlength=3) / len(refit)).tolist(),
                "code_sha256": {str(p.relative_to(PROJECT)): sha256(p) for p in source_paths},
                "prospective_forecasts_created": 0,
                "notes": ["No 2026/27 outcome enters fitting, tuning or probability calibration.",
                          "All eight alternatives remain declared; no winner is selected from new outcomes.",
                          "The previously examined 2025/26 season is now calibration data, not a fresh test."]}
    if sha256(PROTOCOL) != protocol_sha:
        raise ValueError("Prospective protocol changed during model fitting")
    write_json(manifest_path, manifest)
    return destination


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, default=ROOT / "models")
    args = parser.parse_args()
    destination = fit_candidates(args.output_root)
    print(json.dumps({"models_directory": str(destination), "frozen_candidates": 8}))


if __name__ == "__main__":
    main()
