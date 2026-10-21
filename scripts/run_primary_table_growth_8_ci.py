#!/usr/bin/env python3
"""Validate the bounded eighth primary-table growth branch.

Reuse the existing offline execution and six-package verification primitives.
Only frozen case IDs run; earlier full suites are not invoked by this entry point.
"""
import argparse
from collections import Counter
import inspect
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import venv

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
from run_primary_table_growth_7_ci import (
    BRANCH_REF as PREVIOUS_BRANCH_REF, BUILD_COMMAND,
    FULL_JOB_IF as PREVIOUS_FULL_JOB_IF, TARGETED_JOB as PREVIOUS_TARGETED_JOB,
    changed_paths, validate_targeted_run_scalars, validate_wheel_command,
)
from run_evidence_batch_ci import (
    ExactResult, PACKAGES, clean_env, install_offline_guard, installed_origins,
    require, run, sha256, test_ids, verify_wheels,
)

BASE_COMMIT = '5e8d63dc9b7832cab893a5d849346d42b02e3c85'
BRANCH_REF = "refs/heads/experiment/primary-table-growth-8-20261021"
FULL_JOB_IF = PREVIOUS_FULL_JOB_IF.replace("') }}\n", "' && github.ref != '" + BRANCH_REF + "') }}\n")
TARGETED_JOB = (PREVIOUS_TARGETED_JOB
                .replace("  primary-table-growth-7-targeted:\n", "  primary-table-growth-8-targeted:\n")
                .replace(PREVIOUS_BRANCH_REF, BRANCH_REF)
                .replace("run_primary_table_growth_7_ci.py", "run_primary_table_growth_8_ci.py"))

# The owner-approved inventory is frozen after packet, data and history owners finish.
APPROVED_FILES = frozenset({
    '.github/workflows/ci.yml',
    'README.md',
    'THIRD_PARTY_NOTICES.md',
    'experimental/material-batches/zenodo-8089569-filaments-20261021/README.md',
    'experimental/material-batches/zenodo-8089569-filaments-20261021/integration-report.json',
    'experimental/material-batches/zenodo-8089569-filaments-20261021/integration.json',
    'experimental/material-batches/zenodo-8089569-filaments-20261021/packet-spec.json',
    'experimental/material-batches/zenodo-8089569-filaments-20261021/preparation-receipt.json',
    'experimental/material-batches/zenodo-8089569-filaments-20261021/prepared-packet.json',
    'experimental/material-batches/zenodo-8089569-filaments-20261021/source-review.json',
    'experimental/platform/ci/required_test_ids.json',
    'experimental/platform/ingestion/FORMAL_OVERLAP_AUDIT.md',
    'experimental/platform/ingestion/FORMAL_REVIEW_GAPS.md',
    'experimental/platform/ingestion/INCREMENTAL.md',
    'experimental/platform/ingestion/README.md',
    'experimental/platform/ingestion/nomad_review_boundary.py',
    'experimental/platform/ingestion/test_formal_overlap_audit.py',
    'experimental/platform/ingestion/test_formal_review_gaps.py',
    'experimental/platform/ingestion/test_incremental_independent.py',
    'experimental/platform/ingestion/test_nomad_evidence_compare.py',
    'experimental/platform/ingestion/test_nomad_incremental.py',
    'experimental/platform/ingestion/test_review_boundary.py',
    'experimental/platform/query-service/README.md',
    'experimental/platform/query-service/catalog-tests/test_baseline_compatibility.py',
    'experimental/platform/query-service/catalog-tests/test_catalog_baseline.py',
    'experimental/platform/query-service/catalog-tests/test_combined_admission_boundary.py',
    'experimental/platform/query-service/catalog-tests/test_computed_recovery.py',
    'experimental/platform/query-service/catalog-tests/test_computed_v2_second_tranche.py',
    'experimental/platform/query-service/catalog-tests/test_computed_v2_tranche.py',
    'experimental/platform/query-service/catalog-tests/test_family_relationships.py',
    'experimental/platform/query-service/catalog-tests/test_formal_project_catalog.py',
    'experimental/platform/query-service/catalog-tests/test_local_catalog.py',
    'experimental/platform/query-service/materials_query/computed_registry.py',
    'experimental/platform/query-service/materials_query/pins/legacy_baseline.json',
    'experimental/platform/relationships/test_hbn_relationship_projection.py',
    'formal-catalog/README.md',
    'formal-catalog/materials_project_catalog/catalog.py',
    'formal-catalog/tests/test_formal_project_core.py',
    'materials_boundaries/data/materials.json',
    'materials_boundaries/data/reference_properties.json',
    'materials_boundaries/data/sources.json',
    'scripts/extract_curated_filament_cells.py',
    'scripts/prepare_formulation_packet.py',
    'scripts/run_primary_table_growth_8_ci.py',
    'tests/fixtures/primary_table_growth_8_data_20261021.json',
    'tests/fixtures/primary_table_growth_8_files_20261021.json',
    'tests/material_append_successors.py',
    'tests/test_curated_filament_adapter.py',
    'tests/test_primary_table_growth_8_ci.py',
    'tests/test_primary_table_growth_8_preservation.py',
})

