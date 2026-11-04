"""Freeze four existing-PUR source facts and a closed quantity concept only."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
EVIDENCE = ROOT.parent / 'open-database-evidence/polymer-pur-thermal-source-20261104-r1'
XML = ROOT.parent / 'open-database-evidence/polymer-pur-20261103/article-r1.xml'
sys.path.insert(0, str(ROOT))
from materials_boundaries.database import Database, canonical


def read(path):
    return json.loads(path.read_bytes())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(name, value):
    with (OUT / name).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def text(node):
    return ' '.join(''.join(node.itertext()).split())


def main():
    db = Database()
    sid = 'ivdre_2024_lpo_rigid_pur'
    source = db.sources[sid]
    assert source['doi'] == '10.3390/polym16070942'
    assert sha(XML) == '4e0c1a91a9ae26d814576961a3805f9371b46498d4861fb578e7a413bb4c726d'
    acquisition = read(EVIDENCE / 'COMPLETE_ACQUISITION_R3.json')
    assert sha(EVIDENCE / 'article-r2.pdf') == acquisition['sha256']
    assert acquisition['bytes'] == 13850045 and acquisition['pages'] == 23
    root = ET.fromstring(XML.read_bytes())
    table = next(n for n in root.findall('.//table-wrap') if n.find('label') is not None and text(n.find('label')) == 'Table 10')
    row = next(n for n in table.findall('.//tr') if 'Thermal conductivity' in text(n))
    cells = [text(n) for n in list(row) if n.tag in ('th', 'td')]
    expected = ['19.84', '20.26', '20.26', '19.97', '19.07', '19.34']
    assert cells[1:] == expected, cells
    labels = ['LPO-1', 'LPO-2', 'LPO-3', 'SPO-1', 'SPO-2', 'SPO-3']
    selected = ['LPO-1', 'LPO-2', 'SPO-2', 'SPO-3']
    candidates = []
    original = {}
    for label in selected:
        code = label.lower().replace('-', '')
        prop = db.properties[f'refprop_ivdre2024_{code}_rigid_pur_mass_density']
        state = db.states[prop['material_state_id']]
        assert db.identities[state['identity_id']]['category'] == 'polymer'
        original[prop['id']] = hashlib.sha256(canonical(prop)).hexdigest()
        candidates.append({'source_label': label, 'existing_identity_id': state['identity_id'], 'existing_grade_id': state['grade_id'],
                           'existing_density_state_id': state['id'], 'proposed_plate_state_id': state['id'] + '_heat_flow_plate',
                           'proposed_property_id': f'refprop_ivdre2024_{code}_rigid_pur_thermal_conductivity',
                           'source_property_label': 'Thermal conductivity, mW/(m·K) (0…20 °C)',
                           'quantity_proposal': 'thermal_conductivity', 'quantity_dimension_proposal': 'power_per_length_temperature',
                           'value_text': expected[labels.index(label)], 'number': expected[labels.index(label)],
                           'unit_text': 'mW/(m·K)', 'unit_code_proposal': 'mW/(m*K)',
                           'value_locator': f'PDF page17 Table10, thermal-conductivity row, {label} column; XML Table10',
                           'summary_statistic_proposal': 'not_stated', 'numeric_uncertainty': None, 'sample_count': None,
                           'summary_scope': 'Average temperature10°C is an apparatus temperature,not evidence that the cell is a group mean.',
                           'candidate_status': 'source_and_contract_concept_only_not_native_or_engine'})
    conditions = {
        'locator': 'PDF page7 §§2.7–2.8;page17 Table10;page23 reference36',
        'apparatus': 'FOX 200,TA instruments-Water LLC,source spelling',
        'test_mean_temperature_C': '10', 'cold_plate_C': '0', 'hot_plate_C': '20',
        'temperature_scope': 'Source explicitly reported average test temperature and plate temperatures,not room ambient or statistical aggregation',
        'specimen_dimensions_mm': ['200', '200', '30'], 'geometry_scope': 'Heat-flow test plates,not compression cylinders,water-absorption cubes or original density specimen geometry',
        'reported_standard': 'ISO 8301:1991;method and reference36 agree;full standard/compliance not verified',
        'preparation': 'Optimized formulations follow cup-test mixing method,cast in30×30×10cm larger mold;all foams cure24h at room temperature before further testing',
        'conditioning_scope': '24h room-temperature curing is processing,not a complete post-cure humidity/equilibration procedure;numeric cure temperature unknown',
        'unconfirmed': ['thermal-conductivity measurement n and independent batches', 'cell mean/median/single-result estimator', 'numeric SD/SE/CI/expanded uncertainty', 'RH/moisture and conditioning duration/equilibration', 'heat-flow direction relative to foam rise', 'plate contact force,skin removal/location and contact treatment', 'ambient pressure/atmosphere', 'time since foaming or gas ageing', 'apparatus calibration and actual standard compliance', 'raw measurements and uncertainty budget'],
        'non_transfers': ['Cup screening3samples not thermal-conductivity n', 'Compression6cylinders and density-normalization40kg/m3 not thermal-conductivity n/normalization', 'TGA3ormore parallel samples not thermal-conductivity n', 'Water absorption4day immersion not prior thermal-test conditioning', 'Foam geometric anisotropy not isotropic thermal-conductivity proof']}
    write('SOURCE_FACTS_R1.json', {'schema': 'existing-PUR-thermal-conductivity-source/1', 'source_id': sid, 'native_snapshot': db.snapshot,
          'PDF_sha256': acquisition['sha256'], 'PDF_bytes': acquisition['bytes'], 'PDF_pages': 23, 'XML_sha256': sha(XML),
          'visually_inspected_pages': [1, 6, 7, 8, 16, 17, 18, 22, 23], 'candidates': candidates, 'common_conditions': conditions,
          'existing_density_properties_canonical_sha256': original,
          'exclusions': {'LPO3_SPO1': 'Not existing selected identities;no newidentities in this candidate', 'compression': 'Source density-normalized40kg/m3 quantities,not directly admitted as raw compressive values or digitized', 'other_thermal': 'No newTGA/DSC/DMA numbers orplotdigitization', 'density_discrepancy': 'Table10 SPO1density43.9 versussection3.4range40.7–43.5 remains;notrepair orcross-property validation'},
          'rights': 'AuthorCCBY4.0 explicitPDFpage1;onlyselectedfacts/attribution/curation,notrawPDF/XML/figures/standardassets orblanketthirdpartyrights',
          'latest_revision_correction_retraction': 'unknown', 'native_applied': False, 'new_native_properties_states': 0, 'implementation': 'not_started', 'tests_installation': 'not_run_sourceproposalonly', 'pushed': False})
    nist = 'https://www.nist.gov/pml/special-publication-811/nist-guide-si-chapter-4-two-classes-si-units-and-si-prefixes'
    write('UNIT_REFERENCE_R1.json', {'url': nist, 'read_on': '2026-11-04', 'locator': 'NISTSP811chapter4 Table4thermalconductivity;Table5milli', 'facts': ['Thermalconductivity SIunit W/(m·K)', 'Baseunitexpression m·kg·s^-3·K^-1', 'milli is10^-3'], 'inference': '1mW/(m·K)=10^-3W/(m·K),dimensional relation only;not automatic conversion permission', 'not_assessed': ['fullSI conformity', 'ISO8301text/compliance', 'specimenheatflow model']})
    write('CONTRACT_PROPOSAL_R1.json', {'status': 'unimplemented_closed_contract_concept', 'quantity': 'thermal_conductivity', 'quantity_dimension': 'power_per_length_temperature', 'unit_codes': ['W/(m*K)', 'mW/(m*K)'], 'source_typographic_spellings': {'W/(m*K)': ['W/(m·K)', 'W/(m*K)'], 'mW/(m*K)': ['mW/(m·K)', 'mW/(m*K)']},
          'central_domain': 'Strictly positive source scalar/interval/comparison;preserve precision and original units,not conversion', 'uncertainty': 'Reuse closed absolute/relative roles;nonnegative absolute amplitudes with exact same unitcode as centre;no automatic milli/base conversion',
          'schema_plan': 'Explicit7thcomplete mutuallyexclusive branch;keepold6branchobjects andlegacy centralunitdomain literallyunchanged;extendshared uncertainty vocab only through role checks',
          'forbidden': ['Temperatureunit as central conductivity', 'Watt alone,heattransfercoefficientW/(m^2*K),thermalresistance orconductance units', 'Negative/zero central values under thispositive-reference contract', 'density_basis exceptnull orspecified_elongation', 'inferredisotropy', 'engineeringallowable/universalbound/engineinput', 'automatic0.01984Wrewrite of19.84mW sourcecell'], 'source_default': 'catalog_only;summarynot_stated,nunknown,nulluncertainty', 'unit_reference': nist})
    proposal = deepcopy(source)
    if acquisition['url'] not in proposal['urls']:
        proposal['urls'].append(acquisition['url'])
    proposal['claim_notes'].append('2026-11-04 thermal-conductivity source proposal: official23pagePDF SHA256 ' + acquisition['sha256'] + ' selectedpages1,6–8,16–18,22–23 visuallychecked;four existingoptimizedPUR identities inTable10. SourceFOX200 plates200×200×30mm,average10°C,cold0/hot20°C,ISO8301:1991 claim;not statisticalmean,isotropy orverifiedcompliance. Thermal n,numericdispersion,humidity/equilibration,flow/risereorientation andgasageing unknown. Cup/compression/TGA counts andcompressiondensitynormalization nottransferred. Values remain sourceproposalonly untilnewclosedquantity,exactmapping andindependentreview;nodigitization/newidentities/engineinput.')
    changed = [n for n in source if source[n] != proposal[n]]
    test_sources = deepcopy(db.data['sources'])
    test_sources['records'][test_sources['records'].index(source)] = proposal
    Draft202012Validator(read(ROOT / 'schemas/sources.schema.json'), format_checker=FormatChecker()).validate(test_sources)
    write('SOURCE_UPDATE_PROPOSAL_R1.json', {'status': 'unapplied_source_proposal', 'source_id': sid, 'baseline_source': source, 'proposed_source': proposal, 'changed_fields': changed, 'native_applied': False})
    write('VALIDATION_R1.json', {'scope': 'Sourcefacts/identity/unitconcept only', 'selected_cells_match_XML': 4, 'PDF_selected_page_visual_check': True, 'existing_density_properties': 4, 'existing_identities_match': True, 'source_proposal_schema_format': 'passed', 'source_changed_fields': changed, 'native_snapshot': db.snapshot, 'native_code_data_changed': False, 'new_property_quantity_implementation': 'not_started', 'unit_suites_install_fullgraph_history': 'not_run', 'native_applied': False, 'pushed': False})
    print(json.dumps({'candidates': 4, 'source_schema': 'passed', 'native_changed': False, 'implementation': 'not_started'}))


if __name__ == '__main__':
    main()
