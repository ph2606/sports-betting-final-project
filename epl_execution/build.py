"""Build a frozen-probability price replay and exact quote attribution study."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import platform

import numpy as np
import pandas as pd

from epl_strategy.metrics import summarize_strategy
from epl_strategy_validation.build import publish_latest
from .diagnostics import (book_concentration, closing_reference_diagnostics,
    load_archived_closing_reference, payoff_attribution, quote_diagnostics)
from .replay import fixed_exposure_reference, reference_replay

ROOT = Path(__file__).resolve().parents[1]
SCOPES = ("single", "continuous", "seasonal")
MODES = ("original", "reference_replay", "fixed_exposure_reference")
INITIAL = 100000.0
COMPARISON_FIELDS = ("bet_count", "winning_bet_count", "hit_ratio", "trading_frequency",
    "turnover", "profit", "roi", "expected_roi", "expected_gain_total_units",
    "expected_loss_total_units", "expected_net_profit_total_units", "expected_gain_per_trade_units",
    "expected_loss_per_trade_units", "avg_winning_gain_units", "avg_losing_loss_units",
    "max_drawdown", "final_capital_sum_units", "return_on_initial_capital", "funding_feasible")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False, default=str) + "\n", encoding="utf-8")


def save(output, name, frame):
    frame.to_csv(output / (name + ".csv"), index=False)
    frame.to_parquet(output / (name + ".parquet"), index=False)


def code_paths(root=ROOT):
    folder = root / "epl_execution"
    return sorted(p for p in folder.rglob("*") if p.is_file()
        and p.suffix in {".py", ".md", ".txt"} and "results" not in p.relative_to(folder).parts)


def checked_output(output, root=ROOT):
    """Allow new immutable run directories only inside this module's results."""
    output = Path(output).resolve()
    parent = (root / "epl_execution/results").resolve()
    if parent not in output.parents:
        raise ValueError("Execution runs must be new directories under epl_execution/results")
    if output.exists():
        raise FileExistsError("Refusing to overwrite a completed or partial run: " + str(output))
    return output


def metadata(account):
    return {key: account[key] for key in ("account_id", "scope", "season", "episode_id")}


def metric_row(account, metrics, mode):
    config = account["config"]
    flat = {k: json.dumps(v, sort_keys=True) if isinstance(v, (list, dict)) else v for k, v in config.items()}
    flat["catalog_definition_status"] = flat.pop("study_status", None)
    flat["frozen_original_odds_mode"] = config["odds_mode"]
    if mode != "original": flat["odds_mode"] = "reference"
    return {**flat, **metrics, **metadata(account), "strategy_id": config["strategy_id"],
        "execution_mode": mode, "initial_bankroll": INITIAL,
        "study_status": "retrospective_frozen_probability_quote_sensitivity_not_new_holdout",
        "verified_execution": False}


def ledger_metadata(frame, account, mode):
    result = frame.copy()
    # Continuous ledgers retain the genuine season of each fixture/date.
    for key in ("account_id", "scope", "episode_id"):
        result[key] = account[key]
    result["scope_season"] = account["season"]
    result["strategy_id"] = account["config"]["strategy_id"]
    result["execution_mode"] = mode
    return result


def comparison(account, original, reference, fixed, original_bets, reference_bets):
    old = original_bets.set_index("match_id").selection
    new = reference_bets.set_index("match_id").selection
    common = old.index.intersection(new.index)
    retained = int(old.reindex(common).eq(new.reindex(common)).sum())
    row = {**metadata(account), "strategy_id": account["config"]["strategy_id"],
        "frozen_original_odds_mode": account["config"]["odds_mode"],
        "retained_same_outcome_bets": retained, "changed_outcome_bets": len(common) - retained,
        "original_only_matches": len(old.index.difference(new.index)),
        "reference_only_matches": len(new.index.difference(old.index)),
        "reference_minus_original_profit": reference["profit"] - original["profit"],
        "realized_quote_uplift_units": fixed["actual_quote_uplift_units"],
        "model_expected_quote_uplift_units": fixed["model_expected_quote_uplift_units"],
        "fixed_funding_feasible": fixed["funding_feasible"],
        "fixed_minimum_additional_opening_cash_units": fixed["minimum_additional_opening_cash_units"],
        "fixed_first_shortfall_date": fixed["first_shortfall_date"],
        "fixed_shadow_final_balance": fixed["shadow_final_balance"],
        "fixed_shadow_min_balance": fixed["shadow_min_balance"],
        "fixed_shadow_return": fixed["shadow_return"]}
    for prefix, values in (("original", original), ("reference", reference), ("fixed", fixed)):
        row.update({prefix + "_" + field: values.get(field) for field in COMPARISON_FIELDS})
    return row


