"""Document the cumulative experimental scope without predicting remote CI."""
import hashlib,json,shutil,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
EXT=ROOT.parent/'open-database-evidence/polymer-consolidated-delivery-20261112-r69-r72'


def main():
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()=='fb996df80be67aba2896169935f997ad08655690'
    assert subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()=='experimental/open-database'
    assert not subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=ROOT)
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    body='''## r69–r72 聚合物累计成果（实验分支）

本轮累计新增17条来源限定性质及13个文献方法上下文：10条DSC参考归一化结晶度、3条Indulin AT热重性质、1条FTIR拟合羰基带面积比、3条转载SEC摩尔质量／分散性。9条polymer、8条composite性质，不是17种材料或独立实验。当前5757性质、5433状态、134来源；旧5740性质、5420状态和全部身份／牌号／来源保持。原27封闭分支与旧定义保持，当前31分支。

来源归一化Xc不是直接相含量测量，不计算或反推作者值；PHBV first-cooling与second-heating／焓方法主张张力保留，实际相位不自动选择。TGA的±语义、峰序号／质量基准等未知不补造。FTIR面积比不改成浓度或结晶度。SEC的×10⁵倍率、mean／SD和Guho2020继承保留，不重算PDI或传播SD；原作精度、实际协议、样品原格及独立许可未核实，2022共同条件不迁入原实验。共同duplicate／triplicate不作逐格独立n，温度点／性质数不累计试样。

r69–r72各阶段本地最终独审已批准。最新日常19项检查作用于5757性质，98项执行输入保持；历史完整与定向测试各有冻结代码／数据范围，不累加、不冒称当前430全套。当前说明包的真实隔离安装、累计整合审阅及精确交付范围以[累计核验入口](LINK)为准，不由此段预先认证。357条非计算polymer条件清单保留明确未报与未核实的区别；性质条数不代表材料身份、独立试片或科学评分。

本段描述实验分支的累计冻结成果；是否已推送及远端CI只认对应提交SHA的[实际分支检查](https://github.com/chaotic-mixture/materials-boundaries-public/actions/workflows/database.yml?query=branch%3Aexperimental%2Fopen-database)和后续回执。不得据旧阶段“未推送”字样判断本次远端状态。原始资产、包和归档保留在仓库外；不合并main、不稳定发布、不部署。R0、牌号、Tc峰端点及复黏度候选继续暂缓。以下各阶段内容均为其当时冻结范围。

'''
    backup=EXT/'before-documents';backup.mkdir(exist_ok=False)
    files=[ROOT/p for p in ('README.md','HANDOFF.md','docs/DATABASE_COVERAGE.zh.md','docs/MATERIAL_SOURCE_CONDITIONS.zh.md','docs/OPEN_DATABASE_ROADMAP.zh.md')]
    bindings={}
    for p in files:
        relative=p.relative_to(ROOT);saved=backup/relative;saved.parent.mkdir(parents=True,exist_ok=True)
        raw=p.read_bytes();assert b'\r' not in raw
        shutil.copyfile(p,saved);before=sha(p)
        first,rest=raw.decode('utf-8').split('\n',1)
        link=('../' if relative.parent!=Path('.') else '')+'experimental/polymer-exploration/20261112/delivery-r69-r72/README.zh.md'
        p.write_text(first+'\n\n'+body.replace('LINK',link)+rest.lstrip('\n'),encoding='utf-8',newline='\n')
        bindings[relative.as_posix()]=dict(before_sha256=before,saved_before=str(saved),after_sha256=sha(p))
    with (HERE/'DOCUMENT_BINDINGS_R1.json').open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(bindings,ensure_ascii=False,indent=2)+'\n')
    (HERE/'README.zh.md').write_text('# r69–r72 聚合物累计交付\n\n'+body.replace('LINK','REVIEW_DELIVERY_INPUTS_R1.json')+'\n此目录用于累计核验、独审及精确提交范围；提交前不认证远端CI，提交后的回执单独记录。\n',encoding='utf-8',newline='\n')
    print('Five entry documents backed up and updated;native data and code unchanged',flush=True)


if __name__=='__main__':main()
