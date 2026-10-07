"""Collect current club/squad context and available ClubElo page histories."""
from __future__ import annotations

import argparse
import json
import re
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urljoin

import pandas as pd
from bs4 import BeautifulSoup

from common import AS_OF_DATE, ROOT, Collector, canonical_team, current_teams, now_utc, write_table

CLUBELO_NAMES = {
    'Arsenal': 'Arsenal', 'Aston Villa': 'AstonVilla', 'Bournemouth': 'Bournemouth',
    'Brentford': 'Brentford', 'Brighton & Hove Albion': 'Brighton', 'Chelsea': 'Chelsea',
    'Coventry City': 'Coventry', 'Crystal Palace': 'CrystalPalace', 'Everton': 'Everton',
    'Fulham': 'Fulham', 'Hull City': 'Hull', 'Ipswich Town': 'Ipswich', 'Leeds United': 'Leeds',
    'Liverpool': 'Liverpool', 'Manchester City': 'ManCity', 'Manchester United': 'ManUnited',
    'Newcastle United': 'Newcastle', 'Nottingham Forest': 'Forest',
    'Tottenham Hotspur': 'Tottenham', 'Sunderland': 'Sunderland',
}


def money(text):
    text = text.replace('\xa0', '').replace(',', '').strip()
    match = re.search(r'([0-9.]+)\s*(bn|m|k)?', text)
    if not match:
        return None
    return float(match[1]) * {'bn': 1e9, 'm': 1e6, 'k': 1e3, None: 1}[match[2]]


def cell_text(cell):
    return cell.get_text(' ', strip=True)


def sportsdb():
    c = Collector('sportsdb')
    response = c.fetch('https://www.thesportsdb.com/api/v1/json/123/search_all_teams.php',
                       'teams.json', params={'l': 'English Premier League'})
    if response is not None:
        rows = response.json().get('teams') or []
        # Free league search can stop at ten clubs; fetch the remaining clubs by name.
        found = {canonical_team(row.get('strTeam')) for row in rows}
        for team in current_teams()['team']:
            if team in found:
                continue
            result = c.fetch('https://www.thesportsdb.com/api/v1/json/123/searchteams.php',
                             f'club_{team.replace(" ", "_")}.json', params={'t': team})
            if result is not None:
                rows.extend(result.json().get('teams') or [])
        data = pd.DataFrame(rows)
        data['team'] = data['strTeam'].map(canonical_team)
        data = data.loc[data['team'].notna()].drop_duplicates('team').copy()
        data['retrieved_at_utc'] = now_utc()
        data['data_role'] = 'current_snapshot'
        write_table(data, c.out / 'club_profiles.csv')
        print('sportsdb', len(data), 'clubs', flush=True)
    c.finish('Current club profiles: formation year, stadium, location/capacity, website, description, provider IDs. Current fields are not historical snapshots.')


