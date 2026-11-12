"""Current graph once and two focused fictional relative-uncertainty checks."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(ROOT),str(ROOT/'tests')]
from materials_boundaries.database import Database
from materials_boundaries.material_references import validate_material_catalog
from test_gel_fraction_contract import as_gel_fraction
from test_material_reported_measures_contract import synthetic_reported_measures_catalog
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    before=json.loads((HERE/'AFFECTED_INPUTS_R1.json').read_bytes())
    assert all(sha(ROOT/n)==h for n,h in before.items())
    graph=as_gel_fraction(synthetic_reported_measures_catalog('cv'))
    validate_material_catalog(*graph)
    measure=graph[1]['records'][0]['uncertainty']['measures'][0]
    assert measure['reported_value']['unit_code']=='percent'
    measure['reported_value'].update(unit_code='percent_solvent_extraction_gel_fraction',unit_text='%')
    try:validate_material_catalog(*graph)
    except ValueError:pass
    else:raise AssertionError('Relative CV accepted absolute gel-fraction unit role')
    db=Database();result=db.validate_scientific_contracts()
    assert len(db.properties)==5700 and len(db.states)==5407 and len(db.sources)==134
    assert all(sha(ROOT/n)==h for n,h in before.items())
    receipt=dict(current_graph=result,relative_cv_percent='accepted',absolute_role_on_cv='rejected',focused_fictional_cases=2,scope='Not extra unittest count;current graph once without history',all_141_regression_inputs_still_match=True,probe_source_sha256=sha(Path(__file__)))
    with (HERE/'CURRENT_GRAPH_AND_RELATIVE_R1.json').open('x',encoding='utf-8',newline='\n') as f:json.dump(receipt,f,indent=2);f.write('\n')
    print(json.dumps(receipt))
if __name__=='__main__':main()
