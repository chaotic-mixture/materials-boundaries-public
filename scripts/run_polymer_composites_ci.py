#!/usr/bin/env python3
"""Bounded checks for the exact 2026-10-19 polymer/composite experiment.

--validate-scope checks the fixed ancestor, approved paths and exact workflow.
--test runs only the named core modules, with no skipped/expected-failure passes.
--wheel-dir DIR --dependency-dir DIR verifies six local wheels, installs them
offline into a fresh venv, and runs the four-record smoke plus affected platform
modules once. It never invokes the exhaustive check_wheel_metadata smoke.
"""
import argparse
import ast
from email.parser import BytesParser
from hashlib import sha256
import importlib
import inspect
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import tomllib
import unittest
import venv
from zipfile import ZipFile

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
CI = ROOT / "experimental/platform/ci"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
from check_polymer_composites_scope import BASE_COMMIT, validate_scope
from check_wheel_metadata import check_metadata, literal_version

CORE_MODULES = (
    "test_polymer_composites_increment", "test_polymer_composites_source_facts",
    "test_polymer_formulations_increment", "test_nc2_increment",
    "test_nbs_next_batch", "test_material_incremental_integration",
    "test_material_class_counts_preservation", "test_presentation_fast_path_preservation",
)
CORE_TEST_IDS = (
    "test_material_bulk_preservation.MaterialBulkPreservationTests.test_accepted_tree_ledger_helper_and_admission_are_pinned",
    "test_material_bulk_preservation.MaterialBulkPreservationTests.test_readme_counts_and_noncount_prose_remain_checked",
    "test_material_bulk_preservation.MaterialBulkPreservationTests.test_all_402_predecessor_files_round_trip_exactly",
)
NEW_REQUIRED_IDS = {
    "query": {
        "test_baseline_compatibility.BaselineCompatibility.test_a592_complete_manifest_and_catalog_recovery_remain_exact",
        "test_baseline_compatibility.BaselineCompatibility.test_a592_pin_cannot_replace_current_anchor",
        "test_baseline_compatibility.BaselineCompatibility.test_a592_registry_rejected_without_migration",
    },
    "ingestion": {
        "test_nomad_incremental.IncrementalTests.test_a592_predecessor_scope_stays_read_only_without_migration",
    },
}
PLATFORM_GROUPS = {
    "query": ("experimental/platform/query-service/catalog-tests", "local-catalog", (
        "test_catalog_baseline", "test_baseline_compatibility", "test_local_catalog",
        "test_family_relationships", "test_formal_project_catalog", "test_computed_recovery",
        "test_computed_v2_tranche", "test_computed_v2_second_tranche", "test_combined_admission_boundary")),
    "ingestion": ("experimental/platform/ingestion", "nomad-ingestion", (
        "test_review_boundary", "test_nomad_incremental", "test_incremental_independent",
        "test_nomad_evidence_compare", "test_formal_overlap_audit", "test_formal_review_gaps")),
    "hbn": ("experimental/platform/relationships", "hbn-projection", ("test_hbn_relationship_projection",)),
    "formal": ("formal-catalog/tests", None, ("test_formal_project_core",)),
}
# Distribution name, source project, import package. No network-resolved project
# may replace one of these six local wheels.
PACKAGES = (
    ("materials-boundaries", ".", "materials_boundaries"),
    ("materials-project-catalog", "formal-catalog", "materials_project_catalog"),
    ("materials-boundaries-federation-prototype", "experimental/platform/federation", "materials_federation"),
    ("materials-boundaries-query-service", "experimental/platform/query-service", "materials_query"),
    ("materials-lifecycle-prototype", "experimental/platform/lifecycle", "materials_lifecycle"),
    ("materials-boundaries-platform-experimental", "experimental/platform", "materials_platform"),
)
NEW_FACTS = {
    "ewurum2025_pbs_lignin45": ("youngs_modulus", "1206", "MPa", "132", "reported_mean", "reported_standard_deviation"),
    "bianchi2022_epdm_h_p20": ("mass_density", "0.55", "g/cm^3", "0.02", "reported_value", "reported_plus_minus_unspecified"),
    "bianchi2022_epdm_h_p40": ("mass_density", "0.66", "g/cm^3", "0.01", "reported_value", "reported_plus_minus_unspecified"),
    "bianchi2022_epdm_h_p60": ("mass_density", "0.70", "g/cm^3", "0.01", "reported_value", "reported_plus_minus_unspecified"),
}


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def run(command, *, cwd, env, timeout=1800):
    print("+ " + " ".join(map(str, command)), flush=True)
    subprocess.run(list(map(str, command)), cwd=cwd, env=env, check=True, timeout=timeout)


