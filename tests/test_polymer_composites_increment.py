"""Four composition-scoped composites; exact a592 recovery and bounded ingestion."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest

from materials_boundaries.material_references import material_quota_coverage, merge_material_catalogs
from scripts.integrate_material_candidates import write_package
from evidence_batch_data_preservation import (
    has_evidence_batch, pre_evidence_batch_catalog_bytes, recover_pre_evidence_batch_catalogs,
)

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "experimental/material-batches/20261019-polymer-composites-incremental/integration.json"
FILES = {"materials": "materials.json", "properties": "reference_properties.json", "sources": "sources.json"}
BASELINE_A592_SHA256 = {
    "materials": "d078f1fb726289bdd6c7faff6f9a4a84d46eed5cd83ba586cd9c2f6ae0256739",
    "properties": "4a5242f87beab3e07b0e5667e2fdb77b4b984baa71468978aec01092bb0aaad8",
    "sources": "3d8b8c6d4891400504ea9bedbafaa06d05698b5324e9cbd7f5686ebc1ac1736f",
}
NEW_IDENTITIES = frozenset({"mat_ewurum2025_pbs_lignin45", "mat_bianchi2022_epdm_h_p20",
                            "mat_bianchi2022_epdm_h_p40", "mat_bianchi2022_epdm_h_p60"})
NEW_STATES = frozenset({"state_ewurum2025_pbs_lignin45", "state_bianchi2022_epdm_h_p20",
                        "state_bianchi2022_epdm_h_p40", "state_bianchi2022_epdm_h_p60"})
NEW_PROPERTIES = frozenset({"refprop_ewurum2025_pbs_lignin45_youngs_modulus",
                            "refprop_bianchi2022_epdm_h_p20_mass_density",
                            "refprop_bianchi2022_epdm_h_p40_mass_density",
                            "refprop_bianchi2022_epdm_h_p60_mass_density"})
REMOVALS = (("materials", "identities", NEW_IDENTITIES), ("materials", "records", NEW_STATES),
            ("properties", "records", NEW_PROPERTIES))


def serialized(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")


def has_composite_increment(current):
    """Only the fixed twelve IDs select this successor recovery layer."""
    return any(any(row["id"] in identifiers for row in current[table][field])
               for table, field, identifiers in REMOVALS)


def recover_a592_catalogs(current):
    """Reverse exactly four complete records, then check all predecessor bytes.

    Also accepts the exact a592 graph unchanged. No candidate manifest can
    enlarge the removal list; partial batches, metadata/grade/source mutations
    and unrelated append records fail. The input graph is never changed.
    """
    if has_evidence_batch(current):
        current = recover_pre_evidence_batch_catalogs(current)
    recovered = deepcopy(current)
    has_batch = has_composite_increment(current)
    for table, field, identifiers in REMOVALS:
        present = [row["id"] for row in current[table][field] if row["id"] in identifiers]
        if has_batch and (set(present) != identifiers or len(present) != len(identifiers)):
            raise AssertionError("a592c89 recovery requires the complete four-composite batch")
        recovered[table][field] = [row for row in recovered[table][field] if row["id"] not in identifiers]
    for name, expected in BASELINE_A592_SHA256.items():
        actual = sha256(serialized(recovered[name])).hexdigest()
        if actual != expected:
            raise AssertionError("a592c89 baseline bytes changed for " + name + ": " + actual + " != " + expected)
    return recovered


class PolymerCompositesIncrementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.current = {name: json.loads((ROOT / "materials_boundaries/data" / filename).read_bytes())
                       for name, filename in FILES.items()}
        cls.current = recover_pre_evidence_batch_catalogs(cls.current)
        cls.baseline = recover_a592_catalogs(cls.current)
        cls.manifest = json.loads(MANIFEST.read_bytes())
        cls.packets = [{name: json.loads((MANIFEST.parent / batch[name]["path"]).read_bytes())
                        for name in (*FILES, "review")} for batch in cls.manifest["batches"]]

    def test_exact_parent_recovery_retains_every_old_object_and_source_byte(self):
        before = {name: serialized(value) for name, value in self.current.items()}
        self.assertEqual(recover_a592_catalogs(self.baseline), self.baseline)
        self.assertEqual(recover_a592_catalogs(self.current), self.baseline)
        self.assertEqual({name: serialized(value) for name, value in self.current.items()}, before)
        for table, field, identifiers in REMOVALS:
            old = {row["id"] for row in self.baseline[table][field]}
            new = {row["id"] for row in self.current[table][field]}
            self.assertEqual(new - old, identifiers)
            self.assertEqual(len(self.current[table][field]) - len(self.baseline[table][field]), 4)
        self.assertEqual(self.current["materials"]["grades"], self.baseline["materials"]["grades"])
        self.assertEqual(self.current["sources"], self.baseline["sources"])

    def test_recovery_rejects_partial_duplicates_and_unrelated_changes(self):
        for table, field, identifiers in REMOVALS:
            for kind in ("missing", "duplicate"):
                changed = deepcopy(self.current)
                index = next(i for i, row in enumerate(changed[table][field]) if row["id"] in identifiers)
                if kind == "missing":
                    changed[table][field].pop(index)
                else:
                    changed[table][field].append(deepcopy(changed[table][field][index]))
                with self.subTest(table=table, field=field, kind=kind):
                    with self.assertRaisesRegex(AssertionError, "complete four-composite batch"):
                        recover_a592_catalogs(changed)
        for table in FILES:
            changed = deepcopy(self.current)
            changed[table]["schema_version"] = "999.0.0"
            with self.assertRaisesRegex(AssertionError, "a592c89 baseline bytes changed for " + table):
                recover_a592_catalogs(changed)

    def test_exact_four_identity_coverage_and_remaining_gaps(self):
        coverage = material_quota_coverage(self.current["materials"], self.current["properties"], self.current["sources"])
        self.assertEqual(coverage["distinct_material_count"], 1083)
        self.assertEqual({key: value["admitted_unique_identity_count"] for key, value in coverage["classes"].items()},
                         {"natural": 1010, "metal": 22, "inorganic": 26, "polymer": 15, "composite": 10})
        self.assertEqual({key: value["remaining"] for key, value in coverage["classes"].items()},
                         {"natural": 0, "metal": 978, "inorganic": 974, "polymer": 985, "composite": 990})
        self.assertEqual({key for key, value in coverage["classes"].items() if value["target_met"]}, {"natural"})

    def test_actual_packet_replay_produces_current_bytes_and_no_repeat_increment(self):
        with tempfile.TemporaryDirectory() as directory:
            baseline = Path(directory) / "baseline"
            baseline.mkdir()
            for name, filename in FILES.items():
                (baseline / filename).write_bytes(serialized(self.baseline[name]))
            output = Path(directory) / "integration.json"
            package, created = write_package(baseline, MANIFEST, output)
            self.assertTrue(created)
            stored = (output.read_bytes(), output.stat().st_mtime_ns)
            repeated, created = write_package(baseline, MANIFEST, output)
            self.assertFalse(created)
            self.assertEqual(repeated, package)
            self.assertEqual((output.read_bytes(), output.stat().st_mtime_ns), stored)
            self.assertEqual(package["catalogs"], self.current)
            for name, filename in FILES.items():
                self.assertEqual(serialized(package["catalogs"][name]), pre_evidence_batch_catalog_bytes(
                    filename, (ROOT / "materials_boundaries/data" / filename).read_bytes()))
            self.assertEqual(package["report"]["delta"], {"identities": 4, "grades": 0, "states": 4,
                "properties": 4, "sources": 0, "categories": {"natural": 0, "metal": 0, "inorganic": 0, "polymer": 0, "composite": 4}})
            self.assertEqual(package["report"]["formal_admitted_delta"], 0)
            self.assertEqual(package["report"]["released_main_count"], 1081)
            self.assertTrue(package["report"]["pending_gates"])
        for packet in self.packets:
            merged = merge_material_catalogs(self.current["materials"], self.current["properties"],
                                            self.current["sources"], {name: packet[name] for name in FILES})
            self.assertEqual(merged, self.current)

    def assert_packet_rejected(self, packet_index, mutate, message, *, baseline_graph=None):
        """Rebind hashes so semantic gates, rather than stale digests, fail."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            baseline = root / "baseline"
            baseline.mkdir()
            graph = self.baseline if baseline_graph is None else baseline_graph
            manifest = deepcopy(self.manifest)
            for name, filename in FILES.items():
                raw = serialized(graph[name])
                (baseline / filename).write_bytes(raw)
                manifest["baseline_sha256"]["reference_properties" if name == "properties" else name] = sha256(raw).hexdigest()
            packet_root = root / "experimental/material-batches"
            packet_root.mkdir(parents=True)
            for index, original in enumerate(self.packets):
                packet = deepcopy(original)
                if index == packet_index:
                    mutate(packet)
                folder = packet_root / ("packet-" + str(index))
                folder.mkdir()
                for name, value in packet.items():
                    raw = serialized(value)
                    (folder / (name + ".json")).write_bytes(raw)
                    manifest["batches"][index][name] = {"path": folder.name + "/" + name + ".json", "sha256": sha256(raw).hexdigest()}
            manifest_path = packet_root / "integration.json"
            manifest_path.write_bytes(serialized(manifest))
            output = root / "package.json"
            before = {path: path.read_bytes() for path in root.rglob("*") if path.is_file()}
            with self.assertRaisesRegex(ValueError, message):
                write_package(baseline, manifest_path, output, repository_root=root)
            self.assertFalse(output.exists())
            self.assertEqual({path: path.read_bytes() for path in root.rglob("*") if path.is_file()}, before)

    def test_missing_property_fails_atomically_even_after_first_packet_validates(self):
        for index in range(2):
            self.assert_packet_rejected(index, lambda packet: packet["properties"]["records"].pop(),
                                        "property links and ownership must be reciprocal and complete")

    def test_wrong_units_fail_with_refreshed_input_hashes(self):
        def mutate(packet):
            value = packet["properties"]["records"][0]["reported_value"]
            value["unit_code"] = value["unit_text"] = "MPa" if value["unit_code"] == "g/cm^3" else "kg/m^3"
        for index in range(2):
            self.assert_packet_rejected(index, mutate, "unit does not match quantity dimension")

    def test_changed_existing_property_is_not_silently_replaced(self):
        def mutate(packet):
            value = packet["properties"]["records"][0]["reported_value"]
            value["number"] = value["value_text"] = "999"
        for index in range(2):
            self.assert_packet_rejected(index, mutate, "conflicting existing catalog record:", baseline_graph=self.current)


if __name__ == "__main__":
    unittest.main()
