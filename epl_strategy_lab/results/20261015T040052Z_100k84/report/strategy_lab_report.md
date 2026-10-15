# EPL strategy laboratory: every account starts with 100,000

DRAFT FOR REVIEW | October 15, 2026 | Historical EPL research; each strategy has its own 100,000 monetary-unit account.

This comparison includes every one of the 84 catalog strategies on the same 374 eligible 2025/26 fixtures, with 113 settlement dates from August 15, 2025 through May 24, 2026. The initial point is August 14, 2025 at 100,000 for every account. The single graph shows all accounts, including 8 policies with no recorded trade; curves are not summed into a portfolio.

The catalog preserves 38 distinct prior first/rolling-study rules, adds 12 historical threshold-diagnostic recipes, and includes 34 new exploratory benchmarks, ensembles, allocation, side and eligibility rules. Repeated historical season/scope entries are consolidated into distinct rules and replayed in this common season. Threshold diagnostics are not newly selected primary policies. Pending future forecasts have no settled account performance and are kept outside this historical graph. Earlier cost stresses remain a separate sensitivity study.

Probability inputs comprise 13 frozen series: the first-study accuracy-selected SVM and calibration-selected MLP, and 11 rolling-study model/baseline series. Their training/calibration histories differ, so differences combine model, information-window and rule effects. Three fixed equal-weight ensembles add probability combinations without fitting new estimators or selecting weights by return. No source model is refitted.

All accounts start with 100,000; fixed bets request 1,000. Dynamic and fractional-Kelly sizing use each date's starting cash. Same-date requests are allocated before settlement and uniformly scaled to available cash or the configured date cap; same-date winnings cannot finance another request. There are no account resets, borrowing or invented returns for missing future observations. The appendix gives every exact rule, including model sources, edge tests, price selection, filters and caps.

H, D and A mean home win, draw and away win. Outcomes and inclusive odds bounds filter candidates before choice; edge qualification is strict. Ties use H, then D, then A. At most one outcome is selected per match.

This history was already examined before the expanded catalog was defined. All new recipes and the enlarged comparison are exploratory. A high ending balance, a profitable historical curve or an unadjusted conditional interval does not establish a reliable future edge. The current-club cohort omits six fixtures between excluded clubs, so it is 374 rather than all 380 league matches and retains survivor/selection bias.

Open figures/all_strategies_100k.html for the offline interactive graph: every curve is visible initially; click a legend entry to toggle it or double-click to isolate it. Hover shows ID, date and monetary balance. PNG/SVG and the printed graph use the same complete data. Full-precision metrics and exact configurations are in the workbook. The final part of this report explains every catalog ID individually.

## One graph: all strategy balances over time

All 84 independent accounts start at 100,000 on August 14, 2025. Step lines join date-close balances; coincident cash/rule paths remain separate traces. Legend IDs map to the final complete appendix.

![Every strategy equity curve](../figures/all_strategies_100k.png)

Figure 1. Every catalog strategy, in catalog order, on linear monetary and calendar-date axes. No losing curve is removed. Archived quotes, fills and simultaneity remain unverified; this is a historical replay.

## Complete strategy metrics: S001–S028

All money columns are units per recorded trade. Expected positive/negative components use model probabilities; average winning/losing payoffs are realised conditional means. Cash-policy per-trade means, hit ratio and ROI are undefined, shown as dashes.

Table 1 (continued across all catalog IDs). Frequency=bets/374 priced fixtures; ROI=profit/turnover. Monetary totals, bankroll return, expected net, uncertainty, stakes and exposure remain in the full workbook.

| ID | Trades | Hit % | Trade<br>freq. % | Avg. winning<br>gain | Avg. losing<br>loss | Model expected<br>gain/trade | Model expected<br>loss/trade | ROI on<br>stakes | Return on<br>100,000 | Max.<br>drawdown |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S001 | 0 | — | 0.00% | — | — | — | — | — | 0.00% | 0.00% |
| S002 | 0 | — | 0.00% | — | — | — | — | — | 0.00% | 0.00% |
| S003 | 0 | — | 0.00% | — | — | — | — | — | 0.00% | 0.00% |
| S004 | 0 | — | 0.00% | — | — | — | — | — | 0.00% | 0.00% |
| S005 | 371 | 26.68% | 99.20% | 2,663.33 | 1,000.00 | 1,173.68 | 631.47 | −2.25% | −8.33% | 27.74% |
| S006 | 371 | 26.68% | 99.20% | 3,653.27 | 1,468.30 | 1,748.01 | 905.17 | −7.01% | −37.70% | 49.95% |
| S007 | 365 | 26.85% | 97.59% | 2,533.98 | 1,000.00 | 1,087.19 | 625.18 | −5.12% | −18.67% | 28.60% |
| S008 | 365 | 26.85% | 97.59% | 3,368.62 | 1,398.65 | 1,545.18 | 854.83 | −8.57% | −43.31% | 51.21% |
| S009 | 0 | — | 0.00% | — | — | — | — | — | 0.00% | 0.00% |
| S010 | 0 | — | 0.00% | — | — | — | — | — | 0.00% | 0.00% |
| S011 | 0 | — | 0.00% | — | — | — | — | — | 0.00% | 0.00% |
| S012 | 0 | — | 0.00% | — | — | — | — | — | 0.00% | 0.00% |
| S013 | 333 | 27.03% | 89.04% | 2,715.22 | 1,000.00 | 1,240.24 | 631.66 | 0.41% | 1.37% | 28.11% |
| S014 | 333 | 27.03% | 89.04% | 4,673.27 | 1,794.18 | 2,295.30 | 1,107.73 | −2.59% | −15.39% | 54.44% |
| S015 | 314 | 27.71% | 83.96% | 2,582.18 | 1,000.00 | 1,160.52 | 628.63 | −0.75% | −2.35% | 29.38% |
| S016 | 314 | 27.71% | 83.96% | 4,410.79 | 1,765.64 | 2,101.94 | 1,084.41 | −3.09% | −17.06% | 51.98% |
| S017 | 306 | 27.78% | 81.82% | 2,774.94 | 1,000.00 | 1,034.32 | 690.01 | 4.86% | 14.87% | 18.00% |
| S018 | 306 | 27.78% | 81.82% | 3,471.59 | 1,347.54 | 1,430.25 | 903.46 | −0.67% | −2.72% | 35.79% |
| S019 | 304 | 29.28% | 81.28% | 2,890.67 | 1,000.00 | 1,019.10 | 689.70 | 13.90% | 42.27% | 15.10% |
| S020 | 304 | 29.28% | 81.28% | 3,997.61 | 1,567.55 | 1,603.27 | 1,036.33 | 4.04% | 18.76% | 31.36% |
| S021 | 314 | 26.11% | 83.96% | 2,894.88 | 1,000.00 | 1,035.00 | 692.84 | 1.71% | 5.38% | 21.25% |
| S022 | 314 | 26.11% | 83.96% | 2,909.99 | 1,183.05 | 1,231.39 | 782.29 | −9.94% | −35.85% | 48.86% |
| S023 | 321 | 27.10% | 85.83% | 2,835.98 | 1,000.00 | 1,010.98 | 689.58 | 3.97% | 12.73% | 22.14% |
| S024 | 321 | 27.10% | 85.83% | 3,089.88 | 1,273.21 | 1,293.70 | 838.41 | −7.33% | −29.11% | 47.23% |
| S025 | 250 | 24.40% | 66.84% | 2,699.34 | 1,000.00 | 893.26 | 720.60 | −9.74% | −24.34% | 34.22% |
| S026 | 250 | 24.40% | 66.84% | 2,632.00 | 935.13 | 867.71 | 669.15 | −6.63% | −16.19% | 25.64% |
| S027 | 259 | 27.03% | 69.25% | 2,853.71 | 1,000.00 | 896.62 | 717.47 | 4.15% | 10.76% | 19.50% |
| S028 | 259 | 27.03% | 69.25% | 2,856.25 | 1,053.17 | 957.16 | 735.52 | 0.32% | 0.89% | 19.13% |

## Complete strategy metrics: S029–S056

All money columns are units per recorded trade. Expected positive/negative components use model probabilities; average winning/losing payoffs are realised conditional means. Cash-policy per-trade means, hit ratio and ROI are undefined, shown as dashes.

Table 1 (continued across all catalog IDs). Frequency=bets/374 priced fixtures; ROI=profit/turnover. Monetary totals, bankroll return, expected net, uncertainty, stakes and exposure remain in the full workbook.

| ID | Trades | Hit % | Trade<br>freq. % | Avg. winning<br>gain | Avg. losing<br>loss | Model expected<br>gain/trade | Model expected<br>loss/trade | ROI on<br>stakes | Return on<br>100,000 | Max.<br>drawdown |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S029 | 277 | 25.27% | 74.06% | 2,622.14 | 1,000.00 | 897.20 | 709.19 | −8.47% | −23.45% | 34.33% |
| S030 | 277 | 25.27% | 74.06% | 2,618.42 | 1,007.49 | 915.50 | 696.55 | −8.89% | −25.26% | 32.58% |
| S031 | 289 | 24.22% | 77.27% | 2,696.71 | 1,000.00 | 900.22 | 710.69 | −10.46% | −30.23% | 44.57% |
| S032 | 289 | 24.22% | 77.27% | 2,700.53 | 972.86 | 898.72 | 680.11 | −8.32% | −24.02% | 33.95% |
| S033 | 368 | 25.00% | 98.40% | 2,926.30 | 1,000.00 | 1,511.12 | 613.81 | −1.84% | −6.78% | 32.78% |
| S034 | 368 | 25.00% | 98.40% | 4,563.62 | 1,638.89 | 2,505.09 | 987.80 | −5.46% | −32.48% | 57.66% |
| S035 | 62 | 6.45% | 16.58% | 5,125.00 | 1,000.00 | 982.31 | 861.00 | −60.48% | −37.50% | 40.00% |
| S036 | 62 | 6.45% | 16.58% | 2,378.66 | 354.83 | 357.20 | 308.84 | −49.40% | −11.07% | 13.93% |
| S037 | 91 | 6.59% | 24.33% | 4,666.67 | 1,000.00 | 970.99 | 844.61 | −62.64% | −57.00% | 57.00% |
| S038 | 91 | 6.59% | 24.33% | 2,279.54 | 386.36 | 385.79 | 329.87 | −53.73% | −19.16% | 21.26% |
| S039 | 374 | 42.51% | 100.00% | 1,177.23 | 1,000.00 | 537.20 | 562.74 | −7.44% | −27.82% | 44.37% |
| S040 | 374 | 27.54% | 100.00% | 3,037.67 | 1,000.00 | 729.43 | 756.07 | 11.20% | 41.88% | 32.74% |
| S041 | 374 | 29.95% | 100.00% | 2,119.29 | 1,000.00 | 676.98 | 681.19 | −6.59% | −24.64% | 40.75% |
| S042 | 374 | 48.66% | 100.00% | 845.27 | 1,000.00 | 443.06 | 478.23 | −10.20% | −38.16% | 41.23% |
| S043 | 374 | 22.19% | 100.00% | 3,304.94 | 1,000.00 | 784.06 | 780.78 | −4.46% | −16.69% | 38.25% |
| S044 | 374 | 48.93% | 100.00% | 919.67 | 1,000.00 | 468.52 | 514.06 | −6.07% | −22.70% | 31.07% |
| S045 | 374 | 48.40% | 100.00% | 860.88 | 1,000.00 | 451.15 | 489.01 | −9.94% | −37.18% | 41.77% |
| S046 | 304 | 28.62% | 81.28% | 2,820.57 | 1,000.00 | 1,027.68 | 693.72 | 9.34% | 28.39% | 17.78% |
| S047 | 304 | 28.62% | 81.28% | 3,798.85 | 1,516.04 | 1,569.05 | 1,010.16 | 0.34% | 1.52% | 36.06% |
| S048 | 289 | 28.37% | 77.27% | 2,913.54 | 1,000.00 | 963.99 | 716.17 | 11.04% | 31.91% | 20.55% |
| S049 | 289 | 28.37% | 77.27% | 2,966.31 | 1,192.85 | 1,147.59 | 812.53 | −1.10% | −3.68% | 34.23% |
| S050 | 239 | 22.59% | 63.90% | 3,268.89 | 1,000.00 | 956.46 | 746.18 | −3.55% | −8.48% | 28.95% |
| S051 | 239 | 22.59% | 63.90% | 2,126.73 | 841.80 | 793.30 | 589.60 | −21.19% | −40.89% | 43.87% |
| S052 | 321 | 27.10% | 85.83% | 2,720.03 | 985.80 | 990.69 | 676.42 | 1.90% | 5.96% | 23.80% |
| S053 | 289 | 24.22% | 77.27% | 1,994.18 | 771.09 | 688.46 | 542.44 | −13.25% | −29.28% | 37.65% |
| S054 | 289 | 28.37% | 77.27% | 3,070.35 | 1,072.81 | 1,028.92 | 765.50 | 9.63% | 29.70% | 19.30% |
| S055 | 321 | 27.10% | 85.83% | 1,804.62 | 723.85 | 738.16 | 479.10 | −5.46% | −12.38% | 26.12% |
| S056 | 321 | 27.10% | 85.83% | 4,506.91 | 1,705.49 | 1,718.96 | 1,155.98 | −1.29% | −6.98% | 41.49% |

## Complete strategy metrics: S057–S084

All money columns are units per recorded trade. Expected positive/negative components use model probabilities; average winning/losing payoffs are realised conditional means. Cash-policy per-trade means, hit ratio and ROI are undefined, shown as dashes.

Table 1 (continued across all catalog IDs). Frequency=bets/374 priced fixtures; ROI=profit/turnover. Monetary totals, bankroll return, expected net, uncertainty, stakes and exposure remain in the full workbook.

| ID | Trades | Hit % | Trade<br>freq. % | Avg. winning<br>gain | Avg. losing<br>loss | Model expected<br>gain/trade | Model expected<br>loss/trade | ROI on<br>stakes | Return on<br>100,000 | Max.<br>drawdown |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S057 | 289 | 24.22% | 77.27% | 1,536.98 | 542.99 | 503.50 | 381.48 | −6.99% | −11.33% | 17.61% |
| S058 | 289 | 24.22% | 77.27% | 3,197.66 | 1,190.93 | 1,079.15 | 834.37 | −10.66% | −36.98% | 49.37% |
| S059 | 321 | 27.10% | 85.83% | 3,056.02 | 1,267.49 | 1,287.68 | 834.50 | −7.78% | −30.72% | 47.04% |
| S060 | 289 | 24.22% | 77.27% | 2,700.53 | 972.86 | 898.72 | 680.11 | −8.32% | −24.02% | 33.95% |
| S061 | 289 | 28.37% | 77.27% | 2,954.63 | 1,190.96 | 1,145.65 | 811.06 | −1.27% | −4.25% | 34.23% |
| S062 | 270 | 28.15% | 72.19% | 2,890.92 | 1,000.00 | 975.01 | 716.27 | 9.52% | 25.71% | 20.05% |
| S063 | 270 | 28.15% | 72.19% | 3,009.39 | 1,209.95 | 1,172.38 | 823.53 | −1.89% | −6.02% | 33.60% |
| S064 | 116 | 31.90% | 31.02% | 2,348.65 | 1,000.00 | 929.65 | 674.71 | 6.81% | 7.90% | 13.37% |
| S065 | 135 | 32.59% | 36.10% | 3,386.59 | 1,000.00 | 896.42 | 740.92 | 42.97% | 58.01% | 9.83% |
| S066 | 130 | 19.23% | 34.76% | 3,626.40 | 1,000.00 | 1,032.62 | 759.43 | −11.03% | −14.34% | 23.49% |
| S067 | 264 | 25.38% | 70.59% | 3,111.19 | 1,000.00 | 1,075.87 | 700.54 | 4.34% | 11.45% | 20.45% |
| S068 | 200 | 21.50% | 53.48% | 2,988.37 | 1,000.00 | 962.06 | 721.36 | −14.25% | −28.50% | 37.18% |
| S069 | 222 | 24.77% | 59.36% | 3,266.73 | 1,000.00 | 1,028.87 | 728.19 | 5.71% | 12.67% | 21.00% |
| S070 | 256 | 33.20% | 68.45% | 2,515.41 | 1,000.00 | 857.56 | 655.54 | 16.72% | 42.81% | 13.00% |
| S071 | 222 | 31.08% | 59.36% | 2,436.96 | 1,000.00 | 816.10 | 667.18 | 6.82% | 15.15% | 16.30% |
| S072 | 217 | 35.94% | 58.02% | 2,567.18 | 1,000.00 | 833.94 | 674.32 | 28.22% | 61.24% | 12.00% |
| S073 | 374 | 26.74% | 100.00% | 2,662.20 | 1,000.00 | 1,170.29 | 632.09 | −2.08% | −7.78% | 28.00% |
| S074 | 374 | 26.74% | 100.00% | 2,662.20 | 1,000.00 | 1,170.29 | 632.09 | −2.08% | −7.78% | 28.00% |
| S075 | 365 | 26.58% | 97.59% | 2,679.07 | 1,000.00 | 1,181.53 | 631.43 | −2.23% | −8.13% | 28.54% |
| S076 | 349 | 26.65% | 93.32% | 2,679.25 | 1,000.00 | 1,201.85 | 630.70 | −1.96% | −6.83% | 27.81% |
| S077 | 312 | 25.32% | 83.42% | 2,809.49 | 1,000.00 | 1,258.99 | 635.05 | −3.54% | −11.05% | 27.72% |
| S078 | 276 | 26.09% | 73.80% | 2,894.44 | 1,000.00 | 1,317.97 | 634.90 | 1.59% | 4.40% | 18.87% |
| S079 | 364 | 26.37% | 97.33% | 2,686.56 | 1,000.00 | 1,194.85 | 635.56 | −2.77% | −10.09% | 36.93% |
| S080 | 354 | 26.84% | 94.65% | 2,692.74 | 1,000.00 | 1,208.70 | 633.98 | −0.90% | −3.19% | 31.65% |
| S081 | 318 | 27.36% | 85.03% | 2,693.91 | 1,000.00 | 1,263.27 | 628.83 | 1.06% | 3.37% | 24.76% |
| S082 | 302 | 27.15% | 80.75% | 2,770.98 | 1,000.00 | 1,294.95 | 631.49 | 2.39% | 7.22% | 23.33% |
| S083 | 275 | 25.82% | 73.53% | 2,824.37 | 1,000.00 | 1,346.59 | 630.29 | −1.26% | −3.47% | 32.13% |
| S084 | 255 | 23.92% | 68.18% | 2,977.87 | 1,000.00 | 1,388.55 | 629.78 | −4.84% | −12.35% | 35.93% |

