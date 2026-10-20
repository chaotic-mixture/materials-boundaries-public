#!/usr/bin/env python3
"""Validate the bounded fourth primary-table growth branch.

Reuse the existing offline execution and six-package verification primitives.
Only frozen case IDs run; earlier full suites are not invoked by this entry point.
"""
import argparse
from collections import Counter
import inspect
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import venv

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
from run_primary_table_growth_3_ci import (
    BRANCH_REF as PREVIOUS_BRANCH_REF, BUILD_COMMAND,
    FULL_JOB_IF as PREVIOUS_FULL_JOB_IF, TARGETED_JOB as PREVIOUS_TARGETED_JOB,
    changed_paths, validate_targeted_run_scalars, validate_wheel_command,
)
from run_evidence_batch_ci import (
    ExactResult, PACKAGES, clean_env, install_offline_guard, installed_origins,
    require, run, sha256, test_ids, verify_wheels,
)

BASE_COMMIT = "a5cc3f6c47954033db5de7f50220d182cfcff459"
BRANCH_REF = "refs/heads/experiment/primary-table-growth-4-20261019"
FULL_JOB_IF = PREVIOUS_FULL_JOB_IF.replace("') }}\n", "' && github.ref != '" + BRANCH_REF + "') }}\n")
TARGETED_JOB = (PREVIOUS_TARGETED_JOB
                .replace("  primary-table-growth-3-targeted:\n", "  primary-table-growth-4-targeted:\n")
                .replace(PREVIOUS_BRANCH_REF, BRANCH_REF)
                .replace("run_primary_table_growth_3_ci.py", "run_primary_table_growth_4_ci.py"))

# The owner-approved inventory is frozen after packet, data and history owners finish.
APPROVED_FILES = frozenset({
    '.github/workflows/ci.yml',
    'README.md',
    'experimental/material-batches/mtibe-pbs-pbat-hybrids-20261019/README.md',
    'experimental/material-batches/mtibe-pbs-pbat-hybrids-20261019/integration-report.json',
    'experimental/material-batches/mtibe-pbs-pbat-hybrids-20261019/integration.json',
    'experimental/material-batches/mtibe-pbs-pbat-hybrids-20261019/packet-spec.json',
    'experimental/material-batches/mtibe-pbs-pbat-hybrids-20261019/preparation-receipt.json',
    'experimental/material-batches/mtibe-pbs-pbat-hybrids-20261019/prepared-packet.json',
    'experimental/material-batches/mtibe-pbs-pbat-hybrids-20261019/source-review.json',
    'experimental/platform/ci/required_test_ids.json',
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
    'scripts/run_primary_table_growth_4_ci.py',
    'tests/fixtures/primary_table_growth_4_data_20261019.json',
    'tests/fixtures/primary_table_growth_4_files_20261019.json',
    'tests/material_append_successors.py',
    'tests/test_primary_table_growth_4_ci.py',
    'tests/test_primary_table_growth_4_preservation.py',
})

