"""Freeze local r23 acceptance and resolve earlier pins without rewriting them."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[4]
AREA = ROOT / 'experimental/polymer-exploration/20261103'
OUT = Path(__file__).resolve().parent
EXTERNAL = ROOT.parent / 'open-database-evidence'


def read(path): return json.loads(path.read_bytes())
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def main():
    application = read(OUT / 'APPLICATION_R23.json')
    equality = read(OUT / 'NATIVE_INSTALLED_EQUIVALENCE_R23.json')
    inventory = read(AREA / 'condition-gaps-r3/native-r23/INVENTORY_R3.json')
    assert application['after_snapshot'] == equality['snapshot'] == inventory['snapshot']
    assert application['counts']['properties'] == 5317 and equality['all_5317_properties_and_three_tables_equal']
    assert inventory['experimental_class_properties'] == 158 and inventory['sample_count_exact_unconfirmed'] == 91
    head = subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip()
    branch = subprocess.check_output(['git','branch','--show-current'],cwd=ROOT).decode().strip()
    assert head == 'ba1dc2f0a06d306a92c89a3b32de33573907ace5' and branch == 'experimental/open-database'
    assert not subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT)
    archive = OUT / 'pre-r23-documents'
    archive.mkdir()
    shutil.copyfile(ROOT / 'HANDOFF.md', archive / 'HANDOFF.md')
    status = '''# r23 本地聚合物补充（2026-11-04）

本地原生已应用既有 NBR REF 的一条撕裂强度12.32 kN/m及一个独立角形试样状态，无新身份／牌号／来源。5316旧性质完整不变；旧REF状态仅修订版本、热处理流变背景和来源范围，5205其他旧状态不变，一个来源只追加说明。

流变TC90=381s限于170°C／1.67Hz／1°／20min测量背景；原文称压制基于t90，不足以确认实际381s压机保持或90%化学转化。ISO34 MethodB、5kN载荷传感器量程和500mm/min保留；实际撕裂温湿度、调湿、样本数、缺口／厚度实测及提取算法未知。Figure7有误差条并讨论较高SD，精确REF数值幅度及条定义未知；null不表示零散布。硬度图拟合截距不作为REF实测值，硬度继续暂缓。

tear_strength按force_per_length及kN/m／N/m／N/mm闭合；沿用结构与科学语义校验分工，不新增结构分支，不作压力／原始力／Gc／KIC／Young换算或工程输入。

本地预览前152项定向测试通过，失败／错误／跳过均0，104输入前后稳定；包括6条新测试，不与两次已修正开发试测相加。后续仅去除EOF空行，AST相等并经定向复核，未冒称重跑套件。原生应用5317性质检查全部执行、复用0。真实隔离安装65负载／6元数据及完整来源12对象、四语通过；原生64个非版本负载和全部三表5317性质与安装一致。安装额外50个无hash字节码缓存已与源编译对象比较一致。

当前全库5180身份、31牌号、5207状态、5317性质、133来源；聚合物1037身份、1064状态、1158性质，其中1000计算／158实验参考仅为证据标签，不是科学认证。158实验参考中101条测试温度、106条调湿字段未报告；67条有确切n，87条n为空，4条只有下限，确切n未确认91条。按性质对象计数，不当作独立缺失试验组；reported条件不代表RH或湿度平衡完整。

来源、映射R2及安装／应用方案均已有精确独审批准；最终应用验收以同目录最终冻结入口和对应独审回执为准，回执缺失不作通过。完整历史回归、HTTP、平台全量及本批远端CI未运行。本轮未提交或推送，继续本地积累后统一交付；不合并main、不稳定发布、不部署。Git HEAD仍为ba1dc2f0a06d306a92c89a3b32de33573907ace5，当前快照7109e8ad6a61c1dce5e37352418c6c27fd5370b08345cb48021f9bbf580713a6；Git提交与数据库快照不是同一标识。
'''
    (OUT / 'FINAL_LOCAL_STATUS_R23.zh.md').write_text(status, encoding='utf-8', newline='\n')
    handoff = (ROOT / 'HANDOFF.md').read_text(encoding='utf-8')
    title = '# Materials Boundaries development handoff\n'
    assert handoff.startswith(title)
    header = '''
## r23本地继续积累（2026-11-04，尚未提交／推送）

当前本地以[本地状态及验收入口](experimental/polymer-exploration/20261103/local-acceptance-r23/FINAL_LOCAL_STATUS_R23.zh.md)及对应精确独审回执为准。本轮补既有NBR REF撕裂强度12.32kN/m、独立试样状态和流变t90背景；实际压机保持、精确误差、样本数和环境等未知不补造，硬度继续暂缓。全部5316旧性质保持。

当前全库5317性质／5207状态；聚合物1037身份／1064状态／1158性质，1000计算及158实验参考只是标签。152项预览前定向测试通过；原生5317检查全执行、无复用；隔离安装及三表等价通过。158实验参考中101条测试温度、106条调湿字段未报告，确切n未确认91条。最终验收不从本段推定，读取冻结独审回执。

当前实验分支HEAD仍为ba1dc2f0a06d306a92c89a3b32de33573907ace5，新增内容只在本地；本批远端CI未运行。继续本地积累较大进度后统一推送，不合并main、不稳定发布、不部署。下文为已保留的历史交付，不代表本批已上传。

'''
    (ROOT / 'HANDOFF.md').write_text(title + header + handoff[len(title):], encoding='utf-8', newline='\n')
    contexts = []
    for folder, filename in [('nbr-tear-source-contract-r1','REVIEW_INPUTS_R1.json'),
                             ('nbr-tear-native-r1','REVIEW_INPUTS_R1.json'),
                             ('nbr-tear-native-r1','REVIEW_INPUTS_R2.json'),
                             ('installed-preview-r23','REVIEW_INPUTS_R23.json')]:
        p = AREA / folder / filename
        contexts.append((p, read(p)['repo_files_sha256']))
    p = AREA / 'nbr-tear-native-r1/TEST_RESULTS_R23.json'
    contexts.append((p, read(p)['input_sha256_before_and_after']))
    p = AREA / 'delivery-r19-r22/DELIVERY_MANIFEST_R19_R22.json'
    contexts.append((p, {n:v['sha256'] for n,v in read(p)['files'].items()}))
    archives = [p for p in (AREA / 'nbr-tear-source-contract-r1/baseline-contract').rglob('*') if p.is_file()]
    archives += [p for p in (AREA / 'nbr-tear-native-r1/mapping-r1-context').rglob('*') if p.is_file()]
    archives += list(archive.glob('*'))
    recovery = EXTERNAL / 'polymer-native-acceptance-20261104-r23/baseline-tables'
    archives += list(recovery.glob('*.json'))
    archived = {sha(p):p for p in archives}
    resolved = []
    for entry, values in contexts:
        bindings = {}
        for name,digest in values.items():
            current = ROOT / name
            target = current if current.is_file() and sha(current)==digest else archived[digest]
            assert sha(target)==digest
            bindings[name] = dict(sha256=digest, resolved_path=str(target), current=(target==current))
        resolved.append(dict(entry=entry.relative_to(ROOT).as_posix(), entry_sha256=sha(entry), bindings=bindings))
    write(OUT / 'CONTEXT_RESOLUTION_R23.json', dict(contexts=resolved, binding_count=sum(len(c['bindings']) for c in resolved), unresolved=0,
                                                  note='Exact previous bytes only;historical manifests not rewritten;not historical test replay.'))
    folders = ('nbr-tear-source-contract-r1','nbr-tear-native-r1','installed-preview-r23','local-acceptance-r23','condition-gaps-r3/native-r23')
    files = {p for folder in folders for p in (AREA / folder).rglob('*') if p.is_file()}
    names = ['HANDOFF.md','docs/MATERIAL_REFERENCE_CATALOG.md','materials_boundaries/material_references.py',
             'materials_boundaries/material_presentation.py','materials_boundaries/data/material_locales.json',
             'schemas/reference_properties.schema.json','tests/test_tear_strength_contract.py']
    files |= {ROOT / n for n in names}
    files |= {ROOT / 'materials_boundaries/data' / (n + '.json') for n in ('materials','reference_properties','sources')}
    files.add(AREA / 'condition-gaps-r3/build_inventory.py')
    external = set(recovery.glob('*.json'))
    install = EXTERNAL / 'polymer-installed-preview-20261104-r23'
    im = read(AREA / 'installed-preview-r23/REVIEW_INPUTS_R23.json')
    external |= {install / n for n in im['external_evidence_sha256']}
    external |= {Path(n) for n in read(AREA / 'nbr-tear-source-contract-r1/REVIEW_INPUTS_R1.json')['external_files_sha256']}
    external |= set((EXTERNAL / 'polymer-nbr-tear-native-preview-20261104-r23/native-tables').glob('*.json'))
    result = dict(schema='NBR-tear-local-native-acceptance-review/1', baseline_commit=head, branch=branch,
                  repo_files_sha256={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)},
                  external_files_sha256={str(p):sha(p) for p in sorted(external)}, native_snapshot=application['after_snapshot'],
                  local_native_applied=True, committed=False, pushed=False, merged_main=False, stable_release=False, deployed=False,
                  final_independent_acceptance='pending', remote_CI='not_run_for_unpushed_batch', full_history_regression='not_run')
    target = OUT / 'REVIEW_INPUTS_R23.json'
    write(target, result)
    print(json.dumps(dict(input_sha256=sha(target), repo_files=len(files), external_files=len(external),
                          resolved_contexts=len(resolved), resolved_bindings=sum(len(c['bindings']) for c in resolved))))


if __name__ == '__main__': main()
