# Forecast release and source-quality rules

Implementation date: October 14, 2026. This supplements the previously committed
[prospective protocol](../epl_modeling/PROSPECTIVE_PROTOCOL.md), without changing
its feature groups, model alternatives, training chronology or scoring roles.

Capture public responses in a new immutable directory on each manual run. The
current FPL membership and dated source records must agree with the verified
2026/27 league. Retrieve all current player summaries before claiming complete
registry coverage. Normalize player membership from each actual fixture and
home/away indicator, rather than the player's current roster club.

For the initial release, require all core sources to validate, all player
summaries to succeed, and no unexplained FPL fixture more than six hours past
kickoff that remains unfinished. This last rule detects incomplete/outdated
schedule observations; it does not assume that any postponed match was played.
If such records exist, archive the capture and per-model exclusion reasons and
withhold forecasts until source quality is resolved. Do not backfill forecasts
for a match that has already started.

Use a seven-day lookahead and recheck eligibility immediately before appending.
All feature match dates must be strictly earlier than the target printed UTC
calendar date. Missing historical performance stays missing until the frozen
training-fitted imputer processes it; model inputs retain explicit coverage
counts and missing-history flags. Release the four logistic alternatives when
feature/schedule gates pass. A market-residual model additionally requires a
complete Bet365 triplet observed no more than **one hour** before forecast
creation. Raw and temperature-only market benchmarks require the same quote.

That limit bounds the age of our observation, not the provider's publication or
last-price-update time. Unknown publication times must remain explicitly
unverified. No quote is declared executable or simultaneously available merely
because its response was captured recently. No real betting transaction or
autonomous scheduled job is part of this workflow.

Before kickoff, append UTC creation and actual append times, complete H/D/A
probabilities, feature values, source hashes/observation times, model/code/
protocol hashes, and observed prices when applicable. A JSONL hash chain detects
edits, reordering and gaps. Do not replace an earlier forecast; preserve any
explicitly versioned later update, and score the earliest valid released
forecast per model/fixture. Publish the ledger in Git before the forecasted
matches begin to provide an independent version timestamp.

Settlement records belong to a separate append-only outcome ledger. Only a
finished source fixture with consistent goals and identity may settle an
existing forecast. No resolved matches means no observed prospective accuracy,
loss or profit estimate. Report missing forecasts, pending outcomes, source
quality gates and protocol changes rather than silently changing the sample.
