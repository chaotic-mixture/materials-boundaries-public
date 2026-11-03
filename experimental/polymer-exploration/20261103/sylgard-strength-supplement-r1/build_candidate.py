"""Five labelled UTS results on existing Sylgard cure states, with unresolved source scope."""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from materials_boundaries.database import Database
PACKET = Path(__file__).resolve().parent
BASE = '13f837f4a1e02fd397432aab7e47f0d29a48b38211add517c27fd12d6bd0f56c'
SID = 'johnston_2014_bulk_sylgard184'


def read(path): return json.loads(path.read_bytes())
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-pdf', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    out = args.output_dir.resolve()
    assert not out.exists() and not out.is_relative_to(ROOT/'materials_boundaries')
    facts = read(PACKET/'SOURCE_READBACK_R1.json')
    assert sha(args.source_pdf) == facts['pdf']['sha256']
    before = Database()
    assert before.snapshot == BASE
    data = deepcopy(before.data)
    props, states = [], []
    for row in facts['rows']:
        temp = row['cure_temperature_C']
        state = before.states[f'state_dow_corning_sylgard184_johnston2014_{temp}c']
        old = next(before.properties[pid] for pid in state['property_ids']
                   if before.properties[pid]['quantity']=='youngs_modulus')
        assert old['reported_value']['number']==row['youngs_modulus_MPa']
        assert old['uncertainty']['number']==row['youngs_plus_minus_MPa']
        url = old['source_document']['url']
        def ev(locator, *tags):
            return [{'source_id':SID,'url':url,'locator':locator,'supports':list(tags)}]
        value, amplitude = row['ultimate_tensile_strength_MPa'], row['strength_plus_minus_MPa']
        locator = f'PDF p.5 Table 2, {temp} °C row, Ultimate tensile strength (MPa)'
        prop = deepcopy(old)
        prop.update(id=old['id'].replace('_youngs_modulus','_tensile_strength'), version='1.0.0',
                    quantity='tensile_strength', source_property_label='Ultimate tensile strength (MPa)')
        assert prop['id'] not in before.properties
        prop['reported_value'].update(number=value,value_text=value)
        prop['basis_note'] = 'Source Table 2 explicitly labels ultimate tensile strength. Six tensile-sample data sets per cure temperature are averaged, but the order of peak extraction and averaging and the CI estimand are not identified; retain reported_value, not an invented specimen-wise UTS mean.'
        prop['uncertainty'].update(number=amplitude,value_text=amplitude,
            scope=f'Reported ±{amplitude} MPa amplitude of the source-stated 95% confidence interval for the Table 2 {temp} °C-cure UTS result; estimand and construction unknown.',
            evidence=ev(locator,'uncertainty')+ev('PDF p.4 section 4, specified errors represent 95% CI; section 4.1, six tensile samples per cure temperature','uncertainty','sample_count','summary_statistic'))
        for key, notes in [('estimand','The source does not identify the UTS CI estimand; averaging six test-data sets does not establish a CI of a mean of specimen-wise peak stresses.'),
                           ('construction','CI formula, distributional assumptions, peak-extraction/averaging order and coverage factor are unspecified. No SD, SE or t multiplier inferred.')]:
            prop['uncertainty'][key]['notes'] = notes
        prop['uncertainty_note'] = f'{value} ± {amplitude} MPa: source-stated 95% CI, with unknown estimand/construction. The six tensile specimens are not six independent production batches; no SD/SE or population-mean CI inferred.'
        prop['sample_count']['scope'] = f'Six tensile specimens at the selected {temp} °C curing temperature; independent production-batch count and peak-extraction/averaging order unknown.'
        prop['sample_count']['source_statement'] = 'Section 4.1 averages data from six tensile test samples at every cure temperature.'
        definition = 'Source-labelled Table 2 ultimate tensile strength from Hounsfield Universal 10 kN tensile testing, ASTM D412 Type C, crosshead 254 mm/min. Source section 3.1 includes maximum strength in a below-40%-strain computation statement, whereas section 4.1 describes a nonlinear region before failure. Strength extraction range and peak/averaging algorithm remain unresolved; no source value is recalculated.'
        prop['method_definition'].update(definition=definition,extraction_window=None,
            evidence=ev('PDF pp.3–4 section 3.1; p.4 section 4.1 and Figure 3; p.5 Table 2','method','classification'))
        prop['conditions']['test_method']['notes'] = 'Operational strength extraction window/algorithm is unresolved as documented under source_discrepancies; the Young modulus fitting region is not assigned to UTS.'
        prop['conditions']['test_standard']['notes'] = 'Source-stated ASTM D412 Type C; edition and independent compliance unverified. Source mold includes an overflow/bubble trap.'
        extras = [x for x in prop['conditions'].get('additional_conditions',[]) if x['name']!='exact_fitting_algorithm']
        for item in extras:
            if item['name']=='source_applied_geometry_correction':
                item['name']='source_strain_correction_context'
                item['fact']['notes'] = 'Context for source strain data only: factor derived below 40% strain, not a stress/UTS multiplier. Never apply it again to the reported UTS or CI; do not assume validity beyond its stated regime.'
        extras.append({'name':'strength_evaluation_window','fact':{'status':'not_verified','text':None,
            'evidence':ev('PDF p.4 section 3.1 final tensile paragraph versus section 4.1 and Figure 3','condition'),
            'notes':'Conflicting calculation-range wording; source UTS extraction window and aggregation algorithm cannot be resolved. Do not replace with the Young modulus below-40% region or a guessed full-curve algorithm.'}})
        prop['conditions']['additional_conditions'] = extras
        prop['source_discrepancies'].append({'description':facts['method_scope_issue'],
            'disposition':'Retain source-labelled Table 2 UTS and its CI as a catalog-only reported result. Do not repair source wording, assert a verified below-40% or full-curve extraction algorithm, reapply strain correction to stress, or use the result as an engineering allowable.',
            'evidence':ev('PDF p.4 section 3.1 final tensile paragraph, section 4.1 and Figure 3; p.5 Table 2','source_discrepancy')})
        prop['evidence'] = ev(locator,'reported_value','classification')+ev('PDF p.4 sections 4 and 4.1, confidence statement and six-sample data averaging','uncertainty','sample_count','summary_statistic')
        scope = f'Retained institutional-repository PDF pp.1,3–5 visually checked 2026-11-03: article CC BY3.0 notice, Table 1 tensile cures, tensile methods/statistics and Table 2 {temp} °C UTS cell. Source calculation-range contradiction recorded; no new download, raw-data reanalysis or independent scientific certification.'
        prop['source_document'].update(inspected_on='2026-11-03',inspection_scope=scope)
        prop['verification']['source_inspection_scope'] = scope
        prop['scope_note'] = f'Only the existing {temp} °C tensile-cure state of commercial Sylgard 184 mixed at 10:1 parts, exact mass/volume ratio basis unknown. Average test ambient 21 °C/39% RH is not a controlled setpoint or cure temperature; 1 h cooling at 22 °C and testing within 2 h after cure do not establish moisture equilibrium. Table 2 UTS/CI are preserved despite unresolved calculation-window wording. Failure-load and elongation columns are not imported or used for force/area recalculation. No Young modulus, yield or break-stress relabelling, population-mean CI, engineering allowable or automatic calculator input.'
        changed = deepcopy(state)
        major,minor,patch = changed['version'].split('.')
        changed['version'] = f'{major}.{minor}.{int(patch)+1}'
        changed['property_ids'].append(prop['id'])
        changed['source_scope'] += ' 2026-11-03 supplement: same tensile cure/specimens also link the Table 2 source-labelled ultimate tensile strength. Finite Young-modulus window and strength calculation-range discrepancy are property-specific, not transferable method assumptions.'
        props.append(prop);states.append(changed)
    data['reference_properties']['records'].extend(props)
    changes={s['id']:s for s in states}
    data['materials']['records']=[changes.get(s['id'],s) for s in data['materials']['records']]
    source=deepcopy(before.sources[SID])
    source['claim_notes'].append('2026-11-03 supplement: five existing Table 1 tensile-cure states retain their Young moduli and gain Table 2 explicitly labelled ultimate tensile strengths. Source-stated 95% CI and six tensile samples retained with unknown estimand/construction/peak-averaging order. Section 3.1 versus 4.1 strength-window wording remains unresolved and is explicitly recorded; no stress recalculation or source repair. Earlier 100 °C note describes the initial selected result, not current coverage. CC BY3.0 attribution and source-asset exclusion remain.')
    data['sources']['records']=[source if s['id']==SID else s for s in data['sources']['records']]
    after=Database(data);contracts=after.validate_scientific_contracts()
    assert all(after.properties[k]==v for k,v in before.properties.items())
    assert after.identities==before.identities and after.grades==before.grades and set(after.states)==set(before.states)
    assert len(after.properties)==len(before.properties)+5
    out.mkdir(parents=True);tables=out/'native-tables';tables.mkdir()
    for name,value in data.items():write(tables/(name+'.json'),value)
    write(out/'native-candidate-r1.json',{'baseline_snapshot':BASE,'stage':'frozen_not_applied',
        'materials':{'identities':[],'grades':[],'records':states},'sources':{'records':[source]},'reference_properties':{'records':props}})
    write(out/'VALIDATION_R1.json',{'baseline_snapshot':BASE,'preview_snapshot':after.snapshot,'new_properties':5,'new_states':0,'new_identities':0,
        'modified_states':5,'modified_sources':1,'all_existing_property_objects_unchanged':len(before.properties),'contracts':contracts,
        'native_applied':False,'pushed':False,'full_history_regression':'not_run'})
    print(json.dumps({'snapshot':after.snapshot,'properties':len(after.properties),'contracts':contracts}))


if __name__ == '__main__': main()
