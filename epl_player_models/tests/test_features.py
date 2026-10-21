from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from epl_player_models.features import (
    COVERAGE_FEATURES, FORM_FIELDS, PLAYER_FORM_FEATURES, PLAYER_SQUAD_FEATURES,
    TARGET_COLUMNS, build_player_features, load_player_history,
)


def history(dates=("2022-08-01", "2022-08-08")):
    rows, calendar = [], []
    roles = [1] + [2] * 5 + [3] * 4 + [4] * 3
    minutes = [90, 90, 90, 80, 60, 40, 90, 90, 70, 30, 90, 50, 20]
    for index, date in enumerate(dates):
        mid = f"past{index}"
        calendar.append({"match_id": mid, "season": "2022-23", "match_date": date,
                         "home_team": "Arsenal", "away_team": "Chelsea"})
        for team, offset in (("Arsenal", 0), ("Chelsea", 100)):
            for player, (role, mins) in enumerate(zip(roles, minutes), start=1):
                row = {"season": "2022-23", "element": str(player + offset), "fixture": str(index),
                       "match_id": mid, "match_date": date, "team": team,
                       "position_type": role, "position_source": "historical_test_role", "minutes": mins,
                       "source_path": "synthetic_prior_history"}
                row.update({field: float(player % 3) for field in FORM_FIELDS})
                rows.append(row)
    frame = pd.DataFrame(rows)
    frame.attrs["fixture_calendar"] = calendar
    return frame


def targets(date="2022-08-15", season="2022-23", match_id="target"):
    return pd.DataFrame([{"match_id": match_id, "season": season, "match_date": date,
                          "home_team": "Arsenal", "away_team": "Chelsea"}])


def test_exact_locked_feature_counts_and_weighted_projected_profile_math():
    players = history()
    frame, metadata, audits = build_player_features(players, targets())
    assert len(COVERAGE_FEATURES) == 6
    assert len(set(PLAYER_FORM_FEATURES)) == len(PLAYER_FORM_FEATURES) == 96
    assert len(set(PLAYER_SQUAD_FEATURES)) == len(PLAYER_SQUAD_FEATURES) == 222
    assert metadata["feature_counts"] == {"coverage": 6, "player_form": 96, "player_squad": 222}
    assert set(metadata["feature_groups"]["player_squad"]) == set(PLAYER_SQUAD_FEATURES)
    assert not any("expected_" in name or "xg" in name or "odds" in name or "price" in name for name in PLAYER_SQUAD_FEATURES)
    assert frame.feat_player_home_xi_count.iloc[0] == 11
    xi = audits["projected_xi"].query("side == 'home'")
    assert xi.slot_position.value_counts().to_dict() == {"def": 4, "mid": 4, "fwd": 2, "gk": 1}
    assert "6" not in set(xi.element) and "13" not in set(xi.element)
    selected = players.loc[players.team.eq("Arsenal") & players.element.isin(xi.element)]
    assert frame.feat_player_home_xi_points_per90.iloc[0] == pytest.approx(90 * selected.total_points.sum() / selected.minutes.sum())
    assert frame.feat_player_home_xi_recent_minutes_mean.iloc[0] == pytest.approx(selected.minutes.sum() / 11 / 2)
    assert frame.feat_player_home_roll5_goals_scored.iloc[0] == pytest.approx(players.loc[players.team.eq("Arsenal")].goals_scored.sum() / 2)
    assert frame.feat_player_diff_roll5_goals_scored.iloc[0] == 0
    assert frame.feat_player_home_observed_matches5.iloc[0] == 2
    assert frame.audit_player_home_latest_source_date.iloc[0] == pd.Timestamp("2022-08-08")


def test_target_and_future_performance_roles_and_new_rosters_cannot_change_features():
    players = history(("2022-08-01", "2022-08-08", "2022-08-15", "2022-08-22"))
    original, _, audits = build_player_features(players, targets())
    changed = players.copy(deep=True)
    future = pd.to_datetime(changed.match_date).ge("2022-08-15")
    changed.loc[future, list(FORM_FIELDS)] = 99999.
    changed.loc[future, "minutes"] = 1
    changed.loc[future, "position_type"] = 1
    extra = changed.loc[future].iloc[[0]].copy()
    extra["element"] = "brand_new_target_player"
    extra["minutes"] = 120
    changed = pd.concat([changed, extra], ignore_index=True)
    changed.attrs = deepcopy(players.attrs)
    changed["current_roster_team"] = "A completely different snapshot club"
    changed["chance_of_playing_next_round"] = 0
    changed["now_cost"] = 999
    result, _, changed_audits = build_player_features(changed, targets())
    pd.testing.assert_frame_equal(original, result)
    pd.testing.assert_frame_equal(audits["projected_xi"], changed_audits["projected_xi"])
    assert (changed_audits["projected_xi"].latest_source_date < pd.Timestamp("2022-08-15")).all()


