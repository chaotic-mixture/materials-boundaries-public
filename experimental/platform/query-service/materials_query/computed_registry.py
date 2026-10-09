"""Local-only reviewed overlay. This is a new recovery candidate, not a lost release.

Trust anchor: a reviewer supplies an independently checked review SHA-256. A hash
proves identity, not scientific correctness or reviewer authentication. No HTTP
write route exists. SQLite is an integrity-checked local store, not tamper-proof.
"""
from copy import deepcopy
from contextlib import contextmanager
from hashlib import sha256
from importlib.resources import files
from pathlib import Path
import json
import math
import re
import sqlite3

BASELINE_PIN = '259d5d0e87635fec6f87ce544c8a252494038cbb1643228eeb685d5501f17897'
MAX_EXPORT_BYTES = 1_048_576
MAX_RECORDS = 1000


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()


def digest(value):
    return sha256(canonical(value)).hexdigest()


def baseline_digest():
    pin = files('materials_query').joinpath('pins/legacy_baseline.json').read_bytes()
    if sha256(pin).hexdigest() != BASELINE_PIN:
        raise ValueError('Baseline pin was replaced')
    expected = json.loads(pin)
    root = files('materials_boundaries')
    # Exact manifest, not a record count: detect changed values and extra files.
    actual = {str(p.relative_to(root)): sha256(p.read_bytes()).hexdigest()
              for p in sorted(Path(root).rglob('*')) if p.is_file() and p.suffix in {'.py', '.json'}}
    if actual != expected:
        raise ValueError('Installed legacy baseline differs from the recovery anchor')
    return digest(expected)


def validate_review(review):
    if set(review) != {'schema', 'packet_sha256', 'reviewer', 'rationale', 'records'}:
        raise ValueError('Unexpected review shape')
    if review['schema'] != 'computed-review-recovery/1' or not re.fullmatch('[0-9a-f]{64}', review['packet_sha256']):
        raise ValueError('Invalid review identity')
    if not all(isinstance(review[k], str) and review[k].strip() for k in ('reviewer', 'rationale')):
        raise ValueError('Reviewer and rationale required')
    if not isinstance(review['records'], list) or len(review['records']) > MAX_RECORDS:
        raise ValueError('Too many review records')
    ids = set()
    for r in review['records']:
        if set(r) != {'candidate_id', 'decision', 'reason', 'project_material_id', 'formula', 'provider', 'provider_entry_id', 'provider_material_id', 'source_url', 'density', 'attribution', 'rights', 'method'}:
            raise ValueError('Unexpected reviewed record fields')
        if r['decision'] not in ('accepted', 'held') or not isinstance(r['reason'], str) or not r['reason'].strip():
            raise ValueError('Explicit reviewed decision required')
        for k in ('candidate_id', 'formula', 'provider_entry_id', 'provider_material_id', 'attribution', 'rights', 'method'):
            if not isinstance(r[k], str) or not r[k].strip() or len(r[k]) > 4096:
                raise ValueError('Invalid record text')
        if r['candidate_id'] in ids:
            raise ValueError('Duplicate candidate ID')
        ids.add(r['candidate_id'])
        if r['provider'] != 'nomad' or not re.fullmatch(r'[A-Za-z0-9_-]{1,128}', r['provider_entry_id']):
            raise ValueError('Unsupported provider or entry ID')
        if not re.fullmatch(r'[A-Za-z0-9_-]{1,128}', r['provider_material_id']):
            raise ValueError('Invalid material ID')
        if r['project_material_id'] != 'computed:nomad:' + r['provider_material_id']:
            raise ValueError('Canonical project ID must bind provider material ID')
        if r['source_url'] != 'https://nomad-lab.eu/prod/v1/gui/entry/id/' + r['provider_entry_id']:
            raise ValueError('Source URL must bind exact provider entry')
        d = r['density']
        if not isinstance(d, dict) or set(d) != {'value', 'unit', 'evidence_kind', 'source_path'}:
            raise ValueError('Invalid density')
        if type(d['value']) not in (int, float) or not math.isfinite(d['value']) or d['value'] <= 0:
            raise ValueError('Density must be finite and positive')
        if d['unit'] != 'kg/m^3' or d['evidence_kind'] != 'computed' or d['source_path'] != 'results.properties.structures.structure_original.mass_density':
            raise ValueError('Exact computed-density provenance required')
    if len(canonical(review)) > MAX_EXPORT_BYTES:
        raise ValueError('Review exceeds fixed export budget')


