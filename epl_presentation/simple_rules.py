"""Plain-English descriptions of the 116 already implemented trading rules.

This module describes saved catalog settings. It does not fit a model, choose a
new rule, calculate a new strategy, or modify a historical result. Monetary
amounts are generic units, with the presentation's initial capital of 100,000.
The wording follows epl_strategy_lab.engine.simulate_strategy, including its
date-start allocation and its selected-outcome consensus test.
"""
from __future__ import annotations

import json
import math


INITIAL_CAPITAL = 100_000
OUTCOME_NAMES = {"H": "home win", "D": "draw", "A": "away win"}

MODEL_NAMES = {
    "first_accuracy": "Original SVM forecast",
    "first_calibration": "Original neural-network forecast",
    "logit_team_only": "Team form",
    "logit_team_xg": "Team form + chance quality",
    "logit_team_players": "Team form + player form",
    "logit_combined": "Team + chance quality + player form",
    "residual_team_only": "Bookmaker odds + team form",
    "residual_team_xg": "Bookmaker odds + team/chance quality",
    "residual_team_players": "Bookmaker odds + team/player form",
    "residual_combined": "Bookmaker odds + team/chance/player form",
    "baseline_class_frequency": "Past home/draw/away frequencies",
    "baseline_market_only": "Bookmaker probabilities",
    "baseline_market_temperature": "Calibrated bookmaker probabilities",
    "market_temperature": "Calibrated bookmaker probabilities",
    "ensemble_logit4": "Average of four team/player forecasts",
    "ensemble_learned8": "Average of eight learned forecasts",
    "ensemble_market_blend": "Half combined forecast, half bookmaker",
    "pm_logistic_team_control": "Team form (logistic)",
    "pm_hist_boost_team_control": "Team form (boosted trees)",
    "pm_logistic_player_form": "Player form (logistic)",
    "pm_hist_boost_player_form": "Player form (boosted trees)",
    "pm_logistic_player_squad": "Player form + estimated XI/depth (logistic)",
    "pm_hist_boost_player_squad": "Player form + estimated XI/depth (trees)",
    "pm_logistic_team_player_squad": "Team + player form/XI/depth (logistic)",
    "pm_hist_boost_team_player_squad": "Team + player form/XI/depth (trees)",
}


def model_name(key: str) -> str:
    """Return a short name for a model already present in the saved catalog."""
    try:
        return MODEL_NAMES[key]
    except KeyError as error:
        raise ValueError(f"No implemented model description for {key!r}") from error


def _percent(value: float) -> str:
    return f"{100 * float(value):g}%"


def _amount(value: float) -> str:
    return f"{float(value):,.2f}".rstrip("0").rstrip(".")


def _optional(value):
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    return value


def _list(value):
    return json.loads(value) if isinstance(value, str) else list(value)


def _flag(value) -> bool:
    if isinstance(value, str):
        if value.lower() not in {"true", "false"}:
            raise ValueError(f"Invalid boolean {value!r}")
        return value.lower() == "true"
    return bool(value)


