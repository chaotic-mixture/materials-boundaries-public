"""Original synthetic fixtures only; no provider data, network or mass claims."""
import copy
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import geometry_diagnostics as geo


def encoded(value):
    return json.dumps(value, sort_keys=True).encode()


def fixtures():
    source = {'url':'https://example.invalid/synthetic', 'version':'synthetic-v1', 'sha256':'a'*64}
    masses = {'schema':'geometry-masses/1', 'source':source, 'convention':'synthetic_test_only',
              'masses_u':{'H':1.0}, 'atomic_mass_constant_kg':{'value':1e-27, 'source':source}}
    units = {'schema':'nomad-geometry-units/1', 'source':source, 'nomad_commit':'1234567', 'units':dict(geo.UNITS)}
    structure = {'dimension_types':[1,1,1], 'lattice_vectors':[[1e-10,0,0],[0,1e-10,0],[0,0,1e-10]],
                 'cartesian_site_positions':[[0,0,0]], 'species_at_sites':['hydrogen'], 'n_sites':1,
                 'species':[{'name':'hydrogen','chemical_symbols':['H'],'concentration':[1.0]}],
                 'cell_volume':1e-30,'atomic_density':1e30,'mass_density':1000.0}
    row = {'entry_id':'synthetic-entry','archive':{'metadata':{'nomad_commit':'1234567'},
           'results':{'material':{'material_id':'synthetic-model','chemical_formula_hill':'H'},
                      'properties':{'structures':{'structure_original':structure}}}}}
    return {'data':[row], 'pagination':{'total':1}}, masses, units


def structure(data):
    return data['data'][0]['archive']['results']['properties']['structures']['structure_original']


def run(data=None, masses=None, units=None, **kwargs):
    original = fixtures()
    blobs = [encoded(x if x is not None else original[i]) for i,x in enumerate((data,masses,units))]
    return geo.diagnose(*blobs, expected_archive_sha256=geo.sha256(blobs[0]),
                        expected_mass_table_sha256=geo.sha256(blobs[1]), expected_unit_contract_sha256=geo.sha256(blobs[2]),
                        expected_entry_ids=['synthetic-entry'], **kwargs)