def test_zero_minute_only_player_never_enters_prior_appearance_pool():
    players = history()
    extra = players.loc[players.team.eq("Arsenal")].iloc[[0]].copy()
    extra["element"] = "never_appeared"
    extra["minutes"] = 0
    extra["position_type"] = 1
    players = pd.concat([players, extra], ignore_index=True)
    result, _, audit = build_player_features(players, targets())
    assert "never_appeared" not in set(audit["projected_xi"].element)
    assert result.feat_player_home_pool_count.iloc[0] == 13


def test_later_prior_positive_appearance_at_another_club_removes_old_club_candidate():
    players = history()
    transfer = players.loc[players.element.eq("1")].iloc[[-1]].copy()
    transfer["match_id"] = "transfer_evidence"
    transfer["match_date"] = "2022-08-12"
    transfer["team"] = "Liverpool"
    combined = pd.concat([players, transfer], ignore_index=True)
    combined.attrs = deepcopy(players.attrs)
    result, _, audit = build_player_features(combined, targets())
    home = audit["projected_xi"].query("side == 'home'")
    assert "1" not in set(home.element)
    assert result.feat_player_home_xi_count.iloc[0] == 10
    assert result.feat_player_home_xi_gk_count.iloc[0] == 0
    assert result.audit_player_home_latest_source_date.iloc[0] == pd.Timestamp("2022-08-12")
    assert audit["target_coverage"].query("side == 'home'").known_transfer_candidates_excluded.iloc[0] == 1
    combined.loc[combined.match_id.eq("transfer_evidence"), "match_date"] = "2022-08-15"
    same_day, _, same_day_audit = build_player_features(combined, targets())
    assert same_day.feat_player_home_xi_count.iloc[0] == 11
    assert "1" in set(same_day_audit["projected_xi"].query("side == 'home'").element)


def test_season_local_player_identity_and_early_season_missingness_are_preserved():
    players = history()
    new_season = targets(date="2023-08-15", season="2023-24")
    frame, _, audits = build_player_features(players, new_season)
    assert frame.feat_player_home_history_missing.iloc[0] == 1
    assert frame.feat_player_home_observed_matches10.iloc[0] == 0
    assert pd.isna(frame.feat_player_home_roll5_bps.iloc[0])
    assert frame.feat_player_home_xi_count.iloc[0] == 0
    assert audits["projected_xi"].empty
    assert audits["projected_xi"].columns.size > 0


def test_missing_source_fixtures_keep_calendar_slots_and_are_not_zero_performance():
    players = history(("2022-08-01",))
    calendar = []
    for i, date in enumerate(pd.date_range("2022-08-01", periods=10, freq="D")):
        calendar.append({"match_id": "past0" if i == 0 else f"unobserved{i}", "season": "2022-23",
                         "match_date": date.strftime("%Y-%m-%d"), "home_team": "Arsenal", "away_team": "Chelsea"})
    players.attrs["fixture_calendar"] = calendar
    frame, _, details = build_player_features(players, targets("2022-08-11"))
    assert frame.feat_player_home_observed_matches5.iloc[0] == 0
    assert frame.feat_player_home_observed_matches10.iloc[0] == 1
    assert pd.isna(frame.feat_player_home_roll5_total_points.iloc[0])
    assert frame.feat_player_home_roll10_total_points.iloc[0] == players.loc[players.team.eq("Arsenal")].total_points.sum()
    assert details["target_coverage"].prior_fixture_slots5.eq(5).all()
    assert details["target_coverage"].prior_fixture_slots10.eq(10).all()


def test_role_shortage_is_exposed_without_backfilling_a_different_role():
    players = history()
    players.loc[players.team.eq("Arsenal") & players.position_type.eq(1), "position_type"] = np.nan
    frame, _, details = build_player_features(players, targets())
    assert frame.feat_player_home_xi_count.iloc[0] == 10
    assert frame.feat_player_home_xi_gk_count.iloc[0] == 0
    assert pd.isna(frame.feat_player_home_pos5_gk_minutes.iloc[0])
    assert details["target_coverage"].query("side == 'home'").position_observed_matches5.iloc[0] == 0


def test_duplicate_player_fixture_and_conflicting_same_date_club_appearances_reject():
    players = history()
    duplicate = pd.concat([players, players.iloc[[0]]], ignore_index=True)
    with pytest.raises(ValueError, match="Duplicate player-fixture"):
        build_player_features(duplicate, targets())
    conflict = players.iloc[[0]].copy()
    conflict["team"] = "Liverpool"
    conflict["match_id"] = "impossible_other_club"
    with pytest.raises(ValueError, match="Conflicting same-date positive"):
        build_player_features(pd.concat([players, conflict], ignore_index=True), targets())


