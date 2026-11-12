"""Fictional SEC moments, inherited origins and source-only dispersity."""
from copy import deepcopy
from decimal import localcontext
import hashlib,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from jsonschema import Draft202012Validator
from materials_boundaries._sec_molar_mass_contract import MOMENTS,DISPERSITY,QUANTITIES,MOMENT_UNITS,RATIO_UNIT,MOMENT_METHOD,RATIO_METHOD,PROFILE,FACT_FIELDS,VERIFICATIONS,LABEL_KEYS
from materials_boundaries.material_references import _PROPERTIES_SCHEMA,validate_material_catalog,material_coverage,resolve_material
from materials_boundaries.material_presentation import material_labels,render_material_catalog
from materials_boundaries.database import Database,read_snapshot
from test_gel_fraction_contract import as_gel_fraction,fixture as gel_fixture
from test_material_uncertainty_contract import uncertainty_catalog
from test_material_reported_measures_contract import synthetic_reported_measures_catalog
from test_tga_endpoint_contract import add_clone
ROOT=Path(__file__).resolve().parents[1]


def as_sec(graph,quantity=MOMENTS[0]):
    graph=as_gel_fraction(graph);p=graph[1]['records'][0];p.pop('gel_fraction_definition');ratio=quantity==DISPERSITY
    p.update(quantity=quantity,quantity_dimension='dimensionless' if ratio else 'mass_per_amount',
             evidence_kind='published_measurement_derived_reference' if ratio else 'published_experimental_reference',
             determination_basis='source_reports_calculation' if ratio else 'source_reports_measurement',source_property_label='Fictional source SEC result')
    p['reported_value'].update(number='1.08' if ratio else '6.96',value_text='1.08' if ratio else '6.96',unit_code=RATIO_UNIT if ratio else MOMENT_UNITS[2],unit_text='ratio' if ratio else '×10^5 g/mol')
    ev=deepcopy(p['method_definition']['evidence'])
    for e in ev:e['supports']=['method','condition','classification','reported_value']
    unknown=dict(status='not_verified',text=None,evidence=deepcopy(ev),notes='Original per-cell method not verified;not an assumption.')
    p['conditions']={n:([] if n=='additional_conditions' else deepcopy(unknown)) for n in p['conditions']}
    state=graph[0]['records'][0]
    for n in ('processing','temper_or_heat_treatment','conditioning','porosity','orientation'):state['state'][n]=deepcopy(unknown)
    p['method_definition'].update(type=RATIO_METHOD if ratio else MOMENT_METHOD,evidence=deepcopy(ev))
    p['sample_count']=dict(value=None,relation='not_reported',scope='Fictional SEC result;distribution moment notreplicates',source_statement='Exactn unknown',evidence=[])
    cell=dict(table_id='fictional-table-2',row_key='fictional-polymer',column_key=quantity,evidence=deepcopy(ev),notes='Original inspected result cell;changes revise this address.')
    original=dict(status='not_verified',**{n:None for n in ('original_source_id','document_url','sha256','table_id','row_key','column_key')},evidence=deepcopy(ev),notes='Cited original not independently inspected.')
    origin=dict(status='explicitly_reproduced_from_cited_work',original_reference=dict(doi='10.1234/fictional-original',title='Fictional cited original SEC work',year=2020,evidence=deepcopy(ev),notes='Known attribution,not a new reproducing experiment.'),original_result=original,verification={n:deepcopy(unknown) for n in VERIFICATIONS},evidence=deepcopy(ev),notes='Fictional inherited result,not an independently new experiment.')
    definition=dict(source_result_cell=cell,origin=origin,reported_common_context={n:deepcopy(unknown) for n in FACT_FIELDS},actual_original_result_context={n:deepcopy(unknown) for n in FACT_FIELDS},measurement_basis=dict(status='not_verified',text=None,evidence=deepcopy(ev),notes='MALS and calibrant do not establish absolute/relative reduction.'),evidence=deepcopy(ev),notes='Preserve source scales and provenance;no chromatogram evaluation.')
    definition['reported_common_context']['eluent_flow_and_temperature'].update(status='reported',text='Reproducing paper common SEC method30°C;actual original equivalence unknown.')
    p['sec_definition']=definition
    if ratio:
        formula=deepcopy(unknown);formula.update(status='reported',text='Source defines PDI=Mw/Mn;actual pairing/averaging order unknown.')
        p['derivation']=dict(schema_version='1.0.0',profile_id=PROFILE,profile_version='1.0.0',executor='source_reported_only',formula_family='source_weight_over_number_average_molar_mass',numerator_role=MOMENTS[0],denominator_role=MOMENTS[1],reported_formula=formula,evidence=deepcopy(ev),notes='Source ratio result;do not divide printedmeans or infer rawmoments.')
    return graph