## Definitions, uncertainty and source trail

For stake s, decimal odds O and selected win probability p, model-implied expected gain is p·s·(O−1) and expected loss magnitude is (1−p)·s. Their difference is expected net profit. Totals sum those components across recorded trades; per-trade quantities divide totals by trade count. They condition on actual allocated stakes, including the realised bankroll-dependent Kelly path, and are not unconditional predictions of terminal wealth.

Hit ratio is winning selected outcomes / recorded trades, distinct from full-match three-class prediction accuracy. Average winning gain excludes returned principal; losing loss is a positive magnitude. Realised expectancy is net profit / trades. ROI uses turnover as denominator, while return on initial capital uses 100,000. Profit factor compares total positive and negative net P&L, and drawdown includes initial capital and subsequent date-close peaks. No-trade cash totals/activity are zero; undefined ratios remain unavailable.

Bootstrap intervals, where supplied in the workbook, resample recorded whole dates conditional on the model, selections and stake path. They do not refit models, regenerate a counterfactual Kelly path or adjust for trying many recipes. This common-season replay does not turn previously inspected outcomes into a new test. Probability-weighted expectations can diverge substantially from realised returns, especially when odds amplify probability errors.

The replay uses saved preclosing reference and best-individual-book prices. It adds no actual bookmaker fees, deposit interest, fill restrictions or price-expiry mechanism. Compatible simultaneous quotes and accepted execution are unverified. The previous robustness companion separately studies explicit hypothetical costs. Neither the chart nor these calculations establish deployable arbitrage or a current player-availability signal.

Method/source references before the final appendix: epl_modeling/METHODOLOGY.md; epl_modeling/ABLATION_PROTOCOL.md; epl_strategy/METHODOLOGY.md; epl_strategy_lab/PROTOCOL.md. These preserve chronological design, payoff definitions and exact replay conventions. The reporter manifest records consumed files, code and output hashes. The builder's final manifest is written afterward and is not a report input, avoiding a circular hash dependency.

Rebuild the report from a finished output directory with python -m epl_strategy_lab.report --results PATH. All original acquisition data, fitted studies, prior reports and their outputs remain separate. The appendix follows and is the final report section; it includes one standalone explanation and exact configuration for every ID.

## Appendix — complete strategy definitions (final section)

### S001 — First-study accuracy-selected SVM | locked primary cash | best individual-book quotes | flat 1,000

Origin: legacy.

Frozen first-study accuracy-selected SVM. Hold the entire balance in cash; place no wager. The saved no-bet threshold is 1,000,000.

Exact configuration:

```json
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle","allowed_outcomes": ["H","D","A"],"bankroll_fraction": 0.01,"cash_only": true,"consensus_min": null,"consensus_model_keys": [],"date_cap_fraction": null,"description": "First-study accuracy-selected SVM: validation selected no admissible positive-return rule; the frozen threshold is 1,000,000 and this configuration remains entirely in cash.","diagnostic": false,"fixed_stake": 1000.0,"kelly_fraction": 0.25,"max_bet_fraction": 0.02,"max_odds": null,"min_edge": 1000000.0,"min_odds": null,"model_key": "first_accuracy","model_label": "First-study accuracy-selected SVM","name": "First-study accuracy-selected SVM | locked primary cash | best individual-book quotes | flat 1,000","odds_mode": "best","origin": "legacy","policy_family": "locked primary cash","selection_rule": "max_edge","staking": "fixed","strategy_id": "S001","study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}
```

### S002 — First-study accuracy-selected SVM | locked primary cash | best individual-book quotes | 0.25 Kelly, per-bet cap 2%

Origin: legacy.

Frozen first-study accuracy-selected SVM. Hold the entire balance in cash; place no wager. The saved no-bet threshold is 1,000,000.

Exact configuration:

```json
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle","allowed_outcomes": ["H","D","A"],"bankroll_fraction": 0.01,"cash_only": true,"consensus_min": null,"consensus_model_keys": [],"date_cap_fraction": null,"description": "First-study accuracy-selected SVM: validation selected no admissible positive-return rule; the frozen threshold is 1,000,000 and this configuration remains entirely in cash.","diagnostic": false,"fixed_stake": 1000.0,"kelly_fraction": 0.25,"max_bet_fraction": 0.02,"max_odds": null,"min_edge": 1000000.0,"min_odds": null,"model_key": "first_accuracy","model_label": "First-study accuracy-selected SVM","name": "First-study accuracy-selected SVM | locked primary cash | best individual-book quotes | 0.25 Kelly, per-bet cap 2%","odds_mode": "best","origin": "legacy","policy_family": "locked primary cash","selection_rule": "max_edge","staking": "kelly","strategy_id": "S002","study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}
```

### S003 — First-study accuracy-selected SVM | locked primary cash | Bet365 reference quotes | flat 1,000

Origin: legacy.

Frozen first-study accuracy-selected SVM. Hold the entire balance in cash; place no wager. The saved no-bet threshold is 1,000,000.

Exact configuration:

```json
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle","allowed_outcomes": ["H","D","A"],"bankroll_fraction": 0.01,"cash_only": true,"consensus_min": null,"consensus_model_keys": [],"date_cap_fraction": null,"description": "First-study accuracy-selected SVM: validation selected no admissible positive-return rule; the frozen threshold is 1,000,000 and this configuration remains entirely in cash.","diagnostic": false,"fixed_stake": 1000.0,"kelly_fraction": 0.25,"max_bet_fraction": 0.02,"max_odds": null,"min_edge": 1000000.0,"min_odds": null,"model_key": "first_accuracy","model_label": "First-study accuracy-selected SVM","name": "First-study accuracy-selected SVM | locked primary cash | Bet365 reference quotes | flat 1,000","odds_mode": "reference","origin": "legacy","policy_family": "locked primary cash","selection_rule": "max_edge","staking": "fixed","strategy_id": "S003","study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}
```

### S004 — First-study accuracy-selected SVM | locked primary cash | Bet365 reference quotes | 0.25 Kelly, per-bet cap 2%

Origin: legacy.

Frozen first-study accuracy-selected SVM. Hold the entire balance in cash; place no wager. The saved no-bet threshold is 1,000,000.

Exact configuration:

```json
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle","allowed_outcomes": ["H","D","A"],"bankroll_fraction": 0.01,"cash_only": true,"consensus_min": null,"consensus_model_keys": [],"date_cap_fraction": null,"description": "First-study accuracy-selected SVM: validation selected no admissible positive-return rule; the frozen threshold is 1,000,000 and this configuration remains entirely in cash.","diagnostic": false,"fixed_stake": 1000.0,"kelly_fraction": 0.25,"max_bet_fraction": 0.02,"max_odds": null,"min_edge": 1000000.0,"min_odds": null,"model_key": "first_accuracy","model_label": "First-study accuracy-selected SVM","name": "First-study accuracy-selected SVM | locked primary cash | Bet365 reference quotes | 0.25 Kelly, per-bet cap 2%","odds_mode": "reference","origin": "legacy","policy_family": "locked primary cash","selection_rule": "max_edge","staking": "kelly","strategy_id": "S004","study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}
```

### S005 — First-study accuracy-selected SVM | predeclared 5% edge | best individual-book quotes | flat 1,000

Origin: legacy.

Frozen first-study accuracy-selected SVM. Choose the eligible H/D/A outcome with largest p×odds−1. Use best eligible individual-book prices. Apply outcomes H, D, A and no decimal-odds bounds before outcome choice. Require selected p×odds−1 strictly above 5.00%. Request a fixed stake of 1,000 monetary units. Scale same-date requests proportionally to available cash; no extra date cap.

Exact configuration:

```json
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle","allowed_outcomes": ["H","D","A"],"bankroll_fraction": 0.01,"cash_only": false,"consensus_min": null,"consensus_model_keys": [],"date_cap_fraction": null,"description": "First-study accuracy-selected SVM; max_edge selection among the allowed outcomes at best individual-book quotes. Require selected model expected return strictly above 5%; stake flat 1,000.","diagnostic": false,"fixed_stake": 1000.0,"kelly_fraction": 0.25,"max_bet_fraction": 0.02,"max_odds": null,"min_edge": 0.05,"min_odds": null,"model_key": "first_accuracy","model_label": "First-study accuracy-selected SVM","name": "First-study accuracy-selected SVM | predeclared 5% edge | best individual-book quotes | flat 1,000","odds_mode": "best","origin": "legacy","policy_family": "predeclared 5% edge","selection_rule": "max_edge","staking": "fixed","strategy_id": "S005","study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}
```

### S006 — First-study accuracy-selected SVM | predeclared 5% edge | best individual-book quotes | 0.25 Kelly, per-bet cap 2%

Origin: legacy.

Frozen first-study accuracy-selected SVM. Choose the eligible H/D/A outcome with largest p×odds−1. Use best eligible individual-book prices. Apply outcomes H, D, A and no decimal-odds bounds before outcome choice. Require selected p×odds−1 strictly above 5.00%. Request B×min(cap, f×max((p×odds−1)/(odds−1),0)), where B is date-start balance, f=0.2500 and cap=2.00%. Scale same-date requests proportionally to available cash; no extra date cap.

Exact configuration:

```json
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle","allowed_outcomes": ["H","D","A"],"bankroll_fraction": 0.01,"cash_only": false,"consensus_min": null,"consensus_model_keys": [],"date_cap_fraction": null,"description": "First-study accuracy-selected SVM; max_edge selection among the allowed outcomes at best individual-book quotes. Require selected model expected return strictly above 5%; stake 0.25 Kelly, per-bet cap 2%.","diagnostic": false,"fixed_stake": 1000.0,"kelly_fraction": 0.25,"max_bet_fraction": 0.02,"max_odds": null,"min_edge": 0.05,"min_odds": null,"model_key": "first_accuracy","model_label": "First-study accuracy-selected SVM","name": "First-study accuracy-selected SVM | predeclared 5% edge | best individual-book quotes | 0.25 Kelly, per-bet cap 2%","odds_mode": "best","origin": "legacy","policy_family": "predeclared 5% edge","selection_rule": "max_edge","staking": "kelly","strategy_id": "S006","study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}
```

### S007 — First-study accuracy-selected SVM | predeclared 5% edge | Bet365 reference quotes | flat 1,000

Origin: legacy.

Frozen first-study accuracy-selected SVM. Choose the eligible H/D/A outcome with largest p×odds−1. Use Bet365 reference prices. Apply outcomes H, D, A and no decimal-odds bounds before outcome choice. Require selected p×odds−1 strictly above 5.00%. Request a fixed stake of 1,000 monetary units. Scale same-date requests proportionally to available cash; no extra date cap.

Exact configuration:

```json
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle","allowed_outcomes": ["H","D","A"],"bankroll_fraction": 0.01,"cash_only": false,"consensus_min": null,"consensus_model_keys": [],"date_cap_fraction": null,"description": "First-study accuracy-selected SVM; max_edge selection among the allowed outcomes at Bet365 reference quotes. Require selected model expected return strictly above 5%; stake flat 1,000.","diagnostic": false,"fixed_stake": 1000.0,"kelly_fraction": 0.25,"max_bet_fraction": 0.02,"max_odds": null,"min_edge": 0.05,"min_odds": null,"model_key": "first_accuracy","model_label": "First-study accuracy-selected SVM","name": "First-study accuracy-selected SVM | predeclared 5% edge | Bet365 reference quotes | flat 1,000","odds_mode": "reference","origin": "legacy","policy_family": "predeclared 5% edge","selection_rule": "max_edge","staking": "fixed","strategy_id": "S007","study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}
```

### S008 — First-study accuracy-selected SVM | predeclared 5% edge | Bet365 reference quotes | 0.25 Kelly, per-bet cap 2%

Origin: legacy.

Frozen first-study accuracy-selected SVM. Choose the eligible H/D/A outcome with largest p×odds−1. Use Bet365 reference prices. Apply outcomes H, D, A and no decimal-odds bounds before outcome choice. Require selected p×odds−1 strictly above 5.00%. Request B×min(cap, f×max((p×odds−1)/(odds−1),0)), where B is date-start balance, f=0.2500 and cap=2.00%. Scale same-date requests proportionally to available cash; no extra date cap.

Exact configuration:

```json
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle","allowed_outcomes": ["H","D","A"],"bankroll_fraction": 0.01,"cash_only": false,"consensus_min": null,"consensus_model_keys": [],"date_cap_fraction": null,"description": "First-study accuracy-selected SVM; max_edge selection among the allowed outcomes at Bet365 reference quotes. Require selected model expected return strictly above 5%; stake 0.25 Kelly, per-bet cap 2%.","diagnostic": false,"fixed_stake": 1000.0,"kelly_fraction": 0.25,"max_bet_fraction": 0.02,"max_odds": null,"min_edge": 0.05,"min_odds": null,"model_key": "first_accuracy","model_label": "First-study accuracy-selected SVM","name": "First-study accuracy-selected SVM | predeclared 5% edge | Bet365 reference quotes | 0.25 Kelly, per-bet cap 2%","odds_mode": "reference","origin": "legacy","policy_family": "predeclared 5% edge","selection_rule": "max_edge","staking": "kelly","strategy_id": "S008","study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}
```

### S009 — First-study calibration-selected MLP | locked primary cash | best individual-book quotes | flat 1,000

Origin: legacy.

Frozen first-study ECE-selected MLP. Hold the entire balance in cash; place no wager. The saved no-bet threshold is 1,000,000.

Exact configuration:

```json
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle","allowed_outcomes": ["H","D","A"],"bankroll_fraction": 0.01,"cash_only": true,"consensus_min": null,"consensus_model_keys": [],"date_cap_fraction": null,"description": "First-study calibration-selected MLP: validation selected no admissible positive-return rule; the frozen threshold is 1,000,000 and this configuration remains entirely in cash.","diagnostic": false,"fixed_stake": 1000.0,"kelly_fraction": 0.25,"max_bet_fraction": 0.02,"max_odds": null,"min_edge": 1000000.0,"min_odds": null,"model_key": "first_calibration","model_label": "First-study calibration-selected MLP","name": "First-study calibration-selected MLP | locked primary cash | best individual-book quotes | flat 1,000","odds_mode": "best","origin": "legacy","policy_family": "locked primary cash","selection_rule": "max_edge","staking": "fixed","strategy_id": "S009","study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}
```

### S010 — First-study calibration-selected MLP | locked primary cash | best individual-book quotes | 0.25 Kelly, per-bet cap 2%

Origin: legacy.

Frozen first-study ECE-selected MLP. Hold the entire balance in cash; place no wager. The saved no-bet threshold is 1,000,000.

Exact configuration:

```json
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle","allowed_outcomes": ["H","D","A"],"bankroll_fraction": 0.01,"cash_only": true,"consensus_min": null,"consensus_model_keys": [],"date_cap_fraction": null,"description": "First-study calibration-selected MLP: validation selected no admissible positive-return rule; the frozen threshold is 1,000,000 and this configuration remains entirely in cash.","diagnostic": false,"fixed_stake": 1000.0,"kelly_fraction": 0.25,"max_bet_fraction": 0.02,"max_odds": null,"min_edge": 1000000.0,"min_odds": null,"model_key": "first_calibration","model_label": "First-study calibration-selected MLP","name": "First-study calibration-selected MLP | locked primary cash | best individual-book quotes | 0.25 Kelly, per-bet cap 2%","odds_mode": "best","origin": "legacy","policy_family": "locked primary cash","selection_rule": "max_edge","staking": "kelly","strategy_id": "S010","study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}
```

### S011 — First-study calibration-selected MLP | locked primary cash | Bet365 reference quotes | flat 1,000

Origin: legacy.

Frozen first-study ECE-selected MLP. Hold the entire balance in cash; place no wager. The saved no-bet threshold is 1,000,000.

Exact configuration:

```json
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle","allowed_outcomes": ["H","D","A"],"bankroll_fraction": 0.01,"cash_only": true,"consensus_min": null,"consensus_model_keys": [],"date_cap_fraction": null,"description": "First-study calibration-selected MLP: validation selected no admissible positive-return rule; the frozen threshold is 1,000,000 and this configuration remains entirely in cash.","diagnostic": false,"fixed_stake": 1000.0,"kelly_fraction": 0.25,"max_bet_fraction": 0.02,"max_odds": null,"min_edge": 1000000.0,"min_odds": null,"model_key": "first_calibration","model_label": "First-study calibration-selected MLP","name": "First-study calibration-selected MLP | locked primary cash | Bet365 reference quotes | flat 1,000","odds_mode": "reference","origin": "legacy","policy_family": "locked primary cash","selection_rule": "max_edge","staking": "fixed","strategy_id": "S011","study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}
```

### S012 — First-study calibration-selected MLP | locked primary cash | Bet365 reference quotes | 0.25 Kelly, per-bet cap 2%

Origin: legacy.

Frozen first-study ECE-selected MLP. Hold the entire balance in cash; place no wager. The saved no-bet threshold is 1,000,000.

Exact configuration:

```json
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle","allowed_outcomes": ["H","D","A"],"bankroll_fraction": 0.01,"cash_only": true,"consensus_min": null,"consensus_model_keys": [],"date_cap_fraction": null,"description": "First-study calibration-selected MLP: validation selected no admissible positive-return rule; the frozen threshold is 1,000,000 and this configuration remains entirely in cash.","diagnostic": false,"fixed_stake": 1000.0,"kelly_fraction": 0.25,"max_bet_fraction": 0.02,"max_odds": null,"min_edge": 1000000.0,"min_odds": null,"model_key": "first_calibration","model_label": "First-study calibration-selected MLP","name": "First-study calibration-selected MLP | locked primary cash | Bet365 reference quotes | 0.25 Kelly, per-bet cap 2%","odds_mode": "reference","origin": "legacy","policy_family": "locked primary cash","selection_rule": "max_edge","staking": "kelly","strategy_id": "S012","study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}
```

### S013 — First-study calibration-selected MLP | predeclared 5% edge | best individual-book quotes | flat 1,000

Origin: legacy.

Frozen first-study ECE-selected MLP. Choose the eligible H/D/A outcome with largest p×odds−1. Use best eligible individual-book prices. Apply outcomes H, D, A and no decimal-odds bounds before outcome choice. Require selected p×odds−1 strictly above 5.00%. Request a fixed stake of 1,000 monetary units. Scale same-date requests proportionally to available cash; no extra date cap.

Exact configuration:

