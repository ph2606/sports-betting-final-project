# EPL trading-strategy metrics supplement — draft for review

October 14, 2026 | Companion to the unchanged seven-page EPL project draft. Historical archived-price analytics; no model refitting or new strategy selection.

This supplement exposes requested trade outcomes, forecast-implied expectations, activity and bankroll risk. The complete workbook/CSV retains 172 strategy-period rows, including validation, test, historical monitoring, individual ablation seasons, pooled ablation summaries and tuning diagnostics. The displayed tables include all 16 locked-test strategies and all 22 pooled ablation variants/staking rules; cash policies are retained.

For stake s, forecast win probability p and decimal odds O, expected gain is s·p·(O−1), expected loss is s·(1−p), and expected net P&L is s·(pO−1). Gain/loss expectations are probability-weighted positive/negative P&L components, distinct from realised conditional winning/losing payoffs. Per-trade components divide totals by trades. They condition on actual allocated stakes, including the realised bankroll-dependent Kelly path; they are not unconditional predicted terminal wealth or verified true expectations.

Hit ratio is winning bets divided by settled bets. Trading frequency divides bets by matched fixtures with valid prices; the workbook also gives bets divided by all predicted fixtures, active-date fraction and bets per calendar week. Missing quotes must be distinguished from abstention. Classification accuracy is a separate H/D/A metric and cannot substitute for trade hit ratio.

ROI is net profit divided by turnover. Capital return divides profit by the sum of episode initial capital. Profit factor compares total gains with total losses; payoff ratio compares average winning gain with average losing loss. Drawdown is measured at date close, including initial capital. Pooled ablation capital resets remain separate: cash totals may be added, but the displayed pooled drawdown is the worst episode, not a continuous investment track record.

A dash means undefined or unavailable. A cash policy can have zero profit, turnover and trade frequency while its hit ratio, ROI and per-trade averages remain undefined. Genuine positive infinity is displayed explicitly for profit factor when gains exist and losses do not. Pending forecasts supply no settled hit rate or trading profit.

95% hit-ratio/ROI intervals use 1,000 whole-match-date bootstrap draws; pooled draws stratify by season. They condition on recorded wagers and fitted predictions, omit fitting/selection uncertainty and lack multiplicity adjustment. New interpolated-percentile intervals can differ from original noninterpolating bounds; original outputs remain unchanged. The strictly positive qualification rule pO−1>0.05 builds positive model-implied expected ROI into the fixed 5% policy; this is not independent evidence of an edge.

For example, the calibration branch's best-book fixed policy wins 90 of 333 trades (27.03%), with mean winning gain 27.15 and mean losing loss 10.00 units. Model-implied net expectancy is 6.0859 units/trade (60.86% expected ROI), versus realised 0.0411 units/trade (0.41% ROI). These are different quantities.

## First study: complete locked-test trade metrics

2025/26: the primary validation-selected policy and separately declared 5% policy remain distinct. Gain/loss/expectancy columns use bankroll units; hit and frequency use percentages.

Table S1. Every locked-test strategy. Hit bounds are conditional 95% intervals; frequency uses matched valid prices. Expected components use recorded actual stakes.

