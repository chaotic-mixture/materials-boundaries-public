"""Six reviewed fiber/elastomer facts, separate from generic runtime contracts.

Source-conditioned fixtures protect the admitted transcription and qualifications.
They do not constrain future material IDs or perform independent scientific review.
"""
from copy import deepcopy
from contextlib import redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import unittest

from materials_boundaries.catalog import read_catalog, query_catalog
from materials_boundaries.catalog_output import render_catalog
from materials_boundaries.cli import main
from materials_boundaries.material_references import validate_material_catalog, resolve_material
from materials_boundaries.material_presentation import material_labels

ROOT=Path(__file__).resolve().parents[1]
T700='refprop_toray_t700s_mesquita2021_specimen1_tensile_modulus'
BASALT='refprop_deutsche_basalt_faser_a76_9_2_messmer2024_tensile_modulus'
SYLGARD='refprop_dow_corning_sylgard184_johnston2014_100c_youngs_modulus'
NR='refprop_smr10_bianchi2025_nr_mass_density'
EPDM='refprop_vistalon2504_n550_bianchi2022_epdm_mass_density'
NBR='refprop_perbunan3445f_tamas_benyei2025_ref_mass_density'
SELECTED=(T700,BASALT,SYLGARD,NR,EPDM,NBR)
PAIRS={T700:('249.8300317',None,'GPa'),BASALT:('56.1','11.5','GPa'),
       SYLGARD:('2.05','0.12','MPa'),NR:('0.958','0.006','g/cm^3'),
       EPDM:('0.996','0.02','g/cm^3'),NBR:('1.031','0.001','g/cm^3')}


def canonical(value):
    return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()


class ThirdMaterialBatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.materials=read_catalog('materials');cls.properties=read_catalog('reference_properties');cls.sources=read_catalog('sources')
        cls.props={p['id']:p for p in cls.properties['records']}
        cls.states={s['id']:s for s in cls.materials['records']}

    def test_six_distinct_source_scoped_identities_and_exact_result_pairs(self):
        validate_material_catalog(self.materials,self.properties,self.sources)
        identities=[]
        for key in SELECTED:
            p=self.props[key];state=self.states[p['material_state_id']]
            identities.append(state['identity_id']);self.assertEqual(state['property_ids'],[key])
            value,amplitude,unit=PAIRS[key]
            self.assertEqual(p['reported_value']['value_text'],value)
            self.assertEqual(p['reported_value']['number'],value)
            self.assertEqual(p['reported_value']['unit_code'],unit)
            if amplitude is None:self.assertIsNone(p['uncertainty'])
            else:
                self.assertEqual(p['uncertainty']['value_text'],amplitude)
                self.assertEqual(p['uncertainty']['number'],amplitude)
                self.assertEqual(p['uncertainty']['unit_code'],unit)
            self.assertEqual(p['evaluation_support'],'catalog_only')
            self.assertIs(p['universal_bound'],False);self.assertIs(p['engineering_allowable'],False)
            self.assertIs(p['verification']['independent_scientific_review'],False)
            self.assertIs(p['verification']['raw_data_reanalysis'],False)
        self.assertEqual(len(set(identities)),6)

    def test_t700_is_one_exact_dataset_specimen_with_linked_methods(self):
        p=self.props[T700];self.assertEqual(p['summary_statistic'],'reported_value')
        self.assertEqual(p['sample_count']['value'],1)
        self.assertEqual(p['source_id'],'mesquita_2021_dataset_v1')
        self.assertEqual(p['source_document']['hash_status'],'recorded')
        self.assertIn('0.1',p['method_definition']['extraction_window']['text'])
        self.assertIn('0.6%',p['method_definition']['extraction_window']['text'])
        text=json.dumps(p,ensure_ascii=False)
        for value in ('6.8300000','12.1010000','217'):self.assertIn(value,text)
        method_sources={e['source_id'] for e in p['method_definition']['evidence']}
        self.assertEqual(method_sources,{'mesquita_2021_dataset_v1','mesquita_2021_methods'})
        self.assertEqual({s['id'] for s in resolve_material(p['material_state_id'],self.materials,self.properties,self.sources)['sources']},method_sources)
        self.assertEqual(p['conditions']['temperature']['status'],'not_reported_in_inspected_source')

    def test_basalt_mean_sd_never_inherits_twenty_successes_or_strength_area(self):
        p=self.props[BASALT]
        self.assertEqual(p['summary_statistic'],'reported_mean')
        self.assertEqual(p['uncertainty_status'],'reported_standard_deviation')
        self.assertIsNone(p['sample_count']['value'])
        self.assertEqual(p['sample_count']['relation'],'not_reported')
        self.assertIn('20',json.dumps(p))
        self.assertIsNone(p['method_definition']['extraction_window'])
        text=json.dumps(p,ensure_ascii=False).lower()
        self.assertIn('strength',text);self.assertIn('circular',text)
        normalization=next(item['fact'] for item in p['conditions']['additional_conditions'] if item['name']=='modulus_area_normalization')
        self.assertEqual(normalization['status'],'not_verified');self.assertIsNone(normalization['text'])

    def test_sylgard_reported_95_percent_ci_has_no_mean_or_construction_invention(self):
        p=self.props[SYLGARD];u=p['uncertainty']
        self.assertEqual(p['summary_statistic'],'reported_value')
        self.assertEqual(p['sample_count']['value'],6)
        self.assertEqual(u['type'],'reported_confidence_interval')
        self.assertEqual(u['confidence_level'],{'value_text':'95%','number':'95','unit_code':'percent'})
        self.assertIsNone(u['coverage_factor'])
        for key in ('estimand','construction'):
            self.assertEqual(u[key]['status'],'not_reported_in_inspected_source')
            self.assertIsNone(u[key]['text']);self.assertTrue(u[key]['notes'])
        self.assertIn('below 40%',p['method_definition']['extraction_window']['text'])
        text=json.dumps(resolve_material(p['material_state_id'],self.materials,self.properties,self.sources),ensure_ascii=False)
        for token in ('10:1','48','0.40','254','21','39'):self.assertIn(token,text)
        self.assertEqual(p['conditions']['temperature']['status'],'reported')

    def test_rubber_undefined_plus_minus_preserves_aggregation_and_sample_scopes(self):
        for key,count in ((NR,3),(EPDM,10),(NBR,None)):
            p=self.props[key];u=p['uncertainty']
            self.assertEqual(p['summary_statistic'],'reported_value')
            self.assertEqual(p['uncertainty_status'],'reported_plus_minus_unspecified')
            self.assertEqual(u['type'],'reported_plus_minus_unspecified')
            self.assertIsNone(u['confidence_level']);self.assertIsNone(u['coverage_factor'])
            self.assertEqual(p['sample_count']['value'],count)
            self.assertIsNone(p['method_definition']['extraction_window'])
            self.assertIn('±',p['uncertainty_note'])
            self.assertIn('unspecified',u['scope'].lower())
            self.assertIn('does not explicitly define',p['uncertainty_note'].lower())
        self.assertEqual(self.props[NR]['conditions']['temperature']['status'],'reported')
        self.assertEqual(self.props[EPDM]['conditions']['temperature']['status'],'not_reported_in_inspected_source')
        for key in ('temperature','test_method','test_standard','conditioning'):
            self.assertEqual(self.props[NBR]['conditions'][key]['status'],'not_reported_in_inspected_source')
        text=json.dumps(self.props[EPDM],ensure_ascii=False)
        self.assertIn('1.042',text);self.assertIn('standard deviation',text)
        self.assertTrue(self.props[EPDM]['source_discrepancies'])
        self.assertNotEqual(self.props[EPDM]['density_basis'],'bulk')

    def test_actual_uncertainty_labels_and_canonical_cli_in_all_languages(self):
        for key in SELECTED:
            p=self.props[key];selected=query_catalog('reference-properties',record_id=key)
            for lang in ('en','zh','ja','de'):
                labels=material_labels(lang);text=render_catalog(selected,'reference-properties',lang)
                self.assertIn(p['reported_value']['value_text'],text)
                self.assertIn(p['sample_count']['scope'],text)
                self.assertIn(p['uncertainty_note'],text)
                if p['uncertainty'] is not None:
                    u=p['uncertainty'];label={'reported_standard_deviation':'standard_deviation',
                        'reported_confidence_interval':'confidence_interval',
                        'reported_plus_minus_unspecified':'plus_minus_unspecified'}[u['type']]
                    self.assertIn(labels[label]+': '+u['value_text']+' '+u['unit_text'],text)
                    if u['type']!='reported_standard_deviation':
                        self.assertNotIn(labels['standard_deviation']+':',text)
                        self.assertNotIn(labels['statistics_notice'],text)
                if key==SYLGARD:self.assertIn(labels['confidence_level']+': 95%',text)
                window=p['method_definition']['extraction_window']
                if window:self.assertIn(window['text'],text)
                for mode in ('--json','--text'):
                    stdout=io.StringIO()
                    with redirect_stdout(stdout):code=main(['catalog','reference-properties','--id',key,mode,'--lang',lang])
                    self.assertEqual(code,0)
                    self.assertEqual(json.loads(stdout.getvalue()) if mode=='--json' else stdout.getvalue().rstrip('\n'),selected if mode=='--json' else text)

    def test_detail_render_golden_snapshots(self):
        fixture=json.loads((ROOT/'tests/fixtures/fiber_elastomer_render_v0310.json').read_text(encoding='utf-8'))
        self.assertEqual(fixture['release'],'0.31.0')
        for key,langs in fixture['detail_sha256'].items():
            self.assertIn(key,SELECTED)
            for lang,digest in langs.items():
                text=render_catalog(query_catalog('reference-properties',record_id=key),'reference-properties',lang)
                self.assertEqual(hashlib.sha256(text.encode()).hexdigest(),digest)
        self.assertEqual(set(fixture['detail_sha256']),set(SELECTED))

    def test_reviewed_source_fixture_preserves_complete_qualified_selected_objects(self):
        fixture=json.loads((ROOT/'tests/fixtures/fiber_elastomer_source_transcription_v0310.json').read_text(encoding='utf-8'))
        identities={row['id']:row for row in self.materials['identities']}
        self.assertEqual({row['property_id'] for row in fixture['records']},set(SELECTED))
        for row in fixture['records']:
            self.assertEqual(self.props[row['property_id']],row['expected_property'])
            self.assertEqual(self.states[row['state_id']],row['expected_material_state'])
            self.assertEqual(identities[row['identity_id']],row['expected_identity'])

    def test_source_conditioned_negative_mutations_cannot_match_reviewed_facts(self):
        # Arbitrary prose cannot be scientifically adjudicated by a generic
        # schema. This explicit source-fixture gate rejects known unsupported
        # interpretations while the runtime remains open to future reviewed IDs.
        fixture=json.loads((ROOT/'tests/fixtures/fiber_elastomer_source_transcription_v0310.json').read_text(encoding='utf-8'))
        expected={row['property_id']:row for row in fixture['records']}
        cases=[
            (SYLGARD,lambda p:p.update(summary_statistic='reported_mean')),
            (SYLGARD,lambda p:p['uncertainty']['estimand'].update(status='reported',text='Mean of six individually fitted moduli',evidence=p['uncertainty']['evidence'])),
            (SYLGARD,lambda p:p['uncertainty'].update(type='reported_standard_deviation')),
            (SYLGARD,lambda p:p['uncertainty'].update(coverage_factor='1.96')),
            (SYLGARD,lambda p:p['method_definition']['extraction_window'].update(text='0 to 40% strain')),
            (SYLGARD,lambda p:p['reported_value'].update(value_text='0.82',number='0.82')),
            (T700,lambda p:p['reported_value'].update(value_text='230',number='230')),
            (T700,lambda p:p.update(summary_statistic='reported_mean')),
            (T700,lambda p:p['sample_count'].update(value=217)),
            (T700,lambda p:p['method_definition']['extraction_window'].update(text='0.001 to 0.006 strain')),
            (BASALT,lambda p:p['sample_count'].update(value=20,relation='exact')),
            (BASALT,lambda p:next(item['fact'] for item in p['conditions']['additional_conditions'] if item['name']=='modulus_area_normalization').update(status='reported',text='Circular area for modulus confirmed')),
            (NR,lambda p:p['sample_count'].update(value=4)),
            (EPDM,lambda p:p['sample_count'].update(value=60)),
            (EPDM,lambda p:p['conditions']['temperature'].update(status='reported',text='23.0 °C')),
            (EPDM,lambda p:p.update(density_basis='bulk')),
            (NBR,lambda p:p['sample_count'].update(value=10,relation='exact')),
            (NBR,lambda p:p['conditions']['test_method'].update(status='reported',text='ASTM D792')),
        ]
        # Source geometry correction is already applied, never a second scaling.
        for key in (NR,EPDM,NBR):
            cases.extend([(key,lambda p:p.update(summary_statistic='reported_mean')),
                          (key,lambda p:p.update(uncertainty=None,uncertainty_status='not_reported_in_inspected_source')),
                          (key,lambda p:p['uncertainty'].update(type='reported_standard_deviation'))])
        for key,mutation in cases:
            candidate=deepcopy(self.props[key]);mutation(candidate)
            with self.assertRaises(AssertionError):
                self.assertEqual(candidate,expected[key]['expected_property'])
        for text in ('Pure unfilled PDMS','Sylgard 184 base/curing agent 10:1 mass ratio'):
            candidate=deepcopy(self.states[self.props[SYLGARD]['material_state_id']])
            candidate['state']['composition_or_purity']['text']=text
            with self.assertRaises(AssertionError):
                self.assertEqual(candidate,expected[SYLGARD]['expected_material_state'])

    def test_selected_evidence_requires_real_source_registration_and_matching_document(self):
        for key in SELECTED:
            p=self.props[key]
            for mutation in ('unregistered','wrong_document','no_primary_method'):
                altered=deepcopy(self.properties);target=next(r for r in altered['records'] if r['id']==key)
                if mutation=='unregistered':target['evidence'][0]['source_id']='unregistered_source'
                elif mutation=='wrong_document':target['source_document']['url']='https://example.invalid/other.pdf'
                else:
                    target['method_definition']['evidence']=[e for e in target['method_definition']['evidence'] if e['source_id']!=target['source_id']]
                with self.assertRaises(ValueError):validate_material_catalog(self.materials,altered,self.sources)

    def test_three_held_candidates_are_excluded_from_this_batch_only(self):
        selected_json=json.dumps([resolve_material(self.props[k]['material_state_id'],self.materials,self.properties,self.sources)['identity'] for k in SELECTED]).casefold()
        for name in ('kevlar','dyneema','uhmwpe','sylgard 527'):self.assertNotIn(name,selected_json)
        # No runtime ID/family blacklist: newly qualified evidence can be admitted
        # under generic contracts; the independent mixed suite exercises fresh IDs.
        source=(ROOT/'materials_boundaries/material_references.py').read_text()
        for name in ('kevlar','dyneema','uhmwpe','sylgard527','sylgard_527'):self.assertNotIn(name,source.casefold())
