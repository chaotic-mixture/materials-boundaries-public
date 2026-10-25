"""Independent offline diagnostics; no source acquisition or material admission.

The Al2O3 formula is transcribed from the previously supplied Alexandria fragment.
Its response bytes and authenticity are not validated here. Other query examples
are explicitly synthetic counterexamples, not source records or review decisions.
"""
from copy import deepcopy
import hashlib
import io
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
import formal_overlap_audit as audit


def document(*probes):
    return {'schema': 'formal-overlap-probes/1', 'probes': list(probes)}


def snapshot(paths):
    return {str(path): (hashlib.sha256(path.read_bytes()).hexdigest(),
                        path.stat().st_size, path.stat().st_mtime_ns)
            for path in paths}


def synthetic_row(*, formula=None, cue=None):
    """Minimal explicit comparison facts, unrelated to the admitted inventory."""
    return {
        'formal_id': 'synthetic:alpha',
        'identity_sha256': '1' * 64,
        'identity_source': 'synthetic',
        'identity_pointer': '/synthetic/0',
        'structured_composition': None if formula is None else {
            'formula': formula, 'path': '/synthetic/0/canonical_composition'},
        'provider_reference': None,
        'related_provider_groups': {},
        'canonical_taxon': None,
        'conservative_taxon_crosswalk': None,
        'comparison_cues': [] if cue is None else [{
            'text': cue, 'path': '/synthetic/0/name', 'source': 'synthetic',
            'kind': 'name', 'status': None, 'context': {}}],
    }


class FormalOverlapAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inventory = audit.load_inventory()
        cls.rows = {row['formal_id']: row for row in cls.inventory['rows']}
        cls.report = audit.build_report()
        cls.script = Path(audit.__file__).resolve()
        cls.pinned_paths = [audit.ROOT / 'materials_boundaries' / 'data' / (name + '.json')
                            for name in ('materials', 'reference_properties', 'sources',
                                         'wood_baseline_crosswalk_v2')]
        cls.pinned_paths.append(audit.ROOT / 'formal-catalog' / 'materials_project_catalog'
                                / 'data' / 'formal_computed_review.json')

    def run_cli(self, *args, cwd=None, extra_env=None):
        environment = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
        environment.update(extra_env or {})
        return subprocess.run([sys.executable, '-B', str(self.script), *map(str, args)],
                              cwd=cwd, env=environment, capture_output=True, timeout=60)

    def query(self, **fields):
        report = audit.build_report(document({'probe_id': 'synthetic_probe', **fields}))
        result = report['probe_results'][0]
        self.assertEqual(sum(result['counts'].values()), 1188)
        self.assertEqual(len(result['relations']), 1188)
        self.assertIsNone(result['new_material_count'])
        self.assertEqual(result['admitted_delta'], 0)
        return result

    def relation(self, result, formal_id):
        return next(row for row in result['relations'] if row['formal_id'] == formal_id)

    def test_inventory_covers_only_all_1081_frozen_formal_records(self):
        # Retain the historical test ID; the runtime inventory uses the exact
        # current experiment, while archived 1081-entry reports stay unchanged.
        self.assertEqual(self.inventory['formal_counts'], {
            'formal_project_admission_count': 1188,
            'legacy_source_qualified_identity_count': 1164,
            'reviewed_computed_composition_count': 24,
            'categories': {'natural': 1010, 'metal': 44, 'inorganic': 71,
                           'polymer': 30, 'composite': 33}})
        self.assertEqual(len(self.rows), 1188)
        self.assertEqual(sum(row['partition'] == 'legacy-source-qualified'
                             for row in self.rows.values()), 1164)
        self.assertEqual(sum(row['partition'] == 'reviewed-computed'
                             for row in self.rows.values()), 24)
        self.assertEqual([row['formal_id'] for row in self.inventory['rows']],
                         sorted(self.rows))
        self.assertEqual(self.report['admitted_delta'], 0)
        self.assertIsNone(self.report['new_material_count'])

    def test_primary_partition_and_overlapping_dimensions_are_distinct(self):
        self.assertEqual(self.report['primary_comparability_partition'], {
            'structured_composition': 24, 'scoped_taxon_identity': 1000,
            'advisory_taxon_crosswalk': 6, 'source_qualified_text_only': 158})
        self.assertEqual(sum(self.report['primary_comparability_partition'].values()), 1188)
        self.assertEqual(self.report['overlapping_field_coverage_dimensions'], {
            'structured_integer_composition': 24, 'scoped_canonical_taxon': 1000,
            'advisory_taxon_crosswalk': 6, 'reported_composition_prose': 155,
            'associated_grade': 31, 'composite_category': 33})
        self.assertGreater(sum(self.report['overlapping_field_coverage_dimensions'].values()), 1188)

    def test_each_reported_identity_digest_binds_the_frozen_source_record(self):
        legacy = json.loads(self.pinned_paths[0].read_bytes())['identities']
        computed = json.loads(self.pinned_paths[-1].read_bytes())['records']
        inputs = [('legacy:' + row['id'], row) for row in legacy]
        inputs += [(row['conservative_count_bucket'], row) for row in computed]
        for formal_id, value in inputs:
            raw = json.dumps(value, sort_keys=True, separators=(',', ':'),
                             ensure_ascii=False, allow_nan=False).encode('utf-8')
            self.assertEqual(self.rows[formal_id]['identity_sha256'], hashlib.sha256(raw).hexdigest())

    def test_nylon_historical_family_keeps_state_composition_unknown(self):
        formal_id = 'legacy:mat_aniskevich_2023_ultimaker_nylon'
        rows = [row for row in self.inventory['rows'] if row['formal_id'] == formal_id]
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row['partition'], 'legacy-source-qualified')
        self.assertEqual(row['category'], 'polymer')
        self.assertEqual(row['state_count'], 1)
        self.assertEqual(row['grade_count'], 0)
        self.assertEqual(row['primary_comparability'], 'source_qualified_text_only')
        self.assertIsNone(row['structured_composition'])
        self.assertEqual(row['composition_prose_paths'], [])
        materials = json.loads(self.pinned_paths[0].read_bytes())
        self.assertEqual(len(materials['identities']), 1164)
        self.assertEqual(len(materials['records']), 1165)
        linked = [state for state in materials['records'] if state['identity_id'] == 'mat_aniskevich_2023_ultimaker_nylon']
        self.assertEqual([state['id'] for state in linked], ['state_aniskevich_2023_ultimaker_nylon_transparent_filament'])
        self.assertEqual(linked[0]['source_designation'], 'PA, Nylon Transparent 1647')
        self.assertEqual(len(linked[0]['property_ids']), 2)
        self.assertEqual(linked[0]['state']['composition_or_purity']['status'], 'not_reported_in_inspected_source')
        self.assertIsNone(linked[0]['state']['composition_or_purity']['text'])
        self.assertEqual(self.inventory['formal_counts']['formal_project_admission_count'], 1188)

    def test_tough_pla_two_states_form_one_formal_identity(self):
        formal_id = 'legacy:mat_aniskevich_2023_ultimaker_tough_pla'
        rows = [row for row in self.inventory['rows'] if row['formal_id'] == formal_id]
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row['partition'], 'legacy-source-qualified')
        self.assertEqual(row['category'], 'polymer')
        self.assertEqual(row['state_count'], 2)
        self.assertEqual(row['grade_count'], 0)
        self.assertEqual(row['primary_comparability'], 'source_qualified_text_only')
        self.assertIsNone(row['structured_composition'])
        self.assertEqual(row['composition_prose_paths'], ['/records/1142/state/composition_or_purity', '/records/1143/state/composition_or_purity'])
        materials = json.loads(self.pinned_paths[0].read_bytes())
        self.assertEqual(len(materials['identities']), 1164)
        self.assertEqual(len(materials['records']), 1165)
        linked = [state for state in materials['records'] if state['identity_id'] == 'mat_aniskevich_2023_ultimaker_tough_pla']
        self.assertEqual({state['id'] for state in linked}, set(['state_aniskevich_2023_ultimaker_tough_pla_black_filament', 'state_aniskevich_2023_ultimaker_tough_pla_white_filament']))
        self.assertEqual({state['source_designation'] for state in linked},
                         {'PLA Tough White 20231', 'PLA Tough Black 202300'})
        self.assertEqual(self.inventory['formal_counts']['formal_project_admission_count'], 1188)

    def test_legacy_names_grades_and_composites_never_become_stoichiometry(self):
        legacy = [row for row in self.rows.values() if row['partition'] == 'legacy-source-qualified']
        self.assertTrue(all(row['structured_composition'] is None for row in legacy))
        for formal_id in ('legacy:mat_aurubis_c11000',
                          'legacy:mat_lukianova2017_si3n4_85_9_6_sps1650',
                          'legacy:mat_vistalon2504_n550_bianchi2022_epdm'):
            with self.subTest(formal_id=formal_id):
                self.assertIsNone(self.rows[formal_id]['structured_composition'])
        self.assertEqual(sum(row['category'] == 'composite' for row in legacy), 33)

    def test_bruns_nominal_and_icp_oes_recipes_remain_qualified_text(self):
        # Table 1 nominal recipes identify four formulations. The separate
        # ICP-OES assays are neither substitutions nor pure compound formulas.
        recipes = {
            'al1p0': ('SiO2 74.00; B2O3 20.70; Na2O 4.30; Al2O3 1.00',
                     'SiO2 69.75; B2O3 25.59; Na2O 3.32; Al2O3 1.33'),
            'al1p5': ('SiO2 73.62; B2O3 20.60; Na2O 4.28; Al2O3 1.50',
                     'SiO2 68.34; B2O3 26.35; Na2O 3.47; Al2O3 1.82'),
            'al2p0': ('SiO2 73.25; B2O3 20.49; Na2O 4.26; Al2O3 2.00',
                     'SiO2 68.60; B2O3 25.77; Na2O 3.34; Al2O3 2.28'),
            'al4p0': ('SiO2 71.76; B2O3 20.07; Na2O 4.17; Al2O3 4.00',
                     'SiO2 68.22; B2O3 24.57; Na2O 3.40; Al2O3 3.81'),
        }
        for suffix, (nominal, assay) in recipes.items():
            formal_id = 'legacy:mat_bruns2020_nbs2_' + suffix
            row = self.rows[formal_id]
            with self.subTest(formal_id=formal_id):
                self.assertEqual(row['partition'], 'legacy-source-qualified')
                self.assertEqual(row['category'], 'inorganic')
                self.assertEqual(row['primary_comparability'], 'source_qualified_text_only')
                self.assertIsNone(row['structured_composition'])
                self.assertIsNone(row['provider_reference'])
                cues = [cue for cue in row['comparison_cues']
                        if cue['kind'] == 'composition_or_purity']
                self.assertEqual(len(cues), 1)
                cue = cues[0]
                self.assertEqual(cue['text'], 'Nominal mol%: ' + nominal
                                 + '. Separately reported ICP-OES mol%: ' + assay + '.')
                self.assertIn('not certified final stoichiometry', cue['context']['identity_scope'])
                self.assertIn('No assay correction, recipe normalization or exact final purity is inferred',
                              cue['context']['composition_notes'])
                for formula in ('SiO2', 'B2O3', 'Na2O', 'Al2O3'):
                    # Exact ingredient text, without any formula reordering or
                    # conversion of the recipe to a structured composition.
                    relation = audit.compare_probe(row, {'probe_id': 'oxide_cue', 'terms': [formula]})
                    self.assertEqual(relation['status'], 'possible_overlap')
                    self.assertEqual(relation['physical_equivalence'], 'unasserted')
                    self.assertEqual(relation['reasons'], ['literal_text_cue_not_composition_or_identity'])
                    self.assertIn(cue['text'], [evidence.get('text') for evidence in relation['evidence']])

    def test_bruns_furnace_cooled_states_do_not_add_quenched_identities(self):
        materials = json.loads(self.pinned_paths[0].read_bytes())
        identities = [row for row in materials['identities'] if row['id'].startswith('mat_bruns2020_')]
        states = [row for row in materials['records'] if row['id'].startswith('state_bruns2020_')]
        expected = {'mat_bruns2020_nbs2_' + suffix for suffix in ('al1p0', 'al1p5', 'al2p0', 'al4p0')}
        self.assertEqual({row['id'] for row in identities}, expected)
        self.assertEqual(len(states), 4)
        self.assertEqual({row['identity_id'] for row in states}, expected)
        self.assertEqual({row['id'] for row in states},
                         {identity.replace('mat_', 'state_', 1) + '_furnace_cooled' for identity in expected})
        self.assertEqual({row['formal_id'] for row in self.rows.values()
                          if row['formal_id'].startswith('legacy:mat_bruns2020_')},
                         {'legacy:' + identity for identity in expected})
        for state in states:
            row = self.rows['legacy:' + state['identity_id']]
            with self.subTest(state_id=state['id']):
                self.assertEqual(row['state_count'], 1)
                self.assertEqual(row['grade_count'], 0)
                self.assertEqual(state['evaluation_support'], 'catalog_only')
                self.assertIn('Quenched states and all mechanical, spectroscopic and computed values are excluded',
                              state['source_scope'])
                relation = audit.compare_probe(row, {'probe_id': 'excluded_state', 'terms': ['quenched']})
                self.assertEqual(relation['status'], 'unable_to_compare')
        self.assertEqual(self.inventory['formal_counts']['formal_project_admission_count'], 1188)

    def test_kapoor_analyzed_glasses_remain_qualified_text(self):
        materials = json.loads(self.pinned_paths[0].read_bytes())
        states = {row['identity_id']: row for row in materials['records']
                  if row['id'].startswith('state_kapoor2019_')}
        facts = (('P60', '0', '40.4', '59.6'), ('P50', '0', '49.9', '50.1'),
                 ('P46', '0', '53.9', '46.1'), ('Al5', '5.0', '40.2', '54.8'),
                 ('Al10', '10.0', '30.1', '59.9'), ('Al15', '14.8', '20.0', '65.2'))
        expected_ids = {'mat_kapoor2019_' + row[0].lower() for row in facts}
        self.assertEqual(set(states), expected_ids)
        self.assertEqual({row['id'] for row in materials['identities']
                          if row['id'].startswith('mat_kapoor2019_')}, expected_ids)
        for label, alumina, lime, phosphate in facts:
            identity_id = 'mat_kapoor2019_' + label.lower()
            row, state = self.rows['legacy:' + identity_id], states[identity_id]
            with self.subTest(identity_id=identity_id):
                self.assertEqual(row['partition'], 'legacy-source-qualified')
                self.assertEqual(row['category'], 'inorganic')
                self.assertEqual((row['state_count'], row['grade_count']), (1, 0))
                self.assertEqual(row['primary_comparability'], 'source_qualified_text_only')
                self.assertIsNone(row['structured_composition'])
                self.assertIsNone(row['provider_reference'])
                self.assertIsNone(state['grade_id'])
                self.assertEqual(state['property_ids'], ['refprop_kapoor2019_' + label.lower() + '_mass_density'])
                cues = [cue for cue in row['comparison_cues'] if cue['kind'] == 'composition_or_purity']
                self.assertEqual(len(cues), 1)
                cue = cues[0]
                self.assertEqual(cue['text'], 'Analyzed ICP-OES mol%: Al2O3 {}; CaO {}; P2O5 {}.'.format(
                    alumina, lime, phosphate))
                self.assertIn('not nominal batch recipes', cue['context']['composition_notes'])
                relation = audit.compare_probe(row, {'probe_id': 'analyzed_glass', 'terms': [label]})
                self.assertEqual(relation['status'], 'possible_overlap')
                self.assertEqual(relation['physical_equivalence'], 'unasserted')
        self.assertEqual(self.inventory['formal_counts']['formal_project_admission_count'], 1188)

    def test_tian_nominal_composites_remain_qualified_text(self):
        materials = json.loads(self.pinned_paths[0].read_bytes())
        states = {row['identity_id']: row for row in materials['records']
                  if row['id'].startswith('state_tian2023_')}
        expected = {'mat_tian2023_az31_ti_0p5wt', 'mat_tian2023_az31_ti_1wt'}
        self.assertEqual(set(states), expected)
        self.assertEqual({row['id'] for row in materials['identities']
                          if row['id'].startswith('mat_tian2023_')}, expected)
        for suffix, loading, label in (('0p5wt', '0.5', '0.5 wt% Ti'), ('1wt', '1', '1 wt Ti')):
            identity_id = 'mat_tian2023_az31_ti_' + suffix
            row, state = self.rows['legacy:' + identity_id], states[identity_id]
            with self.subTest(identity_id=identity_id):
                self.assertEqual(row['partition'], 'legacy-source-qualified')
                self.assertEqual(row['category'], 'composite')
                self.assertEqual((row['state_count'], row['grade_count']), (1, 0))
                self.assertEqual(row['primary_comparability'], 'source_qualified_text_only')
                self.assertIsNone(row['structured_composition'])
                self.assertIsNone(row['provider_reference'])
                self.assertIsNone(state['grade_id'])
                self.assertEqual(state['source_designation'], label)
                self.assertEqual(state['property_ids'], [
                    'refprop_tian2023_az31_ti_' + suffix + '_mass_density'])
                cues = [cue for cue in row['comparison_cues'] if cue['kind'] == 'composition_or_purity']
                self.assertEqual(len(cues), 1)
                self.assertEqual(cues[0]['text'],
                                 'Mg-3Al-1Zn (AZ31) matrix with nominal ' + loading + ' wt% nano-Ti addition.')
                self.assertIn('not an analyzed final composition', cues[0]['context']['composition_notes'])
                relation = audit.compare_probe(row, {'probe_id': 'nominal_composite', 'terms': ['AZ31']})
                self.assertEqual(relation['status'], 'possible_overlap')
                self.assertEqual(relation['physical_equivalence'], 'unasserted')
                self.assertEqual(audit.compare_probe(row, {'probe_id': 'oxide_probe', 'formula': 'Al2O3'})['status'],
                                 'unable_to_compare')
        comparator = self.rows['legacy:mat_chen2023_az31']
        self.assertEqual(comparator['category'], 'metal')
        self.assertNotIn('mat_chen2023_az31', states)
        self.assertEqual(self.inventory['formal_counts']['formal_project_admission_count'], 1188)

    def test_tarasov_nominal_recipes_remain_qualified_text(self):
        materials = json.loads(self.pinned_paths[0].read_bytes())
        states = {row['identity_id']: row for row in materials['records']
                  if row['id'].startswith('state_tarasov2022_pna_bpf_')}
        expected_ids = {'mat_tarasov2022_pna_bpf_' + str(index) for index in range(1, 6)}
        self.assertEqual(set(states), expected_ids)
        self.assertEqual({row['id'] for row in materials['identities']
                          if row['id'].startswith('mat_tarasov2022_pna_bpf_')}, expected_ids)
        self.assertEqual(len([row for row in materials['records']
                              if row['id'].startswith('state_tarasov2022_pna_bpf_')]), 5)
        for index, nominal in enumerate(('1:8:16', '1:9:16', '1:12:16', '1:18:16', '1:24:16'), 1):
            identity_id = 'mat_tarasov2022_pna_bpf_' + str(index)
            row = self.rows['legacy:' + identity_id]
            state = states[identity_id]
            with self.subTest(identity_id=identity_id):
                self.assertEqual(row['partition'], 'legacy-source-qualified')
                self.assertEqual(row['category'], 'polymer')
                self.assertEqual(row['state_count'], 1)
                self.assertEqual(row['grade_count'], 0)
                self.assertEqual(row['primary_comparability'], 'source_qualified_text_only')
                self.assertIsNone(row['structured_composition'])
                self.assertIsNone(row['provider_reference'])
                self.assertIsNone(state['grade_id'])
                self.assertEqual(state['state']['reinforcement']['status'], 'not_applicable')
                self.assertEqual(state['property_ids'], [
                    'refprop_tarasov2022_pna_bpf_' + str(index) + '_tensile_strength'])
                cues = [cue for cue in row['comparison_cues'] if cue['kind'] == 'composition_or_purity']
                self.assertEqual(len(cues), 1)
                cue = cues[0]
                self.assertEqual(cue['text'], 'Nominal source feed label HCP:BPF:ECH = ' + nominal
                                 + '; mixed phosphazene-containing epoxy resin based on bisphenol F, '
                                 + 'cured using source-described stoichiometric DDS.')
                self.assertIn('internally inconsistent', cue['context']['identity_scope'])
                self.assertIn('not pure molecular species', cue['context']['identity_scope'])
                self.assertIn('The exact DDS fraction and final cured composition are not established',
                              cue['context']['composition_notes'])
                relation = audit.compare_probe(row, {'probe_id': 'nominal_feed', 'terms': [nominal]})
                self.assertEqual(relation['status'], 'possible_overlap')
                self.assertEqual(relation['physical_equivalence'], 'unasserted')
                self.assertEqual(relation['reasons'], ['literal_text_cue_not_composition_or_identity'])
                self.assertIn(cue['text'], [item.get('text') for item in relation['evidence']])
        self.assertEqual(self.inventory['formal_counts']['formal_project_admission_count'], 1188)

    def test_alexandria_formula_exposes_three_distinct_qualified_relations(self):
        # Keep the historical test ID and original three relations; the four
        # appended glasses add literal oxide cues, not pure Al2O3. Kapoor's
        # reported zero entries also match text; they do not prove presence.
        result = self.query(formula='Al2O3')
        possible = {row['formal_id']: row for row in result['relations']
                    if row['status'] == 'possible_overlap'}
        expected = {
            'legacy:mat_kwiatkowski2023_a16sg_sps1500',
            'legacy:mat_ozog2020_aln90_y6_a4_pressed',
            'legacy:mat_lukianova2017_si3n4_85_9_6_sps1650'}
        expected.update('legacy:mat_bruns2020_nbs2_' + suffix
                        for suffix in ('al1p0', 'al1p5', 'al2p0', 'al4p0'))
        expected.update('legacy:mat_kapoor2019_' + suffix
                        for suffix in ('p60', 'p50', 'p46', 'al5', 'al10', 'al15'))
        self.assertEqual(set(possible), expected)
        self.assertEqual(result['counts'], {'confirmed_overlap': 0, 'possible_overlap': 13,
                                           'unable_to_compare': 1172})
        for row in possible.values():
            self.assertIn('literal_text_cue_not_composition_or_identity', row['reasons'])
            self.assertNotIn('same_structured_composition_identity_unresolved', row['reasons'])
            self.assertTrue(any(item['path'].endswith('/composition_or_purity/text')
                                for item in row['evidence']))

    def test_composition_cue_retains_qualifiers_but_does_not_search_them(self):
        result = self.query(formula='Al2O3')
        mixed_id = 'legacy:mat_ozog2020_aln90_y6_a4_pressed'
        hit = self.relation(result, mixed_id)
        cue = next(item for item in hit['evidence']
                   if item['path'].endswith('/composition_or_purity/text'))
        self.assertIn('identity_scope', cue['context'])
        self.assertIn('source_scope', cue['context'])
        self.assertIn('composition_notes', cue['context'])
        self.assertIn('not phase-pure AlN', cue['context']['composition_notes'])
        self.assertIn('not pure AlN or an AN2000 equivalent', cue['context']['source_scope'])
        for term in ('phase-pure AlN', 'AN2000', 'materials-13-04219'):
            with self.subTest(term=term):
                negative = self.query(terms=[term])
                self.assertEqual(self.relation(negative, mixed_id)['status'], 'unable_to_compare')
        for row in self.rows.values():
            for cue in row['comparison_cues']:
                self.assertFalse(cue['path'].endswith(('/notes', '/identity_scope', '/source_scope', '/url')))

    def test_same_composition_polymorphs_remain_possible_relations(self):
        first = synthetic_row(formula='Al2O3')
        second = deepcopy(first)
        second['formal_id'] = 'synthetic:beta'
        second['identity_sha256'] = '2' * 64
        for row in (first, second):
            relation = audit.compare_probe(row, {'probe_id': 'supercell', 'formula': 'Al4O6'})
            self.assertEqual(relation['status'], 'possible_overlap')
            self.assertIn('same_structured_composition_identity_unresolved', relation['reasons'])
        self.assertNotEqual(first['formal_id'], second['formal_id'])

    def test_different_structured_composition_is_unable_not_new(self):
        relation = audit.compare_probe(synthetic_row(formula='Al2O3'),
                                       {'probe_id': 'other', 'formula': 'SiO2'})
        self.assertEqual(relation['status'], 'unable_to_compare')
        self.assertIn('structured_composition_differs', relation['conflicts'])
        self.assertNotIn('new_material', relation)

    def test_formula_matching_preserves_element_case_and_token_boundaries(self):
        cases = [('CO', 'Co'), ('Co', 'CO'), ('Al2O30', 'Al2O3'),
                 ('prefixAl2O3', 'Al2O3'), ('Al2O3suffix', 'Al2O3'), ('al2o3', 'Al2O3')]
        for text, formula in cases:
            with self.subTest(text=text, formula=formula):
                relation = audit.compare_probe(synthetic_row(cue=text),
                                               {'probe_id': 'synthetic', 'formula': formula})
                self.assertEqual(relation['status'], 'unable_to_compare')
        self.assertEqual(audit.compare_probe(synthetic_row(cue='Mixture: Al2O3 + Y2O3'),
                          {'probe_id': 'synthetic', 'formula': 'Al2O3'})['status'], 'possible_overlap')

    def test_literal_name_match_is_not_a_structured_formula(self):
        row = synthetic_row(cue='Al2O3')
        result = audit.compare_probe(row, {'probe_id': 'name_only', 'formula': 'Al2O3'})
        self.assertEqual(result['status'], 'possible_overlap')
        self.assertEqual(result['reasons'], ['literal_text_cue_not_composition_or_identity'])
        self.assertIsNone(row['structured_composition'])

    def test_shared_grade_label_does_not_merge_supplier_identities(self):
        first = synthetic_row(cue='Supplier Alpha CuZn30')
        second = synthetic_row(cue='Supplier Beta CuZn30')
        second['formal_id'] = 'synthetic:other_supplier'
        results = [audit.compare_probe(row, {'probe_id': 'grade', 'terms': ['CuZn30']})
                   for row in (first, second)]
        self.assertEqual({row['status'] for row in results}, {'possible_overlap'})
        self.assertEqual(len({row['formal_id'] for row in results}), 2)
        self.assertTrue(all(row['structured_composition'] is None for row in (first, second)))

    def test_explicit_literal_terms_are_case_insensitive_but_not_substring_or_regex(self):
        for term, expected in [('supplier', 'possible_overlap'), ('UPPLIER', 'unable_to_compare'),
                               ('.*', 'unable_to_compare')]:
            with self.subTest(term=term):
                result = audit.compare_probe(synthetic_row(cue='Supplier Alpha'),
                                              {'probe_id': 'literal', 'terms': [term]})
                self.assertEqual(result['status'], expected)

    def test_exact_frozen_record_reference_confirms_only_record_reuse(self):
        formal_id = 'legacy:mat_aurubis_c11000'
        result = self.query(formal_reference={'id': formal_id,
                                             'identity_sha256': self.rows[formal_id]['identity_sha256']})
        self.assertEqual(result['counts'], {'confirmed_overlap': 1, 'possible_overlap': 0,
                                           'unable_to_compare': 1184})
        hit = self.relation(result, formal_id)
        self.assertEqual(hit['reasons'], ['exact_frozen_formal_record_reference'])
        self.assertEqual(hit['proof_scope'], 'frozen_formal_record_reference')
        self.assertEqual(hit['physical_equivalence'], 'unasserted')
        self.assertIn('not proof', self.report['classification_policy']['confirmed_overlap'])
        self.assertIn('physical material', self.report['classification_policy']['confirmed_overlap'])

    def test_wrong_digest_unknown_id_and_excluded_example_never_confirm(self):
        for formal_id, digest in [('legacy:mat_aurubis_c11000', '0' * 64),
                                 ('synthetic:unknown', '1' * 64),
                                 ('nomad_computed_79d7f2436fdc66a5', '1' * 64)]:
            with self.subTest(formal_id=formal_id):
                result = self.query(formal_reference={'id': formal_id, 'identity_sha256': digest})
                self.assertEqual(result['counts']['confirmed_overlap'], 0)
                self.assertEqual(result['counts']['unable_to_compare'], 1188)
        result = self.query(formal_reference={'id': 'legacy:mat_aurubis_c11000',
                                             'identity_sha256': '0' * 64})
        self.assertIn('formal_reference_digest_differs',
                      self.relation(result, 'legacy:mat_aurubis_c11000')['conflicts'])

    def test_exact_reference_with_conflicting_composition_does_not_confirm(self):
        row = synthetic_row(formula='Al2O3')
        result = audit.compare_probe(row, {'probe_id': 'conflict', 'formula': 'SiO2',
            'formal_reference': {'id': row['formal_id'], 'identity_sha256': row['identity_sha256']}})
        self.assertEqual(result['status'], 'possible_overlap')
        self.assertIn('exact_reference_with_conflicting_probe_facts', result['reasons'])
        self.assertIn('structured_composition_differs', result['conflicts'])

    def test_provider_identifiers_remain_possible_and_partial_conflicts_are_visible(self):
        row = synthetic_row()
        row['provider_reference'] = {'provider': 'nomad', 'entry_id': 'entry_a', 'material_id': 'material_a'}
        for material, expected_conflict in [('material_a', False), ('material_b', True)]:
            with self.subTest(material=material):
                result = audit.compare_probe(row, {'probe_id': 'provider', 'provider_reference': {
                    'provider': 'nomad', 'entry_id': 'entry_a', 'material_id': material}})
                self.assertEqual(result['status'], 'possible_overlap')
                self.assertEqual('provider_references_disagree' in result['conflicts'], expected_conflict)

    def test_exact_reference_with_all_provider_identifiers_wrong_does_not_confirm(self):
        row = synthetic_row()
        row['provider_reference'] = {'provider': 'nomad', 'material_id': 'material_a', 'entry_id': 'entry_a'}
        result = audit.compare_probe(row, {'probe_id': 'all_wrong_provider',
            'formal_reference': {'id': row['formal_id'], 'identity_sha256': row['identity_sha256']},
            'provider_reference': {'provider': 'nomad', 'material_id': 'material_b', 'entry_id': 'entry_b'}})
        self.assertEqual(result['status'], 'possible_overlap')
        self.assertIn('provider_references_disagree', result['conflicts'])
        self.assertIn('exact_reference_with_conflicting_probe_facts', result['reasons'])

    def test_known_related_provider_entry_is_possible_not_missing_or_confirmed(self):
        result = self.query(provider_reference={'provider': 'nomad',
                                               'entry_id': 'qOMH2nGoASvASE3dXKUi9unjv0JQ'})
        row = self.relation(result, 'computed-composition:Ag2AlCo')
        self.assertEqual(row['status'], 'possible_overlap')
        self.assertIn('known_related_provider_group_identity_unresolved', row['reasons'])
        self.assertTrue(any('/overlap_relations/same_composition_provider_groups/' in item['path']
                            for item in row['evidence']))
        self.assertEqual(row['physical_equivalence'], 'unasserted')

    def test_provider_reference_cannot_pair_identifiers_from_different_groups(self):
        row = synthetic_row()
        row['provider_reference'] = {'provider': 'nomad', 'material_id': 'material_a', 'entry_id': 'entry_a'}
        row['related_provider_groups'] = {'material_b': ['entry_b'], 'material_c': ['entry_c']}
        for entry, mismatched in [('entry_b', False), ('entry_c', True)]:
            with self.subTest(entry=entry):
                result = audit.compare_probe(row, {'probe_id': 'provider_pair', 'provider_reference': {
                    'provider': 'nomad', 'material_id': 'material_b', 'entry_id': entry}})
                self.assertEqual(result['status'], 'possible_overlap')
                self.assertEqual('provider_reference_pair_not_found' in result['conflicts'], mismatched)

    def test_taxon_match_retains_backbone_and_tissue_mismatch(self):
        row = synthetic_row()
        row['canonical_taxon'] = {'accepted_taxon_id': 'wfo-0000002457',
            'tissue_scope': 'collection_woody_tissue_anatomy_unspecified',
            'backbone_sha256': '3' * 64, 'path': '/synthetic/taxon'}
        reference = {k: v for k, v in row['canonical_taxon'].items() if k != 'path'}
        for change in ({}, {'tissue_scope': 'cork'}, {'backbone_sha256': '4' * 64}):
            with self.subTest(change=change):
                result = audit.compare_probe(row, {'probe_id': 'taxon',
                                                  'taxon_reference': reference | change})
                self.assertEqual(result['status'], 'possible_overlap')
                self.assertEqual('taxon_tissue_or_backbone_differs' in result['conflicts'], bool(change))

    def test_exact_reference_with_different_taxon_id_does_not_confirm(self):
        row = synthetic_row()
        row['canonical_taxon'] = {'accepted_taxon_id': 'wfo-0000002457',
            'tissue_scope': 'collection_woody_tissue_anatomy_unspecified',
            'backbone_sha256': '3' * 64, 'path': '/synthetic/taxon'}
        reference = {k: v for k, v in row['canonical_taxon'].items() if k != 'path'}
        reference['accepted_taxon_id'] = 'wfo-0000002458'
        result = audit.compare_probe(row, {'probe_id': 'wrong_taxon',
            'formal_reference': {'id': row['formal_id'], 'identity_sha256': row['identity_sha256']},
            'taxon_reference': reference})
        self.assertEqual(result['status'], 'possible_overlap')
        self.assertIn('taxon_id_differs', result['conflicts'])
        self.assertIn('exact_reference_with_conflicting_probe_facts', result['reasons'])

    def test_conservative_taxon_crosswalk_never_confirms_wood_or_cork(self):
        crosswalk_rows = [row for row in self.rows.values() if row['conservative_taxon_crosswalk']]
        self.assertEqual(len(crosswalk_rows), 6)
        dispositions = set()
        for row in crosswalk_rows:
            cross = row['conservative_taxon_crosswalk']
            dispositions.add(cross['disposition'])
            for taxon_id in cross['accepted_wfo_ids']:
                result = audit.compare_probe(row, {'probe_id': 'crosswalk', 'taxon_reference': {
                    'accepted_taxon_id': taxon_id, 'tissue_scope': 'synthetic_unknown_tissue',
                    'backbone_sha256': '5' * 64}})
                self.assertEqual(result['status'], 'possible_overlap')
                self.assertIn('crosswalk_does_not_establish_same_tissue_material', result['conflicts'])
        self.assertEqual(len(dispositions), 2)

    def test_unmatched_and_missing_composition_leave_novelty_unknown(self):
        result = self.query(terms=['synthetic_absent_material_label_8417'])
        self.assertEqual(result['counts'], {'confirmed_overlap': 0, 'possible_overlap': 0,
                                           'unable_to_compare': 1188})
        row = synthetic_row()
        self.assertEqual(audit.compare_probe(row, {'probe_id': 'missing', 'formula': 'Al2O3'})['status'],
                         'unable_to_compare')
        self.assertIsNone(result['new_material_count'])

    def test_probe_order_determinism_and_input_detachment(self):
        probes = document({'probe_id': 'z_formula', 'formula': 'Al2O3'},
                          {'probe_id': 'a_text', 'terms': ['alumina']})
        before = deepcopy(probes)
        first = audit.build_report(probes)
        second = audit.build_report(document(*reversed(probes['probes'])))
        self.assertEqual(first, second)
        self.assertEqual(probes, before)
        self.assertEqual([row['probe_id'] for row in first['probe_results']], ['a_text', 'z_formula'])
        first['rows'][0]['name'] = 'Synthetic caller mutation'
        self.assertNotEqual(first['rows'][0]['name'], audit.build_report()['rows'][0]['name'])

    def test_validate_probe_count_id_and_envelope_bounds(self):
        valid = [{'probe_id': 'p_' + str(i), 'formula': 'Al2O3'} for i in range(20)]
        self.assertEqual(len(audit.validate_probes(document(*valid))), 20)
        invalid = [{}, [], {'schema': 'wrong', 'probes': []}, document(*valid, {'probe_id': 'extra', 'formula': 'Al2O3'}),
                   document({'probe_id': 'duplicate', 'formula': 'Al2O3'}, {'probe_id': 'duplicate', 'formula': 'SiO2'}),
                   document({'probe_id': 'empty'}), document({'probe_id': True, 'formula': 'Al2O3'}),
                   document({'probe_id': 'bad id', 'formula': 'Al2O3'}),
                   document({'probe_id': 'x', 'formula': 'Al2O3', 'approved': True}),
                   {'schema': 'formal-overlap-probes/1', 'probes': [], 'admit': True}]
        for value in invalid:
            with self.subTest(value=value), self.assertRaises(ValueError):
                audit.validate_probes(value)
        with self.assertRaises(ValueError):
            audit.build_report({})

    def test_reject_malformed_formula_and_literal_terms(self):
        invalid = [{'formula': value} for value in (None, True, 5, '', 'Al0O3', 'Xx2', 'Ca(OH)2', 'Al2O3 + SiO2')]
        invalid += [{'terms': value} for value in (None, 'alumina', [], ['a'], ['x' * 81],
                                                  ['Alumina', 'alumina'], ['a\nb'], ['a\ud800b'],
                                                  ['term' + str(i) for i in range(9)])]
        for fields in invalid:
            with self.subTest(fields=fields), self.assertRaises(ValueError):
                audit.validate_probes(document({'probe_id': 'invalid', **fields}))

    def test_reject_incomplete_unknown_and_malformed_reference_fields(self):
        invalid = [
            {'formal_reference': {}},
            {'formal_reference': {'id': 'x', 'identity_sha256': 'a' * 63}},
            {'formal_reference': {'id': 'x', 'identity_sha256': 'A' * 64}},
            {'formal_reference': {'id': 'x', 'identity_sha256': 'a' * 64, 'approved': True}},
            {'provider_reference': {'provider': 'alexandria', 'entry_id': 'agm003206244'}},
            {'provider_reference': {'provider': 'nomad'}},
            {'provider_reference': {'provider': 'nomad', 'entry_id': True}},
            {'provider_reference': {'provider': 'nomad', 'entry_id': 'entry', 'url': 'synthetic'}},
            {'taxon_reference': {'accepted_taxon_id': 'wfo-1', 'tissue_scope': 'wood', 'backbone_sha256': 'a' * 64}},
            {'taxon_reference': {'accepted_taxon_id': 'wfo-0000002457', 'tissue_scope': 'wood'}},
            {'taxon_reference': {'accepted_taxon_id': 'wfo-0000002457', 'tissue_scope': None,
                                 'backbone_sha256': 'a' * 64}},
        ]
        for fields in invalid:
            with self.subTest(fields=fields), self.assertRaises(ValueError):
                audit.validate_probes(document({'probe_id': 'invalid', **fields}))

    def test_catalog_or_crosswalk_pin_drift_fails_closed(self):
        with patch.dict(audit.RESOURCE_SHA256, {'materials': '0' * 64}):
            with self.assertRaises(ValueError):
                audit.build_report()
        with patch.object(audit, 'CROSSWALK_SHA256', '0' * 64):
            with self.assertRaises(ValueError):
                audit.build_report()

    def test_current_inventory_rejects_changed_admission_counts(self):
        original = audit.formal_project_catalog()
        for field, value in (('formal_project_admission_count', 1081),
                             ('legacy_source_qualified_identity_count', 1057),
                             ('reviewed_computed_composition_count', 62)):
            changed = deepcopy(original)
            changed['counts'][field] = value
            with self.subTest(field=field), patch.object(audit, 'formal_project_catalog', return_value=changed):
                with self.assertRaisesRegex(ValueError, 'Unexpected formal scope'):
                    audit.load_inventory()

    def test_offline_report_does_not_attempt_network_or_change_pinned_inputs(self):
        before = snapshot(self.pinned_paths)
        with patch.object(socket, 'getaddrinfo', side_effect=AssertionError('Network forbidden')) as dns, \
             patch.object(socket, 'create_connection', side_effect=AssertionError('Network forbidden')) as connect, \
             patch('urllib.request.urlopen', side_effect=AssertionError('Network forbidden')) as urlopen:
            report = audit.build_report(document({'probe_id': 'offline', 'formula': 'Al2O3'}))
        self.assertEqual(report['admitted_delta'], 0)
        dns.assert_not_called()
        connect.assert_not_called()
        urlopen.assert_not_called()
        self.assertEqual(snapshot(self.pinned_paths), before)

    def test_cli_is_deterministic_utf8_under_ascii_stdout_and_read_only(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / 'probes.json'
            path.write_text(json.dumps(document({'probe_id': 'alumina', 'formula': 'Al2O3'})), encoding='utf-8')
            before = snapshot(self.pinned_paths + [path])
            first = self.run_cli('--probes', path, cwd=root, extra_env={'PYTHONIOENCODING': 'ascii'})
            second = self.run_cli('--probes', path, cwd=root, extra_env={'PYTHONIOENCODING': 'ascii'})
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertEqual(first.stderr, b'')
            self.assertEqual(second.stderr, b'')
            self.assertEqual(first.stdout, second.stdout)
            self.assertEqual(json.loads(first.stdout.decode('utf-8'))['probe_results'][0]['counts']['possible_overlap'], 13)
            self.assertTrue(first.stdout.endswith(b'\n'))
            self.assertTrue(any(byte > 127 for byte in first.stdout))
            self.assertEqual(snapshot(self.pinned_paths + [path]), before)
            self.assertEqual({p.name for p in root.iterdir()}, {'probes.json'})

    def test_cli_rejects_invalid_json_without_echoing_input_or_partial_output(self):
        invalid = [b'{"schema":"formal-overlap-probes/1","probes":[],"probes":[]}',
                   b'{"schema":"formal-overlap-probes/1","probes":NaN}', b'\xff',
                   b'{"secret_marker_8417":"not_a_probe"}']
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'secret_path_marker_8417.json'
            for payload in invalid:
                with self.subTest(payload=payload):
                    path.write_bytes(payload)
                    before = snapshot([path])
                    result = self.run_cli('--probes', path, cwd=directory)
                    self.assertEqual(result.returncode, 2)
                    self.assertEqual(result.stdout, b'')
                    self.assertNotIn(b'marker_8417', result.stderr)
                    self.assertIn(b'no report emitted', result.stderr)
                    self.assertEqual(snapshot([path]), before)

    def test_cli_input_size_missing_path_and_directory_fail_without_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            oversized = root / 'oversized.json'
            oversized.write_bytes(b' ' * 65537)
            for path in (oversized, root / 'missing.json', root):
                with self.subTest(path=path):
                    result = self.run_cli('--probes', path, cwd=root)
                    self.assertEqual(result.returncode, 2)
                    self.assertEqual(result.stdout, b'')
                    self.assertNotIn(str(path).encode(), result.stderr)

    def test_output_size_limit_never_emits_partial_report(self):
        output = io.BytesIO()
        stdout = io.TextIOWrapper(output, encoding='utf-8')
        stderr = io.StringIO()
        with patch.object(audit, 'MAX_OUTPUT_BYTES', 8), \
             patch.object(audit, 'build_report', return_value={'synthetic': 'oversized'}), \
             patch.object(sys, 'stdout', stdout), patch.object(sys, 'stderr', stderr):
            result = audit.main([])
        self.assertEqual(result, 2)
        self.assertEqual(output.getvalue(), b'')
        self.assertIn('no report emitted', stderr.getvalue())


if __name__ == '__main__':
    unittest.main()
