import copy
import json
import math
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from nomad_batch import *

def fixture(eid='entry_1',mid='material_1',formula='Fe2Ni2'):
    return {'entry_id':eid,'archive':{'metadata':{'license':'CC BY 4.0','external_db':'OQMD','nomad_version':'1','nomad_commit':'abc','last_processing_time':'2020','mainfile':'test'},'results':{'material':{'material_id':mid,'elements':sorted(composition(formula)[1]),'chemical_formula_hill':formula,'structural_type':'bulk','symmetry':{'space_group_number':225}},'method':{'method_name':'DFT','simulation':{'program_name':'VASP'}},'properties':{'structures':{'structure_original':{'mass_density':8000,'dimension_types':[1,1,1]}}}}}}

def run(rows, existing=()):
    return normalize(rows,{r['entry_id']:{'authors':[{'name':'Scientist'}]} for r in rows},{r['entry_id']:{'sha256':'fixture'} for r in rows},existing)

class ScientificIdentityTests(unittest.TestCase):
    def test_same_material_multiple_calculations_one_candidate(self):
        p=run([fixture(),fixture('entry_2')]);self.assertEqual(len(p['candidates']),1);self.assertEqual(p['candidates'][0]['dedup']['sample_entry_count'],2)
    def test_same_formula_different_material_groups_not_merged(self):
        p=run([fixture(),fixture('entry_2','material_2')]);self.assertEqual(len(p['candidates']),2);self.assertIsNone(p['counts']['global_unique_material_total'])
    def test_formula_alone_is_never_identity(self):
        r=fixture();del r['archive']['results']['material']['material_id'];self.assertEqual(run([r])['counts']['candidate_provider_material_groups'],0)
    def test_conflicting_formula_quarantines_group(self):
        p=run([fixture(),fixture('entry_2',formula='FeNi2')]);self.assertEqual(p['counts']['exclusion_reasons'],{'provider_identity_conflict':2})
    def test_conflicting_symmetry_quarantines_group(self):
        r=fixture('entry_2');r['archive']['results']['material']['symmetry']['space_group_number']=1
        self.assertEqual(run([fixture(),r])['counts']['candidate_provider_material_groups'],0)
    def test_repeated_same_entry_not_new_material(self):
        self.assertEqual(run([fixture(),fixture()])['counts']['exclusion_reasons'],{'duplicate_calculation_entry':2})
    def test_conflicting_duplicate_entry_all_quarantined(self):
        a=fixture();b=fixture();b['archive']['results']['properties']['structures']['structure_original']['mass_density']=123
        self.assertEqual(run([a,b]),run([b,a]))
        self.assertEqual(run([a,b])['counts']['candidate_provider_material_groups'],0)
    def test_mixed_named_unnamed_authors_quarantined(self):
        self.assertEqual(normalize([fixture()],{'entry_1':{'authors':[{'name':'Named'},{}]}}, {})['counts']['exclusion_reasons'],{'missing_attribution':1})
    def test_null_method_quarantined(self):
        r=fixture();r['archive']['results']['method']=None
        self.assertEqual(run([r])['counts']['exclusion_reasons'],{'unsupported_method':1})
    def test_boolean_dimensions_quarantined(self):
        r=fixture();r['archive']['results']['properties']['structures']['structure_original']['dimension_types']=[True]*3
        self.assertEqual(run([r])['counts']['exclusion_reasons'],{'not_three_dimensional':1})
    def test_seed_overlap_excluded(self):
        self.assertEqual(run([fixture()],['material_1'])['counts']['exclusion_reasons'],{'already_in_reviewed_computed_seed':1})
    def test_scaled_formula_is_same_composition(self):
        self.assertEqual(run([fixture(),fixture('entry_2',formula='FeNi')])['counts']['candidate_provider_material_groups'],1)
    def test_deterministic_selection(self):
        self.assertEqual(run([fixture('z'),fixture('a')]),run([fixture('a'),fixture('z')]))
    def test_reject_nonpositive_nonfinite_boolean(self):
        for value in (0,-1,float('nan'),float('inf'),True,'8000'):
            r=fixture();r['archive']['results']['properties']['structures']['structure_original']['mass_density']=value
            self.assertEqual(len(run([r])['candidates']),0)
    def test_rights_unknown_quarantined(self):
        r=fixture();r['archive']['metadata']['license']='unknown';self.assertEqual(run([r])['counts']['exclusion_reasons'],{'rights_quarantine':1})
    def test_missing_attribution_rejected(self):
        self.assertEqual(normalize([fixture()],{}, {})['counts']['exclusion_reasons'],{'missing_attribution':1})
    def test_empty_author_projection_rejected(self):
        self.assertEqual(normalize([fixture()],{'entry_1':{'authors':[{}]}}, {})['counts']['exclusion_reasons'],{'missing_attribution':1})
    def test_carbon_category_quarantined(self):
        self.assertEqual(run([fixture(formula='CFe')])['counts']['exclusion_reasons'],{'carbon_category_review_required':1})
    def test_inorganic_category(self):
        self.assertEqual(run([fixture(formula='Fe2O3')])['counts']['category_candidates'],{'inorganic':1})
    def test_invalid_formulas(self):
        for f in ('','Fe0','Fe01','FeFe','Xx','Fe2O3junk','Fe(OH)2','Fe1.5','Fe-2'):
            with self.assertRaises(ValueError): composition(f)
    def test_geometry_guard_nested(self):
        with self.assertRaises(ValueError): assert_no_geometry({'data':[{'results':{'lattice_vectors':[]}}]})
    def test_request_limit_no_network(self):
        with tempfile.TemporaryDirectory() as d:
            c=Collector(d);c.log=[{}]*MAX_REQUESTS
            with patch('urllib.request.urlopen',side_effect=AssertionError('network')):
                with self.assertRaises(ValueError):c.fetch('entries/query',{})
    def test_byte_limit_no_network(self):
        with tempfile.TemporaryDirectory() as d:
            c=Collector(d);c.log=[{'bytes':MAX_BYTES}]
            with self.assertRaises(ValueError): c.fetch('entries/query',{})
    def test_pages_limit(self):
        for value in (0,11,True):
            with self.assertRaises(ValueError): collect('unused',value)
    def test_evidence_tamper(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'raw').mkdir();(p/'raw/001.json').write_bytes(b'{}')
            write(p/'acquisition.json',[{'file':'raw/001.json','bytes':2,'sha256':'bad'}])
            with self.assertRaisesRegex(ValueError,'hash'):load_evidence(p)

if __name__=='__main__':unittest.main()
