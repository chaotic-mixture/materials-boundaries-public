"""Offline experimental integration, failure atomicity and frozen five-record delta."""
from contextlib import redirect_stdout
from copy import deepcopy
from hashlib import sha256
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from materials_boundaries.material_references import merge_material_catalogs
from scripts.integrate_material_candidates import (
    FILES, PIN_KEYS, ROOT, build_package, main, write_package,
)
from test_material_append_merge import append_fixture
from test_material_reference_contract import synthetic_material_catalog
from test_nbs_next_batch import recover_742_catalogs


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")


def save(path, value):
    path.write_bytes(encoded(value))
    return sha256(path.read_bytes()).hexdigest()


class IncrementalIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.baseline = self.root / "baseline"
        self.baseline.mkdir()
        self.batch_dir = self.root / "experimental/material-batches/packet"
        self.batch_dir.mkdir(parents=True)
        self.manifest_dir = self.batch_dir.parent / "integration"
        self.manifest_dir.mkdir()
        self.manifest_path = self.manifest_dir / "integration.json"
        self.output = self.root / "package.json"
        graph = dict(zip(FILES, synthetic_material_catalog()))
        self.append = append_fixture()
        pins = {PIN_KEYS[name]: save(self.baseline / FILES[name], value) for name, value in graph.items()}
        self.batch = {"id": "synthetic-test-only", "candidate_commit": "0" * 40}
        for name, value in {**self.append, "review": {"status": "synthetic fixture; all reviews pending"}}.items():
            filename = name + ".json"
            self.batch[name] = {"path": "../packet/" + filename,
                                "sha256": save(self.batch_dir / filename, value)}
        self.manifest = {"schema": "experimental-material-integration/1", "scope": "local-experimental-only",
                         "baseline_sha256": pins, "batches": [self.batch], "status_adjustments": [],
                         "pending_gates": ["Independent scientific and source-specific rights review"],
                         "released_main_count": 1081}
        self.flush()

    def flush(self):
        save(self.manifest_path, self.manifest)

    def update_packet(self, name, value):
        self.batch[name]["sha256"] = save(self.batch_dir / (name + ".json"), value)
        self.flush()

    def run_package(self):
        return write_package(self.baseline, self.manifest_path, self.output, repository_root=self.root)

    def assert_no_write_on_failure(self):
        before = {path: path.read_bytes() for path in self.root.rglob("*.json")}
        with self.assertRaises(ValueError):
            self.run_package()
        self.assertFalse(self.output.exists())
        self.assertEqual({path: path.read_bytes() for path in self.root.rglob("*.json")}, before)

    def test_report_and_identical_rerun_preserve_output_and_inputs(self):
        before = {path: path.read_bytes() for path in self.root.rglob("*.json")}
        package, created = self.run_package()
        self.assertTrue(created)
        stored, timestamp = self.output.read_bytes(), self.output.stat().st_mtime_ns
        second, created = self.run_package()
        self.assertFalse(created)
        self.assertEqual(second, package)
        self.assertEqual(self.output.read_bytes(), stored)
        self.assertEqual(self.output.stat().st_mtime_ns, timestamp)
        self.assertEqual({path: path.read_bytes() for path in before}, before)
        report = package["report"]
        self.assertEqual(report["delta"]["identities"], 1)
        self.assertEqual(report["delta"]["sources"], 0)
        self.assertEqual(report["delta"]["categories"]["metal"], 1)
        self.assertEqual(report["batches"][0]["existing_ids"]["sources"], ["synthetic_reference"])
        self.assertEqual(report["formal_admitted_delta"], 0)
        self.assertEqual(report["released_main_count"], 1081)
        self.assertTrue(report["pending_gates"])

    def test_applied_graph_with_explicitly_rebound_baseline_has_zero_delta(self):
        package, _ = self.run_package()
        for name, value in package["catalogs"].items():
            self.manifest["baseline_sha256"][PIN_KEYS[name]] = save(self.baseline / FILES[name], value)
        self.flush()
        rerun = build_package(self.baseline, self.manifest_path, repository_root=self.root)
        self.assertEqual(rerun["catalogs"], package["catalogs"])
        self.assertTrue(all(rerun["report"]["delta"][name] == 0 for name in ("identities", "properties", "sources")))
        self.assertEqual(rerun["report"]["delta"]["states"], 0)
        self.assertEqual(rerun["report"]["delta"]["identities"], 0)

    def test_different_existing_output_is_never_replaced(self):
        self.output.write_bytes(b"user-owned result\n")
        before = {path: path.read_bytes() for path in self.root.rglob("*.json")}
        with self.assertRaisesRegex(ValueError, "output already exists"):
            self.run_package()
        self.assertEqual({path: path.read_bytes() for path in self.root.rglob("*.json")}, before)

    def test_atomic_publication_failure_removes_temporary_file_without_writing_output(self):
        before = {path: path.read_bytes() for path in self.root.rglob("*") if path.is_file()}
        with patch("scripts.integrate_material_candidates.os.link", side_effect=PermissionError("synthetic link failure")):
            with self.assertRaisesRegex(PermissionError, "synthetic link failure"):
                self.run_package()
        self.assertFalse(self.output.exists())
        self.assertEqual({path: path.read_bytes() for path in self.root.rglob("*") if path.is_file()}, before)

    def test_changed_input_without_new_pin_fails_without_output(self):
        (self.batch_dir / "properties.json").write_bytes(b"{}\n")
        self.assert_no_write_on_failure()

    def test_wrong_baseline_pin_fails_without_output(self):
        self.manifest["baseline_sha256"]["materials"] = "0" * 64
        self.flush()
        self.assert_no_write_on_failure()

    def test_missing_property_link_rejected_even_with_refreshed_pin(self):
        self.update_packet("properties", {"schema_version": "1.0.0", "records": []})
        self.assert_no_write_on_failure()

    def test_missing_quantity_rejected_even_with_refreshed_pin(self):
        del self.append["properties"]["records"][0]["quantity"]
        self.update_packet("properties", self.append["properties"])
        self.assert_no_write_on_failure()

    def test_wrong_unit_rejected_even_with_refreshed_pin(self):
        self.append["properties"]["records"][0]["reported_value"]["unit_code"] = "GPa"
        self.update_packet("properties", self.append["properties"])
        self.assert_no_write_on_failure()

    def test_conflicting_existing_source_rejected(self):
        self.append["sources"]["records"][0]["title"] = "Changed existing source"
        self.update_packet("sources", self.append["sources"])
        self.assert_no_write_on_failure()

    def test_unregistered_evidence_url_rejected(self):
        self.append["properties"]["records"][0]["evidence"][0]["url"] = "https://example.invalid/unregistered.pdf"
        self.update_packet("properties", self.append["properties"])
        self.assert_no_write_on_failure()

    def test_later_bad_batch_cannot_leave_partial_output(self):
        second = deepcopy(self.batch)
        second["id"] = "second-invalid-batch"
        second["review"]["sha256"] = "0" * 64
        self.manifest["batches"].append(second)
        self.flush()
        self.assert_no_write_on_failure()

    def test_arbitrary_scientific_status_adjustment_is_rejected(self):
        self.manifest["status_adjustments"] = [{"batch_id": self.batch["id"], "table": "properties",
            "record_id": "refprop_synthetic_b_density", "field": "reported_value.number",
            "expected": "2.70", "value": "9.99", "reason": "Forbidden scientific edit"}]
        self.flush()
        self.assert_no_write_on_failure()

    def test_duplicate_json_keys_rejected_after_digest_check(self):
        path = self.batch_dir / "review.json"
        path.write_bytes(b'{"status":"pending","status":"approved"}')
        self.batch["review"]["sha256"] = sha256(path.read_bytes()).hexdigest()
        self.flush()
        self.assert_no_write_on_failure()

    def test_candidate_paths_cannot_escape_packet_tree_or_use_runtime_input(self):
        for path in ("../../../baseline/materials.json", "../../../materials_boundaries/data/materials.json"):
            with self.subTest(path=path):
                self.batch["materials"]["path"] = path
                self.flush()
                self.assert_no_write_on_failure()

    def test_output_cannot_target_baseline_or_manifest(self):
        for path in (self.baseline / "new.json", self.manifest_path):
            with self.subTest(path=path):
                with self.assertRaises(ValueError):
                    write_package(self.baseline, self.manifest_path, path, repository_root=self.root)


