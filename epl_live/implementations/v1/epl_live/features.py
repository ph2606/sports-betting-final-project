"""Construct current observation features without mutating historical studies."""
from __future__ import annotations

import csv
import io
import json
from pathlib import Path

import numpy as np
import pandas as pd

from epl_modeling import features as historical
from epl_modeling.fpl_reconciliation import reconcile_fpl_opponents, _supplemental_history


def read_table(snapshot, name):
    path = Path(snapshot) / "normalized" / (name + ".parquet")
    return pd.read_parquet(path) if path.exists() else pd.DataFrame()


def _current_league(path):
    content = path.read_bytes()
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = content.decode("cp1252")
    reader = csv.reader(io.StringIO(text))
    header = next(reader)
    frame = pd.DataFrame([dict(zip(header, row)) for row in reader if row and any(row)])
    if not {"Date", "HomeTeam", "AwayTeam", "FTR", "FTHG", "FTAG"}.issubset(frame):
        raise ValueError("Current Football-Data E0 response has an invalid schema")
    frame = frame.loc[frame.HomeTeam.notna() & frame.AwayTeam.notna()].copy()
    frame["match_date"] = pd.to_datetime(frame.Date, dayfirst=True, format="mixed", errors="coerce").dt.normalize()
    frame["season"], frame["season_start_year"] = "2026-27", 2026
    frame["home_team"], frame["away_team"] = frame.HomeTeam.map(historical._team), frame.AwayTeam.map(historical._team)
    frame["match_id"] = [historical._match_id("2026-27", home, away) for home, away in zip(frame.HomeTeam, frame.AwayTeam)]
    frame["result"] = frame.FTR.where(frame.FTR.isin(["H", "D", "A"]))
    frame["_completed"] = frame.result.notna() & pd.to_numeric(frame.FTHG, errors="coerce").notna() & pd.to_numeric(frame.FTAG, errors="coerce").notna()
    historical._unique(frame, ["match_id"], "current E0 observation")
    return frame


