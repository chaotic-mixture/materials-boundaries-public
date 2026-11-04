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
    assert not (OUT/'FINAL_LOCAL_STATUS_R29.zh.md').exists()
    db=Database();app=read(OUT/'APPLICATION_R29.json');tests=read(OUT/'DAILY_TEST_RESULTS_R29.json')
    inventory=read(AREA/'condition-gaps-native-r29/INVENTORY_R3.json')
    assert db.snapshot==app['after_snapshot']==tests['snapshot']==inventory['snapshot']
    assert tests['tests_run']==19 and tests['successful'] and tests['failures']==tests['errors']==tests['skipped']==0
    installed=EXT/'polymer-installed-preview-20261104-r29';site=installed/'venv/Lib/site-packages'
    payload={n:h for n,h in read(installed/'BUILD_INPUTS_R29.json')['staged_inputs'].items() if n.startswith('materials_boundaries/')}
    for n,h in payload.items():
        assert sha(site/n)==h,n
        if n!='materials_boundaries/_version.py':assert sha(ROOT/n)==h,n
    assert len(payload)==65
    _,exported=read_snapshot(installed/'installed-export-ewurum_mcdonald_2025_pbs_lignin')
    assert exported=={r['property']['id']:r for r in db.records(source='ewurum_mcdonald_2025_pbs_lignin')}
    write(OUT/'NATIVE_INSTALLED_EQUIVALENCE_R29.json',{'snapshot':db.snapshot,'installed_payload_files_verified':65,'nonversion_native_payload_equal_install':64,'three_native_tables_equal_installed':True,'complete_source_export_objects':len(exported),'baseline_version':'0.35.0','isolated_version':'0.35.0+polymerpreview.20261104.r29','version_difference':'Intentional isolated preview only;not a public release','full_history_regression':'not_run','pushed':False})
    stats=db.summary(category='polymer')
    assert (len(db.identities),len(db.grades),len(db.states),len(db.properties),len(db.sources))==(5180,31,5227,5344,133)
    assert (stats['material_identities'],stats['material_states'],stats['property_records'])==(1037,1076,1177)
    assert stats['properties_by_evidence_kind']=={'published_computational_reference':1000,'published_experimental_reference':177}
    assert (inventory['experimental_class_primary_sources'],inventory['experimental_class_identities'],inventory['experimental_class_states'])==(12,37,76)
    assert (inventory['sample_count_exact_confirmed'],inventory['sample_count_value_missing'],inventory['sample_count_reported_non_exact_value'],inventory['sample_count_exact_unconfirmed'])==(67,106,4,110)
    assert inventory['condition_status_counts']['temperature']['not_reported_in_inspected_source']==111
    assert inventory['condition_status_counts']['conditioning']['not_reported_in_inspected_source']==125
    write(OUT/'CURRENT_POLYMER_SUMMARY_R29.json',stats)
    docs=['README.md','HANDOFF.md','docs/DATABASE_COVERAGE.zh.md','docs/MATERIAL_SOURCE_CONDITIONS.zh.md','docs/OPEN_DATABASE_ROADMAP.zh.md']
    archive=OUT/'pre-r29-documents';archive.mkdir()
    for name in docs:
        target=archive/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
    write(OUT/'PRE_R29_DOCUMENT_BINDING.json',{n:sha(archive/n) for n in docs})
    text='''# r29：既有 PBS 配方 DSC 本地接纳

9个既有配方新增9条Table4 Tm性质、9个独立挤出DSC状态，无新身份、牌号或来源。分类保持1个聚合物与8个聚合物基复合材料，不将所有新增性质计入聚合物大类。R0继续排除。全部5335旧性质、5218旧状态完整不变；唯一来源只追加范围说明。

全库5180身份、31牌号、5227状态、5344性质、133来源。聚合物大类1037身份、1076状态、1177性质（1000计算参考、177实验参考标签），不是科学认证或新增材料计数。聚合物实验来源12个、既有身份37个、状态76个。

原文表格整数精度、正文主峰范围差异、共用第二次升温上下文与逐格阶段未知保持。图4只展示5配方；DSC的n、汇总统计、不确定度、调湿、气氛、盘、校准和软件未知。DMA三次重复、TGA气氛和机械试样几何不转入。聚合物177条实验性质中，111条温度字段、125条调湿字段未报告；67确切n、106个n为空、4个下限，确切n未确认110条。按性质计数，不作独立试验组；扫描程序不等于环境温度。

精确来源、映射、实际安装及静态应用方案均经只读独审。真实隔离安装65载荷／6元数据、71项wheel和76项installed RECORD、50项缓存代码对象及64项非版本原生载荷一致；9新性质及全部旧对象、28条完整来源导出、四语展示通过。冻结辅助查询组件只在进程内核验9状态／9新性质／28导出、副本隔离、stale拒绝及三表不变，不启动或认证HTTP或完整平台。

本地应用后19项数据库行为检查通过，0失败／错误／跳过。当前5344图契约已在隔离预览及实际安装核验，应用通过精确三表字节继承该结论；不再重复全图或完整历史回归。先前180项属于先前快照，不累计或宣称在本批重跑。初次mapping比较信封快照、初次缓存marshal编码比较错误均保留失败版本及修正说明，不改生产验证器、不冒称单位套件失败或认证OS轨迹。

本批本地尚未提交／推送，远端CI未运行；已知上一提交1893455的成功不代表本批CI。未合并main、稳定发布或部署。本地先积累较大进度再统一推送。安装预览METADATA沿用旧基线README，不能作本批公开发布文档。
'''
    text+='\n数据库快照：`'+db.snapshot+'`；Git HEAD：`'+subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()+'`。两者含义不同。\n'
    (OUT/'FINAL_LOCAL_STATUS_R29.zh.md').write_text(text,encoding='utf-8',newline='\n')
    link='experimental/polymer-exploration/20261104/local-acceptance-r29/FINAL_LOCAL_STATUS_R29.zh.md'
    for name in docs:
        original=(archive/name).read_text(encoding='utf-8');first,sep,rest=original.partition('\n')
        target='../'+link if name.startswith('docs/') else link
        if name=='README.md':
            header='\n\n## Current local checkpoint: PBS DSC r29 (2026-11-04)\n\nNative tables: **5,180 identities, 5,227 states, 5,344 properties**. Nine thermal properties/states supplement existing formulations (one polymer, eight polymer-based composites); all 5,335 old properties and 5,218 old states remain unchanged. Polymer coverage is 1,037 identities, 1,076 states and 1,177 properties (1,000 computational and 177 experimental-reference labels). Unknown conditions and source discrepancies remain explicit.\n\nActual isolated installation, frozen in-process consumer and 19 current database checks passed; no full-history, HTTP or full-platform regression. This batch is local and uncommitted: no new remote CI, push, main merge, stable release or deployment. See [current local evidence]('+target+').\n\nThe sections below preserve previous checkpoints and do not describe the current native snapshot.\n\n'
        else:
            header='\n\n## 当前本地检查点：PBS DSC r29（2026-11-04）\n\n以[当前本地接纳与核验入口]('+target+')为准：全库5180身份、5227状态、5344性质；既有9配方补9条熔融温度和9个独立DSC状态（1聚合物、8聚合物基复合配方），无新身份。5335旧性质、5218旧状态完整保持，来源差异和未知项不补造。聚合物1037身份、1076状态、1177性质（1000计算／177实验参考标签），不作科学认证。\n\n实际隔离安装、进程内辅助查询及本批19项数据库行为检查通过。先前180项不计作本批重跑；完整历史、HTTP及平台全量未运行。本批未提交／推送，无本批远端CI；不合并main、不稳定发布、不部署，继续本地积累后统一交付。\n\n以下保留先前检查点原文，旧计数、快照和CI仅适用于各自冻结范围。\n\n'
        (ROOT/name).write_text(first+header+rest,encoding='utf-8',newline='\n')
    contexts=[]
    for folder,entry in [('phbv39-thermal-provenance-followup-r1','REVIEW_INPUTS_R1.json'),('phbv39-prior-version-comparison-r1','REVIEW_INPUTS_R1.json'),('pbs-existing-dsc-source-r1','REVIEW_INPUTS_R1.json'),('pbs-existing-dsc-native-r1','REVIEW_INPUTS_R1.json'),('installed-preview-r29','REVIEW_INPUTS_R29.json'),('delivery-r26-r28','REVIEW_INPUTS_R26_R28.json')]:
        p=AREA/folder/entry;d=read(p)
        for key in ['repo_files_sha256','native_files_sha256']:
            if key in d:contexts.append((p,key,d[key]))
    contexts.append((AREA/'installed-preview-r29/PACKAGE_INPUTS_R29.json','root_mapping',read(AREA/'installed-preview-r29/PACKAGE_INPUTS_R29.json')))
    contexts.append((OUT/'DAILY_TEST_RESULTS_R29.json','input_sha256_before_and_after',tests['input_sha256_before_and_after']))
    archived=list(archive.rglob('*'))+list((EXT/'polymer-native-acceptance-20261104-r29/baseline-tables').glob('*.json'))
    index={sha(p):p for p in archived if p.is_file()};resolved=[]
    for entry,key,pins in contexts:
        bindings={}
        for name,digest in pins.items():
            current=ROOT/name;selected=current if current.is_file() and sha(current)==digest else index[digest]
            assert sha(selected)==digest
            bindings[name]={'sha256':digest,'resolved_path':str(selected),'current':selected==current}
        resolved.append({'entry':entry.relative_to(ROOT).as_posix(),'entry_sha256':sha(entry),'field':key,'bindings':bindings})
    write(OUT/'CONTEXT_RESOLUTION_R29.json',{'contexts':resolved,'binding_count':sum(len(x['bindings']) for x in resolved),'unresolved':0,'historical_manifests_rewritten':False})
    print(json.dumps({'status':'documented_local_acceptance','snapshot':db.snapshot,'contexts':len(resolved)}))

if __name__=='__main__':main()
