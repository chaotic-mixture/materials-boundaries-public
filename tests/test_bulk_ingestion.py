"""Synthetic fixtures exercise generic staging, not real material coverage."""
from copy import deepcopy
from dataclasses import replace
import hashlib
import json
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from materials_boundaries.bulk_ingestion import (
    IngestionError, SourceProfile, admit_batch, canonical_json_bytes, coverage,
    registry_digest, sha256_json, stage_batch, validate_decimal, verify_source_files,
)

ROOT = Path(__file__).resolve().parents[1]


def synthetic_batch(count=1):
    """Generate compact clearly fictional rows, never runtime catalog data."""
    evidence = {"file_id": "file_synthetic", "locator": "synthetic row 1",
                "record_id": "synthetic_record_1", "fields": ["density"],
                "row_number": 1, "line_start": 2, "line_end": 2,
                "accession": None, "citation": "Synthetic test fixture"}
    registry = {
        "releases": [{"release_id": "release_synthetic", "source_id": "source_synthetic",
                      "version": "synthetic-1", "immutable_id": "urn:test:synthetic-1",
                      "citation": "Synthetic test fixture, no factual material claims",
                      "license_id": "license_synthetic"}],
        "files": [{"file_id": "file_synthetic", "release_id": "release_synthetic",
                   "file_name": "synthetic.csv", "sha256": hashlib.sha256(b"synthetic\n").hexdigest(),
                   "byte_length": 10, "download_url": "https://example.invalid/synthetic.csv"}],
        "licenses": [{"license_id": "license_synthetic", "identifier": "CC-BY-4.0",
                      "grant_url": "https://example.invalid/synthetic-license",
                      "grant_version": "synthetic-1", "grant_text": "Synthetic fixture grant only",
                      "attribution": "Synthetic Test Fixture", "scope": "synthetic rows only",
                      "restrictions": ["Preserve synthetic-fixture attribution"],
                      "inspected_by": "Synthetic fixture author", "inspected_on": "2026-10-07",
                      "evidence_sha256": "e" * 64, "attested": True}],
    }
    materials, observations = [], []
    for i in range(count):
        key = f"synthetic:material:{i:06d}"
        ev = dict(evidence, locator=f"synthetic row {i + 1}", record_id=f"synthetic_record_{i + 1}",
                  row_number=i + 1, line_start=i + 2, line_end=i + 2)
        materials.append({"identity_key": key, "primary_class": "metal",
                          "name": f"SYNTHETIC material {i}", "aliases": [], "taxon": None,
                          "evidence": [deepcopy(ev)], "metadata": {"fictional": True}})
        observations.append({"observation_id": f"synthetic_density_{i}", "identity_key": key,
                             "quantity": "mass_density", "value": "1000.00", "unit": "kg/m^3",
                             "evidence_kind": "synthetic_test_only", "state_key": None,
                             "evidence": [deepcopy(ev)],
                             "metadata": {"original_number": "1.0000", "original_unit": "g/cm^3",
                                          "missing_temperature": None}})
    return {"schema_version": "1.0.0", "batch_id": "synthetic_batch", "adapter_id": "synthetic_adapter",
            "registry": registry, "materials": materials, "observations": observations, "exclusions": []}


def validate_synthetic(observation, material, registry):
    if observation["quantity"] != "mass_density" or observation["unit"] != "kg/m^3":
        raise ValueError("synthetic contract requires mass_density in kg/m^3")
    if observation["metadata"].get("original_unit") != "g/cm^3":
        raise ValueError("original units must be retained")
    if material["metadata"].get("fictional") is not True:
        raise ValueError("synthetic fixture marker required")


def synthetic_profile(batch):
    return SourceProfile("synthetic_adapter", "synthetic-1", registry_digest(batch["registry"]),
                         frozenset({"CC-BY-4.0"}), validate_synthetic)


def staged(batch=None, baseline=(), profile=None):
    batch = synthetic_batch() if batch is None else batch
    return stage_batch(batch, baseline=baseline,
                       profiles=[synthetic_profile(batch) if profile is None else profile])


def approval(package, keys=None):
    return {"decision": "approve", "reviewer": "Synthetic explicit review",
            "review_manifest_sha256": package["review_manifest_sha256"],
            "approved_identity_keys": keys if keys is not None else [row["identity_key"] for row in package["materials"]]}


