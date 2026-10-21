# EPL implemented-results presentation

Open the editable [PowerPoint](../presentations/latest/EPL_Project_Presentation.pptx)
or matching [PDF](../presentations/latest/EPL_Project_Presentation.pdf) in
**`presentations/latest/`**. The presentation is dated October 21, 2026 and uses
the completed October 20 evidence snapshot. It fits no new model, changes no
trading rule and scores no additional forecast.

The deck has 18 main slides and 17 backup slides. Its opening describes only
the implemented data, modeling, account-replay and prospective pipelines.
It includes both complete 100K money graphs, the strongest learned predictor,
the strongest market benchmark, the simplest predictive model, a team model,
a player-only model and their trading statistics. Historical capital leaders
are identified separately for one season and four continuous seasons.

The backup includes metric definitions, provenance and explanations for every
S001-S084 and P001-P032 strategy. Exact configurations, complete source paths
and interpretation notes are also embedded in PowerPoint speaker notes.

Companion files in the same latest folder:

- `EPL_Presentation_Data.xlsx`: every compared probability series, all 116
  single-season and 88 continuous account metrics, exact configurations and
  full graph data.
- `EPL_Presentation_Speaker_Notes.md`: all slide notes and complete definitions.
- `all_strategies_2025_100k.html` and `all_strategies_continuous_100k.html`:
  offline interactive graphs with every strategy initially visible.

Download the PowerPoint for editing or presenting. Download the HTML files and
open them locally for interactive inspection. The PDF is exported by Microsoft
PowerPoint from the same editable deck, rather than a separate approximation.

## Reproduce

This export requires Windows with Microsoft PowerPoint installed for its native
PDF rendering and actual text-layout audit. Existing result artifacts and the
source-pinned project environment are also required.

```powershell
python -m pip install -r epl_presentation/requirements.txt
python -m epl_presentation.build --output epl_presentation/results/NEW_UNIQUE_RUN --publish
```

Completed final run paths are immutable. Draft iterations may be written outside
the repository using `--draft`. Publishing refuses to overwrite locally edited
registered latest copies. The manifest records source/output hashes; independent
checks reconcile all 19 probability-series scores, graph identities/endpoints,
featured statistics, exact catalog definitions and unique forecast counts.

Microsoft documents the native rendering APIs used here:
[Presentations.Open](https://learn.microsoft.com/en-us/office/vba/api/powerpoint.presentations.open)
and [Presentation.SaveAs](https://learn.microsoft.com/en-us/office/vba/api/powerpoint.presentation.saveas).
The deck opens without a window; the exporter closes only its own presentation.
