"""Protocol-level guards beyond fitting and zero-difference smoke checks."""
import math
import unittest

import numpy as np
import pandas as pd

from epl_modeling.ablation import (
    FEATURE_GROUPS, SOURCE_COVERAGE, complete_history_mask,
    date_stratified_paired_intervals,
)


class ExploratoryProtocolGuards(unittest.TestCase):
    def test_bootstrap_preserves_date_clusters_and_match_weighted_season_strata(self):
        # Each season has a single date. The first has TWO candidate wins; the
        # second has ONE reference win. Stratified whole-date draws must keep
        # all three observations, giving +1/3 accuracy rather than 0 or +/-1.
        identity = pd.DataFrame({
            "outer_season": ["2022-23", "2022-23", "2023-24"],
            "match_id": ["home", "draw", "away"],
            "match_date": pd.to_datetime(["2022-08-01", "2022-08-01", "2023-08-01"]),
            "result": ["H", "D", "A"],
        })
        candidate, reference = identity.copy(), identity.copy()
        candidate[["p_H", "p_D", "p_A"]] = [[.9, .05, .05], [.05, .9, .05], [.9, .05, .05]]
        reference[["p_H", "p_D", "p_A"]] = [[.05, .05, .9], [.9, .05, .05], [.05, .05, .9]]
        intervals = {row["metric"]: row for row in date_stratified_paired_intervals(
            candidate, reference, n_bootstrap=100, seed=9)}
        for key in ("difference", "ci_lower", "ci_upper"):
            self.assertAlmostEqual(intervals["accuracy"][key], 1 / 3)
            self.assertAlmostEqual(intervals["log_loss"][key], -math.log(18) / 3)

    def test_complete_history_mask_ignores_outcomes_and_model_predictions(self):
        frame = pd.DataFrame(1., index=range(3), columns=FEATURE_GROUPS["combined"])
        for column in SOURCE_COVERAGE:
            frame[column] = 8. if "observed_matches" in column else 0.
        frame["result"] = ["H", "D", "A"]
        frame[["p_H", "p_D", "p_A"]] = [.6, .2, .2]
        before = complete_history_mask(frame)
        altered = frame.copy()
        altered["result"] = ["unobserved", "A", "H"]
        altered[["p_H", "p_D", "p_A"]] = [.01, .01, .98]
        pd.testing.assert_series_equal(before, complete_history_mask(altered))
        self.assertTrue(before.all())
        altered.loc[1, "feat_away_fpl_roll10_observed_matches"] = np.nan
        self.assertEqual(complete_history_mask(altered).tolist(), [True, False, True])

    def test_paired_intervals_reject_population_or_settlement_mismatch(self):
        frame = pd.DataFrame({
            "outer_season": ["2022-23"] * 3, "match_id": ["a", "b", "c"],
            "match_date": pd.to_datetime(["2022-08-01"] * 3),
            "result": ["H", "D", "A"], "p_H": .4, "p_D": .3, "p_A": .3,
        })
        bad_result = frame.copy()
        bad_result.loc[0, "result"] = "D"
        bad_date = frame.copy()
        bad_date.loc[0, "match_date"] = pd.Timestamp("2022-08-02")
        for reference in (frame.iloc[:2], bad_result, bad_date):
            with self.assertRaises(ValueError):
                date_stratified_paired_intervals(frame, reference, n_bootstrap=10)


if __name__ == "__main__":
    unittest.main()
