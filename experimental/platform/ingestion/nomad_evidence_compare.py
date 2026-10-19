"""Offline, read-only source-field comparison for two completed NOMAD cycles.

The selected fields aid human review. Hashes bind local content, not reviewer
identity, source authenticity, scientific validity or permission to admit data.
"""
from pathlib import Path
import re

import nomad_incremental as inc

SCHEMA = 'nomad-evidence-compare/1'
MAX_REPORT_BYTES = 2_000_000
MAX_VALUE_BYTES = 2048
MAX_LIST_ITEMS = 100
MAX_ENTRIES = 2000

# Paths are relative to each cached response's data row. Wildcards expand only
# list indices, never arbitrary source keys. Containers receive hash-only views.
ARCHIVE_FIELDS = (
    'archive/metadata/license', 'archive/metadata/external_db',
    'archive/metadata/upload_id', 'archive/metadata/mainfile',
    'archive/metadata/nomad_version', 'archive/metadata/nomad_commit',
    'archive/metadata/last_processing_time', 'archive/metadata/references/*',
    'archive/results/material/material_id',
    'archive/results/material/chemical_formula_hill',
    'archive/results/material/elements/*',
    'archive/results/material/structural_type',
    'archive/results/material/symmetry/space_group_number',
    'archive/results/method/method_name',
    'archive/results/method/simulation/program_name',
    'archive/results/method/simulation/program_version',
    'archive/results/properties/structures/structure_original/mass_density',
    'archive/results/properties/structures/structure_original/mass_density_unit',
    'archive/results/properties/structures/structure_original/unit',
    'archive/results/properties/structures/structure_original/dimension_types/*',
)
ATTRIBUTION_FIELDS = (
    'authors/*/name', 'references/*',
    'datasets/*/dataset_id', 'datasets/*/dataset_name', 'datasets/*/doi',
)
INPUT_EVENTS = frozenset(('new', 'changed', 'reappeared', 'withdrawal_pending_review'))
SENSITIVE_TEXT = re.compile(
    r'(?:^|[^a-z])(?:bearer|token|password|passwd|pwd|secret|credential|authorization|'
    r'api[_ -]?key|access[_ -]?key)(?:$|[^a-z])|'
    r'(?:^|[^a-z0-9])(?:sk[-_]|gh[pousr]_|github_pat_|AKIA|ASIA)|'
    r'-----BEGIN[^\r\n]*KEY-----', re.IGNORECASE)


def _sensitive_text(value):
    """Conservative output guard, not authentication or a universal secret detector."""
    return (any(ord(char) < 32 or ord(char) == 127 for char in value)
            or any(char in value for char in '/\\:@%?#=$')
            or SENSITIVE_TEXT.search(value) is not None
            or any(len(word) > 64 for word in value.split()))


def _public_id(value):
    return isinstance(value, str) and inc.ID.fullmatch(value) and not _sensitive_text(value)


def _view(value, *, scalar=True, pointer=''):
    kind = {type(None): 'null', bool: 'boolean', int: 'integer', float: 'number',
            str: 'string', list: 'array', dict: 'object'}[type(value)]
    encoded = inc.canonical(value)
    result = {'present': True, 'type': kind, 'sha256': inc.digest(value)}
    locator = pointer.endswith('/mainfile') or '/references/' in pointer or pointer.endswith('/doi')
    known_unit = (pointer.rsplit('/', 1)[-1] in ('unit', 'mass_density_unit')
                  and value in ('kg/m^3', 'g/cm^3')) if isinstance(value, str) else False
    sensitive = kind == 'string' and _sensitive_text(value) and not known_unit
    if locator or sensitive:
        result['value_omitted'] = 'sensitive_locator_or_text'
    elif scalar and kind not in ('array', 'object') and len(encoded) <= MAX_VALUE_BYTES:
        result['value'] = value
    else:
        result['value_omitted'] = ('size_limit' if len(encoded) > MAX_VALUE_BYTES
                                   else 'container_or_unselected_shape')
    return result


