"""Read-only search, traceability output, and multilingual CLI contracts."""
import copy
import io
import json
import subprocess
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import patch

from materials_boundaries.catalog import CatalogLookupError, query_catalog, read_catalog
from materials_boundaries.catalog_output import render_catalog
from materials_boundaries.cli import main
from materials_boundaries.i18n import LANGUAGES, translate
from catalog_fixtures import historical_records, isolated_catalogs
from test_engine import ROOT


def ids(result):
    return [record["id"] for record in result["records"]]


class CatalogSearchTests(unittest.TestCase):
    def test_unfiltered_query_preserves_canonical_envelope_and_order(self):
        for kind in ("claims", "sources"):
            self.assertEqual(query_catalog(kind=kind), read_catalog(kind))
            self.assertEqual(set(query_catalog(kind)), {"schema_version", "records"})

    def test_exact_id_and_unknown_id(self):
        with isolated_catalogs():
            for kind, record_id in (("claims", "reuss_bulk"), ("sources", "genin_birman_2009")):
                self.assertEqual(ids(query_catalog(kind, record_id=record_id)), [record_id])
                for unknown in ("not_present", record_id.upper(), record_id + " "):
                    with self.subTest(kind=kind, unknown=unknown), self.assertRaises(CatalogLookupError):
                        query_catalog(kind, record_id=unknown)
            with self.assertRaises(CatalogLookupError):
                query_catalog("claims", record_id="genin_birman_2009")

    def test_query_terms_casefold_and_across_fields(self):
        with isolated_catalogs():
            self.assertEqual(ids(query_catalog("sources", query="MILTON rigorous 10.1016")), ["kochmann_milton_2014"])
            self.assertEqual(ids(query_catalog("sources", query="Victor particulate")), ["genin_birman_2009"])
            self.assertEqual(ids(query_catalog("claims", query="bulk KOCHMANN upper")), ["voigt_bulk"])
            # Unicode casefold, not ASCII-only lowercasing.
            fake = {"schema_version": "1.0.0", "records": [historical_records("sources", ["hashin_shtrikman_1963"])[0]]}
            fake["records"][0]["title"] = "Straße"
            with patch("materials_boundaries.catalog.read_catalog", return_value=fake):
                self.assertEqual(len(query_catalog("sources", query="STRASSE")["records"]), 1)

    def test_literal_terms_are_not_regex_fuzzy_or_translated(self):
        with isolated_catalogs():
            for query in (".*", "Rigrous", "体积模量", "1999999", "\"Rigorous\""):
                with self.subTest(query=query):
                    self.assertEqual(ids(query_catalog("sources", query=query)), [])
            self.assertEqual(ids(query_catalog("sources", query="10.1016/0022-5096(63)90060-7")), ["hashin_shtrikman_1963"])

    def test_query_scope_excludes_notes_formulas_and_joined_titles(self):
        with isolated_catalogs():
            self.assertEqual(ids(query_catalog("sources", query="nonexclusive")), [])
            self.assertEqual(ids(query_catalog("claims", query="negative-stiffness")), [])
            self.assertEqual(ids(query_catalog("claims", query="f1*K1+f2*K2")), [])
            self.assertEqual(ids(query_catalog("sources", query="CC-BY-4.0")), [])

    def test_blank_query_is_no_constraint(self):
        for query in (None, "", " \n\t "):
            self.assertEqual(query_catalog("sources", query=query), read_catalog("sources"))

    def test_claim_filters(self):
        with isolated_catalogs():
            self.assertEqual(ids(query_catalog("claims", direction="interval", source_id="kochmann_milton_2014")), ["hs_bulk_3d_two_phase", "hs_shear_3d_two_phase", "youngs_modulus_outer", "poissons_ratio_outer", "hs_porous_bulk_3d_solid_void", "hs_porous_shear_3d_solid_void"])
            self.assertEqual(ids(query_catalog("claims", source_id="hashin_shtrikman_1963")), ["hs_bulk_3d_two_phase", "hs_shear_3d_two_phase", "hs_porous_bulk_3d_solid_void", "hs_porous_shear_3d_solid_void"])
            self.assertEqual(ids(query_catalog("claims", direction="lower")), ["reuss_bulk", "reuss_shear"])
            self.assertEqual(ids(query_catalog("claims", direction="upper")), ["voigt_bulk", "voigt_shear"])
            self.assertEqual(ids(query_catalog("claims", source_id="KOCHMANN_MILTON_2014")), [])

    def test_source_filters(self):
        with isolated_catalogs():
            self.assertEqual(ids(query_catalog("sources", year=2018)), ["milton_2018_comment", "berger_2018_reply"])
            self.assertEqual(ids(query_catalog("sources", role="changed_assumption_comparison", year=2024, license="CC-BY-4.0")), ["singh_lai_2024"])
            self.assertEqual(ids(query_catalog("sources", license="no_explicit_reuse_license_verified")),
                             ["hashin_shtrikman_1963", "berger_2017", "milton_2018_comment", "berger_2018_reply", "griffith_1921"])
            self.assertEqual(ids(query_catalog("sources", license="cc-by-4.0")), [])
            self.assertEqual(ids(query_catalog("sources", role="missing_role")), [])
            self.assertEqual(ids(query_catalog("sources", year=0)), [])

    def test_filters_combine_with_id_and_query_using_and(self):
        with isolated_catalogs():
            self.assertEqual(ids(query_catalog("sources", query="Berger", year=2018)), ["berger_2018_reply"])
            self.assertEqual(ids(query_catalog("sources", record_id="berger_2017", year=2018)), [])
            self.assertEqual(ids(query_catalog("claims", query="Reuss", direction="upper")), [])
            with self.assertRaises(CatalogLookupError):
                query_catalog("sources", record_id="missing", query="missing")

    def test_bad_kind_filter_types_and_inapplicable_filters(self):
        invalid = [
            ("locales", {}), ("other", {}), ([], {}), ({}, {}), (set(), {}), (None, {}),
            ("claims", {"year": 2014}), ("claims", {"role": "x"}), ("claims", {"license": "x"}),
            ("sources", {"direction": "upper"}), ("sources", {"source_id": "x"}),
            ("claims", {"direction": "sideways"}), ("claims", {"record_id": ""}),
            ("claims", {"record_id": 1}), ("claims", {"source_id": "  "}),
            ("claims", {"query": 1}), ("sources", {"year": True}),
            ("sources", {"year": "2014"}), ("sources", {"year": 2014.0}),
            ("sources", {"role": []}), ("sources", {"license": ""}),
        ]
        for kind, filters in invalid:
            with self.subTest(kind=kind, filters=filters), self.assertRaises(ValueError):
                query_catalog(kind, **filters)

    def test_results_and_human_render_do_not_change_packaged_records(self):
        for kind in ("claims", "sources"):
            before = read_catalog(kind)
            result = query_catalog(kind)
            for lang in LANGUAGES:
                render_catalog(result, kind, lang)
            self.assertEqual(result, before)
            result["records"][0]["id"] = "client_changed_copy"
            self.assertEqual(read_catalog(kind), before)
            self.assertEqual(query_catalog(kind), before)


