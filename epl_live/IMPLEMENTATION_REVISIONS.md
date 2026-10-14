# Implementation revisions

The model alternatives, training seasons and scoring roles remain those in the
committed prospective protocol. Implementation checks can change without
replacing an earlier forecast, source capture, model or outcome.

## v1: initial release, October 14, 2026

The initial run `20261014T092230.366245Z` released 40 logistic forecasts, with
no observed market quotes or settlements. The independent audit reproduced all
feature values and probabilities and verified 672 new response hashes, 6,522
historical response hashes, eight model hashes, the market calibrator and the
executed code. [Release validation](validation/release_validation_20261014.json)
records these checks. The byte-identical executed sources and protocols are
retained in [implementations/v1](implementations/v1/manifest.json); that directory
is a provenance archive, not an alternate runnable package.

## v1.1: safeguards for later runs, October 14, 2026

The active runner now verifies the saved training input, training-code hashes,
all eight candidates and the separate market temperature calibrator before a
release. The training module is unchanged; the runner performs this complete
validation after obtaining the cached model directory.

Before and after constructing features, it hashes a conservative inventory of
every possible historical E0, Understat and reconciled-FPL file input, including
optional evidence paths and both processed table formats. A changed or added
path stops release. The preserved inventory's hash and actual observation time
are included in future forecast provenance. Some inventory files are optional
or bypassed by source preference; inclusion does not claim their values enter
every model. This check does not establish historical publication times.

Settlement additionally requires an outcome's season and both club identities
to agree with the released forecast, including outcomes already in the ledger.
Run reports use the actual run date and observed settlement count. The new
runner includes its validation helper in its executed-code hash.

The v1 ledger, frozen models, first run, report inputs and its pending evaluation
are preserved. No v1.1 forecast has been released yet. Later records retain their
own code hash, so these revisions do not change the provenance of the first 40
forecasts.
