"""Reuse exact fresh236-test evidence and execute current database CLI gates."""
from pathlib import Path
import hashlib,json,os,subprocess,sys
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
EXT=ROOT.parent/'open-database-evidence/polymer-consolidated-delivery-20261111-r39-r41'
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    stage=HERE.parent/'local-acceptance-r41';tests=read(stage/'AFFECTED_RESULTS_R1.json');pins=read(stage/'AFFECTED_INPUTS_R1.json')
    assert tests['tests']==236 and tests['successful'] and tests['inputs_unchanged']
    assert tests['failures']==tests['errors']==tests['skipped']==0
    assert all(sha(ROOT/n)==h for n,h in pins.items())
    out=EXT/'daily-scope-r2';out.mkdir(exist_ok=False);export=out/'database-example'
    commands=[['check','--scientific-contracts'],['export','--query','C11000','--quantity','mass_density','--output',str(export)],['verify','--snapshot',str(export)]]
    results=[];env=os.environ.copy();env.update(PYTHONUTF8='1',PYTHONDONTWRITEBYTECODE='1')
    for i,args in enumerate(commands):
        cmd=[sys.executable,'-X','utf8','-B','-m','materials_boundaries.database',*args]
        result=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True)
        (out/f'command-{i+1}.log').write_bytes(result.stdout+result.stderr)
        result.check_returncode();results.append(dict(command=cmd,exit_code=result.returncode,result=json.loads(result.stdout)))
    manifest=read(export/'manifest.json')
    assert manifest['database_snapshot']==read(HERE/'APPLICATION_R39_R41.json')['snapshot']
    baseline=ROOT.parent/'open-database-evidence/polymer-consolidated-delivery-20261104-r36-r38/daily-scope-r2/database-example/records.jsonl'
    assert sha(baseline)=='fdaf1b08f47a2b8b68e107acbd21109372f5dfcf4389c5faa6c1a0aaa3f2fc2f'
    old=json.loads(baseline.read_text('utf-8'));current=json.loads((export/'records.jsonl').read_text('utf-8'))
    assert {k:v for k,v in old.items() if k!='database_snapshot'}=={k:v for k,v in current.items() if k!='database_snapshot'}
    assert current['database_snapshot']==manifest['database_snapshot']
    assert sha(export/'records.jsonl')==manifest['files']['records.jsonl']
    assert all(sha(ROOT/n)==h for n,h in pins.items())
    payload=dict(scope='Exact r41 fresh236 checks reused without rerunning;current three CLI gates actually executed',scoped_tests=tests,scoped_input_entry_sha256=sha(stage/'AFFECTED_INPUTS_R1.json'),scoped_inputs_still_exact=True,daily19_subset_not_additional=True,commands=results,C11000_join_content_unchanged_excluding_database_snapshot=True,C11000_current_records_sha256=sha(export/'records.jsonl'),full_history='not_run',HTTP='not_run',remote_CI='not_run_for_uncommitted_content')
    with (HERE/'DATABASE_CI_LOCAL_EQUIVALENT_R39_R41.json').open('x',encoding='utf-8',newline='\n') as f:json.dump(payload,f,ensure_ascii=False,indent=2);f.write('\n')
    print('236-test inputs exact;current scientific check/export/verify passed;C11000 content unchanged except snapshot binding')
if __name__=='__main__':main()
