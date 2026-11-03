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
    applied=read(OUT/'APPLICATION_R26.json');equiv=read(OUT/'NATIVE_INSTALLED_EQUIVALENCE_R26.json')
    inventory=read(AREA/'condition-gaps-native-r26/INVENTORY_R3.json')
    assert applied['after_snapshot']==equiv['snapshot']==inventory['snapshot']
    assert applied['counts']['properties']==5332 and applied['counts']['states']==5217
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    archive=OUT/'pre-r26-documents';archive.mkdir()
    shutil.copyfile(ROOT/'HANDOFF.md',archive/'HANDOFF.md')
    write(OUT/'PRE_R26_DOCUMENT_BINDING.json',{'HANDOFF.md':sha(archive/'HANDOFF.md')})
    text='''# r26 本地接纳与未知项

同5个既有PNA-BPF身份新增5条Table7 DSC玻璃化转变温度：160.0／153.0／174.7／169.3／156.7°C；新增5个独立DSC样品状态，无新增材料身份、牌号或来源。全部5327旧性质及5212旧状态完整保持；唯一来源仅追加说明。摘要174.5与表174.7°C、错误Table8引用和三项既有配方疑点继续保留。判据、扫描次序、热历史、调湿、n和数值不确定度未知。源表转录不裁定真实实验值，不作使用温度或工程允许值。

新增温度规则及旧规则组合172项通过，0失败、0错误、0跳过；8项温度检查已包括在172内，不与先前运行重复累计。69项包输入受完整冻结约束；真实离线隔离安装、5条Tg精确查询、40条同来源完整导出、四语展示、RECORD与64项非版本原生包文件／三表等价均通过。应用阶段5332项性质检查全部执行，0复用。独立审阅决策以精确输入回执为准；最终接纳审阅另见本目录。

本批仅本地接纳，未提交或推送，无本批远端CI。完整历史回归、HTTP及平台全量未运行；未合并main、未稳定发布、未部署。保留既有原PDF，无最新修订／补充信息完整性、原始数据、标准合规或实验真实性认证。此前r23–r25的远端成功不能充作本批CI。
'''
    text+='\nGit HEAD：`'+head+'`；数据库快照：`'+applied['after_snapshot']+'`。两者含义不同。\n'
    text+='\n当前全库：'+str(applied['counts'])+'；聚合物：'+str(applied['polymer_summary'])+'。\n'
    text+='\n实验标签性质'+str(inventory['experimental_class_properties'])+'条，温度字段明确未报告'+str(inventory['condition_status_counts']['temperature'].get('not_reported_in_inspected_source',0))+'条，调湿字段明确未报告'+str(inventory['condition_status_counts']['conditioning'].get('not_reported_in_inspected_source',0))+'条，确切n未确认'+str(inventory['sample_count_exact_unconfirmed'])+'条。按性质对象计数，非独立试验组；非等温扫描范围不等于环境温度，标签数量不作科学认证。\n'
    with (OUT/'FINAL_LOCAL_STATUS_R26.zh.md').open('x',encoding='utf-8',newline='\n') as f:f.write(text)
    title='# Materials Boundaries development handoff\n'
    old=(ROOT/'HANDOFF.md').read_text(encoding='utf-8');assert old.startswith(title)
    header='\n## r26 本地积累（2026-11-04，尚未提交／推送）\n\n新增5条既有PNA-BPF的DSC Tg来源限定记录及5个独立状态，旧记录完整保持。摘要／表格差异、错误表号与未知判据、热历史、调湿、样本数随记录保留。当前5332性质／5217状态；172项本轮组合检查、真实隔离安装及40条来源完整导出通过。本批最终审阅状态及精确证据见[本地接纳入口](experimental/polymer-exploration/20261104/local-acceptance-r26/FINAL_LOCAL_STATUS_R26.zh.md)。继续本地积累后统一推送，不合并main、不部署。本批远端CI未运行；下文为历史交付，不代表本批发布。\n\n'
    (ROOT/'HANDOFF.md').write_text(title+header+old[len(title):],encoding='utf-8',newline='\n')
    write(OUT/'CURRENT_HANDOFF_BINDING_R26.json',{'HANDOFF.md':sha(ROOT/'HANDOFF.md')})
    contexts=[]
    for entry,key in [(AREA/'epoxy-tg-source-contract-r1/REVIEW_INPUTS_R1.json','repo_files_sha256'),(AREA/'epoxy-tg-native-r1/REVIEW_INPUTS_R1.json','repo_files_sha256'),(AREA/'epoxy-tg-native-r1/TEST_RESULTS_R26_R1.json','input_sha256_before_and_after'),(AREA/'installed-preview-r26/REVIEW_INPUTS_R26.json','repo_files_sha256')]:
        contexts.append((entry,read(entry)[key]))
    archived=list((AREA/'epoxy-tg-source-contract-r1/baseline-contract').rglob('*'))+list((EXT/'polymer-native-acceptance-20261104-r26/baseline-tables').glob('*.json'))+list(archive.rglob('*'))
    index={sha(p):p for p in archived if p.is_file()};resolved=[]
    for entry,pins in contexts:
        bindings={}
        for n,digest in pins.items():
            p=ROOT/n
            if not p.is_file() or sha(p)!=digest:p=index[digest]
            assert sha(p)==digest
            bindings[n]=dict(sha256=digest,resolved_path=str(p),current=p==ROOT/n)
        resolved.append(dict(entry=entry.relative_to(ROOT).as_posix(),entry_sha256=sha(entry),bindings=bindings))
    write(OUT/'CONTEXT_RESOLUTION_R26.json',dict(contexts=resolved,binding_count=sum(len(c['bindings']) for c in resolved),unresolved=0,historical_manifests_rewritten=False))
    print(json.dumps(dict(status='documented_local_acceptance',snapshot=applied['after_snapshot'],contexts=len(resolved))))
if __name__=='__main__':main()
