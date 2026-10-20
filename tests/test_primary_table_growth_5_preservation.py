"""Six NR/nanoclay composites and exact finite successor recovery.

These checks preserve source transcription, precision and provenance limits.
They do not provide independent scientific review or change reuse permissions.
"""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import material_append_successors as successors
from material_append_history import (
    FILES, appended_rows, digest, encoded, graph_hashes, recover_catalogs,
    recover_file,
)
from materials_boundaries.material_references import material_quota_coverage
from scripts.integrate_material_candidates import write_package
from scripts.prepare_formulation_packet import write_packet

ROOT = Path(__file__).resolve().parents[1]
BATCH_ID = "bianchi-nr-nanoclay-20261020"
PREVIOUS_BATCH_ID = "mtibe-pbs-pbat-hybrids-20261019"
BATCH = ROOT / "experimental/material-batches" / BATCH_ID
SOURCE = "bianchi_2025_nr_nanoclay"
FACTS = {
    "bianchi2025_nr_1mmt": ("0.960", "0.003", "MMT", "1", "NR_1MMT"),
    "bianchi2025_nr_3mmt": ("0.973", "0.001", "MMT", "3", "NR_3MMT"),
    "bianchi2025_nr_5mmt": ("0.981", "0.005", "MMT", "5", "NR_5MMT"),
    "bianchi2025_nr_1ommt": ("0.959", "0.001", "O-MMT", "1", "NR_1O-MMT"),
    "bianchi2025_nr_3ommt": ("0.966", "0.001", "O-MMT", "3", "NR_3O-MMT"),
    "bianchi2025_nr_5ommt": ("0.971", "0.003", "O-MMT", "5", "NR_5O-MMT"),
}


