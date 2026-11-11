"""Bind accepted native data and archive phase navigation before neutral delivery wording."""
from pathlib import Path
import hashlib,json,shutil,subprocess
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
EXT=ROOT.parent/'open-database-evidence/polymer-consolidated-delivery-20261111-r42-r45'
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(n,obj):
    with (HERE/n).open('x',encoding='utf-8',newline='\n') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()=='847be1bb03e37e330e8de18341dbfca6715bd8b0'
    assert subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()=='experimental/open-database'
    approvals={}
    for r in ('R42','R43','R44','R45'):
        folder=HERE.parent/('local-acceptance-'+r.lower());entry=folder/('REVIEW_FINAL_INPUTS_'+r+'.json');receipt=folder/('INDEPENDENT_FINAL_REVIEW_'+r+'.json')
        a=read(receipt);assert a['decision']=='approved' and a['review_inputs_sha256']==sha(entry)
        approvals[r]=dict(entry_sha256=sha(entry),receipt_sha256=sha(receipt))
    stage=HERE.parent/'local-acceptance-r45';entry=read(stage/'REVIEW_FINAL_INPUTS_R45.json')
    assert all(sha(ROOT/n)==h for n,h in entry['repo_files_sha256'].items())
    application=read(stage/'APPLICATION_R45.json');assert all(sha(ROOT/n)==h for n,h in application['after_sha256'].items())
    paths=list(read(stage/'DOCUMENT_BINDINGS_R45.json'));backup=EXT/'before-neutral-navigation';backup.mkdir(parents=True,exist_ok=False);bindings={}
    for name in paths:
        p=ROOT/name;old=p.read_text(encoding='utf-8');text=old.replace('## 当前本地聚合物进展：r42–r45（尚未推送）','## 当前聚合物进展：r42–r45').replace('local-acceptance-r45/README.zh.md','delivery-r42-r45/README.zh.md').replace('r42–r44已获本地最终独审，r45最终状态以入口回执为准；文件缺失不视为通过。','四轮已获本地最终独审；统一交付、安装和后续Git/CI状态以精确回执为准，缺失不视为通过。').replace('本地改动尚未提交/推送，本批远端CI未运行，旧提交847be1bb03e37e330e8de18341dbfca6715bd8b0的CI只代表旧版本。继续本地积累后统一交付；','提交、推送及本批CI只以统一交付入口的精确回执为准；缺失标为未知，旧提交847be1bb03e37e330e8de18341dbfca6715bd8b0的CI只代表旧版本。')
        assert text!=old and text.count('## 当前聚合物进展：r42–r45')==1
        original=backup/name;original.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,original);before=sha(p);assert sha(original)==before
        p.write_text(text,encoding='utf-8',newline='\n');bindings[name]=dict(before_sha256=before,archived_exact_bytes=str(original),current_sha256=sha(p))
    write('BEFORE_NEUTRAL_NAVIGATION_R1.json',bindings)
    write('APPLICATION_R42_R45.json',dict(snapshot=application['snapshot'],after_sha256=application['after_sha256'],properties=5486,states=5289,sources=134,phase_approvals=approvals,native_data_changed=False,scope='Accepted four-phase data;navigation neutralized for later exact Git/CI receipts;not unified approval or push'))
    print('Four phase approvals verified;native unchanged;five navigation inputs neutralized with exact old-byte archives')
if __name__=='__main__':main()
