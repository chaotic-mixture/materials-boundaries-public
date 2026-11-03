"""Compare current native tables and all payload bytes to the reviewed install."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from materials_boundaries.database import Database, read_snapshot


def read(path):
    return json.loads(path.read_bytes())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    out = Path(__file__).resolve().parent
    area = out.parent
    evidence = ROOT.parent / 'open-database-evidence'
    installed = evidence / 'polymer-installed-preview-20261103-r21'
    site = installed / 'venv/Lib/site-packages'
    db = Database()
    application = read(out / 'APPLICATION_R21.json')
    assert db.snapshot == application['after_snapshot']
    expected = read(installed / 'BUILD_INPUTS_R21.json')['staged_inputs']
    payload = {name: digest for name, digest in expected.items() if name.startswith('materials_boundaries/')}
    current_hashes = {}
    for name, digest in payload.items():
        assert sha(site / name) == digest, name
        if name == 'materials_boundaries/_version.py':
            assert '__version__ = "0.35.0"' in (ROOT / name).read_text(encoding='utf-8')
            continue
        assert sha(ROOT / name) == digest, name
        current_hashes[name] = digest
    for name in db.data:
        assert read(site / 'materials_boundaries/data' / (name + '.json')) == db.data[name]
    baseline = evidence / 'polymer-native-acceptance-20261103-r21/baseline-tables'
    old = Database({name: read(baseline / (name + '.json')) for name in db.data})
    assert len(old.properties) == 5301 and len(db.properties) == 5306
    assert all(db.properties[key] == value for key, value in old.properties.items())
    assert old.identities == db.identities and old.grades == db.grades
    assert all(db.states[k] == v for k,v in old.states.items())
    facts=read(area/'sylgard-hardness-source-draft-r1/SOURCE_FACTS_R1.json')['rows']
    assert set(db.states)-set(old.states) == {f['proposed_state_id'] for f in facts}
    assert set(db.properties)-set(old.properties) == {f['new_property_id'] for f in facts}
    assert set(old.sources) == set(db.sources)
    exports = {}
    for sid in ('johnston_2014_bulk_sylgard184',):
        manifest, rows = read_snapshot(installed / ('installed-export-' + sid))
        assert rows == {row['property']['id']: row for row in db.records(source=sid)}
        exports[sid] = len(rows)
    result = {'status': 'native_equal_reviewed_installed_payload', 'snapshot': db.snapshot,
              'baseline_snapshot': old.snapshot, 'old_property_objects_unchanged': 5301,
              'new_properties': 5, 'new_identities': 0, 'new_states': 5,
              'installed_payload_files_verified': len(payload),
              'native_payload_files_equal_install': len(current_hashes),
              'version_difference': 'isolated preview version only; native stays0.35.0',
              'all_5306_properties_and_three_tables_equal': True,
              'installed_exports_equal_current_native': exports,
              'native_polymer_summary': db.summary(category='polymer'),
              'full_history_regression': 'not_run', 'pushed': False, 'merged_main': False, 'deployed': False}
    with (out / 'NATIVE_INSTALLED_EQUIVALENCE_R21.json').open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({'status': result['status'], 'snapshot': db.snapshot, 'properties': len(db.properties)}))


if __name__ == '__main__':
    main()
