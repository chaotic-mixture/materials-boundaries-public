#!/usr/bin/env python3
"""Exact Bruns +4 append, full source tests and fresh six-wheel offline suites.

Only the named experimental push skips the unchanged general jobs. Every source
and platform suite has a frozen sorted-ID fingerprint, not a test-count minimum.
Checkout-only ingestion/projection helpers are not installed product interfaces.
Platform/external-fixture skips have exact IDs/reasons and are not counted as passes.
"""
import argparse
import ast
from collections import Counter
from copy import deepcopy
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
from run_family_adjacency_ci import (
    BRANCH_REF as PREVIOUS_BRANCH_REF, BUILD_COMMAND,
    FULL_JOB_IF as PREVIOUS_FULL_JOB_IF, TARGETED_JOB as PREVIOUS_TARGETED_JOB,
    changed_paths, validate_targeted_run_scalars, validate_wheel_command,
)
from run_evidence_batch_ci import (
    ExactResult, PACKAGES, clean_env, install_offline_guard, installed_origins,
    require, run, sha256, test_ids, verify_wheels,
)

BASE_COMMIT = '46674771ab851d4c267425b985c8f29c8aea25df'
BRANCH_REF = 'refs/heads/experimental/borosilicate-growth-bruns2020'
FULL_JOB_IF = PREVIOUS_FULL_JOB_IF.replace("') }}\n", "' && github.ref != '" + BRANCH_REF + "') }}\n")
TARGETED_JOB = (PREVIOUS_TARGETED_JOB
                .replace('  family-adjacency-targeted:\n', '  bruns-borosilicate-targeted:\n')
                .replace(PREVIOUS_BRANCH_REF, BRANCH_REF)
                .replace('run_family_adjacency_ci.py', 'run_bruns_borosilicate_ci.py'))
PREVIOUS_JOBS = (
    'polymer-composites-targeted', 'evidence-batch-targeted',
    'source-family-growth-targeted', 'pur-formulation-targeted',
    'primary-table-growth-targeted', 'primary-table-growth-2-targeted',
    'primary-table-growth-3-targeted', 'primary-table-growth-4-targeted',
    'primary-table-growth-5-targeted', 'primary-table-growth-6-targeted',
    'primary-table-growth-7-targeted', 'primary-table-growth-8-targeted',
    'zenodo-identity-followup-targeted', 'zenodo-nylon-followup-targeted',
    'family-adjacency-targeted',
)
APPROVED_FILES = frozenset([
    '.github/workflows/ci.yml',
    'README.md',
    'THIRD_PARTY_NOTICES.md',
    'experimental/material-batches/bruns-nbs2-borosilicate-20261023/INTEGRATION.md',
    'experimental/material-batches/bruns-nbs2-borosilicate-20261023/README.md',
    'experimental/material-batches/bruns-nbs2-borosilicate-20261023/VALIDATION.md',
    'experimental/material-batches/bruns-nbs2-borosilicate-20261023/integration-report.json',
    'experimental/material-batches/bruns-nbs2-borosilicate-20261023/integration-validation-results.json',
    'experimental/material-batches/bruns-nbs2-borosilicate-20261023/integration.json',
    'experimental/material-batches/bruns-nbs2-borosilicate-20261023/packet-spec.json',
    'experimental/material-batches/bruns-nbs2-borosilicate-20261023/preparation-receipt.json',
    'experimental/material-batches/bruns-nbs2-borosilicate-20261023/prepared-packet.json',
    'experimental/material-batches/bruns-nbs2-borosilicate-20261023/source-review.json',
    'experimental/material-batches/bruns-nbs2-borosilicate-20261023/validation-results.json',
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
    'experimental/platform/query-service/catalog-tests/test_bruns_borosilicate.py',
    'experimental/platform/query-service/catalog-tests/test_catalog_baseline.py',
    'experimental/platform/query-service/catalog-tests/test_combined_admission_boundary.py',
    'experimental/platform/query-service/catalog-tests/test_computed_recovery.py',
    'experimental/platform/query-service/catalog-tests/test_computed_v2_second_tranche.py',
    'experimental/platform/query-service/catalog-tests/test_computed_v2_tranche.py',
    'experimental/platform/query-service/catalog-tests/test_family_adjacency.py',
    'experimental/platform/query-service/catalog-tests/test_family_relationships.py',
    'experimental/platform/query-service/catalog-tests/test_formal_project_catalog.py',
    'experimental/platform/query-service/catalog-tests/test_local_catalog.py',
    'experimental/platform/query-service/materials_query/computed_registry.py',
    'experimental/platform/query-service/materials_query/pins/legacy_baseline.json',
    'experimental/platform/relationships/HBN_PROJECTION.md',
    'experimental/platform/relationships/test_hbn_relationship_projection.py',
    'formal-catalog/README.md',
    'formal-catalog/materials_project_catalog/catalog.py',
    'formal-catalog/tests/test_formal_project_core.py',
    'materials_boundaries/data/materials.json',
    'materials_boundaries/data/reference_properties.json',
    'materials_boundaries/data/sources.json',
    'scripts/run_bruns_borosilicate_ci.py',
    'tests/fixtures/bruns_borosilicate_data_20261023.json',
    'tests/fixtures/bruns_borosilicate_files_20261023.json',
    'tests/fixtures/legacy_document_call_sites_20261023.json',
    'tests/fixtures/legacy_document_recovery_20261023.json',
    'tests/legacy_document_recovery.py',
    'tests/material_append_successors.py',
    'tests/material_bulk_preservation.py',
    'tests/material_class_counts_preservation.py',
    'tests/test_bruns_borosilicate_ci.py',
    'tests/test_bruns_borosilicate_packet.py',
    'tests/test_bruns_borosilicate_preservation.py',
    'tests/test_family_adjacency_ci.py',
    'tests/test_family_adjacency_history.py',
    'tests/test_legacy_document_recovery.py',
    'tests/test_material_class_counts_preservation.py',
])

