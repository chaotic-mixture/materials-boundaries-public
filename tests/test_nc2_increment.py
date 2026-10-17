"""One source-qualified NC2 formulation and exact recovery of its eaf16e1 parent."""
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
from scripts.integrate_material_candidates import main, write_package
from test_polymer_formulations_increment import recover_738_catalogs


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "experimental/material-batches/20261017-nc2-incremental/integration.json"
FILES = {"materials": "materials.json", "properties": "reference_properties.json",
         "sources": "sources.json"}
BASELINE_EAF_SHA256 = {
    "materials": "304a6c73b7dec07c7badda0c3ea9d6b3b54c988529c8412e6a936875c4957705",
    "properties": "528bdb225e2ccf16cdb37c9cdf9a4ec9aba5e99d3cffda9309def288b1317417",
    "sources": "3d8b8c6d4891400504ea9bedbafaa06d05698b5324e9cbd7f5686ebc1ac1736f",
}
IDENTITY_ID = "mat_domagala2024_nc2_concrete"
STATE_ID = "state_domagala2024_nc2_28d_saturated"
PROPERTY_ID = "refprop_domagala2024_nc2_28d_saturated_mass_density"
SOURCE_ID = "domagala_2024_moisture_normal_weight_concrete"
SOURCE_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC11313055/fullTextXML"
SOURCE_SHA256 = "8eee9708ea9e257dc060117f6b7c20a031443c982ecb98aa92cf5227e7479ec5"


