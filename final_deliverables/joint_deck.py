"""Concise joint NBA/EPL slides from the completed, source-linked evidence."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from epl_presentation.build import (
    load as load_epl_presentation_data, text, card, table, slide, pct, dec, money,
    TEAL, NAVY, MUTED, RED,
)
from epl_presentation.concise import contents as concise_epl_contents, ROLES, profile


def _image(path, x, y, w, h):
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(path)
    return dict(type="image", x=x, y=y, w=w, h=h, path=str(path.resolve()))


def _joint(spec, label):
    result = deepcopy(spec)
    result["kicker"] = label
    return result


def build_slides(data: dict, figures: Path) -> list[dict]:
    """Return 12 main slides, then NBA backup and the complete EPL appendix.

    Source-recorded NBA capital statistics are deliberately retained when the
    later fixed-parameter audit does not reproduce an SVM result. The NBA
    capital graph is consequently a saved-result bar chart, never a fabricated
    SVM wealth path. Existing EPL descriptions and configurations stay exact.
    """
    figures = Path(figures).resolve()
    nba, epl = data["nba"], data["epl"]
    epl_data = data.get("epl_presentation_data") or load_epl_presentation_data()
    slides = []
    slides.append(slide("Machine learning for sports betting", "NBA and English Premier League: accuracy, calibration and archived-price returns.",
        [text(.65, 2.15, 14.67, .75, "Aman Dhillon  •  Panagiotis Housos", 32, NAVY, True, align="center"),
         text(.65, 3.2, 14.67, .65, "Supervisor: Daniel Totouom-Tangho", 26, NAVY, False, align="center"),
         text(.65, 4.38, 14.67, .55, "Statistical Arbitrage  |  Final project  |  23 October 2026", 22, MUTED, align="center"),
         card(.65, 6.1, 4.65, 1.55, "PART 1", "Methodology", "The shared prediction-to-betting framework"),
         card(5.66, 6.1, 4.65, 1.55, "PART 2", "NBA results", "Aman Dhillon"),
         card(10.67, 6.1, 4.65, 1.55, "PART 3", "Premier League", "Panagiotis Housos")],
        kicker="STATISTICAL ARBITRAGE | FINAL REPORT AND PRESENTATION",
        sources=["ML_Sports_Betting_Project_Proposal.pdf"],
        notes="Authors are confirmed by the September 30 joint project proposal. The supervisor name is supplied directly by the user: Daniel Totouom-Tangho. The requested order is common methodology first, NBA results second, Premier League results last. This presentation combines the implemented studies; it does not replace the separate league records with a new pooled investment experiment."))
    elements = []
    steps = [("1  Earlier games", "Earlier team stats\nPrior-season strength\nPlayer/xG extensions"),
             ("2  Probabilities", "NBA: home / away\nEPL: home / draw / away\nExclude target inputs"),
             ("3  Model selection", "Accuracy branch\nCalibration-error branch\nLater-season evaluation"),
             ("4  Betting rule", "Compare probabilities\nwith archived odds\nApply explicit stake rules")]
    for i, (heading, body) in enumerate(steps):
        x = .65 + i * 3.78
        elements += [dict(type="rect", x=x, y=2.15, w=3.45, h=3.25, fill="FFFFFF", line="D8E0E7"),
            text(x + .18, 2.48, 3.08, .47, heading, 20, TEAL, True),
            text(x + .18, 3.28, 3.08, 1.72, body, 19)]
    elements += [text(.65, 6.0, 14.6, .6, "Estimated return per unit staked = model probability × decimal odds − 1", 24, TEAL, True),
        text(.65, 7.03, 14.6, .9, "We test whether better probability estimates improve betting outcomes.\nA higher classification accuracy or smaller calibration error does not guarantee a profitable price.", 21)]
    slides.append(slide("Common methodology: from past games to bets", "The proposal compares calibration-based and accuracy-based model selection. Implementation differs where the sports require it.",
        elements, sources=["ML Sports/Data.ipynb", "epl_modeling/METHODOLOGY.md", "ML_Sports_Betting_Project_Proposal.pdf"],
        notes="Both initial studies consider logistic regression, random forests, SVM and MLP, with feature screening and forward selection before TPE hyperparameter search. NBA uses 30 trials per family/branch; the first EPL experiment uses 12. NBA season-to-date performance is lagged using shift(1).expanding() within team-season, and both teams' first ten games are excluded as target rows. EPL adds explicit missing-history controls and later player/xG comparisons. Walsh and Joshi's original numerical claims are superseded by their 2025 corrigendum; calibration-driven profitability remains a question, not a guarantee."))
    slides.append(slide("Common metrics; explicit league differences", "Compare outcomes within each league. Keep the financial denominators and funding conventions separate.",
        [table(.65, 2.06, 14.67, 4.4, ["Setting", "NBA implementation", "Premier League implementation"],
            [["Outcome space", "Home / away", "Home / draw / away"],
             ["Calibration criterion", "20 bins; score set to 1 if fewer than 16 bins are occupied", "Mean classwise ECE over 3 classes; 10 bins; no occupancy penalty"],
             ["Post-fit calibration", "No separate held-out temperature fit", "Both initial branches receive held-out temperature scaling"],
             ["Stake and starting cash", "100 fixed or 1/8 Kelly; start 10,000", "1,000 fixed or capped Kelly;\nstart 100,000 in expanded accounts"],
             ["Funding", "Game-by-game settlement", "Joint date-start cash allocation before settlement"]], [.22, .39, .39], 17),
         text(.65, 6.83, 14.6, .48, "Capital return = profit / initial cash.     Stake ROI (yield) = profit / total money staked.", 22, TEAL, True),
         text(.65, 7.58, 14.6, .52, "The NBA source calls capital return “ROI”. We relabel it here. Forecast accuracy is also different from the hit ratio of selected bets.", 17, MUTED)],
        sources=["ML Sports/Data.ipynb", "epl_modeling/metrics.py", "epl_strategy/METHODOLOGY.md"],
        notes="The NBA occupancy rule produces an optimisation penalty sentinel; a value of 1 is not literal 100 percent empirical calibration error. EPL ECE is the mean of three one-versus-rest calibration errors. NBA binary Brier and EPL unscaled three-class Brier have different scales and should not be directly ranked. NBA value selection tests the home side first and otherwise the away side; most EPL value rules maximize p*odds-1 over allowed H/D/A outcomes. NBA eighth Kelly has no extra 2 percent cap, only available-cash clamping. EPL date-start allocation cannot use one same-date result to fund another. Quote availability and execution are unverified in these historical simulations."))

    train = nba["training"]
    selection = train["model_selection_2017"]
    lr_row = next(r for r in selection if r["family"] == "LR")
    svm_row = next(r for r in selection if r["family"] == "SVM")
    slides.append(slide("NBA: data and model selection", "Team box-score differences are lagged; each team's first ten appearances are excluded as prediction targets.",
        [card(.65, 2.06, 4.65, 1.55, "ELIGIBLE GAME ROWS", money(nba["data"]["clean_games"]), "Across the supplied historical sample"),
         card(5.66, 2.06, 4.65, 1.55, "FEATURE SCREENING", "26 → 25 → 9", "Candidate → drift-screened → nonredundant"),
         card(10.67, 2.06, 4.65, 1.55, "BETTING EVALUATION", money(nba["data"]["core_betting_games"]), "2018/19 games with odds"),
         table(.65, 4.12, 14.67, 2.1, ["Selection branch", "Chosen model", "Selected inputs", "2017/18 selection criterion"],
            [["Calibration", "Logistic regression", str(train["calibration_branch_features"]), "Penalised ECE " + pct(lr_row["branch_B_ece"])],
             ["Accuracy", "SVM", str(train["accuracy_branch_features"]), "Accuracy " + pct(svm_row["branch_C_accuracy"])]], [.23, .25, .18, .34], 20),
         text(.65, 6.75, 14.6, .95, "Train: 2014/15–2015/16  →  tune: 2016/17  →  family selection: 2017/18  →  bet: 2018/19.\nThe two branches use different selected feature sets; the row scores are not joint metrics of one fitted model.", 19, MUTED)],
        sources=["ML Sports/Data.ipynb"],
        notes="Source cells 1-16. There are 25 box-score measures plus previous-season win percentage before screening. KS train-versus-validation screening drops OREB; absolute Spearman redundancy threshold is 0.7. Calibration SFS selects ORTG and FG3M; accuracy SFS selects ORTG, PREV_SEASON_WP, FG3M and TOV. TPE uses 30 trials for each family and branch, then ten seed-refit predictions are averaged for model-family selection. The notebook calls 2017/18 a test set, but it chooses LR for the calibration branch and SVM for the accuracy branch, so here it is labeled family selection. It is earlier than the separate 2018/19 betting season."))
    records = nba["betting_2018"]["records"]
    rows = [[r["branch"] + " (" + r["model"] + ")", "100 fixed" if r["staking"] == "fixed" else "1/8 Kelly",
        f"{r['final_capital_saved_rounded']:,.2f}", pct(r["capital_return_saved_rounded"]),
        f"{100*r['trading_frequency_saved_rounded']:.1f}%", f"{100*r['hit_ratio_saved_rounded']:.1f}%"] for r in records]
    capital_graph = figures / "nba_core_capital.png"
    slides.append(slide("NBA: saved 2018/19 betting results", "Four rules, each starting with 10,000. Fixed 100 stakes equal 1% of initial capital.",
        [table(.65, 2.06, 14.67, 2.45, ["Branch / model", "Stake rule", "Final capital", "Capital return", "Trade frequency", "Hit ratio"],
            rows, [.22, .14, .17, .16, .17, .14], 17),
         _image(capital_graph, .65, 4.82, 8.45, 2.75),
         text(9.45, 4.9, 5.85, 2.48, "Home value is checked first.\nOtherwise check away value.\nKelly uses 1/8 of full Kelly,\nlimited to available cash.\nBoth saved Kelly outcomes lose.", 19),
         text(.65, 7.82, 14.6, .34, "Saved notebook results: LR reproduced to cents. SVM replay did not match; its saved results are reported, not independently verified.", 14, RED)],
        sources=["ML Sports/Data.ipynb", "final_deliverables/nba_evidence.json"],
        notes="The table preserves the saved notebook's four final amounts and rounded rates; these are not replaced by new SVM replay values. Source code refits selected models on 2014/15-2017/18 before betting 2018/19. The fixed-parameter audit reproduced both LR financial outcomes to cents but could not reproduce SVM; its ten fits reached the iteration limit. The source-recorded SVM final balances remain reported evidence with this explicit limitation. Source prediction accuracy is 65.27 percent for LR and 64.80 percent for SVM on 2018/19. LR guarded ECE is 4.27 percent; the SVM value of 1 means the bin-occupancy penalty fired, not literal 100 percent calibration error. The bar chart uses saved finals rather than an unverified reconstructed SVM wealth path."))
    annual = nba["rolling_annual"]
    slides.append(slide("NBA: nine-season annual robustness", "Each season starts a fresh 10,000 account with fixed 100 requests. Annual paths are not one funded continuous portfolio.",
        [card(.65, 2.04, 4.65, 1.5, "CALIBRATION-BRANCH MEAN", pct(annual["calibration_mean_return_saved"]), "Mean annual capital return"),
         card(5.66, 2.04, 4.65, 1.5, "ACCURACY-BRANCH MEAN", pct(annual["accuracy_mean_return_saved"]), "Mean annual capital return"),
         card(10.67, 2.04, 4.65, 1.5, "CALIBRATION WINS", str(annual["calibration_wins_seasons"]) + " / " + str(annual["n_seasons"]), "Both branches use logistic regression here"),
         _image(figures / "nba_annual_returns.png", .65, 3.88, 14.67, 3.55),
         text(.65, 7.72, 14.6, .47, "This extension reselects features but does not repeat the four-family search. The annual variation does not support a dependable profit advantage.", 16, MUTED)],
        sources=["ML Sports/Data.ipynb", "final_deliverables/nba_evidence.json"],
        notes="Nine source-recorded seasons cover 2014/15 through 2022/23 and 9,344 betting fixtures. Both annual models are logistic regressions using different objective-selected feature subsets. The source means are minus 17.34 and minus 9.49 percent; calibration outperforms accuracy in three of nine seasons. Both paths exhaust their annual cash in 2017/18. The source notebook adds profits from independently reset accounts to draw a cumulative line; this deck deliberately uses annual-return bars so it does not imply continued funding after bankruptcy. Source annual figures are retained at their printed precision. The supplied PDF also reports stronger market log-loss results in additional analyses, but their full event-level supporting outputs are not in the provided notebook; those claims should not be treated as independently reproduced here."))

    first = epl["first_experiment"]
    ps = {r["model"]: r for r in first["test_probability_scores"]}
    selected = {r["strategy_id"]: r for r in epl["strategy_laboratory"]["single_selected"]}
    pred_rows = []
    for k, name in (("accuracy", "Accuracy-selected SVM"), ("calibration", "Calibration-selected MLP"), ("bet365_devig", "Bet365 market benchmark")):
        r = ps[k]
        pred_rows.append([name, pct(r["accuracy"]), pct(r["classwise_ece_10"]), dec(r["log_loss"])])
    trade_rows = []
    for sid, name in (("S005", "SVM"), ("S013", "MLP")):
        r = selected[sid]
        trade_rows.append([name, str(r["bet_count"]), money(r["profit"]), pct(r["roi"]), pct(r["return_on_initial_capital"])])
    slides.append(slide("EPL: the proposal's accuracy–calibration comparison", "The first experiment evaluates 374 matches in 2025/26 after separate tuning, calibration, family selection and strategy validation.",
        [table(.65, 2.05, 10.8, 2.35, ["Probability model", "Accuracy", "ECE 10", "Log loss"], pred_rows, [.46, .18, .18, .18], 18),
         card(11.85, 2.05, 3.45, 2.35, "PRIMARY POLICIES", "Hold cash", "Neither branch found an admissible positive-return validation threshold."),
         text(.65, 4.83, 14.6, .4, "SECONDARY DIAGNOSTIC: predeclared 5% edge, best archived quotes, 1,000 flat stakes from 100,000", 16, TEAL, True),
         table(.65, 5.43, 14.67, 1.8, ["Model", "Bets", "Profit", "Stake ROI", "Capital return"], trade_rows, [.22, .13, .22, .21, .22], 18),
         text(.65, 7.72, 14.6, .46, "The MLP's +0.41% stake ROI is uncertain: its conditional 95% interval includes zero. The following EPL extensions are exploratory.", 16, MUTED)],
        sources=["epl_modeling/results/RESULTS.md", "epl_modeling/results/classification_scores.csv", "epl_strategy_lab/results/20261015T040052Z_100k84/metrics.csv"],
        notes="This is the experiment most directly aligned with the joint proposal: accuracy selects SVM, calibration selects MLP. Both branches receive the same disjoint temperature calibration. Neither primary validation policy found a threshold with at least thirty bets and strictly positive validation stake ROI, so both hold cash in test; no-trade ROI is undefined. The secondary 5 percent policy was separately declared and is not a substitute chosen from test returns. The displayed 100K accounts are rescaled counterpart strategies from the saved laboratory. SVM loses 8,330 on 371 bets and MLP gains 1,370 on 333 bets, with stake ROIs minus 2.2453 and plus 0.4114 percent. Their conditional intervals both include zero. The raw market has stronger proper probability scores than either learned branch. Later rolling/player studies revisit already inspected outcomes and are exploratory."))
    s = slide("EPL: money progression of all 116 strategies", "2025/26 is the common season available for every account. Each starts with 100,000 monetary units.",
        [_image(figures / "epl_all_116.png", .65, 2.08, 14.67, 5.35),
         text(.65, 7.72, 14.6, .5, "All 84 original and 32 new rules are included. The next model pages label their separate four-year statistics explicitly.", 17, MUTED)],
        sources=["epl_player_models/results/20261020_player_models_review/graph_equity_2025_all.csv"],
        notes="The graph has 116 distinct strategy IDs and 13,224 points, including 114 dates per curve with the 100K anchor. The strategies combine model, outcome selection, prices and sizing rather than representing 116 independent fitted algorithms. Only 88 have comparable continuous four-year records. No earlier records are invented for 28 first-study configurations. New player-study accounts all lose over four continuous years, even when one 2025 slice profited. The graph is an archived-price replay, not verified executed betting.")
    slides.append(s)
    for role in ROLES:
        p = profile(epl_data, role)
        p["title"] = "EPL: " + p["title"][0].lower() + p["title"][1:]
        p["kicker"] = "EPL MODEL AND TRADING RULE | " + role[1]
        slides.append(p)
    assert len(slides) == 12
    for index in (1, 2):
        slides[index]["kicker"] = "COMMON METHODOLOGY | NBA AND PREMIER LEAGUE"
    for index in (3, 4, 5):
        slides[index]["kicker"] = "NBA RESULTS | AMAN DHILLON"
    for index in (6, 7):
        slides[index]["kicker"] = "PREMIER LEAGUE RESULTS | PANAGIOTIS HOUSOS"

    # All NBA backup material precedes the EPL backup, preserving the final
    # requested league order even in the appendix.
    rows = []
    for r in records:
        stake = "100 per bet = 1% of initial 10,000" if r["staking"] == "fixed" else "1/8 Kelly; variable; cap only available cash"
        rows.append([r["branch"] + " / " + r["model"], "Fixed" if r["staking"] == "fixed" else "Eighth Kelly", stake,
            "Home value first; otherwise away value"])
    slides.append(slide("Appendix: the four NBA betting rules", "One bet at most per game; settle sequentially. This is not the EPL joint same-date funding rule.",
        [table(.65, 2.08, 14.67, 3.85, ["Forecast branch", "Sizing rule", "Money requested per trade", "Entry rule"],
            rows, [.21, .16, .34, .29], 18),
         text(.65, 6.34, 14.6, .75, "Eighth-Kelly stake = current cash × (1/8) × max(0, (probability × odds − 1) / (odds − 1)).", 21, TEAL, True),
         text(.65, 7.36, 14.6, .62, "Do not add an EPL-style 2% cap to these source rules. A positive estimated return is a model claim, not a guaranteed gain.", 18, MUTED)],
        appendix=True, kicker="NBA APPENDIX | RULES AND CAPITAL", sources=["ML Sports/Data.ipynb"],
        notes="The source simulator tests ph>1/oh first, otherwise pa>1/oa, and excludes a selected probability exactly 0.5 with its default margin-zero filter. Fixed requests are 100 and Kelly requests use one eighth of the full Kelly fraction. Both are clamped to available current cash. The source may use settlement from an earlier processed game to fund another game on the same date, unlike EPL. All four records start at 10,000 independently. Financial results in the core table remain source-recorded; LR only was reproduced to cents in the fixed-parameter audit."))
    old_epl = concise_epl_contents(epl_data, figures)
    for p in old_epl[6:]:
        p = deepcopy(p)
        p["title"] = p["title"].replace("Appendix:", "EPL appendix:", 1)
        p["kicker"] = "EPL APPENDIX | STRATEGY RULES AND CAPITAL"
        slides.append(p)
    assert len(slides) == 23 and sum(not s["appendix"] for s in slides) == 12
    return slides