```json
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle","allowed_outcomes": ["H","D","A"],"bankroll_fraction": 0.01,"cash_only": false,"consensus_min": null,"consensus_model_keys": [],"date_cap_fraction": null,"description": "First-study calibration-selected MLP; max_edge selection among the allowed outcomes at best individual-book quotes. Require selected model expected return strictly above 5%; stake flat 1,000.","diagnostic": false,"fixed_stake": 1000.0,"kelly_fraction": 0.25,"max_bet_fraction": 0.02,"max_odds": null,"min_edge": 0.05,"min_odds": null,"model_key": "first_calibration","model_label": "First-study calibration-selected MLP","name": "First-study calibration-selected MLP | predeclared 5% edge | best individual-book quotes | flat 1,000","odds_mode": "best","origin": "legacy","policy_family": "predeclared 5% edge","selection_rule": "max_edge","staking": "fixed","strategy_id": "S013","study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}
```

### S014 — First-study calibration-selected MLP | predeclared 5% edge | best individual-book quotes | 0.25 Kelly, per-bet cap 2%

Origin: legacy.

Frozen first-study ECE-selected MLP. Choose the eligible H/D/A outcome with largest p×odds−1. Use best eligible individual-book prices. Apply outcomes H, D, A and no decimal-odds bounds before outcome choice. Require selected p×odds−1 strictly above 5.00%. Request B×min(cap, f×max((p×odds−1)/(odds−1),0)), where B is date-start balance, f=0.2500 and cap=2.00%. Scale same-date requests proportionally to available cash; no extra date cap.

Exact configuration:

```json
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle","allowed_outcomes": ["H","D","A"],"bankroll_fraction": 0.01,"cash_only": false,"consensus_min": null,"consensus_model_keys": [],"date_cap_fraction": null,"description": "First-study calibration-selected MLP; max_edge selection among the allowed outcomes at best individual-book quotes. Require selected model expected return strictly above 5%; stake 0.25 Kelly, per-bet cap 2%.","diagnostic": false,"fixed_stake": 1000.0,"kelly_fraction": 0.25,"max_bet_fraction": 0.02,"max_odds": null,"min_edge": 0.05,"min_odds": null,"model_key": "first_calibration","model_label": "First-study calibration-selected MLP","name": "First-study calibration-selected MLP | predeclared 5% edge | best individual-book quotes | 0.25 Kelly, per-bet cap 2%","odds_mode": "best","origin": "legacy","policy_family": "predeclared 5% edge","selection_rule": "max_edge","staking": "kelly","strategy_id": "S014","study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}
```

### S015 — First-study calibration-selected MLP | predeclared 5% edge | Bet365 reference quotes | flat 1,000

Origin: legacy.

Frozen first-study ECE-selected MLP. Choose the eligible H/D/A outcome with largest p×odds−1. Use Bet365 reference prices. Apply outcomes H, D, A and no decimal-odds bounds before outcome choice. Require selected p×odds−1 strictly above 5.00%. Request a fixed stake of 1,000 monetary units. Scale same-date requests proportionally to available cash; no extra date cap.

Exact configuration:

```json
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle","allowed_outcomes": ["H","D","A"],"bankroll_fraction": 0.01,"cash_only": false,"consensus_min": null,"consensus_model_keys": [],"date_cap_fraction": null,"description": "First-study calibration-selected MLP; max_edge selection among the allowed outcomes at Bet365 reference quotes. Require selected model expected return strictly above 5%; stake flat 1,000.","diagnostic": false,"fixed_stake": 1000.0,"kelly_fraction": 0.25,"max_bet_fraction": 0.02,"max_odds": null,"min_edge": 0.05,"min_odds": null,"model_key": "first_calibration","model_label": "First-study calibration-selected MLP","name": "First-study calibration-selected MLP | predeclared 5% edge | Bet365 reference quotes | flat 1,000","odds_mode": "reference","origin": "legacy","policy_family": "predeclared 5% edge","selection_rule": "max_edge","staking": "fixed","strategy_id": "S015","study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}
```

### S016 — First-study calibration-selected MLP | predeclared 5% edge | Bet365 reference quotes | 0.25 Kelly, per-bet cap 2%

Origin: legacy.

Frozen first-study ECE-selected MLP. Choose the eligible H/D/A outcome with largest p×odds−1. Use Bet365 reference prices. Apply outcomes H, D, A and no decimal-odds bounds before outcome choice. Require selected p×odds−1 strictly above 5.00%. Request B×min(cap, f×max((p×odds−1)/(odds−1),0)), where B is date-start balance, f=0.2500 and cap=2.00%. Scale same-date requests proportionally to available cash; no extra date cap.

Exact configuration:

```json
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle","allowed_outcomes": ["H","D","A"],"bankroll_fraction": 0.01,"cash_only": false,"consensus_min": null,"consensus_model_keys": [],"date_cap_fraction": null,"description": "First-study calibration-selected MLP; max_edge selection among the allowed outcomes at Bet365 reference quotes. Require selected model expected return strictly above 5%; stake 0.25 Kelly, per-bet cap 2%.","diagnostic": false,"fixed_stake": 1000.0,"kelly_fraction": 0.25,"max_bet_fraction": 0.02,"max_odds": null,"min_edge": 0.05,"min_odds": null,"model_key": "first_calibration","model_label": "First-study calibration-selected MLP","name": "First-study calibration-selected MLP | predeclared 5% edge | Bet365 reference quotes | 0.25 Kelly, per-bet cap 2%","odds_mode": "reference","origin": "legacy","policy_family": "predeclared 5% edge","selection_rule": "max_edge","staking": "kelly","strategy_id": "S016","study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}
```

### S017 — Rolling logistic: team | predeclared 5% edge | best individual-book quotes | flat 1,000

Origin: legacy.

Frozen rolling-study logistic probabilities; feature group team_only. Choose the eligible H/D/A outcome with largest p×odds−1. Use best eligible individual-book prices. Apply outcomes H, D, A and no decimal-odds bounds before outcome choice. Require selected p×odds−1 strictly above 5.00%. Request a fixed stake of 1,000 monetary units. Scale same-date requests proportionally to available cash; no extra date cap.

Exact configuration:

```json
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle","allowed_outcomes": ["H","D","A"],"bankroll_fraction": 0.01,"cash_only": false,"consensus_min": null,"consensus_model_keys": [],"date_cap_fraction": null,"description": "Rolling logistic: team; max_edge selection among the allowed outcomes at best individual-book quotes. Require selected model expected return strictly above 5%; stake flat 1,000.","diagnostic": false,"fixed_stake": 1000.0,"kelly_fraction": 0.25,"max_bet_fraction": 0.02,"max_odds": null,"min_edge": 0.05,"min_odds": null,"model_key": "logit_team_only","model_label": "Rolling logistic: team","name": "Rolling logistic: team | predeclared 5% edge | best individual-book quotes | flat 1,000","odds_mode": "best","origin": "legacy","policy_family": "predeclared 5% edge","selection_rule": "max_edge","staking": "fixed","strategy_id": "S017","study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}
```

### S018 — Rolling logistic: team | predeclared 5% edge | best individual-book quotes | 0.25 Kelly, per-bet cap 2%

Origin: legacy.

Frozen rolling-study logistic probabilities; feature group team_only. Choose the eligible H/D/A outcome with largest p×odds−1. Use best eligible individual-book prices. Apply outcomes H, D, A and no decimal-odds bounds before outcome choice. Require selected p×odds−1 strictly above 5.00%. Request B×min(cap, f×max((p×odds−1)/(odds−1),0)), where B is date-start balance, f=0.2500 and cap=2.00%. Scale same-date requests proportionally to available cash; no extra date cap.

Exact configuration:

```json
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle","allowed_outcomes": ["H","D","A"],"bankroll_fraction": 0.01,"cash_only": false,"consensus_min": null,"consensus_model_keys": [],"date_cap_fraction": null,"description": "Rolling logistic: team; max_edge selection among the allowed outcomes at best individual-book quotes. Require selected model expected return strictly above 5%; stake 0.25 Kelly, per-bet cap 2%.","diagnostic": false,"fixed_stake": 1000.0,"kelly_fraction": 0.25,"max_bet_fraction": 0.02,"max_odds": null,"min_edge": 0.05,"min_odds": null,"model_key": "logit_team_only","model_label": "Rolling logistic: team","name": "Rolling logistic: team | predeclared 5% edge | best individual-book quotes | 0.25 Kelly, per-bet cap 2%","odds_mode": "best","origin": "legacy","policy_family": "predeclared 5% edge","selection_rule": "max_edge","staking": "kelly","strategy_id": "S018","study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}
```

### S019 — Rolling logistic: team + xG | predeclared 5% edge | best individual-book quotes | flat 1,000

Origin: legacy.

Frozen rolling-study logistic probabilities; feature group team_xg. Choose the eligible H/D/A outcome with largest p×odds−1. Use best eligible individual-book prices. Apply outcomes H, D, A and no decimal-odds bounds before outcome choice. Require selected p×odds−1 strictly above 5.00%. Request a fixed stake of 1,000 monetary units. Scale same-date requests proportionally to available cash; no extra date cap.

Exact configuration:

```json
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle","allowed_outcomes": ["H","D","A"],"bankroll_fraction": 0.01,"cash_only": false,"consensus_min": null,"consensus_model_keys": [],"date_cap_fraction": null,"description": "Rolling logistic: team + xG; max_edge selection among the allowed outcomes at best individual-book quotes. Require selected model expected return strictly above 5%; stake flat 1,000.","diagnostic": false,"fixed_stake": 1000.0,"kelly_fraction": 0.25,"max_bet_fraction": 0.02,"max_odds": null,"min_edge": 0.05,"min_odds": null,"model_key": "logit_team_xg","model_label": "Rolling logistic: team + xG","name": "Rolling logistic: team + xG | predeclared 5% edge | best individual-book quotes | flat 1,000","odds_mode": "best","origin": "legacy","policy_family": "predeclared 5% edge","selection_rule": "max_edge","staking": "fixed","strategy_id": "S019","study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}
```

### S020 — Rolling logistic: team + xG | predeclared 5% edge | best individual-book quotes | 0.25 Kelly, per-bet cap 2%

Origin: legacy.

Frozen rolling-study logistic probabilities; feature group team_xg. Choose the eligible H/D/A outcome with largest p×odds−1. Use best eligible individual-book prices. Apply outcomes H, D, A and no decimal-odds bounds before outcome choice. Require selected p×odds−1 strictly above 5.00%. Request B×min(cap, f×max((p×odds−1)/(odds−1),0)), where B is date-start balance, f=0.2500 and cap=2.00%. Scale same-date requests proportionally to available cash; no extra date cap.

Exact configuration:

```json
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle","allowed_outcomes": ["H","D","A"],"bankroll_fraction": 0.01,"cash_only": false,"consensus_min": null,"consensus_model_keys": [],"date_cap_fraction": null,"description": "Rolling logistic: team + xG; max_edge selection among the allowed outcomes at best individual-book quotes. Require selected model expected return strictly above 5%; stake 0.25 Kelly, per-bet cap 2%.","diagnostic": false,"fixed_stake": 1000.0,"kelly_fraction": 0.25,"max_bet_fraction": 0.02,"max_odds": null,"min_edge": 0.05,"min_odds": null,"model_key": "logit_team_xg","model_label": "Rolling logistic: team + xG","name": "Rolling logistic: team + xG | predeclared 5% edge | best individual-book quotes | 0.25 Kelly, per-bet cap 2%","odds_mode": "best","origin": "legacy","policy_family": "predeclared 5% edge","selection_rule": "max_edge","staking": "kelly","strategy_id": "S020","study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}
```

### S021 — Rolling logistic: team + player | predeclared 5% edge | best individual-book quotes | flat 1,000

Origin: legacy.

Frozen rolling-study logistic probabilities; feature group team_players. Choose the eligible H/D/A outcome with largest p×odds−1. Use best eligible individual-book prices. Apply outcomes H, D, A and no decimal-odds bounds before outcome choice. Require selected p×odds−1 strictly above 5.00%. Request a fixed stake of 1,000 monetary units. Scale same-date requests proportionally to available cash; no extra date cap.

Exact configuration:

```json
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle","allowed_outcomes": ["H","D","A"],"bankroll_fraction": 0.01,"cash_only": false,"consensus_min": null,"consensus_model_keys": [],"date_cap_fraction": null,"description": "Rolling logistic: team + player; max_edge selection among the allowed outcomes at best individual-book quotes. Require selected model expected return strictly above 5%; stake flat 1,000.","diagnostic": false,"fixed_stake": 1000.0,"kelly_fraction": 0.25,"max_bet_fraction": 0.02,"max_odds": null,"min_edge": 0.05,"min_odds": null,"model_key": "logit_team_players","model_label": "Rolling logistic: team + player","name": "Rolling logistic: team + player | predeclared 5% edge | best individual-book quotes | flat 1,000","odds_mode": "best","origin": "legacy","policy_family": "predeclared 5% edge","selection_rule": "max_edge","staking": "fixed","strategy_id": "S021","study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}
```

### S022 — Rolling logistic: team + player | predeclared 5% edge | best individual-book quotes | 0.25 Kelly, per-bet cap 2%

Origin: legacy.

Frozen rolling-study logistic probabilities; feature group team_players. Choose the eligible H/D/A outcome with largest p×odds−1. Use best eligible individual-book prices. Apply outcomes H, D, A and no decimal-odds bounds before outcome choice. Require selected p×odds−1 strictly above 5.00%. Request B×min(cap, f×max((p×odds−1)/(odds−1),0)), where B is date-start balance, f=0.2500 and cap=2.00%. Scale same-date requests proportionally to available cash; no extra date cap.

Exact configuration:

```json
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle","allowed_outcomes": ["H","D","A"],"bankroll_fraction": 0.01,"cash_only": false,"consensus_min": null,"consensus_model_keys": [],"date_cap_fraction": null,"description": "Rolling logistic: team + player; max_edge selection among the allowed outcomes at best individual-book quotes. Require selected model expected return strictly above 5%; stake 0.25 Kelly, per-bet cap 2%.","diagnostic": false,"fixed_stake": 1000.0,"kelly_fraction": 0.25,"max_bet_fraction": 0.02,"max_odds": null,"min_edge": 0.05,"min_odds": null,"model_key": "logit_team_players","model_label": "Rolling logistic: team + player","name": "Rolling logistic: team + player | predeclared 5% edge | best individual-book quotes | 0.25 Kelly, per-bet cap 2%","odds_mode": "best","origin": "legacy","policy_family": "predeclared 5% edge","selection_rule": "max_edge","staking": "kelly","strategy_id": "S022","study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}
```

### S023 — Rolling logistic: combined | predeclared 5% edge | best individual-book quotes | flat 1,000

Origin: legacy.

Frozen rolling-study logistic probabilities; feature group combined. Choose the eligible H/D/A outcome with largest p×odds−1. Use best eligible individual-book prices. Apply outcomes H, D, A and no decimal-odds bounds before outcome choice. Require selected p×odds−1 strictly above 5.00%. Request a fixed stake of 1,000 monetary units. Scale same-date requests proportionally to available cash; no extra date cap.

Exact configuration:

```json
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle","allowed_outcomes": ["H","D","A"],"bankroll_fraction": 0.01,"cash_only": false,"consensus_min": null,"consensus_model_keys": [],"date_cap_fraction": null,"description": "Rolling logistic: combined; max_edge selection among the allowed outcomes at best individual-book quotes. Require selected model expected return strictly above 5%; stake flat 1,000.","diagnostic": false,"fixed_stake": 1000.0,"kelly_fraction": 0.25,"max_bet_fraction": 0.02,"max_odds": null,"min_edge": 0.05,"min_odds": null,"model_key": "logit_combined","model_label": "Rolling logistic: combined","name": "Rolling logistic: combined | predeclared 5% edge | best individual-book quotes | flat 1,000","odds_mode": "best","origin": "legacy","policy_family": "predeclared 5% edge","selection_rule": "max_edge","staking": "fixed","strategy_id": "S023","study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}
```

### S024 — Rolling logistic: combined | predeclared 5% edge | best individual-book quotes | 0.25 Kelly, per-bet cap 2%

Origin: legacy.

Frozen rolling-study logistic probabilities; feature group combined. Choose the eligible H/D/A outcome with largest p×odds−1. Use best eligible individual-book prices. Apply outcomes H, D, A and no decimal-odds bounds before outcome choice. Require selected p×odds−1 strictly above 5.00%. Request B×min(cap, f×max((p×odds−1)/(odds−1),0)), where B is date-start balance, f=0.2500 and cap=2.00%. Scale same-date requests proportionally to available cash; no extra date cap.

Exact configuration:

```json
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle","allowed_outcomes": ["H","D","A"],"bankroll_fraction": 0.01,"cash_only": false,"consensus_min": null,"consensus_model_keys": [],"date_cap_fraction": null,"description": "Rolling logistic: combined; max_edge selection among the allowed outcomes at best individual-book quotes. Require selected model expected return strictly above 5%; stake 0.25 Kelly, per-bet cap 2%.","diagnostic": false,"fixed_stake": 1000.0,"kelly_fraction": 0.25,"max_bet_fraction": 0.02,"max_odds": null,"min_edge": 0.05,"min_odds": null,"model_key": "logit_combined","model_label": "Rolling logistic: combined","name": "Rolling logistic: combined | predeclared 5% edge | best individual-book quotes | 0.25 Kelly, per-bet cap 2%","odds_mode": "best","origin": "legacy","policy_family": "predeclared 5% edge","selection_rule": "max_edge","staking": "kelly","strategy_id": "S024","study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}
```

### S025 — Rolling market residual: team | predeclared 5% edge | best individual-book quotes | flat 1,000

Origin: legacy.

Frozen rolling-study market-residual probabilities; feature group team_only. Choose the eligible H/D/A outcome with largest p×odds−1. Use best eligible individual-book prices. Apply outcomes H, D, A and no decimal-odds bounds before outcome choice. Require selected p×odds−1 strictly above 5.00%. Request a fixed stake of 1,000 monetary units. Scale same-date requests proportionally to available cash; no extra date cap.

Exact configuration:

```json
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle","allowed_outcomes": ["H","D","A"],"bankroll_fraction": 0.01,"cash_only": false,"consensus_min": null,"consensus_model_keys": [],"date_cap_fraction": null,"description": "Rolling market residual: team; max_edge selection among the allowed outcomes at best individual-book quotes. Require selected model expected return strictly above 5%; stake flat 1,000.","diagnostic": false,"fixed_stake": 1000.0,"kelly_fraction": 0.25,"max_bet_fraction": 0.02,"max_odds": null,"min_edge": 0.05,"min_odds": null,"model_key": "residual_team_only","model_label": "Rolling market residual: team","name": "Rolling market residual: team | predeclared 5% edge | best individual-book quotes | flat 1,000","odds_mode": "best","origin": "legacy","policy_family": "predeclared 5% edge","selection_rule": "max_edge","staking": "fixed","strategy_id": "S025","study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}
```

