"""Read retained inputs and compare Table 2 with independent Decimal arithmetic.

Never import or execute the source plotting script. This is a diagnostic, not
an admission gate or a substitute for source review. Original values stay intact.
"""
import argparse
import ast
import csv
from decimal import Decimal, localcontext
import hashlib
import io
import json
from pathlib import Path
import re
import zipfile


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence-dir', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    facts_path = Path(__file__).with_name('TABLE2_SOURCE_FACTS_R1.json')
    facts = json.loads(facts_path.read_bytes())
    evidence = args.evidence_dir
    code = evidence / 'Python_code_plotting.txt'
    archive = evidence / 'CSVs.zip'
    assert digest(code) == '0ac624ef38dd109c94da3acafa411425252b6826aaae700149081f0d7f6fee0c'
    assert digest(archive) == '298d4f43003f39a47feced9bc584f43eee0276f26d869675ef0d0e5371842b75'
    assignments, labels = {}, {}
    for number, line in enumerate(code.read_text(encoding='utf-8-sig').splitlines(), 1):
        match = re.match(r"data(\d+) = pd.read_csv\(path \+'([^']+)'", line)
        if match:
            key = int(match[1])
            assert key not in assignments
            assignments[key] = ('CSVs/' + match[2], number)
        stripped = line.strip().lstrip('#').strip()
        if stripped.startswith('polynomial_fit(data'):
            # Parse a single call as inert syntax; never compile or evaluate it.
            call = ast.parse(stripped, mode='eval').body
            if not isinstance(call, ast.Call):
                raise ValueError('Expected a static call')
            variables = tuple(int(node.id.removeprefix('data')) for node in call.args[:3])
            label = call.args[-1]
            if isinstance(label, ast.Constant) and isinstance(label.value, str):
                labels.setdefault(variables, []).append({'line': number, 'label': label.value})
    assert set(assignments) == set(range(1, 121))
    # Article Table 2 order differs from plotting-code assignment order.
    first_variables = [1, 13, 49, 7, 19, 55, 25, 37, 31, 43, 61, 67,
                       115, 73, 79, 85, 91, 97, 103, 109]
    assert len(first_variables) == len(facts['row_data']) == 20
    samples, groups = {}, []
    with zipfile.ZipFile(archive) as source:
        for key, (name, line) in assignments.items():
            intended_name = name
            if name not in source.namelist():
                matches = [item for item in source.namelist() if item.casefold() == name.casefold()]
                if len(matches) != 1:
                    raise ValueError('Missing or ambiguous source path: ' + name)
                name = matches[0]
            raw = source.read(name)
            rows = list(csv.reader(io.StringIO(raw.decode('utf-8-sig'))))
            assert rows[5] in [
                ['Time (s)', 'Crosshead (mm)', 'Load (kN)', 'Extensometer (mm/mm)', 'Stress (MPa)'],
                ['Time (min)', 'Crosshead (mm)', 'Load (kN)', 'Extensometer (mm/mm)', 'Stress (MPa)']]
            values = [[Decimal(cell) for cell in row] for row in rows[7:] if row]
            assert len(values) > 6 and all(len(row) == 5 for row in values)
            upper = min(range(len(values)), key=lambda i: abs(values[i][3] - Decimal('0.0025')))
            lower = 6
            delta = values[upper][3] - values[lower][3]
            if delta == 0:
                raise ValueError('Zero strain interval: ' + name)
            modulus = (values[upper][4] - values[lower][4]) / delta
            samples[key] = {'source_variable': 'data' + str(key), 'file': name,
                            'source_code_path': intended_name,
                            'path_case_difference': intended_name != name,
                            'file_sha256': hashlib.sha256(raw).hexdigest(),
                            'assignment_line': line, 'observations': len(values),
                            'time_unit_literal': rows[5][0],
                            'lower_index': lower, 'upper_index': upper,
                            'lower_strain': str(values[lower][3]), 'upper_strain': str(values[upper][3]),
                            'modulus_mpa': str(modulus),
                            'peak_stress_mpa': str(max(row[4] for row in values))}
    for row, first in zip(facts['row_data'], first_variables):
        for phase, offset in [('non_weathered', 0), ('weathered', 3)]:
            keys = tuple(range(first + offset, first + offset + 3))
            assert keys in labels, keys
            comparisons = {}
            for field, channel in [('modulus_mpa', 'modulus_mpa'),
                                   ('tensile_strength_mpa', 'peak_stress_mpa')]:
                values = [Decimal(samples[k][channel]) for k in keys]
                mean = sum(values) / Decimal(3)
                sd = (sum((value - mean)**2 for value in values) / Decimal(2)).sqrt()
                reported = row[phase][field]
                comparisons[field] = {}
                for statistic, computed in [('reported_mean', mean), ('reported_sample_sd', sd)]:
                    literal = reported[statistic]
                    half_last_place = Decimal(1).scaleb(Decimal(literal).as_tuple().exponent) / 2
                    difference = computed - Decimal(literal)
                    comparisons[field][statistic] = {
                        'source_table2_value': literal, 'independent_csv_diagnostic': str(computed),
                        'difference': str(difference), 'half_last_place': str(half_last_place),
                        'within_source_rounding_interval': abs(difference) <= half_last_place}
            groups.append({'source_sample_label': row['source_sample_label'], 'phase': phase,
                           'source_plot_labels': labels[keys],
                           'samples': [samples[k] for k in keys], 'comparisons': comparisons})
    checks = [stat for group in groups for channel in group['comparisons'].values()
              for stat in channel.values()]
    result = {'schema': 'polymer-table2-csv-diagnostic/1',
              'status': 'diagnostic_only_not_admission_or_scientific_validation',
              'script_sha256': digest(Path(__file__)), 'table2_facts_sha256': digest(facts_path),
              'source_code_sha256': digest(code), 'source_zip_sha256': digest(archive),
              'source_code_executed': False, 'selected_csv_files': len(samples),
              'groups': groups, 'summary': {'comparisons': len(checks),
              'within_rounding': sum(stat['within_source_rounding_interval'] for stat in checks),
              'outside_rounding': sum(not stat['within_source_rounding_interval'] for stat in checks)},
              'limitations': ['Commented source calls document intended label mapping, not proof of executed code or actual specimen orientation.',
                              'Do not replace published values with these diagnostics.',
                              'Results PDF first-specimen footnote remains a separate channel discrepancy.',
                              'Original_01 archival file is excluded by the source assignment; not an independent specimen.',
                              'Table row to code group association is curated and requires independent review.']}
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps(result['summary']))


if __name__ == '__main__':
    with localcontext() as context:
        context.prec = 40
        main()
