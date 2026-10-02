"""Closed temperature metadata contracts, with independent one-field mutations.

Every rejected mutation starts from a fresh valid catalog and is sent separately
through the dependency-free runtime guard and the complete development validator.
The synthetic appendability record tests plumbing, not new source evidence.
"""
import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

from jsonschema import Draft202012Validator, FormatChecker

from materials_boundaries.temperature import (
    TemperatureError, evaluate_temperature, validate_model_catalog,
)
from scripts.validate_catalogs import CatalogValidationError, load_catalogs, validate_catalogs


ROOT = Path(__file__).resolve().parents[1]
LINEAR = 'synthetic_linear_temperature'
OVERLAP = 'synthetic_overlap_temperature'
UNKNOWN_FIELDS = (
    'pressure', 'test_direction', 'grain_size', 'texture', 'porosity', 'product_form',
    'specimen_geometry', 'cold_work', 'test_method', 'strain_rate_or_frequency',
    'measurement_uncertainty', 'fit_error_statistical_definition', 'confidence_level',
)
MODEL_FIELDS = (
    'id', 'version', 'name', 'descriptions', 'classification', 'evaluation_support',
    'equation_family', 'quantity', 'input_unit', 'output_unit', 'equation_display',
    'coefficient_order', 'coefficient_units', 'material', 'branches', 'unknown_conditions',
    'overlap_policy', 'source_ids', 'source_locator', 'author_provenance',
    'scope_exclusions', 'verification', 'reuse', 'curation_date', 'range_interpretation',
)
PROVENANCE_FIELDS = ('author', 'creation_method', 'is_empirical', 'derived_from_measurements')
VERIFICATION_FLAGS = {
    'synthetic_arithmetic_checked': True,
    'independent_scientific_review': False,
    'empirical_validation': False,
}
FIT_FLAGS = ('is_measurement_uncertainty', 'is_confidence_interval', 'is_validated_maximum_error_bound')
BRANCH = ('branches', 0)
FIT = (*BRANCH, 'reported_fit_error')
OBJECT_FIELDS = (
    ((), MODEL_FIELDS),
    (('descriptions',), ('en', 'zh', 'ja', 'de')),
    (('material',), ('name', 'UNS', 'temper', 'temper_status', 'identity_status')),
    (BRANCH, ('id', 'coefficients_text', 'source_data_range_K', 'equation_range_K',
              'range_status', 'endpoints', 'reported_fit_error')),
    (FIT, ('value', 'unit', 'status', 'statistic', 'confidence_level', *FIT_FLAGS)),
    (('unknown_conditions',), UNKNOWN_FIELDS),
    *((('unknown_conditions', field), ('value', 'status')) for field in UNKNOWN_FIELDS),
    (('author_provenance',), PROVENANCE_FIELDS),
    (('verification',), (*VERIFICATION_FLAGS, 'translation_review')),
    (('reuse',), ('status', 'caveats', 'recommended_attribution')),
)
TEXT_PATHS = (
    ('name',), ('source_locator',), ('range_interpretation',),
    *(('descriptions', lang) for lang in ('en', 'zh', 'ja', 'de')),
    ('material', 'name'),
    *(('unknown_conditions', field, 'status') for field in UNKNOWN_FIELDS),
    ('author_provenance', 'author'),
    ('verification', 'translation_review'), ('reuse', 'status'), ('reuse', 'recommended_attribution'),
    ('source_ids', 0), ('scope_exclusions', 0), ('reuse', 'caveats', 0),
)


def at(value, path):
    for key in path:
        value = value[key]
    return value


def put(value, path, replacement):
    at(value, path[:-1])[path[-1]] = replacement


class TemperatureMetadataGuardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalogs = load_catalogs(ROOT / 'materials_boundaries/data')
        cls.schema = json.loads((ROOT / 'schemas/temperature_models.schema.json').read_text())
        cls.schema_validator = Draft202012Validator(cls.schema, format_checker=FormatChecker())

    def candidate(self, identifier=LINEAR):
        catalogs = copy.deepcopy(self.catalogs)
        model = next(row for row in catalogs['temperature_models']['records'] if row['id'] == identifier)
        return catalogs, model

    def reject(self, catalogs):
        with self.assertRaises(TemperatureError):
            validate_model_catalog(catalogs['temperature_models'])
        with self.assertRaises(CatalogValidationError):
            validate_catalogs(catalogs)

    def reject_value(self, path, value, identifier=LINEAR):
        catalogs, model = self.candidate(identifier)
        put(model, path, value)
        self.reject(catalogs)

    def accept(self, catalogs):
        before = copy.deepcopy(catalogs)
        self.assertIs(validate_model_catalog(catalogs['temperature_models']), catalogs['temperature_models'])
        self.schema_validator.validate(catalogs['temperature_models'])
        validate_catalogs(catalogs)
        self.assertEqual(catalogs, before, 'validation must not normalize or mutate source metadata')

    def test_current_complete_catalog_is_accepted_unchanged(self):
        self.accept(copy.deepcopy(self.catalogs))

    def test_catalog_envelope_is_closed_and_records_are_nonempty(self):
        for value in (None, [], False, 'catalog'):
            with self.subTest(envelope=value):
                catalogs = copy.deepcopy(self.catalogs)
                catalogs['temperature_models'] = value
                self.reject(catalogs)
        for field in ('schema_version', 'records'):
            with self.subTest(missing=field):
                catalogs = copy.deepcopy(self.catalogs)
                del catalogs['temperature_models'][field]
                self.reject(catalogs)
        catalogs = copy.deepcopy(self.catalogs)
        catalogs['temperature_models']['extra'] = None
        self.reject(catalogs)
        for value in ('2.0.0', None, True, 1):
            with self.subTest(schema_version=value):
                catalogs = copy.deepcopy(self.catalogs)
                catalogs['temperature_models']['schema_version'] = value
                self.reject(catalogs)
        for value in ([], None, {}, False, 'records'):
            with self.subTest(records=value):
                catalogs = copy.deepcopy(self.catalogs)
                catalogs['temperature_models']['records'] = value
                self.reject(catalogs)

    def test_every_required_field_is_independently_required(self):
        for path, required in OBJECT_FIELDS:
            for field in required:
                with self.subTest(object=path, missing=field):
                    catalogs, model = self.candidate()
                    del at(model, path)[field]
                    self.reject(catalogs)

    def test_every_object_is_closed_and_requires_an_object(self):
        for path, _ in OBJECT_FIELDS:
            with self.subTest(object=path, extra=True):
                catalogs, model = self.candidate()
                at(model, path)['extra'] = None
                self.reject(catalogs)
            for value in (None, [], False, 'object'):
                with self.subTest(object=path, invalid_type=value):
                    catalogs, model = self.candidate()
                    if path:
                        put(model, path, value)
                    else:
                        index = catalogs['temperature_models']['records'].index(model)
                        catalogs['temperature_models']['records'][index] = value
                    self.reject(catalogs)

    def test_authored_text_fields_reject_empty_whitespace_and_nonstrings(self):
        for path in TEXT_PATHS:
            for value in ('', ' \t\r\n\u2003 ', None, False, 1, [], {}):
                with self.subTest(field=path, value=value):
                    self.reject_value(path, value)

    def test_text_arrays_require_nonempty_lists_and_valid_items(self):
        for path in (('source_ids',), ('scope_exclusions',), ('reuse', 'caveats')):
            for value in ([], None, {}, True, 'not a list', ['valid', None], ['valid', '  ']):
                with self.subTest(field=path, value=value):
                    self.reject_value(path, value)
        catalogs, model = self.candidate()
        model['source_ids'].append(model['source_ids'][0])
        self.reject(catalogs)

    def test_model_and_branch_ids_reject_malformed_and_duplicate_ids(self):
        malformed = ('', ' ', 'UPPER', '0leading', '_leading', 'has-hyphen', 'has.dot',
                     'has space', 'trailing\n', ' leading', 'éclair', None, False, 1, [], {})
        for path in (('id',), (*BRANCH, 'id')):
            for value in malformed:
                with self.subTest(field=path, value=value):
                    self.reject_value(path, value)
        catalogs, model = self.candidate()
        catalogs['temperature_models']['records'].append(copy.deepcopy(model))
        self.reject(catalogs)
        catalogs, model = self.candidate()
        model['branches'].append(copy.deepcopy(model['branches'][0]))
        self.reject(catalogs)
        catalogs, model = self.candidate()
        other = next(row for row in catalogs['temperature_models']['records'] if row['id'] == OVERLAP)
        other['branches'][0]['id'] = model['branches'][0]['id']
        self.reject(catalogs)

    def test_curation_date_requires_real_calendar_date_and_exact_iso_shape(self):
        invalid = ('', ' ', '2026-02-29', '2024-02-30', '2026-13-01', '2026-00-01',
                   '0000-01-01', '2026-10-00', '2026-10-32', '2026-1-02', '2026-10-2',
                   '20261002', '2026-W40-5', '2026-10-02T00:00:00Z', '2026-10-02\n',
                   ' 2026-10-02', '２０２６-１０-０２', None, True, 20261002, [], {})
        for value in invalid:
            with self.subTest(value=value):
                self.reject_value(('curation_date',), value)
        for value in ('2024-02-29', '0001-01-01', '9999-12-31'):
            with self.subTest(valid=value):
                catalogs, model = self.candidate()
                model['curation_date'] = value
                self.accept(catalogs)

    def test_synthetic_identity_rejects_real_material_and_temper_metadata(self):
        for field, values in (
            ('UNS', ('A00000', '', False, 0, [])),
            ('temper', ('TEST', '', False, 0, [])),
            ('temper_status', ('specified', 'not specified', None, True)),
            ('identity_status', ('real_material', '', None, True)),
        ):
            for value in values:
                with self.subTest(field=field,value=value):
                    catalogs, model = self.candidate()
                    model['material'][field] = value
                    self.assertTrue(list(self.schema_validator.iter_errors(catalogs['temperature_models'])))
                    self.reject(catalogs)

    def test_all_unknown_condition_values_must_be_exact_null(self):
        for field in UNKNOWN_FIELDS:
            for value in (False, 0, '', 'unknown', [], {}):
                with self.subTest(field=field, value=value):
                    self.reject_value(('unknown_conditions', field, 'value'), value)

    def test_review_and_retrieval_flags_reject_forged_status_and_boolean_aliases(self):
        flags = [(('verification', field), value) for field, value in VERIFICATION_FLAGS.items()]
        flags += [(('author_provenance', field), False) for field in ('is_empirical','derived_from_measurements')]
        flags += [((*FIT, field), False) for field in FIT_FLAGS]
        for path, expected in flags:
            for value in (not expected, int(expected), float(expected), None, str(expected).lower(), [], {}):
                with self.subTest(field=path, value=value):
                    self.reject_value(path, value)

    def test_fixed_scientific_contract_fields_cannot_be_reinterpreted(self):
        fields = ('version', 'classification', 'evaluation_support', 'equation_family', 'quantity',
                  'input_unit', 'output_unit', 'equation_display', 'coefficient_order',
                  'coefficient_units', 'overlap_policy')
        for field in fields:
            for value in ('unsupported', None, True):
                with self.subTest(field=field, value=value):
                    self.reject_value((field,), value)
        for path, values in (
            ((*BRANCH, 'endpoints'), ('exclusive', None, True)),
            ((*FIT, 'unit'), ('percent', '', True)),
            ((*FIT, 'status'), ('empirical', None, True)),
            ((*BRANCH, 'range_status'), ('measured_interval', None, True)),
            (('author_provenance', 'creation_method'), ('source_transcription', None, True)),
            ((*FIT, 'statistic'), ('maximum', False, 0)),
            ((*FIT, 'confidence_level'), (0.95, False, 0)),
            ((*FIT, 'value'), (-1, 0, 1, True, False, '1', float('nan'), float('inf'), 10**400)),
        ):
            for value in values:
                with self.subTest(field=path, value=value):
                    self.reject_value(path, value)

    def test_branch_arrays_ranges_and_coefficients_remain_closed(self):
        for value in ([], None, {}, True, 'branches'):
            with self.subTest(branches=value):
                self.reject_value(('branches',), value)
        catalogs, model = self.candidate()
        model['branches'] = [copy.deepcopy(model['branches'][0]) for _ in range(21)]
        for index, branch in enumerate(model['branches']):
            branch['id'] = f'synthetic_too_many_{index}'
        self.reject(catalogs)
        for field in ('equation_range_K',):
            for value in (None, True, '1,2', [], [1], [1, 2, 3], [2, 1], [1, 1], [-1, 2],
                          [True, 2], [False, 2], ['1', 2], [1, float('inf')], [1, float('nan')],
                          [1, 10**400]):
                with self.subTest(field=field, value=value):
                    self.reject_value((*BRANCH, field), value)
        self.reject_value((*BRANCH, 'equation_range_K'), [0, 2])
        for value in ([1,2], [], False, 0, 'no data'):
            self.reject_value((*BRANCH, 'source_data_range_K'), value)
        for value in (None, True, '1,2,3,4,5', [], ['1'] * 4, ['1'] * 6):
            with self.subTest(coefficients=value):
                self.reject_value((*BRANCH, 'coefficients_text'), value)
        for value in ('', ' ', '1\n', ' 1', 'NaN', 'Infinity', '1e9999', '1e-9999',
                      '1_000', '0x10', '1/2', '1,2', True, 1, None):
            with self.subTest(coefficient=value):
                self.reject_value((*BRANCH, 'coefficients_text', 0), value)

    def test_synthetic_metadata_cannot_silently_gain_empirical_provenance(self):
        for key, value in (
            ('original_reference', {'title':'invented source'}),
            ('reference_chart_retrieved', False),
        ):
            catalogs, model = self.candidate()
            model[key] = value
            self.reject(catalogs)
        for field in UNKNOWN_FIELDS:
            self.reject_value(('unknown_conditions',field,'status'),'measured or unknown')
        catalogs, model = self.candidate()
        model['verification']['source_equation_checked']=True
        self.reject(catalogs)

    def test_flexible_authored_metadata_and_fresh_supported_quartic_are_accepted(self):
        catalogs, model = self.candidate()
        appended = copy.deepcopy(model)
        appended['id'] = 'synthetic_temperature_metadata_append'
        appended['name'] = 'SYNTHETIC metadata and appendability check only'
        appended['descriptions'] = {lang: f'{lang}: Synthetic polynomial, not scientific evidence.' for lang in ('en','zh','ja','de')}
        appended['material']['name'] = 'Synthetic material label'
        appended['branches'] = [copy.deepcopy(model['branches'][0])]
        branch = appended['branches'][0]
        branch['id'] = 'synthetic_temperature_metadata_branch'
        # 100 + (T-2)^4: positive but decreasing then increasing.
        branch['coefficients_text'] = ['116','-32','24','-8','1']
        branch['equation_range_K'] = [1,3]
        appended['author_provenance']['author'] = 'Authored synthetic fixture contributors'
        appended['verification']['translation_review'] = 'Synthetic wording; translations have not been reviewed.'
        appended['reuse'] = {'status':'Original synthetic metadata',
                             'caveats':['For plumbing tests only'], 'recommended_attribution':'Synthetic test fixture'}
        appended['source_locator'] = 'Synthetic construction locator'
        appended['scope_exclusions'] = ['No real-material inference']
        appended['range_interpretation'] = 'Artificial interval is retained exactly as supplied.'
        appended['curation_date'] = '2024-02-29'
        catalogs['temperature_models']['records'].append(appended)
        self.accept(catalogs)
        with patch('materials_boundaries.temperature.read_catalog', side_effect=lambda name:copy.deepcopy(catalogs[name])):
            for temperature, expected in ((1,101),(2,100),(3,101)):
                result=evaluate_temperature({'schema_version':'1.0.0','model_id':appended['id'],
                                             'temperature':{'value':temperature,'unit':'K'}})
                self.assertEqual(result['status'],'prediction')
                self.assertEqual(result['predictions'][0]['value'],expected)
                self.assertEqual(result['model_snapshot'],appended)

    def test_empirical_contract_remains_separately_appendable_without_bundled_source_data(self):
        # Wholly artificial metadata exercises the existing external-contribution
        # structure. It is not accepted as empirical evidence by this test.
        catalogs, model = self.candidate()
        appended=copy.deepcopy(model)
        appended['id']='artificial_empirical_contract_fixture'
        appended['classification']='empirical_fit_prediction'
        appended['material']={'name':'ARTIFICIAL contract fixture','UNS':'ARTIFICIAL',
                              'temper':'TEST','temper_status':'specified'}
        del appended['author_provenance']
        fields=('title','editor','institution','edition','chart','reference_list_locator')
        appended['original_reference']={field:'Artificial '+field for field in fields}
        appended['original_reference']['reference_chart_retrieved']=False
        appended['verification']={'source_equation_checked':True,'synthetic_arithmetic_checked':True,
                                   'independent_scientific_review':False,'original_charts_retrieved':False,
                                   'translation_review':'Artificial contract fixture only'}
        branch=appended['branches'][0]
        branch['id']='artificial_empirical_contract_branch'
        del branch['range_status']
        branch['source_data_range_K']=[5,95]
        branch['equation_range_K']=[10,100]
        fit=branch['reported_fit_error'];del fit['status']
        fit['value']=0.25;fit['unit']='percent_relative_to_source_data'
        for condition in appended['unknown_conditions'].values():
            condition['status']='Not supplied by artificial contract fixture'
        catalogs['temperature_models']['records'].append(appended)
        self.accept(catalogs)
        # Source-data ranges do not license extrapolation or bound equation ranges.
        with patch('materials_boundaries.temperature.read_catalog',side_effect=lambda name:copy.deepcopy(catalogs[name])):
            for temperature,status in ((5,'out_of_range'),(10,'prediction'),(100,'prediction'),(101,'out_of_range')):
                self.assertEqual(evaluate_temperature({'schema_version':'1.0.0','model_id':appended['id'],
                    'temperature':{'value':temperature,'unit':'K'}})['status'],status)
        appended['material']['temper']=None
        appended['material']['temper_status']='not specified'
        appended['original_reference']['source_date_annotation']='Artificial date annotation, 2026-10-02'
        self.accept(catalogs)

    def test_runtime_metadata_validation_needs_no_development_dependencies(self):
        code = '''
import sys
from materials_boundaries.catalog import read_catalog
from materials_boundaries.temperature import TemperatureError, validate_model_catalog
catalog = read_catalog('temperature_models')
validate_model_catalog(catalog)
catalog['records'][0]['verification']['independent_scientific_review'] = 0
try:
    validate_model_catalog(catalog)
except TemperatureError:
    pass
else:
    raise AssertionError('numeric boolean alias was accepted')
assert 'jsonschema' not in sys.modules
assert 'referencing' not in sys.modules
'''
        result = subprocess.run([sys.executable, '-S', '-c', code], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