def clean_env():
    env = {key: value for key, value in os.environ.items() if not key.startswith("PYTHON")}
    for key in ("MP_API_KEY", "PMG_MAPI_KEY", "MAPI_KEY"):
        env.pop(key, None)
    env.update(PYTHONUTF8="1", PYTHONDONTWRITEBYTECODE="1", PIP_DISABLE_PIP_VERSION_CHECK="1", PIP_NO_INPUT="1")
    return env


def install_offline_guard():
    """Block network I/O except CPython's internal Windows socketpair connect.

    This is a fixture regression guard, not a sandbox against malicious code.
    A loopback destination alone never qualifies for the exception.
    """
    import os
    from pathlib import Path
    import socket
    import sys
    import sysconfig

    if getattr(sys, "_polymer_composites_offline", False):
        return
    if getattr(sys, "_platform_ci_offline", False):
        raise RuntimeError("Start a fresh process without the legacy all-socket sitecustomize guard")
    pair_code = getattr(socket.socketpair, "__code__", None)
    standard_socket = Path(sysconfig.get_path("stdlib")) / "socket.py"
    pair_is_standard = (pair_code is not None and Path(pair_code.co_filename).resolve() == standard_socket.resolve()
                        and Path(socket.__file__).resolve() == standard_socket.resolve())

    def offline(event, args):
        if event not in {"socket.connect", "socket.getaddrinfo", "socket.sendto"}:
            return
        if event == "socket.connect" and os.name == "nt" and pair_is_standard and len(args) == 2:
            caller = sys._getframe(1)
            if caller.f_code is pair_code:
                listener = caller.f_locals.get("lsock")
                address = args[1]
                if (args[0] is caller.f_locals.get("csock") and isinstance(listener, socket.socket)
                        and isinstance(address, tuple) and len(address) == 2
                        and address[0] in {"127.0.0.1", "::1"}
                        and address == listener.getsockname()[:2]
                        and address == (caller.f_locals.get("addr"), caller.f_locals.get("port"))
                        and listener.getsockopt(socket.SOL_SOCKET, socket.SO_ACCEPTCONN) == 1):
                    return
        raise RuntimeError("Offline fixture CI forbids network I/O: " + event)

    sys.addaudithook(offline)
    sys._platform_ci_offline = True
    sys._polymer_composites_offline = True


def test_ids(suite):
    for test in suite:
        if isinstance(test, unittest.TestSuite):
            yield from test_ids(test)
        else:
            yield test.id()


def frozen_test_ids(relative, modules):
    """Existing explicitly declared tests cannot vanish from the selected modules."""
    required = set()
    for module in modules:
        name = relative + "/" + module + ".py"
        result = subprocess.run(["git", "show", BASE_COMMIT + ":" + name], cwd=ROOT, capture_output=True)
        if result.returncode:
            require(module in {"test_polymer_composites_increment", "test_polymer_composites_source_facts",
                               "test_material_class_counts_preservation"},
                    "Cannot read frozen test module: " + name)
            continue
        for node in ast.parse(result.stdout.decode("utf-8")).body:
            if isinstance(node, ast.ClassDef):
                required.update(module + "." + node.name + "." + method.name for method in node.body
                                if isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)) and method.name.startswith("test"))
    return required


def installed_origins():
    for _, _, package in PACKAGES:
        module = importlib.import_module(package)
        require(Path(module.__file__).resolve().is_relative_to(Path(sys.prefix).resolve()),
                "Source package imported instead of installed wheel: " + package)


