from __future__ import annotations

import argparse
import copy
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
BASE = Path(__file__).parent
parser = argparse.ArgumentParser()
parser.add_argument("--data-dir", type=Path, default=ROOT / "materials_boundaries" / "data")
parser.add_argument("--output", required=True, type=Path, help="New independent candidate directory")
args = parser.parse_args()
DATA = args.data_dir.resolve()
OUTPUT = args.output.resolve()
if OUTPUT == DATA or OUTPUT.is_relative_to(DATA):
    parser.error("output must be separate from input")
import hashlib
names = ("materials.json", "reference_properties.json", "sources.json")
baseline = {name: hashlib.sha256((DATA / name).read_bytes()).hexdigest() for name in names}

SOURCE = "wang2026_hierarchical_porous_mullite_nanosheet_properties"
IDENTITY = "mat_wang2026_hierarchical_porous_mullite_nanosheet"
URL = "https://pmc.ncbi.nlm.nih.gov/articles/PMC13514568/"
STATE_PREFIX = "state_wang2026_mullite_"
PROP_PREFIX = "refprop_wang2026_mullite_"

def load(name: str):
    return json.loads((DATA / name).read_text(encoding="utf-8"))

materials, properties, sources = (load(n) for n in ("materials.json", "reference_properties.json", "sources.json"))
materials["identities"] = [x for x in materials["identities"] if x["id"] != IDENTITY]
materials["records"] = [x for x in materials["records"] if not x["id"].startswith(STATE_PREFIX)]
properties["records"] = [x for x in properties["records"] if not x["id"].startswith(PROP_PREFIX)]
sources["records"] = [x for x in sources["records"] if x["id"] != SOURCE]

def ev(locator, *supports):
    return {"source_id": SOURCE, "url": URL, "locator": locator, "supports": list(supports)}

def fact(text, locator, *supports):
    return {"status": "reported", "text": text, "evidence": [ev(locator, *(supports or ("condition",)))], "notes": None}

def missing(note):
    return {"status": "not_reported_in_inspected_source", "text": None, "evidence": [], "notes": note}

source_template = next(x for x in sources["records"] if x.get("license", {}).get("status") == "explicit_reuse_license_verified")
source = copy.deepcopy(source_template)
source.update({
    "id": SOURCE,
    "title": "Hierarchically Porous Mullite Ceramics Assembled from Ultrathin Nanosheets for High-Temperature Thermal Insulation",
    "authors": ["Zhongyan Wang", "Anran Guo", "Xueying Zhang", "Jiaomei Ma", "Jiachen Liu"],
    "year": 2026, "doi": "10.3390/ma19163433", "urls": [URL, "https://doi.org/10.3390/ma19163433"],
    "read_status": "PMC full text inspected; CC BY license stated. Explicit prose values only; no graph digitization.",
    "license": {"status": "explicit_reuse_license_verified", "identifier": "CC-BY-4.0"},
    "role": "published_experimental_reference",
    "claim_notes": ["Four states are included only where §3.2 explicitly reports values; no intermediate graph values are estimated.", "The 20 wt.%/1200 °C compressive strength follows §3.2.2 and the conclusion (0.39 MPa); the abstract's 0.38 MPa discrepancy is retained.", "Porous mullite contains silica-derived cristobalite and is not represented as phase-pure mullite."],
    "provenance": {"curation_date": "2026-11-19", "method": "Directly transcribed explicit prose values from the audited four-row TABLE_VALUES.csv; no graph digitization or raw-data reanalysis."},
    "bundled_content": "bibliographic_metadata_and_attributed_table_transcription_only"
})
sources["records"].append(source)

