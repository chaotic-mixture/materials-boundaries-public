"""The presentation shortcut skips only work on exact, freshly validated data.

Synthetic fixtures are never production additions. Only resource reads are
substituted in the small-graph tests; every counted validation calls the real
complete-graph validator. The directory test also retains the real JSON reader.
"""
from contextlib import contextmanager
from copy import deepcopy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import call, patch

from materials_boundaries import catalog as catalog_module
from materials_boundaries import material_presentation as presentation
from materials_boundaries.material_references import validate_material_catalog
from test_material_reference_contract import (
    synthetic_material_catalog, synthetic_mean_catalog,
)


class _DictSubclass(dict):
    pass


class _ListSubclass(list):
    pass


class _StringSubclass(str):
    pass


class _IntegerSubclass(int):
    pass


class _UntrustedEqual:
    def __eq__(self, other):
        raise AssertionError("custom equality must not authorize the shortcut")


def _two_state_graph():
    """Two distinct fictional states sharing a grade, each with one property."""
    materials, properties, sources = synthetic_material_catalog()
    state = deepcopy(materials["records"][0])
    state.update(id="state_synthetic_b", source_scope="Distinct fictional state B",
                 property_ids=["refprop_synthetic_b_density"])
    prop = deepcopy(properties["records"][0])
    prop.update(id=state["property_ids"][0], material_state_id=state["id"])
    materials["records"].append(state)
    properties["records"].append(prop)
    return materials, properties, sources


@contextmanager
def _observed_graph(graph):
    resources = dict(zip(("materials", "reference_properties", "sources"), graph))

    def read(name):
        # Like the real JSON reader, each read produces new independent objects.
        return deepcopy(resources[name])

    with patch.object(catalog_module, "read_catalog", side_effect=read) as reader:
        with patch("materials_boundaries.material_references.validate_material_catalog",
                   wraps=validate_material_catalog) as validator:
            with patch.object(presentation, "deepcopy", wraps=deepcopy) as copier:
                yield reader, validator, copier


