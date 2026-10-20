# Prospective cohort observation protocol — October 20, 2026

The precommitted October 14 model alternatives and training chronology remain
unchanged. This continuation observes the original October 17–19 targets and
starts a separate future cycle; it does not retune a model or choose a winner
from ten games. The historical 84-strategy catalog and all original results
remain preserved.

## Cohort and immutable evidence

The original forecast ledger is anchored to Git commit
`8d1dc519b7fceb52247a240435424e12ca1b9708` and SHA-256
`f828b68d2a3deb44457c0b92629d3e7c6655cfa8d8eb8f69ff30607b73680214`.
It contains 40 records: four declared logistic feature groups for the same
10 fixtures. New releases append after this exact byte prefix. Earlier
versions remain primary. Four predictions of one result are correlated;
the independent fixture count is ten, never forty.

A new capture retains response bytes, URL, actual UTC observation clock,
HTTP status and hashes. A results-only capture requests the five core
endpoints; a separate complete player capture refreshes the current registry.
An omitted player-summary request is recorded as omitted, never as complete.
The provider's last completed match date is reported separately from our
retrieval clock. Source results may lag elapsed kickoff, so no result is
inferred merely because a match should have finished.

Before settlement, independently verify the raw official FPL bootstrap and
fixture response hashes, exact saved 20-club membership/stable codes and
season calendar. Reconstruct normalized fixture fields and require explicit
finished status, integral nonnegative goals, matching participant identity,
and observation after actual kickoff. Corroborate finished released fixtures
against same-date, canonical-team Football-Data score records. Conflicts fail
closed. Validate the full proposed scoring batch before calling the frozen
outcome writer. Existing outcomes cannot be overwritten. The original pending
evaluation stays dated; a new evaluation records newly available outcomes.

Primary capture endpoints are the official
[FPL fixtures](https://fantasy.premierleague.com/api/fixtures/) and
[FPL bootstrap](https://fantasy.premierleague.com/api/bootstrap-static/),
[Football-Data 2026/27 E0](https://www.football-data.co.uk/mmz4281/2627/E0.csv),
and [Understat 2026 league data](https://understat.com/getLeagueData/EPL/2026).
Snapshots preserve the exact responses used rather than relying on later
versions of these changing URLs.

## Predictive evaluation and uncertainty

Only the original, earliest released version of each model/fixture is scored.
Pending results remain pending. Every original model/fixture pair must be
present; missing or conflicting identities cannot silently shrink the sample.
Results and source observation clocks come from the outcome ledger, while
probabilities come exclusively from the released forecast ledger.

Forecast accuracy uses the largest H/D/A probability, with deterministic
H/D/A ordering for ties. Log loss is the mean negative natural logarithm of
the observed outcome's probability (machine-precision clipping follows the
established scoring implementation). The unscaled multiclass Brier score is
the mean sum across three classes of squared probability error, range [0,2].
Classwise ECE averages three one-versus-rest equal-width-bin errors; 5/10/15
bin results are descriptive and especially unstable with ten fixtures.

Accuracy intervals use the 95% Wilson score formula. Mean log-loss and Brier
intervals use 9,999 fixture-resampling replicates, fixed seed 20261020. The
six pairwise model comparisons use matched fixtures and shared resampling
indices for all score differences. Differences are model A minus model B;
negative log-loss/Brier differences favor A, while positive accuracy
differences favor A. These percentile intervals are descriptive, are not
adjusted for six comparisons, and support neither winner selection nor a
reliable claim about long-run calibration or profitability. Repeating this
review on later cohorts does not create sequential-testing significance.

## Prices, trading and the next cycle

The original release recorded no usable pre-match reference triplets and no
trade decisions or allocated stakes. Its 60 quote-dependent variants remain
withheld. Later archived pre-closing/closing columns are not substituted as
if they had been observed before kickoff. Prospective hit ratio for trades,
expected trading gain/loss, ROI, capital return and a money curve remain
unavailable. Forecast accuracy is explicitly distinct from betting hit ratio.
The existing retrospective strategy report retains all its required trading
statistics and graphs; no hypothetical future trade is added to them.

The next cycle uses a new complete player snapshot and the existing frozen
model bundles. No 2026/27 outcomes enter fitting, tuning or calibration.
Recently completed matches may enter strictly lagged live features for later
targets under the original feature-date rules. Release times and target
kickoffs are rechecked; quote-dependent variants still require the original
complete Bet365 observation no more than one hour old. Source publication
and execution remain unverified. All variants and exclusion reasons remain
visible; the ten observed outcomes do not change which models are declared.

## Reproduction

New exports snapshot original, as-of forecast and as-of outcome ledgers,
record raw source and model hashes, and independently reconcile per-fixture
and aggregate scores. All consumed inputs and implementation files are
hashed before and after building. Old result folders are never overwritten.
The combined report labels preserved October 15 material as a dated view,
prepends the current prospective evidence, retains all historical graphs,
and ends with all 84 exact strategy definitions. Stable latest-report copies
are published only after the completed export manifest is written.
