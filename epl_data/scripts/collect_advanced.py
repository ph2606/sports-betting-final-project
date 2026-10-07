"""Collect public Understat expected-goals history and ESPN teams/players.

Usage: python scripts/collect_advanced.py [--source all|understat|espn|understat-context]
Whole provider responses are retained; curated rows focus on the verified
2026-27 Premier League membership, including historical matches against
other opponents. No credentials or paid endpoints are used.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import hashlib
import json
import re
from datetime import datetime, timezone

import pandas as pd

from common import AS_OF_DATE, ROOT, Collector, canonical_team, current_teams, now_utc, write_table

CUTOFF = AS_OF_DATE + " 23:59:59"


def flatten(value, prefix=""):
    """Preserve every scalar field; encode arrays as explicit JSON columns."""
    out = {}
    for key, item in value.items():
        col = prefix + key
        if isinstance(item, dict):
            out.update(flatten(item, col + "__"))
        elif isinstance(item, list):
            out[col + "__json"] = json.dumps(item, ensure_ascii=False)
        else:
            out[col] = item
    return out


def load_previous(collector):
    path = ROOT / "metadata" / f"{collector.source}_manifest.json"
    if path.exists():
        try:
            return {r["path"]: r for r in json.loads(path.read_text(encoding="utf-8"))["requests"]
                    if r.get("status") in ("downloaded", "cached")}
        except Exception:
            pass
    return {}


def get_json(collector, prior, url, relative, *, params=None, headers=None):
    path = collector.raw / relative
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        key = str(path.relative_to(ROOT)).replace("\\", "/")
        record = dict(prior.get(key, {}))
        record.update(source=collector.source, url=url, parameters=params, path=key,
                      status="cached", sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                      bytes=path.stat().st_size, requested_as_of_date=AS_OF_DATE)
        if not record.get("retrieved_at_utc"):
            # A stopped first acquisition can leave saved responses before its
            # manifest checkpoint. Preserve a labelled file-time recovery.
            record["retrieved_at_utc"] = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()
            record["retrieval_timestamp_basis"] = "original_saved_response_file_mtime_recovered_after_interrupted_first_run"
        record.setdefault("source_published_at_utc", None)
        with collector.lock:
            collector.records.append(record)
        return data
    response = collector.fetch(url, relative, params=params, headers=headers)
    if response is None:
        return None
    try:
        return response.json()
    except Exception as error:
        with collector.lock:
            collector.records[-1]["parse_error"] = str(error)
        return None


def save_rows(collector, name, rows):
    frame = pd.DataFrame(rows)
    if frame.empty:
        columns = ["source", "requested_as_of_date"]
        if name == "player_injury_reports":
            columns = ["team", "espn_player_id", "player_name", *columns]
        frame = pd.DataFrame(columns=columns)
    if not frame.empty:
        numeric_names = {
            "games", "time", "goals", "own_goals", "shots", "xG", "xA", "assists", "key_passes",
            "yellow_cards", "red_cards", "yellow_card", "red_card", "npg", "npxG", "xGChain",
            "xGBuildup", "xGA", "npxGA", "deep", "deep_allowed", "scored", "missed", "xpts",
            "wins", "draws", "loses", "pts", "npxGD", "minute", "X", "Y", "h_goals", "a_goals",
            "ppda__att", "ppda__def", "ppda_allowed__att", "ppda_allowed__def", "weight", "height",
            "age", "attendance", "goals__h", "goals__a", "xG__h", "xG__a", "forecast__w",
            "forecast__d", "forecast__l"}
        for column in frame.columns:
            if column in numeric_names or column.startswith("stat__"):
                frame[column] = pd.to_numeric(frame[column], errors="coerce")
        frame["source"] = collector.source
        frame["requested_as_of_date"] = AS_OF_DATE
    write_table(frame, collector.out / name)
    print(f"{collector.source}/{name}: {len(frame):,} rows", flush=True)
    return len(frame)


def collect_understat():
    collector = Collector("understat")
    prior = load_previous(collector)
    headers = {"X-Requested-With": "XMLHttpRequest", "Referer": "https://understat.com/league/EPL/2026"}
    league = {}
    def season_request(year):
        data = get_json(collector, prior, f"https://understat.com/getLeagueData/EPL/{year}",
                        f"league/EPL_{year}.json", headers=headers)
        return year, data
    with cf.ThreadPoolExecutor(max_workers=4) as pool:
        for year, data in pool.map(season_request, range(2014, 2027)):
            if data:
                league[year] = data
    print(f"Understat league datasets: {len(league)} seasons", flush=True)
    team_rows, team_season_rows, match_rows, player_season_rows, jobs = [], [], [], [], {}
    for year, data in sorted(league.items()):
        season = f"{year}-{str(year+1)[-2:]}"
        match_lookup = {}
        for match in data.get("dates", []):
            home = canonical_team(match.get("h", {}).get("title"))
            away = canonical_team(match.get("a", {}).get("title"))
            if not (home or away):
                continue
            row = flatten(match)
            row.update(season=season, season_start_year=year,
                       home_team=home, away_team=away,
                       home_team_in_current_membership=home is not None,
                       away_team_in_current_membership=away is not None)
            match_rows.append(row)
            for side, opponent, team in [("h", match["a"], home), ("a", match["h"], away)]:
                if team:
                    match_lookup[(str(match[side]["id"]), match.get("datetime"), side)] = {
                        "match_id": str(match["id"]), "opponent_source_team": opponent.get("title"),
                        "opponent_team": canonical_team(opponent.get("title")),
                        "team": team, "season": season, "season_start_year": year,
                        "match_datetime_source": match.get("datetime")}
            if match.get("isResult") and str(match.get("datetime", "")) <= CUTOFF:
                jobs[str(match["id"])] = (year, match)
        for source_id, team in data.get("teams", {}).items():
            canonical = canonical_team(team.get("title"))
            if not canonical:
                continue
            history = []
            for item in team.get("history", []):
                if str(item.get("date", "")) > CUTOFF:
                    continue
                row = flatten(item)
                row.update(season=season, season_start_year=year, team=canonical,
                           source_team=team.get("title"), understat_team_id=source_id)
                row.update(match_lookup.get((str(source_id), item.get("date"), item.get("h_a")), {}))
                team_rows.append(row)
                history.append(item)
            sums = {name: sum(float(x.get(name, 0) or 0) for x in history) for name in
                    ("xG", "xGA", "npxG", "npxGA", "deep", "deep_allowed", "scored", "missed",
                     "xpts", "wins", "draws", "loses", "pts", "npxGD")}
            for metric in ("ppda", "ppda_allowed"):
                att = sum(float(x.get(metric, {}).get("att", 0)) for x in history)
                defense = sum(float(x.get(metric, {}).get("def", 0)) for x in history)
                sums.update({metric + "_att_total": att, metric + "_def_total": defense,
                             metric + "_ratio_from_totals": att / defense if defense else None})
            team_season_rows.append({"team": canonical, "understat_team_id": source_id,
                                     "source_team": team.get("title"), "season": season,
                                     "season_start_year": year, "matches": len(history), **sums})
        for player in data.get("players", []):
            source_teams = re.split(r"\s*,\s*", player.get("team_title", ""))
            focal = list(dict.fromkeys(canonical_team(x) for x in source_teams if canonical_team(x)))
            if not focal:
                continue
            row = flatten(player)
            row.update(season=season, season_start_year=year, team=focal[0] if len(focal)==1 else None,
                       current_membership_teams__json=json.dumps(focal),
                       source_totals_combine_multiple_clubs=len(source_teams)>1,
                       understat_player_id=player.get("id"))
            player_season_rows.append(row)
    counts = {
        "team_match_metrics": save_rows(collector, "team_match_metrics", team_rows),
        "team_season_metrics": save_rows(collector, "team_season_metrics", team_season_rows),
        "matches": save_rows(collector, "matches", match_rows),
        "player_season_metrics": save_rows(collector, "player_season_metrics", player_season_rows),
    }
    roster_rows, shot_rows = [], []
    completed, failures = 0, 0
    def match_request(job):
        match_id, (year, match) = job
        data = get_json(collector, prior, "https://understat.com/getMatchData/" + match_id,
                        f"matches/{match_id}.json", headers=headers)
        return match_id, year, match, data
    collector.finish({"state": "running", "table_rows": counts, "planned_completed_matches": len(jobs)})
    ordered_jobs = sorted(jobs.items(), key=lambda item: (item[1][0], item[1][1].get("datetime", "")), reverse=True)
    with cf.ThreadPoolExecutor(max_workers=12) as pool:
        for match_id, year, match, data in pool.map(match_request, ordered_jobs):
            completed += 1
            if not data:
                failures += 1
                continue
            for side in ("h", "a"):
                team = canonical_team(match.get(side, {}).get("title"))
                if not team:
                    continue
                opponent = match["a" if side=="h" else "h"]
                common = {"match_id": match_id, "season": f"{year}-{str(year+1)[-2:]}",
                          "season_start_year": year, "team": team,
                          "opponent_source_team": opponent.get("title"),
                          "opponent_team": canonical_team(opponent.get("title")),
                          "match_datetime_source": match.get("datetime")}
                roster = data.get("rosters", {}).get(side, {})
                entries = roster.values() if isinstance(roster, dict) else roster
                for player in entries:
                    row = flatten(player)
                    row.update(common, understat_player_id=player.get("player_id"))
                    roster_rows.append(row)
                for shot in data.get("shots", {}).get(side, []):
                    row = flatten(shot)
                    row.update(common, understat_player_id=shot.get("player_id"))
                    shot_rows.append(row)
            if completed % 250 == 0:
                print(f"Understat match details {completed:,}/{len(jobs):,}; failures={failures}", flush=True)
                collector.finish({"state": "running", "match_requests_completed": completed})
    counts["player_match_metrics"] = save_rows(collector, "player_match_metrics", roster_rows)
    counts["shots"] = save_rows(collector, "shots", shot_rows)
    # Displayed team xG and additive individual-shot/player xG are distinct
    # provider outputs. Preserve both, without altering supplied shot values.
    shot_frame = pd.DataFrame(shot_rows)
    roster_frame = pd.DataFrame(roster_rows)
    if not shot_frame.empty and not roster_frame.empty:
        shot_frame["xG"] = pd.to_numeric(shot_frame["xG"], errors="coerce")
        roster_frame["xG"] = pd.to_numeric(roster_frame["xG"], errors="coerce")
        comparison = pd.DataFrame(team_rows)[["match_id", "team", "season", "date", "opponent_source_team", "xG"]].rename(columns={"xG": "displayed_team_xG"})
        shot_sums = shot_frame.groupby(["match_id", "team"])["xG"].sum().rename("additive_shot_xG").reset_index()
        roster_sums = roster_frame.groupby(["match_id", "team"])["xG"].sum().rename("additive_player_xG").reset_index()
        comparison = comparison.merge(shot_sums, on=["match_id", "team"], how="left").merge(roster_sums, on=["match_id", "team"], how="left")
        zero_sides = comparison.displayed_team_xG.eq(0)
        comparison.loc[zero_sides, "additive_shot_xG"] = comparison.loc[zero_sides, "additive_shot_xG"].fillna(0)
        comparison["additive_shot_minus_displayed_team_xG"] = comparison.additive_shot_xG - comparison.displayed_team_xG
        comparison["additive_shot_minus_player_xG"] = comparison.additive_shot_xG - comparison.additive_player_xG
        comparison["team_and_additive_xG_differ_over_0_0001"] = comparison.additive_shot_minus_displayed_team_xG.abs().gt(0.0001)
        counts["xg_basis_comparison"] = save_rows(collector, "xg_basis_comparison", comparison.to_dict("records"))
    notes = {"season_start_years": sorted(league), "table_rows": counts,
             "completed_match_detail_requests": len(jobs), "failed_match_detail_requests": failures,
             "membership_scope": "2026-27 current clubs; excluded clubs appear only as match opponents or raw responses",
             "player_season_multi_club_totals": "Source aggregates across transfers. Flagged rows must not be attributed wholly to one club.",
             "datetime_timezone": "Provider datetime strings preserved as supplied; no timezone invented.",
             "forecast_field_caution": "forecast__w/d/l in completed match records are supplied retrospective outputs. Treat as post-match derived unless a verified provider publication timestamp before kickoff is separately obtained.",
             "future_matches": "Fixture rows retained; actual match/player/shot rows require isResult and date <= 2026-10-06.",
             "current_season_latest_observed_actual_match": max((x.get("datetime", "") for x in league.get(2026, {}).get("dates", []) if x.get("isResult")), default=None),
             "current_season_completed_matches": sum(bool(x.get("isResult")) for x in league.get(2026, {}).get("dates", [])),
             "retrieval_time_recovery": "Where an interrupted first acquisition had saved responses before its manifest checkpoint, timestamp recovered from original saved file mtime and explicitly labelled retrieval_timestamp_basis.",
             "xg_aggregation_caution": "Displayed team/league xG is not interchangeable with additive shot/player xG. Observed differences preserved in xg_basis_comparison. Possession/rebound adjustment is an inference directly supported by raw arithmetic for the largest-gap sample; no official complete aggregation methodology or possession IDs supplied, so all discrepancies are not individually reconciled.",
             "api_reference": "https://understat.com/js/league.min.js and https://understat.com/js/match.min.js expose getLeagueData and getMatchData."}
    collector.finish(notes)
    return notes


def stats_categories(value):
    """Flatten ESPN category stat arrays into name/value fields."""
    out = {}
    for category in value.get("splits", {}).get("categories", []):
        for stat in category.get("stats", []):
            out["stat__" + stat.get("name", "unknown")] = stat.get("value", stat.get("displayValue"))
    return out


def collect_understat_context():
    """Team context aggregates, in every acquired season where club played EPL."""
    collector = Collector("understat_context")
    prior = load_previous(collector)
    teams = pd.read_csv(ROOT / "data" / "processed" / "understat" / "team_season_metrics.csv")
    headers = {"X-Requested-With": "XMLHttpRequest", "Referer": "https://understat.com/league/EPL/2026"}
    def request(row):
        slug = row["source_team"].replace(" ", "_")
        year = int(row["season_start_year"])
        data = get_json(collector, prior, f"https://understat.com/getTeamData/{slug}/{year}",
                        f"teams/{slug}_{year}.json", headers=headers)
        return row, data
    rows, datasets = [], 0
    with cf.ThreadPoolExecutor(max_workers=4) as pool:
        for team, data in pool.map(request, teams.to_dict("records")):
            if not data:
                continue
            datasets += 1
            for category, entries in data.get("statistics", {}).items():
                for group, values in entries.items():
                    row = {"team": team["team"], "source_team": team["source_team"],
                           "understat_team_id": team["understat_team_id"], "season": team["season"],
                           "season_start_year": team["season_start_year"], "category": category,
                           "category_value": group, **flatten(values)}
                    rows.append(row)
    count = save_rows(collector, "team_context_metrics", rows)
    notes = {"team_season_datasets": datasets, "planned_team_season_datasets": len(teams),
             "table_rows": {"team_context_metrics": count},
             "categories": sorted(set(row["category"] for row in rows)),
             "scope": "Current2026-27club whitelist, all acquired EPL seasons2014-2026whereclubparticipated.",
             "aggregation_caution": "Context-group xG follows getTeamData provider statistics. Preserve this separately from displayed league/team xG; all are supplied outputs, not forced to one basis.",
             "availability_caution": "Historical final season context statistics require lagging; they were not all available before each historical match."}
    collector.finish(notes)
    return notes


def collect_espn():
    collector = Collector("espn")
    prior = load_previous(collector)
    base = "https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1"
    teams_json = get_json(collector, prior, base + "/teams", "teams.json", params={"limit": 1000})
    if not teams_json:
        collector.finish({"error": "Teams endpoint unavailable"})
        return {}
    teams = teams_json.get("sports", [{}])[0].get("leagues", [{}])[0].get("teams", [])
    teams = [entry["team"] for entry in teams if canonical_team(entry["team"].get("displayName"))]
    team_rows, profiles, player_stats, injuries, standings, event_jobs = [], [], [], [], [], {}
    schedule_rows = []
    def team_request(team):
        team_id = team["id"]
        roster = get_json(collector, prior, base+f"/teams/{team_id}/roster", f"rosters/{team_id}.json")
        details = get_json(collector, prior, base+f"/teams/{team_id}", f"team_profiles/{team_id}.json")
        schedules = {}
        for year in (2025, 2026):
            schedules[year] = get_json(collector, prior, base+f"/teams/{team_id}/schedule",
                                      f"schedules/{team_id}_{year}.json", params={"season": year})
        return team, roster, details, schedules
    with cf.ThreadPoolExecutor(max_workers=6) as pool:
        for team, roster, details, schedules in pool.map(team_request, teams):
            canonical = canonical_team(team.get("displayName"))
            row = flatten((details or {}).get("team", team))
            row.update(team=canonical, espn_team_id=team["id"])
            team_rows.append(row)
            if roster:
                for athlete in roster.get("athletes", []):
                    row = flatten(athlete)
                    row.update(team=canonical, espn_team_id=team["id"], espn_player_id=athlete.get("id"),
                               source_season_year=roster.get("season", {}).get("year"),
                               source_season_name=roster.get("season", {}).get("displayName"),
                               source_timestamp=roster.get("timestamp"))
                    profiles.append(row)
                    player_stats.append({"team": canonical, "espn_team_id": team["id"],
                                         "espn_player_id": athlete.get("id"), "player_name": athlete.get("fullName"),
                                         "source_season_year": roster.get("season", {}).get("year"),
                                         **stats_categories(athlete.get("statistics", {}))})
                    for injury in athlete.get("injuries", []):
                        injuries.append({"team": canonical, "espn_player_id": athlete.get("id"),
                                         "player_name": athlete.get("fullName"), **flatten(injury)})
            for year, schedule in schedules.items():
                for event in (schedule or {}).get("events", []):
                    competition = event.get("competitions", [{}])[0]
                    row = flatten(event)
                    row.update(team=canonical, espn_team_id=team["id"],
                               espn_match_id=event.get("id"), requested_source_season=year)
                    schedule_rows.append(row)
                    # Historical fallback endpoint may return a club's non-EPL season; inspect league explicitly.
                    competition_league = competition.get("league", {}).get("slug", "eng.1")
                    if competition.get("status", {}).get("type", {}).get("completed") and competition_league=="eng.1":
                        event_jobs[event["id"]] = (year, event)
    for year in (2025, 2026):
        value = get_json(collector, prior, "https://site.api.espn.com/apis/v2/sports/soccer/eng.1/standings",
                         f"standings/{year}.json", params={"season": year})
        for group in (value or {}).get("children", []):
            for entry in group.get("standings", {}).get("entries", []):
                canonical = canonical_team(entry.get("team", {}).get("displayName"))
                if not canonical:
                    continue
                row = {"team": canonical, "espn_team_id": entry["team"].get("id"),
                       "source_season_year": year, "source_group_name": group.get("name")}
                for stat in entry.get("stats", []):
                    row[stat.get("name", "unknown")] = stat.get("value", stat.get("displayValue"))
                standings.append(row)
    match_rows, match_team_rows, match_player_rows, event_rows, odds_rows = [], [], [], [], []
    def summary_request(job):
        match_id, (year, event) = job
        summary = get_json(collector, prior, base + "/summary", f"match_summaries/{match_id}.json",
                           params={"event": match_id})
        return match_id, year, event, summary
    successes = 0
    with cf.ThreadPoolExecutor(max_workers=6) as pool:
        for match_id, year, event, summary in pool.map(summary_request, event_jobs.items()):
            if not summary:
                continue
            successes += 1
            competition = summary.get("header", {}).get("competitions", [{}])[0]
            completed = competition.get("status", {}).get("type", {}).get("completed")
            event_date = event.get("date")
            if not completed or (event_date and event_date[:10] > AS_OF_DATE):
                continue
            common = {"espn_match_id": match_id, "requested_source_season": year, "match_datetime_utc": event_date}
            info = flatten(summary.get("gameInfo", {}))
            competitors = {x.get("homeAway"): x for x in competition.get("competitors", [])}
            match_identity = {}
            for side in ("home", "away"):
                competitor = competitors.get(side, {})
                source_team = competitor.get("team", {}).get("displayName")
                match_identity.update({side+"_team": canonical_team(source_team),
                                       side+"_source_team": source_team,
                                       side+"_espn_team_id": competitor.get("team", {}).get("id"),
                                       side+"_goals": pd.to_numeric(competitor.get("score"), errors="coerce")})
            match_rows.append({**common, **info, **match_identity, "name": event.get("name"),
                               "neutral_site": competition.get("neutralSite"),
                               "status": competition.get("status", {}).get("type", {}).get("name")})
            for team in summary.get("boxscore", {}).get("teams", []):
                canonical = canonical_team(team.get("team", {}).get("displayName"))
                if not canonical:
                    continue
                row = {**common, "team": canonical, "espn_team_id": team["team"].get("id"),
                       "home_away": team.get("homeAway")}
                opposing_side = "away" if team.get("homeAway")=="home" else "home"
                row.update(opponent_team=match_identity.get(opposing_side+"_team"),
                           opponent_source_team=match_identity.get(opposing_side+"_source_team"),
                           team_goals=match_identity.get(team.get("homeAway", "")+"_goals"),
                           opponent_goals=match_identity.get(opposing_side+"_goals"))
                for stat in team.get("statistics", []):
                    row[stat.get("name", "unknown")] = pd.to_numeric(stat.get("value", stat.get("displayValue")), errors="coerce")
                match_team_rows.append(row)
            for roster in summary.get("rosters", []):
                canonical = canonical_team(roster.get("team", {}).get("displayName"))
                if not canonical:
                    continue
                for athlete in roster.get("roster", []):
                    row = flatten(athlete)
                    row.update(common, team=canonical, espn_team_id=roster["team"].get("id"),
                               home_away=roster.get("homeAway"),
                               team_formation=roster.get("formation"),
                               espn_player_id=athlete.get("athlete", {}).get("id"))
                    # Provider stat list format is retained and also flattened when present.
                    for stat in athlete.get("stats", []):
                        if isinstance(stat, dict):
                            row["stat__"+stat.get("name", "unknown")] = stat.get("value", stat.get("displayValue"))
                    match_player_rows.append(row)
            for key_event in summary.get("keyEvents", []):
                canonical = canonical_team(key_event.get("team", {}).get("displayName"))
                if canonical:
                    event_rows.append({**common, **flatten(key_event), "team": canonical})
            for odds in summary.get("odds", []) + summary.get("pickcenter", []):
                odds_rows.append({**common, **flatten(odds)})
            if successes % 100 == 0:
                print(f"ESPN completed summaries {successes:,}/{len(event_jobs):,}", flush=True)
                collector.finish({"state": "running", "summary_requests_completed": successes})
    counts = {}
    for name, rows in [("team_profiles", team_rows), ("player_profiles", profiles),
                       ("player_season_stats", player_stats), ("player_injury_reports", injuries),
                       ("standings", standings), ("team_schedules", schedule_rows),
                       ("match_info", match_rows), ("team_match_stats", match_team_rows),
                       ("player_match_lineups", match_player_rows), ("match_key_events", event_rows),
                       ("match_odds_snapshots", odds_rows)]:
        counts[name] = save_rows(collector, name, rows)
    notes = {"table_rows": counts, "current_roster_clubs": len(teams),
             "summary_requests": len(event_jobs), "successful_summary_requests": successes,
             "schedule_seasons_requested": [2025, 2026],
             "current_season_latest_observed_actual_match": max((x.get("match_datetime_utc", "") for x in match_rows if x.get("requested_source_season")==2026), default=None),
             "current_season_completed_matches": sum(x.get("requested_source_season")==2026 for x in match_rows),
             "player_profile_field_coverage": {"total": len(profiles), "birth_date": sum(bool(x.get("dateOfBirth")) for x in profiles),
                                               "citizenship": sum(bool(x.get("citizenship")) for x in profiles),
                                               "height": sum(x.get("height") is not None for x in profiles),
                                               "weight": sum(x.get("weight") is not None for x in profiles),
                                               "position": sum(bool(x.get("position__displayName")) for x in profiles)},
             "freshness": "Live provider snapshots, with supplied timestamps and season labels. Historical schedules/matches reflect final state, not prediction-time availability.",
             "known_stale_coach_fields": "Roster endpoint includes stale legacy coach entries (e.g. Arsene Wenger for Arsenal). Raw field retained; coaches must not be used as current coaching data.",
             "units": "Player height is ESPN inches; weight is pounds. Provider display units are also retained.",
             "injury_coverage": "Only supplied roster injury arrays, not an authoritative injury registry. Empty reports are unknown coverage, not confirmation all fit.",
             "odds_limitation": "ESPN retrospective/current snapshots lack full exchange/order-book and time history; not usable as contemporaneous arbitrage proof.",
             "membership_scope": "Curated team/player rows only current 2026-27 clubs; excluded clubs may appear as opponents/raw payload context."}
    collector.finish(notes)
    return notes


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", choices=("all", "understat", "espn", "understat-context"), default="all")
    args = parser.parse_args()
    results = {}
    for source in ("understat", "espn", "understat_context"):
        prior_manifest = ROOT / "metadata" / f"{source}_manifest.json"
        if prior_manifest.exists():
            prior_notes = json.loads(prior_manifest.read_text(encoding="utf-8")).get("notes", {})
            if prior_notes and prior_notes.get("state") != "running":
                results[source] = prior_notes
    if args.source == "all":
        with cf.ThreadPoolExecutor(max_workers=2) as pool:
            future_understat = pool.submit(collect_understat)
            future_espn = pool.submit(collect_espn)
            results["understat"] = future_understat.result()
            results["espn"] = future_espn.result()
        results["understat_context"] = collect_understat_context()
    elif args.source == "understat":
        results["understat"] = collect_understat()
    elif args.source == "espn":
        results["espn"] = collect_espn()
    else:
        results["understat_context"] = collect_understat_context()
    lines = ["# Advanced football acquisition", "", f"Requested membership date: {AS_OF_DATE}.",
             "", "Curated rows focus on the 20 current 2026-27 Premier League clubs. Historical opponents",
             "are retained for match context. Raw league and match responses retain the source in full.", "",
             "Sources: [Understat](https://understat.com/league/EPL/2026),",
             "[ESPN Premier League](https://www.espn.com/soccer/league/_/name/eng.1),",
             "and the public JSON endpoints recorded in the source manifests.", "",
             "Understat uses getLeagueData and getMatchData JSON endpoints from its own frontend scripts;",
             "the old embedded JSON scraping method no longer applies. Team histories cover xG/xGA,",
             "non-penalty xG, PPDA numerator/denominator, deep completions and xPoints. Player season/match",
             "rows and individual shots retain positions, minutes, assists/xA, xGChain/xGBuildup, shot coordinates,",
             "situation, body part, last action, and assist-provider name.", "",
             "The separate getTeamData acquisition adds team context aggregates by situation, formation,",
             "game state, match-minute interval, shot zone, attack speed and shot result across acquired seasons.", "",
             "ESPN supplies current rosters and player demographics (birth date, citizenship, height, weight,",
             "position), season statistics, recent-season schedules/standings and completed match summaries",
             "with team event statistics, lineups, venue, attendance, officials and any supplied odds.", "",
             "Use source-specific IDs; player name matching across providers needs a reviewed crosswalk.",
             "Snapshot retrieval times are not field-level publication timestamps. Historical realized",
             "performance is appropriate for lagged features only. Current rosters cannot reconstruct",
             "historical squad membership. Player season summaries across transfers are explicitly flagged.", "",
             "Completed-match forecast__w/d/l fields are supplied retrospective outputs. They must be treated",
             "as post-match derived unless a provider publication time before kickoff is independently verified.", "",
             "ESPN legacy coach fields can be stale and should not be used for current coaches; empty",
             "injury arrays do not establish fitness. Transfer/valuation supplements are catalogued separately",
             "by other collectors. ESPN odds are snapshots without full event-time exchange/order-book history.", "",
             "Additional access probes are recorded in advanced_access_manifest.json: FBref returned",
             "HTTP403, Sofascore returned HTTP403, and Fotmob's older /api/leagues endpoint returned",
             "HTTP404. These sources contributed no team/player data. No authentication or paywall bypass was used.", "",
             "A stopped initial acquisition left a small number of cached responses before the first manifest",
             "checkpoint. Their acquisition timestamp was recovered from the saved response file's modification",
             "time and is explicitly labelled retrieval_timestamp_basis in the manifest.", "",
             "Understat displayed team/league xG and additive raw shot/player xG use different numerical",
             "bases. Their differences are preserved in xg_basis_comparison. Rebound/possession adjustment",
             "is an inference supported by the largest raw-source sample; full official aggregation methodology",
             "and possession IDs are unavailable, so the remaining differences are retained as an explicit",
             "limitation. Do not replace displayed team xG with raw shot sums or force per-shot allocations.", "",
             "Acquisition results:", "", "```json", json.dumps(results, indent=2), "```", ""]
    (ROOT / "metadata" / "advanced_notes.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
