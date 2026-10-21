"""Publish a presentation revision while preserving every fitted-study byte.

This separate immutable copy corrects the initial renderer's coverage-summary
schema and Markdown cell escaping. It never refits or reissues forecasts.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil

import pandas as pd

from . import report
from .audit import audit_export
from .build import ROOT, sha, write_json
from epl_strategy_validation.build import publish_latest


def coverage_table(data):
    frame = data["feature_coverage"].copy()
    columns = {"season", "side", "target_sides", "history_available_fraction",
        "mean_observed_matches5", "mean_observed_matches10", "full_projected_xi_fraction", "mean_projected_players"}
    if not columns.issubset(frame):
        raise ValueError("The reviewed report requires the native per-season coverage summary")
    frame = frame.loc[frame.season.isin(report.SEASONS)].sort_values(["season", "side"])
    if frame.duplicated(["season", "side"]).any() or len(frame) != 8:
        raise ValueError("Coverage must include both sides in all four evaluated seasons")
    return pd.DataFrame([{"Season": row.season, "Side": row.side,
        "Target\nsides": report.number(row.target_sides, 0),
        "History\navailable": report.number(row.history_available_fraction, percent=True),
        "Mean observed\nslots / 5": report.number(row.mean_observed_matches5),
        "Mean observed\nslots / 10": report.number(row.mean_observed_matches10),
        "Full projected\nXI": report.number(row.full_projected_xi_fraction, percent=True),
        "Mean selected\nplayers": report.number(row.mean_projected_players)} for row in frame.itertuples()])


def markdown(pages, entries):
    safe = deepcopy(pages)
    for page in safe:
        for block in page["blocks"]:
            if block["type"] != "table":
                continue
            block["frame"] = block["frame"].map(lambda value: str(value).replace("|", "&#124;"))
            block["frame"].columns = [str(c).replace("|", "&#124;") for c in block["frame"].columns]
    return report.prior._markdown(safe, entries)


@contextmanager
def reviewed_renderer():
    original_coverage, original_markdown, original_body = report._coverage_table, report._markdown, report._body

    def body(data, figures):
        pages, displays = original_body(data, figures)
        scores = data["model_metrics_pooled"]
        controls = scores.loc[scores.feature_group.eq("team_control")].set_index("model_type")
        player = scores.loc[scores.feature_group.isin(("player_form", "player_squad", "team_player_squad"))]
        worse = sum(row.log_loss > controls.loc[row.model_type, "log_loss"] for row in player.itertuples())
        losses = int(data["metrics_continuous"].profit.lt(0).sum())
        pages[0]["blocks"].append({"type": "paragraph", "text":
            f"Observed result: {worse} of {len(player)} player-based variants have higher pooled log loss than their matched team control. "
            f"All {len(data['metrics_continuous'])} new continuous strategy accounts are retained; {losses} lose money. "
            "These retrospective results provide no evidence that this expanded player representation improves the matched team models."})
        for page in pages:
            if page["title"] == "Player-history coverage and projected squad completeness":
                page["blocks"].append({"type": "paragraph", "text":
                    "A short projected XI can result from too few previously observed players in a required role even when source history is complete. "
                    "The selected players' per-90 measures are minutes-weighted historical profiles, not forecasts of the XI's match output. "
                    "Detailed target-side and selected-player audit tables are saved beside this report."})
        return pages, displays

    report._coverage_table, report._markdown, report._body = coverage_table, markdown, body
    try:
        yield
    finally:
        report._coverage_table, report._markdown, report._body = original_coverage, original_markdown, original_body


def build_review(source, output, *, update_latest=False):
    source, output = Path(source).resolve(), Path(output).resolve()
    parent = (ROOT / "epl_player_models/results").resolve()
    if source == output or output.exists() or parent not in output.parents:
        raise ValueError("Use a new review directory below epl_player_models/results")
    original = json.loads((source / "manifest.json").read_text())
    for name, digest in original["output_sha256"].items():
        if sha(source / name) != digest:
            raise ValueError("Changed fitted-study output: " + name)
    output.mkdir(parents=True)
    for name in original["output_sha256"]:
        if Path(name).parts[0] in {"figures", "report"} or name == "independent_audit.json":
            continue
        target = output / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / name, target)
    provenance = json.loads((output / "source_provenance.json").read_text())
    revision = {"source_run": source.relative_to(ROOT).as_posix(), "source_manifest_sha256": sha(source / "manifest.json"),
        "revised_at_utc": datetime.now(timezone.utc).isoformat(),
        "changes": ["Show actual coverage measures for all four evaluated seasons", "Escape literal pipes in Markdown tables", "State the observed comparison and role-coverage limits"],
        "no_model_refit": True, "no_forecast_reissue": True}
    provenance["report_revision"] = revision
    added = [Path(__file__), Path(__file__).parent / "tests/test_report_review.py", source / "manifest.json"]
    provenance["inputs_and_code_sha256"].update({p.relative_to(ROOT).as_posix(): sha(p) for p in added})
    write_json(output / "source_provenance.json", provenance)
    write_json(output / "independent_audit.json", audit_export(output))
    with reviewed_renderer():
        result = report.build_report(output)
    retained = [name for name in original["output_sha256"] if Path(name).parts[0] not in {"figures", "report"}
        and name not in {"independent_audit.json", "source_provenance.json"}]
    if any(sha(source / name) != sha(output / name) for name in retained):
        raise AssertionError("A model, feature, prediction, account or released forecast changed")
    if any(sha(source / name) != digest for name, digest in original["output_sha256"].items()):
        raise AssertionError("The original fitted-study output changed")
    for name, digest in provenance["inputs_and_code_sha256"].items():
        if sha(ROOT / name) != digest:
            raise AssertionError("Protected source changed during report review")
    manifest = {**original, **provenance, "report_revision": {**revision, "byte_identical_analytical_files": len(retained)},
        "completed_at_utc": datetime.now(timezone.utc).isoformat(), "report": result,
        "output_sha256": {p.relative_to(output).as_posix(): sha(p) for p in sorted(output.rglob("*")) if p.is_file()}}
    write_json(output / "manifest.json", manifest)
    if update_latest:
        publish_latest(output)
    return {"report": result, "revision": manifest["report_revision"]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--update-latest", action="store_true")
    args = parser.parse_args()
    print(json.dumps(build_review(args.source, args.output, update_latest=args.update_latest), indent=2))
