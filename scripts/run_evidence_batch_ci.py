#!/usr/bin/env python3
"""Bounded evidence compiler, recovery and installed PA12 checks.

Test IDs are frozen explicitly before publication. Six local wheels are checked
against source bytes, installed without an index in a fresh environment, then
tested through the selected installed API and preservation boundaries. This
entry point never invokes an earlier full core or platform suite.
"""
import argparse
from collections import Counter
import importlib
import inspect
import json
from pathlib import Path
import sys
import tempfile
import unittest
import venv

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
from check_evidence_batch_scope import validate_scope
from run_polymer_composites_ci import (
    PACKAGES, clean_env, install_offline_guard, installed_origins,
    require, run, sha256, test_ids, verify_wheels,
)

# These are exact case inventories, not directory discovery or test minima.
# Owners froze these case IDs before the final local validation phase.
TEST_GROUPS = {
    "core": ("tests", (
        "test_formulation_packet_integration.FormulationPacketIntegrationTests.test_linked_grade_designation_and_alias_cannot_create_another_identity",
        'test_formulation_packet_preparation.FormulationPacketPreparationTests.test_context_collisions_and_wrong_row_ownership_fail_atomically',
        'test_formulation_packet_preparation.FormulationPacketPreparationTests.test_frozen_four_formulation_replay_preserves_all_facts_and_zero_increment',
        'test_formulation_packet_preparation.FormulationPacketPreparationTests.test_missing_crosswalk_review_and_license_remain_pending_without_upgrade',
        'test_formulation_packet_preparation.FormulationPacketPreparationTests.test_missing_properties_wrong_units_and_untraceable_provenance_are_rejected',
        'test_formulation_packet_preparation.FormulationPacketPreparationTests.test_output_path_and_existing_artifact_refusals_preserve_input_bytes',
        'test_formulation_packet_preparation.FormulationPacketPreparationTests.test_prepared_packet_validation_recompiles_input_instead_of_trusting_report',
        'test_formulation_packet_preparation.FormulationPacketPreparationTests.test_reidentified_designation_or_alias_cannot_evade_existing_identity',
        'test_formulation_packet_preparation.FormulationPacketPreparationTests.test_repeated_write_and_cli_keep_identical_bytes_and_mtime',
        'test_formulation_packet_preparation.FormulationPacketPreparationTests.test_shared_contexts_and_explicit_grade_multiple_states_do_not_multiply_identity',
        'test_formulation_packet_preparation.FormulationPacketPreparationTests.test_source_and_baseline_pins_reject_changed_inputs_before_writing',
        'test_formulation_packet_preparation.FormulationPacketPreparationTests.test_strict_json_rejects_duplicate_nonfinite_and_overflow_values',
        'test_formulation_packet_integration.FormulationPacketIntegrationTests.test_closed_manifest_binding_hash_and_no_adjustment_contract',
        'test_formulation_packet_integration.FormulationPacketIntegrationTests.test_cross_batch_source_designation_collision_is_atomic',
        'test_formulation_packet_integration.FormulationPacketIntegrationTests.test_missing_crosswalk_is_reportable_but_not_integrable',
        'test_formulation_packet_integration.FormulationPacketIntegrationTests.test_rehashed_tampering_cannot_replace_full_packet_replay',
        'test_formulation_packet_integration.FormulationPacketIntegrationTests.test_single_packet_replays_then_integrates_idempotently',
        'test_formulation_packet_integration.FormulationPacketIntegrationTests.test_v1_still_accepts_its_original_four_descriptors_and_encoding',
        'test_pa12_source_family_packet.PA12SourceFamilyPacketTests.test_article_attribution_rights_and_asset_boundary',
        'test_pa12_source_family_packet.PA12SourceFamilyPacketTests.test_compiler_packet_preserves_explicit_input_and_zero_admission',
        'test_pa12_source_family_packet.PA12SourceFamilyPacketTests.test_disputed_modulus_and_other_materials_remain_excluded',
        'test_pa12_source_family_packet.PA12SourceFamilyPacketTests.test_one_pa12_representative_and_source_designated_grade',
        'test_pa12_source_family_packet.PA12SourceFamilyPacketTests.test_selected_state_and_method_preserve_unknown_conditions',
        'test_pa12_source_family_packet.PA12SourceFamilyPacketTests.test_table7_strength_statistics_and_count_match_fixture',
        'test_evidence_batch_data_preservation.EvidenceBatchDataPreservationTests.test_complete_predecessor_bytes_are_recovered_without_mutating_input',
        'test_evidence_batch_data_preservation.EvidenceBatchDataPreservationTests.test_one_new_polymer_has_a_property_and_no_other_category_increment',
        'test_evidence_batch_data_preservation.EvidenceBatchDataPreservationTests.test_partial_duplicate_or_changed_additions_are_rejected',
        'test_evidence_batch_data_preservation.EvidenceBatchDataPreservationTests.test_readme_and_resource_bridges_reject_unknown_byte_images',
        'test_evidence_batch_data_preservation.EvidenceBatchDataPreservationTests.test_unrelated_rows_metadata_and_order_cannot_be_hidden_by_recovery',
        'test_evidence_batch_data_preservation.EvidenceBatchDataPreservationTests.test_v2_packet_replay_matches_runtime_and_repeat_has_no_increment',
        'test_evidence_batch_workflow_preservation.EvidenceBatchWorkflowPreservationTests.test_changed_bytes_paths_types_and_before_images_fail_closed',
        'test_evidence_batch_workflow_preservation.EvidenceBatchWorkflowPreservationTests.test_helper_ledger_and_all_previous_ledgers_are_pinned',
        'test_evidence_batch_workflow_preservation.EvidenceBatchWorkflowPreservationTests.test_ledger_drift_and_duplicate_keys_fail_without_mutating_original',
        'test_evidence_batch_workflow_preservation.EvidenceBatchWorkflowPreservationTests.test_old_jobs_and_previous_experiment_are_preserved_exactly',
        'test_evidence_batch_workflow_preservation.EvidenceBatchWorkflowPreservationTests.test_scope_rejects_unknown_paths_deletions_and_nonfiles',
        'test_evidence_batch_workflow_preservation.EvidenceBatchWorkflowPreservationTests.test_three_complete_predecessor_files_round_trip_exactly',
        'test_evidence_batch_workflow_preservation.EvidenceBatchWorkflowPreservationTests.test_unquoted_yaml_scalars_and_nonlocal_wheel_arguments_are_rejected',
        'test_material_class_counts_preservation.MaterialClassCountsPreservationTests.test_all_old_ledgers_remain_unchanged_and_new_ledger_mutations_fail',
        'test_material_class_counts_preservation.MaterialClassCountsPreservationTests.test_changed_bytes_paths_types_and_before_images_cannot_use_the_bridge',
        'test_material_class_counts_preservation.MaterialClassCountsPreservationTests.test_five_exact_predecessors_round_trip_including_ci_and_helpers',
        'test_material_class_counts_preservation.MaterialClassCountsPreservationTests.test_helper_ledger_and_three_snapshot_resources_are_pinned',
        'test_material_class_counts_preservation.MaterialClassCountsPreservationTests.test_readme_exact_recovery_and_all_seven_original_material_chains',
        'test_material_class_counts_preservation.MaterialClassCountsPreservationTests.test_snapshot_is_fixed_while_marked_totals_follow_an_append_rehearsal',
        'test_material_class_counts_preservation.MaterialClassCountsPreservationTests.test_snapshot_sentence_matches_actual_core_classes_and_only_natural_reaches_goal',
        'test_material_class_counts_preservation.MaterialClassCountsPreservationTests.test_wrong_class_counts_dates_duplicate_sentences_and_prose_fail_closed',
        'test_polymer_composites_increment.PolymerCompositesIncrementTests.test_exact_parent_recovery_retains_every_old_object_and_source_byte',
        'test_polymer_composites_increment.PolymerCompositesIncrementTests.test_actual_packet_replay_produces_current_bytes_and_no_repeat_increment',
        'test_material_bulk_preservation.MaterialBulkPreservationTests.test_all_402_predecessor_files_round_trip_exactly',
    )),
    "query": ("experimental/platform/query-service/catalog-tests", (
        "test_catalog_baseline.IntegratedBaselineTests.test_installed_package_matches_exact_new_anchor",
        "test_catalog_baseline.IntegratedBaselineTests.test_old_database_anchor_is_rejected_without_migration",
        "test_catalog_baseline.IntegratedBaselineTests.test_changed_core_resource_fails_even_with_unchanged_identity_count",
        "test_formal_project_catalog.FormalAPI.test_counts_and_no_legacy_rewrite",
        "test_formal_project_catalog.FormalAPI.test_full_records_and_partitions",
        "test_family_relationships.FamilyRelationshipTests.test_coverage_exact_and_no_count_inflation",
        "test_local_catalog.CatalogAPI.test_pa12_source_family_single_identity_resolution",
        "test_baseline_compatibility.BaselineCompatibility.test_evidence_batch_parent_manifest_and_catalog_recovery_remain_exact",
        "test_baseline_compatibility.BaselineCompatibility.test_a592_complete_manifest_and_catalog_recovery_remain_exact",
    )),
    "formal": ("formal-catalog/tests", (
        "test_formal_project_core.FormalProjectCatalog.test_exact_counts_and_categories",
        "test_formal_project_core.FormalProjectCatalog.test_full_legacy_identity_parity",
        "test_formal_project_core.FormalProjectCatalog.test_pin_drift_fail_closed",
    )),
    "ingestion": ("experimental/platform/ingestion", (
        "test_review_boundary.ReviewBoundaryTests.test_formal_and_example_counts_remain_separate",
        "test_nomad_incremental.IncrementalTests.test_evidence_batch_predecessor_scope_stays_read_only_without_migration",
        "test_formal_overlap_audit.FormalOverlapAuditTests.test_primary_partition_and_overlapping_dimensions_are_distinct",
        "test_formal_overlap_audit.FormalOverlapAuditTests.test_alexandria_formula_exposes_three_distinct_qualified_relations",
    )),
}
NEW_IDS = {
    "identity": "mat_zakrecki2025_pa12_pa2200",
    "grade": "grade_zakrecki2025_eos_pa2200",
    "state": "state_zakrecki2025_pa2200_sls_dyed_reference",
    "property": "refprop_zakrecki2025_pa2200_sls_reference_tensile_strength",
    "source": "zakrecki_cieslik_2025_pa12_ageing",
}
PRIMARY_COUNTS = {"natural": 1010, "metal": 22, "inorganic": 26, "polymer": 16, "composite": 10}


class ExactResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.started_ids = []
        self.passed_ids = []

    def startTest(self, test):
        self.started_ids.append(test.id())
        super().startTest(test)

    def addSuccess(self, test):
        self.passed_ids.append(test.id())
        super().addSuccess(test)


def run_group(name):
    install_offline_guard()
    relative, expected = TEST_GROUPS[name]
    require(expected and len(expected) == len(set(expected)), "Exact test inventory is empty or duplicated: " + name)
    if name == "core":
        sys.path.insert(0, str(ROOT))
    else:
        require(sys.prefix != sys.base_prefix, "Selected package checks require a fresh installation")
        require(str(ROOT) not in sys.path, "Checkout root must not shadow installed packages")
        installed_origins()
    directory = ROOT / relative
    sys.path.insert(0, str(directory))
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromNames(list(expected))
    require(not loader.errors, "Selected test loading failed: " + "\n".join(loader.errors))
    discovered = list(test_ids(suite))
    require(discovered == list(expected), "Selected test discovery differs from the fixed inventory")
    print("DISCOVERED " + json.dumps({"group": name, "test_ids": discovered}, sort_keys=True), flush=True)
    result = unittest.TextTestRunner(verbosity=2, resultclass=ExactResult, failfast=False).run(suite)
    require(result.testsRun == len(expected) and result.started_ids == discovered
            and result.passed_ids == discovered and result.wasSuccessful()
            and not result.skipped and not result.expectedFailures and not result.unexpectedSuccesses,
            name + ": discovered/started/passed IDs differ, or failures/errors/skips occurred")
    if name != "core":
        installed_origins()
    print("TARGETED " + json.dumps({"group": name, "passed": result.testsRun, "skipped": 0,
                                    "failed": 0, "errors": 0, "test_ids": discovered}, sort_keys=True), flush=True)