class CatalogPresentationTests(unittest.TestCase):
    def test_source_metadata_labels_and_original_titles_in_four_languages(self):
        result = query_catalog("sources")
        for lang in LANGUAGES:
            text = render_catalog(result, "sources", lang)
            for label in ("catalog_sources", "catalog_original_title", "catalog_read_status",
                          "catalog_license_status", "catalog_evidence_notice", "catalog_original_notice"):
                self.assertIn(translate(label, lang), text)
            for record in result["records"]:
                self.assertIn(record["title"], text)
                self.assertIn(record["id"], text)
                self.assertIn(record["read_status"], text)
                self.assertIn(record["license"]["status"], text)
                if record["doi"]:
                    self.assertIn(record["doi"], text)
            self.assertNotIn("[missing:", text)

    def test_claim_evidence_distinctions_are_visible(self):
        result = query_catalog("claims", record_id="hs_bulk_3d_two_phase")
        for lang in LANGUAGES:
            text = render_catalog(result, "claims", lang)
            for key in ("catalog_status_software_tested_not_peer_reviewed", "catalog_status_equation_cross_checked",
                        "catalog_status_original_equation_not_inspected", "catalog_status_publisher_abstract_only"):
                self.assertIn(translate(key, lang), text)
            for value in ("hashin_shtrikman_1963", "kochmann_milton_2014", "10.1016/0022-5096(63)90060-7",
                          "original_equation_not_inspected", "constituent_symmetry", "well_ordered_phases"):
                self.assertIn(value, text)
            self.assertIn(translate("catalog_independent_review", lang) + ": " + translate("catalog_no", lang), text)
            self.assertIn(result["records"][0]["formula_display"], text)
            self.assertNotIn("[missing:", text)

    def test_unknown_values_are_not_zero_or_verified(self):
        source = query_catalog("sources", record_id="materials_project_elasticity")
        text = render_catalog(source, "sources", "en")
        self.assertIn("Publication year: Unknown", text)
        self.assertIn("DOI: Unknown", text)
        self.assertIn("License identifier: Unknown", text)
        claim = render_catalog(query_catalog("claims", record_id="hs_bulk_3d_two_phase"), "claims", "en")
        self.assertIn("Passage/equation locator (original): Unknown", claim)

    def test_empty_results_and_fallback(self):
        with isolated_catalogs():
            empty = query_catalog("claims", query="no_such_term")
        for lang in LANGUAGES:
            self.assertIn(translate("catalog_empty", lang), render_catalog(empty, "claims", lang))
        fake = copy.deepcopy(read_catalog("locales"))
        del fake["languages"]["ja"]["catalog_empty"]
        del fake["languages"]["ja"]["catalog_count"]
        del fake["languages"]["en"]["catalog_count"]
        with patch("materials_boundaries.i18n.read_catalog", return_value=fake):
            text = render_catalog(empty, "claims", "ja")
        self.assertIn("No matching records.", text)
        self.assertIn("[missing:catalog_count]", text)

    def test_future_untranslated_status_keeps_canonical_value(self):
        result = query_catalog("sources", record_id="hashin_shtrikman_1963")
        result["records"][0]["read_status"] = "new_untranslated_status"
        self.assertIn("Reading scope: new_untranslated_status", render_catalog(result, "sources"))


