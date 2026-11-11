"""Fictional nonisothermal peaks: source phase and occurrence are not specimen counts."""
from copy import deepcopy
from decimal import localcontext
import hashlib,json
from pathlib import Path
import tempfile,unittest
from unittest.mock import patch
from jsonschema import Draft202012Validator
from materials_boundaries.database import Database,read_snapshot
from materials_boundaries.material_references import _PROPERTIES_SCHEMA,validate_material_catalog,resolve_material
from materials_boundaries.material_presentation import material_labels,render_material_catalog
from test_glass_transition_temperature_contract import fixture as temperature_fixture
from test_tga_endpoint_contract import add_clone

def fixture(phase='cooling',ordinal=None):
    graph=temperature_fixture('149.00');p=graph[1]['records'][0]
    p.update(quantity='crystallization_peak_temperature',source_property_label='Fictional Tcc retained label')
    ev=deepcopy(p['method_definition']['evidence'])
    for e in ev:e['supports']=['method','condition']
    condition=deepcopy(ev)
    for e in condition:e['supports']=['condition']
    p['method_definition']['definition']='Fictional nonisothermal source crystallization peak;extraction unknown.'
    p['conditions']['test_method']=dict(status='reported',text='Fictional nonisothermal program.',evidence=deepcopy(condition),notes='Not a real measurement.')
    p['thermal_scan_definition']=dict(kind='nonisothermal_temperature_scan',evidence=ev,notes='Fictional explicit temperature-scan evidence,not isothermal hold.')
    p['thermal_scan_phase']=dict(status='reported' if phase else 'not_reported_in_inspected_source',code=phase,evidence=deepcopy(condition),notes='Fictional source phase or explicit unknown within a known scan.')
    p['thermal_phase_occurrence_ordinal']=dict(status='reported' if ordinal else 'not_reported_in_inspected_source',value=ordinal,evidence=deepcopy(condition),notes='Same-phase occurrence,not overall step,cycle count or n.')
    discrepancy=deepcopy(condition)
    for e in discrepancy:e['supports']=['source_discrepancy']
    p['source_discrepancies']=[dict(description='Fictional Tcc label differs from source phase wording.',disposition='Keep label and phase separately;no repair or certified mechanism.',evidence=discrepancy)]
    return graph

