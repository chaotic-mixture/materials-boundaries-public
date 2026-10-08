#!/usr/bin/env python3
"""Offline synthetic-only scale measurements; never production quota evidence."""
from __future__ import annotations

import argparse
import gc
import hashlib
from pathlib import Path
import platform
import sys
from time import perf_counter
import tracemalloc

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from materials_boundaries.bulk_ingestion import (
    PRIMARY_CLASSES, SourceProfile, admit_batch, canonical_json_bytes,
    registry_digest, stage_batch,
)
from scripts.stage_material_batch import write_immutable_package


def synthetic_batch(count):
    """Generate test-only identities algorithmically, not factual material data."""
    evidence_bytes = b"Synthetic benchmark fixture; no material facts.\n"
    registry = {
        "releases": [{"release_id": "benchmark_release", "source_id": "benchmark_source",
                      "version": "synthetic-1", "immutable_id": "urn:benchmark-only:synthetic-1",
                      "citation": "Synthetic software benchmark fixture; no material facts", "license_id": "benchmark_license"}],
        "files": [{"file_id": "benchmark_file", "release_id": "benchmark_release", "file_name": "synthetic.txt",
                   "sha256": hashlib.sha256(evidence_bytes).hexdigest(), "byte_length": len(evidence_bytes),
                   "download_url": "https://example.invalid/benchmark-only-synthetic.txt"}],
        "licenses": [{"license_id": "benchmark_license", "identifier": "CC0-1.0",
                      "grant_url": "https://example.invalid/benchmark-only-license", "grant_version": "synthetic-1",
                      "grant_text": "Synthetic benchmark test data only", "attribution": "Synthetic benchmark fixture author",
                      "scope": "Generated fictional records only", "restrictions": [], "inspected_by": "Benchmark fixture author",
                      "inspected_on": "2026-10-07", "evidence_sha256": hashlib.sha256(b"synthetic license fixture").hexdigest(), "attested": True}],
    }
    materials, observations = [], []
    for i in range(count):
        key = f"benchmark-only:synthetic:{i:06d}"
        evidence = [{"file_id": "benchmark_file", "locator": f"generated synthetic row {i}",
                     "record_id": f"synthetic:{i}", "fields": ["fictional_density"]}]
        materials.append({"identity_key": key, "primary_class": PRIMARY_CLASSES[i % len(PRIMARY_CLASSES)],
                          "name": f"Fictional benchmark material {i}", "aliases": [f"Synthetic alias {i}"],
                          "taxon": None, "evidence": evidence, "metadata": {"benchmark_only": True}})
        observations.append({"observation_id": f"benchmark-only:observation:{i:06d}", "identity_key": key,
                             "quantity": "mass_density", "value": "1000.00", "unit": "kg/m^3", "state_key": None,
                             "evidence_kind": "synthetic_benchmark_only", "evidence": evidence,
                             "metadata": {"benchmark_only": True, "original_numeric_string": "1000.00"}})
    return {"schema_version": "1.0.0", "batch_id": f"benchmark-only-synthetic-{count}",
            "adapter_id": "benchmark_only_synthetic", "registry": registry,
            "materials": materials, "observations": observations, "exclusions": []}


def _validate_synthetic(observation, material, registry):
    if not material["identity_key"].startswith("benchmark-only:synthetic:"):
        raise ValueError("benchmark identity namespace required")
    if material["metadata"] != {"benchmark_only": True} or observation["metadata"].get("benchmark_only") is not True:
        raise ValueError("synthetic benchmark marker required")
    if (observation["quantity"], observation["unit"]) != ("mass_density", "kg/m^3"):
        raise ValueError("unsupported synthetic benchmark property")


def benchmark(count):
    batch = synthetic_batch(count)
    profile = SourceProfile(batch["adapter_id"], "synthetic-1", registry_digest(batch["registry"]),
                            frozenset({"CC0-1.0"}), _validate_synthetic)
    gc.collect()
    tracemalloc.start()
    started = perf_counter()
    staged = stage_batch(batch, baseline=[], profiles=[profile])
    stage_seconds = perf_counter() - started
    stage_peak = tracemalloc.get_traced_memory()[1]
    stage_bytes = len(canonical_json_bytes(staged))
    tracemalloc.reset_peak()
    reviewed = {"decision": "approve", "reviewer": "Synthetic benchmark test harness, not production approval",
                "review_manifest_sha256": staged["review_manifest_sha256"],
                "approved_identity_keys": [row["identity_key"] for row in batch["materials"]]}
    started = perf_counter()
    admitted = admit_batch(staged, reviewed, expected_review_digest=staged["review_manifest_sha256"], profiles=[profile])
    admission_seconds = perf_counter() - started
    admission_peak = tracemalloc.get_traced_memory()[1]
    admission_bytes = len(canonical_json_bytes(admitted))
    tracemalloc.stop()
    assert admitted["admission_counts"]["admitted_unique_keys_with_numeric_property"] == count
    assert staged["manifest"]["counts"]["by_status"]["admitted"] == 0
    return {"synthetic_identity_count": count, "stage_seconds": f"{stage_seconds:.6f}",
            "admission_replay_seconds": f"{admission_seconds:.6f}", "stage_peak_traced_bytes": stage_peak,
            "admission_peak_traced_bytes": admission_peak, "stage_serialized_bytes": stage_bytes,
            "admission_serialized_bytes": admission_bytes, "review_manifest_sha256": staged["review_manifest_sha256"],
            "stage_counts": staged["manifest"]["counts"], "synthetic_admission_counts": admitted["admission_counts"]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--counts", type=int, nargs="+", default=[1000, 3793, 10000])
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    if any(count < 1 for count in args.counts):
        parser.error("counts must be positive")
    report = {"benchmark_only": True, "production_materials_added": 0,
              "scope": "Generated fictional identities test generic staging and admission replay scaling; none are source-researched or runtime material coverage",
              "timing_note": "Wall-clock includes tracemalloc instrumentation; admission peak includes the retained input and stage artifacts",
              "python": platform.python_version(), "results": []}
    for count in args.counts:
        result = benchmark(count)
        report["results"].append(result)
        print(f"Synthetic {count}: stage {result['stage_seconds']}s; admission replay {result['admission_replay_seconds']}s", flush=True)
    write_immutable_package(args.output, report)
    print(f"Wrote synthetic-only evidence: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
