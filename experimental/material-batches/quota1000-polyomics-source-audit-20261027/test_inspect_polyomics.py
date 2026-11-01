"""Verify CSV fidelity and separation of simulation rows from polymer identities."""
from copy import deepcopy
import csv
import io
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parent))
import inspect_polyomics as audit

def row():
    value={key:'' for key in audit.REQUIRED}
    value.update(UUID='00000000-0000-4000-8000-000000000001',smiles_list='*CC*',smiles_1='*CC*',
                 density='1.2500',temp='300.0',press='1.0',forcefield='source-forcefield',
                 RadonPy_ver='source-version',preset_eq_ver='source-preset',check_eq='True',tacticity='none')
    return value

def csv_bytes(rows,fields=None):
    stream=io.StringIO(newline='');writer=csv.DictWriter(stream,fields or list(audit.REQUIRED));writer.writeheader();writer.writerows(rows)
    return stream.getvalue().encode('utf8')

class PolyOmicsAuditTests(unittest.TestCase):
    def test_quoted_source_text_and_density_significant_zeros_are_retained(self):
        value=row();value['smiles_list']='*CC*,*O*'
        parsed=list(audit.read_rows(csv_bytes([value])))
        facts=audit.selected_facts(parsed[0][1])
        self.assertEqual(facts['source_smiles_list'],'*CC*,*O*')
        self.assertEqual(facts['source_density_literal'],'1.2500')
        self.assertEqual(facts['source_conditions']['press'],'1.0')

    def test_missing_duplicate_and_wrong_width_source_columns_are_rejected(self):
        for raw in [b'UUID,density\nx,1\n',b'UUID,UUID\nx,y\n',csv_bytes([row()])+b'extra,cell\n']:
            with self.subTest(raw=raw[:25]),self.assertRaises(ValueError):
                list(audit.read_rows(raw))

    def test_nonpositive_nonfinite_or_invalid_density_is_held(self):
        for number in ['NaN','Infinity','-Infinity','-1','0','bad','']:
            value=row();value['density']=number
            with self.subTest(value=number),self.assertRaises(ValueError):
                audit.selected_facts(value)

    def test_source_equilibrium_flag_and_uuid_are_not_inferred(self):
        for key,value in [('check_eq','False'),('check_eq',''),('UUID','bad')]:
            changed=row();changed[key]=value
            with self.subTest(key=key,value=value),self.assertRaises(ValueError):
                audit.selected_facts(changed)

    def test_repeated_simulations_and_tacticities_do_not_become_polymer_counts(self):
        first=row();second=deepcopy(first);second.update(UUID='00000000-0000-4000-8000-000000000002',tacticity='atactic')
        summary,_=audit.summarize_rows(enumerate([first,second]))
        self.assertEqual(summary['source_valid_density_rows'],2)
        self.assertEqual(summary['literal_unique_smiles_1'],1)
        self.assertIsNone(summary['canonical_polymer_identity_count'])
        self.assertEqual(summary['admitted_increment'],0)
        with self.assertRaises(ValueError):
            audit.summarize_rows(enumerate([first,first]))

    def test_multiple_components_or_ports_do_not_pass_linear_text_screen(self):
        first=row();first['smiles_2']='*O*'
        second=row();second['UUID']='00000000-0000-4000-8000-000000000002';second['smiles_1']='*C(*)C*'
        summary,_=audit.summarize_rows(enumerate([first,second]))
        self.assertEqual(summary['source_valid_density_rows'],2)
        self.assertEqual(summary['single_component_two_star_text_rows'],0)

    def test_frozen_audit_records_actual_file_counts_instead_of_card_counts(self):
        result=json.loads((Path(__file__).parent/'source-audit.json').read_bytes())
        self.assertEqual(result['source_files']['PFAS.csv']['source_rows'],5810)
        self.assertEqual(result['source_files']['biodegradable_candidate_polyester.csv']['source_rows'],372)
        self.assertIsNone(result['canonical_polymer_identity_count'])
        self.assertEqual(result['admitted_increment'],0)
        self.assertEqual(result['cross_file_conflicting_selected_fact_uuids'],[])

if __name__=='__main__':
    unittest.main()
