"""Observation summaries are typed context, never bounds or executable inputs."""
import copy
import io
import json
import subprocess
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import patch

from materials_boundaries import evaluate, load_json, ValidationError
from materials_boundaries.catalog import CatalogLookupError, query_catalog, read_catalog
from materials_boundaries.catalog_output import render_catalog
from materials_boundaries.cli import main
from materials_boundaries.i18n import LANGUAGES, translate
from materials_boundaries.visualization import build_comparison, render_html, render_svg, validate_comparison
from catalog_fixtures import evidence_for, historical_catalog, historical_records, isolated_catalogs
from catalog_fixtures import expected_provenance
from test_engine import ROOT, example
try:
    from jsonschema import Draft202012Validator, FormatChecker
except ImportError:
    Draft202012Validator = None

IDS = ['lee_2008_graphene_in_plane_stiffness_2d', 'lee_2008_graphene_breaking_strength_2d']
SOURCE = 'lee_wei_kysar_hone_2008'


def ids(catalog):
    return [r['id'] for r in catalog['records']]


class ObservationCatalogTests(unittest.TestCase):
    def test_historical_observation_records_and_catalog_separation(self):
        claims, sources, observations = [read_catalog(k) for k in ('claims', 'sources', 'observations')]
        self.assertEqual([c['schema_version'] for c in (claims, sources, observations)], ['1.13.0', '1.0.0', '1.3.0'])
        self.assertTrue(set(IDS).issubset(ids(observations)))
        self.assertIn(SOURCE, ids(sources))
        self.assertTrue(set(ids(claims)).isdisjoint(IDS))

    def test_two_properties_reference_one_study_not_two_replications(self):
        records = historical_records('observations', IDS)
        self.assertEqual({r['study_id'] for r in records}, {SOURCE})
        self.assertTrue(all(SOURCE in {e['source_id'] for e in r['evidence']} for r in records))
        source_ids = ids(read_catalog('sources'))
        for r in records:
            self.assertEqual(r['study_id'], evidence_for(r, SOURCE)['source_id'])
            self.assertIn(r['study_id'], source_ids)
            self.assertEqual(r['verification']['independent_scientific_review'], expected_provenance('observations', r['id'])['verification']['independent_scientific_review'])
            self.assertTrue(any('not independent confirmations' in s for s in r['limits']))

    def test_reported_quantities_values_units_and_uninterpreted_uncertainty(self):
        for r, quantity, value, error in zip(historical_records('observations', IDS),
            ['in_plane_stiffness_2d', 'breaking_strength_2d'], [340, 42], [50, 4]):
            self.assertEqual((r['quantity'], r['quantity_dimension'], r['si_unit']), (quantity, 'force_per_length', 'N/m'))
            self.assertEqual(r['observation_type'], 'experiment_derived_model_dependent')
            self.assertEqual(r['reported_result']['value'], value)
            u = r['reported_result']['uncertainty']
            self.assertEqual((u['value'], u['unit'], u['notation'], u['type']), (error, 'N/m', 'plus_minus', 'reported_plus_minus_unspecified'))
            self.assertIsNone(u['confidence_level']); self.assertIsNone(u['coverage_factor'])
            for forbidden in ('lower', 'upper', 'standard_deviation', 'standard_error'):
                self.assertNotIn(forbidden, r['reported_result']); self.assertNotIn(forbidden, u)
            self.assertEqual(r['evaluation_support'], 'catalog_only')
            for forbidden in ('claim_type', 'bound_kind', 'direction', 'rule_id', 'formula_display', 'result', 'checks', 'applicability', 'computation'):
                self.assertNotIn(forbidden, r)

    def test_stiffness_distribution_is_separate_and_not_copied_to_failure(self):
        stiff, strength = historical_records('observations', IDS)
        sample = stiff['sample_metadata']
        self.assertEqual(sample['scope'], 'stiffness_force_displacement_fits')
        self.assertEqual(sample['counts'], {'force_displacement_fits': 67, 'membranes': 23, 'flakes': 2})
        self.assertEqual(sample['fitted_distribution'], {'mean': 342, 'standard_deviation': 30, 'unit': 'N/m'})
        self.assertNotEqual(sample['fitted_distribution']['standard_deviation'], stiff['reported_result']['uncertainty']['value'])
        self.assertIsNone(strength['sample_metadata'])
        self.assertTrue(any('counts are not verified' in s for s in strength['verification']['gaps']))
        self.assertIn('p. 386 final paragraph', evidence_for(stiff, SOURCE)['locator'])
        self.assertIn('p. 387 opening', evidence_for(stiff, SOURCE)['locator'])

    def test_material_conditions_and_property_specific_model_scope(self):
        stiff, strength = historical_records('observations', IDS)
        for r in (stiff, strength):
            self.assertEqual(r['material']['dimensionality'], 2)
            self.assertEqual(r['material']['layer_count'], 1)
            self.assertEqual(r['material']['preparation'], 'mechanically_deposited_graphite_flakes')
            self.assertEqual(r['material']['suspended_span_diameters'], {'values': [1, 1.5], 'unit': 'um'})
            self.assertEqual(r['material']['monolayer_identification'], ['optical_microscopy', 'raman_spectroscopy'])
            self.assertEqual(r['conditions'], dict(temperature=None, atmosphere=None, humidity=None, loading_rate=None, verification_status='not_verified'))
            self.assertEqual(r['method']['poissons_ratio_assumed'], .165)
            self.assertEqual(r['method']['stress_measure'], 'second_piola_kirchhoff')
            self.assertEqual(r['method']['strain_measure'], 'lagrangian')
            self.assertTrue(any('not independent imaging proof' in s for s in r['limits']))
        self.assertIn('point-load approximation in Eq. (2)', stiff['method']['model_assumptions'][0])
        self.assertIn('finite-radius', strength['method']['model_assumptions'][0])
        self.assertIn('not the point-load approximation', strength['method']['model_assumptions'][0])
        self.assertIn('finite-element', strength['method']['inference'])
        self.assertIn('-E2D^2/(4*D2D)', strength['method']['inference'])
        self.assertIn('p. 387 final-column', evidence_for(strength, SOURCE)['locator'])
        self.assertIn('p. 388 opening', evidence_for(strength, SOURCE)['locator'])

    def test_source_bibliography_rights_and_inspection_limits(self):
        r = query_catalog('sources', record_id=SOURCE)['records'][0]
        self.assertEqual(r['authors'], ['Changgu Lee', 'Xiaoding Wei', 'Jeffrey W. Kysar', 'James Hone'])
        self.assertEqual((r['doi'], r['year']), ('10.1126/science.1157996', 2008))
        self.assertEqual(r['read_status'], expected_provenance('sources', r['id'])['read_status'])
        self.assertEqual(r['license'], expected_provenance('sources', r['id'])['license'])
        self.assertEqual(r['bundled_content'], expected_provenance('sources', r['id'])['bundled_content'])
        self.assertEqual(r['role'], 'experimental_observation_primary_source')
        self.assertIn('https://pubmed.ncbi.nlm.nih.gov/18635798/', r['urls'])
        notes = ' '.join(r['claim_notes'])
        for phrase in ('18 July 2008', 'one experimental study', 'all rights reserved', 'not claimed as inspected', 'no PDF, figures or raw observations'):
            self.assertIn(phrase, notes)

    def test_catalog_and_comparison_boundaries_are_separate(self):
        original = evaluate(example())
        self.assertEqual(len(original['evaluations']), 8)
        # Even malformed/hostile observations cannot influence the calculator.
        real_read = read_catalog
        def guard(name):
            if name == 'observations':
                raise AssertionError('calculator/visualization must not load observations')
            return real_read(name)
        with patch('materials_boundaries.catalog.read_catalog', side_effect=guard), patch('materials_boundaries.visualization.read_catalog', side_effect=guard):
            self.assertEqual(evaluate(example()), original)
            bundle = build_comparison([example()], fractions=[0, .5, 1])
            self.assertEqual(len(bundle['series']), 8)
            text = json.dumps(bundle) + render_html(bundle) + render_svg(bundle, bundle['cases'][0]['id'], 'effective_youngs_modulus')
        # A study source can later support a claim too; observations themselves
        # must still never become executable claims or comparison quantities.
        for id in [*IDS, 'in_plane_stiffness_2d', 'breaking_strength_2d']:
            self.assertNotIn(id, text)
        self.assertNotIn('observations', bundle['catalogs'])

    def test_observation_records_cannot_be_inputs_or_pressure_output_units(self):
        for r in read_catalog('observations')['records']:
            with self.assertRaises(ValidationError): evaluate(r)
            with self.assertRaises((ValidationError, ValueError)): build_comparison([r], fractions=[0, 1])
        with self.assertRaises((ValidationError, ValueError)): evaluate(example(), output_unit='N/m')
        bundle = build_comparison([example()], fractions=[0, 1])
        for key, value in [('quantity', 'in_plane_stiffness_2d'), ('unit', 'N/m')]:
            bad = copy.deepcopy(bundle); bad['series'][0][key] = value
            with self.assertRaises(ValueError): validate_comparison(bad)

    def test_observations_never_become_a_claim_search_match(self):
        with isolated_catalogs():
            self.assertEqual(query_catalog('claims', source_id=SOURCE)['records'], [])
            for id in IDS:
                with self.assertRaises(CatalogLookupError): query_catalog('claims', record_id=id)
            self.assertEqual(query_catalog('observations', query='universal')['records'], [])


