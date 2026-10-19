"""Read-only field coverage and overlap diagnostics for the frozen formal catalog.

No source adapter, identity inference, candidate queue, approval or admission.
An exact frozen record reference is not proof of physical material equivalence.
"""
import argparse
from collections import Counter, defaultdict
from importlib.resources import files
import hashlib
from pathlib import Path
import re
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'formal-catalog'))

from materials_project_catalog.catalog import formal_project_catalog, RESOURCE_SHA256
from materials_boundaries._material_derivation import canonical_identity_key
from nomad_batch import canonical, composition, digest, ID
from nomad_incremental import decode

SCHEMA = 'formal-overlap-audit/1'
PROBE_SCHEMA = 'formal-overlap-probes/1'
MAX_PROBES, MAX_INPUT_BYTES, MAX_OUTPUT_BYTES = 20, 65536, 12000000
CROSSWALK_SHA256 = 'cddecb6f388814c0e85f64ab580cb9e551673240d2a182929a48e40b94079afa'
HASH = re.compile(r'[0-9a-f]{64}\Z')
SAFE_TEXT = re.compile(r'[^\x00-\x1f\x7f-\x9f\ud800-\udfff]{1,256}\Z')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def _read_pinned(name, expected):
    raw = files('materials_boundaries').joinpath('data', name + '.json').read_bytes()
    require(hashlib.sha256(raw).hexdigest() == expected, 'Pinned audit resource differs')
    return decode(raw)


def _text(value):
    return isinstance(value, str) and bool(SAFE_TEXT.fullmatch(value)) and bool(value.strip())


def validate_probes(document):
    """Explicit diagnostic assertions, never an ingestion/admission input format."""
    require(isinstance(document, dict) and set(document) == {'schema', 'probes'}, 'Invalid probe envelope')
    require(document['schema'] == PROBE_SCHEMA, 'Unsupported probe schema')
    probes = document['probes']
    require(isinstance(probes, list) and len(probes) <= MAX_PROBES, 'Probe limit exceeded or invalid list')
    seen = set()
    allowed = {'probe_id', 'formula', 'terms', 'formal_reference', 'provider_reference', 'taxon_reference'}
    for probe in probes:
        require(isinstance(probe, dict) and not set(probe) - allowed, 'Invalid probe fields')
        pid = probe.get('probe_id')
        require(isinstance(pid, str) and bool(ID.fullmatch(pid)) and pid not in seen, 'Invalid or duplicate probe ID')
        seen.add(pid)
        require(bool(set(probe) - {'probe_id'}), 'Probe has no comparison fields')
        if 'formula' in probe:
            composition(probe['formula'])
        if 'terms' in probe:
            terms = probe['terms']
            require(isinstance(terms, list) and 1 <= len(terms) <= 8, 'Use one to eight literal terms')
            require(all(_text(t) and 2 <= len(t) <= 80 for t in terms), 'Invalid literal term')
            require(len({t.casefold() for t in terms}) == len(terms), 'Duplicate literal terms')
        if 'formal_reference' in probe:
            ref = probe['formal_reference']
            require(isinstance(ref, dict) and set(ref) == {'id', 'identity_sha256'}, 'Invalid formal reference')
            require(_text(ref['id']) and isinstance(ref['identity_sha256'], str)
                    and bool(HASH.fullmatch(ref['identity_sha256'])), 'Invalid formal reference values')
        if 'provider_reference' in probe:
            ref = probe['provider_reference']
            require(isinstance(ref, dict) and ref.get('provider') == 'nomad'
                    and not set(ref) - {'provider', 'material_id', 'entry_id'}
                    and bool(set(ref) - {'provider'}), 'Only explicit NOMAD reference diagnostics are supported')
            require(all(isinstance(v, str) and bool(ID.fullmatch(v)) for k, v in ref.items()
                        if k != 'provider'), 'Invalid provider reference')
        if 'taxon_reference' in probe:
            ref = probe['taxon_reference']
            require(isinstance(ref, dict) and set(ref) == {'accepted_taxon_id', 'tissue_scope', 'backbone_sha256'},
                    'Invalid taxon reference')
            require(isinstance(ref['accepted_taxon_id'], str)
                    and bool(re.fullmatch(r'wfo-[0-9]{10}', ref['accepted_taxon_id']))
                    and _text(ref['tissue_scope']) and isinstance(ref['backbone_sha256'], str)
                    and bool(HASH.fullmatch(ref['backbone_sha256'])), 'Invalid taxon reference values')
    return probes


def _cue(text, path, source, kind, status=None, context=None):
    return {'text': text, 'path': path, 'source': source, 'kind': kind, 'status': status,
            'context': context or {}}


