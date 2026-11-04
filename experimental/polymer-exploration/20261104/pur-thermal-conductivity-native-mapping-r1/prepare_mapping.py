"""Unapplied four-PUR plate mapping using the isolated conductivity contract."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
SOURCE = OUT.parent / 'pur-thermal-conductivity-source-contract-r1'
PROTOTYPE = ROOT.parent / 'open-database-evidence/polymer-thermal-conductivity-contract-prototype-20261104-r1'
sys.path.insert(0, str(PROTOTYPE))
from materials_boundaries.database import Database, canonical
from materials_boundaries.material_references import validate_material_catalog


def read(path):
    return json.loads(path.read_bytes())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(name, value):
    with (OUT / name).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def main():
    facts = read(SOURCE / 'SOURCE_FACTS_R1.json')
    sid = facts['source_id']
    pdf = 'https://mdpi-res.com/d_attachment/polymers/polymers-16-00942/article_deploy/polymers-16-00942.pdf'

    def evidence(locator, *supports):
        return {'source_id': sid, 'url': pdf, 'locator': locator, 'supports': list(supports)}

    def fact(text=None, locator=None, notes=None, role='condition'):
        return {'status': 'reported' if text is not None else 'not_reported_in_inspected_source', 'text': text,
                'evidence': [evidence(locator, role)] if locator else [], 'notes': notes}

    before = Database()
    data = deepcopy(before.data)
    states, properties = [], []
    for candidate in facts['candidates']:
        label = candidate['source_label']
        original_state = before.states[candidate['existing_density_state_id']]
        density = before.properties[original_state['property_ids'][0]]
        assert density['quantity'] == 'mass_density' and original_state['identity_id'] == candidate['existing_identity_id']
        state = deepcopy(original_state)
        state.update(id=candidate['proposed_plate_state_id'], version='1.0.0', property_ids=[candidate['proposed_property_id']])
        state['name'] = f'Ivdre 2024 {label} rigid PUR, heat-flow plate'
        state['names'] = {'en': state['name'], 'zh': f'Ivdre 2024 {label} 硬质PUR热流板', 'ja': f'Ivdre 2024 {label} 硬質PUR熱流測定板', 'de': f'Ivdre 2024 {label} PUR-Hartschaum, Wärmeflussplatte'}
        state['state']['product_form'] = fact('Optimized rigid PUR heat-flow specimen, source-reported 200 × 200 × 30 mm plate', 'PDF p7 §2.8', 'Dimensions of the thermal test specimen, not density specimens, compression cylinders or water-absorption cubes. Individual dimensions and sampling location unknown.', 'state')
        state['state']['processing'] = fact(original_state['state']['processing']['text'] + '; larger 30 × 30 × 10 cm mold; 24 h room-temperature cure before further testing', 'PDF p7 §2.7', 'Numeric cure temperature is not given. Cure is processing, not measured moisture equilibrium or a complete post-cure conditioning procedure.', 'state')
        state['state']['conditioning'] = fact(notes='Post-cure RH, moisture, equilibration interval and time since foaming or gas ageing unknown; the 24 h room-temperature cure is processing only.')
        state['state']['orientation'] = fact(notes='Heat-flow direction relative to the foam-rise direction unknown; source geometric anisotropy does not establish isotropic thermal conductivity.')
        state['state']['porosity']['notes'] = 'Source formulation-level closed-cell content, not total porosity or a measurement on every selected thermal plate.'
        state['source_scope'] = 'Existing optimized formulation identity with a distinct heat-flow plate context. Shared source preparation and composition only; not another identity or certified independent physical coverage. Thermal plate geometry differs from density/compression/DMA/water-absorption tests. Heat-flow/foam-rise relation, plate skin/location/contact, moisture equilibration and gas ageing unknown.'
        state['evidence'] = [evidence(f'PDF pp7,16–17 §§2.7–2.8, Tables9–10 {label}', 'state', 'material_identity')]
        prop = deepcopy(density)
        prop.update(id=candidate['proposed_property_id'], version='1.0.0', material_state_id=state['id'], quantity='thermal_conductivity', quantity_dimension='power_per_length_temperature', source_property_label=candidate['source_property_label'], reported_value={'kind': 'scalar', 'value_text': candidate['value_text'], 'number': candidate['number'], 'unit_code': 'mW/(m*K)', 'unit_text': candidate['unit_text']}, reporting_basis='not_stated', summary_statistic='not_stated', density_basis=None, uncertainty=None, uncertainty_status='not_reported_in_inspected_source')
        prop['basis_note'] = 'Selected optimized-foam Table10 thermal-conductivity cell, not a modeled target, intrinsic solid-polymer constant or density-normalized compression result. Statistical estimator is not specified; average test temperature is not a group-mean statement.'
        prop['uncertainty_note'] = 'No numerical dispersion stated for selected thermal-conductivity cells; neighbouring water-absorption plus-minus values and other thermal/mechanical repeats are not transferred.'
        prop['sample_count'] = {'value': None, 'relation': 'not_reported', 'scope': 'No unambiguous n for this selected optimized-foam heat-flow result; cup screening3, compression6 and TGA3ormore are separate.', 'source_statement': 'The inspected thermal-conductivity method and selected Table10 cell do not identify a specific replicate count.', 'evidence': [evidence('PDF pp7–8 §2.7–2.8; p17 Table10', 'sample_count')]}
        prop['conditions'] = {
            'temperature': fact('Mean test temperature 10 °C; cold plate 0 °C and hot plate +20 °C', 'PDF p7 §2.8; p17 Table10 thermal-conductivity row', 'Apparatus temperatures as reported; not ambient temperature or a statistical aggregation claim.'),
            'test_standard': fact('ISO 8301:1991, source-reported', 'PDF p7 §2.8; p23 reference36', 'Standard text, calibration and compliance not independently verified.'),
            'test_method': fact('FOX 200 heat-flow apparatus; 200 × 200 × 30 mm foam specimens', 'PDF p7 §2.8', 'Source-reported method; exact calibration, reduction implementation and contact treatment unknown.'),
            'conditioning': fact(notes='RH, moisture, post-cure equilibration interval and gas ageing unknown. 24 h room-temperature curing is processing; four-day water immersion belongs to water absorption.'),
            'loading_rate': fact(notes='No thermal scan/loading rate assigned; compression10%/min, DSC and TGA ramp rates are other tests and not transferred.'),
            'direction': fact(notes='Heat-flow direction relative to foam rise unknown; no isotropy inference from geometric anisotropy or nominal plate geometry.'),
            'additional_conditions': [
                {'name': 'skin_location_and_contact', 'fact': fact(notes='Foam skin removal, location in casting, plate-contact pressure and interface treatment unknown.')},
                {'name': 'ambient_pressure_and_atmosphere', 'fact': fact(notes='Thermal-test ambient pressure and atmosphere unknown; other-test nitrogen not transferred.')},
                {'name': 'density_normalization', 'fact': fact(notes='Source40kg/m³ normalization explicitly applies to compressive strength/modulus; no such correction inferred for selected thermal-conductivity cells.')}
            ]}
        prop['method_definition'] = {'type': 'source_reported_conventional', 'definition': 'Source-reported foam heat-flow thermal-conductivity coefficient measured with FOX200 at average test temperature10°C, cold plate0°C and hot plate20°C, per author ISO8301:1991 claim. Literal Table10 value retained; not intrinsic neat-polymer conductivity, heat-transfer coefficient or density-normalized mechanical value.', 'extraction_window': None, 'evidence': [evidence('PDF p7 §2.8; p17 Table10; p23 reference36', 'method', 'classification')]}
        prop['source_discrepancies'] = []
        prop['evidence'] = [evidence(f'PDF p17 Table10 thermal-conductivity row/{label}; p7 §2.8', 'reported_value', 'classification', 'condition', 'method')]
        inspection = 'Official23-pagePDF selectedpages1,6–8,16–18,22–23 visually checked; retainedJATS corroborated. Selected4 thermal-conductivity cells, preparation, plate geometry/temperatures, method, bibliography and author license. No raw data, plot digitization, fullstandard or latest-notice review.'
        prop['source_document'] = {'url': pdf, 'revision': 'Official article-deploy PDF retrieved2026-11-04; latest revision/correction/retraction unknown', 'inspected_on': '2026-11-04', 'sha256': facts['PDF_sha256'], 'hash_status': 'recorded', 'hash_note': None, 'inspection_scope': inspection, 'inspection_status': 'selected_content_inspected'}
        prop['scope_note'] = 'Selected study-specific optimized-foam plate reference only. Original mW/(m·K), precision, unknown summary/n and null numerical uncertainty retained. Apparatus average temperature does not identify an estimator. RH/equilibration, gas ageing, heat-flow/foam-rise direction, skin/location/contact and calibration unknown. No cup/compression/TGA n, neighbouring plus-minus value, four-day immersion or density normalization transferred; no engineering allowable, isotropy certification or engine input.'
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
    assert data['materials']['records'][:-4] == before.data['materials']['records']
    assert data['reference_properties']['records'][:-4] == before.data['reference_properties']['records']
    assert after.identities == before.identities and after.grades == before.grades
    write('NEW_STATES_R1.json', states)
    write('NEW_PROPERTIES_R1.json', properties)
    write('SOURCE_UPDATE_PROPOSAL_R1.json', proposal)
    write('VALIDATION_R1.json', {'scope': 'Unapplied4PURplate mapping with isolated candidate thermal contract', 'baseline_snapshot': before.snapshot, 'preview_snapshot': after.snapshot, 'candidate_properties': len(after.properties), 'candidate_states': len(after.states), 'new_properties': 4, 'new_states': 4, 'new_identities_grades_sources': 0, 'all_old5376properties5250states_preserved': True, 'current_graph': 'passed', 'summary_n_dispersion': 'not_stated/unknown/null for all4', 'native_applied': False, 'installation': 'not_run', 'full_history': 'not_run', 'pushed': False})
    print(json.dumps({'properties': len(after.properties), 'states': len(after.states), 'new_properties_states': [4, 4], 'snapshot': after.snapshot, 'native_changed': False}))


if __name__ == '__main__':
    main()