| Strategy | Trades | Hit %<br>[95% CI] | Trade<br>freq. % | Avg. win<br>gain | Avg. loss<br>size | Expected<br>gain/trade | Expected<br>loss/trade | Expected<br>net/trade | Realised<br>net/trade |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Accuracy / Fixed 5%<br>Best book / Fixed | 371 | 26.68<br>[22.86, 30.77] | 99.20 | 26.63 | 10.00 | 11.74 | 6.31 | 5.42 | −0.22 |
| Accuracy / Fixed 5%<br>Best book / Quarter Kelly | 371 | 26.68<br>[22.86, 30.77] | 99.20 | 36.53 | 14.68 | 17.48 | 9.05 | 8.43 | −1.02 |
| Accuracy / Fixed 5%<br>Bet365 / Fixed | 365 | 26.85<br>[23.14, 30.94] | 97.59 | 25.34 | 10.00 | 10.87 | 6.25 | 4.62 | −0.51 |
| Accuracy / Fixed 5%<br>Bet365 / Quarter Kelly | 365 | 26.85<br>[23.14, 30.94] | 97.59 | 33.69 | 13.99 | 15.45 | 8.55 | 6.90 | −1.19 |
| Calibration / Fixed 5%<br>Best book / Fixed | 333 | 27.03<br>[22.32, 32.12] | 89.04 | 27.15 | 10.00 | 12.40 | 6.32 | 6.09 | 0.04 |
| Calibration / Fixed 5%<br>Best book / Quarter Kelly | 333 | 27.03<br>[22.32, 32.12] | 89.04 | 46.73 | 17.94 | 22.95 | 11.08 | 11.88 | −0.46 |
| Calibration / Fixed 5%<br>Bet365 / Fixed | 314 | 27.71<br>[22.71, 32.92] | 83.96 | 25.82 | 10.00 | 11.61 | 6.29 | 5.32 | −0.07 |
| Calibration / Fixed 5%<br>Bet365 / Quarter Kelly | 314 | 27.71<br>[22.71, 32.92] | 83.96 | 44.11 | 17.66 | 21.02 | 10.84 | 10.18 | −0.54 |
| Accuracy / Primary<br>Best book / Fixed | 0 | — | 0.00 | — | — | — | — | — | — |
| Accuracy / Primary<br>Best book / Quarter Kelly | 0 | — | 0.00 | — | — | — | — | — | — |
| Accuracy / Primary<br>Bet365 / Fixed | 0 | — | 0.00 | — | — | — | — | — | — |
| Accuracy / Primary<br>Bet365 / Quarter Kelly | 0 | — | 0.00 | — | — | — | — | — | — |
| Calibration / Primary<br>Best book / Fixed | 0 | — | 0.00 | — | — | — | — | — | — |
| Calibration / Primary<br>Best book / Quarter Kelly | 0 | — | 0.00 | — | — | — | — | — | — |
| Calibration / Primary<br>Bet365 / Fixed | 0 | — | 0.00 | — | — | — | — | — | — |
| Calibration / Primary<br>Bet365 / Quarter Kelly | 0 | — | 0.00 | — | — | — | — | — | — |

## First study: complete locked-test return and risk metrics

Cash policies remain in the table. ROI measures return per unit staked; capital return measures profit relative to initial bankroll, so the two percentages answer different questions.

Table S2. Same strategies and period as S1. Conditional bounds resample observed dates; undefined cash-policy ROI remains a dash.

| Strategy | Net profit | Turnover | ROI | 95% ROI CI | Expected<br>ROI | Profit<br>factor | Payoff<br>ratio | Max.<br>drawdown | Capital<br>return |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Accuracy / Fixed 5%<br>Best book / Fixed | −83.30 | 3,710.00 | −2.25% | [−18.84%, 15.46%] | 54.22% | 0.97 | 2.66 | 27.74% | −8.33% |
| Accuracy / Fixed 5%<br>Best book / Quarter Kelly | −377.05 | 5,376.77 | −7.01% | [−23.18%, 11.93%] | 58.16% | 0.91 | 2.49 | 49.95% | −37.70% |
| Accuracy / Fixed 5%<br>Bet365 / Fixed | −186.70 | 3,650.00 | −5.12% | [−20.25%, 11.16%] | 46.20% | 0.93 | 2.53 | 28.60% | −18.67% |
| Accuracy / Fixed 5%<br>Bet365 / Quarter Kelly | −433.14 | 5,055.80 | −8.57% | [−23.64%, 8.81%] | 49.84% | 0.88 | 2.41 | 51.21% | −43.31% |
| Calibration / Fixed 5%<br>Best book / Fixed | 13.70 | 3,330.00 | 0.41% | [−20.09%, 22.07%] | 60.86% | 1.01 | 2.72 | 28.11% | 1.37% |
| Calibration / Fixed 5%<br>Best book / Quarter Kelly | −153.91 | 5,950.63 | −2.59% | [−20.94%, 17.72%] | 66.46% | 0.96 | 2.60 | 54.44% | −15.39% |
| Calibration / Fixed 5%<br>Bet365 / Fixed | −23.50 | 3,140.00 | −0.75% | [−19.47%, 19.71%] | 53.19% | 0.99 | 2.58 | 29.38% | −2.35% |
| Calibration / Fixed 5%<br>Bet365 / Quarter Kelly | −170.61 | 5,526.38 | −3.09% | [−20.97%, 16.47%] | 57.81% | 0.96 | 2.50 | 51.98% | −17.06% |
| Accuracy / Primary<br>Best book / Fixed | 0.00 | 0.00 | — | — | — | — | — | 0.00% | 0.00% |
| Accuracy / Primary<br>Best book / Quarter Kelly | 0.00 | 0.00 | — | — | — | — | — | 0.00% | 0.00% |
| Accuracy / Primary<br>Bet365 / Fixed | 0.00 | 0.00 | — | — | — | — | — | 0.00% | 0.00% |
| Accuracy / Primary<br>Bet365 / Quarter Kelly | 0.00 | 0.00 | — | — | — | — | — | 0.00% | 0.00% |
| Calibration / Primary<br>Best book / Fixed | 0.00 | 0.00 | — | — | — | — | — | 0.00% | 0.00% |
| Calibration / Primary<br>Best book / Quarter Kelly | 0.00 | 0.00 | — | — | — | — | — | 0.00% | 0.00% |
| Calibration / Primary<br>Bet365 / Fixed | 0.00 | 0.00 | — | — | — | — | — | 0.00% | 0.00% |
| Calibration / Primary<br>Bet365 / Quarter Kelly | 0.00 | 0.00 | — | — | — | — | — | 0.00% | 0.00% |