def clubelo():
    c = Collector('clubelo')
    timeline, games, snapshots = [], [], []

    def one(pair):
        team, slug = pair
        response = c.fetch(f'https://clubelo.com/{slug}', f'{slug}.html')
        if response is None:
            return
        soup = BeautifulSoup(response.text, 'html.parser')
        retrieved = now_utc()
        for script in soup.find_all('script'):
            content = script.string or script.get_text()
            if 'var vegaJson' not in content:
                continue
            offset = content.index('{', content.index('var vegaJson'))
            chart, _ = json.JSONDecoder().raw_decode(content[offset:])
            for dataset in chart.get('datasets', {}).values():
                for row in dataset:
                    if 'Elo' in row and 'Date' in row:
                        if str(row['Date'])[:10] <= AS_OF_DATE:
                            timeline.append({**row, 'team': team, 'source_team_slug': slug,
                                             'retrieved_at_utc': retrieved,
                                             'data_role': 'retrospective_rating_timeline'})
        for table in soup.find_all('table'):
            headers = table.find('tr')
            if headers and 'New Elo' in headers.get_text(' ', strip=True):
                for tr in table.find_all('tr')[1:]:
                    cells = tr.find_all('td', recursive=False)
                    if len(cells) != 14:
                        continue
                    date_link = cells[0].find('a')
                    if date_link is None:
                        continue
                    date = date_link.get('href', '').strip('/')
                    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', date) or date > AS_OF_DATE:
                        continue
                    opponent_links = cells[2].find_all('a')
                    opponent_slug = opponent_links[-1].get('href', '').strip('/') if opponent_links else None
                    keys = ['date', 'venue', 'opponent_display', 'prior_rating_difference_display',
                            'home_field_advantage_display', 'elo_probability_display', 'full_time_score',
                            'extra_time_score', 'penalty_score', 'game_rating_difference_display',
                            'post_game_rating_difference_display', 'elo_change_display', 'new_elo', 'new_rank']
                    row = dict(zip(keys, [cell_text(td) for td in cells]))
                    row.update(date=date, team=team, opponent_slug=opponent_slug,
                               retrieved_at_utc=retrieved, data_role='retrospective_rating_match_history')
                    games.append(row)
            # Every club page contains the current England ranking table.
            if table is soup.find_all('table')[0]:
                continue
            for tr in table.find_all('tr'):
                cells = tr.find_all('td', recursive=False)
                if len(cells) < 2:
                    continue
                link = cells[0].find('a', href=f'/{slug}')
                if link and re.fullmatch(r'\d{3,4}(?:\.\d+)?', cell_text(cells[-1])):
                    snapshots.append({'team': team, 'elo': float(cell_text(cells[-1])),
                                      'retrieved_at_utc': retrieved, 'data_role': 'current_snapshot'})
                    break
        print('clubelo', team, 'saved', flush=True)

    with ThreadPoolExecutor(max_workers=3) as pool:
        list(pool.map(one, CLUBELO_NAMES.items()))
    for name, rows in [('rating_history', timeline), ('rated_match_history', games), ('ratings_snapshot', snapshots)]:
        if rows:
            frame = pd.DataFrame(rows)
            subset = ['team', 'Date'] if name == 'rating_history' else ['team', 'date'] if name == 'rated_match_history' else ['team']
            frame = frame.drop_duplicates(subset=subset)
            write_table(frame, c.out / f'{name}.csv')
            print('clubelo', name, len(frame), flush=True)
    c.finish('CSV API did not respond in the initial probe; public club pages expose chart JSON and rated match tables. Chart typically shows four years; match table may cover longer history and other competitions. Dates have no guaranteed historical publication time. A current retrospective rating is not verified as the originally published pre-match rating; leave out of causal backtests until validated. Display strings retain provider uncertainty/rounded versions.')