class BulkIngestionTests(unittest.TestCase):
    def reasons(self, package):
        return {row["reason"] for row in package["quarantine"]}

    def test_stage_is_review_only_and_does_not_mutate_inputs(self):
        batch = synthetic_batch(2)
        original = deepcopy(batch)
        result = staged(batch)
        self.assertEqual(batch, original)
        self.assertEqual(result["manifest"]["counts"]["by_status"],
                         {"proposed": 0, "held": 0, "source_supported": 2, "admitted": 0})
        self.assertEqual(result["manifest"]["counts"]["admitted_unique_keys_with_numeric_property"], 0)
        self.assertEqual(result["input"]["registry"]["licenses"][0]["attribution"], "Synthetic Test Fixture")

    def test_unregistered_adapter_stays_proposed(self):
        result = stage_batch(synthetic_batch())
        self.assertEqual(result["materials"][0]["status"], "proposed")
        with self.assertRaises(IngestionError):
            admit_batch(result, approval(result), expected_review_digest=result["review_manifest_sha256"], profiles=[])

    def test_reordering_tables_fields_aliases_is_byte_stable(self):
        batch = synthetic_batch(6)
        batch["materials"][0]["aliases"] = ["synthetic B", "synthetic A"]
        batch["observations"][0]["evidence"][0]["fields"] = ["density", "label"]
        one = staged(batch)
        shuffled = deepcopy(batch)
        rng = random.Random(107)
        for table in ("materials", "observations", "exclusions"):
            rng.shuffle(shuffled[table])
        for row in shuffled["materials"]:
            row["aliases"].reverse()
        for row in shuffled["observations"]:
            row["evidence"][0]["fields"].reverse()
        two = staged(shuffled)
        self.assertEqual(canonical_json_bytes(one), canonical_json_bytes(two))
        self.assertEqual(canonical_json_bytes(two), canonical_json_bytes(staged(shuffled)))
        self.assertEqual(canonical_json_bytes(one), canonical_json_bytes(staged(one["input"])))

    def test_registry_row_order_does_not_change_pin(self):
        batch = synthetic_batch()
        registry = batch["registry"]
        registry["files"].append(dict(registry["files"][0], file_id="file_synthetic_b"))
        before = registry_digest(registry)
        registry["files"].reverse()
        self.assertEqual(before, registry_digest(registry))

    def test_identical_duplicates_do_not_inflate_count(self):
        batch = synthetic_batch()
        batch["materials"] *= 3
        batch["observations"] *= 3
        result = staged(batch)
        self.assertEqual(len(result["materials"]), 1)
        self.assertEqual(len(result["observations"]), 1)
        self.assertEqual(result["manifest"]["counts"]["by_status"]["source_supported"], 1)

    def test_aliases_and_multiple_states_are_not_materials(self):
        batch = synthetic_batch()
        batch["materials"][0]["aliases"] = ["SYN-A", "SYN-B", "SYN-A"]
        for i in range(3):
            observation = deepcopy(batch["observations"][0])
            observation.update(observation_id=f"synthetic_state_{i}", state_key=f"synthetic_state_{i}")
            batch["observations"].append(observation)
        result = staged(batch)
        admitted = admit_batch(result, approval(result), expected_review_digest=result["review_manifest_sha256"], profiles=[synthetic_profile(batch)])
        self.assertEqual(admitted["admission_counts"]["admitted_unique_keys_with_numeric_property"], 1)
        self.assertEqual(len(admitted["observations"]), 4)
        self.assertEqual(admitted["materials"][0]["aliases"], ["SYN-A", "SYN-B"])

    def test_baseline_deduplicates_canonical_identity(self):
        batch = synthetic_batch(2)
        baseline = [{key: batch["materials"][0][key] for key in ("identity_key", "primary_class")}]
        result = staged(batch, baseline=baseline * 2)
        self.assertEqual(result["manifest"]["counts"]["by_status"]["source_supported"], 1)
        self.assertEqual(result["manifest"]["counts"]["by_status"]["held"], 1)
        self.assertIn("baseline_duplicate", self.reasons(result))

    def test_conflicting_baseline_class_holds_candidate(self):
        batch = synthetic_batch()
        result = staged(batch, baseline=[{"identity_key": batch["materials"][0]["identity_key"], "primary_class": "polymer"}])
        self.assertIn("baseline_identity_conflict", self.reasons(result))
        self.assertEqual(result["materials"][0]["status"], "held")

    def test_conflicting_baseline_fails_closed(self):
        key = synthetic_batch()["materials"][0]["identity_key"]
        with self.assertRaises(IngestionError):
            staged(baseline=[{"identity_key": key, "primary_class": cls} for cls in ("metal", "polymer")])

    def test_conflicting_material_definitions_have_no_winner(self):
        batch = synthetic_batch()
        conflict = deepcopy(batch["materials"][0])
        conflict["primary_class"] = "natural"
        batch["materials"].append(conflict)
        first = staged(batch)
        batch["materials"].reverse()
        second = staged(batch)
        self.assertEqual(first, second)
        self.assertIn("conflicting_identity", self.reasons(first))
        self.assertNotIn("primary_class", first["materials"][0])
        self.assertEqual(first["materials"][0]["status"], "held")

    def test_conflicting_observation_ids_hold_whole_identity(self):
        batch = synthetic_batch()
        conflict = deepcopy(batch["observations"][0])
        conflict["value"] = "999"
        batch["observations"].append(conflict)
        result = staged(batch)
        self.assertIn("conflicting_observation_id", self.reasons(result))
        self.assertEqual(result["observations"], [])
        self.assertEqual(result["materials"][0]["status"], "held")

    def test_same_evidence_conflicting_values_cannot_hide_behind_new_id(self):
        batch = synthetic_batch()
        conflict = deepcopy(batch["observations"][0])
        conflict.update(observation_id="different_id", value="999")
        batch["observations"].append(conflict)
        result = staged(batch)
        self.assertIn("conflicting_evidence_claim", self.reasons(result))
        self.assertTrue(all(row["status"] == "held" for row in result["observations"]))

    def test_bad_licenses_and_missing_grant_details_hold(self):
        for field, value in (("identifier", "All-rights-reserved"), ("grant_text", ""),
                             ("attribution", ""), ("grant_url", "http://example.invalid"),
                             ("evidence_sha256", "not-a-hash"), ("attested", False)):
            with self.subTest(field=field):
                batch = synthetic_batch()
                profile = synthetic_profile(batch)
                batch["registry"]["licenses"][0][field] = value
                result = staged(batch, profile=profile)
                self.assertIn("invalid_registry", self.reasons(result))
                self.assertEqual(result["materials"][0]["status"], "held")

    def test_sharealike_is_source_policy_not_universal_ban(self):
        batch = synthetic_batch()
        batch["registry"]["licenses"][0]["identifier"] = "CC-BY-SA-4.0"
        profile = replace(synthetic_profile(batch), allowed_licenses=frozenset({"CC-BY-SA-4.0"}))
        self.assertEqual(staged(batch, profile=profile)["materials"][0]["status"], "source_supported")
        self.assertEqual(staged(batch)["materials"][0]["status"], "held")

    def test_registry_pin_detects_immutable_and_attribution_changes(self):
        for table, field, value in (("files", "sha256", "0" * 64),
                                    ("releases", "version", "another-version"),
                                    ("licenses", "attribution", "replacement-attribution")):
            batch = synthetic_batch()
            profile = synthetic_profile(batch)
            batch["registry"][table][0][field] = value
            self.assertIn("invalid_registry", self.reasons(staged(batch, profile=profile)))

    def test_duplicate_registry_keys_hold_even_identical(self):
        batch = synthetic_batch()
        batch["registry"]["files"] *= 2
        self.assertIn("invalid_registry", self.reasons(staged(batch)))

    def test_missing_and_unknown_provenance_hold(self):
        for table in ("materials", "observations"):
            for evidence in ([], [{"file_id": "unknown", "locator": "line 1", "record_id": "x", "fields": ["value"]}]):
                with self.subTest(table=table, evidence=evidence):
                    batch = synthetic_batch()
                    batch[table][0]["evidence"] = evidence
                    self.assertEqual(staged(batch)["materials"][0]["status"], "held")

    def test_nonfinite_exponent_numeric_types_and_overlong_values_rejected(self):
        for value in ("NaN", "Infinity", "-Infinity", "1e3", "1E-3", " 1", "+1", "01", "-0.00", "9" * 25, "0." + "1" * 25, 2, True, None):
            with self.subTest(value=value):
                batch = synthetic_batch()
                batch["observations"][0]["value"] = value
                self.assertEqual(staged(batch)["materials"][0]["status"], "held")
        for value in (float("nan"), float("inf"), 1.5):
            batch = synthetic_batch()
            batch["observations"][0]["value"] = value
            with self.assertRaises(IngestionError):
                staged(batch)
        for value in ("0", "0.000", "-2.5", "1000.00"):
            validate_decimal(value)

    def test_original_strings_and_null_missingness_remain_exact(self):
        batch = synthetic_batch()
        result = staged(batch)
        self.assertEqual(result["observations"][0]["value"], "1000.00")
        self.assertEqual(result["observations"][0]["metadata"], batch["observations"][0]["metadata"])
        self.assertEqual(result["input"], batch)

    def test_numeric_property_is_required_for_coverage(self):
        batch = synthetic_batch()
        batch["observations"] = []
        result = staged(batch)
        self.assertIn("no_traceable_numeric_property", self.reasons(result))
        self.assertEqual(result["materials"][0]["status"], "held")

    def test_semantic_validator_rejects_quantity_and_cannot_mutate_data(self):
        batch = synthetic_batch()
        batch["observations"][0]["quantity"] = "unspecified_density"
        self.assertIn("semantic_validation_failed", self.reasons(staged(batch)))
        batch = synthetic_batch()
        def mutator(observation, material, registry):
            observation["value"] = "42"
            material["primary_class"] = "natural"
            registry["files"].clear()
        result = staged(batch, profile=replace(synthetic_profile(batch), validate_observation=mutator))
        self.assertEqual(result["observations"][0]["value"], "1000.00")
        self.assertEqual(result["materials"][0]["primary_class"], "metal")

    def test_candidate_status_and_legacy_license_claims_cannot_promote(self):
        for table in ("materials", "observations"):
            for status in ("source_supported", "admitted"):
                batch = synthetic_batch()
                batch[table][0]["status"] = status
                self.assertEqual(staged(batch)["materials"][0]["status"], "held")
        batch = synthetic_batch()
        batch["registry"]["licenses"][0]["license_review_status"] = "cleared"
        self.assertEqual(staged(batch)["materials"][0]["status"], "held")

    def test_unknown_primary_class_is_held(self):
        batch = synthetic_batch()
        batch["materials"][0]["primary_class"] = "wood"
        self.assertEqual(staged(batch)["materials"][0]["status"], "held")
        for category in ("metal", "inorganic", "polymer", "composite", "natural"):
            batch["materials"][0]["primary_class"] = category
            self.assertEqual(staged(batch)["materials"][0]["status"], "source_supported")

    def test_explicit_exclusions_are_machine_readable_and_bind_review(self):
        batch = synthetic_batch(2)
        initial = staged(batch)
        batch["exclusions"] = [{"observation_id": "synthetic_density_0", "reason": "unreviewed_mapping", "detail": "Synthetic mapping awaits review"}]
        result = staged(batch)
        self.assertIn("excluded_unreviewed_mapping", self.reasons(result))
        self.assertNotEqual(initial["review_manifest_sha256"], result["review_manifest_sha256"])
        self.assertEqual(result["manifest"]["counts"]["by_status"]["source_supported"], 1)
        batch["exclusions"][0]["identity_key"] = batch["materials"][1]["identity_key"]
        with self.assertRaises(IngestionError):
            staged(batch)

    def test_malformed_row_is_quarantined_without_crashing(self):
        for field, value in (("identity_key", {}), ("evidence", None), ("metadata", [])):
            batch = synthetic_batch()
            batch["observations"][0][field] = value
            result = staged(batch)
            self.assertIn("invalid_observation", self.reasons(result))
        batch = synthetic_batch()
        batch["materials"].append(None)
        self.assertIn("invalid_material", self.reasons(staged(batch)))

    def test_admission_requires_exact_separate_review_and_remains_pure(self):
        batch = synthetic_batch(2)
        result = staged(batch)
        original = deepcopy(result)
        selected = [batch["materials"][0]["identity_key"]]
        admitted = admit_batch(result, approval(result, selected), expected_review_digest=result["review_manifest_sha256"], profiles=[synthetic_profile(batch)])
        self.assertEqual(result, original)
        self.assertEqual(admitted["admission_counts"]["by_status"], {"proposed": 0, "held": 0, "source_supported": 1, "admitted": 1})
        self.assertEqual(admitted["admission_counts"]["admitted_by_primary_class"]["metal"], 1)
        with self.assertRaises(IngestionError):
            admit_batch(result, approval(result), expected_review_digest="0" * 64, profiles=[synthetic_profile(batch)])
        self.assertEqual(canonical_json_bytes(admitted), canonical_json_bytes(admit_batch(result, approval(result, selected), expected_review_digest=result["review_manifest_sha256"], profiles=[synthetic_profile(batch)])))

    def test_approval_cannot_name_held_unknown_or_duplicate_keys(self):
        batch = synthetic_batch()
        result = staged(batch)
        for keys in (["synthetic:unknown"], [batch["materials"][0]["identity_key"]] * 2, []):
            with self.assertRaises(IngestionError):
                admit_batch(result, approval(result, keys), expected_review_digest=result["review_manifest_sha256"], profiles=[synthetic_profile(batch)])
        batch["materials"][0]["status"] = "admitted"
        held = staged(batch)
        with self.assertRaises(IngestionError):
            admit_batch(held, approval(held), expected_review_digest=held["review_manifest_sha256"], profiles=[synthetic_profile(batch)])

    def test_tampering_input_tables_manifest_or_baseline_fails_replay(self):
        batch = synthetic_batch()
        result = staged(batch)
        variants = []
        for target in ("input", "observations", "materials", "manifest", "baseline"):
            changed = deepcopy(result)
            if target == "input":
                changed[target]["observations"][0]["value"] = "999"
            elif target == "observations":
                changed[target][0]["value"] = "999"
            elif target == "materials":
                changed[target][0]["status"] = "admitted"
            elif target == "manifest":
                changed[target]["input_sha256"] = "0" * 64
            else:
                changed[target].append({"identity_key": "synthetic:new", "primary_class": "metal"})
            variants.append(changed)
        for changed in variants:
            with self.assertRaises(IngestionError):
                admit_batch(changed, approval(result), expected_review_digest=result["review_manifest_sha256"], profiles=[synthetic_profile(batch)])

    def test_review_profile_change_requires_new_review(self):
        batch = synthetic_batch()
        result = staged(batch)
        with self.assertRaises(IngestionError):
            admit_batch(result, approval(result), expected_review_digest=result["review_manifest_sha256"], profiles=[replace(synthetic_profile(batch), version="synthetic-2")])

    def test_source_bytes_are_checked_without_decoding_or_replacement(self):
        batch = synthetic_batch()
        result = verify_source_files(batch["registry"], {"file_synthetic": b"synthetic\n"})
        self.assertEqual(result["registry_sha256"], registry_digest(batch["registry"]))
        for sources in ({}, {"file_synthetic": b"changed!!!"},
                        {"file_synthetic": "synthetic\n"},
                        {"file_synthetic": b"synthetic\n", "extra": b""}):
            with self.assertRaises(IngestionError):
                verify_source_files(batch["registry"], sources)
        raw = b"original invalid UTF-8 \xff\n"
        batch["registry"]["files"][0].update(sha256=hashlib.sha256(raw).hexdigest(), byte_length=len(raw))
        verify_source_files(batch["registry"], {"file_synthetic": raw})
        with self.assertRaises(IngestionError):
            verify_source_files(batch["registry"], {"file_synthetic": raw.decode("utf-8", errors="replace").encode("utf-8")})

    def test_immutable_writer_is_idempotent_and_refuses_to_replace(self):
        from scripts.stage_material_batch import write_immutable_package
        package = staged()
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "stage.json"
            self.assertTrue(write_immutable_package(target, package))
            original = target.read_bytes()
            self.assertFalse(write_immutable_package(target, package))
            changed = deepcopy(package)
            changed["manifest"]["counts"]["by_status"]["held"] += 1
            with self.assertRaises(IngestionError):
                write_immutable_package(target, changed)
            self.assertEqual(target.read_bytes(), original)
            self.assertEqual(list(Path(directory).iterdir()), [target])

    def test_cli_requires_baseline_and_only_stages(self):
        from scripts.stage_material_batch import main
        batch = synthetic_batch()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, baseline, output = (root / name for name in ("batch.json", "baseline.json", "stage.json"))
            source.write_bytes(canonical_json_bytes(batch))
            baseline.write_text("[]\n")
            with patch("scripts.stage_material_batch._reviewed_profiles", return_value=[synthetic_profile(batch)]), redirect_stdout(StringIO()) as printed:
                self.assertEqual(main([str(source), "--baseline", str(baseline), "--output", str(output)]), 0)
                self.assertEqual(main([str(source), "--baseline", str(baseline), "--output", str(output)]), 0)
            result = json.loads(output.read_text())
            self.assertEqual(result["manifest"]["counts"]["by_status"]["admitted"], 0)
            self.assertIn("Unchanged review-only stage", printed.getvalue())
            self.assertIn("No runtime catalogs changed", printed.getvalue())
            invalid = subprocess.run([sys.executable, str(ROOT / "scripts/stage_material_batch.py"), str(source), "--output", str(output)], capture_output=True, text=True)
            self.assertNotEqual(invalid.returncode, 0)
            self.assertIn("--baseline", invalid.stderr)

    def test_full_input_including_original_metadata_is_digest_bound(self):
        batch = synthetic_batch()
        first = staged(batch)
        batch["observations"][0]["metadata"]["original_number"] = "1.000"
        second = staged(batch)
        self.assertNotEqual(first["manifest"]["input_sha256"], second["manifest"]["input_sha256"])
        self.assertNotEqual(first["review_manifest_sha256"], second["review_manifest_sha256"])


if __name__ == "__main__":
    unittest.main()
