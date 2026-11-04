"""Fictional DSC and DMA Tg coordinates retain distinct method context."""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from materials_boundaries.database import Database,read_snapshot
from materials_boundaries.material_references import validate_material_catalog
from materials_boundaries.material_presentation import render_material_catalog
from test_glass_transition_temperature_contract import fixture as tg_fixture


def methods_fixture():
    materials,properties,sources=tg_fixture('-40.00')
    dsc=properties['records'][0]
    dsc['source_property_label']='Fictional DSC inflection-point Tg'
    dsc['method_definition']['definition']='Fictional DSC inflection-point Tg,second heating;not equivalent to a DMA tanδ maximum.'
    dsc['conditions']['additional_conditions']=[]
    dma=deepcopy(dsc)
    dma['id']=dsc['id']+'_dma'
    dma['source_property_label']='Fictional DMA tanδ-maximum Tg'
    dma['method_definition']['definition']='Fictional DMA tanδ-maximum Tg;frequency1Hz,strain0.2%;scan cycle unknown.'
    dma['sample_count'].update(scope='Selected fictional scalar contributors unknown.',source_statement='Method triplication retained separately,not a mean or three independent specimens.')
    original_state=next(s for s in materials['records'] if s['id']==dsc['material_state_id'])
    state_fact=dict(status='reported',text='Fictional DSC pan specimen',evidence=[dict(source_id=dsc['source_id'],url=dsc['source_document']['url'],locator='Fictional physical specimen forms',supports=['state'])],notes='Physical specimen context,not merely an instrument label.')
    original_state['state']['product_form']=state_fact
    state=deepcopy(original_state)
    state['id']=state['id']+'_dma';state['property_ids']=[dma['id']]
    state['state']['product_form']['text']='Fictional DMA rectangular bending specimen'
    dma['material_state_id']=state['id']
    def fact(text,note):
        return dict(status='reported',text=text,evidence=[dict(source_id=dma['source_id'],url=dma['source_document']['url'],locator='Fictional DMA method declaration',supports=['condition'])],notes=note)
    dma['conditions']['additional_conditions']=[
        dict(name='measurement_method_family',fact=fact('DMA','Not DSC.')),
        dict(name='Tg_extraction_criterion',fact=fact('tanδ maximum','Not storage-modulus onset or loss-modulus maximum.')),
        dict(name='oscillation_frequency',fact=fact('1Hz','No frequency normalization or time-temperature shift.')),
        dict(name='strain_amplitude',fact=fact('0.2%','Amplitude convention unknown;not percent elongation at break.')),
        dict(name='common_method_triplicate_measurements',fact=fact('Three common-method repeats','Selected scalar contributors and independent specimen count unknown.'))
    ]
    materials['records'].append(state);properties['records'].append(dma)
    return materials,properties,sources


class GlassTransitionMethodContextTests(unittest.TestCase):
    def test_method_labels_alone_do_not_create_distinct_state_coverage(self):
        graph=methods_fixture()
        graph[0]['records'][-1]['state']=deepcopy(graph[0]['records'][0]['state'])
        with self.assertRaisesRegex(ValueError,'duplicate structural state'):
            validate_material_catalog(*graph)

    def test_same_coordinate_and_identity_preserve_two_method_states_and_exports(self):
        graph=methods_fixture();original=deepcopy(graph);validate_material_catalog(*graph)
        db=Database(dict(zip(('materials','reference_properties','sources'),graph)))
        rows=list(db.records(quantity='glass_transition_temperature'))
        self.assertEqual(len(rows),2)
        self.assertEqual(len({r['identity']['id'] for r in rows}),1)
        self.assertEqual(len({r['state']['id'] for r in rows}),2)
        self.assertEqual({r['property']['id']:r['property'] for r in rows},{p['id']:p for p in graph[1]['records']})
        self.assertEqual({r['property']['reported_value']['number'] for r in rows},{'-40.00'})
        for row in rows:
            self.assertIsNone(row['property']['sample_count']['value'])
            self.assertIsNone(row['property']['uncertainty'])
            self.assertEqual(row['property']['summary_statistic'],'not_stated')
        with tempfile.TemporaryDirectory() as directory:
            dest=Path(directory)/'method-qualified-tg';db.export(dest,quantity='glass_transition_temperature')
            self.assertEqual(read_snapshot(dest)[1],{r['record_id']:r for r in rows})
        self.assertEqual(graph,original)

    def test_four_language_rendering_preserves_method_criterion_and_unknown_count(self):
        graph=methods_fixture();data=dict(zip(('materials','reference_properties','sources'),graph))
        for language in ('en','zh','ja','de'):
            with patch('materials_boundaries.catalog.read_catalog',side_effect=lambda name:data[name]):
                text=render_material_catalog(graph[1],'reference-properties',language)
            for prop in graph[1]['records']:self.assertIn(prop['id'],text)
            for token in ['DSC inflection-point','DMA tanδ-maximum','1Hz','0.2%','Amplitude convention unknown','Three common-method repeats','Selected scalar contributors','-40.00']:
                self.assertIn(token,text)


if __name__=='__main__':unittest.main()
