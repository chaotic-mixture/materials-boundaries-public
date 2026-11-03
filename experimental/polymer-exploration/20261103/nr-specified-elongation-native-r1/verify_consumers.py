"""Verify complete NR exports and typed-target rendering on frozen preview."""
from pathlib import Path
import sys
from unittest.mock import patch
from build_candidate import ROOT, read, write
from materials_boundaries.database import Database, read_snapshot
from materials_boundaries.material_presentation import render_material_catalog


def main():
    out = Path(sys.argv[1]).resolve()
    area = Path(__file__).resolve().parent
    before = Database()
    after = Database({n: read(out/'native-tables'/(n+'.json')) for n in before.data})
    candidate = read(out/'native-candidate-r1.json')
    props = candidate['reference_properties']['records']
    assert [p['specified_elongation']['number'] for p in props] == ['200','400']
    assert len(list(after.records(quantity='tensile_stress_at_specified_elongation'))) == len(list(before.records(quantity='tensile_stress_at_specified_elongation'))) + 2
    counts = {}
    for phase, db in [('before',before),('after',after)]:
        dest = out/'source-exports'/phase
        db.export(dest,source='bianchi_2025_nr_nanoclay')
        manifest,rows = read_snapshot(dest)
        expected = {r['property']['id']:r for r in db.records(source='bianchi_2025_nr_nanoclay')}
        assert rows == expected
        counts[phase] = len(rows)
    assert counts == {'before':9,'after':11}
    for lang in ('en','zh','ja','de'):
        with patch('materials_boundaries.catalog.read_catalog',side_effect=lambda n:after.data[n]):
            rendered = render_material_catalog({'schema_version':'1.0.0','records':props},'reference-properties',lang)
        assert all(token in rendered for token in ('200','400','1.08','0.13','2.10','0.23','unknown'))
        (out/('render-'+lang+'.txt')).write_text(rendered,encoding='utf-8')
    for name in ('native-candidate-r1.json','VALIDATION_R1.json'):
        (area/name).write_bytes((out/name).read_bytes())
    write(area/'EXPORT_RENDER_VALIDATION_R1.json',{'baseline_snapshot':before.snapshot,'preview_snapshot':after.snapshot,'complete_joined_exports':counts,'equality':'all_fields_equal_query','four_language_targets_means_SDs_and_unknowns':'passed','native_applied':False,'installed':'not_run','tests':'No new run;runtime and schema unchanged from127-test acceptedr12','full_history_regression':'not_run'})
    print(counts)


if __name__ == '__main__':
    main()
