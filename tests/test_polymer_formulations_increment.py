"""Three composition-scoped formulations and exact recovery of parent 7388976."""
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
from test_polymer_composites_increment import has_composite_increment, recover_a592_catalogs


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "experimental/material-batches/20261017-polymer-formulations-incremental/integration.json"
FILES = {"materials": "materials.json", "properties": "reference_properties.json", "sources": "sources.json"}
BASELINE_738_SHA256 = {
    "materials": "3a310b7c0f2d3ba0f13562f0feb9e10bc616bc1bb4840b64f38203b7bbe32859",
    "properties": "606c65d7b5eab8d483413c21fdba19e8a6da71dc7dd4bea11722a52b8a004521",
    "sources": "3d8b8c6d4891400504ea9bedbafaa06d05698b5324e9cbd7f5686ebc1ac1736f",
}
NEW_IDENTITIES = {
    "mat_ewurum2025_pbs_lignin10", "mat_ewurum2025_pbs_lignin30", "mat_ivdre2024_spo2_rigid_pur",
}
NEW_STATES = {
    "state_ewurum2025_pbs_lignin10", "state_ewurum2025_pbs_lignin30", "state_ivdre2024_spo2_rigid_pur",
}
NEW_PROPERTIES = {
    "refprop_ewurum2025_pbs_lignin10_youngs_modulus",
    "refprop_ewurum2025_pbs_lignin30_youngs_modulus",
    "refprop_ivdre2024_spo2_rigid_pur_mass_density",
}
SOURCES = {
    "ewurum_mcdonald_2025_pbs_lignin": (
        "https://mdpi-res.com/d_attachment/polymers/polymers-17-00194/article_deploy/polymers-17-00194.pdf",
        "766d17f0e92c7e93cd57a3a5e97dddff0cb66a84bba6bf9118fbd0796d4c2e6f"),
    "ivdre_2024_lpo_rigid_pur": (
        "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC11013755/fullTextXML",
        "4e0c1a91a9ae26d814576961a3805f9371b46498d4861fb578e7a413bb4c726d"),
}


