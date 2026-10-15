from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from epl_strategy_lab.build import build
from epl_strategy_lab.inputs import SOURCE_FILES
from epl_strategy_lab.tests.test_inputs import write_inputs


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


@pytest.fixture(scope="module")
def completed_export(tmp_path_factory):
    parent = tmp_path_factory.mktemp("strategy_lab_export")
    root = write_inputs(parent / "source_project")
    before = {name: digest(root / name) for name in SOURCE_FILES}
    output = parent / "new_export"
    manifest = build(output, project_root=root, bootstrap_samples=25, generate_report=False)
    return root, output, before, manifest


def test_all_84_strategies_have_complete_common_curves_and_single_100k_account(completed_export):
    root, output, before, manifest = completed_export
    catalog = json.loads((output / "catalog.json").read_text())
    metrics = pd.read_parquet(output / "metrics.parquet")
    bets = pd.read_parquet(output / "bets.parquet")
    equity = pd.read_parquet(output / "equity.parquet")
    graph = pd.read_csv(output / "graph_equity.csv")
    ids = [item["strategy_id"] for item in catalog]
    assert len(ids) == len(set(ids)) == len(metrics) == 84
    assert set(ids) == set(metrics.strategy_id) == set(equity.strategy_id) == set(graph.strategy_id)
    assert equity.groupby("strategy_id").size().eq(113).all()
    assert graph.groupby("strategy_id").size().eq(114).all()
    assert graph.loc[graph.is_initial, "end_bankroll"].eq(100000.).all()
    assert graph.loc[graph.is_initial, "match_date"].eq("2025-08-14").all()
    assert graph.groupby("strategy_id").is_initial.sum().eq(1).all()
    assert metrics.initial_capital_sum_units.eq(100000.).all()
    assert metrics.bankroll_reset_episodes.eq(1).all()
    assert metrics.prediction_count.eq(374).all()
    assert metrics.matched_valid_odds_count.eq(374).all()
    assert equity.episode_id.eq("2025-26").all()
    for sid, curve in equity.groupby("strategy_id"):
        curve = curve.sort_values("match_date")
        trades = bets.loc[bets.strategy_id.eq(sid)]
        summary = metrics.loc[metrics.strategy_id.eq(sid)].iloc[0]
        np.testing.assert_allclose(curve.start_bankroll.iloc[1:], curve.end_bankroll.iloc[:-1], atol=1e-7)
        assert curve.start_bankroll.iloc[0] == 100000.
        assert curve.end_bankroll.iloc[-1] == pytest.approx(100000. + trades.profit.sum(), abs=1e-6)
        assert summary.profit == pytest.approx(trades.profit.sum())
        assert summary.turnover == pytest.approx(trades.stake.sum())
        assert summary.trading_frequency == pytest.approx(len(trades) / 374)
        expected_gain = (trades.probability * trades.stake * (trades.odds - 1)).sum()
        expected_loss = ((1 - trades.probability) * trades.stake).sum()
        assert summary.expected_gain_total_units == pytest.approx(expected_gain)
        assert summary.expected_loss_total_units == pytest.approx(expected_loss)
        assert summary.expected_net_profit_total_units == pytest.approx(expected_gain - expected_loss)
    for item in catalog:
        if item["cash_only"]:
            row = metrics.loc[metrics.strategy_id.eq(item["strategy_id"])].iloc[0]
            assert row.bet_count == 0 and row.profit == 0 and pd.isna(row.hit_ratio) and pd.isna(row.roi)
            assert graph.loc[graph.strategy_id.eq(item["strategy_id"]), "end_bankroll"].eq(100000.).all()
    assert sum(item["cash_only"] for item in catalog) == 8
    assert before == {name: digest(root / name) for name in SOURCE_FILES}
    assert manifest["row_counts"]["metrics"] == 84
    assert manifest["row_counts"]["graph_equity"] == 84 * 114


