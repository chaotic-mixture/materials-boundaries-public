"""Freeze two existing-state yield results, never maximum or break stress."""
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

BASE = '62502e5fe24d06f883228fe7d9fea3c579d03d97c25c0b3b8d33a87a9c767bd6'
SHA = 'aa495787abc73a0d98b8c8adbb3c887816afe57076873010b04d41a6730b7f32'
SID = 'mtibe_2022_pbs_pbat_lignin_zno'
URL = 'https://www.ebi.ac.uk/europepmc/webservices/rest/PMC9739168/fullTextXML'


def write(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--xml', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    out = args.output_dir.resolve()
    assert not out.exists() and not out.is_relative_to(ROOT/'materials_boundaries')
    raw = args.xml.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == SHA
    xml = ET.fromstring(raw)
    table = next(t for t in xml.findall('.//table-wrap')
                 if ''.join(t.find('label').itertext()).strip() == 'Table 3')
    assert ''.join(table.find('.//thead/tr')[1].itertext()) == 'Tensile Strength at Yield (MPa)'
    before = Database()
    assert before.snapshot == BASE
    data = deepcopy(before.data)
    props, states = [], []
    for row_name, suffix, expected in [
        ('PBAT', 'pbat_ecoflex_c1200', ('8.38', '0.11')),
        ('PBS-PBAT (70/30)', 'pbs_pbat_70_30', ('26.99', '0.32')),
    ]:
        row = next(r for r in table.findall('.//tbody/tr') if ''.join(r[0].itertext()).strip() == row_name)
        pair = lambda cell: re.fullmatch(r'\s*(\d+\.\d+)\s*±\s*(\d+\.\d+)\s*', ''.join(cell.itertext())).groups()
        old = before.properties['refprop_mtibe2022_'+suffix+'_tensile_modulus']
        assert pair(row[3]) == (old['reported_value']['number'], old['uncertainty']['number'])
        value, amplitude = pair(row[1])
        assert (value, amplitude) == expected
        prop = deepcopy(old)
        prop.update(id=old['id'].replace('_tensile_modulus', '_tensile_yield_strength'),
                    quantity='tensile_yield_strength', source_property_label='Tensile Strength at Yield (MPa)')
        prop['reported_value'].update(number=value, value_text=value)
        prop['uncertainty'].update(number=amplitude, value_text=amplitude)
        prop['uncertainty_note'] = f'{value} ± {amplitude} MPa: source does not define the central estimator or ± as SD, SE, CI, range or tolerance. Five specimens do not establish those statistics.'
        prop['basis_note'] = 'Table 3 explicitly labels tensile strength at yield. Preserve reported center and unspecified ±; do not interpret as maximum tensile strength, stress at break or modulus.'
        method = 'Instron tensile test, source-stated ASTM D638, at 25 °C following 48 h conditioning at 25 °C; five specimens per group. Yield criterion, offset/upper/lower event, gauge geometry and crosshead speed are not specified. Standard edition/compliance not independently verified.'
        prop['conditions']['test_method']['text'] = method
        prop['conditions']['additional_conditions'].append({'name':'yield_criterion', 'fact':{
            'status':'not_reported_in_inspected_source', 'text':None, 'evidence':[],
            'notes':'No offset percentage, upper/lower yield event or numerical yield criterion reported; do not infer 0.2% offset from ASTM D638.'}})
        prop['method_definition']['definition'] = method
        prop['sample_count']['scope'] = 'Five tensile specimens for this selected source group; independent production-batch count unknown.'
        prop['sample_count']['source_statement'] = 'Five specimens from each biopolymer and blend group were tested.'
        prop['scope_note'] += ' Source-labelled yield strength only: yield criterion, test/conditioning RH, numerical rate and gauge geometry remain unknown. No transfer to other preparation states or automatic mechanics evaluation.'
        def evidence_update(node):
            if isinstance(node, dict):
                if node.get('source_id') == SID and 'locator' in node:
                    node['url'] = URL
                    node['locator'] = ('Table 3, '+row_name+' row × Tensile Strength at Yield (MPa)'
                        if 'Table 3' in node['locator'] else 'Section 2.6.2, tensile testing and conditioning')
                for child in node.values(): evidence_update(child)
            elif isinstance(node, list):
                for child in node: evidence_update(child)
        evidence_update(prop)
        scope = 'Retained PMC9739168 primary XML Table 3 selected PBAT and unfilled PBS-PBAT (70/30) yield cells; sections 2.3 and 2.6.2, Tables 1–2 for shared identity/preparation, permission notice. No fresh PDF inspection or raw-data reanalysis.'
        prop['source_document'].update(url=URL, revision='Retained primary XML; historical PDF is a different asset.',
            inspected_on='2026-11-03', sha256=SHA, inspection_scope=scope)
        prop['verification']['source_inspection_scope'] = scope
        state = deepcopy(before.states[prop['material_state_id']])
        state['version'] = '1.0.1'
        state['property_ids'].append(prop['id'])
        props.append(prop)
        states.append(state)
    source = deepcopy(before.sources[SID])
    assert URL not in source['urls']
    source['urls'].append(URL)
    source['claim_notes'].append('2026-11-03 XML supplement: Table 3 selected PBAT and unfilled PBS-PBAT (70/30) source-labelled tensile yield strength. Yield criterion and ± meaning remain unknown. No maximum/break-stress reinterpretation; original five modulus records unchanged.')
    data['reference_properties']['records'].extend(props)
    changed = {state['id']:state for state in states}
    data['materials']['records'] = [changed.get(state['id'], state) for state in data['materials']['records']]
    data['sources']['records'] = [source if item['id']==SID else item for item in data['sources']['records']]
    after = Database(data)
    contracts = after.validate_scientific_contracts()
    assert all(after.properties[k] == v for k,v in before.properties.items())
    assert after.identities == before.identities and after.grades == before.grades and set(after.states) == set(before.states)
    out.mkdir(parents=True)
    tables = out/'native-tables'
    tables.mkdir()
    for name, value in data.items(): write(tables/(name+'.json'), value)
    write(out/'native-candidate-r1.json', {'baseline_snapshot':BASE, 'stage':'frozen_not_applied',
        'materials':{'identities':[], 'grades':[], 'records':states},
        'sources':{'records':[source]}, 'reference_properties':{'records':props}})
    write(out/'VALIDATION_R1.json', {'baseline_snapshot':BASE, 'preview_snapshot':after.snapshot,
        'new_properties':2, 'new_identities':0, 'new_states':0, 'new_sources':0,
        'all_existing_property_objects_unchanged':True, 'contracts':contracts,
        'native_applied':False, 'pushed':False, 'full_history_regression':'not_run'})
    print(json.dumps({'snapshot':after.snapshot, 'contracts':contracts}))


if __name__ == '__main__': main()
