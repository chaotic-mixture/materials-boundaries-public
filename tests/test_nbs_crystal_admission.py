"""Source-qualified NBS additions and exact recovery of the 4c5656c baseline."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import unittest

from materials_boundaries.catalog import read_catalog
from materials_boundaries.material_references import (
    material_quota_coverage, merge_material_catalogs, validate_material_catalog,
)

ROOT = Path(__file__).resolve().parents[1]
BATCH = ROOT / "experimental/material-batches/20261014-nb-nbs-crystals"
MATERIAL_SHA256 = "faba4c02b884bdfc847cc85f2f885c984928334d1a6d2cbf139298aca157218b"
PROPERTY_SHA256 = "764c6124a45313e8593874c69b4a5af505317bd0d603808f102b65cadcb7326a"
BASELINE_SHA256 = {
    "materials": "ffd27ae7a927494083cbdcb173847502283f9ff0f69b8b7321abe0b042824dc1",
    "reference_properties": "7430901a0f401aca384debb8706a124ac43ad6d043165beff1b8d186641fddef",
    "sources": "4240f52ef96bbe34a8a677e2f995296a6c72ac8ab14fc3f8978c043540fcef93",
}
D4E9_SHA256 = {
    "materials": "54fbcfb1de21335f8e0ad2b6d98900cbb847ce77912632936677b38aa86e6378",
    "reference_properties": "a4b9b64178b87e354727327a546db9fd9f1bb4495a9b4f653d8618b728cedcdd",
    "sources": "4240f52ef96bbe34a8a677e2f995296a6c72ac8ab14fc3f8978c043540fcef93",
}


def serialized(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode()


class NBSAdmissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.materials, cls.properties, cls.sources = (
            read_catalog(name) for name in ("materials", "reference_properties", "sources")
        )
        cls.additions = {
            "materials": json.loads((BATCH / "nbs-materials.append.json").read_text(encoding="utf-8")),
            "properties": json.loads((BATCH / "nbs-reference-properties.append.json").read_text(encoding="utf-8")),
            "sources": cls.sources,
        }
        # Recover the frozen three-crystal candidate before exercising its
        # original main-baseline recovery. Later additions cannot weaken either
        # byte boundary or silently rewrite a prior scientific record.
        cls.before_increment = {
            "materials": deepcopy(cls.materials),
            "reference_properties": deepcopy(cls.properties),
            "sources": deepcopy(cls.sources),
        }
        packets = (
            ("20261015-niobium-density", "nb-materials.candidate.json",
             "nb-reference-properties.candidate.json", "nb-sources.candidate.json"),
            ("20261015-nbs-halide-densities", "nbs-materials.candidate.json",
             "nbs-reference-properties.candidate.json", None),
        )
        for directory, material_name, property_name, source_name in packets:
            packet = ROOT / "experimental/material-batches" / directory
            for name, filename, fields in (
                ("materials", material_name, ("identities", "records")),
                ("reference_properties", property_name, ("records",)),
                ("sources", source_name, ("records",)),
            ):
                if filename is None:
                    continue  # The four halides reuse the existing NBS source.
                addition = json.loads((packet / filename).read_text(encoding="utf-8"))
                for field in fields:
                    ids = {record["id"] for record in addition[field]}
                    cls.before_increment[name][field] = [
                        record for record in cls.before_increment[name][field]
                        if record["id"] not in ids
                    ]

    def test_removing_five_incremental_additions_recovers_exact_d4e9_candidate(self):
        for name, expected in D4E9_SHA256.items():
            self.assertEqual(sha256(serialized(self.before_increment[name])).hexdigest(), expected)
        self.assertEqual(len(self.materials["identities"])
                         - len(self.before_increment["materials"]["identities"]), 5)
        self.assertEqual(len(self.sources["records"])
                         - len(self.before_increment["sources"]["records"]), 1)

    def test_reviewed_payload_hashes_and_exact_runtime_records(self):
        for filename, expected in (("nbs-materials.append.json", MATERIAL_SHA256),
                                   ("nbs-reference-properties.append.json", PROPERTY_SHA256)):
            self.assertEqual(sha256((BATCH / filename).read_bytes()).hexdigest(), expected)
        for key, current, fields in (("materials", self.materials, ("identities", "records")),
                                     ("properties", self.properties, ("records",))):
            for field in fields:
                by_id = {record["id"]: record for record in current[field]}
                for record in self.additions[key][field]:
                    self.assertEqual(by_id[record["id"]], record)

    def test_removing_only_three_additions_recovers_exact_baseline(self):
        for name, key, current, fields in (
            ("materials", "materials", self.before_increment["materials"], ("identities", "records")),
            ("reference_properties", "properties", self.before_increment["reference_properties"], ("records",)),
        ):
            recovered = deepcopy(current)
            for field in fields:
                new_ids = {record["id"] for record in self.additions[key][field]}
                self.assertEqual(len(new_ids), 3)
                recovered[field] = [record for record in recovered[field] if record["id"] not in new_ids]
            self.assertEqual(sha256(serialized(recovered)).hexdigest(), BASELINE_SHA256[name])
        self.assertEqual(sha256(serialized(self.before_increment["sources"])).hexdigest(),
                         BASELINE_SHA256["sources"])

    def test_current_coverage_and_repeated_append_do_not_double_count(self):
        validate_material_catalog(self.materials, self.properties, self.sources)
        coverage = material_quota_coverage(self.materials, self.properties, self.sources)
        self.assertEqual(coverage["distinct_material_count"], 1065)
        self.assertEqual({k: v["admitted_unique_identity_count"] for k, v in coverage["classes"].items()},
                         {"natural": 1010, "metal": 15, "inorganic": 23, "polymer": 14, "composite": 3})
        result = merge_material_catalogs(self.materials, self.properties, self.sources, self.additions)
        self.assertEqual(result, {"materials": self.materials, "properties": self.properties, "sources": self.sources})

    def test_source_derived_values_and_review_limits_remain_explicit(self):
        values = {
            "refprop_nbs1953_lif_harshaw_crystallographic_density": "2.638",
            "refprop_nbs1953_kcl_mallinckrodt_kyd1_crystallographic_density": "1.9865",
            "refprop_nbs1953_caf2_stockbarger_mit_crystallographic_density": "3.181",
        }
        for prop in self.additions["properties"]["records"]:
            self.assertEqual(prop["reported_value"]["number"], values[prop["id"]])
            self.assertEqual(prop["reported_value"]["unit_code"], "g/cm^3")
            self.assertEqual(prop["conditions"]["temperature"]["text"], "25 °C")
            self.assertEqual(prop["density_basis"], "crystallographic")
            self.assertEqual(prop["evidence_kind"], "published_measurement_derived_reference")
            self.assertIsNone(prop["uncertainty"])
            self.assertIsNone(prop["sample_count"]["value"])
            self.assertFalse(prop["verification"]["independent_scientific_review"])
            self.assertFalse(prop["verification"]["raw_data_reanalysis"])
            self.assertFalse(prop["universal_bound"])
            self.assertFalse(prop["engineering_allowable"])


if __name__ == "__main__":
    unittest.main()