def test_final_inventory_and_flat_roundtrips_cover_every_saved_artifact(completed_export):
    root, output, before, manifest = completed_export
    saved = json.loads((output / "manifest.json").read_text())
    assert saved == manifest
    assert saved["protected_hashes_unchanged"] is True
    assert saved["config"]["initial_bankroll"] == 100000.
    assert set(saved["source_sha256"]) == set(SOURCE_FILES)
    assert saved["source_sha256"] == before
    assert "manifest.json" not in saved["output_sha256"]
    assert set(saved["output_sha256"]) == {p.relative_to(output).as_posix()
        for p in output.rglob("*") if p.is_file() and p.name != "manifest.json"}
    for relative, sha in saved["output_sha256"].items():
        assert digest(output / relative) == sha
    for name in ("metrics", "bets", "equity"):
        assert len(pd.read_csv(output / f"{name}.csv")) == len(pd.read_parquet(output / f"{name}.parquet"))
    audit = json.loads((output / "inputs_audit.json").read_text())
    assert audit["n_matches"] == 374 and audit["n_match_dates"] == 113
    assert audit["n_strategies"] == 84 and audit["n_original_prediction_series"] == 13
    assert audit["primary_cash_strategies"] == 8 and audit["legacy_diagnostic_strategies"] == 12
    assert audit["ensemble_weights"]["ensemble_market_blend"] == {"logit_combined": .5, "baseline_market_only": .5}
    assert audit["quote_timestamp_missing_counts"]["reference_quote_timestamp_utc"] == 374
    assert audit["execution_verified"] is False


def test_existing_export_cannot_be_overwritten(completed_export):
    root, output, _, _ = completed_export
    before = {path: digest(path) for path in output.rglob("*") if path.is_file()}
    with pytest.raises(FileExistsError, match="Refusing to overwrite"):
        build(output, project_root=root, bootstrap_samples=0, generate_report=False)
    assert before == {path: digest(path) for path in output.rglob("*") if path.is_file()}


def test_source_and_old_study_trees_are_protected_from_new_output(tmp_path):
    root = write_inputs(tmp_path / "project")
    for directory in ("epl_modeling", "epl_data", "epl_live", "epl_strategy", "epl_robustness"):
        with pytest.raises(ValueError, match="preserved source or study tree"):
            build(root / directory / "forbidden_new_output", project_root=root,
                  bootstrap_samples=0, generate_report=False)
        assert not (root / directory / "forbidden_new_output").exists()


def test_missing_common_date_is_not_allowed_to_produce_a_final_export(tmp_path, monkeypatch):
    from epl_strategy_lab import engine
    root = write_inputs(tmp_path / "project")
    original = engine.simulate_strategy
    def omit_date(*args, **kwargs):
        bets, equity = original(*args, **kwargs)
        return bets, equity.iloc[1:]
    monkeypatch.setattr(engine, "simulate_strategy", omit_date)
    output = tmp_path / "incomplete_output"
    with pytest.raises(ValueError, match="every common match date"):
        build(output, project_root=root, bootstrap_samples=0, generate_report=False)
    assert not (output / "manifest.json").exists()


def test_changed_frozen_source_prevents_success_manifest(tmp_path, monkeypatch):
    from epl_strategy_lab import engine
    root = write_inputs(tmp_path / "project")
    original = engine.simulate_strategy
    changed = False
    def change_source_once(*args, **kwargs):
        nonlocal changed
        if not changed:
            path = root / SOURCE_FILES[3]
            path.write_text(path.read_text() + "\n", encoding="utf-8")
            changed = True
        return original(*args, **kwargs)
    monkeypatch.setattr(engine, "simulate_strategy", change_source_once)
    output = tmp_path / "changed_input_output"
    with pytest.raises(RuntimeError, match="changed during build"):
        build(output, project_root=root, bootstrap_samples=0, generate_report=False)
    assert not (output / "manifest.json").exists()
