"""Freeze 1,000 source-fact candidates per category; never modify runtime catalogs."""
import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[3]
AUDIT=ROOT/'experimental/material-batches/quota1000-jarvis-source-audit-20261027'
sys.path.insert(0,str(AUDIT))
from screen_compositions import formula_key,ratio_key,METALS

HEAD='f13586759af6a391635fa81da20c73eb6a6c1c6c'
INDEX_SHA='671c3c2fbd2034aaf8d2081ffad9343bd1e258f7195a279caf06cfb2e4bd15e3'
BASELINE_SHA={
    'materials_boundaries/data/materials.json':'e6cead9a5f06d2334788d82c459f6e9ade9ccf94ac2625c7a3132812b7974479',
    'materials_boundaries/data/reference_properties.json':'5b2e5fb3f8b57d0535cfe6d854a9a86b1f7fa8addf73dd933492242836a51c1a',
    'materials_boundaries/data/sources.json':'e7a7609a21f65b4838f146fccefeaa2ab8964b84d18c50252d16dd329bfda43e',
    'formal-catalog/materials_project_catalog/data/formal_computed_review.json':'a285523b2b2fdbf0d750ce6ac56e3abfb80d5c42056229a2352b016a787fd875'}
# Guards deliberately hold possible overlap; they do not equate materials.
FORMULA_GUARDS=('Al2O3','SiO2','ZrO2','CaSO4','BeO','CaO','CeO2','CuO','MgO','TiO2',
                'NiO','GeO2','As2O3','SeO2','SnO2','ThO2','Mg2SiO4','MgWO4','ZnB2O4','BaN2O6','SrN2O6')
ELEMENT_SET_GUARDS=(
    ('Cu','Zn'),('Cu','Ni'),('Al','Mg'),('Al','Ti','V'),('Al','Mg','Zn'),
    ('Cr','Fe'),('Fe','Ni'),('Cr','Ni'),('Fe','Mn'),('Cr','Fe','Ni'),('Cr','Fe','Mn','Ni'),
    ('O','Y','Zr'),('O','Al','Y'),('O','Al','Si'),('O','B','Si'))

def eligible(facts,formal_keys,guards=None):
    key=facts['ratio_key']
    elements=frozenset(part.split(':')[0] for part in key.split('|'))
    if formula_key(facts['formula'])!=key:
        raise ValueError('Formula differs from candidate composition key')
    if facts['screening_bucket']=='all_metal_elements' and not elements<=METALS:
        raise ValueError('Metal bucket contradicts source elemental composition')
    if facts['screening_bucket']=='oxygen_containing_no_C_H' and ('O' not in elements or {'C','H'}&elements):
        raise ValueError('Oxide bucket contradicts source elemental composition')
    formula_guards,element_guards=guards if guards is not None else (
        {formula_key(f) for f in FORMULA_GUARDS},{frozenset(e) for e in ELEMENT_SET_GUARDS})
    if key in formal_keys:
        return None,'Existing formal computed composition'
    if key in formula_guards:
        return None,'Conservative existing-material formula guard'
    if elements in element_guards:
        return None,'Conservative existing-material element-set guard'
    if not 2<=len(elements)<=4:
        return None,'Outside selected two-to-four-element scope'
    if facts['screening_bucket']=='all_metal_elements':
        return 'metal',None
    if facts['screening_bucket']=='oxygen_containing_no_C_H' and len(elements)<=3:
        return 'inorganic',None
    return None,'Outside selected all-metal/limited-oxide categories'

