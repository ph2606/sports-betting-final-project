# Exploratory rolling-origin source ablations

Protocol date: October 13, 2026. Acquisition snapshot: October 6, 2026.

This is a separate, retrospective exploratory study. The first experiment has
already examined the 2025-26 outcomes and used earlier seasons for fitting,
calibration, selection and validation. **Every result from this new study is
exploratory; 2025-26 is not a fresh or untouched holdout.** Chronological folds
prevent information from later seasons entering an individual fit, but they do
not erase this prior examination or make the redesign prospectively validated.

The question is whether fixed blocks of lagged xG and past player contributions
add predictive information to fixed team statistics, and whether they improve a
market-informed model beyond raw and temperature-recalibrated market forecasts.
This directly examines a question the first run could not answer: its small
ranked/forward-selected set retained only team box-score features.

## Preservation and scope

The original [methodology](METHODOLOGY.md), [coverage audit](FEATURE_COVERAGE.md),
`results/`, executed first-study notebook, fitted models and workbook remain
unchanged. New outputs belong in `ablation_results/`. Record pre-run checksums of
the first-study artifacts and verify them after completion. Record the new
protocol hash before fitting and verify that it is unchanged afterward.

No acquisition table, raw source, original feature implementation or original
result is corrected in place. Any FPL identity reconciliation is a separately
audited, deterministic in-memory overlay applied equally to every new group.
Unresolved or conflicting identities remain unavailable; do not choose a repair
by its predictive or betting result.

The population remains E0 Premier League fixtures involving at least one of the
20 verified 2026-27 clubs. Other clubs remain historical opponents. This is a
present-day cohort applied retrospectively, with survivor/selection limitations;
it is not the whole historical league. The 2025-26 population has 374 eligible
fixtures, not 380. The 50 observed 2026-27 fixtures are outside this rolling-origin
evaluation and do not provide a fresh full-season test.

## Locked chronological roles

Season labels below use their starting year. Each evaluation season has three
strictly preceding, disjoint blocks: initial training, hyperparameter tuning,
and probability calibration.

| Evaluation | Initial training | Tune C | Calibrate temperature |
|---|---|---|---|
| 2022-23 | 2016-17 through 2019-20 | 2020-21 | 2021-22 |
| 2023-24 | 2016-17 through 2020-21 | 2021-22 | 2022-23 |
| 2024-25 | 2016-17 through 2021-22 | 2022-23 | 2023-24 |
| 2025-26 | 2016-17 through 2022-23 | 2023-24 | 2024-25 |

For each group and model family:

1. Fit each `C` in **0.03, 0.3, 3.0** on initial training only. Choose the minimum
   tuning-season multiclass log loss; exact ties choose the smaller C.
2. Refit the selected model and preprocessing on initial training plus tuning.
3. Freeze the base model and preprocessing. Fit one scalar temperature on the
   separate calibration season, minimizing log loss with the existing fixed
   `log(T)` bounds `[-3, 3]`.
4. Score the evaluation season without any further fit, feature selection or
   calibration update. Earlier completed games may update a later game's lagged
   inputs, but never the frozen fitted parameters.

An evaluated season may legitimately enter the training history of a later
rolling-origin fold. Each saved prediction must retain its own outer season,
fitting roles, chosen C and calibration temperature. A block must contain all
three outcome classes. Do not collapse tuning and calibration into one season.

## Fixed predictors and four groups

No supervised screening, KS filtering, ranking, forward selection or top-18
candidate restriction is performed here. Features are fixed before this study's
scores are inspected. All values are computed from strictly earlier calendar
dates; a match's own score, xG, appearances or fantasy points cannot enter its
predictors. Same-date results cannot update another fixture.

The common team performance block has nine columns:

```text
feat_diff_std_goals_diff
feat_diff_roll10_goals_diff
feat_diff_std_shots_on_target_diff
feat_diff_roll10_shots_on_target_diff
feat_diff_std_corners_diff
feat_diff_roll10_points
feat_home_prior_season_win_pct
feat_away_prior_season_win_pct
feat_diff_rest_days
```

`feat_diff_rest_days` is the home club's days since its last earlier E0 fixture
minus the away club's corresponding value. It is EPL rest, not a verified count
of days without cup, European or international matches. Missing rest stays
missing. Previous-season percentages describe EPL performance; a promoted
club's missing prior EPL season is not replaced with a lower-division percentage.

The common team context block has four columns: home and away versions of
`prior_season_missing` and `promoted_from_outside_epl`, each with the `feat_`
prefix. The promotion flag means absence from the observed previous EPL season,
not independent verification of a promotion transaction.

**Every group also receives the same eight source-coverage controls:** home and
away versions of `us_roll10_observed_matches`, `fpl_roll10_observed_matches`,
`us_history_missing`, and `fpl_history_missing`, each with the `feat_` prefix.
Consequently, the team group is a **team-performance model with shared source
coverage controls**, not a completely source-independent baseline.

The xG block adds four columns:

