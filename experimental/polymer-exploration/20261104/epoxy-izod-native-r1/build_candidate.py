"""Prepare five explicitly source-qualified Izod references without native writes."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT))
from jsonschema import Draft202012Validator,FormatChecker
from materials_boundaries.database import Database,read_snapshot
from materials_boundaries.material_presentation import render_material_catalog

AREA=ROOT/'experimental/polymer-exploration/20261104'
OUT=Path(__file__).resolve().parent
BASE='93165ce378158742ee6c4fc1374f5007ba0de1c81ac01b07c93b3be7c26deec4'


def read(path):return json.loads(path.read_bytes())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path,value):
    with path.open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2);stream.write('\n')


def main():
    dest=Path(sys.argv[1]).resolve();assert not dest.exists() and not dest.is_relative_to(ROOT)
    proposal=AREA/'epoxy-izod-source-contract-r1'
    review=read(proposal/'INDEPENDENT_SOURCE_REVIEW_R1.json')
    assert review['decision']=='approved' and review['review_inputs_sha256']==sha(proposal/'REVIEW_INPUTS_R1.json')
    assert review['adjudications']['PNA_BPF_5']['decision']=='conditional_catalog_only_table7_literal'
    manifest=read(proposal/'REVIEW_INPUTS_R1.json');archive=read(proposal/'BASELINE_CONTRACT_BINDING_R1.json')
    for name,digest in manifest['repo_files_sha256'].items():
        if sha(ROOT/name)!=digest:
            old=archive[name];assert sha(ROOT/old['archive_path'])==old['sha256']==digest,name
    for name,digest in manifest['external_files_sha256'].items():assert sha(Path(name))==digest,name
    facts=read(proposal/'SOURCE_FACTS_R1.json');before=Database();assert before.snapshot==BASE
    assert all(before.states[s['id']]==s for s in read(proposal/'BASE_STATES_R1.json'))
    assert all(before.properties[p['id']]==p for p in read(proposal/'BASE_PROPERTIES_R1.json'))
    source=facts['source_id'];states=[];properties=[]
    methodloc='Retained publisherPDFp6 section2.5.3 Izod Impact Test'
    preploc='Retained publisherPDFp5 section2.4 commonDDS preparation and180C8hcure'
    for row in facts['rows']:
        assert row['new_state_id'] not in before.states and row['new_property_id'] not in before.properties
        prop=deepcopy(before.properties[row['base_property_id']]);url=prop['source_document']['url']
        def ev(locator,tags):return dict(source_id=source,url=url,locator=locator,supports=list(tags))
        def unknown(note):return dict(status='not_reported_in_inspected_source',text=None,evidence=[],notes=note)
        def fact(text,locator,note=None,tags=('condition',)):
            return dict(status='reported',text=text,evidence=[ev(locator,tags)],notes=note)
        loc='Retained publisherPDFp16 Table7 '+row['source_label']+' Izod Impact Strength(kJ/m²)'
        description=('Author-labelled Izodimpact strength,Izod-Charpy K1053(ATSFAAR),GOST19109-2017(ISO180:2000) as cited;nominal80x9.8x3.6mm bars. '
            'Notch status,type/radius/remainingligament,impactvelocity,pendulumcapacity/calibration/corrections,actualarea/normalization formula and breakmode unknown. '
            'Machine name does not establishCharpymethod;no bendingmilling/rate/span or DSCconditions transferred.')
        prop.update(id=row['new_property_id'],version='1.0.0',material_state_id=row['new_state_id'],quantity='izod_impact_strength',
            quantity_dimension='energy_per_area',source_property_label='Izod Impact Strength (kJ/m²)',summary_statistic='not_stated',reporting_basis='not_stated',
            uncertainty=None,uncertainty_status='not_reported_in_inspected_source')
        prop['reported_value'].update(number=row['table7_number'],value_text=row['table7_number'],unit_code='kJ/m^2',unit_text='kJ/m²')
        prop['basis_note']='Exact selected Table7 literal,not corrected or extended fromFigure10/abstract. Central estimator,n/batches and numeric uncertainty unknown. Source-qualified transcription does not establish the true experimental value or table superiority.'
        prop['conditions']={
            'temperature':unknown('Izod test temperature unknown;180C cure and DSCtemperatures are not impact ambient.'),
            'test_standard':fact('GOST19109-2017(ISO180:2000),source describesmodifiedISO180',methodloc,'Source citation only;notch/method subdesignation and independent compliance unknown.'),
            'test_method':fact(description,methodloc,'Source Izodlabel,not Charpy or an intrinsic fracture-energy constant.'),
            'direction':unknown('Impactbar orientation,notch/strikingface and processing-axis relationship unknown;no isotropy assigned.'),
            'conditioning':unknown('Impact-specific postcure conditioning,humidity,moisture equilibrium and storage duration unknown.'),
            'loading_rate':unknown('Impactvelocity,releaseangle and pendulum kinetic setting unknown. Bending0.85mm/min and tensile10mm/min are not transferred.'),
            'additional_conditions':[
                {'name':'notch_status','fact':unknown('Notched/unnotched mode unknown;do not choose a mode from ISO180citation.')},
                {'name':'notch_geometry','fact':unknown('Notch type,radius,depth and remaining ligament unknown;no standard-default geometry.')},
                {'name':'area_normalization','fact':unknown('Actual cross-section/ligament area and energy-area reduction/correction formula unknown;no re-normalization from nominal dimensions.')},
                {'name':'pendulum_capacity_and_calibration','fact':unknown('Pendulum energy capacity,calibration and loss corrections unknown;no raw absorbed energy inferred.')},
                {'name':'break_mode','fact':unknown('Failure/break classification and handling of partial or nonbreak events unknown.')},
                {'name':'nominal_specimen_dimensions','fact':fact('80 × 9.8 × 3.6 mm (length × width × thickness)',methodloc,'Nominal bars only;actual metrology and impact machining route unknown.')},
                {'name':'test_relative_humidity','fact':unknown('Izod test RH unknown;no assumed laboratory default.')},
            ]}
        prop['uncertainty_note']='Inspected Izod method/Table7/Figure10 do not define central aggregation,n,batches or numeric SD/SE/CI. Unknown does not mean zero scatter. Table/figure/abstract differences are source discrepancies,not measurement uncertainty or an interval.'
        prop['sample_count']=dict(value=None,relation='not_reported',scope='Selected Izod formulation/test only;exact specimen and independent batch counts unknown.',
            source_statement='No exact Izod count in inspected method/results;five formulations are not n=5 specimens and other-test counts are not transferred.',evidence=[])
        prop['method_definition'].update(definition=description,extraction_window=None,evidence=[ev(methodloc,('method','classification'))])
        discrepancy=('Selected '+row['source_label']+' Table7='+row['table7_number']+'kJ/m²;Figure10 printed-label context='+row['figure10_printed_label_context']+'kJ/m². '
            'The source PNA-BPF-5 additionally has Table7=4.1 versus abstract/Figure10=4.01,not ordinary one-decimal rounding;reason unresolved.')
        prop['source_discrepancies'].append(dict(description=discrepancy,
            disposition='Retain selected Table7 literal and all source alternatives as context,not as a second independent experiment. Do not add Figure10 precision,infer author rounding/rawdata,average,repair a supposedtypo,construct an uncertainty/interval or certify the true value. Figure10/Table6 composition context is not independent composition verification.',
            evidence=[ev('RetainedPDFp1abstract; pp15-16 Table6 reportedfraction context; p16Table7; p19Figure10 printed labels',('source_discrepancy',))]))
        scope='Retained same publisherPDF visually checked pp1,5,6,15,16,19: CCBY4,commonDDS preparation,Izodmethod,Table7 selected literals,Table6 author context andFigure10/abstract alternatives. No fresh PDFdownload,latestrevision/SI completeness,rawdata reanalysis or standards/scientific certification.'
        prop['source_document'].update(inspected_on='2026-11-04',inspection_scope=scope)
        prop['verification']['source_inspection_scope']=scope
        prop['scope_note']='Source-qualified '+row['source_label']+' Table7 '+row['table7_number']+'kJ/m² only. Unknown notch/velocity/normalization/breakmode,T/RH,conditioning,n/dispersion prevents matched-condition or intrinsic-material-constant claims. Table7PNA5 4.1 versus abstract/Figure10 4.01 unresolved;selected table does not override other representations. No conversion toCharpy,rawenergy,force,pressure,tear strength,Gc/J-integral/KIC or engineinput;no automaticunitconversion,allowable or universalbound. Existing nominalfeed/mole/alkali contradictions retained.'
        prop['evidence']=[ev(loc,('reported_value','classification')),ev(methodloc,('method','condition'))]
        state=deepcopy(before.states[row['base_state_id']])
        names={'en':row['source_label']+', DDS-cured Izod bars; notch status unknown',
            'zh':row['source_label']+'，DDS固化Izod冲击试条；缺口状态未知',
            'ja':row['source_label']+'、DDS硬化アイゾット試験片；ノッチ状態不明',
            'de':row['source_label']+', DDS-gehärtete Izod-Proben; Kerbzustand unbekannt'}
        state.update(id=row['new_state_id'],version='1.0.0',name=names['en'],names=names,aliases=[],property_ids=[prop['id']])
        state['state']['product_form']=fact('DDS-cured Izod impact bars,nominal80 × 9.8 × 3.6 mm',methodloc,
            'Notch status and actual dimensions unknown;impact section does not establish milling from a3.6mm plate or the bending specimen route.',('state',))
        state['state']['conditioning']=unknown('Impact-specific postcure storage,temperature,RH,moisture state and duration unknown.')
        state['state']['porosity']=unknown('Izod-specimen porosity unknown;degassing does not establish zero porosity.')
        state['state']['orientation']=unknown('Impactbar/notch/strikingface relation toprocessing and isotropy unknown.')
        state['source_scope']='Separate source-qualified Izod bar state under existing '+row['source_label']+' identity and common DDS preparation/180C8hcure. Nominal80x9.8x3.6mm only;notch status,impact machining route,orientation and conditioning unknown. No bending milling/rate/span,DSC conditions or composition repair transferred. No old tensile/bending property moved and no new material identity.'
        state['evidence']=[ev(methodloc,('state',)),ev(preploc,('state',))]
        states.append(state);properties.append(prop)
    data=deepcopy(before.data);data['materials']['records'].extend(states);data['reference_properties']['records'].extend(properties)
    src=deepcopy(before.sources[source])
    src['claim_notes'].append('2026-11-04 source-qualified Table7 Izod supplement for5existing PNA-BPF identities on separateimpactbarstates:2.2/2.9/2.6/3.7/4.1kJ/m². PNA5 Table4.1 vsabstract/Figure10 4.01 remainsunresolved,not repaired,averaged or uncertainty-coded. Unknownnotch/velocity/areaalgorithm/breakmode,T/RH,conditioning,n/dispersion. No bendingmachining/rate/span transfer,Charpy/Gc/KIC/engineering conversion or scientificcertification;priorfeed/mole/alkaliissues retained.')
    data['sources']['records']=[src if s['id']==source else s for s in data['sources']['records']]
    after=Database(data);contracts=after.validate_scientific_contracts()
    assert len(after.properties)==5327 and len(after.states)==5212
    assert all(after.properties[k]==v for k,v in before.properties.items()) and all(after.states[k]==v for k,v in before.states.items())
    assert after.identities==before.identities and after.grades==before.grades and set(after.sources)==set(before.sources)
    assert all(after.sources[k]==v for k,v in before.sources.items() if k!=source)
    restored=deepcopy(src);restored['claim_notes'].pop();assert restored==before.sources[source]
    for name in data:Draft202012Validator(read(ROOT/'schemas'/(name+'.schema.json')),format_checker=FormatChecker()).validate(data[name])
    dest.mkdir(parents=True);(dest/'native-tables').mkdir()
    for name,value in data.items():write(dest/'native-tables'/(name+'.json'),value)
    write(dest/'native-candidate-r1.json',dict(baseline_snapshot=BASE,stage='not_applied',materials=dict(identities=[],grades=[],records=states),reference_properties=dict(records=properties),sources=dict(records=[src])))
    write(dest/'MAPPING_FACTS_R1.json',dict(rows=facts['rows'],property_records={p['id']:p for p in properties},state_records={s['id']:s for s in states},source_record=src))
    counts={}
    for phase,db in [('before',before),('after',after)]:
        export=dest/'source-exports'/phase;db.export(export,source=source);_,joined=read_snapshot(export)
        assert joined=={r['property']['id']:r for r in db.records(source=source)};counts[phase]=len(joined)
    assert counts=={'before':30,'after':35}
    for language in ('en','zh','ja','de'):
        with patch('materials_boundaries.catalog.read_catalog',side_effect=lambda name:data[name]):
            text=render_material_catalog({'schema_version':'1.0.0','records':properties},'reference-properties',language)
        assert all(row['table7_number'] in text for row in facts['rows'])
        assert all(t in text for t in ('kJ/m²','4.1','4.01','notch','unknown','normalization'))
        (dest/('render-'+language+'.txt')).write_text(text,encoding='utf-8',newline='\n')
    write(dest/'VALIDATION_R25.json',dict(baseline_snapshot=BASE,preview_snapshot=after.snapshot,properties=5327,states=5212,new_properties=5,new_states=5,
        new_identities_grades_sources=0,all_old5322_properties_and5207_states_complete_unchanged=True,source_change='One appendedclaimnote only.',
        schema_format='passed',current_graph=contracts,complete_source_export=counts,four_languages='passed',native_applied=False,installed='not_run',full_history_regression='not_run',pushed=False))
    for name in ('native-candidate-r1.json','MAPPING_FACTS_R1.json','VALIDATION_R25.json'):
        with (OUT/name).open('xb') as stream:stream.write((dest/name).read_bytes())
    print(json.dumps(dict(snapshot=after.snapshot,properties=5327,states=5212,source_exports=counts)))


if __name__=='__main__':main()
