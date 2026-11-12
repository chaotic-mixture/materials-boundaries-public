"""Add verified secondary-PDF evidence without changing source measurements."""
from pathlib import Path
from copy import deepcopy
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
EXT=ROOT.parent/'open-database-evidence/polymer-pla-pcl-evidence-revisions-20261112-r1'
sys.path.insert(0,str(ROOT))
from materials_boundaries.database import Database,read_snapshot
from materials_boundaries.material_references import validate_material_catalog
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
    pdf=ROOT.parent/'open-database-evidence/polymer-pla-pcl-pdf-followup-20261104-r1/article-r1.pdf'
    xml=ROOT.parent/'open-database-evidence/polymer-pla-pcl-source-readback-20261103-r2/article.xml'
    assert sha(pdf)=='2818f9f3904acc4fb687c6fe8f4a049626f7353e94311fe4679833c67d2b2ab9'
    assert sha(xml)=='1fc618818e73292837129bd4bf9885b71982974d5e7fead0056276fb28f8cb6b'
    before=Database();assert len(before.properties)==5640
    # Visually transcribed visible PDF p6 Table2; p4 Table1 supplies identity join.
    rows={
      'b95_5':['0.054','3.70','0.13','59.22','2.03','4.79','0.21','3.39','0.16'],
      'b90_10':['0.108','3.60','0.26','56.38','2.96','6.86','0.32','3.64','0.23'],
      'b85_15':['0.162','3.38','0.27','53.39','3.01','10.07','0.29','3.50','0.28'],
      'b80_20':['0.214','3.20','0.19','49.37','1.86','15.32','0.56','4.01','0.24'],
      'b60_40':['0.421','2.55','0.09','34.51','2.56',None,None,'5.63','0.34'],
      'b40_60':['0.621','1.86','0.11','21.77','1.79',None,None,'7.56','0.45'],
      'b20_80':['0.814','1.13','0.05','19.95','0.96',None,None,'10.39','0.51'],
    }
    columns={'youngs_modulus':(1,'E_t^B(GPa)'), 'tensile_strength':(3,'sigma_t^B(MPa)'), 'tensile_elongation_at_break':(5,'epsilon_t^B at Break(%)'), 'tensile_elongation_at_strength':(7,'epsilon_t^B at Max.Stress(%)')}
    source='delgado_aguilar_2020_pla_pcl';url='https://mdpi-res.com/d_attachment/materials/materials-13-02655/article_deploy/materials-13-02655.pdf';pairs=[]
    for old in before.properties.values():
        if old['source_id']!=source:continue
        key=next(k for k in rows if '_'+k+'_' in old['id']);row=rows[key];index,column=columns[old['quantity']]
        assert old['version']=='1.0.0' and old['reported_value']['number']==row[index]
        amplitude=old['uncertainty']['measures'][0]['reported_value']['number'] if old['quantity']=='youngs_modulus' else old['uncertainty']['number']
        assert amplitude==row[index+1]
        p=deepcopy(old);p['version']='1.0.1'
        p['evidence'].append(dict(source_id=source,url=url,locator='PDF p6 Table2, V_PCL '+row[0]+' row, '+column+' column; p4 Table1 '+key.upper().replace('_','/')+' identity join',supports=['reported_value','classification','uncertainty']))
        p['evidence'].append(dict(source_id=source,url=url,locator='PDF p4 Sections2.1–2.4; p5 Section3.1 processing caveat',supports=['method','condition']))
        if old['quantity']=='youngs_modulus':
            p['evidence'].append(dict(source_id=source,url=url,locator='PDF p11 Section3.2 paragraph following Equation6 explicitly links Table2 modulus variability to standard deviation',supports=['uncertainty']))
        scope='Primary retained official EuropePMC XML remains the source_document with its original URL/hash; selected Tables1–2 and methods are retained. Follow-up2026-11-12: same-byte publisher PDF visually checked on pp4–6 and11 for identity joins, all25 selected source values/printed amplitudes, mechanical method, processing caveat and modulus-specific SD wording. Secondary PDF SHA256 '+sha(pdf)+'. Earlier2026-10-26 no-PDF/access-failure statements describe historical inspection, not current scope. No new download, full-document equivalence, complete latest-notice audit, specimen replication or scientific/standard compliance certification.'
        p['source_document'].update(inspected_on='2026-11-12',inspection_scope=scope)
        p['verification']['source_inspection_scope']=scope
        assert p['conditions']==old['conditions'] and p['sample_count']==old['sample_count'] and p['uncertainty']==old['uncertainty']
        assert p['source_document']['url']==old['source_document']['url'] and p['source_document']['sha256']==old['source_document']['sha256']
        pairs.append(dict(before=old,after=p))
    assert len(pairs)==25
    replacements={x['after']['id']:x['after'] for x in pairs};data=deepcopy(before.data)
    data['reference_properties']['records']=[replacements.get(p['id'],p) for p in data['reference_properties']['records']]
    validate_material_catalog(*(data[n] for n in ['materials','reference_properties','sources']));after=Database(data)
    assert data['materials']==before.data['materials'] and data['sources']==before.data['sources']
    assert all(after.properties[k]==v for k,v in before.properties.items() if k not in replacements)
    EXT.mkdir(exist_ok=False);rowsout=list(after.records(source=source));assert len(rowsout)==25
    after.export(EXT/'source-twentyfive',source=source);assert read_snapshot(EXT/'source-twentyfive')[1]=={r['record_id']:r for r in rowsout}
    write(HERE/'PDF_TABLE2_READBACK_R1.json',dict(rows=rows,columns=columns,pdf_sha256=sha(pdf),xml_sha256=sha(xml),scope='Selected visible source cells, not plot digitization or new measurements'))
    write(HERE/'PROPERTY_REVISIONS_R1.json',pairs)
    write(HERE/'VALIDATION_R1.json',dict(snapshot=after.snapshot,properties=5640,states=5373,sources=134,revised_properties=25,new_properties=0,new_states=0,new_identities=0,other5615properties_unchanged=True,materials_sources_unchanged=True,all_conditions_statistics_values_counts_unchanged=True,primary_xml_url_hash_unchanged=True,scientific_graph='passed',complete_export_records=25,native_changed=False))
    print(json.dumps(dict(revised_properties=25,properties=5640,snapshot=after.snapshot,native_changed=False)))
if __name__=='__main__':main()
