# Premier League data collection

Collected for the EPL part of Aman Dhillon and Panagiotis Housos's
[September 30 ML Sports Betting proposal](../ML_Sports_Betting_Project_Proposal.pdf).
The cohort is the **20 current 2026/27 clubs**, verified as of **October 6, 2026**.
West Ham, Burnley and Wolves are excluded as focal clubs. Coventry, Hull and
Ipswich are included. Historical matches against former clubs retain the opponent.

Start with [EPL_data_overview.xlsx](EPL_data_overview.xlsx) for a spreadsheet
overview, or [01_data_inventory.ipynb](01_data_inventory.ipynb) for Python.
Full data is in **data/processed**, with a CSV and typed Parquet copy per table
where supported. Original source responses are in **data/raw**.

| Collection | Actual downloaded coverage |
|---|---|
| Team match statistics and bookmaker odds | 21,782 matches involving current clubs; Premier League and three lower tiers, 1993/94–2026/27 |
| Team match observations and lagged features | 27,304 focal club-match observations; division preserved |
| Current Fantasy Premier League | 667 FPL-listed players, **562 selectable**, 380 fixtures, 3,216 player-fixture records |
| Historical Fantasy Premier League | 176,282 cleaned player-fixture records, 2016/17–2026/27; 69 removed duplicate/postponement rows audited separately |
| Understat advanced performance | 6,180 team-match rows and 4,736 player-season summaries, 2014/15–2026/27; detailed match players/shots in their own tables |
| ESPN current/historical context | 20 clubs, 585 player profiles, 424 completed match summaries, 14,909 lineup records |
| Current Transfermarkt | 20 club value summaries, 543 roster entries, 77 reported availability records, 607 transfer-page rows |
| Historical Transfermarkt archive | 123,483 appearances, 158,876 lineup rows, 59,298 valuation observations; transfers/events/profiles also saved |
| ClubElo and stadium/club profiles | 20 current ratings, 3,896 rating-history observations, all 20 club/stadium profiles |
| StatsBomb open event data | 930,848 focal-team events across 362 matches in the available EPL seasons 2003/04 and 2015/16, plus lineups and player/team event summaries |

Current 2026/27 completed-match coverage is **50 matches through September 20,
2026 (five per club)**. Retrieval on October 6 does not imply games occurred
after that last observed date. The FPL archive's current-season GW1 overlaps the
official current histories; prefer official FPL for 2026/27 instead of appending
both. FPL-listed entries and provider squads have different eligibility definitions.

The catalog contains **90 tables**. Row counts across different
tables are overlapping grains and must not be added as independent observations.
Published field definitions, source URLs, missingness, season/team coverage and
raw SHA256 hashes are preserved:

- [Dataset catalog](metadata/dataset_catalog.csv)
- [Field dictionary and missingness](metadata/field_dictionary.csv)
- [Team coverage by source and season](metadata/team_coverage.csv)
- [Club IDs across providers](metadata/team_identity_crosswalk.csv)
- [Acquisition/quality summary](metadata/acquisition_summary.json)
- [Source guide and timing limitations](SOURCE_GUIDE.md)
- [FPL collection details](metadata/fpl_notes.md)
- [Football-Data collection details](metadata/football_data_notes.md)
- [Additional provider details](metadata/advanced_notes.md)
- [StatsBomb event coverage and license](metadata/statsbomb_notes.md)
- [Match source links and conflicts](metadata/match_link_validation.json)

This is the data-acquisition step. No prediction model or betting backtest has
been fitted. Current injury/news/valuation snapshots, season-final totals,
current-match results and closing odds cannot become earlier pre-match features.
Pinnacle's known unreliable feed after July 23, 2025 is flagged. Static odds do
not establish simultaneous executable arbitrage. Paid historical odds and
unverified historical publication times remain gaps; blocked sources are logged.

## Reproduce and inspect

From the course workspace in PowerShell:

```powershell
python final_project/epl_data/scripts/collect_fpl.py --mode all
python final_project/epl_data/scripts/collect_football_data.py --reuse-raw
python final_project/epl_data/scripts/collect_advanced.py
python final_project/epl_data/scripts/collect_transfermarkt_archive.py --reuse-raw
python final_project/epl_data/scripts/collect_statsbomb.py
python final_project/epl_data/scripts/normalize_context.py
python final_project/epl_data/scripts/build_match_links.py
python final_project/epl_data/scripts/build_catalog.py
```

The context collector `collect_context.py` acquires ClubElo, SportsDB and current
Transfermarkt pages. It fetches new snapshots; preserve this dated package before
refreshing. The active cohort and cutoff live in `scripts/common.py` and
`metadata/current_teams.csv`; update them deliberately for another season/date.
The archive's player profiles and valuation histories are associated historical
players, not a claim about the October roster. CSV text columns ending in
`__json`/`provider_cells` preserve nested provider records as JSON.

Example:

```python
import pandas as pd
players = pd.read_parquet('final_project/epl_data/data/processed/integrated/current_player_master.parquet')
matches = pd.read_parquet('final_project/epl_data/data/processed/football_data/matches_current_cohort.parquet')
epl_matches = matches.loc[matches['division'].eq('E0')]
```
