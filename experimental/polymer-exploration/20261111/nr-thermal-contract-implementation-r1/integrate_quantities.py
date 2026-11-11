"""Implement only heat-capacity/diffusivity contracts,not conductivity lineage."""
from pathlib import Path
import hashlib,json,shutil,sys
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
EXT=ROOT.parent/'open-database-evidence/polymer-nr-thermal-contract-20261111-r1'
def main():
    EXT.mkdir(exist_ok=False)
    names=['materials_boundaries/material_references.py','materials_boundaries/material_presentation.py','materials_boundaries/data/material_locales.json','schemas/reference_properties.schema.json']
    hashes={}
    for name in names:
        p=EXT/'baseline'/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,p);hashes[name]=hashlib.sha256(p.read_bytes()).hexdigest()
    p=ROOT/names[0];text=p.read_text(encoding='utf-8')
    def change(old,new):
        nonlocal text
        assert text.count(old)==1,old
        text=text.replace(old,new)
    change('WORK_UNITS = ', 'HEAT_CAPACITY_UNITS = ("J/(g*K)", "J/(kg*K)", "kJ/(kg*K)")\nDIFFUSIVITY_UNITS = ("mm^2/s", "m^2/s")\nTHERMAL_NEW_QUANTITIES = ("mass_specific_heat_capacity", "thermal_diffusivity")\nWORK_UNITS = ')
    change('QUANTITY_DIMENSIONS = {','QUANTITY_DIMENSIONS = {\n    "mass_specific_heat_capacity": "energy_per_mass_temperature",\n    "thermal_diffusivity": "area_per_time",')
    change('UNIT_DIMENSIONS = {','UNIT_DIMENSIONS = {\n    **{u: "energy_per_mass_temperature" for u in HEAT_CAPACITY_UNITS},\n    **{u: "area_per_time" for u in DIFFUSIVITY_UNITS},')
    change('and code not in WORK_UNITS)', 'and code not in (*WORK_UNITS, *HEAT_CAPACITY_UNITS, *DIFFUSIVITY_UNITS))')
    change('if code not in {*WORK_UNITS,','if code not in {*HEAT_CAPACITY_UNITS, *DIFFUSIVITY_UNITS, *WORK_UNITS,')
    change('if quantity not in {"dielectric_breakdown_strength",','if quantity not in {*THERMAL_NEW_QUANTITIES, "dielectric_breakdown_strength",')
    change('if q not in {"thermal_conductivity",','if q not in {*THERMAL_NEW_QUANTITIES, "thermal_conductivity",')
    old='    definitions["property"] = {"oneOf": [other, stress, elongation, shore, temperature, electric, thermal, *tga_branches, work]}'
    new='''    definitions["thermal_mass_reference_basis"] = {"oneOf": deepcopy(definitions["fact"]["oneOf"][:3])}
    new_thermal = []
    for quantity, units in (("mass_specific_heat_capacity", HEAT_CAPACITY_UNITS), ("thermal_diffusivity", DIFFUSIVITY_UNITS)):
        value_name = quantity + "_reported_value"
        definitions[value_name] = deepcopy(definitions["reported_value"])
        for value in definitions[value_name]["oneOf"]:
            value["properties"]["unit_code"] = _enum(units)
        branch = deepcopy(other)
        branch["properties"]["quantity"] = {"const": quantity}
        branch["properties"]["quantity_dimension"] = {"const": QUANTITY_DIMENSIONS[quantity]}
        branch["properties"]["reported_value"] = _ref(value_name)
        if quantity == "mass_specific_heat_capacity":
            branch["properties"]["thermal_mass_reference_basis"] = _ref("thermal_mass_reference_basis")
            branch["required"].append("thermal_mass_reference_basis")
        new_thermal.append(branch)
    definitions["property"] = {"oneOf": [other, stress, elongation, shore, temperature, electric, thermal, *tga_branches, work, *new_thermal]}'''
    change(old,new)
    change('_UNIT_SPELLINGS = {','_UNIT_SPELLINGS = {\n    "J/(g*K)": {"J/(g*K)", "J/(g·K)", "J/g·K"},\n    "J/(kg*K)": {"J/(kg*K)", "J/(kg·K)"},\n    "kJ/(kg*K)": {"kJ/(kg*K)", "kJ/(kg·K)"},\n    "mm^2/s": {"mm^2/s", "mm²/s", "mm2/s"},\n    "m^2/s": {"m^2/s", "m²/s", "m2/s"},')
    change('    if "work_reference_basis" in prop:', '''    if "thermal_mass_reference_basis" in prop:
        basis = prop["thermal_mass_reference_basis"]
        if basis["status"] == "reported":
            _require_tag(basis["evidence"], "condition", path + ".thermal_mass_reference_basis", source)
            if not any(e["url"] == prop["source_document"]["url"] for e in _tagged(basis["evidence"], "condition", source)):
                _fail(path, "Thermal mass basis needs primary inspected-document condition evidence")
        elif not basis["notes"]:
            _fail(path, "Unknown thermal mass basis needs an explanatory note")
    if "work_reference_basis" in prop:''')
    change('        "specified_elongation": elongation_key,','''        "specified_elongation": elongation_key,
        **({"thermal_mass_basis": (["reported", prop["thermal_mass_reference_basis"]["text"]]
                  if prop["thermal_mass_reference_basis"]["status"] == "reported" else ["unknown", None])}
           if "thermal_mass_reference_basis" in prop else {}),''')
    p.write_text(text,encoding='utf-8',newline='\n')
    sys.path.insert(0,str(ROOT))
    from materials_boundaries.material_references import _PROPERTIES_SCHEMA
    old=json.loads((EXT/'baseline/schemas/reference_properties.schema.json').read_bytes())
    assert old['$defs']['property']['oneOf']==_PROPERTIES_SCHEMA['$defs']['property']['oneOf'][:12]
    assert old['$defs']['legacy_reported_value']==_PROPERTIES_SCHEMA['$defs']['legacy_reported_value']
    (ROOT/'schemas/reference_properties.schema.json').write_text(json.dumps(_PROPERTIES_SCHEMA,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    p=ROOT/names[1];text=p.read_text(encoding='utf-8')
    text=text.replace('REQUIRED_LABELS |= frozenset(WORK_LABELS)','REQUIRED_LABELS |= frozenset(WORK_LABELS)\nREQUIRED_LABELS |= frozenset(("code_mass_specific_heat_capacity", "code_thermal_diffusivity", "thermal_mass_reference_basis"))',1)
    marker='        if "work_reference_basis" in prop:';assert text.count(marker)==1
    text=text.replace(marker,'        if "thermal_mass_reference_basis" in prop:\n            output.extend(fact("thermal_mass_reference_basis", prop["thermal_mass_reference_basis"], indent + "    "))\n'+marker)
    p.write_text(text,encoding='utf-8',newline='\n')
    p=ROOT/names[2];locales=json.loads(p.read_bytes())
    labels={'en':['Mass-specific heat capacity','Thermal diffusivity','Thermal reference mass basis'],'zh':['质量比热','热扩散率','热性质参考质量基准'],'ja':['質量比熱容量','熱拡散率','熱特性の参照質量基準'],'de':['Massenspezifische Wärmekapazität','Temperaturleitfähigkeit','Bezugsmasse der thermischen Eigenschaft']}
    for lang,values in labels.items():locales['languages'][lang].update(dict(zip(['code_mass_specific_heat_capacity','code_thermal_diffusivity','thermal_mass_reference_basis'],values)))
    p.write_text(json.dumps(locales,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    with (HERE/'INTEGRATION_R1.json').open('x',encoding='utf-8') as f:json.dump(dict(old12branches_equal=True,legacy_value_equal=True,baseline_sha256=hashes,conductivity_profile='not_implemented',native_records_changed=False,tests='pending'),f,indent=2)
    print('Two quantities wired;old12branches retained;conductivity profile and native records untouched')
if __name__=='__main__':main()
