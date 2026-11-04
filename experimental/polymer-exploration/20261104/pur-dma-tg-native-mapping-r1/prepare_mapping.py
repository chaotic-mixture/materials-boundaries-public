"""Draft four existing-PUR DMA Tg records with the already-supported contract."""
from copy import deepcopy
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
SOURCE = OUT.parent / 'pur-dma-tg-tga-followup-source-r1'
sys.path.insert(0, str(ROOT))
from materials_boundaries.database import Database
from materials_boundaries.material_references import validate_material_catalog


def read(path):
    return json.loads(path.read_bytes())


def write(name, value):
    with (OUT / name).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def main():
    facts = read(SOURCE / 'DMA_TG_CANDIDATES_R1.json')
    sid = facts['source_id']
    pdf = 'https://mdpi-res.com/d_attachment/polymers/polymers-16-00942/article_deploy/polymers-16-00942.pdf'

    def evidence(locator, *supports):
        return {'source_id': sid, 'url': pdf, 'locator': locator, 'supports': list(supports)}

    def fact(text=None, locator=None, notes=None, role='condition'):
        return {'status': 'reported' if text is not None else 'not_reported_in_inspected_source', 'text': text, 'evidence': [evidence(locator, role)] if locator else [], 'notes': notes}

    before = Database()
    assert before.snapshot == facts['baseline_snapshot']
    data = deepcopy(before.data)
    states, properties = [], []
    for candidate in facts['candidates']:
        label = candidate['source_label']
        parent = before.states[candidate['existing_density_state_id']]
        density = before.properties[parent['property_ids'][0]]
        assert density['quantity'] == 'mass_density' and parent['identity_id'] == candidate['existing_identity_id']
        state = deepcopy(parent)
        state.update(id=candidate['proposed_state_id'], version='1.0.0', property_ids=[candidate['proposed_property_id']])
        state['name'] = f'Ivdre 2024 {label} rigid PUR, DMA compression-oscillation cylinder'
        state['names'] = {'en': state['name'], 'zh': f'Ivdre 2024 {label} 硬质PUR，DMA压缩振荡圆柱', 'ja': f'Ivdre 2024 {label} 硬質PUR、DMA圧縮振動円柱', 'de': f'Ivdre 2024 {label} PUR-Hartschaum, DMA-Druckschwingungszylinder'}
        state['state']['product_form'] = fact('Rigid PUR DMA specimen, roughly 13 mm diameter and 7 mm height', 'PDF p8 §2.8 DMA paragraph', 'Approximate reported dimensions; not density specimens, thermal plates, static-compression cylinders or DSC pans.', 'state')
        state['state']['processing'] = fact(parent['state']['processing']['text'] + '; optimized foams prepared in larger30×30×10cm mold,24h room-temperature cure before further testing', 'PDF p7 §2.7', 'Numeric cure temperature unknown; preparation is not a complete humidity/equilibration procedure.', 'state')
        state['state']['conditioning'] = fact(notes='Post-cure RH, moisture, storage/equilibration time and any DMA-specific preparation unknown; cure retained under processing.')
        state['state']['orientation'] = fact(notes='DMA compression axis relative to foam-rise direction unknown; old scalar-density not_applicable and static-compression directions are not transferred.')
        state['state']['porosity']['notes'] = 'Source formulation-group closed-cell content, not total porosity, every DMA specimen or a temperature-resolved pore measurement.'
        state['source_scope'] = 'Existing optimized formulation identity, distinct source-reported DMA cylinder context. Shared recipe/preparation only; no new identity or certified independent physical coverage. No equivalence of density, heat-flow plate, static-compression, DSC or DMA sample geometry/conditioning. Direction relative to foam rise unknown.'
        state['evidence'] = [evidence(f'PDF pp7–8,16,19 §§2.7–2.8/Table9/Figure15(b), {label}', 'material_identity', 'state')]
        prop = deepcopy(density)
        prop.update(id=candidate['proposed_property_id'], version='1.0.0', material_state_id=state['id'], quantity='glass_transition_temperature', quantity_dimension='temperature', source_property_label=candidate['source_property_label'], reported_value={'kind': 'scalar', 'number': candidate['number'], 'value_text': candidate['value_text'], 'unit_code': 'degC', 'unit_text': '°C'}, reporting_basis='not_stated', summary_statistic='not_stated', density_basis=None, uncertainty=None, uncertainty_status='not_reported_in_inspected_source')
        prop['basis_note'] = 'Explicit source Figure15(b) printed annotation matched to the named curve/legend; not a digitized curve coordinate, mean-of-peaks, peak-of-mean-curve or fitted raw-data result. Caption identifies DMA tanδ-derived Tg; selected estimator unknown.'
        prop['uncertainty_note'] = 'No numerical dispersion attached to selected annotation; not inferred from curve breadth, nearby DSC values, TGA plus-minus or other-test counts.'
        prop['sample_count'] = {'value': None, 'relation': 'not_reported', 'scope': 'Contributors to the selected printed DMA Tg annotation and independent specimen/batch count unknown.', 'source_statement': 'The DMA paragraph and Figure15 do not state a selected DMA count; the three-or-more parallel samples statement occurs in the TGA paragraph and is not transferred.', 'evidence': [evidence('PDF p8 §2.8 separate DMA and TGA paragraphs;p19 Figure15', 'sample_count')]}
        scan = 'DMA scan25–220°C at3°C/min; cycle number and actual prior thermal history unknown'
        prop['conditions'] = {
            'temperature': fact(scan, 'PDF p8 §2.8 DMA paragraph', 'Source scan settings, not ambient temperature, a logged trace or a claim that the property is a group mean.'),
            'test_standard': fact(notes='No DMA standard named in inspected method; ISO844:2021 concerns static compression,not automatically this DMA experiment.'),
            'test_method': fact('Mettler Toledo DMA/SDTA861e compression oscillation; Figure15(b) source-labelled tanδ-peak Tg; roughly13mm diameter×7mm high cylinders;1Hz,5μm displacement amplitude,maximum force1N. ' + scan, 'PDF p8 §2.8;p19 Figure15(b)/caption', 'Not DSC inflection,storage-modulus onset,loss-modulus peak or a calibrated global-maximum extraction algorithm.'),
            'loading_rate': fact('Compression oscillation1Hz;displacement amplitude5μm;maximum force1N', 'PDF p8 §2.8 DMA paragraph', 'Amplitude peak/RMS convention unknown;maximum force is not a stated preload;no strain conversion or static10%/min-rate transfer.'),
            'direction': fact(notes='Compression direction relative to foam-rise direction unknown;source anisotropy doesnot establish isotropic Tg or mechanical behaviour.'),
            'conditioning': fact(notes='DMA-specific RH,equilibration,storage/drying and prior heating unknown;24h room-temperature cure is processing,not fullconditioning.'),
            'additional_conditions': [
                {'name': 'measurement_method_family', 'fact': fact('DMA', 'PDF p8 §2.8;p19 Figure15(b) caption', 'Not DSC,TGA or staticcompression.')},
                {'name': 'Tg_extraction_criterion', 'fact': fact('Source-labelled tanδ peak', 'PDF p19 Figure15(b), annotations andcaption', 'Source coordinate; peak fitting/interpolation/selection and scalar aggregation unknown.')},
                {'name': 'oscillation_frequency', 'fact': fact('1Hz', 'PDF p8 §2.8 DMA paragraph', 'No frequency normalization or time-temperature shift.')},
                {'name': 'displacement_amplitude', 'fact': fact('5μm', 'PDF p8 §2.8 DMA paragraph', 'Displacement,not measured strain;amplitude convention unknown.')},
                {'name': 'maximum_force', 'fact': fact('1N', 'PDF p8 §2.8 DMA paragraph', 'Maximum force,not a reported staticpreload.')},
                {'name': 'DMA_atmosphere_preload_and_cycle', 'fact': fact(notes='DMA gas/flow,staticpreload and heatingcycle number unknown;DSC nitrogen/secondheat andTGA counts nottransferred.')},
                {'name': 'smoothing_context', 'fact': fact('Adjacent-averaging smoothing for noise above170°C', 'PDF p8 §2.8 DMA paragraph', 'Source context only;no reprocessing of curves or correction of the explicit lower-temperature labels.')},
                {'name': 'transcription_locator', 'fact': fact(candidate['value_locator'], 'PDF p19 Figure15(b)', 'Visible printed annotation,not PDF text reading order or hidden draft text.')}
            ]}
        prop['method_definition'] = {'type': 'source_reported_conventional', 'definition': 'Source Figure15(b) printed DMA tanδ-peak Tg annotation,compression oscillation withDMA/SDTA861e;1Hz,5μm,max1N and25–220°C at3°C/min. Exact scalar aggregation,cycle,preload,peak fitting and direction unknown. Not DSC or a method-independent universal Tg.', 'extraction_window': None, 'evidence': [evidence('PDF p8 §2.8;p19 Figure15(b)/caption', 'method', 'classification')]}
        prop['source_discrepancies'] = []
        if label.startswith('LPO'):
            prop['source_discrepancies'].append({'description': 'Adjacent DSC paragraph first reports detection for LPO and later says LPO was not detected;group wording conflict unresolved.', 'disposition': 'Selected coordinate is the explicit DMA Figure15(b) annotation,not a DSC value;do not silently repair the DSC group name or infer method equivalence.', 'evidence': [evidence('PDF p19 paragraph aboveFigure15 andcaption', 'source_discrepancy')]})
        prop['evidence'] = [evidence(candidate['value_locator'], 'reported_value', 'classification'), evidence('PDF p8 §2.8 DMA paragraph;p19 Figure15(b)/caption', 'method', 'condition')]
        inspection = 'Same official23pagePDF,selected visiblepages1,7–8,16,19–20,23;four Figure15(b) author annotations/colour legends read directly. XML corroborates method/caption,not annotation numerics. Table11 TGA facts andDSC conflict reviewed separately,not admitted as these coordinates. No curve digitization,rawdata analysis or latestnotice confirmation.'
        prop['source_document'] = {'url': pdf, 'revision': 'Official article-deploy PDF retained2026-11-04;latest revision/correction/retraction unknown', 'inspected_on': '2026-11-04', 'sha256': facts['PDF_sha256'], 'hash_status': 'recorded', 'hash_note': None, 'inspection_scope': inspection, 'inspection_status': 'selected_content_inspected'}
        prop['scope_note'] = 'Study-specific method-qualified DMA coordinate,original integer°C annotation preserved. summary not_stated,nunknown,null numerical dispersion. No TGA3ormore,staticcompression6,DSC6mg/secondheat/nitrogen,water4days or40kg/m³ normalization transfer. Unknown RH/equilibration,gas,cycle,preload,amplitude convention,loading/foaming relation and estimator remain unknown. Not universal Tg,engineeringallowable,isotropy or calculator input.'
        prop['verification'] = {'source_inspection_scope': inspection, 'transcription_cross_check': 'completed', 'independent_scientific_review': False, 'raw_data_reanalysis': False}
        states.append(state)
        properties.append(prop)
    data['materials']['records'].extend(states)
    data['reference_properties']['records'].extend(properties)
    proposal = read(SOURCE / 'SOURCE_UPDATE_PROPOSAL_R1.json')
    assert before.sources[sid] == proposal['baseline_source']
    data['sources']['records'] = [proposal['proposed_source'] if s['id'] == sid else s for s in data['sources']['records']]
    validate_material_catalog(*(data[n] for n in ('materials', 'reference_properties', 'sources')))
    after = Database(data)
    assert data['materials']['records'][:-4] == before.data['materials']['records'] and data['reference_properties']['records'][:-4] == before.data['reference_properties']['records']
    assert after.identities == before.identities and after.grades == before.grades
    write('NEW_STATES_R1.json', states)
    write('NEW_PROPERTIES_R1.json', properties)
    write('SOURCE_UPDATE_PROPOSAL_R1.json', proposal)
    write('VALIDATION_R1.json', {'scope': 'Unapplied fourDMA Tg mapping with unchanged native quantity/schema', 'baseline_snapshot': before.snapshot, 'preview_snapshot': after.snapshot, 'candidate_properties': len(after.properties), 'candidate_states': len(after.states), 'new_properties_states': [4, 4], 'new_identities_grades_sources': 0, 'all_old5380properties5254states_unchanged': True, 'current_graph': 'passed', 'runtime_schema_changes': 0, 'native_applied': False, 'installation_fullhistory_HTTP': 'not_run', 'pushed': False})
    print(json.dumps({'candidate_properties': len(after.properties), 'candidate_states': len(after.states), 'snapshot': after.snapshot, 'native_changed': False}))


if __name__ == '__main__':
    main()
