"""Build an unadmitted primary-source candidate; no network or runtime writes."""
from __future__ import annotations

import argparse
from copy import deepcopy
import csv
from decimal import Decimal
import hashlib
import io
import json
import re
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from materials_boundaries.material_references import validate_material_catalog

SOURCE = 'sanchez_2019_cast_al_mea'
DOI = '10.1038/s41598-019-43329-w'
URL = 'https://www.ebi.ac.uk/europepmc/webservices/rest/PMC6494811/fullTextXML'
XML_SHA256 = '9feae72296d930c220b99b57bf79047d9760911718ab007f6f95e2d3a6c0a8dc'
MPEA_SHA256 = 'c5504d93fd324d1be26cf814d0694ee9ee95578d68a0b38aba6813b939fa2c5d'
ROWS = (
    ('fe', 'Al65Cu5Fe5Mg5Si15Zn5', '3.08', '88.7', '04'),
    ('ni', 'Al65Cu5Mg5Ni5Si15Zn5', '3.15', '107.8', '17'),
    ('cr', 'Al70Cr5Cu5Mg5Si10Zn5', '3.06', '78.4', '03'),
    ('mn', 'Al70Cu5Mg5Mn5Si10Zn5', '2.98', '114.1', '02'),
    ('zr', 'Al70Cu5Mg5Si10Zn5Zr5', '3.06', '105.1', '27'),
)
SCOPE = ('Producer checked selected official XML tables, methods and article-specific license. '
         'No independent reviewer, original PDF inspection, PDF/XML equivalence check, '
         'scientific replication or raw-data reanalysis is claimed.')


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')


def evidence(locator, *supports):
    return [{'source_id': SOURCE, 'url': URL, 'locator': locator, 'supports': list(supports)}]


def fact(text=None, *, notes=None, locator='Methods, mechanical characterization', tag='condition', status=None):
    return {'status': status or ('reported' if text is not None else 'not_reported_in_inspected_source'),
            'text': text, 'evidence': evidence(locator, *(['method', 'condition'] if tag == 'method' else [tag])) if text is not None else [], 'notes': notes}


def source_facts(xml_bytes, mpea_bytes):
    if hashlib.sha256(xml_bytes).hexdigest() != XML_SHA256:
        raise ValueError('primary XML checksum mismatch')
    if hashlib.sha256(mpea_bytes).hexdigest() != MPEA_SHA256:
        raise ValueError('MPEA source checksum mismatch')
    tree = ET.fromstring(xml_bytes)
    paragraphs = {e.get('id'): ' '.join(e.itertext()) for e in tree.findall('.//p')}
    if 'standard deviations' not in paragraphs.get('Par25', ''):
        raise ValueError('source SD definition not verified')
    if 'as-cast state' not in paragraphs.get('Par31', ''):
        raise ValueError('source as-cast state not verified')
    if 'shrinkage porosity' not in paragraphs.get('Par14', ''):
        raise ValueError('source porosity description not verified')
    authors = [' '.join((n.findtext('given-names', ''), n.findtext('surname', ''))).strip()
               for n in tree.findall('.//contrib-group[@content-type="author"]/contrib/name')]
    license_text = ' '.join(tree.find('.//permissions').itertext())
    if 'Creative Commons Attribution 4.0 International License' not in license_text:
        raise ValueError('article-specific license not found')
    tables = {}
    for table in tree.findall('.//table-wrap'):
        tables[table.get('id')] = [[''.join(cell.itertext()) for cell in tr]
                                 for tr in table.findall('.//tr')]
    table1 = {r[0]: r for r in tables['Tab1'][1:]}
    table3 = {r[0]: r for r in tables['Tab3'][1:]}
    mpea = [r for r in csv.DictReader(io.StringIO(mpea_bytes.decode('utf-8-sig')))
            if r['REFERENCE: doi'] == DOI]
    if len(mpea) != 5:
        raise ValueError('unexpected MPEA reference-row count')
    result = []
    for suffix, label, density, modulus, pm in ROWS:
        row = table3[label]
        if row[1] != density or row[5].replace('\u2009', '') != modulus + '±' + pm:
            raise ValueError('selected source table cells differ')
        matches = [r for r in mpea if suffix.capitalize() + '0.077' in r['FORMULA']]
        if len(matches) != 1:
            raise ValueError('ambiguous MPEA/source linkage')
        compiled = matches[0]
        if compiled['PROPERTY: Exp. Density (g/cm$^3$)'] != density or compiled['PROPERTY: Exp. Young modulus (GPa)'] != modulus:
            raise ValueError('MPEA numerical cross-check differs')
        nominal = {element: Decimal(number) for element, number in re.findall(r'([A-Z][a-z]?)([0-9]+)', label)}
        expected_ratios = {element: (number / nominal['Al']).quantize(Decimal('0.001'))
                           for element, number in nominal.items()}
        compiled_ratios = {}
        for token in compiled['FORMULA'].split():
            match = re.fullmatch(r'([A-Z][a-z]?)([0-9]+(?:[.][0-9]+)?)', token)
            if match is None:
                raise ValueError('unsupported compiled ratio token')
            compiled_ratios[match[1]] = Decimal(match[2])
        mismatch = expected_ratios != compiled_ratios
        if mismatch != (suffix in {'cr', 'mn', 'zr'}):
            raise ValueError('unexpected primary/compiled composition comparison')
        result.append({'suffix': suffix, 'nominal_composition_at_percent_label': label,
                       'density_g_cm3': density, 'youngs_modulus_gpa': modulus,
                       'modulus_plus_minus_literal': row[5],
                       'measured_sem_eds_at_percent': dict(zip(tables['Tab1'][0][1:], table1[label][1:])),
                       'mpea_formula_literal': compiled['FORMULA'],
                       'original_nominal_ratios_relative_to_Al_rounded_3dp': {k: str(v) for k, v in expected_ratios.items()},
                       'mpea_formula_mismatch': mismatch})
    return authors, result