```text
feat_diff_std_us_xg_for
feat_diff_std_us_xg_against
feat_diff_roll10_us_xg_for
feat_diff_roll10_us_xg_against
```

The player block adds seven columns:

```text
feat_diff_roll10_fpl_total_points
feat_diff_roll10_fpl_bps
feat_diff_roll10_fpl_assists
feat_diff_roll10_fpl_saves
feat_diff_roll10_fpl_influence
feat_diff_roll10_fpl_creativity
feat_diff_roll10_fpl_threat
```

| Group key | Included columns | Count before imputation indicators |
|---|---|---:|
| `team` | Team performance, team context, shared source coverage | 21 |
| `team_xg` | Common block plus xG | 25 |
| `team_player` | Common block plus player contributions | 28 |
| `combined` | Common block plus both source blocks | 32 |

`std` means the mean over earlier completed matches in the same season.
`roll10` means the mean within the last ten earlier completed E0 fixture slots,
crossing season boundaries; unavailable source observations inside those slots
are skipped, not replaced by zero or by older observed source games. A `diff`
subtracts the away club's historical value from the home club's. Within a
historical club fixture, `goals_diff` and similar box-score differences mean
that club's own value minus its opponent's.

FPL inputs aggregate actual earlier fixture-club player records. They are not
target-match lineups, prospective player availability or current-roster form.
Current injuries, ownership, valuations, current club mappings, source forecasts,
season-final totals and target minutes are excluded. Newer FPL defensive/xG
fields are excluded from this fixed block because their longitudinal definitions
and coverage are less comparable. Fantasy points, bonus scoring and assists
still have provider-specific definitions and rule changes.

## Models and benchmarks

Each of the four groups is fitted with regularized multinomial logistic
regression and a regularized market-residual logit model. This gives eight
source/model combinations per fold, with three tuning trials each. Refit all
numeric median imputation, missingness indicators and standardization on the
fitting block only. Use `keep_empty_features=True`; an all-missing training field
does not acquire a median from tuning, calibration or evaluation observations.
During the final refit, the fitting block is initial training plus tuning.

The market probabilities use the complete **native preclosing Bet365 triplet**:
`q_k = (1 / odds_k) / sum_j(1 / odds_j)`, for H, D and A. They are proportional
de-vigged implied probabilities, not guaranteed true probabilities.

The residual model starts with `log(q)` and adds two linear adjustments for H
and D, fixing the away adjustment to zero. For standardized/imputed predictors
z, its logits are:

```text
log(q_H) + b_H + z @ w_H
log(q_D) + b_D + z @ w_D
log(q_A)
```

Fit mean multiclass cross-entropy plus
`(||w_H||² + ||w_D||²) / (2 * C * n_fit)`; intercepts are unpenalized. The common
C grid gives a common search budget and loss-normalization scale. Reference-away
residual coefficients and symmetric multinomial logistic coefficients have
different penalty geometries, so their effective regularization is not identical.
Calibrate the full resulting logits on the calibration season.

Report three benchmarks on the identical evaluated fixtures:

- Raw de-vigged Bet365 (`market_only`, `baseline`).
- The same market probabilities with a scalar temperature fitted only on the
  calibration season (`market_only`, `market_temperature`).
- H/D/A class frequencies from the combined initial-training and tuning block
  (`class_frequency`, `baseline`).

Residual improvements must be compared with temperature-only market calibration
as well as the raw market; otherwise a gain can reflect simple market confidence
recalibration rather than incremental team/player information.

## Common populations, missingness and source limits

The primary population is the same complete-reference-odds fixture intersection
for all groups and both model families. An unavailable extra source is not a
reason to discard a primary fixture. Use training-fitted imputation and report
missingness/observed-count distributions by season and home/away club status.
Coverage controls must enter every group, so a source-added group cannot obtain
an advantage merely from receiving source-availability controls absent in team.

This reduces coverage confounding; it does **not** prove that any improvement is
caused by sporting information. Coarse counts do not fully describe field-level
missingness, and additional imputation indicators can expose availability
patterns. Median-filled values are computational placeholders, not observed
zero or average player performance. Inspect the complete-history sensitivity
before interpreting a source addition, and keep coverage caveats in the result.

The `complete_source_history` sensitivity is **evaluation-only**. Train, tune
and calibrate on the same full matched timeline as the primary analysis. Score
the exact same frozen predictions again on one common mask requiring:

- Both clubs have at least eight observed Understat matches among their prior
  ten E0 fixture slots.
- Both clubs have at least eight observed FPL matches among those slots.
- Every fixed performance input across the union of all groups is nonmissing.

Apply this same mask to every model and benchmark. Do not refit on the subset,
relax a threshold for one group or create group-specific comparison samples.
Because prior-season percentages are among the performance inputs, the mask
also excludes missing-prior-EPL-season cases, including many promoted clubs.
It measures a narrower, well-observed population rather than the whole cohort.

