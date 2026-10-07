"""Build source catalogs, schema dictionaries, identity links and a review workbook."""
from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

from common import AS_OF_DATE, ROOT, current_teams, now_utc, write_table

DESCRIPTIONS = {
    'fpl_current/players': 'Current FPL player snapshot; all provider fields.',
    'fpl_current/teams': 'Current FPL team strengths and metadata.',
    'fpl_current/player_match_history': 'Player fixture statistics; lag before pre-match use.',
    'fpl_current/fixtures': 'Current-season completed and future scheduled fixtures.',
    'fpl_archive/player_gameweeks': 'Historical player-fixture records with actual team attribution.',
    'fpl_archive/duplicate_or_superseded_rows': 'Quarantined duplicate and postponed placeholder rows.',
    'football_data/matches_current_cohort': 'Native historical statistics and odds, at least one eligible club.',
    'football_data/team_match_history': 'One row per eligible team per match; opponent oriented metrics.',
    'football_data/team_match_lagged_features': 'Strictly earlier-date rolling/season-to-date/prior-season inputs.',
    'football_data/match_odds_1x2_long': 'Bookmaker or aggregate 1X2 odds, collection time and reliability flags.',
    'transfermarkt_current/player_squads': 'Current roster/contract/demographic/valuation snapshot.',
    'transfermarkt_current/injury_snapshot': 'Current reported injuries/suspensions; timing unverified.',
    'transfermarkt_archive/player_profiles': 'Historical cohort-associated player profiles; July archive metadata.',
    'transfermarkt_archive/player_valuations': 'Valuation histories of players associated with eligible clubs.',
    'understat/shots': 'Individual match shots and xG; observed after play.',
    'understat/player_match_metrics': 'Understat individual match player statistics.',
    'understat/team_match_metrics': 'Understat xG/expected points/PPDA/deep team match metrics.',
    'clubelo/rating_history': 'Retrospective chart timeline; original availability unverified.',
    'integrated/current_player_master': 'FPL roster plus unambiguous Transfermarkt snapshot links.',
}
MEANINGS = {
    'minutes': ('Minutes recorded by the provider.', 'minutes'),
    'time': ('Understat playing time, or provider time field; see native schema.', 'provider dependent'),
    'xG': ('Understat expected goals, provider model.', 'expected goals'),
    'xA': ('Understat expected assists, provider model.', 'expected assists'),
    'npxG': ('Understat expected goals excluding penalties.', 'expected goals'),
    'expected_goals': ('FPL expected goals, provider model.', 'expected goals'),
    'expected_assists': ('FPL expected assists, provider model.', 'expected assists'),
    'now_cost': ('FPL current player price; divide by 10 for millions.', '0.1 million FPL currency'),
    'selected_by_percent': ('FPL selection/ownership percentage at retrieval.', 'percent'),
    'status': ('Provider status; FPL a=available,d=doubtful,i=injured,s=suspended,u=unavailable.', 'category'),
    'news': ('FPL current availability news; not a historical injury archive.', 'text'),
    'news_added': ('Provider time associated with current news; does not recover older overwritten news.', 'datetime'),
    'birth_date': ('Provider player date of birth.', 'date'),
    'retrieved_at_utc': ('When this observation/source was collected; not original publication time.', 'UTC datetime'),
    'source_published_at_utc': ('Original publication time if observed; null means unobserved.', 'UTC datetime'),
    'data_role': ('Snapshot, outcome, historical or derived context classification.', 'category'),
    'season': ('Football season label; IDs may reset each season.', 'season label'),
    'team': ('Canonical eligible focal team, or native numeric FPL team ID depending on table.', 'name or ID'),
    'canonical_team': ('Canonical eligible focal club name.', 'name'),
    'market_value_eur': ('Transfermarkt estimated player market value at snapshot.', 'EUR'),
    'market_value_in_eur': ('Transfermarkt valuation estimate, not a quoted trade price.', 'EUR'),
    'Elo': ('ClubElo rating from the retrieved timeline, potentially revised.', 'rating points'),
    'FTHG': ('Full-time home goals.', 'goals'), 'FTAG': ('Full-time away goals.', 'goals'),
    'FTR': ('Regular league result: H=home win, D=draw, A=away win.', 'category'),
    'HS': ('Home shots.', 'shots'), 'AS': ('Away shots.', 'shots'),
    'HST': ('Home shots on target.', 'shots'), 'AST': ('Away shots on target.', 'shots'),
    'HC': ('Home corners.', 'corners'), 'AC': ('Away corners.', 'corners'),
    'HF': ('Home fouls.', 'fouls'), 'AF': ('Away fouls.', 'fouls'),
    'HY': ('Home yellow cards.', 'cards'), 'AY': ('Away yellow cards.', 'cards'),
    'HR': ('Home red cards.', 'cards'), 'AR': ('Away red cards.', 'cards'),
}


