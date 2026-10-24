"""Exercise actual unittest fixture and result behavior with tiny local suites."""
from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
from hashlib import sha256
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.runner import _WritelnDecorator
from unittest.mock import patch
from uuid import uuid4


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    'partition_execution_contract_runner', ROOT / 'scripts/run_full_core_partition_ci.py')
ci = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = ci
SPEC.loader.exec_module(ci)


def identifiers(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from identifiers(item)
        else:
            yield item.id()


def cases(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from cases(item)
        else:
            yield item


class PartitionExecutionContracts(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.prefix = 'test_partition_fixture_' + uuid4().hex
        self.modules = []

    def module(self, suffix, body):
        name = self.prefix + '_' + suffix
        path = self.directory / (name + '.py')
        path.write_text('import unittest\nEVENTS = []\n' + body, encoding='utf-8')
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        previous = sys.modules.get(name)
        sys.modules[name] = module
        def restore():
            if previous is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = previous
        self.addCleanup(restore)
        spec.loader.exec_module(module)
        self.modules.append(module)
        return module

    @staticmethod
    def suite(*modules):
        result = unittest.TestSuite()
        for module in modules:
            result.addTests(unittest.TestLoader().loadTestsFromModule(module))
        return result

    @staticmethod
    def manifest(suite, modules, assignments):
        ids = list(identifiers(suite))
        return {
            'partition_count': 4, 'canonical_ids': ids,
            'modules': [
                {'name': module.__name__, 'path': 'tests/' + module.__name__ + '.py',
                 'partition': partition,
                 'test_ids': [identifier for identifier in ids
                              if identifier.split('.')[0] == module.__name__]}
                for module, partition in zip(modules, assignments)],
        }

    @staticmethod
    def result(expected_ids, events=None):
        return ci.ReceiptResult(_WritelnDecorator(io.StringIO()), True, 2,
                                expected_ids=expected_ids,
                                journal=events.append if events is not None else None)

    def execute(self, suite):
        ids = list(identifiers(suite))
        events = []
        result = self.result(ids, events)
        suite.run(result)
        return result, events

    @staticmethod
    def context():
        return {
            'sha': '1' * 40, 'tree': '2' * 40, 'run_id': '40000000001', 'run_attempt': '2',
            'python_version': '3.11', 'python_full_version': '3.11.99',
            'platform': {'system': 'Linux', 'os_name': 'posix', 'sys_platform': 'linux', 'machine': 'x86_64'},
            'manifest_sha256': sha256((ROOT / 'tests/core_partition/manifest.json').read_bytes()).hexdigest(),
            'runner_sha256': sha256((ROOT / 'scripts/run_full_core_partition_ci.py').read_bytes()).hexdigest(),
            'wood_review_dossier_present': False,
        }

    def test_whole_module_filter_keeps_relative_order_and_fixture_lifetimes(self):
        body = '''
def setUpModule(): EVENTS.append('module:start')
def tearDownModule(): EVENTS.append('module:end')
class First(unittest.TestCase):
    @classmethod
    def setUpClass(cls): EVENTS.append('first:start')
    @classmethod
    def tearDownClass(cls): EVENTS.append('first:end')
    def test_a(self): EVENTS.append('first:a')
    def test_b(self): EVENTS.append('first:b')
class Second(unittest.TestCase):
    @classmethod
    def setUpClass(cls): EVENTS.append('second:start')
    @classmethod
    def tearDownClass(cls): EVENTS.append('second:end')
    def test_a(self): EVENTS.append('second:a')
'''
        modules = [self.module(label, body) for label in ('a', 'b', 'c')]
        suite = self.suite(*modules)
        original_ids = list(identifiers(suite))
        manifest = self.manifest(suite, modules, (0, 1, 0))
        selected = ci.select_partition(suite, manifest, 0)
        expected = [identifier for identifier in original_ids
                    if identifier.split('.')[0] in {modules[0].__name__, modules[2].__name__}]
        self.assertEqual(list(identifiers(selected)), expected)
        self.assertEqual(list(identifiers(suite)), original_ids)
        result, _ = self.execute(selected)
        self.assertEqual(result.started_ids, expected)
        self.assertEqual([item['test_id'] for item in result.completed], expected)
        self.assertTrue(all(item['status'] == 'passed' for item in result.completed))
        lifecycle = ['module:start', 'first:start', 'first:a', 'first:b', 'first:end',
                     'second:start', 'second:a', 'second:end', 'module:end']
        self.assertEqual(modules[0].EVENTS, lifecycle)
        self.assertEqual(modules[1].EVENTS, [])
        self.assertEqual(modules[2].EVENTS, lifecycle)

    def test_filter_rejects_reordered_missing_extra_and_duplicate_discovery(self):
        module = self.module('order', '''
class Cases(unittest.TestCase):
    def test_a(self): pass
    def test_b(self): pass
''')
        for operation in ('reverse', 'missing', 'duplicate', 'unknown'):
            suite = self.suite(module)
            manifest = self.manifest(suite, [module], (0,))
            changed = list(cases(suite))
            if operation == 'reverse': changed.reverse()
            elif operation == 'missing': changed.pop()
            elif operation == 'unknown':
                unknown = unittest.FunctionTestCase(lambda: None)
                unknown.id = lambda: 'test_foreign.Case.test_x'
                changed[-1] = unknown
            else: changed.append(changed[0])
            suite = unittest.TestSuite(changed)
            with self.subTest(operation=operation), self.assertRaises(RuntimeError):
                ci.select_partition(suite, manifest, 0)

    def test_module_and_class_fixture_errors_are_recorded_and_do_not_stop_later_modules(self):
        fixtures = {
            'setup_module': "def setUpModule(): raise RuntimeError('fixture setup')\n",
            'teardown_module': "def tearDownModule(): raise RuntimeError('fixture teardown')\n",
            'setup_class': '', 'teardown_class': '',
        }
        for kind, prefix in fixtures.items():
            class_fixture = ''
            if kind == 'setup_class':
                class_fixture = "    @classmethod\n    def setUpClass(cls): raise RuntimeError('class setup')\n"
            elif kind == 'teardown_class':
                class_fixture = "    @classmethod\n    def tearDownClass(cls): raise RuntimeError('class teardown')\n"
            first = self.module(kind + '_a', prefix + 'class Cases(unittest.TestCase):\n' +
                                class_fixture + '    def test_case(self): EVENTS.append("body")\n')
            second = self.module(kind + '_b', '''
class Later(unittest.TestCase):
    def test_case(self): EVENTS.append('later')
''')
            result, _ = self.execute(self.suite(first, second))
            with self.subTest(fixture=kind):
                self.assertTrue(result.fixture_errors)
                self.assertFalse(result.wasSuccessful())
                self.assertEqual(second.EVENTS, ['later'])
                self.assertEqual(result.completed[-1]['status'], 'passed')
                if kind.startswith('setup_'):
                    self.assertEqual(first.EVENTS, [])
                    self.assertEqual(len(result.started_ids), 1)
                else:
                    self.assertEqual(first.EVENTS, ['body'])
                    self.assertEqual(len(result.started_ids), 2)

    def test_method_setup_and_teardown_errors_are_not_counted_as_passes(self):
        for fixture in ('setUp', 'tearDown'):
            module = self.module(fixture.lower(), f'''
class Cases(unittest.TestCase):
    def {fixture}(self): raise RuntimeError('method fixture')
    def test_case(self): EVENTS.append('body')
''')
            result, _ = self.execute(self.suite(module))
            with self.subTest(fixture=fixture):
                self.assertEqual(len(result.started_ids), 1)
                self.assertEqual(len(result.completed), 1)
                self.assertNotEqual(result.completed[0]['status'], 'passed')
                self.assertFalse(result.wasSuccessful())

    def test_failing_and_error_subtests_fail_the_parent_and_execution_continues(self):
        module = self.module('subtests', '''
class Cases(unittest.TestCase):
    def test_a_bad(self):
        with self.subTest(case='failure'): self.fail('intentional failure')
        with self.subTest(case='success'): pass
        with self.subTest(case='error'): raise RuntimeError('intentional error')
    def test_z_after(self): EVENTS.append('after')
''')
        result, _ = self.execute(self.suite(module))
        self.assertEqual(len(result.started_ids), 2)
        self.assertEqual(len(result.completed), 2)
        self.assertEqual(len(result.subtest_errors), 2)
        self.assertNotEqual(result.completed[0]['status'], 'passed')
        self.assertEqual(result.completed[1]['status'], 'passed')
        self.assertEqual(module.EVENTS, ['after'])
        self.assertFalse(result.wasSuccessful())

    def test_expected_failure_and_unexpected_success_have_nonpassing_outcomes(self):
        for kind, body in (('expected_failure', "self.fail('intentional expected failure')"),
                           ('unexpected_success', 'pass')):
            module = self.module(kind, f'''
class Cases(unittest.TestCase):
    @unittest.expectedFailure
    def test_case(self): {body}
''')
            result, _ = self.execute(self.suite(module))
            with self.subTest(kind=kind):
                self.assertEqual(len(result.started_ids), 1)
                self.assertEqual(len(result.completed), 1)
                self.assertNotIn(result.completed[0]['status'], ('passed', 'skipped'))
                self.assertEqual(len(result.expectedFailures) + len(result.unexpectedSuccesses), 1)

    def test_whole_method_skip_is_recorded_but_subtest_skip_is_not_a_parent_pass(self):
        module = self.module('skips', '''
class Cases(unittest.TestCase):
    @unittest.skip('exact fixture reason')
    def test_a_whole(self): pass
    def test_b_subtest(self):
        with self.subTest(case='unexpected skip'): self.skipTest('unlisted inner reason')
''')
        result, _ = self.execute(self.suite(module))
        whole = next(item for item in result.completed if item['test_id'].endswith('.test_a_whole'))
        self.assertEqual(whole['status'], 'skipped')
        self.assertEqual(whole['reason'], 'exact fixture reason')
        subtest = [item for item in result.completed if item['test_id'].endswith('.test_b_subtest')]
        self.assertTrue(result.protocol_errors or result.subtest_errors or
                        (subtest and subtest[0]['status'] not in ('passed', 'skipped')))

    def test_unknown_and_duplicate_result_events_fail_closed(self):
        module = self.module('protocol', '''
class Cases(unittest.TestCase):
    def test_case(self): pass
''')
        case = next(iter(next(iter(self.suite(module)))))
        for kind in ('unknown', 'duplicate_start', 'duplicate_success'):
            result = self.result(['test_other.Case.test_x'] if kind == 'unknown' else [case.id()])
            result.startTest(case)
            if kind == 'duplicate_start': result.startTest(case)
            result.addSuccess(case)
            if kind == 'duplicate_success': result.addSuccess(case)
            result.stopTest(case)
            with self.subTest(kind=kind):
                self.assertTrue(result.protocol_errors)

    def test_interrupt_preserves_started_diagnostics_without_a_pass(self):
        module = self.module('interrupt', '''
class Cases(unittest.TestCase):
    def test_a_interrupt(self): raise KeyboardInterrupt('intentional interruption')
    def test_z_unstarted(self): EVENTS.append('must not run')
''')
        suite = self.suite(module)
        expected = list(identifiers(suite))
        events = []
        result = self.result(expected, events)
        with self.assertRaises(KeyboardInterrupt):
            suite.run(result)
        self.assertEqual(result.started_ids, expected[:1])
        self.assertFalse(any(item['status'] == 'passed' for item in result.completed))
        self.assertEqual(module.EVENTS, [])
        self.assertTrue(events)

    def test_separate_calls_do_not_reuse_result_state_or_module_outcomes(self):
        module = self.module('fresh', '''
class Cases(unittest.TestCase):
    def test_case(self): EVENTS.append('body')
''')
        first, first_events = self.execute(self.suite(module))
        second, second_events = self.execute(self.suite(module))
        self.assertEqual(first.started_ids, second.started_ids)
        self.assertIsNot(first.started_ids, second.started_ids)
        self.assertIsNot(first.completed, second.completed)
        self.assertIsNot(first_events, second_events)
        self.assertEqual(len(first.started_ids), 1)
        self.assertEqual(len(second.started_ids), 1)
        self.assertEqual(module.EVENTS, ['body', 'body'])

    def test_production_entry_has_no_context_or_incomplete_bypass_arguments(self):
        for flag in ('--fake-context', '--context-file', '--allow-incomplete', '--allow-skips'):
            with self.subTest(flag=flag), patch.object(ci, 'production_context') as context:
                with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as caught:
                    ci.main(['run', '--partition', '0', '--output-dir', str(self.directory / 'output'), flag])
                self.assertEqual(caught.exception.code, 2)
                context.assert_not_called()
                self.assertFalse((self.directory / 'output').exists())

    def test_interrupted_run_saves_terminal_rejection_and_partial_journal(self):
        # Only one synthetic method executes. Internal context/discovery injection
        # exercises the real filesystem boundary without a production bypass flag.
        manifest = ci.load_manifest()
        identifier = ci.partition_ids(manifest, 0)[0]
        context = self.context()
        module = self.module('saved_interrupt', '''
class Cases(unittest.TestCase):
    def test_case(self): raise KeyboardInterrupt('intentional saved interruption')
''')
        case = next(cases(self.suite(module)))
        case.id = lambda: identifier
        selected = unittest.TestSuite([case])
        output = self.directory / 'results'
        with patch.object(ci, 'load_manifest', return_value=manifest), \
                patch.object(ci, 'production_context', return_value=context), \
                patch.object(ci, 'discover_inventory', return_value=(selected, ci.manifest_ids(manifest))), \
                patch.object(ci, 'declared_inventory', return_value=ci.manifest_ids(manifest)), \
                patch.object(ci, 'select_partition', return_value=selected), \
                redirect_stderr(io.StringIO()), redirect_stdout(io.StringIO()):
            code = ci.run_partition(0, output, root=self.directory)
        self.assertNotEqual(code, 0)
        receipt = json.loads((output / 'receipt.json').read_bytes())
        self.assertTrue(receipt['terminal'])
        self.assertEqual(receipt['terminal_status'], 'cancelled')
        self.assertEqual(receipt['started_ids'], [identifier])
        self.assertFalse(any(row['status'] == 'passed' for row in receipt['completed']))
        journal_bytes = (output / 'journal.jsonl').read_bytes()
        self.assertEqual(sha256(journal_bytes).hexdigest(), receipt['journal_sha256'])
        events = [json.loads(line) for line in journal_bytes.splitlines()]
        self.assertEqual(events[0]['event'], 'header')
        self.assertTrue(any(row['event'] == 'started' and row['test_id'] == identifier for row in events))
        self.assertEqual(events[-1]['event'], 'terminal')
        self.assertEqual(events[-1]['terminal_status'], 'cancelled')
        with self.assertRaises(RuntimeError):
            ci.validate_receipt(receipt, manifest, context, expected_python='3.11')

    def test_post_execution_context_drift_fails_before_success_can_be_emitted(self):
        manifest = ci.load_manifest()
        identifier = ci.partition_ids(manifest, 0)[0]
        context = self.context()
        changed = deepcopy(context)
        changed['runner_sha256'] = 'f' * 64
        case = unittest.FunctionTestCase(lambda: None)
        case.id = lambda: identifier
        selected = unittest.TestSuite([case])
        output = self.directory / 'drift-results'
        # Receipt coverage is tested independently above and in test_receipts.
        # Replace that validator only to isolate the post-execution source check
        # with one tiny synthetic method rather than hundreds of fake methods.
        with patch.object(ci, 'load_manifest', return_value=manifest), \
                patch.object(ci, 'production_context', side_effect=[context, changed]) as metadata, \
                patch.object(ci, 'discover_inventory', return_value=(selected, ci.manifest_ids(manifest))), \
                patch.object(ci, 'declared_inventory', return_value=ci.manifest_ids(manifest)), \
                patch.object(ci, 'select_partition', return_value=selected), \
                patch.object(ci, 'validate_receipt', return_value={}), \
                redirect_stderr(io.StringIO()), redirect_stdout(io.StringIO()):
            code = ci.run_partition(0, output, root=self.directory)
        self.assertEqual(metadata.call_count, 2)
        self.assertNotEqual(code, 0)
        receipt = json.loads((output / 'receipt.json').read_bytes())
        self.assertEqual(receipt['terminal_status'], 'failed')
        self.assertTrue(receipt['protocol_errors'])
        events = [json.loads(line) for line in (output / 'journal.jsonl').read_bytes().splitlines()]
        self.assertEqual(events[-1]['terminal_status'], 'failed')


if __name__ == '__main__':
    unittest.main()