def _fields(row, paths):
    result = {}

    def visit(value, tokens, pointer):
        if not tokens:
            result[pointer] = _view(value, pointer=pointer)
        elif tokens[0] == '*':
            result[pointer] = _view(value, scalar=False, pointer=pointer)
            if isinstance(value, list) and len(value) <= MAX_LIST_ITEMS:
                for index, item in enumerate(value):
                    visit(item, tokens[1:], pointer + '/' + str(index))
        elif isinstance(value, dict):
            token = tokens[0]
            if token in value:
                visit(value[token], tokens[1:], pointer + '/' + token)
        else:
            # Preserve an invalid/missing container distinction without dumping
            # an unexpected subtree as if it were a reviewed scalar field.
            result[pointer] = _view(value, scalar=False, pointer=pointer)

    if row is not None:
        for path in paths:
            visit(row, path.split('/'), '')
    return result


def _snapshot(db, cycle_id):
    row = db.execute('SELECT state FROM cycles WHERE id=?', (cycle_id,)).fetchone()
    if row is None:
        raise ValueError('Requested comparison cycle does not exist')
    cycle = inc.decode(row['state'])
    report = cycle.get('report')
    if (cycle.get('id') != cycle_id or cycle.get('status') != 'complete'
            or not isinstance(report, dict) or report.get('cycle_id') != cycle_id
            or report.get('schema') != inc.SCHEMA or report.get('status') != 'complete'
            or report.get('complete') is not True or report.get('baseline_committed') is not True):
        raise ValueError('Comparison requires two saved complete cycles')
    if (report.get('profile_sha256') != inc.meta(db, 'profile_sha256')
            or report.get('review_boundary_sha256') != inc.meta(db, 'review_boundary')['sha256']
            or report.get('formal_project_total') != inc.meta(db, 'review_boundary')['formal_project_total']
            or report.get('admitted_delta') != 0
            or report.get('excluded_example_count') != inc.meta(db, 'review_boundary')['excluded_example_count']):
        raise ValueError('Saved comparison report scope binding mismatch')
    attempts = db.execute('SELECT id,request_key,record FROM attempts WHERE cycle=? ORDER BY id',
                          (cycle_id,)).fetchall()
    acquisition = [dict(inc.decode(item['record']), attempt_id=item['id']) for item in attempts]
    if inc.canonical(report.get('acquisition')) != inc.canonical(acquisition):
        raise ValueError('Saved comparison acquisition binding mismatch')
    evidence = []
    seen = set()
    for batch in cycle['batches']:
        archive = inc.evidence(db, cycle_id, batch['archive'])
        if archive is None or (archive[0]['data'] and not batch.get('attribution')):
            raise ValueError('Comparison cycle lacks required archive or attribution evidence')
        for key, endpoint in (('archive', inc.ARCHIVE), ('attribution', inc.ATTRIBUTION)):
            request_key = batch.get(key)
            if request_key is None and key == 'attribution':
                continue
            matches = [item for item in attempts if item['request_key'] == request_key
                       and inc.decode(item['record'])['status'] == 'ok']
            if len(matches) != 1:
                raise ValueError('Comparison cycle evidence reference is missing or ambiguous')
            item = matches[0]
            record = inc.decode(item['record'])
            if record['endpoint'] != endpoint:
                raise ValueError('Comparison cycle evidence endpoint mismatch')
            if item['id'] in seen:
                raise ValueError('Duplicate comparison cycle evidence reference')
            seen.add(item['id'])
            evidence.append({'attempt_id': item['id'], 'endpoint': endpoint,
                             'request_sha256': record['request_sha256'],
                             'response_sha256': record['sha256'], 'bytes': record['bytes']})
    successful = {item['id'] for item in attempts if inc.decode(item['record'])['status'] == 'ok'}
    if seen != successful:
        raise ValueError('Comparison cycle does not account for all successful evidence')
    _, _, _, _, archives, attributions = inc.observed_rows(db, cycle)
    if (sorted(cycle['seen']) != sorted(archives)
            or set(cycle['absent']) & set(archives)):
        raise ValueError('Comparison cycle observation membership mismatch')
    gates = {}
    for gate in report['gate_exclusions']:
        if (not _public_id(gate['provider_entry_id']) or not isinstance(gate['reason'], str)
                or len(gate['reason']) > 256
                or _sensitive_text(gate['reason'].removeprefix('missing_field:'))):
            raise ValueError('Unsafe recorded gate label in comparison report')
        gates.setdefault(gate['provider_entry_id'], []).append(gate)
    for event in report['input_changes']:
        if not _public_id(event['provider_entry_id']) or event['change'] not in INPUT_EVENTS:
            raise ValueError('Invalid recorded input event in comparison report')
    candidates = {}
    for candidate in report['candidate_packet']['candidates']:
        mid = candidate['provider_material_id']
        if not _public_id(mid):
            raise ValueError('Invalid provider group in saved comparison report')
        if mid in candidates:
            raise ValueError('Duplicate provider group in saved comparison report')
        candidates[mid] = inc.digest({key: value for key, value in candidate.items() if key != 'evidence'})
    binding = {'id': cycle_id, 'state_sha256': inc.digest(cycle),
               'report_sha256': inc.digest(report), 'evidence': sorted(evidence, key=lambda x: x['attempt_id'])}
    return {'binding': binding, 'archives': archives, 'attributions': attributions,
            'gates': gates, 'candidates': candidates, 'report': report}


