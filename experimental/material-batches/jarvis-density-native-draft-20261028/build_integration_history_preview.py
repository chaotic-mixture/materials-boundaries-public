"""Freeze an isolated append image and audit exact predecessor data recovery."""
import argparse
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import shutil
import sys

BATCH = Path(__file__).resolve().parent
ROOT = BATCH.parents[2]
CATALOGS = {'materials': 'materials.json', 'properties': 'reference_properties.json', 'sources': 'sources.json'}
TABLES = {'identities': ('materials', 'identities'), 'grades': ('materials', 'grades'),
          'states': ('materials', 'records'), 'properties': ('properties', 'records'), 'sources': ('sources', 'records')}
NATIVE_PATH = 'experimental/material-batches/jarvis-density-native-draft-20261028/native-candidate.json'
NATIVE_SHA = '82a2d8332f934b31567cac4d50960871792841321a94bd4357500604f6184e85'


def read_exact_graph(root, ledger):
    raw = {key: (root / 'materials_boundaries/data' / filename).read_bytes() for key, filename in CATALOGS.items()}
    hashes = {key: sha256(value).hexdigest() for key, value in raw.items()}
    if hashes not in (ledger['baseline_sha256'], ledger['current_sha256']):
        raise AssertionError('Unknown complete raw catalog image')
    return {key: json.loads(value) for key, value in raw.items()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    stage, output = args.stage.resolve(), args.output_dir.resolve()
    if output.exists() or not output.is_relative_to(ROOT.parent / 'growth-source-cache'):
        raise ValueError('Use a new isolated external source-cache directory')
    sys.path[:0] = [str(stage), str(ROOT / 'tests'), str(ROOT)]
    from materials_boundaries.material_references import merge_material_catalogs, validate_material_catalog
    from material_append_history import encoded, recover_catalogs, graph_hashes
    import materials_boundaries.material_references as references
    if not Path(references.__file__).resolve().is_relative_to(stage):
        raise ValueError('The approved isolated implementation must be selected')
    manifest = json.loads((BATCH / 'draft-manifest.json').read_bytes())
    for path, values in manifest['changes'].items():
        if sha256((stage / path).read_bytes()).hexdigest() != values['draft_sha256']:
            raise ValueError('Changed isolated implementation: ' + path)
        if sha256((ROOT / path).read_bytes()).hexdigest() != values['baseline_sha256']:
            raise ValueError('Changed live runtime input: ' + path)
    native_raw = (ROOT / NATIVE_PATH).read_bytes()
    if sha256(native_raw).hexdigest() != NATIVE_SHA:
        raise ValueError('Different reviewed native mapping')
    native = json.loads(native_raw)['catalogs']
    baseline_raw = {key: (ROOT / 'materials_boundaries/data' / name).read_bytes() for key, name in CATALOGS.items()}
    acceptance = json.loads((ROOT / 'experimental/material-batches/sanchez-al-mea-revised-20261027/LOCAL_ACCEPTANCE.json').read_bytes())
    for key, name in CATALOGS.items():
        if sha256(baseline_raw[key]).hexdigest() != acceptance['catalog_sha256'][name]:
            raise ValueError('Different accepted local alloy baseline: ' + name)
    baseline = {key: json.loads(raw) for key, raw in baseline_raw.items()}
    if any(encoded(baseline[key]) != baseline_raw[key] for key in CATALOGS):
        raise ValueError('Predecessor catalog formatting changed')
    current = merge_material_catalogs(baseline['materials'], baseline['properties'], baseline['sources'], native)
    validate_material_catalog(current['materials'], current['properties'], current['sources'])
    repeated = merge_material_catalogs(current['materials'], current['properties'], current['sources'], native)
    if repeated != current:
        raise AssertionError('Reviewed append is not idempotent')
    ledger = {
        'schema_version': 1, 'baseline_commit': 'f13586759af6a391635fa81da20c73eb6a6c1c6c',
        'baseline_scope': 'Exact locally accepted uncommitted Sanchez snapshot, not HEAD catalog bytes or main release.',
        'baseline_sha256': {key: sha256(raw).hexdigest() for key, raw in baseline_raw.items()},
        'current_sha256': graph_hashes(current),
        'packets': [{'path': NATIVE_PATH, 'sha256': NATIVE_SHA,
                     'added_ids': {key: sorted(row['id'] for row in native[table][field])
                                   for key, (table, field) in TABLES.items()}}],
    }
    (output / 'materials_boundaries/data').mkdir(parents=True)
    (output / NATIVE_PATH).parent.mkdir(parents=True)
    shutil.copy2(ROOT / NATIVE_PATH, output / NATIVE_PATH)
    for key, name in CATALOGS.items():
        (output / 'materials_boundaries/data' / name).write_bytes(encoded(current[key]))
    recovered = recover_catalogs(output, read_exact_graph(output, ledger), ledger)
    if recovered != baseline or any(encoded(recovered[key]) != baseline_raw[key] for key in CATALOGS):
        raise AssertionError('Predecessor recovery is not exact')
    if recover_catalogs(output, baseline, ledger) != baseline:
        raise AssertionError('Exact predecessor was not preserved')
    # Also prove adjacency to the already accepted previous five-alloy layer.
    previous_ledger = json.loads((ROOT / 'tests/sanchez_al_mea_runtime/data-history.json').read_bytes())
    if ledger['baseline_sha256'] != previous_ledger['current_sha256']:
        raise AssertionError('New data history is not adjacent to the alloy checkpoint')
    prior = recover_catalogs(ROOT, recovered, previous_ledger)
    if len(prior['materials']['identities']) != 1175:
        raise AssertionError('Older alloy layer no longer recovers its predecessor')
    negative_names = ['partial_identity', 'partial_property', 'reorder_additions', 'changed_new_value',
                      'changed_old_value', 'changed_metadata', 'duplicate_addition']
    for name in negative_names:
        mutated = deepcopy(current)
        if name == 'partial_identity':
            mutated['materials']['identities'].pop()
        elif name == 'partial_property':
            mutated['properties']['records'].pop()
        elif name == 'reorder_additions':
            mutated['materials']['identities'][-2:] = reversed(mutated['materials']['identities'][-2:])
        elif name == 'changed_new_value':
            mutated['properties']['records'][-1]['reported_value']['number'] = '1'
        elif name == 'changed_old_value':
            mutated['materials']['identities'][0]['name'] += ' changed'
        elif name == 'changed_metadata':
            mutated['sources']['unreviewed_extra'] = True
        else:
            mutated['properties']['records'].append(deepcopy(mutated['properties']['records'][-1]))
        try:
            recover_catalogs(output, mutated, ledger)
        except AssertionError:
            continue
        raise AssertionError('Unknown mutation inherited recovery: ' + name)
    for key, name in CATALOGS.items():
        path = output / 'materials_boundaries/data' / name
        raw = path.read_bytes()
        path.write_bytes(raw + b' ')
        try:
            try:
                read_exact_graph(output, ledger)
            except AssertionError:
                pass
            else:
                raise AssertionError('Unknown whitespace image was accepted: ' + name)
        finally:
            path.write_bytes(raw)
    (output / 'data-history.json').write_bytes(encoded(ledger))
    (BATCH / 'data-history-preview.json').write_bytes(encoded(ledger))
    receipt = {
        'schema': 'jarvis-isolated-data-history-preview/1', 'status': 'producer_data_recovery_checks_passed',
        'scope': 'Exact catalog append, idempotence and data-layer recovery only; no file/registry/document history or full runtime admission.',
        'output_dir': str(output), 'native_sha256': NATIVE_SHA,
        'data_history_sha256': sha256(encoded(ledger)).hexdigest(),
        'baseline_sha256': ledger['baseline_sha256'], 'prospective_catalog_sha256': ledger['current_sha256'],
        'prospective_counts': {'identities': 3180, 'grades': 31, 'states': 3181, 'properties': 3197, 'sources': 131},
        'exact_recovery_to_1180_identity_snapshot': True, 'adjacent_recovery_to_1175_identity_checkpoint': True,
        'prefix_objects_order_and_root_metadata_preserved': True, 'append_idempotent': True,
        'rejected_graph_mutations': negative_names, 'rejected_raw_whitespace_images': 3,
        'live_runtime_changed': False, 'admitted_increment': 0,
        'pending': ['Independent data-history review', 'File/registry/document exact recovery',
                    'Live runtime integration', 'Full regression', 'Real installed checks', 'Runtime admission'],
    }
    (BATCH / 'data-history-preview-validation.json').write_bytes(encoded(receipt))
    print(json.dumps({'status': receipt['status'], 'data_history_sha256': receipt['data_history_sha256'],
                      'graph_negatives': len(negative_names), 'raw_image_negatives': 3, 'admitted_increment': 0}))


if __name__ == '__main__':
    main()
