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
print(json.dumps({"version": expected, "metadata_version": metadata_version,
                  "engine_outputs": sorted(outputs), "languages": languages,
                  "installed_without_dependencies": True}))
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
