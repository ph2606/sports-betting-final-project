"""Temporal invariance and opponent-history tests using isolated snapshots."""
from __future__ import annotations

import copy
import hashlib
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from epl_modeling.features import build_features


FOCAL = {"Arsenal", "Chelsea", "Coventry"}
CANONICAL = {"Coventry": "Coventry City", "West Ham": "West Ham United", "Wolves": "Wolverhampton Wanderers"}


def _identifier(season, home, away):
    return "fd_" + hashlib.sha256(f"{season}|E0|{home}|{away}".encode()).hexdigest()[:24]


def _games():
    return [
        {"Date": "28/07/2023", "HomeTeam": "West Ham", "AwayTeam": "Wolves", "FTHG": 3, "FTAG": 0, "FTR": "H"},
        {"Date": "01/08/2023", "HomeTeam": "Arsenal", "AwayTeam": "West Ham", "FTHG": 0, "FTAG": 1, "FTR": "A", "us_h": 1.25, "fpl_h": 30},
        {"Date": "08/08/2023", "HomeTeam": "Arsenal", "AwayTeam": "Coventry", "FTHG": 2, "FTAG": 0, "FTR": "H", "us_h": 900, "fpl_h": 100},
        {"Date": "08/08/2023", "HomeTeam": "Arsenal", "AwayTeam": "Chelsea", "FTHG": 9, "FTAG": 0, "FTR": "H", "us_h": 800, "fpl_h": 300},
        {"Date": "15/08/2023", "HomeTeam": "Chelsea", "AwayTeam": "Arsenal", "FTHG": 0, "FTAG": 4, "FTR": "A", "us_h": 2, "fpl_h": 77},
    ]


def _save(root, games, prior=None, advanced=True):
    """Write only files inside the test's temporary snapshot directory."""
    processed = root / "data" / "processed"
    raw = root / "data" / "raw" / "football_data"
    cohorts, native_us, links, players = [], [], [], []
    seasons = {2023: games}
    if prior is not None:
        seasons[2022] = prior
    fixture = 0
    for year, records in sorted(seasons.items()):
        season = f"{year}-{(year+1)%100:02d}"
        code = f"{year%100:02d}{(year+1)%100:02d}"
        league = []
        for original in records:
            row = {"Div": "E0", "HS": 10, "AS": 12, "HST": 3, "AST": 4, "HC": 4, "AC": 5,
                   "HF": 12, "AF": 10, "HY": 1, "AY": 2, "HR": 0, "AR": 0, **original}
            native = {key: value for key, value in row.items() if not key.startswith(("us_", "fpl_"))}
            league.append(native)
            home, away = row["HomeTeam"], row["AwayTeam"]
            if not ({home, away} & FOCAL):
                continue
            match_id = _identifier(season, home, away)
            day = pd.to_datetime(row["Date"], dayfirst=True).strftime("%Y-%m-%d")
            cohorts.append({**native, "season": season, "season_start_year": year,
                            "division": "E0", "match_date": day, "source_match_key": match_id,
                            "source_file": f"{code}/E0.csv"})
            fixture += 1
            links.append({"source_match_key": match_id, "understat_id": fixture})
            native_us.append({"id": fixture, "season": season, "datetime": day+" 15:00:00",
                              "h__title": home, "a__title": away, "isResult": True,
                              "xG__h": row.get("us_h", 0.5), "xG__a": row.get("us_a", 0.75)})
            if year == 2023:
                for side, team, opponent in (("h", home, away), ("a", away, home)):
                    if team in FOCAL:
                        players.append({"season": season, "fixture": fixture,
                                        "element": {"Arsenal": 1, "Chelsea": 2, "Coventry": 3}[team],
                                        "kickoff_time": day+"T15:00:00Z", "was_home": side=="h",
                                        "canonical_team": CANONICAL.get(team, team),
                                        "opponent_name": CANONICAL.get(opponent, opponent),
                                        "minutes": 90, "total_points": row.get("fpl_"+side, 20)})
        folder = raw / code
        folder.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(league).to_csv(folder / "E0.csv", index=False)
    for folder in ("football_data", "integrated", "understat", "fpl_current"):
        (processed / folder).mkdir(parents=True, exist_ok=True)
    pd.DataFrame(cohorts).to_csv(processed / "football_data" / "matches_current_cohort.csv", index=False)
    if advanced:
        pd.DataFrame(links).to_csv(processed / "integrated" / "match_source_links.csv", index=False)
        pd.DataFrame(native_us).to_csv(processed / "understat" / "matches.csv", index=False)
        pd.DataFrame(players).to_csv(processed / "fpl_current" / "player_match_history.csv", index=False)


class FeatureTimingTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)

    def test_same_date_results_and_advanced_statistics_do_not_enter_each_other(self):
        _save(self.root, _games())
        frame, metadata = build_features(self.root)
        same_day = frame[frame.match_date.eq(pd.Timestamp("2023-08-08"))]
        self.assertEqual(len(same_day), 2)
        for _, row in same_day.iterrows():
            self.assertEqual(row.feat_home_std_matches, 1)
            self.assertEqual(row.feat_home_std_goals_for, 0)
            self.assertEqual(row.feat_home_std_goals_diff, -1)
            self.assertEqual(row.feat_home_roll5_goals_for, 0)
            self.assertEqual(row.feat_home_std_us_xg_for, 1.25)
            self.assertEqual(row.feat_home_std_fpl_total_points, 30)
            self.assertEqual(row.audit_home_fd_latest_prior_date, pd.Timestamp("2023-08-01"))
            self.assertEqual(row.audit_home_us_latest_prior_date, pd.Timestamp("2023-08-01"))
            self.assertEqual(row.audit_home_fpl_latest_prior_date, pd.Timestamp("2023-08-01"))
        self.assertTrue(all(value == 0 for value in metadata["leakage_checks"]["latest_prior_date_violations"].values()))

    def test_future_outcome_and_source_stat_mutations_leave_earlier_features_unchanged(self):
        games = _games()
        _save(self.root, games)
        original, _ = build_features(self.root)
        changed = copy.deepcopy(games)
        changed[-1].update(FTHG=50, FTAG=0, FTR="H", HS=1000, AS=0, HY=30, us_h=12345, fpl_h=54321)
        _save(self.root, changed)
        mutated, _ = build_features(self.root)
        features = [column for column in original if column.startswith("feat_")]
        cutoff = pd.Timestamp("2023-08-08")
        left = original[original.match_date.le(cutoff)].set_index("match_id")[features].sort_index()
        right = mutated[mutated.match_date.le(cutoff)].set_index("match_id")[features].sort_index()
        pd.testing.assert_frame_equal(left, right)
        # The mutated match also cannot consume its own changed outcome.
        pd.testing.assert_frame_equal(original.set_index("match_id")[features].sort_index(),
                                      mutated.set_index("match_id")[features].sort_index())

    def test_noncohort_raw_matches_supply_opponent_history_but_are_not_exported(self):
        _save(self.root, _games(), advanced=False)
        frame, metadata = build_features(self.root)
        first = frame[frame.match_date.eq(pd.Timestamp("2023-08-01"))].iloc[0]
        self.assertEqual(first.away_team, "West Ham United")
        self.assertEqual(first.feat_away_std_goals_for, 3)
        self.assertEqual(first.feat_away_roll5_win, 1)
        excluded_id = _identifier("2023-24", "West Ham", "Wolves")
        self.assertNotIn(excluded_id, set(frame.match_id))
        self.assertEqual(len(frame), 4)
        self.assertEqual(metadata["history_scope"]["full_raw_e0_matches"], 5)

    def test_prior_season_promoted_and_unknown_archive_flags_remain_distinct(self):
        prior = [{"Date": "01/08/2022", "HomeTeam": "Arsenal", "AwayTeam": "Chelsea", "FTHG": 1, "FTAG": 0, "FTR": "H"}]
        _save(self.root, _games(), prior=prior, advanced=False)
        frame, _ = build_features(self.root)
        current = frame[frame.away_team.eq("Coventry City")].iloc[0]
        self.assertEqual(current.feat_home_prior_season_win_pct, 1)
        self.assertEqual(current.feat_home_promoted_from_outside_epl, 0)
        self.assertTrue(np.isnan(current.feat_away_prior_season_win_pct))
        self.assertEqual(current.feat_away_prior_season_missing, 1)
        self.assertEqual(current.feat_away_prior_season_archive_missing, 0)
        self.assertEqual(current.feat_away_promoted_from_outside_epl, 1)
        earliest = frame[frame.season.eq("2022-23")].iloc[0]
        self.assertEqual(earliest.feat_home_prior_season_archive_missing, 1)
        self.assertTrue(np.isnan(earliest.feat_home_promoted_from_outside_epl))

    def test_source_date_mismatch_keeps_target_and_does_not_guess_a_link(self):
        _save(self.root, _games())
        path = self.root / "data" / "processed" / "understat" / "matches.csv"
        source = pd.read_csv(path)
        source.loc[source.id.eq(1), "datetime"] = "2023-07-31 15:00:00"
        source.to_csv(path, index=False)
        frame, metadata = build_features(self.root)
        first = frame[frame.match_date.eq(pd.Timestamp("2023-08-01"))].iloc[0]
        self.assertTrue(first.audit_understat_target_exact_link_missing)
        next_matches = frame[frame.match_date.eq(pd.Timestamp("2023-08-08"))]
        self.assertTrue(next_matches.feat_home_std_us_xg_for.isna().all())
        self.assertTrue(next_matches.feat_home_us_history_missing.eq(1).all())
        self.assertEqual(len(frame), 4)
        self.assertEqual(metadata["coverage"]["understat"]["rejected_identity_or_date_rows"], 1)


if __name__ == "__main__":
    unittest.main()
