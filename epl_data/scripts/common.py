"""Shared public-source acquisition helpers. No credentials or paid requests."""
from __future__ import annotations

import hashlib
import json
import threading
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
AS_OF_DATE = '2026-10-06'
SEASON = '2026-27'
MEMBERSHIP_URL = 'https://www.premierleague.com/en/news/4673099/the-202627-premier-league-season-officially-starts'
ALIASES = {
    'Arsenal': ['Arsenal', 'Arsenal FC'],
    'Aston Villa': ['Aston Villa', 'Aston Villa FC'],
    'Bournemouth': ['Bournemouth', 'AFC Bournemouth', 'Bournemouth AFC'],
    'Brentford': ['Brentford', 'Brentford FC'],
    'Brighton & Hove Albion': ['Brighton', 'Brighton & Hove Albion', 'Brighton and Hove Albion', 'Brighton Hove Albion'],
    'Chelsea': ['Chelsea', 'Chelsea FC'],
    'Coventry City': ['Coventry', 'Coventry City'],
    'Crystal Palace': ['Crystal Palace'],
    'Everton': ['Everton', 'Everton FC'],
    'Fulham': ['Fulham', 'Fulham FC'],
    'Hull City': ['Hull', 'Hull City'],
    'Ipswich Town': ['Ipswich', 'Ipswich Town'],
    'Leeds United': ['Leeds', 'Leeds United'],
    'Liverpool': ['Liverpool', 'Liverpool FC'],
    'Manchester City': ['Man City', 'Manchester City'],
    'Manchester United': ['Man United', 'Man Utd', 'Manchester United'],
    'Newcastle United': ['Newcastle', 'Newcastle United'],
    'Nottingham Forest': ["Nott'm Forest", "Nott'ham Forest", 'Nottingham Forest', 'Nottm Forest'],
    'Tottenham Hotspur': ['Spurs', 'Tottenham', 'Tottenham Hotspur'],
    'Sunderland': ['Sunderland', 'Sunderland AFC'],
}
LOOKUP = {a.casefold(): canonical for canonical, aliases in ALIASES.items() for a in aliases}


def canonical_team(value):
    if value is None or pd.isna(value):
        return None
    return LOOKUP.get(str(value).strip().casefold())


def now_utc():
    return datetime.now(timezone.utc).isoformat()


def write_table(frame, path):
    """Write a human-readable CSV and a typed Parquet copy."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path.with_suffix('.csv'), index=False)
    try:
        frame.to_parquet(path.with_suffix('.parquet'), index=False)
        if path.with_suffix('.parquet_error.txt').exists():
            path.with_suffix('.parquet_error.txt').unlink()
    except Exception as error:
        # CSV is authoritative for mixed provider fields; record any type issue.
        if path.with_suffix('.parquet').exists():
            path.with_suffix('.parquet').unlink()
        path.with_suffix('.parquet_error.txt').write_text(str(error), encoding='utf-8')


class Collector:
    """Save original response bytes, provenance and failed attempts per source."""
    def __init__(self, source):
        self.source = source
        self.raw = ROOT / 'data' / 'raw' / source
        self.out = ROOT / 'data' / 'processed' / source
        self.raw.mkdir(parents=True, exist_ok=True)
        self.out.mkdir(parents=True, exist_ok=True)
        self.records = []
        self.lock = threading.Lock()

    def fetch(self, url, relative_path, *, params=None, timeout=35, headers=None):
        path = self.raw / relative_path
        record = {'source': self.source, 'url': url, 'parameters': params,
                  'retrieved_at_utc': now_utc(), 'requested_as_of_date': AS_OF_DATE,
                  'source_published_at_utc': None, 'path': str(path.relative_to(ROOT)).replace('\\', '/')}
        try:
            response = requests.get(url, params=params, timeout=timeout,
                                    headers={'User-Agent': 'NYU-Academic-EPL-Research/1.0', **(headers or {})})
            record.update(http_status=response.status_code, final_url=response.url,
                          content_type=response.headers.get('content-type'), bytes=len(response.content))
            response.raise_for_status()
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(response.content)
            record.update(status='downloaded', sha256=hashlib.sha256(response.content).hexdigest())
            result = response
        except Exception as error:
            record.update(status='failed', error=str(error))
            result = None
        with self.lock:
            self.records.append(record)
        return result

    def finish(self, notes=None):
        folder = ROOT / 'metadata'
        folder.mkdir(parents=True, exist_ok=True)
        (folder / f'{self.source}_manifest.json').write_text(
            json.dumps({'source': self.source, 'requested_as_of_date': AS_OF_DATE,
                        'created_at_utc': now_utc(), 'notes': notes, 'requests': self.records},
                       indent=2, ensure_ascii=False), encoding='utf-8')


def current_teams():
    return pd.read_csv(ROOT / 'metadata' / 'current_teams.csv')
