"""Fictional stress-at-elongation facts, not production-data allowlists."""
from copy import deepcopy
from decimal import localcontext
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import jsonschema
from materials_boundaries.database import Database, read_snapshot
from materials_boundaries.material_references import _PROPERTIES_SCHEMA, validate_material_catalog
from materials_boundaries.material_presentation import material_labels, render_material_catalog
from test_material_reference_contract import synthetic_mean_catalog

QUANTITY='tensile_stress_at_specified_elongation'


def fixture(target='200'):
    m,p,s=synthetic_mean_catalog()
    prop=p['records'][0]
    prop.update(quantity=QUANTITY,source_property_label='Synthetic stress at specified elongation')
    ev=deepcopy(prop['evidence']);ev[0]['supports']=['condition']
    prop['specified_elongation']={'value_text':target,'number':target,'unit_text':'%','unit_code':'percent',
        'basis':'source_reported_percent_elongation','evidence':ev,
        'notes':'Fictional source target only; actual strain estimator unknown, no slope conversion.'}
    return m,p,s


class SpecifiedElongationContractTests(unittest.TestCase):
    def test_target_above_100_preserves_stress_query_export_and_display(self):
        m,p,s=fixture();original=deepcopy((m,p,s))
        validate_material_catalog(m,p,s)
        jsonschema.Draft202012Validator(_PROPERTIES_SCHEMA).validate(p)
        db=Database({'materials':m,'reference_properties':p,'sources':s})
        self.assertEqual(len(list(db.records(quantity=QUANTITY))),1)
        for other in ('tensile_strength','tensile_modulus','youngs_modulus'):
            self.assertEqual(list(db.records(quantity=other)),[])
        with tempfile.TemporaryDirectory() as tmp:
            dest=Path(tmp)/'export';db.export(dest,quantity=QUANTITY)
            record=read_snapshot(dest)[1][p['records'][0]['id']]['property']
            self.assertEqual(record,p['records'][0])
            self.assertEqual(record['reported_value']['number'],'2500')
            self.assertEqual(record['specified_elongation']['number'],'200')
        resources=dict(zip(('materials','reference_properties','sources'),(m,p,s)))
        for lang in ('en','zh','ja','de'):
            labels=material_labels(lang)
            with patch('materials_boundaries.catalog.read_catalog',side_effect=lambda name:deepcopy(resources[name])):
                output=render_material_catalog(p,'reference-properties',lang)
            self.assertIn(labels['code_'+QUANTITY],output)
            self.assertIn(labels['specified_elongation']+': 200 %',output)
            self.assertIn('2500 MPa',output)
        self.assertEqual((m,p,s),original)

    def test_missing_misplaced_or_malformed_target_fails_both_shapes(self):
        mutations=[lambda x:x.pop('specified_elongation'),
            lambda x:x.update(quantity='tensile_modulus'),
            lambda x:x['specified_elongation'].update(number=200),
            lambda x:x['specified_elongation'].update(unit_code='MPa'),
            lambda x:x['specified_elongation'].update(basis='true_logarithmic_strain'),
            lambda x:x['specified_elongation'].update(evidence=[]),
            lambda x:x['reported_value'].update(unit_code='percent',unit_text='%')]
        for mutate in mutations:
            with self.subTest(mutate=mutate):
                m,p,s=fixture();mutate(p['records'][0])
                with self.assertRaises(ValueError):validate_material_catalog(m,p,s)
                with self.assertRaises(jsonschema.ValidationError):
                    jsonschema.Draft202012Validator(_PROPERTIES_SCHEMA).validate(p)

    def test_numeric_units_and_primary_condition_evidence_are_checked(self):
        mutations=[lambda x:x['specified_elongation'].update(number='0',value_text='0'),
            lambda x:x['specified_elongation'].update(number='100',value_text='200'),
            lambda x:x['specified_elongation'].update(number='NaN',value_text='NaN'),
            lambda x:x['specified_elongation'].update(unit_text='MPa'),
            lambda x:x['specified_elongation']['evidence'][0].update(supports=['method']),
            lambda x:x.update(quantity_dimension='mass_per_volume'),
            lambda x:x['reported_value'].update(unit_code='g/cm^3',unit_text='g/cm³')]
        for mutate in mutations:
            with self.subTest(mutate=mutate):
                m,p,s=fixture();mutate(p['records'][0])
                with self.assertRaises(ValueError):validate_material_catalog(m,p,s)
        m,p,s=fixture();secondary=deepcopy(s['records'][0]);secondary['id']='synthetic_secondary';s['records'].append(secondary)
        p['records'][0]['specified_elongation']['evidence'][0]['source_id']=secondary['id']
        with self.assertRaises(ValueError):validate_material_catalog(m,p,s)

    def add_target(self,m,p,target):
        second=deepcopy(p['records'][0]);second['id']='refprop_synthetic_second_target'
        second['specified_elongation'].update(number=target,value_text=target)
        p['records'].append(second);m['records'][0]['property_ids'].append(second['id'])

    def test_different_targets_with_same_stress_and_locator_are_distinct(self):
        m,p,s=fixture('100');self.add_target(m,p,'200')
        validate_material_catalog(m,p,s)

    def test_equivalent_target_formatting_cannot_duplicate_fact(self):
        m,p,s=fixture('100');self.add_target(m,p,'100.0')
        with self.assertRaisesRegex(ValueError,'duplicate source fact'):validate_material_catalog(m,p,s)

    def test_target_identity_does_not_round_under_decimal_context(self):
        m,p,s=fixture('100.1234');self.add_target(m,p,'100.1235')
        with localcontext() as context:
            context.prec=2
            validate_material_catalog(m,p,s)

    def test_old_property_shape_remains_valid_without_target(self):
        m,p,s=synthetic_mean_catalog()
        validate_material_catalog(m,p,s)
        jsonschema.Draft202012Validator(_PROPERTIES_SCHEMA).validate(p)


if __name__=='__main__':unittest.main()
