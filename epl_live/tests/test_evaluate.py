import unittest

from epl_live.evaluate import score_forecasts


def forecast(version=1, probabilities=None):
    return {'model_id':'model_a','match_id':'fpl_2026-27_70','update_version':version,
            'season':'2026-27','home_team':'Tottenham Hotspur','away_team':'Coventry City',
            'created_at_utc':f'2026-10-{14+version:02d}T09:00:00Z','kickoff_utc':'2026-10-19T19:00:00Z',
            'feature_group':'team','probabilities':probabilities or {'H':0.6,'D':0.2,'A':0.2}}


class EvaluationTests(unittest.TestCase):
    def test_no_resolved_games_does_not_create_zero_performance(self):
        predictions, scores = score_forecasts([forecast()], [])
        self.assertTrue(predictions.empty)
        self.assertTrue(scores.empty)
        self.assertIn('log_loss', scores)

    def test_earliest_release_is_scored_without_hindsight_replacement(self):
        outcome={'match_id':'fpl_2026-27_70','result':'H','settled_at_utc':'2026-10-19T21:00:00Z',
                 'season':'2026-27','home_team':'Tottenham Hotspur','away_team':'Coventry City'}
        predictions, scores = score_forecasts([forecast(),forecast(2,{'H':0.99,'D':0.005,'A':0.005})],[outcome])
        self.assertEqual(len(predictions),1)
        self.assertEqual(predictions.iloc[0].p_H,0.6)
        self.assertAlmostEqual(scores.iloc[0].log_loss,0.5108256238)

    def test_settlement_before_kickoff_is_rejected(self):
        with self.assertRaises(ValueError):
            score_forecasts([forecast()],[{'match_id':'fpl_2026-27_70','result':'H','settled_at_utc':'2026-10-18T21:00:00Z',
                                        'season':'2026-27','home_team':'Tottenham Hotspur','away_team':'Coventry City'}])


if __name__ == '__main__':
    unittest.main()
