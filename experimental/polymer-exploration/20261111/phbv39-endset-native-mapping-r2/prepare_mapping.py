"""Prepare one source endset only after exact implementation approval."""
from pathlib import Path
from copy import deepcopy
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
IMPL=HERE.parent/'endset-implementation-preparation-r2'
sys.path.insert(0,str(ROOT))
from materials_boundaries.database import Database
from materials_boundaries.material_references import validate_material_catalog
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(n,v):
    with (HERE/n).open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
    entry=IMPL/'REVIEW_IMPLEMENTATION_INPUTS_R2.json';receipt=read(IMPL/'INDEPENDENT_IMPLEMENTATION_REVIEW_R2.json')
    assert receipt['decision']=='approved' and receipt['review_inputs_sha256']==sha(entry)
    for field in ('repo_files_sha256','external_files_sha256','native_files_sha256'):
        for n,h in read(entry)[field].items():assert sha(Path(n) if field=='external_files_sha256' else ROOT/n)==h,n
    before=Database();assert len(before.properties)==5506
    data=deepcopy(before.data);parent=before.states['state_abbasi2022_manure_phbv39_tga']
    p=deepcopy(before.properties['refprop_abbasi2022_manure_phbv39_thermal_degradation_onset_temperature'])
    p.update(id='refprop_abbasi2022_manure_phbv39_thermal_degradation_endset_temperature',quantity='thermal_degradation_endset_temperature',source_property_label='T_endset')
    p['reported_value'].update(number='333',value_text='333')
    locator='XMLTable4 polymers-14-04140-t004 PHBV-39/Tendset;sections2.2.5,3.4'
    def ev(*tags):return [dict(source_id=p['source_id'],url=p['source_document']['url'],locator=locator,supports=list(tags))]
    method='Source-labelled TGA degradation endset;operational threshold/tangent/baseline unknown. Perkin-Elmer TGA-7,4–5mg,30–800°C at20°C/min under nitrogen,Pyris13.3;duplicate is method wording,not selected-celln2.'
    p['conditions']['test_method'].update(text=method,evidence=ev('method','condition'))
    p['method_definition'].update(definition=method,evidence=ev('method','classification'))
    p['thermal_scan_definition']=dict(kind='nonisothermal_temperature_scan',evidence=ev('method','condition'),notes='Explicit source heating program;not isothermal hold,constant ambient temperature or operating limit.')
    p['degradation_endset_definition']=dict(status='not_reported_in_inspected_source',text=None,evidence=ev('condition'),notes='Source names endset without an operational threshold,tangent/baseline definition. Not zero mass,complete chemical degradation,scan maximum or use limit.')
    p['evidence']=ev('reported_value','classification','method','condition')
    scope='Retained primaryXML Table4 PHBV-39 Tendset333°C andsections2.2.5/3.4;no new mainPDF inspection,curve extraction or raw-data analysis.'
    p['source_document']['inspection_scope']=scope;p['verification']['source_inspection_scope']=scope
    p['scope_note']=before.identities[parent['identity_id']]['identity_scope']+' Source-qualified TGA endset only;unknown criterion,n,centre,error,conditioning and independent run assignment. Mechanical/DSC conditions not transferred;Guho/reanalysis wording does not prove TGA provenance. Tc104.8 remains held. No ordering law,automatic conversion or engineering allowable.'
    p['basis_note']='Exact primaryXML Table4 integer333°C,not curve reading or added precision. Distinct from onset299 andDTG325;their coexistence does not establish general endpoint ordering or width.'
    assert p['id'] not in before.properties
    state=deepcopy(parent);parts=parent['version'].split('.')
    assert len(parts)==3 and all(v.isdigit() for v in parts)
    state['version']='.'.join(parts[:2]+[str(int(parts[2])+1)]);state['property_ids'].append(p['id'])
    data['reference_properties']['records'].append(p);data['materials']['records']=[state if s['id']==state['id'] else s for s in data['materials']['records']]
    validate_material_catalog(*(data[n] for n in ('materials','reference_properties','sources')));after=Database(data)
    assert all(after.properties[k]==v for k,v in before.properties.items())
    assert all(after.states[k]==v for k,v in before.states.items() if k!=state['id'])
    assert before.identities==after.identities and before.grades==after.grades and before.sources==after.sources
    assert {k:v for k,v in parent.items() if k not in ('version','property_ids')}=={k:v for k,v in state.items() if k not in ('version','property_ids')}
    write('NEW_PROPERTIES_R1.json',[p]);write('STATE_UPDATES_R1.json',[dict(before=parent,after=state)])
    write('VALIDATION_R1.json',dict(snapshot=after.snapshot,properties=len(after.properties),states=len(after.states),new_properties=1,new_states=0,revised_states=1,old5506properties_unchanged=True,native_applied=False,installation='not_run'))
    print(json.dumps(dict(snapshot=after.snapshot,native_applied=False)))
if __name__=='__main__':main()
