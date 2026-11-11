"""Apply exact independently approved existing Sylgard uncorrected extension mapping with before-byte backups."""
from pathlib import Path
from copy import deepcopy
import hashlib,json,shutil,subprocess,sys
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
MAPPING=HERE.parent/'sylgard-extension-native-mapping-r1'
EXT=ROOT.parent/'open-database-evidence/polymer-native-acceptance-20261112-r57'
sys.path.insert(0,str(ROOT))
from materials_boundaries.database import Database
from materials_boundaries.material_references import validate_material_catalog
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def encoded(v):return (json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
def write(n,v):
    with (HERE/n).open('xb') as f:f.write(encoded(v))
def main():
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()=='3880c8ad4c83d8a3c4decf71e130e021b91a8c0d'
    assert subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()=='experimental/open-database'
    entry=MAPPING/'REVIEW_INPUTS_R1.json';receipt=read(MAPPING/'INDEPENDENT_MAPPING_REVIEW_R1.json')
    assert sha(entry)=='ccf9a70838c25c63db1b702c2fd6dd95471cb44a5aff974ff63f52e0f5ceb3db'
    assert receipt['decision']=='approved' and receipt['review_inputs_sha256']==sha(entry)
    for field in ['repo_files_sha256','native_files_sha256','external_files_sha256']:
        for name,digest in read(entry)[field].items():assert sha(Path(name) if field=='external_files_sha256' else ROOT/name)==digest,name
    before=Database();data=deepcopy(before.data)
    states=read(MAPPING/'STATE_UPDATES_R1.json');props=read(MAPPING/'NEW_PROPERTIES_R1.json')
    assert len(states)==len(props)==5
    index={s['before']['id']:s for s in states}
    assert len(index)==5 and all(before.states[k]==s['before'] for k,s in index.items())
    data['materials']['records']=[index[s['id']]['after'] if s['id'] in index else s for s in data['materials']['records']]
    data['reference_properties']['records'].extend(props)
    source=read(MAPPING/'SOURCE_UPDATE_R1.json');key=source['before']['id']
    assert before.sources[key]==source['before']
    data['sources']['records']=[source['after'] if s['id']==key else s for s in data['sources']['records']]
    validate_material_catalog(*(data[n] for n in ['materials','reference_properties','sources']))
    after=Database(data)
    assert after.snapshot==read(MAPPING/'VALIDATION_R1.json')['snapshot']
    assert all(after.properties[k]==v for k,v in before.properties.items())
    assert before.identities==after.identities and before.grades==after.grades
    assert after.sources[key]==source['after'] and all(after.sources[k]==v for k,v in before.sources.items() if k!=key)
    for k,v in before.states.items():
        if k not in index:assert after.states[k]==v
        else:
            assert v['version']=='1.0.1' and after.states[k]['version']=='1.0.2'
            assert {n:x for n,x in v.items() if n not in ('version','property_ids')}=={n:x for n,x in after.states[k].items() if n not in ('version','property_ids')}
            assert all(n in after.states[k]['property_ids'] for n in v['property_ids']) and len(after.states[k]['property_ids'])==3
    paths={f'materials_boundaries/data/{n}.json':encoded(data[n]) for n in ['materials','reference_properties','sources']}
    backup=EXT/'baseline-tables';backup.mkdir(parents=True,exist_ok=False)
    hashes={}
    for name in paths:
        hashes[name]=sha(ROOT/name);shutil.copyfile(ROOT/name,backup/Path(name).name)
        assert sha(backup/Path(name).name)==hashes[name]
    write('APPLICATION_INTENT_R57.json',dict(before_sha256=hashes,after_sha256={n:hashlib.sha256(b).hexdigest() for n,b in paths.items()},snapshot=after.snapshot,backup=str(backup),mapping_entry_sha256=sha(entry),only_write=list(paths)))
    try:
        for name,content in paths.items():(ROOT/name).write_bytes(content)
        assert all((ROOT/name).read_bytes()==content for name,content in paths.items())
    except BaseException:
        for name in paths:shutil.copyfile(backup/Path(name).name,ROOT/name)
        raise
    write('APPLICATION_R57.json',dict(status='exact_reviewed_existing_sylgard_uncorrected_extensions_applied_locally',snapshot=after.snapshot,after_sha256={n:sha(ROOT/n) for n in paths},properties=len(after.properties),states=len(after.states),new_properties=5,new_states=0,revised_states=5,new_sources=0,updated_sources=1,new_identities=0,all_old5631properties_unchanged=True,other5364states_unchanged=True,installation_final_review='pending',pushed=False))
    print(json.dumps({'properties':len(after.properties),'states':len(after.states),'snapshot':after.snapshot}),flush=True)
if __name__=='__main__':main()
