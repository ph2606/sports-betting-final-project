"""Player-history predictors with exact fixture identity and strict date lags.

Raw season player tables supply only the position fallback (id/element_type).
Their current club, season totals, prices, availability and forecasts are never
read. Historical membership comes from native fixture sides and calendar links.
"""
from __future__ import annotations

from collections import defaultdict
import hashlib
import io
from pathlib import Path

import numpy as np
import pandas as pd

from epl_modeling.features import _match_id, _team


FORM_FIELDS = ("goals_scored", "assists", "total_points", "bps", "bonus", "influence",
               "creativity", "threat", "saves", "goals_conceded", "yellow_cards", "red_cards")
FORM_METRICS = FORM_FIELDS + ("active_players", "players60", "minutes")
POSITION_METRICS = ("minutes", "goal_involvements", "bps", "threat", "creativity", "saves")
POSITIONS = {1: "gk", 2: "def", 3: "mid", 4: "fwd"}
FORMATION = {1: 1, 2: 4, 3: 4, 4: 2}
XI_METRICS = ("xi_count", "xi_gk_count", "xi_def_count", "xi_mid_count", "xi_fwd_count",
              "xi_recent_minutes_share", "xi_recent_minutes_mean", "xi_points_per90", "xi_bps_per90",
              "xi_goal_involvements_per90", "xi_threat_per90", "xi_creativity_per90",
              "xi_influence_per90", "xi_saves_per90")
CONTINUITY_METRICS = ("pool_count", "minute_hhi", "retained_players_fraction", "last60_count")
FORM_NAMES = tuple(f"roll{window}_{field}" for window in (5, 10) for field in FORM_METRICS)
SQUAD_NAMES = tuple(f"pos5_{position}_{field}" for position in POSITIONS.values() for field in POSITION_METRICS) + XI_METRICS + CONTINUITY_METRICS
COVERAGE_FEATURES = [f"feat_player_{side}_{name}" for side in ("home", "away")
                     for name in ("observed_matches5", "observed_matches10", "history_missing")]
PLAYER_FORM_FEATURES = [f"feat_player_{side}_{name}" for side in ("home", "away", "diff")
                        for name in FORM_NAMES] + COVERAGE_FEATURES
PLAYER_SQUAD_FEATURES = PLAYER_FORM_FEATURES + [f"feat_player_{side}_{name}"
                                               for side in ("home", "away", "diff") for name in SQUAD_NAMES]
TARGET_COLUMNS = ["match_id", "season", "match_date", "home_team", "away_team"]
HISTORY_COLUMNS = ["season", "element", "fixture", "match_id", "match_date", "team", "position_type",
                   "position_source", "minutes", *FORM_FIELDS, "source_path"]
FIXTURE_AUDIT_COLUMNS = ["season", "fixture", "source_path", "match_date", "home_id", "away_id",
                         "home_team", "away_team", "match_id", "eligible", "reason", "source_rows"]
XI_AUDIT_COLUMNS = ["match_id", "match_date", "season", "team", "side", "element", "player_key",
                    "slot_position", "selection_rank", "prior_minutes5", "prior_observed_rows5",
                    "last_positive_appearance_date", "latest_position_source_date", "latest_source_date",
                    "position_source"]


def _token(value):
    if pd.isna(value):
        return None
    text = str(value).strip()
    try:
        numeric = float(text)
        if np.isfinite(numeric) and numeric.is_integer():
            return str(int(numeric))
    except (ValueError, TypeError):
        pass
    return text or None


def _bool(value):
    if pd.isna(value):
        return None
    return {"true": True, "false": False, "1": True, "0": False}.get(str(value).strip().casefold())


def _role(value):
    text = str(value).strip().casefold() if pd.notna(value) else ""
    named = {"gk": 1, "gkp": 1, "goalkeeper": 1, "def": 2, "defender": 2,
             "mid": 3, "midfielder": 3, "fwd": 4, "forward": 4, "am": 5,
             "manager": 5, "assistant manager": 5}
    if text in named:
        return named[text]
    token = _token(value)
    return int(token) if token in {"1", "2", "3", "4", "5"} else np.nan


def _days(values):
    return pd.to_datetime(values.astype("string").str[:10], format="%Y-%m-%d", errors="coerce")


class _Reader:
    def __init__(self):
        self.paths: list[Path] = []
        self.provenance = {}

    def data(self, path: Path, *, columns=None):
        path = path.resolve()
        raw = path.read_bytes()
        if path not in self.paths:
            self.paths.append(path)
        item = {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}
        if path.suffix == ".parquet":
            result = pd.read_parquet(io.BytesIO(raw), columns=columns)
        else:
            for encoding in ("utf-8-sig", "cp1252", "latin-1"):
                try:
                    result = pd.read_csv(io.BytesIO(raw), encoding=encoding, low_memory=False,
                                         usecols=(lambda name: name in columns) if columns else None)
                    item["encoding"] = encoding
                    break
                except UnicodeDecodeError:
                    continue
        self.provenance[str(path)] = item
        return result


