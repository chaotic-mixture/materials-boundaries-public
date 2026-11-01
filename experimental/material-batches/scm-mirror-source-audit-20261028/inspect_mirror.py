"""Inspect an unverified third-party workbook mirror without executing formulas."""
from collections import Counter
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET

CACHE = Path('F:/材料边界/growth-source-cache/scm-concrete-1456')
SOURCE = CACHE / 'mendeley_scm_based_concrete.github-mirror.xlsx'
SHA = '905abfc3c02e036b21fec9ac161e3519b940220b14780036b567b8f1da3a8f28'
NS = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}


def inspect(raw):
    if sha256(raw).hexdigest() != SHA:
        raise ValueError('Different mirror workbook')
    from io import BytesIO
    with ZipFile(BytesIO(raw)) as archive:
        if sum(i.file_size for i in archive.infolist()) > 50_000_000:
            raise ValueError('Unexpected expanded workbook size')
        strings_root = ET.fromstring(archive.read('xl/sharedStrings.xml'))
        if strings_root.findall('.//s:rPh', NS):
            raise ValueError('Phonetic rich strings require explicit handling')
        strings = [''.join(si.itertext()) for si in strings_root.findall('s:si', NS)]
        sheet = ET.fromstring(archive.read('xl/worksheets/sheet1.xml'))
        cells = {}
        for row in sheet.findall('s:sheetData/s:row', NS):
            for cell in row:
                address = cell.attrib['r']
                if address in cells:
                    raise ValueError('Repeated worksheet address')
                value = cell.find('s:v', NS)
                text = None if value is None else value.text
                kind = cell.attrib.get('t', 'n')
                if kind == 's' and text is not None:
                    text = strings[int(text)]
                elif kind == 'inlineStr':
                    text = ''.join(cell.find('s:is', NS).itertext())
                formula = cell.find('s:f', NS)
                cells[address] = {'value': text, 'type': kind,
                                  'formula': None if formula is None else formula.text,
                                  'formula_present': formula is not None,
                                  'style_index': cell.attrib.get('s')}
        rows = sorted({int(address.lstrip('ABCDEFGHIJKLMNOPQRSTUVWXYZ')) for address in cells})
        data_rows = [i for i in rows if i > 1 and cells.get('A' + str(i), {}).get('value') not in [None, '']]
        non_reference_prefixed = [i for i in data_rows if not cells['A' + str(i)]['value'].startswith('R')]
        headers = {column: cells.get(column + '1', {}).get('value') for column in 'ABCDEFGHIJKLMNOPQRSTUVWXY'}
        formulas = Counter(address.rstrip('0123456789') for address, c in cells.items() if c['formula_present'])
        property_stats = {}
        for column, label in [('J', 'cylinder_compressive_strength'), ('K', 'splitting_tensile_strength'),
                              ('L', 'flexural_strength'), ('M', 'elastic_modulus')]:
            count = Counter()
            for i in data_rows:
                c = cells.get(column + str(i), {})
                value = c.get('value')
                count['formula_cells'] += bool(c.get('formula_present'))
                if value in [None, '']:
                    count['blank'] += 1
                    continue
                try:
                    number = Decimal(value)
                except InvalidOperation:
                    count['non_numeric'] += 1
                    continue
                if not number.is_finite():
                    count['nonfinite'] += 1
                elif number == -1:
                    count['missing_minus_one'] += 1
                elif number > 0:
                    count['positive_cached_numeric'] += 1
                    count['positive_formula_cached'] += bool(c.get('formula_present'))
                    count['positive_nonformula_cell'] += not c.get('formula_present')
                else:
                    count['other_nonpositive'] += 1
            property_stats[label] = dict(count)
        recipes, rejected = {}, Counter()
        for i in data_rows:
            try:
                values = [Decimal(cells[column + str(i)]['value']) for column in 'BCDEFGHI']
                if any(not v.is_finite() or v < 0 for v in values):
                    raise ValueError('Negative/nonfinite ingredient')
            except (KeyError, TypeError, InvalidOperation, ValueError) as error:
                rejected[type(error).__name__] += 1
                continue
            key = tuple(values)
            recipes.setdefault(key, []).append(i)
        explicit_references = {i: cells.get('Y' + str(i), {}).get('value') for i in data_rows
                               if cells.get('Y' + str(i), {}).get('value') not in [None, '']}
        merge_ranges = [c.attrib['ref'] for c in sheet.findall('s:mergeCells/s:mergeCell', NS)]
        return {
            'schema': 'scm-third-party-mirror-raw-workbook-audit/1',
            'status': 'mirror_only_author_version_equivalence_and_scientific_review_pending',
            'mirror_sha256': SHA, 'source_asset_bundled_in_repository': False,
            'worksheet': 'xl/worksheets/sheet1.xml', 'xml_row_elements': len(sheet.findall('s:sheetData/s:row', NS)),
            'mix_id_rows': len(data_rows), 'distinct_mix_ids': len({cells['A' + str(i)]['value'] for i in data_rows}),
            'mix_ids_without_R_prefix': [{'worksheet_row': i, 'mix_id': cells['A' + str(i)]['value']} for i in non_reference_prefixed],
            'headers_as_stored': headers, 'formula_cells_total': sum(formulas.values()), 'formula_cells_by_column': dict(formulas),
            'formulas_executed': False, 'cached_values_recalculated': False,
            'property_cell_stats': property_stats,
            'nonnegative_eight_ingredient_row_count': sum(map(len, recipes.values())),
            'literal_numeric_recipe_vectors': len(recipes), 'recipe_rows_held': dict(rejected),
            'recipe_vector_scope': 'Eight per-volume ingredient numbers only; not canonical chemical identity or verified raw-material equivalence.',
            'explicit_reference_cells': len(explicit_references), 'distinct_explicit_reference_strings': len(set(explicit_references.values())),
            'reference_merge_ranges': [r for r in merge_ranges if r.startswith('Y')],
            'reference_blanks_forward_filled': False,
            'limits': ['Official author-file manifest/byte equivalence not verified; mirror is not promoted to an official source.',
                       'Cached formula values may be conversions; non-formula cells also do not prove direct measurement.',
                       'Raw XML numeric tokens include floating artifacts; display formats and original-paper precision remain unverified.',
                       'Missing -1 properties are excluded from positive statistics; zero ingredients mean absence per author article, not missing properties.',
                       'No density is inferred by summing ingredient kg/m3. Unsupported strength types need separate contracts.',
                       'Row IDs, exact ingredient vectors and literature references do not establish admitted distinct materials.'],
            'canonical_material_identity_count': None, 'admitted_increment': 0,
        }


if __name__ == '__main__':
    result = inspect(SOURCE.read_bytes())
    out = Path(__file__).with_name('mirror-audit.json')
    raw = (json.dumps(result, ensure_ascii=False, indent=2) + '\n').encode('utf8')
    if out.exists() and out.read_bytes() != raw:
        raise ValueError('Refuse different frozen audit')
    out.write_bytes(raw)
    print(json.dumps({k: result[k] for k in ['mix_id_rows', 'distinct_mix_ids', 'literal_numeric_recipe_vectors',
                                          'formula_cells_total', 'formula_cells_by_column', 'property_cell_stats', 'admitted_increment']}))
