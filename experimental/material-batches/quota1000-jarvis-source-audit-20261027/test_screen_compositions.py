"""Check source anomaly handling, exact composition grouping and scope rejection."""
from copy import deepcopy
from io import StringIO
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parent))
import screen_compositions as source

def row():
    value = {'jid':'JVASP-42','formula':'AlNi','nat':2,'density':5.25,
             'func':'OptB88vdW','dimensionality':'3D-bulk','typ':'bulk',
             'atoms':{'elements':['Al','Ni'],'coords':[[0,0,0],[1,1,1]],
                      'lattice_mat':[[2,0,0],[0,2,0],[0,0,2]]},
             'spg_number':'221','reference':'source-parent'}
    return source.DECODER.decode(json.dumps(value))

class JarvisSourceScreenTests(unittest.TestCase):
    def test_chunked_array_preserves_exact_source_number_and_unicode(self):
        raw=' [ {"label":"铝", "density":5.250}, {"density":1e-3} ] '
        for chunk in [1,2,7,20,1000]:
            rows=list(source.array_objects(StringIO(raw),chunk))
            self.assertEqual(rows[0][0]['label'],'铝')
            self.assertIs(type(rows[0][0]['density']),source.NumberToken)
            self.assertEqual(rows[0][0]['density'],'5.250')
            self.assertEqual(rows[1][0]['density'],'1e-3')
            self.assertIn('"density":5.250',rows[0][1])

    def test_truncated_trailing_foreign_or_duplicate_json_is_rejected(self):
        for raw in ['','{}','[1]','[{"a":1}','[{},]','[{} {}]','[] false','[{"x":1,"x":2}]']:
            with self.subTest(raw=raw),self.assertRaises(ValueError):
                list(source.array_objects(StringIO(raw),2))
        self.assertEqual(list(source.array_objects(StringIO(' [ ] '),1)),[])

    def test_nonfinite_source_tokens_are_typed_not_runtime_numbers(self):
        rows=list(source.array_objects(StringIO('[{"elastic_tensor":[[NaN, Infinity, -Infinity]]}]'),4))
        value=rows[0][0]
        self.assertIs(type(value['elastic_tensor'][0][0]),source.SourceNonfiniteToken)
        self.assertEqual(list(source.source_nonfinite_paths(value)),
                         [('elastic_tensor[*][*]','NaN'),('elastic_tensor[*][*]','Infinity'),('elastic_tensor[*][*]','-Infinity')])

    def test_exact_ratio_merges_element_order_and_cell_multiples(self):
        self.assertEqual(source.formula_key('NiAl'),source.formula_key('Al2Ni2'))
        self.assertEqual(source.formula_key('Al0.5Ni0.5'),source.ratio_key({'Ni':8,'Al':8}))
        self.assertNotEqual(source.formula_key('AlNi3'),source.formula_key('AlNi'))

    def test_unresolved_or_invalid_formula_never_receives_a_key(self):
        for value in ['Al2(Ni)2','Al-1Ni','Xx2','Al0Ni','AlNi!','',None]:
            with self.subTest(formula=value),self.assertRaises(ValueError):
                source.formula_key(value)

    def test_selected_density_requires_a_positive_finite_source_numeric_token(self):
        for value in [source.NumberToken('0'),source.NumberToken('-1'),
                      source.SourceNonfiniteToken('NaN'),source.SourceNonfiniteToken('Infinity'),
                      '5.25',True,None]:
            changed=row();changed['density']=value
            with self.subTest(value=value),self.assertRaises(ValueError):
                source.row_facts(changed)
        facts=source.row_facts(row())
        self.assertEqual(facts['source_density_token'],'5.25')

    def test_formula_nat_and_geometry_cannot_disagree_with_selected_structure(self):
        for mutation in [lambda x:x.update(formula='AlNi2'),lambda x:x.update(nat=source.NumberToken('3')),
                         lambda x:x['atoms']['coords'].pop(),lambda x:x['atoms']['elements'].append('Xx'),
                         lambda x:x['atoms']['coords'][0].__setitem__(0,source.SourceNonfiniteToken('NaN'))]:
            changed=row();mutation(changed)
            with self.assertRaises(ValueError):
                source.row_facts(changed)

    def test_computation_and_bulk_scope_are_not_inferred_from_density(self):
        for key,value in [('func','PBE'),('dimensionality','na'),('dimensionality','2D-bulk'),('typ','molecule')]:
            changed=row();changed[key]=value
            with self.subTest(field=key,value=value),self.assertRaises(ValueError):
                source.row_facts(changed)

    def test_screen_buckets_are_compositional_and_do_not_claim_metallic_behavior(self):
        metal=row();metal['optb88vdw_bandgap']=source.NumberToken('2.0')
        self.assertEqual(source.row_facts(metal)['screening_bucket'],'all_metal_elements')
        oxide=row();oxide['formula']='MgO';oxide['atoms']['elements']=['Mg','O']
        self.assertEqual(source.row_facts(oxide)['screening_bucket'],'oxygen_containing_no_C_H')
        organic=row();organic['formula']='CO';organic['atoms']['elements']=['C','O']
        self.assertEqual(source.row_facts(organic)['screening_bucket'],'other_requires_classification')
        self.assertNotIn('admitted',source.row_facts(oxide))

    def test_source_summary_reconciles_all_rows_and_keeps_admission_unknown(self):
        summary=json.loads((Path(__file__).parent/'screening-summary.json').read_bytes())
        self.assertEqual(summary['counts']['source_rows'],93902)
        self.assertEqual(summary['counts']['eligible_rows']+sum(summary['exclusions_by_reason'].values()),93902)
        self.assertEqual(sum(summary['groups_by_screening_bucket'].values()),summary['reduced_composition_groups'])
        self.assertEqual(summary['admitted_increment'],0)
        self.assertIsNone(summary['approved_unique_material_count'])
        self.assertGreater(summary['groups_by_screening_bucket']['all_metal_elements'],1000)
        self.assertGreater(summary['groups_by_screening_bucket']['oxygen_containing_no_C_H'],1000)

if __name__=='__main__':
    unittest.main()
