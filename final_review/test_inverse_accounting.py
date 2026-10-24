"""Boundary cases that historical samples alone may not expose."""
import numpy as np
import pandas as pd

from final_review.epl_inverse import simulate


def sample(prices=(2., 4., 4.), outcomes="HDA", n=3):
    rows = []
    for i in range(n):
        rows.append({"match_id": str(i), "match_date": pd.Timestamp("2025-08-15"),
                     "season": "2025-26", "result": outcomes[i % len(outcomes)],
                     "original_selection": "H", "p_original": .6,
                     "original_odds": prices[0], "requested_risk": 1000.,
                     **{"odds_" + j: p for j, p in zip("HDA", prices)},
                     **{"bookmaker_" + j: "test" for j in "HDA"}})
    return pd.DataFrame(rows)


def run(frame, kind="dutch", cost=0.):
    return simulate(frame, frame, context_id="test", variant="test", kind=kind, cost_rate=cost)


def test_complement_includes_draw_and_prices_each_leg():
    b, _, legs = run(sample())
    np.testing.assert_allclose(b.profit, [-1000, 1000, 1000])
    assert len(legs) == 6
    np.testing.assert_allclose(legs.groupby("match_id").stake.sum(), 1000.)
    assert b.event_hit.tolist() == [False, True, True]


def test_cost_is_on_positive_net_bundle_profit():
    b, _, _ = run(sample(), cost=.05)
    np.testing.assert_allclose(b.fee, [0, 50, 50])
    np.testing.assert_allclose(b.profit, [-1000, 950, 950])
    np.testing.assert_allclose(b.expected_gain, 380.)
    np.testing.assert_allclose(b.expected_loss, 600.)


def test_complement_event_hit_can_still_lose_money():
    b, _, _ = run(sample(prices=(10., 1.5, 1.5)))
    np.testing.assert_allclose(b.profit, [-1000, -250, -250])
    assert b.event_hit.tolist() == [False, True, True]
    assert not b.profit_hit.any()
    np.testing.assert_allclose(b.expected_gain, 0.)
    np.testing.assert_allclose(b.expected_loss, 700.)


def test_joint_funding_and_absorbing_bankruptcy():
    frame = sample(outcomes="H", n=200)
    later = sample(outcomes="D", n=1)
    later["match_id"] = "later"
    later["match_date"] = pd.Timestamp("2025-08-16")
    frame = pd.concat([frame, later], ignore_index=True)
    b, eq, _ = run(frame)
    assert len(b) == 200
    np.testing.assert_allclose(b.risk, 500.)
    np.testing.assert_allclose(eq.end_capital, 0.)
    assert eq.signal_count.tolist() == [200, 1]


def test_fair_prices_match_liability_matched_lay():
    frame = sample(prices=(2., 4., 4.))
    back, _, _ = run(frame)
    lay, _, _ = run(frame, kind="lay")
    np.testing.assert_allclose(back.profit, lay.profit)
    np.testing.assert_allclose(lay.counterstake, 1000.)
