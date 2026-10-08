"""Synthetic contract tests, not scientific observations or coverage."""
from copy import deepcopy
import unittest
from unittest.mock import patch
from materials_boundaries._material_derivation import BASIS, PROFILE, TISSUE, FORMULA_ID, FORMULA_EXPRESSION, ROUNDING_AUDIT_POLICY, INPUT_BASIS
from materials_boundaries.material_references import validate_material_catalog, resolve_materials, material_quota_coverage
from test_material_reference_contract import synthetic_material_catalog


def synthetic_derived_catalog():
    m,p,s=synthetic_material_catalog()
    identity=m['identities'][0]; prop=p['records'][0]
    identity['category']='natural'
    taxon_id='wfo-0000000001'
    identity['canonical_taxon']={
        'identity_key':'wfo:'+taxon_id+':'+TISSUE, 'tissue_scope':TISSUE,
        'accepted_taxon_id':taxon_id,'accepted_name':'Ficticia alba','accepted_authority':'Test.',
        'accepted_full_name':'Ficticia alba Test.','original_full_name':'Ficticia alba Test.',
        'original_name_records':[{'taxon_id':taxon_id,'scientific_name':'Ficticia alba','authorship':'Test.', 'rank':'species','status':'Accepted'}],
        'source_to_accepted_chains':[{'source_name_wfo_id':taxon_id,'wfo_chain_ids':[taxon_id],'accepted_terminal_wfo_id':taxon_id,'error':None}],
        'mapping_method':'synthetic test-only exact match','mapping_disposition':'reviewed_supported_historical_backbone',
        'rank':'species','hybrid':False,'source_taxonomic_reference':'https://example.invalid/test-taxon',
        'backbone':{'doi':'synthetic-only','version':'test','archive_sha256':'a'*64,'archive_member':'synthetic.csv','accepted_record_1based':1,'accepted_physical_line_start':2,'accepted_physical_line_end':2},
    }
    s['records'][0]['role']='published source-applied empirical conversion (synthetic)'
    prop.update(quantity='basic_wood_density',density_basis=BASIS,
                evidence_kind='published_measurement_derived_reference',determination_basis='source_reports_calculation',
                reporting_basis='not_stated',summary_statistic='reported_value')
    prop['reported_value'].update(number='0.38',value_text='0.38')
    prop['method_definition']['type']='source_reported_empirical_conversion'
    prop['method_definition']['evidence'][0]['supports'].append('classification')
    locator={'source_id':'synthetic_reference','release_doi':'synthetic-only','release_version':'test',
             'file_id':'test','file_name':'test.csv','sha256':'b'*64,'url':s['records'][0]['urls'][0],
             'record_id':'test','data_record_1based':1,'physical_line_start':2,'physical_line_end':2,'fields':['value']}
    prop['derivation']={
        'schema_version':'1.0.0','kind':'conversion_derived_estimate_from_measured_input','profile_id':PROFILE,'profile_version':'1.0.0','formula_id':FORMULA_ID,
        'input':{'quantity':'air_dry_specific_gravity','basis':INPUT_BASIS,'number':'0.46','value_text':'0.46','unit_code':'dimensionless','source_property_label':'Specific gravity','deposited_quantity_label':'Airdry SG/Density','evidence_type':'source_reported_measured_input'},
        'deposited_output':{'number':'0.38','unit_code':'g/cm^3','rounding_increment':'0.01'},
        'si_output':{'number':'380','unit_code':'kg/m^3','rounding_increment':'10'},
        'formula':{'expression':FORMULA_EXPRESSION,'coefficient':'0.8281316','coefficient_source_id':'synthetic_reference','coefficient_source_field':'coefficient','calibration_source_id':'synthetic_reference','basis_convention_source_id':'synthetic_reference','water_density_convention_g_cm3':'1','nominal_conversion_moisture_percent':'12','measured_specimen_moisture_percent':None,'calibration_context':'Synthetic test, not field evidence','rounding_audit_policy':ROUNDING_AUDIT_POLICY,'moisture_percent_basis':'water_mass_over_oven_dry_mass'},
        'specimen_scope':{'accession':'SYNTHETIC 1','selection':'selected_collection_accession','tissue_subtype':None,'sample_anatomical_location':None,'orientation':None,'exact_test_temperature':None,'exact_moisture':None,'treatment':None,'collection_date':None,'measurement_date':None,'missingness_reason':'Not established in synthetic test fixture'},
        'counts':{'plants_sampled_as_reported':'1','verified_independent_plants':None,'collection_accessions_selected':1,'v1_mechanically_eligible_source_record_count':2,'count_scope_note':'Mechanical count, not independent n'},
        'uncertainty':{'record_measurement_uncertainty':None,'source_method_uncertainty_note':'Not a per-record interval','conversion_uncertainty':None,'conversion_uncertainty_note':'Not reported','species_variation':None,'rounding_is_uncertainty':False},
        'provenance':{'original':deepcopy(locator),'deposited':deepcopy(locator),'reviewed_batch_sha256':'c'*64,'reviewed_candidate_key':'wood-'+taxon_id,'original_citation':'Synthetic test','normalized_citation':'Synthetic test','license_identifiers':['synthetic'],'attribution':'Synthetic fixture only','source_scope_note':'Not actual source data'},
        'evidence':deepcopy(prop['evidence']),
    }
    s['records'][0]['doi']='synthetic-only'
    s['records'][0]['license']['identifier']='synthetic'
    prop['source_document'].update(sha256='b'*64,hash_status='recorded',hash_note=None)
    prop['derivation']['evidence'][0]['supports'].append('method')
    return m,p,s


