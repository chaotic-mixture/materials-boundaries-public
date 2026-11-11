"""Energy-specific semantics for the isolated preview, not production validation."""
from decimal import Decimal
import re

UNITS = {'J/cm^3': {'J/cm^3', 'J/cm³', 'J/cm3'},
         'MJ/m^3': {'MJ/m^3', 'MJ/m³', 'MJ/m3'},
         'J/m^3': {'J/m^3', 'J/m³', 'J/m3'}}


def validate_work_semantics(prop):
    """Call only after preview schema validation; generic graph gates remain separate."""
    from materials_boundaries.material_references import _numeric_token_matches
    def value_check(value):
        if value['unit_code'] not in UNITS or value['unit_text'].strip() not in UNITS[value['unit_code']]:
            raise ValueError('Work unit role or literal scale mismatch')
        kind = value.get('kind', 'scalar')
        numbers = [value['lower'], value['upper']] if kind == 'interval' else [value['number']]
        if any(Decimal(number) < 0 for number in numbers):
            raise ValueError('Work and amplitude must be nonnegative')
        text = value['value_text'].strip()
        if kind == 'interval':
            pieces = re.split(r'\s*(?:–|—|-|\bto\b)\s*', text)
            if Decimal(numbers[0]) >= Decimal(numbers[1]) or len(pieces) != 2 or not all(_numeric_token_matches(t, n) for t, n in zip(pieces, numbers)):
                raise ValueError('Interval must preserve source endpoints/precision')
        elif kind == 'comparison':
            match = re.fullmatch(r'(>=|<=|>|<|≥|≤)\s*(.+)', text)
            if not match or {'≥': '>=', '≤': '<='}.get(match[1], match[1]) != value['operator'] or not _numeric_token_matches(match[2], numbers[0]):
                raise ValueError('Comparison must preserve source operator/precision')
        elif not _numeric_token_matches(text, numbers[0]):
            raise ValueError('Scalar must preserve source precision')
    if prop['quantity'] != 'volumetric_tensile_work_to_break':
        raise ValueError('Wrong quantity for preview validator')
    value_check(prop['reported_value'])
    basis = prop['work_reference_basis']
    if basis['status'] == 'reported':
        if not any(item['source_id'] == prop['source_id'] and item['url'] == prop['source_document']['url'] and 'condition' in item['supports'] for item in basis['evidence']):
            raise ValueError('Reported work basis needs primary document condition evidence')
    elif basis['status'] not in ('not_reported_in_inspected_source', 'not_verified') or not basis.get('notes'):
        raise ValueError('Unknown reference basis must remain explicit and relevant')
    uncertainty = prop['uncertainty']
    if uncertainty and uncertainty['type'] != 'reported_measures':
        value_check(uncertainty)
        if uncertainty['unit_code'] != prop['reported_value']['unit_code']:
            raise ValueError('Absolute amplitude must retain exact central unit code')


def basis_key(prop):
    """No new coordinates from unknown status or explanatory wording."""
    fact = prop['work_reference_basis']
    return ('reported', fact['text']) if fact['status'] == 'reported' else ('unknown', None)
