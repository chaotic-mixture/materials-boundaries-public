"""Build a source-qualified NBR tear preview; never write the native tables."""
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
BASE = '25d66658d21c8aebad75b875b2da82c121a99f893ddde3965a837cc955f12ba6'


def read(path): return json.loads(path.read_bytes())
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def main():
    dest = Path(sys.argv[1]).resolve()
    assert not dest.exists() and not dest.is_relative_to(ROOT)
    proposal = AREA / 'nbr-tear-source-contract-r1'
    review = read(proposal / 'INDEPENDENT_SOURCE_REVIEW_R1.json')
    assert review['decision'] == 'approved'
    assert review['review_inputs_sha256'] == sha(proposal / 'REVIEW_INPUTS_R1.json')
    manifest = read(proposal / 'REVIEW_INPUTS_R1.json')
    archive = read(proposal / 'BASELINE_CONTRACT_BINDING_R1.json')
    for name, digest in manifest['repo_files_sha256'].items():
        if sha(ROOT / name) != digest:
            old = archive[name]
            assert sha(ROOT / old['archive_path']) == digest == old['sha256'], name
    for name, digest in manifest['external_files_sha256'].items():
        assert sha(Path(name)) == digest, name
    facts = read(proposal / 'SOURCE_FACTS_R1.json')
    before = Database()
    assert before.snapshot == BASE
    source = facts['source_id']
    url = 'https://www.ebi.ac.uk/europepmc/webservices/rest/PMC12750214/fullTextXML'
    oldid = 'state_perbunan3445f_tamas_benyei2025_ref'
    stateid = facts['state_plan']['new_state_id']
    propid = facts['state_plan']['new_property_id']
    assert stateid not in before.states and propid not in before.properties
    assert before.states[oldid] == read(proposal / 'BASE_REF_STATE_R1.json')
    methodloc = 'Retained primary XML/served PMC section2.2: ISO34 MethodB angle tear, ZwickZ005 and common tensile/tear 500mm/min'
    preploc = 'Retained primary XML/served PMC sections2.1-2.3 andTable3: REF formulation, preparation and nominal2mm vulcanized sheet'
    resultloc = 'Retained primary XML/served PMC section3.3 tearing-test paragraph: reference0phr12.32kN/m; Figure7'
    cureloc = 'Retained primary XML/served PMC section2.2 rheometer170C1.67Hz1degree20min; section3.2 REF TC90=381s; section2.3 pressing based on compound t90'

    def ev(locator, supports): return dict(source_id=source, url=url, locator=locator, supports=list(supports))
    def unknown(note): return dict(status='not_reported_in_inspected_source', text=None, evidence=[], notes=note)
    def fact(text, locator, note=None, tags=('condition',)):
        return dict(status='reported', text=text, evidence=[ev(locator, tags)], notes=note)

    heat = fact('Teach-Line Platen Press 200E at170°C and200bar; pressing time based on compound-specific t90. Source REF rheometer TC90=381s at170°C,1.67Hz,1degree amplitude,20min test context.',
                cureloc, '381s is the reported rheometer t90 context. The phrase based on does not independently verify an actual381s press hold, specimen temperature-time history or90% chemical conversion.', ('state',))
    oldstate = deepcopy(before.states[oldid])
    oldstate.update(version='1.0.4', source_scope=oldstate['source_scope'] + ' REF rheometer TC90=381s and its method context are now transcribed; this does not establish the exact press hold or chemical conversion.')
    oldstate['state']['temper_or_heat_treatment'] = deepcopy(heat)

    state = deepcopy(before.states[oldid])
    names = {'en': 'PERBUNAN3445F study REF, angle tear specimen', 'zh': 'PERBUNAN3445F研究REF角形撕裂试样',
             'ja': 'PERBUNAN3445F研究REFアングル形引裂試験片', 'de': 'PERBUNAN3445F Studien-REF, Winkel-Weiterreißprobe'}
    state.update(id=stateid, version='1.0.0', name=names['en'], names=names, aliases=[], property_ids=[propid])
    state['state']['product_form'] = fact('Nonfoamed REF angle tear testpiece cut from a nominal2mm vulcanized sheet; source ISO34 MethodB', preploc+'; '+methodloc,
        'Nominal sheet thickness only; actual specimen thickness, die dimensions, notch geometry and standard edition/part are unverified.', ('state',))
    state['state']['temper_or_heat_treatment'] = deepcopy(heat)
    state['state']['conditioning'] = unknown('Tear-specific post-cure conditioning, temperature, RH, moisture equilibrium and storage interval unknown; no tensile or standard laboratory defaults transferred.')
    state['state']['orientation'] = unknown('General mechanical-method description tests two mutually perpendicular orientations; tear-specific axes, notch relation, group pooling, weights and isotropy unverified. Tensile pooling is not transferred.')
    state['state']['porosity']['notes'] = 'No quantitative REF void fraction is established; nonfoamed preparation does not imply zero porosity.'
    state['source_scope'] = 'Separate ISO34 MethodB angle tear specimen under the existing additive-containing REF identity/grade and common nominal2mm vulcanized-sheet preparation. Not pure/raw NBR, reinforced G/D or foam. Tear-specific direction/pooling, n, test environment, posthandling and force/thickness extraction unknown. Rheometer REF381s context is not a verified actual press hold. No existing density/tensile property moved.'
    state['evidence'] = [ev(preploc, ('state',)), ev(methodloc, ('state',)), ev(cureloc, ('state',))]

    prop = deepcopy(before.properties['refprop_perbunan3445f_tamas_benyei2025_ref_tensile_strength'])
    prop.update(id=propid, version='1.0.0', material_state_id=stateid, quantity='tear_strength', quantity_dimension='force_per_length',
                source_property_label='tear strength (kN/m)', summary_statistic='reported_value', uncertainty=None,
                uncertainty_status='not_reported_in_inspected_source', source_discrepancies=[])
    prop['reported_value'].update(number='12.32', value_text='12.32', unit_code='kN/m', unit_text='kN/m')
    prop['basis_note'] = 'Exact REF scalar transcribed from section3.3 text, not a Figure7 pixel reading. Source plot has error bars and text discusses highSD; central estimator, exact REF amplitude and bar definition remain unknown. No inferred mean, peak-force algorithm or numerical scatter.'
    description = 'Source ISO34 MethodB angle tear testing on REF specimens cut from nominal2mm vulcanized sheets; ZwickZ005 universal test machine,5kN load-cell capacity,500mm/min crosshead speed. Standard part/edition, notch geometry, actual thickness, peak/mean-force choice, normalization algorithm and calibration unverified. General two-direction method does not establish tear-specific groups or tensile-style pooling.'
    prop['conditions'] = {
        'temperature': unknown('Tear-test temperature unknown;170°C is processing/rheometry, not test ambient.'),
        'test_standard': fact('ISO34, MethodB, angle testpieces, as printed', methodloc, 'Part/edition, exact notch geometry and independent compliance not verified.'),
        'test_method': fact(description, methodloc, '5kN is load-cell capacity, not measured specimen force.'),
        'direction': unknown('General mechanical method describes two mutually perpendicular orientations; tear-specific axes, notch relation, pooling weights and isotropy unknown. No tensile ANOVA/pooling transfer.'),
        'conditioning': unknown('Tear-specific pre-test temperature/RH, duration, moisture equilibrium and post-cure storage unknown.'),
        'loading_rate': fact('500mm/min crosshead speed', methodloc, 'Common source statement explicitly covers both tensile and tear testing; not converted to strain rate.'),
        'additional_conditions': [
            {'name': 'test_relative_humidity', 'fact': unknown('Tear-test RH unknown; no standard default assigned.')},
            {'name': 'actual_specimen_thickness', 'fact': unknown('Only nominal2mm source-sheet preparation is reported; measured tear-specimen thickness and its normalization implementation unknown.')},
            {'name': 'load_cell_capacity', 'fact': fact('5kN load-cell capacity', methodloc, 'Instrument range only, not test force or a record of calibration.')},
        ],
    }
    prop['uncertainty_note'] = 'Figure7 contains error bars and section3.3 discusses highSD. Exact numeric REF SD/amplitude and error-bar definition were not obtained from inspected text/figure; null means numeric uncertainty unavailable, not no scatter or zero. No graph estimate, tensile ± or hardness statistics transferred.'
    prop['sample_count'] = dict(value=None, relation='not_reported', scope='Exact tear specimen, per-direction and independent-batch counts unknown.',
        source_statement='10hardness points,3abrasion samples and tensile statistics do not establish tear n.', evidence=[])
    prop['method_definition'].update(definition=description, extraction_window=None, evidence=[ev(methodloc, ('method','classification'))])
    inspection = 'Retained primary XML sections2.1-2.3/3.2/3.3 and freshly served PMC HTML, title/DOI and Figures6/7 visually checked in frozen source audit. Exact REF12.32kN/m comes from text; Figure7 bar definition/amplitude remain unknown. Figure6 regression intercept is not a measured hardness scalar; hardness remains deferred. SI/rawdata/latest-notice completeness unknown; no claim of current fresh PDF inspection.'
    prop['source_document'].update(inspected_on='2026-11-04', inspection_scope=inspection)
    prop['verification']['source_inspection_scope'] = inspection
    prop['evidence'] = [ev(resultloc, ('reported_value','classification')), ev(methodloc, ('method','condition'))]
    prop['scope_note'] = 'Source-qualified12.32kN/m tear strength for existing additive-containing nonfoamed REF, not pure/raw NBR or a new material identity. Force per length only; no raw-force, pressure, fracture-energy/Gc/J-per-area, stress-intensity/KIC or Young-modulus interpretation/conversion and no engine input. Numeric REF uncertainty, n, test temperature/RH, conditioning, actual notch/thickness and extraction algorithm unknown; Figure7 error bars/highSD retained. Tear direction/pooling is not inferred from tensile ANOVA. Pressing based on t90 does not verify actual381s hold or chemical90% conversion.'
    source_record = deepcopy(before.sources[source])
    source_record['claim_notes'].append('2026-11-04 REF angle tear supplement: section3.3 exact12.32kN/m; ISO34 MethodB/ZwickZ0055kN-capacity/500mm-min source context. Figure7 bars/highSD retained with exact numeric uncertainty and n unknown. Separate tear state, no tensile pooling. REF rheometer TC90=381s context does not verify press hold. Figure6 fit intercept is not measured hardness; hardness deferred. No fracture-parameter conversion, scientific certification or engineering allowable.')
    data = deepcopy(before.data)
    data['materials']['records'] = [oldstate if s['id']==oldid else s for s in data['materials']['records']] + [state]
    data['reference_properties']['records'].append(prop)
    data['sources']['records'] = [source_record if s['id']==source else s for s in data['sources']['records']]
    after = Database(data)
    contracts = after.validate_scientific_contracts()
    assert len(after.properties)==5317 and len(after.states)==5207
    assert after.identities==before.identities and after.grades==before.grades
    assert all(after.properties[k]==v for k,v in before.properties.items())
    assert all(after.states[k]==v for k,v in before.states.items() if k!=oldid)
    restored = deepcopy(oldstate)
    for key in ('version','source_scope'): restored[key]=before.states[oldid][key]
    restored['state']['temper_or_heat_treatment']=before.states[oldid]['state']['temper_or_heat_treatment']
    assert restored==before.states[oldid]
    assert set(after.sources)==set(before.sources)
    assert all(after.sources[k]==v for k,v in before.sources.items() if k!=source)
    assert source_record['claim_notes'][:-1]==before.sources[source]['claim_notes']
    restored_source=deepcopy(source_record); restored_source['claim_notes'].pop(); assert restored_source==before.sources[source]
    for name in data:
        Draft202012Validator(read(ROOT/'schemas'/(name+'.schema.json')),format_checker=FormatChecker()).validate(data[name])
    dest.mkdir(parents=True)
    (dest/'native-tables').mkdir()
    for name,value in data.items(): write(dest/'native-tables'/(name+'.json'), value)
    write(dest/'native-candidate-r1.json', {'baseline_snapshot':BASE,'stage':'not_applied','materials':{'identities':[],'grades':[],'records':[oldstate,state]},'reference_properties':{'records':[prop]},'sources':{'records':[source_record]}})
    write(dest/'MAPPING_FACTS_R1.json', {'old_state_id':oldid,'updated_state':oldstate,'new_state':state,'new_property':prop,'source_record':source_record})
    counts={}
    for phase,db in [('before',before),('after',after)]:
        export=dest/'source-exports'/phase
        db.export(export,source=source)
        _,joined=read_snapshot(export)
        assert joined=={r['property']['id']:r for r in db.records(source=source)}
        counts[phase]=len(joined)
    assert counts=={'before':11,'after':12}
    for language in ('en','zh','ja','de'):
        with patch('materials_boundaries.catalog.read_catalog',side_effect=lambda name:data[name]):
            text=render_material_catalog({'schema_version':'1.0.0','records':[prop]},'reference-properties',language)
        assert all(token in text for token in ('12.32','kN/m','error bars','unknown','381s','500mm/min'))
        (dest/('render-'+language+'.txt')).write_text(text,encoding='utf-8',newline='\n')
    write(dest/'VALIDATION_R23.json', {'baseline_snapshot':BASE,'preview_snapshot':after.snapshot,'properties':5317,'states':5207,
        'new_properties':1,'new_states':1,'new_identities_grades_sources':0,'all_old5316properties_complete_unchanged':True,
        'old_state_change':'Only REF version,temper_or_heat_treatment,source_scope;5205 other oldstates unchanged.',
        'source_change':'One appended claim_note only.','schema_format':'passed','current_graph':contracts,'complete_source_export':counts,
        'four_languages':'passed','native_applied':False,'installed':'not_run','full_history_regression':'not_run','pushed':False})
    for name in ('native-candidate-r1.json','MAPPING_FACTS_R1.json','VALIDATION_R23.json'):
        with (OUT/name).open('xb') as stream: stream.write((dest/name).read_bytes())
    print(json.dumps({'snapshot':after.snapshot,'properties':5317,'states':5207,'source_exports':counts}))


if __name__=='__main__': main()
