"""Freeze exact pending experimental content and complete package recipe."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
OUT=Path(__file__).resolve().parent
BASE='4d4f8fa84451ab0481ec6c2cfbe3495209dad4b8'


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def write(p,v):
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')


def main():
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip()==BASE
    assert subprocess.check_output(['git','branch','--show-current'],cwd=ROOT).decode().strip()=='experimental/open-database'
    assert not subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT)
    accepted=ROOT/'experimental/polymer-exploration/20261104/local-acceptance-r28'
    review=read(accepted/'INDEPENDENT_ACCEPTANCE_REVIEW_R28.json');assert review['decision']=='clear' and review['review_inputs_sha256']==sha(accepted/'REVIEW_INPUTS_R28.json')
    allowed=set(read(accepted/'REVIEW_INPUTS_R28.json')['repo_files_sha256'])|{(accepted/n).relative_to(ROOT).as_posix() for n in ('REVIEW_INPUTS_R28.json','INDEPENDENT_ACCEPTANCE_REVIEW_R28.json')}
    allowed|={'README.md','HANDOFF.md','docs/DATABASE_COVERAGE.zh.md','docs/MATERIAL_SOURCE_CONDITIONS.zh.md','docs/OPEN_DATABASE_ROADMAP.zh.md'}
    tests=read(OUT/'SCOPED_TESTS_R26_R28.json');assert tests['successful'] and tests['tests_run']==180 and not any(tests[n] for n in ('failures','errors','skipped'))
    assert tests['inputs_unchanged_during_run']==113 and read(OUT/'HISTORICAL_INPUT_RESOLUTION_R26_R28.json')['unresolved_entries']==0
    recipe={n:sha(ROOT/n) for n in read(ROOT/'experimental/polymer-exploration/20261104/delivery-r23-r25/PACKAGE_INPUTS_R23_R25.json')}
    assert len(recipe)==69 and sum(n.startswith('materials_boundaries/') for n in recipe)==65
    write(OUT/'PACKAGE_INPUTS_R26_R28.json',recipe)
    snapshot=read(OUT/'NATIVE_DELTA_R26_R28.json')['current_snapshot']
    write(OUT/'PACKAGE_GUARD_R26_R28.json',dict(repo_files_sha256=recipe,
        external_preview_directory_hint=str(ROOT/'materials_boundaries/data'),
        external_preview_files_sha256={n+'.json':sha(ROOT/'materials_boundaries/data'/(n+'.json')) for n in ('materials','reference_properties','sources')},combined_snapshot=snapshot))
    raw=subprocess.check_output(['git','status','--porcelain=v1','-z','--untracked-files=all'],cwd=ROOT)
    entries=[e for e in raw.split(b'\0') if e];assert not any(e[:2] in (b'R ',b' R',b'C ',b' C') for e in entries)
    paths=[e[3:].decode('utf-8').replace('\\','/') for e in entries]
    prefix=OUT.relative_to(ROOT).as_posix()+'/'
    assert len(paths)==len(set(paths))
    for n in paths:
        p=(ROOT/n).resolve();assert p.is_relative_to(ROOT) and p.is_file() and (n in allowed or n.startswith(prefix)),n
        assert p.stat().st_size<100*1024*1024 and p.suffix.lower() not in {'.pdf','.xml','.png','.html','.xlsx','.whl','.zip'}
    write(OUT/'REVIEW_INPUTS_R26_R28.json',dict(schema='polymer-r26-r28-consolidated-content-review/1',baseline_commit=BASE,branch='experimental/open-database',native_snapshot=snapshot,
        repo_files_sha256={n:sha(ROOT/n) for n in sorted(paths)},fresh_tests=tests,
        scope='Three-round Git delta/contracts/schema/locales/tests/main docs/exact history/external bindings/prospective final package-consumer helpers;not finalinstall/manifest/Git approval.',
        final_install='not_run_pending_content_approval',full_history_regression='not_run',HTTP='not_run',remote_CI='pending_exact_commit',pushed=False,merged_main=False,stable_release=False,deployed=False))
    print(json.dumps(dict(input_sha256=sha(OUT/'REVIEW_INPUTS_R26_R28.json'),content_files=len(paths))))


if __name__=='__main__':main()
