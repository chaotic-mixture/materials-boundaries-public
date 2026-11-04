"""Record inspected supplement scope and unchanged native unknowns."""
from pathlib import Path
from collections import Counter
from copy import deepcopy
import hashlib
import json
import zipfile

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
EXT = ROOT.parent / 'open-database-evidence/polymer-epoxy-supplement-20261104-r1'
SID = 'tarasov_2022_pna_bpf_epoxy'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def write(name, obj):
    with (HERE / name).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(obj, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def main():
    inputs = {f'materials_boundaries/data/{name}.json': sha(ROOT / f'materials_boundaries/data/{name}.json')
              for name in ('materials', 'reference_properties', 'sources')}
    properties = read(ROOT / 'materials_boundaries/data/reference_properties.json')
    sources = read(ROOT / 'materials_boundaries/data/sources.json')
    selected = [p for p in properties['records'] if p['source_id'] == SID]
    assert len(selected) == 40
    native_source = next(s for s in sources['records'] if s['id'] == SID)
    acquisition = read(EXT / 'ACQUISITION_R2.json')
    assert acquisition['status'] == 200 and acquisition['bytes'] == 1469991
    assert sha(EXT / 'supplementary-response.zip') == acquisition['sha256']
    with zipfile.ZipFile(EXT / 'polymers-14-04547-s001.zip') as archive:
        assert len(archive.infolist()) == 3
    plots = [
        {'file': 'Figure S1. Flexural properties.png', 'panels': ['Flexural strength (MPa)', 'Flexural modulus (GPa)', 'Flexural elongation at break (%)']},
        {'file': 'Figure S2. Impact strength.png', 'panels': ['Izod impact strength (kJ/m2)']},
        {'file': 'Figure S3. Tensile properties.png', 'panels': ['Tensile strength (MPa)', 'Tensile modulus (GPa)', 'Tensile elongation at break (%)']},
    ]
    for plot in plots:
        plot.update(sha256=sha(EXT / plot['file']),
            visible_category_order=['DGEBA', 'DGEBF', 'PNA-BPF-5', 'PNA-BPF-4', 'PNA-BPF-3', 'PNA-BPF-2', 'PNA-BPF-1', 'PNA-BPF-S'],
            vertical_axis='Percent ticks;not absolute MPa/GPa/kJ/m2 property coordinates despite dimensional legend labels',
            visible_numerical_point_labels=False, visible_error_bars=False,
            replicate_ids_or_count=False, temperature_RH_conditioning=False,
            disposition='Do not digitize,invert normalization,reconstruct absolute properties or infer zero scatter/n/mean.')
    facts = {'schema': 'existing-epoxy-supplement-condition-audit/1', 'source_id': SID,
        'doi': '10.3390/polym14214547', 'PMCID': 'PMC9655627',
        'primary_supplement_url': acquisition['requested_url'], 'outer_response_sha256': acquisition['sha256'],
        'nested_zip_sha256': sha(EXT / 'polymers-14-04547-s001.zip'),
        'outer_response_entries': len(acquisition['archive_entries']), 'nested_assets': plots,
        'source_roles': {'S1': 'Flexural group comparison', 'S2': 'Izod group comparison', 'S3': 'Tensile group comparison', 'DSC': 'Not addressed by these three images'},
        'normalization_adjudication': 'Percentage axes and reference comparison visible;normalization equation/denominator not explicitly printed in inspected images. DGEBA appears at0% but that alone is not a verified inversion rule or baseline value.',
        'native_records': [{'id': p['id'], 'sha256': hashlib.sha256(json.dumps(p, ensure_ascii=False, sort_keys=True).encode()).hexdigest(), 'quantity': p['quantity'], 'temperature_status': p['conditions']['temperature']['status'], 'conditioning_status': p['conditions']['conditioning']['status'], 'sample_count': p['sample_count']} for p in selected],
        'current_gap_counts': {'properties': len(selected), 'temperature_not_reported': sum(p['conditions']['temperature']['status'] == 'not_reported_in_inspected_source' for p in selected),
            'conditioning_not_reported': sum(p['conditions']['conditioning']['status'] == 'not_reported_in_inspected_source' for p in selected),
            'n_unknown': sum(p['sample_count']['value'] is None for p in selected), 'quantities': dict(Counter(p['quantity'] for p in selected))},
        'rights_boundary': 'Existing article license metadata retained;no asset-specific blanket license established by image-only inspection. No source images/archives/PDF/XML bundled or relicensed under software license.',
        'unresolved': ['Mechanical test temperature/RH/conditioning', 'Exact selected-cell n and independent batches', 'Central statistic/dispersion construction', 'Supplement percentage normalization equation/denominator', 'Supplement asset-specific rights and latest revision/notices'],
        'native_changed': False, 'unknowns_filled': 0, 'new_properties_states_identities': [0, 0, 0]}
    write('SOURCE_FACTS_R1.json', facts)
    proposed = deepcopy(native_source)
    if acquisition['requested_url'] not in proposed['urls']:
        proposed['urls'].append(acquisition['requested_url'])
    proposed['claim_notes'].append('Official EuropePMC supplementary response inspected2026-11-04:40assets including nested polymers-14-04547-s001.zip with exactly3PNG FiguresS1flexural/S2Izod/S3tensile. Percent comparison plots,not absolute property data;no point numerics,errorbars,replicate IDs/n or temperature/RH/conditioning. No digitization or normalization inversion. Existing40source properties and missing mechanical temperature/conditioning/n preserved;DSC not addressed. Source assets retained externally;asset-specific rights/latest notices not established.')
    write('SOURCE_UPDATE_PROPOSAL_R1.json', {'source_id': SID, 'baseline_source': native_source, 'proposed_source': proposed,
        'changed_fields': [key for key in native_source if native_source[key] != proposed[key]], 'native_applied': False})
    write('VALIDATION_R1.json', {'scope': 'Acquisition fingerprints/3asset completeness/40unchanged source records;not tests',
        'native_before_sha256': inputs, 'native_inputs_unchanged': all(sha(ROOT / name) == digest for name, digest in inputs.items()),
        'current_gap_counts': facts['current_gap_counts'], 'unknowns_filled': 0, 'native_applied': False,
        'tests_installation_fullhistory_CI': 'not_run', 'pushed': False})
    print(json.dumps({'source_properties': len(selected), 'nested_images': 3, 'gap_counts': facts['current_gap_counts'], 'native_applied': False}), flush=True)


if __name__ == '__main__':
    main()