For any evaluated season/scope, fewer than 30 fixtures or absence of any H/D/A
class produces an explicit skipped-evaluation audit record, not a silently
missing score or a relaxed eligibility rule.

Whole-league Football-Data histories cover both clubs' box scores. Saved
Understat histories for noncohort opponents can omit their matches against other
noncohort clubs. FPL histories can be entirely absent for those opponents.
Reconstructing missing early FPL opponent names cannot create uncollected
noncohort player histories. Nineteen historical Understat fixtures with different
printed dates remain unmatched; do not shift dates to obtain more coverage.

The read-only audit of the **preserved first-study frame**, before separate FPL
identity reconciliation, found these coverage counts. They diagnose the starting
data; the new study must export its own post-reconciliation audit.

| Evaluation season | Common-reference fixtures | Complete-history evaluation subset before reconciliation |
|---|---:|---:|
| 2022-23 | 368 | 153 |
| 2023-24 | 360 | 205 |
| 2024-25 | 368 | 205 |
| 2025-26 | 374 | 204 |

The original 2016-17 through 2018-19 frame had zero rows satisfying that complete
intersection because 17,465 early FPL player rows lacked opponent names. This
does **not** shrink the initial training block: completeness is evaluated only
at scoring time. In 2025-26, 51 home-club and 51 away-club rows had no observed
FPL history, principally reflecting the saved cohort scope. Preserve this
diagnosis even if source-identity reconciliation improves early coverage.

## Metrics, paired uncertainty and multiplicity

Use H/D/A column order throughout. Primary predictive comparison is multiclass
log loss; also report the multiclass Brier score, accuracy and ten-bin classwise
ECE. Lower proper scores are better. Low ECE alone can reward nearly constant
probabilities and does not establish information gain or profitability.

Report each outer season and a match-weighted pooled result for both populations.
Pair comparisons on exactly the same outer-season/match-ID rows, settlement
labels and dates. Within each model family, compare each source-added group with
team; compare models with the raw market; compare every residual group with the
temperature-only market. Report the market-temperature and class-frequency
benchmarks against the raw market as well. Do not select a favorable subset of
contrasts after seeing their signs.

For paired log-loss, Brier and accuracy differences, use **1,000** bootstrap
replicates with seed **42**. Resample whole calendar dates with replacement
**separately within each outer season**, keeping all fixtures on a sampled date
together and using the same sampled dates for candidate and reference. For the
pooled result, combine date-level difference sums and counts across the sampled
season strata, then divide total difference by total sampled match count. This
preserves a match-weighted pooled estimand rather than treating each season as
one equally weighted observation.

The 95% intervals are pointwise, conditional and descriptive. They do not
include model fitting, C selection, temperature fitting, source repair or
protocol-design uncertainty; date resampling also does not remove dependence
between dates or overlapping training folds. Multiple groups, model families,
metrics, populations and season/pooled views create many comparisons. Report
all planned comparisons and their denominator; no multiplicity adjustment or
confirmatory rejection claim is made. An interval excluding zero is an
exploratory association requiring a genuinely later prospective study.

## Secondary betting summaries and timing boundary

If betting summaries are exported, the rule is fixed at **5% expected-value
edge**, one selection per match, best complete individual-book preclosing
prices, fixed stake 10 or quarter Kelly capped at 2% of date-start bankroll,
initial capital 1,000. Same-date commitments use date-start capital and scale
to available bankroll. These descriptive summaries are not a new threshold
search or a replacement for the preserved first study's cash-holding primary
policy. Do not tune the edge threshold on an outer evaluation season.

The odds panel excludes aggregate maxima/averages, exchanges, incomplete or
nonfinite triplets and unreliable Pinnacle quotes from July 23, 2025. Every
comparison uses the same native preclosing snapshot class; closing quotes do
not become predictors or substitute prices in this study.

Exact quote timestamps and historical statistic publication/revision times are
not verified. A statistic from an earlier match date is not thereby proven to
have been available before an archived preclosing price. Market-residual inputs
represent archived-price conditioning, not a reconstructed executable decision
time. Mathematical price-arbitrage flags and retrospective value returns do not
establish synchronized, available, funded or executable opportunities.

## Required artifacts and acceptance checks

Save feature groups/counts, FPL reconciliation decisions and unresolved cases,
coverage by season, common population counts, chronological roles, every C
trial, chosen C/temperature, per-fold model bundles, all predictions, predictive
scores, all paired comparisons, skipped-evaluation reasons, fixed-policy betting
ledgers/summaries, protocol/source hashes and first-study preservation checks.
Tables and narrative must say `exploratory_retrospective_not_a_fresh_holdout`.

Before accepting outputs, verify unique fixture/model/fold keys, valid normalized
probabilities, strict chronological blocks, strictly prior feature dates,
identical compared populations, identical shared controls, fixed group counts
21/25/28/32, no target/source forecasts in predictors, calibration after final
base-model refit, full-timeline fitting for both scoring populations, nonnegative
bankroll/commitment limits where betting is shown, and unchanged first-study
and acquisition artifacts.
