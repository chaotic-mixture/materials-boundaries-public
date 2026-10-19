#!/usr/bin/env python3
"""Fail closed on changes outside the one polymer/composite experiment.

The fixed ancestor and exact paths are an execution-scope guard, not scientific
approval. No directory globs, workflow fallback or automatic baseline updates.
"""
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BASE_COMMIT = "a592c89ede0dcced22579e56fc68b6fab4c55f49"
BRANCH_REF = "refs/heads/experiment/polymer-composites-20261019"
FULL_JOB_IF = "    if: ${{ github.event_name != 'push' || github.ref != '" + BRANCH_REF + "' }}\n"

# Only individually approved files belong here. Adding a directory is invalid.
APPROVED_FILES = frozenset({
    ".github/workflows/ci.yml",
    "scripts/check_polymer_composites_scope.py",
    "scripts/run_polymer_composites_ci.py",
    "materials_boundaries/data/materials.json",
    "materials_boundaries/data/reference_properties.json",
    "README.md",
    "tests/test_polymer_formulations_increment.py",
    "tests/test_polymer_composites_increment.py",
    "tests/test_polymer_composites_source_facts.py",
    "tests/material_bulk_preservation.py",
    "tests/presentation_fast_path_preservation.py",
    "tests/test_presentation_fast_path_preservation.py",
    "tests/material_class_counts_preservation.py",
    "tests/fixtures/material_class_counts_updates_20261019.json",
    "tests/test_material_class_counts_preservation.py",
    "experimental/material-batches/20261019-polymer-composites-incremental/integration.json",
    "experimental/material-batches/20261019-polymer-composites-incremental/README.md",
    "experimental/material-batches/20261019-polymer-composites-incremental/VALIDATION.md",
    "experimental/material-batches/20261019-pbs-lignin45/materials.append.json",
    "experimental/material-batches/20261019-pbs-lignin45/reference-properties.append.json",
    "experimental/material-batches/20261019-pbs-lignin45/sources.reused.json",
    "experimental/material-batches/20261019-pbs-lignin45/review.json",
    "experimental/material-batches/20261019-pbs-lignin45/README.md",
    "experimental/material-batches/20261019-epdm-pcm-hostatron/materials.append.json",
    "experimental/material-batches/20261019-epdm-pcm-hostatron/reference-properties.append.json",
    "experimental/material-batches/20261019-epdm-pcm-hostatron/sources.reused.json",
    "experimental/material-batches/20261019-epdm-pcm-hostatron/review.json",
    "experimental/material-batches/20261019-epdm-pcm-hostatron/README.md",
    "tests/fixtures/pbs_lignin45_source_transcription_20261019.json",
    "tests/fixtures/epdm_pcm_hostatron_source_transcription_20261019.json",
    "experimental/platform/query-service/materials_query/computed_registry.py",
    "experimental/platform/query-service/materials_query/pins/legacy_baseline.json",
    "experimental/platform/query-service/catalog-tests/test_catalog_baseline.py",
    "experimental/platform/query-service/catalog-tests/test_baseline_compatibility.py",
    "experimental/platform/query-service/catalog-tests/test_local_catalog.py",
    "experimental/platform/query-service/catalog-tests/test_family_relationships.py",
    "experimental/platform/query-service/catalog-tests/test_formal_project_catalog.py",
    "experimental/platform/query-service/catalog-tests/test_computed_recovery.py",
    "experimental/platform/query-service/catalog-tests/test_computed_v2_tranche.py",
    "experimental/platform/query-service/catalog-tests/test_computed_v2_second_tranche.py",
    "experimental/platform/query-service/catalog-tests/test_combined_admission_boundary.py",
    "experimental/platform/query-service/README.md",
    "experimental/platform/relationships/test_hbn_relationship_projection.py",
    "formal-catalog/materials_project_catalog/catalog.py",
    "formal-catalog/tests/test_formal_project_core.py",
    "formal-catalog/README.md",
    "docs/FORMAL_PROJECT_CATALOG.md",
    "experimental/platform/ingestion/nomad_review_boundary.py",
    "experimental/platform/ingestion/test_review_boundary.py",
    "experimental/platform/ingestion/test_nomad_incremental.py",
    "experimental/platform/ingestion/test_incremental_independent.py",
    "experimental/platform/ingestion/test_nomad_evidence_compare.py",
    "experimental/platform/ingestion/test_formal_overlap_audit.py",
    "experimental/platform/ingestion/test_formal_review_gaps.py",
    "experimental/platform/ingestion/README.md",
    "experimental/platform/ingestion/INCREMENTAL.md",
    "experimental/platform/ingestion/FORMAL_OVERLAP_AUDIT.md",
    "experimental/platform/ingestion/FORMAL_REVIEW_GAPS.md",
})