def installation_payload():
    graphs = {name: json.loads((ROOT / "materials_boundaries/data" / filename).read_bytes())
              for name, filename in (("materials", "materials.json"),
                                     ("properties", "reference_properties.json"), ("sources", "sources.json"))}
    tables = {"identity": graphs["materials"]["identities"], "grade": graphs["materials"]["grades"],
              "state": graphs["materials"]["records"], "property": graphs["properties"]["records"],
              "source": graphs["sources"]["records"]}
    selected = {}
    for kind, identifier in NEW_IDS.items():
        rows = [row for row in tables[kind] if row["id"] == identifier]
        require(len(rows) == 1, "Expected one new PA12 record: " + identifier)
        selected[kind] = rows[0]
    require(dict(Counter(row["category"] for row in tables["identity"])) == PRIMARY_COUNTS,
            "Source tree primary category counts differ from this experiment")
    require({kind: len(rows) for kind, rows in tables.items()} ==
            {"identity": 1084, "grade": 21, "state": 1084, "property": 1084, "source": 116},
            "Source tree exact graph counts differ from this experiment")
    return {"new_ids": NEW_IDS, "selected": selected, "primary_counts": PRIMARY_COUNTS,
            "packages": [package for _, _, package in PACKAGES],
            "resource_hashes": {name: sha256((ROOT / "materials_boundaries/data" / name).read_bytes()).hexdigest()
                                for name in ("materials.json", "reference_properties.json", "sources.json")}}


