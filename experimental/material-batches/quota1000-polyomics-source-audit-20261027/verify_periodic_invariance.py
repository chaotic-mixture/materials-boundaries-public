"""Metamorphic check of every accepted source literal under graph relabeling."""
import argparse
from hashlib import sha256
import json
from pathlib import Path

from rdkit import Chem, rdBase
from periodic_repeat_graph import normalize,parse,METHOD

def verify(index_path,summary_path,output):
    summary=json.loads(summary_path.read_bytes())
    raw=index_path.read_bytes()
    if sha256(raw).hexdigest()!=summary['graph_index_sha256']:
        raise ValueError('Unknown graph index bytes')
    if summary['method']!=METHOD or summary['rdkit_version']!=rdBase.rdkitVersion:
        raise ValueError('Graph environment differs from the recorded prototype')
    index=json.loads(raw)
    source_keys={}
    for digest,group in index['groups'].items():
        if digest!=group['periodic_graph']['periodic_graph_key_sha256']:
            raise ValueError('Group digest differs from its record')
        for row in group['source_records']:
            smiles=row['source_smiles_1']
            if smiles in source_keys and source_keys[smiles]!=digest:
                raise ValueError('One source literal maps to conflicting keys')
            source_keys[smiles]=digest
    failures=[]
    comparisons=0
    for step,(smiles,expected) in enumerate(sorted(source_keys.items())):
        molecule=parse(smiles)
        number=molecule.GetNumAtoms()
        orders=[list(reversed(range(number))),list(range(1,number))+[0]]
        for permutation in orders:
            relabeled=Chem.RenumberAtoms(molecule,permutation)
            alternate=Chem.MolToSmiles(relabeled,canonical=False,isomericSmiles=True)
            result=normalize(alternate)
            comparisons+=1
            if result['periodic_graph_key_sha256']!=expected:
                failures.append({'source_smiles':smiles,'alternative_smiles':alternate,
                                 'expected':expected,'actual':result['periodic_graph_key_sha256']})
        if (step+1)%500==0:
            print(json.dumps({'source_literals_checked':step+1,'total':len(source_keys)}),flush=True)
    result={'schema':'polyomics-periodic-relabeling-verification/1','scope':'Producer metamorphic graph invariance, not independent identity approval',
            'method':METHOD,'rdkit_version':rdBase.rdkitVersion,
            'index_sha256':summary['graph_index_sha256'],'source_literals':len(source_keys),
            'comparisons':comparisons,'failures':failures,'passed':not failures,
            'canonical_polymer_identity_count':None,'admitted_increment':0}
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:v for k,v in result.items() if k!='failures'}),flush=True)
    if failures:
        raise ValueError(f'{len(failures)} graph representations changed their grouping')
    return result

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--index',type=Path,required=True)
    parser.add_argument('--summary',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    verify(args.index,args.summary,args.output)