class ComputedRegistry:
    """Explicit local API. Database paths never enter HTTP request models."""
    def __init__(self, database, review, *, trusted_review_sha256):
        review = deepcopy(review)
        if digest(review) != trusted_review_sha256:
            raise ValueError('Review digest differs from independent trust anchor')
        validate_review(review)
        self._review = review
        self.review_digest = trusted_review_sha256
        self.baseline = baseline_digest()
        self.database = str(database)
        self._by_id = {r['candidate_id']: r for r in review['records']}
        with self._connect() as db:
            db.execute('BEGIN IMMEDIATE')
            db.execute('CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS entries (id TEXT PRIMARY KEY, payload TEXT NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS admissions (id TEXT PRIMARY KEY, payload_sha256 TEXT NOT NULL)')
            existing = dict(db.execute('SELECT key,value FROM metadata'))
            expected = {'baseline': self.baseline, 'review': self.review_digest, 'schema': 'computed-registry-recovery/1'}
            if not existing:
                if db.execute('SELECT count(*) FROM entries').fetchone()[0] or db.execute('SELECT count(*) FROM admissions').fetchone()[0]:
                    raise ValueError('Missing initial registry anchors')
                db.executemany('INSERT INTO metadata VALUES (?,?)', expected.items())
            elif existing != expected:
                raise ValueError('Initial baseline and review input cannot be replaced')
            self._records(db)

    @contextmanager
    def _connect(self):
        db = sqlite3.connect(self.database, timeout=10)
        try:
            db.execute('PRAGMA busy_timeout=10000')
            with db:
                yield db
        finally:
            db.close()

    def _records(self, db):
        if dict(db.execute('SELECT key,value FROM metadata')) != {'baseline':self.baseline,'review':self.review_digest,'schema':'computed-registry-recovery/1'}:
            raise ValueError('Registry anchor changed')
        rows = dict(db.execute('SELECT id,payload FROM entries'))
        ledger = dict(db.execute('SELECT id,payload_sha256 FROM admissions'))
        if rows.keys() != ledger.keys():
            raise ValueError('Deleted or forged admission entry')
        records = []
        for key, payload in sorted(rows.items()):
            expected = self._by_id.get(key)
            if expected is None or expected['decision'] != 'accepted' or payload.encode() != canonical(expected) or ledger[key] != digest(expected):
                raise ValueError('Forged or changed reviewed admission')
            records.append(deepcopy(expected))
        return records

    def admit(self, candidate_ids):
        """All-or-nothing local admission; repeated/concurrent replay is idempotent."""
        if not isinstance(candidate_ids, (list, tuple)):
            raise ValueError('Candidate IDs must be an explicit list')
        ids = list(candidate_ids)
        if not ids or len(ids) > MAX_RECORDS or any(not isinstance(i, str) for i in ids):
            raise ValueError('Bounded explicit candidate IDs required')
        with self._connect() as db:
            db.execute('BEGIN IMMEDIATE')
            self._records(db)
            for key in ids:
                r = self._by_id.get(key)
                if r is None or r['decision'] != 'accepted':
                    raise ValueError('Only exact accepted reviewed candidates may be admitted')
                db.execute('INSERT OR IGNORE INTO entries VALUES (?,?)', (key, canonical(r).decode()))
                db.execute('INSERT OR IGNORE INTO admissions VALUES (?,?)', (key, digest(r)))
            records = self._records(db)
            self._envelope(records)  # size guard before transaction commit
        return self.snapshot()

    def _envelope(self, records):
        result = {'schema':'computed-overlay-recovery/1', 'namespace':'computed', 'baseline_version':self.baseline,
                  'review_version':self.review_digest, 'overlay_version':digest(records), 'records':records,
                  'project_unique_material_count':len({r['project_material_id'] for r in records}),
                  'provider_entry_count':len(records), 'legacy_unique_material_count':1057,
                  'cross_namespace_equivalence':False, 'relationship_graph_reconstructed':False}
        if len(canonical(result)) > MAX_EXPORT_BYTES:
            raise ValueError('Overlay exceeds fixed export budget')
        return result

    def snapshot(self):
        with self._connect() as db:
            db.execute('BEGIN')
            return self._envelope(self._records(db))
