#!/usr/bin/env python3
"""Check a built wheel in a fresh offline venv, never importing the checkout.

Usage: python scripts/check_wheel_metadata.py path/to/materials_boundaries-*.whl
Uses only the standard library plus the venv's bundled pip for installation.
"""
import argparse
import ast
from email.parser import Parser
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import venv
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def literal_version(source):
    assignments = [node for node in ast.parse(source).body
                   if isinstance(node, ast.Assign)
                   and any(isinstance(target, ast.Name) and target.id == "__version__"
                           for target in node.targets)]
    require(len(assignments) == 1, "expected one software version assignment")
    version = ast.literal_eval(assignments[0].value)
    require(isinstance(version, str) and bool(version), "expected a nonempty literal version")
    return version


def check_metadata(metadata, expected):
    require(metadata["Name"] == "materials-boundaries", "wrong wheel project")
    require(metadata["Version"] == expected, "wheel METADATA version differs from source literal")
    # The only supported dependencies are the explicit dev extra. Fail closed
    # on other or compound markers, including platform-specific runtime deps;
    # --no-deps alone would hide an accidental dependency declaration.
    for requirement in metadata.get_all("Requires-Dist", []):
        _, separator, marker = requirement.partition(";")
        require(separator and re.fullmatch(r'''\s*extra\s*==\s*(['"])dev\1\s*''', marker),
                "wheel declares a non-dev dependency: " + requirement)


