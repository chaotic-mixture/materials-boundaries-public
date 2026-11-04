"""Build unapplied TGA candidates only after exact implementation approval."""
from copy import deepcopy
from pathlib import Path
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
SOURCE = OUT.parent / 'pur-dma-tg-tga-followup-source-r1'
IMPLEMENTATION = OUT.parent / 'pur-tga-contract-implementation-r1'
sys.path.insert(0, str(ROOT))


def read(path):
    return json.loads(path.read_bytes())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(name, obj):
    with (OUT / name).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(obj, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def main():
    entry = IMPLEMENTATION / 'REVIEW_INPUTS_R1.json'
    assert sha(entry) == 'c0ab151b950ce95a63fd13cb84a065af7bfe89fc42dbb7280cfcb0ff6158f34d'
    approval = read(IMPLEMENTATION / 'INDEPENDENT_IMPLEMENTATION_REVIEW_R1.json')
    assert approval['decision'] == 'approved' and approval['review_inputs_sha256'] == sha(entry)
    assert all(sha(ROOT / name) == digest for name, digest in read(entry)['repo_files_sha256'].items())
    from materials_boundaries.database import Database
    from materials_boundaries.material_references import validate_material_catalog
    leads = read(SOURCE / 'TGA_SOURCE_LEADS_R1.json')
    sid = leads['source_id']
    pdf = 'https://mdpi-res.com/d_attachment/polymers/polymers-16-00942/article_deploy/polymers-16-00942.pdf'

    def evidence(locator, *supports):
        return {'source_id': sid, 'url': pdf, 'locator': locator, 'supports': list(supports)}

    def fact(text=None, locator=None, notes=None, role='condition'):
        return {'status': 'reported' if text is not None else 'not_reported_in_inspected_source',
                'text': text, 'evidence': [evidence(locator, role)] if locator else [], 'notes': notes}

    before = Database()
    assert before.snapshot == '4f2f95b2f8635782d8af28412fafa077f93db3786b3953a123d6daec49207513'
    data = deepcopy(before.data)
    states, properties = [], []
    for label in ['LPO-1', 'LPO-2', 'SPO-2', 'SPO-3']:
        code = label.lower().replace('-', '')
        parent = before.states[f'state_ivdre2024_{code}_rigid_pur_dma_cylinder']
        state = deepcopy(parent)
        state.update(id=f'state_ivdre2024_{code}_rigid_pur_tga_platinum_pan', version='1.0.0', property_ids=[])
        state['name'] = f'Ivdre 2024 {label} rigid PUR, TGA sample in platinum pan'
        state['names'] = {'en': state['name'], 'zh': f'Ivdre 2024 {label} 硬质PUR，铂盘热重样品',
            'ja': f'Ivdre 2024 {label} 硬質PUR、白金パン中の熱重量試料',
            'de': f'Ivdre 2024 {label} PUR-Hartschaum, TGA-Probe in Platinschale'}
        state['source_designation'] = f'{label}, Table9 formulation and Table11 TGA endpoints'
        state['state']['product_form'] = fact('Rigid PUR sample tested in platinum TGA pan', 'PDF p8 §2.8 final TGA paragraph;p20 Table11',
            'Pan material is reported;selected sample mass,dimensions and sampling location are unknown. No DMA cylinder,DSC sample mass or density plate transfer.', 'state')
        state['state']['conditioning'] = fact(notes='TGA-specific RH,equilibration,storage,drying and prior heating unknown;24h room-temperature cure is processing only.')
        state['state']['orientation'] = fact(notes='TGA sampling location and relation to foam-rise direction unknown;no isotropy or DMA compression direction inferred.')
        state['state']['porosity']['notes'] = 'Source formulation-group closed-cell content,not total porosity,every selected TGA specimen or temperature-resolved pore measurement.'
        state['source_scope'] = 'Existing optimized formulation identity;distinct TGA platinum-pan context with unknown sample mass/dimensions. Shared formulation and curing do not establish identical specimens or conditioning across DMA,DSC,density and TGA. Seven endpoint facts share one state,not seven identities or certified samples.'
        state['evidence'] = [evidence(f'PDF pp7–8,16,20 §§2.7–2.8/Table9/Table11,{label}', 'material_identity', 'state')]
        template = before.properties[parent['property_ids'][0]]
        selected = [lead for lead in leads['facts'] if lead['source_label'] == label]
        assert len(selected) == 7 and all(lead['existing_identity_id'] == parent['identity_id'] for lead in selected)
        for lead in selected:
            quantity = lead['quantity_concept_only']
            prop = deepcopy(template)
            unit, text = ('percent_tga_residue', '%') if quantity == 'tga_residue_percentage' else ('degC', '°C')
            prop.update(id=f"refprop_ivdre2024_{code}_tga_{lead['endpoint_role'].lower()}", material_state_id=state['id'],
                version='1.0.0', quantity=quantity, quantity_dimension='dimensionless' if quantity == 'tga_residue_percentage' else 'temperature',
                source_property_label=lead['source_row_label'], reported_value=dict(kind='scalar', number=lead['centre_number'],
                value_text=lead['centre_number'], unit_code=unit, unit_text=text), reporting_basis='not_stated', summary_statistic='not_stated', density_basis=None)
            prop['basis_note'] = f"Table11 source expression {lead['source_expression']};centre aggregation and ± meaning unspecified. Visible final table and XML cell transcribed,not curve digitization or hidden-draft text. Source Tm5%/Tm10% are loss endpoints,not melting peaks."
            prop['uncertainty'] = dict(type='reported_plus_minus_unspecified', number=lead['plus_minus_number'], value_text=lead['plus_minus_number'],
                unit_code=unit, unit_text=text, scope='Source Table11 symmetric ± amplitude;statistical interpretation and selected n unconfirmed.', coverage_factor=None, confidence_level=None,
                evidence=[evidence(lead['locator'], 'uncertainty')])
            prop['uncertainty_status'] = 'reported_plus_minus_unspecified'
            prop['uncertainty_note'] = 'Original ± retained without inference of mean,SD,SE,CI,confidence level or relative percentage uncertainty;temperature amplitude is a difference with no zero-point shift.'
            prop['sample_count'] = dict(value=None, relation='not_reported', scope='Contributors to this selected table cell and independent batch count unknown.',
                source_statement='TGA method states three or more parallel samples;not exact3 and not unambiguously the selected-cell contributor count. Preserved separately as common method context.',
                evidence=[evidence('PDF p8 §2.8 final TGA paragraph;p20 Table11', 'sample_count')])
            prop['conditions'] = {
                'temperature': fact('TGA heating program30–700°C at10°C/min', 'PDF p8 §2.8 TGA paragraph', 'Program,not ambient temperature or selected endpoint value.'),
                'test_standard': fact(notes='No TGA standard named in inspected method;static compression ISO844 and closed-cell ISO4590 not transferred.'),
                'test_method': fact('TA Instruments Discovery TGA with autosampler,platinum pans,nitrogen;TRIOS5.0.0.44608 and OriginPro2021 9.8.0.200',
                    'PDF p8 §2.8 TGA paragraph;p20 Table11/footnotes', 'Sample mass/dimensions,gas flow/purity,onset criterion,derivative/smoothing/peak selection and baseline corrections unknown.'),
                'direction': fact(notes='TGA sample location and orientation relative to foam rise unknown;not a mechanical loading axis.'),
                'conditioning': fact(notes='TGA-specific RH,equilibration,drying,storage and prior heating unknown;no transfer of DMA geometry,DSC second heat or water immersion.'),
                'loading_rate': fact(notes='No mechanical loading rate applies to the selected thermal mass endpoint;heating rate retained under temperature program.'),
                'additional_conditions': [
                    {'name': 'TGA_atmosphere', 'fact': fact('Nitrogen', 'PDF p8 §2.8 TGA paragraph', 'Flow,purity and residual oxygen unknown.')},
                    {'name': 'common_method_parallel_samples', 'fact': fact('Three or more parallel samples examined and tested', 'PDF p8 §2.8 final TGA paragraph', 'Common method only,not exact3 or a selected-cell lowerbound.')},
                    {'name': 'source_endpoint_definition', 'fact': fact(lead['source_row_label'], lead['locator'], 'Source Table11 endpoint/footnote role retained;not a universal service-temperature or mechanical limit.')},
                    {'name': 'sample_mass_and_normalization', 'fact': fact(notes='Sample mass,as-received/dry/initial reference and baseline correction basis unknown;graph starting near100% is not proof.')},
                ],
            }
            prop['method_definition'] = dict(type='source_reported_conventional', definition='Source Table11 TGA endpoint;Discovery TGA/autosampler,platinum pan,30–700°C at10°C/min under nitrogen. Onset criterion,DTG extraction,source centre estimator,± interpretation and exact selected-cell n unknown.',
                extraction_window=None, evidence=[evidence('PDF p8 §2.8 final TGA paragraph;p20 Table11/footnotes', 'method', 'classification')])
            prop['evidence'] = [evidence(lead['locator'], 'reported_value', 'classification', 'uncertainty'), evidence('PDF p8 §2.8 TGA paragraph;p20 Table11/footnotes', 'method', 'condition')]
            prop['source_discrepancies'] = []
            if label == 'SPO-2' and lead['endpoint_role'] in ('first_onset', 'mass_loss_5_percent'):
                prop['source_discrepancies'] = [dict(description='Source SPO-2 T5%=139°C is below its first onset149°C.', disposition='Keep both literal table cells;unknown onset criterion and unpaired summaries do not justify ordering repair.', evidence=[evidence('PDF p20 Table11 SPO-2 first onset andTm5% cells', 'source_discrepancy')])]
            inspection = 'Official23pagePDF selected method p8 and visible final Table11/footnotes p20 inspected;XML Table11 corroborates exact source cells. Earlier preparation/identity/license inspection retained. No raw-data fit,curve digitization,experimental replication or latest-notice confirmation.'
            prop['source_document'].update(inspection_scope=inspection)
            prop['verification'].update(source_inspection_scope=inspection)
            prop['scope_note'] = 'Study-specific TGA source endpoint;original centre and undefined ± retained. Exact n,mass reference,conditioning,calibration and extraction details unknown. Source onset may include additive/low-molecular volatilization;residue not certified ash,DTG peak not service limit,Tm loss label not melting peak. No numerical repair,unit normalization or cross-test sample-count transfer.'
            if quantity == 'temperature_at_specified_mass_loss':
                number = lead['source_descriptor']['source_mass_loss_percent']
                prop['specified_mass_loss'] = dict(kind='scalar', number=number, value_text=number, unit_code='percent_mass_loss', unit_text='%', evidence=[evidence(lead['locator'], 'condition')], notes='Source Table11 fixed fractional loss coordinate;mass reference unknown,not percent elongation.')
            elif quantity == 'thermal_degradation_rate_peak_temperature':
                prop['degradation_peak_ordinal'] = dict(value=lead['source_descriptor']['source_peak_ordinal'], evidence=[evidence(lead['locator'], 'condition')], notes='Source-labelled DTG peak ordinal,not a recomputed peak rank or material identifier.')
            elif quantity == 'tga_residue_percentage':
                prop['residue_endpoint_temperature'] = dict(kind='scalar', number='700', value_text='700', unit_code='degC', unit_text='°C', evidence=[evidence('PDF p20 Table11 residue row andfootnote3', 'condition')], notes='Solid residue at source endpoint700°C;not ambient or onset temperature.')
            if quantity in ('temperature_at_specified_mass_loss', 'tga_residue_percentage'):
                prop['mass_reference_basis'] = fact(notes='Initial/as-received/dry reference mass and baseline correction basis unconfirmed;source percentage retained without conversion or validity inference.')
            state['property_ids'].append(prop['id'])
            properties.append(prop)
        states.append(state)
    baseline_source = before.sources[sid]
    proposed_source = deepcopy(baseline_source)
    proposed_source['claim_notes'].append('Selected Table11 TGA endpoints for existing LPO-1/LPO-2/SPO-2/SPO-3:28 source facts under4pan states;original ± undefined,per-cell n and mass reference unknown. Tm loss labels not melting peaks,residue not certified ash,DTG peaks not service limits.30–700°C10°C/min nitrogen is program;no source value repair or raw assets bundled. Separate mapping/admission review required.')
    data['materials']['records'].extend(states)
    data['reference_properties']['records'].extend(properties)
    data['sources']['records'] = [proposed_source if source['id'] == sid else source for source in data['sources']['records']]
    validate_material_catalog(*(data[name] for name in ('materials', 'reference_properties', 'sources')))
    after = Database(data)
    assert len(states) == 4 and len(properties) == 28
    assert data['materials']['records'][:-4] == before.data['materials']['records']
    assert data['reference_properties']['records'][:-28] == before.data['reference_properties']['records']
    assert before.identities == after.identities and before.grades == after.grades
    write('NEW_STATES_R1.json', states)
    write('NEW_PROPERTIES_R1.json', properties)
    write('SOURCE_UPDATE_PROPOSAL_R1.json', {'baseline_source': baseline_source, 'proposed_source': proposed_source, 'changed_fields': ['claim_notes'], 'native_applied': False})
    write('VALIDATION_R1.json', {'baseline_snapshot': before.snapshot, 'candidate_snapshot': after.snapshot, 'candidate_properties': len(after.properties), 'candidate_states': len(after.states), 'new_properties_states': [28, 4], 'new_identities_grades_sources': 0, 'all_old5384properties5258states_unchanged': True, 'candidate_graph': 'passed', 'native_applied': False, 'installation': 'not_run', 'pushed': False})
    print(json.dumps({'candidate_properties': len(after.properties), 'candidate_states': len(after.states), 'snapshot': after.snapshot, 'native_applied': False}), flush=True)


if __name__ == '__main__':
    main()
