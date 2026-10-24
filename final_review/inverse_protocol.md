# EPL reversal experiment: design fixed before viewing new EPL returns

This document fixes the new EPL variants before their new returns are inspected.
The NBA reconstruction has already been computed separately and is described
here as an exploratory source-method reconstruction, not as a prospective or
pre-analysis NBA commitment.

This extension asks whether reversing the positions of previously bankrupt
strategies produces a funded, profitable account. It is a retrospective
diagnostic chosen after inspecting the original outcomes. It is not a fresh
holdout, an independently selected live policy, or evidence that every losing
strategy is a profitable trading signal in reverse.

## Scope and zero-account inventory

Run every one of the 47 fixed-stake accounts in the canonical 88-account EPL
continuous comparison (31 earlier accounts plus 16 new player-study accounts),
not only the bankrupt subset. Thirteen are bankrupt and 34 are non-bankrupt
controls. Add the four previously bankrupt Bet365 reference-replay contexts,
for 51 total strategy/price contexts: 17 bankrupt contexts and 34 controls.
This cohort-wide comparison is descriptive; adding controls does not remove
the fact the reversal question was prompted by observed bankruptcies.

Use the existing saved populations and prices. Do not change the existing
models, prediction probabilities, strategy thresholds, eligibility filters,
quote modes or original outputs.

- Main EPL four-year comparison: 13 bankrupt accounts. The old strategies are
  S041 and S043 at best quotes. The new player-study accounts are P009, P011,
  P013, P015, P019, P021, P023, P025, P027, P029 and P031.
- Earlier EPL Bet365 policy-replay sensitivity: four additional bankrupt
  account contexts, S033, S039, S041 and S043 at reference prices. These are
  four contexts, not four additional newly fitted models. S041 and S043 also
  occur in the best-price inventory above.
- There are no bankrupt accounts in the original/new common-2025 comparison,
  the 224 old independently reset annual EPL accounts, or the 128 new annual
  EPL accounts. Unfunded fixed-exposure shadow paths have no ordinary final
  capital and must not be interpreted as additional zero-capital strategies.
- The supplied NBA annual fixed-stake results contain two bankrupt 2017/18
  accounts, one for each feature-selection objective. Both annual models are
  logistic regressions. They are not the core experiment's SVM/LR family pair.

The main EPL population is 1,470 fixtures over 453 match dates,
2022/23--2025/26, with initial capital 100,000 and requested original flat
stakes of 1,000. The NBA 2017/18 reconstruction uses 1,075 eligible games,
initial capital 10,000 and flat requests of 100.

## Three meanings of "opposite"

### 1. Reverse already recorded cashflows: identity diagnostic only

For an original back bet of stake s, decimal odds O and outcome indicator I,
the original profit is s(O I - 1). Its mathematical counterparty payoff is
the negative: +s when the original selection loses and -s(O-1) when it wins.

On the original recorded bets and allocated stakes, the mirrored profit is
exactly the negative of recorded profit. Thus an account that starts at
100,000 and ends at zero necessarily has a mirrored arithmetic ending of
200,000. This is an accounting identity, not new predictive evidence.

The entire mirrored path equals 2 B0 minus the original path. It can go
negative before the endpoint if the original first grows above twice its
starting capital. Even a nonnegative mirrored path can fail funding: the
counterparty must reserve s(O-1) per bet, rather than s. Audit same-date
liabilities against opening capital before describing any path as funded.

Only label this view "recorded-exposure sign-reversal diagnostic". It retains
the original bankruptcy-truncated trade list and must never be substituted
for the full-horizon opposite policy below.

### 2. Hypothetical lay at the original price: risk-matched diagnostic

For all original qualifying fixtures across the full horizon, lay the
original selected outcome at its original back odds, but match the original
maximum cash risk rather than silently increasing it. Request liability
R=1,000 per fixture, so the lay counterstake is R/(O-1). Profit is
+R/(O-1) if the original selection loses and -R if it wins.

Reserve the 1,000 liabilities jointly by match date and uniformly scale the
requests to available opening cash and any original date-budget limit before
settlement. No borrowing or same-date settlement reuse is permitted in EPL.
There is one zero-cost funded hypothetical lay replay for each of the 51
contexts. No same-lay-stake-1,000 experiment or additional liability-matched
Dutch variant is promised or run under this protocol.

The outcome direction is the inverse of the original selection, with matched
maximum loss. Its dollar payoff is not necessarily the negative of an
original 1,000-stake back bet: exact original counterparty payoff requires
liability 1,000(O-1), a different amount. The exact recorded-exposure identity
belongs only to the diagnostic in subsection 1.

This synthetic comparison assumes the original back price is also available
for laying. The existing panel contains back quotes, not exchange lay quotes,
liquidity or accepted lay fills. Therefore it is a hypothetical sensitivity,
not a verified tradable result. State liability and counterstake separately.

### 3. Back the other available outcomes: price-supported complement

In football, the opposite of home is draw OR away, not away alone. For
original selection k, let J be the other two H/D/A outcomes and define

    S = sum(1/O_j for j in J).

For total bundle risk R, request stakes

    u_j = R (1/O_j) / S,

so either complementary result returns the same gross amount R/S. The
bundle profit is -R if k occurs and R(1/S-1) otherwise. Its effective decimal
return is 1/S. Use the existing strategy's price mode for every leg: archived
best individual-book prices or the saved Bet365 triplet. Never invent an
unobserved double-chance quote or silently swap only home and away.

The primary comparable-risk implementation requests R=1,000 per fixture,
the same maximum cash loss as the original flat back bet. Allocate all
same-date bundle risks from opening cash, proportionally scaling when needed.
There are two legs but one market decision: frequency and hit statistics
use fixture bundles, while leg count and total turnover are reported too.

