#!/usr/bin/env python3
"""Validate the bounded Zenodo Nylon follow-up branch.

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
from run_zenodo_identity_followup_ci import (
    BRANCH_REF as PREVIOUS_BRANCH_REF, BUILD_COMMAND,
    FULL_JOB_IF as PREVIOUS_FULL_JOB_IF, TARGETED_JOB as PREVIOUS_TARGETED_JOB,
    changed_paths, validate_targeted_run_scalars, validate_wheel_command,
)
from run_evidence_batch_ci import (
    ExactResult, PACKAGES, clean_env, install_offline_guard, installed_origins,
    require, run, sha256, test_ids, verify_wheels,
)

BASE_COMMIT = '2c8ddac78f5cd43dfa071ad23639b826561a043b'
BRANCH_REF = "refs/heads/experiment/zenodo-8089569-nylon-followup-20261021"
FULL_JOB_IF = PREVIOUS_FULL_JOB_IF.replace("') }}\n", "' && github.ref != '" + BRANCH_REF + "') }}\n")
TARGETED_JOB = (PREVIOUS_TARGETED_JOB
                .replace("  zenodo-identity-followup-targeted:\n", "  zenodo-nylon-followup-targeted:\n")
                .replace(PREVIOUS_BRANCH_REF, BRANCH_REF)
                .replace("run_zenodo_identity_followup_ci.py", "run_zenodo_nylon_followup_ci.py"))

# The owner-approved inventory is frozen after packet, data and history owners finish.
APPROVED_FILES = frozenset({
    '.github/workflows/ci.yml',
    'README.md',
    'THIRD_PARTY_NOTICES.md',
    'experimental/material-batches/zenodo-8089569-nylon-followup-20261021/README.md',
    'experimental/material-batches/zenodo-8089569-nylon-followup-20261021/integration-report.json',
    'experimental/material-batches/zenodo-8089569-nylon-followup-20261021/integration.json',
    'experimental/material-batches/zenodo-8089569-nylon-followup-20261021/packet-spec.json',
    'experimental/material-batches/zenodo-8089569-nylon-followup-20261021/preparation-receipt.json',
    'experimental/material-batches/zenodo-8089569-nylon-followup-20261021/prepared-packet.json',
    'experimental/material-batches/zenodo-8089569-nylon-followup-20261021/source-review.json',
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
    'scripts/prepare_formulation_packet.py',
    'scripts/run_zenodo_nylon_followup_ci.py',
    'tests/fixtures/nylon_followup_data_20261021.json',
    'tests/fixtures/nylon_followup_files_20261021.json',
    'tests/material_append_successors.py',
    'tests/test_nylon_followup.py',
    'tests/test_nylon_followup_preservation.py',
    'tests/test_zenodo_nylon_followup_ci.py',
})

# Nonempty exact inventories are required before any selected phase can run.
TEST_GROUPS = {'core': ('tests', ('test_nylon_followup_preservation.NylonFollowupPreservationTests.test_one_identity_one_state_keeps_independent_measured_properties', 'test_nylon_followup_preservation.NylonFollowupPreservationTests.test_exact_2c8_recovery_rejects_partial_owner_unit_source_and_order_drift', 'test_nylon_followup_preservation.NylonFollowupPreservationTests.test_compiler_and_integrator_replay_preserve_immutable_artifacts', 'test_nylon_followup_preservation.NylonFollowupPreservationTests.test_selected_catalog_bytes_and_legacy_chain_remain_exact', 'test_nylon_followup_preservation.NylonFollowupPreservationTests.test_finite_files_and_registry_selection_keep_old_pins', 'test_zenodo_nylon_followup_ci.ZenodoNylonFollowupCITests.test_previous_jobs_keep_every_step_and_only_new_branch_is_gated', 'test_zenodo_nylon_followup_ci.ZenodoNylonFollowupCITests.test_scope_rejects_unlisted_paths_deleted_files_and_nonfiles', 'test_zenodo_nylon_followup_ci.ZenodoNylonFollowupCITests.test_ci_requires_exact_event_branch_sha_and_clean_checkout', 'test_zenodo_nylon_followup_ci.ZenodoNylonFollowupCITests.test_ambiguous_yaml_scalars_and_index_package_builds_fail', 'test_zenodo_nylon_followup_ci.ZenodoNylonFollowupCITests.test_unknown_predecessor_workflow_shapes_are_rejected', 'test_tough_pla_followup_preservation.ToughPLAFollowupPreservationTests.test_selected_catalog_bytes_and_legacy_chain_remain_exact', 'test_zenodo_identity_followup_ci.ZenodoIdentityFollowupCITests.test_previous_jobs_keep_every_step_and_only_new_branch_is_gated', 'test_curated_filament_adapter.CuratedFilamentAdapterTests.test_frozen_classification_sources_only_support_reviewed_identities', 'test_curated_filament_adapter.CuratedFilamentAdapterTests.test_frozen_classification_sources_reject_rewrites_and_promotions', 'test_curated_filament_adapter.CuratedFilamentAdapterTests.test_measured_columns_exclude_iso_reference_and_print_states', 'test_curated_filament_adapter.CuratedFilamentAdapterTests.test_blanks_zero_and_formula_values_fail_closed', 'test_curated_filament_adapter.CuratedFilamentAdapterTests.test_exact_join_rejects_missing_duplicate_or_state_keys', 'test_curated_filament_adapter.CuratedFilamentAdapterTests.test_sparse_replay_is_deterministic_and_immutable', 'test_curated_filament_adapter.CuratedFilamentAdapterTests.test_xlsx_reader_keeps_numeric_lexemes_and_resolves_shared_strings', 'test_nylon_followup.NylonFollowupTests.test_one_historical_family_binds_original_measured_cells', 'test_nylon_followup.NylonFollowupTests.test_grouped_ownership_and_missing_measurements_fail_closed', 'test_nylon_followup.NylonFollowupTests.test_measured_columns_units_zeros_and_deviations_fail_closed', 'test_nylon_followup.NylonFollowupTests.test_frozen_packet_counts_and_historical_unknowns', 'test_nylon_followup.NylonFollowupTests.test_dual_sources_require_both_exact_identity_only_records', 'test_nylon_followup.NylonFollowupTests.test_source_scoped_alias_collisions_and_sparse_replay', 'test_formulation_packet_preparation.FormulationPacketPreparationTests.test_missing_crosswalk_review_and_license_remain_pending_without_upgrade', 'test_formulation_packet_preparation.FormulationPacketPreparationTests.test_shared_contexts_and_explicit_grade_multiple_states_do_not_multiply_identity', 'test_formulation_packet_preparation.FormulationPacketPreparationTests.test_reidentified_designation_or_alias_cannot_evade_existing_identity', 'test_formulation_packet_integration.FormulationPacketIntegrationTests.test_cross_batch_source_designation_collision_is_atomic', 'test_formulation_packet_integration.FormulationPacketIntegrationTests.test_linked_grade_designation_and_alias_cannot_create_another_identity')), 'query': ('experimental/platform/query-service/catalog-tests', ('test_catalog_baseline.IntegratedBaselineTests.test_installed_package_matches_exact_new_anchor', 'test_catalog_baseline.IntegratedBaselineTests.test_changed_core_resource_fails_even_with_unchanged_identity_count', 'test_baseline_compatibility.BaselineCompatibility.test_nylon_parent_manifest_and_catalog_recovery_remain_exact', 'test_baseline_compatibility.BaselineCompatibility.test_nylon_parent_database_rejected_without_migration', 'test_baseline_compatibility.BaselineCompatibility.test_tough_pla_parent_manifest_and_catalog_recovery_remain_exact', 'test_local_catalog.CatalogAPI.test_nylon_historical_family_preserves_measured_filament_state', 'test_local_catalog.CatalogAPI.test_tough_pla_two_states_share_one_identity', 'test_family_relationships.FamilyRelationshipTests.test_coverage_exact_and_no_count_inflation', 'test_formal_project_catalog.FormalAPI.test_counts_and_no_legacy_rewrite', 'test_formal_project_catalog.FormalAPI.test_drift_disables_only_formal', 'test_computed_recovery.RegistryTests.test_atomic_held_and_replay', 'test_computed_v2_tranche.ReviewedTrancheTests.test_tranche_counts_relations_and_replay')), 'formal': ('formal-catalog/tests', ('test_formal_project_core.FormalProjectCatalog.test_exact_counts_and_categories', 'test_formal_project_core.FormalProjectCatalog.test_full_legacy_identity_parity', 'test_formal_project_core.FormalProjectCatalog.test_pin_drift_fail_closed')), 'ingestion': ('experimental/platform/ingestion', ('test_review_boundary.ReviewBoundaryTests.test_formal_and_example_counts_remain_separate', 'test_review_boundary.ReviewBoundaryTests.test_boundary_fails_closed_on_changed_bytes', 'test_nomad_incremental.IncrementalTests.test_nylon_predecessor_scope_stays_read_only_without_migration', 'test_nomad_incremental.IncrementalTests.test_new_store_requires_exact_current_catalog_scope_before_creation', 'test_formal_overlap_audit.FormalOverlapAuditTests.test_primary_partition_and_overlapping_dimensions_are_distinct', 'test_formal_overlap_audit.FormalOverlapAuditTests.test_nylon_historical_family_keeps_state_composition_unknown', 'test_formal_overlap_audit.FormalOverlapAuditTests.test_tough_pla_two_states_form_one_formal_identity', 'test_formal_overlap_audit.FormalOverlapAuditTests.test_legacy_names_grades_and_composites_never_become_stoichiometry', 'test_formal_overlap_audit.FormalOverlapAuditTests.test_alexandria_formula_exposes_three_distinct_qualified_relations', 'test_formal_overlap_audit.FormalOverlapAuditTests.test_exact_frozen_record_reference_confirms_only_record_reuse')), 'relationships': ('experimental/platform/relationships', ('test_hbn_relationship_projection.HBNRelationshipProjectionTests.test_actual_counts_are_separate_from_proposed_graph',))}

SOURCE_ID = "aniskevich_bulderberga_2023_polymer_mechanical_characterisation"
PACKET_PATH = 'experimental/material-batches/zenodo-8089569-nylon-followup-20261021/prepared-packet.json'
PACKET_SHA256 = 'b18d7fc70bc5da537672f20a1682594c36c8d2d1e4c9e0ac05f9647d586e5172'
DELTA_COUNTS = {'identity': 1, 'grade': 0, 'state': 1, 'property': 2, 'source': 2}
IDENTITY_CATEGORIES = {'mat_aniskevich_2023_ultimaker_nylon': 'polymer'}
SOURCE_COMPANIONS = {'refprop_aniskevich_2023_ultimaker_nylon_transparent_filament_tensile_modulus': {'value_text': '39.07712093742888', 'cell': 'F9'}, 'refprop_aniskevich_2023_ultimaker_nylon_transparent_filament_tensile_strength': {'value_text': '3.6781068579660881', 'cell': 'H9'}}
SOURCE_WORKBOOK_SHA256 = '830b2c9277dcc2d03265b63e311a5e7089c258ebb6a389b45d07601ae4b2e4e7'
FORMAL_COUNTS = {'formal_project_admission_count': 1168, 'legacy_source_qualified_identity_count': 1144, 'reviewed_computed_composition_count': 24, 'categories': {'metal': 44, 'polymer': 25, 'inorganic': 61, 'natural': 1010, 'composite': 28}}
QUERY_BASELINE_SHA256 = '124044eb8afcaf927ec9ff4770da66dfedc641391cd58e4b873735ee7424db4e'
PRIMARY_COUNTS = {'metal': 32, 'polymer': 25, 'inorganic': 49, 'natural': 1010, 'composite': 28}
GRAPH_COUNTS = {'identity': 1144, 'grade': 31, 'state': 1145, 'property': 1156, 'source': 123}


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, timeout=30)


def expected_workflow(baseline):
    """Change only the complementary full-job guards and append one exact job."""
    validate_targeted_run_scalars(TARGETED_JOB)
    commands = [line.removeprefix("      - run: ") for line in TARGETED_JOB.splitlines()
                if line.startswith("      - run: python -m pip wheel ")]
    require(len(commands) == 1, "Expected one six-project wheel build")
    validate_wheel_command(commands[0])
    require(baseline.count(PREVIOUS_FULL_JOB_IF) == 2, "Unexpected frozen full-job guards")
    for name in ("polymer-composites-targeted", "evidence-batch-targeted", "source-family-growth-targeted", "pur-formulation-targeted", "primary-table-growth-targeted", "primary-table-growth-2-targeted", "primary-table-growth-3-targeted", "primary-table-growth-4-targeted", "primary-table-growth-5-targeted", "primary-table-growth-6-targeted", "primary-table-growth-7-targeted", "primary-table-growth-8-targeted", "zenodo-identity-followup-targeted"):
        require(baseline.count("  " + name + ":\n") == 1, "Missing previous experiment job: " + name)
    require("  zenodo-nylon-followup-targeted:\n" not in baseline, "Predecessor already contains this job")
    for name in ("unit-and-schema", "windows-composite"):
        marker = "  " + name + ":\n" + PREVIOUS_FULL_JOB_IF
        require(baseline.count(marker) == 1, "Unexpected predecessor job block: " + name)
        baseline = baseline.replace(marker, "  " + name + ":\n" + FULL_JOB_IF, 1)
    return baseline + TARGETED_JOB


def validate_names(names, *, root=ROOT):
    require(all(type(name) is str for name in names), "Changed paths must be strings")
    unexpected = sorted(set(names) - APPROVED_FILES)
    require(not unexpected, "Changes exceed Zenodo Nylon follow-up scope: " + ", ".join(unexpected))
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
    subprocess.run(["git", "merge-base", "--is-ancestor", BASE_COMMIT, head], cwd=ROOT, check=True, timeout=30)
    validate_event(head)
    names = set(changed_paths(git("diff", "--name-status", "--no-renames", "-z", BASE_COMMIT, "HEAD", "--")))
    names.update(changed_paths(git("diff", "--name-status", "--no-renames", "-z", "HEAD", "--")))
    names.update(name for name in git("ls-files", "--others", "--exclude-standard", "-z").decode("utf-8").split("\0") if name)
    validate_names(names)
    baseline = git("show", BASE_COMMIT + ":.github/workflows/ci.yml").decode("utf-8")
    require((ROOT / ".github/workflows/ci.yml").read_bytes().decode("utf-8") == expected_workflow(baseline),
            "Workflow differs from the exact predecessor plus Zenodo Nylon follow-up job")
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
    packet_raw = (ROOT / PACKET_PATH).read_bytes()
    require(sha256(packet_raw).hexdigest() == PACKET_SHA256, "Reviewed follow-up packet changed")
    candidate = json.loads(packet_raw)["catalogs"]
    graphs = {name: json.loads((ROOT / "materials_boundaries/data" / filename).read_bytes())
              for name, filename in (("materials", "materials.json"),
                                     ("properties", "reference_properties.json"), ("sources", "sources.json"))}
    tables = {"identity": graphs["materials"]["identities"], "grade": graphs["materials"]["grades"],
              "state": graphs["materials"]["records"], "property": graphs["properties"]["records"],
              "source": graphs["sources"]["records"]}
    frozen = {"identity": candidate["materials"]["identities"], "grade": candidate["materials"]["grades"],
              "state": candidate["materials"]["records"], "property": candidate["properties"]["records"],
              "source": candidate["sources"]["records"]}
    require({kind: len(rows) for kind, rows in frozen.items()} == CANDIDATE_COUNTS,
            "Candidate reference inventory changed")
    for kind, rows in frozen.items():
        require(len({row["id"] for row in rows}) == len(rows), "Duplicate candidate " + kind)
        for row in rows:
            require([value for value in tables[kind] if value["id"] == row["id"]] == [row],
                    "Packet/runtime complete record differs: " + row["id"])
    require({row["id"]: row["category"] for row in frozen["identity"]} == IDENTITY_CATEGORIES,
            "Accepted identity/classification scope changed")
    require(set(NEW_SOURCE_IDS).isdisjoint(REUSED_SOURCE_IDS)
            and set(NEW_SOURCE_IDS) | set(REUSED_SOURCE_IDS) == {row["id"] for row in frozen["source"]}
            and len(NEW_SOURCE_IDS) == DELTA_COUNTS["source"], "New and reused source references changed")
    selected = []
    for state in frozen["state"]:
        matches = [row for row in frozen["identity"] if row["id"] == state["identity_id"]]
        require(len(matches) == 1, "State must belong to its one candidate identity")
        identity = matches[0]
        props = [next(row for row in frozen["property"] if row["id"] == identifier)
                 for identifier in state["property_ids"]]
        require(len(props) == 2 and all(prop["material_state_id"] == state["id"] for prop in props),
                "Accepted state must own both measured properties")
        selected.append({"identity": identity, "state": state, "properties": props,
                         "expected_category": IDENTITY_CATEGORIES[identity["id"]],
                         "companions": {prop["id"]: SOURCE_COMPANIONS[prop["id"]] for prop in props}})
    require({state["identity_id"] for state in frozen["state"]} == set(IDENTITY_CATEGORIES),
            "Candidate identity lacks its source-qualified states")
    require(dict(Counter(row["category"] for row in tables["identity"])) == PRIMARY_COUNTS,
            "Source tree primary category counts differ")
    require({kind: len(rows) for kind, rows in tables.items()} == GRAPH_COUNTS, "Source tree graph counts differ")
    require(sha256((ROOT / "experimental/platform/query-service/materials_query/pins/legacy_baseline.json").read_bytes()).hexdigest()
            == QUERY_BASELINE_SHA256, "Query baseline changed after source freeze")
    return {"selected": selected, "sources": frozen["source"], "source_id": SOURCE_ID,
            "new_source_ids": NEW_SOURCE_IDS, "reused_source_ids": REUSED_SOURCE_IDS,
            "candidate_counts": CANDIDATE_COUNTS, "workbook_sha256": SOURCE_WORKBOOK_SHA256,
            "primary_counts": PRIMARY_COUNTS, "graph_counts": GRAPH_COUNTS, "delta_counts": DELTA_COUNTS,
            "formal_counts": FORMAL_COUNTS, "query_baseline": QUERY_BASELINE_SHA256,
            "packages": [package for _, _, package in PACKAGES],
            "resource_hashes": {name: sha256((ROOT / "materials_boundaries/data" / name).read_bytes()).hexdigest()
                                for name in ("materials.json", "reference_properties.json", "sources.json")}}


CANDIDATE_COUNTS = {'identity': 1, 'grade': 0, 'state': 1, 'property': 2, 'source': 3}
NEW_SOURCE_IDS = ['ultimaker_nylon_pricing_20210504', 'ultimaker_nylon_sds_20190114']
REUSED_SOURCE_IDS = ['aniskevich_bulderberga_2023_polymer_mechanical_characterisation']
INSTALLED_SMOKE = '"""Selected installed Nylon contract; embedded in the runner after packet review."""\nfrom collections import Counter\nfrom contextlib import redirect_stdout\nfrom decimal import Decimal\nfrom hashlib import sha256\nfrom importlib.resources import files\nimport importlib\nimport io\nimport json\nfrom pathlib import Path\nimport sys\n\n\ndef require(condition, message):\n    if not condition:\n        raise RuntimeError(message)\n\n\ndef source_ids(value):\n    if isinstance(value, dict):\n        return ([value["source_id"]] if "source_id" in value else []) + [\n            item for child in value.values() for item in source_ids(child)]\n    if isinstance(value, list):\n        return [item for child in value for item in source_ids(child)]\n    return []\n\n\nexpected = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))\nfor name in expected["packages"]:\n    package = importlib.import_module(name)\n    require(Path(package.__file__).resolve().is_relative_to(Path(sys.prefix).resolve()),\n            "Checkout package imported: " + name)\nfrom materials_boundaries.catalog import read_catalog, query_catalog\nfrom materials_boundaries.cli import main\nfrom materials_project_catalog.catalog import formal_project_catalog\nfrom materials_query.computed_registry import baseline_digest\n\nfor name, digest in expected["resource_hashes"].items():\n    require(sha256(files("materials_boundaries").joinpath("data", name).read_bytes()).hexdigest() == digest,\n            "Installed catalog bytes differ: " + name)\nmaterials, properties, sources = (read_catalog(name) for name in ("materials", "reference_properties", "sources"))\ntables = {"identity": materials["identities"], "grade": materials["grades"], "state": materials["records"],\n          "property": properties["records"], "source": sources["records"]}\nrequire({kind: len(rows) for kind, rows in tables.items()} == expected["graph_counts"], "Installed graph counts changed")\nrequire(dict(Counter(row["category"] for row in materials["identities"])) == expected["primary_counts"],\n        "Installed primary categories changed")\nfor source in expected["sources"]:\n    require([row for row in tables["source"] if row["id"] == source["id"]] == [source], "Complete source record differs")\ndataset, = [row for row in expected["sources"] if row["id"] == expected["source_id"]]\nrequire(dataset["license"]["identifier"] == "CC-BY-4.0" and dataset["doi"] == "10.5281/zenodo.8089569",\n        "Dataset license or version DOI changed")\nrequire(len(expected["sources"]) == expected["candidate_counts"]["source"]\n        and len(expected["new_source_ids"]) == expected["delta_counts"]["source"]\n        and set(expected["new_source_ids"]).isdisjoint(expected["reused_source_ids"])\n        and set(expected["new_source_ids"]) | set(expected["reused_source_ids"])\n            == {row["id"] for row in expected["sources"]}, "Source references were counted as new admissions")\noutputs = 0\nidentity_ids, state_ids, property_ids = [], [], []\nfor bundle in expected["selected"]:\n    for kind in ("identity", "state"):\n        wanted = bundle[kind]\n        require([row for row in tables[kind] if row["id"] == wanted["id"]] == [wanted],\n                "Installed complete filament record differs: " + wanted["id"])\n    identity, state = bundle["identity"], bundle["state"]\n    identity_ids.append(identity["id"])\n    state_ids.append(state["id"])\n    require(identity["category"] == bundle["expected_category"] and state["identity_id"] == identity["id"]\n            and state["grade_id"] is None and len(bundle["properties"]) == 2,\n            "Source identity/category/state was multiplied or reclassified")\n    require(set(source_ids(state)) == {expected["source_id"]}, "Classification-only source supports a specimen state")\n    require(set(source_ids(identity)) == {expected["source_id"], *expected["new_source_ids"]},\n            "Historical family identity must retain both identity-only manufacturer sources and the measured study")\n    composition = state["state"]["composition_or_purity"]\n    require(composition["status"] == "not_reported_in_inspected_source" and composition["text"] is None\n            and composition["evidence"] == [], "Historical manufacturer-family context became studied-state composition")\n    require(state["property_ids"] == [prop["id"] for prop in bundle["properties"]], "State property links changed")\n    require(state["state"]["product_form"]["status"] == "reported"\n            and "2.8" in state["state"]["product_form"]["text"]\n            and "filament" in state["state"]["product_form"]["text"].casefold(),\n            "Reference-filament product form changed")\n    for name in ("processing", "temper_or_heat_treatment", "conditioning", "reinforcement", "porosity", "orientation"):\n        fact = state["state"][name]\n        require(fact["status"] == "not_reported_in_inspected_source" and fact["text"] is None,\n                "Reference filament acquired an unreported state: " + name)\n    require({prop["quantity"] for prop in bundle["properties"]} == {"tensile_modulus", "tensile_strength"},\n            "Measured modulus/strength inventory changed")\n    for prop in bundle["properties"]:\n        property_ids.append(prop["id"])\n        require([row for row in tables["property"] if row["id"] == prop["id"]] == [prop],\n                "Installed complete measured property differs: " + prop["id"])\n        require(prop["material_state_id"] == state["id"] and set(source_ids(prop)) == {expected["source_id"]},\n                "Property source/state links changed or classification evidence was promoted")\n        require(prop["source_document"]["hash_status"] == "recorded"\n                and prop["source_document"]["sha256"] == expected["workbook_sha256"],\n                "Measured property document is not the inspected dataset workbook")\n        value = prop["reported_value"]\n        require(prop["quantity_dimension"] == "pressure" and value["kind"] == "scalar"\n                and value["unit_code"] == "MPa" and value["unit_text"] == "MPa "\n                and Decimal(value["number"]) == Decimal(value["value_text"]) > 0,\n                "Measured value, original MPa unit text, or positive literal semantics changed")\n        require(prop["evidence_kind"] == "published_experimental_reference"\n                and prop["determination_basis"] == "source_reports_measurement"\n                and prop["reporting_basis"] == "reported_summary" and prop["summary_statistic"] == "reported_mean"\n                and prop["density_basis"] is None,\n                "Source-reported experimental mean was reclassified")\n        require(prop["uncertainty"] is None and prop["uncertainty_status"] == "not_reported_in_inspected_source"\n                and prop["sample_count"]["value"] is None and prop["sample_count"]["relation"] == "not_reported",\n                "Source avedev or series-level specimen range became typed uncertainty or exact n")\n        companion = bundle["companions"][prop["id"]]\n        require("avedev" in prop["uncertainty_note"] and companion["value_text"] in prop["uncertainty_note"]\n                and companion["cell"] in prop["uncertainty_note"] and "MPa" in prop["uncertainty_note"],\n                "Original source-labelled avedev value, unit or locator was lost")\n        require(prop["conditions"]["loading_rate"]["status"] == "reported"\n                and prop["conditions"]["loading_rate"]["text"] == "10 mm/min"\n                and prop["conditions"]["test_method"]["status"] == "reported",\n                "Measured filament testing/rate context changed")\n        for name in ("temperature", "test_standard", "direction", "conditioning"):\n            fact = prop["conditions"][name]\n            require(fact["status"] == "not_reported_in_inspected_source" and fact["text"] is None,\n                    "Measured filament property acquired an unknown or ISO-reference condition: " + name)\n        require(prop["method_definition"]["type"] == "source_reported_conventional"\n                and prop["method_definition"]["extraction_window"] is None,\n                "Measured property gained an unreported extraction method")\n        require(prop["evaluation_support"] == "catalog_only" and not prop["universal_bound"]\n                and not prop["engineering_allowable"] and not prop["verification"]["independent_scientific_review"]\n                and not prop["verification"]["raw_data_reanalysis"], "Measured reference gained unsupported capabilities")\n    prop = next(row for row in bundle["properties"] if row["quantity"] == "tensile_modulus")\n    selected = query_catalog("reference-properties", record_id=prop["id"])\n    for language in ("en", "zh", "ja", "de"):\n        for flag in ("--json", "--text"):\n            output = io.StringIO()\n            with redirect_stdout(output):\n                code = main(["catalog", "reference-properties", "--id", prop["id"], "--lang", language, flag])\n            text = output.getvalue()\n            require(code == 0 and "[missing:" not in text, "Installed filament CLI failed")\n            if flag == "--json":\n                require(json.loads(text) == selected, "Installed reference JSON depends on language")\n            else:\n                require(prop["reported_value"]["value_text"] in text and prop["uncertainty_note"] in text,\n                        "Original value or source avedev caveat missing from text")\n            outputs += 1\ndelta = expected["delta_counts"]\nrequire(len(set(identity_ids)) == delta["identity"] and len(set(state_ids)) == delta["state"]\n        and len(state_ids) == len(set(state_ids))\n        and len(property_ids) == len(set(property_ids)) == delta["property"] and delta["grade"] == 0\n        and outputs == delta["state"] * 8, "Translations, aliases or states inflated the accepted inventory")\nformal = formal_project_catalog()\nrequire(formal["counts"] == expected["formal_counts"], "Installed formal boundary differs")\nfor identifier in set(identity_ids):\n    require(len([row for row in formal["records"] if row["partition"] == "legacy-source-qualified"\n                 and row["identity"]["id"] == identifier]) == 1, "Filament contributes multiple formal identities")\nanchor = baseline_digest()\nrequire(anchor == expected["query_baseline"], "Installed query pin differs")\nprint(json.dumps({"new_identities": delta["identity"], "new_grades": delta["grade"], "new_states": delta["state"],\n                  "new_properties": delta["property"], "new_sources": delta["source"],\n                  "referenced_sources": len(expected["sources"]), "reused_sources": len(expected["reused_source_ids"]),\n                  "selected_cli_outputs": outputs, "formal_count": formal["counts"]["formal_project_admission_count"],\n                  "reviewed_computed": 24, "core_count": expected["graph_counts"]["identity"],\n                  "query_baseline": anchor, "fresh_install": True,\n                  "scope": "Selected installed reference-filament measurements; not exhaustive regression."}))\n'


def check_installed(wheel_dir, dependency_dir):
    wheels = verify_wheels(wheel_dir)
    require(dependency_dir.is_dir() and any(dependency_dir.glob("*.whl")), "Offline dependency wheels are missing")
    env = clean_env()
    with tempfile.TemporaryDirectory(prefix="zenodo-nylon-followup-installed-") as temporary:
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
