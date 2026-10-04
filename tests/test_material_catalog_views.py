"""Synthetic-only reference catalogue query, rendering and CLI contracts."""
import copy
from contextlib import contextmanager, redirect_stderr, redirect_stdout
import io
import json
import unittest
from unittest.mock import Mock, patch

from materials_boundaries.catalog import CatalogLookupError, query_catalog, read_catalog
from materials_boundaries.catalog_output import render_catalog
from materials_boundaries.cli import main
from materials_boundaries.material_presentation import material_labels, validate_material_locales
from materials_boundaries.material_references import validate_material_catalog


LANGUAGES = ("en", "zh", "ja", "de")


def synthetic_catalogs():
    """Nothing in this isolated graph is real, accepted or shipped material data."""
    def evidence(tag, source="synthetic_manufacturer"):
        return [{"source_id": source, "url": f"https://example.org/{source}.pdf",
                 "locator": "SYNTHETIC test table A, row 1", "supports": [tag]}]

    def unknown():
        return {"status": "not_reported_in_inspected_source", "text": None,
                "evidence": [], "notes": "SYNTHETIC fixture: no physical condition is asserted."}

    identity = {"id": "mat_synthetic_alpha", "version": "1.0.0", "category": "metal",
                "name": "SYNTHETIC Alpha", "names": {"en": "SYNTHETIC Alpha", "zh": "合成测试甲",
                "ja": "合成試験甲", "de": "SYNTHETISCH Straße"},
                "aliases": [{"language": "und", "text": "SYNTH-ALIAS"}],
                "identity_scope": "SYNTHETIC TEST ONLY, not a real material.",
                "evidence": evidence("material_identity")}
    grade = {"id": "grade_synthetic_alpha", "version": "1.0.0", "identity_id": identity["id"],
             "designation": "SYNTH-GRADE-001", "authority": {"kind": "source_designation", "name": "Synthetic test"},
             "manufacturer": unknown(), "aliases": [{"language": "und", "text": "TEST-GRADE-ALIAS"}],
             "evidence": evidence("grade")}
    state = {"id": "state_synthetic_alpha", "version": "1.0.0", "identity_id": identity["id"],
             "grade_id": grade["id"], "name": "SYNTHETIC Alpha test state", "names": copy.deepcopy(identity["names"]),
             "aliases": [], "source_designation": "SYNTHETIC Alpha original",
             "state": {key: unknown() for key in ("product_form", "processing", "temper_or_heat_treatment",
                       "conditioning", "composition_or_purity", "reinforcement", "porosity", "orientation")},
             "source_scope": "SYNTHETIC scope, no production coverage.", "evidence": evidence("state"),
             "property_ids": ["refprop_synthetic_density", "refprop_synthetic_modulus"],
             "evaluation_support": "catalog_only"}
    density = {"id": state["property_ids"][0], "version": "1.0.0", "material_state_id": state["id"],
               "quantity": "mass_density", "quantity_dimension": "mass_per_volume", "source_property_label": "SYNTHETIC Density",
               "reported_value": {"kind": "scalar", "value_text": "2,700", "number": "2.700", "unit_text": "g/cm³", "unit_code": "g/cm^3"},
               "evidence_kind": "manufacturer_reference", "reporting_basis": "typical", "determination_basis": "not_stated",
               "basis_note": "SYNTHETIC manufacturer typical value.",
               "conditions": {key: unknown() for key in ("temperature", "test_standard", "test_method", "direction", "conditioning", "loading_rate")},
               "density_basis": "not_stated", "summary_statistic": "not_stated", "uncertainty": None,
               "uncertainty_status": "not_reported_in_inspected_source", "uncertainty_note": "No numerical uncertainty reported in synthetic fixture.",
               "sample_count": {"value": None, "relation": "not_reported", "scope": "No specimen count asserted.", "source_statement": "Not reported.", "evidence": []},
               "method_definition": {"type": "source_reported_conventional", "definition": "SYNTHETIC density only; no invented method.",
                                     "extraction_window": None, "evidence": evidence("method")},
               "source_discrepancies": [], "source_id": "synthetic_manufacturer",
               "evidence": evidence("reported_value") + evidence("classification"),
               "source_document": {"url": "https://example.org/synthetic_manufacturer.pdf", "revision": None, "inspected_on": "2026-10-04",
                                   "sha256": None, "hash_status": "not_retained", "hash_note": "Synthetic test document does not exist.",
                                   "inspection_scope": "SYNTHETIC test table A, row 1", "inspection_status": "selected_content_inspected"},
               "scope_note": "SYNTHETIC ONLY; no test conditions are assumed.", "evaluation_support": "catalog_only",
               "universal_bound": False, "engineering_allowable": False,
               "verification": {"source_inspection_scope": "SYNTHETIC test table A, row 1", "transcription_cross_check": "completed",
                                "independent_scientific_review": False, "raw_data_reanalysis": False}}
    modulus = copy.deepcopy(density)
    modulus.update(id=state["property_ids"][1], quantity="tensile_modulus", quantity_dimension="pressure",
                   source_property_label="SYNTHETIC Tensile modulus", density_basis=None,
                   reported_value={"kind": "scalar", "value_text": "3,400.0", "number": "3400.0", "unit_text": "N/mm²", "unit_code": "N/mm^2"},
                   evidence_kind="published_experimental_reference", reporting_basis="reported_summary",
                   determination_basis="source_reports_measurement", summary_statistic="reported_mean", source_id="synthetic_paper",
                   basis_note="SYNTHETIC published mean, not manufacturer typical data.",
                   uncertainty={"type": "reported_standard_deviation", "value_text": "25.0", "number": "25.0", "unit_text": "N/mm²",
                                "unit_code": "N/mm^2", "scope": "SYNTHETIC group spread", "coverage_factor": None, "confidence_level": None,
                                "evidence": evidence("uncertainty", "synthetic_paper")},
                   uncertainty_status="reported_standard_deviation", uncertainty_note="Reported SD, no confidence interval.",
                   sample_count={"value": 5, "relation": "at_least", "scope": "SYNTHETIC test group", "source_statement": "At least five specimens.",
                                 "evidence": evidence("sample_count", "synthetic_paper")})
    modulus["source_document"]["url"] = "https://example.org/synthetic_paper.pdf"
    modulus["method_definition"]["evidence"] = evidence("method", "synthetic_paper")
    modulus["evidence"] = sum((evidence(tag, "synthetic_paper") for tag in ("reported_value", "classification", "summary_statistic")), [])
    modulus["conditions"]["additional_conditions"] = [{"name": "SYNTHETIC extra condition", "fact": unknown()}]
    sources = {"schema_version": "1.0.0", "records": [
        {"id": identifier, "title": "SYNTHETIC original source title " + identifier,
         "role": role, "urls": [f"https://example.org/{identifier}.pdf"],
         "read_status": "synthetic_test_fixture_only", "license": {"status": "synthetic_not_for_release", "identifier": None}}
        for identifier, role in (("synthetic_manufacturer", "manufacturer_reference"), ("synthetic_paper", "published_experimental_reference"))]}
    materials = {"schema_version": "1.0.0", "identities": [identity], "grades": [grade], "records": [state]}
    properties = {"schema_version": "1.0.0", "records": [density, modulus]}
    validate_material_catalog(materials, properties, sources)
    return {"materials": materials, "reference_properties": properties, "sources": sources}


