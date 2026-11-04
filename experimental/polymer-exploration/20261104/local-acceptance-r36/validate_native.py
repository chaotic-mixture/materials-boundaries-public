"""Fresh applied-native checks and actual joins, without replaying history."""
from pathlib import Path
import hashlib
import io
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tests'))
from materials_boundaries.database import Database, read_snapshot


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def main():
    application = json.loads((OUT / 'APPLICATION_R36.json').read_bytes())
    assert all(sha(ROOT / n) == h for n, h in application['after_sha256'].items())
    patterns = ['test_database*.py', 'test_glass_transition_method_context_contract.py']
    suite = unittest.TestSuite([unittest.defaultTestLoader.discover(str(ROOT / 'tests'), pattern=p) for p in patterns])
    package = json.loads((OUT.parent / 'local-acceptance-r33/PACKAGE_INPUTS_R33.json').read_bytes())
    paths = {ROOT / n for n in package} | set((ROOT / 'schemas').glob('*.schema.json')) | {ROOT / 'docs/MATERIAL_REFERENCE_CATALOG.md', Path(__file__)}
    for module in list(sys.modules.values()):
        name = getattr(module, '__file__', None)
        if name:
            path = Path(name).resolve()
            if path.is_relative_to(ROOT) and path.is_file():
                paths.add(path)
    before = {p.relative_to(ROOT).as_posix(): sha(p) for p in sorted(paths)}
    write(OUT / 'NATIVE_TEST_INPUTS_R36.json', before)
    log = io.StringIO()
    result = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
    (OUT / 'native-tests-r36.log').write_text(log.getvalue(), encoding='utf-8', newline='\n')
    stable = all(sha(ROOT / n) == h for n, h in before.items())
    write(OUT / 'NATIVE_TEST_RESULTS_R36.json', {'scope': 'Fresh applied native database19 plus glass-transition-method3;not sum withprevious203', 'tests_run': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors), 'skipped': len(result.skipped), 'successful': result.wasSuccessful(), 'inputs_unchanged': stable, 'stable_inputs': len(before), 'input_manifest_sha256': sha(OUT / 'NATIVE_TEST_INPUTS_R36.json'), 'full_history': 'not_run'})
    assert result.wasSuccessful() and result.testsRun == 22 and not result.skipped and stable
    db = Database()
    assert db.snapshot == application['snapshot']
    graph = db.validate_scientific_contracts()
    write(OUT / 'NATIVE_GRAPH_R36.json', graph)
    external = ROOT.parent / 'open-database-evidence/polymer-native-acceptance-20261104-r36'
    candidate = ROOT.parent / 'open-database-evidence/polymer-pur-dma-native-mapping-20261104-r1'
    for name, filters, count in [('new-four', {'quantity': 'glass_transition_temperature', 'source': 'ivdre_2024_lpo_rigid_pur'}, 4), ('complete-source-twelve', {'source': 'ivdre_2024_lpo_rigid_pur'}, 12)]:
        db.export(external / ('accepted-' + name), **filters)
        _, exported = read_snapshot(external / ('accepted-' + name))
        _, expected = read_snapshot(candidate / name)
        assert exported == expected and len(exported) == count
    assert all(sha(ROOT / n) == h for n, h in before.items())
    write(OUT / 'ACCEPTED_CONSUMER_R36.json', {'status': 'passed', 'snapshot': db.snapshot, 'new_quantity_records': 4, 'complete_source_records': 12, 'accepted_exports_match_approved_candidates': True, 'native_graph': graph, 'inputs_unchanged': True, 'installation': 'pending_real_isolated_package', 'pushed': False})
    print(json.dumps({'tests': result.testsRun, 'stable_inputs': len(before), 'new_properties': 4, 'complete_source_records': 12, 'snapshot': db.snapshot}), flush=True)


if __name__ == '__main__':
    main()
