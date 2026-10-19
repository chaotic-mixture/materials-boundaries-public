"""Selected primary-source facts for B45 and three EPDM/PCM formulations.

The constants below were transcribed from Ewurum Table 6 and Bianchi Tables
1/3/5, not generated from runtime data. Fixtures document that transcription;
agreement is not independent scientific validation or experimental replication.
These checks read local JSON only and exercise both candidate and runtime rows.
"""
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
BATCH_ROOT = ROOT / "experimental/material-batches"
PACKETS = {
    "pbs": "20261019-pbs-lignin45",
    "epdm": "20261019-epdm-pcm-hostatron",
}
SOURCES = {
    "pbs": "ewurum_mcdonald_2025_pbs_lignin",
    "epdm": "bianchi_2022_epdm_pcm",
}
BASE = "a592c89ede0dcced22579e56fc68b6fab4c55f49"
# stem, source row, packet, quantity, value, amplitude, unit, statistic, +/- type
CELLS = (
    ("ewurum2025_pbs_lignin45", "B45", "pbs", "youngs_modulus", "1206", "132",
     "MPa", "reported_mean", "reported_standard_deviation"),
    ("bianchi2022_epdm_h_p20", "EPDM_H_P20", "epdm", "mass_density", "0.55", "0.02",
     "g/cm^3", "reported_value", "reported_plus_minus_unspecified"),
    ("bianchi2022_epdm_h_p40", "EPDM_H_P40", "epdm", "mass_density", "0.66", "0.01",
     "g/cm^3", "reported_value", "reported_plus_minus_unspecified"),
    ("bianchi2022_epdm_h_p60", "EPDM_H_P60", "epdm", "mass_density", "0.70", "0.01",
     "g/cm^3", "reported_value", "reported_plus_minus_unspecified"),
)
# Source Table 3 gives distinct phr / nominal wt% / nominal vv% columns.
EPDM_LOADINGS = {
    "EPDM_H_P20": ("33.0", "20.0", "22.0"),
    "EPDM_H_P40": ("87.0", "40.0", "43.0"),
    "EPDM_H_P60": ("196.0", "60.0", "63.0"),
}
COMMON_RECIPE = {
    "Vistalon 2504 EPDM": "100", "Sulfur": "3.00", "Zinc oxide": "3.00",
    "Stearic acid": "1.00", "N550 carbon black": "20.00",
    "Tetramethylthiuram disulfide (TMTD)": "0.87",
    "Zinc dibutyl dithiocarbamate (ZDBC)": "2.50", "Hostatron P0168": "1.3",
}


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


class PolymerCompositesSourceFactsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runtime = {
            name: read_json(ROOT / "materials_boundaries/data" / filename)
            for name, filename in (("materials", "materials.json"),
                                   ("properties", "reference_properties.json"),
                                   ("sources", "sources.json"))
        }
        cls.packets = {
            key: {name: read_json(BATCH_ROOT / folder / filename)
                  for name, filename in (("materials", "materials.append.json"),
                                         ("properties", "reference-properties.append.json"),
                                         ("sources", "sources.reused.json"),
                                         ("review", "review.json"))}
            for key, folder in PACKETS.items()
        }
        cls.fixtures = {
            key: read_json(ROOT / "tests/fixtures" / filename)
            for key, filename in (
                ("pbs", "pbs_lignin45_source_transcription_20261019.json"),
                ("epdm", "epdm_pcm_hostatron_source_transcription_20261019.json"))
        }

    def one(self, rows, identifier):
        matches = [row for row in rows if row["id"] == identifier]
        self.assertEqual(len(matches), 1, "Missing or duplicate row: " + identifier)
        return matches[0]

    def views(self, cell):
        stem, _, packet, quantity, *_ = cell
        for label, graph in (("packet", self.packets[packet]), ("runtime", self.runtime)):
            yield (label, self.one(graph["materials"]["identities"], "mat_" + stem),
                   self.one(graph["materials"]["records"], "state_" + stem),
                   self.one(graph["properties"]["records"], "refprop_" + stem + "_" + quantity))

    def assert_unknown(self, fact):
        self.assertEqual(fact["status"], "not_reported_in_inspected_source")
        self.assertIsNone(fact["text"])

    def test_selected_cells_units_statistics_and_sample_counts(self):
        for cell in CELLS:
            _, code, _, quantity, value, amplitude, unit, statistic, uncertainty = cell
            for label, _, _, prop in self.views(cell):
                with self.subTest(formulation=code, location=label):
                    self.assertEqual(prop["quantity"], quantity)
                    self.assertEqual(prop["quantity_dimension"],
                                     "pressure" if quantity == "youngs_modulus" else "mass_per_volume")
                    self.assertEqual(prop["reported_value"]["kind"], "scalar")
                    for field in ("number", "value_text"):
                        self.assertEqual(prop["reported_value"][field], value)
                        self.assertEqual(prop["uncertainty"][field], amplitude)
                    self.assertEqual(prop["reported_value"]["unit_code"], unit)
                    self.assertEqual(prop["uncertainty"]["unit_code"], unit)
                    self.assertEqual(prop["summary_statistic"], statistic)
                    self.assertEqual(prop["uncertainty_status"], uncertainty)
                    self.assertEqual(prop["uncertainty"]["type"], uncertainty)
                    self.assertIsNone(prop["uncertainty"]["coverage_factor"])
                    self.assertIsNone(prop["uncertainty"]["confidence_level"])
                    self.assertEqual(prop["sample_count"]["value"], 10)
                    self.assertEqual(prop["sample_count"]["relation"], "exact")

    def test_evidence_selects_the_right_table_row_column_and_document(self):
        for cell in CELLS:
            _, code, packet, *_ = cell
            for label, _, _, prop in self.views(cell):
                with self.subTest(formulation=code, location=label):
                    evidence = [item for item in prop["evidence"]
                                if "reported_value" in item["supports"]]
                    self.assertTrue(evidence)
                    for item in evidence:
                        self.assertEqual(item["source_id"], SOURCES[packet])
                        self.assertEqual(item["url"], prop["source_document"]["url"])
                        self.assertIn(code + " row", item["locator"])
                        if packet == "pbs":
                            self.assertIn("p.12 Table 6", item["locator"])
                            self.assertIn("Young's Modulus (MPa)", item["locator"])
                        else:
                            self.assertIn("p.10 Table 5", item["locator"])
                            self.assertIn("rho_geom", item["locator"])
                            self.assertIn("geometrical density", prop["source_property_label"])

    def test_unknown_temperature_humidity_and_conditioning_are_not_defaulted(self):
        for cell in CELLS:
            for label, _, state, prop in self.views(cell):
                with self.subTest(formulation=cell[1], location=label):
                    for name in ("temperature", "conditioning"):
                        self.assert_unknown(prop["conditions"][name])
                    self.assert_unknown(state["state"]["conditioning"])
                    humidity = [item["fact"] for item in prop["conditions"]["additional_conditions"]
                                if "humidity" in item["name"]]
                    self.assertEqual(len(humidity), 1)
                    self.assert_unknown(humidity[0])

    def test_b45_keeps_the_simple_blend_and_tensile_method(self):
        for label, identity, state, prop in self.views(CELLS[0]):
            with self.subTest(location=label):
                composition = state["state"]["composition_or_purity"]["text"]
                self.assertIn("45 wt.% Indulin AT", composition)
                self.assertIn("total polymer mass", composition)
                self.assertIn("simple blend", composition)
                self.assertIn("not DCP-reactive R45", identity["identity_scope"])
                self.assertIn("FZ91PM/FZ91PB", identity["identity_scope"])
                self.assertIn("Injection-molded", state["state"]["product_form"]["text"])
                self.assertNotIn("DCP", state["state"]["processing"]["text"])
                self.assertNotIn("acetone", state["state"]["processing"]["text"].lower())
                for token in ("ASTM D1708", "Instron 5500R-1132", "Epsilon 3542", "1 mm/min"):
                    self.assertIn(token, prop["method_definition"]["definition"])
                self.assertIsNone(prop["method_definition"]["extraction_window"])
                self.assertIn("Tukey grouping", prop["uncertainty_note"])

    def test_epdm_geometrical_method_does_not_inherit_pycnometry(self):
        for cell in CELLS[1:]:
            for label, _, _, prop in self.views(cell):
                with self.subTest(formulation=cell[1], location=label):
                    method = prop["conditions"]["test_method"]["text"]
                    for token in ("Mass divided", "geometrical volume", "Gibertini E42", "caliper"):
                        self.assertIn(token, method)
                    self.assert_unknown(prop["conditions"]["test_standard"])
                    self.assertEqual(prop["density_basis"], "not_stated")
                    reported = [fact["text"] for name, fact in prop["conditions"].items()
                                if name != "additional_conditions" and fact["status"] == "reported"]
                    reported += [item["fact"]["text"]
                                 for item in prop["conditions"]["additional_conditions"]
                                 if item["fact"]["status"] == "reported"]
                    for text in reported:
                        for forbidden in ("23.0", "0.2 g", "60 replicate", "ASTM D6226", "AccuPyc"):
                            self.assertNotIn(forbidden, text)
                    convention = next(item["fact"]["text"]
                                      for item in prop["conditions"]["additional_conditions"]
                                      if item["name"] == "density_volume_convention")
                    self.assertIn("open and closed void volume", convention)

    def test_epdm_phr_recipes_and_nominal_percentages_stay_distinct(self):
        for cell in CELLS[1:]:
            phr, nominal, _ = EPDM_LOADINGS[cell[1]]
            for label, _, state, prop in self.views(cell):
                with self.subTest(formulation=cell[1], location=label):
                    recipe = state["state"]["composition_or_purity"]
                    self.assertIn("RT70HC paraffin " + phr + " phr", recipe["text"])
                    self.assertIn("nominal RT70HC label " + nominal + " wt%", recipe["text"])
                    for token in ("Vistalon 2504 EPDM 100 phr", "N550 carbon black 20.00 phr",
                                  "Hostatron P0168 1.3 phr", "TMTD 0.87 phr", "ZDBC 2.50 phr"):
                        self.assertIn(token, recipe["text"])
                    self.assertIn("unresolved percentage-denominator", recipe["notes"])
                    self.assertIn("without conversion, renormalization", recipe["notes"])
                    self.assertTrue(any("percentage-denominator" in item["description"]
                                        for item in prop["source_discrepancies"]))

    def test_theoretical_epdm_density_conflict_remains_excluded(self):
        for cell in CELLS[1:]:
            for label, _, state, prop in self.views(cell):
                with self.subTest(formulation=cell[1], location=label):
                    conflict = [item for item in prop["source_discrepancies"]
                                if "1.042" in item["description"] and "0.996" in item["description"]]
                    self.assertEqual(len(conflict), 1)
                    self.assertIn("rho_bulk", conflict[0]["description"])
                    self.assertIn("Do not substitute theoretical rho_bulk", conflict[0]["disposition"])
                    self.assertIn("calculate porosity", conflict[0]["disposition"])
                    self.assertEqual(state["state"]["porosity"]["status"], "not_verified")
                    self.assertIsNone(state["state"]["porosity"]["text"])

    def test_four_compositions_have_unique_identities_and_no_supplier_grade(self):
        identity_ids = {"mat_" + cell[0] for cell in CELLS}
        packet_ids = [row["id"] for packet in self.packets.values()
                      for row in packet["materials"]["identities"]]
        self.assertEqual(len(packet_ids), 4)
        self.assertEqual(set(packet_ids), identity_ids)
        self.assertTrue(all(not packet["materials"]["grades"] for packet in self.packets.values()))
        for cell in CELLS:
            stem, code, _, quantity, *_ = cell
            for label, identity, state, prop in self.views(cell):
                with self.subTest(formulation=code, location=label):
                    self.assertEqual(identity["category"], "composite")
                    self.assertEqual(state["identity_id"], identity["id"])
                    self.assertEqual(state["source_designation"], code)
                    self.assertIsNone(state["grade_id"])
                    self.assertEqual(state["property_ids"], ["refprop_" + stem + "_" + quantity])
                    self.assertEqual(prop["material_state_id"], state["id"])
                    for row in (identity, state):
                        self.assertEqual(set(row["names"]), {"en", "zh", "ja", "de"})
                        self.assertEqual(set(row["names"].values()), {row["names"]["en"]})
        base = self.one(self.runtime["materials"]["identities"], "mat_vistalon2504_n550_bianchi2022_epdm")
        self.assertEqual(base["category"], "composite")

    def test_existing_article_sources_and_cc_by_rights_are_reused(self):
        for name, packet in self.packets.items():
            with self.subTest(packet=name):
                self.assertEqual(len(packet["sources"]["records"]), 1)
                source = packet["sources"]["records"][0]
                self.assertEqual(source["id"], SOURCES[name])
                self.assertEqual(source, self.one(self.runtime["sources"]["records"], SOURCES[name]))
                self.assertEqual(source["license"]["identifier"], "CC-BY-4.0")
                review = packet["review"]
                self.assertEqual(review["base_commit"], BASE)
                self.assertEqual(review["new_sources"], 0)
                self.assertEqual(review["formal_admitted_delta"], 0)
                rights = review["rights"]
                self.assertEqual(rights["source_record_reused_unchanged"], SOURCES[name])
                self.assertEqual(rights["license_identifier"], "CC-BY-4.0")
                self.assertEqual(rights["license_url"], "https://creativecommons.org/licenses/by/4.0/")
                self.assertFalse(rights["assets_included"])
                self.assertFalse(rights["third_party_comparison_content_included"])

    def test_inspection_claims_distinguish_retained_pbs_pdf_from_epdm_text(self):
        for cell in CELLS:
            for label, _, _, prop in self.views(cell):
                with self.subTest(formulation=cell[1], location=label):
                    doc = prop["source_document"]
                    self.assertEqual(prop["verification"]["source_inspection_scope"], doc["inspection_scope"])
                    if cell[2] == "pbs":
                        self.assertEqual(doc["hash_status"], "recorded")
                        self.assertEqual(doc["sha256"],
                                         "766d17f0e92c7e93cd57a3a5e97dddff0cb66a84bba6bf9118fbd0796d4c2e6f")
                    else:
                        self.assertEqual(doc["hash_status"], "not_retained")
                        self.assertIsNone(doc["sha256"])
                        self.assertIn("not been reverified", doc["hash_note"])
                        self.assertIn("no new visual cross-check", doc["inspection_scope"])
        self.assertFalse(self.packets["pbs"]["review"]["source_access"]["fresh_successful_full_text_retrieval_claimed"])
        epdm = self.packets["epdm"]["review"]
        self.assertFalse(epdm["historical_hash_reverified"])
        self.assertFalse(epdm["verification"]["new_visual_cross_check"])
        self.assertFalse(epdm["verification"]["new_binary_hash_verification"])

    def test_fixture_cells_match_primary_transcriptions_without_scientific_oracle_claim(self):
        pbs = self.fixtures["pbs"]
        self.assertEqual(pbs["expected_facts"]["mean"], "1206")
        self.assertEqual(pbs["expected_facts"]["standard_deviation"], "132")
        self.assertEqual(pbs["expected_facts"]["unit"], "MPa")
        self.assertEqual(pbs["expected_facts"]["sample_count"], 10)
        self.assertFalse(pbs["expected_scope"]["dcp_reactive"])
        self.assertFalse(pbs["expected_scope"]["independent_scientific_review"])
        self.assertFalse(pbs["source_assets_bundled"])
        epdm = self.fixtures["epdm"]
        self.assertIn("not an independent scientific oracle", epdm["derivation"])
        self.assertFalse(epdm["independent_scientific_review"])
        self.assertEqual(len(epdm["common_recipe"]), len(COMMON_RECIPE))
        self.assertEqual({item["constituent"]: item["amount_text"] for item in epdm["common_recipe"]},
                         COMMON_RECIPE)
        self.assertEqual({item["unit"] for item in epdm["common_recipe"]}, {"phr"})
        self.assertEqual(len(epdm["cases"]), 3)
        facts = {item["source_designation"]: item for item in epdm["cases"]}
        self.assertEqual(set(facts), set(EPDM_LOADINGS))
        for cell in CELLS[1:]:
            fact = facts[cell[1]]
            phr, nominal, volume = EPDM_LOADINGS[cell[1]]
            self.assertEqual((fact["rt70hc_phr"], fact["rt70hc_nominal_wt_percent"],
                              fact["rt70hc_nominal_vv_percent"]), (phr, nominal, volume))
            self.assertEqual((fact["value"], fact["plus_minus"], fact["unit"]), cell[4:7])
            self.assertEqual(fact["uncertainty_type"], "reported_plus_minus_unspecified")
            self.assertEqual(fact["sample_count"], 10)
        for fixture in self.fixtures.values():
            self.assertEqual(fixture["base_commit"], BASE)
            self.assertEqual(fixture["formal_admitted_delta"], 0)

    def test_selected_properties_are_measured_references_not_calculated_allowables(self):
        for cell in CELLS:
            for label, _, _, prop in self.views(cell):
                with self.subTest(formulation=cell[1], location=label):
                    self.assertEqual(prop["evidence_kind"], "published_experimental_reference")
                    self.assertEqual(prop["determination_basis"], "source_reports_measurement")
                    self.assertEqual(prop["method_definition"]["type"], "source_reported_conventional")
                    self.assertEqual(prop["evaluation_support"], "catalog_only")
                    self.assertNotIn("derivation", prop)
                    self.assertFalse(prop["universal_bound"])
                    self.assertFalse(prop["engineering_allowable"])
                    self.assertFalse(prop["verification"]["independent_scientific_review"])
                    self.assertFalse(prop["verification"]["raw_data_reanalysis"])


if __name__ == "__main__":
    unittest.main()