def _calendar(reader: _Reader, root: Path):
    rows = []
    for path in sorted((root / "data/raw/football_data").glob("*/E0.csv")):
        code = int(path.parent.name[:2])
        year = (1900 if code >= 80 else 2000) + code
        if not 2016 <= year <= 2025:
            continue
        season = f"{year}-{(year + 1) % 100:02d}"
        frame = reader.data(path, columns=["Date", "HomeTeam", "AwayTeam", "FTR"])
        dates = pd.to_datetime(frame.Date, format="mixed", dayfirst=True, errors="coerce")
        for i, row in frame.iterrows():
            if pd.isna(dates.iloc[i]) or pd.isna(row.HomeTeam) or pd.isna(row.AwayTeam):
                continue
            if "FTR" in frame and row.FTR not in ("H", "D", "A"):
                continue
            rows.append({"season": season, "match_id": _match_id(season, row.HomeTeam, row.AwayTeam),
                         "match_date": dates.iloc[i].normalize(), "home_team": _team(row.HomeTeam),
                         "away_team": _team(row.AwayTeam)})
    result = pd.DataFrame(rows, columns=TARGET_COLUMNS)
    if result.empty:
        raise FileNotFoundError("Saved historical full-league E0 files are required")
    if result.match_id.duplicated().any():
        raise ValueError("Duplicate native Football-Data fixture IDs")
    return result


def _resolve_names(fixtures, calendar, anchors):
    """Calendar signatures and unique known-side joins, without scores or players."""
    names = dict(anchors)
    by_date = {day: group for day, group in calendar.groupby("match_date", sort=False)}
    possibilities = defaultdict(list)
    for row in fixtures:
        candidates = by_date.get(row["match_date"])
        if candidates is None:
            continue
        possibilities[row["home_id"]].append(set(candidates.home_team))
        possibilities[row["away_id"]].append(set(candidates.away_team))
    for team_id, groups in possibilities.items():
        common = set.intersection(*groups)
        if team_id not in names and len(common) == 1:
            names[team_id] = next(iter(common))
    changed = True
    while changed:
        changed = False
        for row in fixtures:
            candidates = by_date.get(row["match_date"])
            if candidates is None:
                continue
            home, away = names.get(row["home_id"]), names.get(row["away_id"])
            if home is not None:
                candidates = candidates.loc[candidates.home_team.eq(home)]
            if away is not None:
                candidates = candidates.loc[candidates.away_team.eq(away)]
            if len(candidates) != 1:
                continue
            selected = candidates.iloc[0]
            for team_id, value in ((row["home_id"], selected.home_team), (row["away_id"], selected.away_team)):
                if team_id not in names and value not in names.values():
                    names[team_id] = value
                    changed = True
    duplicates = {name for name in names.values() if list(names.values()).count(name) > 1}
    return {key: value for key, value in names.items() if value not in duplicates}


