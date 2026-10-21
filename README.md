# Statistical Arbitrage final project

**Presentation:** [Editable PowerPoint](presentations/latest/EPL_Project_Presentation.pptx)
and [PDF](presentations/latest/EPL_Project_Presentation.pdf), in
**`presentations/latest/`**. The October 21 deck has 18 main slides and 17
backup slides: implemented system, all-account money graphs, best/simple/team/
player models, complete trading metrics and all 116 strategy explanations.
See [LATEST_PRESENTATION.md](LATEST_PRESENTATION.md) for data, speaker notes
and interactive graphs.

**Newest report:** [PDF](reports/latest/EPL_Project_Report.pdf) and
[editable Word](reports/latest/EPL_Project_Report.docx), in **`reports/latest/`**.
See [LATEST_REPORT.md](LATEST_REPORT.md) for the newest workbook, graphs and
canonical run. The newest October 20 continuation adds six player-based model
variants and two matched team controls, 32 new trading strategies, and 80 separate
future forecasts. It retains the earlier prospective evaluation and historical
studies, with a final appendix explaining all 116 strategies.

## Models built from player data

The [player-model study](epl_player_models/README.md) reconstructs player form,
positional profiles, a projected XI and squad depth from **253,509 historical
player-match rows**, plus 4,551 current-season rows for future lagged inputs.
The four fixed feature blocks contain 19, 96, 222 and 235 inputs, each fitted
with logistic regression and histogram gradient boosting. The six player-based
variants are compared with two matched team controls on the same **1,470 fixtures**
in four chronological evaluation seasons. No target lineup or target player
minutes enter the inputs; position proxies have unverified publication clocks.

Every player-based variant has worse pooled log loss than its matched team
control. All 32 new uninterrupted four-season accounts lose money. Results
remain exploratory; no winning policy is selected. All 80 newly recorded
player-study forecasts for October 23–25 remain pending in a separate ledger.

- [Newest report — PDF](reports/latest/EPL_Project_Report.pdf)
- [Player models, predictions and full strategy metrics — workbook](epl_player_models/results/20261020_player_models_review/report/player_models_overview.xlsx)
- [All 116 common-season 100K accounts — interactive graph](epl_player_models/results/20261020_player_models_review/figures/all_strategies_2025_100k.html)
- [All 88 continuous four-season 100K accounts — interactive graph](epl_player_models/results/20261020_player_models_review/figures/all_strategies_continuous_100k.html)
- [Player-model feature, fitting and forecast protocol](epl_player_models/PROTOCOL.md)
- [Canonical reviewed export](epl_player_models/results/20261020_player_models_review/)

The reviewed export corrects coverage-table presentation and Markdown escaping.
Its models, features, predictions, accounts and forecast ledger are byte-identical
to the preserved [initial fitted export](epl_player_models/results/20261020_player_models/).
It refits no model and releases no additional forecast. Every new strategy has
hit ratio, expected gain/loss, frequency, realized payoffs and risk metrics.

**Current project:** [ML Sports Betting proposal — NBA and EPL](ML_Sports_Betting_Project_Proposal.pdf),
September 30, 2026, Aman Dhillon and Panagiotis Housos. Panagiotis's EPL data
collection has started in [epl_data](epl_data/README.md), using the 20 current
2026/27 clubs. See the [data overview workbook](epl_data/EPL_data_overview.xlsx)
and [starter notebook](epl_data/01_data_inventory.ipynb).

This private repository preserves the final-project documents, acquisition code,
raw source snapshots, 90 CSV/Parquet table pairs, metadata, workbook and executed
notebook. Source-specific terms remain applicable; see
[repository access and setup](REPOSITORY.md) before sharing the data.

Clone with Git LFS to retrieve the complete datasets:

```powershell
git lfs install
git clone https://github.com/ph2606/sports-betting-final-project.git
cd sports-betting-final-project
git lfs pull
python -m pip install -r epl_data/requirements.txt
```

Start in `epl_data/01_data_inventory.ipynb`. The acquisition snapshot and quality
reports describe the downloaded coverage and known limitations.

## EPL draft report and new forecasts

