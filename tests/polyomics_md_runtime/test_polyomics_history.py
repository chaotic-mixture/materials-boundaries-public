"""Validate a complete external MD append and finite predecessor recovery."""
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
import polyomics_md_history as _polyomics_history
import scc_flow_history as scc
history = scc.polyomics_test_scope(_polyomics_history)
import jarvis_density_history as jarvis
import sanchez_al_mea_history as sanchez
successors = scc.checkpoint_registry()
from material_append_history import encoded,recover_catalogs,recover_file
from materials_boundaries.material_references import validate_material_catalog
from materials_boundaries.material_presentation import render_material_catalog


def graph():
    return scc.checkpoint_catalogs()


class PolyOmicsHistoryTests(unittest.TestCase):
    def test_current_graph_and_exact_3180_1180_1175_predecessors(self):
        current=graph()
        validate_material_catalog(current['materials'],current['properties'],current['sources'])
        self.assertEqual([len(current['materials'][k]) for k in ['identities','grades','records']],[4180,31,4181])
        self.assertEqual(len(current['properties']['records']),4197)
        self.assertEqual(len(current['sources']['records']),132)
        previous=history.checkpoint_catalogs()
        self.assertEqual(len(previous['materials']['identities']),3180)
        self.assertEqual(len(jarvis.checkpoint_catalogs()['materials']['identities']),1180)
        self.assertEqual(len(sanchez.checkpoint_catalogs()['materials']['identities']),1175)
        for table,fields in [('materials',['identities','grades','records']),('properties',['records']),('sources',['records'])]:
            for field in fields:
                self.assertEqual(current[table][field][:len(previous[table][field])],previous[table][field])
            self.assertEqual({k:v for k,v in current[table].items() if k not in fields},
                             {k:v for k,v in previous[table].items() if k not in fields})

    def test_all_frozen_native_rows_and_model_state_counts_match(self):
        raw=(ROOT/'experimental/material-batches/polyomics-md-native-draft-20261028/native-candidate-r2.json').read_bytes()
        self.assertEqual(sha256(raw).hexdigest(),'1dc58bb6fdbab9d66806e01ca9edbfb1f016574950a49c9727847daa4bf5980e')
        native=json.loads(raw)
        current=graph()
        for table,fields in [('materials',['identities','grades','records']),('properties',['records']),('sources',['records'])]:
            for field in fields:
                index={row['id']:row for row in current[table][field]}
                for row in native['catalogs'][table][field]:
                    self.assertEqual(index[row['id']],row)
        self.assertEqual(len({b['constitution_key_sha256'] for b in native['bindings']}),1000)
        self.assertEqual(len({b['identity_id'] for b in native['bindings']}),1000)

    def test_registry_and_full_catalog_and_file_chains_remain_adjacent(self):
        self.assertEqual(successors.FROZEN_SUCCESSORS[0]['batch_id'],history.BATCH_ID)
        self.assertEqual(history.predecessor_descriptors(successors.FROZEN_SUCCESSORS),history.checkpoint_registry().FROZEN_SUCCESSORS)
        data=successors.data_ledgers()
        for newer,older in zip(data,data[1:]):
            self.assertEqual(newer['baseline_sha256'],older['current_sha256'])
        ledgers=successors.file_ledgers()
        for path in history.file_ledger()['updates']:
            entries=[ledger['updates'][path] for ledger in ledgers if path in ledger['updates']]
            for newer,older in zip(entries,entries[1:]):
                self.assertEqual(newer['previous_sha256'],older['sha256'],path)
        changed=deepcopy(successors.FROZEN_SUCCESSORS)
        changed[0]['batch_id']+=' unknown'
        with self.assertRaises(AssertionError):
            history.predecessor_descriptors(changed)

    def test_exact_old_files_and_registry_recover_unknown_images_are_rejected(self):
        for ledger in [history.file_ledger(),history.registry_ledger()]:
            for path,entry in ledger['updates'].items():
                raw=scc.checkpoint_bytes(path,(ROOT/path).read_bytes())
                previous=recover_file(raw,entry)
                self.assertEqual(sha256(previous).hexdigest(),entry['previous_sha256'])
                self.assertEqual(history.checkpoint_bytes(path,raw),previous)
                for bad in [raw+b' ',raw[:-1],b'!'+raw[1:]]:
                    with self.assertRaises(AssertionError):
                        recover_file(bad,entry)

    def test_complete_disk_is_required_and_single_file_cannot_repair_it(self):
        original=Path.read_bytes
        old={ROOT/path:encoded(history.checkpoint_catalogs()[key]) for key,path in history.CATALOG_PATHS.items()}
        relative=history.CATALOG_PATHS['materials']
        raw=(ROOT/relative).read_bytes()
        with patch.object(Path,'read_bytes',lambda p:old[p] if p in old else original(p)):
            with self.assertRaises(AssertionError):
                history.checkpoint_bytes(relative,raw)
        for target in history.CATALOG_PATHS.values():
            with patch.object(Path,'read_bytes',lambda p:original(p)+b' ' if p==ROOT/target else original(p)):
                with self.assertRaises(AssertionError):
                    history.checkpoint_catalogs()

    def test_partial_changed_retained_changed_new_order_and_metadata_fail(self):
        current=graph()
        for kind in ['partial','old','new','order','metadata']:
            changed=deepcopy(current)
            if kind=='partial':
                changed['materials']['identities'].pop()
            elif kind=='old':
                changed['materials']['identities'][0]['name']+=' changed'
            elif kind=='new':
                changed['properties']['records'][-1]['reported_value']['number']='1'
            elif kind=='order':
                changed['materials']['records'][-2:]=reversed(changed['materials']['records'][-2:])
            else:
                changed['sources']['unknown_metadata']=True
            with self.subTest(kind=kind),self.assertRaises(AssertionError):
                recover_catalogs(ROOT,changed,history.data_ledger())

    def test_original_jarvis_assertions_are_preserved_through_exact_recovery(self):
        path='tests/jarvis_density_runtime/test_jarvis_history.py'
        raw=(ROOT/path).read_bytes()
        previous=history.checkpoint_bytes(path,raw)
        assertions=lambda content:[ast.dump(n,include_attributes=False) for n in ast.walk(ast.parse(content))
            if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr.startswith('assert')]
        self.assertEqual(assertions(raw),assertions(previous))
        self.assertEqual(len(assertions(raw)),28)

    def test_old_jarvis_descriptor_view_is_exact_and_rereads_registry(self):
        view=history.jarvis_test_scope(jarvis)
        previous=history.checkpoint_registry().FROZEN_SUCCESSORS
        self.assertEqual(view.predecessor_descriptors(previous),jarvis.checkpoint_registry().FROZEN_SUCCESSORS)
        changed=deepcopy(previous)
        changed[0]['batch_id']+=' unknown'
        for bad in [changed,previous[:-1],successors.FROZEN_SUCCESSORS]:
            with self.assertRaises(AssertionError):
                view.predecessor_descriptors(bad)
        original=Path.read_bytes
        target=ROOT/'tests/material_append_successors.py'
        with patch.object(Path,'read_bytes',lambda p:original(p)+b' ' if p==target else original(p)):
            with self.assertRaises(AssertionError):
                view.predecessor_descriptors(previous)

    def test_source_method_scalar_unknown_window_and_four_language_rendering(self):
        current=graph()
        selected=current['properties']['records'][-1000:]
        self.assertTrue(all(p['density_basis']=='simulation_cell' and p['evidence_kind']=='published_computational_reference'
                            and p['method_definition']['type']=='source_reported_molecular_simulation_density'
                            and p['method_definition']['extraction_window'] is None and p['sample_count']['value'] is None
                            and p['summary_statistic']=='reported_value' and p['uncertainty'] is None for p in selected))
        for language in ['en','zh','ja','de']:
            text=render_material_catalog({'schema_version':'1.0.0','records':selected[:1]},'reference-properties',language)
            self.assertIn('source_reported_molecular_simulation_density',text)
            self.assertIn(selected[0]['reported_value']['value_text'],text)
            self.assertNotIn('[missing:',text)


if __name__=='__main__':
    unittest.main(verbosity=2)
