# Technical plan and scope decisions

Companion to `project_proposal.md`. These are proposed research specifications, not fitted models or observed trading results. Dates, budgets and the eight-week schedule are working assumptions because the supplied assignment did not specify a deadline, format or data budget.

## 1. The economic comparison

Use one outcome per fixture initially: home win in regular time, including the applicable stoppage-time treatment. Match the event definition before prices. Home-win NO is draw OR away win. Do not mix three-way match results, draw-no-bet, qualification, handicaps, or season-winner markets.

For bookmaker b, let O[b,H], O[b,D], O[b,A] be decimal odds. The baseline reference is:

`q[b,k] = 1 / O[b,k]`

`p[b,k] = q[b,k] / (q[b,H] + q[b,D] + q[b,A])`

Average these normalized vectors across contemporaneously available, eligible bookmakers with equal weights fixed in advance. This keeps the three outcome probabilities summing to one. Exclude stale or incomplete three-way quotes. If a sportsbook is the execution venue in the separate baseline, exclude it from the reference to reduce circularity. A sensitivity check may use a different overround-removal method, logged as an additional research trial.

This estimate can be biased by bookmaker pricing and favorite–longshot effects. Different bookmakers may also share information or feeds; their quotes are not independent repeated measurements of truth. The prediction market can be better informed than the consensus.

## 2. Causal filtering and a falsifiable adjustment model

Let `u[t] = logit(p_consensus_home[t])`. Use a scalar local-level state-space model for the filtered reference:

`x[t] = x[t-1] + w[t]`

`u[t] = x[t] + v[t]`

Fit process and observation noise using training data, then run forward updates. Do not apply a full-sample smoother to historical trading decisions. Keep raw consensus as the essential benchmark. The latent reference is uncertain and may jump around lineup news; smoothing can make it slower rather than better.

Let `m[t]` be a valid prediction-market YES midpoint and define:

`d[t] = logit(m[t]) - x_filtered[t]`

Use logits only away from zero and one under a fixed clipping rule; never alter the actual execution prices. Estimate an interpretable pooled adjustment regression for the subsequent prediction-market price move, controlling for current discrepancy, recent sportsbook movement, and time to kickoff. Fit a corresponding sportsbook-move regression to determine which venue adjusts. A residual AR(1) model can describe persistence within fixture windows; never concatenate the end of one match with the start of another.

Evidence that `d` shrinks is insufficient: the sportsbook can move toward an unchanged prediction quote. The primary target is a subsequent prediction-market price move and its net realizable payoff. Estimate on fixed elapsed-time horizons; do not use a future quote merely because it is the closest timestamp. Treat OU dynamics as a local diagnostic only if supported. A half-life longer than the available holding window is an argument against entering, not a reason to extend exposure beyond the pre-registered deadline.

The primary forecast horizon is 30 minutes. A price-momentum regression using the same horizon supplies a simple alternative explanation. Do not impose permanent mean reversion on the latent match probability or describe binary settlement as proof of pre-kickoff cointegration.

## 3. Trading policy and cash ledger

Observe from T−240 minutes through T−5 minutes, where T is the latest known kickoff. Consider entries on a five-minute grid only when at least 30 minutes remain before the planned exit cutoff. Start with at most one round trip and one side per fixture. Use a fresh order book when available.

For side s in {YES, NO}, the early-exit decision quantity is:

`forecast_net_gain[s] = E[exit_bid[s] at planned horizon | information now] - entry_ask[s] - entry_fee[s] - expected_exit_fee[s] - slippage_buffer[s]`

The exit-bid forecast can be obtained from the predicted midpoint and a conservative spread estimate fitted on training data. Its error distribution must also be estimated on earlier data. Enter only if forecast net gain exceeds an uncertainty threshold. Buy NO when the home-win YES quote is sufficiently expensive; this avoids assuming unrestricted naked shorting. NO bid and ask must be observed or derived correctly from the complementary book, not approximated by one minus a displayed YES last trade.

