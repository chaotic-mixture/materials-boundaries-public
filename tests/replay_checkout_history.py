"""Exact test-only recovery of the full-history checkout correction.

The three complete byte images are finite and pinned. Unknown bytes pass to
unchanged historical checks; this helper cannot authorize new workflow edits.
Its own ROOT is intentional, matching legacy documentation recovery: patching
the successor registry's ROOT must not mask a historical ledger-drift probe.
"""
from pathlib import Path
from material_append_history import digest, load_frozen, recover_file

ROOT = Path(__file__).resolve().parents[1]
BASE_COMMIT = 'e39b6d8a19576a05408b7da0e3faa8499b9f35f6'
LEDGER_PATH = 'tests/history_replay_latest/checkout-history.json'
LEDGER_SHA256 = '847d86d5e5004cdc4ab786f4d3239ec5cb6c6fb3b2ab5acd6a8e5bbcbed42e52'
PATHS = frozenset({'.github/workflows/ci.yml', 'tests/material_append_successors.py',
                   'tests/test_tian_nano_ti_ci.py'})


def code_ledger():
    ledger = load_frozen(ROOT, LEDGER_PATH, LEDGER_SHA256)
    if (set(ledger) != {'schema_version', 'baseline_commit', 'updates'}
            or type(ledger['schema_version']) is not int or ledger['schema_version'] != 1
            or ledger['baseline_commit'] != BASE_COMMIT
            or set(ledger['updates']) != PATHS):
        raise AssertionError('Unexpected finite checkout-history ledger')
    return ledger


def project_checkout_file(filename, raw):
    if type(filename) is not str or type(raw) is not bytes:
        raise AssertionError('Invalid checkout-history file input')
    if filename not in PATHS:
        return raw
    entry = code_ledger()['updates'][filename]
    if digest(raw) == entry['sha256']:
        return recover_file(raw, entry)
    return raw
