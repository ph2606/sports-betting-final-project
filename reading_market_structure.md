# Reading notes: market structure and forecasting

All six assigned PDFs were read in full. References below use PDF page numbers. Morrison and Pike was read visually from all seven scanned pages because the PDF has no text layer. These are paraphrases of the supplied versions; applications to football are our interpretation, not results established by the papers.

## AGame-TheoreticalApproachforDesigningMarketTrading STrategies.pdf

**Actual title:** *A Game-Theoretical Approach for Designing Market Trading Strategies*. Garrison W. Greenwood and Richard Tymerski, IEEE CIG, 2008. **7 pages.**

The authors coevolve two populations of fuzzy trading rules rather than optimize a single rule population. Inputs describe narrow-range days, doji patterns, and hook days; fuzzy membership functions allow partial matches. A rule matrix produces a trading desirability score, and the example buys at the open and sells at the close when desirability exceeds 0.8. The evolutionary tournament transfers a fraction of simulated wealth between competing strategies. Of 1,600 available trading days, the first 1,000 are assigned to training and the last 600 to testing. In two illustrated test windows the fuzzy strategy earns less than the simple strategy in the rising market but preserves capital in the falling market. Training account balances partly reflect artificial tournament transfers, not just trading returns, and the selected illustrations are not a comprehensive profitability study.

**Pages and relevance:** pp. 3–5 explain features and rules; pp. 5–7 explain training and results. Useful for distinguishing model-selection objectives from actual trading profit and for benchmarking active trading against a simple policy. Coevolution would introduce substantial search flexibility for a small football sample; this paper does not establish a sports-market edge.

## Dealing with the Inventory Risk Market Making.pdf

**Actual title:** *Dealing with the Inventory Risk: A solution to the market making problem*. Olivier Guéant, Charles-Albert Lehalle, Joaquin Fernandez-Tapia. Supplied draft July 2012, arXiv version August 2012. **36 pages.**

This paper solves a market maker's finite-horizon exponential-utility problem with hard inventory limits. The reference price follows arithmetic Brownian motion and market orders arrive with intensities decreasing exponentially in the distance of the dealer's quotes from that reference. A change of variables converts the coupled HJB equations into a finite linear ODE system. A spectral characterization yields asymptotic quotes and approximations; extensions allow price drift and adverse-selection-like impact. Quotes respond jointly to inventory, volatility, arrival intensity, and risk aversion. The historical illustration uses France Telecom on one day and compares the strategy with a dealer quoting at the best bid and ask. Its execution simulation assumes full fills when trade prices reach the dealer's quote; the authors explicitly withhold full algorithmic details.

**Pages and relevance:** model pp. 4–7; approximations/extensions pp. 10–20; backtest assumptions pp. 20–23; proofs pp. 25–36. Supports explicit inventory and execution constraints. Applying its formulas to bounded, expiring match contracts would require a different price/terminal-payoff model. Quotes being touched is insufficient evidence of a real fill when queue position is unknown.

## Frequency Arbitrage.pdf

**Actual item:** *Frequency Arbitrage*. No author or date printed. **1-page teaching handout, not a complete research article.**

The handout plots S&P 500 historical volatility against sampling interval over two estimation periods and observes lower measured volatility at longer intervals. It motivates combining otherwise offsetting option positions whose delta hedges are rebalanced at different frequencies. After canceling the option positions, the remaining index exposure produces an intraperiod mean-reversion strategy. An exercise asks the reader to derive exposure proportional to the difference between reciprocal current price and reciprocal price at the start of the week. It does not supply a proof, calibrated implementation, cost analysis, or out-of-sample evaluation. The page was also inspected visually to read the graphs and formula.

**Relevance:** motivates measuring signals at multiple sampling frequencies and examining rebalancing costs. Different sampling intervals can also reflect microstructure effects. The handout cannot justify assuming football probabilities must revert or treating every volatility-frequency difference as a tradable arbitrage.

## MorrisonPike77.pdf

**Actual title:** *Kalman Filtering Applied to Statistical Forecasting*. G. W. Morrison and D. H. Pike, *Management Science* 23(7), March 1977, pp. 768–774. **7 scanned pages.**

The paper expresses a noisy time series with a time-varying mean as a linear state-space system. The latent state contains the mean and coefficients of known functions; it illustrates constant coefficients, random parameter movement, serially correlated changes, and a growth-rate model. Kalman recursion updates estimates and their uncertainty from each new observation. Ordinary least squares emerges as a special case, while fixed-dimensional recursion and moving coefficients give the filter computational and modeling advantages. An electricity-demand example initializes on fourteen annual observations and compares subsequent one-step forecasts. The reported sum of squared errors is 22.225 for the stationary linear specification, 1.286 for the stationary quadratic specification, and 0.335 for a nonstationary specification. The improvement comes from the chosen model, not a universal superiority of filtering.

**Pages and relevance:** assumptions pp. 1–3; recursion/optimality qualifications pp. 3–5; example pp. 5–7. Provides a clear basis for sequential estimation of changing latent probabilities and uncertainty. Gaussian/linear assumptions require checking after transforming bounded event probabilities; observation noise and process noise are distinct.

## Optimal FX Market Making under Inventory Risk.pdf

**Actual title:** *Optimal FX Market Making under Inventory Risk and Adverse Selection Constraints*. Sid Ghoshal and Stephen Roberts, September 2015. **12 pages.**

The authors combine an inventory-based quoting framework with a proposed adjustment for adverse selection by particular FX counterparties. They fit automatic-relevance-determination Gaussian processes to client trading behavior, compare the resulting distributions using Bhattacharyya distances, and group brokers using Bayesian nonnegative matrix factorization. Their main empirical subset contains 35,001 EUR/USD trades during January 2013; the clustering application uses 25 broker connections. A Gaussian entropy measure is proposed as a way to widen quotes for less predictable clients. The crucial premise that high entropy identifies adverse selectors is an assumption, and the functional form of the quoting adjustment is left as an open question. The paper provides behavior analysis and a proposed integration, not a completed out-of-sample trading-profit demonstration.

**Pages and relevance:** framework pp. 2–3; data/features pp. 3–5; empirical analysis pp. 6–10; proposed adjustment p. 11. Future-return and forward-volatility features are retrospective diagnostics, not contemporaneously available inputs. For betting, news shocks and stale quotes create analogous adverse-selection concerns; counterparty-specific FX models cannot be reproduced without equivalent private data.

## TimeSeriesPredictionbyKalmanSmoother.pdf

**Actual title:** *Time Series Prediction by Kalman Smoother with Cross-Validated Noise Density*. Simo Särkkä, Aki Vehtari, Jouko Lampinen, IJCNN CATS benchmark, 2004. **5 pages.**

The method combines a locally linear long-run signal with an autoregressive model for short-run residual periodicity. Kalman filtering and backward smoothing estimate the long-run signal, time-varying AR weights, and short-run component in successive stages. Cross-validation selects process-noise parameters to target the benchmark's prediction criterion. The figures illustrate reconstruction of missing intervals and prediction at the end of the series. As an interval moves away from observed data, the short-run oscillatory contribution weakens toward the long-run estimate. This is a time-series reconstruction application, not a trading backtest, and the paper does not demonstrate investment profitability.

**Pages and relevance:** p. 2 explicitly distinguishes filtering conditional on observations through the current time from smoothing conditional on the entire sample; model and tuning pp. 2–3; results pp. 3–5. Useful for separating slow latent movement from noisy prices and tuning uncertainty parameters. A tradable signal must use one-sided filtering, or smoothing restricted to data already available at the decision time. Full-sample smoothed historical signals would leak future information.
