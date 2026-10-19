"""Eight selected NBS density rows and exact finite successor integration.

Source transcription is separately reviewed. These offline checks preserve its
values and qualifications; they do not perform scientific or licensing review.
"""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import material_append_successors as successors
import pur_formulation_preservation as pur
import source_family_growth_preservation as growth
from material_append_history import (
    FILES, TABLES, appended_rows, digest, encoded, graph_hashes, load_frozen,
    project_catalog_chain, project_file_chain, recover_catalogs, recover_file,
)
from materials_boundaries.material_references import material_quota_coverage
from scripts.integrate_material_candidates import write_package
from scripts.prepare_formulation_packet import write_packet

ROOT = Path(__file__).resolve().parents[1]
BATCH_ID = "nbs-salt-densities-20261019"
BATCH = ROOT / "experimental/material-batches" / BATCH_ID
SOURCE = "swanson_tatge_1953_nbs_circ539v1"
FACTS = {
    "mat_nbs1953_hg2cl2": ("7.176", "26 degrees C"),
    "mat_nbs1953_hgcl2": ("5.49", "26 degrees C"),
    "mat_nbs1953_hgi2": ("6.325", "26 degrees C"),
    "mat_nbs1953_pbfcl": ("7.13", "26 degrees C"),
    "mat_nbs1953_kcn": ("1.555", "25 degrees C"),
    "mat_nbs1953_nacn": ("1.591", "26 degrees C"),
    "mat_nbs1953_sr_no3_2": ("2.986", "26 degrees C"),
    "mat_nbs1953_ba_no3_2": ("3.244", "26 degrees C"),
}


class PrimaryTableGrowthPreservationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ledger = successors.data_ledger(BATCH_ID)
        graph = {name: json.loads((ROOT / "materials_boundaries/data" / filename).read_bytes())
                 for name, filename in FILES.items()}
        # Keep this batch's historical assertions if a later frozen descriptor
        # is prepended; never silently change this batch's count or fact oracle.
        cls.current = successors.project_successor_catalogs(graph, before=BATCH_ID)
        cls.baseline = recover_catalogs(ROOT, cls.current, cls.ledger)
        cls.additions = appended_rows(ROOT, cls.ledger)

    def test_eight_salts_preserve_density_conditions_and_phase_qualifications(self):
        coverage = material_quota_coverage(self.current["materials"], self.current["properties"], self.current["sources"])
        self.assertEqual(coverage["distinct_material_count"], 1100)
        self.assertEqual({key: value["admitted_unique_identity_count"] for key, value in coverage["classes"].items()},
                         {"natural": 1010, "metal": 22, "inorganic": 40, "polymer": 18, "composite": 10})
        identities = {row["id"]: row for row in self.additions["identities"]}
        states = {row["id"]: row for row in self.additions["states"]}
        observed = {}
        for prop in self.additions["properties"]:
            state = states[prop["material_state_id"]]
            identity_id = state["identity_id"]
            self.assertEqual(identities[identity_id]["category"], "inorganic")
            self.assertEqual(state["property_ids"], [prop["id"]])
            self.assertIsNone(state["grade_id"])
            observed[identity_id] = (prop["reported_value"]["number"], prop["conditions"]["temperature"]["text"])
            self.assertEqual(prop["reported_value"]["value_text"], FACTS[identity_id][0])
            self.assertEqual(prop["reported_value"]["unit_code"], "g/cm^3")
            self.assertEqual(prop["quantity"], "mass_density")
            self.assertEqual(prop["density_basis"], "crystallographic")
            self.assertEqual(prop["evidence_kind"], "published_measurement_derived_reference")
            self.assertEqual(prop["determination_basis"], "source_reports_calculation")
            self.assertEqual(prop["method_definition"]["type"], "source_reported_crystallographic_derivation")
            self.assertEqual(prop["summary_statistic"], "reported_value")
            self.assertIsNone(prop["sample_count"]["value"])
            self.assertIsNone(prop["uncertainty"])
            self.assertEqual(prop["source_id"], SOURCE)
            self.assertEqual(prop["source_document"]["sha256"], "003b872fbe7d403d38bbd1d752568ee92a96bdb010b6e381bdc82566929e2a6c")
            self.assertFalse(prop["verification"]["independent_scientific_review"])
            self.assertFalse(prop["verification"]["raw_data_reanalysis"])
            if identity_id == "mat_nbs1953_nacn":
                self.assertIn("96.2", state["state"]["composition_or_purity"]["text"])
                self.assertIn("cubic", prop["scope_note"].casefold())
        self.assertEqual(observed, FACTS)

    def test_shared_source_and_exact_efd4_predecessor_remain_unchanged(self):
        self.assertEqual({key: len(rows) for key, rows in self.additions.items()},
                         {"identities": 8, "grades": 0, "states": 8, "properties": 8, "sources": 0})
        self.assertEqual(self.current["sources"], self.baseline["sources"])
        self.assertEqual(self.current["materials"]["grades"], self.baseline["materials"]["grades"])
        self.assertEqual(len(self.current["sources"]["records"]), 116)
        source = next(row for row in self.current["sources"]["records"] if row["id"] == SOURCE)
        source_raw = (json.dumps(source, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
                                 allow_nan=False) + "\n").encode("utf-8")
        self.assertEqual(digest(source_raw), "af69ed341f5d81b6cd651b984ce489462f8ea798dfa95a98ace78a91b153bade")
        self.assertIsNone(source["license"]["identifier"])
        self.assertEqual(graph_hashes(self.baseline), self.ledger["baseline_sha256"])
        self.assertEqual(graph_hashes(self.current), self.ledger["current_sha256"])
        saved = encoded(self.current)
        self.assertEqual(recover_catalogs(ROOT, self.baseline, self.ledger), self.baseline)
        self.assertEqual(recover_catalogs(ROOT, self.current, self.ledger), self.baseline)
        self.assertEqual(encoded(self.current), saved)
        self.assertEqual(self.ledger["baseline_commit"], "efd4ca2a64c6b389c2a1fa9ba525f6fa77bbe93f")

    def test_partial_duplicate_or_unrelated_drift_is_refused(self):
        for name in ("identities", "states", "properties"):
            table, field = TABLES[name]
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
                    with self.assertRaises(AssertionError):
                        recover_catalogs(ROOT, graph, self.ledger)
                    with self.assertRaises(AssertionError):
                        growth.project_growth_catalogs(graph)
        for base in (self.current, self.baseline):
            for table in FILES:
                graph = deepcopy(base)
                graph[table]["schema_version"] = "999.0.0"
                with self.subTest(stage="current" if base is self.current else "parent", table=table):
                    with self.assertRaises(AssertionError):
                        recover_catalogs(ROOT, graph, self.ledger)
            graph = deepcopy(base)
            source = next(row for row in graph["sources"]["records"] if row["id"] == SOURCE)
            source["license"]["identifier"] = "CC0-1.0"
            with self.assertRaises(AssertionError):
                recover_catalogs(ROOT, graph, self.ledger)
        graph = deepcopy(self.current)
        graph["materials"]["identities"].insert(0, graph["materials"]["identities"].pop())
        with self.assertRaisesRegex(AssertionError, "successor catalog order or bytes"):
            recover_catalogs(ROOT, graph, self.ledger)

    def test_generator_and_integrator_repeat_preserve_exact_artifacts(self):
        with tempfile.TemporaryDirectory() as directory:
            baseline = Path(directory) / "baseline"
            baseline.mkdir()
            for name, filename in FILES.items():
                (baseline / filename).write_bytes(encoded(self.baseline[name]))
            candidate = Path(directory) / "candidate.json"
            packet, created = write_packet(baseline, BATCH / "packet-spec.json", candidate)
            self.assertTrue(created)
            self.assertEqual(packet, json.loads((BATCH / "prepared-packet.json").read_bytes()))
            self.assertTrue(packet["report"]["handoff_ready"])
            self.assertEqual(packet["report"]["formal_admitted_delta"], 0)
            saved = candidate.read_bytes(), candidate.stat().st_mtime_ns
            self.assertFalse(write_packet(baseline, BATCH / "packet-spec.json", candidate)[1])
            self.assertEqual((candidate.read_bytes(), candidate.stat().st_mtime_ns), saved)
            output = Path(directory) / "integration.json"
            package, created = write_package(baseline, BATCH / "integration.json", output)
            self.assertTrue(created)
            self.assertEqual(package["catalogs"], self.current)
            saved = output.read_bytes(), output.stat().st_mtime_ns
            self.assertFalse(write_package(baseline, BATCH / "integration.json", output)[1])
            self.assertEqual((output.read_bytes(), output.stat().st_mtime_ns), saved)
            self.assertEqual(package["report"]["delta"], {
                "identities": 8, "grades": 0, "states": 8, "properties": 8, "sources": 0,
                "categories": {"natural": 0, "metal": 0, "inorganic": 8, "polymer": 0, "composite": 0}})
            self.assertEqual(package["report"]["formal_admitted_delta"], 0)
            self.assertEqual(package["report"]["released_main_count"], 1081)

    def test_catalog_byte_projection_aligns_all_historical_graphs(self):
        import evidence_batch_data_preservation as old
        parent2509 = recover_catalogs(ROOT, self.baseline, pur.data_ledger())
        parentc901 = recover_catalogs(ROOT, parent2509, growth.data_ledger())
        pre_evidence = old.recover_pre_evidence_batch_catalogs(parentc901)
        for name, filename in FILES.items():
            raw = successors.project_successor_catalog_bytes(
                filename, (ROOT / "materials_boundaries/data" / filename).read_bytes(), before=BATCH_ID)
            parent_raw = encoded(self.baseline[name])
            self.assertEqual(successors.project_successor_catalog_bytes(filename, raw), parent_raw)
            for stage, image in (("current", raw), ("efd4", parent_raw),
                                 ("2509", encoded(parent2509[name])), ("c901", encoded(parentc901[name]))):
                with self.subTest(filename=filename, stage=stage):
                    self.assertEqual(growth.project_growth_catalog_bytes(filename, image), encoded(parentc901[name]))
                    self.assertEqual(old.pre_evidence_batch_catalog_bytes(filename, image), encoded(pre_evidence[name]))
            for bad in (raw + b"!", raw[:-1], b"{}"):
                with self.subTest(filename=filename, mutation=bad[-1:]):
                    with self.assertRaises(AssertionError):
                        old.pre_evidence_batch_catalog_bytes(filename, bad)

    def test_ordered_registry_reaches_efd4_2509_c901_and_12cb(self):
        import evidence_batch_data_preservation as old
        before = encoded(self.current)
        self.assertEqual(successors.project_successor_catalogs(self.current), self.baseline)
        self.assertEqual(successors.project_successor_catalogs(self.current, before=BATCH_ID), self.current)
        self.assertEqual(successors.data_ledger(BATCH_ID), self.ledger)
        parent2509 = pur.recover_pre_pur_catalogs(self.current)
        self.assertEqual(graph_hashes(parent2509), pur.data_ledger()["baseline_sha256"])
        parentc901 = growth.recover_growth_catalogs(self.current)
        self.assertEqual(graph_hashes(parentc901), growth.data_ledger()["baseline_sha256"])
        predecessor = old.recover_pre_evidence_batch_catalogs(self.current)
        self.assertEqual(graph_hashes(predecessor), old.load_ledger()["baseline_sha256"])
        self.assertEqual(encoded(self.current), before)
        self.assertEqual(pur.DATA_SHA256, "541a4e325834ed992246489846bcfcf83480bfb86494ec2a212d78de821bf167")
        self.assertEqual(pur.FILE_SHA256, "da273be57628bc69a55ae3cacaea4c07370fa56cd2dec6678f062b551acf7dba")
        self.assertEqual(growth.DATA_SHA256, "9dfc8d71e89041f05e11a870ad29aea34cb3ab90586bcea8f1d717adc9878ac3")
        self.assertEqual(growth.FILE_SHA256, "3fa801355a51e2c369f7f5963cefc69ab7995912903ec10041959d3f6b0d8e76")

    def test_finite_file_chain_preserves_old_pins_and_rejects_drift(self):
        import evidence_batch_workflow_preservation as old
        for filename, entry in successors.file_ledger(BATCH_ID)["updates"].items():
            raw = successors.project_successor_file(filename, (ROOT / filename).read_bytes(), before=BATCH_ID)
            previous = recover_file(raw, entry)
            self.assertEqual(digest(raw), entry["sha256"])
            self.assertEqual(digest(previous), entry["previous_sha256"])
            self.assertEqual(successors.project_successor_file(filename, raw), previous)
            self.assertEqual(successors.project_successor_file(filename, previous), previous)
            for bad in (raw + b"!", raw[:-1], b"unknown", bytearray(raw)):
                with self.subTest(filename=filename, mutation=type(bad).__name__):
                    with self.assertRaises(AssertionError):
                        recover_file(bad, entry)
        for filename, entry in old.validate_ledger(old.load_ledger()).items():
            raw = (ROOT / filename).read_bytes()
            self.assertEqual(digest(old.pre_evidence_batch_workflow_bytes(filename, raw)), entry["previous_sha256"])
            with self.assertRaises(AssertionError):
                old.pre_evidence_batch_workflow_bytes(filename, raw + b"!")

    def test_frozen_inventory_registry_selection_and_chain_order_are_closed(self):
        with self.assertRaises(AssertionError):
            load_frozen(ROOT, successors.DATA_LEDGER, "0" * 64)
        for reader in (successors.data_ledger, successors.file_ledger):
            with self.assertRaises(AssertionError):
                reader("unknown-unreviewed-batch")
            with patch.object(successors, "FROZEN_SUCCESSORS", successors.FROZEN_SUCCESSORS * 2):
                with self.assertRaises(AssertionError):
                    reader()
        with self.assertRaises(AssertionError):
            successors.project_successor_catalogs(self.current, before="unknown-unreviewed-batch")
        for mutation in ("digest", "missing", "duplicate", "reused_source"):
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
        for chain in ([pur.data_ledger(), self.ledger], [self.ledger, self.ledger]):
            with self.assertRaisesRegex(AssertionError, "not adjacent or ordered"):
                project_catalog_chain(ROOT, self.current, chain)
        raw = (ROOT / ".github/workflows/ci.yml").read_bytes()
        with self.assertRaisesRegex(AssertionError, "not adjacent or ordered"):
            project_file_chain(".github/workflows/ci.yml", raw, [pur.file_ledger(), successors.file_ledger(BATCH_ID)])


if __name__ == "__main__":
    unittest.main()
