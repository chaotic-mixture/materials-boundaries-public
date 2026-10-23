#!/usr/bin/env python3
"""Check the bounded family-adjacency experiment and fresh installed API.

The selected inventories are explicit: this is not the full repository suite.
All prior workflow steps remain intact. No catalog or review input is changed.
"""
import argparse
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
from run_zenodo_nylon_followup_ci import (
    BRANCH_REF as PREVIOUS_BRANCH_REF, BUILD_COMMAND,
    FULL_JOB_IF as PREVIOUS_FULL_JOB_IF, TARGETED_JOB as PREVIOUS_TARGETED_JOB,
    changed_paths, validate_targeted_run_scalars, validate_wheel_command,
)
from run_evidence_batch_ci import (
    ExactResult, PACKAGES, clean_env, install_offline_guard, installed_origins,
    require, run, sha256, test_ids, verify_wheels,
)

BASE_COMMIT = '7248dcd06e7ab4bc5f3fae1f3f21a7d9e0dbad3c'
BRANCH_REF = 'refs/heads/experiment/family-adjacency-20261023'
FULL_JOB_IF = PREVIOUS_FULL_JOB_IF.replace("') }}\n", "' && github.ref != '" + BRANCH_REF + "') }}\n")
TARGETED_JOB = (PREVIOUS_TARGETED_JOB
                .replace('  zenodo-nylon-followup-targeted:\n', '  family-adjacency-targeted:\n')
                .replace(PREVIOUS_BRANCH_REF, BRANCH_REF)
                .replace('run_zenodo_nylon_followup_ci.py', 'run_family_adjacency_ci.py'))

APPROVED_FILES = frozenset({
    '.github/workflows/ci.yml',
    'experimental/platform/query-service/materials_query/family_relationships.py',
    'experimental/platform/query-service/materials_query/local_catalog.py',
    'experimental/platform/query-service/catalog-tests/test_family_adjacency.py',
    'experimental/platform/query-service/catalog-tests/test_family_relationships.py',
    'experimental/platform/relationships/FAMILY_OVERLAP.md',
    'scripts/run_family_adjacency_ci.py',
    'tests/fixtures/family_adjacency_files_20261023.json',
    'tests/material_append_successors.py',
    'tests/test_family_adjacency_ci.py',
    'tests/test_family_adjacency_history.py',
})

