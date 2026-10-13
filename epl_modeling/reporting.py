"""Build standalone research figures, workbook, report and executed notebook."""
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


def markdown_table(frame):
    def cell(value):
        if pd.isna(value):
            return "—"
        if isinstance(value, float):
            return f"{value:.4f}"
        return str(value).replace("|", "\\|").replace("\n", " ")
    rows = ["| " + " | ".join(map(str, frame.columns)) + " |",
            "| " + " | ".join(["---"] * len(frame.columns)) + " |"]
    rows += ["| " + " | ".join(cell(value) for value in row) + " |" for row in frame.itertuples(index=False, name=None)]
    return "\n".join(rows)


def build_figures(output):
    plt.rcParams.update({"figure.dpi": 120, "savefig.dpi": 300, "font.size": 10,
                         "axes.spines.top": False, "axes.spines.right": False})
    colors = {"accuracy": "#d97706", "calibration": "#2563eb", "bet365_devig": "#475569"}
    bins = pd.read_parquet(output / "reliability_bins.parquet")
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.8), sharex=True, sharey=True)
    for ax, outcome in zip(axes, ["H", "D", "A"]):
        ax.plot([0, 1], [0, 1], linestyle="--", color="#94a3b8", linewidth=1)
        for model, part in bins.loc[bins.outcome.eq(outcome)].groupby("model", sort=False):
            part = part.loc[part["count"].ge(5)]
            ax.plot(part.mean_probability, part.observed_frequency, marker="o", label=model, color=colors[model])
            ax.scatter(part.mean_probability, part.observed_frequency, s=np.maximum(12, part["count"] * 0.6), color=colors[model], alpha=0.35)
        ax.set(title={"H": "Home win", "D": "Draw", "A": "Away win"}[outcome],
               xlabel="Predicted probability", xlim=(0, 1), ylim=(0, 1))
        ax.grid(alpha=0.15)
    axes[0].set_ylabel("Observed frequency")
    axes[-1].legend(fontsize=8)
    fig.suptitle("2025/26 held-out reliability: bins with at least five matches")
    fig.tight_layout()
    for extension in ("png", "svg"):
        fig.savefig(output / ("test_reliability." + extension), bbox_inches="tight")
    plt.close(fig)
    equity = pd.read_parquet(output / "daily_equity.parquet")
    fig, axes = plt.subplots(1, 2, figsize=(12, 4), sharey=True)
    for ax, policy in zip(axes, ["validation_selected", "predeclared_5pct"]):
        rows = equity.loc[equity.split.eq("test") & equity.policy.eq(policy)
                          & equity.odds_mode.eq("best_individual_book") & equity.staking.eq("fixed")]
        for branch, part in rows.groupby("branch", sort=False):
            part = part.sort_values("match_date")
            dates = pd.to_datetime(part.match_date)
            values = part.end_bankroll.to_numpy()
            if len(values):
                dates = pd.DatetimeIndex([dates.iloc[0] - pd.Timedelta(days=1), *dates.tolist()])
                values = np.r_[1000, values]
            ax.plot(dates, values, label=branch, color=colors[branch])
        ax.axhline(1000, linestyle="--", color="#94a3b8", linewidth=1)
        ax.set(title={"validation_selected": "Validation-selected edge", "predeclared_5pct": "Predeclared 5% edge"}[policy],
               xlabel="Match calendar date")
        ax.tick_params(axis="x", rotation=25)
        ax.grid(alpha=0.15)
        ax.legend(fontsize=8)
    axes[0].set_ylabel("Hypothetical bankroll (initial 1,000)")
    fig.suptitle("2025/26 archived-price replay: fixed stakes, best individual-book quotes")
    fig.tight_layout()
    for extension in ("png", "svg"):
        fig.savefig(output / ("test_bankroll." + extension), bbox_inches="tight")
    plt.close(fig)


