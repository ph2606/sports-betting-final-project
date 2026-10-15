"""The complete declared 84-rule catalog; IDs never depend on realized returns."""
from __future__ import annotations

from copy import deepcopy
import json


LOGIT_KEYS = ["logit_team_only", "logit_team_xg", "logit_team_players", "logit_combined"]
RESIDUAL_KEYS = ["residual_team_only", "residual_team_xg", "residual_team_players", "residual_combined"]
LEARNED_KEYS = LOGIT_KEYS + RESIDUAL_KEYS
MODEL_LABELS = {
    "first_accuracy": "First-study accuracy-selected SVM",
    "first_calibration": "First-study calibration-selected MLP",
    "logit_team_only": "Rolling logistic: team", "logit_team_xg": "Rolling logistic: team + xG",
    "logit_team_players": "Rolling logistic: team + player", "logit_combined": "Rolling logistic: combined",
    "residual_team_only": "Rolling market residual: team", "residual_team_xg": "Rolling market residual: team + xG",
    "residual_team_players": "Rolling market residual: team + player", "residual_combined": "Rolling market residual: combined",
    "baseline_class_frequency": "Rolling training-class frequency", "baseline_market_only": "Raw de-vigged Bet365 market",
    "market_temperature": "Temperature-calibrated Bet365 market",
    "ensemble_logit4": "Equal-weight mean of four rolling logistic probabilities",
    "ensemble_learned8": "Equal-weight mean of all eight rolling learned probabilities",
    "ensemble_market_blend": "50/50 combined logistic and raw de-vigged market probabilities",
}


