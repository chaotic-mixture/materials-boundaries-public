"""Prepare a source-only revision, preserving every material/property object."""
from pathlib import Path
from copy import deepcopy
import hashlib,json,shutil,sys
from jsonschema import Draft202012Validator,FormatChecker
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT))
from materials_boundaries.database import Database,read_snapshot,compare_snapshots
OUT=Path(__file__).resolve().parent
AREA=OUT.parent
AUDIT=AREA/'pla-pcl-pdf-condition-followup-r1'
EXT=ROOT.parent/'open-database-evidence/polymer-pla-pcl-source-metadata-preview-20261104-r1'
SID='delgado_aguilar_2020_pla_pcl'
BASE='b4c2f6c279400bd67848c4ec049a7050f9c984ad4c247702693596b1da74a306'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def write(p,d):
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(d,f,ensure_ascii=False,indent=2);f.write('\n')
def bound(entry,review):
    assert review['decision']=='approved' and sha(entry)==review['review_inputs_sha256']
    d=read(entry)
    for field in ['repo_files_sha256','native_files_sha256','external_files_sha256']:
        for n,h in d.get(field,{}).items():assert sha(Path(n) if field=='external_files_sha256' else ROOT/n)==h,n
    return d
def main():
    assert not EXT.exists() and not (OUT/'VALIDATION_R1.json').exists()
    bound(AUDIT/'REVIEW_INPUTS_R1.json',read(AUDIT/'INDEPENDENT_REVIEW_R1.json'))
    before=Database();assert before.snapshot==BASE
    proposal=read(AUDIT/'SOURCE_UPDATE_PROPOSAL_R1.json')
    old=proposal['baseline_source'];new=proposal['proposed_source'];assert before.sources[SID]==old
    assert {k for k in set(old)|set(new) if old.get(k)!=new.get(k)}=={'read_status','urls','claim_notes','provenance'}
    assert new['urls'][:-2]==old['urls'] and new['claim_notes'][:-1]==old['claim_notes']
    assert new['provenance']['curation_date']==old['provenance']['curation_date']
    assert new['provenance']['method'].startswith(old['provenance']['method'])
    data=deepcopy(before.data)
    for i,s in enumerate(data['sources']['records']):
        if s['id']==SID:data['sources']['records'][i]=deepcopy(new);break
    after=Database(data)
    assert after.identities==before.identities and after.grades==before.grades and after.states==before.states and after.properties==before.properties
    assert all(after.sources[k]==v for k,v in before.sources.items() if k!=SID)
    for table in data:
        Draft202012Validator(read(ROOT/'schemas'/(table+'.schema.json')),format_checker=FormatChecker()).validate(data[table])
    graph=after.validate_scientific_contracts()
    EXT.mkdir();tables=EXT/'native-tables';tables.mkdir()
    for table in data:
        p=tables/(table+'.json')
        if table=='sources':write(p,data[table])
        else:shutil.copyfile(ROOT/'materials_boundaries/data'/p.name,p)
    before.export(EXT/'before-source',source=SID);after.export(EXT/'after-source',source=SID)
    diff=compare_snapshots(EXT/'before-source',EXT/'after-source')
    ids=sorted(p['id'] for p in before.properties.values() if p['source_id']==SID)
    assert len(ids)==25 and diff['modified']==ids and not diff['added'] and not diff['deleted'] and diff['affected_sources']==[SID]
    _,exported=read_snapshot(EXT/'after-source')
    assert exported=={r['property']['id']:r for r in after.records(source=SID)}
    # Unrelated joined objects change only their database snapshot envelope.
    for sid,count in [('ewurum_mcdonald_2025_pbs_lignin',55)]:
        a=list(before.records(source=sid));b=list(after.records(source=sid));assert len(a)==len(b)==count
        for x,y in zip(a,b):
            x.pop('database_snapshot');y.pop('database_snapshot');assert x==y
    before.export(EXT/'before-unrelated',query='C11000',quantity='mass_density')
    after.export(EXT/'after-unrelated',query='C11000',quantity='mass_density')
    unrelated=compare_snapshots(EXT/'before-unrelated',EXT/'after-unrelated')
    assert not unrelated['modified'] and not unrelated['added'] and not unrelated['deleted']
    facts={'source_id':SID,'baseline_source':old,'source_record':new,'affected_property_ids':ids}
    result={'schema':'source-only-native-preview/1','baseline_snapshot':before.snapshot,'preview_snapshot':after.snapshot,'counts':{'properties':len(after.properties),'states':len(after.states),'identities':len(after.identities),'grades':len(after.grades),'sources':len(after.sources)},'all5371_properties_unchanged':True,'all5245_states_unchanged':True,'all_identities_grades_unchanged':True,'sole_source_changed':SID,'source_filtered_export_modified':25,'unrelated55_joined_objects_unchanged_except_snapshot':True,'unrelated_C11000_diff_modified':0,'three_schema_format':'passed','current_graph':graph,'new_properties_states_identities':0,'unknown_conditions_filled':0,'unit_suites':'not_run_at_preview','actual_installation':'not_run_metadata_only_current_native_not_packaged','full_history_regression':'not_run','native_applied':False,'pushed':False}
    write(OUT/'MAPPING_FACTS_R1.json',facts);write(OUT/'VALIDATION_R1.json',result);write(OUT/'SOURCE_EXPORT_DIFF_R1.json',diff)
    write(EXT/'UNRELATED_EXPORT_DIFF_R1.json',unrelated)
    print(json.dumps({'snapshot':after.snapshot,'modified_joined_source_records':25,'property_state_changes':0,'graph':graph}))
if __name__=='__main__':main()
