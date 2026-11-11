"""Check the unchanged current native graph once under the new contract,without historical replay."""
from pathlib import Path
import hashlib,json,os,subprocess,sys
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
EXT=ROOT.parent/'open-database-evidence/polymer-dtg-unknown-ordinal-implementation-20261111-r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    source=HERE.parent/'pbs-pbat-thermal-source-followup-r1/REVIEW_INPUTS_R1.json';pins=json.loads(source.read_bytes())['native_files_sha256']
    assert all(sha(ROOT/n)==h for n,h in pins.items())
    log=EXT/'current-graph-r1.log';assert not log.exists()
    env=os.environ.copy();env.update(PYTHONUTF8='1',PYTHONDONTWRITEBYTECODE='1')
    command=[sys.executable,'-X','utf8','-B','-m','materials_boundaries.database','check','--scientific-contracts']
    result=subprocess.run(command,cwd=ROOT,env=env,capture_output=True);log.write_bytes(result.stdout+result.stderr);result.check_returncode()
    graph=json.loads(result.stdout);assert graph['snapshot']=='921239866811e038708751232e0b1f97242fd80d72a9b726503d830c01f0e8c7' and graph['properties']==5486
    assert all(sha(ROOT/n)==h for n,h in pins.items())
    v=dict(scope='Current unchanged native graph once under updated code;not historical tests,new source mapping or admission',command=command,exit_code=result.returncode,result=graph,native_files_sha256=pins,native_unchanged=True,log_path=str(log),log_sha256=sha(log))
    with (HERE/'NATIVE_COMPATIBILITY_R1.json').open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
    print('Unchanged5486-property graph passed once;native hashes stable;no mapping/admission')
if __name__=='__main__':main()
