"""Source transcription, exact pressure scaling and closed admission tests.

These tests are scientific-metadata/software checks, not raw-data replication,
independent scientific review, standard certification or inferred mechanics.
"""
import copy
from decimal import Decimal, Inexact, Rounded, localcontext
import hashlib
import json
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

from jsonschema import Draft202012Validator

from materials_boundaries._observation_contract import validate_observation_records
from materials_boundaries._pa12_cf15_observation_contract import (
    PA12_DATASET, PA12_FAMILY, PA12_SOURCE, PA12_TEMPERATURES,
    is_pa12_record, validate_pa12_record, validate_pa12_dataset,
    validate_pa12_sources,
)
from source_evidence_preservation import previous_record
from materials_boundaries.catalog import read_catalog
from materials_boundaries.catalog_output import render_catalog

ROOT = Path(__file__).resolve().parents[1]


def load(relative):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def lookup(value, path):
    for key in path:
        value = value[key]
    return value


def replace(value, path, replacement):
    lookup(value, path[:-1])[path[-1]] = replacement


def leaves(value, prefix=()):
    if isinstance(value, dict):
        for key, item in value.items():
            yield from leaves(item, prefix + (key,))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from leaves(item, prefix + (index,))
    else:
        yield prefix, value


def objects(value, prefix=()):
    if isinstance(value, dict):
        yield prefix, value
        for key, item in value.items():
            yield from objects(item, prefix + (key,))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from objects(item, prefix + (index,))


def changed(value):
    if value is None:
        return "invented-known-value"
    if type(value) is bool:
        return not value
    if type(value) in (int, float):
        return value + 1
    return value + " unreviewed"


