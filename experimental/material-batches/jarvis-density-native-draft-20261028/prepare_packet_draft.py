"""Compile reviewed native facts in an isolated implementation; no runtime writes."""
import argparse
from copy import deepcopy
import gzip
from hashlib import sha256
import json
from pathlib import Path
import sys

BATCH = Path(__file__).resolve().parent
ROOT = BATCH.parents[2]
NATIVE_SHA = '82a2d8332f934b31567cac4d50960871792841321a94bd4357500604f6184e85'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    stage = args.stage.resolve()
    output = args.output_dir.resolve()
    if output.exists() or not output.is_relative_to(ROOT.parent / 'growth-source-cache'):
        raise ValueError('Use a fresh external source-cache output directory')
    sys.path[:0] = [str(stage), str(ROOT)]
    from materials_boundaries import material_references
    from scripts.prepare_formulation_packet import compile_spec, record_sha256, validate_prepared_packet
    if not Path(material_references.__file__).resolve().is_relative_to(stage):
        raise ValueError('The unapplied isolated implementation must be selected')
    manifest = json.loads((BATCH / 'draft-manifest.json').read_bytes())
    for rel, hashes in manifest['changes'].items():
        if sha256((stage / rel).read_bytes()).hexdigest() != hashes['draft_sha256']:
            raise ValueError('Different isolated implementation: ' + rel)
        if sha256((ROOT / rel).read_bytes()).hexdigest() != hashes['baseline_sha256']:
            raise ValueError('Changed live runtime baseline: ' + rel)
    raw = (BATCH / 'native-candidate.json').read_bytes()
    if sha256(raw).hexdigest() != NATIVE_SHA:
        raise ValueError('Different independently reviewed native mapping')
    native = json.loads(raw)
    graph = native['catalogs']
    identities = {r['id']: r for r in graph['materials']['identities']}
    states = {r['id']: r for r in graph['materials']['records']}
    properties = {r['id']: r for r in graph['properties']['records']}
    spec = {
        'schema': 'formulation-packet-spec/1', 'batch_id': 'jarvis-density-native-draft-20261028',
        'baseline_sha256': {key: sha256((ROOT / 'materials_boundaries/data' / (key + '.json')).read_bytes()).hexdigest()
                            for key in ['materials', 'reference_properties', 'sources']},
        'source_records': [{'record': r, 'sha256': record_sha256(r)} for r in graph['sources']['records']],
        'contexts': {key: {'exact': {}} for key in ['identity', 'grade', 'state', 'property']},
        'formulations': [], 'identity_crosswalk': [],
        'review': {
            'status': 'independently_reviewed_native_mapping_and_finite_model_identity_candidate',
            'formal_admitted_delta': 0,
            'verification': {'source_transcription_checked': True, 'independent_scientific_review': False, 'raw_data_reanalysis': False},
            'source_reviews': [{'source_id': graph['sources']['records'][0]['id'], 'status': 'selected_facts_checked',
                                'note': 'Authorized read-only source, native mapping, finite model identity/compositional taxonomy and isolated method reviews are recorded in this batch; current native SHA256 ' + NATIVE_SHA + '. No integration, full regression, installed or publication approval.'}],
            'pending_gates': ['Historical preservation and integration implementation', 'Full regression and real installed checks', 'Runtime admission; no remote writes authorized'],
        },
    }
    for binding in native['bindings']:
        identity = identities[binding['identity_id']]
        state = states[binding['state_id']]
        prop = properties[binding['property_id']]
        spec['formulations'].append({
            'identity': {'context': 'exact', 'fields': deepcopy(identity)}, 'grades': [],
            'states': [{'record': {'context': 'exact', 'fields': deepcopy(state)},
                        'properties': [{'context': 'exact', 'fields': deepcopy(prop)}]}]})
        spec['identity_crosswalk'].append({
            'identity_id': identity['id'], 'source_id': prop['source_id'],
            'source_designations': [state['source_designation']], 'disposition': 'distinct',
            'evidence': deepcopy(identity['evidence']),
            'note': 'Independent finite hypothetical-model identity decision: exact reduced composition ' + binding['composition_key']
                    + '; one bucket only, 24 formal computed compositions excluded, current finite source/family guards checked. Not universal chemical or cross-provider phase equivalence.'})
    baseline = ROOT / 'materials_boundaries/data'
    packet = compile_spec(spec, baseline)
    validate_prepared_packet(packet, baseline)
    if packet['catalogs'] != graph:
        raise ValueError('Compiled catalogs differ from independently reviewed native mapping')
    output.mkdir(parents=True)
    encoded = lambda v: (json.dumps(v, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf8')
    files = {}
    for name, value in [('packet-spec.json', spec), ('prepared-packet.json', packet)]:
        content = encoded(value)
        (output / name).write_bytes(content)
        files[name] = {'sha256': sha256(content).hexdigest(), 'bytes': len(content)}
    packed = gzip.compress((output / 'prepared-packet.json').read_bytes(), mtime=0)
    if sha256(gzip.decompress(packed)).hexdigest() != files['prepared-packet.json']['sha256']:
        raise ValueError('Packet archive verification failed')
    (output / 'prepared-packet.json.gz').write_bytes(packed)
    receipt = {
        'schema': 'jarvis-isolated-prepared-packet-validation/1', 'status': 'compiled_and_exactly_replayed_unadmitted',
        'native_candidate_sha256': NATIVE_SHA, 'isolated_implementation_manifest_sha256': sha256((BATCH / 'draft-manifest.json').read_bytes()).hexdigest(),
        'output_dir': str(output), 'output_files': files, 'gzip_sha256': sha256(packed).hexdigest(),
        'compiled_catalogs_equal_reviewed_native_graph': True, 'exact_replay_passed': True,
        'report': packet['report'],
        'ready_flag_scope': 'Compiler handoff_ready covers its finite identity/source checks only, not historical recovery, integration, full regression, installation or admission.',
        'runtime_data_changed': False, 'admitted_increment': 0,
    }
    # The report crosswalk is already in the packet; avoid duplicating its large list in the receipt.
    receipt['report'] = {k: v for k, v in packet['report'].items() if k != 'identity_crosswalk'}
    (BATCH / 'packet-preparation-validation.json').write_bytes(encoded(receipt))
    print(json.dumps({'status': receipt['status'], 'delta': packet['report']['delta'],
                      'compiler_handoff_ready': packet['report']['handoff_ready'], 'admitted_increment': 0}))


if __name__ == '__main__':
    main()
