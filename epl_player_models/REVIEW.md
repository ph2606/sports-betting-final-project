# Player-model results and report reproduction

The canonical report is the presentation revision in
[`results/20261020_player_models_review`](results/20261020_player_models_review/).
The fitted study remains frozen in
[`results/20261020_player_models`](results/20261020_player_models/).

The revision shows the actual player-history coverage measures for both sides
in all four evaluated seasons, escapes literal pipes in Markdown table cells,
and states the observed results and role-coverage limitations. Its 126 retained
analytical files—including all fitted bundles, features, predictions, accounts
and the 80-record player-model forecast ledger—are byte-identical copies of
the initial export. They are the same forecasts, not 80 further releases.
The initial report is kept as an earlier rendering; use the reviewed report.

To reproduce the reviewed presentation without fitting or forecasting again,
choose a new output path:

```powershell
python -m epl_player_models.report_review --source epl_player_models/results/20261020_player_models --output epl_player_models/results/NEW_REVIEW_RUN
```

The base `epl_player_models.report` command mentioned in the original report
renders its original presentation. The `report_review` entry point applies
the coverage and Markdown corrections. Add `--update-latest` only when making
the new rendering the stable latest copy. Both builders refuse an existing
output run directory.

For a full new model study, follow [README.md](README.md) and the
[locked protocol](PROTOCOL.md). The pre-fit protocol commit is
`5a4fa559405eaabf520d1beac30a8766e0f73a48`.

The observed historical evidence does not support the expanded player models:
all six player-based variants have worse pooled log loss than the matched
team control of the same family. All 32 new continuous four-season strategies
lose money; 11 exhaust their cash. Annual and single-season diagnostics,
including any positive returns, remain visible. No model or policy is
promoted on these already examined outcomes.
