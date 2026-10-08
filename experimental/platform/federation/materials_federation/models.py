"""Versioned normalized candidates, deliberately separate from catalog admission."""
from __future__ import annotations
from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Literal, Protocol
from pydantic import BaseModel, ConfigDict, Field, model_validator

ADAPTER_VERSION = "0.1.0"

def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode()).hexdigest()

def now() -> datetime:
    return datetime.now(timezone.utc)

class Model(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

class Query(Model):
    formula: str | None = Field(default=None, min_length=1, max_length=120)
    limit: int = Field(default=5, ge=1, le=25, strict=True)

    @model_validator(mode="after")
    def bounded_scope(self):
        if self.formula is None:
            raise ValueError("A formula is required for the bounded prototype query")
        if any(c in self.formula for c in '*?[]'):
            raise ValueError("Wildcard formulas are not supported")
        return self

class SourceRef(Model):
    provider: Literal["materials_project", "nomad"]
    record_id: str = Field(min_length=1)
    endpoint: str
    source_url: str
    provider_version: str | None = None
    record_updated: str | None = None
    payload_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    retrieved_at: datetime
    adapter_version: Literal["0.1.0"] = ADAPTER_VERSION
    license_identifier: str | None = None
    license_evidence_url: str | None = None
    license_review: Literal["unreviewed", "source_declared"] = "unreviewed"
    fixture: bool = False

class Provenance(Model):
    source: SourceRef
    field_path: str
    task_ids: tuple[str, ...] = ()
    method: dict[str, Any] = Field(default_factory=dict)
    note: str | None = None

class PropertyEvidence(Model):
    quantity: str
    value: float = Field(strict=True)
    unit: str | None
    evidence_kind: Literal["computed", "experimental", "unknown"]
    provenance: Provenance
    uncertainty: float | None = None

class Candidate(Model):
    schema_version: Literal["0.1.0"] = "0.1.0"
    snapshot_id: str
    canonical_material_id: None = None
    source: SourceRef
    formula: str
    composition: dict[str, float] | None = None
    structure: dict[str, Any] | None = None
    structure_format: Literal["pymatgen", "nomad_results", "absent"] = "absent"
    state: dict[str, Any] = Field(default_factory=dict)
    identity_evidence: dict[str, Provenance]
    properties: tuple[PropertyEvidence, ...] = ()
    external_references: dict[str, Any] = Field(default_factory=dict)
    review_status: Literal["pending_review"] = "pending_review"
    quota_credit: Literal[0] = 0
    limitations: tuple[str, ...] = (
        "Provider entry is not a canonical project material or a qualified production identity.",
        "Formula, provider material IDs and structure similarity do not establish equivalence.",
        "Unknown state, processing and uncertainty remain unknown.",
    )

class SearchPage(Model):
    provider: Literal["materials_project", "nomad"]
    query: Query
    candidates: tuple[Candidate, ...]
    retrieved_at: datetime
    possibly_truncated: bool
    next_cursor: str | None = None
    cache_status: Literal["fresh", "cache_hit"] = "fresh"
    fixture: bool = False
    matching_provider_entries: int | None = Field(default=None, ge=0, strict=True)
    warnings: tuple[str, ...] = ()

    @model_validator(mode="after")
    def consistent_acquisition(self):
        if len(self.candidates) > self.query.limit:
            raise ValueError("Page exceeds query limit")
        if any(c.source.fixture != self.fixture for c in self.candidates):
            raise ValueError("Page mixes fixture and live acquisition")
        return self

class Provider(Protocol):
    provider: str
    def search(self, query: Query) -> SearchPage: ...
