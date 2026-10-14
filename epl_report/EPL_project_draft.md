# English Premier League: probability calibration, player features and archived betting prices

DRAFT FOR REVIEW — EPL section only | October 14, 2026 | Statistical Arbitrage, Fall 2026

### Abstract

This section studies whether probability-calibration selection improves football forecasts and archived-price betting outcomes, and whether historical player contributions add information beyond team statistics and bookmaker probabilities. The locked first experiment evaluates 374 fixtures in 2025/26; a later exploratory ablation compares fixed source groups over 1,470 matches. Calibration selection lowers estimated calibration error relative to accuracy selection, but the primary betting policy holds cash. The market benchmark has the strongest pooled proper probability scores. The evidence supports a reproducible forecasting study, not an established tradable betting edge.

### 1. Research question and reference

The September 30 proposal motivates two opportunities: value betting when estimated outcome probabilities exceed price-implied probabilities, and mathematical arbitrage when the best prices across outcomes appear inconsistent. For the EPL contribution, the outcome is home win, draw or away win. We ask whether selecting models by classwise expected calibration error (ECE), rather than accuracy, changes probability quality and hypothetical betting returns, then separately examine xG and player features. These are empirical questions; good probability calibration does not itself determine an advantageous price.

Walsh and Joshi [1] motivate opponent-relative season statistics, feature screening and calibration-oriented model selection. Their 2025 corrigendum [2] reports feature-engineering errors and replaces the original profitability results: corrected average ROI is −9.77% for calibration selection versus −26.78% for accuracy selection. It also states that Kelly staking can fail with a calibrated model. We use the corrected reference and make no profitability guarantee.

### 2. Population and scope

The population is historical EPL fixtures involving at least one of the 20 clubs eligible in 2026/27, as verified in the saved membership list [8]. The cohort comprises Arsenal; Aston Villa; Bournemouth; Brentford; Brighton & Hove Albion; Chelsea; Coventry City; Crystal Palace; Everton; Fulham; Hull City; Ipswich Town; Leeds United; Liverpool; Manchester City; Manchester United; Newcastle United; Nottingham Forest; Tottenham Hotspur; Sunderland. West Ham, Burnley and Wolverhampton Wanderers remain legitimate historical opponents but are excluded as focal clubs. Selecting today's clubs retrospectively creates survivor/selection bias: the population is not the complete historical league. All results in this section are EPL results; no NBA experiment is supplied.

The 374-fixture test omits six games between excluded clubs, rather than losing otherwise eligible observations.

## Data, identity and temporal controls

### 3. Sources and source histories

The saved acquisition snapshot is October 6, 2026; both retrospective experiments were run on October 13.

Football-Data E0 files [4] provide fixture outcomes, goals, shots, corners, fouls, cards and bookmaker triplets. The modeling frame contains 10,860 existing cohort matches; 12,754 saved whole-league matches reconstruct both clubs' basic histories, including excluded-opponent games. Understat [6] supplies displayed team xG through exact integrated fixture links. Official FPL [5] and a version-pinned public archive [7] supply actual-club player-fixture contributions. ESPN profiles, injury/valuation snapshots and other acquired descriptive sources support data exploration but do not enter historical predictors.

The original early FPL table lacked opponent names on 17,465 player rows (6,229 in 2016-17, 5,845 in 2017-18, 5,391 in 2018-19). A separate read-only reconciliation required one exact season/date/actual-club/venue E0 candidate, with known names, season-local IDs and same-fixture peers agreeing. It repaired all those names without conflicting accepted fixtures and increased usable FPL coverage from 2,872 to 3,460 fixtures, adding 588. Official current-season history supersedes overlapping archive rows; 258 assistant-manager records are excluded. Original acquisition and first-study artifacts are preserved.

### 4. Features and time discipline

