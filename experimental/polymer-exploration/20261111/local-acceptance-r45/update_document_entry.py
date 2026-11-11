"""Archive previous navigation bytes and describe actual local counts without release claims."""
from pathlib import Path
import hashlib,json,shutil
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
EXT=ROOT.parent/'open-database-evidence/polymer-native-acceptance-20261111-r45'
DOCUMENTS=('README.md','HANDOFF.md','docs/DATABASE_COVERAGE.zh.md','docs/MATERIAL_SOURCE_CONDITIONS.zh.md','docs/OPEN_DATABASE_ROADMAP.zh.md')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    application=json.loads((HERE/'APPLICATION_R45.json').read_bytes());assert application['properties']==5486 and application['states']==5289
    assert all(sha(ROOT/n)==h for n,h in application['after_sha256'].items())
    assert (HERE/'README.zh.md').is_file();bindings={};plans=[]
    for n in DOCUMENTS:
        p=ROOT/n;s=p.read_text(encoding='utf-8');start=s.index('## 当前聚合物进展：r39–r41');end=s.index('\n## ',start+3)
        prefix='../' if n.startswith('docs/') else ''
        block='## 当前本地聚合物进展：r42–r45（尚未推送）\n\n'
        block+='以[当前本地核验入口]('+prefix+'experimental/polymer-exploration/20261111/local-acceptance-r45/README.zh.md)及随后追加的精确独审回执为准。当前全库5486性质、5289状态、134来源；相较已发布r39–r41累计新增70性质、26试验上下文和1方法来源，0新材料身份/牌号，覆盖既有聚合物及聚合物基复合配方。r42–r44已获本地最终独审，r45最终状态以入口回执为准；文件缺失不视为通过。未知统计、条件和输入关系保留，上下文与重叠查询不等于独立试样或新增物理覆盖。\n\n'
        block+='本地改动尚未提交/推送，本批远端CI未运行，旧提交847be1bb03e37e330e8de18341dbfca6715bd8b0的CI只代表旧版本。继续本地积累后统一交付；不合并main、不稳定发布、不部署。以下历史检查点只代表各自冻结范围。\n\n'
        plans.append((n,p,s[:start]+block+s[end:]))
    backup=EXT/'before-documents';backup.mkdir(parents=True,exist_ok=False)
    for n,p,text in plans:
        original=backup/n;original.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,original)
        before=sha(p);assert sha(original)==before
        p.write_text(text,encoding='utf-8',newline='\n')
        bindings[n]=dict(before_sha256=before,archived_exact_bytes=str(original),after_sha256=sha(p))
    with (HERE/'DOCUMENT_BINDINGS_R45.json').open('x',encoding='utf-8',newline='\n') as f:json.dump(bindings,f,ensure_ascii=False,indent=2);f.write('\n')
    print('Five navigation entries updated to actual local counts;exact previous bytes archived;no publication/CI completion claim')
if __name__=='__main__':main()
