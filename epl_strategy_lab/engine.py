"""Date-batched, one-selection-per-fixture bankroll simulation without resets."""
from __future__ import annotations

import math
from collections.abc import Mapping

import numpy as np
import pandas as pd


OUTCOMES = np.array(["H", "D", "A"])
BET_COLUMNS = ["strategy_id", "strategy_name", "origin", "episode_id", "match_id", "match_date", "result",
               "selection", "probability", "odds", "bookmaker", "edge", "consensus_votes", "full_kelly_fraction",
               "requested_stake", "stake", "won", "gross_return", "profit", "date_start_bankroll", "date_end_bankroll",
               "start_bankroll", "end_bankroll", "commitment_scale", "staking", "odds_mode", "selection_rule",
               "threshold", "snapshot_type"]
EQUITY_COLUMNS = ["strategy_id", "strategy_name", "origin", "episode_id", "match_date", "matched_matches",
                  "qualified_matches", "bet_count", "requested_stakes", "date_budget_fraction", "date_budget_units",
                  "commitment_scale", "turnover", "profit", "start_bankroll", "end_bankroll", "bankroll_start",
                  "bankroll_end", "daily_return", "running_peak", "drawdown", "log_growth"]


def _columns(frame, columns, label):
    missing = sorted(set(columns) - set(frame))
    if missing:
        raise ValueError(f"{label} missing columns: {missing}")


def _number(config, name, default, *, lower=None, upper=None, positive=False):
    value = config.get(name, default)
    if isinstance(value, bool):
        raise ValueError(f"{name} must be numeric")
    try:
        value = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{name} must be numeric") from error
    if not math.isfinite(value) or positive and value <= 0 or lower is not None and value < lower or upper is not None and value > upper:
        raise ValueError(f"Invalid {name}")
    return value


