"""Inert, dependency-free renderers for the reviewed temperature plot.

This is a separate quantitative route. It never changes the inspection view or
its policy, executes no formulas, and uses only the validated bundle snapshots.
"""
from html import escape
import math

from ._observation_temperature_labels import labels, SCOPE_KEYS
from .observation_visualization import _wrapped


# Fixed presentation constants: these do not depend on observed magnitudes.
PLOT_HEIGHT = 340
POINT_RADIUS = 4
CAP_HALF_WIDTH = 5
INK = '#183b4e'
FONT = 'DejaVu Sans,Noto Sans CJK JP,Noto Sans CJK SC,sans-serif'


def _runtime():
    # Import lazily: the public runtime re-exports these render entry points.
    from .observation_temperature_plot import (
        validate_observation_temperature_plot, _canonical, _safe_url, _require)
    return validate_observation_temperature_plot, _canonical, _safe_url, _require


def _text_lines(value, columns):
    """Conservative wrapping with closing punctuation kept on the prior line."""
    lines = _wrapped(value, columns)
    for index in range(1, len(lines)):
        while lines[index] and lines[index][0] in '.,;:!?)]}，。；：！？、）］」』':
            lines[index - 1] += lines[index][0]
            lines[index] = lines[index][1:]
    return [line for line in lines if line]


def _fmt(value):
    return format(value, '.6f').rstrip('0').rstrip('.')


def _plot_elements(bundle, *, left, right, top, responsive=False):
    """Map already-validated glyph endpoints, never recompute source statistics.

    The HTML chart uses SVG percentage x coordinates inside a padded container,
    without a viewBox. Text, dots, caps and y-height therefore retain pixel sizes
    at narrow widths. Standalone SVG uses the exact same linear axis transform.
    """
    bottom = top + PLOT_HEIGHT
    def px(temp):
        fraction = (float(temp) - 15) / 110
        return _fmt(100 * fraction) + '%' if responsive else _fmt(left + fraction * (right - left))
    def py(value):
        return top + PLOT_HEIGHT * (1 - float(value) / 55)
    l, r = ('0', '100%') if responsive else (_fmt(left), _fmt(right))
    result = []
    for tick in (0, 10, 20, 30, 40, 50):
        yy = py(tick)
        result.append(f'<line class="y-grid" x1="{l}" x2="{r}" y1="{_fmt(yy)}" y2="{_fmt(yy)}" stroke="#d5dce0" stroke-width="1"/>')
        tx = -10 if responsive else left - 10
        result.append(f'<text class="y-tick" x="{_fmt(tx)}" y="{_fmt(yy + 4)}" text-anchor="end" font-size="13" fill="{INK}">{tick}</text>')
    result.extend([
        f'<line class="y-axis" x1="{l}" x2="{l}" y1="{_fmt(top)}" y2="{_fmt(bottom)}" stroke="{INK}" stroke-width="1.3"/>',
        f'<line class="x-axis" x1="{l}" x2="{r}" y1="{_fmt(bottom)}" y2="{_fmt(bottom)}" stroke="{INK}" stroke-width="1.3"/>'])
    for tick in (23, 40, 60, 80, 100, 120):
        xx = px(tick)
        result.append(f'<line class="x-tick-mark" x1="{xx}" x2="{xx}" y1="{_fmt(bottom)}" y2="{_fmt(bottom + 5)}" stroke="{INK}"/>')
        result.append(f'<text class="x-tick" x="{xx}" y="{_fmt(bottom + 24)}" text-anchor="middle" font-size="13" fill="{INK}">{tick}</text>')
    for glyph in bundle['glyphs']:
        xx = px(glyph['temperature_value_string'])
        low = py(glyph['derived_lower_string'])
        high = py(glyph['derived_upper_string'])
        center = py(glyph['central_value_string'])
        attr = (' data-record-id="' + escape(glyph['record_id'], quote=True) + '"'
                ' data-temperature="' + escape(glyph['temperature_value_string'], quote=True) + '"'
                ' data-central-value="' + escape(glyph['central_value_string'], quote=True) + '"')
        result.append(f'<line class="sd-whisker"{attr} x1="{xx}" x2="{xx}" y1="{_fmt(low)}" y2="{_fmt(high)}" stroke="{INK}" stroke-width="1.7"/>')
        for cap, yy in (('lower', low), ('upper', high)):
            if responsive:
                # Nested SVG establishes a percentage-positioned origin; its
                # cap is a constant ten pixels, not a scaled percentage mark.
                result.append(f'<svg x="{xx}" y="{_fmt(yy)}" width="1" height="1" overflow="visible" aria-hidden="true"><line class="sd-cap"{attr} data-end="{cap}" x1="-5" x2="5" y1="0" y2="0" stroke="{INK}" stroke-width="1.7"/></svg>')
            else:
                result.append(f'<line class="sd-cap"{attr} data-end="{cap}" x1="{_fmt(float(xx)-CAP_HALF_WIDTH)}" x2="{_fmt(float(xx)+CAP_HALF_WIDTH)}" y1="{_fmt(yy)}" y2="{_fmt(yy)}" stroke="{INK}" stroke-width="1.7"/>')
        result.append(f'<circle class="observation-center"{attr} cx="{xx}" cy="{_fmt(center)}" r="{POINT_RADIUS}" fill="{INK}"/>')
    return result


