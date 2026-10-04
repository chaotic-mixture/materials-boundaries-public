"""Original single-case workflow probes; no new scientific model or evidence."""
import copy
from decimal import localcontext
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from materials_boundaries import evaluate, load_json, validate_instance, ValidationError
from materials_boundaries.catalog import read_catalog
from materials_boundaries.composite import (
    CLAIM_IDS, CompositeReplayError, build_composite_report,
    canonical_json, validate_composite_report,
)
from materials_boundaries.engine import EXPECTED

ROOT = Path(__file__).resolve().parents[1]


def original_case():
    return {
        "schema_version": "1.0.0", "id": "original-composite-case",
        "conditions": dict(EXPECTED),
        "phases": [
            {"id": "A", "volume_fraction": .25,
             "bulk_modulus": {"value": 12, "unit": "GPa"},
             "shear_modulus": {"value": 6, "unit": "GPa"}},
            {"id": "B", "volume_fraction": .75,
             "bulk_modulus": {"value": 36, "unit": "GPa"},
             "shear_modulus": {"value": 18, "unit": "GPa"}},
        ],
        "provenance": {"kind": "synthetic", "note": "Original fictitious contract-test case; no specimen data."},
    }


def set_path(data, path, value):
    for key in path[:-1]:
        data = data[key]
    data[path[-1]] = value


