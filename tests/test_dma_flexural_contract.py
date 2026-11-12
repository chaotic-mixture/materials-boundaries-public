"""Fictional flexural DMA channels, explicit coordinates and source boundaries."""
from copy import deepcopy
from decimal import localcontext
import hashlib,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from jsonschema import Draft202012Validator
from materials_boundaries._dma_flexural_contract import QUANTITIES, FACT_FIELDS
from materials_boundaries.material_references import _PROPERTIES_SCHEMA, validate_material_catalog, resolve_material
from materials_boundaries.material_presentation import material_labels, render_material_catalog
from materials_boundaries.database import Database, read_snapshot
from test_gel_fraction_contract import as_gel_fraction, fixture as gel_fixture
from test_material_uncertainty_contract import uncertainty_catalog
from test_material_reported_measures_contract import synthetic_reported_measures_catalog
from test_tga_endpoint_contract import add_clone
ROOT=Path(__file__).resolve().parents[1]

def as_dma(graph, quantity='dma_flexural_storage_modulus'):
    graph=as_gel_fraction(graph);p=graph[1]['records'][0]
    p.pop('gel_fraction_definition');unit,dimension=QUANTITIES[quantity]
    p.update(quantity=quantity,quantity_dimension=dimension,source_property_label='Fictional Eprime/tan delta')
    p['reported_value'].update(number='12.50',value_text='12.50',unit_code=unit,unit_text='GPa' if dimension=='pressure' else '1')
    evidence=deepcopy(p['evidence'][:1])
    for e in evidence:e['supports']=['method','condition','classification']
    unknown=dict(status='not_verified',text=None,evidence=deepcopy(evidence),notes='Not established by this fictional source.')
    p['dma_definition']=dict(basis='source_reported_flexural_DMA',**{name:deepcopy(unknown) for name in FACT_FIELDS},evidence=deepcopy(evidence),notes='Fictional flexural DMA source,not static modulus or dielectric loss.')
    for field,number,code,text in [('dma_measurement_temperature','-50','degC','°C'),('dma_oscillation_frequency','1','Hz','Hz')]:
        p[field]=dict(status='reported',number=number,value_text=number,unit_code=code,unit_text=text,evidence=deepcopy(evidence),notes='Selected fictional source cell coordinate,not independent samples.')
    return graph

def fixture(quantity='dma_flexural_storage_modulus'):return as_dma(gel_fixture(),quantity)
def check(graph):Draft202012Validator(_PROPERTIES_SCHEMA).validate(graph[1]);validate_material_catalog(*graph)
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()

