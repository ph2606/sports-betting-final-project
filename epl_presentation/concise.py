"""Six requested presentation slides and a plain-language strategy appendix."""
from __future__ import annotations

import argparse
from collections import OrderedDict
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import shutil

from .build import ROOT, PACKAGE, STUDY, LAB, VALIDATION, TEAL, NAVY, MUTED, text, card, table, slide, load, money, pct, dec, sha, jsave
from .render import render
from .simple_rules import describe_strategy, model_name

ORIGINAL = ROOT / "epl_presentation/results/20261021_implemented"
ROLES = [("best_learned", "S029", "Best prediction model: odds + team/player form",
          "Lowest prediction error among the learned models on the same four-year sample.",
          "Starts with bookmaker probabilities, then adjusts them using earlier team results and player form."),
         ("simplest", "S033", "Simplest model: past result frequencies",
          "No match-specific inputs: every game in a season gets the same three probabilities.",
          "Counts how often home wins, draws and away wins happened in the training data. Uses those fractions for every game."),
         ("team", "S017", "Team model: earlier team performance",
          "Uses team performance and data-coverage controls; no player-performance or odds predictors.",
          "Uses earlier goals, shots on target, corners, points, rest days and previous-season results to estimate home/draw/away chances."),
         ("player", "P009", "Player model: earlier Fantasy Premier League form",
          "Uses previous player records; no team-strength or bookmaker-odds predictors.",
          "Uses earlier FPL points, goals and assists.\nAdds minutes and other player statistics.\nLooks back over five and ten games.")]


def profile(data, spec):
    key, sid, title, subtitle, description = spec
    r = data["continuous"].loc[sid]
    p = data["models"]["profiles"][key]["metrics"]
    config = next(row for row in data["catalog"] if row["strategy_id"] == sid)
    rules = describe_strategy(config)
    elements = [text(.65, 2.12, 6.9, .35, "WHAT IT DOES", 15, TEAL, True),
        text(.65, 2.62, 6.9, 1.45, description, 22),
        text(.65, 4.23, 6.9, .35, "WHEN AND HOW MUCH IT BETS", 15, TEAL, True),
        text(.65, 4.75, 6.9, 2.18,
            "Choose home, draw or away with the highest estimated return.\nBet only when the model estimates a return above 5%.\nRequest 1,000 per bet: 1% of the initial 100,000.", 21),
        text(.65, 7.13, 6.9, .5, "Forecast accuracy: " + pct(p["accuracy"]) + "  |  Prediction loss: " + dec(p["log_loss"]), 16, MUTED),
        card(8.05, 2.08, 3.45, 1.55, "ENDING CAPITAL", money(r.final_capital_sum_units), "Started at 100,000"),
        card(11.85, 2.08, 3.45, 1.55, "RETURN ON INITIAL CAPITAL", pct(r.return_on_initial_capital), "Four-year account"),
        table(8.05, 4.05, 7.25, 3.35, ["Trading statistic", "Result"],
            [["Bets / trading frequency", money(r.bet_count) + " / " + pct(r.trading_frequency)],
             ["Hit ratio: bets won", pct(r.hit_ratio)],
             ["Expected gain per trade", dec(r.expected_gain_per_trade_units, 2)],
             ["Expected loss per trade", dec(r.expected_loss_per_trade_units, 2)],
             ["Profit / ROI on total stakes", money(r.profit) + " / " + pct(r.roi)],
             ["Largest drop from a prior peak", pct(r.max_drawdown)]], [.60, .40], 17),
        text(.65, 7.82, 14.6, .35, "Stakes can be reduced to available opening cash. Expected gain/loss are model estimates, not realized average wins/losses.", 14.5, MUTED)]
    return slide(title, subtitle + " Trading statistics: 2022/23–2025/26, 1,470 matches.", elements,
        kicker="MODEL AND ITS TRADING RULE | " + sid,
        sources=[p["source"], VALIDATION / "metrics_continuous.parquet", STUDY / "metrics_continuous.parquet"],
        notes=description + "\n" + rules["plain"] + "\n" + rules["example"] +
            "\nThe fixed 1,000 equals 1% of the INITIAL capital, not 1% of a changing account. "
            "All same-date requests use opening cash and are reduced proportionally if together they exceed available cash. "
            "This model's prediction accuracy and its trading hit ratio measure different things. Historical results are exploratory. "
            "Best refers to the learned model's pooled prediction loss, not the highest ending account; the raw market benchmark has lower prediction loss.\n" +
            "Exact configuration:\n" + json.dumps(config, ensure_ascii=False, sort_keys=True))


