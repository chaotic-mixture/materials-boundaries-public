"""Archive affected tests and update only total branch count11to12."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[4]
EXT=ROOT.parent/'open-database-evidence/polymer-nr-work-contract-20261111-r1/before-count-update'
def main():
    EXT.mkdir(exist_ok=False);changes={}
    for p in (ROOT/'tests').glob('test_*contract.py'):
        text=p.read_text(encoding='utf-8');lines=text.splitlines(keepends=True)
        changed=[line.replace(', 11)',', 12)').replace(',11)',',12)') if 'oneOf' in line else line for line in lines]
        result=''.join(changed)
        if result!=text:
            (EXT/p.name).write_bytes(p.read_bytes());changes[p.relative_to(ROOT).as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
            p.write_text(result,encoding='utf-8',newline='\n')
    assert len(changes)==8
    with (EXT/'BEFORE_SHA256.json').open('x',encoding='utf-8') as f:json.dump(changes,f,indent=2)
    print('8old test files archived;only totalbranch11to12 changed')
if __name__=='__main__':main()
