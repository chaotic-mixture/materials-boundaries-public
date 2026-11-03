"""Map two reviewed source-labelled PBS/PBAT break elongations."""
from copy import deepcopy
import hashlib,json,sys
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT))
from materials_boundaries.database import Database,read_snapshot
from materials_boundaries.material_presentation import render_material_catalog
from jsonschema import Draft202012Validator,FormatChecker
AREA=ROOT/'experimental/polymer-exploration/20261103'
BASE='596b1f2b5cfd756c696429a243b98d8c059ab3be3fe76aae370fad5cba7f99fa'
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
    dest=Path(sys.argv[1]).resolve();assert not dest.exists() and not dest.is_relative_to(ROOT)
    draft=AREA/'pbs-pbat-break-elongation-draft-r1';facts=read(draft/'SOURCE_FACTS_R1.json');review=read(draft/'INDEPENDENT_SOURCE_REVIEW_R1.json')
    assert review['decision']=='approved' and review['review_inputs_sha256']==sha(draft/'REVIEW_INPUTS_R1.json')
    asset=facts['source_asset'];assert sha(Path(asset['path_hint']))==asset['sha256']
    before=Database();assert before.snapshot==BASE==facts['baseline_snapshot']
    props=[];states={};sources={}
    for f in facts['rows']:
        old=before.properties[f['base_property_id']];assert old['quantity']=='tensile_yield_strength' and old['source_id']==f['source_id'] and old['material_state_id']==f['existing_state_id']
        assert f['new_property_id'] not in before.properties
        p=deepcopy(old);p.update(id=f['new_property_id'],version='1.0.0',quantity='tensile_elongation_at_break',quantity_dimension='dimensionless',source_property_label=f['source_property_label'])
        p['reported_value'].update(value_text=f['number'],number=f['number'],unit_text='%',unit_code='percent_elongation')
        assert p['summary_statistic']=='reported_value' and p['uncertainty_status']=='reported_plus_minus_unspecified' and p['sample_count']['value']==5 and p['sample_count']['relation']=='exact'
        p['uncertainty'].update(value_text=f['uncertainty_number'],number=f['uncertainty_number'],unit_text='%',unit_code='percent_elongation',scope='Absolute source plus-minus amplitude in elongation percentage points for this selected group. Statistical construction is unspecified; not a relative percentage error, SD, SE, CI or tolerance.',coverage_factor=None,confidence_level=None)
        ev={'source_id':p['source_id'],'url':p['source_document']['url'],'locator':f['locator'],'supports':['reported_value','classification']}
        p['uncertainty']['evidence']=[dict(ev,supports=['uncertainty'])]
        p['uncertainty_note']=f['number']+' plus/minus '+f['uncertainty_number']+'% on the original elongation percentage scale. Preserve the printed amplitude as reported_plus_minus_unspecified. Five specimens do not define the central estimator or dispersion type; not a verified mean/SD, relative error, confidence interval or bound.'
        p['basis_note']='Source Table3 labels Tensile Strain at Break %. reported_value preserves the original scalar without asserting a mean, individual specimen, estimator or pooling order. No conversion from strength, modulus, target elongation or relative performance claim.'
        definition='Source ASTM D638 tensile citation, Instron tester and dog-bone specimens; model and edition not established. Five specimens per selected group after conditioning at25C for48h, tensile testing at25C. Loading rate, RH, actual reference gauge, strain estimator/convention, rupture criterion/selection, pooling order and independent batches remain unknown. Source-labelled percentage strain at break only; no strain-rate, stretch-ratio or mechanics conversion.'
        p['method_definition'].update(type='source_reported_conventional',definition=definition,extraction_window=None,evidence=[dict(ev,supports=['method','condition'])])
        p['conditions']['test_method'].update(text=definition,evidence=[dict(ev,supports=['method','condition'])],notes='The source citation does not establish independent standard compliance. Reported25C/48h conditioning does not establish controlled RH or moisture equilibration.')
        p['conditions']['additional_conditions']=[x for x in p['conditions']['additional_conditions'] if x['name']!='yield_criterion']
        p['sample_count']['scope']='Five source-reported tensile specimens per selected group, not five independent production batches. Pairing, aggregation and extraction order remain unknown.'
        p['evidence']=[ev,dict(ev,supports=['method','condition','sample_count'])]
        p['source_discrepancies'].append({'description':'Source section3.2 states an approximately167% elongation decrease for the15wt% filled formulation. The reference formula/comparator and quantified claim are unverified.','disposition':'Preserve this source narrative as context outside these selected unfilled rows. Do not repair Table3, adopt a relative-performance property or claim filled-material benefits.','evidence':[dict(ev,locator='XML section3.2 mechanical-properties paragraph,15wt% filler decrease claim and Table3 comparison rows',supports=['source_discrepancy'])]})
        scope='Retained primary XML permissions, Table3 selected PBAT and unfilled PBS/PBAT70/30 break-elongation cells, sections2.6.2/3.2 protocol and narrative boundary; existing identity/preparation bindings retained. No fresh download, PDF visual, latest-revision/correction/retraction or raw-data audit.'
        p['source_document'].update(inspected_on='2026-11-03',inspection_scope=scope);p['verification']['source_inspection_scope']=scope
        p['scope_note']='Existing selected commercial PBAT grade or source-qualified unfilled PBS/PBAT70/30 state only; additives/final chemistry not independently certified. Source-labelled percentage break elongation, not a verified strain convention/gauge/rupture criterion or an imposed target. Original percentages and plus-minus amplitudes are unscaled; statistical construction and central aggregation remain unknown despite n5. Reported25C test and25C/48h conditioning do not fill RH, rate, gauge or equilibrium gaps. No filled/neat-PBS/new-blend state, paired curve, stress/elongation ratio, modulus, energy, toughness, engine input, universal bound, engineering allowable or biomedical/biodegradability certification. Source167% narrative remains unverified and no performance metric is imported.'
        s=deepcopy(before.states[p['material_state_id']]);assert s['id'] not in states
        major,minor,rev=s['version'].split('.');s['version']=f'{major}.{minor}.{int(rev)+1}';s['property_ids'].append(p['id'])
        s['source_scope']+=' Source-labelled percentage break elongation additionally recorded; central aggregation and plus-minus type remain unknown, n5 does not imply mean/SD. Actual strain/gauge/rupture, RH/rate and independent batches unconfirmed.'
        states[s['id']]=s;sources.setdefault(p['source_id'],deepcopy(before.sources[p['source_id']]))
        props.append(p)
    assert len(sources)==1
    for s in sources.values():s['claim_notes'].append('2026-11-03 existing PBAT and unfilled PBS/PBAT70/30 break-elongation supplement:1040+/-9.76% and367.01+/-86.87%, original percentage scale and absolute percentage-point amplitudes. n5,25C test and25C/48h conditioning reported; central estimator/plus-minus construction remain unknown, no SD inference. Section3.2 approximately167% filled-formulation decrease is unverified context, not repaired data or admitted performance claim. No new identity/state or engineering/biomedical claim.')
    data=deepcopy(before.data);data['reference_properties']['records'].extend(props);data['materials']['records']=[states.get(s['id'],s) for s in data['materials']['records']];data['sources']['records']=[sources.get(s['id'],s) for s in data['sources']['records']]
    after=Database(data);contracts=after.validate_scientific_contracts();assert len(after.properties)==5300 and all(after.properties[k]==p for k,p in before.properties.items())
    assert after.identities==before.identities and after.grades==before.grades and after.states.keys()==before.states.keys() and after.sources.keys()==before.sources.keys()
    for n in data:Draft202012Validator(read(ROOT/'schemas'/(n+'.schema.json')),format_checker=FormatChecker()).validate(data[n])
    dest.mkdir(parents=True);(dest/'native-tables').mkdir()
    for n,v in data.items():write(dest/'native-tables'/(n+'.json'),v)
    write(dest/'native-candidate-r1.json',{'baseline_snapshot':BASE,'stage':'not_applied','materials':{'identities':[],'grades':[],'records':list(states.values())},'sources':{'records':list(sources.values())},'reference_properties':{'records':props}})
    sid=next(iter(sources));counts={}
    for phase,db in [('before',before),('after',after)]:
        path=dest/'source-exports'/phase;db.export(path,source=sid);manifest,rows=read_snapshot(path);assert rows=={r['property']['id']:r for r in db.records(source=sid)};counts[phase]=len(rows)
    assert counts=={'before':7,'after':9}
    for lang in ('en','zh','ja','de'):
        with patch('materials_boundaries.catalog.read_catalog',side_effect=lambda n:data[n]):text=render_material_catalog({'schema_version':'1.0.0','records':props},'reference-properties',lang)
        assert all(f['number'] in text and f['uncertainty_number'] in text for f in facts['rows']) and 'unknown' in text and 'not a verified mean/SD' in text
        (dest/('render-'+lang+'.txt')).write_text(text,encoding='utf-8',newline='\n')
    write(dest/'VALIDATION_R1.json',{'baseline_snapshot':BASE,'preview_snapshot':after.snapshot,'properties':5300,'new_properties':2,'all_old_5298_complete_properties_unchanged':True,'new_identity_grade_state_source_objects':0,'modified_states':2,'modified_sources':1,'three_table_schema_format':'passed','current_graph':contracts,'full_joined_source_exports':counts,'four_languages':'passed','yield_criterion_removed_from_new_break_records_only':True,'runtime_schema_changes':False,'tests_this_batch':'not_run;data-only mapping,historical135not newrun','native_applied':False,'installed':'not_run','full_history_regression':'not_run','pushed':False})
    for n in ['native-candidate-r1.json','VALIDATION_R1.json']:(Path(__file__).resolve().parent/n).write_bytes((dest/n).read_bytes())
    print(json.dumps({'snapshot':after.snapshot,'properties':5300,'source_exports':counts}))
if __name__=='__main__':main()
