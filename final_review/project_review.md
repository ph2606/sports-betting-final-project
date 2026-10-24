# Final project academic review

Final review: 23 October 2026, completed after the inverse experiments. This is an assessment against normal academic expectations, **not a claim about the supervisor's unpublished marking rubric or a predicted grade**. Source hashes and checked numerical facts are in `review_checks.json`.

## Completed changes and final assessment

The revised report and presentation add a funded opposite-policy experiment, preserve the original findings, answer the arbitrage component quantitatively, and conclude with a shared answer to the accuracy-versus-calibration question. The report updater puts NBA inverses before the EPL section, EPL inverses near the end of EPL results, and the shared synthesis last. It retains every original strategy definition and metric table. The revised deck contains 28 slides: 15 main and 13 appendix slides, preserving all 23 earlier slides.

The inverse audit covers **19 zero-account cases**: 17 EPL strategy/price contexts (13 main zero accounts plus four additional reference-price zero replays) and two NBA annual zero accounts. The EPL sample includes 15 distinct strategy IDs; repeated price contexts are not independent strategies. All 47 main fixed-stake EPL accounts are included as cases or controls, rather than selecting only bankrupt cases. Inverses use frozen original signals and continue after original bankruptcy with their own funding constraints.

| Completed inverse comparison | Cases | Profitable | Median end capital | Range | Interpretation |
|---|---:|---:|---:|---:|---|
| EPL 17 zero originals: quoted complement, no added cost | 17 | 2 | 62,009.54 | 0–116,968.37 | Back both alternative outcomes, total risk 1,000, start 100,000. |
| Same, 2% haircut of positive fixture net profit | 17 | 2 | 56,767.01 | 0–110,249.00 | Hypothetical cost scenario, not an observed commission. |
| Same, 5% haircut | 17 | 1 | 48,903.21 | 0–100,169.94 | Costs are included before replaying subsequent funding. |
| EPL 17 zero originals: synthetic same-back-price lay | 17 | 16 | 140,579.95 | 93,064.64–176,439.95 | Unobserved contract/prices; not an executable exchange backtest. |
| EPL nonbankrupt controls: quoted complement, no added cost | 34 | 2 | 45,269.17 | 14,325.70–107,369.72 | Important control against a selective reverse-only-winners story. |

Only two of the 13 **main** bankrupt-account complements profit; their median is 66,059.45. Including the four additional reference contexts changes the median to 62,009.54 and produces one further bankrupt complement. No zero-cost complement among all 51 EPL contexts has a conditional 95% stake-yield interval entirely above zero. Among the 17 zero originals, eight intervals are entirely negative and nine include zero; both profitable complements' intervals include zero. These intervals resample recorded cash flows by whole date, not the model fit, policy choice, bankroll sizes or bankruptcy-selection process.

P009 supplies a concrete result: the original player-form account ends at zero, but its full-horizon quoted complement still loses, ending at **92,926.75** after 1,384 signals and trades. Its hit rate is 75.43%, stake yield −0.5111%, conditional 95% interval [−3.5967%, +2.6001%], and maximum drawdown 29.63%. Model-implied expected gain/loss are 199.23/354.83 units per trade. Its hypothetical same-price lay ends at 138,377.47. Thus a high hit rate is not sufficient for profit, and the assumed contract and price materially change the apparent outcome.

The exact recorded-cash-flow mirror ends at **200,000 for all 17 EPL cases by identity**. All 17 pass the hypothetical same-date collateral check with zero additional opening cash. The actual obstruction here is the absence of the assumed opposing contract and price, not demonstrated underfunding. This finding is disclosed rather than using a hypothetical collateral objection to dismiss the result. The mirror still uses the original truncated trade path and cannot be represented as the full-horizon complementary bookmaker policy.

For NBA 2017/18, opposite-team full-horizon flat-100 accounts from 10,000 end at **11,148.07** (calibration branch) and **8,785.30** (accuracy branch). Their stake-yield intervals are [−4.8176%, +7.3270%] and [−7.3610%, +4.5328%]. Prefix-only inverses end at 9,420.33 and 8,155.98, respectively. All 18 rolling flat returns match the source's printed precision, but this is source-method/endpoint reconciliation rather than recovery of saved fitted weights. The unmatched core SVM remains explicitly source-reported.

The final qualitative finding is stronger and narrower than “reverse bad models”: the available quoted complements usually continue to lose, while an unobserved same-price lay looks much better. The experiment exposes the importance of contracts, vig, signal horizon and funding. Bankruptcy-triggered inversion remains post hoc and supplies no confirmed new alpha. The project earns academic credibility by making this distinction and preserving negative findings; no grade is promised.

