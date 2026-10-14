"""Export strategy analytics without fitting models or altering frozen studies.

Each invocation writes a new directory. Pooled ablation ledgers repeat the
original seasonal cashflows under an explicitly different scope; never sum
rows across scopes or strategies as if they formed one investment account.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from uuid import uuid4

import numpy as np
import pandas as pd

from epl_modeling.backtest import simulate_bets
from .metrics import enrich_bets, reconstruct_equity, summarize_strategy


PROJECT = Path(__file__).resolve().parents[1]
FIRST_KEYS = ["branch", "family", "split", "policy", "odds_mode", "staking"]
ABLATION_KEYS = ["outer_season", "feature_group", "model_type", "policy", "odds_mode", "staking"]
LABEL_COLUMNS = ["study", "scope", "strategy_id", "episode_id", "branch", "family",
                 "model_type", "feature_group", "split", "outer_season", "policy",
                 "odds_mode", "staking", "threshold", "is_tuning_diagnostic"]


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _slug(value) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]+", "p", str(value))


def _strategy_id(*values) -> str:
    return "__".join(_slug(value) for value in values)


def _unique(frame: pd.DataFrame, keys: list[str], label: str) -> None:
    if frame[keys].isna().any().any() or frame.duplicated(keys).any():
        raise ValueError(f"{label} requires present, unique keys {keys}")


def _close(actual, expected, label: str) -> None:
    if not np.isclose(float(actual), float(expected), rtol=1e-9, atol=1e-8, equal_nan=True):
        raise ValueError(f"{label} differs: {actual!r} versus {expected!r}")


def _subset(frame: pd.DataFrame, record: dict, keys: list[str]) -> pd.DataFrame:
    mask = pd.Series(True, index=frame.index)
    for key in keys:
        mask &= frame[key].eq(record[key])
    return frame.loc[mask].copy()


def _labels(record: dict, *, study: str, scope: str, episode_id: str,
            diagnostic: bool = False) -> dict:
    first = study.startswith("first")
    family = record.get("family", record.get("model_type", ""))
    labels = {key: "" for key in LABEL_COLUMNS}
    labels.update({"study": study, "scope": scope, "episode_id": episode_id,
                   "branch": record.get("branch", ""), "family": family,
                   "model_type": family if first else record.get("model_type", ""),
                   "feature_group": "branch_selected_features" if first else record.get("feature_group", ""),
                   "split": record.get("split", ""), "outer_season": record.get("outer_season", ""),
                   "policy": record["policy"], "odds_mode": record["odds_mode"],
                   "staking": record["staking"], "threshold": float(record["threshold"]),
                   "is_tuning_diagnostic": bool(diagnostic)})
    components = [study, labels["branch"], labels["family"]] if first else [study, labels["model_type"], labels["feature_group"]]
    labels["strategy_id"] = _strategy_id(*components, labels["policy"], labels["odds_mode"], labels["staking"])
    if diagnostic:
        labels["strategy_id"] += "__edge_" + _slug(record["threshold"])
    return labels


def _annotate(frame: pd.DataFrame, labels: dict, *, preserve_episode: bool = False) -> pd.DataFrame:
    result = frame.copy()
    for key, value in labels.items():
        if key == "episode_id" and preserve_episode:
            continue
        result[key] = value
    if "stake" in result:
        result = enrich_bets(result)
        result["model_expected_gain_cash"] = result.probability * result.stake * (result.odds - 1)
        result["model_expected_loss_cash"] = (1 - result.probability) * result.stake
        result["model_expected_net_profit_cash"] = result.stake * result.edge
        result["realized_net_return"] = result.profit / result.stake
    return result


def _opportunities(predictions: pd.DataFrame, prices: pd.DataFrame) -> pd.DataFrame:
    _unique(predictions, ["match_id"], "prediction series")
    _unique(prices, ["match_id"], "price panel")
    native = predictions[["match_id", "match_date", "season", "result"]].merge(
        prices, on="match_id", how="inner", suffixes=("", "_price"), validate="one_to_one")
    for column in ("match_date", "season", "result"):
        if not native[column].eq(native[column + "_price"]).all():
            raise ValueError(f"Prediction/price {column} identity conflict")
    values = native[[f"{prefix}odds_{label}" for prefix in ("", "ref_") for label in "HDA"]].to_numpy(float)
    native = native.loc[np.isfinite(values).all(axis=1) & (values > 1).all(axis=1)]
    return native[["match_id", "match_date"]].sort_values(["match_date", "match_id"]).reset_index(drop=True)


def _verify_cash(bets: pd.DataFrame, equity: pd.DataFrame, original: dict,
                 opportunities: pd.DataFrame) -> None:
    _unique(bets, ["match_id"], "saved strategy bets")
    _unique(equity, ["match_date"], "strategy date equity")
    if len(bets):
        if not bets.match_id.isin(opportunities.match_id).all():
            raise ValueError("Bet identity outside the matched opportunity population")
        identity = bets[["match_id", "match_date"]].merge(opportunities, on="match_id", validate="one_to_one", suffixes=("", "_opportunity"))
        if not identity.match_date.eq(identity.match_date_opportunity).all():
            raise ValueError("Bet/opportunity date mismatch")
        values = bets[["probability", "odds", "stake", "profit", "edge"]].to_numpy(float)
        if not np.isfinite(values).all() or bets.stake.le(0).any() or bets.odds.le(1).any():
            raise ValueError("Invalid saved probability, price, stake or cashflow")
        if not bets.probability.between(0, 1).all() or not bets.selection.isin(list("HDA")).all():
            raise ValueError("Invalid saved selection/probability")
        if not bets.won.eq(bets.selection.eq(bets.result)).all():
            raise ValueError("Saved win indicator conflicts with settlement")
        if not np.allclose(bets.edge, bets.probability * bets.odds - 1, rtol=1e-9, atol=1e-8):
            raise ValueError("Saved edge conflicts with probability/price")
        if not np.allclose(bets.profit, bets.stake * (bets.odds * bets.won - 1), rtol=1e-9, atol=1e-8):
            raise ValueError("Saved settlement profit conflicts with stake/price")
    _close(len(bets), original["bet_count"], "bet count")
    _close(bets.stake.sum(), original["turnover"], "turnover")
    _close(bets.profit.sum(), original["profit"], "profit")
    _close(len(opportunities), original["matched_valid_odds_count"], "matched opportunity count")
    _close(equity.turnover.sum(), original["turnover"], "date turnover")
    _close(equity.profit.sum(), original["profit"], "date profit")
    _close(equity.bet_count.sum(), original["bet_count"], "date bet count")
    if set(equity.match_date) != set(opportunities.match_date):
        raise ValueError("Equity must contain every matched date, including no-bet dates")
    if len(equity):
        ordered = equity.sort_values("match_date")
        _close(ordered.iloc[0].start_bankroll, original["initial_bankroll"], "initial capital")
        _close(ordered.iloc[-1].end_bankroll, original["final_bankroll"], "final capital")
        if not np.allclose(ordered.end_bankroll, ordered.start_bankroll + ordered.profit, atol=1e-8):
            raise ValueError("Date equity violates cash conservation")
        if not np.allclose(ordered.start_bankroll.iloc[1:], ordered.end_bankroll.iloc[:-1], atol=1e-8):
            raise ValueError("Equity has an undeclared capital reset")
        if (ordered.end_bankroll < -1e-8).any():
            raise ValueError("Negative date-close capital")


def _save(frame: pd.DataFrame, directory: Path, name: str) -> None:
    # The output directory is exclusively created before any export is written.
    frame.to_csv(directory / (name + ".csv"), index=False)
    frame.to_parquet(directory / (name + ".parquet"), index=False)


def build(output_dir: Path | None = None, *, project_root: Path = PROJECT,
          bootstrap_samples: int = 1000, random_state: int = 42) -> dict:
    project_root = Path(project_root).resolve()
    started = datetime.now(timezone.utc)
    if bootstrap_samples < 0:
        raise ValueError("bootstrap_samples must be nonnegative")
    output = Path(output_dir).resolve() if output_dir else project_root / "epl_strategy" / "results" / (started.strftime("%Y%m%dT%H%M%S.%fZ") + "_" + uuid4().hex[:10])
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite existing output directory: {output}")
    protected = [project_root / name for name in ("epl_modeling", "epl_data", "epl_live")]
    if output == project_root or any(output == path or path in output.parents for path in protected):
        raise ValueError("Analytics output must not be inside an existing study or live artifact tree")

    inputs = {}

    def read(relative: str) -> pd.DataFrame:
        path = project_root / relative
        frame = pd.read_parquet(path)
        if "match_date" in frame:
            frame["match_date"] = pd.to_datetime(frame.match_date).dt.normalize()
        inputs[relative] = {"sha256": _hash(path), "bytes": path.stat().st_size, "rows": len(frame)}
        return frame

    first_summary = read("epl_modeling/results/betting_summary.parquet")
    first_bets = read("epl_modeling/results/bets.parquet")
    first_equity = read("epl_modeling/results/daily_equity.parquet")
    first_predictions = read("epl_modeling/results/predictions.parquet")
    prices = read("epl_modeling/results/bookmaker_odds_panel.parquet")
    candidates = read("epl_modeling/results/threshold_validation.parquet")
    ablation_summary = read("epl_modeling/ablation_results/betting_summary.parquet")
    ablation_bets = read("epl_modeling/ablation_results/bets.parquet")
    ablation_predictions = read("epl_modeling/ablation_results/predictions.parquet")
    _unique(first_summary, FIRST_KEYS, "first-study universe")
    _unique(ablation_summary, ABLATION_KEYS, "ablation universe")
    _unique(candidates, ["branch", "threshold"], "tuning candidates")
    if (len(first_summary), len(ablation_summary), len(candidates)) != (48, 88, 14):
        raise ValueError("Frozen study universe differs from the audited 48/88/14 rows")

    records, bet_ledgers, equity_ledgers, metric_columns = [], [], [], set()
    seasonal = []

    def add(bets, equity, labels, *, prediction_count, matched_count, initial=1000.0,
            original=None, preserve_episode=False):
        metric = summarize_strategy(bets, equity, prediction_count=int(prediction_count),
                                    matched_valid_odds_count=int(matched_count), initial_bankroll=float(initial),
                                    bootstrap_samples=bootstrap_samples, random_state=random_state)
        metric_columns.update(metric)
        entry = {**metric, **labels, "bankroll_reset_scope": "each_outer_season" if labels["scope"] == "pooled_seasons" else "episode",
                 "retrospective_only": True, "executable_prices_verified": False,
                 "ledger_role": "pooled_view" if labels["scope"] == "pooled_seasons" else "tuning_reconstruction" if labels["is_tuning_diagnostic"] else "original_saved_strategy"}
        if original:
            entry.update({"original_bet_count": original["bet_count"], "original_profit": original["profit"],
                          "original_turnover": original["turnover"], "fixed_stake": original.get("fixed_stake", 10.0),
                          "kelly_fraction": original.get("kelly_fraction", 0.25), "max_bet_fraction": original.get("max_bet_fraction", 0.02)})
        records.append(entry)
        labelled_bets = _annotate(bets, labels, preserve_episode=preserve_episode)
        labelled_equity = _annotate(equity, labels, preserve_episode=preserve_episode)
        for frame in (labelled_bets, labelled_equity):
            frame["ledger_role"] = entry["ledger_role"]
        bet_ledgers.append(labelled_bets)
        equity_ledgers.append(labelled_equity)
        return labelled_bets, labelled_equity

    for original in first_summary.to_dict("records"):
        pred = _subset(first_predictions, original, ["branch", "family", "split"])
        opportunities = _opportunities(pred, prices)
        if pred.season.nunique() != 1:
            raise ValueError("First-study betting episode must be one season")
        episode = str(pred.season.iloc[0])
        bets = _subset(first_bets, original, FIRST_KEYS)
        equity = _subset(first_equity, original, FIRST_KEYS)
        equity["episode_id"] = episode
        _verify_cash(bets, equity, original, opportunities)
        _close(len(pred), original["prediction_count"], "first prediction count")
        labels = _labels(original, study="first", scope=original["split"], episode_id=episode)
        add(bets, equity, labels, prediction_count=len(pred), matched_count=len(opportunities),
            initial=original["initial_bankroll"], original=original)

    for original in ablation_summary.to_dict("records"):
        pred = _subset(ablation_predictions, original, ["outer_season", "feature_group", "model_type"])
        opportunities = _opportunities(pred, prices)
        bets = _subset(ablation_bets, original, ABLATION_KEYS)
        episode = original["outer_season"]
        equity = reconstruct_equity(bets, opportunities, initial_bankroll=original["initial_bankroll"], episode_id=episode)
        _verify_cash(bets, equity, original, opportunities)
        _close(len(pred), original["prediction_count"], "ablation prediction count")
        labels = _labels(original, study="ablation", scope="outer_test", episode_id=episode)
        labelled_bets, labelled_equity = add(bets, equity, labels, prediction_count=len(pred),
                                             matched_count=len(opportunities), initial=original["initial_bankroll"], original=original)
        seasonal.append((original, labelled_bets, labelled_equity, len(pred), len(opportunities)))

    pool_keys = ["feature_group", "model_type", "policy", "odds_mode", "staking"]
    for values, _ in ablation_summary.groupby(pool_keys, sort=True):
        matching = [row for row in seasonal if all(row[0][key] == value for key, value in zip(pool_keys, values))]
        if len(matching) != 4:
            raise ValueError("A pooled ablation strategy must have four seasonal episodes")
        original = matching[0][0].copy()
        original["outer_season"] = "pooled"
        labels = _labels(original, study="ablation", scope="pooled_seasons", episode_id="season_stratified_pool")
        bets = pd.concat([row[1] for row in matching], ignore_index=True)
        equity = pd.concat([row[2] for row in matching], ignore_index=True)
        add(bets, equity, labels, prediction_count=sum(row[3] for row in matching),
            matched_count=sum(row[4] for row in matching), initial=original["initial_bankroll"], preserve_episode=True)

    for trial in candidates.to_dict("records"):
        pred = first_predictions.loc[first_predictions.branch.eq(trial["branch"]) & first_predictions.split.eq("strategy_validation")].copy()
        if pred.family.nunique() != 1:
            raise ValueError("Threshold diagnostics require a single frozen branch family")
        bets, equity, summary = simulate_bets(pred, prices, threshold=trial["threshold"], staking="fixed", bootstrap_samples=0)
        _close(len(bets), trial["n_bets"], "recovered threshold bet count")
        _close(bets.stake.sum(), trial["turnover"], "recovered threshold turnover")
        _close(bets.profit.sum(), trial["profit"], "recovered threshold profit")
        recovered_roi = bets.profit.sum() / bets.stake.sum() if bets.stake.sum() else np.nan
        _close(recovered_roi, trial["roi"], "recovered threshold ROI")
        if bool(trial["eligible"]) != bool(len(bets) >= 30 and bets.profit.sum() > 0):
            raise ValueError("Recovered candidate eligibility differs from frozen audit")
        episode = str(pred.season.iloc[0])
        equity["episode_id"] = episode
        opportunities = _opportunities(pred, prices)
        _verify_cash(bets, equity, summary, opportunities)
        description = {**trial, "family": pred.family.iloc[0], "split": "strategy_validation",
                       "policy": "threshold_candidate", "odds_mode": "best_individual_book", "staking": "fixed"}
        labels = _labels(description, study="first_tuning", scope="threshold_tuning", episode_id=episode, diagnostic=True)
        add(bets, equity, labels, prediction_count=len(pred), matched_count=len(opportunities), original=summary)
        records[-1]["validation_candidate_eligible"] = bool(trial["eligible"])

    metrics_frame = pd.DataFrame(records)
    bets_frame = pd.concat(bet_ledgers, ignore_index=True)
    equity_frame = pd.concat(equity_ledgers, ignore_index=True)
    if len(metrics_frame) != 172:
        raise ValueError(f"Expected 172 strategy scope rows, received {len(metrics_frame)}")
    _unique(metrics_frame, ["study", "scope", "strategy_id", "episode_id"], "exported strategy universe")
    _unique(bets_frame, ["study", "scope", "strategy_id", "episode_id", "match_id"], "enriched bet ledger")
    _unique(equity_frame, ["study", "scope", "strategy_id", "episode_id", "match_date"], "enriched equity ledger")

    # Forecasts are not trade records. All prospective trading metrics remain
    # unavailable even where a probability forecast has been released.
    from epl_live.ledger import read_forecasts, read_outcomes
    forecasts_path = project_root / "epl_live/forecasts.jsonl"
    outcomes_path = project_root / "epl_live/outcomes.jsonl"
    forecasts = read_forecasts(forecasts_path) if forecasts_path.exists() else []
    outcomes = read_outcomes(outcomes_path) if outcomes_path.exists() else []
    for path in (forecasts_path, outcomes_path):
        if path.exists():
            inputs[str(path.relative_to(project_root)).replace("\\", "/")] = {"sha256": _hash(path), "bytes": path.stat().st_size}
    manifests = sorted((project_root / "epl_live/models").glob("*/manifest.json"))
    if not manifests:
        raise FileNotFoundError("Prospective status requires the frozen live model manifest")
    model_path = max(manifests, key=lambda path: json.loads(path.read_text(encoding="utf-8"))["trained_at_utc"])
    model_manifest = json.loads(model_path.read_text(encoding="utf-8"))
    inputs[str(model_path.relative_to(project_root)).replace("\\", "/")] = {"sha256": _hash(model_path), "bytes": model_path.stat().st_size}
    models = [{"model_id": row["model_id"], "model_type": row["model_type"], "feature_group": row["feature_group"]}
              for row in model_manifest["models"]]
    models += [{"model_id": "prospective_v1_market_raw", "model_type": "baseline", "feature_group": "market_only"},
               {"model_id": "prospective_v1_market_temperature", "model_type": "market_temperature", "feature_group": "market_only"}]
    if len(models) != 10 or len({row["model_id"] for row in models}) != 10:
        raise ValueError("Prospective status requires eight frozen candidates and two market benchmarks")
    observed_outcomes = {row["match_id"] for row in outcomes}
    prospective_rows = []
    for model in models:
        released = [row for row in forecasts if row["model_id"] == model["model_id"]]
        for staking in ("fixed", "kelly"):
            labels = _labels({**model, "policy": "predeclared_5pct", "odds_mode": "not_executed",
                              "staking": staking, "threshold": 0.05}, study="prospective", scope="pending", episode_id="2026-27")
            labels["strategy_id"] = _strategy_id("prospective", model["model_id"], staking)
            prospective_rows.append({**{column: None for column in sorted(metric_columns)}, **labels, **model,
                                     "released_forecast_count": len(released),
                                     "quote_backed_forecast_count": sum(row.get("market_quote") is not None for row in released),
                                     "resolved_forecast_count": sum(row["match_id"] in observed_outcomes for row in released),
                                     "trading_performance_available": False,
                                     "trading_status": "unavailable_no_trade_ledger",
                                     "declared_initial_bankroll": 1000.0, "declared_fixed_stake": 10.0,
                                     "declared_kelly_fraction": 0.25, "declared_max_bet_fraction": 0.02,
                                     "reason": "no_recorded_quote_backed_trades_or_settled_positions",
                                     "reason_description": "Released forecasts are not quote-backed trades; no prospective trade ledger exists"})
    prospective = pd.DataFrame(prospective_rows)

    arb_rows = []

    def arb(study, scope, episode, ids, *, split="", outer_season=""):
        rows = prices.loc[prices.match_id.isin(ids)]
        count = int(rows.mathematical_arb_candidate.sum())
        arb_rows.append({"study": study, "scope": scope, "episode_id": episode, "split": split,
                         "outer_season": outer_season, "eligible_matches": len(rows),
                         "mathematical_candidate_count": count,
                         "mathematical_candidate_fraction": count / len(rows) if len(rows) else np.nan,
                         "quote_clock_unverified_count": int(rows.quotes_asynchronous_or_unverified.sum()),
                         "executable_arbitrage_verified": False, "executed_arbitrage_trade_count": None,
                         "realized_arbitrage_profit": None, "status": "screen_only_no_execution_ledger"})

    for split in first_summary.split.unique():
        one = first_predictions.loc[first_predictions.split.eq(split)]
        arb("first", split, str(one.season.iloc[0]), one.match_id.unique(), split=split)
    for season, one in ablation_predictions.groupby("outer_season", sort=True):
        arb("ablation", "outer_test", season, one.match_id.unique(), outer_season=season)
    arbitrage = pd.DataFrame(arb_rows)

    for relative, item in inputs.items():
        if _hash(project_root / relative) != item["sha256"]:
            raise ValueError(f"Preserved input changed during analytics: {relative}")
    # Deliberately fail rather than reuse even an empty user-supplied directory.
    output.mkdir(parents=True, exist_ok=False)
    for name, frame in [("strategy_metrics", metrics_frame), ("bets_enriched", bets_frame),
                        ("equity_enriched", equity_frame), ("prospective_status", prospective),
                        ("arbitrage_screen", arbitrage)]:
        _save(frame, output, name)
    completed = datetime.now(timezone.utc)
    audit = {"schema_version": 1, "started_at_utc": started.isoformat(), "completed_at_utc": completed.isoformat(),
             "output_directory": str(output), "bootstrap_samples": bootstrap_samples, "random_state": random_state,
             "counts": {"strategy_rows": len(metrics_frame), "first_strategy_rows": 48, "ablation_season_rows": 88,
                        "ablation_pooled_rows": 22, "threshold_diagnostic_rows": 14,
                        "original_first_bet_records": len(first_bets), "original_ablation_bet_records": len(ablation_bets),
                        "enriched_bet_records": len(bets_frame), "enriched_equity_records": len(equity_frame),
                        "prospective_status_rows": len(prospective), "arbitrage_screen_rows": len(arbitrage)},
             "inputs": inputs, "inputs_unchanged_after_build": True,
             "source_sha256": {"epl_strategy/build.py": _hash(Path(__file__)),
                               "epl_strategy/metrics.py": _hash(Path(__file__).with_name("metrics.py")),
                               "epl_modeling/backtest.py": _hash(project_root / "epl_modeling/backtest.py")},
             "tables": {name: {"rows": len(frame), "columns": list(frame.columns),
                               "csv_sha256": _hash(output / (name + ".csv")),
                               "parquet_sha256": _hash(output / (name + ".parquet"))}
                        for name, frame in [("strategy_metrics", metrics_frame), ("bets_enriched", bets_frame),
                                            ("equity_enriched", equity_frame), ("prospective_status", prospective),
                                            ("arbitrage_screen", arbitrage)]},
             "validation": {"summary_left_universes_preserved": True, "saved_counts_and_cash_reconciled": True,
                            "unique_strategy_match_identities": True, "all_matched_dates_retained": True,
                            "threshold_candidates_reproduce_frozen_audit": True, "no_model_refitting": True},
             "limitations": ["All retrospective cashflows use unverified archived preclosing prices.",
                             "Pooled summaries retain 1000 initial capital per season and episode-stratified date bootstrap.",
                             "Pooled enriched ledgers duplicate seasonal records under a distinct scope; never sum across scopes or strategies.",
                             "Threshold candidate rows are tuning diagnostics, not separately selected holdout strategies.",
                             "Prospective forecasts are not trades and all prospective trading metrics remain unavailable.",
                             "Arbitrage rows are mathematical screens without executed trades or realized profit claims."]}
    with (output / "audit_manifest.json").open("x", encoding="utf-8") as handle:
        json.dump(audit, handle, indent=2, ensure_ascii=False, allow_nan=False)
        handle.write("\n")
    return {"output_directory": str(output), **audit["counts"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, help="New output directory; any existing directory is refused")
    parser.add_argument("--bootstrap-samples", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    print(json.dumps(build(args.output_dir, bootstrap_samples=args.bootstrap_samples, random_state=args.seed), indent=2))


if __name__ == "__main__":
    main()
