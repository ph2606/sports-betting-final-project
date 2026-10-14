import unittest

import numpy as np
import pandas as pd

from epl_modeling.ablation import FEATURE_GROUPS, SOURCE_COVERAGE, complete_history_mask, date_stratified_paired_intervals, fold_roles


class AblationProtocolTests(unittest.TestCase):
    def test_all_outer_splits_are_ordered_and_disjoint(self):
        for year in (2022, 2023, 2024, 2025):
            roles = fold_roles(year)
            all_seasons = [item for values in roles.values() for item in values]
            self.assertEqual(len(all_seasons), len(set(all_seasons)))
            self.assertLess(max(roles["train"]), min(roles["tune"]))
            self.assertLess(max(roles["tune"]), min(roles["calibration"]))
            self.assertLess(max(roles["calibration"]), min(roles["evaluation"]))

    def test_source_groups_keep_controls_and_performance_additions(self):
        for names in FEATURE_GROUPS.values():
            self.assertTrue(set(SOURCE_COVERAGE).issubset(names))
            self.assertEqual(len(names), len(set(names)))
        self.assertEqual(set(FEATURE_GROUPS["combined"]), set(FEATURE_GROUPS["team_xg"]) | set(FEATURE_GROUPS["team_player"]))
        self.assertFalse(any("fpl_total_points" in name or "us_xg_for" in name for name in FEATURE_GROUPS["team"]))

    def test_complete_history_is_an_all_source_common_intersection(self):
        frame = pd.DataFrame(1.0, index=range(3), columns=FEATURE_GROUPS["combined"])
        for side in ("home", "away"):
            for source in ("us", "fpl"):
                frame[f"feat_{side}_{source}_roll10_observed_matches"] = 8
        frame.loc[1, "feat_home_fpl_roll10_observed_matches"] = 7
        frame.loc[2, "feat_diff_roll10_us_xg_for"] = np.nan
        self.assertEqual(complete_history_mask(frame).tolist(), [True, False, False])

    def test_identical_forecasts_have_exactly_zero_paired_difference(self):
        frame = pd.DataFrame({"outer_season": ["2022-23"]*6 + ["2023-24"]*6,
                              "match_id": [str(i) for i in range(12)],
                              "match_date": pd.to_datetime(["2022-08-01"]*3 + ["2022-08-02"]*3 + ["2023-08-01"]*3 + ["2023-08-02"]*3),
                              "result": ["H", "D", "A"]*4, "p_H": 0.5, "p_D": 0.25, "p_A": 0.25})
        rows = date_stratified_paired_intervals(frame, frame.copy(), n_bootstrap=100)
        for row in rows:
            self.assertEqual(row["difference"], 0)
            self.assertEqual(row["ci_lower"], 0)
            self.assertEqual(row["ci_upper"], 0)


if __name__ == "__main__":
    unittest.main()