def run_group(name):
    install_offline_guard()
    require(getattr(sys, "_platform_ci_offline", False), "Offline socket guard did not load")
    if name == "core":
        relative, inventory_key, modules = "tests", None, CORE_MODULES
        sys.path.insert(0, str(ROOT))
    else:
        require(sys.prefix != sys.base_prefix, "Platform groups require an isolated installation")
        installed_origins()
        relative, inventory_key, modules = PLATFORM_GROUPS[name]
    directory = ROOT / relative
    sys.path.insert(0, str(directory))
    suite = unittest.TestSuite()
    counts = {}
    for module in modules:
        require((directory / (module + ".py")).is_file(), "Missing selected module: " + module)
        loader = unittest.TestLoader()
        selected = loader.discover(str(directory), pattern=module + ".py")
        require(not loader.errors, "Discovery errors: " + "\n".join(loader.errors))
        count = selected.countTestCases()
        require(count > 0, "Selected module contains no tests: " + module)
        counts[module] = count
        suite.addTests(selected)
    if name == "core":
        for identifier in CORE_TEST_IDS:
            loader = unittest.TestLoader()
            selected = loader.loadTestsFromName(identifier)
            require(not loader.errors and selected.countTestCases() == 1, "Missing selected exact test: " + identifier)
            suite.addTests(selected)
        counts["test_material_bulk_preservation (three exact cases)"] = len(CORE_TEST_IDS)
    ids = list(test_ids(suite))
    require(len(ids) == len(set(ids)), "Duplicate selected test IDs")
    required = frozen_test_ids(relative, modules)
    if name == "core":
        required.update(CORE_TEST_IDS)
    required.update(NEW_REQUIRED_IDS.get(name, ()))
    if inventory_key:
        inventory = json.loads((CI / "required_test_ids.json").read_text(encoding="utf-8"))[inventory_key]
        required.update(identifier for identifier in inventory if identifier.split(".")[0] in modules)
    require(required <= set(ids), "Missing frozen/required test IDs: " + ", ".join(sorted(required - set(ids))))
    if name == "core":
        for module, minimum in (("test_polymer_composites_increment", 7), ("test_polymer_composites_source_facts", 12),
                                ("test_material_class_counts_preservation", 8)):
            require(counts[module] >= minimum, "Missing new batch regression tests: " + module)
    print("DISCOVERED " + json.dumps({"group": name, "module_counts": counts, "test_ids": ids}, sort_keys=True), flush=True)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    require(result.testsRun == len(ids) and result.wasSuccessful() and not result.skipped and not result.expectedFailures,
            name + ": failures, errors, skips or expected failures are not a full pass")
    if name != "core":
        installed_origins()
    print("TARGETED " + json.dumps({"group": name, "passed": result.testsRun, "skipped": 0}), flush=True)


