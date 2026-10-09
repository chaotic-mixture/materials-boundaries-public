"""Bounded read-only NOMAD retrieval and fail-closed candidate normalization.

No geometry, admission, baseline edits, or global material-count claims.
Python 3.11+ standard library only. See README.md for scientific limits.
"""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import time
import urllib.request

API = 'https://nomad-lab.eu/prod/v1/api/v1/'
BASELINE = '6a7bb7c84fa030d7f1527bd18e8e124bee743960'
MAX_REQUESTS, MAX_BYTES, MAX_RESPONSE = 32, 30_000_000, 3_000_000
MAX_PAGES, PAGE_SIZE = 10, 100
METALS = set('Li Be Na Mg Al K Ca Sc Ti V Cr Mn Fe Co Ni Cu Zn Ga Rb Sr Y Zr Nb Mo Tc Ru Rh Pd Ag Cd In Sn Cs Ba La Ce Pr Nd Pm Sm Eu Gd Tb Dy Ho Er Tm Yb Lu Hf Ta W Re Os Ir Pt Au Hg Tl Pb Bi Po Fr Ra Ac Th Pa U Np Pu Am Cm Bk Cf Es Fm Md No Lr'.split())
ELEMENTS = METALS | set('H He B C N O F Ne Si P S Cl Ar Ge As Se Br Kr Sb Te I Xe At Rn Rf Db Sg Bh Hs Mt Ds Rg Cn Nh Fl Mc Lv Ts Og'.split())
ID = re.compile(r'[A-Za-z0-9_-]{1,128}\Z')
FORBIDDEN = {'lattice_vectors', 'cartesian_site_positions', 'positions', 'species_at_sites', 'optimade', 'run', 'raw_files'}
PROJECTION = {'metadata': {k:'*' for k in ('upload_id','mainfile','external_db','license','references','nomad_version','nomad_commit','last_processing_time')}, 'results': {'material': {k:'*' for k in ('material_id','elements','chemical_formula_hill','structural_type','symmetry')}, 'method': '*', 'properties': {'structures': {'structure_original': {'mass_density':'*','dimension_types':'*'}}}}}

def canonical(x):
    return json.dumps(x, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()

def digest(x):
    return hashlib.sha256(canonical(x)).hexdigest()

def write(path, value):
    path.write_bytes(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False).encode()+b'\n')

def assert_no_geometry(value):
    if isinstance(value, dict):
        if FORBIDDEN & value.keys():
            raise ValueError('Geometry or raw simulation section outside allowed scope')
        for v in value.values():
            assert_no_geometry(v)
    elif isinstance(value, list):
        for v in value: assert_no_geometry(v)

