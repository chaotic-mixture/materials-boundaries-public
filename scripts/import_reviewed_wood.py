#!/usr/bin/env python3
"""Verify and stage reviewed-v2 wood; export approved append tables separately.

Never overwrites the production catalog. Import is deliberately split into a
source verification/staging call and a later digest-bound approval call.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from materials_boundaries.bulk_ingestion import admit_batch, canonical_json_bytes, stage_batch
from materials_boundaries.wood_bulk_adapter import (
    baseline_rows, build_wood_batch, materialize_wood_records, reviewed_profiles,
)


def _write(path, value):
    payload = canonical_json_bytes(value)
    if path.exists():
        if path.read_bytes() != payload:
            raise ValueError("refusing to overwrite different output bytes: " + str(path))
        return
    path.write_bytes(payload)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dossier-dir", type=Path, required=True)
    parser.add_argument("--review-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--baseline-materials", type=Path,
                        default=Path(__file__).resolve().parents[1] / "materials_boundaries/data/materials.json")
    parser.add_argument("--approval", type=Path, help="Separate generic approval JSON naming exact identity keys")
    parser.add_argument("--expected-review-digest", help="Digest from the independent staging review, never inferred from approval JSON")
    args = parser.parse_args(argv)
    if bool(args.approval) != bool(args.expected_review_digest):
        parser.error("--approval and --expected-review-digest must be supplied together")
    production = (Path(__file__).resolve().parents[1] / "materials_boundaries/data").resolve()
    output = args.output_dir.resolve()
    if output == production or production in output.parents:
        parser.error("output must be separate from production catalog data")
    try:
        batch = build_wood_batch(args.dossier_dir, args.review_dir)
        baseline = baseline_rows(json.loads(args.baseline_materials.read_text(encoding="utf-8")))
        staged = stage_batch(batch, baseline=baseline, profiles=reviewed_profiles())
        output.mkdir(parents=True, exist_ok=True)
        _write(output / "wood-batch.json", batch)
        _write(output / "wood-staged.json", staged)
        result = {"review_manifest_sha256": staged["review_manifest_sha256"], "counts": staged["manifest"]["counts"]}
        if args.approval:
            admitted = admit_batch(staged, json.loads(args.approval.read_text(encoding="utf-8")),
                                   expected_review_digest=args.expected_review_digest,
                                   profiles=reviewed_profiles())
            tables = materialize_wood_records(admitted, expected_review_digest=args.expected_review_digest)
            _write(output / "wood-admitted.json", admitted)
            for name, table in tables.items():
                _write(output / ("wood-append-" + name + ".json"), table)
            result["admission_counts"] = admitted["admission_counts"]
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    except (ValueError, OSError) as exc:
        parser.exit(2, "reviewed wood import blocked: " + str(exc) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
