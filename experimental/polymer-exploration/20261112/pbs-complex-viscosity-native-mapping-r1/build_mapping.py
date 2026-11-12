"""Review-only source rheology mapping; no fits or unit/frequency conversion."""
from pathlib import Path
from copy import deepcopy
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from materials_boundaries.database import Database,read_snapshot
from materials_boundaries.material_references import validate_material_catalog
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(n,v):
    with (HERE/n).open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
    proposal=HERE.parent/'pbs-complex-viscosity-source-proposal-r1';impl=HERE.parent/'complex-viscosity-implementation-r1'
    for folder,entry,receipt in [(proposal,'REVIEW_INPUTS_R1.json','INDEPENDENT_SOURCE_REVIEW_R1.json'),(impl,'REVIEW_IMPLEMENTATION_INPUTS_R1.json','INDEPENDENT_IMPLEMENTATION_REVIEW_R1.json')]:
        r=read(folder/receipt);assert r['decision']=='approved' and r['review_inputs_sha256']==sha(folder/entry)
        for group in ['repo_files_sha256','external_files_sha256','native_files_sha256']:
            for n,h in read(folder/entry)[group].items():assert sha(Path(n) if group=='external_files_sha256' else ROOT/n)==h,n
    db=Database();assert db.snapshot=='d2062c34b747e03fc4affc2998e25a7f69e362fef2f98503e0b50433b662b177'
    facts=read(proposal/'SOURCE_FACTS_R1.json');source=facts['source_id'];url=facts['primary_url'];assert url in db.sources[source]['urls']
    method='Section2.6 rheology/Equation2;Section3.3 and Table2;PDFpp4/7 selected method and result cells'
    def ev(loc,*roles):return [dict(source_id=source,url=url,locator=loc,supports=list(roles))]
    def unknown(note,role='condition'):return dict(status='not_reported_in_inspected_source',text=None,evidence=ev(method,role),notes=note)
    def known(text,note):return dict(status='reported',text=text,evidence=ev(method,'method','condition'),notes=note)
    scope='Source-reported oscillatory complex-viscosity magnitude at a Table2 cyclic-frequency coordinate. Not steady-shear viscosity,zero-shear limit,real/imaginary component,Cox-Merz substitution or model evaluation. No same aliquot,run,batch or preparation equivalence with DSC,DMA,TGA or mechanical specimens;two frequencies are not n2.'
    states={};props=[]
    for row in facts['candidates']:
        label=row['source_label'];frequency=row['cyclic_frequency']['number'];assert frequency in ['1','30']
        key=label.lower();sid=f'state_ewurum2025_{key}_melt_oscillatory_rheology';pid=f'refprop_ewurum2025_{key}_complex_viscosity_{frequency}hz'
        if sid not in states:
            old=db.states[row['identity_anchor_state_id']];assert old['identity_id']==row['identity_id'];state=deepcopy(old)
            names=dict(en=label+' PBS-based source formulation,parallel-plate melt rheology',zh=label+'来源PBS基配方，平行板熔体流变上下文',ja=label+'出典PBS系配合、平行板溶融レオロジー',de=label+' PBS-basierte Quellrezeptur,Parallelplatten-Schmelzrheologie')
            state.update(id=sid,version='1.0.0',name=names['en'],names=names,aliases=[],source_designation=label+' Table2 oscillatory rheology',property_ids=[],source_scope=scope,evidence=ev('Sections2.1to2.3 formulation '+label+';'+method,'state'))
            for field in state['state']:
                if field not in ['processing','composition_or_purity','reinforcement']:state['state'][field]=unknown('Rheology-specific '+field+' not established; no DSC thermal history or other-method specimen facts transferred.','state')
            state['state']['product_form']=dict(status='reported',text='Source polymer melt during parallel-plate dynamic rheology;source supplies25mm diameter x2.0mm dimensions',evidence=ev(method,'state'),notes='Actual gap versus sample thickness,loading route and rheometer aliquot preparation not independently resolved;not a DSC aliquot or mechanical specimen.')
            state['state']['processing']['notes']='Common source extrusion background only; actual rheometer aliquot preparation,pressing,loading and thermal residence unknown. No DSC thermal program or mechanical injection-molding route assigned.'
            state['state']['temper_or_heat_treatment']=unknown('Prior rheometer heating,thermal dwell,pre-shear and actual residence history unspecified;140C test condition recorded separately,not a complete preparation schedule.','state')
            states[sid]=state
        states[sid]['property_ids'].append(pid)
        p=deepcopy(db.properties[f'refprop_ewurum2025_{key}_dsc_melting_enthalpy']);p.pop('dsc_enthalpy_definition')
        p.update(id=pid,version='1.0.0',material_state_id=sid,quantity='oscillatory_complex_viscosity_magnitude',quantity_dimension='pressure_time',source_property_label='Complex viscosity eta* at '+frequency+'Hz',reported_value=dict(kind='scalar',value_text=row['number'],number=row['number'],unit_text='kPa.s',unit_code='kPa_s_complex_viscosity'),evidence_kind='published_experimental_reference',reporting_basis='reported_summary',determination_basis='source_reports_measurement',density_basis=None,summary_statistic='reported_value',uncertainty=None,uncertainty_status='not_reported_in_inspected_source',uncertainty_note='No numerical amplitude printed for selected eta* cell; n/R2 fit columns are not uncertainties or specimen counts.',basis_note='Table2 direct source result column,not K/n model evaluation or an evaluator calculation. Equation2 absolute notation supports magnitude; source extraction/averaging procedure unknown. Preserve kPa.s without scaling.')
        p['conditions']=dict(temperature=known('140C source rheological measurement temperature','Nominal reported condition; actual sensor record,thermal equilibration and residence unknown.'),test_standard=unknown('No rheology-specific standard named in inspected method; mechanical standards not transferred.'),test_method=known('Bohlin CVO100NF parallel-plate oscillatory rheometry,source25mm diameter x2.0mm dimensions,0.025% strain,0.01to100Hz sweep','Dimensions do not certify actual gap;strain value does not certify LVR or peak/RMS convention;individual extraction procedure unknown.'),direction=unknown('Rheology-specific sample orientation and flow/sampling history unspecified; scalar magnitude does not establish isotropy or direction inapplicability.'),conditioning=unknown('Drying,RH,storage,pre-shear and thermal-equilibration details for rheology aliquots unknown.'),loading_rate=dict(status='not_applicable',text=None,evidence=[],notes='Mechanical crosshead loading rate is not this oscillatory protocol;cyclic frequency is a separate typed source coordinate.'),additional_conditions=[])
        p['oscillation_frequency']=dict(status='reported',number=frequency,value_text=frequency,unit_code='Hz',unit_text='Hz',evidence=ev(row['source_locator'],'condition','classification'),notes='Explicit Table2 cyclic-frequency column;not shear rate or converted angular frequency. No replicate count or same physical run inferred.')
        p['complex_viscosity_definition']=dict(basis='source_reported_oscillatory_complex_viscosity_magnitude',rheometer_and_geometry=known('Bohlin CVO100NF parallel-plate rheometer;source25mm diameter x2.0mm dimensions','Plate surface,actual gap versus sample thickness,loading,sealing and normal force unspecified.'),temperature_control=known('140C source nominal measurement temperature','Actual calibration,thermal ramp,hold,equilibration and atmosphere not supplied.'),strain_amplitude=known('0.025% source strain','Peak/RMS convention,amplitude-sweep evidence and linear-viscoelastic regime not certified.'),frequency_protocol=known('Source0.01to100Hz sweep,with printed parenthetical0.0628to628rad/s range','Selected coordinates remain Table2 Hz;no point conversion,order,dwell,sampling or independent-run inference.'),measurement_and_reduction=known('Source reports measured eta*;Table2 first two columns at1/30Hz are distinct from K,n,R2 fitted-parameter columns;Eq2 uses absolute complex-viscosity notation','Bohlin rheologyv6.51.0.3 andExcel support source power-law analysis background only;raw point extraction/averaging unknown. Do not evaluate fit or infer steady-shear/real/imaginary values.'),sample_preparation_conditioning=unknown('Actual rheometer aliquot fabrication,drying,storage,RH,pre-shear and thermal residence unknown;common extrusion is identity/preparation background only.'),replicate_and_piece_relationship=unknown('Per-frequency specimen,run and independent-batch counts and sharing unknown. Table n is flow exponent,not specimen n;two frequencies not n2.'),instrument_corrections=unknown('Slip,edge,inertia,compliance,normal-force,geometry and instrument correction procedures not supplied.'),evidence=ev(method,'method','condition'),notes=scope)
        p['sample_count']=dict(value=None,relation='not_reported',source_statement='No unambiguous per-cell rheology contributor count;Table2 n is flow-behavior fit exponent,not sample count. Frequencies not specimens;DMAtriplicate not transferred.',scope=label+' selected eta* cell only;aliquot,run and independent-batch counts unknown.',evidence=ev(method,'sample_count'))
        p['method_definition']=dict(type='source_reported_conventional',definition='Source-reported oscillatory complex-viscosity magnitude;140C,0.025% strain,parallel plates and source frequency sweep. No fit evaluation or steady-shear equivalence.',extraction_window=None,evidence=ev(method,'method','condition','classification'))
        p['evidence']=ev(row['source_locator'],'reported_value','classification')+ev(method,'method','condition','classification');p['source_discrepancies']=[]
        inspection='Primary retained XML Table2/Sections2.6,3.3/Equation2 and same-byte publisher PDFpp4/7 selected method/result cells inspected. Selected18 value/frequency cells only;unselected K,n,R2 equivalence,raw traces,full standards and latest-notice completeness not certified.'
        p['source_document'].update(url=url,sha256=facts['primary_xml_sha256'],inspected_on='2026-11-12',revision='Retained primary XML;formal revision and latest notices not independently verified.',inspection_scope=inspection)
        p['verification']['source_inspection_scope']=inspection;p['scope_note']=scope+' n,center estimator,uncertainty and exact reduction details unknown.';props.append(p)
    assert len(props)==18 and len(states)==9
    data=deepcopy(db.data);data['materials']['records'].extend(states.values());data['reference_properties']['records'].extend(props)
    validate_material_catalog(*(data[n] for n in ['materials','reference_properties','sources']));after=Database(data)
    assert after.identities==db.identities and after.grades==db.grades and after.sources==db.sources
    assert all(after.properties[k]==v for k,v in db.properties.items()) and all(after.states[k]==v for k,v in db.states.items())
    ext=ROOT.parent/'open-database-evidence/polymer-pbs-complex-viscosity-mapping-20261112-r1';ext.mkdir(exist_ok=False);groups=[]
    for name,filters,count in [('viscosity-eighteen',dict(quantity='oscillatory_complex_viscosity_magnitude'),18),('source-all',dict(source=source),len(list(db.records(source=source)))+18),('enthalpy-nine',dict(source=source,quantity='dsc_reported_melting_specific_enthalpy'),9)]:
        rows=list(after.records(**filters));assert len(rows)==count;after.export(ext/name,**filters);assert read_snapshot(ext/name)[1]=={r['record_id']:r for r in rows};groups.append(dict(name=name,records=count,full_export_exact=True))
    write('NEW_STATES_R1.json',list(states.values()));write('NEW_PROPERTIES_R1.json',props);write('VALIDATION_R1.json',dict(snapshot=after.snapshot,properties=len(after.properties),states=len(after.states),sources=len(after.sources),new_properties=18,new_contexts=9,new_identities=0,new_sources=0,all_old_properties_and_states_unchanged=True,exports=groups,native_changed=False,installed=False))
    print(json.dumps(dict(snapshot=after.snapshot,properties=len(after.properties),states=len(after.states),native_changed=False)))
if __name__=='__main__':main()
