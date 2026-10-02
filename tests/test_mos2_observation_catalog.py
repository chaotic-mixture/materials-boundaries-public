"""Bertolazzi monolayer observations retain their source limits and stay catalog-only.

Expected facts are transcribed from the inspected institutional artifact. Tests
need neither that copyrighted PDF nor a machine-local research/baseline folder.
The selected pair is a historical fixture, never a cap on future record IDs.
"""
import copy
from contextlib import ExitStack
import hashlib
import json
import subprocess
import sys
import unittest
from unittest.mock import Mock, patch
from uuid import uuid4

from materials_boundaries import ValidationError, evaluate, load_json
from materials_boundaries.catalog import CatalogLookupError, query_catalog, read_catalog
from materials_boundaries.catalog_output import render_catalog
from materials_boundaries.i18n import LANGUAGES, translate
from materials_boundaries.visualization import (
    build_comparison, render_html, render_svg, validate_comparison,
)
from scripts.validate_catalogs import (
    CATALOGS, CatalogValidationError, load_catalogs, validate_catalogs,
)
from test_engine import ROOT, example

from jsonschema import Draft202012Validator, FormatChecker


IDS = (
    'bertolazzi_2011_mos2_monolayer_in_plane_stiffness_2d',
    'bertolazzi_2011_mos2_monolayer_breaking_strength_2d',
)
SOURCE = 'bertolazzi_brivio_kis_2011'
FAMILY = 'bertolazzi_2011_mos2_monolayer_indentation_v1'
MODEL_STATUS = 'source_reported_unresolved_model_discrepancy'
READ_STATUS = 'primary_institutional_main_text_checked_supplement_not_inspected'
DOI = '10.1021/nn203879f'
ARTIFACT_URL = (
    'https://infoscience.epfl.ch/server/api/core/bitstreams/'
    '5af84a4c-55a4-4151-9d85-d5c215d848a4/content'
)

# Canonical full-record hashes from the accepted pre-MoS2 public baseline.
# The historical source and both graphene records must remain unchanged here.
GRAPHENE_DIGESTS = {
    'observations': {
        'lee_2008_graphene_in_plane_stiffness_2d':
            '06b776aa7038c141f350c12d4118168940537445ed62edfc34e9c828a8e28907',
        'lee_2008_graphene_breaking_strength_2d':
            'b2d736a9afe13c914b64fd9ab1bad4e0420eac4eabb51b3e27696592f446aecc',
    },
    'sources': {
        'lee_wei_kysar_hone_2008':
            '3923cfeed09a9331e2b7d492aaa1749a1e1035da6236adb08f70ec2e22ffad96',
    },
}


def selected_records(catalog=None):
    """Explicit fixture order, independent of packaged order and future records."""
    catalog = read_catalog('observations') if catalog is None else catalog
    indexed = {record['id']: record for record in catalog['records']}
    return [indexed[identifier] for identifier in IDS]


def set_path(record, path, value):
    target = record
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value


def patched_catalogs(catalogs):
    stack = ExitStack()
    for module in ('catalog', 'catalog_output', 'i18n', 'visualization'):
        stack.enter_context(patch(
            f'materials_boundaries.{module}.read_catalog',
            side_effect=lambda kind: copy.deepcopy(catalogs[kind]),
        ))
    return stack