def read_table(path):
    parquet = Path(path).with_suffix('.parquet')
    if parquet.exists():
        return pd.read_parquet(parquet)
    try:
        return pd.read_csv(path, low_memory=False)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()


def normalized_name(value):
    if pd.isna(value):
        return ''
    ascii_text = ''.join(char for char in unicodedata.normalize('NFKD', str(value)) if not unicodedata.combining(char))
    return re.sub('[^a-z0-9]+', ' ', ascii_text.casefold()).strip()


def link_current_players():
    base = ROOT / 'data/processed/fpl_current/players.csv'
    other = ROOT / 'data/processed/transfermarkt_current/player_squads.csv'
    if not base.exists():
        return
    players = read_table(base).rename(columns={'team': 'fpl_team_id', 'canonical_team': 'team',
                                               'id': 'fpl_player_id', 'code': 'fpl_player_code'})
    players['player_name'] = players['first_name'].fillna('') + ' ' + players['second_name'].fillna('')
    links = []
    if other.exists():
        squads = read_table(other)
        squads['_normalized_name'] = squads['player_name'].map(normalized_name)
        squads['_birth_date'] = pd.to_datetime(squads.get('date_of_birth_age', pd.Series(index=squads.index, dtype='object')).str.extract(r'(\d{2}/\d{2}/\d{4})')[0],
                                               format='%d/%m/%Y', errors='coerce').dt.strftime('%Y-%m-%d')
        for player in players.to_dict('records'):
            team_squad = squads.loc[squads['team'].eq(player['team'])]
            name = normalized_name(player['player_name'])
            candidates = team_squad.loc[team_squad['_normalized_name'].eq(name)]
            method = 'unique_exact_normalized_name_same_club'
            if len(candidates) != 1:
                dob = player.get('birth_date')
                candidates = team_squad.loc[team_squad['_birth_date'].eq(dob)] if pd.notna(dob) else team_squad.iloc[0:0]
                candidates = candidates.loc[candidates['_normalized_name'].map(lambda value: bool(set(value.split()) & set(name.split())))]
                method = 'unique_birthdate_shared_name_token_same_club'
            if len(candidates) == 1:
                candidate = candidates.iloc[0]
                links.append({'fpl_player_id': player['fpl_player_id'], 'team': player['team'],
                              'fpl_player_name': player['player_name'],
                              'transfermarkt_player_id': candidate['transfermarkt_player_id'],
                              'transfermarkt_player_name': candidate['player_name'], 'link_method': method})
            else:
                links.append({'fpl_player_id': player['fpl_player_id'], 'team': player['team'],
                              'fpl_player_name': player['player_name'], 'transfermarkt_player_id': None,
                              'transfermarkt_player_name': None, 'link_method': 'unmatched_or_ambiguous'})
        crosswalk = pd.DataFrame(links)
        # Reject many-to-one identities rather than silently duplicating a squad record.
        linked = crosswalk['transfermarkt_player_id'].notna()
        collisions = crosswalk.loc[linked, 'transfermarkt_player_id'].duplicated(keep=False)
        if collisions.any():
            bad_ids = set(crosswalk.loc[linked].loc[collisions, 'transfermarkt_player_id'])
            mask = crosswalk['transfermarkt_player_id'].isin(bad_ids)
            crosswalk.loc[mask, 'transfermarkt_player_id'] = None
            crosswalk.loc[mask, 'link_method'] = 'rejected_many_to_one_collision'
        write_table(crosswalk, ROOT / 'data/processed/integrated/player_identity_links.csv')
        players = players.merge(crosswalk[['fpl_player_id', 'transfermarkt_player_id', 'link_method']],
                                on='fpl_player_id', how='left', validate='one_to_one')
        keep = ['transfermarkt_player_id', 'player_name', 'market_value_eur', 'height', 'foot',
                'contract', 'joined', 'nat_image_labels', 'date_of_birth_age', 'retrieved_at_utc',
                'birth_date', 'age_at_snapshot', 'height_cm', 'nationalities', 'contract_end_date',
                'club_join_date', 'position']
        keep = [column for column in keep if column in squads]
        tm = squads[keep].rename(columns={column: 'tm_' + column for column in keep if column != 'transfermarkt_player_id'})
        players = players.merge(tm, on='transfermarkt_player_id', how='left', validate='many_to_one')
    preferred = ['team', 'player_name', 'position_name', 'can_select', 'status', 'news',
                 'minutes', 'goals_scored', 'assists', 'expected_goals', 'expected_assists',
                 'total_points', 'fpl_price_millions', 'selected_by_percent', 'birth_date',
                 'tm_age_at_snapshot', 'tm_height_cm', 'tm_nationalities', 'tm_foot',
                 'tm_market_value_eur', 'tm_contract_end_date', 'fpl_player_id',
                 'fpl_player_code', 'transfermarkt_player_id', 'link_method', 'season',
                 'retrieved_at_utc', 'tm_retrieved_at_utc']
    preferred = [column for column in preferred if column in players]
    players = players[preferred + [column for column in players if column not in preferred]]
    write_table(players, ROOT / 'data/processed/integrated/current_player_master.csv')


