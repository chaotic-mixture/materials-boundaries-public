"""Safe, inert rendering of one closed two-study descriptive profile.

Only validated source strings are converted to floats, solely for linear display
coordinates. No intervals, endpoints, fits, joins or transformed series are
constructed. This module deliberately does not import the older glyph builder.
"""
from html import escape
import math
import unicodedata

from ._observation_study_comparison_labels import FACT_IDS, SCOPE_KEYS, labels

PLOT_HEIGHT = 260
POINT_RADIUS = 4
INK = '#183b4e'
FONT = 'DejaVu Sans,Noto Sans CJK JP,Noto Sans CJK SC,sans-serif'
# Bibliographic identifiers are canonical source text, not translated labels.
_JOURNAL_CITATIONS = {
    'ciganas': 'Polymers 18(5), 563',
    'zach': 'Journal of Composites Science 9(11), 624',
}


def _runtime():
    from .observation_study_comparison import (
        validate_observation_study_comparison, _canonical, _safe_url, _require)
    return validate_observation_study_comparison, _canonical, _safe_url, _require


def _fmt(value):
    return format(value, '.6f').rstrip('0').rstrip('.')


def _text_lines(value, columns):
    """Wrap words, long identifiers and CJK without coupling old renderers.

    Widths are conservative em approximations. Closing punctuation stays with
    the preceding line; no font, browser, network or layout dependency is used.
    """
    def units(char):
        if unicodedata.combining(char):
            return 0
        return 2 if unicodedata.east_asian_width(char) in ('W', 'F') else 1
    lines, line, count = [], '', 0
    for word in str(value).split(' '):
        weight = sum(units(char) for char in word)
        if line and weight <= columns and count + 1 + weight > columns:
            lines.append(line.rstrip()); line, count = '', 0
        for char in (' ' if line else '') + word:
            step = units(char)
            if line and count + step > columns:
                lines.append(line.rstrip()); line, count = '', 0
            line += char; count += step
    if line:
        lines.append(line.rstrip())
    for index in range(1, len(lines)):
        while lines[index] and lines[index][0] in '.,;:!?)]}，。；：！？、）］」』':
            lines[index - 1] += lines[index][0]
            lines[index] = lines[index][1:]
    return [line for line in lines if line]


def _plot_elements(panel, *, left, right, top, responsive=False):
    """Central-only plotting with fixed domains; never calculate SD endpoints."""
    _, canonical, _, _ = _runtime()
    bottom = top + PLOT_HEIGHT
    def px(value):
        fraction = (float(value) - 15) / 140
        return _fmt(100 * fraction) + '%' if responsive else _fmt(left + fraction * (right - left))
    def py(value):
        return top + PLOT_HEIGHT * (1 - float(value) / 65)
    l, r = ('0', '100%') if responsive else (_fmt(left), _fmt(right))
    out = []
    for tick in (0, 10, 20, 30, 40, 50, 60):
        yy = py(tick)
        out.append(f'<line class="y-grid" x1="{l}" x2="{r}" y1="{_fmt(yy)}" y2="{_fmt(yy)}" stroke="#d5dce0"/>')
        xx = -9 if responsive else left - 9
        out.append(f'<text class="y-tick" x="{_fmt(xx)}" y="{_fmt(yy+4)}" text-anchor="end" font-size="12" fill="{INK}">{tick}</text>')
    out.append(f'<line class="y-axis" x1="{l}" x2="{l}" y1="{_fmt(top)}" y2="{_fmt(bottom)}" stroke="{INK}"/>')
    out.append(f'<line class="x-axis" x1="{l}" x2="{r}" y1="{_fmt(bottom)}" y2="{_fmt(bottom)}" stroke="{INK}"/>')
    for tick in (20, 40, 60, 80, 100, 120, 140):
        xx = px(tick)
        out.append(f'<line class="x-tick-mark" x1="{xx}" x2="{xx}" y1="{_fmt(bottom)}" y2="{_fmt(bottom+5)}" stroke="{INK}"/>')
        out.append(f'<text class="x-tick" x="{xx}" y="{_fmt(bottom+22)}" text-anchor="middle" font-size="11" fill="{INK}">{tick}</text>')
    for point in panel['points']:
        attrs = ''.join(' data-' + key + '="' + escape(value, quote=True) + '"' for key, value in (
            ('record-id', point['record_id']),
            ('temperature', point['temperature']['value_string']),
            ('central-value', point['central_value_string']),
            ('source-cell', canonical(point['source_cell']))))
        out.append(f'<circle class="observation-center"{attrs} cx="{px(point["temperature"]["value_string"])}" cy="{_fmt(py(point["central_value_string"]))}" r="{POINT_RADIUS}" fill="{INK}"/>')
    return out