class MoS2SourceFactsTests(unittest.TestCase):
    def test_selected_pair_does_not_close_catalog_growth(self):
        catalog = read_catalog('observations')
        self.assertEqual(catalog['schema_version'], '1.2.0')
        selected = [record for record in catalog['records'] if record['id'] in IDS]
        self.assertEqual(len(selected), 2)
        self.assertEqual({record['id'] for record in selected}, set(IDS))
        self.assertEqual({record['study_id'] for record in selected}, {SOURCE})
        self.assertTrue(set(IDS).isdisjoint(
            record['id'] for record in read_catalog('claims')['records']))
        for record in selected:
            self.assertEqual(record['method_family'], FAMILY)
            self.assertEqual(record['model_status'], MODEL_STATUS)
            self.assertEqual(record['evaluation_support'], 'catalog_only')
            self.assertTrue(any('not independent confirmations' in note
                                for note in record['limits']))

    def test_graphene_records_and_source_are_exactly_preserved(self):
        for kind, expected in GRAPHENE_DIGESTS.items():
            indexed = {record['id']: record for record in read_catalog(kind)['records']}
            for identifier, digest in expected.items():
                with self.subTest(kind=kind, identifier=identifier):
                    encoded = json.dumps(indexed[identifier], sort_keys=True,
                                         separators=(',', ':'), ensure_ascii=False).encode()
                    self.assertEqual(hashlib.sha256(encoded).hexdigest(), digest)

    def test_canonical_two_dimensional_values_and_reported_sd(self):
        expected = [('in_plane_stiffness_2d', 180, 60), ('breaking_strength_2d', 15, 3)]
        for record, (quantity, value, deviation) in zip(selected_records(), expected):
            with self.subTest(quantity=quantity):
                self.assertEqual(record['observation_type'], 'experiment_derived_model_dependent')
                self.assertEqual((record['quantity'], record['quantity_dimension'], record['si_unit']),
                                 (quantity, 'force_per_length', 'N/m'))
                result = record['reported_result']
                self.assertEqual((result['value'], result['unit'], result['summary_statistic']),
                                 (value, 'N/m', 'reported_average'))
                self.assertEqual(result['source_value_string'], f'{value} ± {deviation} Nm⁻¹')
                uncertainty = result['uncertainty']
                self.assertEqual((uncertainty['value'], uncertainty['unit'], uncertainty['notation']),
                                 (deviation, 'N/m', 'plus_minus'))
                self.assertEqual(uncertainty['type'], 'reported_standard_deviation')
                self.assertEqual(uncertainty['scope'], 'reported_property_experimental_values')
                for field in ('confidence_level', 'coverage_factor', 'averaging_convention'):
                    self.assertIsNone(uncertainty[field])
                for field in ('lower', 'upper', 'standard_error', 'confidence_interval'):
                    self.assertNotIn(field, result)
                    self.assertNotIn(field, uncertainty)
                for field in ('thickness', 'default_thickness', 'youngs_modulus_3d'):
                    self.assertNotIn(field, record['material'])
                    self.assertNotIn(field, result)

    def test_monolayer_preparation_and_geometric_tolerances(self):
        for record in selected_records():
            material = record['material']
            self.assertEqual((material['formula'], material['dimensionality'], material['layer_count']),
                             ('MoS2', 2, 1))
            self.assertEqual(material['specimen_form'], 'suspended_membrane')
            self.assertEqual(material['preparation'],
                             'micromechanical_exfoliation_of_molybdenite_with_PVA_PMMA_transfer')
            self.assertEqual(material['monolayer_identification'],
                             ['optical_contrast', 'afm_thickness_verification'])
            self.assertIsNone(material['crystal_orientation'])
            span = material['suspended_span_diameters']
            self.assertEqual((span['values'], span['unit'], span['reported_value_string']),
                             ([550], 'nm', '550 ± 10 nm'))
            tip = record['method']['tip_radius']
            self.assertEqual((tip['value'], tip['unit'], tip['reported_value_string']),
                             (12, 'nm', '12 ± 2 nm'))
            self.assertIn('supplement images not inspected', tip['measurement'])
            for geometry, error in ((span, 10), (tip, 2)):
                self.assertEqual(geometry['uncertainty']['value'], error)
                self.assertEqual(geometry['uncertainty']['unit'], 'nm')
                self.assertEqual(geometry['uncertainty']['type'], 'reported_plus_minus_unspecified')
                self.assertIsNone(geometry['uncertainty']['coverage_factor'])
                self.assertIsNone(geometry['uncertainty']['confidence_level'])
                self.assertIn('PDF p. 3 (C)', geometry['locator'])

    def test_known_probe_speed_does_not_fill_unknown_environment(self):
        for record in selected_records():
            conditions = record['conditions']
            for field in ('temperature', 'atmosphere', 'humidity'):
                self.assertIsNone(conditions[field])
            self.assertEqual(conditions['verification_status'], 'partially_reported_primary_main_text')
            speed = conditions['loading_rate']
            self.assertEqual((speed['quantity'], speed['value'], speed['unit']),
                             ('vertical_probe_translation_speed', 2, 'um/s'))
            self.assertEqual(speed['reported_value_string'], '2 μm s⁻¹')
            self.assertIn('PDF p. 2 (B)', speed['locator'])
            notes = ' '.join(conditions['notes'])
            self.assertIn('not membrane strain rate', notes)
            self.assertIn('400 °C vacuum processing step', notes)

    def test_study_and_property_counts_are_not_failure_or_curve_counts(self):
        stiffness, strength = selected_records()
        for record in (stiffness, strength):
            sample = record['sample_metadata']
            self.assertEqual(sample['scope'], 'study_membrane_counts_not_force_curve_or_failure_event_counts')
            self.assertEqual(sample['counts']['study_monolayer_membranes'], 9)
            for field in ('force_displacement_curves', 'distinct_parent_flakes', 'failure_events'):
                self.assertIsNone(sample['counts'][field])
            self.assertNotIn('study_bilayer_membranes', sample['counts'])
            self.assertNotIn('fitted_distribution', sample)
            self.assertIn('PDF p. 3 (C)', sample['locator'])
        self.assertEqual(stiffness['sample_metadata']['counts']
                         ['membranes_explicitly_associated_with_stiffness_average'], 9)
        self.assertNotIn('membranes_explicitly_associated_with_stiffness_average',
                         strength['sample_metadata']['counts'])

    def test_printed_q_discrepancy_remains_unresolved_without_refitting(self):
        for record in selected_records():
            self.assertEqual(record['method']['poissons_ratio_assumed'], .27)
            report = record['method']['q_source_report']
            self.assertEqual(report['formula_as_printed'], 'q = 1/(1.05 − 0.15ν − 0.16ν²)')
            self.assertEqual((report['nu_as_printed'], report['q_as_printed']), (.27, .95))
            self.assertEqual(report['internal_consistency'], 'inconsistent')
            audit_value = 1 / (1.05 - .15 * .27 - .16 * .27 ** 2)
            self.assertAlmostEqual(report['audit_arithmetic_value'], audit_value, places=14)
            self.assertNotAlmostEqual(report['audit_arithmetic_value'], report['q_as_printed'], places=2)
            self.assertIsNone(report['fit_constant_actually_used'])
            self.assertIn('not a source-reported measurement or a replacement q', report['audit_arithmetic_status'])
            self.assertIn('do not select a corrected fit constant', report['curation_action'])
            self.assertIn('PDF p. 4 (D)', report['locator'])

    def test_property_specific_linear_membrane_models_do_not_inherit_graphene(self):
        stiffness, strength = selected_records()
        for record in (stiffness, strength):
            method = record['method']
            self.assertEqual(method['technique'], 'afm_central_indentation')
            self.assertEqual(method['constitutive_model'], 'isotropic_linear_elastic_membrane')
            self.assertIsNone(method['stress_measure'])
            self.assertIsNone(method['strain_measure'])
            self.assertIn('thermal method', method['calibration'])
            self.assertNotIn('-E2D^2/(4*D2D)', method['inference'])
            self.assertNotIn('finite-element', method['inference'])
            self.assertTrue(any('not the Lee graphene nonlinear' in note for note in record['limits']))
        self.assertEqual(stiffness['method']['inference_model'], 'circular_membrane_elastic_force_deflection_fit')
        self.assertEqual(strength['method']['inference_model'], 'finite_spherical_tip_large_load_maximum_local_stress')
        self.assertEqual(stiffness['method']['direct_experimental_inputs'],
                         ['cantilever_deflection', 'z_piezo_extension'])
        self.assertEqual(strength['method']['direct_experimental_inputs'],
                         ['cantilever_deflection', 'z_piezo_extension', 'failure_event'])
        stiffness_model = ' '.join(stiffness['method']['model_assumptions'])
        strength_model = ' '.join(strength['method']['model_assumptions'])
        self.assertIn('linear material constitutive assumption', stiffness_model)
        self.assertIn('q^3 δ^3/r^2', stiffness_model)
        self.assertIn('Point-loading approximation', stiffness_model)
        self.assertIn('linearly elastic isotropic membrane', strength_model)
        self.assertIn('sqrt(F_max E^(2D)/(4π r_tip))', strength_model)
        self.assertIn('κ < 0.02', strength_model)
        self.assertIn('finite spherical-tip radius', strength['method']['inference'])

    def test_proof_page_locators_and_inspection_status_are_precise(self):
        for record, page in zip(selected_records(), ('PDF p. 4 (D)', 'PDF p. 5 (E)')):
            verification = record['verification']
            self.assertEqual(verification['status'], READ_STATUS)
            self.assertIs(verification['independent_scientific_review'], False)
            inspection = verification['source_inspection']
            self.assertEqual(inspection['artifact'], 'epfl_institutional_main_text')
            self.assertEqual(inspection['pagination'], 'proof_formatted_pdf_pages_A_to_G')
            self.assertIs(inspection['separate_reader_transcription_checked'], True)
            for field in ('publisher_final_text_identity_verified', 'supplement_inspected',
                          'raw_data_reanalysis', 'independent_replication'):
                self.assertIs(inspection[field], False)
            evidence = next(item for item in record['evidence'] if item['source_id'] == SOURCE)
            self.assertEqual((evidence['doi'], evidence['source_url']), (DOI, ARTIFACT_URL))
            self.assertEqual(evidence['verification_status'], 'primary_main_text_passage_and_visual_layout_checked')
            self.assertIn(page, evidence['locator'])
            self.assertIn('PDF p. 4 (D)', evidence['locator'])
            self.assertNotIn('9706', evidence['locator'])

    def test_source_bibliography_and_reuse_limits(self):
        source = query_catalog('sources', record_id=SOURCE)['records'][0]
        self.assertEqual(source['title'], 'Stretching and Breaking of Ultrathin MoS2')
        self.assertEqual(source['authors'], ['Simone Bertolazzi', 'Jacopo Brivio', 'Andras Kis'])
        self.assertEqual((source['year'], source['doi'], source['role']),
                         (2011, DOI, 'experimental_observation_primary_source'))
        self.assertEqual(source['read_status'], READ_STATUS)
        self.assertEqual(source['license'], {
            'status': 'copyright_american_chemical_society_no_explicit_open_reuse_license_verified',
            'identifier': None,
        })
        self.assertIn(ARTIFACT_URL, source['urls'])
        self.assertIn('https://pubmed.ncbi.nlm.nih.gov/22087740/', source['urls'])
        self.assertEqual(source['bundled_content'],
                         'brief_factual_numerical_values_bibliographic_metadata_source_locators_and_original_curation_notes_only')
        notes = ' '.join(source['claim_notes'])
        for phrase in ('ACS Nano 5(12), 9703–9709', 'proof-formatted pages A–G',
                       'one experimental study', 'actual fit constant used remains unresolved',
                       'no legal review', 'No PDF, full text, figures, screenshots',
                       'project MIT license does not relicense'):
            self.assertIn(phrase, notes)


