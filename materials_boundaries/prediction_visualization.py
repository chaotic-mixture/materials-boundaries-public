"""Honest offline discrete-point comparisons from explicit same-source groups."""
from copy import deepcopy
import csv
from html import escape
import io
import math
from pathlib import Path
import unicodedata

from .catalog import read_catalog
from .silicon_predictions import SILICON_FAMILY, SILICON_QUANTITY, critical_strain_evidence, instability_mode_evidence
from .predictions import (DEFAULT_GROUP, PredictionError, canonical_json,
                          prediction_labels, require, validate_prediction_catalog, value_evidence, method_evidence)


def build_prediction_comparison(group_id=DEFAULT_GROUP):
    from . import __version__
    require(isinstance(group_id,str) and bool(group_id.strip()), 'comparison group ID required')
    sources=read_catalog('sources')
    catalog=validate_prediction_catalog(read_catalog('computational_predictions'),sources)
    group=next((g for g in catalog['comparison_groups'] if g['id']==group_id),None)
    require(group is not None,'unknown prediction comparison group: '+group_id)
    records={r['id']:r for r in catalog['records']}
    selected=[records[rid] for rid in group['record_ids']]
    protocol=next(p for p in catalog['protocols'] if p['id']==group['protocol_id'])
    source=next(s for s in sources['records'] if s['id']==group['source_id'])
    silicon=protocol['family']==SILICON_FAMILY
    bundle={'schema_version':'1.1.0' if silicon else '1.0.0','engine_version':__version__,
            'classification':'published_computational_prediction','group_id':group_id,
            'group_snapshot':deepcopy(group),'protocol_snapshot':deepcopy(protocol),
            'source_snapshots':[deepcopy(source)],'record_snapshots':deepcopy(selected),
            'points':[{'record_id':r['id'],'formula':r['formula'],'value_GPa':r['value_GPa'],
                       'source_value_string':r['source_value_string']} for r in selected],
            'axis':{'quantity':protocol['property'],'unit':'GPa','minimum':0},
            'display':'unconnected_categorical_points','interpolation':False,
            'uncertainty_bars':None,'stress_strain_curve':None,
            'comparison_scope':'explicit_same_source_reported_method_only',
            'unknown_conditions_equivalent':False}
    if silicon:
        for point,record in zip(bundle['points'],selected):
            point['direction']=deepcopy(record['direction'])
        bundle['comparison_axis']='loading_direction_family'
        bundle['associated_critical_strains']=[{'record_id':r['id'],**deepcopy(r['critical_engineering_strain'])} for r in selected]
    return bundle


def validate_prediction_comparison(bundle):
    try:
        require(isinstance(bundle,dict),'comparison must be an object')
        rebuilt=build_prediction_comparison(bundle['group_id'])
        require(canonical_json(bundle)==canonical_json(rebuilt), 'noncanonical prediction comparison or stale source snapshot')
    except (KeyError,TypeError,ValueError,OverflowError) as exc:
        raise PredictionError('invalid prediction comparison: '+str(exc)) from exc


def comparison_json(bundle):
    validate_prediction_comparison(bundle)
    return canonical_json(bundle,pretty=True)+'\n'


def comparison_csv(bundle):
    validate_prediction_comparison(bundle)
    if bundle['protocol_snapshot']['family']==SILICON_FAMILY:
        return _silicon_comparison_csv(bundle)
    out=io.StringIO(newline='');writer=csv.writer(out,lineterminator='\n')
    writer.writerow(['record_id','formula','cell_composition','predicted_ideal_shear_strength_GPa','source_value_string',
                     'classification','group_id','protocol_id','source_id','source_table_label','table_locator','value_source_url','method_locator','method_source_url',
                     'comparison_scope','physical_temperature_K','pressure_GPa','magnetic_state','uncertainty_GPa',
                     'unknown_state_reason','convergence_GPa','convergence_is_uncertainty','precision_note','finite_cell_caveat'])
    for r in bundle['record_snapshots']:
        writer.writerow([r['id'],r['formula'],r['cell_composition'],r['source_value_string'],r['source_value_string'],
            r['evidence_type'],bundle['group_id'],r['protocol_id'],r['source_id'],r['source_table_label'],
            value_evidence(r)['locator'],value_evidence(r)['url'],method_evidence(bundle['protocol_snapshot'])['locator'],method_evidence(bundle['protocol_snapshot'])['url'],bundle['comparison_scope'],
            'not_verified','not_verified','not_verified','not_established',
            'Unknown state fields do not establish equivalent conditions; raw inputs not audited.',
            '0.08','false',r['precision_note'], 'Periodic 12-atom, three-layer model; layer-count dependent, not a universal bulk limit.'])
    return out.getvalue()


