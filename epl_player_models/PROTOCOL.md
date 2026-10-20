# Player-driven match models — locked design

Protocol date: October 20, 2026. This redesign is exploratory: all 2022/23–2025/26
outcomes were already examined. Chronological fitting prevents future outcomes
entering an individual fit; it does not create an untouched historical test.
The existing models, strategies, forecasts and study exports remain frozen.

## Prediction question and population

Predict home win, draw or away win from strictly earlier player performances.
Compare player-only models with matched team controls and team-plus-player
models within the same algorithm family. Fit eight variants: four fixed
feature groups, each with regularized multinomial logistic regression and
histogram gradient boosting. No target lineup or target player minutes are
predictors. These are match-outcome models built from player records, not FPL
points forecasts or verified lineup/availability models.

Use the same 1,470 quoted evaluation fixtures as the earlier rolling study:
368 in 2022/23, 360 in 2023/24, 368 in 2024/25 and 374 in 2025/26. Focal fixtures
still involve at least one of the 20 saved current 2026/27 clubs. Historical
opponents remain context; they are not added to the current-club list. Raw
whole-league FPL histories improve opponent coverage beyond the earlier
processed, current-cohort-only player table. Keep primary populations identical
for every variant, using training-fitted missing-value handling rather than
dropping unavailable player histories.

## Historical player identity and timing

Read archived whole-league `merged_gw.csv` data, season team/fixture evidence,
full native E0 calendars and a separate current live snapshot. Resolve actual
fixture club from season-local fixture/club IDs, home/away side and exact
calendar identity. Early archive ID/name gaps may be resolved only through
unique consistent fixture-calendar/venue evidence. A player's season-final
`players_raw.team`, present roster, name similarity or match result cannot
assign the club for a historical performance. Quarantine ambiguous/conflicting
identities and retain reasons. Exclude assistant-manager rows.

Player identifiers are `(season, element)`. Do not connect season-reused IDs
or silently infer transfers by matching names. All target features use only
records on strictly earlier UTC calendar dates, with same-date records withheld.
Current-season history updates future features but never fitting/calibration.
Raw present prices, ownership, transfers, current injuries, current team mapping,
season-final totals and target participants/minutes/starts are excluded.

Native historical position fields are preferred. When unavailable, a
season-fixed archived `element_type` is a disclosed position proxy; its original
publication clock is unverified. Only a previously observed player's prior row
may supply a role. The early position-dependent reconstruction therefore is
retrospective and is not claimed as a fully timestamped historical lineup feed.
The player-form group does not need position labels.

## Fixed feature groups

The common player coverage block contains six home/away controls describing
earlier observed history. All eight variants receive exactly those controls.
The team block contains the existing nine team-performance columns and four
team context flags (`TEAM_PERFORMANCE + TEAM_FLAGS`); it omits the old xG-source
coverage flags. Thus the newly fitted team control is a matched-coverage
control, distinct from the separately retained old team model.

Player form uses rolling five- and ten-observed-fixture summaries of 12 basic
longitudinally available FPL measures: goals, assists, fantasy points, BPS,
bonus, influence, creativity, threat, saves, goals conceded, yellow cards and
red cards. Add active-player count, 60-minute-player count and total minutes.
Keep home, away and home-minus-away representations. These are 90 performance
columns plus the six shared coverage controls. No newer xG/defensive-contribution
fields enter the primary block because their earlier coverage differs.

The expanded player block adds role profiles, a fixed 1-GK/4-DEF/4-MID/2-FWD
projected XI and depth/continuity summaries. Candidates must have a positive-minute
appearance for the club in its previous five observed fixtures. Rank by prior
minutes with deterministic player-ID tie breaks. A later prior positive-minute
appearance for another club removes a candidate from its old club. No target
player list, target role, target start or future performance determines a slot.
Missing roles/players stay unavailable with explicit coverage; do not fetch an
older/future player merely to complete a formation. This is a past-minute
strength proxy, not a confirmed starting XI or proof of availability.

| Group | Inputs | Planned columns |
| --- | --- | --- |
| `team_control` | Team 13 + shared player coverage 6 | 19 |
| `player_form` | Player form + shared coverage | 96 |
| `player_squad` | Player form + role/XI/depth + shared coverage | 222 |
| `team_player_squad` | Team 13 + full player block | 235 |

The exported feature catalog provides every exact column and formula. Feature
engineering uses no outcome-driven screening, rankings or forward selection.
Coverage and projected-player audit rows retain source identities and latest
contributing dates. A common both-clubs-observed sensitivity is descriptive;
it cannot change which models enter the primary comparison.

## Locked chronological fitting and search

Use the unchanged four outer-season roles:

| Evaluation | Initial training | Hyperparameter tune | Temperature calibration |
| --- | --- | --- | --- |
| 2022/23 | 2016/17–2019/20 | 2020/21 | 2021/22 |
| 2023/24 | 2016/17–2020/21 | 2021/22 | 2022/23 |
| 2024/25 | 2016/17–2021/22 | 2022/23 | 2023/24 |
| 2025/26 | 2016/17–2022/23 | 2023/24 | 2024/25 |

