"""Run provider fixtures separately from lifecycle/integration and installed smoke."""
import argparse
from email.parser import BytesParser
import hashlib
import importlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PACKAGES = {
    'materials_boundaries_federation_prototype': ROOT / 'federation',
    'materials_boundaries_query_service': ROOT / 'query-service',
    'materials_lifecycle_prototype': ROOT / 'lifecycle',
    'materials_boundaries_platform_experimental': ROOT,
}
SUITES = {
    'provider-fixtures': ('federation/tests', 19),
    'api-fixtures': ('query-service/tests', 37),
    'lifecycle': ('lifecycle/tests', 25),
    'linked-integration': ('tests', 18),
    'nomad-ingestion': ('ingestion', 106),
    'hbn-projection': ('relationships', 14),  # Checkout-only; isolated from installed smoke.
}


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def check_wheels(directory):
    wheels = sorted(directory.glob('*.whl'))
    require(len(wheels) == 4, 'Expected exactly four local wheels')
    for name, source in PACKAGES.items():
        version = '0.5.0.dev0' if name in {'materials_boundaries_query_service', 'materials_boundaries_platform_experimental'} else '0.1.0'
        matches = list(directory.glob(name + '-' + version + '-*.whl'))
        require(len(matches) == 1, 'Missing or duplicate wheel: ' + name)
        with zipfile.ZipFile(matches[0]) as wheel:
            metadata_paths = [n for n in wheel.namelist() if n.endswith('.dist-info/METADATA')]
            require(len(metadata_paths) == 1, 'Missing distribution metadata')
            metadata = BytesParser().parsebytes(wheel.read(metadata_paths[0]))
            for license_name in ('LICENSE', 'THIRD_PARTY_NOTICES.md'):
                require(license_name in metadata.get_all('License-File', []), 'Missing License-File declaration')
                members = [n for n in wheel.namelist() if '.dist-info/' in n and n.endswith('/' + license_name)]
                require(len(members) == 1, 'Missing or duplicate license/notice')
                require(wheel.read(members[0]) == (source / license_name).read_bytes(), 'License/notice bytes changed')
        print('License/notice bytes and metadata verified:', matches[0].name, flush=True)


def test_ids(suite):
    for test in suite:
        if isinstance(test, unittest.TestSuite):
            yield from test_ids(test)
        else:
            yield test.id()


def discover_suite(name, directory, minimum):
    loader = unittest.TestLoader()
    suite = loader.discover(str(directory), pattern='test*.py')
    require(not loader.errors, name + ': discovery errors: ' + '\n'.join(loader.errors))
    ids = list(test_ids(suite))
    count = len(ids)
    require(count == len(set(ids)), name + ': duplicate discovered test IDs')
    require(count >= minimum, f'{name}: expected at least {minimum} tests, found {count}')
    inventory = json.loads((Path(__file__).with_name('required_test_ids.json')).read_text(encoding='utf-8'))
    required_ids = inventory[name] if name in ('nomad-ingestion', 'local-catalog', 'hbn-projection') else []
    missing = sorted(set(required_ids) - set(ids))
    require(not missing, name + ': missing required test IDs: ' + ', '.join(missing))
    print('DISCOVERED ' + json.dumps({'suite': name, 'count': count, 'test_ids': ids}, sort_keys=True), flush=True)
    return suite


def run_discovered_suite(name, directory, minimum):
    suite = discover_suite(name, directory, minimum)
    count = suite.countTestCases()
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    require(result.testsRun == count, name + ': not every discovered test ran')
    require(result.wasSuccessful() and not result.skipped and not result.expectedFailures,
            name + ': failures, errors, skips or expected failures are not a full pass')
    print(f'OFFLINE {name}: {count} tests passed (minimum {minimum})', flush=True)


def run_suite(name):
    relative, minimum = SUITES[name]
    run_discovered_suite(name, ROOT / relative, minimum)


def run_cli(command, *args):
    executable = Path(sys.executable).parent / command
    return subprocess.check_output([str(executable), *map(str, args)], text=True)


