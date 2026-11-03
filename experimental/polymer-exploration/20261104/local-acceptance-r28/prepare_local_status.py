"""Document verified local acceptance and resolve changed frozen input paths."""
import hashlib,json,shutil,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
AREA=ROOT/'experimental/polymer-exploration/20261104'
OUT=Path(__file__).resolve().parent
EXT=ROOT.parent/'open-database-evidence'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def write(p,v):
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
    applied=read(OUT/'APPLICATION_R28.json');equiv=read(OUT/'NATIVE_INSTALLED_EQUIVALENCE_R28.json')
    inventory=read(AREA/'condition-gaps-native-r28/INVENTORY_R3.json')
    assert applied['after_snapshot']==equiv['snapshot']==inventory['snapshot']
    assert applied['counts']['properties']==5335 and applied['counts']['states']==5218
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    archive=OUT/'pre-r28-documents';archive.mkdir()
    shutil.copyfile(ROOT/'HANDOFF.md',archive/'HANDOFF.md')
    write(OUT/'PRE_R28_DOCUMENT_BINDING.json',{'HANDOFF.md':sha(archive/'HANDOFF.md')})
    text='''# r28 PHBV-39两个熔融峰本地接纳

同一既有PHBV-39纯化DSC第二次升温状态，新增Table4两个源标签熔融峰Tm1=159.7°C、Tm2=170.1°C。各有独立property ID、source_property_label、thermal_peak_label和对应列证据，不按quantity覆盖；不是温区、平均值、两种材料或两次独立实验。没有新身份、状态、牌号或来源。

全部5333旧性质完整保持，包括既有Tg−5.3°C；其他5217状态完整不变。原DSC状态仅从1.0.0修订到1.0.1，追加两个性质ID和范围说明，全部状态事实／名称保持。Abbasi来源仅追加说明。第二次升温吸热峰判据有源支持，不转用Tg拐点、熔融起始／终止、冷却结晶或TGA失重温度。选定单元n、中心聚合、数值不确定度和Guho／重分析原始运行归属继续未知；共同duplicate只作方法背景，不当选定n。

闭合温度分支支持Tg和melting_peak两量，仍五个完整互斥分支；原无符号数域及非温度量同单位不确定度规则保持。本轮180项组合检查通过，零失败／错误／跳过，包含8项新熔融峰检查，不与先前独立运行重复累计。首次8项检查中虚构夹具缺condition证据标签产生3个错误，失败版本／重放日志保留，修正夹具后整组重跑通过。180项运行的三表输入是接纳前ee1b快照；新增5335性质数据另由图、实际安装和对象等价核验，不宣称整组已在接纳后数据重跑。

三表schema／format、5335性质完整图、同状态双峰2条联合筛选与完整导出、全库Tg6条旧性质、Abbasi来源5→7条完整joined和四语通过。真实离线隔离安装、RECORD、64项非版本原生包文件及三表等价通过；本地应用实际5335项性质检查、0复用。精确独审回执见本目录，不作为科学认证、工程允许值或使用温度。

本批仅本地接纳，未提交／推送，无本批远端CI；完整历史回归、HTTP及全平台测试未运行。未新读Guho原文、SI、原始曲线、校准证书或最新通知；不扩大先前数据作品许可。未合并main、稳定发布或部署。历史远端成功不代表本批CI。
'''
    text+='\nGit HEAD：`'+head+'`；数据库快照：`'+applied['after_snapshot']+'`。两者含义不同。\n'
    text+='\n当前全库：'+str(applied['counts'])+'；聚合物：'+str(applied['polymer_summary'])+'。\n'
    text+='\n实验标签性质'+str(inventory['experimental_class_properties'])+'条，温度字段明确未报告'+str(inventory['condition_status_counts']['temperature'].get('not_reported_in_inspected_source',0))+'条，调湿字段明确未报告'+str(inventory['condition_status_counts']['conditioning'].get('not_reported_in_inspected_source',0))+'条，确切n未确认'+str(inventory['sample_count_exact_unconfirmed'])+'条。按性质对象计数，非独立试验组；非等温扫描范围不等于环境温度，标签数量不作科学认证。\n'
    with (OUT/'FINAL_LOCAL_STATUS_R28.zh.md').open('x',encoding='utf-8',newline='\n') as f:f.write(text)
    title='# Materials Boundaries development handoff\n'
    old=(ROOT/'HANDOFF.md').read_text(encoding='utf-8');assert old.startswith(title)
    header='\n## r28 本地积累（2026-11-04，尚未提交／推送）\n\n同一既有PHBV-39 DSC状态新增Tm1=159.7°C、Tm2=170.1°C两个熔融峰性质，各自标签／ID／列证据保留，不当温区或两个独立实验。旧5333性质及其余5217状态完整保持，原DSC状态仅改版本／追加性质ID／范围。当前5335性质／5218状态；本轮180组合检查、实际安装、双峰2条与来源7条完整导出核验通过；早期虚构夹具3错误及修正记录保留。n、数值分散度、Guho／重分析单格归属仍未知。闭合温度规则仍五分支，不扩大旧量数域。当前证据与最终独审见[本地接纳入口](experimental/polymer-exploration/20261104/local-acceptance-r28/FINAL_LOCAL_STATUS_R28.zh.md)。继续本地积累后统一推送，不合并main、不部署；本批远端CI未运行。下文为历史阶段。\n\n'
    (ROOT/'HANDOFF.md').write_text(title+header+old[len(title):],encoding='utf-8',newline='\n')
    write(OUT/'CURRENT_HANDOFF_BINDING_R28.json',{'HANDOFF.md':sha(ROOT/'HANDOFF.md')})
    contexts=[]
    previous=read(AREA/'local-acceptance-r27/CONTEXT_RESOLUTION_R27.json')
    for c in previous['contexts']:
        contexts.append((ROOT/c['entry'],{n:v['sha256'] for n,v in c['bindings'].items()}))
    for entry,key in [(AREA/'local-acceptance-r27/REVIEW_INPUTS_R27.json','repo_files_sha256'),(AREA/'phbv39-melting-peaks-source-contract-r1/REVIEW_INPUTS_R1.json','repo_files_sha256'),(AREA/'phbv39-melting-peaks-native-r1/TEST_RESULTS_R28_R1.json','input_sha256_before_and_after'),(AREA/'phbv39-melting-peaks-native-r1/REVIEW_INPUTS_R1.json','repo_files_sha256'),(AREA/'installed-preview-r28/REVIEW_INPUTS_R28.json','repo_files_sha256')]:
        contexts.append((entry,read(entry)[key]))
    archived=[]
    for folder in [AREA/'epoxy-tg-source-contract-r1/baseline-contract',AREA/'phbv39-melting-peaks-source-contract-r1/baseline-contract',AREA/'local-acceptance-r26/pre-r26-documents',AREA/'local-acceptance-r27/pre-r27-documents',archive]:
        archived+=list(folder.rglob('*'))
    for batch in ('r26','r27','r28'):
        archived+=list((EXT/('polymer-native-acceptance-20261104-'+batch)/'baseline-tables').glob('*.json'))
    index={sha(p):p for p in archived if p.is_file()};resolved=[]
    for entry,pins in contexts:
        bindings={}
        for n,digest in pins.items():
            p=ROOT/n
            if not p.is_file() or sha(p)!=digest:p=index[digest]
            assert sha(p)==digest
            bindings[n]=dict(sha256=digest,resolved_path=str(p),current=p==ROOT/n)
        resolved.append(dict(entry=entry.relative_to(ROOT).as_posix(),entry_sha256=sha(entry),bindings=bindings))
    write(OUT/'CONTEXT_RESOLUTION_R28.json',dict(contexts=resolved,binding_count=sum(len(c['bindings']) for c in resolved),unresolved=0,historical_manifests_rewritten=False))
    print(json.dumps(dict(status='documented_local_acceptance',snapshot=applied['after_snapshot'],contexts=len(resolved))))
if __name__=='__main__':main()
