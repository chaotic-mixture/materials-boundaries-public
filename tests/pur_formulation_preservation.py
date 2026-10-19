"""Finite PUR append configuration; no runtime authorization or source inference."""
from pathlib import Path

from material_append_history import (
    FILES, TABLES, appended_rows, digest, encoded, graph_hashes, load_frozen,
    project_catalog_bytes_chain, project_catalog_chain, project_file_chain,
    recover_catalogs, recover_file,
)

ROOT = Path(__file__).resolve().parents[1]
BASELINE_COMMIT = "2509ee231edb62872ed323e8346895bd55c36c92"
DATA_LEDGER = "tests/fixtures/pur_formulation_data_20261019.json"
DATA_SHA256 = "541a4e325834ed992246489846bcfcf83480bfb86494ec2a212d78de821bf167"
FILE_LEDGER = "tests/fixtures/pur_formulation_files_20261019.json"
FILE_SHA256 = "da273be57628bc69a55ae3cacaea4c07370fa56cd2dec6678f062b551acf7dba"


def data_ledger():
    return load_frozen(ROOT, DATA_LEDGER, DATA_SHA256)


def file_ledger():
    return load_frozen(ROOT, FILE_LEDGER, FILE_SHA256)


def recover_pre_pur_catalogs(current):
    return recover_catalogs(ROOT, current, data_ledger())


def project_pur_catalogs(current):
    return project_catalog_chain(ROOT, current, [data_ledger()])


def project_pur_catalog_bytes(filename, raw):
    return project_catalog_bytes_chain(ROOT, filename, raw, [data_ledger()])


def project_pur_file(filename, raw):
    return project_file_chain(filename, raw, [file_ledger()])
