"""Eight reviewed density transcriptions, without material-specific runtime gates.

The frozen subset records source facts and their qualifications, not a permanent
catalog-size limit. Structural failures are generic contract failures; plausible
but unsupported scientific interpretations are checked against reviewed evidence
in tests, rather than by a production material-name/value whitelist.
"""
from contextlib import redirect_stdout
from copy import deepcopy
import hashlib
import io
import json
from pathlib import Path
import unittest

from materials_boundaries.catalog import read_catalog, query_catalog
from material_bulk_preservation import predecessor_record
from materials_boundaries.catalog_output import render_catalog
from materials_boundaries.cli import main
from materials_boundaries.material_references import validate_material_catalog

ROOT = Path(__file__).resolve().parents[1]
PUR = 'mat_ivdre2024_lpo1_rigid_pur'
AL = 'mat_kosenko2022_amd5_sps_foam'
CORK = 'mat_prasetia2024_qsuber_reproduction_cork'
MOSO = 'mat_drury2023_moso_bamboo_culm'
GUADUA = 'mat_drury2023_guadua_bamboo_culm'
PLASTER = 'mat_saadazzem2022_altaouab_cp_plaster'
BRICK = 'mat_mohajerani2019_boral_control_brick'
K1 = 'mat_jonczy2022_k1_quartz_arenite'
SELECTED = (PUR, AL, CORK, MOSO, GUADUA, PLASTER, BRICK, K1)
# Independent source decisions, not values inferred from the output fixture.
FACTS = {
    PUR: ('43.2', 'kg/m^3', 'apparent', 'reported_value', None, 'polymer'),
    AL: ('0.45', 'g/cm^3', 'not_stated', 'reported_value', None, 'metal'),
    CORK: ('0.17', 'g/cm^3', 'not_stated', 'reported_value', 10, 'natural'),
    MOSO: ('746', 'kg/m^3', 'not_stated', 'reported_mean', 6, 'natural'),
    GUADUA: ('655', 'kg/m^3', 'not_stated', 'reported_mean', 6, 'natural'),
    PLASTER: ('1103.13', 'kg/m^3', 'apparent', 'reported_value', None, 'inorganic'),
    BRICK: ('2122', 'kg/m^3', 'bulk', 'reported_value', None, 'inorganic'),
    K1: ('2.34', 'g/cm^3', 'bulk', 'reported_mean', 5, 'inorganic'),
}


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode()


def indexed(rows):
    return {row['id']: row for row in rows}


def assert_reviewed_subset(test, materials, properties, sources, fixture):
    """Preserve this reviewed subset while permitting new, separate facts."""
    props = indexed(properties['records'])
    states = indexed(materials['records'])
    identities = indexed(materials['identities'])
    for item in fixture['records']:
        test.assertEqual(predecessor_record('reference_properties', 'records', props[item['property_id']]), item['expected_property'])
        actual = deepcopy(predecessor_record('materials', 'records', states[item['state_id']]))
        expected = deepcopy(item['expected_material_state'])
        test.assertTrue(set(expected.pop('property_ids')).issubset(actual.pop('property_ids')))
        test.assertEqual(actual, expected)
        test.assertEqual(predecessor_record('materials', 'identities', identities[item['identity_id']]), item['expected_identity'])
    for expected in fixture['sources']:
        test.assertEqual(indexed(sources['records'])[expected['id']], expected)
    for expected in fixture['grades']:
        test.assertEqual(indexed(materials['grades'])[expected['id']], expected)


class FifthMaterialBatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.materials = read_catalog('materials')
        cls.properties = read_catalog('reference_properties')
        cls.sources = read_catalog('sources')
        cls.props = indexed(cls.properties['records'])
        cls.states = indexed(cls.materials['records'])
        cls.identities = indexed(cls.materials['identities'])
        cls.fixture = json.loads((ROOT / 'tests/fixtures/fifth_batch_source_transcription_v0330.json').read_text())
        cls.selected = {r['identity_id']: r for r in cls.fixture['records']}

    def property(self, identity):
        return self.props[self.selected[identity]['property_id']]

    def state(self, identity):
        return self.states[self.selected[identity]['state_id']]

    def combined_text(self, identity):
        return json.dumps({'identity': self.identities[identity],
                           'state': self.state(identity),
                           'property': self.property(identity)}, ensure_ascii=False).lower()

    def test_eight_distinct_source_qualified_identities_and_exact_density_values(self):
        validate_material_catalog(self.materials, self.properties, self.sources)
        self.assertEqual(set(self.selected), set(SELECTED))
        self.assertEqual(len({self.selected[k]['property_id'] for k in SELECTED}), 8)
        self.assertEqual(len({self.selected[k]['state_id'] for k in SELECTED}), 8)
        self.assertEqual(len({self.property(k)['source_id'] for k in SELECTED}), 7)
        for key, (number, unit, basis, statistic, n, category) in FACTS.items():
            with self.subTest(identity=key):
                p, state = self.property(key), self.state(key)
                self.assertEqual(p['quantity'], 'mass_density')
                self.assertEqual(p['reported_value']['kind'], 'scalar')
                self.assertEqual((p['reported_value']['number'], p['reported_value']['value_text'],
                                  p['reported_value']['unit_code']), (number, number, unit))
                self.assertEqual(p['density_basis'], basis)
                self.assertEqual(p['summary_statistic'], statistic)
                self.assertEqual(p['sample_count']['value'], n)
                self.assertEqual(state['identity_id'], key)
                self.assertIn(p['id'], state['property_ids'])
                self.assertEqual(self.identities[key]['category'], category)
                self.assertIsNone(state['grade_id'])
                self.assertEqual(p['evidence_kind'], 'published_experimental_reference')
                self.assertEqual(p['determination_basis'], 'source_reports_measurement')
                self.assertEqual(p['evaluation_support'], 'catalog_only')
                self.assertIs(p['universal_bound'], False)
                self.assertIs(p['engineering_allowable'], False)
                self.assertIs(p['verification']['independent_scientific_review'], False)
                self.assertIs(p['verification']['raw_data_reanalysis'], False)
        self.assertFalse(any(g['identity_id'] in SELECTED for g in self.materials['grades']))

    def test_existing_objects_remain_unchanged(self):
        catalogs = {'materials': self.materials, 'reference_properties': self.properties,
                    'sources': self.sources}
        for name, collections in self.fixture['baseline_sha256'].items():
            for collection, records in collections.items():
                actual = indexed(catalogs[name][collection])
                for record_id, digest in records.items():
                    with self.subTest(catalog=name, collection=collection, record=record_id):
                        self.assertEqual(hashlib.sha256(canonical(predecessor_record(name, collection, actual[record_id]))).hexdigest(), digest)

    def test_full_reviewed_transcriptions_and_source_scopes_are_preserved(self):
        assert_reviewed_subset(self, self.materials, self.properties, self.sources, self.fixture)

    def test_legitimate_future_appends_do_not_fail_source_fixture_gate(self):
        materials, properties, sources = map(deepcopy, (self.materials, self.properties, self.sources))
        # Synthetic future fact for an existing state, not an admitted measurement.
        future = deepcopy(self.property(PUR))
        future['id'] = 'refprop_future_fifth_batch_synthetic_test_only'
        future['reported_value'].update(number='43.3', value_text='43.3')
        future['evidence'][0]['locator'] = 'Synthetic future separate result, Table 99'
        properties['records'].append(future)
        indexed(materials['records'])[future['material_state_id']]['property_ids'].append(future['id'])
        validate_material_catalog(materials, properties, sources)
        assert_reviewed_subset(self, materials, properties, sources, self.fixture)

    def test_all_density_test_temperatures_remain_unknown(self):
        for key in SELECTED:
            with self.subTest(identity=key):
                fact = self.property(key)['conditions']['temperature']
                self.assertEqual(fact['status'], 'not_reported_in_inspected_source')
                self.assertIsNone(fact['text'])
                self.assertTrue(fact['notes'])

    def test_only_cork_and_k1_have_reported_density_uncertainty(self):
        for key in set(SELECTED) - {CORK, K1}:
            with self.subTest(identity=key):
                p = self.property(key)
                self.assertIsNone(p['uncertainty'])
                self.assertEqual(p['uncertainty_status'], 'not_reported_in_inspected_source')
        cork = self.property(CORK)
        self.assertEqual(cork['summary_statistic'], 'reported_value')
        self.assertEqual(cork['uncertainty_status'], 'reported_measures')
        self.assertEqual(cork['uncertainty']['type'], 'reported_measures')
        measure, = cork['uncertainty']['measures']
        self.assertEqual((measure['kind'], measure['availability'], measure['basis']),
                         ('standard_deviation', 'numeric_reported', 'absolute'))
        self.assertEqual((measure['reported_value']['number'], measure['reported_value']['value_text'],
                          measure['reported_value']['unit_code']), ('0.01', '0.01', 'g/cm^3'))
        self.assertIsNone(measure['confidence_level'])
        self.assertIsNone(measure['coverage_factor'])
        k1 = self.property(K1)
        self.assertEqual(k1['uncertainty_status'], 'reported_plus_minus_unspecified')
        self.assertEqual(k1['uncertainty']['type'], 'reported_plus_minus_unspecified')
        self.assertEqual((k1['uncertainty']['number'], k1['uncertainty']['value_text'],
                          k1['uncertainty']['unit_code']), ('0.01', '0.01', 'g/cm^3'))
        self.assertIsNone(k1['uncertainty']['confidence_level'])
        self.assertIsNone(k1['uncertainty']['coverage_factor'])

    def test_optimized_pur_is_lupranol_control_not_model_target_or_spo(self):
        p, state = self.property(PUR), self.state(PUR)
        self.assertIn('Lupranol', self.identities[PUR]['identity_scope'])
        self.assertIn('not the suberin-based SPO', self.identities[PUR]['identity_scope'])
        composition = state['state']['composition_or_purity']
        for text in ('Lupranol 3300 40 g', 'Lupranol 3422 60 g', 'total water 2.0 g',
                     'Opteon 1100 16.3 g', 'Polycat NP10 4 g', 'PC CAT TKA 30 0.5 g',
                     'Niax Silicone L-6915 2.5 g', 'TCPP 25.3 g',
                     'pMDI (Desmodur 44 V20 L) 165 g', '8 wt.%', 'NCO/OH ratio 1.2'):
            self.assertIn(text, composition['text'])
        self.assertIn('not a measured cured-foam', composition['notes'])
        self.assertIn('Table 9 LPO-1 column and footnotes', composition['evidence'][0]['locator'])
        self.assertIn('45 kg/m³', p['basis_note'])
        self.assertIn('40 kg/m³', p['basis_note'])
        self.assertEqual(p['conditions']['test_standard']['text'], 'ISO 845:2006')
        self.assertIn('24 h', state['state']['conditioning']['text'])
        self.assertIn('94 vol.%', state['state']['porosity']['text'])
        self.assertIn('not total porosity', state['state']['porosity']['notes'])
        self.assertIn('MRSM cup tests', p['sample_count']['scope'])
        self.assertIn('6 cylinders', p['sample_count']['scope'])

    def test_aluminum_keeps_input_alloy_sealed_weighing_and_discrepancies(self):
        p, state = self.property(AL), self.state(AL)
        composition = state['state']['composition_or_purity']
        for text in ('94.8 wt.% Al', '4.8 wt.% Mg', '0.4 wt.% Ti', '10:90', '8:92'):
            self.assertIn(text, composition['text'])
        self.assertIn('not a final bulk chemical assay', composition['notes'])
        self.assertIn('not pure aluminum', self.identities[AL]['identity_scope'])
        self.assertIn('Do not import the ASD6', state['source_scope'])
        for text in ('NaCl space holders', 'average particle size 500–1000 µm',
                     '550 °C', '38 MPa', '5 min', '12 h'):
            self.assertIn(text, state['state']['processing']['text'])
        for text in ('paraffin', 'ethanol', 'not a skeletal density'):
            self.assertIn(text, p['method_definition']['definition'])
        self.assertEqual(p['conditions']['test_standard']['status'], 'not_reported_in_inspected_source')
        self.assertIn('fluid-density reference', p['conditions']['temperature']['notes'])
        descriptions = ' '.join(d['description'] for d in p['source_discrepancies'])
        for text in ('Table 6', 'g/m³', 'g/cm³', 'Underwater Weight', 'ethanol'):
            self.assertIn(text, descriptions)

    def test_cork_exclusions_sample_scope_and_conditioning_are_explicit(self):
        p, state = self.property(CORK), self.state(CORK)
        self.assertIn('Quercus suber', self.identities[CORK]['names']['zh'])
        self.assertIn('not an agglomerated binder composite', state['source_scope'])
        self.assertIn('Do not count boiled cork', state['source_scope'])
        self.assertIn('or import Q. variabilis virgin-cork green density', state['source_scope'])
        self.assertIn('Do not label never-treated cork', state['state']['processing']['notes'])
        self.assertIn('25 ± 5 °C', state['state']['conditioning']['text'])
        self.assertIn('60 ± 5%', state['state']['conditioning']['text'])
        self.assertIn('not exact density-test temperature or RH', state['state']['conditioning']['notes'])
        self.assertIn('Ten specimens', p['sample_count']['scope'])
        self.assertIn('no independence of trees', p['sample_count']['scope'])
        self.assertEqual(p['conditions']['test_standard']['text'], 'KS F 2198')
        self.assertIn('volume-measurement subprocedure is not stated', p['method_definition']['definition'])
        self.assertIn('never mean ± SD', p['uncertainty_note'])
        extras = {e['name']: e['fact'] for e in p['conditions']['additional_conditions']}
        self.assertIn('4.61%', extras['moisture_content']['text'])
        self.assertIn('0.34 percentage points', extras['moisture_content']['text'])
        self.assertIn('not density uncertainty', extras['moisture_content']['notes'])

    def test_bamboo_treatments_cohort_moisture_and_exclusions_stay_distinct(self):
        for key, species in ((MOSO, 'Moso'), (GUADUA, 'Guadua')):
            p, state = self.property(key), self.state(key)
            self.assertIn('not an engineered resin-bonded laminate', state['source_scope'])
            self.assertIn('not additional identities', state['source_scope'])
            self.assertIn('Do not label generic untreated bamboo', state['source_scope'])
            self.assertIn('fumigated for up to 24 h', state['state']['processing']['text'])
            self.assertIn('Stored for one year', state['state']['conditioning']['text'])
            self.assertIn('p.6', state['state']['conditioning']['evidence'][0]['locator'])
            self.assertIn('three nodal and three internodal', p['sample_count']['scope'])
            self.assertIn('separate culms', p['sample_count']['scope'])
            self.assertIn('p.3', p['sample_count']['evidence'][0]['locator'])
            self.assertIn('p.7', p['sample_count']['evidence'][0]['locator'])
            self.assertEqual(p['conditions']['test_method']['status'], 'not_reported_in_inspected_source')
            self.assertEqual(p['conditions']['test_standard']['status'], 'not_reported_in_inspected_source')
            self.assertIn('Do not derive density', p['basis_note'])
            self.assertIn('Do not call this skeletal density or density including the hollow culm central lumen',
                          p['method_definition']['definition'])
            extras = {e['name']: e['fact'] for e in p['conditions']['additional_conditions']}
            moisture = extras['cohort_moisture_context']
            self.assertIn('15.8% average', moisture['text'])
            self.assertIn('entire experimental cohort', moisture['text'])
            self.assertIn('Do not assign 15.8% to every ' + species, moisture['notes'])
            self.assertIn('p.6', moisture['evidence'][0]['locator'])
            discrepancy = p['source_discrepancies'][0]
            self.assertIn('CC BY 3.0', discrepancy['description'])
            self.assertIn('CC BY 4.0', discrepancy['description'])
        self.assertIn('No borax treatment is stated', self.state(MOSO)['state']['processing']['text'])
        for text in ('Dipped in borax', 'internal nodes pierced'):
            self.assertIn(text, self.state(GUADUA)['state']['processing']['text'])

    def test_mineral_preparation_statistics_and_volume_ambiguity_are_qualified(self):
        plaster, brick, k1 = (self.property(k) for k in (PLASTER, BRICK, K1))
        ps, bs = self.state(PLASTER)['state'], self.state(BRICK)['state']
        self.assertIn('0.7', ps['processing']['text'])
        self.assertIn('72 h', ps['processing']['text'])
        self.assertIn('28 days', ps['processing']['text'])
        self.assertIn('Do not call the cured material pure dihydrate', ps['composition_or_purity']['text'])
        self.assertIn('density-specific specimen dimensions are unknown', ps['product_form']['notes'])
        for text in ('20–30 °C', '5% setup accuracy', '60 °C/24 h'):
            self.assertIn(text, plaster['conditions']['temperature']['notes'])
        self.assertIn('100 wt.%', bs['composition_or_purity']['text'])
        self.assertIn('0% biosolids', bs['composition_or_purity']['text'])
        self.assertIn('1100 °C', bs['processing']['text'])
        self.assertIn('raw-material', brick['sample_count']['scope'])
        self.assertIn('shrinkage', brick['sample_count']['scope'])
        self.assertIn('Do not assign density n=3', brick['sample_count']['scope'])
        extras = {e['name']: e['fact'] for e in brick['conditions']['additional_conditions']}
        self.assertIn('regression-estimated', extras['excluded_conductivity']['text'])
        self.assertIn('Do not import', extras['excluded_conductivity']['notes'])
        self.assertIn('Five physical-property replicates', k1['sample_count']['scope'])
        self.assertIn('no independence of geological sampling sites', k1['sample_count']['scope'])
        self.assertIn('without claiming an explicitly specified arithmetic', k1['basis_note'])
        self.assertIn('does not unambiguously select exclusively geometric versus hydrostatic',
                      k1['method_definition']['definition'])
        self.assertIn('EN 1926:2007', k1['conditions']['test_standard']['notes'])
        self.assertIn('must not be transferred', k1['conditions']['test_standard']['notes'])
        self.assertIn('do not assert exact mine/site', self.state(K1)['source_scope'])
        self.assertIn('Do not call it SD, SE, CI', k1['uncertainty_note'])

    def test_recorded_original_document_hashes_and_article_licenses(self):
        sources = indexed(self.sources['records'])
        evidence = {r['identity_id']: r for r in self.fixture['independent_transcriptions']}
        self.assertEqual(set(evidence), set(SELECTED))
        for key in SELECTED:
            p, original = self.property(key), evidence[key]
            doc, source = p['source_document'], sources[p['source_id']]
            with self.subTest(identity=key):
                self.assertEqual(doc['hash_status'], 'recorded')
                self.assertEqual(doc['sha256'], original['source_sha256'])
                self.assertEqual(doc['url'], original['source_url'])
                self.assertIn(doc['url'], source['urls'])
                self.assertIn(doc['sha256'], ' '.join(source['claim_notes']))
                self.assertEqual(source['doi'], original['source_doi'])
                self.assertEqual(source['license']['identifier'], 'CC-BY-4.0')
                self.assertTrue(source['authors'])
                self.assertTrue(source['title'])
                self.assertIn('no_source_assets', source['bundled_content'])
                self.assertNotIn('/workspace/', json.dumps(source))
                self.assertEqual(p['reported_value']['value_text'], original['reported_value_text'])
                self.assertEqual(p['reported_value']['unit_code'], original['source_unit_code'])
                self.assertEqual(p['density_basis'], original['density_basis'])
                self.assertEqual(p['summary_statistic'], original['summary_statistic'])
                self.assertEqual(p['sample_count']['value'], original['sample_count'])
                self.assertEqual(p['uncertainty_status'], original['uncertainty_status'])

    def test_four_language_names_and_json_text_cli_retain_source_semantics(self):
        for key in SELECTED:
            p, state, identity = self.property(key), self.state(key), self.identities[key]
            for obj in (identity, state):
                self.assertEqual(set(obj['names']), {'en', 'zh', 'ja', 'de'})
                self.assertTrue(all(isinstance(n, str) and n.strip() for n in obj['names'].values()))
            for lang in ('en', 'zh', 'ja', 'de'):
                selected = query_catalog('reference-properties', record_id=p['id'])
                text = render_catalog(selected, 'reference-properties', lang)
                self.assertIn(p['reported_value']['value_text'], text)
                self.assertIn(p['uncertainty_note'], text)
                self.assertIn(p['sample_count']['scope'], text)
                for flag in ('--text', '--json'):
                    stdout = io.StringIO()
                    with redirect_stdout(stdout):
                        code = main(['catalog', 'reference-properties', '--id', p['id'], flag, '--lang', lang])
                    self.assertEqual(code, 0)
                    if flag == '--json':
                        self.assertEqual(json.loads(stdout.getvalue()), selected)
                    else:
                        self.assertEqual(stdout.getvalue().rstrip('\n'), text)

    def test_generic_contract_rejects_structural_mutations(self):
        for key in SELECTED:
            for mutation in ('unknown_source', 'wrong_document', 'missing_primary_method',
                             'bad_decimal', 'unknown_temperature_with_text', 'wrong_quantity_unit'):
                altered = deepcopy(self.properties)
                p = indexed(altered['records'])[self.selected[key]['property_id']]
                if mutation == 'unknown_source':
                    p['evidence'][0]['source_id'] = 'unknown_fifth_batch_source'
                elif mutation == 'wrong_document':
                    p['source_document']['url'] = 'https://example.invalid/wrong.pdf'
                elif mutation == 'missing_primary_method':
                    p['method_definition']['evidence'] = []
                elif mutation == 'bad_decimal':
                    p['reported_value']['number'] = 'NaN'
                elif mutation == 'unknown_temperature_with_text':
                    p['conditions']['temperature']['text'] = '25 °C'
                else:
                    p['reported_value']['unit_code'] = 'MPa'
                with self.subTest(identity=key, mutation=mutation), self.assertRaises(ValueError):
                    validate_material_catalog(self.materials, altered, self.sources)
        for key in (CORK, K1):
            altered = deepcopy(self.properties)
            p = indexed(altered['records'])[self.selected[key]['property_id']]
            uncertainty = p['uncertainty']
            if key == CORK:
                uncertainty = uncertainty['measures'][0]
            if key == CORK:
                uncertainty['evidence'][0]['locator'] = 'Different unsupported Table 99'
            else:
                uncertainty['evidence'][0]['source_id'] = 'unknown_fifth_batch_source'
            with self.subTest(identity=key, mutation='unbound_uncertainty'), self.assertRaises(ValueError):
                validate_material_catalog(self.materials, altered, self.sources)

    def test_source_conditioned_statistical_and_method_mutations_are_not_runtime_whitelists(self):
        cases = [
            (PUR, 'optimization target', lambda p: p['reported_value'].update(number='45', value_text='45')),
            (PUR, 'cup-test n', lambda p: p['sample_count'].update(value=3, relation='exact')),
            (AL, 'compression n', lambda p: p['sample_count'].update(value=3, relation='exact')),
            (AL, 'inferred density label', lambda p: p.update(density_basis='bulk')),
            (AL, 'unqualified solid density', lambda p: p.update(density_basis='true')),
            (AL, 'erased source discrepancy', lambda p: p.update(source_discrepancies=[])),
            (CORK, 'inferred mean', lambda p: p.update(summary_statistic='reported_mean')),
            (CORK, 'independent tree count', lambda p: p['sample_count'].update(scope='Ten independent trees')),
            (CORK, 'inferred volume procedure', lambda p: p['method_definition'].update(definition='Volume determined exclusively by geometric measurements')),
            (MOSO, 'doubled specimen count', lambda p: p['sample_count'].update(value=12)),
            (GUADUA, 'plantation independence', lambda p: p['sample_count'].update(scope='Six independent plantations')),
            (MOSO, 'reconstructed ratio of means', lambda p: p['reported_value'].update(number='721', value_text='721')),
            (PLASTER, 'thermal accuracy reused', lambda p: p.update(uncertainty_note='Density setup accuracy is 5%')),
            (BRICK, 'raw-material n', lambda p: p['sample_count'].update(value=3, relation='exact')),
            (BRICK, 'raw-material mean', lambda p: p.update(summary_statistic='reported_mean')),
            (K1, 'geological site independence', lambda p: p['sample_count'].update(scope='Five independent mine sites')),
            (K1, 'resolved volume ambiguity', lambda p: p['method_definition'].update(definition='Dry mass divided by exclusively geometrically determined volume')),
            (K1, 'wrong uncertainty locator', lambda p: p['uncertainty']['evidence'][0].update(locator='Different unsupported Table 99')),
        ]
        for key, label, mutate in cases:
            altered = deepcopy(self.properties)
            prop = indexed(altered['records'])[self.selected[key]['property_id']]
            mutate(prop)
            if label in ('inferred mean', 'raw-material mean'):
                # Invent the corresponding evidence declaration in this synthetic
                # mutation too. Otherwise the generic missing-tag guard rejects
                # it before this independent source-fidelity gate is exercised.
                prop['evidence'][0]['supports'].append('summary_statistic')
            validate_material_catalog(self.materials, altered, self.sources)
            with self.subTest(identity=key, mutation=label), self.assertRaises(AssertionError):
                assert_reviewed_subset(self, self.materials, altered, self.sources, self.fixture)
        # The source's undefined plus/minus is structurally representable as SD,
        # but its scientific meaning still requires the independent source gate.
        altered = deepcopy(self.properties)
        p = indexed(altered['records'])[self.selected[K1]['property_id']]
        p['uncertainty']['type'] = 'reported_standard_deviation'
        p['uncertainty_status'] = 'reported_standard_deviation'
        validate_material_catalog(self.materials, altered, self.sources)
        with self.assertRaises(AssertionError):
            assert_reviewed_subset(self, self.materials, altered, self.sources, self.fixture)

    def test_source_conditioned_identity_and_treatment_mutations_reject_false_scopes(self):
        cases = [
            (PUR, 'composition_or_purity', 'Suberin-based SPO cured-foam formulation'),
            (AL, 'composition_or_purity', 'Pure aluminum, certified final alloy composition'),
            (CORK, 'processing', 'Historically never-treated cork'),
            (MOSO, 'processing', 'Untreated bamboo without fumigation'),
            (GUADUA, 'processing', 'Untreated bamboo without borax or fumigation'),
            (PLASTER, 'composition_or_purity', 'Chemically pure calcium sulfate dihydrate'),
            (BRICK, 'composition_or_purity', '25% biosolids commercial Boral grade'),
        ]
        for key, field, text in cases:
            altered = deepcopy(self.materials)
            indexed(altered['records'])[self.selected[key]['state_id']]['state'][field]['text'] = text
            validate_material_catalog(altered, self.properties, self.sources)
            with self.subTest(identity=key, field=field), self.assertRaises(AssertionError):
                assert_reviewed_subset(self, altered, self.properties, self.sources, self.fixture)
        for key in (CORK, MOSO, GUADUA):
            altered = deepcopy(self.materials)
            indexed(altered['identities'])[key]['category'] = 'polymer'
            validate_material_catalog(altered, self.properties, self.sources)
            with self.subTest(identity=key, mutation='unqualified category'), self.assertRaises(AssertionError):
                assert_reviewed_subset(self, altered, self.properties, self.sources, self.fixture)
            altered = deepcopy(self.materials)
            # Removing an exclusion is a source-semantic change even though the
            # resulting text still satisfies every structural schema constraint.
            indexed(altered['identities'])[key]['identity_scope'] = 'Generic untreated natural material'
            validate_material_catalog(altered, self.properties, self.sources)
            with self.subTest(identity=key, mutation='erased explicit exclusions'), self.assertRaises(AssertionError):
                assert_reviewed_subset(self, altered, self.properties, self.sources, self.fixture)

    def test_source_conditioned_scalar_and_temperature_mutations_need_reviewed_evidence(self):
        for key in SELECTED:
            for mutation in ('different_scalar', 'invented_test_temperature'):
                altered = deepcopy(self.properties)
                p = indexed(altered['records'])[self.selected[key]['property_id']]
                if mutation == 'different_scalar':
                    p['reported_value'].update(number='123', value_text='123')
                else:
                    p['conditions']['temperature'].update(status='reported', text='25 °C',
                                                           evidence=deepcopy(p['evidence']))
                # Both are structurally legal. Their source truth is deliberately
                # checked here, not by material-name exceptions in runtime code.
                validate_material_catalog(self.materials, altered, self.sources)
                with self.subTest(identity=key, mutation=mutation), self.assertRaises(AssertionError):
                    assert_reviewed_subset(self, self.materials, altered, self.sources, self.fixture)


if __name__ == '__main__':
    unittest.main()
