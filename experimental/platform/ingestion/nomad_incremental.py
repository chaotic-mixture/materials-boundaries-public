"""Bounded, resumable public NOMAD review-queue updates (standard library only).

Each SQLite commit is durable before the next network request. A completed cycle
alone advances the observation baseline; neither observations nor candidates are
formal admission. Evidence is the exact response to a geometry-free projection.

Test transport: callable(endpoint, body, byte_limit) -> (status, headers, bytes).
Test clock: callable returning Unix seconds. after_cache(kind, key) is an optional
crash-injection hook after response commit, before state-machine advancement.
"""
import argparse
from collections import Counter, defaultdict
from contextlib import contextmanager
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import hashlib
import json
import math
from pathlib import Path
import sqlite3
import time
import urllib.error
import urllib.request

from nomad_batch import API, ID, PROJECTION, assert_no_geometry, canonical, digest, normalize

SCHEMA = 'nomad-incremental/1'
ARCHIVE = 'entries/archive/query'
ATTRIBUTION = 'entries/query'
DB_NAME = 'incremental.sqlite3'


def utc(seconds):
    return datetime.fromtimestamp(seconds, timezone.utc).isoformat()


def decode(raw):
    def reject_constant(value):
        raise ValueError('Non-finite JSON number is refused')
    def finite_float(value):
        number = float(value)
        if not math.isfinite(number):
            raise ValueError('Non-finite JSON number is refused')
        return number
    def unique_keys(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('Duplicate JSON object key is refused')
            result[key] = value
        return result
    return json.loads(raw, parse_constant=reject_constant, parse_float=finite_float,
                      object_pairs_hook=unique_keys)


class Stopped(Exception):
    """An expected bounded stop; the next invocation may resume."""


@contextmanager
def locked(root):
    """Nonblocking OS lock; the OS releases it after process death."""
    path = Path(root) / '.update.lock'
    with path.open('a+b') as handle:
        handle.seek(0, 2)
        if handle.tell() == 0:
            handle.write(b'0')
            handle.flush()
        handle.seek(0)
        if __import__('os').name == 'nt':
            import msvcrt
            try:
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError as exc:
                raise ValueError('Store is already being updated') from exc
            try:
                yield
            finally:
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            try:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as exc:
                raise ValueError('Store is already being updated') from exc
            try:
                yield
            finally:
                fcntl.flock(handle, fcntl.LOCK_UN)


@contextmanager
def connect(root, readonly=False):
    path = Path(root) / DB_NAME
    if not path.is_file():
        raise ValueError('Store is not initialized')
    db = sqlite3.connect(path.as_uri() + '?mode=ro', uri=True) if readonly else sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    try:
        if readonly:
            # Keep integrity, cycle state, evidence and baseline in one snapshot.
            db.execute('BEGIN')
        yield db
    finally:
        db.close()


def meta(db, key):
    row = db.execute('SELECT value FROM metadata WHERE key=?', (key,)).fetchone()
    return json.loads(row['value']) if row else None


def set_meta(db, key, value):
    db.execute('INSERT OR REPLACE INTO metadata VALUES (?,?)', (key, canonical(value).decode()))


def save_cycle(db, cycle):
    db.execute('UPDATE cycles SET state=? WHERE id=?', (canonical(cycle).decode(), cycle['id']))


def latest(db):
    row = db.execute('SELECT state FROM cycles ORDER BY id DESC LIMIT 1').fetchone()
    return json.loads(row['state']) if row else None


def validate_profile(profile):
    for key, low, high in [('pages', 1, 10), ('page_size', 1, 100), ('max_requests', 1, 32),
                           ('max_bytes', 1, 30_000_000), ('max_response', 1, 3_000_000), ('retries', 0, 3)]:
        if type(profile[key]) is not int or not low <= profile[key] <= high:
            raise ValueError(f'{key} must be {low}..{high}')
    if profile['max_response'] > profile['max_bytes']:
        raise ValueError('max_response exceeds max_bytes')
    for eid in profile['entry_ids'] + ([profile['after']] if profile['after'] else []):
        if not isinstance(eid, str) or not ID.fullmatch(eid):
            raise ValueError('Invalid entry ID or cursor')
    if len(profile['entry_ids']) > profile['page_size']:
        raise ValueError('An exact entry cohort must fit one page')
    if profile['entry_ids'] and (profile['after'] or profile['pages'] != 1):
        raise ValueError('An exact entry cohort uses one page without an after cursor')


def init_store(root, *, pages=1, page_size=2, entry_ids=(), after=None,
               max_requests=8, max_bytes=2_000_000, max_response=500_000,
               retries=1, boundary=None):
    """Create an immutable collection profile; this function does no network IO."""
    profile = dict(pages=pages, page_size=page_size, entry_ids=sorted(set(entry_ids)),
                   after=after, max_requests=max_requests, max_bytes=max_bytes,
                   max_response=max_response, retries=retries, projection=PROJECTION)
    validate_profile(profile)
    if boundary is None:
        from nomad_review_boundary import load_review_boundary
        boundary = load_review_boundary()
    if boundary.get('formal_project_total') != 1081 or boundary.get('excluded_example_count') != 62:
        raise ValueError('Unexpected formal review boundary; review configuration first')
    root = Path(root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    with locked(root):
        if (root / DB_NAME).exists():
            raise ValueError('Store already initialized; profile cannot be overwritten')
        db = sqlite3.connect(root / DB_NAME)
        try:
            with db:
                db.executescript('''
                    CREATE TABLE metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL);
                    CREATE TABLE cycles(id INTEGER PRIMARY KEY, state TEXT NOT NULL);
                    CREATE TABLE attempts(id INTEGER PRIMARY KEY, cycle INTEGER NOT NULL,
                        request_key TEXT NOT NULL, record TEXT NOT NULL, raw BLOB);
                    CREATE INDEX request_lookup ON attempts(cycle,request_key);
                ''')
                for key, value in [('schema', SCHEMA), ('profile', profile),
                                   ('profile_sha256', digest(profile)), ('review_boundary', boundary),
                                   ('boundary_sha256', digest(boundary)), ('not_before', 0), ('last_dispatch', 0),
                                   ('baseline', {'entries': {}, 'candidates': {}})]:
                    set_meta(db, key, value)
        finally:
            db.close()
    return status(root)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def public_transport(endpoint, body, limit):
    """Fixed official endpoints, no credentials, no redirects, bounded bytes/time."""
    if endpoint not in (ARCHIVE, ATTRIBUTION) or body.get('owner') != 'public':
        raise ValueError('Only public official NOMAD queries are allowed')
    request = urllib.request.Request(API + endpoint, data=canonical(body), headers={
        'Content-Type': 'application/json', 'Accept-Encoding': 'identity',
        'User-Agent': 'MaterialsBoundaries-incremental-review/1.0'})
    # An empty proxy map avoids forwarding this public read through a credentialed
    # environment proxy. No cookies, netrc, auth handler or alternate URL is used.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    try:
        response = opener.open(request, timeout=30)
    except urllib.error.HTTPError as exc:
        response = exc
    with response:
        headers = {k.lower(): v for k, v in response.headers.items()}
        if headers.get('content-encoding', 'identity').lower() != 'identity':
            return response.status, headers, b''
        return response.status, headers, response.read(limit + 1)


def retry_time(headers, now):
    value = headers.get('retry-after', '')
    positive_numeric = isinstance(value, str) and value.strip().removeprefix('+').isdecimal()
    try:
        seconds = int(value)
    except OverflowError:
        raise ValueError('Retry-After seconds exceed supported UTC range') from None
    except (ValueError, TypeError):
        # Python may refuse a numeric string before conversion because of its
        # digit limit. Never shorten that positive wait to the malformed fallback.
        if positive_numeric:
            raise ValueError('Retry-After seconds exceed supported UTC range') from None
        try:
            return max(now + 1, parsedate_to_datetime(value).timestamp())
        except (ValueError, TypeError, OverflowError):
            return now + 60
    try:
        until = now + max(1, seconds)
        utc(until)  # Check platform timestamp limits before recording a cooldown.
    except (ValueError, OverflowError, OSError):
        raise ValueError('Retry-After seconds exceed supported UTC range') from None
    return until


def integrity(db):
    profile = meta(db, 'profile')
    if meta(db, 'schema') != SCHEMA or digest(profile) != meta(db, 'profile_sha256'):
        raise ValueError('Store profile hash mismatch')
    if profile['projection'] != PROJECTION or digest(meta(db, 'review_boundary')) != meta(db, 'boundary_sha256'):
        raise ValueError('Projection or review-boundary hash mismatch')
    for row in db.execute('SELECT record,raw FROM attempts WHERE raw IS NOT NULL'):
        record = json.loads(row['record'])
        raw = bytes(row['raw'])
        if len(raw) != record['bytes'] or hashlib.sha256(raw).hexdigest() != record['sha256']:
            raise ValueError('Evidence hash mismatch')
        if record['endpoint'] not in (ARCHIVE, ATTRIBUTION) or record['url'] != API + record['endpoint']:
            raise ValueError('Evidence source endpoint mismatch')
        if record['request_sha256'] != digest(record['request']) or record['request'].get('owner') != 'public':
            raise ValueError('Evidence request hash mismatch')
        if record['endpoint'] == ARCHIVE and record['request'].get('required') != PROJECTION:
            raise ValueError('Evidence projection mismatch')
        assert_no_geometry(decode(raw))


def evidence(db, cycle_id, key):
    rows = db.execute('SELECT id,record,raw FROM attempts WHERE cycle=? AND request_key=? ORDER BY id',
                      (cycle_id, key)).fetchall()
    for row in rows:
        record = json.loads(row['record'])
        if record['status'] == 'ok':
            return decode(row['raw']), record
    return None


def fetch(db, cycle, endpoint, body, key, transport, clock, after_cache):
    cached = evidence(db, cycle['id'], key)
    if cached:
        return cached
    profile = meta(db, 'profile')
    now = clock()
    if now < meta(db, 'not_before'):
        cycle['status'] = 'cooldown'
        raise Stopped('Provider Retry-After cooldown is still active')
    if transport is public_transport:
        delay = 1 - (now - (meta(db, 'last_dispatch') or 0))
        if delay > 0:
            time.sleep(min(delay, 1))
            now = clock()
    previous = db.execute('SELECT COUNT(*) FROM attempts WHERE cycle=? AND request_key=?',
                          (cycle['id'], key)).fetchone()[0]
    if previous >= 1 + profile['retries']:
        cycle['status'] = 'exhausted'
        raise Stopped('Persistent retry budget exhausted for this request')
    if cycle['requests'] >= profile['max_requests'] or cycle['bytes_charged'] >= profile['max_bytes']:
        cycle['status'] = 'exhausted'
        raise Stopped('Persistent cycle request or byte budget exhausted')
    limit = min(profile['max_response'], profile['max_bytes'] - cycle['bytes_charged'])
    # Reserve the complete permitted response before dispatch. If the process dies
    # in flight, its request and byte reservation remain charged on restart.
    record = {'endpoint': endpoint, 'url': API + endpoint, 'request': body,
              'request_sha256': digest(body), 'retrieved_utc': utc(now),
              'status': 'reserved', 'bytes': limit, 'response_limit': limit}
    cycle['requests'] += 1
    cycle['bytes_charged'] += limit
    if previous:
        cycle['retries_used'] += 1
    with db:
        cursor = db.execute('INSERT INTO attempts(cycle,request_key,record) VALUES (?,?,?)',
                            (cycle['id'], key, canonical(record).decode()))
        attempt_id = cursor.lastrowid
        set_meta(db, 'last_dispatch', now)
        save_cycle(db, cycle)
    raw_to_keep = None
    try:
        code, headers, raw = transport(endpoint, body, limit)
        if not isinstance(raw, bytes):
            raise ValueError('Transport must return bytes')
        headers = {k.lower(): v for k, v in headers.items()}
        record['http_status'] = code
        record['bytes'] = len(raw)
        cycle['bytes_charged'] += len(raw) - limit
        if len(raw) > limit:
            raise ValueError('Response byte limit exceeded')
        if headers.get('content-encoding', 'identity').lower() != 'identity':
            raise ValueError('Compressed responses are refused')
        if code in (429, 503):
            until = retry_time(headers, clock())
            record['retry_after_utc'] = utc(until)
            with db:
                set_meta(db, 'not_before', max(meta(db, 'not_before'), until))
            cycle['status'] = 'cooldown'
            raise Stopped(f'HTTP {code}; Retry-After persisted')
        if code != 200:
            raise ValueError(f'HTTP {code}; redirects and non-success responses are refused')
        value = decode(raw)
        assert_no_geometry(value)
        record.update(status='ok', sha256=hashlib.sha256(raw).hexdigest())
        raw_to_keep = raw
    except (OSError, TimeoutError) as exc:
        cycle['status'] = 'paused'
        record.update(status='error', error=type(exc).__name__)
    except Stopped as exc:
        record.update(status='error', error=str(exc))
    except (ValueError, TypeError) as exc:
        cycle['status'] = 'blocked'
        record.update(status='rejected', error=str(exc))
    finally:
        with db:
            db.execute('UPDATE attempts SET record=?,raw=? WHERE id=?',
                       (canonical(record).decode(), raw_to_keep, attempt_id))
            save_cycle(db, cycle)
    if record['status'] != 'ok':
        raise Stopped(record['error'])
    if after_cache:
        after_cache(endpoint, key)
    return value, record


def page_rows(value, body, *, exhaustive=False):
    """Validate pagination before accepting evidence or inferring an omission."""
    if not isinstance(value, dict) or not isinstance(value.get('data'), list):
        raise ValueError('Malformed response data')
    pagination = value.get('pagination')
    if not isinstance(pagination, dict) or type(pagination.get('total')) is not int or pagination['total'] < 0:
        raise ValueError('Missing or malformed pagination total')
    rows = value['data']
    ids = [row.get('entry_id') if isinstance(row, dict) else None for row in rows]
    if any(not isinstance(eid, str) or not ID.fullmatch(eid) for eid in ids):
        raise ValueError('Missing or malformed response entry ID')
    size = body['pagination']['page_size']
    if len(rows) > size or pagination['total'] < len(set(ids)):
        raise ValueError('Response exceeds requested page or total')
    requested = body['query'].get('entry_id', {}).get('any')
    if requested is not None and not set(ids) <= set(requested):
        raise ValueError('Exact-ID response contains an unrequested entry')
    cursor = body['pagination'].get('page_after_value')
    next_cursor = pagination.get('next_page_after_value')
    if ids != sorted(ids) or (cursor and any(eid <= cursor for eid in ids)):
        raise ValueError('Response order or continuation cursor is inconsistent')
    if next_cursor is not None and (not isinstance(next_cursor, str) or not ID.fullmatch(next_cursor)
                                   or not ids or next_cursor != ids[-1]
                                   or (cursor and next_cursor <= cursor)):
        raise ValueError('Malformed or nonadvancing pagination cursor')
    if exhaustive and (next_cursor is not None or pagination['total'] != len(set(ids))):
        raise ValueError('Exact-ID response is incomplete; cannot infer absence')
    if not exhaustive and cursor is None and next_cursor is None and pagination['total'] > len(set(ids)):
        raise ValueError('First page is truncated without a continuation cursor')
    if not rows and next_cursor is not None:
        raise ValueError('Empty page with continuation cursor')
    return rows, next_cursor


def archive_body(profile, cursor=None, exact_ids=None):
    pagination = {'page_size': profile['page_size'], 'order_by': 'entry_id', 'order': 'asc'}
    if cursor:
        pagination['page_after_value'] = cursor
    query = {'entry_id': {'any': exact_ids}} if exact_ids is not None else {
        'external_db': 'OQMD', 'results.material.structural_type': 'bulk'}
    return {'owner': 'public', 'query': query, 'pagination': pagination, 'required': PROJECTION}


def author_body(profile, ids):
    return {'owner': 'public', 'query': {'entry_id': {'any': ids}},
            'pagination': {'page_size': profile['page_size'], 'order_by': 'entry_id', 'order': 'asc'},
            'required': {'include': ['entry_id', 'authors.*', 'references', 'datasets.*']}}


def observed_rows(db, cycle):
    rows, authors, bindings, diagnostics = [], {}, {}, []
    row_variants, author_variants = defaultdict(dict), defaultdict(dict)
    for batch in cycle['batches']:
        archive, record = evidence(db, cycle['id'], batch['archive'])
        for row in archive['data']:
            eid = row['entry_id']
            row_variants[eid][digest(row)] = row
            bindings[eid] = {'sqlite_attempt': batch['archive'], 'sha256': record['sha256'],
                             'retrieved_utc': record['retrieved_utc'], 'request_sha256': record['request_sha256']}
        if batch['attribution']:
            attribution, source = evidence(db, cycle['id'], batch['attribution'])
            for row in attribution['data']:
                eid = row['entry_id']
                author_variants[eid][digest(row)] = row
    for eid, variants in sorted(row_variants.items()):
        author_set = author_variants[eid]
        if len(variants) != 1 or len(author_set) > 1:
            diagnostics.append({'provider_entry_id': eid, 'reason': 'conflicting_duplicate_entry',
                                'variant_hashes': sorted(variants), 'attribution_variant_hashes': sorted(author_set)})
            continue
        row = next(iter(variants.values()))
        rows.append(row)
        authors[eid] = next(iter(author_set.values())) if author_set else {}
    counts = Counter(row['entry_id'] for batch in cycle['batches']
                     for row in evidence(db, cycle['id'], batch['archive'])[0]['data'])
    diagnostics.extend({'provider_entry_id': eid, 'reason': 'identical_duplicate_coalesced', 'rows': count}
                       for eid, count in sorted(counts.items()) if count > 1 and len(row_variants[eid]) == 1)
    return rows, authors, bindings, diagnostics, row_variants, author_variants


def assemble_report(db, cycle, commit=False):
    profile, boundary = meta(db, 'profile'), meta(db, 'review_boundary')
    baseline = meta(db, 'baseline')
    rows, authors, bindings, diagnostics, variants, author_variants = observed_rows(db, cycle)
    known_entries = set(boundary.get('provider_entry_ids', []))
    observed_boundary_labels = dict(baseline.get('boundary_material_aliases', {}))
    known_materials = set(boundary['provider_material_ids']) | set(observed_boundary_labels)
    # A known calculation may be remapped upstream to a new provider group.
    # Hold that entire observed group, including its other calculations, rather
    # than allowing a second entry to reintroduce it as a new candidate.
    for eid in known_entries & set(variants):
        for row in variants[eid].values():
            try:
                mid = row['archive']['results']['material']['material_id']
            except (KeyError, TypeError):
                continue
            if isinstance(mid, str) and ID.fullmatch(mid):
                known_materials.add(mid)
                observed_boundary_labels[mid] = sorted(set(observed_boundary_labels.get(mid, []))
                    | set(boundary.get('entries', {}).get(eid, [])))
    boundary_gates = [{'provider_entry_id': row['entry_id'], 'reason': 'known_review_boundary_entry_overlap',
                       'review_boundary_labels': boundary.get('entries', {}).get(row['entry_id'], [])}
                      for row in rows if row['entry_id'] in known_entries]
    packet = normalize([row for row in rows if row['entry_id'] not in known_entries], authors, bindings,
                       existing_ids=known_materials)
    packet['baseline_commit'] = boundary.get('baseline_commit', '4c5656cf6ba0ad1a54b736e0568e97abe4815c29')
    material_by_entry = {}
    for row in rows:
        try:
            material_by_entry[row['entry_id']] = row['archive']['results']['material']['material_id']
        except (KeyError, TypeError):
            pass
    for exclusion in packet['exclusions']:
        if exclusion['reason'] == 'already_in_reviewed_computed_seed':
            exclusion['reason'] = 'known_review_boundary_material_overlap'
            mid = material_by_entry[exclusion['provider_entry_id']]
            exclusion['provider_material_id'] = mid
            exclusion['review_boundary_labels'] = sorted(set(boundary.get('materials', {}).get(mid, []))
                                                        | set(observed_boundary_labels.get(mid, [])))
    packet['exclusions'].extend(boundary_gates)
    packet['exclusions'].extend(d for d in diagnostics if d['reason'] == 'conflicting_duplicate_entry')
    packet['counts']['acquired_entry_rows'] = len(variants)
    packet['counts']['acquired_entry_rows_basis'] = 'Distinct observed entry IDs after identical-row coalescing; includes held entries'
    packet['counts']['excluded_entry_rows'] = len(packet['exclusions'])
    packet['counts']['exclusion_reasons'] = dict(sorted(Counter(x['reason'] for x in packet['exclusions']).items()))
    for candidate in packet['candidates']:
        labels = boundary.get('compositions', {}).get(candidate['reduced_formula'], [])
        if labels:
            candidate['composition_overlap_advisory'] = {'review_boundary_labels': labels,
                                                         'meaning': 'Formula overlap is not material identity or admission'}
    gates = packet['exclusions']
    entries, input_changes = dict(baseline['entries']), []
    for eid in sorted(variants):
        fingerprint = digest({'archive_variants': sorted(variants[eid]), 'attribution_variants': sorted(author_variants[eid])})
        old = entries.get(eid)
        current = {'sha256': fingerprint, 'state': 'publicly_returned'}
        event = 'new' if not old else ('reappeared' if old['state'] != 'publicly_returned'
                                     else ('changed' if old['sha256'] != fingerprint else None))
        if event:
            input_changes.append({'provider_entry_id': eid, 'change': event,
                                  'old_sha256': old['sha256'] if old else None, 'new_sha256': fingerprint})
        entries[eid] = current
    for eid in cycle['absent']:
        old = entries.get(eid)
        if old and old['state'] == 'publicly_returned':
            entries[eid] = dict(old, state='withdrawal_pending_review')
            input_changes.append({'provider_entry_id': eid, 'change': 'withdrawal_pending_review',
                                  'old_sha256': old['sha256'], 'new_sha256': None,
                                  'meaning': 'Not returned by exhaustive public exact-ID query; not confirmed deletion'})
    candidates, candidate_changes = {}, []
    for candidate in packet['candidates']:
        semantic = {k: v for k, v in candidate.items() if k != 'evidence'}
        mid = candidate['provider_material_id']
        fingerprint = digest(semantic)
        candidates[mid] = fingerprint
        old = baseline['candidates'].get(mid)
        if old != fingerprint:
            candidate_changes.append({'provider_material_id': mid, 'change': 'new' if old is None else 'changed',
                                      'old_sha256': old, 'new_sha256': fingerprint})
    if commit:
        for mid in sorted(set(baseline['candidates']) - set(candidates)):
            candidate_changes.append({'provider_material_id': mid, 'change': 'removed_from_candidate_queue_pending_review',
                                      'old_sha256': baseline['candidates'][mid], 'new_sha256': None})
    acquisition = [dict(json.loads(row['record']), attempt_id=row['id']) for row in db.execute(
        'SELECT id,record FROM attempts WHERE cycle=? ORDER BY id', (cycle['id'],))]
    result = {'schema': SCHEMA, 'cycle_id': cycle['id'], 'status': cycle['status'],
              'complete': cycle['status'] == 'complete', 'baseline_committed': commit,
              'scope': 'Fixed bounded public NOMAD window/cohort, not provider-wide coverage',
              'review_required': ['Independent scientific review', 'Source and license review'],
              'formal_project_total': 1081, 'admitted_delta': 0, 'excluded_example_count': 62,
              'profile_sha256': digest(profile), 'review_boundary_sha256': boundary['sha256'],
              'budget': {k: cycle[k] for k in ('requests', 'bytes_charged', 'retries_used')},
              'limits': {k: profile[k] for k in ('max_requests', 'max_bytes', 'max_response', 'retries')},
              'not_before_utc': utc(meta(db, 'not_before')) if meta(db, 'not_before') else None,
              'input_changes': input_changes, 'candidate_changes': candidate_changes,
              'diagnostics': diagnostics, 'gate_exclusions': gates, 'candidate_packet': packet,
              'acquisition': acquisition, 'stop_reason': cycle.get('stop_reason')}
    if commit:
        set_meta(db, 'baseline', {'entries': entries, 'candidates': candidates,
                                  'boundary_material_aliases': observed_boundary_labels})
    return result


def finish_page(db, cycle, profile):
    pending = cycle.pop('pending')
    cycle['batches'].append({'archive': pending['archive'], 'attribution': pending.get('attribution')})
    cycle['seen'] = sorted(set(cycle['seen']) | set(pending['ids']))
    if cycle['phase'].startswith('scan'):
        cycle['page'] += 1
        if pending['next'] and cycle['page'] < profile['pages']:
            cycle['cursor'] = pending['next']
            cycle['phase'] = 'scan_archive'
        else:
            old_ids = set(meta(db, 'baseline')['entries'])
            cycle['recheck_ids'] = sorted(old_ids - set(cycle['seen']))
            cycle['phase'] = 'recheck_archive'
    else:
        queried = cycle['recheck_ids'][:profile['page_size']]
        cycle['absent'] = sorted(set(cycle['absent']) | (set(queried) - set(pending['ids'])))
        cycle['recheck_ids'] = cycle['recheck_ids'][len(queried):]
        cycle['recheck_page'] += 1
        cycle['phase'] = 'recheck_archive'


def update(root, *, transport=None, clock=time.time, after_cache=None):
    """Resume one partial cycle or start one bounded cycle; no long cooldown sleeps."""
    root = Path(root).resolve()
    with locked(root), connect(root) as db:
        integrity(db)
        profile = meta(db, 'profile')
        cycle = latest(db)
        if cycle is None or cycle['status'] in ('complete', 'abandoned'):
            cycle_id = 1 if cycle is None else cycle['id'] + 1
            cycle = {'id': cycle_id, 'status': 'running', 'phase': 'scan_archive', 'page': 0,
                     'cursor': profile['after'], 'recheck_page': 0, 'batches': [], 'seen': [], 'absent': [],
                     'requests': 0, 'bytes_charged': 0, 'retries_used': 0, 'started_utc': utc(clock())}
            with db:
                db.execute('INSERT INTO cycles VALUES (?,?)', (cycle_id, canonical(cycle).decode()))
        elif cycle['status'] in ('blocked', 'exhausted'):
            return assemble_report(db, cycle)
        cycle['status'] = 'running'
        cycle.pop('stop_reason', None)
        try:
            while True:
                if cycle['phase'] == 'recheck_archive' and not cycle['recheck_ids']:
                    cycle['status'] = 'complete'
                    cycle['completed_utc'] = utc(clock())
                    with db:
                        result = assemble_report(db, cycle, commit=True)
                        cycle['report'] = result
                        save_cycle(db, cycle)
                    return result
                phase = cycle['phase']
                if phase.endswith('_archive'):
                    recheck = phase == 'recheck_archive'
                    ids = cycle['recheck_ids'][:profile['page_size']] if recheck else (profile['entry_ids'] or None)
                    body = archive_body(profile, None if recheck else cycle['cursor'], ids)
                    key = f'{phase}:{cycle["recheck_page"] if recheck else cycle["page"]}'
                    value, _ = fetch(db, cycle, ARCHIVE, body, key, transport or public_transport, clock, after_cache)
                    rows, continuation = page_rows(value, body, exhaustive=ids is not None)
                    if not recheck and not profile['after'] and continuation is None:
                        observed = set(cycle['seen']) | {row['entry_id'] for row in rows}
                        if value['pagination']['total'] > len(observed):
                            raise ValueError('Scan ended before advertised total without a continuation cursor')
                    cycle['pending'] = {'archive': key, 'ids': sorted({row['entry_id'] for row in rows}), 'next': continuation}
                    if rows:
                        cycle['phase'] = 'recheck_auth' if recheck else 'scan_auth'
                    else:
                        finish_page(db, cycle, profile)
                else:
                    ids = cycle['pending']['ids']
                    body = author_body(profile, ids)
                    key = cycle['pending']['archive'] + ':authors'
                    value, _ = fetch(db, cycle, ATTRIBUTION, body, key, transport or public_transport, clock, after_cache)
                    page_rows(value, body, exhaustive=True)
                    cycle['pending']['attribution'] = key
                    finish_page(db, cycle, profile)
                with db:
                    save_cycle(db, cycle)
        except Stopped as exc:
            cycle['stop_reason'] = str(exc)
        except (ValueError, KeyError, TypeError) as exc:
            cycle['status'] = 'blocked'
            cycle['stop_reason'] = str(exc)
        with db:
            save_cycle(db, cycle)
        return assemble_report(db, cycle)


def status(root):
    with connect(Path(root).resolve(), readonly=True) as db:
        integrity(db)
        cycle = latest(db)
        return {'schema': SCHEMA, 'profile': meta(db, 'profile'),
                'cycle': {k: v for k, v in cycle.items() if k != 'report'} if cycle else None,
                'history': [{key: state[key] for key in ('id', 'status', 'requests', 'bytes_charged', 'started_utc')}
                            for state in (json.loads(row['state']) for row in db.execute('SELECT state FROM cycles ORDER BY id'))],
                'not_before_utc': utc(meta(db, 'not_before')) if meta(db, 'not_before') else None,
                'formal_project_total': 1081, 'admitted_delta': 0}


def report(root, cycle=None):
    with connect(Path(root).resolve(), readonly=True) as db:
        integrity(db)
        selected = latest(db)
        if cycle is not None:
            row = db.execute('SELECT state FROM cycles WHERE id=?', (cycle,)).fetchone()
            if row is None:
                raise ValueError('Requested cycle does not exist')
            selected = json.loads(row['state'])
        if selected is None:
            return {'schema': SCHEMA, 'status': 'initialized', 'formal_project_total': 1081, 'admitted_delta': 0}
        return selected.get('report') or assemble_report(db, selected)


def abandon(root, reason, *, clock=time.time):
    if not isinstance(reason, str) or not reason.strip():
        raise ValueError('An explicit abandonment reason is required')
    root = Path(root).resolve()
    with locked(root), connect(root) as db:
        integrity(db)
        cycle = latest(db)
        if cycle is None or cycle['status'] in ('complete', 'abandoned'):
            raise ValueError('No incomplete cycle to abandon')
        cycle.update(status='abandoned', abandoned_utc=utc(clock()), stop_reason=reason)
        with db:
            cycle['report'] = assemble_report(db, cycle)
            save_cycle(db, cycle)
        return cycle['report']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    init = sub.add_parser('init')
    init.add_argument('store')
    for flag, default in [('pages', 1), ('page-size', 2), ('max-requests', 8), ('max-bytes', 2_000_000),
                          ('max-response', 500_000), ('retries', 1)]:
        init.add_argument('--' + flag, type=int, default=default)
    init.add_argument('--entry-id', action='append', default=[])
    init.add_argument('--after')
    for command in ('update', 'status', 'report', 'abandon'):
        child = sub.add_parser(command)
        child.add_argument('store')
        if command == 'abandon':
            child.add_argument('--reason', required=True)
        elif command == 'report':
            child.add_argument('--cycle', type=int)
    args = vars(parser.parse_args())
    command, root = args.pop('command'), args.pop('store')
    if command == 'init':
        args['entry_ids'] = args.pop('entry_id')
    try:
        result = {'init': init_store, 'update': update, 'status': status, 'report': report, 'abandon': abandon}[command](root, **args)
        print(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False))
        if command == 'update' and result.get('status') != 'complete':
            raise SystemExit(2)
    except ValueError as exc:
        parser.exit(2, f'{exc}\n')


if __name__ == '__main__':
    main()
