"""Export immutable cost stress and selection diagnostics from recorded stakes.

No model fitting, threshold optimization, bet requalification, or stake resizing
occurs. Pooled views retain distinct season bankroll resets and repeat seasonal
cashflows; they must never be added to their constituent seasonal views.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from uuid import uuid4

import numpy as np
import pandas as pd

from .stress import SCENARIOS, stress_group
from .diagnostics import build_diagnostics


PROJECT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = PROJECT / "epl_strategy/results/20261014T095929.849994Z_4c6add9911"
LABELS = ["study", "scope", "strategy_id", "episode_id", "branch", "family", "model_type",
          "feature_group", "split", "outer_season", "policy", "odds_mode", "staking",
          "threshold", "is_tuning_diagnostic", "ledger_role"]
GROUP_KEYS = ["study", "scope", "strategy_id"]


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _close(actual, expected, label: str) -> None:
    if actual is None or expected is None or pd.isna(actual) or pd.isna(expected):
        if (actual is None or pd.isna(actual)) and (expected is None or pd.isna(expected)):
            return
        raise ValueError(f"{label}: missing/nonmissing values differ")
    if not np.isclose(float(actual), float(expected), rtol=1e-8, atol=1e-7):
        raise ValueError(f"{label}: {actual!r} differs from {expected!r}")


def _unique(frame, columns, label):
    if frame[columns].isna().any().any() or frame.duplicated(columns).any():
        raise ValueError(f"{label} requires present, unique keys: {columns}")


def _select(frame: pd.DataFrame, original: dict) -> pd.DataFrame:
    mask = pd.Series(True, index=frame.index)
    for column in GROUP_KEYS:
        mask &= frame[column].eq(original[column])
    if original["scope"] != "pooled_seasons":
        mask &= frame.episode_id.eq(original["episode_id"])
    return frame.loc[mask].copy()


def _verify_group(bets, equity, original):
    _unique(bets, ["episode_id", "match_id"], "strategy bets")
    _unique(equity, ["episode_id", "match_date"], "strategy equity")
    _close(len(bets), original["bet_count"], "saved bet count")
    _close(bets.stake.sum(), original["turnover"], "saved turnover")
    _close(bets.profit.sum(), original["profit"], "saved profit")
    _close(equity.turnover.sum(), original["turnover"], "date turnover")
    _close(equity.profit.sum(), original["profit"], "date profit")
    _close(equity.bet_count.sum(), original["bet_count"], "date bet count")
    _close(equity.matched_matches.sum(), original["matched_valid_odds_count"], "priced opportunity count")
    _close(equity.episode_id.nunique(), original["bankroll_reset_episodes"], "bankroll episode count")
    if len(bets) and not set(bets.episode_id).issubset(set(equity.episode_id)):
        raise ValueError("Bet episodes absent from equity")
    joined = bets[["episode_id", "match_date"]].merge(
        equity[["episode_id", "match_date"]], on=["episode_id", "match_date"],
        how="left", validate="many_to_one", indicator=True)
    if not joined["_merge"].eq("both").all():
        raise ValueError("Bet dates absent from the preserved equity universe")
    _close((bets.stake * (bets.odds - 1) * bets.won).sum(), original["gross_winning_profit_units"], "winning net cash")
    _close((bets.stake * ~bets.won.astype(bool)).sum(), original["gross_losing_loss_units"], "losing stakes")
    _close(bets.expected_net_profit_units.sum(), original["expected_net_profit_total_units"], "model expected cash")


def _verify_baseline(rows, original):
    baseline = [row for row in rows if float(row["fee_rate"]) == 0 and float(row["payout_haircut"]) == 0]
    if len(baseline) != 1:
        raise ValueError("Every strategy requires one zero-cost baseline scenario")
    row = baseline[0]
    # The stress API may name cash/risk columns explicitly as stress/shadow
    # quantities. Check those identities without manufacturing missing metrics.
    fields = {
        "profit": ("profit", "stressed_profit", "stress_profit"),
        "turnover": ("turnover", "original_turnover"),
        "hit_ratio": ("hit_ratio",),
        "trading_frequency": ("trading_frequency",),
        "roi": ("roi", "stressed_roi", "stress_roi"),
        "max_drawdown": ("shadow_max_drawdown", "max_drawdown", "shadow_worst_episode_max_drawdown"),
    }
    for source, choices in fields.items():
        column = next((name for name in choices if name in row), None)
        if column is None:
            raise ValueError(f"Stress baseline lacks required {source} metric")
        _close(row[column], original[source], "zero-cost baseline " + source)
    for name in ("bet_count", "expected_gain_total_units", "expected_loss_total_units",
                 "expected_net_profit_total_units", "expected_roi", "initial_capital_sum_units",
                 "final_capital_sum_units", "min_episode_log_growth", "mean_episode_log_growth"):
        if name in row:
            _close(row[name], original[name], "zero-cost baseline " + name)


def _break_even(bets, original):
    turnover = float(bets.stake.sum())
    profit = float(bets.profit.sum())
    positive_net = float((bets.stake * (bets.odds - 1) * bets.won).sum())
    expected_net = float(bets.expected_net_profit_units.sum())
    expected_win_net = float((bets.probability * bets.stake * (bets.odds - 1)).sum())
    return {**{name: original.get(name, "") for name in LABELS},
            "bet_count": len(bets), "baseline_profit": profit, "turnover": turnover,
            "positive_winning_net_pnl": positive_net,
            "baseline_model_expected_profit": expected_net,
            "model_expected_positive_winning_net_pnl": expected_win_net,
            "fee_break_even_signed": profit / turnover if turnover else None,
            "payout_haircut_break_even_signed": profit / positive_net if positive_net else None,
            "model_implied_fee_break_even_signed": expected_net / turnover if turnover else None,
            "model_implied_payout_haircut_break_even_signed": expected_net / expected_win_net if expected_win_net else None,
            "capacity_status": "no_trades_undefined" if not len(bets) else "baseline_losing_no_nonnegative_capacity" if profit < 0 else "zero_margin" if profit == 0 else "positive_realized_capacity",
            "fee_basis": "fee_rate times original recorded stake on every bet",
            "payout_haircut_basis": "payout_haircut times positive winning net payoff; effective odds=1+(1-h)*(odds-1)",
            "joint_break_even_frontier": "fee_rate = baseline_profit/turnover - payout_haircut*positive_winning_net_pnl/turnover",
            "model_expectation_basis": "conditional on recorded model probabilities and allocated stakes; not predicted terminal wealth",
            "negative_capacity_interpretation": "negative signed capacity means already losing before hypothetical cost"}


def _save(frame, output, name):
    if not isinstance(frame, pd.DataFrame):
        raise TypeError(f"{name} must be a DataFrame")
    if not name.replace("_", "").isalnum():
        raise ValueError(f"Unsafe export table name: {name}")
    frame.to_csv(output / (name + ".csv"), index=False)
    frame.to_parquet(output / (name + ".parquet"), index=False)


def build(source_results: Path = DEFAULT_SOURCE, *, output_dir: Path | None = None,
          bootstrap_samples: int = 1000, random_state: int = 42) -> dict:
    source = Path(source_results).resolve()
    started = datetime.now(timezone.utc)
    if not isinstance(bootstrap_samples, int) or bootstrap_samples < 0:
        raise ValueError("bootstrap_samples must be a nonnegative integer")
    output = Path(output_dir).resolve() if output_dir else PROJECT / "epl_robustness/results" / (started.strftime("%Y%m%dT%H%M%S.%fZ") + "_" + uuid4().hex[:10])
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite an existing output path: {output}")
    protected_roots = [PROJECT / name for name in ("epl_data", "epl_modeling", "epl_live", "epl_strategy", "epl_report")]
    if output == PROJECT or output == source or source in output.parents or any(output == path or path in output.parents for path in protected_roots):
        raise ValueError("Robustness outputs must be separate from preserved source artifacts")
    source_manifest_path = source / "audit_manifest.json"
    source_manifest = json.loads(source_manifest_path.read_text(encoding="utf-8"))
    source_files = {str(path.relative_to(source)): _sha(path) for path in source.rglob("*") if path.is_file()}
    inputs, frames = {}, {}
    for name in ("strategy_metrics", "bets_enriched", "equity_enriched"):
        path = source / (name + ".parquet")
        digest = _sha(path)
        if digest != source_manifest["tables"][name]["parquet_sha256"]:
            raise ValueError(f"Source table differs from its frozen manifest: {name}")
        frame = pd.read_parquet(path)
        if "match_date" in frame:
            frame["match_date"] = pd.to_datetime(frame.match_date).dt.normalize()
        inputs[name] = {"path": str(path), "sha256": digest, "bytes": path.stat().st_size, "rows_before_tuning_exclusion": len(frame)}
        if not frame.is_tuning_diagnostic.eq(frame.study.eq("first_tuning")).all():
            raise ValueError("Tuning diagnostic labels conflict")
        frames[name] = frame.loc[~frame.study.eq("first_tuning")].copy()
        if not frames[name].study.isin(["first", "ablation"]).all():
            raise ValueError("Unexpected study in robustness universe")
        inputs[name]["rows_after_tuning_exclusion"] = len(frames[name])
    metrics, bets, equity = (frames[name] for name in ("strategy_metrics", "bets_enriched", "equity_enriched"))
    _unique(metrics, GROUP_KEYS + ["episode_id"], "strategy scope universe")
    if len(metrics) != 158 or metrics.ledger_role.eq("original_saved_strategy").sum() != 136 or metrics.ledger_role.eq("pooled_view").sum() != 22:
        raise ValueError("Expected 136 original and 22 pooled strategy scope rows")
    scenario_ids = [item["scenario_id"] for item in SCENARIOS]
    scenario_definitions = {item["scenario_id"]: item for item in SCENARIOS}
    if len(scenario_ids) != 9 or len(set(scenario_ids)) != 9:
        raise ValueError("Expected nine distinct, predeclared hypothetical scenarios")
    zero = [item for item in SCENARIOS if item["fee_rate"] == 0 and item["payout_haircut"] == 0]
    if len(zero) != 1:
        raise ValueError("Scenario assumptions require one zero-cost baseline")

    # Preserve the historical study inputs already hashed by the analytics
    # producer. Live ledgers can legitimately acquire later records and are
    # not inputs to this retrospective robustness export.
    historical = {}
    for relative, item in source_manifest["inputs"].items():
        if relative.replace("\\", "/").startswith("epl_modeling/"):
            path = PROJECT / relative
            digest = _sha(path)
            if digest != item["sha256"]:
                raise ValueError(f"Historical input changed since analytics: {relative}")
            historical[relative] = digest
    code_paths = [Path(__file__), Path(__file__).with_name("stress.py"), Path(__file__).with_name("diagnostics.py")]
    code_hashes = {path.name: _sha(path) for path in code_paths}
    scenarios, funding, capacities = [], [], []
    for original in metrics.to_dict("records"):
        selected_bets, selected_equity = _select(bets, original), _select(equity, original)
        _verify_group(selected_bets, selected_equity, original)
        rows, detail = stress_group(selected_bets, selected_equity, original,
                                    bootstrap_samples=bootstrap_samples, random_state=random_state)
        if len(rows) != 9 or set(row["scenario_id"] for row in rows) != set(scenario_ids):
            raise ValueError("Stress core did not return every scenario exactly once")
        for row in rows:
            definition = scenario_definitions[row["scenario_id"]]
            for name in ("fee_rate", "payout_haircut"):
                _close(row[name], definition[name], "declared scenario " + name)
            if any(row.get(name) != original[name] for name in GROUP_KEYS + ["episode_id"]):
                raise ValueError("Stress core changed strategy identity labels")
        _verify_baseline(rows, original)
        scenarios.extend(rows)
        if not isinstance(detail, pd.DataFrame):
            raise TypeError("Funding audit must be a DataFrame")
        funding.append(detail)
        capacities.append(_break_even(selected_bets, original))
    sensitivity = pd.DataFrame(scenarios)
    funding_detail = pd.concat(funding, ignore_index=True)
    break_even = pd.DataFrame(capacities)
    _unique(sensitivity, GROUP_KEYS + ["episode_id", "scenario_id"], "scenario metric rows")
    _unique(break_even, GROUP_KEYS + ["episode_id"], "break-even scope rows")
    _unique(funding_detail, GROUP_KEYS + ["scenario_id", "diagnostic_episode_id"], "funding episode audits")
    expected_funding = len(SCENARIOS) * int(metrics.bankroll_reset_episodes.sum())
    if len(funding_detail) != expected_funding:
        raise ValueError("Funding audit must include every scenario and reset episode")
    if len(sensitivity) != 1422 or len(break_even) != 158:
        raise ValueError("Unexpected cost-sensitivity/break-even cardinality")
    diagnostics = build_diagnostics(metrics.copy(), bets.copy(), equity.copy())
    if not isinstance(diagnostics, dict) or not diagnostics:
        raise TypeError("Diagnostics must return a nonempty dict of DataFrames")
    tables = {"cost_sensitivity": sensitivity, "funding_details": funding_detail, "break_even": break_even}
    if set(tables).intersection(diagnostics):
        raise ValueError("Diagnostic table name collides with stress outputs")
    tables.update(diagnostics)
    for name, frame in tables.items():
        if not isinstance(frame, pd.DataFrame):
            raise TypeError(f"Diagnostic {name} is not a DataFrame")
        if "study" in frame and frame.study.eq("first_tuning").any():
            raise ValueError("Tuning diagnostics contaminated robustness outputs")
    for relative, digest in source_files.items():
        if _sha(source / relative) != digest:
            raise ValueError(f"Preserved analytics source changed: {relative}")
    for relative, digest in historical.items():
        if _sha(PROJECT / relative) != digest:
            raise ValueError(f"Preserved historical source changed: {relative}")
    for path in code_paths:
        if _sha(path) != code_hashes[path.name]:
            raise ValueError(f"Robustness source code changed during computation: {path.name}")
    output.mkdir(parents=True, exist_ok=False)
    for name, frame in tables.items():
        _save(frame, output, name)
    manifest = {"schema_version": 1, "started_at_utc": started.isoformat(),
                "completed_at_utc": datetime.now(timezone.utc).isoformat(), "source_results": str(source),
                "output_directory": str(output), "bootstrap_samples": bootstrap_samples, "random_state": random_state,
                "scenario_assumptions": SCENARIOS,
                "counts": {"strategy_scope_rows": len(metrics), "original_strategy_scope_rows": 136,
                           "pooled_strategy_scope_rows": 22, "excluded_threshold_tuning_scope_rows": 14,
                           "scenario_rows": len(sensitivity), "break_even_rows": len(break_even),
                           "funding_detail_rows": len(funding_detail)},
                "inputs": inputs, "source_manifest_sha256": _sha(source_manifest_path),
                "preserved_source_files": source_files, "preserved_historical_input_sha256": historical,
                "code_sha256": code_hashes,
                "tables": {name: {"rows": len(frame), "columns": list(frame.columns),
                                   "csv_sha256": _sha(output / (name + ".csv")),
                                   "parquet_sha256": _sha(output / (name + ".parquet"))}
                           for name, frame in tables.items()},
                "validation": {"zero_cost_baselines_reproduce_saved_metrics": True,
                               "saved_counts_and_cash_reconciled": True, "all_158_strategy_scopes_preserved": True,
                               "all_9_scenarios_per_scope": True, "all_threshold_tuning_rows_excluded": True,
                               "source_analytics_files_unchanged": True, "historical_inputs_unchanged": True,
                               "no_refit_requalification_or_stake_resizing": True},
                "limitations": ["Scenarios are explicit hypothetical assumptions, not measured fees or executable prices.",
                                "Recorded stakes and selections are fixed, including Kelly stakes inherited from the baseline realized path.",
                                "Funding infeasibility is audited before date settlement; shadow cashflows are not a resized self-financing backtest.",
                                "Pooled views retain per-season resets and repeat their constituent seasonal cashflows; do not aggregate across views or alternatives.",
                                "Selected-bet calibration is conditional on value selection and is not full three-outcome match calibration.",
                                "Date and season deletion diagnostics retain all predeclared alternatives without refitting or winner selection.",
                                "Both studies share historical matches; strategies and overlapping study outputs are not independent evidence.",
                                "All comparisons and conditional bootstrap intervals are exploratory and descriptive."]}
    with (output / "audit_manifest.json").open("x", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2, ensure_ascii=False, allow_nan=False)
        handle.write("\n")
    return {"output_directory": str(output), **manifest["counts"],
            "tables": {name: len(frame) for name, frame in tables.items()}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-results", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output-dir", type=Path, help="New output directory; all existing paths are refused")
    parser.add_argument("--bootstrap-samples", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    print(json.dumps(build(args.source_results, output_dir=args.output_dir,
                           bootstrap_samples=args.bootstrap_samples, random_state=args.seed), indent=2))


if __name__ == "__main__":
    main()
