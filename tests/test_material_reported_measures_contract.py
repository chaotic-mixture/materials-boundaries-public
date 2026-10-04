"""Generic measure metadata tests use fictional sources, never material allowlists.

The shared fixture maker supports future-ID/rehearsal tests. Metadata validation
cannot establish scientific source truth or the fidelity of authored explanations.
"""
from contextlib import redirect_stdout
from copy import deepcopy
import io
import json
from pathlib import Path
import unittest

import jsonschema

from materials_boundaries.cli import main
from materials_boundaries.material_presentation import material_labels
from materials_boundaries.material_references import (
    _PROPERTIES_SCHEMA, _shape, material_coverage, resolve_material,
    validate_material_catalog,
)
from test_material_catalog_views import fixture_catalogs
from test_material_reference_contract import synthetic_material_catalog, synthetic_mean_catalog

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ('cv', 'graphical_sd', 'unnamed_center_sd', 'relative_errors', 'scientific_notation')


def synthetic_reported_measures_catalog(example='cv'):
    """Return detached (materials, properties, sources), all explicitly fictional.

    Examples: cv, graphical_sd, unnamed_center_sd, relative_errors (two separate
    relative SEM/inaccuracy descriptors), scientific_notation (unknown uncertainty).
    """
    if example not in EXAMPLES:
        raise ValueError('unknown synthetic measure example: ' + example)
    if example == 'scientific_notation':
        graph = synthetic_material_catalog()
        graph[1]['records'][0]['reported_value'].update(
            number='12340', value_text='12.34 × 10^3', unit_code='kg/m^3', unit_text='kg m−3')
        return graph
    graph = synthetic_mean_catalog()
    prop = graph[1]['records'][0]
    prop['uncertainty_status'] = 'reported_measures'
    prop['uncertainty_note'] = 'Fictional separately typed source measures; no calculation or conversion.'
    evidence = deepcopy(prop['uncertainty']['evidence'])
    evidence[0]['locator'] = ('Synthetic Figure 4b caption, control SD bars' if example == 'graphical_sd'
                              else 'Synthetic test table 2, row SYN-A, reported measure columns')
    prop['evidence'].extend(deepcopy(evidence))

    def measure(kind, number, qualifier='not_qualified_in_source'):
        absolute = kind == 'standard_deviation'
        return {
            'kind': kind, 'availability': 'numeric_reported',
            'basis': 'absolute' if absolute else 'relative_to_reported_value',
            'reported_value': {'number': number, 'value_text': number,
                               'unit_code': 'MPa' if absolute else 'percent',
                               'unit_text': 'MPa' if absolute else '%'},
            'qualifier': qualifier, 'scope': 'Fictional five-test group; selected source descriptor only.',
            'evidence': deepcopy(evidence), 'confidence_level': None, 'coverage_factor': None, 'note': None,
        }

    if example == 'cv':
        measures = [measure('coefficient_of_variation', '56.12')]
    elif example == 'relative_errors':
        measures = [measure('standard_error_of_mean', '0.02'),
                    measure('estimated_inaccuracy', '0.1', 'approximately')]
    else:
        measures = [measure('standard_deviation', '23')]
        if example == 'graphical_sd':
            measures[0].update(availability='graphical_only', reported_value=None,
                               note='Source labels Figure 4b bars as SD; no numerical amplitude was transcribed or digitized.')
        else:
            prop['summary_statistic'] = 'not_stated'
            prop['basis_note'] = 'Source does not identify the aggregation of the central result.'
            prop['evidence'][0]['supports'].remove('summary_statistic')
            measures[0]['note'] = 'Source identifies SD, but the central aggregation is unnamed; no mean is inferred.'
    prop['uncertainty'] = {'type': 'reported_measures', 'measures': measures}
    return graph