## Ablation: complete pooled trade metrics

Four exploratory outer seasons, 2022/23–2025/26; all source groups, benchmarks, fixed stakes and quarter Kelly are retained. The same inspected history is not a fresh holdout.

Table S3. Every pooled variant/staking rule. Components pool recorded cash totals; hit ratio pools wins/bets, not seasonal averages. Probability quality and availability claims remain separate.

| Strategy | Trades | Hit %<br>[95% CI] | Trade<br>freq. % | Avg. win<br>gain | Avg. loss<br>size | Expected<br>gain/trade | Expected<br>loss/trade | Expected<br>net/trade | Realised<br>net/trade |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Class frequency / Fixed | 1,447 | 23.01<br>[20.76, 25.16] | 98.44 | 31.34 | 10.00 | 17.40 | 6.12 | 11.28 | −0.49 |
| Class frequency / Quarter Kelly | 1,447 | 23.01<br>[20.76, 25.16] | 98.44 | 45.00 | 15.02 | 26.29 | 9.07 | 17.23 | −1.21 |
| Raw market / Fixed | 263 | 9.51<br>[6.16, 13.38] | 17.89 | 61.97 | 10.00 | 9.91 | 8.64 | 1.27 | −3.16 |
| Raw market / Quarter Kelly | 263 | 9.51<br>[6.16, 13.38] | 17.89 | 23.08 | 3.51 | 3.55 | 3.06 | 0.49 | −0.98 |
| Logistic: Combined / Fixed | 1,285 | 29.49<br>[26.97, 32.00] | 87.41 | 23.95 | 10.00 | 9.52 | 6.47 | 3.06 | 0.01 |
| Logistic: Combined / Quarter Kelly | 1,285 | 29.49<br>[26.97, 32.00] | 87.41 | 31.17 | 13.72 | 13.30 | 8.59 | 4.71 | −0.48 |
| Logistic: Team / Fixed | 1,241 | 29.57<br>[27.02, 32.07] | 84.42 | 24.35 | 10.00 | 9.63 | 6.48 | 3.14 | 0.16 |
| Logistic: Team / Quarter Kelly | 1,241 | 29.57<br>[27.02, 32.07] | 84.42 | 31.40 | 13.81 | 13.60 | 8.64 | 4.96 | −0.44 |
| Logistic: Team+players / Fixed | 1,274 | 28.81<br>[26.38, 31.45] | 86.67 | 24.11 | 10.00 | 9.65 | 6.48 | 3.17 | −0.17 |
| Logistic: Team+players / Quarter Kelly | 1,274 | 28.81<br>[26.38, 31.45] | 86.67 | 30.20 | 13.35 | 13.13 | 8.35 | 4.78 | −0.81 |
| Logistic: Team+xG / Fixed | 1,236 | 30.42<br>[27.61, 33.01] | 84.08 | 25.18 | 10.00 | 9.51 | 6.47 | 3.04 | 0.70 |
| Logistic: Team+xG / Quarter Kelly | 1,236 | 30.42<br>[27.61, 33.01] | 84.08 | 33.77 | 14.89 | 14.32 | 9.24 | 5.08 | −0.09 |
| Market residual: Combined / Fixed | 1,186 | 30.69<br>[28.31, 33.25] | 80.68 | 22.83 | 10.00 | 8.58 | 6.63 | 1.95 | 0.08 |
| Market residual: Combined / Quarter Kelly | 1,186 | 30.69<br>[28.31, 33.25] | 80.68 | 34.92 | 13.90 | 12.41 | 9.23 | 3.18 | 1.08 |
| Market residual: Team / Fixed | 1,048 | 30.34<br>[27.31, 33.08] | 71.29 | 23.26 | 10.00 | 8.49 | 6.70 | 1.78 | 0.09 |
| Market residual: Team / Quarter Kelly | 1,048 | 30.34<br>[27.31, 33.08] | 71.29 | 28.36 | 12.01 | 10.51 | 7.98 | 2.53 | 0.24 |
| Market residual: Team+players / Fixed | 1,147 | 31.04<br>[28.42, 33.74] | 78.03 | 22.87 | 10.00 | 8.53 | 6.64 | 1.89 | 0.20 |
| Market residual: Team+players / Quarter Kelly | 1,147 | 31.04<br>[28.42, 33.74] | 78.03 | 32.98 | 13.62 | 12.00 | 9.00 | 3.00 | 0.84 |
| Market residual: Team+xG / Fixed | 1,098 | 30.33<br>[27.68, 32.92] | 74.69 | 23.11 | 10.00 | 8.51 | 6.66 | 1.84 | 0.04 |
| Market residual: Team+xG / Quarter Kelly | 1,098 | 30.33<br>[27.68, 32.92] | 74.69 | 29.80 | 12.69 | 11.06 | 8.31 | 2.75 | 0.20 |
| Temperature market / Fixed | 216 | 25.46<br>[20.09, 31.02] | 14.69 | 18.03 | 10.00 | 7.81 | 6.81 | 0.99 | −2.86 |
| Temperature market / Quarter Kelly | 216 | 25.46<br>[20.09, 31.02] | 14.69 | 13.19 | 6.36 | 4.75 | 4.07 | 0.68 | −1.38 |

