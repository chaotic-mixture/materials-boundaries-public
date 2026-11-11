"""Map thirty-six source mechanical cells without native writes or source repair."""
from pathlib import Path
from copy import deepcopy
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
PRIOR=HERE.parent/'local-acceptance-r44';SOURCE=HERE.parent/'nr-clay-mechanical-source-draft-r1'
sys.path.insert(0,str(ROOT))
from materials_boundaries.database import Database
from materials_boundaries.material_references import validate_material_catalog
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(n,obj):
    with (HERE/n).open('x',encoding='utf-8',newline='\n') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
    entry=PRIOR/'REVIEW_FINAL_INPUTS_R44.json';approval=read(PRIOR/'INDEPENDENT_FINAL_REVIEW_R44.json')
    assert approval['decision']=='approved' and approval['review_inputs_sha256']==sha(entry)
    for field in ('repo_files_sha256','external_files_sha256'):
        for n,h in read(entry)[field].items():assert sha(Path(n) if field=='external_files_sha256' else ROOT/n)==h,n
    for field in ('native_files_sha256','external_files_sha256'):
        for n,h in read(SOURCE/'EVIDENCE_BINDINGS_R1.json')[field].items():assert sha(Path(n) if field=='external_files_sha256' else ROOT/n)==h,n
    before=Database();assert before.snapshot=='246e297ea3a81414601d9c93d3776b3162722b41bb3fed76e9f0bc92a56e95e2'
    data=deepcopy(before.data);facts=read(SOURCE/'SOURCE_FACTS_R1.json');assert len(facts)==36
    primary='bianchi_2025_nr_nanoclay';doc=deepcopy(before.properties['refprop_smr10_bianchi2025_nr_volumetric_tensile_work_to_break']['source_document']);url=doc['url']
    def ev(where,*tags):return dict(source_id=primary,url=url,locator=where,supports=list(tags))
    def unknown(note):return dict(status='not_reported_in_inspected_source',text=None,evidence=[],notes=note)
    def rebind(value,locator):
        if isinstance(value,dict):
            if all(k in value for k in ('source_id','url','locator','supports')):value.update(source_id=primary,url=url,locator=locator)
            else:
                for child in value.values():rebind(child,locator)
        elif isinstance(value,list):
            for child in value:rebind(child,locator)
    states={};props=[]
    hardtemplate=before.states['state_smr10_bianchi2025_nr_shore_a_nominal_3mm']
    for fact in facts:
        old=before.states[fact['existing_state_id']];identity=before.identities[fact['existing_identity_id']];hard=fact['quantity']=='shore_a_hardness'
        assert old['identity_id']==identity['id'] and identity['category']=='composite'
        label=fact['source_designation'];context=fact['context_proposed'];key=old['id']+'_'+context
        if key not in states:
            s=deepcopy(old);s.update(id=key,version='1.0.0',name=label+' '+context,names={lang:label+' '+context for lang in ('en','zh','ja','de')},aliases=[],source_designation=label+';'+context,property_ids=[])
            if hard:
                for field in ('product_form','processing','temper_or_heat_treatment','conditioning','orientation'):s['state'][field]=deepcopy(hardtemplate['state'][field])
                for field in ('product_form','processing','temper_or_heat_treatment','conditioning','orientation'):rebind(s['state'][field],'PDF p18 section3.3.4 hardness protocol; p16 section3.2 general1mm sheets; p7 Table4 '+label+' Shore A')
                scope='Separate source-nominal15mm-wide/3mm-thick hardness context. Specific manufacture,cure,stacking,actual thickness and linkage to general1mm sheets unresolved;general120C/3bar process not asserted as actual3mm specimen history.'
            else:
                s['state']['product_form']=unknown('Actual quasi-static tensile specimen geometry/cutting procedure not stated. Source section3.2 general120x120x1mm sheet dimensions are not assigned as tensile specimen dimensions;25mm extensometer gauge is not a geometry substitute.')
                s['state']['conditioning']=unknown('Quasi-static tensile humidity,drying,storage,recovery and post-cure interval unspecified;separate cyclic/relaxation/caloric precycles not assigned.')
                s['state']['orientation']=unknown('Tensile direction relative to source sheet processing axis unspecified;no isotropy claim.')
                scope='Source-formulation quasi-static tensile context. General formulation preparation/cure context retained,actual tensile specimen geometry,cutting and physical batch linkage unknown. No transfer of3mm hardness or45mm caloric geometry.'
            s['state']['porosity']=unknown('Void fraction for these selected test specimens unknown;nonfoamed preparation does not establish zero porosity.')
            s['source_scope']=identity['identity_scope']+' '+scope+' Mechanical method counts and stages do not certify new materials,independent batches or cross-method physical pairing.'
            s['evidence'].append(ev('PDF p7 Table4 '+label+';p18-19 section3.3.4; p16-17 source recipe','state'));states[key]=s
        s=states[key];p=deepcopy(before.properties[fact['existing_unfilled_NR_contract_template_id']])
        suffix=fact['existing_unfilled_NR_contract_template_id'].removeprefix('refprop_smr10_bianchi2025_nr_')
        p.update(id=old['id'].replace('state_','refprop_',1)+'_'+suffix,version='1.0.0',material_state_id=s['id'])
        assert p['id'] not in before.properties
        locator=fact['source_locator']+';'+fact['sample_count_locator']+';'+fact['statistics_locator']+';p16 section3.2 general preparation'
        rebind(p,locator)
        p['reported_value'].update(number=fact['number'],value_text=fact['number'])
        p['uncertainty'].update(number=fact['standard_deviation'],value_text=fact['standard_deviation'])
        assert p['reported_value']['unit_text']==fact['unit_text'] and p['summary_statistic']=='reported_mean' and p['sample_count']['value']==5 and p['uncertainty_status']=='reported_standard_deviation'
        p['basis_note']='Source Table4 '+label+' selected '+p['source_property_label']+';section3.3.4 mechanical mean/SD and five specimens for the corresponding method. No pooling,reconstruction or cross-method independence claim.'
        p['uncertainty_note']=fact['number']+' ± '+fact['standard_deviation']+' '+fact['unit_text']+':source mechanical mean/SD,not SE/CI or a relative percentage. No standard-error conversion,software integration or uncertainty propagation.'
        p['uncertainty']['scope']='Source SD for selected '+label+' mechanical method group;not SE,CI,relative percent,independent batches or uncertainty transferred from another quantity.'
        if hard:p['uncertainty']['scope']+=' Absolute Shore A scale points,not pressure.'
        p['scope_note']='Source-qualified '+label+' '+p['source_property_label']+'. '+p['method_definition']['definition']+' Mean/SD/n5 are limited to the corresponding source mechanical method,not independent batches or cross-method pairing. Temperature of quasi-static tensile tests,RH,conditioning,orientation,actual geometry/preparation linkage and reduction conventions remain unknown except explicitly reported hardness geometry/temperature. No universal bound,engineering allowable,engine input,cross-scale or modulus/pressure conversion;related break-elongation unit conflict remains held.'
        if hard:
            p['source_discrepancies'][0]['disposition']='Keep separate source-nominal3mm hardness context;do not certify general1mm preparation as actual3mm manufacture,repair thickness or infer stacking/layers.'
        elif fact['quantity']=='volumetric_tensile_work_to_break':
            p['source_discrepancies']=[dict(description='Table4 epsilon_b header is mm/mm while Figure3 axis is percent;selected '+label+' elongation unit conflict unresolved.',disposition='Keep elongation held;transcribe only explicit Eb '+fact['number']+' ± '+fact['standard_deviation']+' J/cm³. No strain-unit repair,division by100 or work reconstruction.',evidence=[ev('PDF p7 Table4 '+label+' epsilon_b/Eb andFigure3 axes','source_discrepancy')])]
        inspection='Retained officialPDF p7Table4 '+label+' selected mechanical cell,p18-19section3.3.4 andp16-17recipe/geometry context. Six epsilon_b cells held for unit conflict. No raw curve reconstruction,source repair or latest-notice completeness certification.'
        p['source_document']=deepcopy(doc);p['source_document']['inspection_scope']=inspection
        p.setdefault('verification',{})['source_inspection_scope']=inspection
        props.append(p);s['property_ids'].append(p['id'])
    assert len(states)==12 and len(props)==36
    source_before=before.sources[primary];source_after=deepcopy(source_before)
    source_after['claim_notes'].append('Frozen Table4 mechanical candidate for six existing NR/clay formulations:36selected finite-interval modulus,specified-strain stresses,break stress,volumetric work andShore A facts;mean/SD/n5 confined to corresponding source methods. Six epsilon_b cells remain held for mm/mm-versus-percent conflict. Separate quasi-static and nominal3mm hardness contexts preserve unknown tensile temperature/geometry and unknown3mm manufacture/cure/stacking. No thermal-statistic transfer,new identity,independent-batch or cross-method physical-pairing claim. Actual admission requires later exact receipt.')
    data['materials']['records'].extend(states.values());data['reference_properties']['records'].extend(props);data['sources']['records']=[source_after if x['id']==primary else x for x in data['sources']['records']]
    validate_material_catalog(*(data[n] for n in ('materials','reference_properties','sources')));after=Database(data)
    assert all(after.properties[k]==v for k,v in before.properties.items()) and all(after.states[k]==v for k,v in before.states.items())
    assert before.identities==after.identities and before.grades==after.grades
    assert len(after.properties)==5486 and len(after.states)==5289 and len(after.sources)==134
    write('NEW_PROPERTIES_R1.json',props);write('NEW_STATES_R1.json',list(states.values()));write('SOURCE_UPDATE_R1.json',dict(before=source_before,after=source_after,changed_fields=['claim_notes'],native_applied=False))
    write('VALIDATION_R1.json',dict(baseline_snapshot=before.snapshot,candidate_snapshot=after.snapshot,properties=len(after.properties),states=len(after.states),sources=len(after.sources),new_properties=36,new_context_states=12,new_identities=0,new_grades=0,new_sources=0,old5450properties_unchanged=True,old5277states_unchanged=True,identities_grades_unchanged=True,held_elongation_cells=6,native_applied=False,installation='not_run'))
    print(json.dumps(dict(snapshot=after.snapshot,properties=len(after.properties),states=len(after.states),native_applied=False)))
if __name__=='__main__':main()
