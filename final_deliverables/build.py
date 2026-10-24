"""Assemble and verify the joint LaTeX report and editable presentation."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import zipfile

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter
import numpy as np
import pandas as pd

from epl_presentation.build import load as load_epl
from epl_presentation.concise import appendix_row

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = Path(__file__).parent
STUDY = ROOT / "epl_player_models/results/20261020_player_models_review"


def sha(path):
    value = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def jsave(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False, default=str) + "\n", encoding="utf-8")


def read_data():
    data = {name: json.loads((PACKAGE / (name + "_evidence.json")).read_text(encoding="utf-8")) for name in ("nba", "epl", "methodology")}
    data["epl_presentation_data"] = load_epl()
    data["nba_replay"] = json.loads((PACKAGE / "nba_core_replay/summary.json").read_text())
    assert not data["nba_replay"]["all_four_saved_finals_match_to_cent"]
    assert data["nba_replay"]["individually_reconciled_branches"] == ["Calibration LR"]
    return data


def number(value, places=2):
    return "--" if value is None or pd.isna(value) else f"{float(value):,.{places}f}"


def percent(value, places=2):
    return "--" if value is None or pd.isna(value) else f"{100 * float(value):.{places}f}%"


def tex(value):
    replacements = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#", "_": r"\_", "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}"}
    return "".join(replacements.get(char, char) for char in str(value)).replace("\n", r"\newline ")


def table_text(headers, rows, *, long=False, widths=None):
    columns = ("@{}" + "".join("p{" + str(w) + r"\linewidth}" for w in widths) + "@{}") if widths else "@{}Y" + "r" * (len(headers) - 1) + "@{}"
    head = " & ".join(tex(v) for v in headers) + r" \\" + "\n"
    lines = [r"\begin{longtable}{" + columns + "}" if long else r"\begin{tabularx}{\linewidth}{" + columns + "}", r"\toprule", head, r"\midrule"]
    if long:
        lines += [r"\endfirsthead", r"\toprule", head, r"\midrule", r"\endhead"]
    lines += [" & ".join(tex(v) for v in row) + r" \\" for row in rows]
    lines += [r"\bottomrule", r"\end{longtable}" if long else r"\end{tabularx}"]
    return "\n".join(lines) + "\n"


def write_tables(data, output):
    nba, epl = data["nba"], data["epl"]
    tables = output / "report/tables"; tables.mkdir(parents=True, exist_ok=True)
    registry = {}

    def put(name, headers, rows, **kwargs):
        registry[name] = {"headers": headers, "rows": rows}
        (tables / (name + ".tex")).write_text(table_text(headers, rows, **kwargs), encoding="utf-8")

    put("nba_splits", ["Role", "Seasons", "Games"], [[label, ", ".join(row["seasons"]), number(row["n_games"], 0)] for label, row in zip(
        ["Initial training", "Feature / hyperparameter validation", "Model-family selection", "Betting evaluation"], nba["chronological_splits"])])
    put("nba_selection", ["Family", "B: ECE (2 inputs)", "C: accuracy (4 inputs)"],
        [[{"LR": "Logistic regression", "RF": "Random forest", "MLP": "Neural network", "SVM": "SVM"}[r["family"]], percent(r["branch_B_ece"]), percent(r["branch_C_accuracy"])] for r in nba["training"]["model_selection_2017"]])
    put("nba_capital", ["Branch / model", "Stake", "Final capital", "Capital return", "Bet freq.", "Hit ratio"],
        [[r["branch"] + " / " + r["model"], "Flat 100" if r["staking"] == "fixed" else "1/8 Kelly", number(r["final_capital_saved_rounded"]),
          percent(r["capital_return_saved_rounded"]), percent(r["trading_frequency_saved_rounded"], 1), percent(r["hit_ratio_saved_rounded"], 1)] for r in nba["betting_2018"]["records"]])
    verified = [r for r in nba["replay"]["classification_metrics"] if r["matches_original_saved_outputs"]]
    assert len(verified) == 2
    put("nba_verified_scores", ["Predictor", "Accuracy", "ECE 20", "Log loss", "Binary Brier"],
        [["Matched logistic" if r["series"] == "Calibration" else "Normalised odds", percent(r["accuracy"]), percent(r["ece_binary_20"]), number(r["log_loss"], 4), number(r["brier_binary"], 4)] for r in verified])
    matched = nba["replay"]["verified_calibration_lr_metrics"]
    assert len(matched) == 2 and all(r["final_capital_matches_saved_to_cent"] for r in matched)
    put("nba_verified_trades", ["Stake", "Bets", "Hit", "Freq.", "G/trade", "L/trade", "Stake ROI", "Max DD"],
        [["Flat 100" if r["staking"] == "fixed" else "1/8 Kelly", number(r["n_bets"], 0), percent(r["hit_ratio"]), percent(r["trading_frequency"]),
          number(r["expected_gain_per_trade"]), number(r["expected_loss_per_trade"]), percent(r["roi_on_stakes"]), percent(r["max_drawdown"])] for r in matched])
    annual = nba["rolling_annual"]["records"]
    assert len(annual) == 9 and sum(r["n_games"] for r in annual) == 9344
    put("nba_annual", ["Season", "Games", "B inputs", "C inputs", "Cal. capital return", "Acc. capital return"],
        [[r["season"], number(r["n_games"], 0), str(r["n_features_calibration"]), str(r["n_features_accuracy"]),
          percent(r["calibration_return_on_initial_capital"]), percent(r["accuracy_return_on_initial_capital"])] for r in annual])

    labels = {"accuracy": "Accuracy-selected SVM", "calibration": "Calibration-selected MLP", "bet365_devig": "Normalised Bet365", "training_class_frequency": "Training frequencies"}
    put("epl_primary_scores", ["Predictor", "Accuracy", "ECE 10", "Log loss", "Brier"],
        [[labels[r["model"]], percent(r["accuracy"]), percent(r["classwise_ece_10"]), number(r["log_loss"], 4), number(r["brier_score"], 4)] for r in epl["first_experiment"]["test_probability_scores"]])
    secondary = [r for r in epl["first_experiment"]["test_betting_native1000initial10flat"] if r["policy"] == "fixed_5pct_secondary"]
    if not secondary:
        secondary = [r for r in epl["first_experiment"]["test_betting_native1000initial10flat"] if r["threshold"] == .05]
    assert len(secondary) == 8
    put("epl_secondary", ["Branch / odds", "Stake", "Bets", "Profit", "Stake ROI", "95% ROI interval"],
        [[("SVM" if r["branch"] == "accuracy" else "MLP") + " / " + ("Best" if r["odds_mode"] == "best_individual_book" else "Bet365"),
          "Flat 10" if r["staking"] == "fixed" else "1/4 Kelly", str(r["bet_count"]), number(r["profit"]), percent(r["roi"]),
          "[" + percent(r["roi_ci_low"]) + ", " + percent(r["roi_ci_high"]) + "]"] for r in secondary])
    profiles = epl["rolling_and_player_extensions"]["main_model_profiles"]
    names = {"strongest_benchmark": "Raw market benchmark", "best_learned": "Best learned: odds + team/FPL", "team": "Team logistic", "player": "Player-form logistic", "simplest": "Class frequency"}
    put("epl_rolling", ["Predictor", "Accuracy", "Log loss", "Brier"],
        [[names[k], percent(profiles[k]["metrics"]["accuracy"]), number(profiles[k]["metrics"]["log_loss"], 4), number(profiles[k]["metrics"]["brier_score"], 4)]
         for k in ("strongest_benchmark", "best_learned", "team", "player", "simplest")])
    epl_data = data["epl_presentation_data"]
    continuous = epl_data["continuous"]
    put("epl_representative", ["ID", "Bets", "Hit", "Freq.", "Final capital", "Stake ROI", "G/trade", "L/trade", "Max DD"],
        [[sid, number(r.bet_count, 0), percent(r.hit_ratio), percent(r.trading_frequency), number(r.final_capital_sum_units), percent(r.roi),
          number(r.expected_gain_per_trade_units), number(r.expected_loss_per_trade_units), percent(r.max_drawdown)] for sid, r in continuous.loc[["S029", "S033", "S017", "P009", "S060", "P028"]].iterrows()])
    rules = []
    for row in epl_data["catalog"]:
        r = appendix_row([row])
        r[0] = row["strategy_id"]
        if r[3].startswith(row["strategy_id"] + ": "):
            r[3] = r[3].split(": ", 1)[1]
        rules.append(r)
    put("epl_all_rules", ["ID", "Model / data", "Entry", "Stake / cap", "Prices"], rules,
        long=True, widths=[.07, .23, .27, .25, .10])
    put("epl_all_metrics", ["ID", "Bets", "Hit", "Freq.", "G/trade", "L/trade", "Final capital", "ROI", "Max DD"],
        [[sid, number(r.bet_count, 0), percent(r.hit_ratio), percent(r.trading_frequency), number(r.expected_gain_per_trade_units), number(r.expected_loss_per_trade_units),
          number(r.final_capital_sum_units), percent(r.roi), percent(r.max_drawdown)] for sid, r in epl_data["single"].iterrows()],
        long=True, widths=[.07, .06, .10, .10, .12, .12, .14, .09, .10])
    (output / "data").mkdir(exist_ok=True)
    jsave(output / "data/display_tables.json", registry)
    return registry


def plots(data, figures):
    figures.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.family": "Arial", "font.size": 11, "pdf.fonttype": 42, "ps.fonttype": 42})
    saved = data["nba"]["betting_2018"]["records"]
    fig, ax = plt.subplots(figsize=(9.5, 4.1))
    values = [r["final_capital_saved_rounded"] for r in saved]
    labels = [r["branch"] + "\n" + ("Flat 100" if r["staking"] == "fixed" else "1/8 Kelly") for r in saved]
    ax.bar(range(4), values, color=["#0D897D", "#77B7AC", "#11243A", "#8193A8"], width=.63)
    ax.axhline(10000, linestyle="--", color="#87929B", linewidth=1, label="Starting capital 10,000")
    for i, value in enumerate(values):
        ax.text(i, value + 350, f"{value:,.2f}", ha="center", va="bottom", fontsize=11)
    ax.set_xticks(range(4), labels); ax.set_ylabel("Capital (native monetary units)")
    ax.set_ylim(0, 14500); ax.legend(loc="upper right", frameon=False, fontsize=10)
    ax.spines[["top", "right"]].set_visible(False); ax.grid(axis="y", alpha=.15); ax.set_axisbelow(True)
    fig.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(figures / ("nba_core_capital." + ext), dpi=190)
    plt.close(fig)

    annual = data["nba"]["rolling_annual"]["records"]
    fig, ax = plt.subplots(figsize=(13.8, 4.6))
    x = np.arange(len(annual))
    for offset, key, label, color in ((-.19, "calibration_return_on_initial_capital", "Calibration-selected features; LR", "#0D897D"),
                                     (.19, "accuracy_return_on_initial_capital", "Accuracy-selected features; LR", "#11243A")):
        ax.bar(x + offset, [100 * r[key] for r in annual], width=.36, label=label, color=color)
    ax.axhline(0, color="#667888", linewidth=.8)
    ax.set_xticks(x, [r["season"] for r in annual]); ax.set_ylabel("Capital return in each restarted season (%)")
    ax.set_ylim(-120, 120); ax.legend(loc="upper left", ncol=2, frameon=False, fontsize=10)
    ax.grid(axis="y", alpha=.2); ax.set_axisbelow(True); ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(figures / ("nba_annual_returns." + ext), dpi=190)
    plt.close(fig)
    graph_info = {}
    for scope, stem, lead in (("single", "epl_all_116", "P028"), ("continuous", "epl_all_88", "S060")):
        graph = data["epl_presentation_data"]["graphs"][scope]
        chosen = {lead: "#0D897D", "S029": "#4376AC", "S033": "#735AA6", "S017": "#2A8A94", "P009": "#D18B18"}
        fig, ax = plt.subplots(figsize=(14.2, 5.1))
        for sid, group in graph.groupby("strategy_id", sort=True):
            group = group.sort_values("match_date")
            line, = ax.step(group.match_date, group.end_bankroll, where="post", linewidth=1.8 if sid in chosen else .6,
                color=chosen.get(sid, "#A6B0BA" if sid.startswith("S") else "#CFB78C"), alpha=1 if sid in chosen else .6,
                zorder=3 if sid in chosen else 1)
            line.set_gid("strategy-" + sid)
        ax.axhline(100000, color="#7B8793", linestyle="--", linewidth=.8)
        ax.set_xlim(graph.match_date.min(), graph.match_date.max()); ax.set_ylim(0, graph.end_bankroll.max() * 1.07)
        ax.set_xlabel("Date"); ax.set_ylabel("Account capital (monetary units)")
        ax.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value / 1000:g}K"))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2 if scope == "single" else 8))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y")); ax.grid(axis="y", alpha=.18)
        ax.spines[["top", "right"]].set_visible(False)
        legend = [Line2D([0], [0], color="#A6B0BA", label="Other original rules"), Line2D([0], [0], color="#CFB78C", label="Other new rules")]
        legend += [Line2D([0], [0], color=c, label=s + (" capital leader" if s == lead else "")) for s, c in chosen.items()]
        ax.legend(handles=legend, loc="upper center", bbox_to_anchor=(.5, -.19), ncol=4, frameon=False, fontsize=10)
        fig.subplots_adjust(left=.09, right=.99, top=.98, bottom=.28)
        for ext in ("pdf", "png", "svg"):
            fig.savefig(figures / (stem + "." + ext), dpi=185)
        plt.close(fig)
        graph_info[stem] = {"strategy_ids": sorted(graph.strategy_id.unique()), "points": len(graph), "starting_capital": 100000}
    return graph_info


def compile_report(report):
    engine = shutil.which("xelatex")
    if not engine:
        engine = str(Path(os.environ["LOCALAPPDATA"]) / "Programs/MiKTeX/miktex/bin/x64/xelatex.exe")
    if not Path(engine).is_file():
        raise RuntimeError("XeLaTeX is required to compile the final report")
    compile_env = dict(os.environ)
    compile_env["PATH"] = str(Path(engine).parent) + os.pathsep + compile_env.get("PATH", "")
    for pass_number in (1, 2, 3):
        result = subprocess.run([engine, "-interaction=nonstopmode", "-halt-on-error", "-no-shell-escape", "Final_Report.tex"],
            cwd=report, env=compile_env, capture_output=True, text=True, errors="replace")
        (report / f"compile_pass_{pass_number}.txt").write_text(result.stdout + "\n" + result.stderr, encoding="utf-8")
        if result.returncode:
            raise RuntimeError("XeLaTeX failed: " + result.stdout[-4500:] + result.stderr[-1000:])
    return {"engine": engine, "passes": 3}


def input_paths(data):
    names = set()
    for key in ("nba", "epl", "methodology"):
        names.update(data[key]["source_sha256"])
    files = {ROOT / name for name in names}
    files.update(p for p in PACKAGE.glob("*") if p.is_file() and p.suffix in {".py", ".json", ".tex", ".md", ".txt"})
    files.update(p for p in (PACKAGE / "nba_core_replay").iterdir() if p.is_file())
    for name in ("epl_presentation/build.py", "epl_presentation/render.py", "epl_presentation/concise.py", "epl_presentation/simple_rules.py",
                 "epl_presentation/research_models.json", "epl_presentation/research_trading.json", "epl_presentation/research_audit.json",
                 "epl_modeling/ablation_results/predictions.parquet", "epl_strategy_lab/results/20261015T040052Z_100k84/metrics.parquet",
                 "epl_strategy_validation/results/20261015_temporal_selection/metrics_continuous.parquet"):
        files.add(ROOT / name)
    for name in ("metrics_single.parquet", "metrics_continuous.parquet", "all_strategy_catalog.json", "graph_equity_2025_all.csv", "graph_equity_continuous_all.csv", "predictions.parquet"):
        files.add(STUDY / name)
    return sorted(files)


def publish(output):
    latest = ROOT / "deliverables/final"
    if latest.exists():
        raise ValueError("The final-deliverables folder already exists; preserve any edited final files")
    latest.mkdir(parents=True)
    report, presentation = output / "report", output / "presentation"
    names = ["Final_Report.tex", "methodology.tex", "numbers.tex", "Final_Report.pdf"]
    copies = {}
    for name in names:
        shutil.copyfile(report / name, latest / name)
        copies[name] = {"source": (report / name).relative_to(ROOT).as_posix(), "sha256": sha(latest / name)}
    for folder in ("tables", "figures"):
        shutil.copytree(report / folder, latest / folder)
        for path in (report / folder).rglob("*"):
            if path.is_file():
                relative = path.relative_to(report).as_posix()
                copies[relative] = {"source": path.relative_to(ROOT).as_posix(), "sha256": sha(latest / relative)}
    for name in ("Final_Project_Presentation.pptx", "Final_Project_Presentation.pdf", "Final_Presentation_Notes.md"):
        shutil.copyfile(presentation / name, latest / name)
        copies[name] = {"source": (presentation / name).relative_to(ROOT).as_posix(), "sha256": sha(latest / name)}
    shutil.copyfile(output / "Final_Report_LaTeX.zip", latest / "Final_Report_LaTeX.zip")
    copies["Final_Report_LaTeX.zip"] = {"source": (output / "Final_Report_LaTeX.zip").relative_to(ROOT).as_posix(), "sha256": sha(latest / "Final_Report_LaTeX.zip")}
    (latest / "README.txt").write_text("Final report and presentation: Aman Dhillon and Panagiotis Housos. Supervisor Daniel Totouom-Tangho. Order: common methodology, NBA results, Premier League results. Compile the complete LaTeX source with XeLaTeX three times; alternatively open Final_Report.pdf. The source ZIP is self-contained for report compilation.\n", encoding="utf-8")
    jsave(latest / "manifest.json", {"canonical_run": output.relative_to(ROOT).as_posix(), "copies": copies,
        "author_names": ["Aman Dhillon", "Panagiotis Housos"], "supervisor": "Daniel Totouom-Tangho"})


def build(output, *, draft=False, publish_final=False):
    output = Path(output).resolve()
    if output.exists() and not draft:
        raise ValueError("Choose a new immutable final output directory")
    if not draft and (PACKAGE / "results").resolve() not in output.parents:
        raise ValueError("Final versioned runs belong in final_deliverables/results")
    data = read_data()
    paths = input_paths(data)
    before = {p: sha(p) for p in paths}
    edited_book = ROOT / "epl_data/EPL_data_overview.xlsx"
    book_sha = sha(edited_book)
    output.mkdir(parents=True, exist_ok=True)
    for folder in ("report", "presentation", "data"):
        (output / folder).mkdir(exist_ok=True)
    for key in ("nba", "epl", "methodology"):
        jsave(output / "data" / (key + "_evidence.json"), data[key])
    print("Building source-checked common, NBA and EPL tables", flush=True)
    registry = write_tables(data, output)
    graph_info = plots(data, output / "report/figures")
    shutil.copyfile(PACKAGE / "report_template.tex", output / "report/Final_Report.tex")
    methodology = (PACKAGE / "methodology_draft.tex").read_text(encoding="utf-8")
    methodology = methodology.replace(r"p{0.20\textwidth}p{0.35\textwidth}p{0.35\textwidth}",
        r">{\raggedright\arraybackslash}p{0.20\textwidth}>{\raggedright\arraybackslash}p{0.35\textwidth}>{\raggedright\arraybackslash}p{0.35\textwidth}")
    (output / "report/methodology.tex").write_text(methodology, encoding="utf-8")
    (output / "report/numbers.tex").write_text("% Source-linked numerical tables are generated in tables/.\n", encoding="utf-8")
    print("Compiling the actual LaTeX report", flush=True)
    compilation = compile_report(output / "report")
    from .joint_deck import build_slides
    from .presentation_renderer import render
    slides = build_slides(data, output / "report/figures")
    jsave(output / "presentation/presentation_content.json", slides)
    notes = ["# Joint final presentation", "", "Aman Dhillon and Panagiotis Housos", "Supervisor: Daniel Totouom-Tangho", ""]
    for i, s in enumerate(slides, 1):
        notes.extend([f"## Slide {i}: {s['title']}", "", s["subtitle"], "", s["notes"], "", "Sources:", *["- " + p for p in s["sources"]], ""])
    (output / "presentation/Final_Presentation_Notes.md").write_text("\n".join(notes), encoding="utf-8")
    print(f"Rendering {len(slides)} editable presentation slides", flush=True)
    rendering = render(slides, output / "presentation")
    source_readme = "Compile Final_Report.tex with XeLaTeX three times. Included figures/tables are generated from the archived project evidence. Authors: Aman Dhillon and Panagiotis Housos. Supervisor: Daniel Totouom-Tangho.\n"
    (output / "report/README.txt").write_text(source_readme, encoding="utf-8")
    with zipfile.ZipFile(output / "Final_Report_LaTeX.zip", "w", compression=zipfile.ZIP_DEFLATED) as z:
        for path in sorted((output / "report").rglob("*")):
            if path.is_file() and (path.suffix in {".tex", ".txt"} and not path.name.startswith("compile_pass") or path.parent.name == "figures" and path.suffix == ".pdf"):
                z.write(path, path.relative_to(output / "report").as_posix())
    from .audit import audit
    checked = audit(output)
    jsave(output / "independent_audit.json", checked)
    if sha(edited_book) != book_sha or any(sha(p) != h for p, h in before.items()):
        raise AssertionError("An original input or user workbook changed")
    manifest = {"completed_at_utc": datetime.now(timezone.utc).isoformat(), "authors": ["Aman Dhillon", "Panagiotis Housos"],
        "supervisor": "Daniel Totouom-Tangho", "order": ["Common methodology", "NBA results", "Premier League results"],
        "source_sha256": {p.relative_to(ROOT).as_posix(): h for p, h in before.items()}, "user_workbook_sha256": book_sha,
        "sources_unchanged": True, "no_new_model_selection_or_forecast_release": True,
        "nba_fixed_parameter_audit": "LR matches; SVM does not; saved SVM results are source-reported",
        "compilation": compilation, "rendering": {"slide_count": len(slides), "native_text_overflows": rendering["native_layout"]["text_overflow_count"]},
        "graphs": graph_info, "audit": checked,
        "output_sha256": {p.relative_to(output).as_posix(): sha(p) for p in sorted(output.rglob("*")) if p.is_file() and p.name != "manifest.json"}}
    jsave(output / "manifest.json", manifest)
    if publish_final:
        publish(output)
    return {"output": str(output), "audit": checked, "slides": len(slides)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--draft", action="store_true")
    parser.add_argument("--publish", action="store_true")
    args = parser.parse_args()
    print(json.dumps(build(args.output, draft=args.draft, publish_final=args.publish), indent=2))
