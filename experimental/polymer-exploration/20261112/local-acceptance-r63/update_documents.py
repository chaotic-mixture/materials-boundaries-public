"""Stabilize current-stage documentation before building the actual wheel."""
from pathlib import Path
import hashlib,json,shutil
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    application=json.loads((HERE/'APPLICATION_R63.json').read_bytes())
    assert application['snapshot']=='f702a8c5b0d6de2592a262b440a76f30d5d4bbe41ec179754cd73fcf8836a40c'
    assert all(sha(ROOT/n)==h for n,h in application['after_sha256'].items())
    documents=['HANDOFF.md','README.md','docs/DATABASE_COVERAGE.zh.md','docs/MATERIAL_SOURCE_CONDITIONS.zh.md','docs/OPEN_DATABASE_ROADMAP.zh.md']
    backup=ROOT.parent/'open-database-evidence/polymer-native-acceptance-20261112-r63/before-documents';backup.mkdir(exist_ok=False)
    header='''## 当前本地聚合物进展：r63（尚未推送）

四个既有PUR配方补4条胞孔几何比值及4个独立显微形貌上下文，当前5664性质、5389状态、134来源。原文方向均值之比1.4／1.3／1.4／1.4保持，不新增身份、牌号或来源，不证明新增独立物理批次。分子平行发泡方向平均胞孔直径、分母垂直方向平均胞孔尺寸；不倒数或乘100，不解释为力学、完整三维各向异性或材料各向同性。

显微镜10x、ImageJ1.54d及作者ASTM D3576引用保留，不推定版次或符合性。计数、温湿、切片位置厚度、统计权重、归约细节及误差未知；作者分布／空间差异假设不当已验证统计。来源、22分支实现及真实映射独审须以对应回执为准。实现323项含11新项及每日19项，不累加；首轮10项旧总数断言失败及修正保留。写后检查、实际安装和最终独审以[本地核验入口](LINK)追加回执为准，缺失不视为通过。完整历史和本批远端CI未运行；未推送、不合并main、不部署。以下历史阶段仅代表各自冻结范围。

'''
    bindings={}
    for name in documents:
        p=ROOT/name;old=p.read_bytes();assert b'\r\n' not in old
        target=backup/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
        first,rest=old.decode('utf-8').split('\n',1)
        link=('../' if name.startswith('docs/') else '')+'experimental/polymer-exploration/20261112/local-acceptance-r63/README.zh.md'
        p.write_text(first+'\n\n'+header.replace('LINK',link)+rest.lstrip('\n'),encoding='utf-8',newline='\n')
        bindings[name]={'before':hashlib.sha256(old).hexdigest(),'after':sha(p)}
    (HERE/'README.zh.md').write_text('# r63：胞孔几何比值本地整合\n\n'+header.replace('LINK','README.zh.md')+'\n本说明先于实际打包稳定；后续结果仅追加文件，避免改动README导致包内说明漂移。原资产、备份、安装和导出在仓库外保存。\n',encoding='utf-8')
    with (HERE/'DOCUMENT_BINDINGS_R63.json').open('x',encoding='utf-8') as f:json.dump(bindings,f,indent=2);f.write('\n')
    print('Five main documents and local stage README stabilized before installation.')
if __name__=='__main__':main()
