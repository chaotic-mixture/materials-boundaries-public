"""Exact, finite test-only inputs for the pre-Curaua checkpoint.

This is not an admission mechanism. Unknown images pass through for the
historical oracle to reject; no result or source input is cached across calls.
"""
import json
from pathlib import Path
from types import ModuleType

from material_append_history import digest, encoded, load_frozen, recover_catalogs, recover_file

ROOT = Path(__file__).resolve().parents[1]
BASELINE = "fa170104195e573c868c57006ac77e7d866c28e9"
DIRECTORY = "tests/curaua_runtime/"
DATA_SHA256 = "ce10a8972b4935677db755e25e8b00239513207b83c877de57ae63218fbab375"
FILES_SHA256 = "74ab59414a6ca31f3bd41688e89dfd4db965b9effb6485e5b97685a8f95fe617"
REGISTRY_SHA256 = "4ca52ca2b05d7a53fcc415f76496c04bd8510520cdef3063699d4dcfb040d097"
DOCUMENTS_SHA256 = "64e3af42447851c4959e72c7684900454ec7c3c2a751e6bff65e1e8491e4d441"
INPUTS_SHA256 = "e90a4d812bac9a14ccfcb856df950f61fb27423cc1fe76eba34612069f0d629b"
CATALOG_PATHS = {
    "materials": "materials_boundaries/data/materials.json",
    "properties": "materials_boundaries/data/reference_properties.json",
    "sources": "materials_boundaries/data/sources.json",
}


def data_ledger(root=ROOT):
    return load_frozen(root, DIRECTORY + "data-history.json", DATA_SHA256)


def file_ledger(root=ROOT):
    return load_frozen(root, DIRECTORY + "files-history.json", FILES_SHA256)


def checkpoint_catalogs(root=ROOT):
    ledger = data_ledger(root)
    raw = {key: (root / path).read_bytes() for key, path in CATALOG_PATHS.items()}
    hashes = {key: digest(value) for key, value in raw.items()}
    if hashes not in (ledger["current_sha256"], ledger["baseline_sha256"]):
        raise AssertionError("Unrecognized complete Curaua catalog image")
    graph = {key: json.loads(value) for key, value in raw.items()}
    return recover_catalogs(root, graph, ledger)


def _project(raw, entry):
    if digest(raw) not in {entry["sha256"], entry["previous_sha256"]}:
        return raw
    return recover_file(raw, entry)


def checkpoint_bytes(relative, raw=None, *, root=ROOT):
    relative = Path(relative).as_posix()
    if raw is None:
        raw = (root / relative).read_bytes()
    keys = [key for key, path in CATALOG_PATHS.items() if relative == path]
    if keys:
        key = keys[0]
        ledger = data_ledger(root)
        if digest(raw) == ledger["baseline_sha256"][key]:
            return raw
        if digest(raw) != ledger["current_sha256"][key]:
            return raw
        return encoded(checkpoint_catalogs(root)[key])
    if relative == "tests/material_append_successors.py":
        ledger = load_frozen(root, DIRECTORY + "registry-history.json", REGISTRY_SHA256)
    else:
        ledger = file_ledger(root)
    entry = ledger["updates"].get(relative)
    return _project(raw, entry) if entry is not None else raw


def checkpoint_document(relative, raw, *, root=ROOT):
    ledger = load_frozen(root, DIRECTORY + "document-history.json", DOCUMENTS_SHA256)
    entry = ledger["updates"].get(relative)
    return _project(raw, entry) if entry is not None else raw


def checkpoint_registry(root=ROOT):
    path = "tests/material_append_successors.py"
    raw = checkpoint_bytes(path, root=root)
    ledger = load_frozen(root, DIRECTORY + "registry-history.json", REGISTRY_SHA256)
    if digest(raw) != ledger["updates"][path]["previous_sha256"]:
        raise AssertionError("Unrecognized Curaua registry checkpoint")
    module = ModuleType("curaua_predecessor_registry")
    module.__file__ = str(root / path)
    exec(compile(raw, module.__file__, "exec"), module.__dict__)
    return module


def checkpoint_new_file(relative, raw=None, *, root=ROOT):
    manifest = load_frozen(root, DIRECTORY + "checkpoint-inputs.json", INPUTS_SHA256)
    if raw is None:
        raw = (root / relative).read_bytes()
    if relative not in manifest["added_files"] or digest(raw) != manifest["added_files"][relative]:
        raise AssertionError("Unknown or changed Curaua checkpoint addition")
    return raw


def checkpoint_inventory(relative, actual_ids, *, root=ROOT):
    manifest = load_frozen(root, DIRECTORY + "checkpoint-inputs.json", INPUTS_SHA256)
    entry = manifest["inventories"][relative]
    if list(actual_ids) != entry["current"]:
        raise AssertionError("Unknown Curaua checkpoint test inventory")
    actual_paths = sorted(path.relative_to(root).as_posix()
                          for path in (root / relative).glob("test*.py"))
    if actual_paths != entry["current_paths"]:
        raise AssertionError("Unknown Curaua checkpoint test file inventory")
    for path in actual_paths:
        if path in entry["added_files"]:
            checkpoint_new_file(path, root=root)
        else:
            require_checkpoint_bytes(path, root=root)
    return list(entry["previous"])


def require_checkpoint_bytes(relative, raw=None, *, root=ROOT):
    """Reject unknown input even when a downstream oracle only parses JSON."""
    if raw is None:
        raw = (root / relative).read_bytes()
    result = checkpoint_bytes(relative, raw, root=root)
    manifest = load_frozen(root, DIRECTORY + "checkpoint-inputs.json", INPUTS_SHA256)
    expected = manifest["baseline_files"].get(relative)
    if expected is None or digest(result) != expected:
        raise AssertionError("Unrecognized strict Curaua checkpoint input")
    return result


def checkpoint_changed_paths(raw, *, root=ROOT):
    """Validate every changed original file before replaying the candidate check."""
    paths = raw.decode("utf-8").splitlines()
    for relative in paths:
        require_checkpoint_bytes(relative, root=root)
    return b""


def registry_ledger(root=ROOT):
    return load_frozen(root, DIRECTORY + "registry-history.json", REGISTRY_SHA256)