class CatalogSearchCLITests(unittest.TestCase):
    def run_cli(self, *args, isolated=False):
        if isolated:
            stdout, stderr = io.StringIO(), io.StringIO()
            with isolated_catalogs(), redirect_stdout(stdout), redirect_stderr(stderr):
                code = main(list(args))
            return subprocess.CompletedProcess(args, code, stdout.getvalue(), stderr.getvalue())
        return subprocess.run([sys.executable, "-m", "materials_boundaries", *args],
                              cwd=ROOT, text=True, capture_output=True)

    def test_default_and_explicit_json_are_unchanged_across_languages(self):
        for kind in ("claims", "sources"):
            original = self.run_cli("catalog", kind).stdout
            self.assertEqual(json.loads(original), read_catalog(kind))
            for lang in LANGUAGES:
                result = self.run_cli("catalog", kind, "--json", "--lang", lang)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout, original)
        outputs = [self.run_cli("catalog", "sources", "--query", "MILTON", "--lang", lang).stdout for lang in LANGUAGES]
        self.assertEqual(len(set(outputs)), 1)

    def test_help_in_four_languages_at_root_and_subcommands(self):
        for lang in LANGUAGES:
            for command in ([], ["catalog"], ["evaluate"], ["validate"]):
                for args in (["--lang", lang, *command, "--help"], [*command, "--help", "--lang", lang]):
                    result = self.run_cli(*args)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertIn(translate("cli_usage", lang), result.stdout)
                    self.assertIn(translate("cli_help", lang), result.stdout)
                    self.assertIn("--lang", result.stdout)
                    self.assertNotIn("[missing:", result.stdout)

    def test_language_position_and_last_occurrence(self):
        for args in (
            ["--lang", "zh", "catalog", "claims", "--text"],
            ["catalog", "--lang", "zh", "claims", "--text"],
            ["catalog", "claims", "--lang=zh", "--text"],
            ["--lang", "de", "catalog", "claims", "--text", "--lang", "zh"],
        ):
            result = self.run_cli(*args)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(translate("catalog_claims", "zh"), result.stdout)
        for command in ("evaluate", "validate"):
            result = self.run_cli("--lang", "ja", command, "examples/synthetic-two-phase.json")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(translate("input_id", "ja"), result.stdout)

    def test_unknown_id_is_distinct_from_successful_empty_query(self):
        unknown = self.run_cli("catalog", "claims", "--id", "not_present", "--lang", "de", isolated=True)
        self.assertEqual(unknown.returncode, 2)
        self.assertEqual(unknown.stdout, "")
        self.assertEqual(json.loads(unknown.stderr)["error"], "catalog_id_not_found")
        empty = self.run_cli("catalog", "claims", "--query", "not_present", isolated=True)
        self.assertEqual(empty.returncode, 0, empty.stderr)
        self.assertEqual(json.loads(empty.stdout), {"schema_version": "1.12.0", "records": []})
        text = self.run_cli("catalog", "claims", "--query", "not_present", "--text", "--lang", "ja", isolated=True)
        self.assertEqual(text.returncode, 0, text.stderr)
        self.assertIn(translate("catalog_empty", "ja"), text.stdout)

    def test_cli_filter_combinations(self):
        result = self.run_cli("catalog", "claims", "--query", "bulk kochmann", "--source-id", "kochmann_milton_2014", "--direction", "interval", isolated=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(ids(json.loads(result.stdout)), ["hs_bulk_3d_two_phase", "hs_porous_bulk_3d_solid_void"])
        result = self.run_cli("catalog", "sources", "--query", "singh", "--year", "2024", "--role", "changed_assumption_comparison", "--license", "CC-BY-4.0", isolated=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(ids(json.loads(result.stdout)), ["singh_lai_2024"])

    def test_invalid_cli_combinations(self):
        for args in (
            ["catalog", "claims", "--year", "2014"],
            ["catalog", "sources", "--source-id", "kochmann_milton_2014"],
            ["catalog", "claims", "--text", "--json"],
            ["catalog", "sources", "--year", "2014.0"],
            ["catalog", "claims", "--direction", "sideways"],
            ["catalog", "claims", "--lang", "fr"],
            ["--lang", "fr", "--help"],
            ["catalog", "sources", "--license", ""],
            ["catalog", "claims", "--id", ""],
        ):
            with self.subTest(args=args):
                result = self.run_cli(*args)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, "")

    def test_direct_main_matches_module_entrypoint(self):
        args = ["--lang", "ja", "catalog", "sources", "--id", "genin_birman_2009", "--text"]
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = main(args)
        module = self.run_cli(*args)
        self.assertEqual(code, module.returncode)
        self.assertEqual(stdout.getvalue(), module.stdout)
        self.assertEqual(stderr.getvalue(), module.stderr)


if __name__ == "__main__":
    unittest.main()
