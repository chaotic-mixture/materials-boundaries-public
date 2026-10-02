import copy
import tempfile
import unittest
from pathlib import Path

from materials_boundaries import ValidationError, evaluate, load_json, validate_instance
from test_engine import example


class ValidationTests(unittest.TestCase):
    def test_valid_example(self):
        self.assertIsNone(validate_instance(example()))

    def test_nonfinite_and_boolean_quantities(self):
        for value in (float("nan"), float("inf"), -float("inf"), True, "10", 10**400):
            data = example()
            data["phases"][0]["bulk_modulus"]["value"] = value
            with self.subTest(value=str(value)), self.assertRaises(ValidationError):
                validate_instance(data)

    def test_bad_fractions(self):
        for values in ((-0.1,1.1), (0.2,0.2), (0,0), (float("nan"),0.5), (True,0), (0.9,0.9), (0.8,None,0.5)):
            data = example()
            if len(values)==3:
                data["phases"].append(copy.deepcopy(data["phases"][0]))
                data["phases"][-1]["id"]="phase3"
            for phase, value in zip(data["phases"],values):phase["volume_fraction"]=value
            with self.subTest(values=values), self.assertRaises(ValidationError):validate_instance(data)

    def test_unknown_fraction_is_valid(self):
        data=example(); data["phases"][0]["volume_fraction"]=None
        validate_instance(data)

    def test_unknown_and_missing_quantity_are_valid(self):
        data=example(); del data["phases"][0]["shear_modulus"]
        data["phases"][1]["bulk_modulus"]["value"]=None
        validate_instance(data)

    def test_bad_unit(self):
        for unit in ("gpa","psi","",None,5):
            data=example(); data["phases"][0]["bulk_modulus"]["unit"]=unit
            with self.assertRaises(ValidationError):validate_instance(data)

    def test_duplicate_ids(self):
        data=example(); data["phases"][1]["id"]="phase_1"
        with self.assertRaises(ValidationError):validate_instance(data)

    def test_unknown_keys_rejected(self):
        for path in ((),("conditions",),("phases",0), ("phases",0,"bulk_modulus"),("provenance",)):
            data=example(); at=data
            for key in path:at=at[key]
            at["typo"]=42
            with self.assertRaises(ValidationError):validate_instance(data)

    def test_missing_top_level_keys(self):
        for key in example():
            data=example(); del data[key]
            with self.assertRaises(ValidationError):validate_instance(data)

    def test_wrong_shapes(self):
        for key,value in (("conditions",[]),("phases",[]),("phases",{}),("provenance",[]),("id",""),("schema_version","2")):
            data=example(); data[key]=value
            with self.assertRaises(ValidationError):validate_instance(data)

    def test_invalid_dimension(self):
        for value in (True,3.1,0,-1,"3"):
            data=example(); data["conditions"]["dimension"]=value
            with self.assertRaises(ValidationError):validate_instance(data)

    def test_strict_json_reader(self):
        for text in ('{"x":1,"x":2}','{"x":NaN}','{"x":Infinity}','{"x":1e309}','{"x":1e-400}','[broken', '{"x":' + '1'*5000 + '}'):
            with tempfile.TemporaryDirectory() as folder:
                file=Path(folder)/'bad.json'; file.write_text(text)
                with self.subTest(text=text), self.assertRaises(ValidationError):load_json(file)

    def test_integral_float_dimension_matches_json_schema(self):
        data=example(); data["conditions"]["dimension"]=3.0
        self.assertEqual(evaluate(data)["evaluations"][0]["applicability"], "satisfied")

    def test_bad_output_unit(self):
        with self.assertRaises(ValidationError):evaluate(example(),output_unit="psi")

if __name__ == "__main__":unittest.main()