# Nonempty exact inventories are required before any selected phase can run.
TEST_GROUPS = {'core': ('tests', ('test_primary_table_growth_4_preservation.PrimaryTableGrowth4PreservationTests.test_three_hybrids_keep_raw_formulations_and_measurement_limits', 'test_primary_table_growth_4_preservation.PrimaryTableGrowth4PreservationTests.test_exact_a5_recovery_rejects_partial_duplicate_unit_and_source_drift', 'test_primary_table_growth_4_preservation.PrimaryTableGrowth4PreservationTests.test_compiler_and_integrator_replay_preserve_immutable_artifacts', 'test_primary_table_growth_4_preservation.PrimaryTableGrowth4PreservationTests.test_selected_catalog_bytes_and_legacy_chain_remain_exact', 'test_primary_table_growth_4_preservation.PrimaryTableGrowth4PreservationTests.test_finite_files_and_registry_selection_keep_old_pins', 'test_primary_table_growth_4_ci.PrimaryTableGrowth4CITests.test_previous_jobs_keep_every_step_and_only_new_branch_is_gated', 'test_primary_table_growth_4_ci.PrimaryTableGrowth4CITests.test_scope_rejects_unlisted_paths_deleted_files_and_nonfiles', 'test_primary_table_growth_4_ci.PrimaryTableGrowth4CITests.test_ci_requires_exact_event_branch_sha_and_clean_checkout', 'test_primary_table_growth_4_ci.PrimaryTableGrowth4CITests.test_ambiguous_yaml_scalars_and_index_package_builds_fail', 'test_primary_table_growth_4_ci.PrimaryTableGrowth4CITests.test_unknown_predecessor_workflow_shapes_are_rejected', 'test_primary_table_growth_3_preservation.PrimaryTableGrowth3PreservationTests.test_selected_catalog_bytes_and_legacy_chain_remain_exact', 'test_primary_table_growth_3_ci.PrimaryTableGrowth3CITests.test_previous_jobs_keep_every_step_and_only_new_branch_is_gated')), 'query': ('experimental/platform/query-service/catalog-tests', ('test_catalog_baseline.IntegratedBaselineTests.test_installed_package_matches_exact_new_anchor', 'test_catalog_baseline.IntegratedBaselineTests.test_old_database_anchor_is_rejected_without_migration', 'test_catalog_baseline.IntegratedBaselineTests.test_changed_core_resource_fails_even_with_unchanged_identity_count', 'test_baseline_compatibility.BaselineCompatibility.test_mtibe_batch_parent_manifest_and_catalog_recovery_remain_exact', 'test_baseline_compatibility.BaselineCompatibility.test_mtibe_batch_parent_database_rejected_without_migration', 'test_baseline_compatibility.BaselineCompatibility.test_binary_batch_parent_manifest_and_catalog_recovery_remain_exact', 'test_local_catalog.CatalogAPI.test_02_metadata_counts_and_versions', 'test_local_catalog.CatalogAPI.test_mtibe_hybrid_three_reference_resolutions', 'test_family_relationships.FamilyRelationshipTests.test_coverage_exact_and_no_count_inflation', 'test_formal_project_catalog.FormalAPI.test_counts_and_no_legacy_rewrite', 'test_formal_project_catalog.FormalAPI.test_drift_disables_only_formal', 'test_combined_admission_boundary.CombinedAdmissionBoundary.test_second_tranche_admission_does_not_change_formal_counts_or_pins', 'test_computed_recovery.RegistryTests.test_atomic_held_and_replay')), 'formal': ('formal-catalog/tests', ('test_formal_project_core.FormalProjectCatalog.test_exact_counts_and_categories', 'test_formal_project_core.FormalProjectCatalog.test_full_legacy_identity_parity', 'test_formal_project_core.FormalProjectCatalog.test_pin_drift_fail_closed')), 'ingestion': ('experimental/platform/ingestion', ('test_review_boundary.ReviewBoundaryTests.test_formal_and_example_counts_remain_separate', 'test_review_boundary.ReviewBoundaryTests.test_boundary_fails_closed_on_changed_bytes', 'test_nomad_incremental.IncrementalTests.test_mtibe_predecessor_scope_stays_read_only_without_migration', 'test_nomad_incremental.IncrementalTests.test_new_store_requires_exact_current_catalog_scope_before_creation', 'test_incremental_independent.IndependentIncrementalTests.test_real_boundary_blocks_remapped_entries_without_promoting_examples', 'test_formal_overlap_audit.FormalOverlapAuditTests.test_inventory_covers_only_all_1081_frozen_formal_records', 'test_formal_overlap_audit.FormalOverlapAuditTests.test_primary_partition_and_overlapping_dimensions_are_distinct')), 'relationships': ('experimental/platform/relationships', ('test_hbn_relationship_projection.HBNRelationshipProjectionTests.test_actual_counts_are_separate_from_proposed_graph',))}

