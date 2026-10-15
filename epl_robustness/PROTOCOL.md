# Exploratory execution-cost and return-fragility study

Declared October 14, 2026, after inspecting the original historical studies and
their trading-metric extension. These calculations reuse inspected history;
they are not a new confirmatory holdout or a newly selected trading policy.

## Population and preserved decisions

Use the frozen October 14 strategy-analytics export. Include all 136 original
strategy/period rows and 22 pooled ablation summaries. Exclude the 14 threshold
search reconstructions from this robustness study; they remain available in the
previous export as tuning diagnostics. Keep first-study validation, test and
partial historical monitoring scopes separate. All four ablation seasons retain
their independent 1,000-unit initial funding.

Keep every recorded selection, forecast probability, price, stake and outcome.
Do not retrain, requalify a bet against a new edge, change Kelly sizing, remove a
later bet after a funding problem, or choose a winning filter from these results.
The existing prospective forecast ledger and model settings remain unchanged.

## Explicit friction assumptions

For original stake `s`, decimal odds `O`, winning-outcome indicator `z`, fee
fraction `c` and winning-net-payout haircut `h`, scenario net P&L is

`z * (1-h) * s * (O-1) - (1-z) * s - c*s`.

The hypothetical fee is paid on **every** wager, whether it wins or loses. The
haircut applies to winning profit `s*(O-1)`, not to returned principal or the
full decimal odds. These are sensitivity parameters, not claims about actual
bookmaker fee schedules, slippage distributions, taxes or available execution.

Use nine fixed illustrative scenarios: baseline; stake fees of 0.25%, 0.5%, 1%
and 2%; winning-payout haircuts of 1%, 2.5% and 5%; and a combined 1% stake fee
plus 2.5% payout haircut. They represent separately labeled assumptions.

If `P` is original realized net profit, `W` the sum of winning net profits, and
`T` original turnover, fixed-exposure scenario profit is exactly
`P - h*W - c*T`. Realized signed break-even capacities are `P/T` for fees and
`P/W` for payout haircut. A negative capacity means the baseline already loses;
an undefined denominator stays unavailable. Model-implied capacities use model
expected profit and probability-weighted potential winning gains separately.

Expected positive/negative P&L components use the two scenario outcome payoffs,
including the possibility that a correctly selected winner loses money after
fees. Outcome hit ratio therefore remains separate from profitable-trade share.
Both expected and observed gains/losses, frequency, profit, ROI and risk status
must remain available for every scenario scope, with appropriate missing values.

ROI keeps original base-wager turnover as denominator, so friction comparisons
remain directly interpretable. Fee-inclusive cash outlay and its return are
reported separately. Expectations condition on the original allocated stakes,
including the original realized bankroll-dependent Kelly path; they are not
unconditional forecasts of terminal wealth.

## Funding and uncertainty

Before each date settles, compare original total stakes plus fees with scenario
date-start shadow capital. Record the first funding breach, number of breached
dates, minimum shadow wealth and additional initial capital required to fund
the complete fixed path. Do not silently inject that additional capital.

Unfundable paths remain hypothetical fixed-exposure cashflow stress calculations.
Their shadow drawdown can exceed 100%; conventional fundable-path drawdown is
unavailable. No forced resizing, synthetic margin lending or new executable
Kelly track record is introduced. Pooled risk remains the worst separate-season
path, with additional required initial funding summed across independent seasons.

Use 1,000 whole-match-date bootstrap draws, stratified by reset episode. Reuse
the same draws across the nine shocks within a strategy to preserve matched
comparisons. Intervals condition on recorded selections, probabilities and
stakes. They omit refitting, policy selection, price availability, fill acceptance
and multiple-comparison uncertainty. They do not refit stakes in resampled paths.

## Calibration tails and contribution diagnostics

Inspect selected bets using fixed probability bins of width 0.1, decimal-odds
bins `[1,2), [2,3), [3,5), [5,10), [10,infinity)` and fixed expected-return bins.
Keep empty bins and sample counts. Report outcome hit rate, mean forecast
probability, stake share, model expectation and realized profit/ROI. These
conditional selected-bet statistics are distinct from full-match H/D/A scores.

For the original fee-free payoffs, the model-implied minus realized net-P&L gap
is exactly `sum(stake * odds * (probability - won))`. Use this identity to show
which odds groups contribute to the expectation error. Do not interpret an
inspected tail as a new exclusion recommendation or assume independent bets.

Report the contribution of positive date-net cashflows, removal of each whole
date, and removal of each separate season. Leave-one-date/season-out values
delete recorded cashflows without re-fitting or re-sizing remaining trades;
they are contribution diagnostics, not feasible alternative backtests. They
must not be relabeled a fresh validation or a robustly selected strategy.

## Outputs and preservation

Write a new timestamped analytics directory with CSV/Parquet tables, explicit
scenario definitions, an input/code/output hash manifest, tests, workbook and
a separate review draft. Preserve every original data/model/result artifact,
the previous trading-metrics report, the seven-page main draft and the user's
locally edited data-overview workbook. No wager or scheduled collection job is
part of this study.
