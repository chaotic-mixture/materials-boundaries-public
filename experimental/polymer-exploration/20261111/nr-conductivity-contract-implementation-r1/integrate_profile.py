"""Integrate a reviewed source-product profile,archiving exact previous bytes."""
from pathlib import Path
from copy import deepcopy
import hashlib,json,shutil,sys
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
PROTO=HERE.parent/'nr-conductivity-provenance-prototype-r1'
EXT=ROOT.parent/'open-database-evidence/polymer-nr-conductivity-contract-20261111-r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def put(p,text):p.write_text(text,encoding='utf-8',newline='\n')
def main():
    entry=PROTO/'REVIEW_INPUTS_R1.json';review=read(PROTO/'INDEPENDENT_PROTOTYPE_REVIEW_R1.json')
    assert review['decision']=='approved' and review['review_inputs_sha256']==sha(entry)
    pins=read(entry)
    for field in ('repo_files_sha256','native_files_sha256','external_files_sha256'):
        for n,h in pins[field].items():assert sha(Path(n) if field=='external_files_sha256' else ROOT/n)==h,n
    names=['materials_boundaries/_material_derivation.py','materials_boundaries/material_references.py','materials_boundaries/material_presentation.py','materials_boundaries/data/material_locales.json','schemas/reference_properties.schema.json','tests/test_tga_endpoint_contract.py']
    baseline=EXT/'baseline';baseline.mkdir(parents=True,exist_ok=False)
    before={n:sha(ROOT/n) for n in names}
    for n in names:
        target=baseline/n;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/n,target);assert sha(target)==before[n]
    old_schema=read(ROOT/'schemas/reference_properties.schema.json')
    code=(PROTO/'transport_profile.py').read_text('utf-8');code=code[code.index('PROFILE='):]
    for name in ('PROFILE','METHOD','KIND','EXPRESSION','ROLES','UNKNOWNS'):
        import re
        code=re.sub(r'\b'+name+r'\b','TRANSPORT_'+name,code)
    code=code.replace('def definition(','def _thermal_product_definition(').replace('def validate(prop):','def _validate_thermal_product(prop):')
    p=ROOT/names[0];text=p.read_text('utf-8')
    assert text.count('def definitions(')==1 and text.count('def validate_derivation(')==1
    text=text.replace('def definitions(','def _wood_definitions(',1).replace('def validate_derivation(','def _validate_empirical_derivation(',1)
    text+='\n\n'+code+'''

def definitions(text,decimal,https,null,obj,array,enum):
    result=_wood_definitions(text,decimal,https,null,obj,array,enum)
    result['derivation']={'oneOf':[result['derivation'],_thermal_product_definition(text,https,null,obj,array,enum)]}
    return result


def validate_derivation(prop,identity=None,sources=None):
    derived=prop.get('derivation')
    if (prop['method_definition']['type']==TRANSPORT_METHOD or
        isinstance(derived,dict) and derived.get('profile_id')==TRANSPORT_PROFILE):
        _validate_thermal_product(prop)
        return
    _validate_empirical_derivation(prop,identity,sources)
'''
    put(p,text)
    p=ROOT/names[1];text=p.read_text('utf-8')
    old='"source_reported_crystallographic_derivation", "source_reported_empirical_conversion",'
    assert text.count(old)==1
    text=text.replace(old,old+'\n                                                       "source_reported_thermal_transport_product",')
    old='    if is_derived != (is_crystallographic or is_empirical):'
    assert text.count(old)==1
    text=text.replace(old,'    is_thermal_product = method == "source_reported_thermal_transport_product"\n    if is_derived != (is_crystallographic or is_empirical or is_thermal_product):')
    put(p,text)
    p=ROOT/names[2];text=p.read_text('utf-8')
    marker='def material_labels('
    at=text.index(marker)
    text=text[:at]+"REQUIRED_LABELS |= frozenset(('code_source_reported_thermal_transport_product','source_product_derivation','source_product_notice'))\n\n\n"+text[at:]
    old='''            output.append(indent + "  " + labels["derived_notice"])
            output.append(field("derivation", raw(prop["derivation"]), indent + "  "))'''
    assert text.count(old)==1
    text=text.replace(old,'''            product = prop["method_definition"]["type"] == "source_reported_thermal_transport_product"
            output.append(indent + "  " + labels["source_product_notice" if product else "derived_notice"])
            output.append(field("source_product_derivation" if product else "derivation", raw(prop["derivation"]), indent + "  "))''')
    put(p,text)
    p=ROOT/names[3];locales=read(p)
    labels={
      'en':('Source-reported thermal transport product','Source calculation and provenance','Source-reported conductivity calculated from measured inputs. Context summaries are not verified paired calculation inputs;no product-of-means or uncertainty reconstruction. Not an independent direct measurement or engineering allowable.'),
      'zh':('来源报告的热传输乘积计算','原文计算及溯源','来源用实测输入计算热导率。上下文汇总量不是已核实的配对计算输入，不重算均值乘积或恢复误差；不是独立直接测量或工程允许值。'),
      'ja':('出典で報告された熱輸送積の計算','出典の計算と由来','出典が測定入力から算出した熱伝導率。文脈上の要約値は検証済みの対応入力ではなく、平均値の積や不確かさを再構成しない。独立した直接測定値または設計許容値ではない。'),
      'de':('In der Quelle berechnetes Wärmetransportprodukt','Quellenberechnung und Herkunft','Die Quelle berechnet die Wärmeleitfähigkeit aus Messeingaben. Kontextzusammenfassungen sind keine verifizierten gepaarten Recheneingaben;kein Produkt von Mittelwerten und keine Rekonstruktion der Unsicherheit. Keine unabhängige Direktmessung oder technische Auslegungsgrenze.')}
    for lang,values in labels.items():
        for key,value in zip(('code_source_reported_thermal_transport_product','source_product_derivation','source_product_notice'),values):
            assert key not in locales['languages'][lang];locales['languages'][lang][key]=value
    put(p,json.dumps(locales,ensure_ascii=False,indent=2)+'\n')
    sys.path.insert(0,str(ROOT))
    from materials_boundaries.material_references import _PROPERTIES_SCHEMA as schema
    assert len(schema['$defs']['property']['oneOf'])==14
    assert schema['$defs']['derivation']['oneOf'][0]==old_schema['$defs']['derivation']
    for old,new in zip(old_schema['$defs']['property']['oneOf'],schema['$defs']['property']['oneOf']):
        normalized=deepcopy(new);enum=normalized['properties']['method_definition']['properties']['type']['enum']
        assert enum.count('source_reported_thermal_transport_product')==1;enum.remove('source_reported_thermal_transport_product')
        assert old==normalized
    assert all(schema['$defs'][n]==old_schema['$defs'][n] for n in old_schema['$defs'] if n not in ('property','derivation'))
    put(ROOT/names[4],json.dumps(schema,ensure_ascii=False,indent=2)+'\n')
    # Preserve the old seven-branch structural guard while removing only the
    # documented newly admitted method from its comparison copy.
    p=ROOT/names[5];text=p.read_text('utf-8');old="        self.assertEqual(digest(public['$defs']['property']['oneOf'][:7]), 'efbb98481fda44b3dff58601c05ad5150e2abcdec1b4bf1529c93a8634201aba')"
    assert text.count(old)==1
    text=text.replace(old,"        original_branches=deepcopy(public['$defs']['property']['oneOf'][:7])\n        for branch in original_branches:\n            methods=branch['properties']['method_definition']['properties']['type']['enum']\n            self.assertEqual(methods.count('source_reported_thermal_transport_product'),1)\n            methods.remove('source_reported_thermal_transport_product')\n        self.assertEqual(digest(original_branches), 'efbb98481fda44b3dff58601c05ad5150e2abcdec1b4bf1529c93a8634201aba')")
    put(p,text)
    assert all(sha(ROOT/n)==v for n,v in pins['native_files_sha256'].items())
    with (HERE/'INTEGRATION_R1.json').open('x',encoding='utf-8',newline='\n') as f:
        json.dump(dict(before_sha256=before,after_sha256={n:sha(ROOT/n) for n in names},old_wood_definition_exact=True,old14branches_exact_except_one_added_method=True,other_definitions_exact=True,native_tables_unchanged=True,tests='not_run',native_mapping='not_prepared'),f,indent=2);f.write('\n')
    print('Source-product profile integrated;wood definition and old quantity domains retained;native unchanged')
if __name__=='__main__':main()
