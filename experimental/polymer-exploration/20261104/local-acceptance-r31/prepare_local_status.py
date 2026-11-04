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
    assert not (OUT/'FINAL_LOCAL_STATUS_R31.zh.md').exists()
    db=Database();app=read(OUT/'APPLICATION_R31.json');tests=read(OUT/'DAILY_TEST_RESULTS_R31.json')
    inventory=read(AREA/'condition-gaps-native-r31/INVENTORY_R3.json')
    assert db.snapshot==app['after_snapshot']==tests['snapshot']==inventory['snapshot']
    assert tests['tests_run']==22 and tests['successful'] and tests['failures']==tests['errors']==tests['skipped']==0
    installed=EXT/'polymer-installed-preview-20261104-r31';site=installed/'venv/Lib/site-packages'
    payload={n:h for n,h in read(installed/'BUILD_INPUTS_R31.json')['staged_inputs'].items() if n.startswith('materials_boundaries/')}
    for n,h in payload.items():
        assert sha(site/n)==h,n
        if n!='materials_boundaries/_version.py':assert sha(ROOT/n)==h,n
    assert len(payload)==65
    _,exported=read_snapshot(installed/'installed-export-ewurum_mcdonald_2025_pbs_lignin')
    assert exported=={r['property']['id']:r for r in db.records(source='ewurum_mcdonald_2025_pbs_lignin')}
    write(OUT/'NATIVE_INSTALLED_EQUIVALENCE_R31.json',{'snapshot':db.snapshot,'installed_payload_files_verified':65,'nonversion_native_payload_equal_install':64,'three_native_tables_equal_installed':True,'complete_source_export_objects':len(exported),'baseline_version':'0.35.0','isolated_version':'0.35.0+polymerpreview.20261104.r31','version_difference':'Intentional isolated preview only;not a public release','full_history_regression':'not_run','pushed':False})
    stats=db.summary(category='polymer')
    assert (len(db.identities),len(db.grades),len(db.states),len(db.properties),len(db.sources))==(5180,31,5245,5371,133)
    assert (stats['material_identities'],stats['material_states'],stats['property_records'])==(1037,1078,1180)
    assert stats['properties_by_evidence_kind']=={'published_computational_reference':1000,'published_experimental_reference':180}
    assert (inventory['experimental_class_primary_sources'],inventory['experimental_class_identities'],inventory['experimental_class_states'])==(12,37,78)
    assert (inventory['sample_count_exact_confirmed'],inventory['sample_count_value_missing'],inventory['sample_count_reported_non_exact_value'],inventory['sample_count_exact_unconfirmed'])==(69,107,4,111)
    assert inventory['condition_status_counts']['temperature']['not_reported_in_inspected_source']==113
    assert inventory['condition_status_counts']['conditioning']['not_reported_in_inspected_source']==128
    write(OUT/'CURRENT_POLYMER_SUMMARY_R31.json',stats)
    docs=['README.md','HANDOFF.md','docs/DATABASE_COVERAGE.zh.md','docs/MATERIAL_SOURCE_CONDITIONS.zh.md','docs/OPEN_DATABASE_ROADMAP.zh.md']
    archive=OUT/'pre-r31-documents';archive.mkdir()
    for name in docs:
        target=archive/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
    write(OUT/'PRE_R31_DOCUMENT_BINDING.json',{n:sha(archive/n) for n in docs})
    text='# r31：既有 PBS 配方弯曲性质本地接纳\n\n9个既有配方补18条Table7弯曲强度／模量均值与SD，以及9条来源限定试验上下文状态记录。无新身份、牌号或来源，分类保持1个聚合物、8个聚合物基复合材料。物理形态、成形路线及与既有试样的同一性未解决；新增上下文记录不证明独立物理覆盖、独立批次或材料。R0仍排除。\n\n全部5353前驱性质、5236前驱状态完整不变，唯一来源仅追加一项说明。全库5180身份、31牌号、5245状态记录、5371性质、133来源。聚合物1037身份、1078状态记录、1180性质（1000计算、180实验参考标签），12个实验主来源、37个既有实验身份、78个实验状态记录；不得把16个复合材料新增性质计入聚合物大类。\n\n保留原表MPa、均值和SD精度及SD舍入说明，所选配方来源弯曲组n=8，两项性质共享这组，不计16次独立试验。不从SD、Tukey字母或95%显著性语言构造CI／SE／CV、自由度或正态性。标准仅按文中ASTMD790和参考年份2015记录，具体后缀未知，不认证合规或引入标准默认条件。2.5kN是机器容量，不是施加载荷；1.1mm/min为来源加载速率。\n\nproduct_form、尺寸、跨距、材料方向、精确成形路线、温湿度、调湿、强度端点和模量子型／提取窗口未知。仅记共同挤出背景，不填120°C热压、3.1mm厚度、DMA条形几何／15mm跨距或注塑狗骨路线，不将弯曲模量等同Young或DMA储能模量。上下文名称和范围逐条保留关联未解决的限制。\n\n精确来源、具体映射及真实隔离安装／静态应用方案经只读独审。65载荷／6元数据、71项wheel及76项installed RECORD、50缓存代码对象、64项非版本原生载荷和三表等价通过。18新性质、55条完整来源导出及四语通过；15条旧Tg、11条旧熔融峰完整保持。冻结进程内辅助查询核9上下文／18性质／55导出、副本隔离、过期选择拒绝及三表不变，不启动或认证HTTP和完整平台。\n\n本地接纳后新运行22项检查（19数据库＋3方法保真），0失败／错误／跳过；旧180／19／3／22不累计。5371图契约在隔离预览和实际安装核验，应用以同字节三表继承，不重复完整图或历史回归。主文档在本次执行之后更新，旧README测试输入留档，不冒称对随后更新的文档重跑。首轮映射缺summary_statistic主证据标签的失败helper和修正记录保留，未弱化生产validator。\n\n聚合物180条实验性质中113条温度字段、128条调湿字段未报告；69条来源报告确切n、107个n为空、4个下限，确切n未确认111条。均按性质对象计数，共享组不重复推断独立实验数；精确n不证明独立物理试样或批次。\n\n相对Git提交1893455，三轮累计补36性质、27状态记录；原5335性质、5218状态完整不变，身份及牌号不变，Ewurum来源恰好追加3说明。上下文计数不认证物理独立覆盖。尚未提交／推送，无本批远端CI；历史提交成功不代表本批。未合并main、稳定发布或部署，继续本地积累后统一交付。预览METADATA沿用应用前README，不能作本批公开发布文档。\n'
    text+='\n数据库快照：`'+db.snapshot+'`；Git HEAD：`'+subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()+'`。两者含义不同。\n'
    (OUT/'FINAL_LOCAL_STATUS_R31.zh.md').write_text(text,encoding='utf-8',newline='\n')
    link='experimental/polymer-exploration/20261104/local-acceptance-r31/FINAL_LOCAL_STATUS_R31.zh.md'
    for name in docs:
        original=(archive/name).read_text(encoding='utf-8');first,sep,rest=original.partition('\n')
        target='../'+link if name.startswith('docs/') else link
        if name=='README.md':
            header='\n\n## Current local checkpoint: PBS flexural r31 (2026-11-04)\n\nNative tables: **5,180 identities, 5,245 catalogue state records, 5,371 properties**. Nine existing formulations gain 18 source-reported flexural means/SDs and nine source-qualified test contexts. Physical form, forming route and association with existing specimens remain unresolved; these records do not establish additional independent physical coverage. All 5,353 preceding properties and 5,236 state objects remain unchanged. Polymer coverage is 1,037 identities, 1,078 state records and 1,180 properties (1,000 computational and 180 experimental-reference labels).\n\nActual isolated installation, frozen in-process consumer and 22 fresh post-acceptance checks passed. Unknown conditions remain unknown; both properties share the reported eight-repeat group. No current remote CI, commit, push, main merge, stable release or deployment. See [current local evidence]('+target+').\n\nThe sections below preserve previous checkpoints and do not describe the current native snapshot.\n\n'
        else:
            header='\n\n## 当前本地检查点：PBS弯曲性质 r31（2026-11-04）\n\n以[当前本地接纳与核验入口]('+target+')为准：全库5180身份、5245状态记录、5371性质。9个既有配方补18条弯曲均值／SD及9个来源限定试验上下文，物理形态和与既有试样关联未知，不认证新增独立物理覆盖。5353旧性质、5236旧状态完整保持；两项性质共享来源n=8组，其他未报告条件不补造。聚合物1037身份、1078状态记录、1180性质（1000计算／180实验参考标签）。\n\n真实隔离安装、进程内查询及22项新接纳后检查通过；不累计旧运行，完整历史、HTTP及平台全量未运行。本批未提交／推送，无本批远端CI；不合并main、不稳定发布、不部署，继续本地积累后统一交付。\n\n以下保留先前检查点原文，旧计数、快照和CI仅适用于各自冻结范围。\n\n'
        (ROOT/name).write_text(first+header+rest,encoding='utf-8',newline='\n')
    contexts={}
    def add(entry,key,pins):contexts[(str(entry),key)]=(entry,key,pins)
    previous=[AREA/'local-acceptance-r30/CONTEXT_RESOLUTION_R30.json']
    known_archives=[]
    for file in previous:
        for c in read(file)['contexts']:
            entry=ROOT/c['entry'];key=c.get('field','repo_files_sha256')
            add(entry,key,{n:b['sha256'] for n,b in c['bindings'].items()})
            known_archives.extend(Path(b['resolved_path']) for b in c['bindings'].values())
    for folder,entry_name in [('pbs-existing-flexural-source-r1','REVIEW_INPUTS_R1.json'),('pbs-existing-flexural-native-r1','REVIEW_INPUTS_R1.json'),('installed-preview-r31','REVIEW_INPUTS_R31.json'),('local-acceptance-r30','REVIEW_INPUTS_R30.json')]:
        entry=AREA/folder/entry_name;d=read(entry)
        for key in ['repo_files_sha256','native_files_sha256']:
            if key in d:add(entry,key,d[key])
    add(AREA/'installed-preview-r31/PACKAGE_INPUTS_R31.json','root_mapping',read(AREA/'installed-preview-r31/PACKAGE_INPUTS_R31.json'))
    add(OUT/'DAILY_TEST_RESULTS_R31.json','input_sha256_before_and_after',tests['input_sha256_before_and_after'])
    archived=list(archive.rglob('*'))+known_archives
    for folder in [EXT/'polymer-native-acceptance-20261104-r31/baseline-tables',EXT/'polymer-native-acceptance-20261104-r30/baseline-tables',EXT/'polymer-native-acceptance-20261104-r29/baseline-tables',EXT/'polymer-native-acceptance-20261104-r29/final-freeze-line-ending-correction',AREA/'local-acceptance-r30/pre-r30-documents',AREA/'local-acceptance-r29/pre-r29-documents',AREA/'pbs-existing-dma-tg-source-r1/baseline-contract']:
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
    write(OUT/'CONTEXT_RESOLUTION_R31.json',{'contexts':resolved,'binding_count':sum(len(x['bindings']) for x in resolved),'unresolved':0,'historical_manifests_rewritten':False})
    print(json.dumps({'status':'documented_local_acceptance','snapshot':db.snapshot,'contexts':len(resolved)}))

if __name__=='__main__':main()
