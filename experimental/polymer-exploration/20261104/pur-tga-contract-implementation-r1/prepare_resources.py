"""Generate the public schema and reviewed-concept display vocabulary only."""
from pathlib import Path
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[4]
BASE = Path('F:/材料边界/open-database-evidence/polymer-tga-contract-20261104-r1/baseline')
sys.path.insert(0, str(ROOT))
from materials_boundaries.material_references import _PROPERTIES_SCHEMA


def write(path, obj):
    with path.open('w', encoding='utf-8', newline='\n') as stream:
        json.dump(obj, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def main():
    old = json.loads((BASE / 'reference_properties.schema.json').read_bytes())
    assert old['$defs']['property']['oneOf'] == _PROPERTIES_SCHEMA['$defs']['property']['oneOf'][:7]
    assert old['$defs']['legacy_reported_value'] == _PROPERTIES_SCHEMA['$defs']['legacy_reported_value']
    assert len(_PROPERTIES_SCHEMA['$defs']['property']['oneOf']) == 11
    labels = {
        'en': ['Thermal degradation onset temperature', 'Temperature at specified fractional mass loss', 'Thermal degradation rate peak temperature', 'TGA residue percentage', 'Specified fractional mass loss', 'Source degradation peak ordinal', 'Residue endpoint temperature', 'Mass reference basis', 'Source TGA coordinates only; unknown mass reference, statistics and preparation remain unknown. Not melting peaks, certified ash or service limits.'],
        'zh': ['热降解起始温度', '指定分数失重对应温度', '热降解速率峰温', '热重残留百分数', '指定分数失重', '来源热降解峰序号', '残留端点温度', '质量参考基准', '仅为来源热重坐标；未确认的质量基准、统计和制样条件保持未知。不是熔融峰、认证灰分或使用温度限值。'],
        'ja': ['熱分解開始温度', '指定質量減少率における温度', '熱分解速度のピーク温度', '熱重量測定の残留百分率', '指定質量減少率', '出典の熱分解ピーク番号', '残留量の終点温度', '質量の参照基準', '出典の熱重量座標のみ。不明な質量基準、統計、試料調製は不明のまま保持。融解ピーク、認証灰分、使用温度限界ではありません。'],
        'de': ['Temperatur des thermischen Abbaubeginns', 'Temperatur bei festgelegtem anteiligem Masseverlust', 'Peaktemperatur der thermischen Abbaurate', 'TGA-Rückstandsprozentsatz', 'Festgelegter anteiliger Masseverlust', 'Peaknummer des thermischen Abbaus laut Quelle', 'Endpunkttemperatur des Rückstands', 'Massenbezugsbasis', 'Nur TGA-Koordinaten der Quelle; unbekannte Massenbasis, Statistik und Probenvorbereitung bleiben unbekannt. Keine Schmelzpeaks, zertifizierten Aschegehalte oder Einsatzgrenzen.'],
    }
    keys = ['code_thermal_degradation_onset_temperature', 'code_temperature_at_specified_mass_loss', 'code_thermal_degradation_rate_peak_temperature', 'code_tga_residue_percentage', 'specified_mass_loss', 'degradation_peak_ordinal', 'residue_endpoint_temperature', 'mass_reference_basis', 'tga_reference_notice']
    locales = json.loads((BASE / 'material_locales.json').read_bytes())
    for language, values in labels.items():
        assert len(values) == len(keys)
        locales['languages'][language].update(dict(zip(keys, values)))
    write(ROOT / 'materials_boundaries/data/material_locales.json', locales)
    write(ROOT / 'schemas/reference_properties.schema.json', _PROPERTIES_SCHEMA)
    digest = hashlib.sha256(json.dumps(old['$defs']['property']['oneOf'], sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    legacy = hashlib.sha256(json.dumps(old['$defs']['legacy_reported_value'], sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    print(json.dumps({'old_seven_branches_sha256': digest, 'old_legacy_value_sha256': legacy, 'new_branch_count': 11, 'native_tables_changed': False}))


if __name__ == '__main__':
    main()
