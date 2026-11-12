"""Fictional volumetric water absorption; source percentages are not mass uptake."""
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
QUANTITY = 'water_absorption_volume_percentage'
FACTS = ('volume_reference_basis', 'immersion_exposure', 'fluid', 'specimen_geometry',
         'preconditioning', 'water_temperature', 'surface_water_treatment')


def as_absorption(graph):
    prop = graph[1]['records'][0]
    prop.update(quantity=QUANTITY, quantity_dimension='dimensionless', density_basis=None,
                source_property_label='Fictional water absorption, V%')
    prop['reported_value'].update(number='12.50', value_text='12.50', unit_code='percent_water_absorption_volume', unit_text='V%')
    prop['method_definition'].update(type='source_reported_conventional', extraction_window=None)
    prop.pop('derivation', None)
    evidence = deepcopy(prop['method_definition']['evidence'])
    for entry in evidence:
        entry['supports'] = ['method', 'condition']
    unknown = dict(status='not_verified', text=None, evidence=deepcopy(evidence),
                   notes='Fictional source does not establish this extension fact.')
    prop['water_absorption_definition'] = dict(basis='source_reported_volume_percentage',
        **{name: deepcopy(unknown) for name in FACTS}, evidence=evidence,
        notes='Fictional source volume percentage; no mass conversion or assumed denominator.')
    return graph


def fixture():
    graph = as_absorption(synthetic_mean_catalog())
    graph[1]['records'][0].update(uncertainty=None, uncertainty_status='not_reported_in_inspected_source',
                                uncertainty_note='Fictional source prints no numeric error amplitude.')
    return graph


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(',', ':')).encode()).hexdigest()


