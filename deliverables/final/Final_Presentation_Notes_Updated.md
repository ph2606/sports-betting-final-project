# Updated final presentation

Aman Dhillon and Panagiotis Housos
Supervisor: Daniel Totouom-Tangho

## Slide 1: Machine learning for sports betting

NBA and English Premier League: accuracy, calibration and archived-price returns.

Authors are confirmed by the September 30 joint project proposal. The supervisor name is supplied directly by the user: Daniel Totouom-Tangho. The requested order is common methodology first, NBA results second, Premier League results last. This presentation combines the implemented studies; it does not replace the separate league records with a new pooled investment experiment.

Sources:
- ML_Sports_Betting_Project_Proposal.pdf

## Slide 2: Data sources used in our project

Historical team and player records are matched to archived betting prices; the two leagues use different datasets.

Project sources, not a claim that we collected the original paper's raw dataset. NBA statistics are in ML Sports/regular_season_totals_2010_2024.csv: 33,316 team logs, 16,658 raw games, 14,471 cleaned games. The supplied NBA slide 3 describes this as a public GitHub extract; its original statistics-provider collection is undocumented. The NBA odds database is ML Sports/OddsData.sqlite, described in supplied documentation as Sportsbook Review archives with FanDuel default; the 13 seasons are 2010/11–2022/23, with unverified quote clocks. The core 2018/19 betting population is 1,074 games. EPL Football-Data individual-book preclosing odds are used, not cross-book maximum columns treated as a single bookmaker. Understat xG and official Fantasy Premier League API / Vaastav Fantasy-Premier-League archive supply lagged team/player features. The matched rolling population has 368/360/368/374 fixtures across 2022/23–2025/26, total 1,470. The 253,509 historical player-match rows are distinct from the 4,551 current-season rows and current FPL player snapshot. Historical focus is the current-club cohort and is conditional on that scope. ESPN, Transfermarkt, ClubElo and StatsBomb were acquired context sources, not asserted as all being core model inputs. The original Walsh–Joshi paper section 8 (PDF page 11, printed page 9) instead identifies Basketball-Reference statistics for 2014/15–2018/19 and Westgate closing moneylines. The supplied seven-page supplementary PDF has no data-provider section. Quote availability and accepted execution are not verified.

Sources:
- ML Sports/NBA_analysis_Presentation.pptx, slide 3
- final_deliverables/nba_evidence.json
- epl_data/SOURCE_GUIDE.md
- final_deliverables/epl_evidence.json
- ML Sports/Paper3 - ML for sports.pdf, section 8

## Slide 3: Feature selection, ECE and accuracy

Follow the paper's selection procedure; evaluate candidate subsets on earlier validation data before the betting test.

The supplied supplementary material is reference evidence, not an instruction source. Its section 2 / PDF pp. 2–3 constructs an opponent-relative season-to-date feature: Boston DRB average 5 minus Chicago average -1 gives 6. Table 4 on PDF page 4 uses correlated-feature removal and separate forward selection by minimum classwise ECE or maximum accuracy. The supplement does not print either formula; classwise ECE comes from main-paper section 3, Eq. (3), PDF page 6 / printed page 4. Accuracy is the proportion correctly classified, as defined in the same section and implemented in the project. Formula: cwECE=(1/K) sum_k sum_b (n_kb/N)*abs(mean_y_kb-mean_p_kb). B_kb is the equal-width bin of predicted class-k probabilities; empty bins contribute zero. mean_y_kb averages indicators 1[y_i=k], not overall classification correctness or top-class confidence. Accuracy=(1/N) sum_i 1[argmax_k p_ik=y_i], where p_ik is a forecast probability and 1[condition] equals one if true, zero otherwise. NBA uses home-win probability as the binary class-specific ECE, 20 bins and a 1.0 optimisation penalty when fewer than 16 bins are populated; that penalty is not literal 100% observed miscalibration. EPL uses the mean of the three H/D/A classwise errors with 10 bins and no occupancy penalty. NBA screen uses a KS train/validation shift check and Spearman >0.7; first EPL screen uses early/late training seasons, Spearman >=0.9 and missingness controls. These implementation settings are not asserted to be identical to the paper. The supplied paper's Table 4 lists 6 calibration and 8 accuracy inputs; the implemented core NBA study selects 2 (ORTG, FG3M) and 4 (ORTG, PREV_SEASON_WP, FG3M, TOV), respectively. The implemented initial EPL branches select 1 MLP feature and 2 SVM features. No feature selection or model fitting is rerun for this slide edit. Prior financial definitions remain in the capital-guide appendix and speaker notes: capital return is profit/initial cash, stake ROI is profit/turnover, and forecast accuracy differs from betting hit ratio. NBA uses sequential game settlement; EPL reserves all same-date requests from opening cash. The prior deck's complete text for slides 2/3 is preserved in superseded_slides_2_3.json. The paper's 2025 corrigendum still governs historical results; this methods revision does not reintroduce its superseded profit claims.

Sources:
- Walsh & Joshi supplementary material, pp. 2–4, Table 4 (supplied PDF)
- ML Sports/Paper3 - ML for sports.pdf, section 3, Eq. (3)
- ML Sports/Data.ipynb
- epl_modeling/metrics.py

## Slide 4: NBA: data and model selection

Team box-score differences are lagged; each team's first ten appearances are excluded as prediction targets.

Source cells 1-16. There are 25 box-score measures plus previous-season win percentage before screening. KS train-versus-validation screening drops OREB; absolute Spearman redundancy threshold is 0.7. Calibration SFS selects ORTG and FG3M; accuracy SFS selects ORTG, PREV_SEASON_WP, FG3M and TOV. TPE uses 30 trials for each family and branch, then ten seed-refit predictions are averaged for model-family selection. The notebook calls 2017/18 a test set, but it chooses LR for the calibration branch and SVM for the accuracy branch, so here it is labeled family selection. It is earlier than the separate 2018/19 betting season.

Sources:
- ML Sports/Data.ipynb

## Slide 5: NBA: saved 2018/19 betting results

Four rules, each starting with 10,000. Fixed 100 stakes equal 1% of initial capital.

The table preserves the saved notebook's four final amounts and rounded rates; these are not replaced by new SVM replay values. Source code refits selected models on 2014/15-2017/18 before betting 2018/19. The fixed-parameter audit reproduced both LR financial outcomes to cents but could not reproduce SVM; its ten fits reached the iteration limit. The source-recorded SVM final balances remain reported evidence with this explicit limitation. Source prediction accuracy is 65.27 percent for LR and 64.80 percent for SVM on 2018/19. LR guarded ECE is 4.27 percent; the SVM value of 1 means the bin-occupancy penalty fired, not literal 100 percent calibration error. The bar chart uses saved finals rather than an unverified reconstructed SVM wealth path.

Sources:
- ML Sports/Data.ipynb
- final_deliverables/nba_evidence.json

## Slide 6: NBA: nine-season annual robustness

Each season starts a fresh 10,000 account with fixed 100 requests. Annual paths are not one funded continuous portfolio.

Nine source-recorded seasons cover 2014/15 through 2022/23 and 9,344 betting fixtures. Both annual models are logistic regressions using different objective-selected feature subsets. The source means are minus 17.34 and minus 9.49 percent; calibration outperforms accuracy in three of nine seasons. Both paths exhaust their annual cash in 2017/18. The source notebook adds profits from independently reset accounts to draw a cumulative line; this deck deliberately uses annual-return bars so it does not imply continued funding after bankruptcy. Source annual figures are retained at their printed precision. The supplied PDF also reports stronger market log-loss results in additional analyses, but their full event-level supporting outputs are not in the provided notebook; those claims should not be treated as independently reproduced here.

Sources:
- ML Sports/Data.ipynb
- final_deliverables/nba_evidence.json

## Slide 7: NBA: what happens if we back the other team?

2017/18: both original fixed-stake accounts ended at zero. Both annual models are logistic regressions.

Complete zero inventory: 36 annual accounts across nine seasons, two LR feature-selection branches and fixed/eighth-Kelly sizing. Only the two 2017/18 fixed accounts have zero terminal capital. All 18 saved annual fixed returns and feature counts reconcile. Annual event probabilities were reconstructed using the unchanged source algorithm; the notebook did not preserve saved annual fitted weights or event-level probabilities. This is source-method reconstruction, not proof of byte-identical original predictions. The core unreconciled SVM refit is not used. The original home-first value eligibility and exact probability filter are retained. At most one bet per game; source game-sequential settlement, no borrowing. The full inverse has 915 calibration bets and 884 accuracy bets. Full-season capital returns are 11.48% and -12.15%. Matched recorded-prefix results retain the original positive-stake fixtures and stakes; both lose. The 9,999 whole-match-date percentile bootstrap fixes selected models, signals and stakes: calibration: [-4.82%, 7.33%]; accuracy: [-7.36%, 4.53%]. It does not adjust for fitting, strategy search or selecting failures after seeing outcomes. Quotes and execution timestamps remain unverified. Financial hit ratio counts positive-profit bets; expected components are model-implied, not realised average win/loss. The inverse does not receive a new positive-edge gate under the original forecast.

Sources:
- C:\Users\melin\OneDrive\Desktop\nyu\fall 2026\Stat Arb\final_project\final_review\nba_results\inverse_metrics.csv
- C:\Users\melin\OneDrive\Desktop\nyu\fall 2026\Stat Arb\final_project\final_review\nba_results\audit_summary.json
- C:\Users\melin\OneDrive\Desktop\nyu\fall 2026\Stat Arb\final_project\final_review\nba_results\conditional_uncertainty.csv

## Slide 8: EPL: the proposal's accuracy–calibration comparison

The first experiment evaluates 374 matches in 2025/26 after separate tuning, calibration, family selection and strategy validation.

This is the experiment most directly aligned with the joint proposal: accuracy selects SVM, calibration selects MLP. Both branches receive the same disjoint temperature calibration. Neither primary validation policy found a threshold with at least thirty bets and strictly positive validation stake ROI, so both hold cash in test; no-trade ROI is undefined. The secondary 5 percent policy was separately declared and is not a substitute chosen from test returns. The displayed 100K accounts are rescaled counterpart strategies from the saved laboratory. SVM loses 8,330 on 371 bets and MLP gains 1,370 on 333 bets, with stake ROIs minus 2.2453 and plus 0.4114 percent. Their conditional intervals both include zero. The raw market has stronger proper probability scores than either learned branch. Later rolling/player studies revisit already inspected outcomes and are exploratory.

Sources:
- epl_modeling/results/RESULTS.md
- epl_modeling/results/classification_scores.csv
- epl_strategy_lab/results/20261015T040052Z_100k84/metrics.csv

## Slide 9: EPL: money progression of all 116 strategies

2025/26 is the common season available for every account. Each starts with 100,000 monetary units.

The graph has 116 distinct strategy IDs and 13,224 points, including 114 dates per curve with the 100K anchor. The strategies combine model, outcome selection, prices and sizing rather than representing 116 independent fitted algorithms. Only 88 have comparable continuous four-year records. No earlier records are invented for 28 first-study configurations. New player-study accounts all lose over four continuous years, even when one 2025 slice profited. The graph is an archived-price replay, not verified executed betting.

Sources:
- epl_player_models/results/20261020_player_models_review/graph_equity_2025_all.csv

## Slide 10: EPL: best prediction model: odds + team/player form

Lowest prediction error among the learned models on the same four-year sample. Trading statistics: 2022/23–2025/26, 1,470 matches.

Starts with bookmaker probabilities, then adjusts them using earlier team results and player form.
Bookmaker odds + team/player form Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 5%. 1,000 per bet: 1% of INITIAL 100,000; the amount stays fixed as cash changes. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Highest archived individual-bookmaker odds for the chosen outcome. With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
The fixed 1,000 equals 1% of the INITIAL capital, not 1% of a changing account. All same-date requests use opening cash and are reduced proportionally if together they exceed available cash. This model's prediction accuracy and its trading hit ratio measure different things. Historical results are exploratory. Best refers to the learned model's pooled prediction loss, not the highest ending account; the raw market benchmark has lower prediction loss.
Exact configuration:
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Rolling market residual: team + player; max_edge selection among the allowed outcomes at best individual-book quotes. Require selected model expected return strictly above 5%; stake flat 1,000.", "diagnostic": false, "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.05, "min_odds": null, "model_key": "residual_team_players", "model_label": "Rolling market residual: team + player", "name": "Rolling market residual: team + player | predeclared 5% edge | best individual-book quotes | flat 1,000", "odds_mode": "best", "origin": "legacy", "policy_family": "predeclared 5% edge", "selection_rule": "max_edge", "staking": "fixed", "strategy_id": "S029", "study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}

Sources:
- epl_modeling/ablation_results/predictions.parquet
- epl_strategy_validation\results\20261015_temporal_selection\metrics_continuous.parquet
- epl_player_models\results\20261020_player_models_review\metrics_continuous.parquet

## Slide 11: EPL: simplest model: past result frequencies

No match-specific inputs: every game in a season gets the same three probabilities. Trading statistics: 2022/23–2025/26, 1,470 matches.

Counts how often home wins, draws and away wins happened in the training data. Uses those fractions for every game.
Past home/draw/away frequencies Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 5%. 1,000 per bet: 1% of INITIAL 100,000; the amount stays fixed as cash changes. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Highest archived individual-bookmaker odds for the chosen outcome. With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
The fixed 1,000 equals 1% of the INITIAL capital, not 1% of a changing account. All same-date requests use opening cash and are reduced proportionally if together they exceed available cash. This model's prediction accuracy and its trading hit ratio measure different things. Historical results are exploratory. Best refers to the learned model's pooled prediction loss, not the highest ending account; the raw market benchmark has lower prediction loss.
Exact configuration:
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Rolling training-class frequency; max_edge selection among the allowed outcomes at best individual-book quotes. Require selected model expected return strictly above 5%; stake flat 1,000.", "diagnostic": false, "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.05, "min_odds": null, "model_key": "baseline_class_frequency", "model_label": "Rolling training-class frequency", "name": "Rolling training-class frequency | predeclared 5% edge | best individual-book quotes | flat 1,000", "odds_mode": "best", "origin": "legacy", "policy_family": "predeclared 5% edge", "selection_rule": "max_edge", "staking": "fixed", "strategy_id": "S033", "study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}

Sources:
- epl_modeling/ablation_results/predictions.parquet
- epl_strategy_validation\results\20261015_temporal_selection\metrics_continuous.parquet
- epl_player_models\results\20261020_player_models_review\metrics_continuous.parquet

## Slide 12: EPL: team model: earlier team performance

Uses team performance and data-coverage controls; no player-performance or odds predictors. Trading statistics: 2022/23–2025/26, 1,470 matches.

Uses earlier goals, shots on target, corners, points, rest days and previous-season results to estimate home/draw/away chances.
Team form Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 5%. 1,000 per bet: 1% of INITIAL 100,000; the amount stays fixed as cash changes. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Highest archived individual-bookmaker odds for the chosen outcome. With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
The fixed 1,000 equals 1% of the INITIAL capital, not 1% of a changing account. All same-date requests use opening cash and are reduced proportionally if together they exceed available cash. This model's prediction accuracy and its trading hit ratio measure different things. Historical results are exploratory. Best refers to the learned model's pooled prediction loss, not the highest ending account; the raw market benchmark has lower prediction loss.
Exact configuration:
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Rolling logistic: team; max_edge selection among the allowed outcomes at best individual-book quotes. Require selected model expected return strictly above 5%; stake flat 1,000.", "diagnostic": false, "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.05, "min_odds": null, "model_key": "logit_team_only", "model_label": "Rolling logistic: team", "name": "Rolling logistic: team | predeclared 5% edge | best individual-book quotes | flat 1,000", "odds_mode": "best", "origin": "legacy", "policy_family": "predeclared 5% edge", "selection_rule": "max_edge", "staking": "fixed", "strategy_id": "S017", "study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}

Sources:
- epl_modeling/ablation_results/predictions.parquet
- epl_strategy_validation\results\20261015_temporal_selection\metrics_continuous.parquet
- epl_player_models\results\20261020_player_models_review\metrics_continuous.parquet

## Slide 13: EPL: player model: earlier Fantasy Premier League form

Uses previous player records; no team-strength or bookmaker-odds predictors. Trading statistics: 2022/23–2025/26, 1,470 matches.

Uses earlier FPL points, goals and assists.
Adds minutes and other player statistics.
Looks back over five and ten games.
Player form (logistic) Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 5%. 1,000 per bet: 1% of INITIAL 100,000; the amount stays fixed as cash changes. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Highest archived individual-bookmaker odds for the chosen outcome. With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
The fixed 1,000 equals 1% of the INITIAL capital, not 1% of a changing account. All same-date requests use opening cash and are reduced proportionally if together they exceed available cash. This model's prediction accuracy and its trading hit ratio measure different things. Historical results are exploratory. Best refers to the learned model's pooled prediction loss, not the highest ending account; the raw market benchmark has lower prediction loss.
Exact configuration:
{"allocation_basis": "All requests use date-start cash and are uniformly scaled to available cash before any same-date outcome settles", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Player form only | Logistic regression; choose the allowed H/D/A outcome with maximum p × odds − 1 at the best archived individual-book quote. Trade only for edge strictly greater than 5%; request flat 1,000. H/D/A order resolves ties.", "diagnostic": true, "feature_group": "player_form", "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.05, "min_odds": null, "model_key": "pm_logistic_player_form", "model_label": "Player form only | Logistic regression", "model_type": "logistic", "name": "Player form only | Logistic regression | best | flat 1,000", "odds_mode": "best", "origin": "new_player_model_study", "policy_family": "frozen 5% player-study diagnostic", "selection_rule": "max_edge", "staking": "fixed", "strategy_id": "P009", "study_status": "exploratory_previously_inspected_history_not_new_holdout_or_selected_live_betting_policy"}

Sources:
- epl_player_models/results/20261020_player_models_review/model_metrics_pooled.csv
- epl_strategy_validation\results\20261015_temporal_selection\metrics_continuous.parquet
- epl_player_models\results\20261020_player_models_review\metrics_continuous.parquet

## Slide 14: EPL: back both other outcomes after a zero account

17 bankrupt strategy/price contexts, covering 15 strategy IDs. Each inverse starts a new 100,000 account.

Football has three outcomes. The opposite of home is draw OR away, rather than away alone. For original pick k and other outcomes j, let S=sum(1/O_j). With requested total bundle risk R=1,000, each leg stake is R(1/O_j)/S. Either other result returns R/S gross. The original pick produces loss R; the complementary event produces net R(1/S-1). When S is at least one, even the complementary event can have nonpositive profit, so event hit and profitable-bundle hit are separate fields. The original full-horizon signal is retained; no new positive-edge requirement is imposed on the inverse. All 1,470 opportunities in 2022/23–2025/26 remain eligible for signal reconstruction, including dates after the original account stops. Uniform same-date scaling reserves total bundle risk from opening cash and any original date cap; no borrowing or reuse of same-date wins. Thirteen contexts are in the principal comparison, plus four bankrupt Bet365 reference-price policy replays. S041 and S043 occur at both price modes. Best quotes and Bet365 are retained per context. No unobserved double-chance quote or exchange lay quote is invented for the priced-complement results. Three costs (0%, 2%, 5%) are applied to positive NET portfolio profit per fixture, not gross payout or per-leg wins; these are illustrative haircuts. The full study includes 51 contexts, 153 funded priced complements, 51 hypothetical risk-matched lays, 17 prefix complements and 17 recorded-exposure identity diagnostics. The 34 controls are the other original fixed-stake accounts, not an untouched holdout. Intervals resample whole match dates within season while holding realised funded cashflows fixed; no re-fitting, re-sizing or strategy-search adjustment. 9 of 17 primary intervals include zero, including 2 of 2 profitable accounts. Observed bankruptcy selected the cohort after outcomes; positive returns are unconfirmed hypotheses. The arithmetic mirror of original recorded loss is only an identity, with 0 contexts requiring extra opening collateral for the exact recorded exposures. Archived quotes have unverified simultaneous availability and execution.

Sources:
- C:\Users\melin\OneDrive\Desktop\nyu\fall 2026\Stat Arb\final_project\final_review\epl_results\metrics.csv
- C:\Users\melin\OneDrive\Desktop\nyu\fall 2026\Stat Arb\final_project\final_review\epl_results\summary.json
- final_review/inverse_protocol.md

## Slide 15: What the completed project supports

Calibration, quoted prices and capital risk must be evaluated together. Historical profit alone is not enough.

This answers the September 30 project proposal using completed work, not the initial ambition. NBA annual mean capital returns are -17.34% (calibration-selected LR features) and -9.49% (accuracy-selected LR features), with independent annual resets. The core 2018/19 SVM results remain explicitly source-reported and unreproduced. EPL primary validation found no admissible threshold with at least 30 bets and positive validation stake ROI, so both test policies hold cash. The predeclared EPL secondary calibration branch has +0.4114% stake ROI versus -2.2453% for accuracy; both conditional intervals include zero. Six new player-feature/model combinations have worse pooled log loss than their matched same-family team controls; this does not rule out every possible use of player information. The four arbitrage flags use archived best quotes; no simultaneous accepted fills or complete quote clocks are verified. Opposite-policy counts refer to the two NBA full-season cases and 17 EPL previously bankrupt strategy/price contexts at zero hypothetical cost, not 17 independent newly fitted models. Selection by observed bankruptcy is retrospective. Existing multiple-comparison adjustments do not cover the new inverses. A grade cannot be guaranteed; clarity, correct financial accounting and reproducibility support the academic argument.

Sources:
- final_review/project_review.md
- final_review/review_checks.json
- final_deliverables/epl_evidence.json
- final_review/epl_results/metrics.csv

## Slide 16: Appendix: the four NBA betting rules

One bet at most per game; settle sequentially. This is not the EPL joint same-date funding rule.

The source simulator tests ph>1/oh first, otherwise pa>1/oa, and excludes a selected probability exactly 0.5 with its default margin-zero filter. Fixed requests are 100 and Kelly requests use one eighth of the full Kelly fraction. Both are clamped to available current cash. The source may use settlement from an earlier processed game to fund another game on the same date, unlike EPL. All four records start at 10,000 independently. Financial results in the core table remain source-recorded; LR only was reproduced to cents in the fixed-parameter audit.

Sources:
- ML Sports/Data.ipynb

## Slide 17: EPL appendix: how much capital each rule uses

Stake means the amount requested for one bet. The next pages state the setting for every strategy.

The Kelly multiplier is one quarter, one half, full Kelly or another explicitly listed fraction. B is cash at the start of the date. Formula B*min(max_bet_fraction,kelly_fraction*(p*O-1)/(O-1)); eligibility ensures positive edges where relevant. At most one bet per match. Same-date winnings are not used to fund another same-date bet. Fixed stakes do not automatically shrink to 1% as the account falls; only cash/date-budget allocation can scale them. Prices: Best odds means the highest saved individual-book quote for the chosen outcome; Bet365 means its saved reference quote. These are archived prices with unverified execution clocks.

Sources:
- epl_strategy_lab/engine.py
- epl_player_models\results\20261020_player_models_review\all_strategy_catalog.json

## Slide 18: EPL appendix: strategy rules (1/9)

Default: choose the highest model-estimated return (probability × odds − 1). Only bet above the listed threshold.

Paired IDs share their forecast and entry rule but have separately labeled stakes. Fixed 1,000 is 1% of initial capital; a stated cash percentage uses date-start cash. Kelly fractions and caps are distinct. All IDs below are individual preserved strategies; grouping changes no rule. 'Positive return:6/8 models' requires six models to assign positive estimated return to the chosen outcome, not six favorite picks. H=home win, D=draw, A=away win.

S001: Original SVM forecast No bets: the earlier validation selected cash. 0 per trade; all starting 100,000 stays in cash. No borrowing; no betting exposure. No quotes used for a trade. Starting capital 100,000 stays 100,000 throughout the replay.
Example: Starting capital 100,000 stays 100,000 throughout the replay.
Exact configuration:
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": true, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "First-study accuracy-selected SVM: validation selected no admissible positive-return rule; the frozen threshold is 1,000,000 and this configuration remains entirely in cash.", "diagnostic": false, "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 1000000.0, "min_odds": null, "model_key": "first_accuracy", "model_label": "First-study accuracy-selected SVM", "name": "First-study accuracy-selected SVM | locked primary cash | best individual-book quotes | flat 1,000", "odds_mode": "best", "origin": "legacy", "policy_family": "locked primary cash", "selection_rule": "max_edge", "staking": "fixed", "strategy_id": "S001", "study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}

