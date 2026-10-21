# Short presentation

The revised deck contains **six main slides only**:

1. What has been implemented.
2. Money progression of all 116 strategies from 100,000 initial capital.
3. Best learned prediction model, its results and trading rule: S029.
4. Simplest prediction model and trading rule: S033.
5. A model using team performance: S017.
6. A model using player performance: P009.

The remaining slides are the requested appendix: a plain capital-allocation
guide and grouped explanations of all 116 saved strategies. Paired IDs share
the same entry conditions but have their own separately labeled stakes.
Full individual descriptions, examples and exact configurations remain in notes.

The main model pages explicitly state when to bet and the 1,000 requested stake
per bet: **1% of the initial 100,000**, rather than 1% of changing capital.
The appendix also explains current-cash percentages, Kelly sizing, per-bet
limits, date-wide limits and proportional scaling when there is insufficient cash.

The money chart uses 2025/26 because all 116 strategies have that common season.
The four model pages explicitly label their four-year prediction and trading
statistics. "Best" means lowest pooled prediction loss among the learned models,
rather than the highest ending trading account. No strategy or result is changed.

The shortened files use **`EPL_Project_Presentation_Short.pptx`** and **`.pdf`**
in `presentations/latest/`. The earlier full PowerPoint was open and locally
modified when this revision began, so it remains untouched.

Reproduce with Windows, installed PowerPoint and the existing project environment:

```powershell
python -m epl_presentation.concise --output epl_presentation/results/NEW_SHORT_RUN --publish
```

This writes a new immutable run, checks the statistics and actual PowerPoint
layout, then publishes the four short-version companion files and
`presentations/latest/short_manifest.json`. It does not replace the full deck,
its manifest or any locally edited PowerPoint.
