"""Freeze source facts,explicit-unknown proposal and original acquisition evidence for read-only review."""
from pathlib import Path
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
EVIDENCE=ROOT.parent/'open-database-evidence'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def main():
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()=='5cc2f28c784b3f457bef025d570161fac0e63e49'
    assert subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()=='experimental/open-database'
    assert not subprocess.check_output(['git','diff','--name-only'],cwd=ROOT).strip()
    files={p.relative_to(ROOT).as_posix() for p in HERE.iterdir() if p.is_file()}
    files|={'materials_boundaries/material_references.py','materials_boundaries/material_presentation.py','schemas/reference_properties.schema.json','tests/test_tga_endpoint_contract.py'}
    external={}
    for label in ('polymer-pbs-pbat-thermal-20261111-r1','polymer-pbs-pbat-thermal-20261111-r2'):
        for p in (EVIDENCE/label).rglob('*'):
            if p.is_file():external[str(p)]=sha(p)
    retained=EVIDENCE/'polymer-property-source-rechecks-20261103/pbs-pbat/article-r1.xml';external[str(retained)]=sha(retained)
    native=read(HERE/'VALIDATION_R1.json')['native_files_sha256'];assert all(sha(ROOT/n)==h for n,h in native.items())
    obj=dict(schema='pbs-pbat-thermal-source-concept-review/1',baseline_commit='5cc2f28c784b3f457bef025d570161fac0e63e49',baseline_snapshot='921239866811e038708751232e0b1f97242fd80d72a9b726503d830c01f0e8c7',repo_files_sha256={n:sha(ROOT/n) for n in sorted(files)},external_files_sha256=external,native_files_sha256=native,scope='Eight source thermal facts,identity/unit/method/rights/unknown boundaries,existing ordinal limitation and concept proposal only;no implementation,native mapping,installation or admission',review_constraints='Read-only ownhash/JSON/schema/source-page visual and limited own fictional descriptor probes;no authorhelpers,testmodules,suites,fullgraph/history,writes/install/push')
    p=HERE/'REVIEW_INPUTS_R1.json'
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps(dict(sha256=sha(p),repo=len(files),external=len(external),native=len(native))))
if __name__=='__main__':main()
