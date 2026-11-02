"""Compare retained results PDF, article facts and existing CSV diagnostics.

Requires pypdf for read-only extraction. Page/group order is an explicit curated
crosswalk, not an inferred specimen identity. Never execute source plotting code.
"""
import argparse
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
from pathlib import Path
import re

from pypdf import PdfReader
import pypdf


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compare(diagnostic, source_literal):
    source = Decimal(source_literal.replace(',', '.'))
    diagnostic = Decimal(diagnostic)
    tolerance = Decimal(1).scaleb(source.as_tuple().exponent) / 2
    return {'source_literal': source_literal, 'diagnostic': str(diagnostic),
            'difference': str(diagnostic - source),
            'half_last_place': str(tolerance),
            'within_rounding_interval': abs(diagnostic - source) <= tolerance}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence-dir', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    packet = Path(__file__).parent
    pdf = args.evidence_dir / 'Tensile_test_results.pdf'
    diagnostic_path = args.evidence_dir / 'table2-csv-diagnostic-r1.json'
    assert sha(pdf) == '7a79a905bd7dd5e5fd82add586d09197282e465f40692a31353c526ef09fcefd'
    bindings = json.loads((packet / 'REVIEW_INPUTS_R1.json').read_bytes())
    assert sha(diagnostic_path) == bindings['external_files_sha256'][str(diagnostic_path)]
    diagnostics = json.loads(diagnostic_path.read_bytes())
    by_group = {(g['source_sample_label'], g['phase']): g for g in diagnostics['groups']}
    facts = json.loads((packet / 'TABLE2_SOURCE_FACTS_R1.json').read_bytes())
    assert sha(packet / 'TABLE2_SOURCE_FACTS_R1.json') == diagnostics['table2_facts_sha256']
    reader = PdfReader(pdf)
    # Table2 1-based row numbers per results page, each before then after weathering.
    mapping = {2: [1, 4], 4: [2, 5], 6: [7, 9], 8: [8, 10], 10: [3, 6],
               12: [11, 12], 14: [14], 16: [15], 18: [16, 17],
               20: [18], 22: [19], 24: [20], 26: [13]}
    number = r'(-?\d+(?:,\d+)?)'
    specimen_pattern = re.compile(r'^\s*(?:Sample\s+\d+\s*\*?\s+)?' +
                                  r'\s+'.join([number] * 6) + r'\s*$')
    summary_pattern = re.compile(r'^\s*' + r'\s+'.join([number] * 4) + r'\s*$')
    groups = []
    for page, indices in mapping.items():
        lines = reader.pages[page-1].extract_text(extraction_mode='layout').splitlines()
        samples = [(i+1, m.groups()) for i, line in enumerate(lines)
                   if (m := specimen_pattern.match(line))]
        summaries = [(i+1, m.groups()) for i, line in enumerate(lines)
                     if (m := summary_pattern.match(line))]
        assert len(samples) == len(indices) * 6, (page, len(samples))
        assert len(summaries) == len(indices) * 4, (page, len(summaries))
        for group_index, row_index in enumerate(indices):
            row = facts['row_data'][row_index-1]
            for phase_index, phase in enumerate(['non_weathered', 'weathered']):
                csv_group = by_group[row['source_sample_label'], phase]
                index = group_index * 2 + phase_index
                individual = []
                for j, sample in enumerate(csv_group['samples']):
                    line, values = samples[index*3+j]
                    individual.append({'source_variable': sample['source_variable'],
                                       'csv_file': sample['file'], 'pdf_text_line': line,
                                       'peak_stress_mpa': compare(sample['peak_stress_mpa'], values[2]),
                                       'modulus_mpa': compare(sample['modulus_mpa'], values[5])})
                aggregate = {}
                for channel, column in [('tensile_strength_mpa', 0), ('modulus_mpa', 3)]:
                    aggregate[channel] = {}
                    for j, stat in enumerate(['reported_mean', 'reported_sample_sd']):
                        line, values = summaries[index*2+j]
                        literal = values[column]
                        article = row[phase][channel][stat]
                        from_csv = csv_group['comparisons'][channel][stat]['independent_csv_diagnostic']
                        comparison = compare(from_csv, literal)
                        comparison.update(pdf_text_line=line, article_literal=article,
                                          results_pdf_rounds_to_article=(
                            Decimal(literal.replace(',', '.')).quantize(
                                Decimal(1).scaleb(Decimal(article).as_tuple().exponent),
                                rounding=ROUND_HALF_UP) == Decimal(article)))
                        aggregate[channel][stat] = comparison
                groups.append({'sample_label': row['source_sample_label'], 'phase': phase,
                               'results_pdf_page': page, 'specimens': individual,
                               'aggregate_comparisons': aggregate})
    individual = [v for g in groups for s in g['specimens']
                  for k, v in s.items() if k in ('peak_stress_mpa', 'modulus_mpa')]
    aggregate = [v for g in groups for c in g['aggregate_comparisons'].values() for v in c.values()]
    assert len(groups) == 40 and len(individual) == 240 and len(aggregate) == 160
    result = {'schema': 'polymer-results-pdf-channel-diagnostic/1',
              'scope': 'Numerical correspondence only; preserve source contradictions and footnotes.',
              'source_pdf_sha256': sha(pdf), 'csv_diagnostic_sha256': sha(diagnostic_path),
              'script_sha256': sha(Path(__file__)), 'pypdf_version': pypdf.__version__,
              'source_plotting_code_executed': False, 'groups': groups,
              'summary': {'groups': 40, 'individual_comparisons': 240,
                          'individual_outside_pdf_rounding': sum(not v['within_rounding_interval'] for v in individual),
                          'aggregate_comparisons': 160,
                          'aggregate_outside_pdf_rounding': sum(not v['within_rounding_interval'] for v in aggregate),
                          'results_pdf_to_article_rounding_mismatches': sum(not v['results_pdf_rounds_to_article'] for v in aggregate)},
              'limitations': ['No independent scientific validation or admission.',
                              'Page/group and row/specimen order require visual/source cross-check.',
                              'Matching values do not prove actual apparatus calibration, batch independence or standard compliance.',
                              'Original reported values and unresolved footnotes remain unchanged.']}
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps(result['summary']))


if __name__ == '__main__':
    main()
