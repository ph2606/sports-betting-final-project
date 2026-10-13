"""Hand-calculated odds, settlement, capital, and date-bootstrap checks."""
from __future__ import annotations

import math
from pathlib import Path
import sys
import tempfile
import unittest

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backtest import build_odds_panel, simulate_bets


def predictions(rows):
    return pd.DataFrame(rows, columns=["match_id", "match_date", "result", "p_H", "p_D", "p_A"])


def price_panel(rows):
    frame = pd.DataFrame(rows, columns=["match_id", "match_date", "odds_H", "odds_D", "odds_A"])
    frame["snapshot_type"] = "preclosing"
    for outcome in "HDA":
        frame[f"bookmaker_{outcome}"] = "Bet365"
    return frame


class SimulationMathTests(unittest.TestCase):
    def test_one_selection_maximizes_edge_not_probability(self):
        p = predictions([("m1", "2025-08-01", "D", .6, .25, .15)])
        o = price_panel([("m1", "2025-08-01", 2., 6., 5.)])
        bets, equity, result = simulate_bets(p, o, threshold=.1, bootstrap_samples=0)
        self.assertEqual(len(bets), 1)
        self.assertEqual(bets.iloc[0].selection, "D")
        self.assertAlmostEqual(bets.iloc[0].edge, .5)
        self.assertAlmostEqual(result["profit"], 50.)
        self.assertAlmostEqual(result["turnover"], 10.)
        self.assertAlmostEqual(result["roi"], 5.)
        self.assertAlmostEqual(result["log_growth"], math.log(1.05))
        self.assertAlmostEqual(equity.iloc[0].bankroll_end, 1050.)

    def test_same_date_kelly_uses_start_capital_and_is_order_invariant(self):
        p = predictions([("win", "2025-08-01", "H", .6, .2, .2), ("loss", "2025-08-01", "A", .6, .2, .2)])
        o = price_panel([("win", "2025-08-01", 2., 3., 4.), ("loss", "2025-08-01", 2., 3., 4.)])
        first = simulate_bets(p, o, threshold=0, staking="kelly", initial_bankroll=100,
                              max_bet_fraction=.5, bootstrap_samples=0)
        second = simulate_bets(p.iloc[::-1], o.iloc[::-1], threshold=0, staking="kelly", initial_bankroll=100,
                               max_bet_fraction=.5, bootstrap_samples=0)
        np.testing.assert_allclose(first[0].stake, [5., 5.])
        self.assertTrue(first[0].date_start_bankroll.eq(100.).all())
        self.assertAlmostEqual(first[2]["final_bankroll"], 100.)
        pd.testing.assert_frame_equal(first[0], second[0])
        pd.testing.assert_frame_equal(first[1], second[1])

    def test_fixed_stake_capacity_scaling_and_bankruptcy(self):
        p = predictions([("a", "2025-08-01", "A", .6, .2, .2), ("b", "2025-08-01", "A", .6, .2, .2),
                         ("c", "2025-08-02", "H", .6, .2, .2)])
        o = price_panel([(key, day, 2., 3., 4.) for key, day in [("a", "2025-08-01"), ("b", "2025-08-01"), ("c", "2025-08-02")]])
        bets, equity, result = simulate_bets(p, o, threshold=0, initial_bankroll=10., fixed_stake=10., bootstrap_samples=0)
        np.testing.assert_allclose(bets.stake, [5., 5.])
        self.assertTrue(equity.end_bankroll.ge(0).all())
        self.assertTrue((equity.turnover <= equity.start_bankroll + 1e-12).all())
        self.assertEqual(len(bets), 2)
        self.assertEqual(result["final_bankroll"], 0.)
        self.assertEqual(result["max_drawdown"], 1.)
        self.assertTrue(result["bankrupt"])
        self.assertEqual(result["log_growth"], -math.inf)
        self.assertEqual(result["scaled_commitment_dates"], 1)

    def test_quarter_kelly_formula_and_per_bet_cap(self):
        p = predictions([("a", "2025-08-01", "H", .6, .2, .2)])
        o = price_panel([("a", "2025-08-01", 3., 3., 3.)])
        bets, _, result = simulate_bets(p, o, threshold=0, staking="kelly", bootstrap_samples=0)
        # full Kelly=(.6*3-1)/(3-1)=.4; quarter Kelly=.1, capped at .02.
        self.assertAlmostEqual(bets.iloc[0].full_kelly_fraction, .4)
        self.assertAlmostEqual(bets.iloc[0].stake, 20.)
        self.assertAlmostEqual(result["final_bankroll"], 1040.)

    def test_initial_loss_counts_in_drawdown(self):
        p = predictions([("a", "2025-08-01", "A", .6, .2, .2)])
        o = price_panel([("a", "2025-08-01", 2., 3., 4.)])
        _, _, result = simulate_bets(p, o, threshold=0, initial_bankroll=100., bootstrap_samples=0)
        self.assertAlmostEqual(result["max_drawdown"], .1)

    def test_strict_threshold_and_no_bet_fallback_keep_numeric_columns(self):
        p = predictions([("a", "2025-08-01", "H", .5, .3, .2)])
        o = price_panel([("a", "2025-08-01", 3., 3., 3.)])
        for threshold in (.5, math.inf):
            bets, equity, result = simulate_bets(p, o, threshold=threshold, bootstrap_samples=0)
            self.assertTrue(bets.empty)
            self.assertTrue(pd.api.types.is_numeric_dtype(bets.stake))
            self.assertTrue(pd.api.types.is_numeric_dtype(bets.profit))
            self.assertEqual(len(equity), 1)
            self.assertEqual(result["profit"], 0.)
            self.assertEqual(result["turnover"], 0.)
            self.assertIsNone(result["roi"])
            self.assertEqual(result["max_drawdown"], 0.)

    def test_reference_prices_and_no_input_mutation(self):
        p = predictions([("a", "2025-08-01", "H", .6, .2, .2)])
        o = price_panel([("a", "2025-08-01", 3., 3., 4.)])
        o[["ref_odds_H", "ref_odds_D", "ref_odds_A"]] = [2., 3., 4.]
        original_p, original_o = p.copy(deep=True), o.copy(deep=True)
        best = simulate_bets(p, o, threshold=0, bootstrap_samples=0)[2]
        reference = simulate_bets(p, o, threshold=0, odds_mode="reference", bootstrap_samples=0)[2]
        self.assertAlmostEqual(best["profit"], 20.)
        self.assertAlmostEqual(reference["profit"], 10.)
        pd.testing.assert_frame_equal(p, original_p)
        pd.testing.assert_frame_equal(o, original_o)

    def test_bootstrap_resamples_dates_not_individual_bets(self):
        p = predictions([("a", "2025-08-01", "H", .6, .2, .2), ("b", "2025-08-01", "A", .6, .2, .2),
                         ("c", "2025-08-02", "A", .6, .2, .2)])
        o = price_panel([(key, day, 2., 3., 4.) for key, day in [("a", "2025-08-01"), ("b", "2025-08-01"), ("c", "2025-08-02")]])
        first = simulate_bets(p, o, threshold=0, bootstrap_samples=500, random_state=4)[2]
        second = simulate_bets(p, o, threshold=0, bootstrap_samples=500, random_state=4)[2]
        self.assertAlmostEqual(first["roi"], -1 / 3)
        # The mixed win/loss date must stay together; no resample can have ROI>0.
        self.assertEqual(first["bootstrap"]["intervals"]["roi"], [-1., 0.])
        self.assertEqual(first["bootstrap"]["intervals"]["profit"], [-20., 0.])
        self.assertEqual(first["bootstrap"], second["bootstrap"])

    def test_invalid_inputs_and_snapshot_mixing_rejected(self):
        p = predictions([("a", "2025-08-01", "H", .6, .2, .2)])
        o = price_panel([("a", "2025-08-01", 2., 3., 4.)])
        for probabilities in ([.6, .2, .1], [1.1, -.2, .1], [np.nan, .5, .5]):
            bad = p.copy()
            bad[["p_H", "p_D", "p_A"]] = probabilities
            with self.assertRaises(ValueError):
                simulate_bets(bad, o, threshold=0, bootstrap_samples=0)
        mismatched = o.copy()
        mismatched["match_date"] = "2025-08-02"
        with self.assertRaises(ValueError):
            simulate_bets(p, mismatched, threshold=0, bootstrap_samples=0)
        mixed = pd.concat([o, o.assign(match_id="b", snapshot_type="closing")])
        with self.assertRaises(ValueError):
            simulate_bets(p, mixed, threshold=0, bootstrap_samples=0)
        invalid = o.copy()
        invalid["odds_A"] = np.inf
        bets, _, result = simulate_bets(p, invalid, threshold=0, bootstrap_samples=0)
        self.assertTrue(bets.empty)
        self.assertEqual(result["invalid_odds_rows_excluded"], 1)