SOURCE_ID = "mtibe_2022_pbs_pbat_lignin_zno"
FORMULATIONS = (
    ("5", "95/5/1.5", "261.88", "14.78"),
    ("10", "90/10/1.5", "304.52", "5.22"),
    ("15", "85/15/1.5", "347.44", "16.92"),
)
PRIMARY_COUNTS = {"natural": 1010, "metal": 22, "inorganic": 49, "polymer": 18, "composite": 13}
GRAPH_COUNTS = {"identity": 1112, "grade": 21, "state": 1112, "property": 1112, "source": 116}


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def expected_workflow(baseline):
    """Change only the complementary full-job guards and append one exact job."""
    validate_targeted_run_scalars(TARGETED_JOB)
    commands = [line.removeprefix("      - run: ") for line in TARGETED_JOB.splitlines()
                if line.startswith("      - run: python -m pip wheel ")]
    require(len(commands) == 1, "Expected one six-project wheel build")
    validate_wheel_command(commands[0])
    require(baseline.count(PREVIOUS_FULL_JOB_IF) == 2, "Unexpected frozen full-job guards")
    for name in ("polymer-composites-targeted", "evidence-batch-targeted", "source-family-growth-targeted", "pur-formulation-targeted", "primary-table-growth-targeted", "primary-table-growth-2-targeted", "primary-table-growth-3-targeted"):
        require(baseline.count("  " + name + ":\n") == 1, "Missing previous experiment job: " + name)
    require("  primary-table-growth-4-targeted:\n" not in baseline, "Predecessor already contains this job")
    for name in ("unit-and-schema", "windows-composite"):
        marker = "  " + name + ":\n" + PREVIOUS_FULL_JOB_IF
        require(baseline.count(marker) == 1, "Unexpected predecessor job block: " + name)
        baseline = baseline.replace(marker, "  " + name + ":\n" + FULL_JOB_IF, 1)
    return baseline + TARGETED_JOB


def validate_names(names, *, root=ROOT):
    require(all(type(name) is str for name in names), "Changed paths must be strings")
    unexpected = sorted(set(names) - APPROVED_FILES)
    require(not unexpected, "Changes exceed fourth primary-table growth scope: " + ", ".join(unexpected))
    for name in names:
        path = root / name
        require(not path.is_symlink() and path.is_file() and path.resolve().is_relative_to(root.resolve()),
                "Approved path must remain a regular repository file: " + name)


def validate_event(head):
    if os.environ.get("GITHUB_ACTIONS") == "true":
        require(os.environ.get("GITHUB_EVENT_NAME") == "push", "Scoped CI requires a push event")
        require(os.environ.get("GITHUB_REF") == BRANCH_REF, "Scoped CI requires its exact experiment branch")
        require(os.environ.get("GITHUB_SHA") == head, "Checkout differs from the pushed GITHUB_SHA")
        require(not git("status", "--porcelain", "--untracked-files=normal"), "Scoped CI checkout must be clean")


def validate_scope():
    head = git("rev-parse", "HEAD").decode().strip()
    subprocess.run(["git", "merge-base", "--is-ancestor", BASE_COMMIT, head], cwd=ROOT, check=True)
    validate_event(head)
    names = set(changed_paths(git("diff", "--name-status", "--no-renames", "-z", BASE_COMMIT, "HEAD", "--")))
    names.update(changed_paths(git("diff", "--name-status", "--no-renames", "-z", "HEAD", "--")))
    names.update(name for name in git("ls-files", "--others", "--exclude-standard", "-z").decode("utf-8").split("\0") if name)
    validate_names(names)
    baseline = git("show", BASE_COMMIT + ":.github/workflows/ci.yml").decode("utf-8")
    require((ROOT / ".github/workflows/ci.yml").read_bytes().decode("utf-8") == expected_workflow(baseline),
            "Workflow differs from the exact predecessor plus fourth primary-table growth job")
    result = {"base_commit": BASE_COMMIT, "head": head, "branch_ref": BRANCH_REF, "changed_files": sorted(names),
              "old_job_steps_preserved": True, "previous_experiment_jobs_preserved": True,
              "exact_targeted_job_preserved": True}
    print(json.dumps(result, indent=2), flush=True)
    return result


def run_group(name):
    install_offline_guard()
    relative, expected = TEST_GROUPS[name]
    require(expected and len(expected) == len(set(expected)), "Exact inventory is empty or duplicated: " + name)
    if name == "core":
        sys.path.insert(0, str(ROOT))
    else:
        require(sys.prefix != sys.base_prefix, "Selected package checks require a fresh installation")
        require(str(ROOT) not in sys.path, "Checkout root must not shadow installed packages")
        installed_origins()
    sys.path.insert(0, str(ROOT / relative))
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromNames(list(expected))
    require(not loader.errors, "Selected test loading failed: " + "\n".join(loader.errors))
    discovered = list(test_ids(suite))
    require(discovered == list(expected), "Discovery differs from the fixed inventory")
    print("DISCOVERED " + json.dumps({"group": name, "test_ids": discovered}, sort_keys=True), flush=True)
    result = unittest.TextTestRunner(verbosity=2, resultclass=ExactResult, failfast=False).run(suite)
    require(result.testsRun == len(expected) and result.started_ids == discovered
            and result.passed_ids == discovered and result.wasSuccessful()
            and not result.skipped and not result.expectedFailures and not result.unexpectedSuccesses,
            name + ": discovered/started/passed IDs differ, or failures/errors/skips occurred")
    if name != "core":
        installed_origins()
    print("TARGETED " + json.dumps({"group": name, "passed": result.testsRun, "skipped": 0,
                                    "failed": 0, "errors": 0, "test_ids": discovered}, sort_keys=True), flush=True)


