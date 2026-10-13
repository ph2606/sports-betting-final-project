# EPL study protocol: accuracy versus probability calibration

Protocol date: October 13, 2026. Data snapshot: October 6, 2026. This is the initial English Premier League implementation of [the project proposal](../ML_Sports_Betting_Project_Proposal.pdf). The canonical proposal and its `(1)` copy have identical content. This document describes an experimental adaptation, with explicit data limits; it is not an exact replication or an executable historical trading backtest.

## Research question and corrected reference

We test whether selecting a three-outcome EPL probability model by classwise calibration produces different predictive quality and hypothetical betting returns from selecting by accuracy. Four candidate families—logistic regression, random forest, SVM and MLP—are evaluated in two parallel selection branches. Both branches subsequently receive the same held-out probability-calibration procedure; this compares selection objectives, rather than a calibrated model against an intentionally uncalibrated model.

Walsh and Joshi's original NBA study uses season-to-date opponent-relative statistics, prior-season performance, shift/redundancy screening, forward selection and TPE tuning. Its calibration metric is classwise ECE. It uses twenty bins and a bin-occupancy restriction. These details motivate our design, but football's draw class, data coverage and validation chronology require adaptations. [Original 2024 article](https://doi.org/10.1016/j.mlwa.2024.100539), [author manuscript](https://arxiv.org/pdf/2303.06021).

The **2025 corrigendum supersedes the original numerical results**. The authors report feature-engineering implementation errors discovered during modularisation and testing. Corrected average reported ROI is **−9.77% for calibration selection versus −26.78% for accuracy selection**; best reported ROI is **+23.13% versus +10.9%**. The chosen calibration model changes from SVM to MLP, while the accuracy model remains SVM. The correction also makes clear that Kelly staking can lose despite calibration. We therefore treat superior profitability as a hypothesis to evaluate, not an established guarantee. [Corrigendum and corrected supplementary-code link](https://researchportal.bath.ac.uk/en/publications/corrigendum-to-machine-learning-for-sports-betting-should-model-s/), [DOI](https://doi.org/10.1016/j.mlwa.2025.100627).

## Population and historical information

The target population is matches involving at least one of the twenty verified **2026-27** Premier League clubs. West Ham, Burnley and Wolves are not focal clubs. Their historical appearances as opponents remain legitimate match context. This fixed present-day cohort introduces survivor/selection bias and does not represent the entire historical league.

Whole-league raw E0 records are used to reconstruct **both sides' Football-Data histories**, including an opponent outside the focal cohort. This prevents artificial missing core opponent form and avoids restricting evaluation to fixtures where both clubs happen to belong to today's cohort. Understat and FPL histories remain incomplete outside the saved cohort-linked fixtures; observed-count features expose that coverage rather than implying complete opponent player/xG histories. Filtering the target fixtures still follows the user's current-club scope. The complete 2025-26 season contains **374 eligible cohort fixtures**, rather than all 380 league fixtures; six fixtures between the three excluded clubs are outside the population. Predictive coverage and valid-odds betting coverage are reported separately.

Only Premier League E0 results are target observations. Lower-division records cannot silently become comparable EPL measurements. If previous-season performance is unavailable for a promoted club, it remains missing with explicit coverage information. Team names and source-specific fixture IDs are reconciled before joining; joining two focal-team observations must not double-count one fixture.

Features include strictly lagged team form, season-to-date opponent-relative performance and prior-season performance, with source-specific xG and FPL aggregates where coverage supports them. The exact candidate and selected columns are saved in the feature/filter/selection artifacts. A fixture's own score, shots, xG, player minutes and fantasy points are outcomes, not predictors. Same-calendar-date results cannot update another match's input when exact ordering is not established. Coverage counts and missingness indicators accompany partial histories; missing observations are not converted to zero performance. Earlier completed fixtures may update a later test-season fixture's **features**, while all fitted model parameters remain frozen.

Historical FPL records start in 2016-17; defensive and expected-goal fields have shorter histories and changing definitions. Lagged **club aggregates of past player appearances** are useful form summaries. They do not establish which players were available, injured, selected or expected to start at an earlier decision time. Do not select historical player-form inputs using the target match's realised XI or weight them by target-match minutes. Current FPL injury/news/status, current rosters, season-final `players_raw` totals, archive `xP`, current valuations and present-day player-to-club links are excluded from past predictors. `history_past` does not identify former clubs. FPL fantasy scoring and assists are not interchangeable with other providers' definitions. See [FPL notes](../epl_data/metadata/fpl_notes.md) and the [source guide](../epl_data/SOURCE_GUIDE.md).

## Locked chronological stages

| Stage | Seasons | Permitted use |
|---|---|---|
| Initial training | 2014-15 through 2020-21 | Feature eligibility, KS/Spearman screening, branch-specific forward selection, base-estimator fitting |
| Hyperparameter tuning | 2021-22 | TPE objectives for each family and branch; no probability-calibrator fitting |
| Probability calibration | 2022-23 | Fit one scalar temperature per fixed candidate; no feature or hyperparameter changes |
| Branch model selection | 2023-24 | Select one family per branch using calibrated predictions and its prespecified objective |
| Strategy validation | 2024-25 | Choose the betting edge threshold; model, features and calibrator remain fixed |
| Final held-out test | 2025-26 | One evaluation of the frozen choices over the full eligible season |
| Partial monitoring | 2026-27 | Descriptive replay with the frozen model, clearly separate from the complete-season test |

After tuning, each chosen-parameter base estimator and its preprocessing are refitted on **2014-15 through 2021-22**. They are then frozen before the disjoint 2022-23 calibration step. There is no further base-model or preprocessing refit after calibration, because that would change the score distribution to which the temperature was fitted. The 2023-24 family selection and 2024-25 strategy validation do not become additional training data.

The final test cannot determine features, imputations, scaling, model family, hyperparameters, calibration method, bin counts, edge thresholds, staking rules or the search budget. Any later redesign requires a new evaluation protocol; it cannot reuse 2025-26 as an untouched test. Integrity checks such as fixture uniqueness, source identity and date ordering are distinct from selecting a model by test performance.

The monitoring snapshot contains fifty completed 2026-27 fixtures, with outcomes through September 20. It is not a full season or a live feed as of October 13. These already-observed matches provide retrospective monitoring, not a prospectively timestamped forecast record. New promoted clubs can have substantially less relevant training history; their monitoring probabilities do not establish validated promoted-club performance.

## Training-only screening and limited search

The implementation in [selection.py](selection.py) performs the following operations without consulting 2021-22 or later for screening/forward selection:

1. Reject features with more than 40% missing training observations or at most one distinct observed training value.
2. Compare the early and later halves of the training-season sequence using two-sample KS statistics on available values. A minimum of thirty values in each block is required. Apply Benjamini–Hochberg adjustment, then drop only when adjusted `q < 0.01` **and** KS distance exceeds `0.15`. These are pragmatic drift-screening rules: repeated clubs, temporal dependence, discrete features and multiple changing source definitions prevent interpreting them as a complete formal stability guarantee.
3. Rank candidates by their maximum absolute training Spearman association with the three one-versus-rest outcome indicators. Remove feature-to-feature redundancy at absolute Spearman correlation `>= 0.9`. This avoids imposing an arbitrary numeric ordering on home/draw/away labels. Rank and tie handling are deterministic.
4. Run a separate greedy logistic-regression forward-selection wrapper for each branch, using two expanding-season folds inside the training period. With the planned training window, 2019-20 and 2020-21 are the internal validation seasons. The default budget is eighteen screened candidates and at most eight selected features, with an improvement stopping rule. Imputation and scaling are fitted within each wrapper fit.

Global screening uses the complete outer training block, including seasons subsequently used in these internal forward-selection folds. Consequently, their scores are **optimization diagnostics**, not an unbiased nested-cross-validation performance estimate. The later disjoint stages supply the meaningful external comparisons.

TPE then fits on the initial training window and scores on 2021-22. The accuracy branch maximizes accuracy; the calibration branch minimizes ten-bin classwise ECE. Current defaults are twelve trials per family/branch, four startup trials, seed 42 with deterministic family offsets, and the recorded SFS limits above. A shorter explicitly logged run remains an initial limited-budget study. This is a small seeded search, not an exhaustive search or the original paper's extensive optimization. The run manifest records actual budgets, seeds, package versions, parameter choices and convergence warnings. Neither the number of trials nor candidate retention is adjusted after inspecting test performance.

| Family | Initial search space |
|---|---|
| Logistic regression | Regularization `C` from 0.001 to 30 on a log scale |
| Random forest | 200 trees; depth 3/5/8/unrestricted, minimum leaf size 5–40, feature fraction 0.5–1.0 |
| RBF SVM | `C` 0.03–30 and `gamma` 0.001–0.3 on log scales |
| MLP | One hidden layer with 8/16/32/64 units, L2 penalty 0.0001–1 and initial learning rate 0.0003–0.01 |

All fits use training-fitted median imputation with missingness indicators and standardization. SVM uses `probability=False`, three one-versus-rest decision scores and `break_ties=True`; MLP has `early_stopping=False` to avoid an internal random validation split. Source descriptions of SVM probability fitting explain why its default probability-calibration route is deliberately avoided here. [scikit-learn 1.5 SVC documentation](https://scikit-learn.org/1.5/modules/generated/sklearn.svm.SVC.html).

## Separate probability calibration

The installed environment uses scikit-learn 1.5, so the implementation supplies standalone scalar temperature scaling rather than relying on a newer calibration API. Obtain three aligned scores `s_H, s_D, s_A`. Models with native probabilities use their clipped log probabilities; SVM uses its decision scores. Before calibration, softmax supplies the common probability representation used during tuning.

For each fixed candidate, fit `T > 0` on **2022-23 alone**:

$$
p_{ik}(T)=\frac{\exp(s_{ik}/T)}{\sum_{j\in\{H,D,A\}}\exp(s_{ij}/T)},
\qquad
T^*=\arg\min_T\left[-\frac1N\sum_i\log p_{i,y_i}(T)\right].
$$

The current scalar optimization fixes `log(T)` to `[-3,3]`. The fitted temperature, base estimator and preprocessing are preserved together. Both branches use this same procedure. The 2023-24 branch winners maximize accuracy or minimize ten-bin classwise ECE respectively, with lower log loss and then family name as fixed tie breakers.

This score-to-probability conversion is an explicit experimental adaptation. SVM margins are not native joint probabilities, and one temperature cannot correct arbitrary class-specific biases. Positive scalar temperature also preserves the score argmax; it changes confidence rather than adding a new classifier. Calibration cannot by itself guarantee profitable bets. The disjoint-fitting requirement follows established calibration guidance. [Temperature-scaling research](https://proceedings.mlr.press/v70/guo17a.html), [scikit-learn 1.5 calibration documentation](https://scikit-learn.org/1.5/modules/generated/sklearn.calibration.CalibratedClassifierCV.html).

## Metrics, probability order and uncertainty

Every probability vector uses the explicit order **home, draw, away**. Estimator columns are reordered through `classes_`; alphabetical provider labels must never determine the meaning of a column. Check finite values, bounds and normalization. Hard classification is the argmax of the same probability vector used for evaluation and betting.

For `K=3`, `N` matches, fixed equal-width bins `B_mk={i:p_ik in I_m}`, and `z_ik=1[y_i=k]`, define:

$$
\operatorname{CW\!ECE}
=\frac{1}{3}\sum_{k\in\{H,D,A\}}\sum_{m=1}^{M}
\frac{|B_{mk}|}{N}
\left|
\frac{1}{|B_{mk}|}\sum_{i\in B_{mk}}z_{ik}
-\frac{1}{|B_{mk}|}\sum_{i\in B_{mk}}p_{ik}
\right|.
$$

All **three** probabilities from every match participate, each in its own class's bins. It is not ECE over only the winning/most-confident class. Use `M=10`, left-closed/right-open bins, and include `p=1` in the final bin. Empty bins contribute zero. Report the score on `[0,1]`, or explicitly multiply by 100 for percentage points. Prespecified five- and fifteen-bin results are sensitivity reports, not alternative test-driven selection criteria. Per-class reliability tables include support counts so sparse bins remain visible.

ECE depends on binning and finite-sample noise; a constant predictor can be calibrated while having little useful resolution. We therefore do **not** impose the original paper's eighty-percent nonempty-bin rule on a three-class football model, where draw probabilities may legitimately occupy a narrow range. We supplement ECE with frozen training-frequency and margin-normalized reference-bookmaker baselines, and the following proper probability losses:

$$
\operatorname{LogLoss}=-\frac1N\sum_i\log p_{i,y_i},
\qquad
\operatorname{Brier}=\frac1N\sum_i\sum_{k=1}^{3}(p_{ik}-z_{ik})^2.
$$

Lower is better. Brier is the **unscaled multiclass sum**, ranging from zero to two, not the mean over the three class columns or the binary half-scaled convention. It is implemented directly for compatibility with scikit-learn 1.5. Proper losses assess overall probabilistic forecasting quality, including resolution, and are not pure calibration-error measures. Empirical class frequencies inside bins are estimates, not observable true probabilities for individual fixtures. [Brier definition](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.brier_score_loss.html), [log-loss definition](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.log_loss.html), [calibration and proper scoring rules](https://scikit-learn.org/stable/modules/calibration.html).

Report accuracy, ECE, log loss and Brier on all eligible fixtures, plus a clearly labeled common valid-odds subset for market comparisons. Paired model comparisons use the same matches. Confidence intervals resample whole match dates to preserve dependence within a day's fixtures. These are approximate conditional intervals: they do not incorporate model-search/calibrator/threshold-selection uncertainty or all dependence across dates. One held-out season cannot establish universal superiority.

## Archived-price replay and strategy selection

The main odds panel uses individual-bookmaker **preclosing** triplets; market aggregates are not treated as executable bookmakers. Closing fields are kept separate. A complete Bet365 triplet is required for the reference comparison so best-price and reference-price strategies share the same match panel. Known unreliable Pinnacle observations from July 23, 2025 onward are excluded under a fixed source-quality rule.

Football-Data documents two snapshot types from 2019-20, earlier preclosing collections, and collection typically on Friday afternoons for weekend fixtures or Tuesday afternoons for midweek fixtures. The first snapshot is collected **after** market opening and is not verified opening odds. Its warning covers stale Pinnacle preclosing and closing prices after July 23, 2025. [Provider archive definitions](https://football-data.co.uk/downloadm.php), [source notes](https://www.football-data.co.uk/notes.txt), [provider timing/reliability statement](https://www.football-data.co.uk/data.php).

Our files lack individual quote clocks, contemporaneous xG/FPL publication histories, bookmaker limits, rejection records and execution costs. Features preceding a fixture date are not thereby proven to precede the provider's earlier Friday/Tuesday quote. Retrospective provider/model revisions remain possible. **The main result is an archived-price hypothetical replay with chronological model-selection controls**, not a fully verified historical opportunity to place those bets. Any stronger execution claim requires timestamped prices and an as-of feature store.

For decimal odds `O` and predicted probability `p`, estimated return per unit staked is `p*O-1`. In 2024-25 only, choose an edge threshold from the fixed grid `0, .025, .05, .075, .10, .15, .20`. A candidate must produce **at least thirty validation bets and strictly positive validation ROI**. Select the highest eligible fixed-stake ROI, with the lower threshold breaking ties. If no candidate qualifies, lock the explicit no-bet sentinel threshold (`1e6`) and report no admissible primary validation strategy. Thresholds are locked before the final test. A separately prespecified **5% expected-return threshold** is also reported as a secondary policy, including when the primary validation-selected policy makes no bets; it is not a replacement selected after seeing test results.

Each strategy selects at most one outcome per fixture. Compare a fixed stake of **10 units** and **quarter Kelly capped at 2% of current capital per bet**, starting from **1,000 units** under the same fixed settings. Same-date stakes use date-start capital and are scaled to available bankroll before settlement; unsettled winnings cannot fund other bets that day.

Report profit, turnover, **ROI = profit/turnover**, final capital, log wealth growth, maximum date-close drawdown, bet count and conditional date-bootstrap intervals. Zero-turnover/no-bet ROI is undefined, not evidence of a zero-risk profit. Paper-reported ROI figures are not a numerical target for a differently defined EPL experiment.

For descriptive arbitrage screening, `1/O_H + 1/O_D + 1/O_A < 1` identifies a mathematical combination of archived best prices. Without synchronized observations and verified execution, it does not establish realizable arbitrage. No arbitrage gains are credited to the replay's realised-profit ledger. The project's proposal is thus implemented as a measured comparison of selection and price-shopping policies, with explicit limits on stronger betting or arbitrage claims.

## Reproducibility and completion criteria

Save the chronological split manifest, source/input hashes, feature eligibility audit, SFS paths, TPE trials, convergence warnings, refit/calibration seasons, temperatures, branch-family selection scores, strategy-validation choices, frozen models, fixture-level predictions, valid-odds exclusions, bet ledgers and uncertainty reports. The run records actual software versions and search budgets. Complete the integrity and deterministic synthetic checks before looking at final test metrics. Neither a favorable nor an unfavorable test outcome permits retuning within this study.
