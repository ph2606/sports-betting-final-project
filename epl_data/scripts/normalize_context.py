"""Give saved Transfermarkt roster and availability text explicit typed fields."""
from __future__ import annotations

import json
import re

import pandas as pd
from bs4 import BeautifulSoup

from common import AS_OF_DATE, ROOT, write_table


def main():
    folder = ROOT / 'data/processed/transfermarkt_current'
    squads = pd.read_parquet(folder / 'player_squads.parquet')
    raw_dob = squads['date_of_birth_age'].str.extract(r'(\d{2}/\d{2}/\d{4})')[0]
    squads['birth_date'] = pd.to_datetime(raw_dob, format='%d/%m/%Y', errors='coerce').dt.strftime('%Y-%m-%d')
    squads['age_at_snapshot'] = pd.to_numeric(squads['date_of_birth_age'].str.extract(r'\((\d+)\)')[0], errors='coerce').astype('Int64')
    squads['height_cm'] = pd.to_numeric(squads['height'].str.replace(',', '.', regex=False).str.extract(r'(\d+(?:\.\d+)?)')[0], errors='coerce') * 100
    squads['nationalities'] = squads['nat_image_labels'].map(lambda value: ', '.join(x for x in json.loads(value) if x) if pd.notna(value) else None)
    for source, target in [('contract', 'contract_end_date'), ('joined', 'club_join_date')]:
        squads[target] = pd.to_datetime(squads[source], format='%d/%m/%Y', errors='coerce').dt.strftime('%Y-%m-%d')
    squads['position'] = squads.apply(lambda row: str(row['player'])[len(str(row['player_name'])):].strip() if str(row['player']).startswith(str(row['player_name'])) else None, axis=1)
    write_table(squads, folder / 'player_squads.csv')
    clubs = pd.read_parquet(folder / 'club_market_values.parquet')
    original = pd.read_parquet(folder / 'injury_snapshot.parquet')
    lookup = original.groupby('team')['retrieved_at_utc'].first().to_dict()
    rows = []
    for club in clubs.to_dict('records'):
        path = ROOT / 'data/raw/transfermarkt_current/injuries' / f"{club['transfermarkt_club_id']}.html"
        if not path.exists():
            continue
        soup = BeautifulSoup(path.read_text(encoding='utf-8'), 'html.parser')
        for index, table in enumerate(soup.select('table.items')):
            headers = [th.get_text(' ', strip=True) for th in table.select('thead th')]
            category = 'provider_availability_table'
            for tr in table.select(':scope > tbody > tr'):
                cells = tr.find_all('td', recursive=False)
                if len(cells) == 1:
                    category = cells[0].get_text(' ', strip=True)
                    continue
                link = tr.find('a', href=re.compile(r'/profil/spieler/'))
                if not link:
                    continue
                record = {'team': club['team'], 'transfermarkt_player_id': int(re.search(r'/spieler/(\d+)', link['href'])[1]),
                          'player_name': link.get_text(' ', strip=True), 'provider_table_index': index,
                          'availability_category': category, 'retrieved_at_utc': lookup.get(club['team']), 'data_role': 'current_snapshot'}
                values = [td.get_text(' ', strip=True) for td in cells]
                record['provider_cells'] = json.dumps(values, ensure_ascii=False)
                for header, value in zip(headers, values):
                    key = 'reported_' + re.sub('[^a-z0-9]+', '_', header.casefold()).strip('_')
                    record[key] = value
                rows.append(record)
    data = pd.DataFrame(rows)
    for column in ['reported_since', 'reported_expected_return']:
        if column in data:
            data[column + '_date'] = pd.to_datetime(data[column], format='%d/%m/%Y', errors='coerce').dt.strftime('%Y-%m-%d')
    if 'reported_expected_return_date' in data:
        data['expected_return_precedes_snapshot_date'] = data['reported_expected_return_date'].lt(AS_OF_DATE).where(data['reported_expected_return_date'].notna())
    write_table(data.drop_duplicates(), folder / 'injury_snapshot.csv')
    print('normalized roster', len(squads), 'availability records', len(data), flush=True)


if __name__ == '__main__':
    main()
