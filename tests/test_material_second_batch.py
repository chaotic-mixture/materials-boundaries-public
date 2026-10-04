"""Selected-source regression guards for the seven-identity v0.30 batch.

These checks preserve reviewed transcription and scope; they are not a fresh
source audit, raw-data analysis, or independent scientific validation.
"""
from copy import deepcopy
from contextlib import redirect_stdout
import io
import json
import unittest

from materials_boundaries.catalog import read_catalog, query_catalog
from materials_boundaries.catalog_output import render_catalog
from materials_boundaries.cli import main
from materials_boundaries.material_references import validate_material_catalog, resolve_material
from materials_boundaries.material_presentation import material_labels

SI = 'refprop_nbs_silicon_x2_1975_mass_density'
GE = 'refprop_nbs_ge4065_crystallographic_density'
WOODS = { 'refprop_usda2010_sugar_maple_mc12_flexural_modulus': ('12,600','12600'),
          'refprop_usda2010_northern_red_oak_mc12_flexural_modulus': ('12,500','12500'),
          'refprop_usda2010_sitka_spruce_mc12_flexural_modulus': ('10,800','10800') }
CONCRETE = 'refprop_domagala2024_nc1_28d_saturated_mass_density'
MARBLE = 'refprop_wubalem2025_carrara_marble_specimen13_mass_density'
SELECTED = (SI,GE,*WOODS,CONCRETE,MARBLE)


class SecondMaterialBatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.materials=read_catalog('materials');cls.properties=read_catalog('reference_properties');cls.sources=read_catalog('sources')
        cls.props={p['id']:p for p in cls.properties['records']}
        cls.states={s['id']:s for s in cls.materials['records']}

    def test_seven_source_scoped_identities_have_one_property_and_no_invented_grade(self):
        validate_material_catalog(self.materials,self.properties,self.sources)
        identities=[]
        for identifier in SELECTED:
            p=self.props[identifier];state=self.states[p['material_state_id']]
            identities.append(state['identity_id'])
            self.assertIsNone(state['grade_id'])
            self.assertEqual(state['property_ids'],[identifier])
            self.assertEqual(p['evaluation_support'],'catalog_only')
            self.assertIs(p['universal_bound'],False);self.assertIs(p['engineering_allowable'],False)
            self.assertIs(p['verification']['independent_scientific_review'],False)
            self.assertIs(p['verification']['raw_data_reanalysis'],False)
        self.assertEqual(len(set(identities)),7)

    def test_silicon_exact_lexeme_historical_condition_chain_and_one_crystal(self):
        p=self.props[SI]
        self.assertEqual(p['reported_value']['value_text'],'2.329 1289')
        self.assertEqual(p['reported_value']['number'],'2.3291289')
        self.assertEqual(p['reported_value']['unit_code'],'g/cm^3')
        self.assertEqual(p['sample_count']['value'],1)
        self.assertEqual(p['evidence_kind'],'published_experimental_reference')
        self.assertIsNone(p['uncertainty'])
        temperature=p['conditions']['temperature']
        self.assertIn('20',temperature['text'])
        self.assertIn('reference',temperature['text'].lower())
        self.assertEqual({e['source_id'] for e in temperature['evidence']},
            {'bowman_schoonover_carroll_1974_density_scale',p['source_id']})
        self.assertIn('not a current certified standard',self.states[p['material_state_id']]['source_scope'].lower())

    def test_germanium_is_25c_crystallographic_source_number_not_specimen_count(self):
        p=self.props[GE]
        self.assertEqual(p['reported_value'],{'kind':'scalar','value_text':'5.325','number':'5.325',
            'unit_text':'grams per cubic centimeter','unit_code':'g/cm^3'})
        self.assertEqual(p['density_basis'],'crystallographic')
        self.assertEqual(p['evidence_kind'],'published_measurement_derived_reference')
        self.assertEqual(p['determination_basis'],'source_reports_calculation')
        self.assertEqual(p['method_definition']['type'],'source_reported_crystallographic_derivation')
        self.assertIn('25',p['conditions']['temperature']['text'])
        self.assertIsNone(p['sample_count']['value'])
        self.assertIsNone(p['uncertainty'])
        state=self.states[p['material_state_id']]
        self.assertIn('source number',state['source_designation'].lower())

    def test_woods_are_compiled_shear_inclusive_reference_means_with_unknown_counts(self):
        for identifier,(lexeme,number) in WOODS.items():
            with self.subTest(identifier=identifier):
                p=self.props[identifier]
                self.assertEqual(p['reported_value']['value_text'],lexeme)
                self.assertEqual(p['reported_value']['number'],number)
                self.assertEqual(p['quantity'],'flexural_modulus')
                self.assertEqual(p['evidence_kind'],'published_handbook_reference')
                self.assertEqual(p['determination_basis'],'source_reports_compiled_measurements')
                self.assertEqual(p['method_definition']['type'],'source_reported_compilation')
                self.assertEqual(p['summary_statistic'],'reported_mean')
                self.assertIn('shear',p['method_definition']['definition'].lower())
                self.assertIn('12%',p['conditions']['conditioning']['text'])
                self.assertEqual(p['conditions']['temperature']['status'],'not_reported_in_inspected_source')
                self.assertIsNone(p['sample_count']['value']);self.assertIsNone(p['uncertainty'])
                self.assertEqual(p['source_document']['hash_status'],'recorded')
                self.assertIsNone(p['source_document']['hash_note'])

    def test_concrete_curing_is_not_density_test_temperature(self):
        p=self.props[CONCRETE]
        self.assertEqual(p['reported_value']['number'],'2330')
        self.assertEqual(p['summary_statistic'],'reported_mean')
        self.assertEqual(p['sample_count']['value'],3)
        self.assertEqual(p['density_basis'],'not_stated')
        self.assertEqual(p['conditions']['temperature']['status'],'not_reported_in_inspected_source')
        self.assertEqual(p['conditions']['test_standard']['text'],'EN 12390-7:2019')
        self.assertIn('water',p['conditions']['conditioning']['text'].lower())
        self.assertIsNone(p['uncertainty'])
        self.assertEqual(p['source_document']['url'],'https://www.ebi.ac.uk/europepmc/webservices/rest/PMC11313055/fullTextXML')
        self.assertEqual(p['source_document']['sha256'],'8eee9708ea9e257dc060117f6b7c20a031443c982ecb98aa92cf5227e7479ec5')

    def test_marble_one_bulk_density_preserves_method_and_condition_unknowns(self):
        p=self.props[MARBLE]
        self.assertEqual(p['reported_value']['number'],'2760')
        self.assertEqual(p['summary_statistic'],'reported_value')
        self.assertEqual(p['sample_count']['value'],1)
        self.assertEqual(p['density_basis'],'bulk')
        self.assertIsNone(p['uncertainty'])
        for key in ('temperature','test_method','test_standard','conditioning'):
            self.assertEqual(p['conditions'][key]['status'],'not_reported_in_inspected_source')
        self.assertEqual(len(p['source_discrepancies']),2)
        self.assertIn('13',self.states[p['material_state_id']]['source_designation'])

    def test_new_evidence_filters_and_translations_are_exact_in_four_languages(self):
        for kind in ('published_handbook_reference','published_measurement_derived_reference'):
            selected=query_catalog('reference-properties',evidence_kind=kind)
            self.assertTrue(selected['records'])
            self.assertTrue(all(p['evidence_kind']==kind for p in selected['records']))
            for lang in ('en','zh','ja','de'):
                text=render_catalog(selected,'reference-properties',lang)
                labels=material_labels(lang)
                self.assertIn(labels['code_'+kind],text)
                for p in selected['records']:
                    self.assertIn(p['reported_value']['value_text'],text)
                    self.assertIn(labels['code_'+p['method_definition']['type']],text)
                stdout=io.StringIO()
                with redirect_stdout(stdout):
                    result=main(['catalog','reference-properties','--evidence-kind',kind,'--lang',lang,'--json'])
                self.assertEqual(result,0)
                self.assertEqual(json.loads(stdout.getvalue()),selected)

    def test_new_material_names_are_searchable_in_every_display_language(self):
        for identifier in SELECTED:
            state=self.states[self.props[identifier]['material_state_id']]
            for language,name in state['names'].items():
                with self.subTest(identifier=identifier,language=language):
                    found=query_catalog('materials',query=name)
                    self.assertIn(state['id'],[item['id'] for item in found['records']])

    def test_selected_states_resolve_all_supporting_evidence_sources(self):
        for identifier in SELECTED:
            p=self.props[identifier]
            result=resolve_material(p['material_state_id'],self.materials,self.properties,self.sources)
            self.assertIn(p['source_id'],{s['id'] for s in result['sources']})
            self.assertEqual(result['grade'],None)
            self.assertEqual(result['properties'],[p])


if __name__=='__main__':unittest.main()