def team_crosswalk():
    teams = current_teams()
    sources = [('transfermarkt_current/club_market_values.csv', 'team', 'transfermarkt_club_id'),
               ('espn/team_profiles.csv', 'team', 'espn_team_id'),
               ('understat/team_season_metrics.csv', 'team', 'understat_team_id'),
               ('sportsdb/club_profiles.csv', 'team', 'idTeam')]
    for relative, name_column, id_column in sources:
        path = ROOT / 'data/processed' / relative
        if not path.exists():
            continue
        data = read_table(path)[[name_column, id_column]].drop_duplicates()
        if name_column != 'team':
            data = data.rename(columns={name_column: 'team'})
        if id_column == 'idTeam':
            data = data.rename(columns={id_column: 'sportsdb_team_id'})
        teams = teams.merge(data, on='team', how='left', validate='one_to_one')
    teams['clubelo_slug'] = teams['team'].map(__import__('collect_context').CLUBELO_NAMES)
    teams.to_csv(ROOT / 'metadata/team_identity_crosswalk.csv', index=False)
    return teams


def build():
    metadata = ROOT / 'metadata'
    metadata.mkdir(exist_ok=True)
    link_current_players()
    crosswalk = team_crosswalk()
    catalog, dictionary, coverage, quality = [], [], [], []
    cohort = set(current_teams()['team'])
    for path in sorted((ROOT / 'data/processed').glob('*/*.csv')):
        relative = path.relative_to(ROOT).as_posix()
        source, table = path.parent.name, path.stem
        data = read_table(path)
        nonempty = len(data) > 0
        # Explicit focal columns must be checked even if a noncohort value appears.
        team_column = 'canonical_team' if 'canonical_team' in data else None
        if team_column is None:
            team_column = next((column for column in ['team', 'team_name'] if column in data
                                and (data[column].dropna().isin(cohort).any() or
                                     (not nonempty and pd.api.types.is_string_dtype(data[column])))), None)
        season_column = next((column for column in ['season', 'season_label'] if column in data), None)
        date_column = next((column for column in ['match_date', 'kickoff_time', 'date', 'datetime', 'Date'] if column in data), None)
        dates = pd.to_datetime(data[date_column], errors='coerce', utc=True) if date_column and nonempty else None
        role = ', '.join(str(value) for value in data['data_role'].dropna().unique()[:8]) if 'data_role' in data else 'source-specific; see SOURCE_GUIDE.md'
        catalog.append({'source': source, 'table': table, 'csv_path': relative,
                        'parquet_path': path.with_suffix('.parquet').relative_to(ROOT).as_posix() if path.with_suffix('.parquet').exists() else None,
                        'rows': len(data), 'columns': len(data.columns), 'csv_bytes': path.stat().st_size,
                        'eligible_focal_teams': data[team_column].nunique() if team_column else None,
                        'season_min': data[season_column].min() if season_column and nonempty else None,
                        'season_max': data[season_column].max() if season_column and nonempty else None,
                        'observation_date_min': str(dates.min()) if dates is not None else None,
                        'observation_date_max': str(dates.max()) if dates is not None else None,
                        'data_role': role, 'description': DESCRIPTIONS.get(f'{source}/{table}', table.replace('_', ' ') + '; retain native schema and source definitions.')})
        for column in data.columns:
            description, unit = MEANINGS.get(column, ('Provider-native or derived field; consult source notes/native documentation.', 'provider dependent'))
            if column.startswith('tm_'):
                description = 'Current Transfermarkt linked snapshot: ' + column[3:].replace('_', ' ') + '.'
            dictionary.append({'source': source, 'table': table, 'field': column,
                               'dtype': str(data[column].dtype), 'nonnull_rows': int(data[column].notna().sum()),
                               'missing_fraction': float(data[column].isna().mean()) if nonempty else None,
                               'description': description, 'unit': unit})
        print(f'catalog {source}/{table}: {len(data):,}', flush=True)
        if team_column and nonempty:
            groups = [team_column] + ([season_column] if season_column else [])
            for key, group in data.groupby(groups, dropna=False):
                key = key if isinstance(key, tuple) else (key,)
                coverage.append({'source': source, 'table': table, 'team': key[0],
                                 'season': key[1] if len(key) > 1 else 'snapshot/all', 'rows': len(group)})
        quality.append({'check': f'{source}/{table}: CSV readable', 'passed': True, 'detail': f'{len(data):,} rows; {len(data.columns)} fields'})
        quality.append({'check': f'{source}/{table}: typed Parquet available',
                        'passed': path.with_suffix('.parquet').exists(),
                        'detail': relative})
        if team_column:
            valid = data[team_column].dropna().isin(cohort).all()
            quality.append({'check': f'{source}/{table}: focal clubs within cohort', 'passed': bool(valid), 'detail': team_column})
        del data
    manifest_rows, hashes_checked, hashes_failed = [], 0, []
    for path in sorted(metadata.glob('*_manifest.json')):
        content = json.loads(path.read_text(encoding='utf-8'))
        for record in content.get('requests', []):
            row = {key: value for key, value in record.items() if not isinstance(value, (dict, list))}
            row['manifest'] = path.name
            manifest_rows.append(row)
            if record.get('sha256') and record.get('path'):
                source_path = ROOT / record['path']
                actual = hashlib.sha256(source_path.read_bytes()).hexdigest() if source_path.exists() else None
                hashes_checked += 1
                if actual != record['sha256']:
                    hashes_failed.append(record['path'])
    quality.append({'check': 'Saved source SHA256 hashes', 'passed': not hashes_failed,
                    'detail': f'{hashes_checked} verified; mismatches={hashes_failed[:20]}'})
    quality.append({'check': 'Exactly 20 current Premier League members', 'passed': len(cohort) == 20,
                    'detail': 'West Ham, Burnley and Wolves are not focal clubs.'})
    for name, rows in [('dataset_catalog', catalog), ('field_dictionary', dictionary),
                       ('team_coverage', coverage), ('source_requests', manifest_rows), ('quality_checks', quality)]:
        pd.DataFrame(rows).to_csv(metadata / f'{name}.csv', index=False)
    failures = [row for row in manifest_rows if row.get('status') == 'failed' or row.get('parse_error')]
    (metadata / 'access_failures.json').write_text(json.dumps(failures, indent=2, ensure_ascii=False), encoding='utf-8')
    summary = {'requested_as_of_date': AS_OF_DATE, 'catalog_built_at_utc': now_utc(),
               'club_count': len(cohort), 'tables': len(catalog), 'sources': sorted(set(row['source'] for row in catalog)),
               'raw_request_records': len(manifest_rows), 'raw_hashes_verified': hashes_checked,
               'failed_requests': len(failures), 'failed_quality_checks': [row for row in quality if not row['passed']],
               'table_counts': {f"{row['source']}/{row['table']}": row['rows'] for row in catalog}}
    (metadata / 'acquisition_summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    sheets = {'Current clubs': crosswalk, 'Dataset catalog': pd.DataFrame(catalog),
              'Team coverage': pd.DataFrame(coverage), 'Field dictionary': pd.DataFrame(dictionary),
              'Quality checks': pd.DataFrame(quality)}
    for name, relative in [('Current players', 'integrated/current_player_master.csv'),
                           ('Club values', 'transfermarkt_current/club_market_values.csv'),
                           ('Reported injuries', 'transfermarkt_current/injury_snapshot.csv'),
                           ('Current fixtures', 'fpl_current/fixtures.csv')]:
        path = ROOT / 'data/processed' / relative
        if path.exists():
            data = read_table(path)
            if name == 'Current fixtures':
                preferred = ['season', 'event', 'kickoff_time', 'home_team', 'away_team',
                             'finished', 'team_h_score', 'team_a_score', 'id']
                data = data[preferred + [column for column in data if column not in preferred]]
            sheets[name] = data
    workbook = ROOT / 'EPL_data_overview.xlsx'
    with pd.ExcelWriter(workbook, engine='openpyxl') as writer:
        for name, data in sheets.items():
            data.to_excel(writer, sheet_name=name, index=False)
            worksheet = writer.sheets[name]
            worksheet.freeze_panes = 'C2' if name == 'Current players' else 'A2'
            worksheet.auto_filter.ref = worksheet.dimensions
            for column in worksheet.columns:
                letter = column[0].column_letter
                worksheet.column_dimensions[letter].width = min(45, max(13, len(str(column[0].value or '')) + 2))
    print(json.dumps(summary, indent=2), flush=True)
    if summary['failed_quality_checks']:
        raise RuntimeError('Review failed quality checks in metadata/quality_checks.csv')
    write_readme(summary)