S002: Original SVM forecast No bets: the earlier validation selected cash. 0 per trade; all starting 100,000 stays in cash. No borrowing; no betting exposure. No quotes used for a trade. Starting capital 100,000 stays 100,000 throughout the replay.
Example: Starting capital 100,000 stays 100,000 throughout the replay.
Exact configuration:
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": true, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "First-study accuracy-selected SVM: validation selected no admissible positive-return rule; the frozen threshold is 1,000,000 and this configuration remains entirely in cash.", "diagnostic": false, "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 1000000.0, "min_odds": null, "model_key": "first_accuracy", "model_label": "First-study accuracy-selected SVM", "name": "First-study accuracy-selected SVM | locked primary cash | best individual-book quotes | 0.25 Kelly, per-bet cap 2%", "odds_mode": "best", "origin": "legacy", "policy_family": "locked primary cash", "selection_rule": "max_edge", "staking": "kelly", "strategy_id": "S002", "study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}

S003: Original SVM forecast No bets: the earlier validation selected cash. 0 per trade; all starting 100,000 stays in cash. No borrowing; no betting exposure. No quotes used for a trade. Starting capital 100,000 stays 100,000 throughout the replay.
Example: Starting capital 100,000 stays 100,000 throughout the replay.
Exact configuration:
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": true, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "First-study accuracy-selected SVM: validation selected no admissible positive-return rule; the frozen threshold is 1,000,000 and this configuration remains entirely in cash.", "diagnostic": false, "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 1000000.0, "min_odds": null, "model_key": "first_accuracy", "model_label": "First-study accuracy-selected SVM", "name": "First-study accuracy-selected SVM | locked primary cash | Bet365 reference quotes | flat 1,000", "odds_mode": "reference", "origin": "legacy", "policy_family": "locked primary cash", "selection_rule": "max_edge", "staking": "fixed", "strategy_id": "S003", "study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}

S004: Original SVM forecast No bets: the earlier validation selected cash. 0 per trade; all starting 100,000 stays in cash. No borrowing; no betting exposure. No quotes used for a trade. Starting capital 100,000 stays 100,000 throughout the replay.
Example: Starting capital 100,000 stays 100,000 throughout the replay.
Exact configuration:
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": true, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "First-study accuracy-selected SVM: validation selected no admissible positive-return rule; the frozen threshold is 1,000,000 and this configuration remains entirely in cash.", "diagnostic": false, "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 1000000.0, "min_odds": null, "model_key": "first_accuracy", "model_label": "First-study accuracy-selected SVM", "name": "First-study accuracy-selected SVM | locked primary cash | Bet365 reference quotes | 0.25 Kelly, per-bet cap 2%", "odds_mode": "reference", "origin": "legacy", "policy_family": "locked primary cash", "selection_rule": "max_edge", "staking": "kelly", "strategy_id": "S004", "study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}

S005: Original SVM forecast Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 5%. 1,000 per bet: 1% of INITIAL 100,000; the amount stays fixed as cash changes. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Highest archived individual-bookmaker odds for the chosen outcome. With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Example: With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "First-study accuracy-selected SVM; max_edge selection among the allowed outcomes at best individual-book quotes. Require selected model expected return strictly above 5%; stake flat 1,000.", "diagnostic": false, "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.05, "min_odds": null, "model_key": "first_accuracy", "model_label": "First-study accuracy-selected SVM", "name": "First-study accuracy-selected SVM | predeclared 5% edge | best individual-book quotes | flat 1,000", "odds_mode": "best", "origin": "legacy", "policy_family": "predeclared 5% edge", "selection_rule": "max_edge", "staking": "fixed", "strategy_id": "S005", "study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}

S006: Original SVM forecast Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 5%. Quarter Kelly: B × min(2%, 0.25 × max(0, p×O−1)/(O−1)); B = date-start cash. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Highest archived individual-bookmaker odds for the chosen outcome. B=100,000, p=40%, O=3: full Kelly=10%; 0.25 × 10% capped at 2% requests 2,000 before shared date/cash reduction.
Example: B=100,000, p=40%, O=3: full Kelly=10%; 0.25 × 10% capped at 2% requests 2,000 before shared date/cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "First-study accuracy-selected SVM; max_edge selection among the allowed outcomes at best individual-book quotes. Require selected model expected return strictly above 5%; stake 0.25 Kelly, per-bet cap 2%.", "diagnostic": false, "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.05, "min_odds": null, "model_key": "first_accuracy", "model_label": "First-study accuracy-selected SVM", "name": "First-study accuracy-selected SVM | predeclared 5% edge | best individual-book quotes | 0.25 Kelly, per-bet cap 2%", "odds_mode": "best", "origin": "legacy", "policy_family": "predeclared 5% edge", "selection_rule": "max_edge", "staking": "kelly", "strategy_id": "S006", "study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}

S007: Original SVM forecast Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 5%. 1,000 per bet: 1% of INITIAL 100,000; the amount stays fixed as cash changes. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Archived Bet365 odds for the chosen outcome. With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Example: With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "First-study accuracy-selected SVM; max_edge selection among the allowed outcomes at Bet365 reference quotes. Require selected model expected return strictly above 5%; stake flat 1,000.", "diagnostic": false, "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.05, "min_odds": null, "model_key": "first_accuracy", "model_label": "First-study accuracy-selected SVM", "name": "First-study accuracy-selected SVM | predeclared 5% edge | Bet365 reference quotes | flat 1,000", "odds_mode": "reference", "origin": "legacy", "policy_family": "predeclared 5% edge", "selection_rule": "max_edge", "staking": "fixed", "strategy_id": "S007", "study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}

S008: Original SVM forecast Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 5%. Quarter Kelly: B × min(2%, 0.25 × max(0, p×O−1)/(O−1)); B = date-start cash. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Archived Bet365 odds for the chosen outcome. B=100,000, p=40%, O=3: full Kelly=10%; 0.25 × 10% capped at 2% requests 2,000 before shared date/cash reduction.
Example: B=100,000, p=40%, O=3: full Kelly=10%; 0.25 × 10% capped at 2% requests 2,000 before shared date/cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "First-study accuracy-selected SVM; max_edge selection among the allowed outcomes at Bet365 reference quotes. Require selected model expected return strictly above 5%; stake 0.25 Kelly, per-bet cap 2%.", "diagnostic": false, "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.05, "min_odds": null, "model_key": "first_accuracy", "model_label": "First-study accuracy-selected SVM", "name": "First-study accuracy-selected SVM | predeclared 5% edge | Bet365 reference quotes | 0.25 Kelly, per-bet cap 2%", "odds_mode": "reference", "origin": "legacy", "policy_family": "predeclared 5% edge", "selection_rule": "max_edge", "staking": "kelly", "strategy_id": "S008", "study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}

S009: Original neural-network forecast No bets: the earlier validation selected cash. 0 per trade; all starting 100,000 stays in cash. No borrowing; no betting exposure. No quotes used for a trade. Starting capital 100,000 stays 100,000 throughout the replay.
Example: Starting capital 100,000 stays 100,000 throughout the replay.
Exact configuration:
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": true, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "First-study calibration-selected MLP: validation selected no admissible positive-return rule; the frozen threshold is 1,000,000 and this configuration remains entirely in cash.", "diagnostic": false, "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 1000000.0, "min_odds": null, "model_key": "first_calibration", "model_label": "First-study calibration-selected MLP", "name": "First-study calibration-selected MLP | locked primary cash | best individual-book quotes | flat 1,000", "odds_mode": "best", "origin": "legacy", "policy_family": "locked primary cash", "selection_rule": "max_edge", "staking": "fixed", "strategy_id": "S009", "study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}

S010: Original neural-network forecast No bets: the earlier validation selected cash. 0 per trade; all starting 100,000 stays in cash. No borrowing; no betting exposure. No quotes used for a trade. Starting capital 100,000 stays 100,000 throughout the replay.
Example: Starting capital 100,000 stays 100,000 throughout the replay.
Exact configuration:
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": true, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "First-study calibration-selected MLP: validation selected no admissible positive-return rule; the frozen threshold is 1,000,000 and this configuration remains entirely in cash.", "diagnostic": false, "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 1000000.0, "min_odds": null, "model_key": "first_calibration", "model_label": "First-study calibration-selected MLP", "name": "First-study calibration-selected MLP | locked primary cash | best individual-book quotes | 0.25 Kelly, per-bet cap 2%", "odds_mode": "best", "origin": "legacy", "policy_family": "locked primary cash", "selection_rule": "max_edge", "staking": "kelly", "strategy_id": "S010", "study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}

S011: Original neural-network forecast No bets: the earlier validation selected cash. 0 per trade; all starting 100,000 stays in cash. No borrowing; no betting exposure. No quotes used for a trade. Starting capital 100,000 stays 100,000 throughout the replay.
Example: Starting capital 100,000 stays 100,000 throughout the replay.
Exact configuration:
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": true, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "First-study calibration-selected MLP: validation selected no admissible positive-return rule; the frozen threshold is 1,000,000 and this configuration remains entirely in cash.", "diagnostic": false, "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 1000000.0, "min_odds": null, "model_key": "first_calibration", "model_label": "First-study calibration-selected MLP", "name": "First-study calibration-selected MLP | locked primary cash | Bet365 reference quotes | flat 1,000", "odds_mode": "reference", "origin": "legacy", "policy_family": "locked primary cash", "selection_rule": "max_edge", "staking": "fixed", "strategy_id": "S011", "study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}

S012: Original neural-network forecast No bets: the earlier validation selected cash. 0 per trade; all starting 100,000 stays in cash. No borrowing; no betting exposure. No quotes used for a trade. Starting capital 100,000 stays 100,000 throughout the replay.
Example: Starting capital 100,000 stays 100,000 throughout the replay.
Exact configuration:
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": true, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "First-study calibration-selected MLP: validation selected no admissible positive-return rule; the frozen threshold is 1,000,000 and this configuration remains entirely in cash.", "diagnostic": false, "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 1000000.0, "min_odds": null, "model_key": "first_calibration", "model_label": "First-study calibration-selected MLP", "name": "First-study calibration-selected MLP | locked primary cash | Bet365 reference quotes | 0.25 Kelly, per-bet cap 2%", "odds_mode": "reference", "origin": "legacy", "policy_family": "locked primary cash", "selection_rule": "max_edge", "staking": "kelly", "strategy_id": "S012", "study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}

S013: Original neural-network forecast Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 5%. 1,000 per bet: 1% of INITIAL 100,000; the amount stays fixed as cash changes. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Highest archived individual-bookmaker odds for the chosen outcome. With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Example: With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "First-study calibration-selected MLP; max_edge selection among the allowed outcomes at best individual-book quotes. Require selected model expected return strictly above 5%; stake flat 1,000.", "diagnostic": false, "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.05, "min_odds": null, "model_key": "first_calibration", "model_label": "First-study calibration-selected MLP", "name": "First-study calibration-selected MLP | predeclared 5% edge | best individual-book quotes | flat 1,000", "odds_mode": "best", "origin": "legacy", "policy_family": "predeclared 5% edge", "selection_rule": "max_edge", "staking": "fixed", "strategy_id": "S013", "study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}

S014: Original neural-network forecast Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 5%. Quarter Kelly: B × min(2%, 0.25 × max(0, p×O−1)/(O−1)); B = date-start cash. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Highest archived individual-bookmaker odds for the chosen outcome. B=100,000, p=40%, O=3: full Kelly=10%; 0.25 × 10% capped at 2% requests 2,000 before shared date/cash reduction.
Example: B=100,000, p=40%, O=3: full Kelly=10%; 0.25 × 10% capped at 2% requests 2,000 before shared date/cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "First-study calibration-selected MLP; max_edge selection among the allowed outcomes at best individual-book quotes. Require selected model expected return strictly above 5%; stake 0.25 Kelly, per-bet cap 2%.", "diagnostic": false, "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.05, "min_odds": null, "model_key": "first_calibration", "model_label": "First-study calibration-selected MLP", "name": "First-study calibration-selected MLP | predeclared 5% edge | best individual-book quotes | 0.25 Kelly, per-bet cap 2%", "odds_mode": "best", "origin": "legacy", "policy_family": "predeclared 5% edge", "selection_rule": "max_edge", "staking": "kelly", "strategy_id": "S014", "study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}

S015: Original neural-network forecast Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 5%. 1,000 per bet: 1% of INITIAL 100,000; the amount stays fixed as cash changes. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Archived Bet365 odds for the chosen outcome. With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Example: With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "First-study calibration-selected MLP; max_edge selection among the allowed outcomes at Bet365 reference quotes. Require selected model expected return strictly above 5%; stake flat 1,000.", "diagnostic": false, "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.05, "min_odds": null, "model_key": "first_calibration", "model_label": "First-study calibration-selected MLP", "name": "First-study calibration-selected MLP | predeclared 5% edge | Bet365 reference quotes | flat 1,000", "odds_mode": "reference", "origin": "legacy", "policy_family": "predeclared 5% edge", "selection_rule": "max_edge", "staking": "fixed", "strategy_id": "S015", "study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}

S016: Original neural-network forecast Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 5%. Quarter Kelly: B × min(2%, 0.25 × max(0, p×O−1)/(O−1)); B = date-start cash. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Archived Bet365 odds for the chosen outcome. B=100,000, p=40%, O=3: full Kelly=10%; 0.25 × 10% capped at 2% requests 2,000 before shared date/cash reduction.
Example: B=100,000, p=40%, O=3: full Kelly=10%; 0.25 × 10% capped at 2% requests 2,000 before shared date/cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "First-study calibration-selected MLP; max_edge selection among the allowed outcomes at Bet365 reference quotes. Require selected model expected return strictly above 5%; stake 0.25 Kelly, per-bet cap 2%.", "diagnostic": false, "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.05, "min_odds": null, "model_key": "first_calibration", "model_label": "First-study calibration-selected MLP", "name": "First-study calibration-selected MLP | predeclared 5% edge | Bet365 reference quotes | 0.25 Kelly, per-bet cap 2%", "odds_mode": "reference", "origin": "legacy", "policy_family": "predeclared 5% edge", "selection_rule": "max_edge", "staking": "kelly", "strategy_id": "S016", "study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}

S017: Team form Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 5%. 1,000 per bet: 1% of INITIAL 100,000; the amount stays fixed as cash changes. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Highest archived individual-bookmaker odds for the chosen outcome. With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Example: With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Rolling logistic: team; max_edge selection among the allowed outcomes at best individual-book quotes. Require selected model expected return strictly above 5%; stake flat 1,000.", "diagnostic": false, "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.05, "min_odds": null, "model_key": "logit_team_only", "model_label": "Rolling logistic: team", "name": "Rolling logistic: team | predeclared 5% edge | best individual-book quotes | flat 1,000", "odds_mode": "best", "origin": "legacy", "policy_family": "predeclared 5% edge", "selection_rule": "max_edge", "staking": "fixed", "strategy_id": "S017", "study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}

S018: Team form Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 5%. Quarter Kelly: B × min(2%, 0.25 × max(0, p×O−1)/(O−1)); B = date-start cash. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Highest archived individual-bookmaker odds for the chosen outcome. B=100,000, p=40%, O=3: full Kelly=10%; 0.25 × 10% capped at 2% requests 2,000 before shared date/cash reduction.
Example: B=100,000, p=40%, O=3: full Kelly=10%; 0.25 × 10% capped at 2% requests 2,000 before shared date/cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Rolling logistic: team; max_edge selection among the allowed outcomes at best individual-book quotes. Require selected model expected return strictly above 5%; stake 0.25 Kelly, per-bet cap 2%.", "diagnostic": false, "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.05, "min_odds": null, "model_key": "logit_team_only", "model_label": "Rolling logistic: team", "name": "Rolling logistic: team | predeclared 5% edge | best individual-book quotes | 0.25 Kelly, per-bet cap 2%", "odds_mode": "best", "origin": "legacy", "policy_family": "predeclared 5% edge", "selection_rule": "max_edge", "staking": "kelly", "strategy_id": "S018", "study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}

S019: Team form + chance quality Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 5%. 1,000 per bet: 1% of INITIAL 100,000; the amount stays fixed as cash changes. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Highest archived individual-bookmaker odds for the chosen outcome. With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Example: With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Rolling logistic: team + xG; max_edge selection among the allowed outcomes at best individual-book quotes. Require selected model expected return strictly above 5%; stake flat 1,000.", "diagnostic": false, "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.05, "min_odds": null, "model_key": "logit_team_xg", "model_label": "Rolling logistic: team + xG", "name": "Rolling logistic: team + xG | predeclared 5% edge | best individual-book quotes | flat 1,000", "odds_mode": "best", "origin": "legacy", "policy_family": "predeclared 5% edge", "selection_rule": "max_edge", "staking": "fixed", "strategy_id": "S019", "study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}

S020: Team form + chance quality Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 5%. Quarter Kelly: B × min(2%, 0.25 × max(0, p×O−1)/(O−1)); B = date-start cash. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Highest archived individual-bookmaker odds for the chosen outcome. B=100,000, p=40%, O=3: full Kelly=10%; 0.25 × 10% capped at 2% requests 2,000 before shared date/cash reduction.
Example: B=100,000, p=40%, O=3: full Kelly=10%; 0.25 × 10% capped at 2% requests 2,000 before shared date/cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Rolling logistic: team + xG; max_edge selection among the allowed outcomes at best individual-book quotes. Require selected model expected return strictly above 5%; stake 0.25 Kelly, per-bet cap 2%.", "diagnostic": false, "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.05, "min_odds": null, "model_key": "logit_team_xg", "model_label": "Rolling logistic: team + xG", "name": "Rolling logistic: team + xG | predeclared 5% edge | best individual-book quotes | 0.25 Kelly, per-bet cap 2%", "odds_mode": "best", "origin": "legacy", "policy_family": "predeclared 5% edge", "selection_rule": "max_edge", "staking": "kelly", "strategy_id": "S020", "study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}

S021: Team form + player form Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 5%. 1,000 per bet: 1% of INITIAL 100,000; the amount stays fixed as cash changes. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Highest archived individual-bookmaker odds for the chosen outcome. With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Example: With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Rolling logistic: team + player; max_edge selection among the allowed outcomes at best individual-book quotes. Require selected model expected return strictly above 5%; stake flat 1,000.", "diagnostic": false, "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.05, "min_odds": null, "model_key": "logit_team_players", "model_label": "Rolling logistic: team + player", "name": "Rolling logistic: team + player | predeclared 5% edge | best individual-book quotes | flat 1,000", "odds_mode": "best", "origin": "legacy", "policy_family": "predeclared 5% edge", "selection_rule": "max_edge", "staking": "fixed", "strategy_id": "S021", "study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}

S022: Team form + player form Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 5%. Quarter Kelly: B × min(2%, 0.25 × max(0, p×O−1)/(O−1)); B = date-start cash. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Highest archived individual-bookmaker odds for the chosen outcome. B=100,000, p=40%, O=3: full Kelly=10%; 0.25 × 10% capped at 2% requests 2,000 before shared date/cash reduction.
Example: B=100,000, p=40%, O=3: full Kelly=10%; 0.25 × 10% capped at 2% requests 2,000 before shared date/cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Rolling logistic: team + player; max_edge selection among the allowed outcomes at best individual-book quotes. Require selected model expected return strictly above 5%; stake 0.25 Kelly, per-bet cap 2%.", "diagnostic": false, "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.05, "min_odds": null, "model_key": "logit_team_players", "model_label": "Rolling logistic: team + player", "name": "Rolling logistic: team + player | predeclared 5% edge | best individual-book quotes | 0.25 Kelly, per-bet cap 2%", "odds_mode": "best", "origin": "legacy", "policy_family": "predeclared 5% edge", "selection_rule": "max_edge", "staking": "kelly", "strategy_id": "S022", "study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}

Sources:
- epl_player_models\results\20261020_player_models_review\all_strategy_catalog.json

## Slide 19: EPL appendix: strategy rules (2/9)

Default: choose the highest model-estimated return (probability × odds − 1). Only bet above the listed threshold.

Paired IDs share their forecast and entry rule but have separately labeled stakes. Fixed 1,000 is 1% of initial capital; a stated cash percentage uses date-start cash. Kelly fractions and caps are distinct. All IDs below are individual preserved strategies; grouping changes no rule. 'Positive return:6/8 models' requires six models to assign positive estimated return to the chosen outcome, not six favorite picks. H=home win, D=draw, A=away win.

S023: Team + chance quality + player form Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 5%. 1,000 per bet: 1% of INITIAL 100,000; the amount stays fixed as cash changes. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Highest archived individual-bookmaker odds for the chosen outcome. With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Example: With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Rolling logistic: combined; max_edge selection among the allowed outcomes at best individual-book quotes. Require selected model expected return strictly above 5%; stake flat 1,000.", "diagnostic": false, "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.05, "min_odds": null, "model_key": "logit_combined", "model_label": "Rolling logistic: combined", "name": "Rolling logistic: combined | predeclared 5% edge | best individual-book quotes | flat 1,000", "odds_mode": "best", "origin": "legacy", "policy_family": "predeclared 5% edge", "selection_rule": "max_edge", "staking": "fixed", "strategy_id": "S023", "study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}

S024: Team + chance quality + player form Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 5%. Quarter Kelly: B × min(2%, 0.25 × max(0, p×O−1)/(O−1)); B = date-start cash. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Highest archived individual-bookmaker odds for the chosen outcome. B=100,000, p=40%, O=3: full Kelly=10%; 0.25 × 10% capped at 2% requests 2,000 before shared date/cash reduction.
Example: B=100,000, p=40%, O=3: full Kelly=10%; 0.25 × 10% capped at 2% requests 2,000 before shared date/cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Rolling logistic: combined; max_edge selection among the allowed outcomes at best individual-book quotes. Require selected model expected return strictly above 5%; stake 0.25 Kelly, per-bet cap 2%.", "diagnostic": false, "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.05, "min_odds": null, "model_key": "logit_combined", "model_label": "Rolling logistic: combined", "name": "Rolling logistic: combined | predeclared 5% edge | best individual-book quotes | 0.25 Kelly, per-bet cap 2%", "odds_mode": "best", "origin": "legacy", "policy_family": "predeclared 5% edge", "selection_rule": "max_edge", "staking": "kelly", "strategy_id": "S024", "study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}

S052: Team + chance quality + player form Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 5%. 1% of cash at the start of that match date per bet. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Highest archived individual-bookmaker odds for the chosen outcome. Cash 100,000 → 1,000 per bet; cash 80,000 → 800 per bet, before shared cash reduction.
Example: Cash 100,000 → 1,000 per bet; cash 80,000 → 800 per bet, before shared cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Rolling logistic: combined; max_edge selection among the allowed outcomes at best individual-book quotes. Require selected model expected return strictly above 5%; stake dynamic 1% of date-start capital.", "diagnostic": false, "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.05, "min_odds": null, "model_key": "logit_combined", "model_label": "Rolling logistic: combined", "name": "Rolling logistic: combined | dynamic 1% stake | best individual-book quotes | dynamic 1% of date-start capital", "odds_mode": "best", "origin": "new", "policy_family": "dynamic 1% stake", "selection_rule": "max_edge", "staking": "dynamic_fraction", "strategy_id": "S052", "study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}