def _wrapped(text,width):
    lines=[];line='';units=0
    # Break at spaces when practical, and at glyph boundaries for long CJK text.
    for word in text.split(' '):
        weight=sum(2 if unicodedata.east_asian_width(c) in 'WF' else 1 for c in word)
        if line and weight<=width and units+1+weight>width:
            lines.append(line);line='';units=0
        for c in (' ' if line else '')+word:
            step=2 if unicodedata.east_asian_width(c) in 'WF' else 1
            if units+step>width:lines.append(line);line='';units=0
            line+=c;units+=step
    if line:lines.append(line)
    return lines


def render_prediction_svg(bundle,*,lang='en',width=1100):
    validate_prediction_comparison(bundle);t=prediction_labels(lang,family=bundle['protocol_snapshot']['family'])
    require(type(width) is int and 360<=width<=1600,'SVG width must be an integer in [360,1600]')
    narrow=width<700;out=[];y=26
    def text(x,y,value,size=13,**attrs):
        attrs.setdefault('fill','#16374a')
        extra=' '.join(f'{k.replace("_","-")}="{escape(str(v),quote=True)}"' for k,v in attrs.items())
        out.append(f'<text x="{x:g}" y="{y:g}" font-size="{size}" {extra}>{escape(str(value))}</text>')
    def paragraph(value,size=13,gap=10):
        nonlocal y
        for line in _wrapped(value,max(20,int((width-48)/(size*.57)))):
            text(24,y,line,size);y+=size*1.5
        y+=gap
    paragraph('MATERIALS BOUNDARIES · v'+bundle['engine_version'],11,8 if narrow else 18)
    paragraph(t['title'],22 if narrow else 30,6)
    paragraph(bundle['group_snapshot']['names'][lang],14,10)
    for key in ('model_notice','comparison_notice'):paragraph(t[key],13,8)
    if bundle['protocol_snapshot']['family']==SILICON_FAMILY:
        paragraph(t['criterion_notice'],13,8)
    # Categorical rows and a common horizontal zero-origin GPa scale.
    upper=y+22;bottom=upper+len(bundle['points'])*70
    left=98 if narrow else 170;right=width-70
    max_value=max(p['value_GPa'] for p in bundle['points'])
    require(math.isfinite(max_value*1.08), 'strength exceeds plotting numeric range')
    desired=max_value*1.08/6
    require(math.isfinite(desired) and desired > 0, 'strength below plotting numeric range')
    scale=10.0**math.floor(math.log10(desired))
    step=next(n*scale for n in (1,2,5,10) if n*scale >= desired)
    count=math.ceil(max_value*1.08/step)
    axis_max=count*step
    require(math.isfinite(axis_max) and axis_max > 0, 'strength exceeds plotting numeric range')
    X=lambda v:left+(right-left)*(v/axis_max)
    out.append(f'<rect x="16" y="{upper-19:g}" width="{width-32}" height="{bottom-upper+78:g}" rx="12" fill="white" stroke="#d8e2e8"/>')
    for j in range(count+1):
        v=step*j;x=X(v)
        out.append(f'<line x1="{x:g}" x2="{x:g}" y1="{upper:g}" y2="{bottom:g}" stroke="#d8e2e8"/>')
        text(x,bottom+21,f'{v:g}',11,text_anchor='middle')
    for i,p in enumerate(bundle['points']):
        row=upper+36+i*70
        category=p.get('direction',{}).get('display',p['formula'])
        text(left-13,row+4,category,13 if narrow else 16,text_anchor='end')
        out.append(f'<circle data-record-id="{escape(p["record_id"],quote=True)}" cx="{X(p["value_GPa"]):.6f}" cy="{row:g}" r="6" fill="#087e8b"><title>{escape(category+": "+p["source_value_string"]+" GPa; "+t["legend"])}</title></circle>')
        text(X(p['value_GPa'])+12,row+4,p['source_value_string'],13)
    y=bottom+48
    # Axis text is wrapped below the plot on phones.
    paragraph(t['x_axis'],13,16)
    for key in ('unknown_notice','convergence_notice','precision_notice','finite_cell_notice','points_notice','method_notice','source_notice','review_notice'):
        paragraph(t[key],12 if narrow else 13,8)
    paragraph(bundle['source_snapshots'][0]['title'],11,6)
    for record in bundle['record_snapshots']:
        evidence=value_evidence(record)
        category=record.get('direction',{}).get('display',record['formula'])
        if 'critical_engineering_strain' in record:
            strain=record['critical_engineering_strain'];se=critical_strain_evidence(record)
            paragraph(category+' · '+t['critical_strain']+': '+strain['source_value_string']+'% ('+str(strain['value'])+'; '+strain['unit']+')',12,6)
            paragraph(se['locator']+' | '+se['url'],11,6)
            me=instability_mode_evidence(record)
            paragraph(me['locator']+' | '+me['url'],11,6)
        paragraph(category+': '+evidence['locator']+' | '+evidence['url'],11,6)
    method=method_evidence(bundle['protocol_snapshot'])
    paragraph(t['methods']+': '+method['locator']+' | '+method['url'],11,6)
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{math.ceil(y+8)}" viewBox="0 0 {width} {math.ceil(y+8)}" role="img"><title>{escape(t["title"])}</title><desc>{escape(t["model_notice"]+" "+t["comparison_notice"]+" "+t["unknown_notice"])}</desc><rect width="100%" height="100%" fill="#f4f8fa"/><style>text{{font-family:DejaVu Sans,Noto Sans CJK JP,sans-serif}}</style>\n'+'\n'.join(out)+'\n</svg>\n'


