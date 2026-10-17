"""Source-qualified next NBS batch and exact recovery of its 742890f parent."""
from contextlib import redirect_stdout
from copy import deepcopy
from hashlib import sha256
import io
import json
from pathlib import Path
import tempfile
import unittest

from materials_boundaries.material_references import (
    material_quota_coverage, merge_material_catalogs, validate_material_catalog,
)
from scripts.integrate_material_candidates import main


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "experimental/material-batches/20261016-nbs-next-incremental/integration.json"
FILES = {"materials": "materials.json", "properties": "reference_properties.json",
         "sources": "sources.json"}
BASELINE_742_SHA256 = {
    "materials": "ff81fc4075437e4a44d9bdd54b9776dd526f38ef670d467f2a209e1ce68d50ca",
    "properties": "ce7117fdbcea867b69588320e77f1f24f10446ec510b4f764a37582db30e138c",
    "sources": "3d8b8c6d4891400504ea9bedbafaa06d05698b5324e9cbd7f5686ebc1ac1736f",
}
SOURCE_ID = "swanson_tatge_1953_nbs_circ539v1"
SOURCE_URL = "https://nvlpubs.nist.gov/nistpubs/Legacy/circ/nbscircular539v1.pdf"
SOURCE_SHA256 = "003b872fbe7d403d38bbd1d752568ee92a96bdb010b6e381bdc82566929e2a6c"
# The selected NBS values retain their printed precision. Printed and PDF page
# numbers are distinct; PDF page numbers here are one-based.
FACTS = {
    "pd_johnson_matthey_sponge": ("pd", "metal", "12.04", "25 degrees C", 21, 25),
    "ag_johnson_matthey": ("ag", "metal", "10.500", "25 degrees C", 24, 28),
    "sn_johnson_matthey_beta": ("sn", "metal", "7.286", "26 degrees C", 26, 30),
    "ta_johnson_matthey_annealed": ("ta", "metal", "16.626", "25 degrees C", 31, 35),
    "pt_nbs_chemistry": ("pt", "metal", "21.472", "25 degrees C", 31, 35),
    "au_nbs_chemistry": ("au", "metal", "19.302", "25 degrees C", 33, 37),
    "pb_asarco_annealed": ("pb", "metal", "11.341", "25 degrees C", 34, 38),
    "nh4cl_baker": ("nh4cl", "inorganic", "1.527", "26 degrees C", 61, 65),
    "licl_mallinckrodt_sdd": ("licl", "inorganic", "2.074", "25 degrees C", 62, 66),
    "kf_baker": ("kf", "inorganic", "2.524", "26 degrees C", 65, 69),
}


