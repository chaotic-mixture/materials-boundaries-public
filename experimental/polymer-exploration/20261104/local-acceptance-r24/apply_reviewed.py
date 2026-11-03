"""Apply the exact independently approved existing-polymer supplement locally."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from materials_boundaries.database import Database, ValidationSession

AREA = ROOT/'experimental/polymer-exploration/20261104'
OUT = Path(__file__).resolve().parent
EXTERNAL = ROOT.parent/'open-database-evidence'


def read(path): return json.loads(path.read_bytes())
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def main():
    assert not (OUT/'APPLICATION_R24.json').exists()
    packet = AREA/'epoxy-flexural-elongation-native-r1'
    manifest = read(packet/'REVIEW_INPUTS_R1.json')
    review = read(packet/'INDEPENDENT_MAPPING_REVIEW_R1.json')
    assert review['decision'] == 'approved'
    assert review['review_inputs_sha256'] == sha(packet/'REVIEW_INPUTS_R1.json')
    for name, digest in manifest['repo_files_sha256'].items(): assert sha(ROOT/name) == digest, name
    install_packet = AREA/'installed-preview-r24'
    install_review = read(install_packet/'INDEPENDENT_REVIEW_R24.json')
    assert install_review['decision'] == 'approved'
    assert install_review['review_inputs_sha256'] == sha(install_packet/'REVIEW_INPUTS_R24.json')
    install_inputs = read(install_packet/'REVIEW_INPUTS_R24.json')
    for name, digest in install_inputs['repo_files_sha256'].items(): assert sha(ROOT/name) == digest, name
    install_dir=Path(install_inputs['external_install_directory_hint'])
    for name,digest in install_inputs['external_evidence_sha256'].items(): assert sha(install_dir/name)==digest,name
    install = read(install_packet/'INSTALLED_VALIDATION_R24.json')
    assert install['installed']['snapshot'] == manifest['combined_snapshot']
    before = Database()
    assert before.snapshot == manifest['baseline_snapshot']
    tables = EXTERNAL/'polymer-epoxy-flexural-elongation-native-20261104-r24/native-tables'
    for name, digest in manifest['external_preview_files_sha256'].items(): assert sha(tables/name) == digest
    after = Database({name:read(tables/(name+'.json')) for name in before.data})
    assert after.snapshot == manifest['combined_snapshot']
    assert all(after.properties[k] == value for k,value in before.properties.items())
    facts=read(AREA/'epoxy-flexural-elongation-native-r1/MAPPING_FACTS_R1.json')
    state_records=facts['state_records'];properties=facts['property_records']
    assert len(state_records)==5 and len(properties)==5
    assert after.identities==before.identities and after.grades==before.grades and set(after.states)==set(before.states)
    assert set(after.properties)-set(before.properties)==set(properties)
    from copy import deepcopy
    for key,old in before.states.items():
        if key in state_records:
            assert after.states[key]==state_records[key]
            restored=deepcopy(after.states[key])
            for field in ('version','property_ids','source_scope'):restored[field]=old[field]
            assert restored==old
        else:assert after.states[key]==old
    assert all(after.properties[k]==v for k,v in properties.items())
    sid=facts['source_record']['id']
    assert after.sources[sid]==facts['source_record'] and set(after.sources)==set(before.sources)
    assert all(after.sources[k]==v for k,v in before.sources.items() if k!=sid)
    restored_source=deepcopy(after.sources[sid]);restored_source['claim_notes'].pop();assert restored_source==before.sources[sid]
    session = ValidationSession(before)
    incremental = session.validate(after)
    assert incremental['executed_property_checks'] == 5322 and incremental['reused_property_checks'] == 0
    write(OUT/'INCREMENTAL_VALIDATION_R24.json', incremental)
    baseline = EXTERNAL/'polymer-native-acceptance-20261104-r24/baseline-tables'
    baseline.mkdir(parents=True, exist_ok=False)
    before_hashes = {}
    for name in before.data:
        source = ROOT/'materials_boundaries/data'/(name+'.json')
        before_hashes[source.name] = sha(source)
        shutil.copyfile(source, baseline/source.name)
    write(OUT/'APPLICATION_INTENT_R24.json', {'baseline_snapshot':before.snapshot,
        'target_snapshot':after.snapshot, 'baseline_table_sha256':before_hashes,
        'recovery_copy_hint':str(baseline), 'target_table_sha256':manifest['external_preview_files_sha256']})
    for name in before.data:
        shutil.copyfile(tables/(name+'.json'), ROOT/'materials_boundaries/data'/(name+'.json'))
    native = Database()
    assert native.snapshot == after.snapshot
    assert all(native.data[name] == after.data[name] for name in native.data)
    write(OUT/'APPLICATION_R24.json', {'status':'reviewed_candidate_applied_locally',
        'applied_at_utc':datetime.now(timezone.utc).isoformat(), 'before_snapshot':before.snapshot,
        'after_snapshot':native.snapshot, 'native_table_sha256':{
            name+'.json':sha(ROOT/'materials_boundaries/data'/(name+'.json')) for name in native.data},
        'counts':{'identities':len(native.identities), 'grades':len(native.grades),
                  'states':len(native.states), 'properties':len(native.properties), 'sources':len(native.sources)},
        'polymer_summary':native.summary(category='polymer'), 'all_old_5317_property_objects_unchanged':True,
        'new_properties':5, 'new_identities':0, 'new_states':0,
        'installed_preview_payload_tables_equal_native':True,
        'full_history_regression':'not_run', 'pushed':False, 'merged_main':False, 'deployed':False})
    print(json.dumps({'status':'local_application_passed','snapshot':native.snapshot,'properties':len(native.properties)}))


if __name__ == '__main__': main()
