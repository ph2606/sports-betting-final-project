"""Replay the new fixed rules and append their curves to frozen comparisons."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from epl_strategy.metrics import summarize_strategy
from epl_strategy_validation.inputs import SEASONS, validate_opportunities
from epl_strategy_validation.replay import replay

INITIAL = 100000.0
OLD_SINGLE = Path("epl_strategy_lab/results/20261015T040052Z_100k84")
OLD_CONTINUOUS = Path("epl_strategy_validation/results/20261015_temporal_selection")


def run_accounts(catalog, predictions, opportunities, *, bootstrap_samples=1000):
    native = validate_opportunities(opportunities, exact_population=True)
    if len(catalog) != 32 or [c["strategy_id"] for c in catalog] != [f"P{i:03d}" for i in range(1, 33)]:
        raise ValueError("All 32 fixed player-study strategies must be replayed")
    if predictions.duplicated(["model_key", "match_id"]).any(): raise ValueError("Duplicate model/fixture probabilities")
    models = {key: group.copy() for key, group in predictions.groupby("model_key")}
    metrics, bets, equity = {s: [] for s in ("continuous", "single", "seasonal")}, {s: [] for s in ("continuous", "single", "seasonal")}, {s: [] for s in ("continuous", "single", "seasonal")}
    for index, config in enumerate(catalog, 1):
        episodes = [("continuous", "2022-26", "continuous_2022_26", native),
            ("single", "2025-26", "2025-26", native.loc[native.season.eq("2025-26")])]
        episodes += [("seasonal", season, season, native.loc[native.season.eq(season)]) for season in SEASONS]
        for scope, season, episode, universe in episodes:
            b, e = replay(config, models, universe, initial_bankroll=INITIAL, episode_id=episode)
            row = summarize_strategy(b, e, prediction_count=len(universe), matched_valid_odds_count=len(universe),
                initial_bankroll=INITIAL, bootstrap_samples=bootstrap_samples, random_state=42)
            flat = {key: json.dumps(value, sort_keys=True) if isinstance(value, (list, dict)) else value for key, value in config.items()}
            aid = f"{scope}:{config['strategy_id']}:{season}"
            metrics[scope].append({**flat, **row, "scope": scope, "season": season, "episode_id": episode,
                "account_id": aid, "initial_bankroll": INITIAL, "funding_feasible": True,
                "execution_mode": "new_player_model_replay", "verified_execution": False})
            for frame in (b, e):
                frame["account_id"], frame["scope"], frame["scope_season"] = aid, scope, season
            bets[scope].append(b); equity[scope].append(e)
        if index % 8 == 0: print(f"Replayed {index}/32 player-study strategies", flush=True)
    return {**{"metrics_" + s: pd.DataFrame(metrics[s]) for s in metrics},
        **{"bets_" + s: pd.concat(bets[s], ignore_index=True) for s in bets},
        **{"equity_" + s: pd.concat(equity[s], ignore_index=True) for s in equity}}


def combined_graphs(tables, root):
    root = Path(root)
    frames = {}
    for scope, original, n_old, start in (("single", root / OLD_SINGLE / "equity.parquet", 84, "2025-08-14"),
            ("continuous", root / OLD_CONTINUOUS / "equity_continuous.parquet", 56, "2022-08-04")):
        old = pd.read_parquet(original)[["strategy_id", "match_date", "end_bankroll"]].copy()
        new = tables["equity_" + scope][["strategy_id", "match_date", "end_bankroll"]].copy()
        if old.strategy_id.nunique() != n_old or new.strategy_id.nunique() != 32:
            raise AssertionError("An old or new strategy is missing from the common graph")
        graph = pd.concat([old, new], ignore_index=True)
        graph["match_date"] = pd.to_datetime(graph.match_date)
        graph["is_initial"] = False
        anchor = pd.DataFrame({"strategy_id": sorted(graph.strategy_id.unique()), "match_date": pd.Timestamp(start),
            "end_bankroll": INITIAL, "is_initial": True})
        graph = pd.concat([graph, anchor], ignore_index=True).sort_values(["strategy_id", "match_date"]).reset_index(drop=True)
        if graph.duplicated(["strategy_id", "match_date"]).any() or graph.end_bankroll.lt(-1e-6).any():
            raise AssertionError("Invalid combined wealth curve")
        expected = 114 if scope == "single" else 454
        if len(graph) != (n_old + 32) * expected:
            raise AssertionError("Incomplete common graph dates")
        frames["graph_equity_2025_all" if scope == "single" else "graph_equity_continuous_all"] = graph
    return frames
