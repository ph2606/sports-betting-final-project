# First observed prospective forecast cohort

This October 20 continuation evaluates the predictions actually released on
October 14, refreshes team/player data and releases a separate future batch
using the same frozen models when the original quality gates pass.

The original 40 probability records cover **10 distinct fixtures**, each with
four correlated model predictions. Outcomes belong to a separate append-only
ledger. Predictions, model parameters and the first pending evaluation remain
unchanged. The original release had no observed pre-match quotes or trade
ledger, so prospective trading returns and a capital curve are unavailable.

The combined report retains the complete historical price/strategy study and
all 100,000-unit graphs. Its final appendix still explains all 84 strategies.
The newest PDF and editable Word are always in [reports/latest](../reports/latest/).
See [the protocol](PROTOCOL.md) and [latest report links](../LATEST_REPORT.md).

From the repository root:

```powershell
python -m pytest epl_prospective/tests epl_live/tests -q
python -m epl_prospective.settlement --snapshot epl_live/snapshots/POST_MATCH_SNAPSHOT --evaluate
python -m epl_prospective.build --output epl_prospective/results/NEW_UNIQUE_RUN --results-snapshot RESULTS_SNAPSHOT --player-snapshot FULL_PLAYER_SNAPSHOT --evaluation EVALUATION_DIRECTORY --next-run NEXT_RUN_DIRECTORY --update-latest
```

Settlement validates raw hashes, FPL identities, explicit completion, goal
values and corroborating Football-Data results before appending anything.
The report builder refuses existing run paths, snapshots ledger bytes as of
the build, hashes consumed sources and records all forecast exclusions.
