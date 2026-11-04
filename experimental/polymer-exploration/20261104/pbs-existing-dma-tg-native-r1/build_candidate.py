"""Create nine isolated DMA Tg records on existing source formulation identities."""
from pathlib import Path
from copy import deepcopy
from unittest.mock import patch
import json,hashlib,sys

ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT))
from materials_boundaries.database import Database,read_snapshot
from materials_boundaries.material_presentation import render_material_catalog
from jsonschema import Draft202012Validator,FormatChecker
AREA=ROOT/'experimental/polymer-exploration/20261104'
OUT=Path(__file__).resolve().parent
SID='ewurum_mcdonald_2025_pbs_lignin'
URL='https://mdpi-res.com/d_attachment/polymers/polymers-17-00194/article_deploy/polymers-17-00194.pdf'
BASE='82e9840bca99bc36b273c1df7542f5d1019d4be3141df4584432eef88e399abc'
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(d,f,ensure_ascii=False,indent=2);f.write('\n')
def ev(loc,tags):return dict(source_id=SID,url=URL,locator=loc,supports=list(tags))
def fact(text,loc,note=None,tags=('condition',)):
    return dict(status='reported',text=text,evidence=[ev(loc,tags)],notes=note)
def unknown(note,status='not_reported_in_inspected_source'):
    return dict(status=status,text=None,evidence=[],notes=note)