# Frozen after the test owner finishes; no discovered test can silently vanish.
TEST_GROUPS = {'core': ('tests',
          ('test_release_metadata.ReleaseMetadataTests.test_all_current_engine_labels_match_package',
           'test_release_metadata.ReleaseMetadataTests.test_build_configuration_and_readme_use_current_version',
           'test_release_metadata.ReleaseMetadataTests.test_comparison_embedded_snapshots_and_exact_references',
           'test_release_metadata.ReleaseMetadataTests.test_local_schema_reference_targets_exist',
           'test_release_metadata.ReleaseMetadataTests.test_version_is_one_build_readable_literal',
           'test_family_adjacency_ci.FamilyAdjacencyCITests.test_ambiguous_yaml_scalars_and_index_package_builds_fail',
           'test_family_adjacency_ci.FamilyAdjacencyCITests.test_ci_requires_exact_event_branch_sha_and_clean_checkout',
           'test_family_adjacency_ci.FamilyAdjacencyCITests.test_inventories_are_nonempty_unique_and_preserve_affected_modules',
           'test_family_adjacency_ci.FamilyAdjacencyCITests.test_previous_jobs_keep_every_step_and_only_new_branch_is_gated',
           'test_family_adjacency_ci.FamilyAdjacencyCITests.test_scope_rejects_catalog_data_unlisted_paths_and_nonfiles',
           'test_family_adjacency_ci.FamilyAdjacencyCITests.test_unknown_predecessor_workflow_shapes_are_rejected',
           'test_family_adjacency_history.FamilyAdjacencyHistoryTests.test_all_material_workflow_views_keep_their_exact_file_pins',
           'test_family_adjacency_history.FamilyAdjacencyHistoryTests.test_code_only_workflow_round_trip_retains_old_rejection',
           'test_family_adjacency_history.FamilyAdjacencyHistoryTests.test_data_registry_and_every_material_ledger_remain_unchanged',
           'test_family_adjacency_history.FamilyAdjacencyHistoryTests.test_only_one_workflow_has_a_pinned_code_successor',
           'test_family_adjacency_history.FamilyAdjacencyHistoryTests.test_unknown_boundaries_and_ledger_or_edit_drift_are_rejected',
           'test_zenodo_nylon_followup_ci.ZenodoNylonFollowupCITests.test_previous_jobs_keep_every_step_and_only_new_branch_is_gated')),
 'adjacency': ('experimental/platform/query-service/catalog-tests',
               ('test_family_adjacency.FamilyAdjacencyTests.test_both_deduplicates_self_edge_with_both_navigation_directions',
                'test_family_adjacency.FamilyAdjacencyTests.test_both_version_pins_are_required_and_stale_pins_conflict',
                'test_family_adjacency.FamilyAdjacencyTests.test_captured_query_has_no_disk_reads_or_overlay_refresh',
                'test_family_adjacency.FamilyAdjacencyTests.test_default_and_maximum_limits_bound_output_not_matching_count',
                'test_family_adjacency.FamilyAdjacencyTests.test_default_both_and_single_hop_scope_are_explicit',
                'test_family_adjacency.FamilyAdjacencyTests.test_default_disabled_does_not_load_core',
                'test_family_adjacency.FamilyAdjacencyTests.test_direct_query_rejects_invalid_values',
                'test_family_adjacency.FamilyAdjacencyTests.test_direction_filters_mixed_graph_without_reversing_predicates',
                'test_family_adjacency.FamilyAdjacencyTests.test_duplicate_assertions_remain_an_error_not_silent_review_merging',
                'test_family_adjacency.FamilyAdjacencyTests.test_existing_concurrency_guard_bounds_neighbor_operations',
                'test_family_adjacency.FamilyAdjacencyTests.test_http_request_is_closed_and_strictly_bounded',
                'test_family_adjacency.FamilyAdjacencyTests.test_incoming_preserves_original_assertion_and_evidence',
                'test_family_adjacency.FamilyAdjacencyTests.test_key_is_assertion_identity_not_evidence_revision',
                'test_family_adjacency.FamilyAdjacencyTests.test_known_empty_is_not_unknown_identity',
                'test_family_adjacency.FamilyAdjacencyTests.test_missing_source_evidence_rejects_index_construction',
                'test_family_adjacency.FamilyAdjacencyTests.test_nested_results_are_defensive_copies',
                'test_family_adjacency.FamilyAdjacencyTests.test_overlay_drift_disables_neighbors_but_preserves_catalog_api',
                'test_family_adjacency.FamilyAdjacencyTests.test_queries_do_not_change_legacy_assertions_memberships_or_counts',
                'test_family_adjacency.FamilyAdjacencyTests.test_revised_overlay_requires_new_relationship_pin',
                'test_family_adjacency.FamilyAdjacencyTests.test_single_hop_does_not_expand_chain_or_cycle',
                'test_family_adjacency.FamilyAdjacencyTests.test_source_target_and_quote_drift_reject_index_construction',
                'test_family_adjacency.FamilyAdjacencyTests.test_stable_keys_and_order_survive_overlay_order_changes',
                'test_family_adjacency.FamilyAdjacencyTests.test_transport_boundaries_apply_to_neighbors')),
 'families': ('experimental/platform/query-service/catalog-tests',
              ('test_family_relationships.FamilyRelationshipTests.test_both_pins_required_and_stale_rejected',
               'test_family_relationships.FamilyRelationshipTests.test_ceramic_is_not_synonym_for_inorganic',
               'test_family_relationships.FamilyRelationshipTests.test_constituent_is_not_identity_or_property_equivalence',
               'test_family_relationships.FamilyRelationshipTests.test_coverage_exact_and_no_count_inflation',
               'test_family_relationships.FamilyRelationshipTests.test_cross_category_polymer_composite_overlap',
               'test_family_relationships.FamilyRelationshipTests.test_default_disabled',
               'test_family_relationships.FamilyRelationshipTests.test_detached_results',
               'test_family_relationships.FamilyRelationshipTests.test_implementation_drift_fails_closed',
               'test_family_relationships.FamilyRelationshipTests.test_inputs_and_unknown_identity',
               'test_family_relationships.FamilyRelationshipTests.test_legacy_categories_remain_exclusive_and_unchanged',
               'test_family_relationships.FamilyRelationshipTests.test_metal_alloy_overlap',
               'test_family_relationships.FamilyRelationshipTests.test_no_formula_or_supplier_semiconductor_inference',
               'test_family_relationships.FamilyRelationshipTests.test_no_role_inference_from_graphite',
               'test_family_relationships.FamilyRelationshipTests.test_overlay_drift_fails_closed_without_breaking_legacy',
               'test_family_relationships.FamilyRelationshipTests.test_overlay_duplicate_keys_and_unknown_fields_rejected',
               'test_family_relationships.FamilyRelationshipTests.test_provenance_resolves_and_quotes_match_for_every_assertion',
               'test_family_relationships.FamilyRelationshipTests.test_review_pins_reject_changed_evidence',
               'test_family_relationships.FamilyRelationshipTests.test_transport_boundaries_inherited',
               'test_family_relationships.FamilyRelationshipTests.test_truncation_is_explicit',
               'test_family_relationships.FamilyRelationshipTests.test_version_binds_policy_and_is_repeatable')),
 'catalog': ('experimental/platform/query-service/catalog-tests',
             ('test_local_catalog.CatalogAPI.test_01_validation_once',
              'test_local_catalog.CatalogAPI.test_02_metadata_counts_and_versions',
              'test_local_catalog.CatalogAPI.test_03_exact_baseline_parity',
              'test_local_catalog.CatalogAPI.test_04_resolution_baseline_parity',
              'test_local_catalog.CatalogAPI.test_05_copy_isolation',
              'test_local_catalog.CatalogAPI.test_06_record_kinds',
              'test_local_catalog.CatalogAPI.test_07_stale_pin',
              'test_local_catalog.CatalogAPI.test_08_missing_pin',
              'test_local_catalog.CatalogAPI.test_09_unknown_id',
              'test_local_catalog.CatalogAPI.test_10_invalid_search',
              'test_local_catalog.CatalogAPI.test_11_no_paths_mutation_or_extra_fields',
              'test_local_catalog.CatalogAPI.test_12_parallel_reads',
              'test_local_catalog.CatalogAPI.test_13_concurrency_bound_release',
              'test_local_catalog.CatalogAPI.test_14_local_origin_and_body_bounds',
              'test_local_catalog.CatalogAPI.test_15_ui_static',
              'test_local_catalog.CatalogAPI.test_16_disabled_mp_unchanged',
              'test_local_catalog.CatalogAPI.test_binary_oxide_growth_six_reference_resolutions',
              'test_local_catalog.CatalogAPI.test_filament_measured_reference_resolutions',
              'test_local_catalog.CatalogAPI.test_mtibe_hybrid_three_reference_resolutions',
              'test_local_catalog.CatalogAPI.test_nbr_rcf_six_reference_resolutions',
              'test_local_catalog.CatalogAPI.test_nbs_source_scoped_density_resolution',
              'test_local_catalog.CatalogAPI.test_nr_nanoclay_six_reference_resolutions',
              'test_local_catalog.CatalogAPI.test_nylon_historical_family_preserves_measured_filament_state',
              'test_local_catalog.CatalogAPI.test_outokumpu_core_ten_reference_resolutions',
              'test_local_catalog.CatalogAPI.test_pa12_source_family_single_identity_resolution',
              'test_local_catalog.CatalogAPI.test_primary_table_growth_eight_salt_resolution',
              'test_local_catalog.CatalogAPI.test_pur_formulation_batch_two_property_resolutions',
              'test_local_catalog.CatalogAPI.test_rca_table_growth_three_reference_resolutions',
              'test_local_catalog.CatalogAPI.test_source_family_growth_six_oxide_resolution',
              'test_local_catalog.CatalogAPI.test_tough_pla_two_states_share_one_identity',
              'test_local_catalog.Initialization.test_default_no_core_load',
              'test_local_catalog.Initialization.test_import_discovery_failure_disabled',
              'test_local_catalog.Initialization.test_missing_core_disabled',
              'test_local_catalog.Initialization.test_revision_module_byte_parity',
              'test_local_catalog.Initialization.test_validation_failure_disabled')),
 'transport': ('experimental/platform/query-service/tests',
               ('test_transport_boundary.FullAppTransportTests.test_application_errors_preserve_semantics_and_release',
                'test_transport_boundary.FullAppTransportTests.test_async_work_timeout_runs_cleanup_and_releases',
                'test_transport_boundary.FullAppTransportTests.test_caller_cancellation_joins_sends_and_releases',
                'test_transport_boundary.FullAppTransportTests.test_closed_send_releases',
                'test_transport_boundary.FullAppTransportTests.test_declared_oversize_rejected_without_receiving',
                'test_transport_boundary.FullAppTransportTests.test_disconnect_during_receive_and_send_releases',
                'test_transport_boundary.FullAppTransportTests.test_exact_body_limit_and_oversize_on_non_body_route',
                'test_transport_boundary.FullAppTransportTests.test_incremental_limit_without_or_with_false_content_length',
                'test_transport_boundary.FullAppTransportTests.test_one_shared_limit_retained_through_body_delivery',
                'test_transport_boundary.FullAppTransportTests.test_origin_host_and_security_headers_cover_boundary_errors',
                'test_transport_boundary.FullAppTransportTests.test_receive_timeout_returns_504_and_releases',
                'test_transport_boundary.FullAppTransportTests.test_send_timeout_cancels_without_second_response_and_releases',
                'test_transport_boundary.FullAppTransportTests.test_stalled_response_start_also_holds_slot',
                'test_transport_boundary.FullAppTransportTests.test_sync_worker_timeout_retains_slots_until_workers_exit',
                'test_transport_boundary.FullAppTransportTests.test_sync_workers_keep_slots_until_cancellation_cleanup',
                'test_transport_boundary.FullAppTransportTests.test_timeout_error_delivery_itself_is_bounded')),
 'baseline': ('experimental/platform/query-service/catalog-tests',
              ('test_catalog_baseline.IntegratedBaselineTests.test_installed_package_matches_exact_new_anchor',
               'test_catalog_baseline.IntegratedBaselineTests.test_changed_core_resource_fails_even_with_unchanged_identity_count',
               'test_catalog_baseline.IntegratedBaselineTests.test_windows_paths_use_the_same_manifest_key'))}

