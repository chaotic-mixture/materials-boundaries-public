"""Test the consolidated current state and daily graph/export scope, not history."""
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tests'))


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def main():
    external = Path(sys.argv[1]).resolve()
    assert not external.exists() and not external.is_relative_to(ROOT)
    external.mkdir(parents=True)
    patterns = ['test_database*.py', 'test_tga_endpoint_contract.py', 'test_material_reference_contract.py', 'test_material_presentation_fast_path.py',
                'test_material_reference_expansion.py', 'test_material_uncertainty_contract.py',
                'test_material_reported_measures_contract.py', 'test_material_scientific_notation_contract.py',
                'test_specified_elongation_contract.py', 'test_flexural_strength_contract.py',
                'test_tensile_break_stress_contract.py', 'test_break_elongation_contract.py',
                'test_strength_elongation_contract.py', 'test_shore_a_hardness_contract.py',
                'test_compression_reference_contract.py','test_tear_strength_contract.py','test_flexural_elongation_contract.py','test_izod_impact_contract.py','test_glass_transition_temperature_contract.py','test_melting_peak_temperature_contract.py','test_glass_transition_method_context_contract.py','test_dielectric_breakdown_strength_contract.py','test_thermal_conductivity_contract.py']
    keys = json.loads((OUT.parent / 'local-acceptance-r37/PACKAGE_INPUTS_R37.json').read_bytes())
    paths = {ROOT / name for name in keys} | {p for pattern in patterns for p in (ROOT / 'tests').glob(pattern)}
    paths |= set((ROOT / 'schemas').glob('*.schema.json'))
    paths.add(Path(__file__))
    paths |= {ROOT / n for n in ('README.md', 'HANDOFF.md', 'docs/MATERIAL_REFERENCE_CATALOG.md',
                                'docs/DATABASE_COVERAGE.zh.md', 'docs/MATERIAL_SOURCE_CONDITIONS.zh.md',
                                'docs/OPEN_DATABASE_ROADMAP.zh.md',
                                'experimental/platform/query-service/materials_query/catalog_snapshot.py')}
    before = {p.relative_to(ROOT).as_posix(): sha(p) for p in sorted(paths)}
    write(OUT / 'SCOPED_TEST_INPUTS_R36_R38_R2.json', {'repo_files_sha256': before, 'captured': 'before corrected fresh consolidated test run'})
    suite, daily = unittest.TestSuite(), 0
    for pattern in patterns:
        tests = unittest.TestLoader().discover(str(ROOT / 'tests'), pattern=pattern)
        if pattern == 'test_database*.py': daily = tests.countTestCases()
        suite.addTests(tests)
    log = io.StringIO()
    result = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
    (OUT / 'scoped-tests-r36-r38-r2.log').write_text(log.getvalue(), encoding='utf-8', newline='\n')
    after = {p.relative_to(ROOT).as_posix(): sha(p) for p in sorted(paths)}
    assert before == after
    write(OUT / 'SCOPED_TESTS_R36_R38_R2.json', {'scope': patterns,
          'execution': 'fresh consolidated current5412property native/runtime/docs;not sum of historical local checks',
          'tests_run': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
          'skipped': len(result.skipped), 'successful': result.wasSuccessful(), 'daily_database_subset_tests': daily,
          'inputs_unchanged_during_run': len(before), 'input_manifest_sha256': sha(OUT / 'SCOPED_TEST_INPUTS_R36_R38_R2.json'),
          'full_history_regression': 'not_run'})
    assert result.wasSuccessful() and result.testsRun == 218 and daily == 19 and not result.skipped
    env = os.environ.copy()
    env.update(PYTHONUTF8='1', PYTHONDONTWRITEBYTECODE='1')
    commands = [['check', '--scientific-contracts'],
                ['export', '--query', 'C11000', '--quantity', 'mass_density', '--output', str(external / 'database-example')],
                ['verify', '--snapshot', str(external / 'database-example')]]
    receipts = []
    for args in commands:
        proc = subprocess.run([sys.executable, '-B', '-m', 'materials_boundaries.database', *args],
                              cwd=ROOT, env=env, capture_output=True, encoding='utf-8')
        (external / (args[0] + '.log')).write_text(proc.stdout + proc.stderr, encoding='utf-8', newline='\n')
        proc.check_returncode()
        receipts.append({'command': ['python', '-m', 'materials_boundaries.database', *args],
                         'exit_code': proc.returncode, 'result': json.loads(proc.stdout)})
    assert receipts[-1]['result']['status'] == 'snapshot_integrity_passed'
    assert all(sha(ROOT / name) == digest for name, digest in before.items())
    write(OUT / 'DATABASE_CI_LOCAL_EQUIVALENT_R36_R38.json', {
        'daily_tests': {'executed_as_subset_of_scoped_run': 19, 'not_additional_to_218': True},
        'commands': receipts, 'full_history_regression': 'not_run', 'remote_CI': 'pending_exact_commit'})
    print(json.dumps({'tests': result.testsRun, 'daily_subset': daily, 'stable_inputs': len(before),
                      'graph_export_verify': 'passed'}), flush=True)


if __name__ == '__main__':
    main()
