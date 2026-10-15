"""Descriptive diagnostics on fixed, already inspected strategy cashflows.

No fitting, threshold selection, stake resizing, disk writes or prospective
claims occur here. Selected-bet binary scores concern the selected outcome,
not the original three-class match distribution. Date/season exclusions are
accounting influence diagnostics; they are not new strategies or validation
folds. Pooled rows retain separate underlying bankroll episodes.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from epl_strategy.metrics import enrich_bets


ID_COLUMNS = ["study", "scope", "strategy_id", "episode_id", "branch", "family", "model_type",
              "feature_group", "split", "outer_season", "policy", "odds_mode", "staking"]
GROUP_KEYS = ["study", "scope", "strategy_id"]
PROBABILITY_EDGES = np.array([0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
ODDS_EDGES = np.array([1.0, 2.0, 3.0, 5.0, 10.0, np.inf])
EDGE_EDGES = np.array([-np.inf, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, np.inf])
LOG_LOSS_CLIP = 1e-15
ANALYSIS_STATUS = "exploratory_post_inspection_fixed_cashflow_diagnostic"

BIN_COLUMNS = ID_COLUMNS + ["analysis_status", "diagnostic_status", "bin_type", "bin_index", "bin_label",
    "bin_lower", "bin_upper", "upper_inclusive", "bet_count", "wins", "hit_ratio", "mean_probability",
    "mean_odds", "mean_recorded_edge", "turnover", "profit", "expected_gain_total_units",
    "expected_loss_total_units", "expected_net_profit_total_units", "expected_roi", "roi",
    "matched_valid_odds_count", "trading_frequency", "turnover_share", "expected_minus_realized_profit_units",
    "stake_odds_probability_error_units"]
DATE_COLUMNS = ID_COLUMNS + ["analysis_status", "removed_episode_id", "removed_match_date",
    "removed_bet_count", "removed_matched_matches", "removed_turnover_units", "removed_profit_units",
    "remaining_bet_count", "remaining_turnover_units", "remaining_profit_units", "roi_excluding_date",
    "diagnostic_basis"]
SEASON_COLUMNS = ID_COLUMNS + ["analysis_status", "diagnostic_episode_id", "season_bet_count",
    "season_matched_matches", "season_wins", "season_profit_units", "season_turnover_units", "season_roi",
    "season_hit_ratio", "season_expected_net_profit_units", "season_expected_roi", "remaining_bet_count",
    "remaining_turnover_units", "remaining_profit_units", "roi_excluding_season",
    "break_even_fee_rate_excluding_season", "diagnostic_basis"]


def _require(frame, names, label):
    missing = sorted(set(names) - set(frame.columns))
    if missing:
        raise ValueError(f"{label} is missing columns: {missing}")


def _ratio(numerator, denominator):
    return float(numerator / denominator) if denominator > 0 else None


def _close(actual, expected, name):
    if not np.allclose(np.asarray(actual, dtype=float), np.asarray(expected, dtype=float),
                       rtol=1e-9, atol=1e-7):
        raise ValueError(f"Diagnostic {name} does not reconcile")


def _labels(row):
    return {name: row[name] for name in ID_COLUMNS} | {"analysis_status": ANALYSIS_STATUS}


def _groups(frame):
    return {key: part.copy() for key, part in frame.groupby(GROUP_KEYS, sort=False, dropna=False)}


def _one(groups, empty, row):
    part = groups.get(tuple(row[name] for name in GROUP_KEYS), empty)
    if row["scope"] != "pooled_seasons":
        part = part.loc[part.episode_id.eq(row["episode_id"])]
    return part.copy()


def _cash(part):
    n = len(part)
    turnover, profit = float(part.stake.sum()), float(part.profit.sum())
    gain = float((part.probability * part.stake * (part.odds - 1)).sum())
    loss = float(((1 - part.probability) * part.stake).sum())
    net = gain - loss
    probability_error = float((part.stake * part.odds * (part.probability - part.won.astype(float))).sum())
    _close(net - profit, probability_error, "expected-minus-realized cash gap")
    return {"bet_count": n, "wins": int(part.won.sum()), "hit_ratio": _ratio(part.won.sum(), n),
            "mean_probability": float(part.probability.mean()) if n else None,
            "mean_odds": float(part.odds.mean()) if n else None,
            "mean_recorded_edge": float(part.edge.mean()) if n else None,
            "turnover": turnover, "profit": profit, "expected_gain_total_units": gain,
            "expected_loss_total_units": loss, "expected_net_profit_total_units": net,
            "expected_roi": _ratio(net, turnover), "roi": _ratio(profit, turnover),
            "expected_minus_realized_profit_units": net - profit,
            "stake_odds_probability_error_units": probability_error}


def _bound(value):
    return "-inf" if value == -np.inf else "inf" if value == np.inf else f"{value:g}"


def _bins(part, row, *, field, kind, edges):
    """Left-closed bins, with p=1 retained in the final probability bin."""
    if len(part):
        indices = np.searchsorted(edges, part[field].to_numpy(float), side="right") - 1
        if kind == "probability":
            indices = np.minimum(indices, len(edges) - 2)
        if (indices < 0).any() or (indices >= len(edges) - 1).any():
            raise ValueError(f"A selected {kind} value is outside the declared bins")
    else:
        indices = np.array([], dtype=int)
    records = []
    total_turnover = float(part.stake.sum())
    for index, (lower, upper) in enumerate(zip(edges[:-1], edges[1:])):
        selected = part.loc[indices == index]
        cash = _cash(selected)
        inclusive = kind == "probability" and index == len(edges) - 2
        records.append({**_labels(row), "diagnostic_status": "selected_bets" if len(selected) else "empty_bin",
                        "bin_type": kind, "bin_index": index,
                        "bin_label": f"[{_bound(lower)}, {_bound(upper)}{']' if inclusive else ')'}",
                        "bin_lower": float(lower), "bin_upper": float(upper), "upper_inclusive": inclusive,
                        **cash, "matched_valid_odds_count": int(row["matched_valid_odds_count"]),
                        "trading_frequency": _ratio(len(selected), row["matched_valid_odds_count"]),
                        "turnover_share": _ratio(cash["turnover"], total_turnover)})
    if sum(record["bet_count"] for record in records) != len(part):
        raise ValueError("Selected-bet bin counts do not preserve the original population")
    return records


def _selected_scores(part, row, probability_bins):
    n = len(part)
    cash = _cash(part)
    if n:
        probability, outcome = part.probability.to_numpy(float), part.won.to_numpy(float)
        clipped = np.clip(probability, LOG_LOSS_CLIP, 1 - LOG_LOSS_CLIP)
        loss = float(-np.mean(outcome * np.log(clipped) + (1 - outcome) * np.log1p(-clipped)))
        brier = float(np.mean((probability - outcome) ** 2))
        ece = float(sum(item["bet_count"] / n * abs(item["mean_probability"] - item["hit_ratio"])
                        for item in probability_bins if item["bet_count"]))
        probability_gap = float(probability.mean() - outcome.mean())
    else:
        loss = brier = ece = probability_gap = None
    return {**_labels(row), "diagnostic_status": "selected_bets" if n else "no_recorded_bets", **cash,
            "expected_wins_sum": float(part.probability.sum()), "observed_wins": int(part.won.sum()),
            "mean_probability_minus_hit_ratio": probability_gap,
            "selected_binary_log_loss": loss, "selected_binary_brier_score": brier,
            "selected_binary_ece_10": ece, "log_loss_probability_clip": LOG_LOSS_CLIP,
            "proper_score_population": "selected_recorded_outcomes_only_not_all_three_class_matches",
            "matched_valid_odds_count": int(row["matched_valid_odds_count"]),
            "trading_frequency": _ratio(n, row["matched_valid_odds_count"])}


def _extremes(values):
    valid = [float(value) for value in values if value is not None and np.isfinite(value)]
    return (min(valid), max(valid), len(valid)) if valid else (None, None, 0)


def _concentration(part, curve, row):
    n, turnover, profit = len(part), float(part.stake.sum()), float(part.profit.sum())
    positive_bets = part.loc[part.profit.gt(0), "profit"].sort_values(ascending=False)
    positive_dates = curve.loc[curve.profit.gt(0), "profit"].sort_values(ascending=False)
    positive_bet_total, positive_date_total = float(positive_bets.sum()), float(positive_dates.sum())
    influence = []
    for date in curve.itertuples(index=False):
        remaining_turnover, remaining_profit = turnover - float(date.turnover), profit - float(date.profit)
        # Tiny floating remainders can arise when subtracting one complete day.
        if abs(remaining_turnover) < 1e-8:
            remaining_turnover = 0.0
        influence.append({**_labels(row), "removed_episode_id": date.episode_id,
                          "removed_match_date": date.match_date, "removed_bet_count": int(date.bet_count),
                          "removed_matched_matches": int(date.matched_matches),
                          "removed_turnover_units": float(date.turnover), "removed_profit_units": float(date.profit),
                          "remaining_bet_count": n - int(date.bet_count),
                          "remaining_turnover_units": remaining_turnover, "remaining_profit_units": remaining_profit,
                          "roi_excluding_date": _ratio(remaining_profit, remaining_turnover),
                          "diagnostic_basis": "leave_one_episode_calendar_date_out_fixed_cashflow_accounting_no_refit"})
    low, high, valid = _extremes(item["roi_excluding_date"] for item in influence)
    winning_gains = float(part.loc[part.won, "winning_net_payoff_units"].sum())
    status = ("no_recorded_bets" if not n else "already_negative_before_additional_costs" if profit < 0
              else "positive_historical_margin" if profit > 0 else "zero_historical_margin")
    concentration = {**_labels(row), "diagnostic_status": "selected_bets" if n else "no_recorded_bets",
        "bet_count": n, "turnover": turnover, "profit": profit, "roi": _ratio(profit, turnover),
        "positive_bet_count": len(positive_bets), "positive_bet_profit_total_units": positive_bet_total,
        "positive_date_count": len(positive_dates), "positive_date_profit_total_units": positive_date_total,
        "top1_positive_bet_profit_share": _ratio(positive_bets.head(1).sum(), positive_bet_total),
        "top5_positive_bet_profit_share": _ratio(positive_bets.head(5).sum(), positive_bet_total),
        "top1_positive_date_profit_share": _ratio(positive_dates.head(1).sum(), positive_date_total),
        "top5_positive_date_profit_share": _ratio(positive_dates.head(5).sum(), positive_date_total),
        "top1_positive_date_profit_units": float(positive_dates.head(1).sum()),
        "top5_positive_date_profit_units": float(positive_dates.head(5).sum()),
        "leave_one_date_out_roi_min": low, "leave_one_date_out_roi_max": high,
        "leave_one_date_out_valid_count": valid, "leave_one_date_out_total_dates": len(curve),
        "leave_one_date_out_undefined_count": len(curve) - valid,
        "break_even_fee_rate_signed": _ratio(profit, turnover),
        "break_even_payout_haircut_signed": _ratio(profit, winning_gains), "break_even_status": status,
        "concentration_basis": "positive_date_net_pnl_after_same_date_losses; bet_profit_shares_also_separate",
        "season_diagnostic_status": "not_a_pooled_season_scope",
        "season_count": None, "profitable_season_count": None, "season_roi_min": None, "season_roi_max": None,
        "leave_one_season_out_roi_min": None, "leave_one_season_out_roi_max": None,
        "leave_one_season_out_valid_count": None, "leave_one_season_out_undefined_count": None}
    return concentration, influence


def _season_rows(part, curve, row, concentration):
    if row["scope"] != "pooled_seasons":
        return []
    total_n, turnover, profit = len(part), float(part.stake.sum()), float(part.profit.sum())
    records = []
    for episode, season in curve.groupby("episode_id", sort=True):
        bets = part.loc[part.episode_id.eq(episode)]
        cash = _cash(bets)
        remaining_turnover, remaining_profit = turnover - cash["turnover"], profit - cash["profit"]
        if abs(remaining_turnover) < 1e-8:
            remaining_turnover = 0.0
        records.append({**_labels(row), "diagnostic_episode_id": episode,
            "season_bet_count": len(bets), "season_matched_matches": int(season.matched_matches.sum()),
            "season_wins": cash["wins"], "season_profit_units": cash["profit"],
            "season_turnover_units": cash["turnover"], "season_roi": cash["roi"],
            "season_hit_ratio": cash["hit_ratio"], "season_expected_net_profit_units": cash["expected_net_profit_total_units"],
            "season_expected_roi": cash["expected_roi"], "remaining_bet_count": total_n - len(bets),
            "remaining_turnover_units": remaining_turnover, "remaining_profit_units": remaining_profit,
            "roi_excluding_season": _ratio(remaining_profit, remaining_turnover),
            "break_even_fee_rate_excluding_season": _ratio(remaining_profit, remaining_turnover),
            "diagnostic_basis": "leave_one_evaluation_season_out_accounting_only_models_not_refitted; not_cross_validation"})
    low, high, valid = _extremes(item["roi_excluding_season"] for item in records)
    season_low, season_high, _ = _extremes(item["season_roi"] for item in records)
    concentration.update(season_diagnostic_status="pooled_separately_funded_evaluation_seasons",
                         season_count=len(records), profitable_season_count=sum(item["season_profit_units"] > 0 for item in records),
                         season_roi_min=season_low, season_roi_max=season_high,
                         leave_one_season_out_roi_min=low, leave_one_season_out_roi_max=high,
                         leave_one_season_out_valid_count=valid, leave_one_season_out_undefined_count=len(records) - valid)
    return records


def build_diagnostics(metrics: pd.DataFrame, bets: pd.DataFrame, equity: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Return descriptive tables for all non-tuning strategies, including cash.

    The caller writes immutable exports and verifies file provenance. Each
    pooled summary has episode_id ``season_stratified_pool``; pooled bet/equity
    records keep their original season episode IDs. Numeric bin totals zero
    denote an empty observed bin; its conditional means and ROI stay missing.
    """
    _require(metrics, ID_COLUMNS + ["bet_count", "turnover", "profit", "matched_valid_odds_count"], "Strategy metrics")
    _require(bets, ID_COLUMNS, "Selected-bet ledger")
    _require(equity, ID_COLUMNS + ["match_date", "matched_matches", "bet_count", "turnover", "profit"], "Date equity")
    if metrics[GROUP_KEYS + ["episode_id"]].isna().any().any() or metrics.duplicated(GROUP_KEYS + ["episode_id"]).any():
        raise ValueError("Strategy diagnostic identities must be complete and unique")
    if ("is_tuning_diagnostic" in metrics and metrics.is_tuning_diagnostic.fillna(False).astype(bool).any()) or metrics.study.eq("first_tuning").any():
        raise ValueError("Threshold-tuning diagnostics are excluded from this analysis")
    positions = enrich_bets(bets)
    positions["edge"] = positions.probability * positions.odds - 1
    if "edge" in bets:
        _close(bets.edge.to_numpy(float), positions.edge.to_numpy(float), "recorded probability/price edge")
    curve = equity.copy()
    curve["match_date"] = pd.to_datetime(curve.match_date, errors="raise").dt.normalize()
    if positions.duplicated(GROUP_KEYS + ["episode_id", "match_id"]).any() or curve.duplicated(GROUP_KEYS + ["episode_id", "match_date"]).any():
        raise ValueError("Duplicate selected-match or episode-date diagnostic identity")
    bet_groups, date_groups = _groups(positions), _groups(curve)
    probability_rows, odds_rows, edge_rows, score_rows = [], [], [], []
    availability, concentration_rows, date_rows, season_rows = [], [], [], []
    for row in metrics.to_dict("records"):
        part, dates = _one(bet_groups, positions.iloc[:0], row), _one(date_groups, curve.iloc[:0], row)
        _close(len(part), row["bet_count"], "saved selected-bet count")
        _close(part.stake.sum(), row["turnover"], "saved stake total")
        _close(part.profit.sum(), row["profit"], "saved profit total")
        _close(dates.bet_count.sum(), len(part), "date bet count")
        _close(dates.turnover.sum(), part.stake.sum(), "date stake total")
        _close(dates.profit.sum(), part.profit.sum(), "date profit total")
        _close(dates.matched_matches.sum(), row["matched_valid_odds_count"], "date opportunity denominator")
        available = bool(len(part))
        availability.append({**_labels(row), "diagnostic_status": "selected_bets" if available else "no_recorded_bets",
                             "selected_bet_scores_available": available, "bet_count": len(part),
                             "matched_valid_odds_count": int(row["matched_valid_odds_count"]),
                             "matched_episode_dates": len(dates), "trading_frequency": _ratio(len(part), row["matched_valid_odds_count"]),
                             "fresh_confirmatory_holdout": False})
        prob = _bins(part, row, field="probability", kind="probability", edges=PROBABILITY_EDGES)
        probability_rows.extend(prob)
        odds_rows.extend(_bins(part, row, field="odds", kind="odds", edges=ODDS_EDGES))
        edge_rows.extend(_bins(part, row, field="edge", kind="edge", edges=EDGE_EDGES))
        score_rows.append(_selected_scores(part, row, prob))
        concentration, influence = _concentration(part, dates, row)
        season_rows.extend(_season_rows(part, dates, row, concentration))
        concentration_rows.append(concentration)
        date_rows.extend(influence)
    return {"diagnostic_availability": pd.DataFrame(availability),
            "probability_bins": pd.DataFrame(probability_rows, columns=BIN_COLUMNS),
            "odds_bins": pd.DataFrame(odds_rows, columns=BIN_COLUMNS),
            "edge_bins": pd.DataFrame(edge_rows, columns=BIN_COLUMNS),
            "selected_bet_scores": pd.DataFrame(score_rows),
            "date_concentration": pd.DataFrame(concentration_rows),
            "date_influence": pd.DataFrame(date_rows, columns=DATE_COLUMNS),
            "season_fragility": pd.DataFrame(season_rows, columns=SEASON_COLUMNS)}
