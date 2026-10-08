"""Deterministic, offline staging for reviewed source-specific material adapters.

This module does not fetch research, infer identity, establish legal rights, write
runtime catalogs, or turn a candidate's review claims into permission. Source
profiles are registered by trusted Python callers, never loaded from candidate
JSON. Each profile pins the complete release/file/license registry and provides
a reviewed semantic validator. Metadata and original numeric strings are kept
verbatim. Generic numeric values use bounded fixed-point decimal strings.

A stage package is a self-contained review artifact, not an admitted catalog.
``admit_batch`` replays staging and requires an independently supplied trusted
manifest digest. That digest is an explicit application trust boundary, not a
digital signature: callers must obtain it from their authorized review workflow,
never copy it automatically from an untrusted approval or candidate file.
"""
from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
from dataclasses import dataclass
from decimal import Decimal
import hashlib
import json
import re
from typing import Callable, Iterable, Mapping
from urllib.parse import urlsplit

SCHEMA_VERSION = "1.0.0"
PRIMARY_CLASSES = ("metal", "inorganic", "polymer", "composite", "natural")
STATUSES = ("proposed", "held", "source_supported", "admitted")
_DECIMAL = re.compile(r"-?(?:0|[1-9][0-9]{0,23})(?:\.[0-9]{1,24})?\Z")
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_CONTROL = re.compile(r"[\x00-\x1f\x7f-\x9f\ud800-\udfff]")
Validator = Callable[[dict, dict, dict], None]


class IngestionError(ValueError):
    """Malformed package, failed validation or a rejected admission gate."""


@dataclass(frozen=True)
class SourceProfile:
    """Trusted adapter registration, separate from source-authored JSON.

    ``registry_sha256`` is ``registry_digest(reviewed_registry)``. A change to
    an immutable release, file hash, grant evidence, or attribution breaks this
    pin. Increment ``version`` whenever the semantic contract changes. The
    validator must be deterministic, side-effect-free, and raise ValueError
    when the observation or associated material fails the reviewed contract.
    """

    adapter_id: str
    version: str
    registry_sha256: str
    allowed_licenses: frozenset[str]
    validate_observation: Validator

    def __post_init__(self):
        _text(self.adapter_id, "adapter_id")
        _text(self.version, "profile.version")
        _hash(self.registry_sha256, "profile.registry_sha256")
        if not isinstance(self.allowed_licenses, frozenset) or not self.allowed_licenses:
            raise IngestionError("profile.allowed_licenses must be a nonempty frozenset")
        for identifier in self.allowed_licenses:
            _text(identifier, "profile.allowed_licenses")
        if not callable(self.validate_observation):
            raise IngestionError("profile requires a registered semantic validator")

    def descriptor(self):
        return {"adapter_id": self.adapter_id, "version": self.version,
                "registry_sha256": self.registry_sha256,
                "allowed_licenses": sorted(self.allowed_licenses)}


