"""Create a separate candidate only after the frozen implementation is approved."""
from copy import deepcopy
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))


def main():
    load=lambda p:json.loads(p.read_text('utf-8'))
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    impl=HERE.parent/'ftir-band-area-ratio-implementation-r1'
    entry=impl/'REVIEW_IMPLEMENTATION_INPUTS_R1.json'
    receipt=load(impl/'INDEPENDENT_IMPLEMENTATION_REVIEW_R1.json')
    assert receipt['decision']=='approved' and receipt['review_inputs_sha256']==sha(entry)
    for section in ('repo_files_sha256','external_files_sha256','native_files_sha256'):
        for path,h in load(entry)[section].items():assert sha(ROOT/path if not Path(path).is_absolute() else Path(path))==h,path
    from materials_boundaries._ftir_band_area_ratio_contract import QUANTITY,UNIT,METHOD,PROFILE,WAVENUMBER_UNIT,FACT_FIELDS
    from materials_boundaries.material_references import validate_material_catalog
    materials=load(ROOT/'materials_boundaries/data/materials.json')
    properties=load(ROOT/'materials_boundaries/data/reference_properties.json')
    sources=load(ROOT/'materials_boundaries/data/sources.json')
    old=next(p for p in properties['records'] if p['id']=='refprop_abbasi2022_manure_phbv39_source_dsc_crystallinity')
    state=deepcopy(next(s for s in materials['records'] if s['id']==old['material_state_id']))
    source=old['source_id'];url=old['source_document']['url'];loc='Section2.2.4 FTIR;Section3.3/Table4 PHBV-39 x I_C=O'
    def ev(*roles,locator=loc):return [dict(source_id=source,url=url,locator=locator,supports=list(roles))]
    def unknown(note):return dict(status='not_reported_in_inspected_source',text=None,evidence=ev('condition'),notes=note)
    def reported(text,note):return dict(status='reported',text=text,evidence=ev('method','condition'),notes=note)
    property_id='refprop_abbasi2022_manure_phbv39_ftir_fitted_carbonyl_area_ratio'
    state_id='state_abbasi2022_manure_phbv39_ftir_fitted_carbonyl_area_ratio'
    scope='Existing PHBV-39 identity;source-only Gaussian carbonyl fitted-area-ratio method context,not new material,independent specimen or calibrated phase fraction. Actual spectrum/aliquot pairing and per-cell acquisition provenance unresolved. No DSC,mechanical or rheology specimen conditions transferred.'
    state.update(id=state_id,name='PHBV-39 FTIR fitted carbonyl area-ratio context',names=dict(en='PHBV-39 FTIR fitted carbonyl area-ratio context',zh='PHBV-39 FTIR拟合羰基带面积比方法语境',ja='PHBV-39 FTIRフィットカルボニル帯面積比',de='PHBV-39 FTIR-Flächenverhältnis der Carbonylbanden'),source_scope=scope,property_ids=[property_id],evidence=ev('state'))
    for name in state['state']:
        if name=='composition_or_purity':
            state['state'][name]['evidence']=ev('state',locator='Section2.2.1 extraction;Table1 PHBV-39 purified composition')
        else:state['state'][name]=unknown('Actual FTIR ratio aliquot history/detail not established;other-method facts are not transferable.')
    state['state']['product_form']=dict(status='reported',text='Source purified PHBV-39 sample',evidence=ev('state',locator='Section2.2.1 extraction;Section3.3/Table4 PHBV-39 label'),notes='Operational-day label39,not39%HV;source material context,not confirmed spectral aliquot or geometry.')
    p=deepcopy(old);p.update(id=property_id,material_state_id=state_id,quantity=QUANTITY,source_property_label='I_C=O',reported_value=dict(kind='scalar',number='2.35',value_text='2.35',unit_code=UNIT,unit_text='ratio'),basis_note='Source reports Gaussian fitting and integration of carbonyl bands followed by A1720/A1740 ratio. This project transcribes the source result and does not fit,integrate,divide or infer raw areas.',scope_note=scope,source_discrepancies=[])
    p['conditions']={name:([] if name=='additional_conditions' else unknown('Not established for the selected FTIR area-ratio result;do not borrow DSC,mechanical or rheology conditions.')) for name in old['conditions']}
    p['conditions']['test_method']=reported('ATR-FTIR on Nicolet-iS5 with ZnSe ID5;Omnicv9.5 baseline correction/averaging;normalized spectra Gaussian-fitted in IgorPro9;source half-height width10cm^-1 for1720 and1740cm^-1 bands,then integration and area ratio.','Algorithm details,fit/integration intervals and per-cell operation ordering unresolved.')
    p['method_definition']=dict(type=METHOD,definition='Source-reported Gaussian fitted integrated carbonyl-band area ratio A1720/A1740;not peak-height ratio,concentration or DSC crystallinity.',extraction_window=None,evidence=ev('method','classification'))
    p['sample_count']=dict(value=None,relation='not_reported',scope='Selected FTIR area-ratio cell;independent pieces,batches and exact n unresolved',source_statement='Common FTIR method reports duplicate;this does not establish independent cell-level n or averaging/ratio ordering.',evidence=ev('condition',locator='Section2.2.4 common FTIR duplicate'))
    p['uncertainty_note']='Per-cell numeric uncertainty and central statistic not specified;no SD/CI inferred from duplicate or other-table footnotes.'
    p['evidence']=ev('reported_value',locator='Table4 PHBV-39 row x FTIR I_C=O cell')+ev('method','classification')
    inspected='MainXML Sections2.2.1,2.2.4,3.3 and Table4 PHBV-39 FTIR column;Section3.4 provenance statement inDSC context;no spectral digitization or newPDF/supplement visual review'
    p['source_document'].update(inspection_scope=inspected)
    p['verification'].update(source_inspection_scope=inspected)
    d=dict(schema_version='1.0.0',profile_id=PROFILE,profile_version='1.0.0',executor='source_reported_only',formula_family='source_ordered_fitted_area_ratio',lineshape='source_reported_gaussian',evidence=ev('method','classification'),notes='Author-reported fitted area ratio only;raw areas/sign of denominator not established by positive band coordinates. No software reconstruction or quantitative phase calibration.')
    for name in FACT_FIELDS:d[name]=unknown('Method-specific detail not established in inspected FTIR text.')
    d['reported_formula']=reported('Source carbonyl index I_C=O=A1720/A1740 using integrated Gaussian-fitted carbonyl bands.','Ordered source roles retained;not reciprocal or raw peak heights.')
    d['spectrometer_and_acquisition_mode']=reported('Nicolet-iS5 FTIR with ZnSe ID5 ATR accessory.','Contact pressure,scan count,resolution and actual per-cell acquisition unknown.')
    d['band_assignments_as_author_interpretation']=reported('Source assigns1720cm^-1 crystalline and1740cm^-1 amorphous PHBV carbonyl bands.','Author interpretation only;ratio not calibrated phase fraction,concentration or DSC Xc.')
    d['baseline_and_normalization']=reported('Source spectra baseline corrected and averaged using Omnicv9.5;normalized spectra used for subsequent fitting.','Normalization algorithm/reference and baseline specification not reported.')
    d['fit_model_width_constraints_and_intervals']=reported('IgorPro9 Gaussian fits for1720/1740cm^-1 carbonyl bands;source peak width at half height10cm^-1;fitted bands integrated.','Fit constraints,fit intervals,component count beyond selected bands and integration bounds unknown.')
    d['integration_and_ratio_averaging_order']=unknown('Source describes integrated areas and averaged spectra but does not establish replicate-level integrate/average/ratio ordering;do not invent it.')
    d['sample_preparation_conditioning']=reported('Section2.2.1 reports common extraction/purification ending in vacuum drying of purified PHBV.','Common source background only;actual FTIR aliquot drying schedule,storage,conditioning,temperature and humidity unknown. No mechanical hot-pressing or DSC cycles transferred.')
    d['source_data_attribution']=dict(status='not_verified',text=None,evidence=ev('condition',locator='Sections2.2.4/3.3/Table4;Section3.4 DSC discussion'),notes='Single FTIR cell acquisition/reanalysis origin unresolved. Section3.4 mixed Guho/reanalyzed sentence is inDSC discussion;does not establish FTIR inheritance or a new2022 experiment.')
    d['replication_and_statistics']=reported('FTIR common method says analyses in duplicate.','No direct per-cell exactn or independent specimen/batch inference;uncertainty and summary statistic unresolved.')
    for name,number in [('numerator_band','1720'),('denominator_band','1740')]:
        d[name]=dict(role='gaussian_fitted_integrated_carbonyl_band_area',number=number,value_text=number,unit_code=WAVENUMBER_UNIT,unit_text='cm⁻¹',evidence=ev('method','classification',locator='Section2.2.4 A1720/A1740 and Gaussian band integration'),notes='Source band coordinate,not a reported raw area or its positivity;ordered role preserved.')
    d['source_result_cell']=dict(table_id='polymers-14-04140-t004',row_key='PHBV-39',column_key='I_C=O',evidence=ev('reported_value','classification',locator='Table4 PHBV-39 row x FTIR I_C=O cell'),notes='OriginalXML table row/column;definition,coordinate or statistical clarification revises this cell.')
    p['derivation']=d
    candidate_materials=deepcopy(materials);candidate_properties=deepcopy(properties)
    candidate_materials['records'].append(state);candidate_properties['records'].append(p)
    validate_material_catalog(candidate_materials,candidate_properties,sources)
    def write(path,obj):
        with path.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
    write(HERE/'NEW_STATES_R1.json',[state]);write(HERE/'NEW_PROPERTIES_R1.json',[p])
    write(HERE/'VALIDATION_R1.json',dict(candidate_graph_valid=True,new_properties=1,new_contexts=1,new_identities=0,new_sources=0,properties=len(candidate_properties['records']),states=len(candidate_materials['records']),native_applied=False,scope='One full isolated candidate graph;not regression,installation or independent review'))
    print('Candidate graph5754/5432/134 validated;native unchanged',flush=True)


if __name__=='__main__':main()
