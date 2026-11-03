"""Prepare one source-qualified negative Tg; keep common duplication separate."""
from copy import deepcopy
import hashlib,json,sys,xml.etree.ElementTree as E
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT))
from jsonschema import Draft202012Validator,FormatChecker
from materials_boundaries.database import Database,read_snapshot
from materials_boundaries.material_presentation import render_material_catalog
AREA=ROOT/'experimental/polymer-exploration/20261104'
OUT=Path(__file__).resolve().parent
BASE='9a00c6f56ca0773d1afbdfaae1561567e264aec130d23349e18317b39519a72d'
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
    dest=Path(sys.argv[1]).resolve();assert not dest.exists() and not dest.is_relative_to(ROOT)
    proposal=AREA/'phbv39-tg-source-audit-r1';review=read(proposal/'INDEPENDENT_SOURCE_REVIEW_R1.json')
    assert review['decision']=='approved' and review['review_inputs_sha256']==sha(proposal/'REVIEW_INPUTS_R1.json')
    count_review=review['adjudications']['duplicate_count']
    assert count_review['decision']=='method_context_only'
    assert count_review['selected_scalar_sample_count']=={'value':None,'relation':'not_reported'}
    manifest=read(proposal/'REVIEW_INPUTS_R1.json')
    for n,d in manifest['repo_files_sha256'].items():assert sha(ROOT/n)==d,n
    for n,d in manifest['external_files_sha256'].items():assert sha(Path(n))==d,n
    facts=read(proposal/'SOURCE_FACTS_R1.json');row=facts['row'];before=Database();assert before.snapshot==BASE
    assert before.states[row['base_state_id']]==read(proposal/'BASE_STATE_R1.json')
    assert before.properties[row['base_property_id']]==read(proposal/'BASE_PROPERTY_R1.json')
    assert before.identities[row['identity_id']]==read(proposal/'BASE_IDENTITY_R1.json')
    xml=ROOT.parent/'open-database-evidence/polymer-property-source-rechecks-20261103/phbv/article-r1.xml'
    assert sha(xml)==facts['primary_XML_sha256'];article=E.parse(xml).getroot()
    table=next(t for t in article.findall('.//table-wrap') if t.findtext('label')=='Table 4')
    cells=next([' '.join(' '.join(c.itertext()).split()) for c in tr] for tr in table.findall('.//tr') if 'PHBV-39' in ' '.join(tr.itertext()))
    assert cells[0]=='PHBV-39' and cells[1]==row['source_value_text']=='−5.3'
    assert row['number']=='-5.3' and row['unit_code']=='degC'
    assert row['new_state_id'] not in before.states and row['new_property_id'] not in before.properties
    sid=facts['source_id'];url=facts['primary_XML_url']
    def ev(loc,tags):return dict(source_id=sid,url=url,locator=loc,supports=list(tags))
    def unknown(note):return dict(status='not_reported_in_inspected_source',text=None,evidence=[],notes=note)
    def na(note):return dict(status='not_applicable',text=None,evidence=[],notes=note)
    def fact(text,loc,note=None,tags=('condition',)):
        return dict(status='reported',text=text,evidence=[ev(loc,tags)],notes=note)
    methodloc='Retained primary JATS section2.2.5 Thermal Analysis,DSC paragraph only'
    preploc='Retained primary JATS sections2.1 and2.2.1,operational-day identity,extraction/purification'
    loc='Retained primary JATS Table4,PHBV-39 row,DSC Tg(°C) column'
    definition=('Source-reported DSC Tg from the inflection point of the second heating scan;TA Q200 DSC with refrigerated cooling, '
        '4–6mg purified PHBV in Tzero aluminum pans,nitrogen50mL/min. Source initially equilibrates40°C3min, '
        'heats10°C/min to180°C with3min hold,cools to−50°C at−10°C/min with3min hold,and repeats the cycle. '
        'TA Universal Analysis v4.5A;precise baseline/inflection algorithm unknown. '
        'Method says in duplicate,but the selected Table4 cell actual n/run provenance is not established.')
    prop=deepcopy(before.properties[row['base_property_id']])
    prop.update(id=row['new_property_id'],version='1.0.0',material_state_id=row['new_state_id'],quantity='glass_transition_temperature',
        quantity_dimension='temperature',source_property_label='Tg (°C)',summary_statistic='not_stated',reporting_basis='not_stated',
        uncertainty=None,uncertainty_status='not_reported_in_inspected_source')
    prop['reported_value']=dict(kind='scalar',number='-5.3',value_text='−5.3',unit_code='degC',unit_text='°C')
    prop['basis_note']='Exact selected Abbasi2022 Table4 literal −5.3°C;central estimator and numerical dispersion unknown. Source groups Guho2020 results and reanalyzed data;per-cell run provenance and independence unresolved. Not certified as a new independent2022 experiment.'
    prop['conditions']={
        'temperature':fact('Nonisothermal DSC program:initial40°C3min,heating to180°C,cooling to−50°C,cycle repeated;Tg from second heating.',methodloc,'Program settings only,not ambient,Tg value,a hot-pressing operation or an actual logged profile. Exact second-scan implementation not reconstructed beyond source wording.'),
        'test_standard':unknown('No DSC test standard named in inspected section2.2.5;no ASTM/ISO or mechanical-test standard inferred.'),
        'test_method':fact(definition,methodloc,'Common method context;selected-cell run provenance not established. Tg is not melting,cure or service-temperature limit.'),
        'direction':na('Mechanical loading direction not applicable to DSC;sample orientation/isotropy not established.'),
        'conditioning':unknown('DSC-specific moisture,RH,postextraction storage and drying time/temperature unknown. Extraction vacuum drying does not establish mechanical60°Covernight conditioning for DSC.'),
        'loading_rate':na('Mechanical loading rate not applicable;heating and cooling rates recorded separately.'),
        'additional_conditions':[
            {'name':'thermal_heating_rate','fact':fact('10°C/min',methodloc,'Source nominal heating rate,not mechanical rate or verified actual profile.')},
            {'name':'thermal_cooling_rate','fact':fact('−10°C/min to−50°C',methodloc,'Source signed cooling ramp,not a second Tg or mechanical strain rate.')},
            {'name':'Tg_extraction_criterion','fact':fact('Inflection point of the second heating scan',methodloc,'Precise algorithm,fit window,baseline and rounding unknown.')},
            {'name':'pan_and_sample_mass','fact':fact('Tzero aluminum pans;4–6mg purified PHBV',methodloc,'Exact individualmass,lid details and sample/pan geometry unknown;mass is not n.')},
            {'name':'purge_atmosphere_and_flow','fact':fact('Nitrogen50mL/min',methodloc,'Nominal flow,not gas purity or dry-equilibrium moisture evidence.')},
            {'name':'calibration_and_software','fact':fact('Indium and sapphire standards following manufacturer protocols;TA Universal Analysis v4.5A',methodloc,'Source statement,not calibration certificate,accuracy or uncertainty verification.')},
            {'name':'common_method_duplicate_measurements','fact':fact('DSC method states in duplicate (two measurement repeats)',methodloc,'Common method metadata only. Per-cell Table4 run linkage unresolved;not selected-result n=2,not two independent specimens/batches,and not inferred from two heating cycles.')},
            {'name':'thermal_holds','fact':fact('Initial40°C3min;180°C3min;−50°C3min,then source says cycle repeated',methodloc,'Preserve stated sequence without reconstructing an unreported actual trace or asserting complete erasure of all thermal history.')},
        ]}
    prop['uncertainty_note']='Table4 reports a single literal without central aggregation or numerical SD/SE/CI. The common duplicate DSC method does not establish selected-cell n or an arithmetic mean. Table9 mechanical mean/SD/at-least5 replication is not transferred;unknown is not zero scatter.'
    prop['sample_count']=dict(value=None,relation='not_reported',scope='Selected PHBV-39 Table4 Tg cell:actual contributing measurement/specimen and independent batch counts unknown because per-cell run provenance is unresolved.',
        source_statement='Section2.2.5 states a common in-duplicate DSC method;section3.4 jointly cites Guho results and reanalysis. Common duplication is retained separately,not asserted as this scalar n.',evidence=[])
    prop['method_definition'].update(definition=definition,extraction_window=None,evidence=[ev(methodloc,('method','classification'))])
    prop['source_discrepancies']=[dict(description='Section3.4 associates Table4/FigureS1 with results obtained from Guho2020 and reanalyzed data. The original run/data provenance of the selected −5.3°C cell is not resolved.',
        disposition='Retain only the Abbasi2022 Table4 PHBV-39 literal as source-qualified context. Do not label a new independent2022 experiment,add uninspected Guho measurements,transfer duplicate count to selected n,repair/average values or broaden prior-work licensing.',
        evidence=[ev('Retained JATS section3.4 opening paragraph,Table4 andreference6 DOI10.1016/j.biteb.2020.100588',('source_discrepancy',))])]
    scope='Retained primary PMC9571417 XML selected Table4 PHBV-39 Tg,sections2.1/2.2.1/2.2.5/3.4,Table1 composition andarticlepermission notice. Current PMC HTML readback agrees selected cell/provenance wording. Guho DOI inaccessible;no prior-paper contents,SI figures/rawdata,fresh PDFvisual or latestnotice/completeness audit.'
    prop['source_document'].update(url=url,revision='Retained PMC9571417 primary XML;not a fresh PDF asset.',inspected_on='2026-11-04',sha256=sha(xml),hash_status='recorded',hash_note=None,inspection_scope=scope)
    prop['verification']['source_inspection_scope']=scope
    prop['scope_note']='Source-qualified operational-day39 PHBV Tg−5.3°C,not39%HV. Second-heating inflection/common DSC program are reported;selected-cell run provenance,n/aggregation/dispersion,moisture/storage and exact inflection algorithm unknown. In-duplicate is common-method context only. No hot-pressed mechanical-disc geometry/drying/rate or Table9 statistics transferred. No new independent experiment,melting temperature,service limit,engineering allowable,universal bound,automatic conversion or engine input.'
    prop['evidence']=[ev(loc,('reported_value','classification')),ev(methodloc,('method','condition'))]
    state=deepcopy(before.states[row['base_state_id']])
    names={'en':'Purified operational-day PHBV-39,DSC second-heating sample','zh':'提纯运行日PHBV-39，DSC第二次升温样品','ja':'精製運転日PHBV-39、DSC第2加熱試料','de':'Gereinigtes Betriebstags-PHBV-39,DSC-Probe im zweiten Heizlauf'}
    state.update(id=row['new_state_id'],version='1.0.0',name=names['en'],names=names,aliases=[],property_ids=[prop['id']])
    state['state']={
        'product_form':fact('Purified PHBV DSC sample4–6mg in Tzero aluminum pan',methodloc,'No hot-pressed0.3g disc or cut mechanical-bar geometry inherited;exact samplemass/lid geometry unknown.',('state',)),
        'processing':fact('Operational-day biomass lyophilized and acetone washed;CHCl3 Soxhlet extraction,petroleum-ether and methanol precipitation/purification,then vacuum drying.',preploc,'Extraction/purification only;no mechanical180°C hot pressing or60°Covernight schedule transferred. Purified does not mean100%pure.',('state',)),
        'temper_or_heat_treatment':fact('Source DSC thermal program:initial40°C3min,heating10°C/min to180°C3min,cooling−10°C/min to−50°C3min;cycle repeated,Tg selected fromsecond heating.',methodloc,'DSC program is not a mechanical hot-press history,environment temperature or proof of complete thermal-history erasure.',('state',)),
        'conditioning':unknown('DSC-specific moisture,RH,storage,drying temperature/duration before scan unknown;mechanical60°Covernight vacuumdrying not transferred.'),
        'composition_or_purity':deepcopy(before.states[row['base_state_id']]['state']['composition_or_purity']),
        'reinforcement':unknown('No quantitative reinforcing phase assigned to this selected purified DSC sample.'),
        'porosity':unknown('DSC sample porosity unknown;purification/vacuumdrying does not prove zero porosity.'),
        'orientation':unknown('DSC sample orientation/isotropy unknown;no mechanical test axis assigned.')}
    state['source_scope']='Existing PHBV-39 operational-day identity,not39%HV. Separate purified DSC second-heating state,not hot-pressed mechanical discs. Common extraction andTable1 composition only;no mechanical0.3g/180°Cpress/60°Covernight/cutbar transferred. Source reports DSC program andinflection criterion;per-cellrunprovenance,moisture,n/dispersion unknown. In-duplicate common method not exact selected-result n.'
    state['evidence']=[ev(preploc,('state',)),ev(methodloc,('state',))]
    data=deepcopy(before.data);data['materials']['records'].append(state);data['reference_properties']['records'].append(prop)
    source=deepcopy(before.sources[sid]);source['claim_notes'].append('2026-11-04 selected PHBV-39 Table4 Tg−5.3°C supplement onone separatepurified DSCstate underexisting operational-day39 identity,not39%HV. Source second-heating inflection/common method retained;in-duplicate onlycommonmethod,selected n/aggregation/dispersion andcellrunprovenanceunknown. Section3.4 combinesGuho results/reanalysis;notclaimednewindependent2022experiment orprior-worklicense. No mechanicalhotpress/drying/geometry/statistics transfer,SI/rawdatainspection,engine orengineering/service-limit conversion. Earlier pending limited-selection notes are historical,not proof ofthis supplement acceptance.')
    data['sources']['records']=[source if s['id']==sid else s for s in data['sources']['records']]
    after=Database(data);contracts=after.validate_scientific_contracts()
    assert len(after.properties)==5333 and len(after.states)==5218
    assert all(after.properties[k]==v for k,v in before.properties.items()) and all(after.states[k]==v for k,v in before.states.items())
    assert after.identities==before.identities and after.grades==before.grades and set(after.sources)==set(before.sources)
    assert all(after.sources[k]==v for k,v in before.sources.items() if k!=sid)
    restored=deepcopy(source);restored['claim_notes'].pop();assert restored==before.sources[sid]
    for n,v in data.items():Draft202012Validator(read(ROOT/'schemas'/(n+'.schema.json')),format_checker=FormatChecker()).validate(v)
    selected=list(after.records(source=sid,quantity='glass_transition_temperature'));assert len(selected)==1 and selected[0]['property']==prop
    tg={r['property']['id']:r['property'] for r in after.records(quantity='glass_transition_temperature')};assert len(tg)==6
    dest.mkdir(parents=True);(dest/'native-tables').mkdir()
    for n,v in data.items():write(dest/'native-tables'/(n+'.json'),v)
    write(dest/'native-candidate-r1.json',dict(baseline_snapshot=BASE,stage='not_applied',materials=dict(identities=[],grades=[],records=[state]),reference_properties=dict(records=[prop]),sources=dict(records=[source])))
    write(dest/'MAPPING_FACTS_R1.json',dict(row=row,property_records={prop['id']:prop},state_records={state['id']:state},source_record=source,all_Tg_property_records=tg))
    counts={}
    for phase,db in [('before',before),('after',after)]:
        export=dest/'source-exports'/phase;db.export(export,source=sid);_,joined=read_snapshot(export)
        assert joined=={r['property']['id']:r for r in db.records(source=sid)};counts[phase]=len(joined)
    assert counts=={'before':4,'after':5}
    for language in ('en','zh','ja','de'):
        with patch('materials_boundaries.catalog.read_catalog',side_effect=lambda n:data[n]):
            text=render_material_catalog({'schema_version':'1.0.0','records':[prop]},'reference-properties',language)
        assert all(t in text for t in ('−5.3','°C','inflection','second heating','Guho','unknown','duplicate'))
        (dest/('render-'+language+'.txt')).write_text(text,encoding='utf-8',newline='\n')
    write(dest/'VALIDATION_R27.json',dict(baseline_snapshot=BASE,preview_snapshot=after.snapshot,properties=5333,states=5218,new_properties=1,new_states=1,new_identities_grades_sources=0,
        all_old5332_properties_and5217_states_complete_unchanged=True,source_change='One appended claimnote only.',schema_format='passed',current_graph=contracts,
        exact_source_and_Tg_query=1,total_Tg_query_objects=6,complete_source_export=counts,four_languages='passed',selected_sample_count='unknown;duplicateonlycommonmethod',
        production_runtime_schema_tests_changed=False,unit_tests='Not rerun;exact r26 approved172-input binding inherited,no production/test changes.',native_applied=False,installed='not_run',full_history_regression='not_run',pushed=False))
    for n in ('native-candidate-r1.json','MAPPING_FACTS_R1.json','VALIDATION_R27.json'):
        with (OUT/n).open('xb') as f:f.write((dest/n).read_bytes())
    print(json.dumps(dict(snapshot=after.snapshot,properties=5333,states=5218,source_exports=counts,total_Tg=6)))
if __name__=='__main__':main()
