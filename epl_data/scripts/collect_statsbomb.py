"""Collect official StatsBomb open Premier League events for today's club cohort.

Raw originals are retained; events are streamed into one CSV/Parquet pair per
season, keeping native nested objects as JSON and adding convenience columns.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import csv
import hashlib
import io
import json
import re
import time
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from common import AS_OF_DATE, ROOT, Collector, canonical_team, current_teams, now_utc, write_table

REPO = 'https://github.com/hudl/open-data'
RAW = 'https://raw.githubusercontent.com/hudl/open-data'
INTEGER_NATIVE = {'index', 'period', 'minute', 'second', 'possession'}
BOOL_NATIVE = {'counterpress', 'under_pressure', 'off_camera', 'out'}
INTEGER_ADDED = {'match_id', 'competition_id', 'season_id', 'statsbomb_team_id', 'statsbomb_opponent_team_id', 'statsbomb_player_id', 'event_type_id'}
BOOL_ADDED = {'pass_complete'}
FLOAT_ADDED = {'location_x', 'location_y', 'pass_end_x', 'pass_end_y', 'carry_end_x', 'carry_end_y', 'shot_end_x', 'shot_end_y', 'shot_end_z', 'pass_length', 'pass_angle', 'shot_statsbomb_xg'}
ADDED = ['match_id', 'competition_id', 'season_id', 'season', 'match_date', 'canonical_team',
         'statsbomb_team_id', 'statsbomb_opponent_team_id', 'opponent_name', 'statsbomb_player_id',
         'player_name', 'event_type_id', 'event_type_name', 'location_x', 'location_y',
         'pass_end_x', 'pass_end_y', 'carry_end_x', 'carry_end_y', 'shot_end_x', 'shot_end_y',
         'shot_end_z', 'pass_length', 'pass_angle', 'pass_complete', 'pass_outcome',
         'shot_statsbomb_xg', 'shot_outcome', 'shot_body_part', 'shot_type',
         'source_url', 'retrieved_at_utc', 'requested_as_of_date', 'data_role']


def compact(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':')) if isinstance(value, (dict, list)) else value


def get_name(value):
    return value.get('name') if isinstance(value, dict) else None


def coordinate(value, index):
    return value[index] if isinstance(value, list) and len(value) > index else None


class Acquisition:
    def __init__(self, refresh):
        self.c = Collector('statsbomb')
        self.refresh = refresh
        self.tables = []
        self.prior = {}
        manifest = ROOT / 'metadata/statsbomb_manifest.json'
        if manifest.exists():
            for record in json.loads(manifest.read_text(encoding='utf-8')).get('requests', []):
                if record.get('status') in ('downloaded', 'reused_cached'):
                    self.prior[record['path']] = record

    def fetch(self, url, relative):
        path = self.c.raw / relative
        key = path.relative_to(ROOT).as_posix()
        if path.exists() and not self.refresh and key in self.prior:
            data = path.read_bytes()
            if hashlib.sha256(data).hexdigest() == self.prior[key].get('sha256'):
                record = {**self.prior[key], 'status': 'reused_cached', 'cache_verified_sha256': True,
                          'cache_checked_at_utc': now_utc()}
                with self.c.lock:
                    self.c.records.append(record)
                return data, record
        for attempt in range(3):
            response = self.c.fetch(url, relative, timeout=60)
            with self.c.lock:
                record = next(r for r in reversed(self.c.records) if r['path'] == key)
            if response is not None:
                return response.content, record
            if record.get('http_status') in (400, 401, 403, 404):
                break
            time.sleep(0.5 * (attempt + 1))
        return None, record

    def table(self, data, name, description):
        frame = pd.DataFrame(data)
        for column in frame.columns:
            frame[column] = frame[column].map(compact)
        write_table(frame, self.c.out / name)
        self.add_table(name, len(frame), list(frame.columns), description)

    def add_table(self, name, rows, fields, description):
        self.tables.append({'name': name, 'rows': rows, 'columns': len(fields), 'fields': fields,
                            'csv_path': f'data/processed/statsbomb/{name}.csv',
                            'parquet_path': f'data/processed/statsbomb/{name}.parquet', 'description': description})
        print(f'StatsBomb {name}: {rows:,} rows, {len(fields)} columns', flush=True)

    def finish(self, notes):
        self.c.finish(notes)
        (ROOT / 'metadata/statsbomb_tables_manifest.json').write_text(
            json.dumps({'source': 'statsbomb', 'created_at_utc': now_utc(), 'tables': self.tables,
                        'notes': notes}, indent=2, ensure_ascii=False), encoding='utf-8')


def provenance(record, role):
    return {'source_url': record['url'], 'retrieved_at_utc': record['retrieved_at_utc'],
            'requested_as_of_date': AS_OF_DATE, 'data_role': role}


def match_teams(match):
    home, away = match['home_team'], match['away_team']
    return {home['home_team_id']: {'source_name': home['home_team_name'],
                                 'canonical_team': canonical_team(home['home_team_name']),
                                 'opponent_id': away['away_team_id'], 'opponent_name': away['away_team_name'], 'is_home': True},
            away['away_team_id']: {'source_name': away['away_team_name'],
                                 'canonical_team': canonical_team(away['away_team_name']),
                                 'opponent_id': home['home_team_id'], 'opponent_name': home['home_team_name'], 'is_home': False}}


def row_context(info, team_id, record, role):
    match = info['match']
    participant = (info.get('teams') or match_teams(match))[team_id]
    return {'match_id': match['match_id'], 'competition_id': match['competition']['competition_id'],
            'season_id': match['season']['season_id'], 'season': info['season'],
            'match_date': match['match_date'], 'canonical_team': participant['canonical_team'],
            'statsbomb_team_id': team_id, 'statsbomb_opponent_team_id': participant['opponent_id'],
            'opponent_name': participant['opponent_name'], **provenance(record, role)}


def flatten_event(event, info):
    team_id = event.get('team', {}).get('id')
    participant = (info.get('teams') or match_teams(info['match'])).get(team_id)
    if not participant or not participant['canonical_team']:
        return None
    row = {key: compact(value) for key, value in event.items()}
    player = event.get('player') or {}
    passing, carry, shot = event.get('pass') or {}, event.get('carry') or {}, event.get('shot') or {}
    row.update(row_context(info, team_id, info['event_record'], 'post_match_event_observations'))
    row.update(statsbomb_player_id=player.get('id'), player_name=player.get('name'),
               event_type_id=event.get('type', {}).get('id'), event_type_name=get_name(event.get('type')),
               location_x=coordinate(event.get('location'), 0), location_y=coordinate(event.get('location'), 1),
               pass_end_x=coordinate(passing.get('end_location'), 0), pass_end_y=coordinate(passing.get('end_location'), 1),
               carry_end_x=coordinate(carry.get('end_location'), 0), carry_end_y=coordinate(carry.get('end_location'), 1),
               shot_end_x=coordinate(shot.get('end_location'), 0), shot_end_y=coordinate(shot.get('end_location'), 1),
               shot_end_z=coordinate(shot.get('end_location'), 2), pass_length=passing.get('length'), pass_angle=passing.get('angle'),
               pass_complete=(not passing.get('outcome')) if 'pass' in event else None,
               pass_outcome=get_name(passing.get('outcome')), shot_statsbomb_xg=shot.get('statsbomb_xg'),
               shot_outcome=get_name(shot.get('outcome')), shot_body_part=get_name(shot.get('body_part')), shot_type=get_name(shot.get('type')))
    return row


def add_metrics(target, event):
    name = get_name(event.get('type'))
    target['events'] += 1
    target['passes'] += name == 'Pass'
    target['carries'] += name == 'Carry'
    target['pressures'] += name == 'Pressure'
    target['duels'] += name == 'Duel'
    target['dribbles'] += name == 'Dribble'
    target['interceptions'] += name == 'Interception'
    target['ball_recoveries'] += name == 'Ball Recovery'
    target['clearances'] += name == 'Clearance'
    target['blocks'] += name == 'Block'
    target['fouls_committed'] += name == 'Foul Committed'
    target['fouls_won'] += name == 'Foul Won'
    target['under_pressure_events'] += bool(event.get('under_pressure'))
    target['counterpress_events'] += bool(event.get('counterpress'))
    if name == 'Pass':
        passing = event.get('pass') or {}
        target['completed_passes'] += not passing.get('outcome')
        target['crosses'] += bool(passing.get('cross'))
        target['pass_length_sum'] += passing.get('length', 0) or 0
        target['goal_assist_passes'] += bool(passing.get('goal_assist'))
        target['shot_assist_passes'] += bool(passing.get('shot_assist'))
    if name == 'Shot':
        shot = event.get('shot') or {}
        target['shots'] += 1
        target['shot_goals'] += get_name(shot.get('outcome')) == 'Goal'
        target['shots_on_target'] += get_name(shot.get('outcome')) in ('Goal', 'Saved', 'Saved To Post')
        target['shot_xg_observed'] += shot.get('statsbomb_xg') is not None
        target['shot_statsbomb_xg_sum'] += shot.get('statsbomb_xg', 0) or 0


def process_lineup(info, lineups, lineup_rows, positions, cards):
    teams = match_teams(info['match'])
    for team in lineups:
        team_id = team['team_id']
        if team_id not in teams or not teams[team_id]['canonical_team']:
            continue
        context = row_context(info, team_id, info['lineup_record'], 'historical_match_lineup')
        for player in team.get('lineup', []):
            lineup_rows.append({**player, **context, 'source_team_name': team['team_name'],
                                'positions_recorded': bool(player.get('positions')),
                                'started_match': any(p.get('start_reason') == 'Starting XI' for p in player.get('positions', [])),
                                'data_role': 'historical_match_lineup_including_unused_substitutes'})
            for pos in player.get('positions', []):
                positions.append({**pos, **context, 'player_id': player['player_id'], 'player_name': player['player_name']})
            for card in player.get('cards', []):
                cards.append({**card, **context, 'player_id': player['player_id'], 'player_name': player['player_name']})


def stream_events(run, infos, fieldsets):
    counts = {}
    for season in sorted(fieldsets):
        native = sorted(fieldsets[season])
        fields = native + ADDED
        assert len(fields) == len(set(fields)), 'Native and added fields collided'
        def dtype(name):
            if name in INTEGER_NATIVE | INTEGER_ADDED:
                return pa.int64()
            if name in BOOL_NATIVE | BOOL_ADDED:
                return pa.bool_()
            if name in FLOAT_ADDED or name == 'duration':
                return pa.float64()
            return pa.string()
        schema = pa.schema([pa.field(name, dtype(name), nullable=True) for name in fields])
        name = 'events_' + season.replace('-', '_')
        csv_path = run.c.out / f'{name}.csv'
        parquet_path = run.c.out / f'{name}.parquet'
        row_count = 0
        with csv_path.open('w', encoding='utf-8', newline='') as output, pq.ParquetWriter(parquet_path, schema, compression='zstd') as writer:
            csv_writer = csv.DictWriter(output, fieldnames=fields)
            csv_writer.writeheader()
            for info in infos:
                if info['season'] != season or not info.get('event_ok'):
                    continue
                events = json.loads((ROOT / info['event_record']['path']).read_bytes())
                rows = []
                for event in events:
                    row = flatten_event(event, info)
                    if row is None:
                        continue
                    for key, value in list(row.items()):
                        if value is not None and pa.types.is_string(schema.field(key).type) and not isinstance(value, str):
                            row[key] = str(value)
                    rows.append(row)
                csv_writer.writerows(rows)
                if rows:
                    writer.write_table(pa.Table.from_pylist(rows, schema=schema))
                row_count += len(rows)
        counts[season] = row_count
        run.add_table(name, row_count, fields, 'Every native event field, with nested objects/lists preserved as compact JSON; only actual focal clubs in current cohort. Convenience IDs, types, coordinates, passing and shot/xG columns added. Post-match observations, not historical pre-match inputs.')
    return counts


def collect(workers, refresh):
    run = Acquisition(refresh)
    commit_bytes, _ = run.fetch('https://api.github.com/repos/hudl/open-data/commits/master', 'repository_commit.json')
    commit = json.loads(commit_bytes).get('sha') if commit_bytes else None
    revision = commit or 'master'
    base = f'{RAW}/{revision}'
    documents = ['LICENSE.pdf', 'README.md', 'doc/Open Data Events v4.0.0.pdf', 'doc/Open Data Lineups v2.0.0.pdf', 'doc/Open Data Matches v3.0.0.pdf']
    for document in documents:
        url = f'{base}/{document.replace(" ", "%20")}'
        run.fetch(url, document)
    license_path = run.c.raw / 'LICENSE.pdf'
    if license_path.exists():
        from pypdf import PdfReader
        text = '\n'.join(page.extract_text() or '' for page in PdfReader(license_path).pages)
        (run.c.raw / 'LICENSE_extracted_text.txt').write_text(text, encoding='utf-8')
    bytes_, comp_record = run.fetch(f'{base}/data/competitions.json', 'competitions.json')
    if bytes_ is None:
        run.finish({'error': 'Competitions unavailable', 'repository': REPO, 'repository_commit': commit})
        return
    competitions = [c for c in json.loads(bytes_) if c.get('competition_name') == 'Premier League' and c.get('country_name') == 'England' and c.get('competition_gender') == 'male']
    run.table([{**c, **provenance(comp_record, 'available_open_competition_season_metadata')} for c in competitions], 'competitions', 'Only official open English Premier League competition-seasons, not arbitrary other competitions.')
    infos, selected_matches, focal_matches, season_audit = [], [], [], []
    for competition in competitions:
        competition_id, season_id = competition['competition_id'], competition['season_id']
        data, record = run.fetch(f'{base}/data/matches/{competition_id}/{season_id}.json', f'matches/{competition_id}/{season_id}.json')
        if data is None:
            continue
        matches = json.loads(data)
        season_native = competition['season_name']
        first, last = season_native.split('/')
        season = first + '-' + last[-2:]
        selected = 0
        observed_teams = set()
        for match in matches:
            teams = match_teams(match)
            eligible = [tid for tid, team in teams.items() if team['canonical_team']]
            if not eligible:
                continue
            selected += 1
            info = {'match': match, 'season': season, 'teams': teams}
            infos.append(info)
            selected_matches.append({**match, 'native_season': match.get('season'), 'season': season, 'eligible_home_team': canonical_team(match['home_team']['home_team_name']),
                                     'eligible_away_team': canonical_team(match['away_team']['away_team_name']),
                                     **provenance(record, 'historical_match_context')})
            for tid in eligible:
                participant = teams[tid]
                observed_teams.add(participant['canonical_team'])
                focal_matches.append({**match, 'native_season': match.get('season'), **row_context(info, tid, record, 'historical_focal_team_match'),
                                      'is_home': participant['is_home'], 'source_team_name': participant['source_name'],
                                      'goals_for': match['home_score'] if participant['is_home'] else match['away_score'],
                                      'goals_against': match['away_score'] if participant['is_home'] else match['home_score']})
        season_audit.append({'season': season, 'competition_id': competition_id, 'season_id': season_id,
                             'source_matches': len(matches), 'matches_involving_cohort': selected,
                             'focal_clubs': len(observed_teams), 'focal_club_names': sorted(observed_teams),
                             'official_360_available': competition.get('match_available_360') is not None})
    run.table(selected_matches, 'matches', 'Native historical match metadata for matches involving at least one current-cohort club; all opponent context retained.')
    run.table(focal_matches, 'team_matches', 'One actual focal-club row per match, with native metadata and oriented outcome; current cohort only.')
    print(f'StatsBomb eligible matches to download: {len(infos)}', flush=True)

    def download(info):
        match_id = info['match']['match_id']
        event_bytes, event_record = run.fetch(f'{base}/data/events/{match_id}.json', f'events/{match_id}.json')
        lineup_bytes, lineup_record = run.fetch(f'{base}/data/lineups/{match_id}.json', f'lineups/{match_id}.json')
        return {**info, 'event_record': event_record, 'lineup_record': lineup_record,
                'event_ok': event_bytes is not None, 'lineup_ok': lineup_bytes is not None}

    with cf.ThreadPoolExecutor(max_workers=workers) as pool:
        fetched = []
        for count, info in enumerate(pool.map(download, infos), 1):
            fetched.append(info)
            if count % 25 == 0 or count == len(infos):
                print(f'StatsBomb downloads: {count}/{len(infos)} matches', flush=True)
                run.c.finish({'phase': 'raw_downloads_in_progress', 'repository': REPO,
                              'repository_commit': commit, 'completed_match_downloads': count,
                              'eligible_match_downloads': len(infos)})
    infos = fetched
    # Checkpoint provenance before event processing so a interrupted run can resume.
    run.c.finish({'phase': 'raw_downloads_complete', 'repository': REPO, 'repository_commit': commit})
    lineup_rows, positions, cards, coverage = [], [], [], []
    fieldsets = defaultdict(set)
    team_metrics, player_metrics = {}, {}
    team_types, player_types = Counter(), Counter()
    team_contexts, player_contexts = {}, {}
    for index, info in enumerate(infos, 1):
        match = info['match']
        match_id = match['match_id']
        source_count, focal_count, unmapped_count = 0, 0, 0
        seen_players = set()
        participants = info.get('teams') or match_teams(match)
        if info['lineup_ok']:
            process_lineup(info, json.loads((ROOT / info['lineup_record']['path']).read_bytes()), lineup_rows, positions, cards)
        if info['event_ok']:
            for event in json.loads((ROOT / info['event_record']['path']).read_bytes()):
                source_count += 1
                team_id = event.get('team', {}).get('id')
                participant = participants.get(team_id)
                if participant is None:
                    unmapped_count += 1
                    continue
                if not participant['canonical_team']:
                    continue
                focal_count += 1
                fieldsets[info['season']].update(event.keys())
                tk = (match_id, team_id)
                context = row_context(info, team_id, info['event_record'], 'derived_post_match_event_counts')
                team_contexts[tk] = context
                add_metrics(team_metrics.setdefault(tk, Counter()), event)
                event_name = get_name(event.get('type'))
                team_types[(match_id, team_id, event_name)] += 1
                player = event.get('player') or {}
                if player.get('id') is not None:
                    pk = (match_id, team_id, player['id'])
                    seen_players.add(pk)
                    player_contexts[pk] = {**context, 'player_id': player['id'], 'player_name': player.get('name')}
                    add_metrics(player_metrics.setdefault(pk, Counter()), event)
                    player_types[(*pk, event_name)] += 1
        coverage.append({'match_id': match_id, 'season': info['season'], 'match_date': match['match_date'],
                         'home_team_source': match['home_team']['home_team_name'], 'away_team_source': match['away_team']['away_team_name'],
                         'event_download_success': info['event_ok'], 'lineup_download_success': info['lineup_ok'],
                         'source_events': source_count, 'cohort_events': focal_count,
                         'unresolved_source_team_events': unmapped_count, 'cohort_players_with_events': len(seen_players)})
        if index % 50 == 0 or index == len(infos):
            print(f'StatsBomb processing audit: {index}/{len(infos)}', flush=True)
    event_counts = stream_events(run, infos, fieldsets)
    run.table(lineup_rows, 'player_match_lineups', 'Native per-match player lineups at actual cohort clubs; includes unused substitutes, flagged by position records. Cards/position intervals retained as JSON.')
    run.table(positions, 'player_match_positions', 'Every native position interval, reasons, period and source clock; no invented playing minutes.')
    run.table(cards, 'player_match_cards', 'Every native lineup card entry at an actual cohort club.')
    def metric_rows(metrics, contexts):
        rows = []
        all_metrics = sorted(set().union(*(metric.keys() for metric in metrics.values())))
        for key, metric in metrics.items():
            row = {**{name: metric.get(name, 0) for name in all_metrics}, **contexts[key]}
            if row.get('shots', 0) and not row.get('shot_xg_observed', 0):
                row['shot_statsbomb_xg_sum'] = None
            rows.append(row)
        return rows
    run.table(metric_rows(team_metrics, team_contexts), 'team_match_event_metrics', 'Derived counts of passes/carries/pressures/duels/shots and shot xG; actual event club. Native own-goal events remain in event-type counts; shot_goals excludes own goals.')
    run.table(metric_rows(player_metrics, player_contexts), 'player_match_event_metrics', 'Derived event counts and shot xG per actual player/club/match; StatsBomb player IDs are source-specific and are not FPL IDs.')
    run.table([{**team_contexts[(mid, tid)], 'event_type_name': name, 'event_count': count} for (mid, tid, name), count in team_types.items()],
              'team_match_event_type_counts', 'Complete taxonomy counts for every event type per actual club/match, including non-player match events.')
    run.table([{**player_contexts[(mid, tid, pid)], 'event_type_name': name, 'event_count': count} for (mid, tid, pid, name), count in player_types.items()],
              'player_match_event_type_counts', 'Complete taxonomy counts for every event type assigned to a player.')
    run.table(coverage, 'match_coverage', 'Every eligible match download and source/cohort event count; all failed or missing sources visible.')
    run.table(season_audit, 'season_coverage', 'Exact available EPL source seasons and current-club coverage; 2003-04 is Arsenal-only match selection, not the whole league.')
    notes = {'repository': REPO, 'repository_commit': commit,
             'repository_commit_timestamp': json.loads(commit_bytes).get('commit', {}).get('committer', {}).get('date') if commit_bytes else None,
             'season_coverage': season_audit, 'event_rows_by_season': event_counts,
             'eligible_matches': len(infos), 'event_download_successes': sum(info['event_ok'] for info in infos),
             'lineup_download_successes': sum(info['lineup_ok'] for info in infos),
             'unresolved_source_team_events': sum(row['unresolved_source_team_events'] for row in coverage),
             'raw_originals_preserved': True, 'curated_filter': 'event or lineup actual team at match belongs to current_teams.csv; opponents retained',
             'license': 'StatsBomb Public Data User Agreement; official LICENSE.pdf retained; not MIT/CC. Research use, required published-analysis attribution/logo, restrictions on commercial use and third-party underlying-data redistribution.',
             'coordinate_system': 'StatsBomb event pitch coordinates, conventionally 120 by 80; native locations and provider documentation retained',
             'historical_availability': 'Retrospective source collection. Match outcomes and events are post-match observations; original publication timestamp is not established.'}
    run.finish(notes)
    print(json.dumps(notes, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workers', type=int, default=4)
    parser.add_argument('--refresh', action='store_true')
    args = parser.parse_args()
    collect(max(1, min(args.workers, 4)), args.refresh)