# Nonempty exact inventories are required before any selected phase can run.
TEST_GROUPS = {'core': ('tests', ('test_primary_table_growth_8_preservation.PrimaryTableGrowth8PreservationTests.test_qualified_filaments_keep_measured_properties_and_source_unknowns', 'test_primary_table_growth_8_preservation.PrimaryTableGrowth8PreservationTests.test_exact_5e8_recovery_rejects_partial_duplicate_unit_and_source_drift', 'test_primary_table_growth_8_preservation.PrimaryTableGrowth8PreservationTests.test_compiler_and_integrator_replay_preserve_immutable_artifacts', 'test_primary_table_growth_8_preservation.PrimaryTableGrowth8PreservationTests.test_selected_catalog_bytes_and_legacy_chain_remain_exact', 'test_primary_table_growth_8_preservation.PrimaryTableGrowth8PreservationTests.test_finite_files_and_registry_selection_keep_old_pins', 'test_primary_table_growth_8_ci.PrimaryTableGrowth8CITests.test_previous_jobs_keep_every_step_and_only_new_branch_is_gated', 'test_primary_table_growth_8_ci.PrimaryTableGrowth8CITests.test_scope_rejects_unlisted_paths_deleted_files_and_nonfiles', 'test_primary_table_growth_8_ci.PrimaryTableGrowth8CITests.test_ci_requires_exact_event_branch_sha_and_clean_checkout', 'test_primary_table_growth_8_ci.PrimaryTableGrowth8CITests.test_ambiguous_yaml_scalars_and_index_package_builds_fail', 'test_primary_table_growth_8_ci.PrimaryTableGrowth8CITests.test_unknown_predecessor_workflow_shapes_are_rejected', 'test_primary_table_growth_7_preservation.PrimaryTableGrowth7PreservationTests.test_selected_catalog_bytes_and_legacy_chain_remain_exact', 'test_primary_table_growth_7_ci.PrimaryTableGrowth7CITests.test_previous_jobs_keep_every_step_and_only_new_branch_is_gated', 'test_curated_filament_adapter.CuratedFilamentAdapterTests.test_frozen_classification_sources_only_support_reviewed_identities', 'test_curated_filament_adapter.CuratedFilamentAdapterTests.test_frozen_classification_sources_reject_rewrites_and_promotions', 'test_curated_filament_adapter.CuratedFilamentAdapterTests.test_measured_columns_exclude_iso_reference_and_print_states', 'test_curated_filament_adapter.CuratedFilamentAdapterTests.test_blanks_zero_and_formula_values_fail_closed', 'test_curated_filament_adapter.CuratedFilamentAdapterTests.test_exact_join_rejects_missing_duplicate_or_state_keys', 'test_curated_filament_adapter.CuratedFilamentAdapterTests.test_sparse_replay_is_deterministic_and_immutable', 'test_curated_filament_adapter.CuratedFilamentAdapterTests.test_xlsx_reader_keeps_numeric_lexemes_and_resolves_shared_strings', 'test_formulation_packet_preparation.FormulationPacketPreparationTests.test_missing_crosswalk_review_and_license_remain_pending_without_upgrade', 'test_formulation_packet_preparation.FormulationPacketPreparationTests.test_shared_contexts_and_explicit_grade_multiple_states_do_not_multiply_identity', 'test_formulation_packet_preparation.FormulationPacketPreparationTests.test_reidentified_designation_or_alias_cannot_evade_existing_identity', 'test_formulation_packet_integration.FormulationPacketIntegrationTests.test_cross_batch_source_designation_collision_is_atomic')), 'query': ('experimental/platform/query-service/catalog-tests', ('test_catalog_baseline.IntegratedBaselineTests.test_installed_package_matches_exact_new_anchor', 'test_catalog_baseline.IntegratedBaselineTests.test_old_database_anchor_is_rejected_without_migration', 'test_catalog_baseline.IntegratedBaselineTests.test_changed_core_resource_fails_even_with_unchanged_identity_count', 'test_baseline_compatibility.BaselineCompatibility.test_filament_batch_parent_manifest_and_catalog_recovery_remain_exact', 'test_baseline_compatibility.BaselineCompatibility.test_filament_batch_parent_database_rejected_without_migration', 'test_baseline_compatibility.BaselineCompatibility.test_outokumpu_batch_parent_manifest_and_catalog_recovery_remain_exact', 'test_local_catalog.CatalogAPI.test_02_metadata_counts_and_versions', 'test_local_catalog.CatalogAPI.test_filament_measured_reference_resolutions', 'test_family_relationships.FamilyRelationshipTests.test_coverage_exact_and_no_count_inflation', 'test_formal_project_catalog.FormalAPI.test_counts_and_no_legacy_rewrite', 'test_formal_project_catalog.FormalAPI.test_drift_disables_only_formal', 'test_combined_admission_boundary.CombinedAdmissionBoundary.test_second_tranche_admission_does_not_change_formal_counts_or_pins', 'test_computed_recovery.RegistryTests.test_atomic_held_and_replay')), 'formal': ('formal-catalog/tests', ('test_formal_project_core.FormalProjectCatalog.test_exact_counts_and_categories', 'test_formal_project_core.FormalProjectCatalog.test_full_legacy_identity_parity', 'test_formal_project_core.FormalProjectCatalog.test_pin_drift_fail_closed')), 'ingestion': ('experimental/platform/ingestion', ('test_review_boundary.ReviewBoundaryTests.test_formal_and_example_counts_remain_separate', 'test_review_boundary.ReviewBoundaryTests.test_boundary_fails_closed_on_changed_bytes', 'test_nomad_incremental.IncrementalTests.test_filament_predecessor_scope_stays_read_only_without_migration', 'test_nomad_incremental.IncrementalTests.test_new_store_requires_exact_current_catalog_scope_before_creation', 'test_incremental_independent.IndependentIncrementalTests.test_real_boundary_blocks_remapped_entries_without_promoting_examples', 'test_formal_overlap_audit.FormalOverlapAuditTests.test_inventory_covers_only_all_1081_frozen_formal_records', 'test_formal_overlap_audit.FormalOverlapAuditTests.test_primary_partition_and_overlapping_dimensions_are_distinct')), 'relationships': ('experimental/platform/relationships', ('test_hbn_relationship_projection.HBNRelationshipProjectionTests.test_actual_counts_are_separate_from_proposed_graph',))}