def installation_payload():
    graphs = {name: json.loads((ROOT / "materials_boundaries/data" / filename).read_bytes())
              for name, filename in (("materials", "materials.json"),
                                     ("properties", "reference_properties.json"), ("sources", "sources.json"))}
    tables = {"identity": graphs["materials"]["identities"], "grade": graphs["materials"]["grades"],
              "state": graphs["materials"]["records"], "property": graphs["properties"]["records"],
              "source": graphs["sources"]["records"]}
    selected = []
    for lignin, raw_formula, modulus, plus_minus in FORMULATIONS:
        stem = "mtibe2022_pbs_pbat_lignin" + lignin + "_zno"
        ids = {"identity": "mat_" + stem, "state": "state_" + stem,
               "property": "refprop_" + stem + "_tensile_modulus"}
        composition = ("Table 2 (PBS/PBAT)/Lignin/ZnO = " + raw_formula + " as printed; internal PBS/PBAT = 70/30, ratio basis unspecified. "
                       "Section 2.3 calls the lignosulphonate loading " + lignin + " wt.% and ZnO 1.5 wt.%; the Table 2 entries total 101.5 "
                       "and the ZnO denominator is unspecified. No normalization is performed.")
        bundle = {"expected_modulus": modulus, "expected_plus_minus": plus_minus,
                  "expected_formulation": raw_formula, "expected_composition": composition}
        for kind, identifier in ids.items():
            rows = [row for row in tables[kind] if row["id"] == identifier]
            require(len(rows) == 1, "Expected one hybrid formulation record: " + identifier)
            bundle[kind] = rows[0]
        selected.append(bundle)
    source = [row for row in tables["source"] if row["id"] == SOURCE_ID]
    require(len(source) == 1, "Expected the reused Mtibe source")
    require(dict(Counter(row["category"] for row in tables["identity"])) == PRIMARY_COUNTS,
            "Source tree primary category counts differ")
    require({kind: len(rows) for kind, rows in tables.items()} == GRAPH_COUNTS, "Source tree graph counts differ")
    return {"selected": selected, "source": source[0], "primary_counts": PRIMARY_COUNTS,
            "graph_counts": GRAPH_COUNTS, "packages": [package for _, _, package in PACKAGES],
            "resource_hashes": {name: sha256((ROOT / "materials_boundaries/data" / name).read_bytes()).hexdigest()
                                for name in ("materials.json", "reference_properties.json", "sources.json")}}


