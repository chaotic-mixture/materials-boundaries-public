"""Compare current native bytes and complete source exports to final installation."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT))
from materials_boundaries.database import Database,read_snapshot
OUT=Path(__file__).resolve().parent
EXTERNAL=ROOT.parent/'open-database-evidence/polymer-accepted-install-20261103-r15-r18'
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    db=Database();receipt=read(EXTERNAL/'INSTALLED_VALIDATION_R15_R18.json');inputs=read(EXTERNAL/'BUILD_INPUTS_R15_R18.json')['staged_inputs']
    assert db.snapshot==receipt['installed']['snapshot']
    site=EXTERNAL/'venv/Lib/site-packages';payload={n:h for n,h in inputs.items() if n.startswith('materials_boundaries/')}
    checked={}
    for n,h in payload.items():
        assert sha(site/n)==h,n
        if n=='materials_boundaries/_version.py':
            assert '__version__ = "0.35.0"' in (ROOT/n).read_text(encoding='utf-8');continue
        assert sha(ROOT/n)==h,n;checked[n]=h
    for n in db.data:assert read(site/'materials_boundaries/data'/(n+'.json'))==db.data[n]
    assert len(db.properties)==5298
    exports={}
    for sid in receipt['installed']['source_counts']:
        manifest,rows=read_snapshot(EXTERNAL/('installed-export-'+sid));assert rows=={r['property']['id']:r for r in db.records(source=sid)};exports[sid]=len(rows)
    assert sum(exports.values())==99
    result={'status':'native_equal_final_current_document_install','snapshot':db.snapshot,'installed_payload_files_verified':len(payload),'native_payload_files_equal_install':len(checked),'only_payload_difference':'isolated version file; native remains0.35.0','all_5298_properties_and_three_tables_equal':True,'installed_exports_equal_native':exports,'README_metadata_scope':'Current README included,independently checked by wheel review','wheel_sha256':receipt['wheel_sha256'],'full_history_regression':'not_run','pushed':False,'merged_main':False,'deployed':False}
    with (OUT/'NATIVE_INSTALLED_EQUIVALENCE_R15_R18.json').open('x',encoding='utf-8',newline='\n') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
    (OUT/'INSTALLED_VALIDATION_R15_R18.json').write_bytes((EXTERNAL/'INSTALLED_VALIDATION_R15_R18.json').read_bytes())
    print(json.dumps({'native_payload_matches':len(checked),'properties':5298,'full_joined_exports':sum(exports.values())}))
if __name__=='__main__':main()
