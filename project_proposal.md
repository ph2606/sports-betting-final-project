# Cost-Aware Statistical Arbitrage in Premier League Betting Markets

**Proposed final project — Statistical Arbitrage**  
**Focus:** Sportsbook consensus, prediction-market price adjustment, and Fantasy Premier League player information  
**Team:** One to three students  
**Prepared:** September 25, 2026

## Abstract

This project will investigate whether disagreements between traditional sportsbook odds and prediction-market prices for the same Premier League match outcome contain a profitable trading signal after costs. Motivated by the course readings on mean reversion, filtering, transaction costs, and backtest overfitting, we will estimate a time-varying reference probability from bookmaker odds and test whether prediction-market prices subsequently move toward it. The main strategy will trade fully funded home-win YES or NO contracts before kickoff, with explicit entry thresholds, a limited holding period, and a no-trade region when expected gains are smaller than trading costs and estimation uncertainty. A small set of player and team features inspired by Fantasy Premier League—prior minutes, attacking contributions, and confirmed lineup absences—will test whether football information improves the market-only strategy. We will use chronological training, validation, and testing periods, keeping all observations from each fixture together. Evaluation will distinguish price prediction from executable trading performance and report net profit, drawdown, capital usage, and uncertainty at the match or matchweek level. A separate payoff-matching calculation will identify potential sportsbook–prediction-market arbitrage, subject to compatible settlement rules and simultaneous execution. The contribution will be an empirical assessment of market efficiency and implementable relative-value trading; finding that apparent opportunities disappear after costs will also be a valid result.

## Motivation and research questions

My interest in Fantasy Premier League motivates studying how player availability, rotation, recent performance, and team news enter betting prices. The statistical-arbitrage question is whether the same football outcome is priced differently across venues, whether one venue adjusts more slowly, and whether that adjustment can be traded.

The primary question is: **Do sportsbook–prediction-market discrepancies predict subsequent executable prediction-market returns after fees and bid–ask spreads?** A secondary question is whether a small, pre-specified set of FPL-related features improves those returns beyond information already present in market prices. The null hypothesis is that neither approach produces a reliable net advantage over simple benchmarks.

## Scope and strategy

We will study Premier League regular-time match results, initially using only the binary event “the home team wins.” Its NO outcome includes both a draw and an away win. The initial execution venue will be Kalshi, subject to a data pilot; Polymarket will be a possible replication venue. A traditional sportsbook supplies reference odds and a separate hold-to-settlement benchmark. The main prediction-market strategy does not require a sportsbook cashout or an ability to short a bookmaker bet.

For each sportsbook, decimal odds for home win, draw, and away win will be converted to implied probabilities and normalized to remove the quoted overround. An equal-weighted consensus across fresh, eligible bookmakers will be the transparent baseline; it is an estimate, not known truth. A causal Kalman filter will provide a competing reference estimate. We will model the discrepancy between the prediction-market price and that reference using a small pooled adjustment model, conditional on time to kickoff. Mean reversion and which venue moves will be tested rather than imposed.

The initial observation window is four hours to five minutes before kickoff, with decisions on a five-minute grid and a maximum planned holding period of 30 minutes. Buy YES or NO only when the model predicts a sufficiently favorable future exit bid relative to the current entry ask, after both trading costs and an uncertainty buffer. Exit on signal disappearance, the holding deadline, a pre-specified adverse-price stop, or the pre-kickoff cutoff. Unfilled exits remain open in the ledger and retain settlement risk. Positions will be fully funded, with fixture-level exposure limits and a portfolio variance constraint.

The FPL extension will add only a few interpretable features, computed from information available before the decision. For example, a confirmed starter absence can be weighted by that player's minutes and attacking contribution in previously completed matches. We will compare identical trading rules with and without these features; football knowledge is a testable source of additional information, not an assumed edge.

## Data and feasibility

The intended intraday sample is the overlapping portion of the 2025/26 season, supplemented by prospective 2026/27 observations. **Historical coverage has not yet been downloaded or established.** The first milestone will audit at least 20 fixtures for matching contracts, quote timing, fees, missingness, and liquidity, then determine the usable sample.

