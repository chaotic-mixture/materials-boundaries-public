"""Fictional work records; no source integration or engineering assertions."""
from copy import deepcopy
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
from materials_boundaries.material_references import validate_material_catalog
from materials_boundaries.database import Database, read_snapshot
from materials_boundaries.material_presentation import material_labels, render_material_catalog
from test_tga_endpoint_contract import fixture as base_fixture, add_clone


def fixture():
    graph = base_fixture()
    prop = graph[1]['records'][0]
    prop.update(quantity='volumetric_tensile_work_to_break', quantity_dimension='energy_per_volume')
    prop['reported_value'].update(number='19.800', value_text='19.800', unit_code='J/cm^3', unit_text='J/cm³')
    prop['work_reference_basis'] = dict(status='not_reported_in_inspected_source', text=None, evidence=[], notes='Fictional volume basis unknown.')
    return graph


class VolumetricWorkTests(unittest.TestCase):
    def test_complete_query_export_and_four_languages(self):
        graph = fixture(); before = deepcopy(graph)
        validate_material_catalog(*graph)
        resources = dict(zip(('materials', 'reference_properties', 'sources'), graph))
        db = Database(resources)
        rows = list(db.records(quantity='volumetric_tensile_work_to_break'))
        self.assertEqual(rows[0]['property'], graph[1]['records'][0])
        with tempfile.TemporaryDirectory() as folder:
            db.export(Path(folder)/'work', quantity='volumetric_tensile_work_to_break')
            self.assertEqual(read_snapshot(Path(folder)/'work')[1], {r['record_id']:r for r in rows})
        rows[0]['property']['work_reference_basis']['notes']='changed copy'
        self.assertEqual(list(db.records(quantity='volumetric_tensile_work_to_break'))[0]['property'], before[1]['records'][0])
        for language in ('en','zh','ja','de'):
            with patch('materials_boundaries.catalog.read_catalog', side_effect=lambda name: deepcopy(resources[name])):
                text=render_material_catalog(graph[1], 'reference-properties', language)
            self.assertIn(material_labels(language)['work_reference_basis'],text)
            self.assertIn('19.800 J/cm³',text)
            self.assertIn('Fictional volume basis unknown.',text)
        self.assertEqual(graph,before)

    def test_zero_and_original_unit_scales(self):
        for code,text in [('J/cm^3','J/cm³'),('MJ/m^3','MJ/m³'),('J/m^3','J/m³')]:
            graph=fixture();graph[1]['records'][0]['reported_value'].update(number='0',value_text='0',unit_code=code,unit_text=text)
            validate_material_catalog(*graph)
        for change in [dict(number='-1',value_text='-1'),dict(unit_code='MPa',unit_text='MPa'),dict(unit_text='MJ/m³')]:
            graph=fixture();graph[1]['records'][0]['reported_value'].update(change)
            with self.assertRaises(ValueError):validate_material_catalog(*graph)

    def test_required_relevant_basis_and_primary_evidence(self):
        for change in ['missing','inapplicable','empty_note','wrong_evidence']:
            graph=fixture();p=graph[1]['records'][0]
            if change=='missing':del p['work_reference_basis']
            elif change=='inapplicable':p['work_reference_basis']['status']='not_applicable'
            elif change=='empty_note':p['work_reference_basis']['notes']=None
            else:p['work_reference_basis'].update(status='reported',text='Initial volume',evidence=deepcopy(p['evidence'][:1]))
            with self.assertRaises(ValueError):validate_material_catalog(*graph)
        graph=base_fixture();graph[1]['records'][0]['work_reference_basis']=fixture()[1]['records'][0]['work_reference_basis']
        with self.assertRaises(ValueError):validate_material_catalog(*graph)

    def test_unknown_basis_cannot_inflate_properties(self):
        graph=fixture();clone=add_clone(graph)
        clone['work_reference_basis'].update(status='not_verified',notes='Different unknown wording')
        with self.assertRaisesRegex(ValueError,'duplicate source fact'):validate_material_catalog(*graph)


if __name__=='__main__':unittest.main()
