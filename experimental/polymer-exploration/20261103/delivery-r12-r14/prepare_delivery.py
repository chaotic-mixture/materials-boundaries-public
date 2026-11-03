"""Bind the consolidated native delta and archive documents before updating them."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from materials_boundaries.database import Database
OUT = Path(__file__).resolve().parent
BASE = '5635e4c78754637f8cff0dbf4650d5637bb9eace'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write('\n')


def main():
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==BASE
    assert subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()=='experimental/open-database'
    before = Database({n:json.loads(subprocess.check_output(['git','show',BASE+':materials_boundaries/data/'+n+'.json'],cwd=ROOT)) for n in ('materials','reference_properties','sources')})
    after = Database()
    assert len(before.properties)==5252 and len(after.properties)==5267
    assert all(after.properties[k]==v for k,v in before.properties.items())
    assert before.identities==after.identities and before.grades==after.grades
    assert set(before.states)==set(after.states) and set(before.sources)==set(after.sources)
    state_delta = {k:[f for f in v if v[f]!=after.states[k][f]] for k,v in before.states.items() if v!=after.states[k]}
    source_delta = {k:[f for f in v if v[f]!=after.sources[k][f]] for k,v in before.sources.items() if v!=after.sources[k]}
    assert len(state_delta)==13 and all(set(v)=={'version','source_scope','property_ids'} for v in state_delta.values())
    assert len(source_delta)==3 and all(v==['claim_notes'] for v in source_delta.values())
    added = [after.properties[k] for k in after.properties.keys()-before.properties.keys()]
    write(OUT/'NATIVE_DELTA_R12_R14.json',{'parent_commit':BASE,'baseline_snapshot':before.snapshot,'current_snapshot':after.snapshot,'old_complete_properties_unchanged':5252,'new_properties':15,'new_properties_by_quantity':dict(Counter(p['quantity'] for p in added)),'new_property_ids':sorted(p['id'] for p in added),'new_identities':0,'new_grades':0,'new_states':0,'new_sources':0,'state_changes':state_delta,'source_changes':source_delta,'polymer_summary':after.summary(category='polymer')})
    docs = ['README.md','HANDOFF.md','docs/DATABASE_COVERAGE.zh.md','docs/MATERIAL_SOURCE_CONDITIONS.zh.md','docs/OPEN_DATABASE_ROADMAP.zh.md']
    archive = OUT/'pre-delivery-documents'
    binding = {}
    for name in docs:
        target=archive/name
        target.parent.mkdir(parents=True,exist_ok=True)
        assert not target.exists()
        target.write_bytes((ROOT/name).read_bytes())
        binding[name] = {'before_sha256':sha(target),'archive_path':target.relative_to(ROOT).as_posix()}
        prefix = '../' if name.startswith('docs/') else ''
        link=prefix+'experimental/polymer-exploration/20261103/delivery-r12-r14/README.zh.md'
        if name=='README.md':
            content = ('## Current database checkpoint — polymer r12–r14 (2026-11-03)\n\n'
                       'The current native tables contain **5,180 identities, 5,195 states and 5,267 properties**. Polymer coverage is **1,037 identities, 1,052 states and 1,108 properties**: 1,000 computational-reference and108 experimental-reference labels, not independent scientific certification.\n\n'
                       'This checkpoint adds15 properties on existing polymer states:6 tensile stresses at break,2 stresses at specified elongation, and7 PLA/PCL tensile strengths. Unknown conditions and statistics remain explicit; the7 PLA/PCL strength ± amplitudes are not assigned the modulus-specific SD definition.\n\n'
                       '[Evidence, verification scope and experimental delivery]('+link+'). The database snapshot is `'+after.snapshot+'`. Software remains0.35.0. Submission and remote CI require exact-commit receipts; no main merge, stable release or deployment is claimed. Earlier sections retain their checkpoint context.\n\n')
            old=(ROOT/name).read_bytes()
            split=old.find(b'\n')+1
            (ROOT/name).write_bytes(old[:split]+b'\n'+content.encode('utf-8')+old[split:])
        else:
            content = ('## r12–r14聚合物统一实验交付（2026-11-03）\n\n'
                       '当前[交付与核验入口]('+link+')汇总15条既有状态性质补充：6条拉伸断裂应力、2条NR规定伸长率应力、7条PLA/PCL拉伸强度。无新增身份或状态，全部5252个前驱性质完整对象不变；只13个既有状态的版本／链接／范围说明和3个来源声明更新。\n\n'
                       '当前全库5180身份、31牌号、5195状态、5267性质、133来源；聚合物1037身份、1052状态、1108性质，其中1000计算参考和108实验参考为来源分类标签，不认证科学真实性。快照 `'+after.snapshot+'`。\n\n'
                       '来源、映射、隔离安装和各批本地接纳均已独审；强度±定义、样本数、温湿度／调湿和应力约定等未确认项保持未知，不借用邻近试验或标准默认值。当前108条实验参考的74条温度、77条调湿字段未报告，59条确切n缺失，按性质记录计数，不当作独立试验组或完整率。\n\n'
                       '统一交付的当前文件安装、具体暂存／提交及远端CI以精确收据为准；不把旧127项或旧提交CI当作本次新执行。完整历史回归未运行，不合并main、不稳定发布或部署。下文均为各历史检查点，原冻结文字和数量不改写。\n\n')
            old=(ROOT/name).read_bytes()
            split=old.find(b'\n')+1
            (ROOT/name).write_bytes(old[:split]+b'\n'+content.encode('utf-8')+old[split:])
        binding[name]['current_sha256']=sha(ROOT/name)
    write(OUT/'PREDELIVERY_DOCUMENT_BINDING_R12_R14.json',binding)
    print(json.dumps({'snapshot':after.snapshot,'added_properties':len(added),'modified_states':len(state_delta),'modified_sources':len(source_delta),'documents':len(docs)}))


if __name__=='__main__':
    main()
