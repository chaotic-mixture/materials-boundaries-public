"""Draft a flexural modulus on the existing hot-pressed PHBV-39 state."""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT))
from materials_boundaries.database import Database
BASE='62502e5fe24d06f883228fe7d9fea3c579d03d97c25c0b3b8d33a87a9c767bd6'
SHA='a37eac0af73559b942f680a671d41a4d870d66d94b76e825cdaf61cc6cd3a3a5'
SID='abbasi_2022_manure_phbv'
URL='https://www.ebi.ac.uk/europepmc/webservices/rest/PMC9571417/fullTextXML'


def write(p,obj):
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--xml',type=Path,required=True);parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args();out=args.output_dir.resolve();assert not out.exists() and not out.is_relative_to(ROOT/'materials_boundaries')
    raw=args.xml.read_bytes();assert hashlib.sha256(raw).hexdigest()==SHA
    r=ET.fromstring(raw);table=next(t for t in r.findall('.//table-wrap') if ''.join(t.find('label').itertext()).strip()=='Table 9')
    row=next(t for t in table.findall('.//tbody/tr') if ''.join(t[0].itertext()).strip()=='PHBV-39')
    pair=lambda c:re.fullmatch(r'\s*(\d+\.\d+)\s*±\s*(\d+\.\d+)\s*',c.text).groups()
    before=Database();assert before.snapshot==BASE
    old=before.properties['refprop_abbasi2022_manure_phbv39_youngs_modulus']
    assert pair(row[2])==(old['reported_value']['number'],old['uncertainty']['number'])
    mean,sd=pair(row[4]);assert (mean,sd)==('1.02','0.08')
    p=deepcopy(old);pid=old['id'].replace('youngs_modulus','flexural_modulus');assert pid not in before.properties
    p.update(id=pid,quantity='flexural_modulus',source_property_label='Flexural Modulus (GPa)',
        basis_note='Table 9 PHBV-39 flexural modulus, mean ± SD per table footnote; at least five replicates under section 2.2.8. No conversion to tensile/Young modulus or specimen-level reanalysis.')
    p['reported_value'].update(value_text=mean,number=mean);p['uncertainty'].update(value_text=sd,number=sd)
    p['uncertainty_note']='1.02 ± 0.08 GPa: reported mean ± SD; source notes SD rounded up to mean precision where necessary. No SEM/CI conversion.'
    method='Three-point bending on DMA Q800 at source-described room temperature, span 10 mm, source wording constant strain of 1% until yield; Universal Analysis v4.5A stress–strain analysis. Exact modulus fit window/algorithm and a per-time bending rate are not specified.'
    p['conditions']['test_method']['text']=method
    p['conditions']['loading_rate']={'status':'not_reported_in_inspected_source','text':None,'evidence':[],
        'notes':'Source states constant strain of 1% until yield, without a per-time rate. Do not borrow the tensile 3 N/min ramp or treat 1% as a fit window.'}
    ev=lambda locator,supports:[{'source_id':SID,'url':URL,'locator':locator,'supports':supports}]
    p['conditions']['additional_conditions']=[
        {'name':'test_relative_humidity','fact':{'status':'not_reported_in_inspected_source','text':None,'evidence':[],'notes':'Not reported; no laboratory humidity default.'}},
        {'name':'support_span','fact':{'status':'reported','text':'10 mm','evidence':ev('Section 2.2.8, three-point bending',['condition']),'notes':'Literal source value; not a tensile gauge length.'}},
        {'name':'bending_strain_setting','fact':{'status':'reported','text':'Source wording: constant strain of 1% until yield','evidence':ev('Section 2.2.8, three-point bending',['condition']),'notes':'Keep source wording; not a verified strain rate, fitting interval or oscillatory amplitude.'}}]
    p['method_definition']['definition']=method;p['method_definition']['extraction_window']=None
    p['sample_count']['scope']='At least five mechanical-test replicates for the selected source group; exact count and independent production-batch count not stated.'
    p['scope_note']='Only existing purified PHBV-39 operational-day sample and common hot-pressed cut specimen preparation from section 2.2.8. 39 is not 39% HV. This is source-reported flexural modulus, not Young modulus or oscillatory storage modulus. Post-press conditioning/RH, exact numerical room temperature, fit algorithm and per-time bending rate remain unknown; no clinical/biodegradation qualification inferred.'
    def update(node):
        if isinstance(node,dict):
            if node.get('source_id')==SID and 'locator' in node:
                node['url']=URL
                node['locator']='Table 9, PHBV-39 row, Flexural Modulus (GPa), mean/SD footnote; section 2.2.8' if 'Table 9' in node['locator'] else 'Section 2.2.8, common specimen preparation and three-point bending method'
            for v in node.values():update(v)
        elif isinstance(node,list):
            for v in node:update(v)
    update(p)
    scope='Retained primary XML Table 9 PHBV-39 flexural modulus and footnotes; section 2.2.8 common preparation/bending; article permission notice. No fresh PDF visual inspection or independent review this round.'
    p['source_document'].update(url=URL,revision='Retained PMC9571417 XML; PDF hash is a different asset.',inspected_on='2026-11-03',sha256=SHA,inspection_scope=scope)
    p['verification']['source_inspection_scope']=scope
    state=deepcopy(before.states[old['material_state_id']]);state['version']='1.0.1';state['property_ids'].append(pid)
    state['name']='Purified PHBV-39, hot-pressed cut specimens'
    state['names']={'en':state['name'],'zh':'提纯PHBV-39，热压切割试样','ja':'精製PHBV-39、熱プレス切断試験片','de':'Gereinigtes PHBV-39, heißgepresste geschnittene Proben'}
    source=deepcopy(before.sources[SID]);assert URL not in source['urls'];source['urls'].append(URL)
    source['claim_notes'].append('2026-11-03 curator XML supplement draft: PHBV-39 flexural modulus from Table 9 and common hot-pressed specimens/three-point bending section 2.2.8. Mechanical mean/SD is not assigned to composition assay uncertainty; exact bending rate and fit window remain unknown. Pending independent review.')
    data=deepcopy(before.data);data['reference_properties']['records'].append(p)
    data['materials']['records']=[state if x['id']==state['id'] else x for x in data['materials']['records']]
    data['sources']['records']=[source if x['id']==SID else x for x in data['sources']['records']]
    after=Database(data);contracts=after.validate_scientific_contracts()
    assert all(after.properties[pid]==value for pid,value in before.properties.items())
    assert after.identities==before.identities and after.grades==before.grades and set(after.states)==set(before.states)
    assert Database().snapshot==BASE
    out.mkdir(parents=True);tables=out/'native-tables';tables.mkdir()
    for name,value in data.items():write(tables/(name+'.json'),value)
    write(out/'native-candidate-r1.json',{'stage':'draft_not_applied_pending_independent_review','baseline_snapshot':BASE,'materials':{'identities':[],'grades':[],'records':[state]},'sources':{'records':[source]},'reference_properties':{'records':[p]}})
    write(out/'VALIDATION_R1.json',{'baseline_snapshot':BASE,'preview_snapshot':after.snapshot,'new_properties':1,'new_identities':0,'new_states':0,'new_sources':0,'all_existing_property_objects_unchanged':True,'contracts':contracts,'independent_review':'pending','native_applied':False,'full_history_regression':'not_run','pushed':False})
    print(json.dumps({'new_properties':1,'preview_snapshot':after.snapshot,'contracts':contracts}))


if __name__=='__main__':main()