def _entry(snapshot, eid):
    archives = snapshot['archives'].get(eid, {})
    attributions = snapshot['attributions'].get(eid, {})
    gates = sorted(snapshot['gates'].get(eid, []), key=inc.canonical)
    return {'present': bool(archives), 'archive_sha256': sorted(archives),
            'attribution_sha256': sorted(attributions),
            'gate_reasons': sorted({gate['reason'] for gate in gates}),
            'gate_sha256': inc.digest(gates)}


def _compare(db, before, after):
    inc.integrity(db)
    boundary_label = inc.meta(db, 'review_boundary').get('sha256')
    if not isinstance(boundary_label, str) or len(boundary_label) > 128 or _sensitive_text(boundary_label):
        raise ValueError('Invalid review-boundary label in comparison store')
    left, right = _snapshot(db, before), _snapshot(db, after)
    entry_ids = sorted(set(left['archives']) | set(right['archives']))
    if len(entry_ids) > MAX_ENTRIES:
        raise ValueError('Comparison entry limit exceeded; no partial report produced')
    changes, ambiguous = [], []
    for eid in entry_ids:
        if not _public_id(eid):
            raise ValueError('Invalid provider entry ID in comparison evidence')
        old, new = _entry(left, eid), _entry(right, eid)
        uncertain = any(len(snapshot[kind].get(eid, {})) > 1
                        for snapshot in (left, right) for kind in ('archives', 'attributions'))
        if uncertain:
            ambiguous.append(eid)
        if old == new:
            continue
        source_changed = any(old[key] != new[key] for key in ('archive_sha256', 'attribution_sha256'))
        fields = []
        if not uncertain:
            for source, kind, paths in (('archive', 'archives', ARCHIVE_FIELDS),
                                        ('attribution', 'attributions', ATTRIBUTION_FIELDS)):
                previous = next(iter(left[kind].get(eid, {}).values()), None)
                current = next(iter(right[kind].get(eid, {}).values()), None)
                a, b = _fields(previous, paths), _fields(current, paths)
                for pointer in sorted(set(a) | set(b)):
                    old_value, new_value = a.get(pointer, {'present': False}), b.get(pointer, {'present': False})
                    if old_value != new_value:
                        fields.append({'source': source, 'pointer': pointer, 'before': old_value, 'after': new_value})
        changes.append({'provider_entry_id': eid,
                        'change': ('observed_only_after' if not old['present'] else
                                   'observed_only_before' if not new['present'] else 'changed'),
                        'before': old, 'after': new, 'fields': fields,
                        'source_comparison': 'ambiguous_variants' if uncertain else 'unique',
                        # Deliberately conservative: selected fields are never a
                        # proof that every changed source byte has been explained.
                        'unexpanded_source_change': source_changed,
                        'recorded_after_input_events': [item['change'] for item in right['report']['input_changes']
                                                       if item['provider_entry_id'] == eid]})
    candidate_changes = []
    for mid in sorted(set(left['candidates']) | set(right['candidates'])):
        old, new = left['candidates'].get(mid), right['candidates'].get(mid)
        if old != new:
            candidate_changes.append({'provider_material_id': mid, 'old_sha256': old, 'new_sha256': new,
                                      'change': ('added_to_candidate_queue' if old is None else
                                                 'removed_from_candidate_queue' if new is None else 'changed')})
    result = {'schema': SCHEMA, 'before_cycle': left['binding'], 'after_cycle': right['binding'],
              'profile_sha256': inc.meta(db, 'profile_sha256'),
              'review_boundary_sha256': inc.meta(db, 'review_boundary')['sha256'],
              'review_boundary_content_sha256': inc.meta(db, 'boundary_sha256'),
              'formal_project_total': inc.meta(db, 'review_boundary')['formal_project_total'],
              'excluded_example_count': inc.meta(db, 'review_boundary')['excluded_example_count'], 'admitted_delta': 0,
              'release_authorized': False, 'observed_entry_union': len(entry_ids),
              'entry_changes': changes, 'candidate_changes': candidate_changes,
              'ambiguous_entries': ambiguous,
              'limits': {'max_entries': MAX_ENTRIES, 'max_report_bytes': MAX_REPORT_BYTES,
                         'max_scalar_bytes': MAX_VALUE_BYTES, 'max_expanded_list_items': MAX_LIST_ITEMS},
              'scope': [
                  'Offline comparison of cached bounded observations, not current provider state.',
                  'Pointers are relative to the archive or attribution response data row.',
                  'Selected fields only; unknown fields and large values retain hashes without raw content.',
                  'Mainfile/reference/DOI locators and recognized path or credential-like strings are hash-only.',
                  'The conservative text guard is not a universal secret detector; use public metadata stores only.',
                  'Unexpanded source change conservatively remains true for any changed source fingerprint.',
                  'Gate reasons and candidate membership come from saved reports; no eligibility or approval is reissued.',
                  'Input events belong to the later cycle and its then-baseline, not necessarily the selected earlier cycle.',
                  'Absent observations and queue removal do not prove deletion or revoke formal admission.',
                  'Local hashes do not authenticate sources, reviewers, scientific claims or reuse rights.',
              ]}
    result['comparison_sha256'] = inc.digest(result)
    if len(inc.canonical(result)) + 1 > MAX_REPORT_BYTES:
        raise ValueError('Comparison output limit exceeded; no partial report produced')
    return result


def compare(root, *, before, after):
    """Compare ordered complete cycles in one existing read-only transaction."""
    if type(before) is not int or type(after) is not int or not 0 < before < after:
        raise ValueError('Comparison requires positive cycle IDs with before < after')
    try:
        root = Path(root).resolve()
        path = root / inc.DB_NAME
        if not path.is_file():
            raise ValueError('Store is not initialized')
        # SQLite mode=ro can create WAL/SHM coordination files. The collector's
        # default rollback-journal format needs none; refuse externally changed
        # WAL stores before opening SQLite rather than ignoring their WAL data.
        with path.open('rb') as stream:
            header = stream.read(20)
        if header.startswith(b'SQLite format 3\x00') and 2 in header[18:20]:
            raise ValueError('Comparison requires a rollback-journal store; WAL mode is unsupported')
        with inc.connect(root, readonly=True) as db:
            return _compare(db, before, after)
    except (KeyError, TypeError, IndexError, AttributeError) as exc:
        raise ValueError('Malformed saved comparison evidence or report') from exc
    except inc.sqlite3.Error as exc:
        raise ValueError('Cannot read comparison store') from exc
    except OSError as exc:
        raise ValueError('Cannot inspect comparison store') from exc
