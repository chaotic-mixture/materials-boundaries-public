"""Map frozen source facts into an unadmitted native draft; never write runtime."""
import argparse
from hashlib import sha256
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
FACTS = ROOT / 'experimental/material-batches/jarvis-density-candidates-20261027/source-fact-candidates.json'
FACTS_SHA = '70e6664d18250098ac28cb2e7fd7eff745427a30cbdf69cf972c01529976afdb'
SOURCE = 'jarvis_dft_figshare_v11_2025_3d'
DOI = '10.6084/m9.figshare.6815699.v11'
URL = 'https://ndownloader.figshare.com/files/64391379'
METHOD_URL = 'https://jarvis-materials-design.github.io/dbdocs/jarvisdft/'
UNIT_URL = 'https://github.com/usnistgov/jarvis/blob/3b0c9d0f0c15759135de857dbc93e010db01eb29/jarvis/core/atoms.py'
ARCHIVE_SHA = 'f9e0a3309f0000d5de1ec9e49c93963109ea45e63f451103f8f6595d2eabf7f5'
MEMBER_SHA = '9dacb55ac8371c7c2bf0332933b55c98e9cca6201e92eb9d6fcd03aab0975907'
METHOD = 'source_reported_computational_structure_density'
SCOPE = ('Selected fixed-release row density/composition/model fields independently checked as source facts. '
         'Native mapping, final taxonomy and material identities remain unapproved. '
         'No scientific peer review, raw-data reanalysis, optimization or density recomputation.')


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf8')


def unknown(note=None):
    return {'status': 'not_reported_in_inspected_source', 'text': None,
            'evidence': [], 'notes': note}


def evidence(locator, *tags, url=URL):
    return [{'source_id': SOURCE, 'url': url, 'locator': locator, 'supports': list(tags)}]


def reported(text, locator, *tags):
    return {'status': 'reported', 'text': text, 'evidence': evidence(locator, *tags), 'notes': None}