def render_prediction_html(bundle,*,lang='en'):
    validate_prediction_comparison(bundle);t=prediction_labels(lang,family=bundle['protocol_snapshot']['family'])
    wide=render_prediction_svg(bundle,lang=lang);narrow=render_prediction_svg(bundle,lang=lang,width=380)
    source=bundle['source_snapshots'][0];rows=[]
    silicon=bundle['protocol_snapshot']['family']==SILICON_FAMILY
    for r in bundle['record_snapshots']:
        evidence=value_evidence(r)
        if silicon:
            strain=r['critical_engineering_strain'];se=critical_strain_evidence(r);me=instability_mode_evidence(r)
            rows.append('<tr><td>'+escape(r['direction']['display'])+'</td><td>'+r['source_value_string']+' GPa</td><td>'+strain['source_value_string']+'% ('+str(strain['value'])+'; 1)</td><td><a href="'+escape(evidence['url'],quote=True)+'">'+escape(evidence['locator'])+'</a><br><a href="'+escape(se['url'],quote=True)+'">'+escape(se['locator'])+'</a><br><a href="'+escape(me['url'],quote=True)+'">'+escape(me['locator'])+'</a></td></tr>')
            continue
        rows.append('<tr><td>'+escape(r['cell_composition'])+'</td><td>'+r['source_value_string']+' GPa</td><td>'+escape(r['source_table_label'])+'</td><td><a href="'+escape(evidence['url'],quote=True)+'">'+escape(evidence['locator'])+'</a></td></tr>')
    primary=value_evidence(bundle['record_snapshots'][0])
    method=method_evidence(bundle['protocol_snapshot'])
    value_url=primary['url']
    method_url=method['url']
    links='<p><a href="'+escape(value_url,quote=True)+'">'+escape(t['table']+': '+primary['locator'])+'</a> · <a href="'+escape(method_url,quote=True)+'">'+escape(t['methods']+': '+method['locator'])+'</a></p>'
    return '<!doctype html><html lang="'+lang+'"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+escape(t['title'])+'</title><style>body{font-family:system-ui,sans-serif;max-width:1100px;margin:auto;padding:16px;color:#16374a;background:#f4f8fa}svg{width:100%;height:auto}.narrow{display:none}pre{white-space:pre-wrap;overflow-wrap:anywhere}a{color:#087e8b}p{line-height:1.5}table{border-collapse:collapse;width:100%}th,td{overflow-wrap:anywhere;text-align:left;padding:8px;border-bottom:1px solid #cbd9e1}@media(max-width:699px){.wide{display:none}.narrow{display:block}}</style></head><body><div class="wide">'+wide+'</div><div class="narrow">'+narrow+'</div><table><caption>'+escape(t['catalog'])+'</caption><thead><tr><th>'+escape(t['direction'] if silicon else t['cell'])+'</th><th>'+escape(t['value'])+'</th><th>'+escape(t['critical_strain'] if silicon else t['source_label'])+'</th><th>'+escape(t['table'])+'</th></tr></thead><tbody>'+''.join(rows)+'</tbody></table>'+links+'<p>'+escape(source['title'])+'</p><details><summary>'+escape(t['details'])+'</summary><pre>'+escape(canonical_json(bundle,pretty=True))+'</pre></details></body></html>\n'


def export_prediction_comparison(directory,*,lang='en',group_id=DEFAULT_GROUP):
    bundle=build_prediction_comparison(group_id)
    # Build/validate everything before creating the target directory.
    artifacts={'prediction-comparison.json':comparison_json(bundle),'prediction-comparison.csv':comparison_csv(bundle),
               f'prediction-comparison.{lang}.svg':render_prediction_svg(bundle,lang=lang),
               f'prediction-comparison.narrow.{lang}.svg':render_prediction_svg(bundle,lang=lang,width=380),
               f'prediction-comparison.{lang}.html':render_prediction_html(bundle,lang=lang)}
    target=Path(directory);target.mkdir(parents=True,exist_ok=True)
    for name,content in artifacts.items():(target/name).write_text(content,encoding='utf-8')
    return list(artifacts)


def _silicon_comparison_csv(bundle):
    out=io.StringIO(newline='');writer=csv.writer(out,lineterminator='\n')
    writer.writerow(['record_id','formula','cell_composition','loading_direction_family',
        'predicted_tensile_first_instability_strength_GPa','strength_source_value_string',
        'critical_engineering_strain','critical_engineering_strain_unit','strain_source_value_string','strain_source_unit',
        'classification','group_id','protocol_id','source_id','source_table_label','table_locator','value_source_url',
        'strain_table_locator','strain_source_url','instability_mode_locator','instability_mode_source_url','method_locator','method_source_url','comparison_scope',
        'strength_definition','first_instability_mode','physical_temperature_K','pressure_GPa','magnetic_state','uncertainty_GPa',
        'critical_strain_uncertainty','numerical_stress_error_estimate_GPa','numerical_stress_error_qualifier',
        'numerical_error_is_statistical_or_total_uncertainty','precision_note','strain_precision_note','structure_status'])
    method=method_evidence(bundle['protocol_snapshot'])
    for r in bundle['record_snapshots']:
        strain=r['critical_engineering_strain'];se=critical_strain_evidence(r);ev=value_evidence(r);me=instability_mode_evidence(r)
        writer.writerow([r['id'],r['formula'],r['cell_composition'],r['direction']['display'],
            r['source_value_string'],r['source_value_string'],strain['value'],strain['unit'],strain['source_value_string'],strain['source_unit'],
            r['evidence_type'],bundle['group_id'],r['protocol_id'],r['source_id'],r['source_table_label'],ev['locator'],ev['url'],
            se['locator'],se['url'],me['locator'],me['url'],method['locator'],method['url'],bundle['comparison_scope'],r['reported_strength_definition'],
            r['first_instability']['mode'],'not_verified','not_verified','not_verified','not_established','not_established',
            '0.05','less_than_approximately','false',r['precision_note'],strain['precision_note'],
            'Two-atom primitive cell reported; diamond-cubic normalization explicitly inferred.'])
    return out.getvalue()
