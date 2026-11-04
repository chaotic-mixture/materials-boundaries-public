"""Publish accurate local status and preserve previous frozen path contexts."""
from pathlib import Path
import json,hashlib,shutil,subprocess,sys

ROOT=Path(__file__).resolve().parents[4]
OUT=Path(__file__).resolve().parent
AREA=OUT.parent
EXT=ROOT.parent/'open-database-evidence'
sys.path.insert(0,str(ROOT))
from materials_boundaries.database import Database,read_snapshot
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def write(p,d):
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(d,f,ensure_ascii=False,indent=2);f.write('\n')

def main():
    assert not (OUT/'FINAL_LOCAL_STATUS_R30.zh.md').exists()
    db=Database();app=read(OUT/'APPLICATION_R30.json');tests=read(OUT/'DAILY_TEST_RESULTS_R30.json')
    inventory=read(AREA/'condition-gaps-native-r30/INVENTORY_R3.json')
    assert db.snapshot==app['after_snapshot']==tests['snapshot']==inventory['snapshot']
    assert tests['tests_run']==22 and tests['successful'] and tests['failures']==tests['errors']==tests['skipped']==0
    installed=EXT/'polymer-installed-preview-20261104-r30';site=installed/'venv/Lib/site-packages'
    payload={n:h for n,h in read(installed/'BUILD_INPUTS_R30.json')['staged_inputs'].items() if n.startswith('materials_boundaries/')}
    for n,h in payload.items():
        assert sha(site/n)==h,n
        if n!='materials_boundaries/_version.py':assert sha(ROOT/n)==h,n
    assert len(payload)==65
    _,exported=read_snapshot(installed/'installed-export-ewurum_mcdonald_2025_pbs_lignin')
    assert exported=={r['property']['id']:r for r in db.records(source='ewurum_mcdonald_2025_pbs_lignin')}
    write(OUT/'NATIVE_INSTALLED_EQUIVALENCE_R30.json',{'snapshot':db.snapshot,'installed_payload_files_verified':65,'nonversion_native_payload_equal_install':64,'three_native_tables_equal_installed':True,'complete_source_export_objects':len(exported),'baseline_version':'0.35.0','isolated_version':'0.35.0+polymerpreview.20261104.r30','version_difference':'Intentional isolated preview only;not a public release','full_history_regression':'not_run','pushed':False})
    stats=db.summary(category='polymer')
    assert (len(db.identities),len(db.grades),len(db.states),len(db.properties),len(db.sources))==(5180,31,5236,5353,133)
    assert (stats['material_identities'],stats['material_states'],stats['property_records'])==(1037,1077,1178)
    assert stats['properties_by_evidence_kind']=={'published_computational_reference':1000,'published_experimental_reference':178}
    assert (inventory['experimental_class_primary_sources'],inventory['experimental_class_identities'],inventory['experimental_class_states'])==(12,37,77)
    assert (inventory['sample_count_exact_confirmed'],inventory['sample_count_value_missing'],inventory['sample_count_reported_non_exact_value'],inventory['sample_count_exact_unconfirmed'])==(67,107,4,111)
    assert inventory['condition_status_counts']['temperature']['not_reported_in_inspected_source']==111
    assert inventory['condition_status_counts']['conditioning']['not_reported_in_inspected_source']==126
    write(OUT/'CURRENT_POLYMER_SUMMARY_R30.json',stats)
    docs=['README.md','HANDOFF.md','docs/DATABASE_COVERAGE.zh.md','docs/MATERIAL_SOURCE_CONDITIONS.zh.md','docs/OPEN_DATABASE_ROADMAP.zh.md']
    archive=OUT/'pre-r30-documents';archive.mkdir()
    for name in docs:
        target=archive/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
    write(OUT/'PRE_R30_DOCUMENT_BINDING.json',{n:sha(archive/n) for n in docs})
    text='# r30：既有 PBS 配方 DMA Tg 本地接纳\n\n9个既有配方补9条DMA tanδ峰Tg和9个物理条形试样状态，无新身份、牌号或来源。分类保持1个聚合物、8个聚合物基复合材料。R0继续排除；全部5344前驱性质、5227前驱状态完整不变，唯一来源只追加范围说明。\n\n全库5180身份、31牌号、5236状态、5353性质、133来源。聚合物1037身份、1077状态、1178性质（1000计算参考、178实验参考标签），实验来源12个、既有身份37个、状态77个；不将8个复合材料新增性质计入聚合物大类。\n\nTg按原文DMA tanδ最大值保存，保留1Hz、0.2%应变及其未知约定、−50至120°C／3°C/min、3×5×20mm、三点弯曲15mm跨距和Pyris v13.3。共同三次重复确认，仅作方法背景；选定单值n、汇总、不确定度、DMA条形成形路线、循环、预载、气氛及调湿仍未知。§3.5笼统DSC Tg与§3.4/Table3明确DMA的差异保留，不能拿DSC、TGA或注塑条件补齐。\n\n方法说明扩为来源限定Tg，区分DSC及DMA判据；量、单位、五个互斥分支、运行时及schema未改。同名／同数值不证明方法可比，不去重、平均或换算；只有方法标签变化不能增加物理状态覆盖。3项虚构方法检查的首次错误夹具、失败日志及修正保留，生产validator未改。\n\n来源、具体映射及实际安装／静态应用方案均有精确只读独审。65载荷／6元数据、71项wheel与76项installed RECORD、50缓存代码对象、64项非版本原生载荷及三表等价通过。实际安装新增Tg9、全局Tg15、旧熔融峰11、完整来源导出37及四语通过。冻结进程内查询组件核验9状态／9性质／37导出、副本隔离、stale拒绝及三表不变，不启动或认证HTTP、完整平台或科学合规。\n\n本地接纳后新运行22项检查（19数据库行为＋3方法保真），零失败／错误／跳过。先前19、3或180项不累计。5353图契约在隔离预览及实际安装核验；应用通过同字节三表继承，不再重复全图或完整历史回归。主文档更新在运行后完成，测试输入里的旧README另行保存，不声称测试针对更新后文档重跑。\n\n聚合物178条实验性质中，111条温度字段、126条调湿字段未报告；67确切n、107个n为空、4个下限，确切n未确认111条。计数是性质对象，不作独立试验组，扫描程序不等于环境温度。\n\n本批仅本地接纳，尚未提交／推送，无本批远端CI。历史1893455成功不代表本批。未合并main、稳定发布或部署，继续积累较大进度后统一推送。预览METADATA沿用应用前README，不能作本批公开发布文档。\n'
    text+='\n数据库快照：`'+db.snapshot+'`；Git HEAD：`'+subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()+'`。两者含义不同。\n'
    (OUT/'FINAL_LOCAL_STATUS_R30.zh.md').write_text(text,encoding='utf-8',newline='\n')
    link='experimental/polymer-exploration/20261104/local-acceptance-r30/FINAL_LOCAL_STATUS_R30.zh.md'
    for name in docs:
        original=(archive/name).read_text(encoding='utf-8');first,sep,rest=original.partition('\n')
        target='../'+link if name.startswith('docs/') else link
        if name=='README.md':
            header='\n\n## Current local checkpoint: PBS DMA Tg r30 (2026-11-04)\n\nNative tables: **5,180 identities, 5,236 states, 5,353 properties**. Nine method-qualified DMA Tg properties/states supplement existing formulations (one polymer, eight polymer-based composites). All 5,344 preceding properties and 5,227 states remain unchanged. Polymer coverage is 1,037 identities, 1,077 states and 1,178 properties (1,000 computational and 178 experimental-reference labels). Common triplication is retained separately from unknown scalar n and statistics.\n\nActual isolated installation, frozen in-process consumer and 22 fresh post-acceptance checks (19 database plus 3 method-context cases) passed. No full-history, HTTP or full-platform regression. This batch is local and uncommitted: no current remote CI, push, main merge, stable release or deployment. See [current local evidence]('+target+').\n\nThe sections below preserve previous checkpoints and do not describe the current native snapshot.\n\n'
        else:
            header='\n\n## 当前本地检查点：PBS DMA Tg r30（2026-11-04）\n\n以[当前本地接纳与核验入口]('+target+')为准：全库5180身份、5236状态、5353性质；9个既有配方新增9条DMA tanδ峰Tg及9个物理条形状态（1聚合物、8聚合物基复合配方），无新身份。5344旧性质、5227旧状态完整保持；三次共同重复保留，选定n和统计未知。聚合物1037身份、1077状态、1178性质（1000计算／178实验参考标签），不作方法可比性或科学认证。\n\n实际隔离安装、进程内查询及22项新接纳后检查通过（19数据库＋3方法保真）。不累计旧19／3／180项；完整历史、HTTP及平台全量未运行。本批未提交／推送，无本批远端CI；不合并main、不稳定发布、不部署，继续本地积累后统一交付。\n\n以下保留先前检查点原文，旧计数、快照和CI仅适用于各自冻结范围。\n\n'
        (ROOT/name).write_text(first+header+rest,encoding='utf-8',newline='\n')
    contexts={}
    def add(entry,key,pins):contexts[(str(entry),key)]=(entry,key,pins)
    previous=[AREA/'local-acceptance-r29/CONTEXT_RESOLUTION_R29.json',AREA/'pbs-existing-dma-tg-native-r1/CONTEXT_RESOLUTION_R1.json']
    known_archives=[]
    for file in previous:
        for c in read(file)['contexts']:
            entry=ROOT/c['entry'];key=c.get('field','repo_files_sha256')
            add(entry,key,{n:b['sha256'] for n,b in c['bindings'].items()})
            known_archives.extend(Path(b['resolved_path']) for b in c['bindings'].values())
    for folder,entry_name in [('pbs-existing-dma-tg-source-r1','REVIEW_INPUTS_R1.json'),('pbs-existing-dma-tg-native-r1','REVIEW_INPUTS_R1.json'),('installed-preview-r30','REVIEW_INPUTS_R30.json'),('local-acceptance-r29','REVIEW_INPUTS_R29.json'),('local-acceptance-r29','REVIEW_INPUTS_R29_R2.json')]:
        entry=AREA/folder/entry_name;d=read(entry)
        for key in ['repo_files_sha256','native_files_sha256']:
            if key in d:add(entry,key,d[key])
    add(AREA/'installed-preview-r30/PACKAGE_INPUTS_R30.json','root_mapping',read(AREA/'installed-preview-r30/PACKAGE_INPUTS_R30.json'))
    add(OUT/'DAILY_TEST_RESULTS_R30.json','input_sha256_before_and_after',tests['input_sha256_before_and_after'])
    archived=list(archive.rglob('*'))+known_archives
    for folder in [EXT/'polymer-native-acceptance-20261104-r30/baseline-tables',EXT/'polymer-native-acceptance-20261104-r29/baseline-tables',EXT/'polymer-native-acceptance-20261104-r29/final-freeze-line-ending-correction',AREA/'local-acceptance-r29/pre-r29-documents',AREA/'pbs-existing-dma-tg-source-r1/baseline-contract']:
        archived+=list(folder.rglob('*'))
    archived.append(EXT/'polymer-pbs-dma-tg-20261104-r1/test_method_context_first_attempt.py')
    index={sha(p):p for p in archived if p.is_file()};resolved=[]
    for entry,key,pins in contexts.values():
        bindings={}
        for name,digest in pins.items():
            current=ROOT/name;selected=current if current.is_file() and sha(current)==digest else index[digest]
            assert sha(selected)==digest
            bindings[name]={'sha256':digest,'resolved_path':str(selected),'current':selected==current}
        resolved.append({'entry':entry.relative_to(ROOT).as_posix(),'entry_sha256':sha(entry),'field':key,'bindings':bindings})
    write(OUT/'CONTEXT_RESOLUTION_R30.json',{'contexts':resolved,'binding_count':sum(len(x['bindings']) for x in resolved),'unresolved':0,'historical_manifests_rewritten':False})
    print(json.dumps({'status':'documented_local_acceptance','snapshot':db.snapshot,'contexts':len(resolved)}))

if __name__=='__main__':main()
