"""Synthetic-only fixtures for the open-ID, closed-semantics material lane."""
from copy import deepcopy
import json
from pathlib import Path
import unittest

from materials_boundaries.material_references import (
    _MATERIALS_SCHEMA, _PROPERTIES_SCHEMA, material_coverage, resolve_material,
    validate_material_catalog,
)

ROOT = Path(__file__).resolve().parents[1]


def synthetic_material_catalog():
    """Return independent clearly fictional records; never production coverage."""
    url = "https://example.invalid/synthetic-reference.pdf"
    def evidence(*tags):
        return [{"source_id": "synthetic_reference", "url": url,
                 "locator": "Synthetic test table 1, row SYN-A, density column", "supports": list(tags)}]
    def unknown():
        return {"status": "not_reported_in_inspected_source", "text": None,
                "evidence": [], "notes": None}
    names = {lang: "SYN-A synthetic test material" for lang in ("en", "zh", "ja", "de")}
    source = {"id": "synthetic_reference", "title": "Synthetic test-only reference",
              "authors": ["Synthetic Test Fixture"], "year": None, "doi": None,
              "urls": [url], "read_status": "Synthetic test data, not a factual source",
              "license": {"status": "synthetic", "identifier": None},
              "role": "manufacturer reference (synthetic fixture)", "claim_notes": [],
              "provenance": {"curation_date": "2026-10-04", "method": "Synthetic fixture"},
              "bundled_content": "Synthetic test data only"}
    identity = {"id": "mat_synthetic_a", "version": "1.0.0", "category": "metal",
                "name": names["en"], "names": names, "aliases": [],
                "identity_scope": "Fictional test identity, no physical claims",
                "evidence": evidence("material_identity")}
    grade = {"id": "grade_synthetic_a", "version": "1.0.0", "identity_id": identity["id"],
             "designation": "SYN-A", "authority": {"kind": "manufacturer", "name": "Synthetic Test Fixture"},
             "manufacturer": {"status": "reported", "text": "Synthetic Test Fixture",
                              "evidence": evidence("grade"), "notes": None},
             "aliases": [], "evidence": evidence("grade")}
    state = {"id": "state_synthetic_a", "version": "1.0.0", "identity_id": identity["id"],
             "grade_id": grade["id"], "name": names["en"], "names": deepcopy(names), "aliases": [],
             "source_designation": "SYN-A",
             "state": {key: unknown() for key in ("product_form", "processing", "temper_or_heat_treatment", "conditioning", "composition_or_purity", "reinforcement", "porosity", "orientation")},
             "source_scope": "Fictional test-only state", "evidence": evidence("state"),
             "property_ids": ["refprop_synthetic_a_density"], "evaluation_support": "catalog_only"}
    prop = {"id": state["property_ids"][0], "version": "1.0.0", "material_state_id": state["id"],
            "quantity": "mass_density", "quantity_dimension": "mass_per_volume",
            "source_property_label": "Density", "reported_value": {"kind": "scalar", "value_text": "2.70", "unit_text": "g/cm³", "unit_code": "g/cm^3", "number": "2.70"},
            "evidence_kind": "manufacturer_reference", "reporting_basis": "typical", "determination_basis": "not_stated",
            "basis_note": "Synthetic typical reference", "conditions": {key: unknown() for key in ("temperature", "test_standard", "test_method", "direction", "conditioning", "loading_rate")},
            "density_basis": "not_stated", "summary_statistic": "not_stated", "uncertainty": None,
            "uncertainty_status": "not_reported_in_inspected_source", "uncertainty_note": "No uncertainty is given by this synthetic fixture",
            "sample_count": {"value": None, "relation": "not_reported", "scope": "Selected synthetic reference value", "source_statement": "No count reported in synthetic fixture", "evidence": []},
            "method_definition": {"type": "source_reported_conventional", "definition": "Conventional density label; measurement method is unknown", "extraction_window": None, "evidence": evidence("method")},
            "source_discrepancies": [], "source_id": source["id"], "evidence": evidence("reported_value", "classification"),
            "source_document": {"url": url, "revision": None, "inspected_on": "2026-10-04", "sha256": None, "hash_status": "not_retained", "hash_note": "Synthetic fixture has no source artifact", "inspection_scope": "Synthetic table 1 and notes only", "inspection_status": "selected_content_inspected"},
            "scope_note": "Fictional test-only numeric fact", "evaluation_support": "catalog_only", "universal_bound": False,
            "engineering_allowable": False, "verification": {"source_inspection_scope": "Synthetic table 1 and notes only", "transcription_cross_check": "completed", "independent_scientific_review": False, "raw_data_reanalysis": False}}
    return ({"schema_version": "1.0.0", "identities": [identity], "grades": [grade], "records": [state]},
            {"schema_version": "1.0.0", "records": [prop]},
            {"schema_version": "1.0.0", "records": [source]})


