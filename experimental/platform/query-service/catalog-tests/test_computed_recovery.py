import concurrent.futures
from copy import deepcopy
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from materials_query.computed_registry import ComputedRegistry, digest, baseline_digest
from materials_query.app import create_app


def review_fixture():
    record = {'candidate_id':'fixture-entry', 'decision':'accepted', 'reason':'Synthetic test only',
        'project_material_id':'computed:nomad:material1', 'formula':'Si', 'provider':'nomad',
        'provider_entry_id':'entry1', 'provider_material_id':'material1',
        'source_url':'https://nomad-lab.eu/prod/v1/gui/entry/id/entry1',
        'density':{'value':2300, 'unit':'kg/m^3', 'evidence_kind':'computed',
                   'source_path':'results.properties.structures.structure_original.mass_density'},
        'attribution':'Synthetic test fixture; no real material admission', 'rights':'Synthetic test data', 'method':'Synthetic DFT'}
    held = deepcopy(record); held.update(candidate_id='held', decision='held', reason='Missing review')
    return {'schema':'computed-review-recovery/1', 'packet_sha256':'0'*64, 'reviewer':'Test only', 'rationale':'Synthetic unit tests', 'records':[record,held]}

class RegistryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/'registry.db'; self.review=review_fixture()
        self.registry=ComputedRegistry(self.path,self.review,trusted_review_sha256=digest(self.review))

    def test_atomic_held_and_replay(self):
        with self.assertRaises(ValueError): self.registry.admit(['fixture-entry','held'])
        self.assertEqual(self.registry.snapshot()['provider_entry_count'],0)
        a=self.registry.admit(['fixture-entry']); b=self.registry.admit(['fixture-entry'])
        self.assertEqual(a,b); self.assertEqual(a['project_unique_material_count'],1)
        self.assertEqual(a['legacy_unique_material_count'],1057)

    def test_concurrent_replay(self):
        with concurrent.futures.ThreadPoolExecutor(8) as pool:
            results=list(pool.map(lambda _:self.registry.admit(['fixture-entry']),range(20)))
        self.assertTrue(all(r==results[0] for r in results))
        self.assertEqual(results[0]['provider_entry_count'],1)

    def test_dedup_provider_material_not_formula(self):
        r=deepcopy(self.review); second=deepcopy(r['records'][0]); second['candidate_id']='second'
        second['provider_entry_id']='entry2';second['source_url']='https://nomad-lab.eu/prod/v1/gui/entry/id/entry2'
        r['records'].append(second)
        reg=ComputedRegistry(Path(self.temp.name)/'dedup.db',r,trusted_review_sha256=digest(r))
        s=reg.admit(['fixture-entry','second']);self.assertEqual(s['provider_entry_count'],2);self.assertEqual(s['project_unique_material_count'],1)

    def test_review_pin_source_and_held_tampering(self):
        for key,value in [('decision','accepted'),('source_url','https://example.com/forged')]:
            r=deepcopy(self.review);r['records'][1][key]=value
            with self.assertRaises(ValueError): ComputedRegistry(self.path,r,trusted_review_sha256=digest(self.review))
        r=deepcopy(self.review);r['records'][0]['source_url']='https://example.com/forged'
        with self.assertRaises(ValueError): ComputedRegistry(self.path,r,trusted_review_sha256=digest(r))

    def test_initial_review_cannot_replace(self):
        r=deepcopy(self.review);r['rationale']='New review must use a new registry'
        with self.assertRaises(ValueError): ComputedRegistry(self.path,r,trusted_review_sha256=digest(r))

    def test_deleted_or_forged_entry_fails(self):
        self.registry.admit(['fixture-entry'])
        with sqlite3.connect(self.path) as db: db.execute('DELETE FROM entries')
        with self.assertRaises(ValueError): self.registry.snapshot()

    def test_payload_tampering_fails(self):
        self.registry.admit(['fixture-entry'])
        r=deepcopy(self.review['records'][0]);r['density']['value']=1
        with sqlite3.connect(self.path) as db: db.execute('UPDATE entries SET payload=?',(json.dumps(r),))
        with self.assertRaises(ValueError): self.registry.snapshot()

    def test_changed_baseline_same_count_fails(self):
        original=Path.read_bytes
        def changed(path):
            data=original(path)
            if path.name=='_version.py' and 'materials_boundaries' in str(path):return data+b'\n# altered\n'
            return data
        with patch.object(Path,'read_bytes',changed):
            with self.assertRaises(ValueError):baseline_digest()

    def test_replaced_baseline_pin_fails(self):
        original=Path.read_bytes
        with patch.object(Path,'read_bytes',lambda p: b'{}' if p.name=='legacy_baseline.json' else original(p)):
            with self.assertRaises(ValueError):baseline_digest()

    def test_forged_held_row_fails(self):
        from materials_query.computed_registry import canonical
        held=self.review['records'][1]
        with sqlite3.connect(self.path) as db:
            db.execute('INSERT INTO entries VALUES (?,?)',('held',canonical(held).decode()))
            db.execute('INSERT INTO admissions VALUES (?,?)',('held',digest(held)))
        with self.assertRaises(ValueError):self.registry.snapshot()

    def test_fixed_review_export_budget(self):
        r=deepcopy(self.review)
        r['records']=[deepcopy(r['records'][0]) for _ in range(300)]
        for i,item in enumerate(r['records']):
            item['candidate_id']=str(i)
            item['attribution']='a'*4000
        with self.assertRaises(ValueError):ComputedRegistry(Path(self.temp.name)/'large.db',r,trusted_review_sha256=digest(r))

    def test_routes_default_off_pins_and_exports(self):
        self.assertFalse(TestClient(create_app()).get('/api/computed/status').json()['enabled'])
        self.registry.admit(['fixture-entry']); client=TestClient(create_app(computed_registry=self.registry))
        status=client.get('/api/computed/status').json()
        pin={'namespace':'computed',**{k:status[k] for k in ('baseline_version','overlay_version','review_version')}}
        self.assertEqual(client.post('/api/computed/list',json=pin).status_code,200)
        exact=pin|{'project_material_id':'computed:nomad:material1'}
        for route in ('exact','source'):
            self.assertEqual(client.post('/api/computed/'+route,json=exact).status_code,200)
        prop=client.post('/api/computed/property',json=exact|{'property':'density'}).json()['records'][0]
        self.assertEqual(prop['density']['evidence_kind'],'computed'); self.assertIn('entry1',prop['source_url'])
        self.assertEqual(client.post('/api/computed/export',json=pin).json()['provider_entry_count'],1)
        self.assertEqual(client.post('/api/computed/list',json=pin|{'overlay_version':'0'*64}).status_code,409)
        self.assertEqual(client.post('/api/computed/list',json=pin|{'namespace':'legacy'}).status_code,422)
        self.assertEqual(client.post('/api/computed/list',json=pin|{'path':'/tmp/private'}).status_code,422)
        self.assertEqual(client.post('/api/computed/search',json=pin|{'query':'a '*17}).status_code,400)
        self.assertEqual(client.post('/api/computed/admit',json=pin).status_code,404)
        self.assertEqual(client.post('/api/computed/refresh',json=pin).status_code,404)

if __name__=='__main__':unittest.main()