### S026 — Rolling market residual: team | predeclared 5% edge | best individual-book quotes | 0.25 Kelly, per-bet cap 2%

Origin: legacy.

Frozen rolling-study market-residual probabilities; feature group team_only. Choose the eligible H/D/A outcome with largest p×odds−1. Use best eligible individual-book prices. Apply outcomes H, D, A and no decimal-odds bounds before outcome choice. Require selected p×odds−1 strictly above 5.00%. Request B×min(cap, f×max((p×odds−1)/(odds−1),0)), where B is date-start balance, f=0.2500 and cap=2.00%. Scale same-date requests proportionally to available cash; no extra date cap.

Exact configuration:

```json
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle","allowed_outcomes": ["H","D","A"],"bankroll_fraction": 0.01,"cash_only": false,"consensus_min": null,"consensus_model_keys": [],"date_cap_fraction": null,"description": "Rolling market residual: team; max_edge selection among the allowed outcomes at best individual-book quotes. Require selected model expected return strictly above 5%; stake 0.25 Kelly, per-bet cap 2%.","diagnostic": false,"fixed_stake": 1000.0,"kelly_fraction": 0.25,"max_bet_fraction": 0.02,"max_odds": null,"min_edge": 0.05,"min_odds": null,"model_key": "residual_team_only","model_label": "Rolling market residual: team","name": "Rolling market residual: team | predeclared 5% edge | best individual-book quotes | 0.25 Kelly, per-bet cap 2%","odds_mode": "best","origin": "legacy","policy_family": "predeclared 5% edge","selection_rule": "max_edge","staking": "kelly","strategy_id": "S026","study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}
```

### S027 — Rolling market residual: team + xG | predeclared 5% edge | best individual-book quotes | flat 1,000

Origin: legacy.

Frozen rolling-study market-residual probabilities; feature group team_xg. Choose the eligible H/D/A outcome with largest p×odds−1. Use best eligible individual-book prices. Apply outcomes H, D, A and no decimal-odds bounds before outcome choice. Require selected p×odds−1 strictly above 5.00%. Request a fixed stake of 1,000 monetary units. Scale same-date requests proportionally to available cash; no extra date cap.

Exact configuration:

```json
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle","allowed_outcomes": ["H","D","A"],"bankroll_fraction": 0.01,"cash_only": false,"consensus_min": null,"consensus_model_keys": [],"date_cap_fraction": null,"description": "Rolling market residual: team + xG; max_edge selection among the allowed outcomes at best individual-book quotes. Require selected model expected return strictly above 5%; stake flat 1,000.","diagnostic": false,"fixed_stake": 1000.0,"kelly_fraction": 0.25,"max_bet_fraction": 0.02,"max_odds": null,"min_edge": 0.05,"min_odds": null,"model_key": "residual_team_xg","model_label": "Rolling market residual: team + xG","name": "Rolling market residual: team + xG | predeclared 5% edge | best individual-book quotes | flat 1,000","odds_mode": "best","origin": "legacy","policy_family": "predeclared 5% edge","selection_rule": "max_edge","staking": "fixed","strategy_id": "S027","study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}
```

### S028 — Rolling market residual: team + xG | predeclared 5% edge | best individual-book quotes | 0.25 Kelly, per-bet cap 2%

Origin: legacy.

Frozen rolling-study market-residual probabilities; feature group team_xg. Choose the eligible H/D/A outcome with largest p×odds−1. Use best eligible individual-book prices. Apply outcomes H, D, A and no decimal-odds bounds before outcome choice. Require selected p×odds−1 strictly above 5.00%. Request B×min(cap, f×max((p×odds−1)/(odds−1),0)), where B is date-start balance, f=0.2500 and cap=2.00%. Scale same-date requests proportionally to available cash; no extra date cap.

Exact configuration:

```json
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle","allowed_outcomes": ["H","D","A"],"bankroll_fraction": 0.01,"cash_only": false,"consensus_min": null,"consensus_model_keys": [],"date_cap_fraction": null,"description": "Rolling market residual: team + xG; max_edge selection among the allowed outcomes at best individual-book quotes. Require selected model expected return strictly above 5%; stake 0.25 Kelly, per-bet cap 2%.","diagnostic": false,"fixed_stake": 1000.0,"kelly_fraction": 0.25,"max_bet_fraction": 0.02,"max_odds": null,"min_edge": 0.05,"min_odds": null,"model_key": "residual_team_xg","model_label": "Rolling market residual: team + xG","name": "Rolling market residual: team + xG | predeclared 5% edge | best individual-book quotes | 0.25 Kelly, per-bet cap 2%","odds_mode": "best","origin": "legacy","policy_family": "predeclared 5% edge","selection_rule": "max_edge","staking": "kelly","strategy_id": "S028","study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}
```

### S029 — Rolling market residual: team + player | predeclared 5% edge | best individual-book quotes | flat 1,000

Origin: legacy.

Frozen rolling-study market-residual probabilities; feature group team_players. Choose the eligible H/D/A outcome with largest p×odds−1. Use best eligible individual-book prices. Apply outcomes H, D, A and no decimal-odds bounds before outcome choice. Require selected p×odds−1 strictly above 5.00%. Request a fixed stake of 1,000 monetary units. Scale same-date requests proportionally to available cash; no extra date cap.

Exact configuration:

```json
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle","allowed_outcomes": ["H","D","A"],"bankroll_fraction": 0.01,"cash_only": false,"consensus_min": null,"consensus_model_keys": [],"date_cap_fraction": null,"description": "Rolling market residual: team + player; max_edge selection among the allowed outcomes at best individual-book quotes. Require selected model expected return strictly above 5%; stake flat 1,000.","diagnostic": false,"fixed_stake": 1000.0,"kelly_fraction": 0.25,"max_bet_fraction": 0.02,"max_odds": null,"min_edge": 0.05,"min_odds": null,"model_key": "residual_team_players","model_label": "Rolling market residual: team + player","name": "Rolling market residual: team + player | predeclared 5% edge | best individual-book quotes | flat 1,000","odds_mode": "best","origin": "legacy","policy_family": "predeclared 5% edge","selection_rule": "max_edge","staking": "fixed","strategy_id": "S029","study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}
```

### S030 — Rolling market residual: team + player | predeclared 5% edge | best individual-book quotes | 0.25 Kelly, per-bet cap 2%

Origin: legacy.

Frozen rolling-study market-residual probabilities; feature group team_players. Choose the eligible H/D/A outcome with largest p×odds−1. Use best eligible individual-book prices. Apply outcomes H, D, A and no decimal-odds bounds before outcome choice. Require selected p×odds−1 strictly above 5.00%. Request B×min(cap, f×max((p×odds−1)/(odds−1),0)), where B is date-start balance, f=0.2500 and cap=2.00%. Scale same-date requests proportionally to available cash; no extra date cap.

Exact configuration:

```json
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle","allowed_outcomes": ["H","D","A"],"bankroll_fraction": 0.01,"cash_only": false,"consensus_min": null,"consensus_model_keys": [],"date_cap_fraction": null,"description": "Rolling market residual: team + player; max_edge selection among the allowed outcomes at best individual-book quotes. Require selected model expected return strictly above 5%; stake 0.25 Kelly, per-bet cap 2%.","diagnostic": false,"fixed_stake": 1000.0,"kelly_fraction": 0.25,"max_bet_fraction": 0.02,"max_odds": null,"min_edge": 0.05,"min_odds": null,"model_key": "residual_team_players","model_label": "Rolling market residual: team + player","name": "Rolling market residual: team + player | predeclared 5% edge | best individual-book quotes | 0.25 Kelly, per-bet cap 2%","odds_mode": "best","origin": "legacy","policy_family": "predeclared 5% edge","selection_rule": "max_edge","staking": "kelly","strategy_id": "S030","study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}
```

### S031 — Rolling market residual: combined | predeclared 5% edge | best individual-book quotes | flat 1,000

Origin: legacy.

Frozen rolling-study market-residual probabilities; feature group combined. Choose the eligible H/D/A outcome with largest p×odds−1. Use best eligible individual-book prices. Apply outcomes H, D, A and no decimal-odds bounds before outcome choice. Require selected p×odds−1 strictly above 5.00%. Request a fixed stake of 1,000 monetary units. Scale same-date requests proportionally to available cash; no extra date cap.

Exact configuration:

```json
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle","allowed_outcomes": ["H","D","A"],"bankroll_fraction": 0.01,"cash_only": false,"consensus_min": null,"consensus_model_keys": [],"date_cap_fraction": null,"description": "Rolling market residual: combined; max_edge selection among the allowed outcomes at best individual-book quotes. Require selected model expected return strictly above 5%; stake flat 1,000.","diagnostic": false,"fixed_stake": 1000.0,"kelly_fraction": 0.25,"max_bet_fraction": 0.02,"max_odds": null,"min_edge": 0.05,"min_odds": null,"model_key": "residual_combined","model_label": "Rolling market residual: combined","name": "Rolling market residual: combined | predeclared 5% edge | best individual-book quotes | flat 1,000","odds_mode": "best","origin": "legacy","policy_family": "predeclared 5% edge","selection_rule": "max_edge","staking": "fixed","strategy_id": "S031","study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}
```

### S032 — Rolling market residual: combined | predeclared 5% edge | best individual-book quotes | 0.25 Kelly, per-bet cap 2%

Origin: legacy.

Frozen rolling-study market-residual probabilities; feature group combined. Choose the eligible H/D/A outcome with largest p×odds−1. Use best eligible individual-book prices. Apply outcomes H, D, A and no decimal-odds bounds before outcome choice. Require selected p×odds−1 strictly above 5.00%. Request B×min(cap, f×max((p×odds−1)/(odds−1),0)), where B is date-start balance, f=0.2500 and cap=2.00%. Scale same-date requests proportionally to available cash; no extra date cap.

Exact configuration:

```json
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle","allowed_outcomes": ["H","D","A"],"bankroll_fraction": 0.01,"cash_only": false,"consensus_min": null,"consensus_model_keys": [],"date_cap_fraction": null,"description": "Rolling market residual: combined; max_edge selection among the allowed outcomes at best individual-book quotes. Require selected model expected return strictly above 5%; stake 0.25 Kelly, per-bet cap 2%.","diagnostic": false,"fixed_stake": 1000.0,"kelly_fraction": 0.25,"max_bet_fraction": 0.02,"max_odds": null,"min_edge": 0.05,"min_odds": null,"model_key": "residual_combined","model_label": "Rolling market residual: combined","name": "Rolling market residual: combined | predeclared 5% edge | best individual-book quotes | 0.25 Kelly, per-bet cap 2%","odds_mode": "best","origin": "legacy","policy_family": "predeclared 5% edge","selection_rule": "max_edge","staking": "kelly","strategy_id": "S032","study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}
```

### S033 — Rolling training-class frequency | predeclared 5% edge | best individual-book quotes | flat 1,000

Origin: legacy.

Rolling-study training-class-frequency probabilities. Choose the eligible H/D/A outcome with largest p×odds−1. Use best eligible individual-book prices. Apply outcomes H, D, A and no decimal-odds bounds before outcome choice. Require selected p×odds−1 strictly above 5.00%. Request a fixed stake of 1,000 monetary units. Scale same-date requests proportionally to available cash; no extra date cap.

Exact configuration:

```json
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle","allowed_outcomes": ["H","D","A"],"bankroll_fraction": 0.01,"cash_only": false,"consensus_min": null,"consensus_model_keys": [],"date_cap_fraction": null,"description": "Rolling training-class frequency; max_edge selection among the allowed outcomes at best individual-book quotes. Require selected model expected return strictly above 5%; stake flat 1,000.","diagnostic": false,"fixed_stake": 1000.0,"kelly_fraction": 0.25,"max_bet_fraction": 0.02,"max_odds": null,"min_edge": 0.05,"min_odds": null,"model_key": "baseline_class_frequency","model_label": "Rolling training-class frequency","name": "Rolling training-class frequency | predeclared 5% edge | best individual-book quotes | flat 1,000","odds_mode": "best","origin": "legacy","policy_family": "predeclared 5% edge","selection_rule": "max_edge","staking": "fixed","strategy_id": "S033","study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}
```

### S034 — Rolling training-class frequency | predeclared 5% edge | best individual-book quotes | 0.25 Kelly, per-bet cap 2%

Origin: legacy.

Rolling-study training-class-frequency probabilities. Choose the eligible H/D/A outcome with largest p×odds−1. Use best eligible individual-book prices. Apply outcomes H, D, A and no decimal-odds bounds before outcome choice. Require selected p×odds−1 strictly above 5.00%. Request B×min(cap, f×max((p×odds−1)/(odds−1),0)), where B is date-start balance, f=0.2500 and cap=2.00%. Scale same-date requests proportionally to available cash; no extra date cap.

Exact configuration:

```json
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle","allowed_outcomes": ["H","D","A"],"bankroll_fraction": 0.01,"cash_only": false,"consensus_min": null,"consensus_model_keys": [],"date_cap_fraction": null,"description": "Rolling training-class frequency; max_edge selection among the allowed outcomes at best individual-book quotes. Require selected model expected return strictly above 5%; stake 0.25 Kelly, per-bet cap 2%.","diagnostic": false,"fixed_stake": 1000.0,"kelly_fraction": 0.25,"max_bet_fraction": 0.02,"max_odds": null,"min_edge": 0.05,"min_odds": null,"model_key": "baseline_class_frequency","model_label": "Rolling training-class frequency","name": "Rolling training-class frequency | predeclared 5% edge | best individual-book quotes | 0.25 Kelly, per-bet cap 2%","odds_mode": "best","origin": "legacy","policy_family": "predeclared 5% edge","selection_rule": "max_edge","staking": "kelly","strategy_id": "S034","study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}
```

### S035 — Raw de-vigged Bet365 market | predeclared 5% edge | best individual-book quotes | flat 1,000

Origin: legacy.

Raw normalized inverse Bet365 reference-price probabilities. Choose the eligible H/D/A outcome with largest p×odds−1. Use best eligible individual-book prices. Apply outcomes H, D, A and no decimal-odds bounds before outcome choice. Require selected p×odds−1 strictly above 5.00%. Request a fixed stake of 1,000 monetary units. Scale same-date requests proportionally to available cash; no extra date cap.

Exact configuration:

```json
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle","allowed_outcomes": ["H","D","A"],"bankroll_fraction": 0.01,"cash_only": false,"consensus_min": null,"consensus_model_keys": [],"date_cap_fraction": null,"description": "Raw de-vigged Bet365 market; max_edge selection among the allowed outcomes at best individual-book quotes. Require selected model expected return strictly above 5%; stake flat 1,000.","diagnostic": false,"fixed_stake": 1000.0,"kelly_fraction": 0.25,"max_bet_fraction": 0.02,"max_odds": null,"min_edge": 0.05,"min_odds": null,"model_key": "baseline_market_only","model_label": "Raw de-vigged Bet365 market","name": "Raw de-vigged Bet365 market | predeclared 5% edge | best individual-book quotes | flat 1,000","odds_mode": "best","origin": "legacy","policy_family": "predeclared 5% edge","selection_rule": "max_edge","staking": "fixed","strategy_id": "S035","study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}
```

### S036 — Raw de-vigged Bet365 market | predeclared 5% edge | best individual-book quotes | 0.25 Kelly, per-bet cap 2%

Origin: legacy.

Raw normalized inverse Bet365 reference-price probabilities. Choose the eligible H/D/A outcome with largest p×odds−1. Use best eligible individual-book prices. Apply outcomes H, D, A and no decimal-odds bounds before outcome choice. Require selected p×odds−1 strictly above 5.00%. Request B×min(cap, f×max((p×odds−1)/(odds−1),0)), where B is date-start balance, f=0.2500 and cap=2.00%. Scale same-date requests proportionally to available cash; no extra date cap.

Exact configuration:

```json
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle","allowed_outcomes": ["H","D","A"],"bankroll_fraction": 0.01,"cash_only": false,"consensus_min": null,"consensus_model_keys": [],"date_cap_fraction": null,"description": "Raw de-vigged Bet365 market; max_edge selection among the allowed outcomes at best individual-book quotes. Require selected model expected return strictly above 5%; stake 0.25 Kelly, per-bet cap 2%.","diagnostic": false,"fixed_stake": 1000.0,"kelly_fraction": 0.25,"max_bet_fraction": 0.02,"max_odds": null,"min_edge": 0.05,"min_odds": null,"model_key": "baseline_market_only","model_label": "Raw de-vigged Bet365 market","name": "Raw de-vigged Bet365 market | predeclared 5% edge | best individual-book quotes | 0.25 Kelly, per-bet cap 2%","odds_mode": "best","origin": "legacy","policy_family": "predeclared 5% edge","selection_rule": "max_edge","staking": "kelly","strategy_id": "S036","study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}
```

### S037 — Temperature-calibrated Bet365 market | predeclared 5% edge | best individual-book quotes | flat 1,000

Origin: legacy.

Rolling-study held-out-temperature-adjusted reference-market probabilities. Choose the eligible H/D/A outcome with largest p×odds−1. Use best eligible individual-book prices. Apply outcomes H, D, A and no decimal-odds bounds before outcome choice. Require selected p×odds−1 strictly above 5.00%. Request a fixed stake of 1,000 monetary units. Scale same-date requests proportionally to available cash; no extra date cap.

Exact configuration:

```json
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle","allowed_outcomes": ["H","D","A"],"bankroll_fraction": 0.01,"cash_only": false,"consensus_min": null,"consensus_model_keys": [],"date_cap_fraction": null,"description": "Temperature-calibrated Bet365 market; max_edge selection among the allowed outcomes at best individual-book quotes. Require selected model expected return strictly above 5%; stake flat 1,000.","diagnostic": false,"fixed_stake": 1000.0,"kelly_fraction": 0.25,"max_bet_fraction": 0.02,"max_odds": null,"min_edge": 0.05,"min_odds": null,"model_key": "market_temperature","model_label": "Temperature-calibrated Bet365 market","name": "Temperature-calibrated Bet365 market | predeclared 5% edge | best individual-book quotes | flat 1,000","odds_mode": "best","origin": "legacy","policy_family": "predeclared 5% edge","selection_rule": "max_edge","staking": "fixed","strategy_id": "S037","study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}
```

