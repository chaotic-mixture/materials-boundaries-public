"""Optional normalized public-result cache. Explicit TTL; no silent stale fallback."""
from __future__ import annotations
from datetime import timedelta, datetime
from pathlib import Path
import json
import os
import tempfile
from .models import ADAPTER_VERSION, Query, SearchPage, digest, now

class ResultCache:
    def __init__(self, directory: Path, *, ttl_seconds: int = 3600):
        if not 0 < ttl_seconds <= 86400:
            raise ValueError("Cache TTL must be between 1 and 86400 seconds")
        self.directory, self.ttl = directory, timedelta(seconds=ttl_seconds)

    def key(self, provider: str, query: Query, *, provider_version: str | None = None, fixture: bool = False) -> str:
        return digest([provider, query.model_dump(), provider_version, ADAPTER_VERSION, "public-review-only", "fixture" if fixture else "live"])

    def _path(self, key: str) -> Path:
        if len(key) != 64 or any(c not in "0123456789abcdef" for c in key):
            raise ValueError("Invalid cache key")
        return self.directory / (key + ".json")

    def put(self, key: str, page: SearchPage) -> None:
        # The requested provider-version namespace is caller-controlled; acquisition scope is not.
        # Entries also retain a top-level flag, including empty pages.
        target = self._path(key)
        self.directory.mkdir(parents=True, exist_ok=True)
        data = {"page": page.model_dump(mode="json"), "sha256": digest(page.model_dump(mode="json"))}
        fd, name = tempfile.mkstemp(dir=self.directory, prefix=".pending-")
        try:
            with os.fdopen(fd, "w") as f:
                json.dump(data, f, sort_keys=True, allow_nan=False)
            os.replace(name, target)
        finally:
            if os.path.exists(name): os.unlink(name)

    def get(self, key: str, *, at: datetime | None = None, fixture: bool = False) -> SearchPage | None:
        path = self._path(key)
        if not path.exists(): return None
        try:
            data = json.loads(path.read_text())
            if digest(data["page"]) != data["sha256"]:
                raise ValueError("Cache integrity mismatch")
            page = SearchPage.model_validate(data["page"])
            if page.fixture != fixture:
                raise ValueError("Cache acquisition scope mismatch")
            age = (at or now()) - page.retrieved_at
            if age < timedelta(0) or age > self.ttl: return None
            return page.model_copy(update={"cache_status": "cache_hit"})
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("Invalid cache entry; do not use as live evidence") from exc
