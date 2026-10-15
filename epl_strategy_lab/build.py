"""Create a new, immutable common-window strategy replay from frozen inputs."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
from importlib.metadata import PackageNotFoundError, version
import json
from pathlib import Path
import platform
from uuid import uuid4

import numpy as np
import pandas as pd

from epl_strategy import metrics as frozen_metrics
from .inputs import ABLATION_MODELS, SOURCE_FILES, load_inputs


PROJECT = Path(__file__).resolve().parents[1]
INITIAL_BANKROLL = 100000.0
EXPECTED_STRATEGIES = 84


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _label(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def _json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, allow_nan=False, default=str) + "\n", encoding="utf-8")


def _save(directory: Path, name: str, frame: pd.DataFrame) -> None:
    frame.to_csv(directory / f"{name}.csv", index=False)
    frame.to_parquet(directory / f"{name}.parquet", index=False)


def _versions() -> dict:
    result = {"python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__}
    for package in ("pyarrow", "matplotlib", "openpyxl", "nbformat", "nbclient", "pytest", "plotly",
                    "python-docx", "reportlab", "XlsxWriter", "Pillow", "pypdf"):
        try:
            result[package] = version(package)
        except PackageNotFoundError:
            result[package] = "not_installed"
    return result


def _lab_code_paths(output: Path) -> list[Path]:
    folder = Path(__file__).parent
    return sorted(path for path in folder.rglob("*")
                  if path.is_file() and path.suffix.lower() in {".py", ".md", ".txt"}
                  and "results" not in path.relative_to(folder).parts
                  and "__pycache__" not in path.parts and path != output and output not in path.parents)


def _catalog() -> list[dict]:
    from .catalog import build_catalog
    return build_catalog()


def _validate_catalog(catalog: list[dict], model_keys: set[str]) -> None:
    if len(catalog) != EXPECTED_STRATEGIES:
        raise ValueError(f"Expected {EXPECTED_STRATEGIES} catalog strategies, found {len(catalog)}")
    ids = [item.get("strategy_id") for item in catalog]
    if any(not isinstance(value, str) or not value.strip() for value in ids) or len(set(ids)) != len(ids):
        raise ValueError("Catalog strategy IDs must be present and unique")
    for item in catalog:
        if item.get("model_key") not in model_keys:
            raise ValueError(f"Unknown catalog model key: {item.get('model_key')}")
    # Reject nonstandard JSON infinities before writing a reviewable protocol.
    json.dumps(catalog, allow_nan=False)


def _validate_replay(config: dict, bets: pd.DataFrame, equity: pd.DataFrame,
                     opportunities: pd.DataFrame) -> None:
    expected_dates = pd.DatetimeIndex(opportunities.match_date.unique()).sort_values()
    actual_dates = pd.to_datetime(equity.match_date).dt.normalize()
    if len(equity) != len(expected_dates) or not pd.DatetimeIndex(actual_dates).equals(expected_dates):
        raise ValueError(f"{config['strategy_id']} does not retain every common match date in order")
    if not equity.strategy_id.eq(config["strategy_id"]).all():
        raise ValueError("Equity strategy identity conflicts with catalog")
    if equity.episode_id.nunique() != 1:
        raise ValueError("A common-window strategy must use one uninterrupted bankroll episode")
    if len(bets) and not bets.strategy_id.eq(config["strategy_id"]).all():
        raise ValueError("Bet strategy identity conflicts with catalog")
    # Reconstruct separately from the engine output, including date-start funds
    # and no-bet dates, before allowing the frozen metrics implementation to run.
    episode = equity.episode_id.iloc[0]
    rebuilt = frozen_metrics.reconstruct_equity(
        bets, opportunities, initial_bankroll=INITIAL_BANKROLL, episode_id=episode
    )
    for column in ("matched_matches", "bet_count", "turnover", "profit", "start_bankroll",
                   "end_bankroll", "daily_return", "drawdown"):
        if not np.allclose(equity[column].to_numpy(float), rebuilt[column].to_numpy(float),
                           rtol=1e-10, atol=1e-7):
            raise ValueError(f"Engine {column} differs from independent cash reconstruction")


def build(output_dir: Path | None = None, *, project_root: Path = PROJECT,
          bootstrap_samples: int = 1000, random_state: int = 42,
          generate_report: bool = True) -> dict:
    """Write all 84 strategies with a single 100,000-capital season each.

    This stage neither fits models nor selects policies using the saved results.
    All comparisons are exploratory replays of previously inspected history.
    ``generate_report=False`` is provided for focused integration tests only.
    """
    from .engine import simulate_strategy
    started = datetime.now(timezone.utc)
    root = Path(project_root).resolve()
    if not (root / "epl_modeling").is_dir() and (root / "final_project/epl_modeling").is_dir():
        root = root / "final_project"
    if not isinstance(bootstrap_samples, (int, np.integer)) or bootstrap_samples < 0:
        raise ValueError("bootstrap_samples must be a nonnegative integer")
    output = Path(output_dir).resolve() if output_dir else root / "epl_strategy_lab/results" / (
        started.strftime("%Y%m%dT%H%M%S.%fZ") + "_" + uuid4().hex[:10])
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite existing output directory: {output}")
    protected = [root / name for name in ("epl_modeling", "epl_data", "epl_live", "epl_strategy", "epl_robustness")]
    if output == root or any(output == path or path in output.parents for path in protected):
        raise ValueError("New replay output cannot be placed inside a preserved source or study tree")
    source_paths = [root / relative for relative in SOURCE_FILES]
    code_paths = _lab_code_paths(output)
    dependencies = [Path(frozen_metrics.__file__).resolve()]
    protected_paths = sorted(set(source_paths + code_paths + dependencies))
    before = {path: _sha(path) for path in protected_paths}
    models, opportunities, loaded_source_paths = load_inputs(root)
    if loaded_source_paths != source_paths:
        raise ValueError("The loaded source inventory differs from the protected source inventory")
    catalog = _catalog()
    _validate_catalog(catalog, set(models))
    output.mkdir(parents=True, exist_ok=False)
    _json(output / "catalog.json", catalog)
    versions = _versions()
    _json(output / "source_provenance.json", {
        "started_at_utc": started.isoformat(),
        "inputs_and_code_sha256": {_label(path, root): digest for path, digest in before.items()},
        "source_sha256": {_label(path, root): before[path] for path in source_paths},
        "versions": versions,
        "config": {"season": "2025-26", "initial_bankroll": INITIAL_BANKROLL,
                   "bootstrap_samples": int(bootstrap_samples), "random_state": random_state},
    })
    rows, bet_frames, equity_frames, graph_frames = [], [], [], []
    anchor = opportunities.match_date.min() - pd.Timedelta(days=1)
    for config in catalog:
        bets, equity = simulate_strategy(config, models, opportunities, initial_bankroll=INITIAL_BANKROLL)
        _validate_replay(config, bets, equity, opportunities)
        summary = frozen_metrics.summarize_strategy(
            bets, equity, prediction_count=len(opportunities), matched_valid_odds_count=len(opportunities),
            initial_bankroll=INITIAL_BANKROLL, bootstrap_samples=bootstrap_samples, random_state=random_state
        )
        if summary["bankroll_reset_episodes"] != 1 or summary["initial_capital_sum_units"] != INITIAL_BANKROLL:
            raise ValueError("A strategy introduced a bankroll reset or changed its initial capital")
        rows.append({**config, **summary, "initial_bankroll": INITIAL_BANKROLL,
                     "catalog_params_json": json.dumps(config, sort_keys=True, allow_nan=False),
                     "study_status": "exploratory_retrospective_previously_inspected_2025_26",
                     "risk_context": "one_uninterrupted_2025_26_account"})
        # Unconditional controls have a missing threshold; keep that column a
        # nullable numeric value rather than mixing all-None object and float.
        bets["threshold"] = pd.to_numeric(bets["threshold"], errors="raise").astype(float)
        bet_frames.append(bets)
        equity_frames.append(equity)
        graph = equity[["strategy_id", "match_date", "end_bankroll"]].copy()
        graph["is_initial"] = False
        start = pd.DataFrame([{"strategy_id": config["strategy_id"], "match_date": anchor,
                               "end_bankroll": INITIAL_BANKROLL, "is_initial": True}])
        graph_frames.append(pd.concat([start, graph], ignore_index=True))
    metrics = pd.DataFrame(rows)
    # Lists/tuples are kept exactly in catalog.json and catalog_params_json;
    # scalar-friendly copies make the flat CSV and Parquet equally easy to read.
    for column in metrics:
        if metrics[column].map(lambda value: isinstance(value, (list, tuple, dict))).any():
            metrics[column] = metrics[column].map(
                lambda value: json.dumps(value, sort_keys=True, allow_nan=False)
                if isinstance(value, (list, tuple, dict)) else value)
    populated_bets = [frame for frame in bet_frames if len(frame)]
    bets = pd.concat(populated_bets, ignore_index=True) if populated_bets else bet_frames[0].copy()
    equity = pd.concat(equity_frames, ignore_index=True)
    graph = pd.concat(graph_frames, ignore_index=True)
    for name, frame in (("metrics", metrics), ("bets", bets), ("equity", equity)):
        _save(output, name, frame)
    graph.to_csv(output / "graph_equity.csv", index=False)
    missing_clocks = {column: int(opportunities[column].isna().sum()) for column in opportunities
                      if "timestamp" in column}
    audit = {
        "season": "2025-26", "n_matches": len(opportunities), "n_match_dates": int(opportunities.match_date.nunique()),
        "first_match_date": str(opportunities.match_date.min().date()),
        "last_match_date": str(opportunities.match_date.max().date()),
        "calendar_days_inclusive": int((opportunities.match_date.max() - opportunities.match_date.min()).days + 1),
        "n_original_prediction_series": 13, "n_ensemble_series": 3,
        "n_strategies": len(catalog), "model_keys": list(models),
        "model_source_descriptions": {
            "first_accuracy": "Frozen initial-study accuracy-selected SVM, saved 2025-26 test probabilities.",
            "first_calibration": "Frozen initial-study calibration-selected MLP, saved 2025-26 test probabilities.",
            **{key: f"Frozen rolling-source ablation {group}/{family}, saved outer-season 2025-26 probabilities."
               for (group, family), key in ABLATION_MODELS.items()},
            "ensemble_logit4": "Equal-weight mean of the four saved logistic feature-group probability vectors.",
            "ensemble_learned8": "Equal-weight mean of the four logistic and four market-residual saved probability vectors.",
            "ensemble_market_blend": "Equal-weight mean of saved combined-feature logistic and raw reference-market probability vectors.",
        },
        "ensemble_weights": {
            "ensemble_logit4": {f"logit_{name}": 0.25 for name in ("team_only", "team_xg", "team_players", "combined")},
            "ensemble_learned8": {f"{family}_{name}": 0.125 for family in ("logit", "residual")
                                  for name in ("team_only", "team_xg", "team_players", "combined")},
            "ensemble_market_blend": {"logit_combined": 0.5, "baseline_market_only": 0.5},
        },
        "common_population_dropped_matches": 0, "identity_conflicts": 0,
        "probability_normalization_max_error": float(max(
            np.max(np.abs(frame[["p_H", "p_D", "p_A"]].sum(axis=1).to_numpy() - 1)) for frame in models.values())),
        "quote_timestamp_missing_counts": missing_clocks,
        "archived_snapshot_type": "preclosing", "provider_quote_times_verified": False,
        "execution_verified": False, "initial_bankroll_per_strategy": INITIAL_BANKROLL,
        "continuous_season_accounts": True, "resets_per_strategy": 0,
        "graph_rows": len(graph), "graph_anchor_date": str(anchor.date()),
        "primary_cash_strategies": int(sum(bool(config.get("cash_only", False)) for config in catalog)),
        "legacy_diagnostic_strategies": int(sum(config.get("origin") == "legacy_diagnostic" for config in catalog)),
        "source_paths": [_label(path, root) for path in source_paths],
        "audit_reference_sources": [_label(path, root) for path in source_paths
                                    if path.name == "bets.parquet"],
        "limitations": [
            "All 2025-26 outcomes were previously inspected; new strategy comparisons are retrospective exploratory.",
            "The cohort is defined by current 2026-27 league membership, introducing survivor/cohort selection bias.",
            "Archived bookmaker prices and historical feature publication times are unverified; this is a hypothetical replay.",
            "Independent strategies each receive 100000; their curves cannot be added as one jointly funded portfolio.",
            "Bootstrap intervals condition on recorded predictions, selections and stakes; no refit or multiplicity correction.",
        ],
    }
    _json(output / "inputs_audit.json", audit)
    if generate_report:
        from .report import build_report
        build_report(output)
        from .audit import audit_export
        _json(output / "independent_audit.json", audit_export(output, root=root))
    changed = [_label(path, root) for path, digest in before.items() if not path.is_file() or _sha(path) != digest]
    if _lab_code_paths(output) != code_paths:
        changed.append("lab source/document inventory")
    if changed:
        raise RuntimeError(f"Frozen input, dependency or lab code changed during build: {changed}")
    manifest = {
        "study_status": "exploratory_retrospective_previously_inspected_2025_26",
        "created_at_utc": started.isoformat(), "completed_at_utc": datetime.now(timezone.utc).isoformat(),
        "output_dir": str(output), "duration_seconds": (datetime.now(timezone.utc) - started).total_seconds(),
        "config": {"season": "2025-26", "initial_bankroll": INITIAL_BANKROLL,
                   "bootstrap_samples": int(bootstrap_samples), "random_state": random_state,
                   "strategies": len(catalog), "generate_report": generate_report},
        "inputs_and_code_sha256": {_label(path, root): digest for path, digest in before.items()},
        "source_sha256": {_label(path, root): before[path] for path in source_paths},
        "source_bytes": {_label(path, root): path.stat().st_size for path in source_paths},
        "protected_hashes_unchanged": True,
        "versions": versions,
        "row_counts": {"metrics": len(metrics), "bets": len(bets), "equity": len(equity), "graph_equity": len(graph)},
        "output_sha256": {path.relative_to(output).as_posix(): _sha(path)
                          for path in sorted(output.rglob("*")) if path.is_file()},
    }
    _json(output / "manifest.json", manifest)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--bootstrap-samples", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    result = build(args.output, bootstrap_samples=args.bootstrap_samples, random_state=args.seed)
    print(json.dumps({"output_dir": result["output_dir"], "row_counts": result["row_counts"]}, indent=2))


if __name__ == "__main__":
    main()
