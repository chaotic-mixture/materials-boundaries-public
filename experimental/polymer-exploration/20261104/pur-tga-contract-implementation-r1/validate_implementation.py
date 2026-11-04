"""Bounded new-contract and affected-branch regressions, with exact inputs."""
from pathlib import Path
import hashlib
import io
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT), str(ROOT / 'tests')]
from materials_boundaries.database import Database


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(name, obj):
    with (OUT / name).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(obj, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def main():
    patterns = ['test_database*.py', 'test_tga_endpoint_contract.py',
                'test_material_reference_contract.py', 'test_material_uncertainty_contract.py',
                'test_material_reported_measures_contract.py', 'test_specified_elongation_contract.py',
                'test_strength_elongation_contract.py', 'test_shore_a_hardness_contract.py',
                'test_glass_transition_temperature_contract.py', 'test_melting_peak_temperature_contract.py',
                'test_glass_transition_method_context_contract.py',
                'test_dielectric_breakdown_strength_contract.py', 'test_thermal_conductivity_contract.py']
    suite = unittest.TestSuite([unittest.defaultTestLoader.discover(str(ROOT / 'tests'), pattern=p) for p in patterns])
    package = json.loads((OUT.parent / 'local-acceptance-r33/PACKAGE_INPUTS_R33.json').read_bytes())
    paths = {ROOT / name for name in package} | set((ROOT / 'schemas').glob('*.schema.json'))
    paths |= {ROOT / 'docs/MATERIAL_REFERENCE_CATALOG.md', Path(__file__)}
    for module in list(sys.modules.values()):
        name = getattr(module, '__file__', None)
        if name:
            path = Path(name).resolve()
            if path.is_relative_to(ROOT) and path.is_file():
                paths.add(path)
    inputs = {p.relative_to(ROOT).as_posix(): sha(p) for p in sorted(paths)}
    write('EXECUTION_INPUTS_R2.json', inputs)
    log = io.StringIO()
    result = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
    (OUT / 'implementation-tests-r2.log').write_text(log.getvalue(), encoding='utf-8', newline='\n')
    stable = all(sha(ROOT / name) == digest for name, digest in inputs.items())
    write('TEST_RESULTS_R2.json', {'patterns': patterns, 'tests_run': result.testsRun,
        'failures': len(result.failures), 'errors': len(result.errors), 'skipped': len(result.skipped),
        'successful': result.wasSuccessful(), 'stable_inputs': len(inputs), 'inputs_unchanged': stable,
        'full_history': 'not_run', 'installation': 'not_run', 'native_TGA_admission': False})
    assert result.wasSuccessful() and not result.skipped and stable
    db = Database()
    graph = db.validate_scientific_contracts()
    write('CURRENT_GRAPH_R1.json', {'snapshot': db.snapshot, 'graph': graph,
        'native_TGA_records': sum(len(list(db.records(quantity=q))) for q in (
            'thermal_degradation_onset_temperature', 'temperature_at_specified_mass_loss',
            'thermal_degradation_rate_peak_temperature', 'tga_residue_percentage'))})
    approved = json.loads((OUT.parent / 'pur-tga-endpoint-contract-proposal-r2/REVIEW_INPUTS_R2.json').read_bytes())
    assert all(sha(ROOT / name) == digest for name, digest in approved['native_files_sha256'].items())
    assert all(sha(ROOT / name) == digest for name, digest in inputs.items())
    print(json.dumps({'tests': result.testsRun, 'stable_inputs': len(inputs), 'snapshot': db.snapshot, 'native_TGA_records': 0}), flush=True)


if __name__ == '__main__':
    main()
