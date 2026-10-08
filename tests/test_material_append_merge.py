"""In-memory merge tests; fictional records never enter production."""
from copy import deepcopy
import json
import unittest
from materials_boundaries.material_references import merge_material_catalogs
from test_material_reference_contract import synthetic_material_catalog


def append_fixture():
    m,p,s=synthetic_material_catalog()
    original_id=m['identities'][0]['id']
    m=json.loads(json.dumps(m).replace('synthetic_a','synthetic_b'))
    p=json.loads(json.dumps(p).replace('synthetic_a','synthetic_b'))
    m['identities'][0]['identity_scope']='Another fictional source-supported composition for merge tests'
    return {'materials':m,'properties':p,'sources':s}


class MaterialAppendMergeTests(unittest.TestCase):
    def test_merge_idempotent_preserves_inputs_and_baseline_order(self):
        graph=synthetic_material_catalog();snapshot=deepcopy(graph);append=append_fixture();saved=deepcopy(append)
        merged=merge_material_catalogs(*graph,append)
        self.assertEqual(graph,snapshot);self.assertEqual(append,saved)
        self.assertEqual(len(merged['materials']['identities']),2)
        self.assertEqual(merged['materials']['identities'][0],graph[0]['identities'][0])
        again=merge_material_catalogs(merged['materials'],merged['properties'],merged['sources'],append)
        self.assertEqual(again,merged)
        merged['materials']['identities'][0]['names']['en']='changed detached result'
        self.assertEqual(graph,snapshot)

    def test_conflicting_existing_id_fails_without_partial_mutation(self):
        graph=synthetic_material_catalog();snapshot=deepcopy(graph)
        append={'materials':deepcopy(graph[0]),'properties':deepcopy(graph[1]),'sources':deepcopy(graph[2])}
        append['materials']['identities'][0]['names']['en']='different existing record'
        with self.assertRaisesRegex(ValueError,'conflicting existing'):merge_material_catalogs(*graph,append)
        self.assertEqual(graph,snapshot)

    def test_reordering_new_append_tables_produces_identical_merge(self):
        graph=synthetic_material_catalog();append=append_fixture()
        second=json.loads(json.dumps(append).replace('synthetic_b','synthetic_c').replace('Another fictional','Third fictional'))
        combined=merge_material_catalogs(append['materials'],append['properties'],append['sources'],second)
        reordered=deepcopy(combined)
        for name,fields in [('materials',['identities','grades','records']),('properties',['records']),('sources',['records'])]:
            for field in fields:reordered[name][field].reverse()
        self.assertEqual(merge_material_catalogs(*graph,combined),merge_material_catalogs(*graph,reordered))

    def test_unvalidated_append_cannot_gain_coverage(self):
        graph=synthetic_material_catalog();append=append_fixture()
        append['properties']['records'][0]['engineering_allowable']=True
        with self.assertRaises(ValueError):merge_material_catalogs(*graph,append)

if __name__=='__main__':unittest.main()
