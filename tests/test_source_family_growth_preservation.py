"""Check six source-qualified oxides and exact, repeatable append recovery."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

import source_family_growth_preservation as history
from pur_formulation_preservation import project_pur_catalogs, project_pur_file
from material_append_history import appended_rows, recover_catalogs, recover_file
from materials_boundaries.material_references import material_quota_coverage
from scripts.prepare_formulation_packet import write_packet
from scripts.integrate_material_candidates import write_package

ROOT = Path(__file__).resolve().parents[1]
BATCH = ROOT / "experimental/material-batches/nbs-oxide-density-20261019"
SOURCE = "swanson_tatge_1953_nbs_circ539v1"
FACTS = {"beo": ("3.008", "26 degrees C"), "mgo": ("3.581", "25 degrees C"),
         "cao": ("3.345", "27 degrees C"), "tio2": ("4.250", "26 degrees C"),
         "cuo": ("6.51", "26 degrees C"), "ceo2": ("7.215", "26 degrees C")}


class SourceFamilyGrowthPreservationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ledger = history.data_ledger()
        cls.current = {name: json.loads((ROOT / "materials_boundaries/data" / filename).read_bytes())
                       for name, filename in history.FILES.items()}
        cls.current = project_pur_catalogs(cls.current)
        cls.baseline = history.recover_growth_catalogs(cls.current)
        cls.additions = appended_rows(ROOT, cls.ledger)

    def test_six_oxide_values_conditions_and_category_counts(self):
        coverage = material_quota_coverage(self.current["materials"], self.current["properties"], self.current["sources"])
        self.assertEqual(coverage["distinct_material_count"], 1090)
        self.assertEqual({key: value["admitted_unique_identity_count"] for key, value in coverage["classes"].items()},
                         {"natural": 1010, "metal": 22, "inorganic": 32, "polymer": 16, "composite": 10})
        self.assertEqual([key for key, value in coverage["classes"].items() if value["target_met"]], ["natural"])
        states = {row["id"]: row for row in self.additions["states"]}
        actual = {}
        for prop in self.additions["properties"]:
            state = states[prop["material_state_id"]]
            identity = state["identity_id"].removeprefix("mat_nbs1953_")
            actual[identity] = (prop["reported_value"]["number"], prop["conditions"]["temperature"]["text"])
            self.assertEqual(state["property_ids"], [prop["id"]])
            self.assertIsNone(state["grade_id"])
            self.assertEqual(prop["source_id"], SOURCE)
            self.assertEqual(prop["quantity"], "mass_density")
            self.assertEqual(prop["reported_value"]["unit_code"], "g/cm^3")
            self.assertEqual(prop["density_basis"], "crystallographic")
            self.assertEqual(prop["determination_basis"], "source_reports_calculation")
            self.assertEqual(prop["summary_statistic"], "reported_value")
            self.assertIsNone(prop["uncertainty"])
            self.assertFalse(prop["verification"]["independent_scientific_review"])
            self.assertFalse(prop["verification"]["raw_data_reanalysis"])
            self.assertEqual(prop["source_document"]["sha256"], "003b872fbe7d403d38bbd1d752568ee92a96bdb010b6e381bdc82566929e2a6c")
        self.assertEqual(actual, FACTS)

    def test_shared_source_and_complete_predecessor_are_preserved(self):
        self.assertEqual({key: len(rows) for key, rows in self.additions.items()},
                         {"identities": 6, "grades": 0, "states": 6, "properties": 6, "sources": 0})
        self.assertEqual(self.current["sources"], self.baseline["sources"])
        self.assertEqual(len(self.current["sources"]["records"]), 116)
        self.assertEqual(self.current["materials"]["grades"], self.baseline["materials"]["grades"])
        saved = history.encoded(self.current)
        self.assertEqual(history.graph_hashes(self.baseline), self.ledger["baseline_sha256"])
        self.assertEqual(history.recover_growth_catalogs(self.baseline), self.baseline)
        self.assertEqual(history.recover_growth_catalogs(self.current), self.baseline)
        self.assertEqual(history.encoded(self.current), saved)
        source = next(row for row in self.current["sources"]["records"] if row["id"] == SOURCE)
        self.assertIsNone(source["license"]["identifier"])
        self.assertEqual(source["license"]["status"], "NIST_employee_authored_US_government_work_with_express_worldwide_reuse_notice")

    def test_partial_duplicate_or_changed_append_is_rejected(self):
        for name in ("identities", "states", "properties"):
            table, field = history.TABLES[name]
            wanted = self.additions[name][-1]["id"]
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
                        history.recover_growth_catalogs(graph)

    def test_unrelated_metadata_and_order_are_rejected(self):
        for table in history.FILES:
            graph = deepcopy(self.current)
            graph[table]["schema_version"] = "999.0.0"
            with self.assertRaisesRegex(AssertionError, "predecessor catalog bytes changed"):
                history.recover_growth_catalogs(graph)
        graph = deepcopy(self.current)
        source = next(row for row in graph["sources"]["records"] if row["id"] == SOURCE)
        source["license"]["identifier"] = "CC0-1.0"
        with self.assertRaisesRegex(AssertionError, "predecessor catalog bytes changed"):
            history.recover_growth_catalogs(graph)
        graph = deepcopy(self.current)
        graph["materials"]["identities"].insert(0, graph["materials"]["identities"].pop())
        with self.assertRaisesRegex(AssertionError, "successor catalog order or bytes"):
            history.recover_growth_catalogs(graph)

    def test_generator_and_v2_replay_are_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            baseline = Path(directory) / "baseline"
            baseline.mkdir()
            for name, filename in history.FILES.items():
                (baseline / filename).write_bytes(history.encoded(self.baseline[name]))
            candidate = Path(directory) / "candidate.json"
            packet, created = write_packet(baseline, BATCH / "packet-spec.json", candidate)
            self.assertTrue(created)
            saved = candidate.read_bytes(), candidate.stat().st_mtime_ns
            self.assertEqual(packet, json.loads((BATCH / "prepared-packet.json").read_bytes()))
            self.assertFalse(write_packet(baseline, BATCH / "packet-spec.json", candidate)[1])
            self.assertEqual((candidate.read_bytes(), candidate.stat().st_mtime_ns), saved)
            output = Path(directory) / "integration.json"
            package, created = write_package(baseline, BATCH / "integration.json", output)
            self.assertTrue(created)
            saved = output.read_bytes(), output.stat().st_mtime_ns
            self.assertFalse(write_package(baseline, BATCH / "integration.json", output)[1])
            self.assertEqual((output.read_bytes(), output.stat().st_mtime_ns), saved)
            self.assertEqual(package["catalogs"], self.current)
            self.assertEqual(package["report"]["delta"], {
                "identities": 6, "grades": 0, "states": 6, "properties": 6, "sources": 0,
                "categories": {"natural": 0, "metal": 0, "inorganic": 6, "polymer": 0, "composite": 0}})
            self.assertEqual(package["report"]["formal_admitted_delta"], 0)
            self.assertEqual(package["report"]["released_main_count"], 1081)

    def test_all_finite_file_images_round_trip_and_reject_drift(self):
        for filename, entry in history.file_ledger()["updates"].items():
            raw = project_pur_file(filename, (ROOT / filename).read_bytes())
            previous = recover_file(raw, entry)
            self.assertEqual(history.digest(raw), entry["sha256"])
            self.assertEqual(history.digest(previous), entry["previous_sha256"])
            self.assertEqual(recover_file(previous, entry), previous)
            for bad in (raw + b"!", raw[:-1], b"unknown", bytearray(raw)):
                with self.subTest(filename=filename, mutation=type(bad).__name__):
                    with self.assertRaises(AssertionError):
                        recover_file(bad, entry)

    def test_pinned_packet_and_inventory_cannot_be_substituted(self):
        for mutation in ("digest", "missing", "duplicate", "reused-source"):
            ledger = deepcopy(self.ledger)
            packet = ledger["packets"][0]
            if mutation == "digest":
                packet["sha256"] = "0" * 64
            elif mutation == "missing":
                packet["added_ids"]["identities"].pop()
            elif mutation == "duplicate":
                packet["added_ids"]["states"].append(packet["added_ids"]["states"][0])
            else:
                packet["added_ids"]["sources"].append(SOURCE)
            with self.subTest(mutation=mutation):
                with self.assertRaises(AssertionError):
                    recover_catalogs(ROOT, self.current, ledger)

    def test_old_data_and_workflow_layers_still_recover_exactly(self):
        import evidence_batch_data_preservation as old_data
        import evidence_batch_workflow_preservation as old_files
        previous = old_data.recover_pre_evidence_batch_catalogs(self.current)
        self.assertEqual(history.graph_hashes(previous), old_data.load_ledger()["baseline_sha256"])
        for filename, entry in old_files.validate_ledger(old_files.load_ledger()).items():
            raw = (ROOT / filename).read_bytes()
            self.assertEqual(history.digest(old_files.pre_evidence_batch_workflow_bytes(filename, raw)), entry["previous_sha256"])
        self.assertEqual(history.data_ledger()["baseline_commit"], history.BASELINE_COMMIT)


if __name__ == "__main__":
    unittest.main()
