"""Finite c90188d recovery using the reusable material append-history engine."""
from pathlib import Path

from material_append_history import (
    FILES, TABLES, appended_rows, digest, encoded, graph_hashes,
    load_frozen, project_catalog_bytes_chain, project_catalog_chain,
    project_file_chain, recover_catalogs, recover_file,
)
import pur_formulation_preservation as pur_history
import material_append_successors as successors

ROOT = Path(__file__).resolve().parents[1]
BASELINE_COMMIT = "c90188dcd5ac3a19863be0b49419722571b17eff"
DATA_LEDGER = "tests/fixtures/source_family_growth_data_20261019.json"
DATA_SHA256 = "9dfc8d71e89041f05e11a870ad29aea34cb3ab90586bcea8f1d717adc9878ac3"
FILE_LEDGER = "tests/fixtures/source_family_growth_files_20261019.json"
FILE_SHA256 = "3fa801355a51e2c369f7f5963cefc69ab7995912903ec10041959d3f6b0d8e76"


def data_ledger():
    return load_frozen(ROOT, DATA_LEDGER, DATA_SHA256)


def file_ledger():
    return load_frozen(ROOT, FILE_LEDGER, FILE_SHA256)


def recover_growth_catalogs(current):
    current = pur_history.project_pur_catalogs(current)
    return recover_catalogs(ROOT, current, data_ledger())


def project_growth_catalogs(current):
    """Project this append only; older layers still validate their own images."""
    return project_catalog_chain(ROOT, current, successors.data_ledgers() + [pur_history.data_ledger(), data_ledger()])


def project_growth_file(filename, raw):
    """Recognize the finite new image; leave predecessor checks to older layers."""
    return project_file_chain(filename, raw, successors.file_ledgers() + [pur_history.file_ledger(), file_ledger()])


def project_growth_catalog_bytes(filename, raw):
    return project_catalog_bytes_chain(ROOT, filename, raw, successors.data_ledgers() + [pur_history.data_ledger(), data_ledger()])