def write_readme(summary):
    counts = summary['table_counts']
    player_snapshot = read_table(ROOT / 'data/processed/fpl_current/players.csv')
    selectable = int(player_snapshot['can_select'].sum())
    def count(name):
        value = counts.get(name)
        return f'{value:,}' if value is not None else 'see catalog'
    event_total = sum(value for key, value in counts.items() if key.startswith('statsbomb/events_'))
    text = f'''# Premier League data collection

Collected for the EPL part of Aman Dhillon and Panagiotis Housos's
[September 30 ML Sports Betting proposal](../../ML_Sports_Betting_Project_Proposal.pdf).
The cohort is the **20 current 2026/27 clubs**, verified as of **October 6, 2026**.
West Ham, Burnley and Wolves are excluded as focal clubs. Coventry, Hull and
Ipswich are included. Historical matches against former clubs retain the opponent.

Start with [EPL_data_overview.xlsx](EPL_data_overview.xlsx) for a spreadsheet
overview, or [01_data_inventory.ipynb](01_data_inventory.ipynb) for Python.
Full data is in **data/processed**, with a CSV and typed Parquet copy per table
where supported. Original source responses are in **data/raw**.

| Collection | Actual downloaded coverage |
|---|---|
| Team match statistics and bookmaker odds | {count('football_data/matches_current_cohort')} matches involving current clubs; Premier League and three lower tiers, 1993/94–2026/27 |
| Team match observations and lagged features | {count('football_data/team_match_history')} focal club-match observations; division preserved |
| Current Fantasy Premier League | {count('fpl_current/players')} FPL-listed players, **{selectable:,} selectable**, 380 fixtures, {count('fpl_current/player_match_history')} player-fixture records |
| Historical Fantasy Premier League | {count('fpl_archive/player_gameweeks')} cleaned player-fixture records, 2016/17–2026/27; 69 removed duplicate/postponement rows audited separately |
| Understat advanced performance | {count('understat/team_match_metrics')} team-match rows and {count('understat/player_season_metrics')} player-season summaries, 2014/15–2026/27; detailed match players/shots in their own tables |
| ESPN current/historical context | 20 clubs, {count('espn/player_profiles')} player profiles, {count('espn/match_info')} completed match summaries, {count('espn/player_match_lineups')} lineup records |
| Current Transfermarkt | 20 club value summaries, {count('transfermarkt_current/player_squads')} roster entries, {count('transfermarkt_current/injury_snapshot')} reported availability records, {count('transfermarkt_current/season_transfers')} transfer-page rows |
| Historical Transfermarkt archive | {count('transfermarkt_archive/appearances')} appearances, {count('transfermarkt_archive/game_lineups')} lineup rows, {count('transfermarkt_archive/player_valuations')} valuation observations; transfers/events/profiles also saved |
| ClubElo and stadium/club profiles | 20 current ratings, {count('clubelo/rating_history')} rating-history observations, all 20 club/stadium profiles |
| StatsBomb open event data | {event_total:,} focal-team events across {count('statsbomb/matches')} matches in the available EPL seasons 2003/04 and 2015/16, plus lineups and player/team event summaries |

Current 2026/27 completed-match coverage is **50 matches through September 20,
2026 (five per club)**. Retrieval on October 6 does not imply games occurred
after that last observed date. The FPL archive's current-season GW1 overlaps the
official current histories; prefer official FPL for 2026/27 instead of appending
both. FPL-listed entries and provider squads have different eligibility definitions.

The catalog contains **{summary['tables']} tables**. Row counts across different
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
'''
    (ROOT / 'README.md').write_text(text, encoding='utf-8')


if __name__ == '__main__':
    build()