INSTALLED_SMOKE = r'''
from collections import Counter
from contextlib import redirect_stdout
from hashlib import sha256
from importlib.resources import files
import importlib
import io
import json
from pathlib import Path
import sys

def require(condition, message):
    if not condition:
        raise RuntimeError(message)

expected = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
for name in expected["packages"]:
    package = importlib.import_module(name)
    require(Path(package.__file__).resolve().is_relative_to(Path(sys.prefix).resolve()), "Checkout package imported: " + name)
from materials_boundaries.catalog import read_catalog, query_catalog
from materials_boundaries.cli import main
from materials_project_catalog.catalog import formal_project_catalog
from materials_query.computed_registry import baseline_digest

for name, digest in expected["resource_hashes"].items():
    require(sha256(files("materials_boundaries").joinpath("data", name).read_bytes()).hexdigest() == digest,
            "Installed catalog bytes differ: " + name)
materials, properties, sources = (read_catalog(name) for name in ("materials", "reference_properties", "sources"))
tables = {"identity": materials["identities"], "grade": materials["grades"], "state": materials["records"],
          "property": properties["records"], "source": sources["records"]}
require({kind: len(rows) for kind, rows in tables.items()} == expected["graph_counts"], "Installed graph counts changed")
require(dict(Counter(row["category"] for row in materials["identities"])) == expected["primary_counts"],
        "Installed primary categories changed")
require([row for row in tables["source"] if row["id"] == expected["source"]["id"]] == [expected["source"]],
        "Reused source differs")
outputs = 0
identity_ids = []
for bundle in expected["selected"]:
    for kind in ("identity", "state", "property"):
        wanted = bundle[kind]
        require([row for row in tables[kind] if row["id"] == wanted["id"]] == [wanted],
                "Installed complete hybrid record differs: " + wanted["id"])
    identity, state, prop = (bundle[name] for name in ("identity", "state", "property"))
    identity_ids.append(identity["id"])
    require(identity["category"] == "composite" and state["grade_id"] is None,
            "Hybrid formulation category/grade changed")
    require(prop["quantity"] == "tensile_modulus" and prop["quantity_dimension"] == "pressure"
            and prop["reported_value"]["kind"] == "scalar"
            and prop["reported_value"]["number"] == prop["reported_value"]["value_text"] == bundle["expected_modulus"]
            and prop["reported_value"]["unit_code"] == prop["reported_value"]["unit_text"] == "MPa",
            "Reported tensile-modulus center, dimension or unit changed")
    require(state["identity_id"] == identity["id"] and prop["material_state_id"] == state["id"]
            and state["property_ids"] == [prop["id"]] and prop["source_id"] == expected["source"]["id"],
            "Hybrid identity/state/property/source links changed")
    require(prop["determination_basis"] == "source_reports_measurement" and prop["density_basis"] is None
            and prop["reporting_basis"] == "reported_summary" and prop["summary_statistic"] == "reported_value",
            "Source summary was converted to a mean, calculation or density")
    uncertainty = prop["uncertainty"]
    require(prop["uncertainty_status"] == uncertainty["type"] == "reported_plus_minus_unspecified"
            and uncertainty["number"] == uncertainty["value_text"] == bundle["expected_plus_minus"]
            and uncertainty["unit_code"] == uncertainty["unit_text"] == "MPa"
            and uncertainty["coverage_factor"] is None and uncertainty["confidence_level"] is None,
            "Undefined plus/minus amplitude was changed or given a statistical interpretation")
    require(prop["sample_count"]["value"] == 5 and prop["sample_count"]["relation"] == "exact"
            and "Five tested specimens do not establish a reported arithmetic mean or SD." in prop["basis_note"],
            "Specimen count or unknown aggregation qualification changed")
    require(prop["conditions"]["temperature"]["status"] == "reported"
            and prop["conditions"]["temperature"]["text"] == "25 \u00b0C",
            "Tensile temperature changed or inherited processing conditions")
    require(prop["conditions"]["test_standard"]["text"] == "ASTM D638, source-stated tensile-test basis"
            and prop["conditions"]["test_standard"]["notes"] == "No edition or independent compliance verification."
            and prop["conditions"]["conditioning"]["text"] == "48 h at 25 \u00b0C before tensile testing",
            "Source method, unspecified edition or conditioning changed")
    require(prop["conditions"]["loading_rate"]["status"] == "not_reported_in_inspected_source"
            and prop["conditions"]["loading_rate"]["text"] is None,
            "Unknown loading rate was replaced")
    humidity = [row["fact"] for row in prop["conditions"]["additional_conditions"]
                if row["name"] == "test_relative_humidity"]
    require(len(humidity) == 1 and humidity[0]["status"] == "not_reported_in_inspected_source"
            and humidity[0]["text"] is None, "Unknown tensile humidity was replaced")
    composition = state["state"]["composition_or_purity"]
    require(state["source_designation"] == bundle["expected_formulation"]
            and composition["status"] == "reported" and composition["text"] == bundle["expected_composition"]
            and composition["notes"] == identity["identity_scope"]
            and "Table 3 abbreviates its row labels by omitting ZnO" in identity["identity_scope"],
            "Printed formulation, unknown denominator or table linkage was normalized or lost")
    require(prop["evaluation_support"] == "catalog_only" and not prop["universal_bound"]
            and not prop["engineering_allowable"] and not prop["verification"]["independent_scientific_review"]
            and not prop["verification"]["raw_data_reanalysis"], "hybrid reference gained scientific capabilities")
    selected = query_catalog("reference-properties", record_id=prop["id"])
    for language in ("en", "zh", "ja", "de"):
        for flag in ("--json", "--text"):
            output = io.StringIO()
            with redirect_stdout(output):
                code = main(["catalog", "reference-properties", "--id", prop["id"], "--lang", language, flag])
            text = output.getvalue()
            require(code == 0 and "[missing:" not in text, "Installed hybrid CLI failed")
            if flag == "--json":
                require(json.loads(text) == selected, "Installed hybrid JSON depends on language")
            else:
                require(bundle["expected_modulus"] in text and prop["uncertainty_note"] in text,
                        "Installed hybrid value/caveat missing")
            outputs += 1
require(len(set(identity_ids)) == 3, "hybrid formulas were counted repeatedly")
formal = formal_project_catalog()
require(formal["counts"] == {"formal_project_admission_count": 1136, "legacy_source_qualified_identity_count": 1112,
        "reviewed_computed_composition_count": 24,
        "categories": {"natural": 1010, "metal": 34, "inorganic": 61, "polymer": 18, "composite": 13}},
        "Installed formal boundary differs")
for identifier in identity_ids:
    require(len([row for row in formal["records"] if row["partition"] == "legacy-source-qualified"
                 and row["identity"]["id"] == identifier]) == 1, "hybrid contributes multiple formal identities")
anchor = baseline_digest()
require(isinstance(anchor, str) and len(anchor) == 64, "Installed query anchor failed")
print(json.dumps({"new_identities": 3, "new_grades": 0, "new_states": 3, "new_properties": 3, "new_sources": 0,
                  "selected_cli_outputs": outputs, "formal_count": 1136, "reviewed_computed": 24,
                  "core_count": 1112, "query_baseline": anchor, "fresh_install": True,
                  "scope": "Selected installed hybrid tensile-modulus summaries; not exhaustive regression."}))
'''


