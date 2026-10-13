# Statistical Arbitrage final project

**Current project:** [ML Sports Betting proposal — NBA and EPL](ML_Sports_Betting_Project_Proposal.pdf),
September 30, 2026, Aman Dhillon and Panagiotis Housos. Panagiotis's EPL data
collection has started in [epl_data](epl_data/README.md), using the 20 current
2026/27 clubs. See the [data overview workbook](epl_data/EPL_data_overview.xlsx)
and [starter notebook](epl_data/01_data_inventory.ipynb).

This private repository preserves the final-project documents, acquisition code,
raw source snapshots, 90 CSV/Parquet table pairs, metadata, workbook and executed
notebook. Source-specific terms remain applicable; see
[repository access and setup](REPOSITORY.md) before sharing the data.

Clone with Git LFS to retrieve the complete datasets:

```powershell
git lfs install
git clone https://github.com/ph2606/epl-sports-betting-final-project.git
cd epl-sports-betting-final-project
git lfs pull
python -m pip install -r epl_data/requirements.txt
```

Start in `epl_data/01_data_inventory.ipynb`. The acquisition snapshot and quality
reports describe the downloaded coverage and known limitations.

## First modeling experiment

The EPL section now includes a reproducible four-family comparison of accuracy
and calibration selection, chronological feature/tuning/calibration stages,
bookmaker baselines and a held-out 2025/26 archived-price replay.

- [Findings and results](epl_modeling/results/RESULTS.md)
- [Executed modeling notebook](epl_modeling/02_epl_modeling_results.ipynb)
- [Modeling results workbook](epl_modeling/results/EPL_modeling_results.xlsx)
- [Protocol and corrected reference paper](epl_modeling/METHODOLOGY.md)
- [Code and reproduction instructions](epl_modeling/README.md)

The first run finds no validated positive betting edge. Both primary policies
hold cash; secondary fixed-threshold returns are statistically inconclusive.
The bookmaker baseline has stronger proper probability scores than either ML
branch. The research report distinguishes these findings from executable
profitability or arbitrage claims.

## Earlier reference proposal

**Recommended topic:** Cost-Aware Statistical Arbitrage in Premier League Betting Markets.

Study whether discrepancies between bookmaker consensus probabilities and prediction-market prices predict profitable pre-match trades. Test whether a small set of FPL-related player features adds value after costs. This connects your football interest to the course's mean-reversion, threshold, risk-control and backtesting themes.

- [Submission proposal — Word](project_proposal.docx)
- [Submission proposal — PDF](project_proposal.pdf)
- [Proposal — editable Markdown](project_proposal.md)
- [Complete reading guide: 33 documents, 874 pages](reading_guide.md)
- [Technical plan: models, payoff formulas, risk, execution and tests](technical_plan.md)
- [Data-source audit and feasible alternatives](data_sources_and_feasibility.md)

All supplied PDFs were read before the proposal was chosen. Individual review notes remain in the four `reading_*.md` group files; extracted text, scanned-page images and the source inventory preserve the review trail. No strategy has yet been backtested. Market availability has been checked against official documentation and public pages, but the full historical data overlap still needs a pilot acquisition. No subscription or live trade was made.

The schedule assumes eight weeks and a group of one to three. The professor's exact submission format and deadline were not included in the supplied instructions. A solo project should keep one execution venue, one selection per match and the smallest model set.

Run `python build_documents.py` from the repository root to regenerate the older
combined reading guide and Word/PDF exports after editing the earlier proposal.
The paper inventory retains the original course-workspace paths; the original
course PDF library is separate from this final-project repository.
