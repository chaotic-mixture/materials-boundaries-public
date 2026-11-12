"""Fictional source-only fitted area ratios, not a spectral analysis engine."""
from copy import deepcopy
from decimal import localcontext
import hashlib,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from jsonschema import Draft202012Validator
from materials_boundaries._ftir_band_area_ratio_contract import QUANTITY,UNIT,METHOD,PROFILE,WAVENUMBER_UNIT,FACT_FIELDS,LABEL_KEYS
from materials_boundaries.material_references import _PROPERTIES_SCHEMA,validate_material_catalog,resolve_material
from materials_boundaries.material_presentation import material_labels,render_material_catalog
from materials_boundaries.database import Database,read_snapshot
from test_gel_fraction_contract import as_gel_fraction,fixture as gel_fixture
from test_material_uncertainty_contract import uncertainty_catalog
from test_material_reported_measures_contract import synthetic_reported_measures_catalog
from test_tga_endpoint_contract import add_clone
ROOT=Path(__file__).resolve().parents[1]


def as_area_ratio(graph):
    graph=as_gel_fraction(graph);p=graph[1]['records'][0];p.pop('gel_fraction_definition')
    p.update(quantity=QUANTITY,evidence_kind='published_measurement_derived_reference',determination_basis='source_reports_calculation',source_property_label='Fictional fitted carbonyl band area ratio')
    p['reported_value'].update(number='2.35',value_text='2.35',unit_code=UNIT,unit_text='ratio')
    ev=deepcopy(p['method_definition']['evidence'])
    for e in ev:e['supports']=['method','condition','classification','reported_value']
    p['method_definition'].update(type=METHOD,evidence=deepcopy(ev))
    unknown=dict(status='not_verified',text=None,evidence=deepcopy(ev),notes='Unresolved method details,not an assumed value.')
    d=dict(schema_version='1.0.0',profile_id=PROFILE,profile_version='1.0.0',executor='source_reported_only',formula_family='source_ordered_fitted_area_ratio',lineshape='source_reported_gaussian',**{n:deepcopy(unknown) for n in FACT_FIELDS},evidence=deepcopy(ev),notes='Fictional author result only;no software spectral processing.')
    d['reported_formula'].update(status='reported',text='Source reports fitted integrated A1720/A1740.')
    d['fit_model_width_constraints_and_intervals'].update(status='reported',text='Source Gaussian fitting,width10cm^-1;fit intervals unreported.')
    for name,number in [('numerator_band','1720'),('denominator_band','1740')]:
        d[name]=dict(role='gaussian_fitted_integrated_carbonyl_band_area',number=number,value_text=number,unit_code=WAVENUMBER_UNIT,unit_text='cm⁻¹',evidence=deepcopy(ev),notes='Band center only,not raw area or its sign.')
    d['source_result_cell']=dict(table_id='fictional-table-4',row_key='fictional-sample',column_key='carbonyl-index',evidence=deepcopy(ev),notes='Original primary result address;corrections revise this cell.')
    p['derivation']=d;return graph


def fixture():return as_area_ratio(gel_fixture())
def check(g):Draft202012Validator(_PROPERTIES_SCHEMA).validate(g[1]);validate_material_catalog(*g)
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()


