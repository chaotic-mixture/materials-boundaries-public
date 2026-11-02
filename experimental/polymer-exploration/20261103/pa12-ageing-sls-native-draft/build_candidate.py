"""Build an isolated, source-bound SLS draft; never edit the native tables.

Only Table7 aged moduli and Table8 SLS strength/modulus are selected. A numerical
screen is one piece of evidence; review and admission remain separate decisions.
"""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from materials_boundaries.database import Database

SOURCE = 'zakrecki_cieslik_2025_pa12_ageing'
URL = 'https://www.ebi.ac.uk/europepmc/webservices/rest/PMC12525880/fullTextXML?format=xml'
XML_SHA = '4d930d221c67d38199460f1f80b86a2a724a0b2986a77e09081172d5a83c42d7'
BASELINE = 'aa8308dbec8817ee6551078ed91bedb2a9fb05c7924fd76a9131cc680617a95f'
IDENTITY = 'mat_zakrecki2025_pa12_pa2200'
GRADE = 'grade_zakrecki2025_eos_pa2200'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def evidence(locator, *tags):
    return {'source_id': SOURCE, 'url': URL, 'locator': locator, 'supports': list(tags)}


def reported(value, locator, tags, note=None):
    return {'status': 'reported', 'text': value,
            'evidence': [evidence(locator, *tags)], 'notes': note}


def unknown(note, status='not_reported_in_inspected_source'):
    return {'status': status, 'text': None, 'evidence': [], 'notes': note}


