"""Exact, fail-closed reversal of reviewed metadata changes for old fixtures.

This test-only adapter never changes production data, drops arbitrary fields, or
accepts a prior uncorrected value. It first proves the exact corrected value and
then restores only its recorded predecessor for historical hash comparison.
"""
import copy
import hashlib
import json
from pathlib import Path
from source_evidence_preservation import previous_record

LEDGER = json.loads((Path(__file__).parent / 'fixtures/nist_reuse_correction_v0132.json').read_text(encoding='utf-8'))
DIRECTIONAL_TEST_UPDATES = json.loads((Path(__file__).parent / 'fixtures/directional_test_updates_v0150.json').read_text(encoding='utf-8'))

COMPRESSIBILITY_TEST_UPDATES = json.loads((Path(__file__).parent / 'fixtures/compressibility_test_updates_v0160.json').read_text(encoding='utf-8'))

OBSERVATION_TEST_UPDATES = json.loads((Path(__file__).parent / 'fixtures/observation_test_updates_v0170.json').read_text(encoding='utf-8'))

WAVE_TEST_UPDATES = json.loads((Path(__file__).parent / 'fixtures/wave_test_updates_v0180.json').read_text(encoding='utf-8'))

HBN_TEST_UPDATES = json.loads((Path(__file__).parent / 'fixtures/hbn_test_updates_v0190.json').read_text(encoding='utf-8'))

PA12_TEST_UPDATES = json.loads((Path(__file__).parent / 'fixtures/pa12_test_updates_v0220.json').read_text(encoding='utf-8'))

PUBLIC_BASELINE = json.loads((Path(__file__).parent / 'fixtures/public_baseline_adjustments.json').read_text(encoding='utf-8'))



def _unique_lineage_keys(pairs):
    """New maintenance evidence must not silently collapse duplicate JSON keys."""
    result = {}
    for key, value in pairs:
        if key in result:
            raise AssertionError('Duplicate helper-lineage key: ' + key)
        result[key] = value
    return result


def _load_lineage_fixture(name):
    return json.loads((Path(__file__).parent / 'fixtures' / name).read_text(encoding='utf-8'),
                      object_pairs_hook=_unique_lineage_keys)


HELPER_BOOTSTRAP_BRIDGE = _load_lineage_fixture('helper_bootstrap_bridge_20261003.json')
CURRENT_HELPER_UPDATES = _load_lineage_fixture('helper_maintenance_updates_20261003.json')
PAHT_TEST_UPDATES = _load_lineage_fixture('paht_test_updates_v0240.json')


def _reviewed_bootstrap_hash(filename, expected):
    # This acyclic pin binds all source bytes, endpoint/commit/blob evidence,
    # exact edits, allowed filename and current (never historical) review claim.
    evidence = json.dumps(HELPER_BOOTSTRAP_BRIDGE, ensure_ascii=False, sort_keys=True,
                          separators=(',', ':'), allow_nan=False).encode('utf-8')
    if hashlib.sha256(evidence).hexdigest() != 'f3684e8c8f6ddfbc2fd9bef88bc2918af3a0460eeee6f85cbde9de00b98325ae':
        raise AssertionError('Unexpected current-reviewed public helper bridge')
    change, = HELPER_BOOTSTRAP_BRIDGE['approved_test_updates']
    if filename == change['filename']:
        if expected != change['previous_sha256'] or not change['reason'].strip():
            raise AssertionError('Broken reconstructed public helper provenance: ' + filename)
        return change['sha256']
    return expected


