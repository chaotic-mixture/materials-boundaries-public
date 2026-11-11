"""Isolated structural prototype; production runtime and tables stay untouched."""
from copy import deepcopy
from pathlib import Path
import hashlib
import json
import shutil
import sys

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
EXT = ROOT.parent / 'open-database-evidence/polymer-nr-work-contract-20261111-r1'
sys.path.insert(0, str(ROOT))
from materials_boundaries.material_references import _PROPERTIES_SCHEMA
from jsonschema import Draft202012Validator, ValidationError


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    EXT.mkdir(exist_ok=False)
    names = ['materials_boundaries/material_references.py', 'materials_boundaries/material_presentation.py',
             'materials_boundaries/data/material_locales.json', 'schemas/reference_properties.schema.json']
    before = {name: sha(ROOT / name) for name in names}
    for name in names:
        path = EXT / 'baseline' / name
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, path)
    schema = deepcopy(_PROPERTIES_SCHEMA)
    definitions = schema['$defs']
    units = ['J/cm^3', 'MJ/m^3', 'J/m^3']
    definitions['work_reported_value'] = deepcopy(definitions['reported_value'])
    for value in definitions['work_reported_value']['oneOf']:
        value['properties']['unit_code'] = {'type': 'string', 'enum': units}
    definitions['work_reference_basis'] = {'oneOf': deepcopy(definitions['fact']['oneOf'][:3])}
    branch = deepcopy(definitions['property']['oneOf'][0])
    branch['properties']['quantity'] = {'const': 'volumetric_tensile_work_to_break'}
    branch['properties']['quantity_dimension'] = {'const': 'energy_per_volume'}
    branch['properties']['reported_value'] = {'$ref': '#/$defs/work_reported_value'}
    branch['properties']['work_reference_basis'] = {'$ref': '#/$defs/work_reference_basis'}
    branch['required'].append('work_reference_basis')
    definitions['property']['oneOf'].append(branch)
    def extend(node):
        if isinstance(node, dict):
            value = node.get('properties', {}).get('unit_code', {})
            if 'MPa' in value.get('enum', []):
                value['enum'].extend(units)
            for child in node.values(): extend(child)
        elif isinstance(node, list):
            for child in node: extend(child)
    for name in ['uncertainty', 'reported_measure']:
        extend(definitions[name])
    assert definitions['property']['oneOf'][:11] == _PROPERTIES_SCHEMA['$defs']['property']['oneOf']
    assert definitions['legacy_reported_value'] == _PROPERTIES_SCHEMA['$defs']['legacy_reported_value']
    Draft202012Validator.check_schema(schema)
    properties = json.loads((ROOT / 'materials_boundaries/data/reference_properties.json').read_bytes())
    original = next(p for p in properties['records'] if p['id'] == 'refprop_smr10_bianchi2025_nr_finite_strain_tensile_modulus')
    record = deepcopy(original)
    record.update(quantity='volumetric_tensile_work_to_break', quantity_dimension='energy_per_volume')
    record['reported_value'].update(unit_code='J/cm^3', unit_text='J/cm³')
    record['uncertainty'].update(unit_code='J/cm^3', unit_text='J/cm³')
    record['work_reference_basis'] = dict(status='not_reported_in_inspected_source', text=None, evidence=[], notes='Synthetic structural probe;volume basis unknown.')
    validator = Draft202012Validator(schema)
    def check(value): validator.validate({'schema_version': '1.0.0', 'records': [value]})
    check(record)
    invalid = []
    missing = deepcopy(record); del missing['work_reference_basis']; invalid.append(missing)
    bad = deepcopy(record); bad['work_reference_basis']['status'] = 'not_applicable'; invalid.append(bad)
    bad = deepcopy(record); bad['reported_value']['unit_code'] = 'MPa'; invalid.append(bad)
    bad = deepcopy(original); bad['work_reference_basis'] = record['work_reference_basis']; invalid.append(bad)
    for bad in invalid:
        try: check(bad)
        except ValidationError: pass
        else: raise AssertionError('Invalid structural probe accepted')
    assert all(sha(ROOT / name) == digest for name, digest in before.items())
    for name, value in [('SCHEMA_PREVIEW_R1.json', schema), ('STRUCTURAL_CHECKS_R1.json', {
        'valid_synthetic_envelope': 1, 'invalid_envelopes_rejected': 4, 'old11branches_equal': True,
        'legacy_value_equal': True, 'production_files_sha256_unchanged': before,
        'scope': 'Schema-only prototype,not runtime implementation/tests or native candidate',
        'semantic_validation_render_export_installation': 'not_implemented_or_run', 'native_applied': False})]:
        with (HERE / name).open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2); stream.write('\n')
    print('Schema preview: old11 unchanged;1valid/4invalid structural probes verified;production untouched')


if __name__ == '__main__': main()
