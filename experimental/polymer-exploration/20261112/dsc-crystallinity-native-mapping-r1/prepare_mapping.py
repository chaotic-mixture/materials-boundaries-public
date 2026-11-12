"""Prepare ten author-reported Xc cells without arithmetic or native writes."""
from pathlib import Path
from copy import deepcopy
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent;BASE=HERE.parent
SOURCE=BASE/'dsc-crystallinity-source-screen-r2';IMPL=BASE/'dsc-crystallinity-implementation-r3'
sys.path.insert(0,str(ROOT))
from materials_boundaries.database import Database
from materials_boundaries._dsc_crystallinity_contract import QUANTITY,UNIT,METHOD,PROFILE,REFERENCE_UNIT
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(n,obj):
    with (HERE/n).open('x',encoding='utf-8',newline='\n') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
    entry=IMPL/'REVIEW_IMPLEMENTATION_INPUTS_R3.json';approval=read(IMPL/'INDEPENDENT_IMPLEMENTATION_REVIEW_R3.json')
    assert approval['decision']=='approved' and approval['review_inputs_sha256']==sha(entry)
    frozen=read(entry)
    for field in ('repo_files_sha256','external_files_sha256','native_files_sha256'):
        for n,h in frozen[field].items():assert sha(Path(n) if field=='external_files_sha256' else ROOT/n)==h,n
    before=Database();assert before.snapshot=='3698ac54d2335788a74d21f126c92c96b3d34ef4c2454ed016f141ddac8f947a'
    facts=read(SOURCE/'SOURCE_FACTS_R2.json');props=[];states=[]
    for row in facts['rows']:
        sid=row['source_id'];url=row['primary_url'];label=row['source_label'];pbs=sid.startswith('ewurum');key=label.lower();anchor=before.properties[row['existing_identity_anchor']];oldstate=before.states[anchor['material_state_id']]
        token='ewurum2025_'+key if pbs else 'abbasi2022_manure_phbv39'
        loc='Section2.8/Eq3;Section3.5/Table4' if pbs else 'Section2.2.5/Eq1;Section3.4/Table4'
        def ev(locator,*roles):return dict(source_id=sid,url=url,locator=locator,supports=list(roles))
        def unknown(note):return dict(status='not_reported_in_inspected_source',text=None,evidence=[ev(loc,'condition')],notes=note)
        def reported(text,note):return dict(status='reported',text=text,evidence=[ev(loc,'method','condition')],notes=note)
        state=deepcopy(oldstate);state.update(id='state_'+token+'_source_dsc_crystallinity',version='1.0.0',name=label+' source DSC normalization context',names={'en':label+' source DSC normalization context','zh':label+' 来源DSC归一化方法语境','ja':label+' 出典DSC正規化','de':label+' Quellen-DSC-Normierung'},aliases=[],property_ids=[])
        for field in state['state']:state['state'][field]=unknown('Actual selected Xc calculation-input specimen,history and pairing not established;no other-method facts transferred.')
        for field in ('composition_or_purity','reinforcement'):
            state['state'][field]=deepcopy(oldstate['state'][field])
            state['state'][field]['evidence']=[ev('Sections2.1-2.3;formulation '+label if pbs else 'Source material/extraction sections;Table4 PHBV-39 label','state')]
        state['state']['product_form']=dict(status='reported',text='Source DSC context of extruded PBS formulation' if pbs else 'Source purified manure-derived PHBV-39 sample',evidence=[ev(loc,'state')],notes='Common DSC method description,not confirmed actual Xc aliquot,phase,run or independent specimen. PHBV-39 is an operational-day label,not inferred39%HV.' if not pbs else 'Actual Xc aliquot and linkage to nominal DSC10mg,Tm/DeltaHm records,hot-pressed or injection-molded specimens unresolved.')
        state['source_scope']=label+' existing identity,source-reported DSC reference-normalization method context only. Not new material,independent specimen or actual input pairing. Source program/cycle claims are retained in derivation,not assigned as resolved physical history. No DMA,gel,density or tensile sample information transferred. R0 and grade holds remain.'
        state['evidence']=[ev(loc,'state')]
        p=deepcopy(anchor);p.update(id='refprop_'+token+'_source_dsc_crystallinity',version='1.0.0',material_state_id=state['id'],quantity=QUANTITY,quantity_dimension='dimensionless',source_property_label='Xc (%)',evidence_kind='published_measurement_derived_reference',determination_basis='source_reports_calculation',reporting_basis='reported_summary',summary_statistic='reported_value',density_basis=None,uncertainty=None,uncertainty_status='not_reported_in_inspected_source',uncertainty_note='Per-cell aggregation and numerical uncertainty unresolved;not mean/SD inferred from common replicates.',source_discrepancies=[])
        p['reported_value']=dict(kind='scalar',number=row['source_value_text'],value_text=row['source_value_text'],unit_code=UNIT,unit_text='%')
        for field in p['conditions']:p['conditions'][field]=[] if field=='additional_conditions' else unknown('Not established for selected Xc result;source scan program is not a single constant ambient condition or proof of actual cell input pairing.')
        p['conditions']['test_method']=reported('Author DSC enthalpy/reference normalization;'+row['normalization'],'Source-reported result only,no software arithmetic or author-math consistency check. Actual input linkage,baseline and corrections unresolved.')
        p['method_definition']=dict(type=METHOD,definition='Author-reported Xc reference-enthalpy normalization,not direct phase measurement or software recomputation.',extraction_window=None,evidence=[ev(loc,'method','classification')])
        reference='110.3' if pbs else '146'
        claims=[]
        if pbs:
            specs=[('reported_common_program','heating',2,'Section2.8 andFigure4 caption','Source second ramp/second-heating thermogram context,not an explicit assignment for each Xc cell.'),('reported_common_program','cooling',None,'Section2.8 DSC program','Source cooling to30C within shared program;selected Xc cooling occurrence not assigned.')]
        else:
            specs=[('reported_crystallinity_origin','cooling',1,'Section3.4 first-cooling Xc paragraph','Source explicitly says Xc of purified PHBV obtained from first cooling cycle.'),('reported_enthalpy_scan','heating',2,'Section2.2.5 DSC methods andEq1','Source method associates DeltaHf/endothermal peak with second heating and defines Xc using DeltaHf/DeltaHf0.')]
        for scope,phase,occurrence,cloc,text in specs:
            claims.append(dict(scope=scope,phase=phase,occurrence=occurrence,text=text,evidence=[ev(cloc,'condition','classification')],notes='Attributed source statement only;actual per-cell signal/calculation-input association is not resolved.'))
        cycle=dict(status='not_verified' if pbs else 'conflicting_source_statements',assignment_text=None,claims=claims,evidence=[ev(loc,'condition')],notes='Source shared program retained without per-cell Xc scan assignment.' if pbs else 'Retain first-cooling origin and second-heating/DeltaHf method tension. Do not select actual phase,erase statements or diagnose author error.')
        if not pbs:
            p['source_discrepancies']=[dict(description='Xc first-cooling statement versus second-heating/DeltaHf normalization method context',disposition='Keep both attributed source claims;actual per-cell integration signal and calculation inputs unresolved. Do not change25.8,choose phase or infer new experiment.',evidence=[ev(c['evidence'][0]['locator'],'source_discrepancy') for c in claims])]
        program='DSC-7,nominal10mg;30to150C at10C/min,coolto30C at-10C/min,secondramp150C at10C/min;calibration,pan,purge and actual-cell linkage unknown.' if pbs else 'Q200DSC,common4-6mg,TzeroAlpans,N2 50mL/min,indium/sapphire calibration;40C3min,heat180C at10C/min3min,cool-50C at-10C/min3min,cycle repeated. Actual per-cell input linkage unresolved.'
        attribution='Source Table4 author-reported PBS-lignin results;no proof of independent cell specimens or pairings.' if pbs else 'Section3.4 Table4 jointly contains Guho existing results and reanalyzed data;PHBV-39 Xc single-cell attribution unresolved. Not certified2022newindependent experiment.'
        repeat='No per-cell DSCXc independent n,aggregation or uncertainty established;no DMAtriplicate/mechanical count transferred.' if pbs else 'DSC method says duplicate;per-cell independent n and literature/reanalysis assignment unresolved. Do not infer n2 or same-run.'
        p['derivation']=dict(schema_version='1.0.0',profile_id=PROFILE,profile_version='1.0.0',executor='source_reported_only',formula_family='source_fraction_corrected_enthalpy_ratio' if pbs else 'source_enthalpy_ratio',reference_specific_enthalpy=dict(status='reported',number=reference,value_text=reference,unit_code=REFERENCE_UNIT,unit_text='J/g',evidence=[ev('Section2.8 Eq3 explanatory paragraph' if pbs else 'Section2.2.5 Eq1 explanatory paragraph','method','classification')],notes='Author-cited pure-crystalline reference forPBS[31].' if pbs else 'Author-cited pure-crystalline PHBV reference[27]. Not independently verified original citation,universal constant or measured sample enthalpy.'),cycle_assignment=cycle,reported_formula=reported('Source Eq3 Xc=DeltaHm/(f DeltaH0)x100' if pbs else 'Source Eq1 Xc=DeltaHf/DeltaHf0x100','Original source symbols retained;do not use these symbols to resolve actual per-cell heating/cooling input.'),reference_material_and_citation=reported('Source reference100%crystallinePBS110.3J/g,citation[31]' if pbs else 'Source pure crystalline PHBV146J/g,citation[27]','Reported author citation only,not independent confirmation of reference literature,composition-specific applicability or universal constant.'),fraction_factor_and_mass_basis=reported('Source f denotes weight fraction of polymer in formulation' if pbs else 'Source Eq1 has no explicit f factor','Actual per-cell f,denominator/dry mass basis and corrections unknown;no nominal-recipe completion or normalization. Absence of f does not certify dry basis.'),thermal_signal_and_cycle_claims=reported('Source DeltaHm melting-peak-area definition and common program retained;per-cell cycle assignment unresolved.' if pbs else 'Source explicitly reports first-cooling Xc origin alongside second-heating/DeltaHf method context;both claims retained.','Actual per-cell integration and calculation-input linkage unresolved;not wholly unreported or resolved phase.'),integration_baseline_and_corrections=unknown('Selected integration bounds,peak inclusion,baseline,cold-crystallization adjustments and mass corrections unresolved;no recomputation or inverse reconstruction.'),instrument_program_and_calibration=reported(program,'Common nominal source method,not an actual-cell trace,calibration certificate or proof of source result arithmetic.'),source_data_attribution=reported(attribution,'No actual specimen/run/batch linkage or new independent experiment inferred.'),replication_and_statistics=reported(repeat,'No mean/SD/CV,uncertainty propagation or independent sample count inferred.'),evidence=[ev(loc,'method','classification')],notes='Direct author-reported Table4 Xc value under source reference model. Not direct measured crystalline volume/mass fraction,software output,universal material constant or engineering allowable. References110.3/146 never interchanged.')
        p['basis_note']='Direct selected source Xc cell,classified as source-report of measured-input/reference-model calculation;no software evaluation of equation or arithmetic correction.'
        p['sample_count']=dict(value=None,relation='not_reported',scope='Selected Xc scalar;independent cell-level sample count unresolved',source_statement=repeat,evidence=[ev(loc,'condition')])
        p['evidence']=[ev(row['source_table']+' '+label+' row x Xc','reported_value','classification'),ev(loc,'method','condition')]
        source_path=next(Path(n) for n in frozen['external_files_sha256'] if (n.endswith('article-curl-r1.xml') if pbs else 'phbv' in n and n.endswith('article-r1.xml')))
        inspection='MainXML selected method/formula/Table4 Xc and source-cycle/provenance discussion;no newPDF or supplementary-figure visual inspection'
        p['source_document']=dict(url=url,revision=None,inspected_on='2026-11-12',sha256=sha(source_path),hash_status='recorded',hash_note=None,inspection_scope=inspection,inspection_status='selected_content_inspected')
        p['verification']=dict(source_inspection_scope=inspection,transcription_cross_check='completed',independent_scientific_review=False,raw_data_reanalysis=False)
        p['scope_note']=state['source_scope']+' Source-model normalization and phase/provenance boundaries retained;not absolute/volume crystallinity or cross-study comparability.'
        assert p['id'] not in before.properties and state['id'] not in before.states
        state['property_ids']=[p['id']];props.append(p);states.append(state)
    assert len(props)==len(states)==10
    data=deepcopy(before.data);data['reference_properties']['records'].extend(props);data['materials']['records'].extend(states);after=Database(data);after.validate_scientific_contracts()
    assert all(after.properties[k]==v for k,v in before.properties.items()) and all(after.states[k]==v for k,v in before.states.items())
    assert after.identities==before.identities and after.grades==before.grades and after.sources==before.sources
    write('NEW_PROPERTIES_R1.json',props);write('NEW_STATES_R1.json',states)
    write('VALIDATION_R1.json',dict(candidate_snapshot=after.snapshot,properties=len(after.properties),states=len(after.states),sources=len(after.sources),new_properties=10,new_contexts=10,old5740properties_unchanged=True,old5420states_unchanged=True,identities_grades_sources_unchanged=True,native_applied=False,installation='not_run',tests='not_run_candidate_graph_only'))
    print(json.dumps(dict(snapshot=after.snapshot,properties=len(after.properties),states=len(after.states),native_applied=False)))
if __name__=='__main__':main()