def reviewed_current_test_hash(filename, expected):
    """Apply only this maintenance tail to an exact accepted direct baseline.

    This is deliberately separate from the full historical traversal below.
    Successor bytes are pinned independently by test_helper_lineage.py; embedding
    this file's own successor hash here would create a self-reference cycle.
    """
    ledger = CURRENT_HELPER_UPDATES
    if (set(ledger) != {'schema_version', 'scope', 'review', 'approved_test_updates'}
            or ledger['schema_version'] != 1
            or ledger['scope'] != 'test_helper_self_lineage_only'
            or ledger['review'] != {
                'kind': 'current_maintenance_review', 'review_date': '2026-10-03',
                'baseline_commit': '6b351cc15126f50563eb18740103760f00b9282a',
                'baseline_tree': 'a50b4c986f9d10d61f5aef4cfa0e4a3ad32a12dd',
                'historical_review_claimed': False}):
        raise AssertionError('Unexpected helper maintenance review provenance')
    predecessors = {
        'tests/provenance_corrections.py': '5afbaae797599ac9321ea9a59c925f4877d35799dd283338cd70a3facb0f022c',
        'tests/test_temperature_plot_preservation.py': '25d3449d640fba780d0a7020f50a952ae0f0672c4ace0b809fc7172e53e7115a',
    }
    entries = ledger['approved_test_updates']
    if (not isinstance(entries, list) or len(entries) != len(predecessors)
            or any(not isinstance(e, dict) for e in entries)
            or {e.get('filename') for e in entries} != set(predecessors)):
        raise AssertionError('Unexpected helper maintenance file override')
    for change in entries:
        if (set(change) != {'filename', 'previous_sha256', 'sha256', 'reason'}
                or change['previous_sha256'] != predecessors[change['filename']]
                or not isinstance(change['reason'], str) or not change['reason'].strip()
                or not isinstance(change['sha256'], str) or len(change['sha256']) != 64
                or any(c not in '0123456789abcdef' for c in change['sha256'])):
            raise AssertionError('Broken helper maintenance entry: ' + change['filename'])
    for change in entries:
        if filename == change['filename']:
            if expected != change['previous_sha256']:
                raise AssertionError('Broken current helper maintenance provenance: ' + filename)
            return change['sha256']
    return expected


def reviewed_paht_test_hash(filename, expected):
    """Append only the reviewed v0.24 tail to its exact accepted predecessor.

    The independent PAHT lineage test pins this ledger and its actual successor
    bytes. Keeping that pin outside this helper avoids a self-reference cycle.
    All earlier ledgers, fixture bytes and normalization guards remain intact.
    """
    ledger = PAHT_TEST_UPDATES
    if (set(ledger) != {'schema_version', 'release', 'scope', 'review',
                       'approved_test_updates', 'unchanged_fixture_sha256'}
            or ledger['schema_version'] != 1 or ledger['release'] != '0.24.0'
            or ledger['scope'] != 'paht_source_filter_and_test_lineage_only'
            or ledger['review'] != {
                'kind': 'current_paht_compatibility_review', 'review_date': '2026-10-03',
                'baseline_commit': '828ca90a4a32f4744f0e18ea704965cc0ec7f56e',
                'baseline_tree': '200dbdbf7aab4832aa3293aeec1c8e83ac18a9e9',
                'baseline_file_count': 258, 'historical_review_claimed': False}):
        raise AssertionError('Unexpected PAHT test review provenance')
    predecessors = {
        'tests/provenance_corrections.py': 'e5bf06ae239c9ea8f7db6d767aa6c35a00f88b85a07830858cbc499a9f4de5fe',
        'tests/test_helper_lineage.py': 'b2af5a64ef777d1aa59e2ff763f7f1b07f7bebc69f541f344921c7f28e9d6ac4',
        'tests/test_temperature_plot_preservation.py': '906da60f3065d901d6d618cdc439bb639beb422e5074e9f026b1a48cf557bc1a',
        'tests/test_pa12_cf15_inspection.py': '7688ab79ec0ab39b00e28f406040363a1238b14c430f2ddd47fc5cdcc1f9f83a',
        'tests/test_pa12_cf15_observations.py': '874539ebb135346d2eeecdc2bbb3cc52a95d9b308e0a91e7a8ebe73a22bf0e4f',
    }
    entries = ledger['approved_test_updates']
    if (not isinstance(entries, list) or len(entries) != len(predecessors)
            or any(not isinstance(e, dict) for e in entries)
            or {e.get('filename') for e in entries} != set(predecessors)):
        raise AssertionError('Unexpected PAHT historical file override')
    for change in entries:
        if (set(change) != {'filename', 'previous_sha256', 'sha256', 'reason', 'edits'}
                or change['previous_sha256'] != predecessors[change['filename']]
                or not isinstance(change['reason'], str) or not change['reason'].strip()
                or not isinstance(change['sha256'], str) or len(change['sha256']) != 64
                or any(c not in '0123456789abcdef' for c in change['sha256'])
                or not isinstance(change['edits'], list) or not change['edits']):
            raise AssertionError('Broken PAHT test entry: ' + change['filename'])
        for edit in change['edits']:
            if (not isinstance(edit, dict) or set(edit) != {'offset', 'before', 'after'}
                    or type(edit['offset']) is not int or edit['offset'] < 0
                    or not isinstance(edit['before'], str) or not isinstance(edit['after'], str)
                    or edit['before'] == edit['after']):
                raise AssertionError('Broken PAHT exact edit: ' + change['filename'])
    for change in entries:
        if filename == change['filename']:
            if expected != change['previous_sha256']:
                raise AssertionError('Broken PAHT test-update provenance: ' + filename)
            return change['sha256']
    return expected


