"""Descriptive archived-price and selected-bet payoff diagnostics.

The normalized inverse Bet365 probabilities below are a reference market
benchmark, not true probabilities. Accounting identities do not establish a
forecasting edge. Quote labels have no verified individual capture clocks, so
none of these functions certifies execution or closing-line value.
"""
from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

import numpy as np
import pandas as pd


OUTCOMES = ("H", "D", "A")
ATTRIBUTION_TERMS = (
    "actual_profit", "model_expected_profit", "market_implied_expected_profit",
    "model_probability_premium", "outcome_residual", "payoff_forecast_error",
    "archived_ref_fixed_bet_profit", "realized_price_uplift_vs_reference",
)
BOOK_COLUMNS = [
    "bookmaker", "bet_count", "stake", "total_profit", "bet_share", "stake_share",
    "signed_profit_share", "concentration_hhi_by_bet_count",
    "concentration_hhi_by_stake", "largest_book_stake_share",
]


def _require(frame: pd.DataFrame, columns, label: str) -> None:
    missing = sorted(set(columns) - set(frame))
    if missing:
        raise ValueError(f"{label} missing columns: {missing}")


def _finite(frame: pd.DataFrame, columns, label: str) -> np.ndarray:
    try:
        values = frame[list(columns)].to_numpy(dtype=float)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} contains nonnumeric values") from exc
    if not np.isfinite(values).all():
        raise ValueError(f"{label} contains nonfinite values")
    return values


def _native(opportunities: pd.DataFrame) -> pd.DataFrame:
    _require(opportunities, ["match_id", "match_date", "season", "result"] +
             [f"ref_odds_{outcome}" for outcome in OUTCOMES], "Opportunities")
    native = opportunities.copy(deep=True)
    native["match_id"] = native.match_id.astype("string")
    if native.match_id.isna().any() or native.match_id.str.strip().eq("").any() or native.match_id.duplicated().any():
        raise ValueError("Opportunity match IDs must be present and unique")
    native["match_date"] = pd.to_datetime(native.match_date.astype("string").str[:10],
                                          format="%Y-%m-%d", errors="raise")
    if native.match_date.isna().any() or native.season.isna().any() or not native.result.isin(OUTCOMES).all():
        raise ValueError("Opportunities contain missing dates/seasons or invalid results")
    prices = _finite(native, [f"ref_odds_{outcome}" for outcome in OUTCOMES], "Reference odds")
    if not (prices > 1).all():
        raise ValueError("Reference decimal odds must be greater than one")
    inverse = 1.0 / prices
    q = inverse / inverse.sum(axis=1, keepdims=True)
    supplied = [f"ref_p_{outcome}" for outcome in OUTCOMES]
    if all(column in native for column in supplied):
        if not np.allclose(_finite(native, supplied, "Reference probabilities"), q, atol=1e-11, rtol=0):
            raise ValueError("Saved reference probabilities disagree with normalized inverse Bet365 odds")
    for index, outcome in enumerate(OUTCOMES):
        native[f"diagnostic_ref_p_{outcome}"] = q[:, index]
    if "reference_bookmaker" in native and not native.reference_bookmaker.eq("Bet365").all():
        raise ValueError("The reference book must be Bet365")
    return native.reset_index(drop=True)