SOURCE_ID = "aniskevich_bulderberga_2023_polymer_mechanical_characterisation"
PACKET_PATH = 'experimental/material-batches/zenodo-8089569-filaments-20261021/prepared-packet.json'
PACKET_SHA256 = 'aaa94bd1f752e00f37268f8b786326dcb98011648985f8bc77cb92362f4c57e8'
DELTA_COUNTS = {'identity': 8, 'grade': 0, 'state': 8, 'property': 16, 'source': 4}
IDENTITY_CATEGORIES = {'mat_aniskevich_2023_ultimaker_pc': 'polymer', 'mat_aniskevich_2023_ultimaker_pp': 'polymer', 'mat_aniskevich_2023_ultimaker_tpu95a': 'polymer', 'mat_aniskevich_2023_protopasta_conductive_pla': 'composite', 'mat_aniskevich_2023_kimya_abs_esd': 'composite', 'mat_aniskevich_2023_addnorth_koltron_g1': 'composite', 'mat_aniskevich_2023_stratasys_antero800na': 'polymer', 'mat_aniskevich_2023_stratasys_ultem9085cg': 'polymer'}
SOURCE_COMPANIONS = {'refprop_aniskevich_2023_ultimaker_pc_filament_tensile_modulus': {'value_text': '12.846048545750888', 'cell': 'F6'}, 'refprop_aniskevich_2023_ultimaker_pc_filament_tensile_strength': {'value_text': '0.37772760793745874', 'cell': 'H6'}, 'refprop_aniskevich_2023_ultimaker_pp_filament_tensile_modulus': {'value_text': '3.3884434220774748', 'cell': 'F12'}, 'refprop_aniskevich_2023_ultimaker_pp_filament_tensile_strength': {'value_text': '7.6524603101136623E-2', 'cell': 'H12'}, 'refprop_aniskevich_2023_ultimaker_tpu95a_filament_tensile_modulus': {'value_text': '0.99929582578580267', 'cell': 'F11'}, 'refprop_aniskevich_2023_ultimaker_tpu95a_filament_tensile_strength': {'value_text': '1.8231571011049139', 'cell': 'H11'}, 'refprop_aniskevich_2023_protopasta_conductive_pla_filament_tensile_modulus': {'value_text': '38.847024020963516', 'cell': 'F17'}, 'refprop_aniskevich_2023_protopasta_conductive_pla_filament_tensile_strength': {'value_text': '0.78884272967916691', 'cell': 'H17'}, 'refprop_aniskevich_2023_kimya_abs_esd_filament_tensile_modulus': {'value_text': '14.785410157949164', 'cell': 'F21'}, 'refprop_aniskevich_2023_kimya_abs_esd_filament_tensile_strength': {'value_text': '0.12021685954753565', 'cell': 'H21'}, 'refprop_aniskevich_2023_addnorth_koltron_g1_filament_tensile_modulus': {'value_text': '35.658433900746367', 'cell': 'F20'}, 'refprop_aniskevich_2023_addnorth_koltron_g1_filament_tensile_strength': {'value_text': '8.6351161282011188E-2', 'cell': 'H20'}, 'refprop_aniskevich_2023_stratasys_antero800na_filament_tensile_modulus': {'value_text': '53.100933038290336', 'cell': 'F24'}, 'refprop_aniskevich_2023_stratasys_antero800na_filament_tensile_strength': {'value_text': '0.5469382864506287', 'cell': 'H24'}, 'refprop_aniskevich_2023_stratasys_ultem9085cg_filament_tensile_modulus': {'value_text': '25.6244190249026', 'cell': 'F23'}, 'refprop_aniskevich_2023_stratasys_ultem9085cg_filament_tensile_strength': {'value_text': '2.0973966161110242', 'cell': 'H23'}}
SOURCE_WORKBOOK_SHA256 = '830b2c9277dcc2d03265b63e311a5e7089c258ebb6a389b45d07601ae4b2e4e7'
FORMAL_COUNTS = {'formal_project_admission_count': 1166, 'legacy_source_qualified_identity_count': 1142, 'reviewed_computed_composition_count': 24, 'categories': {'metal': 44, 'polymer': 23, 'inorganic': 61, 'natural': 1010, 'composite': 28}}
QUERY_BASELINE_SHA256 = '393af99b3a9ef08e6d73c87bde302af74e66dd59628e86b368b88882462057a5'
PRIMARY_COUNTS = {'metal': 32, 'polymer': 23, 'inorganic': 49, 'natural': 1010, 'composite': 28}
GRAPH_COUNTS = {'identity': 1142, 'grade': 31, 'state': 1142, 'property': 1150, 'source': 120}


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def expected_workflow(baseline):
    """Change only the complementary full-job guards and append one exact job."""
    validate_targeted_run_scalars(TARGETED_JOB)
    commands = [line.removeprefix("      - run: ") for line in TARGETED_JOB.splitlines()
                if line.startswith("      - run: python -m pip wheel ")]
    require(len(commands) == 1, "Expected one six-project wheel build")
    validate_wheel_command(commands[0])
    require(baseline.count(PREVIOUS_FULL_JOB_IF) == 2, "Unexpected frozen full-job guards")
    for name in ("polymer-composites-targeted", "evidence-batch-targeted", "source-family-growth-targeted", "pur-formulation-targeted", "primary-table-growth-targeted", "primary-table-growth-2-targeted", "primary-table-growth-3-targeted", "primary-table-growth-4-targeted", "primary-table-growth-5-targeted", "primary-table-growth-6-targeted", "primary-table-growth-7-targeted"):
        require(baseline.count("  " + name + ":\n") == 1, "Missing previous experiment job: " + name)
    require("  primary-table-growth-8-targeted:\n" not in baseline, "Predecessor already contains this job")
    for name in ("unit-and-schema", "windows-composite"):
        marker = "  " + name + ":\n" + PREVIOUS_FULL_JOB_IF
        require(baseline.count(marker) == 1, "Unexpected predecessor job block: " + name)
        baseline = baseline.replace(marker, "  " + name + ":\n" + FULL_JOB_IF, 1)
    return baseline + TARGETED_JOB