class OddsPanelTests(unittest.TestCase):
    def make_sources(self, root):
        folder = root / "data/processed/football_data"
        folder.mkdir(parents=True)
        matches = pd.DataFrame([
            ("m1", "2025-07-22"), ("m2", "2025-07-23"), ("m3", "2025-08-15"), ("m4", "2025-08-16")],
            columns=["source_match_key", "match_date"])
        matches["season"] = "2025-26"
        matches["division"] = "E0"
        matches["FTR"] = "H"
        matches["completed_asof"] = True
        quotes = []

        def add(match, prefix, name, prices, snapshot="preclosing", aggregate=False, exchange=False):
            row = matches.loc[matches.source_match_key.eq(match)].iloc[0].to_dict()
            row.update(source_prefix=prefix, bookmaker_or_aggregate=name, snapshot_type=snapshot,
                       is_market_aggregate=aggregate, is_exchange=exchange, pinnacle_stale_warning=False,
                       quote_timestamp_utc=None, decimal_odds_home=prices[0], decimal_odds_draw=prices[1], decimal_odds_away=prices[2])
            quotes.append(row)

        for match in ("m1", "m2", "m3"):
            add(match, "B365", "Bet365", (2., 4., 4.))
        add("m1", "PS", "Pinnacle", (4., 4., 4.))
        add("m2", "PS", "Pinnacle", (100., 100., 100.))
        add("m2", "Max", "Market maximum", (100., 100., 100.), aggregate=True)
        add("m2", "BFE", "Betfair Exchange", (100., 100., 100.), exchange=True)
        add("m2", "ZZ", "Unknown", (100., 100., 100.))
        add("m2", "SO", "Sporting Odds", (100., np.nan, 100.))
        add("m2", "WH", "William Hill", (100., np.inf, 100.))
        add("m2", "WH", "William Hill", (99., 99., 99.), snapshot="closing")
        add("m2", "B365", "Bet365", (2., 4., 4.), snapshot="closing")
        add("m3", "WH", "William Hill", (3., 3., 3.))
        add("m4", "WH", "William Hill", (2., 4., 4.))
        matches.to_parquet(folder / "matches_current_cohort.parquet", index=False)
        pd.DataFrame(quotes).to_parquet(folder / "match_odds_1x2_long.parquet", index=False)

    def test_individual_complete_triplets_cutoff_and_reference(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_sources(root)
            panel, audit = build_odds_panel(root)
            lookup = panel.set_index("match_id")
            self.assertEqual(set(lookup.index), {"m1", "m2", "m3"})
            self.assertEqual(lookup.loc["m1", "bookmaker_H"], "Pinnacle")
            self.assertAlmostEqual(lookup.loc["m2", "odds_H"], 2.)
            self.assertEqual(lookup.loc["m2", "bookmaker_H"], "Bet365")
            self.assertEqual(audit["rejections"]["unreliable_pinnacle"], 1)
            self.assertEqual(audit["rejections"]["invalid_or_incomplete_triplet"], 2)
            self.assertEqual(audit["excluded_matches_missing_reference"], 1)
            np.testing.assert_allclose(panel[["ref_p_H", "ref_p_D", "ref_p_A"]].sum(axis=1), 1.)
            self.assertEqual(len(build_odds_panel(root, require_reference=False)[0]), 4)
            closing, _ = build_odds_panel(root, snapshot="closing")
            self.assertEqual(closing.iloc[0].odds_H, 99.)
            self.assertTrue(closing.snapshot_type.eq("closing").all())

    def test_equal_payout_arbitrage_is_mathematical_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_sources(root)
            panel, audit = build_odds_panel(root)
            row = panel.set_index("match_id").loc["m3"]
            self.assertTrue(row.mathematical_arb_candidate)
            self.assertAlmostEqual(row.arb_inverse_odds_sum, 5 / 6)
            payouts = [row[f"arb_stake_weight_{outcome}"] * row[f"odds_{outcome}"] for outcome in "HDA"]
            np.testing.assert_allclose(payouts, [1.2, 1.2, 1.2])
            self.assertAlmostEqual(sum(row[f"arb_stake_weight_{outcome}"] for outcome in "HDA"), 1.)
            self.assertTrue(row.quotes_asynchronous_or_unverified)
            self.assertFalse(row.executable_arbitrage_verified)
            self.assertFalse(audit["arbitrage_execution_verified"])
            self.assertTrue(any(candidate["match_id"] == "m3" for candidate in audit["candidate_arb_matches"]))


if __name__ == "__main__":
    unittest.main()
