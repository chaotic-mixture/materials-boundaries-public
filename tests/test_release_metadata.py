"""Cheap standard-library preflight; scientific versions stay independent."""
import ast
from pathlib import Path
import unittest

from materials_boundaries import __version__, evaluate, load_json

ROOT = Path(__file__).resolve().parents[1]


def section(text, name):
    return text.split(f"[{name}]", 1)[1].split("\n[", 1)[0]


def references(node):
    if isinstance(node, dict):
        if "$ref" in node:
            yield node["$ref"]
        for value in node.values():
            yield from references(value)
    elif isinstance(node, list):
        for value in node:
            yield from references(value)


class ReleaseMetadataTests(unittest.TestCase):
    def test_version_is_one_build_readable_literal(self):
        tree = ast.parse((ROOT / "materials_boundaries/_version.py").read_text(encoding="utf-8"))
        statements = [node for node in tree.body if not (
            isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str))]
        self.assertEqual(len(statements), 1, "version module must have no import side effects")
        assignment = statements[0]
        self.assertIsInstance(assignment, ast.Assign)
        self.assertEqual([target.id for target in assignment.targets], ["__version__"])
        self.assertEqual(ast.literal_eval(assignment.value), __version__)
        self.assertIsInstance(ast.literal_eval(assignment.value), str)

    def test_build_configuration_and_readme_use_current_version(self):
        # Check the deliberately simple declarations without requiring a TOML
        # dependency on Python 3.10. The separate wheel smoke tests the backend.
        text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        project = section(text, "project")
        self.assertNotRegex(project, r"(?m)^version\s*=")
        self.assertRegex(project, r'(?m)^dependencies\s*=\s*\[\]\s*$')
        self.assertRegex(project, r'(?m)^dynamic\s*=\s*\["version"\]\s*$')
        self.assertRegex(section(text, "tool.setuptools.dynamic"),
                         r'(?m)^version\s*=\s*\{attr\s*=\s*"materials_boundaries\._version\.__version__"\}\s*$')
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn(f"Current software release: **v{__version__}**", readme)

    def test_all_current_engine_labels_match_package(self):
        from materials_boundaries.catalog import read_catalog
        from materials_boundaries.prediction_visualization import build_prediction_comparison
        from materials_boundaries.temperature import evaluate_temperature
        from materials_boundaries.temperature_visualization import build_temperature_comparison
        from materials_boundaries.visualization import build_comparison

        instance = load_json(ROOT / "examples/synthetic-two-phase.json")
        outputs = {
            "evaluation": evaluate(instance),
            "comparison": build_comparison([instance], fractions=[0, 1]),
            "temperature": evaluate_temperature(load_json(ROOT / "examples/temperature/synthetic-linear-50k.json")),
            "temperature_comparison": build_temperature_comparison(points_per_branch=2),
        }
        for group in read_catalog("computational_predictions")["comparison_groups"]:
            outputs[group["id"]] = build_prediction_comparison(group["id"])
        for name, output in outputs.items():
            with self.subTest(output=name):
                self.assertEqual(output["engine_version"], __version__)
        for sample in outputs["comparison"]["cases"][0]["samples"]:
            self.assertEqual(sample["evaluation"]["engine_version"], __version__)

    def test_comparison_embedded_snapshots_and_exact_references(self):
        schema = load_json(ROOT / "schemas/comparison.schema.json")
        properties = schema["properties"]
        case = properties["cases"]["items"]["properties"]
        refs = {
            "instance": case["input"]["$ref"],
            "evaluation": case["samples"]["items"]["properties"]["evaluation"]["$ref"],
            "claims": properties["catalogs"]["properties"]["claims"]["$ref"],
            "sources": properties["catalogs"]["properties"]["sources"]["$ref"],
        }
        self.assertEqual(set(schema["$defs"]), set(refs))
        for name, ref in refs.items():
            with self.subTest(schema=name):
                canonical = load_json(ROOT / "schemas" / f"{name}.schema.json")
                self.assertEqual(schema["$defs"][name], canonical)
                self.assertEqual(ref, canonical["$id"])
                self.assertEqual(ref, schema["$defs"][name]["$id"])

    def test_local_schema_reference_targets_exist(self):
        schemas = [load_json(path) for path in sorted((ROOT / "schemas").glob("*.schema.json"))]
        by_id = {schema["$id"]: schema for schema in schemas}
        self.assertEqual(len(by_id), len(schemas), "duplicate public schema $id")
        for schema in schemas:
            for ref in references(schema):
                with self.subTest(schema=schema["$id"], ref=ref):
                    uri, _, fragment = ref.partition("#")
                    self.assertIn(uri or schema["$id"], by_id)
                    target = by_id[uri or schema["$id"]]
                    if fragment:
                        self.assertTrue(fragment.startswith("/"), "expected a local JSON Pointer")
                        for token in fragment[1:].split("/"):
                            token = token.replace("~1", "/").replace("~0", "~")
                            target = target[int(token)] if isinstance(target, list) else target[token]


if __name__ == "__main__":
    unittest.main()
