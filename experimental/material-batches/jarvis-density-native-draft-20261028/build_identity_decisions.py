"""Prepare explicit per-candidate identity/taxonomy proposals for independent review."""
from hashlib import sha256
import importlib.util
import json
from pathlib import Path

import build_native_draft as native

ROOT = native.ROOT
HELPER = ROOT / 'experimental/material-batches/quota1000-jarvis-source-audit-20261027/screen_compositions.py'


def build():
    if sha256(HELPER.read_bytes()).hexdigest() != 'b5736cc1d32ac701534fd371aa8ff50a7c39e3af3d94bf1048101170c7b6d863':
        raise ValueError('Different source composition helper')
    spec = importlib.util.spec_from_file_location('reviewed_jarvis_compositions', HELPER)
    audit = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(audit)
    raw = native.FACTS.read_bytes()
    if sha256(raw).hexdigest() != native.FACTS_SHA:
        raise ValueError('Different source facts')
    source = json.loads(raw)
    formal = set(source['formal_composition_keys_excluded'])
    rows = []
    for proposed, candidates in source['candidates'].items():
        for candidate in candidates:
            f = candidate['source_record']; key = audit.formula_key(f['formula'])
            if key != candidate['proposed_conservative_composition_key'] or key in formal:
                raise ValueError('Source/formal composition conflict')
            elements = {term.split(':')[0] for term in key.split('|')}
            if 2 <= len(elements) <= 4 and elements <= audit.METALS:
                category = 'metal'
                basis = 'All-metal composition; compositional metal-family membership under the existing finite project convention. Metallic electronic behavior unknown.'
            elif 2 <= len(elements) <= 3 and 'O' in elements and not elements & {'C', 'H'}:
                category = 'inorganic'
                basis = 'Oxygen-containing carbon/hydrogen-free inorganic composition under the finite project convention; bonding, oxidation states and experimental existence are not inferred.'
            else:
                raise ValueError('Outside declared finite classification convention')
            if category != proposed:
                raise ValueError('Classification differs from frozen proposal')
            rows.append({
                'identity_id': 'mat_jarvis_v11_composition_' + sha256(key.encode('ascii')).hexdigest()[:24],
                'identity_kind': 'hypothetical_computed_crystal_model',
                'conservative_composition_key': key, 'source_formula': f['formula'],
                'selected_jid': f['jid'], 'source_archive_sha256': native.ARCHIVE_SHA,
                'source_member_sha256': native.MEMBER_SHA,
                'source_record_index_0_based': f['source_row_index'],
                'source_row_text_sha256': f['source_row_text_sha256'],
                'proposed_category': category, 'category_basis': basis,
                'electronic_behavior': 'unknown', 'experimental_existence': 'unknown',
                'phase_stability': 'unknown', 'cross_provider_phase_equivalence': 'unresolved',
                'counting_scope': 'At most one project identity for this exact reduced composition; other source rows, phases, cells and JIDs receive no additional credit.',
                'overlap_scope': '24 existing formal computed compositions excluded; finite existing source-qualified formula and family guards applied. No universal chemical non-overlap is claimed.',
                'decision': 'proposed_for_independent_review', 'admitted_increment': 0,
            })
    if len(rows) != 2000 or len({r['conservative_composition_key'] for r in rows}) != 2000:
        raise ValueError('Unexpected composition/identity count')
    return {
        'schema': 'jarvis-finite-identity-taxonomy-proposals/1',
        'status': 'producer_proposals_pending_independent_adjudication',
        'source_facts_sha256': native.FACTS_SHA,
        'policy_reference': {'path': 'docs/FORMAL_PROJECT_CATALOG.md',
                             'sha256': sha256((ROOT / 'docs/FORMAL_PROJECT_CATALOG.md').read_bytes()).hexdigest(),
                             'scope': 'Existing finite composition-based project classification and hypothetical-model counting convention; historical main counts are not adopted or updated.'},
        'project_scope': 'Source-qualified hypothetical periodic crystal models, not experimental materials or universally distinct chemical substances.',
        'counting_rule': 'One exact reduced-composition bucket; selected fixed-release model bound by complete file and raw row hashes; no extra polymorph or provider-row credit.',
        'admitted_increment': 0, 'rows': rows,
    }


if __name__ == '__main__':
    p = Path(__file__).with_name('identity-taxonomy-decisions.json')
    raw = native.encoded(build())
    if p.exists() and p.read_bytes() != raw:
        raise ValueError('Refusing different existing proposals')
    p.write_bytes(raw)
    print(json.dumps({'rows': 2000, 'sha256': sha256(raw).hexdigest(), 'admitted_increment': 0}))
