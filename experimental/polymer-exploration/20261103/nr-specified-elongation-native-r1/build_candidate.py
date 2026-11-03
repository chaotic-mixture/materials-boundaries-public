"""Prepare two source-reported stresses at explicit NR elongation targets."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from materials_boundaries.database import Database
from jsonschema import Draft202012Validator, FormatChecker

AREA = ROOT / 'experimental/polymer-exploration/20261103'
BASE = 'ab02d81dffd433da7142847d922304094666a429c2bb8b58e31205ad1d9563fa'


def read(path):
    return json.loads(path.read_bytes())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def main():
    out = Path(sys.argv[1]).resolve()
    assert not out.exists() and not out.is_relative_to(ROOT)
    proposal = AREA / 'nr-specified-elongation-proposal-r1'
    facts = read(proposal / 'SOURCE_FACTS_R1.json')
    review = read(proposal / 'INDEPENDENT_SOURCE_CONCEPT_REVIEW_R1.json')
    assert review['decision'] == 'approved'
    assert review['review_inputs_sha256'] == sha(proposal / 'REVIEW_INPUTS_R1.json')
    assert sha(Path(facts['source_XML_path_hint'])) == facts['source_XML_sha256']
    before = Database()
    assert before.snapshot == BASE
    base = before.properties['refprop_smr10_bianchi2025_nr_finite_strain_tensile_modulus']
    assert base['material_state_id'] == facts['existing_state_id']
    props = []
    for row in facts['rows']:
        target = row['target_percent']
        p = deepcopy(base)
        pid = 'refprop_smr10_bianchi2025_nr_tensile_stress_at_' + target + '_percent_elongation'
        assert pid not in before.properties
        locator = 'Table4 unfilled NR row, sigma' + target + '%(MPa) column; section3.3.4 quasi-static tensile tests and explicit strain targets'
        evidence = {'source_id': facts['source_id'], 'url': base['source_document']['url'], 'locator': locator, 'supports': ['condition']}
        p.update(id=pid, version='1.0.0', quantity='tensile_stress_at_specified_elongation', source_property_label='sigma_' + target + '% (MPa)')
        p['specified_elongation'] = {'value_text': target, 'number': target, 'unit_text': '%', 'unit_code': 'percent', 'basis': 'source_reported_percent_elongation', 'evidence': [evidence], 'notes': 'Direct source strain target, not a certified specimen-level strain implementation, stretch ratio or logarithmic strain. Engineering/true strain convention and exact interpolation/point selection remain unknown. No stress/strain division or modulus inference.'}
        p['reported_value'].update(value_text=row['mean_MPa'], number=row['mean_MPa'])
        p['uncertainty'].update(value_text=row['SD_MPa'], number=row['SD_MPa'])
        p['uncertainty_note'] = row['mean_MPa'] + ' plus/minus ' + row['SD_MPa'] + ' MPa: source mean and SD,n5 tensile specimens;not independent batches,SE or CI.'
        p['basis_note'] = locator + '; source mean/SD for five specimens. Stress at source target, not finite-strain interval slope, initial/tangent/secant modulus or break stress.'
        definition = 'Section3.3.4 quasi-static ASTM D412 (edition unknown),Instron5969/1kN,500mm/min crosshead;Instron2603/25mm. Direct stress at source strain target ' + target + '%. Exact point-selection/interpolation and engineering/true stress-strain conventions unknown; no strain-rate or modulus conversion.'
        p['method_definition'].update(type='source_reported_conventional', definition=definition, extraction_window=None)
        p['conditions']['test_method'].update(text=definition, notes='Reported tensile stress at the explicit source target only;standard citation is not independent compliance verification.')
        for c in p['conditions']['additional_conditions']:
            if c['name'] == 'stress_strain_convention':
                c['fact']['notes'] = 'Source does not explicitly identify engineering versus true stress/strain for the selected target-stress result.'
        def bind(node):
            if isinstance(node, dict):
                if node.get('source_id') == facts['source_id'] and 'locator' in node and 'Table' in node['locator']:
                    node['locator'] = locator
                for value in node.values():
                    bind(value)
            elif isinstance(node, list):
                for value in node:
                    bind(value)
        bind(p)
        scope = 'Retained registered primary XML Table4 unfilled NR sigma200%/sigma400% columns and section3.3.4,mean/SD,n5 and article permissions. No fresh PDF visual or latest revision/correction/retraction audit;latest status unknown.'
        p['source_document'].update(revision='Retained registered XML;latest online revision/correction/retraction status unknown.', inspected_on='2026-11-03', inspection_scope=scope)
        p['verification']['source_inspection_scope'] = scope
        p['scope_note'] = 'Existing unfilled vulcanizate contains curatives;not pure raw NR. Temperature,RH,post-cure conditioning/storage,processing axis,prior quasi-static loading and independent batches unknown. No transfer from hardness,density,cyclic or relaxation conditions. Explicit200%/400% targets do not repair the separate break-strain header/magnitude issue. Unknown stress/strain conventions and point-selection algorithm retained. Not modulus,break/peak/yield stress or toughness;no engine input,engineering allowable or universal bound.'
        props.append(p)
    state = deepcopy(before.states[facts['existing_state_id']])
    a,b,c = state['version'].split('.')
    state['version'] = f'{a}.{b}.{int(c)+1}'
    state['property_ids'].extend(p['id'] for p in props)
    state['source_scope'] += ' Two separate source-reported stress facts at explicit200% and400% strain targets are proposed;not modulus slopes or break stress.'
    source = deepcopy(before.sources[facts['source_id']])
    source['claim_notes'].append('2026-11-03 NR target-stress supplement:Table4 unfilled NR only,sigma200% and sigma400%,mean/SD,n5 quasi-static tensile specimens. Explicit source targets;not stress/strain division or modulus. Unknown conventions,point selection and batches retained;no neighboring-test condition transfer or break-strain correction.')
    data = deepcopy(before.data)
    data['reference_properties']['records'].extend(props)
    data['materials']['records'] = [state if s['id']==state['id'] else s for s in data['materials']['records']]
    data['sources']['records'] = [source if s['id']==source['id'] else s for s in data['sources']['records']]
    after = Database(data)
    contracts = after.validate_scientific_contracts()
    assert all(after.properties[k] == p for k,p in before.properties.items())
    assert before.identities == after.identities and before.grades == after.grades
    assert set(before.states) == set(after.states) and set(before.sources) == set(after.sources)
    assert len(after.properties) == 5260
    for name in data:
        Draft202012Validator(read(ROOT/'schemas'/(name+'.schema.json')),format_checker=FormatChecker()).validate(data[name])
    out.mkdir(parents=True)
    tables = out/'native-tables'
    tables.mkdir()
    for name,value in data.items():
        write(tables/(name+'.json'),value)
    write(out/'native-candidate-r1.json',{'baseline_snapshot':BASE,'stage':'frozen_not_applied','materials':{'identities':[],'grades':[],'records':[state]},'sources':{'records':[source]},'reference_properties':{'records':props}})
    write(out/'VALIDATION_R1.json',{'baseline_snapshot':BASE,'preview_snapshot':after.snapshot,'new_properties':2,'new_identities':0,'new_states':0,'modified_states':1,'modified_sources':1,'old_5258_properties_unchanged':True,'current_graph':contracts,'three_table_schema_and_formats':'passed','native_applied':False,'installed':'not_run','independent_mapping_review':'pending','full_history_regression':'not_run','pushed':False})
    print(json.dumps({'properties':len(after.properties),'snapshot':after.snapshot,'native_applied':False}))


if __name__ == '__main__':
    main()
