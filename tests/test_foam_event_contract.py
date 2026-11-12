"""Fictional source-qualified foam process events, without shared-clock inference."""
from copy import deepcopy
from decimal import localcontext
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from jsonschema import Draft202012Validator
from materials_boundaries.database import Database, read_snapshot
from materials_boundaries.material_references import _PROPERTIES_SCHEMA, resolve_material, validate_material_catalog
from materials_boundaries.material_presentation import material_labels, render_material_catalog
from test_material_reference_contract import synthetic_mean_catalog
from test_material_uncertainty_contract import uncertainty_catalog
from test_material_reported_measures_contract import synthetic_reported_measures_catalog
from test_tga_endpoint_contract import add_clone

ROOT = Path(__file__).resolve().parents[1]
QUANTITY = 'foam_reaction_event_time'
FACTS = ('clock_origin', 'endpoint_criterion', 'apparatus_or_observation_method', 'mixing_reference',
         'reaction_test_geometry_charge', 'reaction_test_environment', 'replicate_and_piece_relationship')


def as_foam_event(graph):
    prop = graph[1]['records'][0]
    prop.update(quantity=QUANTITY, quantity_dimension='time', density_basis=None,
                source_property_label='Fictional foam process event time')
    prop['reported_value'].update(number='12.50', value_text='12.50', unit_code='s', unit_text='s')
    prop['conditions']['direction'] = dict(status='not_reported_in_inspected_source',text=None,evidence=[],notes='Orientation and sample location not stated; a process scalar does not establish orientation or specimen linkage.')
    prop['method_definition'].update(type='source_reported_conventional', extraction_window=None)
    prop.pop('derivation', None)
    value_evidence=deepcopy([e for e in prop['evidence'] if 'reported_value' in e['supports'] and e['url']==prop['source_document']['url']])
    for e in value_evidence:e['supports']=sorted(set(e['supports'])|{'classification'})
    prop['reaction_event']=dict(code='foaming_start',evidence=value_evidence,notes='Fictional source-labelled start observation; no clock origin assumed.')
    state_evidence=deepcopy(value_evidence)
    for e in state_evidence:e['supports']=['state']
    graph[0]['records'][0]['state']['product_form']=dict(status='reported',text='Fictional reacting mixture during foam process observation; not a cured-specimen property.',evidence=state_evidence,notes='Fictional process context only.')
    evidence = deepcopy(prop['method_definition']['evidence'])
    for entry in evidence:
        entry['supports'] = ['method', 'condition']
    unknown = dict(status='not_verified', text=None, evidence=deepcopy(evidence),
                   notes='Fictional source does not establish this process-event fact.')
    prop['reaction_time_definition'] = dict(basis='source_reported_process_event_time',
        **{name: deepcopy(unknown) for name in FACTS}, evidence=evidence,
        notes='Fictional process observation; clock origin and relationships are not inferred.')
    return graph


def fixture():
    graph = as_foam_event(synthetic_mean_catalog())
    graph[1]['records'][0].update(uncertainty=None, uncertainty_status='not_reported_in_inspected_source',
                                uncertainty_note='Fictional source prints no numeric error amplitude.')
    return graph


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(',', ':')).encode()).hexdigest()


