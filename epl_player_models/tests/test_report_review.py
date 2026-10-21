import pandas as pd
import pytest

from epl_player_models.report_review import coverage_table, markdown


def coverage():
    return pd.DataFrame([{"season": season, "side": side, "target_sides": 368,
        "history_available_fraction": .97, "mean_observed_matches5": 4.6,
        "mean_observed_matches10": 8.5, "full_projected_xi_fraction": .8,
        "mean_projected_players": 10.5} for season in ("2016-17", "2022-23", "2023-24", "2024-25", "2025-26") for side in ("home", "away")])


def test_native_aggregate_coverage_displays_all_four_evaluation_seasons_and_measures():
    table = coverage_table({"feature_coverage": coverage()})
    assert len(table) == 8 and set(table.Season) == {"2022-23", "2023-24", "2024-25", "2025-26"}
    assert table["Full projected\nXI"].eq("80.00%").all()
    assert table["Mean observed\nslots / 5"].eq("4.60").all()


def test_missing_coverage_season_is_rejected():
    with pytest.raises(ValueError, match="both sides"):
        coverage_table({"feature_coverage": coverage().iloc[:-1]})


def test_markdown_literal_pipes_do_not_create_extra_columns_or_mutate_source():
    frame = pd.DataFrame({"Model": ["Player form | Logistic"], "Score": [1.02]})
    pages = [{"title": "Scores", "blocks": [{"type": "table", "frame": frame, "caption": "Comparison"}]}]
    text = markdown(pages, [])
    assert "Player form &#124; Logistic" in text
    assert frame.Model.iloc[0] == "Player form | Logistic"
