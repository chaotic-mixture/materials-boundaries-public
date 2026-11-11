"""Prepare two unapplied source-limited LFA facts;never write native tables."""
from pathlib import Path
from copy import deepcopy
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from materials_boundaries.database import Database,read_snapshot
from materials_boundaries.material_references import validate_material_catalog
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(name,obj):
    with (HERE/name).open('x',encoding='utf-8',newline='\n') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
    impl=HERE.parent/'nr-thermal-contract-implementation-r1'
    entry=impl/'REVIEW_IMPLEMENTATION_INPUTS_R1.json';review=read(impl/'INDEPENDENT_IMPLEMENTATION_REVIEW_R1.json')
    assert review['decision']=='approved' and review['review_inputs_sha256']==sha(entry)
    pins=read(entry)
    assert all(sha(ROOT/n)==h for n,h in pins['repo_files_sha256'].items())
    source=HERE.parent/'nr-thermal-source-contract-r1'
    sr=read(source/'INDEPENDENT_SOURCE_CONCEPT_REVIEW_R1.json')
    assert sr['decision']=='approved' and sr['review_inputs_sha256']==sha(source/'REVIEW_INPUTS_R1.json')
    before=Database();data=deepcopy(before.data)
    assert before.snapshot=='6441d83014936d3a92156278fd85cbb437c77f481ce35272c388066eb050a4d8'
    sid='bianchi_2025_nr_nanoclay';url='https://mdpi-res.com/d_attachment/molecules/molecules-30-03035/article_deploy/molecules-30-03035.pdf'
    def ev(locator,*tags):return dict(source_id=sid,url=url,locator=locator,supports=list(tags))
    def unknown(note):return dict(status='not_reported_in_inspected_source',text=None,evidence=[],notes=note)
    def reported(text,locator,tags=('condition',),notes=None):return dict(status='reported',text=text,evidence=[ev(locator,*tags)],notes=notes)
    loc='PDF p18 section3.3.3 Thermal Properties'
    parent=before.states['state_smr10_bianchi2025_nr'];state=deepcopy(parent)
    state.update(id='state_smr10_bianchi2025_nr_lfa',version='1.0.0',name='SMR10 study unfilled NR,LFA cylindrical specimens',names={
        'en':'SMR10 study unfilled NR,LFA cylindrical specimens','zh':'SMR10研究未填充NR，LFA圆柱试样','ja':'SMR10研究未充填NR、LFA円柱試験片','de':'SMR10 Studien-NR ohne Nanoton,LFA-Zylinderproben'})
    state['aliases']=[];state['source_designation']='NR;unfilled NR formulation,LFA specimens'
    state['state']['product_form']=reported('Cylindrical LFA specimens,12.7mm diameter and1mm thickness',loc,('state',),
        'Method-specific geometry;cutting procedure and physical linkage to separately tested mechanical/density specimens unknown.')
    state['state']['conditioning']=unknown('LFA-specific humidity,drying,storage and post-cure interval unspecified.')
    state['state']['orientation']=unknown('Cylinder axis relative to sheet processing direction unspecified;scalar result does not establish isotropy.')
    state['source_scope']='Same study NR formulation and cure recipe as existing identity/grade;separate LFA specimen geometry. Three tested specimens per formulation and five pulses per specimen are method facts,not per-cell statistical n or15 independent replicates. No new material identity or independent batch claimed.'
    state['evidence'].append(ev(loc,'state'));state['property_ids']=[]
    template=before.properties['refprop_smr10_bianchi2025_nr_volumetric_tensile_work_to_break']
    properties=[]
    for qty,dim,number,amp,code,text,label in [
        ('mass_specific_heat_capacity','energy_per_mass_temperature','1.70','0.05','J/(g*K)','J/g·K','Specific heat capacity,cp'),
        ('thermal_diffusivity','area_per_time','0.081','0.001','mm^2/s','mm²/s','Thermal diffusivity')]:
        p=deepcopy(template);p.pop('work_reference_basis');p['source_discrepancies']=[]
        p.update(id='refprop_smr10_bianchi2025_nr_'+qty,version='1.0.0',material_state_id=state['id'],quantity=qty,quantity_dimension=dim,source_property_label=label)
        p['reported_value'].update(number=number,value_text=number,unit_code=code,unit_text=text)
        p['summary_statistic']='not_stated';p['uncertainty_status']='reported_plus_minus_unspecified'
        p['uncertainty'].update(type='reported_plus_minus_unspecified',number=amp,value_text=amp,unit_code=code,unit_text=text,
            scope='Source Table3 plus-minus amplitude;meaning unspecified for these thermal values,not imported mechanical SD.',evidence=[ev('PDF p6 Table3,NR row','uncertainty')])
        p['uncertainty_note']='Thermal plus-minus meaning,coverage and estimator unspecified;no mechanical SD or propagated error assigned.'
        p['sample_count']=dict(value=None,relation='not_reported',scope='Per-cell contributing statistical n unknown;three tested specimens and five pulses each retained only as distinct method facts.',source_statement='Three specimens tested per formulation;five pulses performed for each specimen.',evidence=[ev(loc,'sample_count')])
        p['basis_note']='Source Table3 thermal summary;central estimator unspecified. LFA measured response processing does not establish an independent material batch or a computed-material identity.'
        p['conditions']=dict(temperature=reported('20 °C',loc),test_standard=reported('ASTM-E1461 as cited',loc,notes='Edition and independent compliance unknown.'),
            test_method=reported('Netzsch LFA447;Pyroceram9606 reference for heat capacity;Cowan method with numerical pulse correction for diffusivity',loc),
            direction=unknown('Heat transport direction relative to sheet processing unknown;no isotropy inference.'),
            conditioning=unknown('RH,drying,conditioning,storage and post-cure interval unspecified for LFA.'),
            loading_rate=dict(status='not_applicable',text=None,evidence=[],notes='Mechanical loading rate is not a condition of this LFA thermal result.'),
            additional_conditions=[dict(name=n,fact=f) for n,f in [
                ('method_tested_specimens',reported('Three tested specimens per NR formulation',loc,notes='Not proven per-cell aggregation n or independent batches.')),
                ('pulses_per_specimen',reported('Five pulses for each specimen',loc,notes='Technical pulses;not five independent specimens or n15.')),
                ('test_atmosphere',unknown('Gas composition,pressure and flow unspecified.')),
                ('test_relative_humidity',unknown('No LFA humidity assigned.')),
                ('calibration_implementation',unknown('Reference named,but full calibration implementation and traceability unverified.'))]])
        p['method_definition']=dict(type='source_reported_conventional',definition=(
            'Source LFA heat-capacity determination using Pyroceram9606 reference;source calls quantitycp,constant-pressure experimental conditions independently unverified.' if qty=='mass_specific_heat_capacity' else
            'Source LFA thermal diffusivity using Cowan method with numerical pulse correction;no software pulse refit or mass-diffusion interpretation.'),
            extraction_window=None,evidence=[ev(loc,'method')])
        p['method_definition']['definition']+=' Pulse-processing window,fit interval and aggregation order unspecified.'
        if qty=='mass_specific_heat_capacity':p['thermal_mass_reference_basis']=unknown('As-received/dry mass basis and moisture content unspecified;unit establishes mass normalization only.')
        p['evidence']=[ev('PDF p6 Table3 NR row;p18 section3.3.3','reported_value','classification')]
        inspection='Retained officialPDF p6Table3 and p18section3.3.3,source recipe pp16-17 and same-source XML inspected;thermal statistics remain unspecified. No raw pulse reanalysis or latest-notice verification.'
        p['source_document']['inspection_scope']=inspection;p['verification']['source_inspection_scope']=inspection
        p['scope_note']='Study-specific unfilled vulcanizate at20C using source LFA method. Not a universal bound or design allowable. Per-cell n,estimator,plus-minus meaning,independent batches,RH,conditioning,atmosphere,direction and calibration implementation unknown. No conversion,thermal-conductivity product or uncertainty propagation.'
        properties.append(p);state['property_ids'].append(p['id'])
    source_before=before.sources[sid];source_after=deepcopy(source_before)
    source_after['claim_notes'].append('Additional selected NR Table3 heat capacity and diffusivity retain20C,LFA cylinder geometry,three method specimens and five pulses separately;thermal estimator,plus-minus meaning and per-cell n unknown. Source-calculated conductivity held pending separate provenance contract.')
    data['sources']['records']=[source_after if x['id']==sid else x for x in data['sources']['records']]
    data['materials']['records'].append(state);data['reference_properties']['records'].extend(properties)
    validate_material_catalog(*(data[n] for n in ['materials','reference_properties','sources']))
    after=Database(data)
    assert before.identities==after.identities and before.grades==after.grades
    assert all(after.properties[k]==v for k,v in before.properties.items()) and all(after.states[k]==v for k,v in before.states.items())
    write('NEW_PROPERTIES_R1.json',properties);write('NEW_STATE_R1.json',state)
    write('SOURCE_UPDATE_R1.json',dict(before=source_before,after=source_after))
    write('VALIDATION_R1.json',dict(baseline_snapshot=before.snapshot,candidate_snapshot=after.snapshot,properties=len(after.properties),states=len(after.states),new_properties=2,new_states=1,old_properties_states_unchanged=True,identities_grades_unchanged=True,native_applied=False,installation='not_run',conductivity='held'))
    print(json.dumps(dict(properties=len(after.properties),states=len(after.states),snapshot=after.snapshot,native_applied=False)))
if __name__=='__main__':main()