def write_raw_source(root: Path, *, teams_file=True, fixture_table=False):
    league = root / "data/raw/football_data/1617/E0.csv"
    season = root / "data/raw/fpl_archive/2016-17"
    league.parent.mkdir(parents=True)
    (season / "gws").mkdir(parents=True)
    pd.DataFrame([{"Date": "01/08/2016", "HomeTeam": "Arsenal", "AwayTeam": "Chelsea", "FTR": "H"},
                  {"Date": "08/08/2016", "HomeTeam": "Chelsea", "AwayTeam": "Arsenal", "FTR": "A"}]).to_csv(league, index=False)
    rows = []
    for fixture, date in ((1, "2016-08-01"), (2, "2016-08-08")):
        for own_id, player, role in ((1, 10, 1), (2, 20, 4)):
            is_home = (fixture == 1) == (own_id == 1)
            row = {"element": player, "fixture": fixture, "kickoff_time": date + "T15:00:00Z",
                   "was_home": is_home, "opponent_team": 3 - own_id, "minutes": 90}
            row.update({name: 1 for name in FORM_FIELDS})
            rows.append(row)
    pd.DataFrame(rows).to_csv(season / "gws/merged_gw.csv", index=False)
    # These snapshot clubs are deliberately wrong. Only id/element_type is read.
    pd.DataFrame([{"id": 10, "element_type": 1, "team": 99, "total_points": 99999},
                  {"id": 20, "element_type": 4, "team": 99, "total_points": 99999}]).to_csv(season / "players_raw.csv", index=False)
    if teams_file:
        pd.DataFrame([{"id": 1, "name": "Arsenal"}, {"id": 2, "name": "Chelsea"}]).to_csv(season / "teams.csv", index=False)
    if fixture_table:
        pd.DataFrame([{"id": 1, "team_h": 1, "team_a": 2, "kickoff_time": "2016-08-01T15:00:00Z"},
                      {"id": 2, "team_h": 2, "team_a": 1, "kickoff_time": "2016-08-08T15:00:00Z"}]).to_csv(season / "fixtures.csv", index=False)
    return season


@pytest.mark.parametrize("teams_file", [True, False])
def test_loader_uses_actual_fixture_club_and_calendar_not_snapshot_player_club(tmp_path, teams_file):
    season = write_raw_source(tmp_path, teams_file=teams_file)
    players, metadata, sources = load_player_history(tmp_path)
    assert len(players) == 4
    assert players.loc[players.element.eq("10"), "team"].eq("Arsenal").all()
    assert players.loc[players.element.eq("20"), "team"].eq("Chelsea").all()
    assert players.position_source.eq("season_snapshot_position_fallback").all()
    assert metadata["seasons"]["2016-17"]["quarantined_fixtures"] == 0
    assert all(path.is_absolute() and path.is_file() for path in sources)
    assert players.attrs["fixture_calendar"]
    assert players.attrs["fixture_reconciliation"]


def test_native_historical_role_wins_over_snapshot_fallback_and_manager_excluded(tmp_path):
    season = write_raw_source(tmp_path)
    path = season / "gws/merged_gw.csv"
    rows = pd.read_csv(path)
    rows["position"] = ["DEF", "AM", "DEF", "FWD"]
    rows.to_csv(path, index=False)
    # Removing the only away row on fixture1 removes native side consensus,
    # quarantining that fixture; fixture2 still validates normally.
    players, metadata, _ = load_player_history(tmp_path)
    assert players.loc[players.element.eq("10"), "position_type"].eq(2).all()
    assert players.position_source.eq("native_historical_gw_position").all()
    assert metadata["seasons"]["2016-17"]["manager_rows_excluded"] == 1
    assert metadata["seasons"]["2016-17"]["quarantined_fixtures"] == 1


def test_postponed_zero_minute_placeholder_and_exact_duplicates_do_not_duplicate_matches(tmp_path):
    season = write_raw_source(tmp_path)
    path = season / "gws/merged_gw.csv"
    rows = pd.read_csv(path)
    placeholder = rows.loc[rows.fixture.eq(1)].copy()
    placeholder["kickoff_time"] = "2016-07-15T15:00:00Z"
    placeholder[["minutes", *FORM_FIELDS]] = 0
    pd.concat([rows, rows.iloc[[0]], placeholder]).to_csv(path, index=False)
    players, metadata, _ = load_player_history(tmp_path)
    assert len(players) == 4 and players.match_id.nunique() == 2
    counts = metadata["seasons"]["2016-17"]
    assert counts["identical_rows_removed"] == 1
    assert counts["zero_minute_postponed_placeholder_rows_removed"] == 2


