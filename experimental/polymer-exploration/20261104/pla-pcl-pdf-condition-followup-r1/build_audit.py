"""Freeze a PDF/source follow-up without changing native records or filling unknowns."""
from pathlib import Path
from copy import deepcopy
from collections import Counter
import hashlib,json,sys,zipfile

ROOT=Path(__file__).resolve().parents[4]
OUT=Path(__file__).resolve().parent
EXT=ROOT.parent/'open-database-evidence/polymer-pla-pcl-pdf-followup-20261104-r1'
XML=ROOT.parent/'open-database-evidence/polymer-pla-pcl-source-readback-20261103-r2/article.xml'
SID='delgado_aguilar_2020_pla_pcl'
sys.path.insert(0,str(ROOT))
from materials_boundaries.database import Database

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def write(p,d):
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(d,f,ensure_ascii=False,indent=2);f.write('\n')

def main():
    assert not (OUT/'AUDIT_FACTS_R1.json').exists()
    native={ROOT/'materials_boundaries/data'/n for n in ['materials.json','reference_properties.json','sources.json']}
    before={str(p):sha(p) for p in native}
    db=Database();assert db.snapshot=='b4c2f6c279400bd67848c4ec049a7050f9c984ad4c247702693596b1da74a306'
    assert sha(EXT/'article-r1.pdf')=='2818f9f3904acc4fb687c6fe8f4a049626f7353e94311fe4679833c67d2b2ab9'
    assert sha(XML)=='1fc618818e73292837129bd4bf9885b71982974d5e7fead0056276fb28f8cb6b'
    with zipfile.ZipFile(EXT/'supplement-api-r1.zip') as z:
        assert z.read('materials-13-02655-s001.pdf')==(EXT/'supplement-archive-r1.pdf').read_bytes()
    assert sha(EXT/'supplement-archive-r1.pdf')=='438431f2d917747560fb967807a748c58d94e62069277f1682395f5ed7301e9d'
    # Manually transcribed from visually inspected Table2, PDF page6; no curve digitization.
    # Each tuple: tensile strength/plus-minus, modulus/SD, break/plus-minus or None, max-stress strain/plus-minus.
    table={
      'b95_5':('59.22','2.03','3.70','0.13','4.79','0.21','3.39','0.16'),
      'b90_10':('56.38','2.96','3.60','0.26','6.86','0.32','3.64','0.23'),
      'b85_15':('53.39','3.01','3.38','0.27','10.07','0.29','3.50','0.28'),
      'b80_20':('49.37','1.86','3.20','0.19','15.32','0.56','4.01','0.24'),
      'b60_40':('34.51','2.56','2.55','0.09',None,None,'5.63','0.34'),
      'b40_60':('21.77','1.79','1.86','0.11',None,None,'7.56','0.45'),
      'b20_80':('19.95','0.96','1.13','0.05',None,None,'10.39','0.51')}
    columns={'tensile_strength':(0,'MPa'),'youngs_modulus':(2,'GPa'),'tensile_elongation_at_break':(4,'%'),'tensile_elongation_at_strength':(6,'%')}
    expected={f'refprop_delgado2020_pla_pcl_{form}_{q}':(row[i],row[i+1],unit) for form,row in table.items() for q,(i,unit) in columns.items() if row[i] is not None}
    props={k:p for k,p in db.properties.items() if p['source_id']==SID};assert set(props)==set(expected) and len(props)==25
    rows=[]
    for pid,p in props.items():
        value,amp,unit=expected[pid]
        assert p['reported_value']['value_text']==value and p['reported_value']['unit_text']==unit
        if p['quantity']=='youngs_modulus':
            measure=p['uncertainty']['measures'][0]
            assert measure['kind']=='standard_deviation' and measure['reported_value']['value_text']==amp
        else:
            assert p['uncertainty']['type']=='reported_plus_minus_unspecified' and p['uncertainty']['value_text']==amp
        assert p['summary_statistic']=='not_stated'
        assert p['sample_count']['value'] is None and p['sample_count']['relation']=='not_reported'
        assert all(p['conditions'][k]['status']=='not_reported_in_inspected_source' and p['conditions'][k]['text'] is None for k in ['temperature','conditioning','direction'])
        rows.append({'property_id':pid,'quantity':p['quantity'],'value_text':value,'plus_minus_text':amp,'unit_text':unit,'summary_statistic':p['summary_statistic'],'uncertainty_type':p['uncertainty']['type'],'sample_count':p['sample_count'],'temperature':p['conditions']['temperature']['status'],'conditioning':p['conditions']['conditioning']['status'],'direction':p['conditions']['direction']['status'],'pdf_locator':'Table2,page6; modulus SD interpretation page11 only','native_property_sha256':hashlib.sha256(json.dumps(p,sort_keys=True,ensure_ascii=False).encode()).hexdigest()})
    write(EXT/'BASELINE_SELECTED_PROPERTIES_R1.json',props)
    facts={'schema':'existing-PLA-PCL-PDF-condition-followup/1','native_snapshot':db.snapshot,'source_id':SID,'official_pdf_sha256':sha(EXT/'article-r1.pdf'),'official_pdf_pages':18,'visually_inspected_main_pages':[1,3,4,5,6,10,11,14,18],'official_supplement_sha256':sha(EXT/'supplement-archive-r1.pdf'),'supplement_pages':6,'visually_inspected_supplement_pages':[1,2,3,4,5,6],'selected_properties':rows,'quantity_counts':dict(Counter(p['quantity'] for p in props.values())),
      'confirmed_method_facts':{'method_locator':'PDF page4,sections2.3–2.4','instrument':'Instron1122','load_cell_capacity':'5kN;not applied load','source_cited_tensile_standard':'ISO527-1:2012;no independent compliance claim','crosshead_speed':'2mm/min;not specimen strain rate','clamp_separation':'115mm;not extensometer gauge length'},
      'condition_findings':{'temperature':'Unknown in inspected selected tensile methods/results;processing and MFI temperatures do not establish tensile environment.','conditioning':'Post-molding tensile conditioning remains unknown;60°C raw-material drying and pellet storage are not test conditioning.','humidity':'Test RH remains unknown.','replicate_count':'No selected tensile n established;do not infer from plus-minus or source-cited standard.','central_aggregation':'Unknown for selected25 scalar expressions.','modulus_uncertainty':'PDF page11 explicitly supports SD for Table2 Young modulus only;not transferred to other quantities.','strain_gauge_geometry_direction':'No selected tensile dimensions,extensometer gauge length,flow-relative direction or independent batch count established.'},
      'supplement_findings':{'tables':'S1–S7 commercial PP homopolymer/copolymer,HDPE,ABS,PS,PA12,PA6 product/reference lists with MatWeb links.','selected_blend_conditions':'No additional selected PLA/PCL test conditioning or replicate definition established by these six inspected pages.','license_boundary':'Article CC BY4.0 notice visually checked page18;not blanket permission for linked MatWeb/producer data or standards. No commercial properties imported.','printed_status':'Supplement retains FOR PEER REVIEW and Published:date placeholders. Record actual archive bytes;do not invent final revision metadata.'},
      'representation_limits':['Official PDF includes embedded figure text with peer-review page headers;do not count extracted duplicate text as new data or separate article versions.','Only selected pages visually inspected;not whole-PDF visual equivalence or current correction/retraction audit.','Main PDF and XML selected facts agree;full-document byte or semantic identity is not asserted.'],
      'access_limits':['Initial local urllib DNS failure retained. Elevated curl main PDF fetch returned0.','Guessed publisher supplementary URL returned404;official EuropePMC supplementaryFiles ZIP succeeded. No CAPTCHA bypass.','Parent-recorded download outcomes/headers/hashes are not independently authenticated OS traces.'],
      'native_changes':0,'new_properties':0,'new_materials':0,'unknowns_filled':0,'unit_suites':'not_run_source_followup_only','installation':'not_run','full_history_regression':'not_run','pushed':False}
    write(OUT/'AUDIT_FACTS_R1.json',facts)
    old=deepcopy(db.sources[SID]);new=deepcopy(old)
    new['read_status']='selected_official_archive_xml_html_and_official_pdf_pages_checked_with_supplement_condition_followup'
    new['claim_notes'].append('2026-11-04 PDF/condition follow-up:official article PDF SHA256 '+sha(EXT/'article-r1.pdf')+';selected pages1,3,4,5,6,10,11,14,18 visually checked.Table2 values/units and modulus-only SD interpretation agree with existing25 properties. Official EuropePMC supplement PDF SHA256 '+sha(EXT/'supplement-archive-r1.pdf')+';all6pages contain commercial comparison lists,not additional selected-blend conditioning or n. Test temperature,RH,post-molding conditioning,n,central aggregation and tensile geometry remain unknown. No commercial data or figure-digitized values imported;no blanket rights for linked sources;no latest correction/retraction certification.')
    new['urls']+=['https://mdpi-res.com/d_attachment/materials/materials-13-02655/article_deploy/materials-13-02655.pdf','https://www.ebi.ac.uk/europepmc/webservices/rest/PMC7321633/supplementaryFiles']
    new['provenance']['method']+=' Historical scope above describes the2026-10-26 inspection only. On2026-11-04 official PDF selected pages and all6 supplementary pages were subsequently inspected as recorded in the appended claim note. The old PDF access failure remains historical evidence;latest notices,full-document visual equivalence and linked commercial data rights remain unverified.'
    write(OUT/'SOURCE_UPDATE_PROPOSAL_R1.json',{'status':'unapplied_proposal_requires_separate_mapping_and_integration_review','source_id':SID,'baseline_source':old,'proposed_source':new,'permitted_changed_fields':['read_status','urls','claim_notes','provenance.method'],'property_state_identity_changes':0,'native_applied':False})
    assert before=={str(p):sha(p) for p in native}
    write(OUT/'VALIDATION_R1.json',{'selected_expressions_checked':25,'temperature_conditioning_and_n_unknown_preserved':25,'native_tables_unchanged':before,'snapshot_unchanged':db.snapshot,'scope':'Direct source-expression and preservation assertions,not unit suite or native acceptance','test_suites_run':0,'proposal_applied':False})
    print(json.dumps({'properties_checked':25,'unknowns_filled':0,'native_changed':False}))

if __name__=='__main__':main()
