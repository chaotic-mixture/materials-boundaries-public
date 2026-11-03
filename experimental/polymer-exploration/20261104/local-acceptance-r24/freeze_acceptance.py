"""Freeze the reviewed local supplement and preserve exact earlier contexts."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT=Path(__file__).resolve().parents[4]
AREA=ROOT/'experimental/polymer-exploration/20261104'
OLD=ROOT/'experimental/polymer-exploration/20261103'
OUT=Path(__file__).resolve().parent
EXTERNAL=ROOT.parent/'open-database-evidence'


def read(path):return json.loads(path.read_bytes())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path,value):
    with path.open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2);stream.write('\n')


def main():
    applied=read(OUT/'APPLICATION_R24.json')
    equal=read(OUT/'NATIVE_INSTALLED_EQUIVALENCE_R24.json')
    gap=read(AREA/'condition-gaps-native-r24/INVENTORY_R3.json')
    assert applied['after_snapshot']==equal['snapshot']==gap['snapshot']
    assert equal['all_5322_properties_and_three_tables_equal'] and gap['experimental_class_properties']==163
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip()
    branch=subprocess.check_output(['git','branch','--show-current'],cwd=ROOT).decode().strip()
    assert head=='ba1dc2f0a06d306a92c89a3b32de33573907ace5' and branch=='experimental/open-database'
    assert not subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT)
    archive=OUT/'pre-r24-documents';archive.mkdir()
    shutil.copyfile(ROOT/'HANDOFF.md',archive/'HANDOFF.md')
    status='''# r24本地接纳：五条既有PNA-BPF弯曲断裂伸长（2026-11-04）

Table8中PNA-BPF-1至5的5.73／6.66／8.23／8.19／9.15%已与Figure9印刷数字核对，按独立flexural_elongation_at_break、percent_elongation记录，不除100、不与拉伸端点混用。复用五个既有3.6mm弯曲状态，无新身份／牌号／状态／来源；5317旧性质完整不变，五状态仅version／property_ids／source_scope更新，状态事实及其他5202状态不变。来源只追加说明。

保留50ST／GOST R56810-2015(ASTM D790-10)／0.85mm/min、80×9.8×3.6mm试条与原文64:3.6mm写法；未认证标准合规、支承点数、实际应变／挠度通道、外纤维／工程／真实应变约定或断裂判据。T/RH、调湿、中心统计、n／批次和数值不确定度未知，不从固化、标准或其他试验补齐。旧配比／摩尔／碱矛盾及正文连续下降与8.19→8.23局部次序的边界保持；不平滑或推统计显著性。保留PDF本轮视觉检查1／5／6／16／18页，未新下载、核验最新通知或取得原始数据。

158项本轮预览前定向测试通过，失败／错误／跳过均0，105输入前后稳定，其中6项新测试；不与历史152相加。三表schema／format及5322性质当前完整图通过。实际隔离安装65负载／6元数据、四语及30条来源完整joined导出通过；原生64非版本负载、全部三表5322性质与安装相等。应用5322性质检查全执行、复用0；恢复三表已保留。来源概念、映射和安装／应用方案均已精确独审批准，最终接纳以本目录对应冻结入口和独审回执为准，回执缺失不作通过。

当前全库5180身份、31牌号、5207状态、5322性质、133来源；聚合物1037身份、1064状态、1163性质，其中1000计算／163实验参考仅为证据标签。163条实验参考中106条测试温度、111条调湿字段未报告；67条确切n、92条n为空、4条只有下限，确切n未确认96条。按性质对象计数，不当独立试验组，不把reported条件当RH或湿度平衡完整。

相对已上传r22，当前仅在本地累计r23/r24六条新性质、一个撕裂试样状态及流变条件补充；并非新增六种材料。继续本地积累后统一交付，本批未提交／推送或触发远端CI，不合并main、不稳定发布、不部署。完整历史回归、HTTP和平台全量未运行；不认证科学正确性，不作为工程许用值／通用边界或计算器输入。
'''
    status+='\n当前Git HEAD为`'+head+'`，数据库快照为`'+applied['after_snapshot']+'`，两者含义不同。\n'
    (OUT/'FINAL_LOCAL_STATUS_R24.zh.md').write_text(status,encoding='utf-8',newline='\n')
    title='# Materials Boundaries development handoff\n'
    original=(ROOT/'HANDOFF.md').read_text(encoding='utf-8');assert original.startswith(title)
    section='''
## r24本地继续积累（2026-11-04，尚未提交／推送）

当前以[本地状态与精确验收入口](experimental/polymer-exploration/20261104/local-acceptance-r24/FINAL_LOCAL_STATUS_R24.zh.md)及对应独审回执为准。补充5条既有PNA-BPF弯曲断裂伸长，复用弯曲状态，5317旧性质完整保持；未知应变／断裂判据、统计和环境条件保留。158项预览前定向测试、真实隔离安装、30条来源完整导出及原生三表等价通过；最终接纳读取精确独审回执。

当前5322性质／5207状态；聚合物1037身份／1064状态／1163性质，1000计算和163实验标签不作科学认证。106条测试温度、111条调湿字段未报告，96条确切n未确认；按性质计数，不当独立试验组。当前未上传内容累计r23/r24六条性质，不是六种新材料。继续本地积累后统一推送，不合并main、不稳定发布、不部署；本批远端CI、历史回归和HTTP未运行。下文保留历史阶段，不能当本批发布证明。

'''
    (ROOT/'HANDOFF.md').write_text(title+section+original[len(title):],encoding='utf-8',newline='\n')
    contexts=[]
    previous=read(OLD/'local-acceptance-r23/CONTEXT_RESOLUTION_R23.json')
    for c in previous['contexts']:
        contexts.append((ROOT/c['entry'],{n:v['sha256'] for n,v in c['bindings'].items()}))
    p=OLD/'local-acceptance-r23/REVIEW_INPUTS_R23.json';contexts.append((p,read(p)['repo_files_sha256']))
    for folder,name in [('epoxy-flexural-elongation-source-r1','REVIEW_INPUTS_R1.json'),
                        ('epoxy-flexural-elongation-native-r1','REVIEW_INPUTS_R1.json'),
                        ('installed-preview-r24','REVIEW_INPUTS_R24.json')]:
        p=AREA/folder/name;contexts.append((p,read(p)['repo_files_sha256']))
    p=AREA/'epoxy-flexural-elongation-native-r1/TEST_RESULTS_R24.json'
    contexts.append((p,read(p)['input_sha256_before_and_after']))
    archived=[]
    for folder in (OLD/'nbr-tear-source-contract-r1/baseline-contract',OLD/'nbr-tear-native-r1/mapping-r1-context',
                   OLD/'local-acceptance-r23/pre-r23-documents',AREA/'epoxy-flexural-elongation-source-r1/baseline-contract',archive):
        archived += [p for p in folder.rglob('*') if p.is_file()]
    recovery_folders=[EXTERNAL/'polymer-native-acceptance-20261104-r23/baseline-tables',EXTERNAL/'polymer-native-acceptance-20261104-r24/baseline-tables']
    for folder in recovery_folders:archived+=list(folder.glob('*.json'))
    index={sha(p):p for p in archived};resolved=[]
    for entry,pins in contexts:
        bindings={}
        for name,digest in pins.items():
            path=ROOT/name
            if not path.is_file() or sha(path)!=digest:path=index[digest]
            assert sha(path)==digest
            bindings[name]=dict(sha256=digest,resolved_path=str(path),current=(path==ROOT/name))
        resolved.append(dict(entry=entry.relative_to(ROOT).as_posix(),entry_sha256=sha(entry),bindings=bindings))
    write(OUT/'CONTEXT_RESOLUTION_R24.json',dict(contexts=resolved,binding_count=sum(len(c['bindings']) for c in resolved),unresolved=0,
        note='Exact historical bytes preserved,not old manifests rewritten or historical tests replayed.'))
    files={ROOT/n for n in read(OLD/'local-acceptance-r23/REVIEW_INPUTS_R23.json')['repo_files_sha256']}
    files|={OLD/'local-acceptance-r23'/n for n in ('REVIEW_INPUTS_R23.json','INDEPENDENT_ACCEPTANCE_REVIEW_R23.json')}
    for folder in ('epoxy-flexural-elongation-source-r1','epoxy-flexural-elongation-native-r1','installed-preview-r24','local-acceptance-r24','condition-gaps-native-r24'):
        files|={p for p in (AREA/folder).rglob('*') if p.is_file()}
    files.add(ROOT/'tests/test_flexural_elongation_contract.py')
    oldexternal={Path(n) for n in read(OLD/'local-acceptance-r23/REVIEW_INPUTS_R23.json')['external_files_sha256']}
    im=read(AREA/'installed-preview-r24/REVIEW_INPUTS_R24.json');install=Path(im['external_install_directory_hint'])
    external=oldexternal|{install/n for n in im['external_evidence_sha256']}
    external|={Path(n) for n in read(AREA/'epoxy-flexural-elongation-source-r1/REVIEW_INPUTS_R1.json')['external_files_sha256']}
    external|=set((EXTERNAL/'polymer-native-acceptance-20261104-r24/baseline-tables').glob('*.json'))
    external|=set((EXTERNAL/'polymer-epoxy-flexural-elongation-native-20261104-r24/native-tables').glob('*.json'))
    target=OUT/'REVIEW_INPUTS_R24.json'
    write(target,dict(schema='epoxy-flexural-elongation-local-acceptance-review/1',baseline_commit=head,branch=branch,
        repo_files_sha256={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)},external_files_sha256={str(p):sha(p) for p in sorted(external)},
        native_snapshot=applied['after_snapshot'],local_native_applied=True,committed=False,pushed=False,merged_main=False,stable_release=False,deployed=False,
        final_independent_acceptance='pending',remote_CI='not_run_for_unpushed_batch',full_history_regression='not_run'))
    print(json.dumps(dict(input_sha256=sha(target),repo_files=len(files),external_files=len(external),
                         resolved_contexts=len(resolved),resolved_bindings=sum(len(c['bindings']) for c in resolved))))


if __name__=='__main__':main()
