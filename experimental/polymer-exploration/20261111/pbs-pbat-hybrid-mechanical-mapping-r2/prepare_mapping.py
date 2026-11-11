"""Six mechanical facts on existing states,without native writes or new identities."""
from pathlib import Path
from copy import deepcopy
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[4]; HERE=Path(__file__).resolve().parent
SOURCE=HERE.parent/'pbs-pbat-hybrid-mechanical-source-r1'
sys.path.insert(0,str(ROOT))
from materials_boundaries.database import Database
from materials_boundaries.material_references import validate_material_catalog
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(n,v):
    with (HERE/n).open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
    entry=SOURCE/'REVIEW_INPUTS_R1.json';receipt=read(SOURCE/'INDEPENDENT_SOURCE_REVIEW_R1.json')
    assert receipt['decision']=='approved' and receipt['review_inputs_sha256']==sha(entry)
    for field in ('repo_files_sha256','external_files_sha256','native_files_sha256'):
        for n,h in read(entry)[field].items():assert sha(Path(n) if field=='external_files_sha256' else ROOT/n)==h,n
    before=Database();assert before.snapshot=='6f4639bd62872a0cab8348a651d82c026bf129a18252de9cc30fce247cb86d88'
    data=deepcopy(before.data);props=[];updates={};sid='mtibe_2022_pbs_pbat_lignin_zno'
    url='https://mdpi-res.com/d_attachment/polymers/polymers-14-05065/article_deploy/polymers-14-05065.pdf'
    for fact in read(SOURCE/'SOURCE_FACTS_R1.json'):
        q=fact['quantity_proposed'];base=before.states[fact['existing_state_id']]
        p=deepcopy(before.properties['refprop_mtibe2022_pbs_pbat_70_30_'+q])
        p.update(id=base['id'].replace('state_','refprop_',1)+'_'+q,material_state_id=base['id'],source_property_label=fact['source_property_label'])
        p['reported_value'].update(number=fact['number'],value_text=fact['number'])
        p['uncertainty'].update(number=fact['plus_minus_number'],value_text=fact['plus_minus_number'])
        p['uncertainty_note']=fact['number']+' ± '+fact['plus_minus_number']+' '+fact['unit_text']+': source does not define central estimator or ± as SD,SE,CI,range or tolerance. Five tensile specimens per hybrid group are not independent batches;two quantities do not imply ten specimens.'
        def repin(v):
            if isinstance(v,dict):
                if {'source_id','url','locator','supports'}<=v.keys():
                    v['url']=url
                    v['locator']=('PDF p7section3.2 narrative167percent claim;Table3 comparison' if 'source_discrepancy' in v['supports'] else fact['source_cell_locator'] if any(t in v['supports'] for t in ('reported_value','uncertainty','classification')) else 'PDF p5section2.6.2 tensile protocol;PDF p3section2.3 preparation')
                for x in v.values():repin(x)
            elif isinstance(v,list):
                for x in v:repin(x)
        repin(p)
        for d in p['source_discrepancies']:
            d['disposition']=d['disposition'].replace('outside these selected unfilled rows','separate from the selected literal Table3 results')
        p['sample_count'].update(scope='Five tensile specimens per selected hybrid composite group,shared across its reported tensile properties;not ten independent specimens or five independent production batches.',source_statement='Section2.6.2 explicitly includes hybrid composites at5,10,15wt%lignin with1.5wt%ZnO among groups with five specimens each.')
        scope='Official PDF p7Table3 selected hybrid row;PDF p3Tables1-2/section2.3 andp5section2.6.2;same-byte EuropePMC XML cross-check. Raw curves and individual specimens not reanalysed;latest notice completeness unknown.'
        p['source_document'].update(url=url,revision='Reacquired byte-identical official PDF;latest revision/notices unverified',inspected_on='2026-11-11',sha256='fa72f3441329d8db6348926906817ebac7b3bd7077a90e836f75f8ecdb087287',inspection_scope=scope)
        p['verification'].update(source_inspection_scope=scope)
        p['scope_note']=before.identities[base['identity_id']]['identity_scope']+' Selected Table3 '+fact['source_property_label']+' for the existing hybrid formulation. Group n5 and25C48h tensile conditioning apply to the explicit hybrid group,not thermal testing or independent batches. Test/conditioning RH,numerical rate,gauge geometry,direction and statistical estimator unknown. Recipe70/30 basis andZnO1.5 denominator unresolved;not normalized. Catalog-only,not an engineering allowable or automatic mechanics input.'
        if q=='tensile_yield_strength':
            p['source_discrepancies'].append(dict(description='Table3 labels Tensile Strength at Yield;nearby prose uses generic tensile strength andat-break wording.',disposition='Preserve table-labelled yield quantity without diagnosing author error or converting to tensile maximum/break strength. Yield criterion andoffset/upper/lower event unknown;no narrative percentage-change values imported.',evidence=[dict(source_id=sid,url=url,locator='PDF p6-7section3.2/Table3',supports=['source_discrepancy'])]))
        assert p['id'] not in before.properties
        props.append(p)
        if base['id'] not in updates:
            assert base['version']=='1.0.0';updates[base['id']]=dict(before=deepcopy(base),after=deepcopy(base))
            updates[base['id']]['after']['version']='1.0.1'
        updates[base['id']]['after']['property_ids'].append(p['id'])
    data['reference_properties']['records'].extend(props)
    data['materials']['records']=[updates[s['id']]['after'] if s['id'] in updates else s for s in data['materials']['records']]
    validate_material_catalog(*(data[n] for n in ('materials','reference_properties','sources')));after=Database(data)
    assert len(props)==6 and len(updates)==3 and len(after.properties)==5504 and len(after.states)==5301
    assert before.sources==after.sources and before.identities==after.identities and before.grades==after.grades
    assert all(after.properties[k]==v for k,v in before.properties.items())
    for k,v in before.states.items():
        if k not in updates:assert after.states[k]==v
        else:assert {n:x for n,x in v.items() if n not in ('version','property_ids')}=={n:x for n,x in after.states[k].items() if n not in ('version','property_ids')}
    write('NEW_PROPERTIES_R1.json',props);write('STATE_UPDATES_R1.json',list(updates.values()))
    write('VALIDATION_R1.json',dict(baseline_snapshot=before.snapshot,candidate_snapshot=after.snapshot,properties=5504,states=5301,sources=len(after.sources),new_properties=6,new_states=0,revised_existing_states=3,state_changed_fields=['version','property_ids'],old5498properties_unchanged=True,other5298states_unchanged=True,identities_grades_sources_unchanged=True,native_applied=False,installation='not_run'))
    print(json.dumps(dict(snapshot=after.snapshot,new_properties=6,revised_states=3,native_applied=False)))
if __name__=='__main__':main()
