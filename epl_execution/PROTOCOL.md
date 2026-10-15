# Frozen-probability archived quote sensitivity

This October 15, 2026 continuation measures dependence on the archived quote
panel. It adds no fitted model, optimized rule, new threshold or independent
test. All 84 original configurations are preserved verbatim. The common 2025/26
comparison has 84 accounts; 56 compatible rules also have one uninterrupted
2022/23–2025/26 account and four independently initialized annual accounts.
These are 364 original account scopes, each examined in three modes (1,092 rows).
Every account starts independently with 100,000 monetary units.

## Three questions, three modes

1. `original` copies the exact saved account metrics and original catalog.
   Its price mode may already be reference: eight original configurations
   provide exact identity controls. Original files and results remain frozen.
2. `reference_replay` changes only the configuration's `odds_mode` to
   `reference` (archived Bet365). It reruns price-dependent outcome selection,
   strict edge thresholds, odds bands, consensus vetoes, sizing and joint
   date-level cash allocation. Model probabilities, learned information sets
   and all other rule parameters stay fixed. Changed selections and capital
   therefore make the profit difference broader than pure quote uplift.
3. `fixed_exposure_reference` preserves original selected outcomes, allocated
   stakes and probabilities and substitutes Bet365 payoff odds. Eligibility,
   Kelly fractions and date caps are not reapplied. This is exact payoff
   attribution, even when its preserved commitments cannot be financed.

For each date, the fixed-exposure shadow begins with initial cash plus all
earlier repriced profits. Required extra opening cash is the maximum positive
gap between that date's total committed stakes and its opening shadow balance.
Checking only the minimum closing balance misses dates that end positive but
cannot fund their opening commitments. No artificial loan, stake clipping,
capital reset or additional deposit is inserted. Unfunded shadows retain raw
cashflows, hit ratios, model payoff components, frequency and turnover ROI;
ordinary feasible terminal wealth, capital return, drawdown, return statistics
and confidence intervals are withheld. They are excluded from wealth graphs.
Even funded fixed-exposure paths remain attribution rather than rerun policies.

Full reference replays use the frozen date-batch engine: all same-date requests
depend on opening cash and are uniformly scaled to the applicable cash/date
cap before outcomes settle. At most one bet per match is allowed; H/D/A ordering
resolves ties. Continuous accounts carry cash across all four seasons. Annual
accounts each start fresh and are never spliced into a continuous wealth curve.

## Metrics and exact accounting

Every row retains the established hit ratio; model-implied expected gain and
loss (total and per trade); observed average winning gain and losing loss;
trading frequency per common priced fixture and calendar week; turnover,
profit, ROI, capital return and applicable risk/uncertainty statistics. Expected
gain is Σ p s (O−1), expected loss is Σ (1−p)s; these are model claims, not
realized averages or evidence of calibration. No-bet totals are zero and
undefined conditional averages/ratios remain unavailable.

For original selected stakes s, payoff odds O, probabilities p, realized win
indicator y, and de-vigged reference-market probability q:

- realized profit = Σ s(yO−1);
- model expected profit = Σ s(pO−1);
- market-implied component = Σ s(qO−1);
- model probability premium = Σ sO(p−q);
- outcome residual = Σ sO(y−q);
- forecast payoff error = Σ sO(y−p).

Model expectation equals the market-implied component plus the probability
premium. Realized profit equals the same component plus the outcome residual.
Here q is a descriptive market benchmark, never assumed to be true probability.
These identities establish accounting, not forecasting skill or arbitrage.
Realized pure quote uplift is Σ ys(O_original−O_reference); the corresponding
model-expected uplift is Σ ps(O_original−O_reference). Price improvement is
nonnegative on the same frozen bets because original prices are best/reference.

Bookmaker concentration is reported within each original account. Shares and
Herfindahl indices describe selected bets and stake exposure. Provider profits
reflect different fixture/outcome selections and do not establish causal book
quality. Accounts reuse fixtures, so their counts must not be added as unique
trades or interpreted as a diversified combined portfolio.

## Price provenance and closing comparison

The frozen panel uses complete individual-book H/D/A triplets, excludes market
aggregates/exchanges and applies the existing stale-Pinnacle filter. Bet365 is
the common reference. The outcome-specific best archived prices can come from
different providers. Individual quote clocks are missing: neither panel proves
simultaneous availability, fills, account access, limits or executable returns.

The provider distinguishes pre-closing and closing (`C`) columns since 2019/20
and describes periodic quote collection. Its current notice also documents
unreliable Pinnacle updates from July 23, 2025. See the primary
[Football-Data field notes](https://www.football-data.co.uk/notes.txt) and
[data/source notice](https://www.football-data.co.uk/data.php), consulted October
15, 2026. Source-specific private academic-use restrictions remain applicable.

An additional descriptive panel compares archived pre-closing Bet365 with
archived closing Bet365 for the same fixture and outcome. Its decimal ratio is
entry/reference odds divided by closing/reference odds; both normalized implied
probabilities are retained. It is never used to select, qualify or size a bet,
refit any forecast, or claim verified closing-line value. Best-versus-closing
ratios are avoided because they would mix provider selection with time movement.

## Interpretation, inference and reproduction

All history was previously inspected. The existing conditional 84-rule bootstrap
remains attached only to the original recorded cashflows. It is preserved in
the combined report but does not supply adjusted p-values for new reference
replays. No winner is promoted to a future strategy. Date-bootstrap intervals,
when available, condition on the recorded stake path and do not rerun Kelly
sizing. Execution sensitivity cannot repair the current-club historical cohort
selection or substitute for pending prospective evaluation.

`inputs.py` reconciles native fixture identities, frozen probabilities and source
ledgers; `replay.py` applies the unchanged policy engine; `diagnostics.py` computes
accounting and quote diagnostics; `audit.py` independently reconstructs cash and
payoffs; `report.py` reads the completed tables. The build hashes all consumed
sources and implementation files before and after computation, refuses to
overwrite runs and records runtime package versions. No source result is edited.
All detailed ledgers are available as CSV/Parquet; the compact workbook includes
complete metrics, attribution and external-ledger hash paths. The final appendix
explains all 84 exact original configurations and the reference-mode override.
