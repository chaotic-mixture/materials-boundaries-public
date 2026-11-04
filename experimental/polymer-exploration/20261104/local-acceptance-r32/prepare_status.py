"""Document source-only acceptance and resolve previous immutable input contexts."""
from pathlib import Path
from copy import deepcopy
import hashlib,json,shutil,subprocess,sys
ROOT=Path(__file__).resolve().parents[4]
OUT=Path(__file__).resolve().parent
AREA=OUT.parent
EXT=ROOT.parent/'open-database-evidence'
sys.path.insert(0,str(ROOT))
from materials_boundaries.database import Database
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(d,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
    assert not (OUT/'FINAL_LOCAL_STATUS_R32.zh.md').exists()
    db=Database();app=read(OUT/'APPLICATION_R32.json');tests=read(OUT/'DAILY_TEST_RESULTS_R32.json')
    inventory=read(AREA/'condition-gaps-native-r32/INVENTORY_R3.json')
    assert db.snapshot==app['after_snapshot']==tests['snapshot']==inventory['snapshot']
    assert tests['tests_run']==19 and tests['successful'] and tests['failures']==tests['errors']==tests['skipped']==0
    old=read(AREA/'condition-gaps-native-r31/INVENTORY_R3.json')
    assert all(inventory[k]==v for k,v in old.items() if k!='snapshot')
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    assert head=='1893455b0dc75d9ac7e7c27fc798efd7de8a0d04'
    baseline=Database({n:json.loads(subprocess.check_output(['git','show',head+':materials_boundaries/data/'+n+'.json'],cwd=ROOT)) for n in db.data})
    assert all(db.properties[k]==v for k,v in baseline.properties.items()) and all(db.states[k]==v for k,v in baseline.states.items())
    assert db.identities==baseline.identities and db.grades==baseline.grades and set(db.sources)==set(baseline.sources)
    unionprops={};unionstates={}
    for name in ['pbs-existing-dsc-native-r1','pbs-existing-dma-tg-native-r1','pbs-existing-flexural-native-r1']:
        f=read(AREA/name/'MAPPING_FACTS_R1.json');unionprops.update(f['property_records']);unionstates.update(f['state_records'])
    assert len(unionprops)==36 and len(unionstates)==27
    assert set(db.properties)-set(baseline.properties)==set(unionprops) and all(db.properties[k]==v for k,v in unionprops.items())
    assert set(db.states)-set(baseline.states)==set(unionstates) and all(db.states[k]==v for k,v in unionstates.items())
    changed={k for k in baseline.sources if db.sources[k]!=baseline.sources[k]}
    assert changed=={'ewurum_mcdonald_2025_pbs_lignin','delgado_aguilar_2020_pla_pcl'}
    sid='ewurum_mcdonald_2025_pbs_lignin';restored=deepcopy(db.sources[sid]);assert len(restored['claim_notes'])==len(baseline.sources[sid]['claim_notes'])+3;restored['claim_notes']=restored['claim_notes'][:-3];assert restored==baseline.sources[sid]
    f=read(AREA/'pla-pcl-source-metadata-native-r1/MAPPING_FACTS_R1.json');assert db.sources[f['source_id']]==f['source_record'] and baseline.sources[f['source_id']]==f['baseline_source']
    write(OUT/'CUMULATIVE_LOCAL_DELTA_R29_R32.json',{'baseline_commit':head,'current_snapshot':db.snapshot,'all5335_baseline_properties_unchanged':True,'all5218_baseline_states_unchanged':True,'new_properties':36,'new_catalog_state_records':27,'new_identities_grades_sources':0,'source_records_changed':sorted(changed),'source_changes':'Ewurum exactly3 appended notes;Delgado reviewed PDF inspection scope and links only','independent_physical_coverage':'not_established','full_history_regression':'not_run;three Git blobs compared only','pushed':False})
    docs=['README.md','HANDOFF.md','docs/DATABASE_COVERAGE.zh.md','docs/MATERIAL_SOURCE_CONDITIONS.zh.md','docs/OPEN_DATABASE_ROADMAP.zh.md']
    archive=OUT/'pre-r32-documents';archive.mkdir()
    link='experimental/polymer-exploration/20261104/local-acceptance-r32/FINAL_LOCAL_STATUS_R32.zh.md'
    for name in docs:
        p=archive/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,p)
    status='# r32：PLA/PCL来源元数据本地接纳\n\n已按精确独审候选更新一个既有来源的PDF检查范围、两个官方链接及追加说明；保留历史无PDF核验说明并解释其历史范围。25条关联导出携带更新来源，全部5371性质和5245状态对象保持不变；5180身份、31牌号、133来源数量不变。本批无新材料、性质、状态或物理覆盖。\n\n25条PLA/PCL性质的测试温度、RH、调湿、n、中心汇总及方向未知保持；不把模量SD转给强度／伸长率，不导入商业比较，不扩大许可。PDF选页、全部6页附件和具体来源更新经独审；最新修订、更正、撤稿状态未知。\n\n三表schema／格式、引用和完整图在精确预览核验，接纳以同字节三表继承。接纳后新运行19项数据库行为检查，0失败／错误／跳过；未重跑未变化的3项方法分支、完整历史、HTTP或平台全量。当前条件清单180条聚合物实验标签、113条温度未报、128条调湿未报、111条确切n未确认，与r31逐项相同。\n\nr31隔离安装包保留此前来源字节，不能称为包含本次更新。当前来源元数据尚未重新打包／安装；后续统一交付须重新冻结包输入、构建并核验。旧安装核验只适用于其冻结范围，不冒充当前三表等价。\n\n相对提交1893455，累计36条性质和27目录状态记录，原5335性质和5218状态完整不变；Ewurum来源追加3说明，Delgado来源更新本次检查范围。新目录情境不认证独立物理覆盖。本轮仍未提交／推送，无本批远端CI；未合并main、稳定发布或部署。主文档在测试之后更新，原执行输入另存，不声称对新文档重跑。\n\n当前数据库快照：`'+db.snapshot+'`。Git HEAD：`'+head+'`。\n'
    (OUT/'FINAL_LOCAL_STATUS_R32.zh.md').write_text(status,encoding='utf-8',newline='\n')
    for name in docs:
        original=(archive/name).read_text(encoding='utf-8');first,_,rest=original.partition('\n');target=('../' if name.startswith('docs/') else '')+link
        header='\n\n## 当前本地检查点：PLA/PCL来源更新 r32（2026-11-04）\n\n一个既有来源补充已独审PDF核验范围及官方链接，25条性质的未知条件保持；全库仍为5180身份、5245目录状态、5371性质。接纳后19项数据库检查通过。当前来源更新尚未重新打包，r31安装包只代表其原冻结范围。详见[当前本地证据]('+target+')。本批未提交／推送，无本批远端CI；不合并main、不稳定发布、不部署。\n\n以下保留旧检查点，旧计数、安装和CI仅适用于各自冻结范围。\n\n'
        (ROOT/name).write_text(first+header+rest,encoding='utf-8',newline='\n')
    contexts={};known=[]
    for c in read(AREA/'local-acceptance-r31/CONTEXT_RESOLUTION_R31.json')['contexts']:
        contexts[(c['entry'],c['field'])]=(ROOT/c['entry'],c['field'],{n:b['sha256'] for n,b in c['bindings'].items()});known.extend(Path(b['resolved_path']) for b in c['bindings'].values())
    for folder,file in [('local-acceptance-r31','REVIEW_INPUTS_R31.json'),('pla-pcl-pdf-condition-followup-r1','REVIEW_INPUTS_R1.json'),('pla-pcl-source-metadata-native-r1','REVIEW_INPUTS_R1.json')]:
        entry=AREA/folder/file;d=read(entry)
        for field in ['repo_files_sha256','native_files_sha256']:
            if field in d:contexts[(str(entry),field)]=(entry,field,d[field])
    contexts[('daily','input_sha256_before_and_after')]=(OUT/'DAILY_TEST_RESULTS_R32.json','input_sha256_before_and_after',tests['input_sha256_before_and_after'])
    known+=list(archive.rglob('*'))+list((EXT/'polymer-native-acceptance-20261104-r32/baseline-tables').glob('*'))
    index={sha(p):p for p in known if p.is_file()};resolved=[]
    for entry,field,pins in contexts.values():
        bindings={}
        for name,h in pins.items():
            current=ROOT/name;p=current if current.is_file() and sha(current)==h else index[h];assert sha(p)==h
            bindings[name]={'sha256':h,'resolved_path':str(p),'current':p==current}
        resolved.append({'entry':entry.relative_to(ROOT).as_posix(),'entry_sha256':sha(entry),'field':field,'bindings':bindings})
    write(OUT/'CONTEXT_RESOLUTION_R32.json',{'contexts':resolved,'binding_count':sum(len(c['bindings']) for c in resolved),'unresolved':0,'historical_manifests_rewritten':False})
    print(json.dumps({'snapshot':db.snapshot,'contexts':len(resolved),'binding_count':sum(len(c['bindings']) for c in resolved)}))
if __name__=='__main__':main()
