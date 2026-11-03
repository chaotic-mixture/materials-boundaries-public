"""Resolve changed packet input hashes to exact retained historical bytes."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
OUT=Path(__file__).resolve().parent


def main():
    cache={}
    def sha(p):
        p=p.resolve()
        if p not in cache:cache[p]=hashlib.sha256(p.read_bytes()).hexdigest()
        return cache[p]
    folders=[OUT/'pre-delivery-documents']
    old=ROOT/'experimental/polymer-exploration/20261103';area=OUT.parent
    folders += [old/n for n in ('nbr-tear-source-contract-r1/baseline-contract','nbr-tear-native-r1/mapping-r1-context','local-acceptance-r23/pre-r23-documents')]
    folders += [area/n for n in ('epoxy-flexural-elongation-source-r1/baseline-contract','local-acceptance-r24/pre-r24-documents',
        'epoxy-izod-source-contract-r1/baseline-contract','epoxy-izod-native-r1/test-development-r1','local-acceptance-r25/pre-r25-documents')]
    folders += [ROOT.parent/'open-database-evidence'/('polymer-native-acceptance-20261104-'+s)/'baseline-tables' for s in ('r23','r24','r25')]
    archives={sha(p):p for f in folders for p in f.rglob('*') if p.is_file()}
    entries=[e for e in subprocess.check_output(['git','status','--porcelain=v1','-z','--untracked-files=all'],cwd=ROOT).split(b'\0') if e]
    assert not any(e[:2] in (b'R ',b' R',b'C ',b' C') for e in entries)
    paths=[ROOT/e[3:].decode('utf-8') for e in entries]
    paths.append(old/'delivery-r19-r22/DELIVERY_MANIFEST_R19_R22.json')
    contexts={}
    for p in sorted(set(paths)):
        if p.suffix!='.json' or not p.is_relative_to(ROOT/'experimental'):continue
        v=json.loads(p.read_bytes())
        if not isinstance(v,dict):continue
        pins=v.get('repo_files_sha256');kind='repository inputs'
        if p.name.startswith('PACKAGE_INPUTS'):pins=v;kind='package recipe'
        elif 'input_sha256_before_and_after' in v:pins=v['input_sha256_before_and_after'];kind='test pre/post inputs'
        elif p.name=='DELIVERY_MANIFEST_R19_R22.json':pins={n:d['sha256'] for n,d in v['files'].items()};kind='preceding delivery'
        if pins is None:continue
        resolved={}
        for name,digest in pins.items():
            assert isinstance(digest,str) and len(digest)==64
            current=(ROOT/name).resolve();assert current.is_relative_to(ROOT)
            target=current if current.is_file() and sha(current)==digest else archives[digest]
            assert sha(target)==digest
            resolved[name]=dict(sha256=digest,resolved_path_hint=str(target),current=(target==current))
        contexts[p.relative_to(ROOT).as_posix()]=dict(entry_sha256=sha(p),binding_kind=kind,resolved=resolved)
    result=dict(schema='polymer-r23-r25-historical-input-resolution/1',contexts=contexts,
        resolved_entries=sum(len(c['resolved']) for c in contexts.values()),unresolved_entries=0,
        policy='Exact archives/recovery copies preserve old bindings;old manifests not rewritten;no historical test replay.')
    with (OUT/'HISTORICAL_INPUT_RESOLUTION_R23_R25.json').open('x',encoding='utf-8',newline='\n') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps(dict(contexts=len(contexts),resolved=result['resolved_entries'],unresolved=0)))


if __name__=='__main__':main()
