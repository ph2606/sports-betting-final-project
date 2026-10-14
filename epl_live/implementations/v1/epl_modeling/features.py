"""Build date-lagged EPL features from an existing ``epl_data`` snapshot.

Only existing Football-Data E0 cohort fixtures are exported. Saved whole-league
E0 files supply opponent histories, including matches between two other clubs.
Nothing is downloaded, and no acquisition artifacts are modified.
"""
from __future__ import annotations

import csv
import hashlib
import io
from pathlib import Path

import numpy as np
import pandas as pd


TEAM_ALIASES = {
    "AFC Bournemouth": "Bournemouth", "Bournemouth AFC": "Bournemouth",
    "Brighton": "Brighton & Hove Albion", "Brighton and Hove Albion": "Brighton & Hove Albion",
    "Coventry": "Coventry City", "Hull": "Hull City", "Ipswich": "Ipswich Town",
    "Leeds": "Leeds United", "Man City": "Manchester City", "Man United": "Manchester United",
    "Man Utd": "Manchester United", "Newcastle": "Newcastle United",
    "Nott'm Forest": "Nottingham Forest", "Nott'ham Forest": "Nottingham Forest",
    "Nottm Forest": "Nottingham Forest", "Tottenham": "Tottenham Hotspur", "Spurs": "Tottenham Hotspur",
    "Birmingham": "Birmingham City", "Blackburn": "Blackburn Rovers", "Bolton": "Bolton Wanderers",
    "Bradford": "Bradford City", "Cardiff": "Cardiff City", "Charlton": "Charlton Athletic",
    "Derby": "Derby County", "Huddersfield": "Huddersfield Town", "Leicester": "Leicester City",
    "Luton": "Luton Town", "Norwich": "Norwich City", "Oldham": "Oldham Athletic",
    "QPR": "Queens Park Rangers", "Sheffield Utd": "Sheffield United",
    "Sheffield Weds": "Sheffield Wednesday", "Stoke": "Stoke City", "Swansea": "Swansea City",
    "Swindon": "Swindon Town", "West Brom": "West Bromwich Albion",
    "West Bromwich": "West Bromwich Albion", "West Ham": "West Ham United",
    "Wigan": "Wigan Athletic", "Wolves": "Wolverhampton Wanderers",
    "Wolverhampton": "Wolverhampton Wanderers",
}
LOOKUP = {key.casefold(): value for key, value in TEAM_ALIASES.items()}
LOOKUP.update({value.casefold(): value for value in TEAM_ALIASES.values()})

BOX_FIELDS = {
    "goals": ("FTHG", "FTAG"), "shots": ("HS", "AS"),
    "shots_on_target": ("HST", "AST"), "corners": ("HC", "AC"),
    "fouls": ("HF", "AF"), "yellow_cards": ("HY", "AY"), "red_cards": ("HR", "AR"),
}
FPL_FIELDS = (
    "total_points", "bps", "bonus", "assists", "saves", "minutes", "influence", "creativity",
    "threat", "ict_index", "expected_goals", "expected_assists", "tackles", "recoveries",
    "defensive_contribution",
)
FD_METRICS = ["points", "win"] + [f"{metric}_{direction}" for metric in BOX_FIELDS for direction in ("for", "against", "diff")]
US_METRICS = ["us_xg_for", "us_xg_against", "us_xg_diff"]
FPL_METRICS = ["fpl_" + field for field in FPL_FIELDS]
METRICS = FD_METRICS + US_METRICS + FPL_METRICS
KEYS = ["season", "match_date", "home_team", "away_team"]


def _team(value):
    if pd.isna(value):
        return None
    text = str(value).strip()
    return LOOKUP.get(text.casefold(), text)