def composition(formula):
    if not isinstance(formula, str) or len(formula)>200: raise ValueError('formula')
    parts=re.findall(r'([A-Z][a-z]?)([0-9]*)', formula)
    if ''.join(e+n for e,n in parts)!=formula or not parts: raise ValueError('formula')
    counts={}
    for e,n in parts:
        if e not in ELEMENTS or e in counts or (n and (n.startswith('0') or int(n)>10000)): raise ValueError('formula')
        counts[e]=int(n or 1)
    g=math.gcd(*counts.values())
    return ''.join(e+(str(n//g) if n//g!=1 else '') for e,n in sorted(counts.items())), set(counts)

class Collector:
    def __init__(self, root):
        self.root=Path(root); self.root.mkdir(parents=True,exist_ok=True)
        (self.root/'raw').mkdir(exist_ok=True)
        self.log_path=self.root/'acquisition.json'
        self.log=json.loads(self.log_path.read_text()) if self.log_path.exists() else []
    def fetch(self, path, body):
        if path not in ('entries/archive/query','entries/query'): raise ValueError('Unsupported endpoint')
        used=sum(r.get('bytes',0) for r in self.log)
        if len(self.log)>=MAX_REQUESTS or used>=MAX_BYTES: raise ValueError('Acquisition budget exhausted')
        rec={'url':API+path,'method':'POST','request':body,'retrieved_utc':datetime.now(timezone.utc).isoformat()}
        try:
            req=urllib.request.Request(API+path,data=canonical(body),headers={'Content-Type':'application/json','User-Agent':'MaterialsBoundaries-candidate-batch/1.0'})
            with urllib.request.urlopen(req,timeout=90) as response:
                data=response.read(min(MAX_RESPONSE,MAX_BYTES-used)+1)
                rec['http_status']=response.status
            rec['bytes']=len(data)
            if len(data)>min(MAX_RESPONSE,MAX_BYTES-used): raise ValueError('Response budget exceeded')
            value=json.loads(data); assert_no_geometry(value)
            rec['sha256']=hashlib.sha256(data).hexdigest()
            rec['file']=f'raw/{len(self.log)+1:03d}.json'
            (self.root/rec['file']).write_bytes(data)
        except Exception as exc:
            rec['error']=type(exc).__name__+': '+str(exc)
            raise
        finally:
            self.log.append(rec);write(self.log_path,self.log)
        time.sleep(1)
        return value

def collect(root, pages, after=None):
    if type(pages)!=int or not 1<=pages<=MAX_PAGES: raise ValueError('pages must be 1..10')
    if after is not None and (not isinstance(after,str) or not ID.fullmatch(after)): raise ValueError('Invalid continuation entry ID')
    c=Collector(root)
    if c.log: raise ValueError('Use a fresh evidence directory; never overwrite an acquisition')
    cursor=after
    for page in range(pages):
        pagination={'page_size':PAGE_SIZE,'order_by':'entry_id','order':'asc'}
        if cursor: pagination['page_after_value']=cursor
        body={'owner':'public','query':{'external_db':'OQMD','results.material.structural_type':'bulk'},'pagination':pagination,'required':PROJECTION}
        value=c.fetch('entries/archive/query',body)
        ids=[r['entry_id'] for r in value['data']]
        if ids:
            c.fetch('entries/query',{'owner':'public','query':{'entry_id':{'any':ids}},'pagination':{'page_size':PAGE_SIZE,'order_by':'entry_id','order':'asc'},'required':{'include':['entry_id','authors.*','references','datasets.*']}})
        new_cursor=value['pagination'].get('next_page_after_value')
        print(f'page {page+1}: {len(ids)} entries',flush=True)
        if not new_cursor: break
        if new_cursor==cursor: raise ValueError('Nonadvancing cursor')
        cursor=new_cursor

def repair_attribution(root):
    """Bounded recovery for an earlier overly narrow authors projection."""
    rows,authors,_=load_evidence(root)
    ids=sorted({r['entry_id'] for r in rows if not any(a.get('name') for a in authors.get(r['entry_id'],{}).get('authors',[]))})
    c=Collector(root)
    for start in range(0,len(ids),PAGE_SIZE):
        c.fetch('entries/query',{'owner':'public','query':{'entry_id':{'any':ids[start:start+PAGE_SIZE]}},'pagination':{'page_size':PAGE_SIZE,'order_by':'entry_id','order':'asc'},'required':{'include':['entry_id','authors.*','references','datasets.*']}})
        print(f'recovered attribution {start+len(ids[start:start+PAGE_SIZE])}/{len(ids)}',flush=True)

def load_evidence(root):
    root=Path(root); log=json.loads((root/'acquisition.json').read_text());rows=[]; authors={}; bindings={}
    if len(log)>MAX_REQUESTS or sum(x.get('bytes',0) for x in log)>MAX_BYTES: raise ValueError('Budget violation')
    for rec in log:
        if 'error' in rec: continue
        rel=rec['file']
        if not re.fullmatch(r'raw/[0-9]{3}\.json',rel): raise ValueError('Unsafe evidence path')
        raw=(root/rel).read_bytes()
        if len(raw)!=rec['bytes'] or hashlib.sha256(raw).hexdigest()!=rec['sha256']: raise ValueError('Evidence hash mismatch')
        value=json.loads(raw); assert_no_geometry(value)
        if rec['url']==API+'entries/archive/query':
            if rec['request']['required']!=PROJECTION: raise ValueError('Projection changed')
            for row in value['data']:
                rows.append(row);bindings[row['entry_id']]={'file':rel,'sha256':rec['sha256'],'retrieved_utc':rec['retrieved_utc'],'request_sha256':digest(rec['request'])}
        elif rec['url']==API+'entries/query':
            for row in value['data']:
                authors[row['entry_id']]={'authors':row.get('authors',[]),'datasets':row.get('datasets',[]),'file':rel,'sha256':rec['sha256']}
        else: raise ValueError('Unknown source endpoint')
    return rows,authors,bindings

def normalize(rows, authors, bindings, existing_ids=()):
    exclusions=[]; eligible=[]
    entry_counts=Counter(r.get('entry_id','') for r in rows)
    for row in sorted(rows,key=lambda r:r.get('entry_id','')):
        eid=row.get('entry_id',''); reason=None
        try:
            if not ID.fullmatch(eid): raise ValueError('invalid_entry_id')
            if entry_counts[eid]>1: raise ValueError('duplicate_calculation_entry')
            archive=row['archive']; meta=archive['metadata']; m=archive['results']['material']; mid=m.get('material_id','')
            if not ID.fullmatch(mid): raise ValueError('missing_material_identity')
            reduced,elements=composition(m.get('chemical_formula_hill'))
            if set(m.get('elements',[]))!=elements: raise ValueError('formula_elements_mismatch')
            if meta.get('license')!='CC BY 4.0' or meta.get('external_db')!='OQMD': raise ValueError('rights_quarantine')
            names=authors.get(eid,{}).get('authors',[])
            if not names or not all(isinstance(a,dict) and isinstance(a.get('name'),str) and a['name'].strip() for a in names): raise ValueError('missing_attribution')
            if m.get('structural_type')!='bulk': raise ValueError('not_bulk')
            s=archive['results']['properties']['structures']['structure_original']
            dims=s.get('dimension_types')
            if dims!=[1,1,1] or not all(type(x) is int for x in dims): raise ValueError('not_three_dimensional')
            rho=s.get('mass_density')
            if type(rho) not in (float,int) or not math.isfinite(rho) or rho<=0: raise ValueError('invalid_density')
            symmetry=m.get('symmetry',{}); sg=symmetry.get('space_group_number')
            if type(sg)!=int or not 1<=sg<=230: raise ValueError('missing_symmetry')
            method=archive['results'].get('method',{})
            if not isinstance(method,dict) or method.get('method_name')!='DFT' or not isinstance(method.get('simulation'),dict) or not method['simulation'].get('program_name'): raise ValueError('unsupported_method')
            if not all(meta.get(k) for k in ('nomad_version','nomad_commit','last_processing_time','mainfile')): raise ValueError('missing_provenance_version')
            if 'C' in elements: raise ValueError('carbon_category_review_required')
            category='metal' if elements<=METALS else 'inorganic'
            eligible.append({'candidate_id':'nomad_computed_'+hashlib.sha256(eid.encode()).hexdigest()[:16], 'project_material_id':'computed:nomad:'+mid,'provider_material_id':mid,'provider_entry_id':eid,'formula':m['chemical_formula_hill'],'reduced_formula':reduced,'category_candidate':category,'category_basis':'all-metal elemental composition; metallic behavior unverified' if category=='metal' else 'carbon-free bulk composition; taxonomy review pending','symmetry':symmetry,'density':{'value':rho,'unit':'kg/m^3','evidence_kind':'computed','source_path':'results.properties.structures.structure_original.mass_density'},'method':method,'source_url':'https://nomad-lab.eu/prod/v1/gui/entry/id/'+eid,'provenance':meta,'attribution':authors[eid], 'evidence':bindings[eid], 'rights':{'license':'CC BY 4.0','license_url':'https://creativecommons.org/licenses/by/4.0/','scope':'Computed scalar density and method metadata only; no geometry or raw calculation redistribution. Upstream ICSD geometry rights are not licensed by this packet.','changes':'Selected metadata; units labeled; composition category proposed; provider numerical density unchanged.'},'status':'candidate_pending_independent_review'})
        except (KeyError,TypeError,ValueError,AttributeError) as exc:
            reason=('missing_field:'+str(exc.args[0])) if isinstance(exc,KeyError) else str(exc)
        if reason: exclusions.append({'provider_entry_id':eid,'reason':reason})
    groups=defaultdict(list)
    for r in eligible: groups[r['provider_material_id']].append(r)
    candidates=[]
    for mid, group in sorted(groups.items()):
        # Conflicting composition/symmetry in a provider identity is quarantined,
        # never "resolved" by assigning more identities or choosing a convenient row.
        signatures={(r['reduced_formula'],r['symmetry']['space_group_number']) for r in group}
        if len(signatures)!=1:
            exclusions.extend({'provider_entry_id':r['provider_entry_id'],'reason':'provider_identity_conflict'} for r in group);continue
        if mid in existing_ids:
            exclusions.extend({'provider_entry_id':r['provider_entry_id'],'reason':'already_in_reviewed_computed_seed'} for r in group);continue
        chosen=group[0]; chosen['dedup']={'basis':'NOMAD provider material_id, not formula or calculation ID','sample_entry_count':len(group),'sample_entry_ids':[r['provider_entry_id'] for r in group],'selection':'Lexicographically first eligible entry within bounded acquired sample; no lowest-energy or equilibrium claim','cross_provider_or_legacy_equivalence':'unresolved; excluded from global coverage total'}
        candidates.append(chosen)
        exclusions.extend({'provider_entry_id':r['provider_entry_id'],'reason':'repeated_calculation_same_provider_material'} for r in group[1:])
    return {'schema':'nomad-candidate-batch/1','baseline_commit':BASELINE,'status':'pending_independent_review','counts':{'acquired_entry_rows':len(rows),'candidate_provider_material_groups':len(candidates),'category_candidates':dict(sorted(Counter(c['category_candidate'] for c in candidates).items())),'excluded_entry_rows':len(exclusions),'exclusion_reasons':dict(sorted(Counter(x['reason'] for x in exclusions).items())),'admitted_materials':0,'global_unique_material_total':None},'candidates':candidates,'exclusions':exclusions}

def main():
    p=argparse.ArgumentParser(); sub=p.add_subparsers(dest='command',required=True)
    c=sub.add_parser('collect');c.add_argument('evidence');c.add_argument('--pages',type=int,default=10);c.add_argument('--after')
    a=sub.add_parser('repair-attribution');a.add_argument('evidence')
    n=sub.add_parser('normalize');n.add_argument('evidence');n.add_argument('output');n.add_argument('--seed',required=True)
    args=p.parse_args()
    if args.command=='collect': collect(args.evidence,args.pages,args.after)
    elif args.command=='repair-attribution': repair_attribution(args.evidence)
    else:
        seed=json.loads(Path(args.seed).read_text());ids={r['provider_material_id'] for r in seed['records']}
        packet=normalize(*load_evidence(args.evidence),existing_ids=ids)
        packet['seed_sha256']=hashlib.sha256(Path(args.seed).read_bytes()).hexdigest()
        write(Path(args.output),packet);print(json.dumps(packet['counts'],indent=2))
if __name__=='__main__': main()