S055: Team + chance quality + player form Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 5%. Eighth Kelly: B × min(1%, 0.125 × max(0, p×O−1)/(O−1)); B = date-start cash. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Highest archived individual-bookmaker odds for the chosen outcome. B=100,000, p=40%, O=3: full Kelly=10%; 0.125 × 10% capped at 1% requests 1,000 before shared date/cash reduction.
Example: B=100,000, p=40%, O=3: full Kelly=10%; 0.125 × 10% capped at 1% requests 1,000 before shared date/cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Rolling logistic: combined; max_edge selection among the allowed outcomes at best individual-book quotes. Require selected model expected return strictly above 5%; stake 0.125 Kelly, per-bet cap 1%.", "diagnostic": false, "fixed_stake": 1000.0, "kelly_fraction": 0.125, "max_bet_fraction": 0.01, "max_odds": null, "min_edge": 0.05, "min_odds": null, "model_key": "logit_combined", "model_label": "Rolling logistic: combined", "name": "Rolling logistic: combined | eighth Kelly, cap 1% | best individual-book quotes | 0.125 Kelly, per-bet cap 1%", "odds_mode": "best", "origin": "new", "policy_family": "eighth Kelly, cap 1%", "selection_rule": "max_edge", "staking": "kelly", "strategy_id": "S055", "study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}

S056: Team + chance quality + player form Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 5%. Half Kelly: B × min(2%, 0.5 × max(0, p×O−1)/(O−1)); B = date-start cash. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Highest archived individual-bookmaker odds for the chosen outcome. B=100,000, p=40%, O=3: full Kelly=10%; 0.5 × 10% capped at 2% requests 2,000 before shared date/cash reduction.
Example: B=100,000, p=40%, O=3: full Kelly=10%; 0.5 × 10% capped at 2% requests 2,000 before shared date/cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Rolling logistic: combined; max_edge selection among the allowed outcomes at best individual-book quotes. Require selected model expected return strictly above 5%; stake 0.5 Kelly, per-bet cap 2%.", "diagnostic": false, "fixed_stake": 1000.0, "kelly_fraction": 0.5, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.05, "min_odds": null, "model_key": "logit_combined", "model_label": "Rolling logistic: combined", "name": "Rolling logistic: combined | half Kelly, cap 2% | best individual-book quotes | 0.5 Kelly, per-bet cap 2%", "odds_mode": "best", "origin": "new", "policy_family": "half Kelly, cap 2%", "selection_rule": "max_edge", "staking": "kelly", "strategy_id": "S056", "study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}

S025: Bookmaker odds + team form Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 5%. 1,000 per bet: 1% of INITIAL 100,000; the amount stays fixed as cash changes. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Highest archived individual-bookmaker odds for the chosen outcome. With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Example: With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Rolling market residual: team; max_edge selection among the allowed outcomes at best individual-book quotes. Require selected model expected return strictly above 5%; stake flat 1,000.", "diagnostic": false, "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.05, "min_odds": null, "model_key": "residual_team_only", "model_label": "Rolling market residual: team", "name": "Rolling market residual: team | predeclared 5% edge | best individual-book quotes | flat 1,000", "odds_mode": "best", "origin": "legacy", "policy_family": "predeclared 5% edge", "selection_rule": "max_edge", "staking": "fixed", "strategy_id": "S025", "study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}

S026: Bookmaker odds + team form Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 5%. Quarter Kelly: B × min(2%, 0.25 × max(0, p×O−1)/(O−1)); B = date-start cash. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Highest archived individual-bookmaker odds for the chosen outcome. B=100,000, p=40%, O=3: full Kelly=10%; 0.25 × 10% capped at 2% requests 2,000 before shared date/cash reduction.
Example: B=100,000, p=40%, O=3: full Kelly=10%; 0.25 × 10% capped at 2% requests 2,000 before shared date/cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Rolling market residual: team; max_edge selection among the allowed outcomes at best individual-book quotes. Require selected model expected return strictly above 5%; stake 0.25 Kelly, per-bet cap 2%.", "diagnostic": false, "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.05, "min_odds": null, "model_key": "residual_team_only", "model_label": "Rolling market residual: team", "name": "Rolling market residual: team | predeclared 5% edge | best individual-book quotes | 0.25 Kelly, per-bet cap 2%", "odds_mode": "best", "origin": "legacy", "policy_family": "predeclared 5% edge", "selection_rule": "max_edge", "staking": "kelly", "strategy_id": "S026", "study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}

S027: Bookmaker odds + team/chance quality Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 5%. 1,000 per bet: 1% of INITIAL 100,000; the amount stays fixed as cash changes. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Highest archived individual-bookmaker odds for the chosen outcome. With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Example: With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Rolling market residual: team + xG; max_edge selection among the allowed outcomes at best individual-book quotes. Require selected model expected return strictly above 5%; stake flat 1,000.", "diagnostic": false, "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.05, "min_odds": null, "model_key": "residual_team_xg", "model_label": "Rolling market residual: team + xG", "name": "Rolling market residual: team + xG | predeclared 5% edge | best individual-book quotes | flat 1,000", "odds_mode": "best", "origin": "legacy", "policy_family": "predeclared 5% edge", "selection_rule": "max_edge", "staking": "fixed", "strategy_id": "S027", "study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}

S028: Bookmaker odds + team/chance quality Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 5%. Quarter Kelly: B × min(2%, 0.25 × max(0, p×O−1)/(O−1)); B = date-start cash. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Highest archived individual-bookmaker odds for the chosen outcome. B=100,000, p=40%, O=3: full Kelly=10%; 0.25 × 10% capped at 2% requests 2,000 before shared date/cash reduction.
Example: B=100,000, p=40%, O=3: full Kelly=10%; 0.25 × 10% capped at 2% requests 2,000 before shared date/cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Rolling market residual: team + xG; max_edge selection among the allowed outcomes at best individual-book quotes. Require selected model expected return strictly above 5%; stake 0.25 Kelly, per-bet cap 2%.", "diagnostic": false, "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.05, "min_odds": null, "model_key": "residual_team_xg", "model_label": "Rolling market residual: team + xG", "name": "Rolling market residual: team + xG | predeclared 5% edge | best individual-book quotes | 0.25 Kelly, per-bet cap 2%", "odds_mode": "best", "origin": "legacy", "policy_family": "predeclared 5% edge", "selection_rule": "max_edge", "staking": "kelly", "strategy_id": "S028", "study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}

S029: Bookmaker odds + team/player form Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 5%. 1,000 per bet: 1% of INITIAL 100,000; the amount stays fixed as cash changes. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Highest archived individual-bookmaker odds for the chosen outcome. With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Example: With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Rolling market residual: team + player; max_edge selection among the allowed outcomes at best individual-book quotes. Require selected model expected return strictly above 5%; stake flat 1,000.", "diagnostic": false, "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.05, "min_odds": null, "model_key": "residual_team_players", "model_label": "Rolling market residual: team + player", "name": "Rolling market residual: team + player | predeclared 5% edge | best individual-book quotes | flat 1,000", "odds_mode": "best", "origin": "legacy", "policy_family": "predeclared 5% edge", "selection_rule": "max_edge", "staking": "fixed", "strategy_id": "S029", "study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}

S030: Bookmaker odds + team/player form Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 5%. Quarter Kelly: B × min(2%, 0.25 × max(0, p×O−1)/(O−1)); B = date-start cash. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Highest archived individual-bookmaker odds for the chosen outcome. B=100,000, p=40%, O=3: full Kelly=10%; 0.25 × 10% capped at 2% requests 2,000 before shared date/cash reduction.
Example: B=100,000, p=40%, O=3: full Kelly=10%; 0.25 × 10% capped at 2% requests 2,000 before shared date/cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Rolling market residual: team + player; max_edge selection among the allowed outcomes at best individual-book quotes. Require selected model expected return strictly above 5%; stake 0.25 Kelly, per-bet cap 2%.", "diagnostic": false, "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.05, "min_odds": null, "model_key": "residual_team_players", "model_label": "Rolling market residual: team + player", "name": "Rolling market residual: team + player | predeclared 5% edge | best individual-book quotes | 0.25 Kelly, per-bet cap 2%", "odds_mode": "best", "origin": "legacy", "policy_family": "predeclared 5% edge", "selection_rule": "max_edge", "staking": "kelly", "strategy_id": "S030", "study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}

S031: Bookmaker odds + team/chance/player form Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 5%. 1,000 per bet: 1% of INITIAL 100,000; the amount stays fixed as cash changes. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Highest archived individual-bookmaker odds for the chosen outcome. With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Example: With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Rolling market residual: combined; max_edge selection among the allowed outcomes at best individual-book quotes. Require selected model expected return strictly above 5%; stake flat 1,000.", "diagnostic": false, "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.05, "min_odds": null, "model_key": "residual_combined", "model_label": "Rolling market residual: combined", "name": "Rolling market residual: combined | predeclared 5% edge | best individual-book quotes | flat 1,000", "odds_mode": "best", "origin": "legacy", "policy_family": "predeclared 5% edge", "selection_rule": "max_edge", "staking": "fixed", "strategy_id": "S031", "study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}

S032: Bookmaker odds + team/chance/player form Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 5%. Quarter Kelly: B × min(2%, 0.25 × max(0, p×O−1)/(O−1)); B = date-start cash. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Highest archived individual-bookmaker odds for the chosen outcome. B=100,000, p=40%, O=3: full Kelly=10%; 0.25 × 10% capped at 2% requests 2,000 before shared date/cash reduction.
Example: B=100,000, p=40%, O=3: full Kelly=10%; 0.25 × 10% capped at 2% requests 2,000 before shared date/cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Rolling market residual: combined; max_edge selection among the allowed outcomes at best individual-book quotes. Require selected model expected return strictly above 5%; stake 0.25 Kelly, per-bet cap 2%.", "diagnostic": false, "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.05, "min_odds": null, "model_key": "residual_combined", "model_label": "Rolling market residual: combined", "name": "Rolling market residual: combined | predeclared 5% edge | best individual-book quotes | 0.25 Kelly, per-bet cap 2%", "odds_mode": "best", "origin": "legacy", "policy_family": "predeclared 5% edge", "selection_rule": "max_edge", "staking": "kelly", "strategy_id": "S032", "study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}

S053: Bookmaker odds + team/chance/player form Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 5%. 1% of cash at the start of that match date per bet. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Highest archived individual-bookmaker odds for the chosen outcome. Cash 100,000 → 1,000 per bet; cash 80,000 → 800 per bet, before shared cash reduction.
Example: Cash 100,000 → 1,000 per bet; cash 80,000 → 800 per bet, before shared cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Rolling market residual: combined; max_edge selection among the allowed outcomes at best individual-book quotes. Require selected model expected return strictly above 5%; stake dynamic 1% of date-start capital.", "diagnostic": false, "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.05, "min_odds": null, "model_key": "residual_combined", "model_label": "Rolling market residual: combined", "name": "Rolling market residual: combined | dynamic 1% stake | best individual-book quotes | dynamic 1% of date-start capital", "odds_mode": "best", "origin": "new", "policy_family": "dynamic 1% stake", "selection_rule": "max_edge", "staking": "dynamic_fraction", "strategy_id": "S053", "study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}

S057: Bookmaker odds + team/chance/player form Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 5%. Eighth Kelly: B × min(1%, 0.125 × max(0, p×O−1)/(O−1)); B = date-start cash. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Highest archived individual-bookmaker odds for the chosen outcome. B=100,000, p=40%, O=3: full Kelly=10%; 0.125 × 10% capped at 1% requests 1,000 before shared date/cash reduction.
Example: B=100,000, p=40%, O=3: full Kelly=10%; 0.125 × 10% capped at 1% requests 1,000 before shared date/cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Rolling market residual: combined; max_edge selection among the allowed outcomes at best individual-book quotes. Require selected model expected return strictly above 5%; stake 0.125 Kelly, per-bet cap 1%.", "diagnostic": false, "fixed_stake": 1000.0, "kelly_fraction": 0.125, "max_bet_fraction": 0.01, "max_odds": null, "min_edge": 0.05, "min_odds": null, "model_key": "residual_combined", "model_label": "Rolling market residual: combined", "name": "Rolling market residual: combined | eighth Kelly, cap 1% | best individual-book quotes | 0.125 Kelly, per-bet cap 1%", "odds_mode": "best", "origin": "new", "policy_family": "eighth Kelly, cap 1%", "selection_rule": "max_edge", "staking": "kelly", "strategy_id": "S057", "study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}

Sources:
- epl_player_models\results\20261020_player_models_review\all_strategy_catalog.json

## Slide 20: EPL appendix: strategy rules (3/9)

Default: choose the highest model-estimated return (probability × odds − 1). Only bet above the listed threshold.

Paired IDs share their forecast and entry rule but have separately labeled stakes. Fixed 1,000 is 1% of initial capital; a stated cash percentage uses date-start cash. Kelly fractions and caps are distinct. All IDs below are individual preserved strategies; grouping changes no rule. 'Positive return:6/8 models' requires six models to assign positive estimated return to the chosen outcome, not six favorite picks. H=home win, D=draw, A=away win.

S058: Bookmaker odds + team/chance/player form Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 5%. Half Kelly: B × min(2%, 0.5 × max(0, p×O−1)/(O−1)); B = date-start cash. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Highest archived individual-bookmaker odds for the chosen outcome. B=100,000, p=40%, O=3: full Kelly=10%; 0.5 × 10% capped at 2% requests 2,000 before shared date/cash reduction.
Example: B=100,000, p=40%, O=3: full Kelly=10%; 0.5 × 10% capped at 2% requests 2,000 before shared date/cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Rolling market residual: combined; max_edge selection among the allowed outcomes at best individual-book quotes. Require selected model expected return strictly above 5%; stake 0.5 Kelly, per-bet cap 2%.", "diagnostic": false, "fixed_stake": 1000.0, "kelly_fraction": 0.5, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.05, "min_odds": null, "model_key": "residual_combined", "model_label": "Rolling market residual: combined", "name": "Rolling market residual: combined | half Kelly, cap 2% | best individual-book quotes | 0.5 Kelly, per-bet cap 2%", "odds_mode": "best", "origin": "new", "policy_family": "half Kelly, cap 2%", "selection_rule": "max_edge", "staking": "kelly", "strategy_id": "S058", "study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}

S033: Past home/draw/away frequencies Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 5%. 1,000 per bet: 1% of INITIAL 100,000; the amount stays fixed as cash changes. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Highest archived individual-bookmaker odds for the chosen outcome. With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Example: With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Rolling training-class frequency; max_edge selection among the allowed outcomes at best individual-book quotes. Require selected model expected return strictly above 5%; stake flat 1,000.", "diagnostic": false, "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.05, "min_odds": null, "model_key": "baseline_class_frequency", "model_label": "Rolling training-class frequency", "name": "Rolling training-class frequency | predeclared 5% edge | best individual-book quotes | flat 1,000", "odds_mode": "best", "origin": "legacy", "policy_family": "predeclared 5% edge", "selection_rule": "max_edge", "staking": "fixed", "strategy_id": "S033", "study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}

S034: Past home/draw/away frequencies Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 5%. Quarter Kelly: B × min(2%, 0.25 × max(0, p×O−1)/(O−1)); B = date-start cash. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Highest archived individual-bookmaker odds for the chosen outcome. B=100,000, p=40%, O=3: full Kelly=10%; 0.25 × 10% capped at 2% requests 2,000 before shared date/cash reduction.
Example: B=100,000, p=40%, O=3: full Kelly=10%; 0.25 × 10% capped at 2% requests 2,000 before shared date/cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Rolling training-class frequency; max_edge selection among the allowed outcomes at best individual-book quotes. Require selected model expected return strictly above 5%; stake 0.25 Kelly, per-bet cap 2%.", "diagnostic": false, "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.05, "min_odds": null, "model_key": "baseline_class_frequency", "model_label": "Rolling training-class frequency", "name": "Rolling training-class frequency | predeclared 5% edge | best individual-book quotes | 0.25 Kelly, per-bet cap 2%", "odds_mode": "best", "origin": "legacy", "policy_family": "predeclared 5% edge", "selection_rule": "max_edge", "staking": "kelly", "strategy_id": "S034", "study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}

S035: Bookmaker probabilities Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 5%. 1,000 per bet: 1% of INITIAL 100,000; the amount stays fixed as cash changes. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Highest archived individual-bookmaker odds for the chosen outcome. With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Example: With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Raw de-vigged Bet365 market; max_edge selection among the allowed outcomes at best individual-book quotes. Require selected model expected return strictly above 5%; stake flat 1,000.", "diagnostic": false, "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.05, "min_odds": null, "model_key": "baseline_market_only", "model_label": "Raw de-vigged Bet365 market", "name": "Raw de-vigged Bet365 market | predeclared 5% edge | best individual-book quotes | flat 1,000", "odds_mode": "best", "origin": "legacy", "policy_family": "predeclared 5% edge", "selection_rule": "max_edge", "staking": "fixed", "strategy_id": "S035", "study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}

S036: Bookmaker probabilities Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 5%. Quarter Kelly: B × min(2%, 0.25 × max(0, p×O−1)/(O−1)); B = date-start cash. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Highest archived individual-bookmaker odds for the chosen outcome. B=100,000, p=40%, O=3: full Kelly=10%; 0.25 × 10% capped at 2% requests 2,000 before shared date/cash reduction.
Example: B=100,000, p=40%, O=3: full Kelly=10%; 0.25 × 10% capped at 2% requests 2,000 before shared date/cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Raw de-vigged Bet365 market; max_edge selection among the allowed outcomes at best individual-book quotes. Require selected model expected return strictly above 5%; stake 0.25 Kelly, per-bet cap 2%.", "diagnostic": false, "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.05, "min_odds": null, "model_key": "baseline_market_only", "model_label": "Raw de-vigged Bet365 market", "name": "Raw de-vigged Bet365 market | predeclared 5% edge | best individual-book quotes | 0.25 Kelly, per-bet cap 2%", "odds_mode": "best", "origin": "legacy", "policy_family": "predeclared 5% edge", "selection_rule": "max_edge", "staking": "kelly", "strategy_id": "S036", "study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}

S037: Calibrated bookmaker probabilities Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 5%. 1,000 per bet: 1% of INITIAL 100,000; the amount stays fixed as cash changes. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Highest archived individual-bookmaker odds for the chosen outcome. With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Example: With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Temperature-calibrated Bet365 market; max_edge selection among the allowed outcomes at best individual-book quotes. Require selected model expected return strictly above 5%; stake flat 1,000.", "diagnostic": false, "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.05, "min_odds": null, "model_key": "market_temperature", "model_label": "Temperature-calibrated Bet365 market", "name": "Temperature-calibrated Bet365 market | predeclared 5% edge | best individual-book quotes | flat 1,000", "odds_mode": "best", "origin": "legacy", "policy_family": "predeclared 5% edge", "selection_rule": "max_edge", "staking": "fixed", "strategy_id": "S037", "study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}

S038: Calibrated bookmaker probabilities Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 5%. Quarter Kelly: B × min(2%, 0.25 × max(0, p×O−1)/(O−1)); B = date-start cash. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Highest archived individual-bookmaker odds for the chosen outcome. B=100,000, p=40%, O=3: full Kelly=10%; 0.25 × 10% capped at 2% requests 2,000 before shared date/cash reduction.
Example: B=100,000, p=40%, O=3: full Kelly=10%; 0.25 × 10% capped at 2% requests 2,000 before shared date/cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Temperature-calibrated Bet365 market; max_edge selection among the allowed outcomes at best individual-book quotes. Require selected model expected return strictly above 5%; stake 0.25 Kelly, per-bet cap 2%.", "diagnostic": false, "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.05, "min_odds": null, "model_key": "market_temperature", "model_label": "Temperature-calibrated Bet365 market", "name": "Temperature-calibrated Bet365 market | predeclared 5% edge | best individual-book quotes | 0.25 Kelly, per-bet cap 2%", "odds_mode": "best", "origin": "legacy", "policy_family": "predeclared 5% edge", "selection_rule": "max_edge", "staking": "kelly", "strategy_id": "S038", "study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}

S039: Bookmaker probabilities Bet on home win in every priced match; no return filter. 1,000 per bet: 1% of INITIAL 100,000; the amount stays fixed as cash changes. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Highest archived individual-bookmaker odds for the chosen outcome. With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Example: With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle", "allowed_outcomes": ["H"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Back H on every priced fixture at its best archived individual-book quote, with flat stake 1,000 and no edge filter; market probability is descriptive only.", "diagnostic": false, "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": null, "min_odds": null, "model_key": "baseline_market_only", "model_label": "Raw de-vigged Bet365 market", "name": "Always H | best quotes | flat 1,000", "odds_mode": "best", "origin": "new", "policy_family": "unconditional class benchmark", "selection_rule": "fixed_outcome", "staking": "fixed", "strategy_id": "S039", "study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}

S040: Bookmaker probabilities Bet on draw in every priced match; no return filter. 1,000 per bet: 1% of INITIAL 100,000; the amount stays fixed as cash changes. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Highest archived individual-bookmaker odds for the chosen outcome. With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Example: With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle", "allowed_outcomes": ["D"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Back D on every priced fixture at its best archived individual-book quote, with flat stake 1,000 and no edge filter; market probability is descriptive only.", "diagnostic": false, "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": null, "min_odds": null, "model_key": "baseline_market_only", "model_label": "Raw de-vigged Bet365 market", "name": "Always D | best quotes | flat 1,000", "odds_mode": "best", "origin": "new", "policy_family": "unconditional class benchmark", "selection_rule": "fixed_outcome", "staking": "fixed", "strategy_id": "S040", "study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}

S041: Bookmaker probabilities Bet on away win in every priced match; no return filter. 1,000 per bet: 1% of INITIAL 100,000; the amount stays fixed as cash changes. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Highest archived individual-bookmaker odds for the chosen outcome. With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Example: With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle", "allowed_outcomes": ["A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Back A on every priced fixture at its best archived individual-book quote, with flat stake 1,000 and no edge filter; market probability is descriptive only.", "diagnostic": false, "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": null, "min_odds": null, "model_key": "baseline_market_only", "model_label": "Raw de-vigged Bet365 market", "name": "Always A | best quotes | flat 1,000", "odds_mode": "best", "origin": "new", "policy_family": "unconditional class benchmark", "selection_rule": "fixed_outcome", "staking": "fixed", "strategy_id": "S041", "study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}

S042: Bookmaker probabilities Back the home/draw/away result with the highest bookmaker probability; no return filter. 1,000 per bet: 1% of INITIAL 100,000; the amount stays fixed as cash changes. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Highest archived individual-bookmaker odds for the chosen outcome. With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Example: With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Choose the highest raw de-vigged Bet365 probability, then use that outcome's best archived quote and flat stake 1,000; no edge filter.", "diagnostic": false, "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": null, "min_odds": null, "model_key": "baseline_market_only", "model_label": "Raw de-vigged Bet365 market", "name": "Market favorite | best quotes | flat 1,000", "odds_mode": "best", "origin": "new", "policy_family": "unconditional market benchmark", "selection_rule": "market_favorite", "staking": "fixed", "strategy_id": "S042", "study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}

Sources:
- epl_player_models\results\20261020_player_models_review\all_strategy_catalog.json

## Slide 21: EPL appendix: strategy rules (4/9)

Default: choose the highest model-estimated return (probability × odds − 1). Only bet above the listed threshold.

Paired IDs share their forecast and entry rule but have separately labeled stakes. Fixed 1,000 is 1% of initial capital; a stated cash percentage uses date-start cash. Kelly fractions and caps are distinct. All IDs below are individual preserved strategies; grouping changes no rule. 'Positive return:6/8 models' requires six models to assign positive estimated return to the chosen outcome, not six favorite picks. H=home win, D=draw, A=away win.

S043: Bookmaker probabilities Back the home/draw/away result with the lowest bookmaker probability; no return filter. 1,000 per bet: 1% of INITIAL 100,000; the amount stays fixed as cash changes. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Highest archived individual-bookmaker odds for the chosen outcome. With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Example: With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Choose the lowest raw de-vigged Bet365 probability, then use that outcome's best archived quote and flat stake 1,000; no edge filter.", "diagnostic": false, "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": null, "min_odds": null, "model_key": "baseline_market_only", "model_label": "Raw de-vigged Bet365 market", "name": "Market underdog | best quotes | flat 1,000", "odds_mode": "best", "origin": "new", "policy_family": "unconditional market benchmark", "selection_rule": "market_underdog", "staking": "fixed", "strategy_id": "S043", "study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}