def _source_lines(bundle, panel, t):
    """Concise, visible provenance; complete snapshots belong only in details."""
    source = next(s for s in bundle['source_snapshots'] if s['id'] == panel['study_id'])
    record = next(r for r in bundle['record_snapshots'] if r['id'] == panel['points'][0]['record_id'])
    pid = panel['panel_id']
    inspection = record['verification']['source_inspection']
    cell = panel['points'][0]['source_cell']
    evidence_url = record['reported_result']['uncertainty']['evidence']['source_url']
    yield ', '.join(source['authors']) + ' (' + str(source['year']) + '). ' + source['title'] + '. ' + _JOURNAL_CITATIONS[pid] + '.', None
    yield 'DOI: ' + source['doi'], 'https://doi.org/' + source['doi']
    yield t[pid + '_locator'], evidence_url
    yield t['component'] + ': ' + cell['table_container_id'] + ' / ' + cell['expanded_table_id'], None
    yield t['revision'] + ': ' + inspection['access_date'] + '; ' + t['updated'] + ': ' + inspection['html_latest_update_as_reported'], inspection['version_notes_url']
    yield t[pid + '_discrepancy'], None
    yield 'CC BY 4.0', record['verification']['rights']['license_url']


def _accessible_description(bundle, t):
    """Complete ordered alternative for the standalone root image.

    The root image role may flatten child semantics in assistive technology.
    Therefore its description contains all context before any property values,
    followed by exact separate SD rows and concise provenance. It is authored
    human-facing text, never a raw snapshot or machine-metadata dump.
    """
    parts = [t['subtitle'], t['scope_heading']]
    parts.extend(t[key] for key in SCOPE_KEYS)
    parts.extend((t['review'], t['protocol_heading']))
    for fact in FACT_IDS:
        parts.append(t['fact_' + fact])
        for pid in ('ciganas', 'zach'):
            parts.append(t[pid + '_name'] + ': ' + t[pid + '_' + fact])
    parts.extend(t[key] for key in ('glyph_legend', 'axis_notice', 'table_notice'))
    for panel in bundle['panels']:
        pid = panel['panel_id']
        parts.extend(t[pid + '_' + key] for key in
                     ('name', 'product', 'count', 'sd_notice', 'y_axis'))
        parts.append(t['table_heading'])
        for point in panel['points']:
            parts.append('; '.join((
                t['temperature'] + ': ' + point['temperature']['value_string'],
                t[pid + '_table_central'] + ': ' + point['central_value_string'],
                t[pid + '_table_sd'] + ': ' + point['reported_sd']['value_string'])))
    parts.append(t['source_heading'])
    for panel in bundle['panels']:
        parts.append(t[panel['panel_id'] + '_name'])
        parts.extend(value for value, _ in _source_lines(bundle, panel, t))
    parts.extend(t[key] for key in ('pdf_notice', 'adaptation', 'metadata_notice'))
    return '\n'.join(parts)


class _SvgWriter:
    def __init__(self):
        self.elements = []

    def para(self, value, x, y, available, *, size=12, bold=False, url=None, cls=None):
        _, _, safe_url, _ = _runtime()
        lines = _text_lines(value, max(8, int(available / (size * .62))))
        for line in lines:
            attrs = (' font-weight="700"' if bold else '')
            if cls:
                attrs += ' class="' + escape(cls, quote=True) + '"'
            text = f'<text x="{_fmt(x)}" y="{_fmt(y)}" font-size="{size}" fill="{INK}"{attrs}>' + escape(line) + '</text>'
            if url:
                text = '<a href="' + escape(safe_url(url), quote=True) + '">' + text + '</a>'
            self.elements.append(text)
            y += size * 1.4
        return y + 5


