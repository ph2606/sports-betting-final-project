# Reviewed final submission

The updated [report](../deliverables/final/Final_Report.pdf),
[editable presentation](../deliverables/final/Final_Project_Presentation.pptx)
and [matching slide PDF](../deliverables/final/Final_Project_Presentation.pdf)
are in **`deliverables/final/`**. The order remains common methodology, NBA,
then Premier League. The presentation has 15 main slides and 13 appendix slides.
The complete original strategy appendix is retained.

The frozen review export is
[`results/20261023_reverse_review/`](results/20261023_reverse_review/).
Its [metrics workbook](results/20261023_reverse_review/data/Review_Metrics.xlsx)
contains the full inverse metrics and reconciliation inventories. The
[qualitative and quantitative review](project_review.md) explains the final
academic assessment and the evidence limits; no unpublished marking rubric
or grade is assumed.

## What the opposite study found

There are 19 original zero-ending account contexts: two NBA annual accounts
and 17 EPL strategy/price contexts. The 17 EPL contexts cover 15 strategy IDs:
13 contexts in the principal four-year comparison and four additional
Bet365 reference replays. They are correlated, retrospective cases, not 19
independently selected investment signals.

| Study | Initial capital | Full-horizon opposite | Result |
|---|---:|---|---|
| NBA 2017/18 calibration-feature LR | 10,000 | Back the other team at its archived odds; request 100 | Ends 11,148.07; stake ROI +1.25%; maximum drawdown 29.17% |
| NBA 2017/18 accuracy-feature LR | 10,000 | Same opposite rule; request 100 | Ends 8,785.30; stake ROI −1.37%; maximum drawdown 50.76% |
| EPL 17 bankrupt price contexts | 100,000 each | Back both other H/D/A outcomes, equal gross payouts, 1,000 total requested risk | 2/17 profit; median ending 62,009.54; range 0–116,968.37 |
| EPL 34 surviving controls | 100,000 each | Same priced complement | 2/34 profit; median ending 45,269.17 |

Both profitable EPL complement intervals include zero; neither NBA interval
excludes zero. At a hypothetical haircut of 2% or 5% of positive **net fixture
bundle** profit, EPL bankrupt-context profit counts are 2/17 and 1/17.
These are illustrative sensitivities, not verified venue fee schedules.

A separate synthetic lay assumes the original back price can be laid,
with liability 1,000 and counterstake `1,000/(odds−1)`. It profits in 16/17
bankrupt EPL contexts, but the data contain no actual lay quotes, liquidity,
or accepted fills. Back-book margin explains why the actual complementary
back quotes can perform much worse. The presentation keeps these evidence
classes explicit.

Negating the original recorded cashflows gives ending 200,000 for every
100,000-to-zero history by identity. All 17 exact recorded-exposure mirrors
pass the calculated cash-collateral check, but the counterparty contracts
and original-price lay fills remain unobserved. This identity is not counted
as newly discovered performance. Full-horizon inverses continue receiving
the frozen original signals after the original account's bankruptcy.

## Accounting and evidence

- EPL reserves all same-date bundle stakes or lay liabilities from opening
  cash, scales requests uniformly when necessary, and never reuses same-date
  winnings. NBA retains the supplied sequential game-settlement convention.
- The EPL experiment contains 51 original account reproductions, 153 full
  priced complements, 51 synthetic lays, 17 additional recorded-prefix priced
  complements and 17 exact sign-identity diagnostics. Every declared result,
  including inverse bankruptcies, is saved.
- Metrics separate event hits from positive-profit bundles; expected gain
  and loss are nonnegative payoff components under the original forecast.
  Realised average gains/losses are separate columns. Lay risk yield is not
  labelled yield on a back stake.
- Intervals resample whole match dates while holding funded cashflows fixed.
  They exclude refitting, resizing, model/strategy selection and the decision
  to investigate bankruptcy. The reversal study is not a fresh holdout.
- The EPL design was committed in `23d83be` before new EPL inverse returns
  were calculated. NBA reconstruction had already run, as the protocol
  explicitly records. No claim of prospective NBA design is made.
- All 18 saved NBA annual flat returns and feature counts reconcile to the
  unchanged source method. Saved annual fitted weights are unavailable, so
  this is source-method reconstruction. The separate core SVM refit remains
  unreconciled and is never used as verified inverse evidence.

The whole-project conclusion remains that these experiments do not establish
a stable, executable profit advantage for calibration selection. Four EPL
fixtures have mathematical arbitrage flags, zero have verified execution,
and all six new player-feature/model variants have worse pooled log loss
than their matched team controls.

## Files and reproduction

- [Frozen design](inverse_protocol.md), [design inventory](design_notes.json).
- [EPL implementation](epl_inverse.py), [independent audit](audit_epl_inverse.py),
  [boundary accounting tests](test_inverse_accounting.py).
- [EPL results and ledgers](epl_results/): compact Parquet bundle, leg, signal
  and wealth ledgers; CSV metrics and zero inventory; source/output hashes.
- [NBA implementation](nba_inverse.py), [NBA source-method reconstruction](nba_results/),
  including its independent audit and conditional uncertainty.
- [Report updater](report_update.py), [deck updater](deck_update.py),
  [submission builder](refresh_deliverables.py).

Preserve the committed exports. Recompute EPL into a **new directory**:

```powershell
python -c "from pathlib import Path; import final_review.epl_inverse as study; study.OUT=Path('final_review/reproduction_new'); study.main()"
python final_review/audit_epl_inverse.py --results final_review/reproduction_new
python -m pytest final_review/test_inverse_accounting.py -q
```

The report ZIP is self-contained for compilation: extract it, select
XeLaTeX, and compile `Final_Report.tex` three times. Submission generation
uses native Microsoft PowerPoint PDF export and checks actual text bounds.
The reviewed output manifest records inputs, output hashes, checks and
preservation of the user's edited workbook and presentations. Earlier
canonical NBA/EPL reports, source data and study outputs remain intact.