def _metadata_sections(bundle, t):
    """Complete shared facts and actual source evidence, without six copies.

    Scientific admission guarantees a single shared protocol; per-condition
    temperatures, exact values, source cells and IDs remain in the table.
    Canonical field names/source prose stay verbatim in every locale.
    """
    _, canonical, _, _ = _runtime()
    first = bundle['record_snapshots'][0]
    yield t['identity'], [(canonical(bundle['group']), None),
                          (canonical(bundle['selection']), None)]
    shared = []
    for key in ('material', 'method', 'sample_metadata'):
        for field, value in first[key].items():
            shared.append((key + '.' + field + ': ' + canonical(value), None))
    # Show the varying temperature objects explicitly, preserving nulls.
    for record in bundle['record_snapshots']:
        shared.append((record['id'] + ' | conditions.temperature: ' + canonical(record['conditions']['temperature']), None))
    for field, value in first['conditions'].items():
        if field != 'temperature':
            shared.append(('conditions.' + field + ': ' + canonical(value), None))
    for key in ('summary_statistic', 'central_statistic_explicitly_named', 'aggregation_convention', 'precision_note'):
        shared.append(('reported_result.' + key + ': ' + canonical(first['reported_result'][key]), None))
    uncertainty_definition = {key: value for key, value in first['reported_result']['uncertainty'].items()
                              if key not in ('value', 'value_string')}
    shared.append((t['uncertainty_definition'] + ': ' + canonical(uncertainty_definition), None))
    shared.append(('limits: ' + canonical(first['limits']), None))
    yield t['shared_metadata'], shared
    provenance = []
    for record in bundle['record_snapshots']:
        provenance.append((t['record'] + ': ' + record['id'] + ' | version: ' + record['version'] + ' | ' + record['name'], None))
    for field, value in first['verification'].items():
        provenance.append(('verification.' + field + ': ' + canonical(value), None))
    for evidence in first['evidence']:
        provenance.append((t['evidence'] + ': ' + canonical(evidence), evidence.get('source_url')))
    provenance.append(('record_digests: ' + canonical(bundle['record_digests']), None))
    provenance.append(('source_digests: ' + canonical(bundle['source_digests']), None))
    for source in bundle['source_snapshots']:
        provenance.append((t['source'] + ': ' + canonical(source), None))
        for url in source['urls']:
            provenance.append((url, url))
    yield t['metadata_heading'], provenance


def _source_intro(bundle, t):
    first, source = bundle['record_snapshots'][0], bundle['source_snapshots'][0]
    return [(', '.join(source['authors']) + ' (' + str(source['year']) + '). ' + source['title'], None),
            (first['verification']['rights']['attribution'], None),
            (t['revision'], None),
            (t['adaptation'], None),
            (first['verification']['rights']['license_url'], first['verification']['rights']['license_url'])]