def validate_names(names, *, root=ROOT):
    require(all(type(name) is str for name in names), "Changed paths must be strings")
    unexpected = sorted(set(names) - APPROVED_FILES)
    require(not unexpected, "Changes exceed eighth primary-table growth scope: " + ", ".join(unexpected))
    for name in names:
        path = root / name
        require(not path.is_symlink() and path.is_file() and path.resolve().is_relative_to(root.resolve()),
                "Approved path must remain a regular repository file: " + name)


def validate_event(head):
    if os.environ.get("GITHUB_ACTIONS") == "true":
        require(os.environ.get("GITHUB_EVENT_NAME") == "push", "Scoped CI requires a push event")
        require(os.environ.get("GITHUB_REF") == BRANCH_REF, "Scoped CI requires its exact experiment branch")
        require(os.environ.get("GITHUB_SHA") == head, "Checkout differs from the pushed GITHUB_SHA")
        require(not git("status", "--porcelain", "--untracked-files=normal"), "Scoped CI checkout must be clean")


def validate_scope():
    head = git("rev-parse", "HEAD").decode().strip()
    subprocess.run(["git", "merge-base", "--is-ancestor", BASE_COMMIT, head], cwd=ROOT, check=True)
    validate_event(head)
    names = set(changed_paths(git("diff", "--name-status", "--no-renames", "-z", BASE_COMMIT, "HEAD", "--")))
    names.update(changed_paths(git("diff", "--name-status", "--no-renames", "-z", "HEAD", "--")))
    names.update(name for name in git("ls-files", "--others", "--exclude-standard", "-z").decode("utf-8").split("\0") if name)
    validate_names(names)
    baseline = git("show", BASE_COMMIT + ":.github/workflows/ci.yml").decode("utf-8")
    require((ROOT / ".github/workflows/ci.yml").read_bytes().decode("utf-8") == expected_workflow(baseline),
            "Workflow differs from the exact predecessor plus eighth primary-table growth job")
    result = {"base_commit": BASE_COMMIT, "head": head, "branch_ref": BRANCH_REF, "changed_files": sorted(names),
              "old_job_steps_preserved": True, "previous_experiment_jobs_preserved": True,
              "exact_targeted_job_preserved": True}
    print(json.dumps(result, indent=2), flush=True)
    return result