Team inputs are season-to-date own-minus-opponent box-score averages, prior-season EPL win percentage, and five-/ten-match form. Promoted clubs have explicit missing-history flags. Source-specific xG and FPL aggregates are lagged from earlier completed fixtures; same-calendar-date outcomes cannot update each other. Missing source observations remain missing with observed-count controls. Neither the target score/xG nor its realised lineup/minutes enters its own prediction. Current roster, injury, ownership and price snapshots are excluded. Lagged FPL contributions measure past performance, not future player availability.

Chronological separation also governs fitted preprocessing, feature selection, regularization and calibration. Match-date ordering still does not prove that retrospective statistics were published before an archived quote: provider corrections and original publication clocks are unverified. Figure 1 describes source support rather than available starting lineups.

Median imputation with missingness indicators and standardization use fitted training values. Screening thresholds are 40% missingness, BH-adjusted KS q<0.01 with distance>0.15, and absolute Spearman correlation≥0.9. Internal search scores are optimization diagnostics, not unbiased nested estimates. Base estimators/preprocessing are refitted through 2021/22 and frozen before calibration. One positive temperature minimizes calibration-season log loss without changing the underlying features.

![Figure 1. Reused ablation source-support figure. The shared complete-history sensitivity has 767 matches: both clubs have at least eight observed xG and FPL slots among their last ten earlier E0 games, with fixed performance inputs observed. This is coverage, not roster availability.](../epl_modeling/ablation_results/ablation_history_coverage.png)

Figure 1. Reused ablation source-support figure. The shared complete-history sensitivity has 767 matches: both clubs have at least eight observed xG and FPL slots among their last ten earlier E0 games, with fixed performance inputs observed. This is coverage, not roster availability.

## Locked first-stage probability comparison

### 5. Chronology, model selection and metrics

Training spans 2014/15–2020/21; 2021/22 tunes hyperparameters, 2022/23 fits held-out temperatures [3], 2023/24 selects model families, and 2024/25 selects betting thresholds. The 2025/26 test follows all locked decisions. Each branch considers logistic regression, random forest, SVM and MLP with 12 seeded TPE trials per family. Training-only missingness, KS drift and Spearman redundancy screening precede an 18-candidate forward search. The resulting accuracy branch uses an SVM with two corners/shot predictors; the ECE branch uses an MLP with one corners predictor. No player/xG predictor survives this limited search, so it cannot establish incremental player benefit.

Both branches receive scalar temperature calibration on the same separate season; this compares selection procedures, not calibrated versus deliberately uncalibrated models. Probabilities are ordered H/D/A and sum to one. Accuracy is the argmax hit rate. Ten-bin classwise ECE averages weighted absolute probability/frequency gaps across all three one-vs-rest classes. Log loss is the mean negative log probability of the realised class; multiclass Brier is the mean sum of three squared probability errors, ranging from zero to two. Lower losses/ECE are better. The reference market probabilities normalize inverse Bet365 prices; training class frequencies provide a resolution-poor baseline.

Table 1. Locked 2025/26 test scores on the same 374 complete-reference-price fixtures. ECE is on [0,1]; Brier is the unscaled multiclass sum.

| Predictor | Accuracy (%) | CW-ECE | Log loss | Brier |
| --- | --- | --- | --- | --- |
| Accuracy-selected SVM | 48.13 | 0.0620 | 1.0763 | 0.6446 |
| ECE-selected MLP | 44.39 | 0.0416 | 1.0564 | 0.6356 |
| Normalized Bet365 | 48.66 | 0.0436 | 1.0191 | 0.6120 |
| Training frequency | 42.51 | 0.0290 | 1.0851 | 0.6566 |

The calibration-minus-accuracy ECE difference is -0.0204, with conditional 95% interval [-0.0437, 0.0068]. Its log-loss difference is -0.0199, interval [-0.0451, 0.0058]. Both include zero. The accuracy difference is -3.74 percentage points, interval [-7.09, -0.27] points. The 1,000 date draws condition on fitted choices and omit selection uncertainty.

