"""Prepare four reviewed-source extraction-gel candidates; never write native tables."""
from pathlib import Path
from copy import deepcopy
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
BASE=HERE.parent;IMPL=BASE/'gel-fraction-implementation-r2';SOURCE=BASE/'pbs-density-gel-source-screen-r2'
sys.path.insert(0,str(ROOT))
from materials_boundaries.database import Database
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(n,obj):
    with (HERE/n).open('x',encoding='utf-8',newline='\n') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
    entry=IMPL/'REVIEW_IMPLEMENTATION_INPUTS_R2.json';approval=read(IMPL/'INDEPENDENT_IMPLEMENTATION_REVIEW_R2.json')
    assert approval['decision']=='approved' and approval['review_inputs_sha256']==sha(entry)
    for field in ('repo_files_sha256','external_files_sha256','native_files_sha256'):
        for n,h in read(entry)[field].items():assert sha(Path(n) if field=='external_files_sha256' else ROOT/n)==h,n
    before=Database();assert before.snapshot=='ef3b75e83de9315fb4099de7b9f64185094b50d7c9859d9ef9d74e10413907c8'
    facts=read(SOURCE/'SOURCE_FACTS_R2.json');url=facts['source_url'];sid=facts['source_id'];props=[];states=[]
    def ev(loc,*roles):return dict(source_id=sid,url=url,locator=loc,supports=list(roles))
    loc='Section2.4/Eq1;Section2.3 common preparation;Section3.2/Table1 Gel Fraction column'
    def unknown(note):return dict(status='not_reported_in_inspected_source',text=None,evidence=[ev(loc,'condition')],notes=note)
    def reported(text,note):return dict(status='reported',text=text,evidence=[ev(loc,'method','condition')],notes=note)
    for row in facts['rows']:
        if row['gel_fraction_value'] is None:continue
        label=row['source_label'];key=label.lower();old=before.states[f'state_ewurum2025_{key}_reported_density'];state=deepcopy(old)
        state.update(id=f'state_ewurum2025_{key}_hotpressed_gel_extraction',version='1.0.0',name=f'{label} hot-pressed solvent-extraction gel context',names={'en':f'{label} hot-pressed solvent-extraction gel context','zh':f'{label} 热压溶剂萃取凝胶方法语境','ja':f'{label} 熱プレス溶媒抽出ゲル測定','de':f'{label} Heißpressen und Gelbestimmung durch Extraktion'},property_ids=[])
        state['state']['product_form']=reported('Source hot-pressed DCP-crosslinked PBS-lignin material for gel-fraction analysis','Actual gel aliquot mass,geometry and lineage to common disc/strip route unknown;not density,DSC or injection-molded tensile specimen.')
        state['state']['product_form']['evidence']=[ev('Section2.4 hot-pressed materials;Section2.3 common preparation','state')]
        state['state']['temper_or_heat_treatment']=unknown('Actual gel-aliquot hot-press temperature/pressure/dwell not individually established. Common Section2.3 background120C/30g/75mm/3.1mm is not assigned as actual aliquot facts.')
        state['state']['conditioning']=unknown('Gel-specific storage,RH and conditioning unknown;pre-extrusion80C12h is not gel48h vacuum drying.')
        state['state']['processing']['notes']='Common extrusion background retained;source Section2.4 explicitly says hot-pressed gel materials. Exact route and gel aliquot linkage to Section2.3 discs/strips unknown. No density,DSC or injection-molded tensile specimen linkage inferred.'
        for field in ('porosity','orientation'):state['state'][field]=unknown('Not established for selected hot-pressed extraction-gel aliquot;no density-specimen facts transferred.')
        state['source_scope']=f'Existing {label} identity;separate hot-pressed CHCl3-extraction gel method context,not a new material or independent batch/specimen. Wgel/W0 source labels retained without dry-basis,network-purity,extraction-completeness or crosslink-density certification. No density/DSC/injection-molding specimen lineage inferred.'
        state['evidence']=[ev(loc,'state')]
        p=deepcopy(before.properties[f'refprop_ewurum2025_{key}_reported_mass_density'])
        p.update(id=f'refprop_ewurum2025_{key}_solvent_extraction_gel_fraction',material_state_id=state['id'],quantity='solvent_extraction_gel_fraction_percentage',quantity_dimension='dimensionless',source_property_label='Gel Fraction (%)',density_basis=None)
        p['reported_value'].update(number=row['gel_fraction_value'],value_text=row['gel_fraction_value'],unit_code='percent_solvent_extraction_gel_fraction',unit_text='%')
        for field in p['conditions']:p['conditions'][field]=[] if field=='additional_conditions' else unknown('Not established for selected extraction-gel result;no facts transferred from density,DSC or mechanical tests.')
        p['conditions']['test_method']=reported('CHCl3 Soxhlet extraction48h;undissolved gel collected and vacuum-oven dried48h;reported Wgel/W0x100','Extraction temperature,solvent renewal,drying temperature/vacuum pressure and endpoint unreported;not precursor80C12h.')
        p['gel_fraction_definition']=dict(basis='source_reported_solvent_extraction_gel_fraction_percentage',numerator_and_denominator=reported('Source Eq1 Gel fraction(%)=(Wgel/W0)x100','Original symbols only. W0 dry-basis/preparation and Wgel residual-solvent/lignin contribution unknown;not pure network mass.'),solvent_identity=reported('CHCl3 source extraction solvent','Purity,volume and renewal protocol unknown.'),extraction_protocol=reported('Soxhlet extraction48h to remove source soluble sol fraction','Temperature,cycles,extraction completeness and solvent changes unknown;48h is not sample count.'),residue_collection_and_drying=reported('Undissolved gel collected and dried in vacuum oven48h','Drying temperature,pressure,dry-endpoint criterion and residual solvent unknown;do not transfer precursor80C12h.'),starting_specimen_preparation=reported('Source Section2.4 hot-pressed DCP-crosslinked PBS-lignin copolymers;common Section2.3 background120C,30gcharge,75mmdie,3.1mmdisc and cut strips','Actual gel aliquot connection,geometry,mass,pressure,dwell unknown;PHI30-ton is equipment designation,not applied force.'),corrections_and_recovery=unknown('Lignin/ash/residual-solvent correction,W0 dry basis,blank corrections and quantitative recovery unknown.'),replication_and_piece_relationship=unknown('Per-cell n,aggregation,uncertainty and independent pieces/batches unknown. No mechanical sample counts transferred.'),conditioning_and_storage=unknown('Gel-aliquot conditioning,RH,storage and pre-extraction moisture unknown.'),evidence=[ev(loc,'method','condition')],notes='Source-reported insoluble gel percentage only;do not compute sol fraction,crosslink density,network purity or corrected dry-polymer fraction.')
        p['uncertainty_note']='No gel-fraction uncertainty or central aggregation specified;missing uncertainty is not zero.'
        p['basis_note']='Direct Table1 Gel Fraction percentage literal;source Eq1 supplies Wgel/W0 ratio semantics,not software recomputation. Statistical centre,n,uncertainty and detailed denominator basis unknown.'
        p['sample_count'].update(scope='Selected Table1 gel-fraction cell;48h durations are not replicates',source_statement='No per-cell gel sample count established.',evidence=[ev(loc,'condition')])
        p['method_definition'].update(definition='Source conventional Soxhlet-extraction gel-fraction result,Eq1 Wgel/W0x100;no numerical reconstruction or dry-basis inference.',evidence=[ev(loc,'method','classification')])
        p['evidence']=[ev('Table1 '+label+' row x Gel Fraction(%)','reported_value','classification'),ev(loc,'method','condition')]
        p['source_document'].update(inspection_scope='Main XML Sections2.1-2.4,3.2,Table1 andEq1;no new PDF visual inspection')
        p['verification']['source_inspection_scope']=p['source_document']['inspection_scope']
        p['scope_note']=state['source_scope']+' CHCl3 extraction48h/vacuum drying48h preserved;temperature and exact dry endpoint unknown. Source dash cells are not zero. Catalog only,not engineering allowable.'
        assert p['id'] not in before.properties and state['id'] not in before.states
        state['property_ids']=[p['id']];props.append(p);states.append(state)
    assert len(props)==len(states)==4
    data=deepcopy(before.data);data['reference_properties']['records'].extend(props);data['materials']['records'].extend(states)
    after=Database(data);after.validate_scientific_contracts()
    assert all(after.properties[k]==v for k,v in before.properties.items()) and all(after.states[k]==v for k,v in before.states.items())
    assert after.identities==before.identities and after.grades==before.grades and after.sources==before.sources
    write('NEW_PROPERTIES_R1.json',props);write('NEW_STATES_R1.json',states)
    write('VALIDATION_R1.json',dict(candidate_snapshot=after.snapshot,properties=len(after.properties),states=len(after.states),sources=len(after.sources),new_properties=4,new_contexts=4,old5700properties_unchanged=True,old5407states_unchanged=True,identity_grade_source_objects_unchanged=True,native_applied=False,installation='not_run',tests='not_run_candidate_graph_only'))
    print(json.dumps(dict(snapshot=after.snapshot,properties=len(after.properties),states=len(after.states),native_applied=False)))
if __name__=='__main__':main()