### S038 — Temperature-calibrated Bet365 market | predeclared 5% edge | best individual-book quotes | 0.25 Kelly, per-bet cap 2%

Origin: legacy.

Rolling-study held-out-temperature-adjusted reference-market probabilities. Choose the eligible H/D/A outcome with largest p×odds−1. Use best eligible individual-book prices. Apply outcomes H, D, A and no decimal-odds bounds before outcome choice. Require selected p×odds−1 strictly above 5.00%. Request B×min(cap, f×max((p×odds−1)/(odds−1),0)), where B is date-start balance, f=0.2500 and cap=2.00%. Scale same-date requests proportionally to available cash; no extra date cap.

Exact configuration:

```json
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle","allowed_outcomes": ["H","D","A"],"bankroll_fraction": 0.01,"cash_only": false,"consensus_min": null,"consensus_model_keys": [],"date_cap_fraction": null,"description": "Temperature-calibrated Bet365 market; max_edge selection among the allowed outcomes at best individual-book quotes. Require selected model expected return strictly above 5%; stake 0.25 Kelly, per-bet cap 2%.","diagnostic": false,"fixed_stake": 1000.0,"kelly_fraction": 0.25,"max_bet_fraction": 0.02,"max_odds": null,"min_edge": 0.05,"min_odds": null,"model_key": "market_temperature","model_label": "Temperature-calibrated Bet365 market","name": "Temperature-calibrated Bet365 market | predeclared 5% edge | best individual-book quotes | 0.25 Kelly, per-bet cap 2%","odds_mode": "best","origin": "legacy","policy_family": "predeclared 5% edge","selection_rule": "max_edge","staking": "kelly","strategy_id": "S038","study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}
```

### S039 — Always H | best quotes | flat 1,000

Origin: new.

Raw normalized inverse Bet365 reference-price probabilities. Choose the configured eligible outcome class. Use best eligible individual-book prices. Apply outcomes H and no decimal-odds bounds before outcome choice. No edge qualification is required. Request a fixed stake of 1,000 monetary units. Scale same-date requests proportionally to available cash; no extra date cap.

Exact configuration:

```json
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle","allowed_outcomes": ["H"],"bankroll_fraction": 0.01,"cash_only": false,"consensus_min": null,"consensus_model_keys": [],"date_cap_fraction": null,"description": "Back H on every priced fixture at its best archived individual-book quote, with flat stake 1,000 and no edge filter; market probability is descriptive only.","diagnostic": false,"fixed_stake": 1000.0,"kelly_fraction": 0.25,"max_bet_fraction": 0.02,"max_odds": null,"min_edge": null,"min_odds": null,"model_key": "baseline_market_only","model_label": "Raw de-vigged Bet365 market","name": "Always H | best quotes | flat 1,000","odds_mode": "best","origin": "new","policy_family": "unconditional class benchmark","selection_rule": "fixed_outcome","staking": "fixed","strategy_id": "S039","study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}
```

### S040 — Always D | best quotes | flat 1,000

Origin: new.

Raw normalized inverse Bet365 reference-price probabilities. Choose the configured eligible outcome class. Use best eligible individual-book prices. Apply outcomes D and no decimal-odds bounds before outcome choice. No edge qualification is required. Request a fixed stake of 1,000 monetary units. Scale same-date requests proportionally to available cash; no extra date cap.

Exact configuration:

```json
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle","allowed_outcomes": ["D"],"bankroll_fraction": 0.01,"cash_only": false,"consensus_min": null,"consensus_model_keys": [],"date_cap_fraction": null,"description": "Back D on every priced fixture at its best archived individual-book quote, with flat stake 1,000 and no edge filter; market probability is descriptive only.","diagnostic": false,"fixed_stake": 1000.0,"kelly_fraction": 0.25,"max_bet_fraction": 0.02,"max_odds": null,"min_edge": null,"min_odds": null,"model_key": "baseline_market_only","model_label": "Raw de-vigged Bet365 market","name": "Always D | best quotes | flat 1,000","odds_mode": "best","origin": "new","policy_family": "unconditional class benchmark","selection_rule": "fixed_outcome","staking": "fixed","strategy_id": "S040","study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}
```

### S041 — Always A | best quotes | flat 1,000

Origin: new.

Raw normalized inverse Bet365 reference-price probabilities. Choose the configured eligible outcome class. Use best eligible individual-book prices. Apply outcomes A and no decimal-odds bounds before outcome choice. No edge qualification is required. Request a fixed stake of 1,000 monetary units. Scale same-date requests proportionally to available cash; no extra date cap.

Exact configuration:

```json
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle","allowed_outcomes": ["A"],"bankroll_fraction": 0.01,"cash_only": false,"consensus_min": null,"consensus_model_keys": [],"date_cap_fraction": null,"description": "Back A on every priced fixture at its best archived individual-book quote, with flat stake 1,000 and no edge filter; market probability is descriptive only.","diagnostic": false,"fixed_stake": 1000.0,"kelly_fraction": 0.25,"max_bet_fraction": 0.02,"max_odds": null,"min_edge": null,"min_odds": null,"model_key": "baseline_market_only","model_label": "Raw de-vigged Bet365 market","name": "Always A | best quotes | flat 1,000","odds_mode": "best","origin": "new","policy_family": "unconditional class benchmark","selection_rule": "fixed_outcome","staking": "fixed","strategy_id": "S041","study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}
```

### S042 — Market favorite | best quotes | flat 1,000

Origin: new.

Raw normalized inverse Bet365 reference-price probabilities. Choose the eligible outcome with greatest raw reference-market probability. Use best eligible individual-book prices. Apply outcomes H, D, A and no decimal-odds bounds before outcome choice. No edge qualification is required. Request a fixed stake of 1,000 monetary units. Scale same-date requests proportionally to available cash; no extra date cap.

Exact configuration:

```json
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle","allowed_outcomes": ["H","D","A"],"bankroll_fraction": 0.01,"cash_only": false,"consensus_min": null,"consensus_model_keys": [],"date_cap_fraction": null,"description": "Choose the highest raw de-vigged Bet365 probability, then use that outcome's best archived quote and flat stake 1,000; no edge filter.","diagnostic": false,"fixed_stake": 1000.0,"kelly_fraction": 0.25,"max_bet_fraction": 0.02,"max_odds": null,"min_edge": null,"min_odds": null,"model_key": "baseline_market_only","model_label": "Raw de-vigged Bet365 market","name": "Market favorite | best quotes | flat 1,000","odds_mode": "best","origin": "new","policy_family": "unconditional market benchmark","selection_rule": "market_favorite","staking": "fixed","strategy_id": "S042","study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}
```

### S043 — Market underdog | best quotes | flat 1,000

Origin: new.

Raw normalized inverse Bet365 reference-price probabilities. Choose the eligible outcome with smallest raw reference-market probability. Use best eligible individual-book prices. Apply outcomes H, D, A and no decimal-odds bounds before outcome choice. No edge qualification is required. Request a fixed stake of 1,000 monetary units. Scale same-date requests proportionally to available cash; no extra date cap.

Exact configuration:

```json
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle","allowed_outcomes": ["H","D","A"],"bankroll_fraction": 0.01,"cash_only": false,"consensus_min": null,"consensus_model_keys": [],"date_cap_fraction": null,"description": "Choose the lowest raw de-vigged Bet365 probability, then use that outcome's best archived quote and flat stake 1,000; no edge filter.","diagnostic": false,"fixed_stake": 1000.0,"kelly_fraction": 0.25,"max_bet_fraction": 0.02,"max_odds": null,"min_edge": null,"min_odds": null,"model_key": "baseline_market_only","model_label": "Raw de-vigged Bet365 market","name": "Market underdog | best quotes | flat 1,000","odds_mode": "best","origin": "new","policy_family": "unconditional market benchmark","selection_rule": "market_underdog","staking": "fixed","strategy_id": "S043","study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}
```

### S044 — Rolling logistic: combined | unconditional model favorite | best individual-book quotes | flat 1,000

Origin: new.

Frozen rolling-study logistic probabilities; feature group combined. Choose the eligible outcome with greatest model probability. Use best eligible individual-book prices. Apply outcomes H, D, A and no decimal-odds bounds before outcome choice. No edge qualification is required. Request a fixed stake of 1,000 monetary units. Scale same-date requests proportionally to available cash; no extra date cap.

Exact configuration:

```json
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle","allowed_outcomes": ["H","D","A"],"bankroll_fraction": 0.01,"cash_only": false,"consensus_min": null,"consensus_model_keys": [],"date_cap_fraction": null,"description": "Choose Rolling logistic: combined's highest-probability outcome at its best archived quote; flat stake 1,000 with no edge filter.","diagnostic": false,"fixed_stake": 1000.0,"kelly_fraction": 0.25,"max_bet_fraction": 0.02,"max_odds": null,"min_edge": null,"min_odds": null,"model_key": "logit_combined","model_label": "Rolling logistic: combined","name": "Rolling logistic: combined | unconditional model favorite | best individual-book quotes | flat 1,000","odds_mode": "best","origin": "new","policy_family": "unconditional model favorite","selection_rule": "model_favorite","staking": "fixed","strategy_id": "S044","study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}
```

### S045 — Rolling market residual: combined | unconditional model favorite | best individual-book quotes | flat 1,000

Origin: new.

Frozen rolling-study market-residual probabilities; feature group combined. Choose the eligible outcome with greatest model probability. Use best eligible individual-book prices. Apply outcomes H, D, A and no decimal-odds bounds before outcome choice. No edge qualification is required. Request a fixed stake of 1,000 monetary units. Scale same-date requests proportionally to available cash; no extra date cap.

Exact configuration:

```json
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle","allowed_outcomes": ["H","D","A"],"bankroll_fraction": 0.01,"cash_only": false,"consensus_min": null,"consensus_model_keys": [],"date_cap_fraction": null,"description": "Choose Rolling market residual: combined's highest-probability outcome at its best archived quote; flat stake 1,000 with no edge filter.","diagnostic": false,"fixed_stake": 1000.0,"kelly_fraction": 0.25,"max_bet_fraction": 0.02,"max_odds": null,"min_edge": null,"min_odds": null,"model_key": "residual_combined","model_label": "Rolling market residual: combined","name": "Rolling market residual: combined | unconditional model favorite | best individual-book quotes | flat 1,000","odds_mode": "best","origin": "new","policy_family": "unconditional model favorite","selection_rule": "model_favorite","staking": "fixed","strategy_id": "S045","study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}
```

### S046 — Equal-weight mean of four rolling logistic probabilities | ensemble 5% edge | best individual-book quotes | flat 1,000

Origin: new.

Equal-weight probability mean of logit_team_only, logit_team_xg, logit_team_players, logit_combined; each weight is 1/4. Choose the eligible H/D/A outcome with largest p×odds−1. Use best eligible individual-book prices. Apply outcomes H, D, A and no decimal-odds bounds before outcome choice. Require selected p×odds−1 strictly above 5.00%. Request a fixed stake of 1,000 monetary units. Scale same-date requests proportionally to available cash; no extra date cap.

Exact configuration:

```json
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle","allowed_outcomes": ["H","D","A"],"bankroll_fraction": 0.01,"cash_only": false,"consensus_min": null,"consensus_model_keys": [],"date_cap_fraction": null,"description": "Equal-weight mean of four rolling logistic probabilities; max_edge selection among the allowed outcomes at best individual-book quotes. Require selected model expected return strictly above 5%; stake flat 1,000.","diagnostic": false,"fixed_stake": 1000.0,"kelly_fraction": 0.25,"max_bet_fraction": 0.02,"max_odds": null,"min_edge": 0.05,"min_odds": null,"model_key": "ensemble_logit4","model_label": "Equal-weight mean of four rolling logistic probabilities","name": "Equal-weight mean of four rolling logistic probabilities | ensemble 5% edge | best individual-book quotes | flat 1,000","odds_mode": "best","origin": "new","policy_family": "ensemble 5% edge","selection_rule": "max_edge","staking": "fixed","strategy_id": "S046","study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}
```

### S047 — Equal-weight mean of four rolling logistic probabilities | ensemble 5% edge | best individual-book quotes | 0.25 Kelly, per-bet cap 2%

Origin: new.

Equal-weight probability mean of logit_team_only, logit_team_xg, logit_team_players, logit_combined; each weight is 1/4. Choose the eligible H/D/A outcome with largest p×odds−1. Use best eligible individual-book prices. Apply outcomes H, D, A and no decimal-odds bounds before outcome choice. Require selected p×odds−1 strictly above 5.00%. Request B×min(cap, f×max((p×odds−1)/(odds−1),0)), where B is date-start balance, f=0.2500 and cap=2.00%. Scale same-date requests proportionally to available cash; no extra date cap.

Exact configuration:

```json
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle","allowed_outcomes": ["H","D","A"],"bankroll_fraction": 0.01,"cash_only": false,"consensus_min": null,"consensus_model_keys": [],"date_cap_fraction": null,"description": "Equal-weight mean of four rolling logistic probabilities; max_edge selection among the allowed outcomes at best individual-book quotes. Require selected model expected return strictly above 5%; stake 0.25 Kelly, per-bet cap 2%.","diagnostic": false,"fixed_stake": 1000.0,"kelly_fraction": 0.25,"max_bet_fraction": 0.02,"max_odds": null,"min_edge": 0.05,"min_odds": null,"model_key": "ensemble_logit4","model_label": "Equal-weight mean of four rolling logistic probabilities","name": "Equal-weight mean of four rolling logistic probabilities | ensemble 5% edge | best individual-book quotes | 0.25 Kelly, per-bet cap 2%","odds_mode": "best","origin": "new","policy_family": "ensemble 5% edge","selection_rule": "max_edge","staking": "kelly","strategy_id": "S047","study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}
```

### S048 — Equal-weight mean of all eight rolling learned probabilities | ensemble 5% edge | best individual-book quotes | flat 1,000

Origin: new.

Equal-weight probability mean of logit_team_only, logit_team_xg, logit_team_players, logit_combined, residual_team_only, residual_team_xg, residual_team_players, residual_combined; each weight is 1/8. Choose the eligible H/D/A outcome with largest p×odds−1. Use best eligible individual-book prices. Apply outcomes H, D, A and no decimal-odds bounds before outcome choice. Require selected p×odds−1 strictly above 5.00%. Request a fixed stake of 1,000 monetary units. Scale same-date requests proportionally to available cash; no extra date cap.

Exact configuration:

```json
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle","allowed_outcomes": ["H","D","A"],"bankroll_fraction": 0.01,"cash_only": false,"consensus_min": null,"consensus_model_keys": [],"date_cap_fraction": null,"description": "Equal-weight mean of all eight rolling learned probabilities; max_edge selection among the allowed outcomes at best individual-book quotes. Require selected model expected return strictly above 5%; stake flat 1,000.","diagnostic": false,"fixed_stake": 1000.0,"kelly_fraction": 0.25,"max_bet_fraction": 0.02,"max_odds": null,"min_edge": 0.05,"min_odds": null,"model_key": "ensemble_learned8","model_label": "Equal-weight mean of all eight rolling learned probabilities","name": "Equal-weight mean of all eight rolling learned probabilities | ensemble 5% edge | best individual-book quotes | flat 1,000","odds_mode": "best","origin": "new","policy_family": "ensemble 5% edge","selection_rule": "max_edge","staking": "fixed","strategy_id": "S048","study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}
```

### S049 — Equal-weight mean of all eight rolling learned probabilities | ensemble 5% edge | best individual-book quotes | 0.25 Kelly, per-bet cap 2%

Origin: new.

Equal-weight probability mean of logit_team_only, logit_team_xg, logit_team_players, logit_combined, residual_team_only, residual_team_xg, residual_team_players, residual_combined; each weight is 1/8. Choose the eligible H/D/A outcome with largest p×odds−1. Use best eligible individual-book prices. Apply outcomes H, D, A and no decimal-odds bounds before outcome choice. Require selected p×odds−1 strictly above 5.00%. Request B×min(cap, f×max((p×odds−1)/(odds−1),0)), where B is date-start balance, f=0.2500 and cap=2.00%. Scale same-date requests proportionally to available cash; no extra date cap.

Exact configuration:

```json
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle","allowed_outcomes": ["H","D","A"],"bankroll_fraction": 0.01,"cash_only": false,"consensus_min": null,"consensus_model_keys": [],"date_cap_fraction": null,"description": "Equal-weight mean of all eight rolling learned probabilities; max_edge selection among the allowed outcomes at best individual-book quotes. Require selected model expected return strictly above 5%; stake 0.25 Kelly, per-bet cap 2%.","diagnostic": false,"fixed_stake": 1000.0,"kelly_fraction": 0.25,"max_bet_fraction": 0.02,"max_odds": null,"min_edge": 0.05,"min_odds": null,"model_key": "ensemble_learned8","model_label": "Equal-weight mean of all eight rolling learned probabilities","name": "Equal-weight mean of all eight rolling learned probabilities | ensemble 5% edge | best individual-book quotes | 0.25 Kelly, per-bet cap 2%","odds_mode": "best","origin": "new","policy_family": "ensemble 5% edge","selection_rule": "max_edge","staking": "kelly","strategy_id": "S049","study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}
```

### S050 — 50/50 combined logistic and raw de-vigged market probabilities | ensemble 5% edge | best individual-book quotes | flat 1,000

Origin: new.

Equal-weight probability mean of logit_combined, baseline_market_only; each weight is 1/2. Choose the eligible H/D/A outcome with largest p×odds−1. Use best eligible individual-book prices. Apply outcomes H, D, A and no decimal-odds bounds before outcome choice. Require selected p×odds−1 strictly above 5.00%. Request a fixed stake of 1,000 monetary units. Scale same-date requests proportionally to available cash; no extra date cap.

Exact configuration:

```json
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle","allowed_outcomes": ["H","D","A"],"bankroll_fraction": 0.01,"cash_only": false,"consensus_min": null,"consensus_model_keys": [],"date_cap_fraction": null,"description": "50/50 combined logistic and raw de-vigged market probabilities; max_edge selection among the allowed outcomes at best individual-book quotes. Require selected model expected return strictly above 5%; stake flat 1,000.","diagnostic": false,"fixed_stake": 1000.0,"kelly_fraction": 0.25,"max_bet_fraction": 0.02,"max_odds": null,"min_edge": 0.05,"min_odds": null,"model_key": "ensemble_market_blend","model_label": "50/50 combined logistic and raw de-vigged market probabilities","name": "50/50 combined logistic and raw de-vigged market probabilities | ensemble 5% edge | best individual-book quotes | flat 1,000","odds_mode": "best","origin": "new","policy_family": "ensemble 5% edge","selection_rule": "max_edge","staking": "fixed","strategy_id": "S050","study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}
```

