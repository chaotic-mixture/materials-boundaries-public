"""Closed reviewed-wood adapter regressions; fixture is factual metadata only."""
from copy import deepcopy
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from materials_boundaries.bulk_ingestion import (IngestionError, admit_batch, canonical_json_bytes,
    registry_digest, stage_batch)
from materials_boundaries import wood_bulk_adapter as wood
from materials_boundaries.material_references import validate_material_catalog

# One exact reviewed row, no source PDFs, full raw data, or source cache assets.
FIXTURE = json.loads(r'''
{
  "reviewed_candidate": {
    "binomial": "Abies alba",
    "family": "Pinaceae",
    "major_class": null,
    "classification_status": "user_decision_pending",
    "taxonomic_basis": "independently_checked_pinned_WFO_June2023_authority_aware_chain",
    "property": "basic_wood_density",
    "quantity_scope": "selected_CIRAD_collection_accession_record; not species mean or engineering design value",
    "density_g_cm3": "0.38",
    "reported_rounding_increment_g_cm3": "0.01",
    "reported_rounding_increment_kg_m3": "10",
    "density_kg_m3": "380",
    "evidence_type": "conversion_derived_estimate_from_measured_airdry_specific_gravity",
    "mass_basis": "oven_dry",
    "volume_basis": "fresh_or_water_saturated",
    "original_quantity": "Airdry SG/Density",
    "original_value_as_reported": "0.46",
    "original_property_label": "Specific gravity",
    "original_unit": "dimensionless",
    "original_unit_status": "dimensionless_SG_verified_in_original_CIRAD_paper_p15_footnote5",
    "nominal_conversion_moisture_percent": "12",
    "moisture_basis_status": "nominal_GWDD_basis_not_measured_per_specimen",
    "measured_specimen_moisture_percent": null,
    "conversion_factor": "0.8281316",
    "selected_gwdd_id": "10084",
    "selected_gwdd_csv_data_record_1based": 7854,
    "selected_source_key": "gwdd-source-a165581780152467",
    "selected_original_specimen_id": "CTFT 2803",
    "original_dataset_doi": "10.18167/DVN1/CDHU51",
    "original_file_id": 11836,
    "original_csv_data_record_1based": 2803,
    "original_physical_line_start": 2804,
    "original_physical_line_end": 2804,
    "original_species_reference": "Abies alba Mill.",
    "original_value_exact_match": true,
    "source_species_tokens_exact_match": true,
    "plants_sampled_as_reported_by_gwdd": "1",
    "published_aggregate_csv_data_record_1based": 1791,
    "original_paper_individually_inspected_for_this_species": false,
    "measurement_uncertainty": null,
    "uncertainty_note": "No individual uncertainty supplied; CIRAD paper discusses approximately 3 percent method-level air-dry SG uncertainty, not a per-record confidence interval and not final converted-basic uncertainty; decimal rounding is not measurement uncertainty",
    "baseline_identity_id": null,
    "new_identity_candidate": true,
    "repository_admitted": false,
    "v1_candidate_key": "wood-species-a0845ac865e85bf2",
    "candidate_key": "wood-wfo-0000510976",
    "source_taxonomic_reference": "https://padme.rbge.org.uk/wfo/wfo-0000510976",
    "accepted_wfo_taxon_id": "wfo-0000510976",
    "accepted_full_scientific_name": "Abies alba Mill.",
    "accepted_name": "Abies alba",
    "accepted_authority": "Mill.",
    "gwdd_resolved_species_preserved": "Abies alba",
    "gwdd_accepted_authority_preserved": "Mill.",
    "original_full_scientific_name": "Abies alba Mill.",
    "original_wfo_name_records": [
      {
        "taxon_id": "wfo-0000510976",
        "scientific_name": "Abies alba",
        "authorship": "Mill.",
        "rank": "species",
        "status": "Accepted"
      }
    ],
    "source_to_accepted_wfo_chains": [
      {
        "source_name_wfo_id": "wfo-0000510976",
        "wfo_chain_ids": [
          "wfo-0000510976"
        ],
        "accepted_terminal_wfo_id": "wfo-0000510976",
        "error": null
      }
    ],
    "taxonomy_mapping_method": "strict_original_and_target_full_name_authority_match_period_whitespace_only",
    "taxonomic_backbone": {
      "doi": "10.5281/zenodo.8079052",
      "version": "2023-06",
      "archive_sha256": "854bf0ab8e1b836b79137d56481c536f1b0779214538ef23e56c4dc61849d8db",
      "archive_member": "classification.csv",
      "accepted_record_1based": 504931,
      "accepted_physical_line_start": 504932,
      "accepted_physical_line_end": 504932
    },
    "scientific_assessment_status": "source_chain_supported_pending_independent_v2_review",
    "conversion_method": {
      "coefficient": "0.8281316",
      "coefficient_source": "GWDD v2.1 columns dictionary",
      "calibration_citation_doi": "10.1002/ajb2.1175",
      "method_type": "empirically_calibrated_conversion_not_GWDD_hierarchical_species_estimate",
      "source_water_density_convention_g_cm3": "1",
      "nominal_input_moisture_percent": "12",
      "measured_specimen_moisture_percent": null
    },
    "unknown_specimen_conditions": {
      "tissue_subtype": null,
      "sample_anatomical_location": null,
      "orientation": null,
      "exact_test_temperature": null,
      "exact_moisture": null
    },
    "v1_release_status": "HELD_SUPERSEDED_FOR_CANDIDATE_SELECTION",
    "dossier_version": 2,
    "v1_mechanically_eligible_source_record_count": 2
  },
  "deposited_locator": {
    "row_number": 7854,
    "line_start": 7855,
    "line_end": 7855
  }
}
''')