def verify_wheels(directory):
    wheels = sorted(directory.glob("*.whl"))
    require(len(wheels) == len(PACKAGES), "Expected exactly six locally built wheels")
    results = []
    for distribution, relative, package in PACKAGES:
        matches = [wheel for wheel in wheels if wheel.name.startswith(distribution.replace("-", "_") + "-")]
        require(len(matches) == 1, "Missing or duplicate local wheel: " + distribution)
        project = ROOT / relative
        config = tomllib.loads((project / "pyproject.toml").read_text(encoding="utf-8"))
        version = (literal_version((project / package / "_version.py").read_text(encoding="utf-8"))
                   if distribution == "materials-boundaries" else config["project"]["version"])
        source_files = {path.relative_to(project).as_posix(): path for path in (project / package).rglob("*")
                        if path.is_file() and "__pycache__" not in path.parts and path.suffix not in {".pyc", ".pyo"}}
        with ZipFile(matches[0]) as archive:
            names = archive.namelist()
            require(len(names) == len(set(names)), "Wheel contains duplicate members")
            metadata_paths = [name for name in names if name.endswith(".dist-info/METADATA")]
            require(len(metadata_paths) == 1, "Missing or duplicate wheel metadata")
            metadata = BytesParser().parsebytes(archive.read(metadata_paths[0]))
            require(metadata["Name"] == distribution and metadata["Version"] == version, "Wheel project/version mismatch")
            if distribution == "materials-boundaries":
                check_metadata(metadata, version)
            packaged = {name for name in names if name.startswith(package + "/") and not name.endswith("/")}
            require(packaged == set(source_files), "Packaged file set differs from source: " + package)
            for name, path in source_files.items():
                require(archive.read(name) == path.read_bytes(), "Wheel/source bytes differ: " + name)
            for license_name in ("LICENSE", "THIRD_PARTY_NOTICES.md"):
                require(license_name in metadata.get_all("License-File", []), "Missing license metadata: " + license_name)
                members = [name for name in names if ".dist-info/" in name and name.endswith("/" + license_name)]
                require(len(members) == 1 and archive.read(members[0]) == (project / license_name).read_bytes(),
                        "License/notice bytes differ: " + license_name)
        results.append({"wheel": matches[0].name, "sha256": sha256(matches[0].read_bytes()).hexdigest(),
                        "package_files_exact": len(source_files)})
    print("WHEELS " + json.dumps(results, sort_keys=True), flush=True)
    return wheels


INSTALLED_SMOKE = r'''
from collections import Counter
from contextlib import redirect_stdout
from hashlib import sha256
from importlib.resources import files
import io
import json
from pathlib import Path
import sys

def require(condition, message):
    if not condition:
        raise RuntimeError(message)

import materials_boundaries as package
from materials_boundaries.catalog import read_catalog, query_catalog
from materials_boundaries.cli import main
from materials_project_catalog.catalog import formal_project_catalog
from materials_query.computed_registry import baseline_digest

expected = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
require(Path(package.__file__).resolve().is_relative_to(Path(sys.prefix).resolve()), "Checkout core import")
for filename, digest in expected["resource_hashes"].items():
    require(sha256(files("materials_boundaries").joinpath("data", filename).read_bytes()).hexdigest() == digest,
            "Installed data bytes differ: " + filename)
materials = read_catalog("materials")
properties = read_catalog("reference_properties")
require(len(materials["identities"]) == 1083 and len(materials["records"]) == 1083,
        "Installed source-qualified count differs")
require(dict(Counter(row["category"] for row in materials["identities"])) ==
        {"natural": 1010, "metal": 22, "inorganic": 26, "polymer": 15, "composite": 10},
        "Installed category counts differ")
identities = {row["id"]: row for row in materials["identities"]}
states = {row["id"]: row for row in materials["records"]}
props = {row["id"]: row for row in properties["records"]}
outputs = 0
for suffix, values in expected["facts"].items():
    quantity, number, unit, amplitude, statistic, uncertainty_kind = values
    identity = identities["mat_" + suffix]
    state = states["state_" + suffix]
    prop = props["refprop_" + suffix + "_" + quantity]
    require(identity["category"] == "composite" and state["grade_id"] is None, "New identity/grade changed")
    require((prop["quantity"], prop["reported_value"]["number"], prop["reported_value"]["unit_code"],
             prop["uncertainty"]["number"], prop["summary_statistic"], prop["uncertainty_status"]) == tuple(values),
            "Installed selected source semantics changed: " + suffix)
    require(prop["sample_count"]["value"] == 10 and prop["sample_count"]["relation"] == "exact", "Sample count changed")
    require(prop["evaluation_support"] == "catalog_only" and not prop["universal_bound"] and not prop["engineering_allowable"]
            and not prop["verification"]["independent_scientific_review"] and not prop["verification"]["raw_data_reanalysis"],
            "Installed candidate gained scientific capabilities")
    if suffix == "ewurum2025_pbs_lignin45":
        require(prop["conditions"]["temperature"]["status"] == "not_reported_in_inspected_source", "B45 test temperature invented")
    selected = query_catalog("reference-properties", record_id=prop["id"])
    for language in ("en", "zh", "ja", "de"):
        for flag in ("--json", "--text"):
            output = io.StringIO()
            with redirect_stdout(output):
                code = main(["catalog", "reference-properties", "--id", prop["id"], "--lang", language, flag])
            text = output.getvalue()
            require(code == 0 and "[missing:" not in text, "Installed selected CLI failed")
            if flag == "--json":
                require(json.loads(text) == selected, "Installed JSON depends on language")
            else:
                require(number in text and prop["uncertainty_note"] in text, "Installed source value/caveat lost")
            outputs += 1
formal = formal_project_catalog()
require(formal["counts"] == {"formal_project_admission_count": 1107, "legacy_source_qualified_identity_count": 1083,
        "reviewed_computed_composition_count": 24,
        "categories": {"natural": 1010, "metal": 34, "inorganic": 38, "polymer": 15, "composite": 10}},
        "Installed formal admission boundary changed")
anchor = baseline_digest()
require(isinstance(anchor, str) and len(anchor) == 64, "Installed query anchor failed")
print(json.dumps({"new_identities": 4, "selected_cli_outputs": outputs, "formal_count": 1107,
                  "reviewed_computed": 24, "core_count": 1083, "query_baseline": anchor,
                  "fresh_install": True, "scope": "selected smoke; not the exhaustive wheel metadata suite"}))
'''


