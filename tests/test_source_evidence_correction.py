"""Current source facts and bounded historical lineage are separately testable."""
import ast
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from material_catalog_preservation import pre_material_bytes
import tempfile
import unittest
from unittest.mock import patch

from materials_boundaries.catalog import read_catalog
from materials_boundaries.composite import build_composite_report, validate_composite_report, CompositeReplayError
from materials_boundaries.engine import BASE_RULES, DERIVED_RULES
from materials_boundaries.i18n import LANGUAGES, translate
import source_evidence_preservation as history
from composite_preservation import release_readme_bytes

ROOT = Path(__file__).resolve().parents[1]
LEDGER_SHA256 = 'a599d754e6ebdad8870be38628a05680afd26525b9f1ecc9c7ed0fc41c5ba7ed'
ADAPTER_SHA256 = '6a48335f4188cd058f6ff043c6a479caa7bc73c3a86ff831286fcc3827d0dbfb'
ENGINE_SHA256 = 'd61d56b294184afc401a20d26334fa6afb7667c8e115efc82c28016fa18874d9'
CLAIMS = {'reuss_shear', 'youngs_modulus_outer', 'poissons_ratio_outer'}
SOURCES = {'kochmann_milton_2014', 'meille_garboczi_2001'}


def declarations(raw):
    return {node.name + '.' + child.name for node in ast.parse(raw).body if isinstance(node, ast.ClassDef)
            for child in node.body if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))} | {
            node.name for node in ast.parse(raw).body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}


