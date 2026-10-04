"""Generic source-uncertainty metadata gates; fictional fixtures are not data.

These tests validate declared metadata, not the truth of arbitrary source prose.
Real-source curation and independent source review are separate acceptance gates.
"""
from copy import deepcopy
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from materials_boundaries.material_references import (
    _PROPERTIES_SCHEMA, validate_material_catalog,
)
from materials_boundaries.material_presentation import render_material_catalog, material_labels
from test_material_reference_contract import synthetic_mean_catalog, synthetic_material_catalog

ROOT = Path(__file__).resolve().parents[1]


def uncertainty_catalog(kind='reported_confidence_interval'):
    graph = synthetic_mean_catalog()
    p = graph[1]['records'][0]
    p.update(summary_statistic='reported_value', uncertainty_status=kind,
             basis_note='Fictional central result; arithmetic-mean aggregation is unspecified.')
    p['reported_value'].update(value_text='2.05', number='2.05')
    p['uncertainty'].update(type=kind, value_text='0.12', number='0.12',
        scope='Reported symmetric amplitude; statistical construction is unspecified.')
    p['uncertainty_note'] = 'Synthetic 2.05 ± 0.12 MPa; do not infer SD, SE or arithmetic-mean aggregation.'
    if kind == 'reported_confidence_interval':
        p['uncertainty']['confidence_level'] = {'value_text':'95%', 'number':'95', 'unit_code':'percent'}
        for key in ('estimand','construction'):
            p['uncertainty'][key] = {'status':'not_reported_in_inspected_source',
                'text':None,'evidence':[], 'notes':'This synthetic source does not specify the CI ' + key + '.'}
    p['sample_count'].update(value=6,scope='Six fictional test samples; not an established CI estimand.',
        source_statement='Data from six samples were averaged; fit/averaging order is unspecified.')
    p['method_definition']['extraction_window'] = {'status':'reported','text':'Source linear region below 40% strain',
        'evidence':deepcopy(p['method_definition']['evidence']),
        'notes':'No exact lower endpoint or fitting algorithm is specified.'}
    return graph