class MoS2SchemaContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        schema = load_json(ROOT / 'schemas/observations.schema.json')
        Draft202012Validator.check_schema(schema)
        cls.validator = Draft202012Validator(schema, format_checker=FormatChecker())

    def setUp(self):
        self.catalog = read_catalog('observations')
        self.catalog['records'] = selected_records(self.catalog)

    def invalid_changes(self, changes, indices=(0, 1)):
        for index in indices:
            for path, value in changes:
                with self.subTest(record=IDS[index], path=path, value=value):
                    candidate = copy.deepcopy(self.catalog)
                    set_path(candidate['records'][index], path, value)
                    self.assertTrue(list(self.validator.iter_errors(candidate)),
                                    f'accepted unsupported mutation at {path}')

    def test_current_schema_accepts_pair_full_catalog_and_empty_subset(self):
        self.validator.validate(self.catalog)
        self.validator.validate(read_catalog('observations'))
        self.validator.validate({'schema_version': '1.2.0', 'records': []})
        candidate = copy.deepcopy(self.catalog)
        candidate['schema_version'] = '1.0.0'
        self.assertTrue(list(self.validator.iter_errors(candidate)))

    def test_units_dimensionality_material_and_execution_mutations_fail(self):
        changes = [
            (('si_unit',), 'Pa'), (('quantity_dimension',), 'pressure'),
            (('quantity',), 'youngs_modulus_3d'),
            (('observation_type',), 'theoretical_bound'),
            (('evaluation_support',), 'composite_evaluate'),
            (('reported_result', 'unit'), 'GPa'),
            (('reported_result', 'uncertainty', 'unit'), 'Pa'),
            (('material', 'formula'), 'graphene'), (('material', 'dimensionality'), 3),
            (('material', 'layer_count'), 2), (('material', 'layer_count'), True),
            (('material', 'preparation'), 'chemical_vapor_deposition'),
            (('material', 'default_thickness'), {'value': .65, 'unit': 'nm'}),
            (('material', 'suspended_span_diameters', 'unit'), 'um'),
            (('method', 'tip_radius', 'unit'), 'um'),
            (('claim_type',), 'theoretical_bound'), (('rule_id',), 'mos2_fit_v1'),
            (('direction',), 'upper'), (('result',), {'upper': 180, 'unit': 'N/m'}),
        ]
        self.invalid_changes(changes)

    def test_sd_scope_cannot_be_recast_as_sem_ci_or_geometric_sd(self):
        prefix = ('reported_result', 'uncertainty')
        self.invalid_changes([(prefix + (field,), value) for field, value in (
            ('type', 'reported_plus_minus_unspecified'), ('type', 'standard_error'),
            ('type', 'confidence_interval'), ('confidence_level', .68),
            ('confidence_level', .95), ('coverage_factor', 1), ('coverage_factor', 2),
            ('scope', 'force_displacement_curves'), ('scope', 'independent_failure_events'),
            ('averaging_convention', 'equal_weight_per_membrane'),
            ('standard_error', 20), ('lower', 120), ('upper', 240),
            ('value', -1), ('value', True), ('value', '60'),
        )])
        for geometry in (('material', 'suspended_span_diameters'), ('method', 'tip_radius')):
            self.invalid_changes([
                (geometry + ('uncertainty', 'type'), 'reported_standard_deviation'),
                (geometry + ('uncertainty', 'coverage_factor'), 1),
                (geometry + ('uncertainty', 'confidence_level'), .68),
                (geometry + ('uncertainty', 'unit'), 'um'),
            ])

    def test_counts_cannot_be_relabelled_or_assumed(self):
        prefix = ('sample_metadata', 'counts')
        self.invalid_changes([
            (('sample_metadata', 'scope'), 'failure_events'),
            (prefix + ('force_displacement_curves',), 9),
            (prefix + ('distinct_parent_flakes',), 9),
            (prefix + ('failure_events',), 9),
            (prefix + ('study_monolayer_membranes',), 15),
            (prefix + ('study_monolayer_membranes',), True),
            (prefix + ('study_bilayer_membranes',), 6),
        ])
        self.invalid_changes([(prefix + ('membranes_explicitly_associated_with_stiffness_average',), 9)], indices=(1,))
        self.invalid_changes([(prefix + ('membranes_explicitly_associated_with_stiffness_average',), None)], indices=(0,))
        candidate = copy.deepcopy(self.catalog)
        del candidate['records'][0]['sample_metadata']['counts']['membranes_explicitly_associated_with_stiffness_average']
        self.assertTrue(list(self.validator.iter_errors(candidate)))

    def test_probe_speed_and_unknown_conditions_cannot_be_reinterpreted(self):
        self.invalid_changes([
            (('conditions', 'loading_rate', 'quantity'), 'strain_rate'),
            (('conditions', 'loading_rate', 'unit'), 's^-1'),
            (('conditions', 'loading_rate', 'value'), True),
            (('conditions', 'loading_rate', 'value'), 0),
            (('conditions', 'loading_rate'), None),
            (('conditions', 'temperature'), {'value': 400, 'unit': 'degC'}),
            (('conditions', 'atmosphere'), 'vacuum'),
            (('conditions', 'humidity'), 0),
            (('conditions', 'verification_status'), 'verified'),
            (('method', 'stress_measure'), 'second_piola_kirchhoff'),
            (('method', 'strain_measure'), 'lagrangian'),
        ])

    def test_printed_q_inputs_and_unknown_fit_constant_cannot_be_silently_corrected(self):
        prefix = ('method', 'q_source_report')
        self.invalid_changes([
            (('method', 'poissons_ratio_assumed'), .165),
            (('model_status',), 'verified'),
            (prefix + ('formula_as_printed',), 'q = 1'),
            (prefix + ('nu_as_printed',), .165),
            (prefix + ('q_as_printed',), 1.002168693051764),
            (prefix + ('internal_consistency',), 'consistent'),
            (prefix + ('audit_arithmetic_value',), .95),
            (prefix + ('fit_constant_actually_used',), .95),
            (prefix + ('fit_constant_actually_used',), 1.002168693051764),
        ])
        for field in self.catalog['records'][0]['method']['q_source_report']:
            candidate = copy.deepcopy(self.catalog)
            del candidate['records'][0]['method']['q_source_report'][field]
            with self.subTest(missing=field):
                self.assertTrue(list(self.validator.iter_errors(candidate)))

    def test_source_family_and_traceability_fail_closed(self):
        self.invalid_changes([
            (('method_family',), 'unreviewed_mos2_indentation_v2'),
            (('study_id',), 'unreviewed_mos2_study'),
            (('method', 'technique'), 'uniaxial_tensile_test'),
            (('method', 'constitutive_model'), 'nonlinear_constitutive_finite_element'),
            (('method', 'inference_model'), 'lee_graphene_nonlinear_failure'),
            (('evidence', 0, 'source_id'), 'lee_wei_kysar_hone_2008'),
            (('evidence', 0, 'source_url'), 'https://example.com/unverified.pdf'),
            (('evidence', 0, 'doi'), '10.1126/science.1157996'),
            (('evidence',), []),
        ])
        for field in ('method_family', 'model_status', 'study_id', 'evidence', 'method',
                      'reported_result', 'material', 'conditions', 'sample_metadata', 'verification', 'limits'):
            candidate = copy.deepcopy(self.catalog)
            del candidate['records'][0][field]
            with self.subTest(missing=field):
                self.assertTrue(list(self.validator.iter_errors(candidate)))
        graphene = read_catalog('observations')['records']
        graphene_method = next(record['method'] for record in graphene
                               if record['id'] == 'lee_2008_graphene_breaking_strength_2d')
        self.invalid_changes([(('method',), graphene_method)])

    def test_source_inspection_cannot_be_upgraded_to_replication_or_final_text(self):
        self.invalid_changes([
            (('verification', 'status'), 'full_text_and_supplement_verified'),
            (('verification', 'independent_scientific_review'), True),
            (('verification', 'source_inspection', 'pagination'), 'final_published_pages_9703_to_9709'),
            (('verification', 'source_inspection', 'artifact'), 'publisher_final_text'),
        ] + [
            (('verification', 'source_inspection', field), True)
            for field in ('publisher_final_text_identity_verified', 'supplement_inspected',
                          'raw_data_reanalysis', 'independent_replication')
        ])
        candidate = copy.deepcopy(self.catalog)
        del candidate['records'][0]['verification']['source_inspection']
        self.assertTrue(list(self.validator.iter_errors(candidate)))


