"""Independent identities/cashflow checks and conditional date bootstrap.

This reads the completed NBA inverse experiment and writes no historical input.
The intervals hold the selected models/signals/stakes fixed; they do not correct
the post-hoc choice to examine strategies selected because they went bankrupt.
"""
from pathlib import Path
import hashlib
import json

import numpy as np
import pandas as pd

OUT = Path(__file__).parent
ROOT = OUT.parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def near(actual, expected, label):
    if not np.allclose(actual, expected, atol=1e-7, rtol=1e-10):
        raise AssertionError(label)


def main():
    source = json.loads((ROOT / "final_deliverables/nba_evidence.json").read_text())
    saved = {r["season"]: r for r in source["rolling_annual"]["records"]}
    inventory = pd.read_csv(OUT / "all_rolling_account_inventory.csv")
    reconciliation = pd.read_csv(OUT / "all_source_reconciliations.csv")
    metrics = pd.read_csv(OUT / "inverse_metrics.csv")
    predictions = pd.read_csv(OUT / "all_rolling_predictions.csv")
    assert len(inventory) == 36 and len(reconciliation) == 18
    assert inventory.source_fixed_return_matches_printed_precision.all()
    assert reconciliation.source_fixed_return_matches_printed_precision.all()
    for r in inventory.itertuples():
        expected_features = saved[r.season]["n_features_calibration" if r.branch == "cal" else "n_features_accuracy"]
        assert r.n_features == expected_features == len(json.loads(r.selected_features))
    for (season, branch), p in predictions.groupby(["season", "branch"]):
        assert len(p) == saved[season]["n_games"]
        assert not p.GAME_ID.duplicated().any()
        assert p.p_home.between(0, 1).all()
    exact_zero = inventory.loc[inventory.exact_zero]
    assert set(exact_zero.season) == {"2017-18"} and set(exact_zero.branch) == {"cal", "acc"}
    assert exact_zero.staking.eq("fixed").all() and len(exact_zero) == 2
    assert len(inventory.loc[inventory.rounds_to_zero_cents]) == 2
    intervals, checked_bets = [], 0
    for branch in ("cal", "acc"):
        p = predictions.loc[predictions.season.eq("2017-18") & predictions.branch.eq(branch)].reset_index(drop=True)
        ph = p.p_home.to_numpy()
        home = ph > 1 / p.odds_home.to_numpy()
        away = ~home & ((1 - ph) > 1 / p.odds_away.to_numpy())
        expected_side = np.where(home, "H", np.where(away, "A", ""))
        selected_probability = np.where(home, ph, 1 - ph)
        allowed = (expected_side != "") & (np.abs(selected_probability - .5) > 0)
        signal = pd.read_csv(OUT / f"2017-18_{branch}_fixed_all_signals.csv")
        near(signal.game_order, np.flatnonzero(allowed), "Full-season signals")
        assert signal.original_selection.tolist() == expected_side[allowed].tolist()
        near(signal.original_probability, selected_probability[allowed], "Original probabilities")
        near(signal.opposite_probability, 1 - selected_probability[allowed], "Complement probabilities")
        assert (signal.original_selection != signal.opposite_selection).all()
        original = pd.read_csv(OUT / f"2017-18_{branch}_fixed_original_bets.csv")
        for mode in ("original", "opposite_recorded_prefix", "opposite_full_horizon"):
            b = pd.read_csv(OUT / f"2017-18_{branch}_fixed_{mode}_bets.csv")
            e = pd.read_csv(OUT / f"2017-18_{branch}_fixed_{mode}_equity.csv")
            m = metrics.loc[metrics.branch.eq(branch) & metrics["mode"].eq(mode)].iloc[0]
            assert len(e) == 1075 and not e.game_order.duplicated().any()
            assert b.stake.gt(0).all() and (b.stake <= b.start_bankroll + 1e-8).all()
            assert e.end_bankroll.ge(-1e-8).all()
            near(e.start_bankroll, np.r_[10000, e.end_bankroll.to_numpy()[:-1]], "Sequential funding")
            near(e.end_bankroll - e.start_bankroll, e.profit, "Equity profit")
            correct_odds = np.where(b.selection.eq("H"), b.odds_home, b.odds_away)
            correct_hits = (b.selection.eq("H") & b.TARGET.eq(1)) | (b.selection.eq("A") & b.TARGET.eq(0))
            near(b.odds, correct_odds, "Actual selected back odds")
            assert b.won.tolist() == correct_hits.tolist()
            near(b.profit, b.stake * (b.odds * correct_hits - 1), "Back payoff")
            near(b.expected_gain, b.probability * b.stake * (b.odds - 1), "Expected gain")
            near(b.expected_loss, (1 - b.probability) * b.stake, "Expected loss")
            near(m.final_capital, 10000 + b.profit.sum(), "Final capital")
            near(m.profit, b.profit.sum(), "Profit total")
            near(m.turnover, b.stake.sum(), "Turnover")
            near(m.roi_on_stakes, b.profit.sum() / b.stake.sum(), "Stake ROI")
            near(m.hit_ratio, correct_hits.mean(), "Bet hit ratio")
            near(m.trading_frequency, len(b) / 1075, "Trading frequency")
            path = np.r_[10000, e.end_bankroll]
            near(m.max_drawdown, np.max(1 - path / np.maximum.accumulate(path)), "Drawdown")
            checked_bets += len(b)
            if mode == "opposite_recorded_prefix":
                assert b.game_order.tolist() == original.game_order.tolist()
                near(b.stake, original.stake, "Matched original exposures")
                assert (b.won.to_numpy() == ~original.won.to_numpy()).all()
            if mode == "opposite_full_horizon":
                assert b.game_order.tolist() == signal.game_order.tolist()
                near(b.stake, 100, "Full-horizon flat requests")
                assert b.game_order.max() > original.game_order.max()
                e["n_bets"] = e.game_order.isin(set(b.game_order)).astype(int)
                e["wins"] = e.game_order.map(b.set_index("game_order").won).fillna(False).astype(int)
                dates = e.groupby("GAME_DATE", sort=True).agg(profit=("profit", "sum"), turnover=("stake", "sum"),
                    n_bets=("n_bets", "sum"), wins=("wins", "sum"), games=("game_order", "size"))
                rng = np.random.default_rng(42)
                sampled = rng.integers(0, len(dates), size=(9999, len(dates)))
                sums = dates.to_numpy()[sampled].sum(axis=1)
                roi = sums[:, 0] / sums[:, 1]
                hit = sums[:, 3] / sums[:, 2]
                frequency = sums[:, 2] / sums[:, 4]
                for metric, samples, observed in (("roi_on_stakes", roi, m.roi_on_stakes),
                        ("hit_ratio", hit, m.hit_ratio), ("trading_frequency", frequency, m.trading_frequency)):
                    intervals.append({"season": "2017-18", "branch": branch, "mode": mode, "metric": metric,
                        "value": float(observed), "ci_lower": float(np.quantile(samples, .025)),
                        "ci_upper": float(np.quantile(samples, .975)), "n_bootstrap": 9999,
                        "method": "Whole-match-date percentile bootstrap, selected models/signals/stakes fixed; no selection or fitting adjustment"})
    pd.DataFrame(intervals).to_csv(OUT / "conditional_uncertainty.csv", index=False)
    current = predictions.loc[predictions.season.eq("2017-18") & predictions.branch.eq("cal")]
    overround = 1 / current.odds_home + 1 / current.odds_away - 1
    summary = {"status": "passed", "all_18_saved_annual_fixed_returns_reconciled": True,
        "all_18_feature_counts_and_fixture_counts_reconciled": True, "rolling_accounts_inventoried": 36,
        "exact_zero_accounts": 2, "round_to_zero_additional_accounts": 0,
        "smallest_nonzero_Kelly_capital": float(inventory.loc[inventory.staking.eq("kelly"), "final_capital"].min()),
        "checked_inverse_and_original_positive_stake_bets": checked_bets,
        "verified_full_season_continuation_past_original_bankruptcy": True,
        "opposite_recorded_prefix_uses_actual_other_team_odds": True,
        "source_2017_mean_overround": float(overround.mean()), "source_2017_median_overround": float(overround.median()),
        "source_2017_negative_overround_games": int(overround.lt(0).sum()),
        "bootstrap_intervals": intervals,
        "selection_caveat": "The original failures were selected after examining outcomes. These are descriptive counterfactuals; bootstrap intervals do not create an untouched holdout.",
        "verification_code_sha256": sha(Path(__file__)),
        "input_sha256": {p.name: sha(p) for p in sorted(OUT.glob("*.csv")) if p.name != "conditional_uncertainty.csv"},
        "uncertainty_sha256": sha(OUT / "conditional_uncertainty.csv")}
    (OUT / "audit_summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return summary


if __name__ == "__main__":
    main()
