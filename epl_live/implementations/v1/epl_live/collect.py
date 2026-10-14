"""Collect a new, timestamped, immutable public-source 2026-27 EPL snapshot.

Run once: python -m epl_live.collect --players
Without --players the CLI archives only the five public core endpoints. The API
defaults to player summaries because callers must explicitly request a snapshot.
No existing acquisition/study files or earlier snapshots are updated or reused.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import re
import threading
import time
import uuid

import numpy as np
import pandas as pd
import requests

SEASON = "2026-27"
SEASON_START = pd.Timestamp("2026-07-01", tz="UTC")
SEASON_END = pd.Timestamp("2027-07-01", tz="UTC")
ROOT = Path(__file__).resolve().parents[1]
FPL_API = "https://fantasy.premierleague.com/api"
BOOKMAKERS = {
    "1XB": "1XBet", "B365": "Bet365", "BF": "Betfair Sportsbook", "BFD": "Betfred",
    "BMGM": "BetMGM", "BV": "BetVictor", "BS": "Blue Square", "BW": "Bet & Win",
    "CL": "Coral", "GB": "Gamebookers", "IW": "Interwetten", "LB": "Ladbrokes",
    "PP": "Paddy Power", "PS": "Pinnacle", "P": "Pinnacle", "SK": "Skybet", "SKB": "Skybet",
    "SO": "Sporting Odds", "SB": "Sportingbet", "SJ": "Stan James", "SY": "Stanleybet",
    "VC": "VC Bet", "WH": "William Hill",
}
EXTRA_ALIASES = {
    "Coventry": "Coventry City", "Hull": "Hull City", "Ipswich": "Ipswich Town",
    "Brighton": "Brighton & Hove Albion", "Brighton and Hove Albion": "Brighton & Hove Albion",
    "AFC Bournemouth": "Bournemouth", "Man City": "Manchester City", "Man United": "Manchester United",
    "Man Utd": "Manchester United", "Newcastle": "Newcastle United", "Leeds": "Leeds United",
    "Nott'm Forest": "Nottingham Forest", "Nott'ham Forest": "Nottingham Forest", "Spurs": "Tottenham Hotspur",
    "Tottenham": "Tottenham Hotspur", "Sunderland AFC": "Sunderland",
}
FIXTURE_COLUMNS = ["match_id", "fpl_fixture_id", "season", "home_team", "away_team", "kickoff_utc",
                   "match_date", "finished", "started", "home_goals", "away_goals", "target_eligible",
                   "observed_at_utc", "eligibility_checked_at_utc"]
ODDS_COLUMNS = ["match_id", "fpl_fixture_id", "season", "match_date", "home_team", "away_team",
                "bookmaker", "source_prefix", "odds_H", "odds_D", "odds_A", "snapshot_type",
                "observed_at_utc", "quote_publication_time_unknown", "provider_quote_timestamp_utc",
                "simultaneous_execution_verified", "source_url"]
HISTORY_COLUMNS = ["element", "fixture", "kickoff_time", "canonical_team", "opponent_name", "was_home",
                   "season", "position_type", "observed_at_utc", "history_identity_valid"]
UNDERSTAT_COLUMNS = ["understat_id", "season", "match_date", "home_team", "away_team", "home_xg",
                     "away_xg", "completed", "native_datetime", "observed_at_utc"]


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(moment: datetime) -> str:
    return moment.astimezone(timezone.utc).isoformat(timespec="microseconds")


def _write_json_new(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False)


def _expected_membership():
    path = ROOT / "epl_data/metadata/current_teams.csv"
    frame = pd.read_csv(path)
    if len(frame) != 20 or frame.team.nunique() != 20 or set(frame.season) != {SEASON}:
        raise ValueError("Saved current membership must identify exactly 20 unique 2026-27 clubs")
    aliases = {str(value).strip().casefold(): row.team
               for row in frame.itertuples(index=False)
               for value in (row.team, row.fpl_name)}
    aliases.update({name.casefold(): canonical for name, canonical in EXTRA_ALIASES.items()})
    return frame, aliases, {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def _canonical(value, aliases):
    return aliases.get(str(value).strip().casefold()) if value is not None and not pd.isna(value) else None


def _bool(value):
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    if value in (1, "1", "true", "True"):
        return True
    if value in (0, "0", "false", "False"):
        return False
    return None


def _number(value):
    value = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    return float(value) if pd.notna(value) and np.isfinite(value) else None


def _season_dates(values, label, errors, *, dayfirst=False, require_any=True):
    dates = pd.to_datetime(pd.Series(values, dtype="object"), utc=True, errors="coerce", format="mixed", dayfirst=dayfirst)
    provided = pd.Series(values, dtype="object").notna()
    if (provided & dates.isna()).any():
        errors.append(f"{label}: unparseable provided calendar date")
    if require_any and not dates.notna().any():
        errors.append(f"{label}: no verifiable dated records")
    if (dates.notna() & ((dates < SEASON_START) | (dates >= SEASON_END))).any():
        errors.append(f"{label}: dates conflict with the requested 2026-27 season")
    return dates


def _parse_csv(content):
    for encoding in ("utf-8-sig", "cp1252", "latin1"):
        try:
            text = content.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    rows = list(csv.reader(io.StringIO(text)))
    if not rows:
        raise ValueError("Empty source CSV")
    header = [value.strip() for value in rows[0]]
    while header and not header[-1]:
        header.pop()
    header = [name or f"source_unnamed_{index}" for index, name in enumerate(header)]
    if len(header) != len(set(header)):
        raise ValueError("Source CSV has ambiguous duplicate columns")
    records = []
    for row in rows[1:]:
        while len(row) > len(header) and not row[-1].strip():
            row.pop()
        if len(row) > len(header):
            raise ValueError("Nonempty source CSV values exceed the declared header")
        if any(value.strip() for value in row):
            records.append(dict(zip(header, row)))
    return pd.DataFrame(records).replace("", pd.NA)


class _Archive:
    def __init__(self, path):
        self.path = path
        self.requests = []
        self.lock = threading.Lock()

    def fetch(self, key, url, relative, headers=None):
        started, monotonic_start = _now(), time.perf_counter()
        record = {"source_key": key, "url": url, "request_started_at_utc": _iso(started),
                  "request_completed_at_utc": None, "response_observed_at_utc": None,
                  "http_status": None, "http_response_date": None, "content_type": None,
                  "path": relative, "sha256": None, "bytes": 0, "status": "failed", "error": None,
                  "provider_quote_timestamp_utc": None, "quote_publication_time_unknown": True}
        content = None
        try:
            response = requests.get(url, timeout=(10, 40), headers={
                "User-Agent": "NYU-EPL-Private-Academic-Research/1.0", **(headers or {})})
            content = response.content
            completed = _now()
            record.update(request_completed_at_utc=_iso(completed), response_observed_at_utc=_iso(completed),
                          http_status=int(response.status_code), final_url=response.url,
                          http_response_date=response.headers.get("Date"), content_type=response.headers.get("Content-Type"),
                          bytes=len(content), sha256=hashlib.sha256(content).hexdigest())
            target = self.path / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("xb") as handle:
                handle.write(content)
            if 200 <= response.status_code < 300:
                record["status"] = "downloaded"
            else:
                record.update(status="http_error", error=f"HTTP {response.status_code}")
        except Exception as error:
            record["request_completed_at_utc"] = _iso(_now())
            record["error"] = re.sub(r"://[^/\s@]+@", "://[redacted]@", f"{type(error).__name__}: {error}")
        record["elapsed_seconds_monotonic"] = round(time.perf_counter() - monotonic_start, 6)
        with self.lock:
            self.requests.append(record)
            with (self.path / "request_log.jsonl").open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(record, ensure_ascii=False, allow_nan=False) + "\n")
        return content if record["status"] == "downloaded" else None, record


def _write_table_new(snapshot, name, frame, columns=()):
    frame = frame.copy()
    for column in columns:
        if column not in frame:
            frame[column] = pd.Series(index=frame.index, dtype="object")
    if columns:
        frame = frame[list(columns) + [column for column in frame if column not in columns]]
    for column in frame.select_dtypes(include="object"):
        frame[column] = frame[column].map(lambda value: json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else value)
    folder = snapshot / "normalized"
    folder.mkdir(exist_ok=True)
    with (folder / f"{name}.csv").open("x", encoding="utf-8", newline="") as handle:
        frame.to_csv(handle, index=False)
    with (folder / f"{name}.parquet").open("xb") as handle:
        frame.to_parquet(handle, index=False)
    return {"rows": len(frame), "columns": list(frame.columns), "csv": f"normalized/{name}.csv", "parquet": f"normalized/{name}.parquet"}


def _validate_fpl(bootstrap, fixtures, expected, aliases, errors):
    before = len(errors)
    if not isinstance(bootstrap, dict) or not isinstance(bootstrap.get("teams"), list):
        errors.append("FPL bootstrap schema missing teams")
        return {}, False, False
    native_teams = bootstrap["teams"]
    canonical = [_canonical(row.get("name"), aliases) for row in native_teams]
    membership_valid = len(native_teams) == 20 and len(set(canonical)) == 20 and set(canonical) == set(expected.team)
    if not membership_valid:
        errors.append("FPL league membership differs from the exact saved 20 current clubs")
    ids = [row.get("id") for row in native_teams]
    if any(value is None for value in ids) or len(set(ids)) != len(ids):
        membership_valid = False
        errors.append("FPL team IDs are absent or duplicated")
    codes = dict(zip(expected.team, expected.fpl_team_code))
    if any(name is None or row.get("code") != codes.get(name) for row, name in zip(native_teams, canonical)):
        membership_valid = False
        errors.append("FPL stable club codes conflict with the saved membership")
    names = dict(zip(ids, canonical))
    if not isinstance(fixtures, list) or not fixtures:
        errors.append("FPL fixtures schema must be a nonempty list")
        return names, membership_valid, False
    fixture_ids = [row.get("id") for row in fixtures]
    if None in fixture_ids or len(set(fixture_ids)) != len(fixture_ids):
        errors.append("FPL fixture IDs are missing or duplicated")
    if any(row.get("team_h") not in names or row.get("team_a") not in names or row.get("team_h") == row.get("team_a") for row in fixtures):
        errors.append("FPL fixture participants conflict with the validated league membership")
    _season_dates([row.get("kickoff_time") for row in fixtures], "FPL fixtures", errors)
    events = bootstrap.get("events")
    if not isinstance(events, list) or not events:
        errors.append("FPL season cannot be verified without event deadlines")
    else:
        deadlines = _season_dates([row.get("deadline_time") for row in events], "FPL event deadlines", errors)
        if deadlines.notna().any() and {int(deadlines.min().year), int(deadlines.max().year)} != {2026, 2027}:
            errors.append("FPL event calendar does not span the expected 2026 and 2027 season years")
    if "season" in bootstrap and str(bootstrap["season"]) not in {"2026", "2026-27", "2026/27", "2026-2027", "2026/2027"}:
        errors.append("FPL explicit season label conflicts with 2026-27")
    elements = bootstrap.get("elements")
    if not isinstance(elements, list) or not elements:
        errors.append("FPL bootstrap has no valid player list")
    else:
        player_ids = [row.get("id") for row in elements]
        if None in player_ids or len(set(player_ids)) != len(player_ids):
            errors.append("FPL player IDs are missing or duplicated")
        if any(row.get("team") not in names for row in elements):
            errors.append("FPL player team IDs conflict with current membership")
    return names, membership_valid, len(errors) == before


def _fixtures_table(fixtures, names, observed, cutoff):
    records = []
    for row in fixtures:
        kickoff = pd.to_datetime(row.get("kickoff_time"), utc=True, errors="coerce")
        finished, started = _bool(row.get("finished")), _bool(row.get("started"))
        provisional = _bool(row.get("finished_provisional"))
        eligible = (pd.notna(kickoff) and kickoff > cutoff and started is not True
                    and finished is not True and provisional is not True and (_number(row.get("minutes")) or 0) <= 0)
        records.append({"match_id": f"fpl_{SEASON}_{int(row['id'])}", "fpl_fixture_id": int(row["id"]),
                        "season": SEASON, "home_team": names.get(row["team_h"]), "away_team": names.get(row["team_a"]),
                        "kickoff_utc": kickoff.isoformat() if pd.notna(kickoff) else None,
                        "match_date": kickoff.strftime("%Y-%m-%d") if pd.notna(kickoff) else None,
                        "finished": finished, "started": started, "home_goals": _number(row.get("team_h_score")),
                        "away_goals": _number(row.get("team_a_score")), "target_eligible": bool(eligible),
                        "observed_at_utc": observed, "eligibility_checked_at_utc": cutoff.isoformat()})
    return pd.DataFrame(records, columns=FIXTURE_COLUMNS)


def _understat_table(payload, aliases, observed, errors):
    if not isinstance(payload, dict) or not isinstance(payload.get("dates"), list) or not isinstance(payload.get("teams"), dict):
        errors.append("Understat league schema missing dates/teams")
        return pd.DataFrame(columns=UNDERSTAT_COLUMNS)
    source_names = [_canonical(team.get("title"), aliases) for team in payload["teams"].values()]
    if None in source_names or len(set(source_names)) != 20:
        errors.append("Understat league membership conflicts with current 20 clubs")
    dates = _season_dates([row.get("datetime") for row in payload["dates"]], "Understat native calendar", errors)
    records = []
    for position, row in enumerate(payload["dates"]):
        home, away = _canonical(row.get("h", {}).get("title"), aliases), _canonical(row.get("a", {}).get("title"), aliases)
        if home is None or away is None:
            errors.append("Understat fixture has an unrecognized current-season club")
        records.append({"understat_id": str(row.get("id")), "season": SEASON,
                        "match_date": dates.iloc[position].strftime("%Y-%m-%d") if pd.notna(dates.iloc[position]) else None,
                        "home_team": home, "away_team": away, "home_xg": _number(row.get("xG", {}).get("h")),
                        "away_xg": _number(row.get("xG", {}).get("a")), "completed": _bool(row.get("isResult")) is True,
                        "native_datetime": row.get("datetime"), "observed_at_utc": observed})
    frame = pd.DataFrame(records, columns=UNDERSTAT_COLUMNS)
    if frame.understat_id.duplicated().any():
        errors.append("Understat match IDs are duplicated")
    return frame


def _individual_odds(source, fixtures, aliases, observed, url, errors):
    audit = {"native_e0_rows": 0, "unmatched_or_ineligible_fixture_rows": 0, "invalid_triplets": 0,
             "excluded_pinnacle_triplets": 0, "exact_linked_quotes": 0, "unmatched_examples": []}
    if source.empty:
        return pd.DataFrame(columns=ODDS_COLUMNS), audit
    if not {"Div", "Date", "HomeTeam", "AwayTeam"}.issubset(source):
        errors.append("Football-Data fixture CSV schema invalid")
        return pd.DataFrame(columns=ODDS_COLUMNS), audit
    rows = source.loc[source.Div.eq("E0")].copy()
    audit["native_e0_rows"] = len(rows)
    if rows.empty:
        return pd.DataFrame(columns=ODDS_COLUMNS), audit
    dates = _season_dates(rows.Date.tolist(), "Football-Data E0 upcoming fixtures", errors, dayfirst=True)
    valid = fixtures.loc[fixtures.target_eligible]
    keys = ["match_date", "home_team", "away_team"]
    if valid.duplicated(keys).any():
        errors.append("FPL upcoming fixture calendar keys are ambiguous")
        return pd.DataFrame(columns=ODDS_COLUMNS), audit
    lookup = {tuple(row[key] for key in keys): row for row in valid.to_dict("records")}
    records = []
    for position, row in enumerate(rows.to_dict("records")):
        date = dates.iloc[position].strftime("%Y-%m-%d") if pd.notna(dates.iloc[position]) else None
        home, away = _canonical(row.get("HomeTeam"), aliases), _canonical(row.get("AwayTeam"), aliases)
        target = lookup.get((date, home, away))
        if target is None:
            audit["unmatched_or_ineligible_fixture_rows"] += 1
            if len(audit["unmatched_examples"]) < 20:
                audit["unmatched_examples"].append({"match_date": date, "home_team": home, "away_team": away})
            continue
        for prefix, bookmaker in BOOKMAKERS.items():
            columns = [prefix + outcome for outcome in "HDA"]
            if not all(column in row for column in columns):
                continue
            values = [_number(row[column]) for column in columns]
            if all(value is None for value in values):
                continue
            if prefix in {"PS", "P"} and pd.Timestamp(date) >= pd.Timestamp("2025-07-23"):
                audit["excluded_pinnacle_triplets"] += 1
                continue
            if any(value is None or value <= 1 for value in values):
                audit["invalid_triplets"] += 1
                continue
            records.append({"match_id": target["match_id"], "fpl_fixture_id": target["fpl_fixture_id"],
                            "season": SEASON, "match_date": date, "home_team": home, "away_team": away,
                            "bookmaker": bookmaker, "source_prefix": prefix,
                            "odds_H": values[0], "odds_D": values[1], "odds_A": values[2],
                            "snapshot_type": "preclosing", "observed_at_utc": observed,
                            "quote_publication_time_unknown": True, "provider_quote_timestamp_utc": None,
                            "simultaneous_execution_verified": False, "source_url": url})
    result = pd.DataFrame(records, columns=ODDS_COLUMNS)
    if result.duplicated(["match_id", "source_prefix"]).any():
        errors.append("Football-Data repeated exact bookmaker/fixture quotes; none admitted")
        result = result.iloc[:0]
    audit["exact_linked_quotes"] = len(result)
    return result, audit


def _player_history(summaries, elements, fixtures, names, errors):
    lookup = {int(row["id"]): row for row in fixtures}
    players = {int(row["id"]): row for row in elements}
    records, invalid = [], 0
    for element, data, record in summaries:
        if data is None:
            continue
        if not isinstance(data, dict) or not isinstance(data.get("history"), list):
            invalid += 1
            errors.append(f"FPL player {element}: summary history schema invalid")
            continue
        for native in data["history"]:
            row = dict(native)
            fixture = lookup.get(row.get("fixture"))
            was_home = _bool(row.get("was_home"))
            native_date = str(row.get("kickoff_time", ""))[:10]
            fixture_date = str(fixture.get("kickoff_time", ""))[:10] if fixture else None
            valid = (fixture is not None and was_home is not None and native_date == fixture_date
                     and row.get("element", element) == element)
            if valid:
                own = fixture["team_h" if was_home else "team_a"]
                opponent = fixture["team_a" if was_home else "team_h"]
                valid = row.get("opponent_team", opponent) == opponent
            if not valid:
                invalid += 1
            row.update(element=element, season=SEASON, position_type=players[element].get("element_type"),
                       canonical_team=names.get(own) if valid else None,
                       opponent_name=names.get(opponent) if valid else None, was_home=was_home,
                       observed_at_utc=record["response_observed_at_utc"], history_identity_valid=bool(valid))
            records.append(row)
    frame = pd.DataFrame(records)
    if not frame.empty and frame.duplicated(["element", "fixture"]).any():
        errors.append("FPL element/fixture histories are duplicated")
        invalid += int(frame.duplicated(["element", "fixture"]).sum())
    return frame, invalid


def collect_snapshot(output_root: Path, include_players: bool = True) -> Path:
    """Archive one fresh capture; callers must gate on final manifest.usable.

    There is no cache reuse or overwrite. A failed/mismatched capture is retained
    for audit, marked unusable, and never relabeled as a different season.
    ``fpl_player_summaries_complete`` is a separate strict player-capability gate.
    """
    started = _now()
    snapshot_id = started.strftime("%Y%m%dT%H%M%S.%fZ") + "_" + uuid.uuid4().hex[:10]
    snapshot = Path(output_root).resolve() / snapshot_id
    snapshot.mkdir(parents=True, exist_ok=False)
    archive = _Archive(snapshot)
    _write_json_new(snapshot / "snapshot_header.json", {"snapshot_id": snapshot_id, "season": SEASON,
                    "snapshot_started_at_utc": _iso(started), "include_players": bool(include_players)})
    errors, bodies, request_records, summaries, tables = [], {}, {}, [], {}
    names, membership_valid, fpl_valid = {}, False, False
    player_requested = player_downloaded = invalid_history = 0
    fixtures = pd.DataFrame(columns=FIXTURE_COLUMNS)
    odds = pd.DataFrame(columns=ODDS_COLUMNS)
    understat = pd.DataFrame(columns=UNDERSTAT_COLUMNS)
    history = pd.DataFrame(columns=HISTORY_COLUMNS)
    freshness = {}
    odds_audit = {}
    expected_info = None
    bootstrap, native_fixtures = {}, []
    try:
        expected, aliases, expected_info = _expected_membership()
        jobs = {
            "fpl_bootstrap": (f"{FPL_API}/bootstrap-static/", "raw/fpl/bootstrap-static.json", None),
            "fpl_fixtures": (f"{FPL_API}/fixtures/", "raw/fpl/fixtures.json", None),
            "football_data_e0": ("https://www.football-data.co.uk/mmz4281/2627/E0.csv", "raw/football_data/E0.csv", None),
            "football_data_fixtures": ("https://www.football-data.co.uk/fixtures.csv", "raw/football_data/fixtures.csv", None),
            "understat_league": ("https://understat.com/getLeagueData/EPL/2026", "raw/understat/league_2026.json",
                                {"X-Requested-With": "XMLHttpRequest", "Referer": "https://understat.com/league/EPL/2026"}),
        }
        with ThreadPoolExecutor(max_workers=5) as pool:
            pending = {pool.submit(archive.fetch, key, *arguments): key for key, arguments in jobs.items()}
            for future in as_completed(pending):
                key = pending[future]
                bodies[key], request_records[key] = future.result()
        for key in jobs:
            if bodies[key] is None:
                errors.append(f"Required source failed: {key}")
        if bodies.get("fpl_bootstrap") is not None and bodies.get("fpl_fixtures") is not None:
            bootstrap, native_fixtures = json.loads(bodies["fpl_bootstrap"]), json.loads(bodies["fpl_fixtures"])
            names, membership_valid, fpl_valid = _validate_fpl(bootstrap, native_fixtures, expected, aliases, errors)
        if bodies.get("football_data_e0") is not None:
            e0 = _parse_csv(bodies["football_data_e0"])
            if not {"Div", "Date", "HomeTeam", "AwayTeam", "FTR"}.issubset(e0):
                errors.append("Football-Data current E0 CSV schema invalid")
            else:
                e0 = e0.loc[e0.HomeTeam.notna() & e0.AwayTeam.notna()]
                dates = _season_dates(e0.Date.tolist(), "Football-Data current E0", errors, dayfirst=True)
                if not e0.Div.eq("E0").all() or any(_canonical(value, aliases) is None for value in pd.concat([e0.HomeTeam, e0.AwayTeam])):
                    errors.append("Football-Data current E0 participants/division conflict with 2026-27")
                completed = e0.FTR.isin(["H", "D", "A"]).to_numpy()
                freshness["football_data_last_completed_match_date"] = dates.loc[completed].max().strftime("%Y-%m-%d") if completed.any() else None
        if bodies.get("understat_league") is not None:
            understat = _understat_table(json.loads(bodies["understat_league"]), aliases,
                                        request_records["understat_league"]["response_observed_at_utc"], errors)
            completed = understat.loc[understat.completed]
            freshness["understat_last_completed_match_date"] = completed.match_date.max() if len(completed) else None
        if include_players and membership_valid and fpl_valid and not errors:
            elements = bootstrap["elements"]
            player_requested = len(elements)
            with ThreadPoolExecutor(max_workers=min(6, max(1, player_requested))) as pool:
                pending = {pool.submit(archive.fetch, f"fpl_element_{int(row['id'])}",
                                       f"{FPL_API}/element-summary/{int(row['id'])}/",
                                       f"raw/fpl/element-summary/{int(row['id'])}.json"): int(row["id"]) for row in elements}
                for count, future in enumerate(as_completed(pending), start=1):
                    element = pending[future]
                    content, record = future.result()
                    data = None
                    if content is not None:
                        try:
                            data = json.loads(content)
                            player_downloaded += 1
                        except (ValueError, TypeError):
                            errors.append(f"FPL player {element}: invalid JSON")
                    summaries.append((element, data, record))
                    if count % 50 == 0 or count == player_requested:
                        print(f"Player summaries observed: {count}/{player_requested}", flush=True)
            history, invalid_history = _player_history(summaries, elements, native_fixtures, names, errors)
        cutoff = pd.Timestamp(_now())
        if membership_valid and fpl_valid:
            fixtures = _fixtures_table(native_fixtures, names, request_records["fpl_fixtures"]["response_observed_at_utc"], cutoff)
            completed = fixtures.loc[fixtures.finished.eq(True)]
            freshness["fpl_last_completed_match_date"] = completed.match_date.max() if len(completed) else None
            freshness["fpl_past_unfinished_fixture_count"] = int((pd.to_datetime(fixtures.kickoff_utc, utc=True, errors="coerce").le(cutoff) & ~fixtures.finished.eq(True)).sum())
            teams = pd.DataFrame(bootstrap["teams"])
            teams["canonical_team"] = teams["id"].map(names)
            teams["season"], teams["observed_at_utc"] = SEASON, request_records["fpl_bootstrap"]["response_observed_at_utc"]
            players = pd.DataFrame(bootstrap["elements"])
            players["canonical_team"] = players.team.map(names)
            players["position_type"] = players.element_type
            players["season"], players["observed_at_utc"] = SEASON, request_records["fpl_bootstrap"]["response_observed_at_utc"]
            tables["teams"] = _write_table_new(snapshot, "teams", teams)
            tables["players"] = _write_table_new(snapshot, "players", players)
            if bodies.get("football_data_fixtures") is not None:
                odds, odds_audit = _individual_odds(_parse_csv(bodies["football_data_fixtures"]), fixtures, aliases,
                                                   request_records["football_data_fixtures"]["response_observed_at_utc"],
                                                   jobs["football_data_fixtures"][0], errors)
        tables["fixtures"] = _write_table_new(snapshot, "fixtures", fixtures, FIXTURE_COLUMNS)
        tables["upcoming_targets"] = _write_table_new(snapshot, "upcoming_targets", fixtures.loc[fixtures.target_eligible], FIXTURE_COLUMNS)
        tables["individual_odds"] = _write_table_new(snapshot, "individual_odds", odds, ODDS_COLUMNS)
        tables["player_history"] = _write_table_new(snapshot, "player_history", history, HISTORY_COLUMNS)
        tables["understat_matches"] = _write_table_new(snapshot, "understat_matches", understat, UNDERSTAT_COLUMNS)
    except Exception as error:
        errors.append(f"Snapshot normalization failed: {type(error).__name__}: {error}")
        cutoff = pd.Timestamp(_now())
    player_complete = bool(include_players and player_requested > 0 and player_downloaded == player_requested and invalid_history == 0
                           and not any("FPL player" in error for error in errors))
    core_success = len(request_records) == 5 and all(record["status"] == "downloaded" for record in request_records.values())
    manifest = {"snapshot_id": snapshot_id, "season": SEASON, "snapshot_started_at_utc": _iso(started),
                "snapshot_completed_at_utc": cutoff.isoformat(), "manifest_written_at_utc": _iso(_now()),
                "usable": bool(core_success and membership_valid and fpl_valid and not errors),
                "membership_valid": bool(membership_valid), "fpl_schedule_valid": bool(fpl_valid),
                "expected_membership_reference": expected_info, "current_clubs": sorted(value for value in names.values() if value),
                "include_players": bool(include_players), "fpl_player_summaries_requested": player_requested,
                "fpl_player_summaries_downloaded": player_downloaded, "fpl_player_summaries_complete": player_complete,
                "invalid_player_history_rows_or_summaries": invalid_history,
                "freshness": freshness, "odds_normalization": odds_audit, "tables": tables,
                "errors": sorted(set(errors)), "requests": sorted(archive.requests, key=lambda row: (row["request_started_at_utc"], row["source_key"])),
                "timestamp_semantics": {"observed_at_utc": "Actual UTC completion of public response-body capture, not a provider publication time",
                                        "http_response_date": "Server HTTP Date header only; not quote publication or source-data freshness",
                                        "snapshot_completed_at_utc": "Observation cutoff after all requests, before normalized-file serialization",
                                        "manifest_written_at_utc": "Actual UTC manifest creation after normalization",
                                        "understat_native_datetime": "Printed provider clock retained; no inferred timezone for xG history"},
                "limitations": ["Retrieval freshness does not establish source update freshness; use recorded last-completed-match dates.",
                                "Forecast writers must recheck kickoff > their own record-creation time; eligibility can expire after capture.",
                                "Individual odds are incomplete-timestamp retrospective observations, not verified simultaneous/executable quotes.",
                                "Player histories cover the bootstrap player registry at capture; missing or failed summaries must not be called complete.",
                                "Raw successful and unsuccessful HTTP response bodies are retained; no prior snapshot is overwritten."]}
    _write_json_new(snapshot / "manifest.json", manifest)
    return snapshot


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, default=Path(__file__).resolve().parent / "snapshots")
    parser.add_argument("--players", action="store_true", help="Explicitly collect all current FPL element-summary histories with at most six workers")
    args = parser.parse_args()
    snapshot = collect_snapshot(args.output_root, include_players=args.players)
    manifest = json.loads((snapshot / "manifest.json").read_text(encoding="utf-8"))
    print(json.dumps({"snapshot": str(snapshot), "usable": manifest["usable"], "errors": manifest["errors"],
                      "freshness": manifest["freshness"], "players_complete": manifest["fpl_player_summaries_complete"]}, indent=2))
    if not manifest["usable"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
