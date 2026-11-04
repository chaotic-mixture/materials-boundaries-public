"""Export complete current affected joins and exact32-property cumulative delta."""
from pathlib import Path
from copy import deepcopy
import json
import sys

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
EXT = ROOT.parent / 'open-database-evidence/polymer-native-acceptance-20261104-delivery-r36-r38'
sys.path.insert(0, str(ROOT))
from materials_boundaries.database import Database, read_snapshot


def main():
    EXT.mkdir(exist_ok=False)
    delta = json.loads((HERE / 'NATIVE_DELTA_R36_R38.json').read_bytes())
    db = Database()
    assert db.snapshot == delta['snapshot']
    expected = {p['id']: p for p in delta['new_properties']}
    assert len(expected) == 32 and all(db.properties[key] == value for key, value in expected.items())
    checks = []
    for name, filters, count in [('new-four-dma', dict(quantity='glass_transition_temperature', source='ivdre_2024_lpo_rigid_pur'), 4),
            ('new-twenty-eight', dict(query='_tga_platinum_pan', source='ivdre_2024_lpo_rigid_pur'), 28),
            ('complete-source-forty', dict(source='ivdre_2024_lpo_rigid_pur'), 40),
            ('epoxy-source-forty', dict(source='tarasov_2022_pna_bpf_epoxy'), 40)]:
        rows = list(db.records(**filters))
        assert len(rows) == count
        original = deepcopy(rows)
        db.export(EXT / ('accepted-' + name), **filters)
        assert read_snapshot(EXT / ('accepted-' + name))[1] == {row['record_id']: row for row in rows}
        for row in rows:
            assert row['property'] == db.properties[row['record_id']]
            assert row['state'] == db.states[row['property']['material_state_id']]
            assert row['identity'] == db.identities[row['state']['identity_id']]
            assert row['sources'] == [db.sources[filters['source']]]
        rows[0]['sources'][0]['claim_notes'].append('detached mutation')
        rows[0]['property']['reported_value']['number'] = '999'
        assert list(db.records(**filters)) == original
        checks.append({'export': name, 'complete_records': count, 'roundtrip': 'exact', 'copy_isolation': True})
    with (HERE / 'ACTUAL_CONSUMER_R36_R38.json').open('x', encoding='utf-8', newline='\n') as stream:
        json.dump({'snapshot': db.snapshot, 'new32properties_exact': True, 'affected_source_join_records': 80,
            'checks': checks, 'installation': 'pending_fresh_delivery_install', 'pushed': False}, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print('32new properties and80affected fulljoins/export/roundtrip/copyisolation passed')


if __name__ == '__main__':
    main()
