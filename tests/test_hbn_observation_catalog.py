"""Falin source facts, component-level provenance and closed-family protections.

These are source-transcription/software tests, not replication or raw-data
reanalysis. No source PDF, source full text or local audit path is required.
"""
import copy
import hashlib
import json
import subprocess
import sys
import unittest
from unittest.mock import Mock, patch
from uuid import uuid4

from jsonschema import Draft202012Validator
from materials_boundaries import ValidationError, evaluate, load_json
from materials_boundaries._hbn_observation_contract import HBN_FAMILY, HBN_SOURCE, HBN_REVIEW
from materials_boundaries.catalog import read_catalog, query_catalog, CatalogLookupError
from materials_boundaries.catalog_output import render_catalog
from materials_boundaries.i18n import LANGUAGES, translate
from materials_boundaries.visualization import build_comparison, render_html, render_svg
from scripts.validate_catalogs import load_catalogs, validate_catalogs, CatalogValidationError
from test_engine import ROOT, example
from test_mos2_observation_catalog import set_path, patched_catalogs

IDS = ('falin_2017_hbn_monolayer_in_plane_stiffness_2d',
       'falin_2017_hbn_monolayer_breaking_strength_2d')


def records():
    index = {r['id']: r for r in read_catalog('observations')['records']}
    return [index[i] for i in IDS]


def subset(record):
    return {'schema_version': '1.2.0', 'records': [record]}


