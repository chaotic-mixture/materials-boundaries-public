"""Audit two fixed PolyOmics CSVs without asserting chemical identities or admission."""
import argparse
from collections import Counter
import csv
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import io
import json
from pathlib import Path
from uuid import UUID

REVISION = 'cbab9483395a32dd968fbeb047808031fb0f3a13'
FILES = {'PFAS.csv':('2e80ce549bd6c6e4dfc765d842416278a18422d169859939dd88ec41b61c5529',13714504),
         'biodegradable_candidate_polyester.csv':('fd94f1d2c15640ad13b99ba1821fc9e75191db38cd2f40cdbeb433609d4eb91d',778096)}
CONDITIONS = ('temp','press','forcefield','RadonPy_ver','preset_eq_ver','check_eq','tacticity')
REQUIRED = ('UUID','smiles_list','smiles_1','smiles_2','smiles_3','smiles_4','density',*CONDITIONS)

def read_rows(raw):
    reader = csv.DictReader(io.StringIO(raw.decode('utf-8-sig'),newline=''))
    fields = reader.fieldnames
    if not fields or len(fields)!=len(set(fields)) or not set(REQUIRED)<=set(fields):
        raise ValueError('Missing or duplicate required CSV columns')
    for index,row in enumerate(reader):
        if None in row or any(v is None for v in row.values()):
            raise ValueError('Row width differs from declared source columns')
        yield index,row

def selected_facts(row):
    identifier=row['UUID']
    if str(UUID(identifier))!=identifier:
        raise ValueError('Noncanonical source UUID')
    density=row['density']
    try:
        number=Decimal(density)
    except InvalidOperation as error:
        raise ValueError('Invalid density') from error
    if not number.is_finite() or number<=0:
        raise ValueError('Nonpositive/nonfinite density')
    if row['check_eq']!='True':
        raise ValueError('Source equilibrium flag is not explicitly True')
    smiles=row['smiles_1']
    if not smiles or any(ord(c)<32 or 127<=ord(c)<=159 for c in smiles):
        raise ValueError('Missing or controlled source repeat-unit text')
    return {'uuid':identifier,'source_smiles_1':smiles,'source_smiles_list':row['smiles_list'],
            'source_density_literal':density,'source_conditions':{k:row[k] for k in CONDITIONS}}

def summarize_rows(rows):
    total, valid, lexical_single=0,[],[]
    rejected=Counter()
    conditions={key:Counter() for key in CONDITIONS}
    for index,row in rows:
        total+=1
        for key in CONDITIONS:
            conditions[key][row[key]]+=1
        try:
            facts=selected_facts(row)
        except ValueError as error:
            rejected[str(error)]+=1
            continue
        facts['source_row_index']=index
        valid.append(facts)
        if facts['source_smiles_1'].count('*')==2 and not any(row[f'smiles_{n}'] for n in [2,3,4]):
            lexical_single.append(facts)
    if len({r['uuid'] for r in valid})!=len(valid):
        raise ValueError('Duplicate UUID within one source file')
    summary={'source_rows':total,'source_valid_density_rows':len(valid),
             'unique_source_uuid':len({r['uuid'] for r in valid}),
             'literal_unique_smiles_1':len({r['source_smiles_1'] for r in valid}),
             'literal_unique_smiles_list':len({r['source_smiles_list'] for r in valid}),
             'single_component_two_star_text_rows':len(lexical_single),
             'single_component_two_star_literal_unique_smiles':len({r['source_smiles_1'] for r in lexical_single}),
             'source_condition_literals':{k:dict(v) for k,v in conditions.items()},
             'rejected_by_reason':dict(rejected),'canonical_polymer_identity_count':None,
             'admitted_increment':0}
    return summary,valid

def audit(cache,output):
    summary,all_rows={},{}
    for name,(digest,size) in FILES.items():
        raw=(cache/name).read_bytes()
        if len(raw)!=size or sha256(raw).hexdigest()!=digest:
            raise ValueError('Unverified fixed source bytes: '+name)
        summary[name],all_rows[name]=summarize_rows(read_rows(raw))
        summary[name].update(source_sha256=digest,source_bytes=size)
    by_uuid={}
    conflicts=[]
    for name,rows in all_rows.items():
        for facts in rows:
            key=facts['uuid']
            comparison={k:v for k,v in facts.items() if k!='source_row_index'}
            if key in by_uuid and by_uuid[key]['facts']!=comparison:
                conflicts.append(key)
            if key not in by_uuid:
                by_uuid[key]={'facts':comparison,'files':[]}
            by_uuid[key]['files'].append(name)
    result={'schema':'polyomics-source-audit/1','status':'held_source_audit_only','revision':REVISION,
            'dataset_doi':'10.57967/hf/7475','source_files':summary,
            'cross_file_unique_uuid_count':len(by_uuid),
            'cross_file_repeated_uuid_count':sum(len(v['files'])>1 for v in by_uuid.values()),
            'cross_file_conflicting_selected_fact_uuids':sorted(set(conflicts)),
            'canonical_polymer_identity_count':None,'admitted_increment':0,
            'outstanding':['RDKit parsing and periodic repeat-unit equivalence, including atom maps, end reversal and nonprimitive repeat units',
                           'Finite identity overlap and source-qualified crosswalk against the existing polymer catalog',
                           'Version-specific units, trajectory aggregation and simulation-condition interpretation',
                           'Independent source and identity review, then a frozen candidate and runtime gates'],
            'limits':['UUID is a simulation/source record identity, not automatically a new polymer.',
                      'Two asterisks and one component are lexical screening only, not validated polymer connectivity.',
                      'Tacticity, simulation repeats, states and software versions cannot by themselves inflate identity counts.',
                      'MD values are not experimental facts or certified performance; no experimental validation values were downloaded.']}
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps(result,ensure_ascii=False),flush=True)
    return result

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    audit(args.cache,args.output)