# Complete suite inventories: directory, exact count, SHA-256 of sorted IDs
# encoded as UTF-8 with one trailing newline per ID. No discovered test may
# disappear, be renamed, or be substituted; every skip needs its exact policy.
TEST_GROUPS = {'core': ('tests', 1716,
          '828a83dbc4a78f07ac115f472436c888242ea7e5642985c05f0d4afcc36e533d'),
 'query': ('experimental/platform/query-service/catalog-tests',
           214,
           '53f6774fd72799d0abdb9038924eb74b3298018094408e154ab3f69208ca2450'),
 'formal': ('formal-catalog/tests', 12, '05fd6bb5c18b2b0d543d7d5e5e4b14fb69aff8766ca8bc75ecc236e2dc6e2d1a'),
 'ingestion': ('experimental/platform/ingestion',
               196,
               'f71c08543f3f88c6af71e8702e647d93613eb96d8c59566107a7a0aa1abf6045'),
 'relationships': ('experimental/platform/relationships',
                   14,
                   'ee52759a66ac42805869f8bce7a1dc2c6d7b9507f381c158e84ee854c6bcc936'),
 'provider': ('experimental/platform/federation/tests',
              19,
              '60c12178318c669c29320d1ed385a6a05347c5a397f7f3628bd0be4d9bafe669'),
 'transport': ('experimental/platform/query-service/tests',
               37,
               '6ea89371eae5ef5b84607b6890c305d92e85d7a632fd74572a5f9e0746629c4f'),
 'lifecycle': ('experimental/platform/lifecycle/tests',
               25,
               '8017cf5a6cc1324a6eb3fbbd24c66499a66a4f5e035892ae7c1cc1459d77ecee'),
 'integration': ('experimental/platform/tests',
                 18,
                 'fdff229979a751083a10a2c9cb781692d8793d21b6187f230f732d0ac37dc43d')}
