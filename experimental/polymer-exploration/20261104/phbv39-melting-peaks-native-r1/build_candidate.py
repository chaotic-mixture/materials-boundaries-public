"""Prepare two source-labelled melting peaks on one existing DSC state."""
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
BASE='ee1b29bd4c1a4dbe7b7aea476dcbbb054eb0fe8928ecf3ada2b6d50ef2533c6d'
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
    dest=Path(sys.argv[1]).resolve();assert not dest.exists() and not dest.is_relative_to(ROOT)
    proposal=AREA/'phbv39-melting-peaks-source-contract-r1';review=read(proposal/'INDEPENDENT_SOURCE_REVIEW_R1.json')
    assert review['decision']=='approved' and review['review_inputs_sha256']==sha(proposal/'REVIEW_INPUTS_R1.json')
    manifest=read(proposal/'REVIEW_INPUTS_R1.json');archives=read(proposal/'BASELINE_CONTRACT_BINDING_R1.json')
    for n,d in manifest['repo_files_sha256'].items():
        if sha(ROOT/n)!=d:
            old=archives[n];assert sha(ROOT/old['archive_path'])==old['sha256']==d,n
    for n,d in manifest['external_files_sha256'].items():assert sha(Path(n))==d,n
    facts=read(proposal/'SOURCE_FACTS_R1.json');before=Database();assert before.snapshot==BASE
    base=read(proposal/'BASE_PROPERTY_R1.json');oldstate=read(proposal/'BASE_STATE_R1.json')
    assert before.properties[base['id']]==base and before.states[oldstate['id']]==oldstate
    xml=ROOT.parent/'open-database-evidence/polymer-property-source-rechecks-20261103/phbv/article-r1.xml'
    assert sha(xml)==facts['primary_XML_sha256'];article=E.parse(xml).getroot()
    table=next(t for t in article.findall('.//table-wrap') if t.findtext('label')=='Table 4')
    cells=next([' '.join(' '.join(c.itertext()).split()) for c in tr] for tr in table.findall('.//tr') if 'PHBV-39' in ' '.join(tr.itertext()))
    assert cells[2:4]==['159.7','170.1'] and [r['number'] for r in facts['rows']]==cells[2:4]
    sid=facts['source_id'];url=facts['primary_XML_url'];props=[]
    methodloc='Retained primary JATS section2.2.5 DSC paragraph,second-heating endothermal-peak method for Tm'
    def ev(loc,tags):return dict(source_id=sid,url=url,locator=loc,supports=list(tags))
    def fact(text,loc,note=None,tags=('condition',)):
        return dict(status='reported',text=text,evidence=[ev(loc,tags)],notes=note)
    for row in facts['rows']:
        assert row['new_property_id'] not in before.properties
        prop=deepcopy(base);label=row['source_label'];loc='Retained primary JATS Table4 PHBV-39 row,DSC '+label+'(°C) column'
        definition=('Source-labelled '+label+' endothermic melting peak from second heating,TA Q200 DSC,4–6mg purified PHBV,Tzero aluminum pans,N2 50mL/min. '
            'Common program:initial40°C3min,heat10°C/min to180°C3min,cool−10°C/min to−50°C3min,cycle repeated. '
            'Not Tg inflection,melting onset/endset,cooling crystallization or TGA degradation. Precise peak-picking/baseline algorithm and selected-cell run provenance unknown.')
        prop.update(id=row['new_property_id'],version='1.0.0',quantity='melting_peak_temperature',source_property_label=label+' (°C)')
        prop['reported_value']=dict(kind='scalar',number=row['number'],value_text=row['value_text'],unit_code='degC',unit_text='°C')
        prop['basis_note']='Selected Table4 '+label+' literal only;not an average,temperature interval or a universal single melting point. Central aggregation,n/dispersion and original/reanalysis run provenance unknown;not a new independent2022 experiment.'
        prop['conditions']['temperature']=fact('Nonisothermal DSC program:initial40°C3min,heating to180°C,cooling to−50°C,cycle repeated;melting peaks selected fromsecond heating.',methodloc,'Program settings only,not ambient,actual logged profile or mechanical hot pressing;no second-scan start reconstructed beyond source wording.')
        prop['conditions']['test_method']=fact(definition,methodloc,'Source-labelled endothermic peak;not a generic melting onset,service limit or certified global phase boundary.')
        for item in prop['conditions']['additional_conditions']:
            if item['name']=='Tg_extraction_criterion':
                item['name']='melting_peak_extraction_criterion';item['fact']=fact('Endothermal peak of the second heating scan',methodloc,'Exact baseline/peak algorithm,fit window and rounding unknown;Tg inflection criterion not transferred.')
        prop['conditions']['additional_conditions'].append(dict(name='thermal_peak_label',fact=fact(label,loc,'Source Table4 column label only;no cross-source universal peak ordering,index-to-phase assignment or separate experiment inferred.')))
        prop['method_definition'].update(definition=definition,extraction_window=None,evidence=[ev(methodloc,('method','classification'))])
        prop['sample_count'].update(scope='Selected PHBV-39 Table4 '+label+' cell:actual contributing measurement/specimen and independent batch counts unknown;per-cell original/reanalysis run linkage unresolved.',
            source_statement='Common section2.2.5 DSC method states in duplicate;this does not establish selected '+label+' n. Neither two peak columns nor two heating cycles count as independent specimens.')
        prop['uncertainty_note']='Table4 '+label+' literal has no defined central aggregation or numerical SD/SE/CI. Common duplicate method does not establish selected-cell n or a mean. No Table9 mechanical statistics or uncertainty from peak separation;unknown is not zero scatter.'
        prop['source_discrepancies']=[dict(description='Section3.4 associates Table4/FigureS1 with Guho2020 results and reanalyzed data;selected '+label+'='+row['number']+'°C cell original run provenance and independence remain unresolved.',
            disposition='Retain only selected Abbasi2022 Table4 literal with its own source column. Do not add an uninspected Guho experiment,claim new independent2022 runs,transfer duplicate count to selected n,average peaks,make a temperature interval or broaden prior-work licensing.',
            evidence=[ev('Retained JATS section3.4 opening paragraph,Table4 andreference6 DOI10.1016/j.biteb.2020.100588',('source_discrepancy',))])]
        scope='Retained primary PMC9571417 XML Table4 PHBV-39 '+label+' column,sections2.2.5/3.4 andarticle permission;prior exact approved DSC identity/preparation context retained. No fresh PDF,Guho primary content,SI/rawcurves,actual calibration or latest-notice/completeness audit.'
        prop['source_document'].update(inspected_on='2026-11-04',inspection_scope=scope);prop['verification']['source_inspection_scope']=scope
        prop['scope_note']='Source-qualified operational-day39 PHBV '+label+' melting peak '+row['number']+'°C. Source second-heating endothermal peak criterion only;exact algorithm,cellrunprovenance,n/aggregation/dispersion andmoisture/storage unknown. Separate property on same DSCstate,not another material/run,an implicitTm1–Tm2 interval/average or universal single melting point. No Tg/Tc/TGA substitution,crystal-composition/peak-cause inference,mechanical history/statistics transfer,service limit,allowable,universal bound,automatic conversion orengine input.'
        prop['evidence']=[ev(loc,('reported_value','classification')),ev(methodloc,('method','condition'))]
        assert prop['sample_count']['value'] is None and prop['uncertainty'] is None and prop['summary_statistic']=='not_stated'
        props.append(prop)
    state=deepcopy(oldstate);assert state['version']=='1.0.0';state['version']='1.0.1'
    state['property_ids'].extend(p['id'] for p in props)
    state['source_scope']+=' 2026-11-04 append two separately source-labelled second-heating melting peaks Tm1/Tm2 on this same DSCstate;all existing state facts retained. Neither peaks nor common duplicate method establish independent specimens/runs;selected-cell n/runprovenance unknown.'
    assert {k for k in state if state[k]!=oldstate[k]}=={'version','property_ids','source_scope'}
    data=deepcopy(before.data);data['reference_properties']['records'].extend(props)
    data['materials']['records']=[state if s['id']==state['id'] else s for s in data['materials']['records']]
    source=deepcopy(before.sources[sid]);source['claim_notes'].append('2026-11-04 source-qualified Table4 PHBV-39 melting peaks Tm1=159.7°C/Tm2=170.1°C on existing purified DSCsecond-heating state. Two property IDs/source labels/column evidence,not an interval,average,two materials or independent experiments. Source endothermal peak criterion,not Tg inflection;selected n/aggregation/dispersion andGuho/reanalysisrun attributionunknown,duplicate commonmethod only. No prior-worklicense expansion,SI/rawcurvesinspection,crystalassignment,mechanicalhistory/statistics,engine orengineering/service-limit conversion. Existing Tgproperty completeunchanged.')
    data['sources']['records']=[source if s['id']==sid else s for s in data['sources']['records']]
    after=Database(data);contracts=after.validate_scientific_contracts()
    assert len(after.properties)==5335 and len(after.states)==5218
    assert all(after.properties[k]==v for k,v in before.properties.items())
    assert all(after.states[k]==v for k,v in before.states.items() if k!=state['id'])
    assert after.identities==before.identities and after.grades==before.grades and set(after.sources)==set(before.sources)
    assert all(after.sources[k]==v for k,v in before.sources.items() if k!=sid)
    restored=deepcopy(source);restored['claim_notes'].pop();assert restored==before.sources[sid]
    for n,v in data.items():Draft202012Validator(read(ROOT/'schemas'/(n+'.schema.json')),format_checker=FormatChecker()).validate(v)
    selected=list(after.records(source=sid,quantity='melting_peak_temperature'))
    assert {r['property']['id']:r['property'] for r in selected}=={p['id']:p for p in props}
    assert len({r['state']['id'] for r in selected})==1
    assert {r['property']['id']:r['property'] for r in before.records(quantity='glass_transition_temperature')}=={r['property']['id']:r['property'] for r in after.records(quantity='glass_transition_temperature')}
    dest.mkdir(parents=True);(dest/'native-tables').mkdir()
    for n,v in data.items():write(dest/'native-tables'/(n+'.json'),v)
    write(dest/'native-candidate-r1.json',dict(baseline_snapshot=BASE,stage='not_applied',materials=dict(identities=[],grades=[],records=[state]),reference_properties=dict(records=props),sources=dict(records=[source])))
    write(dest/'MAPPING_FACTS_R1.json',dict(rows=facts['rows'],property_records={p['id']:p for p in props},state_records={state['id']:state},baseline_state=oldstate,baseline_Tg_property=base,source_record=source,all_Tg_property_records={r['property']['id']:r['property'] for r in after.records(quantity='glass_transition_temperature')}))
    counts={}
    for phase,db in [('before',before),('after',after)]:
        export=dest/'source-exports'/phase;db.export(export,source=sid);_,joined=read_snapshot(export)
        assert joined=={r['property']['id']:r for r in db.records(source=sid)};counts[phase]=len(joined)
    assert counts=={'before':5,'after':7}
    after.export(dest/'melting-peak-export',quantity='melting_peak_temperature')
    assert read_snapshot(dest/'melting-peak-export')[1]=={r['record_id']:r for r in selected}
    for language in ('en','zh','ja','de'):
        with patch('materials_boundaries.catalog.read_catalog',side_effect=lambda n:data[n]):
            text=render_material_catalog({'schema_version':'1.0.0','records':props},'reference-properties',language)
        assert all(t in text for t in ('159.7','170.1','Tm1','Tm2','endothermic','unknown','Guho'))
        (dest/('render-'+language+'.txt')).write_text(text,encoding='utf-8',newline='\n')
    write(dest/'VALIDATION_R28.json',dict(baseline_snapshot=BASE,preview_snapshot=after.snapshot,properties=5335,states=5218,new_properties=2,new_states=0,new_identities_grades_sources=0,
        all_old5333_properties_complete_unchanged=True,all_other5217_states_complete_unchanged=True,existing_DSC_state_changes=['version','property_ids','source_scope'],source_change='One appendedclaimnote only.',schema_format='passed',current_graph=contracts,
        melting_peak_query=2,melting_peak_distinct_states=1,Tg_global=6,old_Tg_property_unchanged=True,complete_source_export=counts,complete_melting_peak_export=2,four_languages='passed',
        selected_sample_count='unknown;duplicatecommonmethodonly',native_applied=False,installed='not_run',full_history_regression='not_run',pushed=False))
    for n in ('native-candidate-r1.json','MAPPING_FACTS_R1.json','VALIDATION_R28.json'):
        with (OUT/n).open('xb') as f:f.write((dest/n).read_bytes())
    print(json.dumps(dict(snapshot=after.snapshot,properties=5335,states=5218,source_exports=counts,melting_peaks=2,Tg=6)))
if __name__=='__main__':main()
