# Latest EPL project report

**Updated October 20, 2026.** The newest report is in **`reports/latest/`**:

- [Latest report — PDF](reports/latest/EPL_Project_Report.pdf)
- [Latest report — editable Word](reports/latest/EPL_Project_Report.docx)
- [Player-model results, predictions and trading metrics — Excel](epl_player_models/results/20261020_player_models_review/report/player_models_overview.xlsx)

The report adds six player-based models and two matched team controls, using
recent player form, positional profiles, projected squads and depth. It evaluates
all eight on the same 1,470 historical fixtures across four seasons. Every
player-based variant has worse pooled log loss than its matched team control;
the bookmaker benchmark also remains stronger. These redesigned historical
experiments do not constitute a fresh holdout.

The 32 new strategies include hit ratio, model expected gain/loss, actual
winning/losing payoffs, frequency, turnover, ROI and drawdown. All 32 lose money
over their uninterrupted four-season accounts. Every strategy starts at 100,000.
The final appendix explains all 116 old and new strategies.

- [All 116 common-season accounts on one graph — PNG](epl_player_models/results/20261020_player_models_review/figures/all_strategies_2025_100k.png)
- [All 116 accounts — offline interactive HTML](epl_player_models/results/20261020_player_models_review/figures/all_strategies_2025_100k.html)
- [All 88 compatible continuous four-season accounts — PNG](epl_player_models/results/20261020_player_models_review/figures/all_strategies_continuous_100k.png)
- [All 88 accounts — offline interactive HTML](epl_player_models/results/20261020_player_models_review/figures/all_strategies_continuous_100k.html)
- [Player feature, fitting and forecast protocol](epl_player_models/PROTOCOL.md)
- [Canonical reviewed report and full analytical export](epl_player_models/results/20261020_player_models_review/)
- [Separate player-model forecast ledger — 80 pending predictions](epl_player_models/results/20261020_player_models_review/forecasts.jsonl)
- [Per-target player coverage](epl_player_models/results/20261020_player_models_review/target_coverage.csv)
- [Projected player identities and source-date audit](epl_player_models/results/20261020_player_models_review/projected_xi.parquet)

The reviewed export fixes the coverage display and Markdown table formatting.
All analytical files and the 80-record forecast ledger are byte-identical to
the [initial fitted export](epl_player_models/results/20261020_player_models/).
This presentation revision neither refits models nor reissues forecasts.
The separate player forecasts cover ten October 23–25 fixtures and remain
unscored. Unavailable pre-match prices mean no prospective stakes or trading
returns. Projected lineups use earlier minutes, with historical position proxies
and availability limitations explained in the report.

The report also retains the earlier prospective evaluation, all historical
price/strategy studies, original graphs and exact original strategy definitions:

- [Original prospective evaluation and next-cycle workbook](epl_prospective/results/20261020_first_outcomes/report/prospective_overview.xlsx)
- [Earlier frozen-model future fixtures and probabilities](epl_live/runs/20261020T223825.164001Z/overview/FORECASTS.md)
- [Full historical price and trading diagnostics workbook](epl_execution/results/20261015_quote_sensitivity/report/execution_overview.xlsx)
- [Updated current team data](epl_live/snapshots/20261020T223053.930369Z_299021e7c7/normalized/teams.csv)
- [Updated current player data](epl_live/snapshots/20261020T223053.930369Z_299021e7c7/normalized/players.csv)

Download the HTML graphs and open them locally for hover and legend controls;
all strategies are initially visible. Archived quote clocks and availability
remain unverified, so historical account paths do not demonstrate executable
fills or future profit.
