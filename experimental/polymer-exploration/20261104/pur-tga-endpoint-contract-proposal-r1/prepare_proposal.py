"""Prepare unimplemented typed endpoints for already-reviewed TGA source facts."""
from pathlib import Path
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
SOURCE = OUT.parent / 'pur-dma-tg-tga-followup-source-r1'
sys.path.insert(0, str(ROOT))
from materials_boundaries.database import Database
from materials_boundaries.material_references import QUANTITY_DIMENSIONS, _PROPERTIES_SCHEMA


def read(path):
    return json.loads(path.read_bytes())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(name, value):
    with (OUT / name).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def main():
    source_review = read(SOURCE / 'INDEPENDENT_SOURCE_REVIEW_R1.json')
    assert source_review['decision'] == 'approved' and source_review['review_inputs_sha256'] == sha(SOURCE / 'REVIEW_INPUTS_R1.json')
    leads = read(SOURCE / 'TGA_SOURCE_LEADS_R1.json')['facts']
    assert len(leads) == 28 and len(_PROPERTIES_SCHEMA['$defs']['property']['oneOf']) == 7
    db = Database()
    assert db.snapshot == '4f2f95b2f8635782d8af28412fafa077f93db3786b3953a123d6daec49207513'
    quantities = {
        'thermal_degradation_onset_temperature': {'dimension': 'temperature', 'source_cells': 4, 'required_qualifiers': [], 'meaning': 'Source first TGA onset;unknown onset criterion;may include additive volatilization,not intrinsic neat-polymer decomposition or service limit'},
        'temperature_at_specified_mass_loss': {'dimension': 'temperature', 'source_cells': 8, 'required_qualifiers': ['specified_mass_loss', 'mass_reference_basis'], 'meaning': 'Source endpoint at an explicitly specified positive mass-loss percentage;5% and10% distinct,not melting peaks'},
        'thermal_degradation_rate_peak_temperature': {'dimension': 'temperature', 'source_cells': 12, 'required_qualifiers': ['degradation_peak_ordinal'], 'meaning': 'Source DTG ordinal peak temperature;source1/2/3 retained,not a universal maximum allowed temperature'},
        'tga_residue_percentage': {'dimension': 'dimensionless', 'source_cells': 4, 'required_qualifiers': ['residue_endpoint_temperature', 'mass_reference_basis'], 'meaning': 'Source TGA remaining-solid percentage at specified endpoint;not certified ash or automatically a mass fraction'}
    }
    assert all(n not in QUANTITY_DIMENSIONS for n in quantities)
    qualifiers = {
        'specified_mass_loss': {'shape': 'Scalar original number/value_text/unit_text plus percent_mass_loss role code and nonempty primary condition evidence', 'domain': 'Strictly positive source percentage;do not silently assume initial/dry mass basis or impose an unreported fraction cap', 'example': {'kind': 'scalar', 'value_text': '5', 'number': '5', 'unit_text': '%', 'unit_code': 'percent_mass_loss'}, 'not_allowed': ['zero/negative thresholds', 'percent_elongation role', 'automatic5percent to0.05 conversion', 'interval or comparison as a specified fixed threshold']},
        'degradation_peak_ordinal': {'shape': 'Object with positive integer value and nonempty primary condition evidence', 'domain': 'Source-labelled ordinal>=1,not fitted rank or materialID whitelist', 'examples': [1, 2, 3]},
        'residue_endpoint_temperature': {'shape': 'Scalar original temperature coordinate with degC/K and nonempty primary condition evidence', 'domain': 'Signed Celsius or strictlypositiveKelvin,source precision preserved;not an interval,scan range or automatically shifted coordinate', 'example': {'kind': 'scalar', 'value_text': '700', 'number': '700', 'unit_text': '°C', 'unit_code': 'degC'}},
        'mass_reference_basis': {'shape': 'Existing fact envelope required for mass-loss and residue branches;reported facts need primary condition evidence', 'source_default': {'status': 'not_reported_in_inspected_source', 'text': None, 'evidence': [], 'notes': 'Initial/as-received/dry normalization and correction basis not unambiguously established;do not fill from a graph starting near100%.'}}
    }
    write('CONTRACT_PROPOSAL_R1.json', {'schema': 'unimplemented-TGA-endpoint-contract-concept/1', 'status': 'proposal_only_not_native_schema', 'source_entry_sha256': sha(SOURCE / 'REVIEW_INPUTS_R1.json'), 'source_approval_sha256': sha(SOURCE / 'INDEPENDENT_SOURCE_REVIEW_R1.json'), 'quantities': quantities, 'qualifiers': qualifiers,
          'unit_roles': {'temperature_results': ['degC', 'K'], 'residue_central_unit': {'unit_code': 'percent_tga_residue', 'unit_text': '%', 'dimension': 'dimensionless', 'domain': 'Nonnegative original percentage includingzero;no automatic0–1 rescaling or universal100 cap with unknown massreference'}, 'mass_loss_descriptor_unit': {'unit_code': 'percent_mass_loss', 'unit_text': '%', 'domain': 'Descriptor only,not a legal central unit for any result quantity'}, 'code_scope': 'Internal role identifiers,not differentSI units;physical % symbol unchanged. No wt.%/volume/elongation role inference.'},
          'schema_strategy': ['Add four complete mutuallyexclusive branches after existingseven;keep oldseven branchobjects andlegacy_reported_value literallysame', 'New qualifiers appear only in their own required branches;forbidden in oldquantities and unrelated newTGA branches', 'Temperature result semantic family must extend runtime temperature-domain,absolute amplitude and relative-origin checks without enlarging oldTg/melting schema branch enum', 'Residue nonnegative domain is quantity-specific;all old quantity domains remain unchanged', 'Use existing condition/method/classification evidence tags,not new material-ID exceptions', 'Percent residue unit may extend shared absolute-uncertainty vocabulary,but exact unit/role checks prevent leakage;mass-loss descriptor code never enters central result branches'],
          'statistics': {'centre': 'not_stated for these28', 'selected_n': 'unknown;commonTGAatleast3 separate methodfact,not exact3 or selected-per-cell lowerbound', 'source_plus_minus': 'Reuse reported_plus_minus_unspecified scalar envelope with nonnegative amplitude and unknown statistical interpretation;not meanSD/SE/CI promotion', 'amplitude_units': 'Temperature amplitudes retain Celsius/K difference role with nooffset;residue amplitude same percent_tga_residue code as centre;not relativeCV'},
          'uniqueness_and_coverage': ['Typed masslosslevel,sourcepeakordinal andresidueendpoint/basis must participate in semantic property identity', 'Equal temperature values at5%/10%,or two labelledDTGpeaks,can be distinct coordinates under oneTGAstate', 'Exact qualifier clones areduplicates despite changed labels/evidence/decimal formatting;normalization must be independent of ambientDecimalcontext', 'Four source-qualifiedTGA specimen/pan states planned,not28states/identities;mass/dimensions unknown;no certified physicalcoverage'],
          'presentation': 'Four-language labels for quantities and typedqualifiers/basis;human render and complete query/export must preserve unknownbasis,percent scale,sourceordinal and endpoint temperature. No calculator or engineeringallowable use.',
          'science_boundaries': ['No onset<=T5 ordering repair;unknown onset criterion and unpaired source summaries do not justify cross-record constraints', 'No source Tm5/Tm10 relabel as melting temperatures', 'No residue700C relabel as certified ash,purity or final-mixture massfraction', 'No repair of author values or hidden-draft/curve digitization', 'No transfer of DSC/DMA n,gas orgeometry;TGAplatinumpans ownstate and30–700C10CminN2 method'],
          'implementation_acceptance': ['Public/runtime schema equality and oldseven branch/legacyvalue byte equivalence', 'PositiveKelvin/signedC source forms and uncertainty difference-role checks', 'Residuezero accepted,negative rejected,original13.7not0.137;no global0..100 bound inferred', 'Required typedqualifiers,evidence,basis and wrong-unit/wrong-branch rejection', 'Qualifier-aware semanticduplicate rejection without label or format inflation', 'Undefinedplusminus remains undefined;selectedn unknown', 'Four-language complete descriptor rendering/query/export;noengine', 'Meaningful regression of currentolddata and methods,not fullhistory replay', 'Freeze exact implementation,independentreadonlyreview,then separate28mapping/install/nativeintegration gates'],
          'native_snapshot': db.snapshot, 'native_code_data_changed': False, 'new_native_records': 0, 'implementation': 'not_started', 'tests_installation': 'not_run_proposal_only', 'pushed': False})
    examples = []
    for lead in leads:
        quantity = lead['quantity_concept_only']
        assert quantity in quantities
        is_residue = quantity == 'tga_residue_percentage'
        required = {}
        if quantity == 'temperature_at_specified_mass_loss':
            number = lead['source_descriptor']['source_mass_loss_percent']
            required['specified_mass_loss'] = {'kind': 'scalar', 'value_text': number, 'number': number, 'unit_text': '%', 'unit_code': 'percent_mass_loss'}
        elif quantity == 'thermal_degradation_rate_peak_temperature':
            required['degradation_peak_ordinal'] = {'value': lead['source_descriptor']['source_peak_ordinal']}
        elif is_residue:
            required['residue_endpoint_temperature'] = {'kind': 'scalar', 'value_text': '700', 'number': '700', 'unit_text': '°C', 'unit_code': 'degC'}
        if 'mass_reference_basis' in quantities[quantity]['required_qualifiers']:
            required['mass_reference_basis'] = qualifiers['mass_reference_basis']['source_default']
        examples.append({'source_label': lead['source_label'], 'existing_identity_id': lead['existing_identity_id'], 'source_expression': lead['source_expression'], 'locator': lead['locator'], 'proposed_quantity': quantity, 'quantity_dimension': quantities[quantity]['dimension'], 'centre': {'number': lead['centre_number'], 'value_text': lead['centre_number'], 'unit_code': 'percent_tga_residue' if is_residue else 'degC', 'unit_text': '%' if is_residue else '°C'}, 'undefined_plus_minus': {'number': lead['plus_minus_number'], 'value_text': lead['plus_minus_number'], 'unit_code': 'percent_tga_residue' if is_residue else 'degC', 'unit_text': '%' if is_residue else '°C'}, 'new_qualifier_examples': required, 'summary': 'not_stated', 'n': None, 'scope': 'Partialconcept only,missing full nativeevidenceenvelopes;not schema-valid/admittednativeobjects'})
    write('SOURCE_ROLE_CROSSWALK_R1.json', {'status': 'partial_contract_examples_only', 'examples': examples, 'source_cells': len(examples), 'planned_properties_states': [28, 4], 'new_identities': 0, 'native_applied': False})
    write('UNIT_REFERENCES_R1.json', {'read_on': '2026-11-04', 'references': [{'url': 'https://www.nist.gov/pml/special-publication-811/nist-guide-si-chapter-7-rules-and-style-conventions-expressing-values', 'locator': '§7.10.2', 'facts': ['Percent symbol denotes0.01 for quantities of dimensionone', 'Unit symbol alone doesnot identify a mass/volume fraction or normalization basis']}, {'url': 'https://www.nist.gov/pml/special-publication-811/nist-guide-si-chapter-8', 'locator': '§8.5 and§8.6.10', 'facts': ['Celsius/Kelvin temperature differences have equal numerical magnitudes', 'Massfraction uses componentmass divided by mixturemass;not automatically the article TGAresiduepercent']}], 'proposal_inferences': ['Keep unitnumber/scale and normalizationbasis separate', 'No automatic temperatureoffset on amplitudes or percentconversion of source values', 'No normative fraction cap for a source ratio with unknown massreference'], 'source_mass_normalization_or_standard_compliance_verified': False})
    write('VALIDATION_R1.json', {'scope': 'Proposalstructure/crosswalkcounts/unsupportedquantity guards,not implementation tests', 'source_facts': 28, 'quantity_families': 4, 'planned_states': 4, 'all_new_quantities_unsupported_currently': True, 'current_schema_branches': 7, 'native_snapshot': db.snapshot, 'native_code_data_changed': False, 'implementation_tests_installation_fullhistory': 'not_run', 'pushed': False})
    print(json.dumps({'source_leads': 28, 'proposed_quantities': 4, 'planned_states': 4, 'native_changed': False, 'implementation': 'not_started'}))


if __name__ == '__main__':
    main()
