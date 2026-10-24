"""Read pinned existing examples and formal admissions for overlap detection only.

An example's local ``accepted`` decision never grants formal project admission.
This module neither writes a catalog nor evaluates scientific/rights approval.
"""
from pathlib import Path
import hashlib
import json

from nomad_batch import ID, composition, digest


ROOT = Path(__file__).resolve().parents[3]
BASELINE_COMMIT = "76cae67a9401b916c1409ad3c2212fa3c103be6f"
LEGACY_COUNT = 1159
PROJECT_TOTAL = 1183
SOURCES = {
    "formal_admitted24": (
        "formal-catalog/materials_project_catalog/data/formal_computed_review.json",
        "a285523b2b2fdbf0d750ce6ac56e3abfb80d5c42056229a2352b016a787fd875", 24),
    "unadmitted_example62": (
        "experimental/platform/examples/reviewed-computed-v2-second/normalized-review.json",
        "f47b5612797661aae68f5d360aeee85c7b6eb3945dad4aeb210b65933bfcc279", 62),
    "legacy_example7": (
        "experimental/platform/examples/reviewed-computed-seed/scoped-review-input.json",
        "298e94d77f5166650f66c17ff83e859c6e654f6739745d779a4461310437bb33", 7),
}
LEGACY = ("materials_boundaries/data/materials.json",
          "ec6a73ea89a267a55eb77d8b189f27deee75b5aaabf24941a9b4da5e2ac85c33")


def _pinned(root, relative, expected):
    raw = (root / relative).read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError("Review boundary bytes differ: " + relative)
    return json.loads(raw)


def load_review_boundary(root=ROOT):
    """Load the versioned overlap boundary; fail closed on changed source bytes."""
    root = Path(root)
    materials, entries, compositions = {}, {}, {}
    source_hashes = {}

    def add(mapping, key, label, *, identifier=False):
        if identifier and (not isinstance(key, str) or not ID.fullmatch(key)):
            raise ValueError("Invalid provider identity in review boundary")
        mapping.setdefault(key, set()).add(label)

    for label, (relative, expected, count) in SOURCES.items():
        source = _pinned(root, relative, expected)
        rows = source["records"]
        if len(rows) != count or len({r["provider_material_id"] for r in rows}) != count:
            raise ValueError("Unexpected review boundary cardinality: " + label)
        source_hashes[relative] = expected
        for row in rows:
            add(materials, row["provider_material_id"], label, identifier=True)
            add(entries, row["provider_entry_id"], label, identifier=True)
            add(compositions, composition(row["formula"])[0], label)
            related = row.get("overlap_relations", {}).get("same_composition_provider_groups", {})
            for material_id, entry_ids in related.items():
                add(materials, material_id, label, identifier=True)
                for entry_id in entry_ids:
                    add(entries, entry_id, label, identifier=True)
    legacy = _pinned(root, *LEGACY)
    if len(legacy["identities"]) != LEGACY_COUNT:
        raise ValueError("Unexpected legacy admission count")
    source_hashes[LEGACY[0]] = LEGACY[1]
    boundary = {
        "schema": "nomad-review-boundary/1",
        "baseline_commit": BASELINE_COMMIT,
        "source_sha256": source_hashes,
        "formal_project_total": PROJECT_TOTAL,
        "formal_legacy_count": LEGACY_COUNT,
        "formal_computed_composition_count": 24,
        "excluded_example_count": 62,
        "legacy_example_count": 7,
        "provider_material_ids": sorted(materials),
        "provider_entry_ids": sorted(entries),
        "materials": {k: sorted(v) for k, v in sorted(materials.items())},
        "entries": {k: sorted(v) for k, v in sorted(entries.items())},
        "compositions": {k: sorted(v) for k, v in sorted(compositions.items())},
        "scope": "Known primary and related provider identities, not global equivalence",
        "composition_policy": "Overlap advisory only; formula never establishes identity",
        "automatic_admission": False,
    }
    boundary["sha256"] = digest(boundary)
    return boundary
