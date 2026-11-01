"""Check source/selection fidelity, not canonical polymer identities or admission."""
import csv
from decimal import Decimal
from hashlib import sha256
import io
import json
from pathlib import Path
import unittest

from rdkit import Chem
import select_source_candidates as selection

BATCH = Path(__file__).resolve().parent
CACHE = Path('F:/材料边界/growth-source-cache/polyomics-7475')


class PolyOmicsSourceCandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = (BATCH / 'source-fact-candidates.json').read_bytes()
        cls.frozen = json.loads(cls.raw)
        raw_csv = (CACHE / 'PFAS.csv').read_bytes()
        cls.rows = list(csv.DictReader(io.StringIO(raw_csv.decode('utf-8-sig'), newline='')))
        cls.by_uuid = {r['UUID']: (i, r) for i, r in enumerate(cls.rows)}

    def test_frozen_proposals_do_not_claim_material_admission(self):
        self.assertEqual(sha256(self.raw).hexdigest(), '3e89ef4c7b7b41c99acbc330f53b0d6a00f44aa9216dfdbe03f47eb1959e5b61')
        self.assertEqual(len(self.frozen['candidates']), 1000)
        self.assertIsNone(self.frozen['canonical_polymer_identity_count'])
        self.assertFalse(self.frozen['handoff_ready'])
        self.assertEqual(self.frozen['admitted_increment'], 0)
        for row in self.frozen['candidates']:
            self.assertEqual(row['canonical_polymer_identity'], 'unresolved')
            self.assertIsNone(row['independent_specimen_count'])
            self.assertIsNone(row['uncertainty'])
            self.assertEqual(row['statistical_aggregation'], 'not_established_for_this_csv_export')

    def test_every_selected_fact_and_zero_one_based_index_matches_source(self):
        self.assertEqual(len(self.rows), 5810)
        self.assertEqual(len(self.by_uuid), 5810)
        for candidate in self.frozen['candidates']:
            selected = candidate['selected_source_record']
            index, row = self.by_uuid[selected['uuid']]
            self.assertEqual(selected['source_record_index_0_based'], index)
            self.assertEqual(selected['source_record_number_1_based_excluding_header'], index + 1)
            self.assertEqual(selected['source_density_literal'], row['density'])
            self.assertEqual(selected['source_smiles_1'], row['smiles_1'])
            self.assertEqual(selected['source_smiles_list'], row['smiles_list'])
            for key, value in selected['source_conditions'].items():
                self.assertEqual(value, row[key])
            for key, value in selected['additional_source_literals'].items():
                self.assertEqual(value, row[key])
            row_bytes = json.dumps(row, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode('utf8')
            self.assertEqual(sha256(row_bytes).hexdigest(), selected['source_row_fields_canonical_json_sha256'])

    def test_independent_source_filter_and_minimum_uuid_representatives(self):
        index = json.loads((CACHE / 'periodic-graph-prototype-r1/periodic-graph-index.json').read_bytes())
        eligible = {}
        for key, group in index['groups'].items():
            for record in group['source_records']:
                if record['source_file'] != 'PFAS.csv':
                    continue
                _, row = self.by_uuid[record['uuid']]
                if any(row[k] != v for k, v in selection.COHORT.items()):
                    continue
                token = Decimal(row['nematic_order_parameter'])
                if not token.is_finite() or not Decimal(0) <= token <= Decimal('0.1'):
                    continue
                molecule = Chem.MolFromSmiles(row['smiles_1'])
                if not any(a.GetAtomicNum() == 9 for a in molecule.GetAtoms()):
                    continue
                eligible.setdefault(key, []).append(row['UUID'])
        self.assertEqual(len(eligible), 1789)
        self.assertEqual(sum(map(len, eligible.values())), 2019)
        self.assertEqual([r['operational_graph_key_sha256'] for r in self.frozen['candidates']], sorted(eligible)[:1000])
        for candidate in self.frozen['candidates']:
            group = eligible[candidate['operational_graph_key_sha256']]
            self.assertEqual(candidate['selected_source_record']['uuid'], min(group))
            self.assertEqual(candidate['cohort_rows_sharing_operational_key'], len(group))

    def test_selected_constitution_graphs_retain_explicit_restricted_scope(self):
        keys, uuids = set(), set()
        for candidate in self.frozen['candidates']:
            graph = candidate['unreviewed_periodic_graph']
            molecule = Chem.MolFromSmiles(candidate['selected_source_record']['source_smiles_1'])
            self.assertIsNotNone(molecule)
            self.assertEqual(len(Chem.GetMolFrags(molecule)), 1)
            self.assertEqual(Chem.GetFormalCharge(molecule), 0)
            self.assertTrue(any(a.GetAtomicNum() == 9 for a in molecule.GetAtoms()))
            self.assertEqual(len([a for a in molecule.GetAtoms() if a.GetAtomicNum() == 0]), 2)
            self.assertFalse(graph['admitted'])
            self.assertEqual(graph['independent_identity_review'], 'not_run')
            self.assertEqual(graph['periodic_graph_key_sha256'], candidate['operational_graph_key_sha256'])
            keys.add(candidate['operational_graph_key_sha256'])
            uuids.add(candidate['selected_source_record']['uuid'])
        self.assertEqual(len(keys), 1000)
        self.assertEqual(len(uuids), 1000)

    def test_source_equilibrium_and_nematic_tokens_are_filters_not_certificates(self):
        row = {**selection.COHORT, 'nematic_order_parameter': '0.1'}
        self.assertIsNone(selection.cohort_hold(row, True))
        self.assertIsNotNone(selection.cohort_hold(row, False))
        for bad in ['NaN', 'Infinity', '-Infinity', '', '-0.01', '0.1000001']:
            with self.subTest(token=bad):
                self.assertIsNotNone(selection.cohort_hold({**row, 'nematic_order_parameter': bad}, True))
        self.assertIsNotNone(selection.cohort_hold({**row, 'RadonPy_ver': 'other'}, True))
        self.assertIsNotNone(selection.cohort_hold({**row, 'check_eq': 'False'}, True))

    def test_frozen_existing_polymer_crosswalk_is_input_not_overlap_approval(self):
        raw = (BATCH / 'baseline-polymer-crosswalk.json').read_bytes()
        self.assertEqual(sha256(raw).hexdigest(), self.frozen['baseline_polymer_crosswalk_sha256'])
        baseline = json.loads(raw)
        self.assertEqual(len(baseline['identities']), 37)
        self.assertEqual(baseline['overlap_decision'], 'not_run')
        current_raw = (selection.ROOT / 'materials_boundaries/data/materials.json').read_bytes()
        self.assertEqual(sha256(current_raw).hexdigest(), baseline['working_materials_sha256'])
        current = json.loads(current_raw)
        self.assertEqual(baseline['identities'], [r for r in current['identities'] if r['category'] == 'polymer'])

    def test_citation_license_and_modification_notice_travel_with_facts(self):
        attribution = self.frozen['attribution']
        self.assertEqual(attribution['creators'], 'RadonPy Consortium')
        self.assertEqual(attribution['license'], 'CC-BY-4.0')
        self.assertEqual(attribution['license_url'], 'https://creativecommons.org/licenses/by/4.0/')
        self.assertIn(self.frozen['source_revision'], attribution['version_url'])
        self.assertIn('No endorsement', attribution['modifications'])
        self.assertEqual(self.frozen['source_doi'], '10.57967/hf/7475')

    def test_full_selection_replay_is_byte_identical(self):
        proposals, baseline = selection.select(CACHE)
        self.assertEqual(selection.encoded(proposals), self.raw)
        self.assertEqual(selection.encoded(baseline), (BATCH / 'baseline-polymer-crosswalk.json').read_bytes())


if __name__ == '__main__':
    unittest.main()