def installed_smoke():
    # This process starts outside the checkout and cannot import source packages.
    for name in ('materials_platform', 'materials_federation', 'materials_query', 'materials_lifecycle'):
        module = importlib.import_module(name)
        require(Path(module.__file__).resolve().is_relative_to(Path(sys.prefix).resolve()),
                'Smoke imported source instead of installed wheel: ' + name)
    from fastapi.testclient import TestClient
    from materials_query.app import create_app
    with TestClient(create_app()) as client:
        response = client.get('/api/health')
        require(response.status_code == 200 and response.json()['upstream_health'] == 'not_checked', 'Health smoke failed')
        response = client.post('/api/demo', json={'provider': 'materials_project'})
        require(response.status_code == 200, 'Synthetic MP fixture smoke failed')
        require(response.json()['page']['fixture'] is True, 'Demo mislabeled as live')
        require(client.post('/api/search', json={'provider': 'materials_project', 'formula': 'Si'}).status_code == 503,
                'Unconfigured MP live path must be disabled')
        require(client.get('/openapi.json').status_code == 200, 'OpenAPI smoke failed')
    with tempfile.TemporaryDirectory(prefix='installed-platform-smoke-') as temp:
        folder = Path(temp)
        archives = []
        for label in ('first', 'second'):
            store = folder / label
            summary = json.loads(run_cli('materials-platform', '--output', store))
            require(summary['fixture'] and summary['canonical_material_admissions'] == 0, 'Demo admitted canonical material')
            require(summary['typed_candidate_state'] == 'pending_review', 'Typed candidate unexpectedly approved')
            require(summary['release_archive_self_contained_raw_replay'] is False, 'Incorrect archive replay claim')
            binding = json.loads((store / summary['binding']).read_text())
            require(hashlib.sha256((store / binding['raw_path']).read_bytes()).hexdigest() == binding['raw_sha256'], 'Raw link broken')
            require(hashlib.sha256((store / binding['typed_candidate_path']).read_bytes()).hexdigest() == binding['typed_candidate_sha256'], 'Typed link broken')
            review = json.loads((store / summary['review']).read_text())
            manifest = json.loads((store / summary['release'] / 'manifest.json').read_text())
            require(Path(summary['binding']).stem in review['rationale'], 'Review missing binding')
            require(manifest['decision_sha256'] == Path(summary['review']).stem, 'Release missing exact review')
            require(manifest['counts']['production_admitted'] == manifest['counts']['properties'] == 0, 'Scientific properties admitted')
            archives.append((store / summary['release'] / 'dataset.tar').read_bytes())
        require(archives[0] == archives[1], 'Independent demo archives are not byte-identical')
        fixture = ROOT / 'lifecycle/fixtures/nomad_response.json'
        acquisition = run_cli('materials-lifecycle', '--store', folder / 'lifecycle', 'capture', '--formula', 'CaFe2Re', '--fixture', fixture).strip()
        batch = run_cli('materials-lifecycle', '--store', folder / 'lifecycle', 'stage', acquisition).strip()
        require(Path(batch).is_file(), 'Installed lifecycle fixture staging failed')
    print('Installed CLI/API fixtures, linked provenance, zero admission and deterministic archive passed', flush=True)


def main():
    require(getattr(sys, '_platform_ci_offline', False), 'Offline guard failed to load')
    # Verify the guard without issuing a network request.
    import socket
    try:
        socket.getaddrinfo('ci-guard.invalid', 443)
    except RuntimeError as error:
        require('Offline fixture CI' in str(error), 'Wrong guard failure')
    else:
        raise RuntimeError('Network guard did not block DNS')
    parser = argparse.ArgumentParser()
    parser.add_argument('stage', choices=[*SUITES, 'wheels', 'installed-smoke'])
    parser.add_argument('--wheel-dir', type=Path)
    args = parser.parse_args()
    if args.stage == 'wheels':
        check_wheels(args.wheel_dir)
    elif args.stage == 'installed-smoke':
        installed_smoke()
    else:
        run_suite(args.stage)


if __name__ == '__main__':
    main()
