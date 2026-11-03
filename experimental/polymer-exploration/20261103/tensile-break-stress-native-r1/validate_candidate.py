"""Validate frozen break-stress tables, actual scoped tests and consumer exports."""
from copy import deepcopy
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tests'))
from build_candidate import read, sha, write
from jsonschema import Draft202012Validator, FormatChecker
from materials_boundaries.database import Database, read_snapshot
from materials_boundaries.material_presentation import render_material_catalog, material_labels


def main():
    out = Path(sys.argv[1]).resolve()
    area = Path(__file__).resolve().parent
    patterns = ['test_database*.py', 'test_material_reference_contract.py', 'test_material_presentation_fast_path.py', 'test_material_reference_expansion.py', 'test_material_uncertainty_contract.py', 'test_material_reported_measures_contract.py', 'test_material_scientific_notation_contract.py', 'test_specified_elongation_contract.py', 'test_flexural_strength_contract.py', 'test_tensile_break_stress_contract.py']
    suite = unittest.TestSuite()
    for pattern in patterns:
        suite.addTests(unittest.TestLoader().discover(str(ROOT / 'tests'), pattern=pattern))
    log = io.StringIO()
    result = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
    (area / 'scoped-tests-r1.log').write_text(log.getvalue(), encoding='utf-8')
    write(area / 'TEST_RESULTS_R1.json', {'scope': patterns, 'tests_run': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors), 'skipped': len(result.skipped), 'successful': result.wasSuccessful(), 'full_history_regression': 'not_run'})
    assert result.wasSuccessful()
    tables = out / 'native-tables'
    data = {name: read(tables / (name + '.json')) for name in ('materials', 'reference_properties', 'sources')}
    schema_names = {'materials': 'materials', 'reference_properties': 'reference_properties', 'sources': 'sources'}
    for name, schema in schema_names.items():
        Draft202012Validator(read(ROOT / 'schemas' / (schema + '.schema.json')), format_checker=FormatChecker()).validate(data[name])
    write(area / 'SCHEMA_VALIDATION_R1.json', {'tables': list(data), 'draft': '2020-12', 'format_checker': 'enabled', 'result': 'passed'})
    before, after = Database(), Database(data)
    candidate = read(out / 'native-candidate-r1.json')
    props = candidate['reference_properties']['records']
    assert len(props) == 6 and all(after.properties[k] == p for k, p in before.properties.items())
    results = {}
    for sid in {p['source_id'] for p in props}:
        counts = {}
        for phase, db in [('before', before), ('after', after)]:
            dest = out / 'source-exports' / sid / phase
            db.export(dest, source=sid)
            manifest, records = read_snapshot(dest)
            expected = {r['property']['id']: r for r in db.records(source=sid)}
            assert records == expected
            counts[phase] = len(records)
        assert counts['after'] - counts['before'] == sum(p['source_id'] == sid for p in props)
        results[sid] = counts
    for lang in ('en', 'zh', 'ja', 'de'):
        with patch('materials_boundaries.catalog.read_catalog', side_effect=lambda name: data[name]):
            text = render_material_catalog({'schema_version': '1.0.0', 'records': props}, 'reference-properties', lang)
        assert material_labels(lang)['code_tensile_stress_at_break'] in text
        assert all(p['reported_value']['number'] in text and p['uncertainty']['number'] in text for p in props)
        assert 'fracture' in text and 'unknown' in text
        (out / ('render-' + lang + '.txt')).write_text(text, encoding='utf-8')
    write(area / 'EXPORT_RENDER_VALIDATION_R1.json', {'source_export_counts': results, 'joined_record_equality': 'passed_before_and_after', 'four_languages': ['en', 'zh', 'ja', 'de'], 'six_means_and_SDs_rendered': True, 'unknowns_rendered': True, 'all_old_5252_properties_unchanged': True, 'native_applied': False})
    for name in ('native-candidate-r1.json', 'VALIDATION_R1.json'):
        (area / name).write_bytes((out / name).read_bytes())
    print(json.dumps({'tests': result.testsRun, 'schema': 'passed', 'exports': results, 'snapshot': after.snapshot}))


if __name__ == '__main__':
    main()