def _table(root: Path, relative: str, required=False):
    path = root / "data" / "processed" / relative
    for suffix in (".parquet", ".csv"):
        candidate = path.with_suffix(suffix)
        if candidate.exists():
            try:
                return pd.read_parquet(candidate) if suffix == ".parquet" else pd.read_csv(candidate, low_memory=False)
            except pd.errors.EmptyDataError:
                return pd.DataFrame()
    if required:
        raise FileNotFoundError(f"Required saved table is absent: {path}")
    return pd.DataFrame()


def _number(frame, column):
    values = frame[column] if column in frame else pd.Series(np.nan, index=frame.index)
    return pd.to_numeric(values, errors="coerce")


def _date(values):
    # Match printed calendar dates; no undocumented timezone conversion.
    return pd.to_datetime(values.astype("string").str.slice(0, 10), format="%Y-%m-%d", errors="coerce")


def _unique(frame, columns, source):
    duplicates = frame.duplicated(columns, keep=False)
    if duplicates.any():
        example = frame.loc[duplicates, columns].head(5).to_dict("records")
        raise ValueError(f"Ambiguous {source} keys {columns}: {example}")


def _match_id(season, home, away):
    text = f"{season}|E0|{home}|{away}"
    return "fd_" + hashlib.sha256(text.encode()).hexdigest()[:24]


def _read_league_files(root, cohort):
    files = sorted((root / "data" / "raw" / "football_data").glob("*/E0.csv"))
    if not files:
        raise FileNotFoundError("Saved full raw E0 league files are required to reconstruct all opponent histories")
    source_years = {}
    if {"source_file", "season_start_year"}.issubset(cohort):
        source_years = dict(zip(cohort.source_file, cohort.season_start_year))
    frames, encodings = [], {}
    for path in files:
        relative = f"{path.parent.name}/E0.csv"
        year = source_years.get(relative)
        if pd.isna(year):
            code = int(path.parent.name[:2])
            year = (1900 if code >= 80 else 2000) + code
        year = int(year)
        season = f"{year}-{(year+1)%100:02d}"
        content = path.read_bytes()
        try:
            text, encoding = content.decode("utf-8-sig"), "utf-8-sig"
        except UnicodeDecodeError:
            text, encoding = content.decode("cp1252"), "cp1252"
        encodings[relative] = encoding
        reader = csv.reader(io.StringIO(text))
        header = [value.strip() for value in next(reader)]
        records = [dict(zip(header, row)) for row in reader if any(value.strip() for value in row)]
        frame = pd.DataFrame(records)
        if not {"Date", "HomeTeam", "AwayTeam"}.issubset(frame):
            raise ValueError(f"Invalid saved E0 schema: {path}")
        frame = frame[frame.HomeTeam.notna() & frame.AwayTeam.notna() & frame.HomeTeam.ne("") & frame.AwayTeam.ne("")].copy()
        frame["match_date"] = pd.to_datetime(frame.Date, format="mixed", dayfirst=True, errors="coerce").dt.normalize()
        frame["season"] = season
        frame["season_start_year"] = year
        frame["home_team"] = frame.HomeTeam.map(_team)
        frame["away_team"] = frame.AwayTeam.map(_team)
        frame["match_id"] = [_match_id(season, home, away) for home, away in zip(frame.HomeTeam, frame.AwayTeam)]
        frame["result"] = frame.get("FTR", pd.Series(index=frame.index, dtype="string")).where(lambda value: value.isin(["H", "D", "A"]))
        frame["_completed"] = frame.result.notna() & _number(frame, "FTHG").notna() & _number(frame, "FTAG").notna()
        frames.append(frame)
    league = pd.concat(frames, ignore_index=True)
    _unique(league, ["match_id"], "raw E0 match")
    _unique(league[league.match_date.notna()], KEYS, "raw E0 exact fixture")
    return league, encodings


