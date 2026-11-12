"""Fictional author-reported normalization;no numerical reconstruction."""
from copy import deepcopy
from decimal import localcontext
import hashlib,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from jsonschema import Draft202012Validator
from materials_boundaries._dsc_crystallinity_contract import QUANTITY,UNIT,METHOD,PROFILE,REFERENCE_UNIT,FACT_FIELDS
from materials_boundaries.material_references import _PROPERTIES_SCHEMA,validate_material_catalog,resolve_material
from materials_boundaries.material_presentation import material_labels,render_material_catalog
from materials_boundaries.database import Database,read_snapshot
from test_gel_fraction_contract import as_gel_fraction,fixture as gel_fixture
from test_material_uncertainty_contract import uncertainty_catalog
from test_material_reported_measures_contract import synthetic_reported_measures_catalog
from test_tga_endpoint_contract import add_clone
ROOT=Path(__file__).resolve().parents[1]

def as_crystallinity(graph):
    graph=as_gel_fraction(graph);p=graph[1]['records'][0];p.pop('gel_fraction_definition')
    p.update(quantity=QUANTITY,evidence_kind='published_measurement_derived_reference',determination_basis='source_reports_calculation',source_property_label='Fictional source Xc (%)')
    p['reported_value'].update(unit_code=UNIT,unit_text='%')
    ev=deepcopy(p['method_definition']['evidence'])
    for e in ev:e['supports']=['method','condition','classification']
    p['method_definition'].update(type=METHOD,evidence=deepcopy(ev))
    unknown=dict(status='not_verified',text=None,evidence=deepcopy(ev),notes='Actual source input or method detail unresolved.')
    d=dict(schema_version='1.0.0',profile_id=PROFILE,profile_version='1.0.0',executor='source_reported_only',formula_family='source_enthalpy_ratio',**{name:deepcopy(unknown) for name in FACT_FIELDS},evidence=deepcopy(ev),notes='Fictional author result only;do not evaluate source formula.')
    d['reported_formula'].update(status='reported',text='Source Xc=DeltaH/DeltaH0x100')
    d['reference_specific_enthalpy']=dict(status='reported',number='110.3',value_text='110.3',unit_code=REFERENCE_UNIT,unit_text='J/g',evidence=deepcopy(ev),notes='Source-cited reference,not certified constant or actual measured input.')
    d['cycle_assignment']=dict(status='not_verified',assignment_text=None,claims=[],evidence=deepcopy(ev),notes='Per-cell assignment unresolved;do not borrow another scan.')
    p['derivation']=d;return graph

def fixture():return as_crystallinity(gel_fixture())
def check(g):Draft202012Validator(_PROPERTIES_SCHEMA).validate(g[1]);validate_material_catalog(*g)
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
def conflict(g):
    p=g[1]['records'][0];cycle=p['derivation']['cycle_assignment'];cycle['status']='conflicting_source_statements';ev=deepcopy(cycle['evidence']);claims=[]
    for scope,phase,ordinal,loc in [('reported_crystallinity_origin','cooling',1,'Results first cooling'),('reported_enthalpy_scan','heating',2,'Methods second heating')]:
        ce=deepcopy(ev)
        for e in ce:e.update(locator=loc,supports=['condition','classification'])
        claims.append(dict(scope=scope,phase=phase,occurrence=ordinal,text=loc,evidence=ce,notes='Attributed source claim,not resolved actual input.'))
    cycle['claims']=claims;de=[]
    for c in claims:
        for e in c['evidence']:
            v=deepcopy(e);v['supports']=['source_discrepancy'];de.append(v)
    p['source_discrepancies']=[dict(description='Source cycle statements in tension',disposition='Retain both;no author-error diagnosis or chosen phase.',evidence=de)]
    return g

