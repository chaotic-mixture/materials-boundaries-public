"""Inspectable, append-only local workflow. No authentication or publishing system."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.error import HTTPError
import hashlib
import io
import json
import re
import tarfile
import time
import uuid

class LifecycleError(ValueError):
    pass

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                      allow_nan=False).encode("utf-8")

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def digest(value):
    return sha(canonical(value))

def now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

def strict_load(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise LifecycleError("Duplicate JSON key")
            result[key] = value
        return result
    def bad(value):
        raise LifecycleError("Nonfinite number")
    # Preserve the complete original numeric lexeme, including exponent/precision.
    try:
        return json.loads(raw.decode("utf-8"), object_pairs_hook=pairs,
                          parse_float=str, parse_int=str, parse_constant=bad)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise LifecycleError("Invalid UTF-8 JSON") from exc

def read_json(path):
    return json.loads(Path(path).read_bytes())

def immutable(path, raw):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as stream:
            stream.write(raw)
    except FileExistsError:
        if path.read_bytes() != raw:
            raise LifecycleError("Immutable artifact collision or mutation")
    return path

@dataclass(frozen=True)
class Profile:
    provider: str = "nomad"
    endpoint: str = "https://nomad-lab.eu/prod/v1/api/v1/entries"
    api_version: str = "v1"
    profile_version: str = "1"
    parser_version: str = "1"
    schema_version: str = "candidate-1"
    normalizer_version: str = "1"
    provider_revision: str | None = None
    max_pages: int = 2
    max_records: int = 25
    max_bytes: int = 5_000_000
    timeout_seconds: int = 20
    raw_retention: bool = True
    rights_evidence_url: str | None = None

    def validate(self):
        if self.provider != "nomad" or self.endpoint != Profile().endpoint:
            raise LifecycleError("Unreviewed provider endpoint")
        if not (1 <= self.max_pages <= 10 and 1 <= self.max_records <= 25 and
                1 <= self.max_bytes <= 5_000_000 and 1 <= self.timeout_seconds <= 60):
            raise LifecycleError("Invalid bounded profile")
        if not self.raw_retention:
            raise LifecycleError("Profile does not authorize raw retention")

@dataclass(frozen=True)
class Response:
    body: bytes
    status: int = 200
    headers: dict | None = None

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None

def public_fetch(url, *, timeout, max_bytes):
    # Deliberately no credentials, cookies, redirects or SDK ambient authorization.
    opener = build_opener(NoRedirect)
    request = Request(url, headers={"Accept": "application/json", "Accept-Encoding": "identity"})
    try:
        with opener.open(request, timeout=timeout) as response:
            return Response(response.read(max_bytes + 1), response.status, dict(response.headers))
    except HTTPError as error:
        return Response(b"", error.code, dict(error.headers))

class Workflow:
    def __init__(self, root, profile=None):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.profile = profile or Profile()
        self.profile.validate()

    def put(self, kind, value):
        raw = canonical(value)
        return immutable(self.root / kind / (sha(raw) + ".json"), raw)

    def verify(self, path):
        path = Path(path)
        raw = path.read_bytes()
        if path.stem != sha(raw):
            raise LifecycleError("Artifact hash mismatch")
        return json.loads(raw)

    def capture(self, query, *, fetch=None, fixture=False):
        if set(query) - {"formula", "limit"} or not re.fullmatch(r"[A-Za-z0-9().+\-]{1,100}", query.get("formula", "")):
            raise LifecycleError("Only bounded public formula queries are allowed")
        limit = query.get("limit", self.profile.max_records)
        if type(limit) is not int or not 1 <= limit <= self.profile.max_records:
            raise LifecycleError("Invalid query limit")
        if fetch is not None and fixture is not True:
            raise LifecycleError("Injected transport must be explicitly fixture-labelled")
        fetch = fetch or public_fetch
        start = now()
        pages, seen = [], set()
        cursor, count, total_bytes = None, 0, 0
        status = "bounded"
        try:
            for page_index in range(self.profile.max_pages):
                params = {"owner": "public", "page_size": min(limit - count, 25),
                          "results.material.chemical_formula_reduced": query["formula"]}
                if cursor:
                    params["page_after_value"] = cursor
                url = self.profile.endpoint + "?" + urlencode(params)
                result = fetch(url, timeout=self.profile.timeout_seconds, max_bytes=self.profile.max_bytes - total_bytes)
                headers = {k.lower(): v for k, v in (result.headers or {}).items()}
                if result.status != 200:
                    raise LifecycleError("HTTP status %s; stopped, no automatic retry" % result.status)
                if headers.get("content-encoding", "identity") not in {"identity", ""}:
                    raise LifecycleError("Compressed response unsupported; exact-byte profile requires identity encoding")
                total_bytes += len(result.body)
                if total_bytes > self.profile.max_bytes:
                    raise LifecycleError("Acquisition byte budget exceeded")
                raw_hash = sha(result.body)
                immutable(self.root / "raw" / raw_hash, result.body)
                payload = strict_load(result.body)
                if not isinstance(payload, dict):
                    raise LifecycleError("Response must be a JSON object")
                entries = payload.get("data")
                if not isinstance(entries, list) or len(entries) > limit - count:
                    raise LifecycleError("Schema drift or record budget exceeded")
                pagination = payload.get("pagination", {})
                if not isinstance(pagination, dict):
                    raise LifecycleError("Pagination schema drift")
                nxt = pagination.get("next_page_after_value")
                if nxt is not None and (not isinstance(nxt, str) or len(nxt) > 1024):
                    raise LifecycleError("Invalid cursor")
                pages.append({"index": page_index, "request": params, "status": result.status,
                              "headers": {k: v for k, v in headers.items() if k in {"etag", "last-modified", "content-type", "content-encoding"}},
                              "raw_sha256": raw_hash, "bytes": len(result.body), "capture_level": "http_response_bytes",
                              "selected_payload_sha256": digest(payload), "record_count": len(entries),
                              "provider_total_entries": pagination.get("total"), "next_cursor": nxt})
                count += len(entries)
                if not nxt:
                    status = "complete_for_query"
                    break
                if nxt in seen or not entries:
                    raise LifecycleError("Pagination loop or empty page with cursor")
                seen.add(nxt)
                cursor = nxt
                if count >= limit:
                    break
        except (LifecycleError, OSError, TimeoutError) as error:
            self.put("attempts", {"attempt_id": str(uuid.uuid4()), "started": start, "ended": now(),
                                  "status": "failed", "pages": pages, "reason": str(error)})
            raise
        manifest = {"schema": "acquisition-1", "canonicalization": "mb-json-v1", "acquisition_id": str(uuid.uuid4()),
                    "started": start, "ended": now(), "fixture": fixture, "access": "public", "query": query,
                    "profile": asdict(self.profile), "profile_sha256": digest(asdict(self.profile)),
                    "implementation_sha256": sha(Path(__file__).read_bytes()),
                    "dependency_lock": {"runtime": "Python >=3.11 standard library", "third_party_runtime": []},
                    "provider_revision_reason": None if self.profile.provider_revision else "not supplied",
                    "pages": pages, "pagination_status": status, "captured_entries": count,
                    "scope": "bounded query; provider totals are not material identity counts"}
        return self.put("acquisitions", manifest)

    def _normalize(self, acquisition):
        records = []
        for page in acquisition["pages"]:
            raw = (self.root / "raw" / page["raw_sha256"]).read_bytes()
            if sha(raw) != page["raw_sha256"] or len(raw) != page["bytes"]:
                raise LifecycleError("Raw response mutated")
            entries = strict_load(raw)["data"]
            for native in entries:
                if not isinstance(native, dict):
                    raise LifecycleError("Record schema drift")
                metadata = native.get("metadata", native)
                eid = metadata.get("entry_id")
                if not isinstance(eid, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", eid):
                    raise LifecycleError("Missing or invalid source entry_id")
                results = native.get("results", {})
                if not isinstance(results, dict) or not isinstance(results.get("material", {}), dict):
                    raise LifecycleError("Results schema drift")
                method = results.get("method", {})
                if not isinstance(method, dict):
                    raise LifecycleError("Method schema drift")
                lane = "calculated" if method.get("simulation") else "experimental" if method.get("experimental") else "unknown"
                license_id = metadata.get("license")
                holds = []
                if not isinstance(license_id, str) or license_id.strip().lower() in {"", "unknown", "none", "null", "n/a", "unspecified", "unlicensed"}:
                    holds.append("license_unknown")
                if method.get("simulation") and method.get("experimental"):
                    holds.append("conflicting_evidence_lanes")
                if lane == "unknown":
                    holds.append("evidence_lane_unknown")
                if metadata.get("withdrawn") or metadata.get("retracted"):
                    holds.append("source_withdrawn")
                record = {"id": "nomad:" + eid, "source_record_id": eid,
                          "source_url": "https://nomad-lab.eu/prod/v1/gui/search/entries/entry/id/" + eid,
                          "source_revision": metadata.get("entry_hash") or metadata.get("last_processing_time"),
                          "source_payload_sha256": digest(native), "source_raw_sha256": page["raw_sha256"],
                          "canonical_material_id": None, "lane": lane, "evidence_subtype": method.get("method_name"),
                          "formula": results.get("material", {}).get("chemical_formula_reduced"),
                          "source_license_declaration": license_id, "fixture": acquisition["fixture"],
                          "holds": holds, "native_evidence": native,
                          "normalization": "source-envelope-only; numerical lexemes preserved; no unit conversions or scientific admission"}
                records.append(record)
        ids = [r["id"] for r in records]
        if len(ids) != len(set(ids)):
            raise LifecycleError("Duplicate source identities in acquisition; review revisions separately")
        return sorted(records, key=lambda record: record["id"])

    def stage(self, acquisition_path, *, baseline=None):
        acquisition = self.verify(acquisition_path)
        if acquisition["profile_sha256"] != digest(asdict(self.profile)) or acquisition["implementation_sha256"] != sha(Path(__file__).read_bytes()):
            raise LifecycleError("Profile changed; reacquire under explicit new profile")
        records = self._normalize(acquisition)
        context = {"profile_sha256": acquisition["profile_sha256"], "query": acquisition["query"],
                   "implementation_sha256": acquisition["implementation_sha256"],
                   "raw_hashes": [p["raw_sha256"] for p in acquisition["pages"]], "fixture": acquisition["fixture"],
                   "baseline_sha256": Path(baseline).stem if baseline else None}
        cache_key = digest(context)
        normalized = {"schema": self.profile.schema_version, "context": context, "records": records}
        immutable(self.root / "cache" / (cache_key + ".json"), canonical(normalized))
        old = self.verify(baseline)["records"] if baseline else []
        before, after = {r["id"]: r for r in old}, {r["id"]: r for r in records}
        diff = {"added": sorted(after.keys() - before.keys()), "missing_from_bounded_query": sorted(before.keys() - after.keys()),
                "changed": sorted(key for key in before.keys() & after.keys() if digest(before[key]) != digest(after[key])),
                "record_hash_changes": [{"id": key, "before_sha256": digest(before[key]) if key in before else None,
                    "after_sha256": digest(after[key]) if key in after else None}
                    for key in sorted(before.keys() | after.keys()) if key not in before or key not in after or digest(before[key]) != digest(after[key])],
                "analysis_impact": "Requires human review; not inferred automatically",
                "note": "Missing from a bounded query is not a retraction. Source revisions do not create material identities."}
        queue = [{"id": r["id"], "candidate_sha256": digest(r), "source_sha256": r["source_payload_sha256"],
                  "status": "held" if r["holds"] else "pending_review", "reasons": r["holds"]} for r in records]
        batch = {**normalized, "cache_key": cache_key, "diff": diff, "review_queue": queue,
                 "counts": {"source_records": len(records), "material_identities": 0, "production_admitted": 0},
                 "acquisition_content": {"profile_sha256": acquisition["profile_sha256"], "query": acquisition["query"],
                    "pages": acquisition["pages"], "pagination_status": acquisition["pagination_status"]}}
        path = self.put("batches", batch)
        self.put("lineage", {"batch_sha256": path.stem, "acquisition_sha256": Path(acquisition_path).stem})
        return path

    def current_status(self, record_id):
        events = [self.verify(path) for path in (self.root / "status_events").glob("*.json")]
        relevant = [event for event in events if event["record_id"] == record_id]
        return "withdrawn" if any(event["kind"] == "withdrawn" for event in relevant) else "superseded" if any(event["kind"] == "superseded" for event in relevant) else "held_for_correction" if relevant else "current"

    def review(self, batch_path, *, approved_ids, reviewer, contributor, rationale, rights_evidence,
               demo=False, rejected_ids=()):
        batch = self.verify(batch_path)
        if not reviewer.strip() or reviewer == contributor or not rationale.strip():
            raise LifecycleError("Independent reviewer reference and rationale required")
        if not rights_evidence.startswith("https://"):
            raise LifecycleError("Explicit rights evidence URL required")
        requested = list(approved_ids)
        if not requested or len(requested) != len(set(requested)) or set(requested) & set(rejected_ids):
            raise LifecycleError("Approval must enumerate an exact nonduplicate subset")
        by_id = {r["id"]: r for r in batch["records"]}
        if not set(requested + list(rejected_ids)) <= by_id.keys():
            raise LifecycleError("Unknown review ID")
        approved = []
        for rid in sorted(requested):
            record = by_id[rid]
            if self.current_status(rid) != "current":
                raise LifecycleError("Record withdrawn or superseded; new use blocked")
            if record["holds"]:
                raise LifecycleError("Held candidate cannot be approved: " + rid)
            if record["fixture"] and not demo:
                raise LifecycleError("Fixture cannot enter scientific release")
            approved.append({"id": rid, "candidate_sha256": digest(record), "source_sha256": record["source_payload_sha256"],
                             "source_raw_sha256": record["source_raw_sha256"]})
        decision = {"schema": "review-1", "policy": "local-explicit-review-1", "batch_sha256": Path(batch_path).stem,
                    "context": batch["context"], "approved": approved, "rejected_ids": sorted(rejected_ids),
                    "reviewer": reviewer, "contributor": contributor, "rationale": rationale,
                    "rights_evidence": rights_evidence, "scientific_review": "explicit-local-attestation",
                    "rights_review": "explicit-local-attestation", "demo": demo,
                    "authentication": "not authenticated; caller must verify identity and authority out of band"}
        return self.put("reviews", decision)

    def build(self, batch_path, decision_path, *, trusted_decision_sha256, version, title, creators):
        if not re.fullmatch(r"\d+\.\d+\.\d+", version) or not title or not creators:
            raise LifecycleError("Explicit dataset SemVer, title and verified creator list required")
        batch, decision = self.verify(batch_path), self.verify(decision_path)
        if Path(decision_path).stem != trusted_decision_sha256 or decision["batch_sha256"] != Path(batch_path).stem or decision["context"] != batch["context"]:
            raise LifecycleError("Untrusted, stale or mutated approval")
        if batch["context"]["profile_sha256"] != digest(asdict(self.profile)) or batch["context"]["implementation_sha256"] != sha(Path(__file__).read_bytes()):
            raise LifecycleError("Stale parser/schema/provider profile")
        # Raw bytes are checked again, even if cached candidate JSON remains unchanged.
        for raw_hash in batch["context"]["raw_hashes"]:
            if sha((self.root / "raw" / raw_hash).read_bytes()) != raw_hash:
                raise LifecycleError("Raw capture mutated after review")
        by_id = {r["id"]: r for r in batch["records"]}
        selected = []
        for approval in decision["approved"]:
            record = by_id.get(approval["id"])
            if not record or digest(record) != approval["candidate_sha256"] or record["source_payload_sha256"] != approval["source_sha256"] or record["holds"]:
                raise LifecycleError("Candidate no longer matches approval")
            if record["fixture"] and not decision["demo"]:
                raise LifecycleError("Synthetic scientific release forbidden")
            if self.current_status(record["id"]) != "current":
                raise LifecycleError("Record withdrawn or superseded after review")
            selected.append(record)
        if not selected or len({r["id"] for r in selected}) != len(selected):
            raise LifecycleError("Empty or duplicate release subset")
        selected.sort(key=lambda r: r["id"])
        # Local release does not include raw/native full data outside selected records.
        counts = {"source_records": len(selected), "material_identities": 0, "grades": 0, "states": 0,
                  "properties": 0, "observations": 0, "computed_entries": sum(r["lane"] == "calculated" for r in selected),
                  "held_candidates": sum(bool(r["holds"]) for r in batch["records"]),
                  "rejected_candidates": len(decision["rejected_ids"]), "production_admitted": 0}
        citation = {"type": "dataset", "title": title, "version": version, "creators": creators,
                    "dataset_version_doi": None, "dataset_concept_doi": None, "software_doi": None,
                    "doi_status": "unregistered", "publication_status": "local_demo" if decision["demo"] else "local_release_candidate"}
        files = {"records.json": canonical(selected), "review.json": canonical(decision),
                 "provenance.json": canonical(batch["acquisition_content"]),
                 "rights.json": canonical({"review_evidence": decision["rights_evidence"], "source_declarations":
                     [{"id": r["id"], "license": r["source_license_declaration"], "source": r["source_url"]} for r in selected]}),
                 "citation.json": canonical(citation), "CHANGELOG.json": canonical(batch["diff"])}
        cff = ['cff-version: 1.2.0', 'type: dataset', 'message: "Cite this exact local snapshot and its underlying sources."',
               'title: ' + json.dumps(title), 'version: ' + json.dumps(version), 'authors:']
        cff.extend('  - name: ' + json.dumps(name) for name in creators)
        files["CITATION.cff"] = ("\n".join(cff) + "\n").encode()
        inventory = [{"path": key, "bytes": len(value), "sha256": sha(value)} for key, value in sorted(files.items())]
        manifest = {"schema": "dataset-release-1", "dataset_version": version, "title": title,
                    "snapshot_sha256": digest(inventory), "files": inventory, "counts": counts,
                    "schema_version": self.profile.schema_version, "software_version": "0.1.0",
                    "baseline_batch_sha256": batch["context"]["baseline_sha256"], "parent_snapshot": None,
                    "implementation_sha256": batch["context"]["implementation_sha256"], "batch_sha256": Path(batch_path).stem,
                    "decision_sha256": trusted_decision_sha256, "approved": decision["approved"], "citation": citation,
                    "gates": {"integrity": "pass", "exact_subset": "pass", "explicit_local_review": "pass",
                              "reviewer_authentication": "not_run", "production_catalog_regression": "not_run"},
                    "limitations": ["Local candidate only; not a production admission or authenticated institutional approval.",
                                    "Source envelopes retain numeric lexical strings; no scientific property conversion implemented.",
                                    "Fixture data is demonstration-only." if decision["demo"] else "Bounded acquisition; not exhaustive."]}
        files["manifest.json"] = canonical(manifest)
        files["SHA256SUMS"] = "".join(sha(data) + "  " + name + "\n" for name, data in sorted(files.items())).encode()
        archive = io.BytesIO()
        with tarfile.open(fileobj=archive, mode="w", format=tarfile.USTAR_FORMAT) as tar:
            for name, data in sorted(files.items()):
                info = tarfile.TarInfo(name)
                info.size, info.mtime, info.mode = len(data), 0, 0o644
                info.uid = info.gid = 0
                tar.addfile(info, io.BytesIO(data))
        output = self.root / "releases" / version
        # Version reservation prevents silent version reuse with different bytes.
        immutable(output / "manifest.json", files["manifest.json"])
        for name, data in files.items():
            immutable(output / name, data)
        immutable(output / "dataset.tar", archive.getvalue())
        return output

    def status_event(self, release_path, *, record_id, kind, reason, source_url, superseded_by=None):
        if kind not in {"withdrawn", "superseded", "erratum"} or not reason or not source_url.startswith("https://"):
            raise LifecycleError("Explicit correction kind, source and reason required")
        if kind == "superseded" and not superseded_by:
            raise LifecycleError("Supersession requires replacement reference")
        release = read_json(Path(release_path) / "manifest.json")
        if record_id not in {r["id"] for r in release["approved"]}:
            raise LifecycleError("Correction must target released record")
        return self.put("status_events", {"snapshot_sha256": release["snapshot_sha256"], "record_id": record_id,
                       "kind": kind, "reason": reason, "source_url": source_url, "superseded_by": superseded_by,
                       "recorded_at": now(), "policy": "detached status event; historical release bytes unchanged"})
