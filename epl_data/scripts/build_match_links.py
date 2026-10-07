"""Build exact, auditable EPL match links across the collected source tables.

Run: python scripts/build_match_links.py
Only match_source_links.csv/.parquet and match_link_validation.json are written.
No approximate names, nearby dates, inferred kickoff times, or score-based joins.
"""
from __future__ import annotations

import hashlib
import itertools
import json

import pandas as pd

from common import AS_OF_DATE, ROOT, canonical_team, current_teams, now_utc, write_table

# These aliases describe historical opponents, not additional analysis clubs.
OPPONENT_ALIASES = {
    "Birmingham City": ["Birmingham", "Birmingham City"],
    "Blackburn Rovers": ["Blackburn", "Blackburn Rovers"],
    "Bolton Wanderers": ["Bolton", "Bolton Wanderers"],
    "Bradford City": ["Bradford", "Bradford City"],
    "Cardiff City": ["Cardiff", "Cardiff City"],
    "Charlton Athletic": ["Charlton", "Charlton Athletic"],
    "Derby County": ["Derby", "Derby County"],
    "Huddersfield Town": ["Huddersfield", "Huddersfield Town"],
    "Leicester City": ["Leicester", "Leicester City"],
    "Luton Town": ["Luton", "Luton Town"],
    "Norwich City": ["Norwich", "Norwich City"],
    "Oldham Athletic": ["Oldham", "Oldham Athletic"],
    "Queens Park Rangers": ["QPR", "Queens Park Rangers"],
    "Sheffield United": ["Sheffield United", "Sheffield Utd"],
    "Sheffield Wednesday": ["Sheffield Weds", "Sheffield Wednesday"],
    "Stoke City": ["Stoke", "Stoke City"],
    "Swansea City": ["Swansea", "Swansea City"],
    "Swindon Town": ["Swindon", "Swindon Town"],
    "West Bromwich Albion": ["West Brom", "West Bromwich Albion", "West Bromwich"],
    "West Ham United": ["West Ham", "West Ham United"],
    "Wigan Athletic": ["Wigan", "Wigan Athletic"],
    "Wolverhampton Wanderers": ["Wolves", "Wolverhampton Wanderers", "Wolverhampton"],
}
OPPONENT_LOOKUP = {alias.casefold(): name for name, aliases in OPPONENT_ALIASES.items() for alias in aliases}
KEY_FIELDS = ["season", "match_date", "home_team", "away_team"]
SOURCES = ["football_data", "understat", "espn", "fpl", "statsbomb"]
ID_COLUMNS = {"football_data": "source_match_key", "understat": "understat_id",
              "espn": "espn_match_id", "fpl": "fpl_fixture_id", "statsbomb": "statsbomb_match_id"}


def normalize_team(value):
    if pd.isna(value):
        return None
    value = str(value).strip()
    return canonical_team(value) or OPPONENT_LOOKUP.get(value.casefold()) or value


def native_calendar_date(values):
    """Take the printed source date; do not assume an undocumented timezone."""
    text = values.astype("string").str.slice(0, 10)
    valid = pd.to_datetime(text, format="%Y-%m-%d", errors="coerce")
    return valid.dt.strftime("%Y-%m-%d").astype("string")


def decorate(frame, source):
    frame = frame.copy()
    frame["home_team"] = frame["home_team"].map(normalize_team)
    frame["away_team"] = frame["away_team"].map(normalize_team)
    frame[f"{source}_match_date"] = frame["match_date"]
    frame[f"{source}_completed"] = frame[f"{source}_completed"].astype("boolean")
    ids = frame[ID_COLUMNS[source]]
    assert ids.notna().all(), f"Missing {source} source IDs"
    assert not ids.duplicated().any(), f"Repeated {source} source IDs"
    valid = frame[KEY_FIELDS].notna().all(axis=1)
    duplicates = frame.loc[valid].duplicated(KEY_FIELDS, keep=False)
    assert not duplicates.any(), f"Ambiguous exact {source} match keys"
    key_strings = []
    for row, eligible, source_id in zip(frame[KEY_FIELDS].itertuples(index=False, name=None), valid, ids):
        key = "|".join(str(x) for x in row) if eligible else f"unmatchable|{source}|{source_id}"
        key_strings.append("match_" + hashlib.sha256(key.encode("utf-8")).hexdigest()[:24])
    frame["link_record_key"] = key_strings
    frame[f"{source}_exact_key_eligible"] = valid
    return frame


