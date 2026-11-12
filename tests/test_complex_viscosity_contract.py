"""Fictional oscillatory viscosity magnitudes and cyclic frequency."""
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
QUANTITY = 'oscillatory_complex_viscosity_magnitude'
FACTS = ('rheometer_and_geometry','temperature_control','strain_amplitude','frequency_protocol',
         'measurement_and_reduction','sample_preparation_conditioning','replicate_and_piece_relationship','instrument_corrections')


def as_complex_viscosity(graph):
    prop = graph[1]['records'][0]
    prop.update(quantity=QUANTITY, quantity_dimension='pressure_time', density_basis=None,
                source_property_label='Fictional oscillatory viscosity,kPa.s')
    prop['reported_value'].update(number='12.50', value_text='12.50', unit_code='kPa_s_complex_viscosity', unit_text='kPa.s')
    prop['conditions']['direction'] = dict(status='not_reported_in_inspected_source',text=None,evidence=[],notes='Orientation and sample location not stated; scalar magnitude does not establish orientation.')
    prop['method_definition'].update(type='source_reported_conventional', extraction_window=None)
    prop.pop('derivation', None)
    evidence = deepcopy(prop['method_definition']['evidence'])
    for entry in evidence:
        entry['supports'] = ['method', 'condition']
    unknown = dict(status='not_verified', text=None, evidence=deepcopy(evidence),
                   notes='Fictional source does not establish this rheology fact.')
    prop['complex_viscosity_definition'] = dict(basis='source_reported_oscillatory_complex_viscosity_magnitude',
        **{name: deepcopy(unknown) for name in FACTS}, evidence=evidence,
        notes='Fictional oscillatory viscosity; no steady-shear or frequency conversion inference.')
    value_evidence=deepcopy(next(e for e in prop['evidence'] if 'reported_value' in e['supports'] and e['url']==prop['source_document']['url']))
    value_evidence['supports']=['condition','classification']
    prop['oscillation_frequency']=dict(status='reported',number='1',value_text='1',unit_code='Hz',unit_text='Hz',evidence=[value_evidence],notes='Fictional reported cyclic frequency;not angular frequency or shear rate.')
    return graph


def fixture():
    graph = as_complex_viscosity(synthetic_mean_catalog())
    graph[1]['records'][0].update(uncertainty=None, uncertainty_status='not_reported_in_inspected_source',
                                uncertainty_note='Fictional source prints no numeric error amplitude.')
    return graph


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(',', ':')).encode()).hexdigest()


