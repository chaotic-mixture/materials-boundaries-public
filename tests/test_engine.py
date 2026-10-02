import copy
from decimal import localcontext, Inexact
import json
import math
import random
import unittest
from pathlib import Path

from materials_boundaries import ValidationError, evaluate, load_json

ROOT = Path(__file__).resolve().parents[1]


def example():
    return load_json(ROOT / "examples/synthetic-two-phase.json")


def bounds(data):
    evaluations = {item["claim_id"]: item for item in evaluate(data)["evaluations"]}
    return [evaluations[identifier] for identifier in
            ("hs_bulk_3d_two_phase", "reuss_bulk", "voigt_bulk")]


class EngineTests(unittest.TestCase):
    def test_reference_synthetic_fixture(self):
        hs, reuss, voigt = bounds(example())
        self.assertEqual(hs["result"], {"lower": 16.25, "upper": 17.5, "unit": "GPa"})
        self.assertEqual(reuss["result"]["lower"], 15)
        self.assertEqual(voigt["result"]["upper"], 20)
        self.assertTrue(all(x["applicability"] == "satisfied" for x in (hs, reuss, voigt)))

    def test_independent_rational_fixture(self):
        data = example()
        for phase, value in zip(data["phases"], (1, 10)):
            for key in ("bulk_modulus", "shear_modulus"):
                phase[key]["value"] = value
        hs, reuss, voigt = bounds(data)
        self.assertAlmostEqual(hs["result"]["lower"], 104 / 41)
        self.assertAlmostEqual(hs["result"]["upper"], 500 / 113)
        self.assertAlmostEqual(reuss["result"]["lower"], 20 / 11)
        self.assertEqual(voigt["result"]["upper"], 5.5)

    def test_equal_bulk_moduli(self):
        data = example()
        data["phases"][1]["bulk_modulus"]["value"] = 10
        for item in bounds(data):
            for key in ("lower", "upper"):
                if key in item["result"]:
                    self.assertEqual(item["result"][key], 10)

    def test_equal_shear_moduli(self):
        data = example()
        data["phases"][1]["shear_modulus"]["value"] = 5
        hs, reuss, voigt = bounds(data)
        self.assertEqual(hs["result"]["lower"], hs["result"]["upper"])
        self.assertNotEqual(reuss["result"]["lower"], voigt["result"]["upper"])

    def test_identical_phases(self):
        data = example()
        for prop in ("bulk_modulus", "shear_modulus"):
            data["phases"][1][prop] = copy.deepcopy(data["phases"][0][prop])
        self.assertEqual(bounds(data)[0]["result"]["lower"], 10)

    def test_pure_phase_endpoints_with_absent_unknown_properties(self):
        for present in (0, 1):
            data = example()
            expected = data["phases"][present]["bulk_modulus"]["value"]
            for i, phase in enumerate(data["phases"]):
                phase["volume_fraction"] = 1 if i == present else 0
                if i != present:
                    phase["bulk_modulus"] = None
                    phase["shear_modulus"] = None
            for item in bounds(data):
                self.assertEqual(item["applicability"], "satisfied")
                self.assertEqual(item["result"].get("lower", expected), expected)
                self.assertEqual(item["result"].get("upper", expected), expected)

    def test_pure_phase_keeps_active_condition_requirements(self):
        data = example()
        data["phases"][0]["volume_fraction"] = 1
        data["phases"][1]["volume_fraction"] = 0
        data["conditions"]["effective_symmetry"] = None
        self.assertEqual(bounds(data)[0]["applicability"], "unknown")

    def test_tiny_positive_fraction_not_discarded(self):
        data = example()
        data["phases"][0]["volume_fraction"] = 1e-300
        data["phases"][1]["volume_fraction"] = 1
        data["phases"][0]["bulk_modulus"] = None
        self.assertEqual(bounds(data)[0]["applicability"], "unknown")

    def test_phase_order_invariance(self):
        data = example()
        data["phases"][0]["volume_fraction"] = 0.3
        data["phases"][1]["volume_fraction"] = 0.7
        expected = [x["result"] for x in bounds(data)]
        data["phases"].reverse()
        self.assertEqual([x["result"] for x in bounds(data)], expected)

    def test_unit_conversion_per_quantity(self):
        data = example()
        data["phases"][0]["bulk_modulus"] = {"value": 10000, "unit": "MPa"}
        data["phases"][1]["shear_modulus"] = {"value": 15000000000, "unit": "Pa"}
        self.assertEqual(bounds(data)[0]["result"]["lower"], 16.25)
        self.assertEqual(evaluate(data, output_unit="MPa")["evaluations"][0]["result"]["upper"], 17500)

    def test_uniform_scale(self):
        for scale in (1e-100, 1e-6, 123.5, 1e100):
            data = example()
            for phase in data["phases"]:
                for key in ("bulk_modulus", "shear_modulus"):
                    phase[key]["value"] *= scale
            self.assertAlmostEqual(bounds(data)[0]["result"]["lower"] / scale, 16.25)

    def test_unknown_condition_and_null_quantity(self):
        for mode in ("missing", "null", "quantity", "value", "fraction"):
            data = example()
            if mode == "missing":
                del data["conditions"]["effective_symmetry"]
            elif mode == "null":
                data["conditions"]["effective_symmetry"] = None
            elif mode == "quantity":
                data["phases"][0]["bulk_modulus"] = None
            elif mode == "value":
                data["phases"][0]["bulk_modulus"]["value"] = None
            else:
                data["phases"][0]["volume_fraction"] = None
            for item in bounds(data):
                self.assertEqual(item["applicability"], "unknown")
                self.assertIsNone(item["result"])

    def test_every_incompatible_condition(self):
        incompatible = {"dimension": 2, "constituent_symmetry": "anisotropic", "effective_symmetry": "anisotropic", "kinematics": "finite_strain", "constitutive_law": "viscoelastic", "loading": "dynamic", "interface": "imperfect"}
        for key, value in incompatible.items():
            data = example()
            data["conditions"][key] = value
            with self.subTest(key=key):
                self.assertTrue(all(x["applicability"] == "violated" and x["result"] is None for x in bounds(data)))

    def test_violated_dominates_unknown_retaining_evidence(self):
        data = example()
        data["conditions"]["constituent_symmetry"] = "anisotropic"
        data["conditions"]["effective_symmetry"] = None
        item = bounds(data)[0]
        self.assertEqual(item["applicability"], "violated")
        self.assertEqual({x["state"] for x in item["checks"]}, {"satisfied", "unknown", "violated"})

    def test_nonpositive_moduli_are_outside_supported_scope(self):
        for key in ("bulk_modulus", "shear_modulus"):
            for value in (0, -1):
                data = example()
                data["phases"][0][key]["value"] = value
                self.assertTrue(all(x["applicability"] == "violated" for x in bounds(data)))

    def test_not_well_ordered_only_blocks_hs(self):
        data = example()
        data["phases"][1]["shear_modulus"]["value"] = 1
        hs, reuss, voigt = bounds(data)
        self.assertEqual(hs["applicability"], "violated")
        self.assertIsNone(hs["result"])
        self.assertEqual(reuss["applicability"], "satisfied")
        self.assertEqual(voigt["applicability"], "satisfied")

    def test_one_phase_description_is_unsupported(self):
        data = example()
        data["phases"] = data["phases"][:1]
        data["phases"][0]["volume_fraction"] = 1
        self.assertEqual(bounds(data)[0]["applicability"], "violated")

    def test_normalization_is_reported(self):
        data = example()
        data["phases"][0]["volume_fraction"] = 0.5000000000001
        result = evaluate(data)
        self.assertTrue(result["fraction_normalization"]["performed"])
        self.assertEqual(len(result["fraction_normalization"]["normalized_fractions"]), 2)

    def test_extreme_contrast_remains_finite_positive(self):
        data = example()
        for phase, scale in zip(data["phases"], (1e-250, 1e250)):
            phase["bulk_modulus"]["value"] = scale
            phase["shear_modulus"]["value"] = scale
        for item in bounds(data):
            self.assertEqual(item["computation"], "computed")
            for key in ("lower", "upper"):
                if key in item["result"]:
                    self.assertTrue(math.isfinite(item["result"][key]))
                    self.assertGreater(item["result"][key], 0)

    def test_output_overflow_is_explicit_not_infinity(self):
        data = example()
        for phase in data["phases"]:
            phase["bulk_modulus"]["value"] = 1e308
            phase["shear_modulus"]["value"] = 1e308
        result = evaluate(data, output_unit="Pa")
        for item in result["evaluations"]:
            self.assertEqual(item["computation"], "numerical_range_error")
            self.assertIsNone(item["result"])
            self.assertEqual(item["applicability"], "satisfied")
        json.dumps(result, allow_nan=False)

    def test_output_underflow_is_explicit_not_zero(self):
        data = example()
        for phase in data["phases"]:
            for key in ("bulk_modulus", "shear_modulus"):
                phase[key] = {"value": 5e-324, "unit": "Pa"}
        self.assertTrue(all(x["computation"] == "numerical_range_error" for x in bounds(data)))

    def test_random_ordering_and_equivalent_formula(self):
        rng = random.Random(20261002)
        for _ in range(250):
            data = example()
            k1, k2 = sorted((10 ** rng.uniform(-3, 3), 10 ** rng.uniform(-3, 3)))
            g1, g2 = sorted((10 ** rng.uniform(-3, 3), 10 ** rng.uniform(-3, 3)))
            f = rng.uniform(0.001, 0.999)
            for phase, k, g, vf in zip(data["phases"], (k1, k2), (g1, g2), (f, 1-f)):
                phase["bulk_modulus"]["value"] = k
                phase["shear_modulus"]["value"] = g
                phase["volume_fraction"] = vf
            hs, reuss, voigt = [x["result"] for x in bounds(data)]
            tolerance = max(1, voigt["upper"]) * 1e-12
            self.assertLessEqual(reuss["lower"], hs["lower"] + tolerance)
            self.assertLessEqual(hs["lower"], hs["upper"] + tolerance)
            self.assertLessEqual(hs["upper"], voigt["upper"] + tolerance)
            delta = k2-k1
            direct = k1 + (1-f)*delta*(k1+4*g1/3)/(k1+4*g1/3+f*delta)
            self.assertAlmostEqual(hs["lower"] / direct, 1, places=11)

    def test_independent_of_callers_decimal_context(self):
        data=example()
        expected=evaluate(data)
        with localcontext() as ctx:
            ctx.prec=1
            ctx.Emax=2
            ctx.Emin=-2
            ctx.traps[Inexact]=True
            self.assertEqual(evaluate(data),expected)
            data["phases"][0]["volume_fraction"]=0.6
            data["phases"][1]["volume_fraction"]=0.6
            with self.assertRaises(ValidationError):evaluate(data)

    def test_evaluate_does_not_mutate_input(self):
        data = example()
        original = copy.deepcopy(data)
        evaluate(data)
        self.assertEqual(data, original)


if __name__ == "__main__":
    unittest.main()