class CrystallizationPhaseContractTests(unittest.TestCase):
    def test_closed_sixteenth_branch_preserves_original_fifteen_objects(self):
        stored=json.loads((Path(__file__).resolve().parents[1]/'schemas/reference_properties.schema.json').read_bytes())
        self.assertEqual(stored,_PROPERTIES_SCHEMA);Draft202012Validator.check_schema(stored)
        self.assertEqual(len(stored['$defs']['property']['oneOf']),16)
        digest=lambda x:hashlib.sha256(json.dumps(x,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
        self.assertEqual(digest(stored['$defs']['property']['oneOf'][:15]),'7982b7f526400aa3e41079706550e733bbb3e8b63e6fa2de782587a877b20317')
        self.assertEqual(stored['$defs']['property']['oneOf'][-1]['properties']['quantity'],{'const':'crystallization_peak_temperature'})

    def test_known_and_explicit_unknown_phase_occurrence_preserve_input(self):
        for phase,ordinal in [('heating',1),('cooling',2),('cooling',None),(None,None),(None,1)]:
            graph=fixture(phase,ordinal);before=deepcopy(graph);validate_material_catalog(*graph);self.assertEqual(graph,before)
        graph=fixture(None,None)
        for name in ('thermal_scan_phase','thermal_phase_occurrence_ordinal'):graph[1]['records'][0][name]['status']='not_verified'
        validate_material_catalog(*graph)

    def test_unknown_phase_cannot_hide_isothermal_or_absent_scan_proof(self):
        for change in ('isothermal','unknown_program','missing','no_evidence','method_only','condition_only'):
            with self.subTest(change=change):
                graph=fixture(None,None);p=graph[1]['records'][0];program=p['thermal_scan_definition']
                if change=='isothermal':program['kind']='isothermal_hold'
                elif change=='unknown_program':program.update(kind=None,status='not_reported_in_inspected_source')
                elif change=='missing':del p['thermal_scan_definition']
                elif change=='no_evidence':program['evidence']=[]
                else:
                    for e in program['evidence']:e['supports']=['method' if change=='method_only' else 'condition']
                with self.assertRaises(ValueError):validate_material_catalog(*graph)

    def test_all_three_descriptors_need_inspected_primary_document_roles(self):
        for name in ('thermal_scan_definition','thermal_scan_phase','thermal_phase_occurrence_ordinal'):
            graph=fixture();p=graph[1]['records'][0];url='https://example.org/other-primary-document'
            source=next(s for s in graph[2]['records'] if s['id']==p['source_id']);source['urls'].append(url)
            for e in p[name]['evidence']:e['url']=url
            with self.assertRaisesRegex(ValueError,'primary inspected-document'):validate_material_catalog(*graph)

    def test_invalid_phase_ordinal_status_and_unrelated_quantity_roles_rejected(self):
        cases=[('thermal_scan_phase','code','isothermal'),('thermal_scan_phase','status','not_applicable'),('thermal_scan_phase','code',None),('thermal_phase_occurrence_ordinal','value',0),('thermal_phase_occurrence_ordinal','value',-1),('thermal_phase_occurrence_ordinal','value',True),('thermal_phase_occurrence_ordinal','value','1'),('thermal_phase_occurrence_ordinal','value',1),('thermal_phase_occurrence_ordinal','notes',' ')]
        for name,key,value in cases:
            with self.subTest(name=name,key=key,value=value):
                graph=fixture();graph[1]['records'][0][name][key]=value
                with self.assertRaises(ValueError):validate_material_catalog(*graph)
        for quantity in ('melting_peak_temperature','glass_transition_temperature','thermal_degradation_rate_peak_temperature'):
            graph=fixture();graph[1]['records'][0]['quantity']=quantity
            with self.assertRaises(ValueError):validate_material_catalog(*graph)

    def test_all_partial_coordinate_pairs_follow_explicit_overlap_table(self):
        nodes={'U':(None,None),'H':('heating',None),'C':('cooling',None),'O1':(None,1),'O2':(None,2),'H1':('heating',1),'H2':('heating',2),'C1':('cooling',1),'C2':('cooling',2)}
        allowed={'U':set(),'H':{'C','C1','C2'},'C':{'H','H1','H2'},'O1':{'O2','H2','C2'},'O2':{'O1','H1','C1'},'H1':{'C','O2','H2','C1','C2'},'H2':{'C','O1','H1','C1','C2'},'C1':{'H','O2','H1','H2','C2'},'C2':{'H','O1','H1','H2','C1'}}
        for left,a in nodes.items():
            for right,b in nodes.items():
                with self.subTest(left=left,right=right):
                    graph=fixture(*a);clone=add_clone(graph);other=fixture(*b)[1]['records'][0]
                    for name in ('thermal_scan_phase','thermal_phase_occurrence_ordinal'):clone[name]=deepcopy(other[name])
                    if right in allowed[left]:validate_material_catalog(*graph)
                    else:
                        with self.assertRaisesRegex(ValueError,'duplicate source fact'):validate_material_catalog(*graph)

    def test_notes_status_label_and_numeric_precision_do_not_create_coverage(self):
        graph=fixture(None,None);clone=add_clone(graph)
        for name in ('thermal_scan_phase','thermal_phase_occurrence_ordinal'):
            clone[name]['status']='not_verified';clone[name]['notes']+=' Different note.';clone[name]['evidence'][0]['locator']+=' descriptor spelling'
        clone['source_property_label']='Another spelling';clone['reported_value'].update(number='149',value_text='149')
        with localcontext() as c:
            c.prec=2
            with self.assertRaisesRegex(ValueError,'duplicate source fact'):validate_material_catalog(*graph)
        for different in ('cell','protocol'):
            graph=fixture();clone=add_clone(graph)
            if different=='cell':
                for e in clone['evidence']:
                    if 'reported_value' in e['supports']:e['locator']+=' distinct original source cell'
            else:clone['conditions']['test_method']['text']+=' Distinct reported protocol.'
            validate_material_catalog(*graph)

    def test_absolute_temperature_floors_and_units_remain_strict(self):
        for unit,text,number,valid in [('degC','°C','-273.15',True),('degC','°C','-273.16',False),('K','K','0',True),('K','K','-0.01',False),('MPa','MPa','149',False)]:
            graph=fixture();graph[1]['records'][0]['reported_value'].update(unit_code=unit,unit_text=text,number=number,value_text=number)
            if valid:validate_material_catalog(*graph)
            else:
                with self.assertRaises(ValueError):validate_material_catalog(*graph)

    def test_complete_query_resolve_export_and_copy_keep_source_label_and_unknowns(self):
        graph=fixture('cooling',None);db=Database(dict(zip(('materials','reference_properties','sources'),graph)))
        rows=list(db.records(quantity='crystallization_peak_temperature'));expected=deepcopy({r['record_id']:r for r in rows})
        resolved=resolve_material(graph[0]['records'][0]['id'],*graph);p=resolved['properties'][0]
        self.assertEqual(p['source_property_label'],'Fictional Tcc retained label');self.assertIsNone(p['thermal_phase_occurrence_ordinal']['value']);self.assertTrue(p['source_discrepancies'])
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)/'export';db.export(out,quantity='crystallization_peak_temperature');self.assertEqual(read_snapshot(out)[1],expected)
        rows[0]['property']['thermal_phase_occurrence_ordinal']['value']=2
        self.assertEqual({r['record_id']:r for r in db.records(quantity='crystallization_peak_temperature')},expected)

    def test_four_languages_keep_program_phase_unknown_occurrence_and_discrepancy(self):
        graph=fixture('cooling',None);resources=dict(zip(('materials','reference_properties','sources'),graph))
        for language in ('en','zh','ja','de'):
            labels=material_labels(language)
            with patch('materials_boundaries.catalog.read_catalog',side_effect=lambda name:deepcopy(resources[name])):text=render_material_catalog(graph[1],'reference-properties',language)
            for key in ('code_crystallization_peak_temperature','code_nonisothermal_temperature_scan','code_cooling','thermal_phase_occurrence_ordinal','code_not_reported_in_inspected_source'):self.assertIn(labels[key],text)
            self.assertIn('Fictional Tcc retained label',text);self.assertIn('Keep label and phase separately',text)
            self.assertFalse(any(l.rstrip().endswith((': None',': 0',': 1',': 2')) for l in text.splitlines() if labels['thermal_phase_occurrence_ordinal'] in l))

if __name__=='__main__':unittest.main()
