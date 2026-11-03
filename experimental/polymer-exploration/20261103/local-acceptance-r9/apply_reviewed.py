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

AREA = ROOT/'experimental/polymer-exploration/20261103'
OUT = Path(__file__).resolve().parent
EXTERNAL = ROOT.parent/'open-database-evidence'


def read(path): return json.loads(path.read_bytes())
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def main():
    assert not (OUT/'APPLICATION_R9.json').exists()
    packet = AREA/'nbr-specified-elongation-native-r1'
    manifest = read(packet/'INSTALL_INPUTS_R1.json')
    review = read(packet/'INDEPENDENT_IMPLEMENTATION_REVIEW_R1.json')
    assert review['decision'] == 'approved'
    assert review['review_inputs_sha256'] == sha(packet/'REVIEW_INPUTS_R1.json')
    for name, digest in manifest['repo_files_sha256'].items(): assert sha(ROOT/name) == digest, name
    install_packet = AREA/'installed-preview-r9'
    install_review = read(install_packet/'INDEPENDENT_REVIEW_R9.json')
    assert install_review['decision'] == 'approved'
    assert install_review['review_inputs_sha256'] == sha(install_packet/'REVIEW_INPUTS_R9.json')
    install = read(install_packet/'INSTALLED_VALIDATION_R9.json')
    assert install['installed']['snapshot'] == manifest['combined_snapshot']
    before = Database()
    assert before.snapshot == manifest['baseline_snapshot']
    tables = EXTERNAL/'polymer-nbr-specified-elongation-20261103-r1/native-tables'
    for name, digest in manifest['external_preview_files_sha256'].items(): assert sha(tables/name) == digest
    after = Database({name:read(tables/(name+'.json')) for name in before.data})
    assert after.snapshot == manifest['combined_snapshot']
    assert all(after.properties[k] == value for k,value in before.properties.items())
    session = ValidationSession(before)
    incremental = session.validate(after)
    assert incremental['executed_property_checks'] == 5245 and incremental['reused_property_checks'] == 0
    write(OUT/'INCREMENTAL_VALIDATION_R9.json', incremental)
    baseline = EXTERNAL/'polymer-native-acceptance-20261103-r9/baseline-tables'
    baseline.mkdir(parents=True, exist_ok=False)
    before_hashes = {}
    for name in before.data:
        source = ROOT/'materials_boundaries/data'/(name+'.json')
        before_hashes[source.name] = sha(source)
        shutil.copyfile(source, baseline/source.name)
    write(OUT/'APPLICATION_INTENT_R9.json', {'baseline_snapshot':before.snapshot,
        'target_snapshot':after.snapshot, 'baseline_table_sha256':before_hashes,
        'recovery_copy_hint':str(baseline), 'target_table_sha256':manifest['external_preview_files_sha256']})
    for name in before.data:
        shutil.copyfile(tables/(name+'.json'), ROOT/'materials_boundaries/data'/(name+'.json'))
    native = Database()
    assert native.snapshot == after.snapshot
    assert all(native.data[name] == after.data[name] for name in native.data)
    write(OUT/'APPLICATION_R9.json', {'status':'reviewed_candidate_applied_locally',
        'applied_at_utc':datetime.now(timezone.utc).isoformat(), 'before_snapshot':before.snapshot,
        'after_snapshot':native.snapshot, 'native_table_sha256':{
            name+'.json':sha(ROOT/'materials_boundaries/data'/(name+'.json')) for name in native.data},
        'counts':{'identities':len(native.identities), 'grades':len(native.grades),
                  'states':len(native.states), 'properties':len(native.properties), 'sources':len(native.sources)},
        'polymer_summary':native.summary(category='polymer'), 'all_old_5243_property_objects_unchanged':True,
        'new_properties':2, 'new_identities':0, 'new_states':0,
        'installed_preview_payload_tables_equal_native':True,
        'full_history_regression':'not_run', 'pushed':False, 'merged_main':False, 'deployed':False})
    print(json.dumps({'status':'local_application_passed','snapshot':native.snapshot,'properties':len(native.properties)}))


if __name__ == '__main__': main()
