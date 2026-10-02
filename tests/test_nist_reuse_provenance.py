"""Public bibliography/rights boundaries, without excluded coefficient datasets."""
import copy
from decimal import Context, Decimal, InvalidOperation, localcontext
from hashlib import sha256
import json
from pathlib import Path
import re
import unittest

from materials_boundaries.catalog import read_catalog
from materials_boundaries.temperature import canonical_json, evaluate_temperature
from provenance_corrections import LEDGER, PUBLIC_BASELINE, historical_record, public_previous_record

ROOT = Path(__file__).resolve().parents[1]


class PublicReuseBoundaryTests(unittest.TestCase):
    def test_public_temperature_records_are_authored_synthetic_demos(self):
        for model in read_catalog('temperature_models')['records']:
            self.assertEqual(model['classification'], 'synthetic_demo')
            self.assertTrue(model['id'].startswith('synthetic_'))
            self.assertEqual(model['source_ids'], ['materials_boundaries_synthetic_temperature_demo'])
            self.assertIsNone(model['material']['UNS'])
            self.assertIn('SYNTHETIC', model['material']['name'])
            for branch in model['branches']:
                self.assertIsNone(branch['source_data_range_K'])
                self.assertIsNone(branch['reported_fit_error']['value'])
                self.assertIsNone(branch['reported_fit_error']['unit'])
                self.assertEqual(branch['range_status'], 'artificial_demonstration_interval')

    def test_historical_rights_ledger_is_bibliography_only(self):
        self.assertEqual(set(LEDGER['records']), {'sources'})
        self.assertEqual(LEDGER['locales'], {})
        self.assertTrue(LEDGER['evidence'])
        for entry in LEDGER['evidence']:
            self.assertIn('nist.gov/', entry['url'])

    def test_bibliographic_sources_do_not_claim_database_clearance(self):
        for source in read_catalog('sources')['records']:
            if source['id'] not in PUBLIC_BASELINE['source_corrections']:
                continue
            self.assertIsNone(source['license']['identifier'])
            self.assertIn('omitted', source['bundled_content'])
            self.assertIn('not a determination', ' '.join(source['claim_notes']))
            self.assertTrue(source['urls'])
            self.assertTrue(source['authors'])
            self.assertNotIn('coefficients_text', source)

    def test_exact_public_bibliography_corrections_are_nonmutating(self):
        sources = {source['id']: source for source in read_catalog('sources')['records']}
        for identifier, changes in PUBLIC_BASELINE['source_corrections'].items():
            source = sources[identifier]
            before = copy.deepcopy(source)
            historical_record('sources', source)
            self.assertEqual(source, before)
            for change in changes:
                candidate = copy.deepcopy(source)
                target = candidate
                for key in change['path'][:-1]:
                    target = target[key]
                target[change['path'][-1]] = change['before']
                with self.subTest(source=identifier, path=change['path']):
                    with self.assertRaises(AssertionError):
                        public_previous_record('sources', candidate)

    def test_public_correction_preserves_additions_reordering_and_unrelated_changes(self):
        source = next(source for source in read_catalog('sources')['records']
                      if source['id'] in PUBLIC_BASELINE['source_corrections'])
        source['claim_notes'].append('SYNTHETIC extra curation note')
        source['claim_notes'].reverse()
        source['urls'].reverse()
        source['title'] = 'SYNTHETIC unrelated change'
        restored = public_previous_record('sources', source)
        self.assertIn('SYNTHETIC extra curation note', restored['claim_notes'])
        self.assertEqual(restored['title'], source['title'])

    def test_excluded_model_identifiers_are_absent_from_public_source_files(self):
        # Split pattern deliberately avoids embedding the excluded IDs themselves.
        pattern = re.compile(r'nist_' + r'[a-z0-9_]+_young_temperature')
        for folder in ('materials_boundaries', 'tests', 'docs', 'schemas', 'examples'):
            for path in (ROOT / folder).rglob('*'):
                if not path.is_file() or path.suffix in ('.pyc', '.png'):
                    continue
                with self.subTest(path=str(path.relative_to(ROOT))):
                    self.assertIsNone(pattern.search(path.read_text(encoding='utf-8')))

    def test_excluded_coefficient_and_derived_numeric_fingerprints_are_absent(self):
        fixture = json.loads((ROOT / 'tests/fixtures/public_exclusion_fingerprints.json').read_text())
        forbidden = set(fixture['coefficient_sha256'] + fixture['derived_value_sha256'])
        numeric = re.compile(r'(?<![A-Za-z0-9_])[+-]?(?:\d+\.\d*|\d*\.\d+|\d+)(?:[Ee][+-]?\d+)?(?![A-Za-z0-9_])')
        for path in ROOT.rglob('*'):
            parts = path.relative_to(ROOT).parts
            if not path.is_file() or any(p in ('__pycache__', '.git', 'build', 'dist', '.venv') or p.endswith('.egg-info') for p in parts):
                continue
            try:
                text = path.read_text(encoding='utf-8')
            except UnicodeDecodeError:
                continue
            with localcontext(Context(prec=28)):
                for token in set(numeric.findall(text)):
                    try:
                        fingerprint = sha256(str(Decimal(token).normalize()).encode()).hexdigest()
                    except InvalidOperation:
                        continue
                    self.assertNotIn(fingerprint, forbidden, str(path.relative_to(ROOT)))

    def test_synthetic_source_is_original_project_work_without_empirical_evidence(self):
        source = next(s for s in read_catalog('sources')['records']
                      if s['id'] == 'materials_boundaries_synthetic_temperature_demo')
        self.assertEqual(source['role'], 'synthetic_demo_provenance')
        self.assertEqual(source['license']['identifier'], 'MIT')
        self.assertIn('not represent any real material', ' '.join(source['claim_notes']))

    def test_new_public_results_are_content_addressed_and_synthetic(self):
        request = {'schema_version':'1.0.0', 'model_id':'synthetic_linear_temperature',
                   'temperature':{'value':50, 'unit':'K'}}
        result = evaluate_temperature(request)
        self.assertEqual(result['id'], sha256(canonical_json({k:v for k,v in result.items() if k != 'id'}).encode()).hexdigest()[:20])
        self.assertEqual(result['classification'], 'synthetic_demo')
        self.assertEqual(result['predictions'][0]['value'], 15)


if __name__ == '__main__':
    unittest.main()
