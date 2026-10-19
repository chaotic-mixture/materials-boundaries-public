"""Offline preparation of the existing two-record held formal-review subset.

Hashes bind content, not reviewer identity, scientific validity or reuse rights.
This report preserves the historical scoped acceptance and never admits records.
Only explicitly supplied local files are inspected; no source requests are made.
"""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import stat
import sys

from nomad_batch import assert_no_geometry, digest
from nomad_review_boundary import ROOT, SOURCES, load_review_boundary

SCHEMA = 'formal-admission-gaps/1'
EXAMPLE = 'experimental/platform/examples/reviewed-computed-v2-second/'
PARENT = {
    'input': {'path': EXAMPLE + 'eligible-metadata-input.json',
              'sha256': '41d0691a8289c6d30fc24a5ecaef1f3b3e4b3ded57eac15ea8d64adc8a8398d6'},
    'review': {'path': SOURCES['unadmitted_example62'][0],
               'sha256': SOURCES['unadmitted_example62'][1]},
    'acceptance_pin': {'path': EXAMPLE + 'acceptance-pin.json',
                       'sha256': '47d21e9237a62ce4b2eda806cd2163b7d7bc576f1577deff623caf5e54efd543'},
}
CANONICAL_REVIEW_SHA256 = '318f12f676ff2db9d2429fa1cfb937cb08d9fa89292dff2a46be87171e113115'
SELECTED = {
    'nomad_computed_79d7f2436fdc66a5': {
        'review_index': 4, 'formula': 'AlGa2Sc',
        'canonical_sha256': '70189c104e4dfb57d561623fee7930fb6277799e7ade35afaffc41b0c7c57adf'},
    'nomad_computed_a7cbfee72baf6866': {
        'review_index': 60, 'formula': 'O8Re2Ru4',
        'canonical_sha256': 'eb14fd8ff979b157e979618945997940b03876ed1cc4ba3ac651d43ccff1ee19'},
}
MAX_ARTIFACT_BYTES = 32_000_000
RECORD_EVIDENCE = ('candidate_packet_sha256', 'archive_response_sha256',
                   'relations_response_sha256', 'frozen_source_response_sha256',
                   'attribution_response_sha256')
