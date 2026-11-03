"""Resolve frozen inputs to exact current files or retained historical bytes."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[4]
OUT=Path(__file__).resolve().parent


def main():
    cache={}
    def sha(path):
        path=path.resolve()
        if path not in cache:cache[path]=hashlib.sha256(path.read_bytes()).hexdigest()
        return cache[path]
    external=ROOT.parent/'open-database-evidence'
    backups=list((OUT/'pre-delivery-documents').rglob('*'))
    for stage in ('r12-r2','r13','r14'):
        backups+=list((external/('polymer-native-acceptance-20261103-'+stage)/'baseline-tables').glob('*.json'))
    historical={}
    for f in backups:
        if f.is_file():historical.setdefault(sha(f),f)
    entries=subprocess.check_output(['git','status','--porcelain=v1','-z','--untracked-files=all'],cwd=ROOT).split(b'\0')
    paths=[ROOT/e[3:].decode('utf-8') for e in entries if e]
    contexts={}
    for path in sorted(paths):
        if path.suffix!='.json' or not path.is_relative_to(ROOT/'experimental'):
            continue
        obj=json.loads(path.read_bytes())
        if not isinstance(obj,dict):continue
        bindings=obj.get('repo_files_sha256')
        if path.name.startswith('PACKAGE_INPUTS'):
            bindings=obj
        if bindings is None:continue
        resolved={}
        for name,digest in bindings.items():
            assert isinstance(digest,str) and len(digest)==64,name
            current=(ROOT/name).resolve()
            assert current.is_relative_to(ROOT)
            if current.is_file() and sha(current)==digest:
                target=current
            else:
                assert digest in historical,(str(path),name,digest)
                target=historical[digest]
            assert sha(target)==digest
            resolved[name]={'sha256':digest,'resolved_path_hint':str(target),'current':target==current}
        contexts[path.relative_to(ROOT).as_posix()]={'entry_sha256':sha(path),'resolved':resolved}
    receipt={'schema':'polymer-r12-r14-historical-input-resolution/1','contexts':contexts,
             'resolved_entries':sum(len(v['resolved']) for v in contexts.values()),
             'unresolved_entries':0,'policy':'Frozen entries not rewritten;old README/docs resolve to archived bytes,old native tables to exact recovery copies.'}
    with (OUT/'HISTORICAL_INPUT_RESOLUTION_R12_R14.json').open('x',encoding='utf-8',newline='\n') as f:
        json.dump(receipt,f,ensure_ascii=False,indent=2)
        f.write('\n')
    print(json.dumps({'contexts':len(contexts),'resolved':receipt['resolved_entries'],'unresolved':0}))


if __name__=='__main__':main()
