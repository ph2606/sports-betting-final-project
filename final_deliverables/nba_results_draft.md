# NBA results: source-supported final-report draft

Sources: `ML Sports/Data.ipynb` (zero-based cell indices below), the supplied
`regular_season_totals_2010_2024.csv`, `OddsData.sqlite`, `best_params.json`,
`NBA_analysis_Presentation.pptx` and `Stat_Arb.pdf`. Primary saved notebook
results are distinguished from the new fixed-parameter reconstruction audit.

## Data and league-specific implementation

The NBA data contain 33,316 team-game logs, corresponding to 16,658 distinct
raw games across 14 seasons from 2010/11 through 2023/24. Each game is converted
to one home-team observation. The target is binary: whether the home team won.
For each of 25 box-score statistics, the notebook first computes a team's
outperformance relative to its opponent, then averages only strictly earlier
observations within that team and season. Home and away averages are subtracted.
The difference in prior-season win percentages adds a twenty-sixth candidate.
Both teams must have played more than ten earlier season games for a match to
be retained as a modeling row; these early games still contribute to later
averages. This leaves 14,471 games. The displayed 58.5% home-win rate belongs to
the original training sample, not necessarily this entire cleaned dataset.

The supplied SQLite moneyline tables are joined by calendar date and both
home and away team abbreviations. The five core seasons have 5,368 modeled
games with prices, and all 1,074 games in the final 2018/19 betting sample have
matched moneylines. Opening/closing status and publication clocks are not
established. The supplied presentation describes public odds archived through
Sportsbook Review, with FanDuel as the default provider; it does not establish
a synchronized multi-book execution feed. Sources: notebook cells 1, 3 and 18;
NBA presentation slides 2–3.

The initial training seasons are 2014/15 and 2015/16 (2,145 games); 2016/17
(1,074 games) supplies validation for features and hyperparameters; 2017/18
(1,075 games), called the test set in the notebook, selects the model family.
The later betting season is 2018/19 (1,074 games). The 2017/18 results must
therefore be described as model-selection evidence rather than an untouched
final test. Standardization is fitted on the permitted prior block at each
stage: training only initially, training plus validation before the family
comparison, and all four pre-betting seasons before 2018/19.

The Kolmogorov–Smirnov filter drops offensive rebounds at the 1% level, leaving
25 inputs. A training-sample Spearman filter at absolute correlation 0.7 retains
nine. Sequential forward selection using logistic regression chooses two
features for the calibration branch, offensive rating and three-pointers made;
the accuracy branch additionally retains previous-season win percentage and
turnovers. Optuna TPE searches 30 settings for each of logistic regression,
random forest, neural network and SVM in each branch. Selection scores average
probabilities from ten seed-specific refits.

## Core selection and later betting season

| Family | Calibration branch B: selection ECE | Accuracy branch C: selection accuracy |
|---|---:|---:|
| Logistic regression | 4.31% | 65.30% |
| Random forest | 5.68% | 65.40% |
| Neural network | 4.65% | 65.49% |
| SVM | 4.40% | 66.33% |

These columns refer to different feature-subset variants: the ECE values use
branch B and the accuracy values use branch C. They are not two metrics of a
single fitted model in each row. Calibration selection chooses logistic
regression; accuracy selection chooses SVM. Source: cell 16.

The NBA calibration objective uses twenty equal-width home-probability bins.
If fewer than sixteen bins are occupied, its function returns a penalty of one.
That sentinel is not a measured 100% calibration error. On 2018/19, the saved
logistic model has 65.27% classification accuracy and 4.27% ECE. The saved SVM
has 64.80% classification accuracy, while its reported 100% calibration score
means that the bin-occupancy guard fired. Source: cells 5 and 20. The later
SVM accuracy is lower than its earlier 66.33% family-selection score.

The betting rule first checks whether the model's home probability exceeds
the inverse decimal home odds; if not, it checks the away side. This home-first
rule differs from selecting the maximum expected-return side. Starting capital
is 10,000 units. Fixed staking requests 100 per bet, equal to 1% of starting
capital. Eighth-Kelly requests one eighth of the full Kelly fraction of current
cash and is capped only by available cash, without the EPL study's explicit
2% per-bet ceiling. Bets settle sequentially, including same-date cash reuse;
the NBA routine does not use EPL's joint date-start allocation. Source: cell 17.

| Selected branch | Stake rule | Saved ending capital | Return on starting capital | Trading frequency | Hit ratio |
|---|---|---:|---:|---:|---:|
| Calibration / LR | Fixed 100 | 10,097.74 | +0.98% | 85.3% | 38.0% |
| Calibration / LR | Eighth Kelly | 6,500.40 | −35.00% | 85.3% | 38.0% |
| Accuracy / SVM | Fixed 100 | 12,502.98 | +25.03% | 88.6% | 34.9% |
| Accuracy / SVM | Eighth Kelly | 4,488.59 | −55.11% | 88.6% | 34.9% |