[The Odds API](https://the-odds-api.com/liveapi/guides/v4/) documents historical sportsbook snapshots at five-minute intervals from September 2022 on paid plans. [Kalshi](https://docs.kalshi.com/api-reference/historical/get-historical-market-candlesticks) documents historical bid/ask candles, but these do not establish executable depth. Prospective order-book observations will therefore check execution assumptions. [Football-Data](https://football-data.co.uk/data.php) supplies a historical bookmaker baseline; its pre-closing and closing collections cannot replace synchronized intraday data, and affected Pinnacle quotes after July 23, 2025 will be excluded unless independently validated. [The FPL archive](https://github.com/vaastav/Fantasy-Premier-League) requires careful availability checks, particularly for potentially post-match `xP` values and newer-season updates.

If suitable intraday data cannot be obtained, the deliverable will become a clearly labeled slower sportsbook value-betting backtest plus a prospective prediction-market pilot. It will not claim that closing-only data establish intraday mean reversion. No live wagering is necessary.

## Course connection and evaluation

The project directly applies the supplied themes of mean-reversion trading, threshold and variance constraints, relative-value strategies, and backtesting. Leung and Li motivate cost-sensitive entry and exit; Martin motivates a no-trade region; Kanamura, Rachev, and Fabozzi motivate accounting for nonconvergence before a deadline. Morrison and Pike and the Kalman tutorial support sequential estimation. Dare's Treasury-futures study motivates separating signal midprices from executable bid/ask prices. The two Bailey et al. readings motivate limited model search and an untouched final test. These methods require adaptation because event contracts are bounded and expire; stock-price cointegration and perpetual OU thresholds will not be assumed.

We will reserve the final 20% of fixtures by time for testing, use the first 60% for initial estimation, and the intervening 20% for validation, keeping matchweeks intact at boundaries. Benchmarks will include no trade, a raw consensus threshold, and a simple price-momentum rule. We will report net P&L on committed capital, turnover, maximum drawdown, tail loss, exit failures, and block-bootstrap uncertainty. More frequent quotes will not be counted as independent match outcomes. All tried configurations will be logged; overfitting diagnostics will supplement, rather than replace, chronological testing.

## Deliverables and schedule

Over an assumed eight-week project, weeks 1–2 will establish data and settlement matching; weeks 3–4 will implement the baseline, filter, and cash-accounted backtest; weeks 5–6 will add the FPL comparison and cost/latency stress tests; weeks 7–8 will run the locked test and produce the report and presentation. For three students, responsibilities divide into data and market matching, modeling and player features, and execution/backtesting; a solo project will retain one venue and the simplest feature set.

Deliverables are a reproducible data dictionary and pipeline, an event-driven simulation notebook, a comparison of gross and net results, and a final report explaining whether the evidence supports a tradable effect. Success means a defensible answer to the research question, including an honestly documented negative result.

## Selected course references

1. Leung, T., and Li, X. (2014 supplied draft). *Optimal Mean Reversion Trading with Transaction Costs and Stop-Loss Exit*, especially PDF pp. 9–20.
2. Martin, R. J. (2012). *Optimal Multifactor Trading under Proportional Transaction Costs*, PDF pp. 3–11.
3. Kanamura, T., Rachev, S. T., and Fabozzi, F. J. (2011 working-paper wrapper; 2009 manuscript). *A Profit Model for Spread Trading with an Application to Energy Futures*, PDF pp. 5–14.
4. Morrison, G. W., and Pike, D. H. (1977). *Kalman Filtering Applied to Statistical Forecasting*, PDF pp. 1–7.
5. Dare, W. (2017). *Statistical Arbitrage in the U.S. Treasury Futures Market*, PDF pp. 23–34.
6. Bailey, D. H., Borwein, J. M., López de Prado, M., and Zhu, Q. J. (2014 supplied versions). *The Probability of Backtest Overfitting*; and *Pseudo-Mathematics and Financial Charlatanism: The Effects of Backtest Overfitting on Out-of-Sample Performance*.

The accompanying reading guide covers all 33 supplied PDFs; the technical plan specifies payoff accounting, model comparisons, risk limits, and the data contingency in more detail.