Candidate uncertainty multipliers will be limited to {1, 1.5, 2}. Compare raw consensus, filtered consensus, and filtered consensus with FPL features, giving nine primary configurations. Fix the observation window, horizon, stake caps, and other rules before validation. A momentum benchmark is not another open-ended parameter search. Log every later change as a new trial.

Exit at the first eligible observation where forecast remaining net gain is nonpositive, after 30 minutes, on an adverse executable-bid movement of $0.10 per share, or by T−5, whichever occurs first. The stop is a simulation rule, not a guaranteed fill or maximum loss. A jump can cross it. If the exit book is unavailable, preserve the holding, record the failure, and settle or liquidate later under the recorded market rules. Report these accidental in-play holdings separately.

Realized round-trip P&L is:

`quantity × (actual_exit_bid - actual_entry_ask) - actual_entry_fees - actual_exit_fees`

Settlement P&L is a different object:

`quantity × (realized_contract_payout - entry_ask) - fees`

For a sportsbook held to settlement with stake S and decimal odds O:

`P&L = S × (O × outcome_indicator - 1)`

The sportsbook's quoted odds already incorporate its margin; do not subtract the overround again as a separate fee. Do not use de-vig probabilities as achievable odds. Keep cash, holdings, tied-up capital, settlement timing, venue balances and fees explicitly. A reduction in a statistical residual is never booked directly as profit.

## 4. A separate exact-payoff diagnostic

For the same home-win event, the following are theoretical cost tests for fully matched state-contingent payoffs:

`cost_1 = 1/O_H + prediction_NO_ask + all_costs`

`cost_2 = 1/O_D + 1/O_A + prediction_YES_ask + all_costs`

In the first case a sportsbook stake of `1/O_H` pays $1 on home win, while one NO contract pays $1 otherwise. In the second, stakes `1/O_D` and `1/O_A` jointly pay $1 if the home team does not win, while one YES contract pays $1 on home win. A cost below $1 leaves a positive normal-outcome surplus. For example, entirely hypothetical odds O_H=2.00 and NO ask=$0.47 cost $0.97 before fees; $0.02 of aggregate cost leaves $0.01. This is algebra, not an observed opportunity.

Calculate every payoff including fees, stake rounding, currency/collateral conversion, and settlement delays. Check postponement, void, abandonment, correction and dispute rules. Only call the package locked-in for the explicitly matched states once all legs are actually executable and funded. Otherwise report a quoted opportunity with execution or settlement basis risk. Sportsbook stake limits and rejected bets can prevent completing the package. No de-vig probability appears in these executable cost tests.

This diagnostic is a small benchmark. The main one-venue convergence strategy carries event risk and is a statistical relative-value strategy, not a guaranteed arbitrage or a formally proved asymptotic statistical-arbitrage process.

## 5. FPL connection with a small feature set

Use the market-only model as the main baseline, then add at most three pre-specified predictors:

1. Difference between home and away teams in the contribution of expected regular players missing from the confirmed starting lineups. Define regular-player weights from the preceding five completed team matches' minutes; weight attacking contribution from lagged goals and assists per 90, with shrinkage for few minutes.
2. Difference in lagged team attacking contribution, aggregated consistently over those prior matches.
3. Difference in rest days, calculated from fixtures already played and their completion times.

Lineup information enters only after an independently recorded publication time. Before that, use a missing-lineup indicator rather than the later confirmed team. Exclude the current match's points, minutes, goals, assists, and `xP`, and exclude season-final aggregates. Do not treat a current injury flag as a historical snapshot. FPL points and ownership are not themselves outcome probabilities. If historical lineup timing is unavailable, restrict the historical model to verifiably lagged features and keep the lineup hypothesis prospective.

Fit the small augmented regression with regularization selected inside the training period; do not add a separate high-dimensional football prediction project. Improvement must appear in a paired comparison on the same fixtures, trading clock, fees and risk budget. Better Brier/log loss for a separately fitted settlement-probability model would be secondary evidence; it does not establish that an early-exit strategy makes money.

## 6. Risk and portfolio construction

