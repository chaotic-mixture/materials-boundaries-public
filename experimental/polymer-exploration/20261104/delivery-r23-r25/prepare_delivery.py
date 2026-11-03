"""Bind three accepted rounds to Git baseline and archive/update delivery docs."""
from collections import Counter
from copy import deepcopy
import hashlib,json,subprocess,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT))
from materials_boundaries.database import Database
OUT=Path(__file__).resolve().parent
BASE='ba1dc2f0a06d306a92c89a3b32de33573907ace5'


def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')


def main():
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip()==BASE
    assert subprocess.check_output(['git','branch','--show-current'],cwd=ROOT).decode().strip()=='experimental/open-database'
    before=Database({n:json.loads(subprocess.check_output(['git','show',BASE+':materials_boundaries/data/'+n+'.json'],cwd=ROOT)) for n in ('materials','reference_properties','sources')})
    after=Database();assert len(before.properties)==5316 and len(after.properties)==5327
    assert all(after.properties[k]==v for k,v in before.properties.items())
    assert before.identities==after.identities and before.grades==after.grades
    assert set(before.states)<set(after.states) and set(before.sources)==set(after.sources)
    changed={k:[f for f,v in old.items() if after.states[k][f]!=v] for k,old in before.states.items() if old!=after.states[k]}
    ref='state_perbunan3445f_tamas_benyei2025_ref';assert len(changed)==6
    for sid,fields in changed.items():
        if sid==ref:
            assert set(fields)=={'version','state','source_scope'}
            restored=deepcopy(after.states[sid]['state']);restored['temper_or_heat_treatment']=before.states[sid]['state']['temper_or_heat_treatment']
            assert restored==before.states[sid]['state']
        else:assert set(fields)=={'version','property_ids','source_scope'}
    sources={k:[f for f,v in old.items() if after.sources[k][f]!=v] for k,old in before.sources.items() if old!=after.sources[k]}
    assert set(sources)=={'tamas_benyei_santha_2025_nbr_rcf','tarasov_2022_pna_bpf_epoxy'}
    for sid,fields in sources.items():
        assert fields==['claim_notes'];old=before.sources[sid]['claim_notes'];assert after.sources[sid]['claim_notes'][:len(old)]==old
    newstates=sorted(set(after.states)-set(before.states));assert len(newstates)==6
    added=[after.properties[k] for k in sorted(set(after.properties)-set(before.properties))]
    assert Counter(p['quantity'] for p in added)=={'tear_strength':1,'flexural_elongation_at_break':5,'izod_impact_strength':5}
    assert all(after.identities[after.states[p['material_state_id']]['identity_id']]['category']=='polymer' for p in added)
    chain={};previous=before.snapshot
    for stage,date in [('r23','20261103'),('r24','20261104'),('r25','20261104')]:
        folder=ROOT/'experimental/polymer-exploration'/date/('local-acceptance-'+stage);suffix=stage.upper()
        entry=folder/('REVIEW_INPUTS_'+suffix+'.json');review=read(folder/('INDEPENDENT_ACCEPTANCE_REVIEW_'+suffix+'.json'));app=read(folder/('APPLICATION_'+suffix+'.json'))
        assert review['decision'] in {'approved','clear'} and review['review_inputs_sha256']==sha(entry)
        assert app['before_snapshot']==previous;previous=app['after_snapshot']
        chain[stage]=dict(input_sha256=sha(entry),decision=review['decision'],after_snapshot=previous)
    assert previous==after.snapshot
    delta=dict(baseline_commit=BASE,baseline_snapshot=before.snapshot,current_snapshot=after.snapshot,old_complete_properties_unchanged=5316,
        new_properties=11,new_properties_by_quantity=dict(Counter(p['quantity'] for p in added)),new_property_ids=[p['id'] for p in added],new_state_ids=newstates,
        new_identities=0,new_grades=0,new_states=6,new_sources=0,existing_state_changes=changed,source_changes=sources,
        state_fact_change='Only existing REF temper_or_heat_treatment;5existingbendingstates factsunchanged',local_acceptance_chain=chain,polymer_summary=after.summary(category='polymer'))
    write(OUT/'NATIVE_DELTA_R23_R25.json',delta)
    stateids=sorted(set(newstates)|set(changed));assert len(stateids)==12
    facts=dict(property_records={p['id']:p for p in added},state_records={k:after.states[k] for k in stateids},source_records={k:after.sources[k] for k in sources},
        source_counts={s:len(list(after.records(source=s))) for s in sources},rows=[dict(id=p['id'],quantity=p['quantity'],number=p['reported_value']['number']) for p in added])
    assert sorted(facts['source_counts'].values())==[12,35];write(OUT/'SOURCE_FACTS_R23_R25.json',facts)
    binding={}
    for name in ('README.md','HANDOFF.md','docs/DATABASE_COVERAGE.zh.md','docs/MATERIAL_SOURCE_CONDITIONS.zh.md','docs/OPEN_DATABASE_ROADMAP.zh.md'):
        p=ROOT/name;arc=OUT/'pre-delivery-documents'/name;arc.parent.mkdir(parents=True,exist_ok=True);assert not arc.exists();arc.write_bytes(p.read_bytes())
        link=('../' if name.startswith('docs/') else '')+'experimental/polymer-exploration/20261104/delivery-r23-r25/README.zh.md'
        if name=='README.md':
            header=('## Current database checkpoint: polymer r23-r25 (2026-11-04)\n\n'
                'Current native tables contain **5,180 identities, 5,212 states and 5,327 properties**. Polymer coverage is **1,037 identities, 1,069 states and 1,168 properties**: 1,000 computational-reference and 168 experimental-reference labels, without scientific certification.\n\n'
                'Three accepted local rounds add 11 properties on existing identities: one NBR tear result, five epoxy flexural break elongations and five Izod impact results; six separate specimen states are added. All 5,316 preceding property objects remain unchanged. One REF state adds rheometer t90 context; five bending states only update revisions/links/scope; two existing sources append notes.\n\n'
                'Unknown conditions and source conflicts remain explicit. REF rheometer 381 s does not verify the actual press hold. Izod Table 7 value 4.1 versus abstract/Figure 10 value 4.01 is unresolved; notch status, impact speed and area reduction remain unknown. No source repair, automatic conversion, fracture-parameter inference or engineering input is made.\n\n'
                'Among 168 experimental property objects, 111 test-temperature fields and 116 conditioning fields are unreported; exact n is unconfirmed for 101 (97 null, four lower bounds). These are property counts, not independent test groups.\n\n'
                '[Evidence and experimental delivery]('+link+'). Snapshot `'+after.snapshot+'`; native software remains 0.35.0. Commit, publication and remote CI require exact subsequent receipts. No main merge, stable release or deployment is claimed. Following checkpoints retain historical context.\n\n')
        else:
            header=('## r23-r25聚合物统一实验交付（2026-11-04）\n\n'
                '当前[交付与核验入口]('+link+')汇总3轮既有材料补充：1条NBR撕裂、5条环氧弯曲断裂伸长及5条Izod冲击性质，新增11性质、6试样状态，无新身份／牌号／来源。5316前驱性质完整保持；旧REF只修订版本／流变热处理背景／范围，5旧弯曲状态只修订版本／性质链接／范围，2来源追加说明。\n\n'
                '当前全库5180身份、31牌号、5212状态、5327性质、133来源；聚合物1037身份、1069状态、1168性质，1000计算和168实验参考只是证据标签。流变381s不证明实际压机保持；Izod表4.1与摘要／图4.01未解决，缺口、冲击速度和面积算法未知；弯曲应变／断裂判据未知。原文差异不修，未知不补默认值，不作工程输入或科学认证。\n\n'
                '168实验性质中111条测试温度、116条调湿字段未报告；67条确切n、97条n为空、4条仅下限，确切n未确认101条。按性质对象计数，不作独立试验组；reported不代表湿度平衡完整。硬度及既有NR／PA12／PLA-PCL暂缓项继续保留。\n\n'
                '各批已独审；统一当前测试、安装、目录读取、提交／推送和远端CI以精确收据为准，不累加历史测试或冒用旧提交CI。完整历史回归、HTTP和平台全量未运行。不合并main、不稳定发布、不部署。下文历史原文保留。\n\n')
        raw=p.read_bytes();cut=raw.find(b'\n')+1;p.write_bytes(raw[:cut]+b'\n'+header.encode('utf-8')+raw[cut:])
        binding[name]=dict(before_sha256=sha(arc),archive_path=arc.relative_to(ROOT).as_posix(),current_sha256=sha(p))
    write(OUT/'PREDELIVERY_DOCUMENT_BINDING_R23_R25.json',binding)
    print(json.dumps(dict(snapshot=after.snapshot,new_properties=11,new_states=6,changed_states=6,changed_sources=2,documents=5)))


if __name__=='__main__':main()
