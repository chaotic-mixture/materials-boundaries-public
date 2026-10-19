#!/usr/bin/env python3
"""Limit the evidence-batch experiment to reviewed files and one exact job.

The fixed predecessor and path inventory constrain software execution. They do
not grant scientific approval, license approval or material admission.
"""
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
from check_polymer_composites_scope import (
    FULL_JOB_IF as PREVIOUS_FULL_JOB_IF, changed_paths, require,
    validate_targeted_run_scalars,
)

BASE_COMMIT = "12cb89ca82b48ba444bdb921674c3d232d448720"
BRANCH_REF = "refs/heads/experiment/evidence-batch-ingestion-20261019"
PREVIOUS_BRANCH_REF = "refs/heads/experiment/polymer-composites-20261019"
FULL_JOB_IF = (
    "    if: ${{ github.event_name != 'push' || (github.ref != '" + PREVIOUS_BRANCH_REF
    + "' && github.ref != '" + BRANCH_REF + "') }}\n"
)
BUILD_COMMAND = (
    "python -m pip wheel --no-index --no-deps --no-build-isolation --wheel-dir dist . "
    "./formal-catalog ./experimental/platform/federation ./experimental/platform/query-service "
    "./experimental/platform/lifecycle ./experimental/platform"
)

# Only individually approved files belong here. This inventory is frozen
# against 12cb89c after the compiler, source packet and recovery owners finish.
APPROVED_FILES = frozenset({
    '.github/workflows/ci.yml',
    'README.md',
    'docs/EVIDENCE_BATCH_20261019.md',
    'docs/FORMAL_PROJECT_CATALOG.md',
    'docs/FORMULATION_PACKET_PREPARATION.md',
    'experimental/material-batches/20261019-pa12-source-family/README.md',
    'experimental/material-batches/20261019-pa12-source-family/integration-report.json',
    'experimental/material-batches/20261019-pa12-source-family/integration.json',
    'experimental/material-batches/20261019-pa12-source-family/packet-spec.json',
    'experimental/material-batches/20261019-pa12-source-family/prepared-packet.json',
    'experimental/platform/ingestion/FORMAL_OVERLAP_AUDIT.md',
    'experimental/platform/ingestion/FORMAL_REVIEW_GAPS.md',
    'experimental/platform/ingestion/INCREMENTAL.md',
    'experimental/platform/ingestion/README.md',
    'experimental/platform/ingestion/nomad_review_boundary.py',
    'experimental/platform/ingestion/test_formal_overlap_audit.py',
    'experimental/platform/ingestion/test_formal_review_gaps.py',
    'experimental/platform/ingestion/test_incremental_independent.py',
    'experimental/platform/ingestion/test_nomad_evidence_compare.py',
    'experimental/platform/ingestion/test_nomad_incremental.py',
    'experimental/platform/ingestion/test_review_boundary.py',
    'experimental/platform/query-service/README.md',
    'experimental/platform/query-service/catalog-tests/test_baseline_compatibility.py',
    'experimental/platform/query-service/catalog-tests/test_catalog_baseline.py',
    'experimental/platform/query-service/catalog-tests/test_combined_admission_boundary.py',
    'experimental/platform/query-service/catalog-tests/test_computed_recovery.py',
    'experimental/platform/query-service/catalog-tests/test_computed_v2_second_tranche.py',
    'experimental/platform/query-service/catalog-tests/test_computed_v2_tranche.py',
    'experimental/platform/query-service/catalog-tests/test_family_relationships.py',
    'experimental/platform/query-service/catalog-tests/test_formal_project_catalog.py',
    'experimental/platform/query-service/catalog-tests/test_local_catalog.py',
    'experimental/platform/query-service/materials_query/computed_registry.py',
    'experimental/platform/query-service/materials_query/pins/legacy_baseline.json',
    'experimental/platform/relationships/test_hbn_relationship_projection.py',
    'formal-catalog/README.md',
    'formal-catalog/materials_project_catalog/catalog.py',
    'formal-catalog/tests/test_formal_project_core.py',
    'materials_boundaries/data/materials.json',
    'materials_boundaries/data/reference_properties.json',
    'materials_boundaries/data/sources.json',
    'scripts/check_evidence_batch_scope.py',
    'scripts/integrate_material_candidates.py',
    'scripts/prepare_formulation_packet.py',
    'scripts/run_evidence_batch_ci.py',
    'tests/evidence_batch_data_preservation.py',
    'tests/evidence_batch_workflow_preservation.py',
    'tests/fixtures/evidence_batch_data_updates_20261019.json',
    'tests/fixtures/evidence_batch_workflow_updates_20261019.json',
    'tests/fixtures/formulation_packet_replay_20261019.json',
    'tests/fixtures/pa12_pa2200_source_transcription_20261019.json',
    'tests/material_class_counts_preservation.py',
    'tests/test_evidence_batch_data_preservation.py',
    'tests/test_evidence_batch_workflow_preservation.py',
    'tests/test_formulation_packet_integration.py',
    'tests/test_formulation_packet_preparation.py',
    'tests/test_material_class_counts_preservation.py',
    'tests/test_pa12_source_family_packet.py',
    'tests/test_polymer_composites_increment.py',
})

