"""Map six source-labelled flexural strengths on existing bending states."""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from materials_boundaries.database import Database
AREA = ROOT / 'experimental/polymer-exploration/20261103'
BASE = '59eb6d9e5ae56afbafd9a3413c456f8d060263d280f2664df00b551c0da69650'


def read(path):
    return json.loads(path.read_bytes())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    out = args.output_dir.resolve()
    assert not out.exists() and not out.is_relative_to(ROOT / 'materials_boundaries')
    proposal = AREA / 'flexural-strength-proposal-r1'
    facts = read(proposal / 'SOURCE_FACTS_R1.json')
    review = read(proposal / 'INDEPENDENT_SOURCE_CONCEPT_REVIEW_R1.json')
    assert review['decision'] == 'approved'
    assert review['review_inputs_sha256'] == sha(proposal / 'REVIEW_INPUTS_R1.json')
    for source, path_key, hash_key in [('epoxy_source', 'PDF_path_hint', 'PDF_sha256'), ('phbv_source', 'XML_path_hint', 'XML_sha256')]:
        assert sha(Path(facts[source][path_key])) == facts[source][hash_key]
    before = Database()
    assert before.snapshot == BASE
    properties, states, sources = [], {}, {}
    for fact in facts['rows']:
        old = before.properties[fact['existing_modulus_id']]
        assert old['quantity'] == 'flexural_modulus' and old['source_id'] == fact['source_id']
        prop = deepcopy(old)
        pid = old['id'].replace('flexural_modulus', 'flexural_strength')
        assert pid not in before.properties
        phbv = fact['source_id'] == 'abbasi_2022_manure_phbv'
        prop.update(id=pid, version='1.0.0', quantity='flexural_strength', source_property_label='Flexural Strength (MPa)')
        prop['reported_value'].update(value_text=fact['strength_MPa'], number=fact['strength_MPa'], unit_text='MPa', unit_code='MPa')
        if phbv:
            prop['uncertainty'].update(value_text=fact['SD_MPa'], number=fact['SD_MPa'], unit_text='MPa', unit_code='MPa')
            prop['uncertainty_note'] = '20.8 ± 1.4 MPa: source mean ± SD, including its SD-rounding qualification. No SD-to-SE/CI conversion.'
            prop['basis_note'] = 'Table9 PHBV-39 flexural strength, mean ± SD; at least5 mechanical-test replicates. Exact strength extraction criterion remains unspecified; no maximum, yield, rupture or deflection-limit interpretation inferred.'
            definition = 'Three-point bending on DMA Q800 at source room temperature,10mm span, source constant strain of1% until yield, Universal Analysis v4.5A. Source-labelled flexural strength; exact strength extraction criterion, stress convention and per-time bending rate unknown.1% is not a verified rate, modulus fit window or strength extraction point.'
            scope = 'Retained primary XML Table9 PHBV-39 Flexural Strength (MPa)/mean-SD footnotes, section2.2.8 common preparation and bending method, article permissions. No fresh PDF visual inspection or raw-data reanalysis.'
        else:
            assert prop['summary_statistic'] == 'not_stated' and prop['uncertainty'] is None and prop['sample_count']['value'] is None
            prop['basis_note'] = 'Table8 source flexural-strength scalar. Central estimator, n/batches and dispersion not reported; no mean, SD, SE or CI inferred. Source table precision retained.'
            definition = 'Source flexural strength,50ST/Tinius Olsen, GOST R56810-2015(ASTM D790-10),0.85mm/min;80x9.8x3.6mm bars milled from3.6mm plate; literal span-to-depth statement64:3.6mm. Support-point count, stress formula, exact failure/deflection/strength extraction criterion and standards compliance not independently established.'
            scope = 'Retained exact publisher PDF visually inspected pp1,5,6,16: license, common DDS cure, section2.5.2 bending method, Table8 selected Flexural Strength(MPa) cell. No fresh PDF acquisition or raw-data reanalysis.'
        prop['method_definition'].update(definition=definition, extraction_window=None)
        prop['conditions']['test_method'].update(text=definition, notes='Source-labelled bending strength only; exact extraction criterion unknown. Source standard citation is not independent compliance verification.')
        def bind(node):
            if isinstance(node, dict):
                if node.get('source_id') == fact['source_id'] and 'locator' in node:
                    loc = node['locator']
                    if ('Table' in loc or 'table' in loc) and ('Modulus' in loc or 'modulus' in loc):
                        node['locator'] = fact['locator'] + ('; mean/SD footnote' if phbv else '')
                for value in node.values():
                    bind(value)
            elif isinstance(node, list):
                for value in node:
                    bind(value)
        bind(prop)
        prop['source_document'].update(inspected_on='2026-11-03', inspection_scope=scope)
        prop['verification']['source_inspection_scope'] = scope
        prop['scope_note'] = 'Existing ' + fact['source_label'] + ' identity and its reviewed bending specimen state only. Source-labelled flexural strength, not tensile/yield/break strength or a modulus slope. Exact strength extraction criterion and stress convention remain unknown; no support geometry, missing statistics, environment or conditioning inferred from standards or neighboring tests. Existing composition/nominal-feed discrepancies retained. No automatic engine mapping, engineering allowable or universal bound.'
        state = deepcopy(before.states[prop['material_state_id']])
        assert state['id'] not in states
        a, b, c = state['version'].split('.')
        state['version'] = f'{a}.{b}.{int(c) + 1}'
        state['property_ids'].append(pid)
        state['source_scope'] += ' This supplement also records source-labelled flexural strength; property-specific method/statistics and unknown extraction criterion remain separate.'
        states[state['id']] = state
        source = sources.setdefault(prop['source_id'], deepcopy(before.sources[prop['source_id']]))
        properties.append(prop)
    for source in sources.values():
        source['claim_notes'].append('2026-11-03 flexural-strength supplement: selected existing bending states only, direct Table8 PNA-BPF-1 through-5 or Table9 PHBV-39 facts. Statistics remain source-specific; failure/yield/maximum/deflection criterion not inferred. Historical limited-selection notes describe earlier stages. No new identities, standards text, scientific certification or engine input.')
    data = deepcopy(before.data)
    data['reference_properties']['records'].extend(properties)
    data['materials']['records'] = [states.get(s['id'], s) for s in data['materials']['records']]
    data['sources']['records'] = [sources.get(s['id'], s) for s in data['sources']['records']]
    after = Database(data)
    contracts = after.validate_scientific_contracts()
    assert all(after.properties[k] == v for k, v in before.properties.items())
    assert after.identities == before.identities and after.grades == before.grades and set(after.states) == set(before.states)
    assert len(after.properties) == 5252
    out.mkdir(parents=True)
    tables = out / 'native-tables'
    tables.mkdir()
    for name, value in data.items():
        write(tables / (name + '.json'), value)
    write(out / 'native-candidate-r1.json', {'baseline_snapshot': BASE, 'stage': 'frozen_not_applied', 'materials': {'identities': [], 'grades': [], 'records': list(states.values())}, 'sources': {'records': list(sources.values())}, 'reference_properties': {'records': properties}})
    write(out / 'VALIDATION_R1.json', {'baseline_snapshot': BASE, 'preview_snapshot': after.snapshot, 'new_properties': 6, 'new_identities': 0, 'new_states': 0, 'modified_states': 6, 'modified_sources': 2, 'all_old_5246_properties_unchanged': True, 'contracts': contracts, 'native_applied': False, 'pushed': False, 'full_history_regression': 'not_run'})
    print(json.dumps({'snapshot': after.snapshot, 'properties': len(after.properties), 'contracts': contracts}))


if __name__ == '__main__':
    main()
