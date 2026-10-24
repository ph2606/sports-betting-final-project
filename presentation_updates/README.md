# Data-source and methods slide revision

Current files:

- [Updated PowerPoint](../deliverables/final/Final_Project_Presentation_Updated.pptx)
- [Matching PDF](../deliverables/final/Final_Project_Presentation_Updated.pdf)
- [Speaker notes](../deliverables/final/Final_Presentation_Notes_Updated.md)

Only slides 2 and 3 change. The deck retains 28 slides, all results and the
strategy appendix. The earlier open presentation is preserved; the updated
copy has a distinct filename.

Slide 2 names the sources actually used by the NBA/EPL implementation.
It distinguishes the supplied NBA CSV/database from the reference paper's
Basketball-Reference/Westgate dataset, and identifies Football-Data,
Understat, the official FPL API and the historical FPL archive for EPL.
Uncertain upstream collection and quote timing remain labelled.

Slide 3 presents feature construction, screening and sequential forward
selection, followed by classwise ECE and accuracy formulas. The supplied
seven-page supplement supports feature engineering (pp. 2–3) and feature
selection (Table 4, p. 4). It contains no explicit metric formulas or data
provider list. Classwise ECE is therefore attributed to the main paper,
section 3, equation (3), and checked against project code. The slide states
the implemented NBA 20-bin occupancy penalty and EPL three-class/10-bin
adaptation. Paper feature subsets are not presented as the project's subsets.

The [versioned export](results/20261023_sources_methods/) contains source
specifications, high-resolution and vector equation figures, slide previews,
speaker notes, the old two slide specifications, source fingerprints and a
native PowerPoint layout audit. The supplied supplementary PDF remains at
its original local location; its SHA-256 is recorded for provenance.

Build with `python -m presentation_updates.update_sources_methods` from the
repository root. Choose a new `OUTPUT` directory before a fresh build; the
script refuses to overwrite completed versioned exports. Native Microsoft
PowerPoint generates the PDF from the editable deck. The final report and
previous canonical exports are unchanged.
