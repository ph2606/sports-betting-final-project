"""Independent audit of the exported EPL reversal experiment.

The audited simulator is deliberately not imported. Source readers are used
only to recover frozen forecasts and prices; qualification, three-outcome
payoffs, date funding, wealth and metrics are recomputed here. This audit
does not fit a model, rewrite a source artifact or choose a winning policy.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

LABELS = np.array(list("HDA"))
INITIAL = 100000.0
REQUEST = 1000.0
OLD = Path("epl_strategy_validation/results/20261015_temporal_selection")
PLAYER = Path("epl_player_models/results/20261020_player_models_review")
EXECUTION = Path("epl_execution/results/20261015_quote_sensitivity")
VARIANTS = {
    "original": ("original", 0.0),
    "dutch_cost_0": ("dutch", 0.0),
    "dutch_cost_2": ("dutch", 0.02),
    "dutch_cost_5": ("dutch", 0.05),
    "lay_hypothetical": ("lay", 0.0),
    "dutch_recorded_prefix": ("dutch", 0.0),
}


def _need(frame, columns, label):
    missing = sorted(set(columns) - set(frame.columns))
    if missing:
        raise AssertionError(f"{label}: missing columns {missing}")


def _same(actual, expected, label):
    if list(actual) != list(expected):
        raise AssertionError(f"{label}: identities or order differ")


def _near(actual, expected, label, *, atol=1e-6, rtol=1e-10):
    a, b = np.asarray(actual, dtype=float), np.asarray(expected, dtype=float)
    if not np.allclose(a, b, atol=atol, rtol=rtol, equal_nan=True):
        difference = np.nanmax(np.abs(a - b)) if a.size and b.size else None
        raise AssertionError(f"{label}: numeric mismatch, max absolute error={difference}")


def _date(values):
    return pd.to_datetime(values, errors="raise", utc=True).dt.tz_convert(None).dt.normalize()


def _flag(values):
    if values.dtype == bool:
        return values
    value = values.astype(str).str.lower()
    if not value.isin(["true", "false"]).all():
        raise AssertionError("A Boolean field contains another value")
    return value.eq("true")


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _source_contexts(root):
    """Recover the context population without consulting inverse inventory."""
    from epl_strategy_validation.inputs import load_inputs

    models, opportunities, paths = load_inputs(root)
    player_predictions = pd.read_parquet(root / PLAYER / "predictions.parquet")
    models.update({key: frame for key, frame in player_predictions.groupby("model_key")
                   if key.startswith("pm_")})
    catalog = {row["strategy_id"]: row for row in json.loads(
        (root / PLAYER / "all_strategy_catalog.json").read_text(encoding="utf-8"))}
    metrics = pd.concat([pd.read_parquet(root / folder / "metrics_continuous.parquet")
                         for folder in (OLD, PLAYER)], ignore_index=True)
    bets = pd.concat([pd.read_parquet(root / folder / "bets_continuous.parquet")
                      for folder in (OLD, PLAYER)], ignore_index=True)
    equity = pd.concat([pd.read_parquet(root / folder / "equity_continuous.parquet")
                        for folder in (OLD, PLAYER)], ignore_index=True)
    fixed = metrics.loc[metrics.staking.eq("fixed")]
    if len(fixed) != 47 or fixed.final_capital_sum_units.eq(0).sum() != 13:
        raise AssertionError("The source main fixed cohort is not 47 accounts / 13 zeros")
    contexts = {}
    for record in fixed.to_dict("records"):
        config = dict(catalog[record["strategy_id"]])
        context = config["strategy_id"] + "__" + config["odds_mode"]
        contexts[context] = (config, record["final_capital_sum_units"],
                             bets.loc[bets.strategy_id.eq(config["strategy_id"])].copy(),
                             equity.loc[equity.strategy_id.eq(config["strategy_id"])].copy(),
                             "main_47_fixed")
    ref_metrics = pd.read_parquet(root / EXECUTION / "metrics_continuous.parquet")
    ref_metrics = ref_metrics.loc[ref_metrics.execution_mode.eq("reference_replay") &
                                  ref_metrics.final_capital_sum_units.eq(0)]
    if set(ref_metrics.strategy_id) != {"S033", "S039", "S041", "S043"}:
        raise AssertionError("The four additional reference zero contexts changed")
    ref_bets = pd.read_parquet(root / EXECUTION / "bets_reference_continuous.parquet")
    ref_eq = pd.read_parquet(root / EXECUTION / "equity_reference_continuous.parquet")
    for sid in ref_metrics.strategy_id:
        config = dict(catalog[sid], odds_mode="reference")
        contexts[sid + "__reference"] = (
            config, 0.0, ref_bets.loc[ref_bets.strategy_id.eq(sid)].copy(),
            ref_eq.loc[ref_eq.strategy_id.eq(sid)].copy(), "additional_reference_zero")
    if len(contexts) != 51 or sum(value[1] == 0 for value in contexts.values()) != 17:
        raise AssertionError("Source context inventory is not 51 / 17 zeros")
    for context, (config, _, original, curve, _) in contexts.items():
        if config["staking"] != "fixed" or config["fixed_stake"] != REQUEST:
            raise AssertionError(context + ": inverse cohort contains a different sizing policy")
        original["match_date"], curve["match_date"] = _date(original.match_date), _date(curve.match_date)
        original.sort_values(["match_date", "match_id"], inplace=True)
        curve.sort_values("match_date", inplace=True)
    opportunities["match_date"] = _date(opportunities.match_date)
    opportunities = opportunities.sort_values(["match_date", "match_id"]).reset_index(drop=True)
    return models, opportunities, contexts, paths


def _qualifiers(config, models, opportunities):
    """Compute the frozen selection rules directly, with H/D/A tie order."""
    mode = config["odds_mode"]
    prefix = "ref_" if mode == "reference" else ""
    odds = opportunities[[prefix + "odds_" + label for label in LABELS]].to_numpy(float)

    def probability(key):
        source = models[key]
        if source.match_id.duplicated().any() or set(source.match_id) != set(opportunities.match_id):
            raise AssertionError(key + ": forecast universe does not equal all 1,470 fixtures")
        matrix = source.set_index("match_id").reindex(opportunities.match_id)[["p_" + j for j in LABELS]].to_numpy(float)
        if not np.isfinite(matrix).all() or (matrix < 0).any() or (matrix > 1).any():
            raise AssertionError(key + ": invalid probabilities")
        _near(matrix.sum(axis=1), 1, key + " probability mass", atol=1e-8, rtol=0)
        return matrix

    p = probability(config["model_key"])
    edge = p * odds - 1
    possible = np.broadcast_to(np.isin(LABELS, config["allowed_outcomes"]), odds.shape).copy()
    if config.get("min_odds") is not None:
        possible &= odds >= config["min_odds"]
    if config.get("max_odds") is not None:
        possible &= odds <= config["max_odds"]
    rule = config["selection_rule"]
    if rule == "max_edge":
        score = edge
    elif rule == "model_favorite":
        score = p
    elif rule in {"market_favorite", "market_underdog"}:
        score = probability("baseline_market_only") * (1 if rule == "market_favorite" else -1)
    elif rule == "fixed_outcome":
        score = np.zeros_like(edge)
    else:
        raise AssertionError("Unrecognised frozen selection rule: " + rule)
    chosen = np.argmax(np.where(possible, score, -np.inf), axis=1)
    rows = np.arange(len(opportunities))
    eligible = possible.any(axis=1)
    if config.get("min_edge") is not None:
        eligible &= edge[rows, chosen] > config["min_edge"]
    if config.get("consensus_min") is not None:
        votes = np.zeros(len(opportunities), dtype=int)
        for key in config["consensus_model_keys"]:
            votes += probability(key)[rows, chosen] * odds[rows, chosen] - 1 > 0
        eligible &= votes >= config["consensus_min"]
    if config.get("cash_only"):
        eligible[:] = False
    qualified = opportunities.loc[eligible, ["match_id", "match_date", "season", "result"]].copy()
    qualified["original_selection"] = LABELS[chosen[eligible]]
    qualified["original_odds"] = odds[rows, chosen][eligible]
    qualified["p_original"] = p[rows, chosen][eligible]
    for j, label in enumerate(LABELS):
        qualified["p_" + label] = p[eligible, j]
        qualified["odds_" + label] = odds[eligible, j]
        qualified["bookmaker_" + label] = (opportunities.loc[eligible, "reference_bookmaker"].to_numpy()
                                           if mode == "reference" else opportunities.loc[eligible, "bookmaker_" + label].to_numpy())
    return qualified.reset_index(drop=True)


def _payoffs(signals, risk, kind, cost):
    """Return a genuine H/D/A payoff vector, including effective odds <= 1."""
    selected = signals.original_selection.to_numpy()[:, None] == LABELS[None, :]
    odds = signals[["odds_" + j for j in LABELS]].to_numpy(float)
    risk = np.asarray(risk, dtype=float)
    if kind == "original":
        raw = np.where(selected, risk[:, None] * (odds - 1), -risk[:, None])
        effective = signals.original_odds.to_numpy(float)
    elif kind == "lay":
        effective = 1 + 1 / (signals.original_odds.to_numpy(float) - 1)
        raw = np.where(selected, -risk[:, None], risk[:, None] * (effective[:, None] - 1))
    elif kind == "dutch":
        inverse_sum = np.where(selected, 0, 1 / odds).sum(axis=1)
        effective = 1 / inverse_sum
        # Compute from the actual leg stakes, rather than reusing a binary
        # odds formula whose expected-gain sign is wrong when effective<=1.
        leg_stakes = np.where(selected, 0, risk[:, None] / odds / inverse_sum[:, None])
        raw = leg_stakes * odds - risk[:, None]
    else:
        raise AssertionError("Unknown payoff kind")
    fee_vector = cost * np.maximum(raw, 0)
    net = raw - fee_vector
    p = signals[["p_" + j for j in LABELS]].to_numpy(float)
    expected_gain = (p * np.maximum(net, 0)).sum(axis=1)
    expected_loss = (p * np.maximum(-net, 0)).sum(axis=1)
    outcome = np.argmax(signals.result.to_numpy()[:, None] == LABELS[None, :], axis=1)
    rows = np.arange(len(signals))
    event = signals.result.to_numpy() == signals.original_selection.to_numpy()
    if kind != "original":
        event = ~event
    return {"raw_profit": raw[rows, outcome], "profit": net[rows, outcome],
            "fee": fee_vector[rows, outcome], "effective_odds": effective,
            "expected_gain": expected_gain, "expected_loss": expected_loss,
            "event_hit": event, "profit_hit": net[rows, outcome] > 0,
            "event_probability": (signals.p_original.to_numpy(float) if kind == "original"
                                  else 1 - signals.p_original.to_numpy(float))}


def _legs(signals, bets, legs):
    """Check every physical leg in vectors; no simulator payoff code is used."""
    source = signals.set_index("match_id").reindex(bets.match_id).reset_index()
    prices = source[["odds_" + j for j in LABELS]].to_numpy(float)
    selected = source.original_selection.to_numpy()[:, None] == LABELS[None, :]
    inverse_sum = np.where(selected, 0, 1 / prices).sum(axis=1)
    risk = bets.risk.to_numpy(float)
    expected = []
    for j, label in enumerate(LABELS):
        include = ~selected[:, j]
        stake = risk[include] / prices[include, j] / inverse_sum[include]
        expected.append(pd.DataFrame({
            "match_id": source.loc[include, "match_id"].to_numpy(),
            "match_date": source.loc[include, "match_date"].to_numpy(),
            "outcome": label, "odds": prices[include, j], "stake": stake,
            "bookmaker": source.loc[include, "bookmaker_" + label].astype(str).to_numpy(),
            "gross_return": stake * prices[include, j] * source.loc[include, "result"].eq(label).to_numpy(),
            "equal_gross": risk[include] / inverse_sum[include]}))
    expected = pd.concat(expected, ignore_index=True).sort_values(["match_id", "outcome"])
    actual = legs.sort_values(["match_id", "outcome"])
    for field in ("match_id", "outcome", "match_date", "bookmaker"):
        _same(actual[field].astype(str), expected[field].astype(str), "Exact complementary leg " + field)
    for field in ("odds", "stake", "gross_return"):
        _near(actual[field], expected[field], "Independent complementary leg " + field)
    _near(actual.stake.to_numpy() * actual.odds.to_numpy(), expected.equal_gross,
          "Either complementary outcome pays equal gross return")
    total = actual.groupby("match_id").stake.sum().reindex(bets.match_id).to_numpy(float)
    _near(total, risk, "Each complementary bundle has exactly its reserved total risk")


def _account(context, variant, config, signals, source_original, source_curve, bets, curve, legs, dates):
    kind, cost = VARIANTS[variant]
    signals = signals.copy()
    if variant == "dutch_recorded_prefix":
        stakes = source_original.set_index("match_id").stake
        signals = signals.loc[signals.match_id.isin(stakes.index)].copy()
        signals["audit_request"] = signals.match_id.map(stakes)
    else:
        signals["audit_request"] = REQUEST
    curve = curve.sort_values("match_date").reset_index(drop=True)
    bets = bets.sort_values(["match_date", "match_id"]).reset_index(drop=True)
    if kind == "dutch":
        _legs(signals, bets, legs)
    _same(curve.match_date, dates, context + "/" + variant + " all 453 dates")
    if curve.match_date.duplicated().any() or bets.match_id.duplicated().any():
        raise AssertionError("Duplicate date or bundle")
    cap = 1.0 if config.get("date_cap_fraction") is None else config["date_cap_fraction"]
    prior, peak, checked = INITIAL, INITIAL, 0
    date_groups = {date: group for date, group in signals.groupby("match_date", sort=True)}
    bet_groups = {date: group for date, group in bets.groupby("match_date", sort=True)}
    # Compute every outcome vector once per account. Each actual risk is checked
    # independently against opening-cash allocation in the date loop below.
    funded_source = signals.set_index("match_id").reindex(bets.match_id).reset_index()
    _same(bets.original_selection, funded_source.original_selection, "Frozen selection/tie order")
    expected = _payoffs(funded_source, bets.risk.to_numpy(float), kind, cost)
    for field, values in expected.items():
        if field in {"event_hit", "profit_hit"}:
            _same(_flag(bets[field]), values, "Per-bundle " + field)
        else:
            _near(bets[field], values, "Three-outcome " + field)
    _near(bets.gross_return, bets.risk.to_numpy(float) + expected["raw_profit"], "Pre-fee gross returns")
    _near(bets.p_original, funded_source.p_original, "Source selected probability")
    _near(bets.original_odds, funded_source.original_odds, "Source original odds")
    curve_index = curve.set_index("match_date")
    _near(bets.date_start_capital, bets.match_date.map(curve_index.start_capital), "Bundle opening capital")
    _near(bets.date_end_capital, bets.match_date.map(curve_index.end_capital), "Bundle closing capital")
    _near(bets.commitment_scale, bets.match_date.map(curve_index.commitment_scale), "Bundle commitment scale")
    if kind == "lay":
        _near(bets.counterstake, bets.risk.to_numpy(float) / (funded_source.original_odds.to_numpy(float) - 1),
              "Lay counterstake distinguished from liability")
    expected_cashflows = pd.DataFrame({"match_date": bets.match_date,
                                      "gross": bets.risk.to_numpy(float) + expected["raw_profit"],
                                      "profit": expected["profit"], "fee": expected["fee"]})
    cashflows = expected_cashflows.groupby("match_date").sum()
    for row in curve.itertuples(index=False):
        opening = float(row.start_capital)
        _near(opening, prior, "Date-to-date capital continuity")
        qualified = date_groups.get(row.match_date, signals.iloc[:0]).copy()
        request = qualified.audit_request.to_numpy(float) if opening > 0 else np.zeros(len(qualified))
        budget = opening * cap
        scale = min(1.0, budget / request.sum()) if request.sum() else 1.0
        risk = request * scale
        if len(risk) and risk.sum() > budget:
            risk[-1] = max(0, risk[-1] - (risk.sum() - budget))
        actual = bet_groups.get(row.match_date, bets.iloc[:0])
        funded = qualified.loc[risk > 0].copy()
        funded_risk = risk[risk > 0]
        _same(actual.match_id, funded.match_id, context + "/" + variant + " funded fixtures")
        _near(actual.risk, funded_risk, "Uniform same-date cash allocation")
        _near(actual.requested_risk, request[risk > 0], "Original request before joint allocation")
        _near([row.signal_count, row.bet_count, row.requested_risk, row.risk,
               row.commitment_scale, row.date_cap, row.cost_rate],
              [len(qualified), len(funded), request.sum(), risk.sum(), scale, cap, cost],
              "Date commitment fields")
        if risk.sum() > budget + 1e-7 or risk.sum() > opening + 1e-7 or opening < 0:
            raise AssertionError("Date commitments exceed opening cash/date cap")
        day = cashflows.loc[row.match_date] if row.match_date in cashflows.index else None
        day_profit, day_fee = (float(day.profit), float(day.fee)) if day is not None else (0.0, 0.0)
        gross = float(day.gross) if day is not None else 0.0
        closing = max(0.0, opening - risk.sum() + gross - day_fee)
        peak = max(peak, closing)
        _near([row.end_capital, row.profit, row.fee, row.drawdown],
              [closing, day_profit, day_fee, 1 - closing / peak], "Settlement / wealth / drawdown")
        prior = float(row.end_capital)
        checked += len(actual)
    if variant == "original":
        _same(bets.match_id, source_original.match_id, "Full original recorded trade reproduction")
        for exported, source in (("risk", "stake"), ("profit", "profit"),
                                 ("original_odds", "odds"), ("p_original", "probability")):
            _near(bets[exported], source_original[source], "Frozen original " + source)
        _same(bets.original_selection, source_original.selection, "Frozen original choices")
        _same(curve.match_date, source_curve.match_date, "Frozen original full date grid")
        _near(curve.end_capital, source_curve.end_bankroll, "Every original frozen wealth point")
    return checked


def _metric(row, bets, curve, nsignals):
    kind, cost = VARIANTS[row.variant]
    n, risk = len(bets), float(bets.risk.sum())
    final = float(curve.end_capital.iloc[-1])
    profit = final - INITIAL
    expected = {
        "cost_rate": cost, "initial_capital": INITIAL, "final_capital": final,
        "profit": profit, "return_on_initial_capital": profit / INITIAL,
        "risk_turnover": risk, "turnover": risk if kind != "lay" else np.nan,
        "risk_roi": profit / risk if risk else np.nan,
        "roi": profit / risk if risk and kind != "lay" else np.nan,
        "bet_count": n, "leg_count": n * (2 if kind == "dutch" else 1),
        "qualifying_signals": nsignals, "trading_frequency": n / 1470,
        "event_hit_ratio": bets.event_hit.mean() if n else np.nan,
        "positive_profit_hit_ratio": bets.profit_hit.mean() if n else np.nan,
        "expected_gain_per_trade": bets.expected_gain.mean() if n else np.nan,
        "expected_loss_per_trade": bets.expected_loss.mean() if n else np.nan,
        "avg_winning_gain": bets.loc[bets.profit.gt(0), "profit"].mean(),
        "avg_losing_loss": -bets.loc[bets.profit.lt(0), "profit"].mean(),
        "fees": bets.fee.sum(), "max_drawdown": curve.drawdown.max(),
        "active_dates": curve.bet_count.gt(0).sum(),
        "scaled_dates": (curve.commitment_scale.lt(1 - 1e-12) & curve.bet_count.gt(0)).sum(),
        "max_date_exposure": (curve.risk / curve.start_capital.replace(0, np.nan)).max(),
        "nonpositive_complement_payout_bundles": bets.effective_odds.le(1).sum() if kind == "dutch" else 0,
    }
    for field, value in expected.items():
        _near(getattr(row, field), value, row.context_id + "/" + row.variant + " metric " + field)


def _identity(row, original, equity):
    liability = (original.stake * (original.odds - 1)).groupby(original.match_date).sum()
    liability = liability.reindex(equity.match_date, fill_value=0).to_numpy(float)
    mirrored_opening = 2 * INITIAL - equity.start_bankroll.to_numpy(float)
    mirrored_close = 2 * INITIAL - equity.end_bankroll.to_numpy(float)
    shortfall = np.maximum(liability - mirrored_opening, 0)
    identity_profit = -original.profit.sum()
    _near(INITIAL + identity_profit, mirrored_close[-1], "Sign reversal arithmetic identity")
    expected = {
        "original_final_capital": equity.end_bankroll.iloc[-1],
        "arithmetic_mirror_final": mirrored_close[-1],
        "arithmetic_mirror_minimum": min(INITIAL, mirrored_close.min()),
        "original_peak_capital": max(INITIAL, equity.end_bankroll.max()),
        "max_same_date_liability": liability.max(),
        "minimum_additional_opening_cash": shortfall.max(),
        "funding_shortfall_dates": (shortfall > 1e-7).sum(),
        "original_bet_count": len(original),
    }
    for field, value in expected.items():
        _near(getattr(row, field), value, "Identity diagnostic " + field)
    if bool(row.mirror_funding_feasible) != bool(shortfall.max() <= 1e-7):
        raise AssertionError("Recorded mirror funding feasibility is wrong")
    _near(row.arithmetic_mirror_final, 200000, "Bankruptcy implies 200K by construction")


def _bootstrap(metrics, equity, summary):
    """Independently regenerate the declared conditional date-cluster intervals."""
    if int(summary["bootstrap_samples"]) != 9999:
        raise AssertionError("Undeclared bootstrap count")
    description = str(summary.get("bootstrap_basis", "")).lower()
    if not all(word in description for word in ("fixed", "match dates", "season", "no model")):
        raise AssertionError("Bootstrap must disclose its fixed-cashflow, within-season scope")
    rng = np.random.default_rng(20261023)
    checked = 0
    for row in metrics.loc[metrics.variant.eq("dutch_cost_0")].itertuples(index=False):
        curve = equity.loc[equity.context_id.eq(row.context_id) & equity.variant.eq(row.variant)]
        total_profit, total_risk = np.zeros(9999), np.zeros(9999)
        for _, season in curve.groupby("season", sort=True):
            indices = rng.integers(0, len(season), size=(9999, len(season)))
            total_profit += season.profit.to_numpy()[indices].sum(axis=1)
            total_risk += season.risk.to_numpy()[indices].sum(axis=1)
        positive = total_risk > 0
        interval = np.quantile(total_profit[positive] / total_risk[positive], [0.025, 0.975]) if positive.any() else [np.nan, np.nan]
        _near([row.roi_ci_low, row.roi_ci_high], interval, "Declared clustered ROI interval")
        checked += 1
    other = metrics.loc[~metrics.variant.eq("dutch_cost_0"), ["roi_ci_low", "roi_ci_high"]]
    if other.notna().any().any():
        raise AssertionError("Undeclared variants received an interval")
    return checked


def audit(root=ROOT, output=None):
    root = Path(root).resolve()
    output = Path(output).resolve() if output else root / "final_review/epl_results"
    names = ("metrics.csv", "inventory.csv", "original_reconciliation.csv", "identity_diagnostics.csv",
             "bets.parquet", "equity.parquet", "legs.parquet", "signals.parquet", "opportunities.parquet",
             "summary.json", "cohort_summary.json")
    for name in names:
        if not (output / name).is_file():
            raise AssertionError("Missing required export: " + name)
    summary = json.loads((output / "summary.json").read_text(encoding="utf-8"))
    metrics = pd.read_csv(output / "metrics.csv")
    inventory = pd.read_csv(output / "inventory.csv")
    reconciliation = pd.read_csv(output / "original_reconciliation.csv")
    identities = pd.read_csv(output / "identity_diagnostics.csv")
    frames = {name: pd.read_parquet(output / (name + ".parquet"))
              for name in ("bets", "equity", "legs", "signals", "opportunities")}
    for frame in frames.values():
        frame["match_date"] = _date(frame.match_date)
    for frame in (metrics, inventory):
        frame["original_zero"] = _flag(frame.original_zero)
    identities["mirror_funding_feasible"] = _flag(identities.mirror_funding_feasible)
    bets, equity, legs, signals = [frames[name] for name in ("bets", "equity", "legs", "signals")]
    models, source_opportunities, contexts, source_paths = _source_contexts(root)
    dates = source_opportunities.match_date.drop_duplicates().tolist()
    if len(source_opportunities) != 1470 or len(dates) != 453:
        raise AssertionError("Frozen opportunities are not 1,470 fixtures / 453 dates")
    exported_opportunities = frames["opportunities"].sort_values(["match_date", "match_id"]).reset_index(drop=True)
    pd.testing.assert_frame_equal(exported_opportunities, source_opportunities, check_dtype=False)
    if inventory.context_id.duplicated().any() or set(inventory.context_id) != set(contexts):
        raise AssertionError("The exported 51-context inventory differs from frozen sources")
    if metrics.duplicated(["context_id", "variant"]).any() or len(metrics) != 272:
        raise AssertionError("Expected 51 originals + 204 full inverses + 17 prefix sensitivities")
    if set(metrics.context_id) != set(contexts) or set(signals.context_id) != set(contexts):
        raise AssertionError("Unknown or missing context")
    if signals.duplicated(["context_id", "match_id"]).any():
        raise AssertionError("Duplicate full-horizon signal identity")
    if equity.duplicated(["context_id", "variant", "match_date"]).any():
        raise AssertionError("Duplicate account/date wealth identity")
    if bets.duplicated(["context_id", "variant", "match_id"]).any():
        raise AssertionError("Duplicate funded bundle")
    if legs.duplicated(["context_id", "variant", "match_id", "outcome"]).any():
        raise AssertionError("Duplicate complementary leg")
    if legs.variant.isin(["original", "lay_hypothetical"]).any():
        raise AssertionError("Unexpected physical back legs for original/lay accounts")
    _same(sorted(reconciliation.context_id), sorted(contexts), "All original reconciliations")
    zero_contexts = {key for key, value in contexts.items() if value[1] == 0}
    _same(sorted(identities.context_id), sorted(zero_contexts), "All 17 recorded-identity contexts")
    if len(reconciliation) != 51 or len(identities) != 17:
        raise AssertionError("Wrong original or identity reconciliation count")
    expected_counts = {variant: 51 for variant in VARIANTS if variant != "dutch_recorded_prefix"}
    expected_counts["dutch_recorded_prefix"] = 17
    if metrics.groupby("variant").size().to_dict() != expected_counts:
        raise AssertionError("Declared account/cost grid is incomplete")
    checked_bets, checked_contexts, late_signals, edge_cases = 0, 0, 0, 0
    source_curve_by_context = {}
    for context, (config, saved_final, original, original_curve, scope) in contexts.items():
        print(f"Audit {checked_contexts + 1}/51: {context}", flush=True)
        true_signals = _qualifiers(config, models, source_opportunities)
        exported = signals.loc[signals.context_id.eq(context)].sort_values(["match_date", "match_id"])
        _same(exported.match_id, true_signals.match_id, "Full-horizon eligibility, including after ruin")
        for column in ("original_selection", "result", "season"):
            _same(exported[column], true_signals[column], "Native signal " + column)
        _same(exported.match_date, true_signals.match_date, "Native signal dates")
        for column in ("p_original", "original_odds", "odds_H", "odds_D", "odds_A"):
            _near(exported[column], true_signals[column], "Frozen signal " + column)
        for label in LABELS:
            _same(exported["bookmaker_" + label].astype(str), true_signals["bookmaker_" + label].astype(str),
                  "Frozen signal bookmaker " + label)
        _near(exported.requested_risk, REQUEST, "Constant full-horizon requested risk")
        inv = inventory.loc[inventory.context_id.eq(context)].iloc[0]
        if bool(inv.original_zero) != (saved_final == 0) or inv.scope != scope or inv.price_mode != config["odds_mode"]:
            raise AssertionError("Inventory cohort/zero/price classification changed")
        _near([inv.original_final_capital, inv.original_bet_count, inv.qualifying_signals],
              [saved_final, len(original), len(true_signals)], "Inventory source account fields")
        rec = reconciliation.loc[reconciliation.context_id.eq(context)].iloc[0]
        _near([rec.saved_final_capital, rec.replayed_final_capital, rec.bet_count,
               rec.max_stake_error, rec.max_equity_error],
              [saved_final, saved_final, len(original), 0, 0], "Saved original reconciliation")
        if not bool(_flag(pd.Series([rec.source_reproduced])).iloc[0]):
            raise AssertionError("A source account was not reproduced")
        variants = list(VARIANTS) if saved_final == 0 else [j for j in VARIANTS if j != "dutch_recorded_prefix"]
        _same(sorted(metrics.loc[metrics.context_id.eq(context), "variant"]), sorted(variants), "Per-context variant grid")
        for variant in variants:
            b = bets.loc[bets.context_id.eq(context) & bets.variant.eq(variant)].copy()
            e = equity.loc[equity.context_id.eq(context) & equity.variant.eq(variant)].copy()
            l = legs.loc[legs.context_id.eq(context) & legs.variant.eq(variant)].copy()
            b["event_hit"], b["profit_hit"] = _flag(b.event_hit), _flag(b.profit_hit)
            metric = metrics.loc[metrics.context_id.eq(context) & metrics.variant.eq(variant)].iloc[0]
            if metric.kind != VARIANTS[variant][0] or bool(metric.original_zero) != (saved_final == 0):
                raise AssertionError("Metric kind or original bankruptcy label changed")
            if metric.strategy_id != config["strategy_id"] or metric.model_key != config["model_key"] or metric.price_mode != config["odds_mode"]:
                raise AssertionError("Metric source policy identity changed")
            _same(b.kind.unique(), [metric.kind] if len(b) else [], "Bundle kind")
            _near(b.cost_rate, VARIANTS[variant][1], "Bundle cost scenario")
            checked_bets += _account(context, variant, config, true_signals, original, original_curve, b, e, l, dates)
            nsignals = len(original) if variant == "dutch_recorded_prefix" else len(true_signals)
            _metric(metric, b, e.sort_values("match_date"), nsignals)
            if variant == "dutch_cost_0":
                edge_cases += int(b.effective_odds.le(1).sum())
        if saved_final == 0:
            _identity(identities.loc[identities.context_id.eq(context)].iloc[0], original, original_curve)
            ruined = original_curve.loc[original_curve.end_bankroll.eq(0), "match_date"].min()
            late_signals += int(true_signals.match_date.gt(ruined).sum())
        source_curve_by_context[context] = original_curve
        checked_contexts += 1
    metric_keys = set(map(tuple, metrics[["context_id", "variant"]].to_numpy()))
    for frame in (bets, equity, legs):
        if not set(map(tuple, frame[["context_id", "variant"]].drop_duplicates().to_numpy())).issubset(metric_keys):
            raise AssertionError("An exported ledger contains an undeclared account")
    if len(equity) != 272 * 453:
        raise AssertionError("Not every account preserves every priced date")
    if checked_bets != len(bets):
        raise AssertionError("Some funded bundles escaped audit")
    expected_leg_count = 2 * int(metrics.loc[metrics.kind.eq("dutch"), "bet_count"].sum())
    if len(legs) != expected_leg_count:
        raise AssertionError("Wrong total Dutch leg count")
    intervals = _bootstrap(metrics, equity, summary)
    cohorts = json.loads((output / "cohort_summary.json").read_text(encoding="utf-8"))
    expected_cohorts = []
    for (variant, zero), group in metrics.loc[~metrics.variant.eq("dutch_recorded_prefix")].groupby(["variant", "original_zero"]):
        expected_cohorts.append({"variant": variant, "original_zero": bool(zero), "accounts": len(group),
                                "profitable_accounts": int(group.final_capital.gt(INITIAL + 1e-7).sum()),
                                "bankrupt_accounts": int(group.final_capital.le(1e-7).sum()),
                                "median_final_capital": float(group.final_capital.median()),
                                "min_final_capital": float(group.final_capital.min()),
                                "max_final_capital": float(group.final_capital.max())})
    for exported_cohorts in (cohorts, summary["cohorts"]):
        if len(exported_cohorts) != len(expected_cohorts):
            raise AssertionError("Cohort summaries omit a declared variant/group")
        for actual, expected in zip(exported_cohorts, expected_cohorts):
            for field in ("variant", "original_zero", "accounts", "profitable_accounts", "bankrupt_accounts"):
                if actual[field] != expected[field]:
                    raise AssertionError("Cohort summary identity/count differs: " + field)
            for field in ("median_final_capital", "min_final_capital", "max_final_capital"):
                _near(actual[field], expected[field], "Cohort summary " + field)
    for key, expected in {"contexts": 51, "original_zero_contexts": 17, "nonzero_controls": 34,
                          "main_fixed_cohort": 47, "additional_reference_zero_contexts": 4,
                          "funded_complement_accounts": 153, "hypothetical_lay_accounts": 51,
                          "prefix_complement_diagnostics": 17, "recorded_identity_diagnostics": 17,
                          "fixtures": 1470, "dates": 453}.items():
        if summary.get(key) != expected:
            raise AssertionError("Wrong summary population: " + key)
    checked_hashes = 0
    for relative, digest in summary["source_sha256"].items():
        if _sha(root / relative) != digest:
            raise AssertionError("A frozen source hash changed: " + relative)
        checked_hashes += 1
    for name, digest in summary["outputs_sha256"].items():
        if _sha(output / name) != digest:
            raise AssertionError("An exported output hash changed: " + name)
        checked_hashes += 1
    # Record actual source hashes independently even if an export manifest omits
    # them; the original probability and price panel are indispensable inputs.
    independently_hashed = {str(path.relative_to(root)): _sha(path) for path in source_paths}
    return {"status": "passed", "audit_implementation": str(Path(__file__).relative_to(root)),
            "audit_sha256": _sha(__file__), "source_contexts": checked_contexts,
            "original_accounts_reproduced": 51, "bankrupt_source_contexts": 17,
            "funded_full_horizon_inverse_accounts": 204,
            "additional_recorded_prefix_dutch_diagnostics": 17,
            "recorded_sign_identity_diagnostics": 17, "funded_bundle_rows_checked": checked_bets,
            "physical_complement_leg_rows_checked": len(legs), "wealth_points_checked": len(equity),
            "match_dates_per_account": 453, "qualified_signals_after_original_ruin": late_signals,
            "nonpositive_effective_odds_primary_bundles": edge_cases,
            "conditional_bootstrap_intervals_recomputed": intervals,
            "manifest_hashes_checked": checked_hashes, "independent_input_sha256": independently_hashed,
            "checks": ["Complete frozen source cohort, full-horizon qualification, filters and deterministic tie order",
                       "Actual archived best/reference prices and bookmaker identities for both complementary legs",
                       "H/D/A payoff vectors, per-portfolio positive-profit cost and nonnegative expected gain/loss",
                       "Joint match-date liability/stake reservation, no same-date proceeds, absorbing bankruptcy",
                       "All original trade/wealth points, all funded bundles/legs, endpoints and reported metrics",
                       "Recorded sign identity plus opening-cash liability feasibility, independent of endpoint",
                       "All declared cost variants, controls and complete within-season fixed-cashflow bootstrap"],
            "interpretation": "Accounting and reproducibility checks only; retrospective reversals and conditional intervals do not establish prospective profitability or remove selection bias."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--results", type=Path)
    args = parser.parse_args()
    output = args.results or args.root / "final_review/epl_results"
    result = audit(args.root, output)
    target = output / "independent_audit.json"
    target.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in result.items() if key not in {"checks", "independent_input_sha256"}}, indent=2))


if __name__ == "__main__":
    main()
