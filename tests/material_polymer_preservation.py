"""Test-only exact v0.34.0 recovery of the accepted 394-file v0.33.0 tree.

Successor bytes and edits are pinned. Catalog projections permit only independent
appends after every retained complete object has passed its digest check. The
fixed release serialization must then match its byte pin before reversal.
Production readers and replay do not import this module.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
LEDGER_PATH = 'tests/fixtures/material_polymer_updates_v0340.json'
ADMISSION_PATH = 'tests/fixtures/material_polymer_admission_v0340.json'
BASELINE_COMMIT = '8ed6fa18369b43719174fc407f76bc073e265d7c'
BASELINE_TREE = '754ff52504b8f661214a717c35d2155512f3e951'
BASELINE_FILE_COUNT = 394
ALLOWED_PATHS = frozenset(['CITATION.cff', 'README.md', 'THIRD_PARTY_NOTICES.md', 'docs/MATERIAL_REFERENCE_CATALOG.md', 'materials_boundaries/_version.py', 'materials_boundaries/data/materials.json', 'materials_boundaries/data/reference_properties.json', 'materials_boundaries/data/sources.json', 'tests/material_porous_preservation.py', 'tests/test_material_porous_preservation.py', 'scripts/check_wheel_metadata.py', 'tests/test_schema_meta_cache.py', 'tests/material_catalog_preservation.py'])
CATALOG_NAMES = frozenset({
    'claims', 'computational_predictions', 'locales', 'material_locales',
    'materials', 'observations', 'prediction_locales', 'reference_properties',
    'sources', 'temperature_locales', 'temperature_models', 'visualization_locales',
})
EXECUTABLE_IDS = frozenset({
    'voigt_bulk', 'voigt_shear', 'reuss_bulk', 'reuss_shear',
    'hs_bulk_3d_two_phase', 'hs_shear_3d_two_phase',
    'youngs_modulus_outer', 'poissons_ratio_outer',
})


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise AssertionError('Duplicate v0.34 preservation key: ' + key)
        result[key] = value
    return result


def load_ledger():
    return json.loads((ROOT / LEDGER_PATH).read_text(encoding='utf-8'), object_pairs_hook=unique_keys)


def valid_digest(value):
    return type(value) is str and len(value) == 64 and all(c in '0123456789abcdef' for c in value)


def validate_edits(edits):
    if type(edits) is not list or not edits:
        raise AssertionError('Missing v0.34 exact edits')
    end, previous = 0, -1
    for edit in edits:
        if (type(edit) is not dict or set(edit) != {'offset', 'before', 'after'}
                or type(edit['offset']) is not int or edit['offset'] < end or edit['offset'] <= previous
                or type(edit['before']) is not str or type(edit['after']) is not str
                or edit['before'] == edit['after']):
            raise AssertionError('Invalid v0.34 exact edits')
        previous = edit['offset']
        end = previous + len(edit['before'].encode('utf-8'))


def validate_catalog_pins(catalogs):
    expected = {'materials_boundaries/data/' + name + '.json' for name in CATALOG_NAMES}
    if type(catalogs) is not dict or set(catalogs) != expected:
        raise AssertionError('Incomplete v0.34 catalog preservation inventory')
    for filename, fields in catalogs.items():
        if type(fields) is not dict or not fields:
            raise AssertionError('Invalid v0.34 catalog fields')
        for field, entry in fields.items():
            if type(entry) is not dict or not entry:
                raise AssertionError('Invalid v0.34 catalog pin')
            is_claims = filename.endswith('/claims.json') and field == 'records'
            keys = set(entry)
            if is_claims:
                if keys != {'record_digests', 'evidence_digests'}:
                    raise AssertionError('Invalid v0.34 claim pin')
                records, evidence = entry['record_digests'], entry['evidence_digests']
                if (type(records) is not dict or type(evidence) is not dict
                        or not EXECUTABLE_IDS <= set(records)
                        or set(evidence) != set(records) - EXECUTABLE_IDS):
                    raise AssertionError('Invalid v0.34 executable claim inventory')
                for values in evidence.values():
                    if (type(values) is not list or not values or len(set(values)) != len(values)
                            or any(not valid_digest(v) for v in values)):
                        raise AssertionError('Invalid v0.34 claim evidence pins')
                keys = {'record_digests'}
            if len(keys) != 1:
                raise AssertionError('Ambiguous v0.34 catalog pin')
            kind = next(iter(keys)); values = entry[kind]
            if kind == 'sha256':
                if not valid_digest(values):
                    raise AssertionError('Invalid v0.34 metadata pin')
            elif kind in ('record_digests', 'label_digests'):
                if (type(values) is not dict or not values
                        or any(type(k) is not str or not k or not valid_digest(v) for k, v in values.items())):
                    raise AssertionError('Invalid v0.34 object pins')
            elif kind == 'locale_label_digests':
                if (type(values) is not dict or not values
                        or any(type(lang) is not str or type(labels) is not dict or not labels
                               or any(type(k) is not str or not k or not valid_digest(v) for k, v in labels.items())
                               for lang, labels in values.items())):
                    raise AssertionError('Invalid v0.34 locale pins')
            else:
                raise AssertionError('Unknown v0.34 catalog pin kind')


def validate_ledger(ledger):
    if (type(ledger) is not dict or set(ledger) != {
            'schema_version', 'release', 'baseline_commit', 'baseline_tree',
            'baseline_sha256', 'approved_existing_updates', 'readme_summaries', 'catalog_preservation'}
            or type(ledger['schema_version']) is not int or ledger['schema_version'] != 1
            or ledger['release'] != '0.34.0' or ledger['baseline_commit'] != BASELINE_COMMIT
            or ledger['baseline_tree'] != BASELINE_TREE):
        raise AssertionError('Invalid v0.34 preservation metadata')
    baseline = ledger['baseline_sha256']
    if (type(baseline) is not dict or len(baseline) != BASELINE_FILE_COUNT
            or any(type(p) is not str or not p or p.startswith('/') or '\\' in p
                   or any(part in ('', '.', '..') for part in p.split('/')) or not valid_digest(h)
                   for p, h in baseline.items())):
        raise AssertionError('Incomplete v0.33 predecessor manifest')
    entries = ledger['approved_existing_updates']
    if type(entries) is not list or not entries:
        raise AssertionError('Missing v0.34 integration entries')
    names = []
    for entry in entries:
        if (type(entry) is not dict or set(entry) != {'filename', 'previous_sha256', 'sha256', 'reason', 'edits'}
                or entry['filename'] not in baseline or entry['previous_sha256'] != baseline[entry['filename']]
                or not valid_digest(entry['sha256']) or entry['sha256'] == entry['previous_sha256']
                or type(entry['reason']) is not str or not entry['reason'].strip()):
            raise AssertionError('Invalid v0.34 integration entry')
        names.append(entry['filename']); validate_edits(entry['edits'])
    if len(names) != len(set(names)) or set(names) != ALLOWED_PATHS:
        raise AssertionError('Missing, duplicate or unapproved v0.34 integration entry')
    summaries = ledger['readme_summaries']
    if (type(summaries) is not dict or set(summaries) != {
            'current-catalog-summary', 'material-catalog-summary', 'historical-current-catalog-summary'}
            or any(type(value) is not str for value in summaries.values())):
        raise AssertionError('Invalid v0.34 README summary templates')
    validate_catalog_pins(ledger['catalog_preservation'])
    return {entry['filename']: entry for entry in entries}


def apply_exact_edits(raw, edits):
    if type(raw) is not bytes:
        raise AssertionError('v0.33 predecessor must be bytes')
    validate_edits(edits)
    result, end = bytearray(), 0
    for edit in edits:
        offset, before = edit['offset'], edit['before'].encode('utf-8')
        if offset > len(raw) or raw[offset:offset + len(before)] != before:
            raise AssertionError('v0.34 predecessor edit mismatch')
        result.extend(raw[end:offset]); result.extend(edit['after'].encode('utf-8'))
        end = offset + len(before)
    result.extend(raw[end:])
    return bytes(result)


def reverse_exact_edits(raw, entry):
    if type(raw) is not bytes or digest(raw) != entry['sha256']:
        raise AssertionError('Unreviewed v0.34 successor: ' + entry['filename'])
    validate_edits(entry['edits'])
    delta, reverse = 0, []
    for edit in entry['edits']:
        before, after = edit['before'], edit['after']
        reverse.append({'offset': edit['offset'] + delta, 'before': after, 'after': before})
        delta += len(after.encode('utf-8')) - len(before.encode('utf-8'))
    previous = apply_exact_edits(raw, reverse)
    if digest(previous) != entry['previous_sha256'] or apply_exact_edits(previous, entry['edits']) != raw:
        raise AssertionError('Broken v0.34 predecessor reconstruction')
    return previous


def project_catalog(filename, current, catalogs):
    """Check whole fixed objects before selecting a fixed release collection.

    The only retained-object extension is the older suite's non-executable claim
    evidence suffix. Its complete original evidence prefix and all other fields
    remain pinned; executable claims and every material/source object stay whole.
    """
    fields = catalogs.get(filename)
    if not fields or type(current) is not dict or set(current) != set(fields):
        raise AssertionError('Unreviewed v0.34 catalog envelope: ' + filename)
    projected = {}
    for key, pin in fields.items():
        kind = 'record_digests' if 'record_digests' in pin else next(iter(pin))
        values, actual = pin[kind], current[key]
        if kind == 'record_digests':
            if type(actual) is not list or any(type(r) is not dict or type(r.get('id')) is not str for r in actual):
                raise AssertionError('Invalid v0.34 record collection')
            index = {r['id']: r for r in actual}
            if len(index) != len(actual):
                raise AssertionError('Duplicate v0.34 record identity')
            if [record['id'] for record in actual[:len(values)]] != list(values):
                raise AssertionError('Retained v0.34 records must remain an exact ordered prefix')
            selected = []
            for identifier, expected in values.items():
                if identifier not in index:
                    raise AssertionError('Missing retained v0.34 object: ' + identifier)
                record = deepcopy(index[identifier])
                if identifier in pin.get('evidence_digests', {}):
                    fixed = pin['evidence_digests'][identifier]; evidence = record.get('evidence')
                    if type(evidence) is not list or any(type(item) is not dict for item in evidence):
                        raise AssertionError('Invalid v0.34 claim evidence')
                    hashes = [digest(canonical(item)) for item in evidence]
                    if hashes[:len(fixed)] != fixed or len(set(hashes)) != len(hashes):
                        raise AssertionError('Changed v0.34 claim evidence prefix')
                    record['evidence'] = evidence[:len(fixed)]
                if digest(canonical(record)) != expected:
                    raise AssertionError('Changed retained v0.34 object: ' + identifier)
                selected.append(record)
            projected[key] = selected
        elif kind == 'locale_label_digests':
            if type(actual) is not dict:
                raise AssertionError('Invalid v0.34 locale collection')
            projected[key] = {}
            for lang, labels in values.items():
                if lang not in actual or type(actual[lang]) is not dict:
                    raise AssertionError('Missing v0.34 locale: ' + lang)
                projected[key][lang] = {}
                for label, expected in labels.items():
                    if label not in actual[lang] or digest(canonical(actual[lang][label])) != expected:
                        raise AssertionError('Changed v0.34 locale label: ' + lang + '/' + label)
                    projected[key][lang][label] = deepcopy(actual[lang][label])
        elif kind == 'label_digests':
            if type(actual) is not dict:
                raise AssertionError('Invalid v0.34 label collection')
            projected[key] = {}
            for label, expected in values.items():
                if label not in actual or digest(canonical(actual[label])) != expected:
                    raise AssertionError('Changed v0.34 prior label: ' + label)
                projected[key][label] = deepcopy(actual[label])
        else:
            if digest(canonical(actual)) != values:
                raise AssertionError('Changed v0.34 catalog metadata: ' + key)
            projected[key] = deepcopy(actual)
    return projected


def _section(text, name):
    start, end = '<!-- ' + name + ':start -->', '<!-- ' + name + ':end -->'
    if text.count(start) != 1 or text.count(end) != 1:
        raise AssertionError('Missing/duplicate v0.34 README marker')
    before, rest = text.split(start); summary, after = rest.split(end)
    return before + start, summary, end + after


def truthful_readme(raw, ledger, *, allow_historical_summary=False, root=None):
    """Validate live counts, allowing only one exact old normalizer intermediate."""
    text = raw.decode('utf-8')
    root = ROOT if root is None else root
    def catalog(name):
        return json.loads((root / 'materials_boundaries/data' / (name + '.json')).read_text(encoding='utf-8'))
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
    for name, pairs in counts.items():
        expected = ledger['readme_summaries'][name]
        for pattern, replacement in pairs:
            expected, count = re.subn(pattern, lambda match: replacement, expected)
            if count != 1:
                raise AssertionError('Invalid v0.34 README count template')
        before, actual, after = _section(text, name)
        historical = (allow_historical_summary and name == 'current-catalog-summary'
                      and actual == ledger['readme_summaries']['historical-current-catalog-summary'])
        if actual != expected and not historical:
            raise AssertionError('Only truthful current counts or the exact historical count-normalizer intermediate are accepted')
        text = before + ledger['readme_summaries'][name] + after
    return text.encode('utf-8')


def release_bytes(filename, current, *, ledger=None, allow_historical_summary=False, root=None):
    """Return byte-pinned v0.34 bytes, retaining legitimate append rehearsals."""
    ledger = load_ledger() if ledger is None else ledger
    entries = validate_ledger(ledger)
    if type(current) is not bytes or filename not in ledger['baseline_sha256']:
        raise AssertionError('Unknown v0.34 release file')
    expected = entries[filename]['sha256'] if filename in entries else ledger['baseline_sha256'][filename]
    if filename == 'README.md':
        current = truthful_readme(current, ledger, allow_historical_summary=allow_historical_summary, root=root)
    elif filename in ledger['catalog_preservation']:
        try:
            value = json.loads(current.decode('utf-8'), object_pairs_hook=unique_keys)
        except (ValueError, UnicodeError) as exc:
            raise AssertionError('Invalid v0.34 catalog bytes') from exc
        fixed = project_catalog(filename, value, ledger['catalog_preservation'])
        if digest(current) != expected:
            if value == fixed:
                raise AssertionError('Unreviewed catalog formatting without an independent append')
            # A fixed serializer is admitted only if the entire release byte hash
            # matches. No changed retained object or arbitrary field is erased.
            current = (json.dumps(fixed, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')
    if digest(current) != expected:
        raise AssertionError('Unreviewed v0.34 release bytes: ' + filename)
    return current


def pre_material_polymer_bytes(filename, current, *, ledger=None, allow_historical_summary=False, root=None):
    ledger = load_ledger() if ledger is None else ledger
    entries = validate_ledger(ledger)
    if type(current) is not bytes or filename not in ledger['baseline_sha256']:
        raise AssertionError('Unknown v0.33 predecessor file')
    if digest(current) == ledger['baseline_sha256'][filename]:
        return current
    current = release_bytes(filename, current, ledger=ledger,
                            allow_historical_summary=allow_historical_summary, root=root)
    return reverse_exact_edits(current, entries[filename]) if filename in entries else current