class MaterialUncertaintyContractTests(unittest.TestCase):
    def assert_invalid(self, mutation, kind='reported_confidence_interval'):
        graph = uncertainty_catalog(kind)
        mutation(graph[1]['records'][0])
        with self.assertRaises(ValueError):
            validate_material_catalog(*graph)

    def test_closed_schema_generation_and_existing_sd_contract(self):
        import jsonschema
        self.assertEqual(json.loads((ROOT/'schemas/reference_properties.schema.json').read_text()),_PROPERTIES_SCHEMA)
        jsonschema.Draft202012Validator.check_schema(_PROPERTIES_SCHEMA)
        for make in (synthetic_material_catalog, synthetic_mean_catalog, uncertainty_catalog,
                     lambda:uncertainty_catalog('reported_plus_minus_unspecified')):
            graph=make(); before=deepcopy(graph)
            validate_material_catalog(*graph)
            jsonschema.Draft202012Validator(_PROPERTIES_SCHEMA).validate(graph[1])
            self.assertEqual(graph,before)

    def test_ci_accepts_reported_value_without_mean_and_preserves_unknowns(self):
        graph=uncertainty_catalog();validate_material_catalog(*graph)
        p=graph[1]['records'][0]
        self.assertEqual(p['summary_statistic'],'reported_value')
        self.assertEqual(p['uncertainty']['confidence_level']['number'],'95')
        for key in ('estimand','construction'):
            self.assertIsNone(p['uncertainty'][key]['text'])
            self.assertEqual(p['uncertainty'][key]['status'],'not_reported_in_inspected_source')
        self.assertEqual(json.loads(json.dumps(graph)),list(graph))

    def test_all_numerical_status_type_pairings_are_exact(self):
        kinds=('reported_confidence_interval','reported_plus_minus_unspecified','reported_standard_deviation')
        for kind in kinds[:2]:
            for status in (*kinds,'not_reported_in_inspected_source','not_applicable'):
                if status != kind:
                    with self.subTest(kind=kind,status=status):
                        self.assert_invalid(lambda p:p.update(uncertainty_status=status),kind)
            self.assert_invalid(lambda p:p.update(uncertainty=None),kind)
            self.assert_invalid(lambda p:p['uncertainty'].update(type='unknown_plus_minus'),kind)

    def test_malformed_ci_level_and_unknown_fields_are_rejected(self):
        bad_levels=(None,{}, {'value_text':'95%','number':95,'unit_code':'percent'},
            {'value_text':'95%','number':True,'unit_code':'percent'},
            {'value_text':'95%','number':'95','unit_code':'1'},
            {'value_text':'95%','number':'95','unit_code':'percent','extra':None})
        for level in bad_levels:
            with self.subTest(level=level): self.assert_invalid(lambda p:p['uncertainty'].update(confidence_level=level))
        self.assert_invalid(lambda p:p['uncertainty'].pop('confidence_level'))
        for number in ('0','100','101','NaN','Infinity','-1','9.5e1'):
            self.assert_invalid(lambda p:p['uncertainty']['confidence_level'].update(number=number,value_text=number+'%'))
        for text in ('95','0.95','0.95%','95.0%','95 percent','95% CI','95 ± 1%','+95%','95%\n'):
            self.assert_invalid(lambda p:p['uncertainty']['confidence_level'].update(value_text=text))
        for key in ('estimand','construction'):
            self.assert_invalid(lambda p:p['uncertainty'].pop(key))
            self.assert_invalid(lambda p:p['uncertainty'][key].update(notes=None))
            self.assert_invalid(lambda p:p['uncertainty'][key].update(status='not_applicable'))
        self.assert_invalid(lambda p:p['uncertainty'].update(coverage_factor='1.96'))

    def test_exact_decimal_confidence_level_does_not_round_through_float(self):
        for number in ('0.000000000000000000000001','99.999999999999999999999999','95.00'):
            graph=uncertainty_catalog();p=graph[1]['records'][0]
            p['uncertainty']['confidence_level'].update(number=number,value_text=number+'%')
            validate_material_catalog(*graph)
            self.assertEqual(p['uncertainty']['confidence_level']['number'],number)

    def test_uncertainty_amplitude_units_and_evidence_are_preserved(self):
        for kind in ('reported_confidence_interval','reported_plus_minus_unspecified'):
            for number in ('-0.12','NaN','Infinity','-Infinity','1e-2',0.12,True):
                self.assert_invalid(lambda p:p['uncertainty'].update(number=number),kind)
            for text in ('0.120','±0.12','0.12 (unknown)','0.12 SD','0.12%'):
                self.assert_invalid(lambda p:p['uncertainty'].update(value_text=text),kind)
            for unit in ('GPa','g/cm^3'):
                self.assert_invalid(lambda p:p['uncertainty'].update(unit_code=unit,unit_text=unit),kind)
            self.assert_invalid(lambda p:p['uncertainty'].update(evidence=[]),kind)
            self.assert_invalid(lambda p:p['uncertainty']['evidence'][0].update(supports=['reported_value']),kind)
            self.assert_invalid(lambda p:p['reported_value'].update(kind='comparison',operator='>',value_text='>2.05'),kind)
            graph=uncertainty_catalog(kind);graph[1]['records'][0]['uncertainty'].update(number='0.00',value_text='0.00')
            validate_material_catalog(*graph)

    def test_unknown_plus_minus_cannot_gain_ci_or_sd_semantics(self):
        kind='reported_plus_minus_unspecified'
        self.assert_invalid(lambda p:p['uncertainty'].update(confidence_level={'value_text':'95%','number':'95','unit_code':'percent'}),kind)
        self.assert_invalid(lambda p:p['uncertainty'].update(coverage_factor='2'),kind)
        self.assert_invalid(lambda p:p['uncertainty'].update(estimand={'status':'reported','text':'mean','evidence':[],'notes':None}),kind)
        def relabel_sd(p):
            p['uncertainty']['type']='reported_standard_deviation'
            p['uncertainty_status']='reported_standard_deviation'
        self.assert_invalid(relabel_sd,kind)

    def test_ci_reported_estimand_and_construction_need_primary_uncertainty_evidence(self):
        for key in ('estimand','construction'):
            graph=uncertainty_catalog();p=graph[1]['records'][0]
            p['uncertainty'][key]={'status':'reported','text':'Explicit fictional source-defined '+key,
                'evidence':deepcopy(p['uncertainty']['evidence']),'notes':None}
            validate_material_catalog(*graph)
            p['uncertainty'][key]['evidence'][0]['supports']=['method']
            with self.assertRaises(ValueError):validate_material_catalog(*graph)

    def test_extraction_window_is_evidence_backed_text_not_executable_fit(self):
        for text in ('0.1 to 0.6% strain','linear region below 40% strain'):
            graph=uncertainty_catalog();p=graph[1]['records'][0]
            p['method_definition']['extraction_window']['text']=text
            validate_material_catalog(*graph)
            self.assertEqual(p['method_definition']['extraction_window']['text'],text)
        self.assert_invalid(lambda p:p['method_definition']['extraction_window'].update(evidence=[]))
        self.assert_invalid(lambda p:p['method_definition']['extraction_window']['evidence'][0].update(supports=['condition']))
        self.assert_invalid(lambda p:p['method_definition']['extraction_window'].update(lower=0))
        self.assert_invalid(lambda p:p['method_definition'].update(extraction_window='0–40%'))
        self.assert_invalid(lambda p:p['method_definition']['extraction_window'].update(status='not_reported_in_inspected_source'))
        graph=uncertainty_catalog();graph[1]['records'][0]['method_definition']['extraction_window']=None
        validate_material_catalog(*graph)

    def test_all_languages_show_kind_level_unknowns_source_expression_and_window(self):
        for kind in ('reported_confidence_interval','reported_plus_minus_unspecified'):
            graph=uncertainty_catalog(kind)
            for lang in ('en','zh','ja','de'):
                labels=material_labels(lang)
                with patch('materials_boundaries.material_presentation._resolved_graph',return_value=graph):
                    text=render_material_catalog(graph[1],'reference-properties',lang)
                label='confidence_interval' if kind=='reported_confidence_interval' else 'plus_minus_unspecified'
                self.assertIn(labels[label]+': 0.12 MPa',text)
                self.assertNotIn(labels['standard_deviation']+':',text)
                self.assertNotIn(labels['statistics_notice'],text)
                self.assertIn(labels['reported_uncertainty_notice'],text)
                self.assertIn('2.05 ± 0.12 MPa',text)
                self.assertIn('below 40% strain',text)
                self.assertIn('Six fictional test samples',text)
                if kind=='reported_confidence_interval':
                    self.assertIn(labels['confidence_level']+': 95%',text)
                    for key in ('estimand','construction'):
                        self.assertIn(labels[key]+': '+labels['unknown'],text)