def _aligned_bets(bets: pd.DataFrame, opportunities: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    native = _native(opportunities).set_index("match_id", drop=False)
    _require(bets, ["match_id", "selection", "probability", "odds", "stake"], "Bets")
    bets = bets.copy(deep=True)
    bets["match_id"] = bets.match_id.astype("string")
    if bets.match_id.isna().any() or bets.match_id.duplicated().any():
        raise ValueError("One diagnostic account must have at most one bet per match")
    if not bets.match_id.isin(native.index).all():
        raise ValueError("A bet match is absent from the native opportunities")
    matched = native.reindex(bets.match_id).reset_index(drop=True)
    bets = bets.reset_index(drop=True)
    values = _finite(bets, ["probability", "odds", "stake"], "Bets")
    if not ((values[:, 0] >= 0) & (values[:, 0] <= 1)).all() or not (values[:, 1] > 1).all() or not (values[:, 2] > 0).all():
        raise ValueError("Bets require probabilities in [0,1], odds >1 and positive stakes")
    if not bets.selection.isin(OUTCOMES).all():
        raise ValueError("Bet selections must be H/D/A")
    for column in ("result", "season"):
        if column in bets and not bets[column].eq(matched[column]).all():
            raise ValueError(f"Bet {column} conflicts with the native opportunity")
    if "match_date" in bets:
        dates = pd.to_datetime(bets.match_date.astype("string").str[:10], format="%Y-%m-%d", errors="raise")
        if not dates.eq(matched.match_date).all():
            raise ValueError("Bet date conflicts with the native opportunity")
    won = bets.selection.eq(matched.result).to_numpy()
    if "won" in bets and (bets.won.isna().any() or not bets.won.isin([True, False, 0, 1]).all() or
                          not np.array_equal(bets.won.to_numpy(dtype=bool), won)):
        raise ValueError("Bet won flag conflicts with the native result")
    bets["diagnostic_won"] = won
    calculated = bets.stake.to_numpy(float) * (won.astype(float) * bets.odds.to_numpy(float) - 1)
    if "profit" in bets and not np.allclose(_finite(bets, ["profit"], "Recorded profit").ravel(), calculated,
                                            atol=1e-8, rtol=1e-12):
        raise ValueError("Recorded profit does not reconcile with stake, odds and result")
    if "gross_return" in bets:
        expected_gross = calculated + bets.stake.to_numpy(float)
        if not np.allclose(_finite(bets, ["gross_return"], "Recorded gross return").ravel(), expected_gross,
                           atol=1e-8, rtol=1e-12):
            raise ValueError("Recorded gross return does not reconcile with stake, odds and result")
    return bets, matched


def quote_diagnostics(opportunities: pd.DataFrame, *, scope: str) -> tuple[dict, pd.DataFrame, pd.DataFrame]:
    """Audit one native opportunity population, without duplicating strategy rows.

    The third table counts the selected best-book *quote cells*, not executed
    trades and not every available bookmaker. Ties retain the frozen panel's
    deterministic chosen book. A saved best price below its eligible reference
    quote is a data integrity failure.
    """
    native = _native(opportunities)
    clock_columns = ["reference_quote_timestamp_utc"] + [f"quote_timestamp_{o}_utc" for o in OUTCOMES]
    _require(native, [f"odds_{o}" for o in OUTCOMES] + [f"bookmaker_{o}" for o in OUTCOMES] + clock_columns,
             "Quote panel")
    best = _finite(native, [f"odds_{o}" for o in OUTCOMES], "Best odds")
    reference = native[[f"ref_odds_{o}" for o in OUTCOMES]].to_numpy(float)
    if not (best > 1).all() or (best < reference - 1e-12).any():
        raise ValueError("Best prices must be valid and at least their eligible Bet365 reference")
    for outcome in OUTCOMES:
        if native[f"bookmaker_{outcome}"].isna().any() or native[f"bookmaker_{outcome}"].astype(str).str.strip().eq("").any():
            raise ValueError("Selected best-book identities must be present")
    clocks = {}
    for column in clock_columns:
        parsed = pd.to_datetime(native[column], errors="coerce", utc=True, format="mixed")
        if (native[column].notna() & parsed.isna()).any():
            raise ValueError("Quote timestamps contain malformed nonmissing values")
        clocks[column] = parsed
    rows = []
    for index, record in native.iterrows():
        for outcome in OUTCOMES:
            o, ref = float(record[f"odds_{outcome}"]), float(record[f"ref_odds_{outcome}"])
            q = float(record[f"diagnostic_ref_p_{outcome}"])
            rows.append({"scope": scope, "match_id": record.match_id, "match_date": record.match_date,
                         "season": record.season, "result": record.result, "outcome": outcome,
                         "best_odds": o, "reference_odds": ref, "best_bookmaker": record[f"bookmaker_{outcome}"],
                         "reference_bookmaker": "Bet365", "price_ratio_best_to_reference": o / ref,
                         "decimal_odds_uplift": o - ref, "reference_probability": q,
                         "reference_market_expected_roi_at_best": q * o - 1,
                         "reference_market_expected_roi_at_reference": q * ref - 1,
                         "best_quote_timestamp_utc": clocks[f"quote_timestamp_{outcome}_utc"].iloc[index],
                         "reference_quote_timestamp_utc": clocks["reference_quote_timestamp_utc"].iloc[index],
                         "executable_quotes_verified": False})
    outcomes = pd.DataFrame(rows)
    if outcomes.empty:
        # Real runs are nonempty; preserve an explicit error rather than emit a
        # superficially complete zero-quote execution audit.
        raise ValueError("Quote diagnostics require a nonempty opportunity panel")
    counts = outcomes.groupby("best_bookmaker", sort=True).size().rename("selected_quote_count").reset_index()
    counts = counts.rename(columns={"best_bookmaker": "bookmaker"})
    counts.insert(0, "scope", scope)
    counts["selected_quote_share"] = counts.selected_quote_count / len(outcomes)
    counts["selected_quote_hhi"] = float(np.square(counts.selected_quote_share).sum())
    summary = {"scope": scope, "match_count": int(len(native)), "outcome_quote_count": int(len(outcomes)),
               "selected_best_bookmaker_count": int(len(counts)), "all_best_at_least_reference": True,
               "best_below_reference_count": 0, "strict_best_price_uplift_count": int((best > reference + 1e-12).sum()),
               "mean_price_ratio_best_to_reference": float((best / reference).mean()),
               "median_price_ratio_best_to_reference": float(np.median(best / reference)),
               "reference_timestamp_missing_count": int(clocks["reference_quote_timestamp_utc"].isna().sum()),
               "executable_quotes_verified": False, "verified_closing_line_value": False,
               "interpretation": "Archived snapshot comparisons; quote ordering, simultaneous execution, limits and availability are unverified"}
    for outcome in OUTCOMES:
        summary[f"best_{outcome}_timestamp_missing_count"] = int(clocks[f"quote_timestamp_{outcome}_utc"].isna().sum())
    return summary, outcomes, counts


def payoff_attribution(bets: pd.DataFrame, opportunities: pd.DataFrame, *, account_id: str,
                       strategy_id: str, scope: str, season: str) -> dict:
    """Return exact selected-bet price/forecast attribution for one account.

    With q the normalized inverse reference-book odds and y the observed win,
    actual P = sum(s*(q*O-1)) + sum(s*O*(y-q)); model E[P] replaces y by p.
    Holding recorded selections and stakes while replacing O by reference odds
    is a shadow cashflow diagnostic, not a funded alternative-account replay.
    """
    bets, native = _aligned_bets(bets, opportunities)
    if "strategy_id" in bets and not bets.strategy_id.eq(strategy_id).all():
        raise ValueError("Bets contain a different strategy identity")
    indices = np.array([OUTCOMES.index(outcome) for outcome in bets.selection], dtype=int)
    row = np.arange(len(bets))
    q = native[[f"diagnostic_ref_p_{o}" for o in OUTCOMES]].to_numpy(float)[row, indices]
    reference_odds = native[[f"ref_odds_{o}" for o in OUTCOMES]].to_numpy(float)[row, indices]
    p, o, s = [bets[column].to_numpy(float) for column in ("probability", "odds", "stake")]
    y = bets.diagnostic_won.to_numpy(dtype=float)
    count, turnover = len(bets), float(s.sum())
    values = {
        "actual_profit": float(np.sum(s * (y * o - 1))),
        "model_expected_profit": float(np.sum(s * (p * o - 1))),
        "market_implied_expected_profit": float(np.sum(s * (q * o - 1))),
        "model_probability_premium": float(np.sum(s * o * (p - q))),
        "outcome_residual": float(np.sum(s * o * (y - q))),
        "payoff_forecast_error": float(np.sum(s * o * (y - p))),
        "archived_ref_fixed_bet_profit": float(np.sum(s * (y * reference_odds - 1))),
        "realized_price_uplift_vs_reference": float(np.sum(s * y * (o - reference_odds))),
    }
    result = {"account_id": account_id, "strategy_id": strategy_id, "scope": scope, "season": season,
              "bet_count": int(count), "turnover": turnover,
              "hit_ratio": float(y.mean()) if count else np.nan,
              "mean_model_probability": float(p.mean()) if count else np.nan,
              "mean_reference_probability": float(q.mean()) if count else np.nan,
              "hit_minus_mean_model_probability": float(np.mean(y - p)) if count else np.nan,
              "hit_minus_mean_reference_probability": float(np.mean(y - q)) if count else np.nan,
              "expected_gain_total": float(np.sum(s * p * (o - 1))),
              "expected_loss_total": float(np.sum(s * (1 - p))),
              "actual_gain_total": float(np.sum(s * y * (o - 1))),
              "actual_loss_total": float(np.sum(s * (1 - y))),
              "reference_probability_is_truth": False,
              "attribution_is_executable_edge_evidence": False,
              "fixed_exposure_reference_is_funded_replay": False, **values}
    for key in ATTRIBUTION_TERMS:
        result[f"{key}_per_turnover"] = values[key] / turnover if turnover else np.nan
        result[f"{key}_per_trade"] = values[key] / count if count else np.nan
    result["actual_profit_identity_residual"] = values["actual_profit"] - values["market_implied_expected_profit"] - values["outcome_residual"]
    result["model_expected_identity_residual"] = values["model_expected_profit"] - values["market_implied_expected_profit"] - values["model_probability_premium"]
    result["price_uplift_identity_residual"] = values["actual_profit"] - values["archived_ref_fixed_bet_profit"] - values["realized_price_uplift_vs_reference"]
    return result


def book_concentration(bets: pd.DataFrame, opportunities: pd.DataFrame,
                       accountmetadata: Mapping) -> pd.DataFrame:
    """Describe selected-book exposure within one account, never pool replicas.

    Signed profit shares can be negative or exceed 100% when other books offset
    gains/losses. HHI and maximum stake share are repeated account statistics;
    they must not be summed across book rows or overlapping strategy accounts.
    """
    if not isinstance(accountmetadata, Mapping):
        raise TypeError("accountmetadata must be a mapping")
    if set(accountmetadata) & set(BOOK_COLUMNS):
        raise ValueError("Account metadata cannot overwrite book metric columns")
    bets, _ = _aligned_bets(bets, opportunities)
    _require(bets, ["bookmaker"], "Bets")
    if bets.bookmaker.isna().any() or bets.bookmaker.astype(str).str.strip().eq("").any():
        raise ValueError("Bet bookmaker identities must be present")
    if bets.empty:
        return pd.DataFrame(columns=[*accountmetadata, *BOOK_COLUMNS])
    bets["diagnostic_profit"] = bets.stake.to_numpy(float) * (
        bets.diagnostic_won.to_numpy(float) * bets.odds.to_numpy(float) - 1)
    grouped = bets.groupby("bookmaker", sort=True).agg(
        bet_count=("match_id", "size"), stake=("stake", "sum"), total_profit=("diagnostic_profit", "sum")
    ).reset_index()
    grouped["bet_share"] = grouped.bet_count / len(bets)
    grouped["stake_share"] = grouped.stake / float(bets.stake.sum())
    total_profit = float(grouped.total_profit.sum())
    grouped["signed_profit_share"] = grouped.total_profit / total_profit if total_profit != 0 else np.nan
    grouped["concentration_hhi_by_bet_count"] = float(np.square(grouped.bet_share).sum())
    grouped["concentration_hhi_by_stake"] = float(np.square(grouped.stake_share).sum())
    grouped["largest_book_stake_share"] = float(grouped.stake_share.max())
    for index, (key, value) in enumerate(accountmetadata.items()):
        grouped.insert(index, key, value)
    return grouped


def load_archived_closing_reference(root: Path, opportunities: pd.DataFrame) -> tuple[pd.DataFrame, list[Path]]:
    """Read a separately built closing panel, strictly matching native identities.

    Return the two consumed frozen raw/processed source paths for hashing by the
    caller. No closing value is fed into forecasts, selection or stake sizing.
    """
    from epl_modeling.backtest import build_odds_panel, _football_data_folder

    root = Path(root).resolve()
    data_root = root / "epl_data" if (root / "epl_data").is_dir() else root
    folder = _football_data_folder(data_root)
    panel, _ = build_odds_panel(data_root, snapshot="closing")
    native = _native(opportunities)
    panel = panel.loc[panel.match_id.isin(native.match_id)].copy()
    _validate_closing_pair(native, panel)
    panel = panel.set_index("match_id", drop=False).reindex(native.match_id).reset_index(drop=True)
    sources = [folder / "match_odds_1x2_long.parquet", folder / "matches_current_cohort.parquet"]
    return panel, sources


def _validate_closing_pair(native: pd.DataFrame, closing: pd.DataFrame) -> pd.DataFrame:
    close = _native(closing)
    if set(native.match_id) != set(close.match_id):
        raise ValueError("Closing and preclosing native match populations differ")
    close = close.set_index("match_id", drop=False).reindex(native.match_id).reset_index(drop=True)
    for column in ("match_date", "season", "result"):
        if not native[column].reset_index(drop=True).eq(close[column]).all():
            raise ValueError(f"Closing {column} conflicts with the preclosing native identity")
    if "snapshot_type" not in native or not native.snapshot_type.eq("preclosing").all():
        raise ValueError("The entry benchmark must contain only archived preclosing snapshots")
    if "snapshot_type" not in close or not close.snapshot_type.eq("closing").all():
        raise ValueError("The closing benchmark must contain only archived closing snapshots")
    return close


def closing_reference_diagnostics(opportunities: pd.DataFrame, closingpanel: pd.DataFrame,
                                  *, scope: str) -> tuple[dict, pd.DataFrame]:
    """Compare archived Bet365 with archived Bet365, using the same bookmaker.

    Entry/closing decimal-odds ratios and normalized implied probabilities are
    descriptive. Without verified clocks this is not a realized CLV measure.
    """
    native = _native(opportunities)
    close = _validate_closing_pair(native, closingpanel)
    _require(native, ["reference_quote_timestamp_utc"], "Entry panel")
    _require(close, ["reference_quote_timestamp_utc"], "Closing panel")
    rows = []
    for index, record in native.iterrows():
        final = close.iloc[index]
        for outcome in OUTCOMES:
            entry_odds, closing_odds = float(record[f"ref_odds_{outcome}"]), float(final[f"ref_odds_{outcome}"])
            q_entry, q_close = float(record[f"diagnostic_ref_p_{outcome}"]), float(final[f"diagnostic_ref_p_{outcome}"])
            rows.append({"scope": scope, "match_id": record.match_id, "match_date": record.match_date,
                         "season": record.season, "result": record.result, "outcome": outcome,
                         "bookmaker": "Bet365", "entry_reference_odds": entry_odds,
                         "closing_reference_odds": closing_odds,
                         "entry_to_closing_decimal_ratio": entry_odds / closing_odds,
                         "entry_reference_probability": q_entry, "closing_reference_probability": q_close,
                         "closing_minus_entry_probability": q_close - q_entry,
                         "entry_reference_timestamp_utc": record.reference_quote_timestamp_utc,
                         "closing_reference_timestamp_utc": final.reference_quote_timestamp_utc,
                         "verified_closing_line_value": False, "used_to_select_or_size_bets": False})
    frame = pd.DataFrame(rows)
    if frame.empty:
        raise ValueError("Closing diagnostics require a nonempty opportunity panel")
    entry_missing = pd.to_datetime(native.reference_quote_timestamp_utc, utc=True, errors="coerce", format="mixed").isna()
    closing_missing = pd.to_datetime(close.reference_quote_timestamp_utc, utc=True, errors="coerce", format="mixed").isna()
    summary = {"scope": scope, "match_count": int(len(native)), "outcome_quote_count": int(len(frame)),
               "bookmaker": "Bet365", "entry_timestamp_missing_count": int(entry_missing.sum()),
               "closing_timestamp_missing_count": int(closing_missing.sum()),
               "mean_entry_to_closing_decimal_ratio": float(frame.entry_to_closing_decimal_ratio.mean()),
               "median_entry_to_closing_decimal_ratio": float(frame.entry_to_closing_decimal_ratio.median()),
               "verified_closing_line_value": False, "used_to_select_or_size_bets": False,
               "interpretation": "Same-book archived closing-price benchmark; individual quote clocks and executable price availability are unverified"}
    return summary, frame
