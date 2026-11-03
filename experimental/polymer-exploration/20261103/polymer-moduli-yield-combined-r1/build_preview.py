"""Compose the independently reviewed NR/PHBV modulus and PBAT/PBS-PBAT yield supplements."""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT))
from materials_boundaries.database import Database
AREA=ROOT/'experimental/polymer-exploration/20261103'


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def write(p,obj):
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args();out=args.output_dir.resolve();assert not out.exists() and not out.is_relative_to(ROOT/'materials_boundaries')
    before=Database();data=deepcopy(before.data);inputs={};seen={t:set() for t in ['materials','sources','reference_properties']}
    for packet in ['nr-finite-strain-modulus-draft-r1','phbv39-flexural-modulus-draft-r1','pbs-pbat-yield-native-r1']:
        p=AREA/packet;revision='R2' if packet=='pbs-pbat-yield-native-r1' else 'R1'; manifest=read(p/('REVIEW_INPUTS_'+revision+'.json'));review=read(p/('INDEPENDENT_REVIEW_'+revision+'.json'))
        assert review['decision']=='approved' and review['review_inputs_sha256']==sha(p/('REVIEW_INPUTS_'+revision+'.json'))
        for name,h in manifest['files_sha256'].items():source=ROOT/name if packet=='pbs-pbat-yield-native-r1' else p/name; assert sha(source)==h;inputs[source.relative_to(ROOT).as_posix()]=h
        for name in ['REVIEW_INPUTS_'+revision+'.json','INDEPENDENT_REVIEW_'+revision+'.json']:inputs[(p/name).relative_to(ROOT).as_posix()]=sha(p/name)
        candidate=p/'native-candidate-r1.json' if packet=='pbs-pbat-yield-native-r1' else p/'frozen-r1/native-candidate-r1.json';c=read(candidate);assert c['baseline_snapshot']==before.snapshot
        assert sha(candidate)==review['candidate_sha256']
        for table in seen:
            changes=c[table]['records'];ids={r['id'] for r in changes};assert not ids&seen[table];seen[table]|=ids
            if table=='reference_properties':
                assert not ids&set(before.properties);data[table]['records'].extend(deepcopy(changes))
            else:
                original={r['id']:r for r in data[table]['records']};assert ids<=original.keys()
                original.update({r['id']:deepcopy(r) for r in changes});data[table]['records']=[original[r['id']] for r in data[table]['records']]
    after=Database(data);contracts=after.validate_scientific_contracts()
    assert after.identities==before.identities and after.grades==before.grades and set(after.states)==set(before.states)
    assert all(after.properties[pid]==r for pid,r in before.properties.items())
    assert len(after.properties)==len(before.properties)+4
    out.mkdir(parents=True);tables=out/'native-tables';tables.mkdir()
    for name,table in data.items():write(tables/(name+'.json'),table)
    write(out/'VALIDATION_R1.json',{'schema':'existing-polymer-moduli-yield-combined-preview/1','baseline_snapshot':before.snapshot,'preview_snapshot':after.snapshot,'input_files_sha256':inputs,'preview_files_sha256':{p.name:sha(p) for p in tables.iterdir()},'new_properties':4,'new_identities':0,'new_states':0,'new_sources':0,'modified_states':4,'source_metadata_amendments':3,'all_existing_property_objects_unchanged':True,'contracts':contracts,'yield_strength_concrete_mapping_included':True,'native_applied':False,'pushed':False})
    print(json.dumps({'snapshot':after.snapshot,'new_properties':4,'contracts':contracts}))


if __name__=='__main__':main()