PACKET_PATH = 'experimental/material-batches/bruns-nbs2-borosilicate-20261023/prepared-packet.json'
PACKET_SHA256 = '7bc0fb2ba2dc3512abb95b7bf27b9f25d12c868d4bba041f667421572e5eccde'
BASELINE_HASHES = {
    'materials': 'd228c3b8f0c45fd56809891213d1d1acd73964357b579c51f8b9c731031a3ec5',
    'reference_properties': '66802278a29cdcc4a5fe468b5681d87893a8a10a7c6c4c57f83c4753fe807839',
    'sources': '67e068041af0cd8dbaba1126e6ffe2e39d2f8d26f8d2c8ceefc42240e5eefe76',
}
RESOURCE_HASHES = {
    'materials.json': '9df59cfdf94b35854255222d2a75f419859b269c5670c8eb18d8e9dc5eaa7a70',
    'reference_properties.json': '728c863756c35860b4dee25b64f5df10c1b5273bcb83ed1f35d60cf6ad85aa77',
    'sources.json': 'c06c9bcee46eac59839c51f84b252970f1da46f98cf2f2c08de0b33479b5ba71',
}
QUERY_BASELINE_SHA256 = '09b57c7410b7b6c858abd566153dd932a451c9b5d4ed56b0963cbe4064543a05'
GRAPH_COUNTS = {'identity': 1148, 'grade': 31, 'state': 1149, 'property': 1160, 'source': 124}
DELTA_COUNTS = {'identity': 4, 'grade': 0, 'state': 4, 'property': 4, 'source': 1}
PRIMARY_COUNTS = {'metal': 32, 'inorganic': 53, 'polymer': 25, 'composite': 28, 'natural': 1010}
FORMAL_COUNTS = {
    'formal_project_admission_count': 1172, 'legacy_source_qualified_identity_count': 1148,
    'reviewed_computed_composition_count': 24,
    'categories': {'metal': 44, 'inorganic': 65, 'polymer': 25, 'composite': 28, 'natural': 1010},
}
PRESERVED_RESOURCES = (
    'experimental/platform/query-service/materials_query/pins/family_relationships.json',
    'formal-catalog/materials_project_catalog/data/formal_computed_review.json',
    'materials_boundaries/data/observations.json',
    'materials_boundaries/data/computational_predictions.json',
    'experimental/platform/examples/reviewed-computed-v2-second/normalized-review.json',
    'experimental/platform/examples/reviewed-computed-seed/scoped-review-input.json',
)


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, timeout=30)


def expected_workflow(baseline):
    """Every preexisting job is byte-identical except complementary guards."""
    validate_targeted_run_scalars(TARGETED_JOB)
    commands = [line.removeprefix('      - run: ') for line in TARGETED_JOB.splitlines()
                if line.startswith('      - run: python -m pip wheel ')]
    require(commands == [BUILD_COMMAND], 'Expected the exact six-project wheel build')
    validate_wheel_command(commands[0])
    require(baseline.count(PREVIOUS_FULL_JOB_IF) == 2, 'Unexpected frozen full-job guards')
    for name in PREVIOUS_JOBS:
        require(baseline.count('  ' + name + ':\n') == 1, 'Missing previous experiment job: ' + name)
    require('  bruns-borosilicate-targeted:\n' not in baseline, 'Predecessor already contains this job')
    for name in ('unit-and-schema', 'windows-composite'):
        marker = '  ' + name + ':\n' + PREVIOUS_FULL_JOB_IF
        require(baseline.count(marker) == 1, 'Unexpected predecessor job block: ' + name)
        baseline = baseline.replace(marker, '  ' + name + ':\n' + FULL_JOB_IF, 1)
    return baseline + TARGETED_JOB


