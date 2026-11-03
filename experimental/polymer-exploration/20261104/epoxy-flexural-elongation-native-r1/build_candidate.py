"""Prepare five source-qualified existing-state bending endpoint references."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from jsonschema import Draft202012Validator, FormatChecker
from materials_boundaries.database import Database, read_snapshot
from materials_boundaries.material_presentation import render_material_catalog

AREA = ROOT / 'experimental/polymer-exploration/20261104'
OUT = Path(__file__).resolve().parent
BASE = '7109e8ad6a61c1dce5e37352418c6c27fd5370b08345cb48021f9bbf580713a6'


def read(path): return json.loads(path.read_bytes())
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def main():
    dest = Path(sys.argv[1]).resolve()
    assert not dest.exists() and not dest.is_relative_to(ROOT)
    proposal = AREA / 'epoxy-flexural-elongation-source-r1'
    review = read(proposal / 'INDEPENDENT_SOURCE_REVIEW_R1.json')
    assert review['decision']=='approved' and review['review_inputs_sha256']==sha(proposal/'REVIEW_INPUTS_R1.json')
    manifest = read(proposal/'REVIEW_INPUTS_R1.json')
    archive = read(proposal/'BASELINE_CONTRACT_BINDING_R1.json')
    for name,digest in manifest['repo_files_sha256'].items():
        if sha(ROOT/name)!=digest:
            old=archive[name]
            assert sha(ROOT/old['archive_path'])==old['sha256']==digest,name
    for name,digest in manifest['external_files_sha256'].items(): assert sha(Path(name))==digest,name
    facts=read(proposal/'SOURCE_FACTS_R1.json')
    before=Database()
    assert before.snapshot==BASE and len(before.properties)==5317
    assert all(before.states[s['id']]==s for s in read(proposal/'BASE_STATES_R1.json'))
    assert all(before.properties[p['id']]==p for p in read(proposal/'BASE_PROPERTIES_R1.json'))
    source=facts['source_id']
    states,properties=[],[]
    for row in facts['rows']:
        old=before.states[row['state_id']]
        assert old['version']==row['old_state_version']=='1.0.1'
        prop=deepcopy(before.properties[row['base_property_id']])
        assert row['new_property_id'] not in before.properties
        url=prop['source_document']['url']
        methodloc='Retained publisherPDFp6 section2.5.2 flexural testing; p16Table8 endpoint label'
        valueloc=row['locator']
        def ev(locator,tags): return dict(source_id=source,url=url,locator=locator,supports=list(tags))
        def unknown(note): return dict(status='not_reported_in_inspected_source',text=None,evidence=[],notes=note)
        description=('Author-labelled Flexural Elongation at Break(%),50ST/Tinius Olsen,GOST R56810-2015(ASTM D790-10),0.85mm/min machine/testing speed; '
            '80x9.8x3.6mm bars milled from3.6mm curedplate; source span-to-depth wording64:3.6mm. '
            'Actual deflection/strain channel,outer-fiber/engineering/true strain convention,reduction formula,break detection and evaluation criterion,calibration and support-point count unknown;no standard-based reconstruction.')
        prop.update(id=row['new_property_id'],version='1.0.0',quantity='flexural_elongation_at_break',quantity_dimension='dimensionless',
            source_property_label='Flexural Elongation at Break (%)',summary_statistic='not_stated',reporting_basis='not_stated',
            uncertainty=None,uncertainty_status='not_reported_in_inspected_source')
        prop['reported_value'].update(number=row['number'],value_text=row['number'],unit_code='percent_elongation',unit_text='%')
        prop['basis_note']='Selected Table8 scalar crosschecked against Figure9 printed numerical label. Central estimator,independent specimens/batches and numeric dispersion unknown;not an inferredmean,SD,SE orCI. Original percent,not divided by100 or equated to tensile strain.'
        prop['conditions']['test_method'].update(text=description,evidence=[ev(methodloc,('method','condition'))],notes='Source bending-endpoint label only; actual strain convention and rupture detection unknown. Standard citation does not certify compliance.')
        prop['conditions']['test_standard']['notes']='Source citation only; no missing strain formula,deflection channel,support-count,environment,n or standard compliance inferred.'
        prop['conditions']['additional_conditions']=[c for c in prop['conditions']['additional_conditions'] if c['name']!='modulus_extraction_algorithm']
        prop['conditions']['additional_conditions'].append({'name':'strain_and_break_definition','fact':unknown('Actual deflection/strain channel,outer-fiber/engineering/true convention,reduction formula and rupture/evaluation criterion unknown;not supplied by standard citation.')})
        prop['uncertainty_note']='Inspected section2.5.2/Table8/Figure9 do not define central aggregation,n,batches or numeric SD/SE/CI for this selected endpoint. Unknown numeric uncertainty does not mean zero scatter;no tensile/impact/DSC statistics borrowed.'
        prop['sample_count']=dict(value=None,relation='not_reported',scope='Selected formulation and bending endpoint only;exact specimen and independent batch counts unknown.',source_statement='Inspected bending method/Table8/Figure9 do not specify an exact count;other-test or standard-default counts not transferred.',evidence=[])
        prop['method_definition'].update(definition=description,extraction_window=None,evidence=[ev(methodloc,('method','classification'))])
        prop['source_discrepancies'].append({
            'description':'Page18 describes flexural elongation as continuously decreasing with increasing phosphazene content. Table8/Figure9 give PNA-BPF-4=8.19% and PNA-BPF-3=8.23%, a local scalar ordering that is not strictly decreasing along the source Figure9 context.',
            'disposition':'Retain all Table8 literals and the narrative caveat. No smoothing,repair,validated monotonic law or statistical significance from a small difference without n/dispersion;the author Figure9 composition axis is not independent composition verification.',
            'evidence':[ev('Retained publisherPDFp16 Table8; p18 section3.2 text andFigure9 printed labels',('source_discrepancy',))]})
        scope='Retained exact publisherPDF visually inspected pp1,5,6,16,18: articleCCBY4,commonDDS cure,bending method,Table8 selected flexural-break-elongation column and Figure9 printed numeric labels/narrative ordering caveat. No fresh PDF download,latest-notice/SI completeness,rawdata reanalysis or certification.'
        prop['source_document'].update(inspected_on='2026-11-04',inspection_scope=scope)
        prop['verification']['source_inspection_scope']=scope
        prop['scope_note']='Existing '+row['source_label']+' identity and its3.6mm bending state only,not4mm tensile state. Source-labelled flexural elongation at break,not tensile break/at-strength endpoint or bending modulus/strength;source percent retained without /100. Unknown actual strain/deflection convention,break criterion,T/RH,conditioning,n/dispersion and calibration remain. Existing composition/feed/alkali discrepancies and Table8/Figure9 versus continuous-decrease narrative caveat retained;no source repair,standard-based formula,statistical significance,engine input,allowable or universal bound.'
        prop['evidence']=[ev(valueloc,('reported_value','classification')),ev(methodloc,('method','condition'))]
        state=deepcopy(old)
        state.update(version='1.0.2',property_ids=old['property_ids']+[prop['id']],
            source_scope=old['source_scope']+' Source-labelled flexural elongation at break now linked separately;actual strain/deflection and break criterion unknown,not a tensile endpoint or fit slope.')
        states.append(state);properties.append(prop)
    data=deepcopy(before.data)
    state_map={s['id']:s for s in states}
    data['materials']['records']=[state_map.get(s['id'],s) for s in data['materials']['records']]
    data['reference_properties']['records'].extend(properties)
    src=deepcopy(before.sources[source])
    src['claim_notes'].append('2026-11-04 Table8/Figure9 existingfive PNA-BPF bending-endpoint supplement:5.73/6.66/8.23/8.19/9.15% source-labelled flexural elongation at break. Unknown actualstrain/deflection convention,break criterion,T/RH,conditioning,n/dispersion;not tensile endpoint or engineering input. Continuous-decrease text versus local Table8/Figure9 ordering retained,not smoothed or significance-certified. Existing feed/mole/alkali contradictions remain.')
    data['sources']['records']=[src if s['id']==source else s for s in data['sources']['records']]
    after=Database(data)
    contracts=after.validate_scientific_contracts()
    assert len(after.properties)==5322 and len(after.states)==5207
    assert all(after.properties[k]==v for k,v in before.properties.items())
    assert after.identities==before.identities and after.grades==before.grades and set(after.states)==set(before.states)
    for key,old in before.states.items():
        if key in state_map:
            restored=deepcopy(after.states[key])
            for field in ('version','property_ids','source_scope'):restored[field]=old[field]
            assert restored==old
        else:assert after.states[key]==old
    assert set(after.sources)==set(before.sources) and all(after.sources[k]==v for k,v in before.sources.items() if k!=source)
    restored=deepcopy(src);restored['claim_notes'].pop();assert restored==before.sources[source]
    for name in data:
        Draft202012Validator(read(ROOT/'schemas'/(name+'.schema.json')),format_checker=FormatChecker()).validate(data[name])
    dest.mkdir(parents=True);(dest/'native-tables').mkdir()
    for name,value in data.items():write(dest/'native-tables'/(name+'.json'),value)
    write(dest/'native-candidate-r1.json',dict(baseline_snapshot=BASE,stage='not_applied',materials=dict(identities=[],grades=[],records=states),reference_properties=dict(records=properties),sources=dict(records=[src])))
    write(dest/'MAPPING_FACTS_R1.json',dict(rows=facts['rows'],property_records={p['id']:p for p in properties},state_records=state_map,source_record=src))
    counts={}
    for phase,db in [('before',before),('after',after)]:
        export=dest/'source-exports'/phase;db.export(export,source=source);_,joined=read_snapshot(export)
        assert joined=={r['property']['id']:r for r in db.records(source=source)};counts[phase]=len(joined)
    assert counts=={'before':25,'after':30}
    for language in ('en','zh','ja','de'):
        with patch('materials_boundaries.catalog.read_catalog',side_effect=lambda name:data[name]):
            text=render_material_catalog({'schema_version':'1.0.0','records':properties},'reference-properties',language)
        assert all(row['number'] in text for row in facts['rows'])
        assert all(token in text for token in ('%','0.85','unknown','8.19','8.23','continuously'))
        (dest/('render-'+language+'.txt')).write_text(text,encoding='utf-8',newline='\n')
    write(dest/'VALIDATION_R24.json',dict(baseline_snapshot=BASE,preview_snapshot=after.snapshot,properties=5322,states=5207,
        new_properties=5,new_identities_grades_states_sources=0,all_old5317_properties_complete_unchanged=True,
        state_change='Only fiveexistingbendingstates version/property_ids/source_scope;all statefacts and other5202states unchanged.',
        source_change='One appended claimnote only.',schema_format='passed',current_graph=contracts,complete_source_export=counts,
        four_languages='passed',native_applied=False,installed='not_run',full_history_regression='not_run',pushed=False))
    for name in ('native-candidate-r1.json','MAPPING_FACTS_R1.json','VALIDATION_R24.json'):
        with (OUT/name).open('xb') as stream:stream.write((dest/name).read_bytes())
    print(json.dumps(dict(snapshot=after.snapshot,properties=5322,states=5207,source_exports=counts)))


if __name__=='__main__':main()
