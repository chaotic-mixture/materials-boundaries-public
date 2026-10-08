"""Explicit fixture-only local demonstration; reviewer labels are not people."""
from pathlib import Path
from materials_lifecycle import Workflow, Response
from materials_lifecycle.workflow import read_json

base = Path(__file__).parent
raw = b'{"data":[' + (base / "fixtures/nomad_archive_projected.json").read_bytes() + b'],"pagination":{"total":1}}'
(base / "fixtures/nomad_response.json").write_bytes(raw)
workflow = Workflow(base / "demo-store")
acquisition = workflow.capture({"formula": "CaFe2Re", "limit": 1}, fetch=lambda *a, **k: Response(raw), fixture=True)
batch = workflow.stage(acquisition)
rid = read_json(batch)["records"][0]["id"]
decision = workflow.review(batch, approved_ids=[rid], reviewer="DEMO reviewer (not authenticated)",
    contributor="DEMO fixture contributor", rationale="Offline demo of exact content binding only; not scientific approval",
    rights_evidence="https://creativecommons.org/licenses/by/4.0/", demo=True)
release = workflow.build(batch, decision, trusted_decision_sha256=decision.stem, version="1.0.0",
    title="NOMAD lifecycle fixture demonstration", creators=["Prototype demonstration (not a publication)"])
print("acquisition:", acquisition)
print("batch:", batch)
print("decision:", decision)
print("local demo:", release)
