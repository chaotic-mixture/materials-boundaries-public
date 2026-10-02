"""Offline static facets of synthetic demonstrations and empirical models.

Per-branch polylines never bridge equation gaps or average overlapping endpoints.
Canonical bundle validation rebuilds from installed model/source snapshots.
"""
from copy import deepcopy
import csv
from decimal import Context, Decimal, localcontext
from html import escape
from importlib.resources import files
import io
import json
from pathlib import Path

from .catalog import read_catalog
from .temperature import (LANGUAGES, TemperatureError, _predict, _require, canonical_json,
                          get_model, model_sources)


from .temperature_presentation import (REQUIRED_LABELS, labels, presentation_for,
                                       branch_fit_label, branch_data_label)


def build_temperature_comparison(model_ids=None, *, points_per_branch=101):
    from . import __version__
    if model_ids is None:
        model_ids = [m['id'] for m in read_catalog('temperature_models')['records']]
    _require(isinstance(model_ids, list) and 1 <= len(model_ids) <= 20 and
             all(isinstance(x, str) for x in model_ids) and len(set(model_ids)) == len(model_ids),
             'model_ids: 1–20 distinct IDs required')
    _require(type(points_per_branch) is int and 2 <= points_per_branch <= 501,
             'points_per_branch: integer in [2,501] required')
    cases = []
    for mid in model_ids:
        model = get_model(mid)
        series = []
        for branch in model['branches']:
            low, high = branch['equation_range_K']
            with localcontext(Context(prec=60)):
                temperatures = [float(Decimal(str(low)) + (Decimal(str(high))-Decimal(str(low))) * i / (points_per_branch-1))
                                for i in range(points_per_branch)]
            temperatures[0], temperatures[-1] = low, high
            points = []
            for temperature in temperatures:
                outcome = _predict(model, temperature)
                row = next(p for p in outcome['predictions'] if p['branch_id'] == branch['id'])
                points.append({'temperature_K':temperature, 'value_GPa':row['value'], 'status':outcome['status']})
            series.append({'branch_id':branch['id'], 'equation_range_K':deepcopy(branch['equation_range_K']), 'points':points})
        # Retain exact shared endpoints even when the chosen grid is very coarse.
        shared = sorted({t for b in model['branches'] for t in b['equation_range_K']
                         if len(_predict(model, t)['predictions']) > 1})
        cases.append({'model_id':mid, 'model_snapshot':model, 'source_snapshots':model_sources(model),
                      'series':series, 'overlaps':[{'temperature_K':t, **_predict(model, t)} for t in shared],
                      'specimen_applicability':'not_applicable_synthetic_demo'
                      if model['classification'] == 'synthetic_demo' else 'not_established'})
    classifications = {case['model_snapshot']['classification'] for case in cases}
    classification = next(iter(classifications)) if len(classifications) == 1 else 'mixed_temperature_models'
    return {'schema_version':'1.0.0', 'engine_version':__version__, 'classification':classification,
            'axis':{'quantity':'absolute_temperature','unit':'K'}, 'output':{'quantity':'youngs_modulus','unit':'GPa'},
            'points_per_branch':points_per_branch, 'cases':cases, 'display':'separate_material_facets',
            'overlay_allowed':False, 'uncertainty_band':None,
            'sampling':'Chosen equally spaced samples within each equation range, with exact endpoints; not observations. Straight SVG segments connect samples within a branch only.',
            'comparison':'Synthetic demonstrations represent no real material or empirical evidence. Any empirical models retain their own evidence and unknown specimen conditions. Shared units do not establish physical equivalence.',
            'overlap_policy':'retain_all_matching_branches_without_selection_averaging_or_smoothing'}


def validate_temperature_comparison(bundle):
    try:
        rebuilt = build_temperature_comparison([c['model_id'] for c in bundle['cases']], points_per_branch=bundle['points_per_branch'])
        _require(canonical_json(bundle) == canonical_json(rebuilt), 'noncanonical temperature comparison or stale source snapshot')
    except (KeyError, TypeError, ValueError, OverflowError) as exc:
        raise TemperatureError('invalid temperature comparison: '+str(exc)) from exc


