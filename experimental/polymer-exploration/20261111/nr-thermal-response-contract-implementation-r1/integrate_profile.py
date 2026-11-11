"""Integrate the source-approved scalar time and cited-method fit contract."""
from pathlib import Path
from copy import deepcopy
import hashlib,json,shutil,sys
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
SOURCE=HERE.parent/'nr-notice-damping-source-followup-r1'
EXT=ROOT.parent/'open-database-evidence/polymer-thermal-response-contract-20261111-r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def put(p,s):p.write_text(s,encoding='utf-8',newline='\n')
def main():
    entry=SOURCE/'REVIEW_INPUTS_R1.json';review=read(SOURCE/'INDEPENDENT_SOURCE_CONCEPT_REVIEW_R1.json')
    assert review['decision']=='approved' and review['review_inputs_sha256']==sha(entry)
    for field in ('repo_files_sha256','native_files_sha256','external_files_sha256'):
        for n,h in read(entry)[field].items():assert sha(Path(n) if field=='external_files_sha256' else ROOT/n)==h,n
    names=['materials_boundaries/_material_derivation.py','materials_boundaries/material_references.py','materials_boundaries/material_presentation.py','materials_boundaries/data/material_locales.json','schemas/materials.schema.json','schemas/reference_properties.schema.json']
    baseline=EXT/'baseline';baseline.mkdir(parents=True,exist_ok=False)
    for n in names:
        p=baseline/n;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/n,p)
    old=read(ROOT/'schemas/reference_properties.schema.json')
    p=ROOT/names[0];text=p.read_text('utf-8');profile=(HERE/'fit_profile.py').read_text('utf-8');profile=profile[profile.index('FIT_PROFILE='):]
    text+='\n\n'+profile
    marker="_thermal_product_definition(text,https,null,obj,array,enum)]}"
    assert text.count(marker)==1;text=text.replace(marker,"_thermal_product_definition(text,https,null,obj,array,enum),_thermal_fit_definition(text,https,null,obj,array,enum)]}")
    marker="    derived=prop.get('derivation')\n    if (prop['method_definition']['type']==TRANSPORT_METHOD"
    assert text.count(marker)==1
    text=text.replace(marker,"    derived=prop.get('derivation')\n    if (prop['quantity']==FIT_QUANTITY or prop['method_definition']['type']==FIT_METHOD or\n        isinstance(derived,dict) and derived.get('profile_id')==FIT_PROFILE):\n        _validate_thermal_fit(prop,sources)\n        return\n    if (prop['method_definition']['type']==TRANSPORT_METHOD")
    put(p,text)
    p=ROOT/names[1];text=p.read_text('utf-8')
    def change(a,b):
        nonlocal text
        assert text.count(a)==1,(a,text.count(a));text=text.replace(a,b)
    change('WORK_UNITS =','RESPONSE_TIME_UNITS = ("s", "ms")\nWORK_UNITS =')
    change('QUANTITY_DIMENSIONS = {','QUANTITY_DIMENSIONS = {\n    "thermal_response_characteristic_time": "time",')
    change('UNIT_DIMENSIONS = {','UNIT_DIMENSIONS = {\n    **{u: "time" for u in RESPONSE_TIME_UNITS},')
    change('code not in (*WORK_UNITS, *HEAT_CAPACITY_UNITS, *DIFFUSIVITY_UNITS)','code not in (*RESPONSE_TIME_UNITS, *WORK_UNITS, *HEAT_CAPACITY_UNITS, *DIFFUSIVITY_UNITS)')
    change('code not in {*HEAT_CAPACITY_UNITS,','code not in {*RESPONSE_TIME_UNITS, *HEAT_CAPACITY_UNITS,')
    change('if quantity not in {*THERMAL_NEW_QUANTITIES,','if quantity not in {"thermal_response_characteristic_time", *THERMAL_NEW_QUANTITIES,')
    change('if q not in {*THERMAL_NEW_QUANTITIES,','if q not in {"thermal_response_characteristic_time", *THERMAL_NEW_QUANTITIES,')
    change('"source_reported_thermal_transport_product",','"source_reported_thermal_transport_product", "source_reported_thermal_response_fit",')
    marker='    definitions["property"] = {"oneOf": [other, stress, elongation, shore, temperature, electric, thermal, *tga_branches, work, *new_thermal]}'
    change(marker,'''    definitions["thermal_response_phase"] = _object({"code": _enum(("post_stretching_hold", "post_retraction_recovery")), "evidence": evidence, "notes": TEXT})
    definitions["thermal_convection"] = {"oneOf": [
        _object({"status": {"const": "reported"}, "regime": _enum(("natural_convection", "forced_convection")), "evidence": evidence, "notes": TEXT}),
        _object({"status": _enum(("not_reported_in_inspected_source", "not_verified")), "regime": NULL, "evidence": _array(_ref("evidence"), 0), "notes": TEXT}),
    ]}
    scalar = next(deepcopy(v) for v in definitions["reported_value"]["oneOf"] if v["properties"]["kind"].get("const") == "scalar")
    scalar["properties"]["unit_code"] = _enum(RESPONSE_TIME_UNITS)
    definitions["thermal_response_reported_value"] = scalar
    response = deepcopy(new_thermal[-1])
    response["properties"].update(quantity={"const": "thermal_response_characteristic_time"}, quantity_dimension={"const": "time"}, reported_value=_ref("thermal_response_reported_value"), thermal_response_phase=_ref("thermal_response_phase"), thermal_convection=_ref("thermal_convection"))
    response["required"].extend(("thermal_response_phase", "thermal_convection"))
    definitions["property"] = {"oneOf": [other, stress, elongation, shore, temperature, electric, thermal, *tga_branches, work, *new_thermal, response]}''')
    change('_UNIT_SPELLINGS = {','_UNIT_SPELLINGS = {\n    "s": {"s"}, "ms": {"ms"},')
    change('    if is_derived != (is_crystallographic or is_empirical or is_thermal_product):','    is_thermal_fit = method == "source_reported_thermal_response_fit"\n    if is_derived != (is_crystallographic or is_empirical or is_thermal_product or is_thermal_fit):')
    change('        "specified_elongation": elongation_key,','''        "specified_elongation": elongation_key,
        **({"thermal_response": [prop["thermal_response_phase"]["code"],
            prop["thermal_convection"]["regime"] if prop["thermal_convection"]["status"] == "reported" else "unknown"]}
            if "thermal_response_phase" in prop else {}),''')
    put(p,text)
    p=ROOT/names[2];text=p.read_text('utf-8')
    text=text.replace('def material_labels(','''REQUIRED_LABELS |= frozenset(('code_thermal_response_characteristic_time','thermal_response_phase','code_post_stretching_hold','code_post_retraction_recovery','thermal_convection','code_natural_convection','code_forced_convection','code_source_reported_thermal_response_fit','thermal_response_fit_notice','thermal_response_derivation'))


def material_labels(''',1)
    marker='        if "thermal_mass_reference_basis" in prop:';assert text.count(marker)==1
    text=text.replace(marker,'''        if "thermal_response_phase" in prop:
            phase=prop["thermal_response_phase"];boundary=prop["thermal_convection"]
            output.append(field("thermal_response_phase",code(phase["code"]),indent+"    "))
            output.append(field("scope",phase["notes"],indent+"    "))
            output.extend(evidence(phase["evidence"],indent+"      "))
            output.append(field("thermal_convection",code(boundary["regime"] if boundary["status"]=="reported" else boundary["status"]),indent+"    "))
            output.append(field("scope",boundary["notes"],indent+"    "))
            output.extend(evidence(boundary["evidence"],indent+"      "))
'''+marker)
    marker='''            output.append(indent + "  " + labels["source_product_notice" if product else "derived_notice"])
            output.append(field("source_product_derivation" if product else "derivation", raw(prop["derivation"]), indent + "  "))'''
    assert text.count(marker)==1
    text=text.replace(marker,'''            fit = prop["method_definition"]["type"] == "source_reported_thermal_response_fit"
            output.append(indent + "  " + labels["thermal_response_fit_notice" if fit else "source_product_notice" if product else "derived_notice"])
            output.append(field("thermal_response_derivation" if fit else "source_product_derivation" if product else "derivation", raw(prop["derivation"]), indent + "  "))''')
    put(p,text)
    p=ROOT/names[3];locales=read(p)
    keys=['code_thermal_response_characteristic_time','thermal_response_phase','code_post_stretching_hold','code_post_retraction_recovery','thermal_convection','code_natural_convection','code_forced_convection','code_source_reported_thermal_response_fit','thermal_response_fit_notice','thermal_response_derivation']
    labels={
      'en':['Thermal response characteristic time','Thermal response phase','Post-stretching hold','Post-retraction recovery','Thermal convection boundary','Source-labelled natural convection','Source-labelled forced convection','Source-reported thermal response fit','Source-fitted1/e temperature-deviation time,dependent on geometry and convection;not intrinsic mechanical relaxation,half-life or full cycle duration. Cited-method assumptions do not certify current applicability. Raw curves,fit settings,aggregation and statistics remain source-qualified;no software refit or inverse calculation.','Source fit and cited-method provenance'],
      'zh':['温度响应特征时间','温度响应阶段','拉伸后保持阶段','回缩后恢复阶段','热对流边界','来源标注自然对流','来源标注强制对流','来源报告的温度响应拟合','来源拟合的1/e温差衰减时间，依赖几何和对流，不是固有机械松弛时间、半衰期或完整循环时长。引用模型假设不认证当前实验适用；原始曲线、拟合设置、汇总与统计按来源保留，不重拟合或反演。','来源拟合及引用方法溯源'],
      'ja':['温度応答の特性時間','温度応答段階','伸長後の保持','収縮後の回復','熱対流境界','出典表記の自然対流','出典表記の強制対流','出典の温度応答フィット','幾何形状と対流に依存する出典の1/e温度差減衰時間。固有の機械緩和時間、半減期、全サイクル時間ではない。引用モデルの仮定は現試験の適用性を保証しない。生曲線、設定、集計と統計は出典限定で保持し、再フィットや逆算を行わない。','出典フィットと引用手法の由来'],
      'de':['Charakteristische Temperaturantwortzeit','Phase der Temperaturantwort','Haltephase nach Dehnung','Erholung nach Rückzug','Konvektive Randbedingung','In der Quelle natürliche Konvektion','In der Quelle erzwungene Konvektion','In der Quelle angepasste Temperaturantwort','Quellenangepasste1/e-Zeit der Temperaturdifferenz,abhängig von Geometrie und Konvektion;keine intrinsische mechanische Relaxationszeit,Halbwertszeit oder ganze Zyklusdauer. Modellannahmen zertifizieren die aktuelle Anwendbarkeit nicht. Rohkurven,Einstellungen,Aggregation und Statistik bleiben quellengebunden;keine Neuanpassung oder Inversion.','Quellenanpassung und zitierte Methodenherkunft']}
    for lang,values in labels.items():
        assert len(values)==len(keys)
        for k,v in zip(keys,values):assert k not in locales['languages'][lang];locales['languages'][lang][k]=v
    put(p,json.dumps(locales,ensure_ascii=False,indent=2)+'\n')
    sys.path.insert(0,str(ROOT))
    from materials_boundaries.material_references import _PROPERTIES_SCHEMA,_MATERIALS_SCHEMA
    current=_PROPERTIES_SCHEMA
    assert current['$defs']['derivation']['oneOf'][:2]==old['$defs']['derivation']['oneOf']
    assert len(current['$defs']['property']['oneOf'])==15
    for a,b in zip(old['$defs']['property']['oneOf'],current['$defs']['property']['oneOf'][:14]):
        b=deepcopy(b);methods=b['properties']['method_definition']['properties']['type']['enum'];methods.remove('source_reported_thermal_response_fit');assert a==b
    assert current['$defs']['legacy_reported_value']==old['$defs']['legacy_reported_value']
    for n,schema in [('materials',_MATERIALS_SCHEMA),('reference_properties',_PROPERTIES_SCHEMA)]:put(ROOT/f'schemas/{n}.schema.json',json.dumps(schema,ensure_ascii=False,indent=2)+'\n')
    assert all(sha(ROOT/n)==h for n,h in read(entry)['native_files_sha256'].items())
    with (HERE/'INTEGRATION_R1.json').open('x',encoding='utf-8',newline='\n') as f:json.dump(dict(old14branches_unchanged_except_new_method=True,old_two_derivation_profiles_exact=True,legacy_value_domain_exact=True,native_tables_unchanged=True,tests='not_run',mapping='not_prepared'),f,indent=2);f.write('\n')
    print('Time/phase/convection/two-source fit contract wired;old14branches and2profiles retained;native unchanged')
if __name__=='__main__':main()
