"""Apply exact approved enthalpy candidates and scoped existing-context revisions."""
from pathlib import Path
from copy import deepcopy
import hashlib,json,subprocess,shutil,sys
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
MAPPING=HERE.parent/'pbs-melting-enthalpy-native-mapping-r3'
EXT=ROOT.parent/'open-database-evidence/polymer-native-acceptance-20261112-r64'
sys.path.insert(0,str(ROOT))
from materials_boundaries.database import Database
from materials_boundaries.material_references import validate_material_catalog
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def encoded(v):return (json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
def write(n,v):
    with (HERE/n).open('xb') as f:f.write(encoded(v))
def main():
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()=='dd91c1841e3630bd7de0cbeb1707ad3276080272'
    assert subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()=='experimental/open-database'
    entry=MAPPING/'REVIEW_MAPPING_INPUTS_R3.json';receipt=read(MAPPING/'INDEPENDENT_MAPPING_REVIEW_R3.json')
    assert receipt['decision']=='approved' and receipt['review_inputs_sha256']==sha(entry)
    for group in ['repo_files_sha256','external_files_sha256','native_files_sha256']:
        for n,h in read(entry)[group].items():assert sha(Path(n) if group=='external_files_sha256' else ROOT/n)==h,n
    before=Database();data=deepcopy(before.data);props=read(MAPPING/'NEW_PROPERTIES_R1.json');revisions=read(MAPPING/'STATE_REVISIONS_R1.json')
    assert len(props)==len(revisions)==9 and all(p['id'] not in before.properties for p in props)
    changed={}
    for row in revisions:
        a,b=row['before'],row['after'];assert before.states[a['id']]==a and a['id']==b['id']
        assert a['version']=='1.0.0' and b['version']=='1.0.1'
        assert {k:v for k,v in a.items() if k not in ['version','property_ids','source_scope']}=={k:v for k,v in b.items() if k not in ['version','property_ids','source_scope']}
        changed[b['id']]=b
    data['materials']['records']=[changed.get(s['id'],s) for s in data['materials']['records']];data['reference_properties']['records'].extend(props)
    validate_material_catalog(*(data[n] for n in ['materials','reference_properties','sources']));after=Database(data)
    assert after.snapshot==read(MAPPING/'VALIDATION_R1.json')['snapshot']
    assert all(after.properties[k]==v for k,v in before.properties.items()) and all(after.states[k]==v for k,v in before.states.items() if k not in changed)
    assert after.sources==before.sources and after.identities==before.identities and after.grades==before.grades
    assert len(after.states)==len(before.states)
    paths={f'materials_boundaries/data/{n}.json':encoded(data[n]) for n in ['materials','reference_properties','sources']}
    backup=EXT/'baseline-tables';backup.mkdir(parents=True,exist_ok=False);pins={n:sha(ROOT/n) for n in paths}
    for n,h in pins.items():shutil.copyfile(ROOT/n,backup/Path(n).name);assert sha(backup/Path(n).name)==h
    write('APPLICATION_INTENT_R64.json',dict(before_sha256=pins,after_sha256={n:hashlib.sha256(b).hexdigest() for n,b in paths.items()},backup=str(backup),snapshot=after.snapshot,mapping_entry_sha256=sha(entry),only_write=list(paths)))
    try:
        for n,b in paths.items():(ROOT/n).write_bytes(b)
        assert all((ROOT/n).read_bytes()==b for n,b in paths.items())
    except BaseException:
        for n in paths:shutil.copyfile(backup/Path(n).name,ROOT/n)
        raise
    write('APPLICATION_R64.json',dict(status='exact_reviewed_existing_PBS_enthalpy_applied_locally',snapshot=after.snapshot,after_sha256={n:sha(ROOT/n) for n in paths},properties=len(after.properties),states=len(after.states),sources=len(after.sources),new_properties=9,new_contexts=0,revised_context_ids=sorted(changed),old5664properties_unchanged=True,old_state_facts_preserved=True,new_identities=0,new_grades=0,new_sources=0,installation_final_review='pending',pushed=False))
    print(json.dumps(dict(snapshot=after.snapshot,properties=len(after.properties),states=len(after.states))),flush=True)
if __name__=='__main__':main()
