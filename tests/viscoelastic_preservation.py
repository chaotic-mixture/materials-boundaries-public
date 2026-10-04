"""Bounded v0.26 compatibility: recover exact accepted bytes, never skip hashes.

The new independent preservation test pins this adapter and its ledger. Existing
historical fixtures and the provenance helper remain untouched. These hashes
identify repository payloads, not publisher artifacts or scientific review.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER_PATH = 'tests/fixtures/viscoelastic_updates_v0260.json'
BASELINE_COMMIT = '09ca1725feea6111fbdae7c666bb4f9b5857b3a2'
BASELINE_TREE = '88aac5c40ed73efa6ab8fe6255f911f5649dc93d'
ALLOWED_PATHS = frozenset({
    'README.md', 'CONTRIBUTING.md', 'CITATION.cff', 'THIRD_PARTY_NOTICES.md', 'docs/SOURCES.md',
    'materials_boundaries/_version.py', 'materials_boundaries/catalog.py',
    'materials_boundaries/catalog_output.py', 'schemas/claims.schema.json',
    'schemas/comparison.schema.json', 'scripts/validate_catalogs.py',
    'scripts/check_wheel_metadata.py',
    'tests/test_anisotropy_catalog.py', 'tests/test_bulk_wave_catalog.py',
    'tests/test_catalog_search.py', 'tests/test_directional_compressibility_catalog.py',
    'tests/test_directional_poisson_catalog.py', 'tests/test_fatigue_catalog.py',
    'tests/test_mechanical.py', 'tests/test_mechanics_catalog_expansion.py',
    'tests/test_observation_catalog.py', 'tests/test_fracture_catalog.py',
    'tests/test_catalog_translation_snapshot.py', 'tests/test_helper_lineage.py',
    'tests/test_nickel_prediction_batch.py', 'tests/test_pa12_preservation.py',
    'tests/test_paht_test_lineage.py', 'tests/test_silicon_predictions.py',
    'tests/test_study_comparison_preservation.py',
    'tests/test_temperature_plot_preservation.py',
})


def digest(value):
    return hashlib.sha256(value).hexdigest()


def unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise AssertionError('Duplicate v0.26 preservation key: ' + key)
        result[key] = value
    return result


def load_ledger():
    return json.loads((ROOT / LEDGER_PATH).read_text(encoding='utf-8'), object_pairs_hook=unique_keys)


def validate_ledger(ledger):
    expected_keys = {'schema_version', 'release', 'scope', 'review', 'baseline_sha256',
                     'approved_existing_updates', 'catalog_preservation', 'release_readme_summary'}
    if (not isinstance(ledger, dict) or set(ledger) != expected_keys
            or ledger['schema_version'] != 1 or ledger['release'] != '0.26.0'
            or ledger['scope'] != 'scalar_viscoelastic_catalog_only_exact_compatibility'
            or ledger['review'] != {'kind': 'current_release_compatibility_review',
                'review_date': '2026-10-03', 'baseline_commit': BASELINE_COMMIT,
                'baseline_tree': BASELINE_TREE, 'baseline_file_count': 295,
                'historical_review_claimed': False}):
        raise AssertionError('Unexpected v0.26 preservation metadata')
    baseline = ledger['baseline_sha256']
    if not isinstance(baseline, dict) or len(baseline) != 295:
        raise AssertionError('Incomplete v0.26 baseline')
    entries = ledger['approved_existing_updates']
    if (not isinstance(entries, list) or not entries
            or any(not isinstance(e, dict) for e in entries)):
        raise AssertionError('Invalid v0.26 exact-edit ledger')
    names = [e.get('filename') for e in entries]
    if (len(set(names)) != len(names) or not set(names) <= ALLOWED_PATHS
            or not set(names) <= set(baseline)):
        raise AssertionError('Duplicate or unapproved v0.26 file')
    for entry in entries:
        if (set(entry) != {'filename', 'previous_sha256', 'sha256', 'reason', 'edits'}
                or entry['previous_sha256'] != baseline[entry['filename']]
                or not isinstance(entry['reason'], str) or not entry['reason'].strip()
                or not isinstance(entry['sha256'], str) or len(entry['sha256']) != 64
                or any(c not in '0123456789abcdef' for c in entry['sha256'])
                or not isinstance(entry['edits'], list) or not entry['edits']):
            raise AssertionError('Invalid v0.26 successor entry')
    return {entry['filename']: entry for entry in entries}


def apply_exact_edits(source, edits):
    """Offsets are UTF-8 byte offsets in the complete predecessor."""
    if not isinstance(source, bytes) or not isinstance(edits, list):
        raise AssertionError('Expected bytes and exact edits')
    result, end = bytearray(), 0
    for edit in edits:
        if (not isinstance(edit, dict) or set(edit) != {'offset', 'before', 'after'}
                or not isinstance(edit['before'], str) or not isinstance(edit['after'], str)):
            raise AssertionError('Invalid v0.26 exact-edit fields')
        offset, before, after = edit['offset'], edit['before'].encode(), edit['after'].encode()
        if (type(offset) is not int or offset < end or offset > len(source)
                or source[offset:offset + len(before)] != before or before == after):
            raise AssertionError('Invalid or overlapping v0.26 exact edit')
        result.extend(source[end:offset]); result.extend(after)
        end = offset + len(before)
    result.extend(source[end:])
    return bytes(result)


def reverse_exact_edits(current, entry):
    if digest(current) != entry['sha256']:
        raise AssertionError('Unreviewed v0.26 current bytes: ' + entry['filename'])
    delta, reverse = 0, []
    for edit in entry['edits']:
        # Validate the complete edit contract before calculating its reverse.
        if (not isinstance(edit, dict) or set(edit) != {'offset', 'before', 'after'}
                or type(edit['offset']) is not int or edit['offset'] < 0
                or not isinstance(edit['before'], str) or not isinstance(edit['after'], str)):
            raise AssertionError('Invalid v0.26 reverse edit')
        before, after = edit['before'], edit['after']
        reverse.append({'offset': edit['offset'] + delta, 'before': after, 'after': before})
        delta += len(after.encode()) - len(before.encode())
    predecessor = apply_exact_edits(current, reverse)
    if (digest(predecessor) != entry['previous_sha256']
            or apply_exact_edits(predecessor, entry['edits']) != current):
        raise AssertionError('Broken v0.26 predecessor reconstruction: ' + entry['filename'])
    return predecessor


def pre_viscoelastic_bytes(filename, current, *, ledger=None):
    """Verify exact current bytes, then recover only a recorded predecessor."""
    ledger = load_ledger() if ledger is None else ledger
    entries = validate_ledger(ledger)
    if filename in entries:
        return reverse_exact_edits(current, entries[filename])
    if filename not in ledger['baseline_sha256'] or digest(current) != ledger['baseline_sha256'][filename]:
        raise AssertionError('Unreviewed unchanged v0.26 baseline file: ' + str(filename))
    return current


def historical_claims_envelope(catalog):
    """Align only the independently tested new envelope for old snapshot hashes."""
    if catalog.get('schema_version') != '1.12.0':
        raise AssertionError('Expected the current claims schema before historical comparison')
    result = deepcopy(catalog)
    result['schema_version'] = '1.11.0'
    return result
