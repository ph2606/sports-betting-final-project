"""Verify frozen release dependencies and preserve a historical input inventory."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_frozen_models(model_directory, project_root, protocol_path):
    """Fail before releasing probabilities if any frozen dependency changed."""
    model_directory, project_root = Path(model_directory), Path(project_root)
    manifest = json.loads((model_directory / "manifest.json").read_text(encoding="utf-8"))
    if file_sha256(protocol_path) != manifest["protocol_sha256"]:
        raise ValueError("Frozen model protocol changed")
    if len(manifest["models"]) != 8 or len({item["model_id"] for item in manifest["models"]}) != 8:
        raise ValueError("The eight declared frozen candidates are not present")
    dependencies = {model_directory / item["file"]: item["sha256"] for item in manifest["models"]}
    dependencies[model_directory / "market_temperature.joblib"] = manifest["market_temperature_sha256"]
    dependencies[project_root / manifest["input_feature_table"].replace("\\", "/")] = manifest["input_feature_table_sha256"]
    dependencies.update({project_root / name.replace("\\", "/"): digest
                         for name, digest in manifest["code_sha256"].items()})
    for path, expected in dependencies.items():
        if not path.is_file() or file_sha256(path) != expected:
            raise ValueError("Frozen model dependency is missing or changed: " + str(path))
    return manifest


def historical_feature_inventory(data_root):
    """Cover every historical feature/evidence input, with optional paths included.

    This is a conservative file inventory, not a claim that every available
    optional path contributes a predictor. It deliberately covers both table
    formats and archive seasons, including paths bypassed by source preference.
    Changes or new paths during feature construction fail the release guard.
    """
    root = Path(data_root)
    paths = set((root / "data/raw/football_data").glob("*/E0.csv"))
    for pattern in ("*/teams.csv", "*/players_raw.csv", "*/fixtures.csv", "*/gws/merged_gw.csv"):
        paths.update((root / "data/raw/fpl_archive").glob(pattern))
    paths.update((root / "data/raw/fpl_current").glob("*.json"))
    for relative in ("football_data/matches_current_cohort", "integrated/match_source_links", "understat/matches",
                     "fpl_archive/player_gameweeks", "fpl_current/player_match_history", "fpl_current/teams", "fpl_current/fixtures"):
        for suffix in (".parquet", ".csv"):
            path = (root / "data/processed" / relative).with_suffix(suffix)
            if path.exists():
                paths.add(path)
    return {path.relative_to(root).as_posix(): {"sha256": file_sha256(path), "bytes": path.stat().st_size}
            for path in sorted(paths) if path.is_file()}


def preserve_feature_inventory(output, data_root, before):
    after = historical_feature_inventory(data_root)
    if before != after:
        raise ValueError("Historical feature input files changed during construction")
    path = Path(output) / "historical_feature_inputs.json"
    manifest = {"schema_version": 1, "observed_at_utc": datetime.now(timezone.utc).isoformat(),
                "root": "epl_data", "files": after,
                "scope": "Conservative complete inventory of historical feature and identity-evidence inputs, including optional paths and both table formats.",
                "publication_time_verified": False, "unchanged_across_feature_construction": True}
    with path.open("x", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2)
        handle.write("\n")
    return {"source": "Historical feature-input inventory: " + str(path),
            "sha256": file_sha256(path), "observed_at_utc": manifest["observed_at_utc"],
            "publication_time_verified": False}
