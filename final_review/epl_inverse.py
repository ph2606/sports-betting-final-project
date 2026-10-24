"""Frozen-forecast, date-funded EPL complement study; no fitting or retuning."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from epl_strategy_validation.inputs import load_inputs
from epl_strategy_validation.replay import replay

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "final_review/epl_results"
PLAYER = ROOT / "epl_player_models/results/20261020_player_models_review"
OLD = ROOT / "epl_strategy_validation/results/20261015_temporal_selection"
EXEC = ROOT / "epl_execution/results/20261015_quote_sensitivity"
LABELS = "HDA"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False, default=str) + "\n", encoding="utf-8")


def simulate(signals, opportunities, *, context_id, variant, kind, cost_rate=0., date_cap=1., prefix=False):
    """Reserve all same-date maximum losses before any settlement is observed."""
    capital, peak = 100000., 100000.
    bets, curves, legs = [], [], []
    groups = {date: group for date, group in signals.groupby("match_date", sort=True)}
    for date, day in opportunities.groupby("match_date", sort=True):
        start = capital
        sig = groups.get(date, signals.iloc[:0])
        requested = sig.requested_risk.to_numpy(float) if prefix else np.full(len(sig), 1000.)
        # A bankrupt account is absorbing; signals nevertheless remain available for audit.
        if start <= 0:
            requested = requested * 0
        budget = start * date_cap
        scale = min(1., budget / requested.sum()) if requested.sum() else 1.
        risks = requested * scale
        if len(risks) and risks.sum() > budget:
            risks[-1] = max(0., risks[-1] - (risks.sum() - budget))
        pp, gross_returns, day_records = [], [], []
        for pos, (_, row) in enumerate(sig.iterrows()):
            risk = float(risks[pos])
            if risk <= 0:
                continue
            selection = row.original_selection
            if kind == "original":
                event = row.result == selection
                probability = float(row.p_original)
                multiplier = float(row.original_odds) - 1
                effective_odds = float(row.original_odds)
            else:
                event = row.result != selection
                probability = 1 - float(row.p_original)
                if kind == "dutch":
                    inv = sum(1 / float(row["odds_" + j]) for j in LABELS if j != selection)
                    effective_odds = 1 / inv
                    multiplier = effective_odds - 1
                elif kind == "lay":
                    multiplier = 1 / (float(row.original_odds) - 1)
                    effective_odds = 1 + multiplier
                else:
                    raise ValueError(kind)
            gross = risk * effective_odds if event else 0.
            raw = gross - risk
            fee = cost_rate * max(raw, 0.)
            profit = raw - fee
            gain = risk * probability * max(multiplier, 0.) * (1 - cost_rate)
            loss = risk * ((1 - probability) + probability * max(-multiplier, 0.))
            record = {"context_id": context_id, "variant": variant, "kind": kind,
                      "cost_rate": cost_rate, "match_id": row.match_id, "match_date": date,
                      "season": row.season, "result": row.result, "original_selection": selection,
                      "p_original": float(row.p_original), "original_odds": float(row.original_odds),
                      "event_probability": probability, "effective_odds": effective_odds,
                      "event_hit": bool(event), "profit_hit": bool(profit > 0), "risk": risk,
                      "requested_risk": float(requested[pos]), "commitment_scale": scale,
                      "gross_return": gross, "raw_profit": raw, "fee": fee, "profit": profit,
                      "expected_gain": gain, "expected_loss": loss,
                      "counterstake": risk / (float(row.original_odds) - 1) if kind == "lay" else None,
                      "date_start_capital": start}
            if kind == "dutch":
                for j in LABELS:
                    if j == selection:
                        continue
                    price = float(row["odds_" + j])
                    stake = risk * (1 / price) / inv
                    legs.append({"context_id": context_id, "variant": variant, "match_id": row.match_id,
                                 "match_date": date, "outcome": j, "odds": price,
                                 "bookmaker": row["bookmaker_" + j], "stake": stake,
                                 "gross_return": stake * price if row.result == j else 0.})
            day_records.append(record)
            pp.append(profit)
            gross_returns.append(gross)
        risk_total = float(risks.sum())
        fee_total = float(sum(r["fee"] for r in day_records))
        # Preserve source original summation convention when proving reproduction.
        capital = max(0., start - risk_total + float(np.sum(gross_returns)) - fee_total)
        peak = max(peak, capital)
        for row in day_records:
            row["date_end_capital"] = capital
        bets.extend(day_records)
        curves.append({"context_id": context_id, "variant": variant, "match_date": date,
                       "season": day.season.iloc[0], "start_capital": start, "end_capital": capital,
                       "signal_count": len(sig), "bet_count": len(day_records),
                       "requested_risk": float(requested.sum()), "risk": risk_total,
                       "cost_rate": cost_rate, "fee": fee_total,
                       "profit": float(sum(pp)), "commitment_scale": scale,
                       "date_cap": date_cap, "drawdown": 1 - capital / peak})
    return pd.DataFrame(bets), pd.DataFrame(curves), pd.DataFrame(legs)


def metrics(bets, curve, *, config, context_id, variant, kind, fee, zero, nsignals):
    n = len(bets)
    total = float(bets.risk.sum()) if n else 0.
    profit = float(curve.end_capital.iloc[-1] - 100000.)
    return {"context_id": context_id, "strategy_id": config["strategy_id"],
            "model_key": config["model_key"], "model_label": config.get("model_label", config["model_key"]),
            "price_mode": config["odds_mode"], "selection_rule": config["selection_rule"],
            "original_zero": bool(zero), "variant": variant, "kind": kind, "cost_rate": fee,
            "initial_capital": 100000., "final_capital": float(curve.end_capital.iloc[-1]),
            "profit": profit, "return_on_initial_capital": profit / 100000.,
            "risk_turnover": total, "turnover": total if kind != "lay" else None,
            "risk_roi": profit / total if total else None,
            "roi": profit / total if total and kind != "lay" else None,
            "bet_count": n, "leg_count": n * (2 if kind == "dutch" else 1),
            "qualifying_signals": nsignals, "trading_frequency": n / 1470.,
            "event_hit_ratio": float(bets.event_hit.mean()) if n else None,
            "positive_profit_hit_ratio": float(bets.profit_hit.mean()) if n else None,
            "expected_gain_per_trade": float(bets.expected_gain.mean()) if n else None,
            "expected_loss_per_trade": float(bets.expected_loss.mean()) if n else None,
            "avg_winning_gain": float(bets.loc[bets.profit > 0, "profit"].mean()) if n and bets.profit.gt(0).any() else None,
            "avg_losing_loss": float(-bets.loc[bets.profit < 0, "profit"].mean()) if n and bets.profit.lt(0).any() else None,
            "fees": float(bets.fee.sum()) if n else 0.,
            "max_drawdown": float(curve.drawdown.max()),
            "active_dates": int(curve.bet_count.gt(0).sum()),
            "scaled_dates": int((curve.commitment_scale.lt(1 - 1e-12) & curve.bet_count.gt(0)).sum()),
            "max_date_exposure": float((curve.risk / curve.start_capital.replace(0, np.nan)).max()),
            "nonpositive_complement_payout_bundles": int(bets.effective_odds.le(1).sum()) if n and kind == "dutch" else 0,
            "roi_ci_low": None, "roi_ci_high": None}


def identity_diagnostic(context, original, eq):
    original = original.copy()
    original["liability"] = original.stake * (original.odds - 1)
    liability = original.groupby("match_date").liability.sum().reindex(eq.match_date, fill_value=0).to_numpy()
    opening = 200000. - eq.start_bankroll.to_numpy(float)
    shortfall = np.maximum(liability - opening, 0.)
    return {"context_id": context, "original_final_capital": float(eq.end_bankroll.iloc[-1]),
            "arithmetic_mirror_final": float(200000. - eq.end_bankroll.iloc[-1]),
            "arithmetic_mirror_minimum": float(min(100000., (200000. - eq.end_bankroll).min())),
            "original_peak_capital": float(max(100000., eq.end_bankroll.max())),
            "max_same_date_liability": float(liability.max()),
            "minimum_additional_opening_cash": float(shortfall.max()),
            "funding_shortfall_dates": int((shortfall > 1e-7).sum()),
            "mirror_funding_feasible": bool(shortfall.max() <= 1e-7),
            "original_bet_count": len(original)}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    models, opps, source_paths = load_inputs(ROOT)
    preds = pd.read_parquet(PLAYER / "predictions.parquet")
    for key, frame in preds.groupby("model_key"):
        if key.startswith("pm_"):
            models[key] = frame
    catalog = json.loads((PLAYER / "all_strategy_catalog.json").read_text())
    originals = pd.concat([pd.read_parquet(OLD / "metrics_continuous.parquet"),
                           pd.read_parquet(PLAYER / "metrics_continuous.parquet")], ignore_index=True)
    source_bets = pd.concat([pd.read_parquet(OLD / "bets_continuous.parquet"),
                            pd.read_parquet(PLAYER / "bets_continuous.parquet")], ignore_index=True)
    source_eq = pd.concat([pd.read_parquet(OLD / "equity_continuous.parquet"),
                          pd.read_parquet(PLAYER / "equity_continuous.parquet")], ignore_index=True)
    fixed = originals.loc[originals.staking.eq("fixed")]
    assert len(fixed) == 47
    configs = {r["strategy_id"]: r for r in catalog}
    contexts = []
    for _, record in fixed.iterrows():
        conf = configs[record.strategy_id].copy()
        contexts.append((record.strategy_id + "__" + conf["odds_mode"], conf,
                         float(record.final_capital_sum_units), source_bets[source_bets.strategy_id.eq(record.strategy_id)],
                         source_eq[source_eq.strategy_id.eq(record.strategy_id)]))
    refmetrics = pd.read_parquet(EXEC / "metrics_continuous.parquet")
    refmetrics = refmetrics.loc[refmetrics.execution_mode.eq("reference_replay") & refmetrics.final_capital_sum_units.eq(0)]
    refbets = pd.read_parquet(EXEC / "bets_reference_continuous.parquet")
    refeq = pd.read_parquet(EXEC / "equity_reference_continuous.parquet")
    assert len(refmetrics) == 4
    for _, record in refmetrics.iterrows():
        conf = configs[record.strategy_id].copy()
        conf["odds_mode"] = "reference"
        contexts.append((record.strategy_id + "__reference", conf, 0.,
                         refbets[refbets.strategy_id.eq(record.strategy_id)],
                         refeq[refeq.strategy_id.eq(record.strategy_id)]))
    results, allbets, allcurves, alllegs, allsignals, recs, inventory, identities = [], [], [], [], [], [], [], []
    for i, (context, conf, saved_final, recorded, saved_eq) in enumerate(contexts):
        print(f"{i+1}/51 {context}: reproduce originals and run fixed protocol", flush=True)
        assert conf["fixed_stake"] == 1000 and conf["staking"] == "fixed"
        normal_bets, normal_eq = replay(conf, models, opps)
        recorded = recorded.sort_values(["match_date", "match_id"]).reset_index(drop=True)
        saved_eq = saved_eq.sort_values("match_date").reset_index(drop=True)
        assert normal_bets.match_id.tolist() == recorded.match_id.tolist(), context
        np.testing.assert_allclose(normal_bets.stake, recorded.stake, atol=1e-7, rtol=1e-10)
        np.testing.assert_allclose(normal_bets.profit, recorded.profit, atol=1e-7, rtol=1e-10)
        np.testing.assert_allclose(normal_eq.end_bankroll, saved_eq.end_bankroll, atol=1e-7, rtol=1e-10)
        assert abs(float(normal_eq.end_bankroll.iloc[-1]) - saved_final) < 1e-6
        complete, _ = replay(conf, models, opps, initial_bankroll=1e12)
        signal = complete[["match_id", "selection", "probability", "odds"]].rename(columns={
            "selection": "original_selection", "probability": "p_original", "odds": "original_odds"}).merge(opps, on="match_id", validate="one_to_one")
        signal = signal.drop(columns=[c for c in signal if c.startswith("bookmaker_")]) if conf["odds_mode"] == "reference" else signal
        if conf["odds_mode"] == "reference":
            for j in LABELS:
                signal["odds_" + j] = signal["ref_odds_" + j]
                signal["bookmaker_" + j] = signal.reference_bookmaker
        signal["context_id"] = context
        signal["requested_risk"] = 1000.
        signal = signal.sort_values(["match_date", "match_id"]).reset_index(drop=True)
        allsignals.append(signal)
        zero = saved_final == 0
        inventory.append({"context_id": context, "strategy_id": conf["strategy_id"], "price_mode": conf["odds_mode"],
                          "original_zero": zero, "original_final_capital": saved_final,
                          "original_bet_count": len(recorded), "qualifying_signals": len(signal),
                          "scope": "additional_reference_zero" if context.endswith("reference") and conf["strategy_id"] in {"S033", "S039", "S041", "S043"} else "main_47_fixed"})
        recs.append({"context_id": context, "saved_final_capital": saved_final,
                     "replayed_final_capital": float(normal_eq.end_bankroll.iloc[-1]),
                     "bet_count": len(recorded), "max_stake_error": float(np.max(abs(normal_bets.stake - recorded.stake))) if len(recorded) else 0.,
                     "max_equity_error": float(np.max(abs(normal_eq.end_bankroll - saved_eq.end_bankroll))), "source_reproduced": True})
        variants = [("original", "original", 0., signal)] + [("dutch_cost_" + str(int(100 * f)), "dutch", f, signal) for f in (0., .02, .05)] + [("lay_hypothetical", "lay", 0., signal)]
        if zero:
            identities.append(identity_diagnostic(context, recorded, saved_eq))
            prefix = signal.loc[signal.match_id.isin(recorded.match_id)].copy()
            prefix["requested_risk"] = prefix.match_id.map(recorded.set_index("match_id").stake)
            variants.append(("dutch_recorded_prefix", "dutch", 0., prefix))
        for variant, kind, fee, signals in variants:
            b, e, legs = simulate(signals, opps, context_id=context, variant=variant, kind=kind,
                                  cost_rate=fee, date_cap=conf.get("date_cap_fraction") or 1.,
                                  prefix=variant == "dutch_recorded_prefix")
            if kind == "original":
                assert b.match_id.tolist() == recorded.match_id.tolist()
                np.testing.assert_allclose(b.risk, recorded.stake, atol=1e-6, rtol=1e-10)
                np.testing.assert_allclose(e.end_capital, saved_eq.end_bankroll, atol=1e-6, rtol=1e-10)
            row = metrics(b, e, config=conf, context_id=context, variant=variant, kind=kind, fee=fee, zero=zero, nsignals=len(signals))
            results.append(row)
            allbets.append(b); allcurves.append(e)
            if not legs.empty:
                alllegs.append(legs)
    metrics_frame = pd.DataFrame(results)
    bets_frame, eq_frame = pd.concat(allbets, ignore_index=True), pd.concat(allcurves, ignore_index=True)
    # Conditional intervals resample complete match dates within each outer season.
    # Fixed funded cashflows, no refit/resizing, and no post-selection adjustment.
    rng = np.random.default_rng(20261023)
    draws = 9999
    for index in metrics_frame.index[metrics_frame.variant.eq("dutch_cost_0")]:
        context = metrics_frame.loc[index, "context_id"]
        e = eq_frame.loc[eq_frame.context_id.eq(context) & eq_frame.variant.eq("dutch_cost_0")]
        total_profit, total_risk = np.zeros(draws), np.zeros(draws)
        for _, part in e.groupby("season", sort=True):
            indices = rng.integers(0, len(part), size=(draws, len(part)))
            total_profit += part.profit.to_numpy()[indices].sum(axis=1)
            total_risk += part.risk.to_numpy()[indices].sum(axis=1)
        valid = total_risk > 0
        if valid.any():
            lo, hi = np.quantile(total_profit[valid] / total_risk[valid], [.025, .975])
            metrics_frame.loc[index, ["roi_ci_low", "roi_ci_high"]] = [lo, hi]
    metrics_frame.to_csv(OUT / "metrics.csv", index=False)
    pd.DataFrame(inventory).to_csv(OUT / "inventory.csv", index=False)
    pd.DataFrame(recs).to_csv(OUT / "original_reconciliation.csv", index=False)
    pd.DataFrame(identities).to_csv(OUT / "identity_diagnostics.csv", index=False)
    bets_frame.to_parquet(OUT / "bets.parquet", index=False)
    eq_frame.to_parquet(OUT / "equity.parquet", index=False)
    pd.concat(alllegs, ignore_index=True).to_parquet(OUT / "legs.parquet", index=False)
    pd.concat(allsignals, ignore_index=True).to_parquet(OUT / "signals.parquet", index=False)
    opps.to_parquet(OUT / "opportunities.parquet", index=False)
    cohorts = []
    for (variant, zero), part in metrics_frame.loc[~metrics_frame.variant.eq("dutch_recorded_prefix")].groupby(["variant", "original_zero"]):
        cohorts.append({"variant": variant, "original_zero": bool(zero), "accounts": len(part),
                        "profitable_accounts": int(part.final_capital.gt(100000 + 1e-7).sum()),
                        "bankrupt_accounts": int(part.final_capital.le(1e-7).sum()),
                        "median_final_capital": float(part.final_capital.median()),
                        "min_final_capital": float(part.final_capital.min()),
                        "max_final_capital": float(part.final_capital.max())})
    save_json(OUT / "cohort_summary.json", cohorts)
    paths = [ROOT / "final_review/inverse_protocol.md", ROOT / "final_review/design_notes.json", Path(__file__),
             PLAYER / "all_strategy_catalog.json", PLAYER / "predictions.parquet", OLD / "metrics_continuous.parquet",
             PLAYER / "metrics_continuous.parquet", EXEC / "metrics_continuous.parquet",
             OLD / "bets_continuous.parquet", PLAYER / "bets_continuous.parquet", EXEC / "bets_reference_continuous.parquet",
             OLD / "equity_continuous.parquet", PLAYER / "equity_continuous.parquet", EXEC / "equity_reference_continuous.parquet",
             ROOT / "epl_strategy_lab/engine.py", ROOT / "epl_strategy_validation/replay.py",
             ROOT / "epl_strategy_validation/inputs.py", *source_paths]
    summary = {"contexts": 51, "original_zero_contexts": 17, "nonzero_controls": 34,
               "main_fixed_cohort": 47, "additional_reference_zero_contexts": 4,
               "funded_complement_accounts": 153, "hypothetical_lay_accounts": 51,
               "prefix_complement_diagnostics": 17, "recorded_identity_diagnostics": 17,
               "fixtures": len(opps), "dates": opps.match_date.nunique(), "bootstrap_samples": draws,
               "bootstrap_basis": "Conditional fixed cashflows, whole match dates resampled within each outer season; no model, policy, sizing or family selection uncertainty",
               "cohorts": cohorts, "source_sha256": {str(p.relative_to(ROOT)): sha(p) for p in paths},
               "outputs_sha256": {p.name: sha(p) for p in sorted(OUT.iterdir()) if p.is_file()},
               "status": "exploratory_not_independent_holdout", "protocol_commit": "23d83be"}
    save_json(OUT / "summary.json", summary)
    print(json.dumps(cohorts, indent=2), flush=True)


if __name__ == "__main__":
    main()