INSTALLED_SMOKE = r'''
from collections import Counter
from contextlib import redirect_stdout
from hashlib import sha256
from importlib.resources import files
import importlib
import io
import json
from pathlib import Path
import sys

def require(condition, message):
    if not condition:
        raise RuntimeError(message)

expected = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
for name in expected["packages"]:
    package = importlib.import_module(name)
    require(Path(package.__file__).resolve().is_relative_to(Path(sys.prefix).resolve()),
            "Checkout package imported: " + name)
from materials_boundaries.catalog import read_catalog, query_catalog
from materials_boundaries.cli import main
from materials_project_catalog.catalog import formal_project_catalog
from materials_query.computed_registry import baseline_digest

for name, digest in expected["resource_hashes"].items():
    require(sha256(files("materials_boundaries").joinpath("data", name).read_bytes()).hexdigest() == digest,
            "Installed catalog bytes differ: " + name)
materials, properties, sources = (read_catalog(name) for name in ("materials", "reference_properties", "sources"))
tables = {"identity": materials["identities"], "grade": materials["grades"], "state": materials["records"],
          "property": properties["records"], "source": sources["records"]}
require({kind: len(rows) for kind, rows in tables.items()} ==
        {"identity": 1084, "grade": 21, "state": 1084, "property": 1084, "source": 116}, "Installed graph counts changed")
require(dict(Counter(row["category"] for row in materials["identities"])) == expected["primary_counts"],
        "Installed primary categories changed")
for kind, identifier in expected["new_ids"].items():
    rows = [row for row in tables[kind] if row["id"] == identifier]
    require(rows == [expected["selected"][kind]], "Installed complete PA12 record differs: " + kind)
identity, grade, state, prop = (expected["selected"][name] for name in ("identity", "grade", "state", "property"))
require(identity["category"] == "polymer" and state["grade_id"] == grade["id"], "PA12 category/grade changed")
require((prop["reported_value"]["number"], prop["reported_value"]["unit_code"]) == ("43.72", "MPa"),
        "PA12 measured value changed")
require(prop["uncertainty"]["number"] == "1.03" and prop["sample_count"]["value"] == 6
        and prop["sample_count"]["relation"] == "exact"
        and prop["summary_statistic"] == "reported_mean"
        and prop["uncertainty_status"] == "reported_standard_deviation",
        "PA12 uncertainty or sample count changed")
require(prop["evaluation_support"] == "catalog_only" and not prop["universal_bound"] and not prop["engineering_allowable"]
        and not prop["verification"]["independent_scientific_review"] and not prop["verification"]["raw_data_reanalysis"],
        "PA12 reference gained scientific capabilities")
selected = query_catalog("reference-properties", record_id=prop["id"])
outputs = 0
for language in ("en", "zh", "ja", "de"):
    for flag in ("--json", "--text"):
        output = io.StringIO()
        with redirect_stdout(output):
            code = main(["catalog", "reference-properties", "--id", prop["id"], "--lang", language, flag])
        text = output.getvalue()
        require(code == 0 and "[missing:" not in text, "Installed PA12 CLI failed")
        if flag == "--json":
            require(json.loads(text) == selected, "Installed PA12 JSON depends on language")
        else:
            require("43.72" in text and prop["uncertainty_note"] in text, "Installed PA12 value/caveat missing")
        outputs += 1
formal = formal_project_catalog()
require(formal["counts"] == {"formal_project_admission_count": 1108, "legacy_source_qualified_identity_count": 1084,
        "reviewed_computed_composition_count": 24,
        "categories": {"natural": 1010, "metal": 34, "inorganic": 38, "polymer": 16, "composite": 10}},
        "Installed formal boundary differs")
require(len([row for row in formal["records"] if row["partition"] == "legacy-source-qualified"
             and row["identity"]["id"] == identity["id"]]) == 1, "PA12 contributes more than one identity")
anchor = baseline_digest()
require(isinstance(anchor, str) and len(anchor) == 64, "Installed query anchor failed")
print(json.dumps({"new_identities": 1, "new_grades": 1, "new_states": 1, "new_properties": 1, "new_sources": 1,
                  "selected_cli_outputs": outputs, "formal_count": 1108, "reviewed_computed": 24,
                  "core_count": 1084, "query_baseline": anchor, "fresh_install": True,
                  "scope": "Selected installed PA12 and exact package checks; not exhaustive regression."}))
'''


