"""Exact SCC source-qualified recipe append and strict predecessor bridges."""
import ast
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'tests')]
import scc_flow_history as history
import polyomics_md_history as polyomics
import jarvis_density_history as jarvis
import sanchez_al_mea_history as sanchez
import material_append_successors as successors
from material_append_history import encoded,recover_catalogs,recover_file
from materials_boundaries.material_references import validate_material_catalog
from materials_boundaries.material_presentation import render_material_catalog

NATIVE='experimental/material-batches/scc-fresh-flow-recipes-20261029/native-field-mapping-proposal-r3.json'
NATIVE_SHA='52f9feacacbf936052865621399442028942e94ab88a2f335f810341e270d9d6'


def graph():
    return {key:json.loads((ROOT/path).read_bytes()) for key,path in history.CATALOG_PATHS.items()}


def native():
    raw=(ROOT/NATIVE).read_bytes()
    assert sha256(raw).hexdigest()==NATIVE_SHA
    return json.loads(raw)


def assertions(raw):
    return [ast.dump(n,include_attributes=False) for n in ast.walk(ast.parse(raw)) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr.startswith('assert')]


class SCCFreshFlowHistoryTests(unittest.TestCase):
    def test_current_and_exact_predecessor_graphs_preserve_every_old_object(self):
        current=graph()
        validate_material_catalog(current['materials'],current['properties'],current['sources'])
        self.assertEqual([len(current['materials'][k]) for k in ['identities','grades','records']],[5180,31,5181])
        self.assertEqual(len(current['properties']['records']),5197)
        self.assertEqual(len(current['sources']['records']),133)
        previous=history.checkpoint_catalogs()
        self.assertEqual(len(previous['materials']['identities']),4180)
        self.assertEqual(len(polyomics.checkpoint_catalogs()['materials']['identities']),3180)
        self.assertEqual(len(jarvis.checkpoint_catalogs()['materials']['identities']),1180)
        self.assertEqual(len(sanchez.checkpoint_catalogs()['materials']['identities']),1175)
        for table,fields in [('materials',['identities','grades','records']),('properties',['records']),('sources',['records'])]:
            for field in fields:
                self.assertEqual(current[table][field][:len(previous[table][field])],previous[table][field])
            self.assertEqual({k:v for k,v in current[table].items() if k not in fields},{k:v for k,v in previous[table].items() if k not in fields})

    def test_native_rows_and_all_discrepancies_unknowns_and_source_images_survive(self):
        proposal=native()
        current=graph()
        for table,fields in [('materials',['identities','grades','records']),('properties',['records']),('sources',['records'])]:
            for field in fields:
                indexed={r['id']:r for r in current[table][field]}
                for row in proposal['catalogs'][table][field]:self.assertEqual(indexed[row['id']],row)
        keys=sorted(b['risk_cluster_key_sha256'] for b in proposal['bindings'])
        self.assertEqual(len(keys),len(set(keys)))
        self.assertEqual(sha256(json.dumps(keys,separators=(',',':')).encode()).hexdigest(),'7e146c46c6541ec92b1b06d0184ff70f3f292c9e8167dcf09d981bfeb06d556c')
        selected=proposal['catalogs']['properties']['records']
        self.assertEqual(sum(d['description'].startswith('Ingredient source-image difference') for p in selected for d in p['source_discrepancies']),778)
        self.assertEqual(sum(d['description'].startswith('Selected CSV flow token') for p in selected for d in p['source_discrepancies']),68)
        for p in selected:
            self.assertEqual((p['quantity'],p['quantity_dimension'],p['reported_value']['unit_code']),('slump_flow_spread','length','mm'))
            self.assertEqual(p['evidence_kind'],'published_handbook_reference')
            self.assertEqual(p['determination_basis'],'source_reports_compiled_measurements')
            self.assertEqual(p['method_definition']['type'],'source_reported_compilation')
            self.assertEqual(p['summary_statistic'],'reported_value')
            self.assertIsNone(p['density_basis'])
            self.assertIsNone(p['sample_count']['value'])
            self.assertIsNone(p['uncertainty'])
            self.assertFalse(p['engineering_allowable'])
            self.assertFalse(p['universal_bound'])
            self.assertFalse(p['verification']['independent_scientific_review'])
            extras={e['name']:e['fact'] for e in p['conditions']['additional_conditions']}
            self.assertNotIn('conservative_identity_risk_selection_scope',extras)
            self.assertEqual(len(json.loads(extras['original_ingredient_dual_views']['text'])),43)
            self.assertIn('Project curation selection metadata (not source-reported test conditions; not experimental evidence)',p['scope_note'])
            self.assertTrue(all(p['conditions'][k]['status']=='not_reported_in_inspected_source' for k in ['temperature','test_standard','test_method','direction','conditioning','loading_rate']))

    def test_registry_and_all_catalog_and_file_chains_are_closed_and_adjacent(self):
        self.assertEqual(successors.FROZEN_SUCCESSORS[0]['batch_id'],history.BATCH_ID)
        self.assertEqual(history.predecessor_descriptors(successors.FROZEN_SUCCESSORS),history.checkpoint_registry().FROZEN_SUCCESSORS)
        data=successors.data_ledgers()
        for newer,older in zip(data,data[1:]):self.assertEqual(newer['baseline_sha256'],older['current_sha256'])
        files=successors.file_ledgers()
        for path in history.file_ledger()['updates']:
            entries=[item['updates'][path] for item in files if path in item['updates']]
            for newer,older in zip(entries,entries[1:]):self.assertEqual(newer['previous_sha256'],older['sha256'],path)
        changed=deepcopy(successors.FROZEN_SUCCESSORS)
        changed[0]['batch_id']+=' unreviewed'
        with self.assertRaises(AssertionError):history.predecessor_descriptors(changed)

    def test_exact_code_and_document_recovery_rejects_unknown_bytes(self):
        for path,entry in history.file_ledger()['updates'].items():
            raw=(ROOT/path).read_bytes()
            previous=recover_file(raw,entry)
            self.assertEqual(sha256(previous).hexdigest(),entry['previous_sha256'])
            self.assertEqual(history.checkpoint_bytes(path,raw),previous)
            for bad in [raw+b' ',raw[:-1],b'!'+raw[1:]]:
                with self.subTest(path=path),self.assertRaises(AssertionError):recover_file(bad,entry)

    def test_current_disk_is_required_for_single_catalog_byte_projection(self):
        original=Path.read_bytes
        previous={ROOT/path:encoded(history.checkpoint_catalogs()[key]) for key,path in history.CATALOG_PATHS.items()}
        path=history.CATALOG_PATHS['materials']
        raw=(ROOT/path).read_bytes()
        with patch.object(Path,'read_bytes',lambda p:previous[p] if p in previous else original(p)):
            with self.assertRaises(AssertionError):history.checkpoint_bytes(path,raw)
        for target in history.CATALOG_PATHS.values():
            with patch.object(Path,'read_bytes',lambda p:original(p)+b' ' if p==ROOT/target else original(p)):
                with self.assertRaises(AssertionError):history.checkpoint_catalogs()

    def test_partial_or_changed_old_new_order_and_metadata_are_rejected(self):
        current=graph()
        for kind in ['partial','old','new','order','metadata']:
            changed=deepcopy(current)
            if kind=='partial':changed['materials']['identities'].pop()
            elif kind=='old':changed['materials']['identities'][0]['name']+=' altered'
            elif kind=='new':changed['properties']['records'][-1]['reported_value']['number']='1'
            elif kind=='order':changed['materials']['records'][-2:]=reversed(changed['materials']['records'][-2:])
            else:changed['sources']['unreviewed_metadata']=True
            with self.subTest(kind=kind),self.assertRaises(AssertionError):recover_catalogs(ROOT,changed,history.data_ledger())

    def test_old_MD_assertions_and_nested_descriptor_views_remain_exact(self):
        path='tests/polyomics_md_runtime/test_polyomics_history.py'
        raw=(ROOT/path).read_bytes()
        self.assertEqual(assertions(raw),assertions(history.checkpoint_bytes(path,raw)))
        view=history.polyomics_test_scope(polyomics)
        previous=history.checkpoint_registry().FROZEN_SUCCESSORS
        self.assertEqual(view.predecessor_descriptors(previous),polyomics.checkpoint_registry().FROZEN_SUCCESSORS)
        old_jarvis=view.jarvis_test_scope(jarvis)
        self.assertEqual(old_jarvis.predecessor_descriptors(polyomics.checkpoint_registry().FROZEN_SUCCESSORS),jarvis.checkpoint_registry().FROZEN_SUCCESSORS)
        changed=deepcopy(previous)
        changed[0]['batch_id']+=' unknown'
        for bad in [changed,previous[:-1],successors.FROZEN_SUCCESSORS]:
            with self.assertRaises(AssertionError):view.predecessor_descriptors(bad)
        original=Path.read_bytes
        target=ROOT/'tests/material_append_successors.py'
        with patch.object(Path,'read_bytes',lambda p:original(p)+b' ' if p==target else original(p)):
            with self.assertRaises(AssertionError):view.predecessor_descriptors(previous)

    def test_four_language_flow_discrepancies_and_curation_scope_are_visible(self):
        proposal=native()
        binding=next(b for b in proposal['bindings'] if b['original_source_fact_proposal']['original_workbook_comparison']['flow_numeric_image_differs'] and b['original_source_fact_proposal']['original_workbook_comparison']['all_ingredient_numeric_image_differences'])
        p=next(p for p in proposal['catalogs']['properties']['records'] if p['id']==binding['property_id'])
        for language in ['en','zh','ja','de']:
            text=render_material_catalog({'schema_version':'1.0.0','records':[p]},'reference-properties',language)
            self.assertIn('[slump_flow_spread]',text)
            self.assertIn(p['reported_value']['value_text']+' mm',text)
            self.assertIn('[source_reported_compilation]',text)
            self.assertIn('not source-reported test conditions; not experimental evidence',text)
            self.assertIn('No independent specimen n established',text)
            for difference in p['source_discrepancies']:self.assertIn(difference['description'],text)
            self.assertNotIn('[missing:',text)


if __name__=='__main__':
    unittest.main(verbosity=2)
