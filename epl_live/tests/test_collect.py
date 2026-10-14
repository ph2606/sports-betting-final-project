"""Mocked public endpoints: identity, clocks, immutability and quote guards."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

import pandas as pd

from epl_live import collect


class SnapshotCollectorTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 10, 14, 9, 5, tzinfo=timezone.utc)
        expected, _, _ = collect._expected_membership()
        self.teams = [{"id": int(row.fpl_team_id), "code": int(row.fpl_team_code), "name": row.fpl_name}
                      for row in expected.itertuples(index=False)]
        self.bootstrap = {
            "teams": self.teams,
            "events": [{"id": 1, "deadline_time": "2026-08-21T17:30:00Z"},
                       {"id": 38, "deadline_time": "2027-05-30T13:30:00Z"}],
            "elements": [{"id": 101, "team": 1, "element_type": 2, "web_name": "Test One"},
                         {"id": 102, "team": 6, "element_type": 3, "web_name": "Test Two"}],
        }
        self.fixtures = [
            {"id": 1, "team_h": 1, "team_a": 7, "kickoff_time": "2026-08-21T19:00:00Z",
             "finished": True, "started": True, "minutes": 90, "team_h_score": 3, "team_a_score": 0},
            {"id": 2, "team_h": 1, "team_a": 6, "kickoff_time": "2026-10-17T14:00:00Z",
             "finished": False, "started": False, "minutes": 0, "team_h_score": None, "team_a_score": None},
        ]
        self.understat = {
            "teams": {str(row["id"]): {"title": row["name"]} for row in self.teams},
            "dates": [
                {"id": "901", "datetime": "2026-08-21 20:00:00", "h": {"title": "Arsenal"},
                 "a": {"title": "Coventry"}, "xG": {"h": "3.2", "a": "0.5"}, "isResult": True},
                {"id": "902", "datetime": "2026-10-17 15:00:00", "h": {"title": "Arsenal"},
                 "a": {"title": "Chelsea"}, "xG": {"h": None, "a": None}, "isResult": False},
            ],
        }
        # Player 101 is in Arsenal's current registry, but this earlier fixture
        # row is an appearance for Coventry. Club attribution must follow fixture.
        self.summaries = {
            101: {"history": [{"element": 101, "fixture": 1, "kickoff_time": "2026-08-21T19:00:00Z",
                                "was_home": False, "opponent_team": 1, "minutes": 90,
                                "total_points": 4, "bps": 20, "assists": 1}], "history_past": []},
            102: {"history": [], "history_past": []},
        }
        self.e0 = b"Div,Date,HomeTeam,AwayTeam,FTHG,FTAG,FTR\nE0,21/08/2026,Arsenal,Coventry,3,0,H\n"
        self.quote_csv = (
            "Div,Date,HomeTeam,AwayTeam,B365H,B365D,B365A,PSH,PSD,PSA,MaxH,MaxD,MaxA,"
            "BFEH,BFED,BFEA,WHH,WHD,WHA,B365CH,B365CD,B365CA\n"
            "E0,17/10/2026,Arsenal,Chelsea,2,3.5,4,100,100,100,100,100,100,100,100,100,100,inf,100,99,99,99\n"
        ).encode()
        self.overrides = {}
        self.lock = threading.Lock()
        self.active_players = self.peak_players = 0

    def http_get(self, url, **kwargs):
        player = None
        if "/element-summary/" in url:
            player = int(url.rstrip("/").split("/")[-1])
            with self.lock:
                self.active_players += 1
                self.peak_players = max(self.peak_players, self.active_players)
            time.sleep(.01)
        try:
            if url in self.overrides:
                status, content = self.overrides[url]
            elif url.endswith("/bootstrap-static/"):
                status, content = 200, json.dumps(self.bootstrap).encode()
            elif url.endswith("/api/fixtures/"):
                status, content = 200, json.dumps(self.fixtures).encode()
            elif url.endswith("/2627/E0.csv"):
                status, content = 200, self.e0
            elif url.endswith("/fixtures.csv"):
                status, content = 200, self.quote_csv
            elif "getLeagueData/EPL/2026" in url:
                status, content = 200, json.dumps(self.understat).encode()
            elif player is not None:
                status, content = 200, json.dumps(self.summaries.get(player, {"history": []})).encode()
            else:
                raise AssertionError("Unexpected endpoint: " + url)
            return SimpleNamespace(status_code=status, content=content, url=url,
                                   headers={"Date": "Tue, 13 Oct 2026 23:00:00 GMT", "Content-Type": "application/json"})
        finally:
            if player is not None:
                with self.lock:
                    self.active_players -= 1

    def capture(self, root, players=True):
        with patch.object(collect.requests, "get", side_effect=self.http_get) as get:
            with patch.object(collect, "_now", return_value=self.now):
                snapshot = collect.collect_snapshot(root, include_players=players)
        manifest = json.loads((snapshot / "manifest.json").read_text(encoding="utf-8"))
        return snapshot, manifest, get.call_count

    def test_complete_capture_clocks_schema_and_fixture_club_attribution(self):
        with tempfile.TemporaryDirectory() as tmp:
            snapshot, manifest, calls = self.capture(Path(tmp))
            self.assertTrue(manifest["usable"], manifest["errors"])
            self.assertTrue(manifest["fpl_player_summaries_complete"])
            self.assertEqual(calls, 7)
            self.assertEqual(manifest["snapshot_completed_at_utc"], self.now.isoformat())
            self.assertEqual(manifest["freshness"]["fpl_last_completed_match_date"], "2026-08-21")
            self.assertEqual(manifest["freshness"]["football_data_last_completed_match_date"], "2026-08-21")
            for record in manifest["requests"]:
                content = (snapshot / record["path"]).read_bytes()
                self.assertEqual(record["sha256"], hashlib.sha256(content).hexdigest())
                self.assertEqual(record["bytes"], len(content))
                self.assertEqual(record["response_observed_at_utc"], collect._iso(self.now))
                self.assertEqual(record["http_response_date"], "Tue, 13 Oct 2026 23:00:00 GMT")
                self.assertIsNone(record["provider_quote_timestamp_utc"])
            history = pd.read_parquet(snapshot / "normalized/player_history.parquet")
            self.assertEqual(history.iloc[0].canonical_team, "Coventry City")
            self.assertEqual(history.iloc[0].opponent_name, "Arsenal")
            self.assertEqual(history.iloc[0].position_type, 2)
            self.assertTrue(history.iloc[0].history_identity_valid)
            targets = pd.read_parquet(snapshot / "normalized/upcoming_targets.parquet")
            self.assertEqual(targets.match_id.tolist(), ["fpl_2026-27_2"])
            self.assertEqual(len((snapshot / "request_log.jsonl").read_text().splitlines()), 7)

    def test_repeat_capture_is_new_and_preserves_every_previous_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first, _, _ = self.capture(root, players=False)
            hashes = {p.relative_to(first): hashlib.sha256(p.read_bytes()).hexdigest()
                      for p in first.rglob("*") if p.is_file()}
            second, _, _ = self.capture(root, players=False)
            self.assertNotEqual(first, second)
            self.assertEqual(hashes, {p.relative_to(first): hashlib.sha256(p.read_bytes()).hexdigest()
                                      for p in first.rglob("*") if p.is_file()})
            self.assertTrue(first.name.startswith("20261014T090500"))

    def test_membership_mismatch_fails_closed_and_skips_player_requests(self):
        self.bootstrap["teams"][-1] = {"id": 20, "code": 21, "name": "West Ham"}
        with tempfile.TemporaryDirectory() as tmp:
            snapshot, manifest, calls = self.capture(Path(tmp))
            self.assertFalse(manifest["usable"])
            self.assertFalse(manifest["membership_valid"])
            self.assertEqual(calls, 5)
            self.assertTrue(any("membership" in error for error in manifest["errors"]))
            self.assertTrue((snapshot / "raw/fpl/bootstrap-static.json").exists())
            self.assertTrue(pd.read_parquet(snapshot / "normalized/upcoming_targets.parquet").empty)

    def test_season_date_conflict_fails_closed(self):
        self.fixtures[1]["kickoff_time"] = "2025-10-17T14:00:00Z"
        with tempfile.TemporaryDirectory() as tmp:
            _, manifest, calls = self.capture(Path(tmp))
            self.assertFalse(manifest["usable"])
            self.assertFalse(manifest["fpl_schedule_valid"])
            self.assertEqual(calls, 5)
            self.assertTrue(any("season" in error for error in manifest["errors"]))

    def test_http_error_body_is_archived_with_real_status_and_hash(self):
        failed = "https://www.football-data.co.uk/fixtures.csv"
        self.overrides[failed] = (503, b"temporarily unavailable")
        with tempfile.TemporaryDirectory() as tmp:
            snapshot, manifest, _ = self.capture(Path(tmp), players=False)
            self.assertFalse(manifest["usable"])
            record = next(record for record in manifest["requests"] if record["url"] == failed)
            self.assertEqual(record["status"], "http_error")
            self.assertEqual(record["http_status"], 503)
            self.assertEqual((snapshot / record["path"]).read_bytes(), b"temporarily unavailable")

    def test_quotes_are_individual_complete_and_not_publication_timestamps(self):
        with tempfile.TemporaryDirectory() as tmp:
            snapshot, manifest, _ = self.capture(Path(tmp), players=False)
            odds = pd.read_parquet(snapshot / "normalized/individual_odds.parquet")
            self.assertEqual(odds.source_prefix.tolist(), ["B365"])
            self.assertEqual(odds.iloc[0].odds_H, 2.)
            self.assertEqual(odds.iloc[0].odds_D, 3.5)
            self.assertEqual(odds.iloc[0].odds_A, 4.)
            self.assertTrue(odds.quote_publication_time_unknown.all())
            self.assertTrue(odds.provider_quote_timestamp_utc.isna().all())
            self.assertFalse(odds.simultaneous_execution_verified.any())
            self.assertEqual(odds.iloc[0].observed_at_utc, collect._iso(self.now))
            self.assertEqual(manifest["odds_normalization"]["excluded_pinnacle_triplets"], 1)
            self.assertEqual(manifest["odds_normalization"]["invalid_triplets"], 1)

    def test_started_and_past_unfinished_fixtures_cannot_be_targets(self):
        self.fixtures[1]["started"] = True
        self.fixtures.append({"id": 3, "team_h": 6, "team_a": 7, "kickoff_time": "2026-10-13T19:00:00Z",
                              "started": False, "finished": False, "minutes": 0})
        with tempfile.TemporaryDirectory() as tmp:
            snapshot, manifest, _ = self.capture(Path(tmp), players=False)
            self.assertTrue(manifest["usable"], manifest["errors"])
            fixtures = pd.read_parquet(snapshot / "normalized/fixtures.parquet")
            self.assertEqual(len(fixtures), 3)
            self.assertFalse(fixtures.target_eligible.any())
            self.assertTrue(pd.read_parquet(snapshot / "normalized/upcoming_targets.parquet").empty)
            self.assertEqual(manifest["freshness"]["fpl_past_unfinished_fixture_count"], 1)

    def test_partial_player_requests_do_not_claim_complete_player_inputs(self):
        self.overrides[f"{collect.FPL_API}/element-summary/102/"] = (503, b"retry later")
        with tempfile.TemporaryDirectory() as tmp:
            _, manifest, _ = self.capture(Path(tmp))
            self.assertFalse(manifest["fpl_player_summaries_complete"])
            self.assertEqual(manifest["fpl_player_summaries_requested"], 2)
            self.assertEqual(manifest["fpl_player_summaries_downloaded"], 1)

    def test_player_request_concurrency_never_exceeds_six(self):
        self.bootstrap["elements"] = [{"id": number, "team": 1, "element_type": 2} for number in range(101, 115)]
        with tempfile.TemporaryDirectory() as tmp:
            _, manifest, calls = self.capture(Path(tmp))
            self.assertTrue(manifest["fpl_player_summaries_complete"], manifest["errors"])
            self.assertEqual(calls, 19)
            self.assertLessEqual(self.peak_players, 6)
            self.assertGreater(self.peak_players, 1)


if __name__ == "__main__":
    unittest.main()
