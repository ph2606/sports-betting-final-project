"""Build the reviewed joint submission without altering earlier canonical runs."""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import zipfile

import fitz
import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import pandas as pd
from pptx import Presentation

from final_deliverables.build import compile_report, jsave, sha, read_data
from final_deliverables.audit import audit_source_evidence, audit_tables, norm

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = Path(__file__).parent
BASE = ROOT / "final_deliverables/results/20261023_joint_final"
OUTPUT = PACKAGE / "results/20261023_reverse_review"


def make_plots(figures):
    equity = pd.read_parquet(PACKAGE / "epl_results/equity.parquet")
    inventory = pd.read_csv(PACKAGE / "epl_results/inventory.csv")
    zero_ids = inventory.loc[inventory.original_zero, "context_id"].tolist()
    data = equity.loc[equity.context_id.isin(zero_ids) & equity.variant.eq("dutch_cost_0")]
    colors = plt.get_cmap("tab20")
    fig, ax = plt.subplots(figsize=(13.8, 5.8))
    for i, context in enumerate(zero_ids):
        part = data.loc[data.context_id.eq(context)].sort_values("match_date")
        dates = [part.match_date.iloc[0] - pd.Timedelta(days=1), *part.match_date]
        values = [100000., *part.end_capital]
        ax.step(dates, values, where="post", label=context.replace("__", " / "),
                color=colors(i), linestyle="--" if context.endswith("reference") else "-", linewidth=1.3)
    ax.axhline(100000, color="#758797", linewidth=.8, linestyle=":")
    ax.set_ylabel("Funded account capital (monetary units)")
    ax.set_xlabel("Match date; one continuous account, no annual resets")
    ax.yaxis.set_major_formatter(FuncFormatter(lambda n, _: f"{n/1000:g}K"))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=8))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax.set_ylim(bottom=0); ax.grid(axis="y", alpha=.18)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(loc="upper center", bbox_to_anchor=(.5, -.21), ncol=6, fontsize=8, frameon=False)
    fig.subplots_adjust(left=.08, right=.99, top=.98, bottom=.31)
    for extension in ("png", "pdf", "svg"):
        fig.savefig(figures / ("epl_inverse_capital." + extension), dpi=190)
    plt.close(fig)
    return {"epl_inverse_capital": {"contexts": zero_ids, "lines": len(zero_ids),
            "dated_closes": len(data), "initial_capital_each": 100000., "variant": "dutch_cost_0"}}


def audit_output(output, slides, rendering):
    data = read_data()
    checked = audit_source_evidence(data["nba"], data["epl"])
    checked["unchanged_original_numerical_tables"] = audit_tables(
        json.loads((BASE / "data/display_tables.json").read_text(encoding="utf-8")), data["nba"], data["epl"])
    assert rendering["native_layout"]["text_overflow_count"] == 0, rendering["native_layout"]["text_overflows"]
    assert not rendering["geometry"]["geometry_violations"]
    prs = Presentation(output / "presentation/Final_Project_Presentation.pptx")
    with fitz.open(output / "presentation/Final_Project_Presentation.pdf") as pdf:
        assert len(pdf) == len(slides) == len(prs.slides)
        slide_text = [norm(p.get_text()) for p in pdf]
    with fitz.open(output / "report/Final_Report.pdf") as pdf:
        report_text = norm(" ".join(p.get_text() for p in pdf))
        report_pages = len(pdf)
        for name in ("Aman Dhillon", "Panagiotis Housos", "Daniel Totouom-Tangho"):
            assert norm(name) in norm(pdf[0].get_text()), name
            assert norm(name) in slide_text[0], name
    report_source = (output / "report/Final_Report.tex").read_text(encoding="utf-8")
    assert report_source.index(r"\input{methodology.tex}") < report_source.index(r"\section{NBA") < report_source.index(r"\section{Premier League")
    assert len(slides) == 28 and sum(not s.get("appendix", False) for s in slides) == 15
    assert report_pages >= 22
    for value in ("11,148", "8,785"):
        assert value in report_text and any(value in s for s in slide_text), value
    metrics = pd.read_csv(PACKAGE / "epl_results/metrics.csv")
    inv = metrics.loc[metrics.variant.eq("dutch_cost_0") & metrics.original_zero]
    for context in inv.context_id:
        assert context.split("__")[0] in report_text
    log = (output / "report/Final_Report.log").read_text(encoding="utf-8", errors="replace")
    forbidden = [s for s in log.splitlines() if "Overfull" in s or "undefined" in s.lower() or "Missing character" in s]
    assert not forbidden, forbidden
    nba = json.loads((PACKAGE / "nba_results/audit_summary.json").read_text(encoding="utf-8"))
    epl = json.loads((PACKAGE / "epl_results/independent_audit.json").read_text(encoding="utf-8"))
    checked.update({"report_pages": report_pages, "presentation_slides": len(slides), "main_slides": 15,
                    "native_text_overflows": 0, "latex_unresolved_or_overfull_warnings": forbidden,
                    "nba_inverse_audit": nba, "epl_inverse_audit": epl,
                    "names_on_first_page": True, "requested_section_order": True})
    return checked


