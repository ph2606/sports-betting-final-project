import unittest

import numpy as np
from scipy.optimize import check_grad
from scipy.special import softmax

from epl_modeling.market_residual import MarketResidualClassifier, residual_objective


class MarketResidualTests(unittest.TestCase):
    def test_analytic_gradient_matches_finite_differences(self):
        rng = np.random.default_rng(42)
        design = np.column_stack([np.ones(30), rng.normal(size=(30, 4))])
        offsets = np.log(softmax(rng.normal(size=(30, 3)), axis=1))
        labels = np.resize([0, 1, 2], 30)
        parameters = rng.normal(size=10)
        args = (design, offsets, labels, 0.03)
        error = check_grad(lambda p: residual_objective(p, *args)[0],
                           lambda p: residual_objective(p, *args)[1], parameters)
        self.assertLess(error, 1e-6)

    def test_zero_adjustment_recovers_market(self):
        rng = np.random.default_rng(5)
        baseline = softmax(rng.normal(size=(30, 3)), axis=1)
        features = rng.normal(size=(30, 2))
        model = MarketResidualClassifier().fit(features, baseline, np.resize([0, 1, 2], 30))
        model.coefficients_[:] = 0
        np.testing.assert_allclose(model.predict_proba(features, baseline), baseline, atol=1e-12)

    def test_model_learns_known_feature_adjustments(self):
        rng = np.random.default_rng(42)
        features = rng.normal(size=(1500, 2))
        baseline = np.tile([0.45, 0.25, 0.30], (len(features), 1))
        logits = np.log(baseline)
        logits[:, 0] += features[:, 0]
        truth = softmax(logits, axis=1)
        labels = np.array([rng.choice(3, p=row) for row in truth])
        model = MarketResidualClassifier(C=1).fit(features, baseline, labels)
        predicted = model.predict_proba(features, baseline)
        self.assertLess(np.mean((predicted - truth) ** 2), np.mean((baseline - truth) ** 2))
        np.testing.assert_allclose(predicted.sum(axis=1), 1)


if __name__ == "__main__":
    unittest.main()
