"""Prepare four source-qualified break elongations on existing PA12 states."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT))
from materials_boundaries.database import Database,read_snapshot
from materials_boundaries.material_presentation import render_material_catalog
from jsonschema import Draft202012Validator,FormatChecker
AREA=ROOT/'experimental/polymer-exploration/20261103'
BASE='e0a39a5c4ebc98c622b4dae24e3607636be8a57659525b0345dffbecb8f36d7c'
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
    out=Path(sys.argv[1]).resolve();assert not out.exists() and not out.is_relative_to(ROOT)
    draft=AREA/'pa12-break-elongation-draft-r1';facts=read(draft/'SOURCE_FACTS_R1.json');review=read(draft/'INDEPENDENT_SOURCE_REVIEW_R1.json')
    assert review['decision']=='approved' and review['review_inputs_sha256']==sha(draft/'REVIEW_INPUTS_R1.json')
    asset=facts['source_asset'];assert sha(Path(asset['path_hint']))==asset['sha256']
    before=Database();assert before.snapshot==BASE==facts['baseline_snapshot']
    props=[];states={};sources={}
    for f in facts['rows']:
        old=before.properties[f['base_property_id']];assert old['source_id']==f['source_id'] and old['material_state_id']==f['existing_state_id']
        assert old['quantity'] in ('tensile_strength','youngs_modulus') and f['new_property_id'] not in before.properties
        p=deepcopy(old);p.update(id=f['new_property_id'],version='1.0.0',quantity='tensile_elongation_at_break',quantity_dimension='dimensionless',source_property_label=f['source_property_label'])
        p['reported_value'].update(number=f['number'],value_text=f['number'],unit_code='percent_elongation',unit_text='%')
        p['summary_statistic']='reported_mean';p['uncertainty_status']='reported_standard_deviation'
        p['uncertainty'].update(type='reported_standard_deviation',number=f['uncertainty_number'],value_text=f['uncertainty_number'],unit_code='percent_elongation',unit_text='%',scope='Absolute source SD in elongation percentage points for this selected SLS treatment/exposure group; not relative percentage error, CI or tolerance.',coverage_factor=None,confidence_level=None)
        ev={'source_id':p['source_id'],'url':p['source_document']['url'],'locator':f['locator'],'supports':['reported_value','classification']}
        p['uncertainty']['evidence']=[dict(ev,supports=['uncertainty'])]
        p['uncertainty_note']='Source epsilon Mean '+f['mean']+', Std '+f['sd']+', CV '+f['cv']+'. Mean/SD use original elongation percentage scale; SD absolute percentage points, CV relative percent. All source literals retained without recalculation. Conditional conventional same-group CV=100*SD/mean half-last-place closed rounding intervals overlap; source CV computation unknown, not scientific validation or a derived error estimate.'
        assert p['sample_count']['value']==6 and p['sample_count']['relation']=='exact'
        p['sample_count']['scope']='Source-reported six tensile specimens per selected SLS/postprocess/exposure group, not n18 or six independent printing batches; pooling/extraction order unknown.'
        p['basis_note']='Section3.1 explicitly names epsilon elongation at break; Table7/8 Mean,Std,CV retain printed source literals. Source summary across selected group, not specimen-level paired stress-strain curves; conditional rounding compatibility is not source certification.'
        definition='Source EN ISO527-1 tensile protocol,edition/complianceunknown;Instron5969/maximum50kN,1mm/min crosshead,source testsection L115mm. Source-labelled epsilon elongation at break(%); actual extensometer/reference gauge,strain estimator/engineering-nominal-true-log convention,rupture criterion/selection and pooling order unknown. No percent-to-fraction,stretch ratio,strain-rate or stress/elongation calculation.'
        p['method_definition'].update(type='source_reported_conventional',definition=definition,extraction_window=None,evidence=[dict(ev,supports=['method'])])
        p['conditions']['test_method'].update(text=definition,evidence=[dict(ev,supports=['method','condition'])],notes='115mm source testsection is not verified actual extensometer gauge; standard citation not independent compliance. TestT/RH and post-exposure recovery/conditioning not established.')
        p['evidence']=[ev,dict(ev,supports=['summary_statistic','uncertainty','sample_count','method'])]
        scope='Retained exact primary XML Table7/8 selected four existing SLS epsilon Mean/Std/CV cells;section3.1 break endpoint;sections2.1-2.4 group n,method,exposure,postprocess ordering and permissions;prior all54summary conditional screen retained. No fresh download,PDFvisual or latestrevision/correction/retraction audit.'
        p['source_document'].update(inspected_on='2026-11-03',inspection_scope=scope)
        p['verification']['source_inspection_scope']=scope
        p['scope_note']='Existing EOSPA2200 SLS treatment/exposure state only. Original source percentage break elongation,not certified strain convention/gauge/rupture selection. All source Mean/Std/CV literals retained;absolute SD percentage points versus relative CV percent kept distinct;conditional rounding screen not scientific certification. Source375h/750h chamber exposures distinct from approximate6/12month labels;not fieldlifetime or clinicaldurability. Unknown tensileT/RH,actual gauge/estimator/criterion,post-exposure recovery/conditioning,batches and pairing retained;55Cblacklabel,38Cchamber,23Creferenceinput not tensiletemperature. Table/text postprocess ordering discrepancy retained. No newHPidentity,state,pairedcurve,modulus,energy,toughness,engine input,universal bound or engineeringallowable;deferred dyedReference/750h elongations remain absent.'
        s=deepcopy(before.states[p['material_state_id']]);assert s['id'] not in states
        major,minor,rev=s['version'].split('.');s['version']=f'{major}.{minor}.{int(rev)+1}'
        s['property_ids'].append(p['id']);s['source_scope']+=' Source-labelled percentage break elongation additionally recorded;Mean/SD/CV property-specific,conditional CV compatibility not certification;actual tensile gauge/strain convention/rupture and recovery conditioning unknown.'
        states[s['id']]=s;sources.setdefault(p['source_id'],deepcopy(before.sources[p['source_id']]))
        props.append(p)
    assert len(sources)==1
    for s in sources.values():s['claim_notes'].append('2026-11-03 four existing SLS state break-elongation supplements:dyed375h and dyed+smoothedReference/375h/750h,original epsilon Mean/Std/CV percent strings,n6 per group. SD absolute percentage points,CV relativepercent;conditional rounding compatibility not scientific certification. DyedReference/750h elongation statistics remain deferred;no newstates orHPidentity. Unknown gauge/strain/rupture/recovery retained;chamberhours not fieldmonths,no engine/allowable.')
    data=deepcopy(before.data);data['reference_properties']['records'].extend(props)
    data['materials']['records']=[states.get(s['id'],s) for s in data['materials']['records']];data['sources']['records']=[sources.get(s['id'],s) for s in data['sources']['records']]
    after=Database(data);contracts=after.validate_scientific_contracts()
    assert len(after.properties)==5298 and all(after.properties[k]==p for k,p in before.properties.items())
    assert before.identities==after.identities and before.grades==after.grades and before.states.keys()==after.states.keys() and before.sources.keys()==after.sources.keys()
    for n in data:Draft202012Validator(read(ROOT/'schemas'/(n+'.schema.json')),format_checker=FormatChecker()).validate(data[n])
    out.mkdir(parents=True);(out/'native-tables').mkdir()
    for n,v in data.items():write(out/'native-tables'/(n+'.json'),v)
    write(out/'native-candidate-r1.json',{'baseline_snapshot':BASE,'stage':'not_applied','materials':{'identities':[],'grades':[],'records':list(states.values())},'sources':{'records':list(sources.values())},'reference_properties':{'records':props}})
    sid=next(iter(sources));counts={}
    for phase,db in [('before',before),('after',after)]:
        dest=out/'source-exports'/phase;db.export(dest,source=sid);manifest,rows=read_snapshot(dest)
        assert rows=={r['property']['id']:r for r in db.records(source=sid)};counts[phase]=len(rows)
    assert counts=={'before':9,'after':13}
    for slug in ['dyed_reference','dyed_750h']:assert 'refprop_zakrecki2025_pa2200_sls_'+slug+'_tensile_elongation_at_break' not in after.properties
    for lang in ('en','zh','ja','de'):
        with patch('materials_boundaries.catalog.read_catalog',side_effect=lambda n:data[n]):text=render_material_catalog({'schema_version':'1.0.0','records':props},'reference-properties',lang)
        assert all(f['number'] in text and f['uncertainty_number'] in text and f['cv'] in text for f in facts['rows'])
        assert 'percentage points' in text and 'unknown' in text
        (out/('render-'+lang+'.txt')).write_text(text,encoding='utf-8',newline='\n')
    write(out/'VALIDATION_R1.json',{'baseline_snapshot':BASE,'preview_snapshot':after.snapshot,'properties':5298,'new_properties':4,'all_old_5294_complete_properties_unchanged':True,'new_identity_grade_state_source_objects':0,'modified_states':4,'modified_sources':1,'three_table_schema_format':'passed','current_graph':contracts,'complete_joined_source_export':counts,'four_languages':'passed','two_deferred_existing_state_break_properties':'still_absent','runtime_schema_changes':False,'tests_this_batch':'not_run;data-only mapping,historical135not newrun','native_applied':False,'installed':'not_run','full_history_regression':'not_run','pushed':False})
    for n in ['native-candidate-r1.json','VALIDATION_R1.json']:(Path(__file__).resolve().parent/n).write_bytes((out/n).read_bytes())
    print(json.dumps({'snapshot':after.snapshot,'properties':5298,'source_exports':counts}))
if __name__=='__main__':main()
