from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from epl_strategy_lab.inputs import ABLATION_MODELS, PROBABILITY_COLUMNS, SOURCE_FILES, load_inputs


def write_inputs(root: Path) -> Path:
    """A complete small-on-disk season, intentionally stored out of date order."""
    n = 374
    dates = pd.date_range("2025-08-15", "2026-05-24", periods=113).normalize()
    base = pd.DataFrame({"match_id": [f"m{i:03}" for i in range(n)],
                         "match_date": dates[np.arange(n) % len(dates)],
                         "season": "2025-26", "result": np.resize(list("HDA"), n)})
    first = []
    for branch, family, probabilities in (("accuracy", "svm", [.5, .3, .2]),
                                           ("calibration", "mlp", [.4, .3, .3])):
        frame = base.copy()
        frame[PROBABILITY_COLUMNS] = probabilities
        frame = frame.assign(branch=branch, family=family, split="test")
        first.append(frame)
    ablation = []
    reference = np.array([1 / 2, 1 / 3, 1 / 4])
    reference /= reference.sum()
    for i, (group, model_type) in enumerate(ABLATION_MODELS):
        frame = base.copy()
        probabilities = reference if (group, model_type) == ("market_only", "baseline") else np.array([
            .36 + i * .005, .30 - i * .002, .34 - i * .003])
        frame[PROBABILITY_COLUMNS] = probabilities
        frame = frame.assign(feature_group=group, model_type=model_type, outer_season="2025-26")
        ablation.append(frame)
    prices = base.copy()
    for outcome, odds, probability in zip("HDA", [2., 3., 4.], reference):
        prices[f"odds_{outcome}"] = odds
        prices[f"ref_odds_{outcome}"] = odds
        prices[f"bookmaker_{outcome}"] = "Bet365"
        prices[f"ref_p_{outcome}"] = probability
        prices[f"quote_timestamp_{outcome}_utc"] = None
    prices["snapshot_type"] = "preclosing"
    prices["reference_bookmaker"] = "Bet365"
    prices["reference_quote_timestamp_utc"] = None
    frozen = {"families": {"accuracy": "svm", "calibration": "mlp"},
              "thresholds": {branch: {"threshold": 1000000.,
                  "reason": "no_admissible_positive_validation_strategy",
                  "selection_season": "2024-25", "minimum_validation_bets": 30}
                  for branch in ("accuracy", "calibration")}}
    for relative in SOURCE_FILES:
        (root / relative).parent.mkdir(parents=True, exist_ok=True)
    pd.concat(first).to_parquet(root / SOURCE_FILES[0], index=False)
    pd.concat(ablation).to_parquet(root / SOURCE_FILES[1], index=False)
    prices.to_parquet(root / SOURCE_FILES[2], index=False)
    (root / SOURCE_FILES[3]).write_text(json.dumps({"frozen_choices": frozen}), encoding="utf-8")
    (root / SOURCE_FILES[4]).write_text(json.dumps(frozen), encoding="utf-8")
    pd.DataFrame([{"branch": branch, "threshold": threshold}
                  for branch in ("accuracy", "calibration")
                  for threshold in (0., .025, .05, .075, .1, .15, .2)]).to_csv(root / SOURCE_FILES[5], index=False)
    for relative in SOURCE_FILES[6:]:
        pd.DataFrame({"match_id": pd.Series(dtype=str)}).to_parquet(root / relative, index=False)
    return root


@pytest.fixture
def source_root(tmp_path):
    return write_inputs(tmp_path / "project")


def mutate_parquet(root, index, change):
    path = root / SOURCE_FILES[index]
    frame = pd.read_parquet(path)
    changed = change(frame)
    (frame if changed is None else changed).to_parquet(path, index=False)


