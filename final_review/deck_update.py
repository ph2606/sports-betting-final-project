"""Add the funded opposite-policy study to the existing concise joint deck.

The original slide specifications are copied, so this extension cannot mutate
the archived presentation. All new numerical results come from saved ledgers.
"""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import numpy as np
import pandas as pd

from epl_presentation.build import NAVY, TEAL, MUTED, RED, text, table, slide, pct


ROOT = Path(__file__).resolve().parents[1]
EPL_DIR = Path(__file__).with_name("epl_results")


def _money(value: float, decimals: int = 0) -> str:
    return f"{float(value):,.{decimals}f}"


def _image(path: Path, x: float, y: float, w: float, h: float) -> dict:
    path = Path(path).resolve()
    if not path.is_file():
        raise FileNotFoundError(path)
    return dict(type="image", x=x, y=y, w=w, h=h, path=str(path))


def _nba_slide(nba_dir: Path) -> dict:
    nba_dir = Path(nba_dir).resolve()
    metrics = pd.read_csv(nba_dir / "inverse_metrics.csv")
    full = metrics.loc[metrics["mode"].eq("opposite_full_horizon")].set_index("branch")
    prefix = metrics.loc[metrics["mode"].eq("opposite_recorded_prefix")].set_index("branch")
    if len(full) != 2 or set(full.index) != {"cal", "acc"}:
        raise ValueError("Expected the two audited 2017/18 NBA opposite accounts")
    audit = json.loads((nba_dir / "audit_summary.json").read_text(encoding="utf-8"))
    if audit["status"] != "passed" or audit["exact_zero_accounts"] != 2:
        raise ValueError("NBA opposite accounts require a passed zero-account audit")
    rows = []
    for key, label in (("cal", "Calibration LR"), ("acc", "Accuracy LR")):
        r = full.loc[key]
        rows.append([label, "0 → " + _money(r.final_capital, 2), pct(r.hit_ratio),
            pct(r.trading_frequency), _money(r.expected_gain_per_trade, 2) + " / " + _money(r.expected_loss_per_trade, 2),
            pct(r.roi_on_stakes), pct(r.max_drawdown)])
    intervals = pd.read_csv(nba_dir / "conditional_uncertainty.csv")
    roi = intervals.loc[intervals.metric.eq("roi_on_stakes")].set_index("branch")
    interval_note = "; ".join(
        f"{label}: [{pct(roi.loc[key, 'ci_lower'])}, {pct(roi.loc[key, 'ci_upper'])}]"
        for key, label in (("cal", "calibration"), ("acc", "accuracy")))
    return slide("NBA: what happens if we back the other team?",
        "2017/18: both original fixed-stake accounts ended at zero. Both annual models are logistic regressions.",
        [table(.65, 2.08, 14.67, 2.15,
            ["Original branch", "Original → opposite", "Hit ratio", "Trade frequency", "Expected gain / loss", "Stake ROI", "Max drawdown"],
            rows, [.19, .19, .11, .13, .16, .11, .11], 18, 13),
         text(.65, 4.65, 14.6, 1.1,
            "Keep the original entry signal; bet on the other team at its own recorded odds.\nStart with 10,000; request 100 per bet (1% of initial cash), capped by available cash.\nContinue through all 1,075 games, including games after the original account ran out of money.", 21),
         text(.65, 6.12, 14.6, .85,
            "One full-season inverse profits and one loses. Reversing only the original funded trades loses in both cases: "
            + _money(prefix.loc["cal", "final_capital"]) + " and " + _money(prefix.loc["acc", "final_capital"]) + ".", 21, TEAL, True),
         text(.65, 7.37, 14.6, .72,
            "Post-hoc source-method reconstruction. Both conditional 95% ROI intervals include zero; this is not a confirmed edge.\nExpected gain/loss use the original model's probabilities; actual quoted opposite returns are not minus the original profit.", 16, MUTED)],
        kicker="NBA RESULTS | OPPOSITE-POLICY SENSITIVITY",
        sources=[nba_dir / "inverse_metrics.csv", nba_dir / "audit_summary.json", nba_dir / "conditional_uncertainty.csv"],
        notes=("Complete zero inventory: 36 annual accounts across nine seasons, two LR feature-selection branches and fixed/eighth-Kelly sizing. "
            "Only the two 2017/18 fixed accounts have zero terminal capital. All 18 saved annual fixed returns and feature counts reconcile. "
            "Annual event probabilities were reconstructed using the unchanged source algorithm; the notebook did not preserve saved annual fitted weights or event-level probabilities. "
            "This is source-method reconstruction, not proof of byte-identical original predictions. The core unreconciled SVM refit is not used. "
            "The original home-first value eligibility and exact probability filter are retained. At most one bet per game; source game-sequential settlement, no borrowing. "
            "The full inverse has " + str(int(full.loc["cal", "n_bets"])) + " calibration bets and " + str(int(full.loc["acc", "n_bets"])) + " accuracy bets. "
            "Full-season capital returns are " + pct(full.loc["cal", "return_on_initial_capital"]) + " and " + pct(full.loc["acc", "return_on_initial_capital"]) + ". "
            "Matched recorded-prefix results retain the original positive-stake fixtures and stakes; both lose. "
            "The 9,999 whole-match-date percentile bootstrap fixes selected models, signals and stakes: " + interval_note + ". "
            "It does not adjust for fitting, strategy search or selecting failures after seeing outcomes. Quotes and execution timestamps remain unverified. "
            "Financial hit ratio counts positive-profit bets; expected components are model-implied, not realised average win/loss. "
            "The inverse does not receive a new positive-edge gate under the original forecast."))