def check_installed(wheel_dir, dependency_dir):
    wheels = verify_wheels(wheel_dir)
    require(dependency_dir.is_dir() and any(dependency_dir.glob("*.whl")), "Offline dependency wheel directory is missing")
    env = clean_env()
    with tempfile.TemporaryDirectory(prefix="polymer-composites-installed-") as temporary:
        work = Path(temporary)
        runtime = work / "runtime"
        venv.EnvBuilder(with_pip=True, system_site_packages=False).create(runtime)
        python = runtime / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        run([python, "-I", "-m", "pip", "--isolated", "install", "--no-index", "--no-deps", "--find-links", dependency_dir,
             "-r", ROOT / "experimental/platform/requirements-lock.txt", "-r", CI / "projection-requirements.txt"], cwd=work, env=env)
        run([python, "-I", "-m", "pip", "--isolated", "install", "--no-index", "--no-deps", *wheels], cwd=work, env=env)
        run([python, "-I", "-m", "pip", "check"], cwd=work, env=env)
        payload = {"facts": NEW_FACTS, "resource_hashes": {
            name: sha256((ROOT / "materials_boundaries/data" / name).read_bytes()).hexdigest()
            for name in ("materials.json", "reference_properties.json", "sources.json")}}
        expected = work / "expected.json"
        expected.write_text(json.dumps(payload), encoding="utf-8")
        smoke = work / "installed_smoke.py"
        smoke.write_text(inspect.getsource(install_offline_guard) + "\ninstall_offline_guard()\n" + INSTALLED_SMOKE,
                         encoding="utf-8")
        run([python, "-I", smoke, expected], cwd=work, env=env)
        # Each worker installs the bounded Windows-compatible offline guard.
        # No checkout package or legacy sitecustomize directory is on PYTHONPATH.
        for group in PLATFORM_GROUPS:
            run([python, "-B", Path(__file__).resolve(), "--platform-group", group], cwd=work, env=env)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument("--validate-scope", action="store_true")
    actions.add_argument("--test", action="store_true")
    actions.add_argument("--wheel-dir", type=Path)
    actions.add_argument("--platform-group", choices=tuple(PLATFORM_GROUPS))
    parser.add_argument("--dependency-dir", type=Path)
    args = parser.parse_args()
    if args.platform_group:
        run_group(args.platform_group)
        return
    validate_scope()
    if args.test:
        run_group("core")
    elif args.wheel_dir:
        require(args.dependency_dir is not None, "--wheel-dir requires --dependency-dir for an offline fresh installation")
        check_installed(args.wheel_dir.resolve(), args.dependency_dir.resolve())
    elif args.dependency_dir:
        parser.error("--dependency-dir requires --wheel-dir")


if __name__ == "__main__":
    main()
