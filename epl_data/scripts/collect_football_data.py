"""Archive Football-Data files and curate histories for the current EPL cohort.

Run: python scripts/collect_football_data.py
No credentials, commercial subscriptions, or live bets are used. Provider columns
are preserved in matches; normalized team observations and lagged features are
separate derived tables. See metadata/football_data_notes.md for limitations.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from itertools import groupby

import numpy as np
import pandas as pd

from common import AS_OF_DATE, ROOT, Collector, canonical_team, current_teams, write_table

SOURCE = "https://www.football-data.co.uk"
DIVISIONS = {"E0": "Premier League", "E1": "Championship / Division 1",
             "E2": "League One / Division 2", "E3": "League Two / Division 3"}
TEXT_FIELDS = {"Div", "Date", "Time", "HomeTeam", "AwayTeam", "FTR", "HTR", "Referee", "Res"}
BOOKMAKERS = {
    "1XB": "1XBet", "B365": "Bet365", "BF": "Betfair", "BFD": "Betfred",
    "BMGM": "BetMGM", "BV": "BetVictor", "BS": "Blue Square", "BW": "Bet & Win",
    "CL": "Coral", "GB": "Gamebookers", "IW": "Interwetten", "LB": "Ladbrokes",
    "PP": "Paddy Power", "PS": "Pinnacle", "P": "Pinnacle", "SK": "Skybet", "SKB": "Skybet",
    "SO": "Sporting Odds", "SB": "Sportingbet", "SJ": "Stan James",
    "SY": "Stanleybet", "VC": "VC Bet", "WH": "William Hill",
    "BFE": "Betfair Exchange", "Max": "Market maximum", "Avg": "Market average",
    "BbMx": "Betbrain maximum", "BbAv": "Betbrain average",
}
SIDE_STATS = {
    "goals": ("FTHG", "FTAG"), "half_time_goals": ("HTHG", "HTAG"),
    "expected_goals": ("HxG", "AxG"),
    "shots": ("HS", "AS"), "shots_on_target": ("HST", "AST"),
    "corners": ("HC", "AC"), "fouls": ("HF", "AF"),
    "yellow_cards": ("HY", "AY"), "red_cards": ("HR", "AR"),
    "offsides": ("HO", "AO"), "woodwork": ("HHW", "AHW"),
    "free_kicks_conceded": ("HFKC", "AFKC"), "booking_points": ("HBP", "ABP"),
}
METRICS = ["points", "win", "goals_for", "goals_against", "goal_difference",
           "shots_for", "shots_against", "shots_on_target_for", "shots_on_target_against",
           "corners_for", "corners_against", "yellow_cards_for", "red_cards_for",
           "shots_difference", "shots_on_target_difference", "corners_difference",
           "expected_goals_for", "expected_goals_against", "expected_goals_difference"]


def decode_csv(content):
    for encoding in ("utf-8-sig", "cp1252", "latin1"):
        try:
            return content.decode(encoding), encoding
        except UnicodeDecodeError:
            pass
    raise ValueError("Unable to decode source CSV")


def parse_csv(content):
    """Retain excess nonempty fields, but remove empty trailing CSV padding."""
    text, encoding = decode_csv(content)
    rows = list(csv.reader(io.StringIO(text)))
    if not rows:
        raise ValueError("Empty CSV")
    header = [x.strip() for x in rows[0]]
    while header and not header[-1]:
        header.pop()
    header = [value or f"source_unnamed_{index}" for index, value in enumerate(header)]
    clean, anomalies = [], []
    for source_row, row in enumerate(rows[1:], start=2):
        while len(row) > len(header) and not row[-1].strip():
            row.pop()
        if not any(x.strip() for x in row):
            continue
        if len(row) > len(header):
            anomalies.append({"source_row": source_row, "extra_values": row[len(header):]})
            header.extend(f"source_extra_{i}" for i in range(len(header), len(row)))
        clean.append((source_row, row))
    records = []
    for source_row, row in clean:
        record = dict(zip(header, row))
        record["source_row"] = source_row
        records.append(record)
    frame = pd.DataFrame(records).replace("", pd.NA)
    # All native numerical values are parsed without dropping their raw archive.
    for column in header:
        if column not in TEXT_FIELDS:
            values = frame[column].dropna()
            numeric = pd.to_numeric(values, errors="coerce")
            if len(values) == numeric.notna().sum():
                frame[column] = pd.to_numeric(frame[column], errors="coerce")
    return frame, encoding, anomalies


def fetch_season(collector, year, division, reuse_raw=False):
    code = f"{year % 100:02d}{(year + 1) % 100:02d}"
    season = f"{year}-{(year + 1) % 100:02d}"
    relative = f"{code}/{division}.csv"
    url = f"{SOURCE}/mmz4281/{relative}"
    raw_path = collector.raw / relative
    if reuse_raw and raw_path.exists():
        content = raw_path.read_bytes()
    else:
        response = collector.fetch(url, relative)
        if response is None:
            return None, {"season": season, "division": division, "status": "download_failed"}
        content = response.content
    try:
        frame, encoding, anomalies = parse_csv(content)
        if not {"HomeTeam", "AwayTeam", "Date"}.issubset(frame.columns):
            raise ValueError(f"Missing expected CSV columns: {list(frame.columns)[:10]}")
        native_columns = [c for c in frame.columns if c != "source_row"]
        # A handful of older archives include empty or footer records.
        valid = frame["HomeTeam"].notna() & frame["AwayTeam"].notna()
        dropped = int((~valid).sum())
        frame = frame.loc[valid].copy()
        frame["season"] = season
        frame["season_start_year"] = year
        frame["competition"] = DIVISIONS[division]
        frame["division"] = division
        frame["source_url"] = url
        frame["source_file"] = relative
        frame["home_team_current"] = frame["HomeTeam"].map(canonical_team)
        frame["away_team_current"] = frame["AwayTeam"].map(canonical_team)
        frame["home_is_current_cohort"] = frame["home_team_current"].notna()
        frame["away_is_current_cohort"] = frame["away_team_current"].notna()
        parsed_date = pd.to_datetime(frame["Date"], format="mixed", dayfirst=True, errors="coerce")
        frame["match_date"] = parsed_date.dt.strftime("%Y-%m-%d")
        frame["source_match_key"] = [
            "fd_" + hashlib.sha256(f"{season}|{division}|{h}|{a}".encode()).hexdigest()[:24]
            for h, a in zip(frame["HomeTeam"], frame["AwayTeam"])
        ]
        frame["kickoff_utc"] = pd.NA
        frame["kickoff_timezone_assumption"] = pd.NA
        if "Time" in frame:
            clock = frame["Time"].astype("string")
            has_time = clock.str.fullmatch(r"\d{1,2}:\d{2}", na=False) & parsed_date.notna()
            dt = pd.to_datetime(frame.loc[has_time, "match_date"] + " " + clock.loc[has_time],
                                format="%Y-%m-%d %H:%M", errors="coerce")
            utc = dt.dt.tz_localize("Europe/London", ambiguous="NaT", nonexistent="NaT").dt.tz_convert("UTC")
            frame.loc[has_time, "kickoff_utc"] = utc.dt.strftime("%Y-%m-%dT%H:%M:%SZ")
            frame.loc[has_time, "kickoff_timezone_assumption"] = "England local time; Europe/London assumed"
        full_result = frame.get("FTR", pd.Series(pd.NA, index=frame.index)).isin(["H", "D", "A"])
        goals_present = (pd.to_numeric(frame.get("FTHG", pd.Series(index=frame.index, dtype=float)), errors="coerce").notna()
                         & pd.to_numeric(frame.get("FTAG", pd.Series(index=frame.index, dtype=float)), errors="coerce").notna())
        frame["completed"] = full_result & goals_present
        frame["future_relative_to_asof"] = parsed_date.gt(pd.Timestamp(AS_OF_DATE))
        frame["completed_asof"] = frame["completed"] & parsed_date.le(pd.Timestamp(AS_OF_DATE))
        frame["pinnacle_stale_warning"] = parsed_date.ge(pd.Timestamp("2025-07-23"))
        curated = frame.loc[frame["home_is_current_cohort"] | frame["away_is_current_cohort"]].copy()
        report = {"season": season, "division": division, "status": "parsed", "encoding": encoding,
                  "source_match_rows": len(frame), "cohort_match_rows": len(curated),
                  "native_column_count": len(native_columns), "native_columns": native_columns,
                  "invalid_dates": int(parsed_date.isna().sum()), "nonmatch_rows_removed": dropped,
                  "csv_anomalies": anomalies,
                  "future_completed_rows": int((frame["completed"] & frame["future_relative_to_asof"]).sum())}
        return curated, report
    except Exception as error:
        return None, {"season": season, "division": division, "status": "parse_failed", "error": str(error)}


def team_observations(matches):
    observations = []
    identity = ["source_match_key", "season", "season_start_year", "competition", "division",
                "match_date", "kickoff_utc", "completed", "completed_asof", "future_relative_to_asof",
                "source_url", "pinnacle_stale_warning"]
    for side, other in (("home", "away"), ("away", "home")):
        subset = matches.loc[matches[f"{side}_is_current_cohort"]].copy()
        out = subset[identity].copy()
        home = side == "home"
        out["team"] = subset[f"{side}_team_current"]
        out["opponent"] = subset[f"{other}_team_current"].fillna(subset["AwayTeam" if home else "HomeTeam"])
        out["opponent_is_current_cohort"] = subset[f"{other}_is_current_cohort"]
        out["venue"] = side
        out["provider_team_name"] = subset["HomeTeam" if home else "AwayTeam"]
        out["provider_opponent_name"] = subset["AwayTeam" if home else "HomeTeam"]
        for name, (h, a) in SIDE_STATS.items():
            own, opp = (h, a) if home else (a, h)
            out[f"{name}_for"] = pd.to_numeric(subset.get(own, np.nan), errors="coerce")
            out[f"{name}_against"] = pd.to_numeric(subset.get(opp, np.nan), errors="coerce")
        result = subset.get("FTR", pd.Series(pd.NA, index=subset.index))
        out["result"] = result.map({"H": "W" if home else "L", "D": "D", "A": "L" if home else "W"})
        out.loc[~subset["completed_asof"], "result"] = pd.NA
        out["points"] = out["result"].map({"W": 3, "D": 1, "L": 0})
        out["win"] = out["result"].map({"W": 1, "D": 0, "L": 0})
        out["draw"] = out["result"].map({"W": 0, "D": 1, "L": 0})
        out["loss"] = out["result"].map({"W": 0, "D": 0, "L": 1})
        out["goal_difference"] = out["goals_for"] - out["goals_against"]
        for statistic in ("shots", "shots_on_target", "corners", "expected_goals"):
            out[f"{statistic}_difference"] = out[f"{statistic}_for"] - out[f"{statistic}_against"]
        for column in ("Attendance", "Referee"):
            values = subset.get(column, pd.NA)
            out[column.lower()] = pd.to_numeric(values, errors="coerce") if column == "Attendance" else values
        for book in ("Avg", "Max", "B365", "PS", "P", "BFE"):
            for closing in (False, True):
                prefix = book + ("C" if closing else "")
                for outcome, suffix in (("win", "H" if home else "A"), ("draw", "D"), ("loss", "A" if home else "H")):
                    source_column = prefix + suffix
                    if source_column in subset:
                        out[f"odds_{book}_{'closing' if closing else 'preclosing'}_{outcome}"] = subset[source_column]
        observations.append(out)
    result = pd.concat(observations, ignore_index=True)
    result = result.sort_values(["team", "match_date", "source_match_key"]).reset_index(drop=True)
    return result


def season_summaries(observations):
    records = []
    completed = observations.loc[observations["completed_asof"]]
    for (team, season, year, division, competition), group in completed.groupby(
            ["team", "season", "season_start_year", "division", "competition"]):
        record = {"team": team, "season": season, "season_start_year": year, "division": division,
                  "competition": competition, "matches": len(group), "first_match_date": group["match_date"].min(),
                  "last_match_date": group["match_date"].max(), "as_of_date": AS_OF_DATE,
                  "wins": int(group["win"].sum()), "draws": int(group["draw"].sum()),
                  "losses": int(group["loss"].sum()), "points": int(group["points"].sum()),
                  "win_percentage": float(group["win"].mean())}
        for metric in METRICS:
            record[f"{metric}_mean"] = group[metric].mean()
            record[f"{metric}_observed_matches"] = int(group[metric].notna().sum())
            record[f"{metric}_sum"] = group[metric].sum(min_count=1)
        records.append(record)
    return pd.DataFrame(records).sort_values(["team", "season"])


def lagged_features(observations, summaries):
    """All inputs have match date strictly before the focal match date.

    Date grouping prevents leakage if a provider ever gives the same club two
    matches on one calendar day. Only completed matches available by AS_OF_DATE
    enter history. Prior-season statistics carry their division identifier.
    """
    previous_season = {}
    for record in summaries.to_dict("records"):
        previous_season[(record["team"], record["season_start_year"] + 1)] = record
    rows = []
    for team, group in observations.groupby("team", sort=True):
        history, per_season = [], {}
        ordered = group.sort_values(["match_date", "source_match_key"]).to_dict("records")
        for date, same_day in groupby(ordered, key=lambda record: record["match_date"]):
            day = list(same_day)
            # No trustworthy date means no time-aligned features.
            if pd.isna(date):
                continue
            for record in day:
                out = {key: record[key] for key in ["source_match_key", "team", "opponent", "season", "division", "match_date", "venue"]}
                out["prior_observed_matches_all_divisions"] = len(history)
                out["features_last_match_date"] = history[-1]["match_date"] if history else None
                if history:
                    out["rest_days"] = (pd.Timestamp(date) - pd.Timestamp(history[-1]["match_date"])).days
                prior = previous_season.get((team, record["season_start_year"]))
                out["previous_season_division"] = prior["division"] if prior else None
                out["previous_season_matches"] = prior["matches"] if prior else None
                out["previous_season_win_percentage"] = prior["win_percentage"] if prior else None
                out["previous_season_points_per_match"] = prior["points_mean"] if prior else None
                for window in (5, 10):
                    tail = history[-window:]
                    out[f"prior_{window}_matches_observed"] = len(tail)
                    for metric in METRICS:
                        values = [x[metric] for x in tail if pd.notna(x[metric])]
                        out[f"prior_{window}_{metric}_mean"] = float(np.mean(values)) if values else None
                        out[f"prior_{window}_{metric}_observations"] = len(values)
                current = per_season.get((record["season"], record["division"]), {"matches": 0, "metrics": {}})
                out["season_prior_matches"] = current["matches"]
                for metric in METRICS:
                    total, count = current["metrics"].get(metric, (0.0, 0))
                    out[f"season_prior_{metric}_mean"] = total / count if count else None
                    out[f"season_prior_{metric}_sum"] = total if count else None
                    out[f"season_prior_{metric}_observations"] = count
                rows.append(out)
            for record in (record for record in day if record["completed_asof"]):
                history.append(record)
                current = per_season.setdefault((record["season"], record["division"]), {"matches": 0, "metrics": {}})
                current["matches"] += 1
                for metric in METRICS:
                    if pd.notna(record[metric]):
                        total, count = current["metrics"].get(metric, (0.0, 0))
                        current["metrics"][metric] = (total + float(record[metric]), count + 1)
    return pd.DataFrame(rows)


def odds_long(matches):
    records = []
    for prefix, bookmaker in BOOKMAKERS.items():
        for closing in (False, True):
            p = prefix + ("C" if closing else "")
            columns = [p + suffix for suffix in ("H", "D", "A")]
            if not all(column in matches for column in columns):
                continue
            eligible = matches[columns].apply(pd.to_numeric, errors="coerce").notna().any(axis=1)
            subset = matches.loc[eligible]
            out = subset[["source_match_key", "season", "division", "match_date", "HomeTeam", "AwayTeam",
                          "home_team_current", "away_team_current", "completed_asof"]].copy()
            out["bookmaker_or_aggregate"] = bookmaker
            out["source_prefix"] = prefix
            out["snapshot_type"] = "closing" if closing else "preclosing"
            out["quote_timestamp_utc"] = pd.NA
            for column, outcome in zip(columns, ("home", "draw", "away")):
                out[f"decimal_odds_{outcome}"] = pd.to_numeric(subset[column], errors="coerce")
                out[f"source_column_{outcome}"] = column
            price_columns = [f"decimal_odds_{outcome}" for outcome in ("home", "draw", "away")]
            out["valid_complete_1x2_quote"] = out[price_columns].gt(1).all(axis=1)
            out["has_invalid_decimal_odds"] = out[price_columns].le(1).any(axis=1)
            out["is_market_aggregate"] = prefix in {"Avg", "Max", "BbMx", "BbAv"}
            out["is_exchange"] = prefix == "BFE"
            out["pinnacle_stale_warning"] = subset["pinnacle_stale_warning"] if bookmaker == "Pinnacle" else False
            records.append(out)
    return pd.concat(records, ignore_index=True) if records else pd.DataFrame()


def make_dictionary(matches, native_columns, notes_text):
    definitions = {
        "HxG": "Home expected goals (newer source field; xG methodology not specified in archived notes)",
        "AxG": "Away expected goals (newer source field; xG methodology not specified in archived notes)",
        "SKBH": "Skybet home win odds", "SKBD": "Skybet draw odds", "SKBA": "Skybet away win odds",
    }
    for line in notes_text.splitlines():
        if " = " in line:
            key, meaning = line.split(" = ", 1)
            for alias in re.split(r" and ", key.strip()):
                definitions[alias.strip()] = meaning.strip()
    records = []
    for column in matches.columns:
        explanation = definitions.get(column)
        if explanation is None:
            for prefix, bookmaker in sorted(BOOKMAKERS.items(), key=lambda x: -len(x[0])):
                if column.startswith(prefix + "C"):
                    nonclosing = prefix + column[len(prefix) + 1:]
                    if nonclosing in definitions:
                        explanation = "Closing snapshot: " + definitions[nonclosing]
                        break
        records.append({"column": column, "kind": "native_provider" if column in native_columns else "derived_metadata",
                        "description": explanation or "See archived provider notes or collector source for this field.",
                        "dtype": str(matches[column].dtype), "non_null_rows": int(matches[column].notna().sum()),
                        "total_rows": len(matches)})
    return pd.DataFrame(records)


def main():
    started_at = time.perf_counter()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reuse-raw", action="store_true", help="Rebuild derived tables from archived bytes; download only missing files")
    args = parser.parse_args()
    collector = Collector("football_data")
    previous_manifest = ROOT / "metadata/football_data_manifest.json"
    if args.reuse_raw and previous_manifest.exists():
        collector.records = json.loads(previous_manifest.read_text(encoding="utf-8")).get("requests", [])
    elif args.reuse_raw:
        # An interrupted previous build may have archived every file but not yet
        # flushed its request ledger. Recover only observable facts; never invent
        # a response status or pretend filesystem time is an exact request time.
        for archived in sorted(collector.raw.rglob("*")):
            if not archived.is_file():
                continue
            relative = archived.relative_to(collector.raw).as_posix()
            source_relative = relative[len("documentation/"):] if relative.startswith("documentation/") else "mmz4281/" + relative
            content = archived.read_bytes()
            collector.records.append({
                "source": "football_data", "url": SOURCE + "/" + source_relative,
                "parameters": None, "requested_as_of_date": AS_OF_DATE,
                "retrieved_at_utc": None,
                "archive_written_at_utc": datetime.fromtimestamp(archived.stat().st_mtime, timezone.utc).isoformat(),
                "retrieval_time_method": "Filesystem modification time; exact HTTP retrieval time not preserved",
                "source_published_at_utc": None, "http_status": None,
                "path": archived.relative_to(ROOT).as_posix(), "bytes": len(content),
                "sha256": hashlib.sha256(content).hexdigest(), "status": "recovered_from_archive",
                "provenance_note": "Public download completed in an interrupted build; HTTP ledger was not flushed",
            })
    for page in ("englandm.php", "data.php", "notes.txt", "fixtures.csv"):
        if not (args.reuse_raw and (collector.raw / "documentation" / page).exists()):
            collector.fetch(f"{SOURCE}/{page}", "documentation/" + page)
    years = list(range(1993, 2027))
    frames, coverage = [], []
    with ThreadPoolExecutor(max_workers=5) as pool:
        pending = {pool.submit(fetch_season, collector, year, division, args.reuse_raw): (year, division)
                   for year in years for division in DIVISIONS}
        for future in as_completed(pending):
            frame, report = future.result()
            coverage.append(report)
            if frame is not None:
                frames.append(frame)
            if len(coverage) % 20 == 0:
                print(f"Processed {len(coverage)}/{len(pending)} season/division files", flush=True)
    coverage.sort(key=lambda r: (r["season"], r["division"]))
    # Persist HTTP provenance before any heavier derived-data work can be
    # interrupted. The final write below replaces this intermediate stage.
    collector.finish(notes={"stage": "acquisition_complete_processing_pending", "season_parsing": coverage})
    if not frames:
        collector.finish(notes={"parsing": coverage})
        raise RuntimeError("No Football-Data season files collected")
    matches = pd.concat(frames, ignore_index=True).sort_values(["season", "division", "match_date", "source_match_key"])
    if "Attendance" in matches:
        # Old source footer records can prevent per-file numerical inference.
        # After the nonmatch rows are removed every retained attendance value
        # must remain representable, rather than silently losing provider text.
        attendance = pd.to_numeric(matches["Attendance"], errors="coerce")
        bad_attendance = matches["Attendance"].notna() & attendance.isna()
        if bad_attendance.any():
            matches["Attendance_source_text"] = matches["Attendance"].astype("string")
        matches["Attendance"] = attendance
    # Quarantine any completed result dated after the project's as-of cutoff.
    future_results = matches.loc[matches["completed"] & matches["future_relative_to_asof"]].copy()
    if not future_results.empty:
        write_table(future_results, collector.out / "quarantined_future_results")
        matches = matches.loc[~(matches["completed"] & matches["future_relative_to_asof"])].copy()
    assert not matches["source_match_key"].duplicated().any(), "Unexpected duplicate league fixture keys"
    team_matches = team_observations(matches)
    assert set(team_matches["team"]) <= set(current_teams()["team"])
    assert not team_matches[["source_match_key", "team"]].duplicated().any()
    completed = team_matches.loc[team_matches["completed_asof"]]
    assert set(completed["points"].dropna()) <= {0, 1, 3}
    assert (completed["goals_for"] >= 0).all() and (completed["goals_against"] >= 0).all()
    summaries = season_summaries(team_matches)
    print(f"Curated {len(matches):,} matches and {len(team_matches):,} focal-team observations; constructing lagged features", flush=True)
    features = lagged_features(team_matches, summaries)
    has_history = features["features_last_match_date"].notna()
    assert (features.loc[has_history, "features_last_match_date"] < features.loc[has_history, "match_date"]).all()
    native_columns = {column for report in coverage for column in report.get("native_columns", [])}
    notes_path = collector.raw / "documentation/notes.txt"
    notes_text = decode_csv(notes_path.read_bytes())[0] if notes_path.exists() else ""
    odds = odds_long(matches)
    tables = {"matches_current_cohort": matches, "team_match_history": team_matches,
              "team_season_summary": summaries, "team_match_lagged_features": features,
              "match_odds_1x2_long": odds, "field_dictionary": make_dictionary(matches, native_columns, notes_text)}
    for name, table in tables.items():
        path = collector.out / name
        write_table(table, path)
        if path.with_suffix(".parquet").exists():
            path.with_suffix(".parquet_error.txt").unlink(missing_ok=True)
    coverage_flat = [{key: value for key, value in report.items() if key not in {"native_columns", "csv_anomalies"}}
                     for report in coverage]
    write_table(pd.DataFrame(coverage_flat), collector.out / "season_source_coverage")
    cohort_coverage = team_matches.groupby(["team", "season", "division"], as_index=False).agg(
        match_rows=("source_match_key", "count"), completed_matches=("completed_asof", "sum"),
        first_match_date=("match_date", "min"), last_match_date=("match_date", "max"),
        matches_with_shots=("shots_for", "count"))
    write_table(cohort_coverage, collector.out / "team_season_coverage")
    totals = {name: {"rows": len(table), "columns": len(table.columns)} for name, table in tables.items()}
    totals.update({"source_files_attempted": len(pending), "source_files_parsed": len(frames),
                   "future_results_quarantined": len(future_results),
                   "first_match_date": matches["match_date"].min(), "last_match_date": matches["match_date"].max(),
                   "current_cohort_count": team_matches["team"].nunique(),
                   "failed_source_files": [r for r in coverage if r["status"] != "parsed"]})
    totals["collector_runtime_seconds"] = round(time.perf_counter() - started_at, 2)
    collector.finish(notes={"summary": totals, "season_parsing": coverage,
                            "license": "Provider permits private individual use; does not grant an unrestricted open-data license.",
                            "time_cutoff": AS_OF_DATE})
    (ROOT / "metadata/football_data_notes.md").write_text(NOTES + "\n\nAcquisition summary:\n\n```json\n" +
        json.dumps(totals, indent=2) + "\n```\n", encoding="utf-8")
    print(json.dumps(totals, indent=2), flush=True)


NOTES = """# Football-Data match histories and odds