class DMAFlexuralContractTests(unittest.TestCase):
    def test_old25branches_definitions_and_schema_preserved(self):
        b=json.loads((ROOT/'tests/fixtures/dma_flexural_schema_baseline.json').read_bytes());stored=json.loads((ROOT/'schemas/reference_properties.schema.json').read_bytes())
        self.assertEqual(stored,_PROPERTIES_SCHEMA);Draft202012Validator.check_schema(stored)
        self.assertEqual(len(stored['$defs']['property']['oneOf']),31)
        self.assertEqual(digest(stored['$defs']['property']['oneOf'][:25]),b['old_branch_digest'])
        for k,h in b['old_definition_digests'].items():self.assertEqual(digest(stored['$defs'][k]),h,k)

    def test_both_channels_zero_and_unbounded_loss_tangent(self):
        for q in QUANTITIES:
            for number in ('0','0.000','12.50','125.000'):
                graph=fixture(q);graph[1]['records'][0]['reported_value'].update(number=number,value_text=number);before=deepcopy(graph);check(graph);self.assertEqual(before,graph)
            for number in ('-1','NaN','Infinity','1e3',True):
                graph=fixture(q);graph[1]['records'][0]['reported_value'].update(number=number,value_text=str(number))
                with self.assertRaises(ValueError):validate_material_catalog(*graph)

    def test_dedicated_units_and_unrelated_quantity_reject_reuse(self):
        for q in QUANTITIES:
            for code,text in [('GPa','GPa'),('percent','%'),('ratio_foam_cell_geometric_anisotropy','1')]:
                graph=fixture(q);graph[1]['records'][0]['reported_value'].update(unit_code=code,unit_text=text)
                with self.assertRaises(ValueError):validate_material_catalog(*graph)
        graph=fixture();graph[1]['records'][0]['quantity']='youngs_modulus'
        with self.assertRaises(ValueError):validate_material_catalog(*graph)

    def test_temperature_signed_floor_and_spelling(self):
        for number,code,text in [('-273.15','degC','°C'),('-0.001','degC','°C'),('0','K','K')]:
            graph=fixture();graph[1]['records'][0]['dma_measurement_temperature'].update(number=number,value_text=number,unit_code=code,unit_text=text);check(graph)
        for number,code,text in [('-273.150000000000000000000001','degC','°C'),('-0.001','K','K'),('-50','degC','K')]:
            graph=fixture();graph[1]['records'][0]['dma_measurement_temperature'].update(number=number,value_text=number,unit_code=code,unit_text=text)
            with localcontext() as ctx:
                ctx.prec=2
                with self.assertRaises(ValueError):validate_material_catalog(*graph)

    def test_frequency_positive_cyclic_and_precision(self):
        for number in ('0','-1','NaN',True):
            graph=fixture();graph[1]['records'][0]['dma_oscillation_frequency'].update(number=number,value_text=str(number))
            with self.assertRaises(ValueError):validate_material_catalog(*graph)
        for change in [dict(value_text='1.0'),dict(unit_code='rad/s'),dict(unit_text='s^-1')]:
            graph=fixture();graph[1]['records'][0]['dma_oscillation_frequency'].update(change)
            with self.assertRaises(ValueError):validate_material_catalog(*graph)

    def test_unknown_coordinates_closed_null_and_no_defaults(self):
        for field in ('dma_measurement_temperature','dma_oscillation_frequency'):
            graph=fixture();c=graph[1]['records'][0][field];c.update(status='not_verified',**{k:None for k in ('number','value_text','unit_code','unit_text')});check(graph)
            for change in (dict(number='0'),dict(status='not_applicable'),dict(notes=' ')):
                broken=deepcopy(graph);broken[1]['records'][0][field].update(change)
                with self.assertRaises(ValueError):validate_material_catalog(*broken)

    def test_coordinate_cell_and_primary_document_evidence(self):
        for field in ('dma_measurement_temperature','dma_oscillation_frequency'):
            for bad in ('missing','other_document','other_cell','missing_classification'):
                graph=fixture();c=graph[1]['records'][0][field]
                if bad=='missing':c['evidence']=[]
                elif bad=='other_document':c['evidence'][0]['url']='https://example.invalid/other.pdf'
                elif bad=='other_cell':c['evidence'][0]['locator']='Different source cell'
                else:c['evidence'][0]['supports']=['condition']
                with self.subTest(field=field,bad=bad),self.assertRaises(ValueError):validate_material_catalog(*graph)

    def test_eight_facts_reported_unknown_and_required_evidence(self):
        graph=fixture()
        for name in FACT_FIELDS:graph[1]['records'][0]['dma_definition'][name].update(status='reported',text='Fictional explicitly stated method fact.')
        check(graph)
        for name in FACT_FIELDS:
            for bad in ('missing','invented_unknown_text','empty_notes','wrong_role'):
                graph=fixture();d=graph[1]['records'][0]['dma_definition']
                if bad=='missing':del d[name]
                elif bad=='invented_unknown_text':d[name]['text']='assumed'
                elif bad=='empty_notes':d[name]['notes']=' '
                else:d[name].update(status='reported',text='Fictional fact.');d[name]['evidence'][0]['supports']=['condition']
                with self.subTest(name=name,bad=bad),self.assertRaises(ValueError):validate_material_catalog(*graph)

    def test_absolute_and_relative_uncertainty_roles(self):
        for q,(unit,dimension) in QUANTITIES.items():
            graph=as_dma(uncertainty_catalog(),q);p=graph[1]['records'][0];p['uncertainty'].update(number='150',value_text='150',unit_code=unit,unit_text='GPa' if dimension=='pressure' else '1');check(graph)
            graph=as_dma(synthetic_reported_measures_catalog('cv'),q);check(graph);a=graph[1]['records'][0]['uncertainty']['measures'][0]['reported_value'];self.assertEqual(a['unit_code'],'percent');a.update(unit_code=unit,unit_text='GPa' if dimension=='pressure' else '1')
            with self.assertRaises(ValueError):validate_material_catalog(*graph)

    def test_annotation_enrichment_does_not_duplicate_cell(self):
        for reverse in (False,True):
            graph=fixture();clone=add_clone(graph);clone['reported_value'].update(number='12.500',value_text='12.500');clone['dma_oscillation_frequency'].update(number='2',value_text='2');clone['conditions']['temperature']['text']='annotation revised'
            if reverse:graph[1]['records'].reverse()
            with localcontext() as ctx:
                ctx.prec=2
                with self.assertRaises(ValueError):validate_material_catalog(*graph)

    def test_distinct_real_cells_remain_distinct(self):
        graph=fixture();clone=add_clone(graph)
        for e in clone['evidence']:
            if 'reported_value' in e['supports']:e['locator']+=' separate actual protocol cell'
        for field in ('dma_measurement_temperature','dma_oscillation_frequency'):
            for e in clone[field]['evidence']:e['locator']+=' separate actual protocol cell'
        check(graph)

    def test_complete_consumers_and_four_languages(self):
        for q in QUANTITIES:
            graph=fixture(q);data=dict(zip(('materials','reference_properties','sources'),graph));db=Database(data);p=graph[1]['records'][0];rows=list(db.records(quantity=q));self.assertEqual(resolve_material(p['material_state_id'],*graph)['properties'][0],p)
            with tempfile.TemporaryDirectory() as d:
                out=Path(d)/'dma';db.export(out,quantity=q);self.assertEqual(read_snapshot(out)[1][p['id']]['property'],p)
            rows[0]['property']['dma_definition']['notes']='changed';self.assertEqual(list(db.records(quantity=q))[0]['property'],p)
            for language in ('en','zh','ja','de'):
                labels=material_labels(language)
                with patch('materials_boundaries.catalog.read_catalog',side_effect=lambda name:deepcopy(data[name])):rendered=render_material_catalog(graph[1],'reference-properties',language)
                for key in ('code_'+q,'dma_measurement_temperature','dma_oscillation_frequency','dma_reference_notice',*('dma_'+n for n in FACT_FIELDS)):self.assertIn(labels[key],rendered)
                self.assertIn('-50 °C',rendered);self.assertIn('1 Hz',rendered)

if __name__=='__main__':unittest.main()