def describe_strategy(row) -> dict[str, str]:
    """Describe a saved catalog row, including exactly how capital is requested.

    ``row`` may be a catalog dictionary or a metrics-table row. Formulas use B
    for cash at the start of the match date, p for the selected outcome's model
    probability, and O for decimal odds. Requested stakes can be reduced by the
    shared cash/date budget before any match on that date settles.
    """
    key = str(row["model_key"])
    model = model_name(key)
    rule = str(row["selection_rule"])
    staking = str(row["staking"])
    mode = str(row["odds_mode"])
    allowed = _list(row.get("allowed_outcomes", ["H", "D", "A"]))
    if not allowed or not set(allowed).issubset(OUTCOME_NAMES):
        raise ValueError("Expected implemented home/draw/away outcomes")
    if rule not in {"max_edge", "fixed_outcome", "market_favorite", "market_underdog", "model_favorite"}:
        raise ValueError(f"Unknown implemented selection rule {rule!r}")
    if staking not in {"fixed", "dynamic_fraction", "kelly"}:
        raise ValueError(f"Unknown implemented staking rule {staking!r}")
    if mode not in {"best", "reference"}:
        raise ValueError(f"Unknown implemented price source {mode!r}")
    prices = (
        "Highest archived individual-bookmaker odds for the chosen outcome."
        if mode == "best" else "Archived Bet365 odds for the chosen outcome."
    )

    if _flag(row.get("cash_only", False)):
        result = dict(
            model=model,
            entry="No bets: the earlier validation selected cash.",
            stake="0 per trade; all starting 100,000 stays in cash.",
            limits="No borrowing; no betting exposure.",
            prices="No quotes used for a trade.",
            example="Starting capital 100,000 stays 100,000 throughout the replay.",
        )
        result["plain"] = " ".join(result.values())
        return result

    allowed_text = ", ".join(OUTCOME_NAMES[label] for label in allowed)
    if rule == "fixed_outcome":
        if len(allowed) != 1:
            raise ValueError("A fixed outcome needs one home/draw/away result")
        entry = f"Bet on {OUTCOME_NAMES[allowed[0]]} in every priced match; no return filter."
    elif rule == "market_favorite":
        entry = "Back the home/draw/away result with the highest bookmaker probability; no return filter."
    elif rule == "market_underdog":
        entry = "Back the home/draw/away result with the lowest bookmaker probability; no return filter."
    elif rule == "model_favorite":
        entry = "Back the home/draw/away result with the highest model probability; no return filter."
    else:
        threshold = _optional(row.get("min_edge"))
        if threshold is None:
            raise ValueError("The implemented maximum-return rules need a threshold")
        entry = (
            f"Among {allowed_text}, pick the largest estimated return p×O−1; "
            f"bet only above {_percent(threshold)}."
        )

    restrictions = []
    lo, hi = _optional(row.get("min_odds")), _optional(row.get("max_odds"))
    if lo is not None and hi is not None:
        restrictions.append(f"First keep decimal odds from {_amount(lo)} to {_amount(hi)}, inclusive.")
    elif lo is not None:
        restrictions.append(f"First keep decimal odds at least {_amount(lo)}.")
    elif hi is not None:
        restrictions.append(f"First keep decimal odds at most {_amount(hi)}.")
    consensus = _optional(row.get("consensus_min"))
    if consensus is not None:
        voters = _list(row.get("consensus_model_keys", []))
        restrictions.append(
            f"Then require at least {int(consensus)} of {len(voters)} models to give "
            "the chosen outcome a positive estimated return at these odds."
        )

    if staking == "fixed":
        fixed = float(row.get("fixed_stake", 1_000))
        stake = (
            f"{_amount(fixed)} per bet: {_percent(fixed / INITIAL_CAPITAL)} of INITIAL 100,000; "
            "the amount stays fixed as cash changes."
        )
        example = (
            f"With cash 80,000, still request {_amount(fixed)} per qualifying bet "
            "before any shared cash reduction."
        )
    elif staking == "dynamic_fraction":
        fraction = float(row.get("bankroll_fraction", 0.01))
        stake = f"{_percent(fraction)} of cash at the start of that match date per bet."
        example = (
            f"Cash 100,000 → {_amount(100_000 * fraction)} per bet; "
            f"cash 80,000 → {_amount(80_000 * fraction)} per bet, before shared cash reduction."
        )
    else:
        multiplier = float(row.get("kelly_fraction", 0.25))
        cap = float(row.get("max_bet_fraction", 0.02))
        multiplier_name = {0.125: "Eighth Kelly", 0.25: "Quarter Kelly", 0.5: "Half Kelly"}.get(
            multiplier, f"{_percent(multiplier)} Kelly"
        )
        stake = (
            f"{multiplier_name}: B × min({_percent(cap)}, {multiplier:g} × max(0, p×O−1)/(O−1)); "
            "B = date-start cash."
        )
        request = 100_000 * min(cap, multiplier * (0.40 * 3 - 1) / (3 - 1))
        example = (
            f"B=100,000, p=40%, O=3: full Kelly=10%; {multiplier:g} × 10% "
            f"capped at {_percent(cap)} requests {_amount(request)} before shared date/cash reduction."
        )

    date_cap = _optional(row.get("date_cap_fraction"))
    if date_cap is not None:
        restrictions.append(
            f"All bets on one date together use at most {_percent(date_cap)} of date-start cash; "
            "shrink every request by the same proportion if necessary."
        )
    else:
        restrictions.append(
            "If all same-date requests exceed available cash, shrink every request by the same proportion."
        )
    restrictions.append("At most one bet per match; no borrowing or use of same-date winnings.")
    result = dict(model=model, entry=entry, stake=stake, limits=" ".join(restrictions), prices=prices, example=example)
    result["plain"] = " ".join(result.values())
    return result


