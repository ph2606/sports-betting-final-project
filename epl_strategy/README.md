# EPL trading strategy analytics

Every saved trading policy now has hit ratio, expected gain/loss, trading
frequency, realized payoff and risk metrics, with [explicit definitions](METHODOLOGY.md).
The extension preserves the original models, decisions, results and research draft.

The [October 14 export](results/20261014T095929.849994Z_4c6add9911/audit_manifest.json)
contains 172 strategy/scope rows:

| Scope | Rows | Role |
| --- | ---: | --- |
| First study | 48 | Validation, locked test and partial monitoring kept separate |
| Source ablation | 88 | Eleven variants × four outer seasons × fixed/Kelly staking |
| Pooled ablation | 22 | Four independently funded seasons per variant/staking combination |
| Threshold candidates | 14 | Cached validation diagnostics; no new strategy selection |

All 24 first-study cash policies remain visible. A separate table covers 20
declared prospective model/staking slots; forecasts are not trades, so their
trading performance remains unavailable. Seven mathematical arbitrage screens
retain candidate counts without inventing executed profits or hit ratios.

## Inspect

- [Strategy comparison workbook](results/20261014T095929.849994Z_4c6add9911/report/EPL_strategy_metrics.xlsx)
- [Six-page metrics supplement — PDF](results/20261014T095929.849994Z_4c6add9911/report/EPL_strategy_metrics_supplement.pdf)
- [Metrics supplement — editable Word](results/20261014T095929.849994Z_4c6add9911/report/EPL_strategy_metrics_supplement.docx)
- [Metrics supplement — Markdown](results/20261014T095929.849994Z_4c6add9911/report/EPL_strategy_metrics_supplement.md)
- [All strategy metrics — CSV](results/20261014T095929.849994Z_4c6add9911/strategy_metrics.csv)
- [All strategy metrics — Parquet](results/20261014T095929.849994Z_4c6add9911/strategy_metrics.parquet)
- [Trade cashflows and expected components](results/20261014T095929.849994Z_4c6add9911/bets_enriched.parquet)
- [Matched-date equity, including inactive dates](results/20261014T095929.849994Z_4c6add9911/equity_enriched.parquet)
- [Prospective availability](results/20261014T095929.849994Z_4c6add9911/prospective_status.csv)
- [Arbitrage availability](results/20261014T095929.849994Z_4c6add9911/arbitrage_screen.csv)

The trade/equity exports contain explicitly labeled pooled views that repeat
seasonal cashflows and reconstructed tuning diagnostics. Do not sum across
strategies or scopes as though they were one account. The original 136
strategy/period rows account for 28,780 saved hypothetical trades.

Model-implied expected gain is `p*s*(O-1)`, expected loss is `(1-p)*s`, and
expected net payoff is their difference, for probability `p`, stake `s` and
decimal odds `O`. Observed average winning/losing payoffs are supplied
separately. Hit ratio uses settled bets; trading frequency uses both valid-price
opportunities and all predictions. Price coverage and activity dates remain explicit.

Additional fields include realized expectancy, profit, turnover, ROI, profit
factor, payoff ratio, capital return, stakes/odds/probabilities, drawdown,
capital exposure and conditional date-bootstrap intervals. Pooled drawdown is
the worst reset-season drawdown. No-trade cash totals/frequency are zero;
undefined hit ratios, per-trade means and ROI remain unavailable.

## Visual comparisons

- [All 22 pooled policies: ROI intervals, hit ratio and frequency](results/20261014T095929.849994Z_4c6add9911/figures/ablation_strategy_overview.png)
- [Model-implied versus realized ROI for all 30 displayed alternatives](results/20261014T095929.849994Z_4c6add9911/figures/expected_vs_realized_roi.png)

Both figures also have SVG versions in the same directory for export. All
alternatives are shown; pooled capital resets and conditional intervals remain
explicit. To generate figures for a new analytics export, run
`python -m epl_strategy.charts --results PATH_TO_NEW_ANALYTICS_DIRECTORY`.
Existing figure directories are refused.

## Reproduce without retraining

From the project root:

```powershell
python -m pip install -r epl_strategy/requirements.txt
python -m pytest epl_strategy/tests -q
python -m epl_strategy.build --bootstrap-samples 1000 --seed 42
```

The builder prints a new UTC/UUID directory and refuses to overwrite any
existing directory. Optional `--output-dir NEW_PATH` chooses another new
directory. It verifies source hashes, counts, cashflows, outcomes, opportunity
dates and bankroll conservation. Threshold candidates reuse cached predictions
and the frozen simulator to reconstruct their already recorded decisions;
fitted models are not loaded or changed.

Generate the workbook and Word/PDF metrics supplement for a new export:

```powershell
python -m epl_strategy.report --results PATH_TO_NEW_ANALYTICS_DIRECTORY
```

Positive expected ROI on selected positive-edge bets is not new evidence of
profitability. These are hypothetical archived-price cashflows, without
verified fills or separately modeled costs. Conditional intervals describe
recorded trades and omit selection, refitting and execution uncertainty.