def publish(output):
    stable = ROOT / "deliverables/final"
    old = json.loads((stable / "manifest.json").read_text(encoding="utf-8"))
    changed = [name for name, meta in old["copies"].items() if not (stable / name).is_file() or sha(stable / name) != meta["sha256"]]
    if changed:
        raise RuntimeError("Generated submission files were edited; preserve them and publish to a new folder: " + str(changed))
    copies = {}
    inputs = [(output / "report" / n, Path(n)) for n in ("Final_Report.tex", "methodology.tex", "numbers.tex", "Final_Report.pdf")]
    inputs += [(p, p.relative_to(output / "report")) for folder in ("figures", "tables") for p in (output / "report" / folder).rglob("*") if p.is_file()]
    inputs += [(output / "presentation" / n, Path(n)) for n in ("Final_Project_Presentation.pptx", "Final_Project_Presentation.pdf", "Final_Presentation_Notes.md")]
    inputs += [(output / "Final_Report_LaTeX.zip", Path("Final_Report_LaTeX.zip"))]
    for source, relative in inputs:
        target = stable / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        copies[relative.as_posix()] = {"source": source.relative_to(ROOT).as_posix(), "sha256": sha(target)}
    (stable / "README.txt").write_text("Reviewed final report and presentation. Authors: Aman Dhillon and Panagiotis Housos. Supervisor: Daniel Totouom-Tangho. Common methodology, NBA, then Premier League. Includes funded opposite-strategy study and final project review. Compile the complete LaTeX source with XeLaTeX three times. See final_review/README.md for reproduction and limitations.\n", encoding="utf-8")
    jsave(stable / "manifest.json", {"canonical_run": output.relative_to(ROOT).as_posix(), "copies": copies,
        "author_names": ["Aman Dhillon", "Panagiotis Housos"], "supervisor": "Daniel Totouom-Tangho"})