def simulate_strategy(config, models, opportunities, *, initial_bankroll=100000.0):
    """Return recorded bets and every priced date's close, carrying one account.

    Only candidate class/price restrictions precede outcome selection. An edge
    requirement or selected-outcome consensus vote can then veto the choice.
    The full date's requests are sized and uniformly scaled before settlement;
    same-date proceeds cannot fund another wager. Results never select a bet.
    """
    if not isinstance(config, Mapping) or not isinstance(models, Mapping):
        raise TypeError("config and models must be mappings")
    initial = _number({"initial_bankroll": initial_bankroll}, "initial_bankroll", None, positive=True)
    strategy_id = config.get("strategy_id")
    if not isinstance(strategy_id, str) or not strategy_id:
        raise ValueError("A nonempty strategy_id is required")
    rule, staking, mode = config.get("selection_rule", "max_edge"), config.get("staking", "fixed"), config.get("odds_mode", "best")
    if rule not in {"max_edge", "model_favorite", "market_favorite", "market_underdog", "fixed_outcome"}:
        raise ValueError("Unknown selection_rule")
    if staking not in {"fixed", "dynamic_fraction", "kelly"} or mode not in {"best", "reference"}:
        raise ValueError("Unknown staking or odds_mode")
    allowed = config.get("allowed_outcomes", ["H", "D", "A"])
    if not isinstance(allowed, (list, tuple)) or not allowed or len(set(allowed)) != len(allowed) or not set(allowed).issubset(set(OUTCOMES)):
        raise ValueError("allowed_outcomes must contain distinct H/D/A labels")
    if rule == "fixed_outcome" and len(allowed) != 1:
        raise ValueError("fixed_outcome requires exactly one allowed outcome")
    cash = config.get("cash_only", False)
    if not isinstance(cash, (bool, np.bool_)):
        raise ValueError("cash_only must be boolean")
    edge_min = None if config.get("min_edge") is None else _number(config, "min_edge", None, lower=0)
    min_odds = None if config.get("min_odds") is None else _number(config, "min_odds", None, positive=True)
    max_odds = None if config.get("max_odds") is None else _number(config, "max_odds", None, positive=True)
    if min_odds is not None and max_odds is not None and min_odds > max_odds:
        raise ValueError("min_odds exceeds max_odds")
    fixed = _number(config, "fixed_stake", 1000, positive=True)
    fraction = _number(config, "bankroll_fraction", 0.01, lower=0, upper=1)
    kelly = _number(config, "kelly_fraction", 0.25, lower=0, upper=1)
    per_bet_cap = _number(config, "max_bet_fraction", 0.02, lower=0, upper=1)
    date_cap = 1.0 if config.get("date_cap_fraction") is None else _number(config, "date_cap_fraction", None, lower=0, upper=1)
    voters = config.get("consensus_model_keys", [])
    if not isinstance(voters, (list, tuple)) or len(voters) != len(set(voters)):
        raise ValueError("consensus_model_keys must be distinct model keys")
    consensus_min = config.get("consensus_min")
    if consensus_min is not None:
        if isinstance(consensus_min, bool) or not isinstance(consensus_min, (int, np.integer)) or not 1 <= consensus_min <= len(voters):
            raise ValueError("consensus_min requires a positive integer no larger than the voter count")

    _columns(opportunities, ["match_id", "match_date", "result"], "opportunities")
    native = opportunities.copy(deep=True)
    native["match_id"] = native.match_id.astype("string")
    if native.match_id.isna().any() or native.match_id.duplicated().any():
        raise ValueError("Opportunity match IDs must be present and unique")
    native["match_date"] = pd.to_datetime(native.match_date.astype("string").str[:10], format="%Y-%m-%d", errors="raise")
    if native.match_date.isna().any() or not native.result.isin(OUTCOMES).all():
        raise ValueError("Missing match dates or invalid H/D/A results")
    if "season" in native and not native.season.eq("2025-26").all():
        raise ValueError("The continuous comparison is restricted to 2025-26")
    if "snapshot_type" in native and native.snapshot_type.dropna().nunique() > 1:
        raise ValueError("A strategy cannot mix archived snapshot types")
    native = native.sort_values(["match_date", "match_id"], kind="stable").reset_index(drop=True)
    quote_columns = [f"{'ref_' if mode == 'reference' else ''}odds_{label}" for label in OUTCOMES]
    _columns(native, quote_columns, "selected quote panel")
    quotes = native[quote_columns].apply(pd.to_numeric, errors="coerce").to_numpy(float)
    if not np.isfinite(quotes).all() or not (quotes > 1).all():
        raise ValueError("Every match requires a complete finite individual-book triplet above 1")

    probability_cache = {}

    def probabilities(key):
        if not isinstance(key, str) or not key:
            raise ValueError("model_key must be a nonempty string")
        if key in probability_cache:
            return probability_cache[key]
        if key not in models:
            raise ValueError(f"Missing model probability series: {key}")
        frame = models[key].copy(deep=True)
        _columns(frame, ["match_id", "p_H", "p_D", "p_A"], f"model {key}")
        frame["match_id"] = frame.match_id.astype("string")
        if frame.match_id.isna().any() or frame.match_id.duplicated().any():
            raise ValueError(f"Model {key} has missing or duplicate identities")
        aligned = frame.set_index("match_id").reindex(native.match_id)[["p_H", "p_D", "p_A"]]
        values = aligned.apply(pd.to_numeric, errors="coerce").to_numpy(float)
        if not np.isfinite(values).all() or (values < 0).any() or (values > 1).any() or not np.allclose(values.sum(axis=1), 1, rtol=0, atol=1e-8):
            raise ValueError(f"Model {key} lacks normalized finite probabilities for every priced fixture")
        probability_cache[key] = values
        return values

    probs = probabilities(config.get("model_key"))
    edges = probs * quotes - 1
    candidate = np.broadcast_to(np.isin(OUTCOMES, allowed), quotes.shape).copy()
    if min_odds is not None:
        candidate &= quotes >= min_odds
    if max_odds is not None:
        candidate &= quotes <= max_odds
    scores = edges
    if rule == "model_favorite":
        scores = probs
    elif rule in {"market_favorite", "market_underdog"}:
        scores = probabilities("baseline_market_only") * (1 if rule == "market_favorite" else -1)
    elif rule == "fixed_outcome":
        scores = np.zeros_like(edges)
    chosen = np.argmax(np.where(candidate, scores, -np.inf), axis=1)
    index = np.arange(len(native))
    selected_price, selected_probability, selected_edge = quotes[index, chosen], probs[index, chosen], edges[index, chosen]
    eligible = candidate.any(axis=1)
    if edge_min is not None:
        eligible &= selected_edge > edge_min
    votes = None
    if consensus_min is not None:
        votes = sum((probabilities(key)[index, chosen] * selected_price - 1 > 0).astype(int) for key in voters)
        eligible &= votes >= consensus_min
    if cash:
        eligible[:] = False
    native["_position"] = index
    bankroll, peak = initial, initial
    bet_rows, equity_rows = [], []
    strategy_name, origin = config.get("name", strategy_id), config.get("origin", "unspecified")
    for date, day in native.groupby("match_date", sort=True):
        start = bankroll
        positions = day._position.to_numpy(int)
        selected = positions[eligible[positions]]
        full_kelly = np.maximum(0.0, selected_edge[selected] / (selected_price[selected] - 1))
        if staking == "fixed":
            requested = np.full(len(selected), fixed) if start > 0 else np.zeros(len(selected))
        elif staking == "dynamic_fraction":
            requested = np.full(len(selected), start * fraction)
        else:
            requested = start * np.minimum(per_bet_cap, kelly * full_kelly)
        requested_sum = float(requested.sum())
        if not np.isfinite(requested).all() or not math.isfinite(requested_sum):
            raise ValueError("Nonfinite requested stakes")
        budget = start * date_cap
        scale = min(1.0, budget / requested_sum) if requested_sum > 0 else 1.0
        stakes = requested * scale
        if len(stakes) and stakes.sum() > budget:
            stakes[-1] = max(0.0, stakes[-1] - float(stakes.sum() - budget))
        # Only after the complete date's commitments are fixed do outcomes
        # enter the cashflow calculation.
        wins = native.loc[selected, "result"].to_numpy() == OUTCOMES[chosen[selected]]
        gross = np.where(wins, stakes * selected_price[selected], 0.0)
        if not np.isfinite(gross).all():
            raise ValueError("Nonfinite settlement cashflows")
        turnover, profit = float(stakes.sum()), float((gross - stakes).sum())
        if turnover > start + 1e-8:
            raise AssertionError("Date commitments exceed available cash")
        bankroll = start - turnover + float(gross.sum())
        if bankroll < -1e-8 or not math.isfinite(bankroll):
            raise AssertionError("Invalid closing bankroll")
        bankroll = max(0.0, bankroll)
        peak = max(peak, bankroll)
        for offset, position in enumerate(selected):
            if stakes[offset] <= 0:
                continue
            row = native.iloc[position]
            label = OUTCOMES[chosen[position]]
            bookmaker = row.get("reference_bookmaker", "Bet365") if mode == "reference" else row.get("bookmaker_" + label, "individual_bookmaker_unrecorded")
            bet_rows.append({"strategy_id": strategy_id, "strategy_name": strategy_name, "origin": origin,
                             "episode_id": "2025-26", "match_id": row.match_id, "match_date": date, "result": row.result,
                             "selection": label, "probability": float(selected_probability[position]),
                             "odds": float(selected_price[position]), "bookmaker": bookmaker,
                             "edge": float(selected_edge[position]), "consensus_votes": int(votes[position]) if votes is not None else None,
                             "full_kelly_fraction": float(full_kelly[offset]), "requested_stake": float(requested[offset]),
                             "stake": float(stakes[offset]), "won": bool(wins[offset]), "gross_return": float(gross[offset]),
                             "profit": float(gross[offset] - stakes[offset]), "date_start_bankroll": start, "date_end_bankroll": bankroll,
                             "start_bankroll": start, "end_bankroll": bankroll, "commitment_scale": scale,
                             "staking": staking, "odds_mode": mode, "selection_rule": rule, "threshold": edge_min,
                             "snapshot_type": row.get("snapshot_type", "unspecified_archived_snapshot")})
        equity_rows.append({"strategy_id": strategy_id, "strategy_name": strategy_name, "origin": origin,
                            "episode_id": "2025-26", "match_date": date, "matched_matches": len(day),
                            "qualified_matches": len(selected), "bet_count": int(np.count_nonzero(stakes > 0)),
                            "requested_stakes": requested_sum, "date_budget_fraction": date_cap, "date_budget_units": budget,
                            "commitment_scale": scale, "turnover": turnover, "profit": profit,
                            "start_bankroll": start, "end_bankroll": bankroll, "bankroll_start": start, "bankroll_end": bankroll,
                            "daily_return": bankroll / start - 1 if start > 0 else 0.0,
                            "running_peak": peak, "drawdown": 1 - bankroll / peak,
                            "log_growth": math.log(bankroll / initial) if bankroll > 0 else -math.inf})
    bets = pd.DataFrame(bet_rows, columns=BET_COLUMNS)
    equity = pd.DataFrame(equity_rows, columns=EQUITY_COLUMNS)
    for field in ("probability", "odds", "edge", "full_kelly_fraction", "requested_stake", "stake", "gross_return",
                  "profit", "date_start_bankroll", "date_end_bankroll", "start_bankroll", "end_bankroll", "commitment_scale"):
        bets[field] = bets[field].astype(float)
    bets["won"] = bets.won.astype(bool)
    bets["consensus_votes"] = pd.array(bets.consensus_votes, dtype="Int64")
    bets["match_date"] = pd.to_datetime(bets.match_date)
    equity["match_date"] = pd.to_datetime(equity.match_date)
    if bets.match_id.duplicated().any() or equity.match_date.duplicated().any():
        raise AssertionError("Duplicate selected fixture or date equity identity")
    return bets, equity
