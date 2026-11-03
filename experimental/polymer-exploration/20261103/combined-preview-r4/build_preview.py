"""Apply only the eight reviewed-wording corrections to isolated r3 data."""
from copy import deepcopy
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT))
from materials_boundaries.database import Database
AREA = ROOT/'experimental/polymer-exploration/20261103'


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p): return json.loads(p.read_bytes())
def write(p,o):
    with p.open('x',encoding='utf-8') as f: json.dump(o,f,ensure_ascii=False,indent=2); f.write('\n')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prior-preview-dir',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args();output=args.output_dir.resolve()
    assert not output.exists() and not output.is_relative_to(ROOT)
    manifest=read(AREA/'combined-preview-r3/REVIEW_INPUTS_R3.json')
    data={}
    for name,h in manifest['external_preview_files_sha256'].items():
        p=args.prior_preview_dir/name;assert sha(p)==h;data[p.stem]=read(p)
    prior=Database(data);assert prior.snapshot==manifest['combined_snapshot']
    diff=read(AREA/'pbs-existing-tensile-draft-r2/DIFF_R2.json')
    candidate_path=AREA/'pbs-existing-tensile-draft-r2/native-candidate-r2.json'
    assert sha(candidate_path)==diff['candidate_sha256']
    candidate=read(candidate_path);replacements={r['id']:r for r in candidate['reference_properties']['records']}
    changed=[]
    for r in data['reference_properties']['records']:
        if r['id'] not in replacements:continue
        new=replacements[r['id']]
        if r==new:continue
        oldcopy,newcopy=deepcopy(r),deepcopy(new)
        for key in ('text','notes'):newcopy['conditions']['test_standard'][key]=oldcopy['conditions']['test_standard'][key]
        assert oldcopy==newcopy and r['id'] in diff['changed_property_ids']
        changed.append(r['id']);r.clear();r.update(deepcopy(new))
    assert sorted(changed)==sorted(diff['changed_property_ids'])
    after=Database(data);contracts=after.validate_scientific_contracts()
    assert prior.data['materials']==data['materials'] and prior.data['sources']==data['sources']
    assert set(prior.properties)==set(after.properties)
    output.mkdir(parents=True);tables=output/'native-tables';tables.mkdir()
    for name,table in data.items():write(tables/(name+'.json'),table)
    report={'schema':'polymer-combined-preview/4','prior_snapshot':prior.snapshot,'preview_snapshot':after.snapshot,
            'changed_property_ids':changed,'changed_fields_per_property':['conditions.test_standard.text','conditions.test_standard.notes'],
            'all_other_objects_unchanged':True,'contracts':contracts,'native_applied':False,'published':False,
            'preview_file_sha256':{p.name:sha(p) for p in tables.iterdir()},'independent_recheck':'pending'}
    write(output/'COMBINED_VALIDATION_R4.json',report)
    print(json.dumps({'snapshot':after.snapshot,'changed_fields':8,'contracts':contracts}))


if __name__=='__main__':main()
