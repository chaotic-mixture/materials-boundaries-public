"""Test-only exact recovery of finite, hash-pinned material append packets.

The engine is independent of a material family. A new append needs an explicit
frozen ledger; this module never discovers or authorizes arbitrary additions.
"""
from copy import deepcopy
from hashlib import sha256
import json

FILES = {"materials": "materials.json", "properties": "reference_properties.json", "sources": "sources.json"}
TABLES = {"identities": ("materials", "identities"), "grades": ("materials", "grades"),
          "states": ("materials", "records"), "properties": ("properties", "records"),
          "sources": ("sources", "records")}


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")


def digest(raw):
    return sha256(raw).hexdigest()


def unique_keys(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise AssertionError("Duplicate append-history key")
        value[key] = item
    return value


def load_frozen(root, path, expected):
    raw = (root / path).read_bytes()
    if digest(raw) != expected:
        raise AssertionError("Unreviewed append-history ledger")
    return json.loads(raw, object_pairs_hook=unique_keys)


def appended_rows(root, ledger):
    result = {name: [] for name in TABLES}
    for descriptor in ledger["packets"]:
        path = (root / descriptor["path"]).resolve()
        if not path.is_relative_to((root / "experimental/material-batches").resolve()):
            raise AssertionError("Append packet is outside the reviewed directory")
        raw = path.read_bytes()
        if digest(raw) != descriptor["sha256"]:
            raise AssertionError("Unreviewed append packet bytes")
        packet = json.loads(raw, object_pairs_hook=unique_keys)
        if set(descriptor["added_ids"]) != set(TABLES):
            raise AssertionError("Incomplete append collection inventory")
        for name, (table, field) in TABLES.items():
            ids = descriptor["added_ids"][name]
            rows = [row for row in packet["catalogs"][table][field] if row["id"] in ids]
            if (len(set(ids)) != len(ids) or len(rows) != len(ids)
                    or {row["id"] for row in rows} != set(ids)):
                raise AssertionError("Incomplete or duplicate append inventory")
            result[name].extend(deepcopy(rows))
    for rows in result.values():
        if len({row["id"] for row in rows}) != len(rows):
            raise AssertionError("Duplicate append ID between packets")
    return result


def graph_hashes(graph):
    if type(graph) is not dict or set(graph) != set(FILES):
        raise AssertionError("Incomplete append-history graph")
    return {name: digest(encoded(graph[name])) for name in FILES}


def recover_catalogs(root, current, ledger):
    """Require either the exact predecessor or the complete exact successor."""
    actual = graph_hashes(current)
    if actual == ledger["baseline_sha256"]:
        return deepcopy(current)
    recovered = deepcopy(current)
    for name, rows in appended_rows(root, ledger).items():
        table, field = TABLES[name]
        expected = {row["id"]: row for row in rows}
        selected = [row for row in current[table][field] if row.get("id") in expected]
        if (len(selected) != len(expected) or {row["id"] for row in selected} != set(expected)
                or any(encoded(row) != encoded(expected[row["id"]]) for row in selected)):
            raise AssertionError("Append recovery requires every complete pinned addition")
        recovered[table][field] = [row for row in recovered[table][field] if row.get("id") not in expected]
    if graph_hashes(recovered) != ledger["baseline_sha256"]:
        raise AssertionError("Append predecessor catalog bytes changed")
    if actual != ledger["current_sha256"]:
        raise AssertionError("Unreviewed append successor catalog order or bytes")
    return recovered


def recover_file(raw, entry):
    """Reverse only finite, offset-bound byte edits with a whole-file round trip."""
    if type(raw) is not bytes:
        raise AssertionError("Append-history file input must be bytes")
    if digest(raw) == entry["previous_sha256"]:
        return raw
    if digest(raw) != entry["sha256"]:
        raise AssertionError("Unreviewed append-history file bytes")
    chunks, cursor, shift = [], 0, 0
    for edit in entry["edits"]:
        if type(edit["offset"]) is not int or edit["offset"] < 0:
            raise AssertionError("Invalid append-history edit offset")
        before, after = edit["before"].encode("utf-8"), edit["after"].encode("utf-8")
        offset = edit["offset"] + shift
        if offset < cursor or raw[offset:offset + len(after)] != after:
            raise AssertionError("Append-history after image mismatch")
        chunks.extend((raw[cursor:offset], before))
        cursor = offset + len(after)
        shift += len(after) - len(before)
    previous = b"".join(chunks) + raw[cursor:]
    if digest(previous) != entry["previous_sha256"]:
        raise AssertionError("Append-history predecessor file bytes changed")
    chunks, cursor = [], 0
    for edit in entry["edits"]:
        before, after = edit["before"].encode("utf-8"), edit["after"].encode("utf-8")
        offset = edit["offset"]
        if offset < cursor or previous[offset:offset + len(before)] != before:
            raise AssertionError("Append-history before image mismatch")
        chunks.extend((previous[cursor:offset], after))
        cursor = offset + len(before)
    if b"".join(chunks) + previous[cursor:] != raw:
        raise AssertionError("Append-history file round trip failed")
    return previous


def _ordered_catalog_ledgers(ledgers):
    """Require an explicit newest-first chain of adjacent frozen data images."""
    if not isinstance(ledgers, (list, tuple)):
        raise AssertionError("Append-history chain must be an explicit finite sequence")
    for newer, older in zip(ledgers, ledgers[1:]):
        if newer["baseline_sha256"] != older["current_sha256"]:
            raise AssertionError("Append-history catalog chain is not adjacent or ordered")
    return ledgers


def project_catalog_chain(root, current, ledgers):
    """Remove recognized finite successors; older callers still validate input.

    This is a compatibility projection, not a permissive recovery or admission
    API. A partial known append enters strict recovery and fails. A graph with
    no known additions is passed to the older layer's unchanged exact checks.
    """
    graph_hashes(current)
    for ledger in _ordered_catalog_ledgers(ledgers):
        additions = appended_rows(root, ledger)
        if (graph_hashes(current) == ledger["current_sha256"]
                or any(any(row.get("id") in {item["id"] for item in additions[name]}
                           for row in current[table][field])
                       for name, (table, field) in TABLES.items())):
            current = recover_catalogs(root, current, ledger)
    return current


def project_file_chain(filename, raw, ledgers):
    """Reverse only known byte images; the historical caller rejects others."""
    if type(filename) is not str or type(raw) is not bytes or not isinstance(ledgers, (list, tuple)):
        raise AssertionError("Invalid finite file projection input")
    entries = [ledger["updates"][filename] for ledger in ledgers if filename in ledger["updates"]]
    for newer, older in zip(entries, entries[1:]):
        if newer["previous_sha256"] != older["sha256"]:
            raise AssertionError("Append-history file chain is not adjacent or ordered")
    if filename == "tests/material_append_history.py":
        from material_append_replay_compat import project_engine_bytes
        raw = project_engine_bytes(raw)
    for entry in entries:
        if digest(raw) == entry["sha256"]:
            raw = recover_file(raw, entry)
    return raw


def project_catalog_bytes_chain(root, filename, raw, ledgers):
    """Align the whole disk graph before substituting a known historical file.

    Replacing one current table with an older image before projecting the other
    tables would create a partial append. Recover each intervening prefix on
    the complete graph before substituting the matching single-file image.
    The unmodified disk graph and cursor belong to this invocation only; later
    calls reread disk inputs. A substituted input must not repair the cached
    disk graph and hide a later prefix failure. Unknown images do not load it.
    """
    if filename not in FILES.values() or type(raw) is not bytes:
        raise AssertionError("Unknown append-history catalog path or input type")
    ledgers = _ordered_catalog_ledgers(ledgers)
    name = next(key for key, value in FILES.items() if value == filename)
    graph, processed = None, 0
    for index, ledger in enumerate(ledgers):
        if (ledger["current_sha256"][name] != ledger["baseline_sha256"][name]
                and digest(raw) == ledger["current_sha256"][name]):
            if graph is None:
                graph = {key: json.loads((root / "materials_boundaries/data" / path).read_bytes(),
                                        object_pairs_hook=unique_keys)
                         for key, path in FILES.items()}
            graph = project_catalog_chain(root, graph, ledgers[processed:index])
            processed = index
            selected = dict(graph)
            selected[name] = json.loads(raw, object_pairs_hook=unique_keys)
            raw = encoded(recover_catalogs(root, selected, ledger)[name])
    return raw