def serialized(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")


def next_packets():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    return [
        {name: json.loads((MANIFEST.parent / batch[name]["path"]).read_text(encoding="utf-8"))
         for name in FILES}
        for batch in manifest["batches"]
    ]


def recover_742_catalogs(current):
    """Remove only this batch's appended rows and enforce all historical bytes.

    Older frozen-batch tests use this exact recovered graph, so their d4e9cf3
    and released-main hash checks remain independent of this additive batch.
    No source is removed: every new record reuses the existing NBS source.
    """
    recovered = deepcopy(current)
    for packet in next_packets():
        for table, fields in (("materials", ("identities", "grades", "records")),
                              ("properties", ("records",))):
            for field in fields:
                new_ids = {row["id"] for row in packet[table][field]}
                recovered[table][field] = [row for row in recovered[table][field]
                                           if row["id"] not in new_ids]
    for name, expected in BASELINE_742_SHA256.items():
        actual = sha256(serialized(recovered[name])).hexdigest()
        if actual != expected:
            raise AssertionError("742890f baseline bytes changed for " + name
                                 + ": " + actual + " != " + expected)
    return recovered


class NBSNextBatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.current = {
            name: json.loads((ROOT / "materials_boundaries/data" / filename).read_text(encoding="utf-8"))
            for name, filename in FILES.items()
        }
        cls.packets = next_packets()
        cls.baseline = recover_742_catalogs(cls.current)

    def test_exact_parent_recovery_and_unchanged_source_registry(self):
        for name, expected in BASELINE_742_SHA256.items():
            self.assertEqual(sha256(serialized(self.baseline[name])).hexdigest(), expected)
        self.assertEqual(self.current["sources"], self.baseline["sources"])
        self.assertEqual(len(self.current["sources"]["records"]), 115)
        for packet in self.packets:
            self.assertEqual([row["id"] for row in packet["sources"]["records"]], [SOURCE_ID])
            self.assertEqual(packet["materials"]["grades"], [])
        self.assertEqual(len(self.current["materials"]["identities"])
                         - len(self.baseline["materials"]["identities"]), 10)
        self.assertEqual(len(self.current["materials"]["records"])
                         - len(self.baseline["materials"]["records"]), 10)
        self.assertEqual(len(self.current["properties"]["records"])
                         - len(self.baseline["properties"]["records"]), 10)

    def test_packet_rows_match_runtime_and_repeated_merges_add_nothing(self):
        appended_identity_ids = []
        appended_property_ids = []
        for packet in self.packets:
            for table, fields in (("materials", ("identities", "grades", "records")),
                                  ("properties", ("records",)), ("sources", ("records",))):
                for field in fields:
                    runtime = {row["id"]: row for row in self.current[table][field]}
                    for row in packet[table][field]:
                        self.assertEqual(runtime[row["id"]], row)
            appended_identity_ids.extend(row["id"] for row in packet["materials"]["identities"])
            appended_property_ids.extend(row["id"] for row in packet["properties"]["records"])
            self.assertEqual(merge_material_catalogs(self.current["materials"],
                self.current["properties"], self.current["sources"], packet), self.current)
        self.assertEqual(len(appended_identity_ids), len(set(appended_identity_ids)))
        self.assertEqual(set(appended_identity_ids), {"mat_nbs1953_" + fact[0] for fact in FACTS.values()})
        self.assertEqual(set(appended_property_ids),
                         {"refprop_nbs1953_" + key + "_crystallographic_density" for key in FACTS})
        self.assertTrue(set(appended_identity_ids).isdisjoint(
            row["id"] for row in self.baseline["materials"]["identities"]))

    def test_selected_density_facts_keep_temperature_derivation_and_provenance(self):
        identities = {row["id"]: row for row in self.current["materials"]["identities"]}
        states = {row["id"]: row for row in self.current["materials"]["records"]}
        properties = {row["id"]: row for row in self.current["properties"]["records"]}
        for key, (identity, category, number, temperature, printed_page, pdf_page) in FACTS.items():
            with self.subTest(material=identity):
                prop = properties["refprop_nbs1953_" + key + "_crystallographic_density"]
                state = states[prop["material_state_id"]]
                self.assertEqual(state["identity_id"], "mat_nbs1953_" + identity)
                self.assertIsNone(state["grade_id"])
                self.assertEqual(identities[state["identity_id"]]["category"], category)
                self.assertEqual(prop["quantity"], "mass_density")
                self.assertEqual(prop["quantity_dimension"], "mass_per_volume")
                self.assertEqual(prop["reported_value"]["number"], number)
                self.assertEqual(prop["reported_value"]["value_text"], number)
                self.assertEqual(prop["reported_value"]["unit_code"], "g/cm^3")
                self.assertEqual(prop["conditions"]["temperature"]["status"], "reported")
                self.assertEqual(prop["conditions"]["temperature"]["text"], temperature)
                self.assertEqual(prop["density_basis"], "crystallographic")
                self.assertEqual(prop["determination_basis"], "source_reports_calculation")
                self.assertEqual(prop["evidence_kind"], "published_measurement_derived_reference")
                self.assertEqual(prop["method_definition"]["type"], "source_reported_crystallographic_derivation")
                self.assertEqual(prop["source_id"], SOURCE_ID)
                value_evidence = [item for item in prop["evidence"] if "reported_value" in item["supports"]]
                self.assertTrue(value_evidence)
                locator = " ".join(item["locator"] for item in value_evidence).lower()
                self.assertIn("printed p. " + str(printed_page), locator)
                self.assertIn("pdf p. " + str(pdf_page), locator)
                for item in value_evidence + prop["method_definition"]["evidence"]:
                    self.assertEqual(item["source_id"], SOURCE_ID)
                    self.assertEqual(item["url"], SOURCE_URL)
                self.assertEqual(prop["source_document"]["sha256"], SOURCE_SHA256)
                self.assertEqual(prop["source_document"]["hash_status"], "recorded")
                self.assertEqual(prop["source_document"]["inspection_status"], "selected_content_inspected")
                self.assertIsNone(prop["uncertainty"])
                self.assertIsNone(prop["sample_count"]["value"])
                self.assertFalse(prop["verification"]["independent_scientific_review"])
                self.assertFalse(prop["verification"]["raw_data_reanalysis"])
                self.assertFalse(prop["universal_bound"])
                self.assertFalse(prop["engineering_allowable"])
                self.assertEqual(prop["evaluation_support"], "catalog_only")
        ammonium = properties["refprop_nbs1953_nh4cl_baker_crystallographic_density"]
        self.assertIn("one formula unit", ammonium["method_definition"]["definition"].lower())

    def test_validated_identity_coverage_and_unmet_class_targets(self):
        validate_material_catalog(self.current["materials"], self.current["properties"], self.current["sources"])
        coverage = material_quota_coverage(self.current["materials"], self.current["properties"], self.current["sources"])
        expected = {"natural": 1010, "metal": 22, "inorganic": 26, "polymer": 14, "composite": 3}
        self.assertEqual(coverage["distinct_material_count"], 1075)
        self.assertEqual({key: item["admitted_unique_identity_count"]
                          for key, item in coverage["classes"].items()}, expected)
        self.assertEqual({key: item["remaining"] for key, item in coverage["classes"].items()},
                         {"natural": 0, "metal": 978, "inorganic": 974, "polymer": 986, "composite": 997})
        self.assertEqual({key for key, item in coverage["classes"].items() if item["target_met"]}, {"natural"})

    def test_actual_cli_first_and_repeat_preserve_artifact_and_exact_runtime_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            baseline = Path(directory) / "baseline"
            baseline.mkdir()
            for name, filename in FILES.items():
                (baseline / filename).write_bytes(serialized(self.baseline[name]))
            before = {path: path.read_bytes() for path in baseline.iterdir()}
            output = Path(directory) / "integration.json"
            arguments = ["--baseline-dir", str(baseline), "--manifest", str(MANIFEST), "--output", str(output)]
            with redirect_stdout(io.StringIO()) as stdout:
                self.assertEqual(main(arguments), 0)
            self.assertIn("Recorded baseline-to-candidate identity delta: 10", stdout.getvalue())
            self.assertIn("New artifact written: yes", stdout.getvalue())
            stored, timestamp = output.read_bytes(), output.stat().st_mtime_ns
            with redirect_stdout(io.StringIO()) as stdout:
                self.assertEqual(main(arguments), 0)
            self.assertIn("New artifact written: no", stdout.getvalue())
            self.assertIn("Unchanged experimental integration artifact:", stdout.getvalue())
            self.assertEqual(output.read_bytes(), stored)
            self.assertEqual(output.stat().st_mtime_ns, timestamp)
            self.assertEqual({path: path.read_bytes() for path in before}, before)
            package = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(package["catalogs"], self.current)
        for name, filename in FILES.items():
            self.assertEqual(serialized(package["catalogs"][name]),
                             (ROOT / "materials_boundaries/data" / filename).read_bytes())
        self.assertEqual(package["report"]["delta"], {"identities": 10, "grades": 0,
            "states": 10, "properties": 10, "sources": 0,
            "categories": {"natural": 0, "metal": 7, "inorganic": 3, "polymer": 0, "composite": 0}})
        self.assertEqual(package["report"]["formal_admitted_delta"], 0)
        self.assertEqual(package["report"]["released_main_count"], 1081)


if __name__ == "__main__":
    unittest.main()