def get_rule_guide() -> list[dict[str, str]]:
    """Reusable appendix explanations of the capital rules actually simulated."""
    return [
        {"title": "Starting capital", "rule": "Every displayed account starts with 100,000 monetary units. A strategy is a forecast plus a bet-selection and staking rule."},
        {"title": "What p, O and B mean", "rule": "p is the model's estimated chance of the chosen result; O is decimal odds; B is cash at the start of the match date. Estimated return per unit = p×O−1. A 5% filter means strictly above 5%, not a guaranteed return."},
        {"title": "Fixed 1,000", "rule": "Request 1,000 for each qualifying bet. This is 1% of INITIAL 100,000. With cash 80,000 the request remains 1,000; with cash 120,000 it also remains 1,000."},
        {"title": "Dynamic 1%", "rule": "Request 1% of current date-start cash for each qualifying bet: 1,000 at cash 100,000; 800 at cash 80,000; 1,200 at cash 120,000."},
        {"title": "Kelly amount", "rule": "Full Kelly fraction = max(0, p×O−1)/(O−1). Multiply that fraction by 1/8, 1/4 or 1/2, apply the rule's 1% or 2% per-bet cap, then multiply by date-start cash. This is a varying amount, not always the cap."},
        {"title": "Quarter-Kelly example", "rule": "Cash 100,000, probability 40%, odds 3: full Kelly = (0.40×3−1)/(3−1) = 10%. One quarter is 2.5%; a 2% cap reduces the requested bet to 2,000. At probability 38% and odds 3, the request is 1,750 because the cap is not reached."},
        {"title": "10% date budget", "rule": "For S059–S061, all requests on one date share at most 10% of that date's starting cash. With cash 100,000 and six requests of 2,000, reduce all six to 1,666.67, apart from rounding: total 10,000."},
        {"title": "Shared cash limit", "rule": "Every rule is cash-funded. Fix all stakes for a date before any results settle. If total requested stakes exceed the available cash or smaller date budget, multiply every request by the same reduction factor. Same-date winnings cannot fund another bet; zero cash means no more bets."},
        {"title": "One result per match", "rule": "First apply the allowed-result and odds-range restrictions, then pick one result. Ties use home win, then draw, then away win. A threshold or consensus check can veto that choice; it does not trigger a second choice."},
        {"title": "Six-of-eight consensus", "rule": "For S062–S063, first choose the eight-model average's best-return outcome. At least six of the eight individual models must assign that same outcome positive estimated return at its price. They need not choose it as their own favorite."},
        {"title": "Cash-only rules", "rule": "S001–S004 and S009–S012 request zero on every match because the original validation selected no admissible positive-return rule. Their account stays at 100,000."},
        {"title": "Archived odds", "rule": "Best quotes means the highest saved individual-bookmaker odds for the chosen result; reference means saved Bet365 odds. These are historical quote assumptions, with no verified live execution or fills."},
    ]
