"""Bind four accepted local rounds and update main documents after archiving."""
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
AREA = OUT.parent
BASE = '676df1abd3379f6c6d28bffe8c3685edd63d9b10'


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path): return json.loads(path.read_bytes())


def write(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def main():
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip() == BASE
    assert subprocess.check_output(['git', 'branch', '--show-current'], cwd=ROOT, text=True).strip() == 'experimental/open-database'
    before = Database({name: json.loads(subprocess.check_output(['git', 'show', BASE + ':materials_boundaries/data/' + name + '.json'], cwd=ROOT))
                       for name in ('materials', 'reference_properties', 'sources')})
    after = Database()
    assert len(before.properties) == 5298 and len(after.properties) == 5316
    assert all(after.properties[k] == p for k, p in before.properties.items())
    assert before.identities == after.identities and before.grades == after.grades
    assert set(before.states) < set(after.states) and set(before.sources) == set(after.sources)
    changed_states = {k: [f for f in value if value[f] != after.states[k][f]]
                      for k, value in before.states.items() if value != after.states[k]}
    changed_sources = {k: [f for f in value if value[f] != after.sources[k][f]]
                       for k, value in before.sources.items() if value != after.sources[k]}
    assert len(changed_states) == 2 and all(set(fields) == {'version', 'property_ids', 'source_scope'} for fields in changed_states.values())
    assert len(changed_sources) == 3 and all(fields == ['claim_notes'] for fields in changed_sources.values())
    for sid in changed_sources:
        old = before.sources[sid]['claim_notes']
        assert after.sources[sid]['claim_notes'][:len(old)] == old
    new_states = sorted(set(after.states) - set(before.states))
    assert len(new_states) == 11
    added = [after.properties[k] for k in sorted(set(after.properties) - set(before.properties))]
    assert Counter(p['quantity'] for p in added) == {'tensile_elongation_at_break': 2, 'shore_a_hardness': 6,
                                                  'compressive_modulus': 5, 'compressive_strength': 5}
    assert Counter(p['source_id'] for p in added) == {'mtibe_2022_pbs_pbat_lignin_zno': 2,
                                                   'bianchi_2025_nr_nanoclay': 1, 'johnston_2014_bulk_sylgard184': 15}
    assert all(after.identities[after.states[p['material_state_id']]['identity_id']]['category'] == 'polymer' for p in added)
    stages, previous = {}, before.snapshot
    for stage in ('r19', 'r20', 'r21', 'r22'):
        folder = AREA / ('local-acceptance-' + stage)
        suffix = stage.upper()
        entry = folder / ('REVIEW_INPUTS_' + suffix + '.json')
        receipt = read(folder / ('INDEPENDENT_ACCEPTANCE_REVIEW_' + suffix + '.json'))
        application = read(folder / ('APPLICATION_' + suffix + '.json'))
        assert receipt['decision'] in {'approved', 'clear'} and receipt['review_inputs_sha256'] == sha(entry)
        assert application['before_snapshot'] == previous
        previous = application['after_snapshot']
        stages[stage] = {'input_sha256': sha(entry), 'decision': receipt['decision'], 'after_snapshot': previous}
    assert previous == after.snapshot
    write(OUT / 'NATIVE_DELTA_R19_R22.json', {
        'baseline_commit': BASE, 'baseline_snapshot': before.snapshot, 'current_snapshot': after.snapshot,
        'old_complete_properties_unchanged': 5298, 'new_properties': 18,
        'new_properties_by_quantity': dict(Counter(p['quantity'] for p in added)),
        'new_property_ids': [p['id'] for p in added], 'new_state_ids': new_states,
        'new_identities': 0, 'new_grades': 0, 'new_states': 11, 'new_sources': 0,
        'existing_state_changes': changed_states, 'source_changes': changed_sources,
        'local_acceptance_chain': stages, 'polymer_summary': after.summary(category='polymer')})
    documents = ['README.md', 'HANDOFF.md', 'docs/DATABASE_COVERAGE.zh.md',
                 'docs/MATERIAL_SOURCE_CONDITIONS.zh.md', 'docs/OPEN_DATABASE_ROADMAP.zh.md']
    binding = {}
    for name in documents:
        current = ROOT / name
        archive = OUT / 'pre-delivery-documents' / name
        archive.parent.mkdir(parents=True, exist_ok=True)
        assert not archive.exists()
        archive.write_bytes(current.read_bytes())
        binding[name] = {'before_sha256': sha(archive), 'archive_path': archive.relative_to(ROOT).as_posix()}
        link = ('../' if name.startswith('docs/') else '') + 'experimental/polymer-exploration/20261103/delivery-r19-r22/README.zh.md'
        if name == 'README.md':
            text = ('## Current database checkpoint: polymer r19-r22 (2026-11-03)\n\n'
                    'The current native tables contain **5,180 identities, 5,206 states and 5,316 properties**. Polymer coverage is **1,037 identities, 1,063 states and 1,157 properties**: 1,000 computational-reference and 157 experimental-reference labels, without scientific certification.\n\n'
                    'Four accepted local rounds add 18 properties and 11 specimen states on existing identities: two PBS/PBAT break elongations, six NR/Sylgard Shore A hardness results, and five Sylgard compression moduli plus five compressive strengths. All 5,298 preceding property objects are preserved. Two existing states only update revisions/links/scope; three sources append notes.\n\n'
                    'Shore A is a distinct empirical scale; absolute SD/CI amplitudes use scale points while confidence percentages retain their typed role. Source pressure values and 95% CIs are preserved despite explicit unit/range/extraction conflicts. No unit repair, Young-modulus conversion or engineering input is inferred.\n\n'
                    'Unknown conditions and statistics remain explicit: among 157 experimental property objects, 86 lack numeric n and four report only a lower bound; exact n is unconfirmed for 90 objects. These counts are not independent test groups.\n\n'
                    '[Evidence, limitations and experimental delivery](' + link + '). Snapshot `' + after.snapshot + '`; native software remains 0.35.0. Submission and remote CI require exact-commit receipts. No main merge, stable release or deployment is claimed. Following checkpoints retain historical context.\n\n')
        else:
            text = ('## r19-r22聚合物统一实验交付（2026-11-03）\n\n'
                    '当前[交付与核验入口](' + link + ')汇总四轮既有材料补充：2条PBS/PBAT断裂伸长、6条NR/Sylgard邵氏A硬度、5条Sylgard压缩模量和5条极限压缩强度。新增18性质、11试样状态，无新身份／牌号／来源；全部5298个前驱性质完整不变，只2既有状态的版本／链接／范围说明及3来源追加备注。\n\n'
                    '当前全库5180身份、31牌号、5206状态、5316性质、133来源；聚合物1037身份、1063状态、1157性质，1000计算和157实验参考仅为来源标签，不作科学认证。快照`' + after.snapshot + '`。\n\n'
                    '邵氏A是独立经验标尺，绝对SD／CI为标尺点，置信水平typed percent另列。压缩源MPa与95%CI、摘要GPa／40%及正文约55%范围疑点、Ec异常量级／趋势和提取关系未知均保留，不作单位倍率、Young／导数／割线／泊松比修复，不输入计算器。硬度4试样×8测点不能记32独立试样；压缩n不借其他试验数。\n\n'
                    '157实验性质中100条测试温度、105条调湿字段未报告；67条有确切n，86条n为空、4条仅下限，确切n未确认90条。按性质对象计数，不当独立试验组；reported可能只有冷却／加工时间，不代表RH完整或湿度平衡。NR断裂伸长单位疑点、部分PA12／PLA-PCL断裂及其他未确认项继续暂缓。\n\n'
                    '各批来源、实现／映射、安装及本地接纳已独审；统一交付的当前测试、安装、消费者、提交／推送和远端CI仅以精确收据为准，不将历史140／146或旧提交CI冒充新执行。完整历史回归、HTTP和平台全量验收未运行。不合并main、不稳定发布、不部署。下文保留历史原文，当前以本入口为准。\n\n')
        old = current.read_bytes()
        split = old.find(b'\n') + 1
        current.write_bytes(old[:split] + b'\n' + text.encode('utf-8') + old[split:])
        binding[name]['current_sha256'] = sha(current)
    write(OUT / 'PREDELIVERY_DOCUMENT_BINDING_R19_R22.json', binding)
    print(json.dumps({'snapshot': after.snapshot, 'new_properties': 18, 'new_states': 11,
                      'modified_states': 2, 'modified_sources': 3, 'documents': len(documents)}))


if __name__ == '__main__':
    main()
