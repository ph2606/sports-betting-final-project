"""Read-only exact reconciliation of saved FPL player-fixture opponent names.

No acquisition tables, first-run code, results, or workbooks are written.
Conflicting or ambiguous fixtures remain in the returned row audit and are
excluded from supplemental model aggregates. Identity matching never uses
scores, player performance, fuzzy names, or nearby calendar dates.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import types
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

from . import features as frozen


def _token(value):
    if pd.isna(value):
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        number = float(text)
        if np.isfinite(number) and number.is_integer():
            return str(int(number))
    except ValueError:
        pass
    return text


def _home(value):
    if pd.isna(value):
        return None
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    return {"true": True, "false": False, "1": True, "0": False}.get(str(value).strip().casefold())


def _name(value):
    if pd.isna(value) or not str(value).strip():
        return None
    return frozen._team(value)


def _day(value):
    if pd.isna(value):
        return None
    result = pd.to_datetime(str(value)[:10], format="%Y-%m-%d", errors="coerce")
    return None if pd.isna(result) else result.strftime("%Y-%m-%d")


class _Inputs:
    def __init__(self, root):
        self.root = Path(root)
        self.files = {}

    def read_bytes(self, path):
        data = path.read_bytes()
        self.files[str(path.relative_to(self.root)).replace("\\", "/")] = {
            "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}
        return data

    def csv(self, path, usecols=None):
        content = self.read_bytes(path)
        for encoding in ("utf-8-sig", "cp1252", "latin-1"):
            try:
                result = pd.read_csv(io.BytesIO(content), encoding=encoding, low_memory=False, usecols=usecols)
                self.files[str(path.relative_to(self.root)).replace("\\", "/")]["encoding"] = encoding
                return result
            except UnicodeDecodeError:
                continue
            except pd.errors.EmptyDataError:
                return pd.DataFrame()
        raise ValueError(f"Cannot decode saved CSV {path}")

    def table(self, relative):
        path = self.root / "data" / "processed" / relative
        parquet, csv_path = path.with_suffix(".parquet"), path.with_suffix(".csv")
        if parquet.exists():
            content = self.read_bytes(parquet)
            return pd.read_parquet(io.BytesIO(content))
        return self.csv(csv_path) if csv_path.exists() else pd.DataFrame()


def _league_identities(inputs):
    records = []
    for path in sorted((inputs.root / "data/raw/football_data").glob("*/E0.csv")):
        content = inputs.read_bytes(path)
        try:
            text = content.decode("utf-8-sig")
        except UnicodeDecodeError:
            text = content.decode("cp1252")
        reader = csv.reader(io.StringIO(text))
        header = [x.strip() for x in next(reader)]
        code = int(path.parent.name[:2])
        year = (1900 if code >= 80 else 2000) + code
        season = f"{year}-{(year+1)%100:02d}"
        for source_row, values in enumerate(reader, start=2):
            row = dict(zip(header, values))
            if not row.get("HomeTeam") or not row.get("AwayTeam"):
                continue
            date = pd.to_datetime(row.get("Date"), dayfirst=True, errors="coerce")
            if pd.isna(date):
                continue
            records.append({"season": season, "match_date": date.strftime("%Y-%m-%d"),
                            "home_team": _name(row["HomeTeam"]), "away_team": _name(row["AwayTeam"]),
                            "match_id": frozen._match_id(season, row["HomeTeam"], row["AwayTeam"]),
                            "source_row": source_row})
    if not records:
        raise FileNotFoundError("Saved full raw E0 fixtures are required for exact FPL reconciliation")
    candidates = defaultdict(list)
    for row in records:
        for is_home, own, opponent in ((True, row["home_team"], row["away_team"]),
                                       (False, row["away_team"], row["home_team"])):
            key = (row["season"], row["match_date"], own, is_home)
            candidates[key].append({**row, "opponent": opponent})
    return candidates, len(records)


def _combined(inputs):
    archive = inputs.table("fpl_archive/player_gameweeks")
    current = inputs.table("fpl_current/player_match_history")
    official_seasons = set(current.season.dropna()) if not current.empty else set()
    archive_rows = len(archive)
    if not archive.empty:
        archive = archive.copy()
        archive["reconciliation_source_table"] = "fpl_archive/player_gameweeks"
        archive["reconciliation_source_row"] = np.arange(len(archive))
        archive = archive.loc[~archive.season.isin(official_seasons)]
    if not current.empty:
        current = current.copy()
        current["reconciliation_source_table"] = "fpl_current/player_match_history"
        current["reconciliation_source_row"] = np.arange(len(current))
    pieces = [part for part in (archive, current) if not part.empty]
    if not pieces:
        raise FileNotFoundError("No saved FPL player-fixture history is available")
    players = pd.concat(pieces, ignore_index=True)
    manager = frozen._number(players, "position_type").eq(5)
    if "position_name" in players:
        manager |= players.position_name.astype("string").str.casefold().isin(["manager", "assistant manager"])
    counts = {"official_seasons_preferred": sorted(official_seasons),
              "archive_rows_superseded_by_official_season": archive_rows-len(archive),
              "assistant_manager_rows_excluded": int(manager.sum())}
    players = players.loc[~manager].reset_index(drop=True)
    required = ["season", "fixture", "element", "canonical_team", "was_home", "kickoff_time", "opponent_team"]
    for column in required:
        if column not in players:
            players[column] = pd.NA
    if "opponent_name" not in players:
        players["opponent_name"] = pd.NA
    if "team_at_fixture_id" not in players:
        players["team_at_fixture_id"] = pd.NA
    players["opponent_name_original"] = players.opponent_name.copy()
    players["reconciliation_row_id"] = (players.reconciliation_source_table + ":"
                                         + players.reconciliation_source_row.astype(str))
    return players, official_seasons, counts


def _independent_lookups(inputs, official_seasons):
    """Season IDs from raw teams or raw player team-code lookup, never player club assignment."""
    code_names, team_names, valid_ids = defaultdict(set), defaultdict(set), set()
    season_teams, player_codes = {}, {}
    for path in sorted((inputs.root / "data/raw/fpl_archive").glob("*/teams.csv")):
        frame = inputs.csv(path)
        season_teams[path.parent.name] = frame
        if {"code", "name"}.issubset(frame):
            for code, name in frame[["code", "name"]].itertuples(index=False, name=None):
                if _token(code) and _name(name):
                    code_names[_token(code)].add(_name(name))
    bootstrap = inputs.root / "data/raw/fpl_current/bootstrap-static.json"
    current_teams = pd.DataFrame()
    if bootstrap.exists():
        current_teams = pd.DataFrame(json.loads(inputs.read_bytes(bootstrap)).get("teams", []))
    if current_teams.empty:
        current_teams = inputs.table("fpl_current/teams")
    if {"code", "name"}.issubset(current_teams):
        for code, name in current_teams[["code", "name"]].itertuples(index=False, name=None):
            if _token(code) and _name(name):
                code_names[_token(code)].add(_name(name))
    for season in official_seasons:
        if not current_teams.empty:
            season_teams[season] = current_teams
    for season, frame in season_teams.items():
        if {"id", "name"}.issubset(frame):
            for team_id, name in frame[["id", "name"]].itertuples(index=False, name=None):
                key = (season, _token(team_id))
                valid_ids.add(key)
                if _name(name):
                    team_names[key].add(_name(name))
    for path in sorted((inputs.root / "data/raw/fpl_archive").glob("*/players_raw.csv")):
        season = path.parent.name
        if season in official_seasons:
            continue
        frame = inputs.csv(path, usecols=lambda value: value in {"team", "team_code"})
        if {"team", "team_code"}.issubset(frame):
            mapping = defaultdict(set)
            for team_id, code in frame[["team", "team_code"]].drop_duplicates().itertuples(index=False, name=None):
                if _token(team_id) and _token(code):
                    key = (season, _token(team_id))
                    valid_ids.add(key)
                    mapping[key].add(_token(code))
            player_codes.update(mapping)
    for key, codes in player_codes.items():
        if len(codes) == 1:
            team_names[key].update(code_names[next(iter(codes))])
        else:
            # Retain an explicit ambiguity marker; never select the first code.
            team_names[key].add("__AMBIGUOUS_TEAM_CODE__")
    return team_names, valid_ids, {
        "season_team_ids_observed": len(valid_ids),
        "season_team_ids_with_name_evidence": sum(bool(names) for names in team_names.values()),
        "ambiguous_named_team_ids": sum(len(names)>1 or "__AMBIGUOUS_TEAM_CODE__" in names for names in team_names.values()),
        "stable_team_code_name_bridge": "Raw season-local players_raw team/team_code pairs bridge to names in saved raw teams/bootstrap tables; no player's snapshot club assigns historical membership.",
    }


def _fixture_evidence(inputs, official_seasons):
    evidence = {}
    dates = defaultdict(set)
    def add(season, fixture, day, source, home_ids, away_ids):
        fixture = _token(fixture)
        if fixture is None:
            return
        key = (season, fixture, day, source)
        item = evidence.setdefault(key, {"home_ids": set(), "away_ids": set()})
        item["home_ids"].update(value for value in home_ids if value is not None)
        item["away_ids"].update(value for value in away_ids if value is not None)
        if day is not None:
            dates[(season, fixture, source)].add(day)
    for path in sorted((inputs.root / "data/raw/fpl_archive").glob("*/fixtures.csv")):
        season = path.parent.name
        if season in official_seasons:
            continue
        frame = inputs.csv(path, usecols=lambda value: value in {"id", "team_h", "team_a", "kickoff_time"})
        if {"id", "team_h", "team_a"}.issubset(frame):
            for row in frame.to_dict("records"):
                add(season, row["id"], _day(row.get("kickoff_time")), "raw_fixture_table",
                    [_token(row["team_h"])], [_token(row["team_a"])])
    for path in sorted((inputs.root / "data/raw/fpl_archive").glob("*/gws/merged_gw.csv")):
        season = path.parents[1].name
        if season in official_seasons:
            continue
        frame = inputs.csv(path, usecols=lambda value: value in {"fixture", "opponent_team", "was_home", "kickoff_time"})
        if not {"fixture", "opponent_team", "was_home", "kickoff_time"}.issubset(frame):
            continue
        frame["_fixture"] = frame.fixture.map(_token)
        frame["_date"] = frozen._date(frame.kickoff_time).dt.strftime("%Y-%m-%d")
        frame["_home"] = frame.was_home.map(_home)
        for (fixture, day, is_home), group in frame.groupby(["_fixture", "_date", "_home"], dropna=False, sort=False):
            if pd.isna(is_home):
                continue
            opponents = set(group.opponent_team.map(_token).dropna())
            # Opposition IDs supplied by away players identify the home ID.
            add(season, fixture, None if pd.isna(day) else day, "raw_same_fixture_players",
                [] if is_home else opponents, opponents if is_home else [])
    current = inputs.root / "data/raw/fpl_current/fixtures.json"
    if current.exists():
        records = json.loads(inputs.read_bytes(current))
    else:
        records = inputs.table("fpl_current/fixtures").to_dict("records")
    for season in official_seasons:
        for row in records:
            add(season, row.get("id"), _day(row.get("kickoff_time")), "official_fixture_table",
                [_token(row.get("team_h"))], [_token(row.get("team_a"))])
    return evidence, dates


def reconcile_fpl_opponents(data_root: Path) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Return preferred non-manager player rows, full row audit, and metadata.

    Only missing ``opponent_name`` values on fully validated exact fixtures are
    filled. Original values are retained in ``opponent_name_original``. Every
    returned row has ``reconciliation_eligible``; conflicted/unresolved fixtures
    remain present and must be excluded from model aggregates. A conflict in
    any player identity quarantines the whole FPL fixture, preventing partial
    team totals that silently omit inconsistent players.
    """
    inputs = _Inputs(data_root)
    players, official_seasons, counts = _combined(inputs)
    candidates, league_rows = _league_identities(inputs)
    team_names, valid_ids, lookup_report = _independent_lookups(inputs, official_seasons)
    fixture_evidence, evidence_dates = _fixture_evidence(inputs, official_seasons)
    players["_fixture"] = players.fixture.map(_token)
    players["_own_id"] = players.team_at_fixture_id.map(_token)
    players["_opponent_id"] = players.opponent_team.map(_token)
    players["_own_name"] = players.canonical_team.map(_name)
    players["_opponent_name"] = players.opponent_name.map(_name)
    players["_date"] = frozen._date(players.kickoff_time).dt.strftime("%Y-%m-%d")
    players["_is_home"] = players.was_home.map(_home)
    keys = ["season", "_fixture", "_own_id", "_opponent_id", "_own_name", "_opponent_name", "_date", "_is_home"]
    players["_identity"] = players.groupby(keys, dropna=False, sort=False).ngroup()
    identities = players.drop_duplicates("_identity")
    audited = []
    for row in identities[keys + ["_identity"]].to_dict("records"):
        season, fixture = row["season"], row["_fixture"]
        own, opponent = row["_own_name"], row["_opponent_name"]
        day, is_home = row["_date"], row["_is_home"]
        own_id, opponent_id = row["_own_id"], row["_opponent_id"]
        reasons = []
        required_missing = any(pd.isna(value) for value in (season, fixture, own, day, is_home, opponent_id))
        choices = [] if required_missing else candidates.get((season, day, own, is_home), [])
        candidate = choices[0] if len(choices)==1 else None
        if required_missing:
            reasons.append("missing_required_identity_field")
        elif not choices:
            reasons.append("no_exact_calendar_club_venue_candidate")
        elif len(choices)>1:
            reasons.append("ambiguous_exact_calendar_club_venue_candidates")
        known_name_check, own_lookup_check, opponent_lookup_check = None, None, None
        if candidate:
            if opponent is not None:
                known_name_check = opponent == candidate["opponent"]
                if not known_name_check:
                    reasons.append("known_opponent_name_conflict")
            for label, team_id, expected in (("own", own_id, own), ("opponent", opponent_id, candidate["opponent"])):
                names = team_names.get((season, team_id), set())
                season_has_ids = any(key[0]==season for key in valid_ids)
                passed = None
                if team_id is not None and season_has_ids and (season, team_id) not in valid_ids:
                    reasons.append(f"{label}_team_id_not_in_independent_season_lookup")
                    passed = False
                if names:
                    passed = len(names)==1 and expected in names and "__AMBIGUOUS_TEAM_CODE__" not in names
                    if not passed:
                        reasons.append(f"{label}_team_id_name_lookup_conflict")
                if label=="own":
                    own_lookup_check = passed
                else:
                    opponent_lookup_check = passed
            source_kinds = {key[2] for key in evidence_dates if key[:2]==(season, fixture)}
            for source in source_kinds:
                available_dates = evidence_dates[(season, fixture, source)]
                if day not in available_dates:
                    reasons.append(f"{source}_printed_date_conflict")
            for source in ("raw_fixture_table", "raw_same_fixture_players", "official_fixture_table"):
                evidence = fixture_evidence.get((season, fixture, day, source))
                if evidence is None:
                    evidence = fixture_evidence.get((season, fixture, None, source))
                if evidence is None:
                    continue
                expected_own = evidence["home_ids" if is_home else "away_ids"]
                expected_opponent = evidence["away_ids" if is_home else "home_ids"]
                for label, team_id, expected in (("own", own_id, expected_own), ("opponent", opponent_id, expected_opponent)):
                    if len(expected)>1:
                        reasons.append(f"{source}_{label}_id_ambiguous")
                    elif expected and team_id is not None and team_id not in expected:
                        reasons.append(f"{source}_{label}_id_conflict")
        audited.append({"_identity": row["_identity"], "season": season, "_fixture": fixture,
                        "_own_id": own_id, "_opponent_id": opponent_id,
                        "candidate_count": len(choices),
                        "candidate_opponent_name": None if candidate is None else candidate["opponent"],
                        "reconciliation_fd_match_id": None if candidate is None else candidate["match_id"],
                        "reconciliation_match_date": day,
                        "reconciliation_home_team": None if candidate is None else candidate["home_team"],
                        "reconciliation_away_team": None if candidate is None else candidate["away_team"],
                        "known_opponent_name_agrees": known_name_check, "independent_own_id_name_agrees": own_lookup_check,
                        "independent_opponent_id_name_agrees": opponent_lookup_check,
                        "reconciliation_reason": ";".join(sorted(set(reasons)))})
    identity_audit = pd.DataFrame(audited)
    # A season-local ID must not imply multiple clubs across candidate fixtures.
    for id_field, name_field, label in (("_own_id", "reconciliation_home_team", "own"),
                                       ("_opponent_id", "candidate_opponent_name", "opponent")):
        if label=="own":
            checks = identities[["_identity", "_own_name"]].merge(identity_audit, on="_identity", validate="one_to_one")
            name_field = "_own_name"
        else:
            checks = identity_audit
        present = checks[id_field].notna() & checks[name_field].notna()
        bad = checks.loc[present].groupby(["season", id_field])[name_field].nunique()
        bad_keys = set(bad[bad.gt(1)].index)
        for position, row in identity_audit.iterrows():
            if (row.season, row[id_field]) in bad_keys:
                reason = f"season_local_{label}_id_implies_multiple_clubs"
                identity_audit.at[position, "reconciliation_reason"] = ";".join(filter(None, [row.reconciliation_reason, reason]))
    fixture_groups = identity_audit.groupby(["season", "_fixture"], dropna=False)
    quarantine = set()
    for key, group in fixture_groups:
        if group.reconciliation_reason.ne("").any() or group.reconciliation_fd_match_id.dropna().nunique()!=1:
            quarantine.add(key)
    duplicates = players.duplicated(["season", "fixture", "element"], keep=False)
    duplicate_keys = set(zip(players.loc[duplicates, "season"], players.loc[duplicates, "_fixture"]))
    quarantine |= duplicate_keys
    # Two different FPL fixture IDs may not aggregate into the same FD match.
    linked_fixture_keys = identity_audit.loc[identity_audit.reconciliation_fd_match_id.notna(), ["season", "_fixture", "reconciliation_fd_match_id"]].drop_duplicates()
    duplicated_matches = linked_fixture_keys.groupby("reconciliation_fd_match_id").size().loc[lambda values: values.gt(1)].index
    reverse_conflicts = linked_fixture_keys[linked_fixture_keys.reconciliation_fd_match_id.isin(duplicated_matches)]
    reverse_conflict_keys = set(zip(reverse_conflicts.season, reverse_conflicts._fixture))
    quarantine |= reverse_conflict_keys
    for position, row in identity_audit.iterrows():
        key = (row.season, row._fixture)
        reasons = set(filter(None, str(row.reconciliation_reason).split(";")))
        if key in duplicate_keys:
            reasons.add("duplicate_player_fixture_key")
        if key in reverse_conflict_keys:
            reasons.add("multiple_fpl_fixture_ids_for_one_fd_match")
        if key in quarantine and not reasons:
            reasons.add("same_fixture_peer_identity_conflict_or_unresolved")
        identity_audit.at[position, "reconciliation_reason"] = ";".join(sorted(reasons))
    identity_audit["reconciliation_eligible"] = identity_audit.reconciliation_reason.eq("")
    audit_columns = [column for column in identity_audit if column not in {"season", "_fixture", "_own_id", "_opponent_id"}]
    repaired = players.merge(identity_audit[audit_columns], on="_identity", how="left", validate="many_to_one")
    missing_before = repaired._opponent_name.isna()
    fill = missing_before & repaired.reconciliation_eligible
    repaired.loc[fill, "opponent_name"] = repaired.loc[fill, "candidate_opponent_name"]
    repaired["reconciliation_status"] = np.where(repaired.reconciliation_eligible,
                                                np.where(missing_before, "repaired_missing_opponent", "validated_known_opponent"),
                                                "conflict_or_unresolved")
    audit = repaired[["reconciliation_row_id", "reconciliation_source_table", "reconciliation_source_row",
                      "season", "fixture", "element", "canonical_team", "was_home", "kickoff_time",
                      "team_at_fixture_id", "opponent_team", "opponent_name_original", "opponent_name",
                      "candidate_count", "candidate_opponent_name", "known_opponent_name_agrees",
                      "independent_own_id_name_agrees", "independent_opponent_id_name_agrees",
                      "reconciliation_fd_match_id", "reconciliation_match_date", "reconciliation_home_team",
                      "reconciliation_away_team", "reconciliation_eligible", "reconciliation_status", "reconciliation_reason"]].copy()
    season_report = {}
    for season, group in repaired.groupby("season", sort=True):
        season_report[season] = {"rows": len(group), "missing_opponent_before": int(group._opponent_name.isna().sum()),
                                 "repaired_missing_opponent": int(group.reconciliation_status.eq("repaired_missing_opponent").sum()),
                                 "eligible_rows": int(group.reconciliation_eligible.sum()),
                                 "conflict_or_unresolved_rows": int((~group.reconciliation_eligible).sum())}
    eligible = repaired[repaired.reconciliation_eligible]
    metadata = {**counts, "rows_returned": len(repaired), "audit_rows": len(audit), "full_raw_e0_match_rows": league_rows,
                "missing_opponent_before": int(missing_before.sum()), "missing_opponent_repaired": int(fill.sum()),
                "eligible_player_rows": len(eligible), "conflict_or_unresolved_rows": int((~repaired.reconciliation_eligible).sum()),
                "eligible_exact_fixtures": int(eligible[["season", "fixture"]].drop_duplicates().shape[0]),
                "eligible_exact_fixture_club_pairs": int(eligible[["season", "fixture", "canonical_team"]].drop_duplicates().shape[0]),
                "quarantined_fpl_fixtures": len(quarantine), "independent_lookup": lookup_report, "by_season": season_report,
                "input_files_read": inputs.files,
                "identity_method": "Exactly one saved E0 candidate for season + printed calendar date + actual club + home/away venue; all known names and available independent season-local IDs/source-fixture peers must agree.",
                "no_source_writes": True, "scores_or_performance_used_for_matching": False,
                "policy": "Any conflicting/unresolved identity quarantines its entire FPL fixture. Original player elements/fixture IDs/known opponent names are retained. No fuzzy or nearby-date fallback.",
                "timing_limit": "Identity repair does not establish historical field publication times or pre-match roster availability."}
    private = [column for column in repaired if column.startswith("_")]
    return repaired.drop(columns=private), audit, metadata