def run_group(name):
    install_offline_guard()
    relative, expected = TEST_GROUPS[name]
    require(expected and len(expected) == len(set(expected)), "Exact inventory is empty or duplicated: " + name)
    if name == "core":
        sys.path.insert(0, str(ROOT))
    else:
        require(sys.prefix != sys.base_prefix, "Selected package checks require a fresh installation")
        require(str(ROOT) not in sys.path, "Checkout root must not shadow installed packages")
        installed_origins()
    sys.path.insert(0, str(ROOT / relative))
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromNames(list(expected))
    require(not loader.errors, "Selected test loading failed: " + "\n".join(loader.errors))
    discovered = list(test_ids(suite))
    require(discovered == list(expected), "Discovery differs from the fixed inventory")
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
    packet_path = ROOT / PACKET_PATH
    require(sha256(packet_path.read_bytes()).hexdigest() == PACKET_SHA256, "Reviewed filament packet changed")
    candidate = json.loads(packet_path.read_bytes())["catalogs"]
    graphs = {name: json.loads((ROOT / "materials_boundaries/data" / filename).read_bytes())
              for name, filename in (("materials", "materials.json"),
                                     ("properties", "reference_properties.json"), ("sources", "sources.json"))}
    tables = {"identity": graphs["materials"]["identities"], "grade": graphs["materials"]["grades"],
              "state": graphs["materials"]["records"], "property": graphs["properties"]["records"],
              "source": graphs["sources"]["records"]}
    frozen = {"identity": candidate["materials"]["identities"], "grade": candidate["materials"]["grades"],
              "state": candidate["materials"]["records"], "property": candidate["properties"]["records"],
              "source": candidate["sources"]["records"]}
    require({kind: len(rows) for kind, rows in frozen.items()} == DELTA_COUNTS, "Candidate graph inventory changed")
    for kind, rows in frozen.items():
        for row in rows:
            require([value for value in tables[kind] if value["id"] == row["id"]] == [row],
                    "Packet/runtime complete record differs: " + row["id"])
    require({row["id"]: row["category"] for row in frozen["identity"]} == IDENTITY_CATEGORIES,
            "Accepted identity/classification scope changed")
    selected = []
    for identity in frozen["identity"]:
        states = [row for row in frozen["state"] if row["identity_id"] == identity["id"]]
        require(len(states) == 1, "Accepted identity must have exactly one filament state")
        state = states[0]
        props = [next(row for row in frozen["property"] if row["id"] == identifier)
                 for identifier in state["property_ids"]]
        require(len(props) == 2, "Accepted state must have both measured properties")
        selected.append({"identity": identity, "state": state, "properties": props,
                         "expected_category": IDENTITY_CATEGORIES[identity["id"]],
                         "companions": {prop["id"]: SOURCE_COMPANIONS[prop["id"]] for prop in props}})
    require(dict(Counter(row["category"] for row in tables["identity"])) == PRIMARY_COUNTS,
            "Source tree primary category counts differ")
    require({kind: len(rows) for kind, rows in tables.items()} == GRAPH_COUNTS, "Source tree graph counts differ")
    require(sha256((ROOT / "experimental/platform/query-service/materials_query/pins/legacy_baseline.json").read_bytes()).hexdigest()
            == QUERY_BASELINE_SHA256, "Query baseline changed after source freeze")
    return {"selected": selected, "sources": frozen["source"], "source_id": SOURCE_ID,
            "workbook_sha256": SOURCE_WORKBOOK_SHA256,
            "primary_counts": PRIMARY_COUNTS, "graph_counts": GRAPH_COUNTS, "delta_counts": DELTA_COUNTS,
            "formal_counts": FORMAL_COUNTS, "query_baseline": QUERY_BASELINE_SHA256,
            "packages": [package for _, _, package in PACKAGES],
            "resource_hashes": {name: sha256((ROOT / "materials_boundaries/data" / name).read_bytes()).hexdigest()
                                for name in ("materials.json", "reference_properties.json", "sources.json")}}


