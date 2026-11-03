"""Read selected NR source facts without changing the catalogue."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

EXPECTED = '97eb8a1e73e57b6fc64fcf3b0be6603db3f8dcb5fa927570e91eb033f1018f69'


def text(element):
    return ' '.join(''.join(element.itertext()).split())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--xml', type=Path, required=True)
    args = parser.parse_args()
    raw = args.xml.read_bytes()
    if hashlib.sha256(raw).hexdigest() != EXPECTED:
        raise ValueError('Unreviewed source bytes')
    article = ET.fromstring(raw)
    tables = {text(t.find('label')).rstrip('.'): t for t in article.findall('.//table-wrap')}
    density = next(r for r in tables['Table 1'].findall('.//tbody/tr') if text(r[0]) == 'NR')
    assert text(density[1]) == '0.958 ± 0.006'
    modulus = []
    for row in tables['Table 4'].findall('.//tbody/tr'):
        match = re.fullmatch(r'(\d+\.\d+)\s*±\s*(\d+\.\d+)', text(row[1]))
        assert match, text(row[1])
        modulus.append({'source_label': text(row[0]), 'mean_MPa': match[1], 'SD_MPa': match[2],
                        'decision': 'source_fact_only_not_native_candidate',
                        'method': 'Slope over 100–200 percent strain, not initial Young modulus'})
    assert len(modulus) == 7
    root = next(p for p in Path(__file__).resolve().parents if (p / 'materials_boundaries/data').is_dir())
    properties = json.loads((root / 'materials_boundaries/data/reference_properties.json').read_bytes())['records']
    native = next(p for p in properties if p['id'] == 'refprop_smr10_bianchi2025_nr_mass_density')
    assert native['reported_value']['number'] == '0.958'
    assert native['uncertainty']['number'] == '0.006'
    assert native['sample_count']['value'] == 3
    assert native['uncertainty']['type'] == 'reported_plus_minus_unspecified'
    assert native['conditions']['conditioning']['status'] == 'not_reported_in_inspected_source'
    print(json.dumps({'schema':'nr-density-mechanical-readback/1','xml_sha256':EXPECTED,
          'xml_bytes':len(raw),'density_record_matches':native['id'],
          'density_plus_minus_statistic':'unspecified; mechanical mean/SD statement not transferred',
          'density_conditioning':'not_reported_in_inspected_source',
          'finite_strain_modulus_source_facts':modulus,
          'source_break_strain_header':text(tables['Table 4'].findall('.//thead/tr/th')[5]),
          'break_strain_unit_disposition':'Literal header retained; no percent or fraction conversion',
          'native_changes':0,'independent_scientific_review':False},indent=2))


if __name__ == '__main__':
    main()
