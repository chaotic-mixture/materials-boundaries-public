#!/usr/bin/env python3
"""Offline runtime-scale QA. Preview and synthetic counts are never admission evidence.

Each timed operation runs in a fresh subprocess. Synthetic rich records exist
only in a temporary benchmark directory, never in packaged catalog data.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import gc
import hashlib
import json
from pathlib import Path
import platform
import resource
import subprocess
import sys
import tempfile
from time import perf_counter
import tracemalloc
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from materials_boundaries.material_presentation import LANGUAGES, render_material_catalog
from materials_boundaries.material_references import material_quota_coverage, resolve_materials, validate_material_catalog
from materials_boundaries.material_taxonomy import apply_taxonomy_migration

OPERATIONS = ("validate", "serialize", "coverage", "resolve_sample", "resolve_all", "render_sample", "render_all")
FILES = ("materials", "properties", "sources")
RUNTIME_FILES = tuple("materials_boundaries/" + name + ".py" for name in
                      ("material_references", "material_presentation", "_material_derivation",
                       "catalog", "validation", "material_taxonomy"))


def runtime_hashes():
    return {name: file_hash(ROOT / name) for name in RUNTIME_FILES}



def load_graph(directory):
    return tuple(json.loads((directory / (name + ".json")).read_text(encoding="utf-8")) for name in FILES)


def graph_counts(graph):
    materials, properties, sources = graph
    return {"identities": len(materials["identities"]), "grades": len(materials["grades"]),
            "states": len(materials["records"]), "properties": len(properties["records"]),
            "sources": len(sources["records"])}


def write_graph(directory, graph, state_ids, sample_ids):
    directory.mkdir()
    metadata = {}
    for name, value in zip(FILES, graph):
        path = directory / (name + ".json")
        with path.open("w", encoding="utf-8") as output:
            json.dump(value, output, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
        metadata[name] = {"bytes": path.stat().st_size, "sha256": file_hash(path)}
    (directory / "selection.json").write_text(json.dumps({"all": state_ids, "sample": sample_ids}), encoding="utf-8")
    return metadata


def file_hash(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def preview_with_baseline(preview_dir, baseline_dir):
    manifest_path = preview_dir / "preview-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("status") != "source_supported_preview_not_admitted":
        raise ValueError("Expected explicitly non-admitted reviewed preview")
    expected = {item["path"]: item for item in manifest["files"]}
    for name in FILES:
        path = preview_dir / (name + ".json")
        if path.stat().st_size != expected[path.name]["bytes"] or file_hash(path) != expected[path.name]["sha256"]:
            raise ValueError("Runtime preview bytes differ from manifest: " + name)
    append = load_graph(preview_dir)
    baseline = tuple(json.loads((baseline_dir / name).read_text(encoding="utf-8"))
                     for name in ("materials.json", "reference_properties.json", "sources.json"))
    migrated = apply_taxonomy_migration(baseline[0], baseline[1])
    baseline = (migrated[0], migrated[1], baseline[2])
    if graph_counts(append)["identities"] != 1000 or graph_counts(baseline)["identities"] != 57:
        raise ValueError("This reviewed benchmark requires the exact 1,000-preview plus 57-baseline graph")
    merged = deepcopy(baseline)
    for old, new in zip(merged, append):
        for key, values in new.items():
            if isinstance(values, list):
                old[key].extend(deepcopy(values))
    validate_material_catalog(*merged)
    states = append[0]["records"]
    by_identity = {row["identity_id"]: row["id"] for row in states}
    selected = [by_identity[row["id"]] for row in append[0]["identities"]
                if row["name"] in set(manifest["representative_names"])]
    if len(selected) != 4:
        raise ValueError("Expected four representative preview names")
    provenance = {"status": manifest["status"], "review_manifest_sha256": manifest["review_manifest_sha256"],
                  "preview_manifest_sha256": file_hash(manifest_path),
                  "preview_files": {name: expected[name + ".json"] for name in FILES},
                  "baseline_files": {name: {"sha256": file_hash(baseline_dir / filename)}
                                     for name, filename in zip(FILES, ("materials.json", "reference_properties.json", "sources.json"))}}
    return merged, append, [row["id"] for row in states], selected, provenance


def fictional_text(old, description):
    """Keep broadly comparable free-text size without carrying factual claims."""
    text = "BENCHMARK ONLY: " + description + "; fictional fixture, no material facts."
    return text + (" Synthetic software fixture." * max(0, (len(str(old)) - len(text) + 26) // 27))


def synthetic_graph(template, count):
    """Clone rich record structure, replacing identity and all source attribution.

    wfo-99xxxxxxxx is a schema-shaped TEST namespace here, not a claim that a
    taxon exists in WFO. No generated object is written into production data.
    """
    if type(count) is not int or not 1 <= count <= 100000:
        raise ValueError("Synthetic count must be 1..100000 for the isolated fixture namespace")
    source_map, replacements = {}, {}
    for index, source in enumerate(template[2]["records"]):
        source_map[source["id"]] = "benchmark_only_source_" + str(index)
        replacements[source["id"]] = source_map[source["id"]]
        if source.get("doi"):
            replacements[source["doi"]] = "benchmark-only:fictional-release:" + str(index)
        for offset, url in enumerate(source["urls"]):
            replacements[url] = f"https://example.invalid/benchmark-only/source-{index}/file-{offset}"

    free_text = {"identity_scope", "source_scope", "scope_note", "basis_note", "uncertainty_note",
                 "calibration_context", "count_scope_note", "source_method_uncertainty_note",
                 "conversion_uncertainty_note", "missingness_reason", "source_scope_note", "definition",
                 "inspection_scope", "source_inspection_scope", "source_statement", "scope", "revision",
                 "original_citation", "normalized_citation", "attribution", "mapping_method", "locator"}
    def rewrite(value, serial=None, field=None):
        if isinstance(value, dict):
            return {key: rewrite(item, serial, key) for key, item in value.items()}
        if isinstance(value, list):
            return [rewrite(item, serial, field) for item in value]
        if isinstance(value, str):
            if value in replacements:
                return replacements[value]
            if field in free_text:
                return fictional_text(value, f"{field} for synthetic row {serial}")
        return value

    sources = rewrite(template[2])
    for index, source in enumerate(sources["records"]):
        source.update(title=fictional_text(source["title"], f"source {index}"),
                      authors=["Synthetic benchmark fixture" for _ in source.get("authors", [])],
                      year=None, read_status="synthetic_benchmark_only_not_inspected_scientific_evidence",
                      license={"status": "synthetic_fixture_only", "identifier": "benchmark-only"},
                      claim_notes=[fictional_text(note, "generated source metadata") for note in source.get("claim_notes", [])],
                      provenance={"curation_date": "2026-10-07", "method": "Synthetic software benchmark only"},
                      bundled_content="fictional_runtime_fixture_only_not_for_catalog_admission")
    materials = {"schema_version": "1.0.0", "identities": [], "grades": [], "records": []}
    properties = {"schema_version": "1.0.0", "records": []}
    template_identity = template[0]["identities"][0]
    template_state = next(row for row in template[0]["records"] if row["identity_id"] == template_identity["id"])
    template_prop = next(row for row in template[1]["records"] if row["id"] == template_state["property_ids"][0])
    for index in range(count):
        serial = f"{index:06d}"
        identity, state, prop = (rewrite(row, serial) for row in (template_identity, template_state, template_prop))
        mid, sid, pid = (prefix + "_benchmark_only_" + serial for prefix in ("mat", "state", "refprop"))
        name = "Benchmarkus fictivus" + serial
        identity.update(id=mid, name="BENCHMARK ONLY " + name,
                        names={lang: "BENCHMARK ONLY " + name for lang in LANGUAGES},
                        aliases=[{"language": "und", "text": "BENCHMARK ONLY alias " + serial + " " + str(j)}
                                 for j, _ in enumerate(identity["aliases"])])
        taxon = identity["canonical_taxon"]
        old_accepted = taxon["accepted_taxon_id"]
        taxon_ids = [old_accepted] + sorted({taxon_id for chain in taxon["source_to_accepted_chains"]
                                           for taxon_id in chain["wfo_chain_ids"]} - {old_accepted})
        mapped = {old: f"wfo-{9900000000 + index * 10 + j:010d}" for j, old in enumerate(taxon_ids)}
        accepted = mapped[old_accepted]
        taxon.update(identity_key="wfo:" + accepted + ":" + taxon["tissue_scope"], accepted_taxon_id=accepted,
                     accepted_name=name, accepted_authority="Fixture.", accepted_full_name=name + " Fixture.",
                     original_full_name=name + " Fixture.", source_taxonomic_reference="https://example.invalid/benchmark-only/taxon/" + serial)
        for row in taxon["original_name_records"]:
            row.update(taxon_id=mapped[row["taxon_id"]], scientific_name=name, authorship="Fixture.")
        for chain in taxon["source_to_accepted_chains"]:
            chain.update(source_name_wfo_id=mapped[chain["source_name_wfo_id"]],
                         wfo_chain_ids=[mapped[value] for value in chain["wfo_chain_ids"]], accepted_terminal_wfo_id=accepted)
        taxon["backbone"].update(doi="benchmark-only:fictional-backbone", version="synthetic-1",
                                  archive_sha256="f" * 64, archive_member="benchmark-only.csv",
                                  accepted_record_1based=index + 1, accepted_physical_line_start=index + 2,
                                  accepted_physical_line_end=index + 2)
        state.update(id=sid, identity_id=mid, grade_id=None, name="BENCHMARK ONLY state " + serial,
                     names={lang: "BENCHMARK ONLY state " + serial for lang in LANGUAGES},
                     source_designation="BENCHMARK ONLY accession " + serial, property_ids=[pid])
        prop.update(id=pid, material_state_id=sid, source_property_label="BENCHMARK ONLY example basic density")
        derivation = prop["derivation"]
        derivation["specimen_scope"]["accession"] = "BENCHMARK ONLY accession " + serial
        provenance = derivation["provenance"]
        provenance.update(reviewed_batch_sha256="f" * 64, reviewed_candidate_key="wood-" + accepted,
                          license_identifiers=["benchmark-only"])
        for key in ("original", "deposited"):
            provenance[key].update(record_id="benchmark-only:" + serial, file_id="benchmark-only-file-" + key,
                                   file_name="benchmark-only-" + key + ".csv", sha256="e" * 64,
                                   release_version="synthetic-1", data_record_1based=index + 1,
                                   physical_line_start=index + 2, physical_line_end=index + 2)
        prop["source_document"]["sha256"] = "e" * 64
        prop["verification"]["source_inspection_scope"] = prop["source_document"]["inspection_scope"]
        materials["identities"].append(identity)
        materials["records"].append(state)
        properties["records"].append(prop)
    return materials, properties, sources


def serialize_graph(graph):
    digest = hashlib.sha256()
    length = 0
    encoder = json.JSONEncoder(ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    for value in graph:
        for chunk in encoder.iterencode(value):
            raw = chunk.encode("utf-8")
            digest.update(raw)
            length += len(raw)
    return {"serialized_bytes": length, "concatenated_catalog_sha256": digest.hexdigest()}


def run_worker(args):
    code_hashes = runtime_hashes()
    graph = load_graph(args.worker)
    selection = json.loads((args.worker / "selection.json").read_text(encoding="utf-8"))
    selected_ids = selection["sample" if args.operation.endswith("sample") else "all"]
    gc.collect()
    rss_before = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if args.tracemalloc:
        tracemalloc.start()
    start = perf_counter()
    result = None
    if args.operation == "validate":
        validate_material_catalog(*graph)
    elif args.operation == "serialize":
        result = serialize_graph(graph)
    elif args.operation == "coverage":
        # This operation exercises validation/counting only. Its admitted label
        # is intentionally NOT published as preview/synthetic admission evidence.
        counts = material_quota_coverage(*graph)
        result = {"validated_graph_identity_count": counts["distinct_material_count"], "release_coverage_evidence": False}
    elif args.operation.startswith("resolve"):
        result = resolve_materials(selected_ids, *graph)
    else:
        chosen = set(selected_ids)
        states = [row for row in graph[0]["records"] if row["id"] in chosen]
        incoming = {"schema_version": "1.0.0", "identities": graph[0]["identities"],
                    "grades": graph[0]["grades"], "records": states}
        from materials_boundaries.catalog import read_catalog
        from materials_boundaries.validation import _unique_pairs, _reject_constant, _strict_float, _strict_int
        filenames = dict(zip(("materials", "reference_properties", "sources"), FILES))
        def read(name):
            # Inject offline fixtures only at the resource boundary. Strict JSON
            # reads and all production renderer graph validations are timed.
            if name not in filenames:
                return read_catalog(name)
            raw = (args.worker / (filenames[name] + ".json")).read_text(encoding="utf-8")
            return json.loads(raw, object_pairs_hook=_unique_pairs, parse_constant=_reject_constant,
                              parse_float=_strict_float, parse_int=_strict_int)
        with patch("materials_boundaries.catalog.read_catalog", side_effect=read):
            result = render_material_catalog(incoming, "materials", args.language)
    seconds = perf_counter() - start
    traced_peak = tracemalloc.get_traced_memory()[1] if args.tracemalloc else None
    if args.tracemalloc:
        tracemalloc.stop()
    rss_after = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    rss_unit = 1 if sys.platform == "darwin" else 1024
    report = {"operation": args.operation, "language": args.language if args.operation.startswith("render") else None,
              "elapsed_seconds": round(seconds, 6), "process_peak_rss_bytes": rss_after * rss_unit,
              "pre_operation_process_high_water_rss_bytes": rss_before * rss_unit,
              "increment_over_pre_operation_high_water_bytes": max(0, rss_after - rss_before) * rss_unit,
              "tracemalloc_enabled": args.tracemalloc, "operation_peak_traced_bytes": traced_peak,
              "runtime_implementation_sha256": code_hashes}
    if runtime_hashes() != code_hashes:
        raise RuntimeError("Runtime implementation changed during the measured operation")
    if args.operation.startswith("render"):
        report.update(rendered_state_count=len(selected_ids), utf8_output_bytes=len(result.encode("utf-8")))
    elif args.operation.startswith("resolve"):
        report["resolved_state_count"] = len(result)
    elif result is not None:
        report.update(result)
    print(json.dumps(report, sort_keys=True))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preview-dir", type=Path)
    parser.add_argument("--baseline-dir", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--synthetic-counts", type=int, nargs="*", default=[3793, 10000])
    parser.add_argument("--languages", choices=LANGUAGES, nargs="+", default=list(LANGUAGES))
    parser.add_argument("--synthetic-languages", choices=LANGUAGES, nargs="+", default=["en"])
    parser.add_argument("--operations", choices=OPERATIONS, nargs="+", default=list(OPERATIONS))
    parser.add_argument("--tracemalloc", action="store_true", help="Optional, substantial timing overhead; reported explicitly")
    parser.add_argument("--prepare", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--prepare-count", type=int, default=0, help=argparse.SUPPRESS)
    parser.add_argument("--worker", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--operation", choices=OPERATIONS, help=argparse.SUPPRESS)
    parser.add_argument("--language", choices=LANGUAGES, default="en", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.worker:
        run_worker(args)
        return 0
    if args.prepare:
        merged, template, ids, sample, provenance = preview_with_baseline(args.preview_dir, args.baseline_dir)
        if args.prepare_count:
            del merged
            graph = synthetic_graph(template, args.prepare_count)
            ids = [row["id"] for row in graph[0]["records"]]
            sample = [ids[i] for i in sorted({0, len(ids) // 3, 2 * len(ids) // 3, len(ids) - 1})]
            validate_material_catalog(*graph)
        else:
            graph = merged
        files = write_graph(args.prepare, graph, ids, sample)
        print(json.dumps({"graph_counts": graph_counts(graph), "fixture_files": files,
                          "selected_full_state_count": len(ids), "selected_sample_state_count": len(sample),
                          "catalog_serialized_bytes": sum(value["bytes"] for value in files.values()),
                          "provenance": provenance}))
        return 0
    if not all((args.preview_dir, args.baseline_dir, args.output)):
        parser.error("--preview-dir, --baseline-dir and --output are required")
    if any(not 1 <= count <= 100000 for count in args.synthetic_counts):
        parser.error("synthetic counts must be 1..100000")
    production = ROOT / "materials_boundaries" / "data"
    if args.output.resolve() == production or production in args.output.resolve().parents:
        parser.error("benchmark output must be outside production catalog data")
    code_hashes = runtime_hashes()
    report = {"schema_version": "1.0.0", "generated_at_utc": datetime.now(timezone.utc).isoformat(),
              "runtime_implementation_sha256": code_hashes, "benchmark_script_sha256": file_hash(Path(__file__)),
              "benchmark_only": True, "production_materials_added": 0, "release_coverage_evidence": False,
              "scope": "Reviewed 1,000-row non-admitted runtime preview plus exact 57-row baseline, and separate fictional scale fixtures",
              "python": sys.version, "platform": platform.platform(),
              "method": {"one_fresh_subprocess_per_operation": True, "separate_subprocess_fixture_preparation": True,
                         "parent_elapsed_includes_interpreter_and_input_loading": True,
                         "operation_elapsed_excludes_fixture_load_but_includes_actual_input_validation": True,
                         "peak_rss_scope": "Whole worker process including Python imports and fixture JSON loading; not operation-only allocation",
                         "render_graph_read": "Strict JSON fixture reads supplied at read_catalog boundary; full production renderer and graph validations run unchanged",
                         "serialize_format": "UTF-8 sorted compact JSON, streaming encoder; sum of three catalog byte lengths",
                         "tracemalloc_enabled": args.tracemalloc,
                         "tracemalloc_note": "Instrumentation materially slows timings; compare only like instrumentation",
                         "synthetic_namespace": "IDs include benchmark_only; schema-shaped wfo-99xxxxxxxx values are fictional TEST IDs, not real WFO taxa",
                         "synthetic_generation": "Same rich metadata structure as first reviewed preview record; attribution, names, IDs, locators and scopes fictionalized",
                         "synthetic_quota_policy": "Temporary benchmark files only; never import into production or count as real material coverage"},
              "results": []}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="runtime-benchmark-only-", dir=args.output.parent) as temporary:
        # The controller never loads rich graphs. Preparing fixtures in a separate
        # child avoids inheriting a large parent RSS high-water mark at fork/exec.
        for count in [0, *args.synthetic_counts]:
            synthetic = count != 0
            name = f"fictional_runtime_{count}" if synthetic else "reviewed_preview_1000_plus_57"
            languages = args.synthetic_languages if synthetic else args.languages
            directory = Path(temporary) / name
            command = [sys.executable, str(Path(__file__).resolve()), "--prepare", str(directory),
                       "--prepare-count", str(count), "--preview-dir", str(args.preview_dir.resolve()),
                       "--baseline-dir", str(args.baseline_dir.resolve())]
            prepared = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
            if prepared.returncode:
                raise RuntimeError("Fixture preparation failed:\n" + prepared.stderr)
            details = json.loads(prepared.stdout)
            report["provenance"] = details.pop("provenance")
            current = {"scenario": name, "synthetic": synthetic,
                       "status": "fictional_benchmark_only" if synthetic else "source_supported_preview_not_admitted",
                       **details, "measurements": []}
            report["results"].append(current)
            for operation in args.operations:
                for language in languages if operation.startswith("render") else ["en"]:
                    command = [sys.executable, str(Path(__file__).resolve()), "--worker", str(directory),
                               "--operation", operation, "--language", language]
                    if args.tracemalloc:
                        command.append("--tracemalloc")
                    started = perf_counter()
                    completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
                    if completed.returncode:
                        current["failed_operation"] = {"operation": operation, "language": language,
                                                       "returncode": completed.returncode, "stderr": completed.stderr}
                        args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
                        raise RuntimeError("Benchmark worker failed:\n" + completed.stderr)
                    measurement = json.loads(completed.stdout)
                    if measurement["runtime_implementation_sha256"] != code_hashes:
                        raise RuntimeError("Runtime implementation changed between measurements; rerun on a stable snapshot")
                    measurement["subprocess_wall_seconds"] = round(perf_counter() - started, 6)
                    current["measurements"].append(measurement)
                    print(f'{name}: {operation} {language if operation.startswith("render") else ""} '
                          f'{measurement["elapsed_seconds"]:.3f}s; peak RSS {measurement["process_peak_rss_bytes"] / 1048576:.1f} MiB', flush=True)
                    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    print("Wrote runtime QA evidence: " + str(args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
