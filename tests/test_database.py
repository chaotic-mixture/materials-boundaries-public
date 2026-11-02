"""Database joins, provenance retention and deterministic downloads."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from materials_boundaries.database import Database, compare_snapshots, read_snapshot


def fixture():
    return {'materials': {'identities': [{'id': 'i', 'category': 'metal', 'name': 'Copper'}],
                         'grades': [], 'records': [{'id': 's', 'identity_id': 'i',
                             'grade_id': None, 'property_ids': ['p']}]},
            'reference_properties': {'records': [{'id': 'p', 'version': '1.0.0',
                'material_state_id': 's', 'source_id': 'source', 'quantity': 'mass_density',
                'conditions': {'temperature': None}, 'uncertainty': None,
                'verification': {'transcription_cross_check': 'completed',
                                 'independent_scientific_review': False}}]},
            'sources': {'records': [{'id': 'source', 'license': {'identifier': None}}]}}


class DatabaseTests(unittest.TestCase):
    def test_summary_counts_identities_separately_and_retains_native_statuses(self):
        data = fixture()
        first = data['reference_properties']['records'][0]
        first['conditions'] = {'temperature': {'status': 'not_reported_in_inspected_source'},
                               'additional_conditions': []}
        first['evidence_kind'] = 'manufacturer_reference'
        second = deepcopy(first)
        second.update(id='p2', quantity='elastic_modulus',
                      conditions={'direction': {'status': 'reported'}},
                      uncertainty_status='not_reported_in_inspected_source',
                      sample_count={'relation': 'not_reported', 'value': None})
        data['reference_properties']['records'].append(second)
        data['materials']['records'][0]['property_ids'].append('p2')
        data['sources']['records'].append({'id': 'unused', 'license': {'status': 'not_used'}})
        data['sources']['records'][0]['license']['status'] = 'no_explicit_reuse_license_verified'
        db = Database(data); result = db.summary()
        self.assertEqual(result['property_records'], 2)
        self.assertEqual(result['material_identities'], 1)
        self.assertEqual(result['material_states'], 1)
        self.assertEqual(result['identities_by_category'], {'metal': 1})
        self.assertEqual(result['referenced_sources'], 1)
        self.assertEqual(result['source_license_statuses'], {'no_explicit_reuse_license_verified': 1})
        self.assertEqual(result['condition_statuses'], {
            'temperature': {'__missing__': 1, 'not_reported_in_inspected_source': 1},
            'direction': {'__missing__': 1, 'reported': 1}})
        self.assertEqual(result['sample_count_relations'], {'__missing__': 1, 'not_reported': 1})
        self.assertEqual(result['independent_scientific_review_flags'], {'false': 2})
        self.assertEqual(result['database_snapshot'], db.snapshot)
        self.assertEqual(db.data, data)
        filtered = db.summary(quantity='elastic_modulus')
        self.assertEqual(filtered['property_records'], 1)
        self.assertEqual(filtered['condition_statuses'], {'direction': {'reported': 1}})

    def test_summary_empty_selection_and_drift(self):
        db = Database(fixture())
        result = db.summary(query='absent')
        self.assertEqual(result['property_records'], 0)
        self.assertEqual(result['material_identities'], 0)
        self.assertEqual(result['condition_statuses'], {})
        self.assertEqual(result['source_license_statuses'], {})
        db.data['materials']['identities'][0]['name'] = 'changed'
        with self.assertRaisesRegex(ValueError, 'changed after construction'):
            db.summary()

    def test_in_memory_mutation_cannot_reuse_old_snapshot(self):
        db = Database(fixture())
        db.data['sources']['records'][0]['license']['identifier'] = 'changed'
        with self.assertRaisesRegex(ValueError, 'changed after construction'):
            list(db.records())
        with tempfile.TemporaryDirectory() as temp:
            destination = Path(temp)/'export'
            with self.assertRaises(ValueError): db.export(destination)
            self.assertFalse(destination.exists())
        refreshed = Database(db.data)
        self.assertNotEqual(db.snapshot, refreshed.snapshot)

    def test_diff_ignores_snapshot_only_change_but_tracks_source_edits(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); data = fixture(); Database(data).export(root/'a')
            data['sources']['records'].append({'id': 'unused'})
            Database(data).export(root/'b')
            self.assertEqual(compare_snapshots(root/'a', root/'b')['modified'], [])
            data['sources']['records'][0]['license']['identifier'] = 'changed'
            Database(data).export(root/'c')
            diff = compare_snapshots(root/'b', root/'c')
            self.assertEqual(diff['modified'], ['p'])
            self.assertEqual(diff['affected_sources'], ['source'])

    def test_diff_add_delete_and_filter_mismatch(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); data = fixture(); Database(data).export(root/'a')
            data['reference_properties']['records'] = []
            data['materials']['records'][0]['property_ids'] = []
            Database(data).export(root/'b')
            self.assertEqual(compare_snapshots(root/'a', root/'b')['deleted'], ['p'])
            self.assertEqual(compare_snapshots(root/'b', root/'a')['added'], ['p'])
            Database(data).export(root/'c', query='Copper')
            with self.assertRaises(ValueError): compare_snapshots(root/'b', root/'c')

    def test_snapshot_corruption_is_not_accepted_as_change(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/'snapshot'; Database(fixture()).export(path)
            with (path/'records.jsonl').open('ab') as stream: stream.write(b' ')
            with self.assertRaisesRegex(ValueError, 'checksum'): read_snapshot(path)

    def test_query_preserves_unknowns_and_does_not_promote_review(self):
        record = next(Database(fixture()).records(query='copper', category='metal'))
        self.assertIsNone(record['property']['uncertainty'])
        self.assertFalse(record['review']['independent_scientific_review'])
        self.assertIsNone(record['sources'][0]['license']['identifier'])

    def test_filters_and_detached_results(self):
        data = fixture(); db = Database(data)
        data['materials']['identities'][0]['name'] = 'changed'
        self.assertEqual(len(list(db.records(query='Copper'))), 1)
        self.assertEqual(list(db.records(quantity='elastic_modulus')), [])
        record = next(db.records()); record['property']['quantity'] = 'changed'
        self.assertEqual(next(db.records())['property']['quantity'], 'mass_density')

    def test_duplicate_or_dangling_ids_rejected(self):
        data = fixture(); data['sources']['records'] *= 2
        with self.assertRaises(ValueError): Database(data)
        data = fixture(); data['reference_properties']['records'][0]['source_id'] = 'missing'
        with self.assertRaises(ValueError): Database(data)
        data = fixture(); data['materials']['records'][0]['property_ids'] = []
        with self.assertRaises(ValueError): Database(data)

    def test_secondary_evidence_sources_are_included(self):
        data = fixture(); data['sources']['records'].append({'id': 'secondary'})
        data['reference_properties']['records'][0]['evidence'] = [{'source_id': 'secondary'}]
        self.assertEqual([x['id'] for x in next(Database(data).records())['sources']],
                         ['secondary', 'source'])

    def test_snapshot_changes_when_conditions_or_rights_change(self):
        original = fixture()
        for table in ['reference_properties', 'sources']:
            data = deepcopy(original); data[table]['records'][0]['note'] = 'changed'
            self.assertNotEqual(Database(original).snapshot, Database(data).snapshot)

    def test_export_reproducible_and_refuses_overwrite(self):
        db = Database(fixture())
        with tempfile.TemporaryDirectory() as directory:
            a, b = Path(directory)/'a', Path(directory)/'b'
            manifest = db.export(a); db.export(b)
            raw = (a/'records.jsonl').read_bytes()
            self.assertEqual(raw, (b/'records.jsonl').read_bytes())
            self.assertEqual(hashlib.sha256(raw).hexdigest(), manifest['files']['records.jsonl'])
            self.assertEqual(json.loads(raw)['database_snapshot'], db.snapshot)
            self.assertEqual(manifest['record_count'], 1)
            with self.assertRaises(FileExistsError): db.export(a)


if __name__ == '__main__':
    unittest.main()
