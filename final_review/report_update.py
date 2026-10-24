"""Extend a copied final report with the bankruptcy-opposite audit.

The caller copies the frozen report into ``output_dir / 'report'`` first.
This module writes only to that new copy; original report/data files are read-only.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Iterable

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
BASE_REPORT = ROOT / "final_deliverables/results/20261023_joint_final/report"


def _tex(value: Any) -> str:
    text = str(value)
    mapping = {
        "\\": r"\textbackslash{}", "&": r"\&", "%": r"\%",
        "$": r"\$", "#": r"\#", "_": r"\_", "{": r"\{",
        "}": r"\}", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}",
    }
    return "".join(mapping.get(c, c) for c in text)


def _num(value: Any, decimals: int = 0) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "--"
    return f"{number:,.{decimals}f}" if math.isfinite(number) else "--"


def _pct(value: Any, decimals: int = 2) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "--"
    return f"{100 * number:.{decimals}f}\\%" if math.isfinite(number) else "--"


def _pick(columns: Iterable[str], aliases: Iterable[str], *, required: bool = True) -> str | None:
    available = set(columns)
    for alias in aliases:
        if alias in available:
            return alias
    if required:
        raise ValueError(f"Missing expected field, aliases={list(aliases)}; available={sorted(available)}")
    return None


def _column(df: pd.DataFrame, aliases: Iterable[str], default: Any = None) -> pd.Series:
    name = _pick(df.columns, aliases, required=False)
    if name is not None:
        return df[name]
    return pd.Series(default, index=df.index)


def _truth(series: pd.Series) -> pd.Series:
    return series.astype(str).str.lower().isin(["true", "1", "1.0", "yes"])


def _short_table(headers: list[str], rows: list[list[str]], spec: str) -> str:
    body = "\n".join(" & ".join(row) + r" \\" for row in rows)
    return (
        r"\begin{tabular}{" + spec + "}\n\\toprule\n"
        + " & ".join(headers) + r" \\ \midrule" + "\n"
        + body + "\n\\bottomrule\n\\end{tabular}\n"
    )


def _long_table(headers: list[str], rows: list[list[str]], spec: str, caption: str, label: str) -> str:
    heading = " & ".join(headers) + r" \\ \midrule" + "\n"
    return (
        r"\begin{longtable}{" + spec + "}\n"
        + r"\caption{" + caption + r"}\label{" + label + r"}\\" + "\n"
        + "\\toprule\n" + heading + "\\endfirsthead\n\\toprule\n"
        + heading + "\\endhead\n\\bottomrule\n\\endfoot\n"
        + "\n".join(" & ".join(row) + r" \\" for row in rows)
        + "\n\\end{longtable}\n"
    )


def _insert_before(text: str, anchor: str, addition: str) -> str:
    if text.count(anchor) != 1:
        raise ValueError(f"Expected one report anchor: {anchor!r}; got {text.count(anchor)}")
    return text.replace(anchor, addition + "\n" + anchor, 1)


def _replace_once(text: str, old: str, new: str) -> str:
    if text.count(old) != 1:
        raise ValueError(f"Expected one text block to replace, found {text.count(old)}: {old[:70]}")
    return text.replace(old, new, 1)


def _normalise_epl(metrics: pd.DataFrame) -> pd.DataFrame:
    """Translate exported audit field names into the report's compact schema."""
    d = pd.DataFrame(index=metrics.index)
    d["strategy_id"] = _column(metrics, ["strategy_id"])
    d["context_id"] = _column(metrics, ["context_id", "account_context_id", "original_context_id"], "")
    d["mode"] = _column(metrics, ["mode", "method", "inverse_mode", "inverse_method", "execution_mode", "variant"], "")
    d["cost"] = pd.to_numeric(_column(metrics, ["cost_rate", "cost_fraction", "commission_rate", "haircut_rate", "cost"], 0), errors="raise")
    d["final"] = pd.to_numeric(metrics[_pick(metrics.columns, ["final_capital", "final_capital_sum_units", "ending_capital", "final_bankroll"])], errors="raise")
    d["initial"] = pd.to_numeric(_column(metrics, ["initial_capital", "initial_bankroll", "initial_capital_sum_units"], 100000), errors="raise")
    d["original_final"] = pd.to_numeric(_column(metrics, ["original_final_capital", "original_final_capital_sum_units", "original_ending_capital", "base_final_capital"], float("nan")), errors="coerce")
    d["bankrupt"] = _truth(_column(metrics, ["original_zero", "original_bankrupt", "original_is_bankrupt", "is_original_bankrupt", "bankrupt_context", "selected_bankrupt"], False))
    d["is_main"] = _truth(_column(metrics, ["is_main", "main_context", "is_main_context", "is_main_cohort", "main_catalog_context"], True))
    d["cohort"] = _column(metrics, ["cohort", "cohort_role", "context_role", "group"], "")
    d["odds"] = _column(metrics, ["original_odds_mode", "odds_mode", "price_mode", "quote_mode"], "")
    d["bets"] = pd.to_numeric(_column(metrics, ["bet_count", "n_bets", "funded_bets", "placed_bets"], float("nan")), errors="coerce")
    d["signals"] = pd.to_numeric(_column(metrics, ["qualifying_signals", "qualifying_signal_count", "full_horizon_signals", "full_horizon_original_signals", "signal_count"], float("nan")), errors="coerce")
    d["hit"] = pd.to_numeric(_column(metrics, ["hit_ratio", "complement_event_hit_ratio", "event_hit_ratio"], float("nan")), errors="coerce")
    d["profit_hit"] = pd.to_numeric(_column(metrics, ["positive_profit_hit_ratio", "profitable_bet_ratio", "positive_profit_ratio", "net_profit_hit_ratio", "profitable_bundle_ratio"], float("nan")), errors="coerce")
    d["frequency"] = pd.to_numeric(_column(metrics, ["trading_frequency", "trade_rate_all_predictions"], float("nan")), errors="coerce")
    d["turnover"] = pd.to_numeric(_column(metrics, ["risk_turnover", "turnover", "total_risk", "total_risk_units"], float("nan")), errors="coerce")
    d["roi"] = pd.to_numeric(_column(metrics, ["risk_roi", "roi_on_stakes", "roi_on_risk", "roi"], float("nan")), errors="coerce")
    d["drawdown"] = pd.to_numeric(_column(metrics, ["max_drawdown"], float("nan")), errors="coerce")
    d["expected_gain"] = pd.to_numeric(_column(metrics, ["expected_gain_per_trade", "expected_gain_per_trade_units"], float("nan")), errors="coerce")
    d["expected_loss"] = pd.to_numeric(_column(metrics, ["expected_loss_per_trade", "expected_loss_per_trade_units"], float("nan")), errors="coerce")
    d["realized_win"] = pd.to_numeric(_column(metrics, ["avg_winning_gain", "avg_winning_gain_units"], float("nan")), errors="coerce")
    d["realized_loss"] = pd.to_numeric(_column(metrics, ["avg_losing_loss", "avg_losing_loss_units"], float("nan")), errors="coerce")
    d["ci_low"] = pd.to_numeric(_column(metrics, ["roi_ci_low"], float("nan")), errors="coerce")
    d["ci_high"] = pd.to_numeric(_column(metrics, ["roi_ci_high"], float("nan")), errors="coerce")
    if d["mode"].eq("").all():
        raise ValueError("EPL inverse metrics must identify complement versus hypothetical lay modes.")
    if d["context_id"].eq("").all():
        d["context_id"] = d["strategy_id"].astype(str) + ":" + d["odds"].astype(str)
    # The engine exports the original variant in the same file, making the
    # exact capital and main/reference context distinction directly recoverable.
    original = d[d["mode"].eq("original")].set_index("context_id")["final"]
    if len(original):
        d["original_final"] = d["original_final"].fillna(d["context_id"].map(original))
    if not any(k in metrics for k in ["is_main", "main_context", "is_main_context", "is_main_cohort", "main_catalog_context"]):
        d["is_main"] = ~d["context_id"].isin([f"{sid}__reference" for sid in ["S033", "S039", "S041", "S043"]])
    # Explicit original final capital overrides a redundant exported flag.
    known = d["original_final"].notna()
    d.loc[known, "bankrupt"] = d.loc[known, "original_final"].abs() < 1e-8
    return d


