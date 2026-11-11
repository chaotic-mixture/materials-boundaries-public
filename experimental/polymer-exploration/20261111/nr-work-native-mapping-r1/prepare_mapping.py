"""Build unapplied exact NR work candidate after implementation approval."""
from pathlib import Path
from copy import deepcopy
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
IMPL=HERE.parent/'nr-work-contract-prototype-r1'
SOURCE=ROOT/'experimental/polymer-exploration/20261104/nr-work-to-break-source-contract-r1'
sys.path.insert(0,str(ROOT))
from materials_boundaries.database import Database,read_snapshot
from materials_boundaries.material_references import validate_material_catalog
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(name,obj):
    with (HERE/name).open('x',encoding='utf-8',newline='\n') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
    entry=IMPL/'REVIEW_IMPLEMENTATION_INPUTS_R1.json';review=read(IMPL/'INDEPENDENT_IMPLEMENTATION_REVIEW_R1.json')
    assert review['decision']=='approved' and review['review_inputs_sha256']==sha(entry)
    assert all(sha(ROOT/n)==h for n,h in read(entry)['repo_files_sha256'].items())
    before=Database();data=deepcopy(before.data)
    parent=before.states['state_smr10_bianchi2025_nr'];state=deepcopy(parent)
    pid='refprop_smr10_bianchi2025_nr_volumetric_tensile_work_to_break'
    assert pid not in before.properties
    state['property_ids'].append(pid);state['version']='1.0.4'
    assert parent['version']=='1.0.3'
    state['source_scope']+=' Additional source-reported volumetric tensile work uses the same quasi-static context,mean/SD and5reported specimens;reference volume and stress/strain conventions remain unknown. Density n3 and unspecified dispersion remain property-specific.'
    p=deepcopy(before.properties['refprop_smr10_bianchi2025_nr_finite_strain_tensile_modulus'])
    sid=p['source_id'];url='https://mdpi-res.com/d_attachment/molecules/molecules-30-03035/article_deploy/molecules-30-03035.pdf'
    def evidence(locator,*tags):return dict(source_id=sid,url=url,locator=locator,supports=list(tags))
    p.update(id=pid,version='1.0.0',quantity='volumetric_tensile_work_to_break',quantity_dimension='energy_per_volume',source_property_label='Specific tensile energy to break, Eb')
    p['reported_value'].update(number='32.2',value_text='32.2',unit_code='J/cm^3',unit_text='J/cm³')
    p['uncertainty'].update(number='6.4',value_text='6.4',unit_code='J/cm^3',unit_text='J/cm³',scope='Reported mechanical SD for selected NR work group;not SE,CI or uncertainty of a calculated integral.',evidence=[evidence('PDF p7 Table4 NR/Eb;p19 §3.3.4 final statistics statement','uncertainty')])
    p['basis_note']='Source table reports mean and mechanical SD;source integrates stress-strain curves. Mean of individual integrals versus integral of mean curve unknown. No software integration or reconstruction.'
    p['uncertainty_note']='Source mechanical mean/SD retained;volume basis and integration conventions unconfirmed,not inferred from amplitude.'
    p['work_reference_basis']=dict(status='not_reported_in_inspected_source',text=None,evidence=[],notes='Initial/current reference volume,cross-section and engineering/true stress-strain conventions unknown;J/cm³ establishes volumetric reporting only.')
    p['sample_count']=dict(value=5,relation='exact',scope='Source-reported quasi-static tensile specimens per formulation;not verified independent batches or a defined averaging/integration order.',source_statement='Five specimens per composition in quasi-static paragraph;mechanical mean ± SD stated separately.',evidence=[evidence('PDF p18 §3.3.4 quasi-static paragraph;p19 final statistics statement','sample_count')])
    p['conditions']['test_method']['text']='Instron5969,1kN load cell;Instron2603 resistance extensometer,25mm gauge;source integrates tensile stress-strain curve to break.'
    p['conditions']['test_method']['notes']='Not a finite-strain slope;integration start,offset,algorithm and stress/strain measures unknown.'
    for c in p['conditions']['additional_conditions']:
        if c['name']=='stress_strain_convention':c['fact']['notes']='Engineering/true stress-strain and volume reference for the reported work unknown.'
    p['method_definition']=dict(type='source_reported_conventional',definition='Source-reported volumetric tensile work to break from stress-strain curve integration;ASTMD412 as cited,Instron5969/2603,500mm/min crosshead speed. No reconstruction or pressure conversion.',extraction_window=dict(status='reported',text='Source stress-strain curve integrated to break',evidence=[evidence('PDF p18 §3.3.4 quasi-static paragraph','method')],notes='Integration start,offset,algorithm,quadrature and source averaging order unknown.'),evidence=[evidence('PDF p18 §3.3.4 quasi-static paragraph','method')])
    p['source_discrepancies']=[dict(description='Table4 epsilon_b header is mm/mm while Figure3 uses percent strain;NR730±14 unit conflict unresolved.',disposition='Keep elongation held;transcribe only explicit Eb32.2±6.4J/cm³. Do not correct strain unit,divide by100 or reconstruct work integral.',evidence=[evidence('PDF p7 Table4 epsilon_b andEb columns/Figure3 axes','source_discrepancy')])]
    p['evidence']=[evidence('PDF p7 Table4 NR/Eb;p19 mechanical statistics','reported_value','classification','summary_statistic','uncertainty')]
    inspection='Official23pagePDF retained2026-11-04;selectedpages1,6,7,18,19 and same-source XML inspected. SelectedNRwork table cell/method/statistics;not rawcurve integration or latestnotice verification.'
    p['source_document']=dict(url=url,revision='Retained official PDF;latest revision/notices unverified',inspected_on='2026-11-11',sha256='2e729bb58b361568d27ab772ec1c031648cb6a858f58a6e4ece9ce45b74c3ea2',hash_status='recorded',hash_note=None,inspection_scope=inspection,inspection_status='selected_content_inspected')
    p['verification']['source_inspection_scope']=inspection
    p['scope_note']='Study-specific vulcanizate work per reported volume;not recoverable elastic energy,fracture energy per area or caloric heat. Mean/SD/n5 limitedto reported quasi-static specimens. Temperature,RH,conditioning,volume/stress-strain conventions,integration/averaging order and independent batches unknown;related epsilon unit conflict retained. No conversion,recalculation or engineering allowable.'
    proposal=read(SOURCE/'SOURCE_UPDATE_PROPOSAL_R1.json');assert before.sources[sid]==proposal['baseline_source']
    data['sources']['records']=[proposal['proposed_source'] if s['id']==sid else s for s in data['sources']['records']]
    data['materials']['records']=[state if s['id']==state['id'] else s for s in data['materials']['records']]
    data['reference_properties']['records'].append(p)
    validate_material_catalog(*(data[n] for n in ['materials','reference_properties','sources']))
    after=Database(data)
    assert all(after.properties[k]==v for k,v in before.properties.items())
    assert before.identities==after.identities and before.grades==after.grades and len(after.states)==len(before.states)
    write('NEW_PROPERTY_R1.json',p);write('STATE_UPDATE_R1.json',dict(before=parent,after=state))
    write('SOURCE_UPDATE_R1.json',proposal)
    write('VALIDATION_R1.json',dict(baseline_snapshot=before.snapshot,candidate_snapshot=after.snapshot,properties=len(after.properties),states=len(after.states),new_properties=1,new_states_identities=0,all_old_properties_unchanged=True,native_applied=False,installation='not_run'))
    print(json.dumps({'candidate_properties':len(after.properties),'candidate_states':len(after.states),'snapshot':after.snapshot,'native_applied':False}),flush=True)
if __name__=='__main__':main()