def _svg_panel_heading(writer, panel, t, x, y, available):
    """Measure/render authored heading text independently of observed values."""
    pid, para = panel['panel_id'], writer.para
    y = para(t[pid + '_name'], x, y, available, size=17, bold=True)
    y = para(t[pid + '_product'], x, y, available)
    y = para(t[pid + '_count'], x, y, available, size=11)
    y = para(t[pid + '_sd_notice'], x, y, available, size=11)
    y = para(t[pid + '_y_axis'], x, y + 4, available, size=12, bold=True)
    return y + 8


def _svg_panel(writer, panel, t, x, y, available, *, plot_top=None):
    """One equal-sized plot and one always-visible exact three-column table."""
    pid = panel['panel_id']
    out, para = writer.elements, writer.para
    out.append('<g class="study-panel" data-panel-id="' + pid + '">')
    top = _svg_panel_heading(writer, panel, t, x, y, available)
    if plot_top is not None:
        top = max(top, plot_top)
    left, right = x + 34, x + available - 8
    out.append(f'<g id="temperature-plot-{pid}" class="temperature-plot" data-x-domain="15,155" data-y-domain="0,65" data-plot-left="{_fmt(left)}" data-plot-right="{_fmt(right)}" data-plot-top="{_fmt(top)}" data-plot-bottom="{_fmt(top + PLOT_HEIGHT)}">')
    out.append('<title>' + escape(t[pid + '_name'] + ': ' + t[pid + '_y_axis']) + '</title><desc>' + escape(t['plot_description']) + '</desc>')
    out.extend(_plot_elements(panel, left=left, right=right, top=top))
    out.append('</g>')
    y = para(t['x_axis'], x, top + PLOT_HEIGHT + 44, available, bold=True)
    y = para(t['table_heading'], x, y + 5, available, size=13, bold=True)
    out.append('<g id="exact-source-table-' + pid + '" class="source-table" role="table" aria-label="' + escape(t[pid + '_name'] + ': ' + t['table_heading'], quote=True) + '">')
    # Headers wrap within three persistent columns even at 320 px. Values are
    # never aligned or joined across studies; every point keeps its own row.
    fractions, spans = (0, .24, .62), (.21, .35, .38)
    headers = (t['temperature'], t[pid + '_table_central'], t[pid + '_table_sd'])
    out.append('<g role="row" class="source-header">')
    ends = []
    for header, fraction, span in zip(headers, fractions, spans):
        out.append('<g role="columnheader">')
        ends.append(para(header, x + available * fraction, y, available * span - 5, size=11, bold=True))
        out.append('</g>')
    out.append('</g>')
    y = max(ends) + 4
    for point in panel['points']:
        out.append('<g class="source-row" role="row" data-record-id="' + escape(point['record_id'], quote=True) + '">')
        out.append(f'<line x1="{_fmt(x)}" x2="{_fmt(x+available)}" y1="{_fmt(y-10)}" y2="{_fmt(y-10)}" stroke="#d5dce0"/>')
        values = (point['temperature']['value_string'], point['central_value_string'], point['reported_sd']['value_string'])
        for value, fraction, span in zip(values, fractions, spans):
            out.append('<g role="cell">')
            para(value, x + available * fraction, y + 5, available * span - 5, size=14)
            out.append('</g>')
        y += 31
        out.append('</g>')
    out.append('</g></g>')
    return y + 15