TARGETED_JOB = """  evidence-batch-targeted:
    if: ${{ github.event_name == 'push' && github.ref == 'refs/heads/experiment/evidence-batch-ingestion-20261019' }}
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
          persist-credentials: false
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - run: python scripts/run_evidence_batch_ci.py --validate-scope
      - run: "python -m pip install --no-deps --only-binary=:all: -r experimental/platform/ci/build-requirements.txt"
      - run: python -m pip install --no-build-isolation -e '.[dev]'
      - run: python scripts/run_evidence_batch_ci.py --test
      - run: python scripts/validate_catalogs.py
      - run: python -m pip wheel --no-index --no-deps --no-build-isolation --wheel-dir dist . ./formal-catalog ./experimental/platform/federation ./experimental/platform/query-service ./experimental/platform/lifecycle ./experimental/platform
      - run: "python -m pip download --no-deps --only-binary=:all: --dest dist/dependencies -r experimental/platform/requirements-lock.txt -r experimental/platform/ci/projection-requirements.txt"
      - run: python scripts/run_evidence_batch_ci.py --wheel-dir dist --dependency-dir dist/dependencies
"""


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def validate_wheel_command(command):
    require(command == BUILD_COMMAND,
            "Wheel build must use the exact six local projects and offline build flags")


def expected_workflow(baseline):
    """Preserve the previous branch job and every old step byte for byte."""
    validate_targeted_run_scalars(TARGETED_JOB)
    commands = [line.removeprefix("      - run: ") for line in TARGETED_JOB.splitlines()
                if line.startswith("      - run: python -m pip wheel ")]
    require(len(commands) == 1, "Expected one six-project wheel build")
    validate_wheel_command(commands[0])
    require(baseline.count(PREVIOUS_FULL_JOB_IF) == 2,
            "Unexpected frozen full-job guards")
    require(baseline.count("  polymer-composites-targeted:\n") == 1,
            "The previous experiment job must remain present")
    require("  evidence-batch-targeted:\n" not in baseline,
            "The fixed predecessor must not contain this experiment job")
    for job in ("unit-and-schema", "windows-composite"):
        marker = "  " + job + ":\n" + PREVIOUS_FULL_JOB_IF
        require(baseline.count(marker) == 1, "Unexpected original job block: " + job)
        baseline = baseline.replace(marker, "  " + job + ":\n" + FULL_JOB_IF, 1)
    return baseline + TARGETED_JOB


def validate_names(names, *, root=ROOT):
    require(all(type(name) is str for name in names), "Changed paths must be strings")
    unexpected = sorted(set(names) - APPROVED_FILES)
    require(not unexpected, "Changes exceed the approved evidence-batch scope: " + ", ".join(unexpected))
    for name in names:
        path = root / name
        require(not path.is_symlink() and path.is_file() and path.resolve().is_relative_to(root.resolve()),
                "Approved path must remain a regular repository file: " + name)


def validate_scope():
    head = git("rev-parse", "HEAD").decode().strip()
    subprocess.run(["git", "merge-base", "--is-ancestor", BASE_COMMIT, head], cwd=ROOT, check=True)
    if os.environ.get("GITHUB_ACTIONS") == "true":
        require(os.environ.get("GITHUB_EVENT_NAME") == "push", "Scoped CI requires a push event")
        require(os.environ.get("GITHUB_REF") == BRANCH_REF, "Scoped CI requires its exact experiment branch")
        require(os.environ.get("GITHUB_SHA") == head, "Checkout differs from the pushed GITHUB_SHA")
        require(not git("status", "--porcelain", "--untracked-files=normal"),
                "Scoped CI checkout must be clean before execution")
    names = set(changed_paths(git("diff", "--name-status", "--no-renames", "-z", BASE_COMMIT, "HEAD", "--")))
    names.update(changed_paths(git("diff", "--name-status", "--no-renames", "-z", "HEAD", "--")))
    names.update(name for name in git("ls-files", "--others", "--exclude-standard", "-z").decode("utf-8").split("\0") if name)
    validate_names(names)
    baseline = git("show", BASE_COMMIT + ":.github/workflows/ci.yml").decode("utf-8")
    actual = (ROOT / ".github/workflows/ci.yml").read_bytes().decode("utf-8")
    require(actual == expected_workflow(baseline),
            "Workflow differs from the fixed predecessor plus the exact evidence-batch job")
    result = {"base_commit": BASE_COMMIT, "head": head, "branch_ref": BRANCH_REF,
              "changed_files": sorted(names), "old_job_steps_preserved": True,
              "previous_experiment_job_preserved": True, "exact_targeted_job_preserved": True}
    print(json.dumps(result, indent=2), flush=True)
    return result


if __name__ == "__main__":
    validate_scope()
