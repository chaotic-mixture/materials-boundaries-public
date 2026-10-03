"""Characterize catalog presentation while bounding locale reuse to one call."""
import copy
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

from materials_boundaries.catalog import query_catalog, read_catalog
from materials_boundaries.catalog_output import render_catalog
from materials_boundaries.i18n import LANGUAGES, translate

ROOT = Path(__file__).resolve().parents[1]
EMPTY = {"schema_version": "1.0.0", "records": []}
KEYS = ("catalog_sources", "catalog_count", "catalog_empty",
        "catalog_original_notice", "catalog_evidence_notice", "translation_review_notice")


def locale(token):
    return {"languages": {"en": {key: token + ":" + key for key in KEYS}}}


def empty_text(token):
    return "\n".join((token + ":catalog_sources", token + ":catalog_count: 0",
                      token + ":catalog_empty", "", token + ":catalog_original_notice",
                      token + ":catalog_evidence_notice", token + ":translation_review_notice"))


class CatalogTranslationSnapshotTests(unittest.TestCase):
    def test_original_catalog_text_bytes_and_canonical_json_in_four_languages(self):
        golden = json.loads((ROOT / "tests/fixtures/catalog_translation_v0201.json").read_text())
        for kind, expected in golden["catalogs"].items():
            catalog = query_catalog(kind)
            records = {record["id"]: record for record in catalog["records"]}
            catalog["records"] = [records[identifier] for identifier in expected["record_ids"]]
            for key, identifiers in expected["metadata_ids"].items():
                metadata = {item["id"]: item for item in catalog[key]}
                catalog[key] = [metadata[identifier] for identifier in identifiers]
            # Valid contributions may append evidence to an existing claim.
            # Require every original entry unchanged, then select those entries
            # in baseline order for this exact historical-output comparison.
            for record in catalog["records"]:
                if record["id"] in expected["evidence_sha256"]:
                    evidence = {hashlib.sha256(json.dumps(item, sort_keys=True, separators=(",", ":")).encode()).hexdigest(): item
                                for item in record["evidence"]}
                    record["evidence"] = [evidence[digest] for digest in expected["evidence_sha256"][record["id"]]]
            before = copy.deepcopy(catalog)
            for language in LANGUAGES:
                with self.subTest(kind=kind, language=language):
                    text = render_catalog(catalog, kind, language)
                    self.assertEqual(hashlib.sha256(text.encode()).hexdigest(), expected["text_sha256"][language])
                    self.assertEqual(catalog, before)
                    # Only the observation envelope advances in v0.22; the
                    # frozen v0.20.1 payload/text must remain byte-identical.
                    historic = copy.deepcopy(catalog)
                    if kind == "observations":
                        self.assertEqual(historic["schema_version"], "1.3.0")
                        historic["schema_version"] = "1.2.0"
                    serialized = json.dumps(historic, ensure_ascii=False, indent=2)
                    self.assertEqual(hashlib.sha256(serialized.encode()).hexdigest(), expected["json_sha256"])

    def test_one_fresh_locale_read_per_full_catalog_render(self):
        for kind in ("claims", "sources", "observations"):
            catalog = read_catalog(kind)
            for language in LANGUAGES:
                with self.subTest(kind=kind, language=language):
                    with patch("materials_boundaries.i18n.read_catalog", wraps=read_catalog) as load:
                        first = render_catalog(catalog, kind, language)
                        load.assert_called_once_with("locales")
                        second = render_catalog(catalog, kind, language)
                        self.assertEqual(load.call_count, 2)
                        self.assertEqual(first, second)

    def test_empty_selection_still_reads_and_renders_all_labels(self):
        with patch("materials_boundaries.i18n.read_catalog", return_value=locale("empty")) as load:
            self.assertEqual(render_catalog(EMPTY, "sources"), empty_text("empty"))
            load.assert_called_once_with("locales")

    def test_changed_patched_loader_is_observed_between_calls_and_languages(self):
        snapshots = [locale(language) for language in LANGUAGES]
        with patch("materials_boundaries.i18n.read_catalog", side_effect=snapshots) as load:
            for language in LANGUAGES:
                self.assertEqual(render_catalog(EMPTY, "sources", language), empty_text(language))
            self.assertEqual(load.call_count, len(LANGUAGES))

    def test_same_length_same_mtime_locale_edit_is_observed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "data").mkdir()
            path = root / "data/locales.json"
            path.write_text(json.dumps(locale("first")), encoding="utf-8")
            original = path.stat()
            with patch("materials_boundaries.catalog.files", return_value=root):
                self.assertEqual(render_catalog(EMPTY, "sources"), empty_text("first"))
                path.write_text(json.dumps(locale("later")), encoding="utf-8")
                os.utime(path, ns=(original.st_atime_ns, original.st_mtime_ns))
                self.assertEqual(path.stat().st_size, original.st_size)
                self.assertEqual(path.stat().st_mtime_ns, original.st_mtime_ns)
                self.assertEqual(render_catalog(EMPTY, "sources"), empty_text("later"))

    def test_malformed_edit_after_success_is_not_hidden(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "data").mkdir()
            path = root / "data/locales.json"
            path.write_text(json.dumps(locale("first")), encoding="utf-8")
            original = path.stat()
            with patch("materials_boundaries.catalog.files", return_value=root):
                self.assertEqual(render_catalog(EMPTY, "sources"), empty_text("first"))
                path.write_bytes(b"{" + b" " * (original.st_size - 1))
                os.utime(path, ns=(original.st_atime_ns, original.st_mtime_ns))
                with self.assertRaises(json.JSONDecodeError):
                    render_catalog(EMPTY, "sources")
                path.write_text(json.dumps(locale("later")), encoding="utf-8")
                self.assertEqual(render_catalog(EMPTY, "sources"), empty_text("later"))

    def test_locale_json_loader_compatibility_is_not_silently_tightened(self):
        # Locale loading historically uses json.loads, unlike strict scientific
        # input loaders. Duplicate keys are last-wins and nonfinite values parse.
        cases = [
            ('{"languages":{"en":{"catalog_sources":"first","catalog_sources":"last"}}}', "last"),
            ('{"languages":{"en":{"catalog_count":NaN}}}', "[missing:catalog_sources]"),
            ('{"languages":{"en":{"catalog_count":Infinity}}}', "[missing:catalog_sources]"),
            ('{"languages":{"en":{"catalog_count":-Infinity}}}', "[missing:catalog_sources]"),
        ]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "data").mkdir()
            path = root / "data/locales.json"
            for content, title in cases:
                with self.subTest(content=content):
                    path.write_text(content, encoding="utf-8")
                    with patch("materials_boundaries.catalog.files", return_value=root):
                        output = render_catalog(EMPTY, "sources")
                        self.assertEqual(output.splitlines()[0], title)
                        if "NaN" in content:
                            self.assertEqual(output.splitlines()[1], "nan: 0")
                        elif "-Infinity" in content:
                            self.assertEqual(output.splitlines()[1], "-inf: 0")
                        elif "Infinity" in content:
                            self.assertEqual(output.splitlines()[1], "inf: 0")

    def test_malformed_locale_bytes_keep_exact_loader_errors(self):
        for content in (b"{", b"[]", b'{"languages":[]}', b'{"languages":null}', b"\xff"):
            with self.subTest(content=content), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                (root / "data").mkdir()
                (root / "data/locales.json").write_bytes(content)
                with patch("materials_boundaries.catalog.files", return_value=root):
                    with self.assertRaises(Exception) as standalone:
                        translate("catalog_sources")
                    with self.assertRaises(type(standalone.exception)) as rendered:
                        render_catalog(EMPTY, "sources")
                    self.assertEqual(str(rendered.exception), str(standalone.exception))

    def test_unknown_language_is_rejected_before_locale_read(self):
        with patch("materials_boundaries.i18n.read_catalog", side_effect=AssertionError("must not read")) as load:
            with self.assertRaisesRegex(ValueError, "^unsupported language: fr$"):
                render_catalog(EMPTY, "sources", "fr")
            load.assert_not_called()

    def test_scientific_validation_precedes_language_and_locale_errors(self):
        observation = copy.deepcopy(next(record for record in read_catalog("observations")["records"]
                                         if record.get("method_family") == "bertolazzi_2011_mos2_monolayer_indentation_v1"))
        observation["quantity"] = "not_a_quantity"
        claim = copy.deepcopy(next(record for record in read_catalog("claims")["records"] if "bulk_wave_contract" in record))
        del claim["bulk_wave_contract"]
        for kind, record in (("observations", observation), ("claims", claim)):
            with self.subTest(kind=kind):
                with patch("materials_boundaries.i18n.read_catalog", side_effect=AssertionError("must not read")) as load:
                    with self.assertRaises(ValueError) as error:
                        render_catalog({"records": [record]}, kind, "fr")
                    self.assertNotIn("unsupported language", str(error.exception))
                    load.assert_not_called()

    def test_missing_records_and_claim_dependency_loading_keep_error_precedence(self):
        with patch("materials_boundaries.i18n.read_catalog", side_effect=RuntimeError("locale read")) as load:
            for kind in ("claims", "observations"):
                with self.subTest(kind=kind), self.assertRaises(KeyError) as error:
                    render_catalog({}, kind, "fr")
                self.assertEqual(error.exception.args, ("records",))
            load.assert_not_called()
            with patch("materials_boundaries.catalog_output.read_catalog", side_effect=RuntimeError("claims read")):
                with self.assertRaisesRegex(RuntimeError, "^claims read$"):
                    render_catalog(EMPTY, "claims", "fr")
            load.assert_not_called()
            # Source rendering historically asks for its title before records.
            with self.assertRaisesRegex(RuntimeError, "^locale read$"):
                render_catalog({}, "sources")

    def test_source_and_claim_catalog_reads_remain_fresh_and_in_order(self):
        events = []

        def catalogs(name):
            events.append(name)
            return read_catalog(name)

        with patch("materials_boundaries.catalog_output.read_catalog", side_effect=catalogs), \
             patch("materials_boundaries.i18n.read_catalog", side_effect=catalogs):
            for _ in range(2):
                render_catalog(EMPTY, "claims")
        self.assertEqual(events, ["claims", "locales", "sources"] * 2)

    def test_fallback_missing_key_and_unknown_status_remain_visible(self):
        fake = {"languages": {"en": {"catalog_sources": "English title"}, "ja": {"catalog_count": "Count"}}}
        with patch("materials_boundaries.i18n.read_catalog", return_value=fake):
            text = render_catalog(EMPTY, "sources", "ja")
            self.assertTrue(text.startswith("English title\nCount: 0\n[missing:catalog_empty]"))
            source = copy.deepcopy(read_catalog("sources")["records"][0])
            source["read_status"] = "future_untranslated_status"
            self.assertIn("[missing:catalog_read_status]: future_untranslated_status", render_catalog({"records": [source]}, "sources", "ja"))

    def test_eager_english_fallback_shape_error_is_preserved(self):
        fake = {"languages": {"en": [], "ja": {"catalog_sources": "present"}}}
        with patch("materials_boundaries.i18n.read_catalog", return_value=fake):
            with self.assertRaises(AttributeError) as standalone:
                translate("catalog_sources", "ja")
            with self.assertRaises(AttributeError) as rendered:
                render_catalog(EMPTY, "sources", "ja")
            self.assertEqual(str(rendered.exception), str(standalone.exception))

    def test_nested_render_during_locale_load_has_its_own_snapshot(self):
        nested = []
        entered = False

        def load(name):
            nonlocal entered
            self.assertEqual(name, "locales")
            if not entered:
                entered = True
                nested.append(render_catalog(EMPTY, "sources", "ja"))
                return locale("outer")
            return locale("inner")

        with patch("materials_boundaries.i18n.read_catalog", side_effect=load) as mocked:
            self.assertEqual(render_catalog(EMPTY, "sources"), empty_text("outer"))
            self.assertEqual(nested, [empty_text("inner")])
            self.assertEqual(mocked.call_count, 2)

    def test_nested_render_after_first_label_cannot_replace_outer_snapshot(self):
        nested = []

        def catalogs(name):
            self.assertEqual(name, "sources")
            nested.append(render_catalog(EMPTY, "sources", "de"))
            return {"records": []}

        with patch("materials_boundaries.i18n.read_catalog", side_effect=[locale("outer"), locale("inner")]) as load, \
             patch("materials_boundaries.catalog_output.read_catalog", side_effect=catalogs):
            outer = render_catalog(EMPTY, "observations")
        self.assertEqual(nested, [empty_text("inner")])
        self.assertIn("outer:translation_review_notice", outer)
        self.assertNotIn("inner:", outer)
        self.assertEqual(load.call_count, 2)

    def test_concurrent_renders_do_not_share_snapshots(self):
        barrier = threading.Barrier(len(LANGUAGES))
        current = threading.local()

        def load(name):
            self.assertEqual(name, "locales")
            barrier.wait(timeout=10)
            return locale(current.language)

        def render(language):
            current.language = language
            return render_catalog(EMPTY, "sources", language)

        with patch("materials_boundaries.i18n.read_catalog", side_effect=load) as mocked:
            with ThreadPoolExecutor(max_workers=len(LANGUAGES)) as executor:
                outputs = list(executor.map(render, LANGUAGES))
        self.assertEqual(outputs, [empty_text(language) for language in LANGUAGES])
        self.assertEqual(mocked.call_count, len(LANGUAGES))

    def test_standalone_translation_still_reads_for_every_call(self):
        with patch("materials_boundaries.i18n.read_catalog", side_effect=[locale("first"), locale("later")]) as load:
            self.assertEqual(translate("catalog_sources"), "first:catalog_sources")
            self.assertEqual(translate("catalog_sources"), "later:catalog_sources")
            self.assertEqual(load.call_count, 2)

    def test_render_does_not_mutate_loader_snapshot(self):
        snapshot = locale("unchanged")
        before = copy.deepcopy(snapshot)
        with patch("materials_boundaries.i18n.read_catalog", return_value=snapshot):
            render_catalog(EMPTY, "sources", "ja")
        self.assertEqual(snapshot, before)

    def test_prediction_dispatch_does_not_enter_catalog_locale_lookup(self):
        with patch("materials_boundaries.catalog_output._catalog_translation_lookup", side_effect=AssertionError("wrong renderer")), \
             patch("materials_boundaries.predictions.render_predictions", return_value="prediction") as render:
            self.assertEqual(render_catalog(EMPTY, "predictions", "de"), "prediction")
            render.assert_called_once_with(EMPTY, "de")


if __name__ == "__main__":
    unittest.main()
