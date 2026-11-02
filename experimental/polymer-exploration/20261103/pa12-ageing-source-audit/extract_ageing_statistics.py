"""Extract sparse Table 6-8 facts and screen conventional CV consistency.

No values are repaired. Display-rounding compatibility is a conditional numeric
diagnostic, not source admission, experimental validation or a statistical test.
"""
import argparse
from decimal import Decimal, localcontext
import hashlib
import json
from pathlib import Path
from xml.etree import ElementTree as ET


def text(node):
    return ' '.join(''.join(node.itertext()).split())


def rounding_interval(literal):
    number = Decimal(literal.rstrip('%'))
    half = Decimal(1).scaleb(number.as_tuple().exponent) / 2
    return number-half, number+half


def consistency(mean, sd, cv):
    m_low, m_high = rounding_interval(mean)
    s_low, s_high = rounding_interval(sd)
    c_low, c_high = rounding_interval(cv)
    assert m_low > 0 and s_low >= 0
    predicted_low, predicted_high = 100*s_low/m_high, 100*s_high/m_low
    return {
        'assumption': 'Conventional CV=100*SD/mean on the same group; article table labels CV but inspected text does not define its computation.',
        'rounding_policy': 'Closed half-last-place envelopes for all displayed decimals; conservative boundary treatment.',
        'mean_interval': [str(m_low), str(m_high)],
        'sd_interval': [str(s_low), str(s_high)],
        'reported_cv_interval': [str(c_low), str(c_high)],
        'predicted_cv_percent_interval': [str(predicted_low), str(predicted_high)],
        'intervals_overlap': max(predicted_low, c_low) <= min(predicted_high, c_high),
        'interpretation': 'Conditional arithmetic screen only; do not infer which reported statistic is correct or replace it.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--xml', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    raw = args.xml.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    assert digest == '4d930d221c67d38199460f1f80b86a2a724a0b2986a77e09081172d5a83c42d7'
    root = ET.fromstring(raw)
    groups = []
    for suffix in ('006', '007', '008'):
        table_id = 'materials-18-04478-t'+suffix
        table = next(t for t in root.findall('.//table-wrap') if t.get('id') == table_id)
        rows = table.findall('.//tr')
        assert [text(c) for c in rows[0]][:3] == ['Technology', 'Post-Processing', 'Ageing Test']
        assert [text(c) for c in rows[1]][3:] == ['Mean', 'Std', 'CV'] * 3
        assert len(rows) == 8
        technology, treatment = None, None
        for row_index, row in enumerate(rows[2:], 1):
            values = [text(c) for c in row]
            assert len(values) == 12
            if values[0]:
                technology = values[0]
                treatment = values[1]
            elif values[1]:
                treatment = values[1]
            assert technology in ('SLS', 'HP MJF') and treatment
            condition = values[2]
            assert condition in ('Reference', '1S—6 months', '2S—12 months')
            measures = {}
            for start, quantity, unit in [(3, 'tensile_strength', 'MPa'),
                                          (6, 'source_youngs_modulus', 'GPa'),
                                          (9, 'elongation_at_break', 'percent')]:
                mean, sd, cv = values[start:start+3]
                assert all(Decimal(value.rstrip('%')) > 0 for value in (mean, sd, cv))
                measures[quantity] = {'reported_mean_literal': mean,
                                     'reported_sd_literal': sd,
                                     'reported_cv_literal': cv,
                                     'quantity_unit': unit,
                                     'cv_unit_interpretation': 'percent under conventional CV assumption',
                                     'conditional_cv_check': consistency(mean, sd, cv)}
            groups.append({'table_id': table_id, 'source_body_row': row_index,
                           'technology_literal': technology,
                           'treatment_literal': treatment,
                           'ageing_label_literal': condition,
                           'reported_n': 6,
                           'n_locator': 'sec2dot2-materials-18-04478 and Table5',
                           'reported_elapsed_chamber_hours': {'Reference': None,
                                                              '1S—6 months': '375',
                                                              '2S—12 months': '750'}[condition],
                           'reference_note': 'Reference means before accelerated ageing; not a virgin/unprocessed or moisture-equilibrated certification.',
                           'statistics': measures})
    all_measures = [m for g in groups for m in g['statistics'].values()]
    assert len(groups) == 18 and len(all_measures) == 54
    selected = next(g for g in groups if g['table_id'].endswith('007') and
                    g['technology_literal'] == 'SLS' and g['ageing_label_literal'] == 'Reference')
    assert selected['statistics']['tensile_strength']['reported_mean_literal'] == '43.72'
    assert selected['statistics']['tensile_strength']['conditional_cv_check']['intervals_overlap']
    assert not selected['statistics']['source_youngs_modulus']['conditional_cv_check']['intervals_overlap']
    result = {'schema': 'polymer-pa12-ageing-source-statistics/1',
              'stage': 'source_facts_and_conditional_screen_not_native_candidate',
              'source_doi': '10.3390/ma18194478', 'xml_sha256': digest,
              'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'source_groups': groups,
              'summary': {'groups': 18, 'quantity_summaries': 54,
                          'cv_interval_compatible': sum(m['conditional_cv_check']['intervals_overlap'] for m in all_measures),
                          'cv_interval_incompatible_under_stated_assumption': sum(not m['conditional_cv_check']['intervals_overlap'] for m in all_measures)},
              'limits': ['No new native records or identity claims.',
                         'Raw specimens were not reanalyzed; source summary strings are preserved.',
                         'Manufacturer-derived Tables1-4 are not imported as original measured results.',
                         'Treatment-label inconsistencies and simulated ageing-equivalence remain separately qualified.',
                         'No confidence intervals, engineering allowables, clinical suitability or natural lifetime validation.']}
    with args.output.open('x', encoding='utf-8') as output:
        json.dump(result, output, ensure_ascii=False, indent=2)
        output.write('\n')
    print(json.dumps(result['summary']))


if __name__ == '__main__':
    with localcontext() as context:
        context.prec = 40
        main()
