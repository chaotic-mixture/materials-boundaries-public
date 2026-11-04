"""Bounded checks of source-only integration and complete affected joins."""
from pathlib import Path
from copy import deepcopy
import hashlib
import io
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
AUDIT = HERE.parent / 'epoxy-supplement-condition-followup-r1'
EXT = ROOT.parent / 'open-database-evidence/polymer-native-acceptance-20261104-r38'
sys.path[:0] = [str(ROOT), str(ROOT / 'tests')]
from materials_boundaries.database import Database, read_snapshot


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def write(name, obj):
    with (HERE / name).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(obj, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def main():
    application = read(HERE / 'APPLICATION_R38.json')
    assert all(sha(ROOT / name) == digest for name, digest in application['after_sha256'].items())
    suite = unittest.defaultTestLoader.discover(str(ROOT / 'tests'), pattern='test_database*.py')
    package = read(HERE.parent / 'local-acceptance-r37/PACKAGE_INPUTS_R37.json')
    paths = {ROOT / name for name in package} | set((ROOT / 'schemas').glob('*.schema.json')) | {Path(__file__)}
    for module in list(sys.modules.values()):
        name = getattr(module, '__file__', None)
        if name:
            path = Path(name).resolve()
            if path.is_relative_to(ROOT) and path.is_file():
                paths.add(path)
    inputs = {path.relative_to(ROOT).as_posix(): sha(path) for path in sorted(paths)}
    write('EXECUTION_INPUTS_R38.json', inputs)
    log = io.StringIO()
    result = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
    (HERE / 'metadata-tests-r38.log').write_text(log.getvalue(), encoding='utf-8', newline='\n')
    stable = all(sha(ROOT / name) == digest for name, digest in inputs.items())
    write('TEST_RESULTS_R38.json', {'tests_run': result.testsRun, 'failures': len(result.failures),
        'errors': len(result.errors), 'skipped': len(result.skipped), 'successful': result.wasSuccessful(),
        'stable_inputs': len(inputs), 'inputs_unchanged': stable, 'scope': 'Existing19database checks of actual metadata-only update;no newtest module',
        'full_history_installation': 'not_run'})
    assert result.wasSuccessful() and result.testsRun == 19 and not result.skipped and stable
    db = Database()
    assert db.snapshot == application['snapshot'] and len(db.properties) == 5412 and len(db.states) == 5262
    graph = db.validate_scientific_contracts()
    proposal = read(AUDIT / 'SOURCE_UPDATE_PROPOSAL_R1.json')
    sid = proposal['source_id']
    assert db.sources[sid] == proposal['proposed_source']
    old_properties = read(ROOT / 'materials_boundaries/data/reference_properties.json')
    expected = {p['id']: p for p in old_properties['records'] if p['source_id'] == sid}
    assert len(expected) == 40
    rows = list(db.records(source=sid))
    assert {row['record_id']: row['property'] for row in rows} == expected
    assert all(row['sources'] == [proposal['proposed_source']] for row in rows)
    db.export(EXT / 'accepted-source-forty', source=sid)
    assert read_snapshot(EXT / 'accepted-source-forty')[1] == {row['record_id']: row for row in rows}
    original = deepcopy(rows)
    rows[0]['sources'][0]['claim_notes'].append('detached mutation')
    rows[0]['property']['reported_value']['number'] = '999'
    assert list(db.records(source=sid)) == original
    before_hashes = read(HERE / 'APPLICATION_INTENT_R38.json')['before_sha256']
    assert all(sha(ROOT / name) == digest for name, digest in before_hashes.items() if not name.endswith('/sources.json'))
    write('CURRENT_CONSUMER_R38.json', {'status': 'passed', 'snapshot': db.snapshot, 'complete_source_records': 40,
        'all_material_property_bytes_unchanged': True, 'source_object_equals_approved_proposal': True,
        'joined_export_roundtrip': 'exact', 'copy_isolation': True, 'graph': graph,
        'new_properties_states_identities': [0, 0, 0], 'unknowns_filled': 0,
        'installation': 'not_run_for_metadata_only_update', 'pushed': False})
    assert all(sha(ROOT / name) == digest for name, digest in inputs.items())
    print(json.dumps({'tests': result.testsRun, 'stable_inputs': len(inputs), 'source_records': 40, 'snapshot': db.snapshot}), flush=True)


if __name__ == '__main__':
    main()
