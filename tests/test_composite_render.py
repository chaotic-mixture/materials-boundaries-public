"""Actual text/HTML rendering across applicability, numerical and trust edges."""
import copy
from decimal import Inexact, localcontext
from fractions import Fraction
from html.parser import HTMLParser
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from materials_boundaries import load_json
from materials_boundaries._composite_labels import LABELS, LANGUAGES, label
from materials_boundaries.catalog import read_catalog
from materials_boundaries.composite import build_composite_report, canonical_json, CompositeReplayError
from materials_boundaries.composite_render import render_composite_report, _render_composite_report
from materials_boundaries.engine import evaluate

ROOT = Path(__file__).resolve().parents[1]


def case():
    result = load_json(ROOT / "examples/synthetic-two-phase.json")
    result["id"] = "original-composite-render-test"
    for phase, fraction, k, g in zip(result["phases"], (.25, .75), (12, 36), (6, 18)):
        phase["volume_fraction"] = fraction
        phase["bulk_modulus"] = {"value": k, "unit": "GPa"}
        phase["shear_modulus"] = {"value": g, "unit": "GPa"}
    return result


class Inspection(HTMLParser):
    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.tags = []
        self.attributes = []
        self.content = []
        self.audit_content = []
        self.detail_depth = 0
        self.hidden = False
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        self.tags.append(tag)
        self.attributes.extend((tag, key, value) for key, value in attrs)
        if tag == "details":
            self.detail_depth += 1
        if tag in ("style", "head"):
            self.hidden = True
        if tag == "body":
            self.hidden = False

    def handle_endtag(self, tag):
        if tag == "details":
            self.detail_depth -= 1

    def handle_data(self, data):
        if not self.hidden:
            if self.detail_depth:
                self.audit_content.append(data)
            else:
                self.content.append(data)

    @property
    def text(self):
        return "\n".join(self.content)


def presentations(bundle, lang):
    return (render_composite_report(bundle, lang=lang),
            Inspection(render_composite_report(bundle, lang=lang, format="html")).text)