def build_workbook(output):
    sheets = {"Classification": "classification_scores", "Betting summary": "betting_summary",
              "Model selection": "model_selection_scores", "Threshold validation": "threshold_validation",
              "Chronological splits": "chronological_splits", "Paired test intervals": "paired_test_metric_intervals",
              "Feature filters": "feature_filter_audit", "Bet ledger": "bets"}
    with pd.ExcelWriter(output / "EPL_modeling_results.xlsx", engine="openpyxl") as writer:
        for title, table in sheets.items():
            frame = pd.read_parquet(output / (table + ".parquet"))
            for name in frame:
                if frame[name].dtype == object:
                    frame[name] = frame[name].map(lambda x: json.dumps(x, default=str) if isinstance(x, (dict, list, np.ndarray)) else x)
            # Neutralize spreadsheet formula prefixes in externally sourced strings.
            for name in frame.select_dtypes(include=["object", "string"]).columns:
                frame[name] = frame[name].map(lambda x: "'" + x if isinstance(x, str) and x.startswith(("=", "+", "-", "@")) else x)
            frame.to_excel(writer, sheet_name=title, index=False)
            sheet = writer.sheets[title]
            sheet.freeze_panes = "A2"
            sheet.auto_filter.ref = sheet.dimensions
            for cell in sheet[1]:
                cell.font = Font(bold=True, color="FFFFFF")
                cell.fill = PatternFill("solid", fgColor="1E3A5F")
            for column in sheet.columns:
                values = [str(cell.value or "") for cell in list(column)[:100]]
                sheet.column_dimensions[column[0].column_letter].width = min(40, max(12, max(map(len, values)) + 2))


def build_notebook(output):
    nb = nbformat.v4.new_notebook()
    nb.metadata.kernelspec = {"display_name": "Python 3", "language": "python", "name": "python3"}
    nb.cells = [nbformat.v4.new_markdown_cell(
        "# EPL accuracy versus calibration: first experiment\n\n"
        "This notebook loads the completed, reproducible experiment. It does not retrain or select models using the test season. "
        "See `METHODOLOGY.md` and `results/RESULTS.md` for corrected literature, timing limitations and interpretation.\n\n"
        "Reproduce from the repository root: `python -m epl_modeling.experiment --trials 12`."
    ), nbformat.v4.new_code_cell(
        "from pathlib import Path\nimport json\nimport pandas as pd\nfrom IPython.display import display, Image\n"
        "here = Path.cwd()\nRESULTS = here / 'results' if (here / 'results/run_metadata.json').exists() else here / 'epl_modeling/results'\n"
        "metadata = json.loads((RESULTS / 'run_metadata.json').read_text())\n"
        "print('Snapshot:', metadata['data_snapshot_as_of'])\nprint('Locked winners:', metadata['frozen_choices']['families'])\n"
        "display(pd.read_parquet(RESULTS / 'chronological_splits.parquet'))"
    ), nbformat.v4.new_markdown_cell("## Held-out probability quality\nLower log loss, Brier and ECE are better. ECE alone can favor uninformative forecasts."),
        nbformat.v4.new_code_cell(
            "scores = pd.read_parquet(RESULTS / 'classification_scores.parquet')\n"
            "display(scores[scores['split'].eq('test')].reset_index(drop=True))\n"
            "display(pd.read_parquet(RESULTS / 'paired_test_metric_intervals.parquet'))\n"
            "display(Image(filename=str(RESULTS / 'test_reliability.png')))"
        ), nbformat.v4.new_markdown_cell(
            "## Archived-price replay\nThresholds were selected only on 2024/25. The 5% policy is a separately predeclared secondary comparison. "
            "ROI is profit / stakes, not return on initial bankroll. Quote simultaneity, limits, availability times and execution are unverified."
        ), nbformat.v4.new_code_cell(
            "betting = pd.read_parquet(RESULTS / 'betting_summary.parquet')\n"
            "columns = ['branch','policy','odds_mode','staking','bet_count','profit','turnover','roi','roi_ci_low','roi_ci_high','max_drawdown']\n"
            "display(betting[betting['split'].eq('test')][columns].reset_index(drop=True))\n"
            "display(Image(filename=str(RESULTS / 'test_bankroll.png')))"
        ), nbformat.v4.new_markdown_cell("## Player and team feature audit\nOnly strictly earlier match observations can enter predictors; current squads, injuries and final-season totals are excluded."),
        nbformat.v4.new_code_cell(
            "display(json.loads((RESULTS / 'selected_features.json').read_text()))\n"
            "filters = pd.read_parquet(RESULTS / 'feature_filter_audit.parquet')\n"
            "display(filters[['feature','train_missing_rate','ks_statistic','ks_qvalue','drop_reason']].head(25))\n"
            "features = json.loads((RESULTS / 'feature_metadata.json').read_text())\n"
            "print('Feature metadata keys:', list(features))"
        ), nbformat.v4.new_markdown_cell("## Mathematical price discrepancies\nThese are archived-price candidates, not verified executable arbitrage."),
        nbformat.v4.new_code_cell(
            "odds = pd.read_parquet(RESULTS / 'bookmaker_odds_panel.parquet')\n"
            "test_odds = odds[odds['season'].eq('2025-26')]\n"
            "print('Test matches with odds:', len(test_odds))\n"
            "print('Mathematical candidates:', int(test_odds['mathematical_arb_candidate'].sum()))\n"
            "print('Unverified quote clocks:', int(test_odds['quotes_asynchronous_or_unverified'].sum()))\n"
            "display(test_odds[test_odds['mathematical_arb_candidate']][['match_id','match_date','arb_inverse_odds_sum','arb_theoretical_margin']].head(10))"
        )]
    notebook_path = output.parent / "02_epl_modeling_results.ipynb"
    NotebookClient(nb, timeout=120, kernel_name="python3", resources={"metadata": {"path": str(output.parent)}}).execute()
    nbformat.write(nb, notebook_path)


