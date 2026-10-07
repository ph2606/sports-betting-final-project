# Football-Data match histories and odds

Sources: [English season archive](https://www.football-data.co.uk/englandm.php),
[provider documentation and usage statement](https://www.football-data.co.uk/data.php),
[field definitions](https://www.football-data.co.uk/notes.txt).
Original bytes, retrieval times, URLs, HTTP status and SHA256 hashes are archived.

## Cohort and scope

The analysis cohort is the 20 clubs in metadata/current_teams.csv for 2026-27,
as of 2026-10-06. Raw public files contain whole leagues. Curated match records
require at least one current club; team_match_history contains only current clubs
as the focal team. Former clubs can appear solely as their historical opponents.
E0 is the Premier League; E1/E2/E3 track current clubs' histories in the second,
third and fourth tiers, including the old Division 1/2/3 names. Lower-tier games
must not be treated as Premier League games. National cups, European matches,
friendlies and promotion play-off matches are not guaranteed in this source.

## Tables

- matches_current_cohort: all native fields (full/half-time scores, results,
  attendance when supplied, shots, corners, fouls, offsides, cards, referee,
  expected goals where newly supplied, and decimal odds) plus normalized names,
  provenance, dates and eligibility flags.
- team_match_history: one observation per eligible focal team per match. For and
  against statistics and selected odds are oriented to that club; complete native
  odds including totals and Asian handicaps remain in matches_current_cohort.
- match_odds_1x2_long: bookmaker or market aggregate with home/draw/away odds,
  source fields, preclosing versus closing label, Pinnacle reliability flag and
  flags for missing/invalid decimal prices. Quotes with prices at or below one
  remain archived but are not marked as valid complete quotes.
- team_season_summary: descriptive season/division totals, averages, counts and
  observed-statistic denominators. The active season is partial, and points are
  match-derived (not official table points after administrative deductions).
- team_match_lagged_features: previous 5/10 completed matches across observed
  divisions, strictly earlier dates; season-to-date means/totals restricted to the
  same season/division; prior-calendar-season win proportion and division. Empty
  history remains missing. Goal, expected-goal, shot, shots-on-target and corner differences
  measure outperformance relative to the observed opponents in each match.
  These descriptive inputs are not a trained model.
- team_season_coverage and season_source_coverage: coverage and missing-file audit.
- field_dictionary: native-field descriptions where provider documentation gives
  them, data types and nonnull counts. All tables have CSV and typed Parquet copies.

Rebuild from saved bytes with `python scripts/collect_football_data.py --reuse-raw`;
the original retrieval records and hashes are retained. Omit that option to refresh.
The initial download completed before its long feature build was interrupted.
Its unflushed HTTP ledger was recovered from saved paths/bytes/SHA256 and original
archive-write timestamps. Exact HTTP retrieval times and statuses from that first
run are unrecorded; the recovered records explicitly distinguish filesystem time.

## Dates and reproducibility

Source dates are parsed day first and as-of selection includes 2026-10-06.
Completed outcomes dated later are quarantined outside the analysis tables.
Source kickoff times, when present, are converted assuming English local time
(Europe/London, respecting daylight saving); the source notes do not explicitly
state a timezone, so the assumption is recorded. Missing kickoff times stay null.
Only source dates support feature ordering; games on the same date cannot inform
each other's features. source_match_key is a deterministic hash of season,
division and provider home/away names, stable when a fixture date is rescheduled;
it is not an official fixture identifier. Names are linked through an explicit
alias map, not through unreliable fuzzy matching.

## Odds and modeling limitations

Preclosing odds are snapshots collected after market opening, ordinarily Friday
afternoons for weekend games or Tuesday afternoons for midweek games. They are
not verified opening prices. Closing columns have a C after the bookmaker code.
Most two-snapshot series start in 2019-20; Pinnacle closing 1X2 goes back to
2012-13. Individual quote timestamps, bookmaker stake limits, commission and
execution availability are absent. Quotes or maxima from different bookmakers
need not be synchronized; they do not establish a tradeable arbitrage. Closing
odds must not become a predictor at an earlier preclosing decision time.

The provider warns that Pinnacle's public odds API has been unreliable since
2025-07-23; both its preclosing and closing prices can be stale. Pinnacle fields
are preserved and flagged, not silently treated as reliable. Market average and
maximum prices cease including Pinnacle after that date according to the provider.
Coverage, bookmakers and statistic definitions change over time. Results begin
in 1993-94; detailed statistics and odds generally begin around 2000-01. Missing
fields are missing rather than zero. Raw provider records can contain errors.
The newest E0 files also contain HxG/AxG: expected goals from this provider.
Their detailed model/methodology is not identified in the archived notes and
should not be assumed identical to expected goals from another source.
Historical cohort selection induces survivor bias if used for a league-wide
backtest. Build train/test splits in chronological order and retain division.
Prior-season statistics in a lower division must be interpreted accordingly.

## Usage

Football-Data says its free data is intended for private individuals, and excludes
commercial or data-training products using automated bots/scrapers/AI. This
collection is a private academic project archive; these files are not asserted to
have an unrestricted open license. Review the archived usage statement and seek
provider permission before redistribution or a use outside that scope.


Acquisition summary:

```json
{
  "matches_current_cohort": {
    "rows": 21782,
    "columns": 248
  },
  "team_match_history": {
    "rows": 27304,
    "columns": 86
  },
  "team_season_summary": {
    "rows": 680,
    "columns": 71
  },
  "team_match_lagged_features": {
    "rows": 27304,
    "columns": 150
  },
  "match_odds_1x2_long": {
    "rows": 193622,
    "columns": 24
  },
  "field_dictionary": {
    "rows": 248,
    "columns": 6
  },
  "source_files_attempted": 136,
  "source_files_parsed": 136,
  "future_results_quarantined": 0,
  "first_match_date": "1993-08-14",
  "last_match_date": "2026-09-20",
  "current_cohort_count": 20,
  "failed_source_files": [],
  "collector_runtime_seconds": 77.55
}
```
