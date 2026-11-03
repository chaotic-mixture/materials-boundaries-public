"""Draft one source-qualified finite-strain modulus on the existing NR state."""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT))
from materials_boundaries.database import Database

BASE = '62502e5fe24d06f883228fe7d9fea3c579d03d97c25c0b3b8d33a87a9c767bd6'
XML_SHA = '97eb8a1e73e57b6fc64fcf3b0be6603db3f8dcb5fa927570e91eb033f1018f69'
SID = 'bianchi_2025_nr_nanoclay'
URL = 'https://www.ebi.ac.uk/europepmc/webservices/rest/PMC12300880/fullTextXML'


def ev(locator, *supports):
    return [{'source_id':SID,'url':URL,'locator':locator,'supports':list(supports)}]


def fact(value, locator, note=None):
    return {'status':'reported','text':value,'evidence':ev(locator,'condition'),'notes':note}


def unknown(note):
    return {'status':'not_reported_in_inspected_source','text':None,'evidence':[],'notes':note}


def write(path, obj):
    with path.open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(obj,stream,ensure_ascii=False,indent=2);stream.write('\n')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--xml',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args();out=args.output_dir.resolve()
    assert not out.exists() and not out.is_relative_to(ROOT/'materials_boundaries')
    raw=args.xml.read_bytes();assert hashlib.sha256(raw).hexdigest()==XML_SHA
    article=ET.fromstring(raw)
    table=next(t for t in article.findall('.//table-wrap') if ''.join(t.find('label').itertext()).strip()=='Table 4')
    row=next(r for r in table.findall('.//tbody/tr') if ''.join(r[0].itertext()).strip()=='NR')
    literal=' '.join(''.join(row[1].itertext()).split())
    match=re.fullmatch(r'(\d+\.\d+)\s*±\s*(\d+\.\d+)',literal);assert match
    mean,sd=match.groups();assert (mean,sd)==('0.35','0.08')
    method_section=next(s for s in article.findall('.//sec') if s.get('id')=='sec3dot3dot4-molecules-30-03035')
    method_text=' '.join(method_section.itertext())
    for literal in ['100–200%','Five specimens','500 mm/min','25 mm','mean ± standard deviation']:
        assert literal in method_text,literal
    before=Database();assert before.snapshot==BASE
    density=before.properties['refprop_smr10_bianchi2025_nr_mass_density']
    state=deepcopy(before.states[density['material_state_id']]);source=deepcopy(before.sources[SID])
    pid='refprop_smr10_bianchi2025_nr_finite_strain_tensile_modulus'
    assert pid not in before.properties
    method='Section 3.3.4, quasi-static uniaxial tensile tests'
    cell='Table 4, unfilled NR row, E100–200 (MPa) column; section 3.3.4'
    definition='Source-reported slope of the tensile stress–strain curve in the 100–200% strain region. This is a finite-strain interval modulus, not initial Young modulus. Exact slope fitting, endpoints and engineering/true stress–strain conventions are unspecified.'
    prop=deepcopy(density)
    prop.update(id=pid,version='1.0.0',quantity='tensile_modulus',quantity_dimension='pressure',
        source_property_label='E100–200 (MPa), slope over 100–200% strain',density_basis=None,
        reported_value={'kind':'scalar','value_text':mean,'unit_text':'MPa','unit_code':'MPa','number':mean},
        summary_statistic='reported_mean',basis_note='Table 4 selected finite-strain modulus. Section 3.3.4 explicitly reports all mechanical properties as mean ± SD; five quasi-static tensile specimens per composition. No recalculation or pooling.',
        conditions={'temperature':unknown('Temperature of this quasi-static test is not stated; do not transfer density room temperature or hardness/relaxation 25C.'),
            'test_standard':fact('ASTM D412',method,'Source statement only; exact edition and independent compliance unverified.'),
            'test_method':fact('Instron 5969, 1 kN load cell; resistance extensometer Instron 2603, gauge length 25 mm; finite-strain interval slope.',method,'Apparatus settings do not establish exact fitting implementation or a small-strain material constant.'),
            'direction':unknown('Loading axis relative to sheet processing direction is not specified; no isotropy inferred.'),
            'conditioning':unknown('Post-cure humidity, conditioning and storage/recovery interval of the selected quasi-static tensile specimens are unspecified.'),
            'loading_rate':fact('500 mm/min crosshead speed',method,'Not converted to a verified specimen strain rate.'),
            'additional_conditions':[{'name':'test_relative_humidity','fact':unknown('No humidity value assigned.')},
                {'name':'prior_loading_history','fact':unknown('Cyclic tests and pre-stretching for relaxation are separate procedures, not assigned to quasi-static specimens.')},
                {'name':'stress_strain_convention','fact':unknown('Source does not explicitly identify engineering versus true stress/strain for the selected slope.')}]},
        uncertainty={'type':'reported_standard_deviation','value_text':sd,'number':sd,'unit_text':'MPa','unit_code':'MPa',
            'scope':'Selected mechanical result only; no SD-to-SE/CI conversion or density uncertainty inference.',
            'coverage_factor':None,'confidence_level':None,'evidence':ev(cell,'uncertainty')},
        uncertainty_status='reported_standard_deviation',uncertainty_note='0.35 ± 0.08 MPa, mechanical mean ± SD; not a confidence interval, universal bound or engineering allowable.',
        sample_count={'value':5,'relation':'exact','scope':'Five quasi-static tensile specimens per selected composition; independent batch count unspecified.',
            'source_statement':'Five specimens were tested for each composition.','evidence':ev(method,'sample_count')},
        method_definition={'type':'source_reported_conventional','definition':definition,
            'extraction_window':{'status':'reported','text':'100–200% strain region','evidence':ev(method,'method'),'notes':'Exact fit algorithm and endpoint handling unspecified; no initial tangent or secant-from-origin inference.'},'evidence':ev(method,'method')},
        source_discrepancies=[],evidence=ev(cell,'reported_value','classification','method','summary_statistic','uncertainty','sample_count'),
        source_document={'url':URL,'revision':'Retained PMC12300880 XML; no newer revision verified.','inspected_on':'2026-11-03','sha256':XML_SHA,'hash_status':'recorded','hash_note':None,'inspection_scope':'Selected XML permission notice, Table 4 NR E100–200 cell, sections 3.2 and 3.3.4; no fresh PDF visual review or independent review this round.','inspection_status':'selected_content_inspected'},
        scope_note='Only the existing unfilled-with-nanoclay study NR vulcanizate, including curatives. Finite-strain 100–200% slope cannot be used as small-strain Young modulus or to infer Poisson/shear/bulk moduli. Mechanical n=5 and mean/SD do not fill density metadata. Other six nanoclay formulations and other mechanical quantities remain outside this draft.',
        verification={'source_inspection_scope':'Curator XML transcription of selected finite-strain modulus and method only.','transcription_cross_check':'completed','independent_scientific_review':False,'raw_data_reanalysis':False})
    prop['verification']['source_inspection_scope']=prop['source_document']['inspection_scope']
    state['version']='1.0.1';state['property_ids'].append(pid)
    state['state']['orientation']=unknown('Macroscopic processing/loading-axis relation is not specified. Density direction remains not_applicable in its own property; no isotropy inference.')
    state['source_scope']=state['source_scope'].replace('Arithmetic aggregation and meaning of ± remain unspecified.','For the density result only, arithmetic aggregation and meaning of ± remain unspecified.')+' The additional E100–200 tensile slope uses five quasi-static specimens and mechanical mean ± SD only.'
    assert URL not in source['urls'];source['urls'].append(URL)
    source['claim_notes'].append('2026-11-03 retained primary XML selected finite-strain E100–200 supplement draft: source mechanical mean/SD and n=5 are distinct from density statistics. No new source assets or third-party supplier data bundled; draft pending independent source/mapping review.')
    data=deepcopy(before.data)
    data['materials']['records']=[state if r['id']==state['id'] else r for r in data['materials']['records']]
    data['sources']['records']=[source if r['id']==SID else r for r in data['sources']['records']]
    data['reference_properties']['records'].append(prop)
    after=Database(data);contracts=after.validate_scientific_contracts()
    assert before.identities==after.identities and before.grades==after.grades
    assert set(before.states)==set(after.states)
    assert all(after.properties[pid]==r for pid,r in before.properties.items())
    assert Database().snapshot==BASE
    out.mkdir(parents=True)
    write(out/'native-candidate-r1.json',{'stage':'draft_not_applied_pending_independent_review','baseline_snapshot':BASE,'materials':{'identities':[],'grades':[],'records':[state]},'sources':{'records':[source]},'reference_properties':{'records':[prop]}})
    tables=out/'native-tables';tables.mkdir()
    for name,table in data.items():write(tables/(name+'.json'),table)
    write(out/'VALIDATION_R1.json',{'baseline_snapshot':BASE,'preview_snapshot':after.snapshot,'new_identities':0,'new_states':0,'new_sources':0,'new_properties':1,'modified_state_count':1,'source_metadata_amendments':1,'all_existing_property_objects_unchanged':True,'contracts':contracts,'prior_attempt':'Rejected mismatched verification/document inspection_scope strings; corrected before output without weakening validator','native_applied':False,'full_history_regression':'not_run','independent_review':'pending','pushed':False})
    print(json.dumps({'preview_snapshot':after.snapshot,'new_properties':1,'contracts':contracts}))


if __name__=='__main__':main()
