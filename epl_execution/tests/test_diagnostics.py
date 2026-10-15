"""Independent small cashflow examples and identity/source integrity failures."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from epl_execution.diagnostics import (
    book_concentration, closing_reference_diagnostics, payoff_attribution, quote_diagnostics,
)


def opportunities():
    panel = pd.DataFrame({
        "match_id": ["m1", "m2"], "match_date": ["2025-08-15", "2025-08-16"],
        "season": ["2025-26"] * 2, "result": ["H", "D"], "snapshot_type": ["preclosing"] * 2,
        "reference_bookmaker": ["Bet365"] * 2,
        "ref_odds_H": [2., 2.], "ref_odds_D": [4., 3.], "ref_odds_A": [4., 4.],
        "odds_H": [2.2, 2.1], "odds_D": [4., 3.3], "odds_A": [4.5, 4.2],
        "bookmaker_H": ["Alpha", "Beta"], "bookmaker_D": ["Bet365", "Beta"],
        "bookmaker_A": ["Alpha", "Beta"], "reference_quote_timestamp_utc": [None, None],
        "quote_timestamp_H_utc": [None, None], "quote_timestamp_D_utc": [None, None],
        "quote_timestamp_A_utc": [None, None],
    })
    return panel


def bets():
    return pd.DataFrame({
        "match_id": ["m1", "m2"], "match_date": ["2025-08-15", "2025-08-16"],
        "strategy_id": ["S001"] * 2, "selection": ["H", "A"], "probability": [.6, .3],
        "odds": [2.2, 4.2], "stake": [100., 50.], "bookmaker": ["Alpha", "Beta"],
        "won": [True, False], "gross_return": [220., 0.], "profit": [120., -50.],
    })


def attribute(ledger=None, panel=None):
    return payoff_attribution(bets() if ledger is None else ledger,
                              opportunities() if panel is None else panel,
                              account_id="account", strategy_id="S001", scope="single", season="2025-26")


def test_hand_computed_cash_payoff_and_nonunit_market_overround():
    actual = attribute()
    # m1 has inverse-odds sum 1; m2 has 13/12, hence selected A q=3/13.
    market = 10 + 50 * ((3 / 13) * 4.2 - 1)
    assert actual["bet_count"] == 2
    assert actual["turnover"] == 150
    assert actual["actual_profit"] == pytest.approx(70)
    assert actual["model_expected_profit"] == pytest.approx(45)
    assert actual["market_implied_expected_profit"] == pytest.approx(market)
    assert actual["model_probability_premium"] == pytest.approx(45 - market)
    assert actual["outcome_residual"] == pytest.approx(70 - market)
    assert actual["payoff_forecast_error"] == pytest.approx(25)
    assert actual["expected_gain_total"] == pytest.approx(120)
    assert actual["expected_loss_total"] == pytest.approx(75)
    assert actual["actual_gain_total"] == pytest.approx(120)
    assert actual["actual_loss_total"] == pytest.approx(50)
    assert actual["archived_ref_fixed_bet_profit"] == pytest.approx(50)
    assert actual["realized_price_uplift_vs_reference"] == pytest.approx(20)
    assert actual["actual_profit_per_turnover"] == pytest.approx(70 / 150)
    assert actual["model_expected_profit_per_trade"] == pytest.approx(22.5)
    assert actual["hit_ratio"] == .5
    assert actual["mean_model_probability"] == pytest.approx(.45)
    assert actual["mean_reference_probability"] == pytest.approx((.5 + 3 / 13) / 2)
    for key in ("actual_profit_identity_residual", "model_expected_identity_residual", "price_uplift_identity_residual"):
        assert actual[key] == pytest.approx(0, abs=1e-12)
    assert actual["reference_probability_is_truth"] is False
    assert actual["fixed_exposure_reference_is_funded_replay"] is False


def test_cash_policy_has_zero_totals_and_undefined_per_bet_statistics():
    actual = attribute(bets().iloc[:0])
    assert actual["bet_count"] == 0
    for key in ("actual_profit", "model_expected_profit", "market_implied_expected_profit", "expected_gain_total", "expected_loss_total"):
        assert actual[key] == 0
    for key in ("hit_ratio", "mean_model_probability", "actual_profit_per_turnover", "actual_profit_per_trade"):
        assert np.isnan(actual[key])
    assert book_concentration(bets().iloc[:0], opportunities(), {"account_id": "cash"}).empty


def test_attribution_accepts_reference_book_original_bets_without_fabricating_price_lift():
    ledger = bets()
    ledger["odds"] = [2., 4.]
    ledger["gross_return"] = [200., 0.]
    ledger["profit"] = [100., -50.]
    ledger["bookmaker"] = "Bet365"
    result = attribute(ledger)
    assert result["actual_profit"] == 50
    assert result["realized_price_uplift_vs_reference"] == 0


@pytest.mark.parametrize("change, message", [
    (lambda b: b.assign(probability=[1.1, .3]), "probabilities"),
    (lambda b: b.assign(won=[False, False]), "won flag"),
    (lambda b: b.assign(profit=[121., -50.]), "Recorded profit"),
    (lambda b: b.assign(gross_return=[221., 0.]), "gross return"),
    (lambda b: b.assign(match_id=["m1", "unknown"]), "absent"),
    (lambda b: b.assign(match_id=["m1", "m1"]), "at most one"),
    (lambda b: b.assign(match_date=["2025-08-14", "2025-08-16"]), "date conflicts"),
    (lambda b: b.assign(strategy_id="S002"), "strategy identity"),
])
def test_invalid_recorded_bet_or_identity_fails(change, message):
    with pytest.raises(ValueError, match=message):
        attribute(change(bets()))


def test_supplied_market_probability_must_reconcile_with_reference_odds():
    panel = opportunities()
    panel[["ref_p_H", "ref_p_D", "ref_p_A"]] = [.4, .3, .3]
    with pytest.raises(ValueError, match="disagree"):
        attribute(panel=panel)


def test_quote_audit_counts_native_cells_and_missing_clocks():
    summary, cells, books = quote_diagnostics(opportunities(), scope="single")
    assert summary["match_count"] == 2
    assert summary["outcome_quote_count"] == 6
    assert summary["strict_best_price_uplift_count"] == 5
    assert summary["reference_timestamp_missing_count"] == 2
    for outcome in "HDA":
        assert summary[f"best_{outcome}_timestamp_missing_count"] == 2
    assert summary["executable_quotes_verified"] is False
    assert summary["verified_closing_line_value"] is False
    assert not cells.executable_quotes_verified.any()
    assert cells.loc[(cells.match_id == "m1") & (cells.outcome == "H"), "price_ratio_best_to_reference"].iloc[0] == 1.1
    assert books.selected_quote_count.sum() == 6
    assert books.selected_quote_share.sum() == pytest.approx(1)


def test_quote_audit_fails_if_best_price_is_below_eligible_reference():
    panel = opportunities()
    panel.loc[0, "odds_H"] = 1.9
    with pytest.raises(ValueError, match="at least"):
        quote_diagnostics(panel, scope="single")


def test_quote_audit_rejects_malformed_instead_of_relabeling_missing_timestamp():
    panel = opportunities()
    panel.loc[0, "quote_timestamp_A_utc"] = "unknown-time"
    with pytest.raises(ValueError, match="malformed"):
        quote_diagnostics(panel, scope="single")


def test_book_concentration_is_an_account_property_with_signed_profit_shares():
    actual = book_concentration(bets(), opportunities(), {"account_id": "account", "scope": "single"}).set_index("bookmaker")
    assert actual.stake.sum() == 150
    assert actual.total_profit.sum() == pytest.approx(70)
    assert actual.loc["Alpha", "stake_share"] == pytest.approx(2 / 3)
    assert actual.loc["Beta", "signed_profit_share"] == pytest.approx(-5 / 7)
    assert actual.loc["Alpha", "signed_profit_share"] == pytest.approx(12 / 7)
    assert np.allclose(actual.concentration_hhi_by_stake, 5 / 9)
    assert np.allclose(actual.concentration_hhi_by_bet_count, .5)
    assert np.allclose(actual.largest_book_stake_share, 2 / 3)


def test_book_metadata_cannot_overwrite_statistics():
    with pytest.raises(ValueError, match="overwrite"):
        book_concentration(bets(), opportunities(), {"stake": 0})


def test_closing_benchmark_aligns_shuffled_native_ids_without_lookahead_claim():
    entry = opportunities()
    close = entry.iloc[::-1].copy()
    close["snapshot_type"] = "closing"
    close.loc[close.match_id == "m1", "ref_odds_H"] = 2.5
    summary, frame = closing_reference_diagnostics(entry, close, scope="single")
    assert summary["match_count"] == 2
    assert summary["entry_timestamp_missing_count"] == 2
    assert summary["closing_timestamp_missing_count"] == 2
    home = frame.loc[(frame.match_id == "m1") & (frame.outcome == "H")].iloc[0]
    assert home.entry_to_closing_decimal_ratio == pytest.approx(.8)
    # Closing normalized inverse weights: .4/(.4+.25+.25)=4/9.
    assert home.closing_reference_probability == pytest.approx(4 / 9)
    assert home.closing_minus_entry_probability == pytest.approx(4 / 9 - .5)
    assert frame.bookmaker.eq("Bet365").all()
    assert not frame.verified_closing_line_value.any()
    assert not frame.used_to_select_or_size_bets.any()


@pytest.mark.parametrize("mutation, message", [
    (lambda c: c.iloc[:1], "populations differ"),
    (lambda c: c.assign(result=["D", "D"]), "result conflicts"),
    (lambda c: c.assign(snapshot_type="preclosing"), "closing snapshots"),
])
def test_closing_mismatched_population_result_or_snapshot_fails(mutation, message):
    entry = opportunities()
    close = entry.assign(snapshot_type="closing")
    with pytest.raises(ValueError, match=message):
        closing_reference_diagnostics(entry, mutation(close), scope="single")
