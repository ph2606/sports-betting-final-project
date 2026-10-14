# Plan for a new prospective evaluation

Declared on October 13, 2026, before releasing any forecast under this protocol.
The first study and subsequent four-season ablation are historical research.
The 2025/26 outcomes have already been examined and cannot be called a new test.
This document is an evaluation plan; it contains no prospective predictions or
prospective performance claims. Its Git commit records the declared version.

## Population and observation window

Use the same twenty verified 2026/27 Premier League clubs. Evaluate eligible
fixtures whose kickoff occurs **after both the protocol commit and
2026-10-14 04:00 UTC**. Do not score an already-started fixture as prospective.
Include every qualifying fixture with a valid forecast and archive the reasons
for missing forecasts; do not retain only fixtures that later look attractive.
The October 6 snapshot alone is insufficient for a current live evaluation:
completed-match coverage stops on September 20.

## Fixed alternatives and chronology

The four source groups and two model types are declared in
[ABLATION_PROTOCOL.md](ABLATION_PROTOCOL.md): team, team+xG, team+player and
combined, each with logistic and market-residual models. Keep all eight as
declared alternatives; report raw and temperature-only bookmaker benchmarks.
Do not choose a prospective winner retrospectively from the new outcomes.

Fit base estimators on 2016/17–2023/24; select regularization from
`C = 0.03, 0.3, 3.0` using 2024/25 log loss. Refit base estimators and
preprocessing through 2024/25, then fit scalar temperatures on 2025/26 and
freeze them. The old test season therefore becomes calibration data for this
new protocol, not evidence for its final performance. Earlier 2026/27 results
may update lagged features but cannot update fitted parameters during this
prospective window.

## Required forecast record

Before kickoff, archive the UTC forecast creation time, fixture and provider
identities, kickoff time, model/code/configuration hashes, three H/D/A
probabilities, all feature values and latest contributing source-match dates.
Record the actual retrieval/publication availability of every source used.
The source observations and any revisions must have been available no later
than forecast creation. A historical match date by itself is not proof of that
availability. Preserve the original response bytes and their hashes.

Market-residual forecasts additionally require a contemporaneous complete
reference-book triplet, recorded with its observation time. Record best-book
quotes independently by bookmaker and outcome, including timestamps and any
available status, limits and fees. A provider's old `preclosing` field without
individual observation clocks cannot satisfy this requirement.

Commit or otherwise independently timestamp an append-only forecast ledger
before the matches start. Preserve superseded forecasts rather than replacing
them. Choose the earliest valid released forecast per model/fixture for the
primary comparison, and define any later-update analysis separately.

## Scoring and betting summaries

Primary predictive endpoint is mean multiclass log loss on the common valid
forecast population; report the full population/missingness audit as well.
Brier, accuracy, ten-bin classwise ECE and source-complete sensitivity remain
secondary. Report all declared alternatives and season/date coverage. Multiple
comparisons and calendar-date dependence must be accounted for before claiming
a winning feature group.

If prices and availability are adequately recorded, report the predeclared 5%
expected-return edge, fixed stake 10 from capital 1,000, and quarter Kelly capped
at 2% per bet. Size same-date commitments from date-start capital and report
costs and rejected fills where available. Paper-traded or quoted returns remain
separate from actual executed returns. Without verified synchronized prices,
arbitrage remains descriptive; no arbitrage profit enters the ledger.

At the end of 2026/27, publish the frozen forecast ledger, complete outcome and
coverage audit, primary/secondary scores, all declared model comparisons and
conditional uncertainty intervals. Changes to data identities, features,
model settings or scoring choices after observing these new outcomes must be
versioned as a different study rather than relabeling them as this protocol.
