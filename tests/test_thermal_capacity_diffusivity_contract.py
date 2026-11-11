"""Fictional thermal records; no source statistics or transport calculation."""
from copy import deepcopy
import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch
from materials_boundaries.database import Database,read_snapshot
from materials_boundaries.material_presentation import material_labels,render_material_catalog
from test_material_uncertainty_contract import uncertainty_catalog
from test_tga_endpoint_contract import add_clone
from materials_boundaries.material_references import validate_material_catalog
from test_tga_endpoint_contract import fixture as base_fixture

def fixture(quantity='mass_specific_heat_capacity'):
    graph=base_fixture();p=graph[1]['records'][0]
    heat=quantity=='mass_specific_heat_capacity'
    p.update(quantity=quantity,quantity_dimension='energy_per_mass_temperature' if heat else 'area_per_time')
    p['reported_value'].update(number='1.700',value_text='1.700',unit_code='J/(g*K)' if heat else 'mm^2/s',unit_text='J/g·K' if heat else 'mm²/s')
    if heat:p['thermal_mass_reference_basis']=dict(status='not_reported_in_inspected_source',text=None,evidence=[],notes='Fictional mass basis unknown.')
    return graph

class ThermalCapacityDiffusivityTests(unittest.TestCase):
    def test_positive_units_and_no_implicit_scale_reinterpretation(self):
        for quantity in ['mass_specific_heat_capacity','thermal_diffusivity']:
            graph=fixture(quantity);original=deepcopy(graph);validate_material_catalog(*graph);self.assertEqual(graph,original)
            for change in [dict(number='0',value_text='0'),dict(number='-1',value_text='-1'),dict(unit_code='MPa',unit_text='MPa')]:
                bad=deepcopy(graph);bad[1]['records'][0]['reported_value'].update(change)
                with self.assertRaises(ValueError):validate_material_catalog(*bad)
        graph=fixture();graph[1]['records'][0]['reported_value']['unit_text']='J/(kg*K)'
        with self.assertRaises(ValueError):validate_material_catalog(*graph)

    def test_required_mass_basis_is_exclusive_and_relevant(self):
        for status in ['missing','not_applicable']:
            graph=fixture();p=graph[1]['records'][0]
            if status=='missing':del p['thermal_mass_reference_basis']
            else:p['thermal_mass_reference_basis']['status']=status
            with self.assertRaises(ValueError):validate_material_catalog(*graph)
        graph=fixture('thermal_diffusivity');graph[1]['records'][0]['thermal_mass_reference_basis']=fixture()[1]['records'][0]['thermal_mass_reference_basis']
        with self.assertRaises(ValueError):validate_material_catalog(*graph)

    def test_unknown_statistics_remain_unknown(self):
        for quantity in ['mass_specific_heat_capacity','thermal_diffusivity']:
            graph=fixture(quantity);validate_material_catalog(*graph);p=graph[1]['records'][0]
            self.assertEqual(p['summary_statistic'],'not_stated');self.assertIsNone(p['sample_count']['value']);self.assertIsNone(p['uncertainty'])

    def test_complete_export_render_and_detached_returns(self):
        for quantity in ['mass_specific_heat_capacity','thermal_diffusivity']:
            graph=fixture(quantity);resources=dict(zip(('materials','reference_properties','sources'),graph));db=Database(resources)
            rows=list(db.records(quantity=quantity));expected=deepcopy({r['record_id']:r for r in rows})
            with tempfile.TemporaryDirectory() as folder:
                db.export(Path(folder)/'thermal',quantity=quantity)
                self.assertEqual(read_snapshot(Path(folder)/'thermal')[1],expected)
            rows[0]['property']['reported_value']['number']='999'
            self.assertEqual({r['record_id']:r for r in db.records(quantity=quantity)},expected)
            for lang in ['en','zh','ja','de']:
                with patch('materials_boundaries.catalog.read_catalog',side_effect=lambda n:deepcopy(resources[n])):
                    text=render_material_catalog(graph[1],'reference-properties',lang)
                self.assertIn(material_labels(lang)['code_'+quantity],text);self.assertIn('1.700',text)
                if quantity=='mass_specific_heat_capacity':self.assertIn('Fictional mass basis unknown.',text)

    def test_unspecified_amplitudes_keep_exact_unit_scale(self):
        for quantity in ['mass_specific_heat_capacity','thermal_diffusivity']:
            graph=fixture(quantity);p=graph[1]['records'][0]
            p['uncertainty']=deepcopy(uncertainty_catalog('reported_plus_minus_unspecified')[1]['records'][0]['uncertainty'])
            p['uncertainty_status']='reported_plus_minus_unspecified'
            p['uncertainty'].update(unit_code=p['reported_value']['unit_code'],unit_text=p['reported_value']['unit_text'])
            validate_material_catalog(*graph)
            p['uncertainty'].update(unit_code='J/(kg*K)' if quantity=='mass_specific_heat_capacity' else 'm^2/s',unit_text='J/(kg*K)' if quantity=='mass_specific_heat_capacity' else 'm²/s')
            with self.assertRaises(ValueError):validate_material_catalog(*graph)

    def test_basis_evidence_and_unknown_wording_duplicate_rules(self):
        graph=fixture();clone=add_clone(graph);clone['thermal_mass_reference_basis'].update(status='not_verified',notes='Another unknown wording')
        with self.assertRaisesRegex(ValueError,'duplicate source fact'):validate_material_catalog(*graph)
        graph=fixture();p=graph[1]['records'][0];basis=p['thermal_mass_reference_basis']
        basis.update(status='reported',text='Fictional dry mass',evidence=deepcopy(p['evidence'][:1]))
        basis['evidence'][0]['supports']=['condition'];validate_material_catalog(*graph)
        url='https://example.org/other-thermal-document';graph[2]['records'][0]['urls'].append(url);basis['evidence'][0]['url']=url
        with self.assertRaises(ValueError):validate_material_catalog(*graph)

if __name__=='__main__':unittest.main()
