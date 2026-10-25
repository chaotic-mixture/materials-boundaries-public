"""Finite test-only recovery of the exact pre-Ewurum reactive checkpoint.

Only pinned byte images are projected. Unknown images remain unknown to the
historical oracle; strict reads and inventory recovery reject them. Every call
rereads its inputs, and this module does not authorize runtime admission.
"""
import json
from pathlib import Path
from types import ModuleType

from material_append_history import digest, encoded, load_frozen, recover_catalogs, recover_file

ROOT = Path(__file__).resolve().parents[1]
BASELINE = "29a33009d763c0ef52943c1bce28e24c436c74ac"
DIRECTORY = "tests/ewurum_reactive_runtime/"
DATA_SHA256 = "1fc44b8bc6f121a3323b632a1cdce8f7511bdbd2421bd33768529f359976b513"
FILES_SHA256 = "2f7a1b0b71f4c35411bab466398df1dc3abfcef8bf74b14b6cff33717e032857"
REGISTRY_SHA256 = "2274c5f525ea74a11cfa461ef42f04bf5366420bc27e05c21a6f3761b08c7ec7"
DOCUMENTS_SHA256 = "c58d7dd5a777c62d98a2ebf3d3c5947436dac4414e4f2051c0df437402f2124c"
INPUTS_SHA256 = "60d10267025be222c163a84a0e6812385441fc10c6f80d3b80026aefe40d56d7"
CATALOG_PATHS = {
    "materials": "materials_boundaries/data/materials.json",
    "properties": "materials_boundaries/data/reference_properties.json",
    "sources": "materials_boundaries/data/sources.json",
}


def _relative(relative):
    path = Path(relative)
    if path.is_absolute() or path.drive or ".." in path.parts:
        raise AssertionError("Ewurum checkpoint paths must be repository-relative")
    return path.as_posix()


def data_ledger(root=ROOT):
    return load_frozen(root, DIRECTORY + "data-history.json", DATA_SHA256)


def file_ledger(root=ROOT):
    return load_frozen(root, DIRECTORY + "files-history.json", FILES_SHA256)


def registry_ledger(root=ROOT):
    return load_frozen(root, DIRECTORY + "registry-history.json", REGISTRY_SHA256)


def checkpoint_catalogs(root=ROOT):
    ledger = data_ledger(root)
    raw = {key: (root / path).read_bytes() for key, path in CATALOG_PATHS.items()}
    hashes = {key: digest(value) for key, value in raw.items()}
    if hashes not in (ledger["current_sha256"], ledger["baseline_sha256"]):
        raise AssertionError("Unrecognized complete Ewurum reactive catalog image")
    graph = {key: json.loads(value) for key, value in raw.items()}
    return recover_catalogs(root, graph, ledger)


def _project(raw, entry):
    if type(raw) is not bytes:
        raise AssertionError("Ewurum checkpoint file input must be bytes")
    if digest(raw) not in {entry["sha256"], entry["previous_sha256"]}:
        return raw
    return recover_file(raw, entry)


def checkpoint_bytes(relative, raw=None, *, root=ROOT):
    relative = _relative(relative)
    if raw is None:
        raw = (root / relative).read_bytes()
    if type(raw) is not bytes:
        raise AssertionError("Ewurum checkpoint file input must be bytes")
    keys = [key for key, path in CATALOG_PATHS.items() if relative == path]
    if keys:
        key = keys[0]
        ledger = data_ledger(root)
        if digest(raw) == ledger["baseline_sha256"][key]:
            return raw
        if digest(raw) != ledger["current_sha256"][key]:
            return raw
        return encoded(checkpoint_catalogs(root)[key])
    ledger = registry_ledger(root) if relative == "tests/material_append_successors.py" else file_ledger(root)
    entry = ledger["updates"].get(relative)
    return _project(raw, entry) if entry is not None else raw


def require_checkpoint_bytes(relative, raw=None, *, root=ROOT):
    """Recover one known file and require its exact predecessor byte hash."""
    relative = _relative(relative)
    if raw is None:
        raw = (root / relative).read_bytes()
    result = checkpoint_bytes(relative, raw, root=root)
    manifest = load_frozen(root, DIRECTORY + "checkpoint-inputs.json", INPUTS_SHA256)
    expected = manifest["baseline_files"].get(relative)
    if expected is None or digest(result) != expected:
        raise AssertionError("Unrecognized strict Ewurum reactive checkpoint input")
    return result


