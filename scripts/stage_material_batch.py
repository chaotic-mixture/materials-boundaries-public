#!/usr/bin/env python3
"""Stage a source-separated audit package without changing runtime catalogs.

Only checked-in adapters may establish source_supported status. Unknown adapters
remain proposed. This script has no admission, approval, download, dynamic module
loading, or runtime-promotion option. Review its emitted manifest before using an
explicit authorized admission workflow.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from materials_boundaries.bulk_ingestion import IngestionError, canonical_json_bytes, stage_batch
from materials_boundaries.validation import load_json


def _reviewed_profiles():
    # This list is intentionally code-controlled. Never resolve a Python module
    # or a callback named in candidate JSON or an untrusted command-line file.
    from materials_boundaries.wood_bulk_adapter import reviewed_profiles
    return reviewed_profiles()


def write_immutable_package(path, package):
    """Create an artifact atomically; identical reruns are byte-idempotent."""
    path = Path(path)
    data = canonical_json_bytes(package)
    if path.exists():
        if not path.is_symlink() and path.is_file() and path.read_bytes() == data:
            return False
        raise IngestionError("output already exists with different content; select a new output path")
    if not path.parent.is_dir():
        raise IngestionError("output parent directory does not exist")
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".material-stage-", delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        # Hard linking creates the destination exclusively and atomically. It
        # cannot replace a competing write or accidentally clobber a catalog.
        os.link(temporary, path)
    except FileExistsError as exc:
        raise IngestionError("output appeared during write; no existing artifact was overwritten") from exc
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return True


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("batch", type=Path, help="source-separated candidate batch JSON")
    parser.add_argument("--baseline", type=Path, required=True,
                        help="reviewed baseline JSON array of identity_key/primary_class rows (use [] for an explicitly empty baseline)")
    parser.add_argument("--output", type=Path, required=True,
                        help="new immutable stage package path; same-byte reruns are allowed")
    args = parser.parse_args(argv)
    try:
        if args.output.resolve() in (args.batch.resolve(), args.baseline.resolve()):
            raise IngestionError("output must be separate from batch and baseline inputs")
        batch = load_json(args.batch)
        baseline = load_json(args.baseline)
        if not isinstance(baseline, list):
            raise IngestionError("baseline file must contain a JSON array")
        package = stage_batch(batch, baseline=baseline, profiles=_reviewed_profiles())
        created = write_immutable_package(args.output, package)
    except (OSError, ValueError) as exc:
        parser.exit(2, f"staging failed: {exc}\n")
    counts = package["manifest"]["counts"]["by_status"]
    print(("Created" if created else "Unchanged") + f" review-only stage: {args.output}")
    print("Review manifest SHA-256: " + package["review_manifest_sha256"])
    print("; ".join(f"{status}={counts[status]}" for status in ("proposed", "held", "source_supported", "admitted")))
    print("No runtime catalogs changed. Source support is not admission or scientific certification.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
