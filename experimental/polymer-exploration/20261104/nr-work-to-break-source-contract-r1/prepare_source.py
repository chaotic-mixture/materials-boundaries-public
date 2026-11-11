"""Freeze as-source NR work fact, unresolved elongation and thermal leads."""
from pathlib import Path
from copy import deepcopy
import hashlib
import json
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
EXT = ROOT.parent / 'open-database-evidence/polymer-nr-work-to-break-20261104-r1'
XML = ROOT.parent / 'open-database-evidence/polymer-nr-20261103/article-r2.xml'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def write(name, obj):
    with (HERE / name).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(obj, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def main():
    assert sha(XML) == '97eb8a1e73e57b6fc64fcf3b0be6603db3f8dcb5fa927570e91eb033f1018f69'
    assert sha(EXT / 'article-r1.pdf') == '2e729bb58b361568d27ab772ec1c031648cb6a858f58a6e4ece9ce45b74c3ea2'
    xml = ET.fromstring(XML.read_bytes())
    rows = {}
    for table in xml.iter('table-wrap'):
        label = ''.join(table.find('label').itertext()).strip()
        if label in ('Table 3', 'Table 3.', 'Table 4', 'Table 4.'):
            for row in table.iter('tr'):
                cells = [''.join(cell.itertext()).strip() for cell in list(row)]
                if cells and cells[0] == 'NR':
                    rows[label.rstrip('.')] = cells
    assert len(rows) == 2
    assert '32.2' in rows['Table 4'][6] and '6.4' in rows['Table 4'][6]
    assert '730' in rows['Table 4'][5] and '14' in rows['Table 4'][5]
    for cell, centre, amplitude in zip(rows['Table 3'][1:], ['1.70', '0.081', '0.132'], ['0.05', '0.001', '0.003']):
        assert centre in cell and amplitude in cell
    materials = read(ROOT / 'materials_boundaries/data/materials.json')
    properties = read(ROOT / 'materials_boundaries/data/reference_properties.json')
    sources = read(ROOT / 'materials_boundaries/data/sources.json')
    sid = 'bianchi_2025_nr_nanoclay'
    states_by_id = {item['id']: item for item in materials['records']}
    selected = [prop for prop in properties['records'] if prop['source_id'] == sid
                and states_by_id[prop['material_state_id']]['identity_id'] == 'mat_smr10_bianchi2025_nr']
    assert len(selected) == 6
    state = next(state for state in materials['records'] if state['id'] == 'state_smr10_bianchi2025_nr')
    source = next(source for source in sources['records'] if source['id'] == sid)
    before = {f'materials_boundaries/data/{name}.json': sha(ROOT / f'materials_boundaries/data/{name}.json') for name in ('materials', 'reference_properties', 'sources')}
    write('WORK_SOURCE_CANDIDATE_R1.json', {
        'schema': 'existing-NR-volumetric-tensile-work-source-fact/1', 'source_id': sid,
        'existing_identity_id': state['identity_id'], 'existing_grade_id': state['grade_id'], 'existing_state_id': state['id'],
        'source_label': 'NR', 'source_quantity_label': 'Specific tensile energy to break, Eb',
        'source_expression': '32.2 ± 6.4', 'mean': '32.2', 'SD': '6.4', 'source_unit_text': 'J/cm³',
        'locator': 'PDF p7 Table4 NR/Eb column;XML Table4 NR row',
        'method': 'PDF p18 §3.3.4:source integrates stress-strain curve to break;this software does not integrate,digitize or recalculate',
        'summary': 'reported_mean', 'uncertainty': 'reported_standard_deviation',
        'statistics_evidence': 'PDF p19 §3.3.4 final sentence applies mean/SD to mechanical properties',
        'sample_count': {'value': 5, 'relation': 'exact', 'scope': 'Reported quasi-static tensile specimens per composition,not verified independent production batches', 'locator': 'PDF p18 §3.3.4 quasi-static paragraph'},
        'method_conditions': {'machine': 'Instron5969', 'load_cell_capacity': '1kN', 'crosshead_speed': '500mm/min',
            'strain_measurement': 'Resistance extensometer Instron2603,gauge length25mm', 'standard_as_cited': 'ASTMD412,edition/compliance unverified'},
        'unknowns': ['Quasi-static temperature/RH/post-cureconditioning/storage', 'Stress and strain conventions', 'Initial/current/other reference volume and cross-section',
            'Integration start,offset/algorithm/sampling/smoothing', 'Mean-of-individual-integrals versus integral-of-mean-curve', 'Independent production batches/cross-paper independence'],
        'boundaries': ['Not recoverable elastic strain energy,calorimetric heat Qab,cyclic hysteresis loss or fracture energy per area',
            'J/cm³ identifies volumetric reporting,not a measured/certified volume basis or J/g mass-specific quantity',
            'No hardness25C,relaxation25C,thermal20C,elastocaloric22C or cyclic125mm/min/n1/10cycles/prestretches transferred',
            'Selected table work value/unit independent source transcription;unresolved epsilon header not silently corrected or used to reconstruct integral'],
        'native_applied': False, 'implementation': 'not_started'})
    write('ELONGATION_UNIT_HOLD_R1.json', {'source_id': sid, 'source_label': 'NR', 'source_expression': '730 ± 14',
        'PDF_p7_Table4_header': 'epsilon_b (mm/mm)', 'XML_header': 'epsilon_b (mm/mm)',
        'PDF_p7_Figure3_axis': 'Strain (%)', 'decision': 'hold_not_native',
        'reason': 'Same-source table unit and representative-curve axis conflict;no erratum/explicit source correction verified',
        'forbidden_repairs': ['Relabel730aspercent', 'Divide by100 to7.30', 'Use curve endpoint or another paper as correction authority', 'Infer independent replication from matching numbers']})
    write('THERMAL_RESEARCH_LEADS_R1.json', {'source_id': sid, 'source_label': 'NR', 'locator': 'PDF p6 Table3;PDF p18 §3.3.3;XML Table3',
        'facts': [
            {'quantity_concept_only': 'specific_heat_capacity', 'centre': '1.70', 'amplitude': '0.05', 'source_unit_text': 'J/g·K', 'method_role': 'Source LFA reference comparison;Pyroceram9606', 'native_status': 'unsupported_quantity_research_lead'},
            {'quantity_concept_only': 'thermal_diffusivity', 'centre': '0.081', 'amplitude': '0.001', 'source_unit_text': 'mm²/s', 'method_role': 'Source LFA Cowan model with numerical pulse correction', 'native_status': 'unsupported_quantity_research_lead'},
            {'quantity_concept_only': 'thermal_conductivity', 'centre': '0.132', 'amplitude': '0.003', 'source_unit_text': 'W/m·K', 'method_role': 'Source calculated lambda=alpha*cp*rho,not directly measured heat-flow plate result', 'native_status': 'supported_quantity_but_separate_derivation_classification_review_required'}],
        'method_conditions': {'temperature': '20°C', 'apparatus': 'NetzschLFA447', 'specimen': 'Cylinder12.7mm diameter/1mm thickness', 'standard_as_cited': 'ASTM-E1461,edition/compliance unverified',
            'method_tested_specimens_per_formulation': 3, 'pulses_per_specimen': 5},
        'statistics': 'Table ± semantics/centre estimator/per-cell contributing n unconfirmed;mechanical meanSD statement not transferred;method3specimens separate,not n15',
        'unknowns': ['Thermal sample conditioning/RH/drying', 'Gas/flow', 'Direction/anisotropy', 'Temperature-specific density equivalence', 'Mean/product order and covariance', 'Cross-paper independence'],
        'native_applied': False, 'new_quantities_or_derivation_profile_implemented': False})
    write('CONTRACT_PROPOSAL_R1.json', {'schema': 'unimplemented-volumetric-tensile-work-concept/1',
        'quantity': 'volumetric_tensile_work_to_break', 'quantity_dimension': 'energy_per_volume',
        'dimension_note': 'Semantic energy-density role;SIbase dimensions coincide with pressure,not a new independent SI dimension or automatic permission to use stress units',
        'central_units': ['J/cm^3', 'MJ/m^3', 'J/m^3'], 'domain': 'Nonnegative source scalar/interval/comparison;preserve zero as reported precision,not certified zero work',
        'required_qualifier': 'work_reference_basis', 'qualifier_shape': 'Existing fact envelope reported/not_reported/not_verified;nevernot_applicable. Reported basis needs primary inspected-document condition evidence;unknown basis explicit explanatory note',
        'source_work_reference_basis': 'Unknown reference volume and stress/strain conventions;source unit retained,not inferred initial volume',
        'schema_strategy': 'Append one complete disjoint branch after current11;all current11 branchobjects/legacy central units unchanged;newfield forbidden in oldbranches',
        'unit_strategy': 'New energy-volume unit roles stay out of old central branches;absolute uncertainty may use same role only;no automatic scale or pressure conversion',
        'statistics': 'Reuse reported_mean/SD with exact5specimen evidence for selected source;no claim of mean/integration order or batch independence',
        'uniqueness': 'Keep source-cell/core-fact semantics;basis reported coordinates matter,unknown status/note wording/evidence formatting cannot inflate properties',
        'presentation': 'Four-language quantity/basis labels and complete query/export evidence/unknowns;no mechanics engine,fracture-area metrics or caloric allowables',
        'meaningful_checks_required': ['Old11branches/legacy equality', 'Source-unit precision/scale and no pressure or mass-specific leakage', 'Nonnegative work and uncertainty domains', 'Required basis/evidence/wrong-branch rejection', 'Basis-aware duplicate semantics', 'Four-language rendering/query/export/copy isolation', 'Separate exact implementation/mapping/install/native integration review'],
        'unit_reference': {'url': 'https://www.nist.gov/pml/special-publication-811/nist-guide-si-chapter-4-two-classes-si-units-and-si-prefixes', 'locator': 'Tables3and4', 'scope': 'Energy density J/m³ and pressure same base dimensions;doesnot certify source volume basis or normalize source values'},
        'implementation': 'not_started', 'native_applied': False})
    proposed = deepcopy(source)
    url = read(EXT / 'ACQUISITION_R1.json')['requested_url']
    if url not in proposed['urls']:
        proposed['urls'].append(url)
    proposed['claim_notes'].append('Fresh official23pagePDF inspected2026-11-04(selected1,6,7,18,19):NR Table4 Eb32.2±6.4J/cm³ is source-integrated tensile work,mechanicalmeanSD/5specimens;no integral reconstruction. Epsilon_b730±14 retains mm/mm table versus percent curve-axis conflict,held. Table3 thermal3facts remain separate researchleads;lambda source-calculated viaalpha*cp*rho,mechanicalSD/n not transferred. Unknown volume/stress-strain conventions,conditioning,per-cell thermalstatistics and cross-paper independence retained;rawassets external. Source/proposal only,not native admission.')
    write('SOURCE_UPDATE_PROPOSAL_R1.json', {'source_id': sid, 'baseline_source': source, 'proposed_source': proposed,
        'changed_fields': [field for field in source if source[field] != proposed[field]], 'native_applied': False})
    write('VALIDATION_R1.json', {'scope': 'Direct XML cell/asset fingerprint/6existingNRrecord and proposal checks;not implementation tests',
        'native_before_sha256': before, 'all_native_bytes_unchanged': all(sha(ROOT / name) == digest for name, digest in before.items()),
        'selected_work_source_facts': 1, 'thermal_research_leads': 3, 'elongation_held': 1,
        'new_native_records': 0, 'implementation_tests_installation_history': 'not_run', 'pushed': False})
    print(json.dumps({'work_fact': 1, 'thermal_leads': 3, 'elongation_held': 1, 'native_changed': False}), flush=True)


if __name__ == '__main__':
    main()