def grouped_catalog(catalog):
    fields = ["model_key", "selection_rule", "min_edge", "allowed_outcomes", "min_odds", "max_odds",
        "consensus_min", "consensus_model_keys", "cash_only", "odds_mode", "date_cap_fraction"]
    groups = OrderedDict()
    for row in catalog:
        key = ("cash", row["model_key"]) if row["cash_only"] else tuple(json.dumps(row.get(f), sort_keys=True) for f in fields)
        groups.setdefault(key, []).append(row)
    compact = []
    for group in groups.values():
        if group[0]["cash_only"]:
            compact.append(group)
        else:
            compact.extend(group[start:start + 2] for start in range(0, len(group), 2))
    return compact


def appendix_row(group):
    r = group[0]
    if r["cash_only"]:
        return [group[0]["strategy_id"] + "–" + group[-1]["strategy_id"], model_name(r["model_key"]), "No bets; keep cash", "0", "No betting"]
    ids = " / ".join(row["strategy_id"] for row in group)
    selection = r["selection_rule"]
    if selection == "max_edge":
        entry = "Estimated return > " + f"{100 * r['min_edge']:g}%"
    elif selection == "fixed_outcome":
        entry = {"H": "Always home win", "D": "Always draw", "A": "Always away win"}[r["allowed_outcomes"][0]] + "\nNo return filter"
    elif selection == "market_favorite":
        entry = "Bookmaker's most likely result\nNo return filter"
    elif selection == "market_underdog":
        entry = "Bookmaker's least likely result\nNo return filter"
    else:
        entry = "Model's most likely result\nNo return filter"
    extras = []
    if selection == "max_edge" and r["allowed_outcomes"] != list("HDA"):
        extras.append("Only " + "/".join(r["allowed_outcomes"]))
    if r["min_odds"] is not None or r["max_odds"] is not None:
        extras.append("Odds " + str(r["min_odds"] or "any") + "–" + str(r["max_odds"] or "any"))
    if r["consensus_min"] is not None:
        extras.append(f"Positive return: {r['consensus_min']}/{len(r['consensus_model_keys'])} models")
    if extras:
        entry += "\n" + "; ".join(extras)
    stakes = []
    for row in group:
        if row["staking"] == "fixed":
            stake = money(row["fixed_stake"])
        elif row["staking"] == "dynamic_fraction":
            stake = f"{100 * row['bankroll_fraction']:g}% of current cash"
        else:
            name = {.125: "1/8", .25: "1/4", .5: "1/2", 1.0: "Full"}.get(row["kelly_fraction"], str(row["kelly_fraction"]))
            stake = name + " Kelly; ≤" + f"{100 * row['max_bet_fraction']:g}% cash"
        stakes.append(row["strategy_id"] + ": " + stake)
    price = "Best odds" if r["odds_mode"] == "best" else "Bet365"
    limit = "Cash available" if r["date_cap_fraction"] is None else f"Date cap {100 * r['date_cap_fraction']:g}% cash"
    return [ids, model_name(r["model_key"]), entry, "\n".join(stakes), price + "\n" + limit]


