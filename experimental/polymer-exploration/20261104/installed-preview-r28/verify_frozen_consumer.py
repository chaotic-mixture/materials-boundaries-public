"""Verify two same-state peaks through the frozen in-process catalogue consumer."""
import hashlib,importlib.util,json,sys
from pathlib import Path
from materials_boundaries.database import Database,read_snapshot
from materials_boundaries.catalog import query_catalog
from materials_boundaries.material_references import resolve_materials
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
    root=Path(sys.argv[1]).resolve();install=Path(sys.argv[2]).resolve()
    assert Path(sys.prefix).resolve()==(install/'venv').resolve()
    module_path=root/'experimental/platform/query-service/materials_query/catalog_snapshot.py'
    frozen=install/'FROZEN_CONSUMER_COMPONENT_R28.py';raw=module_path.read_bytes()
    with frozen.open('xb') as f:f.write(raw)
    binding=dict(component_repo_path=module_path.relative_to(root).as_posix(),component_sha256=sha(module_path),
        frozen_path=str(frozen),frozen_sha256=sha(frozen),source_utf8=raw.decode('utf-8'),
        scope='Exact trusted repository component copy,read-only in-process probe;no HTTP/server or deployment.')
    assert binding['component_sha256']==binding['frozen_sha256']
    write(install/'FROZEN_CONSUMER_SOURCE_BINDING_R28.json',binding)
    spec=importlib.util.spec_from_file_location('r28_frozen_catalog_snapshot',frozen)
    module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
    db=Database();facts=json.loads((root/'experimental/polymer-exploration/20261104/phbv39-melting-peaks-native-r1/MAPPING_FACTS_R1.json').read_bytes())
    expected_snapshot=json.loads((root/'experimental/polymer-exploration/20261104/phbv39-melting-peaks-native-r1/REVIEW_INPUTS_R1.json').read_bytes())['combined_snapshot']
    assert db.snapshot==expected_snapshot and len(db.properties)==5335
    data_dir=Path(__import__('materials_boundaries').__file__).resolve().parent/'data'
    assert data_dir.is_relative_to(install/'venv')
    before_hashes={n:sha(data_dir/(n+'.json')) for n in db.data}
    snapshot=module.CatalogSnapshot.from_packaged();state_id,=facts['state_records']
    expected=resolve_materials([state_id],db.data['materials'],db.data['reference_properties'],db.data['sources'])[0]
    resolved=snapshot.resolve(state_id);assert resolved==expected
    assert len(resolved['properties'])==3
    peaks={p['id']:p for p in resolved['properties'] if p['quantity']=='melting_peak_temperature'}
    assert peaks==facts['property_records'] and len(peaks)==2
    assert snapshot.query_exact('materials',state_id)==query_catalog('materials',record_id=state_id)
    for pid,prop in peaks.items():
        assert snapshot.record('reference-properties',pid)==prop
        assert snapshot.query_exact('reference-properties',pid)==query_catalog('reference-properties',record_id=pid)
    sid=facts['source_record']['id'];search=snapshot.search_english('reference-properties',sid,limit=100)
    assert not search['truncated'] and len(search['records'])==7
    assert search['records']==query_catalog('reference-properties',source_id=sid)['records']
    _,exported=read_snapshot(install/('installed-export-'+sid))
    assert exported=={r['property']['id']:r for r in db.records(source=sid)} and len(exported)==7
    quantity_export=install/'installed-melting-peak-export'
    db.export(quantity_export,quantity='melting_peak_temperature')
    assert read_snapshot(quantity_export)[1]=={r['record_id']:r for r in db.records(quantity='melting_peak_temperature')}
    detached=snapshot.resolve(state_id);detached['properties'][0]['scope_note']='Probe-only detached mutation.'
    assert snapshot.resolve(state_id)==resolved
    # The immediate predecessor uses the same runtime and exact frozen pre-apply
    # native bytes; this is a stale-selection probe, not a historical suite replay.
    baseline={n:json.loads((root/'materials_boundaries/data'/(n+'.json')).read_bytes()) for n in db.data}
    before=Database(baseline)
    frozen_inputs=json.loads((install/'BUILD_INPUTS_R28.json').read_bytes())['baseline_inputs']
    baseline_hashes={n:sha(root/'materials_boundaries/data'/(n+'.json')) for n in db.data}
    assert all(h==frozen_inputs['materials_boundaries/data/'+n+'.json'] for n,h in baseline_hashes.items())
    baseline_snapshot=json.loads((root/'experimental/polymer-exploration/20261104/phbv39-melting-peaks-native-r1/REVIEW_INPUTS_R1.json').read_bytes())['baseline_snapshot']
    assert before.snapshot==baseline_snapshot and len(before.properties)==5333
    predecessor=module.CatalogSnapshot(baseline['materials'],baseline['reference_properties'],baseline['sources'])
    assert predecessor.version!=snapshot.version
    try:module.LatestCatalog(snapshot).read_selected(module.Selection(predecessor.version,'materials',state_id))
    except ValueError as error:assert 'stale' in str(error)
    else:raise AssertionError('Immediate predecessor selection was accepted')
    assert module.LatestCatalog(snapshot).read_selected(module.Selection(snapshot.version,'materials',state_id))==snapshot.record('materials',state_id)
    assert before_hashes=={n:sha(data_dir/(n+'.json')) for n in db.data}
    assert baseline_hashes=={n:sha(root/'materials_boundaries/data'/(n+'.json')) for n in db.data}
    assert sha(module_path)==sha(frozen)==binding['component_sha256']
    write(install/'FROZEN_CONSUMER_VALIDATION_R28.json',dict(status='in_process_same_state_two_peaks_preserved',
        core_snapshot=db.snapshot,component_version=snapshot.version,predecessor_component_version=predecessor.version,
        component_sha256=binding['component_sha256'],installed_import_path=str(data_dir.parent),
        resolved_state_count=1,resolved_property_count=3,melting_peak_objects=2,complete_source_exports=7,
        complete_quantity_export_objects=2,installed_quantity_export_sha256={p.name:sha(p) for p in quantity_export.iterdir() if p.is_file()},
        preacceptance_native_table_sha256_unchanged=baseline_hashes,
        detached_copy_isolated=True,immediate_predecessor_selection_rejected=True,current_selection_equal_record=True,
        predecessor_scope='Immediate preacceptance content under current installed runtime;not a historical service/runtime replay.',
        installed_table_sha256_unchanged=before_hashes,native_data_changed=False,HTTP_routes='not_run',
        full_platform_suite='not_run',full_history_regression='not_run',execution_observation='Parent execution and receipt;not independently authenticated OS trace.'))
    print(json.dumps(dict(consumer='same_state_two_peaks_preserved',resolved_properties=3,peaks=2,exports=7,snapshot=db.snapshot)))
if __name__=='__main__':main()