def _observations(league):
    sides = []
    for side, other in (("home", "away"), ("away", "home")):
        frame = league[["match_id", "season", "season_start_year", "match_date", "_completed"]].copy()
        frame["team"] = league[side + "_team"]
        frame["side"] = side
        home = side == "home"
        frame["win"] = league.result.map({"H": int(home), "D": 0, "A": int(not home)})
        frame["points"] = league.result.map({"H": 3 if home else 0, "D": 1, "A": 0 if home else 3})
        for metric, (hfield, afield) in BOX_FIELDS.items():
            own, opponent = (hfield, afield) if home else (afield, hfield)
            frame[metric + "_for"] = _number(league, own)
            frame[metric + "_against"] = _number(league, opponent)
            frame[metric + "_diff"] = frame[metric + "_for"] - frame[metric + "_against"]
        sides.append(frame)
    result = pd.concat(sides, ignore_index=True)
    _unique(result, ["match_id", "team"], "E0 team observation")
    return result


def _understat_history(root, league):
    columns = ["match_id", "team"] + US_METRICS
    report = {"available": False, "exact_linked_matches": 0, "rejected_identity_or_date_rows": 0}
    links = _table(root, "integrated/match_source_links")
    native = _table(root, "understat/matches")
    if links.empty or native.empty or "understat_id" not in links:
        return pd.DataFrame(columns=columns), report
    links = links[links.source_match_key.notna() & links.understat_id.notna()].copy()
    _unique(links, ["source_match_key"], "integrated Football-Data link")
    links["understat_id"] = links.understat_id.astype("string")
    _unique(links, ["understat_id"], "integrated Understat link")
    source = pd.DataFrame({
        "understat_id": native.id.astype("string"), "us_date": _date(native.datetime),
        "us_season": native.season, "us_home": native["h__title"].map(_team),
        "us_away": native["a__title"].map(_team), "us_completed": native.isResult.fillna(False).astype(bool),
        "us_home_xg": _number(native, "xG__h"), "us_away_xg": _number(native, "xG__a"),
    })
    _unique(source, ["understat_id"], "Understat native match")
    # The integrated ID link is necessary; no fallback fuzzy/date-nearby match.
    linked = links[["source_match_key", "understat_id"]].merge(source, on="understat_id", how="left", validate="one_to_one")
    identity = league[["match_id"] + KEYS]
    linked = linked.merge(identity, left_on="source_match_key", right_on="match_id", how="left", validate="one_to_one")
    valid = (linked.us_season.eq(linked.season) & linked.us_date.eq(linked.match_date)
             & linked.us_home.eq(linked.home_team) & linked.us_away.eq(linked.away_team)
             & linked.us_completed.fillna(False))
    report.update(available=True, rejected_identity_or_date_rows=int((~valid).sum()), exact_linked_matches=int(valid.sum()))
    linked = linked.loc[valid]
    sides = []
    for side, other in (("home", "away"), ("away", "home")):
        sides.append(pd.DataFrame({"match_id": linked.match_id, "team": linked[side + "_team"],
                                   "us_xg_for": linked["us_" + side + "_xg"],
                                   "us_xg_against": linked["us_" + other + "_xg"]}))
    result = pd.concat(sides, ignore_index=True)
    result["us_xg_diff"] = result.us_xg_for - result.us_xg_against
    _unique(result, ["match_id", "team"], "exact-linked Understat team match")
    return result[columns], report


