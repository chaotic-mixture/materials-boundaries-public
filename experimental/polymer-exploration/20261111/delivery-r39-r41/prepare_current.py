"""Record the cumulative delta and update navigation without altering milestones."""
from pathlib import Path
from collections import Counter
import hashlib,json,shutil,subprocess
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
EXT=ROOT.parent/'open-database-evidence/polymer-consolidated-delivery-20261111-r39-r41'
BASELINE='ba67983dc11ee8c92ef1c9890b4164adfaf4a83d'
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(n,obj):
    with (HERE/n).open('x',encoding='utf-8',newline='\n') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==BASELINE
    assert subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()=='experimental/open-database'
    assert subprocess.run(['git','diff','--cached','--quiet'],cwd=ROOT).returncode==0
    (EXT/'baseline-tables').mkdir(parents=True,exist_ok=False)
    before={};after={}
    for n in ('materials','reference_properties','sources'):
        raw=subprocess.check_output(['git','show',BASELINE+':materials_boundaries/data/'+n+'.json'],cwd=ROOT)
        (EXT/'baseline-tables'/f'{n}.json').write_bytes(raw)
        before[n]=json.loads(raw);after[n]=read(ROOT/f'materials_boundaries/data/{n}.json')
    assert before['materials']['identities']==after['materials']['identities']
    assert before['materials']['grades']==after['materials']['grades']
    oldp={p['id']:p for p in before['reference_properties']['records']};newp={p['id']:p for p in after['reference_properties']['records']}
    assert all(newp[k]==v for k,v in oldp.items())
    oldst={s['id']:s for s in before['materials']['records']};newst={s['id']:s for s in after['materials']['records']}
    changed={k:dict(before=oldst[k],after=newst[k]) for k in oldst if oldst[k]!=newst[k]}
    assert set(changed)=={'state_smr10_bianchi2025_nr'}
    for item in changed.values():
        a,b=item['before'],item['after']
        assert {k:v for k,v in a.items() if k not in ('version','property_ids','source_scope')}=={k:v for k,v in b.items() if k not in ('version','property_ids','source_scope')}
        assert b['property_ids'][:len(a['property_ids'])]==a['property_ids'] and len(b['property_ids'])==len(a['property_ids'])+1
        assert b['source_scope'].startswith(a['source_scope']) and (a['version'],b['version'])==('1.0.3','1.0.4')
    addedp=[p for k,p in newp.items() if k not in oldp];addeds=[s for k,s in newst.items() if k not in oldst]
    assert len(addedp)==4 and len(addeds)==1
    assert {p['quantity'] for p in addedp}=={'volumetric_tensile_work_to_break','mass_specific_heat_capacity','thermal_diffusivity','thermal_conductivity'}
    a={s['id']:s for s in before['sources']['records']};b={s['id']:s for s in after['sources']['records']};assert a.keys()==b.keys()
    source_changes={k:[n for n in a[k] if a[k][n]!=b[k][n]] for k in a if a[k]!=b[k]}
    assert source_changes=={'bianchi_2025_nr_nanoclay':['urls','claim_notes']}
    for key in ('urls','claim_notes'):assert b['bianchi_2025_nr_nanoclay'][key][:len(a['bianchi_2025_nr_nanoclay'][key])]==a['bianchi_2025_nr_nanoclay'][key]
    snapshot=hashlib.sha256(json.dumps(after,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
    assert snapshot=='54b06dfa38f09e3a65f79522674f554115953a991008b49c2f6770ed84fc8275'
    identities={i['id']:i for i in after['materials']['identities']}
    polymer=[p for p in newp.values() if identities[newst[p['material_state_id']]['identity_id']]['category']=='polymer']
    direct=[p for p in polymer if p['evidence_kind']=='published_experimental_reference']
    counts=dict(identities=len(identities),grades=len(after['materials']['grades']),states=len(newst),properties=len(newp),sources=len(b))
    polycounts=dict(identities=sum(i['category']=='polymer' for i in identities.values()),states=sum(identities[s['identity_id']]['category']=='polymer' for s in newst.values()),properties=len(polymer),by_evidence_kind=dict(Counter(p['evidence_kind'] for p in polymer)),direct_experimental_unknowns=dict(temperature_not_reported=sum(p['conditions']['temperature']['status']=='not_reported_in_inspected_source' for p in direct),conditioning_not_reported=sum(p['conditions']['conditioning']['status']=='not_reported_in_inspected_source' for p in direct),exact_n_unconfirmed=sum(p['sample_count']['relation']!='exact' or p['sample_count']['value'] is None for p in direct)))
    write('NATIVE_DELTA_R39_R41.json',dict(baseline_commit=BASELINE,baseline_properties_states=[len(oldp),len(oldst)],counts=counts,polymer_counts=polycounts,snapshot=snapshot,new_properties=addedp,new_states=addeds,existing_state_updates=changed,old5412properties_unchanged=True,old_state_physical_facts_unchanged=True,identities_grades_unchanged=True,source_field_changes=source_changes))
    write('APPLICATION_R39_R41.json',dict(scope='Cumulative binding,not a new table application',snapshot=snapshot,after_sha256={f'materials_boundaries/data/{n}.json':sha(ROOT/f'materials_boundaries/data/{n}.json') for n in after}))
    names=['README.md','HANDOFF.md','docs/DATABASE_COVERAGE.zh.md','docs/MATERIAL_SOURCE_CONDITIONS.zh.md','docs/OPEN_DATABASE_ROADMAP.zh.md'];backups={}
    for n in names:
        path=ROOT/n;backup=EXT/'before-docs'/n;backup.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,backup)
        backups[n]=dict(sha256=sha(backup),resolved_path_hint=str(backup))
        text=path.read_text('utf-8');assert text.count('## 当前聚合物进展：r36–r38')==1
        text=text.replace('## 当前聚合物进展：r36–r38','## 当前本地聚合物进展：r39–r41（尚未统一推送）',1)
        text=text.replace('experimental/polymer-exploration/20261104/delivery-r36-r38/README.zh.md','experimental/polymer-exploration/20261111/delivery-r39-r41/README.zh.md',1)
        text=text.replace('当前全库5412条性质、5262个状态；本轮累计新增32条性质、8个状态。','当前全库5416条性质、5263个状态；本轮累计新增4条性质、1个状态、0材料身份。来源计算热导率与直接实验类别分开，未知项保留。',1)
        path.write_text(text,encoding='utf-8',newline='\n')
    write('BEFORE_DOCUMENT_BYTES_R39_R41.json',backups)
    print(json.dumps(dict(counts=counts,polymer=polycounts,delta_properties=4,delta_states=1,navigation_files=len(names)),ensure_ascii=False))
if __name__=='__main__':main()