def comparison_json(bundle):
    validate_temperature_comparison(bundle)
    return canonical_json(bundle, pretty=True)+'\n'


def comparison_csv(bundle):
    validate_temperature_comparison(bundle)
    out=io.StringIO(newline=''); writer=csv.writer(out, lineterminator='\n')
    writer.writerow(['model_id','branch_id','temperature_K','predicted_youngs_modulus_GPa','status','classification','uncertainty_band'])
    for case in bundle['cases']:
        for series in case['series']:
            for point in series['points']:
                writer.writerow([case['model_id'],series['branch_id'],point['temperature_K'],point['value_GPa'],point['status'],case['model_snapshot']['classification'],'not_provided'])
    return out.getvalue()


def _wrapped(text, width):
    # Conservative glyph advances for the declared font stack. Wide Latin
    # names need more room too; character count alone clips W/M-heavy labels.
    def advance(char):
        if ord(char) > 0x2ff:
            return 2
        if char in 'WM@%':
            return 2
        if char in 'mw':
            return 1.8
        if char.isupper():
            return 1.5
        if char in "iljtfr.,:;!'|":
            return .8
        return 1.2
    lines=[]; line=''; length=0
    for word in text.split(' '):
        measure=sum(advance(c) for c in word)
        if measure>width:
            if line: lines.append(line); line=''; length=0
            for char in word:
                step=advance(char)
                if length+step>width: lines.append(line); line=''; length=0
                line+=char; length+=step
        elif length+(1 if line else 0)+measure>width:
            lines.append(line); line=word; length=measure
        else:
            line+=(' ' if line else '')+word; length+=(1 if length else 0)+measure
    if line: lines.append(line)
    return lines


def _case_layout(case, lang, facet_width):
    """Wrap before sizing: every branch and overlap endpoint gets its own rows."""
    t = labels(lang)
    model = case['model_snapshot']
    display = presentation_for(model, case['source_snapshots'], lang)
    width = max(20, int((facet_width - 30) / 6.1))
    title = _wrapped(display['name'], max(16, int((facet_width - 30) / 10)))
    intro = []
    for value in (display['condition'],
                  t['source_attribution'].format(source=display['source_id'] or ', '.join(model['source_ids'])),
                  t['condition_evidence'].format(source=display['condition_source_id'])
                  if display['condition_source_id'] else None):
        if value:
            intro.extend(_wrapped(value, width))
    rows = []
    for i, branch in enumerate(model['branches']):
        low, high = branch['equation_range_K']
        texts = [f'{t["branch"]} {i+1}: {branch["id"]}',
                 f'{t["equation_range"]}: {low:g}–{high:g} K · {t["data_range"]}: {branch_data_label(branch, t)}',
                 branch_fit_label(branch, t)]
        for value in texts:
            rows.extend((line, i) for line in _wrapped(value, width))
        rows.append(('', None))
    for overlap in case['overlaps']:
        rows.extend((line, None) for line in _wrapped(t['overlap_at'].format(temperature=f'{overlap["temperature_K"]:g}'), width))
        for row in overlap['predictions']:
            value = t['branch_value'].format(branch=row['branch_id'], value=f'{row["value"]:.6f}')
            rows.extend((line, None) for line in _wrapped(value, width))
        rows.append(('', None))
    rows.extend((line, None) for line in _wrapped(display['rights'], width))
    plot_offset = 30 + len(title)*23 + len(intro)*17 + 28
    details_offset = plot_offset + 244
    return {'display': display, 'title': title, 'intro': intro, 'rows': rows,
            'plot_offset': plot_offset, 'details_offset': details_offset,
            'height': details_offset + len(rows)*17 + 30}


