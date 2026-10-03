"""Check the current README summary without freezing historical release counts.

When rehearsing supported catalog appends in a disposable checkout, refresh that
copy's marked README summary too. Existing scientific tests and fixtures remain
unchanged; the current summary must describe the catalogs in that checkout.
"""
import json
from pathlib import Path
import unittest

from materials_boundaries.engine import BASE_RULES, DERIVED_RULES

ROOT = Path(__file__).resolve().parents[1]
START = "<!-- current-catalog-summary:start -->"
END = "<!-- current-catalog-summary:end -->"


class CurrentReadmeSummaryTests(unittest.TestCase):
    def test_marked_summary_matches_current_catalogs(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertEqual(readme.count(START), 1)
        self.assertEqual(readme.count(END), 1)
        before, _, remainder = readme.partition(START)
        summary, _, after = remainder.partition(END)
        self.assertNotIn(END, before, "summary markers must be in order")
        self.assertTrue(after.strip(), "historical release text stays outside the summary")

        def catalog(name):
            path = ROOT / "materials_boundaries" / "data" / f"{name}.json"
            return json.loads(path.read_text(encoding="utf-8"))

        claims = catalog("claims")["records"]
        sources = catalog("sources")["records"]
        observations = catalog("observations")["records"]
        predictions = catalog("computational_predictions")
        demos = [record for record in catalog("temperature_models")["records"]
                 if record["classification"] == "synthetic_demo"]
        studies = {record["study_id"] for record in observations}
        families = {protocol["family"] for protocol in predictions["protocols"]}
        synthetic_sources = sum(source["role"] == "synthetic_demo_provenance"
                                for source in sources)
        expected = (
            f"**{len(claims)} mechanics claims**",
            f"**{len(sources)} source records**",
            f"**{len(observations)} observations from {len(studies)} studies**",
            f"**{len(predictions['records'])} published computational predictions in "
            f"{len(families)} scientific families and "
            f"{len(predictions['comparison_groups'])} explicit groups**",
            f"**{len(demos)} synthetic temperature demos with "
            f"{sum(len(demo['branches']) for demo in demos)} branches**",
            f"**{len(BASE_RULES) + len(DERIVED_RULES)} executable composite calculation rules**",
            f"The {len(sources)} sources comprise {len(sources) - synthetic_sources} "
            f"bibliographic/source records plus {synthetic_sources} original "
            "synthetic-demo provenance record",
        )
        for statement in expected:
            with self.subTest(statement=statement):
                self.assertIn(statement, summary)


if __name__ == "__main__":
    unittest.main()
