"""Bounded fictional checks of an isolated provenance schema;not material data."""
from pathlib import Path
from copy import deepcopy
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE),str(ROOT),str(ROOT/'tests')]
from jsonschema import Draft202012Validator,ValidationError
from transport_profile import PROFILE,METHOD,KIND,EXPRESSION,ROLES,UNKNOWNS,definition,validate
from materials_boundaries import material_references as m
from test_thermal_conductivity_contract import fixture
def main():
    tracked=['materials_boundaries/_material_derivation.py','materials_boundaries/material_references.py','materials_boundaries/material_presentation.py','materials_boundaries/data/material_locales.json','schemas/reference_properties.schema.json']+['materials_boundaries/data/'+n+'.json' for n in ('materials','reference_properties','sources')]
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();before={n:sha(ROOT/n) for n in tracked}
    schema=definition(m.TEXT,m.HTTPS,m.NULL,m._object,m._array,m._enum)
    schema['$defs']=deepcopy(m._PROPERTIES_SCHEMA['$defs'])
    Draft202012Validator.check_schema(schema);validator=Draft202012Validator(schema)
    p=fixture('W/(m*K)','0.1230')[1]['records'][0]
    def ev(tag):return dict(source_id=p['source_id'],url=p['source_document']['url'],locator='Fictional selected source cell or method',supports=[tag])
    p.update(evidence_kind='published_measurement_derived_reference',determination_basis='source_reports_calculation')
    p['method_definition']['type']=METHOD
    p['derivation']=dict(schema_version='1.0.0',profile_id=PROFILE,profile_version='1.0.0',kind=KIND,
        formula=dict(expression=EXPRESSION,evidence=[ev('method')]),
        contextual_inputs={q:dict(quantity=q,role='source_context_not_verified_actual_input',source_property_label='Fictional '+q,evidence=[ev('reported_value')]) for q in ROLES},
        input_provenance={**{n:None for n in UNKNOWNS},'unknown_scope_note':'Actual paired inputs,order,covariance and propagation unknown.'},
        software_calculation_performed=False,software_uncertainty_propagation_performed=False)
    def check(prop):validator.validate(prop['derivation']);validate(prop)
    original=deepcopy(p);check(p);assert p==original
    rejected=[]
    mutations={
      'missing_profile':lambda p:p.pop('derivation'),
      'direct_measurement_relabel':lambda p:p.update(evidence_kind='published_experimental_reference',determination_basis='source_reports_measurement'),
      'wrong_method':lambda p:p['method_definition'].update(type='source_reported_conventional'),
      'wrong_quantity':lambda p:p.update(quantity='mass_density'),
      'foreign_density_basis':lambda p:p.update(density_basis='apparent'),
      'wrong_unit_role':lambda p:p['reported_value'].update(unit_code='MPa'),
      'missing_context':lambda p:p['derivation']['contextual_inputs'].pop('mass_density'),
      'swapped_role':lambda p:p['derivation']['contextual_inputs']['mass_density'].update(quantity='thermal_diffusivity'),
      'actual_numeric_input':lambda p:p['derivation']['contextual_inputs']['mass_density'].update(number='0.9'),
      'asserted_pairing':lambda p:p['derivation']['input_provenance'].update(actual_specimen_pairing=True),
      'software_product':lambda p:p['derivation'].update(software_calculation_performed=True),
      'software_error_propagation':lambda p:p['derivation'].update(software_uncertainty_propagation_performed=True),
      'missing_unknown_note':lambda p:p['derivation']['input_provenance'].update(unknown_scope_note=''),
      'wrong_formula':lambda p:p['derivation']['formula'].update(expression='lambda = alpha * cp'),
      'foreign_formula_source':lambda p:p['derivation']['formula']['evidence'][0].update(source_id='other'),
      'foreign_context_document':lambda p:p['derivation']['contextual_inputs']['mass_density']['evidence'][0].update(url='https://example.org/other'),
      'wrong_context_support':lambda p:p['derivation']['contextual_inputs']['mass_density']['evidence'][0].update(supports=['method'])}
    for name,mutation in mutations.items():
        bad=deepcopy(p);mutation(bad)
        try:check(bad)
        except (ValueError,ValidationError,KeyError):rejected.append(name)
        else:raise AssertionError(name)
    assert before=={n:sha(ROOT/n) for n in tracked}
    for name,obj in [('ISOLATED_DERIVATION_SCHEMA_R1.json',schema),('FICTIONAL_PROFILE_R1.json',p),('PROTOTYPE_CHECKS_R1.json',dict(valid_profile_passed=True,mutation_rejections=rejected,production_and_native_unchanged=before,scope='Isolated fictional schema+profile semantics only;not production integration,full graph,mapping,installation or admission'))]:
        with (HERE/name).open('x',encoding='utf-8',newline='\n') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps(dict(positive_profile=1,rejected_mutations=len(rejected),production_native_unchanged=True)))
if __name__=='__main__':main()