def _fpl_history(root, league):
    columns = ["match_id", "team"] + FPL_METRICS
    archive = _table(root, "fpl_archive/player_gameweeks")
    official = _table(root, "fpl_current/player_match_history")
    report = {"available": False, "exact_linked_fixtures": 0, "unmatched_or_invalid_fixture_identities": 0,
              "manager_rows_excluded": 0, "official_current_seasons_preferred": []}
    if not official.empty:
        current_seasons = official.season.dropna().unique().tolist()
        report["official_current_seasons_preferred"] = sorted(current_seasons)
        if not archive.empty:
            archive = archive[~archive.season.isin(current_seasons)]
    pieces = [frame for frame in (archive, official) if not frame.empty]
    if not pieces:
        return pd.DataFrame(columns=columns), report
    players = pd.concat(pieces, ignore_index=True)
    manager = _number(players, "position_type").eq(5)
    report["manager_rows_excluded"] = int(manager.sum())
    players = players.loc[~manager].copy()
    _unique(players, ["season", "fixture", "element"], "FPL player-fixture")
    players["match_date"] = _date(players.kickoff_time)
    players["team"] = players.canonical_team.map(_team)
    players["opponent"] = players.opponent_name.map(_team)
    was_home = players.was_home.map({True: True, False: False, "True": True, "False": False, "true": True, "false": False})
    players["home_team"] = players.team.where(was_home.eq(True), players.opponent)
    players["away_team"] = players.opponent.where(was_home.eq(True), players.team)
    valid = players[KEYS + ["fixture", "team"]].notna().all(axis=1) & was_home.notna()
    players = players.loc[valid].copy()
    identities = players[["season", "fixture", "match_date", "home_team", "away_team"]].drop_duplicates()
    _unique(identities, ["season", "fixture"], "FPL fixture identity")
    _unique(identities, KEYS, "FPL exact calendar fixture")
    identities = identities.merge(league[["match_id"] + KEYS], on=KEYS, how="left", validate="one_to_one")
    report["unmatched_or_invalid_fixture_identities"] = int(identities.match_id.isna().sum())
    report["exact_linked_fixtures"] = int(identities.match_id.notna().sum())
    report["invalid_player_identity_rows"] = int((~valid).sum())
    report["available"] = True
    for field in FPL_FIELDS:
        players[field] = _number(players, field)
    aggregated = players.groupby(["season", "fixture", "team"], dropna=False)[list(FPL_FIELDS)].sum(min_count=1).reset_index()
    aggregated = aggregated.merge(identities[["season", "fixture", "match_id"]], on=["season", "fixture"], how="left", validate="many_to_one")
    aggregated = aggregated[aggregated.match_id.notna()].rename(columns={field: "fpl_" + field for field in FPL_FIELDS})
    _unique(aggregated, ["match_id", "team"], "exact-linked FPL team fixture aggregate")
    return aggregated[columns], report


def _means(values, left, right):
    finite = np.isfinite(values)
    sums = np.vstack([np.zeros(values.shape[1]), np.cumsum(np.where(finite, values, 0.0), axis=0)])
    counts = np.vstack([np.zeros(values.shape[1]), np.cumsum(finite, axis=0)])
    numerator, denominator = sums[right] - sums[left], counts[right] - counts[left]
    return np.divide(numerator, denominator, out=np.full(numerator.shape, np.nan), where=denominator > 0)


def _prior_date(dates, target_dates):
    result = np.full(len(target_dates), np.datetime64("NaT"), dtype="datetime64[ns]")
    indices = np.searchsorted(dates, target_dates, side="left") - 1
    present = indices >= 0
    result[present] = dates[indices[present]]
    return result