@contextmanager
def fixture_catalogs(documents=None):
    documents = synthetic_catalogs() if documents is None else documents
    original = read_catalog
    def read(name):
        return copy.deepcopy(documents[name]) if name in documents else original(name)
    with patch("materials_boundaries.catalog.read_catalog", side_effect=read):
        yield documents


def ids(result):
    return [item["id"] for item in result["records"]]


class MaterialQueryTests(unittest.TestCase):
    def test_canonical_envelopes_order_and_detached_results(self):
        with fixture_catalogs() as fixtures:
            for kind, key in (("materials", "materials"), ("reference-properties", "reference_properties")):
                before = copy.deepcopy(fixtures[key])
                result = query_catalog(kind)
                self.assertEqual(result, before)
                result["records"][0]["name"] = "changed caller copy"
                self.assertEqual(query_catalog(kind), before)
                self.assertEqual(fixtures[key], before)

    def test_same_linked_property_satisfies_all_property_filters(self):
        with fixture_catalogs():
            self.assertEqual(ids(query_catalog("materials", quantity="mass_density", source_id="synthetic_paper")), [])
            self.assertEqual(ids(query_catalog("materials", quantity="mass_density", evidence_kind="published_experimental_reference")), [])
            self.assertEqual(ids(query_catalog("materials", quantity="tensile_modulus", source_id="synthetic_paper",
                                             evidence_kind="published_experimental_reference")), ["state_synthetic_alpha"])
            self.assertEqual(ids(query_catalog("materials", quantity="tensile_modulus", source_id="synthetic_paper",
                                             evidence_kind="manufacturer_reference")), [])

    def test_supported_exact_filters_and_empty_results(self):
        with fixture_catalogs():
            self.assertEqual(ids(query_catalog("materials", identity_id="mat_synthetic_alpha", grade_id="grade_synthetic_alpha",
                                             category="metal")), ["state_synthetic_alpha"])
            self.assertEqual(ids(query_catalog("reference-properties", material_id="state_synthetic_alpha", source_id="synthetic_paper",
                                             quantity="tensile_modulus", evidence_kind="published_experimental_reference",
                                             reporting_basis="reported_summary")), ["refprop_synthetic_modulus"])
            for filters in ({"identity_id": "MAT_SYNTHETIC_ALPHA"}, {"grade_id": "missing"}):
                self.assertEqual(ids(query_catalog("materials", **filters)), [])
            empty = query_catalog("materials", record_id="state_synthetic_alpha", category="polymer")
            self.assertEqual(empty, {"schema_version": "1.0.0", "identities": [], "grades": [], "records": []})
            with self.assertRaises(CatalogLookupError):
                query_catalog("materials", record_id="STATE_SYNTHETIC_ALPHA")
            with self.assertRaises(CatalogLookupError):
                query_catalog("reference-properties", record_id="missing", query="nothing")

    def test_literal_all_term_four_language_search(self):
        with fixture_catalogs():
            for term in ("SYNTH-ALIAS", "合成测试甲", "合成試験甲", "STRASSE", "SYNTH-GRADE-001", "TEST-GRADE-ALIAS"):
                for kind in ("materials", "reference-properties"):
                    self.assertTrue(query_catalog(kind, query=term)["records"], (kind, term))
            self.assertEqual(ids(query_catalog("materials", query="STRASSE density")), ["state_synthetic_alpha"])
            for term in (".*", '"Alpha"', "Alhpa", "no production coverage", "original source title", "aluminium"):
                self.assertEqual(ids(query_catalog("materials", query=term)), [], term)
            self.assertEqual(ids(query_catalog("reference-properties", query="STRASSE tensile")), ["refprop_synthetic_modulus"])

    def test_closed_filter_surface_and_types(self):
        invalid = [("materials", {"material_id": "x"}), ("materials", {"reporting_basis": "typical"}),
                   ("reference-properties", {"identity_id": "x"}), ("reference-properties", {"category": "metal"}),
                   ("reference-properties", {"grade_id": "x"}), ("materials", {"category": "Metal"}),
                   ("reference-properties", {"quantity": "specific_gravity"}),
                   ("materials", {"quantity": "Mass_density"}),
                   ("reference-properties", {"reporting_basis": "Typical"}),
                   ("materials", {"evidence_kind": "measured"})]
        for kind in ("materials", "reference-properties"):
            invalid.extend((kind, filters) for filters in ({"direction": "lower"}, {"observation_type": "x"},
                {"claim_type": "theoretical_bound"}, {"role": "x"}, {"year": 2026}, {"license": "x"},
                {"evidence_kind": " "}, {"quantity": 0}, {"query": False}))
        for kind in ("claims", "sources", "observations", "predictions"):
            invalid.extend((kind, {key: "x"}) for key in ("material_id", "identity_id", "grade_id", "category", "evidence_kind", "reporting_basis"))
        for kind, filters in invalid:
            with self.subTest(kind=kind, filters=filters), self.assertRaises(ValueError):
                query_catalog(kind, **filters)

    def test_full_graph_validated_before_excluding_invalid_property(self):
        fixtures = synthetic_catalogs()
        fixtures["reference_properties"]["records"][1]["engineering_allowable"] = True
        with fixture_catalogs(fixtures):
            for kind, filters in (("materials", {"category": "polymer"}),
                                  ("reference-properties", {"record_id": "refprop_synthetic_density"})):
                with self.assertRaises(ValueError):
                    query_catalog(kind, **filters)