def build_report(output: Path):
    metadata = json.loads((output / "run_metadata.json").read_text())
    scores = pd.read_parquet(output / "classification_scores.parquet")
    test = scores.loc[scores.split.eq("test") & scores.scope.eq("matched_bookmaker_coverage"),
                      ["model", "n_matches", "accuracy", "classwise_ece_10", "log_loss", "brier_score"]]
    betting = pd.read_parquet(output / "betting_summary.parquet")
    primary = betting.loc[betting.split.eq("test") & betting.policy.eq("validation_selected"),
                         ["branch", "odds_mode", "staking", "bet_count", "profit", "roi", "roi_ci_low", "roi_ci_high", "max_drawdown"]]
    secondary = betting.loc[betting.split.eq("test") & betting.policy.eq("predeclared_5pct"),
                           ["branch", "odds_mode", "staking", "bet_count", "profit", "roi", "roi_ci_low", "roi_ci_high"]]
    splits = pd.read_parquet(output / "chronological_splits.parquet")
    intervals = pd.read_parquet(output / "paired_test_metric_intervals.parquet")
    odds = pd.read_parquet(output / "bookmaker_odds_panel.parquet")
    test_odds = odds.loc[odds.season.eq("2025-26")]
    choices = metadata["frozen_choices"]
    accuracy_score = test.loc[test.model.eq("accuracy")].iloc[0]
    calibration_score = test.loc[test.model.eq("calibration")].iloc[0]
    market_score = test.loc[test.model.eq("bet365_devig")].iloc[0]
    fixed = secondary.loc[secondary.odds_mode.eq("best_individual_book") & secondary.staking.eq("fixed")]
    fixed_a = fixed.loc[fixed.branch.eq("accuracy")].iloc[0]
    fixed_c = fixed.loc[fixed.branch.eq("calibration")].iloc[0]
    findings = [
        "## First-run findings", "",
        f"On {int(accuracy_score.n_matches)} held-out 2025/26 fixtures, the calibration-selected model's ten-bin classwise ECE is "
        f"{100*calibration_score.classwise_ece_10:.2f}%, versus {100*accuracy_score.classwise_ece_10:.2f}% for the accuracy-selected model. "
        f"Its accuracy is lower ({100*calibration_score.accuracy:.2f}% versus {100*accuracy_score.accuracy:.2f}%). "
        f"The bookmaker benchmark has lower log loss ({market_score.log_loss:.4f}) than both the calibration branch "
        f"({calibration_score.log_loss:.4f}) and accuracy branch ({accuracy_score.log_loss:.4f}). "
        "The training-frequency baseline has the lowest ECE despite worse proper scores, illustrating why ECE alone cannot establish betting usefulness.", "",
        "Neither branch found a positive-profit threshold with at least thirty validation bets. Both primary policies therefore hold cash in the test; "
        "their zero profit and undefined ROI do not demonstrate a profitable strategy.", "",
        f"Under the separately predeclared 5% edge policy with fixed stakes and best individual-book odds, the calibration branch's ROI is "
        f"{100*fixed_c.roi:+.2f}% (conditional 95% date-bootstrap interval {100*fixed_c.roi_ci_low:+.2f}% to {100*fixed_c.roi_ci_high:+.2f}%), "
        f"versus {100*fixed_a.roi:+.2f}% ({100*fixed_a.roi_ci_low:+.2f}% to {100*fixed_a.roi_ci_high:+.2f}%) for accuracy selection. "
        "Both intervals include zero; neither supplies a reliable positive-return finding. The quarter-Kelly versions lose money in this test. "
        "These outcomes support further investigation of probability quality and market information, without establishing a tradable advantage.", "",
        "The selected models use team boxscore features only. Player and xG candidates exist in the feature frame but do not survive this budgeted ranking/selection path. "
        "This run does not measure the incremental value of player information; a separate, prospectively specified ablation is still needed. "
        "See [feature coverage](../FEATURE_COVERAGE.md) for the early FPL opponent-identity gap.", "",
    ]
    lines = ["# EPL first experiment: accuracy versus calibration", "",
             "Run date: October 13, 2026. Data snapshot: October 6, 2026. This is the first completed research run, with a small predefined search budget.", "",
             "The experiment trains logistic regression, random forest, SVM and MLP models under two separate selection objectives. "
             "The accuracy branch selects its final family by 2023/24 accuracy; the calibration branch selects by 2023/24 classwise ECE. "
             "Both branches use held-out temperature calibration, and betting thresholds are fixed using 2024/25 only. "
             "The 2025/26 test season is scored after those decisions are locked.", "",
             "**Interpretation:** these are hypothetical archived-price results. Per-quote clocks and historical feature publication times are unavailable, "
             "so the run does not establish that every feature and price coexisted at a tradable instant. It does not establish executable arbitrage or live profitability.", "",
             *findings, "## Data and chronology", "", markdown_table(splits), "",
             "The historical sample includes only fixtures involving at least one of the 20 current 2026/27 clubs. Other opponents are retained, "
             "and their historical team features are reconstructed from saved whole-league files. This fixed current-club cohort has survivor bias and is not a full historical-league sample. "
             "The partial current season contains only 50 observed completed games through September 20; the October retrieval/run dates do not extend that match coverage.", "",
             "## Locked model choices", "",
             f"- Accuracy family: `{choices['families']['accuracy']}`.",
             f"- Calibration family: `{choices['families']['calibration']}`.",
             f"- TPE budget: {metadata['trials_per_family_per_branch']} seeded trials per family per branch.", "",
             "Selected features and the full trial/selection audit are saved alongside this report. Candidate feature screening uses training data only: "
             "missingness and constant-feature checks, early/late-training KS tests with BH adjustment, a Spearman redundancy filter, "
             "and a budgeted greedy forward search using two expanding training-season folds. Those internal scores are optimization diagnostics. "
             "No test season is used to choose features, hyperparameters, calibration parameters, families or thresholds.", "",
             "## Held-out probability quality", "", markdown_table(test), "",
             "The table uses the same matches covered by complete Bet365 reference triplets for all four predictors. "
             "The full-cohort scores are also saved. Lower log loss, Brier and ECE are better; higher accuracy is better. "
             "Classwise ECE averages three one-vs-rest ECEs in ten equal-width bins. Five- and fifteen-bin sensitivities are saved. "
             "The multiclass Brier score is the mean sum of the three squared probability errors, with range [0,2]. "
             "A low ECE can reward nearly constant probabilities, so frequency and market baselines and proper scores must be considered together.", "",
             "![Held-out reliability](test_reliability.png)", "",
             "Paired calendar-date bootstrap intervals below describe calibration-minus-accuracy metric differences, conditional on the fitted models. "
             "They do not include model-selection or fitting uncertainty, and do not prove performance across other seasons.", "", markdown_table(intervals), "",
             "## Validation-selected betting policy", "",
             "For each branch, thresholds 0%, 2.5%, 5%, 7.5%, 10%, 15% and 20% were examined on 2024/25 only. "
             "The selected policy maximizes fixed-stake validation ROI among thresholds with at least 30 bets and positive profit. "
             "If none qualifies, the primary policy holds cash. The same locked threshold is then used for both quoted-price modes and both staking rules.", ""]
    for branch, item in choices["thresholds"].items():
        label = "hold cash" if item["threshold"] > 100 else f"{100 * item['threshold']:.1f}% expected-return edge"
        lines.append(f"- {branch}: **{label}** ({item['reason']}).")
    lines += ["", markdown_table(primary), "",
              "ROI is profit divided by total stakes; it is not return on the initial bankroll. Fixed stake is 10 with initial capital 1,000. "
              "Quarter Kelly is capped at 2% of date-start capital per bet. Only one outcome is selected per match. "
              "All same-date stakes use the date-start bankroll, and commitments are scaled before any settlement if they exceed available cash. "
              "Bootstrap intervals resample whole match dates conditional on the recorded bets; they omit fitting, threshold selection, execution and cross-date dependence uncertainty.", "",
              "## Predeclared 5% edge comparison", "",
              "This secondary policy was specified before inspecting the test and is reported even if validation recommends holding cash. "
              "It must not be substituted for the primary policy based on which test result looks better.", "", markdown_table(secondary), "",
              "![Held-out bankroll](test_bankroll.png)", "",
              "## Odds and arbitrage audit", "",
              f"There are {len(test_odds)} test matches with complete individual-book prices and a complete Bet365 reference. "
              f"The inverse-best-odds sum is below one in {int(test_odds.mathematical_arb_candidate.sum())} archived test matches. "
              f"All {int(test_odds.quotes_asynchronous_or_unverified.sum())} test price rows have missing or incompatible quote clocks. "
              "These are mathematical candidate discrepancies, not verified simultaneously available arbitrage. "
              "The panel excludes market maxima/averages, exchanges, incomplete or invalid triplets, and unreliable Pinnacle records from July 23, 2025. "
              "All outcomes use the same native preclosing snapshot label. Preclosing does not mean a verified opening quote. "
              "Line-shopping comparisons can change both the chosen outcome and whether a bet qualifies; they measure entire policy differences, not an isolated causal price effect.", "",
              "## Corrected literature and practical limits", "",
              "The proposal cites Walsh and Joshi (2024). Its [2025 corrigendum](https://doi.org/10.1016/j.mlwa.2025.100627) corrects feature-engineering errors "
              "and changes the reported average returns to losses for both selection approaches. The original positive-average-profit headline must not motivate a claim "
              "that calibration guarantees profit. See [METHODOLOGY.md](../METHODOLOGY.md) for the corrected comparison and this study's explicit adaptations.", "",
              "Current player values, injuries, squad snapshots and actual target-match lineups do not enter historical predictors. Lagged FPL aggregates describe "
              "past team/player contributions; they do not establish the players available before a future match. Historical xG models and archival publication clocks may have changed. "
              "The search budget, one held-out season, current-club selection, unsynchronized quotes, unmodeled fees/limits and unverified publication times limit generalization. "
              "Any later changes motivated by this test make 2025/26 development data; a new untouched evaluation period would then be needed.", "",
              "## Reproduce and inspect", "", "```powershell", "python -m pip install -r epl_modeling/requirements.txt",
              "python -m unittest discover -s epl_modeling/tests -p 'test_*.py' -v", "python -m epl_modeling.experiment --trials 12", "```", "",
              "Open [EPL_modeling_results.xlsx](EPL_modeling_results.xlsx) or the [executed notebook](../02_epl_modeling_results.ipynb). "
              "CSV and Parquet tables, fitted model bundles, selected features, trial diagnostics, locked choices and input/code hashes are saved in this directory. "
              "Only load joblib models from a trusted source.", ""]
    (output / "RESULTS.md").write_text("\n".join(lines), encoding="utf-8")
    build_figures(output)
    build_workbook(output)
    build_notebook(output)
