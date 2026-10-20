# Player-driven EPL models

This study adds player-form, projected-XI and squad-depth match-outcome models,
compares them with matched team controls, and preserves the earlier project.
Eight learned variants cross four fixed feature groups with logistic regression
and histogram gradient boosting. The [locked protocol](PROTOCOL.md) specifies
identity rules, timing, search grids and chronological roles.

Historical evaluation uses the same 1,470 quoted fixtures in four seasons.
Raw whole-league player history supplies historical opponent context while the
current focal-club list remains unchanged. Projected XI strength uses past
appearances/minutes, not the target lineup or target minutes. Archived role
metadata and unobserved availability remain limitations.

Thirty-two additional strategies receive full gain/loss, hit ratio, frequency
and risk statistics. Combined money-versus-time graphs include all 116 common
2025/26 accounts and all 88 compatible four-season accounts, each starting at
100,000. The final appendix explains every old and new strategy.

The newest combined report is always in [reports/latest](../reports/latest/).
See [LATEST_REPORT.md](../LATEST_REPORT.md) for the canonical completed run,
workbook and interactive graphs. A separate player-model forecast ledger keeps
new future predictions apart from the original live study.

```powershell
python -m pip install -r epl_player_models/requirements.txt
python -m pytest epl_player_models/tests -q
python -m epl_player_models.build --output epl_player_models/results/NEW_UNIQUE_RUN --update-latest
```

The builder refuses existing run paths and records source/code hashes, fitted
artifacts, feature coverage and independent audits. All historical results are
exploratory; no new model is selected using the already examined evaluation
outcomes. Future model fitting uses seasons through 2025/26 only, with 2026/27
records restricted to lagged future-fixture features.