def build(xml_bytes, mpea_bytes):
    authors, rows = source_facts(xml_bytes, mpea_bytes)
    materials = {'schema_version': '1.0.0', 'identities': [], 'grades': [], 'records': []}
    properties = {'schema_version': '1.0.0', 'records': []}
    source = {
        'id': SOURCE, 'title': 'Design, Microstructure and Mechanical Properties of Cast Medium Entropy Aluminium Alloys',
        'authors': authors, 'year': 2019, 'doi': DOI,
        'urls': [URL, 'https://doi.org/' + DOI, 'https://creativecommons.org/licenses/by/4.0/'],
        'read_status': 'selected_official_archive_xml_tables_methods_and_rights_checked_by_producer',
        'license': {'status': 'explicit_reuse_license_verified', 'identifier': 'CC-BY-4.0'},
        'role': 'published_experimental_reference',
        'claim_notes': [
            'Scientific Reports 9, 6792 (2019). Copyright The Author(s) 2019; article-specific CC BY 4.0.',
            'Changes: selected original factual compositions, density and compressive modulus values structured with unknown conditions. No endorsement is implied.',
            'Selected original Tables 1 and 3 and methods have no separate restriction observed in the inspected XML. Source assets are not bundled.',
            'Three MPEA compiled composition labels conflict with original Al70/Si10 recipes; original nominal labels govern this candidate.',
        ],
        'provenance': {'curation_date': '2026-10-27', 'method': SCOPE},
        'bundled_content': 'selected_factual_reference_values_bibliographic_metadata_and_original_curation_only',
    }
    sources = {'schema_version': '1.0.0', 'records': [source]}
    document = {'url': URL, 'revision': 'Official Europe PMC XML of Scientific Reports 9, 6792 (2019); archive revision unspecified.',
                'inspected_on': '2026-10-27', 'sha256': XML_SHA256, 'hash_status': 'recorded',
                'hash_note': None, 'inspection_scope': SCOPE, 'inspection_status': 'selected_content_inspected'}
    for row in rows:
        suffix, label = row['suffix'], row['nominal_composition_at_percent_label']
        identity = 'mat_sanchez2019_al_mea_' + suffix
        state = 'state_sanchez2019_al_mea_' + suffix + '_cast'
        name = label + ' nominal at.% cast alloy (Sanchez 2019)'
        scope = ('Study-qualified nominal atomic-percent alloy recipe, not certified grade, exact lot purity or final composition. '
                 'Table 1 separately reports averaged SEM-EDS overall compositions including oxygen. '
                 'As-cast state and reported qualitative porosity remain source-qualified; density fluid and quantitative porosity are unknown.')
        materials['identities'].append({'id': identity, 'version': '1.0.0', 'category': 'metal',
            'name': name, 'names': dict.fromkeys(('en', 'zh', 'ja', 'de'), name), 'aliases': [],
            'identity_scope': scope + ' Nominal source recipe: ' + label + '.',
            'evidence': evidence('Table 1 nominal row ' + label + '; Table 3 same alloy row', 'material_identity')})
        state_facts = {key: fact(tag='state') for key in (
            'product_form', 'processing', 'temper_or_heat_treatment', 'conditioning',
            'composition_or_purity', 'reinforcement', 'porosity', 'orientation')}
        state_facts['product_form'] = fact('Cast ingots; exact density specimen geometry unspecified.', tag='state', locator='Methods, materials preparation and characterization')
        state_facts['processing'] = fact('Induction-melted and manually poured into steel moulds.', tag='state', locator='Methods, materials preparation')
        state_facts['temper_or_heat_treatment'] = fact('Studied in the as-cast state.', tag='state', locator='Discussion, Par31', notes='The proposed future study of standard aluminium heat treatments is not an applied treatment in this work.')
        if suffix in {'fe', 'mn', 'zr'}:
            image = {'fe': '2(a)', 'mn': '2(g)', 'zr': '2(i)'}[suffix]
            state_facts['porosity'] = fact('Shrinkage porosity observed in the reported microstructure, Figure ' + image + '.', tag='state', locator='Microstructure results, Par14; Figure ' + image, notes='Qualitative observation; no numeric pore fraction, correction or uniformity across specimens is inferred.')
        elif suffix == 'cr':
            state_facts['porosity'] = fact('Porosity was not detected in the Figure 2(e) field discussed by the authors.', tag='state', locator='Mechanical properties results, Par25; Figure 2(e)', notes='Finite reported image scope, not a measurement of globally zero porosity.')
        state_facts['composition_or_purity'] = fact('Nominal atomic-percent recipe ' + label + '; measured SEM-EDS at.% by element: ' + json.dumps(row['measured_sem_eds_at_percent'], ensure_ascii=False) + '.', tag='state', locator='Table 1, nominal and measured composition row ' + label, notes='Blank EDS cells remain unspecified, not analytically zero. Nominal recipe and measured composition remain distinct.')
        property_ids = []
        for quantity, value, unit in [('mass_density', row['density_g_cm3'], 'g/cm^3'), ('youngs_modulus', row['youngs_modulus_gpa'], 'GPa')]:
            mechanical = quantity == 'youngs_modulus'
            prop_id = 'refprop_sanchez2019_al_mea_' + suffix + '_' + quantity
            property_ids.append(prop_id)
            conditions = {k: fact() for k in ('temperature', 'test_standard', 'test_method', 'direction', 'conditioning', 'loading_rate')}
            conditions['temperature'] = fact('RT, qualitative room-temperature label in Table 3.', locator='Table 3 caption and Methods, mechanical characterization', notes='No numeric temperature is inferred; MPEA 25.0 degrees C is not adopted. Density-specific scope of RT remains subject to independent review.')
            method = ('Compression test with specimen-mounted clip-on extensometer for Young\'s modulus; MTS Insight 100 kN Extended Length.' if mechanical else 'Archimedes method; fluid, correction procedure and density specimen details are not stated.')
            conditions['test_method'] = fact(method, tag='method')
            if mechanical:
                conditions['loading_rate'] = fact('Strain rate 0.001 s^-1.', notes='Source-reported strain rate, not crosshead speed.')
                conditions['direction'] = fact(notes='Compression is the loading mode; orientation relative to cast ingot and grain structure remains unspecified.')
                conditions['additional_conditions'] = [{'name': 'compression_specimen_geometry', 'fact': fact('Cylindrical specimens, diameter 13 mm and height 26 mm.')}]
            else:
                conditions['direction'] = fact(status='not_applicable', notes='Scalar density; not a claim of isotropic mechanical response.')
                conditions['loading_rate'] = fact(status='not_applicable', notes='Mechanical loading rate does not apply to the selected Archimedes density.')
            count = {'value': 5 if mechanical else None, 'relation': 'at_least' if mechanical else 'not_reported',
                     'scope': 'Compression specimens; not independent manufacturing batches.' if mechanical else 'Density-specific count remains unknown.',
                     'source_statement': 'Methods reports at least five specimens for compression repeatability.' if mechanical else 'Density measurement is described separately without a density-specific count.',
                     'evidence': evidence('Methods, mechanical characterization', 'sample_count') if mechanical else []}
            discrepancy = []
            if row['mpea_formula_mismatch']:
                discrepancy = [{'description': 'MPEA formula ratio conflicts with the original Al70/Si10 nominal recipe.',
                                'disposition': 'Use the original Table 1/Table 3 nominal label; do not assign values to the compiled Al65/Si15-like formula.',
                                'evidence': evidence('Tables 1 and 3, alloy row ' + label, 'source_discrepancy')}]
            properties['records'].append({
                'id': prop_id, 'version': '1.0.0', 'material_state_id': state,
                'quantity': quantity, 'quantity_dimension': 'pressure' if mechanical else 'mass_per_volume',
                'source_property_label': 'E (GPa)' if mechanical else 'rho (g/cm3)',
                'reported_value': {'kind': 'scalar', 'value_text': value, 'unit_text': 'GPa' if mechanical else 'g/cm3', 'unit_code': unit, 'number': value},
                'evidence_kind': 'published_experimental_reference', 'reporting_basis': 'reported_summary',
                'determination_basis': 'source_reports_measurement', 'basis_note': 'Original Table 3; center statistic not explicitly defined in inspected methods.',
                'conditions': conditions, 'density_basis': None if mechanical else 'not_stated', 'summary_statistic': 'not_stated',
                'uncertainty': ({'type': 'reported_measures', 'measures': [{
                    'kind': 'standard_deviation', 'availability': 'numeric_reported', 'basis': 'absolute',
                    'reported_value': {
                        'value_text': row['modulus_plus_minus_literal'].split('±')[1].strip(),
                        'unit_text': 'GPa', 'unit_code': 'GPa',
                        'number': str(int(row['modulus_plus_minus_literal'].split('±')[1].strip()))},
                    'qualifier': 'not_qualified_in_source',
                    'scope': 'Table 3 E standard deviation, identified by Par25; source leading-zero integers are preserved without decimal rescaling.',
                    'coverage_factor': None, 'confidence_level': None,
                    'evidence': evidence('Table 3, E column, row ' + label + '; Mechanical properties, Par25', 'uncertainty'),
                    'note': 'SD is reported independently of an unstated center aggregation; do not infer mean, SEM, CI or independent manufacturing batches.'}]}
                    if mechanical else None),
                'uncertainty_status': 'reported_measures' if mechanical else 'not_reported_in_inspected_source',
                'uncertainty_note': ('Original Table 3 E cell: ' + row['modulus_plus_minus_literal'] + ' GPa; Par25 identifies standard deviations. Leading-zero integer is normalized numerically, not changed to an implied decimal. Center statistic remains not_stated.' if mechanical else 'Table 3 density cells have no per-value SD. The general Par25 SD statement supplies no missing density number; mechanical SD and specimen counts are not transferred.'),
                'sample_count': count, 'method_definition': {'type': 'source_reported_conventional', 'definition': method, 'extraction_window': None, 'evidence': evidence('Methods, mechanical characterization', 'method')},
                'source_discrepancies': discrepancy, 'source_id': SOURCE,
                'evidence': evidence('Table 3, row ' + label + ', ' + ('E (GPa)' if mechanical else 'rho (g/cm3)') + ' column', 'reported_value', 'classification') + (evidence('Table 3, E column, row ' + label + '; Mechanical properties, Par25', 'uncertainty') if mechanical else []),
                'source_document': deepcopy(document), 'scope_note': scope + (' Compression-derived modulus; not tensile modulus or verified elastic fitting window.' if mechanical else 'Density method does not establish bulk/true/apparent distinction; no density-derived strength inference.'),
                'evaluation_support': 'catalog_only', 'universal_bound': False, 'engineering_allowable': False,
                'verification': {'source_inspection_scope': SCOPE, 'transcription_cross_check': 'completed', 'independent_scientific_review': False, 'raw_data_reanalysis': False},
            })
        materials['records'].append({'id': state, 'version': '1.0.0', 'identity_id': identity, 'grade_id': None,
            'name': name + ', cast state', 'names': dict.fromkeys(('en', 'zh', 'ja', 'de'), name + ', cast state'),
            'aliases': [], 'source_designation': label, 'state': state_facts, 'source_scope': scope,
            'evidence': evidence('Methods, materials preparation; Tables 1 and 3, ' + label, 'state'),
            'property_ids': property_ids, 'evaluation_support': 'catalog_only'})
    validate_material_catalog(materials, properties, sources)
    return {'schema': 'primary-source-candidate/1', 'status': 'held_pending_independent_review',
            'admitted_increment': 0, 'candidate_counts': {'identities': 5, 'grades': 0, 'states': 5, 'properties': 10, 'sources': 1},
            'catalogs': {'materials': materials, 'properties': properties, 'sources': sources},
            'primary_facts': rows, 'pending_gates': ['Independent source/identity review of this revised frozen payload.',
                'Preserve density-specific unknowns and qualitative RT without numerical defaults.',
                'Full baseline identity overlap review and explicit admission decision.',
                'Integration, full regression and installed-wheel checks.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--xml', type=Path, required=True)
    parser.add_argument('--mpea', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.resolve().is_relative_to((ROOT / 'materials_boundaries/data').resolve()):
        raise ValueError('runtime output prohibited')
    payload = encoded(build(args.xml.read_bytes(), args.mpea.read_bytes()))
    if args.output.exists():
        if args.output.read_bytes() != payload:
            raise ValueError('refusing different existing output')
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(payload)
    print('Candidate: 5 identities / 10 properties; admitted increment 0; independent review pending.')


if __name__ == '__main__':
    main()