![Figure 2. Reused locked-test reliability curves; the diagonal denotes equality between forecast probability and empirical outcome frequency. Only plotted bins with at least five matches are shown; scores use all matches. Sparse-bin deviations are uncertain.](../epl_modeling/results/test_reliability.png)

Figure 2. Reused locked-test reliability curves; the diagonal denotes equality between forecast probability and empirical outcome frequency. Only plotted bins with at least five matches are shown; scores use all matches. Sparse-bin deviations are uncertain.

## Archived-price replay and the first betting result

### 6. Prices, staking and arbitrage mathematics

For decimal price O and forecast p, estimated return per unit stake is pO−1. The secondary threshold is 5% estimated return, not a five-percentage-point probability gap. Each fixture contributes at most one chosen outcome. Reference-book prices are compared with the best complete individual-book triplets. Aggregate maxima/averages, exchanges and unreliable Pinnacle records from July 23, 2025 are excluded under source-quality rules [4]. Preclosing means an earlier archived snapshot, not a verified opening or contemporaneous quote.

Fixed staking uses 10 units from 1,000 initial units. Quarter Kelly uses one-quarter of max(0,(pO−1)/(O−1)), capped at 2% of date-start capital per bet. Same-date commitments are scaled before settlement; that day's winnings cannot finance another commitment. ROI is profit divided by total stakes, not profit divided by initial bankroll. Price shopping can alter both the chosen outcome and qualifying bets, so its contrast measures a policy difference rather than an isolated causal price effect.

### 7. Primary decision and predeclared secondary replay

The primary policy chooses its threshold using only 2024/25: at least thirty validation bets and positive fixed-stake ROI are required. Neither branch qualifies. Both therefore hold cash on the locked test, with zero turnover and undefined ROI. The separately predeclared 5% policy is reported transparently as a secondary comparison; it does not replace the failed primary policy.

Table 2. Secondary 5% archived-price replay on 374 fixtures. Profit is in bankroll units; ROI intervals use 1,000 whole-date bootstrap draws conditional on recorded bets and stakes.

| Branch | Prices | Stake | Bets | Profit (units) | ROI | Conditional 95% ROI CI |
| --- | --- | --- | --- | --- | --- | --- |
| Accuracy | Best book | Fixed | 371 | -83.3 | −2.25% | [−18.83%, 15.45%] |
| Accuracy | Best book | ¼ Kelly | 371 | -377.0 | −7.01% | [−23.18%, 11.92%] |
| Accuracy | Bet365 | Fixed | 365 | -186.7 | −5.12% | [−20.25%, 11.15%] |
| Accuracy | Bet365 | ¼ Kelly | 365 | -433.1 | −8.57% | [−23.64%, 8.79%] |
| Calibration | Best book | Fixed | 333 | 13.7 | 0.41% | [−20.08%, 22.07%] |
| Calibration | Best book | ¼ Kelly | 333 | -153.9 | −2.59% | [−20.93%, 17.72%] |
| Calibration | Bet365 | Fixed | 314 | -23.5 | −0.75% | [−19.46%, 19.70%] |
| Calibration | Bet365 | ¼ Kelly | 314 | -170.6 | −3.09% | [−20.97%, 16.47%] |

The calibration model's best-book fixed-stake point ROI is 0.41%, versus −2.25% for accuracy selection; their intervals cross zero. The small positive point estimate is not reliable evidence of an edge. Kelly does not create information absent from the forecasts and increases sensitivity to probability errors.

A mathematical arbitrage screen checks 1/O_H+1/O_D+1/O_A<1 for best outcome prices, with equal-payout stakes proportional to inverse odds. This arithmetic requires compatible contracts and simultaneous accepted prices. The locked test has no such archived candidate. All test quotes lack verified compatible observation clocks; simultaneous availability, limits, fees and accepted execution cannot be established. No arbitrage profit is credited. A feature before kickoff may still postdate an earlier Friday/Tuesday quote, so this is a hypothetical archived-price replay.

## Exploratory fixed-group source ablation

### 8. Repaired-source study and conditional contrasts