def render_observation_study_comparison_svg(bundle, lang='en', width=1100):
    """Render complete standalone context, two plots, exact SD tables and rights."""
    validate, canonical, _, require = _runtime()
    validate(bundle)
    t = labels(lang)
    require(type(width) is int and 320 <= width <= 1600,
            'SVG width must be an integer in [320,1600]')
    canonical(bundle)  # Validate inert source text too; do not expose this dump.
    margin, gap = (24 if width >= 900 else 14), 26
    space = width - 2 * margin
    writer = _SvgWriter()
    out, para = writer.elements, writer.para
    y = para('MATERIALS BOUNDARIES · v' + bundle['engine_version'], margin, 24, space, size=10)
    y = para(t['title'], margin, y + 4, space, size=24 if width >= 900 else 20, bold=True)
    y = para(t['subtitle'], margin, y, space, size=13)
    out.append('<g id="essential-scope">')
    y = para(t['scope_heading'], margin, y + 6, space, size=16, bold=True)
    for key in SCOPE_KEYS:
        out.append('<g data-warning-code="' + key + '">')
        y = para(t[key], margin, y, space)
        out.append('</g>')
    # Review and display policy are essential, not hidden in audit details.
    y = para(t['review'], margin, y, space, size=11)
    out.append('</g><g id="protocol-facts">')
    y = para(t['protocol_heading'], margin, y + 8, space, size=16, bold=True)
    if width >= 900:
        label_width = 166
        column = (space - label_width - gap) / 2
        xs = (margin + label_width, margin + label_width + column + gap)
        y = max(para(t[pid + '_name'], xx, y, column, bold=True)
                for pid, xx in zip(('ciganas', 'zach'), xs))
        for fact in FACT_IDS:
            out.append('<g data-fact-id="' + fact + '">')
            yy = para(t['fact_' + fact], margin, y, label_width - 12, bold=True)
            y = max(yy, *(para(t[pid + '_' + fact], xx, y, column)
                         for pid, xx in zip(('ciganas', 'zach'), xs))) + 4
            out.append('</g>')
    else:
        for fact in FACT_IDS:
            out.append('<g data-fact-id="' + fact + '">')
            y = para(t['fact_' + fact], margin, y + 3, space, size=13, bold=True)
            for pid in ('ciganas', 'zach'):
                y = para(t[pid + '_name'] + ': ' + t[pid + '_' + fact], margin, y, space)
            out.append('</g>')
    out.append('</g><g id="glyph-legend">')
    y = para(t['glyph_legend'], margin, y + 10, space, bold=True)
    y = para(t['axis_notice'], margin, y, space, size=11)
    y = para(t['table_notice'], margin, y, space, size=11)
    out.append('</g>')
    if width >= 900:
        column = (space - gap) / 2
        plot_top = max(_svg_panel_heading(_SvgWriter(), panel, t, 0, y + 16, column)
                       for panel in bundle['panels'])
        y = max(_svg_panel(writer, panel, t, margin + index * (column + gap),
                           y + 16, column, plot_top=plot_top)
                for index, panel in enumerate(bundle['panels']))
    else:
        for panel in bundle['panels']:
            y = _svg_panel(writer, panel, t, margin, y + 16, space)
    out.append('<g id="source-context">')
    y = para(t['source_heading'], margin, y + 10, space, size=16, bold=True)
    def source_block(panel, x, start, available):
        yy = para(t[panel['panel_id'] + '_name'], x, start, available, size=13, bold=True)
        for value, url in _source_lines(bundle, panel, t):
            yy = para(value, x, yy, available, size=11, url=url)
        return yy
    if width >= 900:
        column = (space - gap) / 2
        y = max(source_block(panel, margin + index * (column + gap), y, column)
                for index, panel in enumerate(bundle['panels']))
    else:
        for panel in bundle['panels']:
            y = source_block(panel, margin, y + 8, space)
    for key in ('pdf_notice', 'adaptation', 'metadata_notice'):
        y = para(t[key], margin, y + 3, space, size=11)
    out.append('</g>')
    height = math.ceil(y + 14)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" lang="{lang}" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="document-title document-description">'
            '<title id="document-title">' + escape(t['title']) + '</title><desc id="document-description">' + escape(_accessible_description(bundle, t)) + '</desc>'
            '<rect width="100%" height="100%" fill="white"/><style>text{font-family:' + FONT + '}</style>\n'
            + '\n'.join(out) + '\n</svg>\n')


