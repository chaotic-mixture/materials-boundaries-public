"""Ten qualified manufacturer grades and exact finite successor recovery.

The reference modulus values retain their source conditions and unknowns.
Source transcription does not establish scientific approval or open reuse rights.
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
BATCH_ID = "outokumpu-core-moduli-20261020"
PREVIOUS_BATCH_ID = "tamas-benyei-nbr-rcf-20261020"
BATCH = ROOT / "experimental/material-batches" / BATCH_ID
SOURCE = "outokumpu_core_1560en4_202211"
FACTS = {
    "outokumpu_304": ("Core 304/4301", "200"),
    "outokumpu_304ln": ("Core 304LN/4311", "200"),
    "outokumpu_305": ("Core 305/4303", "200"),
    "outokumpu_321": ("Core 321/4541", "200"),
    "outokumpu_347": ("Core 347/4550", "200"),
    "outokumpu_301ln": ("Core 301LN/4318", "200"),
    "outokumpu_301": ("Core 301/4310", "200"),
    "outokumpu_201": ("Core 201/4372", "200"),
    "outokumpu_201ln": ("Core 201LN/4372", "200"),
    "outokumpu_4622": ("Core 4622", "220"),
}


class PrimaryTableGrowth7PreservationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ledger = successors.data_ledger(BATCH_ID)
        graph = {name: json.loads((ROOT / "materials_boundaries/data" / filename).read_bytes())
                 for name, filename in FILES.items()}
        cls.current = successors.project_successor_catalogs(graph, before=BATCH_ID)
        cls.baseline = recover_catalogs(ROOT, cls.current, cls.ledger)
        cls.additions = appended_rows(ROOT, cls.ledger)

    def test_ten_qualified_grades_keep_reference_moduli_and_unknown_conditions(self):
        coverage = material_quota_coverage(self.current["materials"], self.current["properties"], self.current["sources"])
        self.assertEqual(coverage["distinct_material_count"], 1134)
        self.assertEqual({key: value["admitted_unique_identity_count"] for key, value in coverage["classes"].items()},
                         {"natural": 1010, "metal": 32, "inorganic": 49, "polymer": 18, "composite": 25})
        self.assertEqual({key: len(rows) for key, rows in self.additions.items()},
                         {"identities": 10, "grades": 10, "states": 10, "properties": 10, "sources": 0})
        identities = {row["id"]: row for row in self.additions["identities"]}
        grades = {row["id"]: row for row in self.additions["grades"]}
        states = {row["id"]: row for row in self.additions["states"]}
        self.assertEqual(set(identities), {"mat_" + stem for stem in FACTS})
        self.assertEqual(set(grades), {"grade_" + stem for stem in FACTS})
        self.assertEqual(set(states), {"state_" + stem for stem in FACTS})
        observed = set()
        for prop in self.additions["properties"]:
            state = states[prop["material_state_id"]]
            stem = state["identity_id"].removeprefix("mat_")
            designation, number = FACTS[stem]
            observed.add(stem)
            self.assertEqual(state["id"], "state_" + stem)
            self.assertEqual(prop["id"], "refprop_" + stem + "_youngs_modulus")
            self.assertEqual(identities[state["identity_id"]]["category"], "metal")
            self.assertEqual(state["source_designation"], designation)
            self.assertEqual(state["grade_id"], "grade_" + stem)
            grade = grades[state["grade_id"]]
            self.assertEqual(grade["identity_id"], state["identity_id"])
            self.assertEqual(grade["designation"], designation)
            self.assertEqual(grade["authority"], {"kind": "manufacturer", "name": "Outokumpu"})
            self.assertEqual(grade["manufacturer"]["status"], "reported")
            self.assertEqual(grade["manufacturer"]["text"], "Outokumpu")
            self.assertTrue(any(e["source_id"] == SOURCE and "grade" in e["supports"] for e in grade["evidence"]))
            self.assertEqual(state["property_ids"], [prop["id"]])
            self.assertEqual(prop["reported_value"]["kind"], "scalar")
            self.assertEqual(prop["reported_value"]["number"], number)
            self.assertEqual(prop["reported_value"]["value_text"], number)
            self.assertEqual(prop["reported_value"]["unit_code"], "GPa")
            self.assertEqual(prop["reported_value"]["unit_text"], "GPa")
            self.assertEqual(prop["quantity"], "youngs_modulus")
            self.assertEqual(prop["quantity_dimension"], "pressure")
            self.assertEqual(prop["evidence_kind"], "manufacturer_reference")
            self.assertEqual(prop["reporting_basis"], "not_stated")
            self.assertEqual(prop["summary_statistic"], "not_stated")
            self.assertEqual(prop["determination_basis"],
                             "source_reports_measurement" if stem == "outokumpu_4622" else "not_stated")
            temperature = prop["conditions"]["temperature"]
            self.assertEqual(temperature["status"], "reported")
            self.assertEqual(temperature["text"], "20 \u00b0C")
            self.assertTrue(any(e["source_id"] == SOURCE and "condition" in e["supports"]
                                for e in temperature["evidence"]))
            for condition in ("test_method", "direction", "conditioning", "loading_rate"):
                self.assertEqual(prop["conditions"][condition]["status"], "not_reported_in_inspected_source")
                self.assertIsNone(prop["conditions"][condition]["text"])
            self.assertIsNone(prop["density_basis"])
            self.assertIsNone(prop["uncertainty"])
            self.assertEqual(prop["uncertainty_status"], "not_reported_in_inspected_source")
            self.assertIsNone(prop["sample_count"]["value"])
            self.assertEqual(prop["sample_count"]["relation"], "not_reported")
            self.assertIsNone(prop["method_definition"]["extraction_window"])
            self.assertEqual(prop["source_id"], SOURCE)
            self.assertEqual(prop["source_document"]["sha256"],
                             "91d2f4b1340562b0d692a3921a5b0ea2518ddcb6cbdcc9ec97a3d7ad886d7ad9")
            self.assertEqual(prop["evaluation_support"], "catalog_only")
            self.assertFalse(prop["universal_bound"])
            self.assertFalse(prop["engineering_allowable"])
            self.assertFalse(prop["verification"]["independent_scientific_review"])
            self.assertFalse(prop["verification"]["raw_data_reanalysis"])
        self.assertEqual(observed, set(FACTS))
        for stem, uns in (("outokumpu_201", "S20100"), ("outokumpu_201ln", "S20153")):
            aliases = {alias["text"] for row in (identities["mat_" + stem], grades["grade_" + stem],
                                                  states["state_" + stem]) for alias in row["aliases"]}
            self.assertNotIn("EN 1.4372", aliases)
            self.assertTrue(any("1.4372" in alias and uns in alias for alias in aliases))
            self.assertIn("1.4372", states["state_" + stem]["state"]["composition_or_purity"]["text"])
        self.assertEqual(self.current["sources"], self.baseline["sources"])
        self.assertEqual(len(self.current["sources"]["records"]), 116)
        self.assertEqual(len(self.current["materials"]["grades"]), 31)
        self.assertEqual([row for row in self.current["materials"]["grades"] if row["id"] not in grades],
                         self.baseline["materials"]["grades"])
        source = next(row for row in self.current["sources"]["records"] if row["id"] == SOURCE)
        canonical = (json.dumps(source, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
                                allow_nan=False) + "\n").encode("utf-8")
        self.assertEqual(digest(canonical), "8495de101d6ce62a9f720cf5c5245aad4349989b0b9a68fee8c81aca501e5154")
        self.assertEqual(source["license"]["status"], "no_explicit_reuse_license_verified_limited_factual_curation_only")
        self.assertIsNone(source["license"]["identifier"])

    def test_exact_eee_recovery_rejects_partial_duplicate_unit_and_source_drift(self):
        self.assertEqual(self.ledger["baseline_commit"], "eee77b5033d7671bbaa2d3b4eca57c88d52fc411")
        self.assertEqual(graph_hashes(self.current), self.ledger["current_sha256"])
        self.assertEqual(graph_hashes(self.baseline), self.ledger["baseline_sha256"])
        saved = encoded(self.current)
        self.assertEqual(recover_catalogs(ROOT, self.baseline, self.ledger), self.baseline)
        self.assertEqual(recover_catalogs(ROOT, self.current, self.ledger), self.baseline)
        self.assertEqual(encoded(self.current), saved)
        # Mutate one detached graph at a time; do not retain a large raw-byte matrix.
        for variant in ("partial state", "partial grade", "duplicate identity", "duplicate grade",
                        "wrong grade owner", "changed unit", "source rights drift", "unexpected source append",
                        "unrelated predecessor drift"):
            graph = deepcopy(self.baseline if variant == "unrelated predecessor drift" else self.current)
            if variant in {"partial state", "partial grade"}:
                table, field = ("states", "records") if variant == "partial state" else ("grades", "grades")
                wanted = self.additions[table][-1]["id"]
                graph["materials"][field] = [row for row in graph["materials"][field] if row["id"] != wanted]
            elif variant in {"duplicate identity", "duplicate grade"}:
                field = "identities" if variant == "duplicate identity" else "grades"
                graph["materials"][field].append(deepcopy(self.additions[field][0]))
            elif variant == "wrong grade owner":
                wanted = self.additions["grades"][0]["id"]
                next(row for row in graph["materials"]["grades"] if row["id"] == wanted)["identity_id"] = "mat_outokumpu_304l"
            elif variant == "changed unit":
                wanted = self.additions["properties"][0]["id"]
                next(row for row in graph["properties"]["records"] if row["id"] == wanted)["reported_value"]["unit_code"] = "g/cm^3"
            elif variant == "source rights drift":
                next(row for row in graph["sources"]["records"] if row["id"] == SOURCE)["license"]["identifier"] = "CC0-1.0"
            elif variant == "unexpected source append":
                graph["sources"]["records"].append({"id": "unreviewed_source"})
            else:
                graph["materials"]["schema_version"] = "999.0.0"
            with self.subTest(mutation=variant), self.assertRaises(AssertionError):
                recover_catalogs(ROOT, graph, self.ledger)
            if variant == "partial state":
                with self.assertRaises(AssertionError):
                    successors.project_successor_catalogs(graph)

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
                "identities": 10, "grades": 10, "states": 10, "properties": 10, "sources": 0,
                "categories": {"natural": 0, "metal": 10, "inorganic": 0, "polymer": 0, "composite": 0}})
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
        # One previous raw table exercises disk-graph alignment before reversing
        # the Tamas append; this is not a matrix over every historical catalog.
        self.assertEqual(successors.project_successor_catalog_bytes(
            "materials.json", previous_raw, before="bianchi-nr-nanoclay-20261020"),
            encoded(before_previous["materials"]))
        saved = encoded(self.current)
        oldest = old.recover_pre_evidence_batch_catalogs(self.current)
        self.assertEqual(graph_hashes(oldest), old.load_ledger()["baseline_sha256"])
        self.assertEqual(encoded(self.current), saved)

    def test_finite_files_and_registry_selection_keep_old_pins(self):
        self.assertEqual(successors.DATA_6_SHA256, "3d3335edadae838524756ad1b33efb733d48893a123e6637c461dc79d59861b5")
        self.assertEqual(successors.FILE_6_SHA256, "e13d5e02e863da91ea6318b598c69df73cc37af72b092ba502d466adba7244ab")
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