### S051 — 50/50 combined logistic and raw de-vigged market probabilities | ensemble 5% edge | best individual-book quotes | 0.25 Kelly, per-bet cap 2%

Origin: new.

Equal-weight probability mean of logit_combined, baseline_market_only; each weight is 1/2. Choose the eligible H/D/A outcome with largest p×odds−1. Use best eligible individual-book prices. Apply outcomes H, D, A and no decimal-odds bounds before outcome choice. Require selected p×odds−1 strictly above 5.00%. Request B×min(cap, f×max((p×odds−1)/(odds−1),0)), where B is date-start balance, f=0.2500 and cap=2.00%. Scale same-date requests proportionally to available cash; no extra date cap.

Exact configuration:

```json
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle","allowed_outcomes": ["H","D","A"],"bankroll_fraction": 0.01,"cash_only": false,"consensus_min": null,"consensus_model_keys": [],"date_cap_fraction": null,"description": "50/50 combined logistic and raw de-vigged market probabilities; max_edge selection among the allowed outcomes at best individual-book quotes. Require selected model expected return strictly above 5%; stake 0.25 Kelly, per-bet cap 2%.","diagnostic": false,"fixed_stake": 1000.0,"kelly_fraction": 0.25,"max_bet_fraction": 0.02,"max_odds": null,"min_edge": 0.05,"min_odds": null,"model_key": "ensemble_market_blend","model_label": "50/50 combined logistic and raw de-vigged market probabilities","name": "50/50 combined logistic and raw de-vigged market probabilities | ensemble 5% edge | best individual-book quotes | 0.25 Kelly, per-bet cap 2%","odds_mode": "best","origin": "new","policy_family": "ensemble 5% edge","selection_rule": "max_edge","staking": "kelly","strategy_id": "S051","study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}
```

### S052 — Rolling logistic: combined | dynamic 1% stake | best individual-book quotes | dynamic 1% of date-start capital

Origin: new.

Frozen rolling-study logistic probabilities; feature group combined. Choose the eligible H/D/A outcome with largest p×odds−1. Use best eligible individual-book prices. Apply outcomes H, D, A and no decimal-odds bounds before outcome choice. Require selected p×odds−1 strictly above 5.00%. Request 1.00% of the date-start balance B. Scale same-date requests proportionally to available cash; no extra date cap.

Exact configuration:

```json
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle","allowed_outcomes": ["H","D","A"],"bankroll_fraction": 0.01,"cash_only": false,"consensus_min": null,"consensus_model_keys": [],"date_cap_fraction": null,"description": "Rolling logistic: combined; max_edge selection among the allowed outcomes at best individual-book quotes. Require selected model expected return strictly above 5%; stake dynamic 1% of date-start capital.","diagnostic": false,"fixed_stake": 1000.0,"kelly_fraction": 0.25,"max_bet_fraction": 0.02,"max_odds": null,"min_edge": 0.05,"min_odds": null,"model_key": "logit_combined","model_label": "Rolling logistic: combined","name": "Rolling logistic: combined | dynamic 1% stake | best individual-book quotes | dynamic 1% of date-start capital","odds_mode": "best","origin": "new","policy_family": "dynamic 1% stake","selection_rule": "max_edge","staking": "dynamic_fraction","strategy_id": "S052","study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}
```

### S053 — Rolling market residual: combined | dynamic 1% stake | best individual-book quotes | dynamic 1% of date-start capital

Origin: new.

Frozen rolling-study market-residual probabilities; feature group combined. Choose the eligible H/D/A outcome with largest p×odds−1. Use best eligible individual-book prices. Apply outcomes H, D, A and no decimal-odds bounds before outcome choice. Require selected p×odds−1 strictly above 5.00%. Request 1.00% of the date-start balance B. Scale same-date requests proportionally to available cash; no extra date cap.

Exact configuration:

```json
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle","allowed_outcomes": ["H","D","A"],"bankroll_fraction": 0.01,"cash_only": false,"consensus_min": null,"consensus_model_keys": [],"date_cap_fraction": null,"description": "Rolling market residual: combined; max_edge selection among the allowed outcomes at best individual-book quotes. Require selected model expected return strictly above 5%; stake dynamic 1% of date-start capital.","diagnostic": false,"fixed_stake": 1000.0,"kelly_fraction": 0.25,"max_bet_fraction": 0.02,"max_odds": null,"min_edge": 0.05,"min_odds": null,"model_key": "residual_combined","model_label": "Rolling market residual: combined","name": "Rolling market residual: combined | dynamic 1% stake | best individual-book quotes | dynamic 1% of date-start capital","odds_mode": "best","origin": "new","policy_family": "dynamic 1% stake","selection_rule": "max_edge","staking": "dynamic_fraction","strategy_id": "S053","study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}
```

### S054 — Equal-weight mean of all eight rolling learned probabilities | dynamic 1% stake | best individual-book quotes | dynamic 1% of date-start capital

Origin: new.

Equal-weight probability mean of logit_team_only, logit_team_xg, logit_team_players, logit_combined, residual_team_only, residual_team_xg, residual_team_players, residual_combined; each weight is 1/8. Choose the eligible H/D/A outcome with largest p×odds−1. Use best eligible individual-book prices. Apply outcomes H, D, A and no decimal-odds bounds before outcome choice. Require selected p×odds−1 strictly above 5.00%. Request 1.00% of the date-start balance B. Scale same-date requests proportionally to available cash; no extra date cap.

Exact configuration:

```json
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle","allowed_outcomes": ["H","D","A"],"bankroll_fraction": 0.01,"cash_only": false,"consensus_min": null,"consensus_model_keys": [],"date_cap_fraction": null,"description": "Equal-weight mean of all eight rolling learned probabilities; max_edge selection among the allowed outcomes at best individual-book quotes. Require selected model expected return strictly above 5%; stake dynamic 1% of date-start capital.","diagnostic": false,"fixed_stake": 1000.0,"kelly_fraction": 0.25,"max_bet_fraction": 0.02,"max_odds": null,"min_edge": 0.05,"min_odds": null,"model_key": "ensemble_learned8","model_label": "Equal-weight mean of all eight rolling learned probabilities","name": "Equal-weight mean of all eight rolling learned probabilities | dynamic 1% stake | best individual-book quotes | dynamic 1% of date-start capital","odds_mode": "best","origin": "new","policy_family": "dynamic 1% stake","selection_rule": "max_edge","staking": "dynamic_fraction","strategy_id": "S054","study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}
```

### S055 — Rolling logistic: combined | eighth Kelly, cap 1% | best individual-book quotes | 0.125 Kelly, per-bet cap 1%

Origin: new.

Frozen rolling-study logistic probabilities; feature group combined. Choose the eligible H/D/A outcome with largest p×odds−1. Use best eligible individual-book prices. Apply outcomes H, D, A and no decimal-odds bounds before outcome choice. Require selected p×odds−1 strictly above 5.00%. Request B×min(cap, f×max((p×odds−1)/(odds−1),0)), where B is date-start balance, f=0.1250 and cap=1.00%. Scale same-date requests proportionally to available cash; no extra date cap.

Exact configuration:

```json
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle","allowed_outcomes": ["H","D","A"],"bankroll_fraction": 0.01,"cash_only": false,"consensus_min": null,"consensus_model_keys": [],"date_cap_fraction": null,"description": "Rolling logistic: combined; max_edge selection among the allowed outcomes at best individual-book quotes. Require selected model expected return strictly above 5%; stake 0.125 Kelly, per-bet cap 1%.","diagnostic": false,"fixed_stake": 1000.0,"kelly_fraction": 0.125,"max_bet_fraction": 0.01,"max_odds": null,"min_edge": 0.05,"min_odds": null,"model_key": "logit_combined","model_label": "Rolling logistic: combined","name": "Rolling logistic: combined | eighth Kelly, cap 1% | best individual-book quotes | 0.125 Kelly, per-bet cap 1%","odds_mode": "best","origin": "new","policy_family": "eighth Kelly, cap 1%","selection_rule": "max_edge","staking": "kelly","strategy_id": "S055","study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}
```

### S056 — Rolling logistic: combined | half Kelly, cap 2% | best individual-book quotes | 0.5 Kelly, per-bet cap 2%

Origin: new.

Frozen rolling-study logistic probabilities; feature group combined. Choose the eligible H/D/A outcome with largest p×odds−1. Use best eligible individual-book prices. Apply outcomes H, D, A and no decimal-odds bounds before outcome choice. Require selected p×odds−1 strictly above 5.00%. Request B×min(cap, f×max((p×odds−1)/(odds−1),0)), where B is date-start balance, f=0.5000 and cap=2.00%. Scale same-date requests proportionally to available cash; no extra date cap.

Exact configuration:

```json
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle","allowed_outcomes": ["H","D","A"],"bankroll_fraction": 0.01,"cash_only": false,"consensus_min": null,"consensus_model_keys": [],"date_cap_fraction": null,"description": "Rolling logistic: combined; max_edge selection among the allowed outcomes at best individual-book quotes. Require selected model expected return strictly above 5%; stake 0.5 Kelly, per-bet cap 2%.","diagnostic": false,"fixed_stake": 1000.0,"kelly_fraction": 0.5,"max_bet_fraction": 0.02,"max_odds": null,"min_edge": 0.05,"min_odds": null,"model_key": "logit_combined","model_label": "Rolling logistic: combined","name": "Rolling logistic: combined | half Kelly, cap 2% | best individual-book quotes | 0.5 Kelly, per-bet cap 2%","odds_mode": "best","origin": "new","policy_family": "half Kelly, cap 2%","selection_rule": "max_edge","staking": "kelly","strategy_id": "S056","study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}
```

### S057 — Rolling market residual: combined | eighth Kelly, cap 1% | best individual-book quotes | 0.125 Kelly, per-bet cap 1%

Origin: new.

Frozen rolling-study market-residual probabilities; feature group combined. Choose the eligible H/D/A outcome with largest p×odds−1. Use best eligible individual-book prices. Apply outcomes H, D, A and no decimal-odds bounds before outcome choice. Require selected p×odds−1 strictly above 5.00%. Request B×min(cap, f×max((p×odds−1)/(odds−1),0)), where B is date-start balance, f=0.1250 and cap=1.00%. Scale same-date requests proportionally to available cash; no extra date cap.

Exact configuration:

```json
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle","allowed_outcomes": ["H","D","A"],"bankroll_fraction": 0.01,"cash_only": false,"consensus_min": null,"consensus_model_keys": [],"date_cap_fraction": null,"description": "Rolling market residual: combined; max_edge selection among the allowed outcomes at best individual-book quotes. Require selected model expected return strictly above 5%; stake 0.125 Kelly, per-bet cap 1%.","diagnostic": false,"fixed_stake": 1000.0,"kelly_fraction": 0.125,"max_bet_fraction": 0.01,"max_odds": null,"min_edge": 0.05,"min_odds": null,"model_key": "residual_combined","model_label": "Rolling market residual: combined","name": "Rolling market residual: combined | eighth Kelly, cap 1% | best individual-book quotes | 0.125 Kelly, per-bet cap 1%","odds_mode": "best","origin": "new","policy_family": "eighth Kelly, cap 1%","selection_rule": "max_edge","staking": "kelly","strategy_id": "S057","study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}
```

### S058 — Rolling market residual: combined | half Kelly, cap 2% | best individual-book quotes | 0.5 Kelly, per-bet cap 2%

Origin: new.

Frozen rolling-study market-residual probabilities; feature group combined. Choose the eligible H/D/A outcome with largest p×odds−1. Use best eligible individual-book prices. Apply outcomes H, D, A and no decimal-odds bounds before outcome choice. Require selected p×odds−1 strictly above 5.00%. Request B×min(cap, f×max((p×odds−1)/(odds−1),0)), where B is date-start balance, f=0.5000 and cap=2.00%. Scale same-date requests proportionally to available cash; no extra date cap.

Exact configuration:

```json
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle","allowed_outcomes": ["H","D","A"],"bankroll_fraction": 0.01,"cash_only": false,"consensus_min": null,"consensus_model_keys": [],"date_cap_fraction": null,"description": "Rolling market residual: combined; max_edge selection among the allowed outcomes at best individual-book quotes. Require selected model expected return strictly above 5%; stake 0.5 Kelly, per-bet cap 2%.","diagnostic": false,"fixed_stake": 1000.0,"kelly_fraction": 0.5,"max_bet_fraction": 0.02,"max_odds": null,"min_edge": 0.05,"min_odds": null,"model_key": "residual_combined","model_label": "Rolling market residual: combined","name": "Rolling market residual: combined | half Kelly, cap 2% | best individual-book quotes | 0.5 Kelly, per-bet cap 2%","odds_mode": "best","origin": "new","policy_family": "half Kelly, cap 2%","selection_rule": "max_edge","staking": "kelly","strategy_id": "S058","study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}
```

### S059 — Rolling logistic: combined | quarter Kelly, 10% date budget | best individual-book quotes | 0.25 Kelly, per-bet cap 2%

Origin: new.

Frozen rolling-study logistic probabilities; feature group combined. Choose the eligible H/D/A outcome with largest p×odds−1. Use best eligible individual-book prices. Apply outcomes H, D, A and no decimal-odds bounds before outcome choice. Require selected p×odds−1 strictly above 5.00%. Request B×min(cap, f×max((p×odds−1)/(odds−1),0)), where B is date-start balance, f=0.2500 and cap=2.00%. Scale all same-date requests proportionally to at most 10.00% of date-start cash.

Exact configuration:

```json
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle","allowed_outcomes": ["H","D","A"],"bankroll_fraction": 0.01,"cash_only": false,"consensus_min": null,"consensus_model_keys": [],"date_cap_fraction": 0.1,"description": "Select Rolling logistic: combined's maximum edge strictly above 5%. Use quarter Kelly capped at 2% per bet, then uniformly scale all same-date requests to at most 10% of date-start capital.","diagnostic": false,"fixed_stake": 1000.0,"kelly_fraction": 0.25,"max_bet_fraction": 0.02,"max_odds": null,"min_edge": 0.05,"min_odds": null,"model_key": "logit_combined","model_label": "Rolling logistic: combined","name": "Rolling logistic: combined | quarter Kelly, 10% date budget | best individual-book quotes | 0.25 Kelly, per-bet cap 2%","odds_mode": "best","origin": "new","policy_family": "quarter Kelly, 10% date budget","selection_rule": "max_edge","staking": "kelly","strategy_id": "S059","study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}
```

### S060 — Rolling market residual: combined | quarter Kelly, 10% date budget | best individual-book quotes | 0.25 Kelly, per-bet cap 2%

Origin: new.

Frozen rolling-study market-residual probabilities; feature group combined. Choose the eligible H/D/A outcome with largest p×odds−1. Use best eligible individual-book prices. Apply outcomes H, D, A and no decimal-odds bounds before outcome choice. Require selected p×odds−1 strictly above 5.00%. Request B×min(cap, f×max((p×odds−1)/(odds−1),0)), where B is date-start balance, f=0.2500 and cap=2.00%. Scale all same-date requests proportionally to at most 10.00% of date-start cash.

Exact configuration:

```json
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle","allowed_outcomes": ["H","D","A"],"bankroll_fraction": 0.01,"cash_only": false,"consensus_min": null,"consensus_model_keys": [],"date_cap_fraction": 0.1,"description": "Select Rolling market residual: combined's maximum edge strictly above 5%. Use quarter Kelly capped at 2% per bet, then uniformly scale all same-date requests to at most 10% of date-start capital.","diagnostic": false,"fixed_stake": 1000.0,"kelly_fraction": 0.25,"max_bet_fraction": 0.02,"max_odds": null,"min_edge": 0.05,"min_odds": null,"model_key": "residual_combined","model_label": "Rolling market residual: combined","name": "Rolling market residual: combined | quarter Kelly, 10% date budget | best individual-book quotes | 0.25 Kelly, per-bet cap 2%","odds_mode": "best","origin": "new","policy_family": "quarter Kelly, 10% date budget","selection_rule": "max_edge","staking": "kelly","strategy_id": "S060","study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}
```

### S061 — Equal-weight mean of all eight rolling learned probabilities | quarter Kelly, 10% date budget | best individual-book quotes | 0.25 Kelly, per-bet cap 2%

Origin: new.

Equal-weight probability mean of logit_team_only, logit_team_xg, logit_team_players, logit_combined, residual_team_only, residual_team_xg, residual_team_players, residual_combined; each weight is 1/8. Choose the eligible H/D/A outcome with largest p×odds−1. Use best eligible individual-book prices. Apply outcomes H, D, A and no decimal-odds bounds before outcome choice. Require selected p×odds−1 strictly above 5.00%. Request B×min(cap, f×max((p×odds−1)/(odds−1),0)), where B is date-start balance, f=0.2500 and cap=2.00%. Scale all same-date requests proportionally to at most 10.00% of date-start cash.

Exact configuration:

```json
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle","allowed_outcomes": ["H","D","A"],"bankroll_fraction": 0.01,"cash_only": false,"consensus_min": null,"consensus_model_keys": [],"date_cap_fraction": 0.1,"description": "Select Equal-weight mean of all eight rolling learned probabilities's maximum edge strictly above 5%. Use quarter Kelly capped at 2% per bet, then uniformly scale all same-date requests to at most 10% of date-start capital.","diagnostic": false,"fixed_stake": 1000.0,"kelly_fraction": 0.25,"max_bet_fraction": 0.02,"max_odds": null,"min_edge": 0.05,"min_odds": null,"model_key": "ensemble_learned8","model_label": "Equal-weight mean of all eight rolling learned probabilities","name": "Equal-weight mean of all eight rolling learned probabilities | quarter Kelly, 10% date budget | best individual-book quotes | 0.25 Kelly, per-bet cap 2%","odds_mode": "best","origin": "new","policy_family": "quarter Kelly, 10% date budget","selection_rule": "max_edge","staking": "kelly","strategy_id": "S061","study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}
```

### S062 — Equal-weight mean of all eight rolling learned probabilities | six-of-eight consensus | best individual-book quotes | flat 1,000

Origin: new.

Equal-weight probability mean of logit_team_only, logit_team_xg, logit_team_players, logit_combined, residual_team_only, residual_team_xg, residual_team_players, residual_combined; each weight is 1/8. Choose the eligible H/D/A outcome with largest p×odds−1. Use best eligible individual-book prices. Apply outcomes H, D, A and no decimal-odds bounds before outcome choice. Require selected p×odds−1 strictly above 5.00%. After choosing the mean-eight maximum-edge outcome, require at least 6 of 8 constituent models to have strictly positive edge at that same quote; otherwise abstain without searching another outcome. Request a fixed stake of 1,000 monetary units. Scale same-date requests proportionally to available cash; no extra date cap.

