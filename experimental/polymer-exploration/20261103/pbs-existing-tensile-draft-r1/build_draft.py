"""Build isolated strength supplements for existing source-qualified PBS states."""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from materials_boundaries.database import Database

XML_SHA = 'a16999d84b85e49d09979b2d32804e9e9763bc0478449d9a4a2c3c346d7a4a1a'
SID = 'ewurum_mcdonald_2025_pbs_lignin'
URL = 'https://www.ebi.ac.uk/europepmc/webservices/rest/PMC11768263/fullTextXML?format=xml'
BASELINE = 'aa8308dbec8817ee6551078ed91bedb2a9fb05c7924fd76a9131cc680617a95f'


def write(path, obj):
    with path.open('x', encoding='utf-8') as out:
        json.dump(obj, out, ensure_ascii=False, indent=2)
        out.write('\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--xml', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    output = args.output_dir.resolve()
    if output.exists() or output.is_relative_to(ROOT / 'materials_boundaries'):
        raise ValueError('Use a new isolated output directory')
    raw = args.xml.read_bytes()
    if hashlib.sha256(raw).hexdigest() != XML_SHA:
        raise ValueError('Unreviewed XML')
    article = ET.fromstring(raw)
    table = next(t for t in article.findall('.//table-wrap') if t.get('id') == 'polymers-17-00194-t006')
    footnotes = ' '.join(table.find('table-wrap-foot').itertext())
    if 'mean ± standard deviation' not in footnotes:
        raise ValueError('Unverified uncertainty definition')
    before = Database()
    if before.snapshot != BASELINE:
        raise ValueError('Native baseline changed')
    native_moduli = {r['id']: r for r in before.properties.values()
                     if r['source_id'] == SID and r['quantity'] == 'youngs_modulus'}
    label_ids = {'B0': 'refprop_ewurum2025_biopbs_youngs_modulus'}
    label_ids.update({f'B{n}': f'refprop_ewurum2025_pbs_lignin{n}_youngs_modulus' for n in (10,20,30,45)})
    label_ids.update({f'R{n}': f'refprop_ewurum2025_pbs_lignin_r{n}_youngs_modulus' for n in (10,20,30,45)})
    assert set(label_ids.values()) == set(native_moduli)
    facts, proposed = [], []
    method = ('Injection-molded microtensile dog-bones; source-stated ASTM D1708, Instron 5500R-1132, '
              'Bluehill v3.3, Epsilon 3542 extensometer; crosshead speed 1 mm/min. '
              'Tensile strength as reported; engineering/true stress convention and strength-reduction algorithm unspecified.')
    for row in table.findall('.//tbody/tr'):
        cells = list(row)
        label = ''.join(cells[0].itertext()).strip()
        # Cell.text excludes Tukey superscripts: letters are not numeric precision.
        strength = re.fullmatch(r'\s*(\d+(?:\.\d+)?)\s*±\s*(\d+(?:\.\d+)?)\s*', cells[1].text or '')
        modulus = re.fullmatch(r'\s*(\d+(?:\.\d+)?)\s*±\s*(\d+(?:\.\d+)?)\s*', cells[2].text or '')
        assert strength and modulus, label
        fact = {'label': label, 'strength_mean_MPa': strength[1], 'strength_SD_MPa': strength[2],
                'modulus_mean_MPa': modulus[1], 'modulus_SD_MPa': modulus[2],
                'decision': 'defer_R0_state_identity_mapping' if label == 'R0' else 'draft_strength_existing_state'}
        facts.append(fact)
        if label == 'R0':
            continue
        base = native_moduli[label_ids[label]]
        assert (base['reported_value']['number'], base['uncertainty']['number']) == (modulus[1], modulus[2])
        record = deepcopy(base)
        record['id'] = base['id'].replace('youngs_modulus', 'tensile_strength')
        assert record['id'] not in before.properties
        record['quantity'] = 'tensile_strength'
        record['source_property_label'] = 'Tensile Strength (MPa)'
        record['reported_value'].update(value_text=strength[1], number=strength[1])
        record['uncertainty'].update(value_text=strength[2], number=strength[2])
        record['uncertainty_note'] = f'{strength[1]} ± {strength[2]} MPa; Table 6 explicitly defines mean ± SD, rounded up to mean precision where necessary. No SE/CI conversion.'
        record['conditions']['test_method']['text'] = method
        record['method_definition']['definition'] = method
        record['scope_note'] = f'Only existing injection-molded {label} state from Ewurum/McDonald 2025. Preserve unresolved BioPBS FZ91PM/FZ91PB designation and source input-ratio/DCP basis. No final-network composition or general engineering allowable inferred.'
        record['sample_count']['scope'] = 'Ten tensile specimens; independent production-batch count unspecified.'
        def evidence_update(node):
            if isinstance(node, dict):
                if node.get('source_id') == SID and 'locator' in node:
                    old_locator = node['locator']
                    node['url'] = URL
                    node['locator'] = (f'Table 6, {label} row, Tensile Strength (MPa); mean/SD footnote'
                                       if 'Table 6' in old_locator else 'Sections 2.1–2.3 and 2.9; source-cited standard reference [32]')
                for value in node.values(): evidence_update(value)
            elif isinstance(node, list):
                for value in node: evidence_update(value)
        evidence_update(record)
        scope = 'Fresh primary XML: sections 2.1–2.3, 2.9, Table 6 and mean/SD footnotes. No fresh PDF visual check or independent review.'
        record['source_document'] = {'url': URL, 'revision': None, 'inspected_on': '2026-11-03',
                                    'sha256': XML_SHA, 'hash_status': 'recorded', 'hash_note': None,
                                    'inspection_scope': scope, 'inspection_status': 'selected_content_inspected'}
        record['verification'].update(source_inspection_scope=scope, independent_scientific_review=False, raw_data_reanalysis=False)
        proposed.append(record)
    assert len(facts) == 10 and len(proposed) == 9
    data = deepcopy(before.data)
    data['reference_properties']['records'].extend(proposed)
    source = next(s for s in data['sources']['records'] if s['id'] == SID)
    assert URL not in source['urls']
    source['urls'].append(URL)
    source['claim_notes'].append('2026-11-03 primary XML supplement: Table 6 tensile strength means/SDs and section 2.9 method reread by curator; draft supplements for nine existing states remain pending independent review. No fresh PDF visual inspection or scientific replication claimed.')
    changed_states = []
    state_rows = {s['id']: s for s in data['materials']['records']}
    for record in proposed:
        state = state_rows[record['material_state_id']]
        state['property_ids'].append(record['id'])
        major, minor, patch = map(int, state['version'].split('.'))
        state['version'] = f'{major}.{minor}.{patch+1}'
        changed_states.append(deepcopy(state))
    after = Database(data)
    contracts = after.validate_scientific_contracts()
    assert data['materials']['identities'] == before.data['materials']['identities']
    assert data['materials']['grades'] == before.data['materials']['grades']
    assert [s for s in data['sources']['records'] if s['id'] != SID] == [s for s in before.data['sources']['records'] if s['id'] != SID]
    for state in changed_states:
        old = before.states[state['id']]
        assert {k:v for k,v in old.items() if k not in ('version','property_ids')} == {k:v for k,v in state.items() if k not in ('version','property_ids')}
    assert len(after.properties) == len(before.properties) + 9
    output.mkdir(parents=True)
    write(output/'source-facts-r1.json', {'rows': facts, 'xml_sha256': XML_SHA,
                                        'uncertainty_definition': 'mean ± SD; source rounding qualifier retained'})
    write(output/'native-candidate-r1.json', {'stage': 'isolated_draft_not_applied_pending_review',
          'baseline_snapshot': BASELINE, 'materials': {'identities': [], 'grades': [], 'records': changed_states},
          'sources': {'records': [source]}, 'reference_properties': {'records': proposed}})
    write(output/'VALIDATION_R1.json', {'baseline_snapshot': BASELINE, 'preview_snapshot': after.snapshot,
          'source_rows_read': 10, 'existing_modulus_mean_SD_pairs_matched': 9, 'draft_strength_records': 9,
          'new_identities': 0, 'new_states': 0, 'new_sources': 0, 'live_native_unchanged': Database().snapshot == BASELINE,
          'existing_state_link_revisions': len(changed_states),
          'contracts': contracts, 'full_history_regression': 'not_run', 'independent_review': 'pending',
          'pdf_visual_check': 'not_performed', 'pushed': False})
    print(json.dumps({'draft_records': 9, 'preview_snapshot': after.snapshot, 'contracts': contracts}))


if __name__ == '__main__':
    main()