def test_all_series_align_and_ensembles_use_exact_fixed_weights(source_root):
    models, opportunities, sources = load_inputs(source_root)
    assert len(models) == 16
    assert len(opportunities) == 374
    assert opportunities.match_date.nunique() == 113
    assert len(sources) == 8
    assert sources == [source_root / name for name in SOURCE_FILES]
    assert opportunities.equals(opportunities.sort_values(["match_date", "match_id"]).reset_index(drop=True))
    for frame in models.values():
        assert frame.match_id.tolist() == opportunities.match_id.tolist()
        np.testing.assert_allclose(frame[PROBABILITY_COLUMNS].sum(axis=1), 1.)
    for ensemble, members in {
        "ensemble_logit4": [f"logit_{name}" for name in ("team_only", "team_xg", "team_players", "combined")],
        "ensemble_learned8": [f"{family}_{name}" for family in ("logit", "residual")
                               for name in ("team_only", "team_xg", "team_players", "combined")],
        "ensemble_market_blend": ["logit_combined", "baseline_market_only"],
    }.items():
        expected = sum(models[key][PROBABILITY_COLUMNS].to_numpy() for key in members) / len(members)
        np.testing.assert_allclose(models[ensemble][PROBABILITY_COLUMNS], expected, atol=1e-15, rtol=0)


@pytest.mark.parametrize("kind,error", [
    ("duplicate", "duplicate"), ("missing", "population differs"),
    ("date", "match_date conflicts"), ("result", "result conflicts"),
    ("normalization", "sum to one"), ("nan", "invalid probabilities"),
    ("odds", "invalid decimal odds"), ("variant", "model identities changed"),
    ("outer_season", "season and outer-season"), ("raw_market", "reference probabilities"),
    ("count", "Expected 374"), ("missing_book", "bookmaker identity"),
])
def test_corrupt_or_misaligned_frozen_sources_fail_instead_of_dropping_matches(source_root, kind, error):
    if kind == "duplicate":
        mutate_parquet(source_root, 0, lambda f: pd.concat([f, f.iloc[[0]]], ignore_index=True))
    elif kind == "missing":
        mutate_parquet(source_root, 1, lambda f: f.iloc[1:])
    elif kind in {"date", "result", "normalization", "nan"}:
        column, value = {"date": ("match_date", pd.Timestamp("2025-08-16")),
                         "result": ("result", "A"), "normalization": ("p_H", .9),
                         "nan": ("p_H", np.nan)}[kind]
        mutate_parquet(source_root, 0, lambda f: f.__setitem__(column, f[column].mask(f.index == 0, value)))
    elif kind == "odds":
        mutate_parquet(source_root, 2, lambda f: f.__setitem__("odds_D", f.odds_D.mask(f.index == 0, 1.)))
    elif kind == "variant":
        mutate_parquet(source_root, 1, lambda f: f.__setitem__("model_type", f.model_type.mask(f.index == 0, "unknown")))
    elif kind == "outer_season":
        mutate_parquet(source_root, 1, lambda f: f.__setitem__("outer_season", f.outer_season.mask(f.index == 0, "2024-25")))
    elif kind == "raw_market":
        def wrong_market(f):
            mask = f.feature_group.eq("market_only") & f.model_type.eq("baseline")
            f.loc[mask, PROBABILITY_COLUMNS] = [.4, .3, .3]
        mutate_parquet(source_root, 1, wrong_market)
    elif kind == "count":
        mutate_parquet(source_root, 2, lambda f: f.iloc[:-1])
    elif kind == "missing_book":
        mutate_parquet(source_root, 2, lambda f: f.__setitem__("bookmaker_H", f.bookmaker_H.mask(f.index == 0, None)))
    with pytest.raises(ValueError, match=error):
        load_inputs(source_root)


def test_locked_choices_must_match_saved_run_metadata(source_root):
    path = source_root / SOURCE_FILES[4]
    data = json.loads(path.read_text())
    data["thresholds"]["accuracy"]["threshold"] = .05
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="locked choices and run metadata disagree"):
        load_inputs(source_root)


def test_threshold_diagnostic_rule_population_is_complete(source_root):
    path = source_root / SOURCE_FILES[5]
    pd.read_csv(path).iloc[1:].to_csv(path, index=False)
    with pytest.raises(ValueError, match="diagnostic rule identities"):
        load_inputs(source_root)


def test_repository_root_can_resolve_final_project(source_root):
    nested = source_root.parent / "repo" / "final_project"
    nested.parent.mkdir()
    source_root.rename(nested)
    models, opportunities, sources = load_inputs(nested.parent)
    assert len(models) == 16 and len(opportunities) == 374
    assert all(nested in path.parents for path in sources)
