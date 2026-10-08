"""Small synthetic-only coverage and rendering QA; no real quota assertions."""
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from copy import deepcopy
from io import StringIO
import json
import os
import unittest
from unittest.mock import patch

from materials_boundaries.catalog import read_catalog
from materials_boundaries.cli import main
from materials_boundaries.material_presentation import LANGUAGES, material_labels, render_material_catalog
from materials_boundaries.material_references import (
    CATEGORIES, material_quota_coverage, resolve_materials, validate_material_catalog,
)
from test_material_derivation_contract import synthetic_derived_catalog
from test_material_reference_contract import synthetic_material_catalog


def five_class_fixture():
    """Five fictional identities, each with a traceable synthetic numeric fact."""
    materials = {"schema_version": "1.0.0", "identities": [], "grades": [], "records": []}
    properties = {"schema_version": "1.0.0", "records": []}
    sources = None
    for category in CATEGORIES:
        m, p, sources = synthetic_material_catalog()
        identity, grade, state, prop = m["identities"][0], m["grades"][0], m["records"][0], p["records"][0]
        identity.update(id="mat_coverage_" + category, category=category,
                        identity_scope="Fictional coverage fixture only: " + category)
        grade.update(id="grade_coverage_" + category, identity_id=identity["id"])
        state.update(id="state_coverage_" + category, identity_id=identity["id"], grade_id=grade["id"])
        prop.update(id="refprop_coverage_" + category, material_state_id=state["id"])
        state["property_ids"] = [prop["id"]]
        for key in ("identities", "grades", "records"):
            materials[key].extend(m[key])
        properties["records"].append(prop)
    return materials, properties, sources


@contextmanager
def fixture_reads(graph):
    documents = dict(zip(("materials", "reference_properties", "sources"), graph))
    def read(name):
        return deepcopy(documents[name]) if name in documents else read_catalog(name)
    with patch("materials_boundaries.catalog.read_catalog", side_effect=read):
        yield


def cli_output(arguments, graph):
    out, err = StringIO(), StringIO()
    with fixture_reads(graph), redirect_stdout(out), redirect_stderr(err):
        try:
            status = main(arguments)
        except SystemExit as exc:
            status = exc.code
    return status, out.getvalue(), err.getvalue()


class MaterialQuotaCoverageTests(unittest.TestCase):
    def test_all_five_classes_and_positive_target_math(self):
        graph = five_class_fixture()
        before = deepcopy(graph)
        result = material_quota_coverage(*graph, target=2)
        self.assertEqual(tuple(result["classes"]), CATEGORIES)
        self.assertEqual(result["distinct_material_count"], 5)
        self.assertEqual(result["target_per_class"], 2)
        for values in result["classes"].values():
            self.assertEqual(values, {"admitted_unique_identity_count": 1, "remaining": 1, "target_met": False})
        self.assertTrue(all(row["target_met"] for row in material_quota_coverage(*graph, target=1)["classes"].values()))
        self.assertEqual(graph, before)

    def test_remaining_is_clamped_after_exceeding_a_target(self):
        graph = five_class_fixture()
        for identity in graph[0]["identities"]:
            identity["category"] = "metal"
        row = material_quota_coverage(*graph, target=1)["classes"]["metal"]
        self.assertEqual(row, {"admitted_unique_identity_count": 5, "remaining": 0, "target_met": True})

    def test_absent_classes_remain_visible(self):
        result = material_quota_coverage(*synthetic_material_catalog())
        self.assertEqual(result["distinct_material_count"], 1)
        self.assertEqual(result["target_per_class"], 1000)
        for category in CATEGORIES:
            expected = int(category == "metal")
            self.assertEqual(result["classes"][category], {"admitted_unique_identity_count": expected,
                             "remaining": 1000 - expected, "target_met": False})

    def test_zero_negative_boolean_and_noninteger_targets_are_rejected(self):
        for target in (0, -1, -1000, False, True, 1.0, "1000", None):
            with self.subTest(target=target):
                with self.assertRaisesRegex(ValueError, "positive integer"):
                    material_quota_coverage(*synthetic_material_catalog(), target=target)

    def test_aliases_grades_states_and_property_rows_do_not_add_identities(self):
        graph = synthetic_material_catalog()
        m, p, _ = graph
        before = material_quota_coverage(*graph)
        m["identities"][0]["aliases"].extend(
            {"language": lang, "text": "Fictional alias " + lang} for lang in LANGUAGES)
        grade, state, prop = deepcopy(m["grades"][0]), deepcopy(m["records"][0]), deepcopy(p["records"][0])
        grade.update(id="grade_coverage_second", designation="SYN-SECOND")
        state.update(id="state_coverage_second", grade_id=grade["id"],
                     source_scope="Distinct fictional second test condition", source_designation="SYN-SECOND")
        state["aliases"] = [{"language": "und", "text": "Another fictional state alias"}]
        prop.update(id="refprop_coverage_second", material_state_id=state["id"])
        state["property_ids"] = [prop["id"]]
        m["grades"].append(grade)
        m["records"].append(state)
        p["records"].append(prop)
        self.assertEqual(material_quota_coverage(*graph), before)

    def test_canonical_duplicates_cannot_hide_behind_new_ids_and_labels(self):
        m, p, s = synthetic_derived_catalog()
        clone = deepcopy(m["identities"][0])
        clone.update(id="mat_coverage_duplicate", name="Different fictional display name",
                     identity_scope="Different fictional presentation scope")
        clone["aliases"] = [{"language": "und", "text": "Fictional alternative alias"}]
        m["identities"].append(clone)
        with self.assertRaisesRegex(ValueError, "duplicate canonical"):
            material_quota_coverage(m, p, s)

    def test_coverage_revalidates_actual_sources_numeric_facts_and_links(self):
        changes = (
            lambda m, p, s: s["records"].clear(),
            lambda m, p, s: p["records"][0]["reported_value"].update(number="NaN"),
            lambda m, p, s: p["records"][0]["evidence"][0].update(url="https://example.invalid/unregistered"),
            lambda m, p, s: m["records"][0]["property_ids"].clear(),
        )
        for index, change in enumerate(changes):
            with self.subTest(case=index):
                graph = synthetic_material_catalog()
                material_quota_coverage(*graph)
                change(*graph)
                with self.assertRaises(ValueError):
                    material_quota_coverage(*graph)

    def test_operation_validates_once_without_a_cross_call_cache(self):
        graph = five_class_fixture()
        with patch("materials_boundaries.material_references.validate_material_catalog",
                   wraps=validate_material_catalog) as validate:
            material_quota_coverage(*graph)
            self.assertEqual(validate.call_count, 1)
            material_quota_coverage(*graph)
            self.assertEqual(validate.call_count, 2)


