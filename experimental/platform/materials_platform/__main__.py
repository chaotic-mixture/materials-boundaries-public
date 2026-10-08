"""Offline golden demo binding typed discovery to envelope-only lifecycle review."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from materials_federation.normalize import normalize_nomad
from materials_lifecycle import Workflow, Response
from materials_lifecycle.workflow import canonical, immutable, read_json, sha


def run_demo(output):
    root = Path(output)
    raw = (Path(__file__).parent / "fixtures/golden_nomad.json").read_bytes()
    native = json.loads(raw)["data"][0]
    candidate = normalize_nomad(native, retrieved_at=datetime(2026, 1, 1, tzinfo=timezone.utc), fixture=True)
    typed = candidate.model_dump(mode="json")
    typed_bytes = canonical(typed)
    typed_hash = sha(typed_bytes)
    typed_path = immutable(root / "typed_candidates" / (typed_hash + ".json"), typed_bytes)
    workflow = Workflow(root)
    acquisition = workflow.capture({"formula": "Si", "limit": 1}, fetch=lambda *a, **k: Response(raw), fixture=True)
    batch = workflow.stage(acquisition)
    staging = read_json(batch)
    record = staging["records"][0]
    assert record["source_record_id"] == typed["source"]["record_id"]
    assert record["source_raw_sha256"] == sha(raw)
    assert typed["canonical_material_id"] is None and typed["review_status"] == "pending_review"
    binding = {"schema": "typed-lifecycle-binding-1", "fixture": True,
        "typed_candidate_sha256": typed_hash, "typed_candidate_path": str(typed_path.relative_to(root)),
        "raw_sha256": sha(raw), "raw_path": "raw/" + sha(raw),
        "provider_record_id": record["source_record_id"], "batch_sha256": batch.stem,
        "lifecycle_candidate_sha256": sha(canonical(record)),
        "adapter_payload_sha256": typed["source"]["payload_sha256"],
        "lifecycle_payload_sha256": record["source_payload_sha256"],
        "note": "Payload digests use different numeric representations; raw hash and source ID link them. Typed properties are not scientifically approved or admitted."}
    binding_bytes = canonical(binding)
    binding_hash = sha(binding_bytes)
    immutable(root / "bindings" / (binding_hash + ".json"), binding_bytes)
    decision = workflow.review(batch, approved_ids=[record["id"]],
        reviewer="DEMO reviewer; not authenticated", contributor="DEMO synthetic fixture author",
        rationale="Demo-only exact source envelope review; typed binding sha256=" + binding_hash + "; no scientific property acceptance.",
        rights_evidence="https://opensource.org/license/mit", demo=True)
    release = workflow.build(batch, decision, trusted_decision_sha256=decision.stem, version="0.1.0",
        title="Synthetic integration demonstration", creators=["Demonstration fixture author; not a publication"])
    summary = {"schema": "integration-demo-1", "fixture": True,
        "acquisition": str(acquisition.relative_to(root)), "batch": str(batch.relative_to(root)),
        "binding": "bindings/" + binding_hash + ".json", "review": str(decision.relative_to(root)),
        "release": str(release.relative_to(root)), "typed_candidate_state": "pending_review",
        "lifecycle_decision": "approved_for_local_demo_only", "canonical_material_admissions": 0,
        "release_archive_self_contained_raw_replay": False,
        "required_replay_objects": [binding["raw_path"], binding["typed_candidate_path"], "bindings/" + binding_hash + ".json"]}
    immutable(root / "demo-summary.json", canonical(summary))
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="New local output directory; never a production catalog")
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Choose a new output directory; earlier acquisitions remain immutable")
    print(json.dumps(run_demo(args.output), indent=2))

if __name__ == "__main__":
    main()
