# Latest EPL project report

**Updated October 15, 2026.** Open the stable folder **`reports/latest/`**:

- [Latest report - PDF](reports/latest/EPL_Project_Report.pdf)
- [Latest report - editable Word](reports/latest/EPL_Project_Report.docx)

The newest report compares original archived prices with full Bet365
reference-price replays, then isolates quote uplift using the original bets
and stakes. It covers 364 account scopes in three modes (1,092 metric rows),
including the original all-84 strategy comparison and 56 continuous four-season
accounts. All money-versus-time graphs start each strategy at 100,000. Every
account has hit ratio, expected gain/loss, realized payoffs, trading frequency
and applicable risk metrics. The final appendix explains all 84 strategies.

- [Full metrics and diagnostics workbook](epl_execution/results/20261015_quote_sensitivity/report/execution_overview.xlsx)
- [All 56 reference-price continuous accounts - graph](epl_execution/results/20261015_quote_sensitivity/figures/all_reference_strategies_4seasons_100k.png)
- [Interactive reference-price graph - download and open locally](epl_execution/results/20261015_quote_sensitivity/figures/all_reference_strategies_4seasons_100k.html)
- [Preserved original 56-account four-season graph](epl_strategy_validation/results/20261015_temporal_selection/figures/all_strategies_4seasons_100k.png)
- [Original all-84 single-season graph](epl_strategy_lab/results/20261015T040052Z_100k84/figures/all_strategies_100k.png)
- [Immutable newest report and audit files](epl_execution/results/20261015_quote_sensitivity/)
- [Quote replay, funding and attribution protocol](epl_execution/PROTOCOL.md)
- [Previous temporal/selection report and workbook](epl_strategy_validation/results/20261015_temporal_selection/)

These remain retrospective historical analyses; the selection audit conditions
on recorded cashflows and does not turn previously inspected outcomes into an
independent test. The new replay paths do not inherit the original-path selection
adjustment. Unfunded fixed-exposure shadows have ordinary capital/risk measures
withheld and are excluded from wealth graphs. Quote timestamps do not verify
execution or closing-line value. No new prospective performance is reported.

For the earlier concise EPL model/data research draft, see
[the original seven-page paper](epl_report/EPL_project_draft.pdf).