def canonical_json_bytes(value) -> bytes:
    """Stable UTF-8 JSON; reject non-JSON values and nonfinite numbers."""
    _json_value(value)
    return (json.dumps(value, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")


def sha256_json(value) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _json_value(value):
    if value is None or type(value) in (str, int, bool):
        if isinstance(value, str) and any(0xD800 <= ord(c) <= 0xDFFF for c in value):
            raise IngestionError("JSON contains an invalid Unicode surrogate")
        return
    if isinstance(value, list):
        for item in value:
            _json_value(item)
        return
    if isinstance(value, dict) and all(isinstance(key, str) for key in value):
        for key, item in value.items():
            _json_value(key)
            _json_value(item)
        return
    # Source numbers are strings; structural counts use integers. Reject floats
    # even when finite rather than silently losing decimal information.
    raise IngestionError("package must contain JSON objects, arrays, strings, integers, booleans or null; numeric measurements must be strings")


def _object(value, required, optional=(), where="record"):
    if not isinstance(value, dict):
        raise IngestionError(f"{where}: expected an object")
    missing = set(required) - value.keys()
    extra = value.keys() - set(required) - set(optional)
    if missing or extra:
        raise IngestionError(f"{where}: missing fields {sorted(missing)}; unsupported fields {sorted(extra)}")


def _text(value, where):
    if not isinstance(value, str) or not value.strip() or _CONTROL.search(value):
        raise IngestionError(f"{where}: expected nonempty text without control characters")


def _texts(value, where, minimum=0):
    if not isinstance(value, list) or len(value) < minimum:
        raise IngestionError(f"{where}: expected an array with at least {minimum} entries")
    for item in value:
        _text(item, where)


def _hash(value, where):
    if not isinstance(value, str) or not _SHA256.fullmatch(value):
        raise IngestionError(f"{where}: expected a lowercase SHA-256 digest")


def _url(value, where):
    _text(value, where)
    parsed = urlsplit(value)
    if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password or any(c.isspace() for c in value):
        raise IngestionError(f"{where}: expected an HTTPS URL without credentials")


def _integer(value, where, minimum=1):
    if type(value) is not int or value < minimum:
        raise IngestionError(f"{where}: expected an integer >= {minimum}")


def validate_decimal(value, where="value") -> None:
    """Require finite fixed-point text, preserving all source precision."""
    if not isinstance(value, str) or not _DECIMAL.fullmatch(value) or not Decimal(value).is_finite():
        raise IngestionError(f"{where}: expected a finite fixed-point decimal string (at most 24 digits on each side)")
    if value.startswith("-") and Decimal(value) == 0:
        raise IngestionError(f"{where}: signed zero is not a canonical number")


def _sorted(items):
    return sorted(deepcopy(items), key=canonical_json_bytes)


def canonical_registry(registry):
    """Sort only registry tables; retain ordered source metadata verbatim."""
    _object(registry, ("releases", "files", "licenses"), where="registry")
    result = deepcopy(registry)
    for table in result:
        if not isinstance(result[table], list):
            raise IngestionError(f"registry.{table}: expected an array")
        result[table] = _sorted(result[table])
    return result


def registry_digest(registry) -> str:
    return sha256_json(canonical_registry(registry))


def _unique_registry(rows, key, table):
    result = {}
    for row in rows:
        if not isinstance(row, dict) or key not in row:
            raise IngestionError(f"registry.{table}: missing {key}")
        _text(row[key], key)
        if row[key] in result:
            raise IngestionError(f"registry.{table}: duplicate {key} {row[key]}")
        result[row[key]] = row
    if not result:
        raise IngestionError(f"registry.{table}: at least one row required")
    return result


def validate_registry(registry, profile=None):
    """Validate lineage and rights attestations; this is not legal verification."""
    registry = canonical_registry(registry)
    releases = _unique_registry(registry["releases"], "release_id", "releases")
    files = _unique_registry(registry["files"], "file_id", "files")
    licenses = _unique_registry(registry["licenses"], "license_id", "licenses")
    for row in licenses.values():
        _object(row, ("license_id", "identifier", "grant_url", "grant_version", "grant_text", "attribution", "scope", "restrictions", "inspected_by", "inspected_on", "evidence_sha256", "attested"), where="license")
        for field in ("license_id", "identifier", "grant_version", "grant_text", "attribution", "scope", "inspected_by", "inspected_on"):
            _text(row[field], "license." + field)
        _url(row["grant_url"], "license.grant_url")
        _hash(row["evidence_sha256"], "license.evidence_sha256")
        _texts(row["restrictions"], "license.restrictions")
        if row["attested"] is not True:
            raise IngestionError("license grant is not attested")
        if profile and row["identifier"] not in profile.allowed_licenses:
            raise IngestionError("license is not permitted by the registered source profile: " + row["identifier"])
    for row in releases.values():
        _object(row, ("release_id", "source_id", "version", "immutable_id", "citation", "license_id"), where="release")
        for field, value in row.items():
            _text(value, "release." + field)
        if row["license_id"] not in licenses:
            raise IngestionError("release references an unknown license")
    for row in files.values():
        _object(row, ("file_id", "release_id", "file_name", "sha256", "byte_length", "download_url"), where="file")
        for field in ("file_id", "release_id", "file_name"):
            _text(row[field], "file." + field)
        _hash(row["sha256"], "file.sha256")
        _integer(row["byte_length"], "file.byte_length", 0)
        _url(row["download_url"], "file.download_url")
        if row["release_id"] not in releases:
            raise IngestionError("file references an unknown release")
    if profile and registry_digest(registry) != profile.registry_sha256:
        raise IngestionError("source registry differs from the registered immutable registry digest")
    return {"releases": releases, "files": files, "licenses": licenses}



def verify_source_files(registry: dict, source_bytes: Mapping[str, bytes]) -> dict:
    """Verify complete cached source bytes against the immutable file registry.

    The adapter owns acquisition and explicit decoding; this helper performs no
    I/O, decoding, replacement, or network access. Grant evidence hashes are
    separate registry attestations, not a claim that grant assets are licensed
    for redistribution. Return a stable verification receipt for adapter audits.
    """
    graph = validate_registry(registry)
    if set(source_bytes) != set(graph["files"]):
        raise IngestionError("source bytes must cover exactly the registry file IDs")
    verified = []
    for file_id, row in sorted(graph["files"].items()):
        data = source_bytes[file_id]
        if not isinstance(data, bytes):
            raise IngestionError("source cache must preserve original bytes")
        digest = hashlib.sha256(data).hexdigest()
        if len(data) != row["byte_length"] or digest != row["sha256"]:
            raise IngestionError("source file checksum or byte length mismatch: " + file_id)
        verified.append({"file_id": file_id, "sha256": digest, "byte_length": len(data)})
    return {"registry_sha256": registry_digest(registry), "verified_files": verified}


def _evidence(items, registry):
    if not isinstance(items, list) or not items:
        raise IngestionError("evidence: at least one source locator required")
    for row in items:
        _object(row, ("file_id", "locator", "record_id", "fields"),
                ("accession", "row_number", "line_start", "line_end", "citation"), "evidence")
        for field in ("file_id", "locator", "record_id"):
            _text(row[field], "evidence." + field)
        _texts(row["fields"], "evidence.fields", 1)
        if row["file_id"] not in registry["files"]:
            raise IngestionError("evidence references an unknown immutable source file")
        for field in ("accession", "citation"):
            if field in row and row[field] is not None:
                _text(row[field], "evidence." + field)
        for field in ("row_number", "line_start", "line_end"):
            if field in row:
                _integer(row[field], "evidence." + field)
        if ("line_start" in row) != ("line_end" in row):
            raise IngestionError("physical line ranges require both start and end")
        if "line_start" in row and row["line_start"] > row["line_end"]:
            raise IngestionError("physical line range is reversed")


def _material(row, registry):
    _object(row, ("identity_key", "primary_class", "name", "aliases", "taxon", "evidence", "metadata"), ("status",), "material")
    for field in ("identity_key", "primary_class", "name"):
        _text(row[field], "material." + field)
    if row["primary_class"] not in PRIMARY_CLASSES:
        raise IngestionError("unknown primary_class")
    _texts(row["aliases"], "material.aliases")
    if row["taxon"] is not None and not isinstance(row["taxon"], dict):
        raise IngestionError("taxon must be null or an adapter-specific object")
    if not isinstance(row["metadata"], dict):
        raise IngestionError("material.metadata must be an object")
    if row.get("status", "proposed") != "proposed":
        raise IngestionError("candidate status cannot assert source support or admission")
    _evidence(row["evidence"], registry)


def _observation(row, registry):
    _object(row, ("observation_id", "identity_key", "quantity", "value", "unit", "evidence_kind", "state_key", "evidence", "metadata"), ("status",), "observation")
    for field in ("observation_id", "identity_key", "quantity", "unit", "evidence_kind"):
        _text(row[field], "observation." + field)
    validate_decimal(row["value"])
    if row["state_key"] is not None:
        _text(row["state_key"], "observation.state_key")
    if not isinstance(row["metadata"], dict):
        raise IngestionError("observation.metadata must be an object")
    if row.get("status", "proposed") != "proposed":
        raise IngestionError("candidate status cannot assert source support or admission")
    _evidence(row["evidence"], registry)


def _canonical_record(row):
    result = deepcopy(row)
    if not isinstance(result, dict):
        return result
    for field in ("aliases", "evidence"):
        if isinstance(result.get(field), list):
            result[field] = _sorted(result[field])
    evidence_rows = result.get("evidence", [])
    for evidence in evidence_rows if isinstance(evidence_rows, list) else []:
        if isinstance(evidence, dict) and isinstance(evidence.get("fields"), list):
            evidence["fields"] = sorted(evidence["fields"], key=canonical_json_bytes)
    if isinstance(result.get("evidence"), list):
        result["evidence"] = _sorted(result["evidence"])
    return result


def _canonical_batch(batch):
    _json_value(batch)
    _object(batch, ("schema_version", "batch_id", "adapter_id", "registry", "materials", "observations", "exclusions"), where="batch")
    if batch["schema_version"] != SCHEMA_VERSION:
        raise IngestionError("unsupported staging schema_version")
    _text(batch["batch_id"], "batch_id")
    _text(batch["adapter_id"], "adapter_id")
    result = deepcopy(batch)
    result["registry"] = canonical_registry(result["registry"])
    for table in ("materials", "observations", "exclusions"):
        if not isinstance(result[table], list):
            raise IngestionError(f"{table}: expected an array")
        result[table] = _sorted([_canonical_record(row) for row in result[table]])
    return result


def _baseline(rows):
    result = {}
    for row in rows:
        _object(row, ("identity_key", "primary_class"), where="baseline")
        _text(row["identity_key"], "baseline.identity_key")
        if row["primary_class"] not in PRIMARY_CLASSES:
            raise IngestionError("baseline has an unknown primary class")
        previous = result.get(row["identity_key"])
        if previous is not None and previous != row:
            raise IngestionError("conflicting baseline identity_key: " + row["identity_key"])
        result[row["identity_key"]] = deepcopy(row)
    return sorted(result.values(), key=lambda row: row["identity_key"])


def _deduplicate(items):
    return [row for _, row in sorted({canonical_json_bytes(row): row for row in items}.items())]


def stage_batch(batch: dict, *, baseline: Iterable[dict] = (),
                profiles: Iterable[SourceProfile] = ()) -> dict:
    """Create a byte-stable audit package. Never change runtime data or admit.

    Malformed top-level envelopes/baselines raise IngestionError. Bad rows and
    bad registry attestations produce machine-readable quarantine records.
    All candidates sharing an inconsistent identity or evidence claim are held;
    input order never selects a winner. The package retains original input rows.
    """
    batch = _canonical_batch(batch)
    baseline = _baseline(baseline)
    baseline_by_key = {row["identity_key"]: row for row in baseline}
    registered = {}
    for item in profiles:
        if not isinstance(item, SourceProfile) or item.adapter_id in registered:
            raise IngestionError("profiles must contain unique SourceProfile registrations")
        registered[item.adapter_id] = item
    profile = registered.get(batch["adapter_id"])
    quarantine = []
    material_reasons = defaultdict(set)
    observation_reasons = defaultdict(set)

    def hold(table, row, code, detail):
        key = row.get("identity_key") if isinstance(row, dict) else None
        oid = row.get("observation_id") if isinstance(row, dict) else None
        key = key if isinstance(key, str) else None
        oid = oid if isinstance(oid, str) else None
        if key is not None:
            material_reasons[key].add(code)
        if oid is not None:
            observation_reasons[oid].add(code)
        quarantine.append({"table": table, "identity_key": key,
                           "observation_id": oid, "reason": code,
                           "detail": detail, "input_sha256": sha256_json(row)})

    registry_error = None
    try:
        registry = validate_registry(batch["registry"], profile)
    except ValueError as exc:
        registry_error = str(exc)
        registry = {"releases": {}, "files": {}, "licenses": {}}
        hold("registry", batch["registry"], "invalid_registry", registry_error)
    materials = defaultdict(list)
    for row in batch["materials"]:
        try:
            _material(row, registry)
        except ValueError as exc:
            hold("materials", row, "invalid_material", str(exc))
        if isinstance(row, dict) and isinstance(row.get("identity_key"), str):
            materials[row["identity_key"]].append(row)
    material_rows = {}
    for key, rows in sorted(materials.items()):
        definitions = {sha256_json({field: row.get(field) for field in ("primary_class", "name", "taxon", "metadata")}): row for row in rows}
        if len(definitions) > 1:
            for row in rows:
                hold("materials", row, "conflicting_identity", "all rows sharing this identity_key disagree on canonical identity facts")
        # A conflicting group gets no representative. Its complete originals
        # remain in input; only a neutral held summary is emitted below.
        if len(definitions) == 1:
            merged = deepcopy(rows[0])
            if all(isinstance(row.get("aliases"), list) for row in rows):
                merged["aliases"] = _deduplicate([alias for row in rows for alias in row["aliases"]])
            if all(isinstance(row.get("evidence"), list) for row in rows):
                merged["evidence"] = _deduplicate([e for row in rows for e in row["evidence"]])
            material_rows[key] = merged
        if key in baseline_by_key:
            code = "baseline_duplicate" if all(row.get("primary_class") == baseline_by_key[key]["primary_class"] for row in rows) else "baseline_identity_conflict"
            for row in rows:
                hold("materials", row, code, "canonical identity_key already exists in the baseline")
        if registry_error:
            material_reasons[key].add("invalid_registry")

    observations = defaultdict(list)
    for row in batch["observations"]:
        try:
            _observation(row, registry)
        except ValueError as exc:
            hold("observations", row, "invalid_observation", str(exc))
        if isinstance(row, dict) and isinstance(row.get("observation_id"), str):
            observations[row["observation_id"]].append(row)
    observation_rows = {}
    facts = defaultdict(list)
    for oid, rows in sorted(observations.items()):
        distinct = _deduplicate(rows)
        if len(distinct) != 1:
            for row in rows:
                hold("observations", row, "conflicting_observation_id", "all rows sharing an observation_id must be identical")
            continue
        row = distinct[0]
        observation_rows[oid] = row
        key = row.get("identity_key")
        if not isinstance(key, str) or key not in materials:
            hold("observations", row, "unknown_identity", "observation does not resolve to a batch identity_key")
            continue
        fact_key = sha256_json({field: row.get(field) for field in ("identity_key", "quantity", "state_key", "evidence")})
        facts[fact_key].append(row)
    for rows in facts.values():
        claims = {sha256_json({field: row.get(field) for field in ("value", "unit", "evidence_kind", "metadata")}) for row in rows}
        if len(claims) > 1:
            for row in rows:
                hold("observations", row, "conflicting_evidence_claim", "same source evidence and quantity have incompatible numeric claims")

    for row in batch["exclusions"]:
        _object(row, ("reason", "detail"), ("identity_key", "observation_id"), "exclusion")
        _text(row["reason"], "exclusion.reason")
        _text(row["detail"], "exclusion.detail")
        if not re.fullmatch(r"[a-z][a-z0-9_]*", row["reason"]):
            raise IngestionError("exclusion.reason must be a machine-readable snake_case code")
        if not set(row) & {"identity_key", "observation_id"}:
            raise IngestionError("exclusion must identify a material or observation")
        target_keys = set()
        if "identity_key" in row:
            _text(row["identity_key"], "exclusion.identity_key")
            if row["identity_key"] not in materials:
                raise IngestionError("exclusion references an unknown identity_key")
            target_keys.add(row["identity_key"])
        if "observation_id" in row:
            _text(row["observation_id"], "exclusion.observation_id")
            if row["observation_id"] not in observations:
                raise IngestionError("exclusion references an unknown observation_id")
            for item in observations[row["observation_id"]]:
                if isinstance(item.get("identity_key"), str):
                    target_keys.add(item["identity_key"])
            if "identity_key" in row and target_keys != {row["identity_key"]}:
                raise IngestionError("exclusion identity and observation targets disagree")
        for key in target_keys:
            item = dict(row, identity_key=key)
            hold("exclusions", item, "excluded_" + row["reason"], row["detail"])

    for oid, row in observation_rows.items():
        key = row.get("identity_key")
        if not isinstance(key, str) or key not in material_rows or observation_reasons[oid] or material_reasons[key]:
            continue
        if profile:
            try:
                # The callback sees detached data and cannot change the audit
                # package by mutation. It must signal rejection with ValueError.
                profile.validate_observation(deepcopy(row), deepcopy(material_rows[key]), deepcopy(batch["registry"]))
            except ValueError as exc:
                hold("observations", row, "semantic_validation_failed", str(exc))
    valid_by_key = defaultdict(list)
    staged_observations = []
    for oid, row in sorted(observation_rows.items()):
        key = row.get("identity_key")
        reasons = sorted(observation_reasons[oid] | (material_reasons[key] if isinstance(key, str) else set()))
        status = "held" if reasons else "source_supported" if profile else "proposed"
        result = deepcopy(row)
        result.update(status=status, reasons=reasons)
        staged_observations.append(result)
        if status == "source_supported":
            valid_by_key[key].append(oid)
    staged_materials = []
    for key in sorted(materials):
        reasons = sorted(material_reasons[key])
        if not reasons and profile and not valid_by_key[key]:
            reasons = ["no_traceable_numeric_property"]
            for row in materials[key]:
                hold("materials", row, reasons[0], "at least one validated numeric observation is required")
        result = deepcopy(material_rows.get(key, {"identity_key": key}))
        result.update(status="held" if reasons else "source_supported" if profile else "proposed",
                      reasons=reasons, observation_ids=sorted(valid_by_key[key]))
        staged_materials.append(result)
    tables = {"materials": staged_materials, "observations": staged_observations,
              "quarantine": _deduplicate(quarantine)}
    counts = coverage(tables)
    manifest = {"schema_version": SCHEMA_VERSION, "batch_id": batch["batch_id"],
                "input_sha256": sha256_json(batch), "baseline_sha256": sha256_json(baseline),
                "registry_sha256": registry_digest(batch["registry"]),
                "profile": profile.descriptor() if profile else None,
                "tables_sha256": sha256_json(tables), "counts": counts}
    return {"schema_version": SCHEMA_VERSION, "input": batch, "baseline": baseline,
            **tables, "manifest": manifest, "review_manifest_sha256": sha256_json(manifest)}


def coverage(package: Mapping) -> dict:
    """Count unique material keys with numeric evidence, never aliases/states."""
    counts = {status: 0 for status in STATUSES}
    admitted_by_class = {category: 0 for category in PRIMARY_CLASSES}
    observations = {row["observation_id"]: row for row in package["observations"]}
    seen = set()
    for row in package["materials"]:
        key = row["identity_key"]
        if key in seen:
            raise IngestionError("coverage requires unique canonical identity keys")
        seen.add(key)
        status = row["status"]
        if status not in STATUSES:
            raise IngestionError("unknown coverage status")
        if status in ("source_supported", "admitted"):
            matched = [observations[oid] for oid in row["observation_ids"] if oid in observations and observations[oid]["identity_key"] == key and observations[oid]["status"] in ("source_supported", "admitted")]
            if not matched:
                raise IngestionError("supported/admitted coverage requires traceable numeric evidence")
            for prop in matched:
                validate_decimal(prop["value"])
                if not prop["evidence"]:
                    raise IngestionError("supported/admitted coverage requires source evidence")
        counts[status] += 1
        if status == "admitted":
            admitted_by_class[row["primary_class"]] += 1
    return {"unique_identities": len(seen), "by_status": counts,
            "admitted_unique_keys_with_numeric_property": counts["admitted"],
            "admitted_by_primary_class": admitted_by_class}


def admit_batch(staged: dict, approval: dict, *, expected_review_digest: str,
                profiles: Iterable[SourceProfile]) -> dict:
    """Replay and explicitly admit only the reviewed keys; never write catalogs.

    ``expected_review_digest`` must come from trusted reviewer configuration or
    an explicit reviewed invocation, independently of candidate/approval JSON.
    An approval is a decision record, not proof of identity or authorization.
    """
    _hash(expected_review_digest, "expected_review_digest")
    _object(staged, ("schema_version", "input", "baseline", "materials", "observations", "quarantine", "manifest", "review_manifest_sha256"), where="staged package")
    replay = stage_batch(staged["input"], baseline=staged["baseline"], profiles=profiles)
    if canonical_json_bytes(replay) != canonical_json_bytes(staged):
        raise IngestionError("staged package differs from deterministic replay")
    if replay["review_manifest_sha256"] != expected_review_digest:
        raise IngestionError("review manifest does not match the independently approved digest")
    _object(approval, ("decision", "reviewer", "review_manifest_sha256", "approved_identity_keys"), where="approval")
    if approval["decision"] != "approve":
        raise IngestionError("explicit approval decision required")
    _text(approval["reviewer"], "approval.reviewer")
    if approval["review_manifest_sha256"] != expected_review_digest:
        raise IngestionError("approval is not bound to the reviewed manifest")
    _texts(approval["approved_identity_keys"], "approved_identity_keys", 1)
    keys = set(approval["approved_identity_keys"])
    if len(keys) != len(approval["approved_identity_keys"]):
        raise IngestionError("approval repeats a canonical identity key")
    supported = {row["identity_key"] for row in replay["materials"] if row["status"] == "source_supported"}
    if not keys <= supported:
        raise IngestionError("approval contains unknown, held, or unsupported material identities")
    result = deepcopy(replay)
    for row in result["materials"]:
        if row["identity_key"] in keys:
            row["status"] = "admitted"
    for row in result["observations"]:
        if row["identity_key"] in keys and row["status"] == "source_supported":
            row["status"] = "admitted"
    result["admission"] = {"decision": "approve", "reviewer": approval["reviewer"],
                           "review_manifest_sha256": expected_review_digest,
                           "approved_identity_keys": sorted(keys)}
    result["admission_counts"] = coverage(result)
    result["admission_sha256"] = sha256_json({"admission": result["admission"],
                                             "materials": result["materials"],
                                             "observations": result["observations"]})
    return result
