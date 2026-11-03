"""Freeze six break-stress facts on existing source-defined tensile states."""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from materials_boundaries.database import Database

BASE = '58defa23d7fa9a5e28f1f1a30d8ba9a47c311ac7a7293b82284d178385a99af8'
AREA = ROOT / 'experimental/polymer-exploration/20261103'


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
    out = parser.parse_args().output_dir.resolve()
    assert not out.exists() and not out.is_relative_to(ROOT / 'materials_boundaries')
    proposal = AREA / 'tensile-break-stress-proposal-r1'
    facts = read(proposal / 'SOURCE_FACTS_R1.json')
    review = read(proposal / 'INDEPENDENT_SOURCE_CONCEPT_REVIEW_R1.json')
    assert review['decision'] == 'approved'
    assert review['review_inputs_sha256'] == sha(proposal / 'REVIEW_INPUTS_R1.json')
    for asset in facts['source_assets'].values():
        path = Path(asset['path_hint'])
        assert sha(path) == asset['sha256'] and path.stat().st_size == asset['bytes']
    before = Database()
    assert before.snapshot == BASE == facts['baseline_snapshot']
    properties, states, sources = [], {}, {}
    for fact in facts['rows']:
        old = before.properties[fact['base_property_id']]
        assert old['source_id'] == fact['source_id']
        prop = deepcopy(old)
        nr = fact['source_label'] == 'NR'
        assert old['quantity'] == ('tensile_modulus' if nr else 'tensile_strength')
        pid = fact['new_property_id']
        assert pid not in before.properties
        prop.update(id=pid, version='1.0.0', quantity='tensile_stress_at_break', source_property_label=fact['source_property_label'])
        prop['reported_value'].update(value_text=fact['mean_MPa'], number=fact['mean_MPa'], unit_text='MPa', unit_code='MPa')
        prop['uncertainty'].update(value_text=fact['SD_MPa'], number=fact['SD_MPa'], unit_text='MPa', unit_code='MPa')
        assert prop['summary_statistic'] == 'reported_mean'
        assert prop['uncertainty']['type'] == 'reported_standard_deviation'
        assert prop['sample_count']['value'] == 5 and prop['sample_count']['relation'] == 'exact'
        prop['uncertainty_note'] = f"{fact['mean_MPa']} ± {fact['SD_MPa']} MPa: source mean ± reported SD for five tensile specimens in the selected composition/group. No SE, CI or independent batch count inferred."
        prop['basis_note'] = fact['locator'] + '; source-labelled tensile stress at break, mean ± SD, n=5 specimens. Not peak tensile strength, yield strength, modulus or toughness.'
        if nr:
            definition = 'Section3.3.4 quasi-static ASTM D412 (edition unknown), Instron5969/1kN,500mm/min crosshead, Instron2603/25mm extensometer. Table4 source sigma_b stress at break; not E100-200 interval slope or sigma200/400. Exact fracture detection, stress convention and reduction implementation unspecified.'
            boundary = 'Unfilled NR formulation includes curatives; not raw or pure NR. Temperature, humidity and post-cure conditioning remain unknown. Do not transfer density, hardness, cyclic or relaxation-test conditions. Table4 break-strain header/magnitude issue is outside this stress-only supplement; no strain or energy mapping/correction.'
        else:
            definition = 'Section2.3 ASTM D638-14, Zwick/RoellZ020/10kN,23C,5.0mm/min crosshead. Table4 s_B stress at break, distinct from s_M tensile strength, E_t and E_Sec. Exact fracture detection, stress convention, extensometry and reduction implementation unspecified.'
            boundary = 'Only the existing printed specimen group and recipe. Grade/SKU, lot, colour, additives, post-print conditioning, humidity and build/raster relation remain unknown. Pre-print drying is not post-print conditioning;100% slicer infill is not verified zero porosity. Mechanical n=5 is separate from dielectric n=3. Retain the source elongation table cross-reference issue without numeric correction.'
            for item in prop['source_discrepancies']:
                item['disposition'] = 'Use Table4 for the selected s_B stress-at-break cell; preserve the section3.1 elongation-at-break cross-reference issue without numeric correction.'
        prop['method_definition'].update(type='source_reported_conventional', definition=definition, extraction_window=None)
        prop['conditions']['test_method'].update(text=definition, notes='Source-labelled tensile stress at break only. Source standard citation is not independent compliance verification; fracture detection and stress convention unknown.')
        if nr:
            for condition in prop['conditions']['additional_conditions']:
                if condition['name'] == 'stress_strain_convention':
                    condition['fact']['notes'] = 'Source does not explicitly identify engineering versus true stress/strain for the selected stress-at-break result.'
        def bind(node):
            if isinstance(node, dict):
                if node.get('source_id') == fact['source_id'] and 'locator' in node:
                    loc = node['locator']
                    if ('Table' in loc or 'table' in loc) and any(word in loc for word in ('s_M', 'E100', 'modulus', 'Modulus', 'slope')):
                        node['locator'] = fact['locator']
                for value in node.values():
                    bind(value)
            elif isinstance(node, list):
                for value in node:
                    bind(value)
        bind(prop)
        # Bind value and classification directly even if an old locator uses symbols.
        for evidence in prop['evidence']:
            if any(key in evidence['supports'] for key in ('reported_value', 'classification')):
                evidence['locator'] = fact['locator']
        for evidence in prop['method_definition']['evidence']:
            evidence['locator'] = fact['locator']
        scope = 'Retained exact primary XML: selected Table4 break-stress mean/SD cell, tensile method and five-specimen statement, existing identity/state and article permissions. No fresh PDF visual inspection or latest revision/correction/retraction audit; latest status unknown.'
        prop['source_document'].update(inspected_on='2026-11-03', inspection_scope=scope)
        prop['source_document']['revision'] = 'Retained registered XML revision; latest online revision/correction/retraction status unknown.'
        prop['verification']['source_inspection_scope'] = scope
        prop['scope_note'] = boundary + ' Independent batch count and fracture-detection/point-selection algorithm unknown. No automatic engine input, engineering allowable, universal bound or independent scientific validation.'
        state = deepcopy(before.states[prop['material_state_id']])
        assert state['id'] not in states
        a, b, c = state['version'].split('.')
        state['version'] = f'{a}.{b}.{int(c) + 1}'
        state['property_ids'].append(pid)
        state['source_scope'] += ' This supplement adds source-labelled tensile stress at break as a separate quantity; property-specific statistics and unknown fracture criterion remain explicit.'
        states[state['id']] = state
        sources.setdefault(prop['source_id'], deepcopy(before.sources[prop['source_id']]))
        properties.append(prop)
    for source in sources.values():
        source['claim_notes'].append('2026-11-03 stress-at-break supplement: selected existing NR or five printed polymer states, Table4 break-stress mean/SD,n=5 tensile specimens. Not peak/yield strength, modulus, strain or toughness. Unknown fracture criterion, stress convention and independent batches retained. Latest online revision/correction/retraction status not verified. No new identities or engine input.')
    data = deepcopy(before.data)
    data['reference_properties']['records'].extend(properties)
    data['materials']['records'] = [states.get(s['id'], s) for s in data['materials']['records']]
    data['sources']['records'] = [sources.get(s['id'], s) for s in data['sources']['records']]
    after = Database(data)
    contracts = after.validate_scientific_contracts()
    assert all(after.properties[k] == v for k, v in before.properties.items())
    assert after.identities == before.identities and after.grades == before.grades
    assert set(after.states) == set(before.states) and set(after.sources) == set(before.sources)
    assert len(after.properties) == 5258
    out.mkdir(parents=True)
    tables = out / 'native-tables'
    tables.mkdir()
    for name, value in data.items():
        write(tables / (name + '.json'), value)
    write(out / 'native-candidate-r1.json', {'baseline_snapshot': BASE, 'stage': 'frozen_not_applied', 'materials': {'identities': [], 'grades': [], 'records': list(states.values())}, 'sources': {'records': list(sources.values())}, 'reference_properties': {'records': properties}})
    write(out / 'VALIDATION_R1.json', {'baseline_snapshot': BASE, 'preview_snapshot': after.snapshot, 'new_properties': 6, 'new_identities': 0, 'new_states': 0, 'modified_states': 6, 'modified_sources': 2, 'all_old_5252_properties_unchanged': True, 'contracts': contracts, 'native_applied': False, 'pushed': False, 'full_history_regression': 'not_run'})
    print(json.dumps({'snapshot': after.snapshot, 'properties': len(after.properties), 'contracts': contracts}))


if __name__ == '__main__':
    main()
