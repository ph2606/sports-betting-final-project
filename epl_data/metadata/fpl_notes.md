# Fantasy Premier League data

Collected for the 2026-27 Premier League cohort in `current_teams.csv`, with requested as-of date 2026-10-06. Every curated focal club belongs to those 20 clubs. West Ham, Burnley and Wolverhampton Wanderers are excluded as focal clubs, including from their historical appearances. Historical opponents can belong to a different club; original whole-league source files are retained to make the filtering and fixture reconstruction reproducible.

## Sources and acquisition

- Official Fantasy Premier League: <https://fantasy.premierleague.com/>.
- Player/team/gameweek bootstrap: <https://fantasy.premierleague.com/api/bootstrap-static/>.
- Fixtures and expanded player match statistics: <https://fantasy.premierleague.com/api/fixtures/>.
- Individual current-season match histories, upcoming fixtures and past-career totals: `https://fantasy.premierleague.com/api/element-summary/{element}/` for every one of the 667 current bootstrap players.
- Completed-gameweek stats and scoring explanations: `https://fantasy.premierleague.com/api/event/{gameweek}/live/` for GW1-5.
- Official weekly best XI: `https://fantasy.premierleague.com/api/dream-team/{gameweek}/` for GW1-5.
- Native set-piece editorial notes: <https://fantasy.premierleague.com/api/team/set-piece-notes/>. The present response is a set of placeholder messages; player bootstrap taker-order fields are available separately.
- Public historical FPL archive: <https://github.com/vaastav/Fantasy-Premier-League>. Downloaded `players_raw.csv`, `gws/merged_gw.csv`, `player_idlist.csv`, and available `teams.csv` and `fixtures.csv` for 2016-17 through 2026-27.
- Archive files are pinned to commit `9779cdbc0c07f6c900c2d0c181ddf6bb9c800f88`, committed 2026-08-28T09:47:53Z. The archive's 2026-27 player-gameweek file contains GW1 only. Official current-season histories are available through GW5 and should take precedence for 2026-27.

There were 680 successful official API requests and no failures. The archive had 51 successful downloads, including the repository commit metadata, and five expected HTTP 404 responses: `teams.csv` for 2016-17, 2017-18 and 2018-19, and `fixtures.csv` for 2016-17 and 2017-18. The available player files and player-gameweek files were downloaded for all 11 seasons.

Original response bytes are under `data/raw/fpl_current` and `data/raw/fpl_archive`. Request manifests record URL, UTC retrieval time, requested as-of date, response status, byte count, SHA-256 and failed requests. Reuse of cached raw files checks their SHA-256 and preserves the original retrieval timestamp. Some older CSVs require Windows-1252 decoding; this is recorded in `source_csv_encoding`, and source bytes are preserved. No replacement characters were introduced by decoding.

## Current official tables

Each table has CSV and Parquet copies under `data/processed/fpl_current`. All native source fields are retained. Nested native objects are serialized as JSON in flat tables. Added fields identify provenance, player code, position and club where appropriate.

| Table | Rows | Columns | Contents |
|---|---:|---:|---|
| `players` | 667 | 118 | Full player bootstrap, current club, position, names, birth/region fields, price, ownership, transfer activity, availability/news, set-piece order, season statistics, ranks and forecasts |
| `teams` | 20 | 28 | Full team bootstrap, names, identifiers and FPL strength fields |
| `events` | 38 | 34 | Gameweek deadlines, completion state, scores, selection/captaincy and chip statistics |
| `fixtures` | 380 | 24 | Full season schedule, played results, difficulty and native player-stat JSON |
| `fixture_player_stats` | 3,502 | 13 | Expanded fixture/player statistical entries |
| `player_match_history` | 3,216 | 54 | Current-season match records, including zero-minute entries, GW1-5 |
| `player_upcoming_fixtures` | 22,011 | 26 | Per-player upcoming schedule/difficulty snapshots |
| `current_roster_history_past` | 2,109 | 42 | Previous-season career totals for today's roster; former club is unknown |
| `team_match_player_totals` | 100 | 24 | Player statistics summed for each club and played fixture |
| `gameweek_live_player_stats` | 3,216 | 46 | Native official completed-gameweek statistics and explanation JSON |
| `gameweek_fantasy_points_explanations` | 4,576 | 14 | Player/fixture/scoring-category points, values and modifications |
| `gameweek_dream_teams` | 55 | 13 | Five official gameweek best XIs and top-player flag |
| `team_set_piece_notes` | 20 | 9 | Current editorial placeholders, with source update time |
| `summary_download_status` | 667 | 6 | One successful summary download for every requested player |
| `element_types` | 4 | 18 | FPL positions and squad constraints |
| `element_stats` | 26 | 7 | Native player-stat descriptions |
| `chips` | 8 | 12 | Native chip metadata |
| `phases` | 11 | 10 | Native season phase metadata |

