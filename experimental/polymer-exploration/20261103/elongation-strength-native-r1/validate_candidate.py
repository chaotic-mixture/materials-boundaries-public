"""Run meaningful related regressions and complete source/consumer checks."""
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
from build_candidate import ROOT,read,write
sys.path.insert(0,str(ROOT/'tests'))
from materials_boundaries.database import Database,read_snapshot
from materials_boundaries.material_presentation import material_labels,render_material_catalog


def main():
    out=Path(sys.argv[1]).resolve()
    area=Path(__file__).resolve().parent
    patterns=['test_database*.py','test_material_reference_contract.py','test_material_presentation_fast_path.py','test_material_reference_expansion.py','test_material_uncertainty_contract.py','test_material_reported_measures_contract.py','test_material_scientific_notation_contract.py','test_specified_elongation_contract.py','test_flexural_strength_contract.py','test_tensile_break_stress_contract.py','test_break_elongation_contract.py','test_strength_elongation_contract.py']
    if '--reuse-tests' in sys.argv[2:]:
        failure=read(area/'FAILED_CONSUMER_VALIDATION_R1.json')
        from build_candidate import sha
        for name,digest in failure['test_inputs_sha256'].items():assert sha(ROOT/name)==digest,name
        assert sha(area/'TEST_RESULTS_R1.json')==failure['test_result_sha256']
        assert sha(area/'scoped-tests-r1.log')==failure['actual_test_log_sha256']
        tests=read(area/'TEST_RESULTS_R1.json')
        assert tests['successful'] and tests['tests_run']==135
        tested_count=tests['tests_run']
    else:
        suite=unittest.TestSuite()
        for pattern in patterns:suite.addTests(unittest.TestLoader().discover(str(ROOT/'tests'),pattern=pattern))
        log=io.StringIO()
        result=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
        (area/'scoped-tests-r1.log').write_text(log.getvalue(),encoding='utf-8')
        write(area/'TEST_RESULTS_R1.json',{'scope':patterns,'tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),'successful':result.wasSuccessful(),'full_history_regression':'not_run'})
        assert result.wasSuccessful() and result.testsRun==135
        tested_count=result.testsRun
    before=Database()
    data={name:read(out/'native-tables'/(name+'.json')) for name in before.data}
    after=Database(data)
    props=read(out/'native-candidate-r1.json')['reference_properties']['records']
    assert len(props)==12 and len(list(after.records(quantity='tensile_elongation_at_strength')))==12
    assert all(after.properties[k]==p for k,p in before.properties.items())
    assert all(p['reported_value']['unit_code']=='percent_elongation' and p['uncertainty']['unit_code']=='percent_elongation' for p in props)
    counts={}
    for source,expected in [('sahin_2026_polymer_mechanical_dielectric',(20,25)),('delgado_aguilar_2020_pla_pcl',(18,25))]:
        entry={}
        for phase,db in [('before',before),('after',after)]:
            dest=out/'source-exports'/source/phase
            if not dest.exists():db.export(dest,source=source)
            manifest,rows=read_snapshot(dest)
            assert rows=={r['property']['id']:r for r in db.records(source=source)}
            entry[phase]=len(rows)
        assert (entry['before'],entry['after'])==expected
        counts[source]=entry
    high_ids=['refprop_delgado2020_pla_pcl_'+slug+'_tensile_elongation_at_strength' for slug in ('b60_40','b40_60','b20_80')]
    assert all(pid in after.properties for pid in high_ids)
    absent_break_ids=[pid.replace('tensile_elongation_at_strength','tensile_elongation_at_break') for pid in high_ids]
    assert all(pid not in after.properties for pid in absent_break_ids)
    for lang in ('en','zh','ja','de'):
        with patch('materials_boundaries.catalog.read_catalog',side_effect=lambda n:data[n]):
            text=render_material_catalog({'schema_version':'1.0.0','records':props},'reference-properties',lang)
        assert material_labels(lang)['code_tensile_elongation_at_strength'] in text
        assert all(p['reported_value']['number'] in text and p['uncertainty']['number'] in text for p in props)
        assert 'percentage points' in text and 'unknown' in text
        (out/('render-'+lang+'.txt')).write_text(text,encoding='utf-8')
    for name in ('native-candidate-r1.json','VALIDATION_R1.json'):(area/name).write_bytes((out/name).read_bytes())
    write(area/'EXPORT_RENDER_VALIDATION_R1.json',{'baseline_snapshot':before.snapshot,'preview_snapshot':after.snapshot,'complete_joined_source_exports':counts,'equality':'all_fields_equal_query','all_old_5276_properties_unchanged':True,'high_PCL_strength_endpoint_created_break_not_created':high_ids,'source_percent_scale_no_rescaling':True,'absolute_percentage_points_not_relative_error':True,'four_languages':'passed','native_applied':False,'installed':'not_run','full_history_regression':'not_run'})
    print(json.dumps({'tests':tested_count,'source_exports':counts,'snapshot':after.snapshot}))


if __name__=='__main__':main()
