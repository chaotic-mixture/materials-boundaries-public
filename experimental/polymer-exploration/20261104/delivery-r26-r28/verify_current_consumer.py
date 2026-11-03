"""Exercise the frozen in-process catalogue consumer against an installed core.

This does not start or certify the experimental HTTP/federation platform.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from materials_boundaries.catalog import query_catalog
from materials_boundaries.database import Database, read_snapshot
from materials_boundaries.material_references import resolve_materials


def main():
    root=Path(sys.argv[1]).resolve()
    install=Path(sys.argv[2]).resolve()
    evidence=Path(sys.argv[3]).resolve()
    evidence.mkdir(exist_ok=False)
    area=root/'experimental/polymer-exploration/20261104/delivery-r26-r28'
    delta=json.loads((area/'NATIVE_DELTA_R26_R28.json').read_bytes())
    module_path=root/'experimental/platform/query-service/materials_query/catalog_snapshot.py'
    spec=importlib.util.spec_from_file_location('delivery_frozen_catalog_snapshot',module_path)
    module=importlib.util.module_from_spec(spec)
    sys.modules[spec.name]=module
    spec.loader.exec_module(module)
    db=Database()
    assert db.snapshot==delta['current_snapshot'] and len(db.properties)==5335
    data_dir=Path(__import__('materials_boundaries').__file__).resolve().parent/'data'
    before_hashes={name:hashlib.sha256((data_dir/(name+'.json')).read_bytes()).hexdigest() for name in db.data}
    snapshot=module.CatalogSnapshot.from_packaged()
    states=list(delta['existing_state_changes'])+list(delta['new_state_ids'])
    assert len(states)==6
    expected=resolve_materials(states,db.data['materials'],db.data['reference_properties'],db.data['sources'])
    for sid,row in zip(states,expected):
        assert snapshot.resolve(sid)==row,sid
        assert snapshot.query_exact('materials',sid)==query_catalog('materials',record_id=sid)
    for pid in delta['new_property_ids']:
        assert snapshot.record('reference-properties',pid)==db.properties[pid]
        assert snapshot.query_exact('reference-properties',pid)==query_catalog('reference-properties',record_id=pid)
    source_counts={}
    for sid,expected_count in [('abbasi_2022_manure_phbv',7),('tarasov_2022_pna_bpf_epoxy',40)]:
        result=snapshot.search_english('reference-properties',sid,limit=100)
        assert not result['truncated'] and len(result['records'])==expected_count
        assert result['records']==query_catalog('reference-properties',source_id=sid)['records']
        manifest,exported=read_snapshot(install/('installed-export-'+sid))
        assert exported=={r['property']['id']:r for r in db.records(source=sid)}
        source_counts[sid]=len(exported)
    phbv=snapshot.resolve('state_abbasi2022_manure_phbv39_dsc_second_heating')
    assert len(phbv['properties'])==3 and sum(p['quantity']=='melting_peak_temperature' for p in phbv['properties'])==2
    original=snapshot.resolve(states[0])
    detached=snapshot.resolve(states[0])
    detached['properties'][0]['scope_note']='Verification-only detached mutation;never native data.'
    assert snapshot.resolve(states[0])==original
    latest=module.LatestCatalog(snapshot)
    try:
        latest.read_selected(module.Selection('0'*64,'materials',states[0]))
    except ValueError as error:
        assert 'stale' in str(error)
    else:
        raise AssertionError('Stale consumer selection was accepted')
    after_hashes={name:hashlib.sha256((data_dir/(name+'.json')).read_bytes()).hexdigest() for name in db.data}
    assert before_hashes==after_hashes
    report={'scope':'Frozen in-process CatalogSnapshot component with actual installed current core;not HTTP or full platform approval',
            'core_import_path':str(data_dir.parent),'core_snapshot':db.snapshot,
            'component_path_hint':str(module_path),'component_sha256':hashlib.sha256(module_path.read_bytes()).hexdigest(),
            'component_version':snapshot.version,'core_and_component_versions_are_distinct':True,
            'complete_resolved_states_equal_core':6,'new_properties_exact_record_and_query_equal':8,
            'complete_source_query_and_joined_export_counts':source_counts,
            'detached_mutation_isolated':True,'stale_selection_rejected':True,
            'three_packaged_tables_unchanged':before_hashes,
            'HTTP_routes':'not_run','legacy_pinned_platform_suite':'not_run_not_rebased',
            'full_history_regression':'not_run','native_data_changed':False}
    with (evidence/'CURRENT_CONSUMER_VALIDATION_R26_R28.json').open('x',encoding='utf-8',newline='\n') as f:
        json.dump(report,f,ensure_ascii=False,indent=2)
        f.write('\n')
    print(json.dumps({'resolved_states':6,'new_properties':8,'joined_exports':sum(source_counts.values()),'scope':'installed core plus frozen in-process component'}))


if __name__=='__main__':main()