class WaterAbsorptionContractTests(unittest.TestCase):
    def test_append_preserves_eighteen_branches_and_old_definitions(self):
        baseline = json.loads((ROOT/'tests/fixtures/water_absorption_schema_baseline.json').read_bytes())
        stored = json.loads((ROOT/'schemas/reference_properties.schema.json').read_bytes())
        self.assertEqual(stored, _PROPERTIES_SCHEMA)
        Draft202012Validator.check_schema(stored)
        branches = stored['$defs']['property']['oneOf']
        self.assertEqual(len(branches), 24)
        self.assertEqual(digest(branches[:18]), baseline['old_branch_digest'])
        for key, expected in baseline['old_definition_digests'].items():
            self.assertEqual(digest(stored['$defs'][key]), expected, key)
        self.assertEqual(branches[18]['properties']['quantity'], {'const': QUANTITY})

    def test_reported_and_unknown_facts_preserve_input(self):
        for known in (False, True):
            graph = fixture()
            if known:
                for name in FACTS:
                    graph[1]['records'][0]['water_absorption_definition'][name].update(
                        status='reported', text='Fictional source explicitly states this fact.')
            before = deepcopy(graph)
            Draft202012Validator(_PROPERTIES_SCHEMA).validate(graph[1])
            validate_material_catalog(*graph)
            self.assertEqual(graph, before)

    def test_volume_percentage_is_not_mass_or_relative_percent_and_zero_is_not_missing(self):
        for unit, text in [('percent_elongation', '%'), ('percent', '%'), ('percent_tga_residue', '%'), ('MPa', 'MPa')]:
            graph = fixture()
            graph[1]['records'][0]['reported_value'].update(unit_code=unit, unit_text=text)
            with self.assertRaises(ValueError):
                validate_material_catalog(*graph)
        graph = fixture()
        graph[1]['records'][0]['reported_value'].update(number='0', value_text='0')
        validate_material_catalog(*graph)
        graph[1]['records'][0]['reported_value'].update(number='-1', value_text='-1')
        with self.assertRaises(ValueError):
            validate_material_catalog(*graph)
        graph = fixture()
        graph[1]['records'][0]['reported_value']['unit_text'] = '%'
        with self.assertRaises(ValueError):
            validate_material_catalog(*graph)

    def test_unknowns_cannot_be_erased_defaulted_or_given_invented_text(self):
        for name in FACTS:
            for change in ('missing', 'not_applicable', 'empty_notes', 'invented_unknown_text', 'empty_reported'):
                graph = fixture()
                definition = graph[1]['records'][0]['water_absorption_definition']
                if change == 'missing':
                    del definition[name]
                elif change == 'not_applicable':
                    definition[name]['status'] = 'not_applicable'
                elif change == 'empty_notes':
                    definition[name]['notes'] = ' '
                elif change == 'invented_unknown_text':
                    definition[name]['text'] = 'assumed gauge'
                else:
                    definition[name].update(status='reported', text=' ')
                with self.subTest(name=name, change=change), self.assertRaises(ValueError):
                    validate_material_catalog(*graph)

    def test_same_primary_document_and_required_roles(self):
        for name in ('water_absorption_definition', *FACTS):
            for bad in ('missing_evidence', 'other_document', 'missing_condition'):
                graph = fixture()
                definition = graph[1]['records'][0]['water_absorption_definition']
                fact = definition if name == 'water_absorption_definition' else definition[name]
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

    def test_no_mass_basis_modulus_window_or_leak_to_old_quantity(self):
        for bad in ('corrected', 'modulus_window', 'extra_field', 'wrong_evidence_class'):
            graph = fixture()
            prop = graph[1]['records'][0]
            if bad == 'corrected':
                prop['water_absorption_definition']['basis'] = 'mass_percentage'
            elif bad == 'modulus_window':
                prop['method_definition']['extraction_window'] = dict(status='reported', text='below40% strain',
                    evidence=deepcopy(prop['method_definition']['evidence']), notes='Borrowed modulus fit window.')
            elif bad == 'extra_field':
                prop['water_absorption_definition']['normalized_percent'] = '50'
            else:
                prop['evidence_kind'] = 'manufacturer_reference'
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                validate_material_catalog(*graph)
        graph = synthetic_mean_catalog()
        validate_material_catalog(*graph)
        graph[1]['records'][0]['water_absorption_definition'] = fixture()[1]['records'][0]['water_absorption_definition']
        with self.assertRaises(ValueError):
            validate_material_catalog(*graph)

    def test_definition_enrichment_and_numeric_typography_are_not_new_facts(self):
        for reverse in (False, True):
            graph = fixture()
            clone = add_clone(graph)
            clone['reported_value'].update(number='12.5000', value_text='12.5000')
            clone['water_absorption_definition']['volume_reference_basis'].update(status='reported', text='Source explicitly defines volume reference')
            if reverse:
                graph[1]['records'].reverse()
            with localcontext() as context:
                context.prec = 2
                with self.assertRaises(ValueError):
                    validate_material_catalog(*graph)

    def test_both_absolute_amplitude_representations_use_dedicated_volume_scale(self):
        for measures in (False, True):
            graph = as_absorption(synthetic_reported_measures_catalog('unnamed_center_sd') if measures
                                 else uncertainty_catalog())
            prop = graph[1]['records'][0]
            amplitude = prop['uncertainty']['measures'][0]['reported_value'] if measures else prop['uncertainty']
            amplitude.update(unit_code='percent_water_absorption_volume', unit_text='V%')
            validate_material_catalog(*graph)
            amplitude.update(unit_code='MPa', unit_text='MPa')
            with self.assertRaises(ValueError):
                validate_material_catalog(*graph)

    def test_resolve_query_export_and_all_languages_retain_volume_and_unknowns(self):
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
        rows[0]['property']['water_absorption_definition']['notes'] = 'detached'
        self.assertEqual(list(db.records(quantity=QUANTITY))[0]['property'], prop)
        for language in ('en', 'zh', 'ja', 'de'):
            labels = material_labels(language)
            with patch('materials_boundaries.catalog.read_catalog', side_effect=lambda name: deepcopy(data[name])):
                rendered = render_material_catalog(graph[1], 'reference-properties', language)
            for key in ('code_' + QUANTITY, 'water_absorption_reference_notice',
                        *("water_absorption_" + name for name in FACTS), 'code_not_verified'):
                self.assertIn(labels[key], rendered)
            self.assertIn('12.50 V%', rendered)



if __name__ == '__main__':
    unittest.main()