def _mode_masks(d: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    words = d["mode"].astype(str).str.lower()
    full = ~words.str.contains("prefix", regex=False)
    return words.str.contains("complement|dutch", regex=True) & full, words.str.contains("lay", regex=True) & full


def _fit_width(table: str) -> str:
    return "\\resizebox{\\linewidth}{!}{%\n" + table + "}%\n"


def _nba_material(nba_dir: Path, tables_dir: Path) -> tuple[str, str]:
    metrics = pd.read_csv(nba_dir / "inverse_metrics.csv")
    intervals = pd.read_csv(nba_dir / "conditional_uncertainty.csv")
    full = metrics[metrics["mode"].eq("opposite_full_horizon")].copy()
    original = metrics[metrics["mode"].eq("original")].copy()
    if len(full) != 2 or len(original) != 2:
        raise ValueError("Expected the two bankrupt annual NBA accounts and their full-horizon reversals.")
    rows = []
    for _, row in full.sort_values("branch", ascending=False).iterrows():
        ci = intervals[(intervals["branch"] == row.branch) & (intervals["metric"] == "roi_on_stakes")].iloc[0]
        branch = "Calibration" if row.branch == "cal" else "Accuracy"
        rows.append([branch, _num(row.full_horizon_original_signals), _num(row.n_bets), _num(row.final_capital, 2), _pct(row.return_on_initial_capital), _pct(row.hit_ratio), _pct(row.roi_on_stakes), f"[{_pct(ci.ci_lower)}, {_pct(ci.ci_upper)}]"])
    (tables_dir / "nba_inverse_main.tex").write_text(_fit_width(_short_table(
        ["Branch", "Signals", "Bets", "End capital", "Capital return", "Hit", "Stake yield", "95\\% interval"], rows, "lrrrrrrl")), encoding="utf-8")
    all_rows = []
    for _, row in metrics.sort_values(["branch", "mode"]).iterrows():
        branch = "Cal." if row.branch == "cal" else "Acc."
        mode = {"original": "Original", "opposite_recorded_prefix": "Opposite prefix", "opposite_full_horizon": "Opposite full"}[row["mode"]]
        all_rows.append([branch, mode, _num(row.n_bets), _num(row.final_capital, 2), _pct(row.hit_ratio), _num(row.expected_gain_per_trade, 2), _num(row.expected_loss_per_trade, 2), _pct(row.trading_frequency), _pct(row.max_drawdown)])
    nba_appendix = r"""
\subsection{NBA zero-account details}
All rows use the 2017/18 rolling logistic-only reconstruction with a fresh
10,000-unit account. The original requests 100; prefix reversals request the
recorded original amounts, including a final cash-clamped stake. Full-horizon
reversals request 100 per frozen original signal. ``Expected'' means the
original model's probability-weighted payoff for the contrarian outcome.
\begin{center}\scriptsize
""" + _short_table(["Branch", "Mode", "Bets", "End", "Hit", "Exp. gain", "Exp. loss", "Frequency", "Drawdown"], all_rows, "llrrrrrrr") + r"""
\end{center}
\sourcefile{data/nba_inverse_metrics.csv; data/nba_conditional_uncertainty.csv}
"""
    nba_main = r"""
% FINAL_REVIEW_NBA_START
\subsection{Opposite bets after bankruptcy: NBA diagnostic}
Both zero annual accounts occur in the 2017/18 logistic-only extension, not
the four-family 2018/19 experiment. We reconstruct all nine annual windows:
all 18 flat-stake returns match the notebook's printed precision. This
method-and-endpoint reconciliation does not recover saved fitted weights or
prove byte-identical original predictions. Only two of the 36 audited annual
flat/Kelly accounts are exactly zero; Kelly leaves positive balances.

For each zero account we keep the original qualifying dates and forecast,
back the other team at its archived opposing moneyline, and request 100
(1\% of initial 10,000). The inverse continues after the original account
stops, clamps each stake to its own cash, and retains source sequential
settlement. It is not a negative copy of the original profit.

\resulttable{NBA full-horizon opposite bets, 2017/18; original ending capital
is zero in both rows. Intervals bootstrap whole dates with fitted predictions,
signals and stakes fixed.}{tab:nba_inverse}{nba_inverse_main.tex}

The calibration-direction inverse ends at 11,148.07, while the
accuracy-direction inverse ends at 8,785.30. Reversing only the recorded
pre-bankruptcy bets instead ends at 9,420.33 and 8,155.98: the observation
window matters. Both full-horizon stake-yield intervals contain zero.
These cases were selected after observing ruin; archived opposing quotes
and sequential funding are not evidence of executable fills or new alpha.
% FINAL_REVIEW_NBA_END
"""
    return nba_main, nba_appendix


def update_report(output_dir: Path, epl_summary: dict, nba_dir: Path) -> None:
    """Update only ``output_dir/report`` using completed inverse exports.

    Required new exports are ``data/epl_inverse_metrics.csv``,
    ``data/epl_identity_diagnostics.csv`` and ``data/epl_cohort_summary.json``.
    The summary argument is retained for the build API and checked against the
    on-disk cohort summary when both contain the same scalar inventory fields.
    """
    output_dir = Path(output_dir).resolve()
    report_dir = output_dir / "report"
    if report_dir.resolve() == BASE_REPORT.resolve() or BASE_REPORT.resolve() in report_dir.resolve().parents:
        raise ValueError("Refusing to modify the frozen base report.")
    report_path = report_dir / "Final_Report.tex"
    if not report_path.exists():
        raise FileNotFoundError("Caller must copy the frozen report into output_dir/report first.")
    text = report_path.read_text(encoding="utf-8")
    if "% FINAL_REVIEW_NBA_START" in text:
        raise ValueError("Report already updated; recopy the frozen base before rebuilding.")
    data_dir = output_dir / "data"
    raw = pd.read_csv(data_dir / "epl_inverse_metrics.csv")
    identity = pd.read_csv(data_dir / "epl_identity_diagnostics.csv")
    cohort = json.loads((data_dir / "epl_cohort_summary.json").read_text(encoding="utf-8"))
    if isinstance(cohort, dict):
        for key in set(epl_summary) & set(cohort):
            if isinstance(epl_summary[key], (int, str, bool)) and isinstance(cohort[key], (int, str, bool)):
                if epl_summary[key] != cohort[key]:
                    raise ValueError(f"Summary mismatch on {key!r}")
    d = _normalise_epl(raw)
    complement, lay = _mode_masks(d)
    d = d[complement | lay].copy()
    complement, lay = _mode_masks(d)
    main = d[d["is_main"]].copy()
    if main["context_id"].nunique() != 47:
        raise ValueError(f"Expected 47 original fixed-stake main controls/cases, found {main['context_id'].nunique()}; check main-cohort field aliases.")
    tables_dir = report_dir / "tables"
    tables_dir.mkdir(exist_ok=True)
    nba_main, nba_appendix = _nba_material(Path(nba_dir), tables_dir)
    text = _insert_before(text, "\\clearpage\n\\section{Premier League results}", nba_main)

    # Main table: count every inverse, including failed and nonbankrupt controls.
    comparison_rows = []
    for bankrupt, label in [(True, "Bankrupt originals"), (False, "Nonbankrupt controls")]:
        group = d[d["is_main"] & d["bankrupt"].eq(bankrupt)]
        gm_comp, gm_lay = _mode_masks(group)
        for cost in sorted(group.loc[gm_comp, "cost"].unique()):
            z = group[gm_comp & (group["cost"] - cost).abs().lt(1e-8)]
            comparison_rows.append([label, "Priced complement", _pct(cost, 0), _num(len(z)), _num((z["final"] > z["initial"] + 1e-8).sum()), _num(z["final"].median()), _num(z["final"].min()), _num(z["final"].max())])
        z = group[gm_lay & group["cost"].abs().lt(1e-8)]
        if len(z):
            comparison_rows.append([label, "Synthetic lay", "0\\%", _num(len(z)), _num((z["final"] > z["initial"] + 1e-8).sum()), _num(z["final"].median()), _num(z["final"].min()), _num(z["final"].max())])
    (tables_dir / "epl_inverse_controls.tex").write_text(_fit_width(_short_table(
        ["Original cohort", "Opposite", "Cost", "N", "Profit", "Median end", "Min end", "Max end"], comparison_rows, "llrrrrrr")), encoding="utf-8")

    # Every zero price-context: best/reference repeats remain separate cases.
    zero = d[d["bankrupt"]].copy()
    zero_contexts = zero["context_id"].drop_duplicates().tolist()
    if len(zero_contexts) != 17 or len(identity) != 17:
        raise ValueError(f"Expected all 17 EPL zero contexts: funded={len(zero_contexts)}, identity={len(identity)}")
    zero_rows = []
    detail_rows = []
    identity_by_context = identity.set_index("context_id")
    for context in zero_contexts:
        z = zero[zero["context_id"] == context]
        row = z.iloc[0]
        zc, zl = _mode_masks(z)
        values = []
        for cost in [0, .02, .05]:
            v = z[zc & (z["cost"] - cost).abs().lt(1e-8)]
            if len(v) != 1:
                raise ValueError(f"Expected one complement row for {context}, cost={cost}")
            values.append(_num(v.iloc[0]["final"]))
        v = z[zl & z["cost"].abs().lt(1e-8)]
        if len(v) != 1:
            raise ValueError(f"Expected one synthetic lay row for {context}")
        gap = identity_by_context.loc[context, "minimum_additional_opening_cash"]
        zero_rows.append([_tex(row.strategy_id), _tex(row.odds), "Main" if row.is_main else "Ref. replay", *values, _num(v.iloc[0]["final"]), _num(gap)])
        for _, each in z.sort_values(["mode", "cost"]).iterrows():
            mode = "Lay" if "lay" in str(each["mode"]).lower() else "Complement"
            detail_rows.append([_tex(row.strategy_id), _tex(row.odds), mode, _pct(each["cost"], 0), _num(each.signals), _num(each.bets), _pct(each.hit), _pct(each.frequency), _num(each.expected_gain, 1), _num(each.expected_loss, 1), _pct(each.roi), _pct(each.drawdown)])
    (tables_dir / "epl_zero_contexts.tex").write_text(_long_table(
        ["ID", "Quotes", "Context", "Comp. 0\\%", "Comp. 2\\%", "Comp. 5\\%", "Lay 0\\%", "Mirror gap"], zero_rows, "lllrrrrr",
        "All 17 EPL zero-original price contexts; every funded inverse starts at 100,000. Original end capital is zero. The first four numeric columns are ending capital; cost haircuts positive fixture net profit. Mirror gap is additional opening cash needed to reserve the hypothetical exact-counterparty liability on at least one date; it is not the funded complement's cash requirement.", "tab:all_zero_contexts"), encoding="utf-8")
    (tables_dir / "epl_inverse_details.tex").write_text(_long_table(
        ["ID", "Quotes", "Mode", "Cost", "Signals", "Bets", "Hit", "Freq.", "Exp. gain", "Exp. loss", "Risk yield", "DD"], detail_rows, "llllrrrrrrrr",
        "Complete funded inverse statistics for the 17 zero contexts. Expected payoff components are model-implied monetary units per placed trade; frequency is placed trades divided by the 1,470 opportunities. DD is maximum date-close drawdown.", "tab:all_inverse_metrics"), encoding="utf-8")

    p009 = d[d["strategy_id"].eq("P009") & d["is_main"] & complement & d["cost"].abs().lt(1e-8)]
    if len(p009) != 1:
        raise ValueError("Need one main-cohort, zero-cost P009 priced-complement row.")
    p009 = p009.iloc[0]
    zbase = d[d["is_main"] & d["bankrupt"] & complement & d["cost"].abs().lt(1e-8)]
    cbase = d[d["is_main"] & ~d["bankrupt"] & complement & d["cost"].abs().lt(1e-8)]
    all_zero_complement = d[d["bankrupt"] & complement & d["cost"].abs().lt(1e-8)]
    all_zero_lay = d[d["bankrupt"] & lay & d["cost"].abs().lt(1e-8)]
    epl_main = r"""
% FINAL_REVIEW_EPL_START
\subsection{Opposite policies after bankruptcy: EPL diagnostic}
The 13 zero continuous main accounts comprise S041, S043 and 11 player
accounts. Four further zero reference-price replays of S033, S039, S041 and
S043 make 17 price contexts across 15 strategy IDs, not 17 independent
models. None of the 116 common-season accounts is zero. We also replay the
34 nonbankrupt main fixed-stake accounts as controls; the main comparison
therefore covers all 47 fixed-stake accounts, not only selected failures.

In a three-outcome market, ``opposite'' means covering both outcomes other
than the original pick, including the draw. With archived decimal odds
$O_k$, $A=\sum_{k\ne s}1/O_k$, and total risk request $B=1,000$, we allocate
$B/(O_kA)$ to each complementary outcome. This equalises gross payout at
$B/A$; it does not stake 1,000 on each leg. The synthetic odds $1/A$ can be
at or below one, so event occurrence and positive trading profit are not
identical. Expected gain/loss sum probability-weighted positive/negative
payoffs over all three outcomes, including these loss-making bundles.

We keep the frozen original signal and its entry filter, continue through
all 1,470 fixtures after original ruin, and do not impose a new value test
on the opposite outcome. Each account starts at 100,000; same-date risks
are proportionally scaled to opening cash before settlement, without
borrowing or reusing same-date proceeds. One thousand is 1\% of initial
capital, not a constant fraction of current cash.

\resulttable{Full-horizon EPL opposite policies from 100,000, main cohort
only. ``Profit'' counts ending balances above 100,000. Costs haircut each
fixture's positive net profit by 0\%, 2\% or 5\%; they are scenarios, not
observed venue commissions.}{tab:epl_inverse_controls}{epl_inverse_controls.tex}

"""
    epl_main += (
        f"At zero added cost, {_num((zbase['final'] > zbase['initial'] + 1e-8).sum())} of 13 bankrupt-original "
        f"complements finish above 100,000, compared with {_num((cbase['final'] > cbase['initial'] + 1e-8).sum())} "
        "of 34 nonbankrupt controls. These are descriptive, correlated outcomes, "
        "not an adjusted hypothesis test. P009's original account ends at zero; "
        f"its priced complement ends at {_num(p009['final'])}, makes {_num(p009.bets)} funded trades "
        f"from {_num(p009.signals)} frozen signals, and has {_pct(p009.drawdown)} maximum drawdown. "
        f"Its conditional stake-yield interval is [{_pct(p009.ci_low)}, {_pct(p009.ci_high)}]; "
        "these whole-date cashflow intervals omit refitting, resizing and the bankruptcy-based selection.\n\n"
    )
    epl_main += (
        "Across all 17 zero price contexts, the quoted complements profit in "
        f"{_num((all_zero_complement['final'] > all_zero_complement['initial'] + 1e-8).sum())}/17 cases, "
        f"with median ending capital {_num(all_zero_complement['final'].median())} "
        f"and range {_num(all_zero_complement['final'].min())}--{_num(all_zero_complement['final'].max())}. "
        "The synthetic same-back-price lay profits in "
        f"{_num((all_zero_lay['final'] > all_zero_lay['initial'] + 1e-8).sum())}/17 cases, "
        f"with median {_num(all_zero_lay['final'].median())}. The apparent improvement depends "
        "on a different, unobserved price contract; it cannot be attributed to changing only "
        "the direction of the bet. No zero-cost priced complement has a conditional 95\\% "
        "stake-yield interval entirely above zero.\n\n"
    )
    epl_main += r"""
A second calculation negates the \emph{recorded original cash flows}; every
100,000-to-zero history then maps to 200,000 by algebra. This truncated-path
identity is not the funded complement. A separate synthetic lay fixes
liability at 1,000 and uses counterstake $1,000/(O_s-1)$ at the original
back quote. It requires unavailable lay-price assumptions and is not an
exchange backtest. Both are labelled diagnostics. The actual complementary
bookmaker quotes lack verified simultaneous availability or accepted stakes.
Bankruptcy prompted these rules; no inverse is promoted as new confirmed
alpha or substituted for the original locked cash policy.
% FINAL_REVIEW_EPL_END
"""
    anchor = "Taken together, the two league studies support a cautious conclusion."
    text = _insert_before(text, anchor, epl_main)

    # Restore priority to verified evidence on the title page.
    cover_old = text[text.index("\\textbf{Main findings.}"):text.index("\\textbf{Evidence standard.}")]
    cover_new = r"""\textbf{Main findings.} In the locked EPL experiment neither branch selects
an admissible validation trading rule, so both primary test policies hold
cash. Its calibration branch's secondary flat-stake yield is $0.41\%$, with
an interval crossing zero. New EPL player models do not improve matched
team controls. The reproducible NBA logistic account returns $0.98\%$ with
flat stakes and $-35.00\%$ with eighth-Kelly; separately restarted annual
logistic accounts have negative average returns for both objectives. The
source-reported SVM returns $25.03\%$ flat but $-55.11\%$ with Kelly; its
refit does not reproduce. Bankrupt-policy reversals are reported separately
as post-hoc sensitivity tests, not confirmed profitable policies.

"""
    text = _replace_once(text, cover_old, cover_new)

    # Add the proposal's operationally qualified arbitrage answer.
    arb = pd.read_parquet(ROOT / "epl_modeling/results/bookmaker_odds_panel.parquet")
    a = arb[arb["season"].isin(["2022-23", "2023-24", "2024-25", "2025-26"])]
    a25 = arb[arb["season"].eq("2025-26")]
    arb_text = (
        "The frozen four-season panel flags " + _num(a.mathematical_arb_candidate.sum())
        + "/" + _num(len(a)) + " mathematical arbitrage candidates ("
        + _pct(a.mathematical_arb_candidate.mean(), 4) + "), with maximum theoretical margin "
        + _pct(a.arb_theoretical_margin.max(), 4) + ". Verified executable cases total "
        + _num(a.executable_arbitrage_verified.sum()) + "; all " + _num(a.selected_quote_timestamps_missing.sum())
        + " selected quote sets lack simultaneous clocks. The common 2025/26 panel has "
        + _num(a25.mathematical_arb_candidate.sum()) + "/" + _num(len(a25))
        + " candidates. These counts answer the arbitrage component without treating flags as earned profit.\n\n"
    )
    text = _insert_before(text, "The saved operational evidence has a separate October 20 cutoff:", arb_text)

    # Calibration on the selected betting subset is different from global ECE.
    lr = pd.read_csv(ROOT / "final_deliverables/nba_core_replay/metrics_all4.csv")
    lr = lr[(lr["model"] == "LR") & (lr["staking"] == "fixed")].iloc[0]
    selected_p = 1 - lr.expected_loss_per_trade / 100
    mismatch = (
        "For the same reconciled flat LR account, mean selected-outcome probability is "
        + _pct(selected_p, 4) + " versus observed hit rate " + _pct(lr.hit_ratio, 4)
        + " (a " + _num(100 * (selected_p - lr.hit_ratio), 4)
        + " percentage-point gap), despite ordinary global ECE " + _pct(lr.ordinary_binary_ece_20, 4)
        + ". Model-implied net payoff is " + _num(lr.expected_net_per_trade, 3)
        + " units/trade; realised net is " + _num(lr.profit / lr.n_bets, 3)
        + ". A small aggregate calibration error need not transfer to the price-selected bet subset.\n\n"
    )
    text = _insert_before(text, "\\resulttable{Additional metrics supported by the cent-matched NBA logistic", mismatch)

    old_closing = text[text.index(anchor):text.index("\\clearpage\n\\begin{thebibliography}")]
    closing = r"""\subsection{Final qualitative and quantitative assessment}
The shared question is answered by the matched comparisons, not by the
largest ex-post account. The original NBA flat capital return favours
accuracy selection by 24.05 percentage points (with the SVM reproduction
limit); eighth-Kelly favours calibration by 20.11 points while both lose.
Across nine annual LR windows calibration wins only three times, with mean
returns of $-17.34\%$ versus $-9.49\%$. EPL primary policies both hold cash;
the secondary flat calibration yield exceeds accuracy by 2.66 points, but
its interval includes zero. Better observed ECE therefore does not establish
a durable advantage in betting returns. Binary/three-outcome scores,
capital returns/stake yields and annual/continuous accounts are not pooled.

The EPL raw market remains the strongest pooled proper-score benchmark,
and all six added player variants lose to their matched team controls on
log loss. Of 88 continuous exploratory accounts, 24 profit and 64 lose,
including 13 bankrupt; the best account's conditional interval includes
zero. For the original 84-strategy family only, the saved global bootstrap
p-values range from 0.3887--0.4187 versus cash and 0.1457--0.1952 versus
the market-favourite baseline across block lengths 1, 3, 5 and 10. These
conditional recorded-cashflow tests do not adjust the newer player or
inverse families, and no family supplies established profitable alpha.

The strongest contributions are the implemented cross-league comparison,
shifted feature construction, explicit funding, market benchmarks and
auditable negative findings. The remaining limits are narrow outcome and
season samples, the current-club EPL cohort, approximate/inconsistent
source environments, unavailable quote clocks, and post-hoc strategy
expansion. Calibration describes probability reliability; betting also
depends on prices, the selected subset, costs and exposure. Opposite-policy
successes, where observed, test the direction of failed signals and are
exploratory. A decisive extension would precommit the model, entry rule,
stake budget and evaluation horizon before collecting a fresh cohort of
timestamped available quotes. The study supports this discipline rather
than a claim of implementable statistical arbitrage.

"""
    text = _replace_once(text, old_closing, closing)

    appendix = r"""
% FINAL_REVIEW_APPENDIX_START
\clearpage
\section{Bankrupt-policy opposite audit}
The 17 EPL contexts below include the 13 main zero accounts and four
additional reference-price policy replays. Repeated IDs with different
prices are different contexts. The two NBA zero annual accounts are shown
separately: the audit therefore covers 19 zero-account cases across the
leagues, without treating them as independent tests. Exact recorded-profit
negation always gives 200,000 for EPL (20,000 for NBA) by arithmetic; this
is not an attainable-return estimate or a funded trade ledger.

{\footnotesize\setlength{\tabcolsep}{3pt}
\input{tables/epl_zero_contexts.tex}}

\subsection{Risk and payoff rules}
All EPL inverses use the original frozen qualification over the full
1,470-fixture horizon. Complement requests split a total 1,000 between the
two alternative outcomes in reciprocal-odds proportions. Synthetic lay
requests reserve total liability 1,000 and compute the counterstake from
the back quote; they do not assume observed exchange liquidity. Risks are
scaled together to date-start cash. Cost sensitivity applies to a fixture's
positive \emph{net bundle profit}, with no rebate on losses, and cash sizes
are replayed for each scenario. Thus the additional haircut does not double
count a winning leg while ignoring its losing complementary leg. Bookmaker
vig is already embedded in the archived odds.

Hit rate reports occurrence of the complementary event. A bundle can still
lose if its synthetic odds do not exceed one; the CSV also preserves the
fraction of bundles earning positive net profit. Expected components use
the original forecast probabilities and signed outcome payoffs, not the
empirical frequency of wins. The original model need not endorse its
contrarian trade. Full CSVs additionally contain turnover, realised payoff
components, funding checks and source/context identifiers.

{\scriptsize\setlength{\tabcolsep}{2pt}
\input{tables/epl_inverse_details.tex}}
\sourcefile{data/epl_inverse_metrics.csv; data/epl_identity_diagnostics.csv; data/epl_cohort_summary.json}
""" + nba_appendix + "\n% FINAL_REVIEW_APPENDIX_END\n"
    mirror_feasible = int(_truth(identity["mirror_funding_feasible"]).sum())
    funding_note = (
        f" On the recorded truncated paths, {mirror_feasible}/17 EPL mirrors pass the "
        "hypothetical same-date liability-reserve check; the maximum additional "
        f"opening-cash requirement is {_num(identity.minimum_additional_opening_cash.max())}. "
        "Thus extra funding is not the observed obstruction for these exact recorded "
        "mirrors. The absent opposing contract and its unobserved price remain the "
        "obstructions to claiming an executable mirror; funding feasibility alone "
        "does not establish availability."
    )
    appendix = _replace_once(
        appendix,
        "is not an attainable-return estimate or a funded trade ledger.",
        "is not an attainable-return estimate or a funded trade ledger." + funding_note,
    )
    text = _insert_before(text, "\\end{document}", appendix)
    report_path.write_text(text, encoding="utf-8")

