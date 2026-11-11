"""Prepare eighteen unapplied LFA facts in six existing-composite specimen contexts."""
from pathlib import Path
from copy import deepcopy
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
PRIOR=HERE.parent/'local-acceptance-r43';SOURCE=HERE.parent/'nr-clay-lfa-source-draft-r1'
sys.path.insert(0,str(ROOT))
from materials_boundaries.database import Database
from materials_boundaries.material_references import validate_material_catalog
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def write(n,obj):
    with (HERE/n).open('x',encoding='utf-8',newline='\n') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
    entry=PRIOR/'REVIEW_FINAL_INPUTS_R43.json';review=read(PRIOR/'INDEPENDENT_FINAL_REVIEW_R43.json')
    assert review['decision']=='approved' and review['review_inputs_sha256']==sha(entry)
    pins=read(entry)
    for field in ('repo_files_sha256','external_files_sha256'):
        for n,h in pins[field].items():assert sha(Path(n) if field=='external_files_sha256' else ROOT/n)==h,n
    sourcepins=read(SOURCE/'EVIDENCE_BINDINGS_R1.json')
    for field in ('native_files_sha256','external_files_sha256'):
        for n,h in sourcepins[field].items():assert sha(Path(n) if field=='external_files_sha256' else ROOT/n)==h,n
    before=Database();assert before.snapshot=='81da352df9c0c8bba0086d5046523f3e77d9378cd7b8e14d65eb6deaffe0ed3d'
    data=deepcopy(before.data);primary='bianchi_2025_nr_nanoclay';url=before.properties['refprop_smr10_bianchi2025_nr_thermal_conductivity']['source_document']['url']
    def ev(where,*tags):return dict(source_id=primary,url=url,locator=where,supports=list(tags))
    states={};props=[];caloric=before.states['state_smr10_bianchi2025_nr_lfa']
    facts=read(SOURCE/'SOURCE_FACTS_R1.json');assert len(facts)==18
    for fact in facts:
        old=before.states[fact['existing_state_id']];identity=before.identities[fact['existing_identity_id']]
        assert old['identity_id']==identity['id'] and identity['category']=='composite'
        label=fact['source_designation'];quantity=fact['quantity'];key=old['id']
        if key not in states:
            state=deepcopy(old);state.update(id=old['id']+'_lfa',version='1.0.0',name=label+' source LFA cylindrical specimens',names={lang:label+' source LFA cylindrical specimens' for lang in ('en','zh','ja','de')},aliases=[],source_designation=label+';LFA specimens',property_ids=[])
            for field in ('product_form','conditioning','orientation'):state['state'][field]=deepcopy(caloric['state'][field])
            state['state']['porosity']['notes']='Selected LFA specimen void fraction unknown;nonfoamed preparation does not establish zero porosity.'
            state['source_scope']=identity['identity_scope']+' Current-paper section3.3.3 LFA cylindrical-specimen context,Table3 '+label+'. Three tested specimens/formulation and five pulses/specimen are method facts,not per-cell n or15 independent replicates. Density/LFA/caloric/mechanical physical pairing and independent batches unknown. Conductivity is a source-calculated result,not a separately certified direct measurement. No new identity or batch claimed.'
            state['evidence'].append(ev('PDF p6 Table3 '+label+';p18 section3.3.3','state'));states[key]=state
        state=states[key];p=deepcopy(before.properties['refprop_smr10_bianchi2025_nr_'+quantity])
        p.update(id=old['id'].replace('state_','refprop_',1)+'_'+quantity,material_state_id=state['id'],version='1.0.0')
        assert p['id'] not in before.properties
        p['reported_value'].update(number=fact['number'],value_text=fact['number'])
        p['uncertainty'].update(number=fact['plus_minus'],value_text=fact['plus_minus'],evidence=[ev(fact['source_locator'],'uncertainty')])
        p['evidence']=[ev(fact['source_locator']+';'+fact['method_locator'],'reported_value','classification')]
        assert p['reported_value']['unit_text']==fact['unit_text'] and p['evidence_kind']==fact['evidence_kind_proposed'] and p['determination_basis']==fact['determination_basis_proposed']
        inspection='Retained officialPDF selectedp6Table3 '+label+' row,p18section3.3.3 andp16-17formulation;thermal statistics unspecified. No raw pulse reanalysis,actual paired-input reconstruction or latest-notice completeness certification.'
        if quantity=='thermal_conductivity':
            inspection+=' Equation4 andp4Table1 provide source context only;Table1 third filled-row label printedNR_3MMsT is not silently repaired.'
            for q,context in p['derivation']['contextual_inputs'].items():
                if q=='mass_density':
                    rowlabel='row printed NR_3MMsT (Table8/3 formulation label NR_3MMT;contextual association only)' if label=='NR_3MMT' else label+' row'
                    locator='PDF p4 Table1 '+rowlabel+';p17 section3.3.1 density method'
                    context['source_property_label']='Density,Table1 '+rowlabel+',not verified actual input'
                else:
                    locator='PDF p6 Table3 '+label+' '+q
                    context['source_property_label']=q+',Table3 '+label+' context,not verified actual input'
                context['evidence']=[ev(locator,'reported_value')]
            if label=='NR_3MMT':p['derivation']['input_provenance']['unknown_scope_note']+=' Table1 printsNR_3MMsT on the corresponding density context row;no textual source repair or certified actual input identification is performed.'
        p['source_document']['inspection_scope']=inspection;p['verification']['source_inspection_scope']=inspection
        p['scope_note']=p['scope_note'].replace('Study-specific unfilled vulcanizate','Source-qualified '+label+' vulcanizate').replace('Study-specific source-calculated','Source-qualified '+label+' source-calculated')+' Recipe phr is per hundred rubber,not total-composite weight percent;current LFA context does not certify pairing with density or other test specimens.'
        assert p['summary_statistic']=='not_stated' and p['sample_count']['value'] is None and p['uncertainty_status']=='reported_plus_minus_unspecified'
        props.append(p);state['property_ids'].append(p['id'])
    source_before=before.sources[primary];source_after=deepcopy(source_before)
    source_after['claim_notes'].append('Frozen selected Table3 candidate:each of six existing NR/MMT and NR/O-MMT formulations adds source LFA heat-capacity,diffusivity and source-calculated conductivity context. Current20C/cylinders/three specimens/five pulses are distinct method facts,not n15. Thermal estimator,plus-minus meaning and per-cell n unknown;actual paired conductivity inputs,physical linkage,density temperature,aggregation/covariance/propagation unknown. Table1 NR_3MMsT printed row-label discrepancy is retained as contextual ambiguity,no repair. No supplier Table7 data,software product/reanalysis or new identity. Native admission requires a later exact receipt.')
    data['materials']['records'].extend(states.values());data['reference_properties']['records'].extend(props)
    data['sources']['records']=[source_after if s['id']==primary else s for s in data['sources']['records']]
    validate_material_catalog(*(data[n] for n in ('materials','reference_properties','sources')));after=Database(data)
    assert all(after.properties[k]==v for k,v in before.properties.items()) and all(after.states[k]==v for k,v in before.states.items())
    assert before.identities==after.identities and before.grades==after.grades
    assert len(props)==18 and len(states)==6 and len(after.properties)==5450 and len(after.states)==5277
    write('NEW_PROPERTIES_R1.json',props);write('NEW_STATES_R1.json',list(states.values()));write('SOURCE_UPDATE_R1.json',dict(before=source_before,after=source_after,changed_fields=['claim_notes'],native_applied=False))
    write('VALIDATION_R1.json',dict(baseline_snapshot=before.snapshot,candidate_snapshot=after.snapshot,properties=len(after.properties),states=len(after.states),sources=len(after.sources),new_properties=18,new_context_states=6,new_identities=0,new_grades=0,new_sources=0,old5432properties_unchanged=True,old5271states_unchanged=True,identities_grades_unchanged=True,native_applied=False,installation='not_run'))
    print(json.dumps(dict(snapshot=after.snapshot,properties=len(after.properties),states=len(after.states),native_applied=False)))
if __name__=='__main__':main()
