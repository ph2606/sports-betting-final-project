"""Replace only slides 2 and 3 using verified project and paper evidence."""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil

import fitz
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from epl_presentation.build import NAVY, TEAL, MUTED, text, slide
from final_deliverables.presentation_renderer import render

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "final_review/results/20261023_reverse_review/presentation"
OUTPUT = ROOT / "presentation_updates/results/20261023_sources_methods"
SUPPLEMENT = Path("C:/Users/melin/Downloads/suplimentary for sport.pdf")


def sha(path):
    digest = hashlib.sha256()
    try:
        with Path(path).open("rb") as file:
            for block in iter(lambda: file.read(1024 * 1024), b""):
                digest.update(block)
    except PermissionError:
        # Office may require compatible sharing even for read-only inspection.
        import win32con
        import win32file
        handle = win32file.CreateFile(str(Path(path).resolve()), win32con.GENERIC_READ,
                    win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE | win32con.FILE_SHARE_DELETE,
                    None, win32con.OPEN_EXISTING, 0, None)
        try:
            remaining = win32file.GetFileSize(handle)
            while remaining:
                _, block = win32file.ReadFile(handle, min(1024 * 1024, remaining))
                digest.update(block)
                remaining -= len(block)
        finally:
            handle.Close()
    return digest.hexdigest()