INSTALLED_CHECK = r'''
from contextlib import redirect_stdout
from importlib.metadata import distribution
import io
import json
from pathlib import Path
import sys

import materials_boundaries as package
from materials_boundaries.catalog import read_catalog
from materials_boundaries.cli import main
from materials_boundaries.i18n import translate
from materials_boundaries.prediction_visualization import build_prediction_comparison
from materials_boundaries.temperature import evaluate_temperature
from materials_boundaries.temperature_visualization import build_temperature_comparison
from materials_boundaries.visualization import build_comparison

def require(condition, message):
    if not condition:
        raise RuntimeError(message)

expected, instance_path, temperature_path = sys.argv[1:]
require(Path(package.__file__).resolve().is_relative_to(Path(sys.prefix).resolve()),
        "package imported from outside the isolated installation")
metadata_version = distribution("materials-boundaries").version
require(metadata_version == package.__version__ == expected,
        "installed METADATA/package version mismatch")
instance = package.load_json(instance_path)
evaluation = package.evaluate(instance)
outputs = {
    "evaluation": evaluation,
    "comparison": build_comparison([instance], fractions=[0, 1]),
    "temperature": evaluate_temperature(package.load_json(temperature_path)),
    "temperature_comparison": build_temperature_comparison(points_per_branch=2),
}
for group in read_catalog("computational_predictions")["comparison_groups"]:
    outputs[group["id"]] = build_prediction_comparison(group["id"])
for name, output in outputs.items():
    require(output["engine_version"] == expected, name + ": stale installed engine label")
for sample in outputs["comparison"]["cases"][0]["samples"]:
    require(sample["evaluation"]["engine_version"] == expected, "stale nested engine label")
languages = ("en", "zh", "ja", "de")
for language in languages:
    for as_json in (False, True):
        stdout = io.StringIO()
        args = ["evaluate", instance_path, "--lang", language] + (["--json"] if as_json else [])
        with redirect_stdout(stdout):
            code = main(args)
        require(code == 0, "installed CLI failed")
        text = stdout.getvalue()
        require(json.loads(text) == evaluation if as_json else translate("summary_title", language) in text,
                "installed CLI output mismatch: " + language)
# Exercise the mixed catalog in the dependency-free installation as well.
from materials_boundaries.catalog import query_catalog
observations = read_catalog("observations")
mos2 = query_catalog("observations", source_id="bertolazzi_brivio_kis_2011")
require(len(mos2["records"]) >= 2, "missing installed MoS2 observations")
for language in languages:
    for filtered in (False, True):
        args = ["catalog", "observations", "--lang", language]
        if filtered:
            args += ["--source-id", "bertolazzi_brivio_kis_2011"]
        for as_json in (False, True):
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                code = main(args + (["--json"] if as_json else ["--text"]))
            text = stdout.getvalue()
            require(code == 0 and "[missing:" not in text, "installed observation CLI failed")
            if as_json:
                require(json.loads(text) == (mos2 if filtered else observations), "observation JSON changed by language")
            else:
                for key in ("catalog_mos2_model_notice", "catalog_sd_notice", "catalog_mos2_source_notice",
                            "catalog_mos2_transcription_notice"):
                    require(translate(key, language) in text, "missing installed scientific disclosure: " + key)
                require(translate("catalog_q_used", language) + ": " + translate("unknown", language) in text,
                        "actual fit constant must remain unknown")
                require(text.index(translate("catalog_mos2_model_notice", language)) < text.index("180 ± 60 N/m"),
                        "unresolved model notice must precede MoS2 value")
# Exercise both non-executable wave families in every language and reject
# weakened scientific metadata without installing schema/runtime dependencies.
from copy import deepcopy
from materials_boundaries.catalog_output import render_catalog
wave_ids = ("isotropic_bulk_plane_wave_speeds_and_ratio", "christoffel_tensor_strong_ellipticity")
for identifier in wave_ids:
    wave = query_catalog("claims", record_id=identifier)
    require(wave["records"][0]["evaluation_support"] == "catalog_only", "wave became executable")
    for language in languages:
        for as_json in (False, True):
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                code = main(["catalog", "claims", "--id", identifier, "--lang", language,
                             "--json" if as_json else "--text"])
            text = stdout.getvalue()
            require(code == 0 and "[missing:" not in text, "installed wave CLI failed")
            if as_json:
                require(json.loads(text) == wave, "wave JSON changed by language")
            else:
                for key in ("notice", "conditions", "normalization", "polarization", "energy", "range", "limits"):
                    require(translate("catalog_wave_" + key, language) in text, "missing wave disclosure: " + key)
    weakened = deepcopy(wave)
    weakened["records"][0]["required_assumptions"]["density"] = "rho>=0"
    try:
        render_catalog(weakened, "claims")
    except ValueError:
        pass
    else:
        raise RuntimeError("installed wave guard accepted non-strict density")
# Falin hBN source components and unknowns must also survive dependency-free installation.
from materials_boundaries._hbn_observation_contract import HBN_SOURCE
hbn = query_catalog("observations", source_id=HBN_SOURCE)
require(len(hbn["records"]) >= 2, "missing installed hBN observations")
for language in languages:
    for record in hbn["records"]:
        selected = {"schema_version": hbn["schema_version"], "records": [record]}
        for as_json in (False, True):
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                code = main(["catalog", "observations", "--id", record["id"], "--lang", language,
                             "--json" if as_json else "--text"])
            text = stdout.getvalue()
            require(code == 0 and "[missing:" not in text, "installed hBN CLI failed")
            if as_json:
                require(json.loads(text) == selected, "hBN JSON changed by language")
            else:
                for key in ("catalog_hbn_model_notice", "catalog_hbn_sd_notice", "catalog_hbn_count_notice",
                            "catalog_hbn_stress_strain_notice", "catalog_hbn_velocity_notice", "catalog_hbn_rights_notice"):
                    require(translate(key, language) in text, "missing installed hBN disclosure: " + key)
                require("PDF p. 8" in text and "MOESM443_ESM.pdf" in text, "missing SD source component")
        weakened = deepcopy(selected)
        weakened["records"][0]["reported_result"]["uncertainty"]["evidence"]["artifact"] = "publisher_html"
        try:
            render_catalog(weakened, "observations", language)
        except ValueError:
            pass
        else:
            raise RuntimeError("installed hBN guard accepted false SD provenance")
# Observation inspection is presentation-only and must work with no dev extras.
from materials_boundaries.observation_visualization import (
    build_observation_inspection, export_observation_inspection, labels,
    validate_observation_inspection, ObservationInspectionError,
)
inspection = build_observation_inspection()
require(inspection["engine_version"] == expected, "stale installed inspection version")
require(inspection["schema_version"] == "1.0.0", "wrong installed inspection schema")
require(inspection["record_snapshots"] == read_catalog("observations")["records"],
        "installed inspection changed observation snapshots")
inspection_files = {}
for language in languages:
    output = Path(instance_path).parent / "inspection" / language
    stdout = io.StringIO()
    with redirect_stdout(stdout):
        code = main(["observation", "inspect", "--output", str(output), "--lang", language])
    report = json.loads(stdout.getvalue())
    require(code == 0 and len(report["artifacts"]) == 5, "installed inspection CLI failed")
    require(set(p.name for p in output.iterdir()) == set(report["artifacts"]), "wrong inspection artifacts")
    for filename in report["artifacts"]:
        text = (output / filename).read_text(encoding="utf-8")
        require("[missing:" not in text, "missing installed inspection labels")
        if filename.endswith((".svg", ".html")):
            require(labels(language)["normalized"] in text, "missing normalized display label")
    inspection_files[language] = [(output / name).read_bytes() for name in
                                 ("observation-inspection.json", "observation-inspection.csv")]
require(all(value == inspection_files["en"] for value in inspection_files.values()),
        "inspection JSON/CSV changed by locale")
weakened = deepcopy(inspection)
weakened["presentation_policy"]["overlay_allowed"] = True
try:
    validate_observation_inspection(weakened)
except ObservationInspectionError:
    pass
else:
    raise RuntimeError("installed inspection guard accepted changed policy")
invalid_output = Path(instance_path).parent / "invalid-inspection"
try:
    export_observation_inspection(invalid_output, record_ids=["not-a-record"])
except ObservationInspectionError:
    pass
else:
    raise RuntimeError("installed inspection accepted an unknown ID")
require(not invalid_output.exists(), "invalid inspection wrote partial files")
print(json.dumps({"version": expected, "metadata_version": metadata_version,
                  "engine_outputs": sorted(outputs), "languages": languages,
                  "installed_without_dependencies": True, "mixed_observation_catalog_languages": languages, "bulk_wave_catalog_languages": languages, "hbn_observation_languages": languages, "observation_inspection_languages": languages, "observation_inspection_schema": "1.0.0"}))
'''


