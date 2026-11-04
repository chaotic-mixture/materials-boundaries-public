"""Apply only the independently reviewed PLA/PCL source-metadata bytes locally."""
from pathlib import Path
import hashlib,json,shutil,sys
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT))
from materials_boundaries.database import Database,read_snapshot
OUT=Path(__file__).resolve().parent
AREA=OUT.parent
EXT=ROOT.parent/'open-database-evidence'
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(d,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
    assert not (OUT/'APPLICATION_INTENT_R32.json').exists()
    folder=AREA/'pla-pcl-source-metadata-native-r1';entry=folder/'REVIEW_INPUTS_R1.json';review=read(folder/'INDEPENDENT_MAPPING_REVIEW_R1.json')
    assert review['decision']=='approved' and review['review_inputs_sha256']==sha(entry)
    frozen=read(entry)
    for field in ['repo_files_sha256','native_files_sha256','external_files_sha256']:
        for n,h in frozen.get(field,{}).items():assert sha(Path(n) if field=='external_files_sha256' else ROOT/n)==h,n
    result=read(folder/'VALIDATION_R1.json');facts=read(folder/'MAPPING_FACTS_R1.json')
    before=Database();assert before.snapshot==result['baseline_snapshot']
    preview=EXT/'polymer-pla-pcl-source-metadata-preview-20261104-r1/native-tables'
    after=Database({n:read(preview/(n+'.json')) for n in before.data})
    assert after.snapshot==result['preview_snapshot'] and result['current_graph']['status']=='material_contracts_passed'
    assert after.properties==before.properties and after.states==before.states and after.identities==before.identities and after.grades==before.grades
    sid=facts['source_id'];assert before.sources[sid]==facts['baseline_source'] and after.sources[sid]==facts['source_record']
    assert set(after.sources)==set(before.sources) and all(after.sources[k]==v for k,v in before.sources.items() if k!=sid)
    _,exported=read_snapshot(preview.parent/'after-source');assert exported=={r['property']['id']:r for r in after.records(source=sid)} and len(exported)==25
    native=ROOT/'materials_boundaries/data'
    unchanged={n:sha(native/n) for n in ['materials.json','reference_properties.json']}
    assert all(sha(preview/n)==h for n,h in unchanged.items())
    backup=EXT/'polymer-native-acceptance-20261104-r32/baseline-tables';backup.mkdir(parents=True,exist_ok=False)
    hashes={}
    for n in before.data:
        p=native/(n+'.json');hashes[p.name]=sha(p);shutil.copyfile(p,backup/p.name);assert sha(backup/p.name)==hashes[p.name]
    write(OUT/'APPLICATION_INTENT_R32.json',{'baseline_snapshot':before.snapshot,'target_snapshot':after.snapshot,'baseline_table_sha256':hashes,'target_sources_sha256':sha(preview/'sources.json'),'only_write':'materials_boundaries/data/sources.json','recovery_copy_hint':str(backup)})
    shutil.copyfile(preview/'sources.json',native/'sources.json')
    assert sha(native/'sources.json')==sha(preview/'sources.json') and all(sha(native/n)==h for n,h in unchanged.items())
    current=Database();assert current.data==after.data and current.snapshot==after.snapshot
    write(OUT/'APPLICATION_R32.json',{'status':'reviewed_source_metadata_applied_locally','applied_at_utc':datetime.now(timezone.utc).isoformat(),'before_snapshot':before.snapshot,'after_snapshot':current.snapshot,'native_table_sha256':{p.name:sha(p) for p in native.glob('*.json') if p.name in hashes},'counts':result['counts'],'all5371_properties_and5245_states_unchanged':True,'source_record_modified':sid,'affected_joined_exports':25,'new_properties_states_identities':0,'unknowns_filled':0,'graph':'reused exact approved preview tables;not rerun','installation':'current source metadata not packaged;previous r31 wheel retains prior source bytes','unit_suites':'pending_scoped_daily_check','pushed':False,'merged_main':False,'deployed':False})
    print(json.dumps({'snapshot':current.snapshot,'source_records_modified':1,'property_state_changes':0}))
if __name__=='__main__':main()