class GeometryDiagnosticsTests(unittest.TestCase):
    def test_cubic_volume_density_self_images_and_held_state(self):
        result = run(); row = result['records'][0]
        self.assertEqual(result['diagnostics_status'], 'consistency_checks_passed')
        self.assertAlmostEqual(row['computed_mass_density_kg_m3'],1000)
        self.assertAlmostEqual(row['minimum_pair_distance_m']/1e-10,1)
        self.assertTrue(row['includes_nonzero_self_images'])
        self.assertEqual(result['state'],'held'); self.assertEqual(result['admitted_delta'],0)
        self.assertFalse(result['scientific_review_approved']); self.assertFalse(result['rights_review_approved'])

    def test_triclinic_pair_distance(self):
        cell = [[1,0,0],[0.3,1.2,0],[0.2,0.4,1.1]]
        answer = geo.minimum_periodic_distance([[x*1e-10 for x in r] for r in cell],[[0,0,0],[1e-11,2e-11,3e-11]])
        self.assertAlmostEqual(answer['minimum_pair_distance_m']/1e-10, math.sqrt(0.14), places=12)

    def test_skew_nearest_translation_outside_fixed_27(self):
        answer = geo.minimum_periodic_distance([[1e-10,0,0],[1e-9,1e-11,0],[0,0,1e-10]],[[0,0,0],[5e-10,5e-12,0]])
        self.assertAlmostEqual(answer['minimum_pair_distance_m']/1e-10,0.05,places=12)

    def test_double_shear_nearest_image(self):
        cell = [[1,0,0],[12,1,0],[0,9,1]]
        answer = geo.minimum_periodic_distance([[x*1e-10 for x in r] for r in cell],[[0,0,0],[6e-10,5e-10,0.5e-10]])
        self.assertAlmostEqual(answer['minimum_pair_distance_m']/1e-10,0.5,places=10)

    def test_empty_improving_box_preserves_shorter_self_image(self):
        answer = geo.minimum_periodic_distance([[1e-10,0,0],[0,1e-8,0],[0,0,1e-8]],[[0,0,0],[0,5e-9,5e-9]])
        self.assertAlmostEqual(answer['minimum_pair_distance_m']/1e-10,1,places=12)

    def test_duplicate_periodic_sites_fail_without_leaking_geometry(self):
        data,_,_ = fixtures(); s=structure(data)
        s['cartesian_site_positions'].append([1e-10,0,0]); s['species_at_sites'].append('hydrogen'); s['n_sites']=2
        s['atomic_density']=2e30;s['mass_density']=2000
        result=run(data);self.assertEqual(result['diagnostics_status'],'held_checks_failed')
        self.assertFalse(result['records'][0]['checks']['no_duplicate_periodic_sites'])

    def test_invalid_lattice_positions_and_periodicity(self):
        for field,value in [('lattice_vectors',[[1,0],[0,1]]),('lattice_vectors',[[0,0,0]]*3),
                            ('cartesian_site_positions',[]),('cartesian_site_positions',[[False,0,0]]),
                            ('dimension_types',[True,1,1]),('dimension_types',[1,1,0]),('n_sites',0)]:
            with self.subTest(field=field,value=value):
                data,_,_=fixtures();structure(data)[field]=value
                self.assertEqual(run(data)['diagnostics_status'],'held_invalid_input')

    def test_zero_negative_nonfinite_or_boolean_source_denominators(self):
        for field in ['cell_volume','atomic_density','mass_density']:
            for value in [0,-1,False,float('nan'),float('inf')]:
                with self.subTest(field=field,value=value):
                    data,_,_=fixtures();structure(data)[field]=value
                    self.assertEqual(run(data)['diagnostics_status'],'held_invalid_input')

    def test_occupancy_and_species_ambiguity_hold(self):
        for change in ['partial','mixed','duplicate','missing','unknown','extra','non_string']:
            with self.subTest(change=change):
                data,_,_=fixtures();s=structure(data)
                if change=='partial':s['species'][0]['concentration']=[0.5]
                if change=='mixed':s['species'][0]['chemical_symbols']=['H','He'];s['species'][0]['concentration']=[0.5,0.5]
                if change=='duplicate':s['species']*=2
                if change=='missing':s['species_at_sites']=['missing']
                if change=='unknown':s['species'][0]['chemical_symbols']=['Xx']
                if change=='extra':s['species'][0]['mass']=[1.0]
                if change=='non_string':s['species'][0]['chemical_symbols']=[{}]
                self.assertEqual(run(data)['diagnostics_status'],'held_invalid_input')

    def test_formula_mismatch_is_failed_check(self):
        data,_,_=fixtures();data['data'][0]['archive']['results']['material']['chemical_formula_hill']='He'
        result=run(data);self.assertEqual(result['diagnostics_status'],'held_checks_failed')
        self.assertFalse(result['records'][0]['checks']['formula_site_composition_match'])

    def test_reduced_composition_not_raw_formula_site_count(self):
        data,_,_=fixtures();data['data'][0]['archive']['results']['material']['chemical_formula_hill']='H2'
        self.assertTrue(run(data)['records'][0]['checks']['formula_site_composition_match'])

    def test_mass_unit_and_processing_bindings_fail_closed(self):
        data,masses,units=fixtures();units['units']['lattice_vectors']='angstrom'
        self.assertEqual(run(units=units)['reason'],'unsupported_units')
        _,_,units=fixtures();units['nomad_commit']='7654321'
        self.assertEqual(run(units=units)['reason'],'processing_commit_mismatch')
        masses['masses_u']={'He':4};self.assertEqual(run(masses=masses)['reason'],'missing_element_mass')

    def test_all_three_source_denominator_errors_enforced(self):
        for source_key,check in [('cell_volume','volume_consistency'),('atomic_density','atomic_density_consistency'),('mass_density','density_mass_diagnostic_pass')]:
            with self.subTest(source_key=source_key):
                data,_,_=fixtures();structure(data)[source_key]*=1.01
                result=run(data);self.assertEqual(result['diagnostics_status'],'held_checks_failed')
                self.assertFalse(result['records'][0]['checks'][check])
                err=result['records'][0][{'cell_volume':'volume_relative_error','atomic_density':'atomic_density_relative_error','mass_density':'density_mass_diagnostic_relative_error'}[source_key]]
                self.assertAlmostEqual(err,0.01/1.01,places=12)

    def test_tolerances_cannot_be_loosened(self):
        for kwargs in [{'density_tolerance':0.003},{'volume_tolerance':1e-7},{'atomic_density_tolerance':1e-7},{'density_tolerance':0},
                       {'density_tolerance':float('nan')},{'density_tolerance':float('inf')},{'density_tolerance':'PRIVATE_TEXT'}, {'density_tolerance':{}}]:
            with self.subTest(kwargs=kwargs):
                result=run(**kwargs);self.assertEqual(result['reason'],'invalid_tolerance')
                self.assertNotIn('PRIVATE_TEXT',json.dumps(result,allow_nan=False))
        self.assertEqual(run(density_tolerance=0.001)['diagnostics_status'],'consistency_checks_passed')

    def test_work_budget_ill_conditioned_and_coordinate_limits(self):
        self.assertEqual(run(max_evaluations=1)['reason'],'distance_work_budget_exceeded')
        data,_,_=fixtures();structure(data)['lattice_vectors']=[[1e-10,0,0],[0,1e-10,0],[0,0,1e-22]]
        self.assertEqual(run(data)['diagnostics_status'],'held_invalid_input')
        data,_,_=fixtures();structure(data)['cartesian_site_positions']=[[1,0,0]]
        self.assertEqual(run(data)['reason'],'excessive_coordinate_magnitude')

    def test_input_hash_duplicate_json_and_cohort_integrity(self):
        data,masses,units=fixtures();blobs=list(map(encoded,[data,masses,units]))
        result=geo.diagnose(*blobs,expected_archive_sha256='0'*64,expected_mass_table_sha256=geo.sha256(blobs[1]),expected_unit_contract_sha256=geo.sha256(blobs[2]),expected_entry_ids=['synthetic-entry'])
        self.assertEqual(result['reason'],'input_hash_mismatch')
        result=geo.diagnose('PRIVATE_TEXT',blobs[1],blobs[2],expected_archive_sha256='0'*64,expected_mass_table_sha256=geo.sha256(blobs[1]),expected_unit_contract_sha256=geo.sha256(blobs[2]),expected_entry_ids=['synthetic-entry'])
        self.assertEqual(result['reason'],'expected_input_bytes');self.assertNotIn('PRIVATE_TEXT',json.dumps(result,allow_nan=False))
        with self.assertRaises(geo.DiagnosticError):geo.strict_load(b'{"data":[],"data":[]}')
        with self.assertRaises(geo.DiagnosticError):geo.strict_load(b'{"unused":1e400}')
        with self.assertRaises(geo.DiagnosticError):geo.strict_load(b'{"unused":'+b'9'*5000+b'}')
        data['pagination']['next_page_after_value']='another';self.assertEqual(run(data)['reason'],'incomplete_cohort_pagination')
        data,_,_=fixtures();data['data']*=2;self.assertEqual(run(data)['reason'],'invalid_cohort_rows')

    def test_malformed_nested_shapes_do_not_escape_or_echo(self):
        for field,value in [('species',[[]]),('species',[{'name':'x','chemical_symbols':[[]],'concentration':[1]}]),
                            ('species_at_sites',[{}]),('cell_volume',{}),('cartesian_site_positions',{'PRIVATE_SECRET':True})]:
            with self.subTest(field=field,value=value):
                data,_,_=fixtures();structure(data)[field]=value
                result=run(data);self.assertEqual(result['diagnostics_status'],'held_invalid_input')
                self.assertNotIn('PRIVATE_SECRET',json.dumps(result))
        data,_,_=fixtures();data['data'][0]['archive']=[]
        self.assertEqual(run(data)['diagnostics_status'],'held_invalid_input')
        _,masses,_=fixtures();masses['source']['url']={}
        self.assertEqual(run(masses=masses)['diagnostics_status'],'held_invalid_input')

    def test_optional_entry_and_elements_bindings(self):
        data,_,_=fixtures();archive=data['data'][0]['archive']
        archive['metadata']['entry_id']='synthetic-entry';archive['results']['material']['elements']=['H']
        self.assertEqual(run(data)['diagnostics_status'],'consistency_checks_passed')
        archive['metadata']['entry_id']='different'
        self.assertEqual(run(data)['reason'],'metadata_entry_id_mismatch')
        archive['metadata']['entry_id']='synthetic-entry';archive['results']['material']['elements']=['He']
        self.assertEqual(run(data)['reason'],'material_elements_mismatch')

    def test_safe_output_determinism_and_input_immutability(self):
        data,masses,units=fixtures();data['data'][0]['archive']['metadata']['private_comment']='PRIVATE_MARKER_COORDINATES'
        before=copy.deepcopy((data,masses,units));result=run(data,masses,units)
        self.assertEqual(result,run(data,masses,units));self.assertEqual(before,(data,masses,units))
        text=json.dumps(result)
        for forbidden in ['lattice_vectors','cartesian_site_positions','species_at_sites','chemical_symbols','PRIVATE_MARKER_COORDINATES','https://example.invalid']:
            self.assertNotIn(forbidden,text)

    def test_missing_n_sites_is_labeled_derived_site_count(self):
        data,_,_=fixtures();del structure(data)['n_sites']
        self.assertEqual(run(data)['records'][0]['site_count'],1)

    def test_cli_external_directory_and_safe_file_error(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory);args=[]
            values=fixtures();values[0]['data'][0]['entry_id']='-synthetic-entry'
            for name,value in zip(['archive','masses','units'],values):
                raw=encoded(value);target=p/(name+'.json');target.write_bytes(raw)
                args += ['--'+name,str(target),'--'+name+'-sha256',geo.sha256(raw)]
            command=[sys.executable,'-B',str(Path(geo.__file__).resolve()),*args,'--entry-id=-synthetic-entry']
            result=subprocess.run(command,cwd=p,capture_output=True,text=True,timeout=10)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual(json.loads(result.stdout)['state'],'held')
            (p/'archive.json').unlink()
            result=subprocess.run(command,cwd=p,capture_output=True,text=True,timeout=10)
            self.assertEqual(result.returncode,2);self.assertNotIn(str(p),result.stdout+result.stderr)
            with self.assertRaises(geo.DiagnosticError):geo.read_private(p)


if __name__ == '__main__':
    unittest.main()