class MaterialCoverageCLITests(unittest.TestCase):
    def test_json_bytes_are_language_independent_and_match_api(self):
        graph = five_class_fixture()
        before = deepcopy(graph)
        outputs = []
        for language in LANGUAGES:
            for prefix in ([], ["--lang", language]):
                with self.subTest(language=language, prefix=prefix):
                    args = prefix + ["coverage", "--json", "--target", "2"]
                    if not prefix:
                        args += ["--lang", language]
                    status, output, error = cli_output(args, graph)
                    self.assertEqual((status, error), (0, ""))
                    self.assertEqual(json.loads(output), material_quota_coverage(*graph, target=2))
                    outputs.append(output)
        self.assertEqual(len(set(outputs)), 1)
        self.assertEqual(graph, before)

    def test_all_four_text_languages_have_same_counts_and_localized_labels(self):
        graph = five_class_fixture()
        outputs = []
        for language in LANGUAGES:
            with self.subTest(language=language):
                status, output, error = cli_output(["coverage", "--text", "--lang", language, "--target", "2"], graph)
                self.assertEqual((status, error), (0, ""))
                labels = material_labels(language)
                self.assertIn(labels["coverage_notice"], output)
                self.assertIn(labels["coverage_target"] + ": 2", output)
                for category in CATEGORIES:
                    self.assertIn(f'{labels["code_" + category]} [{category}]: '
                                  f'{labels["coverage_admitted"]} 1; {labels["coverage_remaining"]} 1', output)
                self.assertNotIn("[missing:", output)
                outputs.append(output)
        self.assertEqual(len(set(outputs)), len(LANGUAGES))

    def test_cli_rejects_invalid_target_and_conflicting_modes(self):
        for target in ("0", "-1", "True", "1.5"):
            status, output, error = cli_output(["coverage", "--target", target], synthetic_material_catalog())
            self.assertEqual(status, 2, (target, output, error))
            self.assertEqual(output, "")
            self.assertTrue(error)
        status, output, error = cli_output(["coverage", "--text", "--json"], synthetic_material_catalog())
        self.assertEqual((status, output), (2, ""))
        self.assertTrue(error)

    def test_invalid_actual_graph_is_not_reported_as_coverage(self):
        graph = synthetic_material_catalog()
        graph[2]["records"].clear()
        status, output, error = cli_output(["coverage", "--json"], graph)
        self.assertEqual((status, output), (2, ""))
        self.assertEqual(json.loads(error)["error"], "invalid_coverage_request")

    def test_material_catalog_json_unchanged_by_text_rendering_or_language(self):
        graph = synthetic_derived_catalog()
        before = deepcopy(graph)
        for kind, index in (("materials", 0), ("reference-properties", 1)):
            outputs = []
            for language in LANGUAGES:
                with self.subTest(kind=kind, language=language):
                    status, output, error = cli_output(["catalog", kind, "--json", "--lang", language], graph)
                    self.assertEqual((status, error), (0, ""))
                    self.assertEqual(json.loads(output), graph[index])
                    outputs.append(output)
                    with fixture_reads(graph):
                        text = render_material_catalog(graph[index], kind, language)
                    self.assertIn(material_labels(language)["derived_notice"], text)
                    self.assertNotIn("[missing:", text)
            self.assertEqual(len(set(outputs)), 1)
        self.assertEqual(graph, before)