def check_installed(wheel_dir, dependency_dir):
    wheels = verify_wheels(wheel_dir)
    require(dependency_dir.is_dir() and any(dependency_dir.glob("*.whl")), "Offline dependency wheels are missing")
    env = clean_env()
    with tempfile.TemporaryDirectory(prefix="primary-table-growth-4-installed-") as temporary:
        work = Path(temporary)
        runtime = work / "runtime"
        venv.EnvBuilder(with_pip=True, system_site_packages=False).create(runtime)
        python = runtime / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
        run([python, "-I", "-m", "pip", "--isolated", "install", "--no-index", "--no-deps", "--find-links", dependency_dir,
             "-r", ROOT / "experimental/platform/requirements-lock.txt",
             "-r", ROOT / "experimental/platform/ci/projection-requirements.txt"], cwd=work, env=env)
        run([python, "-I", "-m", "pip", "--isolated", "install", "--no-index", "--no-deps", *wheels], cwd=work, env=env)
        run([python, "-I", "-m", "pip", "check"], cwd=work, env=env)
        expected = work / "expected.json"
        expected.write_text(json.dumps(installation_payload()), encoding="utf-8")
        smoke = work / "installed_smoke.py"
        smoke.write_text(inspect.getsource(install_offline_guard) + "\ninstall_offline_guard()\n" + INSTALLED_SMOKE,
                         encoding="utf-8")
        run([python, "-I", smoke, expected], cwd=work, env=env)
        for group in TEST_GROUPS:
            if group != "core":
                run([python, "-B", Path(__file__).resolve(), "--installed-group", group], cwd=work, env=env)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument("--validate-scope", action="store_true")
    actions.add_argument("--test", action="store_true")
    actions.add_argument("--wheel-dir", type=Path)
    actions.add_argument("--installed-group", choices=tuple(name for name in TEST_GROUPS if name != "core"))
    parser.add_argument("--dependency-dir", type=Path)
    args = parser.parse_args()
    if args.installed_group:
        run_group(args.installed_group)
        return
    validate_scope()
    if args.test:
        run_group("core")
    elif args.wheel_dir:
        require(args.dependency_dir is not None, "--wheel-dir requires --dependency-dir")
        check_installed(args.wheel_dir.resolve(), args.dependency_dir.resolve())
    elif args.dependency_dir:
        parser.error("--dependency-dir requires --wheel-dir")


if __name__ == "__main__":
    main()
