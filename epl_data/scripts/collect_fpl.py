"""Download FPL snapshots and historical match records for the current EPL cohort.

Run: python scripts/collect_fpl.py [--mode all|current|archive] [--refresh]
The original response is retained. Historical club membership is reconstructed at
the match, never inferred from a player's present-day or season-end club.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import hashlib
import io
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

from common import AS_OF_DATE, ROOT, SEASON, Collector, canonical_team, current_teams, now_utc, write_table

API = 'https://fantasy.premierleague.com/api'
REPO = 'https://github.com/vaastav/Fantasy-Premier-League'
ARCHIVE = 'https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League'
SEASONS = [f'{y}-{str(y+1)[-2:]}' for y in range(2016, 2027)]


class Run:
    def __init__(self, source, refresh=False):
        self.collector = Collector(source)
        self.refresh = refresh
        self.previous = {}
        manifest = ROOT / 'metadata' / f'{source}_manifest.json'
        if manifest.exists():
            for entry in json.loads(manifest.read_text(encoding='utf-8')).get('requests', []):
                if entry.get('status') in ('downloaded', 'reused_cached'):
                    self.previous[entry['path']] = entry
        self.tables = []

    def get(self, url, path, timeout=35):
        absolute = self.collector.raw / path
        relative = str(absolute.relative_to(ROOT)).replace('\\', '/')
        if absolute.exists() and not self.refresh and relative in self.previous:
            cached = absolute.read_bytes()
            if hashlib.sha256(cached).hexdigest() == self.previous[relative].get('sha256'):
                record = {**self.previous[relative], 'status': 'reused_cached', 'cache_checked_at_utc': now_utc(),
                          'cache_verified_sha256': True}
                with self.collector.lock:
                    self.collector.records.append(record)
                return cached, record
        for attempt in range(3):
            response = self.collector.fetch(url, path, timeout=timeout)
            if response is not None:
                # Locate by path rather than last item; requests run concurrently.
                with self.collector.lock:
                    record = next(r for r in reversed(self.collector.records)
                                  if r['path'] == relative and r.get('status') == 'downloaded')
                return response.content, record
            with self.collector.lock:
                record = next(r for r in reversed(self.collector.records) if r['path'] == relative)
            if record.get('http_status') in (400, 401, 403, 404):
                break
            time.sleep(0.5 * (attempt + 1))
        return None, record

    def table(self, frame, name, description):
        frame = frame.copy()
        for col in frame.columns:
            if frame[col].dtype == object:
                frame[col] = frame[col].map(lambda x: json.dumps(x, ensure_ascii=False) if isinstance(x, (dict, list)) else x)
        write_table(frame, self.collector.out / name)
        self.tables.append({'name': name, 'path': f'data/processed/{self.collector.source}/{name}.csv',
                            'rows': len(frame), 'columns': len(frame.columns),
                            'fields': list(frame.columns), 'description': description})
        print(f'{self.collector.source}/{name}: {len(frame):,} rows, {len(frame.columns)} columns', flush=True)

    def finish(self, notes):
        self.collector.finish(notes)
        path = ROOT / 'metadata' / f'{self.collector.source}_tables_manifest.json'
        path.write_text(json.dumps({'source': self.collector.source, 'created_at_utc': now_utc(),
                                   'tables': self.tables, 'notes': notes}, indent=2, ensure_ascii=False), encoding='utf-8')


def provenance(frame, record, season, role):
    frame = frame.copy()
    frame['season'] = season
    frame['source_url'] = record['url']
    frame['retrieved_at_utc'] = record['retrieved_at_utc']
    frame['requested_as_of_date'] = AS_OF_DATE
    frame['data_role'] = role
    return frame


def numeric(series):
    return pd.to_numeric(series, errors='coerce').astype('Int64')


def bool_column(series):
    return series.astype(str).str.casefold().map({'true': True, 'false': False, '1': True, '0': False})


def current_collection(workers, refresh):
    run = Run('fpl_current', refresh)
    roster = current_teams()
    names = dict(zip(roster.fpl_team_id, roster.team))
    content, b_record = run.get(f'{API}/bootstrap-static/', 'bootstrap-static.json')
    if content is None:
        run.finish({'error': 'Official bootstrap unavailable'})
        return
    bootstrap = json.loads(content)
    players = pd.DataFrame(bootstrap['elements'])
    players['canonical_team'] = players['team'].map(names)
    players = players[players.canonical_team.notna()].copy()
    types = {t['id']: t['singular_name'] for t in bootstrap['element_types']}
    players['position_name'] = players.element_type.map(types)
    players['fpl_price_millions'] = pd.to_numeric(players.now_cost, errors='coerce') / 10
    players['player_season_key'] = SEASON + ':' + players.id.astype(str)
    run.table(provenance(players, b_record, SEASON, 'current_snapshot'), 'players',
              'All native bootstrap player fields; present team, demographics, FPL prices, ownership, status, season totals and ranks. Snapshot totals are not historical pre-match features.')
    teams = pd.DataFrame(bootstrap['teams'])
    teams['canonical_team'] = teams.id.map(names)
    run.table(provenance(teams[teams.canonical_team.notna()], b_record, SEASON, 'current_snapshot'), 'teams',
              'Native team attributes/strengths; FPL played/points/wins may be placeholder zeros and are not authoritative standings.')
    for key in ('events', 'element_types', 'element_stats', 'chips', 'phases'):
        run.table(provenance(pd.DataFrame(bootstrap[key]), b_record, SEASON, 'current_snapshot'), key,
                  f'Native FPL {key}, nested native objects retained as JSON strings in flat tables.')
    fixture_content, fixture_record = run.get(f'{API}/fixtures/', 'fixtures.json')
    fixture_frame = pd.DataFrame(json.loads(fixture_content)) if fixture_content else pd.DataFrame()
    if not fixture_frame.empty:
        fixture_frame['home_team'] = fixture_frame.team_h.map(names)
        fixture_frame['away_team'] = fixture_frame.team_a.map(names)
        run.table(provenance(fixture_frame, fixture_record, SEASON, 'match_outcomes_and_schedule'), 'fixtures',
                  'Official fixture IDs, results, kickoffs, difficulty and native match stats. Future scheduling/difficulty is a retrieval-time snapshot.')
        stats = []
        for f in fixture_frame.to_dict('records'):
            for stat in f.get('stats', []):
                for side in ('h', 'a'):
                    for entry in stat.get(side, []):
                        stats.append({'fixture': f['id'], 'event': f['event'], 'kickoff_time': f['kickoff_time'],
                                      'team': names.get(f[f'team_{side}']), 'side': side, 'stat': stat['identifier'], **entry})
        run.table(provenance(pd.DataFrame(stats), fixture_record, SEASON, 'post_match_observations'), 'fixture_player_stats',
                  'Expanded native fixture stats: scoring, assists, own goals, disciplinary, saves, bonus and BPS entries.')
    fixture_home = dict(zip(fixture_frame.id, fixture_frame.team_h)) if not fixture_frame.empty else {}
    fixture_away = dict(zip(fixture_frame.id, fixture_frame.team_a)) if not fixture_frame.empty else {}
    history, upcoming, past = [], [], []
    statuses = []

    def summary(player):
        player_id = int(player['id'])
        data, record = run.get(f'{API}/element-summary/{player_id}/', f'element-summary/{player_id}.json')
        if data is None:
            return player, None, record
        return player, json.loads(data), record

    with cf.ThreadPoolExecutor(max_workers=workers) as executor:
        for count, (player, data, record) in enumerate(executor.map(summary, players.to_dict('records')), 1):
            statuses.append({'element': player['id'], 'code': player['code'], 'canonical_team': player['canonical_team'],
                             'status': 'downloaded' if data is not None else 'failed', 'source_url': record['url'],
                             'retrieved_at_utc': record['retrieved_at_utc']})
            if data is not None:
                identity = {'element': player['id'], 'player_code': player['code'], 'web_name': player['web_name'],
                            'current_roster_team': player['canonical_team'], 'position_name': player['position_name'],
                            'source_url': record['url'], 'retrieved_at_utc': record['retrieved_at_utc'],
                            'requested_as_of_date': AS_OF_DATE}
                for row in data.get('history', []):
                    own_id = fixture_home.get(row['fixture']) if row.get('was_home') else fixture_away.get(row['fixture'])
                    history.append({**identity, **row, 'season': SEASON, 'team_at_fixture_id': own_id,
                                    'canonical_team': names.get(own_id), 'opponent_name': names.get(row.get('opponent_team')),
                                    'team_mapping_method': 'official_fixture_home_away' if own_id else 'unresolved',
                                    'data_role': 'post_match_observations'})
                for row in data.get('fixtures', []):
                    upcoming.append({**identity, **row, 'season': SEASON,
                                     'home_team': names.get(row.get('team_h')), 'away_team': names.get(row.get('team_a')),
                                     'data_role': 'future_schedule_snapshot'})
                for row in data.get('history_past', []):
                    past.append({**identity, **row, 'historical_team': None,
                                 'team_mapping_status': 'FPL_history_past_does_not_identify_historical_team',
                                 'data_role': 'current_roster_career_snapshot_not_team_history'})
            if count % 50 == 0 or count == len(players):
                print(f'Official FPL summaries: {count}/{len(players)}', flush=True)
    run.table(pd.DataFrame(statuses), 'summary_download_status', 'Completeness audit for every current player summary request.')
    history_frame = pd.DataFrame(history)
    run.table(history_frame, 'player_match_history', 'Current-season player-fixture histories with actual club inferred from official fixture participants; includes zero-minute roster entries.')
    run.table(pd.DataFrame(upcoming), 'player_upcoming_fixtures', 'Upcoming player schedules and difficulty at collection time; redundant per-player fixture rows retained.')
    run.table(pd.DataFrame(past), 'current_roster_history_past', 'Past career totals for today\'s roster. Former team is unknown in this endpoint; these records must not be attributed to the current club.')
    if not history_frame.empty:
        totals_fields = [c for c in ['minutes', 'goals_scored', 'assists', 'total_points', 'bonus', 'bps', 'clean_sheets', 'goals_conceded', 'saves', 'yellow_cards', 'red_cards', 'expected_goals', 'expected_assists', 'expected_goal_involvements', 'expected_goals_conceded', 'clearances_blocks_interceptions', 'defensive_contribution', 'recoveries', 'tackles'] if c in history_frame]
        aggregation = history_frame.copy()
        for field in totals_fields:
            aggregation[field] = pd.to_numeric(aggregation[field], errors='coerce')
        team_totals = aggregation.groupby(['season', 'canonical_team', 'fixture', 'round'], dropna=False)[totals_fields].sum(min_count=1).reset_index()
        team_totals['data_role'] = 'derived_post_match_player_statistics_sum_by_club_fixture'
        run.table(team_totals, 'team_match_player_totals', 'Sum of official player history by actual club and fixture. Player clean sheets/points are sums; these do not substitute for team match outcomes.')
    # Official gameweek payloads retain the full native stats and points
    # explanations, including the newer defensive-contribution scoring.
    player_lookup = {int(p['id']): p for p in players.to_dict('records')}
    team_at_fixture = {(int(r['element']), int(r['fixture'])): r.get('canonical_team') for r in history}
    live_rows, explain_rows, dream_rows = [], [], []
    completed_events = [e['id'] for e in bootstrap['events'] if e.get('finished')]
    for event in completed_events:
        live_bytes, live_record = run.get(f'{API}/event/{event}/live/', f'event-live/{event}.json')
        if live_bytes:
            for native in json.loads(live_bytes).get('elements', []):
                element = native['id']
                if element not in player_lookup:
                    continue
                p = player_lookup[element]
                fixture_teams = sorted({team_at_fixture.get((element, int(x['fixture']))) for x in native.get('explain', []) if team_at_fixture.get((element, int(x['fixture'])))})
                live_rows.append({**native, **{f'stats.{k}': v for k, v in native.get('stats', {}).items()},
                                  'event': event, 'element': element, 'player_code': p['code'],
                                  'web_name': p['web_name'], 'current_roster_team': p['canonical_team'],
                                  'canonical_team': fixture_teams[0] if len(fixture_teams) == 1 else None,
                                  'teams_at_fixtures': fixture_teams,
                                  'team_mapping_status': 'matched_player_fixture_history' if len(fixture_teams) == 1 else 'unknown_or_multiple_teams',
                                  'season': SEASON, 'source_url': live_record['url'],
                                  'retrieved_at_utc': live_record['retrieved_at_utc'],
                                  'requested_as_of_date': AS_OF_DATE, 'data_role': 'post_match_gameweek_observations'})
                for explanation in native.get('explain', []):
                    for stat in explanation.get('stats', []):
                        explain_rows.append({**stat, 'event': event, 'element': element, 'player_code': p['code'],
                                             'fixture': explanation['fixture'],
                                             'canonical_team': team_at_fixture.get((element, int(explanation['fixture']))),
                                             'season': SEASON, 'source_url': live_record['url'],
                                             'retrieved_at_utc': live_record['retrieved_at_utc'],
                                             'requested_as_of_date': AS_OF_DATE, 'data_role': 'post_match_fantasy_points_explanation'})
        dream_bytes, dream_record = run.get(f'{API}/dream-team/{event}/', f'dream-team/{event}.json')
        if dream_bytes:
            dream = json.loads(dream_bytes)
            for entry in dream.get('team', []):
                p = player_lookup.get(entry['element'])
                if p:
                    dream_rows.append({**entry, 'event': event, 'player_code': p['code'], 'web_name': p['web_name'],
                                       'current_roster_team': p['canonical_team'],
                                       'is_top_player': dream.get('top_player', {}).get('id') == entry['element'],
                                       'season': SEASON, 'source_url': dream_record['url'],
                                       'retrieved_at_utc': dream_record['retrieved_at_utc'],
                                       'requested_as_of_date': AS_OF_DATE, 'data_role': 'post_match_gameweek_selection'})
    run.table(pd.DataFrame(live_rows), 'gameweek_live_player_stats', 'Official completed-gameweek stats, native explanation JSON and all native fields. Club comes from fixture history where uniquely resolvable.')
    run.table(pd.DataFrame(explain_rows), 'gameweek_fantasy_points_explanations', 'One row per player-fixture-scoring-category explanation with native points/value/modification fields.')
    run.table(pd.DataFrame(dream_rows), 'gameweek_dream_teams', 'Official best XI and top player flags for finished gameweeks.')
    notes_bytes, notes_record = run.get(f'{API}/team/set-piece-notes/', 'team-set-piece-notes.json')
    if notes_bytes:
        native_notes = json.loads(notes_bytes)
        notes_frame = pd.DataFrame(native_notes.get('teams', []))
        if not notes_frame.empty:
            notes_frame['canonical_team'] = notes_frame.id.map(names)
            notes_frame['source_last_updated'] = native_notes.get('last_updated')
            run.table(provenance(notes_frame[notes_frame.canonical_team.notna()], notes_record, SEASON, 'current_editorial_snapshot'), 'team_set_piece_notes', 'Native set-piece editorial notes; the present response contains placeholder check-back messages, rather than useful taker information.')
    run.finish({'players_requested': len(players), 'summary_successes': sum(s['status']=='downloaded' for s in statuses),
                'summary_failures': sum(s['status']=='failed' for s in statuses),
                'finished_gameweeks': [e['id'] for e in bootstrap['events'] if e.get('finished')],
                'current_team_snapshot_fields_may_be_placeholders': True,
                'history_past_former_team': 'not supplied by FPL; deliberately left unknown'})


def read_csv(content):
    if content is None:
        return pd.DataFrame()
    # The oldest archive exports include Windows-1252/Latin-1 names. Decode
    # without replacing characters; original source bytes remain authoritative.
    for encoding in ('utf-8-sig', 'cp1252', 'latin-1'):
        try:
            frame = pd.read_csv(io.BytesIO(content), low_memory=False, encoding=encoding)
            frame.attrs['source_csv_encoding'] = encoding
            return frame
        except UnicodeDecodeError:
            continue
    raise ValueError('Unable to decode source CSV')


def archive_collection(workers, refresh):
    run = Run('fpl_archive', refresh)
    membership = current_teams()
    code_names = dict(zip(membership.fpl_team_code, membership.team))
    commit_bytes, commit_record = run.get('https://api.github.com/repos/vaastav/Fantasy-Premier-League/commits/master', 'repository_commit.json')
    commit = json.loads(commit_bytes).get('sha') if commit_bytes else None
    # Pin every file to one commit when GitHub supplies a revision.
    revision = commit or 'master'
    files = ['teams.csv', 'fixtures.csv', 'players_raw.csv', 'gws/merged_gw.csv', 'player_idlist.csv']

    def fetch_one(task):
        season, file = task
        url = f'{ARCHIVE}/{revision}/data/{season}/{file}'
        data, record = run.get(url, f'{season}/{file}', timeout=60)
        frame = read_csv(data)
        if not frame.empty:
            frame['source_csv_encoding'] = frame.attrs.get('source_csv_encoding')
            record['csv_encoding'] = frame.attrs.get('source_csv_encoding')
        return season, file, frame, record

    downloads = {}
    with cf.ThreadPoolExecutor(max_workers=workers) as executor:
        for season, file, frame, record in executor.map(fetch_one, [(s, f) for s in SEASONS for f in files]):
            downloads[(season, file)] = (frame, record)
            print(f'Archive {season}/{file}: {len(frame):,} rows', flush=True)
    all_gw, all_players, all_teams, all_fixtures, unresolved, audits, all_idlists, removed_duplicates = [], [], [], [], [], [], [], []
    for season in SEASONS:
        teams, team_record = downloads[(season, 'teams.csv')]
        fixtures, fixture_record = downloads[(season, 'fixtures.csv')]
        players, player_record = downloads[(season, 'players_raw.csv')]
        gw, gw_record = downloads[(season, 'gws/merged_gw.csv')]
        ids, id_record = downloads[(season, 'player_idlist.csv')]
        team_names, source_names, team_codes = {}, {}, {}
        if not teams.empty:
            team_names = {int(row.id): canonical_team(row['name']) for _, row in teams.iterrows()}
            source_names = {int(row.id): row['name'] for _, row in teams.iterrows()}
            team_codes = dict(zip(teams.id, teams.code))
            teams['canonical_team'] = teams['name'].map(canonical_team)
            all_teams.append(provenance(teams[teams.canonical_team.notna()], team_record, season, 'archive_team_snapshot'))
        elif not players.empty and {'team', 'team_code'}.issubset(players.columns):
            pair = players[['team', 'team_code']].dropna().drop_duplicates()
            unambiguous = pair.groupby('team').team_code.nunique()
            pair = pair[pair.team.isin(unambiguous[unambiguous == 1].index)]
            team_codes = dict(zip(pair.team.astype(int), pair.team_code.astype(int)))
            team_names = {int(t): code_names.get(int(c)) for t, c in team_codes.items()}
            source_names = {t: name for t, name in team_names.items() if name}
            inferred = pd.DataFrame([{'id': t, 'code': c, 'canonical_team': team_names.get(t),
                                      'mapping_method': 'players_raw_stable_team_code'} for t, c in team_codes.items()])
            all_teams.append(provenance(inferred[inferred.canonical_team.notna()], player_record, season, 'reconstructed_season_team_lookup'))
        if not players.empty:
            players['canonical_team'] = numeric(players.team).map(team_names)
            players['player_season_key'] = season + ':' + players.id.astype(str)
            all_players.append(provenance(players[players.canonical_team.notna()], player_record, season, 'archive_player_snapshot_not_match_time_membership'))
        fixture_home, fixture_away = {}, {}
        if not fixtures.empty and {'id', 'team_h', 'team_a'}.issubset(fixtures.columns):
            f = fixtures.drop_duplicates('id')
            fixture_home, fixture_away = dict(zip(f.id, f.team_h)), dict(zip(f.id, f.team_a))
        if not gw.empty:
            homeflag = bool_column(gw.was_home)
            # Each record supplies the opposition. Players on both sides of a fixture
            # identify the two participants without relying on season-end transfers.
            for flag, target in ((False, fixture_home), (True, fixture_away)):
                group = gw.loc[homeflag.eq(flag), ['fixture', 'opponent_team']].dropna().drop_duplicates()
                unique = group.groupby('fixture').opponent_team.nunique()
                group = group[group.fixture.isin(unique[unique == 1].index)]
                for row in group.itertuples(index=False):
                    target.setdefault(int(row.fixture), int(row.opponent_team))
            own_ids = pd.Series(np.where(homeflag.fillna(False), gw.fixture.map(fixture_home), gw.fixture.map(fixture_away)), index=gw.index)
            own_ids[homeflag.isna()] = np.nan
            own_ids = numeric(own_ids)
            gw['team_at_fixture_id'] = own_ids
            gw['canonical_team'] = own_ids.map(team_names)
            gw['team_at_fixture_source_name'] = own_ids.map(source_names)
            gw['opponent_name'] = numeric(gw.opponent_team).map(source_names)
            gw['opponent_is_current_cohort'] = numeric(gw.opponent_team).map(team_names).notna()
            gw['team_mapping_method'] = 'fixture_table_home_away' if not fixtures.empty else 'opponent_ids_reverse_inferred_fixture'
            gw.loc[own_ids.isna(), 'team_mapping_method'] = 'unresolved_fixture'
            gw.loc[own_ids.notna() & ~own_ids.isin(team_names), 'team_mapping_method'] = 'unresolved_season_team_lookup'
            if 'team' in gw.columns:
                native_name = gw.team.map(canonical_team)
                gw['native_team_name_disagrees_with_fixture'] = native_name.notna() & gw.canonical_team.notna() & native_name.ne(gw.canonical_team)
            else:
                gw['native_team_name_disagrees_with_fixture'] = False
            if not players.empty and 'id' in players and 'code' in players:
                ambiguous_ids = players.groupby('id').code.nunique()
                stable = players[players.id.isin(ambiguous_ids[ambiguous_ids == 1].index)].drop_duplicates('id')
                gw['player_code'] = numeric(gw.element).map(dict(zip(stable.id, stable.code)))
                gw['position_type'] = numeric(gw.element).map(dict(zip(stable.id, stable.element_type))) if 'element_type' in stable else np.nan
            gw['player_season_key'] = season + ':' + gw.element.astype(str)
            gw['minutes_played_positive'] = pd.to_numeric(gw.minutes, errors='coerce').gt(0)
            missing = own_ids.isna() | (own_ids.notna() & ~own_ids.isin(team_names))
            if missing.any():
                unresolved.append(provenance(gw[missing], gw_record, season, 'excluded_unresolved_membership_audit'))
            cohort = gw[gw.canonical_team.notna()].copy()
            before_dedup = len(cohort)
            # The archive can retain a postponed placeholder and its eventual
            # played fixture (notably Manchester City-Arsenal in March/June 2020),
            # or identical duplicate exports. Prefer a completed result, then the
            # latest source kickoff/gameweek. Save every removed original row.
            cohort['_complete_result'] = cohort.team_a_score.notna() & cohort.team_h_score.notna()
            cohort['_source_order'] = np.arange(len(cohort))
            ordered = cohort.sort_values(['_complete_result', 'kickoff_time', 'GW', '_source_order'], na_position='first')
            removed = ordered[ordered.duplicated(['element', 'fixture'], keep='last')].copy()
            if not removed.empty:
                removed['exclusion_reason'] = np.where(~removed['_complete_result'], 'superseded_postponed_fixture_placeholder', 'duplicate_player_fixture_source_row')
                removed_duplicates.append(provenance(removed.drop(columns=['_complete_result', '_source_order']), gw_record, season, 'excluded_duplicate_or_superseded_rows_audit'))
            cohort = ordered.drop_duplicates(['element', 'fixture'], keep='last').sort_values('_source_order').drop(columns=['_complete_result', '_source_order'])
            # Archive current-season coverage is distinct from official current history.
            all_gw.append(provenance(cohort, gw_record, season, 'post_match_archive_observations'))
            if not ids.empty:
                eligible_ids = set(numeric(cohort.element).dropna())
                id_col = 'id' if 'id' in ids else 'element'
                if id_col in ids:
                    all_idlists.append(provenance(ids[numeric(ids[id_col]).isin(eligible_ids)], id_record, season, 'season_specific_player_identity_lookup'))
            audits.append({'season': season, 'source_gameweek_rows': len(gw), 'cohort_gameweek_rows': len(cohort),
                           'cohort_rows_before_duplicate_removal': before_dedup,
                           'duplicate_or_superseded_rows_removed': len(removed),
                           'cohort_positive_minute_rows': int(cohort.minutes_played_positive.sum()),
                           'excluded_noncohort_rows': int((~missing & gw.canonical_team.isna()).sum()),
                           'unresolved_team_rows': int(missing.sum()), 'missing_player_code_rows_in_cohort': int(cohort.player_code.isna().sum()) if 'player_code' in cohort else len(cohort),
                           'native_team_name_conflicts_in_cohort': int(cohort.native_team_name_disagrees_with_fixture.sum()),
                           'min_gameweek': int(pd.to_numeric(gw.GW, errors='coerce').min()) if 'GW' in gw else None,
                           'max_gameweek': int(pd.to_numeric(gw.GW, errors='coerce').max()) if 'GW' in gw else None,
                           'cohort_teams': int(cohort.canonical_team.nunique()),
                           'cohort_players': int(cohort.element.nunique()), 'source_fixture_rows': len(fixtures),
                           'source_players_snapshot_rows': len(players), 'source_team_rows': len(teams),
                           'repository_commit': commit})
        if not fixtures.empty:
            focal = []
            for side, opponent_side in [('h', 'a'), ('a', 'h')]:
                sub = fixtures.copy()
                sub['canonical_team'] = numeric(sub[f'team_{side}']).map(team_names)
                sub['is_home'] = side == 'h'
                sub['opponent_name'] = numeric(sub[f'team_{opponent_side}']).map(source_names)
                sub['opponent_is_current_cohort'] = numeric(sub[f'team_{opponent_side}']).map(team_names).notna()
                focal.append(sub[sub.canonical_team.notna()])
            all_fixtures.append(provenance(pd.concat(focal, ignore_index=True), fixture_record, season, 'archive_focal_team_fixture_records'))
    joined = pd.concat(all_gw, ignore_index=True) if all_gw else pd.DataFrame()
    run.table(joined, 'player_gameweeks', 'Historical player-fixture rows for the current 20-club cohort, filtered by actual club at each match. Native fields unioned; zero-minute records are retained and flagged. Numeric element IDs are season-specific.')
    for tables, name, description in [
        (all_players, 'players_season_snapshots', 'Archive bootstrap player totals, prices and status for eligible clubs at archive snapshot time; club assignment is descriptive and can differ from match-time club.'),
        (all_teams, 'teams_season_snapshots', 'Cohort clubs\' native archive team snapshots; early seasons reconstructed from stable team codes, not invented team stats.'),
        (all_fixtures, 'team_fixture_history', 'One focal-team row per archive fixture involving an eligible club; each native match field retained. A match can appear twice when both clubs are in the cohort.'),
        (all_idlists, 'player_identity_by_season', 'Native archive player name/season-local ID lookups restricted to players with cohort match records.'),
        (unresolved, 'unresolved_membership_rows', 'Unresolved records excluded from curated match history; original fields retained for review.'),
        (removed_duplicates, 'duplicate_or_superseded_rows', 'Original player-fixture rows removed because the source duplicated them or retained a postponed zero-stat placeholder before the actual fixture.')]:
        empty = pd.DataFrame(columns=['season', 'element', 'fixture', 'team_at_fixture_id', 'team_mapping_method', 'source_url', 'retrieved_at_utc'])
        run.table(pd.concat(tables, ignore_index=True) if tables else empty, name, description)
    run.table(pd.DataFrame(audits), 'season_coverage', 'Source-versus-curated counts, season-local team mapping quality, archive gameweek coverage and exclusions.')
    if not joined.empty:
        sums = [c for c in ['minutes', 'goals_scored', 'assists', 'total_points', 'bonus', 'bps', 'clean_sheets', 'goals_conceded', 'saves', 'yellow_cards', 'red_cards', 'expected_goals', 'expected_assists', 'expected_goal_involvements', 'expected_goals_conceded', 'clearances_blocks_interceptions', 'defensive_contribution', 'recoveries', 'tackles'] if c in joined]
        aggregation = joined.copy()
        for field in sums:
            aggregation[field] = pd.to_numeric(aggregation[field], errors='coerce')
        keys = ['season', 'canonical_team', 'element', 'player_code']
        aggregated = aggregation.groupby(keys, dropna=False)[sums].sum(min_count=1).reset_index()
        aggregated['data_role'] = 'derived_post_match_player_team_season_totals'
        run.table(aggregated, 'player_team_season_totals', 'Observed match records summed by actual club/player/season; split transfers into separate clubs. Partial current seasons and historical source gaps remain partial.')
        teams_agg = aggregation.groupby(['season', 'canonical_team', 'GW'], dropna=False)[sums].sum(min_count=1).reset_index()
        teams_agg['data_role'] = 'derived_player_statistics_sum_by_team_gameweek'
        run.table(teams_agg, 'team_gameweek_player_totals', 'Sums of archived player statistics by club/gameweek; fantasy points and player clean sheets are sums, not league-table/team clean-sheet metrics.')
    run.finish({'repository': REPO, 'repository_commit': commit, 'requested_seasons': SEASONS,
                'club_filter': 'actual focal club at fixture time is in current_teams.csv',
                'transfer_handling': 'fixture participants plus was_home; current roster and season-end player teams never determine historical match club',
                'identity': 'element IDs scoped to season; player_code is cross-season join candidate when available, subject to source verification',
                'source_commit_timestamp': json.loads(commit_bytes).get('commit', {}).get('committer', {}).get('date') if commit_bytes else None,
                'coverage': audits})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=['all', 'current', 'archive'], default='all')
    parser.add_argument('--workers', type=int, default=5)
    parser.add_argument('--refresh', action='store_true', help='Fetch responses again instead of using verified cached raw files.')
    args = parser.parse_args()
    workers = max(1, min(args.workers, 6))
    if args.mode in ('all', 'current'):
        current_collection(workers, args.refresh)
    if args.mode in ('all', 'archive'):
        archive_collection(workers, args.refresh)


if __name__ == '__main__':
    main()