class MaterialPresentationTests(unittest.TestCase):
    def test_material_text_resolves_values_unknowns_citations_and_qualifiers(self):
        with fixture_catalogs() as fixtures:
            result = query_catalog("materials")
            before = copy.deepcopy(result)
            for language in LANGUAGES:
                text = render_catalog(result, "materials", language)
                labels = material_labels(language)
                for value in ("2,700 g/cm³", "3,400.0 N/mm²", "25.0 N/mm²", "at_least", "catalog_only",
                              "SYNTH-GRADE-001", "SYNTHETIC extra condition", "synthetic_paper.pdf",
                              "SYNTHETIC test table A, row 1", "not_reported_in_inspected_source"):
                    self.assertIn(value, text)
                for key in ("caveat", "reference_notice", "statistics_notice", "unknown_notice", "translation_notice"):
                    self.assertIn(labels[key], text)
                self.assertIn(labels["temperature"] + ": " + labels["unknown"], text)
                self.assertNotIn("[missing:", text)
            self.assertEqual(result, before)
            self.assertEqual(fixtures["materials"], before)

    def test_property_text_preserves_interval_and_comparator_strings(self):
        for reported, notice in (({"kind": "comparison", "value_text": ">0,90", "number": "0.90", "operator": ">",
                                  "unit_text": "g/cm³", "unit_code": "g/cm^3"}, "comparison_notice"),
                                 ({"kind": "interval", "value_text": "2,700–2,900", "lower": "2.700", "upper": "2.900",
                                   "endpoint_semantics": "source_reported_not_a_confidence_interval",
                                   "unit_text": "g/cm³", "unit_code": "g/cm^3"}, "range_notice")):
            fixtures = synthetic_catalogs()
            fixtures["reference_properties"]["records"][0]["reported_value"] = reported
            with fixture_catalogs(fixtures):
                subset = query_catalog("reference-properties", record_id="refprop_synthetic_density")
                for language in LANGUAGES:
                    text = render_catalog(subset, "reference-properties", language)
                    self.assertIn(reported["value_text"] + " " + reported["unit_text"], text)
                    self.assertIn(material_labels(language)[notice], text)
                    self.assertNotIn("3,400.0 N/mm²", text)

    def test_invalid_caller_envelopes_cannot_bypass_guards(self):
        with fixture_catalogs():
            mutations = []
            original = query_catalog("reference-properties")
            bad = copy.deepcopy(original); del bad["records"][0]["engineering_allowable"]; mutations.append(bad)
            bad = copy.deepcopy(original); bad["records"][0]["evaluation_support"] = "composite_evaluate"; mutations.append(bad)
            bad = copy.deepcopy(original); bad["records"].append(copy.deepcopy(bad["records"][0])); mutations.append(bad)
            bad = copy.deepcopy(original); bad["caveat"] = "omitted"; mutations.append(bad)
            for bad in mutations:
                with self.assertRaises(ValueError):
                    render_catalog(bad, "reference-properties")
            state = query_catalog("materials"); state["records"][0]["property_ids"] = []
            with self.assertRaises(ValueError):
                render_catalog(state, "materials")

    def test_empty_subset_keeps_notices_and_unknown_language_rejected(self):
        with fixture_catalogs():
            for kind in ("materials", "reference-properties"):
                result = query_catalog(kind, query="never_a_match")
                for language in LANGUAGES:
                    text = render_catalog(result, kind, language)
                    self.assertIn(material_labels(language)["empty"], text)
                    self.assertIn(material_labels(language)["caveat"], text)
                with self.assertRaises(ValueError):
                    render_catalog(result, kind, "fr")

    def test_locale_contract_and_metadata(self):
        locales = read_catalog("material_locales")
        validate_material_locales(locales)
        for mutate in (lambda d: d["languages"]["ja"].pop("caveat"),
                       lambda d: d["languages"]["zh"].update(caveat=" "),
                       lambda d: d["languages"]["de"].update(caveat="[missing:caveat]"),
                       lambda d: d.update(translation_review="scientifically_reviewed"),
                       lambda d: d["languages"].update(fr=d["languages"]["en"]),
                       lambda d: d["languages"]["en"].update(extra="unexpected")):
            bad = copy.deepcopy(locales); mutate(bad)
            with self.assertRaises(ValueError):
                validate_material_locales(bad)

    def test_source_terminal_controls_are_escaped_without_changing_json(self):
        fixtures = synthetic_catalogs()
        source = fixtures["sources"]["records"][0]
        source["title"] = "Source title \x1b]52;c;clipboard\x07 and \x1b[2J"
        source["read_status"] = "Scope \x9b31m\x9d52;c;payload\x9c"
        source["license"]["status"] = "Rights \x1b[0m\r\nforged line\t\x7f"
        before = copy.deepcopy(fixtures)
        with fixture_catalogs(fixtures):
            for kind in ("materials", "reference-properties"):
                catalog = query_catalog(kind)
                for language in LANGUAGES:
                    text = render_catalog(catalog, kind, language)
                    self.assertFalse(any(ord(char) < 32 or 127 <= ord(char) <= 159
                                         for char in text if char != "\n"))
                    self.assertIn(r"\u001b]52;c;clipboard\u0007", text)
                    self.assertIn(r"\u001b[2J", text)
                    self.assertIn(r"\u009b31m", text)
                    self.assertIn(r"\u009d52;c;payload\u009c", text)
                self.assertEqual(query_catalog(kind), catalog)
        self.assertEqual(fixtures, before)

    def test_locale_terminal_controls_are_rejected_at_display_boundary(self):
        for control in ("\x1b]52;c;payload\x07", "\x1b[2J", "\x9b31m", "\x9d52;c;payload\x9c", "\n", "\r", "\t", "\x7f"):
            locales = read_catalog("material_locales")
            locales["languages"]["en"]["caveat"] += control
            with self.subTest(control=repr(control)), self.assertRaises(ValueError):
                validate_material_locales(locales)
            with patch("materials_boundaries.catalog._read_reference_resource", return_value=locales), self.assertRaises(ValueError):
                material_labels("en")

    def test_bidi_and_lone_surrogates_escape_without_losing_multilingual_text(self):
        fixtures = synthetic_catalogs()
        controls = "".join(chr(value) for value in (*range(0x202A, 0x202F), *range(0x2066, 0x206A), 0xD800, 0xDFFF))
        safe_text = "English 中文 日本語 Straße 🌡️ 🧪 𠀀"
        fixtures["sources"]["records"][0]["title"] = safe_text + controls
        fixtures["sources"]["records"][0]["license"]["status"] = "Source rights " + controls
        # Bidi source wording remains canonical; the display boundary escapes it.
        fixtures["materials"]["records"][0]["source_scope"] += " \u202econcealed\u202c"
        before = copy.deepcopy(fixtures)
        with fixture_catalogs(fixtures):
            for kind in ("materials", "reference-properties"):
                for language in LANGUAGES:
                    output = render_catalog(query_catalog(kind), kind, language)
                    output.encode("utf-8")
                    self.assertIn(safe_text, output)
                    for char in controls:
                        self.assertNotIn(char, output)
                        self.assertIn(f"\\u{ord(char):04x}", output)
        self.assertEqual(fixtures, before)

    def test_locale_bidi_and_surrogates_rejected_but_astral_text_preserved(self):
        locales = read_catalog("material_locales")
        locales["languages"]["en"]["caveat"] += " 中文 日本語 🌡️ 🧪 𠀀"
        validate_material_locales(locales)
        for value in (*range(0x202A, 0x202F), *range(0x2066, 0x206A), 0xD800, 0xDFFF):
            bad = copy.deepcopy(locales)
            bad["languages"]["en"]["caveat"] += chr(value)
            with self.subTest(value=hex(value)), self.assertRaises(ValueError):
                validate_material_locales(bad)
            with patch("materials_boundaries.catalog._read_reference_resource", return_value=bad), self.assertRaises(ValueError):
                material_labels("en")

    def test_new_resources_reject_duplicate_keys_and_nonfinite_json(self):
        for name in ("materials", "reference_properties", "material_locales"):
            for data in ('{"schema_version":"1.0.0","schema_version":"1.0.0"}', '{"value":NaN}', '{"value":1e999}'):
                resource = Mock()
                resource.joinpath.return_value.read_text.return_value = data
                with patch("materials_boundaries.catalog.files", return_value=resource), self.assertRaises(ValueError):
                    read_catalog(name)


