from epl_prospective.build import original_ledger_bytes, verify_original_prefix

import pytest


def test_original_ledger_anchor_is_the_exact_pre_result_commit():
    original = original_ledger_bytes()
    assert len(original.splitlines()) == 40
    verify_original_prefix(original + b'{"new": "record"}\n', original)


@pytest.mark.parametrize("change", ["edit", "reorder", "truncate"])
def test_original_prefix_cannot_be_rewritten_for_new_results(change):
    original = b"first\nsecond\n"
    current = {"edit": b"first\nchanged\n", "reorder": b"second\nfirst\n", "truncate": b"first\n"}[change]
    with pytest.raises(AssertionError): verify_original_prefix(current, original)