class MaterialReportedMeasuresContractTests(unittest.TestCase):
    def assert_invalid(self, mutation, example='cv', structural=False):
        graph = synthetic_reported_measures_catalog(example)
        mutation(graph[1]['records'][0])
        if structural:
            # The dependency-free shape interpreter and the checked-in JSON
            # Schema agree; graph/lexical cross-field rules remain runtime gates.
            with self.assertRaises(jsonschema.ValidationError):
                jsonschema.Draft202012Validator(_PROPERTIES_SCHEMA).validate(graph[1])
            with self.assertRaises(ValueError):
                _shape(graph[1], _PROPERTIES_SCHEMA, _PROPERTIES_SCHEMA, 'properties')
        before = deepcopy(graph)
        with self.assertRaises(ValueError):
            validate_material_catalog(*graph)
        self.assertEqual(graph, before)

    def test_all_five_generic_examples_schema_runtime_and_exact_json_round_trip(self):
        stored = json.loads((ROOT / 'schemas/reference_properties.schema.json').read_text())
        self.assertEqual(stored, _PROPERTIES_SCHEMA)
        jsonschema.Draft202012Validator.check_schema(stored)
        for example in EXAMPLES:
            with self.subTest(example=example):
                graph = synthetic_reported_measures_catalog(example)
                before = deepcopy(graph)
                jsonschema.Draft202012Validator(stored, format_checker=jsonschema.FormatChecker()).validate(graph[1])
                _shape(graph[1], stored, stored, 'properties')
                validate_material_catalog(*graph)
                view = resolve_material(graph[0]['records'][0]['id'], *graph)
                self.assertEqual(view['properties'], graph[1]['records'])
                self.assertEqual(json.loads(json.dumps(graph, ensure_ascii=False)), list(graph))
                self.assertEqual(graph, before)

    def test_closed_measure_envelope_and_mandatory_nullable_fields(self):
        for key in ('kind', 'availability', 'basis', 'reported_value', 'qualifier', 'scope',
                    'evidence', 'confidence_level', 'coverage_factor', 'note'):
            self.assert_invalid(lambda p: p['uncertainty']['measures'][0].pop(key), structural=True)
        for value in ([], None, {}, [{'type': 'reported_measures', 'measures': []}]):
            self.assert_invalid(lambda p: p['uncertainty'].update(measures=value), structural=True)
        self.assert_invalid(lambda p: p['uncertainty'].update(number='1'), structural=True)
        self.assert_invalid(lambda p: p['uncertainty']['measures'][0].update(formula='CV * mean'), structural=True)
        self.assert_invalid(lambda p: p['uncertainty']['measures'][0]['reported_value'].update(kind='scalar'), structural=True)

    def test_envelope_status_scalar_and_independent_mean_requirements(self):
        for status in ('reported_standard_deviation', 'reported_confidence_interval',
                       'reported_plus_minus_unspecified', 'not_reported_in_inspected_source', 'not_applicable'):
            self.assert_invalid(lambda p: p.update(uncertainty_status=status))
        self.assert_invalid(lambda p: p.update(uncertainty=None))
        self.assert_invalid(lambda p: p['reported_value'].update(kind='comparison', operator='>', value_text='>2500'))
        for example in ('cv', 'graphical_sd', 'relative_errors'):
            self.assert_invalid(lambda p: p['evidence'][0]['supports'].remove('summary_statistic'), example)
        for summary in ('not_stated', 'reported_value'):
            self.assert_invalid(lambda p: p.update(summary_statistic=summary), 'relative_errors')
        for summary in ('not_stated', 'reported_value'):
            graph = synthetic_reported_measures_catalog('unnamed_center_sd')
            graph[1]['records'][0]['summary_statistic'] = summary
            validate_material_catalog(*graph)
        self.assert_invalid(lambda p: p['uncertainty']['measures'][0].update(note=None), 'unnamed_center_sd')
        # The legacy SD branch still independently requires explicit mean metadata.
        graph = synthetic_mean_catalog()
        graph[1]['records'][0]['summary_statistic'] = 'not_stated'
        with self.assertRaises(ValueError):
            validate_material_catalog(*graph)

    def test_numeric_measures_are_typed_and_never_converted(self):
        for example in ('cv', 'relative_errors'):
            self.assert_invalid(lambda p: p['uncertainty']['measures'][0].update(basis='absolute'), example, structural=True)
            self.assert_invalid(lambda p: p['uncertainty']['measures'][0]['reported_value'].update(unit_code='MPa', unit_text='MPa'), example, structural=True)
            self.assert_invalid(lambda p: p['uncertainty']['measures'][0].update(kind='standard_deviation'), example, structural=True)
        self.assert_invalid(lambda p: p['uncertainty']['measures'][0]['reported_value'].update(unit_code='GPa', unit_text='GPa'), 'unnamed_center_sd')
        self.assert_invalid(lambda p: p['uncertainty']['measures'][0].update(basis='relative_to_reported_value'), 'unnamed_center_sd', structural=True)
        for example in ('cv', 'scientific_notation'):
            self.assert_invalid(lambda p: p['reported_value'].update(unit_code='percent', unit_text='%'), example, structural=True)
        self.assert_invalid(lambda p: p['uncertainty']['measures'][0]['reported_value'].update(unit_text='percent'))
        self.assert_invalid(lambda p: p['uncertainty']['measures'][0]['reported_value'].update(value_text='56.12%'))
        # Neither CV nor other relative measures receive an invented 100% cap.
        for number in ('0.00', '156.120', '999999999999999999999999.999999999999999999999999'):
            graph = synthetic_reported_measures_catalog()
            graph[1]['records'][0]['uncertainty']['measures'][0]['reported_value'].update(number=number, value_text=number)
            validate_material_catalog(*graph)

    def test_graphical_sd_requires_null_amplitude_and_specific_figure_evidence(self):
        for value in ({'number': '0', 'value_text': '0', 'unit_text': 'MPa', 'unit_code': 'MPa'},
                      '0', '', 0):
            self.assert_invalid(lambda p: p['uncertainty']['measures'][0].update(reported_value=value), 'graphical_sd', structural=True)
        self.assert_invalid(lambda p: p['uncertainty']['measures'][0].update(reported_value=None), structural=True)
        self.assert_invalid(lambda p: p['uncertainty']['measures'][0].update(availability='graphical_only'), structural=True)
        self.assert_invalid(lambda p: p['uncertainty']['measures'][0].update(note=None), 'graphical_sd', structural=True)
        self.assert_invalid(lambda p: p['uncertainty']['measures'][0].update(kind='coefficient_of_variation'), 'graphical_sd', structural=True)
        for locator in ('Synthetic table 2, SD column', 'Synthetic Figure caption', 'Synthetic Figure'):
            def mutate(p):
                p['uncertainty']['measures'][0]['evidence'][0]['locator'] = locator
                p['evidence'][-1]['locator'] = locator
            self.assert_invalid(mutate, 'graphical_sd')

    def test_measure_evidence_requires_primary_source_and_exact_linked_locator(self):
        self.assert_invalid(lambda p: p['uncertainty']['measures'][0].update(evidence=[]), structural=True)
        for field, value in (('source_id', 'other_source'), ('url', 'https://example.invalid/other.pdf'),
                             ('locator', 'Synthetic table 9, unrelated cell'), ('supports', ['reported_value'])):
            self.assert_invalid(lambda p: p['uncertainty']['measures'][0]['evidence'][0].update({field: value}))
        self.assert_invalid(lambda p: p['evidence'].pop())
        self.assert_invalid(lambda p: p['evidence'][-1].update(supports=['classification']))
        def registered_but_secondary(p):
            p['uncertainty']['measures'][0]['evidence'][0]['source_id'] = 'synthetic_secondary'
            p['evidence'][-1]['source_id'] = 'synthetic_secondary'
        graph = synthetic_reported_measures_catalog()
        source = deepcopy(graph[2]['records'][0]); source['id'] = 'synthetic_secondary'
        graph[2]['records'].append(source)
        registered_but_secondary(graph[1]['records'][0])
        with self.assertRaises(ValueError):
            validate_material_catalog(*graph)

    def test_duplicate_descriptors_rejected_but_equal_distinct_kinds_preserved(self):
        self.assert_invalid(lambda p: p['uncertainty']['measures'].append(deepcopy(p['uncertainty']['measures'][0])), structural=True)
        def same_descriptor_new_number(p):
            duplicate = deepcopy(p['uncertainty']['measures'][0])
            duplicate['reported_value'].update(number='99', value_text='99')
            duplicate['qualifier'] = 'approximately'
            p['uncertainty']['measures'].append(duplicate)
        self.assert_invalid(same_descriptor_new_number)
        graph = synthetic_reported_measures_catalog('relative_errors')
        measures = graph[1]['records'][0]['uncertainty']['measures']
        measures[1]['reported_value'].update(number='0.02', value_text='0.02')
        before = deepcopy(measures)
        validate_material_catalog(*graph)
        self.assertEqual(measures, before)
        self.assertEqual(len(measures), 2)
        self.assertEqual(material_coverage(graph[0], graph[1])['property_record_count'], 1)

    def test_qualifiers_confidence_coverage_and_unsafe_metadata_are_closed(self):
        for field, value in (('qualifier', None), ('qualifier', 'exact'), ('confidence_level', '95'),
                             ('confidence_level', {'number': '95', 'value_text': '95%','unit_code': 'percent'}),
                             ('coverage_factor', '2'), ('coverage_factor', 2)):
            self.assert_invalid(lambda p: p['uncertainty']['measures'][0].update({field: value}), structural=True)
        for field in ('scope', 'note'):
            for value in ('', '   ', 'injected\nline', '\x1b[31m', '\ud800'):
                self.assert_invalid(lambda p: p['uncertainty']['measures'][0].update({field: value}), structural=True)
        for number in ('NaN', 'Infinity', '-Infinity', '-1', '-0', '+1', '1e2', '01',
                       '1' * 25, '0.' + '1' * 25, '1\n', 1, True, None):
            self.assert_invalid(lambda p: p['uncertainty']['measures'][0]['reported_value'].update(number=number), structural=True)
        for text in ('56.120', '56,1200', '±56.12', '~56.12', '56.12 SD'):
            self.assert_invalid(lambda p: p['uncertainty']['measures'][0]['reported_value'].update(value_text=text))

    def test_four_language_cli_text_and_json_preserve_distinct_measures(self):
        for example in EXAMPLES:
            graph = synthetic_reported_measures_catalog(example)
            docs = dict(zip(('materials', 'reference_properties', 'sources'), graph))
            prop = graph[1]['records'][0]
            for language in ('en', 'zh', 'ja', 'de'):
                with self.subTest(example=example, language=language), fixture_catalogs(docs):
                    labels = material_labels(language)
                    output = io.StringIO()
                    with redirect_stdout(output):
                        self.assertEqual(main(['catalog', 'reference-properties', '--text', '--lang', language]), 0)
                    text = output.getvalue()
                    self.assertIn(prop['reported_value']['value_text'], text)
                    if prop['uncertainty'] is not None:
                        self.assertIn(labels['reported_measures_notice'], text)
                        self.assertNotIn(labels['statistics_notice'], text)
                        self.assertNotIn(labels['reported_uncertainty_notice'], text)
                        for measure in prop['uncertainty']['measures']:
                            self.assertIn(labels[measure['kind']] + ':', text)
                            self.assertIn(labels['code_' + measure['qualifier']], text)
                            self.assertIn(labels['code_' + measure['basis']], text)
                            self.assertIn(measure['evidence'][0]['locator'], text)
                        self.assertNotIn('±', text)
                    if example == 'graphical_sd':
                        self.assertIn(labels['graphical_amplitude_unavailable'], text)
                    if example == 'unnamed_center_sd':
                        self.assertIn(labels['central_aggregation_unknown_notice'], text)
                    output = io.StringIO()
                    with redirect_stdout(output):
                        self.assertEqual(main(['catalog', 'reference-properties', '--lang', language, '--json']), 0)
                    self.assertEqual(json.loads(output.getvalue()), graph[1])

    def test_generic_future_append_preserves_identity_count_not_component_count(self):
        first = synthetic_reported_measures_catalog('relative_errors')
        second = synthetic_reported_measures_catalog('graphical_sd')
        # Rename linked IDs and source-scoped facts, never introduce an ID allowlist.
        def rename(value):
            if isinstance(value, dict):
                return {key: rename(item) for key, item in value.items()}
            if isinstance(value, list):
                return [rename(item) for item in value]
            return value.replace('synthetic_a', 'future_generic_b').replace('SYN-A', 'SYN-B') if isinstance(value, str) else value
        second = rename(list(second))
        second[0]['identities'][0]['identity_scope'] += ' Distinct fictional future identity.'
        for key in ('identities', 'grades', 'records'):
            first[0][key].extend(second[0][key])
        first[1]['records'].extend(second[1]['records'])
        validate_material_catalog(*first)
        counts = material_coverage(first[0], first[1])
        self.assertEqual(counts['material_identity_count'], 2)
        self.assertEqual(counts['material_state_count'], 2)
        self.assertEqual(counts['property_record_count'], 2)
        self.assertEqual(sum(len(p['uncertainty']['measures']) for p in first[1]['records']), 3)
