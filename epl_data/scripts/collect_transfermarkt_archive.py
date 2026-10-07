"""Collect the public July 2026 Transfermarkt archive for the current-club cohort."""
from __future__ import annotations

import argparse
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor

import pandas as pd

from common import AS_OF_DATE, ROOT, Collector, now_utc, write_table

BASE = 'https://pub-e682421888d945d684bcae8890b0ec20.r2.dev/data/'
CLUBS = {11: 'Arsenal', 405: 'Aston Villa', 989: 'Bournemouth', 1148: 'Brentford',
         1237: 'Brighton & Hove Albion', 631: 'Chelsea', 990: 'Coventry City',
         873: 'Crystal Palace', 29: 'Everton', 931: 'Fulham', 3008: 'Hull City',
         677: 'Ipswich Town', 399: 'Leeds United', 31: 'Liverpool',
         281: 'Manchester City', 985: 'Manchester United', 762: 'Newcastle United',
         703: 'Nottingham Forest', 148: 'Tottenham Hotspur', 289: 'Sunderland'}
NOTES = ('Provider archive stopped in July 2026; current fields do not describe October 2026 squads. '
         'Original gzip tables retained. Games require at least one current-cohort club; appearances/lineups/events '
         'require the actual historical club in the cohort. Profiles and valuation histories refer to players '
         'associated with these clubs and may describe a later different club. Coventry is absent from archived '
         'clubs and Hull/Ipswich metadata can be old. Future agreed transfers are labeled, not completed. '
         'Current roster/value/injury snapshots are under transfermarkt_current. Publisher declares CC0; license retained.')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--reuse-raw', action='store_true')
    args = parser.parse_args()
    c = Collector('transfermarkt_archive')
    previous_path = ROOT / 'metadata/transfermarkt_archive_manifest.json'
    previous = {}
    if previous_path.exists():
        previous = {r['path']: r for r in json.loads(previous_path.read_text(encoding='utf-8')).get('requests', [])}

    def get(url, relative):
        path = c.raw / relative
        key = path.relative_to(ROOT).as_posix()
        if args.reuse_raw and path.exists() and key in previous:
            with c.lock:
                c.records.append({**previous[key], 'status': 'reused_cached',
                                  'cache_checked_at_utc': now_utc(), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
            return
        c.fetch(url, relative, timeout=90)

    get('https://raw.githubusercontent.com/dcaribou/transfermarkt-datasets/master/README.md', 'README_source.md')
    get('https://raw.githubusercontent.com/dcaribou/transfermarkt-datasets/master/LICENSE', 'LICENSE_source.txt')
    names = ['clubs', 'players', 'games', 'appearances', 'player_valuations', 'club_games',
             'game_events', 'game_lineups', 'transfers', 'competitions']
    with ThreadPoolExecutor(max_workers=3) as pool:
        list(pool.map(lambda name: get(BASE + name + '.csv.gz', name + '.csv.gz'), names))
    collected_players, summaries = set(), []
    for name in ['clubs', 'games', 'appearances', 'club_games', 'game_events', 'game_lineups', 'transfers', 'player_valuations']:
        path = c.raw / (name + '.csv.gz')
        if not path.exists():
            continue
        frames = []
        for chunk in pd.read_csv(path, chunksize=150000, low_memory=False):
            focal = None
            if name == 'games':
                mask = chunk['home_club_id'].isin(CLUBS) | chunk['away_club_id'].isin(CLUBS)
            elif name == 'transfers':
                mask = chunk['from_club_id'].isin(CLUBS) | chunk['to_club_id'].isin(CLUBS)
            elif name == 'appearances':
                mask, focal = chunk['player_club_id'].isin(CLUBS), 'player_club_id'
            elif name == 'player_valuations':
                mask = chunk['player_id'].isin(collected_players)
            else:
                mask, focal = chunk['club_id'].isin(CLUBS), 'club_id'
            frame = chunk.loc[mask].copy()
            if name == 'game_lineups' and 'number' in frame:
                # Shirt numbers can include a dash/unknown marker in the provider.
                frame['number'] = frame['number'].astype('string')
            date_column = 'transfer_date' if name == 'transfers' else 'date'
            if date_column in frame:
                frame['date_is_after_requested_as_of'] = pd.to_datetime(frame[date_column], errors='coerce').dt.strftime('%Y-%m-%d').gt(AS_OF_DATE)
                if name == 'transfers':
                    frame['transfer_is_future_scheduled'] = frame['date_is_after_requested_as_of']
                else:
                    frame = frame.loc[~frame['date_is_after_requested_as_of']].copy()
            if focal:
                frame['team'] = frame[focal].map(CLUBS)
            if name == 'games':
                frame['home_team_cohort'], frame['away_team_cohort'] = frame['home_club_id'].map(CLUBS), frame['away_club_id'].map(CLUBS)
            if name == 'transfers':
                frame['from_team_cohort'], frame['to_team_cohort'] = frame['from_club_id'].map(CLUBS), frame['to_club_id'].map(CLUBS)
            if 'player_id' in frame and name != 'player_valuations':
                collected_players.update(frame['player_id'].dropna().astype(int).unique())
            frame['archive_snapshot_cutoff'] = '2026-07-06'
            frame['retrieved_at_utc'] = now_utc()
            frame['data_role'] = 'historical_related_player_valuations' if name == 'player_valuations' else 'historical_cohort_records'
            if not frame.empty:
                frames.append(frame)
        if frames:
            data = pd.concat(frames, ignore_index=True)
            write_table(data, c.out / f'{name}.csv')
            summaries.append({'table': name, 'rows': len(data), 'columns': len(data.columns)})
            print('archive curated', name, len(data), flush=True)
    path = c.raw / 'players.csv.gz'
    if path.exists():
        data = pd.read_csv(path, low_memory=False)
        data = data.loc[data['player_id'].isin(collected_players) | data['current_club_id'].isin(CLUBS)].copy()
        data['archive_club_cohort'] = data['current_club_id'].map(CLUBS)
        data['archive_snapshot_cutoff'] = '2026-07-06'
        data['data_role'] = 'archive_player_profiles_associated_with_cohort'
        data['retrieved_at_utc'] = now_utc()
        write_table(data, c.out / 'player_profiles.csv')
        summaries.append({'table': 'player_profiles', 'rows': len(data), 'columns': len(data.columns)})
    path = c.raw / 'competitions.csv.gz'
    if path.exists():
        write_table(pd.read_csv(path), c.out / 'competition_dictionary.csv')
    (ROOT / 'metadata/transfermarkt_archive_summary.json').write_text(json.dumps(summaries, indent=2), encoding='utf-8')
    c.finish(NOTES)


if __name__ == '__main__':
    main()
