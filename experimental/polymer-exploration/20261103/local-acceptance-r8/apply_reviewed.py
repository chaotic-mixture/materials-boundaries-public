"""Apply the exact reviewed REF property and scoped old-record wording revisions."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import sys

ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT))
from materials_boundaries.database import Database, ValidationSession
AREA=ROOT/'experimental/polymer-exploration/20261103'
OUT=Path(__file__).resolve().parent
EXT=ROOT.parent/'open-database-evidence'


def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,obj):
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')


def main():
    assert not (OUT/'APPLICATION_R8.json').exists()
    packet=AREA/'nbr-ref-strength-supplement-r1';review=read(packet/'INDEPENDENT_REVIEW_R1.json')
    assert review['decision']=='approved' and review['review_inputs_sha256']==sha(packet/'REVIEW_INPUTS_R1.json')
    manifest=read(packet/'INSTALL_INPUTS_R1.json')
    for name,digest in manifest['repo_files_sha256'].items():assert sha(ROOT/name)==digest,name
    install=AREA/'installed-preview-r8';approval=read(install/'INDEPENDENT_REVIEW_R8.json')
    assert approval['decision']=='approved' and approval['review_inputs_sha256']==sha(install/'REVIEW_INPUTS_R8.json')
    before=Database();assert before.snapshot==review['baseline_snapshot']
    tables=EXT/'polymer-nbr-strength-20261103-r1/candidate-preview/native-tables'
    for name,digest in manifest['external_preview_files_sha256'].items():assert sha(tables/name)==digest,name
    after=Database({name:read(tables/(name+'.json')) for name in before.data})
    assert after.snapshot==review['preview_snapshot']==read(install/'INSTALLED_VALIDATION_R8.json')['installed']['snapshot']
    revised=[]
    for pid,old in before.properties.items():
        new=after.properties[pid]
        if new!=old:
            probe=deepcopy(new);probe['version']=old['version'];probe['source_discrepancies'][0]['disposition']=old['source_discrepancies'][0]['disposition']
            assert probe==old
            revised.append(pid)
    assert len(revised)==6
    assert after.properties['refprop_perbunan3445f_tamas_benyei2025_ref_mass_density']==before.properties['refprop_perbunan3445f_tamas_benyei2025_ref_mass_density']
    incremental=ValidationSession(before).validate(after)
    assert incremental['executed_property_checks']==5243 and incremental['reused_property_checks']==0
    write(OUT/'INCREMENTAL_VALIDATION_R8.json',incremental)
    backup=EXT/'polymer-native-acceptance-20261103-r8/baseline-tables';backup.mkdir(parents=True,exist_ok=False)
    baseline={}
    for name in before.data:
        source=ROOT/'materials_boundaries/data'/(name+'.json');baseline[source.name]=sha(source);shutil.copyfile(source,backup/source.name)
    write(OUT/'APPLICATION_INTENT_R8.json',{'before_snapshot':before.snapshot,'target_snapshot':after.snapshot,'baseline_table_sha256':baseline,'recovery_copy_hint':str(backup),'target_table_sha256':manifest['external_preview_files_sha256']})
    for name in before.data:shutil.copyfile(tables/(name+'.json'),ROOT/'materials_boundaries/data'/(name+'.json'))
    native=Database();assert native.snapshot==after.snapshot and native.data==after.data
    write(OUT/'APPLICATION_R8.json',{'status':'reviewed_candidate_applied_locally','applied_at_utc':datetime.now(timezone.utc).isoformat(),'before_snapshot':before.snapshot,'after_snapshot':native.snapshot,
        'native_table_sha256':{name+'.json':sha(ROOT/'materials_boundaries/data'/(name+'.json')) for name in native.data},
        'counts':{'identities':len(native.identities),'grades':len(native.grades),'states':len(native.states),'properties':len(native.properties),'sources':len(native.sources)},
        'polymer_summary':native.summary(category='polymer'),'new_properties':1,'new_states':0,'new_identities':0,'six_scope_revised_property_ids':revised,
        'all_existing_numeric_statistical_condition_method_evidence_fields_unchanged':True,'entire_REF_density_property_unchanged':True,
        'full_history_regression':'not_run','pushed':False,'merged_main':False,'deployed':False})
    print(json.dumps({'status':'local_application_passed','snapshot':native.snapshot,'properties':len(native.properties)}))


if __name__=='__main__':main()
