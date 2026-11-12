"""Guard the experimental branch and audit the exact cumulative data delta."""
import ast,hashlib,json,subprocess
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
EXT=ROOT.parent/'open-database-evidence/polymer-consolidated-delivery-20261112-r69-r72'
HEAD='fb996df80be67aba2896169935f997ad08655690'


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def write(p,obj):
    with p.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)


def main():
    assert git('rev-parse','HEAD').decode().strip()==HEAD
    assert git('branch','--show-current').decode().strip()=='experimental/open-database'
    assert not git('diff','--cached','--name-only','-z'),'preparation requires empty index'
    # The remote SHA was independently read through the GitHub connector this turn.
    for phase in ('69','70','71','72'):
        d=HERE.parent/('local-acceptance-r'+phase)
        entry=d/('REVIEW_FINAL_INPUTS_R'+phase+'.json');receipt=read(d/('INDEPENDENT_FINAL_REVIEW_R'+phase+'.json'))
        assert receipt['decision']=='approved' and receipt['review_inputs_sha256']==sha(entry)
    EXT.mkdir(exist_ok=False)
    baseline=EXT/'baseline-commit';baseline.mkdir()
    names=['materials_boundaries/data/materials.json','materials_boundaries/data/reference_properties.json','materials_boundaries/data/sources.json','schemas/reference_properties.schema.json','materials_boundaries/_material_derivation.py']
    old={}
    for name in names:
        raw=git('show',HEAD+':'+name);p=baseline/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
        old[name]=p
    materials=read(ROOT/names[0]);properties=read(ROOT/names[1]);before_m=read(old[names[0]]);before_p=read(old[names[1]])
    previous_props={p['id']:p for p in before_p['records']};current_props={p['id']:p for p in properties['records']}
    previous_states={s['id']:s for s in before_m['records']};current_states={s['id']:s for s in materials['records']}
    assert all(current_props[k]==v for k,v in previous_props.items())
    assert all(current_states[k]==v for k,v in previous_states.items())
    assert materials['identities']==before_m['identities'] and materials['grades']==before_m['grades']
    assert (ROOT/names[2]).read_bytes()==old[names[2]].read_bytes()
    added_props=[p for p in properties['records'] if p['id'] not in previous_props]
    added_states=[s for s in materials['records'] if s['id'] not in previous_states]
    assert len(added_props)==17 and len(added_states)==13
    identities={i['id']:i for i in materials['identities']}
    categories=dict(Counter(identities[current_states[p['material_state_id']]['identity_id']]['category'] for p in added_props))
    assert categories=={'polymer':9,'composite':8}
    new_schema=read(ROOT/names[3]);old_schema=read(old[names[3]])
    assert len(old_schema['$defs']['property']['oneOf'])==27 and len(new_schema['$defs']['property']['oneOf'])==31
    assert new_schema['$defs']['property']['oneOf'][:27]==old_schema['$defs']['property']['oneOf']
    assert all(new_schema['$defs'][k]==v for k,v in old_schema['$defs'].items() if k!='property')
    a=ast.parse((ROOT/names[4]).read_text('utf-8'));b=ast.parse(old[names[4]].read_text('utf-8'))
    f=next(n for n in a.body if isinstance(n,ast.FunctionDef) and n.name=='validate_derivation')
    for expected in ('_sec_molar_mass_contract','_ftir_band_area_ratio_contract','_dsc_crystallinity_contract'):
        assert isinstance(f.body[0],ast.ImportFrom) and f.body[0].module==expected and isinstance(f.body[1],ast.If)
        del f.body[:2]
    assert ast.dump(a)==ast.dump(b)
    native={name:sha(ROOT/name) for name in names[:3]}
    report=dict(baseline_commit=HEAD,branch='experimental/open-database',remote_ref_observed_same_sha=True,
                new_properties=17,new_contexts=13,new_property_categories=categories,new_property_quantities=dict(Counter(p['quantity'] for p in added_props)),
                new_property_ids=[p['id'] for p in added_props],new_state_ids=[s['id'] for s in added_states],
                old5740properties_unchanged=True,old5420states_unchanged=True,identities_grades_sources_unchanged=True,
                identities=len(materials['identities']),grades=len(materials['grades']),properties=len(current_props),states=len(current_states),sources=134,
                old27branches_and_definitions_preserved=True,current_branches=31,old_derivation_AST_preserved_after_new_dispatch_removed=True,
                after_sha256=native,snapshot='454ab12d97c41622dac4ed8d604e356537246869e64a0a6ce9ac289143e2a953',
                baseline_files_sha256={str(p):sha(p) for p in old.values()},phase='Guarded cumulative preparation before doc updates',
                goal='Concentrated polymer exploration;delivery is a milestone,not goal completion',main_merge=False,deployment=False,commit_push='not_done')
    assert report['properties']==5757 and report['states']==5433
    write(HERE/'PREPARATION_R1.json',report)
    print(json.dumps({k:v for k,v in report.items() if k in ('new_properties','new_contexts','new_property_categories','properties','states','current_branches')},ensure_ascii=False),flush=True)


if __name__=='__main__':main()
