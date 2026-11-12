"""Stabilize current-stage documentation before building the actual wheel."""
from pathlib import Path
import hashlib,json,shutil
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    application=json.loads((HERE/'APPLICATION_R65.json').read_bytes())
    assert application['snapshot']=='9713cd8823556102b6d7548025dc03cb528c74c5395e7a15b6ea15969a105bcf'
    assert all(sha(ROOT/n)==h for n,h in application['after_sha256'].items())
    documents=['HANDOFF.md','README.md','docs/DATABASE_COVERAGE.zh.md','docs/MATERIAL_SOURCE_CONDITIONS.zh.md','docs/OPEN_DATABASE_ROADMAP.zh.md']
    backup=ROOT.parent/'open-database-evidence/polymer-native-acceptance-20261112-r65/before-documents';backup.mkdir(exist_ok=False)
    header='''## 当前本地聚合物进展：r65（尚未推送）

九个既有PBS基配方补18条振荡复黏度幅值及9个独立熔体流变上下文，当前5691性质、5398状态、134来源。18性质为2polymer、16composite，不新增身份、牌号、来源或已确认独立试样。旧5673性质与5389状态对象保持，DSC仅身份锚点，不认证共用aliquot/run/batch或制样谱系；R0及牌号歧义继续保留。

原文1Hz／30Hz、kPa.s精度、140°C、0.025%及源25mm直径×2mm尺寸保留。实际间隙、LVR、振幅约定、热稳定、滑移、逐点归约、n和误差未知；Table2的n为流动指数，不是试样数，两个频率不是n2。不拟合求值、不推断稳态剪切、Cox–Merz、零剪切或实虚部，不做角频率/剪切速率换算。

来源、24分支实现及真实映射的批准以对应冻结回执为准。实现356项已含19新项与daily19，仅对应原5673数据，不与写后19相加。写后检查、76输入实际安装及最终独审以[本地核验入口](LINK)追加回执为准，缺失不视为通过。完整历史及本批远端CI未运行；未新增推送、不合并main、不部署。以下历史阶段仅代表各自冻结范围。

'''
    bindings={}
    for name in documents:
        p=ROOT/name;old=p.read_bytes();assert b'\r\n' not in old
        target=backup/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
        first,rest=old.decode('utf-8').split('\n',1)
        link=('../' if name.startswith('docs/') else '')+'experimental/polymer-exploration/20261112/local-acceptance-r65/README.zh.md'
        p.write_text(first+'\n\n'+header.replace('LINK',link)+rest.lstrip('\n'),encoding='utf-8',newline='\n')
        bindings[name]={'before':hashlib.sha256(old).hexdigest(),'after':sha(p)}
    (HERE/'README.zh.md').write_text('# r65：振荡复黏度幅值本地整合\n\n'+header.replace('LINK','README.zh.md')+'\n本说明先于实际打包稳定；后续结果仅追加文件，避免改动README导致包内说明漂移。原资产、备份、安装和导出在仓库外保存。\n',encoding='utf-8')
    with (HERE/'DOCUMENT_BINDINGS_R65.json').open('x',encoding='utf-8') as f:json.dump(bindings,f,indent=2);f.write('\n')
    print('Five main documents and local stage README stabilized before installation.')
if __name__=='__main__':main()
