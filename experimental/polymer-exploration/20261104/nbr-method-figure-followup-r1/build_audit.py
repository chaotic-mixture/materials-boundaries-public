"""Bind source methods and exact figure exclusions without admitting new values."""
from pathlib import Path
from copy import deepcopy
import hashlib,json,sys,zipfile,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[4]
OUT=Path(__file__).resolve().parent
EXT=ROOT.parent/'open-database-evidence/polymer-nbr-density-pdf-followup-20261104-r1'
XML=ROOT.parent/'open-database-evidence/polymer-nbr-strength-20261103-r1/article.xml'
SID='tamas_benyei_santha_2025_nbr_rcf'
sys.path.insert(0,str(ROOT))
from materials_boundaries.database import Database,canonical
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def write(p,d):
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(d,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
    assert not (OUT/'SOURCE_FACTS_R1.json').exists()
    assert sha(XML)=='2d8008e2b16dd3fe14b91a6747fb3632c70b461ccee4ccc8dea546dc3c272347'
    db=Database();assert db.snapshot=='698db32a4105434eeae26fd5724c709b2cec5bb965875ff1bf73ef5ec54cd726'
    hashes={n:sha(ROOT/'materials_boundaries/data'/(n+'.json')) for n in db.data}
    xml=ET.parse(XML).getroot();permissions=''.join(xml.find('.//permissions').itertext());assert 'CC-BY 4.0' in permissions
    with zipfile.ZipFile(EXT/'supplementary-files-r1.zip') as z:
        assert z.testzip() is None
        members=z.infolist();assert len(members)==26
        assert all(p.filename.lower().endswith(('.jpg','.gif')) for p in members)
        for n in ['ao5c05493_0006.jpg','ao5c05493_0008.jpg']:assert z.read(n)==(EXT/n).read_bytes()
    props={k:p for k,p in db.properties.items() if p['source_id']==SID};assert len(props)==12
    density=props['refprop_perbunan3445f_tamas_benyei2025_ref_mass_density']
    assert density['reported_value']['value_text']=='1.031' and density['uncertainty']['value_text']=='0.001'
    assert density['conditions']['test_method']['status']=='not_reported_in_inspected_source' and density['sample_count']['value'] is None
    write(EXT/'BASELINE_REF_DENSITY_R1.json',density)
    facts={'schema':'NBR-method-figure-source-followup/1','source_id':SID,'native_snapshot':db.snapshot,'prior_commit':'53dba9694df201957ea300bd768f785ce959183a','retained_XML_sha256':sha(XML),'new_archive_sha256':sha(EXT/'supplementary-files-r1.zip'),'archive_members':26,'returned_member_types':['jpg','gif'],'fresh_PDF_verified':False,'visual_scope':['official archive Figure6 hardness JPG','official archive Figure8 abrasion JPG'],'selected_native_properties':{k:{'quantity':p['quantity'],'state_id':p['material_state_id'],'canonical_property_sha256':hashlib.sha256(canonical(p)).hexdigest()} for k,p in props.items()},'canonical_hash_method':'SHA256 of database.canonical(object),UTF8 sorted compact JSON,no trailing LF','source_counts':{'total_property_objects':12,'polymer_properties':sum(db.identities[db.states[p['material_state_id']]['identity_id']]['category']=='polymer' for p in props.values()),'composite_properties':sum(db.identities[db.states[p['material_state_id']]['identity_id']]['category']=='composite' for p in props.values())},
      'confirmed_method_context':{'locator':'Retained official XML section2.2 Test Methods;not density-specific','Shore_A':{'source_cited_standard':'ISO7619-1,no edition inferred','instrument':'Zwick/Roell H04.3150.000','indentation_time_s':'3','load_N':'8.05','points_per_sample':'10','spacing_mm':'10','aggregation':'average and standard deviation per formulation reported','independent_specimens_or_total_n':'unknown;10 locations per sample do not establish independent specimens or total pooled n'},'abrasion':{'source_cited_standard':'ASTMD5963-04','instrument':'MV rotary drum abrasion tester','specimens_per_material':'3 round pieces','source_method':'before/after weights,differences,average and SD','density_transfer':'none;these3pieces and statistics are not density n/uncertainty definitions'},'other_counts_not_density_n':['300 fibers for length distribution','two mutually perpendicular mechanical test orientations'],'preparation_not_density_environment':['110°C mixing','170°C/200bar pressing','formulation-specific t90','three-step D_Fo hot-air foaming']},
      'figure6_disposition':{'axis':'Shore A hardness versus rCF phr','visible_regression':{'equation':'y=0.527x+58.474','R_squared':'0.9737'},'numeric_point_labels':False,'action':'Do not digitize plotted means/error bars. Do not use58.474 as measuredREF hardness or generate values from fittedline. No new ShoreA properties.','statistics_boundary':'Method reports mean/SD but exact plotted scalar/SD values are not supplied as individual labels in the inspected image.'},
      'figure8_disposition':{'axis':'abrasion percent versus rCF phr','visible_regression':{'equation':'y=0.3665x+0.2109','R_squared':'0.9824'},'numeric_bar_labels':False,'action':'No bar/errorbar digitization,reference-line scalar extraction or fitted values. No new abrasion quantity or records.','regression_scope':'Figure has six B–G positions while x-axis labels are phr;do not infer fitting-variable semantics or source recipes from coefficient alone.','annotation_discrepancy':{'printed_y_axis_range_percent':['0','3.00'],'printed_x_axis_includes_phr':'50','literal_equation_at_x50':'18.5359','disposition':'If printed x means phr,this exceeds the displayed0–3percent range.Fit variable/units remain unresolved;do not substitute formulation index orrepair coefficients. Diagnostic arithmetic only,not a material property.'}},
      'density_disposition':{'locator':'Retained XML section3.4 foaming paragraph','REF_expression':'1.031 ±0.001g/cm3','D_expression_lead_only':'1.161 ±0.013g/cm3','D_Fo_expression_excluded':'0.181 ±0.032g/cm3','existing_REF_action':'Preserve complete property object andunknown method,volume convention,temperature,RH,conditioning,aggregation,plusminus meaning,n.','D_action':'Existing formulation correspondence is a research lead only;no density property admitted without separate basis/method/identity review.','D_Fo_action':'Outside existing nonfoamed state;not a new admitted identity or density candidate.'},
      'rights':{'article_license':'CC-BY4.0 verified from retained XML','selected_figures':'Figures6/8 captions have no separate third-party credit in inspected XML;rawimages stay external.','third_party_boundary':'Figure1 credits Ceresana reprint permission;article license is not a blanket relicensing of every archived asset or cited standard.'},
      'limits':['No fresh original PDF obtained;existing historical PDF review is not replaced or denied.','No complete-archive scientific/supplement completeness or latest correction/retraction claim.','New figure evidence cannot fill density-specific missing facts;absence conclusion limited to inspected source sections/images.','No graph digitization,reanalysis,new measurements or scientific certification.'],'native_changes':0,'new_properties_states_identities':0,'unknowns_filled':0,'tests_or_installation':'not_run_source_followup_only','pushed':False}
    assert facts['source_counts']=={'total_property_objects':12,'polymer_properties':6,'composite_properties':6}
    write(OUT/'SOURCE_FACTS_R1.json',facts)
    old=deepcopy(db.sources[SID]);new=deepcopy(old)
    new['urls'].append('https://www.ebi.ac.uk/europepmc/webservices/rest/PMC12750214/supplementaryFiles')
    new['claim_notes'].append('2026-11-04 official-archive figure/method follow-up:retained XML SHA256 '+sha(XML)+' and new image archive SHA256 '+sha(EXT/'supplementary-files-r1.zip')+'. Selected Figures6/8 inspected,not a freshPDF. ShoreA method reports3s,8.05N,10locations/sample,10mm spacing and mean/SD;not independent specimen n or density protocol. Unlabelled points,bars,errorbars and regression equations are not transcribed as material scalars. REF density1.031±0.001g/cm3 and all12 existing properties unchanged;density method/volume convention/conditions/statistics/n remain unknown. No new hardness,abrasion,D orD_Fo density admission. Figure1 third-party credit not blanket-relicensed.')
    write(OUT/'SOURCE_UPDATE_PROPOSAL_R1.json',{'status':'unapplied_source_metadata_proposal;separate_mapping_andintegration_required','source_id':SID,'baseline_source':old,'proposed_source':new,'changed_fields':['urls','claim_notes'],'native_applied':False})
    assert hashes=={n:sha(ROOT/'materials_boundaries/data'/(n+'.json')) for n in db.data}
    write(OUT/'VALIDATION_R1.json',{'native_snapshot':db.snapshot,'native_tables_unchanged':hashes,'all12_native_property_objects_preserved':True,'REF_density_method_unknown':True,'archive_member_crc':'passed','selected2images_equal_archive_members':True,'new_numeric_properties':0,'unit_suites_run':0,'scientific_certification':False,'proposal_applied':False})
    print(json.dumps({'properties_preserved':12,'new_values':0,'unknowns_filled':0,'new_archive_images_checked':2}))
if __name__=='__main__':main()
