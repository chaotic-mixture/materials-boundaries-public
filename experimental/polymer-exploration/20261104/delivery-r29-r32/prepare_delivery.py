"""Bind accepted local rounds and prepare current consolidated delivery documents."""
from pathlib import Path
from collections import Counter
import hashlib,json,subprocess,sys
ROOT=Path(__file__).resolve().parents[4]
OUT=Path(__file__).resolve().parent
BASE='1893455b0dc75d9ac7e7c27fc798efd7de8a0d04'
sys.path.insert(0,str(ROOT))
from materials_boundaries.database import Database
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def write(p,d):
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(d,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
    assert subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==BASE
    assert subprocess.check_output(['git','branch','--show-current'],text=True).strip()=='experimental/open-database'
    assert not subprocess.check_output(['git','diff','--cached','--name-only'])
    final=OUT.parent/'local-acceptance-r32/REVIEW_INPUTS_R32.json'
    r=read(final.with_name('INDEPENDENT_ACCEPTANCE_REVIEW_R32.json'));assert r['decision']=='clear' and r['review_inputs_sha256']==sha(final)
    for field in ['repo_files_sha256','external_files_sha256']:
        for n,h in read(final)[field].items():assert sha(Path(n) if field=='external_files_sha256' else ROOT/n)==h,n
    before=Database({n:json.loads(subprocess.check_output(['git','show',BASE+':materials_boundaries/data/'+n+'.json'])) for n in ['materials','reference_properties','sources']})
    after=Database();assert after.snapshot=='698db32a4105434eeae26fd5724c709b2cec5bb965875ff1bf73ef5ec54cd726'
    assert len(before.properties)==5335 and len(after.properties)==5371 and len(before.states)==5218 and len(after.states)==5245
    assert all(after.properties[k]==v for k,v in before.properties.items()) and all(after.states[k]==v for k,v in before.states.items())
    assert after.identities==before.identities and after.grades==before.grades and set(after.sources)==set(before.sources)
    added=sorted(set(after.properties)-set(before.properties));states=sorted(set(after.states)-set(before.states))
    assert len(added)==36 and len(states)==27
    changed=sorted(k for k in before.sources if before.sources[k]!=after.sources[k]);assert changed==['delgado_aguilar_2020_pla_pcl','ewurum_mcdonald_2025_pbs_lignin']
    chain={};previous=before.snapshot
    for stage in ['r29','r30','r31','r32']:
        folder=OUT.parent/('local-acceptance-'+stage);suffix=stage.upper()
        entry=folder/('REVIEW_INPUTS_'+suffix+('_R2' if stage=='r29' else '')+'.json')
        review=read(folder/('INDEPENDENT_ACCEPTANCE_REVIEW_'+suffix+'.json'));app=read(folder/('APPLICATION_'+suffix+'.json'))
        assert review['decision']=='clear' and review['review_inputs_sha256']==sha(entry)
        assert app['before_snapshot']==previous;previous=app['after_snapshot']
        chain[stage]={'input_sha256':sha(entry),'review_sha256':sha(folder/('INDEPENDENT_ACCEPTANCE_REVIEW_'+suffix+'.json')),'decision':'clear','after_snapshot':previous}
    assert previous==after.snapshot
    quantities=dict(Counter(after.properties[k]['quantity'] for k in added))
    assert quantities=={'glass_transition_temperature':9,'melting_peak_temperature':9,'flexural_strength':9,'flexural_modulus':9}
    facts={'property_records':{k:after.properties[k] for k in added},'state_records':{k:after.states[k] for k in states},'source_records':{k:after.sources[k] for k in changed},'source_counts':{k:len(list(after.records(source=k))) for k in changed},'rows':[{'id':k,'quantity':after.properties[k]['quantity'],'value_text':after.properties[k]['reported_value']['value_text']} for k in added]}
    assert facts['source_counts']=={'delgado_aguilar_2020_pla_pcl':25,'ewurum_mcdonald_2025_pbs_lignin':55}
    write(OUT/'SOURCE_FACTS_R29_R32.json',facts)
    write(OUT/'NATIVE_DELTA_R29_R32.json',{'baseline_commit':BASE,'baseline_snapshot':before.snapshot,'current_snapshot':after.snapshot,'old_complete_properties_unchanged':5335,'old_complete_states_unchanged':5218,'new_properties':36,'new_properties_by_quantity':quantities,'new_property_ids':added,'new_state_ids':states,'new_states':27,'new_identities':0,'new_grades':0,'new_sources':0,'existing_state_changes':{},'source_changes':{'ewurum_mcdonald_2025_pbs_lignin':'three appended notes','delgado_aguilar_2020_pla_pcl':'approved PDF inspection metadata and official links'},'local_acceptance_chain':chain,'polymer_summary':after.summary(category='polymer'),'independent_physical_coverage':'not established;includes9 unresolved flexural contexts'})
    docs=['README.md','HANDOFF.md','docs/DATABASE_COVERAGE.zh.md','docs/MATERIAL_SOURCE_CONDITIONS.zh.md','docs/OPEN_DATABASE_ROADMAP.zh.md'];binding={}
    for name in docs:
        p=ROOT/name;arc=OUT/'pre-delivery-documents'/name;arc.parent.mkdir(parents=True,exist_ok=True);assert not arc.exists();arc.write_bytes(p.read_bytes())
        link=('../' if name.startswith('docs/') else '')+'experimental/polymer-exploration/20261104/delivery-r29-r32/README.zh.md'
        header='\n\n## r29–r32聚合物累计交付核验（2026-11-04）\n\n当前全库5180身份、31牌号、5245目录状态记录、5371性质、133来源。四轮已独审本地接纳：既有PBS配方补36条性质和27目录状态，PLA/PCL来源补PDF检查范围及链接；原5335性质、5218状态对象完整保持，无新身份／牌号／来源。目录情境不认证独立物理覆盖。\n\n聚合物1037身份、1078状态记录、1180性质（1000计算／180实验参考标签）。113条实验性质温度未报、128条调湿未报，111条确切n未确认；来源未支持的条件继续未知。弯曲两项性质共享来源n=8组，不计16次独立实验；DMA、DSC及弯曲方法不混同。\n\n[统一交付证据]('+link+')记录当前测试、实际安装、目录读取和后续提交／CI各自范围；缺少精确回执不视为通过。重建安装包及统一验收以本轮精确回执为准，缺少回执不视为完成；不冒用r31旧包作为当前三表等价证据。软件版本仍0.35.0。仅实验分支交付，不合并main、不稳定发布、不部署。以下保留旧检查点原文。\n\n'
        raw=p.read_bytes();cut=raw.find(b'\n')+1;p.write_bytes(raw[:cut]+header.encode('utf-8')+raw[cut:])
        binding[name]={'before_sha256':sha(arc),'archive_path':arc.relative_to(ROOT).as_posix(),'current_sha256':sha(p)}
    write(OUT/'PREDELIVERY_DOCUMENT_BINDING_R29_R32.json',binding)
    print(json.dumps({'snapshot':after.snapshot,'new_properties':36,'new_states':27,'old_objects_unchanged':True}))
if __name__=='__main__':main()