def public_previous_record(kind, record):
    """Undo exact current evidence, then older bibliography corrections."""
    result = previous_record(kind, record)
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
    expected = _reviewed_bootstrap_hash(filename, expected)
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
    updates = WAVE_TEST_UPDATES['approved_test_updates']
    allowed = {'tests/test_catalog_search.py', 'tests/test_directional_poisson_catalog.py', 'tests/test_anisotropy_catalog.py', 'tests/provenance_corrections.py', 'tests/test_mechanical.py', 'tests/test_directional_compressibility_catalog.py', 'tests/test_mechanics_catalog_expansion.py', 'tests/test_observation_catalog.py', 'tests/test_fatigue_catalog.py', 'tests/test_fracture_catalog.py'}
    if set(updates) != allowed:
        raise AssertionError('Unexpected wave-release historical test override')
    change = updates.get(filename)
    if change is not None:
        if change['previous_sha256'] != expected or not change['reason'].strip():
            raise AssertionError('Broken wave test-update provenance: ' + filename)
        expected = change['sha256']
    updates = HBN_TEST_UPDATES['approved_test_updates']
    allowed = {'tests/test_observation_catalog.py', 'tests/test_mos2_observation_catalog.py', 'tests/provenance_corrections.py'}
    if set(updates) != allowed:
        raise AssertionError('Unexpected hBN-release historical test override')
    change = updates.get(filename)
    if change is not None:
        if change['previous_sha256'] != expected or not change['reason'].strip():
            raise AssertionError('Broken hBN test-update provenance: ' + filename)
        expected = change['sha256']
    updates = PA12_TEST_UPDATES['approved_test_updates']
    allowed = {'tests/test_catalog_translation_snapshot.py', 'tests/test_hbn_observation_catalog.py',
               'tests/test_mos2_observation_catalog.py', 'tests/test_observation_catalog.py',
               'tests/test_observation_inspection.py', 'tests/provenance_corrections.py'}
    if set(updates) != allowed:
        raise AssertionError('Unexpected PA12-release historical test override')
    change = updates.get(filename)
    if change is not None:
        if change['previous_sha256'] != expected or not change['reason'].strip():
            raise AssertionError('Broken PA12 test-update provenance: ' + filename)
        expected = change['sha256']
    expected = reviewed_current_test_hash(filename, expected)
    return reviewed_paht_test_hash(filename, expected)