identity_template = next(x for x in materials["identities"] if x["category"] == "inorganic")
identity = copy.deepcopy(identity_template)
identity.update({
    "id": IDENTITY, "version": "1.0.0", "category": "inorganic",
    "name": "Hierarchically porous mullite nanosheet ceramics (Wang et al., 2026 study-specific)",
    "names": {"en": "Hierarchically porous mullite nanosheet ceramics (Wang et al., 2026 study-specific)", "zh": "层级多孔莫来石纳米片陶瓷（Wang 等，2026，研究限定）", "ja": "階層多孔ムライトナノシートセラミックス（Wang et al. 2026）", "de": "Hierarchisch poröse Mullit-Nanosheet-Keramik (Wang et al. 2026)"},
    "aliases": [],
    "identity_scope": "Study-specific silica-sol-bonded hierarchical porous mullite nanosheet ceramics; source reports cristobalite in the studied temperature range, so this is not treated as phase-pure mullite.",
    "evidence": [ev("§2.3; §3.2.1-3.2.2", "material_identity", "classification")]
})
materials["identities"].append(identity)

state_template = materials["records"][0]
quantities = {
    "bulk_density": ("mass_density", "g/cm^3", "Bulk density calculated from dry mass and external geometric volume; condition-level repeat count and dispersion are not reported."),
    "apparent_porosity": ("apparent_porosity", "%", "Archimedes apparent porosity using deionized water and 30 min vacuum immersion; condition-level repeat count and dispersion are not reported."),
    "thermal_conductivity": ("thermal_conductivity", "W/(m*K)", "Apparent thermal conductivity measured by Hot Disk TPS 3500 at about 25 °C under ambient conditions; three measurements per condition, but the reported-value statistic and uncertainty are not specified."),
    "compressive_strength": ("compressive_strength", "MPa", "Compressive strength measured at 0.05 mm/min and averaged over five specimens; no dispersion is reported.")
}
templates = {key: copy.deepcopy(next(x for x in properties["records"] if x["quantity"] == q)) for key,(q,_,_) in quantities.items()}

with (BASE / "TABLE_VALUES.csv").open(encoding="utf-8-sig", newline="") as f:
    rows = list(csv.DictReader(f))