def build():
    protected = [ROOT / "epl_data/EPL_data_overview.xlsx", ROOT / "presentations/latest/EPL_Project_Presentation.pptx",
                 ROOT / "presentations/latest/EPL_Project_Presentation_Draft.pptx"]
    protected_hashes = {p: sha(p) for p in protected if p.is_file()}
    base_manifest = json.loads((BASE / "manifest.json").read_text(encoding="utf-8"))
    for relative, expected in base_manifest["source_sha256"].items():
        assert sha(ROOT / relative) == expected, relative
    OUTPUT.mkdir(parents=True, exist_ok=True)
    if not (OUTPUT / "report").exists():
        shutil.copytree(BASE / "report", OUTPUT / "report")
    else:
        # Retry only our unpublished build, never an archived completed run.
        if (OUTPUT / "manifest.json").exists():
            raise RuntimeError("Completed runs are immutable; choose a new versioned output.")
        shutil.copyfile(BASE / "report/Final_Report.tex", OUTPUT / "report/Final_Report.tex")
    (OUTPUT / "data").mkdir(exist_ok=True)
    (OUTPUT / "presentation").mkdir(exist_ok=True)
    for source, target in (("metrics.csv", "epl_inverse_metrics.csv"), ("identity_diagnostics.csv", "epl_identity_diagnostics.csv"),
                           ("cohort_summary.json", "epl_cohort_summary.json"), ("summary.json", "epl_inverse_summary.json"),
                           ("inventory.csv", "epl_inverse_inventory.csv")):
        shutil.copyfile(PACKAGE / "epl_results" / source, OUTPUT / "data" / target)
    for name in ("inverse_metrics.csv", "conditional_uncertainty.csv", "summary.json", "audit_summary.json"):
        shutil.copyfile(PACKAGE / "nba_results" / name, OUTPUT / "data" / ("nba_" + name))
    with pd.ExcelWriter(OUTPUT / "data/Review_Metrics.xlsx", engine="xlsxwriter") as writer:
        sheets = {"EPL all funded accounts": pd.read_csv(PACKAGE / "epl_results/metrics.csv"),
                  "EPL original reconciliation": pd.read_csv(PACKAGE / "epl_results/original_reconciliation.csv"),
                  "EPL mirror diagnostics": pd.read_csv(PACKAGE / "epl_results/identity_diagnostics.csv"),
                  "NBA inverse accounts": pd.read_csv(PACKAGE / "nba_results/inverse_metrics.csv"),
                  "NBA uncertainty": pd.read_csv(PACKAGE / "nba_results/conditional_uncertainty.csv"),
                  "NBA annual inventory": pd.read_csv(PACKAGE / "nba_results/all_rolling_account_inventory.csv")}
        for name, frame in sheets.items():
            frame.to_excel(writer, sheet_name=name, index=False)
            worksheet = writer.sheets[name]
            worksheet.freeze_panes(1, 2)
            worksheet.autofilter(0, 0, len(frame), len(frame.columns) - 1)
            worksheet.set_column(0, len(frame.columns) - 1, 20)
        notes = pd.DataFrame({"Definition": ["Scope", "Primary EPL opposite", "NBA opposite", "Synthetic lay", "Expected gain/loss", "Uncertainty", "Selection"],
                              "Meaning": ["17 EPL bankrupt price contexts + 2 NBA annual bankrupt contexts; 34 EPL controls.",
                              "Two back legs, 1000 total maximum loss,100000 initial capital, equal gross payouts; date-funded.",
                              "Back the other team,100 requested,10000 initial; source sequential settlement.",
                              "1000 liability at unobserved lay price assumed equal to original back price; hypothetical only.",
                              "Original forecast probability-weighted positive and negative portfolio payoff components.",
                              "Conditional whole-date cashflow intervals; no re-fitting, re-sizing or model/strategy-search uncertainty.",
                              "Bankruptcy-triggered reversal is post hoc, not a new holdout or established future edge."]})
        notes.to_excel(writer, sheet_name="Read first", index=False)
        writer.sheets["Read first"].set_column(0, 0, 24)
        writer.sheets["Read first"].set_column(1, 1, 120)
    summary = json.loads((PACKAGE / "epl_results/summary.json").read_text(encoding="utf-8"))
    graphs = make_plots(OUTPUT / "report/figures")
    from .report_update import update_report
    update_report(OUTPUT, summary, PACKAGE / "nba_results")
    (OUTPUT / "report/README.txt").write_text("Reviewed final report: Aman Dhillon and Panagiotis Housos. Supervisor Daniel Totouom-Tangho. Order: common methodology, NBA results, Premier League results. Includes funded bankruptcy-opposite sensitivity and a final qualitative/quantitative review. Compile Final_Report.tex with XeLaTeX three times; figures and generated tables are included. Evidence paths printed in the report refer to the full repository. See final_review/README.md for data, code and interpretation limits.\n", encoding="utf-8")
    compilation = compile_report(OUTPUT / "report")
    from .deck_update import update_slides
    base_slides = json.loads((BASE / "presentation/presentation_content.json").read_text(encoding="utf-8"))
    for s in base_slides:
        for e in s["elements"]:
            if e.get("type") == "image":
                e["path"] = str(OUTPUT / "report/figures" / Path(e["path"]).name)
    slides = update_slides(base_slides, OUTPUT / "report/figures", summary, PACKAGE / "nba_results")
    jsave(OUTPUT / "presentation/presentation_content.json", slides)
    notes = ["# Reviewed final presentation", "", "Aman Dhillon and Panagiotis Housos", "Supervisor: Daniel Totouom-Tangho", ""]
    for i, s in enumerate(slides, 1):
        notes += [f"## Slide {i}: {s['title']}", "", s.get("subtitle", ""), "", s.get("notes", ""), "", "Sources:", *["- " + p for p in s["sources"]], ""]
    (OUTPUT / "presentation/Final_Presentation_Notes.md").write_text("\n".join(notes), encoding="utf-8")
    from final_deliverables.presentation_renderer import render
    rendering = render(slides, OUTPUT / "presentation")
    with zipfile.ZipFile(OUTPUT / "Final_Report_LaTeX.zip", "w", compression=zipfile.ZIP_DEFLATED) as z:
        for p in sorted((OUTPUT / "report").rglob("*")):
            if p.is_file() and (p.suffix == ".tex" or p.name == "README.txt" or p.parent.name == "figures" and p.suffix == ".pdf"):
                z.write(p, p.relative_to(OUTPUT / "report").as_posix())
    return finalize(OUTPUT, slides=slides, rendering=rendering, protected_hashes=protected_hashes,
                    compilation=compilation, graphs=graphs)