_HTML_STYLE = '''
*{box-sizing:border-box}body{font-family:system-ui,"Noto Sans CJK JP","Noto Sans CJK SC",sans-serif;max-width:1150px;margin:auto;padding:18px;color:#183b4e;background:#fff;line-height:1.5}h1{font-size:1.85rem}h2{font-size:1.25rem}h3{font-size:1.12rem}p{margin:.55em 0}p,h1,h2,h3,th,td,a,pre,summary{overflow-wrap:anywhere;min-width:0}section{margin:22px 0}a{color:#065579}a:focus-visible,summary:focus-visible{outline:3px solid #c06d00;outline-offset:3px}.scope{border-left:3px solid #526976;padding-left:12px}.protocol-facts,.source-table{width:100%;border-collapse:collapse;table-layout:fixed}.protocol-facts th,.protocol-facts td,.source-table th,.source-table td{text-align:left;vertical-align:top;padding:9px 8px;border-bottom:1px solid #d5dce0}.protocol-facts th:first-child{width:18%}.mobile-study{display:none}.panels,.sources{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:26px}.study-panel,.source-block{min-width:0}.panel-heading{min-height:15em}.panel-heading h2{margin-top:0}.panel-heading p{font-size:.9rem}.y-axis-title{font-weight:700}.plot-wrap{margin-left:36px;margin-right:8px}.temperature-chart{display:block;width:100%;height:304px;overflow:visible}.temperature-chart text{font-family:DejaVu Sans,"Noto Sans CJK JP","Noto Sans CJK SC",sans-serif}.x-axis-title{font-size:.92rem;font-weight:700;min-height:3em}.source-table{font-size:.92rem}.source-table caption{font-weight:700;text-align:left;margin-bottom:10px}.source-table th:first-child{width:24%}.source-table th:nth-child(2){width:38%}.source-table th:nth-child(3){width:38%}.source-table td,.source-table tbody th{font-size:1rem;font-variant-numeric:tabular-nums}.legend{font-weight:650}.notice,.sources,.audit-notice{font-size:.88rem}pre{white-space:pre-wrap;font-size:.8rem}summary{cursor:pointer;padding:12px 0}details{border-top:1px solid #aabac3;margin:24px 0}
@media(max-width:899px){body{padding:14px}h1{font-size:1.5rem}.panels,.sources{grid-template-columns:minmax(0,1fr)}.panel-heading{min-height:0}.study-panel{margin-bottom:18px}.protocol-facts,.protocol-facts tbody,.protocol-facts tr,.protocol-facts td,.protocol-facts th{display:block;width:100%}.protocol-facts thead{position:absolute;width:1px;height:1px;overflow:hidden;clip-path:inset(50%)}.protocol-facts th:first-child{width:100%;padding-top:13px}.protocol-facts td{border:0;padding:7px 0}.protocol-facts tbody th{padding-left:0}.mobile-study{display:block;font-weight:650}.source-table th,.source-table td{padding:8px 5px}.x-axis-title{min-height:0}}
@media print{body{max-width:none;padding:0;font-size:10pt}.panels,.sources{grid-template-columns:minmax(0,1fr)}.panel-heading{min-height:0}.study-panel,.source-table,.source-block{break-inside:avoid}.scope{border-color:#183b4e}details:not([open]){display:none}a{color:inherit}.temperature-chart{print-color-adjust:exact}.protocol-facts tr{break-inside:avoid}}
'''