Use an illustrative $10,000 simulated bankroll. Cap premium plus entry fees at 0.5% of current equity per fixture and aggregate committed premium plus entry fees at 5%. Use fully funded positions and no assumed cross-platform margin offsets. On observed books, limit order size to a conservative fraction of displayed depth and report sensitivity. Where depth is missing, report a one-contract hypothetical execution scenario without capacity claims.

For a position held to settlement, one binary event with probability p and quantity q has conditional payoff variance `q^2 × p × (1-p)`, before uncertainty about p. Use this for settlement exposure and stress tests. For the planned pre-match trade, forecast holding-horizon mark-to-market covariance from earlier quote changes; apply a common variance budget across strategies. For example, pre-register a 0.5%-of-equity upper bound on forecast portfolio standard deviation at the holding horizon, subject to the stricter cash caps. Such a model-based constraint is not a guarantee during news jumps.

If multiple selections per match are later added, their payoff covariance must reflect mutually exclusive outcomes: `diag(p) - p p'`, followed by the actual position/payoff mapping. Do not count three selections as three independent bets. Across fixtures, retain matchweek blocks and stress simultaneous losses. Include maximum drawdown, worst matchweek, tail loss and venue/fixture concentration; low estimated variance alone is inadequate.

## 7. Data gates and backtest design

Week 1 starts with 20 fixtures for schema and timing validation, not model selection. Target at least a few hundred distinct fixtures if historical overlap permits; this is an acquisition target, not a power guarantee. Produce a coverage table by season, venue, book and time-to-kickoff, including failed matches. Determine the minimum detectable effect from match-level variability; minute counts cannot substitute for independent fixtures.

Create a 60/20/20 chronological split with entire matchweeks assigned to one partition. Within the initial 60%, use expanding-window estimation checks. Choose the configuration in the validation 20%, then freeze its specification and use the last 20% once. If refitting on training plus validation before final testing, fix that procedure in advance. Purge observations whose forecast/holding intervals overlap a partition boundary. In a later prospective phase, all parameters and data-cleaning choices must be frozen before the first test quote.

Use backward as-of joins with both publication and retrieval clocks; do not use a historical closing quote to decide an earlier entry. Fee schedules must be correct for the market and date. With candles, use only completed periods, enter after signal formation, and avoid choosing within-candle best prices. A candle-only execution result remains conditional on price availability and size assumptions. The prospective book sample should test those assumptions, not merely display attractive examples.

Primary outcome: mean net P&L per eligible fixture on the fixed capital policy, including zero on no-trade fixtures, with matchweek-block bootstrap confidence intervals. Also report P&L per trade, return on total bankroll, profit divided by gross stakes/turnover, peak and average committed capital, trade counts, turnover, drawdown, tail loss, and failed exits. If reporting Sharpe, use a defined daily or weekly portfolio-return series including no-trade periods and qualify short-sample annualization. Do not multiply independent-bet assumptions by thousands of correlated quote observations.

Stress fees, one and two additional quote-interval execution delays, worse spreads/slippage, stale-quote cutoffs, and conservative fill sizes. Inspect favorite/underdog and pre/post-lineup subsamples descriptively; avoid selecting the best subgroup after seeing the test. PBO may be calculated only if a sufficiently long synchronized candidate-return panel exists; it is an optional selection diagnostic and is not a loss probability.

## 8. Minimum deliverable and extensions

The preferred study is one prediction venue, one binary selection per fixture, one horizon, three small model variants, and a separate arbitrage screen. Deep RL, neural networks, copulas, wavelets, high-frequency market making, in-play goals/red cards, and player props are outside the initial scope. Their cost, sample, and execution requirements would distract from the main test.

If historical intraday sportsbook data are unaffordable or incomplete, the baseline becomes hold-to-settlement betting at a documented pre-closing bookmaker collection, with a leave-one-book-out reference and lagged football features. Closing prices serve as later diagnostics, never earlier predictors. The prediction-market component then uses a prospective synchronized sample and is labeled a pilot if too small. Report this scope change explicitly rather than claiming that a static baseline answers the intraday question.

Only after the core is complete should the group add a second venue or a finite-horizon optimal-stopping extension. The eight-week schedule and group-size limit appear in the proposal. The exact assignment's grading rubric, required length, and deadline remain unspecified.
