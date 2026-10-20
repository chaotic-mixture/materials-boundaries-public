"""Three Mtibe hybrid composites and exact finite successor recovery.

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
BATCH_ID = "mtibe-pbs-pbat-hybrids-20261019"
PREVIOUS_BATCH_ID = "nbs-binary-oxide-density-20261019"
BATCH = ROOT / "experimental/material-batches" / BATCH_ID
SOURCE = "mtibe_2022_pbs_pbat_lignin_zno"
FACTS = {
    "mtibe2022_pbs_pbat_lignin5_zno": ("261.88", "14.78", "95/5/1.5"),
    "mtibe2022_pbs_pbat_lignin10_zno": ("304.52", "5.22", "90/10/1.5"),
    "mtibe2022_pbs_pbat_lignin15_zno": ("347.44", "16.92", "85/15/1.5"),
}


class PrimaryTableGrowth4PreservationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ledger = successors.data_ledger(BATCH_ID)
        graph = {name: json.loads((ROOT / "materials_boundaries/data" / filename).read_bytes())
                 for name, filename in FILES.items()}
        cls.current = successors.project_successor_catalogs(graph, before=BATCH_ID)
        cls.baseline = recover_catalogs(ROOT, cls.current, cls.ledger)
        cls.additions = appended_rows(ROOT, cls.ledger)

    def test_three_hybrids_keep_raw_formulations_and_measurement_limits(self):
        coverage = material_quota_coverage(self.current["materials"], self.current["properties"], self.current["sources"])
        self.assertEqual(coverage["distinct_material_count"], 1112)
        self.assertEqual({key: value["admitted_unique_identity_count"] for key, value in coverage["classes"].items()},
                         {"natural": 1010, "metal": 22, "inorganic": 49, "polymer": 18, "composite": 13})
        self.assertEqual({key: len(rows) for key, rows in self.additions.items()},
                         {"identities": 3, "grades": 0, "states": 3, "properties": 3, "sources": 0})
        identities = {row["id"]: row for row in self.additions["identities"]}
        states = {row["id"]: row for row in self.additions["states"]}
        self.assertEqual(set(identities), {"mat_" + stem for stem in FACTS})
        observed = set()
        for prop in self.additions["properties"]:
            state = states[prop["material_state_id"]]
            identity = state["identity_id"]
            stem = identity.removeprefix("mat_")
            number, amplitude, raw_ratio = FACTS[stem]
            observed.add(stem)
            self.assertEqual(state["id"], "state_" + stem)
            self.assertEqual(prop["id"], "refprop_" + stem + "_tensile_modulus")
            self.assertEqual(identities[identity]["category"], "composite")
            self.assertEqual(state["property_ids"], [prop["id"]])
            self.assertIsNone(state["grade_id"])
            self.assertEqual(prop["reported_value"]["number"], number)
            self.assertEqual(prop["reported_value"]["value_text"], number)
            self.assertEqual(prop["reported_value"]["unit_code"], "MPa")
            self.assertEqual(prop["quantity"], "tensile_modulus")
            self.assertEqual(prop["quantity_dimension"], "pressure")
            self.assertEqual(prop["reporting_basis"], "reported_summary")
            self.assertEqual(prop["summary_statistic"], "reported_value")
            self.assertEqual(prop["determination_basis"], "source_reports_measurement")
            self.assertEqual(prop["evidence_kind"], "published_experimental_reference")
            self.assertIsNone(prop["density_basis"])
            self.assertEqual(prop["sample_count"]["value"], 5)
            self.assertEqual(prop["sample_count"]["relation"], "exact")
            self.assertEqual(prop["uncertainty"]["type"], "reported_plus_minus_unspecified")
            self.assertEqual(prop["uncertainty_status"], "reported_plus_minus_unspecified")
            self.assertEqual(prop["uncertainty"]["number"], amplitude)
            self.assertEqual(prop["uncertainty"]["value_text"], amplitude)
            self.assertEqual(prop["uncertainty"]["unit_code"], "MPa")
            self.assertIsNone(prop["uncertainty"]["coverage_factor"])
            self.assertIsNone(prop["uncertainty"]["confidence_level"])
            self.assertEqual(prop["conditions"]["temperature"]["text"], "25 \u00b0C")
            self.assertEqual(prop["conditions"]["conditioning"]["text"], "48 h at 25 \u00b0C before tensile testing")
            self.assertEqual(prop["conditions"]["loading_rate"]["status"], "not_reported_in_inspected_source")
            self.assertIsNone(prop["method_definition"]["extraction_window"])
            composition = state["state"]["composition_or_purity"]["text"]
            for qualification in (raw_ratio, "101.5", "70/30, ratio basis unspecified",
                                  "ZnO denominator is unspecified", "No normalization is performed"):
                self.assertIn(qualification, composition)
            self.assertEqual(prop["source_id"], SOURCE)
            self.assertEqual(prop["source_document"]["sha256"], "fa72f3441329d8db6348926906817ebac7b3bd7077a90e836f75f8ecdb087287")
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
        self.assertEqual(digest(canonical), "dc976befcdcb03bc40cba9f6b4921f5f10666f7a67b2cd094d25edcc7a80f9f0")
        self.assertEqual(source["license"]["identifier"], "CC-BY-4.0")

    def test_exact_a5_recovery_rejects_partial_duplicate_unit_and_source_drift(self):
        self.assertEqual(self.ledger["baseline_commit"], "a5cc3f6c47954033db5de7f50220d182cfcff459")
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
        next(row for row in graph["properties"]["records"] if row["id"] == wanted)["reported_value"]["unit_code"] = "g/cm^3"
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
                "identities": 3, "grades": 0, "states": 3, "properties": 3, "sources": 0,
                "categories": {"natural": 0, "metal": 0, "inorganic": 0, "polymer": 0, "composite": 3}})
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
        # reversing the binary oxides; include no older raw-byte matrix here.
        self.assertEqual(successors.project_successor_catalog_bytes(
            "materials.json", previous_raw, before="nbs-rca-density-20261019"),
            encoded(before_previous["materials"]))
        saved = encoded(self.current)
        oldest = old.recover_pre_evidence_batch_catalogs(self.current)
        self.assertEqual(graph_hashes(oldest), old.load_ledger()["baseline_sha256"])
        self.assertEqual(encoded(self.current), saved)

    def test_finite_files_and_registry_selection_keep_old_pins(self):
        self.assertEqual(successors.DATA_3_SHA256, "4ae9986cc914d9ff06a40875c19d606c0502a28527488151e6c71ec5f27eb0fe")
        self.assertEqual(successors.FILE_3_SHA256, "e5a33c0aeb3b3e6eb0bde2c6fc658735a373e29244a891e07d300b3e8b0a66d7")
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