def check_wheel(wheel):
    expected = literal_version((ROOT / "materials_boundaries/_version.py").read_text(encoding="utf-8"))
    with ZipFile(wheel) as archive:
        metadata_files = [name for name in archive.namelist() if name.endswith(".dist-info/METADATA")]
        require(len(metadata_files) == 1, "wheel must contain one METADATA file")
        metadata = Parser().parsestr(archive.read(metadata_files[0]).decode("utf-8"))
        check_metadata(metadata, expected)
        packaged = literal_version(archive.read("materials_boundaries/_version.py").decode("utf-8"))
        require(packaged == expected, "wheel packaged version differs from source literal")
    # Ignore editable installs and caller Python configuration. -I also ignores
    # Python environment variables and excludes the working directory from imports.
    env = {key: value for key, value in os.environ.items() if not key.startswith("PYTHON")}
    with tempfile.TemporaryDirectory(prefix="materials-wheel-check-") as temporary:
        work = Path(temporary)
        venv.EnvBuilder(with_pip=True).create(work / "venv")
        python = work / "venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        subprocess.run([str(python), "-I", "-m", "pip", "--isolated", "install", "--no-index",
                        "--no-deps", "--disable-pip-version-check", str(wheel)],
                       cwd=work, env=env, check=True, capture_output=True, text=True)
        instance = work / "instance.json"
        instance.write_bytes((ROOT / "examples/synthetic-two-phase.json").read_bytes())
        temperature = work / "temperature.json"
        temperature.write_bytes((ROOT / "examples/temperature/synthetic-linear-50k.json").read_bytes())
        result = subprocess.run([str(python), "-I", "-c", INSTALLED_CHECK, expected,
                                 str(instance), str(temperature)],
                                cwd=work, env=env, check=True, capture_output=True, text=True)
        return json.loads(result.stdout)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wheel", type=Path, help="one built wheel from this release")
    args = parser.parse_args()
    try:
        print(json.dumps(check_wheel(args.wheel.resolve()), indent=2))
    except subprocess.CalledProcessError as exc:
        raise SystemExit(exc.stderr or exc.stdout or str(exc)) from exc
