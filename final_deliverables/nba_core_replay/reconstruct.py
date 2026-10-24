"""Read-only fixed-parameter audit of the supplied NBA notebook's core run.

No feature search, parameter optimization or new selection is performed. The
saved two/four-feature branches and saved best_params are refitted exactly as
the notebook specifies, with ten seed-averaged probabilities. Results are
usable only if all four final bankroll values match the supplied outputs.
"""
from pathlib import Path
import hashlib
from importlib.metadata import version
import json
import os
import warnings
import argparse

import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits
from sklearn.metrics import log_loss, brier_score_loss


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "ML Sports"
OUT = Path(__file__).parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ece_ordinary(y, p):
    bins = np.clip(np.digitize(p, np.linspace(0, 1, 21)[1:-1]), 0, 19)
    value = 0
    occupied = 0
    for i in range(20):
        mask = bins == i
        if mask.any():
            occupied += 1
            value += mask.mean() * abs(y[mask].mean() - p[mask].mean())
    return float(value), occupied


def classify_existing():
    """Audit probability scores from the already saved fixed-parameter refit."""
    predictions = pd.read_csv(OUT / "predictions_native.csv")
    metrics = pd.read_csv(OUT / "metrics_all4.csv")
    rows = []
    for tag, group in predictions.groupby("branch", sort=False):
        p, y = group.p_home.to_numpy(), group.TARGET.to_numpy()
        ordinary, occupied = ece_ordinary(y, p)
        rows.append({"series": tag, "n_games": len(group), "accuracy": float((p.round() == y).mean()),
            "log_loss": float(log_loss(y, p)), "brier_binary": float(brier_score_loss(y, p)),
            "ece_binary_20": ordinary, "occupied_bins": occupied,
            "guarded_ece": ordinary if occupied >= 16 else 1.0,
            "provenance": "fixed_parameter_refit",
            "matches_original_saved_outputs": bool(metrics.loc[metrics.branch.eq(tag), "final_capital_matches_saved_to_cent"].all())})
    group = predictions.loc[predictions.branch.eq("Calibration")]
    inv_home, inv_away = 1 / group.odds_home.to_numpy(), 1 / group.odds_away.to_numpy()
    q, y = inv_home / (inv_home + inv_away), group.TARGET.to_numpy()
    ordinary, occupied = ece_ordinary(y, q)
    rows.append({"series": "Normalized bookmaker odds", "n_games": len(group),
        "accuracy": float((q.round() == y).mean()), "log_loss": float(log_loss(y, q)),
        "brier_binary": float(brier_score_loss(y, q)), "ece_binary_20": ordinary,
        "occupied_bins": occupied, "guarded_ece": ordinary if occupied >= 16 else 1.0,
        "provenance": "direct_read_only_derivation_from_native_2018_odds", "matches_original_saved_outputs": True})
    pd.DataFrame(rows).to_csv(OUT / "classification_metrics_2018.csv", index=False)
    return rows


