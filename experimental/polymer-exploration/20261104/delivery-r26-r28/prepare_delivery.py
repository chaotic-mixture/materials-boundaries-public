"""Bind three accepted thermal-property rounds and archive/update delivery docs."""
from collections import Counter
import hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT))
from materials_boundaries.database import Database
OUT=Path(__file__).resolve().parent
BASE='4d4f8fa84451ab0481ec6c2cfbe3495209dad4b8'
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip()==BASE
    assert subprocess.check_output(['git','branch','--show-current'],cwd=ROOT).decode().strip()=='experimental/open-database'
    before=Database({n:json.loads(subprocess.check_output(['git','show',BASE+':materials_boundaries/data/'+n+'.json'],cwd=ROOT)) for n in ('materials','reference_properties','sources')})
    after=Database();assert len(before.properties)==5327 and len(after.properties)==5335
    assert all(after.properties[k]==v for k,v in before.properties.items())
    assert all(after.states[k]==v for k,v in before.states.items())
    assert before.identities==after.identities and before.grades==after.grades and set(before.sources)==set(after.sources)
    newstates=sorted(set(after.states)-set(before.states));assert len(newstates)==6
    added=[after.properties[k] for k in sorted(set(after.properties)-set(before.properties))]
    assert Counter(p['quantity'] for p in added)=={'glass_transition_temperature':6,'melting_peak_temperature':2}
    source_changes={}
    for sid,old in before.sources.items():
        new=after.sources[sid]
        if new==old:continue
        assert {k for k in new if new[k]!=old[k]}=={'claim_notes'}
        assert new['claim_notes'][:len(old['claim_notes'])]==old['claim_notes']
        source_changes[sid]=len(new['claim_notes'])-len(old['claim_notes'])
    assert source_changes=={'tarasov_2022_pna_bpf_epoxy':1,'abbasi_2022_manure_phbv':2}
    chain={};previous=before.snapshot
    for stage in ('r26','r27','r28'):
        folder=OUT.parent/('local-acceptance-'+stage);suffix=stage.upper()
        entry=folder/('REVIEW_INPUTS_'+suffix+'.json');review=read(folder/('INDEPENDENT_ACCEPTANCE_REVIEW_'+suffix+'.json'));app=read(folder/('APPLICATION_'+suffix+'.json'))
        assert review['decision']=='clear' and review['review_inputs_sha256']==sha(entry)
        assert app['before_snapshot']==previous;previous=app['after_snapshot']
        chain[stage]=dict(input_sha256=sha(entry),decision=review['decision'],after_snapshot=previous)
    assert previous==after.snapshot
    delta=dict(baseline_commit=BASE,baseline_snapshot=before.snapshot,current_snapshot=after.snapshot,
        old_complete_properties_unchanged=5327,old_complete_states_unchanged=5212,new_properties=8,
        new_properties_by_quantity=dict(Counter(p['quantity'] for p in added)),new_property_ids=[p['id'] for p in added],new_state_ids=newstates,
        new_identities=0,new_grades=0,new_states=6,new_sources=0,existing_state_changes={},source_changes=source_changes,
        state_fact_change='No published state changed;local newPHBVDSCstate revision1.0.1 adds two meltingpeaks.',local_acceptance_chain=chain,polymer_summary=after.summary(category='polymer'))
    write(OUT/'NATIVE_DELTA_R26_R28.json',delta)
    facts=dict(property_records={p['id']:p for p in added},state_records={k:after.states[k] for k in newstates},source_records={k:after.sources[k] for k in source_changes},
        source_counts={s:len(list(after.records(source=s))) for s in source_changes},rows=[dict(id=p['id'],quantity=p['quantity'],number=p['reported_value']['number'],value_text=p['reported_value']['value_text']) for p in added])
    assert facts['source_counts']=={'tarasov_2022_pna_bpf_epoxy':40,'abbasi_2022_manure_phbv':7}
    write(OUT/'SOURCE_FACTS_R26_R28.json',facts)
    binding={}
    for name in ('README.md','HANDOFF.md','docs/DATABASE_COVERAGE.zh.md','docs/MATERIAL_SOURCE_CONDITIONS.zh.md','docs/OPEN_DATABASE_ROADMAP.zh.md'):
        p=ROOT/name;arc=OUT/'pre-delivery-documents'/name;arc.parent.mkdir(parents=True,exist_ok=True);assert not arc.exists();arc.write_bytes(p.read_bytes())
        link=('../' if name.startswith('docs/') else '')+'experimental/polymer-exploration/20261104/delivery-r26-r28/README.zh.md'
        if name=='README.md':
            header=('## Current database checkpoint: polymer r26-r28 (2026-11-04)\n\n'
                'Current native tables contain **5,180 identities, 5,218 states and 5,335 properties**. Polymer coverage is **1,037 identities, 1,075 states and 1,176 properties**: 1,000 computational-reference and 176 experimental-reference labels, without scientific certification.\n\n'
                'Three accepted local rounds add eight thermal properties on existing identities: five epoxy Tg values, one PHBV-39 Tg and two separately labelled PHBV-39 melting peaks. Six DSC states are added. All 5,327 preceding property objects and 5,212 preceding state objects remain completely unchanged; two existing sources only append notes.\n\n'
                'Tg and melting peaks share a closed temperature branch. Source signs/precision and Celsius/kelvin difference roles are retained without automatic conversion. Two peaks stay separate records on the same DSC state, not an interval, average, two materials or two independent runs. Epoxy abstract 174.5 versus table 174.7 and its incorrect Table 8 reference remain unresolved. PHBV original/reanalysis attribution, selected n and numerical dispersion remain unknown; common duplicate testing does not establish selected-cell n.\n\n'
                'Among 176 experimental property objects, 111 temperature fields and 124 conditioning fields are unreported; exact n is unconfirmed for 109 (105 null, four lower bounds). Counts are properties, not independent test groups; a reported scan program is not ambient temperature.\n\n'
                '[Evidence and experimental delivery]('+link+'). Snapshot `'+after.snapshot+'`; native software remains 0.35.0. Consolidated tests, installation, commit and remote CI require their exact subsequent receipts. No main merge, stable release or deployment is claimed. Earlier checkpoints retain historical context.\n\n')
        else:
            header=('## r26-r28聚合物统一实验交付（2026-11-04）\n\n'
                '当前[交付与核验入口]('+link+')汇总三轮既有材料热性质补充：5条环氧Tg、1条PHBV-39 Tg和2条同DSC状态熔融峰，共8性质、6状态，无新身份／牌号／来源。全部5327前驱性质和5212前驱状态完整保持，2来源仅追加说明。\n\n'
                '当前全库5180身份、31牌号、5218状态、5335性质、133来源；聚合物1037身份、1075状态、1176性质，1000计算和176实验参考只是证据标签。双峰各自ID／标签／列证据保留，不合并温区或平均、不认定两个独立实验。环氧174.5／174.7及错表号、PHBV旧结果／重分析单格归属继续未知，duplicate仅共同方法，选定n／分散度未知。\n\n'
                '176实验性质中111条温度字段、124条调湿字段未报告；67确切n、105个n为空、4个仅下限，确切n未确认109条。按性质计数，不作独立试验组；扫描程序不等于环境温度，reported不证明湿度平衡完整。未核实内容不补默认值，不作科学／标准认证、工程允许值、使用温度或引擎输入。\n\n'
                '各批已独审；统一当前测试、实际安装、目录读取及提交／推送／CI以精确收据为准，不累加历史测试或冒用旧提交CI。完整历史回归、HTTP和平台全量未运行。不合并main、不稳定发布、不部署。以下历史原文保留。\n\n')
        raw=p.read_bytes();cut=raw.find(b'\n')+1;p.write_bytes(raw[:cut]+b'\n'+header.encode('utf-8')+raw[cut:])
        binding[name]=dict(before_sha256=sha(arc),archive_path=arc.relative_to(ROOT).as_posix(),current_sha256=sha(p))
    write(OUT/'PREDELIVERY_DOCUMENT_BINDING_R26_R28.json',binding)
    print(json.dumps(dict(snapshot=after.snapshot,new_properties=8,new_states=6,old_states_unchanged=5212,documents=5)))
if __name__=='__main__':main()
