"""Read-only check of the frozen NBR audit against native bytes."""
import hashlib
import json
from pathlib import Path


def main():
    packet = Path(__file__).resolve().parent
    root = next(p for p in packet.parents if (p / 'materials_boundaries/data').is_dir())
    audit = json.loads((packet / 'SOURCE_READBACK_R1.json').read_text(encoding='utf-8'))
    for name, expected in audit['native_file_sha256'].items():
        actual = hashlib.sha256((root / 'materials_boundaries/data' / name).read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError('Native baseline changed: ' + name)
    table = json.loads((root / 'materials_boundaries/data/reference_properties.json').read_text(encoding='utf-8'))
    record = next(r for r in table['records'] if r['id'] == audit['property_id'])
    expected = audit['native_assertions']
    actual = {
        'source_id': record['source_id'],
        'value': record['reported_value']['number'],
        'unit': record['reported_value']['unit_code'],
        'uncertainty_type': record['uncertainty']['type'],
        'uncertainty_amplitude': record['uncertainty']['number'],
        'summary_statistic': record['summary_statistic'],
        'sample_count': record['sample_count']['value'],
        'density_basis': record['density_basis'],
        'condition_statuses': {k: record['conditions'][k]['status'] for k in expected['condition_statuses']},
    }
    if actual != expected:
        raise ValueError('Native record differs from audited assertions')
    print(json.dumps({'status': 'passed', 'native_files': len(audit['native_file_sha256']),
                      'property_records_checked': 1, 'writes': 0,
                      'scope': 'byte binding and selected fields; not scientific review or regression tests'}))


if __name__ == '__main__':
    main()