class SourceEvidenceCorrectionTests(unittest.TestCase):
    def setUp(self):
        self.evidence = history.load_evidence()
        self.ledger = history.load_ledger()

    def test_exact_current_pins_and_public_predecessor(self):
        self.assertEqual(history.digest((ROOT / history.LEDGER_PATH).read_bytes()), LEDGER_SHA256)
        self.assertEqual(history.digest(pre_material_bytes('tests/source_evidence_preservation.py', (ROOT / 'tests/source_evidence_preservation.py').read_bytes())), ADAPTER_SHA256)
        self.assertEqual(history.digest((ROOT / 'materials_boundaries/engine.py').read_bytes()), ENGINE_SHA256)
        self.assertEqual(len(BASE_RULES) + len(DERIVED_RULES), 8)
        self.assertEqual(self.evidence['review']['baseline_commit'], history.BASELINE_COMMIT)
        self.assertEqual(self.evidence['review']['baseline_tree'], history.BASELINE_TREE)
        self.assertFalse(self.evidence['review']['historical_review_claimed'])
        self.assertFalse(self.evidence['review']['independent_scientific_review'])
        self.assertEqual(len(self.evidence['metadata_changes']), 9)
        self.assertEqual(len(self.evidence['claim_version_changes']), 3)
        self.assertEqual(set(self.evidence['record_digests']['claims']), CLAIMS)
        self.assertEqual(set(self.evidence['record_digests']['sources']), SOURCES)
        entries = history.validate_ledger(self.ledger)
        self.assertEqual(set(entries), history.ALLOWED_PATHS)
        self.assertEqual(len(self.ledger['baseline_sha256']), 334)

    def test_exact_current_record_digests_and_reversible_field_deltas(self):
        for kind, digests in self.evidence['record_digests'].items():
            records = {record['id']: record for record in read_catalog(kind)['records']}
            for identifier, hashes in digests.items():
                current = records[identifier]; saved = deepcopy(current)
                predecessor = history.previous_record(kind, current)
                self.assertEqual(history.digest(history.canonical(current)), hashes['after'])
                self.assertEqual(history.digest(history.canonical(predecessor)), hashes['before'])
                self.assertEqual(current, saved)
                self.assertEqual(history.current_provenance(kind, identifier, predecessor), current)
                with self.assertRaises(AssertionError): history.previous_record(kind, predecessor)
        # The three identity revisions are not conflated with the nine facts.
        for entry in self.evidence['claim_version_changes']:
            self.assertEqual((entry['path'], entry['before'], entry['after']), (['version'], '1.1.0', '1.1.1'))

    def test_retained_science_identity_rights_and_unknown_originals(self):
        claims = {r['id']: r for r in read_catalog('claims')['records']}
        sources = {r['id']: r for r in read_catalog('sources')['records']}
        for rule in (*BASE_RULES, *DERIVED_RULES):
            verification = claims[rule[0]]['verification']
            self.assertEqual(verification['status'], 'software_tested_not_peer_reviewed')
            self.assertFalse(verification['independent_scientific_review'])
        reuss = claims['reuss_shear']['evidence'][0]
        self.assertEqual(reuss['verification_status'], 'standard_formula_with_context_source')
        self.assertIn('translated bulk-compliance', reuss['locator'])
        self.assertIn('original Reuss equation locator has not been established', reuss['locator'])
        for identifier in ('hs_bulk_3d_two_phase', 'hs_shear_3d_two_phase'):
            original = next(e for e in claims[identifier]['evidence'] if e['source_id'] == 'hashin_shtrikman_1963')
            self.assertIsNone(original['locator'])
            self.assertEqual(original['verification_status'], 'original_equation_not_inspected')
        for identifier in ('youngs_modulus_outer', 'poissons_ratio_outer'):
            record = claims[identifier]
            identity = next(e for e in record['evidence'] if e['source_id'] == 'meille_garboczi_2001')
            self.assertEqual(identity['verification_status'], 'algebraic_derivation_from_cited_identities')
            self.assertIn('3D isotropic identities only', identity['locator'])
            self.assertIn('2026-10-04', identity['locator'])
            self.assertEqual(len(record['verification']['gaps']), 3)
            self.assertTrue(any('joint-attainability' in gap for gap in record['verification']['gaps']))
            self.assertTrue(any('supplied assertions' in gap for gap in record['verification']['gaps']))
        source = sources['meille_garboczi_2001']
        self.assertEqual(source['read_status'], 'primary_paper_extracted_text_and_visual_equation_checked')
        self.assertEqual(source['license']['status'], 'copyright_iop_no_open_reuse_license_verified')
        self.assertIsNone(source['license']['identifier'])
        for identifier in SOURCES:
            before = history.previous_record('sources', sources[identifier])
            for field in ('license', 'bundled_content'):
                self.assertEqual(sources[identifier][field], before[field])
            self.assertEqual(sources[identifier]['provenance']['curation_date'], before['provenance']['curation_date'])

    def test_current_readme_supersedes_the_prior_failed_visual_check(self):
        text = (ROOT / 'README.md').read_text(encoding='utf-8')
        self.assertIn('此前截图/渲染核验未成功；2026-10-04 已', text)
        self.assertIn('此次仅核对恒等式来源，不是独立科学审查或证明核验。', text)
        self.assertNotIn('截图/渲染核验失败，因此不声称已完成视觉核验。', text)

    def test_old_and_new_status_labels_coexist_in_all_languages(self):
        for language in LANGUAGES:
            old = translate('catalog_status_primary_paper_extracted_text_equation_checked_visual_not_verified', language)
            current = translate('catalog_status_primary_paper_extracted_text_and_visual_equation_checked', language)
            self.assertNotIn('[missing:', old); self.assertNotIn('[missing:', current)
            self.assertNotEqual(old, current)

    def test_each_wrong_or_predecessor_field_and_duplicate_evidence_fails_closed(self):
        for entry in self.evidence['metadata_changes'] + self.evidence['claim_version_changes']:
            current = next(r for r in read_catalog(entry['catalog'])['records'] if r['id'] == entry['record_id'])
            for replacement in (entry['before'], 'unreviewed source correction'):
                bad = deepcopy(current); parent = bad
                for part in entry['path'][:-1]: parent = parent[part]
                parent[entry['path'][-1]] = deepcopy(replacement)
                with self.subTest(record=entry['record_id'], path=entry['path']), self.assertRaises((AssertionError, TypeError)):
                    history.previous_record(entry['catalog'], bad)
            if entry['path'][0] in ('claim_notes', 'evidence'):
                bad = deepcopy(current)
                collection = bad[entry['path'][0]]
                collection.append(deepcopy(collection[entry['path'][1]]))
                with self.assertRaises(AssertionError): history.previous_record(entry['catalog'], bad)
        current = next(r for r in read_catalog('claims')['records'] if r['id'] == 'youngs_modulus_outer')
        current['verification']['gaps'].append('Additional unreviewed gap stays visible')
        restored = history.previous_record('claims', current)
        self.assertIn('Additional unreviewed gap stays visible', restored['verification']['gaps'])

    def test_all_prior_fixtures_examples_schemas_and_unchanged_noncatalog_bytes(self):
        for filename, expected in self.ledger['baseline_sha256'].items():
            if filename.startswith('materials_boundaries/data/'):
                continue
            current = pre_material_bytes(filename, (ROOT / filename).read_bytes())
            with self.subTest(filename=filename):
                before = history.pre_evidence_bytes(filename, current)
                self.assertEqual(history.digest(before), expected)
                if filename.startswith(('tests/fixtures/', 'examples/', 'schemas/')):
                    self.assertEqual(current, before)
                if filename.startswith('tests/') and filename.endswith('.py'):
                    self.assertLessEqual(declarations(before), declarations(current))

    def test_every_integration_edit_round_trips_and_rejects_arbitrary_bytes(self):
        for entry in self.ledger['approved_existing_updates']:
            # Whole catalog bytes differ in intentional disposable append rehearsals;
            # complete historical objects are checked by the catalog guard instead.
            if entry['filename'].startswith('materials_boundaries/data/'):
                continue
            current = pre_material_bytes(entry['filename'], (ROOT / entry['filename']).read_bytes())
            before = history.reverse_exact_edits(current, entry)
            self.assertEqual(history.apply_exact_edits(before, entry['edits']), current)
            for wrong in (current + b'!', before):
                with self.assertRaises(AssertionError): history.pre_evidence_bytes(entry['filename'], wrong)

    def test_malformed_duplicate_missing_foreign_or_forged_ledger_is_rejected(self):
        mutations = [lambda x: x.update(extra=True), lambda x: x.update(schema_version=True),
            lambda x: x['review'].update(historical_review_claimed=True),
            lambda x: x['review'].update(baseline_commit='0'*40),
            lambda x: x['baseline_sha256'].pop('LICENSE'),
            lambda x: x['approved_existing_updates'].pop(),
            lambda x: x['approved_existing_updates'].append(deepcopy(x['approved_existing_updates'][0])),
            lambda x: x['approved_existing_updates'][0].update(filename='unreviewed.py'),
            lambda x: x['approved_existing_updates'][0].update(previous_sha256='0'*64),
            lambda x: x['approved_existing_updates'][0].update(reason=' '),
            lambda x: x['approved_existing_updates'][0]['edits'][0].update(offset=True)]
        for mutate in mutations:
            bad = deepcopy(self.ledger); mutate(bad)
            with self.assertRaises(AssertionError): history.validate_ledger(bad)
        with self.assertRaises(AssertionError): json.loads('{"a":1,"a":2}', object_pairs_hook=history.unique_keys)
        for key in ('metadata_changes', 'claim_version_changes'):
            for duplicate in (True, False):
                bad = deepcopy(self.evidence)
                if duplicate: bad[key].append(deepcopy(bad[key][0]))
                else: bad[key].pop()
                with tempfile.TemporaryDirectory() as directory:
                    path = Path(directory) / 'bad.json'; path.write_text(json.dumps(bad), encoding='utf-8')
                    with patch.object(history, 'EVIDENCE_PATH', str(path)), self.assertRaises(AssertionError):
                        history.load_evidence()

    def test_old_reports_are_stale_even_with_current_software_version(self):
        from materials_boundaries import composite, catalog
        instance = json.loads((ROOT / 'examples/synthetic-two-phase.json').read_text(encoding='utf-8'))
        current = build_composite_report(instance)
        real_reader = read_catalog
        def historical_reader(kind):
            return history.previous_catalog(kind, real_reader(kind))
        # Holding the software version fixed proves evidence staleness is real,
        # not merely a software-version mismatch. Production replay is untouched.
        with patch.object(composite, 'read_catalog', side_effect=historical_reader), patch.object(catalog, 'read_catalog', side_effect=historical_reader):
            old = build_composite_report(instance)
        self.assertEqual(old['engine_version'], current['engine_version'])
        self.assertEqual(old['input'], current['input'])
        self.assertEqual(old['policy'], current['policy'])
        self.assertNotEqual(old['digests']['claims'], current['digests']['claims'])
        self.assertNotEqual(old['digests']['sources'], current['digests']['sources'])
        self.assertEqual(old['evaluation'], current['evaluation'])
        for row in current['evaluation']['evaluations']:
            self.assertNotIn('claim_version', row)
        with self.assertRaises(CompositeReplayError): validate_composite_report(old)
        self.assertIsNone(validate_composite_report(build_composite_report(deepcopy(old['input']), old['output_unit'])))


if __name__ == '__main__':
    unittest.main()
