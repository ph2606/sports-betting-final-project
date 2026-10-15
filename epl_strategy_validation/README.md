# Four-season strategy stability and selection audit

The latest report is always linked from [LATEST_REPORT.md](../LATEST_REPORT.md).
Open `reports/latest/EPL_Project_Report.pdf` or the editable Word file beside it.

This continuation holds the 84-strategy catalog fixed and adds two checks:

- Replay the 56 rules with available rolling forecasts across four seasons:
  1,470 matches, one continuous 100,000-unit account per strategy, plus four
  separately restarted seasonal accounts per strategy.
- Compare all 84 original 2025/26 recorded paths with cash and the market
  favorite using shared date-block resampling and an explicit adjustment for
  examining the displayed family of strategies.

The other 28 first-study configurations retain their original 2025/26 results;
earlier predictions are not invented. Every account still has hit ratio,
expected gain/loss, realized payoffs, trading frequency, return and risk metrics.
The report preserves the all-84 single-season graph, adds an all-56 four-season
graph and ends with definitions for every strategy.

These are retrospective checks of already examined history. They do not create
an independent holdout or demonstrate an executable edge. Read the
[protocol](PROTOCOL.md) for the two account designs, the conditional statistical
estimand and the limits of fixed-cashflow bootstrap inference.

From the repository root:

```powershell
python -m pip install -r epl_strategy_validation/requirements.txt
python -m pytest epl_strategy_validation/tests -q
python -m epl_strategy_validation.build
```

The builder writes a fresh immutable run. The stable report copies are refreshed
only by its explicit `--update-latest` option after all output checks pass.