class MaterialBatchRuntimeTests(unittest.TestCase):
    def test_resolution_checks_the_complete_graph_once_and_returns_detached_copies(self):
        graph = five_class_fixture()
        ids = [row["id"] for row in graph[0]["records"]]
        with patch("materials_boundaries.material_references.validate_material_catalog",
                   wraps=validate_material_catalog) as validate:
            result = resolve_materials(ids + ids, *graph)
            self.assertEqual(validate.call_count, 1)
        self.assertEqual([row["state"]["id"] for row in result], ids + ids)
        result[0]["identity"]["name"] = "Mutated caller copy"
        self.assertNotEqual(result[0], result[len(ids)])
        graph[1]["records"][-1]["reported_value"]["number"] = "NaN"
        with self.assertRaises(ValueError):
            resolve_materials([ids[0]], *graph)

    def test_render_validations_are_constant_not_per_record(self):
        for factory in (synthetic_material_catalog, five_class_fixture):
            graph = factory()
            for kind, index in (("materials", 0), ("reference-properties", 1)):
                with self.subTest(factory=factory.__name__, kind=kind):
                    with fixture_reads(graph), patch("materials_boundaries.material_references.validate_material_catalog",
                            wraps=validate_material_catalog) as validate:
                        render_material_catalog(graph[index], kind)
                    self.assertEqual(validate.call_count, 2)

    def test_render_rechecks_mutation_after_a_successful_call(self):
        graph = synthetic_derived_catalog()
        with fixture_reads(graph):
            render_material_catalog(graph[0], "materials")
            graph[1]["records"][0]["derivation"]["si_output"]["number"] = "381"
            with self.assertRaises(ValueError):
                render_material_catalog(graph[0], "materials")


@unittest.skipUnless(os.name == "posix", "RSS benchmark uses the POSIX resource module")
class RuntimeBenchmarkFixtureTests(unittest.TestCase):
    def test_fictional_scaling_is_valid_deterministic_detached_and_clearly_labeled(self):
        from scripts.benchmark_material_runtime import synthetic_graph
        template = synthetic_derived_catalog()
        before = deepcopy(template)
        first = synthetic_graph(template, 3)
        self.assertEqual(first, synthetic_graph(template, 3))
        validate_material_catalog(*first)
        self.assertEqual(template, before)
        self.assertEqual(tuple(len(first[0][key]) for key in ("identities", "grades", "records")), (3, 0, 3))
        self.assertEqual(len(first[1]["records"]), 3)
        for identity in first[0]["identities"]:
            self.assertIn("benchmark_only", identity["id"])
            self.assertIn("BENCHMARK ONLY", identity["identity_scope"])
            self.assertTrue(identity["canonical_taxon"]["accepted_taxon_id"].startswith("wfo-99"))
            self.assertIn("example.invalid/benchmark-only", identity["canonical_taxon"]["source_taxonomic_reference"])
        for prop in first[1]["records"]:
            self.assertIn("BENCHMARK ONLY", prop["derivation"]["provenance"]["attribution"])
            self.assertIn("BENCHMARK ONLY", prop["derivation"]["provenance"]["original_citation"])
            source_ids = {source["id"] for source in first[2]["records"]}
            for key in ("coefficient_source_id", "calibration_source_id", "basis_convention_source_id"):
                dependency = prop["derivation"]["formula"][key]
                self.assertIn(dependency, source_ids)
                self.assertTrue(dependency.startswith("benchmark_only_source_"))
                self.assertTrue(any(item["source_id"] == dependency and "method" in item["supports"]
                                    for item in prop["derivation"]["evidence"]))
        for source in first[2]["records"]:
            self.assertEqual(source["license"]["identifier"], "benchmark-only")
            self.assertTrue(all("example.invalid/benchmark-only" in url for url in source["urls"]))

    def test_fictional_fixture_limits_reject_invalid_sizes(self):
        from scripts.benchmark_material_runtime import synthetic_graph
        for count in (0, -1, True, 100001, 1.5):
            with self.subTest(count=count), self.assertRaises(ValueError):
                synthetic_graph(synthetic_derived_catalog(), count)


if __name__ == "__main__":
    unittest.main()