def batch():
    material, observation = wood._generic_records(deepcopy(FIXTURE))
    return {"schema_version": "1.0.0", "adapter_id": wood.ADAPTER_ID,
            "batch_id": "reviewed_wood_single_record_test_only",
            "registry": wood.source_registry(), "materials": [material],
            "observations": [observation], "exclusions": []}


def stage(value=None):
    return stage_batch(batch() if value is None else value, profiles=wood.reviewed_profiles())


def materialize(package):
    return wood.materialize_wood_records(package, expected_review_digest=stage(package["input"])["review_manifest_sha256"])


def admission(value=None):
    staged = stage(value)
    digest = staged["review_manifest_sha256"]
    approval = {"decision": "approve", "reviewer": "unit-test-only-no-production-admission",
                "review_manifest_sha256": digest,
                "approved_identity_keys": [row["identity_key"] for row in staged["materials"]]}
    return admit_batch(staged, approval, expected_review_digest=digest, profiles=wood.reviewed_profiles())


class ReviewedWoodAdapterTests(unittest.TestCase):
    def test_registered_profile_is_source_specific(self):
        profile, = wood.reviewed_profiles()
        self.assertEqual(profile.adapter_id, "gwdd_wood_v2")
        self.assertEqual(profile.registry_sha256, registry_digest(wood.source_registry()))
        self.assertEqual(profile.allowed_licenses, frozenset(("CC-BY-4.0", "CC0-1.0")))
        self.assertNotIn("CC-BY-SA-4.0", profile.allowed_licenses)

    def test_registry_is_detached(self):
        registry = wood.source_registry()
        registry["licenses"][0]["identifier"] = "changed"
        self.assertNotEqual(registry, wood.source_registry())

    def test_stage_has_zero_admissions(self):
        staged = stage()
        self.assertEqual(staged["manifest"]["counts"]["by_status"]["source_supported"], 1)
        self.assertEqual(staged["manifest"]["counts"]["by_status"]["admitted"], 0)
        self.assertEqual(staged["quarantine"], [])

    def test_full_runtime_contract_and_source_schema(self):
        tables = materialize(admission())
        validate_material_catalog(tables["materials"], tables["properties"], tables["sources"])
        try:
            import jsonschema
        except ImportError:
            return
        root = Path(__file__).resolve().parents[1]
        schema = json.loads((root / "schemas/sources.schema.json").read_text())
        jsonschema.Draft202012Validator(schema).validate(tables["sources"])

    def test_basis_convention_has_explicit_inspected_methods_source(self):
        tables = materialize(admission())
        self.assertEqual(len(tables["sources"]["records"]), 6)
        sources = {source["id"]: source for source in tables["sources"]["records"]}
        prop = tables["properties"]["records"][0]
        source_id = prop["derivation"]["formula"]["basis_convention_source_id"]
        self.assertEqual(source_id, wood.GWDD_METHODS)
        source = sources[source_id]
        self.assertEqual(source["doi"], "10.1111/nph.70860")
        self.assertIn(wood.GWDD_METHODS_PDF_SHA256, " ".join(source["claim_notes"]))
        self.assertIn("abbreviated", " ".join(source["claim_notes"]))
        for evidence in (prop["derivation"]["evidence"], prop["method_definition"]["evidence"]):
            linked = [row for row in evidence if row["source_id"] == source_id]
            self.assertEqual(len(linked), 1)
            self.assertIn("method", linked[0]["supports"])
            self.assertIn("classification", linked[0]["supports"])
            self.assertIn("Printed p.6 / PDF p.7", linked[0]["locator"])
        self.assertNotIn("Langbour", " ".join(sources[wood.WFO]["claim_notes"]))
        self.assertIn("34188a6c455ca8681a2c77faf105ab622fd9dc5c66e063b5dc9b4f0fe4a497a3",
                      " ".join(sources[wood.METHOD]["claim_notes"]))

    def test_preserves_values_strings_basis_and_nulls(self):
        tables = materialize(admission())
        prop = tables["properties"]["records"][0]
        d = prop["derivation"]
        self.assertEqual(prop["reported_value"]["number"], "0.38")
        self.assertEqual(d["input"]["number"], "0.46")
        self.assertEqual(d["input"]["value_text"], "0.46")
        self.assertEqual(d["input"]["unit_code"], "dimensionless")
        self.assertEqual(d["si_output"]["number"], "380")
        self.assertEqual(d["formula"]["coefficient"], "0.8281316")
        self.assertEqual(d["formula"]["nominal_conversion_moisture_percent"], "12")
        self.assertIsNone(d["formula"]["measured_specimen_moisture_percent"])
        self.assertIsNone(prop["uncertainty"])
        self.assertIsNone(prop["sample_count"]["value"])
        self.assertIsNone(d["counts"]["verified_independent_plants"])
        self.assertEqual(d["counts"]["v1_mechanically_eligible_source_record_count"], 2)
        self.assertNotIn("eligible_source_record_count", canonical_json_bytes(tables).decode().replace("v1_mechanically_eligible_source_record_count", ""))
        for value in prop["conditions"].values():
            self.assertEqual(value["status"], "not_reported_in_inspected_source")
        for name in ("tissue_subtype", "sample_anatomical_location", "orientation", "exact_moisture", "exact_test_temperature", "treatment", "collection_date", "measurement_date"):
            self.assertIsNone(d["specimen_scope"][name])

    def test_preserves_taxonomy_and_original_file_name(self):
        tables = materialize(admission())
        taxon = tables["materials"]["identities"][0]["canonical_taxon"]
        self.assertEqual(taxon["original_full_name"], FIXTURE["reviewed_candidate"]["original_full_scientific_name"])
        self.assertEqual(taxon["source_to_accepted_chains"], FIXTURE["reviewed_candidate"]["source_to_accepted_wfo_chains"])
        d = tables["properties"]["records"][0]["derivation"]
        self.assertEqual(d["provenance"]["original"]["file_name"], "2021- 06 Cirad wood collection index.csv")
        self.assertEqual(d["provenance"]["original"]["data_record_1based"], 2803)
        self.assertEqual(d["provenance"]["original"]["physical_line_start"], 2804)
        self.assertEqual(d["provenance"]["deposited"]["record_id"], "10084")
        self.assertEqual(d["provenance"]["reviewed_batch_sha256"], wood.REVIEWED_BATCH_SHA256)
        self.assertIn("Sébastien, P.", d["provenance"]["original_citation"])
        self.assertIn("Paradis, Sébastien", d["provenance"]["normalized_citation"])

    def test_all_baseline_exclusions_and_cork_are_distinct(self):
        identities = [{"id": row["baseline_identity_id"], "category": "natural"} for row in wood._data()["baseline_crosswalk"]]
        rows = wood.baseline_rows({"identities": identities})
        self.assertEqual(len(rows), 6)
        keys = {row["identity_key"] for row in rows}
        self.assertIn(wood._identity_key("wfo-0000515026"), keys)
        self.assertIn(wood._identity_key("wfo-0000293006"), keys)
        self.assertIn(wood._identity_key("wfo-0000482639"), keys)
        self.assertIn(wood._identity_key("wfo-0000890373"), keys)
        self.assertIn(wood._identity_key("wfo-0000873500"), keys)
        self.assertIn("catalog:mat_prasetia2024_qsuber_reproduction_cork", keys)
        self.assertNotIn(wood._identity_key("wfo-0000293451"), keys)

    def test_material_and_evidence_reordering_is_deterministic(self):
        value = batch()
        value["materials"][0]["aliases"].reverse()
        for row in value["materials"] + value["observations"]:
            row["evidence"].reverse()
            for evidence in row["evidence"]:
                evidence["fields"].reverse()
        for table in value["registry"].values():
            table.reverse()
        self.assertEqual(canonical_json_bytes(stage()), canonical_json_bytes(stage(value)))

    def test_exact_duplicate_evidence_cannot_inflate_materialization(self):
        value = batch()
        value["materials"] *= 2
        value["observations"] *= 2
        tables = materialize(admission(value))
        self.assertEqual(len(tables["materials"]["identities"]), 1)
        self.assertEqual(len(tables["properties"]["records"]), 1)

    def test_candidate_numeric_scientific_and_identity_mutations_are_held(self):
        edits = {"density_g_cm3": "0.39", "density_kg_m3": "390", "conversion_factor": "0.828",
                 "original_value_as_reported": "NaN", "original_unit": "g/cm3", "mass_basis": "air_dry",
                 "property": "mass_density", "measurement_uncertainty": "0.03",
                 "measured_specimen_moisture_percent": "12", "accepted_wfo_taxon_id": "wfo-0000000000",
                 "original_full_scientific_name": "Acacia sieberiana DC.", "accepted_name": "Acacia terminalis",
                 "binomial": "Populus × tomentosa", "dossier_version": 1,
                 "selected_source_key": "PROSEA", "repository_admitted": True}
        for field, new_value in edits.items():
            with self.subTest(field=field):
                value = batch()
                value["observations"][0]["metadata"]["reviewed_candidate"][field] = new_value
                result = stage(value)
                self.assertEqual(result["materials"][0]["status"], "held")
                self.assertTrue(any(row["reason"] == "semantic_validation_failed" for row in result["quarantine"]))

    def test_relabelled_quantity_unit_value_and_status_are_held(self):
        for field, new_value in (("quantity", "mass_density"), ("unit", "kg/m^3"),
                                 ("value", "0.380"), ("evidence_kind", "published_experimental_reference"),
                                 ("status", "admitted"), ("state_key", "trunk")):
            with self.subTest(field=field):
                value = batch()
                value["observations"][0][field] = new_value
                self.assertEqual(stage(value)["materials"][0]["status"], "held")

    def test_missing_or_changed_lineage_and_rights_are_held(self):
        for change in ("locator", "rights", "file_hash", "original_chain", "nominal_to_measured"):
            with self.subTest(change=change):
                value = batch()
                if change == "locator":
                    value["observations"][0]["metadata"]["deposited_locator"]["line_start"] += 1
                elif change == "rights":
                    value["registry"]["licenses"][0]["identifier"] = "CC-BY-SA-4.0"
                elif change == "file_hash":
                    value["registry"]["files"][0]["sha256"] = "a" * 64
                elif change == "original_chain":
                    value["observations"][0]["metadata"]["reviewed_candidate"]["source_to_accepted_wfo_chains"] = []
                else:
                    value["observations"][0]["metadata"]["reviewed_candidate"]["unknown_specimen_conditions"]["exact_moisture"] = "12"
                self.assertEqual(stage(value)["materials"][0]["status"], "held")

    def test_unreviewed_and_spoofed_admissions_cannot_materialize(self):
        with self.assertRaises(IngestionError):
            wood.materialize_wood_records(stage(), expected_review_digest=stage()["review_manifest_sha256"])
        forged = admission()
        forged["observations"][0]["value"] = "0.5"
        with self.assertRaises(IngestionError):
            materialize(forged)

    def test_independently_supplied_materialization_digest_cannot_be_inferred(self):
        accepted = admission()
        with self.assertRaisesRegex(IngestionError, "independently approved digest"):
            wood.materialize_wood_records(accepted, expected_review_digest="0" * 64)

    def test_registry_hash_is_rechecked_after_cache_population(self):
        wood.reviewed_profiles()
        with tempfile.TemporaryDirectory() as directory:
            changed = Path(directory) / "registry.json"
            changed.write_text("{}")
            with patch.object(wood, "_DATA_PATH", changed):
                for action in (wood.reviewed_profiles, wood.source_registry,
                               lambda: wood.baseline_rows({"identities": []}),
                               lambda: wood.source_supported_preview(stage())):
                    with self.subTest(action=action), self.assertRaisesRegex(IngestionError, "registry bytes differ"):
                        action()

    def test_preview_never_reports_admission(self):
        preview = wood.source_supported_preview(stage())
        self.assertEqual(preview["repository_admitted"], 0)
        self.assertEqual(preview["status"], "source_supported_preview_not_admitted")
        self.assertEqual(len(preview["tables"]["materials"]["identities"]), 1)

    def test_manifest_and_review_bytes_are_not_trusted_by_filename(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "manifest-v2.json").write_text('{"files":[]}')
            with self.assertRaisesRegex(IngestionError, "SHA-256 differs"):
                wood.verify_reviewed_dossier(root, root)

    def test_csv_preserves_unrelated_invalid_encoding_without_replacement(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "source.csv"
            path.write_bytes(b'id;value;unrelated\n1;0.460;\xff\n')
            rows = wood._selected_csv(path, {"1"}, "id", ";")
            self.assertEqual(rows["1"][0]["value"], "0.460")
            self.assertEqual(rows["1"][0]["unrelated"], "\udcff")
            self.assertEqual(rows["1"][1], {"row_number": 1, "line_start": 2, "line_end": 2})

    @unittest.skipUnless(os.environ.get("WOOD_REVIEW_DOSSIER"), "external frozen source-cache integration is opt-in")
    def test_full_external_dossier_source_support_without_admission(self):
        dossier = Path(os.environ["WOOD_REVIEW_DOSSIER"])
        value = wood.build_wood_batch(dossier, dossier.parent / "wood-independent-review/v2")
        result = stage(value)
        self.assertEqual(result["manifest"]["counts"]["by_status"]["source_supported"], 1000)
        self.assertEqual(result["manifest"]["counts"]["by_status"]["admitted"], 0)
        self.assertEqual(result["quarantine"], [])
        palm = next(row for row in value["observations"] if row["metadata"]["reviewed_candidate"]["accepted_name"] == "Cocos nucifera")
        identity, state, prop = wood._runtime_records(palm["metadata"])
        self.assertIsNone(prop["derivation"]["specimen_scope"]["tissue_subtype"])
        self.assertIsNone(prop["derivation"]["specimen_scope"]["sample_anatomical_location"])


if __name__ == "__main__":
    unittest.main()
