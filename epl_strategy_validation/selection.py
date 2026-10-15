"""Conditional, paired cashflow max-statistic sensitivities for 84 saved rules.

The estimand is mean excess net profit per PRICED MATCH DATE, including no-bet
dates. This is deliberately not a rerun of wealth policies on alternate outcomes.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


BLOCK_LENGTHS = (1, 3, 5, 10)
INITIAL_BANKROLL = 100000.0
SOURCE_URLS = {
    "multiple_search_concept": "https://doi.org/10.1111/1468-0262.00152",
    "fixed_circular_block_method": "https://statistics.stanford.edu/technical-reports/circular-block-resampling-procedure-stationary-data",
}


def _close(actual, expected, label):
    if not np.allclose(actual, expected, rtol=1e-10, atol=1e-7):
        raise ValueError(f"Cashflow/identity reconciliation failed: {label}")


def _require(frame, columns, label):
    if not set(columns).issubset(frame.columns):
        raise ValueError(f"{label} missing columns: {sorted(set(columns) - set(frame.columns))}")


def _validated_paths(catalog, metrics, bets, equity):
    """Validate recorded accounting and return a shared date-by-rule matrix."""
    if not isinstance(catalog, list) or not catalog:
        raise ValueError("Catalog must be a nonempty list")
    ids = [row["strategy_id"] for row in catalog]
    if len(set(ids)) != len(ids):
        raise ValueError("Duplicate catalog identity")
    _require(metrics, ["strategy_id", "initial_bankroll", "profit", "bet_count",
                       "matched_valid_odds_count", "matched_match_dates", "final_capital_sum_units"], "metrics")
    _require(equity, ["strategy_id", "match_date", "matched_matches", "bet_count", "turnover",
                      "profit", "start_bankroll", "end_bankroll"], "equity")
    _require(bets, ["strategy_id", "match_id", "match_date", "result", "selection", "won",
                    "stake", "odds", "gross_return", "profit"], "bets")
    if metrics.strategy_id.duplicated().any() or set(metrics.strategy_id) != set(ids):
        raise ValueError("Metrics identities disagree with catalog")
    if set(equity.strategy_id) != set(ids) or not set(bets.strategy_id).issubset(ids):
        raise ValueError("Cashflow identities disagree with catalog")
    eq = equity.copy()
    bs = bets.copy()
    for frame in (eq, bs):
        frame["match_date"] = pd.to_datetime(frame.match_date, errors="raise")
        if frame.match_date.isna().any():
            raise ValueError("Missing match date")
    if eq.duplicated(["strategy_id", "match_date"]).any():
        raise ValueError("Duplicate strategy/date equity identity")
    if bs.duplicated(["strategy_id", "match_id"]).any():
        raise ValueError("Duplicate strategy/match bet identity")
    if bs.match_id.isna().any() or not bs.result.isin(["H", "D", "A"]).all() or not bs.selection.isin(["H", "D", "A"]).all():
        raise ValueError("Invalid match/outcome identity")
    if (bs.groupby("match_id").match_date.nunique() > 1).any() or (bs.groupby("match_id").result.nunique() > 1).any():
        raise ValueError("Conflicting match date or result identity")
    for frame, columns in ((eq, ["matched_matches", "bet_count", "turnover", "profit", "start_bankroll", "end_bankroll"]),
                           (bs, ["stake", "odds", "gross_return", "profit"])):
        if not np.isfinite(frame[columns].to_numpy(dtype=float)).all():
            raise ValueError("Nonfinite cashflow")
    if (eq.matched_matches <= 0).any() or (eq.matched_matches % 1 != 0).any() or (eq.bet_count < 0).any() or (eq.bet_count % 1 != 0).any():
        raise ValueError("Invalid opportunity/bet count")
    if (eq.bet_count > eq.matched_matches).any() or (eq.turnover < 0).any():
        raise ValueError("Invalid date exposure/count")
    if (bs.stake <= 0).any() or (bs.odds <= 1).any():
        raise ValueError("Invalid stake or price")
    _close(bs.won.astype(float), (bs.selection == bs.result).astype(float), "bet win identity")
    _close(bs.gross_return, bs.stake * bs.odds * bs.won.astype(float), "gross settlement")
    _close(bs.profit, bs.gross_return - bs.stake, "bet net profit")
    pnl = eq.pivot(index="match_date", columns="strategy_id", values="profit").reindex(columns=ids).sort_index()
    counts = eq.pivot(index="match_date", columns="strategy_id", values="matched_matches").reindex(index=pnl.index, columns=ids)
    if pnl.isna().any().any() or counts.isna().any().any():
        raise ValueError("Strategies do not share every priced match date")
    if not (counts.to_numpy() == counts.iloc[:, [0]].to_numpy()).all():
        raise ValueError("Strategies have different date opportunity counts")
    date_counts = counts.iloc[:, 0].astype(int)
    met = metrics.set_index("strategy_id")
    bet_dates = bs.groupby(["strategy_id", "match_date"]).agg(profit=("profit", "sum"), turnover=("stake", "sum"), bet_count=("stake", "size"))
    eq_index = eq.set_index(["strategy_id", "match_date"])
    if not bet_dates.index.isin(eq_index.index).all():
        raise ValueError("Bet is outside the equity date universe")
    bet_dates = bet_dates.reindex(eq_index.index, fill_value=0)
    for column in ("profit", "turnover", "bet_count"):
        _close(eq_index[column], bet_dates[column], f"date {column}")
    names = {}
    for config in catalog:
        key = config["strategy_id"]
        path = eq.loc[eq.strategy_id == key].sort_values("match_date")
        row = met.loc[key]
        _close(row.initial_bankroll, INITIAL_BANKROLL, "initial capital")
        _close(path.start_bankroll.iloc[0], INITIAL_BANKROLL, "first date capital")
        _close(path.start_bankroll.iloc[1:], path.end_bankroll.iloc[:-1], "continuous capital")
        _close(path.end_bankroll - path.start_bankroll, path.profit, "date capital change")
        if (path.start_bankroll < -1e-7).any() or (path.turnover > path.start_bankroll + 1e-7).any() or (path.end_bankroll < -1e-7).any():
            raise ValueError("Unfunded recorded cashflow")
        _close(path.profit.sum(), row.profit, "metric net profit")
        _close(path.bet_count.sum(), row.bet_count, "metric bet count")
        _close(path.matched_matches.sum(), row.matched_valid_odds_count, "metric opportunity count")
        _close(len(path), row.matched_match_dates, "metric priced date count")
        _close(path.end_bankroll.iloc[-1], row.final_capital_sum_units, "metric final capital")
        if config.get("cash_only", False) and ((path.profit != 0).any() or (path.bet_count != 0).any()):
            raise ValueError("Cash policy traded")
        names[key] = config.get("name", key)
    return pnl, date_counts, names


def _circular_indices(rng, n_dates, count, block_length):
    """Shared fixed-length circular blocks, truncated to the original date count."""
    starts = rng.integers(0, n_dates, (count, int(np.ceil(n_dates / block_length))))
    return ((starts[:, :, None] + np.arange(block_length)) % n_dates).reshape(count, -1)[:, :n_dates]


def _bootstrap_deviations(pnl, *, block_length, bootstrap_samples, seed):
    values = np.asarray(pnl, dtype=float)
    if values.ndim != 2 or values.shape[0] < 2 or values.shape[1] < 1 or not np.isfinite(values).all():
        raise ValueError("A finite date-by-strategy matrix with at least two dates is required")
    if not isinstance(block_length, int) or isinstance(block_length, bool) or not 1 <= block_length <= len(values):
        raise ValueError("Invalid circular block length")
    if not isinstance(bootstrap_samples, int) or isinstance(bootstrap_samples, bool) or bootstrap_samples < 1:
        raise ValueError("bootstrap_samples must be a positive integer")
    rng = np.random.default_rng(seed)
    centered = values - values.mean(axis=0)
    deviations = np.empty((bootstrap_samples, values.shape[1]))
    for offset in range(0, bootstrap_samples, 256):
        count = min(256, bootstrap_samples - offset)
        indices = _circular_indices(rng, len(values), count, block_length)
        deviations[offset:offset + count] = centered[indices].mean(axis=1)
    return deviations


def _summarize_family(observed, deviations, *, alpha=0.05):
    observed = np.asarray(observed, dtype=float)
    deviations = np.asarray(deviations, dtype=float)
    if deviations.ndim != 2 or observed.shape != (deviations.shape[1],) or not np.isfinite(observed).all() or not np.isfinite(deviations).all():
        raise ValueError("Invalid observed/bootstrap family")
    maximum = np.maximum(0.0, deviations.max(axis=1))
    denominator = len(deviations) + 1
    raw = (1 + (deviations >= observed).sum(axis=0)) / denominator
    adjusted = (1 + (maximum[:, None] >= observed).sum(axis=0)) / denominator
    global_p = (1 + (maximum >= max(0.0, observed.max())).sum()) / denominator
    critical = float(np.quantile(np.abs(deviations).max(axis=1), 1 - alpha, method="higher"))
    pointwise = np.quantile(np.abs(deviations), 1 - alpha, axis=0, method="higher")
    structural_zero = (observed == 0) & (deviations == 0).all(axis=0)
    return {"raw_p": raw, "adjusted_p": adjusted, "global_p": float(global_p),
            "critical": critical, "pointwise": pointwise, "structural_zero": structural_zero}


def run_selection_audit(legacy_dir: Path, output_dir: Path, *, bootstrap_samples=19999, seed=20261015) -> dict:
    """Write 672 conditional comparison rows and eight separately scoped families."""
    legacy_dir, output_dir = Path(legacy_dir), Path(output_dir)
    paths = [legacy_dir / name for name in ("catalog.json", "metrics.parquet", "bets.parquet", "equity.parquet")]
    catalog = json.loads(paths[0].read_text(encoding="utf-8"))
    metrics, bets, equity = [pd.read_parquet(path) for path in paths[1:]]
    if [row["strategy_id"] for row in catalog] != [f"S{i:03d}" for i in range(1, 85)]:
        raise ValueError("The full frozen S001..S084 catalog is required")
    pnl, date_counts, names = _validated_paths(catalog, metrics, bets, equity)
    if pnl.shape != (113, 84) or date_counts.sum() != 374:
        raise ValueError("Expected exactly 113 common priced dates and 374 opportunities")
    if len(bets.loc[bets.strategy_id == "S042"]) != 374:
        raise ValueError("S042 must cover every quoted opportunity")
    favorite = next(row for row in catalog if row["strategy_id"] == "S042")
    if favorite["selection_rule"] != "market_favorite" or favorite["staking"] != "fixed":
        raise ValueError("S042 benchmark identity changed")
    n_dates, n_rules = pnl.shape
    values = pnl.to_numpy()
    observed_profit = values.mean(axis=0)
    favorite_index = list(pnl.columns).index("S042")
    distinct = len(np.unique(values.T, axis=0))
    comparisons, globals_ = [], []
    for block in BLOCK_LENGTHS:
        block_seed = seed + block
        # Generate once: both benchmark comparisons use exactly the same draws.
        base_deviations = _bootstrap_deviations(values, block_length=block, bootstrap_samples=bootstrap_samples, seed=block_seed)
        for benchmark_id, benchmark_name in (("cash", "Cash (zero profit)"), ("S042", names["S042"])):
            benchmark_mean = 0.0 if benchmark_id == "cash" else observed_profit[favorite_index]
            benchmark_deviations = 0.0 if benchmark_id == "cash" else base_deviations[:, [favorite_index]]
            observed = observed_profit - benchmark_mean
            deviations = base_deviations - benchmark_deviations
            result = _summarize_family(observed, deviations)
            for i, strategy_id in enumerate(pnl.columns):
                zero = bool(result["structural_zero"][i])
                width = 0.0 if zero else result["critical"]
                point_width = float(result["pointwise"][i])
                low, high = float(observed[i] - width), float(observed[i] + width)
                comparisons.append({"benchmark_id": benchmark_id, "benchmark_name": benchmark_name,
                    "block_length": block, "bootstrap_samples": bootstrap_samples, "seed": block_seed,
                    "strategy_id": strategy_id, "strategy_name": names[strategy_id], "family_size": n_rules,
                    "matched_match_dates": n_dates, "initial_bankroll": INITIAL_BANKROLL,
                    "mean_date_excess_profit_units": float(observed[i]), "period_excess_profit_units": float(observed[i] * n_dates),
                    "excess_return_on_initial_capital": float(observed[i] * n_dates / INITIAL_BANKROLL),
                    "raw_one_sided_p": float(result["raw_p"][i]), "family_adjusted_one_sided_p": float(result["adjusted_p"][i]),
                    "pointwise_ci_low_mean_date_units": float(observed[i] - point_width),
                    "pointwise_ci_high_mean_date_units": float(observed[i] + point_width),
                    "simultaneous_ci_low_mean_date_units": low, "simultaneous_ci_high_mean_date_units": high,
                    "simultaneous_ci_low_period_units": low * n_dates, "simultaneous_ci_high_period_units": high * n_dates,
                    "simultaneous_ci_low_capital_return": low * n_dates / INITIAL_BANKROLL,
                    "simultaneous_ci_high_capital_return": high * n_dates / INITIAL_BANKROLL,
                    "structural_zero_comparison": zero,
                    "inference_status": "exploratory_conditional_recorded_cashflow_sensitivity"})
            globals_.append({"benchmark_id": benchmark_id, "benchmark_name": benchmark_name,
                "block_length": block, "bootstrap_samples": bootstrap_samples, "seed": block_seed,
                "family_size": n_rules, "distinct_recorded_paths": distinct, "matched_match_dates": n_dates,
                "matched_fixtures": int(date_counts.sum()), "best_observed_strategy_id": str(pnl.columns[np.argmax(observed)]),
                "max_observed_mean_date_excess_profit_units": float(observed.max()),
                "global_one_sided_p": result["global_p"], "simultaneous_95_critical_mean_date_units": result["critical"],
                "reject_global_at_05": bool(result["global_p"] < 0.05),
                "inference_status": "exploratory_conditional_recorded_cashflow_sensitivity"})
    output_dir.mkdir(parents=True, exist_ok=True)
    for stem, frame in (("selection_comparison", pd.DataFrame(comparisons)), ("selection_global", pd.DataFrame(globals_))):
        frame.to_csv(output_dir / f"{stem}.csv", index=False)
        frame.to_parquet(output_dir / f"{stem}.parquet", index=False)
    date_pnl = pnl.copy()
    date_pnl.insert(0, "matched_fixtures", date_counts)
    date_pnl.reset_index().to_csv(output_dir / "selection_date_pnl.csv", index=False)
    method = {"method": "conditional_cashflow_max_statistic_sensitivity", "estimand": "mean excess net P&L per priced match date, including no-bet dates",
        "unit": "money units per priced match date", "family_size": n_rules, "distinct_recorded_paths": distinct,
        "matched_match_dates": n_dates, "matched_fixtures": int(date_counts.sum()), "initial_bankroll": INITIAL_BANKROLL,
        "date_start": str(pnl.index.min().date()), "date_end": str(pnl.index.max().date()),
        "bootstrap_samples": bootstrap_samples, "seed": seed, "block_seed_rule": "seed + block_length",
        "block_lengths": list(BLOCK_LENGTHS), "benchmarks": ["cash", "S042"], "confidence_level": 0.95,
        "algorithm": "Fixed-length circular blocks sample 113 dates with wraparound, truncated at 113; identical indices apply to every strategy and both benchmarks. Center recorded date profits by their original means, then subtract benchmark deviations.",
        "p_value_definition": "(1 + count(centered bootstrap statistic >= observed statistic))/(B+1); the one-sided global statistic and resampled maxima are clipped below at zero. Individual adjusted p-values use the same maximum over all 84 candidates.",
        "interval_definition": "Symmetric two-sided 95% intervals use the higher empirical quantile of max absolute centered mean-date deviations across all 84 rules; pointwise intervals use each rule's absolute deviations. Identically zero comparisons have exact zero conditional intervals.",
        "period_conversion": f"Mean-date effects and interval endpoints multiply by {n_dates}; capital-return equivalents divide that fixed-period difference by {INITIAL_BANKROLL:g}. This does not simulate alternative compounded wealth paths.",
        "family_scope": "Eight separate 84-rule families: each benchmark and each of the four block lengths is reported. No joint correction across benchmarks/block choices and no block length selected for significance.",
        "duplicate_policy": f"All 84 IDs remain, including eight cash rules; identical vectors do not increase a maximum statistic. There are {distinct} distinct recorded date-profit paths.",
        "limitations": ["Previously inspected season and retrospectively designed rules: no fresh validation or confirmed winner.",
            "Recorded models, prices, selections and stakes are fixed. Kelly/dynamic stakes depend on the realized capital path; resampling does not rerun allocation or model fitting.",
            "Approximate resampling diagnostics rely on plausible stationarity and weak dependence; a single season, irregular match-date spacing and changing bankrolls limit those assumptions.",
            "Only the declared 84-rule family is counted; earlier searches, feature choices and model selection outside it are not corrected.",
            "This is not a full White Reality Check, a Romano-Wolf stepdown procedure, or a guarantee of strong familywise error control.",
            "Archived best-book quotes lack verified simultaneous execution and source quote timestamps."],
        "source_urls": SOURCE_URLS,
        "source_artifacts": [{"path": str(path.resolve()), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()} for path in paths],
        "global_results": globals_}
    (output_dir / "selection_method.json").write_text(json.dumps(method, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return method
