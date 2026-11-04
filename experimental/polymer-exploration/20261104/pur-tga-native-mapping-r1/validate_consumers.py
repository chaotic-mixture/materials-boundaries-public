"""Check full candidate records/joins/exports; never write native tables."""
from copy import deepcopy
from pathlib import Path
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
EXTERNAL = ROOT.parent / 'open-database-evidence/polymer-pur-tga-native-mapping-20261104-r1'
sys.path.insert(0, str(ROOT))
from materials_boundaries.database import Database, read_snapshot


def read(name):
    return json.loads((OUT / name).read_bytes())


def main():
    EXTERNAL.mkdir(exist_ok=False)
    before = Database()
    baseline = {name: hashlib.sha256((ROOT / 'materials_boundaries/data' / name).read_bytes()).hexdigest()
                for name in ('materials.json', 'reference_properties.json', 'sources.json')}
    data = deepcopy(before.data)
    states, props, proposal = read('NEW_STATES_R1.json'), read('NEW_PROPERTIES_R1.json'), read('SOURCE_UPDATE_PROPOSAL_R1.json')
    data['materials']['records'].extend(states)
    data['reference_properties']['records'].extend(props)
    sid = proposal['baseline_source']['id']
    assert before.sources[sid] == proposal['baseline_source']
    data['sources']['records'] = [proposal['proposed_source'] if source['id'] == sid else source for source in data['sources']['records']]
    db = Database(data)
    graph = db.validate_scientific_contracts()
    assert db.snapshot == read('VALIDATION_R1.json')['candidate_snapshot']
    checks = []
    for name, filters, count in [('new-twenty-eight', {'source': sid, 'query': '_tga_platinum_pan'}, 28),
                                 ('complete-source-forty', {'source': sid}, 40)]:
        rows = list(db.records(**filters))
        assert len(rows) == count
        db.export(EXTERNAL / name, **filters)
        _, exported = read_snapshot(EXTERNAL / name)
        assert exported == {row['record_id']: row for row in rows}
        for row in rows:
            assert row['property'] == db.properties[row['record_id']]
            assert row['state'] == db.states[row['property']['material_state_id']]
            assert row['identity'] == db.identities[row['state']['identity_id']]
            assert row['sources'] == [db.sources[sid]]
        rows[0]['property']['reported_value']['number'] = '999'
        assert list(db.records(**filters))[0]['property'] == db.properties[rows[0]['record_id']]
        checks.append({'export': name, 'records': count, 'complete_join_roundtrip': True, 'copy_isolation': True})
    assert {p['id']: p for p in props} == {row['record_id']: row['property'] for row in db.records(source=sid, query='_tga_platinum_pan')}
    assert all(hashlib.sha256((ROOT / 'materials_boundaries/data' / name).read_bytes()).hexdigest() == digest for name, digest in baseline.items())
    result = {'scope': 'Unapplied candidate complete joins/exports only', 'candidate_snapshot': db.snapshot,
        'checks': checks, 'graph': graph, 'all28mapping_objects_exact': True, 'native_table_sha256_unchanged': baseline,
        'installation': 'not_run', 'native_applied': False, 'pushed': False}
    with (OUT / 'CANDIDATE_CONSUMER_R1.json').open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({'new_records': 28, 'complete_source_records': 40, 'snapshot': db.snapshot, 'native_applied': False}), flush=True)


if __name__ == '__main__':
    main()
