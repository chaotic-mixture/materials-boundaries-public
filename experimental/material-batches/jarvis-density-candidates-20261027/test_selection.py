"""Check frozen selection, conservative overlap holds and unadmitted status."""
from decimal import Decimal
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parent))
import select_candidates as source

def facts(formula,bucket):
    return {'formula':formula,'ratio_key':source.formula_key(formula),'screening_bucket':bucket}

class JarvisCandidateSelectionTests(unittest.TestCase):
    def test_formal_computed_overlap_is_held_without_new_identity(self):
        key=source.formula_key('Ag2AlCo')
        category,reason=source.eligible(facts('Ag2AlCo','all_metal_elements'),{key})
        self.assertIsNone(category)
        self.assertIn('formal',reason)

    def test_formula_and_grade_family_guards_are_conservative_holds(self):
        for formula,bucket in [('TiO2','oxygen_containing_no_C_H'),('Al2O3','oxygen_containing_no_C_H'),
                               ('CuZn','all_metal_elements'),('AlTiV','all_metal_elements')]:
            with self.subTest(formula=formula):
                category,reason=source.eligible(facts(formula,bucket),set())
                self.assertIsNone(category)
                self.assertIn('Conservative',reason)

    def test_unary_and_unselected_multicomponent_scope_is_held(self):
        for formula,bucket in [('Hf','all_metal_elements'),('AlTiZrO4','oxygen_containing_no_C_H')]:
            with self.subTest(formula=formula):
                self.assertIsNone(source.eligible(facts(formula,bucket),set())[0])

    def test_forged_bucket_or_formula_cannot_override_composition(self):
        for value in [facts('MgO','all_metal_elements'),facts('CO2','oxygen_containing_no_C_H')]:
            with self.assertRaises(ValueError):
                source.eligible(value,set())
        value=facts('NiTi','all_metal_elements');value['formula']='NiTi2'
        with self.assertRaises(ValueError):
            source.eligible(value,set())

    def test_suitable_new_compositions_receive_proposals_only(self):
        self.assertEqual(source.eligible(facts('NiTi','all_metal_elements'),set())[0],'metal')
        self.assertEqual(source.eligible(facts('TiZrO4','oxygen_containing_no_C_H'),set())[0],'inorganic')

    def test_frozen_two_thousand_rows_have_distinct_source_bound_compositions(self):
        path=Path(__file__).parent/'source-fact-candidates.json'
        value=json.loads(path.read_bytes())
        self.assertEqual(value['proposed_counts'],{'metal':1000,'inorganic':1000})
        self.assertFalse(value['handoff_ready'])
        self.assertEqual(value['admitted_increment'],0)
        keys=set();jids=set()
        formal=set(value['formal_composition_keys_excluded'])
        for category,rows in value['candidates'].items():
            self.assertEqual(len(rows),1000)
            previous=-1
            for row in rows:
                record=row['source_record'];key=row['proposed_conservative_composition_key']
                self.assertEqual(key,record['ratio_key'])
                self.assertEqual(source.formula_key(record['formula']),key)
                self.assertNotIn(key,keys);keys.add(key)
                self.assertNotIn(key,formal)
                self.assertNotIn(record['jid'],jids);jids.add(record['jid'])
                self.assertGreater(int(record['jid'].split('-')[1]),previous)
                previous=int(record['jid'].split('-')[1])
                self.assertEqual(source.eligible(record,formal)[0],category)
                self.assertGreater(Decimal(record['source_density_token']),0)
                self.assertEqual(record['functional'],'OptB88vdW')
                self.assertEqual(record['dimensionality'],'3D-bulk')
                self.assertEqual(row['experimental_existence'],'unknown')
                self.assertIsNone(row['exact_temperature_K'])
                self.assertIsNone(row['exact_pressure_Pa'])
                self.assertIn('not_independently_approved_or_admitted',row['candidate_status'])
        self.assertEqual(len(keys),2000)

if __name__=='__main__':
    unittest.main()
