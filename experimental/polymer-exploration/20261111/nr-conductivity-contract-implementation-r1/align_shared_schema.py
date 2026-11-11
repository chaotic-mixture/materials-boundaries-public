"""Align the second public schema sharing the expanded derivation definition."""
from pathlib import Path
import hashlib,json,shutil,sys
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
EXT=ROOT.parent/'open-database-evidence/polymer-nr-conductivity-contract-20261111-r1'
def main():
    name='schemas/materials.schema.json';path=ROOT/name;backup=EXT/'baseline'/name
    assert not backup.exists();shutil.copyfile(path,backup)
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    before=json.loads(path.read_bytes());sys.path.insert(0,str(ROOT))
    from materials_boundaries.material_references import _MATERIALS_SCHEMA as current
    original=current['$defs']['derivation']['oneOf'][0]
    assert original==before['$defs']['derivation']
    normalized=json.loads(json.dumps(current));normalized['$defs']['derivation']=original
    assert normalized==before
    path.write_text(json.dumps(current,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    with (HERE/'SHARED_SCHEMA_ALIGNMENT_R2.json').open('x',encoding='utf-8',newline='\n') as f:
        json.dump(dict(file=name,before_sha256=sha(backup),after_sha256=sha(path),only_change='unused common derivation definition extended with same disjoint profile',first_regression=dict(tests=235,failures=1,errors=0,skipped=0,cause='materials public schema also contains common derivation definition;runtime/public mismatch'),native_tables_changed=False),f,indent=2);f.write('\n')
    print('Shared materials schema aligned;all remaining structure exact')
if __name__=='__main__':main()
