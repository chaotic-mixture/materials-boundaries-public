"""Validate exact applied TGA native data and candidate-equal complete exports."""
from pathlib import Path
import hashlib
import io
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT), str(ROOT / 'tests')]
from materials_boundaries.database import Database, read_snapshot


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(name, obj):
    with (OUT / name).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(obj, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def main():
    application = json.loads((OUT / 'APPLICATION_R37.json').read_bytes())
    assert all(sha(ROOT / name) == digest for name, digest in application['after_sha256'].items())
    suite = unittest.TestSuite([unittest.defaultTestLoader.discover(str(ROOT / 'tests'), pattern=pattern)
                               for pattern in ['test_database*.py', 'test_tga_endpoint_contract.py']])
    package = json.loads((OUT.parent / 'local-acceptance-r33/PACKAGE_INPUTS_R33.json').read_bytes())
    paths = {ROOT / name for name in package} | set((ROOT / 'schemas').glob('*.schema.json'))
    paths |= {ROOT / 'docs/MATERIAL_REFERENCE_CATALOG.md', Path(__file__)}
    for module in list(sys.modules.values()):
        name = getattr(module, '__file__', None)
        if name:
            path = Path(name).resolve()
            if path.is_relative_to(ROOT) and path.is_file():
                paths.add(path)
    inputs = {path.relative_to(ROOT).as_posix(): sha(path) for path in sorted(paths)}
    write('NATIVE_TEST_INPUTS_R37.json', inputs)
    log = io.StringIO()
    result = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
    (OUT / 'native-tests-r37.log').write_text(log.getvalue(), encoding='utf-8', newline='\n')
    stable = all(sha(ROOT / name) == digest for name, digest in inputs.items())
    write('NATIVE_TEST_RESULTS_R37.json', {'scope': 'Fresh applied native database19+TGA15;not sum with implementation142',
        'tests_run': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
        'skipped': len(result.skipped), 'successful': result.wasSuccessful(),
        'inputs_unchanged': stable, 'stable_inputs': len(inputs), 'full_history': 'not_run'})
    assert result.wasSuccessful() and result.testsRun == 34 and not result.skipped and stable
    db = Database()
    assert db.snapshot == application['snapshot']
    graph = db.validate_scientific_contracts()
    write('NATIVE_GRAPH_R37.json', graph)
    external = ROOT.parent / 'open-database-evidence/polymer-native-acceptance-20261104-r37'
    candidate = ROOT.parent / 'open-database-evidence/polymer-pur-tga-native-mapping-20261104-r1'
    for name, filters, count in [('new-twenty-eight', {'source': 'ivdre_2024_lpo_rigid_pur', 'query': '_tga_platinum_pan'}, 28),
                                 ('complete-source-forty', {'source': 'ivdre_2024_lpo_rigid_pur'}, 40)]:
        db.export(external / ('accepted-' + name), **filters)
        _, exported = read_snapshot(external / ('accepted-' + name))
        _, expected = read_snapshot(candidate / name)
        assert exported == expected and len(exported) == count
    assert all(sha(ROOT / name) == digest for name, digest in inputs.items())
    write('ACCEPTED_CONSUMER_R37.json', {'status': 'passed', 'snapshot': db.snapshot,
        'new_TGA_records': 28, 'complete_source_records': 40, 'accepted_exports_equal_candidates': True,
        'inputs_unchanged': True, 'installation_final_review': 'pending', 'pushed': False})
    print(json.dumps({'tests': result.testsRun, 'stable_inputs': len(inputs), 'snapshot': db.snapshot}), flush=True)


if __name__ == '__main__':
    main()
