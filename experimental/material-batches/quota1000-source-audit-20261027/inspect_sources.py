"""Offline source inventory only. Never admits records or writes runtime data."""
from __future__ import annotations

import argparse
from collections import Counter
import csv
from decimal import Decimal, InvalidOperation
import hashlib
import io
import json
from pathlib import Path

POLY_FIELDS = (
    'PSMILES', 'meta.polymer', 'PSMILES_not_canonicalize', 'labels.Exp_Tg(K)',
    'meta.source', 'meta.tg_range', 'meta.tg_values', 'meta.num_of_points',
    'meta.std', 'meta.reliability',
)
PINS = {
    'polymetrix': ('sha256', 'e3064f5d55830a93b4d43d8a709a4fbada7742c19a311c69c0aada6793422a91', 43615282),
    'mpea': ('sha256', 'c5504d93fd324d1be26cf814d0694ee9ee95578d68a0b38aba6813b939fa2c5d', None),
}


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')


def positive_number(value):
    try:
        number = Decimal(value)
        return number.is_finite() and number > 0
    except (InvalidOperation, ValueError):
        return False


def inspect(data, profile):
    algorithm, expected, length = PINS[profile]
    if hashlib.new(algorithm, data).hexdigest() != expected:
        raise ValueError('source checksum mismatch; incomplete or changed source')
    if length is not None and len(data) != length:
        raise ValueError('source byte length mismatch')
    reader = csv.DictReader(io.StringIO(data.decode('utf-8-sig'), newline=''), strict=True)
    fields = reader.fieldnames
    if not fields or len(fields) != len(set(fields)):
        raise ValueError('missing or repeated column names')
    required = set(POLY_FIELDS if profile == 'polymetrix' else (
        'FORMULA', 'REFERENCE: doi', 'PROPERTY: Exp. Density (g/cm$^3$)',
        'PROPERTY: Calculated Density (g/cm$^3$)',
        'PROPERTY: Exp. Young modulus (GPa)',
        'PROPERTY: Calculated Young modulus (GPa)',
    ))
    if not required.issubset(fields):
        raise ValueError('required source fields missing')
    inventory = []
    keys, references, numeric_columns = Counter(), Counter(), Counter()
    missing_identity = 0
    for index, row in enumerate(reader, start=1):
        if None in row or any(value is None for value in row.values()):
            raise ValueError(f'malformed CSV record {index}')
        key = row['PSMILES' if profile == 'polymetrix' else 'FORMULA']
        if key.strip():
            keys[key] += 1
        else:
            missing_identity += 1
        reference = row['meta.source' if profile == 'polymetrix' else 'REFERENCE: doi']
        references[reference] += 1
        for field, value in row.items():
            if positive_number(value):
                numeric_columns[field] += 1
        # Raw source fields are preserved, never converted to admitted identities.
        selected = {field: row[field] for field in POLY_FIELDS} if profile == 'polymetrix' else row
        inventory.append({
            'csv_record_ordinal': index,
            'raw_row_sha256': hashlib.sha256(encode(row)).hexdigest(),
            'status': 'held',
            'source_fields': selected,
        })
    summary = {
        'schema': 'material-source-inventory/1',
        'profile': profile,
        'source_sha256': hashlib.sha256(data).hexdigest(),
        'source_bytes': len(data),
        'csv_data_records': len(inventory),
        'literal_identity_strings': len(keys),
        'repeated_literal_identity_rows': sum(n - 1 for n in keys.values()),
        'missing_identity_rows': missing_identity,
        'canonical_identity_count': None,
        'baseline_overlap_count': None,
        'admitted_increment': 0,
        'dispositions': {'held': len(inventory)},
        'source_reference_labels': dict(sorted(references.items())),
        'positive_finite_numeric_cells_by_source_column': dict(sorted(numeric_columns.items())),
        'scope': 'Literal strings are inventory keys, not chemically resolved identities. '
                 'Numerical presence is not scientific validity. All rows remain unadmitted.',
        'holds': [
            'Canonical identity and overlap with the admitted baseline need review.',
            'Upstream reference/version/rights chain and row-specific locators need review.',
            'Measurement definitions, original versus aggregated/derived values, and unknown conditions need review.',
            'A supported scientific profile and independent frozen-payload review are required before admission.',
        ],
    }
    if profile == 'polymetrix':
        summary['holds'].append('Source standard deviation/reliability/count fields are curator metadata, '
                                'not verified specimen SD, independent n or measurement quality.')
    else:
        summary['holds'].append('Calculated density/modulus are separate from experimental columns; '
                                'compression and tension results must stay separate.')
    return summary, inventory


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', choices=tuple(PINS), required=True)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    summary, inventory = inspect(args.source.read_bytes(), args.profile)
    # Refuse existing destinations; an interrupted run cannot masquerade as a new audit.
    args.output_dir.mkdir(parents=True, exist_ok=False)
    payload = encode(inventory)
    (args.output_dir / 'held-records.json').write_bytes(payload)
    summary['held_records_sha256'] = hashlib.sha256(payload).hexdigest()
    (args.output_dir / 'inventory.json').write_bytes(encode(summary))
    print(json.dumps({k: summary[k] for k in ('profile', 'csv_data_records',
                      'literal_identity_strings', 'admitted_increment')}, indent=2))


if __name__ == '__main__':
    main()
