"""Freeze the exact local r28 acceptance evidence; do not alter historical inputs."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
AREA=ROOT/'experimental/polymer-exploration/20261104'
OUT=Path(__file__).resolve().parent
EXTERNAL=ROOT.parent/'open-database-evidence'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def main():
    files={ROOT/n for n in read(AREA/'phbv39-melting-peaks-native-r1/REVIEW_INPUTS_R1.json')['repo_files_sha256']}
    for folder in ('phbv39-melting-peaks-native-r1','installed-preview-r28','local-acceptance-r28','condition-gaps-native-r28'):
        files|={p for p in (AREA/folder).rglob('*') if p.is_file()}
    install=EXTERNAL/'polymer-installed-preview-20261104-r28'
    external={Path(n) for n in read(AREA/'phbv39-melting-peaks-native-r1/REVIEW_INPUTS_R1.json')['external_files_sha256']}
    external|={install/n for n in read(AREA/'installed-preview-r28/REVIEW_INPUTS_R28.json')['external_evidence_sha256']}
    external|=set((EXTERNAL/'polymer-native-acceptance-20261104-r28/baseline-tables').glob('*.json'))
    value=dict(schema='polymer-melting-peaks-final-local-acceptance/1',repo_files_sha256={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)},external_files_sha256={str(p):sha(p) for p in sorted(external)},snapshot=read(OUT/'APPLICATION_R28.json')['after_snapshot'],native_applied=True,pushed=False,merged_main=False,deployed=False,full_history_regression='not_run',historical_input_resolution='Use exact baseline-contract archives and external pre-application tables; historical manifests unchanged.')
    target=OUT/'REVIEW_INPUTS_R28.json'
    with target.open('x',encoding='utf-8',newline='\n') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps(dict(review_inputs_sha256=sha(target),repo_files=len(files),external_files=len(external))))
if __name__=='__main__':main()
