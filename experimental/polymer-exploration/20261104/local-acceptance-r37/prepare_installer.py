"""Derive a bounded installer from exact approved r36 source, replacing probe fully."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent


def main():
    previous = HERE.parent / 'local-acceptance-r36'
    path = previous / 'build_install_r36.py'
    entry = json.loads((previous / 'REVIEW_ACCEPTANCE_INPUTS_R36.json').read_bytes())
    expected = entry['repo_files_sha256'][path.relative_to(ROOT).as_posix()]
    assert hashlib.sha256(path.read_bytes()).hexdigest() == expected
    code = path.read_text(encoding='utf-8')
    start = code.index("rows=list(db.records(quantity='glass_transition_temperature'")
    end = code.index("\n'''", start)
    probe = r'''rows=list(db.records(query='_tga_platinum_pan',source='ivdre_2024_lpo_rigid_pur'));assert len(rows)==28
for row in rows:
    p=row['property'];assert p['sample_count']['value'] is None and p['summary_statistic']=='not_stated'
    assert p['uncertainty']['type']=='reported_plus_minus_unspecified'
    assert p['uncertainty']['confidence_level'] is None and p['uncertainty']['coverage_factor'] is None
    assert p['conditions']['temperature']['status']=='reported' and p['conditions']['conditioning']['text'] is None
    assert len(row['state']['property_ids'])==7 and p['id'] in row['state']['property_ids']
    if p['quantity'] in ('tga_residue_percentage','temperature_at_specified_mass_loss'):
        assert p['mass_reference_basis']['status']=='not_reported_in_inspected_source' and p['mass_reference_basis']['text'] is None
    assert p['evaluation_support']=='catalog_only' and not p['engineering_allowable'] and not p['universal_bound']
export=folder/'installed-twenty-eight-export';db.export(export,query='_tga_platinum_pan',source='ivdre_2024_lpo_rigid_pur')
assert read_snapshot(export)[1]=={row['record_id']:row for row in rows}
native_evidence=folder.parent
assert read_snapshot(export)[1]==read_snapshot(native_evidence/'accepted-new-twenty-eight')[1]
allsource=list(db.records(source='ivdre_2024_lpo_rigid_pur'));assert len(allsource)==40
full=folder/'installed-source-forty-export';db.export(full,source='ivdre_2024_lpo_rigid_pur')
assert read_snapshot(full)[1]=={row['record_id']:row for row in allsource}
assert read_snapshot(full)[1]==read_snapshot(native_evidence/'accepted-complete-source-forty')[1]
original=list(db.records(query='_tga_platinum_pan',source='ivdre_2024_lpo_rigid_pur'))
rows[0]['property']['reported_value']['number']='999'
assert list(db.records(query='_tga_platinum_pan',source='ivdre_2024_lpo_rigid_pur'))==original
print(json.dumps({'version':distribution.version,'snapshot':db.snapshot,'properties':len(db.properties),'states':len(db.states),'verified_payload_files':len(payload),'installed_record_hashes_checked':checked,'new_TGA_records':len(rows),'complete_source_records':len(allsource),'installed_graph':'passed','joined_export_roundtrip':'exact','installed_exports_equal_accepted_candidates':True,'detached_copy_isolation':True,'module_path':str(materials_boundaries.__file__)}))'''
    code = code[:start] + probe + code[end:]
    code = code.replace('R36', 'R37').replace('r36', 'r37')
    code = code.replace('probe-r37-r2.log', 'probe-r37-r1.log')
    assert 'glass_transition_temperature' not in code
    assert 'thermal_conductivity' not in code
    assert 'installed-twenty-eight-export' in code and 'accepted-complete-source-forty' in code
    with (HERE / 'build_install_r37.py').open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(code)
    print('r37 installer generated from exact approved r36 base;complete probe replaced')


if __name__ == '__main__':
    main()
