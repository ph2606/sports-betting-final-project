import unittest

import numpy as np
from scipy.special import softmax

from epl_modeling.metrics import TemperatureCalibrator, classwise_ece, classification_metrics


class MetricsTests(unittest.TestCase):
    def test_perfect_and_boundary_probabilities(self):
        y = np.array([0, 1, 2])
        p = np.eye(3)
        self.assertEqual(classwise_ece(y, p), 0)
        self.assertEqual(classification_metrics(y, p)["brier_score"], 0)

    def test_classwise_ece_is_not_top_label_ece(self):
        y = np.array([0, 1, 2])
        p = np.tile([0.6, 0.3, 0.1], (3, 1))
        expected = np.mean(np.abs(np.array([0.6, 0.3, 0.1]) - 1 / 3))
        self.assertAlmostEqual(classwise_ece(y, p), expected)

    def test_temperature_preserves_predictions_and_improves_fit(self):
        rng = np.random.default_rng(42)
        latent = rng.normal(size=(1000, 3))
        true_p = softmax(latent, axis=1)
        y = np.array([rng.choice(3, p=row) for row in true_p])
        overconfident = latent * 4
        calibrator = TemperatureCalibrator().fit(overconfident, y)
        before = softmax(overconfident, axis=1)
        after = calibrator.predict_proba(overconfident)
        np.testing.assert_array_equal(before.argmax(axis=1), after.argmax(axis=1))
        self.assertGreater(calibrator.temperature, 1)
        self.assertLess(classification_metrics(y, after)["log_loss"], classification_metrics(y, before)["log_loss"])

    def test_invalid_probability_rows_are_rejected(self):
        with self.assertRaises(ValueError):
            classwise_ece([0], [[0.5, 0.5, 0.5]])


if __name__ == "__main__":
    unittest.main()
