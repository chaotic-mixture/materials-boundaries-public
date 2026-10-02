"""Successful meta-check reuse must not weaken fresh, offline validation."""
import copy
from contextlib import contextmanager
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

from jsonschema import SchemaError
from jsonschema.exceptions import FormatError, ValidationError as SchemaValidationError

from materials_boundaries.validation import ValidationError
from scripts import validate_catalogs as v


@contextmanager
def meta_calls():
    """Observe actual checks without replacing (and invalidating) their code."""
    code = v.Draft202012Validator.check_schema.__func__.__code__
    calls = []
    previous = sys.getprofile()

    def observe(frame, event, arg):
        if event == "call" and frame.f_code is code:
            calls.append(frame.f_locals["schema"])

    sys.setprofile(observe)
    try:
        yield calls
    finally:
        sys.setprofile(previous)


class SchemaMetaCacheTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = v.load_catalogs(v.ROOT / "materials_boundaries/data")

    def setUp(self):
        v._SCHEMA_META_SUCCESSES.clear()
        self.catalogs = copy.deepcopy(self.original)
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.addCleanup(v._SCHEMA_META_SUCCESSES.clear)
        self.schemas = Path(self.temporary.name) / "schemas"
        shutil.copytree(v.ROOT / "schemas", self.schemas)

    def validate(self):
        return v.validate_catalogs(self.catalogs, self.schemas)

    def change_schema(self, kind, change):
        path = self.schemas / f"{kind}.schema.json"
        schema = v.load_json(path)
        change(schema)
        path.write_text(json.dumps(schema), encoding="utf-8")

    def outcome(self):
        try:
            return (None, self.validate())
        except Exception as error:
            return (type(error), str(error))

    def assert_rejection_matches_uncached(self):
        cached = self.outcome()
        with patch.object(v, "_META_CHECK_CONFIGURATION", None):
            uncached = self.outcome()
        self.assertIsNotNone(cached[0])
        self.assertEqual(cached, uncached)
        return cached

    def test_warm_success_keeps_input_and_results_and_strict_loads_fresh(self):
        before = copy.deepcopy(self.catalogs)
        files = {p.name: p.read_bytes() for p in self.schemas.iterdir()}
        with patch.object(v, "load_json", wraps=v.load_json) as load, meta_calls() as calls:
            first = self.validate()
            second = self.validate()
        self.assertEqual(len(calls), len(v.CATALOGS))
        self.assertEqual(load.call_count, 2 * len(v.CATALOGS))
        self.assertEqual(first, second)
        self.assertEqual(self.catalogs, before)
        self.assertEqual(files, {p.name: p.read_bytes() for p in self.schemas.iterdir()})
        self.assertEqual(len(v._SCHEMA_META_SUCCESSES), len(v.CATALOGS))

    def test_changed_contents_same_size_and_mtime_do_not_reuse_success(self):
        self.validate()
        path = self.schemas / "claims.schema.json"
        before = path.stat()
        raw = path.read_text(encoding="utf-8")
        changed = raw.replace('"type": "object"', '"type": "mystic"', 1)
        self.assertNotEqual(raw, changed)
        path.write_text(changed, encoding="utf-8")
        os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns))
        self.assertEqual(path.stat().st_size, before.st_size)
        self.assertEqual(path.stat().st_mtime_ns, before.st_mtime_ns)
        self.assertIs(self.assert_rejection_matches_uncached()[0], SchemaError)

    def test_different_root_uses_actual_contents(self):
        self.validate()
        other = Path(self.temporary.name) / "other"
        shutil.copytree(self.schemas, other)
        self.schemas = other
        self.change_schema("claims", lambda s: s.update(type="mystic"))
        self.assertIs(self.assert_rejection_matches_uncached()[0], SchemaError)

    def test_patched_loader_output_is_used_even_when_files_are_unchanged(self):
        self.validate()
        original_load = v.load_json

        def changed_load(path):
            schema = original_load(path)
            if path.name == "claims.schema.json":
                schema["type"] = "mystic"
            return schema

        with patch.object(v, "load_json", side_effect=changed_load):
            self.assertIs(self.assert_rejection_matches_uncached()[0], SchemaError)

    def test_non_json_loader_shapes_cannot_alias_plain_json_cache_keys(self):
        v._check_schema({"required": ["name"]})
        with self.assertRaises(SchemaError):
            v._check_schema({"required": ("name",)})

    def test_failed_meta_checks_are_never_cached(self):
        schema = {"type": "not-a-type"}
        with meta_calls() as calls:
            for _ in range(2):
                with self.assertRaises(SchemaError):
                    v._check_schema(schema)
        self.assertEqual(len(calls), 2)
        self.assertEqual(len(v._SCHEMA_META_SUCCESSES), 0)

    def test_cache_is_bounded_and_oversized_keys_are_not_retained(self):
        with patch.object(v, "_SCHEMA_META_CACHE_LIMIT", 2):
            for title in ("one", "two", "three"):
                v._check_schema({"title": title})
            self.assertEqual(len(v._SCHEMA_META_SUCCESSES), 2)
            with meta_calls() as calls:
                v._check_schema({"title": "one"})
            self.assertEqual(len(calls), 1)
        v._SCHEMA_META_SUCCESSES.clear()
        with patch.object(v, "_SCHEMA_META_CACHE_KEY_LIMIT", 4), meta_calls() as calls:
            v._check_schema({"title": "large"})
            v._check_schema({"title": "large"})
        self.assertEqual(len(calls), 2)
        self.assertFalse(v._SCHEMA_META_SUCCESSES)

    def test_changed_catalogs_uri_and_date_still_fail_after_warming(self):
        self.validate()
        for field, value in (("urls", ["not a URI"]), ("date", "2026-02-30"), ("name", None)):
            with self.subTest(field=field):
                self.catalogs = copy.deepcopy(self.original)
                if field == "date":
                    self.catalogs["sources"]["records"][-1]["provenance"]["curation_date"] = value
                elif field == "name":
                    self.catalogs["claims"]["records"][0].pop("name")
                else:
                    self.catalogs["sources"]["records"][-1][field] = value
                self.assertIs(self.assert_rejection_matches_uncached()[0], v.CatalogValidationError)

    def test_runtime_format_checker_is_fresh_and_missing_uri_fails(self):
        self.validate()
        checker = v.FormatChecker()
        checker.checkers.pop("uri")
        with patch.object(v, "FormatChecker", return_value=checker):
            with self.assertRaisesRegex(v.CatalogValidationError, "required format checkers unavailable: uri"):
                self.validate()

    def test_changed_runtime_uri_checker_is_used(self):
        self.validate()
        checker = v.FormatChecker()
        checker.checkers["uri"] = (lambda _: False, ())
        with patch.object(v, "FormatChecker", return_value=checker):
            self.assertIs(self.assert_rejection_matches_uncached()[0], v.CatalogValidationError)

    def test_new_unavailable_format_fails_before_reuse(self):
        self.validate()
        self.change_schema("sources", lambda s: s.update(format="not-installed-format"))
        with self.assertRaisesRegex(v.CatalogValidationError, "required format checkers unavailable: not-installed-format"):
            self.validate()

    def test_changed_local_reference_target_is_fresh(self):
        self.validate()
        self.change_schema("temperature_models", lambda s: s["$defs"]["synthetic_model"]["properties"]["name"].update(minLength=10000))
        self.assertIs(self.assert_rejection_matches_uncached()[0], v.CatalogValidationError)

    def test_cross_schema_reference_target_is_reloaded_with_fresh_registry(self):
        claims_id = v.load_json(self.schemas / "claims.schema.json")["$id"]
        self.change_schema("claims", lambda s: s.setdefault("$defs", {}).update(cache_target=True))
        self.change_schema("sources", lambda s: s.update(allOf=[{"$ref": claims_id + "#/$defs/cache_target"}]))
        self.validate()
        self.change_schema("claims", lambda s: s["$defs"].update(cache_target=False))
        self.assertIs(self.assert_rejection_matches_uncached()[0], v.CatalogValidationError)

    def test_missing_local_and_remote_references_stay_fail_closed(self):
        self.validate()
        for reference in ("#/$defs/missing", "https://schema-cache-test.invalid/never-fetch"):
            with self.subTest(reference=reference):
                self.change_schema("temperature_models", lambda s: s["properties"]["records"]["items"].update({"$ref": reference}))
                with patch.object(v, "_no_remote_reference", wraps=v._no_remote_reference) as retrieve:
                    failure = self.assert_rejection_matches_uncached()
                self.assertIn(reference, failure[1])
                self.assertEqual(retrieve.call_count, 2 if reference.startswith("https:") else 0)

    def test_duplicate_nonfinite_overflow_and_underflow_schemas_still_reject(self):
        self.validate()
        path = self.schemas / "claims.schema.json"
        for payload in ('{"type":"object","type":"object"}', '{"value":NaN}',
                        '{"value":Infinity}', '{"value":-Infinity}',
                        '{"value":1e999}', '{"value":1e-999}'):
            with self.subTest(payload=payload):
                path.write_text(payload, encoding="utf-8")
                self.assertIs(self.assert_rejection_matches_uncached()[0], ValidationError)

    def test_replaced_schema_check_function_bypasses_warm_success(self):
        schema = {"type": "object"}
        v._check_schema(schema)
        calls = []

        def changed(cls, schema):
            calls.append(schema)
            raise SchemaError("replacement check ran")

        with patch.object(v.Draft202012Validator, "check_schema", classmethod(changed)):
            for _ in range(2):
                with self.assertRaisesRegex(SchemaError, "replacement check ran"):
                    v._check_schema(schema)
        self.assertEqual(len(calls), 2)

    def test_custom_stateful_schema_checker_success_is_not_cached(self):
        schema = {"type": "object"}
        v._check_schema(schema)
        calls = []

        def changed(cls, schema):
            calls.append(schema)
            if len(calls) > 1:
                raise SchemaError("state changed")

        with patch.object(v.Draft202012Validator, "check_schema", classmethod(changed)):
            self.assertIsNone(v._meta_check_configuration())
            v._check_schema(schema)
            with self.assertRaisesRegex(SchemaError, "state changed"):
                v._check_schema(schema)
        self.assertEqual(len(calls), 2)

    def test_replaced_schema_check_code_bypasses_warm_success(self):
        schema = {"type": "object"}
        v._check_schema(schema)

        def changed(cls, schema, format_checker=None):
            raise RuntimeError("replacement code ran")

        function = v.Draft202012Validator.check_schema.__func__
        original = function.__code__
        try:
            function.__code__ = changed.__code__
            with self.assertRaisesRegex(RuntimeError, "replacement code ran"):
                v._check_schema(schema)
        finally:
            function.__code__ = original

    def test_changed_meta_iterator_default_bypasses_warm_success(self):
        schema = {"type": "object"}
        v._check_schema(schema)
        function = v.Draft202012Validator.iter_errors
        original = function.__defaults__
        try:
            function.__defaults__ = ({"type": "null"},)
            with self.assertWarns(DeprecationWarning), self.assertRaises(SchemaError):
                v._check_schema(schema)
        finally:
            function.__defaults__ = original

    def test_changed_meta_format_mapping_bypasses_warm_success(self):
        schema = {"$id": "urn:cache:test", "type": "object"}
        v._check_schema(schema)
        checker = v.Draft202012Validator.FORMAT_CHECKER
        with patch.dict(checker.checkers, {"uri-reference": (lambda _: False, ())}):
            for _ in range(2):
                with self.assertRaises(SchemaError):
                    v._check_schema(schema)

    def test_changed_meta_format_instance_method_bypasses_warm_success(self):
        schema = {"$id": "urn:cache:test", "type": "object"}
        v._check_schema(schema)
        checker = v.Draft202012Validator.FORMAT_CHECKER
        with patch.object(checker, "check", side_effect=FormatError("changed meta-format method")):
            with self.assertRaises(SchemaError):
                v._check_schema(schema)

    def test_changed_meta_format_default_bypasses_warm_success(self):
        schema = {"$id": "urn:cache:test", "type": "object"}
        v._check_schema(schema)
        checker = v.FormatChecker()
        checker.checkers["uri-reference"] = (lambda _: False, ())
        function = v.Draft202012Validator.check_schema.__func__
        original = function.__defaults__
        try:
            function.__defaults__ = (checker,)
            with self.assertRaises(SchemaError):
                v._check_schema(schema)
        finally:
            function.__defaults__ = original

    def test_changed_meta_schema_bypasses_warm_success(self):
        schema = {"type": "object"}
        v._check_schema(schema)
        with patch.dict(v.Draft202012Validator.META_SCHEMA, {"not": {}}):
            with self.assertRaises(SchemaError):
                v._check_schema(schema)

    def test_changed_meta_keyword_implementation_bypasses_warm_success(self):
        schema = {"type": "object"}
        v._check_schema(schema)

        def changed(*args):
            yield SchemaValidationError("changed type keyword")

        with patch.dict(v.Draft202012Validator.VALIDATORS, {"type": changed}):
            with self.assertRaisesRegex(SchemaError, "changed type keyword"):
                v._check_schema(schema)

    def test_runtime_errors_are_fully_enumerated_in_original_order(self):
        self.validate()
        self.catalogs["claims"]["records"][0].pop("name")
        expected = self.outcome()
        original_iter = v.Draft202012Validator.iter_errors
        completed = []

        def observe(validator, instance, *args, **kwargs):
            yield from original_iter(validator, instance, *args, **kwargs)
            if instance is self.catalogs["claims"]:
                completed.append(True)
                yield SchemaValidationError("later error must not replace first")

        with patch.object(v.Draft202012Validator, "iter_errors", observe):
            self.assertEqual(self.outcome(), expected)
        self.assertEqual(completed, [True])


if __name__ == "__main__":
    unittest.main()