def render_temperature_svg(bundle, *, lang='en', width=1100):
    validate_temperature_comparison(bundle)
    t = labels(lang)
    _require(type(width) is int and 360 <= width <= 1600, 'SVG width must be an integer in [360,1600]')
    narrow = width < 800
    columns = 1 if narrow else 2
    facet_width = (width - 48 - (columns-1)*28) / columns
    wrap_width = max(30, int((width-48)/7))
    title_lines = _wrapped(t['title'], max(24, int((width-48)/(10 if narrow else 13))))
    subtitle_lines = _wrapped(t['subtitle'], wrap_width)
    head_lines = _wrapped(t['scale_notice'], wrap_width)
    top = 47 + len(title_lines)*28 + len(subtitle_lines)*20 + len(head_lines)*19 + 22
    layouts = [_case_layout(case, lang, facet_width) for case in bundle['cases']]
    offsets = []
    position = top
    for start in range(0, len(layouts), columns):
        row_height = max(item['height'] for item in layouts[start:start+columns])
        for item in layouts[start:start+columns]:
            offsets.append((position, row_height))
        position += row_height + 16
    notes = []
    for key in ('range_notice', 'fit_notice', 'unknown_notice', 'overlap_notice',
                'overlap_endpoint_notice', 'endpoint_notice', 'precision_notice',
                'review_notice', 'source_notice'):
        notes.extend(_wrapped(t[key], wrap_width))
        notes.append('')
    footer = position + 8
    height = footer + len(notes)*19 + 20
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img">',
           f'<title>{escape(t["title"])}</title><desc>{escape(t["range_notice"]+" "+t["fit_notice"]+" "+t["overlap_notice"])}</desc>',
           '<rect width="100%" height="100%" fill="#f6f9fc"/>',
           '<style>text{font-family:DejaVu Sans,Noto Sans CJK JP,sans-serif} .grid{stroke:#d6e0e8;stroke-width:1}</style>']
    def text(x, y, value, size=13, **attrs):
        attrs.setdefault('fill', '#15344b')
        extra = ' '.join(f'{k.replace("_", "-")}="{escape(str(v), quote=True)}"' for k,v in attrs.items())
        out.append(f'<text x="{x:g}" y="{y:g}" font-size="{size}" {extra}>{escape(str(value))}</text>')
    text(24, 25, 'MATERIALS BOUNDARIES · v'+bundle['engine_version'], 11)
    y = 54
    for line in title_lines:
        text(24, y, line, 21 if narrow else 28); y += 28
    for line in subtitle_lines:
        text(24, y, line, 12 if narrow else 15); y += 20
    for line in head_lines:
        text(24, y, line, 12); y += 19
    colors = ['#087f8c', '#a45117', '#7446a7', '#3568a0', '#805537']
    x_max = max(300, max(b['equation_range_K'][1] for c in bundle['cases'] for b in c['series']))
    for index, (case, layout) in enumerate(zip(bundle['cases'], layouts)):
        x0 = 24 + (index % columns)*(facet_width+28)
        y0, row_height = offsets[index]
        out.append(f'<g data-model-id="{escape(case["model_id"], quote=True)}">')
        out.append(f'<rect x="{x0:g}" y="{y0:g}" width="{facet_width:g}" height="{row_height:g}" rx="12" fill="white" stroke="#d6e0e8"/>')
        y = y0 + 28
        for line in layout['title']:
            text(x0+14, y, line, 18); y += 23
        y += 3
        for line in layout['intro']:
            text(x0+14, y, line, 11); y += 17
        left = x0+60; right = x0+facet_width-22
        upper = y0+layout['plot_offset']; bottom = upper+192
        values = [p['value_GPa'] for series in case['series'] for p in series['points']]
        lo, hi = min(values), max(values)
        padding = max((hi-lo)*.12, .2); lo -= padding; hi += padding
        X = lambda value: left+(right-left)*value/x_max
        Y = lambda value: bottom-(bottom-upper)*(value-lo)/(hi-lo)
        text(left, upper-13, t['y_axis'], 11)
        for j in range(5):
            value = lo+(hi-lo)*j/4; py = Y(value)
            out.append(f'<path class="grid" d="M {left:g} {py:g} H {right:g}"/>')
            text(left-7, py+4, f'{value:.1f}', 11, text_anchor='end')
        for j in range(7):
            value = x_max*j/6; px = X(value)
            out.append(f'<path class="grid" d="M {px:g} {upper:g} V {bottom:g}"/>')
            text(px, bottom+19, f'{value:.4g}', 10, text_anchor='middle')
        text((left+right)/2, bottom+39, t['x_axis'], 12, text_anchor='middle')
        for si, series in enumerate(case['series']):
            color = colors[si % len(colors)]
            path = ' '.join(f'{X(p["temperature_K"]):.6f},{Y(p["value_GPa"]):.6f}' for p in series['points'])
            out.append(f'<polyline data-branch-id="{escape(series["branch_id"], quote=True)}" fill="none" stroke="{color}" stroke-width="2.4" points="{path}"/>')
            for point in (series['points'][0], series['points'][-1]):
                desc = f'{series["branch_id"]}: {point["temperature_K"]} K: {point["value_GPa"]:.12g} GPa; {point["status"]}'
                out.append(f'<circle cx="{X(point["temperature_K"]):.6f}" cy="{Y(point["value_GPa"]):.6f}" r="3.1" fill="{color}"><title>{escape(desc)}</title></circle>')
        y = y0+layout['details_offset']
        for line, color_index in layout['rows']:
            if line:
                text(x0+14, y, line, 11, fill=colors[color_index % len(colors)] if color_index is not None else '#15344b')
            y += 17
        out.append('</g>')
    for i, line in enumerate(notes):
        if line:
            text(24, footer+i*19, line, 12)
    out.append('</svg>')
    return '\n'.join(out)+'\n'