def _synthesis_slide(epl_positive: int) -> dict:
    rows = [
        ["Calibration versus accuracy", "NBA calibration wins 3/9 annual comparisons.\nEPL locked primary policies both hold cash.", "No stable, established profit advantage."],
        ["Predictive benchmark", "EPL log loss: raw market 0.9662;\nbest learned model 0.9693 (lower is better).", "Prices remain a strong benchmark."],
        ["Extra player data", "All 6 tested new player-feature variants have\nworse loss than their matched team controls.", "These richer features did not improve forecasts."],
        ["Arbitrage and reversals", f"4/1,470 mathematical arbitrage flags; 0 verified fills.\nOpposite accounts profit: NBA 1/2; EPL {epl_positive}/17.", "Neither result establishes an executable future edge."],
    ]
    return slide("What the completed project supports",
        "Calibration, quoted prices and capital risk must be evaluated together. Historical profit alone is not enough.",
        [table(.65, 2.08, 14.67, 3.95, ["Question", "Verified evidence", "Interpretation"],
            rows, [.23, .45, .32], 18, 15),
         text(.65, 6.42, 14.6, .65,
            "Limitations: exploratory reuse of outcomes, uncertain quote availability and one unreproduced NBA SVM result.", 21, MUTED),
         text(.65, 7.35, 14.6, .72,
            "Next test: freeze the model, rules and risk budget; record available quotes before future games; then evaluate both forecasts and funded returns.", 21, TEAL, True)],
        kicker="WHOLE-PROJECT REVIEW | EVIDENCE AND LIMITATIONS",
        sources=["final_review/project_review.md", "final_review/review_checks.json", "final_deliverables/epl_evidence.json", "final_review/epl_results/metrics.csv"],
        notes=("This answers the September 30 project proposal using completed work, not the initial ambition. "
            "NBA annual mean capital returns are -17.34% (calibration-selected LR features) and -9.49% (accuracy-selected LR features), with independent annual resets. "
            "The core 2018/19 SVM results remain explicitly source-reported and unreproduced. EPL primary validation found no admissible threshold with at least 30 bets and positive validation stake ROI, so both test policies hold cash. "
            "The predeclared EPL secondary calibration branch has +0.4114% stake ROI versus -2.2453% for accuracy; both conditional intervals include zero. "
            "Six new player-feature/model combinations have worse pooled log loss than their matched same-family team controls; this does not rule out every possible use of player information. "
            "The four arbitrage flags use archived best quotes; no simultaneous accepted fills or complete quote clocks are verified. "
            "Opposite-policy counts refer to the two NBA full-season cases and 17 EPL previously bankrupt strategy/price contexts at zero hypothetical cost, not 17 independent newly fitted models. "
            "Selection by observed bankruptcy is retrospective. Existing multiple-comparison adjustments do not cover the new inverses. "
            "A grade cannot be guaranteed; clarity, correct financial accounting and reproducibility support the academic argument."))


