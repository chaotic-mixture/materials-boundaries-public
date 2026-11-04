"""Compare final installed payload and complete sources with the current native."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from materials_boundaries.database import Database, read_snapshot

OUT = Path(__file__).resolve().parent
BASE = '1893455b0dc75d9ac7e7c27fc798efd7de8a0d04'


def read(path): return json.loads(path.read_bytes())
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    installed = ROOT.parent / 'open-database-evidence/polymer-accepted-install-20261104-r29-r32'
    site = installed / 'venv/Lib/site-packages'
    db = Database()
    delta = read(OUT / 'NATIVE_DELTA_R29_R32.json')
    assert db.snapshot == delta['current_snapshot']
    expected = read(installed / 'BUILD_INPUTS_R29_R32.json')['staged_inputs']
    payload = {name: digest for name, digest in expected.items() if name.startswith('materials_boundaries/')}
    native = {}
    for name, digest in payload.items():
        assert sha(site / name) == digest, name
        if name == 'materials_boundaries/_version.py':
            assert '__version__ = "0.35.0"' in (ROOT / name).read_text('utf-8')
        else:
            assert sha(ROOT / name) == digest, name
            native[name] = digest
    for name in db.data:
        assert read(site / 'materials_boundaries/data' / (name + '.json')) == db.data[name]
    baseline = Database({name: json.loads(subprocess.check_output(['git', 'show', BASE + ':materials_boundaries/data/' + name + '.json'], cwd=ROOT))
                         for name in db.data})
    assert len(baseline.properties) == 5335 and len(db.properties) == 5371
    assert all(db.properties[key] == value for key, value in baseline.properties.items())
    assert baseline.identities == db.identities and baseline.grades == db.grades
    assert set(db.states) - set(baseline.states) == set(delta['new_state_ids'])
    for sid in baseline.states:
        changed = {key for key, value in baseline.states[sid].items() if db.states[sid][key] != value}
        assert changed == set(delta['existing_state_changes'].get(sid, []))
    facts = read(OUT / 'SOURCE_FACTS_R29_R32.json')
    assert all(db.properties[k] == value for k, value in facts['property_records'].items())
    assert all(db.states[k] == value for k, value in facts['state_records'].items())
    assert all(db.sources[k] == value for k, value in facts['source_records'].items())
    exports = {}
    for sid, count in facts['source_counts'].items():
        _, records = read_snapshot(installed / ('installed-export-' + sid))
        assert records == {row['property']['id']: row for row in db.records(source=sid)}
        assert len(records) == count
        exports[sid] = count
    result = {'status': 'current_native_equal_final_reviewed_install', 'snapshot': db.snapshot,
              'baseline_commit': BASE, 'baseline_snapshot': baseline.snapshot,
              'old_complete_properties_unchanged': 5335, 'new_properties': 36, 'new_states': 27,
              'existing_states_limited_changes': 0, 'new_identities_grades_sources': 0,
              'installed_payload_files_verified': len(payload), 'native_payload_files_equal_install': len(native),
              'version_difference': 'Isolated final verification version only; native stays0.35.0.',
              'all_5371_properties_and_three_tables_equal': True,
              'complete_source_query_and_joined_export_counts': exports,
              'native_polymer_summary': db.summary(category='polymer'),
              'full_history_regression': 'not_run', 'HTTP': 'not_run', 'pushed': False,
              'merged_main': False, 'stable_release': False, 'deployed': False}
    with (OUT / 'NATIVE_INSTALLED_EQUIVALENCE_R29_R32.json').open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({'status': result['status'], 'snapshot': db.snapshot, 'joined_exports': sum(exports.values())}))


if __name__ == '__main__':
    main()