The second study evaluates four source groups—Team (21 inputs), Team+xG (25), Team+players (28) and Combined (32)—with logistic and market-residual models. Across four outer seasons, 2022/23–2025/26, this yields 32 fitted group models and 1,470 common quoted-price matches. Each fold trains/tunes before a separate calibration season, then evaluates the next season; regularization uses the fixed three-value grid. All groups share source-coverage controls. Market-residual scores add learned corrections to log normalized bookmaker probabilities; raw and temperature-only markets separate feature information from recalibration.

This is exploratory retrospective work: 2025/26 was already inspected in stage one, and correct rolling fitting order cannot make it a fresh confirmatory holdout. Within logistic models, adding xG changes pooled log loss by -0.0035, interval [-0.0066, -0.0003]. Player-minus-team changes are 0.0000 for logistic, interval [-0.0039, 0.0036], and -0.0009 for residual models, interval [-0.0044, 0.0027]. Both player intervals include zero. These conditional, unadjusted comparisons do not establish incremental player benefit.

![Figure 3. Reused seasonal paired log-loss contrasts against the same model type's Team group. Negative values favor the added inputs. Conditional 95% intervals use 1,000 whole-date draws within season; pooled draws stratify by season. They omit tuning/fitting uncertainty and have no multiple-comparison adjustment.](../epl_modeling/ablation_results/ablation_paired_logloss.png)

Figure 3. Reused seasonal paired log-loss contrasts against the same model type's Team group. Negative values favor the added inputs. Conditional 95% intervals use 1,000 whole-date draws within season; pooled draws stratify by season. They omit tuning/fitting uncertainty and have no multiple-comparison adjustment.

## Four-season probability and return summaries

Table 3. Pooled scores on 1,470 identical fixtures. LR denotes logistic regression. Pooled ECE is recomputed from predictions, not averaged across seasonal ECE values.

| Variant | Accuracy (%) | CW-ECE | Log loss | Brier |
| --- | --- | --- | --- | --- |
| Raw market | 54.42 | 0.0177 | 0.9662 | 0.5743 |
| Temperature market | 54.42 | 0.0197 | 0.9671 | 0.5750 |
| LR: Team | 52.93 | 0.0217 | 0.9876 | 0.5889 |
| LR: Team + xG | 53.33 | 0.0255 | 0.9841 | 0.5866 |
| LR: Team + players | 52.52 | 0.0275 | 0.9876 | 0.5885 |
| LR: Combined | 53.13 | 0.0301 | 0.9845 | 0.5865 |
| Residual: Team | 54.08 | 0.0226 | 0.9701 | 0.5758 |
| Residual: Team + xG | 54.22 | 0.0309 | 0.9701 | 0.5758 |
| Residual: Team + players | 54.15 | 0.0216 | 0.9693 | 0.5751 |
| Residual: Combined | 54.22 | 0.0203 | 0.9697 | 0.5752 |
| Frequency | 44.29 | 0.0153 | 1.0700 | 0.6471 |

![Figure 4. Reused fixed-5% ablation replay. Profit/turnover combines separate season bankroll resets; it is not a continuous track record. Fixed-stake point ROI ranges −31.59% to 7.01%. This run estimated no betting ROI intervals; blank bounds do not imply certainty or a reliable edge.](../epl_modeling/ablation_results/ablation_betting_roi.png)

Figure 4. Reused fixed-5% ablation replay. Profit/turnover combines separate season bankroll resets; it is not a continuous track record. Fixed-stake point ROI ranges −31.59% to 7.01%. This run estimated no betting ROI intervals; blank bounds do not imply certainty or a reliable edge.

## Discussion, limits and prospective evaluation plan

### 9. Evidence and limitations

The raw market has the lowest observed pooled proper scores: log loss 0.9662 and Brier 0.5743. The lowest-loss residual variant has point log loss 0.0022 higher than temperature-only market. The 767-match complete-history sensitivity changes descriptive rankings, illustrating population dependence rather than validating a chosen production model.

The first study observes an accuracy/calibration trade-off between selected procedures, while its admissibility rule rejects active primary betting. The later study finds modest, model-dependent source-feature changes and stronger overall proper scores for bookmaker probabilities. Neither establishes a dependable incremental player advantage or profitable deployable system. ECE alone is insufficient: class frequencies can attain low error while lacking useful discrimination. Differences also combine feature and model-family choices, so they cannot isolate a causal effect of calibration itself.

The fixed present-day cohort restricts generalization. Historical opponents have incomplete xG/FPL histories outside saved cohort-linked fixtures; changes in source definitions and fantasy scoring can produce drift. Displayed team xG is distinct from additive shot/player xG. Retrospective publication/revision clocks, synchronized prices, fill acceptance, costs and limits are unavailable. Date bootstrap intervals do not cover all dependence or model-selection uncertainty. Exploring many variants after inspecting outcomes adds multiplicity and prevents a new confirmatory interpretation.

### 10. Prospective protocol and pending release

The saved prospective protocol defines an append-only forecast ledger after its committed cutoff. It requires pre-kickoff H/D/A probabilities, code/configuration hashes, latest contributing source dates and actual source-availability/quote clocks; missing forecasts and rejected fills must also be retained. All eight declared alternatives and market benchmarks remain fixed, with 2025/26 reassigned to calibration rather than reused as a new test. Primary evaluation would use log loss on common valid forecasts, with Brier, ECE, accuracy and separately identified paper-trading summaries.

Operational update, October 14: the committed ledger contains 40 forecasts from 4 logistic alternatives for 10 fixtures on October 17–19, 2026. Market-dependent alternatives are withheld: 60 forecast slots lack suitable EPL quotes. Outcomes remain pending, so no prospective performance is reported. The next step is fresh quote capture and settlement of these future matches, retaining missingness and evaluating without outcome-driven protocol changes.

### References and reproducibility

[1] Walsh, C. & Joshi, A. (2024). Machine learning for sports betting: Should model selection be based on accuracy or calibration? Machine Learning with Applications, 16, 100539. [https://doi.org/10.1016/j.mlwa.2024.100539](https://doi.org/10.1016/j.mlwa.2024.100539)

[2] Walsh, C. & Joshi, A. (2025). Corrigendum to the 2024 sports-betting article. Machine Learning with Applications, 19, 100627. [https://doi.org/10.1016/j.mlwa.2025.100627](https://doi.org/10.1016/j.mlwa.2025.100627)

[3] Guo, C., Pleiss, G., Sun, Y. & Weinberger, K. Q. (2017). On Calibration of Modern Neural Networks. PMLR, 70, 1321–1330. [https://proceedings.mlr.press/v70/guo17a.html](https://proceedings.mlr.press/v70/guo17a.html)

[4] Football-Data. Historical results/odds definitions and timing/reliability notes. [https://www.football-data.co.uk/data.php](https://www.football-data.co.uk/data.php)

[5] Premier League. Official Fantasy Premier League data service. [https://fantasy.premierleague.com/api/bootstrap-static/](https://fantasy.premierleague.com/api/bootstrap-static/)

[6] Understat. EPL expected-goals data. [https://understat.com/league/EPL/2026](https://understat.com/league/EPL/2026)

[7] Anand, V. Fantasy Premier League public historical archive; snapshot revision recorded in source manifests. [https://github.com/vaastav/Fantasy-Premier-League](https://github.com/vaastav/Fantasy-Premier-League)

[8] Premier League. Official 2026/27 membership reference recorded in current_teams.csv. [https://www.premierleague.com/en/news/4673099/the-202627-premier-league-season-officially-starts](https://www.premierleague.com/en/news/4673099/the-202627-premier-league-season-officially-starts)

Reproduce the draft with epl_report/build_report.py. Source tables, protocols, figures and hashes are listed in report_manifest.json; no report step retrains models. The proposal and immutable first/ablation outputs remain separate from this editable draft.
