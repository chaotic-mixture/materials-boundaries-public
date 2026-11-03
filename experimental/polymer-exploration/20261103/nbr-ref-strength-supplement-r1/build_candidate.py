"""REF tensile strength plus scoped wording corrections on its existing source family."""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT))
from materials_boundaries.database import Database
PACKET=Path(__file__).resolve().parent
BASE='a0068f8c22fc94cdfb893fda69585b1a416811b937ed2b2b558a803feded0456'
SID='tamas_benyei_santha_2025_nbr_rcf'
URL='https://www.ebi.ac.uk/europepmc/webservices/rest/PMC12750214/fullTextXML'


def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,obj):
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
def patch_version(version):
    a,b,c=version.split('.');return f'{a}.{b}.{int(c)+1}'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--xml',type=Path,required=True);parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args();out=args.output_dir.resolve();assert not out.exists() and not out.is_relative_to(ROOT/'materials_boundaries')
    facts=read(PACKET/'SOURCE_READBACK_R1.json');assert sha(args.xml)==facts['primary_xml']['sha256']
    before=Database();assert before.snapshot==BASE
    density=before.properties['refprop_perbunan3445f_tamas_benyei2025_ref_mass_density']
    old=before.properties['refprop_tamas_benyei2025_nbr_mcf20_tensile_strength']
    prop=deepcopy(old);pid='refprop_perbunan3445f_tamas_benyei2025_ref_tensile_strength';assert pid not in before.properties
    prop.update(id=pid,version='1.0.0',material_state_id=density['material_state_id'])
    prop['reported_value'].update(number='6.01',value_text='6.01')
    prop['uncertainty'].update(number='1.15',value_text='1.15',scope='Selected REF tensile-strength group pooled across tested orientations; no CI, bound or allowable inferred.')
    prop['uncertainty_note']='6.01 ± 1.15 MPa: preserve the printed amplitude as reported_plus_minus_unspecified. Hardness/abrasion statistics and the adjacent strain-at-break SD discussion do not unambiguously define tensile-strength dispersion.'
    prop['sample_count']['scope']='Selected unfilled REF tensile-test group pooled across orientations; exact per-direction/specimen/independent-batch counts unknown.'
    prop['scope_note']='Existing nonfoamed REF formulation: PERBUNAN 3445 F NBR with fixed Table 3 additives and 0 phr mCF, not pure/raw NBR, a new grade, D or D_Fo foam. Same nominal 2 mm vulcanized sheet and processing as the existing REF density state. Tensile mean is pooled across two tested orientations; no universal isotropy or direction-specific value inferred. Density method, aggregation, uncertainty and sample count remain separately unknown. Preserve the abstract-versus-Table 4 disagreement; no reinforcement-benefit claim, source repair, default test environment or engineering allowable. M100/M200 not imported as Young modulus.'
    prop['source_discrepancies'][0]['disposition']='Retain Table 4 REF 6.01 MPa and D 5.33 MPa without adjustment, inferred correction or a 15% performance-improvement claim. This record adds a source-qualified REF tensile property under the existing identity/state; it neither adds a new identity nor validates the source-wide claims.'
    def update_evidence(node):
        if isinstance(node,dict):
            if node.get('source_id')==SID and 'locator' in node:
                loc=node['locator'];node['url']=URL
                node['locator']=('Primary XML Table 4 REF tensile-strength cell; section 3.3 pooled tensile results and abstract/Table 4 comparison' if 'Table 4' in loc else 'Primary XML sections 2.2, 2.3 and 3.3: tensile protocol, sheet preparation and pooling across orientations')
            for child in node.values():update_evidence(child)
        elif isinstance(node,list):
            for child in node:update_evidence(child)
    update_evidence(prop)
    scope='Fresh retained Europe PMC XML: permissions and separately credited Figure 1 exclusion, sections 2.1–2.3/Table 3 REF identity and preparation, Table 4 REF strength and section 3.3 pooling, abstract/Table 4 disagreement; section 3.4 density checked separately. University PDF retrieval failed this round; no fresh PDF hash or visual check claimed.'
    prop['source_document'].update(url=URL,revision='Primary Europe PMC full-text XML; distinct from the historically inspected university PDF.',inspected_on='2026-11-03',sha256=facts['primary_xml']['sha256'],inspection_scope=scope)
    prop['verification']['source_inspection_scope']=scope
    modified=[]
    for row in facts['existing_six_composite_rows_crosschecked']:
        oldp=before.properties[row['existing_property_id']];changed=deepcopy(oldp)
        assert changed['reported_value']['number']==row['strength_MPa'] and changed['uncertainty']['number']==row['plus_minus_MPa']
        text=changed['source_discrepancies'][0]['disposition']
        suffix='REF is comparison evidence only and not added as a new property or identity.';assert suffix in text
        changed['source_discrepancies'][0]['disposition']=text.replace(suffix,'Within this composite property record REF is comparison evidence, not a second recorded material. Separately admitted REF properties keep independent stable IDs and property-specific conditions; this comparator role does not deny their existence elsewhere in the catalog.')
        changed['version']=patch_version(changed['version'])
        probe=deepcopy(changed);probe['version']=oldp['version'];probe['source_discrepancies'][0]['disposition']=oldp['source_discrepancies'][0]['disposition'];assert probe==oldp
        modified.append(changed)
    state=deepcopy(before.states[density['material_state_id']]);state['version']=patch_version(state['version']);state['property_ids'].append(pid)
    ev=lambda locator:[{'source_id':SID,'url':URL,'locator':locator,'supports':['state']}]
    state['state']['orientation']={'status':'reported','text':'Tensile specimens tested in two mutually perpendicular orientations; source results pooled across orientations.',
        'evidence':ev('Primary XML sections 2.2 and 3.3, tensile direction testing and pooled results'),'notes':'Material axes, pooling weights and universal isotropy are not established; scalar density has no directional-axis claim.'}
    state['state']['conditioning']['notes']='Density- and tensile-specific post-cure conditioning, humidity, moisture and storage intervals are unreported; no standard laboratory default is assigned.'
    state['source_scope']='Existing additive-containing nonfoamed REF compound, not raw NBR or D_Fo foam. Density metrology/aggregation/±/n remain unknown independently of the new tensile mean and source ISO 37 procedure. Tensile results are pooled across two orientations, without a universal isotropy claim; count and ± type remain unknown. ACTMIX S-80 is as-added product loading, not inferred elemental sulfur. M100/M200 are not Young modulus and remain outside this mapping. Figure 1 third-party material excluded.'
    source=deepcopy(before.sources[SID]);source['urls'] += [u for u in [URL,'https://pmc.ncbi.nlm.nih.gov/articles/PMC12750214/'] if u not in source['urls']]
    source['claim_notes'].append('2026-11-03 primary XML supplement: REF Table 4 tensile mean 6.01 ± 1.15 MPa, pooled across orientations, unknown tensile ± type and count. Existing REF density stays unchanged and does not inherit tensile methods/statistics. Six older composite-property discrepancy notes now explicitly limit REF comparator wording to the corresponding record; all numerical/statistical fields unchanged. Abstract 15% improvement claim remains contradicted by Table 4 D5.33 versus REF6.01. Fresh XML inspected; university PDF retrieval failed, so the old PDF digest is not a new acquisition or visual-review claim.')
    data=deepcopy(before.data);changes={p['id']:p for p in modified}
    data['reference_properties']['records']=[changes.get(p['id'],p) for p in data['reference_properties']['records']]+[prop]
    data['materials']['records']=[state if s['id']==state['id'] else s for s in data['materials']['records']]
    data['sources']['records']=[source if s['id']==SID else s for s in data['sources']['records']]
    after=Database(data);contracts=after.validate_scientific_contracts()
    assert after.properties[density['id']]==density
    assert all(after.properties[k]==v for k,v in before.properties.items() if k not in changes)
    assert after.identities==before.identities and after.grades==before.grades and set(after.states)==set(before.states)
    out.mkdir(parents=True);tables=out/'native-tables';tables.mkdir()
    for name,value in data.items():write(tables/(name+'.json'),value)
    write(out/'native-candidate-r1.json',{'baseline_snapshot':BASE,'stage':'frozen_not_applied','materials':{'identities':[],'grades':[],'records':[state]},'sources':{'records':[source]},'reference_properties':{'records':modified+[prop]}})
    write(out/'VALIDATION_R1.json',{'baseline_snapshot':BASE,'preview_snapshot':after.snapshot,'new_properties':1,'revised_property_scope_wording':6,'revision_fields_only':['version','source_discrepancies[0].disposition'],'all_existing_numeric_statistical_fields_unchanged':True,'existing_REF_density_object_unchanged':True,'new_identities':0,'new_states':0,'modified_states':1,'modified_sources':1,'contracts':contracts,'native_applied':False,'pushed':False,'full_history_regression':'not_run'})
    print(json.dumps({'snapshot':after.snapshot,'properties':len(after.properties),'contracts':contracts}))


if __name__=='__main__':main()