def main():
    source_names = ["Data.ipynb", "best_params.json", "regular_season_totals_2010_2024.csv", "OddsData.sqlite"]
    before = {name: sha(SOURCE / name) for name in source_names}
    nb = json.loads((SOURCE / "Data.ipynb").read_text(encoding="utf-8"))
    env = {"__name__": "__notebook_audit__"}
    old_cwd = Path.cwd()
    try:
        os.chdir(SOURCE)
        for cell in (1, 5, 8, 10, 11, 14, 17):
            exec(compile("".join(nb["cells"][cell]["source"]), f"supplied_notebook_cell_{cell}", "exec"), env)
        env["best_params"] = json.loads((SOURCE / "best_params.json").read_text())
        env["best_B"], env["best_C"] = "LR", "SVM"
        env["subset_B"] = ["ORTG", "FG3M"]
        env["subset_C"] = ["ORTG", "PREV_SEASON_WP", "FG3M", "TOV"]
        exec(compile("".join(nb["cells"][18]["source"]), "supplied_notebook_cell_18", "exec"), env)
    finally:
        os.chdir(old_cwd)
    frame = env["betting_df"]
    native = frame[["GAME_ID", "GAME_DATE", "HOME_ABBR", "AWAY_ABBR", "TARGET", "ML_Home", "ML_Away"]].copy().reset_index(drop=True)
    native["game_order"] = np.arange(len(native))
    native["odds_home"] = env["american_to_decimal"](native.ML_Home.to_numpy())
    native["odds_away"] = env["american_to_decimal"](native.ML_Away.to_numpy())
    expected = {("Calibration", "fixed"): 10097.74, ("Calibration", "kelly"): 6500.40,
                ("Accuracy", "fixed"): 12502.98, ("Accuracy", "kelly"): 4488.59}
    all_metrics, all_predictions, reconciliations = [], [], []
    for tag, name, columns, param_key in (("Calibration", "LR", env["subset_B"], "B_LR"),
                                         ("Accuracy", "SVM", env["subset_C"], "C_SVM")):
        probabilities = []
        for seed in range(10):
            with threadpool_limits(limits=1):
                estimator = env["fixed"](name, env["best_params"][param_key], len(columns), seed)
                estimator.fit(env["final_train"][columns], env["final_train"].TARGET.to_numpy())
                probabilities.append(estimator.predict_proba(frame[columns])[:, 1])
            print(f"{tag} seed {seed + 1}/10", flush=True)
        p_home = np.mean(probabilities, axis=0)
        y = native.TARGET.to_numpy()
        ordinary, occupied = ece_ordinary(y, p_home)
        pred = native.copy()
        pred["branch"], pred["model"] = tag, name
        pred["p_home"], pred["p_away"] = p_home, 1 - p_home
        all_predictions.append(pred)
        for rule in ("fixed", "kelly"):
            capital, bets, equity = 10000.0, [], []
            for row, ph in zip(native.to_dict("records"), p_home):
                pa, choice = 1 - ph, None
                if ph > 1 / row["odds_home"]:
                    choice, p, odds, won = "H", ph, row["odds_home"], row["TARGET"] == 1
                elif pa > 1 / row["odds_away"]:
                    choice, p, odds, won = "A", pa, row["odds_away"], row["TARGET"] == 0
                start = capital
                stake = profit = 0.0
                if choice and abs(p - .5) > 0:
                    request = 100.0 if rule == "fixed" else max(0, .125 * (p * odds - 1) / (odds - 1) * capital)
                    stake = min(request, capital)
                    capital -= stake
                    if won:
                        capital += stake * odds
                    profit = capital - start
                    bets.append({**row, "branch": tag, "model": name, "staking": rule, "selection": choice,
                        "probability": p, "odds": odds, "stake": stake, "won": won, "profit": profit,
                        "start_bankroll": start, "end_bankroll": capital,
                        "expected_gain": stake * p * (odds - 1), "expected_loss": stake * (1 - p)})
                equity.append({**row, "branch": tag, "model": name, "staking": rule, "start_bankroll": start,
                               "end_bankroll": capital, "stake": stake, "profit": profit})
            b, e = pd.DataFrame(bets), pd.DataFrame(equity)
            original = env["simulate"](p_home, native.odds_home.to_numpy(), native.odds_away.to_numpy(), y, rule)
            assert np.allclose(original["curve"], e.end_bankroll, atol=1e-8, rtol=0)
            path = np.r_[10000, e.end_bankroll.to_numpy()]
            peak = np.maximum.accumulate(path)
            drawdown = float(np.max(1 - path / peak))
            turnover, net = float(b.stake.sum()), capital - 10000
            metrics = {"branch": tag, "model": name, "staking": rule, "n_predictions": len(native),
                "n_bets": len(b), "wins": int(b.won.sum()), "hit_ratio": float(b.won.mean()),
                "trading_frequency": len(b) / len(native), "initial_capital": 10000,
                "final_capital": capital, "profit": net, "turnover": turnover,
                "roi_on_stakes": net / turnover, "return_on_initial_capital": net / 10000,
                "expected_gain_per_trade": float(b.expected_gain.mean()),
                "expected_loss_per_trade": float(b.expected_loss.mean()),
                "expected_net_per_trade": float((b.expected_gain - b.expected_loss).mean()),
                "avg_winning_gain": float(b.loc[b.won, "profit"].mean()),
                "avg_losing_loss": float(-b.loc[~b.won, "profit"].mean()),
                "max_drawdown": drawdown, "min_stake": float(b.stake.min()), "max_stake": float(b.stake.max()),
                "prediction_accuracy": float((p_home.round() == y).mean()),
                "ordinary_binary_ece_20": ordinary, "occupied_bins_out_of_20": occupied,
                "saved_ece_penalized_definition": float(env["classwise_ece"](y, p_home)),
                "source_saved_final_capital": expected[tag, rule],
                "final_capital_matches_saved_to_cent": round(capital, 2) == expected[tag, rule]}
            all_metrics.append(metrics)
            stem = tag.lower() + "_" + rule
            prefix = "" if metrics["final_capital_matches_saved_to_cent"] else "unreconciled_"
            b.to_csv(OUT / (prefix + "bets_" + stem + ".csv"), index=False)
            e.to_csv(OUT / (prefix + "equity_" + stem + ".csv"), index=False)
            print(metrics, flush=True)
    metrics = pd.DataFrame(all_metrics)
    metrics.to_csv(OUT / "metrics_all4.csv", index=False)
    pd.concat(all_predictions, ignore_index=True).to_csv(OUT / "predictions_native.csv", index=False)
    classification = classify_existing()
    after = {name: sha(SOURCE / name) for name in source_names}
    assert before == after
    summary = {"method": "fixed supplied parameters and supplied feature subsets, refitted with ten seed averaging; no retuning",
        "source_notebook_cells": [1, 5, 8, 10, 11, 14, 17, 18, 19, 20],
        "status": "reconciled_to_all_four_saved_bankroll_outputs" if metrics.final_capital_matches_saved_to_cent.all() else "mismatch_do_not_replace_saved_results",
        "all_four_saved_finals_match_to_cent": bool(metrics.final_capital_matches_saved_to_cent.all()),
        "individually_reconciled_branches": [tag for tag, part in metrics.groupby("branch") if part.final_capital_matches_saved_to_cent.all()],
        "unreconciled_branches": [tag for tag, part in metrics.groupby("branch") if not part.final_capital_matches_saved_to_cent.all()],
        "classification_metrics_2018": classification,
        "observed_fit_warning": "Every reconstructed SVM seed reached its supplied maximum of200000iterations; the notebook suppressed these warnings. Original library versions and serialized weights are not supplied.",
        "source_sha256_before_and_after": before,
        "environment": {name: version(name) for name in ("pandas", "numpy", "scipy", "scikit-learn", "threadpoolctl")},
        "caveats": ["These are newly audited fixed-parameter refits, not supplied serialized model weights.",
            "Source simulator is sequential game-level, including same-date cash reuse; it differs from EPL date-start joint allocation.",
            "Source field called roi is return on starting capital, not profit divided by stake turnover.",
            "Source ECE can return 1.0 as a bin-occupancy penalty; ordinary binary ECE is separately reported.",
            "All monetary values remain in original 10,000-unit initial-capital scale."],
        "output_sha256": {p.name: sha(p) for p in OUT.glob("*.csv")}}
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summarize-existing", action="store_true")
    arguments = parser.parse_args()
    if arguments.summarize_existing:
        rows = classify_existing()
        summary = json.loads((OUT / "summary.json").read_text())
        summary["classification_metrics_2018"] = rows
        summary["output_sha256"]["classification_metrics_2018.csv"] = sha(OUT / "classification_metrics_2018.csv")
        (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(rows, indent=2))
    else:
        main()