class MaterialCLITests(unittest.TestCase):
    def cli(self, *args):
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            result = main(list(args))
        return result, stdout.getvalue(), stderr.getvalue()

    def test_canonical_json_identical_in_all_languages(self):
        with fixture_catalogs():
            for kind in ("materials", "reference-properties"):
                outputs = []
                for language in LANGUAGES:
                    result, stdout, stderr = self.cli("catalog", kind, "--json", "--lang", language)
                    self.assertEqual(result, 0, stderr)
                    outputs.append(stdout)
                self.assertEqual(len(set(outputs)), 1)
                self.assertEqual(json.loads(outputs[0]), query_catalog(kind))

    def test_text_and_structured_exit_two(self):
        with fixture_catalogs():
            for kind in ("materials", "reference-properties"):
                for language in LANGUAGES:
                    result, stdout, stderr = self.cli("catalog", kind, "--text", "--lang", language)
                    self.assertEqual(result, 0, stderr)
                    self.assertIn(material_labels(language)["caveat"], stdout)
                for arguments, error in ((("--id", "missing"), "catalog_id_not_found"),
                                         (("--direction", "upper"), "invalid_catalog_query")):
                    result, stdout, stderr = self.cli("catalog", kind, *arguments)
                    self.assertEqual(result, 2)
                    self.assertEqual(json.loads(stderr)["error"], error)
                    self.assertEqual(stdout, "")
            result, _, stderr = self.cli("catalog", "claims", "--category", "metal")
            self.assertEqual(result, 2)
            self.assertEqual(json.loads(stderr)["error"], "invalid_catalog_query")

    def test_exact_filter_flags_and_four_language_help(self):
        with fixture_catalogs():
            result, stdout, stderr = self.cli("catalog", "materials", "--identity-id", "mat_synthetic_alpha", "--grade-id", "grade_synthetic_alpha",
                "--category", "metal", "--quantity", "tensile_modulus", "--source-id", "synthetic_paper", "--evidence-kind", "published_experimental_reference")
            self.assertEqual(result, 0, stderr)
            self.assertEqual(ids(json.loads(stdout)), ["state_synthetic_alpha"])
            result, stdout, stderr = self.cli("catalog", "reference-properties", "--material-id", "state_synthetic_alpha", "--reporting-basis", "reported_summary")
            self.assertEqual(result, 0, stderr)
            self.assertEqual(ids(json.loads(stdout)), ["refprop_synthetic_modulus"])
        for language in LANGUAGES:
            stdout = io.StringIO()
            with redirect_stdout(stdout), self.assertRaises(SystemExit) as exited:
                main(["catalog", "--help", "--lang", language])
            self.assertEqual(exited.exception.code, 0)
            text = " ".join(stdout.getvalue().split())
            self.assertIn("reference-properties", text)
            self.assertIn(" ".join(material_labels(language)["cli_category"].split()), text)


if __name__ == "__main__":
    unittest.main()