def check_installed(wheel_dir, dependency_dir):
    wheels = verify_wheels(wheel_dir)
    require(dependency_dir.is_dir() and any(dependency_dir.glob("*.whl")), "Offline dependency wheels are missing")
    env = clean_env()
    with tempfile.TemporaryDirectory(prefix="evidence-batch-installed-") as temporary:
        work = Path(temporary)
        runtime = work / "runtime"
        venv.EnvBuilder(with_pip=True, system_site_packages=False).create(runtime)
        python = runtime / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
        run([python, "-I", "-m", "pip", "--isolated", "install", "--no-index", "--no-deps", "--find-links", dependency_dir,
             "-r", ROOT / "experimental/platform/requirements-lock.txt",
             "-r", ROOT / "experimental/platform/ci/projection-requirements.txt"], cwd=work, env=env)
        run([python, "-I", "-m", "pip", "--isolated", "install", "--no-index", "--no-deps", *wheels], cwd=work, env=env)
        run([python, "-I", "-m", "pip", "check"], cwd=work, env=env)
        expected = work / "expected.json"
        expected.write_text(json.dumps(installation_payload()), encoding="utf-8")
        smoke = work / "installed_smoke.py"
        smoke.write_text(inspect.getsource(install_offline_guard) + "\ninstall_offline_guard()\n" + INSTALLED_SMOKE,
                         encoding="utf-8")
        run([python, "-I", smoke, expected], cwd=work, env=env)
        for group in TEST_GROUPS:
            if group != "core":
                run([python, "-B", Path(__file__).resolve(), "--installed-group", group], cwd=work, env=env)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument("--validate-scope", action="store_true")
    actions.add_argument("--test", action="store_true")
    actions.add_argument("--wheel-dir", type=Path)
    actions.add_argument("--installed-group", choices=tuple(name for name in TEST_GROUPS if name != "core"))
    parser.add_argument("--dependency-dir", type=Path)
    args = parser.parse_args()
    if args.installed_group:
        run_group(args.installed_group)
        return
    validate_scope()
    if args.test:
        run_group("core")
    elif args.wheel_dir:
        require(args.dependency_dir is not None, "--wheel-dir requires --dependency-dir")
        check_installed(args.wheel_dir.resolve(), args.dependency_dir.resolve())
    elif args.dependency_dir:
        parser.error("--dependency-dir requires --wheel-dir")


if __name__ == "__main__":
    main()
