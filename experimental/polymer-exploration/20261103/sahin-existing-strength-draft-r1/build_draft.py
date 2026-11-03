"""Draft five strength supplements for existing printed-polymer states."""
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

SID = 'sahin_2026_polymer_mechanical_dielectric'
SHA = '0570b4cad935fcbf7363999960e40333d6a46fd2d113b3c9f87e7da9c4a9e7d3'
BASE = 'aa8308dbec8817ee6551078ed91bedb2a9fb05c7924fd76a9131cc680617a95f'


def text(node):
    return ' '.join(''.join(node.itertext()).split())


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
    assert not output.exists()
    assert not output.is_relative_to(ROOT / 'materials_boundaries')
    raw = args.xml.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == SHA
    article = ET.fromstring(raw)
    table = next(t for t in article.findall('.//table-wrap') if t.get('id') == 'polymers-18-01345-t004')
    header = [text(c) for c in table.find('.//thead/tr')][1:]
    assert header == ['PLA', 'ABS', 'PETG', 'ASA', 'PC/ABS']
    rows = {text(r[0]): list(r)[1:] for r in table.findall('.//tbody/tr')}
    modulus = next(v for k,v in rows.items() if 'Tensile Modulus' in k)
    strength = next(v for k,v in rows.items() if 'Tensile Strength' in k and 'Elongation' not in k)
    break_stress = next(v for k,v in rows.items() if 'Stress at Break' in k)
    pair = lambda c: re.fullmatch(r'(\d+\.\d+)\s*±\s*(\d+\.\d+)', text(c)).groups()
    before = Database()
    assert before.snapshot == BASE
    data = deepcopy(before.data)
    states = {s['id']:s for s in data['materials']['records']}
    proposed, modified_states, facts = [], [], []
    for index, label in enumerate(header):
        slug = label.lower().replace('/', '_')
        old = before.properties[f'refprop_porima_{slug}_sahin_2026_fdm_tensile_modulus']
        assert (old['reported_value']['number'], old['uncertainty']['number']) == pair(modulus[index])
        mean, sd = pair(strength[index])
        record = deepcopy(old)
        record['id'] = old['id'].replace('tensile_modulus', 'tensile_strength')
        assert record['id'] not in before.properties
        record['quantity'] = 'tensile_strength'
        record['source_property_label'] = 's_M—Tensile Strength (MPa)'
        record['reported_value'].update(value_text=mean, number=mean)
        record['uncertainty'].update(value_text=sd, number=sd)
        record['basis_note'] = f'Table 4, {label}, s_M tensile strength {mean} ± {sd} MPa; section 2.3 explicitly gives means and SDs for five tensile specimens. Not the separate s_B stress at break.'
        record['uncertainty_note'] = f'{mean} ± {sd} MPa: group mean ± reported SD, n=5 specimens. No SE, CI or engineering allowable inferred.'
        record['conditions']['test_method']['notes'] = 'Source-reported tensile strength; stress-reduction implementation and engineering/true stress convention not explicitly supplied. Extensometry details and post-print conditioning remain unknown.'
        record['method_definition']['definition'] = 'Source-reported s_M tensile strength from ASTM D638-14 tests, distinct from s_B stress at break, E_t tensile modulus and E_Sec secant modulus in Table 4. Crosshead speed 5.0 mm/min; no strain-rate conversion.'
        record['scope_note'] = 'Only the existing source-defined printed specimen group and recipe. Keep unknown grade/SKU, lot, colour, additives, post-print conditioning, humidity and build/raster relation. A 100% slicer infill setting does not prove zero porosity. Table 1 supplier facts are excluded. No independent scientific validation, universal constant or engineering allowable.'
        for discrepancy in record['source_discrepancies']:
            discrepancy['disposition'] = 'Use Table 4 for this selected s_M strength cell; preserve the section 3.1 elongation-at-break cross-reference issue without numeric correction.'
        def update(node):
            if isinstance(node, dict):
                if node.get('source_id') == SID and 'locator' in node:
                    node['locator'] = node['locator'].replace('E_t—Tensile Modulus', 's_M—Tensile Strength').replace('Table 4 E_t row', 'Table 4 s_M tensile-strength row')
                for v in node.values(): update(v)
            elif isinstance(node,list):
                for v in node: update(v)
        update(record)
        scope = 'Primary XML reobtained with same registered SHA; sections 2.1–2.3, Tables 2–4; selected s_M mean/SD cells and n=5 statement. Curator transcription only; no PDF visual check, raw-data reanalysis or independent review this round.'
        record['source_document'].update(inspected_on='2026-11-03', revision='PMC13259274.1; reacquired XML bytes match the registered asset', inspection_scope=scope)
        record['verification'].update(source_inspection_scope=scope, independent_scientific_review=False)
        state = states[record['material_state_id']]
        state['property_ids'].append(record['id'])
        major, minor, patch = map(int,state['version'].split('.'))
        state['version'] = f'{major}.{minor}.{patch+1}'
        modified_states.append(deepcopy(state))
        proposed.append(record)
        facts.append({'source_label':label,'strength_mean_MPa':mean,'strength_SD_MPa':sd,
                      'separate_stress_at_break_mean_MPa':pair(break_stress[index])[0],
                      'existing_state_id':state['id'],'decision':'draft_strength_only'})
    data['reference_properties']['records'].extend(proposed)
    after = Database(data)
    contracts = after.validate_scientific_contracts()
    assert after.identities == before.identities and after.grades == before.grades and after.sources == before.sources
    assert set(after.states) == set(before.states)
    for pid in before.properties: assert before.properties[pid] == after.properties[pid],pid
    assert Database().snapshot == BASE
    output.mkdir(parents=True)
    write(output/'source-selection-r1.json',{'xml_sha256':SHA,'rows':facts})
    write(output/'native-candidate-r1.json',{'stage':'isolated_draft_not_applied_pending_review','baseline_snapshot':BASE,
          'materials':{'identities':[],'grades':[],'records':modified_states},'sources':{'records':[]},
          'reference_properties':{'records':proposed}})
    write(output/'VALIDATION_R1.json',{'baseline_snapshot':BASE,'preview_snapshot':after.snapshot,
          'existing_modulus_mean_SD_pairs_matched':5,'new_properties':5,'existing_state_link_revisions':5,
          'new_identities':0,'new_states':0,'new_sources':0,'all_existing_properties_unchanged':True,
          'contracts':contracts,'independent_review':'pending','native_applied':False,
          'full_history_regression':'not_run','pdf_visual_check':False,'published':False})
    print(json.dumps({'draft_strength_properties':5,'snapshot':after.snapshot,'contracts':contracts}))


if __name__ == '__main__':
    main()
