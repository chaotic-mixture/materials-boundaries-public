"""Synthetic contributions exercise existing contracts without changing real data."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from jsonschema import FormatChecker

from materials_boundaries import evaluate, load_json
from materials_boundaries.catalog import query_catalog
from materials_boundaries.catalog_output import render_catalog
from materials_boundaries.visualization import build_comparison, render_html, render_svg
from scripts.validate_catalogs import (CatalogValidationError, CATALOGS, EXPECTED_EXECUTABLE_PAIRS,
                                      load_catalogs, validate_catalogs)
from test_engine import ROOT, example


FIXTURE = ROOT / "tests/fixtures/contributions/lefm.json"


def contribution_catalogs():
    catalogs = load_catalogs(ROOT / "materials_boundaries/data")
    contribution = load_json(FIXTURE)
    # A disposable whole-suite rehearsal may already contain this exact fixture.
    # Do not normalize or overwrite it: require equality and add it only once.
    for kind, field in (("claims", "claim"), ("sources", "source")):
        existing = next((record for record in catalogs[kind]["records"]
                         if record["id"] == contribution[field]["id"]), None)
        if existing is None:
            catalogs[kind]["records"].append(contribution[field])
        elif existing != contribution[field]:
            raise AssertionError("Synthetic rehearsal record differs from its fixture")
        else:
            # Tests mutate their synthetic record, selected last for convenience;
            # this changes only the in-memory test order, not candidate files.
            catalogs[kind]["records"].remove(existing)
            catalogs[kind]["records"].append(existing)
    for language, label in contribution["labels"].items():
        labels = catalogs["locales"]["languages"][language]
        key = "catalog_name_" + contribution["claim"]["id"]
        if key in labels and labels[key] != label:
            raise AssertionError("Synthetic rehearsal label differs from its fixture")
        labels[key] = label
    addition = contribution["evidence_addition"]
    evidence = next(record for record in catalogs["claims"]["records"] if record["id"] == addition["claim_id"])["evidence"]
    if addition["evidence"] not in evidence:
        evidence.append(addition["evidence"])
    return catalogs


class ContributionWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.catalogs = contribution_catalogs()

    def test_real_catalogs_pass_without_changes(self):
        catalogs = load_catalogs(ROOT / "materials_boundaries/data")
        before = copy.deepcopy(catalogs)
        counts = validate_catalogs(catalogs)
        self.assertEqual(counts, {name: len(catalogs[name]["records"]) for name in CATALOGS})
        self.assertEqual(catalogs, before)

    def test_supported_family_new_id_source_labels_and_extra_evidence_pass(self):
        before = copy.deepcopy(self.catalogs)
        validate_catalogs(self.catalogs)
        self.assertEqual(self.catalogs, before)
        source = self.catalogs["sources"]["records"][-1]
        self.assertIsNone(source["license"]["identifier"])
        self.assertFalse(self.catalogs["claims"]["records"][-1]["verification"]["independent_scientific_review"])
        self.assertIn("synthetic", source["read_status"])

    def test_source_evidence_enrichment_does_not_require_a_duplicate_claim(self):
        # The preferred real-world path is adding independently checked evidence
        # to a matching existing claim. No new ID/alias is necessary in this path.
        self.catalogs["claims"]["records"].pop()
        for labels in self.catalogs["locales"]["languages"].values():
            del labels["catalog_name_synthetic_contribution_lefm"]
        validate_catalogs(self.catalogs)

    def test_other_supported_stability_family_remains_appendable(self):
        record = copy.deepcopy(next(r for r in self.catalogs["claims"]["records"] if r["id"] == "cubic_born_stability"))
        record["id"] = "synthetic_contribution_stability"
        record["name"] = "SYNTHETIC TEST ONLY: existing cubic stability contract"
        self.catalogs["claims"]["records"].append(record)
        for labels in self.catalogs["locales"]["languages"].values():
            labels["catalog_name_" + record["id"]] = labels["catalog_name_synthetic_contribution_lefm"].split(":")[0] + ": cubic"
        validate_catalogs(self.catalogs)

    def test_independent_scientific_contract_mutations_fail_closed(self):
        changes = {
            "unit": lambda r: r.update(si_unit="Pa"),
            "parameter_unit": lambda r: r["parameters"][1].update(si_unit="Pa"),
            "assumption_missing": lambda r: r["required_assumptions"].pop("crack_length_convention"),
            "assumption_changed": lambda r: r["required_assumptions"].update(geometry="edge_crack"),
            "classification": lambda r: r.update(claim_type="theoretical_bound"),
            "source_reference": lambda r: r["evidence"][0].update(source_id="missing_source"),
            "execution_support": lambda r: r.update(evaluation_support="composite_evaluate"),
            "unsupported_family": lambda r: r.update(quantity="unreviewed_strength_relation", rule_id="new_family_v1"),
            "dependency_reference": lambda r: r.update(dependencies=["missing_claim"]),
            "cyclic_dependency": lambda r: r.update(dependencies=[r["id"]]),
        }
        for name, mutation in changes.items():
            with self.subTest(name=name):
                candidate = copy.deepcopy(self.catalogs)
                mutation(candidate["claims"]["records"][-1])
                with self.assertRaises(CatalogValidationError):
                    validate_catalogs(candidate)

    def test_duplicate_ids_bad_studies_and_format_errors_fail(self):
        mutations = [
            lambda c: c["claims"]["records"].append(copy.deepcopy(c["claims"]["records"][-1])),
            lambda c: c["sources"]["records"].append(copy.deepcopy(c["sources"]["records"][-1])),
            lambda c: c["observations"]["records"].append(copy.deepcopy(c["observations"]["records"][0])),
            lambda c: c["observations"]["records"][0].update(study_id="missing_study"),
            lambda c: c["observations"]["records"][0].update(study_id="synthetic_contribution_source"),
            lambda c: c["sources"]["records"][-1].update(urls=["not a URI"]),
            lambda c: c["sources"]["records"][-1]["provenance"].update(curation_date="2026-02-30"),
        ]
        for i, mutation in enumerate(mutations):
            with self.subTest(i=i):
                candidate = copy.deepcopy(self.catalogs)
                mutation(candidate)
                with self.assertRaises(CatalogValidationError):
                    validate_catalogs(candidate)

    def test_executable_registry_is_exact_not_merely_eight_entries(self):
        def executable(candidate):
            return next(r for r in candidate["claims"]["records"] if r["id"] == "voigt_bulk")
        mutations = [
            lambda c: executable(c).update(rule_id="unregistered_v1"),
            lambda c: executable(c).update(id="replaced_executable"),
            lambda c: c["claims"]["records"].remove(executable(c)),
        ]
        for mutation in mutations:
            candidate = copy.deepcopy(self.catalogs)
            mutation(candidate)
            with self.assertRaises(CatalogValidationError):
                validate_catalogs(candidate)

    def test_every_required_family_assumption_is_checked_beyond_schema(self):
        # Some public schema branches require only distinguishing premises. The
        # development guard also requires all shared LEFM physical assumptions.
        for original in self.catalogs["claims"]["records"]:
            for key, value in original["required_assumptions"].items():
                for mutation in ("remove", "change"):
                    with self.subTest(record=original["id"], assumption=key, mutation=mutation):
                        candidate = copy.deepcopy(self.catalogs)
                        target = next(r for r in candidate["claims"]["records"] if r["id"] == original["id"])
                        if mutation == "remove":
                            target["required_assumptions"].pop(key)
                        else:
                            target["required_assumptions"][key] = (not value) if isinstance(value, bool) else "unsupported"
                        with self.assertRaises(CatalogValidationError):
                            validate_catalogs(candidate)

    def test_same_shape_unknown_rule_family_and_bool_numeric_alias_fail(self):
        self.catalogs["claims"]["records"][-1]["rule_id"] = "unsupported_lefm_family_v1"
        with self.assertRaisesRegex(CatalogValidationError, "unsupported scientific family"):
            validate_catalogs(self.catalogs)
        self.catalogs = contribution_catalogs()
        self.catalogs["claims"]["records"][-1]["required_assumptions"]["positive_crack_half_length"] = 1
        with self.assertRaises(CatalogValidationError):
            validate_catalogs(self.catalogs)

    def test_four_authored_languages_required_without_review_upgrade(self):
        mutations = [
            lambda c: c["locales"]["languages"].pop("ja"),
            lambda c: c["locales"]["languages"]["de"].pop("catalog_name_synthetic_contribution_lefm"),
            lambda c: c["locales"]["languages"]["zh"].update(catalog_name_synthetic_contribution_lefm=" "),
            lambda c: c["locales"]["languages"]["de"].update(catalog_name_synthetic_contribution_lefm="{unsupported_placeholder}"),
            lambda c: c["locales"].update(translation_review="scientifically_reviewed"),
        ]
        for mutation in mutations:
            candidate = copy.deepcopy(self.catalogs)
            mutation(candidate)
            with self.assertRaises(CatalogValidationError):
                validate_catalogs(candidate)
        for labels in self.catalogs["locales"]["languages"].values():
            del labels["catalog_name_synthetic_contribution_lefm"]
        with self.assertRaises(CatalogValidationError):
            validate_catalogs(self.catalogs)

    def test_queries_rendering_and_execution_stay_separate(self):
        before = evaluate(example())
        read = lambda name: copy.deepcopy(self.catalogs[name])
        with patch("materials_boundaries.catalog.read_catalog", side_effect=read), \
             patch("materials_boundaries.catalog_output.read_catalog", side_effect=read), \
             patch("materials_boundaries.i18n.read_catalog", side_effect=read), \
             patch("materials_boundaries.visualization.read_catalog", side_effect=read):
            result = query_catalog("claims", record_id="synthetic_contribution_lefm")
            for language in ("en", "zh", "ja", "de"):
                text = render_catalog(result, "claims", language)
                label = self.catalogs["locales"]["languages"][language]["catalog_name_synthetic_contribution_lefm"]
                self.assertIn(label, text)
                self.assertNotIn("[missing:", text)
                self.assertEqual(query_catalog("claims", record_id="synthetic_contribution_lefm", query=label), result)
            source_matches = query_catalog("claims", source_id="synthetic_contribution_source")["records"]
            self.assertTrue({"synthetic_contribution_lefm", "lefm_central_crack_mode_i_stress_intensity"}
                            <= {r["id"] for r in source_matches})
            self.assertTrue(all("synthetic_contribution_source" in {e["source_id"] for e in r["evidence"]}
                                for r in source_matches))
            self.assertEqual(evaluate(example()), before)
            bundle = build_comparison([example()], fractions=[0, 0.5, 1])
            rendered = json.dumps(bundle) + render_html(bundle) + render_svg(bundle, bundle["cases"][0]["id"])
            self.assertNotIn("synthetic_contribution", rendered)
            self.assertEqual(len(bundle["series"]), 8)
            self.assertEqual({(r["id"], r["rule_id"]) for r in bundle["catalogs"]["claims"]["records"]}, EXPECTED_EXECUTABLE_PAIRS)

    def _write_candidate(self, directory):
        for name, catalog in self.catalogs.items():
            (directory / f"{name}.json").write_text(json.dumps(catalog, ensure_ascii=False), encoding="utf-8")

    def test_development_command_reads_candidate_directory_and_reports_limits(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            self._write_candidate(directory)
            before = {p.name: p.read_bytes() for p in directory.iterdir()}
            result = subprocess.run([sys.executable, "scripts/validate_catalogs.py", "--data-dir", str(directory)], cwd=ROOT, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("exactly 8 composite executable pairs", result.stdout)
            self.assertIn("not certified", result.stdout)
            self.assertEqual({p.name: p.read_bytes() for p in directory.iterdir()}, before)

    def test_strict_json_rejects_duplicates_nonfinite_and_overflow(self):
        for payload in ('{"schema_version":"1.0.0","schema_version":"1.0.0","records":[]}',
                        '{"value":NaN}', '{"value":Infinity}', '{"value":1e999}', '{"value":1e-999}'):
            with self.subTest(payload=payload), tempfile.TemporaryDirectory() as tmp:
                directory = Path(tmp)
                self._write_candidate(directory)
                (directory / "sources.json").write_text(payload)
                result = subprocess.run([sys.executable, "scripts/validate_catalogs.py", "--data-dir", str(directory)], cwd=ROOT, text=True, capture_output=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("Catalog validation failed:", result.stderr)
                self.assertNotIn("PASS:", result.stdout)

    def test_missing_jsonschema_is_an_error_not_a_skipped_check(self):
        # -S suppresses site packages in an isolated interpreter.
        result = subprocess.run([sys.executable, "-S", "scripts/validate_catalogs.py"], cwd=ROOT, text=True, capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("requires jsonschema", result.stderr)
        self.assertNotIn("PASS:", result.stdout)

    def test_missing_format_support_is_an_error_not_a_skipped_check(self):
        checker = FormatChecker()
        checker.checkers.pop("uri", None)
        with patch("scripts.validate_catalogs.FormatChecker", return_value=checker):
            with self.assertRaisesRegex(CatalogValidationError, "required format checkers unavailable: uri"):
                validate_catalogs(self.catalogs)


if __name__ == "__main__":
    unittest.main()
