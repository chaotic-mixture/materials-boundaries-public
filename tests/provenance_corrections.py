"""Exact, fail-closed reversal of reviewed metadata changes for old fixtures.

This test-only adapter never changes production data, drops arbitrary fields, or
accepts a prior uncorrected value. It first proves the exact corrected value and
then restores only its recorded predecessor for historical hash comparison.
"""
import copy
import json
from pathlib import Path

LEDGER = json.loads((Path(__file__).parent / 'fixtures/nist_reuse_correction_v0132.json').read_text(encoding='utf-8'))
DIRECTIONAL_TEST_UPDATES = json.loads((Path(__file__).parent / 'fixtures/directional_test_updates_v0150.json').read_text(encoding='utf-8'))

COMPRESSIBILITY_TEST_UPDATES = json.loads((Path(__file__).parent / 'fixtures/compressibility_test_updates_v0160.json').read_text(encoding='utf-8'))

OBSERVATION_TEST_UPDATES = json.loads((Path(__file__).parent / 'fixtures/observation_test_updates_v0170.json').read_text(encoding='utf-8'))

PUBLIC_BASELINE = json.loads((Path(__file__).parent / 'fixtures/public_baseline_adjustments.json').read_text(encoding='utf-8'))


def public_previous_record(kind, record):
    """Undo only exact bibliography-scope corrections for private-baseline parity."""
    result = copy.deepcopy(record)
    if kind == 'sources':
        for change in reversed(PUBLIC_BASELINE['source_corrections'].get(record['id'], [])):
            parent = result
            for key in change['path'][:-1]:
                parent = parent[key]
            key = change['path'][-1]
            # Curation notes may be reordered during contribution rehearsals.
            if isinstance(parent, list):
                if parent.count(change['after']) != 1:
                    raise AssertionError('Unexpected public source correction: ' + record['id'])
                parent[parent.index(change['after'])] = copy.deepcopy(change['before'])
            else:
                if parent[key] != change['after']:
                    raise AssertionError('Unexpected public source correction: ' + record['id'])
                parent[key] = copy.deepcopy(change['before'])
    return result


def historical_record(kind, record):
    result = public_previous_record(kind, record)
    for change in reversed(LEDGER['records'].get(kind, {}).get(record['id'], [])):
        parent = result
        for key in change['path'][:-1]:
            parent = parent[key]
        key = change['path'][-1]
        operation = change['operation']
        if operation == 'replace':
            if parent[key] != change['after']:
                raise AssertionError('Unexpected corrected metadata: ' + record['id'] + ':' + '.'.join(change['path']))
            parent[key] = copy.deepcopy(change['before'])
        elif operation == 'append':
            if parent[key].count(change['value']) != 1:
                raise AssertionError('Missing or duplicate correction evidence: ' + record['id'])
            parent[key].remove(change['value'])
        elif operation == 'replace_item':
            if parent[key].count(change['after']) != 1 or change['before'] in parent[key]:
                raise AssertionError('Unexpected corrected metadata item: ' + record['id'])
            parent[key][parent[key].index(change['after'])] = change['before']
        else:
            raise AssertionError('Unknown correction operation: ' + operation)
    return result


def historical_temperature_result(result):
    result = copy.deepcopy(result)
    result['model_snapshot'] = historical_record('temperature_models', result['model_snapshot'])
    result['source_snapshots'] = [historical_record('sources', source) for source in result['source_snapshots']]
    return result


def historical_locales(kind, catalog):
    result = copy.deepcopy(catalog)
    if kind == 'temperature_locales':
        for lang, changes in LEDGER['locales'].items():
            for key, change in changes.items():
                if result['languages'][lang][key] != change['after']:
                    raise AssertionError('Unexpected corrected notice: ' + lang + ':' + key)
                result['languages'][lang][key] = change['before']
    return result


def reviewed_test_hash(filename, expected):
    if set(LEDGER['approved_test_updates']) != {'tests/test_predictions.py', 'tests/test_anisotropy_catalog.py'}:
        raise AssertionError('Only the two reviewed historical guard tests may have hash overrides')
    change = LEDGER['approved_test_updates'].get(filename)
    if change is not None:
        if change['previous_sha256'] != expected or not change['reason'].strip():
            raise AssertionError('Broken test-update provenance: ' + filename)
        expected = change['sha256']
    updates = DIRECTIONAL_TEST_UPDATES['approved_test_updates']
    allowed = {'tests/test_anisotropy_catalog.py', 'tests/test_catalog_search.py',
               'tests/test_fatigue_catalog.py', 'tests/test_mechanical.py',
               'tests/test_mechanics_catalog_expansion.py', 'tests/test_observation_catalog.py',
               'tests/test_catalog_cli.py', 'tests/test_fracture_catalog.py'}
    if set(updates) != allowed:
        raise AssertionError('Unexpected directional-release historical test override')
    change = updates.get(filename)
    if change is not None:
        if change['previous_sha256'] != expected or not change['reason'].strip():
            raise AssertionError('Broken directional test-update provenance: ' + filename)
        expected = change['sha256']
    updates = COMPRESSIBILITY_TEST_UPDATES['approved_test_updates']
    allowed = {'tests/test_anisotropy_catalog.py', 'tests/test_catalog_search.py',
               'tests/test_directional_poisson_catalog.py', 'tests/test_fatigue_catalog.py',
               'tests/test_mechanical.py', 'tests/test_mechanics_catalog_expansion.py',
               'tests/test_observation_catalog.py', 'tests/test_fracture_catalog.py',
               'tests/provenance_corrections.py'}
    if set(updates) != allowed:
        raise AssertionError('Unexpected compressibility-release historical test override')
    change = updates.get(filename)
    if change is not None:
        if change['previous_sha256'] != expected or not change['reason'].strip():
            raise AssertionError('Broken compressibility test-update provenance: ' + filename)
        expected = change['sha256']
    change = PUBLIC_BASELINE['approved_test_updates'].get(filename)
    if change is not None:
        if change['previous_sha256'] != expected or not change['reason'].strip():
            raise AssertionError('Broken first-public test-update provenance: ' + filename)
        expected = change['sha256']
    updates = OBSERVATION_TEST_UPDATES['approved_test_updates']
    allowed = {'tests/test_observation_catalog.py', 'tests/test_temperature.py',
               'tests/provenance_corrections.py'}
    if set(updates) != allowed:
        raise AssertionError('Unexpected observation-release historical test override')
    change = updates.get(filename)
    if change is not None:
        if change['previous_sha256'] != expected or not change['reason'].strip():
            raise AssertionError('Broken observation test-update provenance: ' + filename)
        expected = change['sha256']
    return expected