class FTIRAreaRatioContractTests(unittest.TestCase):
    def test_old28branches_and_all_definitions_preserved(self):
        baseline=json.loads((ROOT/'tests/fixtures/ftir_band_area_ratio_schema_baseline.json').read_bytes());s=json.loads((ROOT/'schemas/reference_properties.schema.json').read_bytes());self.assertEqual(s,_PROPERTIES_SCHEMA);Draft202012Validator.check_schema(s);self.assertEqual(len(s['$defs']['property']['oneOf']),31);self.assertEqual(digest(s['$defs']['property']['oneOf'][:28]),baseline['old_branch_digest'])
        for k,h in baseline['old_definition_digests'].items():self.assertEqual(digest(s['$defs'][k]),h,k)

    def test_reported_ratio_is_not_recomputed(self):
        g=fixture();p=g[1]['records'][0];p['reported_value'].update(number='999.125',value_text='999.125');before=deepcopy(g);check(g);self.assertEqual(g,before)
        p['derivation']['executor']='software_recomputed'
        with self.assertRaises(ValueError):validate_material_catalog(*g)

    def test_quantity_method_profile_classification_agree_both_ways(self):
        for field,value in [('quantity','dsc_reference_normalized_crystallinity_percentage'),('evidence_kind','published_experimental_reference'),('determination_basis','source_reports_measurement')]:
            g=fixture();g[1]['records'][0][field]=value
            with self.assertRaises(ValueError):validate_material_catalog(*g)
        for field,value in [('profile_id','source_dsc_reference_enthalpy_normalization_v1'),('profile_version','2.0.0'),('formula_family','peak_height_ratio'),('lineshape','lorentzian')]:
            g=fixture();g[1]['records'][0]['derivation'][field]=value
            with self.assertRaises(ValueError):validate_material_catalog(*g)
        g=fixture();g[1]['records'][0]['method_definition']['type']='source_reported_conventional'
        with self.assertRaises(ValueError):validate_material_catalog(*g)

    def test_finite_nonnegative_domain_without_percentage_cap(self):
        for token in ['0','2.35','100.000','999999.123456789012345678901234']:
            g=fixture();g[1]['records'][0]['reported_value'].update(number=token,value_text=token)
            with localcontext() as c:c.prec=2;check(g)
        for token in ['-0.01','NaN','Infinity','2e0',True]:
            g=fixture();g[1]['records'][0]['reported_value'].update(number=token,value_text=str(token))
            with self.assertRaises(ValueError):validate_material_catalog(*g)
        for unit in ['percent','percent_dsc_reference_crystallinity',WAVENUMBER_UNIT]:
            g=fixture();g[1]['records'][0]['reported_value']['unit_code']=unit
            with self.assertRaises(ValueError):validate_material_catalog(*g)

    def test_band_coordinate_not_area_positive_typed_and_precise(self):
        for field in ('numerator_band','denominator_band'):
            for update in [dict(number='0',value_text='0'),dict(number='-1',value_text='-1'),dict(value_text='1720.00'),dict(unit_code='Hz'),dict(role='peak_height'),dict(actual_area='1')]:
                g=fixture();g[1]['records'][0]['derivation'][field].update(update)
                with self.subTest(field=field,update=update),self.assertRaises(ValueError):validate_material_catalog(*g)
        g=fixture();check(g);self.assertNotIn('actual_area',g[1]['records'][0]['derivation']['denominator_band'])

    def test_all_fact_fields_and_strict_unknowns(self):
        for name in FACT_FIELDS:
            for bad in ('missing','unknown_with_text','blank_notes','foreign_document'):
                g=fixture();d=g[1]['records'][0]['derivation']
                if bad=='missing':del d[name]
                elif bad=='unknown_with_text':d[name].update(status='not_verified',text='assumed')
                elif bad=='blank_notes':d[name]['notes']=' '
                else:d[name]['evidence'][0]['url']='https://example.invalid/other.xml'
                with self.subTest(name=name,bad=bad),self.assertRaises(ValueError):validate_material_catalog(*g)

    def test_formula_and_gaussian_method_must_be_source_reported(self):
        for name in ('reported_formula','fit_model_width_constraints_and_intervals'):
            g=fixture();g[1]['records'][0]['derivation'][name].update(status='not_verified',text=None)
            with self.assertRaises(ValueError):validate_material_catalog(*g)
        g=fixture();check(g);self.assertEqual(g[1]['records'][0]['derivation']['integration_and_ratio_averaging_order']['status'],'not_verified')

    def test_derivation_bands_cell_and_facts_need_primary_role_evidence(self):
        for name in ('derivation','numerator_band','denominator_band','source_result_cell','reported_formula'):
            for bad in ('empty','other_document','missing_role'):
                g=fixture();d=g[1]['records'][0]['derivation'];target=d if name=='derivation' else d[name]
                if bad=='empty':target['evidence']=[]
                elif bad=='other_document':target['evidence'][0]['url']='https://example.invalid/other.xml'
                else:target['evidence'][0]['supports']=['condition']
                with self.subTest(name=name,bad=bad),self.assertRaises(ValueError):validate_material_catalog(*g)

    def test_original_result_address_required(self):
        for name in ('table_id','row_key','column_key'):
            for value in ('',' ',' changed '):
                g=fixture();g[1]['records'][0]['derivation']['source_result_cell'][name]=value
                with self.assertRaises(ValueError):validate_material_catalog(*g)

    def test_same_cell_revisions_cannot_be_parallel_facts(self):
        for change in ('bands','definition','statistics','value','conditions','locator'):
            for reverse in (False,True):
                g=fixture();clone=add_clone(g);d=clone['derivation']
                if change=='bands':d['numerator_band'],d['denominator_band']=d['denominator_band'],d['numerator_band']
                elif change=='definition':d['integration_and_ratio_averaging_order'].update(status='reported',text='Source processing now clarified.')
                elif change=='statistics':clone['sample_count'].update(value=4,relation='exact')
                elif change=='value':clone['reported_value'].update(number='2.3500',value_text='2.3500')
                elif change=='conditions':clone['conditions']['temperature']['text']='Changed annotation'
                else:
                    for e in clone['evidence']:
                        if 'reported_value' in e['supports']:e['locator']='Reworded same source cell'
                if reverse:g[1]['records'].reverse()
                with self.subTest(change=change,reverse=reverse),self.assertRaises(ValueError):validate_material_catalog(*g)
        g=fixture();clone=add_clone(g);clone['reported_value'].update(number='2.40',value_text='2.40')
        with self.assertRaises(ValueError):validate_material_catalog(*g)

    def test_distinct_actual_source_cells_remain_distinct(self):
        g=fixture();clone=add_clone(g);clone['derivation']['source_result_cell']['column_key']='Actual other source protocol column'
        for e in clone['evidence']:
            if 'reported_value' in e['supports']:e['locator']='Actual other source protocol column'
        check(g)

    def test_absolute_ratio_uncertainty_and_relative_cv(self):
        g=as_area_ratio(uncertainty_catalog());p=g[1]['records'][0];p['uncertainty'].update(unit_code=UNIT,unit_text='ratio',number='150',value_text='150');check(g)
        p['uncertainty'].update(number='-1',value_text='-1')
        with self.assertRaises(ValueError):validate_material_catalog(*g)
        g=as_area_ratio(synthetic_reported_measures_catalog('cv'));check(g);a=g[1]['records'][0]['uncertainty']['measures'][0]['reported_value'];self.assertEqual(a['unit_code'],'percent');a.update(unit_code=UNIT,unit_text='ratio')
        with self.assertRaises(ValueError):validate_material_catalog(*g)

    def test_actual_areas_compute_flags_and_foreign_roles_are_closed(self):
        for key,value in [('actual_numerator_area','1'),('actual_denominator_area','1'),('computed_result','2.35'),('recompute',True)]:
            g=fixture();g[1]['records'][0]['derivation'][key]=value
            with self.assertRaises(ValueError):validate_material_catalog(*g)
        g=fixture();g[1]['records'][0]['derivation']['numerator_band']['uncertainty']='0.1'
        with self.assertRaises(ValueError):validate_material_catalog(*g)

    def test_full_consumers_and_four_languages_preserve_roles_unknowns(self):
        g=fixture();p=g[1]['records'][0];data=dict(zip(('materials','reference_properties','sources'),g));db=Database(data);rows=list(db.records(quantity=QUANTITY));self.assertEqual(resolve_material(p['material_state_id'],*g)['properties'][0],p)
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)/'normalized';db.export(out,quantity=QUANTITY);self.assertEqual(read_snapshot(out)[1][p['id']]['property'],p)
        rows[0]['property']['derivation']['notes']='mutated';self.assertEqual(list(db.records(quantity=QUANTITY))[0]['property'],p)
        for lang in ('en','zh','ja','de'):
            labels=material_labels(lang)
            with patch('materials_boundaries.catalog.read_catalog',side_effect=lambda name:deepcopy(data[name])):rendered=render_material_catalog(g[1],'reference-properties',lang)
            for key in LABEL_KEYS:
                if key=='code_'+METHOD:continue
                self.assertIn(labels[key],rendered)
            self.assertIn('1720 cm⁻¹',rendered);self.assertIn('1740 cm⁻¹',rendered);self.assertIn(labels['code_not_verified'],rendered)
            self.assertNotIn(PROFILE,rendered);self.assertNotIn('source_ordered_fitted_area_ratio',rendered)


if __name__=='__main__':unittest.main()
