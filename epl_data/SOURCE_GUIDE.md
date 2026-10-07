# EPL acquisition sources and interpretation

The target cohort is the 20 Premier League clubs for **2026/27**, verified on
October 6, 2026. [Official membership announcement](https://www.premierleague.com/en/news/4673099/the-202627-premier-league-season-officially-starts)
confirms Coventry, Hull and Ipswich replaced West Ham, Burnley and Wolves.
`metadata/current_teams.csv` is the explicit cohort list. Current means league
membership; a provider's player list can include unavailable, loaned or removed
players. FPL `can_select`, `removed` and `status` preserve that distinction.

**Historical scope:** collect the history of these current clubs, including their
lower-division years and matches against other opponents. Curated focal-team
records exclude former clubs. Opponent fields can legitimately mention a former
Premier League team. Unmodified raw league files retain all source rows so that
filtering and historical membership mapping can be audited. This fixed cohort
introduces survivor bias if it is used to claim results for the whole historical
league; it answers the user's requested current-club scope.

| Source | Downloaded information | Interpretation |
|---|---|---|
| [Fantasy Premier League official API](https://fantasy.premierleague.com/api/bootstrap-static/) | Players, teams, gameweeks, fixtures, fixture-player statistics, individual player match histories, past-season totals and upcoming fixtures | Prices, ownership, availability/news and season totals are retrieval-time snapshots. FPL IDs are season-specific; stable player `code`/Opta code helps link seasons. FPL assists/points have fantasy rules and differ from other providers. |
| [Vaastav FPL archive](https://github.com/vaastav/Fantasy-Premier-League) | Historical player-gameweek records, per-season player identities, available teams/fixtures, source definitions | Historical appearances are linked to the team represented in that match. Season-final snapshots and `xP` cannot become historical pre-match predictors. Duplicate/postponement cleanup has a separate audit. |
| [Football-Data English archives](https://www.football-data.co.uk/englandm.php), [definitions](https://www.football-data.co.uk/notes.txt) | Match results, full/half-time goals, shots, shots on target, corners, fouls, cards, referee/attendance where available; bookmaker 1X2, totals and Asian-handicap odds | E0/E1/E2/E3 distinguish the Premier League and three lower tiers. Definitions and coverage vary by season. Closing columns are later observations; preclosing collections are not necessarily opening prices. |
| [Understat](https://understat.com/league/EPL/2026) | League/team match expected goals, xG against, expected points, PPDA/deep statistics, player-season xG/xA/npxG/xGChain/xGBuildup, detailed shots and match player statistics where downloaded | xG is provider-specific. Match xG/shots are observed after play and must be lagged. Some player-season totals combine multiple clubs; those records are explicitly marked. |
| [ESPN Premier League](https://www.espn.com/soccer/league/_/name/eng.1) | Team identities, squads and player demographics; schedules, standings, and match summaries/statistics/lineups where available | Public web API endpoints are not a guaranteed service. Some metadata, including coach fields, can be stale; preserve the source and verify before use. Summary lineups have no guaranteed original publication timestamp. |
| [Transfermarkt current league](https://www.transfermarkt.com/premier-league/startseite/wettbewerb/GB1/saison_id/2026) | Club and player valuations, squad size/age, citizenship, height, foot, joining/contract dates, injuries/suspensions, season transfers | Valuations are estimates. Rosters can include loans and differ from FPL. Injury/return dates may be stale. These are current snapshots, without a historical publication clock. Native table text and labels are preserved. |
| [Transfermarkt public archive](https://github.com/dcaribou/transfermarkt-datasets) | Historical player appearances, lineups, goals/cards/substitution events, club games, transfers, valuations, player profiles and competition dictionary | Archive updates stopped in July 2026. It does not establish October squads. Coventry is absent from archived club records; older Hull/Ipswich metadata is stale. Historical-player profiles/valuation histories can include later periods at other clubs and must not be labeled current squad features. Future agreed transfers are flagged. |
| [ClubElo](https://clubelo.com/) | Current team ratings, chart rating timelines and available rated match histories | Public chart history is generally limited to four years; match tables expose a shorter recent window. The CSV API was unavailable. Retrospective ratings may have been revised; original historical publication/availability is unverified. |
| [TheSportsDB](https://www.thesportsdb.com/) | Club/stadium identity, capacity, location, formation year, website and cross-provider IDs | League search returns only ten clubs on the free endpoint; individual searches fill the remainder. Profiles are descriptive current metadata and can be stale. |
| [StatsBomb/Hudl open data](https://github.com/hudl/open-data) | Match events, passes, carries, duels, pressures, shots, lineups, player positions/cards and team/player event aggregates for available EPL seasons | Public EPL coverage is 2003/04 Arsenal matches and the 2015/16 season, not current-season events. The repository commit and actual Public Data User Agreement are retained. Research publication requires attribution/logo; underlying data has redistribution restrictions. Pitch coordinates use the provider's 120 by 80 convention rather than Understat's unit square. |

**Coverage is measured from files, not marketing claims.** See
`metadata/dataset_catalog.csv`, `metadata/team_coverage.csv`, provider coverage
tables and request manifests. A source with a partial current season does not
provide every historical player or every variable for promoted clubs. Empty
tables/audits mean zero recorded rows, not a proven real-world absence.

## Timing and betting data

Every successful source request records its URL, retrieval timestamp, response
size and SHA256 hash in `metadata/*_manifest.json`. Publication time is null when
unobserved. A retrieval clock is not proof that a historical observation was
available before a bet. Original JSON/HTML/CSV/gzip files remain under `data/raw`.
Flattened tables keep provider fields; arrays/nested objects may be JSON strings.
The historical xG downloads also do not establish the original model version or
which values were published at a historical decision time; simple match lagging
does not resolve that unobserved publication history.

Football-Data warns that Pinnacle's odds feed has been unreliable since July 23,
2025. Affected Pinnacle prices are preserved and flagged. Individual quote
timestamps, executable stake limits, fees and synchronized intraday bookmaker
prices are absent. Best odds collected at different times do not prove executable
arbitrage. No paid odds feed, account signup or betting execution was used.

For this project's chronological calibration/value-betting comparison, begin
with E0 completed matches, the explicit preclosing odds collection, and strictly
lagged team/player match statistics. The supplied team feature table includes
previous-season win proportion and season-to-date outperformance. Keep closing
odds, final results, current injuries, future fixtures and season-final snapshots
out of earlier predictors. Prior lower-division performance must retain division.

Providers disagree on some definitions and squad membership. Keep source-specific
IDs and metrics rather than replacing one provider's xG, assist or lineup values
with another's. Cross-source player links in the integrated overview accept
unambiguous same-club exact normalized names or a unique matching birth date plus
overlapping name tokens; unmatched identities remain explicit.

Understat's displayed team xG differs from additive shot/player xG in 2,701 of
6,180 collected team-match sides. Raw shot and player sums agree within 0.0000101.
The largest observed gap exactly reconciles with combining three rebound attempts
as one scoring probability, which supports a possession-adjustment interpretation
for that example. Possession IDs are unavailable, so this is not a reconstruction
of all adjusted chances. Keep displayed team xG and additive shot xG separate;
`understat/xg_basis_comparison` preserves the differences. Understat's native
`forecast` probabilities and expected points are derived from match chances;
they are not established pre-match bookmaker forecasts.

## Reuse and refresh

This is a private academic acquisition, with provider attribution and original
documentation retained. Provider terms differ. Football-Data's statement does
not grant an unrestricted open license; the Transfermarkt archive repository
declares CC0. Do not assume all original websites share that license. Paid/login
sources and blocked endpoints are gaps, not invented observations.

Collector scripts reproduce normalization and record access failures. FPL and
Football-Data support cached reconstruction; Understat/ESPN reuse saved JSON.
Current-context collectors fetch new snapshots. Copy/archive the dated package
before a live refresh to preserve the original point-in-time state, and update
the cohort/as-of setting deliberately if the league season changes.
