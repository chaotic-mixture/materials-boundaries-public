"""Revise preparation provenance without changing unknown test conditioning."""
from pathlib import Path
from copy import deepcopy
import hashlib,json,sys,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
EXT=ROOT.parent/'open-database-evidence/polymer-pur-preparation-revisions-20261112-r1'
sys.path.insert(0,str(ROOT))
from materials_boundaries.database import Database,read_snapshot
from materials_boundaries.material_references import validate_material_catalog
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')

def main():
    before=Database();assert len(before.properties)==5640 and len(before.states)==5373
    pdf=ROOT.parent/'open-database-evidence/polymer-pur-thermal-source-20261104-r1/article-r2.pdf'
    xml=ROOT.parent/'open-database-evidence/polymer-pur-20261103/article-r1.xml'
    assert sha(pdf)=='70b6da773e757f43557ed69bb651ce14e8ff82c1f09d39de1f50671343239e0e'
    assert sha(xml)=='4e0c1a91a9ae26d814576961a3805f9371b46498d4861fb578e7a413bb4c726d'
    tree=ET.parse(xml);section=next(x for x in tree.iter('sec') if x.get('id')=='sec2dot7-polymers-16-00942')
    paragraphs=[' '.join(''.join(x.itertext()).split()) for x in section.findall('p')]
    assert any('24 h to cure at room temperature' in p and 'Before any additional testing' in p for p in paragraphs)
    EXT.mkdir(exist_ok=False)
    write(EXT/'SOURCE_PREPARATION_READBACK_R1.json',dict(pdf_sha256=sha(pdf),xml_sha256=sha(xml),locator='PDF page7 Section2.7 optimized large-mold specimens paragraph; JATS sec2dot7-polymers-16-00942',paragraphs=paragraphs,visual_page='Existing retained page-visual-07.png inspected in this stage',scope='Background cure only, not water temperature, conditioning completeness or per-cell sample counts'))
    sid='ivdre_2024_lpo_rigid_pur';pairs=[];selected=[]
    for old in before.properties.values():
        if old['source_id']!=sid or old['quantity'] in ('mass_density','water_absorption_volume_percentage'):continue
        assert old['source_document']['sha256']==sha(pdf) and old['version']=='1.0.0'
        assert old['conditions']['conditioning']['status']=='not_reported_in_inspected_source'
        p=deepcopy(old);p['version']='1.0.1'
        fact=dict(status='reported',text='Common optimized-foam preparation: 24 h cure at room temperature before additional testing',evidence=[dict(source_id=sid,url=p['source_document']['url'],locator='PDF p7 Section2.7, second paragraph, larger optimized foam samples; corroborated by JATS sec2dot7-polymers-16-00942',supports=['condition'])],notes='Preparation background only. Room-temperature value/RH, drying, storage, test-specific conditioning and equilibrium remain unknown; no proof of identical specimen, batch or timeline across methods. Do not overwrite the unknown conditioning field or transfer cup/compression/TGA sample counts.')
        additional=p['conditions'].setdefault('additional_conditions',[])
        assert not any(a['name']=='optimized_foam_cure_background' for a in additional)
        additional.append(dict(name='optimized_foam_cure_background',fact=fact))
        p['source_document']['inspected_on']='2026-11-12'
        p['source_document']['inspection_scope']+=' Follow-up 2026-11-12: retained same-byte PDF p7 Section2.7 visually rechecked with retained JATS for common optimized-foam 24h room-temperature cure; this adds preparation context only and does not establish test-specific conditioning or per-cell n.'
        p['verification']['source_inspection_scope']=p['source_document']['inspection_scope']
        assert p['sample_count']==old['sample_count'] and p['conditions']['conditioning']==old['conditions']['conditioning']
        pairs.append(dict(before=old,after=p));selected.append(p)
    assert len(pairs)==36
    replacements={p['id']:p for p in selected};data=deepcopy(before.data)
    data['reference_properties']['records']=[replacements.get(p['id'],p) for p in data['reference_properties']['records']]
    validate_material_catalog(*(data[n] for n in ['materials','reference_properties','sources']));after=Database(data)
    assert after.data['materials']==before.data['materials'] and after.data['sources']==before.data['sources']
    assert all(after.properties[k]==p for k,p in before.properties.items() if k not in replacements)
    exports=[]
    for name,filters,count in [('source-fortyfour',dict(source=sid),44),('water-four',dict(quantity='water_absorption_volume_percentage'),4)]:
        rows=list(after.records(**filters));assert len(rows)==count
        after.export(EXT/name,**filters);assert read_snapshot(EXT/name)[1]=={r['record_id']:r for r in rows}
        exports.append(dict(name=name,records=count,full_recovery=True))
    write(HERE/'PROPERTY_REVISIONS_R1.json',pairs)
    write(HERE/'VALIDATION_R1.json',dict(snapshot=after.snapshot,properties=5640,states=5373,sources=134,revised_properties=36,new_properties=0,new_states=0,new_identities=0,unmodified_properties=5604,materials_sources_unchanged=True,unknown_conditioning_unchanged=True,all_sample_counts_unchanged=True,scientific_graph='passed',exports=exports,native_changed=False))
    print(json.dumps(dict(revised_properties=36,properties=5640,snapshot=after.snapshot,native_changed=False)))
if __name__=='__main__':main()
