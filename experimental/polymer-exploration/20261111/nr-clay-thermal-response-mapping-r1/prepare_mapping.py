"""Freeze twelve source cells and six existing-formulation caloric contexts; no native write."""
from pathlib import Path
from copy import deepcopy
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
PRIOR=HERE.parent/'local-acceptance-r42'
sys.path.insert(0,str(ROOT))
from materials_boundaries.database import Database
from materials_boundaries.material_references import validate_material_catalog

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def write(n,obj):
    with (HERE/n).open('x',encoding='utf-8',newline='\n') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')

def main():
    entry=PRIOR/'REVIEW_FINAL_INPUTS_R42.json';review=read(PRIOR/'INDEPENDENT_FINAL_REVIEW_R42.json')
    assert review['decision']=='approved' and review['review_inputs_sha256']==sha(entry)
    pins=read(entry)
    for field in ('repo_files_sha256','external_files_sha256'):
        for n,h in pins[field].items():assert sha(Path(n) if field=='external_files_sha256' else ROOT/n)==h,n
    before=Database();assert before.snapshot=='260639621880d7eb749d6604dd3d28b2335adf0a4edca55ee7bf1f9c8e5f44c6'
    data=deepcopy(before.data);primary='bianchi_2025_nr_nanoclay'
    url=before.properties['refprop_smr10_bianchi2025_nr_thermal_response_forced_convection_post_stretching_hold']['source_document']['url']
    def ev(where,*tags):return dict(source_id=primary,url=url,locator=where,supports=list(tags))
    cells=[('1mmt','NR_1MMT','5.7','0.5','17.3','0.8'),('3mmt','NR_3MMT','6.0','0.7','17.7','0.1'),('5mmt','NR_5MMT','7.5','3.9','20.2','2.0'),('1ommt','NR_1O-MMT','8.8','0.8','19.8','0.4'),('3ommt','NR_3O-MMT','6.7','0.5','15.4','0.6'),('5ommt','NR_5O-MMT','4.8','1.7','16.8','0.2')]
    facts=[];states=[];props=[]
    caloric=before.states['state_smr10_bianchi2025_nr_thermal_response_forced_convection']
    for suffix,label,v1,u1,v2,u2 in cells:
        old=before.states['state_bianchi2025_nr_'+suffix];identity=before.identities[old['identity_id']]
        assert identity['category']=='composite' and old['source_designation']==label and old['grade_id'] is None
        state=deepcopy(old);state.update(id=old['id']+'_thermal_response_forced_convection',version='1.0.0',name=label+' forced-convection thermal response',names={lang:label+' forced-convection thermal response' for lang in ('en','zh','ja','de')},aliases=[],property_ids=[])
        # Source-wide formulation preparation remains; replace density-only geometry/conditioning/axis context.
        for key in ('product_form','conditioning','orientation'):state['state'][key]=deepcopy(caloric['state'][key])
        state['state']['porosity']['notes']='Caloric-specimen void fraction unknown;nonfoamed preparation does not establish zero porosity.'
        state['source_scope']=identity['identity_scope']+' Current-paper section3.3.5 forced-convection caloric-strip context,Table6 row '+label+'. Initial45x15x1mm geometry and25mm gauge reported;deformed geometry and physical linkage to density,LFA,hardness or mechanical specimens unknown. Context is not a new formulation,independent batch or independent specimen count.'
        state['evidence'] += [ev('PDF p15 Table6 '+label+' row and forced-convection footnote;p19-20 section3.3.5','state')]
        for phase,column,value,unc in [('post_stretching_hold','stretching',v1,u1),('post_retraction_recovery','retraction',v2,u2)]:
            locator='PDF p15 Table6 '+label+',tau_c '+column
            p=deepcopy(before.properties['refprop_smr10_bianchi2025_nr_thermal_response_forced_convection_'+phase])
            p.update(id='refprop_bianchi2025_nr_'+suffix+'_thermal_response_forced_convection_'+phase,material_state_id=state['id'])
            p['reported_value'].update(number=value,value_text=value)
            p['uncertainty'].update(number=unc,value_text=unc,evidence=[ev(locator,'uncertainty')])
            p['thermal_response_phase']['evidence']=[ev(locator,'condition')]
            p['thermal_convection']['evidence']=[ev('PDF p15 Table6 '+label+' row and all-nanocomposites forced-convection footnote','condition')]
            p['evidence']=[ev(locator,'reported_value','classification')]
            p['scope_note']='Source-qualified '+label+' fit-derived temperature-response time under current forced-convection protocol. Not intrinsic mechanical relaxation,half-life or cycle duration;not a natural-convection comparison. Centre estimator,plus-minus meaning,per-cell n,fit settings,raw curves,aggregation and independent batches unknown. Recipe phr is per hundred rubber,not composite weight percent. No transfer of reference-paper numerical tables,fit parameters or protocol;no software fit,inverse or engineering allowable.'
            fact=dict(source_designation=label,existing_identity_id=old['identity_id'],existing_formulation_state_id=old['id'],proposed_state_id=state['id'],proposed_property_id=p['id'],phase=phase,source_column=column,number=value,plus_minus=unc,unit='s',summary_statistic='not_stated',plus_minus_meaning='not_stated',per_cell_statistical_n=None,convection='forced_convection',evidence=ev(locator,'reported_value'),identity_evidence=ev('PDF p17 Table8 '+label+' row;p16 sections3.1-3.2','material_identity','state'))
            facts.append(fact);props.append(p);state['property_ids'].append(p['id'])
        states.append(state)
    current=before.sources[primary];after_source=deepcopy(current)
    after_source['claim_notes'].append('Additional selected Table6 facts for six existing NR/MMT and NR/O-MMT formulations:two phase-specific fit-derived temperature-response times each,all forced convection per footnote. Centre estimator,plus-minus meaning,per-cell fit n and actual fit settings unknown;2specimens/formulation and3precycles/specimen are method facts only. Table8 phr recipe context preserved;no new identity,physical batch certification,reference-paper numerical transfer or raw-literature redistribution. This note records the frozen candidate phase;actual admission requires a later exact receipt.')
    data['materials']['records'].extend(states);data['reference_properties']['records'].extend(props)
    data['sources']['records']=[after_source if s['id']==primary else s for s in data['sources']['records']]
    validate_material_catalog(*(data[n] for n in ('materials','reference_properties','sources')))
    after=Database(data)
    assert all(after.properties[k]==v for k,v in before.properties.items()) and all(after.states[k]==v for k,v in before.states.items())
    assert before.identities==after.identities and before.grades==after.grades
    assert len(props)==12 and len(states)==6 and len(after.properties)==5432 and len(after.states)==5271 and len(after.sources)==134
    write('SOURCE_FACTS_R1.json',facts);write('NEW_PROPERTIES_R1.json',props);write('NEW_STATES_R1.json',states)
    write('SOURCE_UPDATE_R1.json',dict(before=current,after=after_source,changed_fields=['claim_notes'],native_applied=False))
    write('VALIDATION_R1.json',dict(baseline_snapshot=before.snapshot,candidate_snapshot=after.snapshot,properties=len(after.properties),states=len(after.states),sources=len(after.sources),new_properties=12,new_context_states=6,new_identities=0,new_grades=0,new_sources=0,old5420properties_unchanged=True,old5265states_unchanged=True,identities_grades_unchanged=True,native_applied=False,installation='not_run'))
    print(json.dumps(dict(snapshot=after.snapshot,properties=len(after.properties),states=len(after.states),native_applied=False)))
if __name__=='__main__':main()
