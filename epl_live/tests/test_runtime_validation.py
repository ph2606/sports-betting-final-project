"""Meaningful guards for changed frozen dependencies and live feature inputs."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from epl_live.runtime_validation import (
    historical_feature_inventory, preserve_feature_inventory, validate_frozen_models,
)


def digest(body):
    return hashlib.sha256(body).hexdigest()


class FrozenDependencyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.models = self.root / "models"
        self.models.mkdir()
        self.protocol = self.root / "protocol.md"
        self.protocol.write_bytes(b"protocol")
        (self.root / "training_features.parquet").write_bytes(b"training inputs")
        (self.root / "train.py").write_bytes(b"training code")
        (self.models / "market_temperature.joblib").write_bytes(b"market temperature")
        items = []
        for index in range(8):
            filename = f"model_{index}.joblib"
            body = f"model_{index}".encode()
            (self.models / filename).write_bytes(body)
            items.append({"model_id": f"model_{index}", "file": filename, "sha256": digest(body)})
        manifest = {"protocol_sha256": digest(b"protocol"), "models": items,
                    "market_temperature_sha256": digest(b"market temperature"),
                    "input_feature_table": "training_features.parquet",
                    "input_feature_table_sha256": digest(b"training inputs"),
                    "code_sha256": {"train.py": digest(b"training code")}}
        (self.models / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    def test_market_calibrator_tampering_fails_before_release(self):
        validate_frozen_models(self.models, self.root, self.protocol)
        (self.models / "market_temperature.joblib").write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "dependency"):
            validate_frozen_models(self.models, self.root, self.protocol)

    def test_training_input_and_code_tampering_fail(self):
        for filename in ("training_features.parquet", "train.py"):
            with self.subTest(filename=filename):
                path = self.root / filename
                original = path.read_bytes()
                path.write_bytes(b"changed")
                with self.assertRaisesRegex(ValueError, "dependency"):
                    validate_frozen_models(self.models, self.root, self.protocol)
                path.write_bytes(original)

    def test_missing_declared_model_fails(self):
        (self.models / "model_7.joblib").unlink()
        with self.assertRaisesRegex(ValueError, "dependency"):
            validate_frozen_models(self.models, self.root, self.protocol)

    def test_runner_rejects_changed_calibrator_before_collection(self):
        from epl_live import run
        (self.models / "market_temperature.joblib").write_bytes(b"changed")
        with patch.object(run, "fit_candidates", return_value=self.models), \
             patch.object(run, "PROJECT", self.root), \
             patch.object(run, "PROTOCOL", self.protocol), \
             patch.object(run, "collect_snapshot") as collect:
            with self.assertRaisesRegex(ValueError, "dependency"):
                run.run_cycle()
        collect.assert_not_called()


class FeatureInventoryTests(unittest.TestCase):
    def test_changed_input_or_added_path_cannot_be_referenced_as_stable(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "data/raw/football_data/2526/E0.csv"
            path.parent.mkdir(parents=True)
            path.write_bytes(b"original")
            output = root / "output"
            output.mkdir()
            before = historical_feature_inventory(root)
            path.write_bytes(b"revised")
            with self.assertRaisesRegex(ValueError, "changed"):
                preserve_feature_inventory(output, root, before)
            path.write_bytes(b"original")
            second = root / "data/raw/fpl_archive/2024-25/teams.csv"
            second.parent.mkdir(parents=True)
            second.write_bytes(b"new lookup")
            with self.assertRaisesRegex(ValueError, "changed"):
                preserve_feature_inventory(output, root, before)
            self.assertFalse((output / "historical_feature_inputs.json").exists())

    def test_stable_inventory_keeps_complete_hashed_file_reference(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "data/processed/understat/matches.parquet"
            path.parent.mkdir(parents=True)
            path.write_bytes(b"xg inputs")
            output = root / "output"
            output.mkdir()
            before = historical_feature_inventory(root)
            reference = preserve_feature_inventory(output, root, before)
            manifest_path = output / "historical_feature_inputs.json"
            manifest = json.loads(manifest_path.read_text())
            self.assertEqual(reference["sha256"], digest(manifest_path.read_bytes()))
            self.assertEqual(manifest["files"]["data/processed/understat/matches.parquet"]["sha256"], digest(b"xg inputs"))
            self.assertFalse(reference["publication_time_verified"])