def validate_names(names, *, root=ROOT):
    require(all(type(name) is str for name in names), 'Changed paths must be strings')
    require(APPROVED_FILES, 'Approved file inventory is not frozen')
    unexpected = sorted(set(names) - APPROVED_FILES)
    require(not unexpected, 'Changes exceed Bruns integration scope: ' + ', '.join(unexpected))
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
    names.update(name for name in git('ls-files', '--others', '--exclude-standard', '-z').decode().split('\0') if name)
    validate_names(names)
    prior = git('show', BASE_COMMIT + ':.github/workflows/ci.yml').decode('utf-8')
    require((ROOT / '.github/workflows/ci.yml').read_bytes().decode('utf-8') == expected_workflow(prior),
            'Workflow differs from the exact predecessor plus Bruns integration job')
    payload = installation_payload()
    result = {'base_commit': BASE_COMMIT, 'head': head, 'branch_ref': BRANCH_REF,
              'changed_files': sorted(names), 'old_job_steps_preserved': True,
              'previous_experiment_jobs_preserved': True, 'exact_targeted_job_preserved': True,
              'packet_sha256': PACKET_SHA256, 'delta_counts': DELTA_COUNTS,
              'graph_counts': GRAPH_COUNTS, 'formal_counts': FORMAL_COUNTS,
              'query_baseline': payload['query_baseline'], 'resource_hashes': payload['resource_hashes']}
    print(json.dumps(result, indent=2), flush=True)
    return result


def inventory_fingerprint(ids):
    return sha256(''.join(identifier + '\n' for identifier in sorted(ids)).encode('utf-8')).hexdigest()


def validate_inventory(name, ids):
    _, count, digest = TEST_GROUPS[name]
    require(count > 0 and len(digest) == 64, 'Complete inventory is not frozen: ' + name)
    require(len(ids) == len(set(ids)) == count and inventory_fingerprint(ids) == digest,
            'Complete inventory differs from the fixed sorted-ID fingerprint: ' + name)


def declared_test_ids(relative, *, predecessor=False):
    """Independent declared-ID oracle used by regression tests, not discovery."""
    names = (git('ls-tree', '-r', '--name-only', BASE_COMMIT, '--', relative).decode().splitlines()
             if predecessor else [path.relative_to(ROOT).as_posix() for path in (ROOT / relative).glob('test*.py')])
    result = []
    for name in sorted(names):
        path = Path(name)
        if path.parent.as_posix() != relative or not path.name.startswith('test') or path.suffix != '.py':
            continue
        raw = git('show', BASE_COMMIT + ':' + name) if predecessor else (ROOT / name).read_bytes()
        for node in ast.parse(raw).body:
            if isinstance(node, ast.ClassDef):
                result.extend(path.stem + '.' + node.name + '.' + method.name for method in node.body
                              if isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef))
                              and method.name.startswith('test'))
    return sorted(result)

