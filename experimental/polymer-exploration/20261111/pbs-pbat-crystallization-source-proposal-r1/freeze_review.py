"""Bind unchanged accepted r46 data,source/phase concept and current descriptive inventory."""
from pathlib import Path
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
ACCEPT=HERE.parent/'local-acceptance-r46'
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()=='5cc2f28c784b3f457bef025d570161fac0e63e49'
    entry=ACCEPT/'REVIEW_FINAL_INPUTS_R46.json';approval=read(ACCEPT/'INDEPENDENT_FINAL_REVIEW_R46.json')
    assert approval['decision']=='approved' and approval['review_inputs_sha256']==sha(entry)
    native=read(entry)['native_files_sha256'];assert all(sha(ROOT/n)==h for n,h in native.items())
    inventory=HERE.parent/'polymer-condition-gaps-current-r2';report=read(inventory/'INVENTORY_R2.json')
    assert report['native_files_sha256']==native and report['summary']['properties']==231 and report['native_data_uncommitted']
    files={p.relative_to(ROOT).as_posix() for folder in (HERE,inventory) for p in folder.iterdir() if p.is_file()}
    files|={p.relative_to(ROOT).as_posix() for p in (entry,ACCEPT/'INDEPENDENT_FINAL_REVIEW_R46.json',ACCEPT/'APPLICATION_R46.json')}
    files|={'materials_boundaries/material_references.py','materials_boundaries/material_presentation.py','schemas/reference_properties.schema.json','experimental/polymer-exploration/20261111/polymer-condition-gaps-current-r1/build_inventory.py'}
    source=HERE.parent/'pbs-pbat-thermal-source-followup-r1/REVIEW_INPUTS_R1.json';external=read(source)['external_files_sha256']
    assert all(sha(Path(n))==h for n,h in external.items())
    obj=dict(schema='PBS-PBAT-crystallization-source-phase-concept-review/1',baseline_commit='5cc2f28c784b3f457bef025d570161fac0e63e49',accepted_native_snapshot=read(ACCEPT/'APPLICATION_R46.json')['snapshot'],repo_files_sha256={n:sha(ROOT/n) for n in sorted(files)},external_files_sha256=external,native_files_sha256=native,scope='Four original Tcc cells,generic phase-qualified crystallization concept with source-label discrepancy retained,and updated231-property descriptive inventory;not implementation,mapping,installation or admission',review_constraints='Read-only ownhash/JSON/schema/sourcevisual and finite self-built conceptual checks;no authorhelpers,testmodules,suites,fullgraph/history,writes/install/push')
    p=HERE/'REVIEW_INPUTS_R1.json'
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps(dict(sha256=sha(p),repo=len(files),external=len(external),native=3)))
if __name__=='__main__':main()
