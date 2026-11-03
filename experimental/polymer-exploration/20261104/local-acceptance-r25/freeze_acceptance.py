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
    applied=read(OUT/'APPLICATION_R25.json')
    equal=read(OUT/'NATIVE_INSTALLED_EQUIVALENCE_R25.json')
    gap=read(AREA/'condition-gaps-native-r25/INVENTORY_R3.json')
    assert applied['after_snapshot']==equal['snapshot']==gap['snapshot']
    assert equal['all_5327_properties_and_three_tables_equal'] and gap['experimental_class_properties']==168
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip()
    branch=subprocess.check_output(['git','branch','--show-current'],cwd=ROOT).decode().strip()
    assert head=='ba1dc2f0a06d306a92c89a3b32de33573907ace5' and branch=='experimental/open-database'
    assert not subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT)
    archive=OUT/'pre-r25-documents';archive.mkdir()
    shutil.copyfile(ROOT/'HANDOFF.md',archive/'HANDOFF.md')
    status="""# r25本地接纳：五条既有PNA-BPF Izod冲击性质（2026-11-04）

按Table7原文记录PNA-BPF-1至5的2.2／2.9／2.6／3.7／4.1kJ/m²，独立izod_impact_strength、energy_per_area，保持原文单位，不自动换算。PNA5 Table7=4.1与摘要／Figure10=4.01不一致，原因未解决，随每条记录保留；不以表格压过其他写法，不平均、修笔误、补图中精度或将差异当不确定度／区间／第二次独立试验。

在五个既有身份下新增五个独立Izod试样状态；5322旧性质及5207旧状态完整不变，无新身份／牌号／来源，来源只追加说明。只复用来源支持的配方、共同DDS制备和180°C／8h固化。名义80×9.8×3.6mm试条不证明缺口模式、实际尺寸或弯曲铣切路线；缺口／韧带、冲击速度／摆锤容量、面积归一化、破坏模式、方向、T/RH、调湿、n及统计保持未知，不从标准、弯曲或DSC补齐。三项旧配比／摩尔／碱矛盾继续保留。机名中的Charpy不作Charpy方法证据；不转Gc／J积分／KIC、原始能量、力／压力或撕裂强度，不进入计算器或作许用值／通用边界。

本轮第一次164项因新增测试夹具漏初始化可选字段，出现5错误、0失败；旧测试字节／日志／收据已保留。修正后6新测试单独通过，整组164项重新执行通过，无失败／错误／跳过、106输入稳定，计数不相加。旧tear测试只更新新登记能量面密度单位的共享schema结构预期，J/m²和kJ/m²运行时拒绝保留并测试。三表schema／format、5327性质当前完整图、35条来源完整joined及四语通过；实际隔离安装65负载／6元数据、原生64非版本负载与全部三表5327性质相等。应用5327检查全执行，复用0，恢复副本已保留。来源、具体映射及安装／应用方案已独审，最终接纳仍读取本目录冻结入口及对应最终回执，缺失不作通过。

当前全库5180身份、31牌号、5212状态、5327性质、133来源；聚合物1037身份、1069状态、1168性质，其中1000计算／168实验参考仅为证据标签。168实验参考中111条测试温度、116条调湿字段未报告；67条确切n、97条n为空、4条只有下限，确切n未确认101条。按性质对象计数，不当独立缺失试验组；reported条件不意味着湿度或平衡完整。

相对已上传r22，本地累计r23-r25十一条新性质、六个试样状态及流变条件补充，不是十一种新材料。继续积累并准备统一交付核验；本批尚未提交／推送或触发远端CI，不合并main、不稳定发布、不部署。完整历史回归、HTTP及平台全量未运行。使用保留PDF，无新下载、作者联系、原始数据或最新通知／补充资料完整性认证；标准合规和实验真实性未认证。
"""
    status+='\n当前Git HEAD为`'+head+'`，数据库快照为`'+applied['after_snapshot']+'`，两者含义不同。\n'
    (OUT/'FINAL_LOCAL_STATUS_R25.zh.md').write_text(status,encoding='utf-8',newline='\n')
    title='# Materials Boundaries development handoff\n'
    original=(ROOT/'HANDOFF.md').read_text(encoding='utf-8');assert original.startswith(title)
    section="""
## r25本地继续积累（2026-11-04，尚未提交／推送）

当前以[本地状态与精确验收入口](experimental/polymer-exploration/20261104/local-acceptance-r25/FINAL_LOCAL_STATUS_R25.zh.md)及对应独审回执为准。新增5条既有PNA-BPF的Table7 Izod来源限定性质和5个独立试样状态，5322旧性质／5207旧状态完整保持。4.1／4.01表图摘要差异及缺口、速度、面积归一化、破坏模式、统计和环境未知随记录保留，不修值或宣称实验值已确认。

修正新增测试夹具后，本轮整组164项重新执行通过；实际隔离安装、35条来源完整导出及原生三表等价通过，最终接纳读取精确独审回执。当前5327性质／5212状态；聚合物1037身份／1069状态／1168性质，1000计算及168实验标签不作科学认证。111条测试温度、116条调湿字段未报告，101条确切n未确认；按性质计数，不当独立试验组。

当前仅在本地累计r23-r25十一条性质，继续积累并准备统一交付核验，尚未提交／推送或跑本批远端CI。不合并main、不稳定发布、不部署；完整历史回归、HTTP和平台全量未运行。下文为历史阶段，不能作本批发布证明。

"""
    (ROOT/'HANDOFF.md').write_text(title+section+original[len(title):],encoding='utf-8',newline='\n')
    contexts=[]
    previous=read(AREA/'local-acceptance-r24/CONTEXT_RESOLUTION_R24.json')
    for c in previous['contexts']:
        contexts.append((ROOT/c['entry'],{n:v['sha256'] for n,v in c['bindings'].items()}))
    p=AREA/'local-acceptance-r24/REVIEW_INPUTS_R24.json';contexts.append((p,read(p)['repo_files_sha256']))
    for folder,name in [('epoxy-izod-source-contract-r1','REVIEW_INPUTS_R1.json'),('epoxy-izod-native-r1','REVIEW_INPUTS_R1.json'),('installed-preview-r25','REVIEW_INPUTS_R25.json')]:
        p=AREA/folder/name;contexts.append((p,read(p)['repo_files_sha256']))
    for name in ('TEST_RESULTS_R25.json','TEST_RESULTS_R25_R2.json'):
        p=AREA/'epoxy-izod-native-r1'/name;contexts.append((p,read(p)['input_sha256_before_and_after']))
    archived=[]
    for folder in (OLD/'nbr-tear-source-contract-r1/baseline-contract',OLD/'nbr-tear-native-r1/mapping-r1-context',
                   OLD/'local-acceptance-r23/pre-r23-documents',AREA/'epoxy-flexural-elongation-source-r1/baseline-contract',AREA/'local-acceptance-r24/pre-r24-documents',AREA/'epoxy-izod-source-contract-r1/baseline-contract',AREA/'epoxy-izod-native-r1/test-development-r1',archive):
        archived += [p for p in folder.rglob('*') if p.is_file()]
    recovery_folders=[EXTERNAL/'polymer-native-acceptance-20261104-r23/baseline-tables',EXTERNAL/'polymer-native-acceptance-20261104-r24/baseline-tables',EXTERNAL/'polymer-native-acceptance-20261104-r25/baseline-tables']
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
    write(OUT/'CONTEXT_RESOLUTION_R25.json',dict(contexts=resolved,binding_count=sum(len(c['bindings']) for c in resolved),unresolved=0,
        note='Exact historical bytes preserved,not old manifests rewritten or historical tests replayed.'))
    files={ROOT/n for n in read(AREA/'local-acceptance-r24/REVIEW_INPUTS_R24.json')['repo_files_sha256']}
    files|={AREA/'local-acceptance-r24'/n for n in ('REVIEW_INPUTS_R24.json','INDEPENDENT_ACCEPTANCE_REVIEW_R24.json')}
    for folder in ('epoxy-izod-source-contract-r1','epoxy-izod-native-r1','installed-preview-r25','local-acceptance-r25','condition-gaps-native-r25'):
        files|={p for p in (AREA/folder).rglob('*') if p.is_file()}
    files.add(ROOT/'tests/test_izod_impact_contract.py')
    oldexternal={Path(n) for n in read(AREA/'local-acceptance-r24/REVIEW_INPUTS_R24.json')['external_files_sha256']}
    im=read(AREA/'installed-preview-r25/REVIEW_INPUTS_R25.json');install=Path(im['external_install_directory_hint'])
    external=oldexternal|{install/n for n in im['external_evidence_sha256']}
    external|={Path(n) for n in read(AREA/'epoxy-izod-source-contract-r1/REVIEW_INPUTS_R1.json')['external_files_sha256']}
    external|=set((EXTERNAL/'polymer-native-acceptance-20261104-r25/baseline-tables').glob('*.json'))
    external|=set((EXTERNAL/'polymer-epoxy-izod-native-20261104-r25/native-tables').glob('*.json'))
    target=OUT/'REVIEW_INPUTS_R25.json'
    write(target,dict(schema='epoxy-Izod-local-acceptance-review/1',baseline_commit=head,branch=branch,
        repo_files_sha256={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)},external_files_sha256={str(p):sha(p) for p in sorted(external)},
        native_snapshot=applied['after_snapshot'],local_native_applied=True,committed=False,pushed=False,merged_main=False,stable_release=False,deployed=False,
        final_independent_acceptance='pending',remote_CI='not_run_for_unpushed_batch',full_history_regression='not_run'))
    print(json.dumps(dict(input_sha256=sha(target),repo_files=len(files),external_files=len(external),
                         resolved_contexts=len(resolved),resolved_bindings=sum(len(c['bindings']) for c in resolved))))


if __name__=='__main__':main()