def render_temperature_html(bundle, *, lang='en'):
    validate_temperature_comparison(bundle)
    t = labels(lang)
    svg = render_temperature_svg(bundle, lang=lang)
    details = []
    for case in bundle['cases']:
        model = case['model_snapshot']
        display = presentation_for(model, case['source_snapshots'], lang)
        details.append('<section data-model-id="'+escape(model['id'], quote=True)+'"><h2>'+escape(display['name'])+'</h2><p>'+escape(model['descriptions'][lang])+'</p>')
        details.append('<p>'+escape(display['condition'])+'</p><p>'+escape(display['rights'])+'</p>')
        for branch in model['branches']:
            details.append('<p>'+escape(f"{branch['id']} · {t['equation_range']}: {branch['equation_range_K']} K · {t['data_range']}: {branch_data_label(branch, t)}")+'</p><p>'+escape(t['coefficients']+': '+', '.join(branch['coefficients_text']))+'</p>')
            details.append('<p>'+escape(branch_fit_label(branch, t))+'</p>')
        for source in case['source_snapshots']:
            details.append('<p><a href="'+escape(source['urls'][0], quote=True)+'">'+escape(source['title'])+'</a></p>')
        details.append('<details><summary>'+escape(t['details'])+'</summary><pre>'+escape(canonical_json({'model':model, 'sources':case['source_snapshots']}, pretty=True))+'</pre></details></section>')
    return '<!doctype html><html lang="'+lang+'"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+escape(t['title'])+'</title><style>body{font-family:system-ui,sans-serif;max-width:1100px;margin:auto;padding:20px;color:#15344b;background:#f6f9fc;overflow-wrap:anywhere}svg{width:100%;height:auto}pre{white-space:pre-wrap;overflow-wrap:anywhere}a{color:#087f8c}p{line-height:1.5}</style><body>'+svg+''.join(details)+'</body></html>\n'


def export_temperature_comparison(directory, *, lang='en', points_per_branch=101):
    bundle=build_temperature_comparison(points_per_branch=points_per_branch)
    target=Path(directory); target.mkdir(parents=True,exist_ok=True)
    artifacts={'temperature-comparison.json':comparison_json(bundle), 'temperature-comparison.csv':comparison_csv(bundle),
               f'temperature-comparison.{lang}.svg':render_temperature_svg(bundle,lang=lang),
               f'temperature-comparison.narrow.{lang}.svg':render_temperature_svg(bundle,lang=lang,width=380),
               f'temperature-comparison.{lang}.html':render_temperature_html(bundle,lang=lang)}
    for name,content in artifacts.items(): (target/name).write_text(content,encoding='utf-8')
    return list(artifacts)
