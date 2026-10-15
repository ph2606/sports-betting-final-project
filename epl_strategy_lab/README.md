# EPL strategy laboratory: a shared 100,000-unit account comparison

This extension replays **84 distinct strategy configurations** over the same
374 archived, quoted 2025/26 fixtures. Every strategy has its own initial
100,000 monetary units. Balances carry continuously from August 15, 2025 through
May 24, 2026. There are no season resets, deposits, transfers between strategies,
or real wagers.

The comparison includes 38 configurations from the original trading studies,
12 additional configurations from the saved threshold diagnostics, and 34 new
exploratory strategies. The eight original primary cash policies remain in the
catalog and graph even though their curves coincide. Repeated season/scope rows
from the earlier studies describe the same rules rather than additional
strategies. Previously reported cost shocks remain sensitivity scenarios in
`epl_robustness`; pending prospective policies have no settled history to replay.

The main deliverables are a single chart containing **every strategy**, an
offline interactive version of that chart, full trading metrics and an appendix
at the end of the report explaining every strategy individually. The graph uses
time on the horizontal axis and account balance on the vertical axis, with a
common 100,000-unit point before the first settlement. Currency is unspecified;
these are comparable monetary units rather than a claim about USD execution.

- [All 84 strategies in one graph - PNG](results/20261015T040052Z_100k84/figures/all_strategies_100k.png)
- [Interactive comparison - download and open in a browser](results/20261015T040052Z_100k84/figures/all_strategies_100k.html)
- [Complete report and final appendix - PDF](results/20261015T040052Z_100k84/report/strategy_lab_report.pdf)
- [Editable report - Word](results/20261015T040052Z_100k84/report/strategy_lab_report.docx)
- [Report and appendix - Markdown](results/20261015T040052Z_100k84/report/strategy_lab_report.md)
- [Every strategy's metrics - workbook](results/20261015T040052Z_100k84/report/strategy_lab_overview.xlsx)
- [Full machine-readable metrics](results/20261015T040052Z_100k84/metrics.csv)
- [Independent cashflow and legacy-policy audit](results/20261015T040052Z_100k84/independent_audit.json)

## What has been added

The new rules include always-home/draw/away and market favorite/underdog
benchmarks; model favorites; equal-weight probability ensembles; dynamic 1%
stakes; eighth-, quarter- and half-Kelly sizing; a 10% date commitment limit;
six-of-eight model consensus; outcome-specific value rules; a 10% edge threshold;
and a fixed decimal-odds eligibility range. Exact parameters, stable IDs and
human-readable descriptions are saved in each run's `catalog.json` and final
appendix.

Each row reports hit ratio, model-implied expected gain and loss, realized
average winning and losing payoffs, trading frequency, total profit, return on
initial capital, return on wager turnover, drawdown, exposure and conditional
confidence intervals. Expected payoffs are the models' claims; they are not
validated expected investment returns. Cash policies have zero profit and
activity, with undefined per-trade ratios left blank.

The [metric definitions](../epl_strategy/METHODOLOGY.md) distinguish winning
net payoff from returned stake principal, and model expectations from observed
payoffs. The new account comparison reuses these definitions with one continuous
100,000-unit episode rather than pooling season accounts with resets.

## Reproduce

From the repository root:

```powershell
python -m pip install -r epl_strategy_lab/requirements.txt
python -m pytest epl_strategy_lab/tests -q
python -m epl_strategy_lab.build
```

To repeat the independent cashflow and original-policy equivalence audit:

```powershell
python -m epl_strategy_lab.audit epl_strategy_lab/results/20261015T040052Z_100k84
```

The builder reads frozen predictions and archived prices, creates a new
timestamped results directory, recomputes stakes against each 100,000-unit
account and saves its input/code hashes. It does not retrain models or rewrite
earlier experiments. See [the comparison protocol](PROTOCOL.md) for the
population, cash accounting and interpretation limits.

All new policies and the enlarged comparison are **retrospective exploratory
analysis**: this season's outcomes had already been inspected before these
rules were defined. Displaying all policies does not provide an independent
test or identify a validated winner. Archived best-book odds also lack verified
quote timestamps and simultaneous executable availability. The separate
append-only prospective evaluation remains the route to genuinely new evidence.
