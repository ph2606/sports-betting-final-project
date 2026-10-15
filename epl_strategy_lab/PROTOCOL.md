# Shared-capital historical strategy comparison

## Population and information sources

Use the exact intersection of the first-study 2025/26 test predictions, all 11
rolling-study 2025/26 probability series and valid reference/best-book prices.
Audit that this intersection equals every source's full 374-match comparison
population, with matching match IDs, dates and results. There are 113 distinct
settlement dates, from 2025-08-15 to 2026-05-24. This is the existing current-club
research cohort's historical match population, not a claim to include all 380
league fixtures. Historical opponents remain in match records as required for
settlement and feature history.

The first experiment contributes its frozen accuracy-selected SVM and
calibration-selected MLP. Its chronological stages used initial training from
2014/15 through 2020/21, tuning on 2021/22, temperature calibration on 2022/23,
family selection on 2023/24 and policy validation on 2024/25 before the 2025/26
test season. After tuning, base models and preprocessing were refitted through
2021/22, then frozen before the separate calibration season. Both validated primary policies hold
cash. Their saved threshold is 1,000,000 with reason
`no_admissible_positive_validation_strategy`.

The rolling comparison contributes four feature groups, each with a logistic
and a market-residual model, together with class-frequency, raw-market and
temperature-adjusted-market baselines. For its 2025 evaluation, the rolling
protocol initially trains through 2022/23, tunes on 2023/24, refits through
2023/24 and calibrates separately on 2024/25. Consequently
the first and rolling studies have different information horizons: their account
curves are comparable cash replays, not a controlled comparison of model
architectures alone. Feature groups are team, team plus expected goals, team
plus historical player information, and the combined group. Exact feature
inventories remain in the frozen modeling artifacts.

The three new probability series are an equal-weight mean of the four logistic
models, an equal-weight mean of all eight learned rolling models, and a 50/50
mean of the combined logistic model and the raw reference-market probabilities.
Weights are fixed without selecting the best historical return. Every source
probability vector and its resulting ensemble must be finite, nonnegative and
sum to one.

## Catalog and outcome choice

The catalog contains 84 uniquely identified configurations:

- 16 first-study policies: two models, primary cash/secondary 5% edge,
  reference/best prices and fixed/quarter-Kelly stakes.
- 22 rolling-study policies: 11 probability series with a 5% edge threshold,
  best prices and fixed/quarter-Kelly stakes.
- 12 additional saved threshold-diagnostic rules: first-study models with best
  prices, fixed stakes and thresholds 0%, 2.5%, 7.5%, 10%, 15% and 20%. The 5%
  versions are already included in the first 16.
- 34 new exploratory benchmark, ensemble, sizing, consensus and eligibility
  policies, fully specified in `catalog.json` and the final report appendix.

For a decimal price O and predicted probability p, net expected return per unit
staked is `edge = p * O - 1`. Value policies choose the largest edge among
eligible H (home win), D (draw) and A (away win) outcomes. Outcome and odds filters apply **before** this
choice; the qualifying edge must then be strictly greater than the configured
threshold. There is at most one selected outcome per match. All ties use H,
then D, then A. Model-favorite policies maximize the named model's probability;
market favorites/underdogs maximize/minimize the raw reference-market
probability. The naive benchmarks do not require positive model edge.

The consensus policy first chooses the eight-model ensemble's largest-edge
outcome. That ensemble edge must exceed 5%, and at least six of its eight
constituent models must have strictly positive edge at the same selected price.
The five new unconditional class/market controls S039-S043 use raw market
probabilities to describe expected payoffs; those probabilities do not impose
an edge filter. Model-favorite controls S044-S045 use their named combined
model's probabilities, and the older class-frequency value policies use the
saved class-frequency probabilities.

The 1.5 to 5.0 decimal-odds eligibility range is inclusive. The home/draw/away
specialists restrict candidate outcomes before selection. No thresholds,
weights, filters or sizing variants are selected from their resulting returns.
The earlier threshold diagnostics are displayed as diagnostic replays, not as
newly selected primary strategies.

## One continuous account per strategy

Each strategy starts with 100,000 monetary units and no open position. A fixed
stake requests 1,000, equal to 1% of initial capital. A dynamic 1% stake requests
1% of the balance at the start of the match date. Kelly requests are
`date_start_balance * min(per_bet_cap, fraction * max(edge / (O - 1), 0))`.
The configured fractions are one eighth, one quarter or one half; the per-bet
caps are specified separately in the catalog.

All requests on a date use the **same starting balance** and are allocated
before any match on that date settles. If their sum exceeds the available
balance, scale every request by the same factor. A policy with a 10% date cap
instead scales to the smaller of available cash and 10% of its date-start
balance. A zero balance is absorbing. Never use one same-date match's winnings
to finance another same-date stake, borrow money, reset an account, resize
after observing its outcome, or omit a losing policy from the chart.

A winning wager returns `stake * O` including its principal; a losing wager
returns zero. Net profit is gross return minus stake. Date-close balance is
date-start balance minus total allocated stakes plus gross returns. Every
eligible date remains in the equity ledger, including dates with no trade.
The graph adds a common 100,000-unit anchor one calendar day before the first
match and uses steps between date closes. This is date-level cash accounting;
the archive does not support an intraday execution reconstruction.

## Metrics and uncertainty

Reuse the audited `epl_strategy.metrics` implementation with initial capital
100,000, 374 predictions and 374 valid priced matches for every strategy.
Expected positive payoff is `sum(p * stake * (O - 1))`; expected loss magnitude
is `sum((1-p) * stake)`. Their difference is model-implied expected net profit.
Report totals and per-trade amounts separately from realized winning/loss
averages and realized expectancy. Trading frequency is bets divided by all
374 priced opportunities. Return on initial capital and ROI on turnover have
different denominators and are labeled separately.

Report drawdown from the initial balance and subsequent running peaks,
turnover, date exposure, profit factor and whole-date bootstrap confidence
intervals. Bootstrap resamples recorded date cashflows and stakes; it does not
refit models or re-size a new counterfactual Kelly path, and is conditional on
the observed selections. The intervals do not adjust for testing many
strategies. No-trade strategies have flat balances, zero totals/activity and
undefined per-trade means or ratios.

## Interpretation and reproducibility

This is a hypothetical archived-price replay with no added fees, payout
haircuts, bookmaker stake restrictions, quote-expiry model or deposit interest.
The earlier robustness extension separately reports hypothetical costs. All
four quote clock fields are absent in the common archived price panel;
best-book prices do not establish simultaneously available execution.

These outcomes were already inspected before the new catalog was defined.
Every new strategy and the enlarged account comparison are exploratory;
neither a highest ending balance nor a positive conditional interval is an
independent validation. A fresh prospective protocol would need to fix the
rules before observing subsequent outcomes. Pending prospective forecasts are
preserved separately and are not assigned fabricated settled returns here.

The builder records source and code SHA256 hashes, audits common identities,
saves the entire catalog, per-bet ledger, date equity and all metrics, and checks
that catalog IDs equal metric, chart and appendix IDs. Original data, fitted
models and earlier reports remain frozen. The last part of the new report is
an appendix with a complete explanation for every strategy ID.
