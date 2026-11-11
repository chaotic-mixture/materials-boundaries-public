"""Archive and minimally update branch/profile guards for the new contract."""
from pathlib import Path
import hashlib,json,shutil
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
EXT=ROOT.parent/'open-database-evidence/polymer-thermal-response-contract-20261111-r1'
def main():
    names=['test_compression_reference_contract.py','test_flexural_elongation_contract.py','test_izod_impact_contract.py','test_glass_transition_temperature_contract.py','test_melting_peak_temperature_contract.py','test_tear_strength_contract.py','test_shore_a_hardness_contract.py','test_tga_endpoint_contract.py','test_thermal_transport_derivation_contract.py']
    base=EXT/'before-test-guard-update';base.mkdir();hashes={}
    for n in names:
        p=ROOT/'tests'/n;shutil.copyfile(p,base/n);hashes[n]=hashlib.sha256(p.read_bytes()).hexdigest();s=p.read_text('utf-8')
        if n!='test_thermal_transport_derivation_contract.py':
            updated=s.replace("oneOf']), 14)","oneOf']), 15)").replace("oneOf']),14)","oneOf']),15)");assert updated!=s;s=updated
        if n=='test_tga_endpoint_contract.py':
            needle="            methods.remove('source_reported_thermal_transport_product')";assert s.count(needle)==1
            s=s.replace(needle,needle+"\n            self.assertEqual(methods.count('source_reported_thermal_response_fit'),1)\n            methods.remove('source_reported_thermal_response_fit')")
        if n=='test_thermal_transport_derivation_contract.py':
            s=s.replace("old,new=schema['$defs']['derivation']['oneOf']","old,new,fit=schema['$defs']['derivation']['oneOf']\n        self.assertEqual(fit['properties']['profile_id']['const'],'thermal_temperature_decay_fit_with_cited_method_v1')")
            s=s.replace("original_branches=deepcopy(schema['$defs']['property']['oneOf'])","original_branches=deepcopy(schema['$defs']['property']['oneOf'][:14])")
            needle='            self.assertEqual(methods.count(TRANSPORT_METHOD),1);methods.remove(TRANSPORT_METHOD)';assert s.count(needle)==1
            s=s.replace(needle,needle+"\n            self.assertEqual(methods.count('source_reported_thermal_response_fit'),1);methods.remove('source_reported_thermal_response_fit')")
        p.write_text(s,encoding='utf-8',newline='\n')
    with (HERE/'OLD_TEST_GUARD_UPDATE_R1.json').open('x',encoding='utf-8',newline='\n') as f:json.dump(dict(before_sha256=hashes,eight_branch_count_guards='14to15',legacy_hashes='Unchanged;comparison copies remove only added method,old14branch prefix explicit',old_two_profile_objects='Retained;new third profile asserted'),f,indent=2);f.write('\n')
    print('9 old test files archived;only count/profile extension guards updated')
if __name__=='__main__':main()