class FrozenFiveRecordIntegrationTests(unittest.TestCase):
    def test_actual_five_records_recover_predecessor_and_reproduce_runtime(self):
        manifest_path = ROOT / "experimental/material-batches/20261016-nb-halide-incremental/integration.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        current = {name: json.loads((ROOT / "materials_boundaries/data" / filename).read_text(encoding="utf-8"))
                   for name, filename in FILES.items()}
        current = recover_742_catalogs(current)
        predecessor = deepcopy(current)
        append_packets = []
        for batch in manifest["batches"]:
            append = {name: json.loads((manifest_path.parent / batch[name]["path"]).read_text(encoding="utf-8"))
                      for name in FILES}
            append_packets.append(append)
            for table, fields in (("materials", ("identities", "grades", "records")), ("properties", ("records",))):
                for field in fields:
                    new_ids = {row["id"] for row in append[table][field]}
                    predecessor[table][field] = [row for row in predecessor[table][field] if row["id"] not in new_ids]
        predecessor["sources"]["records"] = [row for row in predecessor["sources"]["records"]
                                                  if row["id"] != "watanabe2026_niobium_thermophysical"]
        with tempfile.TemporaryDirectory() as directory:
            baseline = Path(directory) / "baseline"
            baseline.mkdir()
            for name, value in predecessor.items():
                actual_hash = save(baseline / FILES[name], value)
                self.assertEqual(actual_hash, manifest["baseline_sha256"][PIN_KEYS[name]])
            output = Path(directory) / "integration.json"
            with redirect_stdout(io.StringIO()) as stdout:
                self.assertEqual(main(["--baseline-dir", str(baseline), "--manifest", str(manifest_path),
                                       "--output", str(output)]), 0)
            self.assertIn("Recorded baseline-to-candidate identity delta: 5", stdout.getvalue())
            self.assertIn("New artifact written: yes", stdout.getvalue())
            stored, timestamp = output.read_bytes(), output.stat().st_mtime_ns
            with redirect_stdout(io.StringIO()) as stdout:
                self.assertEqual(main(["--baseline-dir", str(baseline), "--manifest", str(manifest_path),
                                       "--output", str(output)]), 0)
            self.assertIn("Unchanged experimental integration artifact:", stdout.getvalue())
            self.assertIn("Recorded baseline-to-candidate identity delta: 5", stdout.getvalue())
            self.assertIn("New artifact written: no", stdout.getvalue())
            self.assertEqual(output.read_bytes(), stored)
            self.assertEqual(output.stat().st_mtime_ns, timestamp)
            package = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(package["catalogs"], current)
        for name, filename in FILES.items():
            self.assertEqual(encoded(package["catalogs"][name]),
                             encoded(current[name]),
                             "artifact must recover exact pinned 742890f bytes: " + name)
        self.assertEqual(package["report"]["delta"], {"identities": 5, "grades": 0, "states": 5,
            "properties": 5, "sources": 1,
            "categories": {"natural": 0, "metal": 1, "inorganic": 4, "polymer": 0, "composite": 0}})
        self.assertEqual(package["report"]["after"]["categories"],
                         {"natural": 1010, "metal": 15, "inorganic": 23, "polymer": 14, "composite": 3})
        new_property_ids = {identifier for batch in package["report"]["batches"]
                            for identifier in batch["added_ids"]["properties"]}
        self.assertEqual(len(new_property_ids), 5)
        for prop in current["properties"]["records"]:
            if prop["id"] in new_property_ids:
                self.assertTrue(prop["evidence"])
                expected_unit = "kg/m^3" if prop["id"].startswith("refprop_watanabe2026_") else "g/cm^3"
                self.assertEqual(prop["reported_value"]["unit_code"], expected_unit)
                self.assertFalse(prop["verification"]["independent_scientific_review"])
                self.assertFalse(prop["verification"]["raw_data_reanalysis"])
                self.assertEqual(prop["evaluation_support"], "catalog_only")
        # Reuse the exact adjusted runtime rows to verify ordinary append
        # idempotency independently of the command's immutable-output behavior.
        for append in append_packets:
            for table in ("properties", "sources"):
                runtime = {row["id"]: row for row in current[table]["records"]}
                append[table]["records"] = [runtime[row["id"]] for row in append[table]["records"]]
            self.assertEqual(merge_material_catalogs(current["materials"], current["properties"],
                                                   current["sources"], append), current)


if __name__ == "__main__":
    unittest.main()
