# EPL archived price sensitivity

This continuation replays every available frozen rule at Bet365's recorded
prices and separates quote uplift from model-probability claims. It covers
84 single-season, 56 continuous four-season and 224 independent annual accounts,
in three modes: original, reference replay and fixed-exposure repricing.

The [protocol](PROTOCOL.md) explains funding checks, metrics, probability
decomposition, bookmaker concentration and descriptive same-book closing odds.
Historical quotes have no individual verification clocks. Fixed-exposure
cashflows that cannot finance later stakes are marked as unfunded shadows;
their ordinary capital/risk statistics are withheld.

The stable newest report is always in [reports/latest](../reports/latest/).
Its final appendix explains all 84 strategies. The continuation preserves the
original all-84 graph and 56-rule four-season graph, then adds the complete
56-rule reference-price graph, each account starting independently at 100,000.

```powershell
python -m pip install -r epl_execution/requirements.txt
python -m pytest epl_execution/tests epl_strategy/tests/test_metrics.py
python -m epl_execution.build --output epl_execution/results/NEW_UNIQUE_RUN --update-latest
```

The builder refuses to overwrite any completed or partial run. Output tables
include all required hit ratios, expected and observed gain/loss, frequency,
ROI and applicable capital/risk measures. Full bets and date-level ledgers are
CSV/Parquet; `report/execution_overview.xlsx` keeps review sheets compact and
lists the external ledger paths and hashes. The canonical completed run is
linked from [LATEST_REPORT.md](../LATEST_REPORT.md).