## Ablation: complete pooled return and risk metrics

Each outer season starts a separate bankroll. Pooled ROI uses total profit / turnover; capital return uses total opening capital. 11 of 11 positive point-ROI intervals include zero; conditional comparisons do not identify a reliable winning strategy.

Table S4. Same pooled variants as S3. Max drawdown is the worst seasonal episode; no stitched pooled equity path or annualized Sharpe is claimed.

| Strategy | Net profit | Turnover | ROI | 95% ROI CI | Expected<br>ROI | Profit<br>factor | Payoff<br>ratio | Max.<br>drawdown | Capital<br>return |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Class frequency / Fixed | −702.40 | 14,470.00 | −4.85% | [−15.44%, 6.37%] | 112.76% | 0.94 | 3.13 | 48.07% | −17.56% |
| Class frequency / Quarter Kelly | −1,745.71 | 21,477.81 | −8.13% | [−19.24%, 2.99%] | 116.05% | 0.90 | 3.00 | 71.65% | −43.64% |
| Raw market / Fixed | −830.70 | 2,630.00 | −31.59% | [−60.15%, −0.51%] | 12.70% | 0.65 | 6.20 | 40.00% | −20.77% |
| Raw market / Quarter Kelly | −258.21 | 946.97 | −27.27% | [−55.64%, 3.69%] | 13.67% | 0.69 | 6.58 | 13.93% | −6.46% |
| Logistic: Combined / Fixed | 17.80 | 12,850.00 | 0.14% | [−9.88%, 9.71%] | 30.59% | 1.00 | 2.40 | 63.10% | 0.45% |
| Logistic: Combined / Quarter Kelly | −621.53 | 17,911.66 | −3.47% | [−13.04%, 5.57%] | 33.77% | 0.95 | 2.27 | 62.04% | −15.54% |
| Logistic: Team / Fixed | 197.90 | 12,410.00 | 1.59% | [−9.00%, 11.68%] | 31.41% | 1.02 | 2.44 | 26.47% | 4.95% |
| Logistic: Team / Quarter Kelly | −544.32 | 17,405.19 | −3.13% | [−13.24%, 6.63%] | 35.39% | 0.95 | 2.27 | 46.12% | −13.61% |
| Logistic: Team+players / Fixed | −220.60 | 12,740.00 | −1.73% | [−11.75%, 7.36%] | 31.74% | 0.98 | 2.41 | 37.26% | −5.51% |
| Logistic: Team+players / Quarter Kelly | −1,027.84 | 17,212.31 | −5.97% | [−16.16%, 2.96%] | 35.40% | 0.92 | 2.26 | 55.40% | −25.70% |
| Logistic: Team+xG / Fixed | 866.30 | 12,360.00 | 7.01% | [−4.54%, 18.60%] | 30.41% | 1.10 | 2.52 | 23.26% | 21.66% |
| Logistic: Team+xG / Quarter Kelly | −109.75 | 18,605.85 | −0.59% | [−10.97%, 8.72%] | 33.75% | 0.99 | 2.27 | 48.84% | −2.74% |
| Market residual: Combined / Fixed | 90.30 | 11,860.00 | 0.76% | [−8.60%, 11.05%] | 19.45% | 1.01 | 2.28 | 44.57% | 2.26% |
| Market residual: Combined / Quarter Kelly | 1,285.63 | 17,870.62 | 7.19% | [−2.64%, 17.42%] | 21.12% | 1.11 | 2.51 | 33.95% | 32.14% |
| Market residual: Team / Fixed | 95.30 | 10,480.00 | 0.91% | [−11.04%, 13.22%] | 17.81% | 1.01 | 2.33 | 34.22% | 2.38% |
| Market residual: Team / Quarter Kelly | 250.07 | 13,587.50 | 1.84% | [−7.86%, 12.30%] | 19.53% | 1.03 | 2.36 | 25.64% | 6.25% |
| Market residual: Team+players / Fixed | 233.40 | 11,470.00 | 2.03% | [−8.35%, 12.45%] | 18.92% | 1.03 | 2.29 | 34.33% | 5.83% |
| Market residual: Team+players / Quarter Kelly | 965.14 | 16,820.95 | 5.74% | [−3.88%, 15.84%] | 20.46% | 1.09 | 2.42 | 32.58% | 24.13% |
| Market residual: Team+xG / Fixed | 46.60 | 10,980.00 | 0.42% | [−9.38%, 10.93%] | 18.44% | 1.01 | 2.31 | 22.78% | 1.17% |
| Market residual: Team+xG / Quarter Kelly | 216.80 | 14,835.15 | 1.46% | [−7.78%, 11.22%] | 20.36% | 1.02 | 2.35 | 23.63% | 5.42% |
| Temperature market / Fixed | −618.10 | 2,160.00 | −28.62% | [−50.73%, −5.21%] | 9.93% | 0.62 | 1.80 | 57.00% | −15.45% |
| Temperature market / Quarter Kelly | −297.97 | 1,837.10 | −16.22% | [−31.25%, −1.06%] | 7.94% | 0.71 | 2.07 | 21.26% | −7.45% |

