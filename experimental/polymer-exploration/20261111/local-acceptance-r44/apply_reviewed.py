"""Apply exact independently approved NR mapping with before-byte backups."""
from pathlib import Path
from copy import deepcopy
import hashlib,json,shutil,subprocess,sys
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
MAPPING=HERE.parent/'nr-clay-lfa-native-mapping-r1'
EXT=ROOT.parent/'open-database-evidence/polymer-native-acceptance-20261111-r44'
sys.path.insert(0,str(ROOT))
from materials_boundaries.database import Database
from materials_boundaries.material_references import validate_material_catalog
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def encoded(v):return (json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
def write(n,v):
    with (HERE/n).open('xb') as f:f.write(encoded(v))
def main():
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()=='847be1bb03e37e330e8de18341dbfca6715bd8b0'
    assert subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()=='experimental/open-database'
    entry=MAPPING/'REVIEW_INPUTS_R1.json';receipt=read(MAPPING/'INDEPENDENT_MAPPING_REVIEW_R1.json')
    assert sha(entry)=='ec200d79d6479afad8388210ae317d0d9ce6cb8a69f4712f7d5656f69958b312'
    assert receipt['decision']=='approved' and receipt['review_inputs_sha256']==sha(entry)
    for field in ['repo_files_sha256','native_files_sha256','external_files_sha256']:
        for name,digest in read(entry)[field].items():assert sha(Path(name) if field=='external_files_sha256' else ROOT/name)==digest,name
    before=Database();data=deepcopy(before.data)
    states=read(MAPPING/'NEW_STATES_R1.json');source=read(MAPPING/'SOURCE_UPDATE_R1.json');props=read(MAPPING/'NEW_PROPERTIES_R1.json')
    assert before.sources[source['before']['id']]==source['before']
    assert all(state['id'] not in before.states for state in states)
    data['materials']['records'].extend(states)
    data['sources']['records']=[source['after'] if s['id']==source['before']['id'] else s for s in data['sources']['records']]
    data['reference_properties']['records'].extend(props)
    validate_material_catalog(*(data[n] for n in ['materials','reference_properties','sources']))
    after=Database(data)
    assert after.snapshot==read(MAPPING/'VALIDATION_R1.json')['candidate_snapshot']
    assert all(after.properties[k]==v for k,v in before.properties.items())
    assert before.identities==after.identities and before.grades==after.grades
    assert all(after.states[k]==v for k,v in before.states.items())
    paths={f'materials_boundaries/data/{n}.json':encoded(data[n]) for n in ['materials','reference_properties','sources']}
    backup=EXT/'baseline-tables';backup.mkdir(parents=True,exist_ok=False)
    hashes={}
    for name in paths:
        hashes[name]=sha(ROOT/name);shutil.copyfile(ROOT/name,backup/Path(name).name)
        assert sha(backup/Path(name).name)==hashes[name]
    write('APPLICATION_INTENT_R44.json',dict(before_sha256=hashes,after_sha256={n:hashlib.sha256(b).hexdigest() for n,b in paths.items()},snapshot=after.snapshot,backup=str(backup),mapping_entry_sha256=sha(entry),only_write=list(paths)))
    try:
        for name,content in paths.items():(ROOT/name).write_bytes(content)
        assert all((ROOT/name).read_bytes()==content for name,content in paths.items())
    except BaseException:
        for name in paths:shutil.copyfile(backup/Path(name).name,ROOT/name)
        raise
    write('APPLICATION_R44.json',dict(status='exact_reviewed_NR_clay_eighteen_LFA_properties_applied_locally',snapshot=after.snapshot,after_sha256={n:sha(ROOT/n) for n in paths},properties=len(after.properties),states=len(after.states),new_properties=18,new_states=6,new_sources=0,new_identities=0,all_old5432properties_unchanged=True,all_old5271states_unchanged=True,installation_final_review='pending',pushed=False))
    print(json.dumps({'properties':len(after.properties),'states':len(after.states),'snapshot':after.snapshot}),flush=True)
if __name__=='__main__':main()