def _supplemental_history(repaired, league, reconciliation_metadata):
    good = repaired.loc[repaired.reconciliation_eligible].copy()
    identity = league[["match_id"] + frozen.KEYS]
    frozen._unique(identity, ["match_id"], "v2 FD league match")
    checked = good.merge(identity, left_on="reconciliation_fd_match_id", right_on="match_id", how="left",
                         validate="many_to_one", suffixes=("", "_fd"))
    if checked.match_id.isna().any():
        raise ValueError("Reconciled FPL fixture is absent from the feature builder's raw FD league")
    expected_date = pd.to_datetime(checked.reconciliation_match_date, errors="coerce")
    if not (checked.match_date.eq(expected_date) & checked.season.eq(checked.season_fd)
            & checked.home_team.eq(checked.reconciliation_home_team) & checked.away_team.eq(checked.reconciliation_away_team)).all():
        raise ValueError("Reconciled FPL identity changed between reconciliation and feature construction")
    checked["team"] = checked.canonical_team.map(_name)
    for field in frozen.FPL_FIELDS:
        checked[field] = frozen._number(checked, field)
    history = checked.groupby(["match_id", "team"])[list(frozen.FPL_FIELDS)].sum(min_count=1).reset_index()
    history = history.rename(columns={field: "fpl_"+field for field in frozen.FPL_FIELDS})
    frozen._unique(history, ["match_id", "team"], "reconciled FPL team fixture")
    report = {"available": True, "exact_linked_fixtures": int(history.match_id.nunique()),
              "unmatched_or_invalid_fixture_identities": reconciliation_metadata["quarantined_fpl_fixtures"],
              "manager_rows_excluded": reconciliation_metadata["assistant_manager_rows_excluded"],
              "official_current_seasons_preferred": reconciliation_metadata["official_seasons_preferred"],
              "repaired_missing_opponent_player_rows": reconciliation_metadata["missing_opponent_repaired"],
              "reconciliation_method": reconciliation_metadata["identity_method"]}
    return history, report


