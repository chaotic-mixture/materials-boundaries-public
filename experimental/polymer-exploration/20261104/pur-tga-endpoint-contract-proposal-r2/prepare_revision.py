"""Resolve the independently reviewed R1 concept without rewriting it."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
R1 = HERE.parent / 'pur-tga-endpoint-contract-proposal-r1'


def read(name):
    return json.loads((R1 / name).read_bytes())


def write(name, obj):
    with (HERE / name).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(obj, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def main():
    entry = R1 / 'REVIEW_INPUTS_R1.json'
    assert hashlib.sha256(entry.read_bytes()).hexdigest() == '1b293895d664f39e90baa0594a962c854280e4c9d0724356b261dbe91a33736b'
    review = read('INDEPENDENT_CONCEPT_REVIEW_R1.json')
    assert review['decision'] == 'changes_required' and len(review['findings']) == 3
    proposal = read('CONTRACT_PROPOSAL_R1.json')
    proposal['schema'] = 'unimplemented-TGA-endpoint-contract-concept/2'
    proposal['qualifiers']['specified_mass_loss']['domain'] = 'Fractional mass loss: 0<loss<=100 on the original percent scale. Mass reference basis may remain unknown;unknown basis alone cannot justify a threshold above100. Other source-defined ratios require separate definition/contract review;do not repair or silently admit them.'
    proposal['qualifiers']['specified_mass_loss']['not_allowed'].append('threshold above100 under this fractional-loss contract')
    proposal['qualifiers']['residue_endpoint_temperature']['domain'] = 'Use existing coordinate floors K>=0 and degC>=-273.15;scalar source coordinate,sign/precision retained,no conversion. Includes absolute-zero coordinate boundary without certifying experimental attainability.'
    proposal['unit_roles']['temperature_results_domain'] = 'All three result temperature families and residue endpoint use K>=0/degC>=-273.15. Difference amplitudes nonnegative,no zero-point offset.'
    proposal['unit_roles']['residue_central_unit']['domain'] = 'Nonnegative original remaining-mass/reference-mass percentage including zero;no automatic0–1 rescaling or universal100 cap. Unknown basis is retained and is not by itself scientific justification for values above100;source-defined denominator/corrections and admissibility require review.'
    proposal['uniqueness_and_coverage'][2] = 'Keep existing state/quantity/document/original source-cell locator and core-fact identity semantics. With those identical,only descriptor evidence/display-label/numeric-typography changes cannot create a new coordinate. Unknown-basis note wording cannot inflate coverage. Qualifier numeric normalization must be independent of ambient Decimal context.'
    proposal['implementation_acceptance'][1] = 'K>=0/degC>=-273.15 equivalent coordinate floors for results and endpoint qualifier;reject below-floor coordinates,retain sign/precision;nonnegative temperature-difference amplitudes with no offset'
    proposal['implementation_acceptance'][2] = 'Fractional loss descriptor0<loss<=100;reject zero/negative/>100 or defer other source-defined ratios to another contract. Residue zero accepted/negative rejected,source13.7not0.137;no universal residue100cap and no assertion of scientific validity from unknownbasis'
    proposal['implementation_acceptance'][4] = 'Preserve existing source-cell locator and core-fact duplicate semantics;typed qualifier distinctions admitted,descriptor evidence/typography/unknown-note variations alone cannot inflate coordinates'
    proposal['science_boundaries'].append('Unknown basis does not relax fractional-loss cap or establish scientific validity of residue ratios;do not silently repair/out-of-scope admit source ratios')
    proposal['resolves_review_entry_sha256'] = review['review_inputs_sha256']
    write('CONTRACT_PROPOSAL_R2.json', proposal)
    crosswalk = read('SOURCE_ROLE_CROSSWALK_R1.json')
    from decimal import Decimal
    for row in crosswalk['examples']:
        if row['proposed_quantity'] == 'temperature_at_specified_mass_loss':
            assert 0 < Decimal(row['new_qualifier_examples']['specified_mass_loss']['number']) <= 100
    crosswalk['source_values_changed_from_R1'] = False
    write('SOURCE_ROLE_CROSSWALK_R2.json', crosswalk)
    write('UNIT_REFERENCES_R2.json', read('UNIT_REFERENCES_R1.json'))
    validation = read('VALIDATION_R1.json')
    validation.update(revision_findings_resolved=3, source_values_changed=False, implementation='not_started', scope='Concept revision structure and all8loss descriptors within0..100;not implementation tests')
    write('VALIDATION_R2.json', validation)
    write('REVIEW_RESOLUTION_R2.json', {'prior_review_entry_sha256': review['review_inputs_sha256'], 'prior_decision': review['decision'], 'changes': ['fractional loss0<loss<=100;other ratios separate review;residue no universalcap is not unknownbasis scientific approval', 'coordinate floorsK>=0/C>=-273.15 for result andendpoint;amplitude nooffset', 'preserve sourcecell/corefact uniqueness;descriptor evidence/format/unknownnote no inflation'], 'source_crosswalk_values_changed': False, 'native_runtime_schema_changed': False, 'implementation_mapping_install_admission_approved': False})
    print('R2 concept files created; no native/runtime changes')


if __name__ == '__main__':
    main()
