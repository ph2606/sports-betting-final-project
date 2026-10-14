# EPL project draft

[PDF draft](EPL_project_draft.pdf), [editable Word draft](EPL_project_draft.docx), and [Markdown source](EPL_project_draft.md) are the English Premier League section for review, dated October 14, 2026. This is not a final submission. The PDF contains seven pages, four reused figures and three compact result tables.

From `final_project`, regenerate the documents and provenance manifest:

```powershell
python -m pip install -r epl_report/requirements.txt
python epl_report/build_report.py
```

The builder reads saved first-experiment and ablation outputs; it does not fit models, fetch data or change source/result files. It requires the existing project artifact tree and Windows Times New Roman/Arial font files under `C:/Windows/Fonts`. The pinned rendering dependencies reflect the installed environment; no modeling dependency imports are needed. Word remains editable, so later edits can change its pagination.

`report_manifest.json` records SHA-256 input/output hashes, derived numerical facts, PDF page count and word-count scope. The narrative count excludes captions, table values and references. The three CSV tables in `tables/` contain the exact displayed rounded values; full saved study tables retain their original precision. Page preview PNGs are optional inspection files, not research outputs.

The first comparison uses its locked 374-match 2025/26 test; the 1,470-match four-season source ablation is exploratory because some outcomes were already inspected. The current-club cohort has survivor/selection bias. Historical player contributions do not establish current player availability. Archived odds lack verified publication clocks or executable fills; hypothetical returns and mathematical arbitrage screening do not establish a trading edge. The October 14 operational update is explicitly separate: forty forecasts for ten future fixtures are pending, and quote-dependent alternatives are withheld. No prospective performance or NBA results are claimed.

The operational update is pinned to release `20261014T092230.366245Z` and evaluation `20261014T092819.822459Z`; it is not an automatically rolling status report. Its source summaries and the committed ledger are also hashed by the report builder. Future ledger appends do not turn pending forecasts into results within this dated draft.