PRESERVED_RESOURCES = (
    'materials_boundaries/data/materials.json',
    'materials_boundaries/data/reference_properties.json',
    'materials_boundaries/data/sources.json',
    'experimental/platform/query-service/materials_query/pins/family_relationships.json',
    'experimental/platform/query-service/materials_query/pins/legacy_baseline.json',
)
IMPLEMENTATION_FILES = (
    'experimental/platform/query-service/materials_query/family_relationships.py',
    'experimental/platform/query-service/materials_query/local_catalog.py',
)


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, timeout=30)


def expected_workflow(baseline):
    """Retain every old job step and add one complementary exact-branch job."""
    validate_targeted_run_scalars(TARGETED_JOB)
    commands = [line.removeprefix('      - run: ') for line in TARGETED_JOB.splitlines()
                if line.startswith('      - run: python -m pip wheel ')]
    require(len(commands) == 1, 'Expected one six-project wheel build')
    validate_wheel_command(commands[0])
    require(baseline.count(PREVIOUS_FULL_JOB_IF) == 2, 'Unexpected frozen full-job guards')
    for name in ('polymer-composites-targeted', 'evidence-batch-targeted',
                 'source-family-growth-targeted', 'pur-formulation-targeted',
                 'primary-table-growth-targeted', 'primary-table-growth-2-targeted',
                 'primary-table-growth-3-targeted', 'primary-table-growth-4-targeted',
                 'primary-table-growth-5-targeted', 'primary-table-growth-6-targeted',
                 'primary-table-growth-7-targeted', 'primary-table-growth-8-targeted',
                 'zenodo-identity-followup-targeted', 'zenodo-nylon-followup-targeted'):
        require(baseline.count('  ' + name + ':\n') == 1, 'Missing previous experiment job: ' + name)
    require('  family-adjacency-targeted:\n' not in baseline, 'Predecessor already contains this job')
    for name in ('unit-and-schema', 'windows-composite'):
        marker = '  ' + name + ':\n' + PREVIOUS_FULL_JOB_IF
        require(baseline.count(marker) == 1, 'Unexpected predecessor job block: ' + name)
        baseline = baseline.replace(marker, '  ' + name + ':\n' + FULL_JOB_IF, 1)
    return baseline + TARGETED_JOB