def write_new(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--xml', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    assert digest(args.xml) == XML_SHA
    base = Database()
    assert base.snapshot == BASELINE
    audit = Path(__file__).parent.parent / 'pa12-ageing-source-audit'
    binding = json.loads((audit/'AUDIT_INPUTS_R1.json').read_bytes())
    for name, sha in binding['files_sha256'].items():
        assert digest(audit/name) == sha, name
    index = json.loads((audit/'STATISTICS_INDEX_R1.json').read_bytes())['all_source_summaries']
    selected = [row for row in index if row['technology'] == 'SLS' and
                ((row['table_id'].endswith('007') and row['age_label_literal'] != 'Reference'
                  and row['quantity_label'] == 'source_youngs_modulus') or
                 (row['table_id'].endswith('008') and row['quantity_label'] in
                  ('tensile_strength', 'source_youngs_modulus')))]
    assert len(selected) == 8 and all(row['conditional_cv_interval_overlap'] for row in selected)
    xml = ET.parse(args.xml).getroot()
    tables = {t.get('id'): t for t in xml.findall('.//table-wrap')}
    for row in selected:
        cells = tables[row['table_id']].findall('.//tr')[row['source_body_row']+1]
        literal = [' '.join(''.join(cell.itertext()).split()) for cell in cells]
        offset = 3 if row['quantity_label'] == 'tensile_strength' else 6
        assert literal[offset:offset+3] == [row['mean'], row['sd'], row['cv']]
        assert literal[2] == row['age_label_literal']
    states, properties, selections = {}, [], []
    preparation = 'XML sections2.1–2.2, sec2dot1-materials-18-04478 and sec2dot2-materials-18-04478; Table5'
    test = 'XML section2.3, sec2dot3-materials-18-04478, tensile-testing paragraph'
    exposure = 'XML section2.3, sec2dot3-materials-18-04478, ageing-cycle and calculator paragraphs'
    scope = ('Same-hash Europe PMC XML: sections2.1–2.4, Table5 group definitions, '
             'selected SLS rows of Tables7–8 and article-specific permissions. '
             'Original mean/SD/CV literals cross-checked directly against XML and frozen source index. '
             'No PDF visual inspection, raw-specimen reanalysis, clinical validation or independent scientific review.')
    for row in selected:
        smoothed = row['table_id'].endswith('008')
        hours = row['reported_elapsed_chamber_hours']
        phase = 'reference' if hours is None else hours+'h'
        route = 'dyed_smoothed' if smoothed else 'dyed'
        sid = 'state_zakrecki2025_pa2200_sls_'+route+'_'+phase
        quantity = 'tensile_strength' if row['quantity_label'] == 'tensile_strength' else 'youngs_modulus'
        pid = 'refprop_zakrecki2025_pa2200_sls_'+route+'_'+phase+'_'+quantity
        loc = ('XML Table'+('8' if smoothed else '7')+' ('+row['table_id']+'), SLS / '
               +row['age_label_literal']+' / '+row['treatment_literal'])
        treatment = row['treatment_literal']
        phase_text = ('Unaged reference after selected post-processing' if hours is None else
                      hours+'h accelerated chamber exposure; source label '+row['age_label_literal']+
                      ' is an author-proposed approximate equivalence, not observed natural service time')
        if sid not in states:
            name = 'EOS PA2200 SLS, '+route.replace('_', ' ')+', '+phase.replace('h', ' h')
            states[sid] = {'version': '1.0.0', 'id': sid, 'identity_id': IDENTITY, 'grade_id': GRADE,
                          'name': name, 'names': {lang: name for lang in ('en','zh','ja','de')},
                          'aliases': [], 'source_designation': 'PA2200; SLS / '+row['age_label_literal']+'; '+treatment,
                          'state': {
                'product_form': reported('Horizontally printed tensile specimens, nominal160 x20 x4mm', preparation, ['state']),
                'processing': reported('EOS P396 SLS, study PA2200 material profile; Black01 dye; table treatment '+treatment,
                                       preparation+'; '+loc, ['state'],
                                       'Table route retained literally. Section2.4 lists the equipment in a different order; exact sequence, timings and dye uptake remain unverified.'),
                'temper_or_heat_treatment': unknown('No separate annealing schedule is reported; accelerated exposure is described under conditioning, not assigned as a measured specimen temperature.'),
                'conditioning': reported(phase_text, exposure+'; '+loc, ['state'],
                                         'Moisture equilibration, pre-test recovery/storage interval and actual tensile-test temperature/RH are unknown.'),
                'composition_or_purity': reported('Source identifies EOS PA2200 as a PA12 commercial product', preparation, ['state'],
                                                  'No complete additive package, purity, lot or dye uptake determination.'),
                'reinforcement': unknown('No complete additive/reinforcement assay; absence of additives is not inferred.'),
                'porosity': unknown('No measured porosity is assigned to this condition.'),
                'orientation': reported('HorizontalXY; source identifies X as longest specimen direction', preparation, ['state'])},
                          'source_scope': 'Same study and EOS PA2200 grade as existing source-qualified identity. Different exposure/treatment conditions do not establish new chemical identities or universal grade equivalence.',
                          'evidence': [evidence(preparation+'; '+loc, 'state')], 'property_ids': [], 'evaluation_support': 'catalog_only'}
        states[sid]['property_ids'].append(pid)
        is_modulus = quantity == 'youngs_modulus'
        unit = row['unit']
        conditioning = reported(phase_text+'; selected post-processing '+treatment, exposure+'; '+loc, ['condition'],
                                 'Post-processing and exposure history are not a moisture-equilibration protocol.')
        conditions = {
            'temperature': unknown('Actual tensile-test temperature is not reported.23C calculator reference,38C chamber air and55C black standard are not substituted.'),
            'test_standard': reported('EN ISO527-1, source claim', test, ['condition'], 'Edition and conformity not independently verified.'),
            'test_method': reported('Instron5969 tensile test, source speed1mm/min; nominal specimens160 x20 x4mm; source test-section length115mm', test, ['method','condition'],
                                     '115mm is not certified extensometer gauge length. Stress definition, strain-measurement implementation and exact extraction algorithm are not specified.'),
            'direction': reported('HorizontalXY printing; longest specimen sideX', preparation, ['condition'], 'No isotropy or transverse result inferred.'),
            'conditioning': conditioning,
            'loading_rate': reported('Source test speed1mm/min', test, ['condition']),
            'additional_conditions': [
                {'name': 'test_relative_humidity', 'fact': unknown('Tensile-test RH not reported; exposure RH is not transferred.')},
                {'name': 'post_processing_order', 'fact': unknown('Table treatment and section2.4 list the equipment in different orders; precise operation sequence unresolved.', 'not_verified')},
                {'name': 'post_exposure_recovery', 'fact': unknown('Time and moisture state between selected treatment/exposure and tensile testing not reported.')}]}
        program = ('Q-SUN Xe-3 xenon exposure: source air38C, black standard55C(IBP), '
                   'mixed dry irradiation and irradiation at50%RH, irradiance60W/m2 over300–400nm; '
                   'phase durations, dry-phaseRH and actual specimen temperature not reported')
        conditions['additional_conditions'].append({'name': 'accelerated_ageing_program', 'fact':
            (reported(program, exposure, ['condition']) if hours else
             unknown('Selected unaged reference is not assigned the accelerated exposure program.', 'not_applicable'))})
        definition = ('Source tensile E, labelled modulus of elasticity; strain implementation, fit/window and endpoint handling not reported.' if is_modulus else
                      'Source tensile sigma strength; exact extraction rule, yield/ultimate qualifier and stress convention not reported.')
        discrepancies = [{'description': 'Selected tables list C+DM60+S'+('+PowerfuseS' if smoothed else '')+'; section2.4 lists C+S+DM60'+('+PowerfuseS' if smoothed else '')+'.',
                          'disposition': 'Keep the table label; no certified operation sequence or run time.',
                          'evidence': [evidence(loc+'; XML section2.4, sec2dot4-materials-18-04478', 'source_discrepancy','state')]}]
        if not smoothed:
            companion = next(x for x in index if x['table_id'] == row['table_id'] and x['source_body_row'] == row['source_body_row'] and x['quantity_label'] == 'tensile_strength')
            assert not companion['conditional_cv_interval_overlap']
            discrepancies.append({'description': 'Same-row strength mean/SD/CV literals '+companion['mean']+'/'+companion['sd']+'/'+companion['cv']+' have no overlap under conventionalCV rounding assumptions.',
                                  'disposition': 'Defer that separate strength quantity. No repair and no source-wide scientific pass implied by selecting the modulus.',
                                  'evidence': [evidence(loc+', sigma Mean/Std/CV columns', 'source_discrepancy')]})
        note = ('Source '+('E' if is_modulus else 'sigma')+' Mean '+row['mean']+' '+unit+', Std '+row['sd']+' '+unit+
                '; CV column literal '+row['cv']+'. Preserve all source literals. The conditional conventional percent-CV rounding screen is compatible, not an independent error estimate or scientific validation.')
        prop = {'version':'1.0.0','id':pid,'material_state_id':sid,'quantity':quantity,'quantity_dimension':'pressure',
                'source_property_label':'E (GPa)' if is_modulus else 'σ (MPa)',
                'reported_value':{'kind':'scalar','value_text':row['mean'],'unit_text':unit,'unit_code':unit,'number':row['mean']},
                'evidence_kind':'published_experimental_reference','evaluation_support':'catalog_only','universal_bound':False,'engineering_allowable':False,
                'reporting_basis':'reported_summary','determination_basis':'source_reports_measurement',
                'basis_note':'Original selected SLS source table summary only; no raw-specimen reanalysis, repaired statistic, manufacturer-data substitution or pooled estimate.',
                'conditions':conditions,'density_basis':None,'summary_statistic':'reported_mean',
                'uncertainty':{'type':'reported_standard_deviation','value_text':row['sd'],'number':row['sd'],'unit_text':unit,'unit_code':unit,
                               'scope':loc+', selected '+quantity+' group only','coverage_factor':None,'confidence_level':None,
                               'evidence':[evidence(loc+', Std column','uncertainty')]},
                'uncertainty_status':'reported_standard_deviation','uncertainty_note':note,
                'sample_count':{'value':6,'relation':'exact','scope':'Selected SLS treatment and ageing group, source claim only',
                                'source_statement':'Six tensile specimens per printing technology, post-processing route and ageing group; not independent printing batches.',
                                'evidence':[evidence(preparation+'; '+loc,'sample_count')]},
                'method_definition':{'type':'source_reported_conventional','definition':definition,'extraction_window':None,
                                     'evidence':[evidence(test+'; '+loc,'method')]},
                'source_discrepancies':discrepancies,'source_id':SOURCE,
                'evidence':[evidence(loc+', selected Mean/Std/CV columns','reported_value','summary_statistic','uncertainty','classification')],
                'source_document':{'url':URL,'revision':None,'inspected_on':'2026-11-03','sha256':XML_SHA,'hash_status':'recorded','hash_note':None,
                                   'inspection_scope':scope,'inspection_status':'selected_content_inspected'},
                'scope_note':'Same source-qualified EOS PA2200 identity, selected treatment/exposure only. Reported accelerated-age equivalence is not field lifetime or clinical durability. No engineering allowable or automatic mechanics input.',
                'verification':{'source_inspection_scope':scope,'transcription_cross_check':'completed','independent_scientific_review':False,'raw_data_reanalysis':False}}
        assert row['mean']+' '+unit in note and row['sd']+' '+unit in note and row['cv'] in note
        properties.append(prop)
        selections.append({'property_id':pid, 'state_id':sid, 'source_row':row})
    assert len(states) == 5 and len(properties) == 8
    assert not set(states) & set(base.states)
    assert not {r['id'] for r in properties} & set(base.properties)
    source = deepcopy(base.sources[SOURCE])
    source['urls'].append(URL)
    source['provenance']['curation_date'] = '2026-11-03'
    source['provenance']['method'] = scope
    source['claim_notes'].append('Additional selected SLS scope: Table7 aged moduli and Table8 strength/modulus. Age/treatment states reuse the existing EOS PA2200 identity. Table6 route ambiguity, inconsistent companion statistics, HP identity mapping and elongation quantities remain outside this draft. Conditional CV compatibility does not prove scientific validity.')
    args.output_dir.mkdir(parents=True, exist_ok=False)
    candidate = {'schema':'polymer-pa12-ageing-sls-native-candidate/1','stage':'isolated_native_draft_not_applied_pending_review',
                 'baseline_snapshot':BASELINE,'source_xml_sha256':XML_SHA,
                 'materials':{'schema_version':'1.0.0','identities':[],'grades':[],'records':list(states.values())},
                 'reference_properties':{'schema_version':'1.0.0','records':properties},'sources':{'records':[source]},
                 'increments':{'identities':0,'grades':0,'states':5,'properties':8,'sources':0},'source_metadata_revisions':1}
    write_new(args.output_dir/'native-candidate-r1.json', candidate)
    write_new(args.output_dir/'SELECTION_R1.json', {'schema':'polymer-pa12-ageing-selection/1','selected':selections,
        'already_native_properties':['refprop_zakrecki2025_pa2200_sls_reference_tensile_strength'],
        'deferred_scope':['All Table6 rows: first-route ambiguity','Table7 reference modulus and aged strengths: conditional CV incompatibility',
                          'HP MJF identity/grade mapping','Elongation quantity contract not proposed'],
        'decision_boundary':'Selection for draft only; not reviewed, applied or published.'})
    print(json.dumps({'states':len(states),'properties':len(properties),'new_identities':0,'applied':False,
                      'candidate_sha256':digest(args.output_dir/'native-candidate-r1.json')}))


if __name__ == '__main__':
    main()