def _read_epl(epl_summary: dict) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    metrics = pd.read_csv(EPL_DIR / "metrics.csv")
    identity = pd.read_csv(EPL_DIR / "identity_diagnostics.csv")
    zero = metrics.original_zero.astype(str).str.lower().eq("true")
    primary = metrics.loc[zero & metrics.variant.eq("dutch_cost_0")].copy()
    if len(primary) != 17 or primary.context_id.nunique() != 17:
        raise ValueError("Expected all 17 bankrupt EPL strategy/price contexts")
    if primary.strategy_id.nunique() != 15:
        raise ValueError("The 17 EPL contexts should represent 15 distinct strategy IDs")
    if set(identity.context_id) != set(primary.context_id) or len(identity) != 17:
        raise ValueError("EPL identity diagnostics do not cover every zero context")
    for variant in ("original", "dutch_cost_2", "dutch_cost_5", "lay_hypothetical", "dutch_recorded_prefix"):
        part = metrics.loc[zero & metrics.variant.eq(variant)]
        if len(part) != 17 or set(part.context_id) != set(primary.context_id):
            raise ValueError(f"Incomplete bankrupt-context results: {variant}")
    original = metrics.loc[zero & metrics.variant.eq("original")]
    if not np.allclose(original.final_capital, 0, atol=1e-7):
        raise ValueError("An account labelled bankrupt has nonzero original terminal cash")
    if int(epl_summary["original_zero_contexts"]) != 17 or int(epl_summary["contexts"]) != 51:
        raise ValueError("EPL slide inventory differs from the completed study summary")
    summary = {}
    for variant in ("dutch_cost_0", "dutch_cost_2", "dutch_cost_5", "lay_hypothetical"):
        part = metrics.loc[zero & metrics.variant.eq(variant)]
        summary[variant] = {
            "profitable": int(part.final_capital.gt(100000 + 1e-7).sum()),
            "median": float(part.final_capital.median()),
            "minimum": float(part.final_capital.min()),
            "maximum": float(part.final_capital.max()),
        }
    controls = metrics.loc[~zero & metrics.variant.eq("dutch_cost_0")]
    if len(controls) != 34:
        raise ValueError("Expected the 34 nonbankrupt EPL fixed-stake controls")
    summary["controls_profitable"] = int(controls.final_capital.gt(100000 + 1e-7).sum())
    summary["ci_include_zero"] = int((primary.roi_ci_low.le(0) & primary.roi_ci_high.ge(0)).sum())
    profitable = primary.loc[primary.final_capital.gt(100000 + 1e-7)]
    summary["profitable_ci_include_zero"] = int((profitable.roi_ci_low.le(0) & profitable.roi_ci_high.ge(0)).sum())
    if not np.isfinite(primary[["roi_ci_low", "roi_ci_high"]].to_numpy()).all():
        raise ValueError("All 17 primary inverse results need their conditional intervals")
    summary["mirror_funding_failures"] = int((~identity.mirror_funding_feasible.astype(str).str.lower().eq("true")).sum())
    return metrics, identity, summary


