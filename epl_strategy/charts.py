"""Render all declared strategy alternatives from an immutable analytics export.

Usage: python -m epl_strategy.charts --results PATH
Creates figures/ once, or a new explicitly supplied --output-dir. No model,
threshold, source table or existing analytics file is changed.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import PercentFormatter
import numpy as np
import pandas as pd


STYLE = {"font.family": "DejaVu Sans", "font.size": 10, "axes.titlesize": 12,
         "axes.labelsize": 10, "axes.spines.top": False, "axes.spines.right": False,
         "axes.formatter.useoffset": False, "svg.fonttype": "none", "savefig.facecolor": "white"}
STAKING = {"fixed": ("Fixed stake 10", "F", "o", "#245c85"),
           "kelly": ("Quarter Kelly, cap 2%", "K", "s", "#ac6529")}
GROUP_NAMES = {"team": "Team", "team_xg": "Team + xG", "team_player": "Team + player",
               "combined": "Combined", "market_only": "Market", "class_frequency": "Class frequency"}
MODEL_NAMES = {"logistic": "Logistic", "market_residual": "Market residual",
               "market_temperature": "Temperature-calibrated market", "baseline": "Baseline"}
POOLED_ORDER = [(kind, group) for kind in ("logistic", "market_residual")
                for group in ("team", "team_xg", "team_player", "combined")]
POOLED_ORDER += [("baseline", "market_only"), ("market_temperature", "market_only"),
                 ("baseline", "class_frequency")]


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _pair_name(kind, group):
    if kind == "baseline":
        return "Raw de-vigged market" if group == "market_only" else "Training class frequency"
    if kind == "market_temperature":
        return MODEL_NAMES[kind]
    return MODEL_NAMES[kind] + " / " + GROUP_NAMES[group]


def _ordered_pooled(frame):
    rows = []
    for kind, group in POOLED_ORDER:
        for staking in ("fixed", "kelly"):
            one = frame.loc[frame.model_type.eq(kind) & frame.feature_group.eq(group) & frame.staking.eq(staking)]
            if len(one) != 1:
                raise ValueError(f"Expected one pooled strategy: {kind}/{group}/{staking}")
            rows.append(one.iloc[0])
    return pd.DataFrame(rows).reset_index(drop=True)


def _legend():
    return [Line2D([], [], linestyle="none", marker=marker, color=color,
                   markersize=6, label=name) for name, _, marker, color in STAKING.values()]


def _save(fig, output, name):
    for extension in ("png", "svg"):
        path = output / (name + "." + extension)
        if path.exists():
            raise FileExistsError(f"Refusing to overwrite figure: {path}")
        fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def _overview(frame, output):
    fig, axes = plt.subplots(1, 3, sharey=True, figsize=(17, 11.3),
                             gridspec_kw={"width_ratios": [1.65, 1, 1]})
    positions = np.arange(len(frame))
    labels = [_pair_name(row.model_type, row.feature_group) + " | " + STAKING[row.staking][0]
              for row in frame.itertuples()]
    for ax in axes:
        for pair in range(11):
            if pair % 2 == 0:
                ax.axhspan(pair * 2 - 0.5, pair * 2 + 1.5, color="#f2f4f5", zorder=0)
        ax.grid(axis="x", color="#dde1e3", linewidth=0.6)
        ax.set_axisbelow(True)
        ax.xaxis.set_major_formatter(PercentFormatter(1, decimals=0))
        ax.set_ylim(len(frame) - 0.5, -0.5)
        ax.tick_params(axis="y", length=0)
    axes[0].axvline(0, color="#42484c", linewidth=0.9, zorder=1)
    for index, row in frame.iterrows():
        _, _, marker, color = STAKING[row.staking]
        low, high = row.roi_ci_low, row.roi_ci_high
        if not np.isfinite([row.roi, low, high, row.hit_ratio, row.trading_frequency]).all():
            raise ValueError("Overview requires finite recorded metrics and ROI bootstrap intervals")
        axes[0].hlines(index, low, high, color=color, linewidth=1.2, zorder=2)
        axes[0].vlines([low, high], index - 0.1, index + 0.1, color=color, linewidth=0.8)
        axes[0].scatter(row.roi, index, marker=marker, s=27, color=color, zorder=3)
        axes[1].scatter(row.hit_ratio, index, marker=marker, s=27, color=color, zorder=3)
        axes[2].scatter(row.trading_frequency, index, marker=marker, s=27, color=color, zorder=3)
    axes[0].set_yticks(positions, labels, fontsize=9)
    axes[0].set_title("Realized ROI and 95% date-bootstrap CI", loc="left", pad=13)
    axes[1].set_title("Hit ratio", loc="left", pad=13)
    axes[2].set_title("Trading frequency", loc="left", pad=13)
    axes[0].set_xlabel("Net profit / total stake")
    axes[1].set_xlabel("Winning bets / recorded bets")
    axes[2].set_xlabel("Recorded bets / priced fixtures")
    axes[0].set_xlim(min(-0.05, frame.roi_ci_low.min() - 0.035), frame.roi_ci_high.max() + 0.035)
    axes[1].set_xlim(0, max(0.4, frame.hit_ratio.max() + 0.05))
    axes[2].set_xlim(0, 1.04)
    fig.suptitle("Exploratory EPL source ablation: all 22 strategies, with separate season bankroll resets",
                 fontsize=15, x=0.04, ha="left", y=0.985)
    fig.text(0.04, 0.948, "2022–23 through 2025–26 | fixed 5% edge rule | archived best individual-book preclosing prices",
             fontsize=11, color="#40484e")
    fig.legend(handles=_legend(), loc="lower left", bbox_to_anchor=(0.04, 0.061), ncol=2, frameon=False)
    fig.text(0.04, 0.04, "Intervals resample whole calendar dates within each season (1,000 draws), conditional on the fitted models and recorded stakes.", fontsize=9)
    fig.text(0.04, 0.021, "Initial capital is 1,000 per season. Comparisons are descriptive, with no multiplicity adjustment; prices and execution are unverified.", fontsize=9)
    fig.subplots_adjust(left=0.355, right=0.985, top=0.9, bottom=0.135, wspace=0.2)
    _save(fig, output, "ablation_strategy_overview")


def _spread_labels(ax, points):
    """Place short strategy codes deterministically, retaining every point."""
    ax.figure.canvas.draw()
    occupied = []
    box = ax.get_window_extent()
    centres = [ax.transData.transform((point[0], point[1])) for point in points]
    offsets = [(dx, dy) for radius in (12, 22, 34, 48, 65)
               for dx, dy in ((radius, radius / 2), (-radius, radius / 2),
                              (radius, -radius / 2), (-radius, -radius / 2),
                              (0, radius), (0, -radius), (radius, 0), (-radius, 0))]
    for (x, y, text, color), centre in zip(points, centres):
        candidates = []
        width, height = 21 + 4 * max(0, len(text) - 2), 15
        for dx, dy in offsets:
            candidate = [centre[0] + dx - width / 2, centre[1] + dy - height / 2,
                         centre[0] + dx + width / 2, centre[1] + dy + height / 2]
            overlap = sum(max(0, min(candidate[2], old[2]) - max(candidate[0], old[0])) *
                          max(0, min(candidate[3], old[3]) - max(candidate[1], old[1])) for old in occupied)
            crossing = sum(candidate[0] - 3 < point[0] < candidate[2] + 3 and
                           candidate[1] - 3 < point[1] < candidate[3] + 3 for point in centres)
            outside = candidate[0] < box.x0 + 2 or candidate[2] > box.x1 - 2 or candidate[1] < box.y0 + 2 or candidate[3] > box.y1 - 2
            cost = dx * dx + dy * dy + 150 * overlap + 1200 * crossing + 1e8 * outside
            candidates.append((cost, dx, dy, candidate))
        _, dx, dy, rectangle = min(candidates, key=lambda item: item[0])
        occupied.append(rectangle)
        ax.annotate(text, (x, y), xytext=(dx * 72 / ax.figure.dpi, dy * 72 / ax.figure.dpi),
                    textcoords="offset points", ha="center", va="center", fontsize=8, color=color,
                    bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.85, "pad": 0.5},
                    arrowprops={"arrowstyle": "-", "color": "#8d959b", "lw": 0.45, "shrinkA": 2, "shrinkB": 3})


def _roi_panel(ax, rows, pairs, name, *, first=False):
    points, keys = [], []
    for index, pair in enumerate(pairs, start=1):
        if first:
            branch, odds_mode = pair
            part = rows.loc[rows.branch.eq(branch) & rows.odds_mode.eq(odds_mode)]
            family = part.family.iloc[0].upper()
            key = f"{index}: {branch.capitalize()} ({family}), " + ("best book" if odds_mode == "best_individual_book" else "Bet365")
        else:
            kind, group = pair
            part = rows.loc[rows.model_type.eq(kind) & rows.feature_group.eq(group)]
            key = f"{index}: " + _pair_name(kind, group)
        if len(part) != 2 or set(part.staking) != {"fixed", "kelly"}:
            raise ValueError("ROI comparison requires both staking alternatives per declared model/price pair")
        keys.append(key)
        part = part.set_index("staking").loc[["fixed", "kelly"]]
        ax.plot(part.expected_roi, part.roi, color="#c2c7cb", linewidth=0.7, zorder=1)
        for staking, row in part.iterrows():
            _, code, marker, color = STAKING[staking]
            ax.scatter(row.expected_roi, row.roi, s=32, marker=marker, color=color, zorder=3)
            points.append((row.expected_roi, row.roi, str(index) + code, color))
    values = rows[["expected_roi", "roi"]].to_numpy(float)
    if not np.isfinite(values).all():
        raise ValueError("ROI comparison requires finite expected and realized ROI")
    low, high = min(-0.03, values.min()), max(0.1, values.max())
    margin = (high - low) * 0.13
    ax.set_xlim(low - margin, high + margin)
    ax.set_ylim(low - margin, high + margin)
    ax.set_aspect("equal", adjustable="box")
    ax.plot([low - margin, high + margin], [low - margin, high + margin],
            linestyle="--", color="#67727c", linewidth=0.9, zorder=0)
    ax.axhline(0, color="#d3d9dd", linewidth=0.7, zorder=0)
    ax.set_title(name, loc="left", pad=11)
    ax.set_xlabel("Model-implied ROI on recorded stakes")
    ax.set_ylabel("Realized ROI on recorded stakes")
    ax.xaxis.set_major_formatter(PercentFormatter(1, decimals=0))
    ax.yaxis.set_major_formatter(PercentFormatter(1, decimals=0))
    ax.grid(color="#e6e9eb", linewidth=0.5)
    _spread_labels(ax, points)
    return keys


def _expectation_comparison(first, pooled, output):
    fig = plt.figure(figsize=(17.5, 10.8))
    layout = fig.add_gridspec(2, 3, height_ratios=[3.4, 1.15], hspace=0.22, wspace=0.29,
                             left=0.065, right=0.985, top=0.86, bottom=0.15)
    panels = [fig.add_subplot(layout[0, index]) for index in range(3)]
    first_pairs = [(branch, book) for branch in ("accuracy", "calibration")
                   for book in ("best_individual_book", "bet365_reference")]
    fitted_pairs = POOLED_ORDER[:8]
    benchmark_pairs = POOLED_ORDER[8:]
    keys = [_roi_panel(panels[0], first, first_pairs, "First study: eight 2025–26 test variants", first=True),
            _roi_panel(panels[1], pooled.loc[pooled.model_type.isin(["logistic", "market_residual"])],
                       fitted_pairs, "Exploratory ablation: 16 fitted variants"),
            _roi_panel(panels[2], pooled.loc[~pooled.model_type.isin(["logistic", "market_residual"])],
                       benchmark_pairs, "Exploratory ablation: six benchmark variants")]
    for index, lines in enumerate(keys):
        key_ax = fig.add_subplot(layout[1, index])
        key_ax.axis("off")
        key_ax.text(0, 1, "\n".join(lines), va="top", ha="left", fontsize=9, linespacing=1.4)
    fig.suptitle("Model-implied versus realized ROI: every declared 5% strategy alternative",
                 fontsize=15, x=0.04, ha="left", y=0.982)
    fig.text(0.04, 0.946, "Ablation pools four seasons with 1,000 initial capital per season; all strategies retain their recorded stakes.", fontsize=11)
    fig.text(0.04, 0.914, "Dashed line: realized ROI = model-implied ROI. Gray segments connect fixed and quarter-Kelly alternatives; each panel has its own scale.", fontsize=9)
    fig.legend(handles=_legend(), loc="lower left", bbox_to_anchor=(0.04, 0.091), ncol=2, frameon=False)
    fig.text(0.04, 0.07, "Codes F/K identify staking alternatives; numbered keys retain all eight first-study and all 22 pooled ablation rows.", fontsize=9)
    fig.text(0.04, 0.047, "Model-implied ROI = Σ stake × (probability × decimal odds − 1) / Σ stake: conditional on allocated stakes, not predicted terminal wealth.", fontsize=9)
    fig.text(0.04, 0.024, "These are retrospective archived-price results. The ablation is exploratory; 2025–26 was already examined. No executed returns or selected winner are claimed.", fontsize=9)
    _save(fig, output, "expected_vs_realized_roi")


def build_charts(results: Path, *, output_dir: Path | None = None) -> dict:
    results = Path(results).resolve()
    output = Path(output_dir).resolve() if output_dir else results / "figures"
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite an existing figure directory: {output}")
    if output == results or results not in output.parents:
        raise ValueError("New figures must be written inside the existing analytics directory")
    source, manifest_path = results / "strategy_metrics.parquet", results / "audit_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    source_hash = _sha(source)
    if source_hash != manifest["tables"]["strategy_metrics"]["parquet_sha256"]:
        raise ValueError("Strategy source hash differs from the preserved analytics manifest")
    preserved = {path.name: _sha(path) for path in results.iterdir() if path.is_file()}
    frame = pd.read_parquet(source)
    pooled = _ordered_pooled(frame.loc[frame.study.eq("ablation") & frame.scope.eq("pooled_seasons")])
    first = frame.loc[frame.study.eq("first") & frame.scope.eq("test") & frame.policy.eq("predeclared_5pct")].copy()
    if len(frame) != 172 or len(pooled) != 22 or len(first) != 8:
        raise ValueError("Figures require the preserved 172-row universe with 22 pooled and eight first-study 5% test alternatives")
    if not pooled.policy.eq("predeclared_5pct").all() or not pooled.bankroll_reset_episodes.eq(4).all():
        raise ValueError("Pooled figure scope conflicts with fixed-policy/four-season resets")
    if not pooled.bootstrap_samples.eq(1000).all():
        raise ValueError("Figure confidence-interval label requires the saved 1,000-draw bootstrap")
    output.mkdir(parents=True, exist_ok=False)
    with plt.rc_context(STYLE):
        _overview(pooled, output)
        _expectation_comparison(first, pooled, output)
    if any(_sha(results / name) != digest for name, digest in preserved.items()):
        raise ValueError("An existing analytics file changed during chart rendering")
    metadata = {"created_at_utc": datetime.now(timezone.utc).isoformat(), "results_directory": str(results),
                "figures_directory": str(output), "source_sha256": source_hash,
                "existing_analytics_files_unchanged": True,
                "overview_strategy_ids": pooled.strategy_id.tolist(),
                "roi_comparison_strategy_ids": first.strategy_id.tolist() + pooled.strategy_id.tolist(),
                "overview_rows": 22, "roi_comparison_rows": 30,
                "files": {path.name: {"sha256": _sha(path), "bytes": path.stat().st_size}
                          for path in sorted(output.iterdir()) if path.is_file()},
                "notes": ["Every declared strategy is retained; ordering is by model/source group, not measured performance.",
                          "Pooled capital resets to 1000 each season. ROI is total net profit divided by total stake.",
                          "ROI intervals condition on recorded models and stakes and resample dates within season.",
                          "Expected ROI is conditional on allocated stakes and is not an estimate of expected terminal wealth.",
                          "Ablation is exploratory, multiple comparisons are descriptive, and executable prices are unverified."]}
    with (output / "figure_manifest.json").open("x", encoding="utf-8") as handle:
        json.dump(metadata, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    return {"figures_directory": str(output), "overview_rows": 22, "roi_comparison_rows": 30,
            "files": list(metadata["files"]), "existing_analytics_files_unchanged": True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, help="New subdirectory inside --results; existing paths are refused")
    args = parser.parse_args()
    print(json.dumps(build_charts(args.results, output_dir=args.output_dir), indent=2))


if __name__ == "__main__":
    main()
