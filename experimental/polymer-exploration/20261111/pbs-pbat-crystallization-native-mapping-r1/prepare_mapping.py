"""Prepare four source-qualified cooling peaks; never write native tables."""
from pathlib import Path
from copy import deepcopy
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[4]; HERE=Path(__file__).resolve().parent
IMPL=HERE.parent/'crystallization-phase-implementation-r1'
SOURCE=HERE.parent/'pbs-pbat-crystallization-source-proposal-r1'
sys.path.insert(0,str(ROOT))
from materials_boundaries.database import Database
from materials_boundaries.material_references import validate_material_catalog
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(n,v):
    with (HERE/n).open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
    entry=IMPL/'REVIEW_IMPLEMENTATION_INPUTS_R1.json'; review=read(IMPL/'INDEPENDENT_IMPLEMENTATION_REVIEW_R1.json')
    assert review['decision']=='approved' and review['review_inputs_sha256']==sha(entry)
    for field in ('repo_files_sha256','external_files_sha256','native_files_sha256'):
        for n,h in read(entry)[field].items():assert sha(Path(n) if field=='external_files_sha256' else ROOT/n)==h,n
    before=Database();assert before.snapshot=='d4146fffdd9bf439b2e492acab15c75c33826883ee5d4031cc18f50b243acba3'
    data=deepcopy(before.data); states=[];props=[];sid='mtibe_2022_pbs_pbat_lignin_zno'
    methodloc='PDF p5section2.6.4;p8-9section3.3/Table4/Figure4b'
    url='https://mdpi-res.com/d_attachment/polymers/polymers-14-05065/article_deploy/polymers-14-05065.pdf'
    def ev(locator,*tags):return dict(source_id=sid,url=url,locator=locator,supports=list(tags))
    for fact in read(SOURCE/'SOURCE_FACTS_R1.json'):
        base=fact['existing_formulation_state_id']; old=before.states[base+'_dsc_second_heating']
        state=deepcopy(old);state.update(id=base+'_dsc_cooling_tcc',name=before.identities[fact['existing_identity_id']]['name']+' DSC cooling Tcc',names={lang:before.identities[fact['existing_identity_id']]['name']+' DSC cooling Tcc' for lang in ('en','zh','ja','de')},source_designation=fact['source_row_label']+';DSC cooling Tcc',property_ids=[])
        state['source_scope']=before.identities[fact['existing_identity_id']]['identity_scope']+' Source Table4 Tcc cooling-scan context,not a new material or physical batch. Original cold-crystallization wording retained as a source discrepancy,not a certified mechanism. Selected cooling occurrence and cooling rate unknown;no thermal-piece geometry,conditioning,mechanical n5 or25C48h transfer. Study-wide preparation is background only.'
        state['evidence'].append(ev(fact['source_cell_locator']+';'+methodloc,'state'))
        oldp=before.properties[old['property_ids'][0]];p=deepcopy(oldp)
        p.update(id=base.replace('state_','refprop_',1)+'_crystallization_peak_temperature',material_state_id=state['id'],quantity='crystallization_peak_temperature',source_property_label='Tcc')
        p['reported_value'].update(number=fact['number'],value_text=fact['number'])
        method='TA Instruments DSC-Q2000;source Table4 Tcc in cooling-scan crystallization context. Original cold-crystallization wording is retained without certifying mechanism or relabelling the printed column.'
        program='Source states two cycles;listed sequence:heat−60to200°C,coolto−60°C,heatto200°C. Selected Tcc is associated with cooling from the melt;selected cooling occurrence is unreported.'
        p['conditions']['test_method'].update(text=method,notes='Peak extraction,baseline and aggregation unknown;nonisothermal cooling context evidenced by method andFigure4b.')
        for a in p['conditions']['additional_conditions']:
            if a['name']=='thermal_scan_program':a['fact'].update(text=program)
            if a['name']=='selected_scan':a['fact'].update(text='Cooling from the melt;occurrence ordinal unreported',notes='Not second heating,not an inferred first or second cooling. Source two cycles is not n2.')
        p['method_definition'].update(definition=method+' '+program+' Direct Table4 literal;no digitization,refit or mechanism inference.',evidence=[ev(methodloc,'method','classification')])
        p['thermal_scan_definition']=dict(kind='nonisothermal_temperature_scan',evidence=[ev(methodloc,'method','condition')],notes='Source temperature program and coolingFigure4b establish a nonisothermal scan;cooling rate remains unreported.')
        p['thermal_scan_phase']=dict(status='reported',code='cooling',evidence=[ev(methodloc,'condition')],notes='Method andFigure4b cooling-from-melt context;source printed Tcc and cold wording are not silently repaired.')
        p['thermal_phase_occurrence_ordinal']=dict(status='not_reported_in_inspected_source',value=None,evidence=[ev(methodloc,'condition')],notes=fact['phase_occurrence_ordinal_proposed']['notes'])
        p['basis_note']='Direct selected Table4 Tcc literal. Unit°C supported by same-article methods/axes,not a printed table header. Statistical centre,n,uncertainty and selected cooling occurrence unknown;no mechanism inferred.'
        p['source_discrepancies'].append(dict(description=fact['source_label_discrepancy'],disposition='Retain original Tcc and cold-crystallization wording alongside evidenced cooling phase;no author-error diagnosis or certified cold mechanism.',evidence=[ev(fact['source_cell_locator']+';'+methodloc,'source_discrepancy')]))
        p['evidence']=[ev(fact['source_cell_locator'],'reported_value','classification'),ev(methodloc,'method','condition')]
        p['scope_note']='Source-qualified '+fact['source_row_label']+' printed Tcc,nonisothermal cooling-scan crystallization peak. Not operating/service limit or independent batch. Original cold wording discrepancy explicit;no Tc renaming or cold mechanism certification. Cooling rate,occurrence,n,centre,uncertainty,thermal mass/geometry/conditioning unknown. Recipe70/30 basis andZnO denominator unresolved;no normalization. No Tg,enthalpy or independent neatPBAT thermal value imported.'
        assert p['id'] not in before.properties and state['id'] not in before.states
        state['property_ids']=[p['id']]; states.append(state);props.append(p)
    proposal=read(SOURCE/'SOURCE_UPDATE_PROPOSAL_R1.json');assert proposal['before']==before.sources[sid]
    after_source=deepcopy(proposal['after'])
    after_source['claim_notes'].append('Concrete four-cell Tcc mapping preserves cooling-scan evidence,original cold wording discrepancy and unknown phase occurrence;not new identities,independent batches or native admission. Later exact acceptance receipt controls.')
    data['materials']['records'].extend(states);data['reference_properties']['records'].extend(props)
    data['sources']['records']=[after_source if s['id']==sid else s for s in data['sources']['records']]
    validate_material_catalog(*(data[n] for n in ('materials','reference_properties','sources')));after=Database(data)
    assert all(after.properties[k]==v for k,v in before.properties.items()) and all(after.states[k]==v for k,v in before.states.items())
    assert before.identities==after.identities and before.grades==after.grades
    assert len(props)==len(states)==4 and len(after.properties)==5498 and len(after.states)==5301 and len(after.sources)==134
    write('NEW_PROPERTIES_R1.json',props);write('NEW_STATES_R1.json',states);write('SOURCE_UPDATE_R1.json',dict(before=before.sources[sid],after=after_source,changed_fields=['claim_notes'],native_applied=False))
    write('VALIDATION_R1.json',dict(baseline_snapshot=before.snapshot,candidate_snapshot=after.snapshot,properties=5498,states=5301,sources=134,new_properties=4,new_context_states=4,new_identities=0,new_grades=0,new_sources=0,old5494properties_unchanged=True,old5297states_unchanged=True,identities_grades_unchanged=True,native_applied=False,installation='not_run'))
    print(json.dumps(dict(snapshot=after.snapshot,properties=5498,states=5301,native_applied=False)))
if __name__=='__main__':main()
