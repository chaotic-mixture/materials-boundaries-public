"""Prepare an isolated thermal-conductivity implementation; no native writes."""
from pathlib import Path
import hashlib
import json
import re
import shutil
import sys

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
EXT = ROOT.parent / 'open-database-evidence/polymer-thermal-conductivity-contract-prototype-20261104-r1'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def write(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def main():
    assert not EXT.exists()
    source = OUT.parent / 'pur-thermal-conductivity-source-contract-r1'
    review = read(source / 'INDEPENDENT_SOURCE_REVIEW_R1.json')
    assert review['decision'] == 'approved' and review['review_inputs_sha256'] == sha(source / 'REVIEW_INPUTS_R1.json')
    previous = ROOT.parent / 'open-database-evidence/polymer-ac-breakdown-contract-prototype-20261104-r1/SUPPLEMENTAL_TEST_INPUTS_R2.json'
    selection = read(previous)
    files = set(read(OUT.parent / 'local-acceptance-r33/PACKAGE_INPUTS_R33.json'))
    files.update('schemas/' + n for n in ['materials.schema.json', 'reference_properties.schema.json', 'sources.schema.json'])
    files.add('docs/MATERIAL_REFERENCE_CATALOG.md')
    files.update(selection['unchanged_source_test_input_sha256'])
    files.add('tests/test_dielectric_breakdown_strength_contract.py')
    before = {n: sha(ROOT / n) for n in sorted(files)}
    EXT.mkdir()
    for name in before:
        target = EXT / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, target)
    write(EXT / 'BASELINE_INPUTS_R1.json', {'scope': 'Actual approved local r34 worktree,not literal Git53dba source', 'native_snapshot': 'b644c5add9f2157a6a683480e6f204a3a053b06efaaab45f07564db306004146', 'files_sha256': before, 'source_entry_sha256': sha(source / 'REVIEW_INPUTS_R1.json'), 'source_approval_sha256': sha(source / 'INDEPENDENT_SOURCE_REVIEW_R1.json')})
    shutil.copyfile(ROOT / 'schemas/reference_properties.schema.json', EXT / 'BASELINE_REFERENCE_SCHEMA_R1.json')
    module = EXT / 'materials_boundaries/material_references.py'
    original = module.read_text(encoding='utf-8')
    text = original.replace('QUANTITY_DIMENSIONS = {', 'QUANTITY_DIMENSIONS = {\n    "thermal_conductivity": "power_per_length_temperature",', 1)
    text = text.replace('UNIT_DIMENSIONS = {', 'UNIT_DIMENSIONS = {\n    "W/(m*K)": "power_per_length_temperature", "mW/(m*K)": "power_per_length_temperature",', 1)
    text = text.replace('ELECTRIC_FIELD_UNITS =', 'THERMAL_CONDUCTIVITY_UNITS = ("W/(m*K)", "mW/(m*K)")\nELECTRIC_FIELD_UNITS =', 1)
    marker = '    definitions["electric_field_reported_value"] = deepcopy(definitions["reported_value"])'
    text = text.replace(marker, '    definitions["thermal_conductivity_reported_value"] = deepcopy(definitions["reported_value"])\n    for branch in definitions["thermal_conductivity_reported_value"]["oneOf"]:\n        branch["properties"]["unit_code"] = _enum(THERMAL_CONDUCTIVITY_UNITS)\n' + marker, 1)
    text = text.replace('*TEMPERATURE_UNITS, *ELECTRIC_FIELD_UNITS})', '*TEMPERATURE_UNITS, *ELECTRIC_FIELD_UNITS, *THERMAL_CONDUCTIVITY_UNITS})', 1)
    text = text.replace('if quantity != "dielectric_breakdown_strength"}', 'if quantity not in {"dielectric_breakdown_strength", "thermal_conductivity"}}', 1)
    marker = '    other = definitions["property"]'
    text = text.replace(marker, '    thermal = deepcopy(definitions["property"])\n    thermal["properties"]["quantity"] = {"const": "thermal_conductivity"}\n    thermal["properties"]["quantity_dimension"] = {"const": "power_per_length_temperature"}\n    thermal["properties"]["reported_value"] = _ref("thermal_conductivity_reported_value")\n    del thermal["properties"]["specified_elongation"]\n' + marker, 1)
    text = text.replace('if q not in {"dielectric_breakdown_strength",', 'if q not in {"thermal_conductivity", "dielectric_breakdown_strength",', 1)
    text = text.replace('[other, stress, elongation, shore, temperature, electric]', '[other, stress, elongation, shore, temperature, electric, thermal]', 1)
    text = text.replace('_UNIT_SPELLINGS = {', '_UNIT_SPELLINGS = {\n    "W/(m*K)": {"W/(m*K)", "W/(m·K)"},\n    "mW/(m*K)": {"mW/(m*K)", "mW/(m·K)"},', 1)
    assert text != original and 'THERMAL_CONDUCTIVITY_UNITS' in text
    module.write_text(text, encoding='utf-8', newline='\n')
    presentation = EXT / 'materials_boundaries/material_presentation.py'
    text = presentation.read_text(encoding='utf-8').replace("REQUIRED_LABELS |= frozenset(('code_dielectric_breakdown_strength',))", "REQUIRED_LABELS |= frozenset(('code_dielectric_breakdown_strength',))\nREQUIRED_LABELS |= frozenset(('code_thermal_conductivity',))", 1)
    presentation.write_text(text, encoding='utf-8', newline='\n')
    locale_file = EXT / 'materials_boundaries/data/material_locales.json'
    locales = read(locale_file)
    for language, label in {'en': 'Thermal conductivity', 'zh': '热导率', 'ja': '熱伝導率', 'de': 'Wärmeleitfähigkeit'}.items():
        assert 'code_thermal_conductivity' not in locales['languages'][language]
        locales['languages'][language]['code_thermal_conductivity'] = label
    locale_file.write_text(json.dumps(locales, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
    doc = EXT / 'docs/MATERIAL_REFERENCE_CATALOG.md'
    with doc.open('a', encoding='utf-8', newline='\n') as stream:
        stream.write('''\n\n### Thermal-conductivity references\n\n`thermal_conductivity` uses the separate `power_per_length_temperature` dimension\nand closed `W/(m*K)` / `mW/(m*K)` unit codes. Original middle-dot unit labels and\ndecimal precision are retained; milli/base units are never automatically converted.\nPositive source central values and nonnegative absolute uncertainty amplitudes\nuse the same unit code; existing relative uncertainty roles remain distinct.\nThese are condition-qualified catalogue references, not thermal-engine inputs\nor engineering allowables. Mean plate temperature is not evidence of a group\nmean, isotropy, replicate count or a complete specimen-conditioning procedure.\nDo not transfer counts or density normalization from neighbouring mechanical tests.\n''')
    archive = EXT / 'legacy-six-branch-test-inputs'
    archive.mkdir()
    changed = []
    for name in selection['branch_count_tests_changed']:
        path = EXT / name
        content = path.read_bytes()
        updated, count = re.subn(rb"(\['oneOf'\]\),\s*)6\)", rb'\g<1>7)', content)
        assert count == 1, name
        shutil.copyfile(path, archive / path.name)
        path.write_bytes(updated)
        changed.append(name)
    sys.path.insert(0, str(EXT))
    from materials_boundaries.material_references import _PROPERTIES_SCHEMA
    old = read(EXT / 'BASELINE_REFERENCE_SCHEMA_R1.json')
    assert old['$defs']['property']['oneOf'] == _PROPERTIES_SCHEMA['$defs']['property']['oneOf'][:6]
    assert old['$defs']['legacy_reported_value'] == _PROPERTIES_SCHEMA['$defs']['legacy_reported_value']
    (EXT / 'schemas/reference_properties.schema.json').write_text(json.dumps(_PROPERTIES_SCHEMA, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
    write(EXT / 'LEGACY_SCHEMA_COMPATIBILITY_R1.json', {'old_complete_branches': 6, 'new_complete_branches': 7, 'old_six_branch_objects_literally_equal': True, 'legacy_reported_value_literally_equal': True, 'shared_uncertainty_vocabulary': 'two conductivity units added;existing semantic role/unit rules unchanged'})
    write(EXT / 'SCOPE_SELECTION_R1.json', {'patterns': selection['patterns'] + ['test_thermal_conductivity_contract.py'], 'only_legacy_test_changes': changed, 'old_test_change_scope': 'One expected branchcount6to7 assertion per7files;oldbytes retained'})
    assert all(sha(ROOT / n) == h for n, h in before.items())
    print(json.dumps({'isolated_files': len(before), 'old_six_branches_exact': True, 'legacy_test_count_changes': len(changed), 'native_code_data_changed': False}))


if __name__ == '__main__':
    main()
