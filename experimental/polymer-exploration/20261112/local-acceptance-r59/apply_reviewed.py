"""Apply only independently approved PUR preparation-provenance revisions."""
from pathlib import Path
from copy import deepcopy
import hashlib,json,shutil,subprocess,sys
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
MAPPING=HERE.parent/'pur-preparation-background-revisions-r1'
EXT=ROOT.parent/'open-database-evidence/polymer-native-acceptance-20261112-r59'
sys.path.insert(0,str(ROOT))
from materials_boundaries.database import Database
from materials_boundaries.material_references import validate_material_catalog
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def encoded(v):return (json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
def write(p,v):
    with p.open('xb') as f:f.write(encoded(v))
def main():
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()=='3880c8ad4c83d8a3c4decf71e130e021b91a8c0d'
    assert subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()=='experimental/open-database'
    entry=MAPPING/'REVIEW_INPUTS_R1.json';review=read(MAPPING/'INDEPENDENT_MAPPING_REVIEW_R1.json')
    assert sha(entry)=='765e54f545987780337e51d035adbc32ad91269d6e97c88b33809ec5452f16a6'
    assert review['decision']=='approved' and review['review_inputs_sha256']==sha(entry)
    for group in ['repo_files_sha256','native_files_sha256','external_files_sha256']:
        for n,h in read(entry)[group].items():assert sha(Path(n) if group=='external_files_sha256' else ROOT/n)==h,n
    before=Database();data=deepcopy(before.data);pairs=read(MAPPING/'PROPERTY_REVISIONS_R1.json');assert len(pairs)==36
    replacements={}
    for pair in pairs:
        old,new=pair['before'],pair['after'];key=old['id'];assert before.properties[key]==old and key==new['id']
        assert old['version']=='1.0.0' and new['version']=='1.0.1' and key not in replacements
        a,b=deepcopy(old),deepcopy(new)
        assert a['conditions']['conditioning']==b['conditions']['conditioning'] and a['sample_count']==b['sample_count']
        b['version']=a['version'];extra=b['conditions']['additional_conditions'].pop()
        assert extra['name']=='optimized_foam_cure_background' and extra['fact']['status']=='reported'
        b['source_document']=a['source_document'];b['verification']['source_inspection_scope']=a['verification']['source_inspection_scope']
        assert a==b
        replacements[key]=new
    data['reference_properties']['records']=[replacements.get(p['id'],p) for p in data['reference_properties']['records']]
    validate_material_catalog(*(data[n] for n in ['materials','reference_properties','sources']));after=Database(data)
    assert after.snapshot==read(MAPPING/'VALIDATION_R1.json')['snapshot']
    assert after.data['materials']==before.data['materials'] and after.data['sources']==before.data['sources']
    assert all(after.properties[k]==p for k,p in before.properties.items() if k not in replacements)
    name='materials_boundaries/data/reference_properties.json';backup=EXT/'baseline-tables/reference_properties.json';backup.parent.mkdir(parents=True,exist_ok=False);shutil.copyfile(ROOT/name,backup)
    content=encoded(data['reference_properties']);before_hash=sha(backup)
    write(HERE/'APPLICATION_INTENT_R59.json',dict(only_write=name,before_sha256=before_hash,after_sha256=hashlib.sha256(content).hexdigest(),backup=str(backup),mapping_entry_sha256=sha(entry)))
    try:
        (ROOT/name).write_bytes(content);assert (ROOT/name).read_bytes()==content
    except BaseException:
        shutil.copyfile(backup,ROOT/name);raise
    pins={f'materials_boundaries/data/{n}.json':sha(ROOT/f'materials_boundaries/data/{n}.json') for n in ['materials','reference_properties','sources']}
    write(HERE/'APPLICATION_R59.json',dict(status='reviewed_preparation_background_revisions_applied_locally',snapshot=after.snapshot,after_sha256=pins,properties=5640,states=5373,sources=134,revised_properties=36,new_properties=0,new_states=0,new_identities=0,materials_sources_unchanged=True,unmodified_properties=5604,unknown_conditioning_unchanged=True,all_sample_counts_unchanged=True,installation_final_review='pending',pushed=False))
    print(json.dumps(dict(snapshot=after.snapshot,revised_properties=36,properties=5640,states=5373)))
if __name__=='__main__':main()