For each group/family, choose one of three candidates by lowest tuning log
loss, with deterministic grid-order tie breaks. Refit preprocessing and the
selected model on initial training plus tuning; fit one scalar temperature
only on the separate calibration season, using the existing fixed log-T bounds
[-3,3]. Freeze those parameters for evaluation. All blocks must have the three
outcomes and strictly ordered dates. Median imputation, missingness indicators
and scaling are fitted only inside their fitting block; all-missing fitting
fields cannot learn a median from later data.

- Logistic: L2 multinomial, C in {0.03, 0.3, 3.0}, `lbfgs`, maximum 2,000
  iterations, fixed random state 42; median imputation with indicators and
  retained empty columns, followed by standardization.
- Histogram boosting: maximum leaves in {3, 7, 15}, 150 iterations, learning
  rate .05, minimum 40 samples per leaf, L2 10, fixed state 42. Disable early
  stopping explicitly, avoiding an internal random validation split. Use
  fitting-only missingness handling; there is no outcome-selected feature set.

The primary APIs are documented in the pinned-version official
[logistic regression documentation](https://scikit-learn.org/1.5/modules/generated/sklearn.linear_model.LogisticRegression.html)
and [histogram boosting documentation](https://scikit-learn.org/1.5/modules/generated/sklearn.ensemble.HistGradientBoostingClassifier.html).
The build records installed versions and exact fitted bundles, chosen settings,
calibration temperatures, fitting roles, protocol hash and source hashes.

## Evaluation and interpretation

Primary proper score is multiclass log loss; also report unscaled multiclass
Brier, accuracy and classwise ECE. Retain every declared variant, every outer
season and pooled scores. Compare each player group with the newly fitted team
control of the same algorithm, and every new variant with the raw de-vigged
Bet365 benchmark. Retain old team/player logistic and raw/temperature-market/
class-frequency predictions on the same native fixture identities.

Paired confidence intervals resample whole match dates within each outer
season, keeping shared fixtures paired. They are descriptive, unadjusted for
multiple comparisons and do not establish a prospectively validated winner.
New historical results cannot alter the already released old forecasts or
promote a new real-money betting policy. No score/return-based model omission
or threshold optimization is allowed.

## Trading diagnostics and complete money graphs

Declare exactly 32 new strategies P001–P032: the eight calibrated new model
series crossed with archived best/reference prices and fixed/Kelly staking.
Choose the H/D/A outcome maximizing p×odds−1, using deterministic H/D/A ties;
trade only if that value is strictly above 5%. Fixed stake requests are 1,000;
quarter-Kelly requests use date-start cash times min(2%, .25×edge/(odds−1)).
Allocate all same-date requests jointly and uniformly scale to available cash
before settlement. No deposits, borrowing, interest or fee assumption is added.
Best and reference are separate policy replays, including price-dependent
selection and resizing, rather than a pure payout decomposition.

Each strategy has one uninterrupted 100,000-unit four-season account, one
100,000-unit 2025/26 account for comparison with the original 84, and four
separately initialized annual accounts for stability diagnostics. Report hit
ratio, model expected gain/loss, actual winning/losing means, frequency,
turnover, profit, ROI, capital return, drawdown and applicable uncertainty.
Undefined no-trade conditional ratios remain unavailable. Expected components
are model claims at saved stakes, not realized averages or proof of calibration.

One 2025/26 chart overlays the original 84 plus all 32 new accounts (116 curves).
A separate four-season chart overlays the original 56 compatible plus all 32
new accounts (88 curves). Every curve starts at 100,000 and is initially visible
in the offline interactive charts. Do not fabricate earlier data for the 28
first-study configurations without comparable rolling predictions. The final
appendix retains exact S001–S084 definitions and adds all P001–P032 definitions.
Archive quote clocks/availability remain unverified; no graph demonstrates
executable fills or accounts for unobserved limits/fees.

## Separate future player-model release

Fit eight new future bundles using 2016/17–2023/24 initial training, 2024/25
tuning and refit, and 2025/26 calibration. No 2026/27 fitting/tuning/calibration
outcome enters any bundle. The separate October 20 current-history snapshot
supplies only lagged inputs for the ten October 23–25 targets. Existing saved
team-control values for those future fixtures may be reused with their original
pre-kickoff provenance. Recheck actual creation/append times before kickoff.

Release all eight variants in a new, separate hash-chained forecast ledger,
recording model/protocol/code hashes, feature values and latest prior dates.
The original 80-record ledger and ten recorded outcomes remain unchanged.
Under the reused schema, `forecast_type=team_only` means a non-market-input
forecast; `feature_group` and model identity distinguish player-only and
team-plus-player variants. Missing pre-match quotes mean no prospective stakes,
betting return or money curve. All new forecasts remain pending until a later
validated result observation; do not score them with already examined games.

## Preservation and reproduction

Commit this protocol before full fitting and hash it before/after the build.
All new outputs use a new immutable run directory. Retain raw/input identities,
feature/date audits, training trials, fitted bundles, calibration, predictions,
bet/date ledgers and complete report/workbook outputs. Independently reconcile
probabilities, date bounds, cashflows and graph endpoints. Preserve the user-edited
data overview workbook. Publish stable latest-report copies only after the new
run's final hash manifest is complete.
