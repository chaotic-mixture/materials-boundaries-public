"""Finite test-only successor registry; never a runtime admission authority.

Descriptors are newest first and bind explicit immutable ledgers. Existing
historical wrappers prepend this registry to their unchanged older ledgers.
No directory discovery, candidate inference or unpinned input is accepted.
"""
from pathlib import Path

from material_append_history import (
    load_frozen, project_catalog_bytes_chain, project_catalog_chain,
    project_file_chain, recover_catalogs,
)

ROOT = Path(__file__).resolve().parents[1]
DATA_LEDGER = "tests/fixtures/primary_table_growth_data_20261019.json"
DATA_SHA256 = "faa453c3d57bb4a9040fac084cb9a96ad6c3437c237f80ea8eff4cc3e3fe261f"
FILE_LEDGER = "tests/fixtures/primary_table_growth_files_20261019.json"
FILE_SHA256 = "5af92f8baeb78cf21ea0098b13bfc0241de3623df5989897964426f0ffb33938"
DATA_2_LEDGER = "tests/fixtures/primary_table_growth_2_data_20261019.json"
DATA_2_SHA256 = "f3fcc3e8fdcdb292a2f3cf0b13c50de6bc90604ed2ac28b8938c9334e45933fc"
FILE_2_LEDGER = "tests/fixtures/primary_table_growth_2_files_20261019.json"
FILE_2_SHA256 = "95553e15c07be8aa7d1540875e83c52505fd472a73417a4e78ff0a29edf6fb3c"

FROZEN_SUCCESSORS = (
    {"batch_id": "nbs-rca-density-20261019",
     "data": (DATA_2_LEDGER, DATA_2_SHA256), "files": (FILE_2_LEDGER, FILE_2_SHA256)},
    {"batch_id": "nbs-salt-densities-20261019",
     "data": (DATA_LEDGER, DATA_SHA256), "files": (FILE_LEDGER, FILE_SHA256)},
)


def _descriptors():
    if not isinstance(FROZEN_SUCCESSORS, tuple) or not FROZEN_SUCCESSORS:
        raise AssertionError("Frozen successors must be a nonempty finite tuple")
    names = [descriptor["batch_id"] for descriptor in FROZEN_SUCCESSORS]
    if len(set(names)) != len(names):
        raise AssertionError("Duplicate frozen successor batch")
    return FROZEN_SUCCESSORS


def _index(batch_id):
    indices = [index for index, descriptor in enumerate(_descriptors())
               if descriptor["batch_id"] == batch_id]
    if len(indices) != 1:
        raise AssertionError("Unknown or duplicate frozen successor batch")
    return indices[0]


def _prefix(before):
    return _descriptors() if before is None else _descriptors()[:_index(before)]


def data_ledger(batch_id=None):
    descriptor = _descriptors()[0 if batch_id is None else _index(batch_id)]
    return load_frozen(ROOT, *descriptor["data"])


def file_ledger(batch_id=None):
    descriptor = _descriptors()[0 if batch_id is None else _index(batch_id)]
    return load_frozen(ROOT, *descriptor["files"])


def data_ledgers(*, before=None):
    return [load_frozen(ROOT, *descriptor["data"]) for descriptor in _prefix(before)]


def file_ledgers(*, before=None):
    return [load_frozen(ROOT, *descriptor["files"]) for descriptor in _prefix(before)]


def recover_latest_catalogs(current):
    """Strictly accept the exact latest predecessor or complete successor."""
    return recover_catalogs(ROOT, current, data_ledger())


def project_successor_catalogs(current, *, before=None):
    """Project known successors; the historical caller still validates input."""
    return project_catalog_chain(ROOT, current, data_ledgers(before=before))


def project_successor_catalog_bytes(filename, raw, *, before=None):
    return project_catalog_bytes_chain(ROOT, filename, raw, data_ledgers(before=before))


def project_successor_file(filename, raw, *, before=None):
    return project_file_chain(filename, raw, file_ledgers(before=before))