The October 14 continuation adds a seven-page EPL research draft and a manual
forecasting workflow. The fresh Football-Data, Understat and FPL capture covers
completed games through October 12 and includes all 667 current player summaries.
Eight model candidates are fitted and frozen using earlier seasons. Four logistic
alternatives released 40 timestamped probability records for 10 fixtures on
October 17–19. The October 20 continuation has since scored these ten fixtures;
the linked artifacts below preserve the original capture.

- [Draft report — PDF](epl_report/EPL_project_draft.pdf)
- [Draft report — editable Word](epl_report/EPL_project_draft.docx)
- [Draft report — Markdown and reproduction](epl_report/README.md)
- [Forecast probabilities and comparison workbook](epl_live/runs/20261014T092230.366245Z/overview/FORECASTS.md)
- [Live workflow, coverage and manual commands](epl_live/README.md)
- [Append-only forecast ledger](epl_live/forecasts.jsonl)
- [Initial pending-outcome evaluation](epl_live/evaluations/20261014T092819.822459Z/STATUS.md)

The observed price file contains no upcoming EPL quotes. The 40 market-residual
forecasts and 20 market benchmarks are therefore withheld. Capture clocks and
source hashes are saved; provider publication times remain unverified. No
prospective accuracy or profit is available before these fixtures settle. The
draft reports the historical findings below and clearly identifies the new
forecasts as pending.

## More strategies and one 100,000-unit account graph

The [strategy laboratory](epl_strategy_lab/README.md) compares **84 strategies**
over the same 374 quoted 2025/26 matches: 50 previously recorded configurations
(including threshold diagnostics) and 34 new exploratory rules. Each strategy
starts with its own 100,000 monetary units and carries its balance through the
season. All curves, including the eight cash policies, appear on one graph.

- [Every strategy on one money-versus-time graph](epl_strategy_lab/results/20261015T040052Z_100k84/figures/all_strategies_100k.png)
- [Interactive version - download and open locally](epl_strategy_lab/results/20261015T040052Z_100k84/figures/all_strategies_100k.html)
- [Report with a final appendix explaining every strategy - PDF](epl_strategy_lab/results/20261015T040052Z_100k84/report/strategy_lab_report.pdf)
- [Report - editable Word](epl_strategy_lab/results/20261015T040052Z_100k84/report/strategy_lab_report.docx)
- [All trading metrics - workbook](epl_strategy_lab/results/20261015T040052Z_100k84/report/strategy_lab_overview.xlsx)

The new rules cover probability ensembles, simple outcome benchmarks,
consensus, alternative stake sizing, date commitment limits and fixed
eligibility filters. Every strategy retains hit ratio, expected gain/loss,
realized payoffs, trading frequency and risk measures. This is an exploratory
archived-price replay of an already inspected season, with no independently
validated winner or new prospective performance claim.

## Metrics for every trading strategy

The [strategy analytics extension](epl_strategy/README.md) adds hit ratio,
expected gain, expected loss and trading frequency to every saved trading
policy. Its 172 strategy/scope rows include all original validation, test,
monitoring and ablation results, four-season pooled summaries and the existing
threshold-tuning diagnostics. All no-trade policies remain visible.

The tables separately report model-implied expectations and observed winning/
losing payoffs, plus realized expectancy, ROI, turnover, profit factor, capital
return, drawdown and confidence intervals. Prospective trades and executable
arbitrage performance remain unavailable where no position ledger exists.
Original models, historical results and the seven-page draft are preserved.

- [Strategy comparison workbook](epl_strategy/results/20261014T095929.849994Z_4c6add9911/report/EPL_strategy_metrics.xlsx)
- [Trading metrics supplement — PDF](epl_strategy/results/20261014T095929.849994Z_4c6add9911/report/EPL_strategy_metrics_supplement.pdf)
- [Trading metrics supplement — Word](epl_strategy/results/20261014T095929.849994Z_4c6add9911/report/EPL_strategy_metrics_supplement.docx)
- [Metric definitions and reproduction](epl_strategy/METHODOLOGY.md)

## Costs, calibration tails and robustness

The [robustness extension](epl_robustness/README.md) adds nine explicitly
hypothetical fee/payout scenarios for all 158 original and pooled strategy
scopes, plus selected-bet probability diagnostics, odds tails and date/season
contributions. All 1,422 scenario rows retain the requested trading metrics.
Recorded selections and stakes stay fixed, with a separate funding audit.