def _team_features(observations, targets, archive_years):
    rows = []
    history = observations[observations._completed & observations.match_date.notna()].copy()
    histories = {team: group.sort_values(["match_date", "match_id"]) for team, group in history.groupby("team", sort=False)}
    for team, query in targets.groupby("team", sort=False, dropna=False):
        query = query.copy()
        computed = {}
        hist = histories.get(team, history.iloc[:0])
        dates = hist.match_date.to_numpy(dtype="datetime64[ns]")
        target_dates = query.match_date.to_numpy(dtype="datetime64[ns]")
        valid_date = query.match_date.notna().to_numpy()
        right = np.searchsorted(dates, target_dates, side="left")
        right[~valid_date] = 0
        values = hist[METRICS].to_numpy(dtype=float)
        computed["history_matches"] = right.astype(float)
        latest = _prior_date(dates, target_dates)
        latest[~valid_date] = np.datetime64("NaT")
        computed["audit_fd_latest_prior_date"] = latest
        computed["rest_days"] = (target_dates - latest) / np.timedelta64(1, "D")
        computed["fd_history_missing"] = (right == 0).astype(float)
        for window in (5, 10):
            means = _means(values, np.maximum(0, right-window), right)
            for position, metric in enumerate(METRICS):
                computed[f"roll{window}_{metric}"] = means[:, position]
            computed[f"roll{window}_matches"] = np.minimum(window, right).astype(float)
        std = np.full((len(query), len(METRICS)), np.nan)
        std_counts = np.zeros(len(query))
        prior_win = np.full(len(query), np.nan)
        prior_missing = np.ones(len(query))
        prior_archive_missing = np.ones(len(query))
        promoted = np.full(len(query), np.nan)
        for season in query.season.dropna().unique():
            mask = query.season.eq(season).to_numpy()
            season_history = hist[hist.season.eq(season)]
            season_dates = season_history.match_date.to_numpy(dtype="datetime64[ns]")
            season_right = np.searchsorted(season_dates, target_dates[mask], side="left")
            season_right[~valid_date[mask]] = 0
            std[mask] = _means(season_history[METRICS].to_numpy(dtype=float), np.zeros(mask.sum(), dtype=int), season_right)
            std_counts[mask] = season_right
            year = int(str(season)[:4])
            previous = hist[hist.season_start_year.eq(year-1)]
            previous_dates = previous.match_date.to_numpy(dtype="datetime64[ns]")
            previous_right = np.searchsorted(previous_dates, target_dates[mask], side="left")
            previous_right[~valid_date[mask]] = 0
            means = _means(previous[["win"]].to_numpy(dtype=float), np.zeros(mask.sum(), dtype=int), previous_right)[:, 0]
            prior_win[mask] = means
            prior_missing[mask] = np.isnan(means)
            prior_archive_missing[mask] = float(year-1 not in archive_years)
            if year-1 in archive_years:
                promoted[mask] = (previous_right == 0).astype(float)
        for position, metric in enumerate(METRICS):
            computed["std_" + metric] = std[:, position]
        computed["std_matches"] = std_counts
        computed["prior_season_win_pct"] = prior_win
        computed["prior_season_missing"] = prior_missing
        computed["prior_season_archive_missing"] = prior_archive_missing
        computed["promoted_from_outside_epl"] = promoted
        for source, metric in (("us", "us_xg_for"), ("fpl", "fpl_minutes")):
            observed = np.isfinite(hist[metric].to_numpy(dtype=float))
            source_dates = dates[observed]
            latest = _prior_date(source_dates, target_dates)
            latest[~valid_date] = np.datetime64("NaT")
            computed[f"audit_{source}_latest_prior_date"] = latest
            source_count = np.searchsorted(source_dates, target_dates, side="left")
            source_count[~valid_date] = 0
            computed[f"{source}_history_missing"] = (source_count == 0).astype(float)
            count_prefix = np.r_[0, np.cumsum(observed)]
            for window in (5, 10):
                computed[f"{source}_roll{window}_observed_matches"] = count_prefix[right] - count_prefix[np.maximum(0, right-window)]
            season_counts = np.zeros(len(query))
            for season in query.season.dropna().unique():
                mask = query.season.eq(season).to_numpy()
                source_season_dates = hist.loc[hist.season.eq(season) & observed, "match_date"].to_numpy(dtype="datetime64[ns]")
                season_counts[mask] = np.searchsorted(source_season_dates, target_dates[mask], side="left")
            season_counts[~valid_date] = 0
            computed[f"{source}_std_observed_matches"] = season_counts
        # No prediction-time features are reconstructed for an undated fixture.
        feature_frame = pd.DataFrame(computed, index=query.index)
        feature_columns = [column for column in feature_frame if not column.startswith("audit_")]
        feature_frame.loc[~valid_date, feature_columns] = np.nan
        rows.append(pd.concat([query, feature_frame], axis=1))
    return pd.concat(rows, ignore_index=True)


