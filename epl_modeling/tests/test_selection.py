import unittest

import numpy as np
import pandas as pd

from epl_modeling.selection import bh_adjust, chronological_folds, filter_features


class SelectionTests(unittest.TestCase):
    def test_adjusted_pvalues_are_valid(self):
        p = np.array([0.001, 0.04, 0.3, 1])
        q = bh_adjust(p)
        self.assertTrue(np.all(q >= p))
        self.assertTrue(np.all(q <= 1))
        self.assertTrue(np.all(np.diff(q) >= 0))

    def test_filters_remove_constant_and_duplicate_features(self):
        rng = np.random.default_rng(42)
        x = rng.normal(size=200)
        frame = pd.DataFrame({"season": np.repeat(["2017-18", "2018-19", "2019-20", "2020-21"], 50),
                              "result": np.resize(["H", "D", "A"], 200),
                              "feat_x": x, "feat_duplicate": x, "feat_constant": 1.0})
        kept, audit = filter_features(frame)
        self.assertEqual(len(kept), 1)
        self.assertIn("constant_in_training", audit.drop_reason.tolist())
        self.assertIn("spearman_redundancy", audit.drop_reason.tolist())

    def test_fold_dates_are_strictly_ordered(self):
        frame = pd.DataFrame({"season": ["2017-18", "2018-19", "2019-20", "2020-21"],
                              "match_date": pd.to_datetime(["2017-08-01", "2018-08-01", "2019-08-01", "2020-08-01"])})
        for earlier, later, _ in chronological_folds(frame):
            self.assertLess(frame.loc[earlier, "match_date"].max(), frame.loc[later, "match_date"].min())


if __name__ == "__main__":
    unittest.main()
