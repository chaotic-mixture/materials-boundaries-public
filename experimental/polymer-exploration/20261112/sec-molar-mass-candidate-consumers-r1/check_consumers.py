"""Complete candidate records and scoped four-language views, no native writes."""
from copy import deepcopy
import hashlib,json,sys
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from materials_boundaries.database import Database,read_snapshot
from materials_boundaries.material_presentation import render_material_catalog,material_labels
from materials_boundaries._sec_molar_mass_contract import MOMENTS,DISPERSITY,MOMENT_UNITS,RATIO_UNIT


def main():
    mapping=HERE.parent/'sec-molar-mass-native-mapping-r1'
    external=ROOT.parent/'open-database-evidence/polymer-sec-molar-mass-candidate-consumers-20261112-r1'
    external.mkdir(exist_ok=False)
    load=lambda p:json.loads(p.read_bytes())
    before=Database();data=deepcopy(before.data)
    newprops=load(mapping/'NEW_PROPERTIES_R1.json');newstates=load(mapping/'NEW_STATES_R1.json')
    data['materials']['records'].extend(newstates);data['reference_properties']['records'].extend(newprops)
    db=Database(data);assert db.snapshot==load(mapping/'VALIDATION_R1.json')['candidate_snapshot']
    checks=[]
    for name,filters,count in [('sec-three',dict(query=newstates[0]['id']),3),('phbv-identity-all',dict(query='mat_abbasi2022_manure_phbv39'),15),('phbv-source-all',dict(source='abbasi_2022_manure_phbv'),15)]:
        rows=list(db.records(**filters));assert len(rows)==count
        expected=deepcopy({r['record_id']:r for r in rows})
        db.export(external/name,**filters);assert read_snapshot(external/name)[1]==expected
        for row in rows:
            assert row['property']==db.properties[row['record_id']]
            assert row['state']==db.states[row['property']['material_state_id']]
        rows[0]['property']['scope_note']='detached probe'
        assert {r['record_id']:r for r in db.records(**filters)}==expected
        checks.append(dict(group=name,records=count,full_candidate_query_export_restore_equal=True,copy_isolation=True))
    expectedvalues=dict(zip((*MOMENTS,DISPERSITY),(('6.96','0.38'),('6.45','0.32'),('1.08','0.08'))))
    for p in newprops:
        assert (p['reported_value']['number'],p['uncertainty']['number'])==expectedvalues[p['quantity']]
        assert p['summary_statistic']=='reported_mean' and p['uncertainty_status']=='reported_standard_deviation'
        assert p['sample_count']['value'] is None and p['sample_count']['relation']=='not_reported'
        assert p['reported_value']['unit_code']==p['uncertainty']['unit_code']==(RATIO_UNIT if p['quantity']==DISPERSITY else MOMENT_UNITS[2])
        assert p['sec_definition']['origin']['status']=='explicitly_reproduced_from_cited_work'
        assert p['sec_definition']['origin']['original_result']['status']=='not_verified'
        assert p['sec_definition']['measurement_basis']['status']=='not_verified'
        assert all(f['status']=='not_verified' for f in p['sec_definition']['actual_original_result_context'].values())
    rows=list(db.records(query=newstates[0]['id']));assert all(r['identity']['category']=='polymer' for r in rows)
    scoped=dict(materials=dict(schema_version=data['materials']['schema_version'],identities=[deepcopy(rows[0]['identity'])],grades=[],records=deepcopy(newstates)),
                reference_properties=dict(schema_version=data['reference_properties']['schema_version'],records=deepcopy(newprops)),
                sources=dict(schema_version=data['sources']['schema_version'],records=deepcopy(rows[0]['sources'])))
    languages=[]
    for language in ('en','zh','ja','de'):
        with patch('materials_boundaries.catalog.read_catalog',side_effect=lambda name:deepcopy(scoped[name])):
            rendered=render_material_catalog(scoped['reference_properties'],'reference-properties',language)
        labels=material_labels(language)
        for key in ('sec_reported_common_context','sec_actual_original_context','code_explicitly_reproduced_from_cited_work','sec_origin','code_not_verified'):
            assert labels[key] in rendered
        assert '×10⁵ g·mol⁻¹' in rendered and '10.1016/j.biteb.2020.100588' in rendered
        assert 'source_sec_molar_mass_dispersity_v1' not in rendered
        (external/('view-'+language+'.txt')).write_text(rendered,encoding='utf-8',newline='\n')
        languages.append(language)
    receipt=dict(snapshot=db.snapshot,groups=checks,scoped_languages=languages,
                 external_files_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in external.rglob('*') if p.is_file()},
                 native_applied=False,installation='not_run',scope='Candidate3/15/15 fullobjects and scoped3property4language views only;not independent scientific review,new experiment or source recomputation')
    with (HERE/'CONSUMERS_R1.json').open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(groups=checks,languages=languages)),flush=True)


if __name__=='__main__':main()