# These are unavailable test executions, never successful platform evidence.
WINDOWS_ONLY_TESTS = dict.fromkeys((
    'test_composite_windows.NativeWindowsExportTests.test_blank_demo_report_replay_and_existing_output_refusal',
    'test_composite_windows.NativeWindowsExportTests.test_every_pinned_ancestor_refuses_rename_and_handles_close',
    'test_composite_windows.NativeWindowsExportTests.test_existing_empty_destination_and_staging_file_collision',
    'test_composite_windows.NativeWindowsExportTests.test_extended_length_local_path',
    'test_composite_windows.NativeWindowsExportTests.test_junction_ancestor_and_output_refused',
    'test_composite_windows.NativeWindowsExportTests.test_partial_directory_open_failure_closes_ancestors',
    'test_composite_windows.NativeWindowsExportTests.test_publish_failure_manifest_last_rollback_all_positions',
    'test_composite_windows.NativeWindowsExportTests.test_published_replacement_and_unrelated_addition_preserved',
    'test_composite_windows.NativeWindowsExportTests.test_relative_and_unicode_paths',
    'test_composite_windows.NativeWindowsExportTests.test_replaced_input_stage_is_rejected_before_publication',
    'test_composite_windows.NativeWindowsExportTests.test_replaced_stage_is_rejected_before_publication',
    'test_composite_windows.NativeWindowsExportTests.test_root_and_stage_open_failure_cleanup_and_release',
    'test_composite_windows.NativeWindowsExportTests.test_stage_write_failures_and_input_fsync_close_before_cleanup',
    'test_composite_windows.NativeWindowsExportTests.test_staging_collision_and_replacement_are_not_deleted',
    'test_composite_windows.NativeWindowsExportTests.test_symlink_and_dangling_leaf_refused',
    'test_composite_windows.NativeWindowsExportTests.test_transient_cleanup_failure_rolls_back_manifest_and_retries',
    'test_composite_windows.NativeWindowsExportTests.test_zero_file_identity_fails_closed_without_deleting_unknown_file',
), 'requires actual native Windows on local NTFS')
POSIX_ONLY_TESTS = {
    **dict.fromkeys((
        'test_composite_export.ExportTests.test_cleanup_failure_rolls_back_manifest_then_retries_owned_stage',
        'test_composite_export.ExportTests.test_concurrent_unrelated_file_is_preserved',
        'test_composite_export.ExportTests.test_exclusive_name_collision_does_not_delete_other_input',
        'test_composite_export.ExportTests.test_publish_failures_manifest_last_and_rollback',
        'test_composite_export.ExportTests.test_rollback_does_not_delete_replacement',
        'test_composite_export.ExportTests.test_stage_failures_clean_only_own_data',
        'test_composite_export.ExportTests.test_stage_open_failure_removes_created_empty_stage',
        'test_composite_export.ExportTests.test_symlink_output_and_ancestor_and_traversal_refused',
    ), 'POSIX backend; native Windows coverage is separate'),
    **dict.fromkeys((
        'test_composite_intake.CompositeIntakePTYTests.test_cli_redirected_input_is_rejected_without_file',
        'test_composite_intake.CompositeIntakePTYTests.test_real_terminal_back_edit_and_confirm_save',
        'test_composite_intake.CompositeIntakePTYTests.test_real_terminal_cancel_and_sigint_leave_no_file',
    ), 'requires POSIX pseudo-terminal'),
    **dict.fromkeys((
        'test_material_coverage.RuntimeBenchmarkFixtureTests.test_fictional_fixture_limits_reject_invalid_sizes',
        'test_material_coverage.RuntimeBenchmarkFixtureTests.test_fictional_scaling_is_valid_deterministic_detached_and_clearly_labeled',
    ), 'RSS benchmark uses the POSIX resource module'),
}
NON_WINDOWS_GUARD = (
    'test_composite_windows.WindowsSpellingTests.test_native_api_is_not_emulated_as_platform_support'
)
EXTERNAL_DOSSIER_TEST = (
    'test_wood_bulk_adapter.ReviewedWoodAdapterTests.test_full_external_dossier_source_support_without_admission'
)
WINDOWS_SYMLINK_TEST = (
    'test_composite_windows.NativeWindowsExportTests.test_symlink_and_dangling_leaf_refused'
)


def source_skip_contract(*, platform_name=None, dossier_enabled=None):
    platform_name = os.name if platform_name is None else platform_name
    dossier_enabled = bool(os.environ.get('WOOD_REVIEW_DOSSIER')) if dossier_enabled is None else dossier_enabled
    require(platform_name in {'posix', 'nt'}, 'Unreviewed platform skip policy')
    mandatory = dict(WINDOWS_ONLY_TESTS if platform_name == 'posix' else POSIX_ONLY_TESTS)
    optional = {}
    if platform_name == 'nt':
        mandatory[NON_WINDOWS_GUARD] = 'non-Windows guard only'
        optional[WINDOWS_SYMLINK_TEST] = 'Windows symlink privilege unavailable; mandatory junction tests still run'
    if not dossier_enabled:
        mandatory[EXTERNAL_DOSSIER_TEST] = 'external frozen source-cache integration is opt-in'
    return mandatory, optional