def _epl_slide(figures: Path, results: dict) -> dict:
    primary = results["dutch_cost_0"]
    return slide("EPL: back both other outcomes after a zero account",
        "17 bankrupt strategy/price contexts, covering 15 strategy IDs. Each inverse starts a new 100,000 account.",
        [_image(figures / "epl_inverse_capital.png", .65, 2.08, 9.25, 4.55),
         text(10.2, 2.14, 5.1, .35, "FULL-HORIZON PRICED COMPLEMENT", 14, TEAL, True),
         text(10.2, 2.72, 5.1, .6, f"{primary['profitable']} / 17 profit at 0% cost", 26, TEAL, True),
         text(10.2, 3.58, 5.1, .9,
            "Median ending cash: " + _money(primary["median"]) + "\nRange: " + _money(primary["minimum"]) + "–" + _money(primary["maximum"]), 20),
         text(10.2, 4.69, 5.1, .78,
            f"Profitable after 2% / 5% cost:\n{results['dutch_cost_2']['profitable']} / 17 and {results['dutch_cost_5']['profitable']} / 17", 20),
         text(10.2, 5.68, 5.1, 1.0,
            f"Controls: {results['controls_profitable']} / 34 profit.\nProfitable cases with 95% ROI intervals\nincluding zero: {results['profitable_ci_include_zero']} / {primary['profitable']}.", 18, MUTED),
         text(.65, 6.94, 14.6, .8,
            "Keep the original signal. Split 1,000 total risk (1% of initial cash) across the other two results for equal payouts.\nFund all same-date bundles from opening cash; continue after the original account's bankruptcy.", 19),
         text(.65, 7.92, 14.6, .28,
            f"Hypothetical lays profit in {results['lay_hypothetical']['profitable']}/17 cases but assume unobserved lay quotes. This post-hoc study does not verify executable returns.", 14, MUTED)],
        kicker="PREMIER LEAGUE RESULTS | OPPOSITE-POLICY SENSITIVITY",
        sources=[EPL_DIR / "metrics.csv", EPL_DIR / "summary.json", "final_review/inverse_protocol.md"],
        notes=("Football has three outcomes. The opposite of home is draw OR away, rather than away alone. "
            "For original pick k and other outcomes j, let S=sum(1/O_j). With requested total bundle risk R=1,000, each leg stake is R(1/O_j)/S. "
            "Either other result returns R/S gross. The original pick produces loss R; the complementary event produces net R(1/S-1). "
            "When S is at least one, even the complementary event can have nonpositive profit, so event hit and profitable-bundle hit are separate fields. "
            "The original full-horizon signal is retained; no new positive-edge requirement is imposed on the inverse. "
            "All 1,470 opportunities in 2022/23–2025/26 remain eligible for signal reconstruction, including dates after the original account stops. "
            "Uniform same-date scaling reserves total bundle risk from opening cash and any original date cap; no borrowing or reuse of same-date wins. "
            "Thirteen contexts are in the principal comparison, plus four bankrupt Bet365 reference-price policy replays. S041 and S043 occur at both price modes. "
            "Best quotes and Bet365 are retained per context. No unobserved double-chance quote or exchange lay quote is invented for the priced-complement results. "
            "Three costs (0%, 2%, 5%) are applied to positive NET portfolio profit per fixture, not gross payout or per-leg wins; these are illustrative haircuts. "
            "The full study includes 51 contexts, 153 funded priced complements, 51 hypothetical risk-matched lays, 17 prefix complements and 17 recorded-exposure identity diagnostics. "
            "The 34 controls are the other original fixed-stake accounts, not an untouched holdout. "
            "Intervals resample whole match dates within season while holding realised funded cashflows fixed; no re-fitting, re-sizing or strategy-search adjustment. "
            + str(results["ci_include_zero"]) + " of 17 primary intervals include zero, including " + str(results["profitable_ci_include_zero"]) + " of " + str(primary["profitable"]) + " profitable accounts. "
            "Observed bankruptcy selected the cohort after outcomes; positive returns are unconfirmed hypotheses. "
            "The arithmetic mirror of original recorded loss is only an identity, with " + str(results["mirror_funding_failures"]) + " contexts requiring extra opening collateral for the exact recorded exposures. "
            "Archived quotes have unverified simultaneous availability and execution."))


