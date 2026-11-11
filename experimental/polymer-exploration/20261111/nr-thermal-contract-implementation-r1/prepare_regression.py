"""Archive old count assertions and derive the affected regression runner."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
EXT=ROOT.parent/'open-database-evidence/polymer-nr-thermal-contract-20261111-r1/before-count-update'
def main():
    EXT.mkdir(exist_ok=False);pins={}
    for p in (ROOT/'tests').glob('test_*contract.py'):
        text=p.read_text(encoding='utf-8');changed=''.join(line.replace(', 12)',', 14)').replace(',12)',',14)') if 'oneOf' in line else line for line in text.splitlines(keepends=True))
        if text!=changed:
            (EXT/p.name).write_bytes(p.read_bytes());pins[p.relative_to(ROOT).as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest();p.write_text(changed,encoding='utf-8',newline='\n')
    assert len(pins)==8
    with (EXT/'BEFORE_SHA256.json').open('x',encoding='utf-8') as f:json.dump(pins,f,indent=2)
    text=(HERE.parent/'local-acceptance-r39/validate_current.py').read_text(encoding='utf-8')
    text=text.replace("patterns.append('test_volumetric_work_contract.py')", "patterns.extend(['test_volumetric_work_contract.py','test_thermal_capacity_diffusivity_contract.py'])")
    text=text.replace('r.testsRun==222','r.testsRun==228')
    with (HERE/'run_affected_regression.py').open('x',encoding='utf-8',newline='\n') as f:f.write(text)
    print('8count assertions archived/updated;228case runner prepared')
if __name__=='__main__':main()