def build_live_features(data_root: Path, snapshot: Path, targets: pd.DataFrame):
    """Return numeric declared features plus actual contributing match-date audits."""
    snapshot, data_root = Path(snapshot), Path(data_root)
    manifest = json.loads((snapshot / "manifest.json").read_text(encoding="utf-8"))
    if not manifest.get("usable", False):
        raise ValueError("Snapshot failed membership/season/source validation")
    cohort = historical._table(data_root, "football_data/matches_current_cohort", required=True)
    league, _ = historical._read_league_files(data_root, cohort)
    current = _current_league(snapshot / "raw" / "football_data" / "E0.csv")
    observed = pd.Timestamp(manifest["snapshot_completed_at_utc"])
    current.loc[current.match_date.ge(observed.tz_convert("UTC").tz_localize(None).normalize()), "_completed"] = False
    older_current = league.loc[league.season.eq("2026-27") & league._completed]
    if not set(older_current.match_id).issubset(set(current.loc[current._completed, "match_id"])):
        raise ValueError("New E0 snapshot has less completed coverage than the saved historical snapshot")
    league = pd.concat([league.loc[~league.season.eq("2026-27")], current], ignore_index=True)
    observations = historical._observations(league)
    us, us_report = historical._understat_history(data_root, league)
    us = us.loc[~us.match_id.isin(current.match_id)].copy()
    live_us = read_table(snapshot, "understat_matches")
    identities = current[["match_id", "season", "match_date", "home_team", "away_team"]]
    if not live_us.empty:
        live_us["match_date"] = pd.to_datetime(live_us.match_date).dt.normalize()
        live_us = live_us.loc[live_us.completed.fillna(False)].copy()
        joined = live_us.merge(identities, on=["season", "match_date", "home_team", "away_team"], validate="one_to_one")
        sides = []
        for side, other in (("home", "away"), ("away", "home")):
            sides.append(pd.DataFrame({"match_id": joined.match_id, "team": joined[side + "_team"],
                                       "us_xg_for": pd.to_numeric(joined[side + "_xg"], errors="coerce"),
                                       "us_xg_against": pd.to_numeric(joined[other + "_xg"], errors="coerce")}))
        supplemented = pd.concat(sides, ignore_index=True)
        supplemented["us_xg_diff"] = supplemented.us_xg_for - supplemented.us_xg_against
        us = pd.concat([us, supplemented], ignore_index=True)
    historical._unique(us, ["match_id", "team"], "live xG fixture observation")
    repaired, _, repair_meta = reconcile_fpl_opponents(data_root)
    fpl, _ = _supplemental_history(repaired, league, repair_meta)
    fpl = fpl.loc[~fpl.match_id.isin(current.match_id)].copy()
    live_fpl = read_table(snapshot, "player_history")
    if not live_fpl.empty:
        live_fpl = live_fpl.loc[~pd.to_numeric(live_fpl.position_type, errors="coerce").eq(5)].copy()
        live_fpl["match_date"] = pd.to_datetime(live_fpl.kickoff_time.astype(str).str[:10], errors="coerce").dt.normalize()
        was_home = live_fpl.was_home.map({True: True, False: False, "True": True, "False": False})
        live_fpl["home_team"] = live_fpl.canonical_team.where(was_home.eq(True), live_fpl.opponent_name)
        live_fpl["away_team"] = live_fpl.opponent_name.where(was_home.eq(True), live_fpl.canonical_team)
        linked = live_fpl.merge(identities, on=["season", "match_date", "home_team", "away_team"], validate="many_to_one")
        for name in historical.FPL_FIELDS:
            linked[name] = pd.to_numeric(linked.get(name, pd.Series(np.nan, index=linked.index)), errors="coerce")
        aggregate = linked.groupby(["match_id", "canonical_team"])[list(historical.FPL_FIELDS)].sum(min_count=1).reset_index()
        aggregate = aggregate.rename(columns={"canonical_team": "team", **{name: "fpl_" + name for name in historical.FPL_FIELDS}})
        fpl = pd.concat([fpl, aggregate], ignore_index=True)
    historical._unique(fpl, ["match_id", "team"], "live FPL fixture observation")
    observations = observations.merge(us, on=["match_id", "team"], how="left", validate="one_to_one")
    observations = observations.merge(fpl, on=["match_id", "team"], how="left", validate="one_to_one")
    # Calendar dates without reliable result clocks cannot justify today's or
    # future completed observations, even if a provider marks them complete.
    observations.loc[observations.match_date.ge(observed.tz_convert("UTC").tz_localize(None).normalize()), "_completed"] = False
    for metric in historical.METRICS:
        observations[metric] = historical._number(observations, metric)
    queries = []
    for side in ("home", "away"):
        one = targets[["match_id", "season", "match_date"]].copy()
        one["team"], one["side"] = targets[side + "_team"], side
        queries.append(one)
    calculated = historical._team_features(observations, pd.concat(queries, ignore_index=True), set(league.season_start_year.unique()))
    frame = targets.copy()
    for side in ("home", "away"):
        part = calculated.loc[calculated.side.eq(side)].drop(columns=["season", "match_date", "team", "side"])
        names = {name: (f"audit_{side}_" + name.removeprefix("audit_") if name.startswith("audit_") else f"feat_{side}_" + name)
                 for name in part if name != "match_id"}
        frame = frame.merge(part.rename(columns=names), on="match_id", validate="one_to_one")
    diffs = {f"feat_diff_{period}_{metric}": frame[f"feat_home_{period}_{metric}"] - frame[f"feat_away_{period}_{metric}"]
             for period in ("std", "roll5", "roll10") for metric in historical.METRICS}
    diffs["feat_diff_rest_days"] = frame.feat_home_rest_days - frame.feat_away_rest_days
    frame = pd.concat([frame, pd.DataFrame(diffs)], axis=1)
    audit_dates = [name for name in frame if name.startswith("audit_") and name.endswith("_date")]
    for name in audit_dates:
        if (frame[name].notna() & frame[name].ge(frame.match_date)).any():
            raise ValueError("A target/same-date observation entered live features")
    fixtures = read_table(snapshot, "fixtures")
    clocks = pd.to_datetime(fixtures.kickoff_utc, utc=True, errors="coerce")
    overdue = fixtures.loc[clocks.lt(observed - pd.Timedelta(hours=6)) & ~fixtures.finished.fillna(False)]
    meta = {"latest_completed_e0_match_date": str(current.loc[current._completed, "match_date"].max().date()),
            "current_completed_e0_matches": int(current._completed.sum()), "current_xg_team_observations": int(us.match_id.isin(current.match_id).sum()),
            "current_fpl_team_observations": int(fpl.match_id.isin(current.match_id).sum()),
            "past_due_unfinished_fpl_fixtures": len(overdue), "source_publication_times_verified": False,
            "fpl_player_summaries_complete": bool(manifest.get("fpl_player_summaries_complete", False)),
            "feature_latest_date_violations": 0, "targets": len(frame), "historical_understat_audit": us_report}
    return frame, meta
