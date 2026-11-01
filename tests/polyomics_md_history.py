"""Exact test-only checkpoint for one frozen PolyOmics MD append; never admission."""
import json
import scc_flow_history as scc
from pathlib import Path
from types import ModuleType

from material_append_history import digest, encoded, load_frozen, recover_catalogs, recover_file

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = 'tests/polyomics_md_runtime/'
DATA_SHA256 = '25800896a359d0f610bcae5f9dc26b3509a6f6e07bc78bbbac5b5c7a47f73d5f'
FILES_SHA256 = 'bcfbeacec52f52a452bdbd3efba303374462c5232d61d32dfafcfce9943e53ab'
REGISTRY_SHA256 = '8d8878d97c21cab6e3142f948ec0ec69afadee9ce3978b0c758c9957afcca114'
DOCUMENTS_SHA256 = 'be964d838d952c9c7d375021146730ce7feae7c8881c3074406df1b0a024ce43'
BATCH_ID = 'polyomics-md-native-draft-20261028'
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
    raw = {key: encoded(value) for key, value in scc.checkpoint_catalogs(root).items()}
    hashes = {key: digest(value) for key, value in raw.items()}
    if hashes not in (ledger['baseline_sha256'], ledger['current_sha256']):
        raise AssertionError('Unknown complete PolyOmics MD catalog byte image')
    return raw, hashes


def checkpoint_catalogs(root=ROOT):
    ledger = data_ledger(root)
    raw, _ = _raw_graph(root, ledger)
    return recover_catalogs(root, {key: json.loads(value) for key, value in raw.items()}, ledger)


def checkpoint_bytes(relative, raw=None, *, root=ROOT):
    path = Path(relative)
    if path.is_absolute() or path.drive or '..' in path.parts:
        raise AssertionError('PolyOmics MD checkpoint path must be repository-relative')
    relative = path.as_posix()
    if raw is None:
        raw = (root / relative).read_bytes()
    if type(raw) is not bytes:
        raise AssertionError('PolyOmics MD checkpoint input must be bytes')
    raw = scc.checkpoint_bytes(relative, raw, root=root)
    key = next((k for k, p in CATALOG_PATHS.items() if p == relative), None)
    if key is not None:
        ledger = data_ledger(root)
        if digest(raw) == ledger['baseline_sha256'][key]:
            return raw
        if digest(raw) == ledger['current_sha256'][key]:
            disk, hashes = _raw_graph(root, ledger)
            if hashes != ledger['current_sha256'] or raw != disk[key]:
                raise AssertionError('PolyOmics MD current file requires the complete current disk image')
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
        raise AssertionError('Unknown pre-PolyOmics MD registry image')
    module = ModuleType('polyomics_predecessor_registry')
    module.__file__ = str(root / relative)
    exec(compile(raw, module.__file__, 'exec'), module.__dict__)
    return module


def predecessor_descriptors(actual, root=ROOT):
    actual = scc.predecessor_descriptors(actual, root=root)
    previous = checkpoint_registry(root).FROZEN_SUCCESSORS
    descriptor = {'batch_id': BATCH_ID,
                  'data': (DIRECTORY + 'data-history.json', DATA_SHA256),
                  'files': (DIRECTORY + 'files-history.json', FILES_SHA256)}
    if actual != (descriptor,) + previous:
        raise AssertionError('Unknown live PolyOmics MD successor descriptor tuple')
    return previous


def checkpoint_document(relative, raw, *, root=ROOT):
    raw = scc.checkpoint_document(relative, raw, root=root)
    ledger = load_frozen(root, DIRECTORY + 'document-history.json', DOCUMENTS_SHA256)
    entry = ledger['updates'].get(relative)
    if entry is None or digest(raw) not in {entry['sha256'], entry['previous_sha256']}:
        return raw
    return recover_file(raw, entry)


def jarvis_test_scope(module):
    """Adapt only the exact pre-MD descriptor tuple for old JARVIS assertions.

    Other functions retain their current, nested strict checkpoint behavior.
    This view is local to the old test module, not a mutation of shared modules.
    """
    view = ModuleType('polyomics_exact_jarvis_test_view')
    view.__dict__.update(vars(module))

    def predecessor_descriptors(actual, root=ROOT):
        previous = checkpoint_registry(root).FROZEN_SUCCESSORS
        if actual != previous:
            raise AssertionError('Unknown projected JARVIS descriptor tuple')
        descriptor = {'batch_id': BATCH_ID,
                      'data': (DIRECTORY + 'data-history.json', DATA_SHA256),
                      'files': (DIRECTORY + 'files-history.json', FILES_SHA256)}
        return module.predecessor_descriptors(scc.successor_descriptors((descriptor,) + actual, root=root), root=root)

    view.predecessor_descriptors = predecessor_descriptors
    return view