def contents(data, output):
    elements = [card(.65, 2.05, 4.65, 1.6, "DATA", "20 current clubs", "Team and player histories"),
        card(5.66, 2.05, 4.65, 1.6, "TRADING RULES", "116 strategies", "Models combined with betting rules"),
        card(10.67, 2.05, 4.65, 1.6, "STARTING CAPITAL", "100,000 each", "Separate account for every strategy"),
        text(.65, 4.3, 14.6, 2.6,
             "Collected and checked team and player data.\nBuilt models for home wins, draws and away wins.\nTested betting rules and recorded profits, losses and risk.\nProduced money-progression graphs and timestamped forecasts.", 25),
        text(.65, 7.58, 14.6, .6, "Only completed work is shown. Historical backtests are not verified real-money trading results.", 18, MUTED)]
    slides = [slide("What we have implemented", "Premier League models and their trading strategies.", elements,
        sources=[STUDY / "study_status.json"], notes="Implemented data, outcome prediction, archived-price backtesting, metrics, charts and forecasts. No original-proposal material is included.")]
    graph = ORIGINAL / "figures/all_accounts_2025.png"
    slides.append(slide("Money progression of all 116 strategies", "2025/26: the common season available for every strategy. Every line starts at 100,000.",
        [dict(type="image", x=.65, y=2.1, w=14.7, h=5.35, path=str(graph)),
         text(.65, 7.72, 14.6, .5, "Each line is one model + betting rule + stake size. The following model statistics use the full four-year evaluation.", 16, MUTED)],
        sources=[STUDY / "graph_equity_2025_all.csv"], notes="All 116 strategy curves are shown, including overlapping cash accounts. The graph uses the one common season for all 116; only 88 strategies have comparable continuous four-year records. The four featured model pages use the saved four-year statistics, explicitly labeled. The graph is copied exactly from the previous audited presentation."))
    slides.extend(profile(data, row) for row in ROLES)
    slides.append(slide("Appendix: how much capital each rule uses", "Stake means the amount requested for one bet. The next pages state the setting for every strategy.",
        [table(.65, 2.05, 14.67, 3.55, ["Stake type", "Plain meaning", "Example"],
            [["Fixed 1,000", "Same requested amount each bet: 1% of INITIAL 100,000", "Cash 80,000 → still request 1,000"],
             ["1% of current cash", "One percent of cash at the start of the match date", "Cash 80,000 → request 800"],
             ["Kelly sizing", "Amount varies with estimated advantage and odds; the listed % is a ceiling", "A 2% cap means at most 2,000 when cash is 100,000"]], [.19, .46, .35], 19),
         text(.65, 5.98, 14.6, .75, "Kelly example: 100,000 cash, a 40% chance and odds of 3.\nQuarter Kelly requests 2,500; a 2% cap reduces the bet to 2,000.", 20),
         text(.65, 6.91, 14.6, .55, "Kelly stake = opening cash × min(cap, Kelly fraction × (probability × odds − 1) / (odds − 1)).", 17, MUTED),
         text(.65, 7.59, 14.6, .6, "All bets on a date share opening cash. Date caps apply to their combined stakes. Reduce all requests proportionally when needed; never borrow.", 17, MUTED)],
        appendix=True, sources=["epl_strategy_lab/engine.py", STUDY / "all_strategy_catalog.json"],
        notes="The Kelly multiplier is one quarter, one half, full Kelly or another explicitly listed fraction. B is cash at the start of the date. Formula B*min(max_bet_fraction,kelly_fraction*(p*O-1)/(O-1)); eligibility ensures positive edges where relevant. At most one bet per match. Same-date winnings are not used to fund another same-date bet. Fixed stakes do not automatically shrink to 1% as the account falls; only cash/date-budget allocation can scale them. Prices: Best odds means the highest saved individual-book quote for the chosen outcome; Bet365 means its saved reference quote. These are archived prices with unverified execution clocks."))
    groups = grouped_catalog(data["catalog"])
    n_pages = math.ceil(len(groups) / 9)
    q, remainder = divmod(len(groups), n_pages)
    start = 0
    for i in range(n_pages):
        count = q + int(i < remainder)
        page_groups = groups[start:start + count]
        start += count
        configs = [row for group in page_groups for row in group]
        details = []
        for row in configs:
            r = describe_strategy(row)
            details.append(row["strategy_id"] + ": " + r["plain"] + "\nExample: " + r["example"] +
                "\nExact configuration:\n" + json.dumps(row, ensure_ascii=False, sort_keys=True))
        slides.append(slide(f"Appendix: strategy rules ({i + 1}/{n_pages})",
            "Default: choose the highest model-estimated return (probability × odds − 1). Only bet above the listed threshold.",
            [table(.65, 2.02, 14.67, 6.0, ["Strategy IDs", "Data / model", "When it bets", "Requested money per bet", "Odds / total limit"],
                [appendix_row(group) for group in page_groups], [.12, .25, .25, .24, .14], 13, header_size=12)],
            appendix=True, sources=[STUDY / "all_strategy_catalog.json"],
            notes="Paired IDs share their forecast and entry rule but have separately labeled stakes. Fixed 1,000 is 1% of initial capital; a stated cash percentage uses date-start cash. Kelly fractions and caps are distinct. All IDs below are individual preserved strategies; grouping changes no rule. 'Positive return:6/8 models' requires six models to assign positive estimated return to the chosen outcome, not six favorite picks. H=home win, D=draw, A=away win.\n\n" + "\n\n".join(details)))
    return slides