S044: Team + chance quality + player form Back the home/draw/away result with the highest model probability; no return filter. 1,000 per bet: 1% of INITIAL 100,000; the amount stays fixed as cash changes. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Highest archived individual-bookmaker odds for the chosen outcome. With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Example: With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Choose Rolling logistic: combined's highest-probability outcome at its best archived quote; flat stake 1,000 with no edge filter.", "diagnostic": false, "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": null, "min_odds": null, "model_key": "logit_combined", "model_label": "Rolling logistic: combined", "name": "Rolling logistic: combined | unconditional model favorite | best individual-book quotes | flat 1,000", "odds_mode": "best", "origin": "new", "policy_family": "unconditional model favorite", "selection_rule": "model_favorite", "staking": "fixed", "strategy_id": "S044", "study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}

S045: Bookmaker odds + team/chance/player form Back the home/draw/away result with the highest model probability; no return filter. 1,000 per bet: 1% of INITIAL 100,000; the amount stays fixed as cash changes. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Highest archived individual-bookmaker odds for the chosen outcome. With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Example: With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Choose Rolling market residual: combined's highest-probability outcome at its best archived quote; flat stake 1,000 with no edge filter.", "diagnostic": false, "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": null, "min_odds": null, "model_key": "residual_combined", "model_label": "Rolling market residual: combined", "name": "Rolling market residual: combined | unconditional model favorite | best individual-book quotes | flat 1,000", "odds_mode": "best", "origin": "new", "policy_family": "unconditional model favorite", "selection_rule": "model_favorite", "staking": "fixed", "strategy_id": "S045", "study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}

S046: Average of four team/player forecasts Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 5%. 1,000 per bet: 1% of INITIAL 100,000; the amount stays fixed as cash changes. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Highest archived individual-bookmaker odds for the chosen outcome. With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Example: With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Equal-weight mean of four rolling logistic probabilities; max_edge selection among the allowed outcomes at best individual-book quotes. Require selected model expected return strictly above 5%; stake flat 1,000.", "diagnostic": false, "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.05, "min_odds": null, "model_key": "ensemble_logit4", "model_label": "Equal-weight mean of four rolling logistic probabilities", "name": "Equal-weight mean of four rolling logistic probabilities | ensemble 5% edge | best individual-book quotes | flat 1,000", "odds_mode": "best", "origin": "new", "policy_family": "ensemble 5% edge", "selection_rule": "max_edge", "staking": "fixed", "strategy_id": "S046", "study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}

S047: Average of four team/player forecasts Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 5%. Quarter Kelly: B × min(2%, 0.25 × max(0, p×O−1)/(O−1)); B = date-start cash. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Highest archived individual-bookmaker odds for the chosen outcome. B=100,000, p=40%, O=3: full Kelly=10%; 0.25 × 10% capped at 2% requests 2,000 before shared date/cash reduction.
Example: B=100,000, p=40%, O=3: full Kelly=10%; 0.25 × 10% capped at 2% requests 2,000 before shared date/cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Equal-weight mean of four rolling logistic probabilities; max_edge selection among the allowed outcomes at best individual-book quotes. Require selected model expected return strictly above 5%; stake 0.25 Kelly, per-bet cap 2%.", "diagnostic": false, "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.05, "min_odds": null, "model_key": "ensemble_logit4", "model_label": "Equal-weight mean of four rolling logistic probabilities", "name": "Equal-weight mean of four rolling logistic probabilities | ensemble 5% edge | best individual-book quotes | 0.25 Kelly, per-bet cap 2%", "odds_mode": "best", "origin": "new", "policy_family": "ensemble 5% edge", "selection_rule": "max_edge", "staking": "kelly", "strategy_id": "S047", "study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}

S048: Average of eight learned forecasts Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 5%. 1,000 per bet: 1% of INITIAL 100,000; the amount stays fixed as cash changes. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Highest archived individual-bookmaker odds for the chosen outcome. With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Example: With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Equal-weight mean of all eight rolling learned probabilities; max_edge selection among the allowed outcomes at best individual-book quotes. Require selected model expected return strictly above 5%; stake flat 1,000.", "diagnostic": false, "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.05, "min_odds": null, "model_key": "ensemble_learned8", "model_label": "Equal-weight mean of all eight rolling learned probabilities", "name": "Equal-weight mean of all eight rolling learned probabilities | ensemble 5% edge | best individual-book quotes | flat 1,000", "odds_mode": "best", "origin": "new", "policy_family": "ensemble 5% edge", "selection_rule": "max_edge", "staking": "fixed", "strategy_id": "S048", "study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}

S049: Average of eight learned forecasts Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 5%. Quarter Kelly: B × min(2%, 0.25 × max(0, p×O−1)/(O−1)); B = date-start cash. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Highest archived individual-bookmaker odds for the chosen outcome. B=100,000, p=40%, O=3: full Kelly=10%; 0.25 × 10% capped at 2% requests 2,000 before shared date/cash reduction.
Example: B=100,000, p=40%, O=3: full Kelly=10%; 0.25 × 10% capped at 2% requests 2,000 before shared date/cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Equal-weight mean of all eight rolling learned probabilities; max_edge selection among the allowed outcomes at best individual-book quotes. Require selected model expected return strictly above 5%; stake 0.25 Kelly, per-bet cap 2%.", "diagnostic": false, "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.05, "min_odds": null, "model_key": "ensemble_learned8", "model_label": "Equal-weight mean of all eight rolling learned probabilities", "name": "Equal-weight mean of all eight rolling learned probabilities | ensemble 5% edge | best individual-book quotes | 0.25 Kelly, per-bet cap 2%", "odds_mode": "best", "origin": "new", "policy_family": "ensemble 5% edge", "selection_rule": "max_edge", "staking": "kelly", "strategy_id": "S049", "study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}

S054: Average of eight learned forecasts Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 5%. 1% of cash at the start of that match date per bet. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Highest archived individual-bookmaker odds for the chosen outcome. Cash 100,000 → 1,000 per bet; cash 80,000 → 800 per bet, before shared cash reduction.
Example: Cash 100,000 → 1,000 per bet; cash 80,000 → 800 per bet, before shared cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Equal-weight mean of all eight rolling learned probabilities; max_edge selection among the allowed outcomes at best individual-book quotes. Require selected model expected return strictly above 5%; stake dynamic 1% of date-start capital.", "diagnostic": false, "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.05, "min_odds": null, "model_key": "ensemble_learned8", "model_label": "Equal-weight mean of all eight rolling learned probabilities", "name": "Equal-weight mean of all eight rolling learned probabilities | dynamic 1% stake | best individual-book quotes | dynamic 1% of date-start capital", "odds_mode": "best", "origin": "new", "policy_family": "dynamic 1% stake", "selection_rule": "max_edge", "staking": "dynamic_fraction", "strategy_id": "S054", "study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}

S050: Half combined forecast, half bookmaker Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 5%. 1,000 per bet: 1% of INITIAL 100,000; the amount stays fixed as cash changes. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Highest archived individual-bookmaker odds for the chosen outcome. With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Example: With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "50/50 combined logistic and raw de-vigged market probabilities; max_edge selection among the allowed outcomes at best individual-book quotes. Require selected model expected return strictly above 5%; stake flat 1,000.", "diagnostic": false, "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.05, "min_odds": null, "model_key": "ensemble_market_blend", "model_label": "50/50 combined logistic and raw de-vigged market probabilities", "name": "50/50 combined logistic and raw de-vigged market probabilities | ensemble 5% edge | best individual-book quotes | flat 1,000", "odds_mode": "best", "origin": "new", "policy_family": "ensemble 5% edge", "selection_rule": "max_edge", "staking": "fixed", "strategy_id": "S050", "study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}

S051: Half combined forecast, half bookmaker Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 5%. Quarter Kelly: B × min(2%, 0.25 × max(0, p×O−1)/(O−1)); B = date-start cash. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Highest archived individual-bookmaker odds for the chosen outcome. B=100,000, p=40%, O=3: full Kelly=10%; 0.25 × 10% capped at 2% requests 2,000 before shared date/cash reduction.
Example: B=100,000, p=40%, O=3: full Kelly=10%; 0.25 × 10% capped at 2% requests 2,000 before shared date/cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "50/50 combined logistic and raw de-vigged market probabilities; max_edge selection among the allowed outcomes at best individual-book quotes. Require selected model expected return strictly above 5%; stake 0.25 Kelly, per-bet cap 2%.", "diagnostic": false, "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.05, "min_odds": null, "model_key": "ensemble_market_blend", "model_label": "50/50 combined logistic and raw de-vigged market probabilities", "name": "50/50 combined logistic and raw de-vigged market probabilities | ensemble 5% edge | best individual-book quotes | 0.25 Kelly, per-bet cap 2%", "odds_mode": "best", "origin": "new", "policy_family": "ensemble 5% edge", "selection_rule": "max_edge", "staking": "kelly", "strategy_id": "S051", "study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}

S059: Team + chance quality + player form Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 5%. Quarter Kelly: B × min(2%, 0.25 × max(0, p×O−1)/(O−1)); B = date-start cash. All bets on one date together use at most 10% of date-start cash; shrink every request by the same proportion if necessary. At most one bet per match; no borrowing or use of same-date winnings. Highest archived individual-bookmaker odds for the chosen outcome. B=100,000, p=40%, O=3: full Kelly=10%; 0.25 × 10% capped at 2% requests 2,000 before shared date/cash reduction.
Example: B=100,000, p=40%, O=3: full Kelly=10%; 0.25 × 10% capped at 2% requests 2,000 before shared date/cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": 0.1, "description": "Select Rolling logistic: combined's maximum edge strictly above 5%. Use quarter Kelly capped at 2% per bet, then uniformly scale all same-date requests to at most 10% of date-start capital.", "diagnostic": false, "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.05, "min_odds": null, "model_key": "logit_combined", "model_label": "Rolling logistic: combined", "name": "Rolling logistic: combined | quarter Kelly, 10% date budget | best individual-book quotes | 0.25 Kelly, per-bet cap 2%", "odds_mode": "best", "origin": "new", "policy_family": "quarter Kelly, 10% date budget", "selection_rule": "max_edge", "staking": "kelly", "strategy_id": "S059", "study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}

Sources:
- epl_player_models\results\20261020_player_models_review\all_strategy_catalog.json

## Slide 22: EPL appendix: strategy rules (5/9)

Default: choose the highest model-estimated return (probability × odds − 1). Only bet above the listed threshold.

Paired IDs share their forecast and entry rule but have separately labeled stakes. Fixed 1,000 is 1% of initial capital; a stated cash percentage uses date-start cash. Kelly fractions and caps are distinct. All IDs below are individual preserved strategies; grouping changes no rule. 'Positive return:6/8 models' requires six models to assign positive estimated return to the chosen outcome, not six favorite picks. H=home win, D=draw, A=away win.

S060: Bookmaker odds + team/chance/player form Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 5%. Quarter Kelly: B × min(2%, 0.25 × max(0, p×O−1)/(O−1)); B = date-start cash. All bets on one date together use at most 10% of date-start cash; shrink every request by the same proportion if necessary. At most one bet per match; no borrowing or use of same-date winnings. Highest archived individual-bookmaker odds for the chosen outcome. B=100,000, p=40%, O=3: full Kelly=10%; 0.25 × 10% capped at 2% requests 2,000 before shared date/cash reduction.
Example: B=100,000, p=40%, O=3: full Kelly=10%; 0.25 × 10% capped at 2% requests 2,000 before shared date/cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": 0.1, "description": "Select Rolling market residual: combined's maximum edge strictly above 5%. Use quarter Kelly capped at 2% per bet, then uniformly scale all same-date requests to at most 10% of date-start capital.", "diagnostic": false, "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.05, "min_odds": null, "model_key": "residual_combined", "model_label": "Rolling market residual: combined", "name": "Rolling market residual: combined | quarter Kelly, 10% date budget | best individual-book quotes | 0.25 Kelly, per-bet cap 2%", "odds_mode": "best", "origin": "new", "policy_family": "quarter Kelly, 10% date budget", "selection_rule": "max_edge", "staking": "kelly", "strategy_id": "S060", "study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}

S061: Average of eight learned forecasts Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 5%. Quarter Kelly: B × min(2%, 0.25 × max(0, p×O−1)/(O−1)); B = date-start cash. All bets on one date together use at most 10% of date-start cash; shrink every request by the same proportion if necessary. At most one bet per match; no borrowing or use of same-date winnings. Highest archived individual-bookmaker odds for the chosen outcome. B=100,000, p=40%, O=3: full Kelly=10%; 0.25 × 10% capped at 2% requests 2,000 before shared date/cash reduction.
Example: B=100,000, p=40%, O=3: full Kelly=10%; 0.25 × 10% capped at 2% requests 2,000 before shared date/cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": 0.1, "description": "Select Equal-weight mean of all eight rolling learned probabilities's maximum edge strictly above 5%. Use quarter Kelly capped at 2% per bet, then uniformly scale all same-date requests to at most 10% of date-start capital.", "diagnostic": false, "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.05, "min_odds": null, "model_key": "ensemble_learned8", "model_label": "Equal-weight mean of all eight rolling learned probabilities", "name": "Equal-weight mean of all eight rolling learned probabilities | quarter Kelly, 10% date budget | best individual-book quotes | 0.25 Kelly, per-bet cap 2%", "odds_mode": "best", "origin": "new", "policy_family": "quarter Kelly, 10% date budget", "selection_rule": "max_edge", "staking": "kelly", "strategy_id": "S061", "study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}

S062: Average of eight learned forecasts Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 5%. 1,000 per bet: 1% of INITIAL 100,000; the amount stays fixed as cash changes. Then require at least 6 of 8 models to give the chosen outcome a positive estimated return at these odds. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Highest archived individual-bookmaker odds for the chosen outcome. With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Example: With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": 6, "consensus_model_keys": ["logit_team_only", "logit_team_xg", "logit_team_players", "logit_combined", "residual_team_only", "residual_team_xg", "residual_team_players", "residual_combined"], "date_cap_fraction": null, "description": "Choose the mean-eight maximum-edge outcome strictly above 5%; retain it only if at least six of the eight individual rolling learned models have strictly positive edge at that same selected best quote. A failed vote means no bet, without searching another class.", "diagnostic": false, "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.05, "min_odds": null, "model_key": "ensemble_learned8", "model_label": "Equal-weight mean of all eight rolling learned probabilities", "name": "Equal-weight mean of all eight rolling learned probabilities | six-of-eight consensus | best individual-book quotes | flat 1,000", "odds_mode": "best", "origin": "new", "policy_family": "six-of-eight consensus", "selection_rule": "max_edge", "staking": "fixed", "strategy_id": "S062", "study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}

S063: Average of eight learned forecasts Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 5%. Quarter Kelly: B × min(2%, 0.25 × max(0, p×O−1)/(O−1)); B = date-start cash. Then require at least 6 of 8 models to give the chosen outcome a positive estimated return at these odds. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Highest archived individual-bookmaker odds for the chosen outcome. B=100,000, p=40%, O=3: full Kelly=10%; 0.25 × 10% capped at 2% requests 2,000 before shared date/cash reduction.
Example: B=100,000, p=40%, O=3: full Kelly=10%; 0.25 × 10% capped at 2% requests 2,000 before shared date/cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": 6, "consensus_model_keys": ["logit_team_only", "logit_team_xg", "logit_team_players", "logit_combined", "residual_team_only", "residual_team_xg", "residual_team_players", "residual_combined"], "date_cap_fraction": null, "description": "Choose the mean-eight maximum-edge outcome strictly above 5%; retain it only if at least six of the eight individual rolling learned models have strictly positive edge at that same selected best quote. A failed vote means no bet, without searching another class.", "diagnostic": false, "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.05, "min_odds": null, "model_key": "ensemble_learned8", "model_label": "Equal-weight mean of all eight rolling learned probabilities", "name": "Equal-weight mean of all eight rolling learned probabilities | six-of-eight consensus | best individual-book quotes | 0.25 Kelly, per-bet cap 2%", "odds_mode": "best", "origin": "new", "policy_family": "six-of-eight consensus", "selection_rule": "max_edge", "staking": "kelly", "strategy_id": "S063", "study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}

S064: Average of eight learned forecasts Among home win, pick the largest estimated return p×O−1; bet only above 5%. 1,000 per bet: 1% of INITIAL 100,000; the amount stays fixed as cash changes. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Highest archived individual-bookmaker odds for the chosen outcome. With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Example: With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle", "allowed_outcomes": ["H"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Restrict candidates to outcome H before maximizing mean-eight edge; require strict edge above 5% and use flat stake 1,000 at its best archived quote.", "diagnostic": false, "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.05, "min_odds": null, "model_key": "ensemble_learned8", "model_label": "Equal-weight mean of all eight rolling learned probabilities", "name": "Equal-weight mean of all eight rolling learned probabilities | 5% edge, H only | best individual-book quotes | flat 1,000", "odds_mode": "best", "origin": "new", "policy_family": "5% edge, H only", "selection_rule": "max_edge", "staking": "fixed", "strategy_id": "S064", "study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}

S065: Average of eight learned forecasts Among draw, pick the largest estimated return p×O−1; bet only above 5%. 1,000 per bet: 1% of INITIAL 100,000; the amount stays fixed as cash changes. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Highest archived individual-bookmaker odds for the chosen outcome. With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Example: With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle", "allowed_outcomes": ["D"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Restrict candidates to outcome D before maximizing mean-eight edge; require strict edge above 5% and use flat stake 1,000 at its best archived quote.", "diagnostic": false, "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.05, "min_odds": null, "model_key": "ensemble_learned8", "model_label": "Equal-weight mean of all eight rolling learned probabilities", "name": "Equal-weight mean of all eight rolling learned probabilities | 5% edge, D only | best individual-book quotes | flat 1,000", "odds_mode": "best", "origin": "new", "policy_family": "5% edge, D only", "selection_rule": "max_edge", "staking": "fixed", "strategy_id": "S065", "study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}

S066: Average of eight learned forecasts Among away win, pick the largest estimated return p×O−1; bet only above 5%. 1,000 per bet: 1% of INITIAL 100,000; the amount stays fixed as cash changes. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Highest archived individual-bookmaker odds for the chosen outcome. With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Example: With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle", "allowed_outcomes": ["A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Restrict candidates to outcome A before maximizing mean-eight edge; require strict edge above 5% and use flat stake 1,000 at its best archived quote.", "diagnostic": false, "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.05, "min_odds": null, "model_key": "ensemble_learned8", "model_label": "Equal-weight mean of all eight rolling learned probabilities", "name": "Equal-weight mean of all eight rolling learned probabilities | 5% edge, A only | best individual-book quotes | flat 1,000", "odds_mode": "best", "origin": "new", "policy_family": "5% edge, A only", "selection_rule": "max_edge", "staking": "fixed", "strategy_id": "S066", "study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}

S067: Team + chance quality + player form Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 10%. 1,000 per bet: 1% of INITIAL 100,000; the amount stays fixed as cash changes. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Highest archived individual-bookmaker odds for the chosen outcome. With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Example: With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Rolling logistic: combined; max_edge selection among the allowed outcomes at best individual-book quotes. Require selected model expected return strictly above 10%; stake flat 1,000.", "diagnostic": false, "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.1, "min_odds": null, "model_key": "logit_combined", "model_label": "Rolling logistic: combined", "name": "Rolling logistic: combined | 10% edge | best individual-book quotes | flat 1,000", "odds_mode": "best", "origin": "new", "policy_family": "10% edge", "selection_rule": "max_edge", "staking": "fixed", "strategy_id": "S067", "study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}

S068: Bookmaker odds + team/chance/player form Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 10%. 1,000 per bet: 1% of INITIAL 100,000; the amount stays fixed as cash changes. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Highest archived individual-bookmaker odds for the chosen outcome. With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Example: With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Rolling market residual: combined; max_edge selection among the allowed outcomes at best individual-book quotes. Require selected model expected return strictly above 10%; stake flat 1,000.", "diagnostic": false, "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.1, "min_odds": null, "model_key": "residual_combined", "model_label": "Rolling market residual: combined", "name": "Rolling market residual: combined | 10% edge | best individual-book quotes | flat 1,000", "odds_mode": "best", "origin": "new", "policy_family": "10% edge", "selection_rule": "max_edge", "staking": "fixed", "strategy_id": "S068", "study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}

Sources:
- epl_player_models\results\20261020_player_models_review\all_strategy_catalog.json

## Slide 23: EPL appendix: strategy rules (6/9)

Default: choose the highest model-estimated return (probability × odds − 1). Only bet above the listed threshold.

Paired IDs share their forecast and entry rule but have separately labeled stakes. Fixed 1,000 is 1% of initial capital; a stated cash percentage uses date-start cash. Kelly fractions and caps are distinct. All IDs below are individual preserved strategies; grouping changes no rule. 'Positive return:6/8 models' requires six models to assign positive estimated return to the chosen outcome, not six favorite picks. H=home win, D=draw, A=away win.

S069: Average of eight learned forecasts Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 10%. 1,000 per bet: 1% of INITIAL 100,000; the amount stays fixed as cash changes. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Highest archived individual-bookmaker odds for the chosen outcome. With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Example: With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Equal-weight mean of all eight rolling learned probabilities; max_edge selection among the allowed outcomes at best individual-book quotes. Require selected model expected return strictly above 10%; stake flat 1,000.", "diagnostic": false, "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.1, "min_odds": null, "model_key": "ensemble_learned8", "model_label": "Equal-weight mean of all eight rolling learned probabilities", "name": "Equal-weight mean of all eight rolling learned probabilities | 10% edge | best individual-book quotes | flat 1,000", "odds_mode": "best", "origin": "new", "policy_family": "10% edge", "selection_rule": "max_edge", "staking": "fixed", "strategy_id": "S069", "study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}

S070: Team + chance quality + player form Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 5%. 1,000 per bet: 1% of INITIAL 100,000; the amount stays fixed as cash changes. First keep decimal odds from 1.5 to 5, inclusive. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Highest archived individual-bookmaker odds for the chosen outcome. With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Example: With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Retain only outcomes with inclusive best-quote decimal odds from 1.5 to 5 before maximizing Rolling logistic: combined's edge. Require selected edge strictly above 5%; flat stake 1,000.", "diagnostic": false, "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": 5.0, "min_edge": 0.05, "min_odds": 1.5, "model_key": "logit_combined", "model_label": "Rolling logistic: combined", "name": "Rolling logistic: combined | 5% edge, odds 1.5–5 | best individual-book quotes | flat 1,000", "odds_mode": "best", "origin": "new", "policy_family": "5% edge, odds 1.5–5", "selection_rule": "max_edge", "staking": "fixed", "strategy_id": "S070", "study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}

S071: Bookmaker odds + team/chance/player form Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 5%. 1,000 per bet: 1% of INITIAL 100,000; the amount stays fixed as cash changes. First keep decimal odds from 1.5 to 5, inclusive. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Highest archived individual-bookmaker odds for the chosen outcome. With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Example: With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Retain only outcomes with inclusive best-quote decimal odds from 1.5 to 5 before maximizing Rolling market residual: combined's edge. Require selected edge strictly above 5%; flat stake 1,000.", "diagnostic": false, "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": 5.0, "min_edge": 0.05, "min_odds": 1.5, "model_key": "residual_combined", "model_label": "Rolling market residual: combined", "name": "Rolling market residual: combined | 5% edge, odds 1.5–5 | best individual-book quotes | flat 1,000", "odds_mode": "best", "origin": "new", "policy_family": "5% edge, odds 1.5–5", "selection_rule": "max_edge", "staking": "fixed", "strategy_id": "S071", "study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}

S072: Average of eight learned forecasts Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 5%. 1,000 per bet: 1% of INITIAL 100,000; the amount stays fixed as cash changes. First keep decimal odds from 1.5 to 5, inclusive. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Highest archived individual-bookmaker odds for the chosen outcome. With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Example: With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Retain only outcomes with inclusive best-quote decimal odds from 1.5 to 5 before maximizing Equal-weight mean of all eight rolling learned probabilities's edge. Require selected edge strictly above 5%; flat stake 1,000.", "diagnostic": false, "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": 5.0, "min_edge": 0.05, "min_odds": 1.5, "model_key": "ensemble_learned8", "model_label": "Equal-weight mean of all eight rolling learned probabilities", "name": "Equal-weight mean of all eight rolling learned probabilities | 5% edge, odds 1.5–5 | best individual-book quotes | flat 1,000", "odds_mode": "best", "origin": "new", "policy_family": "5% edge, odds 1.5–5", "selection_rule": "max_edge", "staking": "fixed", "strategy_id": "S072", "study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}

