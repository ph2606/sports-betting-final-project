"""Independent arithmetic audit of exported quote-sensitivity accounts.

This module never calls the new replay or diagnostic calculations. It checks
recorded cashflows, opening-date funding and exact payoff identities directly.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


MODES = ("original", "reference_replay", "fixed_exposure_reference")
SCOPE_COUNTS = {"single": 84, "continuous": 56, "seasonal": 224}
SEASON_COUNTS = {"2022-23": 368, "2023-24": 360, "2024-25": 368, "2025-26": 374}
SEASON_DATES = {"2022-23": 117, "2023-24": 116, "2024-25": 107, "2025-26": 113}
UNFUNDED_WITHHELD = (
    "final_capital_sum_units", "return_on_initial_capital", "max_drawdown",
    "min_episode_log_growth", "mean_episode_log_growth", "date_return_mean",
    "date_return_sample_std", "date_return_mean_to_std_unannualized",
    "max_date_capital_exposure", "mean_date_capital_exposure",
)


def _require(frame, columns, label):
    missing = sorted(set(columns) - set(frame))
    if missing:
        raise AssertionError(f"{label} missing columns: {missing}")


def _near(left, right, label, *, atol=1e-6):
    if not np.allclose(np.asarray(left, dtype=float), np.asarray(right, dtype=float),
                       atol=atol, rtol=1e-10, equal_nan=True):
        raise AssertionError(label + " does not reconcile")


def _ratio(numerator, denominator):
    return numerator / denominator if denominator else np.nan


def _metric(metric, key, expected):
    if key not in metric:
        raise AssertionError("Metric missing: " + key)
    value = np.nan if metric[key] is None else metric[key]
    _near(value, expected, "Metric " + key)


def _dates(values):
    dates = pd.to_datetime(values.astype("string").str[:10], format="%Y-%m-%d", errors="raise")
    if dates.isna().any():
        raise AssertionError("Missing native match date")
    return dates


def _audit_account(metric, bets, equity, *, opportunities=None):
    """Independently audit one account, including unfunded shadow cashflows."""
    bets, equity = bets.copy(), equity.copy()
    _require(bets, ["match_id", "match_date", "selection", "result", "probability", "odds", "stake", "won", "profit", "gross_return"], "Bets")
    _require(equity, ["match_date", "matched_matches", "bet_count", "turnover", "profit", "start_bankroll", "end_bankroll"], "Equity")
    bets["match_date"], equity["match_date"] = _dates(bets.match_date), _dates(equity.match_date)
    if bets.match_id.isna().any() or bets.match_id.duplicated().any() or equity.match_date.duplicated().any() or equity.empty:
        raise AssertionError("Duplicate/missing bet identity or equity date")
    equity = equity.sort_values("match_date").reset_index(drop=True)
    numeric = bets[["probability", "odds", "stake", "won", "profit", "gross_return"]].to_numpy(float)
    if not np.isfinite(numeric).all() or not bets.probability.between(0, 1).all() or not bets.odds.gt(1).all() or not bets.stake.gt(0).all():
        raise AssertionError("Invalid bet probability, price, stake or cashflow")
    if not bets.selection.isin(list("HDA")).all() or not bets.result.isin(list("HDA")).all() or not bets.won.isin([0, 1]).all():
        raise AssertionError("Invalid recorded settlement")
    y = bets.selection.eq(bets.result).to_numpy(dtype=float)
    _near(bets.won, y, "Win indicators", atol=0)
    s, p, o = [bets[c].to_numpy(float) for c in ("stake", "probability", "odds")]
    gross, profit = s * o * y, s * (o * y - 1)
    _near(bets.gross_return, gross, "Gross cash settlement")
    _near(bets.profit, profit, "Net cash settlement")
    if not bets.match_date.isin(equity.match_date).all():
        raise AssertionError("Bet date is absent from the account curve")
    cash = pd.DataFrame({"match_date": bets.match_date, "stake": s, "profit": profit}).groupby("match_date").agg(
        turnover=("stake", "sum"), profit=("profit", "sum"), bet_count=("stake", "size"))
    daily = cash.reindex(equity.match_date, fill_value=0)
    for column in ("turnover", "profit", "bet_count"):
        _near(equity[column], daily[column], "Date " + column)
    if opportunities is not None:
        native = opportunities.copy()
        native["match_date"] = _dates(native.match_date)
        if native.match_id.isna().any() or native.match_id.duplicated().any():
            raise AssertionError("Duplicate native opportunity identity")
        by_id = native.set_index("match_id")
        if not bets.match_id.isin(by_id.index).all():
            raise AssertionError("Bet identity absent from native opportunity panel")
        for column in ("match_date", "result"):
            if not bets[column].eq(bets.match_id.map(by_id[column])).all():
                raise AssertionError("Native bet " + column + " conflict")
        if "season" in bets and not bets.season.eq(bets.match_id.map(by_id.season)).all():
            raise AssertionError("A bet's real season was overwritten")
        counts = native.groupby("match_date").size().sort_index()
        if not pd.DatetimeIndex(counts.index).equals(pd.DatetimeIndex(equity.match_date)):
            raise AssertionError("Equity omits a priced date")
        _near(equity.matched_matches, counts, "Date priced match counts", atol=0)
    n, wins = len(bets), int(y.sum())
    turnover, total = float(s.sum()), float(profit.sum())
    matched = int(equity.matched_matches.sum())
    expected_gain = float(np.sum(s * p * (o - 1)))
    expected_loss = float(np.sum(s * (1 - p)))
    expected = {
        "bet_count": n, "winning_bet_count": wins, "losing_bet_count": n - wins,
        "hit_ratio": _ratio(wins, n), "profit": total, "turnover": turnover,
        "gross_return": float(gross.sum()), "roi": _ratio(total, turnover),
        "matched_valid_odds_count": matched, "prediction_count": matched,
        "trading_frequency": _ratio(n, matched), "trade_rate_all_predictions": _ratio(n, matched),
        "expected_gain_total_units": expected_gain, "expected_loss_total_units": expected_loss,
        "expected_net_profit_total_units": expected_gain - expected_loss,
        "expected_roi": _ratio(expected_gain - expected_loss, turnover),
        "expected_gain_per_trade_units": _ratio(expected_gain, n),
        "expected_loss_per_trade_units": _ratio(expected_loss, n),
        "realized_expectancy_per_trade_units": _ratio(total, n),
        "avg_winning_gain_units": float(profit[y == 1].mean()) if wins else np.nan,
        "avg_losing_loss_units": float(-profit[y == 0].mean()) if n - wins else np.nan,
    }
    for key, value in expected.items():
        _metric(metric, key, value)
    initial = float(metric.get("initial_capital_sum_units", metric.get("initial_bankroll", 100000)))
    _near(initial, 100000, "Initial account capital", atol=1e-8)
    ends = initial + np.cumsum(daily.profit.to_numpy(float))
    starts = np.r_[initial, ends[:-1]]
    _near(equity.start_bankroll, starts, "Date opening balance")
    _near(equity.end_bankroll, ends, "Date closing balance")
    gap = np.maximum(daily.turnover.to_numpy(float) - starts, 0)
    feasible = bool((gap <= 1e-7).all())
    mode = metric["execution_mode"]
    if bool(metric["funding_feasible"]) != feasible:
        raise AssertionError("Account funding flag disagrees with date-opening commitments")
    if mode != "fixed_exposure_reference" and not feasible:
        raise AssertionError("A policy replay cannot require external opening cash")
    wealth = np.r_[initial, ends]
    peaks = np.maximum.accumulate(wealth)
    dd = 1 - wealth / peaks
    if mode == "fixed_exposure_reference":
        _require(equity, ["shadow_start_balance", "shadow_end_balance", "funding_shortfall_units", "date_funding_feasible"], "Shadow curve")
        _near(equity.shadow_start_balance, starts, "Shadow opening balance")
        _near(equity.shadow_end_balance, ends, "Shadow closing balance")
        _near(equity.funding_shortfall_units, gap, "Date opening-cash gap")
        if not np.array_equal(equity.date_funding_feasible.to_numpy(bool), gap <= 1e-7):
            raise AssertionError("Shadow date funding status is inconsistent")
        for key, value in {"max_funding_shortfall_units": float(gap.max()),
                           "minimum_additional_opening_cash_units": float(gap.max()),
                           "funding_breach_dates": int((gap > 1e-7).sum()),
                           "shadow_final_balance": float(ends[-1]),
                           "shadow_min_balance": float(wealth.min()),
                           "shadow_max_drawdown": float(dd.max())}.items():
            _metric(metric, key, value)
    if feasible:
        if (wealth < -1e-6).any():
            raise AssertionError("Funded account has negative cash")
        _metric(metric, "final_capital_sum_units", float(ends[-1]))
        _metric(metric, "return_on_initial_capital", total / initial)
        _metric(metric, "max_drawdown", float(dd.max()))
        if "drawdown" in equity:
            _near(equity.drawdown, dd[1:], "Funded account drawdown")
    else:
        for key in UNFUNDED_WITHHELD:
            if key not in metric or pd.notna(metric[key]):
                raise AssertionError("Unfunded shadow account must withhold " + key)
        for key in metric:
            if "_ci_" in key and pd.notna(metric[key]):
                raise AssertionError("Unfunded shadow account must withhold confidence intervals")
        for key in ("daily_return", "running_peak", "drawdown", "log_growth"):
            if key in equity and equity[key].notna().any():
                raise AssertionError("Unfunded shadow curve exposes ordinary risk statistics")
    return {"bet_count": n, "funding_feasible": feasible, "profit": total}


def _audit_attribution(frame):
    _require(frame, ["account_id", "actual_profit", "model_expected_profit", "market_implied_expected_profit",
                     "model_probability_premium", "outcome_residual", "payoff_forecast_error",
                     "archived_ref_fixed_bet_profit", "realized_price_uplift_vs_reference"], "Attribution")
    if frame.account_id.duplicated().any():
        raise AssertionError("Duplicate attribution account")
    _near(frame.actual_profit, frame.market_implied_expected_profit + frame.outcome_residual, "Realized market attribution")
    _near(frame.model_expected_profit, frame.market_implied_expected_profit + frame.model_probability_premium, "Model market attribution")
    _near(frame.payoff_forecast_error, frame.actual_profit - frame.model_expected_profit, "Payoff forecast error")
    _near(frame.actual_profit, frame.archived_ref_fixed_bet_profit + frame.realized_price_uplift_vs_reference, "Price contribution")


def _audit_graph(graph, reference, compatible_ids, *, dates_per_account=454):
    graph = graph.copy()
    _require(graph, ["strategy_id", "match_date", "end_bankroll", "is_initial"], "Reference graph")
    graph["match_date"] = _dates(graph.match_date)
    if not pd.api.types.is_bool_dtype(graph.is_initial):
        values = graph.is_initial.astype(str).str.lower()
        if not values.isin(["true", "false"]).all():
            raise AssertionError("Invalid graph anchor flags")
        graph["is_initial"] = values.eq("true")
    if set(graph.strategy_id) != set(compatible_ids) or len(graph) != len(compatible_ids) * dates_per_account:
        raise AssertionError("Reference graph omits strategy curves or settlement dates")
    if graph.duplicated(["strategy_id", "match_date"]).any() or not np.isfinite(graph.end_bankroll).all() or graph.end_bankroll.lt(-1e-6).any():
        raise AssertionError("Invalid or duplicate reference graph cash balance")
    reference = reference.set_index("strategy_id")
    common_dates = None
    for sid, curve in graph.groupby("strategy_id", sort=True):
        curve = curve.sort_values("match_date")
        if len(curve) != dates_per_account or curve.is_initial.sum() != 1 or not curve.is_initial.iloc[0]:
            raise AssertionError("Reference graph must have one leading initial point")
        _near(curve.end_bankroll.iloc[0], 100000, "Graph initial capital", atol=1e-8)
        if curve.match_date.iloc[0] != pd.Timestamp("2022-08-04"):
            raise AssertionError("Reference graph initial date changed")
        if common_dates is None:
            common_dates = curve.match_date.to_numpy()
        elif not np.array_equal(common_dates, curve.match_date.to_numpy()):
            raise AssertionError("Reference curves do not share all calendar dates")
        _near(curve.end_bankroll.iloc[-1], 100000 + reference.loc[sid, "profit"], "Graph endpoint")


def _read_original(root, scope):
    if scope == "single":
        base = root / "epl_strategy_lab/results/20261015T040052Z_100k84"
        return pd.read_parquet(base / "bets.parquet"), pd.read_parquet(base / "equity.parquet")
    base = root / "epl_strategy_validation/results/20261015_temporal_selection"
    return pd.read_parquet(base / f"bets_{scope}.parquet"), pd.read_parquet(base / f"equity_{scope}.parquet")


def _part(frame, metric, *, original=False):
    if not original:
        return frame.loc[frame.account_id.eq(metric["account_id"])].copy()
    keep = frame.strategy_id.eq(metric["strategy_id"])
    if metric["scope"] == "seasonal":
        keep &= frame.season.eq(metric["season"])
    return frame.loc[keep].copy()


def _audit_reference_identity(original_bets, original_equity, reference_bets, reference_equity):
    """Already-reference configurations must retain identical bets and cash."""
    old, new = [frame.sort_values("match_id").reset_index(drop=True) for frame in (original_bets, reference_bets)]
    if old.match_id.tolist() != new.match_id.tolist() or old.selection.tolist() != new.selection.tolist():
        raise AssertionError("Already-reference replay changed trade identity or outcome")
    for column in ("probability", "odds", "stake", "profit", "gross_return"):
        _near(old[column], new[column], "Already-reference bet " + column)
    old_curve, new_curve = [frame.sort_values("match_date").reset_index(drop=True) for frame in (original_equity, reference_equity)]
    if not _dates(old_curve.match_date).equals(_dates(new_curve.match_date)):
        raise AssertionError("Already-reference replay changed settlement dates")
    for column in ("start_bankroll", "end_bankroll", "turnover", "profit", "bet_count"):
        _near(old_curve[column], new_curve[column], "Already-reference curve " + column)


def _audit_fixed_identity(original_bets, fixed_bets, metric):
    old, fixed = [frame.sort_values("match_id").reset_index(drop=True) for frame in (original_bets, fixed_bets)]
    if old.match_id.tolist() != fixed.match_id.tolist() or old.selection.tolist() != fixed.selection.tolist():
        raise AssertionError("Fixed exposure changed original trade identity or outcome")
    for column in ("probability", "stake", "won"):
        _near(old[column], fixed[column], "Fixed exposure retained " + column)
    s, p, y = [old[c].to_numpy(float) for c in ("stake", "probability", "won")]
    difference = old.odds.to_numpy(float) - fixed.odds.to_numpy(float)
    actual_uplift = float(np.sum(s * y * difference))
    expected_uplift = float(np.sum(s * p * difference))
    _metric(metric, "actual_quote_uplift_units", actual_uplift)
    _metric(metric, "model_expected_quote_uplift_units", expected_uplift)
    _near(old.profit.sum(), fixed.profit.sum() + actual_uplift, "Fixed realized price decomposition")
    old_expected = float(np.sum(s * (p * old.odds.to_numpy(float) - 1)))
    new_expected = float(np.sum(s * (p * fixed.odds.to_numpy(float) - 1)))
    _near(old_expected, new_expected + expected_uplift, "Fixed model expected price decomposition")


def audit_export(output: Path, *, root: Path | None = None) -> dict:
    """Check complete exported populations and independently reconstruct cash.

    Passing the project root additionally reconciles originals to their frozen
    ledgers and verifies native fixture identities and market-price attribution.
    Without it, the exported replay/shadow ledgers and all table identities are
    still checked; no original-ledger verification is claimed.
    """
    output = Path(output)
    root = Path(root).resolve() if root is not None else None
    catalog = json.loads((output / "catalog.json").read_text(encoding="utf-8"))
    all_ids = {row["strategy_id"] for row in catalog}
    compatible = {row["strategy_id"] for row in catalog if not row["model_key"].startswith("first_")}
    if len(catalog) != 84 or len(all_ids) != 84 or len(compatible) != 56:
        raise AssertionError("Frozen 84/56 strategy catalog coverage changed")
    metric_tables = {scope: pd.read_parquet(output / f"metrics_{scope}.parquet") for scope in SCOPE_COUNTS}
    checked = 0
    unfunded = {scope: 0 for scope in SCOPE_COUNTS}
    originals, reference_ledgers, fixed_ledgers = {}, {}, {}
    native = None
    if root is not None:
        native = pd.read_parquet(root / "epl_modeling/results/bookmaker_odds_panel.parquet")
        native = native.loc[native.season.isin(SEASON_COUNTS)].copy()
        native["match_date"] = _dates(native.match_date)
        if native.groupby("season").size().to_dict() != SEASON_COUNTS:
            raise AssertionError("Native opportunity population changed")
        frozen_catalog = json.loads((root / "epl_strategy_lab/results/20261015T040052Z_100k84/catalog.json").read_text())
        if catalog != frozen_catalog:
            raise AssertionError("The saved original strategy definitions changed")
    all_accounts = []
    for scope, count in SCOPE_COUNTS.items():
        table = metric_tables[scope]
        _require(table, ["account_id", "strategy_id", "scope", "season", "execution_mode", "funding_feasible"], "Metrics " + scope)
        if len(table) != count * 3 or set(table.execution_mode) != set(MODES) or table.duplicated(["account_id", "execution_mode"]).any():
            raise AssertionError("Incomplete or duplicate account/mode metrics for " + scope)
        expected_ids = all_ids if scope == "single" else compatible
        if not table.scope.eq(scope).all():
            raise AssertionError("Metric account scope conflict")
        for mode in MODES:
            mode_rows = table.loc[table.execution_mode.eq(mode)]
            if len(mode_rows) != count or set(mode_rows.strategy_id) != expected_ids:
                raise AssertionError("Strategy omitted from " + scope + ": " + mode)
            if scope == "seasonal" and (mode_rows.groupby("season").size().to_dict() != {season: 56 for season in SEASON_COUNTS}
                                      or mode_rows.duplicated(["strategy_id", "season"]).any()):
                raise AssertionError("Seasonal strategy accounts omitted or duplicated")
        for mode in MODES[1:]:
            if set(table.loc[table.execution_mode.eq(mode), "account_id"]) != set(table.loc[table.execution_mode.eq("original"), "account_id"]):
                raise AssertionError("Execution views use different account identities")
        originals[scope] = _read_original(root, scope) if root is not None else None
        reference_ledgers[scope] = tuple(pd.read_parquet(output / f"{kind}_reference_{scope}.parquet") for kind in ("bets", "equity"))
        fixed_ledgers[scope] = tuple(pd.read_parquet(output / f"{kind}_fixed_reference_{scope}.parquet") for kind in ("bets", "equity"))
        for ledger in [*reference_ledgers[scope], *fixed_ledgers[scope]]:
            _require(ledger, ["account_id", "strategy_id", "execution_mode"], "Saved account ledger")
        for metric in table.to_dict("records"):
            mode = metric["execution_mode"]
            if mode == "original" and originals[scope] is None:
                continue
            pair = originals[scope] if mode == "original" else reference_ledgers[scope] if mode == "reference_replay" else fixed_ledgers[scope]
            bets, curve = [_part(frame, metric, original=mode == "original") for frame in pair]
            if mode != "original":
                if not bets.execution_mode.eq(mode).all() or not curve.execution_mode.eq(mode).all():
                    raise AssertionError("Ledger execution mode disagrees with its metrics")
                if not bets.strategy_id.eq(metric["strategy_id"]).all() or not curve.strategy_id.eq(metric["strategy_id"]).all():
                    raise AssertionError("Ledger strategy identity disagrees with its account")
            universe = None
            if native is not None:
                universe = native if scope == "continuous" else native.loc[native.season.eq(metric["season"])]
            result = _audit_account(metric, bets, curve, opportunities=universe)
            if mode == "fixed_exposure_reference" and root is not None:
                original_bets = _part(originals[scope][0], metric, original=True)
                _audit_fixed_identity(original_bets, bets, metric)
            checked += 1
            if not result["funding_feasible"]:
                unfunded[scope] += 1
        all_accounts.extend(table.loc[table.execution_mode.eq("original"), "account_id"].tolist())
    if len(set(all_accounts)) != 364:
        raise AssertionError("Account IDs overlap between independent scopes")
    metrics = pd.concat(metric_tables.values(), ignore_index=True)
    comparison = pd.read_parquet(output / "execution_comparison.parquet")
    attribution = pd.read_parquet(output / "payoff_attribution.parquet")
    for name, table in (("Comparison", comparison), ("Attribution", attribution)):
        if len(table) != 364 or table.account_id.duplicated().any() or set(table.account_id) != set(all_accounts):
            raise AssertionError(name + " must cover every original account once")
    _audit_attribution(attribution)
    indexed = metrics.set_index(["account_id", "execution_mode"])
    for row in comparison.to_dict("records"):
        for prefix, mode in (("original", "original"), ("reference", "reference_replay"), ("fixed", "fixed_exposure_reference")):
            metric = indexed.loc[(row["account_id"], mode)]
            for key in ("profit", "roi", "bet_count", "turnover", "hit_ratio", "trading_frequency"):
                name = prefix + "_" + key
                if name in row:
                    _near(row[name], metric[key], "Comparison " + name)
        _near(row["original_profit"], row["fixed_profit"] + row["realized_quote_uplift_units"], "Comparison fixed price attribution")
        _near(row["original_expected_net_profit_total_units"],
              row["fixed_expected_net_profit_total_units"] + row["model_expected_quote_uplift_units"],
              "Comparison fixed model expected attribution")
    original_metrics = metrics.loc[metrics.execution_mode.eq("original")].set_index("account_id")
    fixed_metrics = metrics.loc[metrics.execution_mode.eq("fixed_exposure_reference")].set_index("account_id")
    for row in attribution.to_dict("records"):
        original = original_metrics.loc[row["account_id"]]
        fixed = fixed_metrics.loc[row["account_id"]]
        _near(row["actual_profit"], original.profit, "Attribution original account profit")
        _near(row["model_expected_profit"], original.expected_net_profit_total_units, "Attribution model expected profit")
        _near(row["archived_ref_fixed_bet_profit"], fixed.profit, "Attribution fixed-reference profit")
        if root is not None:
            bets = _part(originals[row["scope"]][0], original.to_dict(), original=True)
            selected = native.set_index("match_id").reindex(bets.match_id)
            ix = np.array(["HDA".index(o) for o in bets.selection], dtype=int)
            reference = selected[["ref_odds_H", "ref_odds_D", "ref_odds_A"]].to_numpy(float)
            inv = 1 / reference
            q = (inv / inv.sum(axis=1, keepdims=True))[np.arange(len(bets)), ix]
            s, o, p = [bets[c].to_numpy(float) for c in ("stake", "odds", "probability")]
            _near(row["market_implied_expected_profit"], np.sum(s * (q * o - 1)), "Independent market-implied attribution")
            _near(row["model_probability_premium"], np.sum(s * o * (p - q)), "Independent probability premium")
    identity_ids = {config["strategy_id"] for config in catalog if config["odds_mode"] == "reference"}
    if len(identity_ids) != 8:
        raise AssertionError("The eight original reference-price controls changed")
    single = metric_tables["single"]
    for sid in identity_ids:
        part = single.loc[single.strategy_id.eq(sid)].set_index("execution_mode")
        for key in ("profit", "turnover", "bet_count", "hit_ratio", "trading_frequency"):
            _near(part.loc["original", key], part.loc["reference_replay", key], "Already-reference strategy " + sid)
        if root is not None:
            metric = part.loc["reference_replay"].to_dict()
            metric["scope"], metric["strategy_id"] = "single", sid
            old_bets, old_curve = [_part(frame, metric, original=True) for frame in originals["single"]]
            new_bets, new_curve = [_part(frame, metric) for frame in reference_ledgers["single"]]
            _audit_reference_identity(old_bets, old_curve, new_bets, new_curve)
    books = pd.read_parquet(output / "book_concentration.parquet")
    if books.duplicated(["account_id", "bookmaker"]).any() or not set(books.account_id).issubset(all_accounts):
        raise AssertionError("Duplicate or unknown account/book exposure")
    active_ids = set(original_metrics.loc[original_metrics.bet_count.gt(0)].index)
    if set(books.account_id) != active_ids:
        raise AssertionError("Book concentration omits an active original account")
    for aid, table in books.groupby("account_id", sort=False):
        metric = original_metrics.loc[aid]
        _near(table.bet_count.sum(), metric.bet_count, "Book concentration bet count")
        _near(table.stake.sum(), metric.turnover, "Book concentration stake")
        _near(table.total_profit.sum(), metric.profit, "Book concentration profit")
        shares = table.stake.to_numpy(float) / metric.turnover
        _near(table.stake_share, shares, "Book stake shares")
        _near(table.concentration_hhi_by_stake, np.full(len(table), np.square(shares).sum()), "Book stake HHI")
        _near(table.largest_book_stake_share, np.full(len(table), shares.max()), "Largest book stake share")
    quotes = pd.read_parquet(output / "quote_outcomes.parquet")
    closing = pd.read_parquet(output / "closing_quote_outcomes.parquet")
    closing_native = pd.read_parquet(output / "archived_closing_reference.parquet")
    if len(quotes) != 4410 or quotes.duplicated(["match_id", "outcome"]).any() or quotes.match_id.nunique() != 1470:
        raise AssertionError("Quote audit must cover all 4,410 native outcome cells")
    if (quotes.best_odds < quotes.reference_odds - 1e-12).any():
        raise AssertionError("A recorded best quote is below its reference")
    _near(quotes.price_ratio_best_to_reference, quotes.best_odds / quotes.reference_odds, "Quote price ratio")
    if quotes.executable_quotes_verified.any():
        raise AssertionError("Unverified historical quotes were labelled executable")
    quote_summary = json.loads((output / "quote_summary.json").read_text())
    for key in ("reference_timestamp_missing_count", "best_H_timestamp_missing_count", "best_D_timestamp_missing_count", "best_A_timestamp_missing_count"):
        if quote_summary[key] != 1470:
            raise AssertionError("Frozen quote-clock missingness changed")
    if len(closing) != 4410 or closing.duplicated(["match_id", "outcome"]).any() or len(closing_native) != 1470 or closing_native.match_id.duplicated().any():
        raise AssertionError("Closing benchmark native coverage changed")
    if set(closing.match_id) != set(quotes.match_id) or set(closing_native.match_id) != set(quotes.match_id):
        raise AssertionError("Closing and entry native match identities differ")
    if not closing.bookmaker.eq("Bet365").all() or closing.verified_closing_line_value.any() or closing.used_to_select_or_size_bets.any():
        raise AssertionError("Closing benchmark makes an execution or lookahead claim")
    _near(closing.entry_to_closing_decimal_ratio, closing.entry_reference_odds / closing.closing_reference_odds, "Closing decimal odds ratio")
    if root is not None:
        paired = closing_native.set_index("match_id").reindex(native.match_id)
        for column in ("match_date", "result", "season"):
            left, right = native[column].reset_index(drop=True), paired[column].reset_index(drop=True)
            if column == "match_date":
                left, right = _dates(left), _dates(right)
            if not left.equals(right):
                raise AssertionError("Closing native " + column + " conflict")
    graph = pd.read_csv(output / "graph_equity_reference_continuous.csv")
    ref = metric_tables["continuous"].loc[lambda frame: frame.execution_mode.eq("reference_replay")]
    _audit_graph(graph, ref, compatible)
    return {"status": "passed", "metric_rows": len(metrics), "independent_account_scopes": 364,
            "checked_cashflow_accounts": checked, "frozen_original_ledgers_checked": root is not None,
            "unfunded_fixed_exposure_accounts": unfunded, "quote_outcome_rows": len(quotes),
            "closing_outcome_rows": len(closing), "reference_graph_rows": len(graph),
            "already_reference_identity_strategies": len(identity_ids),
            "interpretation": "Independent exported-cashflow and identity checks; does not establish executable prices or predictive edge"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--root", type=Path)
    args = parser.parse_args()
    print(json.dumps(audit_export(args.output, root=args.root), indent=2))


if __name__ == "__main__":
    main()
