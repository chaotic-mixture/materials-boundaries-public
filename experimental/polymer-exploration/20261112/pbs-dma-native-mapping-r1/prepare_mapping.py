"""Prepare36 source-qualified DMA cells in9method contexts without native writes."""
from pathlib import Path
from copy import deepcopy
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent;BASE=HERE.parent
IMPL=BASE/'dma-implementation-r1';SOURCE=BASE/'pbs-dma-storage-loss-source-screen-r1'
sys.path.insert(0,str(ROOT))
from materials_boundaries.database import Database
from materials_boundaries._dma_flexural_contract import QUANTITIES
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(n,obj):
    with (HERE/n).open('x',encoding='utf-8',newline='\n') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
    entry=IMPL/'REVIEW_IMPLEMENTATION_INPUTS_R1.json';approval=read(IMPL/'INDEPENDENT_IMPLEMENTATION_REVIEW_R1.json')
    assert approval['decision']=='approved' and approval['review_inputs_sha256']==sha(entry)
    frozen=read(entry)
    for field in ('repo_files_sha256','external_files_sha256','native_files_sha256'):
        for n,h in frozen[field].items():assert sha(Path(n) if field=='external_files_sha256' else ROOT/n)==h,n
    before=Database();assert before.snapshot=='06ded10fa2f0d2b5f8ee48793100d1a9041547636ae851544436db4179c19140'
    facts=read(SOURCE/'SOURCE_FACTS_R1.json');sid=facts['source_id'];url=facts['source_url']
    def ev(loc,*roles):return dict(source_id=sid,url=url,locator=loc,supports=list(roles))
    methodloc='Section2.8 DMA paragraph;Section3.4 and Table3'
    def unknown(note):return dict(status='not_reported_in_inspected_source',text=None,evidence=[ev(methodloc,'condition')],notes=note)
    def reported(text,note):return dict(status='reported',text=text,evidence=[ev(methodloc,'method','condition')],notes=note)
    states=[];props=[]
    for label in sorted({x['source_label'] for x in facts['selected_rows']}):
        key=label.lower();old=before.states[before.properties[f'refprop_ewurum2025_{key}_dma_glass_transition_temperature']['material_state_id']];state=deepcopy(old)
        state.update(id=f'state_ewurum2025_{key}_flexural_dma_channels',version='1.0.0',name=f'{label} flexural DMA source-channel context',names={'en':f'{label} flexural DMA channel context','zh':f'{label} 弯曲DMA通道方法语境','ja':f'{label} 曲げDMA信号測定','de':f'{label} Biege-DMA Signalkontext'},aliases=[],property_ids=[])
        for field in state['state']:state['state'][field]=unknown('Not established for selected flexural DMA method context;no density,gel,DSC or tensile facts transferred.')
        for field in ('composition_or_purity','reinforcement'):
            state['state'][field]=deepcopy(old['state'][field]);state['state'][field]['evidence']=[ev('Sections2.1-2.3;formulation '+label,'state')]
        state['state']['product_form']=dict(status='reported',text='Rectangular DMA bars3x5x20mm,source dimension order retained',evidence=[ev('Section2.8 DMA paragraph','state')],notes='Nominal source geometry;material axes,tolerances and actual bar lineage unknown. Common hotpress3.1mm disc background does not establish finishing or specimen pairing.')
        state['state']['processing']=dict(status='reported',text='Common formulation single-screw extrusion140°C,3mm strands and pelletization',evidence=[ev('Section2.3','state')],notes='Background only. Common hotpress120°C/30g/75mm/3.1mm described inSection2.3 does not assign actual DMA bar route,pressure or dwell. PHI30-ton is equipment rating. No injection-molding or gel/density/DSC lineage certified.')
        state['state']['temper_or_heat_treatment']=dict(status='reported',text='DMA temperature scan−50to120°C at3°C/min',evidence=[ev('Section2.8 DMA paragraph','state')],notes='Test program,not processing/annealing or DSC history;cycle,hold,calibration and actual trace unknown.')
        state['source_scope']=f'Existing {label} formulation identity;source flexural DMA method context for2temperatures x2channels,not a new material or independent physical coverage. Actual pairing/run/batch among four cells or to Tg,gel,density,DSC,tensile records unknown. Unresolved BioPBS grade and R0 exclusion remain. Common triplicate does not establish each cell independent n3.'
        state['evidence']=[ev('Sections2.1-2.3;Section2.8;Table3 '+label,'state')]
        for row in [x for x in facts['selected_rows'] if x['source_label']==label]:
            quantity='dma_flexural_storage_modulus' if row['source_property_label']=='E′' else 'dma_flexural_loss_tangent';unit,dimension=QUANTITIES[quantity];temp=row['temperature_value_text'];tag='minus50c' if temp=='-50' else '10c'
            p=deepcopy(before.properties[f'refprop_ewurum2025_{key}_reported_mass_density'])
            p.update(id=f'refprop_ewurum2025_{key}_{quantity}_{tag}',material_state_id=state['id'],quantity=quantity,quantity_dimension=dimension,source_property_label=row['source_property_label']+' at '+temp+'°C',density_basis=None)
            p['reported_value'].update(number=row['source_value_text'],value_text=row['source_value_text'],unit_code=unit,unit_text='GPa' if dimension=='pressure' else 'dimensionless')
            cell='Table3 '+label+' row x '+row['source_property_label']+' at '+temp+'°C column'
            cell_evidence=[ev(cell,'condition','classification'),ev('Section2.8 DMA paragraph','method','condition')]
            p['dma_measurement_temperature']=dict(status='reported',number=temp,value_text=temp,unit_code='degC',unit_text='°C',evidence=deepcopy(cell_evidence),notes='Selected table measurement coordinate,not ambient or service limit;calibration/equilibration unknown.')
            p['dma_oscillation_frequency']=dict(status='reported',number='1',value_text='1',unit_code='Hz',unit_text='Hz',evidence=deepcopy(cell_evidence),notes='Source common cyclic frequency1Hz applied to selected cell;no angular/shear conversion or n inference.')
            for field in p['conditions']:p['conditions'][field]=[] if field=='additional_conditions' else unknown('Not established for selected DMA scalar;source common triplicate is not independent per-cell statistics.')
            p['conditions']['temperature']=reported('Selected DMA measurement temperature '+temp+'°C','SourceTable3 coordinate;not laboratory ambient or operating limit.')
            p['conditions']['test_method']=reported('Perkin Elmer DMA-7,threepoint bending15mm span,3x5x20mm bars,1Hz,0.2%strain,scan−50to120°C at3°C/min;Pyrisv13.3','Amplitude convention,LVR,clamp/preload corrections,calibration and actual signal aggregation unknown;not static modulus or Tg peak extraction.')
            p['dma_definition']=dict(basis='source_reported_flexural_DMA',apparatus_and_bending_geometry=reported('DMA-7 threepoint bending,15mm span and3x5x20mm rectangular bars','Source nominal geometry;actual tolerances,axes,preload and clamping correction unknown.'),strain_amplitude_and_convention=reported('Source strain0.2%','Peak/peak-to-peak/RMS convention and LVR validation unknown.'),temperature_program_and_control=reported('Source−50to120°C temperature scan at3°C/min;selected cell at'+temp+'°C','Temperature calibration,actual trace,equilibration,holds and prior cycles unknown.'),frequency_protocol=reported('Source common DMA cyclic frequency1Hz','No frequency-to-shear/angle conversion;not replicate count.'),signal_channel_and_reduction=reported('SourceTable3 '+row['source_property_label']+' scalar;Section3.4 storage modulus/tan delta discussion;Pyrisv13.3 analysis','No E-doubleprime/complex modulus reconstruction,static/dielectric equivalence or per-point statistical reduction inferred.'),specimen_preparation_and_lineage=reported('Source DMA rectangular bars;common extrusion/hotpress preparation background described separatelySection2.3','Actual selected bars,forming route,pressure/dwell and same-run/piece linkage between cells or to other methods unknown.30-ton is not applied pressure.'),replication_and_statistics=reported('DMA method performed in triplicate','Common method statement only;per-cell independent n,central aggregation,uncertainty and batch count unknown.2temperatures x2channels x3 is not12specimens.'),conditioning_and_corrections=unknown('DMA RH,storage,moisture equilibration,LVR,clamp/compliance and temperature correction details unknown;no precursor80C12h assigned.'),evidence=[ev(methodloc,'method','condition')],notes='Direct source flexural DMA channel,not static modulus,dielectric loss,engineering allowable or independent physical-sample coverage.')
            p['basis_note']='Direct selected Table3 scalar,not graph digitization or a calculated channel. GPa printed for Eprime;tan delta has no physical unit printed and is represented as a dimensionless ratio,not percent.'
            p['uncertainty_note']='Selected cell central aggregation and numerical uncertainty unknown;not mean/SD inferred from triplicate.'
            p['sample_count']=dict(value=None,relation='not_reported',scope='SelectedTable3 DMA scalar;independent pieces and per-cell n unresolved',source_statement='DMA performed in triplicate as common method statement;per-cell independent n unknown.',evidence=[ev('Section2.8 DMA paragraph','condition')])
            p['method_definition'].update(definition='Source-reported flexural DMA '+row['source_property_label']+' at selected temperature and1Hz;no static conversion,loss-modulus computation or Tg-peak reuse.',evidence=[ev(methodloc,'method','classification')])
            p['evidence']=[ev(cell,'reported_value','classification'),ev(methodloc,'method','condition')]
            p['source_document'].update(inspection_scope='MainXML Sections2.1-2.3,2.8,3.4 andTable3 selected Eprime/tan-delta cells;no newPDF visual inspection')
            p['verification']['source_inspection_scope']=p['source_document']['inspection_scope'];p['scope_note']=state['source_scope']+' Source measurement coordinates and original decimal precision retained. LVR,amplitude convention,corrections,statistics and exact bar lineage unknown.'
            assert p['id'] not in before.properties;state['property_ids'].append(p['id']);props.append(p)
        assert len(state['property_ids'])==4;assert state['id'] not in before.states;states.append(state)
    assert len(props)==36 and len(states)==9
    data=deepcopy(before.data);data['materials']['records'].extend(states);data['reference_properties']['records'].extend(props);after=Database(data);after.validate_scientific_contracts()
    assert all(after.properties[k]==v for k,v in before.properties.items()) and all(after.states[k]==v for k,v in before.states.items())
    assert after.identities==before.identities and after.grades==before.grades and after.sources==before.sources
    write('NEW_PROPERTIES_R1.json',props);write('NEW_STATES_R1.json',states)
    write('VALIDATION_R1.json',dict(candidate_snapshot=after.snapshot,properties=len(after.properties),states=len(after.states),sources=len(after.sources),new_properties=36,new_contexts=9,old5704properties_unchanged=True,old5411states_unchanged=True,identities_grades_sources_unchanged=True,native_applied=False,installation='not_run',tests='not_run_candidate_graph_only'))
    print(json.dumps(dict(snapshot=after.snapshot,properties=len(after.properties),states=len(after.states),native_applied=False)))
if __name__=='__main__':main()
