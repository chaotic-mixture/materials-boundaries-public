"""Check source-complete exports and actual rendering of unspecified plus-minus."""
from pathlib import Path
import sys
from unittest.mock import patch
from build_candidate import read, write
from materials_boundaries.database import Database, read_snapshot
from materials_boundaries.material_presentation import render_material_catalog


def main():
    out = Path(sys.argv[1]).resolve()
    area = Path(__file__).resolve().parent
    before = Database()
    after = Database({n:read(out/'native-tables'/(n+'.json')) for n in before.data})
    props = read(out/'native-candidate-r1.json')['reference_properties']['records']
    assert len(props)==7
    assert all(p['summary_statistic']=='not_stated' and p['reporting_basis']=='not_stated' for p in props)
    assert all(p['uncertainty_status']=='reported_plus_minus_unspecified' and p['uncertainty']['type']=='reported_plus_minus_unspecified' for p in props)
    assert all(p['sample_count']['value'] is None and 'specified_elongation' not in p for p in props)
    assert all(after.properties[k]==v for k,v in before.properties.items())
    sid = 'delgado_aguilar_2020_pla_pcl'
    assert len(list(after.records(source=sid,quantity='tensile_strength')))==7
    assert len(list(after.records(source=sid,quantity='youngs_modulus')))==7
    assert not list(after.records(source=sid,quantity='tensile_stress_at_break'))
    counts = {}
    for phase,db in [('before',before),('after',after)]:
        dest = out/'source-exports'/phase
        db.export(dest,source=sid)
        manifest,rows = read_snapshot(dest)
        assert rows=={r['property']['id']:r for r in db.records(source=sid)}
        counts[phase] = len(rows)
    assert counts=={'before':7,'after':14}
    for lang in ('en','zh','ja','de'):
        with patch('materials_boundaries.catalog.read_catalog',side_effect=lambda n:after.data[n]):
            rendered = render_material_catalog({'schema_version':'1.0.0','records':props},'reference-properties',lang)
        assert all(p['reported_value']['number'] in rendered and p['uncertainty']['number'] in rendered for p in props)
        assert 'unknown' in rendered and 'not a verified mean/SD' in rendered
        (out/('render-'+lang+'.txt')).write_text(rendered,encoding='utf-8')
    for name in ('native-candidate-r1.json','VALIDATION_R1.json'):
        (area/name).write_bytes((out/name).read_bytes())
    write(area/'EXPORT_RENDER_VALIDATION_R1.json',{'baseline_snapshot':before.snapshot,'preview_snapshot':after.snapshot,'complete_joined_source_exports':counts,'equality':'all_fields_equal_query','seven_old_modulus_properties_unchanged':True,'seven_strengths_not_mean_not_SD':True,'n_unknown':True,'four_languages':'passed','native_applied':False,'installed':'not_run','tests':'No new run;existing runtime/schema reused','full_history_regression':'not_run'})
    print(counts)


if __name__ == '__main__':
    main()