def _labels(row, pointer, source, context=None):
    cues = []
    for key in ('name', 'source_designation', 'designation'):
        if isinstance(row.get(key), str):
            cues.append(_cue(row[key], pointer + '/' + key, source, 'qualified_text', context=context))
    for lang, text in row.get('names', {}).items():
        cues.append(_cue(text, pointer + '/names/' + lang, source, 'name', context=context))
    for index, alias in enumerate(row.get('aliases', [])):
        cues.append(_cue(alias['text'], pointer + '/aliases/' + str(index) + '/text', source, 'alias', context=context))
    return cues


def load_inventory():
    """Reuse formal admission pins; inspect linked fields without editing them."""
    catalog = formal_project_catalog()
    require(catalog['counts']['formal_project_admission_count'] == 1081, 'Unexpected formal scope')
    materials = _read_pinned('materials', RESOURCE_SHA256['materials'])
    crosswalk = _read_pinned('wood_baseline_crosswalk_v2', CROSSWALK_SHA256)
    by_crosswalk = {r['baseline_identity_id']: (i, r) for i, r in enumerate(crosswalk)}
    states, grades = defaultdict(list), defaultdict(list)
    for index, row in enumerate(materials['records']):
        states[row['identity_id']].append((index, row))
    for index, row in enumerate(materials['grades']):
        grades[row['identity_id']].append((index, row))
    identities = {row['id']: (i, row) for i, row in enumerate(materials['identities'])}
    rows = []
    for formal in catalog['records']:
        item = {'formal_id': formal['id'], 'category': formal['category'],
                'partition': formal['partition'], 'name': formal['name'],
                'structured_composition': None, 'canonical_taxon': None,
                'conservative_taxon_crosswalk': None, 'provider_reference': None,
                'related_provider_groups': {},
                'grade_count': 0, 'state_count': 0, 'composition_prose_paths': [],
                'comparison_cues': []}
        if formal['partition'] == 'reviewed-computed':
            model = formal['model']
            index = len(rows) - len(materials['identities'])
            pointer = '/records/' + str(index)
            reduced, _ = composition(model['formula'])
            counts = model['canonical_composition']
            require(all(type(v) is int and v > 0 for v in counts.values()), 'Invalid pinned composition')
            require(composition(''.join(k + str(v) for k, v in sorted(counts.items())))[0] == reduced,
                    'Pinned composition disagrees with formula')
            item.update(identity_sha256=digest(model), identity_pointer=pointer,
                        identity_source='formal_computed_review',
                        primary_comparability='structured_composition',
                        structured_composition={'formula': reduced, 'path': pointer + '/canonical_composition'},
                        provider_reference={'provider': 'nomad', 'material_id': model['provider_material_id'],
                                            'entry_id': model['provider_entry_id']},
                        related_provider_groups=model.get('overlap_relations', {}).get('same_composition_provider_groups', {}))
            item['comparison_cues'] = [_cue(model['formula'], pointer + '/formula', 'formal_computed_review', 'formula')]
        else:
            index, identity = identities[formal['identity']['id']]
            pointer = '/identities/' + str(index)
            item.update(identity_sha256=digest(identity), identity_pointer=pointer,
                        identity_source='materials', scoped_catalog_key=canonical_identity_key(identity),
                        primary_comparability='source_qualified_text_only')
            context = {'identity_scope': identity['identity_scope']}
            item['comparison_cues'] = _labels(identity, pointer, 'materials', context)
            taxon = identity.get('canonical_taxon')
            if taxon:
                item['canonical_taxon'] = {key: taxon[key] for key in ('identity_key', 'accepted_taxon_id', 'tissue_scope')}
                item['canonical_taxon'].update(backbone_sha256=taxon['backbone']['archive_sha256'],
                                               path=pointer + '/canonical_taxon')
                item['primary_comparability'] = 'scoped_taxon_identity'
            if identity['id'] in by_crosswalk:
                cross_index, cross = by_crosswalk[identity['id']]
                item['conservative_taxon_crosswalk'] = {
                    key: cross[key] for key in ('accepted_wfo_ids', 'baseline_tissue', 'disposition',
                                                'authority_abbreviation_reconciled')}
                item['conservative_taxon_crosswalk']['path'] = '/' + str(cross_index)
                item['primary_comparability'] = 'advisory_taxon_crosswalk'
            item['grade_count'] = len(grades[identity['id']])
            item['state_count'] = len(states[identity['id']])
            for grade_index, grade in grades[identity['id']]:
                gp = '/grades/' + str(grade_index)
                grade_context = context | {'grade_authority': grade['authority'], 'manufacturer': grade['manufacturer']}
                item['comparison_cues'].extend(_labels(grade, gp, 'materials', grade_context))
            for state_index, state in states[identity['id']]:
                sp = '/records/' + str(state_index)
                fact = state['state']['composition_or_purity']
                state_context = context | {'source_scope': state['source_scope'], 'composition_notes': fact['notes']}
                item['comparison_cues'].extend(_labels(state, sp, 'materials', state_context))
                fp = sp + '/state/composition_or_purity'
                if fact['status'] == 'reported':
                    item['composition_prose_paths'].append(fp)
                    item['comparison_cues'].append(_cue(fact['text'], fp + '/text', 'materials',
                                                         'composition_or_purity', fact['status'], state_context))
        rows.append(item)
    require(len(rows) == 1081 and len({r['formal_id'] for r in rows}) == 1081, 'Formal identity coverage differs')
    return {'catalog_version': catalog['version'], 'resource_sha256': catalog['resource_sha256'] | {
                'wood_baseline_crosswalk_v2': CROSSWALK_SHA256},
            'formal_counts': catalog['counts'], 'rows': sorted(rows, key=lambda r: r['formal_id'])}


