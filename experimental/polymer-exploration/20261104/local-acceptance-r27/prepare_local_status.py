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
    applied=read(OUT/'APPLICATION_R27.json');equiv=read(OUT/'NATIVE_INSTALLED_EQUIVALENCE_R27.json')
    inventory=read(AREA/'condition-gaps-native-r27/INVENTORY_R3.json')
    assert applied['after_snapshot']==equiv['snapshot']==inventory['snapshot']
    assert applied['counts']['properties']==5333 and applied['counts']['states']==5218
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    archive=OUT/'pre-r27-documents';archive.mkdir()
    shutil.copyfile(ROOT/'HANDOFF.md',archive/'HANDOFF.md')
    write(OUT/'PRE_R27_DOCUMENT_BINDING.json',{'HANDOFF.md':sha(archive/'HANDOFF.md')})
    text='''# r27 PHBV-39负温度Tg本地接纳

既有运行日PHBV-39新增Table4 DSC Tg −5.3°C及1个独立纯化DSC状态，无新身份、牌号或来源。全部5332旧性质、5217旧状态完整保持，Abbasi来源仅追加说明。39不是39%HV；第二次升温和拐点判据有原文支持，精确算法／曲线、湿度、存储、选定单元样本数和数值不确定度未知。

原文将Guho2020结果和重分析数据共同引向Table4／FigureS1，单格运行归属及独立性未解。共同DSC方法的duplicate=2仅保留为附加条件，不升级为选定标量n=2。未查看Guho原文／原始数据或补充图，不声称新的独立2022实验或扩张旧作品许可。未继承机械180°C热压、0.3g、60°C过夜、试条几何或至少5次重复。

r26的172项组合测试仅按其历史冻结输入保留；本批运行时代码、schema和测试文件未变，但数据已变化，未重跑该套件，不将172宣称为本批或当前数据的完整测试结果。新增数据通过三表schema／format、完整5333性质图、来源4→5完整joined导出及四语；真实隔离安装的单来源Tg精确查询1条、全库Tg6条完整对象相等，来源5条完整导出一致。RECORD、64项非版本原生包文件及三表安装等价通过。本地应用实际执行5333项性质检查，0复用。最终独审回执另见本目录。

另有Sahin Table1五个供应商丝材Tg范围完成排除审计：未当打印试样DSC实测、未映射或接纳，原始规格版本／方法和第三方许可未知。首次提取遗漏空方法列的断言失败和七列修正已保留，未当单元测试结果。

本批仅本地接纳，未提交／推送、无本批远端CI；完整历史回归、HTTP、全平台测试未运行。网页只回读选定PMC表格／来源文字，非HTTP产品测试或最新通知审计。未合并main、未稳定发布、未部署；不作标准合规或实验真实性认证。此前远端成功不代表本批CI。
'''
    text+='\nGit HEAD：`'+head+'`；数据库快照：`'+applied['after_snapshot']+'`。两者含义不同。\n'
    text+='\n当前全库：'+str(applied['counts'])+'；聚合物：'+str(applied['polymer_summary'])+'。\n'
    text+='\n实验标签性质'+str(inventory['experimental_class_properties'])+'条，温度字段明确未报告'+str(inventory['condition_status_counts']['temperature'].get('not_reported_in_inspected_source',0))+'条，调湿字段明确未报告'+str(inventory['condition_status_counts']['conditioning'].get('not_reported_in_inspected_source',0))+'条，确切n未确认'+str(inventory['sample_count_exact_unconfirmed'])+'条。按性质对象计数，非独立试验组；非等温扫描范围不等于环境温度，标签数量不作科学认证。\n'
    with (OUT/'FINAL_LOCAL_STATUS_R27.zh.md').open('x',encoding='utf-8',newline='\n') as f:f.write(text)
    title='# Materials Boundaries development handoff\n'
    old=(ROOT/'HANDOFF.md').read_text(encoding='utf-8');assert old.startswith(title)
    header='\n## r27 本地积累（2026-11-04，尚未提交／推送）\n\n既有PHBV-39新增Table4 DSC Tg −5.3°C及1个独立DSC状态，全部5332旧性质／5217旧状态完整保持。第二次升温和拐点判据有来源支持；旧研究／重分析的单格归属未知，共同duplicate不当选定n。当前5333性质／5218状态；新增数据图、真实隔离安装、Tg单来源1条／全库6条与来源5条完整导出核验通过。172组合结果沿用精确未变实现，本批未重跑。五条供应商Tg范围仍排除。当前证据及最终独审见[本地接纳入口](experimental/polymer-exploration/20261104/local-acceptance-r27/FINAL_LOCAL_STATUS_R27.zh.md)。继续本地积累后统一推送，不合并main、不部署；本批远端CI未运行。下文为历史阶段。\n\n'
    (ROOT/'HANDOFF.md').write_text(title+header+old[len(title):],encoding='utf-8',newline='\n')
    write(OUT/'CURRENT_HANDOFF_BINDING_R27.json',{'HANDOFF.md':sha(ROOT/'HANDOFF.md')})
    contexts=[]
    previous=read(AREA/'local-acceptance-r26/CONTEXT_RESOLUTION_R26.json')
    for c in previous['contexts']:
        contexts.append((ROOT/c['entry'],{n:v['sha256'] for n,v in c['bindings'].items()}))
    for entry in [AREA/'local-acceptance-r26/REVIEW_INPUTS_R26.json',AREA/'phbv39-tg-source-audit-r1/REVIEW_INPUTS_R1.json',AREA/'phbv39-tg-native-r1/REVIEW_INPUTS_R1.json',AREA/'installed-preview-r27/REVIEW_INPUTS_R27.json']:
        contexts.append((entry,read(entry)['repo_files_sha256']))
    archived=list((AREA/'epoxy-tg-source-contract-r1/baseline-contract').rglob('*'))+list((EXT/'polymer-native-acceptance-20261104-r26/baseline-tables').glob('*.json'))+list((EXT/'polymer-native-acceptance-20261104-r27/baseline-tables').glob('*.json'))+list((AREA/'local-acceptance-r26/pre-r26-documents').rglob('*'))+list(archive.rglob('*'))
    index={sha(p):p for p in archived if p.is_file()};resolved=[]
    for entry,pins in contexts:
        bindings={}
        for n,digest in pins.items():
            p=ROOT/n
            if not p.is_file() or sha(p)!=digest:p=index[digest]
            assert sha(p)==digest
            bindings[n]=dict(sha256=digest,resolved_path=str(p),current=p==ROOT/n)
        resolved.append(dict(entry=entry.relative_to(ROOT).as_posix(),entry_sha256=sha(entry),bindings=bindings))
    write(OUT/'CONTEXT_RESOLUTION_R27.json',dict(contexts=resolved,binding_count=sum(len(c['bindings']) for c in resolved),unresolved=0,historical_manifests_rewritten=False))
    print(json.dumps(dict(status='documented_local_acceptance',snapshot=applied['after_snapshot'],contexts=len(resolved))))
if __name__=='__main__':main()
