"""Conservative relationship hints and review packages, never admission tokens."""
from __future__ import annotations
from typing import Literal
from .models import Candidate, Model, digest

class MatchHint(Model):
    relation: Literal["same_provider_snapshot", "provider_revision", "candidate_matches", "unresolved"]
    status: Literal["candidate", "supported"]
    explanation: str
    may_merge: Literal[False] = False

def compare(left: Candidate, right: Candidate) -> MatchHint:
    a, b = left.source, right.source
    if (a.provider, a.record_id) == (b.provider, b.record_id):
        exact = left.snapshot_id == right.snapshot_id
        return MatchHint(relation="same_provider_snapshot" if exact else "provider_revision",
            status="supported", explanation="Same provider record snapshot." if exact else
            "Same provider record, different version or selected payload; not a distinct material count.")
    if left.formula == right.formula:
        return MatchHint(relation="candidate_matches", status="candidate",
            explanation="Matching provider formula only; phase, structure, state and source lineage unresolved.")
    return MatchHint(relation="unresolved", status="candidate",
        explanation="Different formula strings do not prove different compositions; no identity inference performed.")

def review_package(candidates: list[Candidate]) -> dict:
    """Content hash supports audit, not authorization. Deliberately not legacy admit_batch input."""
    records = [x.model_dump(mode="json") for x in candidates]
    return {"schema_version": "federated_review/0.1.0", "candidates": records,
        "package_sha256": digest(records), "admission_status": "not_admitted",
        "quota_credit": 0, "review_requirements": [
            "Resolve source-qualified canonical material identity and all provider revisions.",
            "Review phases, structures, states and imported duplicate lineage independently.",
            "Verify each field's source location, calculation/measurement method and units.",
            "Review source-specific reuse terms, license evidence and attribution.",
            "Route predictions and observations to distinct reviewed scientific contracts.",
            "Assign application roles only with independent evidence; no formula-based role inference.",
            "Use a separately trusted legacy admission or new scientific-family workflow after review."]}
