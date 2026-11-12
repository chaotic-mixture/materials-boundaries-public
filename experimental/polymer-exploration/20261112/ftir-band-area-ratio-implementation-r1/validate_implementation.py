"""Fresh extension and existing contract regression; no source admission or history replay."""
from pathlib import Path
import ast,hashlib,io,json,sys,unittest
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(ROOT),str(ROOT/'tests')]
def main():
    tree=ast.parse((ROOT/'experimental/polymer-exploration/20261104/delivery-r36-r38/validate_delivery.py').read_text(encoding='utf-8'))
    patterns=next(ast.literal_eval(n.value) for n in ast.walk(tree) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='patterns' for t in n.targets))
    patterns.extend(['test_volumetric_work_contract.py','test_thermal_capacity_diffusivity_contract.py','test_thermal_transport_derivation_contract.py','test_thermal_response_fit_contract.py','test_dtg_unknown_ordinal_contract.py','test_crystallization_phase_contract.py','test_tga_endset_contract.py','test_tensile_extension_contract.py','test_water_absorption_contract.py','test_closed_cell_contract.py','test_foam_event_contract.py','test_cell_anisotropy_contract.py','test_dsc_enthalpy_contract.py','test_complex_viscosity_contract.py','test_gel_fraction_contract.py','test_dma_flexural_contract.py','test_dsc_crystallinity_contract.py','test_ftir_band_area_ratio_contract.py'])
    suite=unittest.TestSuite([unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern=p) for p in patterns])
    paths=set((ROOT/'materials_boundaries').rglob('*.py'))|set((ROOT/'materials_boundaries/data').glob('*.json'))|set((ROOT/'schemas').glob('*.json'))|{Path(__file__),ROOT/'tests/fixtures/tensile_extension_schema_baseline.json',ROOT/'tests/fixtures/water_absorption_schema_baseline.json',ROOT/'tests/fixtures/closed_cell_schema_baseline.json',ROOT/'tests/fixtures/foam_event_schema_baseline.json',ROOT/'tests/fixtures/cell_anisotropy_schema_baseline.json',ROOT/'tests/fixtures/dsc_melting_enthalpy_schema_baseline.json',ROOT/'tests/fixtures/complex_viscosity_schema_baseline.json',ROOT/'tests/fixtures/gel_fraction_schema_baseline.json',ROOT/'tests/fixtures/dma_flexural_schema_baseline.json',ROOT/'tests/fixtures/dsc_crystallinity_schema_baseline.json',ROOT/'tests/fixtures/ftir_band_area_ratio_schema_baseline.json'}
    for module in list(sys.modules.values()):
        name=getattr(module,'__file__',None)
        if name:
            p=Path(name).resolve()
            if p.is_relative_to(ROOT) and p.is_file():paths.add(p)
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    before={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(paths)}
    with (HERE/'AFFECTED_INPUTS_R1.json').open('x',encoding='utf-8') as f:json.dump(before,f,indent=2)
    log=io.StringIO();r=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
    (HERE/'affected-tests-r1.log').write_text(log.getvalue(),encoding='utf-8',newline='\n')
    stable=all(sha(ROOT/n)==h for n,h in before.items())
    result=dict(tests=r.testsRun,failures=len(r.failures),errors=len(r.errors),skipped=len(r.skipped),successful=r.wasSuccessful(),stable_inputs=len(before),inputs_unchanged=stable,scope='Fresh FTIR area ratio implementation409 checks,current5753-property baseline;not historical sum',installation_native_admission='not_run')
    with (HERE/'AFFECTED_RESULTS_R1.json').open('x',encoding='utf-8') as f:json.dump(result,f,indent=2)
    print(json.dumps(result),flush=True)
    assert r.wasSuccessful() and r.testsRun==409 and stable and not r.skipped
if __name__=='__main__':main()