def _archive_season(reader, directory, calendar):
    season = directory.name
    path = directory / "gws/merged_gw.csv"
    wanted = ["element", "fixture", "kickoff_time", "opponent_team", "was_home", "position", "minutes", *FORM_FIELDS]
    rows = reader.data(path, columns=wanted)
    raw_count = len(rows)
    rows["_day"] = _days(rows.kickoff_time)
    rows["_home"] = rows.was_home.map(_bool)
    rows["fixture"] = rows.fixture.map(_token)
    rows["element"] = rows.element.map(_token)
    rows["_opponent"] = rows.opponent_team.map(_token)
    for field in ("minutes", *FORM_FIELDS):
        rows[field] = pd.to_numeric(rows[field], errors="coerce") if field in rows else np.nan
    # Static season role is a fallback only. No snapshot club or totals are read.
    role_path = directory / "players_raw.csv"
    fallback = {}
    if role_path.exists():
        role_rows = reader.data(role_path, columns=["id", "element_type"])
        if {"id", "element_type"}.issubset(role_rows):
            pairs = role_rows.assign(_id=role_rows.id.map(_token), _role=role_rows.element_type.map(_role))
            if pairs.groupby("_id")._role.nunique().gt(1).any():
                raise ValueError(f"Conflicting season position fallback for {season}")
            fallback = pairs.drop_duplicates("_id").set_index("_id")._role.to_dict()
    native_role = rows.position.map(_role) if "position" in rows else pd.Series(np.nan, index=rows.index)
    rows["position_type"] = native_role.fillna(rows.element.map(fallback))
    rows["position_source"] = np.where(native_role.notna(), "native_historical_gw_position",
                                       np.where(rows.position_type.notna(), "season_snapshot_position_fallback", "unknown"))
    managers = rows.position_type.eq(5)
    rows = rows.loc[~managers].copy()
    before_duplicate = len(rows)
    rows = rows.drop_duplicates(["fixture", "element", "_day", "_home", "_opponent", "position_type", "minutes", *FORM_FIELDS])
    exact_duplicates = before_duplicate - len(rows)
    all_zero = rows.groupby(["fixture", "_day"], dropna=False).minutes.transform("sum").le(0)
    placeholders = int(all_zero.sum())
    rows = rows.loc[~all_zero].copy()
    anchors = {}
    team_path = directory / "teams.csv"
    if team_path.exists():
        teams = reader.data(team_path, columns=["id", "name"])
        if {"id", "name"}.issubset(teams):
            if teams.groupby("id")["name"].nunique().gt(1).any():
                raise ValueError(f"Conflicting native season team IDs for {season}")
            anchors = {_token(row.id): _team(row["name"]) for _, row in teams.iterrows()}
    fixture_path = directory / "fixtures.csv"
    native_fixtures = {}
    if fixture_path.exists():
        native = reader.data(fixture_path, columns=["id", "team_h", "team_a", "kickoff_time"])
        if native.id.duplicated().any():
            raise ValueError(f"Duplicate native fixture IDs for {season}")
        for _, row in native.iterrows():
            native_fixtures[_token(row.id)] = (_token(row.team_h), _token(row.team_a),
                                               _days(pd.Series([row.kickoff_time])).iloc[0])
    identities = []
    grouped = rows.groupby("fixture", sort=False, dropna=False)
    for fixture, group in grouped:
        reasons = []
        dates = group._day.dropna().unique()
        home_ids = set(group.loc[group._home.eq(False), "_opponent"].dropna())
        away_ids = set(group.loc[group._home.eq(True), "_opponent"].dropna())
        if len(dates) != 1:
            reasons.append("conflicting_or_missing_fixture_dates")
        if len(home_ids) != 1 or len(away_ids) != 1 or home_ids == away_ids:
            reasons.append("ambiguous_native_fixture_side_ids")
        if group.element.isna().any() or group._home.isna().any() or group._opponent.isna().any() or group.minutes.isna().any():
            reasons.append("missing_player_fixture_identity_or_minutes")
        if group.element.duplicated().any():
            reasons.append("conflicting_duplicate_player_fixture")
        day = pd.Timestamp(dates[0]) if len(dates) == 1 else pd.NaT
        home_id = next(iter(home_ids)) if len(home_ids) == 1 else None
        away_id = next(iter(away_ids)) if len(away_ids) == 1 else None
        if fixture in native_fixtures:
            nh, na, nd = native_fixtures[fixture]
            if (home_id, away_id) != (nh, na) or pd.isna(nd) or pd.isna(day) or nd != day:
                reasons.append("raw_fixture_table_identity_conflict")
        identities.append({"season": season, "fixture": fixture, "match_date": day,
                           "home_id": home_id, "away_id": away_id, "reason": ";".join(reasons),
                           "source_path": str(path.resolve()), "source_rows": len(group)})
    names = _resolve_names([item for item in identities if not item["reason"]], calendar, anchors)
    by_date = {day: group for day, group in calendar.groupby("match_date", sort=False)}
    accepted = {}
    for item in identities:
        home, away = names.get(item["home_id"]), names.get(item["away_id"])
        candidates = by_date.get(item["match_date"], calendar.iloc[:0])
        candidates = candidates.loc[candidates.home_team.eq(home) & candidates.away_team.eq(away)]
        reasons = list(filter(None, item["reason"].split(";")))
        if len(candidates) != 1:
            reasons.append("no_unique_exact_calendar_club_fixture")
        item.update(home_team=home, away_team=away, eligible=not reasons,
                    match_id=candidates.match_id.iloc[0] if len(candidates) == 1 else None,
                    reason=";".join(sorted(set(reasons))))
        if item["eligible"]:
            accepted[item["fixture"]] = item
    rows = rows.loc[rows.fixture.isin(accepted)].copy()
    rows["season"] = season
    rows["match_id"] = rows.fixture.map(lambda value: accepted[value]["match_id"])
    rows["match_date"] = rows._day
    rows["team"] = [accepted[fixture]["home_team" if is_home else "away_team"]
                    for fixture, is_home in zip(rows.fixture, rows._home)]
    rows["source_path"] = str(path.resolve())
    metadata = {"raw_player_rows": raw_count, "manager_rows_excluded": int(managers.sum()),
                "identical_rows_removed": exact_duplicates, "zero_minute_postponed_placeholder_rows_removed": placeholders,
                "eligible_player_rows": len(rows), "eligible_fixtures": len(accepted),
                "quarantined_fixtures": sum(not item["eligible"] for item in identities),
                "clubs_with_player_history": int(rows.team.nunique()), "calendar_named_season_ids": len(names)}
    return rows[HISTORY_COLUMNS], identities, metadata


