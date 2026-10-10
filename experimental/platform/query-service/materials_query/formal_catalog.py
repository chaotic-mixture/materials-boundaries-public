"""Read-only formal project view; available only with explicit local-core opt-in."""
from copy import deepcopy
from typing import Literal
from fastapi import HTTPException
from pydantic import Field
from materials_federation.models import Model

class Selection(Model):
    version: str = Field(pattern=r"^[0-9a-f]{64}$")
    query: str | None = Field(default=None, min_length=1, max_length=256)
    partition: Literal["legacy-source-qualified", "reviewed-computed"] | None = None
    record_id: str | None = Field(default=None, min_length=1, max_length=512)
    offset: int = Field(default=0, ge=0, le=10000, strict=True)
    limit: int = Field(default=20, ge=1, le=100, strict=True)


def install_routes(app, *, enabled=False):
    snapshot = None
    error = "not_enabled"
    if enabled:
        try:
            from materials_project_catalog.catalog import formal_project_catalog
            snapshot = formal_project_catalog()
            error = None
        except Exception:
            error = "formal_admission_initialization_failed"

    @app.get("/api/catalog/project/status")
    def status():
        if snapshot is None:
            return {"enabled": False, "reason": error}
        return deepcopy({key: value for key, value in snapshot.items() if key != "records"}) | {
            "enabled": True, "freshness": "process pin; restart after reviewed release",
            "http_admission": False, "automatic_refresh": False}

    @app.post("/api/catalog/project/list")
    def listing(req: Selection):
        if snapshot is None:
            raise HTTPException(503, "Formal project catalog unavailable")
        if req.version != snapshot["version"]:
            raise HTTPException(409, "Formal project version differs")
        from materials_project_catalog.catalog import select_formal_catalog
        from materials_boundaries.catalog import CatalogLookupError
        try:
            return select_formal_catalog(snapshot, **req.model_dump(exclude={"version"}))
        except CatalogLookupError:
            raise HTTPException(404, "Unknown formal admission ID") from None
        except ValueError:
            raise HTTPException(400, "Invalid formal catalog selection") from None
