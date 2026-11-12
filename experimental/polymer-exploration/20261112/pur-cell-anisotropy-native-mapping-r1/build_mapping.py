"""Review-only morphology mapping, gated by source and implementation approvals."""
from pathlib import Path
from copy import deepcopy
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from materials_boundaries.database import Database,read_snapshot
from materials_boundaries.material_references import validate_material_catalog
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(n,v):
    with (HERE/n).open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
    source_folder=HERE.parent/'pur-cell-anisotropy-source-proposal-r1';impl=HERE.parent/'cell-anisotropy-implementation-r2'
    for folder,entry,receipt in [(source_folder,'REVIEW_INPUTS_R1.json','INDEPENDENT_SOURCE_REVIEW_R1.json'),(impl,'REVIEW_IMPLEMENTATION_INPUTS_R2.json','INDEPENDENT_IMPLEMENTATION_REVIEW_R2.json')]:
        r=read(folder/receipt);assert r['decision']=='approved' and r['review_inputs_sha256']==sha(folder/entry)
        for group in ['repo_files_sha256','external_files_sha256','native_files_sha256']:
            for n,h in read(folder/entry)[group].items():assert sha(Path(n) if group=='external_files_sha256' else ROOT/n)==h,n
    db=Database();assert db.snapshot=='20a936c91e6dcdc4e81ef7ecd3bcaf3483a3e5829484860576261ba71168d074'
    source='ivdre_2024_lpo_rigid_pur';url='https://www.ebi.ac.uk/europepmc/webservices/rest/PMC11013755/fullTextXML'
    method='Section2.8 morphology paragraph, XML sec2dot8-polymers-16-00942; Table10 Geometrical anisotropy'
    def ev(loc,*roles):return [dict(source_id=source,url=url,locator=loc,supports=list(roles))]
    def unknown(note,role='condition'):return dict(status='not_reported_in_inspected_source',text=None,evidence=ev(method,role),notes=note)
    def known(text,note):return dict(status='reported',text=text,evidence=ev(method,'method','condition'),notes=note)
    scope='Independent microscopy morphology context of source formulation; no physical specimen,batch or location equivalence with density,closed-cell,water,mechanical or thermal tests. Directional mean cell-size ratio only,not mechanical or full3D anisotropy; ratio1 does not certify material isotropy.'
    states=[];props=[]
    for row in read(source_folder/'SOURCE_FACTS_R1.json')['candidates']:
        label=row['source_label'];key=label.lower().replace('-','');state=deepcopy(db.states[row['existing_state_id']]);assert state['identity_id']==row['identity_id']
        sid=f'state_ivdre2024_{key}_cell_microscopy';pid=f'refprop_ivdre2024_{key}_cell_geometric_anisotropy'
        names=dict(en=label+' rigid PUR, cell microscopy context',zh=label+'硬质PUR，胞孔显微形貌上下文',ja=label+'硬質PUR、気泡顕微鏡形態観察',de=label+'-PUR-Hartschaum, Zellmikroskopie-Kontext')
        state.update(id=sid,version='1.0.0',name=names['en'],names=names,aliases=[],source_designation=label+' Table10 Geometrical anisotropy / Section2.8 microscopy',property_ids=[pid],source_scope=scope,evidence=ev('Table9 '+label+' formulation;'+method,'state'))
        for field in state['state']:
            if field not in ['composition_or_purity','processing']:state['state'][field]=unknown('Microscopy-specific '+field+' not established; other-method specimens and conditions not transferred.','state')
        state['state']['product_form']=dict(status='reported',text='Thin razor-cut foam sections parallel and perpendicular to foam-rise direction for optical microscopy',evidence=ev(method,'state'),notes='Section thickness,position,field selection and physical relationship to other test pieces unknown.')
        state['state']['orientation']=dict(status='reported',text='Sections parallel and perpendicular to foam-rise direction; ratio numerator parallel mean diameter,denominator perpendicular mean size',evidence=ev(method,'state'),notes='No full3D or mechanical anisotropy inference; no shared raw-cell population established.')
        state['state']['conditioning']=unknown('Microscopy-specific storage,drying,RH and equilibration unknown; common24h cure is preparation background,not method equilibrium.','state')
        p=deepcopy(db.properties[f'refprop_ivdre2024_{key}_rigid_pur_mass_density'])
        p.update(id=pid,version='1.0.0',material_state_id=sid,quantity='foam_cell_geometric_anisotropy_ratio',quantity_dimension='dimensionless',source_property_label='Geometrical anisotropy',reported_value=dict(kind='scalar',value_text=row['number'],number=row['number'],unit_text='ratio',unit_code='ratio_foam_cell_geometric_anisotropy'),density_basis=None,summary_statistic='reported_value',uncertainty=None,uncertainty_status='not_reported_in_inspected_source',uncertainty_note='No amplitude printed in selected source cell; no uncertainty inferred from assumed size distribution.',basis_note='Source prints no unit; dedicated dimensionless ratio role follows explicitly stated directional quotient,without scaling or reciprocal conversion.')
        p['conditions']={name:unknown('Microscopy-specific '+name+' unspecified; no apparatus or standard defaults.') for name in ['temperature','conditioning','loading_rate']}
        p['conditions'].update(test_standard=known('ASTM D3576,author citation','No edition inferred from reference date; full standard not inspected and compliance not certified.'),test_method=known('Diamond MCXMP500 optical microscope10x; ImageJ1.54d; directional average cell dimensions and geometric ratio','Author microscopy-based conventional reduction,not an instrument direct ratio reading or evaluator recomputation.'),direction=known('Numerator parallel to foam rise; denominator perpendicular to foam rise','Direction pertains to cell-size measures,not mechanical loading.'),additional_conditions=[])
        p['cell_anisotropy_definition']=dict(basis='source_reported_ratio_of_directional_mean_cell_sizes',numerator_direction_and_measure=known('Average cell diameter parallel to foaming direction','Exact diameter estimator,raw measurements and sampling weights not given.'),denominator_direction_and_measure=known('Average cell size perpendicular to foaming direction','Preserve source wording; no reciprocal conversion,exact size estimator or raw dimension inferred.'),imaging_and_analysis=known('Diamond MCXMP500 light microscopy10x and ImageJ1.54d; author ASTM D3576 citation','Image calibration,segmentation and software processing details not specified.'),sectioning_and_sampling=known('Thin slices cut using razor blade parallel and perpendicular to foam-rise direction','Thickness,location,field count,specimen count and selection protocol unknown.'),averaging_and_ratio_reduction=known('Divide parallel average cell diameter by perpendicular average cell size','Not mean of per-cell ratios; weighting,per-specimen pooling,rounding and reduction implementation unknown. Author assumed normal distribution and no discernible spatial mean difference; assumptions not independently verified.'),cell_selection_and_count=unknown('Cell,field,section,specimen and independent-batch counts not supplied; no count transferred from other methods.'),preconditioning=unknown('Microscopy-specific drying,storage and RH/equilibrium unknown; common preparation cure is not microscopy equilibration.'),evidence=ev(method,'method','condition'),notes=scope)
        p['sample_count']=dict(value=None,relation='not_reported',source_statement='No unambiguous cell,field,section,specimen or independent-batch n for selected morphology result.',scope=label+' Table10 geometric ratio; directional means do not establish cross-specimen estimator or n.',evidence=ev(method,'sample_count'))
        p['method_definition']=dict(type='source_reported_conventional',definition='Source-calculated quotient of directional mean cell dimensions from optical microscopy/ImageJ; raw dimensions and reduction detail unknown.',extraction_window=None,evidence=ev(method,'method','condition','classification'))
        p['evidence']=ev(row['source_locator'],'reported_value','classification')+ev(method,'method','condition','classification')
        inspection='Retained primary XML selected Table10 cells and Section2.8 morphology paragraph inspected. No new PDF visual,raw images,full standard,latest-notice completeness or scientific validity certification.'
        p['source_document'].update(inspected_on='2026-11-12',inspection_scope=inspection,revision='Retained primary XML;formal revision and latest notices not independently verified.')
        p['verification']['source_inspection_scope']=inspection;p['scope_note']=scope+' n,uncertainty,center estimator and detailed averaging unknown. Author normality/spatial-uniformity assumptions not validated.'
        states.append(state);props.append(p)
    data=deepcopy(db.data);data['materials']['records'].extend(states);data['reference_properties']['records'].extend(props)
    validate_material_catalog(*(data[n] for n in ['materials','reference_properties','sources']));after=Database(data)
    assert after.identities==db.identities and after.grades==db.grades and after.sources==db.sources
    assert all(after.properties[k]==v for k,v in db.properties.items()) and all(after.states[k]==v for k,v in db.states.items())
    ext=ROOT.parent/'open-database-evidence/polymer-pur-cell-anisotropy-mapping-20261112-r1';ext.mkdir(exist_ok=False)
    groups=[]
    for name,filters,count in [('morphology-four',dict(quantity='foam_cell_geometric_anisotropy_ratio'),4),('source-sixtyeight',dict(source=source),68)]:
        rows=list(after.records(**filters));assert len(rows)==count;after.export(ext/name,**filters);assert read_snapshot(ext/name)[1]=={r['record_id']:r for r in rows};groups.append(dict(name=name,records=count,full_export_exact=True))
    write('NEW_STATES_R1.json',states);write('NEW_PROPERTIES_R1.json',props);write('VALIDATION_R1.json',dict(snapshot=after.snapshot,properties=len(after.properties),states=len(after.states),sources=len(after.sources),new_properties=4,new_contexts=4,new_identities=0,new_sources=0,old_objects_preserved=True,exports=groups,native_changed=False,installed=False))
    print(json.dumps(dict(snapshot=after.snapshot,properties=len(after.properties),states=len(after.states),native_changed=False)))
if __name__=='__main__':main()
