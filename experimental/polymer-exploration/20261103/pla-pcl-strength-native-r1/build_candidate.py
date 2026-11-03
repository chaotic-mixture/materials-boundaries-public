"""Map source tensile strengths without borrowing modulus SD definitions."""
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
BASE = '191d3abdf5a5528019ce63551df281fab156eeaa5bdb81541048cb1835e8df44'


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
    proposal = AREA/'pla-pcl-source-readback-r1'
    facts = read(proposal/'SOURCE_FACTS_R1.json')
    review = read(proposal/'INDEPENDENT_SOURCE_REVIEW_R1.json')
    assert review['decision'] == 'approved'
    assert review['review_inputs_sha256'] == sha(proposal/'REVIEW_INPUTS_R1.json')
    assert sha(Path(facts['XML_path_hint'])) == facts['XML_sha256']
    before = Database()
    assert before.snapshot == BASE == facts['native_snapshot']
    props, states = [], {}
    for fact in facts['rows']:
        old = before.properties[fact['base_property_id']]
        assert old['quantity']=='youngs_modulus' and old['source_id']==facts['source_id']
        assert old['material_state_id']==fact['existing_state_id']
        p = deepcopy(old)
        assert fact['new_property_id'] not in before.properties
        p.update(id=fact['new_property_id'],version='1.0.0',quantity='tensile_strength',source_property_label='sigma_t^B (MPa)')
        p['reported_value'].update(number=fact['strength_MPa'],value_text=fact['strength_MPa'],unit_text='MPa',unit_code='MPa')
        assert p['summary_statistic']=='not_stated' and p['reporting_basis']=='not_stated'
        p['basis_note'] = 'Table2 experimental tensile strength of the selected blend;Table3 experimental column repeats the same source expression. Central aggregation and n unknown;no theoretical RoM or commercial comparison value selected. SuperscriptB denotes blend,not break.'
        p['uncertainty_status'] = 'reported_plus_minus_unspecified'
        uev = {'source_id':facts['source_id'],'url':p['source_document']['url'],'locator':fact['locator'],'supports':['uncertainty']}
        p['uncertainty'] = {'type':'reported_plus_minus_unspecified','value_text':fact['plus_minus_MPa'],'number':fact['plus_minus_MPa'],'unit_text':'MPa','unit_code':'MPa','scope':'Source plus-minus amplitude for this selected tensile-strength expression only;statistical construction and central aggregation unspecified. Modulus-specific SD statement does not define strength dispersion.','coverage_factor':None,'confidence_level':None,'evidence':[uev]}
        p['uncertainty_note'] = fact['strength_MPa']+' plus/minus '+fact['plus_minus_MPa']+' MPa: reported expression,not a verified mean/SD,SE,CI,tolerance or physical range. Section3.2 afterEq6 identifies only Young modulus variability as SD;do not transfer that definition to strength.'
        assert p['sample_count']['value'] is None and p['sample_count']['relation']=='not_reported'
        p['sample_count'].update(scope='Specimens or measurements contributing to this selected tensile-strength result are not stated;independent manufacturing batches unknown.',source_statement='Selected methods and Table2 do not state tensile specimen/replicate counts;number of blend formulations is not n.')
        definition = 'Source experimental tensile strength of injection-molded blend,Instron1122/5kN,source-cited ISO527-1:2012,2mm/min crosshead and115mm clamp separation. Exact strength selection/reduction,engineering/true stress convention,strain estimator and extensometer gauge unspecified. Not Young modulus or stress at break.'
        p['method_definition'].update(type='source_reported_conventional',definition=definition,extraction_window=None)
        p['conditions']['test_method'].update(text=definition,notes='Clamp separation is not an extensometer gauge length;no strain-rate conversion or standard-derived default conditions.')
        for evidence in p['evidence']:
            if any(k in evidence['supports'] for k in ('reported_value','classification','uncertainty')):
                evidence['locator'] = fact['locator']
        scope = 'Reacquired official EuropePMC XML byte-equal registered asset;article permissions,sections2.1-2.4 and3.1-3.2,Tables1/2/3;selected experimental tensile strengths and unspecified plus-minus expressions. No fresh PDF visual inspection,raw-data analysis or latest correction/retraction audit.'
        p['source_document'].update(revision='Reacquired registered XML bytes;latest revision/correction/retraction status unknown.',inspected_on='2026-11-03',inspection_scope=scope)
        p['verification']['source_inspection_scope'] = scope
        p['scope_note'] = 'Existing source-defined blend and injection-molded state only;reported mass ratio and PCL volume fraction are distinct. Central statistic,plus-minus definition,n and batches unknown. Tensile temperature,RH,pressure,post-molding conditioning,flow/loading relation,specimen geometry,stress convention and peak-selection algorithm unknown. Ingredient/pellet60C storage,molding175-190C/330-600bar and MFI210C do not supply tensile environment. Source molding-setting discrepancy retained;no universal per-blend recipe. Not break/yield strength,modulus,impact/toughness or modeled output;no automatic engine input,universal bound or engineering allowable.'
        state = deepcopy(before.states[p['material_state_id']])
        assert state['id'] not in states
        a,b,c = state['version'].split('.')
        state['version'] = f'{a}.{b}.{int(c)+1}'
        state['property_ids'].append(p['id'])
        state['source_scope'] += ' Experimental tensile strength is also recorded with source plus-minus amplitude of unspecified statistical meaning;central aggregation and sample count remain unknown.'
        states[state['id']] = state
        props.append(p)
    source = deepcopy(before.sources[facts['source_id']])
    source['claim_notes'].append('2026-11-03 existing seven blend tensile-strength supplement:Table2 sigma_t^B experimental values,Table3 experimental corroboration;B denotes blend. Strength plus-minus definition,central aggregation,n and tensile conditioning unknown;modulus-specific SD not transferred. Existing modulus objects preserved. No neat endpoints,commercial comparisons,modeled values,new identities or engine inputs.')
    data = deepcopy(before.data)
    data['reference_properties']['records'].extend(props)
    data['materials']['records'] = [states.get(s['id'],s) for s in data['materials']['records']]
    data['sources']['records'] = [source if s['id']==source['id'] else s for s in data['sources']['records']]
    after = Database(data)
    contracts = after.validate_scientific_contracts()
    assert all(after.properties[k]==p for k,p in before.properties.items())
    assert before.identities==after.identities and before.grades==after.grades
    assert set(before.states)==set(after.states) and set(before.sources)==set(after.sources)
    assert len(after.properties)==5267
    for name in data:
        Draft202012Validator(read(ROOT/'schemas'/(name+'.schema.json')),format_checker=FormatChecker()).validate(data[name])
    out.mkdir(parents=True)
    (out/'native-tables').mkdir()
    for name,value in data.items():
        write(out/'native-tables'/(name+'.json'),value)
    write(out/'native-candidate-r1.json',{'baseline_snapshot':BASE,'stage':'frozen_not_applied','materials':{'identities':[],'grades':[],'records':list(states.values())},'sources':{'records':[source]},'reference_properties':{'records':props}})
    write(out/'VALIDATION_R1.json',{'baseline_snapshot':BASE,'preview_snapshot':after.snapshot,'new_properties':7,'new_identities':0,'new_states':0,'modified_states':7,'modified_sources':1,'old_5260_properties_unchanged':True,'current_graph':contracts,'three_table_schema_and_format':'passed','native_applied':False,'installed':'not_run','full_history_regression':'not_run','pushed':False})
    print(json.dumps({'properties':len(after.properties),'snapshot':after.snapshot,'native_applied':False}))


if __name__ == '__main__':
    main()