def _live_history(reader, snapshot):
    history_path = snapshot / "normalized/player_history.parquet"
    fixture_path = snapshot / "normalized/fixtures.parquet"
    raw = reader.data(history_path)
    fixtures = reader.data(fixture_path)
    if fixtures.fpl_fixture_id.duplicated().any() or fixtures.match_id.duplicated().any():
        raise ValueError("Live snapshot contains duplicate native fixture IDs")
    fixtures = fixtures.copy()
    fixtures["_fixture"] = fixtures.fpl_fixture_id.map(_token)
    fixtures["match_date"] = _days(fixtures.match_date)
    native = fixtures.set_index("_fixture")
    raw["fixture"] = raw.fixture.map(_token)
    raw["element"] = raw.element.map(_token)
    raw["match_date"] = _days(raw.kickoff_time)
    raw["position_type"] = raw.position_type.map(_role)
    raw["position_source"] = "live_history_snapshot_position_proxy"
    raw["team"] = raw.canonical_team.map(_team)
    own_home = raw.was_home.map(_bool)
    mapped_home = raw.fixture.map(native.home_team).map(_team)
    mapped_away = raw.fixture.map(native.away_team).map(_team)
    valid = raw.history_identity_valid.eq(True) & raw.fixture.isin(native.index)
    valid &= raw.fixture.map(native.finished).eq(True) & raw.season.eq("2026-27")
    valid &= raw.season.eq(raw.fixture.map(native.season))
    valid &= raw.match_date.eq(raw.fixture.map(native.match_date)) & own_home.notna()
    valid &= raw.team.eq(mapped_home.where(own_home.eq(True), mapped_away))
    valid &= raw.opponent_name.map(_team).eq(mapped_away.where(own_home.eq(True), mapped_home))
    valid &= raw.position_type.ne(5)
    duplicate_fixtures = set(raw.loc[raw.duplicated(["fixture", "element"], keep=False), "fixture"])
    bad_fixtures = set(raw.loc[~valid, "fixture"]) | duplicate_fixtures
    raw = raw.loc[valid & ~raw.fixture.isin(bad_fixtures)].copy()
    raw["match_id"] = raw.fixture.map(native.match_id)
    raw["source_path"] = str(history_path.resolve())
    for field in ("minutes", *FORM_FIELDS):
        raw[field] = pd.to_numeric(raw[field], errors="coerce") if field in raw else np.nan
    if raw.minutes.isna().any():
        raise ValueError("Missing live player-history minutes")
    audit = []
    for fixture, group in raw.groupby("fixture", sort=False):
        identity = native.loc[fixture]
        audit.append({"season": "2026-27", "fixture": fixture, "source_path": str(history_path.resolve()),
                      "match_date": identity.match_date, "home_id": None, "away_id": None,
                      "home_team": identity.home_team, "away_team": identity.away_team,
                      "match_id": identity.match_id, "eligible": True, "reason": "", "source_rows": len(group)})
    for fixture in sorted(bad_fixtures, key=str):
        audit.append({"season": "2026-27", "fixture": fixture, "source_path": str(history_path.resolve()),
                      "eligible": False, "reason": "live_fixture_identity_conflict_or_duplicate"})
    calendar = fixtures.loc[fixtures.finished.eq(True), TARGET_COLUMNS].copy()
    metadata = {"eligible_player_rows": len(raw), "eligible_fixtures": int(raw.fixture.nunique()),
                "quarantined_fixtures": len(bad_fixtures), "clubs_with_player_history": int(raw.team.nunique()),
                "position_proxy": "Position labels supplied on history rows by the captured current snapshot; no roster-club/availability fields are used."}
    return raw[HISTORY_COLUMNS], audit, calendar, metadata