TARGETED_JOB = """  polymer-composites-targeted:
    if: ${{ github.event_name == 'push' && github.ref == 'refs/heads/experiment/polymer-composites-20261019' }}
    runs-on: ${{ matrix.os }}
    timeout-minutes: 60
    strategy:
      fail-fast: false
      matrix:
        include:
          - os: ubuntu-latest
            python-version: '3.11'
          - os: windows-latest
            python-version: '3.12'
    env:
      PYTHONUTF8: '1'
      PYTHONDONTWRITEBYTECODE: '1'
    steps:
      - run: git config --global core.autocrlf false
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - run: python scripts/run_polymer_composites_ci.py --validate-scope
      - run: python -m pip install --no-deps --only-binary=:all: -r experimental/platform/ci/build-requirements.txt
      - run: python -m pip install --no-build-isolation -e '.[dev]'
      - run: python scripts/run_polymer_composites_ci.py --test
      - run: python scripts/validate_catalogs.py
      - run: python -m pip wheel --no-deps --no-build-isolation --wheel-dir dist . formal-catalog experimental/platform/federation experimental/platform/query-service experimental/platform/lifecycle experimental/platform
      - run: python -m pip download --no-deps --only-binary=:all: --dest dist/dependencies -r experimental/platform/requirements-lock.txt -r experimental/platform/ci/projection-requirements.txt
      - run: python scripts/run_polymer_composites_ci.py --wheel-dir dist --dependency-dir dist/dependencies
"""


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def expected_workflow(baseline):
    """Preserve the complete old workflow except the two complementary guards."""
    for job in ("unit-and-schema", "windows-composite"):
        marker = "  " + job + ":\n"
        require(baseline.count(marker) == 1, "Unexpected frozen full-job structure: " + job)
        baseline = baseline.replace(marker, marker + FULL_JOB_IF, 1)
    return baseline + TARGETED_JOB


def changed_paths(raw):
    tokens = raw.decode("utf-8").split("\0")
    if tokens[-1] == "":
        tokens.pop()
    require(len(tokens) % 2 == 0, "Malformed NUL-delimited Git diff")
    changes = []
    for status, name in zip(tokens[::2], tokens[1::2]):
        require(status in {"A", "M"}, "Only additions/modifications are approved: " + status + " " + name)
        changes.append(name)
    return changes


def validate_scope():
    head = git("rev-parse", "HEAD").decode().strip()
    subprocess.run(["git", "merge-base", "--is-ancestor", BASE_COMMIT, head], cwd=ROOT, check=True)
    if os.environ.get("GITHUB_ACTIONS") == "true":
        require(os.environ.get("GITHUB_EVENT_NAME") == "push", "Scoped CI requires a push event")
        require(os.environ.get("GITHUB_REF") == BRANCH_REF, "Scoped CI requires its exact experiment branch")
        require(os.environ.get("GITHUB_SHA") == head, "Checkout HEAD differs from the pushed GITHUB_SHA")
        require(not git("status", "--porcelain", "--untracked-files=normal"), "Scoped CI checkout must be clean before execution")
    names = set(changed_paths(git("diff", "--name-status", "--no-renames", "-z", BASE_COMMIT, "HEAD", "--")))
    names.update(changed_paths(git("diff", "--name-status", "--no-renames", "-z", "HEAD", "--")))
    names.update(name for name in git("ls-files", "--others", "--exclude-standard", "-z").decode("utf-8").split("\0") if name)
    unexpected = sorted(names - APPROVED_FILES)
    require(not unexpected, "Changes exceed the approved experiment scope: " + ", ".join(unexpected))
    for name in names:
        path = ROOT / name
        require(not path.is_symlink() and path.is_file() and path.resolve().is_relative_to(ROOT),
                "Approved path must remain a regular repository file: " + name)
    baseline = git("show", BASE_COMMIT + ":.github/workflows/ci.yml").decode("utf-8")
    actual = (ROOT / ".github/workflows/ci.yml").read_bytes().decode("utf-8")
    require(actual == expected_workflow(baseline),
            "Workflow differs from the frozen two full jobs plus the exact scoped job")
    report = {"base_commit": BASE_COMMIT, "head": head, "branch_ref": BRANCH_REF,
              "changed_files": sorted(names), "original_full_jobs_preserved": True,
              "exact_targeted_job_preserved": True}
    print(json.dumps(report, indent=2), flush=True)
    return report


if __name__ == "__main__":
    validate_scope()
