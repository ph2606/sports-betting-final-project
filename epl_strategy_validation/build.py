"""Build an immutable four-season account study and conditional selection audit."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import platform
import shutil
from uuid import uuid4

import numpy as np
import pandas as pd

from epl_strategy.metrics import reconstruct_equity, summarize_strategy
from .analysis import season_stability
from .audit import audit_export
from .inputs import (LAB_EXPORT_RELATIVE, SEASONS, SEASON_MATCH_COUNTS, SEASON_DATE_COUNTS,
                     SOURCE_FILES, compatible_catalog, load_inputs)
from .replay import replay
from .selection import run_selection_audit


ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False, default=str) + "\n", encoding="utf-8")


def save(output, name, frame):
    frame.to_csv(output / (name + ".csv"), index=False)
    frame.to_parquet(output / (name + ".parquet"), index=False)


def code_paths():
    return sorted(p for p in Path(__file__).parent.rglob("*") if p.is_file()
                  and p.suffix in {".py", ".md", ".txt"}
                  and "results" not in p.relative_to(Path(__file__).parent).parts)


def publish_latest(output: Path, root: Path = ROOT):
    """Publish verified report copies under an easy-to-find stable folder."""
    manifest = json.loads((output / "manifest.json").read_text())
    target = root / "reports/latest"
    target.mkdir(parents=True, exist_ok=True)
    mappings = {"EPL_Project_Report.pdf": "report/validation_report.pdf",
                "EPL_Project_Report.docx": "report/validation_report.docx"}
    previous_path = target / "manifest.json"
    if previous_path.exists():
        previous = json.loads(previous_path.read_text())
        for name, item in previous.get("copies", {}).items():
            if (target / name).exists() and sha(target / name) != item["sha256"]:
                raise RuntimeError("The stable report copy has local edits: " + name)
    for name, source in mappings.items():
        if (target / name).exists() and not previous_path.exists():
            raise RuntimeError("Refusing to replace an untracked existing report: " + name)
        if sha(output / source) != manifest["output_sha256"][source]:
            raise RuntimeError("The report no longer matches its completed build manifest")
    copies = {}
    for name, source in mappings.items():
        shutil.copyfile(output / source, target / name)
        assert sha(target / name) == sha(output / source)
        copies[name] = {"source": (output / source).relative_to(root).as_posix(), "sha256": sha(target / name)}
    write_json(previous_path, {"canonical_run": output.relative_to(root).as_posix(),
                              "published_at_utc": datetime.now(timezone.utc).isoformat(), "copies": copies})


def build(output: Path | None = None, *, bootstrap_samples=1000, selection_samples=19999,
          update_latest=False):
    start = datetime.now(timezone.utc)
    output = Path(output).resolve() if output else ROOT / "epl_strategy_validation/results" / (
        start.strftime("%Y%m%dT%H%M%S.%fZ") + "_" + uuid4().hex[:8])
    if output.exists():
        raise FileExistsError("Refusing to overwrite an existing completed or partial run: " + str(output))
    for name in ("epl_data", "epl_modeling", "epl_live", "epl_report", "epl_strategy", "epl_robustness", "epl_strategy_lab", "reports"):
        protected = ROOT / name
        if output == protected or protected in output.parents or output == ROOT:
            raise ValueError("New results cannot be written into a preserved study or report tree")
    if not isinstance(bootstrap_samples, int) or bootstrap_samples < 0:
        raise ValueError("bootstrap_samples must be nonnegative")
    legacy = ROOT / LAB_EXPORT_RELATIVE
    sources = [ROOT / name for name in SOURCE_FILES]
    sources += [legacy / name for name in ("catalog.json", "metrics.parquet", "bets.parquet", "equity.parquet",
                                            "manifest.json", "figures/all_strategies_100k.png")]
    dependencies = [ROOT / "epl_strategy/metrics.py", ROOT / "epl_strategy/report.py"]
    dependencies += list((ROOT / "epl_strategy_lab").glob("*.py"))
    method_files = [ROOT / name for name in ("epl_modeling/METHODOLOGY.md", "epl_modeling/ABLATION_PROTOCOL.md",
                                             "epl_strategy/METHODOLOGY.md", "epl_strategy_lab/PROTOCOL.md")]
    protected = sorted(set(sources + dependencies + method_files + code_paths()))
    before = {path: sha(path) for path in protected}
    inventory = set(code_paths())
    models, opportunities, loaded = load_inputs(ROOT)
    if loaded != [ROOT / name for name in SOURCE_FILES]:
        raise AssertionError("Loaded source inventory differs from the protected source list")
    catalog, compatible = compatible_catalog(ROOT)
    output.mkdir(parents=True)
    write_json(output / "catalog.json", catalog)
    write_json(output / "compatible_catalog.json", compatible)
    versions = {name: version(name) for name in ("numpy", "pandas", "pyarrow", "matplotlib", "plotly", "reportlab", "python-docx", "XlsxWriter", "pypdf")}
    versions["python"] = platform.python_version()
    provenance = {"started_at_utc": start.isoformat(), "versions": versions,
                  "initial_bankroll": 100000, "metric_bootstrap_samples": bootstrap_samples,
                  "selection_bootstrap_samples": selection_samples,
                  "inputs_and_code_sha256": {p.relative_to(ROOT).as_posix(): s for p, s in before.items()}}
    write_json(output / "source_provenance.json", provenance)
    metric_rows = {"continuous": [], "seasonal": []}
    bet_rows = {"continuous": [], "seasonal": []}
    equity_rows = {"continuous": [], "seasonal": []}

    def account(config, universe, scope, season):
        episode = "continuous_2022_26" if scope == "continuous" else season
        bets, equity = replay(config, models, universe, initial_bankroll=100000, episode_id=episode)
        rebuilt = reconstruct_equity(bets, universe, initial_bankroll=100000, episode_id=episode)
        for column in ("start_bankroll", "end_bankroll", "turnover", "profit", "bet_count", "drawdown"):
            if not np.allclose(equity[column], rebuilt[column], atol=1e-6, rtol=1e-10):
                raise AssertionError("Independent cash reconstruction differs: " + column)
        metrics = summarize_strategy(bets, equity, prediction_count=len(universe), matched_valid_odds_count=len(universe),
                                     initial_bankroll=100000, bootstrap_samples=bootstrap_samples, random_state=42)
        flat = {k: json.dumps(v, sort_keys=True) if isinstance(v, (list, dict)) else v for k, v in config.items()}
        catalog_status = flat.pop("study_status", None)
        metric_rows[scope].append({**flat, **metrics, "scope": scope, "season": season, "episode_id": episode,
            "initial_bankroll": 100000., "catalog_definition_status": catalog_status,
            "study_status": "retrospective_frozen_rule_four_season_stability_not_new_holdout"})
        if len(bets): bet_rows[scope].append(bets)
        equity_rows[scope].append(equity)

    for config in compatible:
        account(config, opportunities, "continuous", "2022-26")
        for season in SEASONS:
            account(config, opportunities.loc[opportunities.season.eq(season)], "seasonal", season)
    tables = {}
    for scope in ("continuous", "seasonal"):
        tables["metrics_" + scope] = pd.DataFrame(metric_rows[scope])
        tables["bets_" + scope] = pd.concat(bet_rows[scope], ignore_index=True)
        tables["equity_" + scope] = pd.concat(equity_rows[scope], ignore_index=True)
    tables["season_stability"] = season_stability(tables["metrics_seasonal"], tables["metrics_continuous"])
    for name, frame in tables.items(): save(output, name, frame)
    graph = tables["equity_continuous"][["strategy_id", "match_date", "end_bankroll"]].copy()
    graph["is_initial"] = False
    anchor = pd.DataFrame({"strategy_id": [c["strategy_id"] for c in compatible],
                           "match_date": opportunities.match_date.min() - pd.Timedelta(days=1),
                           "end_bankroll": 100000., "is_initial": True})
    pd.concat([graph, anchor], ignore_index=True).sort_values(["strategy_id", "match_date"]).to_csv(output / "graph_equity_continuous.csv", index=False)
    write_json(output / "coverage.json", {"four_season_strategies": 56, "catalog_strategies": 84,
        "excluded_earlier_ids": [c["strategy_id"] for c in catalog if c not in compatible],
        "matches": len(opportunities), "match_dates": opportunities.match_date.nunique(),
        "season_matches": SEASON_MATCH_COUNTS, "season_match_dates": SEASON_DATE_COUNTS,
        "original_2025_graph": (LAB_EXPORT_RELATIVE / "figures/all_strategies_100k.png").as_posix(),
        "initial_bankroll": 100000, "model_count_including_ensembles": len(models),
        "study_status": "retrospective_previously_inspected_history_not_new_holdout"})
    run_selection_audit(legacy, output, bootstrap_samples=selection_samples, seed=20261015)
    write_json(output / "independent_audit.json", audit_export(output, ROOT))
    from .report import build_report
    report = build_report(output)
    changed = [str(p.relative_to(ROOT)) for p, digest in before.items() if not p.exists() or sha(p) != digest]
    if changed or set(code_paths()) != inventory:
        raise RuntimeError("Protected source/code changed during build: " + str(changed))
    manifest = {**provenance, "completed_at_utc": datetime.now(timezone.utc).isoformat(),
        "duration_seconds": (datetime.now(timezone.utc) - start).total_seconds(),
        "protected_hashes_unchanged": True, "report": report,
        "row_counts": {name: len(frame) for name, frame in tables.items()},
        "output_sha256": {p.relative_to(output).as_posix(): sha(p) for p in sorted(output.rglob("*")) if p.is_file()}}
    write_json(output / "manifest.json", manifest)
    if update_latest: publish_latest(output)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--bootstrap-samples", type=int, default=1000)
    parser.add_argument("--selection-samples", type=int, default=19999)
    parser.add_argument("--update-latest", action="store_true")
    args = parser.parse_args()
    result = build(args.output, bootstrap_samples=args.bootstrap_samples,
                   selection_samples=args.selection_samples, update_latest=args.update_latest)
    print(json.dumps({"completed": result["completed_at_utc"], "rows": result["row_counts"]}, indent=2))


if __name__ == "__main__": main()
