# Trading strategy metrics

This extension evaluates the **recorded hypothetical trades**, rather than
the accuracy of every match forecast. It preserves all original strategies and
their periods, including policies that hold cash. It neither refits a model nor
selects a strategy using the added metrics.

The original first study contributes 48 strategy/split rows; the source
ablation contributes 88 strategy/season rows. Twenty-two additional ablation
rows pool four independently funded seasons. Fourteen threshold-search rows
are reproduced from cached validation predictions as **tuning diagnostics**,
not additional held-out evidence. Future paper-policy slots and mathematical
arbitrage screens receive separate availability tables.

## Payoffs and expectations

For an allocated stake `s`, decimal odds `O`, and selected outcome probability
`p`, the net payoff is `s * (O - 1)` if the bet wins and `-s` otherwise. Returned
stake is excluded from winning profit. These recorded replays contain binary
H/D/A settlements, no pushes and no separately modeled transaction costs.

| Metric | Definition | Interpretation |
| --- | --- | --- |
| Hit ratio | winning trades / settled positive-stake trades | Bet-selection success, distinct from all-match prediction accuracy |
| Average winning gain | mean positive realized net profit | Observed conditional winning payoff, in bankroll units |
| Average losing loss | mean absolute negative realized net profit | Observed conditional loss magnitude, in bankroll units |
| Realized expectancy per trade | total realized net profit / trades | Empirical mean net payoff |
| Expected gain | sum of `p * s * (O - 1)` | Model-implied positive cash component |
| Expected loss | sum of `(1 - p) * s` | Model-implied negative cash component, reported as a positive magnitude |
| Expected net profit | expected gain minus expected loss | Equals sum of `s * (p * O - 1)` |
| Expected gain/loss per trade | each model-implied cash component / trades | Comparable average component at the recorded allocated stakes |
| Expected ROI | expected net profit / total stakes | Stake-weighted model expectation, not observed ROI |
| Realized ROI | realized net profit / total stakes | Return per staked unit; distinct from bankroll return |
| Profit factor | sum of positive net profits / sum of absolute negative net profits | Realized gain/loss balance |
| Payoff ratio | average winning gain / average losing loss | Observed conditional payoff balance |

If all trades have ordinary win/loss payoffs, empirical expectancy is also
`hit_ratio * average_gain - (1 - hit_ratio) * average_loss`. Conditional means
are undefined when the corresponding outcome subset is empty; a zero-weight
component should be treated as zero in the arithmetic, not as an estimated
conditional payoff. The unconditional empirical gain and loss components are
provided separately to retain that identity for one-sided samples.

Expected components use each recorded probability and **actual allocated
stake**, including Kelly sizing and capacity scaling. They do not substitute
the requested stake or an average price. Both cash-unit and per-staked-unit
payoffs are supplied because fixed and Kelly stakes differ. Positive expected
ROI on the 5% rule is largely imposed by selecting `p * O - 1 > 0.05`; it is
not independent evidence that the model predicts a profitable opportunity.
Comparing it with realized results reveals the distinction.

The empirical break-even hit ratio `mean_loss / (mean_gain + mean_loss)` is a
descriptive identity for the observed payoff mixture. It is not a universal
threshold for changing odds, stakes or selected matches. The mean of inverse
odds and the inverse of mean odds are not silently substituted for it.

## Trading frequency and coverage

Primary trading frequency is the number of trades divided by the number of
predicted matches with valid prices in the same scope. A second participation
rate divides by **all** predicted matches. Price coverage and the number of
predictions without valid prices remain separate: lacking a price is not an
economic decision to abstain.

Additional activity measures are trades per matched match date, the fraction
of matched dates with at least one trade, and trades per calendar week. The
weekly denominator is the sum of inclusive first-to-last priced-match calendar
spans within each reset episode, divided by seven. Off-season gaps between
pooled episodes are not included. All date-close equity and bootstrap inputs
retain eligible dates on which no trade was placed.

## Capital and risk

Profit, turnover, average/minimum/maximum stake, mean selected probability and
odds, and mean per-staked-unit returns accompany every settled strategy row.
Return on initial capital uses the sum of independently funded episode
bankrolls, rather than turnover. Each first-study split and ablation season
starts separately with 1,000 units; four-season pooled capital is 4,000 units.

Drawdown includes initial capital and is measured at date close. The pooled
drawdown is the **worst separate season drawdown**, never a fictitious curve
joining reset balances. Episode log-growth summaries remain episode summaries.
Capital exposure is date turnover divided by date-start bankroll; same-date
stakes must fit available cash before any result is credited.

Mean, sample standard deviation and their ratio are supplied for returns on
matched match dates, including inactive dates. This ratio is unannualized and
uses no risk-free adjustment. It is not presented as an annualized Sharpe ratio:
the observations are irregular football match dates and may be dependent.

## Uncertainty and unavailable values

The extension supplies conditional 95% percentile intervals for realized ROI,
hit ratio, realized expectancy and primary trading frequency, using 1,000
whole-match-date bootstrap draws. Each reset episode is resampled separately
and pooled cashflows/counts are then added. Recorded selections, forecasts and
stakes remain fixed. No model refitting, threshold reselection, execution
uncertainty or multiple-comparison adjustment is included. These intervals do
not establish a newly selected winning strategy.

These are newly computed intervals under one common analytics bootstrap.
The first study's original interval values remain preserved; small differences
can arise because this extension uses linearly interpolated percentiles while
the original replay used noninterpolating empirical quantiles.

For a recorded no-trade policy, trade counts, cash totals and frequency are
zero when opportunities exist. Hit ratio, per-trade means, conditional payoffs
and ROI are undefined. With positive winning profit and no losing trades,
profit factor is infinite; with no gains or losses it is undefined. The status
field identifies these cases explicitly.

Unsettled prospective forecasts do not constitute settled trades. Without
quote-backed recorded positions, their expected trading gains/losses and
frequency are unavailable. Mathematical cross-book arbitrage candidates also
have no executed-trade hit ratio: compatible contracts, simultaneous prices,
fees, limits and accepted fills are unverified. Neither case receives invented
zero-error or zero-risk performance.

All source cashflows, bet counts, fixture dates, outcomes and bankroll paths are
reconciled before aggregation. Original study outputs, the seven-page draft,
the live forecasts and the user-edited acquisition workbook are preserved.

## Terminology reference

The profitable-trade share, average winning/losing payoff and profit-factor
terminology agrees with the [official MetaTrader trading-report definitions](https://www.metatrader5.com/en/terminal/help/trading_advanced/history_report),
checked October 14, 2026. This project's probability-weighted expected cash
components are explicitly separated from empirical average trade profit.
