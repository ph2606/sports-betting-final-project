# Premier League results - draft for the combined final report

## Evidence status and supplied material

The supplied `ML Sports/EPL_Project_Presentation.pdf` is the same 35-page
presentation as the preserved `epl_presentation/results/20261021_implemented`
export, byte for byte. It is not a newer experiment and must not be counted as
additional evidence. The numerical results below come from the underlying
saved tables. The compilation adds no fitted model, forecast or settled result.
The latest operational evidence discussed here is the saved October 20, 2026
snapshot; it must not be presented as a live result update on October 23.

## EPL data and adaptation of the common question

The football component predicts three mutually exclusive outcomes: a home win,
a draw or an away win. Target fixtures involve at least one of the 20 saved
2026/27 Premier League clubs. Historical opponents remain valid context, so
relegated clubs are not added to the current focal list but their earlier games
are retained when reconstructing form. This present-day cohort introduces
selection/survivor bias. In particular, its 2025/26 evaluation contains 374
fixtures rather than all 380 league games.

Football-Data supplies results, team statistics and archived individual-book
odds; Understat supplies displayed team expected goals; FPL supplies historical
player contributions and later squad-form features. The expanded player loader
contains 253,509 historical player-match records for 2016/17-2025/26 and 4,551
current-season records through 70 completed fixtures. Its October 20 capture
contains 668 current player summaries. Historical performance features use only
strictly earlier match dates. A target game's score, shots, xG, participants and
minutes cannot determine its own predictors. Current injuries, present rosters,
ownership and prices are not used to backfill historical availability.

The shared project question-accuracy-oriented versus calibration-oriented model
selection-is tested first in a locked EPL experiment. The subsequent source
comparisons and large strategy laboratory are separate exploratory extensions.
These phases must not be combined into a single claim of untouched evaluation.

## Proposal-aligned experiment: accuracy versus calibration selection

The four candidate families are logistic regression, random forest, SVM and MLP,
with 12 seeded tuning trials per family per selection branch. Training spans
2014/15-2020/21; 2021/22 tunes hyperparameters, 2022/23 fits a scalar temperature,
2023/24 selects the model family, and 2024/25 selects a trading threshold.
The frozen choices are evaluated on 2025/26. Base estimators and preprocessing
are refitted through 2021/22 before calibration and are not refitted afterwards.
Both branches receive temperature calibration, so the comparison concerns the
model-selection objective, not calibrated versus deliberately uncalibrated
predictions.

Accuracy selection chooses an SVM using two earlier team box-score features;
classwise-ECE selection chooses an MLP using one earlier corners feature.
Player/xG candidates do not survive this first small-budget selection path.
This phase alone therefore cannot establish their incremental value.

**Table EPL-1. Locked 2025/26 probability scores; identical 374 fixtures.**

| Predictor | Accuracy | CW-ECE, 10 bins | Log loss | Brier |
|---|---:|---:|---:|---:|
| Accuracy-selected SVM | 48.13% | 6.20% | 1.0763 | 0.6446 |
| Calibration-selected MLP | 44.39% | 4.16% | 1.0564 | 0.6356 |
| Normalized Bet365 probabilities | 48.66% | 4.36% | 1.0191 | 0.6120 |
| Training class frequencies | 42.51% | 2.90% | 1.0851 | 0.6566 |

The calibration branch has lower point ECE and proper probability losses, but
lower classification accuracy. The normalized bookmaker benchmark has lower
log loss and Brier than either learned branch. The near-constant frequency
baseline has the smallest ECE despite weak probability scores; calibration
error by itself is not a sufficient measure of betting usefulness.
The conditional 95% whole-date bootstrap interval for the calibration-minus-
accuracy ECE difference is [-0.0437, 0.0068], and its log-loss interval is
[-0.0451, 0.0058]. Both include zero and omit model-selection uncertainty.
Because the two branches choose different features and model families, this
is not a causal experiment isolating calibration alone.

### Primary and secondary trading decisions

The primary trading threshold must have positive validation profit and at least
30 bets in 2024/25. Neither branch meets this rule. Consequently both primary
policies hold cash on the test: zero bets, zero turnover and undefined ROI.
A zero return from holding cash must not be reported as a successful betting
strategy.

