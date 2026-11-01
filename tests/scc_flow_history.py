"""Exact test-only checkpoint for one frozen SCC fresh flow append; never admission."""
import json
from pathlib import Path
from types import ModuleType

from material_append_history import digest, encoded, load_frozen, recover_catalogs, recover_file

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = 'tests/scc_fresh_flow_runtime/'
DATA_SHA256 = 'e6448c679dccdc7cbc54bee880c5e582242abbf9e233386bb461fa8c58cfc0cb'
FILES_SHA256 = '8975b1d04a696694c539700087d50fdb9f9361ba16af0dcfe9209fcd198a20f3'
REGISTRY_SHA256 = '573854c0c8fd8e135faafdc16cdba70671716617964488f573c399a4537e6113'
DOCUMENTS_SHA256 = '5da48904e03ceeb9be92d7336214fa87d3e0da44f5586e4943edf2a4f12c5d1e'
BATCH_ID = 'scc-fresh-flow-nominal-recipes-20261029'
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
    raw = {key: (root / path).read_bytes() for key, path in CATALOG_PATHS.items()}
    hashes = {key: digest(value) for key, value in raw.items()}
    if hashes not in (ledger['baseline_sha256'], ledger['current_sha256']):
        raise AssertionError('Unknown complete SCC fresh flow catalog byte image')
    return raw, hashes


def checkpoint_catalogs(root=ROOT):
    ledger = data_ledger(root)
    raw, _ = _raw_graph(root, ledger)
    return recover_catalogs(root, {key: json.loads(value) for key, value in raw.items()}, ledger)


def checkpoint_bytes(relative, raw=None, *, root=ROOT):
    path = Path(relative)
    if path.is_absolute() or path.drive or '..' in path.parts:
        raise AssertionError('SCC fresh flow checkpoint path must be repository-relative')
    relative = path.as_posix()
    if raw is None:
        raw = (root / relative).read_bytes()
    if type(raw) is not bytes:
        raise AssertionError('SCC fresh flow checkpoint input must be bytes')
    key = next((k for k, p in CATALOG_PATHS.items() if p == relative), None)
    if key is not None:
        ledger = data_ledger(root)
        if digest(raw) == ledger['baseline_sha256'][key]:
            return raw
        if digest(raw) == ledger['current_sha256'][key]:
            disk, hashes = _raw_graph(root, ledger)
            if hashes != ledger['current_sha256'] or raw != disk[key]:
                raise AssertionError('SCC fresh flow current file requires the complete current disk image')
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
        raise AssertionError('Unknown pre-SCC fresh flow registry image')
    module = ModuleType('scc_predecessor_registry')
    module.__file__ = str(root / relative)
    exec(compile(raw, module.__file__, 'exec'), module.__dict__)
    return module


def predecessor_descriptors(actual, root=ROOT):
    previous = checkpoint_registry(root).FROZEN_SUCCESSORS
    descriptor = {'batch_id': BATCH_ID,
                  'data': (DIRECTORY + 'data-history.json', DATA_SHA256),
                  'files': (DIRECTORY + 'files-history.json', FILES_SHA256)}
    if actual != (descriptor,) + previous:
        raise AssertionError('Unknown live SCC fresh flow successor descriptor tuple')
    return previous


def checkpoint_document(relative, raw, *, root=ROOT):
    ledger = load_frozen(root, DIRECTORY + 'document-history.json', DOCUMENTS_SHA256)
    entry = ledger['updates'].get(relative)
    if entry is None or digest(raw) not in {entry['sha256'], entry['previous_sha256']}:
        return raw
    return recover_file(raw, entry)


def polyomics_test_scope(module):
    """Adapt only the exact pre-SCC descriptor tuple for old PolyOmics assertions.

    Other functions retain their current, nested strict checkpoint behavior.
    This view is local to the old test module, not a mutation of shared modules.
    """
    view = ModuleType('scc_exact_polyomics_test_view')
    view.__dict__.update(vars(module))

    def predecessor_descriptors(actual, root=ROOT):
        previous = checkpoint_registry(root).FROZEN_SUCCESSORS
        if actual != previous:
            raise AssertionError('Unknown projected JARVIS descriptor tuple')
        descriptor = {'batch_id': BATCH_ID,
                      'data': (DIRECTORY + 'data-history.json', DATA_SHA256),
                      'files': (DIRECTORY + 'files-history.json', FILES_SHA256)}
        return module.predecessor_descriptors((descriptor,) + actual, root=root)

    view.predecessor_descriptors = predecessor_descriptors
    return view


def successor_descriptors(actual, root=ROOT):
    """Prepend only this exact SCC descriptor to its exact frozen predecessor."""
    previous = checkpoint_registry(root).FROZEN_SUCCESSORS
    if actual != previous:
        raise AssertionError('Unknown pre-SCC successor descriptor tuple')
    descriptor = {'batch_id': BATCH_ID,
                  'data': (DIRECTORY + 'data-history.json', DATA_SHA256),
                  'files': (DIRECTORY + 'files-history.json', FILES_SHA256)}
    return (descriptor,) + actual
