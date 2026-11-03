"""Read native polymer evidence classes and preserve actual unknown statuses.

This is a descriptive inventory, not a completeness score or independent source
verification. Reported fields may still carry important limitations in notes.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from materials_boundaries.database import Database


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    db = Database()
    conditions = ('temperature','test_standard','test_method','direction','conditioning','loading_rate')
    by_source = defaultdict(list)
    evidence_classes = Counter()
    records = []
    pending_path = ROOT/'experimental/polymer-exploration/20261103/filament-drawing-method-audit/native-correction-candidate-r1.json'
    pending = json.loads(pending_path.read_bytes())
    pending_ids = {row['id'] for row in pending['reference_properties']['records']}
    for prop in db.properties.values():
        state = db.states[prop['material_state_id']]
        identity = db.identities[state['identity_id']]
        if identity['category'] != 'polymer':
            continue
        evidence_classes[prop['evidence_kind']] += 1
        if prop['evidence_kind'] != 'published_experimental_reference':
            continue
        by_source[prop['source_id']].append(prop)
        records.append({'record_id':prop['id'],'identity_id':identity['id'],'state_id':state['id'],
                        'source_id':prop['source_id'],'quantity':prop['quantity'],
                        'conditions':{key:{field:prop['conditions'][key][field]
                                          for field in ('status','text','notes')} for key in conditions},
                        'sample_count':prop['sample_count'],
                        'uncertainty_status':prop['uncertainty_status'],
                        'uncertainty_note':prop['uncertainty_note'],
                        'pending_unapplied_filament_amendment':prop['id'] in pending_ids})
    source_rows = []
    for source_id, props in sorted(by_source.items(),key=lambda pair:(-len(pair[1]),pair[0])):
        source = db.sources[source_id]
        source_rows.append({'source_id':source_id,'title':source['title'],'doi':source.get('doi'),
                            'license':source['license'],'native_properties':len(props),
                            'native_identities':len({db.states[p['material_state_id']]['identity_id'] for p in props}),
                            'native_states':len({p['material_state_id'] for p in props}),
                            'condition_status_counts':{key:dict(Counter(p['conditions'][key]['status'] for p in props)) for key in conditions},
                            'sample_count_value_missing':sum(p['sample_count']['value'] is None for p in props),
                            'uncertainty_status_counts':dict(Counter(p['uncertainty_status'] for p in props)),
                            'record_ids':sorted(p['id'] for p in props)})
    aggregate = {key:dict(Counter(row['conditions'][key]['status'] for row in records)) for key in conditions}
    result = {'schema':'polymer-native-condition-gap-inventory/1',
              'scope':'Native evidence-class description only; not proof of experimental validity or complete conditioning.',
              'database_snapshot':db.snapshot,
              'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'polymer_evidence_class_counts':dict(evidence_classes),
              'experimental_class_records':len(records),
              'experimental_class_primary_sources':len(source_rows),
              'experimental_class_identities':len({r['identity_id'] for r in records}),
              'experimental_class_states':len({r['state_id'] for r in records}),
              'condition_status_counts':aggregate,
              'sample_count_value_missing':sum(r['sample_count']['value'] is None for r in records),
              'uncertainty_status_counts':dict(Counter(r['uncertainty_status'] for r in records)),
              'source_rows':source_rows,'records':sorted(records,key=lambda r:r['record_id']),
              'pending_amendment_sha256':hashlib.sha256(pending_path.read_bytes()).hexdigest(),
              'limitations':['1000computational records are not included in experimental gap counts.',
                             'A reported conditioning field may describe preparation while moisture equilibration remains unknown; read notes.',
                             'Untyped uncertainty can include source avedev values; it does not mean no deviation was reported.',
                             'Missing exact sample count is not zero specimens.',
                             'Native statuses remain unchanged even where an unapplied amendment has stronger source evidence.',
                             'Source counts here concern primary property sources,not all joined bibliographic sources.'],
              'native_applied':False,'admitted_increment':0,'independent_review':'not_claimed'}
    assert len(records)==50 and len(source_rows)==12
    assert len(result['records'])==len({r['record_id'] for r in result['records']})
    assert Database().snapshot==db.snapshot
    with args.output.open('x',encoding='utf-8') as stream:
        json.dump(result,stream,ensure_ascii=False,indent=2)
        stream.write('\n')
    print(json.dumps({k:result[k] for k in ('database_snapshot','experimental_class_records',
          'experimental_class_primary_sources','experimental_class_identities','experimental_class_states',
          'sample_count_value_missing','uncertainty_status_counts')}))


if __name__ == '__main__':
    main()
