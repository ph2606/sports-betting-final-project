# EPL cost sensitivity and return fragility

This extension tests the same recorded strategies under explicit hypothetical
frictions and examines selected-bet calibration, odds tails and contributions
from individual dates/seasons. It preserves the previous models, forecasts,
trading decisions, metrics exports and reports.

Read the [study protocol and formulas](PROTOCOL.md). The
[audited export](results/20261015T024639.840013Z_ecce1f1b9c/audit_manifest.json)
contains 158 strategy scopes under nine assumptions: **1,422 scenario rows**.
The directory is stamped in actual UTC (October 15); the client date in New
York at this continuation is October 14. The 14 threshold-tuning reconstructions
remain in the earlier export and are excluded from this robustness analysis.

## Findings

For the first study's calibration / 5% / best-book / fixed-stake test policy,
the observed archived-price ROI is 0.4114%. A hypothetical fee of 0.5% of every
stake changes its fixed-exposure ROI to -0.0886%. A 1% reduction of winning net
payout changes it to -0.3224%. These assumptions illustrate a thin observed
margin; they are not measured bookmaker fees or executable-price estimates.

The same strategy's 20 bets at odds of at least 10 have zero wins, despite mean
forecast probability 20.29%. Their model-implied expected profit is 388.84
units and their recorded loss is 200 units. This small, inspected subgroup
illustrates how long-odds probability errors can amplify expected-return gaps;
it is not a validated reason to remove such bets from a future strategy.

Season results differ by model and staking rule. All season contributions and
leave-one-season-out summaries remain visible, including groups with positive
results in all four seasons. These are descriptive calculations on already
inspected history, not an independent validation or a newly selected winner.

## Inspect the data

- [All cost-scenario metrics](results/20261015T024639.840013Z_ecce1f1b9c/cost_sensitivity.csv)
- [Signed fee/payout break-even capacities](results/20261015T024639.840013Z_ecce1f1b9c/break_even.csv)
- [Funding audit for every scenario and episode](results/20261015T024639.840013Z_ecce1f1b9c/funding_details.csv)
- [Selected-bet probability scores](results/20261015T024639.840013Z_ecce1f1b9c/selected_bet_scores.csv)
- [Fixed odds-bin diagnostics](results/20261015T024639.840013Z_ecce1f1b9c/odds_bins.csv)
- [Date concentration and deletion summaries](results/20261015T024639.840013Z_ecce1f1b9c/date_concentration.csv)
- [Individual season contribution/deletion diagnostics](results/20261015T024639.840013Z_ecce1f1b9c/season_fragility.csv)

Every scenario retains hit ratio, expected gain/loss, observed winning/losing
payoffs, trading frequency, ROI, confidence intervals and risk/funding status.
Outcome hit ratio and profitable-trade share remain separate if fees make a
correctly selected winner lose money. Cash policies keep zero cash totals and
undefined per-trade ratios. All tables are also supplied in Parquet format.

The field `remaining_signed_break_even_fee_rate_at_haircut` means the **total**
signed fee capacity at that haircut, `(baseline_profit - haircut*winning_gains)
/ turnover`. Additional headroom beyond a scenario's existing fee is that value
minus `fee_rate`. Negative capacities mean the fixed path already loses.

## Funding and interpretation

Stakes and selections are fixed. Before any same-date result is credited, the
funding audit checks whether shadow date-start capital covers all original
stakes plus fees. All nine illustrative scenarios pass this check in this
saved dataset. The code also tests unfundable examples: they retain shadow
cashflows, disclose required extra initial capital and leave conventional
fundable-path drawdown unavailable. No stake resizing or injected funding is
silently assumed.

ROI uses original wager turnover; fee-inclusive cash outlay and its return are
separate fields. Expectations condition on the actual recorded stake path,
including baseline Kelly sizing. Pooled seasons keep four separate bankrolls.
Date/season deletions remove cashflows without refitting or resizing remaining
bets and therefore are contribution diagnostics, not alternative backtests.

## Reproduce

From the repository root:

```powershell
python -m pip install -r epl_robustness/requirements.txt
python -m pytest epl_robustness/tests -q
python -m epl_robustness.build --bootstrap-samples 1000 --seed 42
```

The builder prints a new output directory and refuses any existing path. It
checks all zero-cost baselines against saved metrics, preserves every scope,
and records source/code/output hashes. Optional `--source-results PATH` uses
another compatible saved analytics tree; `--output-dir NEW_PATH` chooses a new
export location. Nothing is downloaded, retrained or traded.

Generate the separate review report and workbook for an export with:

```powershell
python -m epl_robustness.report --results PATH_TO_NEW_ROBUSTNESS_EXPORT
```

All intervals are conditional whole-date bootstrap diagnostics, with common
draws across shocks and separate seasonal strata. They omit model fitting,
selection, cross-date dependence, execution and multiple-comparison uncertainty.
Overlapping study/season/policy rows are not independent evidence.