class HBNSourceFacts(unittest.TestCase):
    def test_two_selected_source_values_and_distinct_statistics(self):
        self.assertEqual(read_catalog('observations')['schema_version'], '1.2.0')
        for r, value, sd, stat in zip(records(), (289, 23.6), (24, 1.8),
                                     ('reported_average', 'reported_strength_summary')):
            self.assertEqual((r['method_family'], r['study_id']), (HBN_FAMILY, HBN_SOURCE))
            self.assertEqual((r['quantity_dimension'], r['si_unit'], r['evaluation_support']),
                             ('force_per_length', 'N/m', 'catalog_only'))
            result = r['reported_result']
            self.assertEqual((result['value'], result['uncertainty']['value'], result['unit'], result['summary_statistic']),
                             (value, sd, 'N/m', stat))
            u = result['uncertainty']
            self.assertEqual((u['type'], u['definition_basis']),
                             ('reported_standard_deviation', 'publisher_peer_review_author_response'))
            self.assertEqual(u['evidence']['source_url'], HBN_REVIEW)
            self.assertEqual(u['evidence']['locator'], 'PDF p. 8, Reviewer #1 question 3, author response')
            for key in ('confidence_level', 'coverage_factor', 'averaging_convention'):
                self.assertIsNone(u[key])
        self.assertIsNone(records()[1]['reported_result']['central_statistic_explicitly_named'])

    def test_stiffness_q_arithmetic_is_not_a_reported_or_used_constant(self):
        m = records()[0]['method'];q = m['q_source_report']
        self.assertEqual(m['poissons_ratio_assumed'], .211)
        self.assertEqual(q['formula_as_printed'], 'q = 1/(1.049 − 0.15ν − 0.16ν²)')
        self.assertAlmostEqual(q['audit_arithmetic_value'], 1/(1.049-.15*.211-.16*.211**2), places=15)
        self.assertIsNone(q['q_as_printed']);self.assertIsNone(q['fit_constant_actually_used'])
        self.assertEqual(m['fit_force_law']['formula_as_printed'], 'F = σ₀²ᴰ(πa)(δ/a) + E²ᴰ(q³a)(δ/a)³')
        self.assertEqual(m['inference_model'], 'circular_membrane_force_deflection_fit')
        self.assertNotIn('finite_element_model', m)

    def test_strength_volume_average_is_not_diagnostic_maximum(self):
        m = records()[1]['method'];f = m['finite_element_model']
        self.assertEqual(m['constitutive_relation']['formula_as_printed'], 'σ = Eε + Dε²')
        self.assertEqual(m['constitutive_relation']['E']['value'], 865)
        self.assertEqual(m['constitutive_relation']['D']['value'], -2035)
        self.assertEqual(f['strength_reduction'], 'volume_average_of_under_indenter_element_stresses_at_experimental_fracture_load')
        self.assertIsNone(f['reported_stress_component_or_invariant_for_this_average'])
        self.assertEqual(m['diagnostic_not_selected_result']['plotted_quantity'], 'maximum Von Mises stress')
        self.assertNotIn('q_source_report', m)
        for r in records():
            self.assertIsNone(r['method']['stress_measure']);self.assertIsNone(r['method']['strain_measure'])
            self.assertEqual(r['method']['effective_thickness_convention']['value'], .334)
            self.assertEqual(r['material']['example_afm_apparent_height']['value'], .48)

    def test_sheet_count_and_typical_protocol_do_not_create_failures_or_curves(self):
        for r in records():
            s = r['sample_metadata'];c = s['counts']
            self.assertEqual(c['study_monolayer_tested_sheets'], 11)
            for key in ('force_displacement_curves_acquired', 'force_displacement_curves_retained',
                        'force_displacement_curves_excluded', 'distinct_parent_flakes', 'failure_events'):
                self.assertIsNone(c[key])
            self.assertEqual(s['typical_protocol']['indentations_per_sheet_typically'], 5)
            self.assertIs(s['typical_protocol']['exact_count'], False)
            self.assertEqual(s['count_definition_source']['source_url'], HBN_REVIEW)
        self.assertEqual(records()[0]['sample_metadata']['counts']['tested_sheets_explicitly_associated_with_stiffness_average'], 11)
        self.assertNotIn('tested_sheets_explicitly_associated_with_stiffness_average', records()[1]['sample_metadata']['counts'])

    def test_ambient_and_translation_velocity_leave_numerical_environment_unknown(self):
        for r in records():
            c=r['conditions']
            for key in ('temperature', 'atmosphere', 'humidity', 'pressure'):
                self.assertIsNone(c[key])
            self.assertEqual(c['environment_description'], 'ambient conditions')
            self.assertEqual((c['loading_rate']['quantity'], c['loading_rate']['value'], c['loading_rate']['unit']),
                ('reported_loading_and_unloading_translation_velocity', .5, 'um/s'))
            self.assertIsNone(c['loading_rate']['strain_rate'])

    def test_inspection_and_component_rights_are_not_overstated(self):
        for r in records():
            v=r['verification'];i=v['source_inspection']
            for key in ('main_pdf_inspected','raw_data_reanalysis','plot_digitization','independent_replication'):
                self.assertIs(i[key], False)
            self.assertIs(v['independent_scientific_review'], False)
            self.assertEqual(i['supplement_visual_pages'], [4,5]);self.assertEqual(i['peer_review_visual_pages'], [8])
            self.assertEqual({e['artifact'] for e in r['evidence']}, {'publisher_html','supplement','peer_review_author_response'})
            self.assertTrue(all(e['source_id']==HBN_SOURCE for e in r['evidence']))
        source=query_catalog('sources',record_id=HBN_SOURCE)['records'][0]
        self.assertEqual(source['doi'],'10.1038/ncomms15815')
        self.assertEqual(source['license']['identifier'],'CC-BY-4.0')
        self.assertEqual(len(source['authors']),14)
        notes=' '.join(source['claim_notes'])
        self.assertIn('peer-review',notes);self.assertIn('license',notes)

    def test_all_old_record_objects_are_preserved(self):
        fixture=load_json(ROOT/'tests/fixtures/pre_hbn_record_digests.json')
        for kind, expected in fixture.items():
            index={r['id']:r for r in read_catalog(kind)['records']}
            for identifier,digest in expected.items():
                with self.subTest(kind=kind,id=identifier):
                    record=copy.deepcopy(index[identifier])
                    if kind == 'claims':
                        # Evidence can accumulate on an existing claim. Restore
                        # only the exact, individually hashed baseline members
                        # in their baseline order for a full-record comparison;
                        # never discard or normalize historical source facts.
                        evidence_by_digest={}
                        for item in record['evidence']:
                            item_digest=hashlib.sha256(json.dumps(item,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
                            evidence_by_digest.setdefault(item_digest,[]).append(item)
                        for item_digest in digest['evidence_sha256']:
                            self.assertEqual(len(evidence_by_digest.get(item_digest,[])),1)
                        record['evidence']=[evidence_by_digest[key][0] for key in digest['evidence_sha256']]
                        digest=digest['record_sha256']
                    actual=hashlib.sha256(json.dumps(record,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
                    self.assertEqual(actual,digest)


class HBNContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.validator=Draft202012Validator(load_json(ROOT/'schemas/observations.schema.json'))

    def invalid(self, changes, indices=(0,1)):
        for index in indices:
            for path,value in changes:
                with self.subTest(index=index,path=path,value=value):
                    r=copy.deepcopy(records()[index]);set_path(r,path,value);candidate=subset(r)
                    self.assertTrue(list(self.validator.iter_errors(candidate)))
                    with self.assertRaises(ValueError):render_catalog(candidate,'observations')
                    resource=Mock();resource.joinpath.return_value.read_text.return_value=json.dumps(candidate)
                    with patch('materials_boundaries.catalog.files',return_value=resource),self.assertRaises(ValueError):
                        read_catalog('observations')

    def test_family_units_method_and_conversion_mutations_fail(self):
        self.invalid([(('method_family',),'arbitrary_family'),(('model_status',),'validated'),
            (('si_unit',),'GPa'),(('quantity_dimension',),'pressure'),(('quantity',),'youngs_modulus_3d'),
            (('evaluation_support',),'composite_evaluate'),(('quantity',),[]),(('quantity',),{}),
            (('material','layer_count'),True),
            (('material','layer_count'),2),(('material','formula'),'MoS2'),
            (('material','default_thickness'),.334),(('method','poissons_ratio_assumed'),.27),
            (('method','stress_measure'),'second_piola_kirchhoff'),(('method','strain_measure'),'lagrangian'),
            (('reported_result','value'),True),(('reported_result','unit'),'Pa'),
            (('reported_result','uncertainty','unit'),'GPa'),(('reported_result','uncertainty','value'),-1),
            (('reported_result','uncertainty','coverage_factor'),1),(('reported_result','uncertainty','confidence_level'),.68),
            (('reported_result','uncertainty','averaging_convention'),'equal_weight'),
            (('reported_result','uncertainty','type'),'standard_error')])

    def test_source_component_sd_provenance_is_required(self):
        prefix=('reported_result','uncertainty')
        self.invalid([(prefix+('definition_basis',),'publisher_main_text'),
            (prefix+('evidence','artifact'),'publisher_html'),(prefix+('evidence','source_url'),'https://www.nature.com/articles/ncomms15815'),
            (prefix+('evidence','locator'),'Main text Fig. 3'),(prefix+('evidence','source_id'),'lee_wei_kysar_hone_2008'),
            (prefix+('evidence','verification_status'),'publisher_main_text_passage_checked'),
            (('sample_metadata','count_definition_source','artifact'),'publisher_html'),
            (('verification','source_inspection','main_pdf_inspected'),True),
            (('verification','source_inspection','independent_replication'),True),
            (('verification','independent_scientific_review'),True)])

    def test_counts_rates_unknowns_and_scope_do_not_leak(self):
        changes=[(('sample_metadata','counts',k),55) for k in
                 ('force_displacement_curves_acquired','force_displacement_curves_retained','force_displacement_curves_excluded')]
        changes += [(('sample_metadata','counts','failure_events'),11),
            (('sample_metadata','typical_protocol','exact_count'),True),
            (('conditions','loading_rate','quantity'),'strain_rate'),(('conditions','loading_rate','value'),.1),
            (('conditions','loading_rate','unit'),'s^-1'),(('conditions','loading_rate','strain_rate'),.5),
            (('conditions','environment_description'),'controlled ambient')]
        changes += [(('conditions',k),v) for k,v in [('temperature',298.15),('humidity',.5),('pressure',101325),('atmosphere','air')]]
        self.invalid(changes)
        self.invalid([(('sample_metadata','counts','tested_sheets_explicitly_associated_with_stiffness_average'),11)],indices=(1,))

    def test_property_specific_models_cannot_be_interchanged(self):
        self.invalid([(('method','q_source_report','q_as_printed'),.9898768854482001),
            (('method','q_source_report','fit_constant_actually_used'),.9898768854482001),
            (('method','q_source_report','nu_as_printed'),.27),
            (('method','q_source_report','audit_arithmetic_value'),.95),
            (('method','fit_force_law','formula_as_printed'),'linear only')],indices=(0,))
        self.invalid([(('method','finite_element_model','strength_reduction'),'maximum_von_mises'),
            (('method','finite_element_model','reported_stress_component_or_invariant_for_this_average'),'von_mises'),
            (('method','constitutive_relation','D','value'),2035),
            (('method','finite_element_model','contact'),'bonded'),
            (('method','diagnostic_not_selected_result','plotted_quantity'),'volume_average'),
            (('reported_result','central_statistic_explicitly_named'),'mean')],indices=(1,))

    def test_missing_caveats_and_evidence_fail(self):
        self.invalid([(('limits',),[]),(('verification','gaps'),[]),(('method','model_assumptions'),[]),
                      (('evidence',),[]),(('method','stress_strain_measure_status'),'')])
        for field in ('method_family','method','conditions','reported_result','sample_metadata','verification'):
            candidate=subset(copy.deepcopy(records()[0]));del candidate['records'][0][field]
            self.assertTrue(list(self.validator.iter_errors(candidate)))
            with self.assertRaises(ValueError):render_catalog(candidate,'observations')

    def test_source_prose_cannot_reverse_scientific_caveats(self):
        self.invalid([(('method','stress_strain_measure_status'),'Known second Piola/Lagrangian'),
            (('method','effective_thickness_convention','selected_2d_values_status'),'Computed by default thickness'),
            (('reported_result','uncertainty','interpretation'),'SEM defined by main text'),
            (('reported_result','source_value_string'),'recomputed value'),
            (('evidence',0,'locator'),'unknown location'),
            (('evidence',0,'verified_as'),'independent replication')])

    def test_relabeling_cannot_escape_family_dispatch(self):
        from materials_boundaries._observation_contract import validate_observation_records
        for original in records():
            r=copy.deepcopy(original);del r['method_family']
            r['study_id']='lee_wei_kysar_hone_2008';r['material']['formula']='C'
            with self.assertRaises(ValueError):validate_observation_records([r])
            for key in ('material','method','evidence'):
                r=copy.deepcopy(original);r[key]=None
                with self.subTest(key=key),self.assertRaises(ValueError):
                    validate_observation_records([r])
        # JSON Schema regards integral JSON floats as the same numeric values;
        # the dependency-free guard normalizes those, without conflating bool.
        r=copy.deepcopy(records()[0]);r['reported_result']['value']=289.0
        r['material']['layer_count']=1.0
        validate_observation_records([r]);self.validator.validate(subset(r))

    def test_required_hbn_notices_cannot_be_dropped(self):
        from materials_boundaries._hbn_observation_contract import HBN_LABELS
        c=load_catalogs(ROOT/'materials_boundaries/data')
        for key in ('catalog_hbn_sd_notice','catalog_hbn_count_notice','catalog_hbn_model_notice',
                    'catalog_hbn_rights_notice','catalog_hbn_velocity_notice','catalog_hbn_stress_strain_notice'):
            self.assertIn(key,HBN_LABELS)
            candidate=copy.deepcopy(c)
            for labels in candidate['locales']['languages'].values():del labels[key]
            with self.subTest(key=key),self.assertRaises(CatalogValidationError):validate_catalogs(candidate)

    def test_same_family_ids_and_reversed_evidence_are_appendable(self):
        c=load_catalogs(ROOT/'materials_boundaries/data');fresh=[]
        for original in records():
            r=copy.deepcopy(original);r['id']='synthetic_hbn_'+uuid4().hex;r['name']='Synthetic test fixture '+r['id']
            r['evidence'].reverse();c['observations']['records'].append(r);fresh.append(r)
            for lang,labels in c['locales']['languages'].items():labels['catalog_name_'+r['id']]=lang+': '+r['name']
        for kind in ('claims','sources','observations'):c[kind]['records'].reverse()
        before=copy.deepcopy(c);validate_catalogs(c);self.assertEqual(c,before)
        with patched_catalogs(c):
            for r in fresh:
                self.assertEqual(query_catalog('observations',record_id=r['id'])['records'],[r])
                for language in LANGUAGES:
                    text=render_catalog(subset(r),'observations',language)
                    self.assertIn(r['name'],text);self.assertNotIn('[missing:',text)
        del c['locales']['languages']['ja']['catalog_name_'+fresh[0]['id']]
        with self.assertRaises(CatalogValidationError):validate_catalogs(c)

    def test_unknown_family_cannot_route_to_mos2_or_graphene(self):
        self.invalid([(('method_family',),'unreviewed_v1')])
        r=copy.deepcopy(read_catalog('observations')['records'][0]);r['method_family']='unreviewed_v1'
        with self.assertRaises(ValueError):render_catalog(subset(r),'observations')


class HBNDisplayIsolationTests(unittest.TestCase):
    def test_four_language_text_and_canonical_json(self):
        for language in LANGUAGES:
            for r in records():
                filtered=query_catalog('observations',record_id=r['id']);before=copy.deepcopy(filtered)
                text=render_catalog(filtered,'observations',language)
                self.assertEqual(filtered,before);self.assertNotIn('[missing:',text)
                self.assertIn(translate('catalog_name_'+r['id'],language),text)
                self.assertIn(f"{r['reported_result']['value']} ± {r['reported_result']['uncertainty']['value']} N/m",text)
                self.assertIn(HBN_REVIEW,text);self.assertIn('PDF p. 8',text)
                self.assertNotIn(translate('catalog_mos2_model_notice',language),text)
                self.assertNotIn(translate('catalog_reported_uncertainty_notice',language),text)
                for key in ('catalog_temperature','catalog_atmosphere','catalog_humidity','catalog_stress_measure','catalog_strain_measure'):
                    self.assertIn(translate(key,language)+': '+translate('unknown',language),text)
            run=subprocess.run([sys.executable,'-m','materials_boundaries','catalog','observations','--source-id',HBN_SOURCE,'--json','--lang',language],cwd=ROOT,text=True,capture_output=True)
            self.assertEqual(run.returncode,0,run.stderr)
            self.assertEqual(json.loads(run.stdout),query_catalog('observations',source_id=HBN_SOURCE))

    def test_evaluator_and_visualizations_remain_isolated(self):
        expected=evaluate(example());real_read=read_catalog
        def guard(kind):
            if kind=='observations':raise AssertionError('No observation evaluator or overlay')
            return real_read(kind)
        with patch('materials_boundaries.catalog.read_catalog',side_effect=guard),patch('materials_boundaries.visualization.read_catalog',side_effect=guard):
            self.assertEqual(evaluate(example()),expected)
            result=build_comparison([example()],fractions=[0,.5,1])
            text=json.dumps(result)+render_html(result)+render_svg(result,result['cases'][0]['id'])
        self.assertEqual(len(result['series']),8)
        for token in (*IDS,HBN_FAMILY,HBN_SOURCE):self.assertNotIn(token,text)
        for r in records():
            with self.assertRaises(ValidationError):evaluate(r)
            with self.assertRaises(CatalogLookupError):query_catalog('claims',record_id=r['id'])
