"""Map six reviewed source-labelled break elongations on existing states."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT))
from materials_boundaries.database import Database, read_snapshot
from materials_boundaries.material_presentation import render_material_catalog
from jsonschema import Draft202012Validator, FormatChecker
from unittest.mock import patch
AREA=ROOT/'experimental/polymer-exploration/20261103'
BASE='62b47bb10c6ea5ad08905dffa326c29f6dee894f530990c63f6bd3f9d86ecd19'

def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):
    with p.open('x',encoding='utf-8',newline='\n') as f:
        json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')

def main():
    out=Path(sys.argv[1]).resolve()
    assert not out.exists() and not out.is_relative_to(ROOT)
    draft=AREA/'nbr-epoxy-break-elongation-draft-r1'
    facts=read(draft/'SOURCE_FACTS_R1.json')
    approval=read(draft/'INDEPENDENT_SOURCE_REVIEW_R1.json')
    assert approval['decision']=='approved' and approval['review_inputs_sha256']==sha(draft/'REVIEW_INPUTS_R1.json')
    for asset in facts['source_assets']:
        path=Path(asset['path_hint']);assert sha(path)==asset['sha256'] and path.stat().st_size==asset['bytes']
    before=Database();assert before.snapshot==BASE==facts['baseline_snapshot']
    props=[];states={};sources={}
    for fact in facts['rows']:
        old=before.properties[fact['base_property_id']]
        assert old['quantity']=='tensile_strength' and old['source_id']==fact['source_id'] and old['material_state_id']==fact['existing_state_id']
        p=deepcopy(old);nbr=fact['group']=='NBR'
        assert fact['new_property_id'] not in before.properties
        p.update(id=fact['new_property_id'],version='1.0.0',quantity='tensile_elongation_at_break',quantity_dimension='dimensionless',source_property_label=fact['source_property_label'])
        p['reported_value'].update(number=fact['number'],value_text=fact['number'],unit_code='percent_elongation',unit_text='%')
        p['summary_statistic']=fact['summary_statistic']
        p['uncertainty_status']=fact['uncertainty_type']
        assert p['sample_count']['value'] is None
        p['sample_count']['scope']='Specimens contributing to selected break-elongation result; exact per-direction and independent-batch counts unknown.'
        ev={'source_id':p['source_id'],'url':p['source_document']['url'],'locator':fact['locator'],'supports':['reported_value','classification']}
        if nbr:
            p['uncertainty'].update(type='reported_standard_deviation',number='105',value_text='105',unit_code='percent_elongation',unit_text='%',scope='Absolute SD in elongation percentage points for the pooled REF break-elongation result; not relative error, SE, CI or tolerance.',coverage_factor=None,confidence_level=None)
            p['uncertainty']['evidence']=[dict(ev,supports=['uncertainty'])]
            p['uncertainty_note']='451 plus/minus 105% on original source percentage scale. Section3.3 specifically describes average strain at break and overlapping standard deviations; SD is specific to break elongation, not transferred to strength/M100/M200/density. Absolute 105 percentage points, not 105% relative error. Exact n and independent batches unknown.'
            p['basis_note']='Table4 REF strain at break and section3.3 tensile results averaged across all tested orientations. Source mean/SD only, without asserted arithmetic estimator, weighting, per-direction n or pairing; not a single-specimen curve.'
            definition='Source ISO37 Type2 dumbbell tensile specimens from nominal2mm vulcanized sheets; ZwickZ005/5kN at500mm/min crosshead. Two mutually perpendicular orientations pooled by source. Source-labelled strain at break(%); actual reference gauge, strain estimator/convention and rupture/point selection unknown.'
            for issue in p['source_discrepancies']:
                issue['disposition']='Retain this separate source-level strength claim conflict as inherited context, not a discrepancy in the selected REF451% break-elongation cell. Do not repair strength values or infer reinforcement improvement; no source-wide certification.'
        else:
            assert p['uncertainty'] is None
            p['uncertainty_note']='Table7 selected tensile elongation-at-break cell has no dispersion, SD, SE or CI. Central statistic and n unknown; missing uncertainty is not zero.'
            p['basis_note']='PDF Table7 source-labelled tensile elongation at break; scalar copied at table precision without asserting mean, individual specimen or estimator. Central statistic, n and uncertainty not stated.'
            definition='Source GOST11262-2017(ISO527-2:2012) tensile protocol:50ST/TiniusOlsen,10mm/min, specimens milled from4mm cured plate. Figure2 nominal L0=75 plus/minus0.5mm is source schematic geometry, not verified actual extensometer gauge. Source-labelled tensile elongation at break(%); strain estimator/convention, reference gauge actually used and rupture/point selection unknown.'
            p['source_discrepancies'].append({'description':'PDF abstract reports a maximum tensile elongation at break up to6.22%, whereas Table7 selected PNA-BPF-3 cell prints6.2%.','disposition':'Preserve each selected Table7 cell at its printed precision; no padding to6.22, inferred source correction or claim that the precision difference proves conflicting experiments.','evidence':[dict(ev,locator='PDF p.1 abstract maximum tensile elongation; p.16 Table7 PNA-BPF-3 tensile elongation at break',supports=['source_discrepancy'])]})
        definition+=' No percent-to-fraction, stretch-ratio or strain-rate conversion; standard citation does not establish independent compliance.'
        p['method_definition'].update(type='source_reported_conventional',definition=definition,extraction_window=None,evidence=[dict(ev,supports=['method','condition'])])
        p['conditions']['test_method'].update(text=definition,evidence=[dict(ev,supports=['method','condition'])],notes='Existing source-specific tensile protocol only; strain estimator, actual gauge, fracture algorithm, temperature/RH and conditioning remain unconfirmed. Preparation temperatures are not test conditions.')
        p['evidence']=[ev,dict(ev,supports=['method','condition'])]
        if nbr:p['evidence'].append(dict(ev,supports=['summary_statistic','uncertainty']))
        scope=('Retained exact primary XML permissions,Table4 REF strain-at-break,sections2.2 and3.3 method,pooled mean and break-specific SD.' if nbr else 'Registered retained publisher PDF hash matched; retained page images1,6,16 actually visually checked this round for CC-BY4.0,method/Figure2,Table7 selected five tensile-break-elongation cells. Existing preparation/identity conflicts inherited without repair.')+' No fresh download or latest revision/correction/retraction audit; latest status unknown.'
        p['source_document'].update(inspected_on='2026-11-03',inspection_scope=scope)
        p['verification']['source_inspection_scope']=scope
        p['scope_note']='Existing selected source formulation and tensile specimen state only; percentage break elongation, not verified engineering/nominal/true/log strain or elongation ratio. Unknown environment/conditioning, estimator/gauge/rupture/selection and independent batches preserved. No paired curves, endpoint ordering, modulus, toughness,energy,engine input,universal bound or engineering allowable. '+('Unfilled nonfoamed REF has fixed additives,not raw NBR; orientation pooling not isotropy,n2 or per-axis output; break SD does not fill other properties.' if nbr else 'Same4mm tensile plate,not3.6mm flexural state. Nominal recipe/alkali conflicts inherited; central statistic,n,dispersion unknown; Table7 precision retained,abstract not used to pad. DDS cure180C/8h is not testing/conditioning; DGEBA/DGEBF/PNA-BPF-S/flexural elongation excluded.')
        s=deepcopy(before.states[p['material_state_id']]);assert s['id'] not in states
        major,minor,rev=s['version'].split('.');s['version']=f'{major}.{minor}.{int(rev)+1}'
        s['property_ids'].append(p['id']);s['source_scope']+=' Source-labelled tensile break elongation separately recorded on original percentage scale; statistics property-specific, strain estimator/gauge/fracture selection unknown.'
        states[s['id']]=s;sources.setdefault(p['source_id'],deepcopy(before.sources[p['source_id']]))
        props.append(p)
    for source in sources.values():
        source['claim_notes'].append('2026-11-03 existing-state break-elongation supplement: NBR REF451+/-105% source pooled mean/break-specific SD,nunknown; five PNA-BPF tensile Table7 cells at original precision,central statistic/n/uncertaintyunknown. No other identity,state or method inference; unknown strain convention/gauge/rupture retained. No SD transfer to older properties,no engine or source-wide certification.')
    data=deepcopy(before.data);data['reference_properties']['records'].extend(props)
    data['materials']['records']=[states.get(x['id'],x) for x in data['materials']['records']]
    data['sources']['records']=[sources.get(x['id'],x) for x in data['sources']['records']]
    after=Database(data);contracts=after.validate_scientific_contracts()
    assert len(after.properties)==5294 and all(after.properties[k]==v for k,v in before.properties.items())
    assert before.identities==after.identities and before.grades==after.grades and before.states.keys()==after.states.keys() and before.sources.keys()==after.sources.keys()
    for name in data:Draft202012Validator(read(ROOT/'schemas'/(name+'.schema.json')),format_checker=FormatChecker()).validate(data[name])
    out.mkdir(parents=True);(out/'native-tables').mkdir()
    for name,value in data.items():write(out/'native-tables'/(name+'.json'),value)
    write(out/'native-candidate-r1.json',{'baseline_snapshot':BASE,'stage':'not_applied','materials':{'identities':[],'grades':[],'records':list(states.values())},'sources':{'records':list(sources.values())},'reference_properties':{'records':props}})
    counts={}
    for sid in sources:
        counts[sid]={}
        for phase,db in [('before',before),('after',after)]:
            dest=out/'source-exports'/sid/phase;db.export(dest,source=sid)
            manifest,rows=read_snapshot(dest);assert rows=={x['property']['id']:x for x in db.records(source=sid)}
            counts[sid][phase]=len(rows)
    for lang in ('en','zh','ja','de'):
        with patch('materials_boundaries.catalog.read_catalog',side_effect=lambda n:data[n]):
            text=render_material_catalog({'schema_version':'1.0.0','records':props},'reference-properties',lang)
        assert all(p['reported_value']['number'] in text for p in props) and '105' in text and 'unknown' in text
        (out/('render-'+lang+'.txt')).write_text(text,encoding='utf-8',newline='\n')
    write(out/'VALIDATION_R1.json',{'baseline_snapshot':BASE,'preview_snapshot':after.snapshot,'properties':5294,'new_properties':6,'all_old_5288_complete_properties_unchanged':True,'new_identity_grade_state_source_objects':0,'modified_states':6,'modified_sources':2,'three_table_schema_format':'passed','current_graph':contracts,'complete_joined_exports':counts,'four_language_rendering':'passed','runtime_schema_implementation_changes':False,'tests_this_batch':'not_run; data-only mapping; unchanged135 successful scoped test evidence is historical,not a new run','full_history_regression':'not_run','native_applied':False,'installed':'not_run','pushed':False})
    for name in ['native-candidate-r1.json','VALIDATION_R1.json']:(Path(__file__).resolve().parent/name).write_bytes((out/name).read_bytes())
    print(json.dumps({'snapshot':after.snapshot,'properties':len(after.properties),'exports':counts}))

if __name__=='__main__':main()
