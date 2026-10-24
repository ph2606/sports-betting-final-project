# Joint NBA and Premier League final project

Authors: **Aman Dhillon** (NBA) and **Panagiotis Housos** (Premier League).
Supervisor: **Daniel Totouom-Tangho**.

The submission files are in **`deliverables/final/`**:

- `Final_Report.pdf`: the compiled 22-page report.
- `Final_Report.tex`: the editable LaTeX main source, with its tables and figures.
- `Final_Report_LaTeX.zip`: portable source bundle for the complete report.
- `Final_Project_Presentation.pptx`: editable presentation, 12 main slides and
  11 appendix slides.
- `Final_Project_Presentation.pdf`: matching native PowerPoint PDF.

Both first pages contain both authors and the supervisor. Main sections are
ordered **common methodology, NBA results, Premier League results**. Appendix
material retains the NBA capital rules before the complete EPL strategy catalog.
Every strategy includes its entry condition and requested money/capital limits.

The joint report follows the actual September 30 NBA/EPL proposal, rather than
the older EPL-only proposal. The source NBA material is read from `ML Sports/`.
Mac resource-fork copies and `.DS_Store` files are not analytical inputs.

## Evidence handling

The NBA notebook's original four 2018/19 financial outcomes and nine independently
restarted annual results are preserved. A fixed-parameter audit reproduced both
logistic-regression financial results to the cent; the SVM did not reproduce.
Its original numbers therefore remain explicitly source-reported. The refitted
SVM diagnostics are prefixed `unreconciled_` and are not used as original results.
The notebook's additive plot of independently restarted seasons is not presented
as continuous, self-funded wealth.

NBA source "ROI" is profit divided by initial capital. The report calls that
capital return, separately from profit/turnover stake ROI. NBA 20-bin ECE has
an occupancy penalty, while EPL mean classwise ECE uses ten bins. The report
does not pool these scales or assume identical settlement conventions.

The first EPL accuracy/calibration comparison is separated from its later,
exploratory player-feature and strategy studies. EPL forecasts and operational
status retain their saved October 20 evidence cutoff; this compilation does not
settle later fixtures or issue new forecasts. Existing edited presentations and
the data overview workbook are left untouched.

## Reproduce

For the source ZIP, extract all files and compile `Final_Report.tex` with
**XeLaTeX**, three times, to resolve references. On Overleaf select XeLaTeX;
the fonts fall back to Latin Modern when Windows fonts are unavailable.

For the complete source-linked assembly, retain the original repository data
and supplied NBA files. Windows with Microsoft PowerPoint is needed for the
editable deck's native PDF and text-layout audit; XeLaTeX is needed for the report.

```powershell
python -m pip install -r final_deliverables/requirements.txt
python -m final_deliverables.build --output final_deliverables/results/NEW_UNIQUE_RUN
```

The builder refuses existing final run directories. `--draft` is available for
iterations outside the repository. `--publish` writes a new `deliverables/final`
folder only when none exists, preserving any existing edited submission files.
No new model-family search, strategy optimisation or forecast release occurs.

Each versioned run contains the report, presentation, numerical tables, source
evidence and an independent audit. The manifest hashes consumed files and all
outputs, and verifies preservation of the user-edited data overview workbook.
