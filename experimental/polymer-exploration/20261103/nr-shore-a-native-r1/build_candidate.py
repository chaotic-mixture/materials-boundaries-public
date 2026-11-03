"""Prepare a source-nominal 3mm NR Shore A state without rewriting 1mm data."""
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
BASE='35c10b8bcde2e5d0c5c1266dc98e428962683009d0a4d4511ba3f2f301cf6153'
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
    dest=Path(sys.argv[1]).resolve();assert not dest.exists() and not dest.is_relative_to(ROOT)
    proposal=AREA/'nr-shore-a-source-contract-proposal-r1';facts=read(proposal/'SOURCE_FACTS_R1.json');review=read(proposal/'INDEPENDENT_SOURCE_CONTRACT_REVIEW_R1.json')
    assert review['decision']=='approved' and review['review_inputs_sha256']==sha(proposal/'REVIEW_INPUTS_R1.json')
    archive=read(proposal/'BASELINE_CONTRACT_BINDING_R1.json')
    for name,digest in read(proposal/'REVIEW_INPUTS_R1.json')['repo_files_sha256'].items():
        path=ROOT/name
        if sha(path)!=digest:
            old=ROOT/archive[name]['archive_path'];assert sha(old)==digest==archive[name]['sha256']
    asset=facts['source_asset'];assert sha(Path(asset['path_hint']))==asset['sha256']
    before=Database();assert before.snapshot==BASE==facts['baseline_local_snapshot']
    oldstate=before.states[facts['existing_1mm_state_id']];source='bianchi_2025_nr_nanoclay'
    p=deepcopy(before.properties['refprop_smr10_bianchi2025_nr_tensile_stress_at_break'])
    pid='refprop_smr10_bianchi2025_nr_shore_a_hardness';sid='state_smr10_bianchi2025_nr_shore_a_nominal_3mm';assert pid not in before.properties and sid not in before.states
    url=p['source_document']['url']
    def ev(locator,supports):return {'source_id':source,'url':url,'locator':locator,'supports':supports}
    def unknown(note):return {'status':'not_reported_in_inspected_source','text':None,'evidence':[],'notes':note}
    def fact(text,locator,note=None,tag='condition'):return {'status':'reported','text':text,'evidence':[ev(locator,[tag])],'notes':note}
    methodloc='Retained XML section3.3.4 first hardness paragraph;Table4 NR row x Shore A'
    statloc='Retained XML section3.3.4 hardness paragraph five specimens and final mechanical mean plus/minus standard-deviation statement;Table4 NR Shore A cell'
    geomloc='Retained XML section3.2 general120x120x1mm sheets versus section3.3.4 hardness square15mm wide,3mm thick'
    definition='Source-labelled Shore A durometer hardness at25C, after10s pressing an indenter; source load setting488g retained without conversion to force. Source instrument spelling Hilderbrand Durometer, model/calibration unknown; ASTM D2240 cited without edition or independent compliance. Nominal square15mm wide,3mm thick; its preparation/stacking/cure route is unreported and differs from general1mm sheet description. RH, conditioning, approach/loading rate and indentation face/processing axis remain unknown.'
    p.update(id=pid,version='1.0.0',material_state_id=sid,quantity='shore_a_hardness',quantity_dimension='dimensionless',source_property_label='Shore A')
    p['reported_value'].update(number='38.0',value_text='38.0',unit_text='Shore A',unit_code='shore_a_scale')
    p['uncertainty'].update(type='reported_standard_deviation',number='0.8',value_text='0.8',unit_text='Shore A',unit_code='shore_a_scale',scope='Source SD in absolute Shore A scale points for this nominal specimen group, not relative percent, pressure, confidence interval or a material bound.',coverage_factor=None,confidence_level=None,evidence=[ev(statloc,['uncertainty'])])
    p.update(summary_statistic='reported_mean',uncertainty_status='reported_standard_deviation',reporting_basis='reported_summary',basis_note='Source Table4 NR Shore A scalar and section3.3.4 common mechanical mean/SD statement. Reported group mean only, no calibrated bulk-grade hardness, sample-level curve or constitutive conversion.')
    p['uncertainty_note']='38.0 plus/minus0.8 Shore A: source-reported mean and SD, absolute scale points, not percent or MPa. Five specimens are not five independent batches; indentation counts per specimen, calibration and stacking are unknown.'
    p['sample_count']={'value':5,'relation':'exact','scope':'Five source-reported hardness specimens per formulation; not independent batches or a known count of repeated indentations.','source_statement':'Five specimens were tested for each formulation in the hardness paragraph.','evidence':[ev(statloc,['sample_count'])]}
    p['conditions']={'temperature':fact('25°C',methodloc,'Hardness temperature only; not transferred to quasi-static tensile properties.'),'test_standard':fact('ASTM D2240; edition not stated',methodloc,'Source citation only; independent compliance not verified.'),'test_method':fact(definition,methodloc,'Nominal source geometry; no thickness repair, layer inference or actual-load certification.'),'direction':unknown('Indentation face and orientation relative to processing axes are not established; no isotropy inference.'),'conditioning':unknown('Hardness-specific post-cure storage, RH and equilibration are not stated;25C testing and10s indentation do not supply conditioning.'),'loading_rate':unknown('Approach/application/loading rate is not stated;10s duration is not a rate, and tensile500mm/min is not transferred.'),'additional_conditions':[{'name':'reported_contact_time','fact':fact('10s after pressing the indenter',methodloc,'Exact contact/timer trigger unverified.')},{'name':'source_reported_load_setting','fact':fact('488g',methodloc,'As printed; not converted toN or asserted as calibrated normal force.')},{'name':'test_relative_humidity','fact':unknown('Hardness-test relative humidity is not stated.')} ]}
    p['method_definition'].update(type='source_reported_conventional',definition=definition,extraction_window=None,evidence=[ev(methodloc,['method','condition'])])
    p['source_discrepancies']=[{'description':'General sample preparation states120x120x1mm sheets, while the hardness protocol states3mm-thick square specimens. The source does not reconcile the specific3mm preparation route.','disposition':'Retain a separate source-nominal3mm hardness state. Do not attach this result to1mm tensile/density state, infer stacking/layers, replace3mm with6mm, or certify geometry/standard compliance.','evidence':[ev(geomloc,['source_discrepancy','state'])]}]
    p['evidence']=[ev(methodloc,['reported_value','classification','method','condition']),ev(statloc,['summary_statistic','uncertainty','sample_count'])]
    scope='Retained exact primary XML Table4 NR Shore A38.0+/-0.8,section3.3.4 hardness protocol/n5/common mechanical mean-SD,section3.2 geometry discrepancy,Table8 NR formulation and permissions. No new PDF visual,calibration,raw-data or latest-revision/correction/retraction audit.'
    p['source_document'].update(inspected_on='2026-11-03',inspection_scope=scope);p['verification']['source_inspection_scope']=scope
    p['scope_note']='Source-qualified NR vulcanizate with curatives, no nanoclay, not raw/pure SMR10. Empirical Shore A reading on source-nominal3mm specimens only; specific preparation/cure/stacking,actual thickness,calibration,face/RH/conditioning and independent batches unverified. General1mm sheet preparation is not confirmed3mm manufacture;488g is source setting,not converted force. Scale domain0..100 does not certify edge reliability or method compliance. No cross-scale,Young-modulus,stress,energy,engine,universal-bound or engineering-allowable inference. NR break-strain unit ambiguity remains deferred.'
    state=deepcopy(oldstate);state.update(id=sid,version='1.0.0',name='Study NR, source-nominal3mm Shore A specimens',names={'en':'Study NR, source-nominal3mm Shore A specimens','zh':'研究NR，源称名义3mm邵氏A试样','ja':'研究NR、原文公称3mmショアA試験片','de':'Studien-NR, nominelle3mm-Proben für Shore A laut Quelle'},aliases=[],source_designation='NR; source-nominal square15mm wide and3mm thick hardness specimens',property_ids=[pid])
    state['state']['product_form']=fact('Source-nominal square hardness specimens,15mm wide and3mm thick',methodloc,'General1mm sheet statement differs; actual preparation/stacking unresolved.','state')
    state['state']['processing']=unknown('Specific3mm specimen preparation path is not stated. General1mm compound-sheet process does not establish stacking or3mm manufacture.')
    state['state']['temper_or_heat_treatment']=unknown('Specific3mm specimen cure route/time is not established; do not upgrade general1mm preparation120C/3bar into confirmed3mm history.')
    state['state']['conditioning']=unknown('Hardness-specific storage/conditioning/RH/equilibration is not stated; test25C and10s contact are not conditioning.')
    for name in ('composition_or_purity','reinforcement'):
        state['state'][name]['evidence']=[ev('Retained XML section3.1 SMR10 and Table8 NR reference recipe;no nanoclay',['state','material_identity','grade'])]
    state['state']['orientation']=unknown('Source does not establish indentation face or its relation to processing axes; no isotropy inference.')
    state['source_scope']='Separate source-nominal3mm hardness specimen state under the same study NR formulation/grade. General1mm sheet preparation and3mm hardness geometry remain unreconciled; route,cure,stacking,actual thickness and conditioning not confirmed. Hardness mean/SD/n5 and25C/10s/488g are property-specific source reports,not independent certification. No old tensile/density property is moved or reinterpreted.'
    state['evidence']=[ev(methodloc,['state']),ev(geomloc,['state'])]
    src=deepcopy(before.sources[source]);src['claim_notes'].append('2026-11-03 separate source-nominal3mm NR Shore A state and38.0+/-0.8 mean/SD/n5 reference.25C,10s,488g source setting preserved. General1mm sheet description does not establish3mm preparation/cure/stacking; no thickness repair or compliance/calibration certification. Empirical scale only,no modulus/cross-scale/engine conversion. NR break-strain unit issue remains deferred.')
    data=deepcopy(before.data);data['materials']['records'].append(state);data['reference_properties']['records'].append(p);data['sources']['records']=[src if s['id']==source else s for s in data['sources']['records']]
    after=Database(data);contracts=after.validate_scientific_contracts()
    assert len(after.properties)==5301 and len(after.states)==5196
    assert all(after.properties[k]==v for k,v in before.properties.items()) and all(after.states[k]==v for k,v in before.states.items())
    assert after.identities==before.identities and after.grades==before.grades and after.sources.keys()==before.sources.keys()
    assert not list(after.records(source=source,quantity='tensile_elongation_at_break'))
    for n in data:Draft202012Validator(read(ROOT/'schemas'/(n+'.schema.json')),format_checker=FormatChecker()).validate(data[n])
    dest.mkdir(parents=True);(dest/'native-tables').mkdir()
    for n,v in data.items():write(dest/'native-tables'/(n+'.json'),v)
    write(dest/'native-candidate-r1.json',{'baseline_snapshot':BASE,'stage':'not_applied','materials':{'identities':[],'grades':[],'records':[state]},'reference_properties':{'records':[p]},'sources':{'records':[src]}})
    counts={}
    for phase,db in [('before',before),('after',after)]:
        target=dest/'source-exports'/phase;db.export(target,source=source);manifest,rows=read_snapshot(target);assert rows=={r['property']['id']:r for r in db.records(source=source)};counts[phase]=len(rows)
    assert counts=={'before':11,'after':12}
    for lang in ('en','zh','ja','de'):
        with patch('materials_boundaries.catalog.read_catalog',side_effect=lambda n:data[n]):text=render_material_catalog({'schema_version':'1.0.0','records':[p]},'reference-properties',lang)
        assert '38.0' in text and '0.8' in text and 'Shore A' in text and '3mm' in text
        (dest/('render-'+lang+'.txt')).write_text(text,encoding='utf-8',newline='\n')
    write(dest/'VALIDATION_R20.json',{'baseline_snapshot':BASE,'preview_snapshot':after.snapshot,'properties':5301,'states':5196,'new_properties':1,'new_states':1,'new_identities_grades_sources':0,'old5300properties_and5195states_complete_unchanged':True,'source_change':'One appended claim_note only.','schema_format':'passed','current_graph':contracts,'complete_source_export':counts,'four_languages':'passed','native_applied':False,'installed':'not_run','full_history_regression':'not_run','pushed':False})
    for n in ['native-candidate-r1.json','VALIDATION_R20.json']:(Path(__file__).resolve().parent/n).write_bytes((dest/n).read_bytes())
    print(json.dumps({'snapshot':after.snapshot,'properties':5301,'states':5196,'exports':counts}))
if __name__=='__main__':main()
