"""Freeze DMA annotation candidates, a DSC hold and unadmitted TGA leads."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
EXT = ROOT.parent / 'open-database-evidence/polymer-pur-tga-source-20261104-r1'
PDF_DIR = ROOT.parent / 'open-database-evidence/polymer-pur-thermal-source-20261104-r1'
XML = ROOT.parent / 'open-database-evidence/polymer-pur-20261103/article-r1.xml'
sys.path.insert(0, str(ROOT))
from materials_boundaries.database import Database, canonical
from materials_boundaries.material_references import QUANTITY_DIMENSIONS


def read(path):
    return json.loads(path.read_bytes())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def text(node):
    return ' '.join(''.join(node.itertext()).split())


def write(name, value):
    with (OUT / name).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def main():
    db = Database()
    assert db.snapshot == '6a8bd7f0c6591088dbd14ab1c91662dca789f4821577be3a855e17d97af2c1b2'
    pdf = PDF_DIR / 'article-r2.pdf'
    assert sha(pdf) == '70b6da773e757f43557ed69bb651ce14e8ff82c1f09d39de1f50671343239e0e'
    assert sha(XML) == '4e0c1a91a9ae26d814576961a3805f9371b46498d4861fb578e7a413bb4c726d'
    sid = 'ivdre_2024_lpo_rigid_pur'
    source = db.sources[sid]
    root = ET.fromstring(XML.read_bytes())
    figure = next(n for n in root.findall('.//fig') if n.find('label') is not None and text(n.find('label')) == 'Figure 15')
    assert 'DMA' in text(figure) and 'tan δ' in text(figure)
    selected = ['LPO-1', 'LPO-2', 'SPO-2', 'SPO-3']
    annotations = {'LPO-1': ('126', 'black'), 'LPO-2': ('116', 'red'), 'SPO-2': ('125', 'purple'), 'SPO-3': ('137', 'orange')}
    candidates = []
    for label in selected:
        code = label.lower().replace('-', '')
        state = db.states[f'state_ivdre2024_{code}_rigid_pur']
        assert db.identities[state['identity_id']]['category'] == 'polymer'
        value, colour = annotations[label]
        candidates.append({'source_label': label, 'existing_identity_id': state['identity_id'], 'existing_grade_id': state['grade_id'], 'existing_density_state_id': state['id'],
                           'proposed_state_id': state['id'] + '_dma_cylinder', 'proposed_property_id': f'refprop_ivdre2024_{code}_dma_glass_transition_temperature',
                           'quantity': 'glass_transition_temperature', 'quantity_dimension': 'temperature', 'value_text': value, 'number': value, 'unit_text': '°C', 'unit_code': 'degC',
                           'value_locator': f'PDF p19 Figure15(b), author printed {colour} annotation and same-colour {label} curve/legend',
                           'source_property_label': 'Tg by DMA, source-labelled tanδ peak', 'summary_statistic_proposal': 'not_stated', 'numeric_uncertainty': None, 'selected_sample_count': None,
                           'transcription_method': 'Read explicitly printed numeric annotation,not curve coordinate estimation or digitization;XML confirms caption/method but doesnot contain annotation numerics',
                           'native_status': 'source_candidate_only_not_applied'})
    common = {'method_locator': 'PDF p8 §2.8 DMA paragraph; p19 Figure15(b) and caption', 'instrument': 'Mettler Toledo DMA/SDTA861e', 'mode': 'compression oscillation',
              'specimen_geometry': 'roughly13mm diameter and7mm height', 'frequency_Hz': '1', 'displacement_amplitude_um': '5', 'maximum_force_N': '1',
              'scan_start_C': '25', 'scan_end_C': '220', 'scan_rate_C_per_min': '3', 'smoothing': 'Source adjacent-averaging treatment for noise above170°C;no reprocessing or correction applied to printed labels',
              'source_Tg_criterion': 'Figure15(b) annotated tanδ peak;not DSC transition,storage-modulus onset or loss-modulus peak',
              'preparation': 'Shared optimized large-mold foam preparation,24h room-temperature cure; numeric roomtemperature not given',
              'unknowns': ['selected scalar estimator and contributors', 'numeric SD/SE/CI/expanded uncertainty', 'DMA n and independent batch count', 'amplitude peak/RMS convention', 'static preload and contact pressure', 'heating-cycle number and actual prior thermal history', 'DMA atmosphere and gas flow', 'RH and post-cure equilibration', 'compression direction relative to foam rise', 'peak fit/interpolation/selection implementation', 'calibration and actual standard compliance'],
              'non_transfers': ['TGA3ormore parallel samples is not DMA n', 'six static-compression cylinders and40kg/m3 normalization not DMA count/normalization', 'DSC second heating/nitrogen/6mg not DMA conditions', '1N maximum force is not a stated preload', '5um displacement is not a measured strain amplitude', 'room-temperature cure is not complete conditioning']}
    existing = {p['id']: hashlib.sha256(canonical(p)).hexdigest() for p in db.properties.values() if p['source_id'] == sid}
    assert len(existing) == 8
    write('DMA_TG_CANDIDATES_R1.json', {'schema': 'existing-PUR-DMA-Tg-source/1', 'source_id': sid, 'baseline_snapshot': db.snapshot, 'PDF_sha256': sha(pdf), 'XML_sha256': sha(XML), 'candidates': candidates, 'common_conditions': common, 'existing8_property_canonical_sha256': existing, 'new_quantity_or_schema_needed': False, 'quantity_supported_now': 'glass_transition_temperature' in QUANTITY_DIMENSIONS, 'latest_revision_correction_retraction': 'unknown', 'native_applied': False, 'new_native_records': 0, 'pushed': False})
    write('DSC_CONTRADICTION_HOLD_R1.json', {'status': 'held_not_admitted;independent_adjudication_requested', 'source_id': sid, 'locator': 'PDF p19 paragraph aboveFigure15 and Figure15(a);XML §3.4', 'selected_identity_leads': [{'label': 'LPO-1', 'figure_annotation_C': '123'}, {'label': 'LPO-2', 'figure_annotation_C': '129'}], 'conflict': 'The paragraph first attributes DSC-detected123–132°C transitions to LPO,then says DSCcouldnot detect LPO. The graphic annotates LPOcurves;do not silentlyreplace the second LPOwithSPO.', 'policy': 'Preserve source conflict;no DSC numeric admission in this candidate and no inferred statement about absent Tg. No reuse of DMA values or assumed method equivalence.', 'excluded': ['LPO-3 annotation132C,no existingselectedidentity', 'No SPO DSC value estimated from curves'], 'native_applied': False})
    table = next(n for n in root.findall('.//table-wrap') if n.find('label') is not None and text(n.find('label')) == 'Table 11')
    rows = [[text(n) for n in row if n.tag in ('td', 'th')] for row in table.findall('.//tr')]
    headers = rows[0][1:]
    assert headers == ['LPO-1', 'LPO-2', 'LPO-3', 'SPO-1', 'SPO-2', 'SPO-3']
    families = [('first_onset', 'thermal_degradation_onset_temperature', None), ('mass_loss_5_percent', 'temperature_at_specified_mass_loss', {'source_mass_loss_percent': '5'}), ('mass_loss_10_percent', 'temperature_at_specified_mass_loss', {'source_mass_loss_percent': '10'}), ('residue_at_700C', 'tga_residue_percentage', {'source_endpoint_temperature_C': '700'}), ('DTG_peak_1', 'thermal_degradation_rate_peak_temperature', {'source_peak_ordinal': 1}), ('DTG_peak_2', 'thermal_degradation_rate_peak_temperature', {'source_peak_ordinal': 2}), ('DTG_peak_3', 'thermal_degradation_rate_peak_temperature', {'source_peak_ordinal': 3})]
    assert len(rows[1:]) == len(families)
    leads = []
    for row, (role, quantity, descriptor) in zip(rows[1:], families):
        assert quantity not in QUANTITY_DIMENSIONS
        for label in selected:
            value = row[1 + headers.index(label)]
            match = re.fullmatch(r'(\d+(?:\.\d+)?)\s*±\s*(\d+(?:\.\d+)?)', value)
            assert match, value
            code = label.lower().replace('-', '')
            leads.append({'source_label': label, 'existing_identity_id': f'mat_ivdre2024_{code}_rigid_pur', 'source_row_label': row[0], 'endpoint_role': role, 'quantity_concept_only': quantity, 'source_descriptor': descriptor,
                          'source_expression': value, 'centre_number': match.group(1), 'plus_minus_number': match.group(2), 'unit_text': '%' if role == 'residue_at_700C' else '°C',
                          'locator': f'PDF p20 Table11 row{row[0]}/{label};XML Table11', 'centre_estimator': 'unknown', 'plus_minus_semantics': 'unknown;not silently SD/SE/CI',
                          'selected_sample_count': None, 'native_supported_quantity': False, 'native_status': 'research_lead_only;requiresseparateendpointcontractsandmappingreview'})
    assert len(leads) == 28
    write('TGA_SOURCE_LEADS_R1.json', {'schema': 'existing-PUR-TGA-research-leads/1', 'source_id': sid, 'facts': leads, 'count': len(leads), 'method': {'locator': 'PDF p8 §2.8 lastthermalparagraph; p20Figure16/Table11', 'apparatus': 'TA Instruments Discovery TGA withautosampler', 'holder': 'platinum scale pans', 'program': '30–700°C at10°C/min in nitrogen', 'common_parallel_samples_statement': 'Three or more parallel samples examined and tested,within TGAparagraph', 'selected_n_adjudication': 'Keepunknown;statement is not exact3,not unambiguouslyeachselectedcell contributor count orindependentbatchcount', 'software': ['TA Instruments TRIOS5.0.0.44608', 'OriginPro2021 9.8.0.200'], 'unknowns': ['sample mass/dimensions/location', 'nitrogen flow/purity', 'RH/preconditioning/drying/gasageing', 'heating calibration and baseline corrections', 'onset tangent/threshold definition', 'DTG derivative/smoothing/peak-selection method', 'percentage normalization initial/dry basis', 'centre aggregation andplus-minus definition']}, 'endpoint_boundaries': ['Tm5%/Tm10% are mass-loss endpoint temperatures,not melting peaks', 'DTGpeak1/2/3 retain distinctsource ordinals;not service-temperature maxima or interchangeable Tg', 'Residue700C is source TGA residue percentage,not certified ash content ormassdensity;normalization basis remainsunknown', 'No automatic conversion of percent to0–1 fractions', 'SPO2 T5%=139C below firstonset149C preserved;unknown onset criterion doesnot permit ordering-based repair', 'First TGA onset may include source-described low-molecular/additive volatilization;not intrinsic neat-polymer decomposition,service-temperature limit or mechanical failure temperature.', 'Do not digitize Figure14 normalizedcompression orotherplot coordinates'], 'native_applied': False, 'new_native_records': 0, 'contract_implementation': 'not_started', 'pushed': False})
    write('EXTRACTION_CAUTION_R1.json', {'scope': 'Local PDF text extraction is a locator,not independent numeric authority', 'observation': 'Pages19–20 extractedtext duplicates some embedded graphic/draft-page text. Visible finalpage number,figurepanel,legend andprintedannotations govern;Table11 XMLrow parsedonce.', 'visuals': ['page-visual-19.png', 'page-visual-20.png'], 'paper_assets_bundled': False})
    proposed = deepcopy(source)
    proposed['claim_notes'].append('2026-11-04 additionalPURthermal source followup: sameofficial23pagePDF SHA256 ' + sha(pdf) + ',visiblepages19–20 checked againstXMLmethod/Figure15caption/Table11. Four existingidentity DMA tan-delta peak annotations126/116/125/137C are sourcecandidates only;compression-oscillation cylindersapprox13mm×7mm,1Hz,5um,maximum1N,25–220C at3C/min. n,estimator,dispersion,preload,cycle,RH andloadingdirection relative tofoamrise unknown;TGA3ormore notDMA n. DSCparagraph LPOdetection conflict preserved;Table11 28selectedTGAcell facts remainunadmitted endpointleads withunknownplusminus. No curve digitization,newidentity,sourceassetredistribution orengineinput.')
    changed = [n for n in source if proposed[n] != source[n]]
    assert changed == ['claim_notes']
    data = deepcopy(db.data['sources'])
    data['records'][data['records'].index(source)] = proposed
    Draft202012Validator(read(ROOT / 'schemas/sources.schema.json'), format_checker=FormatChecker()).validate(data)
    write('SOURCE_UPDATE_PROPOSAL_R1.json', {'status': 'unapplied_source_note_proposal', 'source_id': sid, 'baseline_source': source, 'proposed_source': proposed, 'changed_fields': changed, 'native_applied': False})
    write('VALIDATION_R1.json', {'scope': 'Producer sourcefacts only;not independentreview or nativeadmission', 'baseline_snapshot': db.snapshot, 'DMA_annotation_candidates': 4, 'DMA_numbers_from_visible_PDF_not_XML_text': True, 'XML_caption_and_method_checked': True, 'TGA_cells_parsed_once': 28, 'DSC_selected_leads_held': 2, 'existing8_source_properties_unchanged': True, 'source_note_schema_format': 'passed', 'runtime_schema_changed': False, 'native_applied': False, 'tests_install_fullgraph_history': 'not_run_sourceproposalonly', 'pushed': False})
    print(json.dumps({'DMA_candidates': 4, 'DSC_held': 2, 'TGA_research_leads': 28, 'source_note_schema': 'passed', 'native_changed': False}))


if __name__ == '__main__':
    main()
