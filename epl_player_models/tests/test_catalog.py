from epl_player_models.catalog import build_catalog, model_members


def test_all_eight_variants_receive_every_quote_and_sizing_combination():
    catalog = build_catalog()
    assert [r["strategy_id"] for r in catalog] == [f"P{i:03d}" for i in range(1, 33)]
    for member in model_members():
        rows = [r for r in catalog if r["model_key"] == member["model_key"]]
        assert {(r["odds_mode"], r["staking"]) for r in rows} == {(q, s) for q in ("best", "reference") for s in ("fixed", "kelly")}
        assert all(r["min_edge"] == .05 and r["fixed_stake"] == 1000 and r["kelly_fraction"] == .25 and r["max_bet_fraction"] == .02 for r in rows)


def test_catalog_identity_does_not_change_between_calls_or_allow_external_mutation():
    original = build_catalog()
    changed = build_catalog(); changed[0]["allowed_outcomes"].clear()
    assert original == build_catalog()