class FoamEventContractTests(unittest.TestCase):
    def setUp(self):
        validate_material_catalog(*fixture())

    def test_append_preserves_twenty_branches_and_old_definitions(self):
        baseline = json.loads((ROOT/'tests/fixtures/foam_event_schema_baseline.json').read_bytes())
        stored = json.loads((ROOT/'schemas/reference_properties.schema.json').read_bytes())
        self.assertEqual(stored, _PROPERTIES_SCHEMA)
        Draft202012Validator.check_schema(stored)
        branches = stored['$defs']['property']['oneOf']
        self.assertEqual(len(branches), 27)
        self.assertEqual(digest(branches[:20]), baseline['old_branch_digest'])
        for key, expected in baseline['old_definition_digests'].items():
            self.assertEqual(digest(stored['$defs'][key]), expected, key)
        self.assertEqual(branches[20]['properties']['quantity'], {'const': QUANTITY})

    def test_reported_and_unknown_facts_preserve_input(self):
        for known in (False, True):
            graph = fixture()
            if known:
                for name in FACTS:
                    graph[1]['records'][0]['reaction_time_definition'][name].update(
                        status='reported', text='Fictional source explicitly states this fact.')
            before = deepcopy(graph)
            Draft202012Validator(_PROPERTIES_SCHEMA).validate(graph[1])
            validate_material_catalog(*graph)
            self.assertEqual(graph, before)

    def test_event_seconds_are_nonnegative_and_not_thermal_or_other_units(self):
        for token in ('0','0.000','100.000000000000000000000001','10000'):
            graph=fixture();graph[1]['records'][0]['reported_value'].update(number=token,value_text=token)
            Draft202012Validator(_PROPERTIES_SCHEMA).validate(graph[1]);validate_material_catalog(*graph)
        for token in ('-1','unknown'):
            graph=fixture();graph[1]['records'][0]['reported_value'].update(number=token,value_text=token)
            with self.assertRaises(ValueError):validate_material_catalog(*graph)
        for unit,text in [('percent','%'),('ms','ms'),('mm','mm'),('MPa','MPa')]:
            graph=fixture();graph[1]['records'][0]['reported_value'].update(unit_code=unit,unit_text=text)
            with self.assertRaises(ValueError):validate_material_catalog(*graph)
        graph=fixture();graph[1]['records'][0]['quantity']='thermal_response_characteristic_time'
        with self.assertRaises(ValueError):validate_material_catalog(*graph)

    def test_event_roles_and_matching_source_cell_are_required(self):
        for event in ('foaming_start','gel_string','tack_free','foam_rise'):
            graph=fixture();graph[1]['records'][0]['reaction_event']['code']=event;validate_material_catalog(*graph)
        for change in ('missing','wrong_code','blank_notes','wrong_document','wrong_cell','missing_value_role'):
            graph=fixture();p=graph[1]['records'][0];event=p['reaction_event']
            if change=='missing':del p['reaction_event']
            elif change=='wrong_code':event['code']='complete_cure'
            elif change=='blank_notes':event['notes']=' '
            elif change=='wrong_document':event['evidence'][0]['url']='https://example.invalid/other-document'
            elif change=='wrong_cell':event['evidence'][0]['locator']='Another source cell'
            else:event['evidence'][0]['supports']=['classification']
            with self.subTest(change=change),self.assertRaises(ValueError):validate_material_catalog(*graph)

    def test_no_event_order_or_shared_clock_is_inferred(self):
        graph=fixture();base=deepcopy(graph[1]['records'][0]);state=graph[0]['records'][0]
        for index,(code,value) in enumerate(zip(('foaming_start','gel_string','tack_free','foam_rise'),('20','5','30','1'))):
            p=graph[1]['records'][0] if index==0 else deepcopy(base)
            if index:
                p['id']=base['id']+'_event'+str(index);graph[1]['records'].append(p);state['property_ids'].append(p['id'])
            p['reaction_event']['code']=code;p['reported_value'].update(number=value,value_text=value)
            locator='Fictional Table4 row1 event column'+str(index)
            for e in p['evidence']:
                if 'reported_value' in e['supports']:e['locator']=locator
            for e in p['reaction_event']['evidence']:e['locator']=locator
        original=deepcopy(graph);validate_material_catalog(*graph);self.assertEqual(graph,original)
        self.assertTrue(all(p['reaction_time_definition']['clock_origin']['text'] is None for p in graph[1]['records']))

    def test_scalar_result_cannot_erase_unknown_orientation(self):
        graph=fixture();graph[1]['records'][0]['conditions']['direction'].update(status='not_applicable')
        with self.assertRaises(ValueError):validate_material_catalog(*graph)

    def test_unknowns_cannot_be_erased_defaulted_or_given_invented_text(self):
        for name in FACTS:
            for change in ('missing', 'not_applicable', 'empty_notes', 'invented_unknown_text', 'empty_reported'):
                graph = fixture()
                definition = graph[1]['records'][0]['reaction_time_definition']
                if change == 'missing':
                    del definition[name]
                elif change == 'not_applicable':
                    definition[name]['status'] = 'not_applicable'
                elif change == 'empty_notes':
                    definition[name]['notes'] = ' '
                elif change == 'invented_unknown_text':
                    definition[name]['text'] = 'assumed gas'
                else:
                    definition[name].update(status='reported', text=' ')
                with self.subTest(name=name, change=change), self.assertRaises(ValueError):
                    validate_material_catalog(*graph)

    def test_same_primary_document_and_required_roles(self):
        for name in ('reaction_time_definition', *FACTS):
            for bad in ('missing_evidence', 'other_document', 'missing_condition'):
                graph = fixture()
                definition = graph[1]['records'][0]['reaction_time_definition']
                fact = definition if name == 'reaction_time_definition' else definition[name]
                if bad == 'missing_evidence':
                    fact['evidence'] = []
                elif bad == 'other_document':
                    for item in fact['evidence']:
                        item['url'] = 'https://example.invalid/uninspected-supplement.pdf'
                else:
                    for item in fact['evidence']:
                        item['supports'] = ['method']
                with self.subTest(name=name, bad=bad), self.assertRaises(ValueError):
                    validate_material_catalog(*graph)

    def test_process_basis_has_no_fit_window_or_legacy_leak(self):
        for bad in ('corrected', 'modulus_window', 'extra_field', 'wrong_evidence_class'):
            graph = fixture()
            prop = graph[1]['records'][0]
            if bad == 'corrected':
                prop['reaction_time_definition']['basis'] = 'mass_percentage'
            elif bad == 'modulus_window':
                prop['method_definition']['extraction_window'] = dict(status='reported', text='below40% strain',
                    evidence=deepcopy(prop['method_definition']['evidence']), notes='Borrowed modulus fit window.')
            elif bad == 'extra_field':
                prop['reaction_time_definition']['normalized_percent'] = '50'
            else:
                prop['evidence_kind'] = 'manufacturer_reference'
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                validate_material_catalog(*graph)
        graph = synthetic_mean_catalog()
        validate_material_catalog(*graph)
        graph[1]['records'][0]['reaction_time_definition'] = fixture()[1]['records'][0]['reaction_time_definition']
        with self.assertRaises(ValueError):
            validate_material_catalog(*graph)

    def test_definition_enrichment_and_numeric_typography_are_not_new_facts(self):
        for reverse in (False, True):
            graph = fixture()
            clone = add_clone(graph)
            clone['reported_value'].update(number='12.5000', value_text='12.5000')
            clone['reaction_time_definition']['clock_origin'].update(status='reported', text='Fictional source explicitly identifies clock origin')
            clone['reaction_event']['code']='tack_free'
            clone['source_property_label']='Relabelled fictional source event'
            if reverse:
                graph[1]['records'].reverse()
            with localcontext() as context:
                context.prec = 2
                with self.assertRaises(ValueError):
                    validate_material_catalog(*graph)

    def test_absolute_amplitude_representations_use_seconds(self):
        for measures in (False, True):
            graph = as_foam_event(synthetic_reported_measures_catalog('unnamed_center_sd') if measures
                                 else uncertainty_catalog())
            prop = graph[1]['records'][0]
            amplitude = prop['uncertainty']['measures'][0]['reported_value'] if measures else prop['uncertainty']
            amplitude.update(unit_code='s', unit_text='s')
            validate_material_catalog(*graph)
            amplitude.update(unit_code='MPa', unit_text='MPa')
            with self.assertRaises(ValueError):
                validate_material_catalog(*graph)

    def test_resolve_query_export_and_all_languages_retain_event_and_unknowns(self):
        graph = fixture()
        prop = graph[1]['records'][0]
        data = dict(zip(('materials', 'reference_properties', 'sources'), graph))
        db = Database(data)
        rows = list(db.records(quantity=QUANTITY))
        self.assertEqual(len(rows), 1)
        self.assertEqual(list(db.records(quantity='tensile_elongation_at_break')), [])
        self.assertEqual(resolve_material(prop['material_state_id'], *graph)['properties'][0], prop)
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)/'absorption'
            db.export(folder, quantity=QUANTITY)
            self.assertEqual(read_snapshot(folder)[1][prop['id']]['property'], prop)
        rows[0]['property']['reaction_time_definition']['notes'] = 'detached'
        self.assertEqual(list(db.records(quantity=QUANTITY))[0]['property'], prop)
        for language in ('en', 'zh', 'ja', 'de'):
            labels = material_labels(language)
            with patch('materials_boundaries.catalog.read_catalog', side_effect=lambda name: deepcopy(data[name])):
                rendered = render_material_catalog(graph[1], 'reference-properties', language)
            for key in ('code_' + QUANTITY, 'reaction_time_reference_notice',
                        *("reaction_time_" + name for name in FACTS), 'code_not_verified'):
                self.assertIn(labels[key], rendered)
            self.assertIn('12.50 s', rendered)
            self.assertIn(labels['code_foaming_start'], rendered)



if __name__ == '__main__':
    unittest.main()