for row in rows:
    pct, temp = row["solid_content_wt_percent"], row["sintering_temperature_C"]
    slug = f"{pct}wt_{temp}c"
    sid = STATE_PREFIX + slug
    designation = f"{pct} wt.% solids, sintered at {temp} °C"
    state = copy.deepcopy(state_template)
    state.update({
        "id": sid, "version": "1.0.0", "identity_id": IDENTITY, "grade_id": None,
        "name": designation, "names": {"en": designation, "zh": f"固含量 {pct} wt.%、烧结 {temp} °C", "ja": designation, "de": designation},
        "aliases": [], "source_designation": designation, "property_ids": [],
        "source_scope": "Study-specific porous mullite nanosheet ceramic state; no universal material constant is implied.",
        "evidence": [ev(row["source_locator"], "state", "condition")]
    })
    state["state"] = {
        "product_form": fact("Hierarchically porous mullite nanosheet ceramic.", "§2.3; §3.2", "state", "condition"),
        "processing": fact(f"Silica-sol-bonded porous mullite; solid content {pct} wt.%; sintered at {temp} °C. The standard program is air, 4 °C/min to 1200 °C, 2 h hold; source temperature-series state is retained as reported.", "§2.3; §3.2", "state", "condition"),
        "temper_or_heat_treatment": fact(f"Sintered at {temp} °C.", row["source_locator"], "state", "condition"),
        "conditioning": missing("No additional conditioning before property measurements is reported."),
        "composition_or_purity": fact("Silica-sol-bonded porous mullite nanosheet ceramic; XRD also identifies cristobalite attributed to silica sol.", "§3.1; §3.2", "material_identity", "state"),
        "reinforcement": missing("No reinforcement phase is reported."),
        "porosity": fact(f"Apparent porosity {row['apparent_porosity_percent']}% by Archimedes method; deionized water and 30 min vacuum immersion.", row["source_locator"], "state", "condition"),
        "orientation": missing("No material orientation for the reported tests is specified.")
    }
    materials["records"].append(state)
    for key,(quantity,unit,note) in quantities.items():
        pid = PROP_PREFIX + slug + "_" + key
        value_col = {"bulk_density":"bulk_density_g_cm3", "apparent_porosity":"apparent_porosity_percent", "thermal_conductivity":"room_temperature_thermal_conductivity_W_mK", "compressive_strength":"compressive_strength_MPa"}[key]
        value = row[value_col]
        p = copy.deepcopy(templates[key])
        p.update({
            "id": pid, "version": "1.0.0", "material_state_id": sid, "quantity": quantity,
            "reported_value": {"kind":"scalar", "value_text":value, "number":value, "unit_text":unit, "unit_code":"percent" if key == "apparent_porosity" else unit},
            "source_id": SOURCE, "source_property_label": quantity,
            "source_discrepancies": [],
            "basis_note": note, "scope_note": "Source-specific porous ceramic result; not a dense mullite constant or engineering allowable.",
            "evidence": [ev(row["source_locator"], "reported_value", "method", "state", "classification")],
            "sample_count": {"value": 5 if key == "compressive_strength" else (3 if key == "thermal_conductivity" else None), "relation": "exact" if key == "compressive_strength" else ("exact" if key == "thermal_conductivity" else "not_reported"), "scope": note, "source_statement": note, "evidence": [ev(row["source_locator"], "sample_count")] if key in ("compressive_strength", "thermal_conductivity") else []},
            "uncertainty": None, "uncertainty_status": "not_reported_in_inspected_source",
            "uncertainty_note": "No uncertainty is reported for this selected value.",
            "source_document": {"url": URL, "revision": "PMC Version of Record, 2026", "inspected_on": "2026-11-19", "sha256": None, "hash_status": "not_retained", "hash_note": "The full text was inspected online; source bytes were not retained locally.", "inspection_scope": "PMC full text: §§2.3–2.4, §§3.1–3.2 and conclusions; explicit prose values only.", "inspection_status": "selected_content_inspected"},
            "method_definition": {"type": "source_reported_conventional", "definition": note, "extraction_window": None, "evidence": [ev(row["source_locator"], "method", "classification")]},
            "verification": {"source_inspection_scope": "PMC full text: §§2.3–2.4, §§3.1–3.2 and conclusions; explicit prose values only.", "transcription_cross_check": "completed", "independent_scientific_review": False, "raw_data_reanalysis": False},
            "conditions": {
                "temperature": fact("Approximately 25 °C ambient conditions.", "§2.4", "condition") if key == "thermal_conductivity" else missing("Test temperature is not reported."),
                "test_standard": missing("No external test standard is specified."),
                "test_method": fact(note, row["source_locator"], "method", "condition"),
                "direction": missing("Measurement direction is not reported."),
                "conditioning": missing("No additional conditioning is reported."),
                "loading_rate": fact("0.05 mm/min", "§2.4", "condition") if key == "compressive_strength" else missing("Not applicable or not reported for this property."),
                "additional_conditions": []
            }
        })
        if key == "bulk_density": p["density_basis"] = "bulk"
        state["property_ids"].append(pid)
        properties["records"].append(p)

original_ids = {row["id"] for row in load("reference_properties.json")["records"]}
missing_ids = original_ids - {row["id"] for row in properties["records"]}
if missing_ids:
    raise SystemExit("Unexplained missing property IDs: " + ", ".join(sorted(missing_ids)))
if any(hashlib.sha256((DATA / name).read_bytes()).hexdigest() != digest for name, digest in baseline.items()):
    raise SystemExit("Input snapshot changed during reconstruction")
OUTPUT.mkdir(parents=True, exist_ok=False)
for name,obj in (("materials.json",materials),("reference_properties.json",properties),("sources.json",sources)):
    (OUTPUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps({"identity":IDENTITY,"states":len(rows),"properties":len(rows)*4,"source":SOURCE}))