def build(output, *, draft=False, publish=False):
    out = Path(output).resolve()
    if out.exists() and not draft:
        raise ValueError("Use a new concise presentation directory")
    if not draft and (PACKAGE / "results").resolve() not in out.parents:
        raise ValueError("Final outputs belong under epl_presentation/results")
    inputs = [PACKAGE / name for name in ("build.py", "render.py", "concise.py", "concise_audit.py", "simple_rules.py", "research_models.json", "research_trading.json", "research_audit.json")]
    inputs += [ORIGINAL / "figures/all_accounts_2025.png", ORIGINAL / "figures/all_accounts_2025.svg",
        ROOT / STUDY / "all_strategy_catalog.json", ROOT / STUDY / "metrics_continuous.parquet",
        ROOT / VALIDATION / "metrics_continuous.parquet", ROOT / "epl_modeling/ablation_results/predictions.parquet",
        ROOT / STUDY / "model_metrics_pooled.parquet", ROOT / STUDY / "graph_equity_2025_all.csv",
        ROOT / "epl_data/EPL_data_overview.xlsx"]
    protected = {p: sha(p) for p in inputs}
    out.mkdir(parents=True, exist_ok=True)
    data = load()
    slides = contents(data, out)
    figures = out / "figures"; figures.mkdir(exist_ok=True)
    for ext in ("png", "svg"):
        shutil.copyfile(ORIGINAL / f"figures/all_accounts_2025.{ext}", figures / f"all_accounts_2025.{ext}")
    slides[1]["elements"][0]["path"] = str(figures / "all_accounts_2025.png")
    jsave(out / "presentation_content.json", slides)
    jsave(out / "complete_strategy_catalog.json", data["catalog"])
    notes = ["# Short EPL presentation: six main slides", ""]
    for i, s in enumerate(slides, 1):
        notes += [f"## {i}. {s['title']}", "", s["subtitle"], "", s["notes"], "", "Sources:", *["- " + p for p in s["sources"]], ""]
    (out / "EPL_Presentation_Short_Notes.md").write_text("\n".join(notes), encoding="utf-8")
    rules = [{"strategy_id": row["strategy_id"], **describe_strategy(row)} for row in data["catalog"]]
    import pandas as pd
    pd.DataFrame(rules).to_csv(out / "EPL_Presentation_Short_Rules.csv", index=False)
    print(f"Rendering six main slides plus {len(slides) - 6} appendix slides", flush=True)
    rendering = render(slides, out)
    from .concise_audit import audit
    checked = audit(out, data=data)
    jsave(out / "independent_audit.json", checked)
    if any(sha(p) != digest for p, digest in protected.items()):
        raise AssertionError("A protected input changed")
    manifest = {"built_at_utc": datetime.now(timezone.utc).isoformat(), "main_slides": 6,
        "appendix_slides": len(slides) - 6, "source_sha256": {p.relative_to(ROOT).as_posix(): h for p, h in protected.items()},
        "user_open_full_presentation_untouched": True, "audit": checked,
        "native_text_overflows": rendering["native_layout"]["text_overflow_count"],
        "output_sha256": {p.relative_to(out).as_posix(): sha(p) for p in out.rglob("*") if p.is_file() and p.name != "manifest.json"}}
    jsave(out / "manifest.json", manifest)
    if publish:
        latest = ROOT / "presentations/latest"
        names = {"EPL_Project_Presentation.pptx": "EPL_Project_Presentation_Short.pptx",
            "EPL_Project_Presentation.pdf": "EPL_Project_Presentation_Short.pdf",
            "EPL_Presentation_Short_Notes.md": "EPL_Presentation_Short_Notes.md",
            "EPL_Presentation_Short_Rules.csv": "EPL_Presentation_Short_Rules.csv"}
        previous = json.loads((latest / "short_manifest.json").read_text()) if (latest / "short_manifest.json").exists() else {"copies": {}}
        for target in names.values():
            if (latest / target).exists() and (target not in previous["copies"] or sha(latest / target) != previous["copies"][target]["sha256"]):
                raise ValueError("A short latest file was edited locally")
        copied = {}
        for source, target in names.items():
            shutil.copyfile(out / source, latest / target)
            copied[target] = {"source": (out / source).relative_to(ROOT).as_posix(), "sha256": sha(latest / target)}
        jsave(latest / "short_manifest.json", {"canonical_run": out.relative_to(ROOT).as_posix(), "copies": copied})
    return {"output": str(out), "main_slides": 6, "appendix_slides": len(slides) - 6, "audit": checked}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--draft", action="store_true")
    parser.add_argument("--publish", action="store_true")
    args = parser.parse_args()
    print(json.dumps(build(args.output, draft=args.draft, publish=args.publish), indent=2))
