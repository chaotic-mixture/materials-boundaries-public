"""Meaningful synthetic boundary probes; not source measurements or full tests."""
from copy import deepcopy
from pathlib import Path
import hashlib
import json
import sys
ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from jsonschema import Draft202012Validator
from semantic_preview import validate_work_semantics, basis_key


def main():
    schema = json.loads((HERE / 'SCHEMA_PREVIEW_R1.json').read_bytes())
    validator = Draft202012Validator(schema)
    native = json.loads((ROOT / 'materials_boundaries/data/reference_properties.json').read_bytes())
    original = next(p for p in native['records'] if p['id'] == 'refprop_smr10_bianchi2025_nr_finite_strain_tensile_modulus')
    prop = deepcopy(original)
    prop.update(quantity='volumetric_tensile_work_to_break', quantity_dimension='energy_per_volume')
    prop['reported_value'].update(number='0.350', value_text='0.350', unit_code='J/cm^3', unit_text='J/cm³')
    prop['uncertainty'].update(unit_code='J/cm^3', unit_text='J/cm³')
    prop['work_reference_basis'] = dict(status='not_reported_in_inspected_source', text=None, evidence=[], notes='Synthetic unknown volume basis.')
    def check(p):
        validator.validate({'schema_version': '1.0.0', 'records': [p]})
        validate_work_semantics(p)
    check(prop)
    zero = deepcopy(prop); zero['reported_value'].update(number='0', value_text='0'); check(zero)
    failures = []
    p = deepcopy(prop); p['reported_value']['unit_text'] = 'MJ/m³'; failures.append(p)
    p = deepcopy(prop); p['uncertainty'].update(unit_code='MJ/m^3', unit_text='MJ/m³'); failures.append(p)
    p = deepcopy(prop); p['reported_value']['value_text'] = '0.35'; failures.append(p)
    p = deepcopy(prop); p['work_reference_basis'].update(status='reported', text='initial volume', evidence=deepcopy(prop['evidence'][:1])); p['work_reference_basis']['evidence'][0]['supports'] = ['reported_value']; failures.append(p)
    p = deepcopy(prop); p['work_reference_basis']['notes'] = None; failures.append(p)
    for p in failures:
        try: check(p)
        except ValueError: pass
        else: raise AssertionError('Semantic defect accepted')
    clone = deepcopy(prop); clone['work_reference_basis'].update(status='not_verified', notes='Different unknown wording')
    assert basis_key(clone) == basis_key(prop)
    before = json.loads((HERE / 'STRUCTURAL_CHECKS_R1.json').read_bytes())['production_files_sha256_unchanged']
    assert all(hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest for name, digest in before.items())
    with (HERE / 'SEMANTIC_CHECKS_R1.json').open('x', encoding='utf-8', newline='\n') as stream:
        json.dump({'synthetic_valid_cases': 2, 'semantic_defects_rejected': len(failures), 'unknown_basis_no_wording_inflation': True,
            'production_unchanged': True, 'scope': 'Isolated work-specific checks,not generic graph/runtime integration',
            'presentation_export_install_native_admission': 'not_run'}, stream, indent=2); stream.write('\n')
    print('2 valid/5 semantic defects checked;unknown basis stable;production unchanged')


if __name__ == '__main__': main()
