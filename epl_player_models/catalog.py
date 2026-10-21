"""Stable new model/strategy identities independent of realised performance."""
from copy import deepcopy
import json

GROUPS = ("team_control", "player_form", "player_squad", "team_player_squad")
FAMILIES = ("logistic", "hist_boost")
GROUP_LABELS = {"team_control": "Matched team control", "player_form": "Player form only",
    "player_squad": "Player form + projected XI + depth", "team_player_squad": "Team + full player block"}
FAMILY_LABELS = {"logistic": "Logistic regression", "hist_boost": "Histogram gradient boosting"}


def model_key(group, family):
    if group not in GROUPS or family not in FAMILIES: raise ValueError("Unknown fixed model variant")
    return "pm_" + family + "_" + group


def model_members(feature_groups=None):
    rows = []
    for group in GROUPS:
        for family in FAMILIES:
            rows.append({"model_key": model_key(group, family), "feature_group": group, "model_type": family,
                "label": GROUP_LABELS[group] + " | " + FAMILY_LABELS[family],
                "n_features": len(feature_groups[group]) if feature_groups is not None else None,
                "uses_player_performance": group != "team_control", "uses_team_performance": group in ("team_control", "team_player_squad")})
    return rows


def build_catalog():
    rows = []
    for member in model_members():
        for odds_mode in ("best", "reference"):
            for staking in ("fixed", "kelly"):
                price = "best archived individual-book quote" if odds_mode == "best" else "archived Bet365 reference quote"
                sizing = "flat 1,000" if staking == "fixed" else "quarter Kelly capped at 2% of date-start cash per bet"
                rows.append({"strategy_id": f"P{len(rows)+1:03d}", "origin": "new_player_model_study",
                    "diagnostic": True, "model_key": member["model_key"], "model_label": member["label"],
                    "feature_group": member["feature_group"], "model_type": member["model_type"],
                    "selection_rule": "max_edge", "min_edge": .05, "allowed_outcomes": ["H", "D", "A"],
                    "min_odds": None, "max_odds": None, "consensus_min": None, "consensus_model_keys": [],
                    "staking": staking, "fixed_stake": 1000., "bankroll_fraction": .01,
                    "kelly_fraction": .25, "max_bet_fraction": .02, "date_cap_fraction": None,
                    "cash_only": False, "odds_mode": odds_mode, "policy_family": "frozen 5% player-study diagnostic",
                    "name": member["label"] + " | " + odds_mode + " | " + sizing,
                    "description": member["label"] + "; choose the allowed H/D/A outcome with maximum p × odds − 1 at the " + price +
                        ". Trade only for edge strictly greater than 5%; request " + sizing + ". H/D/A order resolves ties.",
                    "allocation_basis": "All requests use date-start cash and are uniformly scaled to available cash before any same-date outcome settles",
                    "study_status": "exploratory_previously_inspected_history_not_new_holdout_or_selected_live_betting_policy"})
    if len(rows) != 32 or len({r["strategy_id"] for r in rows}) != 32:
        raise AssertionError("The complete fixed 32-strategy catalog changed")
    json.dumps(rows, allow_nan=False)
    return deepcopy(rows)
