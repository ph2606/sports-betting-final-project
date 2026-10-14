# EPL modeling and retrospective evaluation

This stage implements the September 30 proposal's accuracy-versus-calibration
comparison using the saved October 6 data snapshot. It produces actual fitted
models, held-out probabilities and archived-price betting simulations.

Start with [the results report](results/RESULTS.md),
[results workbook](results/EPL_modeling_results.xlsx), or
[executed notebook](02_epl_modeling_results.ipynb).
Read [METHODOLOGY.md](METHODOLOGY.md) for the corrected reference paper,
chronology, metrics and experimental adaptations.

From the repository root:

```powershell
python -m pip install -r epl_modeling/requirements.txt
python -m unittest discover -s epl_modeling/tests -p 'test_*.py' -v
python -m epl_modeling.experiment --trials 12
```

The runner creates CSV/Parquet result tables, model bundles, validation choices,
source/feature audits, figures, a workbook and an executed notebook. The seed,
package versions and source/input hashes are recorded in `results/run_metadata.json`.
The run performs no fresh source downloads or betting transactions.

Both branches use the same disjoint season roles: training 2014/15–2020/21,
tuning 2021/22, probability calibration 2022/23, family selection 2023/24,
betting-rule validation 2024/25, final test 2025/26. The 50 observed 2026/27
matches are a separate frozen-model monitoring sample.

The current-club cohort is preserved. Historical opponents can belong to clubs
outside today's Premier League; the model needs their earlier match histories
to evaluate the requested clubs' fixtures. Player predictors, where selected,
use past contributions rather than current squad/injury snapshots.

Prices have no trustworthy individual quote timestamps. Strictly earlier-match
features therefore do not prove availability before each archived price.
Performance is a hypothetical archived-price replay. Mathematical arbitrage
candidates are not verified executable opportunities. This initial study uses a
small search budget and one held-out season, so its report states the practical
limits of its conclusions.

## Separate rolling feature study

[Read the second study](ablation_results/ABLATION_RESULTS.md),
[open its workbook](ablation_results/EPL_feature_ablation.xlsx), or inspect
[executed notebook 03](03_epl_feature_ablation.ipynb).

```powershell
python -m epl_modeling.ablation
```

This runner preserves the first experiment and writes to `ablation_results/`.
An audited in-memory overlay reconciles early FPL opponents, keeping original
acquisition files unchanged. Four fixed source-performance groups (team,
team+xG, team+player, combined) share the same coverage controls and match
populations. Logistic and regularized market-residual models are evaluated
across four rolling seasons, with raw and temperature-only market benchmarks.

The [locked ablation protocol](ABLATION_PROTOCOL.md) records exact features,
chronological roles, preprocessing, search grid and uncertainty definitions.
The new historical study is exploratory; 2025/26 is not a fresh holdout.
The [prospective evaluation plan](PROSPECTIVE_PROTOCOL.md) defines a separate
future test requiring timestamped source availability, prices and forecasts.
No prospective forecasts or live-feed deployment are included in these results.
