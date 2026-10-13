# Feature coverage and limits of the first experiment

The October 13, 2026 experiment uses the saved October 6 snapshot. The feature
builder exports 10,860 existing Football-Data Premier League cohort fixtures and
405 numeric `feat_*` predictors. Saved full-league E0 files contain 12,754
matches involving 51 clubs; those files reconstruct complete historical
opponent box scores, including games between clubs outside the export cohort.
The historical export still requires at least one of the 20 current 2026/27
clubs. Current actual-match coverage ends September 20, 2026.

The output retains unmatched source observations as missing features. It does
not replace unavailable player or xG observations with zero performance. The
fixture identifiers, `result`, and `audit_*` columns are outside the predictor
set. All contributing historical match dates are strictly earlier than the
target calendar date, including when a club has multiple source fixtures on
one day. Historical publication times and later statistical revisions remain
unverified.

## FPL coverage gap

The curated historical FPL player-fixture table contains **17,465 rows with a
missing `opponent_name`**, after omitting the overlapping current-season archive
in favor of official current histories. This is an internal source identity
gap in three early seasons:

| Season | Player-fixture rows missing `opponent_name` |
| --- | ---: |
| 2016-17 | 6,229 |
| 2017-18 | 5,845 |
| 2018-19 | 5,391 |
| **Total** | **17,465** |

These rows have a kickoff time, an actual fixture club, a numeric opponent team
ID and a home/away indicator. The missing opponent name prevents the current
feature builder from verifying the full exact season/date/home/away identity.
They are excluded from FPL fixture aggregates; their Football-Data target
matches remain in the modeling frame. No missing date was inferred, and no
opponent was guessed. The inspected curated FPL rows have no missing
`kickoff_time`, `canonical_team` or `was_home` values. This particular missing
opponent-name gap does not occur in the 2019/20 onward/current histories.

The resulting FPL feature history covers 2,872 exactly linked fixtures. A
further 258 assistant-manager records are excluded because they are not player
contributions. Official 2026/27 player histories supersede the overlapping
archive season, preventing duplicate GW1 observations. Player fixture
statistics are summed by actual fixture club before lagging; current roster
membership, price, ownership, transfers, injury status and source forecasts
are excluded. Available fields and FPL scoring rules vary by season, and some
recent metrics have no observations in the training seasons.

## Understat coverage

The builder attaches displayed team xG through the saved integrated exact
fixture links. It obtains 4,089 matched completed games. Nineteen additional
completed Understat cohort games have different printed calendar dates from
the other saved source fixture and remain unlinked. They are explicitly
flagged as different-source-date records in the integrated table. The builder
does not silently shift their dates or use nearby-date matching.

Historical opponents outside the cohort can have incomplete Understat/FPL
histories because those saved curated sources focus on cohort fixtures.
Per-source observed-match counts and missing-history indicators expose this
coverage. Rolling means use the last five or ten strictly earlier completed
E0 fixture slots; missing source observations within those slots are skipped.
Season-to-date means use only earlier matches in the same season. Rolling
histories can cross season boundaries and long gaps between EPL appearances;
the separate days-since-prior-EPL-match feature records those gaps.

Displayed team xG is kept separate from additive shot/player xG. Their known
aggregation differences are documented in the acquisition package. Completed
match `forecast__w/d/l` fields and season-final contextual totals are excluded
from these predictors.

## What the selected models establish

The first run considers a ranked pool of at most 18 candidate features in its
budgeted forward search. Its final selected predictors, recorded in
[`results/selected_features.json`](results/selected_features.json), are:

| Selection branch | Selected lagged predictor |
| --- | --- |
| Accuracy | `feat_diff_std_corners_diff` |
| Accuracy | `feat_diff_roll10_shots_on_target_diff` |
| Calibration | `feat_diff_std_corners_against` |

Each `feat_diff_*` value subtracts the away club's historical average from the
home club's corresponding historical average. A club-level `corners_diff` or
`shots_on_target_diff` is its own count minus its opponent's count in an earlier
fixture. `std` denotes season to date; `roll10` denotes the last ten earlier
E0 matches. The accuracy branch therefore retains two team box-score
predictors, while the calibration branch retains one corners predictor.

**No FPL/player or Understat xG predictor survives into either final model.**
The first experiment does not establish an incremental benefit from player or
xG features. Their absence from this small selected set also does not show
that they have no predictive value: coverage filters, redundancy screening,
ranking and the limited search budget constrain which alternatives can be
examined. This run remains a comparison of the selected team-statistic models.

## Outstanding research for a separately specified experiment

Early FPL identities could be reconciled using saved season-local opponent
IDs and any available source team/fixture lookup, with exact season, printed
calendar date, focal club and home/away venue as consistency checks. A
candidate must resolve to exactly one saved E0 fixture, agree with available
independent source identifiers, preserve one fixture-club aggregate per key,
and retain unresolved or conflicting rows in an audit table. Checking
uniqueness is necessary; date proximity alone is insufficient. Any revised
reconciliation should rerun the same-date and future-outcome invariance tests.

A future player/xG study should specify comparable team-only, team-plus-xG,
team-plus-player and combined ablations before evaluation, with identical
chronological folds and declared search budgets. The existing 2025/26 test
results must not guide repairs, feature choices or retuning for this run.
Changes motivated by that test would require a fresh untouched evaluation
period or a newly specified nested historical study.

Five focused tests in [`tests/test_features.py`](tests/test_features.py)
currently verify same-date exclusion across all three feature sources, future
outcome/statistic mutation invariance, complete noncohort opponent history
without extra exported targets, distinct promoted/missing-archive flags, and
retention of a target whose Understat source date fails exact reconciliation.
The real snapshot build reports zero violations across all six latest-prior
date audit columns and preserves the existing cohort fixture IDs.