class ComplexViscosityContractTests(unittest.TestCase):
    def setUp(self):
        validate_material_catalog(*fixture())

    def test_append_preserves_twentythree_branches_and_old_definitions(self):
        baseline = json.loads((ROOT/'tests/fixtures/complex_viscosity_schema_baseline.json').read_bytes())
        stored = json.loads((ROOT/'schemas/reference_properties.schema.json').read_bytes())
        self.assertEqual(stored, _PROPERTIES_SCHEMA)
        Draft202012Validator.check_schema(stored)
        branches = stored['$defs']['property']['oneOf']
        self.assertEqual(len(branches), 27)
        self.assertEqual(digest(branches[:23]), baseline['old_branch_digest'])
        for key, expected in baseline['old_definition_digests'].items():
            self.assertEqual(digest(stored['$defs'][key]), expected, key)
        self.assertEqual(branches[23]['properties']['quantity'], {'const': QUANTITY})

    def test_reported_and_unknown_facts_preserve_input(self):
        for known in (False, True):
            graph = fixture()
            if known:
                for name in FACTS:
                    graph[1]['records'][0]['complex_viscosity_definition'][name].update(
                        status='reported', text='Fictional source explicitly states this fact.')
            before = deepcopy(graph)
            Draft202012Validator(_PROPERTIES_SCHEMA).validate(graph[1])
            validate_material_catalog(*graph)
            self.assertEqual(graph, before)

    def test_nonnegative_magnitude_is_not_percent_or_frequency(self):
        for token in ('0','0.000','0.9','100','1000.000'):
            graph=fixture();graph[1]['records'][0]['reported_value'].update(number=token,value_text=token)
            Draft202012Validator(_PROPERTIES_SCHEMA).validate(graph[1]);validate_material_catalog(*graph)
        for token in ('-1','NaN','Infinity'):
            graph=fixture();graph[1]['records'][0]['reported_value'].update(number=token,value_text=token)
            self.assertFalse(Draft202012Validator(_PROPERTIES_SCHEMA).is_valid(graph[1]))
            with self.assertRaises(ValueError):validate_material_catalog(*graph)
        for unit,text in [('percent_closed_cell_content_volume','vol.%'),('s','s'),('percent','%'),('percent_water_absorption_volume','V%'),('percent_tga_residue','%'),('percent_elongation','%')]:
            graph=fixture();graph[1]['records'][0]['reported_value'].update(unit_code=unit,unit_text=text)
            with self.assertRaises(ValueError):validate_material_catalog(*graph)
        graph=fixture();graph[1]['records'][0]['reported_value']['unit_text']='%'
        with self.assertRaises(ValueError):validate_material_catalog(*graph)

    def test_scalar_result_cannot_erase_unknown_orientation(self):
        graph=fixture();graph[1]['records'][0]['conditions']['direction'].update(status='not_applicable')
        with self.assertRaises(ValueError):validate_material_catalog(*graph)

    def test_unknowns_cannot_be_erased_defaulted_or_given_invented_text(self):
        for name in FACTS:
            for change in ('missing', 'not_applicable', 'empty_notes', 'invented_unknown_text', 'empty_reported'):
                graph = fixture()
                definition = graph[1]['records'][0]['complex_viscosity_definition']
                if change == 'missing':
                    del definition[name]
                elif change == 'not_applicable':
                    definition[name]['status'] = 'not_applicable'
                elif change == 'empty_notes':
                    definition[name]['notes'] = ' '
                elif change == 'invented_unknown_text':
                    definition[name]['text'] = 'assumed image count'
                else:
                    definition[name].update(status='reported', text=' ')
                with self.subTest(name=name, change=change), self.assertRaises(ValueError):
                    validate_material_catalog(*graph)

    def test_same_primary_document_and_required_roles(self):
        for name in ('complex_viscosity_definition', *FACTS):
            for bad in ('missing_evidence', 'other_document', 'missing_condition'):
                graph = fixture()
                definition = graph[1]['records'][0]['complex_viscosity_definition']
                fact = definition if name == 'complex_viscosity_definition' else definition[name]
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
                prop['complex_viscosity_definition']['basis'] = 'mass_percentage'
            elif bad == 'modulus_window':
                prop['method_definition']['extraction_window'] = dict(status='reported', text='below40% strain',
                    evidence=deepcopy(prop['method_definition']['evidence']), notes='Borrowed modulus fit window.')
            elif bad == 'extra_field':
                prop['complex_viscosity_definition']['normalized_percent'] = '50'
            else:
                prop['evidence_kind'] = 'manufacturer_reference'
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                validate_material_catalog(*graph)
        graph = synthetic_mean_catalog()
        validate_material_catalog(*graph)
        graph[1]['records'][0]['complex_viscosity_definition'] = fixture()[1]['records'][0]['complex_viscosity_definition']
        with self.assertRaises(ValueError):
            validate_material_catalog(*graph)

    def test_definition_enrichment_and_numeric_typography_are_not_new_facts(self):
        for reverse in (False, True):
            graph = fixture()
            clone = add_clone(graph)
            clone['reported_value'].update(number='12.5000', value_text='12.5000')
            clone['complex_viscosity_definition']['temperature_control'].update(status='reported', text='Source explicitly defines temperature control')
            if reverse:
                graph[1]['records'].reverse()
            with localcontext() as context:
                context.prec = 2
                with self.assertRaises(ValueError):
                    validate_material_catalog(*graph)

    def test_both_absolute_amplitude_representations_use_dedicated_viscosity_unit(self):
        for measures in (False, True):
            graph = as_complex_viscosity(synthetic_reported_measures_catalog('unnamed_center_sd') if measures
                                 else uncertainty_catalog())
            prop = graph[1]['records'][0]
            amplitude = prop['uncertainty']['measures'][0]['reported_value'] if measures else prop['uncertainty']
            amplitude.update(unit_code='kPa_s_complex_viscosity', unit_text='kPa.s')
            validate_material_catalog(*graph)
            amplitude.update(unit_code='MPa', unit_text='MPa')
            with self.assertRaises(ValueError):
                validate_material_catalog(*graph)

    def test_relative_cv_keeps_percent_separate_from_absolute_viscosity(self):
        graph=as_complex_viscosity(synthetic_reported_measures_catalog('cv'))
        prop=graph[1]['records'][0]
        validate_material_catalog(*graph)
        measure=prop['uncertainty']['measures'][0]
        self.assertEqual(measure['reported_value']['unit_code'],'percent')
        measure['reported_value'].update(unit_code='kPa_s_complex_viscosity',unit_text='kPa.s')
        with self.assertRaises(ValueError):validate_material_catalog(*graph)

    def test_resolve_query_export_and_all_languages_retain_viscosity_definition_and_unknowns(self):
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
        rows[0]['property']['complex_viscosity_definition']['notes'] = 'detached'
        self.assertEqual(list(db.records(quantity=QUANTITY))[0]['property'], prop)
        for language in ('en', 'zh', 'ja', 'de'):
            labels = material_labels(language)
            with patch('materials_boundaries.catalog.read_catalog', side_effect=lambda name: deepcopy(data[name])):
                rendered = render_material_catalog(graph[1], 'reference-properties', language)
            for key in ('code_' + QUANTITY, 'complex_viscosity_reference_notice',
                        *("complex_viscosity_" + name for name in FACTS), 'code_not_verified'):
                self.assertIn(labels[key], rendered)
            self.assertIn('12.50 kPa.s', rendered)


    def test_reported_and_explicit_unknown_frequency_shapes(self):
        for status in ('reported','not_verified','not_reported_in_inspected_source'):
            graph=fixture();coordinate=graph[1]['records'][0]['oscillation_frequency']
            if status!='reported':
                coordinate.update(status=status,**{k:None for k in ('number','value_text','unit_code','unit_text')})
            before=deepcopy(graph);validate_material_catalog(*graph);self.assertEqual(graph,before)

    def test_frequency_positive_hz_and_source_precision_only(self):
        for number,text in [('0','0'),('-1','-1'),('NaN','NaN'),('1e3','1e3'),('1.00','1.0')]:
            graph=fixture();graph[1]['records'][0]['oscillation_frequency'].update(number=number,value_text=text)
            with self.subTest(number=number),self.assertRaises(ValueError):validate_material_catalog(*graph)
        for code in ('rad/s','s^-1','s','percent'):
            graph=fixture();graph[1]['records'][0]['oscillation_frequency'].update(unit_code=code,unit_text=code)
            with self.assertRaises(ValueError):validate_material_catalog(*graph)

    def test_unknown_frequency_cannot_be_defaulted_or_erased(self):
        for change in ('number','value_text','unit_code','unit_text','notes','status','missing'):
            graph=fixture();prop=graph[1]['records'][0];coordinate=prop['oscillation_frequency']
            coordinate.update(status='not_verified',**{k:None for k in ('number','value_text','unit_code','unit_text')})
            if change in ('number','value_text'):coordinate[change]='0'
            elif change in ('unit_code','unit_text'):coordinate[change]='Hz'
            elif change=='notes':coordinate['notes']=' '
            elif change=='status':coordinate['status']='not_applicable'
            else:del prop['oscillation_frequency']
            with self.subTest(change=change),self.assertRaises(ValueError):validate_material_catalog(*graph)

    def test_frequency_requires_matching_primary_value_cell_evidence(self):
        for change in ('empty','other_document','other_cell','missing_condition','missing_classification'):
            graph=fixture();coordinate=graph[1]['records'][0]['oscillation_frequency']
            if change=='empty':coordinate['evidence']=[]
            elif change=='other_document':coordinate['evidence'][0]['url']='https://example.invalid/other.pdf'
            elif change=='other_cell':coordinate['evidence'][0]['locator']='Different frequency column'
            elif change=='missing_condition':coordinate['evidence'][0]['supports']=['classification']
            else:coordinate['evidence'][0]['supports']=['condition']
            with self.subTest(change=change),self.assertRaises(ValueError):validate_material_catalog(*graph)

    def test_same_cell_frequency_relabel_and_unknown_enrichment_are_revisions(self):
        for reverse in (False,True):
            for unknown in (False,True):
                graph=fixture();clone=add_clone(graph)
                clone['reported_value'].update(number='12.5000',value_text='12.5000')
                if unknown:clone['oscillation_frequency'].update(status='not_verified',**{k:None for k in ('number','value_text','unit_code','unit_text')})
                else:clone['oscillation_frequency'].update(number='30',value_text='30')
                clone['source_property_label']='Fictional alias for same source cell'
                if reverse:graph[1]['records'].reverse()
                with localcontext() as context:
                    context.prec=2
                    with self.assertRaises(ValueError):validate_material_catalog(*graph)

    def test_distinct_frequency_cells_can_share_central_value(self):
        graph=fixture();clone=add_clone(graph);clone['oscillation_frequency'].update(number='30',value_text='30')
        for entry in clone['evidence']:
            if 'reported_value' in entry['supports']:entry['locator']+=' / distinct30Hzcell'
        clone['oscillation_frequency']['evidence'][0]['locator']=next(e['locator'] for e in clone['evidence'] if 'reported_value' in e['supports'])
        validate_material_catalog(*graph)
        db=Database(dict(zip(('materials','reference_properties','sources'),graph)))
        self.assertEqual(len(list(db.records(quantity=QUANTITY))),2)

    def test_unknown_frequency_survives_full_export_copy_and_languages(self):
        graph=fixture();prop=graph[1]['records'][0];prop['oscillation_frequency'].update(status='not_verified',**{k:None for k in ('number','value_text','unit_code','unit_text')})
        data=dict(zip(('materials','reference_properties','sources'),graph));db=Database(data)
        with tempfile.TemporaryDirectory() as directory:
            folder=Path(directory)/'unknown-frequency';db.export(folder,quantity=QUANTITY)
            self.assertEqual(read_snapshot(folder)[1][prop['id']]['property'],prop)
        rows=list(db.records(quantity=QUANTITY));rows[0]['property']['oscillation_frequency']['number']='0'
        self.assertIsNone(list(db.records(quantity=QUANTITY))[0]['property']['oscillation_frequency']['number'])
        for language in ('en','zh','ja','de'):
            with patch('materials_boundaries.catalog.read_catalog',side_effect=lambda name:deepcopy(data[name])):
                rendered=render_material_catalog(graph[1],'reference-properties',language)
            self.assertIn(material_labels(language)['oscillation_frequency'],rendered)
            self.assertNotIn('0 Hz',rendered)

    def test_zero_central_and_absolute_amplitude_do_not_become_unknown(self):
        for measures in (False,True):
            graph=as_complex_viscosity(synthetic_reported_measures_catalog('unnamed_center_sd') if measures else uncertainty_catalog())
            prop=graph[1]['records'][0];prop['reported_value'].update(number='0',value_text='0')
            amplitude=prop['uncertainty']['measures'][0]['reported_value'] if measures else prop['uncertainty']
            amplitude.update(unit_code='kPa_s_complex_viscosity',unit_text='kPa.s',number='0',value_text='0')
            validate_material_catalog(*graph)
            amplitude.update(number='-0.1',value_text='-0.1')
            with self.assertRaises(ValueError):validate_material_catalog(*graph)



if __name__ == '__main__':
    unittest.main()
