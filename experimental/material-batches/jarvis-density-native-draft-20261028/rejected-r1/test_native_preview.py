"""Source fidelity and isolated preview checks; passing never grants admission."""
import argparse
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

parser = argparse.ArgumentParser()
parser.add_argument('--stage', type=Path, required=True)
args, remaining = parser.parse_known_args()
STAGE = args.stage.resolve()
sys.path.insert(0, str(STAGE))
import materials_boundaries.material_references as references
from materials_boundaries.material_presentation import material_labels, render_material_catalog
import build_native_draft as builder

assert Path(references.__file__).resolve().is_relative_to(STAGE)
BATCH = Path(__file__).resolve().parent


class NativeDraftPreviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = (BATCH / 'native-candidate.json').read_bytes()
        cls.draft = json.loads(cls.raw)
        cls.graph = cls.draft['catalogs']
        cls.source = json.loads(builder.FACTS.read_bytes())

    def test_all_source_values_and_bindings_are_preserved(self):
        facts = {r['source_record']['jid']: r for rows in self.source['candidates'].values() for r in rows}
        identities = {r['id']: r for r in self.graph['materials']['identities']}
        properties = {r['id']: r for r in self.graph['properties']['records']}
        self.assertEqual(len(facts), 2000)
        self.assertEqual(len(self.draft['bindings']), 2000)
        self.assertEqual(len({r['composition_key'] for r in self.draft['bindings']}), 2000)
        for binding in self.draft['bindings']:
            source = facts[binding['jid']]
            prop = properties[binding['property_id']]
            self.assertEqual(binding['composition_key'], source['proposed_conservative_composition_key'])
            self.assertEqual(binding['source_row_text_sha256'], source['source_record']['source_row_text_sha256'])
            self.assertEqual(prop['reported_value']['number'], source['source_record']['source_density_token'])
            self.assertEqual(prop['reported_value']['value_text'], source['source_record']['source_density_token'])
            self.assertEqual(identities[binding['identity_id']]['category'], source['proposed_category'])

    def test_unknowns_and_computational_semantics_are_preserved(self):
        for prop in self.graph['properties']['records']:
            self.assertEqual(prop['method_definition']['type'], builder.METHOD)
            self.assertEqual(prop['evidence_kind'], 'published_computational_reference')
            self.assertEqual(prop['determination_basis'], 'source_reports_calculation')
            self.assertEqual(prop['density_basis'], 'crystallographic')
            self.assertEqual(prop['summary_statistic'], 'reported_value')
            self.assertIsNone(prop['sample_count']['value'])
            self.assertIsNone(prop['uncertainty'])
            self.assertFalse(prop['verification']['raw_data_reanalysis'])
            self.assertFalse(prop['verification']['independent_scientific_review'])
            for condition in prop['conditions'].values():
                self.assertEqual(condition['status'], 'not_reported_in_inspected_source')
                self.assertIsNone(condition['text'])

    def test_native_graph_and_in_memory_baseline_preview(self):
        references.validate_material_catalog(self.graph['materials'], self.graph['properties'], self.graph['sources'])
        baseline = {k: json.loads((STAGE / 'materials_boundaries/data' / n).read_bytes()) for k, n in
                    [('materials', 'materials.json'), ('properties', 'reference_properties.json'), ('sources', 'sources.json')]}
        preview = deepcopy(baseline)
        for kind, fields in [('materials', ['identities', 'grades', 'records']), ('properties', ['records']), ('sources', ['records'])]:
            for field in fields:
                old_ids = {r['id'] for r in preview[kind][field]}
                self.assertFalse(old_ids & {r['id'] for r in self.graph[kind][field]})
                preview[kind][field].extend(deepcopy(self.graph[kind][field]))
                self.assertEqual(preview[kind][field][:len(baseline[kind][field])], baseline[kind][field])
        references.validate_material_catalog(preview['materials'], preview['properties'], preview['sources'])
        self.assertEqual(len(preview['materials']['identities']), 3180)
        # This is a validation preview. It is never written to a runtime catalog
        # or passed to the admitted quota reporter.

    def test_mapping_replay_is_byte_identical(self):
        self.assertEqual(builder.encoded(builder.build(builder.FACTS.read_bytes())), self.raw)

    def test_attribution_and_explicit_unadmitted_state(self):
        self.assertFalse(self.draft['handoff_ready'])
        self.assertEqual(self.draft['admitted_increment'], 0)
        source = self.graph['sources']['records'][0]
        self.assertEqual(source['authors'], ['Kamal Choudhary'])
        self.assertEqual(source['doi'], builder.DOI)
        self.assertEqual(source['license']['identifier'], 'CC-BY-4.0')
        self.assertIn('https://creativecommons.org/licenses/by/4.0/', source['urls'])
        self.assertTrue(any('Changes:' in n for n in source['claim_notes']))

    def test_four_language_presentation_on_explicit_preview(self):
        # Supply the dependency-complete unadmitted graph only for this preview.
        # This does not simulate an installed release or alter actual resources.
        selected_states = [self.graph['materials']['records'][0], self.graph['materials']['records'][1000]]
        state_ids = {r['id'] for r in selected_states}
        identity_ids = {r['identity_id'] for r in selected_states}
        subset = {'schema_version': '1.0.0', 'records': selected_states, 'grades': [],
                  'identities': [r for r in self.graph['materials']['identities'] if r['id'] in identity_ids]}
        properties = {'schema_version': '1.0.0', 'records': [r for r in self.graph['properties']['records'] if r['material_state_id'] in state_ids]}
        inputs = {'materials': self.graph['materials'], 'reference_properties': self.graph['properties'], 'sources': self.graph['sources']}
        with patch('materials_boundaries.catalog.read_catalog', side_effect=lambda name: deepcopy(inputs[name])):
            for lang in ['en', 'zh', 'ja', 'de']:
                label = material_labels(lang)['code_' + builder.METHOD]
                for kind, catalog in [('materials', subset), ('reference-properties', properties)]:
                    rendered = render_material_catalog(catalog, kind, lang)
                    self.assertIn(label, rendered)
                    self.assertIn(builder.METHOD, rendered)
                    self.assertNotIn('[missing:', rendered)
                    (STAGE / ('preview-' + lang + '-' + kind + '.txt')).write_text(rendered, encoding='utf8')


if __name__ == '__main__':
    unittest.main(argv=[sys.argv[0], *remaining])