INSTALLED_SMOKE = '"""Selected installed filament contract; embedded in the runner after packet review."""\nfrom collections import Counter\nfrom contextlib import redirect_stdout\nfrom decimal import Decimal\nfrom hashlib import sha256\nfrom importlib.resources import files\nimport importlib\nimport io\nimport json\nfrom pathlib import Path\nimport sys\n\n\ndef require(condition, message):\n    if not condition:\n        raise RuntimeError(message)\n\n\ndef source_ids(value):\n    if isinstance(value, dict):\n        return ([value["source_id"]] if "source_id" in value else []) + [\n            item for child in value.values() for item in source_ids(child)]\n    if isinstance(value, list):\n        return [item for child in value for item in source_ids(child)]\n    return []\n\n\nexpected = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))\nfor name in expected["packages"]:\n    package = importlib.import_module(name)\n    require(Path(package.__file__).resolve().is_relative_to(Path(sys.prefix).resolve()),\n            "Checkout package imported: " + name)\nfrom materials_boundaries.catalog import read_catalog, query_catalog\nfrom materials_boundaries.cli import main\nfrom materials_project_catalog.catalog import formal_project_catalog\nfrom materials_query.computed_registry import baseline_digest\n\nfor name, digest in expected["resource_hashes"].items():\n    require(sha256(files("materials_boundaries").joinpath("data", name).read_bytes()).hexdigest() == digest,\n            "Installed catalog bytes differ: " + name)\nmaterials, properties, sources = (read_catalog(name) for name in ("materials", "reference_properties", "sources"))\ntables = {"identity": materials["identities"], "grade": materials["grades"], "state": materials["records"],\n          "property": properties["records"], "source": sources["records"]}\nrequire({kind: len(rows) for kind, rows in tables.items()} == expected["graph_counts"], "Installed graph counts changed")\nrequire(dict(Counter(row["category"] for row in materials["identities"])) == expected["primary_counts"],\n        "Installed primary categories changed")\nfor source in expected["sources"]:\n    require([row for row in tables["source"] if row["id"] == source["id"]] == [source], "Complete source record differs")\ndataset, = [row for row in expected["sources"] if row["id"] == expected["source_id"]]\nrequire(dataset["license"]["identifier"] == "CC-BY-4.0" and dataset["doi"] == "10.5281/zenodo.8089569",\n        "Dataset license or version DOI changed")\noutputs = 0\nidentity_ids, state_ids, property_ids = [], [], []\nfor bundle in expected["selected"]:\n    for kind in ("identity", "state"):\n        wanted = bundle[kind]\n        require([row for row in tables[kind] if row["id"] == wanted["id"]] == [wanted],\n                "Installed complete filament record differs: " + wanted["id"])\n    identity, state = bundle["identity"], bundle["state"]\n    identity_ids.append(identity["id"])\n    state_ids.append(state["id"])\n    require(identity["category"] == bundle["expected_category"] and state["identity_id"] == identity["id"]\n            and state["grade_id"] is None and len(bundle["properties"]) == 2,\n            "Source identity/category/state was multiplied or reclassified")\n    require(set(source_ids(state)) == {expected["source_id"]}, "Classification-only source supports a specimen state")\n    require(state["property_ids"] == [prop["id"] for prop in bundle["properties"]], "State property links changed")\n    require(state["state"]["product_form"]["status"] == "reported"\n            and "2.8" in state["state"]["product_form"]["text"]\n            and "filament" in state["state"]["product_form"]["text"].casefold(),\n            "Reference-filament product form changed")\n    for name in ("processing", "temper_or_heat_treatment", "conditioning", "reinforcement", "porosity", "orientation"):\n        fact = state["state"][name]\n        require(fact["status"] == "not_reported_in_inspected_source" and fact["text"] is None,\n                "Reference filament acquired an unreported state: " + name)\n    require({prop["quantity"] for prop in bundle["properties"]} == {"tensile_modulus", "tensile_strength"},\n            "Measured modulus/strength inventory changed")\n    for prop in bundle["properties"]:\n        property_ids.append(prop["id"])\n        require([row for row in tables["property"] if row["id"] == prop["id"]] == [prop],\n                "Installed complete measured property differs: " + prop["id"])\n        require(prop["material_state_id"] == state["id"] and set(source_ids(prop)) == {expected["source_id"]},\n                "Property source/state links changed or classification evidence was promoted")\n        require(prop["source_document"]["hash_status"] == "recorded"\n                and prop["source_document"]["sha256"] == expected["workbook_sha256"],\n                "Measured property document is not the inspected dataset workbook")\n        value = prop["reported_value"]\n        require(prop["quantity_dimension"] == "pressure" and value["kind"] == "scalar"\n                and value["unit_code"] == "MPa" and value["unit_text"] == "MPa "\n                and Decimal(value["number"]) == Decimal(value["value_text"]) > 0,\n                "Measured value, original MPa unit text, or positive literal semantics changed")\n        require(prop["evidence_kind"] == "published_experimental_reference"\n                and prop["determination_basis"] == "source_reports_measurement"\n                and prop["reporting_basis"] == "reported_summary" and prop["summary_statistic"] == "reported_mean"\n                and prop["density_basis"] is None,\n                "Source-reported experimental mean was reclassified")\n        require(prop["uncertainty"] is None and prop["uncertainty_status"] == "not_reported_in_inspected_source"\n                and prop["sample_count"]["value"] is None and prop["sample_count"]["relation"] == "not_reported",\n                "Source avedev or series-level specimen range became typed uncertainty or exact n")\n        companion = bundle["companions"][prop["id"]]\n        require("avedev" in prop["uncertainty_note"] and companion["value_text"] in prop["uncertainty_note"]\n                and companion["cell"] in prop["uncertainty_note"] and "MPa" in prop["uncertainty_note"],\n                "Original source-labelled avedev value, unit or locator was lost")\n        require(prop["conditions"]["loading_rate"]["status"] == "reported"\n                and prop["conditions"]["loading_rate"]["text"] == "10 mm/min"\n                and prop["conditions"]["test_method"]["status"] == "reported",\n                "Measured filament testing/rate context changed")\n        for name in ("temperature", "test_standard", "direction", "conditioning"):\n            fact = prop["conditions"][name]\n            require(fact["status"] == "not_reported_in_inspected_source" and fact["text"] is None,\n                    "Measured filament property acquired an unknown or ISO-reference condition: " + name)\n        require(prop["method_definition"]["type"] == "source_reported_conventional"\n                and prop["method_definition"]["extraction_window"] is None,\n                "Measured property gained an unreported extraction method")\n        require(prop["evaluation_support"] == "catalog_only" and not prop["universal_bound"]\n                and not prop["engineering_allowable"] and not prop["verification"]["independent_scientific_review"]\n                and not prop["verification"]["raw_data_reanalysis"], "Measured reference gained unsupported capabilities")\n    prop = next(row for row in bundle["properties"] if row["quantity"] == "tensile_modulus")\n    selected = query_catalog("reference-properties", record_id=prop["id"])\n    for language in ("en", "zh", "ja", "de"):\n        for flag in ("--json", "--text"):\n            output = io.StringIO()\n            with redirect_stdout(output):\n                code = main(["catalog", "reference-properties", "--id", prop["id"], "--lang", language, flag])\n            text = output.getvalue()\n            require(code == 0 and "[missing:" not in text, "Installed filament CLI failed")\n            if flag == "--json":\n                require(json.loads(text) == selected, "Installed reference JSON depends on language")\n            else:\n                require(prop["reported_value"]["value_text"] in text and prop["uncertainty_note"] in text,\n                        "Original value or source avedev caveat missing from text")\n            outputs += 1\ndelta = expected["delta_counts"]\nrequire(len(set(identity_ids)) == delta["identity"] and len(set(state_ids)) == delta["state"]\n        and len(set(property_ids)) == delta["property"] and delta["grade"] == 0\n        and outputs == delta["identity"] * 8, "Translations, aliases or states inflated the accepted inventory")\nformal = formal_project_catalog()\nrequire(formal["counts"] == expected["formal_counts"], "Installed formal boundary differs")\nfor identifier in identity_ids:\n    require(len([row for row in formal["records"] if row["partition"] == "legacy-source-qualified"\n                 and row["identity"]["id"] == identifier]) == 1, "Filament contributes multiple formal identities")\nanchor = baseline_digest()\nrequire(anchor == expected["query_baseline"], "Installed query pin differs")\nprint(json.dumps({"new_identities": delta["identity"], "new_grades": delta["grade"], "new_states": delta["state"],\n                  "new_properties": delta["property"], "new_sources": delta["source"],\n                  "selected_cli_outputs": outputs, "formal_count": formal["counts"]["formal_project_admission_count"],\n                  "reviewed_computed": 24, "core_count": expected["graph_counts"]["identity"],\n                  "query_baseline": anchor, "fresh_install": True,\n                  "scope": "Selected installed reference-filament measurements; not exhaustive regression."}))\n'


def check_installed(wheel_dir, dependency_dir):
    wheels = verify_wheels(wheel_dir)
    require(dependency_dir.is_dir() and any(dependency_dir.glob("*.whl")), "Offline dependency wheels are missing")
    env = clean_env()
    with tempfile.TemporaryDirectory(prefix="primary-table-growth-8-installed-") as temporary:
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
