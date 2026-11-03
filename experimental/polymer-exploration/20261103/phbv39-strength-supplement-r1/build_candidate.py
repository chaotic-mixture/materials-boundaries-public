"""Freeze a source-labelled PHBV-39 tensile-strength candidate, without applying it."""
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

BASE = '06d8e433c7c28c7b3b10c7a8f9432082a6ccad789f3e0aac7fb50c08d717c7c5'
XML_SHA = 'a37eac0af73559b942f680a671d41a4d870d66d94b76e825cdaf61cc6cd3a3a5'
SID = 'abbasi_2022_manure_phbv'
URL = 'https://www.ebi.ac.uk/europepmc/webservices/rest/PMC9571417/fullTextXML'


def write(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--xml', required=True, type=Path)
    parser.add_argument('--output-dir', required=True, type=Path)
    args = parser.parse_args()
    out = args.output_dir.resolve()
    assert not out.exists() and not out.is_relative_to(ROOT / 'materials_boundaries')
    raw = args.xml.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == XML_SHA
    root = ET.fromstring(raw)
    text = lambda node: ' '.join(' '.join(node.itertext()).split())
    table = next(t for t in root.iter('table-wrap') if text(t.find('label')) == 'Table 9')
    row = next(r for r in table.findall('.//tbody/tr') if text(r[0]) == 'PHBV-39')
    mean, sd = re.fullmatch(r'\s*(\d+\.\d+)\s*±\s*(\d+\.\d+)\s*', row[1].text).groups()
    assert (mean, sd) == ('12.7', '1.9')
    before = Database()
    assert before.snapshot == BASE
    old = before.properties['refprop_abbasi2022_manure_phbv39_youngs_modulus']
    prop = deepcopy(old)
    pid = 'refprop_abbasi2022_manure_phbv39_tensile_strength'
    assert pid not in before.properties
    prop.update(id=pid, quantity='tensile_strength', source_property_label='Tensile Strength (MPa)',
                basis_note='Table 9 source-labelled tensile strength, mean and SD. Source method loads until yield; exact strength extraction criterion remains unspecified. No conversion to maximum, yield or break stress.')
    prop['reported_value'].update(value_text=mean, number=mean, unit_text='MPa', unit_code='MPa')
    prop['uncertainty'].update(value_text=sd, number=sd, unit_text='MPa', unit_code='MPa')
    prop['uncertainty_note'] = '12.7 ± 1.9 MPa, source mean ± SD; table notes SD rounding up to mean precision where necessary. No SE/CI, endpoints or design allowable inferred.'
    method = 'Source-labelled tensile strength from DMA Q800 stress–strain analysis in Universal Analysis v4.5A, room temperature, 10 mm gauge length, controlled force ramp 3 N/min until yield. Exact strength extraction point, stress convention and criterion are not specified; not independently established as maximum, yield or break stress.'
    prop['conditions']['test_method'].update(text=method, notes='Until-yield procedure and tensile-strength table label are retained together, without repairing the source or inferring an extraction criterion.')
    prop['method_definition'].update(definition=method, extraction_window=None)
    prop['sample_count']['scope'] = 'At least five mechanical-test replicates per section 2.2.8; exact selected tensile-group count and independent production-batch count not specified.'
    # Every inherited citation is rebound to the inspected XML, with property-specific locators.
    def citations(node):
        if isinstance(node, dict):
            if node.get('source_id') == SID and 'locator' in node:
                node['url'] = URL
                node['locator'] = ('Table 9, PHBV-39 row, Tensile Strength (MPa), mean/SD footnote' if 'Table 9' in node['locator'] else 'Section 2.2.8, common preparation and tensile method')
            for value in node.values():
                citations(value)
        elif isinstance(node, list):
            for value in node:
                citations(value)
    citations(prop)
    scope = 'Retained primary XML Table 9 PHBV-39 tensile-strength cell/footnotes, section 2.2.8 preparation and tensile method, article permission notice. No fresh PDF inspection, raw-data reanalysis or independent scientific validation.'
    prop['source_document'].update(url=URL, revision='Retained PMC9571417 XML; distinct from historical PDF.', inspected_on='2026-11-03', sha256=XML_SHA, inspection_scope=scope)
    prop['verification']['source_inspection_scope'] = scope
    prop['scope_note'] += ' Source-labelled tensile strength only. Until-yield testing does not establish a maximum-stress, break-stress or yield criterion. Actual temperature/RH, post-press conditioning, exact replicate count, stress convention and extraction rule remain unspecified. SD is mechanical-test variability, not PHBV purity or HV-content uncertainty.'
    state = deepcopy(before.states[prop['material_state_id']])
    major, minor, patch = state['version'].split('.')
    state['version'] = f'{major}.{minor}.{int(patch) + 1}'
    state['property_ids'].append(pid)
    source = deepcopy(before.sources[SID])
    source['claim_notes'].append('2026-11-03 PHBV-39 tensile-strength candidate: direct Table9 12.7 ± 1.9 MPa mean/SD, at least5 replicates. Until-yield method retained; precise strength criterion unknown. No conversion to yield/break/maximum strength, no new identity or state. Pending independent review and local acceptance.')
    data = deepcopy(before.data)
    data['reference_properties']['records'].append(prop)
    data['materials']['records'] = [state if s['id'] == state['id'] else s for s in data['materials']['records']]
    data['sources']['records'] = [source if s['id'] == SID else s for s in data['sources']['records']]
    after = Database(data)
    contracts = after.validate_scientific_contracts()
    assert all(after.properties[k] == v for k, v in before.properties.items())
    assert after.identities == before.identities and after.grades == before.grades and set(after.states) == set(before.states)
    assert Database().snapshot == BASE
    out.mkdir(parents=True)
    tables = out / 'native-tables'
    tables.mkdir()
    for name, value in data.items():
        write(tables / (name + '.json'), value)
    write(out / 'native-candidate-r1.json', {'baseline_snapshot': BASE, 'stage': 'frozen_not_applied', 'materials': {'identities': [], 'grades': [], 'records': [state]}, 'sources': {'records': [source]}, 'reference_properties': {'records': [prop]}})
    write(out / 'SOURCE_FACTS_R1.json', {'source_id': SID, 'primary_XML_sha256': XML_SHA, 'primary_XML_bytes': len(raw), 'table': 'Table 9', 'row': 'PHBV-39', 'quantity_label': 'Tensile Strength (MPa)', 'mean_MPa': mean, 'SD_MPa': sd, 'sample_count_relation': 'at_least', 'sample_count': 5, 'source_until_yield_method_retained': True, 'precise_strength_extraction_criterion': 'unknown', 'license': 'CC BY 4.0', 'other_operational_days_and_flexural_strength': 'not_mapped', 'fresh_PDF_review': False})
    write(out / 'VALIDATION_R1.json', {'baseline_snapshot': BASE, 'preview_snapshot': after.snapshot, 'new_properties': 1, 'new_identities': 0, 'new_states': 0, 'modified_states': 1, 'modified_sources': 1, 'old_5245_properties_unchanged': True, 'contracts': contracts, 'independent_review': 'pending', 'native_applied': False, 'pushed': False, 'full_history_regression': 'not_run'})
    print(json.dumps({'preview_snapshot': after.snapshot, 'contracts': contracts}))


if __name__ == '__main__':
    main()
