"""Measured commercial filament facts and exact finite successor recovery.

Measured filament evidence does not establish printed-part properties, scientific
approval, or engineering allowables. Manufacturer evidence supports classification.
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
BATCH_ID = "zenodo-8089569-nylon-followup-20261021"
PREVIOUS_BATCH_ID = "zenodo-8089569-tough-pla-followup-20261021"
BATCH = ROOT / "experimental/material-batches" / BATCH_ID
SOURCE = "aniskevich_bulderberga_2023_polymer_mechanical_characterisation"
FACTS = {'state_aniskevich_2023_ultimaker_nylon_transparent_filament': {'identity_id': 'mat_aniskevich_2023_ultimaker_nylon',
                                                                'category': 'polymer',
                                                                'grade_id': None,
                                                                'source_designation': 'PA, Nylon Transparent '
                                                                                      '1647',
                                                                'properties': {'refprop_aniskevich_2023_ultimaker_nylon_transparent_filament_tensile_modulus': ('tensile_modulus',
                                                                                                                                                                {'kind': 'scalar',
                                                                                                                                                                 'unit_text': 'MPa ',
                                                                                                                                                                 'unit_code': 'MPa',
                                                                                                                                                                 'value_text': '2774.8837867501061',
                                                                                                                                                                 'number': '2774.8837867501061'}),
                                                                               'refprop_aniskevich_2023_ultimaker_nylon_transparent_filament_tensile_strength': ('tensile_strength',
                                                                                                                                                                 {'kind': 'scalar',
                                                                                                                                                                  'unit_text': 'MPa ',
                                                                                                                                                                  'unit_code': 'MPa',
                                                                                                                                                                  'value_text': '209.43237576723914',
                                                                                                                                                                  'number': '209.43237576723914'})}}}
COMMON_PROPERTY_FACTS = {'summary_statistic': 'reported_mean',
 'reporting_basis': 'reported_summary',
 'evidence_kind': 'published_experimental_reference',
 'determination_basis': 'source_reports_measurement',
 'uncertainty': None,
 'uncertainty_status': 'not_reported_in_inspected_source',
 'conditions': {'temperature': {'status': 'not_reported_in_inspected_source', 'text': None},
                'test_standard': {'status': 'not_reported_in_inspected_source', 'text': None},
                'test_method': {'status': 'reported',
                                'text': 'Tensile testing of reference filament 2.8 mm; source '
                                        'reports E-mod and tensile strength'},
                'direction': {'status': 'not_reported_in_inspected_source', 'text': None},
                'conditioning': {'status': 'not_reported_in_inspected_source', 'text': None},
                'loading_rate': {'status': 'reported', 'text': '10 mm/min'}},
 'sample_count': {'value': None, 'relation': 'not_reported'},
 'source_document_sha256': '830b2c9277dcc2d03265b63e311a5e7089c258ebb6a389b45d07601ae4b2e4e7'}
EXPECTED_AFTER = {'identities': 1144,
 'grades': 31,
 'states': 1145,
 'properties': 1156,
 'sources': 123,
 'categories': {'metal': 32, 'inorganic': 49, 'polymer': 25, 'composite': 28, 'natural': 1010}}
EXPECTED_DELTA = {'identities': 1,
 'grades': 0,
 'states': 1,
 'properties': 2,
 'sources': 2,
 'categories': {'metal': 0, 'inorganic': 0, 'polymer': 1, 'composite': 0, 'natural': 0}}


class NylonFollowupPreservationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ledger = successors.data_ledger(BATCH_ID)
        graph = {name: json.loads((ROOT / "materials_boundaries/data" / filename).read_bytes())
                 for name, filename in FILES.items()}
        cls.current = successors.project_successor_catalogs(graph, before=BATCH_ID)
        cls.baseline = recover_catalogs(ROOT, cls.current, cls.ledger)
        cls.additions = appended_rows(ROOT, cls.ledger)

    def test_one_identity_one_state_keeps_independent_measured_properties(self):
        coverage = material_quota_coverage(self.current["materials"], self.current["properties"], self.current["sources"])
        self.assertEqual(coverage["distinct_material_count"], EXPECTED_AFTER["identities"])
        self.assertEqual({key: value["admitted_unique_identity_count"] for key, value in coverage["classes"].items()},
                         EXPECTED_AFTER["categories"])
        self.assertEqual({key: len(rows) for key, rows in self.additions.items()},
                         {key: EXPECTED_DELTA[key] for key in self.additions})
        identities = {row["id"]: row for row in self.additions["identities"]}
        states = {row["id"]: row for row in self.additions["states"]}
        properties = {row["id"]: row for row in self.additions["properties"]}
        self.assertEqual(set(states), set(FACTS))
        self.assertEqual(len(identities), 1)
        self.assertEqual(len(states), 1)
        self.assertEqual(len(properties), 2)
        self.assertEqual({row["identity_id"] for row in states.values()}, set(identities))
        self.assertEqual(next(iter(states.values()))["state"]["composition_or_purity"]["status"], "not_reported_in_inspected_source")
        self.assertIsNone(next(iter(states.values()))["state"]["composition_or_purity"]["text"])
        self.assertEqual(set(identities), {fact["identity_id"] for fact in FACTS.values()})
        self.assertEqual(set(properties), {pid for fact in FACTS.values() for pid in fact["properties"]})
        for state_id, fact in FACTS.items():
            state = states[state_id]
            self.assertEqual(state["identity_id"], fact["identity_id"])
            self.assertEqual(identities[state["identity_id"]]["category"], fact["category"])
            self.assertEqual(state["grade_id"], fact["grade_id"])
            self.assertEqual(state["source_designation"], fact["source_designation"])
            self.assertEqual(state["property_ids"], list(fact["properties"]))
            self.assertEqual(len(state["property_ids"]), 2)
            for pid, expected in fact["properties"].items():
                prop = properties[pid]
                self.assertEqual(prop["material_state_id"], state_id)
                self.assertEqual((prop["quantity"], prop["reported_value"]), expected)
                ordinary = set(COMMON_PROPERTY_FACTS) - {"conditions", "sample_count", "source_document_sha256"}
                self.assertEqual({key: prop[key] for key in ordinary}, {key: COMMON_PROPERTY_FACTS[key] for key in ordinary})
                self.assertEqual({key: {field: value[field] for field in ("status", "text")}
                                  for key, value in prop["conditions"].items()}, COMMON_PROPERTY_FACTS["conditions"])
                self.assertEqual({key: prop["sample_count"][key] for key in ("value", "relation")}, COMMON_PROPERTY_FACTS["sample_count"])
                self.assertEqual(prop["source_document"]["sha256"], COMMON_PROPERTY_FACTS["source_document_sha256"])
                self.assertEqual(prop["source_id"], SOURCE)
                self.assertEqual(prop["quantity_dimension"], "pressure")
                self.assertEqual(prop["evaluation_support"], "catalog_only")
                self.assertIsNone(prop["sample_count"]["value"])
                self.assertFalse(prop["universal_bound"])
                self.assertFalse(prop["engineering_allowable"])
                self.assertFalse(prop["verification"]["independent_scientific_review"])
                self.assertFalse(prop["verification"]["raw_data_reanalysis"])
        for section, collection in (("sources", "records"), ("materials", "grades")):
            self.assertEqual(self.current[section][collection][:len(self.baseline[section][collection])],
                             self.baseline[section][collection])
        self.assertEqual(len(self.current["materials"]["grades"]), EXPECTED_AFTER["grades"])
        self.assertEqual(len(self.current["sources"]["records"]), EXPECTED_AFTER["sources"])

    def test_exact_2c8_recovery_rejects_partial_owner_unit_source_and_order_drift(self):
        self.assertEqual(self.ledger["baseline_commit"], "2c8ddac78f5cd43dfa071ad23639b826561a043b")
        self.assertEqual(graph_hashes(self.current), self.ledger["current_sha256"])
        self.assertEqual(graph_hashes(self.baseline), self.ledger["baseline_sha256"])
        saved = encoded(self.current)
        self.assertEqual(recover_catalogs(ROOT, self.baseline, self.ledger), self.baseline)
        self.assertEqual(recover_catalogs(ROOT, self.current, self.ledger), self.baseline)
        self.assertEqual(encoded(self.current), saved)
        for table, section, collection in (("identities", "materials", "identities"),
                                            ("grades", "materials", "grades"),
                                            ("states", "materials", "records"),
                                            ("properties", "properties", "records"),
                                            ("sources", "sources", "records")):
            if not self.additions[table]:
                continue
            candidate = self.additions[table][0]
            for mutation in ("missing", "changed", "duplicate"):
                graph = deepcopy(self.current)
                rows = graph[section][collection]
                row = next(row for row in rows if row["id"] == candidate["id"])
                if mutation == "missing":
                    rows.remove(row)
                elif mutation == "changed":
                    row["version"] = "unreviewed"
                else:
                    rows.append(deepcopy(row))
                with self.subTest(table=table, mutation=mutation), self.assertRaises(AssertionError):
                    recover_catalogs(ROOT, graph, self.ledger)
                if table == "states" and mutation == "missing":
                    with self.assertRaises(AssertionError):
                        successors.project_successor_catalogs(graph)
        for mutation in ("wrong property owner", "changed unit", "source rights drift", "predecessor drift"):
            graph = deepcopy(self.baseline if mutation == "predecessor drift" else self.current)
            if mutation in {"wrong property owner", "changed unit"}:
                pid = self.additions["properties"][0]["id"]
                prop = next(row for row in graph["properties"]["records"] if row["id"] == pid)
                if mutation == "wrong property owner":
                    prop["material_state_id"] = self.baseline["materials"]["records"][0]["id"]
                    self.assertNotEqual(prop["material_state_id"], self.additions["states"][0]["id"])
                else:
                    prop["reported_value"]["unit_code"] = "g/cm^3"
            elif mutation == "source rights drift":
                next(row for row in graph["sources"]["records"] if row["id"] == SOURCE)["license"]["identifier"] = "CC0-1.0"
            else:
                graph["materials"]["schema_version"] = "999.0.0"
            with self.subTest(mutation=mutation), self.assertRaises(AssertionError):
                recover_catalogs(ROOT, graph, self.ledger)

        for section, collection in (("properties", "records"), ("sources", "records")):
            graph = deepcopy(self.current)
            self.assertEqual(len(self.additions[section]), 2)
            before_order = encoded(graph)
            graph[section][collection][-2:] = reversed(graph[section][collection][-2:])
            self.assertNotEqual(encoded(graph), before_order)
            with self.subTest(order=section), self.assertRaises(AssertionError):
                recover_catalogs(ROOT, graph, self.ledger)

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
            self.assertEqual(package["report"]["delta"], EXPECTED_DELTA)
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
        self.assertEqual(successors.project_successor_catalog_bytes(
            "materials.json", previous_raw, before="zenodo-8089569-filaments-20261021"),
            encoded(before_previous["materials"]))
        saved = encoded(self.current)
        oldest = old.recover_pre_evidence_batch_catalogs(self.current)
        self.assertEqual(graph_hashes(oldest), old.load_ledger()["baseline_sha256"])
        self.assertEqual(encoded(self.current), saved)

    def test_finite_files_and_registry_selection_keep_old_pins(self):
        self.assertEqual(successors.TOUGH_DATA_SHA256, "46d33c7bfc8abb32b341a5c026ed8cb03e47350feeb17e2b0c478999aeacf1f4")
        self.assertEqual(successors.TOUGH_FILE_SHA256, "7c1ff7be1ffb8f5085e004f465ca52e936e9068bfc1357e46925e150eb08bfef")
        self.assertEqual(successors.DATA_8_SHA256, "de662ffe08378402a224b4ee4180252b620278dfb79164b58a20884d68e82c51")
        self.assertEqual(successors.FILE_8_SHA256, "ad37d06723db7e66a071fe1f6584f28f16f7a386626db8778e5fa3045f27d5ea")
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
