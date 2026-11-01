"""Exact test-only checkpoint for one frozen JARVIS append; never admission."""
import json
import polyomics_md_history as polyomics
from pathlib import Path
from types import ModuleType

from material_append_history import digest, encoded, load_frozen, recover_catalogs, recover_file

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = 'tests/jarvis_density_runtime/'
DATA_SHA256 = '8cd7307d48573fc1d7612154793040e191299abc147b58fbf328adaa99bd34fc'
FILES_SHA256 = '4cfbf789975e3340e1d0d7950a07822fb87b59b4da1068d1476b22cad14a6e41'
REGISTRY_SHA256 = 'fde21217caf22a0b7e3d1e248224fd4fb357c74fa7c3344d4bfa04043f494ed8'
DOCUMENTS_SHA256 = '6a955b71fbae8b9100a9a593eb14703c63e5568f1348bb657c6059c44b8d3237'
BATCH_ID = 'jarvis-density-native-draft-20261028'
CATALOG_PATHS = {'materials': 'materials_boundaries/data/materials.json',
                 'properties': 'materials_boundaries/data/reference_properties.json',
                 'sources': 'materials_boundaries/data/sources.json'}


def data_ledger(root=ROOT):
    return load_frozen(root, DIRECTORY + 'data-history.json', DATA_SHA256)


def file_ledger(root=ROOT):
    return load_frozen(root, DIRECTORY + 'files-history.json', FILES_SHA256)


def registry_ledger(root=ROOT):
    return load_frozen(root, DIRECTORY + 'registry-history.json', REGISTRY_SHA256)


def _raw_graph(root, ledger):
    raw = {key: encoded(value) for key, value in polyomics.checkpoint_catalogs(root).items()}
    hashes = {key: digest(value) for key, value in raw.items()}
    if hashes not in (ledger['baseline_sha256'], ledger['current_sha256']):
        raise AssertionError('Unknown complete JARVIS catalog byte image')
    return raw, hashes


def checkpoint_catalogs(root=ROOT):
    ledger = data_ledger(root)
    raw, _ = _raw_graph(root, ledger)
    return recover_catalogs(root, {key: json.loads(value) for key, value in raw.items()}, ledger)


def checkpoint_bytes(relative, raw=None, *, root=ROOT):
    path = Path(relative)
    if path.is_absolute() or path.drive or '..' in path.parts:
        raise AssertionError('JARVIS checkpoint path must be repository-relative')
    relative = path.as_posix()
    if raw is None:
        raw = (root / relative).read_bytes()
    if type(raw) is not bytes:
        raise AssertionError('JARVIS checkpoint input must be bytes')
    raw = polyomics.checkpoint_bytes(relative, raw, root=root)
    key = next((k for k, p in CATALOG_PATHS.items() if p == relative), None)
    if key is not None:
        ledger = data_ledger(root)
        if digest(raw) == ledger['baseline_sha256'][key]:
            return raw
        if digest(raw) == ledger['current_sha256'][key]:
            disk, hashes = _raw_graph(root, ledger)
            if hashes != ledger['current_sha256'] or raw != disk[key]:
                raise AssertionError('JARVIS current file requires the complete current disk image')
            return encoded(recover_catalogs(root, {k: json.loads(v) for k, v in disk.items()}, ledger)[key])
        return raw
    ledger = registry_ledger(root) if relative == 'tests/material_append_successors.py' else file_ledger(root)
    entry = ledger['updates'].get(relative)
    if entry is None or digest(raw) not in {entry['sha256'], entry['previous_sha256']}:
        return raw
    return recover_file(raw, entry)


def checkpoint_registry(root=ROOT):
    relative = 'tests/material_append_successors.py'
    raw = checkpoint_bytes(relative, root=root)
    if digest(raw) != registry_ledger(root)['updates'][relative]['previous_sha256']:
        raise AssertionError('Unknown pre-JARVIS registry image')
    module = ModuleType('jarvis_predecessor_registry')
    module.__file__ = str(root / relative)
    exec(compile(raw, module.__file__, 'exec'), module.__dict__)
    return module


def predecessor_descriptors(actual, root=ROOT):
    actual = polyomics.predecessor_descriptors(actual, root=root)
    previous = checkpoint_registry(root).FROZEN_SUCCESSORS
    descriptor = {'batch_id': BATCH_ID,
                  'data': (DIRECTORY + 'data-history.json', DATA_SHA256),
                  'files': (DIRECTORY + 'files-history.json', FILES_SHA256)}
    if actual != (descriptor,) + previous:
        raise AssertionError('Unknown live JARVIS successor descriptor tuple')
    return previous


def checkpoint_document(relative, raw, *, root=ROOT):
    raw = polyomics.checkpoint_document(relative, raw, root=root)
    ledger = load_frozen(root, DIRECTORY + 'document-history.json', DOCUMENTS_SHA256)
    entry = ledger['updates'].get(relative)
    if entry is None or digest(raw) not in {entry['sha256'], entry['previous_sha256']}:
        return raw
    return recover_file(raw, entry)