The FPL team bootstrap currently contains placeholder zero values for played/points/wins and several attack/defence strength fields, plus null overall `strength`. Retain them as native source fields, but use authoritative standings or actual fixture results for team performance measures.

Current histories have 610, 626, 654, 659 and 667 player-fixture records respectively for GW1-5, reflecting when players entered the FPL roster. There are 1,538 positive-minute records. The latest completed fixture in this response was 2026-09-20; no later outcomes have been invented. All 3,216 records have a uniquely resolved actual club. All 667 current players have unique FPL player codes. This is the FPL-listed player pool, not a verified list of active first-team squad members: 562 are currently selectable, 105 are not selectable, all 667 remain transactable, and all have `removed=False`. Native status counts are 446 available, 105 unavailable, 72 injured, 40 doubtful and four suspended. Unavailable and injured players remain in the data with these flags.

## Historical archive tables

CSV and Parquet copies are under `data/processed/fpl_archive`.

| Table | Rows | Columns | Contents |
|---|---:|---:|---|
| `player_gameweeks` | 176,282 | 90 | Historical player-fixture records for actual appearances/roster entries at cohort clubs |
| `players_season_snapshots` | 5,682 | 129 | Native season-level player snapshots at cohort clubs; descriptive snapshots |
| `teams_season_snapshots` | 156 | 30 | Native available team snapshots; early seasons supply reconstructed team-code lookup rows |
| `team_fixture_history` | 5,092 | 31 | Focal-club fixture rows for seasons with fixture files; two rows when both clubs are in the cohort |
| `player_identity_by_season` | 5,725 | 9 | Archive names and season-local player identifiers |
| `player_team_season_totals` | 5,836 | 24 | Match statistics summed by actual club/player/season; transfers split between clubs |
| `team_gameweek_player_totals` | 5,004 | 23 | Player statistics summed by actual club/gameweek |
| `season_coverage` | 11 | 18 | Per-season coverage, source counts, exclusions and mapping audit |
| `duplicate_or_superseded_rows` | 69 | 64 | Removed original records retained for review |
| `unresolved_membership_rows` | 0 | 7 | Schema-bearing audit table; no unresolved fixture/club memberships |

| Season | Curated player-fixture rows | Cohort clubs observed | FPL gameweeks observed |
|---|---:|---:|---|
| 2016-17 | 13,164 | 11 | 1-38 |
| 2017-18 | 12,305 | 11 | 1-38 |
| 2018-19 | 12,809 | 12 | 1-38 |
| 2019-20 | 13,637 | 12 | 1-47, with original FPL COVID-restart numbering |
| 2020-21 | 16,036 | 13 | 1-38 |
| 2021-22 | 16,631 | 13 | 1-38 |
| 2022-23 | 21,552 | 16 | 1-38 |
| 2023-24 | 22,307 | 15 | 1-38 |
| 2024-25 | 22,040 | 16 | 1-38 |
| 2025-26 | 25,191 | 17 | 1-38 |
| 2026-27 | 610 | 20 | 1 only; use official current history for this season |

