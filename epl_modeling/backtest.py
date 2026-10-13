"""Retrospective EPL odds comparison and date-batched value-betting simulation.

Prices are archived snapshots, not synchronized executable quotes. Preclosing and
closing panels are built separately. No exchange, market aggregate, or stale
Pinnacle quote enters a panel. Mathematical arbitrage candidates are descriptive;
they are never reported as realized/executable arbitrage profits.

Kelly fraction for a single binary settlement at decimal price o is
max(0, (p*o-1)/(o-1)); apply the chosen fraction and a per-bet cap. This is not
a jointly optimized portfolio Kelly allocation across matches. Same-day capital
commitments are scaled to the date-start bankroll before any settlement.

Sources: https://www.football-data.co.uk/data.php ; Kelly (1956),
https://www.princeton.edu/~wbialek/rome/refs/kelly_56.pdf
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

OUTCOMES = ("H", "D", "A")
PRICE_COLUMNS = ("decimal_odds_home", "decimal_odds_draw", "decimal_odds_away")
INDIVIDUAL_PREFIXES = frozenset({
    "1XB", "B365", "BF", "BFD", "BMGM", "BV", "BS", "BW", "CL", "GB",
    "IW", "LB", "PP", "PS", "P", "SK", "SKB", "SO", "SB", "SJ", "SY", "VC", "WH",
})
PINNACLE_UNRELIABLE_FROM = pd.Timestamp("2025-07-23")
BET_COLUMNS = [
    "match_id", "match_date", "result", "selection", "probability", "odds", "bookmaker",
    "edge", "full_kelly_fraction", "requested_stake", "stake", "won", "gross_return",
    "profit", "date_start_bankroll", "date_end_bankroll", "commitment_scale", "staking",
    "odds_mode", "snapshot_type", "threshold",
]
EQUITY_COLUMNS = [
    "match_date", "matched_matches", "qualified_matches", "bet_count", "start_bankroll",
    "requested_stakes", "commitment_scale", "turnover", "profit", "end_bankroll",
    "daily_return", "running_peak", "drawdown", "log_growth", "bankroll_start", "bankroll_end",
]


def _dates(values: pd.Series) -> pd.Series:
    """Use each printed calendar date, without an implicit timezone conversion."""
    dates = pd.to_datetime(values.astype("string").str[:10], format="%Y-%m-%d", errors="raise")
    if dates.isna().any():
        raise ValueError("Match calendar dates must be present")
    return dates


def _require_columns(frame: pd.DataFrame, columns, label: str) -> None:
    missing = sorted(set(columns) - set(frame))
    if missing:
        raise ValueError(f"{label} is missing columns: {missing}")


def _football_data_folder(data_root: Path) -> Path:
    root = Path(data_root)
    for folder in (root / "data/processed/football_data", root / "processed/football_data",
                   root / "football_data", root):
        if (folder / "match_odds_1x2_long.parquet").exists():
            return folder
    raise FileNotFoundError(f"No collected Football-Data odds table below {root}")


def build_odds_panel(
    data_root: Path, *, snapshot: str = "preclosing", require_reference: bool = True,
    division: str = "E0",
) -> tuple[pd.DataFrame, dict]:
    """Return one complete-price row per match and a source/price-quality audit.

    Best H/D/A prices may come from different actual bookmakers, always from the
    same requested snapshot. Every contributing bookmaker must supply a complete,
    finite triplet with all three decimal odds >1. Default reference availability
    is a complete Bet365 triplet so reference/best-price backtests share matches.

    ``data_root`` accepts epl_data, its processed directory, or football_data.
    The returned ``match_id`` is Football-Data's native source_match_key.
    ``ref_p_*`` are proportional, de-vigged Bet365 implied probabilities.
    """
    if snapshot not in {"preclosing", "closing"}:
        raise ValueError("snapshot must be 'preclosing' or 'closing'")
    folder = _football_data_folder(data_root)
    quotes = pd.read_parquet(folder / "match_odds_1x2_long.parquet").copy()
    matches = pd.read_parquet(folder / "matches_current_cohort.parquet").copy()
    _require_columns(quotes, ["source_match_key", "season", "division", "match_date", "snapshot_type",
                     "source_prefix", "bookmaker_or_aggregate", "is_market_aggregate", "is_exchange",
                     "quote_timestamp_utc", *PRICE_COLUMNS], "odds source")
    _require_columns(matches, ["source_match_key", "season", "division", "match_date", "FTR", "completed_asof"], "match source")
    audit = {"input_quote_rows": len(quotes), "snapshot_type": snapshot, "division": division,
             "require_complete_bet365_reference": bool(require_reference), "rejections": {}}

    def keep(mask, reason):
        nonlocal quotes
        mask = mask.fillna(False).astype(bool)
        audit["rejections"][reason] = int((~mask).sum())
        quotes = quotes.loc[mask].copy()

    keep(quotes["division"].eq(division), "other_division")
    keep(quotes["snapshot_type"].eq(snapshot), "other_snapshot")
    keep(quotes["source_prefix"].isin(INDIVIDUAL_PREFIXES)
         & ~quotes["is_market_aggregate"].fillna(True).astype(bool)
         & ~quotes["is_exchange"].fillna(True).astype(bool), "aggregate_exchange_or_unknown_bookmaker")
    quotes["match_date"] = _dates(quotes["match_date"])
    is_pinnacle = quotes["source_prefix"].isin({"PS", "P"}) | quotes["bookmaker_or_aggregate"].astype("string").str.casefold().eq("pinnacle")
    stale = quotes["match_date"].ge(PINNACLE_UNRELIABLE_FROM)
    if "pinnacle_stale_warning" in quotes:
        stale |= quotes["pinnacle_stale_warning"].fillna(False).astype(bool)
    keep(~(is_pinnacle & stale), "unreliable_pinnacle")
    for column in PRICE_COLUMNS:
        quotes[column] = pd.to_numeric(quotes[column], errors="coerce")
    price_array = quotes[list(PRICE_COLUMNS)].to_numpy(dtype=float)
    keep(pd.Series(np.isfinite(price_array).all(axis=1) & (price_array > 1).all(axis=1), index=quotes.index),
         "invalid_or_incomplete_triplet")
    quotes["match_id"] = quotes["source_match_key"].astype("string")
    # Exact duplicate native records are harmless; conflicting prices for an
    # identical book/snapshot cannot be resolved without a trustworthy clock.
    duplicate_key = ["match_id", "bookmaker_or_aggregate", "snapshot_type"]
    original_count = len(quotes)
    quotes = quotes.drop_duplicates(duplicate_key + list(PRICE_COLUMNS) + ["quote_timestamp_utc"])
    audit["identical_duplicate_quotes_removed"] = original_count - len(quotes)
    if quotes.duplicated(duplicate_key).any():
        raise ValueError("Conflicting bookmaker triplets for one match and snapshot")
    matches = matches.loc[matches["division"].eq(division) & matches["completed_asof"].fillna(False)
                          & matches["FTR"].isin(OUTCOMES)].copy()
    matches["match_id"] = matches["source_match_key"].astype("string")
    matches["match_date"] = _dates(matches["match_date"])
    if matches["match_id"].isna().any() or matches["match_id"].duplicated().any():
        raise ValueError("Match source IDs must be present and unique")
    match_dates = matches.set_index("match_id")["match_date"]
    source_dates = quotes["match_id"].map(match_dates)
    keep(source_dates.notna(), "no_completed_match_record")
    if not quotes["match_date"].eq(quotes["match_id"].map(match_dates)).all():
        raise ValueError("Quote date conflicts with native match calendar date")
    audit["eligible_complete_quote_rows"] = len(quotes)
    audit["quotes_per_season_bookmaker"] = quotes.groupby(
        ["season", "bookmaker_or_aggregate", "source_prefix"], as_index=False).size().rename(columns={"size": "quote_count"}).to_dict("records")
    base_columns = ["match_id", "match_date", "season", "FTR"]
    panel = matches[base_columns].rename(columns={"FTR": "result"}).set_index("match_id")
    reference = quotes.loc[quotes["source_prefix"].eq("B365")].set_index("match_id")
    if reference.index.has_duplicates:
        raise ValueError("More than one reference triplet per match")
    for outcome, column in zip(OUTCOMES, PRICE_COLUMNS):
        panel[f"ref_odds_{outcome}"] = reference[column]
    panel["reference_bookmaker"] = "Bet365"
    panel["reference_quote_timestamp_utc"] = reference["quote_timestamp_utc"]
    # Lexical bookmaker order provides deterministic resolution of price ties.
    ordered = quotes.sort_values(["match_id", "bookmaker_or_aggregate", "source_prefix"], kind="stable")
    for outcome, column in zip(OUTCOMES, PRICE_COLUMNS):
        selected = ordered.loc[ordered.groupby("match_id")[column].idxmax()].set_index("match_id")
        panel[f"odds_{outcome}"] = selected[column]
        panel[f"bookmaker_{outcome}"] = selected["bookmaker_or_aggregate"]
        panel[f"quote_timestamp_{outcome}_utc"] = selected["quote_timestamp_utc"]
    panel["eligible_bookmaker_count"] = quotes.groupby("match_id")["bookmaker_or_aggregate"].nunique()
    panel["snapshot_type"] = snapshot
    best_complete = panel[[f"odds_{outcome}" for outcome in OUTCOMES]].notna().all(axis=1)
    ref_complete = panel[[f"ref_odds_{outcome}" for outcome in OUTCOMES]].notna().all(axis=1)
    audit["matches_with_best_complete_triplet"] = int(best_complete.sum())
    audit["matches_with_complete_bet365_triplet"] = int(ref_complete.sum())
    audit["excluded_matches_missing_reference"] = int((best_complete & ~ref_complete).sum()) if require_reference else 0
    panel = panel.loc[best_complete & (ref_complete if require_reference else True)].copy()
    ref_inverse = 1 / panel[[f"ref_odds_{outcome}" for outcome in OUTCOMES]].to_numpy(float)
    ref_denominator = ref_inverse.sum(axis=1)
    for index, outcome in enumerate(OUTCOMES):
        panel[f"ref_p_{outcome}"] = ref_inverse[:, index] / ref_denominator
    best_inverse = 1 / panel[[f"odds_{outcome}" for outcome in OUTCOMES]].to_numpy(float)
    inverse_sum = best_inverse.sum(axis=1)
    panel["arb_inverse_odds_sum"] = inverse_sum
    panel["mathematical_arb_candidate"] = inverse_sum < 1 - 1e-12
    for index, outcome in enumerate(OUTCOMES):
        panel[f"arb_stake_weight_{outcome}"] = best_inverse[:, index] / inverse_sum
    panel["arb_theoretical_gross_return_per_unit"] = 1 / inverse_sum
    panel["arb_theoretical_margin"] = 1 / inverse_sum - 1
    clock_columns = [f"quote_timestamp_{outcome}_utc" for outcome in OUTCOMES]
    clocks = panel[clock_columns].apply(lambda column: pd.to_datetime(column, utc=True, errors="coerce", format="mixed"))
    panel["selected_quote_timestamps_missing"] = clocks.isna().any(axis=1)
    panel["selected_quote_timestamps_differ"] = clocks.nunique(axis=1).gt(1)
    panel["quotes_asynchronous_or_unverified"] = panel["selected_quote_timestamps_missing"] | panel["selected_quote_timestamps_differ"]
    panel["retrospective_only"] = True
    panel["executable_arbitrage_verified"] = False
    panel = panel.reset_index().sort_values(["match_date", "match_id"]).reset_index(drop=True)
    candidate_columns = ["match_id", "match_date", "season", "snapshot_type", "arb_inverse_odds_sum",
                         "arb_theoretical_margin", "quotes_asynchronous_or_unverified"]
    candidate_columns += [f"{prefix}_{outcome}" for outcome in OUTCOMES for prefix in ("odds", "bookmaker", "arb_stake_weight")]
    candidates = panel.loc[panel["mathematical_arb_candidate"], candidate_columns].copy()
    candidates["match_date"] = candidates["match_date"].dt.strftime("%Y-%m-%d")
    audit.update({"panel_matches": len(panel), "mathematical_arb_candidate_count": len(candidates),
                  "candidate_arb_matches": candidates.to_dict("records"),
                  "panel_matches_per_season": panel.groupby("season").size().to_dict(),
                  "quote_clocks_unverified_matches": int(panel["quotes_asynchronous_or_unverified"].sum()),
                  "arbitrage_execution_verified": False,
                  "notes": ["Preclosing is an archived after-opening snapshot, not a verified opening quote.",
                            "Mathematical candidates combine complete individual-book triplets within one snapshot label; clocks, limits, fees and execution are unverified.",
                            "Closing odds are available only through a separate sensitivity panel; they must not inform an earlier forecast."]})
    return panel, audit


def _maximum_drawdown(bankrolls: np.ndarray) -> float:
    peaks = np.maximum.accumulate(bankrolls)
    return float(np.max(1 - bankrolls / peaks)) if len(bankrolls) else 0.0


def _date_bootstrap(equity: pd.DataFrame, samples: int, ci_level: float, random_state: int) -> dict:
    """Resample whole match dates, conditional on the fitted model and stakes.

    Cash profit/ROI resample the recorded date cashflows; growth/drawdown resample
    recorded date returns. This is not a re-fit or a re-optimization of Kelly stakes.
    """
    metrics = ("roi", "profit", "turnover", "log_growth", "max_drawdown", "bet_count")
    out = {metric: [None, None] for metric in metrics}
    if samples == 0 or equity.empty:
        return {"confidence_level": ci_level, "requested_samples": samples, "valid_roi_samples": 0,
                "method": "whole-match-date percentile bootstrap", "intervals": out}
    rng = np.random.default_rng(random_state)
    profits = equity["profit"].to_numpy(float)
    turnovers = equity["turnover"].to_numpy(float)
    counts = equity["bet_count"].to_numpy(int)
    returns = equity["daily_return"].to_numpy(float)
    records = {metric: [] for metric in metrics}
    for _ in range(samples):
        indices = rng.integers(0, len(equity), size=len(equity))
        profit = float(profits[indices].sum())
        turnover = float(turnovers[indices].sum())
        date_returns = returns[indices]
        wealth = np.concatenate(([1.0], np.cumprod(1 + date_returns)))
        records["profit"].append(profit)
        records["turnover"].append(turnover)
        records["bet_count"].append(float(counts[indices].sum()))
        if turnover > 0:
            records["roi"].append(profit / turnover)
        records["log_growth"].append(float(np.log(wealth[-1])) if wealth[-1] > 0 else -math.inf)
        records["max_drawdown"].append(_maximum_drawdown(wealth))
    quantiles = [(1 - ci_level) / 2, (1 + ci_level) / 2]
    for metric, values in records.items():
        if values:
            # A noninterpolating percentile also handles genuine -infinite growth.
            out[metric] = np.quantile(values, quantiles, method="inverted_cdf").astype(float).tolist()
    return {"confidence_level": ci_level, "requested_samples": samples, "valid_roi_samples": len(records["roi"]),
            "method": "whole-match-date percentile bootstrap; fixed recorded cashflows for ROI/profit, recorded date returns for growth/drawdown; no model refit",
            "intervals": out}


def simulate_bets(
    predictions: pd.DataFrame, odds: pd.DataFrame, *, threshold: float,
    staking: str = "fixed", odds_mode: str = "best", initial_bankroll: float = 1000.0,
    fixed_stake: float = 10.0, kelly_fraction: float = 0.25, max_bet_fraction: float = 0.02,
    bootstrap_samples: int = 1000, ci_level: float = 0.95, random_state: int = 42,
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Simulate one maximum-positive-edge selection per match above ``threshold``.

    predictions: match_id, match_date, result in H/D/A, p_H/p_D/p_A.
    odds: one unique match row, odds_H/D/A and optionally bookmaker_H/D/A.
    odds_mode='reference' selects ref_odds_* (Bet365); 'best' selects odds_*.
    ``staking`` accepts fixed or fractional_kelly (also kelly/quarter_kelly).
    Fixed stakes remain fixed except when total same-date commitments exceed the
    available bankroll. ``max_bet_fraction`` caps fractional-Kelly stakes only.
    ``threshold=math.inf`` is the explicitly locked no-bet fallback.

    The threshold must be chosen on a separate validation period and held fixed;
    this function never chooses/tunes a threshold using its supplied outcomes.
    It returns bet records, date-close equity including no-bet match dates, and
    hypothetical retrospective performance with date-cluster bootstrap intervals.
    """
    if staking not in {"fixed", "fractional_kelly", "kelly", "quarter_kelly"}:
        raise ValueError("staking must be fixed or fractional_kelly")
    if odds_mode not in {"best", "reference"}:
        raise ValueError("odds_mode must be best or reference")
    threshold = float(threshold)
    if math.isnan(threshold) or threshold < 0:
        raise ValueError("threshold must be nonnegative, or +infinity for no bets")
    for name, value in (("initial_bankroll", initial_bankroll), ("fixed_stake", fixed_stake)):
        if not np.isfinite(value) or value <= 0:
            raise ValueError(f"{name} must be finite and positive")
    if not np.isfinite(kelly_fraction) or not 0 < kelly_fraction <= 1:
        raise ValueError("kelly_fraction must lie in (0, 1]")
    if not np.isfinite(max_bet_fraction) or not 0 < max_bet_fraction <= 1:
        raise ValueError("max_bet_fraction must lie in (0, 1]")
    if not isinstance(bootstrap_samples, (int, np.integer)) or bootstrap_samples < 0:
        raise ValueError("bootstrap_samples must be a nonnegative integer")
    if not 0 < ci_level < 1:
        raise ValueError("ci_level must lie in (0, 1)")
    _require_columns(predictions, ["match_id", "match_date", "result", *[f"p_{outcome}" for outcome in OUTCOMES]], "predictions")
    selected_price_columns = [f"{'ref_' if odds_mode == 'reference' else ''}odds_{outcome}" for outcome in OUTCOMES]
    _require_columns(odds, ["match_id", "match_date", *selected_price_columns], "odds panel")
    pred = predictions[["match_id", "match_date", "result", *[f"p_{outcome}" for outcome in OUTCOMES]]].copy()
    prices = odds.copy()
    for frame, label in ((pred, "predictions"), (prices, "odds panel")):
        frame["match_id"] = frame["match_id"].astype("string")
        if frame["match_id"].isna().any() or frame["match_id"].duplicated().any():
            raise ValueError(f"{label} match_id must be present and unique")
        frame["match_date"] = _dates(frame["match_date"])
    if not pred["result"].isin(OUTCOMES).all():
        raise ValueError("prediction results must be H, D or A")
    probability_columns = [f"p_{outcome}" for outcome in OUTCOMES]
    probabilities = pred[probability_columns].apply(pd.to_numeric, errors="coerce").to_numpy(float)
    if (not np.isfinite(probabilities).all() or (probabilities < 0).any() or (probabilities > 1).any()
            or not np.allclose(probabilities.sum(axis=1), 1, rtol=0, atol=1e-6)):
        raise ValueError("probabilities must be finite, lie in [0,1], and sum to one")
    pred[probability_columns] = probabilities
    if "snapshot_type" in prices and prices["snapshot_type"].dropna().nunique() > 1:
        raise ValueError("Never mix preclosing and closing snapshots in one simulation")
    if "snapshot_type" not in prices:
        prices["snapshot_type"] = "unspecified_retrospective_snapshot"
    merged = pred.merge(prices, on="match_id", how="inner", validate="one_to_one", suffixes=("", "_odds"))
    if not merged["match_date"].eq(merged["match_date_odds"]).all():
        raise ValueError("Prediction and odds match dates disagree")
    if "result_odds" in merged and not merged["result"].eq(merged["result_odds"]).all():
        raise ValueError("Prediction and odds settlement results disagree")
    for outcome, column in zip(OUTCOMES, selected_price_columns):
        merged[f"selected_odds_{outcome}"] = pd.to_numeric(merged[column], errors="coerce")
        if odds_mode == "reference":
            merged[f"selected_bookmaker_{outcome}"] = merged.get("reference_bookmaker", "Bet365")
        else:
            merged[f"selected_bookmaker_{outcome}"] = merged.get(f"bookmaker_{outcome}", "unspecified_individual_bookmaker")
    price_array = merged[[f"selected_odds_{outcome}" for outcome in OUTCOMES]].to_numpy(float)
    valid_odds = np.isfinite(price_array).all(axis=1) & (price_array > 1).all(axis=1)
    invalid_odds_rows = int((~valid_odds).sum())
    merged = merged.loc[valid_odds].sort_values(["match_date", "match_id"], kind="stable").reset_index(drop=True)
    if not merged.empty:
        price_array = merged[[f"selected_odds_{outcome}" for outcome in OUTCOMES]].to_numpy(float)
        probability_array = merged[probability_columns].to_numpy(float)
        edges = probability_array * price_array - 1
        choice = edges.argmax(axis=1)  # deterministic H, then D, then A on ties
        row_index = np.arange(len(merged))
        merged["selection"] = np.asarray(OUTCOMES)[choice]
        merged["probability"] = probability_array[row_index, choice]
        merged["selected_odds"] = price_array[row_index, choice]
        merged["edge"] = edges[row_index, choice]
        book_array = merged[[f"selected_bookmaker_{outcome}" for outcome in OUTCOMES]].to_numpy()
        merged["selected_bookmaker"] = book_array[row_index, choice]
    bankroll = float(initial_bankroll)
    peak = bankroll
    bet_records, equity_records = [], []
    for date, day in merged.groupby("match_date", sort=True):
        start_bankroll = bankroll
        qualified = day.loc[day["edge"].gt(threshold)].copy()
        full_kelly = np.maximum(0, qualified["edge"].to_numpy(float) / (qualified["selected_odds"].to_numpy(float) - 1))
        if staking == "fixed":
            requested = np.full(len(qualified), float(fixed_stake)) if start_bankroll > 0 else np.zeros(len(qualified))
        else:
            requested = start_bankroll * np.minimum(max_bet_fraction, kelly_fraction * full_kelly)
        requested_sum = float(requested.sum())
        scale = min(1.0, start_bankroll / requested_sum) if requested_sum > 0 else 1.0
        stakes = requested * scale
        if len(stakes) and stakes.sum() > start_bankroll:
            stakes[-1] = max(0, stakes[-1] - (float(stakes.sum()) - start_bankroll))
        wins = qualified["selection"].eq(qualified["result"]).to_numpy(bool)
        gross = stakes * qualified["selected_odds"].to_numpy(float) * wins
        turnover = float(stakes.sum())
        profit = float((gross - stakes).sum())
        bankroll = max(0.0, start_bankroll - turnover + float(gross.sum()))
        peak = max(peak, bankroll)
        for position, record in enumerate(qualified.to_dict("records")):
            if stakes[position] <= 0:
                continue
            bet_records.append({
                "match_id": record["match_id"], "match_date": date, "result": record["result"],
                "selection": record["selection"], "probability": record["probability"],
                "odds": record["selected_odds"], "bookmaker": record["selected_bookmaker"],
                "edge": record["edge"], "full_kelly_fraction": float(full_kelly[position]),
                "requested_stake": float(requested[position]), "stake": float(stakes[position]),
                "won": bool(wins[position]), "gross_return": float(gross[position]),
                "profit": float(gross[position] - stakes[position]), "date_start_bankroll": start_bankroll,
                "date_end_bankroll": bankroll, "commitment_scale": scale, "staking": staking,
                "odds_mode": odds_mode, "snapshot_type": record["snapshot_type"], "threshold": threshold,
            })
        equity_records.append({
            "match_date": date, "matched_matches": len(day), "qualified_matches": len(qualified),
            "bet_count": int((stakes > 0).sum()), "start_bankroll": start_bankroll,
            "requested_stakes": requested_sum, "commitment_scale": scale, "turnover": turnover,
            "profit": profit, "end_bankroll": bankroll,
            "daily_return": bankroll / start_bankroll - 1 if start_bankroll > 0 else 0.0,
            "running_peak": peak, "drawdown": 1 - bankroll / peak,
            "log_growth": math.log(bankroll / initial_bankroll) if bankroll > 0 else -math.inf,
            "bankroll_start": start_bankroll, "bankroll_end": bankroll,
        })
    bets = pd.DataFrame(bet_records, columns=BET_COLUMNS)
    for column in ("probability", "odds", "edge", "full_kelly_fraction", "requested_stake", "stake",
                   "gross_return", "profit", "date_start_bankroll", "date_end_bankroll", "commitment_scale", "threshold"):
        bets[column] = bets[column].astype(float)
    equity = pd.DataFrame(equity_records, columns=EQUITY_COLUMNS)
    turnover = float(bets["stake"].sum()) if not bets.empty else 0.0
    profit = float(bankroll - initial_bankroll)
    wealth = np.concatenate(([float(initial_bankroll)], equity["end_bankroll"].to_numpy(float)))
    bootstrap = _date_bootstrap(equity, bootstrap_samples, ci_level, random_state)
    summary = {
        "staking": staking, "odds_mode": odds_mode, "threshold": threshold,
        "initial_bankroll": float(initial_bankroll), "final_bankroll": bankroll,
        "fixed_stake": float(fixed_stake), "kelly_fraction": float(kelly_fraction),
        "max_bet_fraction": float(max_bet_fraction), "profit": profit, "turnover": turnover,
        "roi": profit / turnover if turnover > 0 else None,
        "log_growth": math.log(bankroll / initial_bankroll) if bankroll > 0 else -math.inf,
        "max_drawdown": _maximum_drawdown(wealth), "bet_count": len(bets),
        "win_rate": float(bets["won"].mean()) if len(bets) else None,
        "bankrupt": bankroll <= 0, "prediction_count": len(pred), "matched_valid_odds_count": len(merged),
        "unmatched_predictions": len(pred) - (len(merged) + invalid_odds_rows),
        "invalid_odds_rows_excluded": invalid_odds_rows, "match_dates": len(equity),
        "scaled_commitment_dates": int(equity["commitment_scale"].lt(1).sum()),
        "bootstrap": bootstrap,
        "roi_ci_low": bootstrap["intervals"]["roi"][0], "roi_ci_high": bootstrap["intervals"]["roi"][1],
        "retrospective_only": True, "arbitrage_profit_claimed": False,
        "notes": ["One outcome per match; threshold supplied externally and never optimized on these results.",
                  "All same-date stakes use the date-start bankroll; aggregate commitments are scaled before settlement.",
                  "Fractional Kelly is capped per bet; fixed stakes are reduced only by aggregate bankroll capacity.",
                  "Drawdown includes initial capital and is measured at date-close; intraday settlement ordering is not observed.",
                  "Bootstrap conditions on the recorded model, threshold and stakes; it does not include model-fitting or threshold-selection uncertainty.",
                  "Returns are hypothetical archived-price results, not verified executable betting returns."],
    }
    return bets, equity, summary