def finalize(output=OUTPUT, *, slides=None, rendering=None, protected_hashes=None, compilation=None, graphs=None):
    """Resume acceptance after the independent audit, without rerendering."""
    output = Path(output)
    if (output / "manifest.json").exists():
        raise RuntimeError("Completed versioned exports are immutable.")
    for relative, expected in json.loads((BASE / "manifest.json").read_text(encoding="utf-8"))["source_sha256"].items():
        assert sha(ROOT / relative) == expected, relative
    slides = slides or json.loads((output / "presentation/presentation_content.json").read_text(encoding="utf-8"))
    rendering = rendering or json.loads((output / "presentation/render_audit.json").read_text(encoding="utf-8"))
    for name, expected in rendering["sha256"].items():
        assert sha(output / "presentation" / name) == expected, name
    if protected_hashes is None:
        protected_hashes = {p: sha(p) for p in [ROOT / "epl_data/EPL_data_overview.xlsx",
            ROOT / "presentations/latest/EPL_Project_Presentation.pptx",
            ROOT / "presentations/latest/EPL_Project_Presentation_Draft.pptx"] if p.is_file()}
    audit = audit_output(output, slides, rendering)
    portable = output / "portable_source_audit.json"
    if portable.is_file():
        audit["portable_latex_source"] = json.loads(portable.read_text(encoding="utf-8"))
    jsave(output / "independent_audit.json", audit)
    for p, h in protected_hashes.items():
        assert sha(p) == h, p
    sources = [p for p in PACKAGE.rglob("*") if p.is_file() and "results" not in p.relative_to(PACKAGE).parts
               and "__pycache__" not in p.parts and p.suffix in {".py", ".md", ".json", ".csv", ".parquet"}]
    jsave(output / "manifest.json", {"completed_at_utc": datetime.now(timezone.utc).isoformat(),
        "base_run": BASE.relative_to(ROOT).as_posix(), "base_manifest_sha256": sha(BASE / "manifest.json"),
        "source_sha256": {p.relative_to(ROOT).as_posix(): sha(p) for p in sorted(sources)},
        "user_files_preserved": {p.relative_to(ROOT).as_posix(): h for p, h in protected_hashes.items()},
        "compilation": compilation or {"engine": "XeLaTeX", "passes": 3, "logs": "report/compile_pass_1..3.txt"},
        "slides": len(slides), "graphs": graphs or {"epl_inverse_capital": {"lines": 17, "initial_capital_each": 100000}},
        "output_sha256": {p.relative_to(output).as_posix(): sha(p) for p in sorted(output.rglob("*")) if p.is_file() and p.name != "manifest.json"}})
    publish(output)
    print(json.dumps({"output": str(output), "report_pages": audit["report_pages"], "slides": len(slides), "audit": "passed"}))


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--finalize", action="store_true", help="Accept an already compiled/rendered export after independent ledger audit")
    args = parser.parse_args()
    finalize() if args.finalize else build()
