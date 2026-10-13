"""Explicit multiclass metrics and held-out temperature calibration."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.optimize import minimize_scalar
from scipy.special import softmax
from sklearn.metrics import accuracy_score, log_loss

CLASSES = ("H", "D", "A")


def encode_results(results):
    labels = np.asarray(results)
    if not np.isin(labels, CLASSES).all():
        raise ValueError("Results must be H, D or A")
    return np.array([CLASSES.index(value) for value in labels], dtype=int)


def validate_probabilities(probabilities):
    p = np.asarray(probabilities, dtype=float)
    if p.ndim != 2 or p.shape[1] != 3 or not np.isfinite(p).all():
        raise ValueError("Expected a finite n-by-3 probability matrix in H/D/A order")
    if (p < 0).any() or (p > 1).any() or not np.allclose(p.sum(axis=1), 1, atol=1e-8):
        raise ValueError("Probabilities must be in [0,1] and sum to one")
    return p


def classwise_ece(y, probabilities, n_bins=10):
    """Mean of three one-vs-rest ECEs with fixed equal-width probability bins."""
    p = validate_probabilities(probabilities)
    y = np.asarray(y, dtype=int)
    if len(y) != len(p) or not len(y) or not np.isin(y, range(3)).all():
        raise ValueError("Expected matching nonempty encoded labels")
    if n_bins < 1:
        raise ValueError("n_bins must be positive")
    errors = []
    for k in range(3):
        # Include p=1 in the final bin, without silently dropping boundary values.
        bins = np.minimum((p[:, k] * n_bins).astype(int), n_bins - 1)
        error = 0.0
        for b in range(n_bins):
            mask = bins == b
            if mask.any():
                error += mask.mean() * abs(p[mask, k].mean() - (y[mask] == k).mean())
        errors.append(error)
    return float(np.mean(errors))


def classification_metrics(y, probabilities):
    p = validate_probabilities(probabilities)
    y = np.asarray(y, dtype=int)
    target = np.eye(3)[y]
    return {
        "n_matches": int(len(y)),
        "accuracy": float(accuracy_score(y, p.argmax(axis=1))),
        "classwise_ece_10": classwise_ece(y, p, 10),
        "classwise_ece_5": classwise_ece(y, p, 5),
        "classwise_ece_15": classwise_ece(y, p, 15),
        "log_loss": float(log_loss(y, p, labels=[0, 1, 2])),
        # Unscaled multiclass Brier: sum over classes, then mean over matches; range [0,2].
        "brier_score": float(np.mean(np.sum((p - target) ** 2, axis=1))),
    }


def estimator_logits(estimator, frame):
    """Align sklearn class columns; avoid SVC's internal shuffled calibration."""
    classes = list(estimator.classes_)
    if set(classes) != {0, 1, 2}:
        raise ValueError("Every estimator must be trained on all three outcomes")
    if hasattr(estimator, "predict_proba"):
        values = np.log(np.clip(estimator.predict_proba(frame), 1e-12, 1))
    else:
        values = np.asarray(estimator.decision_function(frame), dtype=float)
    return values[:, [classes.index(k) for k in range(3)]]


@dataclass
class TemperatureCalibrator:
    temperature: float = 1.0

    def fit(self, logits, y):
        logits = np.asarray(logits, dtype=float)
        y = np.asarray(y, dtype=int)
        if logits.shape != (len(y), 3) or not np.isfinite(logits).all() or not len(y):
            raise ValueError("Invalid held-out calibration data")
        result = minimize_scalar(
            lambda log_t: log_loss(y, softmax(logits / np.exp(log_t), axis=1), labels=[0, 1, 2]),
            bounds=(-3, 3), method="bounded", options={"xatol": 1e-8},
        )
        if not result.success:
            raise RuntimeError("Temperature calibration failed")
        self.temperature = float(np.exp(result.x))
        return self

    def predict_proba(self, logits):
        if self.temperature <= 0:
            raise ValueError("Temperature must be positive")
        return softmax(np.asarray(logits, dtype=float) / self.temperature, axis=1)


def reliability_bins(y, probabilities, n_bins=10):
    p = validate_probabilities(probabilities)
    y = np.asarray(y, dtype=int)
    rows = []
    for k, label in enumerate(CLASSES):
        bins = np.minimum((p[:, k] * n_bins).astype(int), n_bins - 1)
        for b in range(n_bins):
            mask = bins == b
            rows.append({"outcome": label, "bin": b, "lower": b / n_bins,
                         "upper": (b + 1) / n_bins, "count": int(mask.sum()),
                         "mean_probability": float(p[mask, k].mean()) if mask.any() else np.nan,
                         "observed_frequency": float((y[mask] == k).mean()) if mask.any() else np.nan})
    return rows
