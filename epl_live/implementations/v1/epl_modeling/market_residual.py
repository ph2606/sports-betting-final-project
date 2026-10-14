"""Regularized, identifiable probability adjustments around a market baseline."""
from __future__ import annotations

import numpy as np
from scipy.optimize import minimize
from scipy.special import logsumexp, softmax
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler

from .metrics import validate_probabilities


def residual_objective(parameters, design, offsets, y, regularization):
    """Mean multinomial loss and gradient; away is the reference adjustment."""
    coefficients = parameters.reshape(design.shape[1], 2)
    logits = offsets.copy()
    logits[:, :2] += design @ coefficients
    normalizers = logsumexp(logits, axis=1)
    loss = np.mean(normalizers - logits[np.arange(len(y)), y])
    loss += 0.5 * regularization * np.sum(coefficients[1:] ** 2)
    probabilities = softmax(logits, axis=1)
    probabilities[np.arange(len(y)), y] -= 1
    gradient = design.T @ probabilities[:, :2] / len(y)
    gradient[1:] += regularization * coefficients[1:]
    return float(loss), gradient.ravel()


class MarketResidualClassifier:
    """Fit feature-driven log-odds adjustments to de-vigged bookmaker probabilities.

    Two adjustment columns correspond to H/D relative to A. The intercept is
    unpenalized; standardized feature coefficients have penalty 1/(C*n_train).
    The baseline is an input at training and prediction time, never a target.
    """
    def __init__(self, C=0.3, max_iter=1000):
        if C <= 0:
            raise ValueError("C must be positive")
        self.C = C
        self.max_iter = max_iter

    def fit(self, features, market_probabilities, y):
        baseline = validate_probabilities(market_probabilities)
        y = np.asarray(y, dtype=int)
        if len(y) != len(baseline) or not len(y) or set(y) != {0, 1, 2}:
            raise ValueError("Training must contain matching labels and all three classes")
        self.imputer_ = SimpleImputer(strategy="median", add_indicator=True, keep_empty_features=True)
        self.scaler_ = StandardScaler()
        transformed = self.scaler_.fit_transform(self.imputer_.fit_transform(features))
        design = np.column_stack([np.ones(len(transformed)), transformed])
        offsets = np.log(np.clip(baseline, 1e-12, 1))
        result = minimize(residual_objective, np.zeros(design.shape[1] * 2),
                          args=(design, offsets, y, 1 / (self.C * len(y))),
                          method="L-BFGS-B", jac=True,
                          options={"maxiter": self.max_iter, "ftol": 1e-11, "gtol": 1e-7})
        if not result.success:
            raise RuntimeError("Market-residual optimization failed: " + str(result.message))
        self.coefficients_ = result.x.reshape(design.shape[1], 2)
        self.classes_ = np.array([0, 1, 2])
        self.optimization_ = {"iterations": int(result.nit), "loss": float(result.fun), "success": bool(result.success)}
        return self

    def decision_function(self, features, market_probabilities):
        baseline = validate_probabilities(market_probabilities)
        transformed = self.scaler_.transform(self.imputer_.transform(features))
        if len(transformed) != len(baseline):
            raise ValueError("Feature and market rows must match")
        design = np.column_stack([np.ones(len(transformed)), transformed])
        logits = np.log(np.clip(baseline, 1e-12, 1))
        logits[:, :2] += design @ self.coefficients_
        return logits

    def predict_proba(self, features, market_probabilities):
        return softmax(self.decision_function(features, market_probabilities), axis=1)
