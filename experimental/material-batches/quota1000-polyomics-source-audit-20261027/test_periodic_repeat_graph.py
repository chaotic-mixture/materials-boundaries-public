"""Chemical graph cases for the unreviewed periodic-normalization prototype."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parent))
import periodic_repeat_graph as graph

def identity(smiles):
    return graph.normalize(smiles)['periodic_graph_key_sha256']

class PeriodicGraphTests(unittest.TestCase):
    def test_polyethylene_nonprimitive_repeat_does_not_inflate_groups(self):
        self.assertEqual(identity('*C*'),identity('*CC*'))
        self.assertEqual(identity('*C*'),identity('*CCCC*'))
        self.assertEqual(graph.normalize('*CCCC*')['repeat_factor'],4)

    def test_ptfe_nonprimitive_repeat_and_atom_order_are_equivalent(self):
        self.assertEqual(identity('*C(F)(F)*'),identity('*C(F)(F)C(F)(F)*'))
        self.assertEqual(identity('*C(F)(F)*'),identity('FC(*)(F)*'))

    def test_repeat_boundary_shift_and_chain_direction_are_equivalent(self):
        self.assertEqual(identity('*CCO*'),identity('*COC*'))
        self.assertEqual(identity('*CCO*'),identity('*OCC*'))

    def test_distinct_chemical_compositions_and_connectivity_stay_distinct(self):
        self.assertNotEqual(identity('*CCO*'),identity('*CO*'))
        self.assertNotEqual(identity('*CC(C)*'),identity('*CCC*'))
        self.assertNotEqual(identity('*CO*'),identity('*CS*'))

    def test_aromatic_repeat_is_retained_and_unary_isotope_not_erased(self):
        result=graph.normalize('*c1ccc(*)cc1')
        self.assertEqual(result['primitive_non_dummy_atoms'],6)
        self.assertNotEqual(identity('*[13CH2]*'),identity('*C*'))

    def test_port_labels_and_atom_maps_are_metadata_not_new_atoms(self):
        self.assertEqual(identity('[1*][CH2:7][CH2:8][2*]'),identity('*CC*'))

    def test_explicit_stereochemistry_and_ionic_or_multicomponent_models_are_held(self):
        for smiles in ['*C[C@H](F)*','*/C=C/*','*CC[NH2+]*','[Na+].*CC*']:
            with self.subTest(smiles=smiles),self.assertRaises(ValueError):
                graph.normalize(smiles)

    def test_wrong_connectivity_and_non_single_port_bonds_are_held(self):
        for smiles in ['CC','*CC','*C(*)C*','*=CC=*','bad']:
            with self.subTest(smiles=smiles),self.assertRaises(ValueError):
                graph.normalize(smiles)

    def test_successful_graph_comparison_does_not_claim_admission(self):
        result=graph.normalize('*CCO*')
        self.assertFalse(result['admitted'])
        self.assertEqual(result['independent_identity_review'],'not_run')

if __name__=='__main__':
    unittest.main()
