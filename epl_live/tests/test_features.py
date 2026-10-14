import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import pandas as pd

from epl_live.features import _current_league, build_live_features
from epl_modeling import features as history


class LiveFeatureTests(unittest.TestCase):
    def test_future_completed_source_rows_cannot_inform_an_earlier_creation(self):
        with tempfile.TemporaryDirectory() as folder:
            snapshot = Path(folder)
            raw = snapshot / 'raw/football_data/E0.csv'
            raw.parent.mkdir(parents=True)
            header = 'Div,Date,HomeTeam,AwayTeam,FTHG,FTAG,FTR\n'
            raw.write_text(header + 'E0,10/10/2026,Arsenal,Liverpool,2,0,H\nE0,16/10/2026,Liverpool,Arsenal,99,0,H\n')
            old_league = _current_league(raw).iloc[:1].copy()
            (snapshot / 'manifest.json').write_text(json.dumps({'usable': True, 'snapshot_completed_at_utc': '2026-10-14T09:00:00Z', 'fpl_player_summaries_complete': True}))
            normalized = snapshot / 'normalized'
            normalized.mkdir()
            fixtures = pd.DataFrame({'kickoff_utc':['2026-10-17T14:00:00Z'], 'finished':[False]})
            fixtures.to_parquet(normalized/'fixtures.parquet')
            target = pd.DataFrame({'match_id':['fpl_2026-27_70'], 'season':['2026-27'],
                                   'match_date':pd.to_datetime(['2026-10-17']),
                                   'home_team':['Liverpool'], 'away_team':['Arsenal']})
            us = pd.DataFrame(columns=['match_id','team',*history.US_METRICS])
            fpl = pd.DataFrame(columns=['match_id','team',*history.FPL_METRICS])
            with patch('epl_live.features.historical._table',return_value=pd.DataFrame()), \
                 patch('epl_live.features.historical._read_league_files',return_value=(old_league,{})), \
                 patch('epl_live.features.historical._understat_history',return_value=(us,{})), \
                 patch('epl_live.features.reconcile_fpl_opponents',return_value=(pd.DataFrame(),pd.DataFrame(),{})), \
                 patch('epl_live.features._supplemental_history',return_value=(fpl,{})):
                frame, meta = build_live_features(snapshot, snapshot, target)
            self.assertEqual(frame.iloc[0].feat_home_roll10_goals_for, 0)
            self.assertEqual(frame.iloc[0].feat_away_roll10_goals_for, 2)
            self.assertEqual(frame.iloc[0].audit_home_fd_latest_prior_date, pd.Timestamp('2026-10-10'))
            self.assertEqual(meta['current_completed_e0_matches'], 1)
            self.assertEqual(meta['feature_latest_date_violations'], 0)

    def test_invalid_snapshot_is_rejected_before_feature_reads(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)
            (p/'manifest.json').write_text('{"usable":false}')
            with self.assertRaises(ValueError):
                build_live_features(p,p,pd.DataFrame())


if __name__ == '__main__':
    unittest.main()