def serialized(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")


def recover_738_catalogs(current):
    """Remove only these three identities/states/properties and pin all parent bytes.

    The exact 7388976 predecessor is accepted unchanged. Historical grades,
    sources, row ordering and metadata remain part of the byte-level contract.
    Candidate manifests cannot enlarge this fixed removal allowlist.
    """
    recovered = recover_a592_catalogs(current) if has_composite_increment(current) else deepcopy(current)
    for table, field, identifiers in (("materials", "identities", NEW_IDENTITIES),
                                      ("materials", "records", NEW_STATES),
                                      ("properties", "records", NEW_PROPERTIES)):
        recovered[table][field] = [row for row in recovered[table][field] if row["id"] not in identifiers]
    for name, expected in BASELINE_738_SHA256.items():
        actual = sha256(serialized(recovered[name])).hexdigest()
        if actual != expected:
            raise AssertionError("7388976 baseline bytes changed for " + name + ": " + actual + " != " + expected)
    return recovered


class PolymerFormulationsIncrementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.current = {name: json.loads((ROOT / "materials_boundaries/data" / filename).read_text(encoding="utf-8"))
                       for name, filename in FILES.items()}
        cls.current = recover_a592_catalogs(cls.current)
        cls.baseline = recover_738_catalogs(cls.current)
        cls.manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        if len(cls.manifest["batches"]) != 2:
            raise AssertionError("Formulation integration must select exactly the two reviewed packets")
        cls.packets = [{name: json.loads((MANIFEST.parent / batch[name]["path"]).read_text(encoding="utf-8"))
                        for name in (*FILES, "review")} for batch in cls.manifest["batches"]]
        cls.identities = {row["id"]: row for row in cls.current["materials"]["identities"]}
        cls.states = {row["id"]: row for row in cls.current["materials"]["records"]}
        cls.properties = {row["id"]: row for row in cls.current["properties"]["records"]}

    def test_exact_predecessor_bytes_and_only_three_appended_rows_per_table(self):
        before = {name: serialized(value) for name, value in self.current.items()}
        self.assertEqual(recover_738_catalogs(self.current), self.baseline)
        self.assertEqual(recover_738_catalogs(self.baseline), self.baseline)
        self.assertEqual({name: serialized(value) for name, value in self.current.items()}, before)
        for name, expected in BASELINE_738_SHA256.items():
            self.assertEqual(sha256(serialized(self.baseline[name])).hexdigest(), expected)
        for table, field, identifiers in (("materials", "identities", NEW_IDENTITIES),
                                          ("materials", "records", NEW_STATES),
                                          ("properties", "records", NEW_PROPERTIES)):
            old = {row["id"] for row in self.baseline[table][field]}
            new = {row["id"] for row in self.current[table][field]}
            self.assertEqual(new - old, identifiers)
            self.assertEqual(len(self.current[table][field]) - len(self.baseline[table][field]), 3)
        self.assertEqual(self.current["materials"]["grades"], self.baseline["materials"]["grades"])
        self.assertEqual(self.current["sources"], self.baseline["sources"])

    def test_recovery_rejects_unrelated_historical_mutations(self):
        for table in FILES:
            with self.subTest(table=table):
                changed = deepcopy(self.current)
                changed[table]["schema_version"] = "999.0.0"
                with self.assertRaisesRegex(AssertionError, "7388976 baseline bytes changed for " + table):
                    recover_738_catalogs(changed)

    def test_compositions_distinguish_new_formulations_from_existing_materials(self):
        b20 = self.states["state_ewurum2025_pbs_lignin20"]
        self.assertIn("20 wt.%", b20["state"]["composition_or_purity"]["text"])
        for loading in ("10", "30"):
            state = self.states["state_ewurum2025_pbs_lignin" + loading]
            identity = self.identities[state["identity_id"]]
            self.assertEqual(identity["category"], "composite")
            self.assertEqual(state["source_designation"], "B" + loading)
            recipe = state["state"]["composition_or_purity"]["text"]
            self.assertIn(loading + " wt.% Indulin AT", recipe)
            self.assertIn("total polymer mass", recipe)
            self.assertNotEqual(recipe, b20["state"]["composition_or_purity"]["text"])
            self.assertIn("separately extruded physical formulations", identity["identity_scope"])
            self.assertIn("not DCP-reactive R" + loading, identity["identity_scope"])
            self.assertIn("FZ91PM/FZ91PB", identity["identity_scope"])
            self.assertIsNone(state["grade_id"])
        spo = self.states["state_ivdre2024_spo2_rigid_pur"]
        self.assertEqual(self.identities[spo["identity_id"]]["category"], "polymer")
        self.assertIsNone(spo["grade_id"])
        recipe = spo["state"]["composition_or_purity"]["text"]
        self.assertIn("SA-C_TOFA(50:50)/TMP 67 g", recipe)
        self.assertIn("SA-E_ETOFA(50:50)/TMP 33 g", recipe)
        self.assertIn("unlike the existing LPO-1", self.identities[spo["identity_id"]]["identity_scope"])
        self.assertIn("Lupranol", self.states["state_ivdre2024_lpo1_rigid_pur"]["state"]["composition_or_purity"]["text"])

    def test_pbs_means_sds_sample_counts_and_method_unknowns_match_selected_cells(self):
        for loading, mean in (("10", "922"), ("30", "969")):
            with self.subTest(formulation="B" + loading):
                prop = self.properties["refprop_ewurum2025_pbs_lignin" + loading + "_youngs_modulus"]
                self.assertEqual(prop["quantity"], "youngs_modulus")
                self.assertEqual(prop["quantity_dimension"], "pressure")
                self.assertEqual(prop["reported_value"]["number"], mean)
                self.assertEqual(prop["reported_value"]["value_text"], mean)
                self.assertEqual(prop["reported_value"]["unit_code"], "MPa")
                self.assertEqual(prop["reported_value"]["unit_text"], "MPa")
                self.assertEqual(prop["summary_statistic"], "reported_mean")
                self.assertEqual(prop["uncertainty"]["type"], "reported_standard_deviation")
                self.assertEqual(prop["uncertainty"]["number"], "77")
                self.assertEqual(prop["uncertainty"]["unit_code"], "MPa")
                self.assertEqual(prop["sample_count"]["value"], 10)
                self.assertEqual(prop["sample_count"]["relation"], "exact")
                self.assertIn("ASTM D1708", prop["conditions"]["test_standard"]["text"])
                for phrase in ("Instron 5500R-1132", "Epsilon 3542", "1 mm/min"):
                    self.assertIn(phrase, prop["method_definition"]["definition"])
                self.assertIsNone(prop["method_definition"]["extraction_window"])
                for name in ("temperature", "conditioning"):
                    self.assertEqual(prop["conditions"][name]["status"], "not_reported_in_inspected_source")
                    self.assertIsNone(prop["conditions"][name]["text"])
                humidity = next(item["fact"] for item in prop["conditions"]["additional_conditions"]
                                if item["name"] == "test_relative_humidity")
                self.assertEqual(humidity["status"], "not_reported_in_inspected_source")
                self.assertIn("Tukey grouping", prop["uncertainty_note"])
                evidence = [item for item in prop["evidence"] if "reported_value" in item["supports"]]
                self.assertTrue(evidence)
                for item in evidence:
                    self.assertIn("Table 6, B" + loading + " row", item["locator"])

    def test_spo2_measured_density_does_not_inherit_targets_or_unreported_statistics(self):
        prop = self.properties["refprop_ivdre2024_spo2_rigid_pur_mass_density"]
        self.assertEqual(prop["quantity"], "mass_density")
        self.assertEqual(prop["quantity_dimension"], "mass_per_volume")
        self.assertEqual(prop["reported_value"]["number"], "40.7")
        self.assertEqual(prop["reported_value"]["value_text"], "40.7")
        self.assertEqual(prop["reported_value"]["unit_code"], "kg/m^3")
        self.assertEqual(prop["density_basis"], "apparent")
        self.assertEqual(prop["summary_statistic"], "reported_value")
        self.assertIsNone(prop["uncertainty"])
        self.assertEqual(prop["uncertainty_status"], "not_reported_in_inspected_source")
        self.assertIsNone(prop["sample_count"]["value"])
        self.assertEqual(prop["sample_count"]["relation"], "not_reported")
        self.assertEqual(prop["conditions"]["test_standard"]["text"], "ISO 845:2006")
        self.assertEqual(prop["conditions"]["temperature"]["status"], "not_reported_in_inspected_source")
        self.assertIsNone(prop["conditions"]["temperature"]["text"])
        for item in prop["conditions"]["additional_conditions"]:
            self.assertEqual(item["fact"]["status"], "not_reported_in_inspected_source")
            self.assertIsNone(item["fact"]["text"])
        self.assertEqual({item["name"] for item in prop["conditions"]["additional_conditions"]},
                         {"density_test_humidity", "density_test_pressure", "density_specimen_dimensions"})
        self.assertIn("target density 45", prop["basis_note"])
        self.assertIn("compression-normalization density 40", prop["basis_note"])
        self.assertIn("Cured for 24 h at room temperature", prop["conditions"]["conditioning"]["text"])
        self.assertIn("not density-test conditions", prop["conditions"]["conditioning"]["notes"])
        porosity = self.states[prop["material_state_id"]]["state"]["porosity"]
        self.assertEqual(porosity["text"], "Closed-cell content 95 vol.%")
        self.assertIn("not total porosity", porosity["notes"])
        self.assertEqual(len(prop["source_discrepancies"]), 1)
        self.assertIn("SPO-1", prop["source_discrepancies"][0]["description"])
        self.assertIn("43.9", prop["source_discrepancies"][0]["description"])
        self.assertIn("40.7-43.5", prop["source_discrepancies"][0]["description"])
        self.assertIn("selected SPO-2 value 40.7", prop["source_discrepancies"][0]["disposition"])

    def test_existing_sources_rights_and_new_inspection_limits_remain_explicit(self):
        source_index = {row["id"]: row for row in self.baseline["sources"]["records"]}
        selected_sources = []
        for packet in self.packets:
            self.assertEqual(packet["materials"]["grades"], [])
            for source in packet["sources"]["records"]:
                self.assertEqual(source, source_index[source["id"]])
                self.assertEqual(source["license"]["identifier"], "CC-BY-4.0")
                selected_sources.append(source["id"])
        self.assertEqual(set(selected_sources), set(SOURCES))
        self.assertEqual(len(selected_sources), 2)
        for identifier in NEW_PROPERTIES:
            prop = self.properties[identifier]
            source_url, source_sha = SOURCES[prop["source_id"]]
            self.assertEqual(prop["source_document"]["url"], source_url)
            self.assertEqual(prop["source_document"]["sha256"], source_sha)
            self.assertEqual(prop["source_document"]["inspected_on"], "2026-10-17")
            self.assertEqual(prop["source_document"]["inspection_status"], "selected_content_inspected")
            self.assertEqual(prop["source_document"]["hash_status"], "recorded")
            self.assertEqual(prop["determination_basis"], "source_reports_measurement")
            self.assertEqual(prop["evidence_kind"], "published_experimental_reference")
            self.assertFalse(prop["verification"]["independent_scientific_review"])
            self.assertFalse(prop["verification"]["raw_data_reanalysis"])
            self.assertFalse(prop["universal_bound"])
            self.assertFalse(prop["engineering_allowable"])
            self.assertEqual(prop["evaluation_support"], "catalog_only")
            self.assertTrue(prop["evidence"])
            for item in prop["evidence"]:
                self.assertEqual(item["source_id"], prop["source_id"])
                self.assertEqual(item["url"], source_url)

    def test_full_graph_repeated_merges_and_three_identity_coverage_delta(self):
        validate_material_catalog(self.current["materials"], self.current["properties"], self.current["sources"])
        merged = self.baseline
        for packet in self.packets:
            append = {name: packet[name] for name in FILES}
            merged = merge_material_catalogs(merged["materials"], merged["properties"], merged["sources"], append)
            self.assertEqual(merge_material_catalogs(merged["materials"], merged["properties"], merged["sources"], append), merged)
        self.assertEqual(merged, self.current)
        coverage = material_quota_coverage(self.current["materials"], self.current["properties"], self.current["sources"])
        self.assertEqual(coverage["distinct_material_count"], 1079)
        self.assertEqual({key: value["admitted_unique_identity_count"] for key, value in coverage["classes"].items()},
                         {"natural": 1010, "metal": 22, "inorganic": 26, "polymer": 15, "composite": 6})
        self.assertEqual(coverage["classes"]["polymer"]["remaining"], 985)
        self.assertEqual(coverage["classes"]["composite"]["remaining"], 994)
        self.assertEqual({key for key, value in coverage["classes"].items() if value["target_met"]}, {"natural"})

    def test_actual_two_packet_cli_first_and_repeat_preserve_runtime_bytes_and_artifact_mtime(self):
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
            self.assertIn("Recorded baseline-to-candidate identity delta: 3", stdout.getvalue())
            self.assertIn("New artifact written: yes", stdout.getvalue())
            stored, mtime = output.read_bytes(), output.stat().st_mtime_ns
            with redirect_stdout(io.StringIO()) as stdout:
                self.assertEqual(main(arguments), 0)
            self.assertIn("Unchanged experimental integration artifact:", stdout.getvalue())
            self.assertIn("New artifact written: no", stdout.getvalue())
            self.assertEqual(output.read_bytes(), stored)
            self.assertEqual(output.stat().st_mtime_ns, mtime)
            self.assertEqual({path: path.read_bytes() for path in before}, before)
            package = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(package["catalogs"], self.current)
        for name, filename in FILES.items():
            self.assertEqual(serialized(package["catalogs"][name]), serialized(self.current[name]))
        report = package["report"]
        self.assertEqual(len(report["batches"]), 2)
        self.assertEqual(report["delta"], {"identities": 3, "grades": 0, "states": 3, "properties": 3, "sources": 0,
            "categories": {"natural": 0, "metal": 0, "inorganic": 0, "polymer": 1, "composite": 2}})
        self.assertEqual(report["formal_admitted_delta"], 0)
        self.assertEqual(report["released_main_count"], 1081)
        self.assertTrue(report["pending_gates"])

    def assert_mutation_rejected(self, packet_index, mutate, message, *, baseline_graph=None):
        """Keep both batches and refresh pins so validation, not digest mismatch, rejects the mutation."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            baseline = root / "baseline"
            baseline.mkdir()
            graph = self.baseline if baseline_graph is None else baseline_graph
            manifest = deepcopy(self.manifest)
            for name, filename in FILES.items():
                data = serialized(graph[name])
                (baseline / filename).write_bytes(data)
                manifest["baseline_sha256"]["reference_properties" if name == "properties" else name] = sha256(data).hexdigest()
            packet_root = root / "experimental/material-batches"
            packet_root.mkdir(parents=True)
            for index, original in enumerate(self.packets):
                packet = deepcopy(original)
                if index == packet_index:
                    mutate(packet)
                folder = packet_root / ("packet-" + str(index))
                folder.mkdir()
                for name, value in packet.items():
                    data = serialized(value)
                    filename = name + ".json"
                    (folder / filename).write_bytes(data)
                    manifest["batches"][index][name] = {"path": folder.name + "/" + filename,
                                                       "sha256": sha256(data).hexdigest()}
            manifest_path = packet_root / "integration.json"
            manifest_path.write_bytes(serialized(manifest))
            output = root / "package.json"
            before = {path: path.read_bytes() for path in root.rglob("*") if path.is_file()}
            with self.assertRaisesRegex(ValueError, message):
                write_package(baseline, manifest_path, output, repository_root=root)
            self.assertFalse(output.exists())
            self.assertEqual({path: path.read_bytes() for path in root.rglob("*") if path.is_file()}, before)

    def test_missing_property_in_either_packet_rejected_after_refreshed_pins(self):
        def mutate(packet):
            packet["properties"]["records"].pop()
        for index in range(2):
            with self.subTest(batch=index):
                self.assert_mutation_rejected(index, mutate, "property links and ownership must be reciprocal and complete")

    def test_wrong_quantity_dimension_in_either_packet_rejected_after_refreshed_pins(self):
        def mutate(packet):
            value = packet["properties"]["records"][0]["reported_value"]
            wrong = "kg/m^3" if value["unit_code"] == "MPa" else "MPa"
            value["unit_code"] = value["unit_text"] = wrong
        for index in range(2):
            with self.subTest(batch=index):
                self.assert_mutation_rejected(index, mutate, "unit does not match quantity dimension")

    def test_changed_existing_property_in_either_packet_rejected_without_partial_output(self):
        def mutate(packet):
            value = packet["properties"]["records"][0]["reported_value"]
            value["number"] = value["value_text"] = "999"
        for index in range(2):
            with self.subTest(batch=index):
                self.assert_mutation_rejected(index, mutate, "conflicting existing catalog record:", baseline_graph=self.current)


if __name__ == "__main__":
    unittest.main()
