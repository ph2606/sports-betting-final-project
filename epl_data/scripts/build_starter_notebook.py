"""Generate a small, executable data inspection notebook; no model fitting."""
from __future__ import annotations

import nbformat as nbf

from common import ROOT


def main():
    notebook = nbf.v4.new_notebook()
    md, code = nbf.v4.new_markdown_cell, nbf.v4.new_code_cell
    notebook.cells = [
        md('# English Premier League data — collection phase\n\n'
           'Data for the 20 clubs in the 2026/27 Premier League, as requested on October 6, 2026. '
           'This starts the EPL component of the September 30 NBA/EPL calibrated betting proposal. '
           'The notebook inspects collected data; no probabilities, returns or arbitrage claims have been fitted. '
           'Read `README.md` and `SOURCE_GUIDE.md` before constructing historical predictors.'),
        code("from pathlib import Path\nimport pandas as pd\n\n"
             "candidates = [Path.cwd(), Path.cwd() / 'final_project' / 'epl_data', Path.cwd() / 'epl_data']\n"
             "ROOT = next(path for path in candidates if (path / 'metadata' / 'current_teams.csv').exists())\n"
             "def load(source, table):\n    return pd.read_parquet(ROOT / 'data' / 'processed' / source / f'{table}.parquet')\n"
             "pd.set_option('display.max_columns', 25)"),
        code("catalog = pd.read_csv(ROOT / 'metadata' / 'dataset_catalog.csv')\n"
             "display(catalog[['source', 'table', 'rows', 'columns', 'season_min', 'season_max']])"),
        code("teams = pd.read_csv(ROOT / 'metadata' / 'team_identity_crosswalk.csv')\n"
             "assert len(teams) == 20 and teams['team'].is_unique\n"
             "assert not teams['team'].str.contains('West Ham|Burnley|Wolverhampton', case=False).any()\n"
             "display(teams)"),
        md('## Current player and availability snapshots\n\n'
           'The primary player master starts from all FPL-listed entries, including unavailable players. '
           '`can_select` identifies selectable entries. Transfermarkt links are conservative and unmatched '
           'players remain in the FPL universe. Current news, market values and injuries describe retrieval time.'),
        code("players = load('integrated', 'current_player_master')\n"
             "print(f'FPL-listed: {len(players):,}; selectable: {int(players.can_select.sum()):,}')\n"
             "display(players.groupby('team').agg(listed=('fpl_player_id', 'size'), selectable=('can_select', 'sum')))\n"
             "columns = ['team', 'player_name', 'position_name', 'can_select', 'status', 'news', 'minutes',\n"
             "           'goals_scored', 'assists', 'expected_goals', 'expected_assists', 'tm_market_value_eur']\n"
             "display(players[[column for column in columns if column in players]].head(20))"),
        md('## Historical team matches and bookmaker odds\n\n'
           'Use E0 for Premier League modeling. E1/E2/E3 retain lower-division history for these clubs. '
           'Source date coverage is measured from the downloaded records; missing values remain missing.'),
        code("matches = load('football_data', 'matches_current_cohort')\n"
             "epl = matches.loc[matches['division'].eq('E0')].copy()\n"
             "display(epl.groupby('season').agg(matches=('source_match_key', 'size'), first=('match_date', 'min'), last=('match_date', 'max')))\n"
             "odds = load('football_data', 'match_odds_1x2_long')\n"
             "display(odds.head())"),
        code("features = load('football_data', 'team_match_lagged_features')\n"
             "known = features['features_last_match_date'].notna()\n"
             "assert (features.loc[known, 'features_last_match_date'] < features.loc[known, 'match_date']).all()\n"
             "display(features.head())"),
        md('## Historical player fixtures\n\n'
           'Historical club attribution follows the actual fixture, preserving transfers. The archive current-season '
           'GW1 overlaps official FPL; use official histories for 2026/27 when combining. Zero-minute fantasy '
           'records are preserved; filter `minutes > 0` for actual appearances. Match statistics must be lagged.'),
        code("historical = load('fpl_archive', 'player_gameweeks')\n"
             "current = load('fpl_current', 'player_match_history')\n"
             "player_history = pd.concat([historical.loc[historical['season'].ne('2026-27')], current], ignore_index=True, sort=False)\n"
             "assert not player_history.duplicated(['season', 'element', 'fixture']).any()\n"
             "display(player_history.groupby('season').agg(records=('element', 'size'), players=('element', 'nunique'), clubs=('canonical_team', 'nunique')))"),
        md('## Advanced expected-goals data and coverage\n\n'
           'Different providers use different xG definitions. Full-season player summaries, detailed shots, '
           'lineups and historical values are descriptive records, not pre-match forecasts.'),
        code("xg = load('understat', 'team_match_metrics')\n"
             "display(xg.head())\n"
             "display(pd.read_csv(ROOT / 'metadata' / 'quality_checks.csv'))"),
        md('## Next modeling step\n\n'
           'Choose past-season training/validation/test blocks, use only earlier completed match statistics, '
           'and compare calibration-driven versus accuracy-driven models on identical fixtures. '
           'Preserve the distinction between preclosing and closing odds. The collected static bookmaker '
           'snapshots do not establish synchronized executable arbitrage.'),
    ]
    notebook.metadata = {'kernelspec': {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'},
                         'language_info': {'name': 'python', 'version': '3.12'}}
    nbf.write(notebook, ROOT / '01_data_inventory.ipynb')
    print(ROOT / '01_data_inventory.ipynb')


if __name__ == '__main__':
    main()