S073: Original SVM forecast Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 0%. 1,000 per bet: 1% of INITIAL 100,000; the amount stays fixed as cash changes. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Highest archived individual-bookmaker odds for the chosen outcome. With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Example: With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Replay the saved First-study accuracy-selected SVM validation-candidate rule with edge strictly above 0% (p × odds − 1 > 0), best individual-book quotes and flat stake 1,000. This is an exploratory diagnostic replay on an already examined season, not the selected primary strategy.", "diagnostic": true, "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.0, "min_odds": null, "model_key": "first_accuracy", "model_label": "First-study accuracy-selected SVM", "name": "First-study accuracy-selected SVM | historical threshold diagnostic 0% | best individual-book quotes | flat 1,000", "odds_mode": "best", "origin": "legacy_diagnostic", "policy_family": "historical threshold diagnostic 0%", "selection_rule": "max_edge", "staking": "fixed", "strategy_id": "S073", "study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}

S074: Original SVM forecast Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 2.5%. 1,000 per bet: 1% of INITIAL 100,000; the amount stays fixed as cash changes. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Highest archived individual-bookmaker odds for the chosen outcome. With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Example: With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Replay the saved First-study accuracy-selected SVM validation-candidate rule with edge strictly above 2.5% (p × odds − 1 > 0.025), best individual-book quotes and flat stake 1,000. This is an exploratory diagnostic replay on an already examined season, not the selected primary strategy.", "diagnostic": true, "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.025, "min_odds": null, "model_key": "first_accuracy", "model_label": "First-study accuracy-selected SVM", "name": "First-study accuracy-selected SVM | historical threshold diagnostic 2.5% | best individual-book quotes | flat 1,000", "odds_mode": "best", "origin": "legacy_diagnostic", "policy_family": "historical threshold diagnostic 2.5%", "selection_rule": "max_edge", "staking": "fixed", "strategy_id": "S074", "study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}

S075: Original SVM forecast Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 7.5%. 1,000 per bet: 1% of INITIAL 100,000; the amount stays fixed as cash changes. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Highest archived individual-bookmaker odds for the chosen outcome. With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Example: With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Replay the saved First-study accuracy-selected SVM validation-candidate rule with edge strictly above 7.5% (p × odds − 1 > 0.075), best individual-book quotes and flat stake 1,000. This is an exploratory diagnostic replay on an already examined season, not the selected primary strategy.", "diagnostic": true, "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.075, "min_odds": null, "model_key": "first_accuracy", "model_label": "First-study accuracy-selected SVM", "name": "First-study accuracy-selected SVM | historical threshold diagnostic 7.5% | best individual-book quotes | flat 1,000", "odds_mode": "best", "origin": "legacy_diagnostic", "policy_family": "historical threshold diagnostic 7.5%", "selection_rule": "max_edge", "staking": "fixed", "strategy_id": "S075", "study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}

S076: Original SVM forecast Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 10%. 1,000 per bet: 1% of INITIAL 100,000; the amount stays fixed as cash changes. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Highest archived individual-bookmaker odds for the chosen outcome. With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Example: With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Replay the saved First-study accuracy-selected SVM validation-candidate rule with edge strictly above 10% (p × odds − 1 > 0.1), best individual-book quotes and flat stake 1,000. This is an exploratory diagnostic replay on an already examined season, not the selected primary strategy.", "diagnostic": true, "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.1, "min_odds": null, "model_key": "first_accuracy", "model_label": "First-study accuracy-selected SVM", "name": "First-study accuracy-selected SVM | historical threshold diagnostic 10% | best individual-book quotes | flat 1,000", "odds_mode": "best", "origin": "legacy_diagnostic", "policy_family": "historical threshold diagnostic 10%", "selection_rule": "max_edge", "staking": "fixed", "strategy_id": "S076", "study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}

Sources:
- epl_player_models\results\20261020_player_models_review\all_strategy_catalog.json

## Slide 24: EPL appendix: strategy rules (7/9)

Default: choose the highest model-estimated return (probability × odds − 1). Only bet above the listed threshold.

Paired IDs share their forecast and entry rule but have separately labeled stakes. Fixed 1,000 is 1% of initial capital; a stated cash percentage uses date-start cash. Kelly fractions and caps are distinct. All IDs below are individual preserved strategies; grouping changes no rule. 'Positive return:6/8 models' requires six models to assign positive estimated return to the chosen outcome, not six favorite picks. H=home win, D=draw, A=away win.

S077: Original SVM forecast Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 15%. 1,000 per bet: 1% of INITIAL 100,000; the amount stays fixed as cash changes. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Highest archived individual-bookmaker odds for the chosen outcome. With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Example: With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Replay the saved First-study accuracy-selected SVM validation-candidate rule with edge strictly above 15% (p × odds − 1 > 0.15), best individual-book quotes and flat stake 1,000. This is an exploratory diagnostic replay on an already examined season, not the selected primary strategy.", "diagnostic": true, "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.15, "min_odds": null, "model_key": "first_accuracy", "model_label": "First-study accuracy-selected SVM", "name": "First-study accuracy-selected SVM | historical threshold diagnostic 15% | best individual-book quotes | flat 1,000", "odds_mode": "best", "origin": "legacy_diagnostic", "policy_family": "historical threshold diagnostic 15%", "selection_rule": "max_edge", "staking": "fixed", "strategy_id": "S077", "study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}

S078: Original SVM forecast Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 20%. 1,000 per bet: 1% of INITIAL 100,000; the amount stays fixed as cash changes. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Highest archived individual-bookmaker odds for the chosen outcome. With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Example: With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Replay the saved First-study accuracy-selected SVM validation-candidate rule with edge strictly above 20% (p × odds − 1 > 0.2), best individual-book quotes and flat stake 1,000. This is an exploratory diagnostic replay on an already examined season, not the selected primary strategy.", "diagnostic": true, "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.2, "min_odds": null, "model_key": "first_accuracy", "model_label": "First-study accuracy-selected SVM", "name": "First-study accuracy-selected SVM | historical threshold diagnostic 20% | best individual-book quotes | flat 1,000", "odds_mode": "best", "origin": "legacy_diagnostic", "policy_family": "historical threshold diagnostic 20%", "selection_rule": "max_edge", "staking": "fixed", "strategy_id": "S078", "study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}

S079: Original neural-network forecast Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 0%. 1,000 per bet: 1% of INITIAL 100,000; the amount stays fixed as cash changes. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Highest archived individual-bookmaker odds for the chosen outcome. With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Example: With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Replay the saved First-study calibration-selected MLP validation-candidate rule with edge strictly above 0% (p × odds − 1 > 0), best individual-book quotes and flat stake 1,000. This is an exploratory diagnostic replay on an already examined season, not the selected primary strategy.", "diagnostic": true, "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.0, "min_odds": null, "model_key": "first_calibration", "model_label": "First-study calibration-selected MLP", "name": "First-study calibration-selected MLP | historical threshold diagnostic 0% | best individual-book quotes | flat 1,000", "odds_mode": "best", "origin": "legacy_diagnostic", "policy_family": "historical threshold diagnostic 0%", "selection_rule": "max_edge", "staking": "fixed", "strategy_id": "S079", "study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}

S080: Original neural-network forecast Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 2.5%. 1,000 per bet: 1% of INITIAL 100,000; the amount stays fixed as cash changes. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Highest archived individual-bookmaker odds for the chosen outcome. With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Example: With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Replay the saved First-study calibration-selected MLP validation-candidate rule with edge strictly above 2.5% (p × odds − 1 > 0.025), best individual-book quotes and flat stake 1,000. This is an exploratory diagnostic replay on an already examined season, not the selected primary strategy.", "diagnostic": true, "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.025, "min_odds": null, "model_key": "first_calibration", "model_label": "First-study calibration-selected MLP", "name": "First-study calibration-selected MLP | historical threshold diagnostic 2.5% | best individual-book quotes | flat 1,000", "odds_mode": "best", "origin": "legacy_diagnostic", "policy_family": "historical threshold diagnostic 2.5%", "selection_rule": "max_edge", "staking": "fixed", "strategy_id": "S080", "study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}

S081: Original neural-network forecast Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 7.5%. 1,000 per bet: 1% of INITIAL 100,000; the amount stays fixed as cash changes. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Highest archived individual-bookmaker odds for the chosen outcome. With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Example: With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Replay the saved First-study calibration-selected MLP validation-candidate rule with edge strictly above 7.5% (p × odds − 1 > 0.075), best individual-book quotes and flat stake 1,000. This is an exploratory diagnostic replay on an already examined season, not the selected primary strategy.", "diagnostic": true, "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.075, "min_odds": null, "model_key": "first_calibration", "model_label": "First-study calibration-selected MLP", "name": "First-study calibration-selected MLP | historical threshold diagnostic 7.5% | best individual-book quotes | flat 1,000", "odds_mode": "best", "origin": "legacy_diagnostic", "policy_family": "historical threshold diagnostic 7.5%", "selection_rule": "max_edge", "staking": "fixed", "strategy_id": "S081", "study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}

S082: Original neural-network forecast Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 10%. 1,000 per bet: 1% of INITIAL 100,000; the amount stays fixed as cash changes. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Highest archived individual-bookmaker odds for the chosen outcome. With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Example: With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Replay the saved First-study calibration-selected MLP validation-candidate rule with edge strictly above 10% (p × odds − 1 > 0.1), best individual-book quotes and flat stake 1,000. This is an exploratory diagnostic replay on an already examined season, not the selected primary strategy.", "diagnostic": true, "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.1, "min_odds": null, "model_key": "first_calibration", "model_label": "First-study calibration-selected MLP", "name": "First-study calibration-selected MLP | historical threshold diagnostic 10% | best individual-book quotes | flat 1,000", "odds_mode": "best", "origin": "legacy_diagnostic", "policy_family": "historical threshold diagnostic 10%", "selection_rule": "max_edge", "staking": "fixed", "strategy_id": "S082", "study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}

S083: Original neural-network forecast Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 15%. 1,000 per bet: 1% of INITIAL 100,000; the amount stays fixed as cash changes. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Highest archived individual-bookmaker odds for the chosen outcome. With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Example: With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Replay the saved First-study calibration-selected MLP validation-candidate rule with edge strictly above 15% (p × odds − 1 > 0.15), best individual-book quotes and flat stake 1,000. This is an exploratory diagnostic replay on an already examined season, not the selected primary strategy.", "diagnostic": true, "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.15, "min_odds": null, "model_key": "first_calibration", "model_label": "First-study calibration-selected MLP", "name": "First-study calibration-selected MLP | historical threshold diagnostic 15% | best individual-book quotes | flat 1,000", "odds_mode": "best", "origin": "legacy_diagnostic", "policy_family": "historical threshold diagnostic 15%", "selection_rule": "max_edge", "staking": "fixed", "strategy_id": "S083", "study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}

S084: Original neural-network forecast Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 20%. 1,000 per bet: 1% of INITIAL 100,000; the amount stays fixed as cash changes. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Highest archived individual-bookmaker odds for the chosen outcome. With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Example: With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start capital and are uniformly scaled to available cash and any declared date cap before outcomes settle", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Replay the saved First-study calibration-selected MLP validation-candidate rule with edge strictly above 20% (p × odds − 1 > 0.2), best individual-book quotes and flat stake 1,000. This is an exploratory diagnostic replay on an already examined season, not the selected primary strategy.", "diagnostic": true, "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.2, "min_odds": null, "model_key": "first_calibration", "model_label": "First-study calibration-selected MLP", "name": "First-study calibration-selected MLP | historical threshold diagnostic 20% | best individual-book quotes | flat 1,000", "odds_mode": "best", "origin": "legacy_diagnostic", "policy_family": "historical threshold diagnostic 20%", "selection_rule": "max_edge", "staking": "fixed", "strategy_id": "S084", "study_status": "exploratory_replay_of_already_examined_2025_26_no_new_holdout"}

Sources:
- epl_player_models\results\20261020_player_models_review\all_strategy_catalog.json

## Slide 25: EPL appendix: strategy rules (8/9)

Default: choose the highest model-estimated return (probability × odds − 1). Only bet above the listed threshold.

Paired IDs share their forecast and entry rule but have separately labeled stakes. Fixed 1,000 is 1% of initial capital; a stated cash percentage uses date-start cash. Kelly fractions and caps are distinct. All IDs below are individual preserved strategies; grouping changes no rule. 'Positive return:6/8 models' requires six models to assign positive estimated return to the chosen outcome, not six favorite picks. H=home win, D=draw, A=away win.

P001: Team form (logistic) Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 5%. 1,000 per bet: 1% of INITIAL 100,000; the amount stays fixed as cash changes. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Highest archived individual-bookmaker odds for the chosen outcome. With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Example: With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start cash and are uniformly scaled to available cash before any same-date outcome settles", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Matched team control | Logistic regression; choose the allowed H/D/A outcome with maximum p × odds − 1 at the best archived individual-book quote. Trade only for edge strictly greater than 5%; request flat 1,000. H/D/A order resolves ties.", "diagnostic": true, "feature_group": "team_control", "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.05, "min_odds": null, "model_key": "pm_logistic_team_control", "model_label": "Matched team control | Logistic regression", "model_type": "logistic", "name": "Matched team control | Logistic regression | best | flat 1,000", "odds_mode": "best", "origin": "new_player_model_study", "policy_family": "frozen 5% player-study diagnostic", "selection_rule": "max_edge", "staking": "fixed", "strategy_id": "P001", "study_status": "exploratory_previously_inspected_history_not_new_holdout_or_selected_live_betting_policy"}

P002: Team form (logistic) Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 5%. Quarter Kelly: B × min(2%, 0.25 × max(0, p×O−1)/(O−1)); B = date-start cash. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Highest archived individual-bookmaker odds for the chosen outcome. B=100,000, p=40%, O=3: full Kelly=10%; 0.25 × 10% capped at 2% requests 2,000 before shared date/cash reduction.
Example: B=100,000, p=40%, O=3: full Kelly=10%; 0.25 × 10% capped at 2% requests 2,000 before shared date/cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start cash and are uniformly scaled to available cash before any same-date outcome settles", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Matched team control | Logistic regression; choose the allowed H/D/A outcome with maximum p × odds − 1 at the best archived individual-book quote. Trade only for edge strictly greater than 5%; request quarter Kelly capped at 2% of date-start cash per bet. H/D/A order resolves ties.", "diagnostic": true, "feature_group": "team_control", "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.05, "min_odds": null, "model_key": "pm_logistic_team_control", "model_label": "Matched team control | Logistic regression", "model_type": "logistic", "name": "Matched team control | Logistic regression | best | quarter Kelly capped at 2% of date-start cash per bet", "odds_mode": "best", "origin": "new_player_model_study", "policy_family": "frozen 5% player-study diagnostic", "selection_rule": "max_edge", "staking": "kelly", "strategy_id": "P002", "study_status": "exploratory_previously_inspected_history_not_new_holdout_or_selected_live_betting_policy"}

P003: Team form (logistic) Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 5%. 1,000 per bet: 1% of INITIAL 100,000; the amount stays fixed as cash changes. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Archived Bet365 odds for the chosen outcome. With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Example: With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start cash and are uniformly scaled to available cash before any same-date outcome settles", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Matched team control | Logistic regression; choose the allowed H/D/A outcome with maximum p × odds − 1 at the archived Bet365 reference quote. Trade only for edge strictly greater than 5%; request flat 1,000. H/D/A order resolves ties.", "diagnostic": true, "feature_group": "team_control", "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.05, "min_odds": null, "model_key": "pm_logistic_team_control", "model_label": "Matched team control | Logistic regression", "model_type": "logistic", "name": "Matched team control | Logistic regression | reference | flat 1,000", "odds_mode": "reference", "origin": "new_player_model_study", "policy_family": "frozen 5% player-study diagnostic", "selection_rule": "max_edge", "staking": "fixed", "strategy_id": "P003", "study_status": "exploratory_previously_inspected_history_not_new_holdout_or_selected_live_betting_policy"}

P004: Team form (logistic) Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 5%. Quarter Kelly: B × min(2%, 0.25 × max(0, p×O−1)/(O−1)); B = date-start cash. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Archived Bet365 odds for the chosen outcome. B=100,000, p=40%, O=3: full Kelly=10%; 0.25 × 10% capped at 2% requests 2,000 before shared date/cash reduction.
Example: B=100,000, p=40%, O=3: full Kelly=10%; 0.25 × 10% capped at 2% requests 2,000 before shared date/cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start cash and are uniformly scaled to available cash before any same-date outcome settles", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Matched team control | Logistic regression; choose the allowed H/D/A outcome with maximum p × odds − 1 at the archived Bet365 reference quote. Trade only for edge strictly greater than 5%; request quarter Kelly capped at 2% of date-start cash per bet. H/D/A order resolves ties.", "diagnostic": true, "feature_group": "team_control", "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.05, "min_odds": null, "model_key": "pm_logistic_team_control", "model_label": "Matched team control | Logistic regression", "model_type": "logistic", "name": "Matched team control | Logistic regression | reference | quarter Kelly capped at 2% of date-start cash per bet", "odds_mode": "reference", "origin": "new_player_model_study", "policy_family": "frozen 5% player-study diagnostic", "selection_rule": "max_edge", "staking": "kelly", "strategy_id": "P004", "study_status": "exploratory_previously_inspected_history_not_new_holdout_or_selected_live_betting_policy"}

P005: Team form (boosted trees) Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 5%. 1,000 per bet: 1% of INITIAL 100,000; the amount stays fixed as cash changes. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Highest archived individual-bookmaker odds for the chosen outcome. With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Example: With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start cash and are uniformly scaled to available cash before any same-date outcome settles", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Matched team control | Histogram gradient boosting; choose the allowed H/D/A outcome with maximum p × odds − 1 at the best archived individual-book quote. Trade only for edge strictly greater than 5%; request flat 1,000. H/D/A order resolves ties.", "diagnostic": true, "feature_group": "team_control", "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.05, "min_odds": null, "model_key": "pm_hist_boost_team_control", "model_label": "Matched team control | Histogram gradient boosting", "model_type": "hist_boost", "name": "Matched team control | Histogram gradient boosting | best | flat 1,000", "odds_mode": "best", "origin": "new_player_model_study", "policy_family": "frozen 5% player-study diagnostic", "selection_rule": "max_edge", "staking": "fixed", "strategy_id": "P005", "study_status": "exploratory_previously_inspected_history_not_new_holdout_or_selected_live_betting_policy"}

P006: Team form (boosted trees) Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 5%. Quarter Kelly: B × min(2%, 0.25 × max(0, p×O−1)/(O−1)); B = date-start cash. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Highest archived individual-bookmaker odds for the chosen outcome. B=100,000, p=40%, O=3: full Kelly=10%; 0.25 × 10% capped at 2% requests 2,000 before shared date/cash reduction.
Example: B=100,000, p=40%, O=3: full Kelly=10%; 0.25 × 10% capped at 2% requests 2,000 before shared date/cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start cash and are uniformly scaled to available cash before any same-date outcome settles", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Matched team control | Histogram gradient boosting; choose the allowed H/D/A outcome with maximum p × odds − 1 at the best archived individual-book quote. Trade only for edge strictly greater than 5%; request quarter Kelly capped at 2% of date-start cash per bet. H/D/A order resolves ties.", "diagnostic": true, "feature_group": "team_control", "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.05, "min_odds": null, "model_key": "pm_hist_boost_team_control", "model_label": "Matched team control | Histogram gradient boosting", "model_type": "hist_boost", "name": "Matched team control | Histogram gradient boosting | best | quarter Kelly capped at 2% of date-start cash per bet", "odds_mode": "best", "origin": "new_player_model_study", "policy_family": "frozen 5% player-study diagnostic", "selection_rule": "max_edge", "staking": "kelly", "strategy_id": "P006", "study_status": "exploratory_previously_inspected_history_not_new_holdout_or_selected_live_betting_policy"}

P007: Team form (boosted trees) Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 5%. 1,000 per bet: 1% of INITIAL 100,000; the amount stays fixed as cash changes. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Archived Bet365 odds for the chosen outcome. With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Example: With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start cash and are uniformly scaled to available cash before any same-date outcome settles", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Matched team control | Histogram gradient boosting; choose the allowed H/D/A outcome with maximum p × odds − 1 at the archived Bet365 reference quote. Trade only for edge strictly greater than 5%; request flat 1,000. H/D/A order resolves ties.", "diagnostic": true, "feature_group": "team_control", "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.05, "min_odds": null, "model_key": "pm_hist_boost_team_control", "model_label": "Matched team control | Histogram gradient boosting", "model_type": "hist_boost", "name": "Matched team control | Histogram gradient boosting | reference | flat 1,000", "odds_mode": "reference", "origin": "new_player_model_study", "policy_family": "frozen 5% player-study diagnostic", "selection_rule": "max_edge", "staking": "fixed", "strategy_id": "P007", "study_status": "exploratory_previously_inspected_history_not_new_holdout_or_selected_live_betting_policy"}

P008: Team form (boosted trees) Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 5%. Quarter Kelly: B × min(2%, 0.25 × max(0, p×O−1)/(O−1)); B = date-start cash. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Archived Bet365 odds for the chosen outcome. B=100,000, p=40%, O=3: full Kelly=10%; 0.25 × 10% capped at 2% requests 2,000 before shared date/cash reduction.
Example: B=100,000, p=40%, O=3: full Kelly=10%; 0.25 × 10% capped at 2% requests 2,000 before shared date/cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start cash and are uniformly scaled to available cash before any same-date outcome settles", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Matched team control | Histogram gradient boosting; choose the allowed H/D/A outcome with maximum p × odds − 1 at the archived Bet365 reference quote. Trade only for edge strictly greater than 5%; request quarter Kelly capped at 2% of date-start cash per bet. H/D/A order resolves ties.", "diagnostic": true, "feature_group": "team_control", "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.05, "min_odds": null, "model_key": "pm_hist_boost_team_control", "model_label": "Matched team control | Histogram gradient boosting", "model_type": "hist_boost", "name": "Matched team control | Histogram gradient boosting | reference | quarter Kelly capped at 2% of date-start cash per bet", "odds_mode": "reference", "origin": "new_player_model_study", "policy_family": "frozen 5% player-study diagnostic", "selection_rule": "max_edge", "staking": "kelly", "strategy_id": "P008", "study_status": "exploratory_previously_inspected_history_not_new_holdout_or_selected_live_betting_policy"}

P009: Player form (logistic) Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 5%. 1,000 per bet: 1% of INITIAL 100,000; the amount stays fixed as cash changes. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Highest archived individual-bookmaker odds for the chosen outcome. With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Example: With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start cash and are uniformly scaled to available cash before any same-date outcome settles", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Player form only | Logistic regression; choose the allowed H/D/A outcome with maximum p × odds − 1 at the best archived individual-book quote. Trade only for edge strictly greater than 5%; request flat 1,000. H/D/A order resolves ties.", "diagnostic": true, "feature_group": "player_form", "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.05, "min_odds": null, "model_key": "pm_logistic_player_form", "model_label": "Player form only | Logistic regression", "model_type": "logistic", "name": "Player form only | Logistic regression | best | flat 1,000", "odds_mode": "best", "origin": "new_player_model_study", "policy_family": "frozen 5% player-study diagnostic", "selection_rule": "max_edge", "staking": "fixed", "strategy_id": "P009", "study_status": "exploratory_previously_inspected_history_not_new_holdout_or_selected_live_betting_policy"}

