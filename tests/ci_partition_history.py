"""Finite test-only recovery of the complete-core CI partition change.

Only hash-bound whole-file images can recover their exact bf1c7a8 predecessors.
Unknown bytes remain unchanged for historical callers to reject. Each call
rereads the independently pinned ledger; no cross-call cache is introduced.
"""
from pathlib import Path
from types import ModuleType

from material_append_history import digest, load_frozen, recover_file

ROOT = Path(__file__).resolve().parents[1]
BASE_COMMIT = 'bf1c7a86068c37c2733ac4d25c268144090f9aad'
LEDGER_PATH = 'tests/core_partition/partition-history.json'
LEDGER_SHA256 = '9a6befc0edd6562b7e2149b6197e90d7ee0fd2a8bdff1ddcb00e0247c77e5a30'
PATHS = frozenset({
    '.github/workflows/ci.yml',
    'scripts/run_history_replay_latest_ci.py',
    'tests/material_append_successors.py',
    'tests/test_tian_nano_ti_ci.py',
    'tests/history_replay/test_replay_compat.py',
    'tests/history_replay_latest/test_checkout_history.py',
    'tests/history_replay_latest/test_ci_contract.py',
})


def code_ledger():
    ledger = load_frozen(ROOT, LEDGER_PATH, LEDGER_SHA256)
    if (set(ledger) != {'schema_version', 'baseline_commit', 'updates'}
            or type(ledger['schema_version']) is not int or ledger['schema_version'] != 1
            or ledger['baseline_commit'] != BASE_COMMIT
            or set(ledger['updates']) != PATHS):
        raise AssertionError('Unexpected finite CI partition history ledger')
    return ledger


def project_partition_file(filename, raw):
    """Recover only a reviewed successor; never normalize unknown input."""
    if type(filename) is not str or type(raw) is not bytes:
        raise AssertionError('Invalid CI partition history file input')
    if filename not in PATHS:
        return raw
    entry = code_ledger()['updates'][filename]
    if digest(raw) == entry['sha256']:
        return recover_file(raw, entry)
    return raw


def require_partition_file(filename, raw):
    """Accept only the current whole image before returning its predecessor."""
    if type(filename) is not str or type(raw) is not bytes or filename not in PATHS:
        raise AssertionError('Invalid required CI partition history file input')
    entry = code_ledger()['updates'][filename]
    if digest(raw) != entry['sha256']:
        raise AssertionError('Unreviewed current CI partition history file')
    return recover_file(raw, entry)


def predecessor_registry():
    """Load the exact previous registry for unchanged historical assertions."""
    filename = 'tests/material_append_successors.py'
    raw = require_partition_file(filename, (ROOT / filename).read_bytes())
    registry = ModuleType('partition_predecessor_registry')
    registry.__file__ = str(ROOT / filename)
    exec(compile(raw, BASE_COMMIT + ':' + filename, 'exec'), registry.__dict__)
    return registry
