"""Run the unreviewed periodic graph screen on fixed source CSVs, outside runtime."""
import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path

import inspect_polyomics as audit
from periodic_repeat_graph import normalize, METHOD, rdBase

def run(cache,output_dir):
    if output_dir.exists():
        raise ValueError('Use a new output directory to preserve prior evidence')
    inputs={}
    source_rows=[]
    excluded=Counter()
    for name,(digest,size) in audit.FILES.items():
        raw=(cache/name).read_bytes()
        if len(raw)!=size or sha256(raw).hexdigest()!=digest:
            raise ValueError('Unexpected fixed source bytes: '+name)
        inputs[name]=digest
        for index,row in audit.read_rows(raw):
            facts=audit.selected_facts(row)
            if any(row[f'smiles_{i}'] for i in [2,3,4]):
                excluded['Multiple source components/attachment models require separate review']+=1
                continue
            facts.update(source_file=name,source_row_index=index)
            source_rows.append(facts)
    literal_values=sorted({r['source_smiles_1'] for r in source_rows})
    normalized,held={},{}
    for index,smiles in enumerate(literal_values):
        try:
            normalized[smiles]=normalize(smiles)
        except ValueError as error:
            held[smiles]=str(error)
        if (index+1)%500==0:
            print(json.dumps({'source_literals_processed':index+1,'total':len(literal_values)}),flush=True)
    groups={}
    held_examples=[]
    for facts in source_rows:
        smiles=facts['source_smiles_1']
        if smiles in held:
            excluded[held[smiles]]+=1
            if len(held_examples)<25:
                held_examples.append({'uuid':facts['uuid'],'reason':held[smiles]})
            continue
        identity=normalized[smiles]
        digest=identity['periodic_graph_key_sha256']
        if digest not in groups:
            groups[digest]={'periodic_graph':identity,'source_records':[]}
        previous=groups[digest]['periodic_graph']
        if previous['four_repeat_cyclic_graph_smiles']!=identity['four_repeat_cyclic_graph_smiles']:
            raise ValueError('Graph digest collision')
        if previous['primitive_non_dummy_atoms']!=identity['primitive_non_dummy_atoms']:
            raise ValueError('Inconsistent atom count under a normalized graph')
        groups[digest]['source_records'].append(facts)
    for group in groups.values():
        group['source_records'].sort(key=lambda r:(r['uuid'],r['source_file']))
    index_raw=(json.dumps({'schema':'polyomics-unreviewed-periodic-graph-index/1','groups':groups},ensure_ascii=False,indent=2)+'\n').encode('utf8')
    completed=sum(len(g['source_records']) for g in groups.values())
    summary={'schema':'polyomics-unreviewed-periodic-graph-summary/1','status':'prototype_not_independently_reviewed',
             'method':METHOD,'rdkit_version':rdBase.rdkitVersion,'source_inputs_sha256':inputs,
             'source_rows':sum(audit_count for audit_count in [len(source_rows),sum(v for k,v in excluded.items() if k.startswith('Multiple source'))]),
             'single_component_source_rows':len(source_rows),'literal_repeat_units_processed':len(literal_values),
             'graph_normalized_source_rows':completed,'operational_periodic_graph_groups':len(groups),
             'held_source_rows':dict(excluded),'held_examples':held_examples,
             'nonprimitive_source_literals':sum(r['repeat_factor']>1 for r in normalized.values()),
             'graph_index_sha256':sha256(index_raw).hexdigest(),'canonical_polymer_identity_count':None,
             'admitted_increment':0,'remaining':['Independent algorithm and finite identity review',
                                              'Overlap with the existing polymer catalog and imported sources',
                                              'Version-specific physical units and statistical aggregation',
                                              'Frozen source-supported candidates and ordinary admission gates'],
             'boundaries':['Keys are operational graph comparison results, not approved material identities.',
                           'Explicit stereochemistry, ionic models and non-single attachment bonds remain held.',
                           'Original density values and conditions remain per simulation UUID; no new average is calculated.',
                           'No computational property becomes an experimental measurement or a certified allowable.']}
    output_dir.mkdir(parents=True)
    (output_dir/'periodic-graph-index.json').write_bytes(index_raw)
    (output_dir/'periodic-graph-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps(summary,ensure_ascii=False),flush=True)
    return summary

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args()
    run(args.cache,args.output_dir)