def test_conflicting_raw_fixture_evidence_quarantines_whole_fixture(tmp_path):
    season = write_raw_source(tmp_path, fixture_table=True)
    path = season / "fixtures.csv"
    fixtures = pd.read_csv(path)
    fixtures.loc[0, "team_h"] = 2
    fixtures.to_csv(path, index=False)
    players, metadata, _ = load_player_history(tmp_path)
    assert set(players.fixture) == {"2"}
    audit = pd.DataFrame(players.attrs["fixture_reconciliation"])
    bad = audit.loc[audit.fixture.eq("1")].iloc[0]
    assert not bad.eligible and "raw_fixture_table_identity_conflict" in bad.reason


def test_conflicting_duplicate_performance_quarantines_fixture_instead_of_picking_first(tmp_path):
    season = write_raw_source(tmp_path)
    path = season / "gws/merged_gw.csv"
    rows = pd.read_csv(path)
    conflict = rows.iloc[[0]].copy()
    conflict["minutes"] = 30
    pd.concat([rows, conflict]).to_csv(path, index=False)
    players, metadata, _ = load_player_history(tmp_path)
    assert set(players.fixture) == {"2"}
    assert metadata["seasons"]["2016-17"]["quarantined_fixtures"] == 1


def test_feature_builder_does_not_mutate_source_frame_or_calendar():
    players = history()
    before = players.copy(deep=True)
    attrs = deepcopy(players.attrs)
    build_player_features(players, targets())
    pd.testing.assert_frame_equal(players, before)
    assert players.attrs == attrs


def live_snapshot(parent):
    directory = parent / "snapshot" / "normalized"
    directory.mkdir(parents=True)
    fixture = {"match_id": "fpl_2026-27_1", "fpl_fixture_id": 1, "season": "2026-27",
               "match_date": "2026-10-17", "home_team": "Arsenal", "away_team": "Chelsea", "finished": True}
    pd.DataFrame([fixture]).to_parquet(directory / "fixtures.parquet", index=False)
    rows = []
    for element, team, opponent, home in ((10, "Arsenal", "Chelsea", True), (20, "Chelsea", "Arsenal", False)):
        row = {"element": element, "fixture": 1, "season": "2026-27", "kickoff_time": "2026-10-17T14:00:00Z",
               "canonical_team": team, "opponent_name": opponent, "was_home": home,
               "history_identity_valid": True, "position_type": 1, "minutes": 90}
        row.update({field: 1. for field in FORM_FIELDS})
        rows.append(row)
    pd.DataFrame(rows).to_parquet(directory / "player_history.parquet", index=False)
    return directory.parent


def test_only_explicit_completed_valid_live_history_extends_current_season(tmp_path):
    write_raw_source(tmp_path / "data_root")
    snapshot = live_snapshot(tmp_path)
    historical, _, _ = load_player_history(tmp_path / "data_root")
    assert not historical.season.eq("2026-27").any()
    players, metadata, sources = load_player_history(tmp_path / "data_root", live_snapshot=snapshot)
    current = players.loc[players.season.eq("2026-27")]
    assert len(current) == 2 and set(current.team) == {"Arsenal", "Chelsea"}
    assert current.position_source.eq("live_history_snapshot_position_proxy").all()
    assert len([path for path in sources if snapshot in path.parents]) == 2
    result, _, _ = build_player_features(players, targets("2026-10-23", "2026-27"))
    assert result.feat_player_home_observed_matches5.iloc[0] == 1
    assert result.audit_player_home_latest_source_date.iloc[0] == pd.Timestamp("2026-10-17")


@pytest.mark.parametrize("corruption", ["unfinished", "club", "season"])
def test_invalid_live_identity_quarantines_all_players_in_fixture(tmp_path, corruption):
    write_raw_source(tmp_path / "data_root")
    snapshot = live_snapshot(tmp_path)
    if corruption in {"unfinished", "season"}:
        path = snapshot / "normalized/fixtures.parquet"
        frame = pd.read_parquet(path)
        frame["finished" if corruption == "unfinished" else "season"] = False if corruption == "unfinished" else "2025-26"
    else:
        path = snapshot / "normalized/player_history.parquet"
        frame = pd.read_parquet(path)
        frame.loc[0, "canonical_team"] = "Liverpool"
    frame.to_parquet(path, index=False)
    players, metadata, _ = load_player_history(tmp_path / "data_root", live_snapshot=snapshot)
    assert not players.season.eq("2026-27").any()
    assert metadata["seasons"]["2026-27"]["quarantined_fixtures"] == 1
