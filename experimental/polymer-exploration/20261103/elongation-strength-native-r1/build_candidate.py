"""Map twelve source-labelled strength-endpoint percentage elongations on existing tensile states."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT))
from materials_boundaries.database import Database
from jsonschema import Draft202012Validator,FormatChecker

AREA=ROOT/'experimental/polymer-exploration/20261103'
BASE='a0413960c6bb433dfcdc78d1226f617c8d9b64f33515f746b0e94fa37747c927'


def read(path):return json.loads(path.read_bytes())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path,value):
    with path.open('x',encoding='utf-8',newline='\n') as f:
        json.dump(value,f,ensure_ascii=False,indent=2)
        f.write('\n')


def main():
    out=Path(sys.argv[1]).resolve()
    assert not out.exists() and not out.is_relative_to(ROOT)
    proposal=AREA/'elongation-strength-proposal-r1'
    facts=read(proposal/'SOURCE_FACTS_R1.json')
    review=read(proposal/'INDEPENDENT_SOURCE_CONTRACT_REVIEW_R1.json')
    assert review['decision']=='approved' and review['review_inputs_sha256']==sha(proposal/'REVIEW_INPUTS_R1.json')
    for asset in facts['source_assets'].values():
        path=Path(asset['path_hint'])
        assert sha(path)==asset['sha256'] and path.stat().st_size==asset['bytes']
    before=Database()
    assert before.snapshot==BASE==facts['baseline_snapshot']
    props,states,sources=[],{},{}
    for fact in facts['rows']:
        old=before.properties[fact['base_property_id']]
        assert old['source_id']==fact['source_id'] and old['material_state_id']==fact['existing_state_id']
        assert old['quantity']=='tensile_strength'
        p=deepcopy(old)
        assert fact['new_property_id'] not in before.properties
        sahin=fact['source']=='Sahin'
        p.update(id=fact['new_property_id'],version='1.0.0',quantity='tensile_elongation_at_strength',quantity_dimension='dimensionless',source_property_label=fact['source_property_label'])
        p['reported_value'].update(number=fact['number'],value_text=fact['number'],unit_code='percent_elongation',unit_text='%')
        p['uncertainty'].update(number=fact['uncertainty_number'],value_text=fact['uncertainty_number'],unit_code='percent_elongation',unit_text='%')
        assert p['summary_statistic']==fact['summary_statistic']
        assert p['uncertainty']['type']==fact['uncertainty_type'] and p['sample_count']['value']==fact['sample_count']
        p['uncertainty']['scope']='Absolute source SD in elongation-percentage points for this material group;not relative percent error.' if sahin else 'Absolute source plus-minus amplitude in elongation-percentage points;statistical construction and central aggregation unknown,not relative percent error.'
        p['uncertainty_note']=fact['number']+' plus/minus '+fact['uncertainty_number']+'% on the original elongation percentage scale. '+('Source mean and SD,n5 specimens;not independent batches or relative error.' if sahin else 'Central statistic,plus-minus meaning and nunknown;modulus-specific SD statement not transferred.')
        p['basis_note']=fact['locator']+';source-labelled elongation at reported strength/maximum stress,not break/yield elongation,an imposed target,absolute extension or certified engineering/nominal/true strain.'
        p['sample_count']['scope']='Five tensile specimens per selected material group;independent batches unknown.' if sahin else 'Specimens or measurements contributing to this selected strength-endpoint elongation expression are not stated;independent batches unknown.'
        definition=('Section2.3 ASTM D638-14,Zwick/RoellZ020/10kN,23C,5.0mm/min crosshead.' if sahin else 'Section2.4 source-cited ISO527-1:2012,Instron1122/5kN,2mm/min crosshead,115mm clamp separation.')+' Source percentage elongation at reported strength/maximum stress within source tested range;strain estimator,reference gauge,engineering/nominal/true/logarithmic convention,exact peak/elongation selection and pooling order unknown. No percent-to-fraction,stretch-ratio or strain-rate conversion.'
        p['method_definition'].update(type='source_reported_conventional',definition=definition,extraction_window=None)
        p['conditions']['test_method'].update(text=definition,notes='Source-labelled strength-endpoint elongation only;standard citation does not supply missing estimator/gauge/convention or prove compliance. Clamp separation is not a verified extensometer gauge.')
        for evidence in p['evidence']:
            if any(k in evidence['supports'] for k in ('reported_value','classification','uncertainty')):evidence['locator']=fact['locator']
        for evidence in p['uncertainty']['evidence']:evidence['locator']=fact['locator']
        for evidence in p['method_definition']['evidence']:evidence['locator']=fact['locator']
        if sahin:
            for issue in p['source_discrepancies']:
                issue['disposition']='Transcribe selected epsilon_M strength-endpoint cell from Table4;retain separate section3.1 Table1/Table4 break-elongation cross-reference issue without numerical repair.'
        scope='Retained exact primary XML selected strength/maximum-stress percentage elongation cells,source identity/state,methods/statistics and permissions;no fresh PDF visual or latest revision/correction/retraction audit.'
        p['source_document'].update(revision='Retained registered XML bytes;latest online revision/correction/retraction status unknown.',inspected_on='2026-11-03',inspection_scope=scope)
        p['verification']['source_inspection_scope']=scope
        p['scope_note']='Only the existing selected source specimen state. Source-labelled percentage elongation at strength/maximum stress,not break/yield or a verified peak/strain convention/reference gauge. No stress,modulus,toughness,energy,stretch-ratio or target inference;no engine input,universal bound or engineering allowable. '+('Keep unknown SKU,lot,additives,post-print conditioning,RH,axis relation and batches;100%infill not verified zero porosity;Table1/Table4 source cross-reference retained.' if sahin else 'Keep unknown tensile environment,post-molding conditioning,axis/geometry,n and batches;pellet storage/molding/MFI not tensile conditions. Molding setup/adjustment discrepancy retained. High-PCL rows select explicit maximum-stress elongation only;break hyphens remain unfilled,no break bounds. Pure endpoints excluded;B denotes blend,not break.')
        state=deepcopy(before.states[p['material_state_id']])
        assert state['id'] not in states
        a,b,c=state['version'].split('.')
        state['version']=f'{a}.{b}.{int(c)+1}'
        state['property_ids'].append(p['id'])
        state['source_scope']+=' Source-labelled percentage elongation at strength/maximum stress is separately recorded;peak selection,measurement convention/gauge and extraction remain unknown,statistics property-specific. No paired-curve or modulus inference.'
        states[state['id']]=state
        sources.setdefault(p['source_id'],deepcopy(before.sources[p['source_id']]))
        props.append(p)
    for source in sources.values():
        source['claim_notes'].append('2026-11-03 strength-endpoint elongation supplement on existing selected states:original percentage scale,not break/yield strain or certified global/first-local peak. Sahin5groups mean/SD/n5;PLA-PCL7blends central/±/nunknown,no modulus SD transfer. High-PCL maximum-stress entries do not fill break hyphens. Unknown gauge/convention/selection/pooling retained;no ordering,paired-curve,stress/mean-strain or engine inference.')
    data=deepcopy(before.data)
    data['reference_properties']['records'].extend(props)
    data['materials']['records']=[states.get(s['id'],s) for s in data['materials']['records']]
    data['sources']['records']=[sources.get(s['id'],s) for s in data['sources']['records']]
    after=Database(data)
    contracts=after.validate_scientific_contracts()
    assert len(after.properties)==5288 and all(after.properties[k]==p for k,p in before.properties.items())
    assert after.identities==before.identities and after.grades==before.grades
    assert set(after.states)==set(before.states) and set(after.sources)==set(before.sources)
    for name in data:Draft202012Validator(read(ROOT/'schemas'/(name+'.schema.json')),format_checker=FormatChecker()).validate(data[name])
    out.mkdir(parents=True)
    (out/'native-tables').mkdir()
    for name,value in data.items():write(out/'native-tables'/(name+'.json'),value)
    write(out/'native-candidate-r1.json',{'baseline_snapshot':BASE,'stage':'frozen_not_applied','materials':{'identities':[],'grades':[],'records':list(states.values())},'sources':{'records':list(sources.values())},'reference_properties':{'records':props}})
    write(out/'VALIDATION_R1.json',{'baseline_snapshot':BASE,'preview_snapshot':after.snapshot,'new_properties':12,'old_5276_complete_properties_unchanged':True,'new_identities':0,'new_states':0,'modified_states':12,'modified_sources':2,'current_graph':contracts,'three_table_schema_format':'passed','native_applied':False,'installed':'not_run','full_history_regression':'not_run','pushed':False})
    print(json.dumps({'snapshot':after.snapshot,'preview_properties':5288,'native_applied':False}))


if __name__=='__main__':main()