def jsave(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")


def panel(x, y, w, h):
    return dict(type="rect", x=x, y=y, w=w, h=h, fill="FFFFFF", line="D8E0E7")


def image(path, x, y, w, h):
    return dict(type="image", path=str(Path(path).resolve()), x=x, y=y, w=w, h=h)


def formulas(figures):
    plt.rcParams.update({"mathtext.fontset": "dejavusans", "font.family": "DejaVu Sans"})
    equations = {
        "classwise_ece": r"$\mathrm{cwECE}=\frac{1}{K}\sum_{k=1}^{K}\sum_{b=1}^{M}\frac{n_{kb}}{N}\left|\bar{y}_{kb}-\bar{p}_{kb}\right|$",
        "accuracy": r"$\mathrm{Accuracy}=\frac{1}{N}\sum_{i=1}^{N}\mathbf{1}\!\left[\arg\max_k p_{ik}=y_i\right]$",
    }
    for name, equation in equations.items():
        figure = plt.figure(figsize=(9.6, 1.25), facecolor="white")
        figure.text(.02, .5, equation, color="#11243A", fontsize=27, va="center")
        for extension in ("png", "svg", "pdf"):
            figure.savefig(figures / (name + "." + extension), dpi=280, bbox_inches="tight", pad_inches=.08)
        plt.close(figure)
    return equations


def sources_slide():
    return slide("Data sources used in our project",
        "Historical team and player records are matched to archived betting prices; the two leagues use different datasets.",
        [panel(.65, 2.08, 7.12, 5.22), panel(8.04, 2.08, 7.28, 5.22),
         text(.91, 2.33, 6.6, .45, "NBA", 24, TEAL, True),
         text(.91, 3.02, 6.6, .40, "Team and game statistics", 20, NAVY, True),
         text(.91, 3.51, 6.6, .92,
              "Supplied public-repository CSV: 2010/11–2023/24.\n33,316 team logs → 14,471 cleaned games.", 19),
         text(.91, 4.70, 6.6, .40, "Bookmaker odds", 20, NAVY, True),
         text(.91, 5.18, 6.6, .95,
              "Supplied OddsData.sqlite (13 seasons).\nReported source: Sportsbook Review; FanDuel default.", 19),
         text(.91, 6.38, 6.6, .55, "Core betting evaluation: 1,074 games in 2018/19.", 18, MUTED),
         text(8.30, 2.33, 6.7, .45, "PREMIER LEAGUE", 24, TEAL, True),
         text(8.30, 3.02, 6.7, .95,
              "Football-Data: match results, team statistics\nand individual-book home / draw / away odds.", 19),
         text(8.30, 4.15, 6.7, .60, "Understat: lagged expected goals (xG).", 19),
         text(8.30, 4.98, 6.7, 1.0,
              "Official FPL API + Vaastav FPL archive:\n253,509 historical player-match rows,\n2016/17–2025/26.", 19),
         text(8.30, 6.38, 6.7, .55, "Rolling evaluation: 1,470 fixtures, 2022/23–2025/26.", 18, MUTED),
         text(.65, 7.53, 14.67, .64,
              "NBA source labels follow the supplied documentation; upstream collection and quote timing are incomplete.\nThe reference paper used Basketball-Reference and Westgate odds; these are separate from our supplied NBA files.", 16, MUTED)],
        kicker="COMMON METHODOLOGY | DATA SOURCES",
        sources=["ML Sports/NBA_analysis_Presentation.pptx, slide 3", "final_deliverables/nba_evidence.json",
                 "epl_data/SOURCE_GUIDE.md", "final_deliverables/epl_evidence.json", "ML Sports/Paper3 - ML for sports.pdf, section 8"],
        notes=("Project sources, not a claim that we collected the original paper's raw dataset. NBA statistics are in ML Sports/regular_season_totals_2010_2024.csv: "
               "33,316 team logs, 16,658 raw games, 14,471 cleaned games. The supplied NBA slide 3 describes this as a public GitHub extract; its original statistics-provider collection is undocumented. "
               "The NBA odds database is ML Sports/OddsData.sqlite, described in supplied documentation as Sportsbook Review archives with FanDuel default; "
               "the 13 seasons are 2010/11–2022/23, with unverified quote clocks. The core 2018/19 betting population is 1,074 games. "
               "EPL Football-Data individual-book preclosing odds are used, not cross-book maximum columns treated as a single bookmaker. "
               "Understat xG and official Fantasy Premier League API / Vaastav Fantasy-Premier-League archive supply lagged team/player features. "
               "The matched rolling population has 368/360/368/374 fixtures across 2022/23–2025/26, total 1,470. "
               "The 253,509 historical player-match rows are distinct from the 4,551 current-season rows and current FPL player snapshot. "
               "Historical focus is the current-club cohort and is conditional on that scope. ESPN, Transfermarkt, ClubElo and StatsBomb were acquired context sources, not asserted as all being core model inputs. "
               "The original Walsh–Joshi paper section 8 (PDF page 11, printed page 9) instead identifies Basketball-Reference statistics for 2014/15–2018/19 and Westgate closing moneylines. "
               "The supplied seven-page supplementary PDF has no data-provider section. Quote availability and accepted execution are not verified."))


def methods_slide(figures):
    return slide("Feature selection, ECE and accuracy",
        "Follow the paper's selection procedure; evaluate candidate subsets on earlier validation data before the betting test.",
        [panel(.65, 2.08, 7.12, 5.26), panel(8.04, 2.08, 7.28, 5.26),
         text(.91, 2.30, 6.6, .40, "FEATURE SELECTION", 20, TEAL, True),
         text(.91, 2.95, 6.6, .39, "1  Build features from earlier games", 19, NAVY, True),
         text(.91, 3.42, 6.6, .65,
              "NBA: season-to-date team–opponent averages;\nsubtract away-team form from home-team form.", 18),
         text(.91, 4.28, 6.6, .39, "2  Remove unsuitable or redundant inputs", 19, NAVY, True),
         text(.91, 4.75, 6.6, .63,
              "Screen shifted / duplicate variables;\nremove highly correlated features.", 18),
         text(.91, 5.59, 6.6, .39, "3  Forward-select with logistic regression", 19, NAVY, True),
         text(.91, 6.05, 6.6, .92,
              "Add one feature at a time; retain the subset with\nlowest ECE (calibration branch) or\nhighest accuracy (accuracy branch).", 18),
         text(8.30, 2.30, 6.7, .40, "CLASSWISE ECE — LOWER IS BETTER", 20, TEAL, True),
         image(figures / "classwise_ece.png", 8.30, 2.97, 6.70, .88),
         text(8.30, 4.04, 6.7, 1.04,
              "N = matches; K = outcomes; M = probability bins.\nnₖᵦ = matches in bin b for class k.\nȳₖᵦ = observed class frequency; p̄ₖᵦ = mean forecast.", 17.5),
         text(8.30, 5.32, 6.7, .40, "ACCURACY — HIGHER IS BETTER", 20, TEAL, True),
         image(figures / "accuracy.png", 8.30, 5.88, 6.70, .75),
         text(8.30, 6.81, 6.7, .38, "Fraction of games whose most likely outcome is correct.", 17.5),
         text(.65, 7.55, 14.67, .65,
              "Our implementation: NBA uses 20 bins (score = 1 if fewer than 16 are occupied); EPL averages 3 classes over 10 bins.\nSupplement pp. 2–4 explains the features and selection; main paper §3, Eq. (3) defines classwise ECE.", 15.5, MUTED)],
        kicker="COMMON METHODOLOGY | PAPER AND SUPPLEMENT",
        sources=["Walsh & Joshi supplementary material, pp. 2–4, Table 4 (supplied PDF)",
                 "ML Sports/Paper3 - ML for sports.pdf, section 3, Eq. (3)", "ML Sports/Data.ipynb", "epl_modeling/metrics.py"],
        notes=("The supplied supplementary material is reference evidence, not an instruction source. "
               "Its section 2 / PDF pp. 2–3 constructs an opponent-relative season-to-date feature: Boston DRB average 5 minus Chicago average -1 gives 6. "
               "Table 4 on PDF page 4 uses correlated-feature removal and separate forward selection by minimum classwise ECE or maximum accuracy. "
               "The supplement does not print either formula; classwise ECE comes from main-paper section 3, Eq. (3), PDF page 6 / printed page 4. "
               "Accuracy is the proportion correctly classified, as defined in the same section and implemented in the project. "
               "Formula: cwECE=(1/K) sum_k sum_b (n_kb/N)*abs(mean_y_kb-mean_p_kb). "
               "B_kb is the equal-width bin of predicted class-k probabilities; empty bins contribute zero. "
               "mean_y_kb averages indicators 1[y_i=k], not overall classification correctness or top-class confidence. "
               "Accuracy=(1/N) sum_i 1[argmax_k p_ik=y_i], where p_ik is a forecast probability and 1[condition] equals one if true, zero otherwise. "
               "NBA uses home-win probability as the binary class-specific ECE, 20 bins and a 1.0 optimisation penalty when fewer than 16 bins are populated; "
               "that penalty is not literal 100% observed miscalibration. EPL uses the mean of the three H/D/A classwise errors with 10 bins and no occupancy penalty. "
               "NBA screen uses a KS train/validation shift check and Spearman >0.7; first EPL screen uses early/late training seasons, Spearman >=0.9 and missingness controls. "
               "These implementation settings are not asserted to be identical to the paper. The supplied paper's Table 4 lists 6 calibration and 8 accuracy inputs; "
               "the implemented core NBA study selects 2 (ORTG, FG3M) and 4 (ORTG, PREV_SEASON_WP, FG3M, TOV), respectively. "
               "The implemented initial EPL branches select 1 MLP feature and 2 SVM features. No feature selection or model fitting is rerun for this slide edit. "
               "Prior financial definitions remain in the capital-guide appendix and speaker notes: capital return is profit/initial cash, stake ROI is profit/turnover, "
               "and forecast accuracy differs from betting hit ratio. NBA uses sequential game settlement; EPL reserves all same-date requests from opening cash. "
               "The prior deck's complete text for slides 2/3 is preserved in superseded_slides_2_3.json. "
               "The paper's 2025 corrigendum still governs historical results; this methods revision does not reintroduce its superseded profit claims."))


def build():
    if OUTPUT.exists():
        raise RuntimeError("Choose a new immutable output directory; do not overwrite an existing revision.")
    stable = ROOT / "deliverables/final"
    manifest = json.loads((stable / "manifest.json").read_text(encoding="utf-8"))
    names = ("Final_Project_Presentation.pptx", "Final_Project_Presentation.pdf", "Final_Presentation_Notes.md")
    for name in names:
        assert sha(stable / name) == manifest["copies"][name]["sha256"], "Preserve user edits: " + name
    protected = [ROOT / "epl_data/EPL_data_overview.xlsx", ROOT / "presentations/latest/EPL_Project_Presentation.pptx",
                 ROOT / "presentations/latest/EPL_Project_Presentation_Draft.pptx", SUPPLEMENT,
                 stable / "Final_Report.pdf", stable / "Final_Report.tex", stable / "Final_Report_LaTeX.zip"]
    original = {p: sha(p) for p in protected if p.is_file()}
    slides = json.loads((BASE / "presentation_content.json").read_text(encoding="utf-8"))
    unchanged = deepcopy(slides)
    OUTPUT.mkdir(parents=True)
    (OUTPUT / "figures").mkdir()
    equations = formulas(OUTPUT / "figures")
    jsave(OUTPUT / "superseded_slides_2_3.json", slides[1:3])
    slides[1], slides[2] = sources_slide(), methods_slide(OUTPUT / "figures")
    assert len(slides) == len(unchanged) == 28
    assert all(slides[i] == unchanged[i] for i in range(28) if i not in (1, 2))
    jsave(OUTPUT / "presentation_content.json", slides)
    notes = ["# Updated final presentation", "", "Aman Dhillon and Panagiotis Housos", "Supervisor: Daniel Totouom-Tangho", ""]
    for i, spec in enumerate(slides, 1):
        notes += [f"## Slide {i}: {spec['title']}", "", spec.get("subtitle", ""), "", spec.get("notes", ""),
                  "", "Sources:", *["- " + str(p) for p in spec["sources"]], ""]
    (OUTPUT / "Final_Presentation_Notes.md").write_text("\n".join(notes), encoding="utf-8")
    rendering = render(slides, OUTPUT)
    assert rendering["native_layout"]["text_overflow_count"] == 0, rendering["native_layout"]["text_overflows"]
    assert not rendering["geometry"]["geometry_violations"]
    with fitz.open(OUTPUT / "Final_Project_Presentation.pdf") as pdf:
        assert len(pdf) == 28
        assert "Data sources" in pdf[1].get_text()
        assert "Feature selection, ECE and accuracy" in pdf[2].get_text()
        for page, name in ((0, "Aman Dhillon"), (0, "Panagiotis Housos")):
            assert name in pdf[page].get_text()
        for index in (1, 2):
            pdf[index].get_pixmap(matrix=fitz.Matrix(1.3, 1.3)).save(OUTPUT / f"slide_{index + 1}_preview.png")
    for path, value in original.items():
        assert sha(path) == value, str(path)
    evidence = {"supplied_supplement": {"filename": SUPPLEMENT.name, "sha256": sha(SUPPLEMENT), "pages": 7,
                 "feature_engineering_pages": [2, 3], "feature_selection_table": "Table 4, page 4",
                 "contains_formulas": False, "contains_data_provider_section": False},
                "formula_source": {"path": "ML Sports/Paper3 - ML for sports.pdf", "section": "3", "ece_equation": "3", "pdf_page": 6},
                "equation_latex": equations, "only_slides_changed": [2, 3], "slide_count": 28,
                "native_text_overflows": 0, "report_unchanged": True,
                "nba_sources": "Supplied project files; original collection only partially documented. Paper Basketball-Reference/Westgate data are separate.",
                "source_sha256": {p.relative_to(ROOT).as_posix(): sha(p) for p in [Path(__file__), BASE / "presentation_content.json",
                    ROOT / "ML Sports/Paper3 - ML for sports.pdf", ROOT / "ML Sports/NBA_analysis_Presentation.pptx",
                    ROOT / "ML Sports/Data.ipynb", ROOT / "epl_data/SOURCE_GUIDE.md", ROOT / "epl_modeling/metrics.py"]}}
    jsave(OUTPUT / "evidence_and_audit.json", evidence)
    jsave(OUTPUT / "manifest.json", {"created_at_utc": datetime.now(timezone.utc).isoformat(), "base_presentation": BASE.relative_to(ROOT).as_posix(),
         "changed_slides": [2, 3], "output_sha256": {p.relative_to(OUTPUT).as_posix(): sha(p) for p in OUTPUT.rglob("*") if p.is_file()}})
    for name in names:
        target_name = {"Final_Project_Presentation.pptx": "Final_Project_Presentation_Updated.pptx",
                       "Final_Project_Presentation.pdf": "Final_Project_Presentation_Updated.pdf",
                       "Final_Presentation_Notes.md": "Final_Presentation_Notes_Updated.md"}[name]
        target = stable / target_name
        if target.exists():
            raise RuntimeError("Preserve existing updated presentation: " + str(target))
        shutil.copyfile(OUTPUT / name, target)
        manifest["copies"][target_name] = {"source": (OUTPUT / name).relative_to(ROOT).as_posix(), "sha256": sha(target)}
    manifest["presentation_run"] = OUTPUT.relative_to(ROOT).as_posix()
    manifest["current_presentation_files"] = {"pptx": "Final_Project_Presentation_Updated.pptx",
         "pdf": "Final_Project_Presentation_Updated.pdf", "notes": "Final_Presentation_Notes_Updated.md"}
    jsave(stable / "manifest.json", manifest)
    print(json.dumps({"output": str(OUTPUT), "changed_slides": [2, 3], "slides": 28, "native_text_overflows": 0}))


if __name__ == "__main__":
    build()