def inputs():
    fd_native = pd.read_parquet(ROOT / "data/processed/football_data/matches_current_cohort.parquet")
    fd_native = fd_native.loc[fd_native["division"].eq("E0")].copy()
    fd = pd.DataFrame({
        "season": fd_native["season"], "match_date": fd_native["match_date"],
        "home_team": fd_native["HomeTeam"], "away_team": fd_native["AwayTeam"],
        "source_match_key": fd_native["source_match_key"],
        "football_data_home_name_native": fd_native["HomeTeam"],
        "football_data_away_name_native": fd_native["AwayTeam"],
        "football_data_date_native": fd_native["Date"],
        "football_data_time_native": fd_native.get("Time", pd.NA),
        "football_data_kickoff_utc": fd_native["kickoff_utc"],
        "football_data_kickoff_timezone_assumption": fd_native["kickoff_timezone_assumption"],
        "football_data_home_goals": pd.to_numeric(fd_native["FTHG"], errors="coerce"),
        "football_data_away_goals": pd.to_numeric(fd_native["FTAG"], errors="coerce"),
        "football_data_full_time_result": fd_native["FTR"],
        "football_data_completed": fd_native["completed_asof"],
    })
    us_native = pd.read_parquet(ROOT / "data/processed/understat/matches.parquet")
    us = pd.DataFrame({
        "season": us_native["season"], "match_date": native_calendar_date(us_native["datetime"]),
        "home_team": us_native["h__title"], "away_team": us_native["a__title"],
        "understat_id": us_native["id"].astype("string"),
        "understat_home_name_native": us_native["h__title"],
        "understat_away_name_native": us_native["a__title"],
        "understat_datetime_native": us_native["datetime"],
        "understat_home_goals": pd.to_numeric(us_native["goals__h"], errors="coerce"),
        "understat_away_goals": pd.to_numeric(us_native["goals__a"], errors="coerce"),
        "understat_completed": us_native["isResult"],
    })
    espn_native = pd.read_parquet(ROOT / "data/processed/espn/match_info.parquet")
    source_year = pd.to_numeric(espn_native["requested_source_season"], errors="raise").astype(int)
    es = pd.DataFrame({
        "season": source_year.map(lambda year: f"{year}-{(year + 1) % 100:02d}"),
        "match_date": native_calendar_date(espn_native["match_datetime_utc"]),
        "home_team": espn_native["home_source_team"], "away_team": espn_native["away_source_team"],
        "espn_match_id": espn_native["espn_match_id"].astype("string"),
        "espn_home_name_native": espn_native["home_source_team"],
        "espn_away_name_native": espn_native["away_source_team"],
        "espn_kickoff_utc": espn_native["match_datetime_utc"],
        "espn_home_goals": pd.to_numeric(espn_native["home_goals"], errors="coerce"),
        "espn_away_goals": pd.to_numeric(espn_native["away_goals"], errors="coerce"),
        "espn_status": espn_native["status"],
        "espn_completed": espn_native["status"].isin(["STATUS_FULL_TIME", "STATUS_FINAL", "STATUS_FINAL_AET", "STATUS_FINAL_PEN"]),
    })
    fpl_native = pd.read_parquet(ROOT / "data/processed/fpl_current/fixtures.parquet")
    fpl = pd.DataFrame({
        "season": fpl_native["season"], "match_date": native_calendar_date(fpl_native["kickoff_time"]),
        "home_team": fpl_native["home_team"], "away_team": fpl_native["away_team"],
        "fpl_fixture_id": pd.to_numeric(fpl_native["id"], errors="raise").astype("Int64"),
        "fpl_fixture_code": pd.to_numeric(fpl_native["code"], errors="raise").astype("Int64"),
        "fpl_home_team_id": pd.to_numeric(fpl_native["team_h"], errors="raise").astype("Int64"),
        "fpl_away_team_id": pd.to_numeric(fpl_native["team_a"], errors="raise").astype("Int64"),
        "fpl_home_name_native": fpl_native["home_team"],
        "fpl_away_name_native": fpl_native["away_team"],
        "fpl_kickoff_utc": fpl_native["kickoff_time"],
        "fpl_gameweek": pd.to_numeric(fpl_native["event"], errors="coerce").astype("Int64"),
        "fpl_home_goals": pd.to_numeric(fpl_native["team_h_score"], errors="coerce"),
        "fpl_away_goals": pd.to_numeric(fpl_native["team_a_score"], errors="coerce"),
        "fpl_completed": fpl_native["finished"],
    })
    frames = {source: decorate(frame, source) for source, frame in zip(SOURCES[:4], [fd, us, es, fpl])}
    statsbomb_path = ROOT / "data/processed/statsbomb/matches.parquet"
    if statsbomb_path.exists():
        sb_native = pd.read_parquet(statsbomb_path)
        home_names = sb_native["home_team"].map(lambda value: json.loads(value)["home_team_name"])
        away_names = sb_native["away_team"].map(lambda value: json.loads(value)["away_team_name"])
        sb = pd.DataFrame({
            "season": sb_native["season"], "match_date": native_calendar_date(sb_native["match_date"]),
            "home_team": home_names, "away_team": away_names,
            "statsbomb_match_id": pd.to_numeric(sb_native["match_id"], errors="raise").astype("Int64"),
            "statsbomb_home_name_native": home_names, "statsbomb_away_name_native": away_names,
            "statsbomb_native_season": sb_native["native_season"],
            "statsbomb_kickoff_native": sb_native["kick_off"],
            "statsbomb_home_goals": pd.to_numeric(sb_native["home_score"], errors="coerce"),
            "statsbomb_away_goals": pd.to_numeric(sb_native["away_score"], errors="coerce"),
            "statsbomb_match_status": sb_native["match_status"],
            "statsbomb_completed": sb_native["match_status"].eq("available") & sb_native[["home_score", "away_score"]].notna().all(axis=1),
        })
        frames["statsbomb"] = decorate(sb, "statsbomb")
    return frames


