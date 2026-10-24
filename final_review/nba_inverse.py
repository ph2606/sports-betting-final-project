"""Audit and invert the saved NBA rolling rules that actually exhausted cash.

Original NBA inputs are read only. The supplied rolling logistic algorithm is
replayed unchanged, with additional return values to preserve its probabilities.
Opposite bets use the other team's quoted back odds; profit is not sign-flipped.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import warnings

import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "ML Sports"
OUT = Path(__file__).with_name("nba_results")
INITIAL = 10_000.0
FIXED = 100.0


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def jsave(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False, default=str) + "\n", encoding="utf-8")


def source_environment():
    notebook = json.loads((SOURCE / "Data.ipynb").read_text(encoding="utf-8"))
    env = {"__name__": "__nba_rolling_inverse_audit__"}
    old_cwd = Path.cwd()
    try:
        os.chdir(SOURCE)
        for index in (1, 5, 17):
            exec(compile("".join(notebook["cells"][index]["source"]), f"supplied_cell_{index}", "exec"), env)
        env["name_to_abbr"] = dict(zip(env["df"].TEAM_NAME, env["df"].TEAM_ABBREVIATION))

        def pdate(row):
            year = int(row.SEASON_YEAR_own[:4])
            month, day = int(row.Date[-4:-2]), int(row.Date[-2:])
            return pd.Timestamp(year=year if month >= 10 else year + 1, month=month, day=day)

        env["pdate"] = pdate
        odds_source = "".join(notebook["cells"][22]["source"])
        odds_source = odds_source.replace('sqlite3.connect("OddsData.sqlite")',
            'sqlite3.connect("file:OddsData.sqlite?mode=ro", uri=True)')
        exec(compile(odds_source, "supplied_cell_22_read_only", "exec"), env)
        env["conn"].close()
    finally:
        os.chdir(old_cwd)
    original = "".join(notebook["cells"][21]["source"])
    augmented = original.replace(
        'out = {"season": bet_s, "n": len(bd), "nB": len(B), "nC": len(C)}',
        'out = {"season": bet_s, "n": len(bd), "nB": len(B), "nC": len(C)}\n'
        '    out["_audit_probabilities"] = {}\n'
        '    out["_audit_columns"] = {"cal": list(B), "acc": list(C)}\n'
        '    out["_audit_native"] = bd[["GAME_ID", "GAME_DATE", "HOME_ABBR", "AWAY_ABBR", "TARGET", "ML_Home", "ML_Away"]].copy()')
    augmented = augmented.replace('out[tag+"_ece"] = classwise_ece(won, p)',
        'out["_audit_probabilities"][tag] = p.copy()\n        out[tag+"_ece"] = classwise_ece(won, p)')
    if augmented == original or '_audit_native' not in augmented:
        raise AssertionError("Supplied rolling function structure changed")
    exec(compile(augmented, "supplied_cell_21_with_read_only_audit_returns", "exec"), env)
    return env, {"original_cell21_sha256": hashlib.sha256(original.encode()).hexdigest(),
        "audit_augmented_cell21_sha256": hashlib.sha256(augmented.encode()).hexdigest(),
        "algorithm_changes": "None; added probability, feature-name and native-identity return values only"}


def native_signals(native, p_home):
    rows = []
    for number, (row, ph) in enumerate(zip(native.to_dict("records"), p_home)):
        oh, oa = float(row["odds_home"]), float(row["odds_away"])
        selection = None
        if ph > 1 / oh:
            selection, selected_p, selected_odds = "H", ph, oh
        elif 1 - ph > 1 / oa:
            selection, selected_p, selected_odds = "A", 1 - ph, oa
        if selection and abs(selected_p - .5) > 0:
            rows.append({**row, "game_order": number, "original_selection": selection,
                "original_probability": float(selected_p), "original_odds": selected_odds,
                "opposite_selection": "A" if selection == "H" else "H",
                "opposite_probability": float(1 - selected_p),
                "opposite_odds": oa if selection == "H" else oh})
    return pd.DataFrame(rows)


def replay(native, signals, *, season, branch, mode, staking="fixed", prefix_stakes=None):
    """Keep the original signal; choose its other team at actual recorded odds."""
    selected = signals.set_index("game_order")
    cash, bets, equity = INITIAL, [], []
    for number, row in enumerate(native.to_dict("records")):
        opening, stake, profit = cash, 0.0, 0.0
        if number in selected.index and (prefix_stakes is None or number in prefix_stakes):
            signal = selected.loc[number]
            opposite = mode.startswith("opposite")
            choice = signal.opposite_selection if opposite else signal.original_selection
            probability = float(signal.opposite_probability if opposite else signal.original_probability)
            odds = float(signal.opposite_odds if opposite else signal.original_odds)
            if prefix_stakes is not None:
                request = float(prefix_stakes[number])
            elif staking == "fixed":
                request = FIXED
            else:
                request = max(0.0, .125 * (probability * odds - 1) / (odds - 1) * cash)
            stake = min(cash, request)
            won = (choice == "H" and row["TARGET"] == 1) or (choice == "A" and row["TARGET"] == 0)
            if stake > 0:
                cash -= stake
                if won:
                    cash += stake * odds
                profit = cash - opening
                bets.append({**row, "game_order": number, "season": season, "branch": branch,
                    "mode": mode, "staking": staking, "selection": choice, "probability": probability,
                    "odds": odds, "stake": stake, "won": bool(won), "profit": profit,
                    "start_bankroll": opening, "end_bankroll": cash,
                    "original_selection": signal.original_selection,
                    "original_probability": float(signal.original_probability),
                    "original_odds": float(signal.original_odds),
                    "expected_gain": probability * stake * (odds - 1),
                    "expected_loss": (1 - probability) * stake})
        equity.append({**row, "game_order": number, "season": season, "branch": branch, "mode": mode,
            "staking": staking, "start_bankroll": opening, "stake": stake, "profit": profit,
            "end_bankroll": cash})
    b, e = pd.DataFrame(bets), pd.DataFrame(equity)
    path = np.r_[INITIAL, e.end_bankroll.to_numpy()]
    max_drawdown = float(np.max(1 - path / np.maximum.accumulate(path)))
    turnover = float(b.stake.sum()) if len(b) else 0.0
    metrics = {"season": season, "branch": branch, "mode": mode, "staking": staking,
        "n_predictions": len(native), "full_horizon_original_signals": len(signals), "n_bets": len(b),
        "wins": int(b.won.sum()) if len(b) else 0, "hit_ratio": float(b.won.mean()) if len(b) else None,
        "trading_frequency": len(b) / len(native), "initial_capital": INITIAL,
        "final_capital": cash, "profit": cash - INITIAL, "turnover": turnover,
        "roi_on_stakes": (cash - INITIAL) / turnover if turnover else None,
        "return_on_initial_capital": (cash - INITIAL) / INITIAL,
        "expected_gain_per_trade": float(b.expected_gain.mean()) if len(b) else None,
        "expected_loss_per_trade": float(b.expected_loss.mean()) if len(b) else None,
        "avg_winning_gain": float(b.loc[b.won, "profit"].mean()) if len(b) and b.won.any() else None,
        "avg_losing_loss": float(-b.loc[~b.won, "profit"].mean()) if len(b) and (~b.won).any() else None,
        "max_drawdown": max_drawdown,
        "first_zero_game_order": int(e.loc[e.end_bankroll.le(0), "game_order"].iloc[0]) if e.end_bankroll.le(0).any() else None,
        "funding_convention": "Original NBA game-sequential settlement; cash clamping, no borrowing",
        "price_basis": "Original single-source home/away moneyline pair; no verified execution timestamps",
        "expectation_basis": "Same original forecast; opposite outcome probability equals one minus original selected probability"}
    assert np.allclose(np.r_[INITIAL, e.end_bankroll.to_numpy()[:-1]], e.start_bankroll)
    assert np.all(e.stake <= e.start_bankroll + 1e-9) and np.all(e.end_bankroll >= -1e-9)
    assert np.isclose(INITIAL + sum(e.profit), cash, atol=1e-8)
    return b, e, metrics


def main(output=OUT):
    output = Path(output).resolve()
    if output.exists() and (output / "summary.json").exists():
        raise ValueError("Do not overwrite a completed NBA inversion run")
    output.mkdir(parents=True, exist_ok=True)
    protected = {SOURCE / name: sha(SOURCE / name) for name in ("Data.ipynb", "OddsData.sqlite", "regular_season_totals_2010_2024.csv")}
    evidence_path = ROOT / "final_deliverables/nba_evidence.json"
    evidence = json.loads(evidence_path.read_text())
    protected[evidence_path] = sha(evidence_path)
    env, augmentation = source_environment()
    native_games = env["games"]
    years = sorted(native_games.SEASON_YEAR_own.unique())
    saved = {r["season"]: r for r in evidence["rolling_annual"]["records"]}
    records, metrics, inventory, probabilities = [], [], [], []
    for season in saved:
        i = years.index(season) - 4
        tr, va, te, bet = years[i:i + 2], years[i + 2], years[i + 3], years[i + 4]
        with threadpool_limits(limits=1):
            r = env["run_window"](native_games, env["g2_all"], env["diff_stats"], tr, va, te, bet,
                env["classwise_ece"], env["simulate"], env["american_to_decimal"])
        native = r["_audit_native"].reset_index(drop=True)
        native["odds_home"] = env["american_to_decimal"](native.ML_Home)
        native["odds_away"] = env["american_to_decimal"](native.ML_Away)
        print(f"Replayed source rolling NBA season {season}", flush=True)
        for branch, saved_key in (("cal", "calibration_return_on_initial_capital"), ("acc", "accuracy_return_on_initial_capital")):
            matched = round(float(r[branch + "_fixed"]), 2) == round(100 * saved[season][saved_key], 2)
            p = r["_audit_probabilities"][branch]
            pred = native.copy()
            pred["season"], pred["branch"], pred["p_home"] = season, branch, p
            probabilities.append(pred)
            signals = native_signals(native, p)
            for staking in ("fixed", "kelly"):
                b, e, m = replay(native, signals, season=season, branch=branch, mode="original", staking=staking)
                assert np.allclose(e.end_bankroll, r[f"curve_{branch}_{staking}"], atol=1e-7, rtol=0)
                original_zero = m["final_capital"] == 0
                inventory.append({"season": season, "branch": branch, "staking": staking,
                    "final_capital": m["final_capital"], "source_fixed_return_percent": 100 * saved[season][saved_key],
                    "replayed_fixed_return_percent": r[branch + "_fixed"], "source_fixed_return_matches_printed_precision": matched,
                    "exact_zero": original_zero, "rounds_to_zero_cents": round(m["final_capital"], 2) == 0,
                    "n_features": r["nB"] if branch == "cal" else r["nC"],
                    "selected_features": json.dumps(r["_audit_columns"][branch])})
                if not original_zero:
                    continue
                if not matched:
                    raise AssertionError("A zero source season did not reconcile to its printed fixed-stake return")
                stem = f"{season}_{branch}_{staking}"
                metrics.append(m)
                b.to_csv(output / (stem + "_original_bets.csv"), index=False)
                e.to_csv(output / (stem + "_original_equity.csv"), index=False)
                for mode, prefix in (("opposite_recorded_prefix", b.set_index("game_order").stake.to_dict()),
                                     ("opposite_full_horizon", None)):
                    ib, ie, im = replay(native, signals, season=season, branch=branch, mode=mode,
                        staking=staking, prefix_stakes=prefix)
                    metrics.append(im)
                    ib.to_csv(output / (stem + "_" + mode + "_bets.csv"), index=False)
                    ie.to_csv(output / (stem + "_" + mode + "_equity.csv"), index=False)
                signals.to_csv(output / (stem + "_all_signals.csv"), index=False)
            records.append({"season": season, "branch": branch, "n_games": len(native),
                "source_fixed_return_matches_printed_precision": matched,
                "source_fixed_return_percent": 100 * saved[season][saved_key],
                "replayed_fixed_return_percent": float(r[branch + "_fixed"]),
                "selected_features": r["_audit_columns"][branch]})
    pd.DataFrame(inventory).to_csv(output / "all_rolling_account_inventory.csv", index=False)
    pd.DataFrame(records).to_csv(output / "all_source_reconciliations.csv", index=False)
    pd.DataFrame(metrics).to_csv(output / "inverse_metrics.csv", index=False)
    pd.concat(probabilities, ignore_index=True).to_csv(output / "all_rolling_predictions.csv", index=False)
    if any(sha(path) != digest for path, digest in protected.items()):
        raise AssertionError("An original NBA input changed")
    frame = pd.DataFrame(inventory)
    summary = {"completed_at_utc": datetime.now(timezone.utc).isoformat(), "scope": "All nine source rolling NBA seasons, both LR feature-selection branches, fixed and eighth-Kelly stakes",
        "algorithm": augmentation, "all_fixed_branches_match_source_printed_precision": bool(pd.DataFrame(records).source_fixed_return_matches_printed_precision.all()),
        "original_annual_accounts_audited": len(inventory), "exact_zero_accounts": int(frame.exact_zero.sum()),
        "rounded_zero_accounts": int(frame.rounds_to_zero_cents.sum()), "inverse_metric_rows": len(metrics),
        "source_sha256": {p.relative_to(ROOT).as_posix(): h for p, h in protected.items()},
        "definition": "Back the opposite team at its recorded opposing moneyline, retaining the original qualifying signal. Not a negative copy of original PnL.",
        "modes": {"opposite_recorded_prefix": "Only original positive-stake bets; request their recorded stakes at opposite odds, subject to opposite account cash.",
                  "opposite_full_horizon": "Continue the frozen original signal through the whole season, including fixtures after original bankruptcy; request fixed 100 and clamp to own available cash."},
        "expectations": "Inverse p is one minus original selected p. The original model generally does not endorse taking this contrarian position.",
        "limits": ["Post-hoc selection of bankrupt histories; no new independent holdout or selected live policy.",
                   "Single-source archived odds and sequential source funding, not verified executable fills or observed game-time settlement.",
                   "Kelly is bounded away from an all-in request and may become economically tiny without literally reaching zero.",
                   "No unreconciled SVM prediction is used; these are the source rolling logistic-only extensions."],
        "output_sha256": {p.name: sha(p) for p in sorted(output.glob("*")) if p.is_file()}}
    jsave(output / "summary.json", summary)
    print(json.dumps({"exact_zero_accounts": summary["exact_zero_accounts"], "all_fixed_reconciled": summary["all_fixed_branches_match_source_printed_precision"], "metrics": metrics}, indent=2))
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUT)
    args = parser.parse_args()
    main(args.output)