## Coverage, pending opportunities and audit trail

The prospective table contains 20 declared strategy/staking status slots, each summarising a model's future opportunities; these are not 20 fixtures or executed trades. Across distinct models it records 40 released forecasts, 0 quote-backed forecasts and 0 resolved forecasts. Trading performance remains unavailable without recorded quote-backed positions. Unknown trade counts, profits and expectations stay unavailable rather than becoming zero. Full per-slot reasons remain in the workbook and CSV.

The separate arbitrage screen contains 7 source rows. The arithmetic sum of inverse best-outcome prices can describe a candidate; it does not prove synchronized observation, accepted stakes, compatible settlement, fees or execution. Screen statuses are retained separately from strategy wagers and are not credited as trading profit.

Validation and threshold-grid diagnostics are labelled explicitly and excluded from the two held-out/pool displays. Historical monitoring is retrospective. All 172 underlying rows remain available without selecting the best strategy after observing returns. The supplement neither changes decisions nor promises future profit.

Open EPL_strategy_metrics.xlsx for all strategies, source scopes, prospective status, arbitrage status and metric definitions. strategy_metrics_full.csv retains every source metric at original precision. The four display CSVs contain the rounded published tables. No fee or fill assumptions are silently introduced.

The companion report_manifest.json lists input/output SHA-256 hashes and verifies that original study outputs and the seven-page draft stayed unchanged. Regenerate this supplement with python -m epl_strategy.report --results PATH. The report reads the saved analytics; it does not retrieve data, train estimators, tune thresholds or rewrite historical results.

Definitions and interval conventions follow epl_strategy/METHODOLOGY.md. Winning-trade share, conditional mean win/loss and profit-factor terminology is consistent with the official MetaTrader report reference linked there; the probability-weighted components remain separately defined in this project.