class PA12SourceTranscriptionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = load("materials_boundaries/data/observations.json")
        cls.records = sorted((r for r in cls.catalog["records"] if r.get("study_id") == PA12_SOURCE),
                             key=lambda r: int(r["source_cell"]["temperature_column"]))
        cls.sources = load("materials_boundaries/data/sources.json")
        cls.source = next(r for r in cls.sources["records"] if r["id"] == PA12_SOURCE)
        cls.facts = load("tests/fixtures/pa12_cf15_source_transcription.json")
        cls.schema = load("schemas/observations.schema.json")
        cls.validator = Draft202012Validator(cls.schema)
        # The exact same new schema branch, avoiding unrelated historical error
        # trees in exhaustive closed-leaf tests. Full envelope is also tested.
        cls.family_validator = Draft202012Validator(cls.schema["$defs"]["ciganas_pa12_cf15"])

    def assert_rejected(self, record):
        self.assertFalse(self.family_validator.is_valid(record))
        with self.assertRaises(ValueError):
            validate_pa12_record(record)
        with self.assertRaises(ValueError):
            validate_observation_records([record])

    def test_six_source_cells_and_exact_decimal_unit_scaling(self):
        self.assertEqual(self.catalog["schema_version"], "1.3.0")
        self.assertEqual(len(self.records), 6)
        self.assertTrue(self.validator.is_valid(self.catalog))
        validate_observation_records(self.catalog["records"])
        validate_pa12_dataset(self.catalog["records"], require_complete=True)
        validate_pa12_sources(self.sources["records"])
        for record, cell in zip(self.records, self.facts["cells"]):
            result = record["reported_result"]
            sd = result["uncertainty"]
            self.assertEqual(record["source_cell"]["temperature_column"], cell["temperature"])
            self.assertEqual(record["conditions"]["temperature"]["value"], int(cell["temperature"]))
            self.assertEqual(result["value_string"], cell["central"])
            self.assertEqual(sd["value_string"], cell["sd"])
            self.assertEqual(result["source_value_string"], cell["central"] + " ± " + cell["sd"])
            self.assertEqual(record["si_result"]["value"], cell["pa"])
            self.assertEqual(record["si_result"]["uncertainty_value"], cell["sd_pa"])
            self.assertEqual(Decimal(cell["central"]) * Decimal("1000000"), cell["pa"])
            self.assertEqual(Decimal(cell["sd"]) * Decimal("1000000"), cell["sd_pa"])
            self.assertEqual(Decimal(str(result["value"])), Decimal(cell["central"]))
            self.assertEqual(Decimal(str(sd["value"])), Decimal(cell["sd"]))

    def test_external_decimal_context_does_not_change_admission(self):
        with localcontext() as context:
            context.prec = 1
            context.traps[Inexact] = True
            context.traps[Rounded] = True
            validate_pa12_dataset(self.records, require_complete=True)
            for record in self.records:
                validate_pa12_record(record)

    def test_each_record_is_self_contained_with_factual_unknowns(self):
        for record in self.records:
            for path, expected in self.facts["facts_by_record_path"].items():
                with self.subTest(id=record["id"], path=path):
                    actual = lookup(record, path.split("/"))
                    self.assertEqual(actual, expected)
                    if expected is None or type(expected) is bool:
                        self.assertIs(actual, expected)
            self.assertIn("not SEM", record["reported_result"]["uncertainty"]["interpretation"])
            self.assertIn("Table 4", record["verification"]["source_inspection"]["source_version_note"])
            self.assertIn("Table 1", record["verification"]["rights"]["third_party_exclusion"])
            self.assertIn("110", record["method"]["strain_definition_note"])
            self.assertIn("80", record["method"]["strain_definition_note"])
            self.assertIn("not establish", record["method"]["stress_definition_note"])
            self.assertIn("1 °C/min", record["conditions"]["temperature"]["control_description"])

    def test_component_locators_match_their_specific_facts(self):
        for record in self.records:
            evidence = record["evidence"]
            self.assertEqual(evidence[1]["component_id"], "sec2dot1-polymers-18-00563")
            self.assertIn("30-minute chamber stabilization", evidence[1]["verified_as"])
            self.assertEqual(evidence[3]["component_id"], "sec2dot2-polymers-18-00563")
            self.assertNotIn("stabilization", evidence[3]["verified_as"])
            self.assertEqual(evidence[4], record["sample_metadata"]["count_definition_source"])
            self.assertEqual(evidence[4]["component_id"], "sec2dot2-polymers-18-00563")
            self.assertEqual(record["reported_result"]["uncertainty"]["evidence"], evidence[0])
            for item in evidence:
                self.assertEqual(item["source_id"], PA12_SOURCE)
                self.assertTrue(item["source_url"].startswith(self.facts["source_url"]))

    def test_source_bibliography_rights_and_version_are_scoped(self):
        self.assertEqual(self.source["doi"], self.facts["doi"])
        self.assertEqual(self.source["authors"], ["Justas Ciganas", "Tomas Kalinauskis", "Urte Cigane"])
        self.assertEqual(self.source["license"]["identifier"], "CC-BY-4.0")
        notes = " ".join(self.source["claim_notes"])
        for phrase in ("PDF not inspected", "Table 4", "Table 1", "independent scientific review",
                       "MIT", "Reorganized", "10.3390/polym18050563", "2026 by the authors"):
            self.assertIn(phrase, notes)
        self.assertNotIn("https://www.iso.org/standard/527-2", self.source["urls"])

    def test_every_scientific_leaf_is_closed_in_schema_and_runtime(self):
        original = self.records[0]
        for path, value in leaves(original):
            if path in (("id",), ("name",)):
                continue
            with self.subTest(path=path):
                record = copy.deepcopy(original)
                replace(record, path, changed(value))
                self.assert_rejected(record)

    def test_each_required_key_and_nested_extra_fail_closed(self):
        original = self.records[0]
        for path, value in objects(original):
            with self.subTest(extra_at=path):
                record = copy.deepcopy(original)
                lookup(record, path)["unreviewed_extension"] = True
                self.assert_rejected(record)
            for key in value:
                with self.subTest(deleted_at=path + (key,)):
                    record = copy.deepcopy(original)
                    del lookup(record, path)[key]
                    self.assert_rejected(record)

    def test_cell_binding_prevents_temperature_or_result_swaps(self):
        for i, original in enumerate(self.records):
            other = self.records[(i + 1) % 6]
            for path in (("source_cell",), ("conditions", "temperature"), ("reported_result",), ("si_result",)):
                with self.subTest(i=i, path=path):
                    record = copy.deepcopy(original)
                    replace(record, path, copy.deepcopy(lookup(other, path)))
                    self.assert_rejected(record)

    def test_boolean_nonfinite_and_wrong_types_never_become_numbers(self):
        for path in (("reported_result", "value"), ("reported_result", "uncertainty", "value"),
                     ("si_result", "value"), ("si_result", "uncertainty_value"),
                     ("conditions", "temperature", "value"), ("sample_metadata", "count"),
                     ("method", "loading_rate", "value")):
            for replacement in (True, False, float("nan"), float("inf"), float("-inf"), 10**400, "1", [], {}):
                with self.subTest(path=path, value=replacement):
                    record = copy.deepcopy(self.records[0])
                    replace(record, path, replacement)
                    self.assert_rejected(record)

    def test_json_equivalent_integral_floats_are_accepted(self):
        record = copy.deepcopy(self.records[0])
        for path, value in list(leaves(record)):
            if type(value) is int:
                replace(record, path, float(value))
        self.assertTrue(self.family_validator.is_valid(record))
        validate_pa12_record(record)

    def test_subset_and_renamed_identity_are_supported_but_aliases_are_not_new_cells(self):
        validate_pa12_dataset([])
        for original in self.records:
            record = copy.deepcopy(original)
            record["id"] = "renamed-observation"
            record["name"] = "A renamed display title"
            self.assertTrue(self.family_validator.is_valid(record))
            validate_observation_records([record])
            validate_pa12_dataset([record])
            with self.assertRaises(ValueError):
                validate_pa12_dataset([record], require_complete=True)
            with self.assertRaises(ValueError):
                validate_pa12_dataset([original, record])
        renamed = copy.deepcopy(self.records)
        for i, record in enumerate(renamed):
            record["id"] = "renamed-" + str(i)
        validate_pa12_dataset(renamed, require_complete=True)
        with self.assertRaises(ValueError):
            validate_pa12_dataset(renamed + [copy.deepcopy(self.records[0])], require_complete=True)
        # Catalog ordering is presentation-only; completeness is by source cell.
        validate_pa12_dataset(list(reversed(renamed)), require_complete=True)

    def test_family_source_dataset_spoofing_cannot_escape_guards(self):
        for discriminator in ("method_family", "study_id", "dataset_id", "protocol_id"):
            for replacement in (None, "lee_wei_kysar_hone_2008", "bertolazzi_2011_mos2_monolayer_indentation_v1"):
                record = copy.deepcopy(self.records[0])
                if replacement is None:
                    del record[discriminator]
                else:
                    record[discriminator] = replacement
                self.assertTrue(is_pa12_record(record))
                self.assert_rejected(record)
        for legacy in (r for r in self.catalog["records"] if r["observation_type"] == "experiment_derived_model_dependent"):
            record = copy.deepcopy(legacy)
            record["dataset_id"] = PA12_DATASET
            self.assertTrue(is_pa12_record(record))
            with self.assertRaises(ValueError):
                validate_observation_records([record])
        disguised = copy.deepcopy(self.records[0])
        for field in ("method_family", "study_id", "dataset_id", "protocol_id"):
            disguised.pop(field)
        disguised["study_id"] = "lee_wei_kysar_hone_2008"
        self.assert_rejected(disguised)

    def test_actual_source_payload_is_closed_in_runtime(self):
        for path, value in leaves(self.source):
            with self.subTest(path=path):
                source = copy.deepcopy(self.source)
                replace(source, path, changed(value))
                with self.assertRaises(ValueError):
                    validate_pa12_sources([source])
        for key in self.source:
            source = copy.deepcopy(self.source)
            del source[key]
            with self.subTest(deleted=key), self.assertRaises(ValueError):
                validate_pa12_sources([source])
        source = copy.deepcopy(self.source)
        source["id"] = "renamed-source"
        with self.assertRaises(ValueError):
            validate_pa12_sources([source])
        with self.assertRaises(ValueError):
            validate_pa12_sources([self.source, copy.deepcopy(self.source)])
        validate_pa12_sources([])
        validate_pa12_sources([s for s in self.sources["records"] if s["id"] != PA12_SOURCE])

    def test_historical_record_payloads_remain_exact(self):
        frozen = load("tests/fixtures/pre_pa12_v0220.json")["record_sha256"]
        for kind, expected in frozen.items():
            current = {r["id"]: r for r in load("materials_boundaries/data/" + kind + ".json")["records"]}
            for identifier, digest in expected.items():
                with self.subTest(kind=kind, id=identifier):
                    record = previous_record(kind, current[identifier])
                    if kind == "claims":
                        # Existing contracts allow additional source evidence.
                        # Require every exact historical member, then hash the
                        # untouched baseline payload in its recorded order.
                        fixture = load("tests/fixtures/pre_pa12_v0220.json")
                        evidence = {hashlib.sha256(json.dumps(item, ensure_ascii=False,
                            sort_keys=True, separators=(",", ":")).encode()).hexdigest(): item
                            for item in record["evidence"]}
                        record["evidence"] = [evidence[h] for h in fixture["claim_evidence_sha256"][identifier]]
                    actual = hashlib.sha256(json.dumps(record, ensure_ascii=False,
                        sort_keys=True, separators=(",", ":")).encode()).hexdigest()
                    self.assertEqual(actual, digest)

    def test_development_validator_enforces_source_truth_and_complete_cells(self):
        from scripts.validate_catalogs import load_catalogs, validate_catalogs, CatalogValidationError
        catalogs = load_catalogs(ROOT / "materials_boundaries/data")
        validate_catalogs(catalogs)
        candidates = []
        missing = copy.deepcopy(catalogs)
        missing["observations"]["records"] = [r for r in missing["observations"]["records"]
            if r["id"] != self.records[-1]["id"]]
        candidates.append(missing)
        alias = copy.deepcopy(catalogs)
        aliased = copy.deepcopy(self.records[0])
        aliased["id"] = "duplicate-source-cell-alias"
        alias["observations"]["records"].append(aliased)
        candidates.append(alias)
        for path, value in ((("doi",), "10.0000/unreviewed"),
                            (("claim_notes", 0), "All representations including PDF agree"),
                            (("license", "identifier"), "MIT"),
                            (("provenance", "method"), "Independent replication")):
            candidate = copy.deepcopy(catalogs)
            source = next(r for r in candidate["sources"]["records"] if r["id"] == PA12_SOURCE)
            replace(source, path, value)
            candidates.append(candidate)
        for candidate in candidates:
            with self.assertRaises(CatalogValidationError):
                validate_catalogs(candidate)

    def test_legacy_clones_do_not_expand_or_break_the_six_cell_contract(self):
        records = copy.deepcopy(self.catalog["records"])
        clones = [copy.deepcopy(r) for r in records if r["observation_type"] == "experiment_derived_model_dependent"]
        for index, record in enumerate(clones):
            record["id"] = "legacy-clone-" + str(index)
            record["name"] = "Legacy family renamed observation"
        records.extend(clones)
        self.assertEqual(len(records), len(self.catalog["records"]) + len(clones))
        self.assertEqual(sum(is_pa12_record(r) for r in records), 6)
        validate_observation_records(records)
        validate_pa12_dataset(records, require_complete=True)
        self.assertEqual(tuple(sorted((r["source_cell"]["temperature_column"] for r in records
            if is_pa12_record(r)), key=int)), PA12_TEMPERATURES)

    def test_catalog_reads_and_source_text_use_dependency_free_guards(self):
        record = copy.deepcopy(self.records[0])
        record["conditions"]["temperature"]["basis"] = "directly_measured_specimen"
        candidate = copy.deepcopy(self.catalog)
        target = next(i for i, r in enumerate(candidate["records"]) if r["id"] == record["id"])
        candidate["records"][target] = record
        resource = Mock()
        resource.joinpath.return_value.read_text.return_value = json.dumps(candidate)
        with patch("materials_boundaries.catalog.files", return_value=resource), self.assertRaises(ValueError):
            read_catalog("observations")
        with self.assertRaises(ValueError):
            render_catalog(candidate, "observations")
        source = copy.deepcopy(self.source)
        source["claim_notes"][0] = "All source representations and PDF agree"
        # The intentionally generic source schema is insufficient by itself.
        source_catalog = {"schema_version": "1.0.0", "records": [source]}
        source_schema = Draft202012Validator(load("schemas/sources.schema.json"))
        self.assertTrue(source_schema.is_valid(source_catalog))
        resource.joinpath.return_value.read_text.return_value = json.dumps(source_catalog)
        with patch("materials_boundaries.catalog.files", return_value=resource), self.assertRaises(ValueError):
            read_catalog("sources")
        with self.assertRaises(ValueError):
            render_catalog(source_catalog, "sources")


if __name__ == "__main__":
    unittest.main()