def json_records(frame):
    return json.loads(frame.to_json(orient="records"))


def main():
    frames = inputs()
    active_sources = list(frames)
    result = None
    for source, frame in frames.items():
        if result is None:
            result = frame
            continue
        merged = result.merge(frame, on="link_record_key", how="outer", validate="one_to_one", suffixes=("", "__right"))
        for key in KEY_FIELDS:
            both = merged[key].notna() & merged[key + "__right"].notna()
            assert (merged.loc[both, key] == merged.loc[both, key + "__right"]).all(), "Hash collision or incompatible exact key"
            merged[key] = merged[key].combine_first(merged[key + "__right"])
            merged = merged.drop(columns=key + "__right")
        result = merged
    comparison_columns = []
    overlap_report = {}
    for first, second in itertools.combinations(active_sources, 2):
        linked = result[ID_COLUMNS[first]].notna() & result[ID_COLUMNS[second]].notna()
        scores = [f"{source}_{side}_goals" for source in (first, second) for side in ("home", "away")]
        comparable = linked & result[scores].notna().all(axis=1)
        comparable &= result[f"{first}_completed"].fillna(False).astype(bool) & result[f"{second}_completed"].fillna(False).astype(bool)
        column = f"{first}_{second}_score_mismatch"
        result[column] = pd.Series(pd.NA, index=result.index, dtype="boolean")
        disagrees = (result[f"{first}_home_goals"] != result[f"{second}_home_goals"]) | (result[f"{first}_away_goals"] != result[f"{second}_away_goals"])
        result.loc[comparable, column] = disagrees.loc[comparable].astype(bool)
        comparison_columns.append(column)
        overlap_report[f"{first}__{second}"] = {
            "exact_linked_rows": int(linked.sum()), "completed_score_comparisons": int(comparable.sum()),
            "score_mismatches": int(result[column].fillna(False).sum()),
            "conflict_examples": json_records(result.loc[result[column].fillna(False), KEY_FIELDS +
                [ID_COLUMNS[first], ID_COLUMNS[second]] + scores].head(20)),
        }
    result["score_comparison_pairs"] = result[comparison_columns].notna().sum(axis=1)
    result["score_mismatch_any"] = result[comparison_columns].fillna(False).any(axis=1)
    for source in active_sources:
        result[f"has_{source}"] = result[ID_COLUMNS[source]].notna()
        result[f"{source}_exact_key_eligible"] = result[f"{source}_exact_key_eligible"].astype("boolean")
        result[f"{source}_completed"] = result[f"{source}_completed"].astype("boolean")
    result["source_count"] = result[[f"has_{source}" for source in active_sources]].sum(axis=1)
    # Do not relax the key if an identical home/away fixture has another date.
    date_groups = result.groupby(["season", "home_team", "away_team"], dropna=False)["match_date"].transform("nunique")
    result["has_same_fixture_different_source_date"] = date_groups.gt(1)
    kickoff_report = {}
    # These three providers expose UTC or a recorded England-local assumption.
    # Understat's undocumented native clock is retained without a UTC comparison.
    for first, second in itertools.combinations(["football_data", "espn", "fpl"], 2):
        a = pd.to_datetime(result[f"{first}_kickoff_utc"], utc=True, errors="coerce", format="mixed")
        b = pd.to_datetime(result[f"{second}_kickoff_utc"], utc=True, errors="coerce", format="mixed")
        comparable = a.notna() & b.notna()
        column = f"{first}_{second}_kickoff_mismatch"
        result[column] = pd.Series(pd.NA, index=result.index, dtype="boolean")
        result.loc[comparable, column] = a.loc[comparable].ne(b.loc[comparable])
        kickoff_report[f"{first}__{second}"] = {"compared_rows": int(comparable.sum()),
            "mismatches": int(result[column].fillna(False).sum()),
            "examples": json_records(result.loc[result[column].fillna(False), KEY_FIELDS +
                [f"{first}_kickoff_utc", f"{second}_kickoff_utc"]].head(20))}
    cohort = set(current_teams()["team"])
    assert (result["home_team"].isin(cohort) | result["away_team"].isin(cohort)).all(), "Unexpected noncohort match"
    assert not result["link_record_key"].duplicated().any()
    for source, frame in frames.items():
        assert result[ID_COLUMNS[source]].notna().sum() == len(frame), f"Lost {source} records"
    result = result.sort_values(KEY_FIELDS + ["link_record_key"]).reset_index(drop=True)
    result["requested_as_of_date"] = AS_OF_DATE
    # Sources may include unplayed future fixtures; retain them as schedule data.
    result["match_date_after_asof"] = result["match_date"].gt(AS_OF_DATE).fillna(False)
    output = ROOT / "data/processed/integrated/match_source_links"
    write_table(result, output)
    assert output.with_suffix(".parquet").exists(), "Parquet export failed"
    reread = pd.read_parquet(output.with_suffix(".parquet"))
    assert len(reread) == len(result)
    aggregations = {"link_rows": ("link_record_key", "size"),
                    "score_mismatch_rows": ("score_mismatch_any", "sum"),
                    "date_conflict_rows": ("has_same_fixture_different_source_date", "sum")}
    aggregations.update({f"{source}_rows": (f"has_{source}", "sum") for source in active_sources})
    by_season = result.groupby("season", as_index=False).agg(**aggregations)
    source_coverage = {}
    for source, frame in frames.items():
        selected = result.loc[result[f"has_{source}"]]
        source_coverage[source] = {"input_rows": len(frame), "retained_rows": len(selected),
            "rows_with_other_source": int(selected["source_count"].gt(1).sum()),
            "source_only_rows": int(selected["source_count"].eq(1).sum()),
            "unmatchable_keys": int((~frame[f"{source}_exact_key_eligible"]).sum()),
            "linked_to_football_data": int(selected["has_football_data"].sum())}
    report = {
        "status": "passed", "created_at_utc": now_utc(), "requested_as_of_date": AS_OF_DATE,
        "output_rows": len(result), "output_columns": len(result.columns),
        "join_method": "Exact season + normalized home team + normalized away team + printed source calendar date; full outer union",
        "key_uniqueness": "All source IDs unique and all complete per-source exact keys unique; outer merges validated one-to-one",
        "missing_key_policy": "Incomplete keys are source-specific unmatched records; null dates never join",
        "time_policy": "Provider native times retained separately. Understat and StatsBomb native clocks are not assigned an inferred timezone. Football-Data UTC uses the collector's documented Europe/London assumption.",
        "opponent_aliases": OPPONENT_ALIASES,
        "source_coverage": source_coverage, "coverage_by_season": json_records(by_season),
        "pairwise_score_validation": overlap_report, "pairwise_kickoff_validation": kickoff_report,
        "rows_with_any_score_mismatch": int(result["score_mismatch_any"].sum()),
        "rows_with_date_conflicts": int(result["has_same_fixture_different_source_date"].sum()),
        "date_conflict_examples": json_records(result.loc[result["has_same_fixture_different_source_date"],
            KEY_FIELDS + [ID_COLUMNS[source] for source in active_sources]].groupby("season", group_keys=False).head(10)),
        "future_schedule_rows": int(result["match_date_after_asof"].sum()),
        "notes": ["No score differences are silently overwritten; all native home/away scores remain separate.",
                  "A false score_mismatch_any with zero score_comparison_pairs means no score comparison was possible.",
                  "Football-Data sources cover E0 only in this link table; lower-tier histories remain in their original tables.",
                  "Current-club scope is unchanged; former clubs appear only as historical opponents.",
                  "Quotes are not time-aligned or executable solely because fixture IDs are linked."],
    }
    (ROOT / "metadata/match_link_validation.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"rows": len(result), "source_coverage": source_coverage,
                      "score_overlaps": {pair: {key: value for key, value in stats.items() if key != "conflict_examples"}
                                         for pair, stats in overlap_report.items()},
                      "score_mismatch_rows": report["rows_with_any_score_mismatch"],
                      "date_conflict_rows": report["rows_with_date_conflicts"]}, indent=2))


if __name__ == "__main__":
    main()
