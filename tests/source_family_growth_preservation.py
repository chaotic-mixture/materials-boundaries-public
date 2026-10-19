"""Finite c90188d recovery using the reusable material append-history engine."""
import json
from pathlib import Path

from material_append_history import (
    FILES, TABLES, appended_rows, digest, encoded, graph_hashes,
    load_frozen, recover_catalogs, recover_file,
)

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
    return recover_catalogs(ROOT, current, data_ledger())


def project_growth_catalogs(current):
    """Project this append only; older layers still validate their own images."""
    additions = appended_rows(ROOT, data_ledger())
    if any(any(row.get("id") in {item["id"] for item in additions[name]}
               for row in current[table][field])
           for name, (table, field) in TABLES.items()):
        return recover_growth_catalogs(current)
    return current


def project_growth_file(filename, raw):
    """Recognize the finite new image; leave predecessor checks to older layers."""
    if type(raw) is not bytes:
        raise AssertionError("Growth file input must be bytes")
    entries = file_ledger()["updates"]
    if filename in entries and digest(raw) == entries[filename]["sha256"]:
        return recover_file(raw, entries[filename])
    return raw


def project_growth_catalog_bytes(filename, raw):
    if filename not in FILES.values() or type(raw) is not bytes:
        raise AssertionError("Unknown growth catalog path or input type")
    ledger = data_ledger()
    name = next(key for key, value in FILES.items() if value == filename)
    if ledger["current_sha256"][name] == ledger["baseline_sha256"][name]:
        return raw
    if digest(raw) == ledger["current_sha256"][name]:
        graph = {key: json.loads((ROOT / "materials_boundaries/data" / path).read_bytes())
                 for key, path in FILES.items()}
        graph[name] = json.loads(raw)
        return encoded(recover_growth_catalogs(graph)[name])
    return raw