def load_player_history(data_root: Path, *, live_snapshot: Path | None = None):
    """Return whole-league historical rows, JSON metadata and exact source paths.

    ``players.attrs`` carries a JSON-safe complete fixture calendar and the
    fixture audit to the feature builder. Preserve these attrs when subsetting
    the returned frame. Only explicitly supplied live-snapshot rows can extend
    history into 2026--27; the saved current roster is never consulted.
    """
    root = Path(data_root).resolve()
    if not (root / "data/raw").is_dir() and (root / "epl_data/data/raw").is_dir():
        root = root / "epl_data"
    reader = _Reader()
    calendar = _calendar(reader, root)
    pieces, audit_rows, seasons = [], [], {}
    for directory in sorted((root / "data/raw/fpl_archive").iterdir()):
        if not directory.is_dir() or not (directory / "gws/merged_gw.csv").exists():
            continue
        if not 2016 <= int(directory.name[:4]) <= 2025:
            continue
        subset = calendar.loc[calendar.season.eq(directory.name)]
        rows, audit, metadata = _archive_season(reader, directory, subset)
        pieces.append(rows)
        audit_rows.extend(audit)
        seasons[directory.name] = metadata
    if live_snapshot is not None:
        rows, audit, live_calendar, metadata = _live_history(reader, Path(live_snapshot).resolve())
        pieces.append(rows)
        audit_rows.extend(audit)
        calendar = pd.concat([calendar, live_calendar], ignore_index=True)
        seasons["2026-27"] = metadata
    if not pieces:
        raise FileNotFoundError("No saved historical FPL merged gameweek files found")
    players = pd.concat(pieces, ignore_index=True)
    if players.duplicated(["season", "match_id", "element"]).any():
        raise ValueError("Duplicate reconciled player-fixture identity")
    if players.minutes.isna().any() or players.minutes.lt(0).any() or players.minutes.gt(120).any():
        raise ValueError("Invalid historical player minutes")
    players = players.sort_values(["season", "match_date", "match_id", "element"], kind="stable").reset_index(drop=True)
    # Cross-club same-date positive appearances are impossible identity evidence.
    positive = players.loc[players.minutes.gt(0)]
    conflicts = positive.groupby(["season", "element", "match_date"]).team.nunique().gt(1)
    if conflicts.any():
        raise ValueError("A player has positive minutes for multiple clubs on one calendar date")
    calendar_records = calendar.assign(match_date=calendar.match_date.dt.strftime("%Y-%m-%d")).to_dict("records")
    audit_frame = pd.DataFrame(audit_rows).reindex(columns=FIXTURE_AUDIT_COLUMNS)
    audit_frame["match_date"] = pd.to_datetime(audit_frame.match_date).dt.strftime("%Y-%m-%d")
    players.attrs["fixture_calendar"] = calendar_records
    players.attrs["fixture_reconciliation"] = audit_frame.where(audit_frame.notna(), None).to_dict("records")
    metadata = {"player_rows": len(players), "seasons": seasons, "position_sources": players.position_source.value_counts().to_dict(),
                "fixture_calendar_rows": len(calendar), "fixture_audit_rows": len(audit_frame),
                "input_files_read": reader.provenance,
                "membership_method": "Native fixture-side opponent IDs, independent raw fixture table where present, and exact E0 calendar/venue identity; no player's snapshot club is read.",
                "early_missing_team_names_method": "Unique intersection of full-season calendar/venue signatures and unique known-side fixture propagation; unresolved identities quarantined, no scores/fuzzy dates.",
                "position_method": "Historical GW position preferred; id/element_type season snapshot fallback only. Current-snapshot role labels remain explicit proxies with unverified historical publication time.",
                "player_identity": "season + element; no cross-season ID/name matching",
                "live_snapshot": str(Path(live_snapshot).resolve()) if live_snapshot is not None else None,
                "no_source_writes": True}
    return players, metadata, reader.paths


def _safe_mean(values):
    values = np.asarray(values, dtype=float)
    if not len(values):
        return np.full(len(FORM_METRICS), np.nan)
    counts = np.isfinite(values).sum(axis=0)
    return np.divide(np.nansum(values, axis=0), counts,
                     out=np.full(values.shape[1], np.nan), where=counts > 0)


def _max_date(values):
    valid = [pd.Timestamp(value) for value in values if pd.notna(value)]
    return max(valid) if valid else pd.NaT


