"""Extract selected density facts from retained primary XML; never edit native tables."""
import argparse
import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path

SOURCE_SHA256 = '4e0c1a91a9ae26d814576961a3805f9371b46498d4861fb578e7a413bb4c726d'
SOURCE_ID = 'ivdre_2024_lpo_rigid_pur'


def text(node):
    return ' '.join(''.join(node.itertext()).split())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--xml', type=Path, required=True)
    args = parser.parse_args()
    raw = args.xml.read_bytes()
    if hashlib.sha256(raw).hexdigest() != SOURCE_SHA256:
        raise ValueError('Unreviewed XML bytes')
    article = ET.fromstring(raw)
    table = next(t for t in article.findall('.//table-wrap') if t.get('id') == 'polymers-16-00942-t010')
    header = [text(c) for c in table.find('.//thead/tr')]
    labels = [c for c in header if c]
    row = next(r for r in table.findall('.//tbody/tr') if text(r[0]).startswith('Apparent density'))
    values = [text(c) for c in row][1:]
    if len(labels) != 6 or len(values) != 6:
        raise ValueError('Unexpected table layout')
    densities = dict(zip(labels, values))
    root = next(p for p in Path(__file__).resolve().parents if (p / 'materials_boundaries/data').is_dir())
    table_path = root / 'materials_boundaries/data/reference_properties.json'
    records = json.loads(table_path.read_text(encoding='utf-8'))['records']
    selected = {r['id']: r for r in records if r['source_id'] == SOURCE_ID}
    if len(selected) != 4:
        raise ValueError('Native source selection changed')
    result = []
    for rid, record in selected.items():
        label = next(label for label in labels if label.lower().replace('-', '') in rid)
        if record['reported_value']['number'] != densities[label]:
            raise ValueError('Native density mismatch: ' + rid)
        if record['reported_value']['unit_code'] != 'kg/m^3':
            raise ValueError('Unexpected unit: ' + rid)
        if record['uncertainty'] is not None or record['sample_count']['value'] is not None:
            raise ValueError('Unexpected density statistics: ' + rid)
        result.append({'property_id': rid, 'source_label': label,
                       'density_number': densities[label], 'unit_code': 'kg/m^3'})
    print(json.dumps({'schema': 'polymer-pur-density-source-comparison/1',
                      'xml_sha256': SOURCE_SHA256, 'xml_bytes': len(raw),
                      'native_properties_sha256': hashlib.sha256(table_path.read_bytes()).hexdigest(),
                      'matched_native_records': result, 'density_statistics_inferred': False,
                      'scope': 'Selected density row and native scalar fields only; not scientific review'}, indent=2))


if __name__ == '__main__':
    main()
