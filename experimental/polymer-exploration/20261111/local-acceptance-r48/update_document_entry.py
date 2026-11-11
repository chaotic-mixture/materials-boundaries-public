"""Archive exact published navigation and point to actual local r48 counts and phase receipts."""
from pathlib import Path
import hashlib,json,shutil
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
EXT=ROOT.parent/'open-database-evidence/polymer-native-acceptance-20261111-r48'
DOCUMENTS=('README.md','HANDOFF.md','docs/DATABASE_COVERAGE.zh.md','docs/MATERIAL_SOURCE_CONDITIONS.zh.md','docs/OPEN_DATABASE_ROADMAP.zh.md')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    application=json.loads((HERE/'APPLICATION_R48.json').read_bytes());assert application['properties']==5504 and application['states']==5301
    assert all(sha(ROOT/n)==h for n,h in application['after_sha256'].items())
    mapping=json.loads((HERE.parent/'pbs-pbat-hybrid-mechanical-mapping-r2/REVIEW_INPUTS_R1.json').read_bytes())
    assert not(set(DOCUMENTS)&set(mapping['repo_files_sha256']))
    assert (HERE/'README.zh.md').is_file();plans=[];bindings={}
    for n in DOCUMENTS:
        p=ROOT/n;text=p.read_text(encoding='utf-8');start=text.index('## 当前本地聚合物进展：r47（尚未推送）');end=text.index('\n## ',start+3)
        prefix='../' if n.startswith('docs/') else ''
        block='## 当前本地聚合物进展：r48（尚未推送）\n\n'
        block+='以[当前本地核验入口]('+prefix+'experimental/polymer-exploration/20261111/local-acceptance-r48/README.zh.md)及随后追加的精确回执为准。当前全库5504性质、5301状态、134来源；本轮三个既有PBS/PBAT复合配方补6力学性质，修订3个已有拉伸状态，无新状态；与r46/r47累计18性质及12新增热测试上下文，0新身份/牌号/来源。本轮来源表头yield与正文泛称、167%未核实叙述及±类别未知均保留；共享组n5不重复计数。既有Tcc标签差异及Tmax/冷却次数未知不变，统计/调湿/样本数和单位来源边界按逐条证据保留；上下文和重叠查询不等于独立试样或新增材料。安装及最终独审以精确回执为准，缺失不视为通过。\n\n'
        block+='本轮本地改动尚未提交/推送，本批远端CI未运行；已发布5cc2f28c784b3f457bef025d570161fac0e63e49的CI只代表此前版本，不代表新实现或数据。继续本地积累后统一交付；不合并main、不稳定发布、不部署。以下历史检查点只代表各自冻结范围。\n\n'
        plans.append((n,p,text[:start]+block+text[end:]))
    backup=EXT/'before-documents';backup.mkdir(parents=True,exist_ok=False)
    for n,p,text in plans:
        original=backup/n;original.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,original);before=sha(p);assert sha(original)==before
        p.write_text(text,encoding='utf-8',newline='\n');bindings[n]=dict(before_sha256=before,archived_exact_bytes=str(original),after_sha256=sha(p))
    with (HERE/'DOCUMENT_BINDINGS_R48.json').open('x',encoding='utf-8',newline='\n') as f:json.dump(bindings,f,ensure_ascii=False,indent=2);f.write('\n')
    print('Five navigation entries point to actual local5504/5301 counts;exact old bytes archived;no CI/publication completion claim')
if __name__=='__main__':main()