class DSCNormalizationContractTests(unittest.TestCase):
    def test_old27branches_and_all_definitions_preserved(self):
        baseline=json.loads((ROOT/'tests/fixtures/dsc_crystallinity_schema_baseline.json').read_bytes());s=json.loads((ROOT/'schemas/reference_properties.schema.json').read_bytes());self.assertEqual(s,_PROPERTIES_SCHEMA);Draft202012Validator.check_schema(s);self.assertEqual(len(s['$defs']['property']['oneOf']),31);self.assertEqual(digest(s['$defs']['property']['oneOf'][:27]),baseline['old_branch_digest'])
        for k,h in baseline['old_definition_digests'].items():self.assertEqual(digest(s['$defs'][k]),h,k)

    def test_source_only_result_not_recomputed_or_input_invented(self):
        g=fixture();p=g[1]['records'][0];p['reported_value'].update(number='99.50',value_text='99.50');before=deepcopy(g);check(g);self.assertEqual(g,before)
        p['derivation']['executor']='software_recomputed'
        with self.assertRaises(ValueError):validate_material_catalog(*g)

    def test_quantity_method_profile_and_classification_are_closed_both_ways(self):
        for field,value in [('quantity','tensile_elongation_at_break'),('evidence_kind','published_experimental_reference'),('determination_basis','source_reports_measurement')]:
            g=fixture();g[1]['records'][0][field]=value
            with self.assertRaises(ValueError):validate_material_catalog(*g)
        for target,field,value in [('method','type','source_reported_conventional'),('profile','profile_id','gwdd_airdry_sg_to_basic_density_v2_1'),('profile','profile_version','2.0.0')]:
            g=fixture();p=g[1]['records'][0];(p['method_definition'] if target=='method' else p['derivation'])[field]=value
            with self.assertRaises(ValueError):validate_material_catalog(*g)

    def test_central_percent_domain_and_wrong_unit_roles(self):
        for token in ['0','100.000','49.000']:
            g=fixture();g[1]['records'][0]['reported_value'].update(number=token,value_text=token);check(g)
        for token in ['-1','100.000000000000000000000001','NaN','1e2',True]:
            g=fixture();g[1]['records'][0]['reported_value'].update(number=token,value_text=str(token))
            with localcontext() as c:
                c.prec=2
                with self.assertRaises(ValueError):validate_material_catalog(*g)
        for unit in ['percent', 'percent_solvent_extraction_gel_fraction',REFERENCE_UNIT]:
            g=fixture();g[1]['records'][0]['reported_value']['unit_code']=unit
            with self.assertRaises(ValueError):validate_material_catalog(*g)

    def test_reference_is_separate_positive_model_input_or_strict_unknown(self):
        g=fixture();r=g[1]['records'][0]['derivation']['reference_specific_enthalpy'];r.update(status='not_verified',**{k:None for k in ('number','value_text','unit_code','unit_text')});check(g)
        for change in [dict(number='0',value_text='0'),dict(number='-1',value_text='-1'),dict(unit_code='J_per_g_dsc_melting_enthalpy'),dict(value_text='110.30')]:
            g=fixture();g[1]['records'][0]['derivation']['reference_specific_enthalpy'].update(change)
            with self.assertRaises(ValueError):validate_material_catalog(*g)

    def test_reference_and_derivation_primary_evidence(self):
        for target in ('derivation','reference_specific_enthalpy'):
            for bad in ('missing','other_document','missing_classification'):
                g=fixture();d=g[1]['records'][0]['derivation'];obj=d if target=='derivation' else d[target]
                if bad=='missing':obj['evidence']=[]
                elif bad=='other_document':obj['evidence'][0]['url']='https://example.invalid/other.pdf'
                else:obj['evidence'][0]['supports']=['method','condition']
                with self.assertRaises(ValueError):validate_material_catalog(*g)

    def test_all8facts_mandatory_and_formula_cannot_be_erased(self):
        for name in FACT_FIELDS:
            for bad in ('missing','invented_unknown_text','blank_notes','unreported_formula'):
                if bad=='unreported_formula' and name!='reported_formula':continue
                g=fixture();d=g[1]['records'][0]['derivation']
                if bad=='missing':del d[name]
                elif bad=='blank_notes':d[name]['notes']=' '
                elif bad=='unreported_formula':d[name].update(status='not_verified',text=None)
                else:d[name].update(status='not_verified',text='assumed input')
                with self.subTest(name=name,bad=bad),self.assertRaises(ValueError):validate_material_catalog(*g)

    def test_known_cycle_conflict_retains_claims_and_discrepancy(self):
        g=conflict(fixture());before=deepcopy(g);check(g);self.assertEqual(before,g)
        for status in ['not_reported_in_inspected_source','not_verified','reported_source_assignment']:
            bad=deepcopy(g);c=bad[1]['records'][0]['derivation']['cycle_assignment'];c['status']=status
            if status=='reported_source_assignment':c['assignment_text']='second heating chosen'
            with self.assertRaises(ValueError):validate_material_catalog(*bad)

    def test_conflict_cannot_duplicate_claim_alias_or_choose_actual_phase(self):
        for bad in ('duplicate','missing_claim','missing_discrepancy','unrelated_discrepancy','chosen_phase'):
            g=conflict(fixture());p=g[1]['records'][0];c=p['derivation']['cycle_assignment']
            if bad=='duplicate':c['claims'][1]=deepcopy(c['claims'][0]);c['claims'][1]['text']='reworded same claim'
            elif bad=='missing_claim':c['claims'].pop()
            elif bad=='missing_discrepancy':p['source_discrepancies']=[]
            elif bad=='unrelated_discrepancy':p['source_discrepancies'][0]['evidence'][0]['locator']='Elsewhere'
            else:c['assignment_text']='first cooling selected as actual input'
            with self.assertRaises(ValueError):validate_material_catalog(*g)

    def test_unknown_occurrence_is_not_a_conflicting_known_occurrence(self):
        g=conflict(fixture());c=g[1]['records'][0]['derivation']['cycle_assignment']
        c['claims'][1].update(phase='cooling',occurrence=None,text='Cooling occurrence unspecified in this claim')
        with self.assertRaises(ValueError):validate_material_catalog(*g)
        c['status']='not_verified';check(g)

    def test_common_program_heating_cooling_cannot_manufacture_conflict(self):
        g=conflict(fixture());c=g[1]['records'][0]['derivation']['cycle_assignment']
        for claim in c['claims']:claim['scope']='reported_common_program'
        with self.assertRaises(ValueError):validate_material_catalog(*g)
        c['status']='not_verified';check(g)

    def test_agreeing_origin_input_plus_other_program_phase_is_not_conflict(self):
        g=conflict(fixture());c=g[1]['records'][0]['derivation']['cycle_assignment']
        c['claims'][0].update(phase='heating',occurrence=2,text='Origin and input agree on second heating')
        common=deepcopy(c['claims'][0]);common.update(scope='reported_common_program',phase='cooling',occurrence=1,text='Common preceding cooling program')
        c['claims'].append(common)
        with self.assertRaises(ValueError):validate_material_catalog(*g)
        c['status']='not_verified';check(g)

    def test_absolute_and_relative_uncertainty_are_distinct(self):
        g=as_crystallinity(uncertainty_catalog());p=g[1]['records'][0];p['uncertainty'].update(unit_code=UNIT,unit_text='%',number='150',value_text='150');check(g)
        g=as_crystallinity(synthetic_reported_measures_catalog('cv'));check(g);a=g[1]['records'][0]['uncertainty']['measures'][0]['reported_value'];self.assertEqual(a['unit_code'],'percent');a.update(unit_code=UNIT,unit_text='%')
        with self.assertRaises(ValueError):validate_material_catalog(*g)

    def test_input_data_and_compute_flags_cannot_be_injected(self):
        for key,value in [('actual_f','0.9'),('measured_enthalpy','55'),('computed_result','49'),('recompute',True)]:
            g=fixture();g[1]['records'][0]['derivation'][key]=value
            with self.assertRaises(ValueError):validate_material_catalog(*g)

    def test_metadata_enrichment_and_trailing_zero_are_not_new_cells(self):
        for reverse in (False,True):
            g=fixture();clone=add_clone(g);clone['reported_value'].update(number='12.5000',value_text='12.5000');clone['derivation']['reference_specific_enthalpy'].update(number='146',value_text='146');clone['derivation']['source_data_attribution'].update(status='reported',text='Source attribution now clarified')
            if reverse:g[1]['records'].reverse()
            with localcontext() as c:
                c.prec=2
                with self.assertRaises(ValueError):validate_material_catalog(*g)

    def test_distinct_actual_model_cells_remain_distinct(self):
        g=fixture();clone=add_clone(g)
        for e in clone['evidence']:
            if 'reported_value' in e['supports']:e['locator']+=' actual separate model cell'
        check(g)

    def test_complete_derived_consumers_and_four_languages_preserve_claims(self):
        g=conflict(fixture());p=g[1]['records'][0];data=dict(zip(('materials','reference_properties','sources'),g));db=Database(data);rows=list(db.records(quantity=QUANTITY));self.assertEqual(resolve_material(p['material_state_id'],*g)['properties'][0],p)
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)/'normalized';db.export(out,quantity=QUANTITY);self.assertEqual(read_snapshot(out)[1][p['id']]['property'],p)
        rows[0]['property']['derivation']['notes']='mutated';self.assertEqual(list(db.records(quantity=QUANTITY))[0]['property'],p)
        for lang in ('en','zh','ja','de'):
            labels=material_labels(lang)
            with patch('materials_boundaries.catalog.read_catalog',side_effect=lambda name:deepcopy(data[name])):rendered=render_material_catalog(g[1],'reference-properties',lang)
            for key in ['code_'+QUANTITY,'dsc_crystallinity_notice','code_conflicting_source_statements','dsc_crystallinity_reference',*('dsc_crystallinity_'+n for n in FACT_FIELDS)]:self.assertIn(labels[key],rendered)
            self.assertIn('Results first cooling',rendered);self.assertIn('Methods second heating',rendered);self.assertIn('110.3 J/g',rendered)

if __name__=='__main__':unittest.main()