def _epl_appendix(metrics: pd.DataFrame, identity: pd.DataFrame) -> list[dict]:
    zero = metrics.original_zero.astype(str).str.lower().eq("true")
    primary = metrics.loc[zero & metrics.variant.eq("dutch_cost_0")].copy()
    primary["_sort"] = primary.strategy_id.str.extract(r"(\d+)")[0].astype(int)
    # Existing S policies precede the later P feature study; keep price contexts adjacent.
    primary["_group"] = primary.strategy_id.str.startswith("P").astype(int)
    primary = primary.sort_values(["_group", "_sort", "price_mode"])
    by_variant = metrics.loc[zero].set_index(["variant", "context_id"])
    identities = identity.set_index("context_id")
    slides = []
    for page, start in enumerate((0, 9), 1):
        part = primary.iloc[start:start + 9]
        rows, details = [], []
        for r in part.itertuples():
            fee2 = by_variant.loc[("dutch_cost_2", r.context_id)]
            fee5 = by_variant.loc[("dutch_cost_5", r.context_id)]
            lay = by_variant.loc[("lay_hypothetical", r.context_id)]
            ident = identities.loc[r.context_id]
            rows.append([r.strategy_id + " / " + ("Best" if r.price_mode == "best" else "Bet365"),
                _money(r.final_capital), pct(r.roi), pct(r.positive_profit_hit_ratio),
                f"{int(r.bet_count)}/{int(r.qualifying_signals)}; {pct(r.trading_frequency)}",
                _money(r.expected_gain_per_trade, 1) + " / " + _money(r.expected_loss_per_trade, 1),
                pct(r.max_drawdown), _money(fee2.final_capital) + " / " + _money(fee5.final_capital),
                _money(lay.final_capital)])
            details.append({"context": r.context_id, "model": r.model_label, "entry_rule": r.selection_rule,
                "primary": {k: v for k, v in r._asdict().items() if not k.startswith("_")},
                "cost_2_final": float(fee2.final_capital), "cost_5_final": float(fee5.final_capital),
                "synthetic_lay_final": float(lay.final_capital), "identity_diagnostic": ident.to_dict()})
        slides.append(slide(f"EPL appendix: every bankrupt-policy inverse ({page}/2)",
            "Original ending cash is zero in every row. Main results are funded full-horizon complements with no cost, 2022/23–2025/26.",
            [table(.65, 2.08, 14.67, 5.45,
                ["Strategy / quotes", "Ending cash", "Stake ROI", "Profit hit", "Bets / signals; frequency", "Expected gain / loss", "Max drawdown", "Ending: 2% / 5% cost", "Synthetic lay ending"],
                rows, [.13, .10, .07, .07, .13, .13, .08, .15, .14], 13, 11.5),
             text(.65, 7.67, 14.6, .50,
                "Risk 1,000 TOTAL across two outcomes; start 100,000. Same-date requests share opening cash and can be scaled.\n"
                "Hit = positive bundle profit; expected gain/loss are model claims. Synthetic lay assumes unobserved lay quotes.", 14.5, MUTED)],
            appendix=True, kicker="EPL APPENDIX | ALL ZERO-CONTEXT INVERSES",
            sources=[EPL_DIR / "metrics.csv", EPL_DIR / "identity_diagnostics.csv", "final_review/inverse_protocol.md"],
            notes=("Each original strategy is explained in the preceding catalogue. Its original qualification is retained on the entire 1,470-fixture horizon, including after bankruptcy. "
                "Context is strategy ID plus quote mode; the 17 contexts cover 15 distinct IDs. Best denotes archived highest individual-book quotes; Bet365 denotes a reference-policy replay with its own original selection under those prices. "
                "Complement rule: back both other outcomes, splitting total risk R=1,000 by reciprocal quote weights so both gross payouts are R/S, S=sum(1/O_other). "
                "Retain any original date cap. All same-date commitments share opening cash; scale uniformly and never borrow or reuse same-date wins. A zero inverse remains zero. "
                "Frequency denominator is 1,470 opportunities. Bets are funded fixture bundles; there are two back legs per bundle. Signals include unfunded qualifying fixtures. "
                "Stake ROI is profit divided by allocated bundle stakes. Expected gain and loss are nonnegative probability-weighted components under the original model, not realised average wins and losses. "
                "Price-supported costs haircut positive net bundle profit at 2% and 5%, without rebating negative profit. Synthetic lay uses fixed maximum liability 1,000, counterstake 1,000/(original odds-1), at the original back price; real lay quotes and fills are not supplied. "
                "The recorded-exposure mirror is the negative of existing realised cashflow. Its arithmetic endpoint is an identity, not a newly earned strategy result; exact liability may require extra opening cash. "
                "Every full metric, conditional ROI interval and identity funding diagnostic for these rows follows:\n" + json.dumps(details, ensure_ascii=False, indent=2, default=str))))
    return slides


def update_slides(base_slides: list, figures: Path, epl_summary: dict, nba_dir: Path) -> list:
    """Return 15 main slides and 13 appendix slides from the original 23 specs."""
    slides = deepcopy(base_slides)
    if len(slides) != 23 or sum(not s.get("appendix", False) for s in slides) != 12:
        raise ValueError("Expected the archived concise joint deck: 12 main + 11 appendix")
    metrics, identity, results = _read_epl(epl_summary)
    annual = [i for i, s in enumerate(slides) if s["title"] == "NBA: nine-season annual robustness"]
    player = [i for i, s in enumerate(slides) if s["title"].startswith("EPL: player model:")]
    if len(annual) != 1 or len(player) != 1:
        raise ValueError("Could not locate the original NBA annual and EPL player slides")
    slides.insert(annual[0] + 1, _nba_slide(nba_dir))
    # Search again after the NBA insertion so the original index cannot drift.
    player = next(i for i, s in enumerate(slides) if s["title"].startswith("EPL: player model:"))
    slides.insert(player + 1, _epl_slide(Path(figures).resolve(), results))
    first_appendix = next(i for i, s in enumerate(slides) if s.get("appendix", False))
    slides.insert(first_appendix, _synthesis_slide(results["dutch_cost_0"]["profitable"]))
    slides.extend(_epl_appendix(metrics, identity))
    if len(slides) != 28 or sum(not s.get("appendix", False) for s in slides) != 15:
        raise AssertionError("Updated joint deck must contain 15 main + 13 appendix slides")
    return slides
