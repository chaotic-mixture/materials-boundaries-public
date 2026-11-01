"""Inventory pinned COD metadata and a 50-file feasibility probe; no admission."""
import argparse
from collections import defaultdict
from fractions import Fraction
from functools import reduce
from math import gcd, lcm
import hashlib
import io
import json
from pathlib import Path
import re
import zipfile

METADATA_SHA256 = 'd193614fafc30fa1ace4e83f9a308f780a5e049c324cbbd1b15852c8dadcca07'
ARCHIVE_SHA256 = '20b8db98cc4a5f133a5c95ea3d3272f52a90f915d41fa9c73a05ee533577c4ec'


def formula_ratio_key(formula):
    """Exact rational coefficient grouping only, not chemical identity resolution."""
    parts = []
    for token in formula.strip().strip('-').strip().split():
        match = re.fullmatch(r'([A-Z][a-z]?)([0-9]+(?:\.[0-9]+)?)?', token)
        if match is None:
            raise ValueError('unsupported formula token')
        coefficient = Fraction(match[2] or '1')
        if coefficient <= 0:
            raise ValueError('nonpositive formula coefficient')
        parts.append((match[1], coefficient))
    if not parts or len({name for name, n in parts}) != len(parts):
        raise ValueError('empty formula or repeated element')
    denominator = lcm(*(n.denominator for name, n in parts))
    integers = [int(n * denominator) for name, n in parts]
    common = reduce(gcd, integers)
    return tuple(sorted((name, n // common) for (name, _), n in zip(parts, integers)))


def inspect(metadata_bytes, archive_bytes):
    if hashlib.sha256(metadata_bytes).hexdigest() != METADATA_SHA256:
        raise ValueError('COD metadata checksum mismatch')
    if hashlib.sha256(archive_bytes).hexdigest() != ARCHIVE_SHA256:
        raise ValueError('COD probe archive checksum mismatch')
    rows = json.loads(metadata_bytes)
    index = {r['file']: r for r in rows}
    if len(index) != len(rows):
        raise ValueError('repeated COD record ID')
    groups = defaultdict(list)
    for row in rows:
        groups[formula_ratio_key(row['formula'])].append(row['file'])
    probes = []
    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
        names = archive.namelist()
        if len(names) != 50 or len(set(names)) != 50:
            raise ValueError('unexpected probe archive membership')
        for name in names:
            if not re.fullmatch(r'[0-9]{7}\.cif', name) or name[:-4] not in index:
                raise ValueError('probe member outside metadata selection')
            raw = archive.read(name)
            text = raw.decode('utf8')
            revision = re.search(r'^#\$Revision:\s*([0-9]+)\s*\$', text, re.M)
            density_lines = [line for line in text.splitlines()
                             if re.match(r'^_exptl_crystal_density_(?:diffrn|meas)\s', line, re.I)]
            row = index[name[:-4]]
            probes.append({'cod_id': name[:-4], 'cif_sha256': hashlib.sha256(raw).hexdigest(),
                           'metadata_svnrevision': row['svnrevision'],
                           'cif_header_revision': revision[1] if revision else None,
                           'revision_matches': bool(revision and revision[1] == row['svnrevision']),
                           'source_formula': row['formula'],
                           'literal_density_tag_lines': density_lines,
                           'status': 'held_pending_semantic_cif_and_source_review'})
    return {
        'schema': 'cod-source-probe/1',
        'query': 'https://www.crystallography.net/cod/result?id=1%25&el1=O&nel1=C&strictmax=3&format=json',
        'metadata_sha256': METADATA_SHA256, 'archive_sha256': ARCHIVE_SHA256,
        'metadata_records': len(rows), 'literal_formula_strings': len({r['formula'] for r in rows}),
        'exact_rational_formula_ratio_groups': len(groups),
        'canonical_material_identity_count': None, 'baseline_overlap_count': None,
        'probe_cif_files': len(probes),
        'probe_files_with_density_tag_lines': sum(bool(p['literal_density_tag_lines']) for p in probes),
        'revision_mismatches': [p['cod_id'] for p in probes if not p['revision_matches']],
        'admitted_increment': 0,
        'scope': 'Rational grouping screens coefficient-scaled formulas; it does not prove material identity, '
                 'phase equivalence, exact composition, purity or category admission. Density-tag lines are '
                 'a lexical feasibility inventory, not parsed CIF quantities, verified units or approved measurements. '
                 'No missing density is reconstructed from unit-cell parameters.',
        'probes': probes,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--metadata', type=Path, required=True)
    p.add_argument('--archive', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    report = inspect(args.metadata.read_bytes(), args.archive.read_bytes())
    data = (json.dumps(report, ensure_ascii=False, indent=2) + '\n').encode('utf8')
    if args.output.exists():
        if args.output.read_bytes() != data:
            raise ValueError('refusing different existing probe report')
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(data)
    print(json.dumps({k: v for k, v in report.items() if k in ('metadata_records',
                     'exact_rational_formula_ratio_groups', 'probe_files_with_density_tag_lines',
                     'revision_mismatches', 'admitted_increment')}, indent=2))


if __name__ == '__main__':
    main()