P010: Player form (logistic) Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 5%. Quarter Kelly: B × min(2%, 0.25 × max(0, p×O−1)/(O−1)); B = date-start cash. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Highest archived individual-bookmaker odds for the chosen outcome. B=100,000, p=40%, O=3: full Kelly=10%; 0.25 × 10% capped at 2% requests 2,000 before shared date/cash reduction.
Example: B=100,000, p=40%, O=3: full Kelly=10%; 0.25 × 10% capped at 2% requests 2,000 before shared date/cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start cash and are uniformly scaled to available cash before any same-date outcome settles", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Player form only | Logistic regression; choose the allowed H/D/A outcome with maximum p × odds − 1 at the best archived individual-book quote. Trade only for edge strictly greater than 5%; request quarter Kelly capped at 2% of date-start cash per bet. H/D/A order resolves ties.", "diagnostic": true, "feature_group": "player_form", "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.05, "min_odds": null, "model_key": "pm_logistic_player_form", "model_label": "Player form only | Logistic regression", "model_type": "logistic", "name": "Player form only | Logistic regression | best | quarter Kelly capped at 2% of date-start cash per bet", "odds_mode": "best", "origin": "new_player_model_study", "policy_family": "frozen 5% player-study diagnostic", "selection_rule": "max_edge", "staking": "kelly", "strategy_id": "P010", "study_status": "exploratory_previously_inspected_history_not_new_holdout_or_selected_live_betting_policy"}

P011: Player form (logistic) Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 5%. 1,000 per bet: 1% of INITIAL 100,000; the amount stays fixed as cash changes. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Archived Bet365 odds for the chosen outcome. With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Example: With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start cash and are uniformly scaled to available cash before any same-date outcome settles", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Player form only | Logistic regression; choose the allowed H/D/A outcome with maximum p × odds − 1 at the archived Bet365 reference quote. Trade only for edge strictly greater than 5%; request flat 1,000. H/D/A order resolves ties.", "diagnostic": true, "feature_group": "player_form", "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.05, "min_odds": null, "model_key": "pm_logistic_player_form", "model_label": "Player form only | Logistic regression", "model_type": "logistic", "name": "Player form only | Logistic regression | reference | flat 1,000", "odds_mode": "reference", "origin": "new_player_model_study", "policy_family": "frozen 5% player-study diagnostic", "selection_rule": "max_edge", "staking": "fixed", "strategy_id": "P011", "study_status": "exploratory_previously_inspected_history_not_new_holdout_or_selected_live_betting_policy"}

P012: Player form (logistic) Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 5%. Quarter Kelly: B × min(2%, 0.25 × max(0, p×O−1)/(O−1)); B = date-start cash. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Archived Bet365 odds for the chosen outcome. B=100,000, p=40%, O=3: full Kelly=10%; 0.25 × 10% capped at 2% requests 2,000 before shared date/cash reduction.
Example: B=100,000, p=40%, O=3: full Kelly=10%; 0.25 × 10% capped at 2% requests 2,000 before shared date/cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start cash and are uniformly scaled to available cash before any same-date outcome settles", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Player form only | Logistic regression; choose the allowed H/D/A outcome with maximum p × odds − 1 at the archived Bet365 reference quote. Trade only for edge strictly greater than 5%; request quarter Kelly capped at 2% of date-start cash per bet. H/D/A order resolves ties.", "diagnostic": true, "feature_group": "player_form", "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.05, "min_odds": null, "model_key": "pm_logistic_player_form", "model_label": "Player form only | Logistic regression", "model_type": "logistic", "name": "Player form only | Logistic regression | reference | quarter Kelly capped at 2% of date-start cash per bet", "odds_mode": "reference", "origin": "new_player_model_study", "policy_family": "frozen 5% player-study diagnostic", "selection_rule": "max_edge", "staking": "kelly", "strategy_id": "P012", "study_status": "exploratory_previously_inspected_history_not_new_holdout_or_selected_live_betting_policy"}

P013: Player form (boosted trees) Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 5%. 1,000 per bet: 1% of INITIAL 100,000; the amount stays fixed as cash changes. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Highest archived individual-bookmaker odds for the chosen outcome. With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Example: With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start cash and are uniformly scaled to available cash before any same-date outcome settles", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Player form only | Histogram gradient boosting; choose the allowed H/D/A outcome with maximum p × odds − 1 at the best archived individual-book quote. Trade only for edge strictly greater than 5%; request flat 1,000. H/D/A order resolves ties.", "diagnostic": true, "feature_group": "player_form", "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.05, "min_odds": null, "model_key": "pm_hist_boost_player_form", "model_label": "Player form only | Histogram gradient boosting", "model_type": "hist_boost", "name": "Player form only | Histogram gradient boosting | best | flat 1,000", "odds_mode": "best", "origin": "new_player_model_study", "policy_family": "frozen 5% player-study diagnostic", "selection_rule": "max_edge", "staking": "fixed", "strategy_id": "P013", "study_status": "exploratory_previously_inspected_history_not_new_holdout_or_selected_live_betting_policy"}

P014: Player form (boosted trees) Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 5%. Quarter Kelly: B × min(2%, 0.25 × max(0, p×O−1)/(O−1)); B = date-start cash. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Highest archived individual-bookmaker odds for the chosen outcome. B=100,000, p=40%, O=3: full Kelly=10%; 0.25 × 10% capped at 2% requests 2,000 before shared date/cash reduction.
Example: B=100,000, p=40%, O=3: full Kelly=10%; 0.25 × 10% capped at 2% requests 2,000 before shared date/cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start cash and are uniformly scaled to available cash before any same-date outcome settles", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Player form only | Histogram gradient boosting; choose the allowed H/D/A outcome with maximum p × odds − 1 at the best archived individual-book quote. Trade only for edge strictly greater than 5%; request quarter Kelly capped at 2% of date-start cash per bet. H/D/A order resolves ties.", "diagnostic": true, "feature_group": "player_form", "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.05, "min_odds": null, "model_key": "pm_hist_boost_player_form", "model_label": "Player form only | Histogram gradient boosting", "model_type": "hist_boost", "name": "Player form only | Histogram gradient boosting | best | quarter Kelly capped at 2% of date-start cash per bet", "odds_mode": "best", "origin": "new_player_model_study", "policy_family": "frozen 5% player-study diagnostic", "selection_rule": "max_edge", "staking": "kelly", "strategy_id": "P014", "study_status": "exploratory_previously_inspected_history_not_new_holdout_or_selected_live_betting_policy"}

P015: Player form (boosted trees) Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 5%. 1,000 per bet: 1% of INITIAL 100,000; the amount stays fixed as cash changes. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Archived Bet365 odds for the chosen outcome. With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Example: With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start cash and are uniformly scaled to available cash before any same-date outcome settles", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Player form only | Histogram gradient boosting; choose the allowed H/D/A outcome with maximum p × odds − 1 at the archived Bet365 reference quote. Trade only for edge strictly greater than 5%; request flat 1,000. H/D/A order resolves ties.", "diagnostic": true, "feature_group": "player_form", "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.05, "min_odds": null, "model_key": "pm_hist_boost_player_form", "model_label": "Player form only | Histogram gradient boosting", "model_type": "hist_boost", "name": "Player form only | Histogram gradient boosting | reference | flat 1,000", "odds_mode": "reference", "origin": "new_player_model_study", "policy_family": "frozen 5% player-study diagnostic", "selection_rule": "max_edge", "staking": "fixed", "strategy_id": "P015", "study_status": "exploratory_previously_inspected_history_not_new_holdout_or_selected_live_betting_policy"}

P016: Player form (boosted trees) Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 5%. Quarter Kelly: B × min(2%, 0.25 × max(0, p×O−1)/(O−1)); B = date-start cash. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Archived Bet365 odds for the chosen outcome. B=100,000, p=40%, O=3: full Kelly=10%; 0.25 × 10% capped at 2% requests 2,000 before shared date/cash reduction.
Example: B=100,000, p=40%, O=3: full Kelly=10%; 0.25 × 10% capped at 2% requests 2,000 before shared date/cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start cash and are uniformly scaled to available cash before any same-date outcome settles", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Player form only | Histogram gradient boosting; choose the allowed H/D/A outcome with maximum p × odds − 1 at the archived Bet365 reference quote. Trade only for edge strictly greater than 5%; request quarter Kelly capped at 2% of date-start cash per bet. H/D/A order resolves ties.", "diagnostic": true, "feature_group": "player_form", "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.05, "min_odds": null, "model_key": "pm_hist_boost_player_form", "model_label": "Player form only | Histogram gradient boosting", "model_type": "hist_boost", "name": "Player form only | Histogram gradient boosting | reference | quarter Kelly capped at 2% of date-start cash per bet", "odds_mode": "reference", "origin": "new_player_model_study", "policy_family": "frozen 5% player-study diagnostic", "selection_rule": "max_edge", "staking": "kelly", "strategy_id": "P016", "study_status": "exploratory_previously_inspected_history_not_new_holdout_or_selected_live_betting_policy"}

Sources:
- epl_player_models\results\20261020_player_models_review\all_strategy_catalog.json

## Slide 26: EPL appendix: strategy rules (9/9)

Default: choose the highest model-estimated return (probability × odds − 1). Only bet above the listed threshold.

Paired IDs share their forecast and entry rule but have separately labeled stakes. Fixed 1,000 is 1% of initial capital; a stated cash percentage uses date-start cash. Kelly fractions and caps are distinct. All IDs below are individual preserved strategies; grouping changes no rule. 'Positive return:6/8 models' requires six models to assign positive estimated return to the chosen outcome, not six favorite picks. H=home win, D=draw, A=away win.

P017: Player form + estimated XI/depth (logistic) Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 5%. 1,000 per bet: 1% of INITIAL 100,000; the amount stays fixed as cash changes. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Highest archived individual-bookmaker odds for the chosen outcome. With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Example: With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start cash and are uniformly scaled to available cash before any same-date outcome settles", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Player form + projected XI + depth | Logistic regression; choose the allowed H/D/A outcome with maximum p × odds − 1 at the best archived individual-book quote. Trade only for edge strictly greater than 5%; request flat 1,000. H/D/A order resolves ties.", "diagnostic": true, "feature_group": "player_squad", "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.05, "min_odds": null, "model_key": "pm_logistic_player_squad", "model_label": "Player form + projected XI + depth | Logistic regression", "model_type": "logistic", "name": "Player form + projected XI + depth | Logistic regression | best | flat 1,000", "odds_mode": "best", "origin": "new_player_model_study", "policy_family": "frozen 5% player-study diagnostic", "selection_rule": "max_edge", "staking": "fixed", "strategy_id": "P017", "study_status": "exploratory_previously_inspected_history_not_new_holdout_or_selected_live_betting_policy"}

P018: Player form + estimated XI/depth (logistic) Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 5%. Quarter Kelly: B × min(2%, 0.25 × max(0, p×O−1)/(O−1)); B = date-start cash. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Highest archived individual-bookmaker odds for the chosen outcome. B=100,000, p=40%, O=3: full Kelly=10%; 0.25 × 10% capped at 2% requests 2,000 before shared date/cash reduction.
Example: B=100,000, p=40%, O=3: full Kelly=10%; 0.25 × 10% capped at 2% requests 2,000 before shared date/cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start cash and are uniformly scaled to available cash before any same-date outcome settles", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Player form + projected XI + depth | Logistic regression; choose the allowed H/D/A outcome with maximum p × odds − 1 at the best archived individual-book quote. Trade only for edge strictly greater than 5%; request quarter Kelly capped at 2% of date-start cash per bet. H/D/A order resolves ties.", "diagnostic": true, "feature_group": "player_squad", "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.05, "min_odds": null, "model_key": "pm_logistic_player_squad", "model_label": "Player form + projected XI + depth | Logistic regression", "model_type": "logistic", "name": "Player form + projected XI + depth | Logistic regression | best | quarter Kelly capped at 2% of date-start cash per bet", "odds_mode": "best", "origin": "new_player_model_study", "policy_family": "frozen 5% player-study diagnostic", "selection_rule": "max_edge", "staking": "kelly", "strategy_id": "P018", "study_status": "exploratory_previously_inspected_history_not_new_holdout_or_selected_live_betting_policy"}

P019: Player form + estimated XI/depth (logistic) Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 5%. 1,000 per bet: 1% of INITIAL 100,000; the amount stays fixed as cash changes. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Archived Bet365 odds for the chosen outcome. With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Example: With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start cash and are uniformly scaled to available cash before any same-date outcome settles", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Player form + projected XI + depth | Logistic regression; choose the allowed H/D/A outcome with maximum p × odds − 1 at the archived Bet365 reference quote. Trade only for edge strictly greater than 5%; request flat 1,000. H/D/A order resolves ties.", "diagnostic": true, "feature_group": "player_squad", "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.05, "min_odds": null, "model_key": "pm_logistic_player_squad", "model_label": "Player form + projected XI + depth | Logistic regression", "model_type": "logistic", "name": "Player form + projected XI + depth | Logistic regression | reference | flat 1,000", "odds_mode": "reference", "origin": "new_player_model_study", "policy_family": "frozen 5% player-study diagnostic", "selection_rule": "max_edge", "staking": "fixed", "strategy_id": "P019", "study_status": "exploratory_previously_inspected_history_not_new_holdout_or_selected_live_betting_policy"}

P020: Player form + estimated XI/depth (logistic) Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 5%. Quarter Kelly: B × min(2%, 0.25 × max(0, p×O−1)/(O−1)); B = date-start cash. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Archived Bet365 odds for the chosen outcome. B=100,000, p=40%, O=3: full Kelly=10%; 0.25 × 10% capped at 2% requests 2,000 before shared date/cash reduction.
Example: B=100,000, p=40%, O=3: full Kelly=10%; 0.25 × 10% capped at 2% requests 2,000 before shared date/cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start cash and are uniformly scaled to available cash before any same-date outcome settles", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Player form + projected XI + depth | Logistic regression; choose the allowed H/D/A outcome with maximum p × odds − 1 at the archived Bet365 reference quote. Trade only for edge strictly greater than 5%; request quarter Kelly capped at 2% of date-start cash per bet. H/D/A order resolves ties.", "diagnostic": true, "feature_group": "player_squad", "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.05, "min_odds": null, "model_key": "pm_logistic_player_squad", "model_label": "Player form + projected XI + depth | Logistic regression", "model_type": "logistic", "name": "Player form + projected XI + depth | Logistic regression | reference | quarter Kelly capped at 2% of date-start cash per bet", "odds_mode": "reference", "origin": "new_player_model_study", "policy_family": "frozen 5% player-study diagnostic", "selection_rule": "max_edge", "staking": "kelly", "strategy_id": "P020", "study_status": "exploratory_previously_inspected_history_not_new_holdout_or_selected_live_betting_policy"}

P021: Player form + estimated XI/depth (trees) Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 5%. 1,000 per bet: 1% of INITIAL 100,000; the amount stays fixed as cash changes. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Highest archived individual-bookmaker odds for the chosen outcome. With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Example: With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start cash and are uniformly scaled to available cash before any same-date outcome settles", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Player form + projected XI + depth | Histogram gradient boosting; choose the allowed H/D/A outcome with maximum p × odds − 1 at the best archived individual-book quote. Trade only for edge strictly greater than 5%; request flat 1,000. H/D/A order resolves ties.", "diagnostic": true, "feature_group": "player_squad", "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.05, "min_odds": null, "model_key": "pm_hist_boost_player_squad", "model_label": "Player form + projected XI + depth | Histogram gradient boosting", "model_type": "hist_boost", "name": "Player form + projected XI + depth | Histogram gradient boosting | best | flat 1,000", "odds_mode": "best", "origin": "new_player_model_study", "policy_family": "frozen 5% player-study diagnostic", "selection_rule": "max_edge", "staking": "fixed", "strategy_id": "P021", "study_status": "exploratory_previously_inspected_history_not_new_holdout_or_selected_live_betting_policy"}

P022: Player form + estimated XI/depth (trees) Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 5%. Quarter Kelly: B × min(2%, 0.25 × max(0, p×O−1)/(O−1)); B = date-start cash. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Highest archived individual-bookmaker odds for the chosen outcome. B=100,000, p=40%, O=3: full Kelly=10%; 0.25 × 10% capped at 2% requests 2,000 before shared date/cash reduction.
Example: B=100,000, p=40%, O=3: full Kelly=10%; 0.25 × 10% capped at 2% requests 2,000 before shared date/cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start cash and are uniformly scaled to available cash before any same-date outcome settles", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Player form + projected XI + depth | Histogram gradient boosting; choose the allowed H/D/A outcome with maximum p × odds − 1 at the best archived individual-book quote. Trade only for edge strictly greater than 5%; request quarter Kelly capped at 2% of date-start cash per bet. H/D/A order resolves ties.", "diagnostic": true, "feature_group": "player_squad", "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.05, "min_odds": null, "model_key": "pm_hist_boost_player_squad", "model_label": "Player form + projected XI + depth | Histogram gradient boosting", "model_type": "hist_boost", "name": "Player form + projected XI + depth | Histogram gradient boosting | best | quarter Kelly capped at 2% of date-start cash per bet", "odds_mode": "best", "origin": "new_player_model_study", "policy_family": "frozen 5% player-study diagnostic", "selection_rule": "max_edge", "staking": "kelly", "strategy_id": "P022", "study_status": "exploratory_previously_inspected_history_not_new_holdout_or_selected_live_betting_policy"}

P023: Player form + estimated XI/depth (trees) Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 5%. 1,000 per bet: 1% of INITIAL 100,000; the amount stays fixed as cash changes. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Archived Bet365 odds for the chosen outcome. With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Example: With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start cash and are uniformly scaled to available cash before any same-date outcome settles", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Player form + projected XI + depth | Histogram gradient boosting; choose the allowed H/D/A outcome with maximum p × odds − 1 at the archived Bet365 reference quote. Trade only for edge strictly greater than 5%; request flat 1,000. H/D/A order resolves ties.", "diagnostic": true, "feature_group": "player_squad", "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.05, "min_odds": null, "model_key": "pm_hist_boost_player_squad", "model_label": "Player form + projected XI + depth | Histogram gradient boosting", "model_type": "hist_boost", "name": "Player form + projected XI + depth | Histogram gradient boosting | reference | flat 1,000", "odds_mode": "reference", "origin": "new_player_model_study", "policy_family": "frozen 5% player-study diagnostic", "selection_rule": "max_edge", "staking": "fixed", "strategy_id": "P023", "study_status": "exploratory_previously_inspected_history_not_new_holdout_or_selected_live_betting_policy"}

P024: Player form + estimated XI/depth (trees) Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 5%. Quarter Kelly: B × min(2%, 0.25 × max(0, p×O−1)/(O−1)); B = date-start cash. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Archived Bet365 odds for the chosen outcome. B=100,000, p=40%, O=3: full Kelly=10%; 0.25 × 10% capped at 2% requests 2,000 before shared date/cash reduction.
Example: B=100,000, p=40%, O=3: full Kelly=10%; 0.25 × 10% capped at 2% requests 2,000 before shared date/cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start cash and are uniformly scaled to available cash before any same-date outcome settles", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Player form + projected XI + depth | Histogram gradient boosting; choose the allowed H/D/A outcome with maximum p × odds − 1 at the archived Bet365 reference quote. Trade only for edge strictly greater than 5%; request quarter Kelly capped at 2% of date-start cash per bet. H/D/A order resolves ties.", "diagnostic": true, "feature_group": "player_squad", "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.05, "min_odds": null, "model_key": "pm_hist_boost_player_squad", "model_label": "Player form + projected XI + depth | Histogram gradient boosting", "model_type": "hist_boost", "name": "Player form + projected XI + depth | Histogram gradient boosting | reference | quarter Kelly capped at 2% of date-start cash per bet", "odds_mode": "reference", "origin": "new_player_model_study", "policy_family": "frozen 5% player-study diagnostic", "selection_rule": "max_edge", "staking": "kelly", "strategy_id": "P024", "study_status": "exploratory_previously_inspected_history_not_new_holdout_or_selected_live_betting_policy"}

P025: Team + player form/XI/depth (logistic) Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 5%. 1,000 per bet: 1% of INITIAL 100,000; the amount stays fixed as cash changes. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Highest archived individual-bookmaker odds for the chosen outcome. With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Example: With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start cash and are uniformly scaled to available cash before any same-date outcome settles", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Team + full player block | Logistic regression; choose the allowed H/D/A outcome with maximum p × odds − 1 at the best archived individual-book quote. Trade only for edge strictly greater than 5%; request flat 1,000. H/D/A order resolves ties.", "diagnostic": true, "feature_group": "team_player_squad", "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.05, "min_odds": null, "model_key": "pm_logistic_team_player_squad", "model_label": "Team + full player block | Logistic regression", "model_type": "logistic", "name": "Team + full player block | Logistic regression | best | flat 1,000", "odds_mode": "best", "origin": "new_player_model_study", "policy_family": "frozen 5% player-study diagnostic", "selection_rule": "max_edge", "staking": "fixed", "strategy_id": "P025", "study_status": "exploratory_previously_inspected_history_not_new_holdout_or_selected_live_betting_policy"}

P026: Team + player form/XI/depth (logistic) Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 5%. Quarter Kelly: B × min(2%, 0.25 × max(0, p×O−1)/(O−1)); B = date-start cash. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Highest archived individual-bookmaker odds for the chosen outcome. B=100,000, p=40%, O=3: full Kelly=10%; 0.25 × 10% capped at 2% requests 2,000 before shared date/cash reduction.
Example: B=100,000, p=40%, O=3: full Kelly=10%; 0.25 × 10% capped at 2% requests 2,000 before shared date/cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start cash and are uniformly scaled to available cash before any same-date outcome settles", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Team + full player block | Logistic regression; choose the allowed H/D/A outcome with maximum p × odds − 1 at the best archived individual-book quote. Trade only for edge strictly greater than 5%; request quarter Kelly capped at 2% of date-start cash per bet. H/D/A order resolves ties.", "diagnostic": true, "feature_group": "team_player_squad", "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.05, "min_odds": null, "model_key": "pm_logistic_team_player_squad", "model_label": "Team + full player block | Logistic regression", "model_type": "logistic", "name": "Team + full player block | Logistic regression | best | quarter Kelly capped at 2% of date-start cash per bet", "odds_mode": "best", "origin": "new_player_model_study", "policy_family": "frozen 5% player-study diagnostic", "selection_rule": "max_edge", "staking": "kelly", "strategy_id": "P026", "study_status": "exploratory_previously_inspected_history_not_new_holdout_or_selected_live_betting_policy"}

P027: Team + player form/XI/depth (logistic) Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 5%. 1,000 per bet: 1% of INITIAL 100,000; the amount stays fixed as cash changes. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Archived Bet365 odds for the chosen outcome. With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Example: With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start cash and are uniformly scaled to available cash before any same-date outcome settles", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Team + full player block | Logistic regression; choose the allowed H/D/A outcome with maximum p × odds − 1 at the archived Bet365 reference quote. Trade only for edge strictly greater than 5%; request flat 1,000. H/D/A order resolves ties.", "diagnostic": true, "feature_group": "team_player_squad", "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.05, "min_odds": null, "model_key": "pm_logistic_team_player_squad", "model_label": "Team + full player block | Logistic regression", "model_type": "logistic", "name": "Team + full player block | Logistic regression | reference | flat 1,000", "odds_mode": "reference", "origin": "new_player_model_study", "policy_family": "frozen 5% player-study diagnostic", "selection_rule": "max_edge", "staking": "fixed", "strategy_id": "P027", "study_status": "exploratory_previously_inspected_history_not_new_holdout_or_selected_live_betting_policy"}

P028: Team + player form/XI/depth (logistic) Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 5%. Quarter Kelly: B × min(2%, 0.25 × max(0, p×O−1)/(O−1)); B = date-start cash. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Archived Bet365 odds for the chosen outcome. B=100,000, p=40%, O=3: full Kelly=10%; 0.25 × 10% capped at 2% requests 2,000 before shared date/cash reduction.
Example: B=100,000, p=40%, O=3: full Kelly=10%; 0.25 × 10% capped at 2% requests 2,000 before shared date/cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start cash and are uniformly scaled to available cash before any same-date outcome settles", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Team + full player block | Logistic regression; choose the allowed H/D/A outcome with maximum p × odds − 1 at the archived Bet365 reference quote. Trade only for edge strictly greater than 5%; request quarter Kelly capped at 2% of date-start cash per bet. H/D/A order resolves ties.", "diagnostic": true, "feature_group": "team_player_squad", "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.05, "min_odds": null, "model_key": "pm_logistic_team_player_squad", "model_label": "Team + full player block | Logistic regression", "model_type": "logistic", "name": "Team + full player block | Logistic regression | reference | quarter Kelly capped at 2% of date-start cash per bet", "odds_mode": "reference", "origin": "new_player_model_study", "policy_family": "frozen 5% player-study diagnostic", "selection_rule": "max_edge", "staking": "kelly", "strategy_id": "P028", "study_status": "exploratory_previously_inspected_history_not_new_holdout_or_selected_live_betting_policy"}