A separately predeclared secondary policy places at most one bet per match,
choosing the outcome with maximum estimated return `p * decimal odds - 1` only
when it exceeds 5%. Its original account begins with 1,000 units and its fixed
stake is 10 units. Quarter Kelly stakes use the opening cash of the match date,
with a 2% per-bet cap; same-date requests are proportionally reduced if together
they exceed cash. No same-date winnings finance another request.

**Table EPL-2. Secondary fixed-5% test replay; native account units.**

| Branch | Odds | Stake rule | Bets | Profit | Stake ROI | Conditional 95% ROI interval |
|---|---|---|---:|---:|---:|---|
| Accuracy SVM | Best saved book | Fixed 10 | 371 | -83.30 | -2.25% | [-18.83%, 15.45%] |
| Accuracy SVM | Best saved book | Quarter Kelly | 371 | -377.05 | -7.01% | [-23.18%, 11.92%] |
| Calibration MLP | Best saved book | Fixed 10 | 333 | 13.70 | 0.41% | [-20.08%, 22.07%] |
| Calibration MLP | Best saved book | Quarter Kelly | 333 | -153.91 | -2.59% | [-20.93%, 17.72%] |
| Accuracy SVM | Bet365 | Fixed 10 | 365 | -186.70 | -5.12% | [-20.25%, 11.15%] |
| Calibration MLP | Bet365 | Fixed 10 | 314 | -23.50 | -0.75% | [-19.46%, 19.70%] |

The MLP's small positive best-price fixed-stake estimate does not survive as
reliable evidence of positive returns: its interval spans substantial losses
and gains, its Bet365 fixed-stake result is negative, and its quarter-Kelly
result is negative. The primary cash decision remains the main locked-policy
result. The later 100,000-unit presentation replays scale initial capital and
fixed stakes by 100; percentage returns, hit ratios and drawdowns remain the
same, but monetary profit numbers must be labeled with their capital basis.

## Exploratory team, market and player extensions

The rolling extension evaluates 1,470 common quoted fixtures in four seasons:
368 in 2022/23, 360 in 2023/24, 368 in 2024/25 and 374 in 2025/26. Every fold
trains and tunes in earlier seasons, uses a separate calibration season, then
evaluates the following season. Correct chronological fitting protects each
individual information boundary, but cannot make already inspected historical
outcomes a fresh confirmatory test.

The earlier source study crosses logistic and market-residual families with
team, team+xG, team+seven-FPL-aggregate and combined feature blocks. A
market-residual model begins with normalized Bet365 probabilities and learns
regularized feature-driven log-odds corrections. The expanded study separately
crosses logistic and histogram-boosting families with matched team controls
(19 inputs), player form (96), player form plus role/XI/depth (222), and team plus
full player block (235). All models retain the common primary fixture sample.

**Table EPL-3. Selected pooled scores on 1,470 identical fixtures.**

| Predictor | Accuracy | Log loss | Brier |
|---|---:|---:|---:|
| Raw market benchmark | 54.42% | 0.9662 | 0.5743 |
| Best learned by log loss: market residual + team/FPL | 54.15% | 0.9693 | 0.5751 |
| Legacy team logistic | 52.93% | 0.9876 | 0.5889 |
| Pure-player form logistic | 50.07% | 1.0218 | 0.6114 |
| Class-frequency baseline | 44.29% | 1.0700 | 0.6471 |

The raw market has the lowest pooled log loss and Brier among all 19 comparable
series. The best learned model is not an odds-free forecast: it uses the
bookmaker probability offset. All six new player-based variants have worse
pooled log loss than their matched same-algorithm team control. All 32 new
continuous strategy accounts lose money, with 11 exhausting their cash.
This negative result concerns the tested player representations and models;
it is not a general claim that player information cannot help.

Player form summarizes earlier FPL performance in five- and ten-fixture slots.
The richer squad block estimates a fixed 1-GK/4-DEF/4-MID/2-FWD lineup from prior
minutes and tracks depth/continuity. It is not a confirmed starting XI or an
injury feed. Historical role fallbacks sometimes use season-fixed archived
position proxies whose original publication times are unverified. These
position-based histories are not a fully timestamp-verified lineup dataset.

## Money progression, representative strategies and capital rules

The complete common-season graph contains all 116 strategies-84 earlier rules
and 32 new rules-over the same 374 fixtures, with each account starting at
100,000 units. It has 33 positive, 75 negative and eight flat/cash accounts.
A separate continuous graph contains 88 comparable strategies across all four
seasons with no annual resets: 24 positive, 64 negative and 13 bankrupt.
The 28 first-study configurations lack comparable earlier rolling predictions
and are not backfilled into the four-year graph.