Exact configuration:

```json
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle","allowed_outcomes": ["H","D","A"],"bankroll_fraction": 0.01,"cash_only": false,"consensus_min": 6,"consensus_model_keys": ["logit_team_only","logit_team_xg","logit_team_players","logit_combined","residual_team_only","residual_team_xg","residual_team_players","residual_combined"],"date_cap_fraction": null,"description": "Choose the mean-eight maximum-edge outcome strictly above 5%; retain it only if at least six of the eight individual rolling learned models have strictly positive edge at that same selected best quote. A failed vote means no bet, without searching another class.","diagnostic": false,"fixed_stake": 1000.0,"kelly_fraction": 0.25,"max_bet_fraction": 0.02,"max_odds": null,"min_edge": 0.05,"min_odds": null,"model_key": "ensemble_learned8","model_label": "Equal-weight mean of all eight rolling learned probabilities","name": "Equal-weight mean of all eight rolling learned probabilities | six-of-eight consensus | best individual-book quotes | flat 1,000","odds_mode": "best","origin": "new","policy_family": "six-of-eight consensus","selection_rule": "max_edge","staking": "fixed","strategy_id": "S062","study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}
```

### S063 — Equal-weight mean of all eight rolling learned probabilities | six-of-eight consensus | best individual-book quotes | 0.25 Kelly, per-bet cap 2%

Origin: new.

Equal-weight probability mean of logit_team_only, logit_team_xg, logit_team_players, logit_combined, residual_team_only, residual_team_xg, residual_team_players, residual_combined; each weight is 1/8. Choose the eligible H/D/A outcome with largest p×odds−1. Use best eligible individual-book prices. Apply outcomes H, D, A and no decimal-odds bounds before outcome choice. Require selected p×odds−1 strictly above 5.00%. After choosing the mean-eight maximum-edge outcome, require at least 6 of 8 constituent models to have strictly positive edge at that same quote; otherwise abstain without searching another outcome. Request B×min(cap, f×max((p×odds−1)/(odds−1),0)), where B is date-start balance, f=0.2500 and cap=2.00%. Scale same-date requests proportionally to available cash; no extra date cap.

Exact configuration:

```json
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle","allowed_outcomes": ["H","D","A"],"bankroll_fraction": 0.01,"cash_only": false,"consensus_min": 6,"consensus_model_keys": ["logit_team_only","logit_team_xg","logit_team_players","logit_combined","residual_team_only","residual_team_xg","residual_team_players","residual_combined"],"date_cap_fraction": null,"description": "Choose the mean-eight maximum-edge outcome strictly above 5%; retain it only if at least six of the eight individual rolling learned models have strictly positive edge at that same selected best quote. A failed vote means no bet, without searching another class.","diagnostic": false,"fixed_stake": 1000.0,"kelly_fraction": 0.25,"max_bet_fraction": 0.02,"max_odds": null,"min_edge": 0.05,"min_odds": null,"model_key": "ensemble_learned8","model_label": "Equal-weight mean of all eight rolling learned probabilities","name": "Equal-weight mean of all eight rolling learned probabilities | six-of-eight consensus | best individual-book quotes | 0.25 Kelly, per-bet cap 2%","odds_mode": "best","origin": "new","policy_family": "six-of-eight consensus","selection_rule": "max_edge","staking": "kelly","strategy_id": "S063","study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}
```

### S064 — Equal-weight mean of all eight rolling learned probabilities | 5% edge, H only | best individual-book quotes | flat 1,000

Origin: new.

Equal-weight probability mean of logit_team_only, logit_team_xg, logit_team_players, logit_combined, residual_team_only, residual_team_xg, residual_team_players, residual_combined; each weight is 1/8. Choose the eligible H/D/A outcome with largest p×odds−1. Use best eligible individual-book prices. Apply outcomes H and no decimal-odds bounds before outcome choice. Require selected p×odds−1 strictly above 5.00%. Request a fixed stake of 1,000 monetary units. Scale same-date requests proportionally to available cash; no extra date cap.

Exact configuration:

```json
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle","allowed_outcomes": ["H"],"bankroll_fraction": 0.01,"cash_only": false,"consensus_min": null,"consensus_model_keys": [],"date_cap_fraction": null,"description": "Restrict candidates to outcome H before maximizing mean-eight edge; require strict edge above 5% and use flat stake 1,000 at its best archived quote.","diagnostic": false,"fixed_stake": 1000.0,"kelly_fraction": 0.25,"max_bet_fraction": 0.02,"max_odds": null,"min_edge": 0.05,"min_odds": null,"model_key": "ensemble_learned8","model_label": "Equal-weight mean of all eight rolling learned probabilities","name": "Equal-weight mean of all eight rolling learned probabilities | 5% edge, H only | best individual-book quotes | flat 1,000","odds_mode": "best","origin": "new","policy_family": "5% edge, H only","selection_rule": "max_edge","staking": "fixed","strategy_id": "S064","study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}
```

### S065 — Equal-weight mean of all eight rolling learned probabilities | 5% edge, D only | best individual-book quotes | flat 1,000

Origin: new.

Equal-weight probability mean of logit_team_only, logit_team_xg, logit_team_players, logit_combined, residual_team_only, residual_team_xg, residual_team_players, residual_combined; each weight is 1/8. Choose the eligible H/D/A outcome with largest p×odds−1. Use best eligible individual-book prices. Apply outcomes D and no decimal-odds bounds before outcome choice. Require selected p×odds−1 strictly above 5.00%. Request a fixed stake of 1,000 monetary units. Scale same-date requests proportionally to available cash; no extra date cap.

Exact configuration:

```json
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle","allowed_outcomes": ["D"],"bankroll_fraction": 0.01,"cash_only": false,"consensus_min": null,"consensus_model_keys": [],"date_cap_fraction": null,"description": "Restrict candidates to outcome D before maximizing mean-eight edge; require strict edge above 5% and use flat stake 1,000 at its best archived quote.","diagnostic": false,"fixed_stake": 1000.0,"kelly_fraction": 0.25,"max_bet_fraction": 0.02,"max_odds": null,"min_edge": 0.05,"min_odds": null,"model_key": "ensemble_learned8","model_label": "Equal-weight mean of all eight rolling learned probabilities","name": "Equal-weight mean of all eight rolling learned probabilities | 5% edge, D only | best individual-book quotes | flat 1,000","odds_mode": "best","origin": "new","policy_family": "5% edge, D only","selection_rule": "max_edge","staking": "fixed","strategy_id": "S065","study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}
```

### S066 — Equal-weight mean of all eight rolling learned probabilities | 5% edge, A only | best individual-book quotes | flat 1,000

Origin: new.

Equal-weight probability mean of logit_team_only, logit_team_xg, logit_team_players, logit_combined, residual_team_only, residual_team_xg, residual_team_players, residual_combined; each weight is 1/8. Choose the eligible H/D/A outcome with largest p×odds−1. Use best eligible individual-book prices. Apply outcomes A and no decimal-odds bounds before outcome choice. Require selected p×odds−1 strictly above 5.00%. Request a fixed stake of 1,000 monetary units. Scale same-date requests proportionally to available cash; no extra date cap.

Exact configuration:

```json
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle","allowed_outcomes": ["A"],"bankroll_fraction": 0.01,"cash_only": false,"consensus_min": null,"consensus_model_keys": [],"date_cap_fraction": null,"description": "Restrict candidates to outcome A before maximizing mean-eight edge; require strict edge above 5% and use flat stake 1,000 at its best archived quote.","diagnostic": false,"fixed_stake": 1000.0,"kelly_fraction": 0.25,"max_bet_fraction": 0.02,"max_odds": null,"min_edge": 0.05,"min_odds": null,"model_key": "ensemble_learned8","model_label": "Equal-weight mean of all eight rolling learned probabilities","name": "Equal-weight mean of all eight rolling learned probabilities | 5% edge, A only | best individual-book quotes | flat 1,000","odds_mode": "best","origin": "new","policy_family": "5% edge, A only","selection_rule": "max_edge","staking": "fixed","strategy_id": "S066","study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}
```

### S067 — Rolling logistic: combined | 10% edge | best individual-book quotes | flat 1,000

Origin: new.

Frozen rolling-study logistic probabilities; feature group combined. Choose the eligible H/D/A outcome with largest p×odds−1. Use best eligible individual-book prices. Apply outcomes H, D, A and no decimal-odds bounds before outcome choice. Require selected p×odds−1 strictly above 10.00%. Request a fixed stake of 1,000 monetary units. Scale same-date requests proportionally to available cash; no extra date cap.

Exact configuration:

```json
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle","allowed_outcomes": ["H","D","A"],"bankroll_fraction": 0.01,"cash_only": false,"consensus_min": null,"consensus_model_keys": [],"date_cap_fraction": null,"description": "Rolling logistic: combined; max_edge selection among the allowed outcomes at best individual-book quotes. Require selected model expected return strictly above 10%; stake flat 1,000.","diagnostic": false,"fixed_stake": 1000.0,"kelly_fraction": 0.25,"max_bet_fraction": 0.02,"max_odds": null,"min_edge": 0.1,"min_odds": null,"model_key": "logit_combined","model_label": "Rolling logistic: combined","name": "Rolling logistic: combined | 10% edge | best individual-book quotes | flat 1,000","odds_mode": "best","origin": "new","policy_family": "10% edge","selection_rule": "max_edge","staking": "fixed","strategy_id": "S067","study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}
```

### S068 — Rolling market residual: combined | 10% edge | best individual-book quotes | flat 1,000

Origin: new.

Frozen rolling-study market-residual probabilities; feature group combined. Choose the eligible H/D/A outcome with largest p×odds−1. Use best eligible individual-book prices. Apply outcomes H, D, A and no decimal-odds bounds before outcome choice. Require selected p×odds−1 strictly above 10.00%. Request a fixed stake of 1,000 monetary units. Scale same-date requests proportionally to available cash; no extra date cap.

Exact configuration:

```json
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle","allowed_outcomes": ["H","D","A"],"bankroll_fraction": 0.01,"cash_only": false,"consensus_min": null,"consensus_model_keys": [],"date_cap_fraction": null,"description": "Rolling market residual: combined; max_edge selection among the allowed outcomes at best individual-book quotes. Require selected model expected return strictly above 10%; stake flat 1,000.","diagnostic": false,"fixed_stake": 1000.0,"kelly_fraction": 0.25,"max_bet_fraction": 0.02,"max_odds": null,"min_edge": 0.1,"min_odds": null,"model_key": "residual_combined","model_label": "Rolling market residual: combined","name": "Rolling market residual: combined | 10% edge | best individual-book quotes | flat 1,000","odds_mode": "best","origin": "new","policy_family": "10% edge","selection_rule": "max_edge","staking": "fixed","strategy_id": "S068","study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}
```

### S069 — Equal-weight mean of all eight rolling learned probabilities | 10% edge | best individual-book quotes | flat 1,000

Origin: new.

Equal-weight probability mean of logit_team_only, logit_team_xg, logit_team_players, logit_combined, residual_team_only, residual_team_xg, residual_team_players, residual_combined; each weight is 1/8. Choose the eligible H/D/A outcome with largest p×odds−1. Use best eligible individual-book prices. Apply outcomes H, D, A and no decimal-odds bounds before outcome choice. Require selected p×odds−1 strictly above 10.00%. Request a fixed stake of 1,000 monetary units. Scale same-date requests proportionally to available cash; no extra date cap.

Exact configuration:

```json
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle","allowed_outcomes": ["H","D","A"],"bankroll_fraction": 0.01,"cash_only": false,"consensus_min": null,"consensus_model_keys": [],"date_cap_fraction": null,"description": "Equal-weight mean of all eight rolling learned probabilities; max_edge selection among the allowed outcomes at best individual-book quotes. Require selected model expected return strictly above 10%; stake flat 1,000.","diagnostic": false,"fixed_stake": 1000.0,"kelly_fraction": 0.25,"max_bet_fraction": 0.02,"max_odds": null,"min_edge": 0.1,"min_odds": null,"model_key": "ensemble_learned8","model_label": "Equal-weight mean of all eight rolling learned probabilities","name": "Equal-weight mean of all eight rolling learned probabilities | 10% edge | best individual-book quotes | flat 1,000","odds_mode": "best","origin": "new","policy_family": "10% edge","selection_rule": "max_edge","staking": "fixed","strategy_id": "S069","study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}
```

### S070 — Rolling logistic: combined | 5% edge, odds 1.5–5 | best individual-book quotes | flat 1,000

Origin: new.

Frozen rolling-study logistic probabilities; feature group combined. Choose the eligible H/D/A outcome with largest p×odds−1. Use best eligible individual-book prices. Apply outcomes H, D, A and inclusive decimal-odds range 1.50 to 5.00 before outcome choice. Require selected p×odds−1 strictly above 5.00%. Request a fixed stake of 1,000 monetary units. Scale same-date requests proportionally to available cash; no extra date cap.

Exact configuration:

```json
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle","allowed_outcomes": ["H","D","A"],"bankroll_fraction": 0.01,"cash_only": false,"consensus_min": null,"consensus_model_keys": [],"date_cap_fraction": null,"description": "Retain only outcomes with inclusive best-quote decimal odds from 1.5 to 5 before maximizing Rolling logistic: combined's edge. Require selected edge strictly above 5%; flat stake 1,000.","diagnostic": false,"fixed_stake": 1000.0,"kelly_fraction": 0.25,"max_bet_fraction": 0.02,"max_odds": 5.0,"min_edge": 0.05,"min_odds": 1.5,"model_key": "logit_combined","model_label": "Rolling logistic: combined","name": "Rolling logistic: combined | 5% edge, odds 1.5–5 | best individual-book quotes | flat 1,000","odds_mode": "best","origin": "new","policy_family": "5% edge, odds 1.5–5","selection_rule": "max_edge","staking": "fixed","strategy_id": "S070","study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}
```

### S071 — Rolling market residual: combined | 5% edge, odds 1.5–5 | best individual-book quotes | flat 1,000

Origin: new.

Frozen rolling-study market-residual probabilities; feature group combined. Choose the eligible H/D/A outcome with largest p×odds−1. Use best eligible individual-book prices. Apply outcomes H, D, A and inclusive decimal-odds range 1.50 to 5.00 before outcome choice. Require selected p×odds−1 strictly above 5.00%. Request a fixed stake of 1,000 monetary units. Scale same-date requests proportionally to available cash; no extra date cap.

Exact configuration:

```json
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle","allowed_outcomes": ["H","D","A"],"bankroll_fraction": 0.01,"cash_only": false,"consensus_min": null,"consensus_model_keys": [],"date_cap_fraction": null,"description": "Retain only outcomes with inclusive best-quote decimal odds from 1.5 to 5 before maximizing Rolling market residual: combined's edge. Require selected edge strictly above 5%; flat stake 1,000.","diagnostic": false,"fixed_stake": 1000.0,"kelly_fraction": 0.25,"max_bet_fraction": 0.02,"max_odds": 5.0,"min_edge": 0.05,"min_odds": 1.5,"model_key": "residual_combined","model_label": "Rolling market residual: combined","name": "Rolling market residual: combined | 5% edge, odds 1.5–5 | best individual-book quotes | flat 1,000","odds_mode": "best","origin": "new","policy_family": "5% edge, odds 1.5–5","selection_rule": "max_edge","staking": "fixed","strategy_id": "S071","study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}
```

### S072 — Equal-weight mean of all eight rolling learned probabilities | 5% edge, odds 1.5–5 | best individual-book quotes | flat 1,000

Origin: new.

Equal-weight probability mean of logit_team_only, logit_team_xg, logit_team_players, logit_combined, residual_team_only, residual_team_xg, residual_team_players, residual_combined; each weight is 1/8. Choose the eligible H/D/A outcome with largest p×odds−1. Use best eligible individual-book prices. Apply outcomes H, D, A and inclusive decimal-odds range 1.50 to 5.00 before outcome choice. Require selected p×odds−1 strictly above 5.00%. Request a fixed stake of 1,000 monetary units. Scale same-date requests proportionally to available cash; no extra date cap.

Exact configuration:

```json
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle","allowed_outcomes": ["H","D","A"],"bankroll_fraction": 0.01,"cash_only": false,"consensus_min": null,"consensus_model_keys": [],"date_cap_fraction": null,"description": "Retain only outcomes with inclusive best-quote decimal odds from 1.5 to 5 before maximizing Equal-weight mean of all eight rolling learned probabilities's edge. Require selected edge strictly above 5%; flat stake 1,000.","diagnostic": false,"fixed_stake": 1000.0,"kelly_fraction": 0.25,"max_bet_fraction": 0.02,"max_odds": 5.0,"min_edge": 0.05,"min_odds": 1.5,"model_key": "ensemble_learned8","model_label": "Equal-weight mean of all eight rolling learned probabilities","name": "Equal-weight mean of all eight rolling learned probabilities | 5% edge, odds 1.5–5 | best individual-book quotes | flat 1,000","odds_mode": "best","origin": "new","policy_family": "5% edge, odds 1.5–5","selection_rule": "max_edge","staking": "fixed","strategy_id": "S072","study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}
```

### S073 — First-study accuracy-selected SVM | historical threshold diagnostic 0% | best individual-book quotes | flat 1,000

Origin: legacy_diagnostic.

Frozen first-study accuracy-selected SVM. Choose the eligible H/D/A outcome with largest p×odds−1. Use best eligible individual-book prices. Apply outcomes H, D, A and no decimal-odds bounds before outcome choice. Require selected p×odds−1 strictly above 0.00%. Request a fixed stake of 1,000 monetary units. Scale same-date requests proportionally to available cash; no extra date cap. Historical threshold-diagnostic recipe replayed on this common period; not a newly selected primary rule.

Exact configuration:

```json
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle","allowed_outcomes": ["H","D","A"],"bankroll_fraction": 0.01,"cash_only": false,"consensus_min": null,"consensus_model_keys": [],"date_cap_fraction": null,"description": "Replay the saved First-study accuracy-selected SVM validation-candidate rule with edge strictly above 0% (p × odds − 1 > 0), best individual-book quotes and flat stake 1,000. This is an exploratory diagnostic replay on an already examined season, not the selected primary strategy.","diagnostic": true,"fixed_stake": 1000.0,"kelly_fraction": 0.25,"max_bet_fraction": 0.02,"max_odds": null,"min_edge": 0.0,"min_odds": null,"model_key": "first_accuracy","model_label": "First-study accuracy-selected SVM","name": "First-study accuracy-selected SVM | historical threshold diagnostic 0% | best individual-book quotes | flat 1,000","odds_mode": "best","origin": "legacy_diagnostic","policy_family": "historical threshold diagnostic 0%","selection_rule": "max_edge","staking": "fixed","strategy_id": "S073","study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}
```