def validate_result(name, discovered, result, *, skip_contract=None):
    mandatory, optional = skip_contract if skip_contract is not None else ({}, {})
    require(name == 'core' or not (mandatory or optional), 'Installed suites cannot allow skips')
    observed = [(test.id(), reason) for test, reason in result.skipped]
    skipped = dict(observed)
    require(len(observed) == len(skipped), 'Duplicate skipped test ID')
    require(set(mandatory).issubset(skipped), 'Missing mandatory unavailable-platform/fixture skip')
    allowed = {**mandatory, **optional}
    require(all(identifier in discovered and identifier in allowed and reason == allowed[identifier]
                for identifier, reason in observed), 'Unexpected skip, reason drift or wrong platform')
    passed = [identifier for identifier in discovered if identifier not in skipped]
    require(result.testsRun == len(discovered) and result.started_ids == discovered
            and result.passed_ids == passed and result.wasSuccessful()
            and not result.expectedFailures and not result.unexpectedSuccesses,
            name + ': discovered/started/passed/skipped IDs differ, or failures/errors occurred')
    return {'group': name, 'discovered': len(discovered), 'started': result.testsRun,
            'passed': len(result.passed_ids), 'skipped': len(skipped), 'failed': 0, 'errors': 0,
            'skipped_tests': [{'test_id': identifier, 'reason': reason} for identifier, reason in observed],
            'inventory_sha256': inventory_fingerprint(discovered)}


def run_group(name):
    install_offline_guard()
    import socket
    try:
        socket.getaddrinfo('ci-guard.invalid', 443)
    except RuntimeError as error:
        require('Offline fixture CI' in str(error), 'Wrong offline guard failure')
    else:
        raise RuntimeError('Offline guard did not block DNS')
    relative, _, _ = TEST_GROUPS[name]
    skip_policy = source_skip_contract() if name == 'core' else ({}, {})
    if name == 'core':
        sys.path.insert(0, str(ROOT))
    else:
        require(sys.prefix != sys.base_prefix, 'Package checks require a fresh installation')
        require(str(ROOT) not in sys.path, 'Checkout root must not shadow installed packages')
        installed_origins()
    loader = unittest.TestLoader()
    suite = loader.discover(str(ROOT / relative), pattern='test*.py')
    require(not loader.errors, 'Complete test loading failed: ' + '\n'.join(loader.errors))
    discovered = list(test_ids(suite))
    validate_inventory(name, discovered)
    print('DISCOVERED ' + json.dumps({'group': name, 'count': len(discovered), 'test_ids': discovered}, sort_keys=True), flush=True)
    result = unittest.TextTestRunner(verbosity=2, resultclass=ExactResult, failfast=False).run(suite)
    summary = validate_result(name, discovered, result, skip_contract=skip_policy)
    if name != 'core':
        installed_origins()
    print('COMPLETE ' + json.dumps(summary, sort_keys=True), flush=True)


def table_rows(graphs):
    return {'identity': graphs['materials']['identities'], 'grade': graphs['materials']['grades'],
            'state': graphs['materials']['records'], 'property': graphs['properties']['records'],
            'source': graphs['sources']['records']}


def validate_append(candidate, before, current):
    """Reject count-preserving rewrites, partial appends, reordered rows and metadata drift."""
    wanted = deepcopy(before)
    for graph, fields in (('materials', ('identities', 'grades', 'records')),
                          ('properties', ('records',)), ('sources', ('records',))):
        for field in fields:
            previous = wanted[graph][field]
            added = candidate[graph][field]
            require(len({row['id'] for row in added}) == len(added), 'Duplicate packet record')
            require(not ({row['id'] for row in previous} & {row['id'] for row in added}), 'Packet ID already exists')
            previous.extend(deepcopy(added))
    require(current == wanted, 'Runtime differs from exact predecessor plus complete frozen append')
    require({kind: len(rows) for kind, rows in table_rows(candidate).items()} == DELTA_COUNTS,
            'Frozen packet delta changed')
    require({kind: len(rows) for kind, rows in table_rows(current).items()} == GRAPH_COUNTS,
            'Current graph counts changed')
    require(dict(Counter(row['category'] for row in current['materials']['identities'])) == PRIMARY_COUNTS,
            'Current exclusive primary categories changed')


