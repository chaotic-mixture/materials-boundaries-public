"""Bind consolidated native delta and archive current documents before updating."""
from collections import Counter
import hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT))
from materials_boundaries.database import Database
OUT=Path(__file__).resolve().parent
BASE='1d454f99b3baddef0f4b304c27bdb7dd954ee5fa'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==BASE
    assert subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()=='experimental/open-database'
    before=Database({n:json.loads(subprocess.check_output(['git','show',BASE+':materials_boundaries/data/'+n+'.json'],cwd=ROOT)) for n in ('materials','reference_properties','sources')})
    after=Database();assert len(before.properties)==5267 and len(after.properties)==5298
    assert all(after.properties[k]==p for k,p in before.properties.items())
    assert before.identities==after.identities and before.grades==after.grades and before.states.keys()==after.states.keys() and before.sources.keys()==after.sources.keys()
    state_delta={k:[f for f in v if v[f]!=after.states[k][f]] for k,v in before.states.items() if v!=after.states[k]}
    source_delta={k:[f for f in v if v[f]!=after.sources[k][f]] for k,v in before.sources.items() if v!=after.sources[k]}
    assert len(state_delta)==22 and all(set(x)=={'version','source_scope','property_ids'} for x in state_delta.values())
    assert len(source_delta)==5 and all(x==['claim_notes'] for x in source_delta.values())
    added=[after.properties[k] for k in after.properties.keys()-before.properties.keys()]
    assert Counter(p['quantity'] for p in added)=={'tensile_elongation_at_break':19,'tensile_elongation_at_strength':12}
    write(OUT/'NATIVE_DELTA_R15_R18.json',{'parent_commit':BASE,'baseline_snapshot':before.snapshot,'current_snapshot':after.snapshot,'old_complete_properties_unchanged':5267,'new_properties':31,'new_properties_by_quantity':dict(Counter(p['quantity'] for p in added)),'new_property_ids':sorted(p['id'] for p in added),'new_identities':0,'new_grades':0,'new_states':0,'new_sources':0,'state_changes':state_delta,'source_changes':source_delta,'polymer_summary':after.summary(category='polymer')})
    docs=['README.md','HANDOFF.md','docs/DATABASE_COVERAGE.zh.md','docs/MATERIAL_SOURCE_CONDITIONS.zh.md','docs/OPEN_DATABASE_ROADMAP.zh.md']
    binding={}
    for name in docs:
        target=OUT/'pre-delivery-documents'/name;target.parent.mkdir(parents=True,exist_ok=True);assert not target.exists();target.write_bytes((ROOT/name).read_bytes())
        binding[name]={'before_sha256':sha(target),'archive_path':target.relative_to(ROOT).as_posix()}
        prefix='../' if name.startswith('docs/') else '';link=prefix+'experimental/polymer-exploration/20261103/delivery-r15-r18/README.zh.md'
        if name=='README.md':
            content=('## Current database checkpoint: polymer r15-r18 (2026-11-03)\n\n'
              'The current native tables contain **5,180 identities, 5,195 states and 5,298 properties**. Polymer coverage is **1,037 identities, 1,052 states and 1,139 properties**: 1,000 computational-reference and 139 experimental-reference labels, without independent scientific certification.\n\n'
              'This checkpoint adds 31 source-qualified properties on existing polymer states: 19 elongations at break and 12 elongations at tensile strength. Endpoints remain separate. Original percentage values are retained; absolute SD/plus-minus amplitudes use elongation percentage points, while CV remains relative percent. New application-context code percent_elongation does not introduce a physical unit or rescale values.\n\n'
              'Unknown conditions and statistics remain explicit. Among the 139 experimental property objects, 76 lack a numeric n and four only report a lower bound; exact n is therefore unconfirmed for 80 records. These are property-object counts, not independent test groups. Earlier R2 value-missing counters must not be interpreted as all unknown exact n.\n\n'
              '[Evidence, limitations and experimental delivery]('+link+'). Snapshot `'+after.snapshot+'`; software remains 0.35.0. Actual submission and remote CI require exact-commit receipts. No main merge, stable release or deployment is claimed. All following checkpoints retain historical context.\n\n')
        else:
            content=('## r15-r18聚合物统一实验交付（2026-11-03）\n\n'
              '当前[交付与核验入口]('+link+')汇总31条既有试样性质补充：19条断裂伸长率、12条拉伸强度处伸长率。两类端点分别表达，三条高PCL断裂缺失和两条PA12统计暂缓记录继续保留。全部5267个前驱性质完整对象不变；无新身份、牌号、状态或来源，只22既有状态的版本／链接／范围说明与5来源追加声明。\n\n'
              '当前全库5180身份、31牌号、5195状态、5298性质、133来源；聚合物1037身份、1052状态、1139性质，其中1000计算与139实验参考仅为来源证据标签，不认证科学真实性。快照 `'+after.snapshot+'`。\n\n'
              '原文百分数不缩放；绝对SD／±是伸长百分点，CV是相对百分比，不混为中央单位或相对误差。percent_elongation是应用上下文码，不是新物理单位。来源、映射、各批安装及接纳均已独审；原文未知温湿度、调湿、标距／应变约定／断裂选点、统计及批次仍未知。来源条件相容筛查不作科学认证，腔体小时不当自然寿命。\n\n'
              '当前139条实验性质中，95条温度、104条调湿字段未报告；76条n数值为空，另4条只报告至少5重复，确切n未确认共80条。59条有来源报告的确切n。样本数关系分类按性质记录计数，不当独立试验组；旧R2 sample_count_value_missing 仅为空值计数，不是全部确切n未知。\n\n'
              '统一交付安装、暂存／提交和远端CI均以精确收据为准，不把历史135项测试或旧提交CI冒称新执行。完整历史回归未运行，不合并main、不稳定发布、不部署。下文保留历史阶段原文和数量，当前状态以本入口为准。\n\n')
        old=(ROOT/name).read_bytes();split=old.find(b'\n')+1
        (ROOT/name).write_bytes(old[:split]+b'\n'+content.encode('utf-8')+old[split:]);binding[name]['current_sha256']=sha(ROOT/name)
    write(OUT/'PREDELIVERY_DOCUMENT_BINDING_R15_R18.json',binding)
    print(json.dumps({'snapshot':after.snapshot,'added':31,'modified_states':22,'modified_sources':5,'documents':len(docs)}))
if __name__=='__main__':main()