def transfermarkt():
    c = Collector('transfermarkt_current')
    url = 'https://www.transfermarkt.com/premier-league/startseite/wettbewerb/GB1/saison_id/2026'
    response = c.fetch(url, 'league.html')
    if response is None:
        c.finish()
        return
    soup = BeautifulSoup(response.text, 'html.parser')
    club_rows = []
    for tr in soup.select('table.items > tbody > tr'):
        cells = tr.find_all('td', recursive=False)
        if len(cells) != 7:
            continue
        link = cells[1].find('a', href=re.compile('/verein/'))
        if link is None:
            continue
        team = canonical_team(link.get('title') or link.get_text())
        if team is None:
            # Sunderland's branding differs between sources.
            team = 'Sunderland' if 'Sunderland' in link.get_text() else None
        if team is None:
            continue
        href = link['href']
        club_id = int(re.search(r'/verein/(\d+)', href)[1])
        squad_link = cells[2].find('a')
        club_rows.append({'team': team, 'transfermarkt_club_id': club_id,
                          'source_club_name': link.get_text(' ', strip=True),
                          'squad_size': int(cell_text(cells[2])), 'average_age': float(cell_text(cells[3])),
                          'foreign_players': int(cell_text(cells[4])),
                          'average_market_value_eur': money(cell_text(cells[5])),
                          'total_market_value_eur': money(cell_text(cells[6])),
                          'squad_url': urljoin(url, squad_link['href']),
                          'season': '2026-27', 'retrieved_at_utc': now_utc(), 'data_role': 'current_snapshot'})
    clubs = pd.DataFrame(club_rows)
    write_table(clubs, c.out / 'club_market_values.csv')
    player_rows, injury_rows, transfer_rows = [], [], []

    def one(club):
        team, club_id = club['team'], club['transfermarkt_club_id']
        # Detailed roster has position, citizenship, height/foot/contract and value.
        detailed_url = club['squad_url'].rstrip('/') + '/plus/1'
        response = c.fetch(detailed_url, f'squads/{club_id}.html')
        if response is not None:
            soup = BeautifulSoup(response.text, 'html.parser')
            table = soup.select_one('table.items')
            if table:
                headers = [cell_text(th) for th in table.select('thead th')]
                for tr in table.select(':scope > tbody > tr'):
                    link = tr.find('a', href=re.compile('/profil/spieler/'))
                    if not link:
                        continue
                    cells = tr.find_all('td', recursive=False)
                    record = {'team': team, 'transfermarkt_club_id': club_id,
                              'transfermarkt_player_id': int(re.search(r'/spieler/(\d+)', link['href'])[1]),
                              'player_name': link.get_text(' ', strip=True),
                              'player_url': urljoin(detailed_url, link['href']),
                              'season': '2026-27', 'retrieved_at_utc': now_utc(), 'data_role': 'current_snapshot'}
                    for i, td in enumerate(cells):
                        header = headers[i] if i < len(headers) else f'column_{i}'
                        key = re.sub('[^a-z0-9]+', '_', header.casefold()).strip('_') or f'column_{i}'
                        if key in record:
                            key = f'provider_{key}'
                        record[key] = cell_text(td)
                        titles = [img.get('title') or img.get('alt') for img in td.find_all('img')]
                        if titles:
                            record[key + '_image_labels'] = json.dumps(titles, ensure_ascii=False)
                    value_cell = tr.select_one('td.rechts.hauptlink')
                    if value_cell:
                        record['market_value_eur'] = money(cell_text(value_cell))
                    player_rows.append(record)
        # Injury records are today's state, without historical publication timing.
        response = c.fetch(f'https://www.transfermarkt.com/club/sperrenundverletzungen/verein/{club_id}',
                           f'injuries/{club_id}.html')
        if response is not None:
            soup = BeautifulSoup(response.text, 'html.parser')
            for tr in soup.select('table.items > tbody > tr'):
                link = tr.find('a', href=re.compile('/profil/spieler/'))
                if link:
                    injury_rows.append({'team': team, 'transfermarkt_player_id': int(re.search(r'/spieler/(\d+)', link['href'])[1]),
                                        'player_name': link.get_text(' ', strip=True),
                                        'provider_cells': json.dumps([cell_text(td) for td in tr.find_all('td', recursive=False)], ensure_ascii=False),
                                        'retrieved_at_utc': now_utc(), 'data_role': 'current_snapshot'})
        response = c.fetch(f'https://www.transfermarkt.com/club/transfers/verein/{club_id}/saison_id/2026',
                           f'transfers/{club_id}.html')
        if response is not None:
            soup = BeautifulSoup(response.text, 'html.parser')
            for table_index, table in enumerate(soup.select('table.items')):
                for tr in table.select(':scope > tbody > tr'):
                    link = tr.find('a', href=re.compile('/profil/spieler/'))
                    if link:
                        transfer_rows.append({'team': team, 'transfermarkt_player_id': int(re.search(r'/spieler/(\d+)', link['href'])[1]),
                                              'player_name': link.get_text(' ', strip=True), 'provider_table_index': table_index,
                                              'provider_cells': json.dumps([cell_text(td) for td in tr.find_all('td', recursive=False)], ensure_ascii=False),
                                              'season': '2026-27', 'retrieved_at_utc': now_utc(), 'data_role': 'current_snapshot'})
        print('transfermarkt current', team, 'saved', flush=True)

    with ThreadPoolExecutor(max_workers=3) as pool:
        list(pool.map(one, club_rows))
    for name, rows in [('player_squads', player_rows), ('injury_snapshot', injury_rows), ('season_transfers', transfer_rows)]:
        frame = pd.DataFrame(rows)
        if rows:
            frame = frame.drop_duplicates()
            write_table(frame, c.out / f'{name}.csv')
            print('transfermarkt current', name, len(frame), flush=True)
    c.finish('Transfermarkt 2026-27 squad and club valuation pages, injury pages and transfer pages; valuation estimates are not transaction prices. Tables retain native text/image nationality labels. Current roster, contract, age/value and injury snapshots must never be assigned to historical decision dates.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--sources', nargs='+', choices=['sportsdb', 'clubelo', 'transfermarkt'],
                        default=['sportsdb', 'clubelo', 'transfermarkt'])
    args = parser.parse_args()
    for source in args.sources:
        globals()[source]()
