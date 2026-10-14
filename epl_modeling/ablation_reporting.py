"""Present saved retrospective EPL ablations without fitting or selecting models.

Only ``ablation_results``-style output artifacts and the new 03 notebook are
written. The original experiment's results directory is explicitly protected.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import nbformat
from nbclient import NotebookClient
import numpy as np
import pandas as pd
from openpyxl.styles import Font, PatternFill


PERFORMANCE_GROUPS = ("team", "team_xg", "team_player", "combined")
MODEL_TYPES = ("logistic", "market_residual")
GROUP_LABELS = {"team": "Team", "team_xg": "Team + xG", "team_player": "Team + players",
                "combined": "Combined", "market_only": "Market", "class_frequency": "Class frequency"}
MODEL_LABELS = {"logistic": "Logistic", "market_residual": "Market residual", "baseline": "Baseline",
                "market_temperature": "Market temperature"}
COLORS = {"team": "#245889", "team_xg": "#087F83", "team_player": "#BE7918", "combined": "#7851A9"}
METRICS = ("accuracy", "classwise_ece_10", "log_loss", "brier_score")
SCORE_KEYS = ["outer_season", "scope", "feature_group", "model_type"]


def _read_table(output: Path, name: str, *, required: bool = True) -> pd.DataFrame:
    parquet, csv = output / f"{name}.parquet", output / f"{name}.csv"
    if parquet.exists():
        return pd.read_parquet(parquet)
    if csv.exists():
        try:
            return pd.read_csv(csv, low_memory=False)
        except pd.errors.EmptyDataError:
            return pd.DataFrame()
    if required:
        raise FileNotFoundError(f"Missing ablation input: {name}.csv or {name}.parquet")
    return pd.DataFrame()


def _read_json(output: Path, name: str) -> dict:
    path = output / f"{name}.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def _need(frame: pd.DataFrame, columns, name: str) -> None:
    missing = set(columns) - set(frame)
    if missing:
        raise ValueError(f"{name} is missing columns: {sorted(missing)}")


def _variant(group: str, kind: str) -> str:
    if group == "market_only":
        return "Temperature-only market" if kind == "market_temperature" else "Raw market"
    if group == "class_frequency":
        return "Class frequency"
    return f"{MODEL_LABELS.get(kind, kind)}: {GROUP_LABELS.get(group, group)}"


def _table(frame: pd.DataFrame, *, digits: int = 4) -> str:
    if frame.empty:
        return "No qualifying rows are available."
    def cell(value):
        if isinstance(value, (dict, list, tuple)):
            value = json.dumps(value, default=str)
        if pd.isna(value):
            return "—"
        if isinstance(value, (float, np.floating)):
            return f"{value:.{digits}f}" if np.isfinite(value) else str(value)
        return str(value).replace("|", "\\|").replace("\n", " ")
    lines = ["| " + " | ".join(map(str, frame.columns)) + " |",
             "| " + " | ".join("---" for _ in frame.columns) + " |"]
    lines.extend("| " + " | ".join(cell(value) for value in row) + " |"
                 for row in frame.itertuples(index=False, name=None))
    return "\n".join(lines)


def _flatten(value, *, prefix="", max_rows=2000) -> pd.DataFrame:
    """Compact JSON inspection table; original JSON remains authoritative."""
    rows = []
    def visit(item, key, depth):
        if len(rows) >= max_rows:
            return
        if isinstance(item, dict) and depth < 7:
            for name, child in item.items():
                visit(child, f"{key}.{name}" if key else str(name), depth + 1)
        elif isinstance(item, list):
            text = json.dumps(item, ensure_ascii=False, default=str)
            if len(text) > 2000:
                text = json.dumps(item[:10], ensure_ascii=False, default=str) + f" … ({len(item)} items; see JSON)"
            rows.append({"field": key, "value": text})
        else:
            rows.append({"field": key, "value": item})
    visit(value, prefix, 0)
    if len(rows) >= max_rows:
        rows.append({"field": "inspection_limit", "value": "See the complete original JSON for remaining fields."})
    return pd.DataFrame(rows, columns=["field", "value"])


def _validate_inputs(scores, predictions, betting, pairs) -> None:
    _need(scores, SCORE_KEYS + ["n_matches", *METRICS], "classification_scores")
    _need(predictions, ["match_id", "match_date", "season", "result", "p_H", "p_D", "p_A",
                        "feature_group", "model_type", "outer_season"], "predictions")
    _need(betting, ["outer_season", "feature_group", "model_type", "policy", "odds_mode", "staking",
                    "bet_count", "profit", "turnover", "roi", "roi_ci_low", "roi_ci_high", "max_drawdown"], "betting_summary")
    if scores.empty or predictions.empty:
        raise ValueError("Ablation reporting requires nonempty completed scores and predictions")
    if scores.duplicated(SCORE_KEYS).any():
        raise ValueError("Duplicate ablation score keys")
    pk = ["outer_season", "feature_group", "model_type", "match_id"]
    if predictions.duplicated(pk).any():
        raise ValueError("Duplicate fixture predictions within an ablation variant")
    if predictions[["outer_season", "match_id", "match_date", "season", "result"]].isna().any().any():
        raise ValueError("Ablation fixture identities, dates and settlement labels must be present")
    agreement = ["match_date", "season", "result"]
    if "complete_source_history" in predictions:
        agreement.append("complete_source_history")
    if predictions.groupby(["outer_season", "match_id"])[agreement].nunique(dropna=False).gt(1).any().any():
        raise ValueError("Variants disagree on fixture identity, settlement or shared source-history eligibility")
    p = predictions[["p_H", "p_D", "p_A"]].to_numpy(float)
    if not np.isfinite(p).all() or (p < 0).any() or (p > 1).any() or not np.allclose(p.sum(axis=1), 1, atol=1e-8, rtol=1e-8):
        raise ValueError("Invalid ablation probabilities; expected normalized H/D/A vectors")
    if not predictions.result.isin(["H", "D", "A"]).all():
        raise ValueError("Unknown football result label")
    if not betting.empty:
        if not betting.policy.eq("predeclared_5pct").all() or not betting.odds_mode.eq("best_individual_book").all():
            raise ValueError("This ablation report expects only the fixed 5% best-individual-book policy")
        if not betting.staking.isin(["fixed", "kelly"]).all():
            raise ValueError("Unknown staking rule in ablation summaries")
        if betting.duplicated(["outer_season", "feature_group", "model_type", "policy", "odds_mode", "staking"]).any():
            raise ValueError("Duplicate betting summaries would double-count pooled cashflows")
    for season, one in predictions.groupby("outer_season", sort=False):
        sets = [set(part.match_id) for _, part in one.groupby(["feature_group", "model_type"], sort=False)]
        if any(ids != sets[0] for ids in sets[1:]):
            raise ValueError(f"Variants do not share the same common-odds fixture IDs in {season}")
    for (season, scope), one in scores.groupby(["outer_season", "scope"], sort=False):
        if one.n_matches.nunique() != 1:
            raise ValueError(f"Variant-dependent sample sizes in {season}/{scope}; comparisons would be misleading")
    if not pairs.empty:
        _need(pairs, ["outer_season", "scope", "feature_group", "model_type", "reference_group",
                      "metric", "difference", "ci_lower", "ci_upper", "n_matches"], "paired_comparisons")
    common = scores.loc[scores.scope.eq("common_odds_matches")]
    for row in common.itertuples(index=False):
        one = predictions.loc[predictions.feature_group.eq(row.feature_group) & predictions.model_type.eq(row.model_type)]
        if str(row.outer_season) != "pooled":
            one = one.loc[one.outer_season.astype(str).eq(str(row.outer_season))]
        if len(one) != int(row.n_matches):
            raise ValueError(f"Score/prediction support mismatch for {row.outer_season}/{row.feature_group}/{row.model_type}")
    if "complete_source_history" in predictions:
        eligible = predictions.complete_source_history
        if eligible.dtype != bool:
            eligible = eligible.astype(str).str.lower().map({"true": True, "false": False, "1": True, "0": False})
            if eligible.isna().any():
                raise ValueError("Invalid complete-source-history eligibility flag")
        for row in scores.loc[scores.scope.eq("complete_source_history")].itertuples(index=False):
            mask = eligible & predictions.feature_group.eq(row.feature_group) & predictions.model_type.eq(row.model_type)
            if str(row.outer_season) != "pooled":
                mask &= predictions.outer_season.astype(str).eq(str(row.outer_season))
            if int(mask.sum()) != int(row.n_matches):
                raise ValueError("Complete-history sensitivity scores do not match the shared eligibility flag")


def _pooled_scores(scores, scope="common_odds_matches") -> pd.DataFrame:
    # Pooled ECE must come from all pooled probabilities, not averaged seasonal ECEs.
    pooled = scores.loc[scores.outer_season.astype(str).eq("pooled") & scores.scope.eq(scope)].copy()
    if not pooled.empty:
        pooled["variant"] = [_variant(g, k) for g, k in zip(pooled.feature_group, pooled.model_type)]
    return pooled.sort_values(["log_loss", "brier_score", "variant"]) if not pooled.empty else pooled


def _pooled_betting(betting) -> pd.DataFrame:
    rows = []
    for (group, kind, staking), part in betting.groupby(["feature_group", "model_type", "staking"], sort=False):
        turnover, profit = float(part.turnover.sum()), float(part.profit.sum())
        rows.append({"feature_group": group, "model_type": kind, "variant": _variant(group, kind),
                     "staking": staking, "outer_seasons": int(part.outer_season.nunique()),
                     "bet_count": int(part.bet_count.sum()), "profit": profit, "turnover": turnover,
                     "roi": profit / turnover if turnover > 0 else np.nan})
    return pd.DataFrame(rows)


def _findings(scores, pairs, betting) -> list[str]:
    pooled = _pooled_scores(scores)
    common = scores.loc[scores.scope.eq("common_odds_matches") & ~scores.outer_season.astype(str).eq("pooled")]
    seasons = sorted(common.outer_season.astype(str).unique())
    lines = [f"The retrospective evaluation covers {len(seasons)} outer seasons ({', '.join(seasons)}). "
             "All variants use the same eligible quoted-price fixtures in each season."]
    if not pooled.empty:
        best = pooled.iloc[0]
        lines.append(f"The lowest observed pooled log loss is **{best.log_loss:.4f}** for **{best.variant}** "
                     f"over {int(best.n_matches):,} matches. This is a descriptive ranking of already inspected history, "
                     "not a newly selected production model or a fresh holdout result.")
        for kind in MODEL_TYPES:
            one = pooled.loc[pooled.model_type.eq(kind) & pooled.feature_group.isin(PERFORMANCE_GROUPS)].set_index("feature_group")
            if "team" not in one.index:
                continue
            values = []
            for group in PERFORMANCE_GROUPS[1:]:
                if group in one.index:
                    difference = float(one.loc[group, "log_loss"] - one.loc["team", "log_loss"])
                    values.append(f"{GROUP_LABELS[group]} **{difference:+.4f}**")
            if values:
                lines.append(f"Within {MODEL_LABELS[kind]}, pooled log-loss changes versus Team are " + "; ".join(values)
                             + ". Negative means lower loss. All groups also share source-coverage controls.")
        calibrated = pooled.loc[pooled.feature_group.eq("market_only") & pooled.model_type.eq("market_temperature")]
        residual = pooled.loc[pooled.model_type.eq("market_residual")]
        if not calibrated.empty and not residual.empty:
            best_residual = residual.sort_values("log_loss").iloc[0]
            delta = float(best_residual.log_loss - calibrated.iloc[0].log_loss)
            lines.append(f"The lowest-loss residual variant changes pooled log loss by **{delta:+.4f}** versus the "
                         "temperature-only market baseline. This comparison helps separate added historical features "
                         "from improvement attributable solely to recalibrating bookmaker probabilities.")
    if not pairs.empty:
        player = pairs.loc[pairs.outer_season.astype(str).eq("pooled") & pairs.scope.eq("common_odds_matches")
                           & pairs.feature_group.eq("team_player") & pairs.reference_group.eq("team") & pairs.metric.eq("log_loss")].copy()
        if "reference_model_type" in player:
            player = player.loc[player.reference_model_type.eq(player.model_type)]
        finite = player.loc[np.isfinite(pd.to_numeric(player.ci_lower, errors="coerce"))
                            & np.isfinite(pd.to_numeric(player.ci_upper, errors="coerce"))]
        if not finite.empty:
            crossing = int((finite.ci_lower.le(0) & finite.ci_upper.ge(0)).sum())
            below = int(finite.ci_upper.lt(0).sum())
            lines.append(f"Of {len(finite)} pooled player-versus-team conditional log-loss intervals, "
                         f"{crossing} include zero and {below} lie entirely below zero. "
                         "These exploratory intervals are not adjusted for multiple comparisons and omit fitting/selection uncertainty.")
    pooled_bets = _pooled_betting(betting)
    fixed = pooled_bets.loc[pooled_bets.staking.eq("fixed") & pooled_bets.roi.notna()] if not pooled_bets.empty else pd.DataFrame()
    if not fixed.empty:
        lines.append(f"Across fixed-stake variants, pooled archived profit/turnover ranges from "
                     f"**{fixed.roi.min():+.2%} to {fixed.roi.max():+.2%}**. Capital resets in each outer season; "
                     "these are descriptive combinations of separate replays, not a continuous investment track record.")
    interval = betting[["roi_ci_low", "roi_ci_high"]].apply(pd.to_numeric, errors="coerce")
    if not np.isfinite(interval.to_numpy()).any():
        lines.append("**Betting ROI uncertainty was not estimated in this run.** Empty interval columns do not mean "
                     "precise returns or zero uncertainty. Positive historical point estimates cannot establish a reliable betting edge.")
    else:
        lines.append("Any supplied betting ROI intervals are conditional historical summaries. No pooled betting interval "
                     "is created by averaging their endpoints, and no synchronized execution or profitable edge is established.")
    return lines


def _save_figure(fig, output, stem):
    for extension in ("png", "svg"):
        fig.savefig(output / f"{stem}.{extension}", bbox_inches="tight", dpi=300, facecolor="white")
    plt.close(fig)


def _plot_series(ax, rows, metric, seasons, kind):
    x = np.arange(len(seasons))
    for group in PERFORMANCE_GROUPS:
        one = rows.loc[rows.model_type.eq(kind) & rows.feature_group.eq(group)].set_index("outer_season")
        values = one[metric].reindex(seasons).to_numpy(float)
        ax.plot(x, values, marker="o", color=COLORS[group], linewidth=1.8, markersize=4, label=GROUP_LABELS[group])
    for group, model, label, color, style in [
        ("market_only", "baseline", "Raw market", "#5B6875", "--"),
        ("market_only", "market_temperature", "Temperature-only market", "#152E40", "-."),
        ("class_frequency", "baseline", "Class frequency", "#96989D", ":")]:
        one = rows.loc[rows.feature_group.eq(group) & rows.model_type.eq(model)].set_index("outer_season")
        if not one.empty:
            ax.plot(x, one[metric].reindex(seasons).to_numpy(float), color=color, linestyle=style,
                    linewidth=1.3, marker=".", label=label)
    ax.set_xticks(x, [s.replace("-", "/") for s in seasons])
    ax.grid(alpha=0.18)


def _build_figures(output, scores, pairs, betting) -> list[str]:
    common = scores.loc[scores.scope.eq("common_odds_matches") & ~scores.outer_season.astype(str).eq("pooled")].copy()
    common["outer_season"] = common.outer_season.astype(str)
    seasons = sorted(common.outer_season.unique())
    files = []
    with plt.rc_context({"font.size": 10, "figure.dpi": 120, "axes.spines.top": False,
                         "axes.spines.right": False, "svg.fonttype": "none"}):
        fig, axes = plt.subplots(2, 2, figsize=(12, 7), squeeze=False)
        for row, kind in enumerate(MODEL_TYPES):
            for col, (metric, ylabel) in enumerate([("log_loss", "Log loss"), ("brier_score", "Multiclass Brier [0, 2]")]):
                _plot_series(axes[row, col], common, metric, seasons, kind)
                axes[row, col].set(title=MODEL_LABELS[kind], ylabel=ylabel, xlabel="Outer evaluation season")
        handles, labels = axes[0, 0].get_legend_handles_labels()
        fig.legend(handles, labels, loc="lower center", ncol=4, fontsize=8, frameon=False)
        fig.suptitle("Retrospective rolling ablations: probability quality (lower is better)")
        fig.tight_layout(rect=(0, 0.09, 1, 0.95))
        _save_figure(fig, output, "ablation_probability_quality")
        files.append("ablation_probability_quality")

        fig, axes = plt.subplots(1, 2, figsize=(12, 4.3), squeeze=False)
        scaled = common.copy()
        scaled["classwise_ece_10"] *= 100
        for ax, kind in zip(axes[0], MODEL_TYPES):
            _plot_series(ax, scaled, "classwise_ece_10", seasons, kind)
            ax.set(title=MODEL_LABELS[kind], ylabel="10-bin classwise ECE (%)", xlabel="Outer evaluation season")
            ax.set_ylim(bottom=0)
        handles, labels = axes[0, 0].get_legend_handles_labels()
        fig.legend(handles, labels, loc="lower center", ncol=4, fontsize=8, frameon=False)
        fig.suptitle("Calibration error: fixed bins, common quoted-price fixtures")
        fig.tight_layout(rect=(0, 0.14, 1, 0.93))
        _save_figure(fig, output, "ablation_calibration_error")
        files.append("ablation_calibration_error")

        if not pairs.empty:
            selected = pairs.loc[pairs.scope.eq("common_odds_matches") & pairs.metric.eq("log_loss")
                                 & pairs.reference_group.eq("team") & pairs.feature_group.isin(PERFORMANCE_GROUPS[1:])
                                 & ~pairs.outer_season.astype(str).eq("pooled")].copy()
            if "reference_model_type" in selected:
                selected = selected.loc[selected.reference_model_type.eq(selected.model_type)]
            if not selected.empty:
                height = max(4.4, 0.34 * max(len(selected.loc[selected.model_type.eq(k)]) for k in MODEL_TYPES) + 2.0)
                fig, axes = plt.subplots(1, 2, figsize=(13, height), squeeze=False)
                for ax, kind in zip(axes[0], MODEL_TYPES):
                    one = selected.loc[selected.model_type.eq(kind)].sort_values(["outer_season", "feature_group"])
                    labels = []
                    for y, row in enumerate(one.itertuples(index=False)):
                        color = COLORS.get(row.feature_group, "#5B6875")
                        lo, hi, difference = float(row.ci_lower), float(row.ci_upper), float(row.difference)
                        if np.isfinite(lo) and np.isfinite(hi):
                            ax.hlines(y, lo, hi, color=color, linewidth=1.7)
                        ax.scatter(difference, y, color=color, s=25, zorder=3)
                        labels.append(f"{row.outer_season} · {GROUP_LABELS.get(row.feature_group, row.feature_group)}")
                    ax.axvline(0, color="#63717B", linestyle="--", linewidth=1)
                    ax.set_yticks(np.arange(len(labels)), labels, fontsize=8)
                    ax.invert_yaxis()
                    ax.set(title=MODEL_LABELS[kind], xlabel="Log-loss difference vs same-kind Team; negative is lower")
                    ax.grid(axis="x", alpha=0.15)
                fig.suptitle("Conditional paired date-bootstrap intervals; retrospective, no multiplicity adjustment")
                fig.tight_layout(rect=(0, 0, 1, 0.94))
                _save_figure(fig, output, "ablation_paired_logloss")
                files.append("ablation_paired_logloss")

        pooled_bets = _pooled_betting(betting)
        if not pooled_bets.empty:
            order = sorted(pooled_bets.variant.unique(), key=lambda name: (name in {"Raw market", "Temperature-only market", "Class frequency"}, name))
            fig, axes = plt.subplots(1, 2, figsize=(13, max(5, 0.36 * len(order) + 2)), sharey=True, squeeze=False)
            for ax, staking in zip(axes[0], ["fixed", "kelly"]):
                one = pooled_bets.loc[pooled_bets.staking.eq(staking)].set_index("variant").reindex(order)
                values = one.roi.to_numpy(float) * 100
                colors = [COLORS.get(group, "#74808C") for group in one.feature_group]
                ax.barh(np.arange(len(order)), values, color=colors, height=0.7)
                for i, value in enumerate(values):
                    if not np.isfinite(value):
                        ax.text(0, i, "no stakes", va="center", fontsize=8)
                ax.axvline(0, color="#475569", linewidth=1)
                ax.set(title="Fixed stakes" if staking == "fixed" else "Quarter Kelly; 2% per-bet cap",
                       xlabel="Pooled archived profit / turnover (%)")
                ax.grid(axis="x", alpha=0.15)
            axes[0, 0].set_yticks(np.arange(len(order)), order, fontsize=8)
            axes[0, 0].invert_yaxis()
            fig.suptitle("Exploratory 5% policy; capital resets each season; no pooled betting intervals")
            fig.tight_layout(rect=(0, 0, 1, 0.94))
            _save_figure(fig, output, "ablation_betting_roi")
            files.append("ablation_betting_roi")

        support = scores.loc[~scores.outer_season.astype(str).eq("pooled")].groupby(["outer_season", "scope"]).n_matches.first().unstack("scope")
        if "common_odds_matches" in support:
            support = support.reindex(seasons)
            x = np.arange(len(support))
            fig, ax = plt.subplots(figsize=(8, 4))
            ax.bar(x, support.common_odds_matches, color="#BCC8D2", width=0.65, label="Common quoted-price sample")
            complete = support.get("complete_source_history", pd.Series(0, index=support.index)).fillna(0)
            ax.bar(x, complete, color="#087F83", width=0.4, label="Same complete-source intersection for every variant")
            for i, (n, total) in enumerate(zip(complete, support.common_odds_matches)):
                ax.text(i, float(total) + 4, f"{int(n)}/{int(total)}", ha="center", fontsize=9)
            ax.set_xticks(x, [s.replace("-", "/") for s in seasons])
            ax.set(ylabel="Eligible outer-season fixtures", xlabel="Outer evaluation season",
                   title="Source-history sensitivity: both clubs ≥8 observed slots in prior 10")
            ax.set_ylim(0, support.common_odds_matches.max() * 1.16)
            ax.legend(fontsize=8, loc="lower left")
            ax.grid(axis="y", alpha=0.15)
            fig.tight_layout()
            _save_figure(fig, output, "ablation_history_coverage")
            files.append("ablation_history_coverage")
    return files


def _safe_excel(frame):
    frame = frame.copy()
    for name in frame:
        if frame[name].dtype == object or pd.api.types.is_string_dtype(frame[name]):
            def safe(value):
                if isinstance(value, (dict, list, tuple, np.ndarray)):
                    value = json.dumps(value, ensure_ascii=False, default=str)
                if isinstance(value, str):
                    value = value[:32000] + (" … see original JSON" if len(value) > 32000 else "")
                    if value.startswith(("=", "+", "-", "@")):
                        value = "'" + value
                return value
            frame[name] = frame[name].map(safe)
    return frame


def _build_workbook(output, scores, pairs, betting, roles, trials, groups, reconciliation, metadata, findings):
    overview = pd.DataFrame([{"field": f"finding_{i+1}", "value": text} for i, text in enumerate(findings)])
    keys = ["study_status", "run_date", "data_snapshot_as_of", "cohort", "seasons", "seed", "n_models",
            "n_tuning_trials", "common_sample_matches", "first_experiment_preserved", "limitations"]
    overview = pd.concat([overview, _flatten({key: metadata[key] for key in keys if key in metadata})], ignore_index=True)
    sheets = {"Findings": overview, "Probability scores": scores, "Paired comparisons": pairs,
              "Betting summary": betting, "Chronological roles": roles, "Feature groups": _flatten(groups),
              "Source audit": _flatten(reconciliation), "Tuning trials": trials}
    with pd.ExcelWriter(output / "EPL_feature_ablation.xlsx", engine="openpyxl") as writer:
        for title, frame in sheets.items():
            _safe_excel(frame).to_excel(writer, sheet_name=title, index=False)
            sheet = writer.sheets[title]
            sheet.freeze_panes = "A2"
            sheet.auto_filter.ref = sheet.dimensions
            for cell in sheet[1]:
                cell.font = Font(bold=True, color="FFFFFF")
                cell.fill = PatternFill("solid", fgColor="173B4B")
            for column in sheet.columns:
                texts = [str(cell.value or "") for cell in list(column)[:80]]
                sheet.column_dimensions[column[0].column_letter].width = min(52, max(12, max(map(len, texts)) + 2))


def _build_notebook(output, figure_stems):
    folder = json.dumps(output.name)
    nb = nbformat.v4.new_notebook()
    nb.metadata.kernelspec = {"display_name": "Python 3", "language": "python", "name": "python3"}
    nb.cells = [nbformat.v4.new_markdown_cell(
        "# EPL rolling feature ablations: exploratory retrospective research\n\n"
        "**2025/26 outcomes were inspected in the first experiment. This is not a fresh confirmatory holdout.** "
        "This executed notebook loads saved outputs only: it does not train, tune, calibrate or select a model. "
        "Current-club survivor bias and unverified quote/feature publication times remain. See `ablation_results/ABLATION_RESULTS.md`."),
        nbformat.v4.new_code_cell(
            "from pathlib import Path\nimport json\nimport pandas as pd\nfrom IPython.display import display, Image\n"
            f"folder = {folder}\n"
            "candidates = [Path.cwd()/folder, Path.cwd()/'epl_modeling'/folder, Path.cwd()]\n"
            "RESULTS = next((p for p in candidates if (p/'run_metadata.json').exists() and "
            "((p/'classification_scores.parquet').exists() or (p/'classification_scores.csv').exists())), None)\n"
            "if RESULTS is None:\n    raise FileNotFoundError('Run the ablation experiment first, then open this notebook from epl_modeling or the project root.')\n"
            "def table(name):\n    p=RESULTS/(name+'.parquet')\n    return pd.read_parquet(p) if p.exists() else pd.read_csv(RESULTS/(name+'.csv'))\n"
            "metadata=json.loads((RESULTS/'run_metadata.json').read_text(encoding='utf-8'))\n"
            "display({k:metadata.get(k) for k in ['study_status','run_date','data_snapshot_as_of','seed','common_sample_matches','first_experiment_preserved']})\n"
            "display(table('chronological_roles'))"),
        nbformat.v4.new_markdown_cell("## Pooled probability quality\nLower log loss/Brier are better. Pooled ECE is recomputed from pooled probabilities, not an average of seasonal ECE. All rankings are descriptive."),
        nbformat.v4.new_code_cell(
            "scores=table('classification_scores')\n"
            "display(scores[scores['outer_season'].astype(str).eq('pooled')].sort_values(['scope','log_loss']))\n"
            "display(Image(filename=str(RESULTS/'ablation_probability_quality.png')))\n"
            "display(Image(filename=str(RESULTS/'ablation_calibration_error.png')))"),
        nbformat.v4.new_markdown_cell("## Incremental feature comparisons\nDifferences are candidate minus reference. Conditional date-bootstrap intervals omit fitting/selection uncertainty and are not adjusted for multiple comparisons. ECE comparisons are point estimates only."),
        nbformat.v4.new_code_cell(
            "pairs=table('paired_comparisons')\n"
            "display(pairs[pairs['outer_season'].astype(str).eq('pooled')].reset_index(drop=True))\n"
            + ("display(Image(filename=str(RESULTS/'ablation_paired_logloss.png')))" if "ablation_paired_logloss" in figure_stems else "")),
        nbformat.v4.new_markdown_cell("## Same source-history intersection\nEvery variant shares the complete-history eligibility mask. Both clubs need at least eight observed xG and FPL slots in their ten earlier E0 matches and nonmissing fixed performance inputs. This is an evaluation sensitivity, not a refit."),
        nbformat.v4.new_code_cell(
            "display(scores[scores['scope'].eq('complete_source_history')].reset_index(drop=True))\n"
            + ("display(Image(filename=str(RESULTS/'ablation_history_coverage.png')))\n" if "ablation_history_coverage" in figure_stems else "")
            + "source_audit=json.loads((RESULTS/'source_reconciliation_summary.json').read_text(encoding='utf-8'))\n"
            "print('Full reconciliation fields:', list(source_audit))\n"
            "groups=json.loads((RESULTS/'feature_groups.json').read_text(encoding='utf-8'))\n"
            "display(groups)"),
        nbformat.v4.new_markdown_cell("## Fixed exploratory archived-price policies\nThe 5% expected-return threshold is not newly selected on these results. Fixed stakes and quarter Kelly (2% cap) are hypothetical. Capital resets per outer season. Empty ROI interval columns mean uncertainty was not estimated, not that returns are precise."),
        nbformat.v4.new_code_cell(
            "betting=table('betting_summary')\n"
            "display(betting[['outer_season','feature_group','model_type','staking','bet_count','profit','turnover','roi','roi_ci_low','roi_ci_high','max_drawdown']])\n"
            + ("display(Image(filename=str(RESULTS/'ablation_betting_roi.png')))\n" if "ablation_betting_roi" in figure_stems else "")
            + "display(table('predictions').head(12))"),
        nbformat.v4.new_markdown_cell("## Tuning audit and limits\nPast outer seasons use earlier training/tuning/calibration roles. These chronological controls do not make already inspected history a new untouched test. No prospective predictions or live execution are established."),
        nbformat.v4.new_code_cell("display(table('tuning_trials').head(30))\nprint('Run limitations:',metadata.get('limitations',[]))")]
    NotebookClient(nb, timeout=120, kernel_name="python3", resources={"metadata": {"path": str(output.parent)}}).execute()
    nbformat.write(nb, output.parent / "03_epl_feature_ablation.ipynb")


def build_ablation_report(output: Path) -> None:
    """Build outcome-led artifacts from completed ablation outputs; never refit."""
    output = Path(output).resolve()
    original = (Path(__file__).resolve().parent / "results").resolve()
    if output == original or original in output.parents:
        raise ValueError("The first experiment results are immutable; use a separate ablation directory")
    output.mkdir(parents=True, exist_ok=True)
    scores = _read_table(output, "classification_scores")
    predictions = _read_table(output, "predictions")
    pairs = _read_table(output, "paired_comparisons")
    betting = _read_table(output, "betting_summary")
    roles = _read_table(output, "chronological_roles")
    trials = _read_table(output, "tuning_trials")
    groups = _read_json(output, "feature_groups")
    reconciliation = _read_json(output, "source_reconciliation_summary")
    metadata = _read_json(output, "run_metadata")
    _validate_inputs(scores, predictions, betting, pairs)
    findings = _findings(scores, pairs, betting)
    figures = _build_figures(output, scores, pairs, betting)
    pooled = _pooled_scores(scores)
    complete = _pooled_scores(scores, "complete_source_history")
    paired_pooled = pairs.loc[pairs.outer_season.astype(str).eq("pooled") & pairs.scope.eq("common_odds_matches")].copy()
    pooled_bets = _pooled_betting(betting)
    score_cols = ["variant", "n_matches", *METRICS]
    pair_cols = ["model_type", "feature_group", "reference_group"]
    if "reference_model_type" in paired_pooled:
        pair_cols += ["reference_model_type"]
    pair_cols += ["metric", "difference", "ci_lower", "ci_upper", "n_matches"]
    interval_details = []
    for name in ("ci_level", "n_bootstrap", "bootstrap_unit"):
        if name in pairs and pairs[name].notna().any():
            values = pairs[name].dropna().astype(str).unique().tolist()
            interval_details.append(f"{name}: {', '.join(values[:5])}")
    lines = ["# EPL rolling source-feature ablations", "",
             f"Run date: {metadata.get('run_date','not recorded')}. Saved data snapshot: {metadata.get('data_snapshot_as_of','not recorded')}.", "",
             "**Exploratory retrospective study. The first experiment already inspected 2025/26 outcomes; "
             "there is no new untouched confirmatory holdout here.** No prospective predictions, live profitability or executable arbitrage are claimed.", "",
             "## Numerical findings", ""]
    lines += [f"- {finding}" for finding in findings]
    lines += ["", "## Pooled probability quality on common fixtures", "", _table(pooled[score_cols] if not pooled.empty else pooled), "",
              "Pooled log loss, Brier, accuracy and ECE are computed on all saved outer-season predictions. "
              "ECE is not averaged across seasonal ECE estimates. Lower proper losses are better; "
              "constant forecasts can have low ECE with little resolution. Raw-market, held-out-temperature-only market, "
              "and fixed training-frequency baselines are retained.", "",
              "![Rolling probability quality](ablation_probability_quality.png)", "",
              "![Classwise calibration error](ablation_calibration_error.png)", "",
              "## Same-history sensitivity", "",
              "Every variant shares the same complete-history intersection: both clubs have at least eight observed xG "
              "slots and eight FPL slots in their ten strictly earlier E0 games, with nonmissing fixed numeric performance inputs. "
              "Coverage flags/counts themselves need not equal ten. The all-common-fixture analysis retains missing histories "
              "with training-fitted preprocessing. This sensitivity restricts evaluation of the same fitted predictions; it does not refit.", "",
              _table(complete[score_cols] if not complete.empty else complete), ""]
    if "ablation_history_coverage" in figures:
        lines += ["![Shared history support](ablation_history_coverage.png)", ""]
    lines += ["## Paired comparisons", "", _table(paired_pooled[pair_cols] if not paired_pooled.empty else paired_pooled), "",
              "Differences are candidate minus reference: negative is lower log loss/Brier, positive is higher accuracy. "
              "Conditional intervals resample whole calendar dates within season; pooled comparisons are season-stratified. "
              "They omit model-fitting/calibration/tuning uncertainty and broader cross-date dependence, and are not corrected for multiple comparisons. "
              "ECE values are point-score comparisons unless an explicitly estimated interval is supplied; blank intervals are not zero uncertainty.", ""]
    if interval_details:
        lines += ["Recorded paired-interval settings: " + "; ".join(interval_details) + ".", ""]
    if "ablation_paired_logloss" in figures:
        lines += ["![Paired log-loss intervals](ablation_paired_logloss.png)", ""]
    lines += ["## Fixed exploratory betting summaries", "",
              "All policies use a fixed 5% estimated-return threshold, best individual-book preclosing prices, "
              "and at most one outcome per match. Fixed stake is 10 with initial capital 1,000; quarter Kelly "
              "is capped at 2% per bet, with same-date commitments allocated before settlement. "
              "There is no new tuned-threshold stage in this study. ROI means profit/turnover, not growth on initial capital.", "",
              _table(pooled_bets[["variant", "staking", "outer_seasons", "bet_count", "profit", "turnover", "roi"]] if not pooled_bets.empty else pooled_bets), "",
              "The table adds profit and turnover from separate season replays, each with reset capital; "
              "it is not a continuous bankroll path. No pooled betting confidence interval is manufactured by averaging fold endpoints. "
              "When bootstrap intervals were not computed, those columns remain unavailable and no precision is inferred.", ""]
    if "ablation_betting_roi" in figures:
        lines += ["![Descriptive archived-price returns](ablation_betting_roi.png)", ""]
    lines += ["## Chronology, source controls and limits", "", _table(roles), "",
              "The rolling roles train/tune/calibrate strictly before each outer season. Already inspected outer history "
              "remains retrospective research even with this correct chronological fitting order. "
              "All performance groups share source-availability controls, so Team is not independent of xG/FPL coverage metadata. "
              "The ablations isolate additional performance inputs conditional on those shared controls, rather than removing all source information.", "",
              "Full raw E0 histories support both clubs' basic match statistics. Expanded source reconciliation and "
              "observed-count controls do not prove a historically available starting XI, injury list or squad. "
              "Lagged FPL contributions describe prior player/team performance; source definitions, fantasy scoring and "
              "archived xG model versions can change. Original publication times and quote clocks remain unverified. "
              "A feature earlier than kickoff is not necessarily earlier than an archived preclosing price.", "",
              "Targets are fixtures involving at least one of the twenty 2026/27 clubs, so current-club survivor bias remains. "
              "The first experiment's artifacts are retained separately. The data snapshot is frozen historical material, "
              "not a live feed. Fees, stake limits, price simultaneity and execution are unverified; even positive "
              "historical returns or conditional intervals cannot establish a currently tradeable advantage.", "",
              f"First-experiment output preservation recorded by the run: **{metadata.get('first_experiment_preserved','not recorded')}**.", "",
              "See `source_reconciliation_summary.json`, `feature_groups.json`, `run_metadata.json`, the full paired table, "
              "and tuning/chronological-role tables for audit detail. Numeric findings above are derived from these saved outputs; "
              "report generation never retrains or changes a model.", "",
              "## Inspect and regenerate displays", "",
              "Open [EPL_feature_ablation.xlsx](EPL_feature_ablation.xlsx) or "
              "[the executed notebook](../03_epl_feature_ablation.ipynb). Figures are supplied as PNG and vector SVG. "
              "The workbook has eight review sheets; full source JSON and fixture-level predictions remain separate.", "",
              "From the project root, rebuild displays without retraining:", "", "```powershell",
              "python -c \"from pathlib import Path; from epl_modeling.ablation_reporting import build_ablation_report; "
              f"build_ablation_report(Path('epl_modeling/{output.name}'))\"", "```", ""]
    (output / "ABLATION_RESULTS.md").write_text("\n".join(lines), encoding="utf-8")
    _build_workbook(output, scores, pairs, betting, roles, trials, groups, reconciliation, metadata, findings)
    _build_notebook(output, figures)
