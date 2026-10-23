"""Fail-closed CI scope, complete inventories and exact Bruns append contract."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('bruns_borosilicate_ci', ROOT / 'scripts/run_bruns_borosilicate_ci.py')
ci = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ci)


class BrunsBorosilicateCITests(unittest.TestCase):
    def test_previous_jobs_keep_every_step_and_only_new_branch_is_gated(self):
        prior = ci.git('show', ci.BASE_COMMIT + ':.github/workflows/ci.yml').decode('utf-8')
        current = (ROOT / '.github/workflows/ci.yml').read_bytes().decode('utf-8')
        self.assertEqual(current, ci.expected_workflow(prior))
        restored = current.removesuffix(ci.TARGETED_JOB).replace(ci.FULL_JOB_IF, ci.PREVIOUS_FULL_JOB_IF)
        self.assertEqual(restored, prior)
        self.assertEqual(current.count('  bruns-borosilicate-targeted:\n'), 1)
        self.assertEqual(ci.FULL_JOB_IF.count(ci.BRANCH_REF), 1)
        self.assertIn("github.event_name != 'push'", ci.FULL_JOB_IF)
        self.assertIn("github.event_name == 'push'", ci.TARGETED_JOB)
        self.assertIn('persist-credentials: false', ci.TARGETED_JOB)
        self.assertIn("python-version: '3.11'", ci.TARGETED_JOB)
        self.assertIn("python-version: '3.12'", ci.TARGETED_JOB)
        self.assertEqual(ci.BRANCH_REF, 'refs/heads/experimental/borosilicate-growth-bruns2020')

    def test_scope_rejects_unlisted_deleted_nonfile_and_symlink_paths(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            allowed = 'scripts/run_bruns_borosilicate_ci.py'
            (root / 'scripts').mkdir()
            (root / allowed).write_text('fixture', encoding='utf-8')
            ci.validate_names([allowed], root=root)
            for names in (['credentials.json'], ['../outside'], [None],
                          ['experimental/platform/query-service/materials_query/pins/family_relationships.json'],
                          ['materials_boundaries/data/observations.json']):
                with self.subTest(names=names), self.assertRaises(RuntimeError):
                    ci.validate_names(names, root=root)
            with patch.object(Path, 'is_symlink', return_value=True), self.assertRaises(RuntimeError):
                ci.validate_names([allowed], root=root)
            (root / allowed).unlink()
            with self.assertRaises(RuntimeError):
                ci.validate_names([allowed], root=root)
            (root / allowed).mkdir()
            with self.assertRaises(RuntimeError):
                ci.validate_names([allowed], root=root)
        for raw in (b'D\0README.md\0', b'R100\0old\0new\0', b'M\0', b'A\0one\0M\0'):
            with self.subTest(raw=raw), self.assertRaises(RuntimeError):
                ci.changed_paths(raw)

    def test_ci_requires_exact_push_branch_sha_and_clean_checkout(self):
        expected = {'GITHUB_ACTIONS': 'true', 'GITHUB_EVENT_NAME': 'push',
                    'GITHUB_REF': ci.BRANCH_REF, 'GITHUB_SHA': 'f' * 40}
        with patch.dict(ci.os.environ, expected, clear=True), patch.object(ci, 'git', return_value=b''):
            ci.validate_event('f' * 40)
        for key, value in (('GITHUB_EVENT_NAME', 'pull_request'), ('GITHUB_EVENT_NAME', 'workflow_dispatch'),
                           ('GITHUB_REF', 'refs/heads/main'), ('GITHUB_REF', ci.PREVIOUS_BRANCH_REF),
                           ('GITHUB_SHA', 'e' * 40), ('GITHUB_SHA', '')):
            with self.subTest(key=key, value=value), patch.dict(ci.os.environ, {**expected, key: value}, clear=True):
                with patch.object(ci, 'git', return_value=b''), self.assertRaises(RuntimeError):
                    ci.validate_event('f' * 40)
        with patch.dict(ci.os.environ, expected, clear=True), patch.object(ci, 'git', return_value=b' M README.md\n'):
            with self.assertRaises(RuntimeError):
                ci.validate_event('f' * 40)

    def test_ambiguous_yaml_scalars_and_index_package_builds_fail(self):
        ci.validate_targeted_run_scalars(ci.TARGETED_JOB)
        ci.validate_wheel_command(ci.BUILD_COMMAND)
        for verb in ('install', 'download'):
            marker = '      - run: "python -m pip ' + verb
            line = next(line for line in ci.TARGETED_JOB.splitlines() if line.startswith(marker))
            malformed = ci.TARGETED_JOB.replace(line, line.replace('run: "', 'run: ', 1)[:-1])
            with self.subTest(verb=verb), self.assertRaises(RuntimeError):
                ci.validate_targeted_run_scalars(malformed)
        for command in (ci.BUILD_COMMAND.replace('./formal-catalog', 'formal-catalog'),
                        ci.BUILD_COMMAND.replace('--no-index ', ''),
                        ci.BUILD_COMMAND.replace('./experimental/platform/lifecycle', 'https://example.invalid/package')):
            with self.subTest(command=command), self.assertRaises(RuntimeError):
                ci.validate_wheel_command(command)

    def test_unknown_predecessor_workflow_shapes_are_rejected(self):
        prior = ci.git('show', ci.BASE_COMMIT + ':.github/workflows/ci.yml').decode('utf-8')
        for value in (prior.replace(ci.PREVIOUS_FULL_JOB_IF, '', 1),
                      prior.replace('  evidence-batch-targeted:\n', '  missing-job:\n'),
                      prior.replace('  family-adjacency-targeted:\n', '  missing-job:\n'),
                      prior + ci.TARGETED_JOB):
            with self.subTest(length=len(value)), self.assertRaises(RuntimeError):
                ci.expected_workflow(value)

    def test_complete_inventories_preserve_every_predecessor_and_new_test(self):
        all_ids = []
        self.assertEqual(set(ci.TEST_GROUPS), {'core', 'query', 'formal', 'ingestion', 'relationships',
                                             'provider', 'transport', 'lifecycle', 'integration'})
        for name, (relative, _, _) in ci.TEST_GROUPS.items():
            with self.subTest(group=name):
                declared = ci.declared_test_ids(relative)
                ci.validate_inventory(name, declared)
                prior = ci.declared_test_ids(relative, predecessor=True)
                self.assertTrue(prior)
                self.assertTrue(set(prior).issubset(declared))
                all_ids.extend(declared)
        self.assertEqual(len(all_ids), len(set(all_ids)))
        for module in ('test_bruns_borosilicate_packet', 'test_bruns_borosilicate_preservation',
                       'test_bruns_borosilicate_ci'):
            self.assertTrue(any(identifier.startswith(module + '.') for identifier in all_ids))

    def test_missing_duplicate_substituted_or_extra_inventory_ids_are_rejected(self):
        for name, (relative, _, _) in ci.TEST_GROUPS.items():
            ids = ci.declared_test_ids(relative)
            for changed in (ids[:-1], ids + ids[:1], ids[1:] + ['different.Case.test_replacement'],
                            ids + ['different.Case.test_extra']):
                with self.subTest(group=name, count=len(changed)), self.assertRaises(RuntimeError):
                    ci.validate_inventory(name, changed)
        self.assertEqual(ci.inventory_fingerprint(['b', 'a']), ci.inventory_fingerprint(['a', 'b']))

    def test_current_payload_pins_exact_packet_data_baseline_and_unchanged_reviews(self):
        payload = ci.installation_payload()
        self.assertEqual(payload['delta_counts'], {'identity': 4, 'grade': 0, 'state': 4, 'property': 4, 'source': 1})
        self.assertEqual(payload['graph_counts'], {'identity': 1148, 'grade': 31, 'state': 1149, 'property': 1160, 'source': 124})
        self.assertEqual(payload['formal_counts']['formal_project_admission_count'], 1172)
        self.assertEqual(payload['formal_counts']['reviewed_computed_composition_count'], 24)
        self.assertEqual(len(payload['packages']), 6)
        self.assertEqual(set(payload['preserved_resources']), set(ci.PRESERVED_RESOURCES))
        for name in ('PACKET_SHA256', 'QUERY_BASELINE_SHA256'):
            with self.subTest(pin=name), patch.object(ci, name, '0' * 64), self.assertRaises(RuntimeError):
                ci.installation_payload()
        with patch.dict(ci.RESOURCE_HASHES, {'materials.json': '0' * 64}), self.assertRaises(RuntimeError):
            ci.installation_payload()

    def test_append_rejects_count_preserving_rewrite_partial_order_metadata_and_id_drift(self):
        before = {'materials': {'identities': [{'id': 'old', 'category': 'inorganic'}], 'grades': [], 'records': [], 'version': '1'},
                  'properties': {'records': []}, 'sources': {'records': []}}
        candidate = {'materials': {'identities': [{'id': 'new', 'category': 'inorganic'}], 'grades': [], 'records': []},
                     'properties': {'records': []}, 'sources': {'records': []}}
        current = deepcopy(before)
        current['materials']['identities'] += deepcopy(candidate['materials']['identities'])
        total = {'identity': 2, 'grade': 0, 'state': 0, 'property': 0, 'source': 0}
        delta = {**total, 'identity': 1}
        with patch.object(ci, 'GRAPH_COUNTS', total), patch.object(ci, 'DELTA_COUNTS', delta), \
                patch.object(ci, 'PRIMARY_COUNTS', {'inorganic': 2}):
            ci.validate_append(candidate, before, current)
            for mutation in ('partial', 'old_row', 'new_row', 'order', 'metadata'):
                altered = deepcopy(current)
                if mutation == 'partial':
                    altered['materials']['identities'].pop()
                elif mutation == 'old_row':
                    altered['materials']['identities'][0]['category'] = 'metal'
                elif mutation == 'new_row':
                    altered['materials']['identities'][1]['id'] = 'changed'
                elif mutation == 'order':
                    altered['materials']['identities'].reverse()
                else:
                    altered['materials']['version'] = '2'
                with self.subTest(mutation=mutation), self.assertRaises(RuntimeError):
                    ci.validate_append(candidate, before, altered)
            for rows in ([{'id': 'old'}], [{'id': 'new'}, {'id': 'new'}]):
                changed = deepcopy(candidate)
                changed['materials']['identities'] = rows
                with self.assertRaises(RuntimeError):
                    ci.validate_append(changed, before, current)

    def test_installed_protocol_is_six_wheels_no_index_and_all_complete_suites(self):
        calls = []
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            dependency = root / 'deps'
            dependency.mkdir()
            (dependency / 'dependency.whl').write_bytes(b'fixture')
            wheels = [root / (str(index) + '.whl') for index in range(6)]
            with patch.object(ci, 'verify_wheels', return_value=wheels) as verified, \
                    patch.object(ci.venv.EnvBuilder, 'create'), patch.object(ci, 'installation_payload', return_value={}), \
                    patch.object(ci, 'run', side_effect=lambda command, **kwargs: calls.append((list(map(str, command)), kwargs))):
                ci.check_installed(root, dependency)
            verified.assert_called_once_with(root)
        install_calls = [command for command, _ in calls if 'install' in command]
        self.assertEqual(len(install_calls), 2)
        self.assertTrue(all('--no-index' in command and '--no-deps' in command and '--isolated' in command
                            for command in install_calls))
        self.assertTrue(all(str(wheel) in install_calls[1] for wheel in wheels))
        groups = [command[-1] for command, _ in calls if '--installed-group' in command]
        self.assertEqual(groups, [name for name in ci.TEST_GROUPS if name != 'core'])
        self.assertTrue(all('-I' in command for command, _ in calls if '--installed-group' in command))
        self.assertTrue(any(command[-1] == 'installed-smoke' for command, _ in calls))
        self.assertTrue(all(kwargs['cwd'] != ROOT for _, kwargs in calls))


def synthetic_result(ids, skips):
    skipped_ids = {identifier for identifier, _ in skips}
    return SimpleNamespace(
        testsRun=len(ids),
        started_ids=list(ids),
        passed_ids=[identifier for identifier in ids if identifier not in skipped_ids],
        skipped=[
            (SimpleNamespace(id=lambda identifier=identifier: identifier), reason)
            for identifier, reason in skips
        ],
        expectedFailures=[],
        unexpectedSuccesses=[],
        wasSuccessful=lambda: True,
    )


class BrunsBorosilicateSkipPolicyTests(unittest.TestCase):

    def test_platform_and_opt_in_counts_are_exact(self):
        self.assertEqual(len(ci.source_skip_contract(platform_name='posix', dossier_enabled=False)[0]), 18)
        self.assertEqual(len(ci.source_skip_contract(platform_name='posix', dossier_enabled=True)[0]), 17)
        self.assertEqual(len(ci.source_skip_contract(platform_name='nt', dossier_enabled=False)[0]), 15)
        self.assertEqual(len(ci.source_skip_contract(platform_name='nt', dossier_enabled=True)[0]), 14)
        with self.assertRaises(RuntimeError):
            ci.source_skip_contract(platform_name='unknown')

    def test_known_skips_never_increment_passed_count(self):
        for platform in ('posix', 'nt'):
            for dossier in (True, False):
                contract = ci.source_skip_contract(platform_name=platform, dossier_enabled=dossier)
                ids = sorted([*contract[0], 'extra.Case.test_pass'])
                summary = ci.validate_result(
                    'core', ids, synthetic_result(ids, list(contract[0].items())),
                    skip_contract=contract,
                )
                self.assertEqual(summary['passed'], 1)
                self.assertEqual(summary['skipped'], len(contract[0]))

    def test_missing_unexpected_duplicate_reason_and_os_drift_fail(self):
        contract = ci.source_skip_contract(platform_name='posix', dossier_enabled=False)
        mandatory = list(contract[0].items())
        ids = sorted([*contract[0], 'extra.Case.test_pass'])
        for changed in (
            mandatory[:-1],
            mandatory + [mandatory[0]],
            mandatory + [('extra.Case.test_pass', 'optional jsonschema dev dependency not installed')],
            mandatory + [('extra.Case.test_pass', None)],
            [(mandatory[0][0], 'different reason'), *mandatory[1:]],
            list(ci.source_skip_contract(platform_name='nt', dossier_enabled=False)[0].items()),
        ):
            with self.assertRaises(RuntimeError):
                ci.validate_result('core', ids, synthetic_result(ids, changed), skip_contract=contract)

    def test_windows_privilege_exception_is_one_exact_case_and_reason(self):
        contract = ci.source_skip_contract(platform_name='nt', dossier_enabled=False)
        ids = sorted([*contract[0], ci.WINDOWS_SYMLINK_TEST, 'extra.Case.test_pass'])
        mandatory = list(contract[0].items())
        optional = list(contract[1].items())
        for observed in (mandatory, mandatory + optional):
            summary = ci.validate_result('core', ids, synthetic_result(ids, observed), skip_contract=contract)
            self.assertEqual(summary['passed'], len(ids) - len(observed))
        for wrong in (
            [(ci.WINDOWS_SYMLINK_TEST, 'different reason')],
            [('extra.Case.test_pass', optional[0][1])],
        ):
            with self.assertRaises(RuntimeError):
                ci.validate_result(
                    'core', ids, synthetic_result(ids, mandatory + wrong), skip_contract=contract,
                )

    def test_installed_suites_cannot_use_source_skip_exceptions(self):
        contract = ci.source_skip_contract(platform_name='posix', dossier_enabled=False)
        ids = sorted(contract[0])
        r = synthetic_result(ids, list(contract[0].items()))
        with self.assertRaises(RuntimeError):
            ci.validate_result('query', ids, r, skip_contract=contract)
        with self.assertRaises(RuntimeError):
            ci.validate_result('query', ids, r)

    def test_missing_execution_or_pass_and_failure_cannot_hide_behind_skips(self):
        ids = ['extra.Case.test_pass']
        for attribute, value in (
            ('testsRun', 0),
            ('started_ids', []),
            ('passed_ids', []),
            ('expectedFailures', [('test', 'expected')]),
            ('unexpectedSuccesses', ['test']),
            ('wasSuccessful', lambda: False),
        ):
            r = synthetic_result(ids, [])
            setattr(r, attribute, value)
            with self.assertRaises(RuntimeError):
                ci.validate_result('query', ids, r)


if __name__ == '__main__':
    unittest.main()