At fair zero-margin quotes, S=(O_k-1)/O_k and the complementary back bundle
matches the risk-matched lay at O_k. With an overround, the
other two back prices generally deliver worse complementary payouts.

Some actual quote combinations have S>=1: one of 4,410 possible best-price
combinations and 24 of 4,410 Bet365 combinations in the 1,470-fixture panel.
Those combinations are not necessarily selected by the strategies,
but the implementation must handle them. Their effective decimal return is
at most one, so even a complementary outcome can produce zero or negative
net profit. Do not quietly drop these fixtures or pass the bundle through a
metric function that insists on decimal odds above one.

For each of the 51 contexts, run the primary priced complement at three fixed
hypothetical cost rates: 0%, 2% and 5% of positive net profit of each
fixture's complementary two-leg portfolio. Charge the net positive bundle
profit, not gross payouts or the winning leg before subtracting the losing
leg. Negative bundle profit receives no rebate. These are illustrative cost
haircuts, not actual venue commission schedules. This gives 153 funded
priced-complement accounts and 51 zero-cost synthetic-lay accounts, plus the
17 recorded-exposure identity diagnostics. Report every declared result.

## Full-horizon eligibility and funding

Original selection and qualification are outcome-independent: reconstruct
them on every original opportunity, using the frozen probabilities and
original filters. Eligibility continues beyond the date when the original
account ran out of cash. The original account's actual funded stakes and
bankruptcy stopping time do not decide whether the opposite account gets
later opportunities.

Reproduce each of the 51 original funded 100,000 accounts before accepting
its reversal output. Recover complete qualification calendars by calling the
frozen fixed-stake replay with a sufficiently large diagnostic initial capital
(e.g. 10^12 with a 1,000 request), which prevents cash exhaustion from hiding
later signals. This is an eligibility extraction device, not a reported wealth
path or increased-capital strategy. All reported funded inverses start at
100,000.

Do not apply a new positive-edge requirement to the complementary position
under the original model. That changes the question and would often simply
hold cash: the original model was selected precisely because it preferred
the original position. A profitable inverse would challenge the original
model's selected-bet probabilities, not validate them by definition.

Retain one initial capital allocation per continuous episode. A zero-capital
opposite account remains zero. Same-date liabilities or total bundle stakes
are fixed before any same-date outcome is observed. Report scaling and
capital-shortfall diagnostics. Bet365 reference variants must recompute the
original policy's selections under the reference triplet, not retain choices
from best quotes and call that a policy replay.

## Metrics and independent checks

For every funded variant, report initial/final capital, profit, return on
initial capital, turnover, stake ROI, maximum drawdown, number of market
decisions and legs, frequency, active dates, commitment/scaling statistics,
and its new-model expected gain/loss at the actual allocated stakes.

For a bundle with mutually exclusive outcome payoffs pi_k and original model
probabilities p_k, compute expected gain as sum p_k max(pi_k,0), and expected
loss as sum p_k max(-pi_k,0). They are nonnegative components. This remains
valid when the effective complementary odds are at most one; the ordinary
back-bet formula would incorrectly call a negative amount an expected gain.

Report two distinct success statistics when needed:

- selection hit: the realised outcome lies in the complement;
- profitable bundle hit: net allocated bundle profit is strictly positive.

The latter is the financial hit ratio. Always disclose its definition.
Expected payoff is a claim under the original probabilities, not an observed
winning payoff or proof that a profitable strategy exists.

Independently reconcile every bundle's leg stakes, uniform gross payout on
either complementary outcome, realised profit, probability mass, date-level
cash budget and curve endpoint. Test H/D/A tie order, no-trade dates,
bankruptcy, same-date overcommitment, quote-mode changes, S>=1, and the
recorded-sign-reversal identity. Preserve original source hashes.

## NBA reconstruction boundary

The source annual 2017/18 window trains initially on 2013/14 and 2014/15,
selects features on 2015/16, includes 2016/17 before its final fit, and bets
2017/18. The saved counts are 1,075 games, four calibration-selected features
and six accuracy-selected features; both annual models are ordinary logistic
regressions with the source's default settings.

There are no saved event-level annual probabilities. Re-executing the original
rolling procedure reconstructs them, but an endpoint of zero and matching
feature counts are not a unique fingerprint of the original probabilities.
Label any NBA inverse result as a source-method reconstruction, with its
sample, selected features and financial endpoint checks stated. Do not
mislabel it as an exact saved-weight replication or use the unreconciled
core SVM refit as the annual accuracy model.

For each source qualifying home/away decision, place the opposite side at
that side's own supplied odds. Keep the original home-first IF/ELIF rule
and exact-default probability filter to determine the original pick, then
reverse it. Do not demand a new edge on the reversed side. Use flat 100
from a fresh 10,000 and the source's sequential settlement convention;
describe separately any more conservative common-date funding sensitivity.
The opposite-side quoted payoff is not the arithmetic negative of the
original payoff because the two prices include a margin.

## Interpretation and presentation

Keep the original bankrupt accounts visible beside their inverses. State
explicitly that bankruptcy selected this group after observing returns.
Report every declared variant and zero/negative result; do not promote only
the highest inverse endpoint. Do not reuse the old study's multiple-testing
adjustment as if it covered this new experiment. Fresh validation would
require rules fixed now and probabilities/prices recorded before later games.

The core teaching point is that reversing a realised loss is easy algebra;
demonstrating a funded, price-supported, persistent opposite edge is a
different empirical test. Maximising the project's academic quality means
showing that distinction, complete rules, equal-risk comparisons, honest
limitations and a reproducible result, rather than manufacturing a positive
headline or promising a grade.