def render_observation_temperature_svg(bundle, *, lang='en', width=1100):
    """Render a complete standalone document, including scope and exact cells."""
    validate, canonical, safe_url, require = _runtime()
    validate(bundle)
    t = labels(lang)
    require(type(width) is int and 320 <= width <= 1600,
            'SVG width must be an integer in [320,1600]')
    # Validation also rejects XML-illegal strings, including legal-ID renames.
    canonical(bundle)
    margin = 24 if width >= 700 else 14
    space = width - 2 * margin
    elements = []
    def para(value, y, *, x=margin, available=space, size=13, bold=False, url=None, cls=None):
        lines = _text_lines(value, max(10, int(available / (size * (.58 if width >= 700 else .68)))))
        for line in lines:
            attrs = (' font-weight="700"' if bold else '') + (' class="' + cls + '"' if cls else '')
            tag = f'<text x="{_fmt(x)}" y="{_fmt(y)}" font-size="{size}" fill="{INK}"{attrs}>' + escape(line) + '</text>'
            if url is not None:
                tag = '<a href="' + escape(safe_url(url), quote=True) + '">' + tag + '</a>'
            elements.append(tag)
            y += size * (1.45 if width >= 700 else 1.55)
        return y + (6 if width >= 700 else 8)
    y = para('MATERIALS BOUNDARIES · v' + bundle['engine_version'], 26, size=11)
    y = para(t['title'], y, size=24 if width >= 700 else 21, bold=True)
    y = para(t['subtitle'], y)
    y = para(t['translation_notice'], y, size=12)
    elements.append('<g id="essential-scope">')
    y = para(t['scope_heading'], y + 6, size=16, bold=True)
    for key in SCOPE_KEYS:
        elements.append('<g data-warning-code="' + key + '">')
        y = para(t[key], y)
        elements.append('</g>')
    elements.append('</g><g id="glyph-legend">')
    y = para(t['glyph_legend'], y + 5, bold=True)
    elements.append('</g>')
    y = para(t['y_axis'], y + 6, size=14, bold=True, cls='axis-title y-axis-title')
    top, left, right = y + 6, margin + 39, width - margin - 8
    elements.append(f'<g id="temperature-plot" data-x-domain="15,125" data-y-domain="0,55" data-plot-left="{left}" data-plot-right="{right}" data-plot-top="{_fmt(top)}" data-plot-bottom="{_fmt(top+PLOT_HEIGHT)}">')
    elements.extend(_plot_elements(bundle, left=left, right=right, top=top))
    elements.append('</g>')
    y = para(t['x_axis'], top + PLOT_HEIGHT + 54, size=14, bold=True, cls='axis-title x-axis-title')
    y = para(t['axis_notice'], y, size=12)
    y = para(t['table_heading'], y + 14, size=19, bold=True)
    y = para(t['table_notice'], y, size=12)
    elements.append('<g id="exact-source-table">')
    headers = ('temperature', 'source_value', 'reported_sd', 'sample_count', 'record_cell')
    records = {record['id']: record for record in bundle['record_snapshots']}
    if width >= 700:
        fractions = (0, .13, .35, .52, .68)
        widths = (.11, .20, .15, .14, .32)
        ys = [para(t[key], y, x=margin+space*pos, available=space*span-8, size=11, bold=True)
              for key, pos, span in zip(headers, fractions, widths)]
        y = max(ys)
    for glyph in bundle['glyphs']:
        elements.append('<g class="source-row" data-record-id="' + escape(glyph['record_id'], quote=True) + '"><title>' + escape(records[glyph['record_id']]['name']) + '</title>')
        values = (glyph['temperature_value_string'], glyph['source_value_string'], glyph['sd_value_string'], str(glyph['sample_count']))
        elements.append(f'<line x1="{margin}" x2="{width-margin}" y1="{_fmt(y-8)}" y2="{_fmt(y-8)}" stroke="#aabac3"/>')
        locator = t['table_column'] + ': ' + glyph['source_cell']['temperature_column']
        if width >= 700:
            ys = [para(value, y+9, x=margin+space*pos, available=space*span-8, size=14, bold=True)
                  for value, pos, span in zip(values, fractions, widths)]
            record_y = para(glyph['record_id'], y + 7, x=margin+space*.68,
                            available=space*.32-8, size=11)
            record_y = para(locator, record_y - 3, x=margin+space*.68,
                            available=space*.32-8, size=11)
            y = max(*ys, record_y) + 5
        else:
            for key, value in zip(headers, values):
                y = para(t[key], y + 3, size=12, bold=True)
                y = para(value, y, size=16, bold=True)
            y = para(t['sd_type'], y, size=12)
            y = para(t['record'] + ': ' + glyph['record_id'], y, size=12)
            y = para(locator, y, size=12)
            y += 10
        elements.append('</g>')
    elements.append('</g>')
    elements.append('<g id="shared-source-locators">')
    cell = bundle['glyphs'][0]['source_cell']
    for key, value in (('table_row', cell['row']), ('table_container', cell['table_container_id']),
                       ('expanded_table', cell['expanded_table_id'])):
        y = para(t[key] + ': ' + value, y, size=11)
    table_url = bundle['record_snapshots'][0]['reported_result']['uncertainty']['evidence']['source_url']
    y = para(table_url, y, size=11, url=table_url)
    elements.append('</g><g id="protocol-summary">')
    y = para(t['protocol_heading'], y + 12, size=19, bold=True)
    for key in ('protocol_geometry', 'protocol_preparation', 'protocol_unknowns'):
        y = para(t[key], y)
    y = para(t['si_notice'], y, size=12)
    elements.append('</g><g id="source-summary">')
    y = para(t['source_heading'], y + 8, size=18, bold=True)
    first, source = bundle['record_snapshots'][0], bundle['source_snapshots'][0]
    y = para(t['source'] + ': ' + source['id'], y, size=11)
    y = para(first['verification']['rights']['attribution'], y, size=12)
    for key in ('revision', 'adaptation', 'metadata_exports', 'snapshot_notice'):
        y = para(t[key], y, size=12)
    for url in (source['urls'][0], first['verification']['rights']['license_url']):
        link_text = (source['license']['identifier'] + ': ' + url
                     if url == first['verification']['rights']['license_url'] else url)
        y = para(link_text, y, size=11, url=url)
    elements.append('</g>')
    height = math.ceil(y + 12)
    desc = t['plot_description'] + ' ' + t['glyph_legend']
    return (f'<svg xmlns="http://www.w3.org/2000/svg" lang="{lang}" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="document-title document-description">'
            '<title id="document-title">' + escape(t['title']) + '</title><desc id="document-description">' + escape(desc) + '</desc>'
            '<rect width="100%" height="100%" fill="#ffffff"/><style>text{font-family:' + FONT + '}</style>\n'
            + '\n'.join(elements) + '\n</svg>\n')