def _literal_hit(text, term, *, case_sensitive=False):
    return re.search(r'(?<![\w])' + re.escape(term) + r'(?![\w])', text,
                     0 if case_sensitive else re.IGNORECASE) is not None


def compare_probe(row, probe):
    """Compare supported facts; absence or disagreement never proves novelty."""
    reasons, evidence, conflicts = [], [], []
    formula = composition(probe['formula'])[0] if 'formula' in probe else None
    structured = row['structured_composition']
    if formula and structured:
        if formula == structured['formula']:
            reasons.append('same_structured_composition_identity_unresolved')
            evidence.append({'source': row['identity_source'], 'path': structured['path']})
        else:
            conflicts.append('structured_composition_differs')
    ref = probe.get('provider_reference')
    existing = row['provider_reference']
    if ref and existing:
        shared = [key for key in ('material_id', 'entry_id') if key in ref and ref[key] == existing[key]]
        if shared:
            reasons.append('shared_provider_reference_identity_unresolved')
            evidence.extend({'source': 'formal_computed_review', 'path': row['identity_pointer'] + '/provider_' + key}
                            for key in shared)
        if any(key in ref and ref[key] != existing[key] for key in ('material_id', 'entry_id')):
            conflicts.append('provider_references_disagree')
        for material_id, entry_ids in row['related_provider_groups'].items():
            if ref.get('material_id') == material_id or ref.get('entry_id') in entry_ids:
                reasons.append('known_related_provider_group_identity_unresolved')
                token = material_id.replace('~', '~0').replace('/', '~1')
                evidence.append({'source': 'formal_computed_review', 'path': row['identity_pointer']
                                 + '/overlap_relations/same_composition_provider_groups/' + token})
        if 'material_id' in ref and 'entry_id' in ref:
            primary_pair = ref['material_id'] == existing['material_id'] and ref['entry_id'] == existing['entry_id']
            related_pair = ref['entry_id'] in row['related_provider_groups'].get(ref['material_id'], [])
            if not primary_pair and not related_pair:
                conflicts.append('provider_reference_pair_not_found')
    taxon = probe.get('taxon_reference')
    existing_taxon = row['canonical_taxon']
    cross = row['conservative_taxon_crosswalk']
    if taxon and existing_taxon:
        if taxon['accepted_taxon_id'] == existing_taxon['accepted_taxon_id']:
            reasons.append('shared_taxon_reference_scope_requires_review')
            evidence.append({'source': 'materials', 'path': existing_taxon['path']})
        else:
            conflicts.append('taxon_id_differs')
        if any(taxon[key] != existing_taxon[key] for key in ('tissue_scope', 'backbone_sha256')):
            conflicts.append('taxon_tissue_or_backbone_differs')
    if taxon and cross and taxon['accepted_taxon_id'] in cross['accepted_wfo_ids']:
        reasons.append('conservative_taxon_crosswalk_advisory')
        evidence.append({'source': 'wood_baseline_crosswalk_v2', 'path': cross['path'],
                         'disposition': cross['disposition'], 'tissue': cross['baseline_tissue']})
        conflicts.append('crosswalk_does_not_establish_same_tissue_material')
    for cue in row['comparison_cues']:
        formula_hit = formula and _literal_hit(cue['text'], formula, case_sensitive=True)
        term_hit = any(_literal_hit(cue['text'], term) for term in probe.get('terms', []))
        if formula_hit or term_hit:
            reasons.append('literal_text_cue_not_composition_or_identity')
            evidence.append({key: cue[key] for key in ('source', 'path', 'kind', 'status', 'context')} | {
                'text': cue['text'], 'hit': 'formula_literal' if formula_hit else 'caller_supplied_literal_term'})
    formal = probe.get('formal_reference')
    exact = False
    if formal and formal['id'] == row['formal_id']:
        if formal['identity_sha256'] == row['identity_sha256']:
            exact = True
            reasons.append('exact_frozen_formal_record_reference')
            evidence.append({'source': row['identity_source'], 'path': row['identity_pointer'],
                             'identity_sha256': row['identity_sha256']})
        else:
            conflicts.append('formal_reference_digest_differs')
    status = 'confirmed_overlap' if exact and not conflicts else 'possible_overlap' if reasons else 'unable_to_compare'
    if exact and conflicts:
        reasons.append('exact_reference_with_conflicting_probe_facts')
    if not reasons:
        reasons.append('no_overlap_evidence_in_supported_fields')
    return {'formal_id': row['formal_id'], 'status': status,
            'proof_scope': 'frozen_formal_record_reference' if status == 'confirmed_overlap' else 'diagnostic_relation_only',
            'physical_equivalence': 'unasserted', 'reasons': sorted(set(reasons)),
            'conflicts': sorted(set(conflicts)),
            'evidence': sorted({digest(item): item for item in evidence}.values(), key=lambda x: (x['source'], x['path'], digest(x)))}


