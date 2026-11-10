import unittest
from dataclasses import replace

from materials_boundaries.database import Database
from materials_boundaries.tension import Case, COPPER, NICKEL, evaluate


class TensionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = Database()
        cls.case = Case(NICKEL, ".001", "free", True)

    def test_free(self):
        result = evaluate(self.case, self.db)
        self.assertEqual((result["axial_stress"], result["unit"]), (.205, "GPa"))
        self.assertTrue(result["evidence"])

    def test_missing(self):
        for case in (replace(self.case, record=COPPER), replace(self.case, assume_model=False)):
            result = evaluate(case, self.db)
            self.assertTrue(result["missing"])
            self.assertNotIn("axial_stress", result)

    def test_revision(self):
        fixed = replace(self.case, constraint="fixed")
        result = evaluate(fixed, self.db)
        self.assertEqual(result["missing"], ["Poisson ratio for the selected state"])
        self.assertNotIn("axial_stress", result)
        self.assertAlmostEqual(evaluate(replace(fixed, poisson=".3"), self.db)["axial_stress"],
                               .205 * .7 / (1.3 * .4))
