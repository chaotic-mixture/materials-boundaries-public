"""Three lignin thermal references under existing contracts;no native writes."""
from pathlib import Path
from copy import deepcopy
import json,hashlib,sys
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent;SOURCE=HERE.parent/'indulin-tga-source-screen-r1'
sys.path.insert(0,str(ROOT))
from materials_boundaries.database import Database
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(n,obj):
    with (HERE/n).open('x',encoding='utf-8',newline='\n') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
    entry=SOURCE/'REVIEW_INPUTS_R1.json';review=read(SOURCE/'INDEPENDENT_SOURCE_REVIEW_R1.json');assert review['decision']=='approved' and review['review_inputs_sha256']==sha(entry)
    for group in ('repo_files_sha256','external_files_sha256','native_files_sha256'):
        for n,h in read(entry)[group].items():assert sha(Path(n) if group=='external_files_sha256' else ROOT/n)==h,n
    before=Database();assert before.snapshot=='7052976761726b3ada70656c7b6b6baca4dba92b9d74946ffa23d292fb47a55f'
    facts=read(SOURCE/'SOURCE_FACTS_R1.json');sid=facts['source_id'];url=facts['primary_url'];loc='Section2.8 TGA paragraph;Section3.6/Table5 Lignin row'
    def ev(locator,*roles):return dict(source_id=sid,url=url,locator=locator,supports=list(roles))
    def unknown(note):return dict(status='not_reported_in_inspected_source',text=None,evidence=[ev(loc,'condition')],notes=note)
    state=deepcopy(before.states[facts['density_state_reference_only']]);state.update(id='state_ewurum2025_indulin_at_tga',version='1.0.0',name='Indulin AT source TGA context',names={'en':'Indulin AT source TGA context','zh':'Indulin AT 来源热重方法语境','ja':'Indulin AT 出典熱重量分析','de':'Indulin AT Quellen-TGA-Kontext'},aliases=[],source_designation='Lignin;Table5 TGA',property_ids=[])
    composition=deepcopy(state['state']['composition_or_purity'])
    for name in state['state']:state['state'][name]=unknown('Selected TGA aliquot '+name+' unresolved;no pycnometry2g,DSC,DMA,gel or mechanical specimen facts transferred.')
    composition['evidence']=[ev('Sections2.1-2.2 lignin identity;Table5 Lignin row','state')];state['state']['composition_or_purity']=composition
    state['source_scope']='Existing Westvaco Indulin AT softwood kraft lignin identity. Separate source TGA method context,not new material or independent specimen. Nominal5mg applies to sharedTGA method,not density2g aliquot. Actual form,conditioning,processing/thermal history,geometry,pressure and cross-method lineage unknown. Residual mass is not purity or elemental carbon.'
    state['evidence']=[ev(loc,'state')];props=[]
    def evidence_rebind(v):
        if isinstance(v,dict):
            if {'source_id','url','locator','supports'}<=set(v):v.update(source_id=sid,url=url,locator=loc)
            for child in v.values():evidence_rebind(child)
        elif isinstance(v,list):
            for child in v:evidence_rebind(child)
    for fact in facts['selected_facts']:
        q=fact['quantity'];p=deepcopy(next(v for v in before.properties.values() if 'ewurum2025_b0' in v['id'] and v['quantity']==q));evidence_rebind(p)
        p.update(id='refprop_ewurum2025_indulin_at_'+q,material_state_id=state['id'],version='1.0.0')
        p['reported_value'].update(number=fact['number'],value_text=fact['number'])
        p['uncertainty'].update(number=fact['plus_minus_source_text'],value_text=fact['plus_minus_source_text'])
        p['basis_note']='Direct Table5 Lignin row scalar and undefined absolute +/- amplitude;no mean,SD,CI or calculated mixture value inferred.'
        p['conditions']['test_method']['text']='Shared sourceTGA:PerkinElmerTGA7,nominal5mg,30to800C at20C/min,N2 30mL/min,Pyrisv13.3.1;source calibration alumel/perkalloy/nickel/iron.'
        p['conditions']['test_method']['notes']='Nominal source method,not independent calibration certification or selected actual trace. Not density nitrogen-pycnometry2g,DSCcycles,DMAtriplicate or gel drying.'
        p['method_definition']['definition']=p['conditions']['test_method']['text']+' Source '+fact['source_label']+' role;criterion/algorithm and actual aliquot linkage unknown.'
        p['uncertainty_note']='Source parentheses +/- not defined asSD/SE/CI/tolerance. Section2.10 significance95% does not supply uncertainty coverage or mean;temperature amplitude is difference,residue amplitude percentage points.'
        p['sample_count']=dict(value=None,relation='not_reported',scope='Selected lignin thermal scalar;independent n/batches unknown',source_statement='No TGA per-cell count established;nominal5mg is mass,not n.',evidence=[ev(loc,'condition')])
        p['source_discrepancies']=[]
        p['evidence']=[ev('Table5 Lignin row x '+fact['source_label'],'reported_value','classification'),ev(loc,'method','condition')]
        p['uncertainty']['evidence']=[ev('Table5 Lignin row x '+fact['source_label']+' parenthesized +/-','uncertainty')]
        inspection='MainXML Sections2.1-2.2 identity,2.8 TGA,2.10 statistics,3.6/Table5 Lignin values;no newPDF visual inspection'
        p['source_document']=dict(url=url,revision=None,inspected_on='2026-11-12',sha256=next(iter(read(entry)['external_files_sha256'].values())),hash_status='recorded',hash_note=None,inspection_scope=inspection,inspection_status='selected_content_inspected')
        p['verification']=dict(source_inspection_scope=inspection,transcription_cross_check='completed',independent_scientific_review=False,raw_data_reanalysis=False)
        p['scope_note']=state['source_scope']+' Source onset criterion,DTG differentiation/smoothing and peak ordinal,initial-mass reference before/after moisture loss and statistics unknown. Residue40%at800C not pure carbon,gel or independent chemical assay. No use-temperature or engineering-allowable inference.'
        assert p['id'] not in before.properties;props.append(p);state['property_ids'].append(p['id'])
    assert state['id'] not in before.states and len(props)==3
    data=deepcopy(before.data);data['materials']['records'].append(state);data['reference_properties']['records'].extend(props);after=Database(data);after.validate_scientific_contracts()
    assert all(after.properties[k]==v for k,v in before.properties.items()) and all(after.states[k]==v for k,v in before.states.items());assert before.identities==after.identities and before.grades==after.grades and before.sources==after.sources
    write('NEW_PROPERTIES_R1.json',props);write('NEW_STATES_R1.json',[state]);write('VALIDATION_R1.json',dict(candidate_snapshot=after.snapshot,properties=len(after.properties),states=len(after.states),sources=len(after.sources),new_properties=3,new_contexts=1,old5750properties_unchanged=True,old5430states_unchanged=True,identities_grades_sources_unchanged=True,native_applied=False,installation='not_run',tests='not_run_candidate_graph_only'))
    print(json.dumps(dict(snapshot=after.snapshot,properties=len(after.properties),states=len(after.states),native_applied=False)))
if __name__=='__main__':main()