def synthetic_mean_catalog():
    materials, properties, sources = synthetic_material_catalog()
    prop = properties["records"][0]
    sources["records"][0]["role"] = "published experimental paper (synthetic fixture)"
    prop.update(quantity="tensile_modulus", quantity_dimension="pressure", density_basis=None,
                source_property_label="Tensile modulus", evidence_kind="published_experimental_reference",
                reporting_basis="reported_summary", determination_basis="source_reports_measurement",
                summary_statistic="reported_mean", uncertainty_status="reported_standard_deviation")
    prop["reported_value"] = {"kind": "scalar", "value_text": "2500", "unit_text": "MPa", "unit_code": "MPa", "number": "2500"}
    prop["evidence"][0]["supports"].append("summary_statistic")
    def evidence(tag):
        item = deepcopy(prop["evidence"][0])
        item["supports"] = [tag]
        return [item]
    prop["uncertainty"] = {"type": "reported_standard_deviation", "value_text": "50.0", "number": "50.0", "unit_text": "MPa", "unit_code": "MPa", "scope": "Selected synthetic five-test group", "coverage_factor": None, "confidence_level": None, "evidence": evidence("uncertainty")}
    prop["sample_count"] = {"value": 5, "relation": "exact", "scope": "Selected synthetic five-test group", "source_statement": "Mean and standard deviation of five specimens", "evidence": evidence("sample_count")}
    prop["conditions"]["temperature"] = {"status": "reported", "text": "23 °C", "evidence": evidence("condition"), "notes": None}
    return materials, properties, sources


