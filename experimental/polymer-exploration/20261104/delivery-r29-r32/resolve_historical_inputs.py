"""Resolve changed frozen inputs to exact retained bytes, without rewriting them."""
from pathlib import Path
import json,hashlib,subprocess
ROOT=Path(__file__).resolve().parents[4]
OUT=Path(__file__).resolve().parent
AREA=OUT.parent
def read(p):return json.loads(p.read_bytes())
def main():
    cache={}
    def sha(p):
        p=p.resolve()
        if p not in cache:cache[p]=hashlib.sha256(p.read_bytes()).hexdigest()
        return cache[p]
    previous=read(AREA/'local-acceptance-r32/CONTEXT_RESOLUTION_R32.json')
    known=[Path(b['resolved_path']) for c in previous['contexts'] for b in c['bindings'].values()]
    folders=[OUT/'pre-delivery-documents',OUT/'test-input-documents',AREA/'local-acceptance-r32/pre-r32-documents',AREA/'local-acceptance-r31/pre-r31-documents',AREA/'local-acceptance-r30/pre-r30-documents',AREA/'local-acceptance-r29/pre-r29-documents',AREA/'pbs-existing-dma-tg-source-r1/baseline-contract']
    folders += [ROOT.parent/'open-database-evidence'/('polymer-native-acceptance-20261104-'+s)/'baseline-tables' for s in ['r29','r30','r31','r32']]
    known += [p for f in folders for p in f.rglob('*') if p.is_file()]
    archives={sha(p):p for p in known if p.is_file()}
    raw=subprocess.check_output(['git','status','--porcelain=v1','-z','--untracked-files=all'])
    entries=[e for e in raw.split(b'\0') if e];assert not any(e[:2] in [b'R ',b' R',b'C ',b' C'] for e in entries)
    paths=[ROOT/e[3:].decode('utf-8') for e in entries]+[AREA/'delivery-r26-r28/DELIVERY_MANIFEST_R26_R28.json']
    contexts={}
    for c in previous['contexts']:
        contexts[(c['entry'],c['field'])]=(ROOT/c['entry'],c['field'],{n:b['sha256'] for n,b in c['bindings'].items()})
    for p in sorted(set(paths)):
        if p.suffix!='.json' or not p.is_relative_to(ROOT/'experimental'):continue
        d=read(p)
        if not isinstance(d,dict):continue
        for field in ['repo_files_sha256','native_files_sha256','input_sha256_before_and_after']:
            if field in d:contexts[(str(p),field)]=(p,field,d[field])
        if p.name.startswith('PACKAGE_INPUTS'):contexts[(str(p),'root_mapping')]=(p,'root_mapping',d)
        if p.name=='DELIVERY_MANIFEST_R26_R28.json':contexts[(str(p),'files')]=(p,'files',{n:v['sha256'] for n,v in d['files'].items()})
    result=[]
    for entry,field,pins in contexts.values():
        resolved={}
        for name,h in pins.items():
            current=(ROOT/name).resolve();assert current.is_relative_to(ROOT)
            p=current if current.is_file() and sha(current)==h else archives[h];assert sha(p)==h
            resolved[name]={'sha256':h,'resolved_path_hint':str(p),'current':p==current}
        result.append({'entry':entry.relative_to(ROOT).as_posix(),'entry_sha256':sha(entry),'field':field,'resolved':resolved})
    value={'schema':'r29-r32-consolidated-historical-resolution/1','contexts':result,'resolved_entries':sum(len(c['resolved']) for c in result),'unresolved_entries':0,'policy':'Exact archives/recovery copies;no rewrite or historical test replay'}
    with (OUT/'HISTORICAL_INPUT_RESOLUTION_R29_R32.json').open('x',encoding='utf-8',newline='\n') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps({'contexts':len(result),'resolved':value['resolved_entries'],'unresolved':0}))
if __name__=='__main__':main()
