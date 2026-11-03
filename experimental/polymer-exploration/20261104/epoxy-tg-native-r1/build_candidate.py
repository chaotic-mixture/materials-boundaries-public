"""Prepare source-qualified DSC Tg records; never change native tables."""
from copy import deepcopy
import hashlib,json,sys
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT))
from jsonschema import Draft202012Validator,FormatChecker
from materials_boundaries.database import Database,read_snapshot
from materials_boundaries.material_presentation import render_material_catalog
AREA=ROOT/'experimental/polymer-exploration/20261104'
OUT=Path(__file__).resolve().parent
BASE='a5c0c67e51e471294363c9d30db9af82a73f1dd619e1d1a4ecb5c2a276e42ea1'
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,value):
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
    dest=Path(sys.argv[1]).resolve();assert not dest.exists() and not dest.is_relative_to(ROOT)
    proposal=AREA/'epoxy-tg-source-contract-r1';review=read(proposal/'INDEPENDENT_SOURCE_REVIEW_R1.json')
    assert review['decision']=='approved' and review['review_inputs_sha256']==sha(proposal/'REVIEW_INPUTS_R1.json')
    manifest=read(proposal/'REVIEW_INPUTS_R1.json');archive=read(proposal/'BASELINE_CONTRACT_BINDING_R1.json')
    for n,d in manifest['repo_files_sha256'].items():
        if sha(ROOT/n)!=d:
            old=archive[n];assert sha(ROOT/old['archive_path'])==old['sha256']==d,n
    for n,d in manifest['external_files_sha256'].items():assert sha(Path(n))==d,n
    facts=read(proposal/'SOURCE_FACTS_R1.json');before=Database();assert before.snapshot==BASE
    assert all(before.states[s['id']]==s for s in read(proposal/'BASE_STATES_R1.json'))
    assert all(before.properties[p['id']]==p for p in read(proposal/'BASE_PROPERTIES_R1.json'))
    source=facts['source_id'];states=[];properties=[]
    methodloc='Retained publisher PDF p6 section2.5.4 Differential Scanning Calorimetry'
    preploc='Retained publisher PDF p5 section2.4 common DDS preparation and180C8h cure'
    for row in facts['rows']:
        assert row['new_state_id'] not in before.states and row['new_property_id'] not in before.properties
        prop=deepcopy(before.properties[row['base_property_id']]);url=prop['source_document']['url']
        assert len(prop['source_discrepancies'])==3
        def ev(loc,tags):return dict(source_id=source,url=url,locator=loc,supports=list(tags))
        def unknown(note):return dict(status='not_reported_in_inspected_source',text=None,evidence=[],notes=note)
        def na(note):return dict(status='not_applicable',text=None,evidence=[],notes=note)
        def fact(text,loc,note=None,tags=('condition',)):
            return dict(status='reported',text=text,evidence=[ev(loc,tags)],notes=note)
        loc='Retained publisher PDF p16 Table7 '+row['source_label']+' Tg(°C) column'
        description=('Source-reported DSC glass transition temperature: DSC204F1Phoenix(Netzsch), '
            'GOST R55135-2012(ISO11357-2:1999) as cited; dynamic heating40–270°C at10°C/min, '
            'nitrogen60–100mL/min, samplemass5–10mg. Tg onset/midpoint/inflection criterion, '
            'scan cycle, preceding heating/cooling history and baseline/software unknown.')
        prop.update(id=row['new_property_id'],version='1.0.0',material_state_id=row['new_state_id'],quantity='glass_transition_temperature',
            quantity_dimension='temperature',source_property_label='Tg (°C)',summary_statistic='not_stated',reporting_basis='not_stated',
            uncertainty=None,uncertainty_status='not_reported_in_inspected_source')
        prop['reported_value'].update(number=row['table7_number'],value_text=row['table7_number'],unit_code='degC',unit_text='°C')
        prop['basis_note']='Selected Table7 literal only; central estimator,n and numerical dispersion unknown. Table174.7 versus abstract maximum174.5°C unresolved; table selection does not certify priority or the true experimental value.'
        prop['conditions']={
            'temperature':fact('Nonisothermal dynamic DSC heating scan40–270°C',methodloc,'Scan range only,not ambient,cure temperature,Tg itself or the actual logged profile.'),
            'test_standard':fact('GOST R55135-2012(ISO11357-2:1999),as cited',methodloc,'Source citation only; no independent standards-compliance certification.'),
            'test_method':fact(description,methodloc,'Tg is not melting,decomposition,cure or service-temperature limit.'),
            'direction':na('No mechanical loading direction assigned to this DSC result; sample orientation and isotropy are not established.'),
            'conditioning':unknown('DSC-specific postcure conditioning,humidity,moisture equilibrium,storage and prior thermal history unknown.'),
            'loading_rate':na('Mechanical loading rate is not applicable;10°C/min is a thermal heating rate,recorded separately.'),
            'additional_conditions':[
                {'name':'thermal_heating_rate','fact':fact('10°C/min',methodloc,'Source nominal rate,not mechanical strain/crosshead rate or verified actual thermal profile.')},
                {'name':'purge_atmosphere_and_flow','fact':fact('Nitrogen60–100mL/min',methodloc,'Source flow range,not verified instantaneous flow or gas purity.')},
                {'name':'sample_mass_range','fact':fact('5–10mg',methodloc,'Mass range only;exact per-sample mass unknown and not replicate count.')},
                {'name':'calibration_statement','fact':fact('Temperature/enthalpy calibration using gallium,indium,tin,bismuth,zinc',methodloc,'Source statement only;current certificate,uncertainty,accuracy and calibration execution not verified.')},
                {'name':'Tg_extraction_criterion','fact':unknown('Onset,midpoint,inflection or other Tg criterion unknown;no algorithm inferred from standard citation.')},
                {'name':'scan_cycle_and_thermal_history','fact':unknown('First/second/later heating,cycle count,cooling rate,preceding thermal history and actual logged profile unknown.')},
                {'name':'pan_geometry_and_reduction','fact':unknown('Pan/lid material and geometry,exact sample mass,baseline and reduction software unknown.')},
                {'name':'test_relative_humidity','fact':unknown('DSC sample humidity/moisture context unknown;nitrogen purge does not establish dry-equilibrium conditioning.')},
            ]}
        prop['uncertainty_note']='Inspected DSC method and Table7 do not define central aggregation,n,batches or numeric SD/SE/CI. Unknown does not mean zero scatter. Abstract/table discrepancy is not measurement uncertainty or an interval.'
        prop['sample_count']=dict(value=None,relation='not_reported',scope='Selected DSC formulation/test;specimen and independent batch counts unknown.',
            source_statement='5–10mg is sample mass,not n;five formulations and other-method specimen counts are not DSC replication.',evidence=[])
        prop['method_definition'].update(definition=description,extraction_window=None,evidence=[ev(methodloc,('method','classification'))])
        prop['source_discrepancies'].extend([
            dict(description='Abstract p1 states maximum Tg174.5°C whereas Table7 PNA-BPF-3 reports174.7°C;reason unresolved.',
                disposition='Retain each Table7 literal,including174.7,as source-qualified context. No priority/true-value adjudication,typo repair,averaging,uncertainty interval or duplicate independent experiment.',
                evidence=[ev('Retained PDF p1 abstract and p16 Table7',('source_discrepancy',))]),
            dict(description='The Tg discussion on p19 cites Table8; Tg values are in Table7 and Table8 contains flexural results.',
                disposition='Preserve the source cross-reference issue without relocating,correcting or independently certifying the values.',
                evidence=[ev('Retained PDF p16 Table7 and p19 Tg paragraph/Table8',('source_discrepancy',))])])
        scope='Retained same publisher PDF visually checked pp1,5,6,16,19:CCBY4,common DDS preparation,DSC method,Table7 Tg literals,abstract maximum and incorrect Table8 cross-reference. No fresh PDF/latestrevision/supplementary-information completeness,rawdata or independent standards/scientific certification.'
        prop['source_document'].update(inspected_on='2026-11-04',inspection_scope=scope);prop['verification']['source_inspection_scope']=scope
        prop['scope_note']='Source-qualified '+row['source_label']+' Table7 Tg='+row['table7_number']+'°C only. Unknown extraction criterion,scan cycle,prior thermal history,conditioning,n and dispersion prevent matched-condition claims. Abstract174.5 vsTable174.7 and incorrectTable8 reference unresolved;prior feed/mole/alkali issues retained. No tensile/bending/impact specimen geometry transferred. Not a melting,cure or service temperature,allowable,universal bound or engine input;no automatic conversion.'
        prop['evidence']=[ev(loc,('reported_value','classification')),ev(methodloc,('method','condition'))]
        state=deepcopy(before.states[row['base_state_id']])
        names={lang:row['source_label']+suffix for lang,suffix in {'en':', DDS-cured DSC sample; thermal history unknown','zh':'，DDS固化DSC样品；热历史未知','ja':'、DDS硬化DSC試料；熱履歴不明','de':', DDS-gehärtete DSC-Probe; thermische Vorgeschichte unbekannt'}.items()}
        state.update(id=row['new_state_id'],version='1.0.0',name=names['en'],names=names,aliases=[],property_ids=[prop['id']])
        state['state']['product_form']=fact('DDS-cured DSC sample,source mass range5–10mg',methodloc,'No mechanical-bar geometry inherited;exact sample mass and pan/sample shape unknown.',('state',))
        state['state']['conditioning']=unknown('DSC-specific postcure storage,RH,moisture and prior heating/cooling history unknown.')
        state['state']['porosity']=unknown('DSC sample porosity unknown;degassing does not establish zero porosity.')
        state['state']['orientation']=unknown('DSC sample orientation and isotropy unknown;no mechanical loading axis assigned.')
        state['source_scope']='Separate DSC state under existing '+row['source_label']+' identity and common source DDS preparation/180°C8h cure only. No tensile,bending or impact bar geometry,mechanical rate,span,notch or machining route inherited. Actual sample/pan geometry,conditioning and prior thermal history unknown. Existing nominalfeed/mole/alkali contradictions retained;no old property moved.'
        state['evidence']=[ev(methodloc,('state',)),ev(preploc,('state',))]
        states.append(state);properties.append(prop)
    data=deepcopy(before.data);data['materials']['records'].extend(states);data['reference_properties']['records'].extend(properties)
    src=deepcopy(before.sources[source]);src['claim_notes'].append('2026-11-04 source-qualified Table7 DSC Tg supplement for five existing PNA-BPF identities on separate DSC states:160.0/153.0/174.7/169.3/156.7°C. Abstract maximum174.5 vsTable174.7 and p19 erroneousTable8 reference unresolved;no true-value priority,repair,average or uncertainty conversion. Source40–270°C,10°C/min,N2 60–100mL/min,5–10mg;criterion,cycle,prior history,conditioning,n/dispersion unknown. Common DDS cure only,no mechanical specimen geometry or engine/engineering/service-temperature conversion;prior recipe issues retained.')
    data['sources']['records']=[src if s['id']==source else s for s in data['sources']['records']]
    after=Database(data);contracts=after.validate_scientific_contracts()
    assert len(after.properties)==5332 and len(after.states)==5217
    assert all(after.properties[k]==v for k,v in before.properties.items()) and all(after.states[k]==v for k,v in before.states.items())
    assert after.identities==before.identities and after.grades==before.grades and set(after.sources)==set(before.sources)
    assert all(after.sources[k]==v for k,v in before.sources.items() if k!=source)
    restored=deepcopy(src);restored['claim_notes'].pop();assert restored==before.sources[source]
    for n in data:Draft202012Validator(read(ROOT/'schemas'/(n+'.schema.json')),format_checker=FormatChecker()).validate(data[n])
    dest.mkdir(parents=True);(dest/'native-tables').mkdir()
    for n,v in data.items():write(dest/'native-tables'/(n+'.json'),v)
    write(dest/'native-candidate-r1.json',dict(baseline_snapshot=BASE,stage='not_applied',materials=dict(identities=[],grades=[],records=states),reference_properties=dict(records=properties),sources=dict(records=[src])))
    write(dest/'MAPPING_FACTS_R1.json',dict(rows=facts['rows'],property_records={p['id']:p for p in properties},state_records={s['id']:s for s in states},source_record=src))
    counts={}
    for phase,db in [('before',before),('after',after)]:
        export=dest/'source-exports'/phase;db.export(export,source=source);_,joined=read_snapshot(export)
        assert joined=={r['property']['id']:r for r in db.records(source=source)};counts[phase]=len(joined)
    assert counts=={'before':35,'after':40}
    for language in ('en','zh','ja','de'):
        with patch('materials_boundaries.catalog.read_catalog',side_effect=lambda n:data[n]):
            text=render_material_catalog({'schema_version':'1.0.0','records':properties},'reference-properties',language)
        assert all(row['table7_number'] in text for row in facts['rows'])
        assert all(t in text for t in ('°C','174.5','174.7','criterion','unknown','Table8'))
        (dest/('render-'+language+'.txt')).write_text(text,encoding='utf-8',newline='\n')
    write(dest/'VALIDATION_R26.json',dict(baseline_snapshot=BASE,preview_snapshot=after.snapshot,properties=5332,states=5217,new_properties=5,new_states=5,
        new_identities_grades_sources=0,all_old5327_properties_and5212_states_complete_unchanged=True,source_change='One appended claim note only.',
        schema_format='passed',current_graph=contracts,complete_source_export=counts,four_languages='passed',native_applied=False,installed='not_run',full_history_regression='not_run',pushed=False))
    for n in ('native-candidate-r1.json','MAPPING_FACTS_R1.json','VALIDATION_R26.json'):(OUT/n).write_bytes((dest/n).read_bytes())
    print(json.dumps(dict(snapshot=after.snapshot,properties=5332,states=5217,source_exports=counts)))
if __name__=='__main__':main()