def build_report(probe_document=None):
    probes = validate_probes({'schema': PROBE_SCHEMA, 'probes': []} if probe_document is None else probe_document)
    inventory = load_inventory()
    rows = inventory['rows']
    dimensions = {
        'structured_integer_composition': sum(r['structured_composition'] is not None for r in rows),
        'scoped_canonical_taxon': sum(r['canonical_taxon'] is not None for r in rows),
        'advisory_taxon_crosswalk': sum(r['conservative_taxon_crosswalk'] is not None for r in rows),
        'reported_composition_prose': sum(bool(r['composition_prose_paths']) for r in rows),
        'associated_grade': sum(bool(r['grade_count']) for r in rows),
        'composite_category': sum(r['category'] == 'composite' for r in rows)}
    comparisons = []
    for probe in sorted(probes, key=lambda p: p['probe_id']):
        relations = [compare_probe(row, probe) for row in rows]
        comparisons.append({'probe_id': probe['probe_id'], 'probe_sha256': digest(probe),
                            'counts': {status: sum(r['status'] == status for r in relations)
                                       for status in ('confirmed_overlap', 'possible_overlap', 'unable_to_compare')},
                            'relations': relations, 'new_material_count': None, 'admitted_delta': 0})
    # Keep full qualifying prose only where it actually matched; inventory stores locations.
    public_rows = [{key: value for key, value in row.items() if key != 'comparison_cues'} for row in rows]
    return {'schema': SCHEMA, 'catalog_version': inventory['catalog_version'],
            'resource_sha256': inventory['resource_sha256'], 'formal_counts': inventory['formal_counts'],
            'primary_comparability_partition': dict(sorted(Counter(r['primary_comparability'] for r in rows).items())),
            'overlapping_field_coverage_dimensions': dimensions,
            'coverage_policy': 'Dimensions overlap; only primary_comparability_partition sums to 1081. Text is never parsed into trusted stoichiometry.',
            'classification_policy': {
                'confirmed_overlap': 'Exact supplied formal ID and frozen identity-content digest; catalog-record reuse only, not proof a new source describes the same physical material.',
                'possible_overlap': 'Shared composition, provider/taxon reference or literal text clue; scope, phase, formulation, state and equivalence require review.',
                'unable_to_compare': 'No supported overlap evidence, including nonmatching structured values; not evidence of novelty or eligibility.'},
            'rows': public_rows, 'probe_results': comparisons,
            'limits': [
                'Frozen metadata audit only. No source truth, scientific validity, license decision or complete cross-provider equivalence is established.',
                'Taxon keys include tissue/backbone scope; conservative wood exclusions and cork remain advisory.',
                'Literal terms are explicit caller hints, not synonyms, fuzzy chemistry or a complete search. Zero matches do not establish novelty.',
                'Provider IDs and composition buckets are not universal physical material identities.',
                'The 62 unadmitted examples and old seven examples are not added to the formal inventory.',
                'No material, candidate queue, source adapter, approval, admission, or network state is changed.'],
            'new_material_count': None, 'admitted_delta': 0}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--probes', type=Path, help='Explicit local diagnostic probe JSON (at most 20); no source URLs')
    args = parser.parse_args(argv)
    try:
        document = None
        if args.probes is not None:
            with args.probes.open('rb') as handle:
                raw = handle.read(MAX_INPUT_BYTES + 1)
            require(len(raw) <= MAX_INPUT_BYTES, 'Probe input exceeds byte limit')
            document = decode(raw.decode('utf-8'))
        result = canonical(build_report(document)) + b'\n'
        require(len(result) <= MAX_OUTPUT_BYTES, 'Diagnostic output exceeds byte limit')
    except (ValueError, TypeError, KeyError, OSError, RecursionError, UnicodeError):
        print('Formal overlap audit rejected invalid or unavailable input; no report emitted.', file=sys.stderr)
        return 2
    sys.stdout.buffer.write(result)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
