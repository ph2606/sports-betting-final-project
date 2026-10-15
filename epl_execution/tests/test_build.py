from copy import deepcopy

import pandas as pd
import pytest

from epl_execution.build import checked_output, comparison, ledger_metadata, metric_row


def account():
    return {"account_id": "continuous:S019:2022-26", "scope": "continuous",
        "season": "2022-26", "episode_id": "continuous_2022_26",
        "config": {"strategy_id": "S019", "odds_mode": "best", "model_key": "logit_team_xg",
            "consensus_model_keys": ["a", "b"], "study_status": "frozen"}}


def test_run_path_cannot_overwrite_preserved_studies_or_existing_run(tmp_path):
    with pytest.raises(ValueError):
        checked_output(tmp_path / "epl_strategy_validation/results/new", root=tmp_path)
    with pytest.raises(ValueError):
        checked_output(tmp_path / "epl_execution/results", root=tmp_path)
    run = tmp_path / "epl_execution/results/new"
    assert checked_output(run, root=tmp_path) == run
    run.mkdir(parents=True)
    with pytest.raises(FileExistsError): checked_output(run, root=tmp_path)


def test_continuous_export_metadata_preserves_native_seasons():
    native = pd.DataFrame({"season": ["2022-23", "2025-26"], "stake": [1000., 1000.]})
    exported = ledger_metadata(native, account(), "reference_replay")
    assert exported.season.tolist() == ["2022-23", "2025-26"]
    assert exported.scope_season.eq("2022-26").all()
    assert "scope_season" not in native


def test_reference_row_preserves_original_quote_mode_and_frozen_definition():
    item = account(); before = deepcopy(item)
    row = metric_row(item, {"profit": 20., "funding_feasible": True}, "reference_replay")
    assert row["odds_mode"] == "reference"
    assert row["frozen_original_odds_mode"] == "best"
    assert row["verified_execution"] is False
    assert item == before


def test_trade_changes_distinguish_changed_sides_from_dropped_matches():
    old = pd.DataFrame({"match_id": ["a", "b", "c"], "selection": ["H", "D", "A"]})
    new = pd.DataFrame({"match_id": ["a", "b", "d"], "selection": ["H", "A", "D"]})
    original = {"profit": 50.}
    reference = {"profit": -20.}
    fixed = {"actual_quote_uplift_units": 70., "model_expected_quote_uplift_units": 40.,
        "funding_feasible": False, "minimum_additional_opening_cash_units": 8.,
        "first_shortfall_date": "2025-01-01", "shadow_final_balance": 99980.,
        "shadow_min_balance": 90000., "shadow_return": -.0002, "profit": -20.}
    row = comparison(account(), original, reference, fixed, old, new)
    assert row["retained_same_outcome_bets"] == 1
    assert row["changed_outcome_bets"] == 1
    assert row["original_only_matches"] == row["reference_only_matches"] == 1
    assert row["reference_minus_original_profit"] == -70.
    assert row["fixed_minimum_additional_opening_cash_units"] == 8.
