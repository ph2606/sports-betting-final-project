# StatsBomb official open Premier League event data

Source: [StatsBomb Open Data repository](https://github.com/hudl/open-data), which the former `statsbomb/open-data` repository redirects to. All source files are pinned to commit `4b73468fc5b0f1950f9f66fada70ad3a4f9327cb`, dated 2026-09-07T16:27:15Z. Requested as-of date: 2026-10-06.

The official `competitions.json` lists two available men's English Premier League seasons: 2003/2004 and 2015/2016. This collection only uses those competitions. The 2015-16 source supplies all 380 league matches; 324 involve at least one of the current 20-club cohort. The 2003-04 source supplies Arsenal's 38 league matches, all of which qualify. These are selected historic seasons, not current-season event coverage.

All 362 qualifying match event files and all 362 lineup files downloaded successfully. There were 733 successful original-source requests, no failures, and 1,087,301,338 original response bytes. Original JSON, the official README, actual LICENSE.pdf and event/lineup/match specification PDFs are retained under `data/raw/statsbomb`. The readable license text is a local PDF extraction, separately named; the original PDF remains authoritative.

Historical focal club membership comes from the actual native match/event/lineup team ID, matched to the verified current cohort. It never comes from a player's present club. Curated event, player and focal-team tables exclude former Premier League clubs as subjects. Opponent context and the complete original source response remain available. Players who subsequently changed clubs are preserved at the club they represented in each source match.

## Coverage

| Season | Source matches | Downloaded qualifying matches | Focal club-match rows | Original events in downloaded matches | Curated cohort events |
|---|---:|---:|---:|---:|---:|
| 2003-04 | 38 Arsenal matches | 38 | 58 | 129,401 | 102,459 |
| 2015-16 | 380 | 324 | 456 | 1,128,176 | 828,389 |
| Total | 418 | 362 | 514 | 1,257,577 | 930,848 |

In 2015-16, Arsenal, Aston Villa, Bournemouth, Chelsea, Crystal Palace, Everton, Liverpool, Manchester City, Manchester United, Newcastle United, Sunderland and Tottenham Hotspur each have their full 38-match season. Other participating teams are opponents rather than focal clubs.

In 2003-04, Arsenal has 38 matches. Aston Villa, Chelsea, Everton, Fulham, Leeds United, Liverpool, Manchester City, Manchester United, Newcastle United and Tottenham Hotspur have only their two matches against Arsenal. This is an Arsenal-selected sample; other clubs' missing games are not zero-event games or complete season coverage.

Across the two available seasons, 14 of today's 20 clubs have focal records. There are no focal event records for Brentford, Brighton & Hove Albion, Coventry City, Hull City, Ipswich Town or Nottingham Forest in this open EPL subset. There is no 2026-27 StatsBomb open EPL event season listed in the retrieved index. Both available seasons report no public StatsBomb 360 frame availability. Embedded shot freeze-frame information is still retained inside native shot objects.

## Tables

Every table has CSV and typed Parquet copies under `data/processed/statsbomb`. The large event outputs were written match-by-match into per-season files, rather than assembling a million-row data frame in memory. Full CSV output totals approximately 826 MB; Parquet totals approximately 99 MB and is preferable for analysis.

| Table | Rows | Columns | Contents |
|---|---:|---:|---|
| `competitions` | 2 | 16 | Native available EPL competition-season metadata |
| `matches` | 362 | 25 | Native match metadata, scores, source IDs, teams/managers, stadium/referee and explicit original native season JSON |
| `team_matches` | 514 | 33 | One actual current-cohort focal club per match; opponent and oriented goals retained |
| `events_2003_04` | 102,459 | 74 | Every retained native event field and added query-friendly identifiers/coordinates |
| `events_2015_16` | 828,389 | 75 | Every retained native event field and added query-friendly identifiers/coordinates |
| `player_match_lineups` | 9,054 | 23 | Native match roster, countries, jersey numbers, cards and position intervals; includes unused substitutes |
| `player_match_positions` | 8,575 | 23 | Native position intervals and start/end reasons, preserving source clocks and periods |
| `player_match_cards` | 854 | 19 | Native lineup disciplinary entries |
| `team_match_event_metrics` | 514 | 37 | Derived focal-team event counts, passing/shot statistics and shot xG sums |
| `player_match_event_metrics` | 7,032 | 39 | Derived statistics for players with source events at actual focal clubs |
| `team_match_event_type_counts` | 12,526 | 15 | Complete provider event taxonomy counts by actual club/match |
| `player_match_event_type_counts` | 80,399 | 17 | Complete provider event taxonomy counts by actual player/club/match |
| `match_coverage` | 362 | 11 | All qualifying matches, download success and source/curated event counts |
| `season_coverage` | 2 | 8 | Available source seasons, qualifying matches, focal club names and 360 availability |

The event tables preserve all native top-level fields. Every native nested object/list is retained as compact JSON, including `pass`, `shot`, `carry`, `tactics`, `related_events`, native player/team/position objects and coordinates. Added columns expose source player/team IDs, event type, starting coordinates, pass/carry endpoints, shot endpoint including height where available, pass length/angle/outcome, shot outcome/body part/type and StatsBomb xG. UUID `id` remains the native event ID. Missing optional fields remain missing.

The full event taxonomy is retained, not only shots. The cohort subset contains 262,847 passes, 243,441 ball receipts, 201,030 carries, 78,584 pressure events, 28,268 ball recoveries, 21,452 duels and 6,921 shots, alongside interceptions, dribbles, clearances, blocks, keeper actions, fouls, cards, substitutions, tactical events and other native types. Coordinates use the StatsBomb pitch convention, typically 120 by 80; native values and provider specification are preserved without conversion to meters or another provider's pitch system.

Lineups contain 614 distinct source player IDs. There are 7,044 player-match entries with native position intervals and 5,654 Starting XI entries, exactly eleven per focal club-match. The remaining lineup entries include unused substitutes. Some participating players have no individual recorded event, so the event-metric table is not a full participation roster. `positions_recorded` and `started_match` expose these distinctions. No artificial playing minutes are assigned from position intervals whose final-whistle clocks are null.

## Derived measures and identity

Metrics count recorded source events. A pass is classified as completed when its native pass object has no outcome object. Shot-on-target counts use native outcomes `Goal`, `Saved` and `Saved To Post`; this is an explicit derived measure. `shot_goals` excludes own-goal events; fixture scores remain authoritative for team outcomes. Every event type, including own-goal types, remains in the taxonomy tables. Absent event-category counts are zero in the derived metrics; missing native optional attributes remain missing in the full event records. Shot xG observation counts accompany xG sums so incomplete coverage can be identified.

StatsBomb player/team/match IDs and event UUIDs are source-specific. They must not be treated as FPL element/team/fixture IDs. Match-level links to other providers require club/date/season/result checks; player links require an explicit verified crosswalk. Names are retained with their original accents and source spelling. Native `season` objects are retained in `native_season` while `season` supplies the normalized football-season label.

These are post-match observations from retrospectively downloaded source files. Native source metadata and UTC acquisition timestamps are retained, but the collector does not establish when each observation was originally published. They cannot be assigned directly to historical pre-match decisions. Use only earlier completed match observations when constructing predictive inputs and distinguish retrospective source availability from a contemporaneous feed.

## Validation and refresh

All 930,848 curated event UUIDs are unique. No event has a focal club outside the current cohort. Every player-attributed event links to that player's native lineup at the same actual club and match. There are no unresolved source team events or shot xG values outside zero to one. Full taxonomy counts and team-event aggregates both reconcile exactly to the 930,848 retained event records. All fourteen CSV schemas and Parquet row/schema counts were checked. Results are saved in `statsbomb_validation_manifest.json`; source requests and SHA-256 hashes are in `statsbomb_manifest.json`, and complete field lists are in `statsbomb_tables_manifest.json`.

From `final_project/epl_data`:

```powershell
python scripts/collect_statsbomb.py --workers 4 --refresh
```

Omit `--refresh` to SHA-256 verify and reuse original cached responses, preserving retrieval timestamps. Concurrency is capped at four; requests have timeouts and limited retries. The collector checkpoints its provenance during downloads so an interrupted run can resume. Processing is bounded by one match's events rather than the complete dataset. Standard project dependencies suffice for event acquisition and processing; `pypdf` extracts the readable copy of the retained license.

## Actual source license

The retained [official LICENSE.pdf](../data/raw/statsbomb/LICENSE.pdf) is the StatsBomb Public Data User Agreement, last updated 8 September 2023. It provides research access, requires StatsBomb attribution and its brand logo for published analysis, and restricts commercial exploitation and third-party redistribution of underlying data. The source README also states the published-analysis attribution/logo requirement. The original PDF contains the actual terms; this source is not tagged with a generic MIT or Creative Commons license. This collection is a local research acquisition and analysis of the original responses.