def _definition(name):
    if name.startswith("feat_diff_"):
        return {"calculation": "home minus away for corresponding lagged team feature", "timing": "strictly earlier calendar dates"}
    short = name.removeprefix("feat_home_").removeprefix("feat_away_")
    source = "understat exact integrated links" if "_us_" in "_"+short else "FPL actual-club fixture aggregates" if "_fpl_" in "_"+short else "Football-Data full raw E0 history"
    if short.startswith("std_"):
        calculation = "arithmetic mean over earlier completed matches in the target season"
    elif short.startswith("roll5_") or short.startswith("roll10_"):
        calculation = "arithmetic mean over the last 5 or 10 earlier completed E0 matches, crossing season boundaries"
    else:
        calculation = {
            "prior_season_win_pct": "wins / completed EPL matches in immediately preceding season, observed before target date",
            "promoted_from_outside_epl": "1 if club has no earlier match in prior EPL season whose raw archive is present; NaN if archive absent",
            "prior_season_missing": "1 when prior-season EPL win percentage unavailable",
            "prior_season_archive_missing": "1 when immediately preceding EPL raw file is absent",
            "rest_days": "calendar days since latest strictly earlier completed E0 match",
        }.get(short, "historical match count or missing-history indicator; never target-match statistics")
    return {"source": source, "calculation": calculation,
            "timing": "source match date strictly less than target match date",
            "missing_values": "NaN means unavailable; averages skip missing observations without converting them to zero",
            "difference_convention": "own minus opponent; card/foul differences describe frequency, not a claim that higher is better"}