def fixture(quantity=MOMENTS[0]):return as_sec(gel_fixture(),quantity)
def check(g):Draft202012Validator(_PROPERTIES_SCHEMA).validate(g[1]);validate_material_catalog(*g)
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()


def direct(g):
    p=g[1]['records'][0];o=p['sec_definition']['origin'];ev=deepcopy(o['evidence']);s=g[2]['records'][0];s['doi']=o['original_reference']['doi'];s['year']=2020
    p['source_document'].update(sha256='0'*64,hash_status='recorded',hash_note=None)
    o.update(status='direct_primary_report',original_result=dict(status='verified',original_source_id=p['source_id'],document_url=p['source_document']['url'],sha256='0'*64,**{n:p['sec_definition']['source_result_cell'][n] for n in ('table_id','row_key','column_key')},evidence=deepcopy(ev),notes='Fictional original source address,not physical certification.'))
    o['verification']['protocol_equivalence'].update(status='reported',text='Fictional original source method inspected.',evidence=deepcopy(ev))
    return g


def secondary_clone(g):
    clone=add_clone(g);d=clone['sec_definition'];old=clone['source_id'];oldurl=clone['source_document']['url'];new='synthetic_secondary_reference';url='https://example.invalid/secondary-sec.pdf'
    # Preserve independently inspected original references while rebinding the
    # reproducing document's own evidence and common method context.
    original=deepcopy(d['origin']['original_result']);verification=deepcopy(d['origin']['verification']);actual=deepcopy(d['actual_original_result_context'])
    def rebind(node):
        if isinstance(node,dict):
            if node.get('source_id')==old and node.get('url')==oldurl:node.update(source_id=new,url=url)
            for v in node.values():rebind(v)
        elif isinstance(node,list):
            for v in node:rebind(v)
    rebind(clone);clone['source_id']=new;clone['source_document'].update(url=url,sha256='1'*64,hash_status='recorded',hash_note=None)
    if original['status']=='verified':
        d['origin']['original_result']=original
        for n,item in verification.items():
            if item['status']=='reported':d['origin']['verification'][n]=item
        for n,item in actual.items():
            if item['status']=='reported':d['actual_original_result_context'][n]=item
    d['origin']['status']='explicitly_reproduced_from_cited_work'
    source=deepcopy(g[2]['records'][0]);source.update(id=new,doi='10.1234/fictional-secondary',urls=[url]);g[2]['records'].append(source)
    return clone


