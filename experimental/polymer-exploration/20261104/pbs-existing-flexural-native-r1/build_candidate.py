"""Prepare reported flexural means/SDs in unresolved source test contexts."""
from pathlib import Path
from copy import deepcopy
from unittest.mock import patch
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT))
from materials_boundaries.database import Database,read_snapshot
from materials_boundaries.material_presentation import render_material_catalog
from jsonschema import Draft202012Validator,FormatChecker
AREA=ROOT/'experimental/polymer-exploration/20261104'
OUT=Path(__file__).resolve().parent
SID='ewurum_mcdonald_2025_pbs_lignin'
URL='https://mdpi-res.com/d_attachment/polymers/polymers-17-00194/article_deploy/polymers-17-00194.pdf'
BASE='1ea75d1cee10a186eabbd44e96c04625716450490c55614492d316acb5139020'
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(d,f,ensure_ascii=False,indent=2);f.write('\n')
def ev(loc,tags):return dict(source_id=SID,url=URL,locator=loc,supports=list(tags))
def fact(text,loc,note=None,tags=('condition',)):
    return dict(status='reported',text=text,evidence=[ev(loc,tags)],notes=note)
def unknown(note):return dict(status='not_reported_in_inspected_source',text=None,evidence=[],notes=note)

def main():
    dest=Path(sys.argv[1]).resolve();assert not dest.exists() and not dest.is_relative_to(ROOT)
    proposal=AREA/'pbs-existing-flexural-source-r1';review=read(proposal/'INDEPENDENT_SOURCE_REVIEW_R1.json')
    assert review['decision']=='approved' and review['review_inputs_sha256']==sha(proposal/'REVIEW_INPUTS_R1.json')
    assert review['adjudications']['sample_count']['decision']=='exact8_selected_formulation_flexural_group'
    assert review['adjudications']['state_plan']['decision']=='conditional_catalog_only_test_context'
    inputs=read(proposal/'REVIEW_INPUTS_R1.json')
    for key in ['repo_files_sha256','native_files_sha256','external_files_sha256']:
        for n,h in inputs[key].items():assert sha(Path(n) if key=='external_files_sha256' else ROOT/n)==h,n
    facts=read(proposal/'SOURCE_FACTS_R1.json');contexts={c['identity']['id']:c for c in read(proposal/'BASE_CONTEXT_R1.json')['formulations']}
    before=Database();assert before.snapshot==BASE
    methodloc='PDF p.5 section2.9 three-point flexural paragraph;p.13 Table7 andfootnotes;reference33 bibliographic year2015'
    scope='Official PDF pp.3,5,13 selected formulation/preparation,flexural method,Table7 mean/SD andsource rounding;retained XML permissions/reference33. No rawcurves,calibration,standard text,latest notice orforming-route certification.'
    props=[];states=[]
    for group in facts['rows']:
        label=group['source_label'];ctx=contexts[group['identity_id']]
        assert before.identities[group['identity_id']]==ctx['identity']
        assert all(before.states[s['id']]==s for s in ctx['existing_states'])
        old=next(s for s in ctx['existing_states'] if s['id']==ctx['existing_youngs_property']['material_state_id'])
        s=deepcopy(old);name=label+' source flexural test context,physical form and specimen association unresolved'
        s.update(id=group['proposed_state_id'],version='1.0.0',name=name,names={lang:name for lang in ['en','zh','ja','de']},aliases=[],source_designation=label,property_ids=[p['new_property_id'] for p in group['properties']])
        for key in s['state']:s['state'][key]=unknown('Not established for selected Table7 flexural-test context;no physical distinction from oridentity with earlier specimens inferred.')
        s['state']['product_form']=unknown('Selected flexural specimen shape anddimensions not linked. Do not assign hot-pressed strips,DMA3×5×20mm bars or injection-molded dog-bones.')
        s['state']['processing']=fact('Common source formulation single-screw extruded at140°C into3mm strands andpelletized','PDF p.3 section2.3','Common background only. Exact selected flexural forming route andits relationship to existing specimens unresolved;no120°C hot pressing,3.1mm thickness oradditional injection compounding assigned.',('state',))
        s['state']['conditioning']=unknown('Selected flexural temperature/RH/storage,drying andmoisture conditioning not reported;precursor recipe preparation is not test conditioning.')
        for key in ['composition_or_purity','reinforcement']:
            s['state'][key]=deepcopy(old['state'][key])
            if s['state'][key]['status']=='reported':s['state'][key]['evidence']=[ev('PDF p.3 sections2.1–2.3 formulation '+label,('state',))]
        s['source_scope']='Existing '+label+' identity,source-qualified Table7 quasi-static flexural-test context. Physical form,exact forming route andidentity/overlap with existing specimens unresolved. This catalogue state record does not establish new independent physical coverage,batches ormaterials. Geometry,span,direction,temperature andconditioning unknown;no DMA or injection facts transferred. Shared eight-replicate group forstrength andmodulus.'
        s['evidence']=[ev('PDF p.3 sections2.1–2.3',('state',)),ev(methodloc,('state',))]
        for index,row in enumerate(group['properties']):
            loc='PDF p.13 Table7 '+label+' row × '+row['source_property_label']+';footnote a mean±SD androunding'
            description=('Source-reported quasi-static three-point flexural strength;exact endpoint orstrain cutoff unknown.' if row['quantity']=='flexural_strength' else 'Source-reported quasi-static three-point flexural modulus;tangent/secant/chord subtype andextraction window unknown,not Young modulus orDMA storage modulus.')
            definition=description+' Mecmesin MultiTest-dV,2.5kN machine capacity,VectorPro Lite V6.1.0.0,crosshead1.1mm/min,source citesASTM D790. Selected formulation mean±SD,common8replicate flexural-test group;independent specimen/batch count andphysical forming route unresolved.'
            p=deepcopy(ctx['existing_youngs_property'])
            p.update(id=row['new_property_id'],version='1.0.0',material_state_id=s['id'],quantity=row['quantity'],quantity_dimension='pressure',source_property_label=row['source_property_label'],reported_value=dict(kind='scalar',number=row['number'],value_text=row['value_text'],unit_code='MPa',unit_text='MPa'),source_id=SID,reporting_basis='reported_summary',summary_statistic='reported_mean',determination_basis='source_reports_measurement')
            p['basis_note']='Selected Table7 reported mean andSD in sourceMPa precision. Rounded narrative GPa examples are not substituted. Strength andmodulus share one source eight-repeat group,not16independent tests;test context doesnot establish new unique physical specimen coverage.'
            p['conditions']={
                'temperature':unknown('Flexural-test temperature not reported;no standard ambient orDMA sweep assigned.'),
                'test_standard':fact('ASTM D790,reference33 bibliographic year2015',methodloc,'Exact revision suffix unknown;citation doesnot certify compliance orpermit standard-default geometry/conditioning.'),
                'test_method':fact(definition,methodloc,'Capacity is not applied force;no calculation ofstress ormodulus from unreported geometry.'),
                'direction':unknown('Material/test-axis relationship unknown;three-point bending doesnot establish isotropy.'),
                'conditioning':deepcopy(s['state']['conditioning']),
                'loading_rate':fact('Crosshead1.1mm/min','PDF p.5 section2.9 flexural paragraph','Not tensile1mm/min orDMA1Hz;no strain-rate conversion without geometry.'),
                'additional_conditions':[
                    dict(name='flexural_geometry_and_span',fact=unknown('Selected dimensions andsupport span unreported;no DMA orstandard-default values assigned.')),
                    dict(name='flexural_instrument_capacity',fact=fact('Mecmesin MultiTest-dV,2.5kN capacity','PDF p.5 section2.9 flexural paragraph','Instrument capacity only,not measured specimen load.')),
                    dict(name='flexural_software',fact=fact('VectorPro Lite V6.1.0.0','PDF p.5 section2.9 flexural paragraph')),
                    dict(name='selected_formulation_replicate_group',fact=fact('8flexural-test replicates per source formulation','PDF p.5 section2.9;p.13 Table7 mean/SD footnote','Shared group forboth properties;physical specimen independence,production batches andeffective degrees offreedom unknown.')),
                    dict(name='source_table_cell_text',fact=fact(group['source_cells'][index],loc,'Source significance superscripts retained as text;not sample count,uncertainty amplitude orindividual confidence interval.')),
                    dict(name='flexural_definition_detail',fact=unknown('Strength endpoint/strain cutoff ormodulus subtype/extraction window not given;source label only.')),
                    dict(name='selected_specimen_association',fact=unknown('Forming route andphysical overlap/identity with previously catalogued specimens unresolved;not additional independent material coverage.'))
                ]}
            p['uncertainty']=dict(type='reported_standard_deviation',value_text=row['standard_deviation_value_text'],number=row['standard_deviation_number'],unit_text='MPa',unit_code='MPa',scope='Source Table7 selected formulation SD only;source says rounded upward to mean precision where necessary. No confidence interval,standard error,engineering allowable orpopulation variance inferred.',coverage_factor=None,confidence_level=None,evidence=[ev(loc,('uncertainty',))])
            p['uncertainty_status']='reported_standard_deviation';p['uncertainty_note']='Reported mean±SD withsource rounding note preserved. Do not reconstruct unrounded SD,divide bysqrt8 orturn Tukey significance/95%analysis language into individual confidence bounds. SD convention andeffective degrees offreedom unknown.'
            p['sample_count']=dict(value=8,relation='exact',scope='Selected formulation source flexural-test replicate group;both properties share this group,not16independent tests. Distinct physical specimens andindependent production batches not established.',source_statement='Section2.9 reports8replicates forflexural testing;Table7 reports selected formulation mean±SD.',evidence=[ev(methodloc,('sample_count',))])
            p['method_definition']=dict(type='source_reported_conventional',definition=definition,extraction_window=None,evidence=[ev(methodloc,('method','classification'))])
            p['source_discrepancies']=[]
            p['evidence']=[ev(loc,('reported_value','classification','summary_statistic','uncertainty')),ev(methodloc,('method','condition','sample_count'))]
            p['source_document']=dict(url=URL,revision='Official publisher PDF Polymers2025,17,194;retained2026-11-04.',inspected_on='2026-11-04',sha256=facts['PDF_sha256'],hash_status='recorded',hash_note=None,inspection_scope=scope,inspection_status='selected_content_inspected')
            p['verification']=dict(source_inspection_scope=scope,transcription_cross_check='completed',independent_scientific_review=False,raw_data_reanalysis=False)
            p['scope_note']='Source '+label+' Table7 '+row['source_property_label']+' mean='+row['number']+'MPa,SD='+row['standard_deviation_number']+'MPa,n=8source flexural repeats. '+description+' Physical form,forming route,specimen association,geometry,span,axis,temperature/RH andconditioning unresolved. No new independent material/specimen/batch coverage. Shared group,source precision androunding retained;no DMA/tensile metadata transfer,standard compliance,normality/CI/SE/CV,service limit,allowable,universal bound orengine input.'
            assert p['density_basis'] is None and p['evaluation_support']=='catalog_only' and not p['universal_bound'] and not p['engineering_allowable']
            props.append(p)
        states.append(s)
    source=deepcopy(before.sources[SID]);source['claim_notes'].append('2026-11-04 Table7 reported flexural-strength/modulus mean±SD for9existing PBS formulations,18properties in9unresolved source test-context states;no R0. Source8replicate formulation group shared bytwo properties,not16tests. PreserveMPa precision/SD rounding;physical form/route/specimen overlap/geometry/span/conditioning unknown,no independent physical coverage claim. No DMA/tensile geometry,rates/statistics orstandard-default conditions/compliance/engineering use inferred.')
    data=deepcopy(before.data);data['materials']['records'].extend(states);data['reference_properties']['records'].extend(props);data['sources']['records']=[source if s['id']==SID else s for s in data['sources']['records']]
    after=Database(data);assert len(after.properties)==5371 and len(after.states)==5245
    assert all(after.properties[k]==v for k,v in before.properties.items()) and all(after.states[k]==v for k,v in before.states.items())
    assert after.identities==before.identities and after.grades==before.grades and set(after.sources)==set(before.sources)
    assert all(after.sources[k]==v for k,v in before.sources.items() if k!=SID)
    restored=deepcopy(source);restored['claim_notes'].pop();assert restored==before.sources[SID]
    # Do not bypass structural duplicates or invent geometry if this fails.
    contracts=after.validate_scientific_contracts()
    for name in data:Draft202012Validator(read(ROOT/'schemas'/(name+'.schema.json')),format_checker=FormatChecker()).validate(data[name])
    for quantity in ['flexural_strength','flexural_modulus']:
        actual={r['property']['id']:r['property'] for r in after.records(source=SID,quantity=quantity)}
        assert actual=={p['id']:p for p in props if p['quantity']==quantity} and len(actual)==9
    assert {r['property']['id']:r['property'] for r in before.records(quantity='glass_transition_temperature')}=={r['property']['id']:r['property'] for r in after.records(quantity='glass_transition_temperature')}
    assert {r['property']['id']:r['property'] for r in before.records(quantity='melting_peak_temperature')}=={r['property']['id']:r['property'] for r in after.records(quantity='melting_peak_temperature')}
    dest.mkdir(parents=True);(dest/'native-tables').mkdir()
    for name in data:write(dest/'native-tables'/(name+'.json'),data[name])
    candidate=dict(baseline_snapshot=BASE,stage='not_applied',materials=dict(identities=[],grades=[],records=states),reference_properties=dict(records=props),sources=dict(records=[source]))
    write(dest/'native-candidate-r1.json',candidate);after.export(dest/'source-export',source=SID);_,exported=read_snapshot(dest/'source-export')
    assert exported=={r['property']['id']:r for r in after.records(source=SID)} and len(exported)==55
    for language in ['en','zh','ja','de']:
        with patch('materials_boundaries.catalog.read_catalog',side_effect=lambda name:data[name]):text=render_material_catalog({'schema_version':'1.0.0','records':props},'reference-properties',language)
        assert all(p['id'] in text and p['reported_value']['value_text'] in text and p['uncertainty']['value_text'] in text for p in props)
        for token in ['physical form','unresolved','1.1mm/min','rounded','not16']:assert token in text
        (dest/('render-'+language+'.txt')).write_text(text,encoding='utf-8',newline='\n')
    result=dict(baseline_snapshot=BASE,preview_snapshot=after.snapshot,properties=5371,states=5245,new_properties=18,new_catalog_test_context_states=9,new_identities_grades_sources=0,independent_physical_coverage='not_established',all5353_old_properties_unchanged=True,all5236_old_states_unchanged=True,source_append_only=True,current_graph=contracts,schema_format='passed',source_export_objects=55,new_strength_query=9,new_modulus_query=9,old_Tg15_and_melting11_properties_unchanged=True,four_languages='passed',source_selected_group_n=8,shared_group_not16=True,unit_suites_run=False,installed=False,native_applied=False,full_history_regression='not_run',pushed=False)
    write(dest/'VALIDATION_R1.json',result);write(dest/'MAPPING_FACTS_R1.json',dict(property_records={p['id']:p for p in props},state_records={s['id']:s for s in states},source_record=source))
    for name in ['native-candidate-r1.json','MAPPING_FACTS_R1.json','VALIDATION_R1.json']:write(OUT/name,read(dest/name))
    print(json.dumps(result))
if __name__=='__main__':main()
