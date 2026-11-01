"""Compare incremental rejection with original scientific validation."""
from copy import deepcopy
import unittest
from materials_boundaries.database import Database, ValidationSession


class IncrementalDatabaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        original = Database()
        state = deepcopy(original.states['state_aurubis_c11000'])
        cls.data = {'materials': {'schema_version': original.data['materials']['schema_version'],
            'identities': [deepcopy(original.identities[state['identity_id']])],
            'grades': [deepcopy(original.grades[state['grade_id']])], 'records': [state]},
            'reference_properties': {'schema_version': original.data['reference_properties']['schema_version'],
                'records': [deepcopy(original.properties[p]) for p in state['property_ids']]},
            'sources': deepcopy(original.data['sources'])}
        cls.session = ValidationSession(Database(cls.data))

    def test_unchanged_properties_reuse_scientific_checks(self):
        result = self.session.validate(Database(self.data))
        self.assertEqual(result['executed_property_checks'], 0)
        self.assertEqual(result['reused_property_checks'], len(self.data['reference_properties']['records']))

    def test_changed_property_revalidated(self):
        data = deepcopy(self.data)
        data['reference_properties']['records'][0]['scope_note'] += ' Additional curation note.'
        db = Database(data); db.validate_scientific_contracts()
        self.assertEqual(self.session.validate(db)['executed_property_checks'], 1)

    def test_invalid_value_rejected_by_both_paths(self):
        data = deepcopy(self.data)
        data['reference_properties']['records'][0]['reported_value']['number'] = '-1'
        db = Database(data)
        with self.assertRaises(ValueError): db.validate_scientific_contracts()
        with self.assertRaises(ValueError): self.session.validate(db)

    def test_source_change_invalidates_all_property_reuse(self):
        data = deepcopy(self.data)
        data['sources']['records'][0]['claim_notes'].append('Curation note.')
        result = self.session.validate(Database(data))
        self.assertEqual(result['reused_property_checks'], 0)

    def test_global_duplicate_cannot_hide_in_reused_properties(self):
        data = deepcopy(self.data)
        duplicate = deepcopy(data['materials']['identities'][0]); duplicate['id'] += '_duplicate'
        data['materials']['identities'].append(duplicate)
        db = Database(data)
        with self.assertRaises(ValueError): db.validate_scientific_contracts()
        with self.assertRaises(ValueError): self.session.validate(db)


class EvidenceClassCoverageTests(unittest.TestCase):
    def test_all_current_evidence_classes_match_full_validation(self):
        original = Database()
        session = ValidationSession(original)
        candidate_data = deepcopy(original.data)
        selected = {}
        for prop in candidate_data['reference_properties']['records']:
            if prop['evidence_kind'] not in selected:
                selected[prop['evidence_kind']] = prop['id']
                prop['scope_note'] += ' Database curation annotation; scientific value unchanged.'
        self.assertEqual(set(selected), {'manufacturer_reference', 'published_experimental_reference',
            'published_measurement_derived_reference', 'published_handbook_reference',
            'published_computational_reference'})
        candidate = Database(candidate_data)
        candidate.validate_scientific_contracts()
        report = session.validate(candidate)
        self.assertEqual(report['executed_property_checks'], len(selected))
        self.assertEqual(report['reused_property_checks'], len(original.properties)-len(selected))