class MoS2ContributionAndIsolationTests(unittest.TestCase):
    def setUp(self):
        self.catalogs = load_catalogs(ROOT / 'materials_boundaries/data')

    def append_fresh_pair(self):
        fresh = []
        for original in selected_records(self.catalogs['observations']):
            record = copy.deepcopy(original)
            record['id'] = 'synthetic_mos2_' + uuid4().hex
            record['name'] = 'SYNTHETIC TEST ONLY: ' + record['id']
            self.catalogs['observations']['records'].append(record)
            for language, labels in self.catalogs['locales']['languages'].items():
                labels['catalog_name_' + record['id']] = f'{language}: {record["name"]}'
            fresh.append(record)
        return fresh

    def test_full_validation_and_same_family_fresh_ids_allow_shifted_order(self):
        fresh = self.append_fresh_pair()
        before = copy.deepcopy(self.catalogs)
        counts = validate_catalogs(self.catalogs)
        self.assertEqual(counts, {kind: len(self.catalogs[kind]['records']) for kind in CATALOGS})
        self.assertEqual(self.catalogs, before)
        for kind in CATALOGS:
            self.catalogs[kind]['records'].reverse()
        self.assertEqual(validate_catalogs(self.catalogs), counts)
        with patched_catalogs(self.catalogs):
            source_records = query_catalog('observations', source_id=SOURCE)['records']
            self.assertTrue({record['id'] for record in fresh} | set(IDS)
                            <= {record['id'] for record in source_records})
            self.assertEqual(source_records, [record for record in self.catalogs['observations']['records']
                                              if SOURCE in {item['source_id'] for item in record['evidence']}])
            for record in fresh:
                filtered = query_catalog('observations', record_id=record['id'])
                self.assertEqual(filtered['records'], [record])
                for language in LANGUAGES:
                    label = self.catalogs['locales']['languages'][language]['catalog_name_' + record['id']]
                    self.assertEqual(query_catalog('observations', query=label)['records'], [record])
                    rendered = render_catalog(filtered, 'observations', language)
                    self.assertIn(label, rendered)
                    self.assertNotIn('[missing:', rendered)
                    self.assertIn('0.95', rendered)
                    self.assertIn('1.002168693051764', rendered)

    def test_missing_source_and_unsupported_appended_family_are_rejected(self):
        fresh = self.append_fresh_pair()
        validate_catalogs(self.catalogs)
        no_source = copy.deepcopy(self.catalogs)
        no_source['sources']['records'] = [record for record in no_source['sources']['records']
                                          if record['id'] != SOURCE]
        with self.assertRaisesRegex(CatalogValidationError, 'unresolved.*source'):
            validate_catalogs(no_source)
        for path, value in ((('method_family',), 'unreviewed_family_v1'),
                            (('study_id',), 'unreviewed_source'),
                            (('material', 'layer_count'), 2)):
            candidate = copy.deepcopy(self.catalogs)
            target = next(record for record in candidate['observations']['records']
                          if record['id'] == fresh[0]['id'])
            set_path(target, path, value)
            with self.subTest(path=path), self.assertRaises(CatalogValidationError):
                validate_catalogs(candidate)

    def test_new_ids_still_require_all_four_aliases_and_unique_ids(self):
        fresh = self.append_fresh_pair()
        candidate = copy.deepcopy(self.catalogs)
        del candidate['locales']['languages']['ja']['catalog_name_' + fresh[0]['id']]
        with self.assertRaises(CatalogValidationError):
            validate_catalogs(candidate)
        candidate = copy.deepcopy(self.catalogs)
        candidate['observations']['records'].append(copy.deepcopy(fresh[0]))
        with self.assertRaisesRegex(CatalogValidationError, 'duplicate record ID'):
            validate_catalogs(candidate)

    def test_required_mos2_notices_cannot_be_removed_in_every_language(self):
        # Removing every copy must fail independently of dictionary-key parity.
        for key in ('catalog_mos2_model_notice', 'catalog_mos2_source_notice',
                    'catalog_sd_notice', 'catalog_q_used', 'catalog_geometry_uncertainty_notice',
                    'catalog_probe_speed_notice', 'catalog_mos2_transcription_notice'):
            candidate = copy.deepcopy(self.catalogs)
            for labels in candidate['locales']['languages'].values():
                del labels[key]
            with self.subTest(key=key), self.assertRaises(CatalogValidationError):
                validate_catalogs(candidate)
        for language in LANGUAGES:
            candidate = copy.deepcopy(self.catalogs)
            candidate['locales']['languages'][language]['catalog_mos2_model_notice'] = ' '
            with self.subTest(language=language), self.assertRaises(CatalogValidationError):
                validate_catalogs(candidate)

    def test_evaluator_and_comparison_never_read_observations_or_overlay_them(self):
        expected = evaluate(example())
        real_read = read_catalog
        def guard(kind):
            if kind == 'observations':
                raise AssertionError('evaluation and comparison must not read observation records')
            return real_read(kind)
        with patch('materials_boundaries.catalog.read_catalog', side_effect=guard), \
             patch('materials_boundaries.visualization.read_catalog', side_effect=guard):
            self.assertEqual(evaluate(example()), expected)
            bundle = build_comparison([example()], fractions=[0, .5, 1])
            rendered = json.dumps(bundle) + render_html(bundle) + render_svg(bundle, bundle['cases'][0]['id'])
        self.assertEqual(len(bundle['series']), 8)
        self.assertNotIn('observations', bundle['catalogs'])
        for token in (*IDS, FAMILY, 'in_plane_stiffness_2d', 'breaking_strength_2d'):
            self.assertNotIn(token, rendered)
        for record in selected_records():
            with self.assertRaises(ValidationError):
                evaluate(record)
            with self.assertRaises((ValidationError, ValueError)):
                build_comparison([record], fractions=[0, 1])
            with self.assertRaises(CatalogLookupError):
                query_catalog('claims', record_id=record['id'])
        for field, value in (('quantity', 'in_plane_stiffness_2d'), ('unit', 'N/m')):
            candidate = copy.deepcopy(bundle)
            candidate['series'][0][field] = value
            with self.assertRaises(ValueError):
                validate_comparison(candidate)
        with self.assertRaises((ValidationError, ValueError)):
            evaluate(example(), output_unit='N/m')