class SECMolarMassContractTests(unittest.TestCase):
    def test_old29branches_and_all_definitions_preserved(self):
        b=json.loads((ROOT/'tests/fixtures/sec_molar_mass_schema_baseline.json').read_bytes());s=json.loads((ROOT/'schemas/reference_properties.schema.json').read_bytes());self.assertEqual(s,_PROPERTIES_SCHEMA);Draft202012Validator.check_schema(s);self.assertEqual(len(s['$defs']['property']['oneOf']),31);self.assertEqual(digest(s['$defs']['property']['oneOf'][:29]),b['old_branch_digest'])
        for k,h in b['old_definition_digests'].items():self.assertEqual(digest(s['$defs'][k]),h,k)

    def test_moment_and_derived_roles_are_closed_both_ways(self):
        for quantity in QUANTITIES:
            check(fixture(quantity))
            for field,value in [('quantity','mass_density'),('quantity_dimension','mass_per_volume'),('determination_basis','source_reports_compiled_measurements'),('evidence_kind','published_handbook_reference')]:
                g=fixture(quantity);g[1]['records'][0][field]=value
                with self.subTest(quantity=quantity,field=field),self.assertRaises(ValueError):validate_material_catalog(*g)
        for quantity,method in [(MOMENTS[0],RATIO_METHOD),(DISPERSITY,MOMENT_METHOD)]:
            g=fixture(quantity);g[1]['records'][0]['method_definition']['type']=method
            with self.assertRaises(ValueError):validate_material_catalog(*g)

    def test_molar_mass_scale_and_amplitude_preserved(self):
        for unit,text in zip(MOMENT_UNITS,('g/mol','kg/mol','×10^5 g/mol')):
            g=as_sec(uncertainty_catalog());p=g[1]['records'][0];p['reported_value'].update(unit_code=unit,unit_text=text);p['uncertainty'].update(unit_code=unit,unit_text=text,number='150',value_text='150');before=deepcopy(g);check(g);self.assertEqual(g,before)
        for unit,text in [('g_per_mol_sec_molar_mass','g/mol'),(RATIO_UNIT,'ratio')]:
            g=as_sec(uncertainty_catalog());g[1]['records'][0]['uncertainty'].update(unit_code=unit,unit_text=text)
            with self.assertRaises(ValueError):validate_material_catalog(*g)
        g=fixture();g[1]['records'][0]['reported_value']['unit_text']='g/mol'
        with self.assertRaises(ValueError):validate_material_catalog(*g)

    def test_central_domain_not_uncertainty_interval(self):
        for quantity,tokens in [(MOMENTS[0],['0.0001','999999.0']),(DISPERSITY,['1','1.0800','999999.0'])]:
            for token in tokens:
                g=fixture(quantity);g[1]['records'][0]['reported_value'].update(number=token,value_text=token)
                with localcontext() as c:c.prec=2;check(g)
        for quantity,tokens in [(MOMENTS[1],['0','-1','NaN','1e5']),(DISPERSITY,['0','0.999999999999999999999999','-1','Infinity'])]:
            for token in tokens:
                g=fixture(quantity);g[1]['records'][0]['reported_value'].update(number=token,value_text=token)
                with self.assertRaises(ValueError):validate_material_catalog(*g)
        g=as_sec(uncertainty_catalog(),DISPERSITY);g[1]['records'][0]['uncertainty'].update(unit_code=RATIO_UNIT,unit_text='ratio',number='150',value_text='150');check(g)

    def test_source_dispersity_not_ratio_of_printed_means(self):
        g=fixture(DISPERSITY);g[1]['records'][0]['reported_value'].update(number='15.50',value_text='15.50');before=deepcopy(g);check(g);self.assertEqual(g,before)
        for change in [dict(executor='software_recomputed'),dict(numerator_role=MOMENTS[1]),dict(denominator_role=MOMENTS[0]),dict(profile_id='source_ftir_fitted_carbonyl_band_area_ratio_v1'),dict(actual_Mw='6.96')]:
            g=fixture(DISPERSITY);g[1]['records'][0]['derivation'].update(change)
            with self.assertRaises(ValueError):validate_material_catalog(*g)
        g=fixture(DISPERSITY);g[1]['records'][0]['derivation']['reported_formula'].update(status='not_verified',text=None)
        with self.assertRaises(ValueError):validate_material_catalog(*g)

    def test_unknown_shapes_and_all_twenty_method_facts(self):
        for group in ('reported_common_context','actual_original_result_context'):
            for name in FACT_FIELDS:
                g=fixture();del g[1]['records'][0]['sec_definition'][group][name]
                with self.assertRaises(ValueError):validate_material_catalog(*g)
                g=fixture();g[1]['records'][0]['sec_definition'][group][name].update(status='not_verified',text='assumed')
                with self.assertRaises(ValueError):validate_material_catalog(*g)
        for name in VERIFICATIONS:
            g=fixture();g[1]['records'][0]['sec_definition']['origin']['verification'][name]['notes']=' '
            with self.assertRaises(ValueError):validate_material_catalog(*g)

    def test_common_method_cannot_populate_original_conditions_or_specimen(self):
        for key in FACT_FIELDS:
            g=fixture();g[1]['records'][0]['sec_definition']['actual_original_result_context'][key].update(status='reported',text='Transferred common2022method')
            with self.assertRaises(ValueError):validate_material_catalog(*g)
        for key in ('temperature','test_method','conditioning'):
            g=fixture();g[1]['records'][0]['conditions'][key].update(status='reported',text='Transferred30°Corcommonmethod')
            with self.assertRaises(ValueError):validate_material_catalog(*g)
        for key in ('processing','conditioning','orientation'):
            g=fixture();g[0]['records'][0]['state'][key].update(status='reported',text='Transferredcommonhistory')
            with self.assertRaises(ValueError):validate_material_catalog(*g)

    def test_absolute_or_relative_basis_cannot_be_inferred(self):
        for status in ('source_reported_relative_calibration','source_reported_absolute_reduction'):
            g=fixture();g[1]['records'][0]['sec_definition']['measurement_basis'].update(status=status,text='MALS/PSthereforeknown')
            with self.assertRaises(ValueError):validate_material_catalog(*g)
        g=direct(fixture());basis=g[1]['records'][0]['sec_definition']['measurement_basis'];basis.update(status='source_reported_absolute_reduction',text='Fictional original explicitly reports reduction basis.');check(g)

    def test_known_inheritance_cannot_be_erased_or_declared_new(self):
        for status in ('original_attribution_unresolved','direct_primary_report'):
            g=fixture();g[1]['records'][0]['sec_definition']['origin']['status']=status
            with self.assertRaises(ValueError):validate_material_catalog(*g)
        g=fixture();g[1]['records'][0]['sec_definition']['origin']['original_reference']=None
        with self.assertRaises(ValueError):validate_material_catalog(*g)
        g=fixture();o=g[1]['records'][0]['sec_definition']['origin'];o.update(status='original_attribution_unresolved',original_reference=None);check(g)

    def test_original_verification_requires_registered_matching_original(self):
        for name in VERIFICATIONS:
            g=fixture();g[1]['records'][0]['sec_definition']['origin']['verification'][name].update(status='reported',text='Originalverifiedwithoutinspection')
            with self.assertRaises(ValueError):validate_material_catalog(*g)
        for change in [dict(original_source_id='missing_original'),dict(document_url='https://example.invalid/missing.pdf'),dict(sha256='1'*64)]:
            g=direct(fixture());g[1]['records'][0]['sec_definition']['origin']['original_result'].update(change)
            with self.assertRaises(ValueError):validate_material_catalog(*g)
        g=direct(fixture());g[2]['records'][0]['doi']='10.1234/other-original'
        with self.assertRaises(ValueError):validate_material_catalog(*g)

    def test_primary_evidence_cannot_point_elsewhere(self):
        for target in ('definition','cell','origin','reference','common'):
            g=fixture();d=g[1]['records'][0]['sec_definition'];item={'definition':d,'cell':d['source_result_cell'],'origin':d['origin'],'reference':d['origin']['original_reference'],'common':d['reported_common_context']['eluent_flow_and_temperature']}[target];item['evidence'][0]['url']='https://example.invalid/other.pdf'
            with self.assertRaises(ValueError):validate_material_catalog(*g)

    def test_original_license_claim_requires_registered_rights_verification(self):
        g=direct(fixture());p=g[1]['records'][0];o=p['sec_definition']['origin'];o['verification']['reuse_license'].update(status='reported',text='Fictional original explicitly grants CC BY4.0.')
        with self.assertRaises(ValueError):validate_material_catalog(*g)
        g[2]['records'][0]['license'].update(status='explicit_reuse_license_verified',identifier='CC-BY-4.0');check(g)

    def test_original_result_unknown_must_not_carry_verified_fields(self):
        for name,value in [('original_source_id','invented_original'),('sha256','0'*64),('row_key','guessedrow')]:
            g=fixture();g[1]['records'][0]['sec_definition']['origin']['original_result'][name]=value
            with self.assertRaises(ValueError):validate_material_catalog(*g)

    def test_same_cell_revisions_not_parallel_facts_both_orders(self):
        for change in ('unit','value','condition_notes','definition','locator'):
            for reverse in (False,True):
                g=fixture();clone=add_clone(g)
                if change=='unit':clone['reported_value'].update(unit_code=MOMENT_UNITS[0],unit_text='g/mol',number='696000',value_text='696000')
                elif change=='value':clone['reported_value'].update(number='7.000',value_text='7.000')
                elif change=='condition_notes':clone['conditions']['temperature']['notes']='Nowclarifiedunknown'
                elif change=='definition':clone['sec_definition']['reported_common_context']['dn_dc_and_concentration_reduction']['notes']='Moreknowncontext'
                else:
                    for e in clone['evidence']:
                        if 'reported_value' in e['supports']:e['locator']='Rewordedsameoriginalcell'
                if reverse:g[1]['records'].reverse()
                with self.assertRaises(ValueError):validate_material_catalog(*g)

    def test_unknown_original_second_publication_is_held_both_orders(self):
        for reverse in (False,True):
            g=fixture();secondary_clone(g)
            if reverse:g[1]['records'].reverse()
            with self.assertRaises(ValueError):validate_material_catalog(*g)
            with self.assertRaises(ValueError):material_coverage(g[0],g[1])

    def test_confirmed_same_original_datum_rejected_across_publications(self):
        for reverse in (False,True):
            g=direct(fixture());secondary_clone(g)
            if reverse:g[1]['records'].reverse()
            with self.assertRaises(ValueError):validate_material_catalog(*g)

    def test_distinct_confirmed_original_cells_and_moments_not_merged(self):
        g=direct(fixture());clone=secondary_clone(g);clone['sec_definition']['origin']['original_result']['column_key']='Distinctoriginalprotocolcolumn';clone['sec_definition']['source_result_cell']['column_key']='Distinctoriginalprotocolcolumn';check(g)
        g=fixture();clone=add_clone(g);clone['quantity']=MOMENTS[1];clone['sec_definition']['source_result_cell']['column_key']=MOMENTS[1];check(g)
        g=fixture();clone=add_clone(g);clone['sec_definition']['source_result_cell']['column_key']='Actual other protocol column'
        for e in clone['evidence']:
            if 'reported_value' in e['supports']:e['locator']='Actual other protocol column'
        check(g)

    def test_source_mean_sd_and_relative_cv_roles_remain_separate(self):
        g=as_sec(uncertainty_catalog('reported_standard_deviation'));p=g[1]['records'][0];p.update(summary_statistic='reported_mean',basis_note='Fictional source explicitly reports mean andSD.',uncertainty_note='Fictional source SD with explicitmean.');p['uncertainty'].update(unit_code=MOMENT_UNITS[2],unit_text='×10^5 g/mol');check(g);p['summary_statistic']='reported_value'
        with self.assertRaises(ValueError):validate_material_catalog(*g)
        g=as_sec(synthetic_reported_measures_catalog('cv'));check(g);m=g[1]['records'][0]['uncertainty']['measures'][0]['reported_value'];self.assertEqual(m['unit_code'],'percent');m.update(unit_code=MOMENT_UNITS[2],unit_text='×10^5 g/mol')
        with self.assertRaises(ValueError):validate_material_catalog(*g)

    def test_full_consumers_four_languages_keep_inheritance_scale_and_unknowns(self):
        for quantity in QUANTITIES:
            g=fixture(quantity);p=g[1]['records'][0];data=dict(zip(('materials','reference_properties','sources'),g));db=Database(data);rows=list(db.records(quantity=quantity));self.assertEqual(resolve_material(p['material_state_id'],*g)['properties'][0],p)
            with tempfile.TemporaryDirectory() as d:
                out=Path(d)/'normalized';db.export(out,quantity=quantity);self.assertEqual(read_snapshot(out)[1][p['id']]['property'],p)
            rows[0]['property']['sec_definition']['origin']['notes']='mutated';self.assertEqual(list(db.records(quantity=quantity))[0]['property'],p)
            for lang in ('en','zh','ja','de'):
                labels=material_labels(lang)
                with patch('materials_boundaries.catalog.read_catalog',side_effect=lambda name:deepcopy(data[name])):rendered=render_material_catalog(g[1],'reference-properties',lang)
                for key in ['code_'+quantity,'sec_notice','sec_origin','sec_reported_common_context','sec_actual_original_context','code_explicitly_reproduced_from_cited_work',*('sec_'+n for n in VERIFICATIONS)]:self.assertIn(labels[key],rendered)
                self.assertIn('10.1234/fictional-original',rendered);self.assertIn(labels['code_not_verified'],rendered);self.assertNotIn(PROFILE,rendered)
                if quantity in MOMENTS:self.assertIn('×10^5 g/mol',rendered)

    def test_original_doi_and_url_reject_controls_surrogates_and_final_newlines(self):
        for suffix in ('\x00','\x1b[2J','\x7f','\x80','\x9f','\n','\r\n','\ud800','\udfff'):
            for position in ('middle','end'):
                g=fixture();doi='10.1234/fictional'+suffix+('suffix' if position=='middle' else '')
                g[1]['records'][0]['sec_definition']['origin']['original_reference']['doi']=doi
                with self.subTest(field='doi',suffix=repr(suffix),position=position):
                    self.assertFalse(Draft202012Validator(_PROPERTIES_SCHEMA).is_valid(g[1]))
                    with self.assertRaises(ValueError):validate_material_catalog(*g)
                g=direct(fixture());url='https://example.invalid/original'+suffix+('suffix' if position=='middle' else '')
                g[1]['records'][0]['sec_definition']['origin']['original_result']['document_url']=url
                with self.subTest(field='url',suffix=repr(suffix),position=position):
                    self.assertFalse(Draft202012Validator(_PROPERTIES_SCHEMA).is_valid(g[1]))
                    with self.assertRaises(ValueError):validate_material_catalog(*g)

    def test_safe_original_reference_and_https_preserve_source_strings(self):
        for doi in ('10.1234/Case.Suffix(2)-v1','10.12345/original_2020.1'):
            for url in ('https://example.invalid/original.pdf','https://example.invalid/path/original?version=2#table-2'):
                g=direct(fixture());p=g[1]['records'][0];oldurl=p['source_document']['url']
                def replace(node):
                    if isinstance(node,dict):
                        for key,value in node.items():
                            if value==oldurl:node[key]=url
                            else:replace(value)
                    elif isinstance(node,list):
                        for index,value in enumerate(node):
                            if value==oldurl:node[index]=url
                            else:replace(value)
                replace(g);p['sec_definition']['origin']['original_reference']['doi']=doi;g[2]['records'][0]['doi']=doi
                before=deepcopy(g);check(g);self.assertEqual(before,g)


if __name__=='__main__':unittest.main()