def main():
    dest=Path(sys.argv[1]).resolve();assert not dest.exists() and not dest.is_relative_to(ROOT)
    proposal=AREA/'pbs-existing-dma-tg-source-r1';review=read(proposal/'INDEPENDENT_SOURCE_REVIEW_R1.json')
    assert review['decision']=='approved' and review['review_inputs_sha256']==sha(proposal/'REVIEW_INPUTS_R1.json')
    assert review['count_adjudication']['decision']=='method_context_only'
    assert review['count_adjudication']['selected_scalar_sample_count']=={'value':None,'relation':'not_reported'}
    manifest=read(proposal/'REVIEW_INPUTS_R1.json')
    for key in ['repo_files_sha256','native_files_sha256','external_files_sha256']:
        for n,h in manifest[key].items():assert sha(Path(n) if key=='external_files_sha256' else ROOT/n)==h,n
    facts=read(proposal/'SOURCE_FACTS_R1.json');contexts={a['identity']['id']:a for a in read(proposal/'BASE_CONTEXT_R1.json')['existing_formulations']}
    before=Database();assert before.snapshot==BASE
    methodloc='PDF p.4 section2.8 DMA paragraph;p.8 section3.4/Table3 tanδ-maximum criterion'
    program='DMA scan from−50 to120°C at3°C/min;cycle number,prior scan history and hold durations unknown.'
    definition='Source Table3 Tg from DMA tanδ maximum,Perkin Elmer DMA-7,three-point bending,15mm span,3×5×20mm bars,1Hz,0.2%strain,Pyrisv13.3. '+program+' Strain amplitude convention,static preload,gas andselected-scalar aggregation unknown;not DSC inflection,storage-modulus onset or loss-modulus maximum.'
    scope='Official PDF pp.3,4,8,9 identity/preparation,DMA method,Table3 andtanδ criterion;retained XML permissions. Selected content only;no rawtraces,calibration certificate,latest notice orstandard compliance verification.'
    props=[];states=[]
    for row in facts['rows']:
        ctx=contexts[row['identity_id']];old=ctx['existing_mechanical_state'];label=row['source_label']
        assert before.states[old['id']]==old and before.identities[row['identity_id']]==ctx['identity']
        assert before.states[ctx['existing_DSC_state']['id']]==ctx['existing_DSC_state']
        loc='PDF p.8 Table3 '+label+' row × Tg(°C) column;section3.4 tanδ-maximum definition'
        s=deepcopy(old)
        name=label+' PBS formulation,DMA tanδ-maximum Tg bar specimen'
        s.update(id=row['new_DMA_state_id'],version='1.0.0',name=name,names={lang:name for lang in ['en','zh','ja','de']},aliases=[],source_designation=label,property_ids=[row['new_property_id']])
        for key in s['state']:s['state'][key]=unknown('Not established for selected DMA bar specimen;mechanical and DSC state metadata not transferred.')
        s['state']['product_form']=fact('Rectangular DMA bars,3×5×20mm,source dimension order retained','PDF p.4 section2.8 DMA paragraph','Physical bar form is distinct from tensile dog-bone and10mg DSC aliquot;axis assignment andactual machining tolerances unknown.',('state',))
        processing='Source formulation single-screw extruded at140°C into3mm strands and pelletized.'
        if label.startswith('R'):processing+=' Reactive-series DCP/acetone precursor preparation includes24h fume-hood drying then80°C vacuum drying12h before extrusion.'
        s['state']['processing']=fact(processing,'PDF p.3 section2.3','Exact post-extrusion DMA bar-forming route is not linked. No120°C hot-press disc history,Dynisco injection compounding or tensile geometry assigned. Reactive precursor drying is not DMA moisture equilibrium.',('state',))
        s['state']['temper_or_heat_treatment']=fact(program,'PDF p.4 section2.8 DMA paragraph','DMA test scan,not DSC second heating,processing/annealing schedule or complete thermal-history erasure.',('state',))
        s['state']['conditioning']=unknown('DMA-specific RH,storage,drying and moisture equilibrium unknown;reactive precursor preparation is not selected-bar conditioning.')
        for key in ['composition_or_purity','reinforcement']:
            s['state'][key]=deepcopy(old['state'][key])
            if s['state'][key]['status']=='reported':s['state'][key]['evidence']=[ev('PDF p.3 sections2.1–2.3,formulation '+label,('state',))]
        s['source_scope']='Existing '+label+' source formulation identity;separate physical DMA rectangular-bar state,not DSC aliquot or injection-molded tensile state. Tanδ-maximum Tg at1Hz/0.2%strain. GradeFZ91PM/FZ91PB,post-extrusion bar-forming route,cycle,conditioning,selected-scalar n/statistics andindependent specimens/batches unknown.'
        s['evidence']=[ev('PDF p.3 sections2.1–2.3',('state',)),ev(methodloc,('state',))]
        p=deepcopy(before.properties['refprop_abbasi2022_manure_phbv39_glass_transition_temperature'])
        p.update(id=row['new_property_id'],version='1.0.0',material_state_id=s['id'],source_id=SID,source_property_label=row['source_property_label'],reported_value=dict(kind='scalar',number=row['number'],value_text=row['value_text'],unit_code='degC',unit_text='°C'))
        p['basis_note']='Selected Table3 '+label+' source literal andprecision only. DMA tanδ-maximum criterion,not a DSC equivalent or a unique material constant. Common three DMA repeats retained separately;selected scalar aggregation,n and dispersion unknown.'
        p['conditions']={
            'temperature':fact(program,methodloc,'Scan settings,not ambient temperature or actual logged trace.'),
            'test_standard':unknown('No DMA standard named in inspected method;ASTM/ISO andmechanical standards not inferred.'),
            'test_method':fact(definition,methodloc,'Method-qualified catalogue coordinate only;no DSC/DMA comparison or conversion inferred.'),
            'direction':unknown('Bending fixture is known;material-axis assignment relative to loading direction andisotropy are not stated.'),
            'conditioning':deepcopy(s['state']['conditioning']),
            'loading_rate':fact('Oscillatory loading at1Hz with0.2%strain','PDF p.4 section2.8 DMA paragraph','Dynamic frequency andstrain amplitude;not a quasistatic crosshead rate,not the thermal scan rate.'),
            'additional_conditions':[
                dict(name='measurement_method_family',fact=fact('DMA',methodloc,'Not DSC or TGA.')),
                dict(name='Tg_extraction_criterion',fact=fact('tanδ maximum','PDF p.8 section3.4 paragraph following Table3','Not storage-modulus onset,loss-modulus maximum,DSC inflection or crystallization.')),
                dict(name='oscillation_frequency',fact=fact('1Hz','PDF p.4 section2.8 DMA paragraph','No frequency normalization or time-temperature superposition.')),
                dict(name='strain_amplitude',fact=fact('0.2%strain','PDF p.4 section2.8 DMA paragraph','Source does not specify peak,RMS or peak-to-peak convention;not elongation at break.')),
                dict(name='thermal_heating_rate',fact=fact('3°C/min','PDF p.4 section2.8 DMA paragraph','Not mechanical loading frequency or a DSC10°C/min ramp.')),
                dict(name='DMA_geometry_and_fixture',fact=fact('3×5×20mm bars;three-point bending;15mm span','PDF p.4 section2.8 DMA paragraph','Dimensions in source order;no axis mapping,clamp geometry or preload invented.')),
                dict(name='DMA_software',fact=fact('Pyrisv13.3','PDF p.4 section2.8 DMA paragraph','DMA analysis software statement only;not calibration certificate or raw-data reanalysis.')),
                dict(name='common_method_triplicate_measurements',fact=fact('DMA common method:three repeats,in triplicate','PDF p.4 section2.8 DMA paragraph','Method context confirmed;does not establish selected scalar n=3,a mean,three distinct bars orindependent production batches.')),
                dict(name='thermal_cycle',fact=unknown('DMA scan/cycle number andrepeat-scan averaging not stated.')),
                dict(name='DMA_atmosphere_and_preload',fact=unknown('DMA purge gas,flow andstatic preload not stated;TGA nitrogen andDSC conditions not transferred.'))
            ]}
        p['summary_statistic']='not_stated';p['uncertainty']=None;p['uncertainty_status']='not_reported_in_inspected_source'
        p['uncertainty_note']='Table3 gives scalar Tg literals without mean/SD/SE/CI definition. Common triplication is not converted to uncertainty orselected-scalar contributor count;unknown is not zero scatter.'
        p['sample_count']=dict(value=None,relation='not_reported',scope='Selected Table3 '+label+' Tg scalar contributors unknown;common DMA method triplication retained separately.',source_statement='DMA in triplicate in section2.8. Table3 does not identify mean-of-peaks,peak-of-mean-curve,representative curve orcontributing records. Independent specimen/batch count unknown.',evidence=[])
        p['method_definition']=dict(type='source_reported_conventional',definition=definition,extraction_window=None,evidence=[ev(methodloc,('method','classification'))])
        p['source_discrepancies']=[dict(description=d['description'],disposition=d['disposition'],evidence=[ev('PDF p.8 section3.4/Table3;p.9 section3.5 opening',('source_discrepancy',))]) for d in facts['source_discrepancies']]
        p['evidence']=[ev(loc,('reported_value','classification')),ev(methodloc,('method','condition'))]
        p['source_document']=dict(url=URL,revision='Official publisher PDF Polymers2025,17,194;retained2026-11-04.',inspected_on='2026-11-04',sha256=facts['PDF_sha256'],hash_status='recorded',hash_note=None,inspection_scope=scope,inspection_status='selected_content_inspected')
        p['verification']=dict(source_inspection_scope=scope,transcription_cross_check='completed',independent_scientific_review=False,raw_data_reanalysis=False)
        p['scope_note']='Source '+label+' Table3 DMA tanδ-maximum Tg='+row['number']+'°C at1Hz and0.2%strain,scan−50 to120°C at3°C/min. Source polarity/precision retained. Not DSC Tg,storage-modulus onset,loss-modulus maximum ormelting temperature. Common triplication only,selected n/summary/dispersion andindependent specimen/batch counts unknown. No automatic comparability,frequency/criterion conversion,curve digitization,structural mechanism,standard compliance,service limit,allowable,bound orengine input.'
        props.append(p);states.append(s)
    source=deepcopy(before.sources[SID]);source['claim_notes'].append('2026-11-04 Table3 source-qualified DMA tanδ-maximum Tg for nine existing B0/B10/B20/B30/B45/R10/R20/R30/R45 identities on separate rectangular-bar states;no R0. Keep1Hz/0.2%/3°Cmin,geometry,software andconfirmed common triplication withselected n/aggregation/dispersion unknown. Source section3.5 generalDSCTg wording is not selected-method evidence. No DSC/TGA/mechanical metadata transfer,method interchangeability orengineering use.')
    data=deepcopy(before.data);data['materials']['records'].extend(states);data['reference_properties']['records'].extend(props)
    data['sources']['records']=[source if s['id']==SID else s for s in data['sources']['records']]
    after=Database(data);assert len(after.properties)==5353 and len(after.states)==5236
    assert all(after.properties[k]==v for k,v in before.properties.items()) and all(after.states[k]==v for k,v in before.states.items())
    assert after.identities==before.identities and after.grades==before.grades and set(after.sources)==set(before.sources)
    assert all(after.sources[k]==v for k,v in before.sources.items() if k!=SID)
    restored=deepcopy(source);restored['claim_notes'].pop();assert restored==before.sources[SID]
    for name in ['materials','reference_properties','sources']:Draft202012Validator(read(ROOT/'schemas'/(name+'.schema.json')),format_checker=FormatChecker()).validate(data[name])
    selected=list(after.records(source=SID,quantity='glass_transition_temperature'))
    assert {r['property']['id']:r['property'] for r in selected}=={p['id']:p for p in props}
    assert len(list(after.records(quantity='glass_transition_temperature')))==15
    assert {r['property']['id']:r['property'] for r in before.records(quantity='melting_peak_temperature')}=={r['property']['id']:r['property'] for r in after.records(quantity='melting_peak_temperature')}
    dest.mkdir(parents=True);(dest/'native-tables').mkdir()
    for name in data:write(dest/'native-tables'/(name+'.json'),data[name])
    write(dest/'native-candidate-r1.json',dict(baseline_snapshot=BASE,stage='not_applied',materials=dict(identities=[],grades=[],records=states),reference_properties=dict(records=props),sources=dict(records=[source])))
    after.export(dest/'source-export',source=SID);_,exported=read_snapshot(dest/'source-export')
    assert exported=={r['property']['id']:r for r in after.records(source=SID)} and len(exported)==37
    for language in ['en','zh','ja','de']:
        with patch('materials_boundaries.catalog.read_catalog',side_effect=lambda name:data[name]):text=render_material_catalog({'schema_version':'1.0.0','records':props},'reference-properties',language)
        assert all(p['id'] in text and p['reported_value']['value_text'] in text for p in props)
        for token in ['tanδ','1Hz','0.2%','three repeats','unknown']:assert token in text
        (dest/('render-'+language+'.txt')).write_text(text,encoding='utf-8',newline='\n')
    validation=dict(baseline_snapshot=BASE,preview_snapshot=after.snapshot,properties=5353,states=5236,new_properties=9,new_states=9,new_identities_grades_sources=0,old5344_properties_complete_unchanged=True,old5227_states_complete_unchanged=True,source_append_only=True,schema_format='passed',new_Tg_query_objects=9,global_Tg=15,all11_melting_properties_unchanged=True,complete_source_export=37,four_languages='passed',selected_n=None,common_DMA_method_repeats=3,native_applied=False,installed=False,full_history_regression='not_run',pushed=False)
    write(dest/'VALIDATION_R1.json',validation)
    write(dest/'MAPPING_FACTS_R1.json',dict(property_records={p['id']:p for p in props},state_records={s['id']:s for s in states},source_record=source))
    for name in ['native-candidate-r1.json','MAPPING_FACTS_R1.json','VALIDATION_R1.json']:write(OUT/name,read(dest/name))
    print(json.dumps(validation))

if __name__=='__main__':main()
