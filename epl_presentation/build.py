"""Create an editable, source-linked presentation of the completed EPL project."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter
import numpy as np
import pandas as pd

from epl_modeling.metrics import classification_metrics, encode_results

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = Path(__file__).parent
STUDY = Path("epl_player_models/results/20261020_player_models_review")
LAB = Path("epl_strategy_lab/results/20261015T040052Z_100k84")
VALIDATION = Path("epl_strategy_validation/results/20261015_temporal_selection")
EXECUTION = Path("epl_execution/results/20261015_quote_sensitivity")
PROSPECTIVE = Path("epl_prospective/results/20261020_first_outcomes")
TEAL, NAVY, AMBER, MUTED, RED, BLUE = "0D897D", "11243A", "D18B18", "536578", "B44949", "4376AC"


def sha(path):
    value = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def jsave(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False, default=str) + "\n", encoding="utf-8")


def money(value):
    return f"{float(value):,.0f}"


def pct(value):
    return f"{float(value):.2%}"


def dec(value, digits=4):
    return f"{float(value):.{digits}f}"


def text(x, y, w, h, value, size=20, color=NAVY, bold=False, **extra):
    return dict(type="text", x=x, y=y, w=w, h=h, text=str(value), size=size, color=color, bold=bold, **extra)


def card(x, y, w, h, label, value, detail="", accent=TEAL):
    return dict(type="card", x=x, y=y, w=w, h=h, label=label, value=str(value), detail=detail, accent=accent)


def table(x, y, w, h, headers, rows, widths=None, font_size=17, header_size=14, **extra):
    return dict(type="table", x=x, y=y, w=w, h=h, headers=headers, rows=rows,
        widths=widths or [1 / len(headers)] * len(headers), font_size=font_size, header_size=header_size, **extra)


def slide(title, subtitle, elements, *, kicker="EPL | IMPLEMENTED RESULTS", notes="", sources=None, appendix=False):
    return dict(title=title, kicker=kicker, subtitle=subtitle, elements=elements, notes=notes,
        sources=[str(p) for p in sources or []], appendix=appendix)


def load():
    model_research = json.loads((PACKAGE / "research_models.json").read_text(encoding="utf-8"))
    trading_research = json.loads((PACKAGE / "research_trading.json").read_text(encoding="utf-8"))
    audit_research = json.loads((PACKAGE / "research_audit.json").read_text(encoding="utf-8"))
    catalog = json.loads((ROOT / STUDY / "all_strategy_catalog.json").read_text())
    single = pd.concat([pd.read_parquet(ROOT / LAB / "metrics.parquet"),
        pd.read_parquet(ROOT / STUDY / "metrics_single.parquet")], ignore_index=True).set_index("strategy_id")
    continuous = pd.concat([pd.read_parquet(ROOT / VALIDATION / "metrics_continuous.parquet"),
        pd.read_parquet(ROOT / STUDY / "metrics_continuous.parquet")], ignore_index=True).set_index("strategy_id")
    graphs = {scope: pd.read_csv(ROOT / STUDY / name, parse_dates=["match_date"])
        for scope, name in (("single", "graph_equity_2025_all.csv"), ("continuous", "graph_equity_continuous_all.csv"))}
    assert len(catalog) == len(single) == 116 and len(continuous) == 88
    for scope, metrics in (("single", single), ("continuous", continuous)):
        graph = graphs[scope]
        assert set(graph.strategy_id) == set(metrics.index)
        assert not graph.duplicated(["strategy_id", "match_date"]).any()
        ends = graph.sort_values("match_date").groupby("strategy_id").tail(1).set_index("strategy_id").reindex(metrics.index)
        assert np.allclose(ends.end_bankroll, metrics.final_capital_sum_units, atol=1e-6, rtol=0)
        anchors = graph.loc[graph.is_initial]
        assert len(anchors) == len(metrics) and anchors.end_bankroll.eq(100000).all()
    old = pd.read_parquet(ROOT / "epl_modeling/ablation_results/predictions.parquet")
    new = pd.read_parquet(ROOT / STUDY / "predictions.parquet")
    ranking = pd.DataFrame(model_research["ranking_by_pooled_log_loss"])
    for row in ranking.itertuples():
        if row.model_key.startswith("pm_"):
            part = new.loc[new.model_key.eq(row.model_key)]
        else:
            part = old.loc[old.feature_group.eq(row.feature_group) & old.model_type.eq(row.model_type)]
        assert len(part) == 1470 and not part.match_id.duplicated().any()
        scores = classification_metrics(encode_results(part.result), part[["p_H", "p_D", "p_A"]])
        for key in ("accuracy", "log_loss", "brier_score", "classwise_ece_10"):
            assert np.isclose(scores[key], getattr(row, key), atol=1e-12, rtol=0)
    assert ranking.iloc[0].model_key == "baseline_market_only"
    assert ranking.loc[ranking.learned_predictor].iloc[0].model_key == "residual_team_players"
    assert single.final_capital_sum_units.idxmax() == "P028"
    assert continuous.final_capital_sum_units.idxmax() == "S060"
    return dict(models=model_research, trading=trading_research, audit=audit_research,
        catalog=catalog, single=single, continuous=continuous, graphs=graphs, ranking=ranking)


def graph_accounts(data, scope, output):
    graph = data["graphs"][scope]
    leader = "P028" if scope == "single" else "S060"
    colors = {leader: "#0D897D", "S033": "#4376AC", "S017": "#735AA6", "P009": "#D18B18"}
    if scope == "continuous":
        colors["P028"] = "#B44949"
    plt.rcParams.update({"font.family": "Arial", "font.size": 13})
    fig, ax = plt.subplots(figsize=(14.7, 4.95), facecolor="#F7F8FA")
    ax.set_facecolor("#F7F8FA")
    for key, part in graph.groupby("strategy_id", sort=True):
        if key in colors:
            continue
        part = part.sort_values("match_date")
        line, = ax.step(part.match_date, part.end_bankroll, where="post", color="#A5AFB8" if key.startswith("S") else "#D6B780",
            linewidth=.7, alpha=.65, zorder=1)
        line.set_gid("strategy-" + key)
    ax.axhline(100000, color="#74818E", linewidth=.8, linestyle="--", alpha=.6)
    for key, color in colors.items():
        part = graph.loc[graph.strategy_id.eq(key)].sort_values("match_date")
        line, = ax.step(part.match_date, part.end_bankroll, where="post", color=color, linewidth=2.1, zorder=3)
        line.set_gid("strategy-" + key)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value / 1000:,.0f}K"))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2 if scope == "single" else 8))
    ax.set_xlabel("Date", labelpad=8)
    ax.set_ylabel("Account balance (monetary units)", labelpad=8)
    ax.set_ylim(0, graph.end_bankroll.max() * 1.08)
    ax.set_xlim(graph.match_date.min(), graph.match_date.max())
    ax.grid(axis="y", color="#D7DFE5", linewidth=.6)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color("#A5AFB8"); ax.spines["left"].set_color("#A5AFB8")
    handles = [Line2D([0], [0], color="#A5AFB8", label="Other original rules"),
        Line2D([0], [0], color="#D6B780", label="Other new-study rules")]
    labels = {leader: leader + " | capital leader", "S033": "S033 | simplest", "S017": "S017 | team data", "P009": "P009 | player form"}
    if scope == "continuous":
        labels["P028"] = "P028 | 2025/26 leader"
    handles += [Line2D([0], [0], color=color, linewidth=2.1, label=labels[key]) for key, color in colors.items()]
    fig.legend(handles=handles, loc="lower center", ncol=4, frameon=False, fontsize=10.5, bbox_to_anchor=(.52, -.005))
    fig.subplots_adjust(left=.09, right=.99, top=.97, bottom=.24)
    stem = "all_accounts_2025" if scope == "single" else "all_accounts_continuous"
    for suffix in ("png", "svg"):
        fig.savefig(output / f"{stem}.{suffix}", dpi=200, facecolor=fig.get_facecolor())
    plt.close(fig)
    return {"path": str(output / f"{stem}.png"), "strategy_count": int(graph.strategy_id.nunique()),
        "points": len(graph), "initial_capital": 100000, "all_ids_plotted": sorted(graph.strategy_id.unique())}


def profile_slide(data, key, title, subtitle, description, interpretation, sid):
    profile = data["models"]["profiles"][key]
    scores, account = profile["metrics"], data["continuous"].loc[sid]
    values = [("Classification accuracy", pct(scores["accuracy"])), ("Log loss | lower is better", dec(scores["log_loss"])),
        ("Brier score | lower is better", dec(scores["brier_score"])), ("Classwise ECE | 10 bins", pct(scores["classwise_ece_10"]))]
    elements = [card(.65 + 3.78 * i, 2.05, 3.45, 1.5, label, value, "1,470 common fixtures") for i, (label, value) in enumerate(values)]
    elements += [text(.65, 3.92, 7.0, .4, "WHAT THE MODEL DOES", 15, TEAL, True),
        text(.65, 4.43, 7.0, 2.25, description, 20),
        text(8.05, 3.92, 7.25, .4, f"TRADING WRAPPER {sid} | CONTINUOUS FOUR SEASONS", 14, TEAL, True),
        table(8.05, 4.48, 7.25, 2.72, ["Trading statistic", "Recorded result"],
            [["Ending account", money(account.final_capital_sum_units)], ["Return on starting 100K", pct(account.return_on_initial_capital)],
             ["Hit ratio / trade frequency", pct(account.hit_ratio) + " / " + pct(account.trading_frequency)],
             ["ROI on total stakes", pct(account.roi)], ["Maximum drawdown", pct(account.max_drawdown)]], [.61, .39], 17),
        text(.65, 7.35, 14.6, .73, interpretation, 18, MUTED)]
    return slide(title, subtitle, elements, kicker="MODEL PROFILE | SAME 1,470 FIXTURES", sources=[scores["source"], VALIDATION / "metrics_continuous.parquet", STUDY / "metrics_continuous.parquet"],
        notes=profile["description"] + "\n\n" + interpretation + "\nThe trading result is separate from probability quality. "
        + sid + " takes the maximum model-implied edge above 5%, with flat requested stakes of 1,000, best archived quotes and date-start cash allocation. "
        "Hit ratio is a fraction of bets won. Classification accuracy is a fraction of all match outcomes correctly classified. "
        "All comparisons are retrospective. Full per-trade expected components and actual payoffs appear in the common-scope scorecard and workbook.")


def short_model(key):
    mapping = {"first_accuracy": "First-study SVM", "first_calibration": "First-study MLP", "logit_team_only": "Team logistic",
        "logit_team_xg": "Team+xG logistic", "logit_team_players": "Team+FPL logistic", "logit_combined": "Team+xG+FPL logistic",
        "residual_team_only": "Team market-residual", "residual_team_xg": "Team+xG residual", "residual_team_players": "Team+FPL residual",
        "residual_combined": "Team+xG+FPL residual", "baseline_class_frequency": "Class-frequency baseline",
        "baseline_market_only": "Raw market baseline", "baseline_market_temperature": "Calibrated market", "ensemble_logit4": "4-logistic mean",
        "ensemble_learned8": "8-learned mean", "ensemble_market_blend": "Combined-logistic/market mean"}
    if key in mapping:
        return mapping[key]
    if key.startswith("pm_"):
        return key.replace("pm_", "").replace("hist_boost", "HGB").replace("logistic", "Logistic").replace("team_player_squad", "team+full player").replace("player_squad", "player squad").replace("player_form", "player form").replace("team_control", "team control").replace("_", " ")
    return key


def rule_columns(row):
    if row.get("cash_only"):
        selection = "Cash; no admissible trade"
    elif row["selection_rule"] == "fixed_outcome":
        selection = "/".join(row["allowed_outcomes"]) + " in every fixture"
    elif row["selection_rule"] == "market_favorite":
        selection = "Highest raw market probability"
    elif row["selection_rule"] == "market_underdog":
        selection = "Lowest raw market probability"
    elif row["selection_rule"] == "model_favorite":
        selection = "Highest model probability; no edge filter"
    else:
        selection = "Max edge > " + pct(row["min_edge"])
    if row.get("allowed_outcomes") != list("HDA") and row["selection_rule"] != "fixed_outcome":
        selection += "; " + "/".join(row["allowed_outcomes"])
    if row.get("min_odds") is not None or row.get("max_odds") is not None:
        selection += "; odds " + str(row.get("min_odds") or "any") + "–" + str(row.get("max_odds") or "any")
    if row.get("consensus_min"):
        selection += f"; agree ≥{row['consensus_min']}/{len(row['consensus_model_keys'])}"
    if row["staking"] == "fixed":
        stake = "Flat " + money(row["fixed_stake"])
    elif row["staking"] == "dynamic_fraction":
        stake = pct(row["bankroll_fraction"]) + " of cash"
    else:
        stake = f"{row['kelly_fraction']:g} Kelly; cap {pct(row['max_bet_fraction'])}"
    if row.get("date_cap_fraction"):
        stake += "; date cap " + pct(row["date_cap_fraction"])
    return [row["strategy_id"], short_model(row["model_key"]), selection, stake, "Best" if row["odds_mode"] == "best" else "Bet365"]


def contents(data, charts):
    profiles = data["models"]["profiles"]
    simple, market, best = profiles["simplest"]["metrics"], profiles["strongest_benchmark"]["metrics"], profiles["best_learned"]["metrics"]
    single, continuous = data["single"], data["continuous"]
    sources_models = [Path("epl_modeling/ablation_results/predictions.parquet"), STUDY / "model_metrics_pooled.parquet"]
    sources_trade = [LAB / "metrics.parquet", VALIDATION / "metrics_continuous.parquet", STUDY / "metrics_single.parquet", STUDY / "metrics_continuous.parquet"]
    slides = []
    slides.append(slide("EPL: what we have implemented", "An end-to-end research system for match probabilities, archived-price trading and prospective evaluation.",
        [card(.65, 2.05, 4.65, 1.7, "DATA", "20 current clubs", "Team, xG and player histories"),
         card(5.66, 2.05, 4.65, 1.7, "PREDICTION", "19 model series", "16 learned predictors + 3 benchmarks"),
         card(10.67, 2.05, 4.65, 1.7, "TRADING", "116 accounts", "Each starts at 100,000 in 2025/26"),
         text(.65, 4.3, 14.6, .5, "What is already built", 23, NAVY, True),
         text(.65, 5.0, 7.0, 2.35, "Source captures and identity checks\nStrictly lagged team and player features\nChronological fitting and calibration", 23),
         text(8.05, 5.0, 7.15, 2.35, "Trading, cash and risk accounting\nComplete money curves and strategy catalog\nTimestamped forecasts, audits and reports", 23),
         text(.65, 7.75, 14.6, .4, "Presentation: 21 October 2026  |  Completed evidence through the 20 October snapshot  |  EPL component", 15, MUTED)],
        sources=[STUDY / "study_status.json", PROSPECTIVE / "prospective_status.json"],
        notes="This opening describes the implemented work, not the original proposal. The 19 series are the 11 earlier rolling comparisons plus eight new player-study variants, all sharing the same four-year evaluation population. The first-study SVM/MLP are preserved in the 2025 account comparison but lack the same earlier rolling history. Strategies are combinations of model, selection, prices and stakes; 116 does not mean 116 different algorithms. There are no claimed executed real-money trades."))
    slides.append(slide("The data behind the implemented system", "Current-club scope; full historical opponents remain context. Snapshot completed matches run through 19 October 2026.",
        [card(.65, 2.05, 4.65, 1.65, "HISTORICAL PLAYER RECORDS", "253,509", "Player-match rows, 2016/17–2025/26"),
         card(5.66, 2.05, 4.65, 1.65, "CURRENT PLAYER HISTORY", "4,551", "Rows from 70 completed fixtures"),
         card(10.67, 2.05, 4.65, 1.65, "CURRENT PLAYER SUMMARIES", "668", "Full FPL snapshot, 20 October"),
         table(.65, 4.15, 14.67, 3.15, ["Source block", "Implemented use", "Timing boundary"],
            [["Football-Data + bookmaker panel", "Results, team form, individual-book prices", "Strictly earlier features; quote clocks unverified"],
             ["Understat", "Team expected-goals history", "Earlier completed games"],
             ["FPL archives + current FPL", "Player form, squad profiles and projected XI", "Earlier same-season fixture slots only"]], [.24, .36, .40], 19),
         text(.65, 7.55, 14.6, .55, "Other acquired sources are preserved in the data inventory; this deck describes the inputs actually used in the models.", 17, MUTED)],
        sources=[STUDY / "study_status.json", STUDY / "model_catalog.json", PROSPECTIVE / "prospective_status.json"],
        notes="The new loader reconciles whole-league historical player records to exact fixture sides; the historical membership is not a present-day roster assignment. Each season contains 20 clubs and 380 native fixtures. Current 2026/27 records are used only for lagged future features, never model fitting. Historical opposition is retained so relegated teams are not mislabeled as current clubs. The current snapshot contains 668 player summaries and 70 completed fixtures. Some historical role metadata are season-fixed proxies with unverified publication times."))
    steps = [("1  Lagged inputs", "Team form\nxG\nPlayer histories"), ("2  H / D / A", "Regularized models\nSeparate calibration\nSaved probabilities"),
             ("3  Trading rule", "Outcome and edge\nPrice panel\nStake request"), ("4  Account replay", "Date-start cash\nJoint allocation\nSettlement and risk")]
    elements = []
    for i, (heading, body) in enumerate(steps):
        elements += [dict(type="rect", x=.65 + 3.78 * i, y=2.2, w=3.45, h=3.3, fill="FFFFFF", line="D8E0E7"),
            text(.9 + 3.78 * i, 2.55, 2.95, .5, heading, 20, TEAL, True),
            text(.9 + 3.78 * i, 3.35, 2.95, 1.65, body, 21)]
    elements += [text(.65, 6.05, 14.6, .65, "Model quality ≠ strategy profitability", 30, TEAL, True),
        text(.65, 7.02, 14.6, .8, "Accuracy and probability loss score forecasts. Hit ratio and money depend on the bets, prices and stake sizes actually replayed.", 22)]
    slides.append(slide("A prediction model is one part of a strategy", "The account graph combines model + outcome rule + prices + sizing; it does not compare algorithms in isolation.", elements,
        sources=[STUDY / "all_strategy_catalog.json", "epl_strategy/metrics.py"], notes="H/D/A denotes home win, draw and away win. Most value rules choose the maximum p×decimal-odds−1 above a fixed threshold, with deterministic H/D/A ties. Same-date requests use opening cash and are allocated before outcomes settle. Flat, cash-fraction and capped Kelly requests are distinct strategy configurations. This explains why the strongest probability model need not generate the largest account."))
    slides.append(slide("A chronological comparison on the same fixtures", "1,470 quoted matches in four evaluation seasons. Historical redesigns remain exploratory.",
        [table(.65, 2.1, 14.67, 3.7, ["Evaluate", "Initial training", "Tune, then include in refit", "Calibrate", "Matches"],
            [["2022/23", "2016/17–2019/20", "2020/21", "2021/22", "368"],
             ["2023/24", "2016/17–2020/21", "2021/22", "2022/23", "360"],
             ["2024/25", "2016/17–2021/22", "2022/23", "2023/24", "368"],
             ["2025/26", "2016/17–2022/23", "2023/24", "2024/25", "374"]], [.14, .28, .28, .17, .13], 20),
         text(.65, 6.23, 7.1, 1.4, "Fit preprocessing only on permitted fitting data. Freeze coefficients and calibration within each evaluation season.", 20),
         text(8.1, 6.23, 7.1, 1.4, "Every comparable model sees the same evaluation fixtures. Earlier games may update later lagged inputs.", 20),
         text(.65, 7.83, 14.6, .35, "Repeatedly inspected history is not a new untouched test. The current-club cohort also creates selection limitations.", 16, RED)],
        sources=["epl_modeling/ABLATION_PROTOCOL.md", "epl_player_models/PROTOCOL.md"],
        notes="Tune one of three fixed regularization or tree-leaf settings on the earlier tuning season, refit on training plus tuning, and fit one scalar temperature on the separate calibration season. No evaluation outcomes enter that fold's fit. The cohort comprises matches involving at least one saved current 2026/27 club, rather than every historical EPL fixture. A chronological boundary protects a fit, but cannot erase the fact these historical results have already been examined."))
    comparison_keys = ["strongest_benchmark", "best_learned", "team", "player", "simplest"]
    display_names = ["Raw Bet365 market benchmark", "Best learned: market residual + team/FPL", "Team logistic regression", "Player-form logistic regression", "Class-frequency baseline"]
    rows = []
    for key, name in zip(comparison_keys, display_names):
        row = profiles[key]["metrics"]
        rows.append([name, pct(row["accuracy"]), dec(row["log_loss"]), dec(row["brier_score"]), pct(row["classwise_ece_10"])])
    slides.append(slide("The strongest learned predictor still trails the market", "Observed pooled probability scores on the same 1,470 fixtures; lower log loss and Brier are better.",
        [table(.65, 2.15, 14.67, 3.9, ["Predictor", "Accuracy", "Log loss", "Brier", "ECE 10"], rows, [.44, .14, .14, .14, .14], 19),
         text(.65, 6.48, 14.6, .6, "Best learned = market residual with team data and seven FPL aggregates.", 25, TEAL, True),
         text(.65, 7.3, 14.6, .75, "It uses bookmaker probabilities as an input. Its small historical changes do not establish incremental value over the market.", 20, MUTED)],
        sources=sources_models, notes="Best means minimum observed pooled log loss among the 16 learned predictors with comparable four-year records. There are 19 series when the three baselines are included. Raw normalized inverse Bet365 odds are the strongest benchmark: log loss .96616994. The best learned model is the earlier team+player market-residual variant: .96929380. Its paired descriptive interval versus the raw market includes zero; there is no fresh or multiplicity-adjusted superiority result. ECE is classwise calibration error at ten bins and does not measure forecast resolution."))
    slides.append(profile_slide(data, "best_learned", "Best learned predictor: market residual + team/FPL", "28 historical inputs + bookmaker-probability offset; regularized home/draw adjustments, then temperature calibration.",
        "Start from normalized inverse Bet365 odds.\nLearn regularized adjustments from team form and seven rolling FPL aggregates.\nKeep training, tuning and calibration chronological.",
        "The raw market has lower pooled log loss (0.9662). S029's positive archived return is not proof of a validated predictive edge.", "S029"))
    prior = profiles["simplest"]["season_priors"]["2025-26"]
    slides.append(profile_slide(data, "simplest", "Simplest model: historical class frequencies", "No match features, team identity or odds input. The same three probabilities are used for every match within an outer season.",
        "Count home wins, draws and away wins in the fitting block. Use those fractions as the forecast.\n2025/26 probabilities:\nH " + pct(prior["p_H"]) + "   D " + pct(prior["p_D"]) + "   A " + pct(prior["p_A"]),
        "Low ECE alone does not imply useful match discrimination. S033 applies an edge rule to these probabilities; it is not an always-home policy.", "S033"))
    slides.append(profile_slide(data, "team", "Team-data model: regularized logistic regression", "21 inputs: nine team-performance measures, four context flags and eight shared source-coverage controls.",
        "Use earlier goals, shots on target, corners, points, rest and prior-season win rates.\nMedian imputation, indicators and scaling are fitted in the permitted block.\nNo player-performance or odds predictors.",
        "S017 has a positive historical capital return, with a 40.35% drawdown. The probability model still trails the raw market benchmark.", "S017"))
    slides.append(profile_slide(data, "player", "Player-only model: recent FPL form", "96 inputs: 90 player-performance aggregates and six coverage controls. No team-strength, position or odds predictors.",
        "Aggregate 12 FPL measures plus player/minute counts over the previous 5 and 10 fixture slots.\nRepresent home, away and their differences.\nMissing history remains visible; target appearances are excluded.",
        "The matched team-control log loss is 0.9925 versus 1.0218 here. P009 exhausts its four-season cash; that path includes no borrowing.", "P009"))
    new_scores = pd.read_parquet(ROOT / STUDY / "model_metrics_pooled.parquet")
    rows = []
    for group, label, count in (("team_control", "Matched team control", 19), ("player_form", "Player form", 96),
                               ("player_squad", "Player form + XI + depth", 222), ("team_player_squad", "Team + full player block", 235)):
        part = new_scores.loc[new_scores.feature_group.eq(group)].set_index("model_type")
        rows.append([label, str(count), dec(part.loc["logistic", "log_loss"]), dec(part.loc["hist_boost", "log_loss"])])
    slides.append(slide("Richer player features did not improve these models", "Four fixed feature groups, each crossed with logistic regression and histogram gradient boosting.",
        [table(.65, 2.15, 14.67, 3.4, ["Feature group", "Inputs", "Logistic log loss", "Boosting log loss"], rows, [.43, .13, .22, .22], 21),
         card(.65, 5.98, 4.65, 1.55, "POOLED COMPARISON", "0 / 6 improve", "Player-based variants vs matched controls", RED),
         card(5.66, 5.98, 4.65, 1.55, "NEW STRATEGY STUDY", "0 / 32 profitable", "Continuous four-season accounts", RED),
         card(10.67, 5.98, 4.65, 1.55, "CASH EXHAUSTION", "11 / 32", "New accounts reach zero", RED),
         text(.65, 7.66, 14.6, .56, "Projected XI is a past-minute proxy, not a confirmed lineup or availability feed.\nSome archived position proxies have unverified publication times.", 15, MUTED)],
        sources=[STUDY / "model_metrics_pooled.parquet", STUDY / "metrics_continuous.parquet", "epl_player_models/PROTOCOL.md"],
        notes="The richer player squad block has 222 inputs, including fixed 1-GK/4-DEF/4-MID/2-FWD selections based on prior minutes. The combined block has 235. All six player-based variants have worse pooled log loss than their newly fitted same-algorithm team control. The primary population is unchanged; a better-supported-history sensitivity does not reverse the pooled ranking. This result concerns these particular representations and models, not a general claim that player information has no value. The 32 new rules include the matched team controls as well as player models."))
    for scope, title, subtitle in (("single", "Money progression: all 116 strategy accounts", "2025/26 | Same 374 quoted fixtures | Every account begins at 100,000"),
                                   ("continuous", "Money progression: all 88 comparable accounts", "2022/23–2025/26 | Same 1,470 fixtures | Continuous cash with no annual resets")):
        graph = charts[scope]
        count = graph["strategy_count"]
        summary = data["trading"]["summaries"]["single_2025_26_all" if scope == "single" else "continuous_2022_26_all"]
        html = "all_strategies_2025_100k.html" if scope == "single" else "all_strategies_continuous_100k.html"
        extra = "The 28 first-study rules without comparable earlier predictions are excluded from the four-year chart." if scope == "continuous" else "All 84 original rules and all 32 new rules are included. Coincident cash paths overlap."
        flat = f"   /   {summary['zero_profit_count']} flat/cash" if summary["zero_profit_count"] else ""
        slides.append(slide(title, subtitle,
            [text(.65, 2.0, 14.6, .45, f"{summary['positive_profit_count']} profitable   /   {summary['negative_profit_count']} losing" + flat + f"   /   {summary['bankrupt_count']} reach zero", 20, NAVY, True),
             dict(type="image", x=.65, y=2.58, w=14.7, h=4.95, path=graph["path"]),
             text(.65, 7.75, 11.9, .46, extra, 15.5, MUTED),
             text(12.75, 7.72, 2.55, .48, "Open interactive HTML", 14, TEAL, True, url=html)],
            sources=[STUDY / ("graph_equity_2025_all.csv" if scope == "single" else "graph_equity_continuous_all.csv")],
            notes=f"Every one of the {count} account IDs is plotted using its saved curve, including all initial-capital anchors. The chart counts distinct strategies, not independent algorithms. Each account begins at 100000 generic monetary units; the accounts are alternatives, not added together. Time is horizontal and account balance is vertical. All graph endpoints match the source metrics. Use the adjacent offline HTML to hover individual strategies or control their visibility. " + extra + " The full strategy appendix maps every ID. These are archived-price hypothetical replays, with unverified quote availability and no real-money execution claim."))
    leader = continuous.loc["S060"]
    rows = [["Bets / priced fixtures", f"{int(leader.bet_count):,} / 1,470"], ["Hit ratio / trading frequency", pct(leader.hit_ratio) + " / " + pct(leader.trading_frequency)],
            ["Expected gain / loss per trade", dec(leader.expected_gain_per_trade_units, 2) + " / " + dec(leader.expected_loss_per_trade_units, 2)],
            ["Realized winning gain / losing loss", dec(leader.avg_winning_gain_units, 2) + " / " + dec(leader.avg_losing_loss_units, 2)],
            ["ROI on total stakes", pct(leader.roi)], ["Maximum drawdown", pct(leader.max_drawdown)]]
    slides.append(slide("Highest four-season ending capital: S060", "A historical capital leader, selected descriptively after comparing the 88 compatible accounts.",
        [card(.65, 2.05, 4.65, 1.55, "ENDING ACCOUNT", money(leader.final_capital_sum_units), "Initial 100,000"),
         card(5.66, 2.05, 4.65, 1.55, "PROFIT", money(leader.profit), "Four seasons without deposits"),
         card(10.67, 2.05, 4.65, 1.55, "RETURN ON STARTING CASH", pct(leader.return_on_initial_capital), "Not the ROI on turnover"),
         text(.65, 4.0, 7.0, 2.55, "Market-residual model with team, xG and FPL inputs.\nChoose maximum edge above 5%.\nQuarter Kelly; 2% per-bet cap.\n10% date-level cash budget; best archived quotes.", 21),
         table(8.05, 4.0, 7.25, 3.35, ["Trading statistic", "Recorded result"], rows, [.57, .43], 17),
         text(.65, 7.75, 14.6, .4, "Its recorded ROI confidence interval crosses zero. The historical ranking does not select a validated live policy.", 16, RED)],
        sources=sources_trade, notes="S060 uses the combined market-residual probability series, which is not the best pooled probability-score variant. It adds xG to team and legacy FPL aggregates and uses Bet365 market probabilities as an offset. The strategy changes both staking and total date exposure relative to flat stake variants. Its positive capital result is an observed path, conditional on archived best quotes, and is not a multiplicity-adjusted discovery. A conditional date-bootstrap ROI interval crosses zero and does not include full model-refitting or strategy-selection uncertainty."))
    winner, long = single.loc["P028"], continuous.loc["P028"]
    slides.append(slide("A one-season winner can fail over four seasons", "P028: team + full player block, logistic regression, Bet365 reference prices, quarter Kelly capped at 2% per bet.",
        [card(.65, 2.1, 7.05, 1.8, "2025/26 ENDING ACCOUNT", money(winner.final_capital_sum_units), pct(winner.return_on_initial_capital) + " return on starting cash", TEAL),
         card(8.05, 2.1, 7.25, 1.8, "CONTINUOUS FOUR-SEASON ACCOUNT", money(long.final_capital_sum_units), pct(long.return_on_initial_capital) + " return on starting cash", RED),
         table(.65, 4.35, 14.67, 2.55, ["Scope", "Bets", "Hit ratio", "Trade frequency", "Stake ROI", "Max drawdown"],
             [["2025/26", str(int(winner.bet_count)), pct(winner.hit_ratio), pct(winner.trading_frequency), pct(winner.roi), pct(winner.max_drawdown)],
              ["Continuous four seasons", str(int(long.bet_count)), pct(long.hit_ratio), pct(long.trading_frequency), pct(long.roi), pct(long.max_drawdown)]], [.28, .10, .14, .17, .14, .17], 20),
         text(.65, 7.4, 14.6, .65, "The model's pooled accuracy is 50.95% and log loss is 1.0161. A profitable slice does not establish better forecasting.", 20, MUTED)],
        sources=[STUDY / "metrics_single.parquet", STUDY / "metrics_continuous.parquet", STUDY / "model_metrics_pooled.parquet"],
        notes="P028 is the highest ending 2025/26 account among all 116, including the old strategies. Its continuous account contains the same 2025 season after three prior seasons and begins only once at 100000; it does not reset at the start of 2025. Its annual diagnostic starts a separate account at 100000 and must not be spliced into the continuous path. The underlying logistic model uses 235 inputs. All new player-study continuous paths lose, even though eight new-study paths are positive in 2025 alone. This is a concrete reason to show both time horizons."))
    rows = []
    for sid, name in (("S029", "Best learned predictor"), ("S033", "Simplest predictor"), ("S017", "Team data"), ("P009", "Player form"), ("S060", "4-year capital leader"), ("P028", "2025 capital leader")):
        r = continuous.loc[sid]
        rows.append([sid + " | " + name, money(r.final_capital_sum_units), pct(r.hit_ratio), pct(r.trading_frequency),
            dec(r.expected_gain_per_trade_units, 2), dec(r.expected_loss_per_trade_units, 2), pct(r.roi), pct(r.max_drawdown)])
    slides.append(slide("The same-scope trading scorecard", "All rows: continuous four seasons, 1,470 priced opportunities, one initial 100,000 account.",
        [table(.65, 2.1, 14.67, 4.6, ["Strategy / role", "Final money", "Hit ratio", "Trade freq.", "Expected gain / trade", "Expected loss / trade", "Stake ROI", "Max DD"],
               rows, [.25, .13, .10, .10, .12, .12, .09, .09], 17),
         text(.65, 7.1, 14.6, 1.0, "Expected gain/loss use the model's probabilities and the recorded stakes. They are not average realized wins/losses.\nFull observed payoffs, uncertainty and all 116 / 88 account metrics are in the companion workbook.", 19, MUTED)],
        sources=sources_trade, notes="The scorecard intentionally aligns all six featured policies to the same four-season scope. Expected gain per trade averages p times stake times odds minus one; expected loss averages one minus p times stake. These may look favorable even when actual trading loses because they rely on the model's probabilities, especially on selected high-edge bets. ROI divides net profit by turnover and is not return on starting capital. Frequency divides actual placed bets by all 1470 common priced opportunities; bankruptcy can reduce realized frequency. The companion workbook also preserves average observed winning/losing payoffs and the confidence intervals."))
    execution = data["trading"]["execution_sensitivity"]["selected"]["S060"]
    ref = next(row for row in execution if row["execution_mode"] == "reference_replay")
    fixed = next(row for row in execution if row["execution_mode"] == "fixed_exposure_reference")
    slides.append(slide("Historical profit depends on prices and path assumptions", "S060 illustrates why a quote replay and a payout-only repricing answer different questions.",
        [card(.65, 2.12, 4.65, 1.75, "ORIGINAL BEST-QUOTE PROFIT", money(leader.profit), "Saved choices and cash path"),
         card(5.66, 2.12, 4.65, 1.75, "BET365 POLICY REPLAY PROFIT", money(ref["profit"]), "Recompute selection and sizing"),
         card(10.67, 2.12, 4.65, 1.75, "FIXED-EXPOSURE REPRICING", money(fixed["profit"]), "Keep original bets/stakes; change payouts", RED),
         text(.65, 4.48, 7.05, 2.6, "Best quotes may come from different books.\nCapture clocks and availability are unverified.\nNo stake limits or observed transaction costs are modeled.", 22),
         text(8.05, 4.48, 7.25, 2.6, "Selections and sizing react to odds.\nCash exposure changes the later path.\nWhole-date bootstrap intervals do not remove model or strategy selection uncertainty.", 22),
         text(.65, 7.65, 14.6, .5, "These archived-price paths do not demonstrate executable fills, arbitrage or prospective investment returns.", 18, RED)],
        sources=[EXECUTION / "metrics_continuous.parquet", EXECUTION / "quote_summary.json", "epl_execution/PROTOCOL.md"],
        notes="Do not interpret the three displayed profits as a pure causal price effect. The full Bet365 replay computes model edge and requests again, so choices, bet count and cash sizes can differ. Fixed-exposure repricing keeps original selections and stakes and is a shadow comparison; some such paths in the wider study are unfunded, with normal capital and risk metrics withheld. This slide reports its profit only. Quote-time uncertainty also prevents a verified closing-line-value claim. No new fee scenario or outcome-based filter is chosen here."))
    slides.append(slide("A prospective pipeline exists; trading P&L does not", "Status of the saved 20 October snapshot. October 23–25 targets have not been scored in this presentation.",
        [card(.65, 2.1, 4.65, 1.8, "RESOLVED FIXTURES", "10", "40 predictions from four frozen models"),
         card(5.66, 2.1, 4.65, 1.8, "NEXT COHORT", "120 pending", "40 earlier-model + 80 new-model forecasts"),
         card(10.67, 2.1, 4.65, 1.8, "RECORDED PROSPECTIVE TRADES", "0", "No valid pre-kickoff quote/stake ledger", AMBER),
         text(.65, 4.52, 7.0, 2.4, "All four earlier models scored 6 / 10.\n60% accuracy; 95% Wilson interval:\n31.27%–83.18%.\nNo winner was selected.", 23),
         text(8.05, 4.52, 7.2, 2.4, "All 120 pending predictions refer to the same ten upcoming fixtures.\nThe reviewed export copies the same 80 new-model records; it adds no forecasts.", 23),
         text(.65, 7.65, 14.6, .5, "Hash-chained records retain creation times, inputs and model hashes. Missing prices mean no prospective ROI or wealth graph.", 18, MUTED)],
        sources=[PROSPECTIVE / "prospective_status.json", PROSPECTIVE / "model_scores.csv", STUDY / "forecast_release.json"],
        notes="The first prospective result set has ten independent fixtures, not forty independent observations. The four models produce correlated predictions on the same matches, all with six correct classifications. The 95% Wilson interval on six out of ten is approximately .3127 to .8318. The pending pool contains 40 earlier-model records and 80 new-model records for the same October 23–25 fixtures: 120 unique forecasts, but ten targets. The original and reviewed player-study ledgers are byte-identical copies and must never be counted as two releases. There are 160 total unique saved forecasts across resolved and pending cohorts. Later archived prices cannot manufacture pre-match trades."))
    slides.append(slide("What the implemented results support", "A reproducible research and forecasting system, with clear negative as well as positive findings.",
        [card(.65, 2.15, 4.65, 1.55, "PREDICTION", "Market baseline", "Lowest pooled log loss and Brier"),
         card(5.66, 2.15, 4.65, 1.55, "PLAYER EXPANSION", "No improvement", "All six variants trail matched controls", AMBER),
         card(10.67, 2.15, 4.65, 1.55, "TRADING", "Leaders differ", "Probability loss and capital are distinct"),
         text(.65, 4.5, 14.6, .5, "The next valid evidence is already defined", 26, TEAL, True),
         text(.65, 5.35, 14.6, 1.5, "Evaluate the fixed pending forecast cohorts as their results arrive.\nCapture valid pre-kickoff quotes before assessing prospective trading.\nPreserve losing variants and the original information boundaries.", 25),
         text(.65, 7.55, 14.6, .55, "The following slides are backup material: metric definitions, provenance and the complete 116-strategy catalog.", 18, MUTED)],
        sources=[STUDY / "independent_audit.json", "epl_modeling/ablation_results/ABLATION_RESULTS.md"],
        notes="The contribution is the implemented pipeline and auditable comparisons, not a claim to have found a dependable betting edge. Richer player inputs are not useful in these tested representations; that does not imply all player information is unhelpful. All historical winners remain descriptive and conditional on replay assumptions. The next cohort already has immutable predictions and is more informative than repeatedly revising models on the same historical outcomes. Backup slides retain the strategy definitions and metric interpretations for questions."))
    slides.append(slide("Backup | metric definitions", "All money values are generic monetary units. Cash accounts have no deposits or borrowing.",
        [table(.65, 2.1, 14.67, 5.7, ["Metric", "Definition / denominator"],
            [["Prediction accuracy", "Correct most-likely H/D/A classifications / evaluated matches"],
             ["Hit ratio", "Winning settled bets / all settled bets"],
             ["Trade frequency", "Actual placed bets / common priced fixture opportunities"],
             ["Model expected gain per trade", "Mean of p × stake × (decimal odds − 1) over placed bets"],
             ["Model expected loss per trade", "Mean of (1 − p) × stake over placed bets"],
             ["Observed win / loss means", "Average net winning payoff / average losing stake, conditional on outcome"],
             ["Stake ROI / capital return", "Net profit / turnover; net profit / initial 100,000"],
             ["Maximum drawdown", "Largest peak-to-trough proportional decline in the account path"]], [.30, .70], 18)],
        appendix=True, sources=["epl_strategy/METHODOLOGY.md", "epl_strategy/metrics.py"],
        notes="Expected components use the selected model probability at the recorded allocated stake. They are unconditional components per trade, not the conditional mean payoff of wins or losses. No-trade conditional quantities remain undefined in the source workbook. Log loss is negative mean log probability assigned to the observed H/D/A outcome; Brier is the unscaled three-class squared error. ECE is classwise calibration error, bin-dependent and descriptive. Cash stays flat when no interest is modeled. Conditional date-bootstrap intervals are not a full model-and-search uncertainty analysis."))
    slides.append(slide("Backup | provenance and reproducibility", "All displayed numerical results come from saved project artifacts; this presentation fits no models and places no trades.",
        [table(.65, 2.1, 14.67, 4.6, ["Artifact block", "What to inspect"],
            [["epl_modeling/ablation_results", "Earlier rolling predictions, 11 variants and fitted models"],
             ["epl_player_models/results/20261020_player_models_review", "New model comparisons, all-116 / all-88 graph data, detailed accounts"],
             ["epl_strategy_validation / epl_execution", "Continuous cash replays, selection audit and quote sensitivity"],
             ["epl_prospective/results/20261020_first_outcomes", "First ten-game prospective evaluation and source cross-checks"],
             ["Presentation companion files", "All numerical tables, exact configurations, source hashes and speaker notes"]], [.42, .58], 18),
         text(.65, 6.92, 14.6, 1.0, "Protected previous exports and the user-edited data workbook remain unchanged.\nThe presentation audit reconciles scores, curve endpoints, ranking scopes and all 116 catalog IDs.", 21, MUTED)],
        appendix=True, sources=["reports/latest/manifest.json", STUDY / "manifest.json"],
        notes="The presentation source manifest hashes all consumed numerical artifacts, research evidence and presentation code. The project reports use reports/latest; the presentation uses presentations/latest. The underlying latest project report is not replaced by the slides. A separate immutable presentation run records source/output hashes. All complete configurations are in the workbook and notes. The user-edited epl_data/EPL_data_overview.xlsx is deliberately excluded from staging and remains byte-identical to the start of this task."))
    for start in range(0, len(data["catalog"]), 8):
        chunk = data["catalog"][start:start + 8]
        first, last = chunk[0]["strategy_id"], chunk[-1]["strategy_id"]
        slides.append(slide(f"Strategy appendix | {first}–{last}", "H / D / A = home / draw / away. Edge = p × decimal odds − 1. Full definitions and exact configurations are in speaker notes.",
            [table(.65, 2.0, 14.67, 5.85, ["ID", "Probability series", "Outcome / eligibility", "Requested stake / date cap", "Prices"],
                [rule_columns(row) for row in chunk], [.07, .25, .30, .28, .10], 14.5, header_size=13),
             text(.65, 8.0, 14.6, .25, "Jointly scale same-date requests to available opening cash. Best = archived best individual-book quote. Cash rules do not trade.", 13, MUTED)],
            appendix=True, kicker="COMPLETE STRATEGY CATALOG | BACKUP", sources=[STUDY / "all_strategy_catalog.json"],
            notes="Every listed configuration is the saved original definition. Cash and nontrading variants remain included. All strategies select at most one outcome per fixture. Ties use deterministic H/D/A ordering. Dynamic stake requests use date-start cash. All requests on a date are uniformly scaled to available cash and any declared date cap before settlement.\n\n" + "\n\n".join(row["strategy_id"] + ": " + row["description"] + "\nExact configuration:\n" + json.dumps(row, ensure_ascii=False, sort_keys=True) for row in chunk)))
    return slides


def consumed_sources():
    names = set()
    for path in (PACKAGE / "research_trading.json", PACKAGE / "research_audit.json"):
        info = json.loads(path.read_text())
        names.update(info.get("source_paths_sha256", info.get("source_sha256", {})))
    names.update(str(p) for p in [STUDY / "manifest.json", STUDY / "model_metrics_pooled.parquet", STUDY / "predictions.parquet",
        STUDY / "metrics_single.parquet", STUDY / "metrics_continuous.parquet", STUDY / "all_strategy_catalog.json",
        LAB / "metrics.parquet", VALIDATION / "metrics_continuous.parquet", "epl_modeling/ablation_results/predictions.parquet",
        "epl_modeling/ablation.py", "epl_strategy/metrics.py", "epl_modeling/market_residual.py",
        STUDY / "figures/all_strategies_2025_100k.html", STUDY / "figures/all_strategies_continuous_100k.html",
        "epl_live/forecasts.jsonl", "epl_live/outcomes.jsonl", STUDY / "forecasts.jsonl"])
    return sorted({ROOT / name for name in names} | {p for p in PACKAGE.glob("*") if p.suffix in {".py", ".json", ".md", ".txt"}})


def write_companions(data, slides, output):
    catalog_rows = [{**row, **{key: json.dumps(value, ensure_ascii=False) for key, value in row.items() if isinstance(value, (dict, list))}}
        for row in data["catalog"]]
    workbook = output / "EPL_Presentation_Data.xlsx"
    with pd.ExcelWriter(workbook, engine="xlsxwriter", engine_kwargs={"options": {"strings_to_urls": False}}) as writer:
        sheets = {"Read me": pd.DataFrame([{"Item": "Cutoff", "Meaning": "Completed evidence through the October 20 snapshot; presentation dated October 21, 2026."},
            {"Item": "Scopes", "Meaning": "116 accounts in 2025/26; 88 compatible continuous 2022/23-2025/26 accounts; 100,000 initial monetary units each."},
            {"Item": "Expected components", "Meaning": "Model-probability-weighted gain/loss at allocated stakes; different from observed average wins/losses."},
            {"Item": "Historical rankings", "Meaning": "Descriptive rankings on previously examined history; no selected or validated live trading policy."},
            {"Item": "Forecast count", "Meaning": "40 resolved and 120 pending predictions; 10 resolved and 10 pending distinct fixtures; no recorded prospective trades."}]),
            "All19 probability scores": data["ranking"], "All116 2025 metrics": data["single"].reset_index(),
            "All88 continuous metrics": data["continuous"].reset_index(), "Complete116 configurations": pd.DataFrame(catalog_rows),
            "Graph 2025": data["graphs"]["single"], "Graph continuous": data["graphs"]["continuous"]}
        book = writer.book
        header = book.add_format({"bold": True, "font_color": "white", "bg_color": "#11243A", "text_wrap": True})
        numeric = book.add_format({"num_format": "#,##0.0000"})
        percentage = book.add_format({"num_format": "0.00%"})
        percentages = {"accuracy", "classwise_ece_10", "classwise_ece_5", "classwise_ece_15", "hit_ratio", "trading_frequency", "roi",
            "expected_roi", "return_on_initial_capital", "max_drawdown", "price_coverage", "trade_rate_all_predictions", "active_date_fraction",
            "max_date_capital_exposure", "mean_date_capital_exposure", "avg_selected_probability", "empirical_break_even_hit_ratio"}
        for name, frame in sheets.items():
            clean = frame.copy()
            for col in clean:
                if clean[col].dtype == object:
                    clean[col] = clean[col].map(lambda value: json.dumps(value, ensure_ascii=False) if isinstance(value, (list, dict)) else value)
            clean.to_excel(writer, sheet_name=name, index=False, na_rep="NA", inf_rep="inf")
            sheet = writer.sheets[name]
            sheet.freeze_panes(1, 1); sheet.autofilter(0, 0, len(clean), len(clean.columns) - 1)
            for index, column in enumerate(clean.columns):
                base = str(column).removesuffix("_ci_low").removesuffix("_ci_high")
                sheet.set_column(index, index, 24, percentage if base in percentages else numeric)
            sheet.set_column(0, 0, 38); sheet.set_row(0, 42)
            sheet.write_row(0, 0, list(clean.columns), header)
            if name == "Read me":
                sheet.set_column(1, 1, 110)
    for scope in ("single", "continuous"):
        data[scope].reset_index().to_csv(output / ("strategy_metrics_" + scope + ".csv"), index=False)
    data["ranking"].to_csv(output / "model_probability_scores.csv", index=False)
    jsave(output / "presentation_content.json", slides)
    jsave(output / "complete_strategy_catalog.json", data["catalog"])
    notes = ["# EPL presentation | speaker notes", "", "21 October 2026. Evidence cutoff: the completed 20 October project snapshot.", ""]
    for i, s in enumerate(slides, 1):
        notes += [f"## Slide {i}: {s['title']}", "", s["subtitle"], "", s["notes"], "", "Sources:"]
        notes += ["- " + path for path in s["sources"]]
        notes += [""]
    (output / "EPL_Presentation_Speaker_Notes.md").write_text("\n".join(notes), encoding="utf-8")


def build(output, *, draft=False, publish=False):
    from .render import render
    output = Path(output).resolve()
    if output.exists() and not draft:
        raise ValueError("Use a new immutable presentation run directory")
    if not draft and (PACKAGE / "results").resolve() not in output.parents:
        raise ValueError("Final runs belong under epl_presentation/results")
    user_book = ROOT / "epl_data/EPL_data_overview.xlsx"
    user_sha = sha(user_book)
    paths = consumed_sources()
    before = {path: sha(path) for path in paths}
    output.mkdir(parents=True, exist_ok=True)
    print("Reading completed results and reconciling all common samples", flush=True)
    data = load()
    assets = output / "figures"; assets.mkdir(exist_ok=True)
    charts = {scope: graph_accounts(data, scope, assets) for scope in ("single", "continuous")}
    slides = contents(data, charts)
    write_companions(data, slides, output)
    for name in ("all_strategies_2025_100k.html", "all_strategies_continuous_100k.html"):
        shutil.copyfile(ROOT / STUDY / "figures" / name, output / name)
    print(f"Rendering {len(slides)} editable slides and the matching native PowerPoint PDF", flush=True)
    rendering = render(slides, output)
    from .audit import audit_presentation
    audit = audit_presentation(output, data=data)
    jsave(output / "independent_audit.json", audit)
    if sha(user_book) != user_sha or any(sha(path) != digest for path, digest in before.items()):
        raise AssertionError("A protected existing artifact changed")
    manifest = {"built_at_utc": datetime.now(timezone.utc).isoformat(), "presentation_date_new_york": "2026-10-21",
        "evidence_cutoff": "Completed project snapshot of 2026-10-20; no new fitting, forecasting or settlement",
        "source_sha256": {p.relative_to(ROOT).as_posix(): digest for p, digest in before.items()},
        "source_and_user_workbook_unchanged": True, "input_user_workbook_sha256": user_sha,
        "rendering": rendering, "slide_count": len(slides), "main_slides": 18, "appendix_slides": len(slides) - 18,
        "graphs": charts, "audit": audit, "output_sha256": {p.relative_to(output).as_posix(): sha(p) for p in sorted(output.rglob("*")) if p.is_file() and p.name != "manifest.json"}}
    jsave(output / "manifest.json", manifest)
    if publish:
        latest = ROOT / "presentations/latest"; latest.mkdir(parents=True, exist_ok=True)
        copied = {}
        for name in ("EPL_Project_Presentation.pptx", "EPL_Project_Presentation.pdf", "EPL_Presentation_Data.xlsx", "EPL_Presentation_Speaker_Notes.md", "all_strategies_2025_100k.html", "all_strategies_continuous_100k.html"):
            target = latest / name
            if target.exists():
                prior_path = latest / "manifest.json"
                if not prior_path.exists():
                    raise ValueError("An unregistered latest presentation exists")
                prior = json.loads(prior_path.read_text())["copies"]
                if name not in prior or sha(target) != prior[name]["sha256"]:
                    raise ValueError("A latest presentation file was edited locally")
            shutil.copyfile(output / name, target)
            copied[name] = {"source": (output / name).relative_to(ROOT).as_posix(), "sha256": sha(target)}
        jsave(latest / "manifest.json", {"canonical_run": output.relative_to(ROOT).as_posix(), "copies": copied})
    return {"output": str(output), "slides": len(slides), "audit": audit,
        "rendering": {"pdf_pages": rendering["pdf_pages"], "native_text_overflows": rendering["native_layout"]["text_overflow_count"]}}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--draft", action="store_true")
    parser.add_argument("--publish", action="store_true")
    args = parser.parse_args()
    print(json.dumps(build(args.output, draft=args.draft, publish=args.publish), indent=2))
