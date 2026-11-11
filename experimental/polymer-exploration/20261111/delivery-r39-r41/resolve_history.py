"""Resolve immutable milestone bytes;report missing evidence instead of guessing."""
from pathlib import Path
import hashlib,json,re
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
EVIDENCE=ROOT.parent/'open-database-evidence';CACHE={}
def read(p):return json.loads(p.read_bytes())
def sha(p):
    p=p.resolve()
    if p not in CACHE:CACHE[p]=hashlib.sha256(p.read_bytes()).hexdigest()
    return CACHE[p]
def main():
    previous=read(ROOT/'experimental/polymer-exploration/20261104/delivery-r36-r38/HISTORICAL_INPUT_RESOLUTION_R36_R38.json')
    pool={Path(item['resolved_path_hint']) for c in previous['contexts'] for item in c['resolved'].values()}
    work=ROOT/'experimental/polymer-exploration/20261111'
    entries=[]
    for p in sorted(work.rglob('*.json')):
        if p.is_relative_to(HERE):continue
        if p.name.startswith(('REVIEW_','AFFECTED_INPUTS_','PACKAGE_INPUTS_')):entries.append(p)
    entries+=[ROOT/'experimental/polymer-exploration/20261104/nr-work-to-break-source-contract-r1/REVIEW_INPUTS_R1.json',ROOT/'experimental/polymer-exploration/20261104/delivery-r36-r38/REVIEW_CONTENT_INPUTS_R36_R38.json']
    for p in entries:
        obj=read(p)
        for name in obj.get('external_files_sha256',{}):pool.add(Path(name))
    for folder in ('polymer-nr-work-contract-20261111-r1','polymer-nr-thermal-contract-20261111-r1','polymer-nr-conductivity-contract-20261111-r1','polymer-consolidated-delivery-20261111-r39-r41'):
        pool|={p for p in (EVIDENCE/folder).rglob('*') if p.is_file()}
    by_hash={}
    for p in sorted(pool):
        if p.is_file():by_hash.setdefault(sha(p),p)
    contexts=[];missing=[]
    def add(entry,field,pins,expected=None):
        if expected:assert sha(entry)==expected,str(entry)
        resolved={}
        for name,digest in pins.items():
            if digest is None:continue
            assert isinstance(digest,str) and re.fullmatch('[0-9a-f]{64}',digest),(str(entry),name)
            current=Path(name) if Path(name).is_absolute() else ROOT/name
            p=current if current.is_file() and sha(current)==digest else by_hash.get(digest)
            if p is None:
                missing.append(dict(entry=entry.relative_to(ROOT).as_posix(),field=field,name=name,sha256=digest));continue
            assert sha(p)==digest
            by_hash.setdefault(digest,p)
            resolved[name]=dict(sha256=digest,resolved_path_hint=str(p),current=p.resolve()==current.resolve())
        contexts.append(dict(entry=entry.relative_to(ROOT).as_posix(),entry_sha256=sha(entry),field=field,resolved=resolved))
    for c in previous['contexts']:add(ROOT/c['entry'],c['field'],{n:i['sha256'] for n,i in c['resolved'].items()},c['entry_sha256'])
    for p in entries:
        obj=read(p)
        fields=[n for n in ('repo_files_sha256','native_files_sha256','external_files_sha256') if n in obj]
        if fields:
            for field in fields:add(p,field,obj[field])
        elif obj and all(isinstance(v,str) and re.fullmatch('[0-9a-f]{64}',v) for v in obj.values()):add(p,'plain_hash_map',obj)
        else:raise ValueError('Unrecognized frozen entry '+str(p))
    result=dict(schema='r39-r41-historical-input-resolution/1',contexts=contexts,context_count=len(contexts),bindings=sum(len(c['resolved']) for c in contexts),unresolved=len(missing),missing=missing,historical_absence_conditions=previous['historical_absence_conditions'],scope='Resolve frozen bytes only,not rerunning historical tests;missing evidence stays unresolved')
    assert len(result['historical_absence_conditions'])==2
    with (HERE/'HISTORICAL_INPUT_RESOLUTION_R39_R41_R1.json').open('x',encoding='utf-8',newline='\n') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps(dict(contexts=len(contexts),resolved=result['bindings'],unresolved=len(missing),first_missing=missing[:8]),ensure_ascii=False))
if __name__=='__main__':main()