def render_observation_temperature_html(bundle, *, lang='en'):
    """Render script-free responsive HTML with an ordinary semantic table."""
    validate, canonical, safe_url, _ = _runtime()
    validate(bundle)
    t = labels(lang)
    canonical(bundle)
    out = ['<!doctype html><html lang="' + lang + '"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>' + escape(t['title']) + '</title><style>',
        'body{font-family:system-ui,"Noto Sans CJK JP",sans-serif;max-width:1100px;margin:auto;padding:14px;color:#183b4e;background:white;line-height:1.55}*{box-sizing:border-box}h1{font-size:1.9rem}h2{font-size:1.3rem}p,li,h1,h2,h3,a,pre,td,th{overflow-wrap:anywhere;min-width:0}p{margin:.6em 0}section{margin:24px 0}a{color:#065579}pre{white-space:pre-wrap;font-size:.85rem}.scope{border-left:3px solid #526976;padding-left:12px}.plot-wrap{margin-left:45px;margin-right:12px}.temperature-chart{display:block;width:100%;height:390px;overflow:visible}.temperature-chart text{font-family:DejaVu Sans,"Noto Sans CJK JP",sans-serif}.axis-title{font-size:1rem;font-weight:700}.legend{font-weight:600}.metadata{font-size:.85rem}.source-table{width:100%;border-collapse:collapse;table-layout:fixed}.source-table th,.source-table td{text-align:left;padding:10px 8px;vertical-align:top}.source-table thead{border-bottom:1px solid #aabac3}.source-table .source-identity{border-bottom:1px solid #aabac3;font-size:.85rem}.source-table .numeric{font-variant-numeric:tabular-nums;font-size:1.1rem}.mobile-label{display:none}summary{cursor:pointer} @media(max-width:699px){h1{font-size:1.5rem}.source-table,.source-table tbody,.source-table tr,.source-table th,.source-table td{display:block;width:100%}.source-table thead{position:absolute;width:1px;height:1px;overflow:hidden;clip-path:inset(50%)}.source-table td,.source-table th{padding:5px 0}.source-table .source-identity{padding-bottom:14px;margin-bottom:14px}.mobile-label{display:block;font-size:.85rem;font-weight:600}.source-table .numeric{font-size:1rem}}',
        '</style></head><body><header><p>MATERIALS BOUNDARIES · v' + escape(bundle['engine_version']) + '</p><h1>' + escape(t['title']) + '</h1>']
    def p(value, url=None, cls=None):
        text = escape(str(value))
        if url is not None:
            text = '<a href="' + escape(safe_url(url), quote=True) + '">' + text + '</a>'
        out.append('<p' + (' class="' + cls + '"' if cls else '') + '>' + text + '</p>')
    p(t['subtitle']); p(t['translation_notice'])
    out.append('</header><main><section class="scope" id="essential-scope"><h2>' + escape(t['scope_heading']) + '</h2>')
    for key in SCOPE_KEYS:
        out.append('<p data-warning-code="' + key + '">' + escape(t[key]) + '</p>')
    out.append('</section><figure style="margin:0"><p class="legend" id="glyph-legend">' + escape(t['glyph_legend']) + '</p>')
    p(t['y_axis'], cls='axis-title y-axis-title')
    out.append('<div class="plot-wrap"><svg xmlns="http://www.w3.org/2000/svg" id="temperature-plot" class="temperature-chart" role="img" aria-labelledby="plot-title plot-description" data-x-domain="15,125" data-y-domain="0,55"><title id="plot-title">' + escape(t['title']) + '</title><desc id="plot-description">' + escape(t['plot_description'] + ' ' + t['glyph_legend']) + '</desc>')
    out.extend(_plot_elements(bundle, left=0, right=100, top=10, responsive=True))
    out.append('</svg></div>')
    p(t['x_axis'], cls='axis-title x-axis-title')
    out.append('<figcaption>' + escape(t['axis_notice']) + '</figcaption></figure><section><h2>' + escape(t['table_heading']) + '</h2>')
    p(t['table_notice'])
    headers = ('temperature', 'source_value', 'reported_sd', 'sample_count')
    out.append('<table id="exact-source-table" class="source-table"><caption>' + escape(t['sd_type']) + '</caption><thead><tr>')
    for key in headers:
        out.append('<th id="col-' + key + '" scope="col">' + escape(t[key]) + '</th>')
    out.append('</tr></thead><tbody>')
    for index, glyph in enumerate(bundle['glyphs']):
        rid = 'condition-' + str(index)
        out.append('<tr class="source-row" data-record-id="' + escape(glyph['record_id'], quote=True) + '">')
        values = (glyph['temperature_value_string'], glyph['source_value_string'], glyph['sd_value_string'], str(glyph['sample_count']))
        for pos, (key, value) in enumerate(zip(headers, values)):
            tag = 'th' if pos == 0 else 'td'
            attr = ' id="' + rid + '" scope="row"' if pos == 0 else ' headers="' + rid + ' col-' + key + '"'
            out.append('<' + tag + attr + ' class="numeric"><span class="mobile-label" aria-hidden="true">' + escape(t[key]) + '</span>' + escape(value) + '</' + tag + '>')
        out.append('</tr><tr><td class="source-identity" colspan="4">')
        p(t['record'] + ': ' + glyph['record_id'])
        p(t['source_cell'] + ': ' + canonical(glyph['source_cell']))
        out.append('</td></tr>')
    out.append('</tbody></table></section><section><h2>' + escape(t['protocol_heading']) + '</h2>')
    for key in ('protocol_geometry', 'protocol_preparation', 'protocol_unknowns'):
        p(t[key])
    out.append('</section><section><h2>' + escape(t['source_heading']) + '</h2>')
    for value, url in _source_intro(bundle, t):
        p(value, url)
    out.append('</section>')
    p(t['metadata_exports'])
    out.append('<details id="audit-details"><summary>' + escape(t['audit_details']) + '</summary><section><h2>' + escape(t['si_heading']) + '</h2>')
    p(t['si_notice'])
    for r in bundle['record_snapshots']:
        si = r['si_result']
        p(r['conditions']['temperature']['value_string'] + ' °C: ' + str(si['value']) + ' ± ' + str(si['uncertainty_value']) + ' Pa')
    out.append('</section>')
    for heading, lines in _metadata_sections(bundle, t):
        out.append('<section><h2>' + escape(heading) + '</h2>')
        for value, url in lines:
            p(value, url, cls='metadata')
        out.append('</section>')
    p(t['snapshot_notice'])
    out.append('<details><summary>' + escape(t['details']) + '</summary><pre id="temperature-plot-json">' + escape(canonical(bundle, pretty=True)) + '</pre></details></details></main></body></html>\n')
    return ''.join(out)