def serialized(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")


def recover_eaf_catalogs(current):
    """Remove only the NC2 identity, state and property; enforce all parent bytes.

    This also accepts the exact predecessor, so older recovery chains can use
    it without weakening their own historical pins. Sources and grades are
    never removed or rewritten, and the supplied graph remains unchanged.
    """
    # Older NBS tests also supply this exact already-recovered predecessor.
    # Only its complete byte-pinned graph may bypass successor recovery.
    if all(sha256(serialized(current[name])).hexdigest() == expected
           for name, expected in BASELINE_EAF_SHA256.items()):
        return deepcopy(current)
    recovered = recover_738_catalogs(current)
    for table, field, identifier in (("materials", "identities", IDENTITY_ID),
                                     ("materials", "records", STATE_ID),
                                     ("properties", "records", PROPERTY_ID)):
        recovered[table][field] = [row for row in recovered[table][field]
                                   if row["id"] != identifier]
    for name, expected in BASELINE_EAF_SHA256.items():
        actual = sha256(serialized(recovered[name])).hexdigest()
        if actual != expected:
            raise AssertionError("eaf16e1 baseline bytes changed for " + name
                                 + ": " + actual + " != " + expected)
    return recovered


class NC2IncrementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.current = {
            name: json.loads((ROOT / "materials_boundaries/data" / filename).read_text(encoding="utf-8"))
            for name, filename in FILES.items()
        }
        cls.current = recover_738_catalogs(cls.current)
        cls.baseline = recover_eaf_catalogs(cls.current)
        cls.manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        if len(cls.manifest["batches"]) != 1:
            raise AssertionError("NC2 integration must select exactly one reviewed packet")
        batch = cls.manifest["batches"][0]
        cls.packet = {name: json.loads((MANIFEST.parent / batch[name]["path"]).read_text(encoding="utf-8"))
                      for name in (*FILES, "review")}
        cls.append = {name: cls.packet[name] for name in FILES}
        cls.identity = next(row for row in cls.current["materials"]["identities"] if row["id"] == IDENTITY_ID)
        cls.state = next(row for row in cls.current["materials"]["records"] if row["id"] == STATE_ID)
        cls.prop = next(row for row in cls.current["properties"]["records"] if row["id"] == PROPERTY_ID)

    def test_exact_parent_recovery_preserves_source_registry_and_all_earlier_rows(self):
        before = {name: serialized(value) for name, value in self.current.items()}
        self.assertEqual(recover_eaf_catalogs(self.baseline), self.baseline)
        self.assertEqual({name: serialized(value) for name, value in self.current.items()}, before)
        for name, expected in BASELINE_EAF_SHA256.items():
            self.assertEqual(sha256(serialized(self.baseline[name])).hexdigest(), expected)
        self.assertEqual(self.current["sources"], self.baseline["sources"])
        self.assertEqual(len(self.current["sources"]["records"]), 115)
        self.assertEqual(self.current["materials"]["grades"], self.baseline["materials"]["grades"])
        for table, field, identifier in (("materials", "identities", IDENTITY_ID),
                                         ("materials", "records", STATE_ID),
                                         ("properties", "records", PROPERTY_ID)):
            prior = {row["id"] for row in self.baseline[table][field]}
            present = {row["id"] for row in self.current[table][field]}
            self.assertEqual(present - prior, {identifier})
            self.assertEqual(len(self.current[table][field]) - len(self.baseline[table][field]), 1)

    def test_recovery_rejects_unrelated_historical_changes(self):
        changed = deepcopy(self.current)
        changed["materials"]["identities"][0]["name"] += " synthetic mutation"
        with self.assertRaisesRegex(AssertionError, "(?:eaf16e1|7388976) baseline bytes changed for materials"):
            recover_eaf_catalogs(changed)

    def test_nc2_identity_is_supported_by_a_different_recipe_not_an_extra_state(self):
        self.assertEqual(self.identity["category"], "composite")
        self.assertEqual(self.state["identity_id"], IDENTITY_ID)
        self.assertIsNone(self.state["grade_id"])
        self.assertEqual(self.append["materials"]["grades"], [])
        self.assertEqual([row["id"] for row in self.append["materials"]["identities"]], [IDENTITY_ID])
        self.assertEqual([row["id"] for row in self.append["materials"]["records"]], [STATE_ID])
        nc1 = next(row for row in self.baseline["materials"]["records"]
                   if row["identity_id"] == "mat_domagala2024_nc1_concrete")
        nc2_recipe = self.state["state"]["composition_or_purity"]["text"]
        nc1_recipe = nc1["state"]["composition_or_purity"]["text"]
        for phrase in ("cement CEM I 42.5 R 470", "tap water 174", "superplasticizer 1.9", "w/c = 0.37"):
            self.assertIn(phrase, nc2_recipe)
        for phrase in ("cement CEM I 42.5 R 377", "tap water 208", "superplasticizer 0", "w/c = 0.55"):
            self.assertIn(phrase, nc1_recipe)
        for recipe in (nc1_recipe, nc2_recipe):
            self.assertIn("natural gravel 1140", recipe)
            self.assertIn("natural sand 570", recipe)
        self.assertNotEqual(nc2_recipe, nc1_recipe)
        self.assertIn("different mixture recipes", self.identity["identity_scope"])
        self.assertIn("Table 1 NC2 row", self.identity["evidence"][0]["locator"])

    def test_density_keeps_selected_wet_mean_age_method_and_three_specimens(self):
        prop = self.prop
        self.assertEqual(prop["material_state_id"], STATE_ID)
        self.assertEqual(self.state["property_ids"], [PROPERTY_ID])
        self.assertEqual(prop["quantity"], "mass_density")
        self.assertEqual(prop["quantity_dimension"], "mass_per_volume")
        self.assertEqual(prop["reported_value"], {"kind": "scalar", "number": "2340",
            "value_text": "2340", "unit_text": "kg/m\u00b3", "unit_code": "kg/m^3"})
        self.assertEqual(prop["source_property_label"], "D_w")
        self.assertEqual(prop["summary_statistic"], "reported_mean")
        self.assertEqual(prop["reporting_basis"], "reported_summary")
        self.assertEqual(prop["determination_basis"], "source_reports_measurement")
        self.assertEqual(prop["evidence_kind"], "published_experimental_reference")
        self.assertEqual(prop["conditions"]["conditioning"]["text"],
                         "Water-saturated, nominal source age 28 days")
        self.assertEqual(prop["conditions"]["test_standard"]["text"], "EN 12390-7:2019")
        self.assertEqual(prop["sample_count"]["value"], 3)
        self.assertEqual(prop["sample_count"]["relation"], "exact")
        self.assertIn("shared count cell", prop["sample_count"]["source_statement"])
        self.assertIn("per concrete series", prop["sample_count"]["source_statement"])
        self.assertIn("150 mm", self.state["state"]["product_form"]["text"])
        self.assertIn("300 mm", self.state["state"]["product_form"]["text"])
        self.assertIn("wet measurement preceded oven-dry", self.state["state"]["conditioning"]["text"])

    def test_unknowns_rights_and_inspection_scope_are_not_strengthened(self):
        prop = self.prop
        self.assertEqual(prop["conditions"]["temperature"]["status"], "not_reported_in_inspected_source")
        self.assertIsNone(prop["conditions"]["temperature"]["text"])
        self.assertIn("curing/storage", prop["conditions"]["temperature"]["notes"])
        self.assertEqual(prop["density_basis"], "not_stated")
        self.assertIsNone(prop["uncertainty"])
        self.assertEqual(prop["uncertainty_status"], "not_reported_in_inspected_source")
        self.assertIn("maximum-deviation", prop["uncertainty_note"])
        self.assertIn("No density standard deviation, confidence interval, or instrument uncertainty is supplied.",
                      prop["uncertainty_note"])
        self.assertIn("without inferring 29 days", prop["scope_note"])
        self.assertIn("exact volume/mass subprocedure and instrument not specified",
                      prop["method_definition"]["definition"])
        self.assertEqual(prop["source_id"], SOURCE_ID)
        self.assertEqual(prop["source_document"]["url"], SOURCE_URL)
        self.assertEqual(prop["source_document"]["sha256"], SOURCE_SHA256)
        self.assertEqual(prop["source_document"]["hash_status"], "recorded")
        self.assertEqual(prop["source_document"]["inspection_status"], "selected_content_inspected")
        value_evidence = [item for item in prop["evidence"] if "reported_value" in item["supports"]]
        self.assertTrue(value_evidence)
        for evidence in value_evidence:
            self.assertEqual(evidence["source_id"], SOURCE_ID)
            self.assertEqual(evidence["url"], SOURCE_URL)
            self.assertIn("Table 3, NC2 row, D_w", evidence["locator"])
        self.assertFalse(prop["verification"]["independent_scientific_review"])
        self.assertFalse(prop["verification"]["raw_data_reanalysis"])
        self.assertFalse(prop["universal_bound"])
        self.assertFalse(prop["engineering_allowable"])
        self.assertEqual(prop["evaluation_support"], "catalog_only")
        sources = {row["id"]: row for row in self.baseline["sources"]["records"]}
        self.assertEqual(self.append["sources"]["records"], [sources[SOURCE_ID]])
        self.assertEqual(sources[SOURCE_ID]["license"]["identifier"], "CC-BY-4.0")

    def test_validated_graph_and_repeated_merge_add_only_one_composite_identity(self):
        validate_material_catalog(self.current["materials"], self.current["properties"], self.current["sources"])
        merged = merge_material_catalogs(self.baseline["materials"], self.baseline["properties"],
                                        self.baseline["sources"], self.append)
        self.assertEqual(merged, self.current)
        self.assertEqual(merge_material_catalogs(merged["materials"], merged["properties"],
                                                merged["sources"], self.append), merged)
        coverage = material_quota_coverage(self.current["materials"], self.current["properties"], self.current["sources"])
        self.assertEqual(coverage["distinct_material_count"], 1076)
        self.assertEqual({key: item["admitted_unique_identity_count"] for key, item in coverage["classes"].items()},
                         {"natural": 1010, "metal": 22, "inorganic": 26, "polymer": 14, "composite": 4})
        self.assertEqual(coverage["classes"]["composite"]["remaining"], 996)
        self.assertEqual(coverage["classes"]["polymer"]["remaining"], 986)
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
            self.assertIn("Recorded baseline-to-candidate identity delta: 1", stdout.getvalue())
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
                             serialized(self.current[name]),
                             "artifact must recover exact pinned 7388976 bytes: " + name)
        self.assertEqual(package["report"]["delta"], {"identities": 1, "grades": 0,
            "states": 1, "properties": 1, "sources": 0,
            "categories": {"natural": 0, "metal": 0, "inorganic": 0, "polymer": 0, "composite": 1}})
        self.assertEqual(package["report"]["formal_admitted_delta"], 0)
        self.assertEqual(package["report"]["released_main_count"], 1081)
        self.assertTrue(package["report"]["pending_gates"])

    def assert_mutated_packet_rejected(self, mutate, message, *, baseline_graph=None):
        """Refresh every local pin so failures exercise graph gates, not hashes."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            baseline = root / "baseline"
            baseline.mkdir()
            graph = self.baseline if baseline_graph is None else baseline_graph
            manifest = deepcopy(self.manifest)
            for name, filename in FILES.items():
                data = serialized(graph[name])
                (baseline / filename).write_bytes(data)
                pin = "reference_properties" if name == "properties" else name
                manifest["baseline_sha256"][pin] = sha256(data).hexdigest()
            packet_dir = root / "experimental/material-batches/nc2"
            packet_dir.mkdir(parents=True)
            packet = deepcopy(self.packet)
            mutate(packet)
            for name, value in packet.items():
                data = serialized(value)
                filename = name + ".json"
                (packet_dir / filename).write_bytes(data)
                manifest["batches"][0][name] = {"path": filename, "sha256": sha256(data).hexdigest()}
            manifest_path = packet_dir / "integration.json"
            manifest_path.write_bytes(serialized(manifest))
            output = root / "package.json"
            before = {path: path.read_bytes() for path in root.rglob("*") if path.is_file()}
            with self.assertRaisesRegex(ValueError, message):
                write_package(baseline, manifest_path, output, repository_root=root)
            self.assertFalse(output.exists())
            self.assertEqual({path: path.read_bytes() for path in root.rglob("*") if path.is_file()}, before)

    def test_missing_property_is_rejected_after_refreshed_input_pins(self):
        def mutate(packet):
            packet["properties"]["records"] = []
        self.assert_mutated_packet_rejected(mutate, "property links and ownership must be reciprocal and complete")

    def test_wrong_density_unit_is_rejected_after_refreshed_input_pins(self):
        def mutate(packet):
            value = packet["properties"]["records"][0]["reported_value"]
            value["unit_code"] = value["unit_text"] = "GPa"
        self.assert_mutated_packet_rejected(mutate, "unit does not match quantity dimension")

    def test_changed_existing_nc2_property_is_rejected_without_partial_output(self):
        def mutate(packet):
            value = packet["properties"]["records"][0]["reported_value"]
            value["number"] = value["value_text"] = "2350"
        self.assert_mutated_packet_rejected(mutate, "conflicting existing catalog record: " + PROPERTY_ID,
                                            baseline_graph=self.current)


if __name__ == "__main__":
    unittest.main()