class PrimaryTableGrowth5PreservationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ledger = successors.data_ledger(BATCH_ID)
        graph = {name: json.loads((ROOT / "materials_boundaries/data" / filename).read_bytes())
                 for name, filename in FILES.items()}
        cls.current = successors.project_successor_catalogs(graph, before=BATCH_ID)
        cls.baseline = recover_catalogs(ROOT, cls.current, cls.ledger)
        cls.additions = appended_rows(ROOT, cls.ledger)

    def test_six_nanoclay_composites_keep_density_and_statistical_limits(self):
        coverage = material_quota_coverage(self.current["materials"], self.current["properties"], self.current["sources"])
        self.assertEqual(coverage["distinct_material_count"], 1118)
        self.assertEqual({key: value["admitted_unique_identity_count"] for key, value in coverage["classes"].items()},
                         {"natural": 1010, "metal": 22, "inorganic": 49, "polymer": 18, "composite": 19})
        self.assertEqual({key: len(rows) for key, rows in self.additions.items()},
                         {"identities": 6, "grades": 0, "states": 6, "properties": 6, "sources": 0})
        identities = {row["id"]: row for row in self.additions["identities"]}
        states = {row["id"]: row for row in self.additions["states"]}
        self.assertEqual(set(identities), {"mat_" + stem for stem in FACTS})
        observed = set()
        for prop in self.additions["properties"]:
            state = states[prop["material_state_id"]]
            identity = state["identity_id"]
            stem = identity.removeprefix("mat_")
            number, amplitude, clay, phr, label = FACTS[stem]
            observed.add(stem)
            self.assertEqual(state["id"], "state_" + stem)
            self.assertEqual(prop["id"], "refprop_" + stem + "_mass_density")
            self.assertEqual(identities[identity]["category"], "composite")
            self.assertEqual(state["property_ids"], [prop["id"]])
            self.assertIsNone(state["grade_id"])
            self.assertEqual(prop["reported_value"]["number"], number)
            self.assertEqual(prop["reported_value"]["value_text"], number)
            self.assertEqual(prop["reported_value"]["unit_code"], "g/cm^3")
            self.assertEqual(prop["quantity"], "mass_density")
            self.assertEqual(prop["reporting_basis"], "reported_summary")
            self.assertEqual(prop["summary_statistic"], "reported_value")
            self.assertEqual(prop["determination_basis"], "source_reports_measurement")
            self.assertEqual(prop["evidence_kind"], "published_experimental_reference")
            self.assertEqual(prop["density_basis"], "not_stated")
            self.assertEqual(prop["sample_count"]["value"], 3)
            self.assertEqual(prop["sample_count"]["relation"], "exact")
            self.assertEqual(prop["uncertainty"]["type"], "reported_plus_minus_unspecified")
            self.assertEqual(prop["uncertainty_status"], "reported_plus_minus_unspecified")
            self.assertEqual(prop["uncertainty"]["number"], amplitude)
            self.assertEqual(prop["uncertainty"]["value_text"], amplitude)
            self.assertEqual(prop["uncertainty"]["unit_code"], "g/cm^3")
            self.assertIsNone(prop["uncertainty"]["coverage_factor"])
            self.assertIsNone(prop["uncertainty"]["confidence_level"])
            self.assertEqual(prop["conditions"]["temperature"]["text"],
                             "Room temperature; numerical temperature unspecified")
            self.assertEqual(prop["conditions"]["conditioning"]["status"], "not_reported_in_inspected_source")
            self.assertIsNone(prop["conditions"]["conditioning"]["text"])
            self.assertEqual(prop["conditions"]["loading_rate"]["status"], "not_applicable")
            self.assertIsNone(prop["method_definition"]["extraction_window"])
            self.assertEqual(prop["conditions"]["test_standard"]["text"], "ASTM D792")
            composition = state["state"]["composition_or_purity"]["text"]
            self.assertIn("phr = parts per hundred rubber", composition)
            self.assertIn("SMR 10 natural rubber 100.0", composition)
            self.assertIn("sulfur 1.5; ZnO 5.0; stearic acid 2.0; ZDBC 0.7", composition)
            self.assertIn(clay + " " + phr + ".0", composition)
            self.assertEqual(state["source_designation"], label)
            self.assertIn("modifier identity/amount in the finished composite", prop["scope_note"])
            self.assertIn("are not established within the selected article-authored evidence", prop["scope_note"])
            self.assertIn("No producer-derived Table 7 density, spacing, modifier structure or supplier specification is imported", prop["scope_note"])
            if stem == "bianchi2025_nr_3mmt":
                self.assertIn("NR_3MMsT", {alias["text"] for alias in state["aliases"]})
                self.assertIn("NR_3MMsT", prop["evidence"][0]["locator"])
                discrepancies = json.dumps(prop["source_discrepancies"], ensure_ascii=False)
                self.assertIn("NR_3MMsT", discrepancies)
                self.assertIn("NR_3MMT", discrepancies)
            statistical = next(row["fact"] for row in prop["conditions"]["additional_conditions"]
                               if row["name"] == "statistical_scope")
            self.assertEqual(statistical["status"], "not_reported_in_inspected_source")
            self.assertIn("mechanical", statistical["notes"])
            self.assertEqual(prop["source_id"], SOURCE)
            self.assertEqual(prop["source_document"]["sha256"], "2e729bb58b361568d27ab772ec1c031648cb6a858f58a6e4ece9ce45b74c3ea2")
            self.assertFalse(prop["verification"]["independent_scientific_review"])
            self.assertFalse(prop["verification"]["raw_data_reanalysis"])
        self.assertEqual(observed, set(FACTS))
        self.assertEqual(self.current["sources"], self.baseline["sources"])
        self.assertEqual(self.current["materials"]["grades"], self.baseline["materials"]["grades"])
        self.assertEqual(len(self.current["sources"]["records"]), 116)
        self.assertEqual(len(self.current["materials"]["grades"]), 21)
        source = next(row for row in self.current["sources"]["records"] if row["id"] == SOURCE)
        canonical = (json.dumps(source, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
                                allow_nan=False) + "\n").encode("utf-8")
        self.assertEqual(digest(canonical), "16404406aa2c9a98f15dd099fec5747f6dea02250b5c817035b162b59a1f7865")
        self.assertEqual(source["license"]["identifier"], "CC-BY-4.0")

    def test_exact_898_recovery_rejects_partial_duplicate_unit_and_source_drift(self):
        self.assertEqual(self.ledger["baseline_commit"], "8981840519f611e62490ce4e9a614381201fe7e3")
        self.assertEqual(graph_hashes(self.current), self.ledger["current_sha256"])
        self.assertEqual(graph_hashes(self.baseline), self.ledger["baseline_sha256"])
        saved = encoded(self.current)
        self.assertEqual(recover_catalogs(ROOT, self.baseline, self.ledger), self.baseline)
        self.assertEqual(recover_catalogs(ROOT, self.current, self.ledger), self.baseline)
        self.assertEqual(encoded(self.current), saved)
        variants = {}
        graph = variants["partial state"] = deepcopy(self.current)
        wanted = self.additions["states"][-1]["id"]
        graph["materials"]["records"] = [row for row in graph["materials"]["records"] if row["id"] != wanted]
        graph = variants["duplicate identity"] = deepcopy(self.current)
        graph["materials"]["identities"].append(deepcopy(self.additions["identities"][0]))
        graph = variants["changed unit"] = deepcopy(self.current)
        wanted = self.additions["properties"][0]["id"]
        next(row for row in graph["properties"]["records"] if row["id"] == wanted)["reported_value"]["unit_code"] = "MPa"
        graph = variants["source rights drift"] = deepcopy(self.current)
        next(row for row in graph["sources"]["records"] if row["id"] == SOURCE)["license"]["identifier"] = "CC0-1.0"
        graph = variants["unexpected source append"] = deepcopy(self.current)
        graph["sources"]["records"].append({"id": "unreviewed_source"})
        graph = variants["unrelated predecessor drift"] = deepcopy(self.baseline)
        graph["materials"]["schema_version"] = "999.0.0"
        for label, graph in variants.items():
            with self.subTest(mutation=label), self.assertRaises(AssertionError):
                recover_catalogs(ROOT, graph, self.ledger)
        with self.assertRaises(AssertionError):
            successors.project_successor_catalogs(variants["partial state"])

    def test_compiler_and_integrator_replay_preserve_immutable_artifacts(self):
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
                "identities": 6, "grades": 0, "states": 6, "properties": 6, "sources": 0,
                "categories": {"natural": 0, "metal": 0, "inorganic": 0, "polymer": 0, "composite": 6}})
            self.assertEqual(package["report"]["formal_admitted_delta"], 0)
            self.assertEqual(package["report"]["released_main_count"], 1081)

    def test_selected_catalog_bytes_and_legacy_chain_remain_exact(self):
        import evidence_batch_data_preservation as old
        previous = successors.data_ledger(PREVIOUS_BATCH_ID)
        before_previous = recover_catalogs(ROOT, self.baseline, previous)
        self.assertEqual(successors.project_successor_catalogs(self.current, before=PREVIOUS_BATCH_ID), self.baseline)
        current_raw = successors.project_successor_catalog_bytes(
            "materials.json", (ROOT / "materials_boundaries/data/materials.json").read_bytes(), before=BATCH_ID)
        previous_raw = encoded(self.baseline["materials"])
        self.assertEqual(successors.project_successor_catalog_bytes(
            "materials.json", current_raw, before=PREVIOUS_BATCH_ID), previous_raw)
        # Align an older raw table with the current whole disk graph before
        # reversing the Mtibe append; include no older raw-byte matrix here.
        self.assertEqual(successors.project_successor_catalog_bytes(
            "materials.json", previous_raw, before="nbs-binary-oxide-density-20261019"),
            encoded(before_previous["materials"]))
        saved = encoded(self.current)
        oldest = old.recover_pre_evidence_batch_catalogs(self.current)
        self.assertEqual(graph_hashes(oldest), old.load_ledger()["baseline_sha256"])
        self.assertEqual(encoded(self.current), saved)

    def test_finite_files_and_registry_selection_keep_old_pins(self):
        self.assertEqual(successors.DATA_4_SHA256, "d57a1014e6d9e66f3f6c031e3a56abda909acc924fb9ab16835948989f4ce89c")
        self.assertEqual(successors.FILE_4_SHA256, "a0bd763d3524ce9f453d53cc060c3ec993a69c011450db0a00bc76b13597e16b")
        self.assertEqual(successors.data_ledger(BATCH_ID), self.ledger)
        newest = successors.FROZEN_SUCCESSORS[0]["batch_id"]
        self.assertEqual(successors.data_ledgers(before=newest), [])
        self.assertEqual(successors.data_ledgers(before=PREVIOUS_BATCH_ID),
                         [*successors.data_ledgers(before=BATCH_ID), self.ledger])
        entries = successors.file_ledger(BATCH_ID)["updates"]
        self.assertEqual(set(entries), {"README.md", ".github/workflows/ci.yml"})
        for filename, entry in entries.items():
            raw = successors.project_successor_file(filename, (ROOT / filename).read_bytes(), before=BATCH_ID)
            previous = recover_file(raw, entry)
            self.assertEqual(digest(raw), entry["sha256"])
            self.assertEqual(digest(previous), entry["previous_sha256"])
            self.assertEqual(successors.project_successor_file(filename, raw, before=PREVIOUS_BATCH_ID), previous)
            self.assertEqual(recover_file(previous, entry), previous)
            with self.subTest(filename=filename), self.assertRaises(AssertionError):
                recover_file(raw + b"!", entry)
        with self.assertRaises(AssertionError):
            successors.data_ledger("unknown-unreviewed-batch")
        with self.assertRaises(AssertionError):
            successors.project_successor_file("README.md", b"", before="unknown-unreviewed-batch")
        with patch.object(successors, "FROZEN_SUCCESSORS", successors.FROZEN_SUCCESSORS * 2):
            with self.assertRaises(AssertionError):
                successors.data_ledger()
        with patch.object(successors, "FROZEN_SUCCESSORS", tuple(reversed(successors.FROZEN_SUCCESSORS))):
            with self.assertRaisesRegex(AssertionError, "not adjacent or ordered"):
                successors.project_successor_catalogs(self.current)


if __name__ == "__main__":
    unittest.main()
