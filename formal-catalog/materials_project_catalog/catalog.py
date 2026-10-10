"""Frozen formal project admissions, separate from legacy physical/evidence claims.

No registry, provider query, environment variable, or user path grants admission.
Any new tranche or baseline requires a reviewed release and updated byte pins.
"""
from collections import Counter
from copy import deepcopy
from hashlib import sha256
from importlib.resources import files
import json

RESOURCE_SHA256 = {'materials': 'ffd27ae7a927494083cbdcb173847502283f9ff0f69b8b7321abe0b042824dc1', 'reference_properties': '7430901a0f401aca384debb8706a124ac43ad6d043165beff1b8d186641fddef', 'sources': '4240f52ef96bbe34a8a677e2f995296a6c72ac8ab14fc3f8978c043540fcef93', 'formal_computed_review': 'a285523b2b2fdbf0d750ce6ac56e3abfb80d5c42056229a2352b016a787fd875'}
POLICY = {
    "schema": "formal-project-count-policy/1",
    "rule": "legacy-source-qualified-identities-plus-reviewed-composition-buckets",
    "scope": "Frozen legacy catalog and exactly the independently accepted 2026-10-09 v2 tranche",
    "physical_global_uniqueness": "unasserted",
    "equivalence": "Phase, site-order, cross-provider, constituent and formulation equivalence remain unresolved",
    "computed_bucket_rule": "At most one admission per reduced integer composition in this tranche",
    "excluded": "Prior seven-record tranche, provider search results, related groups and calculations",
}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()


def formal_project_catalog():
    """Read only the exact reviewed package; return fully detached rich records."""
    data = {}
    for name, expected in RESOURCE_SHA256.items():
        raw = files("materials_project_catalog" if name == "formal_computed_review" else "materials_boundaries").joinpath("data", name + ".json").read_bytes()
        if sha256(raw).hexdigest() != expected:
            raise ValueError("Formal project admission resource differs: " + name)
        data[name] = json.loads(raw)
    review = data["formal_computed_review"]
    if sha256(canonical(review)).hexdigest() != "8cc9ea2e0bf0006df29ec46c720e871b059d3b7b876976ec94bdd9cdfb6507de":
        raise ValueError("Formal computed review pin differs")
    # Exact release-reviewed resource pins fail closed before any projection.
    records = [{"id": "legacy:" + row["id"], "partition": "legacy-source-qualified",
                "category": row["category"], "name": row["name"],
                "evidence_kind": "retained-per-property", "identity": row}
               for row in data["materials"]["identities"]]
    computed = review["records"]
    buckets = {row["conservative_count_bucket"] for row in computed}
    if len(computed) != 24 or len(buckets) != 24 or any(row["decision"] != "accepted" for row in computed):
        raise ValueError("Formal admission requires exactly the accepted 24 composition buckets")
    records.extend({"id": row["conservative_count_bucket"], "partition": "reviewed-computed",
                    "category": row["primary_category"], "name": row["formula"],
                    "evidence_kind": "computed", "model": row} for row in computed)
    counts = dict(Counter(row["category"] for row in records))
    result = {"schema": "formal-project-catalog/1", "status": "admitted-by-packaged-policy",
              "count_policy": deepcopy(POLICY), "resource_sha256": dict(RESOURCE_SHA256),
              "review_sha256": "8cc9ea2e0bf0006df29ec46c720e871b059d3b7b876976ec94bdd9cdfb6507de",
              "input_file_sha256": review["input_file_sha256"],
              "counts": {"formal_project_admission_count": len(records),
                         "legacy_source_qualified_identity_count": len(data["materials"]["identities"]),
                         "reviewed_computed_composition_count": len(buckets),
                         "categories": counts}, "records": records}
    result["version"] = sha256(canonical(result)).hexdigest()
    return result


def select_formal_catalog(snapshot, *, query=None, partition=None, record_id=None, offset=0, limit=100):
    """Bounded literal selection, preserving qualifiers and provenance in full."""
    if type(offset) is not int or offset < 0 or offset > 10000 or type(limit) is not int or not 1 <= limit <= 100:
        raise ValueError("Use offset 0-10000 and limit 1-100")
    if partition not in (None, "legacy-source-qualified", "reviewed-computed"):
        raise ValueError("Unknown formal partition")
    if query is not None and (not isinstance(query, str) or not query.strip() or len(query) > 256 or len(query.split()) > 16 or any(ord(c) < 32 for c in query)):
        raise ValueError("Use 1-16 literal query terms, at most 256 characters, without controls")
    terms = (query or "").casefold().split()
    selected = [row for row in snapshot["records"] if
                (partition is None or row["partition"] == partition) and
                (record_id is None or row["id"] == record_id) and
                all(term in (row["id"] + " " + row["name"] + " " + row["category"]).casefold() for term in terms)]
    if record_id is not None and not selected:
        from materials_boundaries.catalog import CatalogLookupError
        raise CatalogLookupError("Unknown formal admission ID")
    return {"version": snapshot["version"], "count_policy": deepcopy(snapshot["count_policy"]),
            "matched_count": len(selected), "offset": offset,
            "truncated": offset + limit < len(selected), "records": deepcopy(selected[offset:offset+limit])}