def build_reconciled_features(data_root: Path, reconciliation=None) -> tuple[pd.DataFrame, dict]:
    """Run the frozen builder with only its FPL history hook replaced in isolation.

    An isolated function-global namespace leaves the original module/hook
    untouched, including on exceptions. No temporary data roots or disk writes
    are necessary. Pass a previously returned reconciliation tuple to avoid
    repeating the read-only identity audit.
    """
    repaired, audit, report = reconciliation or reconcile_fpl_opponents(data_root)
    def supplemental_hook(_root, league):
        return _supplemental_history(repaired, league, report)
    namespace = dict(frozen.build_features.__globals__)
    namespace["_fpl_history"] = supplemental_hook
    isolated_builder = types.FunctionType(frozen.build_features.__code__, namespace,
                                           name="build_reconciled_features_impl", argdefs=frozen.build_features.__defaults__)
    frame, metadata = isolated_builder(Path(data_root))
    metadata["reconciliation"] = report
    metadata["feature_builder_variant"] = "v2_exact_reconciled_fpl"
    metadata["frozen_features_sha256"] = hashlib.sha256(Path(frozen.__file__).read_bytes()).hexdigest()
    metadata["original_fpl_hook_unmodified"] = frozen._fpl_history is frozen.build_features.__globals__["_fpl_history"]
    return frame, metadata
