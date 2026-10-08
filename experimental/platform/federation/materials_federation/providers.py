"""Bounded read-only adapters. No credentials, implicit authentication or admission."""
from __future__ import annotations
from typing import Any
import json
import re
import httpx
from .models import Candidate, Query, SearchPage, now
from .normalize import NOMAD_ENDPOINT, normalize_mp, normalize_nomad

class ProviderError(RuntimeError):
    pass

class AuthenticationRequired(ProviderError):
    pass

class MaterialsProjectAdapter:
    provider = "materials_project"
    FIELDS = (
        "material_id", "formula_pretty", "composition_reduced", "structure", "symmetry",
        "density", "band_gap", "formation_energy_per_atom", "energy_above_hull",
        "bulk_modulus", "shear_modulus", "theoretical", "database_IDs", "origins",
        "last_updated", "builder_meta", "warnings", "deprecated", "is_metal", "is_stable",
    )

    def __init__(self, authorized_client: Any = None, *, fixture: bool = False):
        # Do not instantiate MPRester here: its credential discovery is deliberately outside scope.
        self.client = authorized_client
        self.fixture = fixture

    def search(self, query: Query) -> SearchPage:
        if self.client is None:
            raise AuthenticationRequired("MP requires a separately authorized client; no API key was read or requested")
        timestamp = now()
        rester = self.client.materials.summary
        available = set(rester.available_fields)
        required = {"material_id", "formula_pretty", "builder_meta", "origins", "deprecated"}
        if not required <= available:
            raise ProviderError("MP schema changed: required summary fields are unavailable")
        fields = [f for f in self.FIELDS if f in available]
        try:
            version_before = getattr(self.client, "db_version", None)
            docs = rester.search(formula=query.formula, fields=fields, all_fields=False,
                deprecated=False, include_gnome=False, num_chunks=1, chunk_size=query.limit)
            if len(docs) > query.limit:
                raise ProviderError("MP violated bounded response size")
            version = getattr(self.client, "db_version", None)
            if version_before != version:
                raise ProviderError("MP release changed during query; retry later as a new snapshot")
            candidates = tuple(normalize_mp(d, database_version=str(version) if version else None,
                               retrieved_at=timestamp, fixture=self.fixture) for d in docs)
        except ProviderError:
            raise
        except Exception:
            # Client exceptions may include request headers; never propagate those into review artifacts.
            raise ProviderError("MP query or normalization failed; inspect a credential-redacted diagnostic locally") from None
        return SearchPage(provider=self.provider, query=query, candidates=candidates, fixture=self.fixture,
            retrieved_at=timestamp, possibly_truncated=len(candidates) == query.limit,
            warnings=("One bounded page only; this is not an exhaustive provider search.",
                "Before/after client release values agree; fresh server release consistency is not proven.",
                "License declarations are unreviewed for redistribution; GNoME excluded.") +
                (("Some optional fields are unavailable in this API schema.",) if len(fields) != len(self.FIELDS) else ()))

class NomadAdapter:
    provider = "nomad"
    # No client injection: an arbitrary configured client could carry ambient auth/cookies.
    # HTTPX MockTransport is supported for deterministic local fixture verification.
    def __init__(self, *, transport: httpx.BaseTransport | None = None, fixture: bool = False):
        self.transport = transport
        self.fixture = fixture

    def _request(self, method: str, url: str, **kwargs) -> dict:
        with httpx.Client(transport=self.transport, timeout=20.0, follow_redirects=False,
                          trust_env=True) as client:
            with client.stream(method, url, **kwargs) as response:
                if response.status_code in (401, 403):
                    raise ProviderError("NOMAD public read denied; do not bypass access controls")
                if response.status_code == 429:
                    raise ProviderError("NOMAD rate limit: stop and respect Retry-After before a future request")
                response.raise_for_status()
                raw = bytearray()
                for chunk in response.iter_bytes():
                    raw.extend(chunk)
                    if len(raw) > 5_000_000:
                        raise ProviderError("NOMAD response exceeds 5 MB prototype bound")
                return json.loads(raw)

    def search(self, query: Query) -> SearchPage:
        timestamp = now()
        params = [("owner", "public"), ("page_size", str(query.limit)),
                  ("results.material.chemical_formula_reduced", query.formula)]
        params.extend(("include", field) for field in (
            "entry_id", "upload_id", "results.material.*", "results.method.*",
            "results.properties.structures.*", "datasets.*", "references",
            "last_processing_time", "nomad_version", "nomad_commit"))
        try:
            payload = self._request("GET", NOMAD_ENDPOINT, params=params)
            entries = payload["data"]
            if len(entries) > query.limit:
                raise ProviderError("NOMAD violated bounded response size")
            candidates = tuple(normalize_nomad(d, retrieved_at=timestamp,
                                               fixture=self.fixture) for d in entries)
            page = payload.get("pagination") or {}
            cursor = page.get("next_page_after_value")
        except ProviderError:
            raise
        except (httpx.HTTPError, ValueError, KeyError, TypeError):
            raise ProviderError("NOMAD query or normalization failed; no partial results admitted") from None
        return SearchPage(provider=self.provider, query=query, candidates=candidates, fixture=self.fixture,
            retrieved_at=timestamp, next_cursor=cursor,
            matching_provider_entries=page.get("total"),
            possibly_truncated=bool(cursor) or len(candidates) == query.limit,
            warnings=("One bounded public page only; cursor retained but not automatically followed.",
                "Search metadata can omit full structures; archive enrichment is a separate read.",
                "Source-declared license does not establish complete attribution or redistribution review."))

    def enrich_archive(self, candidate: Candidate) -> Candidate:
        """Explicit one-entry read. Search snapshots remain intact and independently traceable."""
        if candidate.source.provider != "nomad" or not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", candidate.source.record_id):
            raise ValueError("Expected a NOMAD candidate with a valid entry ID")
        if candidate.source.fixture != self.fixture:
            raise ValueError("Cannot mix fixture and live provenance")
        eid = candidate.source.record_id
        required = {"metadata": {k: "*" for k in (
            "entry_id", "upload_id", "entry_hash", "license", "last_processing_time",
            "nomad_version", "nomad_commit", "external_db", "datasets", "references")},
            "results": {"material": "*", "method": "*", "properties": {
                "structures": {"structure_original": "*"}}}}
        try:
            payload = self._request("POST", NOMAD_ENDPOINT + "/" + eid + "/archive/query",
                                    json={"required": required})
            archive = payload["data"]["archive"]
            if archive["metadata"]["entry_id"] != eid:
                raise ProviderError("Archive entry ID does not match requested candidate")
            return normalize_nomad(archive, fixture=self.fixture)
        except ProviderError:
            raise
        except (httpx.HTTPError, ValueError, KeyError, TypeError):
            raise ProviderError("NOMAD archive enrichment failed; original candidate remains unchanged") from None
