"""Two explicit PUR formulations and finite, ordered historical recovery.

These checks preserve selected source facts and software boundaries. They do
not claim a new source retrieval, scientific review or measurement replication.
"""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

import pur_formulation_preservation as history
import source_family_growth_preservation as growth
import material_append_successors as successors
from material_append_history import (
    appended_rows, load_frozen, project_catalog_chain, project_file_chain,
    recover_catalogs, recover_file,
)
from materials_boundaries.material_references import material_quota_coverage
from scripts.integrate_material_candidates import write_package
from scripts.prepare_formulation_packet import write_packet

ROOT = Path(__file__).resolve().parents[1]
BATCH = ROOT / "experimental/material-batches/pur-formulations-20261019"
SOURCE = "ivdre_2024_lpo_rigid_pur"
FACTS = {
    "mat_ivdre2024_lpo2_rigid_pur": ("43.5", "Lupranol 3300 66 g; Lupranol 3422 34 g"),
    "mat_ivdre2024_spo3_rigid_pur": ("43.2", "SA-C_TOFA(50:50)/TMP 40 g; SA-E_ETOFA(50:50)/TMP 60 g"),
}


class PURFormulationPreservationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ledger = history.data_ledger()
        cls.current = {name: json.loads((ROOT / "materials_boundaries/data" / filename).read_bytes())
                       for name, filename in history.FILES.items()}
        cls.current = successors.project_successor_catalogs(cls.current)
        cls.baseline = history.recover_pre_pur_catalogs(cls.current)
        cls.additions = appended_rows(ROOT, cls.ledger)

    def test_two_formulations_preserve_reported_density_and_unknown_conditions(self):
        coverage = material_quota_coverage(self.current["materials"], self.current["properties"], self.current["sources"])
        self.assertEqual(coverage["distinct_material_count"], 1092)
        self.assertEqual({key: value["admitted_unique_identity_count"] for key, value in coverage["classes"].items()},
                         {"natural": 1010, "metal": 22, "inorganic": 32, "polymer": 18, "composite": 10})
        identities = {row["id"]: row for row in self.additions["identities"]}
        states = {row["id"]: row for row in self.additions["states"]}
        observed = {}
        for prop in self.additions["properties"]:
            state = states[prop["material_state_id"]]
            identity_id = state["identity_id"]
            value, composition = FACTS[identity_id]
            observed[identity_id] = prop["reported_value"]["number"]
            self.assertEqual(identities[identity_id]["category"], "polymer")
            self.assertEqual(state["property_ids"], [prop["id"]])
            self.assertIsNone(state["grade_id"])
            self.assertIn(composition, state["state"]["composition_or_purity"]["text"])
            self.assertEqual(prop["reported_value"]["value_text"], value)
            self.assertEqual(prop["reported_value"]["unit_code"], "kg/m^3")
            self.assertEqual(prop["quantity"], "mass_density")
            self.assertEqual(prop["density_basis"], "apparent")
            self.assertEqual(prop["determination_basis"], "source_reports_measurement")
            self.assertEqual(prop["summary_statistic"], "reported_value")
            self.assertEqual(prop["conditions"]["test_standard"]["text"], "ISO 845:2006")
            self.assertEqual(prop["conditions"]["temperature"]["status"], "not_reported_in_inspected_source")
            self.assertIsNone(prop["conditions"]["temperature"]["text"])
            self.assertIsNone(prop["sample_count"]["value"])
            self.assertIsNone(prop["uncertainty"])
            self.assertEqual(prop["source_id"], SOURCE)
            self.assertEqual(prop["source_document"]["sha256"], "4e0c1a91a9ae26d814576961a3805f9371b46498d4861fb578e7a413bb4c726d")
            self.assertTrue(prop["source_discrepancies"])
            self.assertFalse(prop["verification"]["independent_scientific_review"])
            self.assertFalse(prop["verification"]["raw_data_reanalysis"])
        self.assertEqual(observed, {identity: fact[0] for identity, fact in FACTS.items()})

    def test_shared_source_and_exact_2509_predecessor_remain_unchanged(self):
        self.assertEqual({key: len(rows) for key, rows in self.additions.items()},
                         {"identities": 2, "grades": 0, "states": 2, "properties": 2, "sources": 0})
        self.assertEqual(self.current["sources"], self.baseline["sources"])
        self.assertEqual(self.current["materials"]["grades"], self.baseline["materials"]["grades"])
        self.assertEqual(len(self.current["sources"]["records"]), 116)
        source = next(row for row in self.current["sources"]["records"] if row["id"] == SOURCE)
        self.assertEqual(source["license"], {"status": "explicit_reuse_license_verified", "identifier": "CC-BY-4.0"})
        self.assertEqual(history.graph_hashes(self.baseline), self.ledger["baseline_sha256"])
        self.assertEqual(history.graph_hashes(self.current), self.ledger["current_sha256"])
        saved = history.encoded(self.current)
        self.assertEqual(history.recover_pre_pur_catalogs(self.baseline), self.baseline)
        self.assertEqual(history.recover_pre_pur_catalogs(self.current), self.baseline)
        self.assertEqual(history.encoded(self.current), saved)
        self.assertEqual(self.ledger["baseline_commit"], "2509ee231edb62872ed323e8346895bd55c36c92")

    def test_partial_duplicate_or_unrelated_drift_is_refused(self):
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
                    with self.assertRaises(AssertionError):
                        history.recover_pre_pur_catalogs(graph)
                    with self.assertRaises(AssertionError):
                        growth.project_growth_catalogs(graph)
        for base in (self.current, self.baseline):
            for table in history.FILES:
                graph = deepcopy(base)
                graph[table]["schema_version"] = "999.0.0"
                with self.subTest(stage="current" if base is self.current else "parent", table=table):
                    with self.assertRaises(AssertionError):
                        history.recover_pre_pur_catalogs(graph)
            graph = deepcopy(base)
            source = next(row for row in graph["sources"]["records"] if row["id"] == SOURCE)
            source["license"]["identifier"] = "CC0-1.0"
            with self.assertRaises(AssertionError):
                history.recover_pre_pur_catalogs(graph)
        graph = deepcopy(self.current)
        graph["materials"]["identities"].insert(0, graph["materials"]["identities"].pop())
        with self.assertRaisesRegex(AssertionError, "successor catalog order or bytes"):
            history.recover_pre_pur_catalogs(graph)

    def test_generator_and_integrator_repeat_preserve_exact_artifacts(self):
        with tempfile.TemporaryDirectory() as directory:
            baseline = Path(directory) / "baseline"
            baseline.mkdir()
            for name, filename in history.FILES.items():
                (baseline / filename).write_bytes(history.encoded(self.baseline[name]))
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
                "identities": 2, "grades": 0, "states": 2, "properties": 2, "sources": 0,
                "categories": {"natural": 0, "metal": 0, "inorganic": 0, "polymer": 2, "composite": 0}})
            self.assertEqual(package["report"]["formal_admitted_delta"], 0)
            self.assertEqual(package["report"]["released_main_count"], 1081)

    def test_catalog_byte_projection_aligns_current_and_predecessor_graphs(self):
        import evidence_batch_data_preservation as old
        c901 = recover_catalogs(ROOT, self.baseline, growth.data_ledger())
        pre_evidence = old.recover_pre_evidence_batch_catalogs(c901)
        for name, filename in history.FILES.items():
            current_raw = successors.project_successor_catalog_bytes(
                filename, (ROOT / "materials_boundaries/data" / filename).read_bytes())
            parent_raw = history.encoded(self.baseline[name])
            c901_raw = history.encoded(c901[name])
            self.assertEqual(history.project_pur_catalog_bytes(filename, current_raw), parent_raw)
            self.assertEqual(history.project_pur_catalog_bytes(filename, parent_raw), parent_raw)
            for stage, raw in (("current", current_raw), ("2509", parent_raw), ("c901", c901_raw)):
                with self.subTest(filename=filename, stage=stage):
                    self.assertEqual(growth.project_growth_catalog_bytes(filename, raw), c901_raw)
                    self.assertEqual(old.pre_evidence_batch_catalog_bytes(filename, raw),
                                     history.encoded(pre_evidence[name]))
            for raw in (current_raw + b"!", current_raw[:-1], b"{}"):
                with self.subTest(filename=filename, mutation=raw[-1:]):
                    with self.assertRaises(AssertionError):
                        old.pre_evidence_batch_catalog_bytes(filename, raw)

    def test_ordered_chain_reaches_exact_c901_and_12cb_without_mutation(self):
        import evidence_batch_data_preservation as old
        before = history.encoded(self.current)
        c901 = project_catalog_chain(ROOT, self.current, [self.ledger, growth.data_ledger()])
        self.assertEqual(history.graph_hashes(c901), growth.data_ledger()["baseline_sha256"])
        self.assertEqual(growth.recover_growth_catalogs(self.current), c901)
        self.assertEqual(growth.recover_growth_catalogs(self.baseline), c901)
        predecessor = old.recover_pre_evidence_batch_catalogs(self.current)
        self.assertEqual(history.graph_hashes(predecessor), old.load_ledger()["baseline_sha256"])
        self.assertEqual(history.encoded(self.current), before)
        self.assertEqual(growth.DATA_SHA256, "9dfc8d71e89041f05e11a870ad29aea34cb3ab90586bcea8f1d717adc9878ac3")
        self.assertEqual(growth.FILE_SHA256, "3fa801355a51e2c369f7f5963cefc69ab7995912903ec10041959d3f6b0d8e76")

    def test_finite_file_chain_preserves_old_pins_and_rejects_drift(self):
        import evidence_batch_workflow_preservation as old
        for filename, entry in history.file_ledger()["updates"].items():
            raw = successors.project_successor_file(filename, (ROOT / filename).read_bytes())
            previous = recover_file(raw, entry)
            self.assertEqual(history.digest(raw), entry["sha256"])
            self.assertEqual(history.digest(previous), entry["previous_sha256"])
            self.assertEqual(history.project_pur_file(filename, raw), previous)
            self.assertEqual(history.project_pur_file(filename, previous), previous)
            for bad in (raw + b"!", raw[:-1], b"unknown", bytearray(raw)):
                with self.subTest(filename=filename, mutation=type(bad).__name__):
                    with self.assertRaises(AssertionError):
                        recover_file(bad, entry)
        for filename, entry in old.validate_ledger(old.load_ledger()).items():
            raw = (ROOT / filename).read_bytes()
            self.assertEqual(history.digest(old.pre_evidence_batch_workflow_bytes(filename, raw)),
                             entry["previous_sha256"])
            with self.assertRaises(AssertionError):
                old.pre_evidence_batch_workflow_bytes(filename, raw + b"!")

    def test_frozen_inventory_and_chain_order_cannot_be_substituted(self):
        with self.assertRaises(AssertionError):
            load_frozen(ROOT, history.DATA_LEDGER, "0" * 64)
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
        for chain in ([growth.data_ledger(), self.ledger], [self.ledger, self.ledger]):
            with self.assertRaisesRegex(AssertionError, "not adjacent or ordered"):
                project_catalog_chain(ROOT, self.current, chain)
        wrong_parent = deepcopy(self.ledger)
        wrong_parent["baseline_sha256"]["materials"] = "0" * 64
        with self.assertRaisesRegex(AssertionError, "not adjacent or ordered"):
            project_catalog_chain(ROOT, self.current, [wrong_parent, growth.data_ledger()])
        raw = (ROOT / ".github/workflows/ci.yml").read_bytes()
        with self.assertRaisesRegex(AssertionError, "not adjacent or ordered"):
            project_file_chain(".github/workflows/ci.yml", raw, [growth.file_ledger(), history.file_ledger()])


if __name__ == "__main__":
    unittest.main()