def build(output=None, *, bootstrap_samples=1000, update_latest=False):
    from .inputs import load_inputs, source_paths
    start = datetime.now(timezone.utc)
    if isinstance(bootstrap_samples, bool) or not isinstance(bootstrap_samples, int) or bootstrap_samples < 0:
        raise ValueError("bootstrap_samples must be a nonnegative integer")
    output = checked_output(output or ROOT / "epl_execution/results" / start.strftime("%Y%m%dT%H%M%S.%fZ"))
    dependencies = [p for name in ("epl_strategy", "epl_strategy_lab", "epl_strategy_validation")
        for p in (ROOT / name).glob("*.py")]
    dependencies += [ROOT / "epl_modeling/backtest.py"]
    methods = [ROOT / name for name in ("epl_strategy/METHODOLOGY.md", "epl_strategy_lab/PROTOCOL.md",
        "epl_strategy_validation/PROTOCOL.md")]
    protected = sorted(set(source_paths(ROOT) + dependencies + methods + code_paths()))
    before = {path: sha(path) for path in protected}
    inventory = set(code_paths())
    study = load_inputs(ROOT)
    if set(study["source_paths"]) != set(source_paths(ROOT)):
        raise AssertionError("Consumed inputs differ from the upfront protected inventory")
    output.mkdir(parents=True)
    catalog, models, opportunities = study["catalog"], study["models"], study["opportunities"]
    write_json(output / "catalog.json", catalog)
    versions = {name: version(name) for name in ("numpy", "pandas", "pyarrow", "matplotlib", "plotly",
        "reportlab", "python-docx", "XlsxWriter", "pypdf")}
    versions["python"] = platform.python_version()
    provenance = {"started_at_utc": start.isoformat(), "versions": versions,
        "initial_bankroll_per_account": INITIAL, "metric_bootstrap_samples": bootstrap_samples,
        "models_refitted": False, "new_holdout": False, "verified_execution": False,
        "inputs_and_code_sha256": {p.relative_to(ROOT).as_posix(): digest for p, digest in before.items()}}
    write_json(output / "source_provenance.json", provenance)
    rows = {scope: [] for scope in SCOPES}
    ledgers = {f"{kind}_{mode}_{scope}": [] for kind in ("bets", "equity")
        for mode in ("reference", "fixed_reference") for scope in SCOPES}
    comparisons, attributions, books = [], [], []
    for index, account in enumerate(study["accounts"], 1):
        config, universe = account["config"], account["opportunities"]
        original_bets = account["original_bets"]
        original = {**account["original_metrics"], "funding_feasible": True, "is_policy_replay": True,
            "analysis_type": "exact_frozen_original_account", "metric_status": "frozen_original"}
        rb, re = reference_replay(config, models, universe, scope=account["scope"],
            episode_id=account["episode_id"], initial_bankroll=INITIAL)
        reference = summarize_strategy(rb, re, prediction_count=len(universe), matched_valid_odds_count=len(universe),
            initial_bankroll=INITIAL, bootstrap_samples=bootstrap_samples, random_state=42)
        reference.update({"funding_feasible": True, "is_policy_replay": True,
            "analysis_type": "reference_price_selection_and_sizing_replay", "metric_status": "reference_price_replay"})
        fixed, fb, fe = fixed_exposure_reference(config, original_bets, universe,
            episode_id=account["episode_id"], initial_bankroll=INITIAL, bootstrap_samples=bootstrap_samples)
        for mode, values in (("original", original), ("reference_replay", reference), ("fixed_exposure_reference", fixed)):
            rows[account["scope"]].append(metric_row(account, values, mode))
        for kind, mode, frame in (("bets", "reference", rb), ("equity", "reference", re),
                ("bets", "fixed_reference", fb), ("equity", "fixed_reference", fe)):
            ledgers[f"{kind}_{mode}_{account['scope']}"].append(ledger_metadata(frame, account,
                "reference_replay" if mode == "reference" else "fixed_exposure_reference"))
        comparisons.append(comparison(account, original, reference, fixed, original_bets, rb))
        info = {**metadata(account), "strategy_id": config["strategy_id"]}
        attributions.append(payoff_attribution(original_bets, universe, **{key: info[key]
            for key in ("account_id", "strategy_id", "scope", "season")}))
        books.append(book_concentration(original_bets, universe, info))
        if index % 28 == 0 or index == len(study["accounts"]):
            print(f"Replayed {index}/{len(study['accounts'])} original account scopes", flush=True)
    tables = {"metrics_" + scope: pd.DataFrame(rows[scope]) for scope in SCOPES}
    tables.update({name: pd.concat(parts, ignore_index=True) for name, parts in ledgers.items()})
    tables.update({"execution_comparison": pd.DataFrame(comparisons),
        "payoff_attribution": pd.DataFrame(attributions), "book_concentration": pd.concat(books, ignore_index=True)})
    summary, outcomes, quote_books = quote_diagnostics(opportunities, scope="four_season_common_quotes")
    single_summary, _, _ = quote_diagnostics(opportunities.loc[opportunities.season.eq("2025-26")], scope="single_2025_26")
    summary["single_2025_26"] = single_summary
    write_json(output / "quote_summary.json", summary)
    tables["quote_outcomes"], tables["quote_book_concentration"] = outcomes, quote_books
    closing, closing_sources = load_archived_closing_reference(ROOT, opportunities)
    if not set(closing_sources).issubset(before): raise AssertionError("Closing source was not protected upfront")
    closing_summary, closing_outcomes = closing_reference_diagnostics(opportunities, closing, scope="four_season_same_book")
    write_json(output / "closing_quote_summary.json", closing_summary)
    tables["archived_closing_reference"], tables["closing_quote_outcomes"] = closing, closing_outcomes
    for name, frame in tables.items(): save(output, name, frame)
    graph = tables["equity_reference_continuous"][["strategy_id", "match_date", "end_bankroll"]].copy()
    graph["is_initial"] = False
    anchor = pd.DataFrame({"strategy_id": sorted(graph.strategy_id.unique()),
        "match_date": opportunities.match_date.min() - pd.Timedelta(days=1), "end_bankroll": INITIAL, "is_initial": True})
    pd.concat([graph, anchor], ignore_index=True).sort_values(["strategy_id", "match_date"]).to_csv(
        output / "graph_equity_reference_continuous.csv", index=False)
    write_json(output / "coverage.json", {"catalog_strategies": 84, "compatible_four_season_strategies": 56,
        "account_scopes": 364, "metric_rows": 1092, "modes": list(MODES), "matches": len(opportunities),
        "match_dates": int(opportunities.match_date.nunique()), "scope_accounts": {s: len(rows[s]) // 3 for s in SCOPES},
        "native_season_counts": {str(s): int(n) for s, n in opportunities.groupby("season").size().items()}})
    from .audit import audit_export
    write_json(output / "independent_audit.json", audit_export(output, root=ROOT))
    from .report import build_report
    report = build_report(output)
    changed = [p.relative_to(ROOT).as_posix() for p, digest in before.items() if not p.exists() or sha(p) != digest]
    if changed or set(code_paths()) != inventory:
        raise RuntimeError("Protected source/code changed during the build: " + str(changed))
    manifest = {**provenance, "completed_at_utc": datetime.now(timezone.utc).isoformat(),
        "duration_seconds": (datetime.now(timezone.utc) - start).total_seconds(), "protected_hashes_unchanged": True,
        "report": report, "row_counts": {name: len(frame) for name, frame in tables.items()},
        "output_sha256": {p.relative_to(output).as_posix(): sha(p) for p in sorted(output.rglob("*")) if p.is_file()}}
    write_json(output / "manifest.json", manifest)
    if update_latest: publish_latest(output)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--bootstrap-samples", type=int, default=1000)
    parser.add_argument("--update-latest", action="store_true")
    args = parser.parse_args()
    result = build(args.output, bootstrap_samples=args.bootstrap_samples, update_latest=args.update_latest)
    print(json.dumps({"completed": result["completed_at_utc"], "rows": result["row_counts"], "report": result["report"]}, indent=2))


if __name__ == "__main__": main()
