"""Map two REF stress-at-elongation facts; never calculate a slope."""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT))
from materials_boundaries.database import Database
AREA=ROOT/'experimental/polymer-exploration/20261103'
BASE='8adff2c3c8e51f3fa1a6825349e870465998c680c0f5aa2dbf16c8ace5857471'
SID='tamas_benyei_santha_2025_nbr_rcf'
URL='https://www.ebi.ac.uk/europepmc/webservices/rest/PMC12750214/fullTextXML'


def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,obj):
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--xml',type=Path,required=True);parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args();out=args.output_dir.resolve();assert not out.exists() and not out.is_relative_to(ROOT/'materials_boundaries')
    proposal=AREA/'nbr-specified-elongation-proposal-r1';facts=read(proposal/'SOURCE_FACTS_R1.json');review=read(proposal/'INDEPENDENT_SOURCE_CONTRACT_REVIEW_R1.json')
    assert review['decision']=='approved' and review['review_inputs_sha256']==sha(proposal/'REVIEW_INPUTS_R1.json')
    assert sha(args.xml)==facts['primary_XML_sha256']
    before=Database();assert before.snapshot==BASE
    old=before.properties['refprop_perbunan3445f_tamas_benyei2025_ref_tensile_strength'];props=[]
    for row in facts['rows']:
        label,target=row['label'],row['specified_elongation_percent']
        prop=deepcopy(old);pid='refprop_perbunan3445f_tamas_benyei2025_ref_'+label.lower()+'_stress';assert pid not in before.properties
        prop.update(id=pid,version='1.0.0',quantity='tensile_stress_at_specified_elongation',source_property_label=label+' (MPa)')
        prop['reported_value'].update(number=row['stress_MPa'],value_text=row['stress_MPa'])
        prop['uncertainty'].update(number=row['plus_minus_MPa'],value_text=row['plus_minus_MPa'],scope=f'Selected REF {label} source stress group only; per-target participant count and ± type unknown.')
        prop['uncertainty_note']=f"{row['stress_MPa']} ± {row['plus_minus_MPa']} MPa: printed amplitude retained without defining SD/SE/CI; statistics from other tests or adjacent strain-at-break discussion cannot establish this type."
        def ev(locator,*tags):return [{'source_id':SID,'url':URL,'locator':locator,'supports':list(tags)}]
        prop['specified_elongation']={'value_text':target,'number':target,'unit_text':'%','unit_code':'percent','basis':'source_reported_percent_elongation',
            'evidence':ev(f'Primary XML Table 4 REF {label}; section3.3, 100%/200% elongation descriptions','condition'),
            'notes':f'Source {label} at {target}% elongation. This is the source target, not a verified specimen-wise strain measurement, stretch ratio or logarithmic strain. Gauge and strain-estimation implementation remain unknown; no target/result conversion performed.'}
        prop['basis_note']='Section3.3 averages tensile results across orientations; preserve reported_mean without assuming estimator, per-target participant count or order of point extraction and averaging. Rubber M label is represented as stress at source-specified elongation, never stress-strain slope.'
        prop['sample_count']['scope']=f'Selected REF {label} target group only; per-target/per-direction specimen and independent-batch counts unknown. Do not assume every tensile specimen reached this target or equals the strength-test population.'
        method=f'Source ISO37 Type2 tensile testing of nominal2mm vulcanized sheet on ZwickZ005/5kN load cell at500mm/min, pooled across two orientations. Reported {label} stress at {target}% elongation; source standard edition/compliance, actual strain estimator/stress convention and point-extraction/averaging order unknown. No division by elongation or fitted tangent/secant modulus.'
        prop['method_definition'].update(definition=method,extraction_window=None,evidence=ev('Primary XML sections2.2/3.3 and Table4 REF '+label,'method','classification'))
        prop['conditions']['test_method']['notes']='Source-labelled finite-elongation stress, not modulus slope; 5kN is instrument capacity. ISO2024 terminology reference does not identify the edition used by authors or prove compliance.'
        prop['evidence']=ev('Primary XML Table4 REF row, '+label+'(MPa)','reported_value','classification')+ev('Primary XML section3.3 pooled tensile results','summary_statistic')
        prop['uncertainty']['evidence']=ev('Primary XML Table4 REF row, '+label+' printed ±','uncertainty')
        scope='Retained primary XML Table4 selected REF '+label+' cell; sections2.2/2.3/3.3 for methods/preparation/target descriptions and pooling; permissions and Figure1 third-party exclusion. No fresh PDF inspection or raw-data reanalysis.'
        prop['source_document']['inspection_scope']=scope;prop['verification']['source_inspection_scope']=scope
        prop['scope_note']='Existing additive-containing nonfoamed REF identity and tensile state only. Directly preserve source MPa stress and percent target; do not relabel as Young/tangent/secant modulus, tensile/yield strength or break stress. Unknown count/±/environment/conditioning/gauge/strain implementation remain unknown. Inherited abstract/Table4 disagreement concerns tensile-strength improvement, not a newly calculated discrepancy for this target. No model conversion, automatic calculator input, universal bound or engineering allowable.'
        props.append(prop)
    state=deepcopy(before.states[old['material_state_id']]);a,b,c=state['version'].split('.');state['version']=f'{a}.{b}.{int(c)+1}';state['property_ids'] += [p['id'] for p in props]
    state['source_scope']='Existing additive-containing nonfoamed REF 2mm vulcanizate, shared by independent density/tensile-strength/stress-at-specified-elongation references. Each property keeps its own methods/statistics and unknowns. M100/M200 now map to source-labelled stresses at100%/200% elongation, never Young modulus. No universal isotropy, pure-NBR, foam or elemental-sulfur conversion claim; Figure1 third-party content excluded.'
    source=deepcopy(before.sources[SID]);source['claim_notes'].append('2026-11-03 REF M100/M200 supplement: direct Table4 stress values plus source100%/200% elongation targets, not slope moduli or recalculated secants. ISO37 edition used by authors remains unknown; current terminology references are not compliance certification. Per-target participants, estimator, extraction/averaging order and ± type remain unspecified. Existing density and tensile-strength facts unchanged.')
    data=deepcopy(before.data);data['reference_properties']['records']+=props;data['materials']['records']=[state if s['id']==state['id'] else s for s in data['materials']['records']];data['sources']['records']=[source if s['id']==SID else s for s in data['sources']['records']]
    after=Database(data);contracts=after.validate_scientific_contracts()
    assert all(after.properties[k]==v for k,v in before.properties.items()) and after.identities==before.identities and after.grades==before.grades and set(after.states)==set(before.states)
    out.mkdir(parents=True);tables=out/'native-tables';tables.mkdir()
    for name,value in data.items():write(tables/(name+'.json'),value)
    write(out/'native-candidate-r1.json',{'baseline_snapshot':BASE,'stage':'frozen_not_applied','materials':{'identities':[],'grades':[],'records':[state]},'sources':{'records':[source]},'reference_properties':{'records':props}})
    write(out/'VALIDATION_R1.json',{'baseline_snapshot':BASE,'preview_snapshot':after.snapshot,'new_properties':2,'new_identities':0,'new_states':0,'modified_states':1,'modified_sources':1,'all_old_5243_property_objects_unchanged':True,'contracts':contracts,'native_applied':False,'pushed':False,'full_history_regression':'not_run'})
    print(json.dumps({'snapshot':after.snapshot,'properties':len(after.properties),'contracts':contracts}))


if __name__=='__main__':main()