Final numerical acceptance checks pass for the inventory, full-horizon mode selection, all-zero coverage, control cohort, conditional intervals, identity funding counts, arbitrage counts and NBA endpoint comparisons. The report updater compiles syntactically and writes exclusively to the new report copy. The final builder owns rendered PDF/PPTX clipping checks, source/output hashes and preservation checks; these are rerun after the review source freezes.

## Preserved pre-extension assessment

The following assessment was made against the **30 September 2026 proposal**, the then-current 22-page report and 23-slide presentation, saved NBA notebook evidence and frozen EPL results. Its recommendations document the academic rationale for the completed additions above; they are not a new request to search for favourable outcomes.

The project has a defensible result: calibration is relevant to betting decisions, but these experiments do not establish that selecting the lowest-ECE model reliably earns a profitable, executable edge. Honest negative results, a fair comparison, and a reproducible audit strengthen that result. Making historical losses appear profitable by selectively presenting inverses would weaken it.

## What is already implemented well

| Assessment dimension | Verified status | Remaining limit |
|---|---|---|
| Proposal and research question | The report asks whether selecting by calibration rather than accuracy improves betting outcomes. Common methodology precedes NBA, then EPL. | Add one final table that answers this question across the actual comparisons. |
| Authorship and structure | Aman Dhillon and Panagiotis Housos; supervisor Daniel Totouom-Tangho; required league order is present. | Retain this ordering when adding inverse slides. |
| Model selection and timing | NBA training/selection/betting periods and EPL temporal selection are distinguished. The locked EPL primary result remains cash when no rule qualifies. | Exploratory strategy expansion and bankruptcy-triggered inverses are post hoc; they are not a new untouched test. |
| Reproducibility | Original NBA results are preserved. Ten fixed-parameter LR refits reproduce the two saved accounts to the cent. SVM refits do not reproduce and hit iteration limits. | Keep the original SVM return explicitly source-reported; do not present it as independently validated. |
| Probability quality | ECE, proper scores, accuracy and market benchmarks are separated. The 2025 corrigendum to Walsh and Joshi is cited. | NBA binary and EPL three-outcome Brier/ECE definitions cannot be pooled as identical measures. |
| Financial accounting | Stake yield and return on starting capital are distinguished; NBA annual resets are not turned into a funded continuous wealth curve. | Qualifying signals, executed trades, turnover, liability and terminal wealth need equal care for inverses. |
| Scope and explanation | Team and player models, simple market rules, wealth paths, and a complete EPL strategy appendix exist. Stake rules are documented. | Add a concise shared closing synthesis; the current main deck ends on the bankrupt player example. |

## Quantitative answer to the research question

| Matched comparison | Calibration branch | Accuracy branch | Interpretation |
|---|---:|---:|---|
| NBA 2018/19 flat staking, return on starting capital | +0.98% | +25.03% | Difference −24.05 percentage points. The SVM accuracy result is source-reported and not reproduced. |
| NBA 2018/19 eighth-Kelly, return on starting capital | −35.00% | −55.11% | Calibration loses less; both lose. The same SVM reproducibility limit applies. |
| NBA nine annual LR accounts, mean annual capital return | −17.34% | −9.49% | Calibration wins 3/9 seasons; annual accounts reset. Means are not a continuous compounded investment. |
| EPL locked primary policy | Cash, 0% | Cash, 0% | No admissible positive-validation rule passes the minimum 30-bet selection condition. This is a valid primary result. |
| EPL predeclared secondary, 5% edge / best quote / fixed stake, yield on stakes | +0.4114% | −2.2453% | Difference +2.6567 percentage points; both individual 95% intervals include zero. No established betting edge. |

The EPL ECE difference (calibration minus accuracy) is −2.0438 percentage points with conditional 95% interval [−4.3677, +0.6777]; log-loss difference is −0.01994 with interval [−0.04512, +0.00576]. These intervals do not include model-refitting and model-selection uncertainty. The raw market has pooled log loss 0.96617 versus 0.96929 for the best learned model. All six newly introduced player-feature groups perform worse than their matched controls on the relevant proper-loss comparison. Neither claim means the market dominates every metric on every cohort.

The continuous EPL exploration contains **88 accounts: 24 positive, 64 negative and 13 bankrupt**. All 32 new player accounts are negative and 11 are bankrupt. In the single-season comparison there are **116 accounts: 33 positive, 75 negative and eight cash; none bankrupt**. These are correlated strategies sharing fixtures, not 116 independent experiments. The old multiple-comparison audit applies only to the original 84 strategies (75 distinct recorded paths): its global p-values versus cash are 0.3887–0.4187 and versus the market-favourite baseline 0.1457–0.1952 across block lengths 1, 3, 5 and 10. It cannot be extended by assertion to the player additions or inverses.

## Highest-priority changes

### 1. Make the opposite-policy experiment mathematically and financially explicit

