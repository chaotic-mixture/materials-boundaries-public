"""Describe actual native polymer condition gaps without inventing defaults."""
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from materials_boundaries.database import Database


def sample_count_summary(records):
    values = [r['sample_count'] for r in records]
    exact = sum(v['relation']=='exact' and v['value'] is not None for v in values)
    return {'sample_count_value_missing':sum(v['value'] is None for v in values),
            'sample_count_relation_counts':dict(Counter(v['relation'] for v in values)),
            'sample_count_exact_confirmed':exact,
            'sample_count_exact_unconfirmed':len(values)-exact,
            'sample_count_reported_non_exact_value':sum(v['value'] is not None and v['relation']!='exact' for v in values)}


def main():
    dest = Path(sys.argv[1]).resolve()
    assert not dest.exists()
    db = Database()
    keys = ('temperature','test_standard','test_method','direction','conditioning','loading_rate')
    classes, groups, rows = Counter(), defaultdict(list), []
    for prop in db.properties.values():
        state = db.states[prop['material_state_id']]
        identity = db.identities[state['identity_id']]
        if identity['category'] != 'polymer':
            continue
        classes[prop['evidence_kind']] += 1
        if prop['evidence_kind'] != 'published_experimental_reference':
            continue
        row = {'record_id':prop['id'],'quantity':prop['quantity'],'state_id':state['id'],
               'identity_id':identity['id'],'source_id':prop['source_id'],
               'conditions':prop['conditions'],'sample_count':prop['sample_count'],
               'uncertainty_status':prop['uncertainty_status'],'uncertainty_note':prop['uncertainty_note'],
               'method_definition':prop['method_definition'],'scope_note':prop['scope_note'],
               'source_discrepancies':prop['source_discrepancies'],
               'source_document':prop['source_document']}
        rows.append(row)
        groups[prop['source_id']].append(row)
    sources = []
    for sid, records in sorted(groups.items()):
        source = db.sources[sid]
        sources.append({'source_id':sid,'title':source['title'],'doi':source.get('doi'),
                        'properties':len(records),'identities':len({r['identity_id'] for r in records}),
                        'states':len({r['state_id'] for r in records}),
                        'conditions':{k:dict(Counter(r['conditions'][k]['status'] for r in records)) for k in keys},
                        **sample_count_summary(records),
                        'uncertainty_statuses':dict(Counter(r['uncertainty_status'] for r in records)),
                        'record_ids':sorted(r['record_id'] for r in records)})
    result = {'schema':'native-polymer-condition-gap-inventory/3','snapshot':db.snapshot,
              'producer_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'polymer_evidence_class_counts':dict(classes),'experimental_class_properties':len(rows),
              'experimental_class_primary_sources':len(sources),
              'experimental_class_identities':len({r['identity_id'] for r in rows}),
              'experimental_class_states':len({r['state_id'] for r in rows}),
              'condition_status_counts':{k:dict(Counter(r['conditions'][k]['status'] for r in rows)) for k in keys},
              **sample_count_summary(rows),
              'sources':sources,'records':sorted(rows,key=lambda r:r['record_id']),
              'limits':['Descriptive native evidence-class labels;not scientific certification or fresh source verification.',
                        'Computational properties excluded from experimental gap counts.',
                        'Counts are property objects,not independent test groups or unique missing conditions.',
                        'Reported conditioning may describe processing only;read text,notes and additional_conditions.',
                        'A missing numeric n differs from a reported lower bound. Neither establishes exact n; counts are property objects, not independent groups.',
                        'No missing humidity default or completeness score is inferred.',
                        'Primary source count differs from all joined bibliographic source count.'],
              'source_refresh':'not_run','native_data_changed':False,'full_history_regression':'not_run'}
    assert len(rows)==len({r['record_id'] for r in rows})
    assert sum(s['properties'] for s in sources)==len(rows)
    assert Database().snapshot==db.snapshot
    dest.mkdir(parents=True)
    with (dest/'INVENTORY_R3.json').open('x',encoding='utf-8',newline='\n') as f:
        json.dump(result,f,ensure_ascii=False,indent=2)
        f.write('\n')
    text = ['# 当前聚合物条件缺口：原生清单 r3','',
            '仅描述快照 `'+db.snapshot+'`；不刷新原文，不补默认值，不改变数据。',
            '',f'聚合物证据分类：{dict(classes)}。本表仅覆盖{len(rows)}条实验参考标签性质、{len(sources)}个主来源。状态描述不能证明调湿完整或科学有效。','',
            '| 主来源 | 性质数 | 温度明确未报告 | 调湿字段明确未报告 | n数值为空 | 确切n未确认 |',
            '| --- | --- | --- | --- | --- | --- |']
    for s in sorted(sources,key=lambda s:(-s['properties'],s['source_id'])):
        text.append('| `'+s['source_id']+'` | '+str(s['properties'])+' | '+str(s['conditions']['temperature'].get('not_reported_in_inspected_source',0))+' | '+str(s['conditions']['conditioning'].get('not_reported_in_inspected_source',0))+' | '+str(s['sample_count_value_missing'])+' | '+str(s['sample_count_exact_unconfirmed'])+' |')
    text += ['', f"样本数分类：{result['sample_count_exact_confirmed']}条有来源报告的确切n；{result['sample_count_value_missing']}条n数值为空；另{result['sample_count_reported_non_exact_value']}条有下限等非确切数值。确切n未确认共{result['sample_count_exact_unconfirmed']}条。按性质对象计数，非独立试验组；下限不改成恰好该数值。", '', '机器清单逐条保留完整条件证据、附加条件、备注、样本数、方法、来源差异及原文检查范围。一个状态多项性质可能共用同一个缺口；不当作缺失试验组数，也不计算完整率。reported可能仅有加工或固化信息；RH缺失不从字段名推断。缺少确切n不表示没有试样。', '',
             '优先继续核实既有原文可直接支持的方法和条件；没有来源支持的调湿、温湿度、统计和应力约定保持未知。历史待接纳标记不移植到本清单；所有记录以当前原生实际对象为准。']
    (dest/'README.zh.md').write_text('\n'.join(text)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({k:result[k] for k in ('snapshot','experimental_class_properties','experimental_class_primary_sources','sample_count_value_missing','sample_count_exact_confirmed','sample_count_exact_unconfirmed','sample_count_relation_counts','condition_status_counts')}))


if __name__ == '__main__':
    main()
