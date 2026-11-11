"""Fictional unnumbered DTG facts: preserve unknowns without new ranks or duplicate coverage."""
from copy import deepcopy
from decimal import localcontext
import hashlib,json
from pathlib import Path
import tempfile,unittest
from unittest.mock import patch
from jsonschema import Draft202012Validator
from materials_boundaries.database import Database,read_snapshot
from materials_boundaries.material_references import _PROPERTIES_SCHEMA,resolve_material,validate_material_catalog
from materials_boundaries.material_presentation import material_labels,render_material_catalog
from test_tga_endpoint_contract import fixture as tga_fixture,add_clone

def fixture(status='not_reported_in_inspected_source'):
    graph=tga_fixture('thermal_degradation_rate_peak_temperature')
    ordinal=graph[1]['records'][0]['degradation_peak_ordinal']
    ordinal.update(status=status,value=None,notes='Fictional source Tmax is unnumbered;do not assign an ordinal.')
    return graph

def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False).encode()).hexdigest()

class DtgUnknownOrdinalContractTests(unittest.TestCase):
    def test_public_schema_legacy_positive_shape_and_fifteen_branches_preserved(self):
        public=json.loads((Path(__file__).resolve().parents[1]/'schemas/reference_properties.schema.json').read_bytes())
        self.assertEqual(public,_PROPERTIES_SCHEMA);Draft202012Validator.check_schema(public)
        self.assertEqual(digest(public['$defs']['degradation_peak_ordinal']['oneOf'][0]),'966d61b868128690b5562b4cec3ae11c1ff72ff108cc7a411eeff545a79c92ce')
        self.assertEqual(digest(public['$defs']['property']['oneOf'][:15]),'7982b7f526400aa3e41079706550e733bbb3e8b63e6fa2de782587a877b20317')
        validate_material_catalog(*tga_fixture('thermal_degradation_rate_peak_temperature'))

    def test_two_explicit_unknown_states_are_valid_and_do_not_mutate(self):
        for status in ('not_reported_in_inspected_source','not_verified'):
            graph=fixture(status);before=deepcopy(graph);validate_material_catalog(*graph)
            self.assertEqual(graph,before);self.assertIsNone(graph[1]['records'][0]['degradation_peak_ordinal']['value'])

    def test_null_requires_explicit_valid_status_notes_and_closed_shape(self):
        cases=[('status',None),('status','reported'),('status','not_applicable'),('value',0),('value',-1),('value',False),('value',True),('value',1),('value','1'),('notes',' '),('notes',None),('unexpected','field')]
        for key,value in cases:
            with self.subTest(key=key,value=value):
                graph=fixture();graph[1]['records'][0]['degradation_peak_ordinal'][key]=value
                with self.assertRaises(ValueError):validate_material_catalog(*graph)
        graph=fixture();del graph[1]['records'][0]['degradation_peak_ordinal']['status']
        with self.assertRaises(ValueError):validate_material_catalog(*graph)

    def test_unknown_needs_inspected_primary_document_condition_evidence(self):
        for change in ('empty','wrong_role','other_document'):
            with self.subTest(change=change):
                graph=fixture();ordinal=graph[1]['records'][0]['degradation_peak_ordinal']
                if change=='empty':ordinal['evidence']=[]
                elif change=='wrong_role':ordinal['evidence'][0]['supports']=['reported_value']
                else:ordinal['evidence'][0]['url']='https://example.org/other-document'
                with self.assertRaises(ValueError):validate_material_catalog(*graph)

    def test_unknown_is_not_a_new_coordinate_through_status_notes_or_number_format(self):
        graph=fixture();clone=add_clone(graph);clone['degradation_peak_ordinal']['status']='not_verified'
        clone['degradation_peak_ordinal']['notes']='Different wording for the same unknown.'
        clone['degradation_peak_ordinal']['evidence'][0]['locator']+=' descriptor wording'
        clone['source_property_label']='Rephrased same Tmax'
        clone['reported_value'].update(number='149',value_text='149')
        with localcontext() as ctx:
            ctx.prec=2
            with self.assertRaisesRegex(ValueError,'duplicate source fact'):validate_material_catalog(*graph)

    def test_unknown_to_known_upgrade_cannot_coexist_in_either_order(self):
        for unknown_first in (True,False):
            for known_value in (1,2):
                with self.subTest(unknown_first=unknown_first,known_value=known_value):
                    graph=fixture();clone=add_clone(graph)
                    target=clone if unknown_first else graph[1]['records'][0]
                    target['degradation_peak_ordinal'].pop('status');target['degradation_peak_ordinal']['value']=known_value
                    target['reported_value'].update(number='149.000',value_text='149.000')
                    with self.assertRaisesRegex(ValueError,'duplicate source fact'):validate_material_catalog(*graph)

    def test_distinct_numbered_peaks_source_cells_and_protocols_remain_distinct(self):
        graph=tga_fixture('thermal_degradation_rate_peak_temperature');clone=add_clone(graph);clone['degradation_peak_ordinal']['value']=2
        validate_material_catalog(*graph)
        graph=fixture();clone=add_clone(graph)
        for ev in clone['evidence']:
            if 'reported_value' in ev['supports']:ev['locator']+=' distinct original source cell'
        validate_material_catalog(*graph)
        graph=fixture();clone=add_clone(graph)
        clone['conditions']['test_method']=dict(status='reported',text='Fictional separately reported protocol.',
            evidence=deepcopy(clone['degradation_peak_ordinal']['evidence']),notes='Fictional protocol distinction,not a note-only new fact.')
        validate_material_catalog(*graph)
        graph=fixture();p=graph[1]['records'][0];p['degradation_peak_ordinal'].pop('status');p['degradation_peak_ordinal']['value']=1
        validate_material_catalog(*graph)  # A single in-place curation update is not an added fact.

    def test_query_resolve_export_recovery_and_detached_copy_retain_null_status_evidence(self):
        for status in ('not_reported_in_inspected_source','not_verified'):
            graph=fixture(status);db=Database(dict(zip(('materials','reference_properties','sources'),graph)))
            rows=list(db.records(quantity='thermal_degradation_rate_peak_temperature'));expected=deepcopy({r['record_id']:r for r in rows})
            self.assertEqual(rows[0]['property']['degradation_peak_ordinal'],graph[1]['records'][0]['degradation_peak_ordinal'])
            resolved=resolve_material(graph[0]['records'][0]['id'],*graph)
            self.assertEqual(resolved['properties'][0]['degradation_peak_ordinal']['status'],status)
            with tempfile.TemporaryDirectory() as d:
                folder=Path(d)/'snapshot';db.export(folder,quantity='thermal_degradation_rate_peak_temperature');self.assertEqual(read_snapshot(folder)[1],expected)
            rows[0]['property']['degradation_peak_ordinal']['value']=1;rows[0]['property']['degradation_peak_ordinal']['notes']='detached mutation'
            self.assertEqual({r['record_id']:r for r in db.records(quantity='thermal_degradation_rate_peak_temperature')},expected)

    def test_four_languages_display_unknown_not_none_zero_or_inferred_one(self):
        for status in ('not_reported_in_inspected_source','not_verified'):
            graph=fixture(status);resources=dict(zip(('materials','reference_properties','sources'),graph))
            for language in ('en','zh','ja','de'):
                labels=material_labels(language)
                with patch('materials_boundaries.catalog.read_catalog',side_effect=lambda name:deepcopy(resources[name])):rendered=render_material_catalog(graph[1],'reference-properties',language)
                lines=[line for line in rendered.splitlines() if labels['degradation_peak_ordinal'] in line]
                self.assertTrue(any(labels['code_'+status] in line for line in lines))
                self.assertFalse(any(line.rstrip().endswith((': None',': 0',': 1')) for line in lines))
                self.assertIn(graph[1]['records'][0]['degradation_peak_ordinal']['notes'],rendered)

    def test_unknown_does_not_relax_quantity_unit_or_absolute_temperature_floor(self):
        graph=fixture();graph[1]['records'][0]['quantity']='thermal_degradation_onset_temperature'
        with self.assertRaises(ValueError):validate_material_catalog(*graph)
        for unit,text,number,valid in [('degC','°C','-273.15',True),('degC','°C','-273.16',False),('K','K','0',True),('K','K','-0.01',False),('MPa','MPa','149',False)]:
            with self.subTest(unit=unit,number=number):
                graph=fixture();graph[1]['records'][0]['reported_value'].update(unit_code=unit,unit_text=text,number=number,value_text=number)
                if valid:validate_material_catalog(*graph)
                else:
                    with self.assertRaises(ValueError):validate_material_catalog(*graph)

if __name__=='__main__':unittest.main()
