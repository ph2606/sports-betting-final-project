# Four-season stability and conditional selection audit

This continuation fixes the existing 84-strategy catalog and adds historical
stability evidence. It does not fit a new model, optimize a filter, select a
winning strategy or create a new holdout. All these outcomes had already been
examined. The directory name `validation` describes checks and historical
stress analysis, not independently validated profitability.

## Two populations, kept separate

The 56 rolling-compatible configurations S017-S072 have saved probability
forecasts for four rolling-origin evaluation seasons. Their common quoted
populations are:

| Season | Fixtures | Priced match dates |
| --- | ---: | ---: |
| 2022/23 | 368 | 117 |
| 2023/24 | 360 | 116 |
| 2024/25 | 368 | 107 |
| 2025/26 | 374 | 113 |
| Total | 1,470 | 453 |

Every model in an outer season must have the exact same match identities,
dates, season labels and results as its source price panel. Check normalized,
finite probabilities and complete valid reference/best prices. No silent
intersection may drop a problematic fixture. Rebuild the three ensemble
probability vectors from the same fixed 4/8/2 constituent vectors separately
within each source season; no forecast may be borrowed from another season.

The first-study SVM/MLP configurations S001-S016 and S073-S084 cannot be
extended fairly into these earlier evaluation seasons: their model selection
or calibration used some of that history. Those 28 configurations retain only
their previously reported 2025/26 replay. The existing graph and metrics for
all 84 strategies remain available in the new report. The separate selection
audit below uses all 84 on those original 374 fixtures and 113 dates.

Historical populations reflect the current-2026/27-club research cohort and
retain its membership/survivor selection. Opponents needed for match settlement
remain in the history. Coverage is not a claim of all league fixtures.

## Account designs

**Continuous:** Each of the 56 compatible rules starts with 100,000 monetary
units on the day before its first 2022/23 match and carries its balance through
the last 2025/26 match. There are no seasonal deposits or resets. All 1,470
fixtures pass through the same simulation in chronological order. The account
is flat between settlements, including off-seasons. A zero balance is absorbing.

**Seasonal:** Replay the same 56 rules in each of the four seasons with a
separate fresh 100,000-unit account: 224 rows. These are independent starting
accounts and cannot be interpreted as one continuously funded portfolio.
Do not slice a continuous Kelly path and pretend it started again at 100,000.

Selection, strict edge thresholds, inclusive candidate filters, consensus veto,
deterministic H/D/A ties and sizing are exactly the frozen catalog rules. Fixed
stakes request 1,000 throughout. Dynamic/Kelly requests use current date-start
cash, and all requests on a date are committed before settlement. Scale
uniformly to available cash and any declared date cap. No same-date result may
finance another request.

The adapter validates real season metadata, passes only transaction fields to
the frozen generic cash engine, and restores the true source season and account
episode IDs afterward. It never assigns fake 2025 labels to earlier fixtures.
Continuous peak/drawdown calculations include the original 100,000 and all later
date closes. Fresh 2025 seasonal accounts must reproduce the 56 saved policies'
selections, stakes, cashflows and date balances exactly within floating tolerance.

## Metrics and season stability

Reuse `epl_strategy.metrics.summarize_strategy` for every continuous and seasonal
account. Report hit ratio, probability-weighted expected positive payoff and
loss magnitude, realized winning/losing payoffs, trade frequency, profit,
turnover, capital return, ROI, drawdown and conditional date-bootstrap intervals.
Initial funding is 100,000 per row; the continuous row has one uninterrupted
episode, and each seasonal row describes its own account. Capital return and
ROI on turnover have different denominators.

Season-stability summaries use the four **fresh seasonal accounts**: all four
capital returns, number of positive seasons, worst/best season, sample return
standard deviation, pooled reset-account ROI and leave-one-season-out pooled
ROI. For the latter, omit a seasonal account's profit and turnover from their
four-account totals. This is not a counterfactual continuous Kelly replay after
deleting a year. Pooled reset-account return uses 400,000 total starting capital,
never 100,000. Saved individual metrics remain the primary audit trail.

## Conditional comparison after examining 84 rules

Use the original 2025/26 ledger to construct a 113-date by 84-strategy matrix of
net profit, retaining dates with no bet. Compare each column with (a) cash,
whose date profit is zero, and (b) S042, the frozen market-favorite benchmark.
Each comparator defines a separate 84-rule family. Every strategy uses the
same original 100,000 funding, although stake schedules and exposures differ.

The declared statistic is **mean excess net profit per priced match date**:

`theta_j = mean_t(profit_tj - profit_t,benchmark)`.

It is not profit per selected bet, profit per fixture or a difference in
turnover ROI. Multiplying it by 113 gives the observed fixed-period difference
in aggregate net cash; dividing that amount by 100,000 expresses the difference
relative to initial capital.

For block lengths 1, 3, 5 and 10 priced match dates, draw 19,999 circular
fixed-length block resamples with deterministic seeds. Apply the same sampled
dates to all strategies and both comparators. Center each bootstrap mean at
its observed mean. The upper distribution of the maximum centered deviation
over all 84 rules gives a one-sided global comparison and single-step
family-adjusted p-values. Use `(1 + exceedances)/(B + 1)` so the Monte Carlo
p-value never equals zero. Also report own-column p-values and two-sided 95%
simultaneous bands using the maximum absolute centered deviation. The exact
benchmark-self/cash-self path remains zero. Duplicated paths stay in the catalog;
common resampling retains their dependence.

Each of the eight comparator/block-length combinations is separately reported;
do not choose the one with the smallest p-value or claim adjustment across these
method choices. All 84 rules define the displayed family, not every model,
feature, threshold or research decision ever examined in the project.

These are **conditional cashflow max-statistic sensitivities**. Recorded
selections and realized stake paths remain fixed; bootstrap samples do not
refit models or regenerate Kelly positions under alternative outcomes.
Stationarity and weak dependence are approximations for this short season and
changing bankrolls. The calculations are not a full implementable-policy White
Reality Check, a guarantee of finite-sample familywise error control or new
evidence collected after fixing the catalog. A non-rejection is not proof that
every edge is zero, and a small adjusted p-value would not independently
validate a profitable strategy.

The circular fixed-block construction follows
[Politis and Romano's original technical report](https://statistics.stanford.edu/technical-reports/circular-block-resampling-procedure-stationary-data).
The motivation for accounting for searching many rules is
[White's data-snooping framework](https://doi.org/10.1111/1468-0262.00152).
The conditional adaptation and its limitations above are this project's own
design; no claim is made that the full original procedure is implemented.

## Preservation and publication

Hash consumed source tables, the frozen catalog, code and method documents
before processing; verify them again before writing a success manifest. Save
all 56 continuous and 224 seasonal metrics, full bet/equity ledgers, every graph
point and the eight-family comparison results. Old models and reports stay
unchanged. The final report includes every frozen strategy definition in its
last appendix, with explicit 4-season versus 2025-only coverage.

After checks, copy the final PDF and editable Word report into the stable
`reports/latest/` folder and link them from root `LATEST_REPORT.md`. Those are
byte-identical copies of the immutable run artifacts, with a small copy-hash
manifest. No forecasts or real wagers are created by this continuation.
