"""Prepare one source-calculated NR conductivity fact after contract approval."""
from pathlib import Path
from copy import deepcopy
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
IMPL=HERE.parent/'nr-conductivity-contract-implementation-r1'
sys.path.insert(0,str(ROOT))
from materials_boundaries.database import Database
from materials_boundaries.material_references import validate_material_catalog
from materials_boundaries._material_derivation import TRANSPORT_PROFILE,TRANSPORT_METHOD,TRANSPORT_KIND,TRANSPORT_EXPRESSION,TRANSPORT_UNKNOWNS
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(n,obj):
    with (HERE/n).open('x',encoding='utf-8',newline='\n') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
    entry=IMPL/'REVIEW_IMPLEMENTATION_INPUTS_R2.json';review=read(IMPL/'INDEPENDENT_IMPLEMENTATION_REVIEW_R2.json')
    assert review['decision']=='approved' and review['review_inputs_sha256']==sha(entry)
    for field in ('repo_files_sha256','native_files_sha256','external_files_sha256'):
        for n,digest in read(entry)[field].items():assert sha(Path(n) if field=='external_files_sha256' else ROOT/n)==digest,n
    before=Database();assert before.snapshot=='373c0d4379aecc3249813e4a49950774a7a5161eb97f945aa0475f84a9f8dea4'
    data=deepcopy(before.data);p=deepcopy(before.properties['refprop_smr10_bianchi2025_nr_mass_specific_heat_capacity'])
    p.pop('thermal_mass_reference_basis');sid=p['source_id'];url=p['source_document']['url'];loc='PDF p18 section3.3.3 Thermal Properties,Equation4'
    def ev(locator,*tags):return dict(source_id=sid,url=url,locator=locator,supports=list(tags))
    p.update(id='refprop_smr10_bianchi2025_nr_thermal_conductivity',quantity='thermal_conductivity',quantity_dimension='power_per_length_temperature',source_property_label='Thermal conductivity,lambda',evidence_kind='published_measurement_derived_reference',determination_basis='source_reports_calculation')
    p['reported_value'].update(number='0.132',value_text='0.132',unit_code='W/(m*K)',unit_text='W/m·K')
    p['uncertainty'].update(number='0.003',value_text='0.003',unit_code='W/(m*K)',unit_text='W/m·K',scope='Source-reported thermal-conductivity plus-minus amplitude;meaning and propagation method unspecified.',evidence=[ev('PDF p6 Table3,NR thermal conductivity cell','uncertainty')])
    p['uncertainty_note']='Thermal plus-minus meaning and source propagation method unspecified;not transferred mechanical SD or software propagated error.'
    p['basis_note']='Source explicitly calculates lambda=alpha*cp*rho from LFA results and Archimedes density. Context tables are unpaired summaries,not certified actual calculation inputs or proof of product-of-means. Source output transcribed without recalculation.'
    p['conditions']['test_standard']=dict(status='not_reported_in_inspected_source',text=None,evidence=[],notes='No separate conductivity-calculation standard or edition stated;ASTM-E1461 is cited for heat-capacity reference determination only.')
    p['conditions']['test_method'].update(text='Source calculates lambda=alpha*cp*rho;LFA447 diffusivity using Cowan numerical pulse correction,Pyroceram9606 heat-capacity reference;Archimedes density method.',evidence=[ev(loc,'condition')],notes='Source calculation,not direct heat-flow-plate measurement. Actual joint inputs and density-temperature alignment unknown.')
    p['conditions']['additional_conditions'].append(dict(name='source_standard_context',fact=dict(status='reported',text='ASTM-E1461 cited for heat-capacity reference determination',evidence=[ev(loc,'condition')],notes='Not assigned as a verified direct-conductivity test standard;edition/compliance unknown.')))
    p['sample_count'].update(scope='Per-cell statistical n of source-calculated conductivity unknown;three LFA specimens and five pulses each are input-acquisition method facts,not n15 or independent conductivity measurements.')
    p['method_definition']=dict(type=TRANSPORT_METHOD,definition='Source-reported conductivity product lambda=alpha*cp*rho from measured thermal inputs and Archimedes density;Table1/3 summaries only contextual,actual paired inputs and order unknown. No software product,rounding audit or uncertainty propagation.',extraction_window=None,evidence=[ev(loc,'method','classification')])
    p['derivation']=dict(schema_version='1.0.0',profile_version='1.0.0',profile_id=TRANSPORT_PROFILE,kind=TRANSPORT_KIND,
        formula=dict(expression=TRANSPORT_EXPRESSION,evidence=[ev(loc,'method')]),contextual_inputs={q:dict(quantity=q,role='source_context_not_verified_actual_input',source_property_label=label,evidence=[ev(where,'reported_value')]) for q,label,where in [
            ('thermal_diffusivity','Thermal diffusivity,Table3 context','PDF p6 Table3,NR thermal diffusivity cell'),
            ('mass_specific_heat_capacity','Specific heat capacity,Table3 context','PDF p6 Table3,NR specific heat capacity cell'),
            ('mass_density','Density,Table1 context','PDF p4 Table1,NR density cell')]},
        input_provenance={**{n:None for n in TRANSPORT_UNKNOWNS},'unknown_scope_note':'Table1/3 are contextual summaries only. Actual paired inputs,specimen linkage,density temperature alignment,calculation/aggregation order,covariance and source uncertainty propagation unspecified. Do not treat product of table centres as the source algorithm or verified reconstruction.'},
        software_calculation_performed=False,software_uncertainty_propagation_performed=False)
    p['evidence']=[ev('PDF p6 Table3 NR conductivity cell;p18 Equation4','reported_value','classification')]
    inspection='Retained officialPDF selectedp4Table1 density context,p6Table3 thermal cells,p18section3.3.3/Equation4 and same-source XML;source-reported calculation only. No raw paired inputs,latest-notice verification or source-product reconstruction.'
    p['source_document']['inspection_scope']=inspection;p['verification']['source_inspection_scope']=inspection
    p['scope_note']='Study-specific source-calculated thermal conductivity at source20C context,not independent direct measurement. Actual paired inputs,density temperature alignment,aggregation order,covariance,uncertainty propagation,thermal central estimator,plus-minus meaning and per-cell n unknown. Three LFA specimens and five pulses are separate method facts. RH,conditioning,atmosphere,direction and independent batches unknown. No software product,rounding certification,uncertainty propagation or engineering allowable.'
    parent=before.states[p['material_state_id']];state=deepcopy(parent);assert state['version']=='1.0.0'
    state['version']='1.0.1';state['property_ids'].append(p['id'])
    state['source_scope']+=' Additional conductivity is source-calculated from measured inputs;contextual Table1/3 summaries do not certify actual paired inputs,density temperature alignment or calculation/aggregation order. No independent direct conductivity measurement or new material identity claimed.'
    source=before.sources[sid];updated=deepcopy(source)
    updated['claim_notes'].append('NR Table3 thermal conductivity0.132±0.003W/mK transcribed as source-reported measured-input product,not direct heat-flow measurement. Equation4 alpha*cp*rho and Table1/3 contexts preserved without reconstructing actual paired inputs,product of means,rounding or uncertainty propagation. Thermal estimator,plus-minus meaning and per-cell n unknown;3LFA specimens/5pulses distinct method facts.')
    data['materials']['records']=[state if x['id']==state['id'] else x for x in data['materials']['records']]
    data['sources']['records']=[updated if x['id']==sid else x for x in data['sources']['records']]
    data['reference_properties']['records'].append(p)
    validate_material_catalog(*(data[n] for n in ('materials','reference_properties','sources')))
    after=Database(data)
    assert before.identities==after.identities and before.grades==after.grades and len(before.states)==len(after.states)
    assert all(after.properties[k]==v for k,v in before.properties.items())
    assert all(after.states[k]==v for k,v in before.states.items() if k!=state['id'])
    assert {k:v for k,v in parent.items() if k not in ('version','property_ids','source_scope')}=={k:v for k,v in state.items() if k not in ('version','property_ids','source_scope')}
    write('NEW_PROPERTY_R1.json',p);write('STATE_UPDATE_R1.json',dict(before=parent,after=state));write('SOURCE_UPDATE_R1.json',dict(before=source,after=updated))
    write('VALIDATION_R1.json',dict(baseline_snapshot=before.snapshot,candidate_snapshot=after.snapshot,properties=len(after.properties),states=len(after.states),new_properties=1,new_states_identities=0,old5415properties_unchanged=True,old_state_facts_unchanged=True,source_change='claim_notes_append_only',native_applied=False,installation='not_run'))
    print(json.dumps(dict(properties=len(after.properties),states=len(after.states),snapshot=after.snapshot,native_applied=False)))
if __name__=='__main__':main()