def checkpoint_document(relative, raw, *, root=ROOT):
    """Recover documentation after the existing truthful README normalizer."""
    relative = _relative(relative)
    ledger = load_frozen(root, DIRECTORY + "document-history.json", DOCUMENTS_SHA256)
    entry = ledger["updates"].get(relative)
    return _project(raw, entry) if entry is not None else raw


def checkpoint_registry(root=ROOT):
    path = "tests/material_append_successors.py"
    raw = checkpoint_bytes(path, root=root)
    ledger = registry_ledger(root)
    if digest(raw) != ledger["updates"][path]["previous_sha256"]:
        raise AssertionError("Unrecognized Ewurum reactive registry checkpoint")
    module = ModuleType("ewurum_reactive_predecessor_registry")
    module.__file__ = str(root / path)
    exec(compile(raw, module.__file__, "exec"), module.__dict__)
    return module


def checkpoint_new_file(relative, raw=None, *, root=ROOT):
    relative = _relative(relative)
    manifest = load_frozen(root, DIRECTORY + "checkpoint-inputs.json", INPUTS_SHA256)
    if raw is None:
        raw = (root / relative).read_bytes()
    if relative not in manifest["added_files"] or digest(raw) != manifest["added_files"][relative]:
        raise AssertionError("Unknown or changed Ewurum reactive checkpoint addition")
    return raw


def checkpoint_inventory_view(relative, actual_ids, *, root=ROOT):
    """Accept one complete current or previous directory image, never a mix."""
    relative = _relative(relative)
    manifest = load_frozen(root, DIRECTORY + "checkpoint-inputs.json", INPUTS_SHA256)
    entry = manifest["inventories"].get(relative)
    if entry is None:
        raise AssertionError("Unknown Ewurum reactive checkpoint test inventory")
    actual_ids = list(actual_ids)
    actual_files = list((root / relative).glob("test*.py"))
    if any(path.is_symlink() or not path.is_file() for path in actual_files):
        raise AssertionError("Ewurum checkpoint test paths must be regular files")
    actual_paths = sorted(path.relative_to(root).as_posix() for path in actual_files)
    if set(entry["current_file_sha256"]) != set(entry["current_paths"]):
        raise AssertionError("Incomplete Ewurum reactive checkpoint file hash inventory")
    raw_files = {path: (root / path).read_bytes() for path in actual_paths}
    actual_hashes = {path: digest(raw) for path, raw in raw_files.items()}
    previous_hashes = {path: manifest["baseline_files"][path] for path in entry["previous_paths"]}
    current_image = (actual_ids == entry["current"] and actual_paths == entry["current_paths"]
                     and actual_hashes == entry["current_file_sha256"])
    previous_image = (actual_ids == entry["previous"] and actual_paths == entry["previous_paths"]
                      and actual_hashes == previous_hashes)
    if not (current_image or previous_image):
        raise AssertionError("Ewurum checkpoint IDs, paths and bytes are not one complete current or previous inventory image")
    if current_image:
        updates = file_ledger(root)["updates"]
        for path, raw in raw_files.items():
            if path in entry["added_files"]:
                if manifest["added_files"].get(path) != digest(raw):
                    raise AssertionError("Unknown or changed Ewurum reactive checkpoint addition")
            else:
                restored = _project(raw, updates[path]) if path in updates else raw
                if manifest["baseline_files"].get(path) != digest(restored):
                    raise AssertionError("Unrecognized strict Ewurum reactive checkpoint test input")
    return list(entry["previous"]), list(entry["previous_paths"])


def checkpoint_inventory(relative, actual_ids, *, root=ROOT):
    return checkpoint_inventory_view(relative, actual_ids, root=root)[0]


def checkpoint_changed_paths(raw, *, root=ROOT):
    """Require every changed original file before replaying candidate checks."""
    for relative in raw.decode("utf-8").splitlines():
        require_checkpoint_bytes(relative, root=root)
    return b""
