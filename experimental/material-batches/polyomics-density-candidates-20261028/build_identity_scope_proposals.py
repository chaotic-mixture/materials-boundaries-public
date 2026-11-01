"""Make finite source-qualified model-scope decisions explicit for independent review."""
from hashlib import sha256
import json
from pathlib import Path

BATCH = Path(__file__).resolve().parent
ROOT = BATCH.parents[2]
FACTS_SHA = '3e89ef4c7b7b41c99acbc330f53b0d6a00f44aa9216dfdbe03f47eb1959e5b61'


def build():
    raw = (BATCH / 'source-fact-candidates.json').read_bytes()
    if sha256(raw).hexdigest() != FACTS_SHA:
        raise ValueError('Different source proposals')
    facts = json.loads(raw)
    baseline_raw = (BATCH / 'baseline-polymer-crosswalk.json').read_bytes()
    if sha256(baseline_raw).hexdigest() != facts['baseline_polymer_crosswalk_sha256']:
        raise ValueError('Different existing polymer crosswalk')
    baseline = json.loads(baseline_raw)
    caution = [{'identity_id': r['identity_id'], 'state_id': r['id'],
                'source_composition_fact': r['state']['composition_or_purity'],
                'disposition': 'Contains a source-reported fluorinated blowing-agent input; no element-disjointness claim. Compare the named foam formulation scope to a hypothetical linear-chain constitution model.'}
               for r in baseline['states'] if 'opteon' in json.dumps(r).lower()]
    rows = []
    for candidate in facts['candidates']:
        key = candidate['operational_graph_key_sha256']
        source = candidate['selected_source_record']
        rows.append({
            'proposed_identity_id': 'mat_polyomics_linear_model_' + key[:24],
            'proposed_identity_kind': 'source_qualified_hypothetical_linear_polymer_constitution_model',
            'constitution_key_scope': 'Frozen restricted-source graph key, subject to independent bridge-block/primitive-period equivalence adjudication; not a universal polymer ontology.',
            'operational_graph_key_sha256': key, 'source_repeat_unit_smiles': source['source_smiles_1'],
            'selected_simulation_uuid_state_only': source['uuid'],
            'source_revision': facts['source_revision'], 'source_sha256': facts['source_sha256'],
            'source_record_index_0_based': source['source_record_index_0_based'],
            'source_record_number_1_based_excluding_header': source['source_record_number_1_based_excluding_header'],
            'source_row_fields_canonical_json_sha256': source['source_row_fields_canonical_json_sha256'],
            'proposed_category': 'polymer',
            'category_basis': 'Author-reported polymer molecular-simulation model; restricted two-port linear repeat connectivity. Fluorine is a cohort filter, not alone a polymer classification or novelty proof.',
            'state_not_identity_factors': ['UUID', 'simulation chain length/count', 'software/preset version', 'tacticity label', 'temperature/pressure state', 'density value'],
            'counting_scope': 'At most one source-qualified restricted constitution model per independently adjudicated primitive connectivity class; no extra credit for representation, source rows, states or repeats.',
            'baseline_scope_relation_proposed': 'Distinct project scope from the existing named products, formulations and network/foam source-qualified references; not a claim that all chemistry or constituents are disjoint.',
            'experimental_existence': 'unknown', 'stable_thermodynamic_phase': 'unknown',
            'stereochemical_identity': 'not_assigned_beyond_source_state_labels',
            'net_charge_scope': 'Molecular net charge zero; individual atom formal charges may occur and are retained.',
            'cross_provider_or_universal_equivalence': 'unresolved',
            'decision': 'proposed_for_independent_finite_scope_adjudication', 'admitted_increment': 0,
        })
    if len(rows) != 1000 or len({r['proposed_identity_id'] for r in rows}) != 1000:
        raise ValueError('Unexpected identity proposal count')
    return {'schema': 'polyomics-finite-model-identity-scope-proposals/1',
            'status': 'producer_proposals_pending_independent_adjudication',
            'source_facts_sha256': FACTS_SHA,
            'baseline_crosswalk_sha256': sha256(baseline_raw).hexdigest(),
            'baseline_identity_ids': [r['id'] for r in baseline['identities']],
            'baseline_scope_cautions': caution,
            'project_scope_policy_reference': {'path': 'docs/FORMAL_PROJECT_CATALOG.md',
                                                'sha256': sha256((ROOT / 'docs/FORMAL_PROJECT_CATALOG.md').read_bytes()).hexdigest(),
                                                'scope': 'Existing finite project distinction among named products/formulations and hypothetical periodic models; no historical published count adopted.'},
            'rows': rows, 'admitted_increment': 0}


if __name__ == '__main__':
    p = BATCH / 'identity-scope-proposals.json'
    raw = (json.dumps(build(), ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf8')
    if p.exists() and p.read_bytes() != raw:
        raise ValueError('Refusing different frozen scope proposals')
    p.write_bytes(raw)
    print(json.dumps({'rows': 1000, 'sha256': sha256(raw).hexdigest(), 'admitted_increment': 0}))