class ObservationQueryAndDisplayTests(unittest.TestCase):
    def test_read_query_copy_and_stable_envelope(self):
        baseline = read_catalog('observations')
        self.assertEqual(query_catalog('observations'), baseline)
        self.assertEqual(set(baseline), {'schema_version', 'records'})
        for lang in LANGUAGES:
            render_catalog(baseline, 'observations', lang)
        self.assertEqual(baseline, read_catalog('observations'))
        record_id = baseline['records'][0]['id']
        original_value = baseline['records'][0]['reported_result']['value']
        baseline['records'][0]['reported_result']['value'] = 999
        self.assertEqual(query_catalog('observations', record_id=record_id)['records'][0]['reported_result']['value'], original_value)

    def test_exact_id_filters_and_literal_query(self):
        with isolated_catalogs() as catalogs:
            self.assertEqual(ids(query_catalog('observations', source_id=SOURCE)), IDS)
            self.assertEqual(ids(query_catalog('observations', quantity='breaking_strength_2d')), IDS[1:])
            self.assertEqual(ids(query_catalog('observations', observation_type='experiment_derived_model_dependent')), IDS)
            self.assertEqual(ids(query_catalog('observations', query='GRAPHENE stiffness lee_wei')), IDS[:1])
            self.assertEqual(ids(query_catalog('observations', record_id=IDS[0], quantity='breaking_strength_2d')), [])
            for q in ('340', '.*', 'standard_deviation', 'finite-element', '10.1126/science.1157996'):
                self.assertEqual(query_catalog('observations', query=q)['records'], [])
            for q in (None, '', ' \n\t '):
                self.assertEqual(query_catalog('observations', query=q), catalogs['observations'])
            for kw in ({'quantity': 'IN_PLANE_STIFFNESS_2D'}, {'source_id': SOURCE.upper()}, {'quantity': 'no_such_quantity'}):
                self.assertEqual(query_catalog('observations', **kw)['records'], [])
            with self.assertRaises(CatalogLookupError): query_catalog('observations', record_id='not_present')

    def test_all_localized_names_are_literal_aliases(self):
        with isolated_catalogs() as catalogs:
            labels = catalogs['locales']['languages']
            for lang in LANGUAGES:
                for id in IDS:
                    self.assertEqual(ids(query_catalog('observations', query=labels[lang]['catalog_name_'+id])), [id])
                    self.assertEqual(ids(query_catalog('claims', query=labels[lang]['catalog_name_'+id])), [])

    def test_invalid_cross_catalog_filters_and_argument_types(self):
        invalid = [
            ('observations', {'direction':'upper'}), ('observations', {'claim_type':'theoretical_bound'}),
            ('observations', {'role':'x'}), ('observations', {'year':2008}), ('observations', {'license':'x'}),
            ('claims', {'quantity':'x'}), ('sources', {'quantity':'x'}),
            ('claims', {'observation_type':'experiment_derived_model_dependent'}),
            ('sources', {'observation_type':'experiment_derived_model_dependent'}),
            ('observations', {'observation_type':'theoretical_bound'}), ('observations', {'observation_type':[]} ),
            ('observations', {'quantity':1}), ('observations', {'quantity':''}), ('observations', {'quantity':'  '}),
            ('observations', {'query':1}), ('observations', {'source_id':False}),
        ]
        for kind, kwargs in invalid:
            with self.subTest(kind=kind, kwargs=kwargs), self.assertRaises(ValueError): query_catalog(kind, **kwargs)

    def test_four_language_disclosures_and_original_data_are_visible(self):
        catalog = read_catalog('observations')
        for lang in LANGUAGES:
            text = render_catalog(catalog, 'observations', lang)
            self.assertNotIn('[missing:', text)
            for key in ('catalog_observations', 'catalog_observation_notice', 'catalog_reported_uncertainty_notice',
                        'catalog_observation_compatibility_notice', 'catalog_study_id', 'catalog_distribution_sd',
                        'catalog_coverage_factor', 'catalog_confidence_level', 'catalog_sample_metadata', 'translation_review_notice'):
                self.assertIn(translate(key, lang), text)
            for key in ('catalog_coverage_factor', 'catalog_confidence_level', 'catalog_temperature', 'catalog_loading_rate'):
                self.assertIn(translate(key, lang)+': '+translate('unknown', lang), text)
            for r in catalog['records']:
                self.assertIn(r['name'], text)
                self.assertIn(r['id'], text)
                self.assertIn(r['evidence'][0]['locator'], text)
            for literal in ('340 ± 50 N/m', '42 ± 4 N/m', '342 N/m', '30 N/m', '10.1126/science.1157996'):
                self.assertIn(literal, text)

    def test_cli_json_is_identical_across_languages_and_filters(self):
        outputs=[]
        for lang in LANGUAGES:
            run=subprocess.run([sys.executable,'-m','materials_boundaries','catalog','observations','--source-id',SOURCE,
                                '--observation-type','experiment_derived_model_dependent','--json','--lang',lang],cwd=ROOT,text=True,capture_output=True)
            self.assertEqual(run.returncode,0,run.stderr);outputs.append(run.stdout)
        self.assertEqual(len(set(outputs)),1)
        self.assertEqual(json.loads(outputs[0]), query_catalog('observations', source_id=SOURCE,
                         observation_type='experiment_derived_model_dependent'))
        run=subprocess.run([sys.executable,'-m','materials_boundaries','catalog','observations','--id',IDS[1],'--quantity','breaking_strength_2d','--text','--lang','zh'],cwd=ROOT,text=True,capture_output=True)
        self.assertEqual(run.returncode,0,run.stderr);self.assertIn('42 ± 4 N/m',run.stdout);self.assertNotIn('340 ± 50 N/m',run.stdout)

    def test_cli_empty_wrong_kind_and_unknown_id(self):
        for args, code in [(['--id','missing'],2),(['--direction','upper'],2),(['--year','2008'],2),(['--query','missing'],0)]:
            stdout, stderr = io.StringIO(), io.StringIO()
            with isolated_catalogs(), redirect_stdout(stdout), redirect_stderr(stderr):
                actual = main(['catalog', 'observations', *args])
            self.assertEqual(actual, code, stderr.getvalue())
            if code == 0:
                self.assertEqual(json.loads(stdout.getvalue()), {'schema_version': read_catalog('observations')['schema_version'], 'records': []})