def build_catalog() -> list[dict]:
    """Return independent JSON-safe configs in the fixed S001..S084 order.

    Filters on allowed classes and prices operate before selection. The
    consensus condition vetoes the selected mean-eight max-edge outcome.
    Edge thresholds are strict; odds-band bounds are inclusive.
    """
    rows = []

    def add(model_key, *, origin="new", staking="fixed", selection_rule="max_edge",
            name=None, description=None, policy_family="value", **changes):
        config = {"strategy_id": f"S{len(rows) + 1:03d}", "origin": origin,
                  "diagnostic": origin == "legacy_diagnostic", "model_key": model_key,
                  "model_label": MODEL_LABELS[model_key], "selection_rule": selection_rule,
                  "min_edge": 0.05, "allowed_outcomes": ["H", "D", "A"],
                  "min_odds": None, "max_odds": None, "consensus_min": None,
                  "consensus_model_keys": [], "staking": staking, "fixed_stake": 1000.0,
                  "bankroll_fraction": 0.01, "kelly_fraction": 0.25, "max_bet_fraction": 0.02,
                  "date_cap_fraction": None, "cash_only": False, "odds_mode": "best",
                  "policy_family": policy_family}
        config.update(changes)
        quote = "best individual-book quotes" if config["odds_mode"] == "best" else "Bet365 reference quotes"
        stake_name = "flat 1,000" if staking == "fixed" else "dynamic 1% of date-start capital" if staking == "dynamic_fraction" else f"{config['kelly_fraction']:g} Kelly, per-bet cap {config['max_bet_fraction']:.0%}"
        config["name"] = name or f"{MODEL_LABELS[model_key]} | {policy_family} | {quote} | {stake_name}"
        config["description"] = description or (
            f"{MODEL_LABELS[model_key]}; {selection_rule} selection among the allowed outcomes at {quote}. "
            f"Require selected model expected return strictly above {100 * config['min_edge']:g}%; stake {stake_name}."
        )
        config["allocation_basis"] = "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle"
        config["study_status"] = "exploratory_replay_of_already_examined_2025_26_no_new_holdout"
        rows.append(config)

    # S001..S016: both locked first-study branches, including explicit cash
    # policies; distinct historical configurations remain distinct flat curves.
    for model in ("first_accuracy", "first_calibration"):
        for cash in (True, False):
            for odds_mode in ("best", "reference"):
                for staking in ("fixed", "kelly"):
                    add(model, origin="legacy", staking=staking, odds_mode=odds_mode,
                        min_edge=1_000_000.0 if cash else 0.05, cash_only=cash,
                        policy_family="locked primary cash" if cash else "predeclared 5% edge",
                        description=(f"{MODEL_LABELS[model]}: validation selected no admissible positive-return rule; "
                                     "the frozen threshold is 1,000,000 and this configuration remains entirely in cash.") if cash else None)
    # S017..S038: all eleven source-study series, both original stake rules.
    for model in LEARNED_KEYS + ["baseline_class_frequency", "baseline_market_only", "market_temperature"]:
        for staking in ("fixed", "kelly"):
            add(model, origin="legacy", staking=staking, policy_family="predeclared 5% edge")

    # S039..S045: unconditional controls retain negative expected edges.
    for outcome in "HDA":
        add("baseline_market_only", selection_rule="fixed_outcome", min_edge=None,
            allowed_outcomes=[outcome], policy_family="unconditional class benchmark",
            name=f"Always {outcome} | best quotes | flat 1,000",
            description=f"Back {outcome} on every priced fixture at its best archived individual-book quote, with flat stake 1,000 and no edge filter; market probability is descriptive only.")
    for rule, title in (("market_favorite", "Market favorite"), ("market_underdog", "Market underdog")):
        add("baseline_market_only", selection_rule=rule, min_edge=None,
            policy_family="unconditional market benchmark", name=f"{title} | best quotes | flat 1,000",
            description=f"Choose the {'highest' if rule == 'market_favorite' else 'lowest'} raw de-vigged Bet365 probability, then use that outcome's best archived quote and flat stake 1,000; no edge filter.")
    for model in ("logit_combined", "residual_combined"):
        add(model, selection_rule="model_favorite", min_edge=None,
            policy_family="unconditional model favorite",
            description=f"Choose {MODEL_LABELS[model]}'s highest-probability outcome at its best archived quote; flat stake 1,000 with no edge filter.")

    # S046..S051: outcome-independent probability combinations.
    for model in ("ensemble_logit4", "ensemble_learned8", "ensemble_market_blend"):
        for staking in ("fixed", "kelly"):
            add(model, staking=staking, policy_family="ensemble 5% edge")
    # S052..S054: a capital-fraction stake, independent of the stated edge size.
    focal = ["logit_combined", "residual_combined", "ensemble_learned8"]
    for model in focal:
        add(model, staking="dynamic_fraction", policy_family="dynamic 1% stake")
    # S055..S058: declared Kelly fractions and caps, without outcome tuning.
    for model in focal[:2]:
        for fraction, cap, title in ((0.125, 0.01, "eighth Kelly, cap 1%"), (0.5, 0.02, "half Kelly, cap 2%")):
            add(model, staking="kelly", kelly_fraction=fraction, max_bet_fraction=cap, policy_family=title)
    # S059..S061: scale aggregate same-date commitments to at most 10%.
    for model in focal:
        add(model, staking="kelly", date_cap_fraction=0.1, policy_family="quarter Kelly, 10% date budget",
            description=f"Select {MODEL_LABELS[model]}'s maximum edge strictly above 5%. Use quarter Kelly capped at 2% per bet, then uniformly scale all same-date requests to at most 10% of date-start capital.")
    # S062..S063: do not search another outcome after a consensus veto.
    for staking in ("fixed", "kelly"):
        add("ensemble_learned8", staking=staking, consensus_min=6,
            consensus_model_keys=LEARNED_KEYS.copy(), policy_family="six-of-eight consensus",
            description="Choose the mean-eight maximum-edge outcome strictly above 5%; retain it only if at least six of the eight individual rolling learned models have strictly positive edge at that same selected best quote. A failed vote means no bet, without searching another class.")
    # S064..S066: class restrictions act on candidates before argmax.
    for outcome in "HDA":
        add("ensemble_learned8", allowed_outcomes=[outcome], policy_family=f"5% edge, {outcome} only",
            description=f"Restrict candidates to outcome {outcome} before maximizing mean-eight edge; require strict edge above 5% and use flat stake 1,000 at its best archived quote.")
    # S067..S069 and S070..S072: two declared eligibility sensitivities.
    for model in focal:
        add(model, min_edge=0.1, policy_family="10% edge")
    for model in focal:
        add(model, min_odds=1.5, max_odds=5.0, policy_family="5% edge, odds 1.5–5",
            description=f"Retain only outcomes with inclusive best-quote decimal odds from 1.5 to 5 before maximizing {MODEL_LABELS[model]}'s edge. Require selected edge strictly above 5%; flat stake 1,000.")
    # S073..S084: preserve every distinct saved threshold-diagnostic rule.
    for model in ("first_accuracy", "first_calibration"):
        for edge in (0.0, 0.025, 0.075, 0.10, 0.15, 0.20):
            add(model, origin="legacy_diagnostic", min_edge=edge,
                policy_family=f"historical threshold diagnostic {100 * edge:g}%",
                description=f"Replay the saved {MODEL_LABELS[model]} validation-candidate rule with edge strictly above {100 * edge:g}% (p × odds − 1 > {edge:g}), best individual-book quotes and flat stake 1,000. This is an exploratory diagnostic replay on an already examined season, not the selected primary strategy.")
    if len(rows) != 84 or [row["strategy_id"] for row in rows] != [f"S{i:03d}" for i in range(1, 85)]:
        raise AssertionError("The declared catalog must retain all 84 stable IDs")
    if sum(row["origin"] == "new" for row in rows) != 34:
        raise AssertionError("Exactly 34 added exploratory configurations are declared")
    json.dumps(rows, allow_nan=False)
    return deepcopy(rows)


CATALOG = build_catalog()
