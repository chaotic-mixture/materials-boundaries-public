"""Prepare four source-qualified water-test contexts without native writes."""
from pathlib import Path
from copy import deepcopy
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
EXT=ROOT.parent/'open-database-evidence/polymer-pur-water-absorption-mapping-20261112-r2'
sys.path.insert(0,str(ROOT))
from materials_boundaries.database import Database,read_snapshot
from materials_boundaries.material_references import validate_material_catalog

def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')

def main():
    approved=HERE.parent/'pur-water-absorption-source-proposal-r1'
    implementation=HERE.parent/'water-absorption-implementation-r1'
    for folder,name,receipt in [(approved,'REVIEW_INPUTS_R1.json','INDEPENDENT_SOURCE_REVIEW_R1.json'),(implementation,'REVIEW_IMPLEMENTATION_INPUTS_R1.json','INDEPENDENT_IMPLEMENTATION_REVIEW_R1.json')]:
        entry=folder/name;review=read(folder/receipt)
        assert review['decision']=='approved' and review['review_inputs_sha256']==sha(entry)
        for group in ['repo_files_sha256','native_files_sha256','external_files_sha256']:
            for n,h in read(entry)[group].items():assert sha(Path(n) if group=='external_files_sha256' else ROOT/n)==h,n
    before=Database();assert len(before.properties)==5636 and len(before.states)==5369
    data=deepcopy(before.data);facts=read(approved/'SOURCE_FACTS_R1.json')['candidates'];states=[];props=[]
    source='ivdre_2024_lpo_rigid_pur';url='https://www.ebi.ac.uk/europepmc/webservices/rest/PMC11013755/fullTextXML'
    def ev(locator,*supports):return [dict(source_id=source,url=url,locator=locator,supports=list(supports))]
    method_locator='Section 2.8, XML sec2dot8-polymers-16-00942, water-absorption paragraph; Table10 polymers-16-00942-t010 water-absorption row'
    def known(text,notes):return dict(status='reported',text=text,evidence=ev(method_locator,'method','condition'),notes=notes)
    def unknown(notes):return dict(status='not_reported_in_inspected_source',text=None,evidence=ev(method_locator,'condition'),notes=notes)
    for row in facts:
        label=row['source_label'];key=label.lower().replace('-','');state=deepcopy(before.states[row['existing_density_state_id']]);p=deepcopy(before.properties[row['existing_density_property_id']])
        sid=f'state_ivdre2024_{key}_rigid_pur_water_immersion_4d';pid=f'refprop_ivdre2024_{key}_rigid_pur_water_absorption_volume_percentage'
        state.update(id=sid,version='1.0.0',property_ids=[pid],aliases=[],source_designation=label+', Table10 water absorption, four-day immersion')
        names=dict(en=label+' rigid PUR, four-day water immersion',zh=label+'硬质PUR，浸水四天',ja=label+'硬質PUR、4日間浸水',de=label+'-PUR-Hartschaum, vier Tage Wasserlagerung')
        state.update(name=names['en'],names=names,source_scope='Source-qualified '+label+' formulation, separate nominal water-test context. No assertion of specimen, batch or test-piece equivalence with density, thermal or compression measurements.')
        state['state']['product_form']=known('Rigid PUR water-test specimens, nominal dimensions 50 x 50 x 50 mm','Water-test specimen dimensions, not mold size or compression/DMA geometry.')
        state['state']['product_form']['evidence']=ev(method_locator,'state')
        state['state']['conditioning']=dict(status='reported',text='Cured for 24 h at room temperature before additional testing; water absorption tested after four days of water immersion',evidence=ev('Sections2.7 and2.8, optimized specimens preparation and water-absorption paragraphs','state'),notes='Curing is preparation; no humidity equilibrium, numeric room temperature, water temperature, pre-drying or surface-water removal is established.')
        state['state']['porosity']=dict(status='not_reported_in_inspected_source',text=None,evidence=[],notes='No porosity measurement assigned to the selected water-test pieces; closed-cell content of other characterization is not transferred.')
        state['state']['orientation']=dict(status='not_reported_in_inspected_source',text=None,evidence=ev(method_locator,'state'),notes='Water-test specimen orientation relative to foam rise and exposure direction is not stated; full/partial immersion details are unknown. Scalar absorption does not establish isotropy or make orientation inapplicable.')
        state['evidence']=ev('Table9 '+label+' formulation; Table10 '+label+' water-absorption row; Sections2.7 and2.8','state')
        table_locator=row['locator'];value_ev=ev(table_locator,'reported_value','classification','uncertainty')
        p.update(id=pid,version='1.0.0',material_state_id=sid,quantity='water_absorption_volume_percentage',quantity_dimension='dimensionless',source_property_label='Water absorption, V%',density_basis=None,summary_statistic='reported_value')
        p['reported_value']=dict(kind='scalar',number=row['reported_number'],value_text=row['reported_number'],unit_code='percent_water_absorption_volume',unit_text='V%')
        p['basis_note']='Table10 experimental source-reported water absorption in V%; exact denominator/formula and central aggregation unspecified. No density-based conversion, mass percentage, saturation, diffusion or permeability inference.'
        p['conditions']=dict(temperature=unknown('Water and test-environment temperatures not stated; curing room temperature and thermal-test temperatures are not transferred.'),test_standard=known('ISO 2896:2001','Author-reported standard only; full standard not inspected, no independent compliance certification.'),test_method=known('Water absorption after four-day immersion in water using nominal 50 x 50 x 50 mm specimens','No unreported standard subprocedure, calculation or correction imported.'),direction=unknown('Water-test specimen orientation relative to foam rise and exposure direction is not stated; immersion details unknown. Scalar absorption does not establish isotropy or make direction inapplicable.'),conditioning=known('Preparation:24 h cure at room temperature before additional testing; exposure:four days in water','No humidity equilibrium, pre-drying or numerical room temperature is established.'),loading_rate=dict(status='not_applicable',text=None,evidence=[],notes='Mechanical loading rate does not apply to selected water absorption.'))
        p['conditions']['conditioning']['evidence']=ev('Sections2.7 and2.8, optimized-specimen cure and water-absorption paragraphs','method','condition')
        definition=dict(basis='source_reported_volume_percentage',volume_reference_basis=unknown('V% is reported; explicit volume denominator or formula not provided in inspected text. Do not fill from standard title.'),immersion_exposure=known('Four days of immersion in water','No unreported full/partial immersion, weighting, saturation or equilibrium procedure inferred.'),fluid=known('Water','Composition, purity, treatment and temperature not stated.'),specimen_geometry=known('Nominal 50 x 50 x 50 mm','Actual specimen tolerances and per-piece dimensions unknown.'),preconditioning=unknown('Preparation cure24h at room temperature is stated; water-specific drying, initial moisture and equilibration protocol not stated.'),water_temperature=unknown('Water temperature is not stated; no transfer from cure, DMA or thermal-conductivity plate temperatures.'),surface_water_treatment=unknown('Surface-water removal, blotting and weighing delay not stated; no procedure imported from ISO title.'),evidence=ev(method_locator,'method','condition'),notes='Source-limited volumetric absorption result after four-day exposure. Unknown basis and procedures remain explicit; not converted or certified for service.')
        p['water_absorption_definition']=definition
        p['uncertainty']=dict(type='reported_plus_minus_unspecified',value_text=row['reported_absolute_amplitude'],number=row['reported_absolute_amplitude'],unit_text='V%',unit_code='percent_water_absorption_volume',scope='Printed absolute plus/minus amplitude on source V% scale; not identified as SD, SE, CI, tolerance or range. Central value not assumed mean.',coverage_factor=None,confidence_level=None,evidence=deepcopy(value_ev))
        p.update(uncertainty_status='reported_plus_minus_unspecified',uncertainty_note='Preserve printed absolute amplitude; meaning and aggregation unspecified. Do not divide by center or convert to relative percent.')
        p['sample_count']=dict(value=None,relation='not_reported',source_statement='No unambiguous water-absorption-specific count in the inspected sections; MRSM three cups, six compression cylinders and TGA parallel samples have separate scopes.',scope='Selected '+label+' Table10 water-absorption cell only.',evidence=ev('Sections2.7 and2.8; Table10 '+label+' water absorption','sample_count'))
        p['method_definition']=dict(type='source_reported_conventional',definition='Source-reported four-day water-immersion absorption, nominal 50 x 50 x 50 mm specimen, citing ISO2896:2001; formula, denominator and procedural details unknown.',extraction_window=None,evidence=ev(method_locator,'method','condition','classification'))
        p['evidence']=value_ev+ev(method_locator,'method','condition','classification')
        scope='Retained CC-BY4.0 XML Table10 and Sections2.7–2.8 inspected for water-absorption values, nominal method, identity and statistics scope; no new PDF, raw reanalysis, full ISO procedure or comprehensive latest-notice audit.'
        p['source_document'].update(inspected_on='2026-11-12',inspection_scope=scope,revision='Retained source XML; formal revision and latest-notice completeness not verified.')
        p['verification']['source_inspection_scope']=scope
        p['scope_note']='Only source '+label+' existing formulation under a distinct four-day water-test context. V% is not mass uptake or saturation. Unknown volume reference, n, center statistic, plus/minus meaning and water procedures remain unknown. No use suitability or independent sample/batch certification.'
        states.append(state);props.append(p)
    oldsource=before.sources[source];newsource=deepcopy(oldsource)
    newsource['claim_notes'].append('Selected Table10 water absorption for existing LPO-1/LPO-2/SPO-2/SPO-3: four-day water immersion, nominal50x50x50mm, author-citedISO2896:2001. V% and absolute plus/minus transcribed; volume denominator, center statistic, n, amplitude meaning, water temperature/purity and pretreatment unknown. Separate water-test contexts; no mass conversion or standard certification. Mapping/admission require independent review.')
    data['materials']['records'].extend(states);data['reference_properties']['records'].extend(props)
    data['sources']['records']=[newsource if x['id']==source else x for x in data['sources']['records']]
    validate_material_catalog(*(data[n] for n in ['materials','reference_properties','sources']));after=Database(data)
    assert all(after.properties[k]==v for k,v in before.properties.items()) and all(after.states[k]==v for k,v in before.states.items())
    assert after.identities==before.identities and after.grades==before.grades
    EXT.mkdir(exist_ok=False);exports=[]
    for name,filters,count in [('water-four',dict(quantity='water_absorption_volume_percentage'),4),('source-fortyfour',dict(source=source),44),('source-density-four',dict(source=source,quantity='mass_density'),4)]:
        records=list(after.records(**filters));assert len(records)==count
        if not (EXT/name).exists():after.export(EXT/name,**filters)
        recovered=read_snapshot(EXT/name)[1];assert [recovered[x['property']['id']] for x in records]==records
        exports.append(dict(name=name,records=count,complete_recovery=True))
    write(HERE/'NEW_STATES_R1.json',states);write(HERE/'NEW_PROPERTIES_R1.json',props);write(HERE/'SOURCE_UPDATE_R1.json',dict(before=oldsource,after=newsource))
    write(HERE/'VALIDATION_R1.json',dict(snapshot=after.snapshot,properties=len(after.properties),states=len(after.states),new_properties=4,new_states=4,new_identities=0,new_sources=0,updated_sources=1,old5636properties_unchanged=True,old5369states_unchanged=True,scientific_graph='passed',exports=exports,native_written=False,installed=False))
    print(json.dumps(dict(snapshot=after.snapshot,properties=len(after.properties),states=len(after.states),native_written=False)))
if __name__=='__main__':main()