There are 1,917 distinct stable player codes in the archive. Historical coverage is restricted to seasons when the focal club was in the Premier League. Coventry has no earlier Premier League season in the 2016-17 onward archive, for example; absent rows are not zero-performance observations.

## Identity, transfers, exclusions and validation

`element`/`id` is an FPL season-local identifier. Join it with `season`, or use `player_season_key`. FPL `player_code`/native `code` is a candidate for joining the same player across seasons; preserve season-local IDs and verify changes before making a permanent cross-provider identity table.

Match-time club is obtained from fixture participants and `was_home`. For 2016-17 and 2017-18, the fixture home/away teams are reconstructed from the unique opponent IDs supplied by players on each side of the same fixture. For 2016-17 to 2018-19, missing native team tables are replaced by the unambiguous season-local `team` to stable `team_code` relation in `players_raw.csv`. Stable team codes then resolve to the verified current club cohort. A player's current or season-end team is never used to assign historical match club.

There are no unresolved historical match-club mappings, no missing stable player codes in curated archive rows, no source-team/fixture-team conflicts, and no remaining duplicate `(season, element, fixture)` keys. All 176,282 curated archive records have completed match scores. The archive cleanup removed 59 March 2020 Manchester City-Arsenal postponed-fixture placeholders, which were superseded by the played June fixture, and 10 exact duplicate 2025-26 source rows. These 69 original rows are retained in the audit table and excluded from all derived totals.

The official current history also has unique `(season, element, fixture)` keys, no missing club mapping, and all 20 current clubs. Current and archive tables are separate observations of overlapping source data: 2026-27 archive GW1 overlaps 610 official current-history rows. Prefer the official source for the full current season; do not concatenate those tables and count both copies.

`history_past` does not supply a former team. Its `current_roster_team` is explicitly today's roster context, while `historical_team` is empty. Those career snapshots can include seasons at other clubs and are not evidence of historical team-level performance for the current club. The archive player snapshot has a similarly explicit `data_role`: its current-at-archive club and cumulative totals are descriptive, not match-time team labels.

## Modeling use

Match histories include minutes, goals, assists, clean sheets, conceded goals, own goals, penalties, disciplinary cards, saves, bonus/BPS, influence/creativity/threat/ICT, ownership/selection and transfer counts, price, scores, dates and opponent IDs. Newer seasons add starts, xG/xA/xGI/xGC and defensive metrics; unavailable fields remain missing rather than being converted to zero. Scoring and available fields change between FPL seasons.

Every table identifies its `data_role` where meaningful. Completed-match observations, source forecasts, upcoming schedule/difficulty, editorial news and player-season totals have different time semantics. A row's UTC `retrieved_at_utc` records acquisition, not when every field became knowable. Bootstrap form, forecasts, injury status, cumulative totals, ranks and current ownership are snapshots and must not be used as historical pre-match predictors. Compute historical features from prior completed fixtures, with a cutoff before the prediction date. FPL transfers/selected/value in match-history records are retrospective provider snapshots; their exact pre-deadline availability is not independently verified.

Player sums of clean sheets, goals conceded, saves, fantasy points and BPS do not represent league-table team measures. `team_match_player_totals` and `team_gameweek_player_totals` explicitly aggregate player statistics. Use fixture scores for match outcomes. Double gameweeks can have several fixtures; use fixture IDs and kickoff dates. The FPL archive includes zero-minute roster records and flags `minutes_played_positive`; filter that flag when studying actual on-pitch appearances.

## Refresh

From the `final_project/epl_data` directory:

```powershell
python scripts/collect_fpl.py --mode all --workers 5 --refresh
```

Without `--refresh`, successfully downloaded raw responses are SHA-256 checked and reused, preserving the collection snapshot. `--mode current` refreshes official FPL alone; `--mode archive` refreshes the public archive alone. Worker count is capped at six, with timeouts, limited retries and explicit failed-request records. This collector does not require credentials or make paid requests. Table manifests enumerate every retained column for the data dictionary.