The calibration branch's 0.41% archived test ROI becomes negative under a
hypothetical 0.5% fee on every stake. Its high-odds tail also shows substantial
model-implied versus observed payoff differences. These are exploratory
diagnostics of inspected history; no new filter, winner or executable edge is
selected from them. Previous results and reports remain unchanged.

- [Cost and robustness workbook](epl_robustness/results/20261015T024639.840013Z_ecce1f1b9c/report/EPL_robustness_metrics.xlsx)
- [Robustness companion — PDF](epl_robustness/results/20261015T024639.840013Z_ecce1f1b9c/report/EPL_robustness_companion.pdf)
- [Robustness companion — Word](epl_robustness/results/20261015T024639.840013Z_ecce1f1b9c/report/EPL_robustness_companion.docx)

## First modeling experiment

The EPL section now includes a reproducible four-family comparison of accuracy
and calibration selection, chronological feature/tuning/calibration stages,
bookmaker baselines and a held-out 2025/26 archived-price replay.

- [Findings and results](epl_modeling/results/RESULTS.md)
- [Executed modeling notebook](epl_modeling/02_epl_modeling_results.ipynb)
- [Modeling results workbook](epl_modeling/results/EPL_modeling_results.xlsx)
- [Protocol and corrected reference paper](epl_modeling/METHODOLOGY.md)
- [Code and reproduction instructions](epl_modeling/README.md)

The first run finds no validated positive betting edge. Both primary policies
hold cash; secondary fixed-threshold returns are statistically inconclusive.
The bookmaker baseline has stronger proper probability scores than either ML
branch. The research report distinguishes these findings from executable
profitability or arbitrage claims.

## Team, xG and player comparisons

The separate rolling study repairs all 17,465 early FPL opponent identities
through an audited overlay, adding 588 usable player-data fixtures. It compares
four fixed feature groups with logistic and market-informed models across
2022/23–2025/26: 32 fitted model variants and 1,470 common evaluation fixtures.

- [Feature-comparison findings](epl_modeling/ablation_results/ABLATION_RESULTS.md)
- [Executed comparison notebook](epl_modeling/03_epl_feature_ablation.ipynb)
- [Comparison workbook](epl_modeling/ablation_results/EPL_feature_ablation.xlsx)
- [Locked historical study protocol](epl_modeling/ABLATION_PROTOCOL.md)
- [Plan for a new prospective test](epl_modeling/PROSPECTIVE_PROTOCOL.md)

xG modestly improves the team-statistic model's observed probability quality;
player inputs have no consistent incremental gain, and raw bookmaker
probabilities remain best on pooled proper scores. The comparison is explicitly
exploratory because some historical outcomes were already inspected. The first
experiment's code and results remain unchanged and are checked by SHA256.

## Earlier reference proposal

**Recommended topic:** Cost-Aware Statistical Arbitrage in Premier League Betting Markets.

Study whether discrepancies between bookmaker consensus probabilities and prediction-market prices predict profitable pre-match trades. Test whether a small set of FPL-related player features adds value after costs. This connects your football interest to the course's mean-reversion, threshold, risk-control and backtesting themes.

- [Submission proposal — Word](project_proposal.docx)
- [Submission proposal — PDF](project_proposal.pdf)
- [Proposal — editable Markdown](project_proposal.md)
- [Complete reading guide: 33 documents, 874 pages](reading_guide.md)
- [Technical plan: models, payoff formulas, risk, execution and tests](technical_plan.md)
- [Data-source audit and feasible alternatives](data_sources_and_feasibility.md)

All supplied PDFs were read before the earlier proposal was chosen. Individual
review notes remain in the four `reading_*.md` group files; extracted text,
scanned-page images and the source inventory preserve the review trail. That
proposal predates the completed EPL acquisition and historical experiments
linked above. No subscription or live trade was made.

The schedule assumes eight weeks and a group of one to three. The professor's exact submission format and deadline were not included in the supplied instructions. A solo project should keep one execution venue, one selection per match and the smallest model set.

Run `python build_documents.py` from the repository root to regenerate the older
combined reading guide and Word/PDF exports after editing the earlier proposal.
The paper inventory retains the original course-workspace paths; the original
course PDF library is separate from this final-project repository.