### S074 — First-study accuracy-selected SVM | historical threshold diagnostic 2.5% | best individual-book quotes | flat 1,000

Origin: legacy_diagnostic.

Frozen first-study accuracy-selected SVM. Choose the eligible H/D/A outcome with largest p×odds−1. Use best eligible individual-book prices. Apply outcomes H, D, A and no decimal-odds bounds before outcome choice. Require selected p×odds−1 strictly above 2.50%. Request a fixed stake of 1,000 monetary units. Scale same-date requests proportionally to available cash; no extra date cap. Historical threshold-diagnostic recipe replayed on this common period; not a newly selected primary rule.

Exact configuration:

```json
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle","allowed_outcomes": ["H","D","A"],"bankroll_fraction": 0.01,"cash_only": false,"consensus_min": null,"consensus_model_keys": [],"date_cap_fraction": null,"description": "Replay the saved First-study accuracy-selected SVM validation-candidate rule with edge strictly above 2.5% (p × odds − 1 > 0.025), best individual-book quotes and flat stake 1,000. This is an exploratory diagnostic replay on an already examined season, not the selected primary strategy.","diagnostic": true,"fixed_stake": 1000.0,"kelly_fraction": 0.25,"max_bet_fraction": 0.02,"max_odds": null,"min_edge": 0.025,"min_odds": null,"model_key": "first_accuracy","model_label": "First-study accuracy-selected SVM","name": "First-study accuracy-selected SVM | historical threshold diagnostic 2.5% | best individual-book quotes | flat 1,000","odds_mode": "best","origin": "legacy_diagnostic","policy_family": "historical threshold diagnostic 2.5%","selection_rule": "max_edge","staking": "fixed","strategy_id": "S074","study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}
```

### S075 — First-study accuracy-selected SVM | historical threshold diagnostic 7.5% | best individual-book quotes | flat 1,000

Origin: legacy_diagnostic.

Frozen first-study accuracy-selected SVM. Choose the eligible H/D/A outcome with largest p×odds−1. Use best eligible individual-book prices. Apply outcomes H, D, A and no decimal-odds bounds before outcome choice. Require selected p×odds−1 strictly above 7.50%. Request a fixed stake of 1,000 monetary units. Scale same-date requests proportionally to available cash; no extra date cap. Historical threshold-diagnostic recipe replayed on this common period; not a newly selected primary rule.

Exact configuration:

```json
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle","allowed_outcomes": ["H","D","A"],"bankroll_fraction": 0.01,"cash_only": false,"consensus_min": null,"consensus_model_keys": [],"date_cap_fraction": null,"description": "Replay the saved First-study accuracy-selected SVM validation-candidate rule with edge strictly above 7.5% (p × odds − 1 > 0.075), best individual-book quotes and flat stake 1,000. This is an exploratory diagnostic replay on an already examined season, not the selected primary strategy.","diagnostic": true,"fixed_stake": 1000.0,"kelly_fraction": 0.25,"max_bet_fraction": 0.02,"max_odds": null,"min_edge": 0.075,"min_odds": null,"model_key": "first_accuracy","model_label": "First-study accuracy-selected SVM","name": "First-study accuracy-selected SVM | historical threshold diagnostic 7.5% | best individual-book quotes | flat 1,000","odds_mode": "best","origin": "legacy_diagnostic","policy_family": "historical threshold diagnostic 7.5%","selection_rule": "max_edge","staking": "fixed","strategy_id": "S075","study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}
```

### S076 — First-study accuracy-selected SVM | historical threshold diagnostic 10% | best individual-book quotes | flat 1,000

Origin: legacy_diagnostic.

Frozen first-study accuracy-selected SVM. Choose the eligible H/D/A outcome with largest p×odds−1. Use best eligible individual-book prices. Apply outcomes H, D, A and no decimal-odds bounds before outcome choice. Require selected p×odds−1 strictly above 10.00%. Request a fixed stake of 1,000 monetary units. Scale same-date requests proportionally to available cash; no extra date cap. Historical threshold-diagnostic recipe replayed on this common period; not a newly selected primary rule.

Exact configuration:

```json
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle","allowed_outcomes": ["H","D","A"],"bankroll_fraction": 0.01,"cash_only": false,"consensus_min": null,"consensus_model_keys": [],"date_cap_fraction": null,"description": "Replay the saved First-study accuracy-selected SVM validation-candidate rule with edge strictly above 10% (p × odds − 1 > 0.1), best individual-book quotes and flat stake 1,000. This is an exploratory diagnostic replay on an already examined season, not the selected primary strategy.","diagnostic": true,"fixed_stake": 1000.0,"kelly_fraction": 0.25,"max_bet_fraction": 0.02,"max_odds": null,"min_edge": 0.1,"min_odds": null,"model_key": "first_accuracy","model_label": "First-study accuracy-selected SVM","name": "First-study accuracy-selected SVM | historical threshold diagnostic 10% | best individual-book quotes | flat 1,000","odds_mode": "best","origin": "legacy_diagnostic","policy_family": "historical threshold diagnostic 10%","selection_rule": "max_edge","staking": "fixed","strategy_id": "S076","study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}
```

### S077 — First-study accuracy-selected SVM | historical threshold diagnostic 15% | best individual-book quotes | flat 1,000

Origin: legacy_diagnostic.

Frozen first-study accuracy-selected SVM. Choose the eligible H/D/A outcome with largest p×odds−1. Use best eligible individual-book prices. Apply outcomes H, D, A and no decimal-odds bounds before outcome choice. Require selected p×odds−1 strictly above 15.00%. Request a fixed stake of 1,000 monetary units. Scale same-date requests proportionally to available cash; no extra date cap. Historical threshold-diagnostic recipe replayed on this common period; not a newly selected primary rule.

Exact configuration:

```json
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle","allowed_outcomes": ["H","D","A"],"bankroll_fraction": 0.01,"cash_only": false,"consensus_min": null,"consensus_model_keys": [],"date_cap_fraction": null,"description": "Replay the saved First-study accuracy-selected SVM validation-candidate rule with edge strictly above 15% (p × odds − 1 > 0.15), best individual-book quotes and flat stake 1,000. This is an exploratory diagnostic replay on an already examined season, not the selected primary strategy.","diagnostic": true,"fixed_stake": 1000.0,"kelly_fraction": 0.25,"max_bet_fraction": 0.02,"max_odds": null,"min_edge": 0.15,"min_odds": null,"model_key": "first_accuracy","model_label": "First-study accuracy-selected SVM","name": "First-study accuracy-selected SVM | historical threshold diagnostic 15% | best individual-book quotes | flat 1,000","odds_mode": "best","origin": "legacy_diagnostic","policy_family": "historical threshold diagnostic 15%","selection_rule": "max_edge","staking": "fixed","strategy_id": "S077","study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}
```

### S078 — First-study accuracy-selected SVM | historical threshold diagnostic 20% | best individual-book quotes | flat 1,000

Origin: legacy_diagnostic.

Frozen first-study accuracy-selected SVM. Choose the eligible H/D/A outcome with largest p×odds−1. Use best eligible individual-book prices. Apply outcomes H, D, A and no decimal-odds bounds before outcome choice. Require selected p×odds−1 strictly above 20.00%. Request a fixed stake of 1,000 monetary units. Scale same-date requests proportionally to available cash; no extra date cap. Historical threshold-diagnostic recipe replayed on this common period; not a newly selected primary rule.

Exact configuration:

```json
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle","allowed_outcomes": ["H","D","A"],"bankroll_fraction": 0.01,"cash_only": false,"consensus_min": null,"consensus_model_keys": [],"date_cap_fraction": null,"description": "Replay the saved First-study accuracy-selected SVM validation-candidate rule with edge strictly above 20% (p × odds − 1 > 0.2), best individual-book quotes and flat stake 1,000. This is an exploratory diagnostic replay on an already examined season, not the selected primary strategy.","diagnostic": true,"fixed_stake": 1000.0,"kelly_fraction": 0.25,"max_bet_fraction": 0.02,"max_odds": null,"min_edge": 0.2,"min_odds": null,"model_key": "first_accuracy","model_label": "First-study accuracy-selected SVM","name": "First-study accuracy-selected SVM | historical threshold diagnostic 20% | best individual-book quotes | flat 1,000","odds_mode": "best","origin": "legacy_diagnostic","policy_family": "historical threshold diagnostic 20%","selection_rule": "max_edge","staking": "fixed","strategy_id": "S078","study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}
```

### S079 — First-study calibration-selected MLP | historical threshold diagnostic 0% | best individual-book quotes | flat 1,000

Origin: legacy_diagnostic.

Frozen first-study ECE-selected MLP. Choose the eligible H/D/A outcome with largest p×odds−1. Use best eligible individual-book prices. Apply outcomes H, D, A and no decimal-odds bounds before outcome choice. Require selected p×odds−1 strictly above 0.00%. Request a fixed stake of 1,000 monetary units. Scale same-date requests proportionally to available cash; no extra date cap. Historical threshold-diagnostic recipe replayed on this common period; not a newly selected primary rule.

Exact configuration:

```json
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle","allowed_outcomes": ["H","D","A"],"bankroll_fraction": 0.01,"cash_only": false,"consensus_min": null,"consensus_model_keys": [],"date_cap_fraction": null,"description": "Replay the saved First-study calibration-selected MLP validation-candidate rule with edge strictly above 0% (p × odds − 1 > 0), best individual-book quotes and flat stake 1,000. This is an exploratory diagnostic replay on an already examined season, not the selected primary strategy.","diagnostic": true,"fixed_stake": 1000.0,"kelly_fraction": 0.25,"max_bet_fraction": 0.02,"max_odds": null,"min_edge": 0.0,"min_odds": null,"model_key": "first_calibration","model_label": "First-study calibration-selected MLP","name": "First-study calibration-selected MLP | historical threshold diagnostic 0% | best individual-book quotes | flat 1,000","odds_mode": "best","origin": "legacy_diagnostic","policy_family": "historical threshold diagnostic 0%","selection_rule": "max_edge","staking": "fixed","strategy_id": "S079","study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}
```

### S080 — First-study calibration-selected MLP | historical threshold diagnostic 2.5% | best individual-book quotes | flat 1,000

Origin: legacy_diagnostic.

Frozen first-study ECE-selected MLP. Choose the eligible H/D/A outcome with largest p×odds−1. Use best eligible individual-book prices. Apply outcomes H, D, A and no decimal-odds bounds before outcome choice. Require selected p×odds−1 strictly above 2.50%. Request a fixed stake of 1,000 monetary units. Scale same-date requests proportionally to available cash; no extra date cap. Historical threshold-diagnostic recipe replayed on this common period; not a newly selected primary rule.

Exact configuration:

```json
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle","allowed_outcomes": ["H","D","A"],"bankroll_fraction": 0.01,"cash_only": false,"consensus_min": null,"consensus_model_keys": [],"date_cap_fraction": null,"description": "Replay the saved First-study calibration-selected MLP validation-candidate rule with edge strictly above 2.5% (p × odds − 1 > 0.025), best individual-book quotes and flat stake 1,000. This is an exploratory diagnostic replay on an already examined season, not the selected primary strategy.","diagnostic": true,"fixed_stake": 1000.0,"kelly_fraction": 0.25,"max_bet_fraction": 0.02,"max_odds": null,"min_edge": 0.025,"min_odds": null,"model_key": "first_calibration","model_label": "First-study calibration-selected MLP","name": "First-study calibration-selected MLP | historical threshold diagnostic 2.5% | best individual-book quotes | flat 1,000","odds_mode": "best","origin": "legacy_diagnostic","policy_family": "historical threshold diagnostic 2.5%","selection_rule": "max_edge","staking": "fixed","strategy_id": "S080","study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}
```

### S081 — First-study calibration-selected MLP | historical threshold diagnostic 7.5% | best individual-book quotes | flat 1,000

Origin: legacy_diagnostic.

Frozen first-study ECE-selected MLP. Choose the eligible H/D/A outcome with largest p×odds−1. Use best eligible individual-book prices. Apply outcomes H, D, A and no decimal-odds bounds before outcome choice. Require selected p×odds−1 strictly above 7.50%. Request a fixed stake of 1,000 monetary units. Scale same-date requests proportionally to available cash; no extra date cap. Historical threshold-diagnostic recipe replayed on this common period; not a newly selected primary rule.

Exact configuration:

```json
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle","allowed_outcomes": ["H","D","A"],"bankroll_fraction": 0.01,"cash_only": false,"consensus_min": null,"consensus_model_keys": [],"date_cap_fraction": null,"description": "Replay the saved First-study calibration-selected MLP validation-candidate rule with edge strictly above 7.5% (p × odds − 1 > 0.075), best individual-book quotes and flat stake 1,000. This is an exploratory diagnostic replay on an already examined season, not the selected primary strategy.","diagnostic": true,"fixed_stake": 1000.0,"kelly_fraction": 0.25,"max_bet_fraction": 0.02,"max_odds": null,"min_edge": 0.075,"min_odds": null,"model_key": "first_calibration","model_label": "First-study calibration-selected MLP","name": "First-study calibration-selected MLP | historical threshold diagnostic 7.5% | best individual-book quotes | flat 1,000","odds_mode": "best","origin": "legacy_diagnostic","policy_family": "historical threshold diagnostic 7.5%","selection_rule": "max_edge","staking": "fixed","strategy_id": "S081","study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}
```

### S082 — First-study calibration-selected MLP | historical threshold diagnostic 10% | best individual-book quotes | flat 1,000

Origin: legacy_diagnostic.

Frozen first-study ECE-selected MLP. Choose the eligible H/D/A outcome with largest p×odds−1. Use best eligible individual-book prices. Apply outcomes H, D, A and no decimal-odds bounds before outcome choice. Require selected p×odds−1 strictly above 10.00%. Request a fixed stake of 1,000 monetary units. Scale same-date requests proportionally to available cash; no extra date cap. Historical threshold-diagnostic recipe replayed on this common period; not a newly selected primary rule.

Exact configuration:

```json
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle","allowed_outcomes": ["H","D","A"],"bankroll_fraction": 0.01,"cash_only": false,"consensus_min": null,"consensus_model_keys": [],"date_cap_fraction": null,"description": "Replay the saved First-study calibration-selected MLP validation-candidate rule with edge strictly above 10% (p × odds − 1 > 0.1), best individual-book quotes and flat stake 1,000. This is an exploratory diagnostic replay on an already examined season, not the selected primary strategy.","diagnostic": true,"fixed_stake": 1000.0,"kelly_fraction": 0.25,"max_bet_fraction": 0.02,"max_odds": null,"min_edge": 0.1,"min_odds": null,"model_key": "first_calibration","model_label": "First-study calibration-selected MLP","name": "First-study calibration-selected MLP | historical threshold diagnostic 10% | best individual-book quotes | flat 1,000","odds_mode": "best","origin": "legacy_diagnostic","policy_family": "historical threshold diagnostic 10%","selection_rule": "max_edge","staking": "fixed","strategy_id": "S082","study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}
```

### S083 — First-study calibration-selected MLP | historical threshold diagnostic 15% | best individual-book quotes | flat 1,000

Origin: legacy_diagnostic.

Frozen first-study ECE-selected MLP. Choose the eligible H/D/A outcome with largest p×odds−1. Use best eligible individual-book prices. Apply outcomes H, D, A and no decimal-odds bounds before outcome choice. Require selected p×odds−1 strictly above 15.00%. Request a fixed stake of 1,000 monetary units. Scale same-date requests proportionally to available cash; no extra date cap. Historical threshold-diagnostic recipe replayed on this common period; not a newly selected primary rule.

Exact configuration:

```json
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle","allowed_outcomes": ["H","D","A"],"bankroll_fraction": 0.01,"cash_only": false,"consensus_min": null,"consensus_model_keys": [],"date_cap_fraction": null,"description": "Replay the saved First-study calibration-selected MLP validation-candidate rule with edge strictly above 15% (p × odds − 1 > 0.15), best individual-book quotes and flat stake 1,000. This is an exploratory diagnostic replay on an already examined season, not the selected primary strategy.","diagnostic": true,"fixed_stake": 1000.0,"kelly_fraction": 0.25,"max_bet_fraction": 0.02,"max_odds": null,"min_edge": 0.15,"min_odds": null,"model_key": "first_calibration","model_label": "First-study calibration-selected MLP","name": "First-study calibration-selected MLP | historical threshold diagnostic 15% | best individual-book quotes | flat 1,000","odds_mode": "best","origin": "legacy_diagnostic","policy_family": "historical threshold diagnostic 15%","selection_rule": "max_edge","staking": "fixed","strategy_id": "S083","study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}
```

### S084 — First-study calibration-selected MLP | historical threshold diagnostic 20% | best individual-book quotes | flat 1,000

Origin: legacy_diagnostic.

Frozen first-study ECE-selected MLP. Choose the eligible H/D/A outcome with largest p×odds−1. Use best eligible individual-book prices. Apply outcomes H, D, A and no decimal-odds bounds before outcome choice. Require selected p×odds−1 strictly above 20.00%. Request a fixed stake of 1,000 monetary units. Scale same-date requests proportionally to available cash; no extra date cap. Historical threshold-diagnostic recipe replayed on this common period; not a newly selected primary rule.

Exact configuration:

```json
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle","allowed_outcomes": ["H","D","A"],"bankroll_fraction": 0.01,"cash_only": false,"consensus_min": null,"consensus_model_keys": [],"date_cap_fraction": null,"description": "Replay the saved First-study calibration-selected MLP validation-candidate rule with edge strictly above 20% (p × odds − 1 > 0.2), best individual-book quotes and flat stake 1,000. This is an exploratory diagnostic replay on an already examined season, not the selected primary strategy.","diagnostic": true,"fixed_stake": 1000.0,"kelly_fraction": 0.25,"max_bet_fraction": 0.02,"max_odds": null,"min_edge": 0.2,"min_odds": null,"model_key": "first_calibration","model_label": "First-study calibration-selected MLP","name": "First-study calibration-selected MLP | historical threshold diagnostic 20% | best individual-book quotes | flat 1,000","odds_mode": "best","origin": "legacy_diagnostic","policy_family": "historical threshold diagnostic 20%","selection_rule": "max_edge","staking": "fixed","strategy_id": "S084","study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}
```