def validate_names(names, *, root=ROOT):
    require(all(type(name) is str for name in names), 'Changed paths must be strings')
    unexpected = sorted(set(names) - APPROVED_FILES)
    require(not unexpected, 'Changes exceed family adjacency scope: ' + ', '.join(unexpected))
    for name in names:
        path = root / name
        require(not path.is_symlink() and path.is_file() and path.resolve().is_relative_to(root.resolve()),
                'Approved path must remain a regular repository file: ' + name)


def validate_event(head):
    if os.environ.get('GITHUB_ACTIONS') == 'true':
        require(os.environ.get('GITHUB_EVENT_NAME') == 'push', 'Scoped CI requires a push event')
        require(os.environ.get('GITHUB_REF') == BRANCH_REF, 'Scoped CI requires its exact experiment branch')
        require(os.environ.get('GITHUB_SHA') == head, 'Checkout differs from the pushed GITHUB_SHA')
        require(not git('status', '--porcelain', '--untracked-files=normal'), 'Scoped CI checkout must be clean')


def validate_scope():
    head = git('rev-parse', 'HEAD').decode().strip()
    subprocess.run(['git', 'merge-base', '--is-ancestor', BASE_COMMIT, head], cwd=ROOT, check=True, timeout=30)
    validate_event(head)
    names = set(changed_paths(git('diff', '--name-status', '--no-renames', '-z', BASE_COMMIT, 'HEAD', '--')))
    names.update(changed_paths(git('diff', '--name-status', '--no-renames', '-z', 'HEAD', '--')))
    names.update(name for name in git('ls-files', '--others', '--exclude-standard', '-z').decode('utf-8').split('\0') if name)
    validate_names(names)
    baseline = git('show', BASE_COMMIT + ':.github/workflows/ci.yml').decode('utf-8')
    require((ROOT / '.github/workflows/ci.yml').read_bytes().decode('utf-8') == expected_workflow(baseline),
            'Workflow differs from the exact predecessor plus family adjacency job')
    preserved = {}
    for name in PRESERVED_RESOURCES:
        raw = (ROOT / name).read_bytes()
        require(raw == git('show', BASE_COMMIT + ':' + name), 'Catalog/review input changed: ' + name)
        preserved[name] = sha256(raw).hexdigest()
    result = {'base_commit': BASE_COMMIT, 'head': head, 'branch_ref': BRANCH_REF,
              'changed_files': sorted(names), 'preserved_resources': preserved,
              'old_job_steps_preserved': True, 'previous_experiment_jobs_preserved': True,
              'exact_targeted_job_preserved': True, 'new_identities': 0}
    print(json.dumps(result, indent=2), flush=True)
    return result