Sources: [English season archive](https://www.football-data.co.uk/englandm.php),
[provider documentation and usage statement](https://www.football-data.co.uk/data.php),
[field definitions](https://www.football-data.co.uk/notes.txt).
Original bytes, retrieval times, URLs, HTTP status and SHA256 hashes are archived.

## Cohort and scope

The analysis cohort is the 20 clubs in metadata/current_teams.csv for 2026-27,
as of 2026-10-06. Raw public files contain whole leagues. Curated match records
require at least one current club; team_match_history contains only current clubs
as the focal team. Former clubs can appear solely as their historical opponents.
E0 is the Premier League; E1/E2/E3 track current clubs' histories in the second,
third and fourth tiers, including the old Division 1/2/3 names. Lower-tier games
must not be treated as Premier League games. National cups, European matches,
friendlies and promotion play-off matches are not guaranteed in this source.

## Tables

- matches_current_cohort: all native fields (full/half-time scores, results,
  attendance when supplied, shots, corners, fouls, offsides, cards, referee,
  expected goals where newly supplied, and decimal odds) plus normalized names,
  provenance, dates and eligibility flags.
- team_match_history: one observation per eligible focal team per match. For and
  against statistics and selected odds are oriented to that club; complete native
  odds including totals and Asian handicaps remain in matches_current_cohort.
- match_odds_1x2_long: bookmaker or market aggregate with home/draw/away odds,
  source fields, preclosing versus closing label, Pinnacle reliability flag and
  flags for missing/invalid decimal prices. Quotes with prices at or below one
  remain archived but are not marked as valid complete quotes.
- team_season_summary: descriptive season/division totals, averages, counts and
  observed-statistic denominators. The active season is partial, and points are
  match-derived (not official table points after administrative deductions).
- team_match_lagged_features: previous 5/10 completed matches across observed
  divisions, strictly earlier dates; season-to-date means/totals restricted to the
  same season/division; prior-calendar-season win proportion and division. Empty
  history remains missing. Goal, expected-goal, shot, shots-on-target and corner differences
  measure outperformance relative to the observed opponents in each match.
  These descriptive inputs are not a trained model.
- team_season_coverage and season_source_coverage: coverage and missing-file audit.
- field_dictionary: native-field descriptions where provider documentation gives
  them, data types and nonnull counts. All tables have CSV and typed Parquet copies.

Rebuild from saved bytes with `python scripts/collect_football_data.py --reuse-raw`;
the original retrieval records and hashes are retained. Omit that option to refresh.
The initial download completed before its long feature build was interrupted.
Its unflushed HTTP ledger was recovered from saved paths/bytes/SHA256 and original
archive-write timestamps. Exact HTTP retrieval times and statuses from that first
run are unrecorded; the recovered records explicitly distinguish filesystem time.

## Dates and reproducibility

Source dates are parsed day first and as-of selection includes 2026-10-06.
Completed outcomes dated later are quarantined outside the analysis tables.
Source kickoff times, when present, are converted assuming English local time
(Europe/London, respecting daylight saving); the source notes do not explicitly
state a timezone, so the assumption is recorded. Missing kickoff times stay null.
Only source dates support feature ordering; games on the same date cannot inform
each other's features. source_match_key is a deterministic hash of season,
division and provider home/away names, stable when a fixture date is rescheduled;
it is not an official fixture identifier. Names are linked through an explicit
alias map, not through unreliable fuzzy matching.

## Odds and modeling limitations

Preclosing odds are snapshots collected after market opening, ordinarily Friday
afternoons for weekend games or Tuesday afternoons for midweek games. They are
not verified opening prices. Closing columns have a C after the bookmaker code.
Most two-snapshot series start in 2019-20; Pinnacle closing 1X2 goes back to
2012-13. Individual quote timestamps, bookmaker stake limits, commission and
execution availability are absent. Quotes or maxima from different bookmakers
need not be synchronized; they do not establish a tradeable arbitrage. Closing
odds must not become a predictor at an earlier preclosing decision time.

The provider warns that Pinnacle's public odds API has been unreliable since
2025-07-23; both its preclosing and closing prices can be stale. Pinnacle fields
are preserved and flagged, not silently treated as reliable. Market average and
maximum prices cease including Pinnacle after that date according to the provider.
Coverage, bookmakers and statistic definitions change over time. Results begin
in 1993-94; detailed statistics and odds generally begin around 2000-01. Missing
fields are missing rather than zero. Raw provider records can contain errors.
The newest E0 files also contain HxG/AxG: expected goals from this provider.
Their detailed model/methodology is not identified in the archived notes and
should not be assumed identical to expected goals from another source.
Historical cohort selection induces survivor bias if used for a league-wide
backtest. Build train/test splits in chronological order and retain division.
Prior-season statistics in a lower division must be interpreted accordingly.

## Usage

Football-Data says its free data is intended for private individuals, and excludes
commercial or data-training products using automated bots/scrapers/AI. This
collection is a private academic project archive; these files are not asserted to
have an unrestricted open license. Review the archived usage statement and seek
provider permission before redistribution or a use outside that scope.
"""

if __name__ == "__main__":
    main()
