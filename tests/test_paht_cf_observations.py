"""Closed factual transcription and catalog-only semantics, not replication."""
from copy import deepcopy
from decimal import Decimal, Inexact, Rounded, localcontext
import json
from pathlib import Path
import unittest
from jsonschema import Draft202012Validator
from materials_boundaries._paht_cf_observation_contract import (
    PAHT_SOURCE, PAHT_FAMILY, PAHT_DATASET, PAHT_TEMPERATURES,
    validate_paht_record, validate_paht_dataset, validate_paht_sources,
)
from materials_boundaries._pa12_cf15_observation_contract import validate_pa12_dataset
from materials_boundaries._observation_contract import validate_observation_records
from materials_boundaries.catalog import read_catalog, query_catalog
from materials_boundaries.observation_temperature_plot import build_observation_temperature_plot

ROOT = Path(__file__).resolve().parents[1]


def leaves(value, prefix=()):
    if isinstance(value, dict):
        for key, item in value.items():
            yield from leaves(item, prefix + (key,))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from leaves(item, prefix + (index,))
    else:
        yield prefix, value


def mutate(value):
    if value is None:
        return 'invented known value'
    if type(value) is bool:
        return not value
    return value + 1 if type(value) in (int, float) else value + ' altered'


def replace(record, path, value):
    for key in path[:-1]:
        record = record[key]
    record[path[-1]] = value


class PAHTAdmissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = read_catalog('observations')
        cls.records = sorted(query_catalog('observations', source_id=PAHT_SOURCE)['records'],
                             key=lambda r: int(r['source_cell']['temperature_column']))
        cls.sources = read_catalog('sources')['records']
        cls.source = next(s for s in cls.sources if s['id'] == PAHT_SOURCE)
        cls.facts = json.loads((ROOT/'tests/fixtures/paht_cf_source_transcription.json').read_text())
        cls.schema = json.loads((ROOT/'schemas/observations.schema.json').read_text())
        cls.validator = Draft202012Validator(cls.schema['$defs']['zach_paht_cf_annealed'])

    def test_exact_four_median_and_separate_sd_source_strings(self):
        self.assertEqual(len(self.records), 4)
        self.assertEqual(tuple(r['source_cell']['temperature_column'] for r in self.records), PAHT_TEMPERATURES)
        for r, c in zip(self.records, self.facts['cells']):
            with self.subTest(temperature=c['temperature']):
                result, sd, si = r['reported_result'], r['reported_result']['uncertainty'], r['si_result']
                self.assertEqual((result['value_string'], sd['value_string']), (c['median'], c['sd']))
                self.assertEqual(result['source_value_string'], c['median'])
                self.assertNotIn('±', result['source_value_string'])
                self.assertEqual(result['summary_statistic'], 'median_as_reported')
                self.assertEqual(sd['notation'], 'separate_sd')
                self.assertIs(sd['header_unit_explicit'], False)
                self.assertIsNone(sd['source_unit_string'])
                self.assertEqual(sd['unit_basis'], 'contextual_inference_from_associated_uts_column')
                self.assertEqual(si['uncertainty_unit_basis'], 'conditional_on_contextual_MPa_inference')
                self.assertEqual((si['value'], si['uncertainty_value']), (c['pa'], c['conditional_sd_pa']))
                self.assertEqual(Decimal(c['median'])*Decimal('1000000'), c['pa'])
                self.assertEqual(Decimal(c['sd'])*Decimal('1000000'), c['conditional_sd_pa'])
                self.assertTrue(self.validator.is_valid(r))
        Draft202012Validator(self.schema).validate(self.catalog)
        validate_paht_dataset(self.catalog['records'], require_complete=True)
        validate_paht_sources(self.sources)
        validate_pa12_dataset(self.catalog['records'], require_complete=True)

    def test_all_scientific_leaves_fail_closed_in_schema_and_runtime(self):
        original = self.records[0]
        for path, value in leaves(original):
            if path[0] in ('id', 'name'):
                continue
            changed = deepcopy(original); replace(changed, path, mutate(value))
            with self.subTest(path=path):
                self.assertFalse(self.validator.is_valid(changed))
                with self.assertRaises(ValueError):
                    validate_paht_record(changed)
                with self.assertRaises(ValueError):
                    validate_observation_records([changed])

    def test_missing_or_extra_fields_and_nonfinite_booleans_rejected(self):
        r = self.records[0]
        for key in r:
            changed = deepcopy(r); del changed[key]
            with self.subTest(missing=key), self.assertRaises(ValueError):
                validate_paht_record(changed)
            self.assertFalse(self.validator.is_valid(changed))
        for path in [('conditions','temperature','value'), ('sample_metadata','count'),
                     ('reported_result','value'), ('si_result','value')]:
            for value in (True, float('nan'), float('inf')):
                changed=deepcopy(r);replace(changed,path,value)
                with self.subTest(path=path,value=value), self.assertRaises(ValueError):
                    validate_paht_record(changed)
        changed=deepcopy(r);changed['unreviewed_model']=True
        with self.assertRaises(ValueError): validate_paht_record(changed)
        self.assertFalse(self.validator.is_valid(changed))

    def test_ids_are_aliasable_but_source_cells_are_not_new_measurements(self):
        changed=deepcopy(self.records)
        for i,r in enumerate(changed):
            r['id']='alternate-'+str(i);r['name']='Alternate display'
            r['si_result']['value']=float(r['si_result']['value'])
            r['conditions']['temperature']['value']=float(r['conditions']['temperature']['value'])
        validate_paht_dataset(changed,require_complete=True)
        validate_observation_records(changed)
        for r in changed:self.assertTrue(self.validator.is_valid(r))
        for records in [changed+[deepcopy(changed[0])], self.records+[changed[0]]]:
            with self.assertRaises(ValueError): validate_paht_dataset(records)
        validate_paht_dataset(changed[:1])
        with self.assertRaises(ValueError): validate_paht_dataset(changed[:1],require_complete=True)
        with self.assertRaises(ValueError): validate_paht_dataset(changed,require_complete=1)

    def test_host_decimal_context_cannot_change_admission(self):
        with localcontext() as context:
            context.prec=1;context.traps[Inexact]=True;context.traps[Rounded]=True
            validate_paht_dataset(self.records,require_complete=True)

    def test_source_cells_and_study_markers_cannot_be_laundered(self):
        for key in ('method_family','study_id','dataset_id','protocol_id'):
            for action in ('remove','change'):
                r=deepcopy(self.records[0])
                if action=='remove':del r[key]
                else:r[key]='foreign'
                with self.subTest(key=key,action=action),self.assertRaises(ValueError):
                    validate_observation_records([r])
        for path in [('source_cell','temperature_column'),('conditions','temperature','value_string')]:
            r=deepcopy(self.records[0]);replace(r,path,'50')
            with self.assertRaises(ValueError):validate_paht_record(r)

    def test_cross_family_dataset_spoofs_and_mixed_alias_duplicates_are_rejected(self):
        from materials_boundaries._pa12_cf15_observation_contract import (
            PA12_SOURCE, PA12_DATASET, is_pa12_record,
        )
        pa12 = query_catalog('observations', source_id=PA12_SOURCE)['records']
        validator = Draft202012Validator(self.schema)
        for originals, foreign_dataset in ((self.records, PA12_DATASET), (pa12, PAHT_DATASET)):
            for original in originals:
                changed = deepcopy(original)
                changed['dataset_id'] = foreign_dataset
                with self.subTest(record=original['id'], dataset=foreign_dataset):
                    with self.assertRaises(ValueError):
                        validate_observation_records([changed])
                    candidate = deepcopy(self.catalog)
                    candidate['records'] = [changed if r['id'] == original['id'] else r
                                            for r in candidate['records']]
                    self.assertFalse(validator.is_valid(candidate))
                    if original['study_id'] == PAHT_SOURCE:
                        # A false PA12 label cannot bypass PAHT's closed guard.
                        with self.assertRaises(ValueError):
                            is_pa12_record(changed)
        for original in self.records:
            self.assertFalse(is_pa12_record(original))
            alias = deepcopy(original)
            alias['id'] = 'mixed-catalog-alias-' + original['id']
            mixed = deepcopy(self.catalog['records']) + [alias]
            with self.subTest(duplicate=original['id']):
                with self.assertRaises(ValueError):
                    validate_observation_records(mixed)
                with self.assertRaises(ValueError):
                    validate_paht_dataset(mixed, require_complete=True)

    def test_every_source_field_is_closed_and_source_aliases_rejected(self):
        for path,value in leaves(self.source):
            s=deepcopy(self.source);replace(s,path,mutate(value))
            with self.subTest(path=path),self.assertRaises(ValueError):validate_paht_sources([s])
        with self.assertRaises(ValueError):validate_paht_sources([self.source,self.source])
        validate_paht_sources([])

    def test_scientific_unknowns_and_rate_are_not_normalized(self):
        for r in self.records:
            self.assertEqual(r['method']['loading_rate']['unit'],'mm/s')
            self.assertEqual(r['method']['loading_rate']['value'],10)
            for key in ('stress_measure','stress_area_basis','uts_extraction_criterion',
                        'strain_measure','strain_reference_length','local_strain_rate_per_s'):
                self.assertIsNone(r['method'][key])
            self.assertEqual(r['sample_metadata']['count'],5)
            self.assertIsNone(r['sample_metadata']['replicate_independence'])
            self.assertIsNone(r['conditions']['humidity']['specimen_moisture_content'])
            self.assertIsNone(r['material']['measured_porosity'])
            self.assertIsNone(r['method']['specimen']['extensometer_gauge_length'])
            self.assertIsNone(r['method']['specimen']['drawing_annotations']['unit_explicit_in_inspected_caption'])
            self.assertFalse(r['method']['standard_compliance_independently_verified'])
            self.assertFalse(r['verification']['independent_scientific_review'])
            self.assertFalse(r['verification']['source_inspection']['independent_replication'])
            self.assertIn('Only explicitly annealed',r['verification']['gaps'][7])

    def test_new_study_cannot_enter_existing_temperature_plot(self):
        with self.assertRaises(ValueError):
            build_observation_temperature_plot(dataset_id=PAHT_DATASET)
        from materials_boundaries._pa12_cf15_observation_contract import PA12_DATASET
        plot=build_observation_temperature_plot(dataset_id=PA12_DATASET)
        self.assertEqual(len(plot['glyphs']),6)
        self.assertTrue(all(r['study_id'] != PAHT_SOURCE for r in plot['record_snapshots']))
        self.assertTrue(all(r['evaluation_support']=='catalog_only' for r in self.records))

    def test_rights_keep_article_and_project_licenses_distinct(self):
        self.assertEqual(self.source['license']['identifier'],'CC-BY-4.0')
        for r in self.records:
            rights=r['verification']['rights']
            self.assertIn('10.3390/jcs9110624',rights['attribution'])
            self.assertIn('contextually inferred',rights['attribution'])
            self.assertFalse(rights['source_assets_redistributed'])
            self.assertFalse(rights['selected_table_third_party_credit_line_present'])
            self.assertIn('MIT',rights['project_license_scope'])


if __name__=='__main__':unittest.main()
