"""Exact, test-only v0.28.2 evidence predecessor reconstruction.

Current production catalogs and strict report replay never import this module.
A dated source ledger separately binds nine source-fact edits and three claim
identity patches. No fields are stripped, no old fixtures are refreshed, and
uncorrected or arbitrary successor values fail closed.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from material_catalog_preservation import pre_material_bytes

ROOT = Path(__file__).resolve().parents[1]
LEDGER_PATH = 'tests/fixtures/source_evidence_updates_v0282.json'
EVIDENCE_PATH = 'tests/fixtures/source_evidence_correction_v0282.json'
BASELINE_COMMIT = '3affa5c5f2520435623a79b1761a436ef96b13bc'
BASELINE_TREE = '2058d6acfc154fda844fab2c8a489924c4eb1e57'
BASELINE_FILE_COUNT = 334
EVIDENCE_SHA256 = 'c9690460dea724565a8a2b936f438c8adfe929e7242d8b91ad2850f1d35fec1a'
ALLOWED_PATHS = frozenset({
    '.github/workflows/ci.yml',
    'CITATION.cff',
    'README.md',
    'docs/COMPOSITE_WORKFLOW.md',
    'docs/MODEL.md',
    'docs/SOURCES.md',
    'materials_boundaries/_composite_labels.py',
    'materials_boundaries/_version.py',
    'materials_boundaries/data/claims.json',
    'materials_boundaries/data/locales.json',
    'materials_boundaries/data/sources.json',
    'tests/catalog_fixtures.py',
    'tests/composite_preservation.py',
    'tests/provenance_corrections.py',
    'tests/test_bulk_wave_catalog.py',
    'tests/test_catalog_translation_snapshot.py',
    'tests/test_composite_acceptance.py',
    'tests/test_composite_preservation.py',
    'tests/test_crystal_stability_catalog.py',
    'tests/test_fatigue_catalog.py',
    'tests/test_hbn_observation_catalog.py',
    'tests/test_helper_lineage.py',
    'tests/test_historical_provenance.py',
    'tests/test_mechanical.py',
    'tests/test_pa12_cf15_observations.py',
    'tests/test_pa12_preservation.py',
    'tests/test_paht_preservation.py',
    'tests/test_paht_test_lineage.py',
    'tests/test_porous_catalog.py',
    'tests/test_stability_catalog.py',
    'tests/test_study_comparison_preservation.py',
    'tests/test_temperature.py',
    'tests/test_temperature_plot_preservation.py',
    'tests/test_viscoelastic_preservation.py',
    'tests/test_windows_export_preservation.py',
    'tests/test_yield_preservation.py',
    'tests/windows_export_preservation.py',
})  # Filled from the reviewed, exact integration inventory.


def digest(value):
    return hashlib.sha256(value).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise AssertionError('Duplicate v0.28.2 evidence key: ' + key)
        result[key] = value
    return result


def load_evidence():
    raw = (ROOT / EVIDENCE_PATH).read_bytes()
    if digest(raw) != EVIDENCE_SHA256:
        raise AssertionError('Unreviewed source-evidence correction ledger')
    return json.loads(raw.decode('utf-8'), object_pairs_hook=unique_keys)


def _change_value(record, change, *, forward=False, fragment=False):
    path = change['path']
    expected = change['before'] if forward else change['after']
    replacement = change['after'] if forward else change['before']
    if fragment and path[0] not in record:
        return
    if path[0] == 'evidence':
        source_id = ('kochmann_milton_2014' if change['record_id'] == 'reuss_shear'
                     else 'meille_garboczi_2001')
        candidates = [item for item in record['evidence']
                      if item.get('source_id') == source_id and item.get('locator') == expected]
        if len(candidates) != 1:
            raise AssertionError('Missing, duplicate or unreviewed corrected equation locator: ' + change['record_id'])
        # Another historical/corrected locator with this role is not appendability.
        if any(item.get('source_id') == source_id and item.get('locator') == replacement
               for item in record['evidence']):
            raise AssertionError('Conflicting equation correction predecessor: ' + change['record_id'])
        candidates[0]['locator'] = deepcopy(replacement)
        return
    if path[0] == 'claim_notes':
        notes = record['claim_notes']
        if notes.count(expected) != 1 or replacement in notes:
            raise AssertionError('Missing, duplicate or unreviewed corrected source note: ' + change['record_id'])
        notes[notes.index(expected)] = deepcopy(replacement)
        return
    if path == ['verification', 'gaps']:
        gaps = record['verification']['gaps']
        if not isinstance(gaps, list) or any(gaps.count(item) != 1 for item in expected):
            raise AssertionError('Missing or duplicate retained source-evidence gap: ' + change['record_id'])
        removed = [item for item in expected if item not in replacement]
        added = [item for item in replacement if item not in expected]
        if any(item in gaps for item in added):
            raise AssertionError('Uncorrected or duplicate source-evidence gap: ' + change['record_id'])
        for item in removed:
            gaps.remove(item)
        for item in added:
            gaps.insert(min(replacement.index(item), len(gaps)), deepcopy(item))
        return
    parent = record
    for key in path[:-1]:
        parent = parent[key]
    key = path[-1]
    if parent[key] != expected:
        raise AssertionError('Unreviewed corrected source value: ' + change['record_id'] + ':' + str(path))
    parent[key] = deepcopy(replacement)


def previous_record(kind, record):
    """Validate exact successors and restore only explicitly recorded fields."""
    result = deepcopy(record)
    ledger = load_evidence()
    changes = ledger['metadata_changes'] + ledger['claim_version_changes']
    for change in reversed(changes):
        if change['catalog'] == kind and change['record_id'] == record.get('id'):
            _change_value(result, change)
    return result


def previous_catalog(kind, catalog):
    result = deepcopy(catalog)
    if kind in ('claims', 'sources'):
        result['records'] = [previous_record(kind, record) for record in result['records']]
    return result


def current_provenance(kind, identifier, historical_fragment):
    """Keep old fixture bytes; derive only their exact current expectation."""
    result = deepcopy(historical_fragment)
    ledger = load_evidence()
    for change in ledger['metadata_changes'] + ledger['claim_version_changes']:
        if change['catalog'] == kind and change['record_id'] == identifier:
            _change_value(result, change, forward=True, fragment=True)
    return result


def valid_digest(value):
    return (isinstance(value, str) and len(value) == 64
            and all(char in '0123456789abcdef' for char in value))


def load_ledger():
    return json.loads((ROOT / LEDGER_PATH).read_text(encoding='utf-8'), object_pairs_hook=unique_keys)


def validate_edits(edits):
    if not isinstance(edits, list) or not edits:
        raise AssertionError('Expected nonempty v0.28.2 exact edits')
    end, previous_offset = 0, -1
    for edit in edits:
        if (not isinstance(edit, dict) or set(edit) != {'offset', 'before', 'after'}
                or type(edit['offset']) is not int
                or not isinstance(edit['before'], str) or not isinstance(edit['after'], str)
                or edit['before'] == edit['after']
                or edit['offset'] < end or edit['offset'] <= previous_offset):
            raise AssertionError('Invalid or overlapping v0.28.2 exact edit')
        previous_offset = edit['offset']
        end = previous_offset + len(edit['before'].encode('utf-8'))


def validate_ledger(ledger):
    if (not isinstance(ledger, dict)
            or set(ledger) != {'schema_version', 'release', 'scope', 'review',
                               'baseline_sha256', 'approved_existing_updates'}
            or type(ledger['schema_version']) is not int or ledger['schema_version'] != 1
            or ledger['release'] != '0.28.2'
            or ledger['scope'] != 'source_evidence_exact_compatibility'
            or ledger['review'] != {
                'kind': 'current_source_evidence_compatibility_review',
                'review_date': '2026-10-04', 'baseline_commit': BASELINE_COMMIT,
                'baseline_tree': BASELINE_TREE, 'baseline_file_count': BASELINE_FILE_COUNT,
                'historical_review_claimed': False,
            }):
        raise AssertionError('Unexpected v0.28.2 preservation metadata')
    baseline = ledger['baseline_sha256']
    if (not isinstance(baseline, dict) or len(baseline) != BASELINE_FILE_COUNT
            or any(not isinstance(path, str) or not path or path.startswith('/')
                   or '\\' in path or any(part in ('', '.', '..') for part in path.split('/'))
                   or not valid_digest(value) for path, value in baseline.items())):
        raise AssertionError('Incomplete v0.28.2 exact public baseline')
    entries = ledger['approved_existing_updates']
    if not isinstance(entries, list) or any(not isinstance(entry, dict) for entry in entries):
        raise AssertionError('Invalid v0.28.2 integration ledger')
    names = [entry.get('filename') for entry in entries]
    if (any(not isinstance(name, str) for name in names)
            or len(names) != len(set(names)) or set(names) != ALLOWED_PATHS
            or not set(names) <= set(baseline)):
        raise AssertionError('Missing, duplicate or unapproved v0.28.2 file')
    for entry in entries:
        if (set(entry) != {'filename', 'previous_sha256', 'sha256', 'reason', 'edits'}
                or entry['previous_sha256'] != baseline[entry['filename']]
                or not valid_digest(entry['sha256']) or entry['sha256'] == entry['previous_sha256']
                or not isinstance(entry['reason'], str) or not entry['reason'].strip()):
            raise AssertionError('Invalid v0.28.2 successor entry')
        validate_edits(entry['edits'])
    return {entry['filename']: entry for entry in entries}


def apply_exact_edits(source, edits):
    if not isinstance(source, bytes):
        raise AssertionError('Expected v0.28.2 source bytes')
    validate_edits(edits)
    result, end = bytearray(), 0
    for edit in edits:
        offset = edit['offset']
        before, after = edit['before'].encode('utf-8'), edit['after'].encode('utf-8')
        if offset > len(source) or source[offset:offset + len(before)] != before:
            raise AssertionError('Unreviewed v0.28.2 exact-edit source')
        result.extend(source[end:offset]); result.extend(after)
        end = offset + len(before)
    result.extend(source[end:])
    return bytes(result)


def reverse_exact_edits(current, entry):
    if not isinstance(current, bytes) or digest(current) != entry['sha256']:
        raise AssertionError('Unreviewed v0.28.2 current bytes: ' + entry['filename'])
    validate_edits(entry['edits'])
    delta, reverse = 0, []
    for edit in entry['edits']:
        before, after = edit['before'], edit['after']
        reverse.append({'offset': edit['offset'] + delta, 'before': after, 'after': before})
        delta += len(after.encode('utf-8')) - len(before.encode('utf-8'))
    predecessor = apply_exact_edits(current, reverse)
    if (digest(predecessor) != entry['previous_sha256']
            or apply_exact_edits(predecessor, entry['edits']) != current):
        raise AssertionError('Broken v0.28.2 predecessor reconstruction: ' + entry['filename'])
    return predecessor


def pre_evidence_bytes(filename, current, *, ledger=None):
    """Recover v0.28.1 bytes only from the reviewed v0.28.2 successor."""
    ledger = load_ledger() if ledger is None else ledger
    entries = validate_ledger(ledger)
    accepted = entries[filename]['sha256'] if filename in entries else ledger['baseline_sha256'].get(filename)
    if digest(current) != accepted:
        current = pre_material_bytes(filename, current)
    if filename in entries:
        return reverse_exact_edits(current, entries[filename])
    if (not isinstance(current, bytes) or filename not in ledger['baseline_sha256']
            or digest(current) != ledger['baseline_sha256'][filename]):
        raise AssertionError('Unreviewed unchanged v0.28.2 baseline file: ' + str(filename))
    return current
