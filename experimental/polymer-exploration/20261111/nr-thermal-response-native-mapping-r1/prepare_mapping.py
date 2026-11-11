"""Prepare four unapplied source-qualified time facts and two context states."""
from pathlib import Path
from copy import deepcopy
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
IMPL=HERE.parent/'nr-thermal-response-contract-implementation-r1';SOURCE=HERE.parent/'nr-notice-damping-source-followup-r1'
sys.path.insert(0,str(ROOT))
from materials_boundaries.database import Database
from materials_boundaries.material_references import validate_material_catalog
from materials_boundaries._material_derivation import FIT_PROFILE,FIT_METHOD,FIT_EXPRESSION,FIT_UNKNOWNS
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(n,obj):
    with (HERE/n).open('x',encoding='utf-8',newline='\n') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
    entry=IMPL/'REVIEW_IMPLEMENTATION_INPUTS_R1.json';review=read(IMPL/'INDEPENDENT_IMPLEMENTATION_REVIEW_R1.json')
    assert review['decision']=='approved' and review['review_inputs_sha256']==sha(entry)
    for field in ('repo_files_sha256','native_files_sha256','external_files_sha256'):
        for n,h in read(entry)[field].items():assert sha(Path(n) if field=='external_files_sha256' else ROOT/n)==h,n
    before=Database();assert before.snapshot=='54b06dfa38f09e3a65f79522674f554115953a991008b49c2f6770ed84fc8275'
    data=deepcopy(before.data);parent=before.states['state_smr10_bianchi2025_nr'];template=before.properties['refprop_smr10_bianchi2025_nr_thermal_conductivity']
    primary=template['source_id'];url=template['source_document']['url']
    added_source=read(SOURCE/'METHOD_SOURCE_PROPOSAL_R1.json')['proposed_source'];secondary=added_source['id'];method_url=added_source['urls'][-1]
    assert secondary not in before.sources and not any((s.get('doi') or '').lower()==added_source['doi'].lower() for s in before.sources.values())
    proposal=read(SOURCE/'SOURCE_UPDATE_PROPOSAL_R1.json');assert before.sources[primary]==proposal['before']
    def ev(where,*tags,sid=primary,doc=url):return dict(source_id=sid,url=doc,locator=where,supports=list(tags))
    def unknown(note):return dict(status='not_reported_in_inspected_source',text=None,evidence=[],notes=note)
    def reported(text,where='PDF pp19-20 section3.3.5',tag='condition',notes=None):return dict(status='reported',text=text,evidence=[ev(where,tag)],notes=notes)
    states={};properties=[]
    for regime in ('natural_convection','forced_convection'):
        forced=regime=='forced_convection';state=deepcopy(parent)
        state.update(id='state_smr10_bianchi2025_nr_thermal_response_'+regime,version='1.0.0',name='Study NR thermal-response '+regime,names={
            'en':'Study NR thermal-response '+regime,'zh':'研究NR温度响应：'+('强制对流' if forced else '自然对流比较'),'ja':'研究NR温度応答：'+('強制対流' if forced else '自然対流比較'),'de':'Studien-NR Temperaturantwort:'+('erzwungene Konvektion' if forced else 'Vergleich natürliche Konvektion')},aliases=[],source_designation='NR '+regime.replace('_',' '),property_ids=[])
        if forced:
            state['state']['product_form']=reported('Initial rectangular caloric specimens45 ×15 ×1mm³;25mm nominal gauge',tag='state',notes='Dimensions before deformation;phase-specific deformed geometry and physical linkage to other test specimens unknown.')
            state['state']['conditioning']=unknown('Caloric specimen humidity,drying,storage and post-cure interval unspecified;precycles are property method facts,not humidity conditioning.')
            state['state']['orientation']=unknown('Tensile axis relative to sheet processing direction unspecified;no isotropy claim.')
            state['source_scope']='Same-paper study NR formulation/grade context,forced-convection caloric strips. Initial geometry and current protocol reported;not proof of same physical samples as LFA,hardness or quasi-static states. Phase qualifiers describe fitted responses,not independent materials or additional tested specimens.'
            state['evidence'].append(ev('PDF pp19-20 section3.3.5','state'))
        else:
            state['state']={key:unknown('Natural-control-specific '+key+' is not independently assigned from the current forced protocol or2024article. Same-paper NR designation is reference identity context only;physical sample/batch lineage unknown.') for key in parent['state']}
            state['state']['reinforcement']=reported('Source-labelled unfilled NR comparison,no nanoclay assigned to selected label','PDF p15 Table6 NR natural convection',tag='state',notes='Source designation,not independent compositional analysis or batch certification.')
            state['source_scope']='Source-labelled2025 NR natural-convection comparison context only,associated with existing study NR identity/grade by same-paper designation. Natural-control-specific formulation/batch,processing,cure,geometry,temperature,strain/wait/precycle settings and physical lineage are not independently assigned from forced samples or2024paper. No new identity or independent replication claimed.'
            state['evidence']=[ev('PDF p15 Table6 NR natural convection','state')]
        states[regime]=state
    for fact in read(SOURCE/'THERMAL_DAMPING_CANDIDATES_R1.json'):
        regime=fact['convection_regime'];forced=regime=='forced_convection';state=states[regime];phase=fact['thermal_response_phase'];p=deepcopy(template)
        p.update(id='refprop_smr10_bianchi2025_nr_thermal_response_'+regime+'_'+phase,material_state_id=state['id'],quantity='thermal_response_characteristic_time',quantity_dimension='time',source_property_label='Characteristic time of temperature dampening,tau_c,'+fact['source_phase_label'])
        p['reported_value']=dict(kind='scalar',**fact['reported_value'])
        p['uncertainty'].update(number=fact['reported_plus_minus']['number'],value_text=fact['reported_plus_minus']['value_text'],unit_code='s',unit_text='s',scope='Table6 plus-minus amplitude;thermal fit/aggregate dispersion meaning unspecified,not mechanical SD or a reference-example fit standard error.',evidence=[ev(fact['source_cell_evidence']['locator'],'uncertainty')])
        p['uncertainty_note']='Meaning of thermal time plus-minus and source aggregation order unknown;no mechanical SD/mean or reference-example coefficient error transfer.'
        p['summary_statistic']='not_stated';p['uncertainty_status']='reported_plus_minus_unspecified'
        p['basis_note']='Source-reported fit-derived1/e temperature-deviation time with explicit delegated method. Geometry/convection-dependent response descriptor,not intrinsic mechanical relaxation or full cycle duration.'
        p['thermal_response_phase']=dict(code=phase,evidence=[ev(fact['source_cell_evidence']['locator'],'condition')],notes='Source '+fact['source_phase_label']+' column;post-action temperature response,not duration of rapid mechanical loading or a separate independent specimen.')
        p['thermal_convection']=dict(status='reported',regime=regime,evidence=[ev('PDF p15 Table6 '+fact['source_designation'],'condition')],notes='Source regime label only;actual flow field/velocity and uniform transfer coefficient unverified.')
        p['conditions']=dict(temperature=reported('22 °C') if forced else unknown('Natural-control test temperature not separately assigned;no transfer of forced22C,LFA20C,mechanical25C or2024conditions.'),
            test_standard=unknown('No separate standard or edition reported for this caloric time fit;mechanical/LFA standards not transferred.'),
            test_method=reported('STEP Lab XUD05,1kN;IRtech Fotric348A16fps,emissivity0.9,camera50cm;AnalyzIR5.0.7.117 point-temperature acquisition;source fit method delegated toReference10.' if forced else 'Table6 natural-convection NR comparison;fit definition delegated through2025section3.3.5 to2024Reference10. Natural-control-specific apparatus/acquisition settings not assigned.',where='PDF pp19-20 section3.3.5 andp15Table6',notes='Model-definition citation only;current fit window,solver/weighting,baseline treatment and aggregation unknown.'),
            direction=unknown('Response/loading direction relative to processing and temperature observation ROI/cross-section distribution unverified.'),
            conditioning=unknown('Humidity,drying,storage and post-cure interval unspecified for selected response.'),
            loading_rate=reported('0.5m/s loading and unloading crosshead speed',notes='Preparatory rapid mechanical action,not fitted thermal decay rate or verified specimen strain rate.') if forced else unknown('Natural-control loading/unloading speed not independently assigned from forced or2024method.'),additional_conditions=[])
        items=[('reference_definition',reported('1/e absolute specimen-to-fluid temperature-deviation decay;source delegates reference method','PDF p20 section3.3.5 final sentence/Reference10',notes='Method-reference assumptions are not certification of actual constant fluid temperature,uniform h or negligible radiation.')),
            ('current_fit_settings',unknown('Actual raw curves,fit interval,solver/weights,baseline temperature handling and fit/aggregate order unknown.')),
            ('test_relative_humidity',unknown('Selected thermal-response RH unspecified.')),
            ('independent_batches',unknown('No certified independent batch count or cross-paper replication assigned.'))]
        for key,text in [('imposed_strain','400%'),('post_stretching_hold','60s'),('post_retraction_recovery','60s'),('method_tested_specimens','Two tested specimens per formulation'),('pre_stretch_cycles_per_specimen','Three pre-stretches per specimen'),('fan_settings','2.5W fan positioned50cm from specimen'),('infrared_settings','Source resolution0.1C;16fps;emissivity0.9;camera50cm')]:
            items.append((key,reported(text,notes='Current forced method fact;not per-cell n,independent repetitions,air velocity,fit uncertainty or a transferred2024condition.') if forced else unknown('Natural-control-specific '+key+' not separately assigned;current forced and2024protocols not transferred.')))
        p['conditions']['additional_conditions']=[dict(name=n,fact=f) for n,f in items]
        p['sample_count']=dict(value=None,relation='not_reported',scope='Per-cell fitted/aggregated time count unknown;method specimens and precycles are not fit n or independent batches.',source_statement='Current forced method reports2specimens/formulation and3precycles/specimen;not assigned to each Table6 cell.' if forced else 'Natural-control-specific specimen/fit count not separately established;forced2 and reference-paper counts not transferred.',evidence=[ev('PDF pp19-20 section3.3.5','sample_count')] if forced else [])
        p['method_definition']=dict(type=FIT_METHOD,definition='Source-fitted thermal-response1/e time;2025source explicitly delegates method to2024Reference10. Model definition only,no current raw fit reconstruction or numerical table transfer.',extraction_window=None,evidence=[ev('PDF p20 section3.3.5 final sentence/Reference10;p15Table6','method','classification')])
        method_sha='e41c84742ae2e31f49ed03d7805bd9d4d2c39547715ab053eb85261f786c87cb'
        p['derivation']=dict(schema_version='1.0.0',profile_id=FIT_PROFILE,profile_version='1.0.0',kind='source_reported_temperature_response_fit',model=FIT_EXPRESSION,definition='absolute_temperature_deviation_to_fluid_decays_to_initial_divided_by_e',
            primary_delegation=dict(primary_doi=before.sources[primary]['doi'],cited_source_id=secondary,cited_doi=added_source['doi'],cited_document_url=method_url,cited_document_sha256=method_sha,evidence=[ev('PDF p20 section3.3.5 final sentence andReference10','method')]),
            method_reference=dict(source_id=secondary,doi=added_source['doi'],url=method_url,sha256=method_sha,inspected_on='2026-11-11',inspection_scope='Selected2024PDFp1license,p8definition/Equation5 only;pp11/19contradictory tables held. No reference numerical values,250s protocol,fit-example coefficients/SE or Bi judgment transferred.',use_role='method_definition_only_not_current_protocol_or_numeric_input',evidence=[ev('PDF p8 section2.3.4 definition/Equation5/fitting paragraph','method',sid=secondary,doc=method_url)]),
            model_context=dict(fluid_temperature='reference_model_assumes_constant',heat_transfer_coefficient='reference_model_assumes_uniform_constant',radiation='reference_model_neglects_radiation',actual_applicability_certified=False),
            unverified_fit_inputs={**{k:None for k in FIT_UNKNOWNS},'unknown_scope_note':'Current raw curves,fit window,optimizer/weights,baseline treatment,fit aggregation and per-cell fit count unverified. Model assumptions are cited context only;no reference-paper fit settings or numerical coefficients imported.'},software_fit_performed=False,software_inverse_performed=False)
        p['source_discrepancies']=[]
        p['evidence']=[ev(fact['source_cell_evidence']['locator'],'reported_value','classification')]
        scope='Selected same-byte2025PDFp15Table6,pp19-20method andReference10;method definition separately inspected in2024PDFp8. No source curve refit or latest-notice completeness certification.'
        p['source_document']['inspection_scope']=scope;p['verification']['source_inspection_scope']=scope
        p['scope_note']='Source-qualified fit-derived time for named phase and convection boundary. Not intrinsic mechanical relaxation,half-life or cycle duration. Centre estimator,plus-minus meaning,per-cell n,fit settings,raw curves,aggregation and independent batches unknown. Natural-control physical/protocol lineage not inferred from forced samples or2024article. No software fit,inverse,source-table repair or engineering allowable.'
        properties.append(p);state['property_ids'].append(p['id'])
    data['materials']['records'].extend(states.values());data['reference_properties']['records'].extend(properties)
    data['sources']['records']=[proposal['after'] if s['id']==primary else s for s in data['sources']['records']]+[added_source]
    validate_material_catalog(*(data[n] for n in ('materials','reference_properties','sources')))
    after=Database(data)
    assert all(after.properties[k]==v for k,v in before.properties.items()) and all(after.states[k]==v for k,v in before.states.items())
    assert before.identities==after.identities and before.grades==after.grades
    write('NEW_PROPERTIES_R1.json',properties);write('NEW_STATES_R1.json',list(states.values()));write('SOURCE_UPDATE_R1.json',proposal);write('NEW_METHOD_SOURCE_R1.json',added_source)
    write('VALIDATION_R1.json',dict(baseline_snapshot=before.snapshot,candidate_snapshot=after.snapshot,properties=len(after.properties),states=len(after.states),sources=len(after.sources),new_properties=4,new_context_states=2,new_material_identities=0,old5416properties_unchanged=True,old5263states_unchanged=True,identities_grades_unchanged=True,native_applied=False,installation='not_run'))
    print(json.dumps(dict(candidate_properties=len(after.properties),candidate_states=len(after.states),candidate_sources=len(after.sources),snapshot=after.snapshot,native_applied=False)))
if __name__=='__main__':main()
