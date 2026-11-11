"""Describe current noncomputed polymer-category condition gaps without changing evidence or inferring completeness."""
from pathlib import Path
from collections import Counter
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(n,v):
    with (HERE/n).open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();assert commit=='5cc2f28c784b3f457bef025d570161fac0e63e49'
    acceptance=HERE.parent/'local-acceptance-r47'
    approval=read(acceptance/'INDEPENDENT_FINAL_REVIEW_R47.json');entry=acceptance/'REVIEW_FINAL_INPUTS_R47.json'
    assert approval['decision']=='approved' and approval['review_inputs_sha256']==sha(entry)
    accepted=read(acceptance/'APPLICATION_R47.json')
    pins={n:sha(ROOT/n) for n in accepted['after_sha256']}
    assert pins==accepted['after_sha256']==read(entry)['native_files_sha256']
    m=read(ROOT/'materials_boundaries/data/materials.json');states={s['id']:s for s in m['records']};identities={i['id']:i for i in m['identities']}
    allprops=read(ROOT/'materials_boundaries/data/reference_properties.json')['records']
    selected=[p for p in allprops if identities[states[p['material_state_id']]['identity_id']]['category']=='polymer' and p['evidence_kind']!='published_computational_reference']
    def exact(p):return p['sample_count']['relation']=='exact' and p['sample_count']['value'] is not None
    def summary(rows):
        return dict(properties=len(rows),evidence_kinds=dict(Counter(p['evidence_kind'] for p in rows)),temperature_statuses=dict(Counter(p['conditions']['temperature']['status'] for p in rows)),conditioning_statuses=dict(Counter(p['conditions']['conditioning']['status'] for p in rows)),temperature_explicitly_not_reported=sum(p['conditions']['temperature']['status']=='not_reported_in_inspected_source' for p in rows),conditioning_explicitly_not_reported=sum(p['conditions']['conditioning']['status']=='not_reported_in_inspected_source' for p in rows),sample_count_relations=dict(Counter(p['sample_count']['relation'] for p in rows)),sample_count_value_missing=sum(p['sample_count']['value'] is None for p in rows),exact_n_reported=sum(exact(p) for p in rows),exact_n_unconfirmed=sum(not exact(p) for p in rows))
    sources={sid:summary([p for p in selected if p['source_id']==sid]) for sid in sorted({p['source_id'] for p in selected})}
    detail=[dict(property_id=p['id'],version=p['version'],identity_id=states[p['material_state_id']]['identity_id'],material_state_id=p['material_state_id'],source_id=p['source_id'],quantity=p['quantity'],evidence_kind=p['evidence_kind'],conditions=p['conditions'],sample_count=p['sample_count'],summary_statistic=p['summary_statistic'],uncertainty_status=p['uncertainty_status'],source_inspection_scope=p.get('source_document',{}).get('inspection_scope'),scope_note=p['scope_note']) for p in sorted(selected,key=lambda p:(p['source_id'],p['id']))]
    assert len(selected)==232 and len(sources)==12 and Counter(p['evidence_kind'] for p in selected)==dict(published_experimental_reference=227,published_measurement_derived_reference=5)
    result=dict(schema='current-polymer-condition-description/1',commit=commit,snapshot=accepted['snapshot'],native_data_uncommitted=True,acceptance_entry_sha256=sha(entry),acceptance_receipt_sha256=sha(acceptance/'INDEPENDENT_FINAL_REVIEW_R47.json'),native_files_sha256=pins,scope='Polymer directory category only,noncomputed property records;not chemical purity,independent experiments,complete conditioning or scientific approval',summary=summary(selected),by_source=sources,records=detail,computed_polymer_properties_excluded=sum(identities[states[p['material_state_id']]['identity_id']]['category']=='polymer' and p['evidence_kind']=='published_computational_reference' for p in allprops),draft_candidates_included=False,native_changed=False,tests='not_run_readonly_inventory')
    write('INVENTORY_R3.json',result)
    text='# 当前聚合物条件缺口：只读清单\n\n'
    text+='对应已本地接纳r47，基准提交'+commit+'（本批未提交/推送）、快照'+accepted['snapshot']+'，原生三表字节与最终本地独审绑定一致。仅描述目录polymer类别的232条非计算性质（227实验来源参考、5来源派生参考），排除1000条计算性质；类别不证明化学纯度，复合材料不改计聚合物。\n\n'
    text+='| 主来源 | 性质 | 温度明确未报 | 调湿明确未报 | n数值为空 | 确切n未确认 |\n| --- | ---: | ---: | ---: | ---: | ---: |\n'
    for sid,s in sorted(sources.items(),key=lambda x:(-x[1]['exact_n_unconfirmed'],-x[1]['properties'],x[0])):text+='| '+sid+' | '+' | '.join(str(s[k]) for k in ('properties','temperature_explicitly_not_reported','conditioning_explicitly_not_reported','sample_count_value_missing','exact_n_unconfirmed'))+' |\n'
    s=result['summary'];text+='\n来源报告确切n共'+str(s['exact_n_reported'])+'条；n数值为空'+str(s['sample_count_value_missing'])+'条；确切n未确认共'+str(s['exact_n_unconfirmed'])+'条。下限等非exact关系不改成恰好该值，也不当零样本。按性质计数，多项性质可能共享方法组，不能累加为独立试样/批次。\n\n'
    text+='机器清单逐条保留完整条件、附加条件、样本数关系及范围说明。reported调湿可能只包含时间/加工背景，不证明RH完整或平衡完成；未单列某字段不等于已核实原文没有该条件，不计算完整率或科学评分。\n\n'
    text+='r47新增4条结晶峰温度已本地接纳，其中1条polymer类别计入本清单，3条composite不计入；机械n5/25°C48h不能借给热分析。该清单不改变来源事实、原生数据或旧冻结清单，不重跑历史测试，不构成测试通过或独审接纳。未提交/推送，不合并main、不发布、不部署。\n'
    with (HERE/'README.zh.md').open('x',encoding='utf-8',newline='\n') as f:f.write(text)
    assert all(sha(ROOT/n)==h for n,h in pins.items())
    print(json.dumps(dict(properties=232,sources=12,summary=s,native_unchanged=True),ensure_ascii=False))
if __name__=='__main__':main()
