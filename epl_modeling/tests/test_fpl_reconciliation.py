"""Exact identity repair, conflict quarantine, and read-only integration tests."""
from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from epl_modeling import features
from epl_modeling.fpl_reconciliation import build_reconciled_features, reconcile_fpl_opponents
from epl_modeling.tests.test_features import _games, _save


IDS = {"Arsenal": 1, "Chelsea": 2, "Coventry City": 3, "West Ham United": 4, "Wolverhampton Wanderers": 5}


def _snapshot(root, ambiguous=False):
    games = _games() if ambiguous else [_games()[position] for position in (0, 1, 3, 4)]
    _save(root, games)
    path = root / "data/processed/fpl_current/player_match_history.csv"
    players = pd.read_csv(path)
    players["team_at_fixture_id"] = players.canonical_team.map(IDS)
    players["opponent_team"] = players.opponent_name.map(IDS)
    teams_path = root / "data/processed/fpl_current/teams.csv"
    pd.DataFrame([{"id": team_id, "name": name, "code": team_id+100} for name, team_id in IDS.items()]).to_csv(teams_path, index=False)
    fixtures = []
    for fixture, group in players.groupby("fixture"):
        row = group.iloc[0]
        own, opponent = int(row.team_at_fixture_id), int(row.opponent_team)
        home, away = (own, opponent) if row.was_home else (opponent, own)
        fixtures.append({"id": int(fixture), "team_h": home, "team_a": away, "kickoff_time": row.kickoff_time})
    raw = root / "data/raw/fpl_current"
    raw.mkdir(parents=True, exist_ok=True)
    (raw / "fixtures.json").write_text(json.dumps(fixtures), encoding="utf-8")
    players.loc[players.fixture.eq(1), "opponent_name"] = pd.NA
    players.to_csv(path, index=False)
    return path


def _hashes(root):
    return {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in root.rglob("*") if path.is_file()}


class FPLReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)

    def test_missing_name_repairs_only_exact_unique_identity_and_preserves_element(self):
        path = _snapshot(self.root)
        original = pd.read_csv(path)
        repaired, audit, metadata = reconcile_fpl_opponents(self.root)
        first = repaired[repaired.fixture.eq(1)].iloc[0]
        self.assertEqual(first.opponent_name, "West Ham United")
        self.assertTrue(pd.isna(first.opponent_name_original))
        self.assertTrue(first.reconciliation_eligible)
        self.assertEqual(first.reconciliation_status, "repaired_missing_opponent")
        pd.testing.assert_series_equal(original.element.reset_index(drop=True), repaired.element.reset_index(drop=True), check_names=False)
        self.assertEqual(metadata["missing_opponent_repaired"], 1)
        self.assertEqual(metadata["conflict_or_unresolved_rows"], 0)
        self.assertTrue(audit.independent_opponent_id_name_agrees.dropna().all())

    def test_ambiguous_same_date_club_venue_candidates_are_not_narrowed_by_known_name(self):
        _snapshot(self.root, ambiguous=True)
        repaired, audit, metadata = reconcile_fpl_opponents(self.root)
        home_rows = audit[audit.kickoff_time.str.startswith("2023-08-08") & audit.canonical_team.eq("Arsenal")]
        self.assertTrue(home_rows.candidate_count.eq(2).all())
        self.assertFalse(home_rows.reconciliation_eligible.any())
        self.assertTrue(home_rows.reconciliation_reason.str.contains("ambiguous_exact").all())
        self.assertGreater(metadata["quarantined_fpl_fixtures"], 0)
        self.assertEqual(len(repaired), len(audit))

    def test_known_opponent_conflict_quarantines_same_fixture_peers(self):
        path = _snapshot(self.root)
        players = pd.read_csv(path)
        mask = players.fixture.eq(2) & players.canonical_team.eq("Arsenal")
        players.loc[mask, "opponent_name"] = "Coventry City"
        players.to_csv(path, index=False)
        repaired, audit, _ = reconcile_fpl_opponents(self.root)
        fixture = audit[audit.fixture.eq(2)]
        self.assertEqual(len(fixture), 2)
        self.assertFalse(fixture.reconciliation_eligible.any())
        self.assertTrue(fixture.reconciliation_reason.str.contains("known_opponent_name_conflict|same_fixture_peer").all())
        self.assertEqual(repaired.loc[mask, "opponent_name"].iloc[0], "Coventry City")

    def test_independent_season_opponent_id_conflict_prevents_repair(self):
        path = _snapshot(self.root)
        players = pd.read_csv(path)
        players.loc[players.fixture.eq(1), "opponent_team"] = IDS["Coventry City"]
        players.to_csv(path, index=False)
        repaired, audit, _ = reconcile_fpl_opponents(self.root)
        first = audit[audit.fixture.eq(1)].iloc[0]
        self.assertFalse(first.reconciliation_eligible)
        self.assertIn("opponent_team_id_name_lookup_conflict", first.reconciliation_reason)
        self.assertIn("official_fixture_table_opponent_id_conflict", first.reconciliation_reason)
        self.assertTrue(pd.isna(repaired[repaired.fixture.eq(1)].iloc[0].opponent_name))

    def test_nearby_date_is_unresolved_and_is_not_shifted(self):
        path = _snapshot(self.root)
        players = pd.read_csv(path)
        players.loc[players.fixture.eq(1), "kickoff_time"] = "2023-08-02T15:00:00Z"
        players.to_csv(path, index=False)
        repaired, audit, _ = reconcile_fpl_opponents(self.root)
        first = audit[audit.fixture.eq(1)].iloc[0]
        self.assertEqual(first.candidate_count, 0)
        self.assertFalse(first.reconciliation_eligible)
        self.assertIn("no_exact_calendar_club_venue_candidate", first.reconciliation_reason)
        self.assertEqual(repaired[repaired.fixture.eq(1)].iloc[0].kickoff_time, "2023-08-02T15:00:00Z")

    def test_current_precedence_manager_exclusion_and_duplicate_quarantine(self):
        path = _snapshot(self.root)
        players = pd.read_csv(path)
        archive = self.root / "data/processed/fpl_archive"
        archive.mkdir(parents=True, exist_ok=True)
        old = players.copy()
        old["total_points"] = 9999
        old.to_csv(archive / "player_gameweeks.csv", index=False)
        manager = players.iloc[[0]].copy()
        manager["element"], manager["position_type"] = 99, 5
        pd.concat([players, manager], ignore_index=True).to_csv(path, index=False)
        repaired, _, metadata = reconcile_fpl_opponents(self.root)
        self.assertEqual(metadata["archive_rows_superseded_by_official_season"], len(players))
        self.assertEqual(metadata["assistant_manager_rows_excluded"], 1)
        self.assertFalse(repaired.element.eq(99).any())
        self.assertFalse(repaired.total_points.eq(9999).any())
        pd.concat([players, players.iloc[[0]]], ignore_index=True).to_csv(path, index=False)
        _, audit, _ = reconcile_fpl_opponents(self.root)
        duplicate = audit[audit.fixture.eq(1)]
        self.assertFalse(duplicate.reconciliation_eligible.any())
        self.assertTrue(duplicate.reconciliation_reason.str.contains("duplicate_player_fixture_key").all())

    def test_wrapper_changes_only_fpl_history_without_file_writes_or_global_monkeypatch(self):
        _snapshot(self.root)
        original_hook = features._fpl_history
        initial_hashes = _hashes(self.root)
        original, _ = features.build_features(self.root)
        reconciliation = reconcile_fpl_opponents(self.root)
        revised, metadata = build_reconciled_features(self.root, reconciliation)
        self.assertIs(features._fpl_history, original_hook)
        self.assertEqual(_hashes(self.root), initial_hashes)
        self.assertTrue(metadata["original_fpl_hook_unmodified"])
        baseline = original.set_index("match_id")
        changed = revised.set_index("match_id")
        fd_columns = [column for column in baseline if column.startswith("feat_") and "fpl" not in column]
        pd.testing.assert_frame_equal(baseline[fd_columns].sort_index(), changed[fd_columns].sort_index())
        target = revised[revised.match_date.eq(pd.Timestamp("2023-08-08"))].iloc[0]
        old_target = original[original.match_date.eq(pd.Timestamp("2023-08-08"))].iloc[0]
        self.assertTrue(pd.isna(old_target.feat_home_std_fpl_total_points))
        self.assertEqual(target.feat_home_std_fpl_total_points, 30)
        self.assertEqual(target.audit_home_fpl_latest_prior_date, pd.Timestamp("2023-08-01"))


if __name__ == "__main__":
    unittest.main()