def run_group(name):
    install_offline_guard()
    relative, expected = TEST_GROUPS[name]
    require(expected and len(expected) == len(set(expected)), 'Exact inventory is empty or duplicated: ' + name)
    if name == 'core':
        sys.path.insert(0, str(ROOT))
    else:
        require(sys.prefix != sys.base_prefix, 'Selected package checks require a fresh installation')
        require(str(ROOT) not in sys.path, 'Checkout root must not shadow installed packages')
        installed_origins()
    sys.path.insert(0, str(ROOT / relative))
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromNames(list(expected))
    require(not loader.errors, 'Selected test loading failed: ' + '\n'.join(loader.errors))
    discovered = list(test_ids(suite))
    require(discovered == list(expected), 'Discovery differs from the fixed inventory')
    print('DISCOVERED ' + json.dumps({'group': name, 'test_ids': discovered}, sort_keys=True), flush=True)
    result = unittest.TextTestRunner(verbosity=2, resultclass=ExactResult, failfast=False).run(suite)
    require(result.testsRun == len(expected) and result.started_ids == discovered
            and result.passed_ids == discovered and result.wasSuccessful()
            and not result.skipped and not result.expectedFailures and not result.unexpectedSuccesses,
            name + ': discovered/started/passed IDs differ, or failures/errors/skips occurred')
    if name != 'core':
        installed_origins()
    print('TARGETED ' + json.dumps({'group': name, 'passed': result.testsRun, 'skipped': 0,
                                    'failed': 0, 'errors': 0, 'test_ids': discovered}, sort_keys=True), flush=True)