P029: Team + player form/XI/depth (trees) Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 5%. 1,000 per bet: 1% of INITIAL 100,000; the amount stays fixed as cash changes. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Highest archived individual-bookmaker odds for the chosen outcome. With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Example: With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start cash and are uniformly scaled to available cash before any same-date outcome settles", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Team + full player block | Histogram gradient boosting; choose the allowed H/D/A outcome with maximum p × odds − 1 at the best archived individual-book quote. Trade only for edge strictly greater than 5%; request flat 1,000. H/D/A order resolves ties.", "diagnostic": true, "feature_group": "team_player_squad", "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.05, "min_odds": null, "model_key": "pm_hist_boost_team_player_squad", "model_label": "Team + full player block | Histogram gradient boosting", "model_type": "hist_boost", "name": "Team + full player block | Histogram gradient boosting | best | flat 1,000", "odds_mode": "best", "origin": "new_player_model_study", "policy_family": "frozen 5% player-study diagnostic", "selection_rule": "max_edge", "staking": "fixed", "strategy_id": "P029", "study_status": "exploratory_previously_inspected_history_not_new_holdout_or_selected_live_betting_policy"}

P030: Team + player form/XI/depth (trees) Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 5%. Quarter Kelly: B × min(2%, 0.25 × max(0, p×O−1)/(O−1)); B = date-start cash. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Highest archived individual-bookmaker odds for the chosen outcome. B=100,000, p=40%, O=3: full Kelly=10%; 0.25 × 10% capped at 2% requests 2,000 before shared date/cash reduction.
Example: B=100,000, p=40%, O=3: full Kelly=10%; 0.25 × 10% capped at 2% requests 2,000 before shared date/cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start cash and are uniformly scaled to available cash before any same-date outcome settles", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Team + full player block | Histogram gradient boosting; choose the allowed H/D/A outcome with maximum p × odds − 1 at the best archived individual-book quote. Trade only for edge strictly greater than 5%; request quarter Kelly capped at 2% of date-start cash per bet. H/D/A order resolves ties.", "diagnostic": true, "feature_group": "team_player_squad", "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.05, "min_odds": null, "model_key": "pm_hist_boost_team_player_squad", "model_label": "Team + full player block | Histogram gradient boosting", "model_type": "hist_boost", "name": "Team + full player block | Histogram gradient boosting | best | quarter Kelly capped at 2% of date-start cash per bet", "odds_mode": "best", "origin": "new_player_model_study", "policy_family": "frozen 5% player-study diagnostic", "selection_rule": "max_edge", "staking": "kelly", "strategy_id": "P030", "study_status": "exploratory_previously_inspected_history_not_new_holdout_or_selected_live_betting_policy"}

P031: Team + player form/XI/depth (trees) Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 5%. 1,000 per bet: 1% of INITIAL 100,000; the amount stays fixed as cash changes. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Archived Bet365 odds for the chosen outcome. With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Example: With cash 80,000, still request 1,000 per qualifying bet before any shared cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start cash and are uniformly scaled to available cash before any same-date outcome settles", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Team + full player block | Histogram gradient boosting; choose the allowed H/D/A outcome with maximum p × odds − 1 at the archived Bet365 reference quote. Trade only for edge strictly greater than 5%; request flat 1,000. H/D/A order resolves ties.", "diagnostic": true, "feature_group": "team_player_squad", "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.05, "min_odds": null, "model_key": "pm_hist_boost_team_player_squad", "model_label": "Team + full player block | Histogram gradient boosting", "model_type": "hist_boost", "name": "Team + full player block | Histogram gradient boosting | reference | flat 1,000", "odds_mode": "reference", "origin": "new_player_model_study", "policy_family": "frozen 5% player-study diagnostic", "selection_rule": "max_edge", "staking": "fixed", "strategy_id": "P031", "study_status": "exploratory_previously_inspected_history_not_new_holdout_or_selected_live_betting_policy"}

P032: Team + player form/XI/depth (trees) Among home win, draw, away win, pick the largest estimated return p×O−1; bet only above 5%. Quarter Kelly: B × min(2%, 0.25 × max(0, p×O−1)/(O−1)); B = date-start cash. If all same-date requests exceed available cash, shrink every request by the same proportion. At most one bet per match; no borrowing or use of same-date winnings. Archived Bet365 odds for the chosen outcome. B=100,000, p=40%, O=3: full Kelly=10%; 0.25 × 10% capped at 2% requests 2,000 before shared date/cash reduction.
Example: B=100,000, p=40%, O=3: full Kelly=10%; 0.25 × 10% capped at 2% requests 2,000 before shared date/cash reduction.
Exact configuration:
{"allocation_basis": "All requests use date-start cash and are uniformly scaled to available cash before any same-date outcome settles", "allowed_outcomes": ["H", "D", "A"], "bankroll_fraction": 0.01, "cash_only": false, "consensus_min": null, "consensus_model_keys": [], "date_cap_fraction": null, "description": "Team + full player block | Histogram gradient boosting; choose the allowed H/D/A outcome with maximum p × odds − 1 at the archived Bet365 reference quote. Trade only for edge strictly greater than 5%; request quarter Kelly capped at 2% of date-start cash per bet. H/D/A order resolves ties.", "diagnostic": true, "feature_group": "team_player_squad", "fixed_stake": 1000.0, "kelly_fraction": 0.25, "max_bet_fraction": 0.02, "max_odds": null, "min_edge": 0.05, "min_odds": null, "model_key": "pm_hist_boost_team_player_squad", "model_label": "Team + full player block | Histogram gradient boosting", "model_type": "hist_boost", "name": "Team + full player block | Histogram gradient boosting | reference | quarter Kelly capped at 2% of date-start cash per bet", "odds_mode": "reference", "origin": "new_player_model_study", "policy_family": "frozen 5% player-study diagnostic", "selection_rule": "max_edge", "staking": "kelly", "strategy_id": "P032", "study_status": "exploratory_previously_inspected_history_not_new_holdout_or_selected_live_betting_policy"}

Sources:
- epl_player_models\results\20261020_player_models_review\all_strategy_catalog.json

## Slide 27: EPL appendix: every bankrupt-policy inverse (1/2)

Original ending cash is zero in every row. Main results are funded full-horizon complements with no cost, 2022/23–2025/26.

Each original strategy is explained in the preceding catalogue. Its original qualification is retained on the entire 1,470-fixture horizon, including after bankruptcy. Context is strategy ID plus quote mode; the 17 contexts cover 15 distinct IDs. Best denotes archived highest individual-book quotes; Bet365 denotes a reference-policy replay with its own original selection under those prices. Complement rule: back both other outcomes, splitting total risk R=1,000 by reciprocal quote weights so both gross payouts are R/S, S=sum(1/O_other). Retain any original date cap. All same-date commitments share opening cash; scale uniformly and never borrow or reuse same-date wins. A zero inverse remains zero. Frequency denominator is 1,470 opportunities. Bets are funded fixture bundles; there are two back legs per bundle. Signals include unfunded qualifying fixtures. Stake ROI is profit divided by allocated bundle stakes. Expected gain and loss are nonnegative probability-weighted components under the original model, not realised average wins and losses. Price-supported costs haircut positive net bundle profit at 2% and 5%, without rebating negative profit. Synthetic lay uses fixed maximum liability 1,000, counterstake 1,000/(original odds-1), at the original back price; real lay quotes and fills are not supplied. The recorded-exposure mirror is the negative of existing realised cashflow. Its arithmetic endpoint is an identity, not a newly earned strategy result; exact liability may require extra opening cash. Every full metric, conditional ROI interval and identity funding diagnostic for these rows follows:
[
  {
    "context": "S033__reference",
    "model": "Rolling training-class frequency",
    "entry_rule": "max_edge",
    "primary": {
      "Index": 249,
      "context_id": "S033__reference",
      "strategy_id": "S033",
      "model_key": "baseline_class_frequency",
      "model_label": "Rolling training-class frequency",
      "price_mode": "reference",
      "selection_rule": "max_edge",
      "original_zero": true,
      "variant": "dutch_cost_0",
      "kind": "dutch",
      "cost_rate": 0.0,
      "initial_capital": 100000.0,
      "final_capital": 24426.20052788943,
      "profit": -75573.79947211058,
      "return_on_initial_capital": -0.7557379947211058,
      "risk_turnover": 1409000.0,
      "turnover": 1409000.0,
      "risk_roi": -0.0536364793982332,
      "roi": -0.0536364793982332,
      "bet_count": 1409,
      "leg_count": 2818,
      "qualifying_signals": 1409,
      "trading_frequency": 0.9585034013605442,
      "event_hit_ratio": 0.7764371894960965,
      "positive_profit_hit_ratio": 0.7601135557132718,
      "expected_gain_per_trade": 142.30241374465822,
      "expected_loss_per_trade": 387.446621025456,
      "avg_winning_gain": 223.7171765487201,
      "avg_losing_loss": 938.0205224874692,
      "fees": 0.0,
      "max_drawdown": 0.7562790998388946,
      "active_dates": 450,
      "scaled_dates": 0,
      "max_date_exposure": 0.3321895976569706,
      "nonpositive_complement_payout_bundles": 24,
      "roi_ci_low": -0.0817515339164416,
      "roi_ci_high": -0.0249233503079763
    },
    "cost_2_final": 19634.178606215904,
    "cost_5_final": 12446.145723705393,
    "synthetic_lay_final": 120882.26300782234,
    "identity_diagnostic": {
      "original_final_capital": 0.0,
      "arithmetic_mirror_final": 200000.0,
      "arithmetic_mirror_minimum": 81990.0,
      "original_peak_capital": 118010.0,
      "max_same_date_liability": 64400.0,
      "minimum_additional_opening_cash": 0.0,
      "funding_shortfall_dates": 0,
      "mirror_funding_feasible": true,
      "original_bet_count": 781
    }
  },
  {
    "context": "S039__reference",
    "model": "Raw de-vigged Bet365 market",
    "entry_rule": "fixed_outcome",
    "primary": {
      "Index": 255,
      "context_id": "S039__reference",
      "strategy_id": "S039",
      "model_key": "baseline_market_only",
      "model_label": "Raw de-vigged Bet365 market",
      "price_mode": "reference",
      "selection_rule": "fixed_outcome",
      "original_zero": true,
      "variant": "dutch_cost_0",
      "kind": "dutch",
      "cost_rate": 0.0,
      "initial_capital": 100000.0,
      "final_capital": 0.0,
      "profit": -100000.0,
      "return_on_initial_capital": -1.0,
      "risk_turnover": 1121830.9735631864,
      "turnover": 1121830.9735631864,
      "risk_roi": -0.0891399884265787,
      "roi": -0.0891399884265787,
      "bet_count": 1194,
      "leg_count": 2388,
      "qualifying_signals": 1470,
      "trading_frequency": 0.8122448979591836,
      "event_hit_ratio": 0.5452261306532663,
      "positive_profit_hit_ratio": 0.5443886097152428,
      "expected_gain_per_trade": 368.2894856570305,
      "expected_loss_per_trade": 416.71377579187583,
      "avg_winning_gain": 632.544250367342,
      "avg_losing_loss": 939.620887387449,
      "fees": 0.0,
      "max_drawdown": 1.0,
      "active_dates": 368,
      "scaled_dates": 25,
      "max_date_exposure": 1.0,
      "nonpositive_complement_payout_bundles": 1,
      "roi_ci_low": -0.1469187427561068,
      "roi_ci_high": -0.0301944894486122
    },
    "cost_2_final": 0.0,
    "cost_5_final": 0.0,
    "synthetic_lay_final": 176439.95248527723,
    "identity_diagnostic": {
      "original_final_capital": 0.0,
      "arithmetic_mirror_final": 200000.0,
      "arithmetic_mirror_minimum": 64440.0,
      "original_peak_capital": 135560.0,
      "max_same_date_liability": 24790.0,
      "minimum_additional_opening_cash": 0.0,
      "funding_shortfall_dates": 0,
      "mirror_funding_feasible": true,
      "original_bet_count": 1420
    }
  },
  {
    "context": "S041__best",
    "model": "Raw de-vigged Bet365 market",
    "entry_rule": "fixed_outcome",
    "primary": {
      "Index": 66,
      "context_id": "S041__best",
      "strategy_id": "S041",
      "model_key": "baseline_market_only",
      "model_label": "Raw de-vigged Bet365 market",
      "price_mode": "best",
      "selection_rule": "fixed_outcome",
      "original_zero": true,
      "variant": "dutch_cost_0",
      "kind": "dutch",
      "cost_rate": 0.0,
      "initial_capital": 100000.0,
      "final_capital": 83273.81539575412,
      "profit": -16726.18460424588,
      "return_on_initial_capital": -0.1672618460424587,
      "risk_turnover": 1470000.0,
      "turnover": 1470000.0,
      "risk_roi": -0.0113783568736366,
      "roi": -0.0113783568736366,
      "bet_count": 1470,
      "leg_count": 2940,
      "qualifying_signals": 1470,
      "trading_frequency": 1.0,
      "event_hit_ratio": 0.6863945578231293,
      "positive_profit_hit_ratio": 0.6857142857142857,
      "expected_gain_per_trade": 301.20300571320377,
      "expected_loss_per_trade": 323.03427074419943,
      "avg_winning_gain": 440.748215611592,
      "avg_losing_loss": 997.8363332050444,
      "fees": 0.0,
      "max_drawdown": 0.3923940452038462,
      "active_dates": 453,
      "scaled_dates": 0,
      "max_date_exposure": 0.1204245201845918,
      "nonpositive_complement_payout_bundles": 1,
      "roi_ci_low": -0.051557510723285,
      "roi_ci_high": 0.0294654275522586
    },
    "cost_2_final": 74388.33136902445,
    "cost_5_final": 61060.10532892992,
    "synthetic_lay_final": 140579.9459567052,
    "identity_diagnostic": {
      "original_final_capital": 0.0,
      "arithmetic_mirror_final": 200000.0,
      "arithmetic_mirror_minimum": 99110.0,
      "original_peak_capital": 100890.0,
      "max_same_date_liability": 66590.0,
      "minimum_additional_opening_cash": 0.0,
      "funding_shortfall_dates": 0,
      "mirror_funding_feasible": true,
      "original_bet_count": 670
    }
  },
  {
    "context": "S041__reference",
    "model": "Raw de-vigged Bet365 market",
    "entry_rule": "fixed_outcome",
    "primary": {
      "Index": 261,
      "context_id": "S041__reference",
      "strategy_id": "S041",
      "model_key": "baseline_market_only",
      "model_label": "Raw de-vigged Bet365 market",
      "price_mode": "reference",
      "selection_rule": "fixed_outcome",
      "original_zero": true,
      "variant": "dutch_cost_0",
      "kind": "dutch",
      "cost_rate": 0.0,
      "initial_capital": 100000.0,
      "final_capital": 39139.423434874974,
      "profit": -60860.57656512503,
      "return_on_initial_capital": -0.6086057656512502,
      "risk_turnover": 1470000.0,
      "turnover": 1470000.0,
      "risk_roi": -0.0414017527653911,
      "roi": -0.0414017527653911,
      "bet_count": 1470,
      "leg_count": 2940,
      "qualifying_signals": 1470,
      "trading_frequency": 1.0,
      "event_hit_ratio": 0.6863945578231293,
      "positive_profit_hit_ratio": 0.6714285714285714,
      "expected_gain_per_trade": 271.47114107769164,
      "expected_loss_per_trade": 323.14794808068245,
      "avg_winning_gain": 405.5847323271096,
      "avg_losing_loss": 958.7790174053686,
      "fees": 0.0,
      "max_drawdown": 0.7317936992906701,
      "active_dates": 453,
      "scaled_dates": 0,
      "max_date_exposure": 0.2298535631078913,
      "nonpositive_complement_payout_bundles": 23,
      "roi_ci_low": -0.0805111646606932,
      "roi_ci_high": -0.0023417627224205
    },
    "cost_2_final": 31133.180818737845,
    "cost_5_final": 19123.816894531967,
    "synthetic_lay_final": 168947.58450303628,
    "identity_diagnostic": {
      "original_final_capital": 0.0,
      "arithmetic_mirror_final": 200000.0,
      "arithmetic_mirror_minimum": 99150.0,
      "original_peak_capital": 100850.0,
      "max_same_date_liability": 57350.0,
      "minimum_additional_opening_cash": 0.0,
      "funding_shortfall_dates": 0,
      "mirror_funding_feasible": true,
      "original_bet_count": 644
    }
  },
  {
    "context": "S043__best",
    "model": "Raw de-vigged Bet365 market",
    "entry_rule": "market_underdog",
    "primary": {
      "Index": 77,
      "context_id": "S043__best",
      "strategy_id": "S043",
      "model_key": "baseline_market_only",
      "model_label": "Raw de-vigged Bet365 market",
      "price_mode": "best",
      "selection_rule": "market_underdog",
      "original_zero": true,
      "variant": "dutch_cost_0",
      "kind": "dutch",
      "cost_rate": 0.0,
      "initial_capital": 100000.0,
      "final_capital": 63773.70034036881,
      "profit": -36226.29965963119,
      "return_on_initial_capital": -0.3622629965963119,
      "risk_turnover": 1470000.0,
      "turnover": 1470000.0,
      "risk_roi": -0.0246437412650552,
      "roi": -0.0246437412650552,
      "bet_count": 1470,
      "leg_count": 2940,
      "qualifying_signals": 1470,
      "trading_frequency": 1.0,
      "event_hit_ratio": 0.7952380952380952,
      "positive_profit_hit_ratio": 0.7945578231292517,
      "expected_gain_per_trade": 180.8332346076035,
      "expected_loss_per_trade": 207.28439208139028,
      "avg_winning_gain": 226.69014236395483,
      "avg_losing_loss": 996.690019671293,
      "fees": 0.0,
      "max_drawdown": 0.3638230082268603,
      "active_dates": 453,
      "scaled_dates": 0,
      "max_date_exposure": 0.1355023387346839,
      "nonpositive_complement_payout_bundles": 1,
      "roi_ci_low": -0.0507688675149691,
      "roi_ci_high": 0.0011573301357374
    },
    "cost_2_final": 58478.21861474677,
    "cost_5_final": 50534.9960263136,
    "synthetic_lay_final": 107026.21910893676,
    "identity_diagnostic": {
      "original_final_capital": 0.0,
      "arithmetic_mirror_final": 200000.0,
      "arithmetic_mirror_minimum": 80590.0,
      "original_peak_capital": 119410.0,
      "max_same_date_liability": 76430.0,
      "minimum_additional_opening_cash": 0.0,
      "funding_shortfall_dates": 0,
      "mirror_funding_feasible": true,
      "original_bet_count": 1363
    }
  },
  {
    "context": "S043__reference",
    "model": "Raw de-vigged Bet365 market",
    "entry_rule": "market_underdog",
    "primary": {
      "Index": 267,
      "context_id": "S043__reference",
      "strategy_id": "S043",
      "model_key": "baseline_market_only",
      "model_label": "Raw de-vigged Bet365 market",
      "price_mode": "reference",
      "selection_rule": "market_underdog",
      "original_zero": true,
      "variant": "dutch_cost_0",
      "kind": "dutch",
      "cost_rate": 0.0,
      "initial_capital": 100000.0,
      "final_capital": 26653.167196931263,
      "profit": -73346.83280306874,
      "return_on_initial_capital": -0.7334683280306874,
      "risk_turnover": 1470000.0,
      "turnover": 1470000.0,
      "risk_roi": -0.0498958046279379,
      "roi": -0.0498958046279379,
      "bet_count": 1470,
      "leg_count": 2940,
      "qualifying_signals": 1470,
      "trading_frequency": 1.0,
      "event_hit_ratio": 0.7952380952380952,
      "positive_profit_hit_ratio": 0.7795918367346939,
      "expected_gain_per_trade": 155.72266844842045,
      "expected_loss_per_trade": 207.3994754514113,
      "avg_winning_gain": 198.8028470791632,
      "avg_losing_loss": 935.3257625956202,
      "fees": 0.0,
      "max_drawdown": 0.7340587663659117,
      "active_dates": 453,
      "scaled_dates": 0,
      "max_date_exposure": 0.3056411058264084,
      "nonpositive_complement_payout_bundles": 24,
      "roi_ci_low": -0.0749754153267812,
      "roi_ci_high": -0.0245448357359063
    },
    "cost_2_final": 22096.60594187682,
    "cost_5_final": 15261.764059295156,
    "synthetic_lay_final": 124837.83285595424,
    "identity_diagnostic": {
      "original_final_capital": 0.0,
      "arithmetic_mirror_final": 200000.0,
      "arithmetic_mirror_minimum": 83900.0,
      "original_peak_capital": 116100.0,
      "max_same_date_liability": 70630.0,
      "minimum_additional_opening_cash": 0.0,
      "funding_shortfall_dates": 0,
      "mirror_funding_feasible": true,
      "original_bet_count": 806
    }
  },
  {
    "context": "P009__best",
    "model": "Player form only | Logistic regression",
    "entry_rule": "max_edge",
    "primary": {
      "Index": 178,
      "context_id": "P009__best",
      "strategy_id": "P009",
      "model_key": "pm_logistic_player_form",
      "model_label": "Player form only | Logistic regression",
      "price_mode": "best",
      "selection_rule": "max_edge",
      "original_zero": true,
      "variant": "dutch_cost_0",
      "kind": "dutch",
      "cost_rate": 0.0,
      "initial_capital": 100000.0,
      "final_capital": 92926.75404630994,
      "profit": -7073.245953690057,
      "return_on_initial_capital": -0.0707324595369005,
      "risk_turnover": 1384000.0,
      "turnover": 1384000.0,
      "risk_roi": -0.0051107268451517,
      "roi": -0.0051107268451517,
      "bet_count": 1384,
      "leg_count": 2768,
      "qualifying_signals": 1384,
      "trading_frequency": 0.9414965986394558,
      "event_hit_ratio": 0.7543352601156069,
      "positive_profit_hit_ratio": 0.7543352601156069,
      "expected_gain_per_trade": 199.23175388064777,
      "expected_loss_per_trade": 354.8259624361926,
      "avg_winning_gain": 318.8953582819061,
      "avg_losing_loss": 1000.0,
      "fees": 0.0,
      "max_drawdown": 0.2963226566175935,
      "active_dates": 450,
      "scaled_dates": 0,
      "max_date_exposure": 0.1213287247103896,
      "nonpositive_complement_payout_bundles": 0,
      "roi_ci_low": -0.0359667960871959,
      "roi_ci_high": 0.0260014282881813
    },
    "cost_2_final": 86268.21896538365,
    "cost_5_final": 76280.4163439945,
    "synthetic_lay_final": 138377.46960545555,
    "identity_diagnostic": {
      "original_final_capital": 0.0,
      "arithmetic_mirror_final": 200000.0,
      "arithmetic_mirror_minimum": 85260.0,
      "original_peak_capital": 114740.0,
      "max_same_date_liability": 53870.0,
      "minimum_additional_opening_cash": 0.0,
      "funding_shortfall_dates": 0,
      "mirror_funding_feasible": true,
      "original_bet_count": 944
    }
  },
  {
    "context": "P011__reference",
    "model": "Player form only | Logistic regression",
    "entry_rule": "max_edge",
    "primary": {
      "Index": 184,
      "context_id": "P011__reference",
      "strategy_id": "P011",
      "model_key": "pm_logistic_player_form",
      "model_label": "Player form only | Logistic regression",
      "price_mode": "reference",
      "selection_rule": "max_edge",
      "original_zero": true,
      "variant": "dutch_cost_0",
      "kind": "dutch",
      "cost_rate": 0.0,
      "initial_capital": 100000.0,
      "final_capital": 49177.76660434643,
      "profit": -50822.23339565357,
      "return_on_initial_capital": -0.5082223339565357,
      "risk_turnover": 1290000.0,
      "turnover": 1290000.0,
      "risk_roi": -0.0393970801516694,
      "roi": -0.0393970801516694,
      "bet_count": 1290,
      "leg_count": 2580,
      "qualifying_signals": 1290,
      "trading_frequency": 0.8775510204081632,
      "event_hit_ratio": 0.7534883720930232,
      "positive_profit_hit_ratio": 0.7472868217054264,
      "expected_gain_per_trade": 170.48615045544108,
      "expected_loss_per_trade": 356.14161720073,
      "avg_winning_gain": 277.22395827265257,
      "avg_losing_loss": 975.6629729156156,
      "fees": 0.0,
      "max_drawdown": 0.5093117519018546,
      "active_dates": 439,
      "scaled_dates": 0,
      "max_date_exposure": 0.153462303783835,
      "nonpositive_complement_payout_bundles": 8,
      "roi_ci_low": -0.0703186906027105,
      "roi_ci_high": -0.0068681893981596
    },
    "cost_2_final": 43832.88868884975,
    "cost_5_final": 35815.57181560449,
    "synthetic_lay_final": 145073.41155223537,
    "identity_diagnostic": {
      "original_final_capital": 0.0,
      "arithmetic_mirror_final": 200000.0,
      "arithmetic_mirror_minimum": 91930.0,
      "original_peak_capital": 108070.0,
      "max_same_date_liability": 49130.0,
      "minimum_additional_opening_cash": 0.0,
      "funding_shortfall_dates": 0,
      "mirror_funding_feasible": true,
      "original_bet_count": 681
    }
  },
  {
    "context": "P013__best",
    "model": "Player form only | Histogram gradient boosting",
    "entry_rule": "max_edge",
    "primary": {
      "Index": 190,
      "context_id": "P013__best",
      "strategy_id": "P013",
      "model_key": "pm_hist_boost_player_form",
      "model_label": "Player form only | Histogram gradient boosting",
      "price_mode": "best",
      "selection_rule": "max_edge",
      "original_zero": true,
      "variant": "dutch_cost_0",
      "kind": "dutch",
      "cost_rate": 0.0,
      "initial_capital": 100000.0,
      "final_capital": 94727.19017021284,
      "profit": -5272.809829787162,
      "return_on_initial_capital": -0.0527280982978716,
      "risk_turnover": 1351000.0,
      "turnover": 1351000.0,
      "risk_roi": -0.0039028940264893,
      "roi": -0.0039028940264893,
      "bet_count": 1351,
      "leg_count": 2702,
      "qualifying_signals": 1351,
      "trading_frequency": 0.919047619047619,
      "event_hit_ratio": 0.769059955588453,
      "positive_profit_hit_ratio": 0.768319763138416,
      "expected_gain_per_trade": 188.7798164014372,
      "expected_loss_per_trade": 342.0166143196193,
      "avg_winning_gain": 295.49862823790306,
      "avg_losing_loss": 996.806344858564,
      "fees": 0.0,
      "max_drawdown": 0.2194378022371294,
      "active_dates": 439,
      "scaled_dates": 0,
      "max_date_exposure": 0.1144903568343258,
      "nonpositive_complement_payout_bundles": 1,
      "roi_ci_low": -0.0366632907808258,
      "roi_ci_high": 0.0285638557107247
    },
    "cost_2_final": 88592.63864799392,
    "cost_5_final": 79390.81136466563,
    "synthetic_lay_final": 138138.2098214374,
    "identity_diagnostic": {
      "original_final_capital": 0.0,
      "arithmetic_mirror_final": 200000.0,
      "arithmetic_mirror_minimum": 63880.0,
      "original_peak_capital": 136120.0,
      "max_same_date_liability": 65970.0,
      "minimum_additional_opening_cash": 0.0,
      "funding_shortfall_dates": 0,
      "mirror_funding_feasible": true,
      "original_bet_count": 1037
    }
  }
]

