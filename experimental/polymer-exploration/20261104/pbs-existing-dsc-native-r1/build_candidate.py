"""Build isolated DSC mappings for nine existing PBS source formulations."""
from copy import deepcopy
from pathlib import Path
import hashlib,json,sys
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT))
from materials_boundaries.database import Database,read_snapshot
from materials_boundaries.material_presentation import render_material_catalog
from jsonschema import Draft202012Validator,FormatChecker

AREA=ROOT/'experimental/polymer-exploration/20261104'
OUT=Path(__file__).resolve().parent
BASE='19079de9d0a0ad0808d77f9dc2c7681c88c1facc4c43e72ae7980eb64f35c491'
SID='ewurum_mcdonald_2025_pbs_lignin'
URL='https://mdpi-res.com/d_attachment/polymers/polymers-17-00194/article_deploy/polymers-17-00194.pdf'
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
    dest=Path(sys.argv[1]).resolve()
    assert not dest.exists() and not dest.is_relative_to(ROOT)
    proposal=AREA/'pbs-existing-dsc-source-r1'
    review=read(proposal/'INDEPENDENT_SOURCE_REVIEW_R1.json')
    assert review['decision']=='approved' and review['review_inputs_sha256']==sha(proposal/'REVIEW_INPUTS_R1.json')
    inputs=read(proposal/'REVIEW_INPUTS_R1.json')
    for key in ['repo_files_sha256','native_files_sha256','external_files_sha256']:
        for n,d in inputs[key].items():assert sha(Path(n) if key=='external_files_sha256' else ROOT/n)==d,n
    facts=read(proposal/'SOURCE_FACTS_R1.json')
    contexts={r['identity']['id']:r for r in read(proposal/'BASE_CONTEXT_R1.json')['existing_formulations']}
    before=Database();assert before.snapshot==BASE
    template=deepcopy(before.properties['refprop_abbasi2022_manure_phbv39_melting_peak_1_temperature'])
    program='DSC program30 to150°C at10°C/min,cool to30°C at−10°C/min,then second ramp to150°C at10°C/min;hold durations unknown.'
    phase='Second-heating context from section3.5/Figure4 caption,not a separately documented scan assignment for each Table4 cell;Figure4 plots only B0/B20/B45/R20/R45.'
    definition='Source Table4 Tm of extruded PBS formulation,Perkin Elmer DSC-7,nominal10mg. '+program+' '+phase+' Section3.5 describes a large main melting peak as Tm2;Table4 label remains Tm. Precise peak-picking/baseline algorithm unknown;not onset,Tg,Tc or TGA.'
    methodloc='PDF p.4 section2.8 DSC paragraph;p.9 section3.5 and Figure4'
    scopeloc='PDF p.3 sections2.1–2.3;p.4 section2.8;p.9 section3.5/Figure4;p.10 Table4;retained XML permissions. Selected content only,no SI/raw-trace/calibration-certificate/latest-notice inspection.'
    newprops=[];newstates=[]
    for row in facts['rows']:
        ctx=contexts[row['identity_id']];oldstate=ctx['existing_state'];label=row['source_label']
        assert before.states[oldstate['id']]==oldstate and before.identities[row['identity_id']]==ctx['identity']
        loc='PDF p.10 Table4 '+label+' row × Tm(°C) column'
        s=deepcopy(oldstate)
        s.update(id=row['new_state_id'],version='1.0.0',name=label+' extruded PBS formulation,DSC second-heating context',aliases=[],source_designation=label,
            names={lang:label+' extruded PBS formulation,DSC second-heating context' for lang in ['en','zh','ja','de']},property_ids=[row['new_property_id']])
        for k in s['state']:s['state'][k]=unknown('Not established for the selected extruded DSC specimen;mechanical-state facts are not transferred.')
        s['state']['product_form']=fact('Extruded formulation sample,nominal10mg for DSC',methodloc,'Actual per-run mass,pan,lid and aliquot geometry unknown;not injection-molded tensile or hot-pressed flexural specimen.',('state',))
        process='Source formulation single-screw extruded at140°C into3mm strands and pelletized.'
        if label.startswith('R'):process+=' DCP reactive-series preparation includes acetone/DCP treatment,24h fume-hood drying and80°C vacuum drying12h before extrusion.'
        s['state']['processing']=fact(process,'PDF p.3 section2.3','Pre-extrusion recipe only;selected DSC aliquot route beyond extruded material is not resolved. No post-extrusion hot pressing,additional compounding or injection molding assigned.',('state',))
        s['state']['temper_or_heat_treatment']=fact(program,methodloc,phase+' Not ambient conditioning or proof of complete history erasure.',('state',))
        s['state']['conditioning']=unknown('DSC-specific RH,moisture equilibrium,storage and pre-scan drying unknown. Reactive precursor drying is not DSC conditioning;no such schedule assigned to B-series.')
        for k in ['composition_or_purity','reinforcement']:
            s['state'][k]=deepcopy(oldstate['state'][k])
            if s['state'][k]['status']=='reported':s['state'][k]['evidence']=[ev('PDF p.3 sections2.1–2.3,source formulation '+label,('state',))]
        s['source_scope']='Existing '+label+' source formulation identity;separate extruded DSC state. '+phase+' BioPBS FZ91PM/FZ91PB unresolved;recipe additions do not establish final reacted composition or network topology. No mechanical geometry/conditioning,n or statistics transferred.'
        s['evidence']=[ev('PDF p.3 sections2.1–2.3',('state',)),ev(methodloc,('state',))]
        p=deepcopy(template)
        p.update(id=row['new_property_id'],version='1.0.0',material_state_id=s['id'],source_id=SID,source_property_label='Tm (°C), Table 4',
            reported_value=dict(kind='scalar',number=row['number'],value_text=row['value_text'],unit_code='degC',unit_text='°C'))
        p['basis_note']='Table4 '+label+' literal at source integer precision;central aggregation,selected n and numerical dispersion not stated. '+phase
        p['conditions']={
            'temperature':fact(program,methodloc,phase),
            'test_standard':unknown('No DSC-specific standard named in inspected method;mechanical ASTM standards not transferred.'),
            'test_method':fact(definition,methodloc,'Source main-peak context retained;not a certified generic melting point.'),
            'direction':unknown('Mechanical loading direction is not applicable;specimen isotropy is not inferred.','not_applicable'),
            'conditioning':deepcopy(s['state']['conditioning']),
            'loading_rate':unknown('Mechanical loading rate not applicable;thermal ramp recorded separately.','not_applicable'),
            'additional_conditions':[
                dict(name='thermal_heating_rate',fact=fact('10°C/min',methodloc)),
                dict(name='thermal_cooling_rate',fact=fact('−10°C/min to30°C',methodloc)),
                dict(name='thermal_peak_label',fact=fact('Tm,Table4',loc,'Main-peak Tm2 context appears in section3.5;column itself is Tm. No per-row Tm1 inferred.')),
                dict(name='scan_phase_context',fact=fact('Second heating,shared section3.5/Figure4 context',methodloc,phase)),
                dict(name='nominal_DSC_sample_mass',fact=fact('10mg',methodloc,'Nominal source method,not replicate count or actual weighing log.')),
                dict(name='purge_atmosphere_and_flow',fact=unknown('Not specified in DSC paragraph;TGA nitrogen30mL/min not transferred.')),
                dict(name='pan_and_lid',fact=unknown('DSC pan/lid geometry not specified.')),
                dict(name='calibration_and_software',fact=unknown('DSC calibration and software not specified;DMA/TGA statements not transferred.')),
                dict(name='thermal_holds',fact=unknown('No DSC dwell/hold durations stated.'))
            ]}
        p['summary_statistic']='not_stated';p['uncertainty']=None;p['uncertainty_status']='not_reported_in_inspected_source'
        p['uncertainty_note']='Table4 gives integer literals without defined central statistics or SD/SE/CI. DMA triplicate and mechanical mean/SD do not apply. Narrative/table range differences are not uncertainty;unknown is not zero scatter.'
        p['sample_count']=dict(value=None,relation='not_reported',scope='Selected Table4 '+label+' Tm cell;measurement,specimen and independent-batch counts unknown.',source_statement='DSC repeat count not stated;nearby triplicate statement belongs to DMA only.',evidence=[])
        p['method_definition']=dict(type='source_reported_conventional',definition=definition,extraction_window=None,evidence=[ev(methodloc,('method','classification'))])
        p['source_discrepancies']=[dict(description=d['description'],disposition=d['disposition'],evidence=[ev('PDF p.9 section3.5;p.10 Table4',('source_discrepancy',))]) for d in facts['discrepancies']]
        p['evidence']=[ev(loc,('reported_value','classification')),ev(methodloc,('method','condition'))]
        p['source_document']=dict(url=URL,revision='Official publisher PDF Polymers2025,17,194;retained 2026-11-04.',inspected_on='2026-11-04',sha256=facts['primary_pdf_sha256'],hash_status='recorded',hash_note=None,inspection_scope=scopeloc,inspection_status='selected_content_inspected')
        p['verification']=dict(source_inspection_scope=scopeloc,transcription_cross_check='completed',independent_scientific_review=False,raw_data_reanalysis=False)
        p['scope_note']='Source-qualified '+label+' Table4 Tm='+row['number']+'°C only. '+phase+' Precise algorithm,n,aggregation,dispersion,pan,gas,calibration,software and moisture/storage unknown. No DMA/TGA/mechanical metadata transfer,small-peak digitization,decimal reconstruction,service limit,allowable,universal bound,automatic conversion or engine input.'
        assert p['density_basis'] is None and p['evaluation_support']=='catalog_only' and not p['universal_bound'] and not p['engineering_allowable']
        newprops.append(p);newstates.append(s)
    source=deepcopy(before.sources[SID])
    source['claim_notes'].append('2026-11-04 source Table4 literal DSC Tm values for nine existing B0/B10/B20/B30/B45/R10/R20/R30/R45 formulation identities on separate extruded DSC states. Common second-heating context from section3.5/Figure4,not per-cell phase certification. Keep integer precision,source Tm label,narrative ranges and unknown n/statistics/conditioning/DSC atmosphere. No R0 identity mapping,DMA/TGA/mechanical metadata transfer,small-peak digitization or engineering/engine use.')
    data=deepcopy(before.data)
    data['materials']['records'].extend(newstates);data['reference_properties']['records'].extend(newprops)
    data['sources']['records']=[source if x['id']==SID else x for x in data['sources']['records']]
    after=Database(data)
    assert len(after.properties)==5344 and len(after.states)==5227
    assert all(after.properties[k]==v for k,v in before.properties.items())
    assert all(after.states[k]==v for k,v in before.states.items())
    assert after.identities==before.identities and after.grades==before.grades
    assert all(after.sources[k]==v for k,v in before.sources.items() if k!=SID)
    restored=deepcopy(source);restored['claim_notes'].pop();assert restored==before.sources[SID]
    for name in ['materials','reference_properties','sources']:
        Draft202012Validator(read(ROOT/'schemas'/(name+'.schema.json')),format_checker=FormatChecker()).validate(data[name])
    selected=list(after.records(source=SID,quantity='melting_peak_temperature'))
    assert {x['property']['id']:x['property'] for x in selected}=={p['id']:p for p in newprops}
    assert len({x['state']['id'] for x in selected})==9
    assert {x['property']['id']:x['property'] for x in before.records(quantity='glass_transition_temperature')}=={x['property']['id']:x['property'] for x in after.records(quantity='glass_transition_temperature')}
    dest.mkdir(parents=True);(dest/'native-tables').mkdir()
    for name in ['materials','reference_properties','sources']:write(dest/'native-tables'/(name+'.json'),data[name])
    candidate=dict(baseline_snapshot=BASE,stage='not_applied',materials=dict(identities=[],grades=[],records=newstates),reference_properties=dict(records=newprops),sources=dict(records=[source]))
    write(dest/'native-candidate-r1.json',candidate)
    export=dest/'source-export';after.export(export,source=SID);_,joined=read_snapshot(export)
    assert joined=={x['property']['id']:x for x in after.records(source=SID)}
    for language in ['en','zh','ja','de']:
        with patch('materials_boundaries.catalog.read_catalog',side_effect=lambda name:data[name]):
            rendered=render_material_catalog({'schema_version':'1.0.0','records':newprops},'reference-properties',language)
        assert all(p['reported_value']['value_text'] in rendered for p in newprops)
        (dest/('render-'+language+'.md')).write_text(rendered,encoding='utf-8')
    result=dict(before_snapshot=BASE,after_snapshot=after.snapshot,new_properties=9,new_states=9,new_identities=0,new_grades=0,new_sources=0,all_5335_old_properties_unchanged=True,all_5218_old_states_unchanged=True,source_export_records=len(joined),query_new_records=len(selected),four_language_rendered=True,unit_suites_run=False,applied=False,pushed=False)
    write(dest/'VALIDATION_R1.json',result)
    for name in ['native-candidate-r1.json','VALIDATION_R1.json']:write(OUT/name,read(dest/name))
    write(OUT/'MAPPING_FACTS_R1.json',dict(property_records={p['id']:p for p in newprops},state_records={s['id']:s for s in newstates},source_record=source))
    print(json.dumps(result))

if __name__=='__main__':main()
