"""Explicit, lossless replay of the reviewed five-class taxonomy migration.

This module does not classify new materials or run on ordinary catalog reads.
The finite historical migration is intentionally pinned; future catalog growth
uses the generic material contract, independently of this migration inventory.
"""
from copy import deepcopy
import hashlib
from importlib.resources import files
import json

TAXONOMY_POLICY_VERSION = "1.0.0"
MIGRATION_ID = "natural-biological-tissue-v1"
MIGRATION_RESOURCE = "taxonomy_migration_v1.json"
MIGRATION_SHA256 = "78f2c8f078856568d049aa9649101c0291d1c819e6dbb35e29f26c5da0cb0541"
BASELINE_COMMIT = "7e37be919ee97f1275249dcf745f9f55e951986a"
PRIMARY_CATEGORIES = ("metal", "inorganic", "polymer", "composite", "natural")


def _canonical(value):
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True,
                          separators=(",", ":"), allow_nan=False).encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as exc:
        raise ValueError("Taxonomy input must be finite UTF-8 JSON") from exc


def _digest(value):
    return hashlib.sha256(_canonical(value)).hexdigest()


def _unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate taxonomy ledger key: " + key)
        result[key] = value
    return result


def load_taxonomy_migration():
    """Return an independent copy of the exact packaged, versioned ledger.

    The content pin includes every before/after string, retained-object digest,
    policy declaration and migration target. A changed ledger needs deliberate
    review and a new version; it is not caller-supplied editing authority.
    """
    raw = files("materials_boundaries").joinpath("data", MIGRATION_RESOURCE).read_bytes()
    if hashlib.sha256(raw).hexdigest() != MIGRATION_SHA256:
        raise ValueError("Unreviewed taxonomy migration ledger")
    ledger = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_keys)
    if (ledger["taxonomy_policy_version"] != TAXONOMY_POLICY_VERSION
            or ledger["migration_id"] != MIGRATION_ID
            or ledger["baseline_commit"] != BASELINE_COMMIT
            or tuple(ledger["categories"]) != PRIMARY_CATEGORIES):
        raise ValueError("Inconsistent taxonomy migration metadata")
    return ledger


def _index(records, label):
    if type(records) is not list:
        raise ValueError("Taxonomy collection must be a list: " + label)
    result = {}
    for record in records:
        if (type(record) is not dict or type(record.get("id")) is not str
                or not record["id"] or record["id"] in result):
            raise ValueError("Invalid or duplicate taxonomy record ID: " + label)
        result[record["id"]] = record
    return result


def _check_snapshot(catalog, pin, phase, name):
    if type(catalog) is not dict or _digest(catalog) != pin[phase + "_canonical_sha256"]:
        raise ValueError("Unreviewed " + phase + " taxonomy snapshot: " + name)


def apply_taxonomy_migration(materials, properties, *, reverse=False):
    """Copy and migrate the exact v0.34 material/property snapshots in memory.

    Returns ``(materials, reference_properties)``. The default requires the
    complete pre-migration snapshots; ``reverse=True`` requires the complete
    migrated snapshots. Partial, mixed, repeated or otherwise edited inputs
    fail closed. Neither inputs nor files are modified, and all unlisted fields
    retain their exact JSON values. This is not a general-purpose migration
    engine or validation/admission route for new material identities.
    """
    if type(reverse) is not bool:
        raise ValueError("reverse must be a boolean")
    ledger = load_taxonomy_migration()
    phase, target = ("after", "before") if reverse else ("before", "after")
    inputs = {"materials": materials, "reference_properties": properties}
    for name, catalog in inputs.items():
        _check_snapshot(catalog, ledger["catalogs"][name], phase, name)
    result = deepcopy(inputs)
    indexes = {(name, collection): _index(catalog[collection], name + "/" + collection)
               for name, catalog in result.items()
               for collection in ledger["catalogs"][name]["collections"]}
    for change in ledger["changes"]:
        record = indexes[change["catalog"], change["collection"]][change["record_id"]]
        if record[change["field"]] != change[phase]:
            raise ValueError("Taxonomy field does not match its reviewed value")
        record[change["field"]] = change[target]
    for name, catalog in result.items():
        _check_snapshot(catalog, ledger["catalogs"][name], target, name)
    return result["materials"], result["reference_properties"]


def _retained_snapshot(catalog, pin, name):
    if type(catalog) is not dict or set(catalog) != set(pin["metadata"]) | set(pin["collections"]):
        raise ValueError("Changed taxonomy catalog envelope: " + name)
    retained = deepcopy(pin["metadata"])
    for field, value in pin["metadata"].items():
        if _canonical(catalog[field]) != _canonical(value):
            raise ValueError("Changed taxonomy catalog metadata: " + name + "/" + field)
    for collection, records in pin["collections"].items():
        rows = catalog[collection]
        index = _index(rows, name + "/" + collection)
        if [row["id"] for row in rows[:len(records)]] != list(records):
            raise ValueError("Retained taxonomy records must remain an exact ordered prefix")
        selected = []
        for identifier, hashes in records.items():
            if identifier not in index or _digest(index[identifier]) != hashes["after_sha256"]:
                raise ValueError("Changed retained taxonomy object: " + identifier)
            selected.append(deepcopy(index[identifier]))
        retained[collection] = selected
    _check_snapshot(retained, pin, "after", name)
    return retained


def verify_taxonomy_migration(materials, properties):
    """Verify all retained baseline objects; permit independent suffix appends.

    This checks the complete post-migration identity, grade, state and property
    objects, including every scientific field and every unchanged record.
    New suffix records are checked for unique nonempty IDs only here. They still
    require normal material-schema, source and scientific-contract validation;
    successful historical preservation is not admission of an appended record.
    """
    ledger = load_taxonomy_migration()
    _retained_snapshot(materials, ledger["catalogs"]["materials"], "materials")
    _retained_snapshot(properties, ledger["catalogs"]["reference_properties"],
                       "reference_properties")
