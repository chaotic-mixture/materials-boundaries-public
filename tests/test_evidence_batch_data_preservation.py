"""Validate the complete PA12 append, its v2 replay and exact predecessor."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

import evidence_batch_data_preservation as bridge
from source_family_growth_preservation import (
    project_growth_catalogs, project_growth_catalog_bytes, project_growth_file,
)
from materials_boundaries.material_references import material_quota_coverage
from scripts.integrate_material_candidates import write_package

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "experimental/material-batches/20261019-pa12-source-family/integration.json"


class EvidenceBatchDataPreservationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.current = {key: json.loads((ROOT / "materials_boundaries/data" / filename).read_bytes())
                       for key, filename in bridge.FILES.items()}
        cls.current = project_growth_catalogs(cls.current)
        cls.baseline = bridge.recover_pre_evidence_batch_catalogs(cls.current)
        cls.ledger = bridge.load_ledger()

    def test_one_new_polymer_has_a_property_and_no_other_category_increment(self):
        coverage = material_quota_coverage(self.current["materials"], self.current["properties"], self.current["sources"])
        self.assertEqual(coverage["distinct_material_count"], 1084)
        self.assertEqual({key: value["admitted_unique_identity_count"] for key, value in coverage["classes"].items()},
                         {"natural": 1010, "metal": 22, "inorganic": 26, "polymer": 16, "composite": 10})
        self.assertEqual([key for key, value in coverage["classes"].items() if value["target_met"]], ["natural"])
        rows = bridge.appended_rows()
        self.assertEqual({key: len(value) for key, value in rows.items()},
                         {"identities": 1, "grades": 1, "states": 1, "properties": 1, "sources": 1})
        self.assertEqual(rows["states"][0]["property_ids"], [rows["properties"][0]["id"]])
        self.assertEqual(rows["properties"][0]["reported_value"]["number"], "43.72")
        self.assertFalse(rows["properties"][0]["verification"]["independent_scientific_review"])
        self.assertFalse(rows["properties"][0]["verification"]["raw_data_reanalysis"])

    def test_complete_predecessor_bytes_are_recovered_without_mutating_input(self):
        original = deepcopy(self.current)
        self.assertEqual(bridge.recover_pre_evidence_batch_catalogs(self.baseline), self.baseline)
        self.assertEqual(bridge.recover_pre_evidence_batch_catalogs(self.current), self.baseline)
        self.assertEqual(self.current, original)
        for key, filename in bridge.FILES.items():
            raw = (ROOT / "materials_boundaries/data" / filename).read_bytes()
            raw = project_growth_catalog_bytes(filename, raw)
            previous = bridge.pre_evidence_batch_catalog_bytes(filename, raw)
            self.assertEqual(bridge.digest(previous), self.ledger["baseline_sha256"][key])
            self.assertEqual(previous, bridge.serialized(self.baseline[key]))
            self.assertEqual(bridge.pre_evidence_batch_catalog_bytes(filename, previous), previous)

    def test_partial_duplicate_or_changed_additions_are_rejected(self):
        for name, (table, field) in bridge.TABLES.items():
            wanted = bridge.appended_rows()[name][0]["id"]
            for mutation in ("missing", "duplicate", "changed"):
                graph = deepcopy(self.current)
                index = next(i for i, row in enumerate(graph[table][field]) if row["id"] == wanted)
                if mutation == "missing":
                    graph[table][field].pop(index)
                elif mutation == "duplicate":
                    graph[table][field].append(deepcopy(graph[table][field][index]))
                else:
                    graph[table][field][index]["unreviewed"] = True
                with self.subTest(collection=name, mutation=mutation):
                    with self.assertRaisesRegex(AssertionError, "complete pinned addition"):
                        bridge.recover_pre_evidence_batch_catalogs(graph)

    def test_unrelated_rows_metadata_and_order_cannot_be_hidden_by_recovery(self):
        for table, field in bridge.TABLES.values():
            graph = deepcopy(self.current)
            graph[table][field].append({"id": "unrelated_unreviewed"})
            with self.subTest(table=table, field=field):
                with self.assertRaisesRegex(AssertionError, "predecessor catalog bytes changed"):
                    bridge.recover_pre_evidence_batch_catalogs(graph)
        for table in bridge.FILES:
            graph = deepcopy(self.current)
            graph[table]["schema_version"] = "999.0.0"
            with self.assertRaisesRegex(AssertionError, "predecessor catalog bytes changed"):
                bridge.recover_pre_evidence_batch_catalogs(graph)
        graph = deepcopy(self.current)
        graph["materials"]["identities"].insert(0, graph["materials"]["identities"].pop())
        with self.assertRaisesRegex(AssertionError, "successor catalog order or bytes"):
            bridge.recover_pre_evidence_batch_catalogs(graph)

    def test_v2_packet_replay_matches_runtime_and_repeat_has_no_increment(self):
        self.assertEqual(json.loads(MANIFEST.read_bytes())["schema"], "experimental-material-integration/2")
        with tempfile.TemporaryDirectory() as directory:
            baseline = Path(directory) / "baseline"
            baseline.mkdir()
            for key, filename in bridge.FILES.items():
                (baseline / filename).write_bytes(bridge.serialized(self.baseline[key]))
            output = Path(directory) / "integration.json"
            package, created = write_package(baseline, MANIFEST, output)
            self.assertTrue(created)
            saved = output.read_bytes(), output.stat().st_mtime_ns
            repeated, created = write_package(baseline, MANIFEST, output)
            self.assertFalse(created)
            self.assertEqual(repeated, package)
            self.assertEqual((output.read_bytes(), output.stat().st_mtime_ns), saved)
            self.assertEqual(package["catalogs"], self.current)
            self.assertEqual(package["report"]["delta"], {
                "identities": 1, "grades": 1, "states": 1, "properties": 1, "sources": 1,
                "categories": {"natural": 0, "metal": 0, "inorganic": 0, "polymer": 1, "composite": 0}})
            self.assertEqual(package["report"]["formal_admitted_delta"], 0)
            self.assertEqual(package["report"]["released_main_count"], 1081)
            self.assertTrue(package["report"]["pending_gates"])
            for key, filename in bridge.FILES.items():
                self.assertEqual(bridge.serialized(package["catalogs"][key]),
                                 project_growth_catalog_bytes(filename, (ROOT / "materials_boundaries/data" / filename).read_bytes()))

    def test_readme_and_resource_bridges_reject_unknown_byte_images(self):
        current = (ROOT / "README.md").read_bytes()
        current = project_growth_file("README.md", current)
        previous = bridge.pre_evidence_batch_readme_bytes(current)
        self.assertEqual(bridge.digest(previous), self.ledger["readme"]["previous_sha256"])
        self.assertIn(b"**1083 material identities**", previous)
        self.assertIn(b"**1084 material identities**", current)
        self.assertEqual(bridge.pre_evidence_batch_readme_bytes(previous), previous)
        for raw in (current + b"!", current[:-1], b"unknown", current.decode("utf-8"), bytearray(current)):
            with self.assertRaises(AssertionError):
                bridge.pre_evidence_batch_readme_bytes(raw)
        for filename in bridge.FILES.values():
            raw = (ROOT / "materials_boundaries/data" / filename).read_bytes()
            with self.assertRaises(AssertionError):
                bridge.pre_evidence_batch_catalog_bytes(filename, raw + b" ")


if __name__ == "__main__":
    unittest.main()
