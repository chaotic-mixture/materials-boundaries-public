"""Test-only exact v0.29.0 predecessor recovery; no production imports.

Only byte-pinned approved changes can be reversed. Current summaries may vary
only with truthful append-only catalogue counts. Old fixtures stay untouched.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
LEDGER_PATH = 'tests/fixtures/material_catalog_updates_v0290.json'
BASELINE_COMMIT = 'd3207a21b341fff92c2c864805bf912cec40ec2e'
BASELINE_TREE = 'c6ba7b33fd5b3672c92a0ee65b8ebf82e3f8544f'
BASELINE_FILE_COUNT = 339
ALLOWED_PATHS = frozenset(['.github/workflows/ci.yml', 'CITATION.cff', 'CONTRIBUTING.md', 'README.md', 'THIRD_PARTY_NOTICES.md', 'materials_boundaries/_version.py', 'materials_boundaries/catalog.py', 'materials_boundaries/catalog_output.py', 'materials_boundaries/cli.py', 'scripts/validate_catalogs.py', 'scripts/check_wheel_metadata.py', 'tests/source_evidence_preservation.py', 'tests/test_source_evidence_correction.py'])


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise AssertionError('Duplicate material preservation key: ' + key)
        result[key] = value
    return result


def load_ledger():
    return json.loads((ROOT / LEDGER_PATH).read_text(encoding='utf-8'), object_pairs_hook=unique_keys)


def valid_digest(value):
    return type(value) is str and len(value) == 64 and all(c in '0123456789abcdef' for c in value)


def validate_ledger(ledger):
    if (type(ledger) is not dict or set(ledger) != {'schema_version', 'release', 'baseline_commit',
            'baseline_tree', 'baseline_sha256', 'approved_existing_updates', 'readme_summaries'}
            or type(ledger['schema_version']) is not int or ledger['schema_version'] != 1
            or ledger['release'] != '0.29.0' or ledger['baseline_commit'] != BASELINE_COMMIT
            or ledger['baseline_tree'] != BASELINE_TREE):
        raise AssertionError('Invalid material preservation metadata')
    baseline = ledger['baseline_sha256']
    if (type(baseline) is not dict or len(baseline) != BASELINE_FILE_COUNT
            or any(type(p) is not str or not p or p.startswith('/') or '\\' in p
                   or any(part in ('', '.', '..') for part in p.split('/')) or not valid_digest(h)
                   for p, h in baseline.items())):
        raise AssertionError('Incomplete material predecessor manifest')
    entries = ledger['approved_existing_updates']
    if type(entries) is not list or not entries:
        raise AssertionError('Missing material integration entries')
    names = []
    for entry in entries:
        if (type(entry) is not dict or set(entry) != {'filename', 'previous_sha256', 'sha256', 'reason', 'edits'}
                or entry['filename'] not in baseline or entry['previous_sha256'] != baseline[entry['filename']]
                or not valid_digest(entry['sha256']) or entry['sha256'] == entry['previous_sha256']
                or type(entry['reason']) is not str or not entry['reason'].strip()):
            raise AssertionError('Invalid material integration entry')
        names.append(entry['filename'])
        _validate_edits(entry['edits'])
    if len(names) != len(set(names)) or set(names) != ALLOWED_PATHS:
        raise AssertionError('Missing, duplicate or unapproved material integration entry')
    summaries = ledger['readme_summaries']
    if type(summaries) is not dict or set(summaries) != {'current-catalog-summary', 'material-catalog-summary', 'baseline-current-catalog-summary'} or any(type(s) is not str for s in summaries.values()):
        raise AssertionError('Invalid material README summary templates')
    return {entry['filename']: entry for entry in entries}


def _validate_edits(edits):
    if type(edits) is not list or not edits:
        raise AssertionError('Missing material exact edits')
    end, previous = 0, -1
    for edit in edits:
        if (type(edit) is not dict or set(edit) != {'offset', 'before', 'after'}
                or type(edit['offset']) is not int or edit['offset'] < end or edit['offset'] <= previous
                or type(edit['before']) is not str or type(edit['after']) is not str
                or edit['before'] == edit['after']):
            raise AssertionError('Invalid material exact edits')
        previous = edit['offset']; end = previous + len(edit['before'].encode('utf-8'))


def apply_exact_edits(raw, edits):
    if type(raw) is not bytes:
        raise AssertionError('Material predecessor must be bytes')
    _validate_edits(edits)
    result, end = bytearray(), 0
    for edit in edits:
        offset, before = edit['offset'], edit['before'].encode('utf-8')
        if offset > len(raw) or raw[offset:offset + len(before)] != before:
            raise AssertionError('Material predecessor edit mismatch')
        result.extend(raw[end:offset]); result.extend(edit['after'].encode('utf-8'))
        end = offset + len(before)
    result.extend(raw[end:])
    return bytes(result)


def reverse_exact_edits(raw, entry):
    if type(raw) is not bytes or digest(raw) != entry['sha256']:
        raise AssertionError('Unreviewed material successor: ' + entry['filename'])
    _validate_edits(entry['edits'])
    delta, reverse = 0, []
    for edit in entry['edits']:
        before, after = edit['before'], edit['after']
        reverse.append({'offset': edit['offset'] + delta, 'before': after, 'after': before})
        delta += len(after.encode('utf-8')) - len(before.encode('utf-8'))
    previous = apply_exact_edits(raw, reverse)
    if digest(previous) != entry['previous_sha256'] or apply_exact_edits(previous, entry['edits']) != raw:
        raise AssertionError('Broken material predecessor reconstruction')
    return previous


def _section(text, name):
    start, end = '<!-- ' + name + ':start -->', '<!-- ' + name + ':end -->'
    if text.count(start) != 1 or text.count(end) != 1:
        raise AssertionError('Missing/duplicate material README marker')
    before, rest = text.split(start)
    summary, after = rest.split(end)
    return before + start, summary, end + after


def _truthful_readme(raw, ledger, *, allow_historical_summary=False):
    text = raw.decode('utf-8')
    def catalog(name):
        return json.loads((ROOT / 'materials_boundaries/data' / (name + '.json')).read_text(encoding='utf-8'))
    claims, sources, observations = (catalog(n)['records'] for n in ('claims', 'sources', 'observations'))
    predictions, temperature = catalog('computational_predictions'), catalog('temperature_models')
    demos = [r for r in temperature['records'] if r['classification'] == 'synthetic_demo']
    synthetic = sum(r['role'] == 'synthetic_demo_provenance' for r in sources)
    from materials_boundaries.material_references import material_coverage
    coverage = material_coverage(catalog('materials'), catalog('reference_properties'))
    counts = {
        'current-catalog-summary': [
            (r'\*\*\d+ mechanics claims\*\*', f'**{len(claims)} mechanics claims**'),
            (r'\*\*\d+ source records\*\*', f'**{len(sources)} source records**'),
            (r'\*\*\d+ observations from \d+ studies\*\*', f'**{len(observations)} observations from {len({r["study_id"] for r in observations})} studies**'),
            (r'\*\*\d+ published computational predictions in \d+ scientific families and \d+ explicit groups\*\*', f'**{len(predictions["records"])} published computational predictions in {len({p["family"] for p in predictions["protocols"]})} scientific families and {len(predictions["comparison_groups"])} explicit groups**'),
            (r'\*\*\d+ synthetic temperature demos with \d+ branches\*\*', f'**{len(demos)} synthetic temperature demos with {sum(len(r["branches"]) for r in demos)} branches**'),
            (r'The \d+ sources comprise \d+ bibliographic/source records plus \d+ original synthetic-demo provenance record', f'The {len(sources)} sources comprise {len(sources)-synthetic} bibliographic/source records plus {synthetic} original synthetic-demo provenance record'),
        ],
        'material-catalog-summary': [
            (r'\*\*\d+ material identities\*\*', f'**{coverage["material_identity_count"]} material identities**'),
            (r'\*\*\d+ qualified grades\*\*', f'**{coverage["grade_count"]} qualified grades**'),
            (r'\*\*\d+ source-scoped states\*\*', f'**{coverage["material_state_count"]} source-scoped states**'),
            (r'\*\*\d+ reference properties\*\*', f'**{coverage["property_record_count"]} reference properties**'),
        ],
    }
    original_summary = _section(text, 'current-catalog-summary')[1]
    for name, pairs in counts.items():
        expected = ledger['readme_summaries'][name]
        for pattern, replacement in pairs:
            expected, n = re.subn(pattern, lambda match: replacement, expected)
            if n != 1:
                raise AssertionError('Invalid material README count template')
        before, actual, after = _section(text, name)
        historical = (allow_historical_summary and name == 'current-catalog-summary'
                      and actual == ledger['readme_summaries']['baseline-current-catalog-summary'])
        if actual != expected and not historical:
            raise AssertionError('Only truthful catalogue count refreshes or the exact historical count-normalizer intermediate are accepted')
        text = before + ledger['readme_summaries'][name] + after
    return text.encode('utf-8'), original_summary


def pre_material_bytes(filename, current, *, ledger=None):
    ledger = load_ledger() if ledger is None else ledger
    entries = validate_ledger(ledger)
    if type(current) is not bytes or filename not in ledger['baseline_sha256']:
        raise AssertionError('Unknown material predecessor file')
    if digest(current) == ledger['baseline_sha256'][filename]:
        return current
    if filename == 'README.md':
        current, _ = _truthful_readme(current, ledger, allow_historical_summary=True)
    if filename not in entries:
        raise AssertionError('Unreviewed unchanged material predecessor: ' + filename)
    return reverse_exact_edits(current, entries[filename])


def pre_material_readme(actual):
    """Recover the exact old README after validating both current count sections."""
    return pre_material_bytes('README.md', actual)