@unittest.skipIf(Draft202012Validator is None, 'optional jsonschema dev dependency not installed')
class ObservationSchemaTests(unittest.TestCase):
    def setUp(self):
        self.catalog = historical_catalog('observations')
        schema = load_json(ROOT/'schemas/observations.schema.json')
        Draft202012Validator.check_schema(schema)
        self.validator = Draft202012Validator(schema, format_checker=FormatChecker())

    def invalid(self, mutation, index=0):
        bad = copy.deepcopy(self.catalog); mutation(bad['records'][index])
        self.assertTrue(list(self.validator.iter_errors(bad)))

    def test_schema_accepts_canonical_catalog_and_empty_query(self):
        self.validator.validate(read_catalog('observations'))
        self.validator.validate({'schema_version': self.catalog['schema_version'], 'records': []})

    def test_no_execution_bound_or_generic_pressure_type_can_be_added(self):
        for key, value in [('observation_type','theoretical_bound'),('evaluation_support','composite_evaluate'),
                           ('quantity','effective_youngs_modulus'),('quantity_dimension','pressure'),('si_unit','Pa'),
                           ('claim_type','model_estimate'),('direction','upper'),('rule_id','voigt_bulk_v1')]:
            self.invalid(lambda r:r.update({key:value}))
        self.invalid(lambda r:r['reported_result'].update(unit='GPa'))
        self.invalid(lambda r:r['reported_result']['uncertainty'].update(unit='Pa'))
        self.invalid(lambda r:r['material'].update(dimensionality=3))
        self.invalid(lambda r:r['material']['suspended_span_diameters'].update(unit='mm'))

    def test_unspecified_plus_minus_cannot_be_promoted_to_statistical_claim(self):
        for field, value in [('type','standard_deviation'),('type','confidence_interval'),('confidence_level',.95),
                             ('coverage_factor',2),('lower',290),('upper',390),('standard_error',50)]:
            self.invalid(lambda r:r['reported_result']['uncertainty'].update({field:value}))
        for value in (-1, True, None, '50'):
            self.invalid(lambda r:r['reported_result']['uncertainty'].update(value=value))
        self.invalid(lambda r:r['reported_result'].update(lower=290,upper=390))

    def test_property_specific_samples_are_not_interchangeable(self):
        self.invalid(lambda r:r.update(sample_metadata=copy.deepcopy(self.catalog['records'][0]['sample_metadata'])),index=1)
        self.invalid(lambda r:r.update(sample_metadata=None))
        self.invalid(lambda r:r['sample_metadata']['counts'].update(membranes=0))
        self.invalid(lambda r:r['sample_metadata']['counts'].update(membranes=True))
        self.invalid(lambda r:r['sample_metadata']['fitted_distribution'].update(standard_deviation=-30))
        self.invalid(lambda r:r['sample_metadata']['fitted_distribution'].update(unit='GPa'))

    def test_unknown_conditions_cannot_be_silently_filled_or_verified(self):
        for key in ('temperature','atmosphere','humidity','loading_rate'):
            self.invalid(lambda r:r['conditions'].update({key:0}))
        self.invalid(lambda r:r['conditions'].update(verification_status='verified'))
        self.invalid(lambda r:r['verification'].update(independent_scientific_review=True))
        self.invalid(lambda r:r['verification'].update(status='full_text_and_supplement_verified'))

    def test_required_traceability_and_conventions_cannot_be_removed(self):
        for key in ('study_id','evidence','reported_result','conditions','sample_metadata','method','material','limits'):
            self.invalid(lambda r:r.pop(key))
        self.invalid(lambda r:r.update(evidence=[]))
        self.invalid(lambda r:r['evidence'][0].update(source_id=''))
        self.invalid(lambda r:r['method'].update(stress_measure='cauchy'))
        self.invalid(lambda r:r['method'].update(strain_measure='engineering'))
        self.invalid(lambda r:r['method'].update(poissons_ratio_assumed=True))


if __name__ == '__main__':
    unittest.main()
