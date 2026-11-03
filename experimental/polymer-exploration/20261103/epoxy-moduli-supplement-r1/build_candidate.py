"""Supplement five existing epoxy identities with source-scoped moduli only."""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from materials_boundaries.database import Database

BASE = '044456eb1e9413ec819b7145543dab8dce4c6e7d1ea963d8c3a2e6f717edbaec'
SID = 'tarasov_2022_pna_bpf_epoxy'
PACKET = Path(__file__).resolve().parent


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
    assert sha(args.source_pdf) == facts['source_pdf']['sha256']
    before = Database()
    assert before.snapshot == BASE
    data = deepcopy(before.data)
    new_props, new_states, modified_states = [], [], []
    for i, fact in enumerate(facts['rows'], start=1):
        state = before.states[fact['existing_state_id']]
        assert len(state['property_ids']) == 1
        old = before.properties[state['property_ids'][0]]
        assert old['quantity'] == 'tensile_strength' and old['reported_value']['number'] == fact['old_tensile_strength_MPa']
        assert state['identity_id'] == f'mat_tarasov2022_pna_bpf_{i}'
        url = old['source_document']['url']
        def ev(locator, *supports):
            return [{'source_id':SID, 'url':url, 'locator':locator, 'supports':list(supports)}]
        label = fact['source_label']
        for quantity, table, value in [('tensile_modulus',7,fact['tensile_modulus_GPa']),
                                       ('flexural_modulus',8,fact['flexural_modulus_GPa'])]:
            flexural = quantity == 'flexural_modulus'
            method_section = '2.5.2' if flexural else '2.5.1'
            locator = f'PDF p.16, Table {table}, {label} row, '+('Flexural' if flexural else 'Tensile')+' Modulus (GPa)'
            method_loc = f'PDF p.6, section {method_section}'
            prop = deepcopy(old)
            prop.update(id=f'refprop_tarasov2022_pna_bpf_{i}_{quantity}', quantity=quantity,
                        source_property_label=('Flexural' if flexural else 'Tensile')+' Modulus (GPa)')
            prop['reported_value'].update(unit_text='GPa',unit_code='GPa',value_text=value,number=value)
            prop['basis_note'] = f'Table {table} reports a {quantity.replace("_", " ")} scalar for this cured formulation. Central estimator, specimen/batch counts and dispersion are unreported; no mean, individual-specimen status, SD or CI inferred. Table precision is preserved without adding digits from the abstract.'
            definition = (facts['flexural_method'] if flexural else facts['tensile_method'])
            prop['method_definition'].update(definition=definition, extraction_window=None, evidence=ev(method_loc,'method','classification'))
            prop['conditions']['test_method'] = {'status':'reported', 'text':definition,
                'evidence':ev(method_loc,'method','condition'), 'notes':'Exact modulus extraction algorithm/strain window and independent standards compliance remain unknown.'}
            prop['conditions']['test_standard'] = {'status':'reported',
                'text':'GOST R 56810-2015 (ASTM D790-10)' if flexural else 'GOST 11262-2017 (ISO 527-2:2012)',
                'evidence':ev(method_loc,'condition','method'),
                'notes':'Source citation only; does not supply missing environmental conditions, repeat counts, fitting method or independently verified compliance.'}
            prop['conditions']['loading_rate'] = {'status':'reported', 'text':'0.85 mm/min' if flexural else '10 mm/min',
                'evidence':ev(method_loc,'condition'), 'notes':'Reported machine/testing speed, not a measured strain rate; do not transfer between methods.'}
            unknown = lambda notes:{'status':'not_reported_in_inspected_source','text':None,'evidence':[],'notes':notes}
            for key in ['temperature','conditioning','direction']:
                prop['conditions'][key] = unknown('Selected mechanical method does not specify this condition; cure/DSC/rheology conditions and assumed isotropy cannot supply it.')
            prop['conditions']['additional_conditions'] = [{'name':'relative_humidity','fact':unknown('Test and post-cure conditioning RH are not reported.')},
                {'name':'modulus_extraction_algorithm','fact':unknown('No numerical fit window, tangent/secant definition or actual strain estimator is reported; not automatically Young modulus.')},
                {'name':'specimen_plate_thickness','fact':{'status':'reported','text':'3.6 mm' if flexural else '4 mm','evidence':ev(method_loc,'condition'),'notes':'Source plate specification, not per-specimen metrology.'}}]
            if flexural:
                prop['conditions']['additional_conditions'] += [
                    {'name':'specimen_dimensions','fact':{'status':'reported','text':'80 × 9.8 × 3.6 mm (length × width × thickness)','evidence':ev(method_loc,'condition'),'notes':'Source nominal bar dimensions; no transferred tensile geometry or measured tolerances.'}},
                    {'name':'span_to_depth_source_statement','fact':{'status':'reported','text':'64:3.6 mm','evidence':ev(method_loc,'condition'),'notes':'Literal source wording; not recast as a dimensionless measured ratio or proof of support-point count.'}}]
            stats = f'Inspected section {method_section} and Table {table} do not state central aggregation, exact specimen/independent batch count or numerical SD/SE/CI. Unknown does not mean zero uncertainty.'
            prop['uncertainty_note'] = stats
            prop['sample_count'].update(scope='Selected formulation and mechanical method only; specimen and independent batch counts unknown.', source_statement=stats)
            prop['evidence'] = ev(locator,'reported_value','classification')+ev(method_loc,'method','condition')
            scope = f'Retained publisher PDF pp.5–6 sections 2.4 and {method_section}; p.16 Table {table} selected {label} modulus cell; p.1 article-specific CC BY4.0. Pages 5,6,16 visually rechecked 2026-11-03; no raw-data reanalysis or full-page absence audit.'
            prop['source_document'].update(inspected_on='2026-11-03', inspection_scope=scope)
            prop['verification']['source_inspection_scope'] = scope
            prop['scope_note'] = f'Only the existing {label} source-qualified mixed epoxy identity and its DDS cure. '+('Flexural bars milled from 3.6 mm plate are a separate source-scoped state from 4 mm tensile specimens. ' if flexural else 'Tensile modulus shares the existing 4 mm tensile specimen state; not relabelled Young modulus. ')+ 'Inherited nominal-feed/mole-number/alkali discrepancies remain unresolved. Test T/RH, post-cure conditioning, fit algorithm and statistics remain unknown; no calculator input, engineering allowable or universal bound.'
            if flexural:
                bend = deepcopy(state)
                bend.update(id=state['id']+'_flexural',version='1.0.0',aliases=[],property_ids=[prop['id']])
                bend['name'] = f'{label}, DDS-cured flexural bars from 3.6 mm plate (Tarasov 2022)'
                bend['names'] = {'en':bend['name'], 'zh':f'{label}，DDS固化3.6 mm板铣切弯曲条形试样',
                    'ja':f'{label}、DDS硬化3.6 mm板から切削した曲げ試験片', 'de':f'{label}, DDS-gehärtete Biegeproben aus 3,6-mm-Platte'}
                bend['state']['product_form'] = {'status':'reported','text':'Flexural bars milled from 3.6 mm-thick cured binder plate, 80 × 9.8 × 3.6 mm.',
                    'evidence':ev(method_loc,'state'),'notes':'Separate specimen form from the 4 mm tensile plate; no new material identity.'}
                for key, notes in [('conditioning','Post-cure flexural storage, humidity, moisture and duration are not specified.'),
                                   ('porosity','Flexural-specimen porosity is not reported; zero porosity is not inferred.')]:
                    bend['state'][key] = unknown(notes)
                bend['state']['temper_or_heat_treatment']['notes'] = 'Cure temperature/time qualifies the state, not test temperature or confirmed conversion.'
                bend['source_scope'] = prop['scope_note']
                bend['evidence'] = deepcopy(state['evidence'][:1])+ev('PDF p.5 section 2.4; p.6 section 2.5.2; p.16 Table 8 '+label,'state')
                prop['material_state_id'] = bend['id']
                new_states.append(bend)
            else:
                changed = deepcopy(state)
                changed['version'] = '1.0.1'
                changed['property_ids'].append(prop['id'])
                changed['source_scope'] = changed['source_scope'].replace('selected Table 7 tensile-strength result','selected Table 7 tensile-strength and tensile-modulus results')
                modified_states.append(changed)
            new_props.append(prop)
    data['reference_properties']['records'].extend(new_props)
    modified = {s['id']:s for s in modified_states}
    data['materials']['records'] = [modified.get(s['id'],s) for s in data['materials']['records']]+new_states
    source = deepcopy(before.sources[SID])
    source['claim_notes'].append('2026-11-03 supplement: five selected existing PNA-BPF-1 through -5 tensile moduli from Table 7 and flexural moduli from Table 8; separate 4 mm tensile and 3.6 mm flexural specimen states. Source-reported scalar precision/unknown statistics retained, no new identities, standards text or scientific certification. Earlier limited selection notes describe the original transcription stage; this supplement extends only the selected factual cells.')
    data['sources']['records'] = [source if s['id']==SID else s for s in data['sources']['records']]
    after = Database(data)
    contracts = after.validate_scientific_contracts()
    assert all(after.properties[k]==v for k,v in before.properties.items())
    assert after.identities==before.identities and after.grades==before.grades
    assert len(after.states)==len(before.states)+5 and len(after.properties)==len(before.properties)+10
    out.mkdir(parents=True)
    tables=out/'native-tables';tables.mkdir()
    for name,value in data.items():write(tables/(name+'.json'),value)
    write(out/'native-candidate-r1.json', {'baseline_snapshot':BASE,'stage':'frozen_not_applied',
        'materials':{'identities':[],'grades':[],'records':modified_states+new_states},'sources':{'records':[source]},
        'reference_properties':{'records':new_props}})
    write(out/'VALIDATION_R1.json', {'baseline_snapshot':BASE,'preview_snapshot':after.snapshot,'new_properties':10,
        'new_states':5,'modified_states':5,'new_identities':0,'new_sources':0,'modified_sources':1,
        'all_existing_property_objects_unchanged':len(before.properties),'contracts':contracts,
        'native_applied':False,'pushed':False,'full_history_regression':'not_run'})
    print(json.dumps({'snapshot':after.snapshot,'properties':len(after.properties),'states':len(after.states),'contracts':contracts}))


if __name__ == '__main__': main()
