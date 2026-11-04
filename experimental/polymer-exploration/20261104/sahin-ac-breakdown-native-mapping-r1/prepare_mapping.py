"""Prepare five reviewed source facts as an unapplied native mapping draft."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
DEST = Path(__file__).resolve().parent
SOURCE = DEST.parent / 'sahin-ac-breakdown-source-contract-r1'
PROTOTYPE = ROOT.parent / 'open-database-evidence/polymer-ac-breakdown-contract-prototype-20261104-r1'
sys.path.insert(0, str(PROTOTYPE))
from materials_boundaries.material_references import validate_material_catalog
from materials_boundaries.database import canonical


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(name, value):
    (DEST / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')


facts = load(SOURCE / 'SOURCE_FACTS_R1.json')
sid = facts['source_id']
pdf = 'https://mdpi-res.com/d_attachment/polymers/polymers-18-01345/article_deploy/polymers-18-01345.pdf'


def evidence(locator, *supports):
    return {'source_id': sid, 'url': pdf, 'locator': locator, 'supports': list(supports)}


def fact(text=None, locator=None, notes=None):
    return {'status': 'reported' if text is not None else 'not_reported_in_inspected_source',
            'text': text, 'evidence': [evidence(locator, 'condition')] if locator else [], 'notes': notes}


def state_fact(text=None, locator=None, notes=None):
    result = fact(text, None, notes)
    result['evidence'] = [evidence(locator, 'state')] if locator else []
    return result


materials, properties, sources = [load(ROOT / f'materials_boundaries/data/{n}.json') for n in ('materials', 'reference_properties', 'sources')]
baseline = deepcopy((materials, properties, sources))
state_index = {s['id']: s for s in materials['records']}
property_index = {p['id']: p for p in properties['records']}
states, new_properties = [], []
for candidate in facts['candidates']:
    label = candidate['material_label']
    old_state = state_index[candidate['existing_mechanical_state_id']]
    assert old_state['identity_id'] == candidate['existing_identity_id']
    state = deepcopy(old_state)
    state.update(id=candidate['proposed_disc_state_id'], version='1.0.0', property_ids=[candidate['proposed_property_id']])
    state['name'] = f'Porima {label}, Şahin 2026 FDM AC breakdown discs'
    state['names'] = {
        'en': state['name'], 'zh': f'Porima {label}，Şahin 2026 FDM 交流击穿圆片',
        'ja': f'Porima {label}、Şahin 2026 FDM 交流絶縁破壊円板',
        'de': f'Porima {label}, Şahin 2026 FDM-Scheiben für Wechselspannungsdurchschlag'}
    state['state']['product_form'] = state_fact('FDM-printed electrical-test disc, nominal diameter 50 mm and nominal thickness 1.2 mm; from 1.75 mm Porima filament', 'PDF pp5,7, §2.2 and Figure5', 'Nominal geometry, not individually measured specimen thicknesses; separate from Type I tensile specimens.')
    processing = candidate['processing']
    chamber = processing['chamber_C_or_unreported']
    state['state']['processing'] = state_fact(
        f"Qidi Q1 Pro FDM; 0.4 mm nozzle; 0.2 mm layer height; nominal 100% rectilinear infill; nozzle {processing['nozzle_C']} °C; bed {processing['bed_C']} °C; chamber " + (f'{chamber} °C' if chamber else 'not reported') + f"; printing ambient 23 °C; filament pre-dried {processing['filament_drying_C']} °C for {processing['filament_drying_h']} h",
        f'PDF pp5–6, §2.2 and Tables2–3, {label} column',
        'Filament drying is a processing step, not post-print specimen conditioning; printing ambient is not electrical-test temperature. Nominal infill is not measured zero porosity.')
    state['state']['conditioning'] = state_fact(notes='Post-print humidity, conditioning interval and pre-test equilibration unknown; pre-print filament drying recorded under processing.')
    state['state']['orientation'] = state_fact(notes='Raster/build orientation and its relation to the electrical field unknown; rectilinear infill does not establish them.')
    # Composition family is unchanged; evidence supports that family, not a formulation.
    state['state']['composition_or_purity']['evidence'] = [evidence('PDF pp4–5, §2.1, material labels', 'state')]
    state['source_scope'] = 'Single-study electrical-disc group under the existing polymer identity. No new grade, identity or independent physical-coverage claim. Nominal infill does not establish full density; actual individual thickness, batch count, composition, additives, conditioning and field/build relation unknown. Not a tensile-specimen state or universal polymer property.'
    state['evidence'] = [evidence('PDF pp4–8, §§2.1–2.4 and Tables2–3', 'material_identity', 'state')]
    # Start from a complete current contract envelope and replace all property-specific fields.
    old_id = candidate['proposed_property_id'].replace('_ac_dielectric_breakdown_strength', '_fdm_tensile_modulus')
    prop = deepcopy(property_index[old_id])
    prop.update(id=candidate['proposed_property_id'], version='1.0.0', material_state_id=state['id'],
                quantity='dielectric_breakdown_strength', quantity_dimension='electric_field',
                source_property_label=candidate['source_property_label'],
                reported_value={'kind': 'scalar', 'value_text': candidate['value_text'], 'number': candidate['number'], 'unit_code': 'kV/mm', 'unit_text': 'kV/mm'},
                summary_statistic=candidate['producer_summary_proposal'],
                reporting_basis='reported_summary' if label == 'ASA' else 'not_stated',
                basis_note='Selected §3.2 prose centre; ASA explicitly described as average. The other four individual centres have no unambiguous estimator identification; generic later average-values wording is insufficient. No figure digitization or Weibull substitution.',
                uncertainty=None, uncertainty_status='not_reported_in_inspected_source',
                uncertainty_note='Qualitative low standard deviations and boxplots supply no numerical SD, SE or CI. No borrowing of tensile SD/n or interpretation of Weibull 95% probability as a confidence level.')
    prop['sample_count'] = {'value': 3, 'relation': 'exact', 'scope': f'Three destructive electrical measurements for the {label} material group; not independent printing batches or laboratories.',
                            'source_statement': 'Sections2.4 and3.2 report three electrical measurements per material.',
                            'evidence': [evidence('PDF pp8,11, §§2.4 and3.2', 'sample_count')]}
    prop['conditions'] = {
        'test_method': fact('AC short-duration rapid-rise electrical breakdown test in mineral oil with opposing cylindrical electrodes', 'PDF pp7–8, §2.4', 'Source-reported field definition; exact reduction algorithm, AC frequency and RMS/peak convention unknown.'),
        'direction': fact(notes='Electrical field direction relative to the printing/build layers unknown; opposing electrodes alone do not define that relation.'),
        'temperature': fact(notes='Electrical-test/oil temperature unknown. The 23 °C all-tests statement belongs to tensile §2.3; printing ambient is a separate processing fact.'),
        'test_standard': fact('Method refers to IEC60243-1 §10 short-duration rapid-rise and IEC60243/IEC60060 series; applied edition and verified compliance unknown.', 'PDF pp7–8, §2.4; pp18–20, references27–29,33–34', 'References33–34 identify IEC60060, while references27–29 identify BS EN60243 editions. Bibliography does not establish the applied edition, frequency or RMS/peak convention.'),
        'conditioning': fact(notes='Post-print RH, duration, equilibration and oil immersion time unknown; pre-print filament drying is processing only.'),
        'loading_rate': fact('Applied AC voltage rise rate 500 V/s', 'PDF p8, §2.4', 'Voltage ramp, not a derived field ramp; no division by nominal thickness.'),
        'additional_conditions': [
            {'name': 'medium_and_container', 'fact': fact('Nytro Lyra X mineral oil; 200 × 200 × 200 mm container', 'PDF pp7–8, §2.4', 'Oil temperature, water content, degassing and immersion duration unknown.')},
            {'name': 'electrodes', 'fact': fact('Two identical cylindrical electrodes, diameter 25 mm, height 25 mm, corner radius 3 mm, with disc between them', 'PDF pp7–8, §2.4 and Figures5–6', 'Contact load and individual failure classification unknown.')},
            {'name': 'AC_frequency_and_convention', 'fact': fact(notes='AC frequency and RMS versus peak convention unknown; no standard-default inference.')},
            {'name': 'geometry_and_field_reduction', 'fact': fact(notes='State gives nominal 50 mm diameter and 1.2 mm thickness; individual actual thicknesses and field reduction algorithm unknown.')},
            {'name': 'source_capacity', 'fact': fact('AC source capacity 90 kV', 'PDF p8, §2.4', 'Equipment capacity, not observed breakdown voltage or engineering allowable.')}
        ]}
    prop['method_definition'] = {'type': 'source_reported_conventional', 'definition': 'Source-reported AC short-duration rapid-rise electrical breakdown field in mineral oil using opposing cylindrical electrodes; field values transcribed literally from §3.2. Frequency, RMS/peak convention, actual individual thickness reduction and numerical failure-selection algorithm unknown.', 'extraction_window': None, 'evidence': [evidence('PDF pp7–8,10–11, §§2.4 and3.2', 'method', 'classification')]}
    prop['source_discrepancies'] = [{'description': 'Method series citation points to references33–34 (IEC60060), while references27–29 contain BS EN60243 editions.', 'disposition': 'Retain the method wording and bibliography context without selecting an applied edition or importing default test conditions.', 'evidence': [evidence('PDF pp7–8,18–20, §2.4 and references27–29,33–34', 'source_discrepancy')]}]
    prop['evidence'] = [evidence('PDF pp10–11, §3.2 prose', 'reported_value', 'classification', 'summary_statistic'), evidence('PDF pp7–8,11, §§2.4 and3.2', 'method', 'sample_count')]
    inspection = 'Official 20-page PDF selected pages1,4–8,10–11,18–20 visually checked; retained JATS corroborated. Selected electrical prose values, method, nominal geometry, statistics and permissions; no plot digitization, raw-data reanalysis or latest-revision verification.'
    prop['source_document'] = {'url': pdf, 'revision': 'Official article-deploy PDF, 20 pages, retrieved 2026-11-04; latest revision/correction/retraction unknown', 'inspected_on': '2026-11-04', 'sha256': facts['PDF_sha256'], 'hash_status': 'recorded', 'hash_note': None, 'inspection_scope': inspection, 'inspection_status': 'selected_content_inspected'}
    prop['scope_note'] = 'Selected study-specific electrical-disc result only. ASA explicitly mean; other four central estimator identities unknown; n=3 electrical measurements per group, not n=5 tensile specimens or three independent batches. No numerical dispersion supplied. Test/oil temperature, frequency, RMS/peak, humidity, conditioning, immersion time, actual thickness, field/build relation and applied standard edition unknown. No supplier Table1, figure digitization, Weibull quantiles, engineering allowables or engine input.'
    prop['verification'] = {'source_inspection_scope': inspection, 'transcription_cross_check': 'completed', 'independent_scientific_review': False, 'raw_data_reanalysis': False}
    assert prop['evaluation_support'] == 'catalog_only' and prop['engineering_allowable'] is False
    states.append(state); new_properties.append(prop)

materials['records'].extend(states); properties['records'].extend(new_properties)
proposal = load(SOURCE / 'SOURCE_UPDATE_PROPOSAL_R1.json')
original_source = next(s for s in sources['records'] if s['id'] == sid)
assert original_source == proposal['baseline_source']
sources['records'][sources['records'].index(original_source)] = proposal['proposed_source']
write('NEW_STATES_R1.json', states)
write('NEW_PROPERTIES_R1.json', new_properties)
validate_material_catalog(materials, properties, sources)
assert materials['identities'] == baseline[0]['identities'] and materials['grades'] == baseline[0]['grades']
assert materials['records'][:-5] == baseline[0]['records'] and properties['records'][:-5] == baseline[1]['records']
write('NEW_STATES_R1.json', states)
write('NEW_PROPERTIES_R1.json', new_properties)
write('SOURCE_UPDATE_PROPOSAL_R1.json', proposal)
write('VALIDATION_R1.json', {'scope': 'Unapplied in-memory mapping against isolated candidate electric-field contract', 'native_applied': False, 'native_properties': len(baseline[1]['records']), 'proposed_properties': len(properties['records']), 'proposed_states': len(materials['records']), 'new_properties': 5, 'new_states': 5, 'new_identities_grades_sources': 0, 'all_existing_properties_states_preserved': True, 'graph_validation': 'passed', 'uncertainty': 'null for all5', 'sample_count': 'exact3 electrical measurements per group', 'summary': 'ASA reported_mean;other4 not_stated', 'source_entry_sha256': sha(SOURCE / 'REVIEW_INPUTS_R1.json'), 'contract_entry_sha256': sha(DEST.parent / 'ac-breakdown-contract-implementation-r1/REVIEW_INPUTS_R1.json'), 'candidate_tables_canonical_sha256': hashlib.sha256(canonical(dict(zip(('materials','reference_properties','sources'), (materials, properties, sources))))).hexdigest(), 'not_run': ['native_apply', 'wheel_install', 'HTTP', 'full_history'], 'pushed': False})
print('Five states / five properties mapped; proposed graph validation passed; native unchanged.')