class DerivedPropertyContractTests(unittest.TestCase):
    def test_closed_profile_accepts_basis_preserving_deposited_value(self):
        graph=synthetic_derived_catalog();validate_material_catalog(*graph)
        self.assertEqual(material_quota_coverage(*graph)['classes']['natural']['admitted_unique_identity_count'],1)

    def test_relabels_missingness_and_false_counts_rejected(self):
        changes=[
            lambda m,p,s:p['records'][0].update(quantity='mass_density'),
            lambda m,p,s:p['records'][0]['derivation']['formula'].update(calibration_source_id='dangling'),
            lambda m,p,s:p['records'][0]['derivation']['formula'].update(basis_convention_source_id='dangling'),
            lambda m,p,s:p['records'][0]['derivation']['formula'].update(expression='incorrect displayed formula'),
            lambda m,p,s:p['records'][0]['derivation']['provenance']['original'].update(release_doi='wrong-doi'),
            lambda m,p,s:p['records'][0].update(density_basis='bulk'),
            lambda m,p,s:p['records'][0].update(evidence_kind='published_experimental_reference'),
            lambda m,p,s:p['records'][0]['method_definition'].update(type='source_reported_crystallographic_derivation'),
            lambda m,p,s:p['records'][0].pop('derivation'),
            lambda m,p,s:p['records'][0]['derivation']['input'].update(unit_code='g/cm^3'),
            lambda m,p,s:p['records'][0]['derivation']['input'].update(number='NaN'),
            lambda m,p,s:p['records'][0]['derivation']['formula'].update(coefficient='0.828'),
            lambda m,p,s:p['records'][0]['derivation']['formula'].update(measured_specimen_moisture_percent='12'),
            lambda m,p,s:p['records'][0]['derivation']['specimen_scope'].update(sample_anatomical_location='trunk'),
            lambda m,p,s:p['records'][0]['derivation']['counts'].update(verified_independent_plants=1),
            lambda m,p,s:p['records'][0]['sample_count'].update(value=2,relation='exact'),
            lambda m,p,s:p['records'][0]['derivation']['si_output'].update(number='380.940536'),
            lambda m,p,s:p['records'][0]['derivation']['provenance']['original'].pop('sha256'),
            lambda m,p,s:p['records'][0].update(summary_statistic='reported_mean'),
            lambda m,p,s:m['identities'][0]['canonical_taxon'].update(original_full_name='Ficticia x alba Test.'),
            lambda m,p,s:m['identities'][0]['canonical_taxon']['source_to_accepted_chains'][0].update(accepted_terminal_wfo_id='wfo-0000000002'),
            lambda m,p,s:m['identities'][0]['canonical_taxon']['original_name_records'][0].update(authorship='Other.'),
        ]
        for index,change in enumerate(changes):
            with self.subTest(case=index):
                graph=synthetic_derived_catalog();change(*graph)
                with self.assertRaises(ValueError):validate_material_catalog(*graph)

    def test_wood_basis_cannot_be_smuggled_into_conventional_density(self):
        m,p,s=synthetic_material_catalog();p['records'][0]['density_basis']=BASIS
        with self.assertRaises(ValueError):validate_material_catalog(m,p,s)

    def test_duplicate_canonical_identity_fails_despite_alias_and_new_scope(self):
        m,p,s=synthetic_derived_catalog(); clone=deepcopy(m['identities'][0]);clone['id']='mat_other';clone['identity_scope']='Different presentation'
        m['identities'].append(clone)
        with self.assertRaisesRegex(ValueError,'canonical'):validate_material_catalog(m,p,s)

    def test_original_name_normalization_matches_reviewed_period_whitespace_only(self):
        m,p,s=synthetic_derived_catalog()
        taxon=m['identities'][0]['canonical_taxon']
        taxon['original_full_name']='Ficticia alba T. Est.'
        taxon['original_name_records'][0]['authorship']='T.Est.'
        validate_material_catalog(m,p,s)
        taxon['original_full_name']='ficticia alba T. Est.'
        with self.assertRaises(ValueError):validate_material_catalog(m,p,s)

    def test_original_http_taxonomic_reference_is_preserved(self):
        m,p,s=synthetic_derived_catalog()
        taxon=m['identities'][0]['canonical_taxon']
        taxon['source_taxonomic_reference']='http://example.invalid/original-source-reference'
        validate_material_catalog(m,p,s)
        self.assertTrue(taxon['source_taxonomic_reference'].startswith('http://'))
        taxon['source_taxonomic_reference']='javascript:alert(1)'
        with self.assertRaises(ValueError):validate_material_catalog(m,p,s)

    def test_retained_baseline_excludes_canonical_reimport(self):
        from materials_boundaries.catalog import read_catalog
        baseline_m=read_catalog('materials');baseline_p=read_catalog('reference_properties');baseline_s=read_catalog('sources')
        m,p,s=synthetic_derived_catalog();taxon=m['identities'][0]['canonical_taxon']
        old=taxon['accepted_taxon_id'];new='wfo-0000515026'
        import json
        m=json.loads(json.dumps(m).replace(old,new));p=json.loads(json.dumps(p).replace(old,new))
        for field in ('identities','grades','records'):baseline_m[field].extend(m[field])
        baseline_p['records'].extend(p['records']);baseline_s['records'].extend(s['records'])
        with self.assertRaisesRegex(ValueError,'baseline identity'):validate_material_catalog(baseline_m,baseline_p,baseline_s)

    def test_resolution_validates_once_and_rechecks_mutation_on_next_call(self):
        graph=synthetic_derived_catalog();m,p,s=graph
        with patch('materials_boundaries.material_references.validate_material_catalog',wraps=validate_material_catalog) as mocked:
            resolved=resolve_materials([m['records'][0]['id']]*10,*graph)
            self.assertEqual(mocked.call_count,1)
        p['records'][0]['derivation']['si_output']['number']='381'
        self.assertEqual(resolved[0]['properties'][0]['derivation']['si_output']['number'],'380')
        with self.assertRaises(ValueError):resolve_materials([m['records'][0]['id']],*graph)

if __name__=='__main__':unittest.main()