def build_player_features(players: pd.DataFrame, target_matches: pd.DataFrame):
    """Return feature frame, exact feature-group metadata and audit tables.

    All windows use the team's last 5/10 strictly earlier calendar-date fixture
    slots within the same season. Missing source fixtures stay missing and are
    exposed by observed-slot counts. XI candidates require an earlier positive
    appearance in that club's last five slots; a later prior positive appearance
    at another club removes that candidate. This estimates neither injury status
    nor a confirmed lineup. All target-date source rows are excluded together.
    """
    missing = set(TARGET_COLUMNS) - set(target_matches)
    if missing:
        raise ValueError(f"Target matches missing columns: {sorted(missing)}")
    targets = target_matches[TARGET_COLUMNS].copy()
    targets["match_date"] = _days(targets.match_date)
    if targets.match_id.isna().any() or targets.match_id.duplicated().any() or targets.match_date.isna().any():
        raise ValueError("Target match IDs/dates must be present and IDs unique")
    for column in ("home_team", "away_team"):
        targets[column] = targets[column].map(_team)
    if targets[["season", "home_team", "away_team"]].isna().any().any() or targets.home_team.eq(targets.away_team).any():
        raise ValueError("Target season and distinct club identities are required")
    required = {"season", "element", "match_id", "match_date", "team", "position_type", "minutes"}
    if required - set(players):
        raise ValueError(f"Player history missing columns: {sorted(required - set(players))}")
    history = players.copy()
    # The public input attrs preserve context for this API. Do not propagate
    # thousands of calendar/audit records into each bounded temporary group.
    history.attrs = {}
    history["match_date"] = _days(history.match_date)
    history["element"] = history.element.map(_token)
    history["team"] = history.team.map(_team)
    history["position_type"] = history.position_type.map(_role)
    history["position_source"] = history.get("position_source", pd.Series("supplied_historical_role_proxy", index=history.index))
    for column in ("minutes", *FORM_FIELDS):
        history[column] = pd.to_numeric(history[column], errors="coerce") if column in history else np.nan
    if history[["season", "element", "match_id", "match_date", "team", "minutes"]].isna().any().any():
        raise ValueError("Player history has missing fixture identity or minutes")
    if history.duplicated(["season", "match_id", "element"]).any():
        raise ValueError("Duplicate player-fixture history")
    if history.minutes.lt(0).any() or history.minutes.gt(120).any():
        raise ValueError("Invalid player-history minutes")
    history = history.loc[history.position_type.ne(5)].copy()
    history["active_players"] = history.minutes.gt(0).astype(float)
    history["players60"] = history.minutes.ge(60).astype(float)
    history["goal_involvements"] = history.goals_scored + history.assists
    keys = ["season", "team", "match_id"]
    grouped = history.groupby(keys, sort=False)
    totals = grouped[list(FORM_METRICS)].sum(min_count=1)
    total_lookup = {key: row.to_numpy(float) for key, row in totals.iterrows()}
    row_lookup = {key: group.sort_values(["match_date", "element"], kind="stable")
                  for key, group in grouped}
    role_totals = history.loc[history.position_type.isin(POSITIONS)].groupby(keys + ["position_type"])[list(POSITION_METRICS)].sum(min_count=1)
    position_lookup = {}
    for key, group in grouped:
        if (group.minutes.gt(0) & ~group.position_type.isin(POSITIONS)).any():
            position_lookup[key] = np.full(24, np.nan)
            continue
        values = []
        for role in POSITIONS:
            rkey = (*key, role)
            values.extend(role_totals.loc[rkey].to_numpy(float) if rkey in role_totals.index else np.zeros(6))
        position_lookup[key] = np.asarray(values, dtype=float)
    calendar_data = players.attrs.get("fixture_calendar")
    if calendar_data:
        calendar = pd.DataFrame(calendar_data)
        calendar["match_date"] = _days(calendar.match_date)
        calendar_basis = "full_saved_E0_and_explicit_live_finished_fixture_calendar"
        sides = []
        for side in ("home", "away"):
            one = calendar[["match_id", "season", "match_date"]].copy()
            one["team"] = calendar[side + "_team"].map(_team)
            sides.append(one)
        slots = pd.concat(sides, ignore_index=True)
    else:
        slots = history[["match_id", "season", "match_date", "team"]].drop_duplicates()
        calendar_basis = "observed_history_only_no_external_calendar_supplied"
    if slots.duplicated(["season", "team", "match_id"]).any():
        raise ValueError("Duplicate team fixture slots")
    calendars = {key: group.sort_values(["match_date", "match_id"], kind="stable")
                 for key, group in slots.groupby(["season", "team"], sort=False)}
    positive = history.loc[history.minutes.gt(0)].sort_values(["season", "element", "match_date", "match_id"])
    membership = {}
    for key, group in positive.groupby(["season", "element"], sort=False):
        if group.groupby("match_date").team.nunique().gt(1).any():
            raise ValueError("Conflicting same-date positive club appearances")
        membership[key] = (group.match_date.to_numpy(dtype="datetime64[ns]"), group.team.to_numpy())
    rows, xi_rows, coverage_rows = [], [], []
    empty_calendar = pd.DataFrame(columns=["match_id", "match_date"])
    for target in targets.itertuples(index=False):
        output = {column: getattr(target, column) for column in TARGET_COLUMNS}
        side_values = {}
        for side in ("home", "away"):
            team = getattr(target, side + "_team")
            calendar = calendars.get((target.season, team), empty_calendar)
            end = int(np.searchsorted(calendar.match_date.to_numpy(dtype="datetime64[ns]"), np.datetime64(target.match_date), side="left"))
            previous = calendar.iloc[max(0, end - 10):end]
            selected_slots = previous.iloc[-5:]
            full_keys = [(target.season, team, mid) for mid in previous.match_id]
            keys5 = [(target.season, team, mid) for mid in selected_slots.match_id]
            observed10 = [key for key in full_keys if key in total_lookup]
            observed5 = [key for key in keys5 if key in total_lookup]
            values = {}
            for window, selected in ((5, observed5), (10, observed10)):
                mean = _safe_mean([total_lookup[key] for key in selected])
                values.update({f"roll{window}_{name}": float(value) for name, value in zip(FORM_METRICS, mean)})
            position_mean = _safe_mean([position_lookup[key] for key in observed5]) if observed5 else np.full(24, np.nan)
            values.update({name: float(value) for name, value in zip(SQUAD_NAMES[:24], position_mean)})
            recent = pd.concat([row_lookup[key] for key in observed5], ignore_index=True) if observed5 else history.iloc[:0]
            # No current or future row may define candidates, role or club.
            active = recent.loc[recent.minutes.gt(0)]
            recent_stats = recent.groupby("element", sort=False).agg(
                total_minutes=("minutes", "sum"), observed_rows=("minutes", "size"),
                latest_source=("match_date", "max")).to_dict("index")
            membership_dates = []
            excluded_transfers = 0
            pool = []
            for element, group in active.groupby("element", sort=False):
                player_dates, player_teams = membership[(target.season, element)]
                limit = np.searchsorted(player_dates, np.datetime64(target.match_date), side="left")
                latest_date, latest_team = pd.Timestamp(player_dates[limit - 1]), player_teams[limit - 1]
                membership_dates.append(latest_date)
                if latest_team != team:
                    excluded_transfers += 1
                    continue
                observed = recent_stats[element]
                # Windows/rows were already ordered chronologically above.
                latest_role = group.iloc[-1]
                pool.append({"element": element, "position_type": latest_role.position_type,
                             "minutes": float(observed["total_minutes"]), "role_source": latest_role.position_source,
                             "role_date": latest_role.match_date, "last_positive": latest_role.match_date,
                             "latest_source": max(observed["latest_source"], latest_date),
                             "observed_rows": observed["observed_rows"]})
            candidates = pd.DataFrame(pool, columns=["element", "position_type", "minutes", "role_source", "role_date",
                                                     "last_positive", "latest_source", "observed_rows"])
            selected = []
            for role, count in FORMATION.items():
                ordered = candidates.loc[candidates.position_type.eq(role)].sort_values(["minutes", "element"], ascending=[False, True], kind="stable")
                selected.extend(ordered.head(count).to_dict("records"))
            selected_ids = {item["element"] for item in selected}
            selected_history = recent.loc[recent.element.isin(selected_ids)]
            selected_minutes = float(selected_history.minutes.sum())
            candidate_minutes = float(candidates.minutes.sum())
            values["xi_count"] = float(len(selected))
            for role, label in POSITIONS.items():
                values[f"xi_{label}_count"] = float(sum(item["position_type"] == role for item in selected))
            values["xi_recent_minutes_share"] = selected_minutes / candidate_minutes if candidate_minutes > 0 else np.nan
            values["xi_recent_minutes_mean"] = selected_minutes / len(selected) / len(observed5) if selected and observed5 else np.nan
            for feature, field in (("points", "total_points"), ("bps", "bps"), ("goal_involvements", "goal_involvements"),
                                   ("threat", "threat"), ("creativity", "creativity"), ("influence", "influence"), ("saves", "saves")):
                numerator = selected_history[field].sum(min_count=1)
                values[f"xi_{feature}_per90"] = float(numerator * 90 / selected_minutes) if selected_minutes > 0 else np.nan
            values["pool_count"] = float(len(candidates))
            values["minute_hhi"] = float(np.sum((candidates.minutes / candidate_minutes) ** 2)) if candidate_minutes > 0 else np.nan
            active_sets = [set(row_lookup[key].loc[row_lookup[key].minutes.gt(0), "element"]) for key in observed5]
            values["retained_players_fraction"] = len(active_sets[-1] & active_sets[-2]) / len(active_sets[-1]) if len(active_sets) >= 2 and active_sets[-1] else np.nan
            values["last60_count"] = float(row_lookup[observed5[-1]].minutes.ge(60).sum()) if observed5 else np.nan
            latest_form = _max_date([row_lookup[key].match_date.max() for key in observed10])
            latest_source = _max_date([latest_form, *membership_dates])
            latest_xi = _max_date([item["latest_source"] for item in selected])
            output[f"audit_player_{side}_latest_source_date"] = latest_source
            output[f"audit_player_{side}_xi_latest_source_date"] = latest_xi
            for name, value in (("observed_matches5", len(observed5)), ("observed_matches10", len(observed10)),
                                ("history_missing", int(not observed10))):
                output[f"feat_player_{side}_{name}"] = float(value)
            side_values[side] = values
            for rank, item in enumerate(selected, start=1):
                xi_rows.append({"match_id": target.match_id, "match_date": target.match_date, "season": target.season,
                    "team": team, "side": side, "element": item["element"], "player_key": f"{target.season}:{item['element']}",
                    "slot_position": POSITIONS[int(item["position_type"])], "selection_rank": rank,
                    "prior_minutes5": item["minutes"], "prior_observed_rows5": item["observed_rows"],
                    "last_positive_appearance_date": item["last_positive"], "latest_position_source_date": item["role_date"],
                    "latest_source_date": item["latest_source"], "position_source": item["role_source"]})
            coverage_rows.append({"match_id": target.match_id, "match_date": target.match_date, "season": target.season,
                "team": team, "side": side, "prior_fixture_slots5": len(selected_slots), "prior_fixture_slots10": len(previous),
                "observed_matches5": len(observed5), "observed_matches10": len(observed10),
                "position_observed_matches5": sum(np.isfinite(position_lookup[key]).all() for key in observed5),
                "xi_selected_players": len(selected), "xi_missing_slots": 11 - len(selected),
                "prior_positive_pool_count": len(candidates), "known_transfer_candidates_excluded": excluded_transfers,
                "latest_source_date": latest_source, "xi_latest_source_date": latest_xi})
        for side in ("home", "away"):
            output.update({f"feat_player_{side}_{name}": side_values[side][name] for name in (*FORM_NAMES, *SQUAD_NAMES)})
        output.update({f"feat_player_diff_{name}": side_values["home"][name] - side_values["away"][name]
                       for name in (*FORM_NAMES, *SQUAD_NAMES)})
        rows.append(output)
    frame = pd.DataFrame(rows)
    if len(frame):
        frame[PLAYER_SQUAD_FEATURES] = frame[PLAYER_SQUAD_FEATURES].astype(float)
        if np.isinf(frame[PLAYER_SQUAD_FEATURES].to_numpy()).any():
            raise AssertionError("Infinite player features")
        for column in [name for name in frame if name.startswith("audit_player_")]:
            frame[column] = pd.to_datetime(frame[column])
            if (frame[column].notna() & frame[column].ge(frame.match_date)).any():
                raise AssertionError("A non-prior source date entered player features")
    coverage = pd.DataFrame(coverage_rows)
    xi = pd.DataFrame(xi_rows, columns=XI_AUDIT_COLUMNS)
    metadata = {
        "target_rows": len(frame), "player_history_rows": len(history), "player_identity": "season + element",
        "feature_groups": {"coverage": COVERAGE_FEATURES, "player_form": PLAYER_FORM_FEATURES, "player_squad": PLAYER_SQUAD_FEATURES},
        "feature_counts": {"coverage": len(COVERAGE_FEATURES), "player_form": len(PLAYER_FORM_FEATURES), "player_squad": len(PLAYER_SQUAD_FEATURES)},
        "calendar_basis": calendar_basis, "formation": {POSITIONS[key]: value for key, value in FORMATION.items()},
        "window_definition": "Last5/10 same-season fixture-calendar slots strictly before the target printed calendar date; average available source fixtures, never fill a missing fixture's performance with zero.",
        "xi_definition": "Fixed1GK4DEF4MID2FWD from prior-positive-appearance pool in last5slots; rank own-club observed minutes descending then element string ascending; remove players whose latest earlier positive appearance was at another club; no alternative-role backfill.",
        "xi_rate_definition": "90 * sum selected players' observed historical statistic / sum their observed historical minutes; weighted per-player-90 profile, not a predicted11-player match total.",
        "minute_mean_definition": "Selected total prior minutes / selected players / observed club fixtures in last5slots.",
        "continuity_definition": "Share of positive-minute players in the last observed fixture also positive in the preceding observed fixture; unknown with fewer than2observed fixtures.",
        "leakage_checks": {"strictly_earlier_calendar_dates": True, "target_rows_roles_rosters_excluded": True,
                           "cross_season_player_ids_joined": False, "all_target_ids_preserved": set(frame.match_id) == set(targets.match_id)},
        "coverage_by_season": coverage.groupby("season").agg(target_sides=("match_id", "size"),
            sides_with_history=("observed_matches10", lambda values: int(values.gt(0).sum())),
            full_prior_xi=("xi_selected_players", lambda values: int(values.eq(11).sum()))).reset_index().to_dict("records") if len(coverage) else [],
        "limitations": [
            "Retrospectively saved fields and revisions have unverified historical publication times.",
            "A positive-appearance pool cannot establish transfers without a later observed appearance, injuries, eligibility or actual availability.",
            "FPL position labels may be season/current snapshot proxies; each selected role is taken only from a strictly earlier history row, and provenance is retained.",
            "Same-season identity resets create missing/limited features early in each season and for newly observed players.",
            "Scoring rules change across seasons. Native xG, starts, current roster, price, ownership and availability fields are excluded from these primary features.",
            "Current club cohort target selection and all previously inspected seasons make subsequent model comparisons exploratory.",
        ],
    }
    details = {"fixture_reconciliation": pd.DataFrame(players.attrs.get("fixture_reconciliation", []), columns=FIXTURE_AUDIT_COLUMNS),
               "projected_xi": xi, "target_coverage": coverage}
    return frame, metadata, details