Sources:
- C:\Users\melin\OneDrive\Desktop\nyu\fall 2026\Stat Arb\final_project\final_review\epl_results\metrics.csv
- C:\Users\melin\OneDrive\Desktop\nyu\fall 2026\Stat Arb\final_project\final_review\epl_results\identity_diagnostics.csv
- final_review/inverse_protocol.md

## Slide 28: EPL appendix: every bankrupt-policy inverse (2/2)

Original ending cash is zero in every row. Main results are funded full-horizon complements with no cost, 2022/23–2025/26.

Each original strategy is explained in the preceding catalogue. Its original qualification is retained on the entire 1,470-fixture horizon, including after bankruptcy. Context is strategy ID plus quote mode; the 17 contexts cover 15 distinct IDs. Best denotes archived highest individual-book quotes; Bet365 denotes a reference-policy replay with its own original selection under those prices. Complement rule: back both other outcomes, splitting total risk R=1,000 by reciprocal quote weights so both gross payouts are R/S, S=sum(1/O_other). Retain any original date cap. All same-date commitments share opening cash; scale uniformly and never borrow or reuse same-date wins. A zero inverse remains zero. Frequency denominator is 1,470 opportunities. Bets are funded fixture bundles; there are two back legs per bundle. Signals include unfunded qualifying fixtures. Stake ROI is profit divided by allocated bundle stakes. Expected gain and loss are nonnegative probability-weighted components under the original model, not realised average wins and losses. Price-supported costs haircut positive net bundle profit at 2% and 5%, without rebating negative profit. Synthetic lay uses fixed maximum liability 1,000, counterstake 1,000/(original odds-1), at the original back price; real lay quotes and fills are not supplied. The recorded-exposure mirror is the negative of existing realised cashflow. Its arithmetic endpoint is an identity, not a newly earned strategy result; exact liability may require extra opening cash. Every full metric, conditional ROI interval and identity funding diagnostic for these rows follows:
[
  {
    "context": "P015__reference",
    "model": "Player form only | Histogram gradient boosting",
    "entry_rule": "max_edge",
    "primary": {
      "Index": 196,
      "context_id": "P015__reference",
      "strategy_id": "P015",
      "model_key": "pm_hist_boost_player_form",
      "model_label": "Player form only | Histogram gradient boosting",
      "price_mode": "reference",
      "selection_rule": "max_edge",
      "original_zero": true,
      "variant": "dutch_cost_0",
      "kind": "dutch",
      "cost_rate": 0.0,
      "initial_capital": 100000.0,
      "final_capital": 66059.4531166984,
      "profit": -33940.546883301606,
      "return_on_initial_capital": -0.339405468833016,
      "risk_turnover": 1276000.0,
      "turnover": 1276000.0,
      "risk_roi": -0.0265991746734338,
      "roi": -0.0265991746734338,
      "bet_count": 1276,
      "leg_count": 2552,
      "qualifying_signals": 1276,
      "trading_frequency": 0.8680272108843538,
      "event_hit_ratio": 0.7750783699059561,
      "positive_profit_hit_ratio": 0.7641065830721003,
      "expected_gain_per_trade": 163.08552831160912,
      "expected_loss_per_trade": 344.64317001782723,
      "avg_winning_gain": 259.650016444758,
      "avg_losing_loss": 956.9977097231356,
      "fees": 0.0,
      "max_drawdown": 0.3417896069113082,
      "active_dates": 430,
      "scaled_dates": 0,
      "max_date_exposure": 0.1308664313719313,
      "nonpositive_complement_payout_bundles": 15,
      "roi_ci_low": -0.0586436728794564,
      "roi_ci_high": 0.0051978450778305
    },
    "cost_2_final": 60996.277796025446,
    "cost_5_final": 53401.51481501638,
    "synthetic_lay_final": 159942.21182525004,
    "identity_diagnostic": {
      "original_final_capital": 0.0,
      "arithmetic_mirror_final": 200000.0,
      "arithmetic_mirror_minimum": 69440.0,
      "original_peak_capital": 130560.0,
      "max_same_date_liability": 52250.0,
      "minimum_additional_opening_cash": 0.0,
      "funding_shortfall_dates": 0,
      "mirror_funding_feasible": true,
      "original_bet_count": 787
    }
  },
  {
    "context": "P019__reference",
    "model": "Player form + projected XI + depth | Logistic regression",
    "entry_rule": "max_edge",
    "primary": {
      "Index": 207,
      "context_id": "P019__reference",
      "strategy_id": "P019",
      "model_key": "pm_logistic_player_squad",
      "model_label": "Player form + projected XI + depth | Logistic regression",
      "price_mode": "reference",
      "selection_rule": "max_edge",
      "original_zero": true,
      "variant": "dutch_cost_0",
      "kind": "dutch",
      "cost_rate": 0.0,
      "initial_capital": 100000.0,
      "final_capital": 20120.95811880124,
      "profit": -79879.04188119876,
      "return_on_initial_capital": -0.7987904188119876,
      "risk_turnover": 1360000.0,
      "turnover": 1360000.0,
      "risk_roi": -0.0587345896185285,
      "roi": -0.0587345896185285,
      "bet_count": 1360,
      "leg_count": 2720,
      "qualifying_signals": 1360,
      "trading_frequency": 0.9251700680272108,
      "event_hit_ratio": 0.7411764705882353,
      "positive_profit_hit_ratio": 0.7330882352941176,
      "expected_gain_per_trade": 167.63306074719014,
      "expected_loss_per_trade": 365.5101634044209,
      "avg_winning_gain": 273.037885964604,
      "avg_losing_loss": 969.9664302697212,
      "fees": 0.0,
      "max_drawdown": 0.8037543310180307,
      "active_dates": 439,
      "scaled_dates": 0,
      "max_date_exposure": 0.3292821245669403,
      "nonpositive_complement_payout_bundles": 11,
      "roi_ci_low": -0.0895823759961758,
      "roi_ci_high": -0.0277626843325944
    },
    "cost_2_final": 14676.582672667078,
    "cost_5_final": 6510.019503465721,
    "synthetic_lay_final": 118747.42956039764,
    "identity_diagnostic": {
      "original_final_capital": 0.0,
      "arithmetic_mirror_final": 200000.0,
      "arithmetic_mirror_minimum": 94940.0,
      "original_peak_capital": 105060.0,
      "max_same_date_liability": 50130.0,
      "minimum_additional_opening_cash": 0.0,
      "funding_shortfall_dates": 0,
      "mirror_funding_feasible": true,
      "original_bet_count": 724
    }
  },
  {
    "context": "P021__best",
    "model": "Player form + projected XI + depth | Histogram gradient boosting",
    "entry_rule": "max_edge",
    "primary": {
      "Index": 213,
      "context_id": "P021__best",
      "strategy_id": "P021",
      "model_key": "pm_hist_boost_player_squad",
      "model_label": "Player form + projected XI + depth | Histogram gradient boosting",
      "price_mode": "best",
      "selection_rule": "max_edge",
      "original_zero": true,
      "variant": "dutch_cost_0",
      "kind": "dutch",
      "cost_rate": 0.0,
      "initial_capital": 100000.0,
      "final_capital": 115263.13928161246,
      "profit": 15263.139281612455,
      "return_on_initial_capital": 0.1526313928161245,
      "risk_turnover": 1370000.0,
      "turnover": 1370000.0,
      "risk_roi": 0.0111409775778193,
      "roi": 0.0111409775778193,
      "bet_count": 1370,
      "leg_count": 2740,
      "qualifying_signals": 1370,
      "trading_frequency": 0.9319727891156464,
      "event_hit_ratio": 0.7781021897810219,
      "positive_profit_hit_ratio": 0.7773722627737226,
      "expected_gain_per_trade": 191.17528127009984,
      "expected_loss_per_trade": 344.92886715607494,
      "avg_winning_gain": 299.7779579552516,
      "avg_losing_loss": 996.7225768548542,
      "fees": 0.0,
      "max_drawdown": 0.1619995428818291,
      "active_dates": 439,
      "scaled_dates": 0,
      "max_date_exposure": 0.0974497983779885,
      "nonpositive_complement_payout_bundles": 1,
      "roi_ci_low": -0.019846478215701,
      "roi_ci_high": 0.0424060377370689
    },
    "cost_2_final": 108877.86877716552,
    "cost_5_final": 99299.96302049531,
    "synthetic_lay_final": 160426.02553241458,
    "identity_diagnostic": {
      "original_final_capital": 0.0,
      "arithmetic_mirror_final": 200000.0,
      "arithmetic_mirror_minimum": 91890.0,
      "original_peak_capital": 108110.0,
      "max_same_date_liability": 65970.0,
      "minimum_additional_opening_cash": 0.0,
      "funding_shortfall_dates": 0,
      "mirror_funding_feasible": true,
      "original_bet_count": 859
    }
  },
  {
    "context": "P023__reference",
    "model": "Player form + projected XI + depth | Histogram gradient boosting",
    "entry_rule": "max_edge",
    "primary": {
      "Index": 219,
      "context_id": "P023__reference",
      "strategy_id": "P023",
      "model_key": "pm_hist_boost_player_squad",
      "model_label": "Player form + projected XI + depth | Histogram gradient boosting",
      "price_mode": "reference",
      "selection_rule": "max_edge",
      "original_zero": true,
      "variant": "dutch_cost_0",
      "kind": "dutch",
      "cost_rate": 0.0,
      "initial_capital": 100000.0,
      "final_capital": 70365.9259052488,
      "profit": -29634.074094751195,
      "return_on_initial_capital": -0.2963407409475119,
      "risk_turnover": 1287000.0,
      "turnover": 1287000.0,
      "risk_roi": -0.0230256985973202,
      "roi": -0.0230256985973202,
      "bet_count": 1287,
      "leg_count": 2574,
      "qualifying_signals": 1287,
      "trading_frequency": 0.8755102040816326,
      "event_hit_ratio": 0.777000777000777,
      "positive_profit_hit_ratio": 0.7637917637917638,
      "expected_gain_per_trade": 164.09398500043287,
      "expected_loss_per_trade": 346.50074554692253,
      "avg_winning_gain": 261.945672894254,
      "avg_losing_loss": 947.6127740917588,
      "fees": 0.0,
      "max_drawdown": 0.2982425247790335,
      "active_dates": 430,
      "scaled_dates": 0,
      "max_date_exposure": 0.1243431514681116,
      "nonpositive_complement_payout_bundles": 17,
      "roi_ci_low": -0.0524327877542959,
      "roi_ci_high": 0.0073477258268557
    },
    "cost_2_final": 65216.0739761478,
    "cost_5_final": 57491.29608249604,
    "synthetic_lay_final": 165886.50041848913,
    "identity_diagnostic": {
      "original_final_capital": 0.0,
      "arithmetic_mirror_final": 200000.0,
      "arithmetic_mirror_minimum": 95850.0,
      "original_peak_capital": 104150.0,
      "max_same_date_liability": 57750.0,
      "minimum_additional_opening_cash": 0.0,
      "funding_shortfall_dates": 0,
      "mirror_funding_feasible": true,
      "original_bet_count": 543
    }
  },
  {
    "context": "P025__best",
    "model": "Team + full player block | Logistic regression",
    "entry_rule": "max_edge",
    "primary": {
      "Index": 225,
      "context_id": "P025__best",
      "strategy_id": "P025",
      "model_key": "pm_logistic_team_player_squad",
      "model_label": "Team + full player block | Logistic regression",
      "price_mode": "best",
      "selection_rule": "max_edge",
      "original_zero": true,
      "variant": "dutch_cost_0",
      "kind": "dutch",
      "cost_rate": 0.0,
      "initial_capital": 100000.0,
      "final_capital": 48757.68614571406,
      "profit": -51242.31385428594,
      "return_on_initial_capital": -0.5124231385428594,
      "risk_turnover": 1402000.0,
      "turnover": 1402000.0,
      "risk_roi": -0.0365494392683922,
      "roi": -0.0365494392683922,
      "bet_count": 1402,
      "leg_count": 2804,
      "qualifying_signals": 1402,
      "trading_frequency": 0.9537414965986396,
      "event_hit_ratio": 0.7382310984308131,
      "positive_profit_hit_ratio": 0.7375178316690443,
      "expected_gain_per_trade": 194.8376087714026,
      "expected_loss_per_trade": 359.4178763065813,
      "avg_winning_gain": 305.3753114955944,
      "avg_losing_loss": 997.2836574476372,
      "fees": 0.0,
      "max_drawdown": 0.5202085768014844,
      "active_dates": 448,
      "scaled_dates": 0,
      "max_date_exposure": 0.156702508921437,
      "nonpositive_complement_payout_bundles": 1,
      "roi_ci_low": -0.0681912385401768,
      "roi_ci_high": -0.0048839829948332
    },
    "cost_2_final": 42442.52470398517,
    "cost_5_final": 32969.78254139188,
    "synthetic_lay_final": 93064.63866926145,
    "identity_diagnostic": {
      "original_final_capital": 0.0,
      "arithmetic_mirror_final": 200000.0,
      "arithmetic_mirror_minimum": 93150.0,
      "original_peak_capital": 106850.0,
      "max_same_date_liability": 57720.0,
      "minimum_additional_opening_cash": 0.0,
      "funding_shortfall_dates": 0,
      "mirror_funding_feasible": true,
      "original_bet_count": 977
    }
  },
  {
    "context": "P027__reference",
    "model": "Team + full player block | Logistic regression",
    "entry_rule": "max_edge",
    "primary": {
      "Index": 231,
      "context_id": "P027__reference",
      "strategy_id": "P027",
      "model_key": "pm_logistic_team_player_squad",
      "model_label": "Team + full player block | Logistic regression",
      "price_mode": "reference",
      "selection_rule": "max_edge",
      "original_zero": true,
      "variant": "dutch_cost_0",
      "kind": "dutch",
      "cost_rate": 0.0,
      "initial_capital": 100000.0,
      "final_capital": 6420.723474837168,
      "profit": -93579.27652516284,
      "return_on_initial_capital": -0.9357927652516282,
      "risk_turnover": 1328000.0,
      "turnover": 1328000.0,
      "risk_roi": -0.0704663226846105,
      "roi": -0.0704663226846105,
      "bet_count": 1328,
      "leg_count": 2656,
      "qualifying_signals": 1328,
      "trading_frequency": 0.9034013605442176,
      "event_hit_ratio": 0.7341867469879518,
      "positive_profit_hit_ratio": 0.7289156626506024,
      "expected_gain_per_trade": 169.33041059037936,
      "expected_loss_per_trade": 362.5629895732018,
      "avg_winning_gain": 268.0554528237617,
      "avg_losing_loss": 980.7137634960114,
      "fees": 0.0,
      "max_drawdown": 0.936142674771774,
      "active_dates": 441,
      "scaled_dates": 0,
      "max_date_exposure": 0.7275630693854256,
      "nonpositive_complement_payout_bundles": 7,
      "roi_ci_low": -0.1023951494548394,
      "roi_ci_high": -0.0390641570346583
    },
    "cost_2_final": 2419.691953966308,
    "cost_5_final": 0.0,
    "synthetic_lay_final": 101274.1458179076,
    "identity_diagnostic": {
      "original_final_capital": 0.0,
      "arithmetic_mirror_final": 200000.0,
      "arithmetic_mirror_minimum": 96010.0,
      "original_peak_capital": 103990.0,
      "max_same_date_liability": 47400.0,
      "minimum_additional_opening_cash": 0.0,
      "funding_shortfall_dates": 0,
      "mirror_funding_feasible": true,
      "original_bet_count": 780
    }
  },
  {
    "context": "P029__best",
    "model": "Team + full player block | Histogram gradient boosting",
    "entry_rule": "max_edge",
    "primary": {
      "Index": 237,
      "context_id": "P029__best",
      "strategy_id": "P029",
      "model_key": "pm_hist_boost_team_player_squad",
      "model_label": "Team + full player block | Histogram gradient boosting",
      "price_mode": "best",
      "selection_rule": "max_edge",
      "original_zero": true,
      "variant": "dutch_cost_0",
      "kind": "dutch",
      "cost_rate": 0.0,
      "initial_capital": 100000.0,
      "final_capital": 116968.37494643942,
      "profit": 16968.37494643942,
      "return_on_initial_capital": 0.1696837494643942,
      "risk_turnover": 1346000.0,
      "turnover": 1346000.0,
      "risk_roi": 0.0126065192767009,
      "roi": 0.0126065192767009,
      "bet_count": 1346,
      "leg_count": 2692,
      "qualifying_signals": 1346,
      "trading_frequency": 0.9156462585034012,
      "event_hit_ratio": 0.763001485884101,
      "positive_profit_hit_ratio": 0.7622585438335809,
      "expected_gain_per_trade": 202.1601763685485,
      "expected_loss_per_trade": 348.45856467934834,
      "avg_winning_gain": 327.45493263856724,
      "avg_losing_loss": 996.8762060647828,
      "fees": 0.0,
      "max_drawdown": 0.1397964710197732,
      "active_dates": 444,
      "scaled_dates": 0,
      "max_date_exposure": 0.0956155331510953,
      "nonpositive_complement_payout_bundles": 1,
      "roi_ci_low": -0.0192533562510067,
      "roi_ci_high": 0.0442261090920945
    },
    "cost_2_final": 110248.9997286958,
    "cost_5_final": 100169.93690208094,
    "synthetic_lay_final": 162935.99069889326,
    "identity_diagnostic": {
      "original_final_capital": 0.0,
      "arithmetic_mirror_final": 200000.0,
      "arithmetic_mirror_minimum": 83850.0,
      "original_peak_capital": 116150.0,
      "max_same_date_liability": 63610.0,
      "minimum_additional_opening_cash": 0.0,
      "funding_shortfall_dates": 0,
      "mirror_funding_feasible": true,
      "original_bet_count": 888
    }
  },
  {
    "context": "P031__reference",
    "model": "Team + full player block | Histogram gradient boosting",
    "entry_rule": "max_edge",
    "primary": {
      "Index": 243,
      "context_id": "P031__reference",
      "strategy_id": "P031",
      "model_key": "pm_hist_boost_team_player_squad",
      "model_label": "Team + full player block | Histogram gradient boosting",
      "price_mode": "reference",
      "selection_rule": "max_edge",
      "original_zero": true,
      "variant": "dutch_cost_0",
      "kind": "dutch",
      "cost_rate": 0.0,
      "initial_capital": 100000.0,
      "final_capital": 62009.53633087672,
      "profit": -37990.46366912328,
      "return_on_initial_capital": -0.3799046366912328,
      "risk_turnover": 1234000.0,
      "turnover": 1234000.0,
      "risk_roi": -0.0307864373331631,
      "roi": -0.0307864373331631,
      "bet_count": 1234,
      "leg_count": 2468,
      "qualifying_signals": 1234,
      "trading_frequency": 0.8394557823129252,
      "event_hit_ratio": 0.7568881685575365,
      "positive_profit_hit_ratio": 0.7447325769854133,
      "expected_gain_per_trade": 172.4970451971804,
      "expected_loss_per_trade": 348.8711822127225,
      "avg_winning_gain": 285.2300695644506,
      "avg_losing_loss": 955.7862980855208,
      "fees": 0.0,
      "max_drawdown": 0.3846723555085916,
      "active_dates": 432,
      "scaled_dates": 0,
      "max_date_exposure": 0.1132388382622431,
      "nonpositive_complement_payout_bundles": 16,
      "roi_ci_low": -0.0628953667083217,
      "roi_ci_high": 0.0013226099752173
    },
    "cost_2_final": 56767.00765228198,
    "cost_5_final": 48903.21463439004,
    "synthetic_lay_final": 155769.66093192674,
    "identity_diagnostic": {
      "original_final_capital": 0.0,
      "arithmetic_mirror_final": 200000.0,
      "arithmetic_mirror_minimum": 75580.0,
      "original_peak_capital": 124420.0,
      "max_same_date_liability": 62130.0,
      "minimum_additional_opening_cash": 0.0,
      "funding_shortfall_dates": 0,
      "mirror_funding_feasible": true,
      "original_bet_count": 842
    }
  }
]

Sources:
- C:\Users\melin\OneDrive\Desktop\nyu\fall 2026\Stat Arb\final_project\final_review\epl_results\metrics.csv
- C:\Users\melin\OneDrive\Desktop\nyu\fall 2026\Stat Arb\final_project\final_review\epl_results\identity_diagnostics.csv
- final_review/inverse_protocol.md
