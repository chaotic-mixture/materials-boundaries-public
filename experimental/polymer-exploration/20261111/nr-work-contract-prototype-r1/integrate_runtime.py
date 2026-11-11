"""Integrate approved work concept; no native records or Git writes."""
from pathlib import Path
import json
import sys
ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent


def main():
    path = ROOT / 'materials_boundaries/material_references.py'
    text = path.read_text(encoding='utf-8')
    assert 'WORK_UNITS' not in text
    def replace(old, new):
        nonlocal text
        assert text.count(old) == 1, old
        text = text.replace(old, new)
    replace('QUANTITY_DIMENSIONS = {', 'WORK_UNITS = ("J/cm^3", "MJ/m^3", "J/m^3")\nQUANTITY_DIMENSIONS = {\n    "volumetric_tensile_work_to_break": "energy_per_volume",')
    replace('UNIT_DIMENSIONS = {', 'UNIT_DIMENSIONS = {\n    **{unit: "energy_per_volume" for unit in WORK_UNITS},')
    replace('if quantity not in {"dielectric_breakdown_strength", "thermal_conductivity"}', 'if quantity not in {"dielectric_breakdown_strength", "thermal_conductivity", "volumetric_tensile_work_to_break"}')
    replace('if code != "percent_tga_residue")', 'if code != "percent_tga_residue" and code not in WORK_UNITS)')
    replace('if code not in {"percent_tga_residue",', 'if code not in {*WORK_UNITS, "percent_tga_residue",')
    replace('*TEMPERATURE_QUANTITIES, *TGA_QUANTITIES}', '*TEMPERATURE_QUANTITIES, *TGA_QUANTITIES, "volumetric_tensile_work_to_break"}')
    old='    definitions["property"] = {"oneOf": [other, stress, elongation, shore, temperature, electric, thermal, *tga_branches]}'
    new='''    definitions["work_reference_basis"] = {"oneOf": deepcopy(definitions["fact"]["oneOf"][:3])}
    definitions["work_reported_value"] = deepcopy(definitions["reported_value"])
    for value in definitions["work_reported_value"]["oneOf"]:
        value["properties"]["unit_code"] = _enum(WORK_UNITS)
    work = deepcopy(other)
    work["properties"]["quantity"] = {"const": "volumetric_tensile_work_to_break"}
    work["properties"]["quantity_dimension"] = {"const": "energy_per_volume"}
    work["properties"]["reported_value"] = _ref("work_reported_value")
    work["properties"]["work_reference_basis"] = _ref("work_reference_basis")
    work["required"].append("work_reference_basis")
    definitions["property"] = {"oneOf": [other, stress, elongation, shore, temperature, electric, thermal, *tga_branches, work]}'''
    replace(old,new)
    replace('_UNIT_SPELLINGS = {', '_UNIT_SPELLINGS = {\n    "J/cm^3": {"J/cm^3", "J/cm³", "J/cm3"},\n    "MJ/m^3": {"MJ/m^3", "MJ/m³", "MJ/m3"},\n    "J/m^3": {"J/m^3", "J/m³", "J/m3"},')
    replace('{"shore_a_hardness", "tga_residue_percentage"}))', '{"shore_a_hardness", "tga_residue_percentage", "volumetric_tensile_work_to_break"}))')
    replace('    if prop["quantity"] == "shore_a_hardness":', '''    if "work_reference_basis" in prop:
        basis = prop["work_reference_basis"]
        if basis["status"] == "reported":
            _require_tag(basis["evidence"], "condition", path + ".work_reference_basis", source)
            if not any(e["url"] == prop["source_document"]["url"] for e in _tagged(basis["evidence"], "condition", source)):
                _fail(path, "Work basis needs primary inspected-document condition evidence")
        elif not basis["notes"]:
            _fail(path, "Unknown work reference basis needs an explanatory note")
    if prop["quantity"] == "shore_a_hardness":''')
    replace('        "specified_elongation": elongation_key,', '''        "specified_elongation": elongation_key,
        **({"work_basis": (["reported", prop["work_reference_basis"]["text"]]
                           if prop["work_reference_basis"]["status"] == "reported" else ["unknown", None])}
           if "work_reference_basis" in prop else {}),''')
    # Only write after all exact replacement guards have passed.
    path.write_text(text, encoding='utf-8', newline='\n')
    sys.path.insert(0,str(ROOT))
    from materials_boundaries.material_references import _PROPERTIES_SCHEMA
    before = json.loads((ROOT.parent / 'open-database-evidence/polymer-nr-work-contract-20261111-r1/baseline/schemas/reference_properties.schema.json').read_bytes())
    assert before['$defs']['property']['oneOf'] == _PROPERTIES_SCHEMA['$defs']['property']['oneOf'][:11]
    assert before['$defs']['legacy_reported_value'] == _PROPERTIES_SCHEMA['$defs']['legacy_reported_value']
    (ROOT/'schemas/reference_properties.schema.json').write_text(json.dumps(_PROPERTIES_SCHEMA,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    presentation = ROOT/'materials_boundaries/material_presentation.py'
    text = presentation.read_text(encoding='utf-8')
    text = text.replace('LANGUAGES = ("en", "zh", "ja", "de")', 'LANGUAGES = ("en", "zh", "ja", "de")\nWORK_LABELS = ("code_volumetric_tensile_work_to_break", "work_reference_basis", "work_reference_notice")',1)
    marker='REQUIRED_LABELS |= frozenset(("specified_mass_loss",'
    assert marker in text
    text=text.replace(marker,'REQUIRED_LABELS |= frozenset(WORK_LABELS)\n'+marker,1)
    marker='        if "mass_reference_basis" in prop:'
    assert text.count(marker)==1
    text=text.replace(marker,'''        if "work_reference_basis" in prop:
            output.extend(fact("work_reference_basis", prop["work_reference_basis"], indent + "    "))
            output.append(indent + "    " + labels["work_reference_notice"])
'''+marker)
    presentation.write_text(text,encoding='utf-8',newline='\n')
    path=ROOT/'materials_boundaries/data/material_locales.json';locales=json.loads(path.read_bytes())
    labels={'en':['Volumetric tensile work to break','Work reference volume basis','Source-reported work only; volume and stress/strain conventions may be unknown. Not recoverable elastic energy, caloric heat or an allowable.'],
    'zh':['体积归一化拉伸断裂功','断裂功参考体积基准','仅为来源报告的断裂功；体积与应力/应变口径可未知，不代表可恢复弹性能、制冷热量或工程允许值。'],
    'ja':['体積当たりの引張破断仕事','仕事の参照体積基準','出典の破断仕事のみ。体積と応力・ひずみ規約は不明の場合があります。回復可能な弾性エネルギー、熱量、許容値ではありません。'],
    'de':['Volumenbezogene Zugbrucharbeit','Bezugsvolumen der Arbeit','Nur Quellenwert; Volumen- und Spannungs-/Dehnungskonvention können unbekannt sein. Keine rückgewinnbare elastische Energie, Wärmemenge oder zulässiger Wert.']}
    for lang,values in labels.items():locales['languages'][lang].update(dict(zip(['code_volumetric_tensile_work_to_break','work_reference_basis','work_reference_notice'],values)))
    path.write_text(json.dumps(locales,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('Production contract wired:12branches,old11equal;native records untouched;regressions pending')


if __name__=='__main__':main()
