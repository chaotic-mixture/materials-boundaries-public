"""Review-only DSC enthalpy mapping; reuse method contexts without specimen claims."""
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
    proposal=HERE.parent/'pbs-melting-enthalpy-source-proposal-r2';impl=HERE.parent/'dsc-enthalpy-implementation-r1'
    for folder,entry,receipt in [(proposal,'REVIEW_INPUTS_R2.json','INDEPENDENT_SOURCE_REVIEW_R2.json'),(impl,'REVIEW_IMPLEMENTATION_INPUTS_R1.json','INDEPENDENT_IMPLEMENTATION_REVIEW_R1.json')]:
        r=read(folder/receipt);assert r['decision']=='approved' and r['review_inputs_sha256']==sha(folder/entry)
        for group in ['repo_files_sha256','external_files_sha256','native_files_sha256']:
            for n,h in read(folder/entry)[group].items():assert sha(Path(n) if group=='external_files_sha256' else ROOT/n)==h,n
    corroboration=read(HERE.parent/'pbs-enthalpy-pdf-corroboration-r1/PDF_READBACK_R1.json')
    for n,h in corroboration['external_files_sha256'].items():assert sha(Path(n))==h,n
    db=Database();assert db.snapshot=='f702a8c5b0d6de2592a262b440a76f30d5d4bbe41ec179754cd73fcf8836a40c'
    source='ewurum_mcdonald_2025_pbs_lignin';facts=read(proposal/'SOURCE_FACTS_R1.json');url=facts['primary_url']
    method='Section2.8 DSC paragraph and equation3 explanation;Section3.5/Figure4 shared second-heating context;Table4 DeltaHm'
    def ev(loc,*roles):return [dict(source_id=source,url=url,locator=loc,supports=list(roles))]
    def unknown(note):return dict(status='not_reported_in_inspected_source',text=None,evidence=ev(method,'condition'),notes=note)
    def known(text,note):return dict(status='reported',text=text,evidence=ev(method,'method','condition'),notes=note)
    program='30to150C at10C/min,cool to30C at-10C/min,then second ramp to150C at10C/min;hold durations unknown'
    scope='Source Table4 DeltaHm from calorimetric peak area. Shared extruded DSC method context only,not proof of same aliquot,run,scan or batch as Tm. Second heating is shared Figure4/discussion context,not per-cell certification. Exact included peaks,mass basis,baseline,limits,sign convention,n and uncertainty unknown; no Xc conversion or110.3J/g reference assigned as measurement.'
    props=[];revisions=[]
    for row in facts['candidates']:
        label=row['source_label'];oldstate=db.states[row['existing_dsc_state_id']];assert oldstate['identity_id']==row['identity_id'] and oldstate['version']=='1.0.0'
        state=deepcopy(oldstate);pid=f'refprop_ewurum2025_{label.lower()}_dsc_melting_enthalpy'
        assert pid not in db.properties and pid not in state['property_ids']
        state['version']='1.0.1';state['property_ids'].append(pid)
        state['source_scope']+=' Added Table4 DeltaHm shares this contextual DSC method description only; actual aliquot,run and per-cell cycle linkage to Tm unknown. No new physical specimen or batch coverage claimed.'
        assert state['state']==oldstate['state']
        p=deepcopy(db.properties[row['existing_melting_property_id']])
        p.update(id=pid,version='1.0.0',quantity='dsc_reported_melting_specific_enthalpy',quantity_dimension='energy_per_mass',source_property_label='Delta H_m (J/g)',reported_value=dict(kind='scalar',value_text=row['number'],number=row['number'],unit_text='J/g',unit_code='J_per_g_dsc_melting_enthalpy'),density_basis=None,summary_statistic='reported_value',uncertainty=None,uncertainty_status='not_reported_in_inspected_source',uncertainty_note='No numeric amplitude printed in selected Table4 enthalpy cell; mechanical-table SD and DSC trace appearance not transferred.',basis_note='Author-reported peak-area reduction,not raw instrument reading or evaluator computation. Preserve positive printed integer without sign flip,scaling or assumed normalization.')
        p['conditions']=dict(temperature=known(program,'Dynamic source program,not ambient temperature or a single isothermal enthalpy measurement point.'),test_standard=unknown('No DSC-specific standard named in inspected method; mechanical standards not transferred.'),test_method=known('Perkin Elmer DSC-7; extruded formulation nominal10mg;source peak-area melting enthalpy;'+program,'Second heating is contextual only; integration coverage and mass normalization not resolved.'),direction=unknown('DSC-specific sampling orientation and physical aliquot relation unknown; no scalar-isotropy or mechanical-direction inference.'),conditioning=unknown('DSC pre-scan drying,storage,RH and equilibration unknown; precursor preparation is not DSC conditioning.'),loading_rate=dict(status='not_applicable',text=None,evidence=[],notes='Mechanical loading rate does not describe DSC; signed heating/cooling rates retained in thermal program.'),additional_conditions=[dict(name='nominal_DSC_sample_mass',fact=known('10mg','Nominal source method only,not actual per-run weighing,replicate count or normalization denominator.')),dict(name='purge_pan_software',fact=unknown('DSC gas,flow,pan,lid and software unspecified; neighboring DMA/TGA statements not transferred.'))])
        p['dsc_enthalpy_definition']=dict(basis='source_reported_dsc_melting_peak_area_specific_enthalpy',thermal_program=known(program,'Actual run history,holds and heat-history erasure not independently verified.'),cycle_assignment=known('Figure4 caption identifies second heating;Table4 situated in same DSC discussion','Shared context only;Figure4 plots B0/B20/B45/R20/R45,not all selected rows;Table4 does not individually assign each DeltaHm cell.'),integration_scope=known('Source defines DeltaHm as melting enthalpy derived from area under the peak','Two melting peaks discussed; main-peak-only versus combined integration not specified. No range or deconvolution inferred.'),normalization_mass_basis=unknown('Unambiguous per-cell sample-mass versus polymer-phase-mass normalization not stated independently;Xc equation f and110.3 reference do not substitute for that evidence.'),baseline_and_limits=unknown('Baseline construction,integration limits and software reduction settings not given.'),apparatus_and_calibration=known('Perkin Elmer DSC-7;nominal10mg extruded formulations','Calibration,pan,lid,gas and DSC-specific software not supplied;no defaults or neighboring-method software transferred.'),sample_replication_conditioning=unknown('DSC n,run/aliquot/batch links,drying,RH and storage unknown;two ramps are not n2 and DMAtriplicate not transferred.'),sign_convention=unknown('Table4 selected values are printed positive;endotherm/exotherm and software sign convention not explicitly established. Preserve signs,do not infer from plot orientation.'),evidence=ev(method,'method','condition'),notes=scope)
        p['sample_count']=dict(value=None,relation='not_reported',source_statement='No unambiguous DSC enthalpy contributor count;10mg is nominal mass,two ramps are program steps,DMAtriplicate not transferred.',scope=label+' Table4 DeltaHm only;per-run,specimen and independent batch counts unknown.',evidence=ev(method,'sample_count'))
        p['method_definition']=dict(type='source_reported_conventional',definition='Source-reported DSC melting peak-area specific enthalpy;'+program+';integration,mass basis and sign convention unknown.',extraction_window=None,evidence=ev(method,'method','condition','classification'))
        p['evidence']=ev(row['source_locator'],'reported_value','classification')+ev(method,'method','condition','classification')
        inspection='Primary retained XML Table4 and selected DSC method/discussion/caption inspected;secondary same-byte publisher PDFpp4/9/10 visually corroborated. XML primary URL/hash not replaced by PDF hash. No raw traces,integration logs,full standard or latest-notice completeness inspection.'
        p['source_document'].update(url=url,sha256=facts['primary_xml_sha256'],hash_status='recorded',hash_note=None,inspected_on='2026-11-12',revision='Retained primary XML;formal revision and latest notices not independently verified.',inspection_scope=inspection)
        p['verification']['source_inspection_scope']=inspection;p['scope_note']=scope
        props.append(p);revisions.append(dict(before=oldstate,after=state))
    data=deepcopy(db.data);changed={x['after']['id']:x['after'] for x in revisions};data['materials']['records']=[changed.get(s['id'],s) for s in data['materials']['records']];data['reference_properties']['records'].extend(props)
    validate_material_catalog(*(data[n] for n in ['materials','reference_properties','sources']));after=Database(data)
    assert after.identities==db.identities and after.grades==db.grades and after.sources==db.sources
    assert all(after.properties[k]==v for k,v in db.properties.items())
    assert all(after.states[k]==v for k,v in db.states.items() if k not in changed)
    assert len(after.states)==len(db.states) and len(props)==len(revisions)==9
    ext=ROOT.parent/'open-database-evidence/polymer-pbs-enthalpy-mapping-20261112-r1';ext.mkdir(exist_ok=False)
    old_source_count=len(list(db.records(source=source)));groups=[]
    for name,filters,count in [('enthalpy-nine',dict(quantity='dsc_reported_melting_specific_enthalpy'),9),('source-all',dict(source=source),old_source_count+9),('melting-nine',dict(source=source,quantity='melting_peak_temperature'),9)]:
        rows=list(after.records(**filters));assert len(rows)==count;after.export(ext/name,**filters);assert read_snapshot(ext/name)[1]=={r['record_id']:r for r in rows};groups.append(dict(name=name,records=count,full_export_exact=True))
    write('NEW_PROPERTIES_R1.json',props);write('STATE_REVISIONS_R1.json',revisions);write('VALIDATION_R1.json',dict(snapshot=after.snapshot,properties=len(after.properties),states=len(after.states),sources=len(after.sources),new_properties=9,revised_contexts=9,new_contexts=0,new_identities=0,new_sources=0,all_old_properties_unchanged=True,old_state_facts_unchanged=True,exports=groups,native_changed=False,installed=False))
    print(json.dumps(dict(snapshot=after.snapshot,properties=len(after.properties),states=len(after.states),native_changed=False)))
if __name__=='__main__':main()