def build(raw):
    if sha256(raw).hexdigest() != FACTS_SHA:
        raise ValueError('Different frozen source facts; requires fresh review')
    facts = json.loads(raw)
    for rel, digest in facts['baseline_sha256'].items():
        if sha256((ROOT / rel).read_bytes()).hexdigest() != digest:
            raise ValueError('Changed candidate preparation baseline: ' + rel)
    materials = {'schema_version': '1.0.0', 'identities': [], 'grades': [], 'records': []}
    properties = {'schema_version': '1.0.0', 'records': []}
    source = {
        'id': SOURCE, 'title': 'JARVIS-DFT 3D dataset (jdft_3d.json), Figshare version 11',
        'authors': ['Kamal Choudhary'], 'year': 2026, 'doi': DOI,
        'urls': [URL, 'https://doi.org/' + DOI, METHOD_URL, UNIT_URL,
                 'https://creativecommons.org/licenses/by/4.0/'],
        'read_status': 'fixed_release_selected_source_facts_checked_native_mapping_unreviewed',
        'license': {'status': 'explicit_reuse_license_verified', 'identifier': 'CC-BY-4.0'},
        'role': 'published_computational_reference',
        'claim_notes': [
            'Kamal Choudhary, fixed Figshare version DOI ' + DOI + '; CC BY 4.0.',
            'Changes: selected factual fields structured, compositions conservatively grouped, one minimum-numeric-JID model selected per composition, unknown conditions retained. No endorsement.',
            'Dataset license is separate from JARVIS software license. Parent database identifiers are citations only; parent database assets are not bundled.',
            'Filename dates the data 2025-09-24; fixed version metadata publication is 2026-05-09. Actual generator code version is unknown.',
        ],
        'provenance': {'curation_date': '2026-10-28', 'method': SCOPE},
        'bundled_content': 'selected_factual_fields_bibliographic_metadata_and_original_curation_only',
    }
    document = {'url': URL, 'revision': 'Figshare v11; file 64391379; jdft_3d-9-24-2025.json.zip',
                'inspected_on': '2026-10-27', 'sha256': ARCHIVE_SHA, 'hash_status': 'recorded',
                'hash_note': None, 'inspection_scope': SCOPE, 'inspection_status': 'selected_content_inspected'}
    bindings = []
    for proposed, rows in facts['candidates'].items():
        for row in rows:
            f = row['source_record']; key = row['proposed_conservative_composition_key']
            suffix = sha256(key.encode('ascii')).hexdigest()[:24]
            identity = 'mat_jarvis_v11_composition_' + suffix
            state = 'state_jarvis_v11_' + f['jid'].lower().replace('-', '_')
            prop_id = 'refprop_jarvis_v11_' + f['jid'].lower().replace('-', '_') + '_density'
            locator = ('Member jdft_3d-9-24-2025.json, data record 1-based ' + str(f['source_row_index'])
                       + ', jid=' + f['jid'] + ', formula=' + f['formula']
                       + '; raw row SHA256=' + f['source_row_text_sha256'])
            name = f['formula'] + ' source-qualified composition (JARVIS-DFT v11)'
            scope = ('Conservative source-qualified reduced composition ' + key + '. One identity proposal per '
                     'composition; alternate cells/JIDs do not add identities. The selected state is ' + f['jid']
                     + '; stable phase and experimental existence unknown. Final category is proposed, not approved. '
                     'All-metal elements alone do not establish metallic electronic behavior.')
            materials['identities'].append({
                'id': identity, 'version': '1.0.0', 'category': proposed, 'name': name,
                'names': dict.fromkeys(('en', 'zh', 'ja', 'de'), name), 'aliases': [],
                'identity_scope': scope, 'evidence': evidence(locator, 'material_identity', 'classification')})
            state_facts = {k: unknown('No physical specimen, manufacture or measurement is inferred from the computational model.')
                           for k in ['product_form', 'processing', 'temper_or_heat_treatment', 'conditioning',
                                     'composition_or_purity', 'reinforcement', 'porosity', 'orientation']}
            state_facts['composition_or_purity'] = reported(
                'Source formula ' + f['formula'] + '; reduced exact composition ' + key
                + '; computational model only, not measured purity.', locator, 'state')
            state_name = f['formula'] + ' / ' + f['jid'] + ' / ' + f['functional'] + ' reported 3D model'
            model_scope = ('Selected original model ' + f['jid'] + '; functional=' + f['functional']
                           + '; dimensionality=' + f['dimensionality'] + '; reported space group=' + f['space_group_number']
                           + '; parent reference=' + f['parent_structure_reference']
                           + '. Space group is not independently solved. Model is bound to the complete fixed archive/member and exact raw row hash, not space group alone.')
            materials['records'].append({
                'id': state, 'version': '1.0.0', 'identity_id': identity, 'grade_id': None,
                'name': state_name, 'names': dict.fromkeys(('en', 'zh', 'ja', 'de'), state_name), 'aliases': [],
                'source_designation': f['jid'], 'state': state_facts, 'source_scope': model_scope,
                'evidence': evidence(locator, 'state'), 'property_ids': [prop_id], 'evaluation_support': 'catalog_only'})
            method_evidence = (evidence(locator, 'method', 'classification')
                               + evidence('JARVIS-DFT geometry optimization and derived quantities description', 'method', 'classification', url=METHOD_URL)
                               + evidence('Atoms.density docstring: density in g/cm3; actual dataset generator version unknown', 'method', 'classification', url=UNIT_URL))
            properties['records'].append({
                'id': prop_id, 'version': '1.0.0', 'material_state_id': state,
                'quantity': 'mass_density', 'quantity_dimension': 'mass_per_volume',
                'source_property_label': 'density',
                'reported_value': {'kind': 'scalar', 'value_text': f['source_density_token'],
                                   'number': f['source_density_token'], 'unit_text': 'g/cm3', 'unit_code': 'g/cm^3'},
                'evidence_kind': 'published_computational_reference', 'reporting_basis': 'not_stated',
                'determination_basis': 'source_reports_calculation',
                'basis_note': 'Source-reported optimized computational structure density; not measured bulk/apparent density. Unit from official method/code documentation, not an explicit per-row unit string.',
                'conditions': {k: unknown('Static DFT does not establish measured temperature, pressure or test conditions.')
                               for k in ['temperature', 'test_standard', 'test_method', 'direction', 'conditioning', 'loading_rate']},
                'density_basis': 'crystallographic', 'summary_statistic': 'reported_value',
                'uncertainty': None, 'uncertainty_status': 'not_reported_in_inspected_source',
                'uncertainty_note': 'Per-record convergence, numerical/model uncertainty and phase stability unknown; absence of an uncertainty field is not zero uncertainty.',
                'sample_count': {'value': None, 'relation': 'not_reported', 'scope': 'One selected model, not a physical specimen count.',
                                 'source_statement': 'No verified independent specimen count is reported.', 'evidence': []},
                'method_definition': {'type': METHOD, 'definition': 'Reported OptB88vdW 3D optimized-structure density; no density recalculation in this project.',
                                      'extraction_window': None, 'evidence': method_evidence},
                'source_discrepancies': [], 'source_id': SOURCE,
                'evidence': evidence(locator + ', density field', 'reported_value', 'classification'),
                'source_document': dict(document), 'scope_note': model_scope + ' ' + scope,
                'evaluation_support': 'catalog_only', 'universal_bound': False, 'engineering_allowable': False,
                'verification': {'source_inspection_scope': SCOPE, 'transcription_cross_check': 'completed',
                                 'independent_scientific_review': False, 'raw_data_reanalysis': False}})
            bindings.append({'identity_id': identity, 'state_id': state, 'property_id': prop_id,
                             'composition_key': key, 'jid': f['jid'], 'proposed_category': proposed,
                             'source_row_text_sha256': f['source_row_text_sha256']})
    return {'schema': 'jarvis-native-unadmitted-draft/1', 'status': 'held_pending_independent_native_mapping_identity_and_classification_review',
            'handoff_ready': False, 'admitted_increment': 0, 'source_facts_sha256': FACTS_SHA,
            'archive_member_sha256': MEMBER_SHA,
            'catalogs': {'materials': materials, 'properties': properties, 'sources': {'schema_version': '1.0.0', 'records': [source]}},
            'bindings': bindings, 'pending': ['Native mapping and final identity/taxonomy independent review',
                'Independent four-file method implementation review', 'Historical preservation and full integration/installed checks',
                'No runtime admission or remote write before gates pass']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if not args.output.resolve().is_relative_to(Path(__file__).resolve().parent):
        raise ValueError('Output must remain inside this experimental draft batch')
    raw = encoded(build(FACTS.read_bytes()))
    if args.output.exists() and args.output.read_bytes() != raw:
        raise ValueError('Refusing to overwrite different frozen output')
    args.output.write_bytes(raw)
    print(json.dumps({'bytes': len(raw), 'sha256': sha256(raw).hexdigest(), 'admitted_increment': 0}))