class MoS2RuntimeGuardTests(unittest.TestCase):
    def test_malformed_critical_metadata_cannot_be_read_or_rendered(self):
        changes = [
            (('method_family',), 'unreviewed_family_v1'),
            (('model_status',), 'verified'),
            (('material', 'layer_count'), 2),
            (('reported_result', 'uncertainty', 'type'), 'standard_error'),
            (('reported_result', 'uncertainty', 'confidence_level'), .95),
            (('reported_result', 'uncertainty', 'scope'), 'independent_failures'),
            (('method', 'q_source_report', 'q_as_printed'), 1.002168693051764),
            (('method', 'q_source_report', 'fit_constant_actually_used'), .95),
            (('method', 'constitutive_model'), 'nonlinear_constitutive_finite_element'),
            (('method', 'inference_model'), 'lee_graphene_nonlinear_failure'),
            (('method', 'stress_measure'), 'second_piola_kirchhoff'),
            (('conditions', 'loading_rate', 'quantity'), 'strain_rate'),
            (('sample_metadata', 'counts', 'failure_events'), 9),
            (('sample_metadata', 'counts', 'force_displacement_curves'), 9),
            (('verification', 'source_inspection', 'supplement_inspected'), True),
            (('evaluation_support',), 'composite_evaluate'),
            (('si_unit',), 'GPa'),
        ]
        for original in selected_records():
            for path, value in changes:
                with self.subTest(record=original['id'], path=path):
                    record = copy.deepcopy(original)
                    set_path(record, path, value)
                    candidate = {'schema_version': '1.2.0', 'records': [record]}
                    with self.assertRaises(ValueError):
                        render_catalog(candidate, 'observations')
                    resource = Mock()
                    resource.joinpath.return_value.read_text.return_value = json.dumps(candidate)
                    with patch('materials_boundaries.catalog.files', return_value=resource), \
                         self.assertRaises(ValueError):
                        read_catalog('observations')

    def test_required_model_fields_cannot_be_omitted_from_filtered_output(self):
        for path in (('method_family',), ('model_status',),
                     ('method', 'q_source_report'), ('method', 'constitutive_model'),
                     ('method', 'inference_model'), ('verification', 'source_inspection')):
            record = copy.deepcopy(selected_records()[0])
            target = record
            for key in path[:-1]:
                target = target[key]
            del target[path[-1]]
            with self.subTest(path=path), self.assertRaises(ValueError):
                render_catalog({'schema_version': '1.2.0', 'records': [record]}, 'observations')