class MaterialReferenceContractTests(unittest.TestCase):
    def assert_rejected(self, mutate, mean=False):
        graph = synthetic_mean_catalog() if mean else synthetic_material_catalog()
        mutate(*graph)
        with self.assertRaises(ValueError):
            validate_material_catalog(*graph)

    def test_schemas_match_runtime_and_are_valid(self):
        import jsonschema
        for name, schema in (("materials", _MATERIALS_SCHEMA), ("reference_properties", _PROPERTIES_SCHEMA)):
            stored = json.loads((ROOT / "schemas" / (name + ".schema.json")).read_text())
            self.assertEqual(stored, schema)
            jsonschema.Draft202012Validator.check_schema(stored)
        for make in (synthetic_material_catalog, synthetic_mean_catalog):
            m, p, s = make()
            jsonschema.Draft202012Validator(_MATERIALS_SCHEMA, format_checker=jsonschema.FormatChecker()).validate(m)
            jsonschema.Draft202012Validator(_PROPERTIES_SCHEMA, format_checker=jsonschema.FormatChecker()).validate(p)
            validate_material_catalog(m, p, s)

    def test_scalar_unknowns_and_detached_resolver(self):
        m, p, s = synthetic_material_catalog()
        original = deepcopy((m, p, s))
        result = resolve_material("state_synthetic_a", m, p, s)
        self.assertEqual(result["identity"]["id"], "mat_synthetic_a")
        self.assertEqual(result["properties"][0]["reported_value"]["value_text"], "2.70")
        self.assertEqual(len(result["sources"]), 1)
        result["state"]["name"] = "changed"
        self.assertEqual((m, p, s), original)
        self.assertRaises(ValueError, resolve_material, "state_missing", m, p, s)

    def test_reference_scalar_measurement_does_not_change_evidence_class(self):
        m, p, s = synthetic_material_catalog()
        p["records"][0]["determination_basis"] = "source_reports_measurement"
        validate_material_catalog(m, p, s)
        self.assertEqual(p["records"][0]["evidence_kind"], "manufacturer_reference")

    def test_reported_standard_and_not_applicable_explanation(self):
        m, p, s = synthetic_material_catalog()
        evidence = deepcopy(p["records"][0]["evidence"])
        evidence[0]["supports"] = ["condition"]
        p["records"][0]["conditions"]["test_standard"] = {"status": "reported", "text": "Synthetic ISO test", "evidence": evidence, "notes": None}
        m["records"][0]["state"]["reinforcement"] = {"status": "not_applicable", "text": None, "evidence": [], "notes": "Synthetic material is explicitly unreinforced"}
        validate_material_catalog(m, p, s)

    def test_interval_and_comparison_preserve_source_typography(self):
        for representation in (
            {"kind": "interval", "value_text": "2.60–2.70", "lower": "2.60", "upper": "2.70", "endpoint_semantics": "source_reported_not_a_confidence_interval"},
            {"kind": "comparison", "value_text": ">0,90", "operator": ">", "number": "0.90"},
            {"kind": "comparison", "value_text": "≥ 0.90", "operator": ">=", "number": "0.90"},
        ):
            with self.subTest(representation=representation):
                m, p, s = synthetic_material_catalog()
                p["records"][0]["reported_value"] = {**representation, "unit_text": "g/cm³", "unit_code": "g/cm^3"}
                p["records"][0]["reporting_basis"] = "guideline"
                validate_material_catalog(m, p, s)
                self.assertEqual(resolve_material(m["records"][0]["id"], m, p, s)["properties"][0]["reported_value"]["value_text"], representation["value_text"])

    def test_grouped_number_and_actual_density_unit_spellings(self):
        for value, number, spelling, code in (("1,000.00", "1000.00", "kg/m³", "kg/m^3"), ("1.000,00", "1000.00", "kg/dm³", "kg/dm^3"), ("0.098", "0.098", "lb./in.³", "lb/in^3")):
            m, p, s = synthetic_material_catalog()
            p["records"][0]["reported_value"].update(value_text=value, number=number, unit_text=spelling, unit_code=code)
            validate_material_catalog(m, p, s)

    def test_mean_sd_exact_count_and_at_least_without_sd(self):
        m, p, s = synthetic_mean_catalog()
        validate_material_catalog(m, p, s)
        p["records"][0]["uncertainty"] = None
        p["records"][0]["uncertainty_status"] = "not_reported_in_inspected_source"
        p["records"][0]["sample_count"]["relation"] = "at_least"
        p["records"][0]["sample_count"]["source_statement"] = "At least five tests"
        validate_material_catalog(m, p, s)

    def test_published_scalar_without_invented_mean(self):
        m, p, s = synthetic_material_catalog()
        sources = s["records"][0]
        sources["role"] = "published experimental paper"
        p["records"][0].update(evidence_kind="published_experimental_reference", determination_basis="source_reports_measurement", reporting_basis="not_stated")
        validate_material_catalog(m, p, s)

    def test_counts_new_grade_state_property_and_alias(self):
        m, p, s = synthetic_material_catalog()
        self.assertEqual(material_coverage(m, p)["material_identity_count"], 1)
        m["identities"][0]["aliases"].append({"language": "de", "text": "Synthetisch"})
        second = deepcopy(p["records"][0]); second["id"] = "refprop_synthetic_second"
        second["source_property_label"] = "Separately sourced density"
        second["evidence"][0]["locator"] = "Synthetic table 2, row SYN-A, density"
        p["records"].append(second); m["records"][0]["property_ids"].append(second["id"])
        self.assertEqual(material_coverage(m, p)["property_record_count"], 2)
        new_grade = deepcopy(m["grades"][0]); new_grade.update(id="grade_new_vendor_b", designation="SYN-B")
        new_grade["evidence"][0]["locator"] = "Synthetic table 1, distinct grade SYN-B designation"
        m["grades"].append(new_grade)
        new_state = deepcopy(m["records"][0]); new_state.update(id="state_new_vendor_b", grade_id=new_grade["id"], property_ids=["refprop_new_vendor_b"])
        m["records"].append(new_state)
        new_prop = deepcopy(second); new_prop.update(id="refprop_new_vendor_b", material_state_id=new_state["id"])
        p["records"].append(new_prop)
        third_state = deepcopy(new_state); third_state.update(id="state_new_vendor_c", property_ids=["refprop_new_vendor_c"], source_scope="Synthetic SYN-B cold-worked state")
        third_state["state"]["processing"] = {"status": "reported", "text": "Cold worked", "evidence": deepcopy(third_state["evidence"]), "notes": None}
        third_state["state"]["processing"]["evidence"][0]["locator"] = "Synthetic table 2, SYN-B cold-worked processing"
        m["records"].append(third_state)
        third_prop = deepcopy(second); third_prop.update(id="refprop_new_vendor_c", material_state_id=third_state["id"])
        p["records"].append(third_prop)
        validate_material_catalog(m, p, s)
        counts = material_coverage(m, p)
        self.assertEqual([counts[key] for key in ("material_identity_count", "grade_count", "material_state_count", "property_record_count")], [1, 2, 3, 4])

    def test_ungraded_and_empty_catalogue(self):
        m, p, s = synthetic_material_catalog(); m["grades"] = []; m["records"][0]["grade_id"] = None
        validate_material_catalog(m, p, s)
        self.assertIsNone(resolve_material(m["records"][0]["id"], m, p, s)["grade"])
        self.assertEqual(material_coverage(m, p)["grade_count"], 0)
        validate_material_catalog({"schema_version": "1.0.0", "identities": [], "grades": [], "records": []}, {"schema_version": "1.0.0", "records": []}, s)

    def test_technical_and_computational_reference_classes(self):
        for evidence, determination, role in (
            ("technical_association_reference", "not_stated", "technical association reference"),
            ("published_computational_reference", "source_reports_calculation", "published computation paper"),
        ):
            m, p, s = synthetic_material_catalog()
            p["records"][0].update(evidence_kind=evidence, determination_basis=determination)
            s["records"][0]["role"] = role
            validate_material_catalog(m, p, s)
        m, p, s = synthetic_material_catalog()
        s["records"][0]["role"] = "technical-association reference"
        self.assertRaises(ValueError, validate_material_catalog, m, p, s)

    def test_zero_sd_recorded_hash_and_secondary_resolved_source(self):
        m, p, s = synthetic_mean_catalog()
        p["records"][0]["uncertainty"].update(number="0.0", value_text="0.0")
        p["records"][0]["source_document"].update(sha256="f" * 64, hash_status="recorded", hash_note=None)
        other = deepcopy(s["records"][0]); other["id"] = "synthetic_identity_reference"
        s["records"].append(other)
        m["identities"][0]["evidence"][0]["source_id"] = other["id"]
        validate_material_catalog(m, p, s)
        self.assertEqual(len(resolve_material(m["records"][0]["id"], m, p, s)["sources"]), 2)

    def test_homepage_only_and_invalid_dates_or_hashes(self):
        for field, value in (("inspected_on", "2026-02-30"), ("sha256", "a" * 64 + "\n")):
            self.assert_rejected(lambda m, p, s: p["records"][0]["source_document"].update({field: value}))
        m, p, s = synthetic_material_catalog()
        old = s["records"][0]["urls"][0]
        m, p, s = json.loads(json.dumps([m, p, s]).replace(old, "https://example.invalid/"))
        self.assertRaises(ValueError, validate_material_catalog, m, p, s)
        self.assert_rejected(lambda m, p, s: m["identities"][0].update(id="mat_bad\n"))

    def test_shape_mutations_rejected_by_schema_and_runtime(self):
        import jsonschema
        mutations = [
            ("m", lambda m, p, s: m.update(schema_version="9.0.0")),
            ("m", lambda m, p, s: m["identities"][0]["names"].pop("zh")),
            ("m", lambda m, p, s: m["records"][0]["state"]["porosity"].update(text="0")),
            ("m", lambda m, p, s: m["records"][0].update(evaluator="model")),
            ("m", lambda m, p, s: m["records"][0].update(property_ids=[])),
            ("m", lambda m, p, s: m["records"][0].update(evaluation_support="evaluate")),
            ("p", lambda m, p, s: p["records"][0].update(universal_bound=True)),
            ("p", lambda m, p, s: p["records"][0].update(engineering_allowable=0)),
            ("p", lambda m, p, s: p["records"][0].update(quantity="apparent_tensile_modulus")),
            ("p", lambda m, p, s: p["records"][0]["reported_value"].update(number=True)),
            ("p", lambda m, p, s: p["records"][0]["reported_value"].update(number="1e999999")),
            ("p", lambda m, p, s: p["records"][0]["reported_value"].update(si_number="2700")),
            ("p", lambda m, p, s: p["records"][0]["sample_count"].update(value=5)),
        ]
        for target, mutate in mutations:
            with self.subTest(mutate=mutate):
                m, p, s = synthetic_material_catalog(); mutate(m, p, s)
                with self.assertRaises(jsonschema.ValidationError):
                    jsonschema.validate(m if target == "m" else p, _MATERIALS_SCHEMA if target == "m" else _PROPERTIES_SCHEMA)
                with self.assertRaises(ValueError): validate_material_catalog(m, p, s)

    def test_graph_mutations(self):
        mutations = [
            lambda m, p, s: m["identities"].append(deepcopy(m["identities"][0])),
            lambda m, p, s: m["grades"][0].update(identity_id="mat_missing"),
            lambda m, p, s: m["records"][0].update(grade_id="grade_missing"),
            lambda m, p, s: p["records"][0].update(material_state_id="state_missing"),
            lambda m, p, s: m["records"][0]["property_ids"].append("refprop_missing"),
            lambda m, p, s: m["records"][0]["property_ids"].append(m["records"][0]["property_ids"][0]),
            lambda m, p, s: s["records"].clear(),
            lambda m, p, s: s["records"].append(deepcopy(s["records"][0])),
            lambda m, p, s: s["records"].append({**deepcopy(s["records"][0]), "id": "mat_synthetic_a"}),
            lambda m, p, s: p["records"][0]["evidence"][0].update(source_id="missing"),
            lambda m, p, s: p["records"][0]["evidence"][0].update(supports=["classification"]),
            lambda m, p, s: p["records"][0]["evidence"][0].update(locator="website"),
            lambda m, p, s: p["records"][0]["evidence"][0].update(url="https://example.invalid/other.pdf"),
            lambda m, p, s: m["identities"].append({**deepcopy(m["identities"][0]), "id": "mat_orphan"}),
            lambda m, p, s: m["grades"].append({**deepcopy(m["grades"][0]), "id": "grade_orphan"}),
        ]
        for mutate in mutations:
            with self.subTest(mutate=mutate): self.assert_rejected(mutate)

    def test_numeric_and_semantic_mutations(self):
        for number in ("NaN", "Infinity", "-1", "0", "1e2", "9" * 25, "2.700"):
            with self.subTest(number=number):
                self.assert_rejected(lambda m, p, s: p["records"][0]["reported_value"].update(number=number))
        mutations = [
            lambda m, p, s: p["records"][0].update(quantity_dimension="pressure"),
            lambda m, p, s: p["records"][0]["reported_value"].update(unit_code="MPa", unit_text="MPa"),
            lambda m, p, s: p["records"][0]["reported_value"].update(unit_text="kg/m³"),
            lambda m, p, s: p["records"][0].update(density_basis=None),
            lambda m, p, s: p["records"][0].update(summary_statistic="reported_mean"),
            lambda m, p, s: p["records"][0].update(uncertainty_status="reported_standard_deviation"),
            lambda m, p, s: p["records"][0].update(evidence_kind="published_experimental_reference", determination_basis="source_reports_measurement"),
            lambda m, p, s: p["records"][0]["source_document"].update(hash_status="recorded"),
            lambda m, p, s: p["records"][0]["verification"].update(source_inspection_scope="whole paper"),
        ]
        for mutate in mutations:
            with self.subTest(mutate=mutate): self.assert_rejected(mutate)

    def test_mean_sd_count_mutations(self):
        mutations = [
            lambda m, p, s: p["records"][0].update(reporting_basis="typical"),
            lambda m, p, s: p["records"][0].update(summary_statistic="reported_value"),
            lambda m, p, s: p["records"][0]["uncertainty"].update(type="standard_error"),
            lambda m, p, s: p["records"][0]["uncertainty"].update(unit_code="GPa", unit_text="GPa"),
            lambda m, p, s: p["records"][0]["uncertainty"].update(number="-1", value_text="-1"),
            lambda m, p, s: p["records"][0]["uncertainty"].update(evidence=[]),
            lambda m, p, s: p["records"][0]["sample_count"].update(value=True),
            lambda m, p, s: p["records"][0]["sample_count"].update(value=0),
            lambda m, p, s: p["records"][0]["sample_count"].update(evidence=[]),
            lambda m, p, s: p["records"][0].update(determination_basis="source_reports_calculation"),
            lambda m, p, s: p["records"][0].update(source_property_label="Apparent tensile modulus"),
        ]
        for mutate in mutations:
            with self.subTest(mutate=mutate): self.assert_rejected(mutate, mean=True)

    def test_invalid_interval_comparison_and_duplicate_fact(self):
        for value in (
            {"kind": "interval", "value_text": "2.70–2.60", "lower": "2.70", "upper": "2.60", "endpoint_semantics": "source_reported_not_a_confidence_interval"},
            {"kind": "interval", "value_text": "2.70–2.70", "lower": "2.70", "upper": "2.70", "endpoint_semantics": "source_reported_not_a_confidence_interval"},
            {"kind": "comparison", "value_text": ">0,90", "operator": "<", "number": "0.90"},
        ):
            self.assert_rejected(lambda m, p, s: p["records"][0].update(reported_value={**value, "unit_text": "g/cm³", "unit_code": "g/cm^3"}))
        m, p, s = synthetic_material_catalog(); duplicate = deepcopy(p["records"][0]); duplicate["id"] = "refprop_duplicate"
        p["records"].append(duplicate); m["records"][0]["property_ids"].append(duplicate["id"])
        self.assertRaises(ValueError, validate_material_catalog, m, p, s)
        self.assertRaises(ValueError, material_coverage, m, p)
        duplicate["reported_value"]["value_text"] = "2,70"
        self.assertRaises(ValueError, material_coverage, m, p)

    def test_all_control_code_text_and_url_mutations_fail_both_contracts(self):
        import jsonschema
        validators = {
            "m": jsonschema.Draft202012Validator(_MATERIALS_SCHEMA),
            "p": jsonschema.Draft202012Validator(_PROPERTIES_SCHEMA),
        }
        controls = [chr(value) for value in (*range(0x20), *range(0x7f, 0xa0))]
        fields = (
            ("m", lambda m, p, control: m["identities"][0].update(name="source" + control + "name")),
            ("m", lambda m, p, control: m["records"][0]["names"].update(en="name" + control + "suffix")),
            ("m", lambda m, p, control: m["records"][0].update(source_designation="SYN" + control + "A")),
            ("m", lambda m, p, control: m["grades"][0]["authority"].update(name="authority" + control)),
            ("p", lambda m, p, control: p["records"][0]["evidence"][0].update(locator="Table 1" + control + "row A")),
            ("p", lambda m, p, control: p["records"][0]["evidence"][0].update(url="https://example.invalid/" + control + "table")),
            ("p", lambda m, p, control: p["records"][0]["source_document"].update(url="https://example.invalid/" + control + "table")),
            ("p", lambda m, p, control: p["records"][0].update(source_property_label="Density" + control)),
        )
        for control in controls:
            for target, mutate in fields:
                with self.subTest(control=ord(control), target=target):
                    m, p, s = synthetic_material_catalog()
                    mutate(m, p, control)
                    self.assertTrue(list(validators[target].iter_errors(m if target == "m" else p)))
                    self.assertRaises(ValueError, validate_material_catalog, m, p, s)

    def test_complete_terminal_injection_payload_is_rejected(self):
        payload = "\x1b[2J\x1b[HFORGED SAFE RESULT\x1b]8;;https://attacker.invalid\x07CLICK\x1b]8;;\x07"
        self.assert_rejected(lambda m, p, s: m["records"][0]["names"].update(en=payload))
        for control in ("\x1b", "\x07", "\x9b"):
            self.assert_rejected(lambda m, p, s: s["records"][0].update(id="synthetic" + control + "source"))

    def test_complete_identity_grade_state_property_clone_cannot_inflate_counts(self):
        m, p, s = synthetic_material_catalog()
        identity = deepcopy(m["identities"][0]); identity["id"] = "mat_clone"
        grade = deepcopy(m["grades"][0]); grade.update(id="grade_clone", identity_id=identity["id"])
        state = deepcopy(m["records"][0]); state.update(id="state_clone", identity_id=identity["id"], grade_id=grade["id"], property_ids=["refprop_clone"])
        prop = deepcopy(p["records"][0]); prop.update(id="refprop_clone", material_state_id=state["id"])
        m["identities"].append(identity); m["grades"].append(grade); m["records"].append(state); p["records"].append(prop)
        self.assertRaisesRegex(ValueError, "duplicate structural identity", validate_material_catalog, m, p, s)
        self.assertRaisesRegex(ValueError, "duplicate structural identity", material_coverage, m, p)
        identity.update(name="Different display label", names={lang: "Different translation" for lang in ("en", "zh", "ja", "de")}, aliases=[{"language": "en", "text": "Another alias"}])
        identity["evidence"][0]["supports"].reverse()
        self.assertRaisesRegex(ValueError, "duplicate structural identity", material_coverage, m, p)

    def test_exact_grade_and_state_clones_rejected(self):
        for clone_grade in (True, False):
            m, p, s = synthetic_material_catalog()
            state = deepcopy(m["records"][0]); state.update(id="state_clone", property_ids=["refprop_clone"])
            prop = deepcopy(p["records"][0]); prop.update(id="refprop_clone", material_state_id=state["id"])
            if clone_grade:
                grade = deepcopy(m["grades"][0]); grade.update(id="grade_clone", aliases=[{"language": "und", "text": "Alternate spelling"}])
                m["grades"].append(grade); state["grade_id"] = grade["id"]
            else:
                state.update(name="Translated display", names={lang: "Translated" for lang in ("en", "zh", "ja", "de")})
            m["records"].append(state); p["records"].append(prop)
            kind = "grade" if clone_grade else "state"
            self.assertRaisesRegex(ValueError, "duplicate structural " + kind, validate_material_catalog, m, p, s)
            self.assertRaisesRegex(ValueError, "duplicate structural " + kind, material_coverage, m, p)

    def test_distinct_source_supported_identity_is_data_only(self):
        m, p, s = synthetic_material_catalog()
        identity = deepcopy(m["identities"][0]); identity.update(id="mat_distinct", identity_scope="Distinct synthetic formulation B")
        identity["evidence"][0]["locator"] = "Synthetic table 2, distinct formulation B"
        state = deepcopy(m["records"][0]); state.update(id="state_distinct", identity_id=identity["id"], grade_id=None, property_ids=["refprop_distinct"])
        state["source_scope"] = "Fictional formulation B source scope"
        prop = deepcopy(p["records"][0]); prop.update(id="refprop_distinct", material_state_id=state["id"])
        m["identities"].append(identity); m["records"].append(state); p["records"].append(prop)
        validate_material_catalog(m, p, s)
        self.assertEqual(material_coverage(m, p)["material_identity_count"], 2)

    def test_optional_condition_presence_and_order_do_not_create_new_properties(self):
        for populated in (False, True):
            m, p, s = synthetic_material_catalog()
            original = p["records"][0]
            if populated:
                evidence = deepcopy(original["evidence"])
                evidence[0]["supports"] = ["condition"]
                original["conditions"]["additional_conditions"] = [
                    {"name": name, "fact": {"status": "reported", "text": text,
                                            "evidence": deepcopy(evidence), "notes": None}}
                    for name, text in (("humidity", "50% RH"), ("pressure", "101 kPa"))
                ]
            duplicate = deepcopy(original); duplicate["id"] = "refprop_reordered_clone"
            duplicate["conditions"]["additional_conditions"] = list(reversed(duplicate["conditions"].get("additional_conditions", [])))
            duplicate["evidence"][0]["supports"].reverse()
            p["records"].append(duplicate); m["records"][0]["property_ids"].append(duplicate["id"])
            self.assertRaisesRegex(ValueError, "duplicate source fact", validate_material_catalog, m, p, s)
            self.assertRaisesRegex(ValueError, "duplicate source fact", material_coverage, m, p)
            # A separately sourced result still counts, under the same generic
            # reporting contract; no material-specific dispatch is involved.
            duplicate["reported_value"].update(value_text="2.71", number="2.71")
            duplicate["evidence"][0]["locator"] = "Synthetic table 2, independent density result"
            validate_material_catalog(m, p, s)
            self.assertEqual(material_coverage(m, p)["property_record_count"], 2)

    def test_surrogates_loaded_from_json_are_rejected_but_astral_text_survives(self):
        import jsonschema
        from materials_boundaries.material_references import validate_reference_text
        for codepoint in (0xd800, 0xdbff, 0xdc00, 0xdfff):
            bad = "broken_" + chr(codepoint)
            m, p, s = synthetic_material_catalog()
            m["records"][0]["names"]["en"] = bad
            m, p, s = json.loads(json.dumps([m, p, s], ensure_ascii=True))
            self.assertRaises(jsonschema.ValidationError, jsonschema.Draft202012Validator(_MATERIALS_SCHEMA).validate, m)
            self.assertRaises(ValueError, validate_material_catalog, m, p, s)
            self.assertRaises(ValueError, validate_reference_text, bad)
            m, p, s = synthetic_material_catalog()
            p["records"][0]["evidence"][0]["url"] = "https://example.invalid/" + bad
            p = json.loads(json.dumps(p, ensure_ascii=True))
            self.assertRaises(jsonschema.ValidationError, jsonschema.Draft202012Validator(_PROPERTIES_SCHEMA).validate, p)
            self.assertRaises(ValueError, validate_material_catalog, m, p, s)
            self.assert_rejected(lambda m, p, s: p["records"][0]["evidence"][0].update(locator=bad))
        m, p, s = synthetic_material_catalog()
        m["records"][0]["names"]["en"] = "Synthetic microscopy \U0001f52c"
        m, p, s = json.loads(json.dumps([m, p, s], ensure_ascii=True))
        validate_material_catalog(m, p, s)
        validate_reference_text(m["records"][0]["names"]["en"])
        resolved = resolve_material(m["records"][0]["id"], m, p, s)
        self.assertEqual(resolved["state"]["names"]["en"].encode("utf-8"), "Synthetic microscopy \U0001f52c".encode("utf-8"))

    def test_resolution_validates_unselected_records(self):
        m, p, s = synthetic_material_catalog()
        m["identities"].append({**deepcopy(m["identities"][0]), "id": "mat_unselected_orphan"})
        self.assertRaises(ValueError, resolve_material, "state_synthetic_a", m, p, s)


if __name__ == "__main__":
    unittest.main()
