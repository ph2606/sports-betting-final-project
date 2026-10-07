# Advanced football acquisition

Requested membership date: 2026-10-06.

Curated rows focus on the 20 current 2026-27 Premier League clubs. Historical opponents
are retained for match context. Raw league and match responses retain the source in full.

Sources: [Understat](https://understat.com/league/EPL/2026),
[ESPN Premier League](https://www.espn.com/soccer/league/_/name/eng.1),
and the public JSON endpoints recorded in the source manifests.

Understat uses getLeagueData and getMatchData JSON endpoints from its own frontend scripts;
the old embedded JSON scraping method no longer applies. Team histories cover xG/xGA,
non-penalty xG, PPDA numerator/denominator, deep completions and xPoints. Player season/match
rows and individual shots retain positions, minutes, assists/xA, xGChain/xGBuildup, shot coordinates,
situation, body part, last action, and assist-provider name.

The separate getTeamData acquisition adds team context aggregates by situation, formation,
game state, match-minute interval, shot zone, attack speed and shot result across acquired seasons.

ESPN supplies current rosters and player demographics (birth date, citizenship, height, weight,
position), season statistics, recent-season schedules/standings and completed match summaries
with team event statistics, lineups, venue, attendance, officials and any supplied odds.

Use source-specific IDs; player name matching across providers needs a reviewed crosswalk.
Snapshot retrieval times are not field-level publication timestamps. Historical realized
performance is appropriate for lagged features only. Current rosters cannot reconstruct
historical squad membership. Player season summaries across transfers are explicitly flagged.

Completed-match forecast__w/d/l fields are supplied retrospective outputs. They must be treated
as post-match derived unless a provider publication time before kickoff is independently verified.

ESPN legacy coach fields can be stale and should not be used for current coaches; empty
injury arrays do not establish fitness. Transfer/valuation supplements are catalogued separately
by other collectors. ESPN odds are snapshots without full event-time exchange/order-book history.

Additional access probes are recorded in advanced_access_manifest.json: FBref returned
HTTP403, Sofascore returned HTTP403, and Fotmob's older /api/leagues endpoint returned
HTTP404. These sources contributed no team/player data. No authentication or paywall bypass was used.

A stopped initial acquisition left a small number of cached responses before the first manifest
checkpoint. Their acquisition timestamp was recovered from the saved response file's modification
time and is explicitly labelled retrieval_timestamp_basis in the manifest.

Understat displayed team/league xG and additive raw shot/player xG use different numerical
bases. Their differences are preserved in xg_basis_comparison. Rebound/possession adjustment
is an inference supported by the largest raw-source sample; full official aggregation methodology
and possession IDs are unavailable, so the remaining differences are retained as an explicit
limitation. Do not replace displayed team xG with raw shot sums or force per-shot allocations.

Acquisition results:

```json
{
  "understat": {
    "season_start_years": [
      2014,
      2015,
      2016,
      2017,
      2018,
      2019,
      2020,
      2021,
      2022,
      2023,
      2024,
      2025,
      2026
    ],
    "table_rows": {
      "team_match_metrics": 6180,
      "team_season_metrics": 180,
      "matches": 4438,
      "player_season_metrics": 4736,
      "player_match_metrics": 88533,
      "shots": 83455,
      "xg_basis_comparison": 6180
    },
    "completed_match_detail_requests": 4108,
    "failed_match_detail_requests": 0,
    "membership_scope": "2026-27 current clubs; excluded clubs appear only as match opponents or raw responses",
    "player_season_multi_club_totals": "Source aggregates across transfers. Flagged rows must not be attributed wholly to one club.",
    "datetime_timezone": "Provider datetime strings preserved as supplied; no timezone invented.",
    "future_matches": "Fixture rows retained; actual match/player/shot rows require isResult and date <= 2026-10-06.",
    "current_season_latest_observed_actual_match": "2026-09-20 15:30:00",
    "current_season_completed_matches": 50,
    "retrieval_time_recovery": "Where an interrupted first acquisition had saved responses before its manifest checkpoint, timestamp recovered from original saved file mtime and explicitly labelled retrieval_timestamp_basis.",
    "xg_aggregation_caution": "Displayed team/league xG is not interchangeable with additive shot/player xG. Observed differences preserved in xg_basis_comparison. Possession/rebound adjustment is an inference directly supported by raw arithmetic for the largest-gap sample; no official complete aggregation methodology or possession IDs supplied, so all discrepancies are not individually reconciled.",
    "api_reference": "https://understat.com/js/league.min.js and https://understat.com/js/match.min.js expose getLeagueData and getMatchData.",
    "forecast_field_caution": "forecast__w/d/l in completed match records are supplied retrospective outputs. Treat as post-match derived unless a verified provider publication timestamp before kickoff is separately obtained."
  },
  "espn": {
    "table_rows": {
      "team_profiles": 20,
      "player_profiles": 585,
      "player_season_stats": 585,
      "player_injury_reports": 0,
      "standings": 37,
      "team_schedules": 746,
      "match_info": 424,
      "team_match_stats": 746,
      "player_match_lineups": 14909,
      "match_key_events": 5989,
      "match_odds_snapshots": 1294
    },
    "current_roster_clubs": 20,
    "summary_requests": 424,
    "successful_summary_requests": 424,
    "schedule_seasons_requested": [
      2025,
      2026
    ],
    "current_season_latest_observed_actual_match": "2026-09-20T15:30Z",
    "current_season_completed_matches": 50,
    "player_profile_field_coverage": {
      "total": 585,
      "birth_date": 579,
      "citizenship": 579,
      "height": 550,
      "weight": 525,
      "position": 585
    },
    "freshness": "Live provider snapshots, with supplied timestamps and season labels. Historical schedules/matches reflect final state, not prediction-time availability.",
    "known_stale_coach_fields": "Roster endpoint includes stale legacy coach entries (e.g. Arsene Wenger for Arsenal). Raw field retained; coaches must not be used as current coaching data.",
    "units": "Player height is ESPN inches; weight is pounds. Provider display units are also retained.",
    "injury_coverage": "Only supplied roster injury arrays, not an authoritative injury registry. Empty reports are unknown coverage, not confirmation all fit.",
    "odds_limitation": "ESPN retrospective/current snapshots lack full exchange/order-book and time history; not usable as contemporaneous arbitrage proof.",
    "membership_scope": "Curated team/player rows only current 2026-27 clubs; excluded clubs may appear as opponents/raw payload context."
  },
  "understat_context": {
    "team_season_datasets": 180,
    "planned_team_season_datasets": 180,
    "table_rows": {
      "team_context_metrics": 6552
    },
    "categories": [
      "attackSpeed",
      "formation",
      "gameState",
      "result",
      "shotZone",
      "situation",
      "timing"
    ],
    "scope": "Current2026-27club whitelist, all acquired EPL seasons2014-2026whereclubparticipated.",
    "aggregation_caution": "Context-group xG follows getTeamData provider statistics. Preserve this separately from displayed league/team xG; all are supplied outputs, not forced to one basis.",
    "availability_caution": "Historical final season context statistics require lagging; they were not all available before each historical match."
  }
}
```