class CompositeCoreTests(unittest.TestCase):
    def test_one_engine_evaluation_and_one_input_validation(self):
        instance = original_case()
        with patch("materials_boundaries.composite.evaluate", wraps=evaluate) as engine_call:
            with patch("materials_boundaries.engine.validate_instance", wraps=validate_instance) as validate:
                result = build_composite_report(instance)
        self.assertEqual(engine_call.call_count, 1)
        self.assertEqual(validate.call_count, 1)
        self.assertEqual(result["evaluation"], evaluate(instance))
        self.assertEqual(result["input"], instance)
        self.assertEqual([r["claim_id"] for r in result["evaluation"]["evaluations"]], list(CLAIM_IDS))
        self.assertEqual([r["id"] for r in result["catalogs"]["claims"]["records"]], list(CLAIM_IDS))

    def test_exact_reference_endpoints(self):
        rows = build_composite_report(original_case())["evaluation"]["evaluations"]
        refs = [(Fraction(336, 13), Fraction(192, 7)), (Fraction(24), None),
                (None, Fraction(30)), (Fraction(411, 31), Fraction(267, 19)),
                (Fraction(12), None), (None, Fraction(15))]
        kl, ku, gl, gu = refs[0][0], refs[0][1], refs[3][0], refs[3][1]
        young = lambda k, g: 9 * k * g / (3 * k + g)
        poisson = lambda k, g: (3 * k - 2 * g) / (2 * (3 * k + g))
        refs.extend([(young(kl, gl), young(ku, gu)), (poisson(kl, gu), poisson(ku, gl))])
        for row, endpoints in zip(rows, refs):
            self.assertEqual(row["applicability"], "satisfied")
            for side, expected in zip(("lower", "upper"), endpoints):
                if expected is None:
                    self.assertNotIn(side, row["result"])
                else:
                    self.assertEqual(row["result"][side], float(expected))

    def test_preserves_missing_null_provenance_and_original_fractions(self):
        instance = original_case()
        instance["conditions"].pop("effective_symmetry")
        instance["phases"][0]["shear_modulus"] = None
        instance["phases"][1].pop("volume_fraction")
        instance["provenance"]["source_ids"] = ["unknown_source", "unknown_source"]
        before = copy.deepcopy(instance)
        result = build_composite_report(instance)
        self.assertEqual(instance, before)
        self.assertEqual(result["input"], before)
        self.assertEqual(result["evaluation"], evaluate(before))
        self.assertEqual(result["catalogs"]["unresolved_source_ids"], ["unknown_source"])
        validate_composite_report(result)
        result["input"]["provenance"]["note"] = "Changed output copy"
        self.assertEqual(instance, before)

    def test_deterministic_order_unicode_and_decimal_context(self):
        instance = original_case()
        instance["id"] = "../<script>未知 ' \" α"
        first = build_composite_report(instance)
        shuffled = dict(reversed(list(instance.items())))
        with localcontext() as ctx:
            ctx.prec = 5
            second = build_composite_report(shuffled)
        self.assertEqual(canonical_json(first), canonical_json(second))
        self.assertNotIn("timestamp", first)
        self.assertNotIn("lang", first)
        self.assertIn("未知", canonical_json(first))
        validate_composite_report(first)

    def test_full_catalog_records_exact_and_only_referenced_sources(self):
        catalog_paths = [ROOT / "materials_boundaries/data" / (kind + ".json") for kind in ("claims", "sources")]
        before = {p: p.read_bytes() for p in catalog_paths}
        instance = original_case()
        instance["provenance"]["source_ids"] = ["genin_birman_2009", "unresolved_z", "unresolved_a"]
        result = build_composite_report(instance)
        claim_catalog = read_catalog("claims")
        lookup = {r["id"]: r for r in claim_catalog["records"]}
        self.assertEqual(result["catalogs"]["claims"]["records"], [lookup[k] for k in CLAIM_IDS])
        source_ids = {e["source_id"] for claim in result["catalogs"]["claims"]["records"] for e in claim["evidence"]}
        source_ids.update(instance["provenance"]["source_ids"])
        source_catalog = read_catalog("sources")
        self.assertEqual(result["catalogs"]["sources"]["records"], [r for r in source_catalog["records"] if r["id"] in source_ids])
        self.assertEqual(result["catalogs"]["unresolved_source_ids"], ["unresolved_a", "unresolved_z"])
        for path in catalog_paths:
            self.assertEqual(path.read_bytes(), before[path])
        hs = result["catalogs"]["claims"]["records"][0]
        self.assertIsNone(hs["evidence"][1]["locator"])
        self.assertFalse(hs["verification"]["independent_scientific_review"])
        self.assertTrue(hs["verification"]["gaps"])
        self.assertEqual(hs["evidence"][1]["verification_status"], "original_equation_not_inspected")

    def test_every_input_catalog_source_resolves_without_extra_claims(self):
        # Input citations can name any packaged record without granting it an
        # executable rule or changing its original status/rights wording.
        instance = original_case()
        sources = read_catalog("sources")["records"]
        instance["provenance"]["source_ids"] = [r["id"] for r in sources]
        result = build_composite_report(instance)
        self.assertEqual(result["catalogs"]["sources"]["records"], sources)
        self.assertEqual(len(result["catalogs"]["claims"]["records"]), 8)
        validate_composite_report(result)

    def test_component_digests_use_exact_canonical_utf8_content(self):
        result = build_composite_report(original_case())
        for field, value in (("input", result["input"]), ("evaluation", result["evaluation"]),
                             ("claims", result["catalogs"]["claims"]), ("sources", result["catalogs"]["sources"])):
            expected = sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False,
                                         separators=(",", ":")).encode("utf-8")).hexdigest()
            self.assertEqual(result["digests"][field], expected)

    def test_arbitrary_precision_integer_phase_order_and_file_replay(self):
        instance = original_case()
        instance["phases"][0]["bulk_modulus"]["value"] = 10 ** 110
        instance["phases"][1]["bulk_modulus"]["value"] = 10 ** 110 + 3
        instance["phases"][0]["shear_modulus"]["value"] = 9
        instance["phases"][1]["shear_modulus"]["value"] = 4
        result = build_composite_report(instance)
        self.assertEqual(result["input"]["phases"][1]["bulk_modulus"]["value"] - result["input"]["phases"][0]["bulk_modulus"]["value"], 3)
        self.assertIn(str(10 ** 110 + 3), canonical_json(result))
        self.assertEqual([r["applicability"] for r in result["evaluation"]["evaluations"]],
                         ["violated", "satisfied", "satisfied", "violated", "satisfied", "satisfied", "violated", "violated"])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bundle.json"
            path.write_text(canonical_json(result), encoding="utf-8")
            restored = load_json(path)
        self.assertEqual(restored["input"], instance)
        validate_composite_report(restored)

    def test_invalid_input_rejected_before_engine_evaluation(self):
        for path, value in [(("phases", 0, "bulk_modulus", "value"), True),
                            (("phases", 0, "bulk_modulus", "value"), float("nan")),
                            (("phases", 0, "bulk_modulus", "unit"), "psi"),
                            (("phases", 1, "id"), "A"),
                            (("phases", 1, "volume_fraction"), .9)]:
            instance = original_case()
            set_path(instance, path, value)
            with self.subTest(path=path, value=value), self.assertRaises(ValidationError):
                build_composite_report(instance)
        for unit in (None, [], {}, "psi", 3, True):
            with self.subTest(unit=unit), self.assertRaises(ValidationError):
                build_composite_report(original_case(), unit)

    def test_strict_file_parser_rejects_duplicate_nonfinite_and_underflow(self):
        texts = ['{"input": 1, "input": 2}', '{"value": NaN}', '{"value": Infinity}',
                 '{"value": -Infinity}', '{"value": 1e309}', '{"value": 1e-400}',
                 '{"value": ' + '9' * 400 + '}']
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.json"
            for source in texts:
                with self.subTest(source=source[:40]):
                    path.write_text(source, encoding="utf-8")
                    with self.assertRaises(ValidationError):
                        load_json(path)

    def test_unknown_violated_and_numerical_error_reports_replay(self):
        unknown = original_case(); unknown["conditions"] = {}
        crossed = original_case(); crossed["phases"][0]["shear_modulus"]["value"] = 18
        crossed["phases"][1]["shear_modulus"]["value"] = 6
        violated = original_case(); violated["conditions"]["loading"] = "dynamic"
        violated["phases"][1]["shear_modulus"] = None
        for instance, state in ((unknown, "unknown"), (crossed, "violated"), (violated, "violated")):
            result = build_composite_report(instance)
            self.assertEqual(result["evaluation"]["evaluations"][0]["applicability"], state)
            self.assertEqual(result["evaluation"], evaluate(instance))
            validate_composite_report(result)
        checks = build_composite_report(violated)["evaluation"]["evaluations"][0]["checks"]
        self.assertIn("unknown", {c["state"] for c in checks})
        self.assertIn("violated", {c["state"] for c in checks})
        for value, raw_unit, output_unit in ((1e307, "GPa", "Pa"), (1e-323, "Pa", "GPa")):
            instance = original_case()
            for phase in instance["phases"]:
                for key in ("bulk_modulus", "shear_modulus"):
                    phase[key] = {"value": value, "unit": raw_unit}
            result = build_composite_report(instance, output_unit)
            self.assertTrue(all(r["computation"] == "numerical_range_error" for r in result["evaluation"]["evaluations"]))
            validate_composite_report(result)

    def test_tiny_positive_phase_is_preserved_and_active(self):
        instance = original_case()
        instance["phases"][0]["volume_fraction"] = 1
        instance["phases"][1]["volume_fraction"] = 1e-299
        instance["phases"][1]["bulk_modulus"] = None
        result = build_composite_report(instance)
        self.assertEqual(result["input"]["phases"][1]["volume_fraction"], 1e-299)
        self.assertTrue(all(r["applicability"] == "unknown" for r in result["evaluation"]["evaluations"]))
        validate_composite_report(result)

    def test_normalization_disclosed_without_input_rewrite(self):
        instance = original_case()
        instance["phases"][0]["volume_fraction"] = .2500000000002
        result = build_composite_report(instance)
        self.assertEqual(result["input"], instance)
        self.assertTrue(result["evaluation"]["fraction_normalization"]["performed"])
        self.assertEqual(result["evaluation"]["fraction_normalization"]["original_sum"], "1.0000000000002")
        validate_composite_report(result)
        instance["phases"][0]["volume_fraction"] = .250000000002
        with self.assertRaises(ValidationError):
            build_composite_report(instance)

    def test_mixed_units_phase_reversal_and_dimensionless_output(self):
        original = original_case()
        mixed = copy.deepcopy(original)
        mixed["phases"][0]["bulk_modulus"] = {"value": 12000, "unit": "MPa"}
        mixed["phases"][1]["shear_modulus"] = {"value": 18000000000, "unit": "Pa"}
        mixed["phases"].reverse()
        first = build_composite_report(original)
        second = build_composite_report(mixed)
        self.assertEqual(second["input"], mixed)
        self.assertEqual([r["result"] for r in first["evaluation"]["evaluations"]],
                         [r["result"] for r in second["evaluation"]["evaluations"]])
        mpa = build_composite_report(original, "MPa")
        self.assertEqual(first["evaluation"]["evaluations"][-1]["result"], mpa["evaluation"]["evaluations"][-1]["result"])
        self.assertEqual(mpa["evaluation"]["evaluations"][-1]["result"]["unit"], "1")
        validate_composite_report(second)

    def test_literature_model_input_kept_exact_without_evidence_upgrade(self):
        instance = load_json(ROOT / "examples/literature-epoxy-glass-model.json")
        before = copy.deepcopy(instance)
        result = build_composite_report(instance)
        self.assertEqual(result["input"], before)
        self.assertEqual(result["evaluation"]["input_provenance"], before["provenance"])
        self.assertIn("model_evidence", result["input"]["provenance"])
        self.assertFalse(result["policy"]["independent_scientific_review"])
        self.assertIsNone(result["input"]["provenance"]["model_evidence"]["temperature_k"])
        validate_composite_report(result)

    def test_altered_or_stale_semantic_fields_fail_closed(self):
        base = build_composite_report(original_case())
        mutations = [
            (("instance_id",), "other"),
            (("kind",), "other_report"),
            (("schema_version",), "2.0.0"),
            (("report_version",), "2.0.0"),
            (("engine_version",), "0.1.0"),
            (("instance_schema_version",), "2.0.0"),
            (("evaluation_schema_version",), "2.0.0"),
            (("input", "id"), "other"),
            (("input", "conditions", "loading"), "dynamic"),
            (("output_unit",), "MPa"),
            (("evaluation", "instance_id"), "other"),
            (("evaluation", "schema_version"), "2.0.0"),
            (("evaluation", "evaluations", 0, "result", "lower"), 25.0),
            (("evaluation", "evaluations", 0, "result", "unit"), "MPa"),
            (("evaluation", "evaluations", 0, "rule_id"), "invented_rule"),
            (("evaluation", "evaluations", 0, "checks", 0, "observed"), 2),
            (("evaluation", "evaluations", 6, "dependencies", "instance_id"), "other"),
            (("evaluation", "evaluations", 6, "dependencies", "claim_ids"), ["reuss_bulk", "reuss_shear"]),
            (("evaluation", "evaluations", 6, "dependencies", "joint_attainability"), "asserted"),
            (("catalogs", "claims", "schema_version"), "2.0.0"),
            (("catalogs", "claims", "records", 0, "rule_id"), "invented_rule"),
            (("catalogs", "claims", "records", 0, "verification", "independent_scientific_review"), True),
            (("catalogs", "claims", "records", 0, "verification", "gaps"), []),
            (("catalogs", "claims", "records", 0, "evidence", 1, "locator"), "invented equation"),
            (("catalogs", "sources", "records", 0, "read_status"), "fully_verified"),
            (("catalogs", "sources", "records", 0, "urls"), ["javascript:alert(1)"]),
            (("catalogs", "sources", "records", 0, "license", "status"), "public_domain"),
            (("catalogs", "unresolved_source_ids"), ["invented"]),
            (("policy", "hash_scope"), "authenticates_authorship"),
            (("policy", "independent_scientific_review"), True),
            (("digests", "input"), "0" * 64),
        ]
        for path, value in mutations:
            result = copy.deepcopy(base)
            set_path(result, path, value)
            before = copy.deepcopy(result)
            with self.subTest(path=path), self.assertRaises(CompositeReplayError):
                validate_composite_report(result)
            self.assertEqual(result, before)

    def test_collection_and_cross_case_substitution_is_mismatch(self):
        base = build_composite_report(original_case())
        alternatives = []
        reordered = copy.deepcopy(base)
        reordered["catalogs"]["claims"]["records"].reverse()
        alternatives.append(reordered)
        omitted_source = copy.deepcopy(base)
        omitted_source["catalogs"]["sources"]["records"].pop()
        alternatives.append(omitted_source)
        extra_source = copy.deepcopy(base)
        used = {r["id"] for r in extra_source["catalogs"]["sources"]["records"]}
        extra_source["catalogs"]["sources"]["records"].append(next(
            r for r in read_catalog("sources")["records"] if r["id"] not in used))
        alternatives.append(extra_source)
        another = original_case()
        another["id"] = "other-instance"
        another["phases"][0]["volume_fraction"] = .5
        another["phases"][1]["volume_fraction"] = .5
        replaced_result = copy.deepcopy(base)
        replaced_result["evaluation"]["evaluations"][6] = build_composite_report(another)["evaluation"]["evaluations"][6]
        alternatives.append(replaced_result)
        for result in alternatives:
            with self.subTest(result=result["instance_id"]), self.assertRaises(CompositeReplayError):
                validate_composite_report(result)

    def test_numeric_json_representation_is_not_silently_coerced(self):
        result = build_composite_report(original_case())
        # Python equality treats 24 == 24.0 and False == 0. The complete
        # canonical JSON comparison retains the declared representation.
        result["evaluation"]["evaluations"][1]["result"]["lower"] = 24
        with self.assertRaises(CompositeReplayError):
            validate_composite_report(result)
        self.assertNotEqual(canonical_json(False), canonical_json(0))

    def test_valid_fraction_change_without_rebuild_is_mismatch(self):
        result = build_composite_report(original_case())
        result["input"]["phases"][0]["volume_fraction"] = .4
        result["input"]["phases"][1]["volume_fraction"] = .6
        with self.assertRaises(CompositeReplayError):
            validate_composite_report(result)

    def test_hashes_do_not_replace_semantic_rebuild(self):
        result = build_composite_report(original_case())
        result["evaluation"]["evaluations"][0]["result"]["lower"] = 1.0
        result["digests"]["evaluation"] = sha256(canonical_json(result["evaluation"]).encode("utf-8")).hexdigest()
        with self.assertRaises(CompositeReplayError):
            validate_composite_report(result)
        replacement = original_case(); replacement["id"] = "entirely-new-consistent-case"
        validate_composite_report(build_composite_report(replacement))

    def test_closed_root_and_deep_object_shapes_reject_malformed(self):
        base = build_composite_report(original_case())
        objects = [(), ("evaluation",), ("evaluation", "fraction_normalization"),
                   ("evaluation", "evaluations", 0), ("evaluation", "evaluations", 0, "checks", 0),
                   ("evaluation", "evaluations", 0, "result"),
                   ("evaluation", "evaluations", 6, "dependencies"),
                   ("catalogs",), ("catalogs", "claims"), ("catalogs", "sources"),
                   ("catalogs", "claims", "records", 0),
                   ("catalogs", "claims", "records", 0, "evidence", 0),
                   ("catalogs", "claims", "records", 0, "verification"),
                   ("catalogs", "sources", "records", 0),
                   ("catalogs", "sources", "records", 0, "license"),
                   ("catalogs", "sources", "records", 0, "provenance"),
                   ("policy",), ("digests",)]
        for path in objects:
            result = copy.deepcopy(base)
            target = result
            for key in path:
                target = target[key]
            target["unrecognized"] = True
            with self.subTest(path=path), self.assertRaises(ValidationError):
                validate_composite_report(result)
        for field in base:
            result = copy.deepcopy(base); del result[field]
            with self.subTest(missing=field), self.assertRaises(ValidationError):
                validate_composite_report(result)

    def test_malformed_deep_types_never_escape_as_raw_exceptions(self):
        base = build_composite_report(original_case())
        mutations = [
            (("input",), []), (("output_unit",), []), (("evaluation",), None),
            (("evaluation", "input_provenance"), []),
            (("evaluation", "evaluations"), {}),
            (("evaluation", "evaluations", 0), 3),
            (("evaluation", "evaluations", 0, "checks"), None),
            (("evaluation", "evaluations", 0, "result", "lower"), True),
            (("evaluation", "evaluations", 0, "result", "lower"), float("inf")),
            (("evaluation", "evaluations", 0, "result", "lower"), 10 ** 400),
            (("evaluation", "evaluations", 6, "dependencies", "claim_ids"), "HS"),
            (("catalogs", "claims", "records", 0, "evidence", 0, "locator"), 2),
            (("catalogs", "claims", "records", 0, "verification", "independent_scientific_review"), 0),
            (("catalogs", "claims", "records", 0, "required_assumptions"), []),
            (("catalogs", "sources", "records", 0, "year"), True),
            (("catalogs", "sources", "records", 0, "license"), []),
            (("policy",), []), (("digests", "input"), "invalid"),
        ]
        for path, value in mutations:
            result = copy.deepcopy(base)
            set_path(result, path, value)
            with self.subTest(path=path), self.assertRaises(ValidationError):
                validate_composite_report(result)
        for bad in (None, [], True, "report", {1: "non-string key"}):
            with self.subTest(root=bad), self.assertRaises(ValidationError):
                validate_composite_report(bad)

    def test_nonjson_cycles_depth_and_invalid_unicode_rejected(self):
        cycle = {}; cycle["self"] = cycle
        deep = []
        for _ in range(140):
            deep = [deep]
        for value in (cycle, deep, {"key": "\ud800"}, {"\ud800": 1}, {"tuple": (1, 2)}, {"set": {1, 2}}):
            with self.assertRaises(ValidationError):
                canonical_json(value)
        # Multiple references to a shared JSON object are normal for evaluate.
        shared = {"x": 1}
        self.assertEqual(canonical_json([shared, shared]), '[{"x":1},{"x":1}]')

    def test_replay_runs_engine_not_just_schema_or_digest_checks(self):
        result = build_composite_report(original_case())
        before = copy.deepcopy(result)
        with patch("materials_boundaries.composite.evaluate", wraps=evaluate) as call:
            self.assertIsNone(validate_composite_report(result))
        self.assertEqual(call.call_count, 1)
        self.assertEqual(result, before)

    def test_report_schema_local_registry_formats_and_source_classification(self):
        try:
            from jsonschema import Draft202012Validator, FormatChecker
            from referencing import Registry, Resource
        except ImportError:
            self.skipTest("optional schema-test dependency is not installed")
        schemas = [load_json(path) for path in (ROOT / "schemas").glob("*.schema.json")]
        by_name = {schema["$id"]: schema for schema in schemas}

        def no_remote(uri):
            self.fail("report schema attempted a nonlocal reference: " + uri)

        # Same local resource/format configuration used by validate_catalogs;
        # report validation must not fetch schemas or require a network source.
        registry = Registry(retrieve=no_remote).with_resources(
            (schema["$id"], Resource.from_contents(schema)) for schema in schemas)
        schema = by_name["urn:materials-boundaries:schema:composite-report:1.0.0"]
        validator = Draft202012Validator(schema, format_checker=FormatChecker(), registry=registry)
        report = build_composite_report(original_case())
        self.assertEqual(list(validator.iter_errors(report)), [])
        for kind in ("claims", "sources"):
            catalog_schema = load_json(ROOT / "schemas" / (kind + ".schema.json"))
            original = Draft202012Validator(catalog_schema, format_checker=FormatChecker(), registry=registry)
            self.assertEqual(list(original.iter_errors(report["catalogs"][kind])), [])
        for path, value in [
            (("catalogs", "claims", "records", 0, "evaluation_support"), "catalog_only"),
            (("catalogs", "claims", "records", 0, "claim_type"), "model_estimate"),
            (("catalogs", "claims", "records", 0, "quantity_dimension"), "speed_squared"),
            (("catalogs", "sources", "records", 0, "provenance", "curation_date"), "not-a-date"),
        ]:
            changed = copy.deepcopy(report)
            set_path(changed, path, value)
            with self.subTest(path=path):
                self.assertFalse(validator.is_valid(changed))
        if "uri" in FormatChecker().checkers:
            changed = copy.deepcopy(report)
            changed["catalogs"]["sources"]["records"][0]["urls"] = ["not a URI"]
            self.assertFalse(validator.is_valid(changed))

    def test_independent_composite_schema_and_unchanged_existing_schemas(self):
        try:
            from jsonschema import Draft202012Validator
        except ImportError:
            self.skipTest("optional schema-test dependency is not installed")
        schema = load_json(ROOT / "schemas/composite-report.schema.json")
        Draft202012Validator.check_schema(schema)
        validator = Draft202012Validator(schema)
        for name in ("synthetic-two-phase", "unknown-isotropy", "anisotropic-constituent", "literature-epoxy-glass-model"):
            instance = load_json(ROOT / "examples" / (name + ".json"))
            result = build_composite_report(instance)
            self.assertEqual(list(validator.iter_errors(result)), [])
        instance_schema = copy.deepcopy(load_json(ROOT / "schemas/instance.schema.json"))
        evaluation_schema = copy.deepcopy(load_json(ROOT / "schemas/evaluation.schema.json"))
        for embedded in (instance_schema, evaluation_schema):
            for key in ("$id", "$schema", "title"):
                embedded.pop(key, None)
        self.assertEqual(schema["$defs"]["instance"], instance_schema)
        self.assertEqual(schema["$defs"]["evaluation"], evaluation_schema)


if __name__ == "__main__":
    unittest.main()
