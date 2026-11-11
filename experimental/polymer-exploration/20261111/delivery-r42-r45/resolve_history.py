"""Resolve frozen historical bytes to exact current or archived files;never replay historical tests."""
from pathlib import Path
import hashlib,json,re
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
CACHE={}
def read(p):return json.loads(p.read_bytes())
def sha(p):
    p=p.resolve()
    if p not in CACHE:CACHE[p]=hashlib.sha256(p.read_bytes()).hexdigest()
    return CACHE[p]
def main():
    prior=ROOT/'experimental/polymer-exploration/20261111/delivery-r39-r41/HISTORICAL_INPUT_RESOLUTION_R39_R41_R3.json';previous=read(prior)
    pool={Path(v['resolved_path_hint']) for c in previous['contexts'] for v in c['resolved'].values()}
    work=HERE.parent;entries=[p for p in sorted(work.rglob('*.json')) if not p.is_relative_to(HERE) and p.name.startswith(('REVIEW_','AFFECTED_INPUTS_','PACKAGE_INPUTS_'))]
    entries+=sorted(HERE.glob('PACKAGE_INPUTS_*.json'))
    for p in entries:
        for n in read(p).get('external_files_sha256',{}):pool.add(Path(n))
    archive=ROOT.parent/'open-database-evidence/polymer-consolidated-delivery-20261111-r42-r45/before-neutral-navigation'
    pool|={p for p in archive.rglob('*') if p.is_file()}
    by_hash={}
    for p in sorted(pool):
        if p.is_file():by_hash.setdefault(sha(p),p)
    contexts=[];missing=[];seen={}
    def add(entry,field,pins,expected=None):
        if expected:assert sha(entry)==expected,str(entry)
        key=(entry.relative_to(ROOT).as_posix(),field)
        normalized={n:h for n,h in pins.items() if h is not None}
        if key in seen:
            assert seen[key]==normalized,key
            return
        seen[key]=normalized;resolved={}
        for name,digest in normalized.items():
            assert isinstance(digest,str) and re.fullmatch('[0-9a-f]{64}',digest),(key,name)
            current=Path(name) if Path(name).is_absolute() else ROOT/name
            p=current if current.is_file() and sha(current)==digest else by_hash.get(digest)
            if p is None:
                missing.append(dict(entry=key[0],field=field,name=name,sha256=digest));continue
            assert sha(p)==digest;by_hash.setdefault(digest,p)
            resolved[name]=dict(sha256=digest,resolved_path_hint=str(p),current=p.resolve()==current.resolve())
        contexts.append(dict(entry=key[0],entry_sha256=sha(entry),field=field,resolved=resolved))
    for c in previous['contexts']:add(ROOT/c['entry'],c['field'],{n:i['sha256'] for n,i in c['resolved'].items()},c['entry_sha256'])
    for p in entries:
        obj=read(p);fields=[f for f in ('repo_files_sha256','native_files_sha256','external_files_sha256') if f in obj]
        if fields:
            for field in fields:add(p,field,obj[field])
        elif obj and all(isinstance(v,str) and re.fullmatch('[0-9a-f]{64}',v) for v in obj.values()):add(p,'plain_hash_map',obj)
        else:raise ValueError('Unrecognized frozen entry '+str(p))
    manifest=HERE.parent/'delivery-r39-r41/DELIVERY_MANIFEST_R39_R41.json'
    add(manifest,'files.sha256',{n:v['sha256'] for n,v in read(manifest)['files'].items()})
    result=dict(schema='r42-r45-historical-input-resolution/1',contexts=contexts,context_count=len(contexts),bindings=sum(len(c['resolved']) for c in contexts),unresolved=len(missing),missing=missing,historical_absence_conditions=previous['historical_absence_conditions'],duplicate_contexts_deduplicated=True,scope='Exact immutable byte resolution only;not historical test replay or current approval')
    assert len(result['historical_absence_conditions'])==2
    with (HERE/'HISTORICAL_INPUT_RESOLUTION_R42_R45_R1.json').open('x',encoding='utf-8',newline='\n') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps(dict(contexts=len(contexts),bindings=result['bindings'],unresolved=len(missing),first_missing=missing[:8]),ensure_ascii=False))
    assert not missing
if __name__=='__main__':main()
