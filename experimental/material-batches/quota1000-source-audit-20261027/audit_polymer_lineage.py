"""Offline lineage/aggregate audit. Does not approve rights or admit materials."""
import argparse
from collections import Counter
import csv
from decimal import Decimal
import hashlib
import io
import json
from pathlib import Path

PINS = {
    'tg': 'e3064f5d55830a93b4d43d8a709a4fbada7742c19a311c69c0aada6793422a91',
    'radonpy': '4ee41d526db3d03eb5b83010672b4e63a4d51a114871a2187ca7fd57d30556a4',
}


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf8')


def read_rows(data, profile):
    if hashlib.sha256(data).hexdigest() != PINS[profile]:
        raise ValueError('source checksum mismatch')
    reader = csv.DictReader(io.StringIO(data.decode('utf-8-sig'), newline=''), strict=True)
    if not reader.fieldnames or len(reader.fieldnames) != len(set(reader.fieldnames)):
        raise ValueError('missing or repeated headers')
    rows = list(reader)
    if any(None in row or any(v is None for v in row.values()) for row in rows):
        raise ValueError('malformed CSV record')
    return rows


def aggregate_median(raw_values, raw_count, raw_label):
    def reject_constant(value):
        raise ValueError('nonfinite source value: ' + value)
    values = json.loads(raw_values, parse_float=Decimal, parse_int=Decimal,
                        parse_constant=reject_constant)
    if not isinstance(values, list) or not values or len(values) > 100:
        raise ValueError('expected bounded nonempty Tg value list')
    if any(not isinstance(v, Decimal) or not v.is_finite() or v <= 0 for v in values):
        raise ValueError('invalid absolute-temperature source value')
    count = Decimal(raw_count)
    label = Decimal(raw_label)
    if not count.is_finite() or count != count.to_integral_value() or count < 1:
        raise ValueError('invalid contribution count')
    if not label.is_finite() or label <= 0:
        raise ValueError('invalid aggregate label')
    ordered = sorted(values)
    half = len(ordered) // 2
    median = ordered[half] if len(ordered) % 2 else (ordered[half - 1] + ordered[half]) / 2
    return {'count_matches': count == len(values), 'median_matches': label == median,
            'calculated_median_kelvin': str(median)}


def audit_tg(rows):
    aggregates = []
    for ordinal, row in enumerate(rows, 1):
        if row['meta.tg_values']:
            aggregates.append({'csv_record_ordinal': ordinal,
                               **aggregate_median(row['meta.tg_values'], row['meta.num_of_points'], row['labels.Exp_Tg(K)'])})
    return {
        'rows': len(rows),
        'source_label_counts': dict(sorted(Counter(r['meta.source'] for r in rows).items())),
        'curator_reliability_label_counts': dict(sorted(Counter(r['meta.reliability'] for r in rows).items())),
        'rows_with_explicit_contributing_values': len(aggregates),
        'contribution_count_mismatches': [r for r in aggregates if not r['count_matches']],
        'exact_decimal_median_mismatches': [r for r in aggregates if not r['median_matches']],
        'grea_labelled_rows_held_for_upstream_notice': sum(r['meta.source'] == 'GREA' for r in rows),
        'other_source_label_rows_not_cleared': sum(r['meta.source'] != 'GREA' for r in rows),
        'admitted_increment': 0,
        'interpretation': 'Counts are contributing dataset entries, not independent specimens or production batches. '
                          'Exact median consistency is not original-source verification. The single meta.source '
                          'label does not enumerate every upstream contribution to an aggregate.',
    }


def audit_radonpy(rows):
    required = ('monomer_ID', 'smiles', 'temp', 'press', 'density', 'density_min',
                'density_max', 'density_std', 'density_count', 'tacticity', 'DP', 'n_mol')
    if any(not set(required).issubset(row) for row in rows):
        raise ValueError('missing required computational source fields')
    issues = []
    for ordinal, row in enumerate(rows, 1):
        try:
            density, low, high = (Decimal(row[k]) for k in ('density', 'density_min', 'density_max'))
            count = Decimal(row['density_count'])
            if not all(v.is_finite() for v in (density, low, high, count)):
                raise ValueError('nonfinite density/count')
            if not (0 < low <= density <= high) or count < 1 or count != count.to_integral_value():
                raise ValueError('density bounds or replica-count inconsistency')
        except (ValueError, ArithmeticError) as exc:
            issues.append({'csv_record_ordinal': ordinal, 'issue': str(exc)})
    return {
        'rows': len(rows), 'literal_monomer_ids': len({r['monomer_ID'] for r in rows}),
        'literal_smiles_strings': len({r['smiles'] for r in rows}),
        'canonical_polymer_identity_count': None, 'baseline_overlap_count': None,
        'source_temperature_labels': dict(Counter(r['temp'] for r in rows)),
        'source_pressure_labels': dict(Counter(r['press'] for r in rows)),
        'source_density_count_labels': dict(Counter(r['density_count'] for r in rows)),
        'density_numeric_consistency_issues': issues,
        'evidence_kind': 'published_computational_reference',
        'experimental_rows_selected': 0, 'admitted_increment': 0,
        'source_name_count_discrepancy': 'File/README calls the dataset PI1070, while the pinned CSV contains 1077 records. Equivalence to the paper dataset is unverified.',
        'holds': ['Dataset-specific reuse scope and upstream structure provenance need review.',
                  'Canonical polymer identities and existing-catalog overlaps need review.',
                  'CSV units, averaging/SD/count semantics and version linkage to the methods need review.',
                  'Independent scientific/source review and explicit admission are pending.'],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tg', type=Path, required=True)
    parser.add_argument('--radonpy', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    inputs = {k: p.read_bytes() for k, p in [('tg', args.tg), ('radonpy', args.radonpy)]}
    report = {'schema': 'polymer-lineage-audit/1', 'source_sha256': dict(PINS),
              'tg': audit_tg(read_rows(inputs['tg'], 'tg')),
              'radonpy': audit_radonpy(read_rows(inputs['radonpy'], 'radonpy'))}
    payload = encode(report)
    if args.output.exists():
        if args.output.read_bytes() != payload:
            raise ValueError('refusing different existing audit')
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(payload)
    print('Source rows audited; admitted increment 0.')


if __name__ == '__main__':
    main()