Cover **all 13 bankrupt EPL accounts**: S041, S043, P009, P011, P013, P015, P019, P021, P023, P025, P027, P029 and P031. Cover the **two NBA annual 2017/18 zero accounts** as well. None of the four source core NBA 2018/19 accounts ends at zero.

For a binary NBA bet, the opposite is the other team at its archived quote, keeping the original signal dates. For EPL, flipping home to away is not the opposite because draws exist. A complement backs both other outcomes with a **total**, not per-leg, risk budget, preferably equal-payout Dutch stakes. A lay is a separate contract requiring actual lay prices and reserve for liability. With total risk budget B and complement reciprocal-odds sum A, the Dutch stake on outcome k is B/(O_k A). State that archived bookmaker quotes have unverified simultaneous availability.

The arithmetic identity `opposite cash flow = −original cash flow` maps an original 100,000-to-zero recorded account to 200,000. That is an identity on the original recorded bets, **not a new discovered return**, and it may require unavailable lay contracts or more opening collateral than the account has. Report this only as a labelled diagnostic. A funded replay must apply the chosen risk budget, enforce cash/liability constraints, and use the frozen full-horizon signals after the original account stops trading. Show both qualifying signals and funded trades. For example, S041 made only 670 recorded trades despite being an always-away rule over 1,470 fixtures; reversing that prefix alone cannot measure the full policy.

Keep the initial primary EPL result unchanged. The inversion rule was prompted by observed ruin, so the inverse study is exploratory. Display failures as well as successes. Even a profitable funded inverse is an unconfirmed historical hypothesis until assessed on a genuinely untouched future cohort with valid quotes.

### 2. Complete the proposal's arbitrage answer

On the frozen 2022/23–2025/26 panel, **4/1,470 fixtures (0.2721%)** have mathematical three-way arbitrage flags; the largest theoretical margin is **0.6272%**. **0 are verified executable**, and all 1,470 selected quote sets lack reliable simultaneous timestamps. The common 2025/26 sample has **0/374** flags. A small count table answers the proposal more concretely than an arbitrage formula alone. Never count these candidates as earned profit.

### 3. Explain why a low ECE score need not create a profitable bet

One verified NBA example is enough. The cent-matched LR flat strategy selects 916 bets with mean selected-outcome probability **45.7821%** but observed hit rate **37.9913%**, a **7.7909 percentage-point gap**. Its ordinary aggregate 20-bin ECE is only 4.2721%. Model-implied net gain is **29.487 units/trade**; realised net is **0.107 units/trade**. Global calibration therefore does not certify calibration on the subset selected for apparent value, particularly when long odds and stake concentration matter. Label expected gains and losses as model claims; realised conditional winning gains and losing losses are separate statistics.

### 4. Improve emphasis and delivery

Lead the report with verified findings and the locked primary result. Preserve the original SVM +25.03% as source-reported evidence, with its reproduction limit beside it; it should not outrank the reproducible evidence on the cover.

Add at most **two or three main slides**: a compact NBA inverse result near NBA results, an EPL inverse result near the end of EPL results, and a closing cross-league synthesis after EPL. If only two new slides fit, combine the inverse summaries and keep the closing synthesis. Put full per-policy statistics, stake formulas, funding rejections, quote limitations and all unsuccessful inverses in the appendix. Use one sentence on each main model slide to state its outcome rule and stake size. Fixed 1,000 is 1% of **initial** 100,000, not 1% of the declining current bankroll.

## Suggested closing synthesis

“Our calibration-selected models do not deliver a stable, statistically established profit advantage over accuracy selection. Proper probability scores, prices and stake sizing jointly determine betting results. The market is a strong benchmark, the new EPL player models do not improve the matched control, and no mathematical arbitrage candidate is verified executable. Bankrupt-policy inverses test sensitivity to the direction of the signal; because the rules were chosen after observing bankruptcy, they remain exploratory. The next decisive experiment is a locked future evaluation with timestamped available quotes and a precommitted risk budget.”

## Final acceptance checks

- Keep all names, supervisor spelling, proposal date and common/NBA/EPL order correct in both formats.
- Show one capital-progression graph on a common time axis where accounts share a legitimate horizon. Do not splice independent NBA annual resets into one investable account.
- Report initial/final capital, hit rate, model expected gain/loss, realised gain/loss, executed and qualifying trades, turnover, stake yield, capital return, drawdown, stake rule and quote assumptions for every inverse in the appendix.
- Reconcile endpoints to trade ledgers; check every stake or liability fits available cash; preserve full signal dates after original ruin.
- Rebuild PDFs/PPTX/LaTeX bundle, check slide and page clipping, formulas, source links and appendix references. Keep older source artifacts intact.
- Retain the original cutoff dates and reproducibility disclosures. More favourable metrics, revised definitions or newer results must not silently replace the frozen comparisons.

This review recommends clearer inference and stronger verification, not additional strategy searching until an attractive outcome appears.
