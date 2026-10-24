# Fixed-parameter NBA reconstruction audit

**The supplied SVM outputs did not reproduce. Do not substitute this audit's
SVM predictions, money curves or trading statistics for the original results.**

`reconstruct.py` reads the supplied NBA notebook, raw game logs, odds database
and saved `best_params.json`. It uses the supplied two/four-feature branches
and averages ten seed-specific refits. It does not run Optuna or search features.
No supplied source file was changed. Current library versions are in `summary.json`.

The calibration logistic-regression branch reproduces the notebook's fixed and
eighth-Kelly ending balances to the cent, and matches the notebook's prediction
accuracy and calibration summary. Its two matched ledgers and derived metrics
can be cited as a **separately reconstructed audit**.

The SVM branch does not reproduce either ending balance or prediction summary;
all reconstructed SVM fits reach the supplied 200,000-iteration limit. The
original serialized models and original library versions are absent, so the
cause is not established. Its four ledger filenames begin **`unreconciled_`**.
`predictions_native.csv` and `metrics_all4.csv` contain both audit branches;
the latter explicitly marks which rows match the source outputs.

`classification_metrics_2018.csv` also reports a directly derived normalized
bookmaker-odds benchmark on the same 1,074 games. The bookmaker row is not a
newly fitted prediction model. A 1.0 guarded ECE is a bin-occupancy penalty,
whereas ordinary binary ECE is separately reported.

All amounts remain on the source's 10,000 initial-capital scale. The source
routine settles games sequentially; it does not implement EPL date-level
joint funding. Its field called `roi` is return on initial capital. This audit
also computes the distinct profit/turnover stake ROI, expected payoff
components and drawdown for the matched branch.

Run the fixed-parameter audit again with:

```powershell
python final_deliverables/nba_core_replay/reconstruct.py
```

Recalculate probability-score summaries from the existing audit outputs without
any refitting:

```powershell
python final_deliverables/nba_core_replay/reconstruct.py --summarize-existing
```
