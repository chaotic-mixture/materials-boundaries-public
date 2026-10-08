import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from materials_platform.__main__ import run_demo
from materials_lifecycle.workflow import read_json, canonical

class Integration(unittest.TestCase):
    def test_end_to_end_binding(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); s=run_demo(root)
            b=read_json(root/s['binding']); batch=read_json(root/s['batch'])
            review=read_json(root/s['review']); manifest=read_json(root/s['release']/'manifest.json')
            typed=read_json(root/b['typed_candidate_path'])
            self.assertEqual(hashlib.sha256((root/b['raw_path']).read_bytes()).hexdigest(),b['raw_sha256'])
            self.assertEqual(hashlib.sha256(canonical(typed)).hexdigest(),b['typed_candidate_sha256'])
            self.assertEqual(batch['review_queue'][0]['status'],'pending_review')
            self.assertEqual(typed['review_status'],'pending_review')
            self.assertIsNone(typed['canonical_material_id'])
            self.assertIn(Path(s['binding']).stem,review['rationale'])
            self.assertEqual(manifest['decision_sha256'],Path(s['review']).stem)
            self.assertEqual(manifest['counts']['production_admitted'],0)
            self.assertEqual(manifest['counts']['properties'],0)
            self.assertEqual(manifest['citation']['publication_status'],'local_demo')
            self.assertFalse(s['release_archive_self_contained_raw_replay'])
    def test_repeat_scientific_content(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t); a=run_demo(root/'a'); b=run_demo(root/'b')
            self.assertEqual((root/'a'/a['release']/'dataset.tar').read_bytes(),(root/'b'/b['release']/'dataset.tar').read_bytes())