class MoS2QueryAndDisplayTests(unittest.TestCase):
    def test_source_quantity_id_and_literal_alias_filters(self):
        source_filtered = query_catalog('observations', source_id=SOURCE)
        self.assertTrue(set(IDS) <= {record['id'] for record in source_filtered['records']})
        for record in selected_records():
            filtered = query_catalog('observations', record_id=record['id'], source_id=SOURCE,
                                     quantity=record['quantity'],
                                     observation_type='experiment_derived_model_dependent')
            self.assertEqual(filtered['records'], [record])
            for language in LANGUAGES:
                alias = translate('catalog_name_' + record['id'], language)
                self.assertNotIn('[missing:', alias)
                self.assertIn(record, query_catalog('observations', query=alias)['records'])
                self.assertEqual(query_catalog('claims', query=alias)['records'], [])
        self.assertEqual(query_catalog('observations', record_id=IDS[0], quantity='breaking_strength_2d')['records'], [])

    def test_each_filtered_record_discloses_localized_model_warning_before_values(self):
        locales = read_catalog('locales')['languages']
        notices = ('catalog_mos2_model_notice', 'catalog_mos2_source_notice',
                   'catalog_sd_notice', 'catalog_geometry_uncertainty_notice',
                   'catalog_probe_speed_notice', 'catalog_mos2_transcription_notice')
        warning_anchors = {'en': 'UNRESOLVED', 'zh': '未解决', 'ja': '未解決', 'de': 'UNGEKLÄRTER'}
        sd_anchors = {'en': 'standard deviations', 'zh': '标准差', 'ja': '標準偏差', 'de': 'Standardabweichungen'}
        for language in LANGUAGES:
            self.assertIn(warning_anchors[language], locales[language]['catalog_mos2_model_notice'])
            self.assertIn('q = 0.95', locales[language]['catalog_mos2_model_notice'])
            self.assertIn('ν = 0.27', locales[language]['catalog_mos2_model_notice'])
            self.assertIn('A–G', locales[language]['catalog_mos2_source_notice'])
            self.assertIn(sd_anchors[language], locales[language]['catalog_sd_notice'])
            for key in notices:
                self.assertIn(key, locales[language])
                self.assertTrue(locales[language][key].strip())
                if language != 'en':
                    self.assertNotEqual(locales[language][key], locales['en'][key])
            for record in selected_records():
                with self.subTest(language=language, record=record['id']):
                    catalog = query_catalog('observations', record_id=record['id'])
                    before = copy.deepcopy(catalog)
                    text = render_catalog(catalog, 'observations', language)
                    self.assertEqual(catalog, before)
                    self.assertNotIn('[missing:', text)
                    result = record['reported_result']
                    displayed_value = f'{result["value"]} ± {result["uncertainty"]["value"]} N/m'
                    self.assertIn(displayed_value, text)
                    for key in notices:
                        self.assertIn(locales[language][key], text)
                    for key in ('catalog_mos2_model_notice', 'catalog_mos2_source_notice'):
                        self.assertLess(text.index(locales[language][key]), text.index(displayed_value))
                    self.assertIn(translate('catalog_status_reported_standard_deviation', language), text)
                    self.assertIn('reported_standard_deviation', text)
                    self.assertNotIn(translate('catalog_reported_uncertainty_notice', language), text)
                    for key in ('catalog_q_used', 'catalog_averaging_convention',
                                'catalog_coverage_factor', 'catalog_confidence_level',
                                'catalog_temperature', 'catalog_atmosphere', 'catalog_humidity',
                                'catalog_stress_measure', 'catalog_strain_measure',
                                'catalog_curve_count', 'catalog_failure_count',
                                'catalog_parent_flake_count'):
                        self.assertIn(translate(key, language) + ': ' + translate('unknown', language), text)
                    report = record['method']['q_source_report']
                    self.assertIn(report['formula_as_printed'], text)
                    self.assertIn(translate('catalog_q_nu', language) + ': 0.27', text)
                    self.assertIn(translate('catalog_q_reported', language) + ': 0.95', text)
                    self.assertIn(translate('catalog_q_arithmetic', language) + ': 1.002168693051764', text)
                    self.assertIn(translate('catalog_probe_speed', language) + ': 2 um/s', text)
                    self.assertIn(translate('catalog_study_monolayer_count', language) + ': 9', text)
                    self.assertIn('550 ± 10 nm', text)
                    self.assertIn('12 ± 2 nm', text)
                    self.assertIn(ARTIFACT_URL, text)
                    self.assertIn(DOI, text)
                    self.assertIn(record['evidence'][0]['locator'], text)
                    self.assertIn(record['id'], text)
                    self.assertIn(record['name'], text)
                    self.assertNotIn(IDS[1 - IDS.index(record['id'])], text)
                    if record['quantity'] == 'breaking_strength_2d':
                        self.assertNotIn(translate('catalog_stiffness_membrane_count', language) + ': 9', text)

    def test_filtered_graphene_does_not_acquire_mos2_sd_or_model_warning(self):
        for identifier in GRAPHENE_DIGESTS['observations']:
            for language in LANGUAGES:
                catalog = query_catalog('observations', record_id=identifier)
                text = render_catalog(catalog, 'observations', language)
                self.assertIn(translate('catalog_reported_uncertainty_notice', language), text)
                self.assertIn('reported_plus_minus_unspecified', text)
                self.assertNotIn(translate('catalog_mos2_model_notice', language), text)
                self.assertNotIn(translate('catalog_sd_notice', language), text)
                self.assertNotIn('reported_standard_deviation', text)

    def test_fresh_id_without_alias_has_safe_canonical_rendering_fallback(self):
        record = copy.deepcopy(selected_records()[0])
        record['id'] = 'synthetic_unaliased_' + uuid4().hex
        record['name'] = 'SYNTHETIC TEST ONLY: canonical display fallback'
        subset = {'schema_version': '1.2.0', 'records': [record]}
        for language in LANGUAGES:
            text = render_catalog(subset, 'observations', language)
            self.assertIn(record['id'], text)
            self.assertIn(record['name'], text)
            self.assertNotIn('[missing:', text)
            self.assertLess(text.index(translate('catalog_mos2_model_notice', language)),
                            text.index('180 ± 60 N/m'))

    def test_cli_text_filtered_by_id_and_quantity_keeps_warning_and_unknown_fit(self):
        for language in LANGUAGES:
            run = subprocess.run([
                sys.executable, '-m', 'materials_boundaries', 'catalog', 'observations',
                '--id', IDS[1], '--quantity', 'breaking_strength_2d', '--text', '--lang', language,
            ], cwd=ROOT, text=True, capture_output=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertNotIn('[missing:', run.stdout)
            self.assertIn('15 ± 3 N/m', run.stdout)
            self.assertNotIn('180 ± 60 N/m', run.stdout)
            self.assertLess(run.stdout.index(translate('catalog_mos2_model_notice', language)),
                            run.stdout.index('15 ± 3 N/m'))
            self.assertIn(translate('catalog_q_used', language) + ': ' + translate('unknown', language),
                          run.stdout)
            self.assertIn('PDF p. 5 (E)', run.stdout)

    def test_cli_json_stays_canonical_across_all_four_languages(self):
        outputs = []
        for language in LANGUAGES:
            run = subprocess.run([
                sys.executable, '-m', 'materials_boundaries', 'catalog', 'observations',
                '--source-id', SOURCE, '--json', '--lang', language,
            ], cwd=ROOT, text=True, capture_output=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            outputs.append(run.stdout)
        self.assertEqual(len(set(outputs)), 1)
        self.assertEqual(json.loads(outputs[0]), query_catalog('observations', source_id=SOURCE))


if __name__ == '__main__':
    unittest.main()
