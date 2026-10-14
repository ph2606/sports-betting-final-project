# EPL prospective forecasts

This directory preserves manually captured public data, frozen models and forecasts recorded before kickoff. It extends the retrospective studies without replacing their data or results. The operational rules are in [OPERATIONAL_PROTOCOL.md](OPERATIONAL_PROTOCOL.md), with the model specification in [PROSPECTIVE_PROTOCOL.md](../epl_modeling/PROSPECTIVE_PROTOCOL.md).

## First release: October 14, 2026

The successful [snapshot manifest](snapshots/20261014T091234.352344Z_4ee7a3a730/manifest.json) records capture from **09:12:34 to 09:14:16 UTC** on October 14. Official FPL membership matched the saved 20 current clubs; all **667 requested player summaries** were downloaded. FPL, Football-Data and Understat each reported their latest completed league match on **October 12**. The live feature audit used 60 completed current-season matches and found no feature-date violations.

The [run summary](runs/20261014T092230.366245Z/run_summary.json) and [coverage table](runs/20261014T092230.366245Z/forecast_coverage.csv) document the release:

| Item | Recorded result |
| --- | --- |
| Upcoming targets | 10 fixtures, October 17–19, within the seven-day window |
| Frozen model candidates | Eight: logistic and market residual, each with team, team + xG, team + player, and combined features |
| Released forecasts | 40 logistic forecasts: four feature groups for each fixture |
| Withheld variants | 60: 40 market residual forecasts and 20 raw/temperature-calibrated market benchmarks |
| Price coverage | Zero E0 upcoming rows in Football-Data's captured fixtures feed; no usable Bet365 triplets |
| Prospective outcomes | None observed; no prospective accuracy, loss, ROI or profit estimate |

The [model manifest](models/e82cad876a650c66/manifest.json) freezes the candidates and their hashes. Training used 2016–17 through 2023–24, tuning used 2024–25, final fitting added that tuning season, and calibration used the already examined 2025–26 season. No 2026–27 outcomes entered fitting, tuning or calibration. The released probabilities are in [forecasts.jsonl](forecasts.jsonl); the ten target identities and kickoff times are in [target_fixtures.csv](runs/20261014T092230.366245Z/target_fixtures.csv). Missing prices were recorded as exclusions rather than filled from another season or source.

## Manual collection and release

Run these commands from the `final_project` repository root using the project's Python environment. Collection makes network requests; there is no scheduled collection or wager placement.

```powershell
python -m pip install -r epl_live/requirements.txt
python -m epl_live.collect --players
```

The collector prints the new snapshot path and source validation status. `--players` requests all current FPL element-summary histories with at most six workers; it is required for the complete player inputs expected by the release runner. Optional `--output-root PATH` changes the snapshot parent directory. Each invocation creates a unique UTC timestamp/random-suffix directory, retaining response bytes, request clocks, hashes, errors, the manifest, and normalized CSV/Parquet tables. Existing snapshots are never overwritten.

Supply the newly printed path to release forecasts:

```powershell
$snapshotPath = "epl_live/snapshots/20261014T091234.352344Z_4ee7a3a730"
python -m epl_live.run --snapshot $snapshotPath --lookahead-days 7
```

The path above identifies the first capture; replace it with a fresh capture for a later cycle. Reusing a snapshot preserves its original observation clocks. Alternatively, `python -m epl_live.run --lookahead-days 7` performs one new collection, including player histories, before releasing forecasts. The runner reuses the frozen candidate bundles, checks that targets remain in the future, and skips model/fixture forecasts already released.

The next useful manual collection is when the provider publishes complete upcoming Bet365 prices, while the targets are still before kickoff. Market variants require valid complete triplets observed within one hour of forecast creation. This age rule concerns local observation, not verified provider publication or executable availability. Retain earlier snapshots and forecasts when collecting again.

The first release's [probability overview](runs/20261014T092230.366245Z/overview/FORECASTS.md)
and [Excel workbook](runs/20261014T092230.366245Z/overview/EPL_live_forecasts.xlsx)
are dated views. For a new run directory, export another immutable view with
`python -m epl_live.overview --run PATH_TO_NEW_RUN_DIRECTORY`.

The active runner includes the [v1.1 safeguards](IMPLEMENTATION_REVISIONS.md).
The executed v1 sources are archived, and the original 40 forecast records
remain unchanged. No later forecasts have been released as part of this update.

## Settlement and integrity

After target games finish, make a fresh collection and evaluate using that new snapshot:

```powershell
$resultsSnapshotPath = "epl_live/snapshots/REPLACE_WITH_POST_MATCH_SNAPSHOT_ID"
python -m epl_live.evaluate --snapshot $resultsSnapshotPath
```

Evaluation appends observed completed results to a separate `outcomes.jsonl` ledger and writes a new timestamped `evaluations/` directory. It scores the earliest released version per model/fixture. A conflicting result is rejected for investigation; forecasts and prior settlements are not replaced. Scores describe each model's available resolved forecasts, so differing coverage alone does not establish model superiority.

Forecast and outcome ledgers hash each canonical record envelope, including its sequence and previous hash. Readers validate the chain, identities and timing rules; writers validate the entire batch before appending. Check the forecast ledger manually with:

```powershell
python -c "from epl_live.ledger import verify_ledger; print(verify_ledger('epl_live/forecasts.jsonl', 'forecast'))"
```

Preserve independent repository commitments of ledger heads. A local hash chain checks consistency but cannot independently prove when a forecast was published or detect a complete rewrite with recomputed hashes.

All capture and release clocks use actual UTC. `observed_at_utc` means completion of local response-body capture; HTTP `Date` is a server header. Neither verifies when the provider published its data or odds. Recent retrieval also does not establish fresh underlying results: inspect the recorded latest completed match dates. Archived quotes do not establish simultaneous or executable prices, arbitrage execution, or realized betting returns.

Run the live tests with `python -m pytest epl_live/tests -q`. This includes the
ledger's pytest cases and the unittest cases for collection, features,
settlement and runtime dependency checks. The release audit also retains the
earlier study's distinct 40 modeling checks.