The notebook calls these capital returns `ROI`. The joint report should relabel
them as capital returns and reserve stake ROI for profit divided by total
stakes. The table shows that fixed and fractional-Kelly staking can generate
very different financial paths from the same selected sides. Positive
single-season results do not demonstrate reliable superiority of either
selection criterion. Source: saved cell 19 output.

## Nine-season robustness extension

The robustness extension reselects features in each rolling window but fits
logistic regression in both branches. It does not repeat the four-family LR,
RF, MLP and SVM search. Each betting season starts a new 10,000-unit account
and requests fixed stakes of 100. Across nine seasons, there are 9,344 betting
games. Sources: cells 21–24.

| Betting season | Games | Calibration capital return | Accuracy capital return |
|---|---:|---:|---:|
| 2014/15 | 1,072 | −65.30% | −16.78% |
| 2015/16 | 1,073 | −17.73% | −12.31% |
| 2016/17 | 1,074 | +57.42% | +46.75% |
| 2017/18 | 1,075 | −100.00% | −100.00% |
| 2018/19 | 1,074 | +2.08% | +12.25% |
| 2019/20 | 906 | +85.58% | +100.86% |
| 2020/21 | 924 | −31.59% | −33.85% |
| 2021/22 | 1,073 | −83.67% | −89.28% |
| 2022/23 | 1,073 | −2.89% | +6.93% |
| Mean | | −17.34% | −9.49% |
| Sample standard deviation | | 61.7 percentage points | 62.5 percentage points |

Calibration selection wins in three of nine annual comparisons. Both branches
reach zero in 2017/18; the wide variation and negative means do not establish a
stable positive edge. The 2018/19 row differs from the core table because this
extension uses newly selected logistic models and default fitting settings,
rather than the original tuned logistic-versus-SVM pair.

The source cell-25 cumulative graphic must not be presented as continuous
self-funded wealth. Its code adds each independently reset year's P&L onto a
running base, even after an earlier account is exhausted. The calibration line
ends below zero. Use the nine annual returns or separate annual account paths
instead. Annual percentages are saved only to two decimals; further numerical
precision should not be invented.

## New reconstruction audit and its limits

A fixed-parameter refit used the supplied raw files, supplied branch subsets
and `best_params.json`, following the notebook's ten-seed averaging. It performed
no feature search, new model selection or parameter tuning. The calibration-LR
refit reproduced both saved ending capitals to the cent, as well as the saved
2018 prediction accuracy and ECE. Its separately audited statistics are:

| Calibration LR | Fixed 100 | Eighth Kelly |
|---|---:|---:|
| Bets / wins | 916 / 348 | 916 / 348 |
| Hit ratio | 37.9913% | 37.9913% |
| Trading frequency | 85.2886% | 85.2886% |
| Expected gain per trade | 83.7048 | 103.4281 |
| Expected loss per trade | 54.2179 | 54.3674 |
| Observed average winning gain | 163.4992 | 177.0678 |
| Observed average losing loss | 100.0000 | 114.6464 |
| Stake turnover | 91,600.00 | 107,471.15 |
| Stake ROI | +0.1067% | −3.2563% |
| Maximum drawdown | 29.0916% | 59.4506% |

The SVM refit did not reproduce its saved outputs under the recorded local
library versions; all reconstructed SVM seeds reached the supplied 200,000
iteration limit. Original serialized SVM weights and original library versions
are not provided, and this audit does not resolve the discrepancy. Consequently
the supplied SVM results remain reported source results, and the newly generated
SVM curves and diagnostics must not be substituted for them. The derived audit
files explicitly mark the mismatch. Additional expected-payoff, turnover or
drawdown metrics for the saved SVM strategy remain unavailable.

For the same 1,074 native 2018/19 games, a direct normalized-inverse-odds
benchmark has log loss 0.5954, binary Brier 0.2045 and accuracy 66.95%, versus
0.6172, 0.2141 and 65.27% for the cent-matched logistic refit. Ordinary twenty-bin
ECE is 4.73% for the benchmark and 4.27% for LR. Thus this verified comparison
supports better market probability loss and accuracy, but not the claim that
the market is superior on every metric. It also illustrates why one calibration
summary cannot establish positive betting returns.

The supplied NBA report's additional pooled market, fused-feature and underdog
analyses do not have corresponding saved code or predictions in the notebook.
If retained, they must be attributed to that report rather than described as
independently reconstructed. In particular, avoid unverified power estimates
or claims proving luck, complete market efficiency or that box scores can never
provide value. The combined report can state the narrower supported finding:
this implementation does not establish a stable positive betting edge.