def render_observation_study_comparison_html(bundle, lang='en'):
    """Offline responsive HTML with semantic tables and inert audit disclosure."""
    validate, canonical, safe_url, _ = _runtime()
    validate(bundle)
    t = labels(lang)
    canonical(bundle)
    out = ['<!doctype html><html lang="' + lang + '"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>' + escape(t['title']) + '</title><style>' + _HTML_STYLE + '</style></head><body><header><p>MATERIALS BOUNDARIES · v' + escape(bundle['engine_version']) + '</p><h1>' + escape(t['title']) + '</h1><p>' + escape(t['subtitle']) + '</p></header><main>']
    def p(value, *, url=None, cls=None):
        value = escape(str(value))
        if url:
            value = '<a href="' + escape(safe_url(url), quote=True) + '">' + value + '</a>'
        out.append('<p' + (' class="' + cls + '"' if cls else '') + '>' + value + '</p>')
    out.append('<section class="scope" id="essential-scope" aria-labelledby="scope-title"><h2 id="scope-title">' + escape(t['scope_heading']) + '</h2>')
    for key in SCOPE_KEYS:
        out.append('<p data-warning-code="' + key + '">' + escape(t[key]) + '</p>')
    p(t['review'], cls='notice')
    out.append('</section><section aria-labelledby="protocol-title"><h2 id="protocol-title">' + escape(t['protocol_heading']) + '</h2><table id="protocol-facts" class="protocol-facts"><thead><tr><th scope="col">' + escape(t['protocol_heading']) + '</th>')
    for pid in ('ciganas', 'zach'):
        out.append('<th scope="col">' + escape(t[pid + '_name']) + '</th>')
    out.append('</tr></thead><tbody>')
    for fact in FACT_IDS:
        out.append('<tr data-fact-id="' + fact + '"><th scope="row">' + escape(t['fact_' + fact]) + '</th>')
        for pid in ('ciganas', 'zach'):
            out.append('<td><span class="mobile-study" aria-hidden="true">' + escape(t[pid + '_name']) + '</span>' + escape(t[pid + '_' + fact]) + '</td>')
        out.append('</tr>')
    out.append('</tbody></table></section><section id="glyph-legend" aria-label="' + escape(t['scope_heading'], quote=True) + '">')
    p(t['glyph_legend'], cls='legend'); p(t['axis_notice'], cls='notice'); p(t['table_notice'], cls='notice')
    out.append('</section><div class="panels">')
    for panel in bundle['panels']:
        pid = panel['panel_id']
        out.append('<section class="study-panel" data-panel-id="' + pid + '" aria-labelledby="panel-title-' + pid + '"><div class="panel-heading"><h2 id="panel-title-' + pid + '">' + escape(t[pid + '_name']) + '</h2>')
        for key in ('product', 'count', 'sd_notice'):
            p(t[pid + '_' + key])
        p(t[pid + '_y_axis'], cls='y-axis-title')
        out.append('</div><figure style="margin:0"><div class="plot-wrap"><svg xmlns="http://www.w3.org/2000/svg" id="temperature-plot-' + pid + '" class="temperature-chart temperature-plot" role="img" aria-labelledby="plot-title-' + pid + ' plot-description-' + pid + '" data-x-domain="15,155" data-y-domain="0,65" data-plot-left="0" data-plot-right="100%" data-plot-top="10" data-plot-bottom="270"><title id="plot-title-' + pid + '">' + escape(t[pid + '_name'] + ': ' + t[pid + '_y_axis']) + '</title><desc id="plot-description-' + pid + '">' + escape(t['plot_description'] + ' ' + t['glyph_legend']) + '</desc>')
        out.extend(_plot_elements(panel, left=0, right=100, top=10, responsive=True))
        out.append('</svg></div><figcaption class="x-axis-title">' + escape(t['x_axis']) + '</figcaption></figure>')
        out.append('<table id="exact-source-table-' + pid + '" class="source-table"><caption>' + escape(t['table_heading']) + '</caption><thead><tr>')
        for name, title in (('temperature', t['temperature']), ('central', t[pid + '_table_central']), ('sd', t[pid + '_table_sd'])):
            out.append('<th id="' + pid + '-col-' + name + '" scope="col">' + escape(title) + '</th>')
        out.append('</tr></thead><tbody>')
        for index, point in enumerate(panel['points']):
            rid = pid + '-condition-' + str(index)
            out.append('<tr class="source-row" data-record-id="' + escape(point['record_id'], quote=True) + '"><th id="' + rid + '" scope="row">' + escape(point['temperature']['value_string']) + '</th>')
            for name, value in (('central', point['central_value_string']), ('sd', point['reported_sd']['value_string'])):
                out.append('<td headers="' + rid + ' ' + pid + '-col-' + name + '">' + escape(value) + '</td>')
            out.append('</tr>')
        out.append('</tbody></table></section>')
    out.append('</div><section id="source-context" aria-labelledby="source-title"><h2 id="source-title">' + escape(t['source_heading']) + '</h2><div class="sources">')
    for panel in bundle['panels']:
        pid = panel['panel_id']
        out.append('<section class="source-block" aria-labelledby="source-' + pid + '"><h3 id="source-' + pid + '">' + escape(t[pid + '_name']) + '</h3>')
        for value, url in _source_lines(bundle, panel, t):
            p(value, url=url)
        out.append('</section>')
    out.append('</div>')
    for key in ('pdf_notice', 'adaptation', 'metadata_notice'):
        p(t[key], cls='audit-notice')
    out.append('</section><details id="audit-details"><summary>' + escape(t['details']) + '</summary><pre id="study-comparison-json">' + escape(canonical(bundle, pretty=True)) + '</pre></details></main></body></html>\n')
    return ''.join(out)
