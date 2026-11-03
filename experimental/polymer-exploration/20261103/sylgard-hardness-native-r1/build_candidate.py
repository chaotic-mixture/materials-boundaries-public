"""Build five existing-material hardness specimen states after source approval."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from jsonschema import Draft202012Validator, FormatChecker
from materials_boundaries.database import Database, read_snapshot
from materials_boundaries.material_presentation import render_material_catalog

AREA = ROOT / 'experimental/polymer-exploration/20261103'
OUT = Path(__file__).resolve().parent


def read(path):
    return json.loads(path.read_bytes())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def main():
    dest = Path(sys.argv[1]).resolve()
    assert not dest.exists() and not dest.is_relative_to(ROOT)
    proposal = AREA / 'sylgard-hardness-source-draft-r1'
    manifest = read(proposal / 'REVIEW_INPUTS_R1.json')
    review = read(proposal / 'INDEPENDENT_SOURCE_REVIEW_R1.json')
    assert review['decision'] == 'approved'
    assert review['review_inputs_sha256'] == sha(proposal / 'REVIEW_INPUTS_R1.json')
    for name, digest in manifest['repo_files_sha256'].items():
        assert sha(ROOT / name) == digest, name
    for name, digest in manifest['external_files_sha256'].items():
        assert sha(Path(name)) == digest, name
    facts = read(proposal / 'SOURCE_FACTS_R1.json')
    before = Database()
    assert before.snapshot == facts['baseline_snapshot']
    source = facts['source_id']
    url = facts['url']
    state_template = before.states['state_dow_corning_sylgard184_johnston2014_100c']
    property_template = before.properties['refprop_dow_corning_sylgard184_johnston2014_25c_tensile_strength']
    properties, states = [], []

    def ev(locator, supports):
        return {'source_id': source, 'url': url, 'locator': locator, 'supports': supports}

    def unknown(note):
        return {'status': 'not_reported_in_inspected_source', 'text': None, 'evidence': [], 'notes': note}

    def fact(text, locator, note=None, tag='condition'):
        return {'status': 'reported', 'text': text, 'evidence': [ev(locator, [tag])], 'notes': note}

    methodloc = 'Retained PDF p.4 section3.3 hardness testing;pp.5-6 section4.3;Table5 p.6'
    statloc = 'Retained PDF p.4 section4 all specified errors95%CI;pp.5-6 section4.3 four samples and eight locations per sample;Table5 p.6'
    statscope = 'Surface readings are averaged in section3.3; group estimator, CI estimand/construction, averaging order, coverage factor and independent production batches are unreported.'
    preparationloc = 'Retained PDF pp.2-3 sections2.1-2.3 alltestpieces preparation,compression-mold hardness linkage andTable1; p.3 section3 cooling/testingtime'
    for row in facts['rows']:
        temp = row['cure_temperature_C']
        pid, sid = row['new_property_id'], row['proposed_state_id']
        assert pid not in before.properties and sid not in before.states
        tableloc = f'Retained PDF p.6 Table5,{temp}C cure row,Hardness(Shore A)'
        description = ('Hand-held Shore Instruments Type A-2 durometer, source ASTM D2240-05(2010)type A; '
                       'read on complete indentation and average repeated locations; no exact numerical dwell, '
                       'approach rate, applied force, hardness-test T/RH, calibration or test-face axis established. '
                       'Four specimens per cure temperature, eight locations each; CI construction and group aggregation unknown.')
        prop = deepcopy(property_template)
        prop.update(id=pid, version='1.0.0', material_state_id=sid, quantity='shore_a_hardness',
                    quantity_dimension='dimensionless', source_property_label='Hardness (Shore A)')
        prop['reported_value'].update(number=row['number'], value_text=row['number'], unit_code='shore_a_scale', unit_text='Shore A')
        prop['basis_note'] = 'Table5 source hardness scalar; repeated surface readings averaged, but a specimen-wise group mean or exact averaging order is not established. ' + statscope
        prop['summary_statistic'] = 'reported_value'
        prop['conditions'] = {
            'temperature': unknown('Hardness-test temperature not separately stated;21C tensile,20C compression,22C cooling and cure temperature are not hardness-test ambient.'),
            'test_standard': fact('ASTM D2240-05(2010)type A', methodloc, 'Source citation; independent compliance and calibration not verified.'),
            'test_method': fact(description, methodloc),
            'direction': unknown('Hardness-test face and material-axis relation not established; no isotropy claim.'),
            'conditioning': fact('General cured specimens cooled1h at laboratory22C before demolding; all mechanical tests within2h after end of cure', preparationloc, 'Processing/cooling timing only; hardness-specific RH, moisture equilibrium, order and preloading unknown.'),
            'loading_rate': unknown('Hardness approach/application rate unreported; do not transfer tensile254mm/min or compression20mm/min.'),
            'additional_conditions': [
                {'name': 'hardness_test_relative_humidity', 'fact': unknown('No hardness-specific RH supplied;39% is reported for tensile/compression methods only.')},
                {'name': 'indentation_reading_timing', 'fact': fact('Read as soon as complete indentation occurred', methodloc, 'The5-15s relaxation discussion is context, not an assigned dwell duration.')},
                {'name': 'hardness_applied_force', 'fact': unknown('Hardness force not supplied; no transfer of NR488g or NBR8.05N.')},
                {'name': 'locations_per_specimen', 'fact': fact('Eight different locations per hardness sample', statloc, 'Four samples per cure temperature;32locations are not32 independent specimens or batches.')},
                {'name': 'hardness_specific_cure_duration', 'fact': unknown('No separately labelled hardness cure-duration column; Table1 compression durations are context, not an exact hardness-duration assignment.')},
                {'name': 'compression_cure_context_only', 'fact': fact(f"Table1 compression-mold corrected duration at{temp}C:{row['compression_table1_duration_context_only']}", preparationloc, 'Context only, not transferred to confirmed hardness-specific duration; no arithmetic correction of200C printed24min.')},
            ],
        }
        uncertainty = prop['uncertainty']
        uncertainty.update(number=row['uncertainty_number'], value_text=row['uncertainty_number'],
                           unit_code='shore_a_scale', unit_text='Shore A',
                           scope=f"Reported plus/minus{row['uncertainty_number']} absolute Shore A scale points of source-stated95%CI forTable5 {temp}C cure hardness; estimand and construction unknown.",
                           evidence=[ev(tableloc, ['uncertainty']), ev(statloc, ['uncertainty', 'sample_count'])])
        uncertainty['estimand'] = unknown('Hardness CI estimand not identified; point/surface averaging does not establish a group population-mean CI.')
        uncertainty['construction'] = unknown(statscope + ' No SD/SE/t conversion inferred.')
        prop['uncertainty_note'] = f"{row['number']} plus/minus{row['uncertainty_number']} Shore A: source-stated95%CI, notSD/SE; absolute scale points. Four specimens, eight locations each, not32 independent samples. " + statscope
        prop['sample_count'] = {'value': 4, 'relation': 'exact', 'scope': f'Four hardness specimens at{temp}C cure temperature; eight locations per specimen, not32 independent samples; production-batch count unknown.',
                                'source_statement': 'Section4.3 reports four PDMS samples per temperature, each at eight locations.',
                                'evidence': [ev(statloc, ['sample_count'])]}
        prop['method_definition'].update(definition=description, extraction_window=None, evidence=[ev(methodloc, ['method', 'classification'])])
        prop['source_discrepancies'] = [{
            'description': 'Hardness specimens are linked to the compression-mold family, butTable1 labels only tensile and compression duration columns; hardness-specific duration is not separately supplied.',
            'disposition': 'Separate hardness specimen states retain reported cure temperature; compression durations remain explicit context, not confirmed hardness duration. Do not attach to tensile dumbbells or infer numerical standard geometry.',
            'evidence': [ev(preparationloc, ['source_discrepancy', 'state'])],
        }]
        scope = f'Retained PDF pp.1-6 visually checked: article CC BY3.0,hardnessTable5 {temp}C row,sections3.3/4.3 and common95%CI statement,preparation/temperature and cure-duration boundary. No raw-data,calibration,compliance or latest-notice audit.'
        prop['source_document'].update(inspected_on='2026-11-03', inspection_scope=scope)
        prop['verification']['source_inspection_scope'] = scope
        prop['scope_note'] = (f'Commercial Sylgard184,10:1parts at{temp}C cure,ratio mass/volume basis unreported; not pure/unfilled PDMS. '
                              'Separate compression-mold-family hardness specimen state; numerical geometry and exact hardness cure duration not established. '
                              'Empirical Shore A and source95%CI only; no modulus/crossscale/stress/energy conversion,engine input,universal bound or engineering allowable. '
                              'Cooling22C is not testtemperature or moisture equilibrium. Four specimens with repeated locations are not independent batches; no new compression/shear/bulk properties.')
        prop['evidence'] = [ev(tableloc, ['reported_value', 'classification']), ev(statloc, ['uncertainty', 'sample_count']), ev(methodloc, ['method', 'condition'])]
        state = deepcopy(state_template)
        names = {'en': f'Sylgard184,10:1parts,{temp}C hardness specimens; exact cure duration unknown',
                 'zh': f'Sylgard184，10:1份，{temp}°C固化硬度试样；确切固化时长未知',
                 'ja': f'Sylgard184、10:1部、{temp}°C硬化硬さ試験片；正確な硬化時間不明',
                 'de': f'Sylgard184,10:1Teile,{temp}°C Härteproben;genaue Härteproben-Härtungsdauer unbekannt'}
        state.update(id=sid, version='1.0.0', name=names['en'], names=names, aliases=[], property_ids=[pid])
        state['state']['product_form'] = fact('Cured Sylgard184 hardness specimen;source-linked compression-mold family', preparationloc, 'No numerical specimen dimensions inferred from ASTM;actual geometry/compliance not independently established.', 'state')
        state['state']['temper_or_heat_treatment'] = fact(f'Cure temperature{temp}C;exact hardness-specific cure duration not separately supplied', tableloc, 'Table1 compression duration is context only. Degree of cure is not analytically measured.', 'state')
        # Replace all inherited preparation references to the tensile state.
        for key in ('processing', 'conditioning', 'composition_or_purity', 'porosity'):
            state['state'][key]['evidence'] = [ev(preparationloc, ['state'])]
        state['state']['conditioning'] = deepcopy(prop['conditions']['conditioning'])
        state['state']['conditioning']['evidence'] = [ev(preparationloc, ['condition', 'state'])]
        state['state']['orientation'] = unknown('Hardness indentation face/axis not characterized; no isotropy inferred.')
        state['source_scope'] = f'Separate{temp}C hardness specimen state under existing Sylgard184 identity/grade. Hardness-specific duration and numerical geometry unestablished;compression times remain context. No tensile property moved or changed.'
        state['evidence'] = [ev(preparationloc, ['state']), ev(tableloc, ['state'])]
        states.append(state)
        properties.append(prop)
    data = deepcopy(before.data)
    data['materials']['records'].extend(states)
    data['reference_properties']['records'].extend(properties)
    src = deepcopy(before.sources[source])
    src['claim_notes'].append('2026-11-03 hardness supplement:Table5 five cure temperatures,ShoreA/source95%CI,n4specimens x8locations. Separate hardness states;hardness-specific cure duration/numerical geometry/testT/RH/calibration unknown. CompressionTable1 durations are context only;no transfer of tensile states,compression/shear/bulk values or crossscale/modulus conversion.')
    data['sources']['records'] = [src if s['id'] == source else s for s in data['sources']['records']]
    after = Database(data)
    contracts = after.validate_scientific_contracts()
    assert len(after.properties) == 5306 and len(after.states) == 5201
    assert all(after.properties[k] == v for k, v in before.properties.items())
    assert all(after.states[k] == v for k, v in before.states.items())
    assert after.identities == before.identities and after.grades == before.grades
    assert set(after.sources) == set(before.sources)
    for name in data:
        Draft202012Validator(read(ROOT / 'schemas' / (name + '.schema.json')), format_checker=FormatChecker()).validate(data[name])
    dest.mkdir(parents=True)
    (dest / 'native-tables').mkdir()
    for name, value in data.items():
        write(dest / 'native-tables' / (name + '.json'), value)
    write(dest / 'native-candidate-r1.json', {'baseline_snapshot': before.snapshot, 'stage': 'not_applied',
          'materials': {'identities': [], 'grades': [], 'records': states},
          'reference_properties': {'records': properties}, 'sources': {'records': [src]}})
    counts = {}
    for phase, db in [('before', before), ('after', after)]:
        target = dest / 'source-exports' / phase
        db.export(target, source=source)
        _, joined = read_snapshot(target)
        assert joined == {r['property']['id']: r for r in db.records(source=source)}
        counts[phase] = len(joined)
    assert counts == {'before': 10, 'after': 15}
    for lang in ('en', 'zh', 'ja', 'de'):
        with patch('materials_boundaries.catalog.read_catalog', side_effect=lambda n: data[n]):
            text = render_material_catalog({'schema_version': '1.0.0', 'records': properties}, 'reference-properties', lang)
        assert all(f['number'] in text and f['uncertainty_number'] in text for f in facts['rows'])
        assert 'Shore A' in text and '95%' in text and 'unknown' in text
        (dest / ('render-' + lang + '.txt')).write_text(text, encoding='utf-8', newline='\n')
    write(dest / 'VALIDATION_R21.json', {'baseline_snapshot': before.snapshot, 'preview_snapshot': after.snapshot,
          'properties': 5306, 'states': 5201, 'new_properties': 5, 'new_states': 5, 'new_identities_grades_sources': 0,
          'all_old5301properties_and5196states_complete_unchanged': True, 'source_change': 'One appended claim_note only.',
          'schema_format': 'passed', 'current_graph': contracts, 'complete_source_export': counts,
          'four_languages': 'passed', 'native_applied': False, 'installed': 'not_run', 'new_test_suite': 'not_run_data_only_existing_contract',
          'full_history_regression': 'not_run', 'pushed': False})
    for name in ('native-candidate-r1.json', 'VALIDATION_R21.json'):
        (OUT / name).write_bytes((dest / name).read_bytes())
    print(json.dumps({'snapshot': after.snapshot, 'properties': 5306, 'states': 5201, 'source_exports': counts}))


if __name__ == '__main__':
    main()
