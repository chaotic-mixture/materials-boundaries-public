"""Build a review-only process-event candidate; never modify native tables."""
from pathlib import Path
from copy import deepcopy
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from materials_boundaries.database import Database
from materials_boundaries.material_references import validate_material_catalog
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(name,obj):
    with (HERE/name).open('x',encoding='utf-8',newline='\n') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
    proposal=HERE.parent/'pur-foaming-events-source-proposal-r1'
    implementation=HERE.parent/'foam-event-implementation-r1'
    for folder,entry,receipt in [(proposal,'REVIEW_INPUTS_R1.json','INDEPENDENT_SOURCE_REVIEW_R1.json'),(implementation,'REVIEW_IMPLEMENTATION_INPUTS_R1.json','INDEPENDENT_IMPLEMENTATION_REVIEW_R1.json')]:
        review=read(folder/receipt);assert review['decision']=='approved' and review['review_inputs_sha256']==sha(folder/entry)
        for group in ['repo_files_sha256','external_files_sha256','native_files_sha256']:
            for n,h in read(folder/entry)[group].items():assert sha(Path(n) if group=='external_files_sha256' else ROOT/n)==h,n
    before=Database();assert before.snapshot=='dec71f6cdfe34eb906017d06518f4560eb8f2782dbd8ce0568206a3eba53d5ed'
    source='ivdre_2024_lpo_rigid_pur';url='https://www.ebi.ac.uk/europepmc/webservices/rest/PMC11013755/fullTextXML'
    method='Section2.8 foaming kinetics and glass-rod paragraphs; XML sec2dot8-polymers-16-00942; PDFp7'
    def ev(loc,*roles):return [dict(source_id=source,url=url,locator=loc,supports=list(roles))]
    def unknown(note,role='condition'):return dict(status='not_reported_in_inspected_source',text=None,evidence=ev(method,role),notes=note)
    def known(text,note):return dict(status='reported',text=text,evidence=ev(method,'method','condition'),notes=note)
    scope='Source-qualified reacting formulation/foaming-process observation, not a cured specimen property. Method grouping establishes no same cup, batch, specimen, network or shared clock. No event ordering, subtraction, full cure, conversion, pot life or thermal-fit interpretation.'
    states={};props=[]
    for row in read(proposal/'SOURCE_FACTS_R1.json')['candidates']:
        label=row['source_label'];key=label.lower().replace('-','');family='foamat' if row['method_family']=='Foamat' else 'glass_rod'
        sid=f'state_ivdre2024_{key}_reacting_{family}';pid=f'refprop_ivdre2024_{key}_reaction_{row["event"]}'
        if sid not in states:
            state=deepcopy(before.states[f'state_ivdre2024_{key}_rigid_pur'])
            assert state['identity_id']==row['identity_id']
            names=dict(en=f'{label} reacting PUR formulation, {family} process context',zh=f'{label}反应中PUR配方，{family}发泡过程上下文',ja=f'{label}反応中PUR配合、{family}発泡過程',de=f'{label} reagierende PUR-Rezeptur, {family}-Prozesskontext')
            state.update(id=sid,version='1.0.0',name=names['en'],names=names,aliases=[],source_designation=label+' Table10 reaction event observations',property_ids=[],source_scope=scope,evidence=ev('Table9 '+label+' input formulation;Table10 reaction times;Section2.8','state'))
            for field in state['state']:
                if field!='composition_or_purity':state['state'][field]=unknown('Actual reacting-process '+field+' not established; do not transfer cured-foam preparation,24h cure,porosity,geometry or orientation.','state')
            state['state']['product_form']=dict(status='reported',text='Reacting PUR input formulation during source-observed foaming process, '+family+' method context',evidence=ev(method,'state'),notes=scope)
            states[sid]=state
        states[sid]['property_ids'].append(pid)
        p=deepcopy(before.properties[f'refprop_ivdre2024_{key}_rigid_pur_mass_density'])
        p.update(id=pid,version='1.0.0',material_state_id=sid,quantity='foam_reaction_event_time',quantity_dimension='time',source_property_label=row['source_property_label'],reported_value=dict(kind='scalar',value_text=row['number'],number=row['number'],unit_text='s',unit_code='s'),density_basis=None,summary_statistic='reported_value',uncertainty=None,uncertainty_status='not_reported_in_inspected_source',uncertainty_note='No numeric uncertainty for this source event cell; no adjacent property amplitude transferred.',basis_note=scope)
        p['conditions']={k:unknown('Actual reaction-test '+k+' unspecified; no cured-specimen,apparatus-default or common-clock inference.') for k in ['temperature','test_standard','direction','conditioning','loading_rate']}
        apparatus='Foamat instrument for start and rise observations' if family=='foamat' else 'Glass rod repeated dipping/pulling for string emergence; light surface contact for no adhesion'
        p['conditions']['test_method']=known(apparatus,'Source operational observation only; observer,intervals,rod dimensions and instrument algorithms unknown.')
        p['conditions']['additional_conditions']=[]
        p['reaction_event']=dict(code=row['event'],evidence=ev(row['source_locator'],'reported_value','classification'),notes='Preserve source operational event label; no universal temporal order or chemical-cure interpretation.')
        endpoint=deepcopy(row['endpoint_criterion']);endpoint['evidence']=ev(method,*(['method','condition'] if endpoint['status']=='reported' else ['condition']))
        p['reaction_time_definition']=dict(basis='source_reported_process_event_time',clock_origin=unknown(row['clock_origin']['notes']),endpoint_criterion=endpoint,apparatus_or_observation_method=known(apparatus,'No apparatus default endpoint or clock origin inferred.'),mixing_reference=unknown('Actual event timing reference relative to mixing,pMDI addition,pouring or trigger unspecified;10s preparation is not a clock origin.'),reaction_test_geometry_charge=unknown('Actual reacting-test vessel,geometry and charge unknown; MRSM cups and cured specimen dimensions not transferred.'),reaction_test_environment=unknown('Actual reacting temperature,RH and pressure unspecified;24h room-temperature cure not transferred.'),replicate_and_piece_relationship=unknown('Per-cell n,independent batches and common cup/specimen relationships not stated; grouping is method-only.'),evidence=ev(method,'method','condition'),notes=scope)
        p['sample_count']=dict(value=None,relation='not_reported',source_statement='No unambiguous per-event contributor count; MRSM cups and other-method specimen counts not transferred.',scope=label+' '+row['event']+' source cell only; aggregation unknown.',evidence=ev(method,'sample_count'))
        p['method_definition']=dict(type='source_reported_conventional',definition=apparatus+'; clock origin unknown; source-defined process event,not thermal fit or standardized pot life.',extraction_window=None,evidence=ev(method,'method','condition','classification'))
        p['evidence']=ev(row['source_locator'],'reported_value','classification')+ev(method,'method','condition','classification')
        inspection='Retained primary JATS Table10 and Section2.8 inspected; same-byte publisher PDFpp7/17 corroborates selected event cells and methods. No raw timing traces,standard,latest-notice completeness or scientific validity certified.'
        p['source_document'].update(inspected_on='2026-11-12',inspection_scope=inspection,revision='Retained selected source representations; formal revision and latest notices not verified.')
        p['verification']['source_inspection_scope']=inspection;p['scope_note']=scope+' Central estimator,n,uncertainty and clock origin unknown.'
        props.append(p)
    data=deepcopy(before.data);data['materials']['records'].extend(states.values());data['reference_properties']['records'].extend(props)
    validate_material_catalog(*(data[n] for n in ['materials','reference_properties','sources']));after=Database(data)
    assert len(props)==16 and len(states)==8 and after.identities==before.identities and after.grades==before.grades and after.sources==before.sources
    assert all(after.properties[k]==v for k,v in before.properties.items()) and all(after.states[k]==v for k,v in before.states.items())
    rows=list(after.records(quantity='foam_reaction_event_time'));assert len(rows)==16
    write('NEW_STATES_R1.json',list(states.values()));write('NEW_PROPERTIES_R1.json',props)
    write('VALIDATION_R1.json',dict(snapshot=after.snapshot,properties=len(after.properties),states=len(after.states),sources=len(after.sources),new_properties=16,new_method_contexts=8,new_identities=0,new_sources=0,old_properties_and_states_unchanged=True,graph='passed',query_records=16,native_changed=False,installed=False))
    print(json.dumps(dict(snapshot=after.snapshot,properties=len(after.properties),states=len(after.states),native_changed=False)))
if __name__=='__main__':main()