def installation_payload():
    raw = (ROOT / PACKET_PATH).read_bytes()
    require(sha256(raw).hexdigest() == PACKET_SHA256, 'Reviewed Bruns packet bytes changed')
    packet = json.loads(raw)
    require(packet['input']['baseline_sha256'] == BASELINE_HASHES, 'Packet predecessor hashes changed')
    before, current = {}, {}
    for kind, filename in (('materials', 'materials.json'), ('properties', 'reference_properties.json'), ('sources', 'sources.json')):
        old = git('show', BASE_COMMIT + ':materials_boundaries/data/' + filename)
        new = (ROOT / 'materials_boundaries/data' / filename).read_bytes()
        require(sha256(old).hexdigest() == BASELINE_HASHES[filename[:-5]], 'Predecessor resource pin differs')
        require(sha256(new).hexdigest() == RESOURCE_HASHES[filename], 'Current resource pin differs: ' + filename)
        before[kind], current[kind] = json.loads(old), json.loads(new)
    validate_append(packet['catalogs'], before, current)
    baseline = ROOT / 'experimental/platform/query-service/materials_query/pins/legacy_baseline.json'
    require(sha256(baseline.read_bytes()).hexdigest() == QUERY_BASELINE_SHA256, 'Current query baseline pin changed')
    preserved = {}
    for name in PRESERVED_RESOURCES:
        raw = (ROOT / name).read_bytes()
        require(raw == git('show', BASE_COMMIT + ':' + name), 'Reviewed or excluded resource changed: ' + name)
        preserved[name] = sha256(raw).hexdigest()
    examples = json.loads((ROOT / 'experimental/platform/examples/reviewed-computed-v2-second/normalized-review.json').read_bytes())
    require(len(examples['records']) == 62, 'Excluded examples acquired admission or changed count')
    manifest = json.loads((ROOT / PACKET_PATH).with_name('integration.json').read_bytes())
    require(manifest['released_main_count'] == 1081, 'Released main count changed')
    return {'candidate': packet['catalogs'], 'resource_hashes': RESOURCE_HASHES,
            'excluded_examples': 62, 'released_main_count': 1081,
            'delta_counts': DELTA_COUNTS, 'graph_counts': GRAPH_COUNTS,
            'primary_counts': PRIMARY_COUNTS, 'formal_counts': FORMAL_COUNTS,
            'query_baseline': QUERY_BASELINE_SHA256, 'preserved_resources': preserved,
            'packages': [package for _, _, package in PACKAGES]}


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

expected = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
for name in expected['packages']:
    package = importlib.import_module(name)
    require(Path(package.__file__).resolve().is_relative_to(Path(sys.prefix).resolve()), 'Checkout package imported: ' + name)
from materials_boundaries.catalog import read_catalog, query_catalog
from materials_boundaries.cli import main
from materials_project_catalog.catalog import formal_project_catalog
from materials_query.computed_registry import baseline_digest
for name, digest in expected['resource_hashes'].items():
    require(sha256(files('materials_boundaries').joinpath('data', name).read_bytes()).hexdigest() == digest,
            'Installed catalog bytes differ: ' + name)
materials, properties, sources = (read_catalog(name) for name in ('materials', 'reference_properties', 'sources'))
tables = {'identity': materials['identities'], 'grade': materials['grades'], 'state': materials['records'],
          'property': properties['records'], 'source': sources['records']}
candidate = expected['candidate']
frozen = {'identity': candidate['materials']['identities'], 'grade': candidate['materials']['grades'],
          'state': candidate['materials']['records'], 'property': candidate['properties']['records'],
          'source': candidate['sources']['records']}
