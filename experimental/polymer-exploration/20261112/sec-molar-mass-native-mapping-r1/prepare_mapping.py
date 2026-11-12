"""Map inspected reproduced SEC facts only after implementation approval."""
from copy import deepcopy
import hashlib,json,sys,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))


def main():
    load=lambda p:json.loads(p.read_text('utf-8'))
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    impl=HERE.parent/'sec-molar-mass-implementation-r2'
    entry=impl/'REVIEW_IMPLEMENTATION_INPUTS_R2.json'
    receipt=load(impl/'INDEPENDENT_IMPLEMENTATION_REVIEW_R2.json')
    assert receipt['decision']=='approved' and receipt['review_inputs_sha256']==sha(entry)
    for section in ('repo_files_sha256','external_files_sha256','native_files_sha256'):
        for name,h in load(entry)[section].items():
            p=Path(name) if section=='external_files_sha256' else ROOT/name
            assert sha(p)==h,name
    source_stage=HERE.parent/'phbv39-sec-molar-mass-source-screen-r1'
    facts=load(source_stage/'SOURCE_FACTS_R1.json')
    raw=ROOT.parent/'open-database-evidence/polymer-property-source-rechecks-20261103/phbv/article-r1.xml'
    tree=ET.parse(raw).getroot()
    table=next(t for t in tree.iter('table-wrap') if t.get('id')==facts['table_id'])
    row=next([''.join(c.itertext()).strip() for c in r] for r in table.iter('tr')
             if len(r) and ''.join(r[0].itertext()).strip()=='PHBV-39')
    assert row==facts['raw_selected_row']==['PHBV-39','6.96 ± 0.38','6.45 ± 0.32','1.08 ± 0.08']
    from materials_boundaries._sec_molar_mass_contract import MOMENTS,DISPERSITY,MOMENT_UNITS,RATIO_UNIT,MOMENT_METHOD,RATIO_METHOD,PROFILE,FACT_FIELDS,VERIFICATIONS
    from materials_boundaries.material_references import validate_material_catalog
    from materials_boundaries.database import Database
    materials=load(ROOT/'materials_boundaries/data/materials.json')
    properties=load(ROOT/'materials_boundaries/data/reference_properties.json')
    sources=load(ROOT/'materials_boundaries/data/sources.json')
    template=next(p for p in properties['records'] if p['id']=='refprop_abbasi2022_manure_phbv39_ftir_fitted_carbonyl_area_ratio')
    state=deepcopy(next(s for s in materials['records'] if s['id']==template['material_state_id']))
    source=template['source_id'];url=template['source_document']['url']
    def ev(*roles,locator='Section3.2/Table2 PHBV-39;reference6 Guho2020'):
        return [dict(source_id=source,url=url,locator=locator,supports=list(roles))]
    def unknown(note,locator='Section3.2/Table2 reproduced PHBV-39;reference6'):
        return dict(status='not_verified',text=None,evidence=ev('condition',locator=locator),notes=note)
    def reported(text,note,locator='Section2.2.3 SEC method reported in2022'):
        return dict(status='reported',text=text,evidence=ev('method','condition',locator=locator),notes=note)
    state_id='state_abbasi2022_manure_phbv39_sec_reproduced_context'
    new_ids=['refprop_abbasi2022_manure_phbv39_'+q for q in (*MOMENTS,DISPERSITY)]
    scope=('Existing source-qualified PHBV-39 operational-day identity;2022 reproduces Guho2020 SEC results. '
           'One literature method context,not a new material,independent physical specimen or new2022 experiment. '
           'Original2020 value precision,sample/cell mapping,protocol and license remain unverified;no automatic original-source merge. '
           'No DSC,FTIR,mechanical or rheology specimen conditions or composition assays transferred.')
    state.update(id=state_id,name='PHBV-39 reproduced SEC molar-mass context',
                 names=dict(en='PHBV-39 reproduced SEC molar-mass context',zh='PHBV-39 转载SEC摩尔质量方法语境',ja='PHBV-39 転載SECモル質量の方法文脈',de='PHBV-39 Methodenbezug übernommener SEC-Molmassen'),
                 source_scope=scope,property_ids=new_ids,evidence=ev('state'))
    for name in state['state']:
        state['state'][name]=unknown('Actual original SEC aliquot detail unresolved;2022 other-method facts and assays are not transferred.')
    state['state']['product_form']=dict(status='reported',text='Source Table2 purified PHBV-39 material label',
        evidence=ev('state',locator='Table2 caption and PHBV-39 row;Section2.2.1 operational-day sample coding'),
        notes='2022 source material context only;39 is operationalday,not39%HV. No confirmed original SEC aliquot,geometry or actual2020 purification history.')
    state['state']['composition_or_purity']['notes']='2022 Table1 assays belong to source identity context;not verified for the original2020 SEC aliquot,so numerical purity/HV values are not transferred.'
    new=[]
    for q,symbol,number,sd,pid in zip((*MOMENTS,DISPERSITY),('Mw','Mn','PDI'),('6.96','6.45','1.08'),('0.38','0.32','0.08'),new_ids):
        ratio=q==DISPERSITY;p=deepcopy(template)
        unit,text=(RATIO_UNIT,'ratio') if ratio else (MOMENT_UNITS[2],'×10⁵ g·mol⁻¹')
        cell_locator='Table2 PHBV-39 row x '+symbol+' column'
        p.pop('derivation',None)
        p.update(id=pid,material_state_id=state_id,quantity=q,quantity_dimension='dimensionless' if ratio else 'mass_per_amount',
                 source_property_label=symbol,reported_value=dict(kind='scalar',number=number,value_text=number,unit_code=unit,unit_text=text),
                 evidence_kind='published_measurement_derived_reference' if ratio else 'published_experimental_reference',
                 determination_basis='source_reports_calculation' if ratio else 'source_reports_measurement',summary_statistic='reported_mean',
                 basis_note='2022 Table2 explicitly reports a reproduced mean±SD from Guho2020. Molecular-distribution moment weighting is not replicate averaging;not a new2022 experiment. No conversion,division or error propagation.',
                 source_discrepancies=[],scope_note=scope)
        p['conditions']={name:([] if name=='additional_conditions' else unknown('Actual original SEC condition not verified. Section3.2 calls results SEC-MALS;the method family is retained in the quantity/method definition,not used to transfer2022 detailed protocol.')) for name in template['conditions']}
        p['method_definition']=dict(type=RATIO_METHOD if ratio else MOMENT_METHOD,
            definition='Source reports Guho2020 SEC-MALS molar-mass results in2022 Table2;source PDI is defined as Mw/Mn,not recomputed from printed means. Original detailed protocol equivalence unknown.',
            extraction_window=None,evidence=ev('method','classification',locator='Sections2.2.3/3.2;Table2 caption,footnote a and reference6'))
        p['uncertainty']=dict(type='reported_standard_deviation',number=sd,value_text=sd,unit_code=unit,unit_text=text,
            scope='Source2022 Table2 selected cell SD in same scaled unit as center;not molecular-distribution width,confidence interval or certified bound.',
            confidence_level=None,coverage_factor=None,evidence=ev('uncertainty',locator=cell_locator+';Table2 footnote b mean±SD and rounding rule'))
        p['uncertainty_status']='reported_standard_deviation'
        p['uncertainty_note']='Table2 itself explicitly reports mean±SD and upward SD rounding to mean precision where needed. Preserve center/SD tokens and scale;original2020 precision and independent n unverified. Do not recompute PDI or propagate moment SDs.'
        p['sample_count']=dict(value=None,relation='not_reported',scope='Selected reproduced SEC scalar;independent specimens,batches and exact n unknown',
            source_statement='Table2 reports mean±SD without per-cell independent n. Mw/Mn distribution moments,2mg/mL solution concentration andPDI are not replicate counts.',evidence=ev('condition',locator='Section2.2.3;Table2 footnotes a/b'))
        p['evidence']=ev('reported_value',locator=cell_locator)+ev('summary_statistic','uncertainty',locator=cell_locator+';Table2 footnote b')+ev('method','classification')
        inspected='MainXML Sections2.2.1/2.2.3/3.2,Table2 PHBV-39 and ownfootnotes,reference6;2020 original fulltext not inspected,no newPDF or chromatogram digitization'
        p['source_document'].update(inspection_scope=inspected)
        p['verification'].update(source_inspection_scope=inspected)
        origin=dict(status='explicitly_reproduced_from_cited_work',original_reference=dict(
            doi='10.1016/j.biteb.2020.100588',title=facts['inheritance']['original_reference']['title'],year=2020,
            evidence=ev('classification',locator='Section3.2/Table2 heading;reference6 full citation'),
            notes='Explicit known inherited origin;citation is not a verified registered original source or original license claim.'),
            original_result=dict(status='not_verified',**{name:None for name in ('original_source_id','document_url','sha256','table_id','row_key','column_key')},
                evidence=ev('condition'),notes='Original2020 fulltext/result address not independently inspected;do not invent originalsourceID,hash,row orsample match.'),
            verification={name:unknown('Original2020 '+name+' unverified;2022 reproduction supports selected transcribed facts only.') for name in VERIFICATIONS},
            evidence=ev('classification'),notes='Known Guho2020 inheritance retained;not new2022 independent measurement. Original exact sample/cell and method/rights remain unverified;any second publication representation is held pending dedup adjudication.')
        common={name:unknown('Not established for the method reported in inspected2022 SEC text.',locator='Section2.2.3 SEC method') for name in FACT_FIELDS}
        common['sec_column_and_geometry_source_notation']=reported('Jordi DVB linear mixed-bed column;source geometry7.8mm ×300mm².','Original notation preserved;dimensional interpretation unresolved,not repaired toID/length orarea.')
        common['sample_solution_preparation_and_concentration']=reported('2022 SEC method reports PHBV solution2mg/mL.','Concentration is not sample mass or n;original2020 solution preparation,equilibration and protocol equivalence unverified.')
        common['eluent_flow_and_temperature']=reported('2022 SEC method reportsCHCl3 eluent,0.5mL/min and30°C.','Not assigned as actual original2020 per-cell conditions without verified equivalence.')
        common['detector_types_pairing_and_optical_configuration']=reported('Waters2414 RI detector and PostNovaPN3609 MALS detector658nm in reported2022 method.','Actual original detector pairing,normalization,dn/dc and optical constants unresolved;MALS name does not certify absolute accuracy.')
        common['calibrants_and_calibration_pathway']=reported('2022 system calibrated using narrow polystyrene standard,source Mw105,268g/mol.','Calibrant is not the PHBV sample;actual original calibration and absolute/relative reduction path remain unknown.')
        common['chromatogram_integration_and_moment_reduction']=reported('2022 SEC data analyzed with NovaSECv1.5.0.','Chromatogram integration bounds,baseline,moment reduction settings and original2020 software/protocol equivalence unverified.')
        common['sample_conditioning_storage_and_history']=reported('Section2.2.1 describes common PHBV extraction/purification ending in vacuum drying.','Only2022 preparation background;not verified actual SEC aliquot conditioning,duration,moisture orstorage history.',locator='Section2.2.1 common extraction/purification')
        common['replication_and_statistics']=reported('Table2 footnote b reports mean±standard deviation,with SD rounded upward to mean precision where needed.','Selected displayed2022 statistics retained;independent n,batches,ratio/mean ordering and original2020 reporting precision unknown.',locator='Table2 footnotes a/b')
        definition=dict(source_result_cell=dict(table_id='polymers-14-04140-t002',row_key='PHBV-39',column_key=symbol,
            evidence=ev('reported_value','classification',locator=cell_locator),notes='Stable inspected2022 result cell;corrections of units,values,method orstatistics revise it.'),
            origin=origin,reported_common_context=common,
            actual_original_result_context={name:unknown('Original2020 detailed protocol not independently verified;2022 common method cannot be copied as actual original condition.') for name in FACT_FIELDS},
            measurement_basis=dict(status='not_verified',text=None,evidence=ev('condition'),notes='Neither MALS name nor polystyrene calibration independently establishes relative/absolute reduction or accuracy.'),
            evidence=ev('method','classification'),notes='Inspected2022 reproduced numerical fact with explicit Guho2020 attribution;preserve source scale/statistics. Primary2020 identity,actual protocol,raw data and rights not certified;not an additional experiment.')
        p['sec_definition']=definition
        if ratio:
            p['derivation']=dict(schema_version='1.0.0',profile_id=PROFILE,profile_version='1.0.0',executor='source_reported_only',
                formula_family='source_weight_over_number_average_molar_mass',numerator_role=MOMENTS[0],denominator_role=MOMENTS[1],
                reported_formula=reported('Source Table2 footnote a defines PDI=Mw/Mn.','Reported meanPDI not assumed equal ratio of printed meanMw andmeanMn;no actual input pairing or averaging order inferred.',locator='Section2.2.3;Table2 footnote a PDI definition'),
                evidence=ev('method','classification',locator='Section2.2.3;Table2 footnote a'),notes='Only source-reported PDI1.08±0.08;do not recompute ratio,propagate SDs or infer actual paired moments.')
        new.append(p)
    candidate_materials=deepcopy(materials);candidate_properties=deepcopy(properties)
    candidate_materials['records'].append(state);candidate_properties['records'].extend(new)
    validate_material_catalog(candidate_materials,candidate_properties,sources)
    db=Database(dict(materials=candidate_materials,reference_properties=candidate_properties,sources=sources))
    def write(path,value):
        with path.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
    write(HERE/'NEW_STATES_R1.json',[state]);write(HERE/'NEW_PROPERTIES_R1.json',new)
    write(HERE/'VALIDATION_R1.json',dict(candidate_snapshot=db.snapshot,candidate_graph_valid=True,properties=len(db.properties),states=len(db.states),sources=len(db.sources),new_properties=3,new_contexts=1,new_identities=0,new_sources=0,native_applied=False,scope='One complete candidate graph;not installation or independent admission'))
    print(json.dumps(dict(properties=len(db.properties),states=len(db.states),sources=len(db.sources),snapshot=db.snapshot)),flush=True)


if __name__=='__main__':main()