def installation_payload():
    hashes = {}
    for name in (*PRESERVED_RESOURCES, *IMPLEMENTATION_FILES):
        package_name = 'materials_boundaries' if name.startswith('materials_boundaries/') else 'materials_query'
        package_path = name.split(package_name + '/', 1)[1]
        hashes[package_name + '/' + package_path] = sha256((ROOT / name).read_bytes()).hexdigest()
    return {'resource_hashes': hashes, 'packages': [package for _, _, package in PACKAGES]}


INSTALLED_SMOKE = r'''
from hashlib import sha256
from importlib.resources import files
import importlib
import json
from pathlib import Path
import sys

def require(condition, message):
    if not condition:
        raise RuntimeError(message)

expected = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
for name in expected['packages']:
    package = importlib.import_module(name)
    require(Path(package.__file__).resolve().is_relative_to(Path(sys.prefix).resolve()),
            'Checkout package imported: ' + name)
for name, digest in expected['resource_hashes'].items():
    package, relative = name.split('/', 1)
    require(sha256(files(package).joinpath(*relative.split('/')).read_bytes()).hexdigest() == digest,
            'Installed resource bytes differ: ' + name)
from materials_project_catalog.catalog import formal_project_catalog
counts = formal_project_catalog()['counts']
require(counts == {'formal_project_admission_count': 1168, 'legacy_source_qualified_identity_count': 1144,
                  'reviewed_computed_composition_count': 24,
                  'categories': {'metal': 44, 'polymer': 25, 'inorganic': 61, 'natural': 1010, 'composite': 28}},
        'Existing formal admission boundary changed')
print(json.dumps({'fresh_install': True, 'new_identities': 0, 'counts': counts,
                  'resource_hashes': expected['resource_hashes'],
                  'scope': 'Byte-identical catalog and reviewed inputs; API tests run separately.'}))
'''


def check_installed(wheel_dir, dependency_dir):
    wheels = verify_wheels(wheel_dir)
    require(dependency_dir.is_dir() and any(dependency_dir.glob('*.whl')), 'Offline dependency wheels are missing')
    env = clean_env()
    with tempfile.TemporaryDirectory(prefix='family-adjacency-installed-') as temporary:
        work = Path(temporary)
        runtime = work / 'runtime'
        venv.EnvBuilder(with_pip=True, system_site_packages=False).create(runtime)
        python = runtime / ('Scripts/python.exe' if sys.platform == 'win32' else 'bin/python')
        run([python, '-I', '-m', 'pip', '--isolated', 'install', '--no-index', '--no-deps', '--find-links', dependency_dir,
             '-r', ROOT / 'experimental/platform/requirements-lock.txt',
             '-r', ROOT / 'experimental/platform/ci/projection-requirements.txt'], cwd=work, env=env)
        run([python, '-I', '-m', 'pip', '--isolated', 'install', '--no-index', '--no-deps', *wheels], cwd=work, env=env)
        run([python, '-I', '-m', 'pip', 'check'], cwd=work, env=env)
        expected = work / 'expected.json'
        expected.write_text(json.dumps(installation_payload()), encoding='utf-8')
        smoke = work / 'installed_smoke.py'
        smoke.write_text(inspect.getsource(install_offline_guard) + '\ninstall_offline_guard()\n' + INSTALLED_SMOKE,
                         encoding='utf-8')
        run([python, '-I', smoke, expected], cwd=work, env=env)
        for group in TEST_GROUPS:
            if group != 'core':
                run([python, '-I', '-B', Path(__file__).resolve(), '--installed-group', group], cwd=work, env=env)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument('--validate-scope', action='store_true')
    actions.add_argument('--test', action='store_true')
    actions.add_argument('--wheel-dir', type=Path)
    actions.add_argument('--installed-group', choices=tuple(name for name in TEST_GROUPS if name != 'core'))
    parser.add_argument('--dependency-dir', type=Path)
    args = parser.parse_args()
    if args.installed_group:
        run_group(args.installed_group)
        return
    validate_scope()
    if args.test:
        run_group('core')
    elif args.wheel_dir:
        require(args.dependency_dir is not None, '--wheel-dir requires --dependency-dir')
        check_installed(args.wheel_dir.resolve(), args.dependency_dir.resolve())
    elif args.dependency_dir:
        parser.error('--dependency-dir requires --wheel-dir')


if __name__ == '__main__':
    main()
