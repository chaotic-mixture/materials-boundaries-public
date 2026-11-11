"""Map eight source thermal coordinates into separate TGA/DSC contexts without native writes."""
from pathlib import Path
from copy import deepcopy
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
IMPL=HERE.parent/'dtg-unknown-ordinal-implementation-r1';SOURCE=HERE.parent/'pbs-pbat-thermal-source-followup-r1'
sys.path.insert(0,str(ROOT))
from materials_boundaries.database import Database
from materials_boundaries.material_references import validate_material_catalog
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(n,obj):
    with (HERE/n).open('x',encoding='utf-8',newline='\n') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
    entry=IMPL/'REVIEW_IMPLEMENTATION_INPUTS_R1.json';review=read(IMPL/'INDEPENDENT_IMPLEMENTATION_REVIEW_R1.json')
    assert review['decision']=='approved' and review['review_inputs_sha256']==sha(entry)
    for field in ('repo_files_sha256','external_files_sha256','native_files_sha256'):
        for n,h in read(entry)[field].items():assert sha(Path(n) if field=='external_files_sha256' else ROOT/n)==h,n
    before=Database();assert before.snapshot=='921239866811e038708751232e0b1f97242fd80d72a9b726503d830c01f0e8c7'
    data=deepcopy(before.data);sid='mtibe_2022_pbs_pbat_lignin_zno';url='https://mdpi-res.com/d_attachment/polymers/polymers-14-05065/article_deploy/polymers-14-05065.pdf'
    def ev(locator,*tags):return dict(source_id=sid,url=url,locator=locator,supports=list(tags))
    def unknown(notes):return dict(status='not_reported_in_inspected_source',text=None,evidence=[],notes=notes)
    def reported(text,locator,tag='condition',notes=None):return dict(status='reported',text=text,evidence=[ev(locator,tag)],notes=notes)
    states={};properties=[]
    for fact in read(SOURCE/'SOURCE_FACTS_R1.json'):
        parent=before.states[fact['existing_state_id']];identity=before.identities[fact['existing_identity_id']]
        assert parent['identity_id']==identity['id'] and parent['grade_id'] is None
        tga=fact['source_column_label']=='Tmax';suffix='tga_single_major_loss' if tga else 'dsc_second_heating';key=parent['id']+'_'+suffix
        methodloc='PDF p5 section2.6.3;p7-8section3.3/Figure3/Table4' if tga else 'PDF p5section2.6.4;p8-9section3.3/Figure4/Table4'
        if key not in states:
            state=deepcopy(parent);state.update(id=key,version='1.0.0',name=identity['name']+' '+suffix,names={lang:identity['name']+' '+suffix for lang in ('en','zh','ja','de')},aliases=[],source_designation=fact['source_table_row_label']+';'+suffix,property_ids=[])
            state['state']['product_form']=unknown('Geometry,mass,cutting and physical origin of the selected thermal portion unspecified;general injection-moulded dog-bone and photocatalysis strips are not assigned as thermal specimen geometry.')
            state['state']['processing']=reported('Study-wide preparation:biopolymer drying80°C overnight;TE-30/600-11-40 twin-screw extrusion,L/D40:1,zones120–145°C;pelletization and80°C24h drying;source also describes injection-moulded dog-bones at120–145°C.','PDF p3section2.3',tag='state',notes='General formulation preparation context only. Actual selected thermal portion/cutting route and physical pairing to dog-bones or other tests unconfirmed;no specimen-specific injection history certified.')
            state['state']['temper_or_heat_treatment']=unknown('Thermal-piece-specific post-processing treatment/history not established;instrument scan program belongs to the property method and is not a confirmed prior cure or service temperature.')
            state['state']['conditioning']=unknown('Thermal-specific humidity,drying,storage and equilibrated moisture unspecified. Mechanical25°C48h conditioning and general pre-processing drying are not thermal-piece conditioning.')
            state['state']['orientation']=unknown('Thermal sampling direction and physical relation to moulding/processing axes unspecified;no isotropy claim.')
            state['state']['porosity']=unknown('Selected thermal-piece void fraction unreported;no zero-porosity inference.')
            state['source_scope']=identity['identity_scope']+' Source Table4 '+suffix+' context;not a new material or independent physical batch. Recipe and study-wide preparation retained as source context only;thermal geometry,cutting and cross-method physical pairing unknown. Thermal statistics and n unknown;no mechanical n5/25C48h transfer. Source Tmax unnumbered and Tm second-heating context remain distinct from cooling crystallization.'
            state['evidence'].append(ev(fact['source_cell_locator']+';'+methodloc,'state'));states[key]=state
        state=states[key];qty=fact['quantity_proposed'];label=fact['source_column_label']
        program='Room temperature to900°C at10°C/min under nitrogen' if tga else 'Source states two cycles;listed sequence:heat−60to200°C,coolto−60°C,heatto200°C;selected Tm from second heating'
        method='PerkinElmer thermogravimetric analyser,model unspecified;source Tmax associated with DTG/single major weight-loss event,not scan maximum or onset.' if tga else 'TA Instruments DSC-Q2000;source Tm in second-heating melting endotherm context,not onset/endset or cooling peak.'
        extra=[('thermal_scan_program',reported(program,methodloc,notes='Temperature coordinates and ramp are scan settings,not ambient temperature,conditioning or an operating envelope.')),
            ('heating_rate',reported('10°C/min',methodloc,notes='Source heating rate;cooling rate is not inferred.')),
            ('test_atmosphere',reported('Nitrogen',methodloc)),
            ('gas_flow',unknown('TGA numerical gas flow not reported;DSC25mL/min not transferred.') if tga else reported('25mL/min',methodloc,notes='DSC-specific source setting,not TGA flow.')),
            ('sample_mass',unknown('Selected thermal sample mass unreported.')),
            ('pan_and_calibration',unknown('Pan,baseline calibration and traceability details unreported.')),
            ('independent_batches',unknown('Independent batch count and cross-method physical pairing unconfirmed.')),
            ('source_unit_context',reported('°C supported by same-article method and figure axes;Table4 header has no printed unit.',fact['unit_evidence_locator'],notes='Values are direct Table4 literals,not graph digitization;not falsely attributed to a printed table-header unit.'))]
        if not tga:extra.extend([('selected_scan',reported('Second heating',methodloc)),('cooling_rate',unknown('Cooling rate not separately stated;do not infer−10°C/min.')),('cycle_count_scope',reported('Source wording:two cycles;listed heat/cool/reheat sequence retained',methodloc,notes='Not two independent specimens,n2 or a manufactured further cooling stage.'))])
        scope='Retained officialPDF p1license,p3recipe,p5methods,p7-9Table4/Figures3-4 and identical EuropePMC XML. Table header units absent;same-document methods/axes support Celsius. No raw curve analysis or latest-notice completeness certification.'
        p=dict(id=parent['id'].replace('state_','refprop_',1)+'_'+qty,version='1.0.0',material_state_id=state['id'],quantity=qty,quantity_dimension='temperature',source_property_label=label,
            reported_value=dict(kind='scalar',number=fact['number'],value_text=fact['number'],unit_code='degC',unit_text='°C'),evidence_kind='published_experimental_reference',reporting_basis='not_stated',determination_basis='source_reports_measurement',
            basis_note='Selected Table4 '+label+' cell. Central aggregation,uncertainty and contributing n unspecified. Celsius unit context comes from the same article methods/axes/prose,not the table header;no curve refit or temperature conversion.',
            conditions=dict(temperature=unknown('Separate numerical ambient test temperature unreported;scanned temperature program is kept separately,not filled from mechanical25°C.'),test_standard=unknown('No thermal standard/edition independently assigned;ASTM D638 belongs to tensile method.'),test_method=reported(method,methodloc,notes='Differentiation,smoothing/baseline and precise peak-picking implementation unknown.'),direction=unknown('Thermal sampling orientation unreported.'),conditioning=unknown('Thermal-piece RH,equilibration and storage unreported;no mechanical48h conditioning transfer.'),loading_rate=dict(status='not_applicable',text=None,evidence=[],notes='Mechanical loading rate is not the thermal scan heating rate.'),additional_conditions=[dict(name=n,fact=f) for n,f in extra]),
            density_basis=None,summary_statistic='not_stated',uncertainty=None,uncertainty_status='not_reported_in_inspected_source',uncertainty_note='No selected-cell uncertainty or statistical estimator reported;not zero dispersion,no SD/SE/CI or mechanical plus-minus transfer.',
            sample_count=dict(value=None,relation='not_reported',scope='Selected thermal-cell contributing measurements/specimens and independent batches unknown.',source_statement='Thermal methods give no selected-cell n;mechanical five specimens and DSC cycle sequence are not statistical counts for this result.',evidence=[]),
            method_definition=dict(type='source_reported_conventional',definition=method+' '+program+'. Source cell transcribed,not recomputed;exact extraction algorithm and aggregation unknown.',extraction_window=None,evidence=[ev(methodloc,'method','classification')]),
            source_discrepancies=[dict(description='Table4 temperature-column headers omit units;Celsius context is supplied by same-article methods,axes and prose.',disposition='Retain direct numerical literal and explicit unit provenance;do not claim a printed header unit or digitize/refit curves.',evidence=[ev(fact['source_cell_locator']+';'+fact['unit_evidence_locator'],'source_discrepancy')])],
            source_id=sid,evidence=[ev(fact['source_cell_locator'],'reported_value','classification'),ev(fact['unit_evidence_locator'],'method','condition')],
            source_document=dict(url=url,revision='Reacquired official PDF byte-identical to retained version;latest revision/notices unverified',inspected_on='2026-11-11',sha256='fa72f3441329d8db6348926906817ebac7b3bd7077a90e836f75f8ecdb087287',hash_status='recorded',hash_note=None,inspection_scope=scope,inspection_status='selected_content_inspected'),
            scope_note='Source-qualified '+fact['source_table_row_label']+' '+label+' thermal coordinate. Not an operating/service limit or independent batch. Centre,uncertainty,n,thermal sample mass/geometry,conditioning,calibration and original peak extraction unknown. Recipe70/30 basis and1.5ZnO denominator remain unresolved,not normalized. No Tg,ambiguous Tcc,enthalpy or neatPBAT thermal value imported;no mechanical-statistic transfer or raw curve reconstruction.',evaluation_support='catalog_only',universal_bound=False,engineering_allowable=False,
            verification=dict(source_inspection_scope=scope,transcription_cross_check='completed',independent_scientific_review=False,raw_data_reanalysis=False))
        if tga:p['degradation_peak_ordinal']=dict(status='not_reported_in_inspected_source',value=None,evidence=[ev(fact['source_cell_locator']+';PDF p7-8section3.3/Figure3b','condition')],notes='Source labels the selected single-major-event coordinate Tmax without a numbered peak. No ordinal1 or rank inferred;minor events are not denied.')
        assert p['id'] not in before.properties
        properties.append(p);state['property_ids'].append(p['id'])
    proposal=read(SOURCE/'SOURCE_UPDATE_PROPOSAL_R1.json');assert before.sources[sid]==proposal['before']
    after_source=deepcopy(proposal['after']);after_source['claim_notes'].append('Frozen concrete mapping adds separate source-qualifiedTGA/DSC contexts for eightTable4 facts,not new identities. Tmax ordinal explicitlynull with inspected-source evidence;mechanical counts/conditioning and DSCflow/cycles not transferred across methods. General preparation is study context only,thermal-piece geometry/pairing unknown. Mapping is not actual native admission;later exact receipt controls.')
    data['materials']['records'].extend(states.values());data['reference_properties']['records'].extend(properties);data['sources']['records']=[after_source if x['id']==sid else x for x in data['sources']['records']]
    validate_material_catalog(*(data[n] for n in ('materials','reference_properties','sources')));after=Database(data)
    assert all(after.properties[k]==v for k,v in before.properties.items()) and all(after.states[k]==v for k,v in before.states.items())
    assert before.identities==after.identities and before.grades==after.grades
    assert len(properties)==len(states)==8 and len(after.properties)==5494 and len(after.states)==5297 and len(after.sources)==134
    write('NEW_PROPERTIES_R1.json',properties);write('NEW_STATES_R1.json',list(states.values()));write('SOURCE_UPDATE_R1.json',dict(before=before.sources[sid],after=after_source,changed_fields=['claim_notes'],native_applied=False))
    write('VALIDATION_R1.json',dict(baseline_snapshot=before.snapshot,candidate_snapshot=after.snapshot,properties=len(after.properties),states=len(after.states),sources=len(after.sources),new_properties=8,new_context_states=8,new_identities=0,new_grades=0,new_sources=0,old5486properties_unchanged=True,old5289states_unchanged=True,identities_grades_unchanged=True,native_applied=False,installation='not_run'))
    print(json.dumps(dict(snapshot=after.snapshot,properties=len(after.properties),states=len(after.states),native_applied=False)))
if __name__=='__main__':main()