class MaterialPresentationFastPathTests(unittest.TestCase):
    def assert_reads(self, reader, calls=1):
        self.assertEqual(reader.call_args_list, [
            call("materials"), call("reference_properties"), call("sources"),
        ] * calls)

    def resolve_checked(self, graph, incoming, kind, validations):
        before_graph, before_incoming = deepcopy(graph), deepcopy(incoming)
        with _observed_graph(graph) as (reader, validator, copier):
            result = presentation._resolved_graph(incoming, kind)
            self.assert_reads(reader)
            self.assertEqual(validator.call_count, validations)
            if validations == 1:
                self.assertEqual(copier.call_count, 0)
            else:
                self.assertGreater(copier.call_count, 0)
        self.assertEqual(graph, before_graph)
        self.assertEqual(incoming, before_incoming)
        return result

    def assert_fallback_rejected(self, graph, incoming, kind="reference-properties",
                                 compare_input=True):
        before_graph = deepcopy(graph)
        before_incoming = deepcopy(incoming) if compare_input else None
        with _observed_graph(graph) as (reader, validator, copier):
            with self.assertRaises(ValueError):
                presentation._resolved_graph(incoming, kind)
            self.assert_reads(reader)
            self.assertEqual(validator.call_count, 2)
            self.assertGreater(copier.call_count, 0)
        self.assertEqual(graph, before_graph)
        if compare_input:
            self.assertEqual(incoming, before_incoming)

    def test_exact_material_and_property_subsets_validate_once_without_copying(self):
        graph = _two_state_graph()
        for kind, index in (("materials", 0), ("reference-properties", 1)):
            with self.subTest(kind=kind):
                incoming = deepcopy(graph[index])
                incoming["records"] = incoming["records"][:1]
                result = self.resolve_checked(graph, incoming, kind, 1)
                self.assertEqual(result, graph)
                self.assertEqual(len(result[index]["records"]), 2)
                result[index]["records"][0]["version"] = "2.0.0"
                self.assertEqual(incoming["records"][0]["version"], "1.0.0")
                self.assertEqual(graph[index]["records"][0]["version"], "1.0.0")

    def test_empty_selected_lists_keep_the_complete_validated_graph(self):
        graph = synthetic_material_catalog()
        for kind, incoming in (
            ("materials", {"schema_version": "1.0.0", "identities": [],
                           "grades": [], "records": []}),
            ("reference-properties", {"schema_version": "1.0.0", "records": []}),
        ):
            with self.subTest(kind=kind):
                self.assertEqual(self.resolve_checked(graph, incoming, kind, 1), graph)

    def test_duplicate_ids_in_every_selected_collection_are_rejected(self):
        graph = synthetic_material_catalog()
        for kind, index, keys in (("materials", 0, ("identities", "grades", "records")),
                                  ("reference-properties", 1, ("records",))):
            for key in keys:
                with self.subTest(kind=kind, collection=key):
                    incoming = deepcopy(graph[index])
                    incoming[key].append(deepcopy(incoming[key][0]))
                    with _observed_graph(graph) as (reader, validator, _):
                        with self.assertRaisesRegex(ValueError, "duplicate .* ID"):
                            presentation._resolved_graph(incoming, kind)
                        self.assert_reads(reader)
                        self.assertEqual(validator.call_count, 1)

    def test_invalid_envelopes_are_checked_after_fresh_graph_validation(self):
        graph = synthetic_material_catalog()
        mutations = (
            lambda value: value.pop("schema_version"),
            lambda value: value.update(schema_version="2.0.0"),
            lambda value: value.update(extra=[]),
            lambda value: value.pop("records"),
        )
        for mutate in mutations:
            incoming = deepcopy(graph[1])
            mutate(incoming)
            with self.subTest(incoming=incoming.keys()):
                with _observed_graph(graph) as (reader, validator, _):
                    with self.assertRaisesRegex(ValueError, "invalid canonical catalogue envelope"):
                        presentation._resolved_graph(incoming, "reference-properties")
                    self.assert_reads(reader)
                    self.assertEqual(validator.call_count, 1)

    def test_selected_collections_must_be_lists(self):
        graph = synthetic_material_catalog()
        for key in ("identities", "grades", "records"):
            for replacement in (None, {}, ()):
                incoming = deepcopy(graph[0])
                incoming[key] = replacement
                with self.subTest(collection=key, replacement=type(replacement)):
                    with _observed_graph(graph) as (reader, validator, _):
                        with self.assertRaisesRegex(ValueError, "must be a list"):
                            presentation._resolved_graph(incoming, "materials")
                        self.assert_reads(reader)
                        self.assertEqual(validator.call_count, 1)

    def test_selected_records_require_string_ids(self):
        graph = synthetic_material_catalog()
        for replacement in (None, [], {}, {"id": None}, {"id": 0}):
            incoming = {"schema_version": "1.0.0", "records": [replacement]}
            with self.subTest(replacement=replacement):
                with _observed_graph(graph) as (reader, validator, _):
                    with self.assertRaisesRegex(ValueError, "invalid records record"):
                        presentation._resolved_graph(incoming, "reference-properties")
                    self.assert_reads(reader)
                    self.assertEqual(validator.call_count, 1)

    def test_false_to_equal_integer_or_float_cannot_bypass_validation(self):
        graph = synthetic_material_catalog()
        paths = (("universal_bound",), ("engineering_allowable",),
                 ("verification", "independent_scientific_review"),
                 ("verification", "raw_data_reanalysis"))
        for path in paths:
            for replacement in (0, 0.0):
                with self.subTest(path=path, replacement=type(replacement)):
                    incoming = deepcopy(graph[1])
                    owner = incoming["records"][0]
                    for key in path[:-1]:
                        owner = owner[key]
                    self.assertEqual(owner[path[-1]], replacement)
                    owner[path[-1]] = replacement
                    self.assert_fallback_rejected(graph, incoming)

    def test_equal_float_and_boolean_cannot_replace_integer_count(self):
        for count, replacement in ((5, 5.0), (1, True)):
            with self.subTest(count=count, replacement=type(replacement)):
                graph = synthetic_mean_catalog()
                graph[1]["records"][0]["sample_count"]["value"] = count
                incoming = deepcopy(graph[1])
                incoming["records"][0]["sample_count"]["value"] = replacement
                self.assert_fallback_rejected(graph, incoming)

    def test_missing_record_and_nested_fields_use_the_rejecting_fallback(self):
        graph = synthetic_material_catalog()
        for path in (("universal_bound",), ("reported_value", "unit_code"),
                     ("verification", "raw_data_reanalysis")):
            with self.subTest(path=path):
                incoming = deepcopy(graph[1])
                owner = incoming["records"][0]
                for key in path[:-1]:
                    owner = owner[key]
                owner.pop(path[-1])
                self.assert_fallback_rejected(graph, incoming)

    def test_nested_evidence_order_changes_are_preserved_by_the_fallback(self):
        graph = synthetic_material_catalog()
        evidence = graph[1]["records"][0]["evidence"]
        second = deepcopy(evidence[0])
        second["locator"] = "Synthetic second table, SYN-A density note"
        evidence.append(second)
        incoming = deepcopy(graph[1])
        incoming["records"][0]["evidence"].reverse()
        result = self.resolve_checked(graph, incoming, "reference-properties", 2)
        self.assertEqual(result[1], incoming)

    def test_nested_duplicate_evidence_is_not_normalized_into_an_exact_match(self):
        graph = synthetic_material_catalog()
        incoming = deepcopy(graph[1])
        evidence = incoming["records"][0]["evidence"]
        evidence.append(deepcopy(evidence[0]))
        result = self.resolve_checked(graph, incoming, "reference-properties", 2)
        self.assertEqual(result[1], incoming)
        self.assertEqual(len(result[1]["records"][0]["evidence"]), 2)

    def test_nested_support_order_changes_do_not_use_structural_equivalence(self):
        graph = synthetic_material_catalog()
        incoming = deepcopy(graph[1])
        incoming["records"][0]["evidence"][0]["supports"].reverse()
        result = self.resolve_checked(graph, incoming, "reference-properties", 2)
        self.assertEqual(result[1], incoming)

    def test_dictionary_order_changes_conservatively_use_the_fallback(self):
        graph = synthetic_material_catalog()
        incoming = deepcopy(graph[1])
        record = incoming["records"][0]
        record["reported_value"] = dict(reversed(list(record["reported_value"].items())))
        self.assertEqual(incoming, graph[1])
        result = self.resolve_checked(graph, incoming, "reference-properties", 2)
        self.assertEqual(list(result[1]["records"][0]["reported_value"]),
                         list(record["reported_value"]))

    def test_top_level_record_order_changes_use_the_fallback(self):
        graph = _two_state_graph()
        for kind, index in (("materials", 0), ("reference-properties", 1)):
            with self.subTest(kind=kind):
                incoming = deepcopy(graph[index])
                incoming["records"].reverse()
                result = self.resolve_checked(graph, incoming, kind, 2)
                # The existing overlay preserves the complete graph's order.
                # Rendering still takes its selected order from the input.
                self.assertEqual(result, graph)

    def test_modified_legal_property_is_copied_and_revalidated(self):
        graph = synthetic_material_catalog()
        incoming = deepcopy(graph[1])
        incoming["records"][0]["scope_note"] = "A revised fictional presentation scope"
        result = self.resolve_checked(graph, incoming, "reference-properties", 2)
        self.assertEqual(result[1], incoming)
        result[1]["records"][0]["scope_note"] = "Detached return value"
        self.assertNotEqual(result[1], incoming)

    def test_changed_identities_and_grades_are_not_hidden_by_unchanged_states(self):
        graph = synthetic_material_catalog()
        for key, field in (("identities", "identity_scope"), ("grades", "designation")):
            with self.subTest(collection=key):
                incoming = deepcopy(graph[0])
                incoming[key][0][field] += " revised synthetic scope"
                result = self.resolve_checked(graph, incoming, "materials", 2)
                self.assertEqual(result[0], incoming)

    def test_new_legal_grade_and_relinked_state_use_complete_graph_validation(self):
        graph = _two_state_graph()
        incoming = deepcopy(graph[0])
        grade = deepcopy(incoming["grades"][0])
        grade.update(id="grade_synthetic_b", designation="SYN-B")
        incoming["grades"].append(grade)
        incoming["records"][0]["grade_id"] = grade["id"]
        result = self.resolve_checked(graph, incoming, "materials", 2)
        self.assertEqual(result[0], incoming)
        self.assertEqual(len(result[0]["grades"]), 2)

    def test_new_property_without_reciprocal_state_link_still_fails(self):
        graph = synthetic_material_catalog()
        incoming = deepcopy(graph[1])
        prop = deepcopy(incoming["records"][0])
        prop["id"] = "refprop_synthetic_unlinked"
        incoming["records"].append(prop)
        self.assert_fallback_rejected(graph, incoming)

    def test_bad_unselected_record_blocks_even_an_exact_selected_record(self):
        graph = _two_state_graph()
        incoming = {"schema_version": "1.0.0",
                    "records": [deepcopy(graph[1]["records"][0])]}
        graph[1]["records"][1]["engineering_allowable"] = True
        before = deepcopy((graph, incoming))
        with _observed_graph(graph) as (reader, validator, copier):
            with self.assertRaises(ValueError):
                presentation._resolved_graph(incoming, "reference-properties")
            self.assert_reads(reader)
            self.assertEqual(validator.call_count, 1)
            self.assertEqual(copier.call_count, 0)
        self.assertEqual((graph, incoming), before)

    def test_bad_unselected_source_blocks_an_empty_selection(self):
        graph = synthetic_material_catalog()
        extra = deepcopy(graph[2]["records"][0])
        extra.update(id="synthetic_unselected_source", urls=[])
        graph[2]["records"].append(extra)
        with _observed_graph(graph) as (reader, validator, copier):
            with self.assertRaises(ValueError):
                presentation._resolved_graph({"schema_version": "1.0.0", "records": []},
                                             "reference-properties")
            self.assert_reads(reader)
            self.assertEqual(validator.call_count, 1)
            self.assertEqual(copier.call_count, 0)

    def test_envelope_and_list_subclasses_use_the_original_valid_fallback(self):
        graph = synthetic_material_catalog()
        for location in ("envelope", "records", "schema_version"):
            incoming = deepcopy(graph[1])
            if location == "envelope":
                incoming = _DictSubclass(incoming)
            elif location == "records":
                incoming["records"] = _ListSubclass(incoming["records"])
            else:
                incoming["schema_version"] = _StringSubclass(incoming["schema_version"])
            with self.subTest(location=location):
                self.assertEqual(self.resolve_checked(graph, incoming, "reference-properties", 2),
                                 graph)

    def test_record_and_nested_subclasses_do_not_bypass_strict_schema_types(self):
        for location in ("record", "evidence", "text", "integer"):
            graph = synthetic_mean_catalog()
            incoming = deepcopy(graph[1])
            prop = incoming["records"][0]
            if location == "record":
                incoming["records"][0] = _DictSubclass(prop)
            elif location == "evidence":
                prop["evidence"] = _ListSubclass(prop["evidence"])
            elif location == "text":
                prop["scope_note"] = _StringSubclass(prop["scope_note"])
            else:
                prop["sample_count"]["value"] = _IntegerSubclass(5)
            with self.subTest(location=location):
                self.assert_fallback_rejected(graph, incoming)

    def test_custom_equality_is_never_used_to_prove_unchanged_data(self):
        graph = synthetic_material_catalog()
        incoming = deepcopy(graph[1])
        value = _UntrustedEqual()
        incoming["records"][0]["engineering_allowable"] = value
        self.assert_fallback_rejected(graph, incoming, compare_input=False)
        self.assertIs(incoming["records"][0]["engineering_allowable"], value)

    def test_cyclic_input_reaches_the_original_rejecting_validation(self):
        graph = synthetic_material_catalog()
        incoming = deepcopy(graph[1])
        evidence = incoming["records"][0]["evidence"]
        evidence[0]["supports"][0] = evidence
        self.assert_fallback_rejected(graph, incoming, compare_input=False)
        self.assertIs(evidence[0]["supports"][0], evidence)

    def test_real_directory_changes_are_seen_on_each_consecutive_call(self):
        graph = _two_state_graph()
        incoming = {"schema_version": "1.0.0",
                    "records": [deepcopy(graph[1]["records"][0])]}
        original_input = deepcopy(incoming)
        with TemporaryDirectory(prefix="materials-presentation-fresh-") as directory:
            root = Path(directory)
            (root / "data").mkdir()
            names = ("materials", "reference_properties", "sources")

            def write_graph():
                for name, resource in zip(names, graph):
                    (root / "data" / (name + ".json")).write_text(
                        json.dumps(resource), encoding="utf-8")

            write_graph()
            with patch.object(catalog_module, "files", return_value=root):
                with patch.object(catalog_module, "read_catalog",
                                  wraps=catalog_module.read_catalog) as reader:
                    with patch("materials_boundaries.material_references.validate_material_catalog",
                               wraps=validate_material_catalog) as validator:
                        first = presentation._resolved_graph(incoming, "reference-properties")
                        graph[1]["records"][1]["scope_note"] = "New on-disk synthetic note"
                        graph[2]["records"][0]["title"] = "New on-disk synthetic title"
                        write_graph()
                        second = presentation._resolved_graph(incoming, "reference-properties")
                        self.assertNotEqual(first[1], second[1])
                        self.assertNotEqual(first[2], second[2])
                        self.assertEqual(second, graph)
                        self.assertEqual(validator.call_count, 2)
                        graph[1]["records"][1]["engineering_allowable"] = True
                        write_graph()
                        with self.assertRaises(ValueError):
                            presentation._resolved_graph(incoming, "reference-properties")
                        self.assertEqual(validator.call_count, 3)
                        self.assert_reads(reader, calls=3)
        self.assertEqual(incoming, original_input)


if __name__ == "__main__":
    unittest.main()
