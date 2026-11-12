"""Stabilize current-stage documentation before building the actual wheel."""
from pathlib import Path
import hashlib,json,shutil
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    application=json.loads((HERE/'APPLICATION_R64.json').read_bytes())
    assert application['snapshot']=='d2062c34b747e03fc4affc2998e25a7f69e362fef2f98503e0b50433b662b177'
    assert all(sha(ROOT/n)==h for n,h in application['after_sha256'].items())
    documents=['HANDOFF.md','README.md','docs/DATABASE_COVERAGE.zh.md','docs/MATERIAL_SOURCE_CONDITIONS.zh.md','docs/OPEN_DATABASE_ROADMAP.zh.md']
    backup=ROOT.parent/'open-database-evidence/polymer-native-acceptance-20261112-r64/before-documents';backup.mkdir(exist_ok=False)
    header='''## 当前本地聚合物进展：r64（尚未推送）

九个既有PBS配方补9条来源限定DSC熔融比焓，当前5673性质、5389状态、134来源。复用9个挤出DSC上下文，版本1.0.0→1.0.1，仅追加性质链接和范围说明；原state事实及全部旧性质保持，旧Tm完整关联对象会带更新后的上下文，不能说整个joined对象未变。1条polymer、8条composite，不新增身份、牌号、来源、上下文或物理试样计数。

ΔHm为58／49／44／42／29／49／44／39／29J/g，峰面积定义、名义10mg和热程序已知；周期仅共同第二升温图注，质量基准、积分范围、符号约定、校准及n/误差未知。不借DMAtriplicate、TGA气氛、不由Xc或110.3参考反算。原R0身份暂缓保持。原生映射采用同PMCID的既有注册XML地址，PDF所选三页仅佐证，不认证实际积分或热力学标准化。

来源、23分支实现及R3映射的批准以对应冻结回执为准；首次维度守卫失败和映射R1报告角色、R2地址形式失败保留，不放宽规则。实现337项含14新项及daily19，仅对应原5664数据，不与写后19相加。写后检查、75输入实际安装及最终独审以[本地核验入口](LINK)追加回执为准，缺失不视为通过。完整历史及本批远端CI未运行；未新增推送、不合并main、不部署。以下历史阶段仅代表各自冻结范围。

'''
    bindings={}
    for name in documents:
        p=ROOT/name;old=p.read_bytes();assert b'\r\n' not in old
        target=backup/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
        first,rest=old.decode('utf-8').split('\n',1)
        link=('../' if name.startswith('docs/') else '')+'experimental/polymer-exploration/20261112/local-acceptance-r64/README.zh.md'
        p.write_text(first+'\n\n'+header.replace('LINK',link)+rest.lstrip('\n'),encoding='utf-8',newline='\n')
        bindings[name]={'before':hashlib.sha256(old).hexdigest(),'after':sha(p)}
    (HERE/'README.zh.md').write_text('# r64：胞孔几何比值本地整合\n\n'+header.replace('LINK','README.zh.md')+'\n本说明先于实际打包稳定；后续结果仅追加文件，避免改动README导致包内说明漂移。原资产、备份、安装和导出在仓库外保存。\n',encoding='utf-8')
    with (HERE/'DOCUMENT_BINDINGS_R64.json').open('x',encoding='utf-8') as f:json.dump(bindings,f,indent=2);f.write('\n')
    print('Five main documents and local stage README stabilized before installation.')
if __name__=='__main__':main()