Suggested figure files: `epl_presentation/results/20261021_implemented/figures/`
`all_accounts_2025.png` and `all_accounts_continuous.png`. Their underlying
CSV paths are in `epl_evidence.json`, with 13,224 and 39,952 graph points.
Every line is a model/entry/price/stake combination; 116 strategies do not mean
116 independently trained algorithms.

**Table EPL-4. Representative continuous four-year accounts; initial 100,000.**

| Strategy | Final capital | Hit ratio | Frequency | Expected gain/loss per trade | Stake ROI | Max drawdown |
|---|---:|---:|---:|---|---:|---:|
| S029: best learned predictor, flat stake | 123,340 | 31.04% | 78.03% | 852.95 / 663.70 | 2.03% | 31.88% |
| S033: simplest class-frequency predictor | 29,760 | 23.01% | 98.44% | 1,739.52 / 611.96 | -4.85% | 89.49% |
| S017: team-only performance model | 119,790 | 29.57% | 84.42% | 962.54 / 648.43 | 1.59% | 40.35% |
| P009: player-only form model | 0 | 25.00% | 64.22% | 1,098.04 / 618.22 | -10.87% | 100.00% |
| S060: highest four-year ending account | 195,190 | 30.69% | 80.68% | 2,226.45 / 1,652.54 | 2.99% | 38.35% |

The first four rows choose the largest model-implied edge strictly above 5%
and request a fixed 1,000 per bet at best archived prices. This is 1% of
INITIAL 100,000, not a fixed 1% of changing capital. S060 uses a combined
market-residual forecast and quarter Kelly capped at 2% of date-start cash
per bet, with a 10% combined date-level budget. Cash-only rules request zero;
dynamic-percentage alternatives request 1% of current date-start cash. All
requests share opening cash, are scaled jointly when necessary and cannot
borrow or reuse same-date winnings.

Expected gain and loss per trade are model-probability-weighted components at
the recorded stake, not conditional averages of winning and losing payoffs.
They can remain positive even when realized performance is poor. Hit ratio
uses bets as its denominator; classification accuracy uses every evaluated
match. Stake ROI divides profit by turnover, while capital return divides
profit by the initial bankroll. In particular S060's 95.19% capital increase
is not a 95.19% stake ROI: its stake ROI is 2.99%.

P028 is the highest ending 2025/26 account at 167,925 (+67.93% capital return),
but its uninterrupted four-year account ends at 16,675 (-83.33%). Its apparent
single-season success does not identify a stable winner. The original
84-rule conditional block-bootstrap selection audit does not reject its
global null. It does not provide a new adjustment for the 32 added strategies,
model refitting, or newly repriced paths. S060's own recorded conditional ROI
interval also crosses zero.

### Execution and the final EPL finding

The quote sensitivity study recomputes policy selections and stakes under
Bet365 reference prices rather than merely changing payouts. For S060,
original best-price profit is 95,190, full Bet365-replay profit is 55,952,
and fixed-original-exposure payout repricing gives -30,549. These contrasts
answer different questions; none is an isolated causal price effect.
Some fixed-exposure shadows in the wider study require extra capital, so they
must not be shown as normally funded wealth accounts. Archived quote clocks,
accepted fills, limits and costs are unverified. No executable arbitrage or
prospective trading profit is established.

The saved October 20 prospective snapshot resolves ten independent fixtures
with 40 correlated predictions from four models; all four score six correct
outcomes out of ten. It also retains 40 earlier-model and 80 new-model forecasts
for the same next ten October 23-25 fixtures. These are pending in that saved
snapshot, not an updated statement about results on the final report date.
The reviewed export copies the same 80 records and is not another release.
Missing pre-kickoff quotes and a trade ledger prevent prospective betting P&L.

The EPL evidence therefore shows an accuracy/calibration trade-off in the
initial selected procedures, without a validated active primary betting rule.
Its exploratory extensions find stronger pooled proper scores for market
probabilities and no improvement from the new player-feature expansions.
Positive historical account paths remain conditional on strategy search and
unverified execution. This conclusion is specific to the implemented EPL
experiments; it does not override different NBA evidence or combine the two
leagues into an artificial joint portfolio.
