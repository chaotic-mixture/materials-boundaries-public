"""Bounded hBN projection: source identity, navigation and scientific limits."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

from jsonschema import Draft202012Validator

sys.path.insert(0, str(Path(__file__).resolve().parent))
import hbn_relationship_projection as view

SOURCE = 'falin_et_al_2017_hbn_mechanical_properties'
MATERIAL = 'proposal:material:' + SOURCE
STATE = 'proposal:state:' + SOURCE + ':1L'
COHORT = 'proposal:cohort:' + SOURCE
FEEDSTOCK = 'proposal:feedstock:' + SOURCE
STIFFNESS, STRENGTH = view.SOURCE_IDS.values()


class HBNRelationshipProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = [r for r in view.read_catalog('observations')['records']
                       if r['id'] in (STIFFNESS, STRENGTH)]
        cls.projection = view.build_projection()
        cls.examples = json.loads(view.EXAMPLES_PATH.read_text(encoding='utf-8'))
        cls.review = json.loads(view.REVIEW_PATH.read_text(encoding='utf-8'))

    def test_actual_counts_are_separate_from_proposed_graph(self):
        p = self.projection
        self.assertEqual(p['formal_counts']['formal_project_admission_count'], 1108)
        self.assertEqual(p['formal_counts']['legacy_source_qualified_identity_count'], 1084)
        self.assertEqual(p['formal_counts']['reviewed_computed_composition_count'], 24)
        self.assertEqual(p['counts'], {
            'node_count': 8, 'edge_count': 7, 'proposed_material_count': 1,
            'state_count': 1, 'cohort_count': 1, 'feedstock_count': 1,
            'unique_source_observation_count': 2, 'catalog_observation_record_count': 2,
            'study_count': 1, 'admitted_delta': 0, 'new_materials': 0, 'new_observations': 0})
        for item in [p] + p['nodes'] + p['edges']:
            self.assertEqual(item['curation'], 'proposed')
            self.assertEqual(item['evaluation_support'], 'catalog_only')
        self.assertIsNone(p['identity_mapping']['legacy_identity_id'])
        self.assertIsNone(p['identity_mapping']['formal_admission_id'])

    def test_original_edges_are_preserved_and_bridges_are_explicit(self):
        old = {e['id']: e for e in self.examples}
        expected = {e['id'] for e in self.review['existing_edges']}
        bridges = {e['id'] for e in self.review['bridge_edges']}
        self.assertEqual(bridges, {'rel_hbn_projection_material_has_state_v1',
                                  'rel_hbn_projection_cohort_realizes_state_v1'})
        for edge in self.projection['edges']:
            original = {k: v for k, v in edge.items() if k != 'evaluation_support'}
            if edge['id'] in expected:
                self.assertEqual(original, old[edge['id']])
            else:
                self.assertIn(original, self.review['bridge_edges'])
        schema = json.loads(view.REVIEW_PATH.with_name('relationship.schema.json').read_text(encoding='utf-8'))
        validator = Draft202012Validator({'$defs': schema['$defs'], '$ref': '#/$defs/edge'})
        for edge in self.review['bridge_edges']:
            validator.validate(edge)

    def test_one_or_two_properties_never_increase_material_count(self):
        for record in self.records:
            p = view.build_projection([record])
            self.assertEqual(p['counts']['proposed_material_count'], 1)
            self.assertEqual(p['counts']['unique_source_observation_count'], 1)
            self.assertEqual((p['counts']['node_count'], p['counts']['edge_count']), (7, 6))
            self.assertEqual(p['counts']['admitted_delta'], 0)
            self.assertEqual(p['formal_counts'], self.projection['formal_counts'])
        with self.assertRaises(ValueError):
            view.build_projection([])

    def test_aliases_reversed_evidence_and_integral_floats_deduplicate_only_view(self):
        aliases = deepcopy(self.records)
        for row in aliases:
            row['id'] += '_appendable_alias'
            row['name'] += ' appended alias'
            row['evidence'].reverse()
            row['material']['layer_count'] = 1.0
        inputs = deepcopy(self.records) + aliases
        before = deepcopy(inputs)
        p = view.build_projection(inputs)
        self.assertEqual(inputs, before)
        self.assertEqual(p['counts']['catalog_observation_record_count'], 4)
        self.assertEqual(p['counts']['unique_source_observation_count'], 2)
        self.assertEqual(p['counts']['proposed_material_count'], 1)
        self.assertEqual(p['counts']['study_count'], 1)
        self.assertEqual(view.build_projection(list(reversed(inputs))), p)
        for alias in aliases:
            navigation = view.traverse(p, alias['id'], 'both', 8)
            self.assertEqual(navigation['resolved_node_id'], view.SOURCE_IDS[alias['quantity']])
            self.assertEqual(navigation['counts']['visited_material_count'], 1)
            self.assertEqual(navigation['counts']['visited_source_observation_count'], 2)
        only_alias = view.build_projection(aliases)
        self.assertEqual({n['id'] for n in only_alias['nodes'] if n['kind'] == 'observation'},
                         {STIFFNESS, STRENGTH})

    def test_duplicate_or_shadowing_catalog_ids_are_rejected(self):
        with self.assertRaises(ValueError):
            view.build_projection(self.records + [deepcopy(self.records[0])])
        alias = deepcopy(self.records[0])
        alias['id'] = STATE
        with self.assertRaises(ValueError):
            view.build_projection([alias])

    def test_unrelated_cubic_bn_is_not_merged(self):
        other = {'id': 'other_study_cubic_bn', 'study_id': 'other_study',
                 'method_family': 'other_family', 'material': {'formula': 'BN', 'phase': 'cubic'}}
        p = view.build_projection(self.records + [other])
        self.assertEqual(p, self.projection)
        self.assertNotIn(other['id'], p['observation_aliases'])
        changed = deepcopy(self.records)
        changed[0]['material']['phase'] = 'cubic'
        with self.assertRaises(ValueError):
            view.build_projection(changed)

    def test_layer_counts_and_reverse_navigation_do_not_add_materials(self):
        for start in (MATERIAL, STATE, COHORT, FEEDSTOCK, STIFFNESS, STRENGTH):
            walked = view.traverse(self.projection, start, 'both', 8)
            self.assertEqual(walked['counts']['visited_material_count'], 1)
            self.assertEqual(walked['counts']['visited_node_count'], 8)
            self.assertEqual(walked['counts']['visited_edge_count'], 7)
            self.assertEqual(walked['counts']['admitted_delta'], 0)
            self.assertEqual(walked['edges'], self.projection['edges'])
        changed = deepcopy(self.records)
        changed[0]['material']['layer_count'] = 2
        with self.assertRaises(ValueError):
            view.build_projection(changed)

    def test_physical_lineage_and_cohort_do_not_inherit_properties(self):
        walked = view.traverse(self.projection, FEEDSTOCK, 'both', 8)
        self.assertFalse(walked['property_inheritance'])
        for node in walked['nodes']:
            if node['kind'] != 'observation':
                self.assertEqual(node['properties'], {})
        lineage = next(e for e in walked['edges'] if e['predicate'] == 'derived_from')
        self.assertEqual((lineage['subject'], lineage['object']), (STATE, FEEDSTOCK))
        self.assertIsNone(lineage['qualifiers']['ancestor_catalogue_identity'])
        for edge in walked['edges']:
            if edge['predicate'] in ('observed_on', 'realizes_state'):
                self.assertEqual(edge['qualifiers']['individual_specimen_overlap'], 'unknown')
        reverse = view.traverse(self.projection, STATE, 'incoming', 2)
        self.assertEqual(reverse['counts']['visited_material_count'], 1)
        self.assertEqual(reverse['counts']['visited_source_observation_count'], 2)

    def test_source_results_and_distinct_height_conventions_survive_projection(self):
        for node in self.projection['nodes']:
            if node['kind'] != 'observation':
                continue
            row = next(r for r in self.records if r['id'] == node['id'])
            p = node['properties']
            self.assertEqual(p, {k: v for k, v in row.items() if k not in ('id', 'name', 'evidence')})
            self.assertEqual(p['reported_result']['unit'], 'N/m')
            self.assertEqual(p['material']['example_afm_apparent_height']['value'], .48)
            self.assertEqual(p['method']['effective_thickness_convention']['value'], .334)
            self.assertIsNone(p['sample_metadata']['counts']['failure_events'])
            self.assertIsNone(p['sample_metadata']['counts']['force_displacement_curves_acquired'])
        self.assertEqual(self.projection['rights_scope']['supplement_license'], 'unverified')
        self.assertEqual(self.projection['rights_scope']['peer_review_author_response_license'], 'unverified')

    def test_invented_failures_curves_conversions_or_thickness_are_rejected(self):
        cases = [
            (('sample_metadata', 'counts', 'failure_events'), 11),
            (('sample_metadata', 'counts', 'force_displacement_curves_acquired'), 55),
            (('sample_metadata', 'typical_protocol', 'exact_count'), True),
            (('reported_result', 'unit'), 'GPa'),
            (('reported_result', 'converted_3d_value'), 865),
            (('method', 'effective_thickness_convention', 'value'), .48),
            (('material', 'example_afm_apparent_height', 'value'), .334),
            (('material', 'layer_count'), True),
            (('evaluation_support',), 'executable'),
        ]
        for path, value in cases:
            with self.subTest(path=path):
                rows = deepcopy(self.records)
                target = rows[1]
                for key in path[:-1]:
                    target = target[key]
                target[path[-1]] = value
                with self.assertRaises(ValueError):
                    view.build_projection(rows)

    def test_canonical_id_spoof_and_scientific_change_cannot_hide_in_aliases(self):
        for update in ({'study_id': 'other'}, {'quantity': 'youngs_modulus'}, {'method_family': 'other'}):
            rows = deepcopy(self.records)
            rows[0].update(update)
            with self.assertRaises(ValueError):
                view.build_projection(rows)
        alias = deepcopy(self.records[0])
        alias['id'] += '_changed'
        alias['reported_result']['value'] += 1
        with self.assertRaises(ValueError):
            view.build_projection(self.records + [alias])

    def test_missing_changed_and_extra_relationships_require_review(self):
        old = next(e for e in self.examples if e['id'] == self.review['existing_edges'][0]['id'])
        variants = [[e for e in self.examples if e['id'] != old['id']]]
        changed = deepcopy(self.examples)
        next(e for e in changed if e['id'] == old['id'])['curation'] = 'admitted'
        variants.append(changed)
        extra = deepcopy(old)
        extra['id'] = 'unreviewed_extra_hbn_edge'
        variants.append(self.examples + [extra])
        reverse = deepcopy(old)
        reverse.update(id='unreviewed_incoming_hbn_edge', subject='external:other',
                       object=STIFFNESS, evidence=[])
        variants.append(self.examples + [reverse])
        for edges in variants:
            with self.assertRaises(ValueError):
                view.build_projection(typed_edges=edges)
        with patch.object(view, 'REVIEW_SHA256', '0' * 64), self.assertRaises(ValueError):
            view.build_projection()

    def test_detached_repeatable_results_and_bounded_traversal(self):
        p = view.build_projection()
        self.assertEqual(p, self.projection)
        walked = view.traverse(p, MATERIAL, max_depth=0)
        self.assertEqual(walked['counts']['visited_node_count'], 1)
        walked['nodes'][0]['properties']['injected'] = True
        self.assertEqual(p, self.projection)
        for depth in (-1, 9, True, 1.5):
            with self.assertRaises(ValueError):
                view.traverse(p, MATERIAL, max_depth=depth)
        with self.assertRaises(ValueError):
            view.traverse(p, MATERIAL, direction='sideways')
        with self.assertRaises(ValueError):
            view.traverse(p, 'unknown')
        p['counts']['proposed_material_count'] = 8
        with self.assertRaises(ValueError):
            view.traverse(p, MATERIAL)

    def test_checkout_cli_outputs_json_and_rejects_unknown_node(self):
        command = [sys.executable, '-B', str(Path(view.__file__).resolve())]
        good = subprocess.run(command, capture_output=True, check=True)
        self.assertEqual(json.loads(good.stdout), self.projection)
        self.assertEqual(good.stderr, b'')
        navigation = subprocess.run(command + ['--node', FEEDSTOCK, '--direction', 'both', '--max-depth', '8'],
                                    capture_output=True, check=True)
        self.assertEqual(json.loads(navigation.stdout)['counts']['visited_material_count'], 1)
        bad = subprocess.run(command + ['--node', 'unknown'], capture_output=True)
        self.assertEqual(bad.returncode, 2)
        self.assertEqual(bad.stdout, b'')


if __name__ == '__main__':
    unittest.main()
