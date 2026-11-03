"""Prepare source-qualified Sylgard compression references, never engine inputs."""
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
BASE = '75969436917b8e2eb4e1ce12a0240b6f75903995f0290f8b0635ed6f583dfe2c'


def read(path): return json.loads(path.read_bytes())
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def main():
    dest = Path(sys.argv[1]).resolve()
    assert not dest.exists() and not dest.is_relative_to(ROOT)
    proposal = AREA / 'sylgard-compression-source-contract-r1'
    review = read(proposal / 'INDEPENDENT_SOURCE_REVIEW_R3.json')
    assert review['decision'] == 'approved'
    assert review['review_inputs_sha256'] == sha(proposal / 'REVIEW_INPUTS_R3.json')
    manifest = read(proposal / 'REVIEW_INPUTS_R3.json')
    archive = read(proposal / 'BASELINE_CONTRACT_BINDING_R3.json')
    for name, digest in manifest['repo_files_sha256'].items():
        if sha(ROOT / name) != digest:
            old = archive[name]
            assert sha(ROOT / old['archive_path']) == digest == old['sha256'], name
    for name, digest in manifest['external_files_sha256'].items():
        assert sha(Path(name)) == digest, name
    facts = read(proposal / 'SOURCE_CONTRACT_PROPOSAL_R3.json')
    before = Database()
    assert before.snapshot == BASE
    source, url = facts['source_id'], facts['url']
    template_state = before.states['state_dow_corning_sylgard184_johnston2014_100c']
    template_property = before.properties['refprop_dow_corning_sylgard184_johnston2014_25c_tensile_strength']
    states, properties, mapping_facts = [], [], []
    methodloc = 'Retained PDF p.4 section3.2 compression testing; p.5 section4.2 andFigure6'
    prep = 'Retained PDF pp.2-3 sections2.1-2.3,Table1 compression column; p.3 section3 cooling/testing time'
    statloc = 'Retained PDF p.4 section4 specified errors95%CI; p.5 Table3/section4.2 and p.6 Table5;compression n not explicitly stated in inspected method/result'

    def ev(locator, supports): return {'source_id': source, 'url': url, 'locator': locator, 'supports': supports}
    def unknown(note): return {'status': 'not_reported_in_inspected_source', 'text': None, 'evidence': [], 'notes': note}
    def fact(text, locator, note=None, tags=('condition',)):
        return {'status': 'reported', 'text': text, 'evidence': [ev(locator, list(tags))], 'notes': note}

    unit_issue = {
        'description': 'Abstract labels the UCS range inGPa, whileTables3/5 andFigure6 useMPa. This is a source conflict, not a resolved unit correction.',
        'disposition': 'Retain the selected tableMPa literals. Do not multiply by1000, repair the abstract or claim scientific unit verification; the abstract conflict concerns UCS and does not establish a new Ec unit.',
        'evidence': [ev('RetainedPDFp.1 abstract; p.5 Table3/Figure6; p.6 Table5', ['source_discrepancy'])],
    }
    range_issue = {
        'description': 'Abstract appends up to40%strain with ambiguous scope; section4.2 describes approximately linear below55% then nonlinear untilfailure; Figure6 extends beyond these stated regions.',
        'disposition': 'Neither40% nor55% is assigned as an actual modulus-fit window, UCS evaluation window or failure criterion. Extraction/averaging remain unknown; no graph digitization or numerical repair.',
        'evidence': [ev('RetainedPDFp.1 abstract; p.5 section4.2/Figure6', ['source_discrepancy', 'method'])],
    }
    modulus_issue = {
        'description': 'Page6 sections4.5/conclusion explicitly claim Ec approximatelytwo orders higher thanYoung modulus and an opposite cure-temperature trend; actual extraction and its relationship toFigure6 are unresolved.',
        'disposition': 'Keep the author-labelled compressive_modulus with this anomalous source relationship explicit. Do not certify a small-strain/tangent/secant/global constant or replace values fromYoung, derivatives, secants, multipliers or assumedPoisson ratio.',
        'evidence': [ev('RetainedPDFp.6 sections4.5/conclusion; p.5 section4.2/Figure6/7', ['source_discrepancy', 'method'])],
    }
    for row in facts['rows']:
        temp = row['cure_temperature_C']
        duration = row['corrected_compression_cure_duration']
        sid = f'state_dow_corning_sylgard184_johnston2014_{temp}c_compression'
        assert sid not in before.states
        ids = []
        for quantity, value_key, error_key, label in (
            ('compressive_modulus', 'compressive_modulus_MPa', 'compressive_modulus_CI_amplitude_MPa', 'Compressive modulus (MPa)'),
            ('compressive_strength', 'ultimate_compressive_strength_MPa', 'strength_CI_amplitude_MPa', 'Ultimate compressive strength (MPa)'),
        ):
            assert review['quantity_admissibility'][quantity]['decision'] == 'conditional_catalog_only'
            pid = f'refprop_dow_corning_sylgard184_johnston2014_{temp}c_{quantity}'
            assert pid not in before.properties
            ids.append(pid)
            number, error = row[value_key], row[error_key]
            tableloc = f'RetainedPDFp.5 Table3 and p.6 Table5,{temp}C row,{label}'
            prop = deepcopy(template_property)
            prop.update(id=pid, version='1.0.0', material_state_id=sid, quantity=quantity,
                        quantity_dimension='pressure', source_property_label=label, summary_statistic='reported_value')
            prop['reported_value'].update(number=number, value_text=number, unit_code='MPa', unit_text='MPa')
            prop['basis_note'] = 'Author-labelled Table3 result repeated inTable5, not an independently verified physical quantity or group estimator. Exact fit/peak/averaging order and compression n unknown; source95%CI retained, not inferredmean/SD.'
            description = ('Source-labelled ' + label + ' from compression testing,Avery Denison T42U,source ASTM D1229-03(2008)(lowtemperature),maximum crosshead20mm/min; '
                           'machineoil onparallel specimen surfaces beforetest toreducefriction/barrelling. Figure6 reportsengineeringstress/strain. '
                           'Actual geometry,fit/peak/failure criterion,area/strain determination and averaging order unestablished; no40%/55% window inferred.')
            if quantity == 'compressive_modulus':
                description += ' Author claimEc abouttwo orders aboveYoung/oppositecuringtrend and unknownFigure6 extraction retained; not a verifiedsmallstrain/tangent/secant/Young/globalconstant.'
            prop['conditions'] = {
                'temperature': fact('20°C average ambient during consecutivecompressiontests', methodloc, 'Not a controlled setpoint,22C cooling or curetemperature.'),
                'test_standard': fact('ASTM D1229-03(2008)(lowtemperature),as cited for compression test', methodloc, 'The mold is separately described withASTMD575-91; do not replace citations or certify compliance.'),
                'test_method': fact(description, methodloc),
                'direction': fact('Axial compression of a cylindrical specimen between parallel surfaces', methodloc, 'Loading geometry only; processing axes,material orientation and isotropy unknown.'),
                'conditioning': fact('Cooled1h at laboratory22C before moldremoval; testedwithin2h afterendofcure', prep, 'General handling timing,not moisture equilibrium; preloading/cycling and RH-control tolerance unknown.'),
                'loading_rate': fact('20mm/min crosshead velocity,set to maximum', methodloc, 'Source setting,not verified strain rate; displacement/gauge calibration and exactgeometry unknown.'),
                'additional_conditions': [
                    {'name': 'compression_test_humidity', 'fact': fact('39% average ambient relativehumidity during consecutivecompressiontests', methodloc, 'Average,not controlledtolerance or postcure humidityequilibration.')},
                    {'name': 'lubrication', 'fact': fact('A drop ofmachineoil onparallel surfaces immediatelybeforetest', methodloc, 'Source action toreducefriction/barrelling,not proofartifacts eliminated; oil specification/filmthickness unknown.')},
                    {'name': 'source_curve_convention', 'fact': fact('Figure6 labelled averagedengineeringstress/strain', methodloc, 'No rawcurve/area/strain/fit reconstruction.')},
                    {'name': 'evaluation_window', 'fact': unknown('Abstract40% scopeambiguous and bodyapprox55% isnot a verifiedEcfit/UCS criterion; actual extractionwindow unknown.')},
                    {'name': 'mold_standard_context', 'fact': fact('Compressionmold described underASTMD575-91', prep, 'Geometry context distinctfrom sourceD1229testcitation; no numericaldimensions inferred fromstandard.')},
                ],
            }
            prop['uncertainty'].update(number=error, value_text=error, unit_code='MPa', unit_text='MPa',
                scope=f'Reported plus/minus{error}MPa absolute amplitude of source95%CI forTable3/5 {temp}C cure {quantity}; estimand/construction unknown.',
                evidence=[ev(tableloc, ['uncertainty']), ev(statloc, ['uncertainty'])])
            prop['uncertainty']['estimand'] = unknown('Source doesnot identify this compressionCI estimand; neither per-specimenfit/peakmean nor populationmean is established.')
            prop['uncertainty']['construction'] = unknown('CI formula,distribution,coveragefactor and extraction/averaging order unknown. No SD/SE/t conversion.')
            prop['uncertainty_note'] = f'{number} plus/minus{error}MPa is source95%CI,notSD/SE; absolute pressure amplitude. Compressionn and independentbatch count unknown; total60/tensile6/hardness4 not transferred.'
            prop['sample_count'] = {'value': None, 'relation': 'not_reported', 'scope': 'Exact compression specimen/repeat/batch count not explicit in selected method/results.',
                                    'source_statement': 'No explicit compressionn in inspectedsections; total60testpieces and othertest counts do not establish compressionn.', 'evidence': []}
            prop['method_definition'].update(definition=description, extraction_window=None,
                evidence=[ev(methodloc, ['method', 'classification'])])
            prop['source_discrepancies'] = deepcopy([unit_issue, range_issue] + ([modulus_issue] if quantity == 'compressive_modulus' else []))
            scope = f'RetainedsamePDFTable3/5 {temp}C compressionresult; sourceR3 independentlyadjudicated againstpriorvisualPDFpp.1-6. Currentmapping performs no freshPDFvisual/download/latestnotice/rawdatacheck; preservesunit/range and extractionunknowns.'
            prop['source_document'].update(inspected_on='2026-11-03', inspection_scope=scope)
            prop['verification']['source_inspection_scope'] = scope
            prop['scope_note'] = (f'CommercialSylgard18410:1parts,compression-specific{temp}C/{duration} cure,not tensile/hardnessstate. '
                                  'Reported20C/39%RH average iscompressionambient,not cure/cooling or moistureequilibrium. SourceMPa/95%CI only; abstractUCSGPa and40%scopeconflicts remain,approx55%notfit/failurecriterion. '
                                  'Unknowncompressionn,CIestimand/construction,fit/peak/averaging,geometry and calibration; no inferredmean/SD or sourceunit repair. '
                                  'No engineeringallowable/universalbound,engineinput or elasticconstantconversion.')
            if quantity == 'compressive_modulus':
                prop['scope_note'] += ' SourceEc abouttwoordershigherthanYoung/oppositecuringtrend is retained asclaim,not certified; unknownFigure6extraction,notverifiedsmallstrain/tangent/secant/Young/globalmodulus. No derivative/secant/multiplier/Poisson repair.'
            prop['evidence'] = [ev(tableloc, ['reported_value', 'classification']), ev(statloc, ['uncertainty']), ev(methodloc, ['method', 'condition'])]
            properties.append(prop)
            mapping_facts.append({'new_property_id': pid, 'proposed_state_id': sid, 'quantity': quantity, 'number': number, 'uncertainty_number': error,
                                  'cure_temperature_C': temp, 'corrected_compression_cure_duration': duration})
        state = deepcopy(template_state)
        names = {'en': f'Sylgard184,10:1parts,{temp}C/{duration} compressioncure',
                 'zh': f'Sylgard184，10:1份，{temp}°C/{duration}压缩试样固化',
                 'ja': f'Sylgard184、10:1部、{temp}°C/{duration}圧縮試験片硬化',
                 'de': f'Sylgard184,10:1Teile,Druckprobenhärtung{temp}°C/{duration}'}
        state.update(id=sid, version='1.0.0', name=names['en'], names=names, aliases=[], property_ids=ids)
        state['state']['product_form'] = fact('Cured commercialkit cylindricalcompression specimen,sourceASTMD575-91moldfamily', prep, 'Numericalspecimendimensions not supplied here; no standard-based geometry inference or compliancecertification.', ('state',))
        state['state']['temper_or_heat_treatment'] = fact(f'Compressioncure{temp}C forTable1 corrected{duration}', prep, 'Asprinted;200C24min not repaired from18min heatpropagation context. Authorsassumefullcure,analyticaldegreeofcureunknown.', ('state',))
        for key in ('processing', 'conditioning', 'composition_or_purity', 'porosity'):
            state['state'][key]['evidence'] = [ev(prep, ['state'])]
        state['state']['conditioning']['notes'] = '22C cooling and curetemperature are distinctfrom20C averagecompressionambient; RH/equilibration/preloadingunknown.'
        state['state']['orientation'] = unknown('Material processingaxes and isotropy not established; geometricaxialcompression reportedonlywithproperty.')
        state['source_scope'] = f'Separatecompression-specimenstate underexistingcommercialidentity/grade,{temp}C/{duration}Table1compressioncure. No oldtensile/hardnessproperty moved or changed;temperature/rate/statistics/extractionboundaries property-specific.'
        state['evidence'] = [ev(prep, ['state'])]
        states.append(state)
    data = deepcopy(before.data)
    data['materials']['records'].extend(states)
    data['reference_properties']['records'].extend(properties)
    src = deepcopy(before.sources[source])
    src['claim_notes'].append('2026-11-03 source-qualifiedcompressionTable3/5 supplement:fivecompressioncures,Ec/UCS MPa/source95%CI,compressionnunknown. AbstractUCSGPa/40%scope/bodyapprox55% and sourceEcabouttwoordersaboveYoung/oppositetrendwithunknownFigure6extraction retained;no unit/Young/derivative/secant/Poisson repair,scientificcertification orengineinput.')
    data['sources']['records'] = [src if s['id'] == source else s for s in data['sources']['records']]
    after = Database(data)
    contracts = after.validate_scientific_contracts()
    assert len(after.properties) == 5316 and len(after.states) == 5206
    assert all(after.properties[k] == v for k, v in before.properties.items())
    assert all(after.states[k] == v for k, v in before.states.items())
    assert after.identities == before.identities and after.grades == before.grades and set(after.sources) == set(before.sources)
    for name in data:
        Draft202012Validator(read(ROOT / 'schemas' / (name + '.schema.json')), format_checker=FormatChecker()).validate(data[name])
    dest.mkdir(parents=True)
    (dest / 'native-tables').mkdir()
    for name, value in data.items(): write(dest / 'native-tables' / (name + '.json'), value)
    write(dest / 'native-candidate-r1.json', {'baseline_snapshot': BASE, 'stage': 'not_applied', 'materials': {'identities': [], 'grades': [], 'records': states},
          'reference_properties': {'records': properties}, 'sources': {'records': [src]}})
    write(dest / 'MAPPING_FACTS_R1.json', {'rows': mapping_facts})
    counts = {}
    for phase, db in [('before', before), ('after', after)]:
        target = dest / 'source-exports' / phase
        db.export(target, source=source)
        _, joined = read_snapshot(target)
        assert joined == {r['property']['id']: r for r in db.records(source=source)}
        counts[phase] = len(joined)
    assert counts == {'before': 15, 'after': 25}
    for language in ('en', 'zh', 'ja', 'de'):
        with patch('materials_boundaries.catalog.read_catalog', side_effect=lambda name: data[name]):
            text = render_material_catalog({'schema_version': '1.0.0', 'records': properties}, 'reference-properties', language)
        assert all(f['number'] in text and f['uncertainty_number'] in text for f in mapping_facts)
        assert all(token in text for token in ('95%', 'MPa', 'GPa', '40%', '55%', 'unknown', 'twoorders'))
        (dest / ('render-' + language + '.txt')).write_text(text, encoding='utf-8', newline='\n')
    write(dest / 'VALIDATION_R22.json', {'baseline_snapshot': BASE, 'preview_snapshot': after.snapshot, 'properties': 5316, 'states': 5206,
          'new_properties': 10, 'new_states': 5, 'new_identities_grades_sources': 0, 'all_old5306properties_and5201states_complete_unchanged': True,
          'source_change': 'One appended claim_note only.', 'schema_format': 'passed', 'current_graph': contracts, 'complete_source_export': counts,
          'four_languages': 'passed', 'native_applied': False, 'installed': 'not_run', 'full_history_regression': 'not_run', 'pushed': False})
    for name in ('native-candidate-r1.json', 'MAPPING_FACTS_R1.json', 'VALIDATION_R22.json'):
        (OUT / name).write_bytes((dest / name).read_bytes())
    print(json.dumps({'snapshot': after.snapshot, 'properties': 5316, 'states': 5206, 'source_exports': counts}))


if __name__ == '__main__':
    main()