def select(index_path,limit=1000):
    if type(limit) is not int or limit<1:
        raise ValueError('Positive integer candidate limit required')
    if subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()!=HEAD:
        raise ValueError('Different working checkout HEAD')
    if sha256((AUDIT/'screen_compositions.py').read_bytes()).hexdigest()!='b5736cc1d32ac701534fd371aa8ff50a7c39e3af3d94bf1048101170c7b6d863':
        raise ValueError('Unreviewed source helper')
    for path,digest in BASELINE_SHA.items():
        if sha256((ROOT/path).read_bytes()).hexdigest()!=digest:
            raise ValueError('Changed frozen candidate-preparation baseline: '+path)
    raw=index_path.read_bytes()
    if sha256(raw).hexdigest()!=INDEX_SHA:
        raise ValueError('Unreviewed complete source composition index')
    index=json.loads(raw)
    formal=json.loads((ROOT/'formal-catalog/materials_project_catalog/data/formal_computed_review.json').read_bytes())
    accepted=[r for r in formal['records'] if r['decision']=='accepted']
    if len(accepted)!=24:
        raise ValueError('Different formal computed review baseline')
    formal_keys={ratio_key(r['canonical_composition']) for r in accepted}
    if len(formal_keys)!=24:
        raise ValueError('Formal computed compositions are not the expected distinct set')
    guards=({formula_key(f) for f in FORMULA_GUARDS},{frozenset(e) for e in ELEMENT_SET_GUARDS})
    selected={'metal':[],'inorganic':[]};held=Counter();available=Counter()
    groups=sorted(index['groups'].items(),key=lambda item:int(item[1]['representative']['jid'].split('-')[1]))
    for group_key,group in groups:
        facts=group['representative']
        if group_key!=facts['ratio_key']:
            raise ValueError('Index key differs from representative composition')
        category,reason=eligible(facts,formal_keys,guards)
        if category is None:
            held[reason]+=1
            continue
        available[category]+=1
        if len(selected[category])>=limit:
            continue
        selected[category].append({
            'proposed_category':category,'proposed_conservative_composition_key':group_key,
            'source_record':facts,'source_rows_sharing_composition':group['source_row_count'],
            'representation':'one source-qualified computed crystal model per composition; other phases do not add identities',
            'proposed_quantity':'mass_density','proposed_unit_code':'g/cm^3',
            'proposed_evidence_kind':'published_computational_reference',
            'proposed_method_type':'source_reported_computational_structure_density',
            'experimental_existence':'unknown','phase_stability':'unknown','per_record_convergence':'unknown',
            'exact_temperature_K':None,'exact_pressure_Pa':None,
            'candidate_status':'proposed_not_independently_approved_or_admitted'})
    if any(len(v)!=limit for v in selected.values()):
        raise ValueError('Insufficient candidates after explicit overlap guards')
    keys=[r['proposed_conservative_composition_key'] for rows in selected.values() for r in rows]
    if len(keys)!=len(set(keys)):
        raise ValueError('Candidate compositions overlap between categories')
    return {'schema':'jarvis-frozen-source-fact-candidates/1',
            'batch_id':'jarvis-density-candidates-20261027','status':'held_pending_contract_implementation_and_identity_review',
            'handoff_ready':False,'admitted_increment':0,'proposed_counts':{k:len(v) for k,v in selected.items()},
            'available_composition_groups_after_guards':dict(available),'held_group_counts':dict(held),
            'source_index_sha256':INDEX_SHA,'source_dataset_doi':'10.6084/m9.figshare.6815699.v11',
            'source_archive_sha256':'f9e0a3309f0000d5de1ec9e49c93963109ea45e63f451103f8f6595d2eabf7f5',
            'working_baseline_head':HEAD,'working_baseline_includes_five_pending_sanchez_identities':True,
            'baseline_sha256':dict(BASELINE_SHA),'formal_composition_keys_excluded':sorted(formal_keys),
            'conservative_formula_guards':list(FORMULA_GUARDS),
            'conservative_element_set_guards':[list(v) for v in ELEMENT_SET_GUARDS],
            'guard_scope':'Broad holds for possible baseline overlap are not chemical equivalence assertions or a complete identity review.',
            'selection':'Smallest numeric JID representative per frozen source composition group; sorted by numeric JID, first requested count per category after guards. No energy/stability ranking or property averaging.',
            'candidates':selected,
            'pending':['Independent finite candidate identity/category/overlap review',
                       'Computed-structure-density method implementation, tests and independent implementation review',
                       'Ordinary schema/source-fidelity/history/installed gates before runtime admission',
                       'Close current five-alloy full regression before altering its frozen runtime inputs']}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--index',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    result=select(args.index)
    raw=(json.dumps(result,ensure_ascii=False,indent=2)+'\n').encode('utf8')
    if args.output.exists() and args.output.read_bytes()!=raw:
        raise ValueError('Refuse to replace a different frozen candidate')
    args.output.write_bytes(raw)
    print(json.dumps({'proposed':result['proposed_counts'],'available':result['available_composition_groups_after_guards'],
                      'sha256':sha256(raw).hexdigest(),'admitted_increment':0,'handoff_ready':False}),flush=True)