GAPS = (
    ('source_snapshot_review',
     'Locate snapshot-bound source/relation/attribution evidence, or policy-compatible identified review receipts. '
     'Verify applicability to this exact subset; missing public raw geometry does not invalidate historical acceptance.'),
    ('numerical_semantics_review',
     'Verify exact computed density, source field, kg/m^3 unit semantics and method scope through source evidence '
     'or applicable identified prior review. Do not infer experimental or ambient-condition density.'),
    ('identity_scope_review',
     'Review selected and related provider groups, prototype/symmetry assertions, composition buckets and overlap '
     'under the current project policy. Preserve unresolved phase/site-order and cross-provider equivalence.'),
    ('scientific_review_authority',
     'The release operator must verify the identified reviewer, independence, conflicts, authority and exact-subset '
     'applicability of an existing review receipt, or obtain a new explicit subset review.'),
    ('scoped_reuse_review',
     'Locate or obtain an identified scoped reuse review covering attribution, modification notices and access, '
     'retention, derived export and redistribution. Declared CC BY 4.0 and hash matches are not new legal clearance.'),
    ('formal_release_decision',
     'Obtain a separately authorized reviewed formal release decision, applicable count policy, exact new pins '
     'and required source/installed-artifact checks. Historical experimental acceptance is not formal admission.'),
)
GAP_EVIDENCE = {
    'source_snapshot_review': list(RECORD_EVIDENCE),
    'numerical_semantics_review': ['archive_response_sha256', 'frozen_source_response_sha256',
                                  'source_unit_definition_snapshot_sha256'],
    'identity_scope_review': ['relations_response_sha256', 'frozen_source_response_sha256'],
    'scientific_review_authority': [],
    'scoped_reuse_review': ['attribution_response_sha256', 'frozen_source_response_sha256'],
    'formal_release_decision': [],
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def load_parents(root):
    """Compare against code-pinned identities before trusting cross-file claims."""
    documents = {}
    for label, binding in PARENT.items():
        try:
            raw = (root / binding['path']).read_bytes()
        except OSError as exc:
            raise ValueError('Required parent artifact unavailable: ' + label) from exc
        require(hashlib.sha256(raw).hexdigest() == binding['sha256'], 'Parent artifact hash mismatch: ' + label)
        documents[label] = json.loads(raw)
    source, review, pin = (documents[key] for key in ('input', 'review', 'acceptance_pin'))
    require(digest(review) == CANONICAL_REVIEW_SHA256, 'Canonical parent review hash mismatch')
    require(pin['input_file_sha256'] == review['input_file_sha256'] == PARENT['input']['sha256'],
            'Parent input binding mismatch')
    require(pin['normalized_review_file_sha256'] == PARENT['review']['sha256']
            and pin['canonical_review_sha256'] == CANONICAL_REVIEW_SHA256, 'Acceptance review binding mismatch')
    require(pin['decision'] == 'accepted_exact_scoped_metadata_only' and pin['persistent_admissions'] == 0,
            'Unexpected historical acceptance scope')
    for label, document in (('input', source), ('review', review)):
        rows = document['records']
        require(len(rows) == 62 and len({row['candidate_id'] for row in rows}) == 62,
                'Parent record cardinality or identity mismatch: ' + label)
    require({r['candidate_id'] for r in source['records']} == {r['candidate_id'] for r in review['records']},
            'Input/review candidate identities differ')
    return source, review, pin


def observe_artifact(label, expected, references, local_path):
    """Inspect only provided bytes; never emit file paths, contents or OS errors."""
    result = {'label': label, 'expected_sha256': expected, 'references': references,
              'availability': 'reference_only_not_provided', 'actual_sha256': None, 'bytes_read': None,
              'meaning': 'Availability/content binding only; does not complete scientific, rights or release review'}
    if local_path is None:
        return result
    try:
        path = Path(local_path)
        if not stat.S_ISREG(path.stat().st_mode):
            result['availability'] = 'not_regular_file'
            return result
        with path.open('rb') as handle:
            raw = handle.read(MAX_ARTIFACT_BYTES + 1)
    except FileNotFoundError:
        result['availability'] = 'missing'
    except OSError:
        result['availability'] = 'read_error'
    else:
        result['bytes_read'] = len(raw)
        if len(raw) > MAX_ARTIFACT_BYTES:
            result['availability'] = 'size_limit_exceeded'
        else:
            result['actual_sha256'] = hashlib.sha256(raw).hexdigest()
            result['availability'] = 'digest_match' if result['actual_sha256'] == expected else 'digest_mismatch'
    return result


def build_report(root=ROOT, *, candidate_ids=None, local_artifacts=None):
    """Return a detached deterministic report for the exact held two-record subset.

    ``local_artifacts`` maps a reported evidence label to an explicit local path.
    Its observations never change the six human-review gates or formal status.
    ``candidate_ids`` must be exactly the two code-pinned IDs without duplicates.
    """
    root = Path(root)
    ids = list(SELECTED if candidate_ids is None else candidate_ids)
    require(len(ids) == len(SELECTED) and len(set(ids)) == len(ids) and set(ids) == set(SELECTED),
            'Selection must contain exactly the two pinned candidate IDs without duplicates')
    local_artifacts = dict(local_artifacts or {})
    allowed_labels = set(RECORD_EVIDENCE) | {'source_unit_definition_snapshot_sha256', 'acceptance_candidate_file_sha256'}
    require(set(local_artifacts) <= allowed_labels, 'Unknown local evidence label')
    source, review, pin = load_parents(root)
    boundary = load_review_boundary(root)
    source_by_id = {row['candidate_id']: row for row in source['records']}
    selected, references = [], {}
    for candidate_id, expected in SELECTED.items():
        index = expected['review_index']
        row = review['records'][index]
        require(row['candidate_id'] == candidate_id and row['formula'] == expected['formula']
                and digest(row) == expected['canonical_sha256'], 'Selected canonical record binding mismatch')
        require(row['decision'] == 'accepted', 'Historical selected decision changed')
        assert_no_geometry(row)
        input_row = source_by_id[candidate_id]
        # Bind each retained scientific field to its preparation input; the
        # reviewed derivative intentionally adds its scoped rights wording.
        for field in ('provider_entry_id', 'provider_material_id', 'formula', 'canonical_composition',
                      'conservative_count_bucket', 'material_scope', 'method', 'provenance', 'attribution',
                      'source_url', 'checks', 'overlap_relations', 'evidence'):
            require(row[field] == input_row[field], 'Selected input transcription mismatch: ' + field)
        require(row['density'] == input_row['property'], 'Selected density transcription mismatch')
        require('unadmitted_example62' in boundary['materials'].get(row['provider_material_id'], [])
                and 'formal_admitted24' not in boundary['materials'].get(row['provider_material_id'], []),
                'Selected provider identity crossed formal review boundary')
        selected.append({'candidate_id': candidate_id, 'review_pointer': f'/records/{index}',
                         'canonical_record_sha256': expected['canonical_sha256'],
                         'input_record_sha256': digest(input_row), 'basis': 'historical_parent_review',
                         'source_review_decision': row['decision'], 'formal_state': 'held',
                         'current_scientific_verification': False, 'record': deepcopy(row)})
        for label in RECORD_EVIDENCE:
            expected_hash = row['evidence'][label]
            existing = references.setdefault(label, {'sha256': expected_hash, 'locators': []})
            require(existing['sha256'] == expected_hash, 'Selected source evidence hashes differ: ' + label)
            existing['locators'].append({'artifact': 'review', 'pointer': f'/records/{index}/evidence/{label}'})
    for label, field in [('source_unit_definition_snapshot_sha256', 'source_unit_definition_snapshot_sha256'),
                         ('acceptance_candidate_file_sha256', 'candidate_file_sha256')]:
        references[label] = {'sha256': pin[field], 'locators': [{'artifact': 'acceptance_pin', 'pointer': '/' + field}]}
    observations = [observe_artifact(label, ref['sha256'], ref['locators'], local_artifacts.get(label))
                    for label, ref in sorted(references.items())]
    result = {
        'schema': SCHEMA,
        'scope': 'Preparation report for the existing AlGa2Sc/O8Re2Ru4 held subset; no new scientific or formal acceptance',
        'source_bindings': deepcopy(PARENT) | {'canonical_review_sha256': CANONICAL_REVIEW_SHA256},
        'review_boundary': {'basis': 'Existing pinned review-boundary reader; no new formal release',
                            'sha256': boundary['sha256'], 'baseline_commit': boundary['baseline_commit'],
                            'formal_project_total': boundary['formal_project_total'],
                            'formal_legacy_count': boundary['formal_legacy_count'],
                            'formal_computed_composition_count': boundary['formal_computed_composition_count'],
                            'excluded_example_count': boundary['excluded_example_count']},
        'historical_acceptance': {'basis': 'historical_parent_review', 'decision': pin['decision'],
                                   'reviewer_label': review['reviewer'], 'rationale': review['rationale'],
                                   'scope': pin['scope'], 'count_policy': deepcopy(review['count_policy']),
                                   'persistent_admissions': pin['persistent_admissions'],
                                   'reviewer_authenticated_by_this_report': False,
                                   'current_scientific_verification': False,
                                   'candidate_canonical_sha256_reference': pin['candidate_canonical_sha256']},
        'formal_release': {'state': 'held', 'admitted_delta': 0, 'automatic_admission': False,
                           'release_authorized_by_this_report': False},
        'allowed_unknowns': {'policy': 'Preserved scope limitations, not deficiencies created by this report',
                             'null_conditions': ['temperature_K', 'pressure_Pa'],
                             'unknown_states': ['experimental_existence', 'phase_stability', 'equilibrium',
                                                'convergence', 'electronic_behavior'],
                             'physical_and_global_equivalence': 'unresolved'},
        'selected_records': selected,
        'gaps': [{'id': name, 'status': 'unverified_for_new_release', 'candidate_ids': list(SELECTED),
                  'related_evidence_labels': list(GAP_EVIDENCE[name]), 'required_review': requirement}
                 for name, requirement in GAPS],
        'evidence_observations': observations,
        'limitations': ['Hash matches prove byte identity only, not reviewer authority, science, source authenticity or rights.',
                        'A missing local artifact does not prove it never existed or invalidate the prior scoped acceptance.',
                        'Private source evidence may remain private; raw geometry publication is not required.',
                        'Historical checks and confidence labels are preserved assertions, not recomputed by this report.'],
    }
    result['report_sha256'] = digest(result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo-root', type=Path, default=ROOT)
    parser.add_argument('--artifact', action='append', default=[], metavar='LABEL=PATH')
    args = parser.parse_args()
    try:
        paths = {}
        for argument in args.artifact:
            label, separator, path = argument.partition('=')
            require(separator and label and path and label not in paths, 'Each artifact requires a unique LABEL=PATH')
            paths[label] = path
        result = build_report(args.repo_root, local_artifacts=paths)
        sys.stdout.buffer.write(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False).encode('utf-8') + b'\n')
    except (ValueError, KeyError, TypeError, OSError):
        parser.exit(2, 'Formal-review gap report refused: parent, selection, boundary or artifact arguments failed validation.\n')


if __name__ == '__main__':
    main()