def build_features(data_root: Path) -> tuple[pd.DataFrame, dict]:
    """Return the preserved cohort modeling frame and JSON-serializable metadata.

    ``data_root`` is the existing ``epl_data`` package directory. ``feat_*``
    columns are numeric predictors; identifiers, result and ``audit_*`` columns
    must never be supplied to the estimator as numeric predictors.
    """
    root = Path(data_root)
    cohort = _table(root, "football_data/matches_current_cohort", required=True)
    cohort = cohort.loc[cohort.division.eq("E0")].copy()
    _unique(cohort, ["source_match_key"], "existing E0 cohort")
    league, encodings = _read_league_files(root, cohort)
    missing_raw = sorted(set(cohort.source_match_key)-set(league.match_id))
    if missing_raw:
        raise ValueError(f"Existing cohort fixtures absent from full raw E0 archives: {missing_raw[:5]}")
    frame = pd.DataFrame({"match_id": cohort.source_match_key, "season": cohort.season,
                          "match_date": _date(cohort.match_date),
                          "home_team": cohort.HomeTeam.map(_team), "away_team": cohort.AwayTeam.map(_team),
                          "result": cohort.FTR.where(cohort.FTR.isin(["H", "D", "A"]))})
    frame = frame.reset_index(drop=True)
    observations = _observations(league)
    us, us_report = _understat_history(root, league)
    fpl, fpl_report = _fpl_history(root, league)
    observations = observations.merge(us, on=["match_id", "team"], how="left", validate="one_to_one")
    observations = observations.merge(fpl, on=["match_id", "team"], how="left", validate="one_to_one")
    for metric in METRICS:
        observations[metric] = _number(observations, metric)
    # Respect the saved requested-as-of cutoff if supplied, without using current snapshots.
    cutoff = None
    membership = root / "metadata" / "current_teams.csv"
    if membership.exists():
        teams = pd.read_csv(membership)
        if "as_of_date" in teams:
            cutoff = pd.to_datetime(teams.as_of_date.dropna(), errors="coerce").max()
    if cutoff is not None and pd.notna(cutoff):
        observations.loc[observations.match_date.gt(cutoff), "_completed"] = False
    targets = []
    for side in ("home", "away"):
        target = frame[["match_id", "season", "match_date"]].copy()
        target["team"], target["side"] = frame[side+"_team"], side
        targets.append(target)
    features = _team_features(observations, pd.concat(targets, ignore_index=True), set(league.season_start_year.unique()))
    feature_names = []
    for side in ("home", "away"):
        one_side = features.loc[features.side.eq(side)].drop(columns=["season", "match_date", "team", "side"])
        rename = {}
        for column in one_side:
            if column == "match_id":
                continue
            renamed = f"audit_{side}_" + column.removeprefix("audit_") if column.startswith("audit_") else f"feat_{side}_" + column
            rename[column] = renamed
            if renamed.startswith("feat_"):
                feature_names.append(renamed)
        frame = frame.merge(one_side.rename(columns=rename), on="match_id", how="left", validate="one_to_one")
    differences = {}
    for period in ("std", "roll5", "roll10"):
        for metric in METRICS:
            name = f"feat_diff_{period}_{metric}"
            differences[name] = frame[f"feat_home_{period}_{metric}"] - frame[f"feat_away_{period}_{metric}"]
    frame = pd.concat([frame, pd.DataFrame(differences)], axis=1)
    feature_names += list(differences)
    frame[feature_names] = frame[feature_names].apply(pd.to_numeric, errors="coerce").astype(float)
    frame["audit_match_date_missing"] = frame.match_date.isna()
    frame["audit_understat_target_exact_link_missing"] = ~frame.match_id.isin(us.match_id)
    frame["audit_fpl_target_exact_link_missing"] = ~frame.match_id.isin(fpl.match_id)
    audit_dates = [column for column in frame if column.startswith("audit_") and column.endswith("_date")]
    violations = {column: int((frame[column].notna() & frame.match_date.notna() & frame[column].ge(frame.match_date)).sum()) for column in audit_dates}
    if any(violations.values()):
        raise AssertionError(f"Non-prior history entered features: {violations}")
    _unique(frame, ["match_id"], "exported modeling fixture")
    frame = frame.sort_values(["match_date", "match_id"], na_position="last").reset_index(drop=True)
    metadata = {
        "rows": len(frame), "feature_count": len(feature_names), "feature_columns": feature_names,
        "feature_definitions": {name: _definition(name) for name in feature_names},
        "coverage": {"feature_nonmissing": {column: int(frame[column].notna().sum()) for column in feature_names},
                     "seasons": sorted(frame.season.dropna().unique().tolist()), "missing_target_results": int(frame.result.isna().sum()),
                     "invalid_target_dates": int(frame.match_date.isna().sum()),
                     "understat": us_report, "fpl": fpl_report},
        "history_scope": {"full_raw_e0_matches": len(league), "exported_existing_cohort_matches": len(frame),
                          "all_opponent_clubs_in_history": int(observations.team.nunique()), "raw_encodings": encodings,
                          "requested_snapshot_cutoff": None if cutoff is None or pd.isna(cutoff) else cutoff.strftime("%Y-%m-%d")},
        "leakage_checks": {"latest_prior_date_violations": violations, "same_date_matches_excluded": True,
                           "one_to_one_match_joins_checked": True,
                           "export_ids_equal_existing_cohort": set(frame.match_id)==set(cohort.source_match_key),
                           "target_boxscores_excluded_from_own_features": True},
        "limitations": [
            "Retrospectively acquired statistics are lagged by match date; historical publication times and revisions are not independently verified.",
            "Current bootstrap/roster/injury/ownership/price/forecast snapshots, target lineups, odds and season-final totals are excluded.",
            "Understat uses displayed team xG from exact integrated fixture links, not additive player/shot xG or retrospective forecast fields.",
            "Understat and FPL histories for historical opponents can be incomplete outside saved cohort-linked fixtures; observed-count features expose that coverage.",
            "FPL statistics are sums of actual fixture-club player records. Official current-season history supersedes overlapping archive records; manager records are excluded.",
            "FPL scoring rules and field availability change by season; missing fields remain NaN, not zero.",
            "The currently eligible club cohort is imposed on historical exports, creating a retrospective cohort selection limitation.",
            "Promoted flag means absent from the observed prior EPL season, not a verified promotion transaction; it is unknown when that season's raw archive is absent.",
        ],
    }
    return frame, metadata
