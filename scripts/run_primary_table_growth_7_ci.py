#!/usr/bin/env python3
"""Validate the bounded seventh primary-table growth branch.

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
from run_primary_table_growth_6_ci import (
    BRANCH_REF as PREVIOUS_BRANCH_REF, BUILD_COMMAND,
    FULL_JOB_IF as PREVIOUS_FULL_JOB_IF, TARGETED_JOB as PREVIOUS_TARGETED_JOB,
    changed_paths, validate_targeted_run_scalars, validate_wheel_command,
)
from run_evidence_batch_ci import (
    ExactResult, PACKAGES, clean_env, install_offline_guard, installed_origins,
    require, run, sha256, test_ids, verify_wheels,
)

BASE_COMMIT = 'eee77b5033d7671bbaa2d3b4eca57c88d52fc411'
BRANCH_REF = "refs/heads/experiment/primary-table-growth-7-20261020"
FULL_JOB_IF = PREVIOUS_FULL_JOB_IF.replace("') }}\n", "' && github.ref != '" + BRANCH_REF + "') }}\n")
TARGETED_JOB = (PREVIOUS_TARGETED_JOB
                .replace("  primary-table-growth-6-targeted:\n", "  primary-table-growth-7-targeted:\n")
                .replace(PREVIOUS_BRANCH_REF, BRANCH_REF)
                .replace("run_primary_table_growth_6_ci.py", "run_primary_table_growth_7_ci.py"))

# The owner-approved inventory is frozen after packet, data and history owners finish.
APPROVED_FILES = frozenset({
    '.github/workflows/ci.yml',
    'README.md',
    'docs/FORMULATION_PACKET_PREPARATION.md',
    'experimental/material-batches/outokumpu-core-moduli-20261020/README.md',
    'experimental/material-batches/outokumpu-core-moduli-20261020/integration-report.json',
    'experimental/material-batches/outokumpu-core-moduli-20261020/integration.json',
    'experimental/material-batches/outokumpu-core-moduli-20261020/packet-spec.json',
    'experimental/material-batches/outokumpu-core-moduli-20261020/preparation-receipt.json',
    'experimental/material-batches/outokumpu-core-moduli-20261020/prepared-packet.json',
    'experimental/material-batches/outokumpu-core-moduli-20261020/source-review.json',
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
    'scripts/prepare_formulation_packet.py',
    'scripts/run_primary_table_growth_7_ci.py',
    'tests/fixtures/primary_table_growth_7_data_20261020.json',
    'tests/fixtures/primary_table_growth_7_files_20261020.json',
    'tests/material_append_successors.py',
    'tests/test_formulation_packet_metal.py',
    'tests/test_primary_table_growth_7_ci.py',
    'tests/test_primary_table_growth_7_preservation.py',
})

# Nonempty exact inventories are required before any selected phase can run.
TEST_GROUPS = {'core': ('tests', ('test_primary_table_growth_7_preservation.PrimaryTableGrowth7PreservationTests.test_ten_qualified_grades_keep_reference_moduli_and_unknown_conditions', 'test_primary_table_growth_7_preservation.PrimaryTableGrowth7PreservationTests.test_exact_eee_recovery_rejects_partial_duplicate_unit_and_source_drift', 'test_primary_table_growth_7_preservation.PrimaryTableGrowth7PreservationTests.test_compiler_and_integrator_replay_preserve_immutable_artifacts', 'test_primary_table_growth_7_preservation.PrimaryTableGrowth7PreservationTests.test_selected_catalog_bytes_and_legacy_chain_remain_exact', 'test_primary_table_growth_7_preservation.PrimaryTableGrowth7PreservationTests.test_finite_files_and_registry_selection_keep_old_pins', 'test_primary_table_growth_7_ci.PrimaryTableGrowth7CITests.test_previous_jobs_keep_every_step_and_only_new_branch_is_gated', 'test_primary_table_growth_7_ci.PrimaryTableGrowth7CITests.test_scope_rejects_unlisted_paths_deleted_files_and_nonfiles', 'test_primary_table_growth_7_ci.PrimaryTableGrowth7CITests.test_ci_requires_exact_event_branch_sha_and_clean_checkout', 'test_primary_table_growth_7_ci.PrimaryTableGrowth7CITests.test_ambiguous_yaml_scalars_and_index_package_builds_fail', 'test_primary_table_growth_7_ci.PrimaryTableGrowth7CITests.test_unknown_predecessor_workflow_shapes_are_rejected', 'test_primary_table_growth_6_preservation.PrimaryTableGrowth6PreservationTests.test_selected_catalog_bytes_and_legacy_chain_remain_exact', 'test_primary_table_growth_6_ci.PrimaryTableGrowth6CITests.test_previous_jobs_keep_every_step_and_only_new_branch_is_gated', 'test_formulation_packet_metal.MetalFormulationPacketTests.test_frozen_manufacturer_profile_keeps_qualified_grades_and_reference_semantics', 'test_formulation_packet_metal.MetalFormulationPacketTests.test_rehashed_source_claimed_license_or_another_manufacturer_stays_pending', 'test_formulation_packet_metal.MetalFormulationPacketTests.test_document_or_property_scope_drift_stays_pending_without_conversion', 'test_formulation_packet_metal.MetalFormulationPacketTests.test_pending_source_review_and_scientific_upgrade_cannot_become_ready', 'test_formulation_packet_preparation.FormulationPacketPreparationTests.test_missing_crosswalk_review_and_license_remain_pending_without_upgrade', 'test_formulation_packet_preparation.FormulationPacketPreparationTests.test_shared_contexts_and_explicit_grade_multiple_states_do_not_multiply_identity')), 'query': ('experimental/platform/query-service/catalog-tests', ('test_catalog_baseline.IntegratedBaselineTests.test_installed_package_matches_exact_new_anchor', 'test_catalog_baseline.IntegratedBaselineTests.test_old_database_anchor_is_rejected_without_migration', 'test_catalog_baseline.IntegratedBaselineTests.test_changed_core_resource_fails_even_with_unchanged_identity_count', 'test_baseline_compatibility.BaselineCompatibility.test_outokumpu_batch_parent_manifest_and_catalog_recovery_remain_exact', 'test_baseline_compatibility.BaselineCompatibility.test_outokumpu_batch_parent_database_rejected_without_migration', 'test_baseline_compatibility.BaselineCompatibility.test_nbr_batch_parent_manifest_and_catalog_recovery_remain_exact', 'test_local_catalog.CatalogAPI.test_02_metadata_counts_and_versions', 'test_local_catalog.CatalogAPI.test_outokumpu_core_ten_reference_resolutions', 'test_family_relationships.FamilyRelationshipTests.test_coverage_exact_and_no_count_inflation', 'test_formal_project_catalog.FormalAPI.test_counts_and_no_legacy_rewrite', 'test_formal_project_catalog.FormalAPI.test_drift_disables_only_formal', 'test_combined_admission_boundary.CombinedAdmissionBoundary.test_second_tranche_admission_does_not_change_formal_counts_or_pins', 'test_computed_recovery.RegistryTests.test_atomic_held_and_replay')), 'formal': ('formal-catalog/tests', ('test_formal_project_core.FormalProjectCatalog.test_exact_counts_and_categories', 'test_formal_project_core.FormalProjectCatalog.test_full_legacy_identity_parity', 'test_formal_project_core.FormalProjectCatalog.test_pin_drift_fail_closed')), 'ingestion': ('experimental/platform/ingestion', ('test_review_boundary.ReviewBoundaryTests.test_formal_and_example_counts_remain_separate', 'test_review_boundary.ReviewBoundaryTests.test_boundary_fails_closed_on_changed_bytes', 'test_nomad_incremental.IncrementalTests.test_outokumpu_predecessor_scope_stays_read_only_without_migration', 'test_nomad_incremental.IncrementalTests.test_new_store_requires_exact_current_catalog_scope_before_creation', 'test_incremental_independent.IndependentIncrementalTests.test_real_boundary_blocks_remapped_entries_without_promoting_examples', 'test_formal_overlap_audit.FormalOverlapAuditTests.test_inventory_covers_only_all_1081_frozen_formal_records', 'test_formal_overlap_audit.FormalOverlapAuditTests.test_primary_partition_and_overlapping_dimensions_are_distinct')), 'relationships': ('experimental/platform/relationships', ('test_hbn_relationship_projection.HBNRelationshipProjectionTests.test_actual_counts_are_separate_from_proposed_graph',))}

SOURCE_ID = "outokumpu_core_1560en4_202211"
FORMULATIONS = (('304', 'Core 304/4301', '200', 'not_stated'), ('304ln', 'Core 304LN/4311', '200', 'not_stated'), ('305', 'Core 305/4303', '200', 'not_stated'), ('321', 'Core 321/4541', '200', 'not_stated'), ('347', 'Core 347/4550', '200', 'not_stated'), ('301ln', 'Core 301LN/4318', '200', 'not_stated'), ('301', 'Core 301/4310', '200', 'not_stated'), ('201', 'Core 201/4372', '200', 'not_stated'), ('201ln', 'Core 201LN/4372', '200', 'not_stated'), ('4622', 'Core 4622', '220', 'source_reports_measurement'))
PRIMARY_COUNTS = {"natural": 1010, "metal": 32, "inorganic": 49, "polymer": 18, "composite": 25}
GRAPH_COUNTS = {"identity": 1134, "grade": 31, "state": 1134, "property": 1134, "source": 116}


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
    for name in ("polymer-composites-targeted", "evidence-batch-targeted", "source-family-growth-targeted", "pur-formulation-targeted", "primary-table-growth-targeted", "primary-table-growth-2-targeted", "primary-table-growth-3-targeted", "primary-table-growth-4-targeted", "primary-table-growth-5-targeted", "primary-table-growth-6-targeted"):
        require(baseline.count("  " + name + ":\n") == 1, "Missing previous experiment job: " + name)
    require("  primary-table-growth-7-targeted:\n" not in baseline, "Predecessor already contains this job")
    for name in ("unit-and-schema", "windows-composite"):
        marker = "  " + name + ":\n" + PREVIOUS_FULL_JOB_IF
        require(baseline.count(marker) == 1, "Unexpected predecessor job block: " + name)
        baseline = baseline.replace(marker, "  " + name + ":\n" + FULL_JOB_IF, 1)
    return baseline + TARGETED_JOB


def validate_names(names, *, root=ROOT):
    require(all(type(name) is str for name in names), "Changed paths must be strings")
    unexpected = sorted(set(names) - APPROVED_FILES)
    require(not unexpected, "Changes exceed seventh primary-table growth scope: " + ", ".join(unexpected))
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
            "Workflow differs from the exact predecessor plus seventh primary-table growth job")
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
    packet_path = ROOT / "experimental/material-batches/outokumpu-core-moduli-20261020/prepared-packet.json"
    require(sha256(packet_path.read_bytes()).hexdigest() == "c7317758ae4c1a4025ac00c6b288770e61cf33056caaf1771a638af66d32b84f",
            "Reviewed manufacturer-reference packet changed")
    candidate = json.loads(packet_path.read_bytes())["catalogs"]
    graphs = {name: json.loads((ROOT / "materials_boundaries/data" / filename).read_bytes())
              for name, filename in (("materials", "materials.json"),
                                     ("properties", "reference_properties.json"), ("sources", "sources.json"))}
    tables = {"identity": graphs["materials"]["identities"], "grade": graphs["materials"]["grades"],
              "state": graphs["materials"]["records"], "property": graphs["properties"]["records"],
              "source": graphs["sources"]["records"]}
    candidate_tables = {"identity": candidate["materials"]["identities"], "grade": candidate["materials"]["grades"],
                        "state": candidate["materials"]["records"], "property": candidate["properties"]["records"]}
    require(all(len(rows) == 10 for rows in candidate_tables.values()),
            "Candidate identity/grade/state/property inventory changed")
    selected = []
    for suffix, designation, modulus, determination in FORMULATIONS:
        stem = "outokumpu_" + suffix
        ids = {"identity": "mat_" + stem, "grade": "grade_" + stem, "state": "state_" + stem,
               "property": "refprop_" + stem + "_youngs_modulus"}
        bundle = {"expected_modulus": modulus, "expected_determination": determination,
                  "expected_designation": designation}
        for kind, identifier in ids.items():
            rows = [row for row in tables[kind] if row["id"] == identifier]
            frozen = [row for row in candidate_tables[kind] if row["id"] == identifier]
            require(len(rows) == 1 and rows == frozen, "Expected one exact reviewed metal record: " + identifier)
            bundle[kind] = rows[0]
        selected.append(bundle)
    source = [row for row in tables["source"] if row["id"] == SOURCE_ID]
    require(len(source) == 1 and source == candidate["sources"]["records"],
            "Expected the exact reused Outokumpu source")
    require(dict(Counter(row["category"] for row in tables["identity"])) == PRIMARY_COUNTS,
            "Source tree primary category counts differ")
    require({kind: len(rows) for kind, rows in tables.items()} == GRAPH_COUNTS, "Source tree graph counts differ")
    return {"selected": selected, "source": source[0], "primary_counts": PRIMARY_COUNTS,
            "graph_counts": GRAPH_COUNTS, "packages": [package for _, _, package in PACKAGES],
            "resource_hashes": {name: sha256((ROOT / "materials_boundaries/data" / name).read_bytes()).hexdigest()
                                for name in ("materials.json", "reference_properties.json", "sources.json")}}


INSTALLED_SMOKE = r'''
"""Selected installed manufacturer-reference contract; not run during preparation."""
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
    require(Path(package.__file__).resolve().is_relative_to(Path(sys.prefix).resolve()),
            "Checkout package imported: " + name)
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
require({kind: len(rows) for kind, rows in tables.items()} == expected["graph_counts"],
        "Installed graph counts changed")
require(dict(Counter(row["category"] for row in materials["identities"])) == expected["primary_counts"],
        "Installed primary categories changed")
require([row for row in tables["source"] if row["id"] == expected["source"]["id"]] == [expected["source"]],
        "Reused source differs")
require(expected["source"]["license"] == {
    "status": "no_explicit_reuse_license_verified_limited_factual_curation_only", "identifier": None},
    "Limited factual-curation source acquired a reuse license")
outputs = 0
identity_ids, grade_ids = [], []
for bundle in expected["selected"]:
    for kind in ("identity", "grade", "state", "property"):
        wanted = bundle[kind]
        require([row for row in tables[kind] if row["id"] == wanted["id"]] == [wanted],
                "Installed complete manufacturer-reference record differs: " + wanted["id"])
    identity, grade, state, prop = (bundle[name] for name in ("identity", "grade", "state", "property"))
    identity_ids.append(identity["id"])
    grade_ids.append(grade["id"])
    require(identity["category"] == "metal" and grade["identity_id"] == identity["id"]
            and state["identity_id"] == identity["id"] and state["grade_id"] == grade["id"]
            and prop["material_state_id"] == state["id"] and state["property_ids"] == [prop["id"]]
            and prop["source_id"] == expected["source"]["id"],
            "Manufacturer identity/grade/state/property/source links changed")
    require(grade["authority"] == {"kind": "manufacturer", "name": "Outokumpu"}
            and grade["designation"] == state["source_designation"] == bundle["expected_designation"],
            "Source-designated grade changed")
    require(prop["quantity"] == "youngs_modulus" and prop["quantity_dimension"] == "pressure"
            and prop["reported_value"]["kind"] == "scalar"
            and prop["reported_value"]["number"] == prop["reported_value"]["value_text"] == bundle["expected_modulus"]
            and prop["reported_value"]["unit_code"] == prop["reported_value"]["unit_text"] == "GPa",
            "Table 7 modulus, precision, dimension or unit changed")
    require(prop["evidence_kind"] == "manufacturer_reference"
            and prop["determination_basis"] == bundle["expected_determination"]
            and prop["density_basis"] is None and prop["reporting_basis"] == "not_stated"
            and prop["summary_statistic"] == "not_stated",
            "Manufacturer reference or tested-value footnote was reclassified")
    require(prop["uncertainty"] is None and prop["uncertainty_status"] == "not_reported_in_inspected_source"
            and prop["sample_count"]["value"] is None and prop["sample_count"]["relation"] == "not_reported",
            "Reference cell gained uncertainty or specimen statistics")
    require(prop["conditions"]["temperature"]["status"] == "reported"
            and prop["conditions"]["temperature"]["text"] == "20 \u00b0C"
            and prop["conditions"]["test_standard"]["text"] == "EN 10088-1",
            "Table 7 temperature or standard-reference attribution changed")
    for name in ("test_method", "direction", "conditioning", "loading_rate"):
        fact = prop["conditions"][name]
        require(fact["status"] == "not_reported_in_inspected_source" and fact["text"] is None,
                "Reference gained an unstated specimen-test condition: " + name)
    require(prop["method_definition"]["type"] == "source_reported_conventional"
            and prop["method_definition"]["extraction_window"] is None
            and "humidity" in prop["scope_note"], "Unreported method/environment limits were lost")
    for name in ("processing", "temper_or_heat_treatment", "conditioning", "orientation"):
        fact = state["state"][name]
        require(fact["status"] == "not_reported_in_inspected_source" and fact["text"] is None,
                "Reference acquired a specimen state: " + name)
    if bundle["expected_determination"] == "source_reports_measurement":
        require(identity["id"] == "mat_outokumpu_4622" and "Outokumpu tested values" in prop["basis_note"],
                "Tested-row footnote was detached from Core 4622")
    else:
        require("unstarred row" in prop["basis_note"], "Unstarred reference limitation was lost")
    require(prop["evaluation_support"] == "catalog_only" and not prop["universal_bound"]
            and not prop["engineering_allowable"] and not prop["verification"]["independent_scientific_review"]
            and not prop["verification"]["raw_data_reanalysis"], "Reference gained scientific capabilities")
    selected = query_catalog("reference-properties", record_id=prop["id"])
    for language in ("en", "zh", "ja", "de"):
        for flag in ("--json", "--text"):
            output = io.StringIO()
            with redirect_stdout(output):
                code = main(["catalog", "reference-properties", "--id", prop["id"], "--lang", language, flag])
            text = output.getvalue()
            require(code == 0 and "[missing:" not in text, "Installed manufacturer-reference CLI failed")
            if flag == "--json":
                require(json.loads(text) == selected, "Installed reference JSON depends on language")
            else:
                require(bundle["expected_modulus"] in text and prop["uncertainty_note"] in text,
                        "Installed modulus or unknown-uncertainty caveat missing")
            outputs += 1
require(len(set(identity_ids)) == len(set(grade_ids)) == 10 and outputs == 80,
        "Grades, aliases or CLI variants inflated identity counts")
for suffix, uns in (("201", "S20100"), ("201ln", "S20153")):
    grade, = [row for row in tables["grade"] if row["id"] == "grade_outokumpu_" + suffix]
    labels = [row["text"] for row in grade["aliases"]]
    require("EN 1.4372 / UNS " + uns in labels and "EN 1.4372" not in labels,
            "Shared EN designation became a duplicate bare alias")
formal = formal_project_catalog()
require(formal["counts"] == {"formal_project_admission_count": 1158, "legacy_source_qualified_identity_count": 1134,
        "reviewed_computed_composition_count": 24,
        "categories": {"natural": 1010, "metal": 44, "inorganic": 61, "polymer": 18, "composite": 25}},
        "Installed formal boundary differs")
for identifier in identity_ids:
    require(len([row for row in formal["records"] if row["partition"] == "legacy-source-qualified"
                 and row["identity"]["id"] == identifier]) == 1, "Grade contributes multiple formal identities")
anchor = baseline_digest()
require(isinstance(anchor, str) and len(anchor) == 64, "Installed query anchor failed")
print(json.dumps({"new_identities": 10, "new_grades": 10, "new_states": 10, "new_properties": 10, "new_sources": 0,
                  "selected_cli_outputs": outputs, "formal_count": 1158, "reviewed_computed": 24,
                  "core_count": 1134, "query_baseline": anchor, "fresh_install": True,
                  "scope": "Selected installed Outokumpu manufacturer-reference moduli; not exhaustive regression."}))
'''


def check_installed(wheel_dir, dependency_dir):
    wheels = verify_wheels(wheel_dir)
    require(dependency_dir.is_dir() and any(dependency_dir.glob("*.whl")), "Offline dependency wheels are missing")
    env = clean_env()
    with tempfile.TemporaryDirectory(prefix="primary-table-growth-7-installed-") as temporary:
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