class CompositeRenderTests(unittest.TestCase):
    def test_all_language_labels_have_parity_and_explicit_missing_marker(self):
        for lang in LANGUAGES:
            self.assertEqual(set(LABELS[lang]), set(LABELS["en"]))
            self.assertTrue(all(isinstance(value, str) and value for value in LABELS[lang].values()))
            self.assertEqual(label("nonexistent", lang), "[missing:nonexistent]")
            self.assertNotIn("[missing:", label("translation_notice", lang))

    def test_deterministic_across_formats_languages_and_key_order_without_mutation(self):
        bundle = build_composite_report(case())
        before = canonical_json(bundle)
        reordered = json.loads(before)
        for lang in LANGUAGES:
            for format in ("text", "html"):
                with self.subTest(lang=lang, format=format):
                    first = render_composite_report(bundle, lang=lang, format=format)
                    self.assertEqual(first, render_composite_report(bundle, lang=lang, format=format))
                    self.assertEqual(first, render_composite_report(reordered, lang=lang, format=format))
                    self.assertTrue(first.endswith("\n"))
                    self.assertNotIn("[missing:", first)
                    self.assertEqual(first, _render_composite_report(bundle, lang=lang, format=format))
        self.assertEqual(canonical_json(bundle), before)

    def test_eight_rows_separate_states_early_caveats_and_all_round_trip_values(self):
        bundle = build_composite_report(case())
        for lang in LANGUAGES:
            html = render_composite_report(bundle, lang=lang, format="html")
            self.assertEqual(Inspection(html).tags.count("article"), 8)
            for text in presentations(bundle, lang):
                for key in ("structure", "applicability", "availability", "review"):
                    self.assertIn(label(key, lang), text)
                for notice in ("scope_notice", "source_notice", "numerical_notice", "joint_notice"):
                    self.assertLess(text.index(label(notice, lang)), text.index(label("answer", lang)))
                for item in bundle["evaluation"]["evaluations"]:
                    self.assertIn("[" + item["claim_id"] + "]", text)
                    self.assertIn(item["rule_id"], text)
                    self.assertIn(item["applicability"], text)
                    self.assertIn(item["computation"], text)
                    for side in ("lower", "upper"):
                        if side in item["result"]:
                            self.assertIn(side + " ≈ " + repr(item["result"][side]), text)
                self.assertNotIn("validated material", text.lower())
                self.assertIn("software replay only; does not verify the physical sample or prove a theorem", text)

    def test_one_sided_rows_do_not_gain_fictitious_endpoints(self):
        html = render_composite_report(build_composite_report(case()), format="html")
        cards = html.split('<article class="result">')[1:]
        for index in (1, 4):
            card = Inspection(cards[index].split("</article>")[0]).text
            self.assertIn("lower ≈", card)
            self.assertNotIn("upper ≈", card)
        for index in (2, 5):
            card = Inspection(cards[index].split("</article>")[0]).text
            self.assertIn("upper ≈", card)
            self.assertNotIn("lower ≈", card)

    def test_crossed_ordering_preserves_four_reuss_voigt_results(self):
        instance = case()
        instance["phases"][0]["shear_modulus"]["value"] = 18
        instance["phases"][1]["shear_modulus"]["value"] = 6
        bundle = build_composite_report(instance)
        for lang in LANGUAGES:
            html = render_composite_report(bundle, lang=lang, format="html")
            cards = html.split('<article class="result">')[1:]
            self.assertEqual(len(cards), 8)
            for index, card in enumerate(cards):
                visible = Inspection(card.split("</article>")[0]).text
                self.assertIn(label("state_computed" if index in (1, 2, 4, 5) else "state_not_computed", lang) + " (" + ("computed" if index in (1, 2, 4, 5) else "not_computed") + ")", visible)
            for text in presentations(bundle, lang):
                self.assertIn("well_ordered_phases", text)
                self.assertIn(label("condition_well_ordered_phases", lang), text)
                self.assertIn("lower ≈ 7.2", text)
                self.assertIn("upper ≈ 9.0", text)

    def test_unknown_and_violated_both_remain_visible(self):
        instance = case()
        instance["conditions"]["loading"] = "dynamic"
        instance["phases"][1]["shear_modulus"] = None
        bundle = build_composite_report(instance)
        for lang in LANGUAGES:
            for text in presentations(bundle, lang):
                self.assertIn(label("condition_name_loading", lang) + " (loading): " + label("state_violated", lang) + " (violated)", text)
                self.assertIn(label("condition_name_positive_shear_moduli", lang) + " (positive_shear_moduli): " + label("state_unknown", lang) + " (unknown)", text)
                self.assertIn(label("next_unknown", lang), text)
                self.assertIn(label("next_violated", lang), text)
                self.assertIn(label("condition_positive_shear_moduli", lang), text)
                self.assertNotIn("lower ≈", text)

    def test_unknown_effective_isotropy_not_inferred_from_constituents(self):
        instance = case()
        instance["conditions"]["effective_symmetry"] = None
        bundle = build_composite_report(instance)
        for lang in LANGUAGES:
            for text in presentations(bundle, lang):
                self.assertIn(label("condition_name_effective_symmetry", lang) + " (effective_symmetry): " + label("state_unknown", lang) + " (unknown)", text)
                self.assertIn(label("condition_effective_symmetry", lang), text)
                self.assertNotIn("lower ≈", text)

    def test_missing_fraction_tiny_active_phase_and_inactive_phase_are_distinct(self):
        for mode in ("missing", "tiny", "inactive"):
            instance = case()
            instance["phases"][0]["volume_fraction"] = 1
            instance["phases"][1]["volume_fraction"] = {"missing": None, "tiny": 1e-299, "inactive": 0}[mode]
            instance["phases"][1]["bulk_modulus"] = None
            instance["phases"][1]["shear_modulus"] = None
            bundle = build_composite_report(instance)
            for lang in LANGUAGES:
                for text in presentations(bundle, lang):
                    self.assertIn(label("normalization_notice", lang), text)
                    if mode == "inactive":
                        self.assertIn("lower ≈", text)
                        self.assertIn(label("collapsed", lang), text)
                    else:
                        self.assertNotIn("lower ≈", text)
                        self.assertIn("(unknown)", text)
                    if mode == "tiny":
                        self.assertIn("1e-299", text)

    def test_coincident_displayed_endpoints_do_not_claim_exact_model_response(self):
        instance = case()
        instance["phases"][0]["volume_fraction"] = 1
        instance["phases"][1]["volume_fraction"] = 1e-20
        bundle = build_composite_report(instance)
        hs = bundle["evaluation"]["evaluations"][0]
        # Independent exact arithmetic proves nonzero interval width despite
        # the identical serialized floats. The second phase remains active.
        f1 = Fraction(10**20, 10**20 + 1)
        f2 = Fraction(1, 10**20 + 1)
        def exact_bulk(c):
            return (12 * 36 + c * (f1 * 12 + f2 * 36)) / (f1 * 36 + f2 * 12 + c)
        self.assertLess(exact_bulk(8), exact_bulk(24))
        self.assertEqual(float(exact_bulk(8)), float(exact_bulk(24)))
        self.assertEqual(hs["result"]["lower"], hs["result"]["upper"])
        self.assertNotEqual(instance["phases"][0]["bulk_modulus"], instance["phases"][1]["bulk_modulus"])
        self.assertNotEqual(instance["phases"][0]["shear_modulus"], instance["phases"][1]["shear_modulus"])
        self.assertEqual(bundle["input"], instance)
        positive_check = next(check for check in hs["checks"] if check["condition_id"] == "positive_bulk_moduli")
        self.assertEqual(len(positive_check["observed"]), 2)
        self.assertGreater(Fraction(bundle["evaluation"]["fraction_normalization"]["normalized_fractions"][1]), 0)
        self.assertEqual(label("collapsed", "en"), "Displayed endpoints coincide at output precision; no exact physical response is established")
        for lang in LANGUAGES:
            for text in presentations(bundle, lang):
                with self.subTest(lang=lang):
                    self.assertIn(label("collapsed", lang), text)
                    self.assertIn(label("normalization_notice", lang), text)
                    self.assertIn("1e-20", text)
                    for phase in instance["phases"]:
                        self.assertIn(phase["id"], text)
                        self.assertIn("K=" + str(phase["bulk_modulus"]["value"]) + " GPa", text)
                        self.assertIn("G=" + str(phase["shear_modulus"]["value"]) + " GPa", text)
                    self.assertNotIn("Collapsed interval: conditional model limit only", text)

    def test_fraction_normalization_is_disclosed_exactly(self):
        instance = case()
        instance["phases"][0]["volume_fraction"] = .2500000000002
        bundle = build_composite_report(instance)
        normalization = bundle["evaluation"]["fraction_normalization"]
        for lang in LANGUAGES:
            for text in presentations(bundle, lang):
                self.assertIn("0.2500000000002", text)
                self.assertIn(normalization["original_sum"], text)
                self.assertIn("performed=true", text)
                for fraction in normalization["normalized_fractions"]:
                    self.assertIn(fraction, text)
                self.assertIn(label("normalization_notice", lang), text)

    def test_all_languages_keep_negative_zero_and_interior_near_boundary_poisson(self):
        for bulk, shear in ((2, 6), (4, 6), (10**15, 2), (2, 10**15)):
            instance = case()
            for phase in instance["phases"]:
                phase["bulk_modulus"]["value"] = bulk
                phase["shear_modulus"]["value"] = shear
            bundle = build_composite_report(instance)
            result = bundle["evaluation"]["evaluations"][-1]["result"]
            self.assertIsNotNone(result)
            for lang in LANGUAGES:
                for text in presentations(bundle, lang):
                    self.assertIn("lower ≈ " + repr(result["lower"]), text)
                    self.assertIn("upper ≈ " + repr(result["upper"]), text)
                    if bulk == 10**15:
                        self.assertIn("0.499999999999999", text)
                    if shear == 10**15:
                        self.assertLess(result["upper"], -.999999999999)

    def test_boundary_rounding_only_removes_poisson_in_every_language(self):
        for bulk, shear in ((1e90, 2), (2, 1e90)):
            instance = case()
            for phase in instance["phases"]:
                phase["bulk_modulus"]["value"] = bulk
                phase["shear_modulus"]["value"] = shear
            bundle = build_composite_report(instance)
            self.assertEqual(bundle["evaluation"]["evaluations"][-1]["computation"], "numerical_range_error")
            for lang in LANGUAGES:
                cards = render_composite_report(bundle, lang=lang, format="html").split('<article class="result">')[1:]
                for card in cards[:7]:
                    self.assertIn(label("state_computed", lang) + " (computed)", Inspection(card.split("</article>")[0]).text)
                last = Inspection(cards[7].split("</article>")[0]).text
                self.assertIn(label("state_satisfied", lang) + " (satisfied)", last)
                self.assertIn(label("state_numerical_range_error", lang) + " (numerical_range_error)", last)
                self.assertNotIn("lower ≈", last)
                self.assertIn(label("next_numeric", lang), Inspection(render_composite_report(bundle, lang=lang, format="html")).text)

    def test_overflow_underflow_preserve_applicability_and_complete_report(self):
        for value, input_unit, output_unit in ((1e307, "GPa", "Pa"), (1e-323, "Pa", "GPa")):
            instance = case()
            for phase in instance["phases"]:
                for key in ("bulk_modulus", "shear_modulus"):
                    phase[key] = {"value": value, "unit": input_unit}
            bundle = build_composite_report(instance, output_unit)
            for lang in LANGUAGES:
                for text in presentations(bundle, lang):
                    self.assertIn("(satisfied): 8", text)
                    self.assertIn("(numerical_range_error): 8", text)
                    self.assertIn(label("next_numeric", lang), text)
                    self.assertNotIn("lower ≈", text)

    def test_exact_large_integer_difference_survives_all_formats(self):
        instance = case()
        for phase, k, g in zip(instance["phases"], (10**110, 10**110 + 3), (9, 4)):
            phase["bulk_modulus"]["value"] = k
            phase["shear_modulus"]["value"] = g
        bundle = build_composite_report(instance)
        for lang in LANGUAGES:
            for text in presentations(bundle, lang):
                self.assertIn(str(10**110), text)
                self.assertIn(str(10**110 + 3), text)
                self.assertIn(label("condition_name_well_ordered_phases", lang) + " (well_ordered_phases): " + label("state_violated", lang) + " (violated)", text)

    def test_mixed_unit_raw_and_exact_pa_conversion_are_visible(self):
        instance = case()
        instance["phases"][0]["bulk_modulus"] = {"value": 12000, "unit": "MPa"}
        instance["phases"][1]["shear_modulus"] = {"value": 18000000000, "unit": "Pa"}
        bundle = build_composite_report(instance, "MPa")
        for lang in LANGUAGES:
            for text in presentations(bundle, lang):
                self.assertIn("K=12000 MPa", text)
                self.assertIn("1.2000E+10", text)
                self.assertIn("18000000000", text)
                self.assertIn(label("conversion_notice", lang), text)

    def test_literature_model_raw_converted_effective_inputs_and_unknown_context_distinct(self):
        instance = load_json(ROOT / "examples/literature-epoxy-glass-model.json")
        bundle = build_composite_report(instance)
        model = instance["provenance"]["model_evidence"]
        for lang in LANGUAGES:
            for text in presentations(bundle, lang):
                for key in ("raw_parameters", "converted_inputs", "model_distinction", "phase_evidence"):
                    self.assertIn(label(key, lang), text)
                self.assertIn(model["scope_note"], text)
                self.assertIn(model["locator"], text)
                self.assertIn("(source_model)", text)
                self.assertIn("(calculator_assumption)", text)
                self.assertIn("(calculator_choice)", text)
                for key in ("temperature_k", "material_grade", "cure_state", "measurement_uncertainty"):
                    self.assertIn(key + "=null", text)

    def test_complete_claim_gaps_locators_source_notes_and_rights_retained(self):
        bundle = build_composite_report(case())
        for lang in LANGUAGES:
            for text in presentations(bundle, lang):
                for claim in bundle["catalogs"]["claims"]["records"]:
                    for gap in claim["verification"]["gaps"]:
                        self.assertIn(gap, text)
                    for limit in claim["limits"]:
                        self.assertIn(limit, text)
                    for evidence in claim["evidence"]:
                        if evidence["locator"] is not None:
                            self.assertIn(evidence["locator"], text)
                        self.assertIn(evidence["verification_status"], text)
                        self.assertIn(evidence["verified_as"], text)
                for source in bundle["catalogs"]["sources"]["records"]:
                    self.assertIn(source["title"], text)
                    self.assertIn(source["license"]["status"], text)
                self.assertIn("hashin_shtrikman_1963 · K HS / G HS: locator=null", text)
                self.assertIn("independent_scientific_review = false", text)
                self.assertIn(label("rights_notice", lang), text)
                self.assertIn(label("comparison_notice", lang), text)

    def test_same_case_dependency_trace_and_relative_command(self):
        instance = case()
        instance["id"] = "../../hostile-case; touch /tmp/should-not-run"
        bundle = build_composite_report(instance)
        for lang in LANGUAGES:
            for text in presentations(bundle, lang):
                self.assertIn("instance_id=" + instance["id"], text)
                self.assertIn("joint_attainability=not_asserted", text)
                self.assertIn(label("corner_notice", lang), text)
                self.assertIn("E_lower=E(K_HS_lower,G_HS_lower)", text)
                self.assertIn("nu_lower=nu(K_HS_lower,G_HS_upper)", text)
                command = "materials-boundaries composite report input.json --output replay-report --unit GPa --lang " + lang
                self.assertIn(command, text)
                self.assertIn("materials-boundaries composite verify bundle.json --json", text)
                self.assertNotIn("composite report " + instance["id"], text)
                for digest in ("input", "evaluation", "claims", "sources"):
                    self.assertIn(bundle["digests"][digest], text)

    def test_hostile_user_strings_are_text_only_in_all_languages(self):
        hostile = '</pre></p><script>alert("x")</script><img src="https://bad.test/asset" onerror="boom()"> & Unicode 雪 🧪 javascript:alert(1)'
        instance = case()
        instance["id"] = "../" + hostile
        instance["phases"][0]["id"] = hostile
        instance["conditions"]["loading"] = hostile
        instance["provenance"]["note"] = hostile + ("长" * 12000)
        instance["provenance"]["source_ids"] = ["javascript:alert(1)", hostile]
        bundle = build_composite_report(instance)
        for lang in LANGUAGES:
            html = render_composite_report(bundle, lang=lang, format="html")
            parsed = Inspection(html)
            self.assertNotIn("script", parsed.tags)
            self.assertNotIn("img", parsed.tags)
            self.assertNotIn("form", parsed.tags)
            self.assertNotIn("iframe", parsed.tags)
            self.assertNotIn("link", parsed.tags)
            self.assertIn(hostile, parsed.text)
            self.assertIn(instance["provenance"]["note"], parsed.text)
            self.assertIn(label("unresolved", lang), parsed.text)
            self.assertIn("javascript:alert(1)", parsed.text)
            self.assertNotIn(hostile, html)
            self.assertIn("&lt;script&gt;", html)
            for tag, attr, value in parsed.attributes:
                self.assertNotIn(attr, ("href", "src", "srcdoc", "action", "formaction"))
                self.assertFalse(attr.startswith("on"))
                self.assertNotIn("bad.test", value or "")

    def test_hostile_catalog_urls_and_titles_remain_inert_original_text(self):
        def catalog(kind):
            result = copy.deepcopy(read_catalog(kind))
            if kind == "sources":
                for source in result["records"]:
                    if source["id"] == "hashin_shtrikman_1963":
                        source["urls"] = ["javascript:alert(1)", 'https://bad.test/" onmouseover="bad()']
                        source["title"] = '<svg onload="bad()"> original title'
            return result
        with patch("materials_boundaries.composite.read_catalog", side_effect=catalog):
            bundle = build_composite_report(case())
            for lang in LANGUAGES:
                parsed = Inspection(render_composite_report(bundle, lang=lang, format="html"))
                self.assertNotIn("svg", parsed.tags)
                self.assertIn("javascript:alert(1)", "".join(parsed.audit_content))
                self.assertIn('<svg onload="bad()"> original title', parsed.text)
                self.assertFalse(any(key in ("href", "src") or key.startswith("on") for _, key, _ in parsed.attributes))

    def test_html_accessible_static_wrapping_document(self):
        for lang in LANGUAGES:
            html = render_composite_report(build_composite_report(case()), lang=lang, format="html")
            parsed = Inspection(html)
            self.assertIn(("html", "lang", lang), parsed.attributes)
            self.assertEqual(parsed.tags.count("h1"), 1)
            self.assertEqual(parsed.tags.count("main"), 1)
            self.assertEqual(parsed.tags.count("details"), 1)
            self.assertFalse(any(tag == "details" and key == "open" for tag, key, value in parsed.attributes))
            self.assertIn(label("full_records", lang), "".join(parsed.audit_content))
            self.assertNotIn("table", parsed.tags)  # Rows wrap without horizontal table scrolling.
            self.assertIn("width=device-width", html)
            self.assertIn("overflow-wrap:anywhere", html)
            self.assertIn("white-space:pre-wrap", html)
            self.assertIn("@media(max-width:35rem)", html)
            self.assertIn("default-src 'none'", html)
            self.assertNotIn("@import", html)
            self.assertNotIn("url(", html)
            self.assertTrue(set(parsed.tags) <= {"html", "head", "meta", "title", "style", "body", "main", "h1", "h2", "h3", "h4", "p", "pre", "article", "details", "summary"})

    def test_public_renderer_fails_closed_before_showing_tampered_values(self):
        for change in ("endpoint", "policy", "review", "dependency", "source", "instance_id", "engine_version"):
            bundle = build_composite_report(case())
            if change == "endpoint":
                bundle["evaluation"]["evaluations"][0]["result"]["lower"] = 999
            elif change == "policy":
                bundle["policy"]["joint_attainability"] = "asserted"
            elif change == "review":
                bundle["catalogs"]["claims"]["records"][0]["verification"]["independent_scientific_review"] = True
            elif change == "dependency":
                bundle["evaluation"]["evaluations"][-1]["dependencies"]["instance_id"] = "different"
            elif change == "source":
                bundle["catalogs"]["sources"]["records"][0]["title"] = "fabricated"
            else:
                bundle[change] = "different"
            for format in ("text", "html"):
                with self.subTest(change=change, format=format), self.assertRaises(CompositeReplayError):
                    render_composite_report(bundle, format=format)

    def test_public_validation_replays_once_internal_export_does_not(self):
        bundle = build_composite_report(case())
        with patch("materials_boundaries.composite.evaluate", wraps=evaluate) as called:
            render_composite_report(bundle)
            self.assertEqual(called.call_count, 1)
            _render_composite_report(bundle, format="html")
            self.assertEqual(called.call_count, 1)

    def test_invalid_presentation_options_rejected(self):
        bundle = build_composite_report(case())
        for lang in ("fr", "EN", "", None, ["en"]):
            with self.subTest(lang=lang), self.assertRaises(ValueError):
                render_composite_report(bundle, lang=lang)
        for format in ("csv", "HTML", "", None, ["html"]):
            with self.subTest(format=format), self.assertRaises(ValueError):
                render_composite_report(bundle, format=format)

    def test_original_demo_is_concise_in_all_languages_with_inputs_before_outputs(self):
        instance = load_json(ROOT / "tests/fixtures/composite-acceptance.json")["input"]
        bundle = build_composite_report(instance)
        before = canonical_json(bundle).encode("utf-8")
        for lang in LANGUAGES:
            text, visible = presentations(bundle, lang)
            self.assertLessEqual(len(text.splitlines()), 180)
            self.assertLessEqual(len(text), 18000)
            self.assertNotIn("required_assumptions", text)
            self.assertNotIn("verification.gaps", text)
            self.assertNotIn("\npolicy.", text)
            for output in (text, visible):
                self.assertLess(output.index(label("phase_inputs", lang)), output.index(label("answer", lang)))
                for phase in instance["phases"]:
                    self.assertLess(output.index(phase["id"]), output.index(label("answer", lang)))
                gaps = {gap for claim in bundle["catalogs"]["claims"]["records"] for gap in claim["verification"]["gaps"]}
                for gap in gaps:
                    self.assertEqual(output.count(gap), 1)
        self.assertEqual(canonical_json(bundle).encode("utf-8"), before)

    def test_concise_unknown_crossed_and_model_cases_keep_actionable_evidence(self):
        unknown = case()
        unknown["conditions"]["effective_symmetry"] = None
        crossed = case()
        crossed["phases"][0]["shear_modulus"]["value"] = 18
        crossed["phases"][1]["shear_modulus"]["value"] = 6
        model = load_json(ROOT / "examples/literature-epoxy-glass-model.json")
        for name, instance in (("unknown", unknown), ("crossed", crossed), ("model", model)):
            bundle = build_composite_report(instance)
            for lang in LANGUAGES:
                text, visible = presentations(bundle, lang)
                with self.subTest(case=name, lang=lang):
                    self.assertLessEqual(len(text.splitlines()), 180)
                    self.assertEqual(visible.count(label("ledger_columns", lang)), 1)
                    if name == "unknown":
                        self.assertIn(label("next_unknown", lang), text)
                        self.assertNotIn("lower ≈", text)
                    elif name == "crossed":
                        self.assertIn(label("next_violated", lang), text)
                        self.assertIn("lower ≈ 7.2", text)
                    else:
                        self.assertLess(text.index(label("raw_parameters", lang)), text.index(label("converted_inputs", lang)))
                        self.assertLess(text.index(label("converted_inputs", lang)), text.index(label("answer", lang)))
                        self.assertIn(instance["provenance"]["model_evidence"]["scope_note"], text)

    def test_ledger_localizes_conditions_values_states_and_bases_without_inventing_values(self):
        instance = case()
        instance["conditions"]["effective_symmetry"] = None
        instance["conditions"]["loading"] = "dynamic"
        instance["conditions"]["interface"] = "User's original <interface> wording 未知"
        bundle = build_composite_report(instance)
        for lang in LANGUAGES:
            for text in presentations(bundle, lang):
                ledger = text.split(label("ledger_columns", lang), 1)[1].split(label("check_explanations", lang), 1)[0]
                for key in instance["conditions"]:
                    self.assertIn(label("condition_name_" + key, lang) + " (" + key + ")", ledger)
                self.assertIn(label("value_isotropic", lang) + " (isotropic)", ledger)
                self.assertIn(label("value_small_strain", lang) + " (small_strain)", ledger)
                self.assertIn(label("value_linear_elastic", lang) + " (linear_elastic)", ledger)
                self.assertIn(label("value_static", lang) + " (static)", ledger)
                self.assertIn(label("value_dynamic", lang) + " (dynamic)", ledger)
                self.assertIn(label("value_perfectly_bonded", lang) + " (perfectly_bonded)", ledger)
                self.assertIn(label("value_null", lang) + " (null)", ledger)
                for key in ("unknown", "violated", "satisfied"):
                    self.assertIn(label("state_" + key, lang) + " (" + key + ")", ledger)
                self.assertIn(label("basis_supplied_assertion", lang) + " (supplied_assertion)", ledger)
                self.assertIn(label("required_volume_fractions_known", lang), ledger)
                self.assertIn(label("required_positive_bulk_moduli", lang), ledger)
                self.assertIn(label("required_compatible_bulk_shear_bounds", lang), ledger)
                self.assertIn(instance["conditions"]["interface"], ledger)
                self.assertNotIn("[missing:", text)

    def test_closed_html_audit_records_are_lossless_essential_evidence_stays_visible(self):
        bundle = build_composite_report(case())
        for lang in LANGUAGES:
            parsed = Inspection(render_composite_report(bundle, lang=lang, format="html"))
            audit = "".join(parsed.audit_content)
            self.assertEqual(json.loads(audit[audit.index("{"):]), bundle)
            self.assertFalse(any(tag == "details" and attr == "open" for tag, attr, value in parsed.attributes))
            for key in ("scope_notice", "source_notice", "numerical_notice", "joint_notice", "rights_notice", "translation_notice", "comparison_notice"):
                self.assertIn(label(key, lang), parsed.text)
            for claim in bundle["catalogs"]["claims"]["records"]:
                for evidence in claim["evidence"]:
                    line = next(line for line in parsed.text.splitlines()
                                if line.startswith(evidence["source_id"] + " · ")
                                and "locator=" + (evidence["locator"] or "null") in line)
                    self.assertIn(evidence["verification_status"], line)
                    self.assertIn(evidence["verified_as"], line)

    def test_long_user_text_is_never_truncated_to_meet_demo_length_target(self):
        instance = case()
        instance["provenance"]["note"] = "Unabridged user evidence line\n" * 200 + "终止 " + "x" * 19000
        bundle = build_composite_report(instance)
        for lang in LANGUAGES:
            for text in presentations(bundle, lang):
                self.assertIn(instance["provenance"]["note"], text)
                self.assertGreater(len(text), 18000)

    def test_render_is_independent_of_decimal_context(self):
        bundle = build_composite_report(case())
        expected = render_composite_report(bundle)
        with localcontext() as context:
            context.prec = 1
            context.Emax = 2
            context.Emin = -2
            context.traps[Inexact] = True
            self.assertEqual(render_composite_report(bundle), expected)


if __name__ == "__main__":
    unittest.main()