require({kind: len(rows) for kind, rows in tables.items()} == expected['graph_counts'], 'Installed graph counts differ')
require(dict(Counter(row['category'] for row in tables['identity'])) == expected['primary_counts'], 'Installed categories differ')
for kind, rows in frozen.items():
    for row in rows:
        require([value for value in tables[kind] if value['id'] == row['id']] == [row], 'Installed complete packet record differs')
outputs = 0
for prop in frozen['property']:
    require(prop['evaluation_support'] == 'catalog_only' and not prop['universal_bound']
            and not prop['engineering_allowable'] and not prop['verification']['independent_scientific_review']
            and not prop['verification']['raw_data_reanalysis'], 'Density gained unsupported scientific capabilities')
    require(prop['quantity'] == 'mass_density' and prop['summary_statistic'] == 'reported_mean'
            and prop['uncertainty']['type'] == 'reported_standard_deviation'
            and prop['reported_value']['unit_code'] == 'g/cm^3'
            and prop['sample_count']['value'] is None and prop['sample_count']['relation'] == 'not_reported'
            and prop['density_basis'] == 'not_stated', 'Source-qualified density semantics changed')
    selected = query_catalog('reference-properties', record_id=prop['id'])
    for language in ('en', 'zh', 'ja', 'de'):
        for flag in ('--json', '--text'):
            output = io.StringIO()
            with redirect_stdout(output):
                code = main(['catalog', 'reference-properties', '--id', prop['id'], '--lang', language, flag])
            text = output.getvalue()
            require(code == 0 and '[missing:' not in text, 'Installed density CLI failed')
            if flag == '--json':
                require(json.loads(text) == selected, 'Installed JSON depends on language')
            else:
                require(prop['reported_value']['value_text'] in text and prop['uncertainty_note'] in text,
                        'Reported density or caveat missing from text')
            outputs += 1
formal = formal_project_catalog()
require(formal['counts'] == expected['formal_counts'], 'Installed formal boundary changed')
for row in frozen['identity']:
    require(len([entry for entry in formal['records'] if entry['partition'] == 'legacy-source-qualified'
                 and entry['identity']['id'] == row['id']]) == 1, 'Recipe contributes multiple formal identities')
require(baseline_digest() == expected['query_baseline'], 'Installed query baseline differs')
print(json.dumps({'fresh_install': True, 'delta_counts': expected['delta_counts'],
                  'formal_counts': formal['counts'], 'graph_counts': expected['graph_counts'],
                  'selected_cli_outputs': outputs, 'query_baseline': expected['query_baseline']}))
'''


def check_installed(wheel_dir, dependency_dir):
    wheels = verify_wheels(wheel_dir)
    require(dependency_dir.is_dir() and any(dependency_dir.glob('*.whl')), 'Offline dependency wheels are missing')
    env = clean_env()
    with tempfile.TemporaryDirectory(prefix='bruns-borosilicate-installed-') as temporary:
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
        smoke.write_text(inspect.getsource(install_offline_guard) + '\ninstall_offline_guard()\n' + INSTALLED_SMOKE, encoding='utf-8')
        run([python, '-I', smoke, expected], cwd=work, env=env)
        guard = work / 'sitecustomize.py'
        guard.write_text(inspect.getsource(install_offline_guard) + '\ninstall_offline_guard()\n', encoding='utf-8')
        env['PYTHONPATH'] = str(work)
        for group in TEST_GROUPS:
            if group != 'core':
                run([python, '-I', '-B', Path(__file__).resolve(), '--installed-group', group], cwd=work, env=env)
        # Reuse the existing independent installed CLI/API/linked-fixture smoke,
        # but load the portable guard explicitly, including in CLI subprocesses.
        run([python, '-B', ROOT / 'experimental/platform/ci/check_offline.py', 'installed-smoke'], cwd=work, env=env)
    print('Complete Bruns source/installed contract: installed phase passed; no live, deployment or release claim.', flush=True)


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
