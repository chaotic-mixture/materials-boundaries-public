"""Prepare nine density references for review without writing native tables."""
from pathlib import Path
from copy import deepcopy
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent
SOURCE=HERE.parent/'pbs-density-gel-source-screen-r2'
sys.path.insert(0,str(ROOT))
from materials_boundaries.database import Database
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(n,obj):
    with (HERE/n).open('x',encoding='utf-8',newline='\n') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
    entry=SOURCE/'REVIEW_INPUTS_R2.json';review=read(SOURCE/'INDEPENDENT_SOURCE_REVIEW_R2.json')
    assert review['decision']=='approved' and review['review_inputs_sha256']==sha(entry)
    frozen=read(entry)
    for field in ('repo_files_sha256','external_files_sha256','native_files_sha256'):
        for name,h in frozen[field].items():assert sha(Path(name) if field=='external_files_sha256' else ROOT/name)==h,name
    before=Database();assert before.snapshot=='9713cd8823556102b6d7548025dc03cb528c74c5395e7a15b6ea15969a105bcf'
    facts=read(SOURCE/'SOURCE_FACTS_R2.json');url=facts['source_url'];sid=facts['source_id']
    def ev(locator,*supports):return dict(source_id=sid,url=url,locator=locator,supports=list(supports))
    loc='Table1 formulation row x Density(g/cm3);Sections2.1-2.3 and3.2'
    def unknown(note):return dict(status='not_reported_in_inspected_source',text=None,evidence=[ev(loc,'condition')],notes=note)
    props=[];states=[]
    for fact in facts['rows']:
        label=fact['source_label'];key=label.lower()
        anchor=before.properties[f'refprop_ewurum2025_{key}_dsc_melting_temperature']
        state=deepcopy(before.states[anchor['material_state_id']])
        state.update(id=f'state_ewurum2025_{key}_reported_density',version='1.0.0',name=f'{label} source-reported formulation density context',names={lang:f'{label} source-reported formulation density context' for lang in ('en','zh','ja','de')},aliases=[],source_designation=label,property_ids=[])
        state['state']['product_form']=dict(status='reported',text='Source Table1 extruded formulation;actual density specimen form unspecified',evidence=[ev('Table1 caption;Section2.3','state')],notes='Not proof of pellet,strand,disc,DSC aliquot or injection-molded specimen geometry.')
        state['state']['temper_or_heat_treatment']=unknown('Density-specific post-extrusion thermal history unknown;no DSC program or hot-press background assigned.')
        state['state']['conditioning']=unknown('Density-specific conditioning and moisture history unknown;no precursor drying assigned.')
        state['state']['processing']['notes']='Common formulation extrusion background only;actual density aliquot route after extrusion unknown. No hot pressing,injection molding or DSC lineage asserted.'
        for field in ('porosity','orientation'):state['state'][field]=unknown('Not established for selected density specimen;no facts from other method contexts transferred.')
        state['source_scope']=f'Existing {label} formulation identity only. Table1 source-reported density method context,not a new identity or independent specimen/batch. Actual specimen shape,conditioning and processing linkage unknown. No lignin nitrogen-pycnometry method,hot-press conditions,DSC program or mechanical sample count transferred.'
        state['evidence']=[ev('Sections2.1-2.3;Table1 formulation row','state')]
        p=deepcopy(before.properties['refprop_ewurum2025_indulin_at_mass_density'])
        p.update(id=f'refprop_ewurum2025_{key}_reported_mass_density',version='1.0.0',material_state_id=state['id'],source_property_label='Density (g/cm3)')
        p['reported_value'].update(number=fact['density_value_text'],value_text=fact['density_value_text'],unit_text='g/cm3')
        for field in p['conditions']:p['conditions'][field]=[] if field=='additional_conditions' else unknown('Not established for selected formulation density;no laboratory defaults or cross-method conditions assigned.')
        for field in ('direction','loading_rate'):p['conditions'][field]=dict(status='not_applicable',text=None,evidence=[],notes='Mechanical loading coordinate not applicable to this scalar source-reported density reference.')
        p['density_basis']='not_stated';p['summary_statistic']='reported_value'
        p['basis_note']='Direct Table1 formulation density cell. Method and density basis unspecified for these formulations;the explicit nitrogen pycnometry method applies only to lignin. No supplier substitution,conversion or mixture calculation.'
        p['uncertainty_note']='No uncertainty or central aggregation specified for this density cell;missing is not zero.'
        p['sample_count']=dict(value=None,relation='not_reported',scope='Selected formulation density cell;no independent specimen or batch count established',source_statement='No density replicate count established.',evidence=[ev(loc,'condition')])
        p['method_definition']=dict(type='source_reported_conventional',definition='Source-reported Table1 density;measurement procedure unspecified for PBS formulations. This descriptor records reported density semantics,not certification of a conventional measurement method.',extraction_window=None,evidence=[ev(loc,'method','classification')])
        p['evidence']=[ev('Table1 '+label+' row x Density(g/cm3)','reported_value','classification'),ev('Sections2.2-2.3;Section3.2 formulation-density discussion','method','condition')]
        p['source_document']=dict(url=url,revision=None,inspected_on='2026-11-12',sha256=next(iter(frozen['external_files_sha256'].values())),hash_status='recorded',hash_note=None,inspection_scope='Main XML Sections2.1-2.4,3.2 and Table1;no new PDF visual inspection',inspection_status='selected_content_inspected')
        p['verification']=dict(source_inspection_scope=p['source_document']['inspection_scope'],transcription_cross_check='completed',independent_scientific_review=False,raw_data_reanalysis=False)
        p['scope_note']=state['source_scope']+' Density basis not_stated;not supplier PBS1.26 or lignin1.226g/cm3. Catalog-only reference,not engineering allowable,universal constant or automatic calculator input.'
        assert p['id'] not in before.properties and state['id'] not in before.states
        state['property_ids']=[p['id']];props.append(p);states.append(state)
    data=deepcopy(before.data);data['materials']['records'].extend(states);data['reference_properties']['records'].extend(props)
    after=Database(data)
    assert all(after.properties[k]==v for k,v in before.properties.items()) and all(after.states[k]==v for k,v in before.states.items())
    assert before.identities==after.identities and before.grades==after.grades and before.sources==after.sources
    assert len(after.properties)==5700 and len(after.states)==5407
    write('NEW_PROPERTIES_R1.json',props);write('NEW_STATES_R1.json',states)
    write('VALIDATION_R1.json',dict(baseline_snapshot=before.snapshot,candidate_snapshot=after.snapshot,properties=5700,states=5407,sources=134,new_properties=9,new_contexts=9,old5691properties_unchanged=True,old5398states_unchanged=True,identities_grades_sources_unchanged=True,native_applied=False,installation='not_run',tests='not_run_candidate_graph_validation_only'))
    print(json.dumps(dict(snapshot=after.snapshot,new_properties=9,new_contexts=9,native_applied=False)))
if __name__=='__main__':main()
