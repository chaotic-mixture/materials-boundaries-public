"""Exact test-only projection of the reviewed Sanchez runtime append.

Only complete frozen predecessor/successor images are accepted. This module
does not authorize admission, relax old assertions or cache validation results.
"""
import json
import jarvis_density_history as jarvis
from pathlib import Path
from types import ModuleType

from material_append_history import digest, encoded, load_frozen, recover_catalogs, recover_file

ROOT = Path(__file__).resolve().parents[1]
BASELINE = 'f13586759af6a391635fa81da20c73eb6a6c1c6c'
DIRECTORY = 'tests/sanchez_al_mea_runtime/'
DATA_SHA256 = '0554b5416d827264b4aff4c52e646a6c01e6210eff88d39343b75f7e9c6aa18f'
FILES_SHA256 = 'bec3bd497d04b7ad95432cbe9e71f46e5aa81fbe937057327e05271aa6bb038c'
REGISTRY_SHA256 = 'b3bb3bf3a923838a72f925e88daf501baf6555f75cd5723a0488dd06a77aa95a'
DOCUMENTS_SHA256 = '80e15e83c854c9161e6ec74018f6efd76b00499ae055e9f7b5ed78512aaa7fae'
CATALOG_PATHS = {'materials': 'materials_boundaries/data/materials.json',
                 'properties': 'materials_boundaries/data/reference_properties.json',
                 'sources': 'materials_boundaries/data/sources.json'}


def data_ledger(root=ROOT):
    return load_frozen(root, DIRECTORY + 'data-history.json', DATA_SHA256)


def file_ledger(root=ROOT):
    return load_frozen(root, DIRECTORY + 'files-history.json', FILES_SHA256)


def registry_ledger(root=ROOT):
    return load_frozen(root, DIRECTORY + 'registry-history.json', REGISTRY_SHA256)


def checkpoint_catalogs(root=ROOT):
    ledger = data_ledger(root)
    raw = {key: encoded(value) for key, value in jarvis.checkpoint_catalogs(root).items()}
    hashes = {key: digest(value) for key, value in raw.items()}
    if hashes not in (ledger['current_sha256'], ledger['baseline_sha256']):
        raise AssertionError('Unknown complete Sanchez catalog byte image')
    return recover_catalogs(root, {key: json.loads(value) for key, value in raw.items()}, ledger)


def checkpoint_bytes(relative, raw=None, *, root=ROOT):
    path = Path(relative)
    if path.is_absolute() or path.drive or '..' in path.parts:
        raise AssertionError('Sanchez checkpoint path must be repository-relative')
    relative = path.as_posix()
    if raw is None:
        raw = (root / relative).read_bytes()
    if type(raw) is not bytes:
        raise AssertionError('Sanchez checkpoint input must be bytes')
    raw = jarvis.checkpoint_bytes(relative, raw, root=root)
    keys = [k for k, p in CATALOG_PATHS.items() if p == relative]
    if keys:
        key = keys[0]
        ledger = data_ledger(root)
        if digest(raw) == ledger['baseline_sha256'][key]:
            return raw
        if digest(raw) == ledger['current_sha256'][key]:
            return encoded(checkpoint_catalogs(root)[key])
        return raw
    ledger = registry_ledger(root) if relative == 'tests/material_append_successors.py' else file_ledger(root)
    entry = ledger['updates'].get(relative)
    if entry is None or digest(raw) not in {entry['sha256'], entry['previous_sha256']}:
        return raw
    return recover_file(raw, entry)


def checkpoint_registry(root=ROOT):
    relative = 'tests/material_append_successors.py'
    raw = checkpoint_bytes(relative, root=root)
    entry = registry_ledger(root)['updates'][relative]
    if digest(raw) != entry['previous_sha256']:
        raise AssertionError('Unknown Sanchez predecessor registry image')
    module = ModuleType('sanchez_predecessor_registry')
    module.__file__ = str(root / relative)
    exec(compile(raw, module.__file__, 'exec'), module.__dict__)
    return module


def predecessor_descriptors(actual, root=ROOT):
    """Project only the exact live registry tuple; mutated in-memory views fail."""
    actual = jarvis.predecessor_descriptors(actual, root=root)
    previous = checkpoint_registry(root).FROZEN_SUCCESSORS
    descriptor = {'batch_id': 'sanchez-al-mea-revised-20261027',
                  'data': (DIRECTORY + 'data-history.json', DATA_SHA256),
                  'files': (DIRECTORY + 'files-history.json', FILES_SHA256)}
    if actual != (descriptor,) + previous:
        raise AssertionError('Unknown live Sanchez successor descriptor tuple')
    return previous


def checkpoint_document(relative, raw, *, root=ROOT):
    raw = jarvis.checkpoint_document(relative, raw, root=root)
    ledger = load_frozen(root, DIRECTORY + 'document-history.json', DOCUMENTS_SHA256)
    entry = ledger['updates'].get(relative)
    if entry is None or digest(raw) not in {entry['sha256'], entry['previous_sha256']}:
        return raw
    return recover_file(raw, entry)
