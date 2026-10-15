"""Focused completeness and offline-rendering checks; no model fitting."""
import json

import numpy as np
import pandas as pd
import pytest
from pypdf import PdfReader

from epl_strategy_lab.catalog import build_catalog
from epl_strategy_lab.report import INITIAL, _appendix, _body, _graphs, _human, _pdf, _validate


@pytest.fixture
def flat_accounts():
    catalog=build_catalog();ids=[c["strategy_id"] for c in catalog]
    dates=pd.to_datetime(["2025-08-15"]+list(pd.date_range("2025-08-16",periods=111))+["2026-05-24"])
    equity=pd.DataFrame([{"strategy_id":sid,"match_date":date,"end_bankroll":INITIAL} for sid in ids for date in dates])
    anchors=pd.DataFrame([{"strategy_id":sid,"match_date":pd.Timestamp("2025-08-14"),"end_bankroll":INITIAL,"is_initial":True} for sid in ids])
    graph=pd.concat([anchors,equity.assign(is_initial=False)],ignore_index=True)
    metrics=pd.DataFrame([{"strategy_id":sid,"prediction_count":374,"matched_valid_odds_count":374,"initial_capital_sum_units":INITIAL,
        "profit":0.,"bet_count":0,"hit_ratio":np.nan,"trading_frequency":0.,"avg_winning_gain_units":np.nan,"avg_losing_loss_units":np.nan,
        "expected_gain_per_trade_units":np.nan,"expected_loss_per_trade_units":np.nan,"roi":np.nan,"max_drawdown":0.,"return_on_initial_capital":0.} for sid in ids])
    bets=pd.DataFrame(columns=["strategy_id"])
    return catalog,metrics,graph,equity,bets


def test_every_account_has_pre_match_100k_and_complete_shared_dates(flat_accounts):
    catalog,metrics,graph,equity,bets=flat_accounts
    checked,_,ids,anchor=_validate(catalog,metrics,graph,equity,bets)
    assert len(ids)==84 and len(checked)==84*114 and anchor==pd.Timestamp("2025-08-14")
    assert checked.loc[checked.is_initial].end_bankroll.eq(100000).all()


def test_missing_trace_or_wrong_anchor_is_rejected(flat_accounts):
    catalog,metrics,graph,equity,bets=flat_accounts
    with pytest.raises(ValueError,match="IDs differ"):
        _validate(catalog,metrics,graph.loc[graph.strategy_id.ne("S084")],equity,bets)
    graph.loc[graph.is_initial & graph.strategy_id.eq("S084"),"end_bankroll"]=99999
    with pytest.raises(ValueError,match="anchor"):_validate(catalog,metrics,graph,equity,bets)


def test_appendix_preserves_every_config_and_explains_consensus_sizing():
    catalog=build_catalog();entries=_appendix(catalog)
    assert [e["strategy_id"] for e in entries]==[c["strategy_id"] for c in catalog]
    assert [json.loads(e["exact_config"]) for e in entries]==catalog
    consensus=entries[61]["explanation"]
    assert "at least 6 of 8" in consensus and "without searching another outcome" in consensus
    assert "each weight is 1/8" in consensus
    assert "best eligible individual-book prices" in _human(catalog[4])
    assert "Bet365 reference prices" in _human(catalog[6])
    assert "date-start balance" in _human(catalog[51])
    assert "B×min(cap" in _human(catalog[55])


def test_offline_html_has_all_initially_visible_traces_and_same_complete_appendix(flat_accounts,tmp_path):
    catalog,_,graph,_,_=flat_accounts
    # Two traces suffice to exercise bundling/toggling; production ID coverage is
    # separately enforced above for all84 accounts.
    configs=[catalog[0],catalog[-1]];selected=graph.loc[graph.strategy_id.isin(["S001","S084"])]
    info=_graphs(configs,selected,tmp_path,_appendix(configs))
    html=(tmp_path/"all_strategies_100k.html").read_text(encoding="utf-8")
    assert info["trace_ids"]==["S001","S084"] and info["initially_visible_traces"]==2
    assert "Plotly.newPlot" in html and "<script src=" not in html
    assert "Show all" in html and "Hide all" in html
    assert html.index("Appendix — complete")<html.index("id='S001'")<html.index("id='S084'")


def test_complete_pdf_appendix_is_last_and_all84_entries_survive_layout(flat_accounts,tmp_path):
    catalog,metrics,_,_,_=flat_accounts
    # Reuse the tiny real graph from the previous interface, without fitting or
    # manufacturing any research results. This document stays in pytest tmp.
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots(figsize=(11.8,7.4));ax.plot([0,1],[100000,100000]);image=tmp_path/"layout.png";fig.savefig(image);plt.close(fig)
    pages,_,_=_body(catalog,metrics,[c["strategy_id"] for c in catalog],image)
    entries=_appendix(catalog);pdf=tmp_path/"layout.pdf";_pdf(pages,entries,pdf)
    text=" ".join("\n".join(p.extract_text() or "" for p in PdfReader(pdf).pages).split())
    tail=text.split("Appendix — complete strategy definitions (final section)",1)[1]
    assert all(" ".join(e["title"].split()) in tail for e in entries)
    assert "S084" in (PdfReader(pdf).pages[-1].extract_text() or "")
