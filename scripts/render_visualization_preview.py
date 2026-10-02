#!/usr/bin/env python3
"""Optional static PNG QA: compose the canonical SVG charts and render with Inkscape.

Requires an already installed Inkscape. This is SVG rendering, not browser/HTML
layout verification. No scientific values are calculated by this helper.
"""
from pathlib import Path
from html import escape
import argparse
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from materials_boundaries import load_json
from materials_boundaries.visualization import QUANTITIES, render_svg, validate_comparison


def compose(bundle: dict, *, narrow: bool, lang: str = "en") -> str:
    validate_comparison(bundle)
    expected = [load_json(ROOT / 'examples' / filename) for filename in
                ('synthetic-two-phase.json', 'literature-epoxy-glass-model.json')]
    if [case['input'] for case in bundle['cases']] != expected:
        raise ValueError('Overview labels are specific to the two bundled demo inputs; use render_svg for other cases')
    zh = lang == 'zh'
    width, chart_width = (380,340) if narrow else (1180,550)
    chart_height = 310 if narrow else 330
    columns = 1 if narrow else 2
    row_height = 338 if narrow else 360
    case_height = 110 + 4 // columns * row_height
    top = 230 if narrow else 190
    height = top + len(bundle['cases']) * case_height + 80
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img">',
           '<title>Conditional elastic bounds: synthetic and literature-model cases</title>',
           '<rect width="100%" height="100%" fill="#f7fafb"/>',
           '<style>text{font-family:sans-serif;fill:#173449}</style>']
    def text(x,y,value,size=16,color='#173449'):
        out.append(f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}">{escape(value)}</text>')
    text(20,27,'MATERIALS BOUNDARIES · v'+bundle['engine_version'],13)
    if narrow:
        text(20,63,'有条件弹性界限' if zh else 'Conditional elastic bounds',23)
        text(20,90,'独立案例 · 对齐坐标尺度' if zh else 'Separate cases · aligned scales',17)
        for i,line in enumerate(['阴影为理论界限区间，', '不是置信区间或测量不确定性。', 'E/ν 为推导外包络；不声称', '联合可达或紧致。', '自选体积分数扫描；圆点不是观测值。'] if zh else ['Shaded bands: theoretical intervals,', 'not confidence intervals or measurements.',
            'E/ν: derived outer envelopes; not jointly', 'attainable or tight by assertion.', 'Chosen fraction sweep; dots ≠ observations.']):
            text(20,120+i*20,line,14)
    else:
        text(20,65,'有条件弹性界限的并列比较' if zh else 'Conditional elastic bounds, side by side',32)
        text(20,100,'阴影为理论界限区间，不是置信区间或测量不确定性。' if zh else 'Shaded bands: theoretical intervals, not confidence intervals or measurement uncertainty.',17)
        text(20,127,'E/ν 为保守推导外包络；不声称端点联合可达或紧致。' if zh else 'E/ν: conservative derived outer envelopes; joint attainability and tightness are not asserted.',17)
        text(20,154,'横轴为自选的相体积分数扫描；圆点是计算参数，不是观测值。全部数值由规范计算引擎生成。' if zh else 'Chosen phase-fraction sweep; dots are evaluated parameters, not observations. All values: canonical engine.',16)
    for case_index,case in enumerate(bundle['cases']):
        y0=top+case_index*case_height
        label=('合成演示' if zh else 'Synthetic illustration') if case['input_provenance']['kind']=='synthetic' else ('文献环氧/玻璃模型' if zh else 'Literature epoxy/glass model')
        text(20,y0,label,22 if narrow else 25)
        text(20,y0+25, ('非测量结果 · f₂ = ' if zh else 'Not measurements · f₂ = ')+case['axis']['phase_id'],14)
        if narrow:
            text(20,y0+48,'未知：温度、牌号、固化状态、测量不确定性' if zh else 'Unknown: temperature, grade, cure, uncertainty',13)
            text(20,y0+70,'HS 实线；Reuss 虚线；Voigt 点线' if zh else 'HS (solid); Reuss (dashed); Voigt (dotted)',13)
        else:
            text(20,y0+51,'未知：温度、材料牌号、固化状态及测量不确定性。案例保持独立分面，不暗示具有相同的物理背景。' if zh else 'Unknown: temperature, material grade, cure state and measurement uncertainty. Separate facets prevent an implied common physical context.',14)
            text(20,y0+76,'青色实线/阴影：HS 界或推导外包络     橙色虚线：Reuss 下界     紫色点线：Voigt 上界' if zh else 'Teal solid/band: HS or derived envelope     Orange dashed: Reuss lower     Purple dotted: Voigt upper',14)
        for index,quantity in enumerate(QUANTITIES):
            svg=render_svg(bundle,case['id'],quantity,width=chart_width,lang=lang)
            svg=svg.replace('<svg ',f'<svg x="{20+(index%columns)*(chart_width+40)}" y="{y0+95+(index//columns)*row_height}" ',1)
            out.append(svg)
    if narrow:
        text(20,height-53,'已进行公式核对和软件测试；' if zh else 'Equation-cross-checked and software-tested;',13)
        text(20,height-32,'未经独立科学同行评审。' if zh else 'not independent scientific peer review.',13)
    else:
        text(20,height-42,'仅作独立分面：同单位不能确立物理可比性。完整条件、来源 ID、论断版本与数值检查见 comparison.json。' if zh else 'Separate facets only: units do not establish comparability. Full conditions, source IDs, claim versions and numerical checks: comparison.json.',15)
        text(20,height-17,'已进行公式核对和软件测试；未经独立科学同行评审。这是静态 SVG 预览，未进行断裂计算。' if zh else 'Equation-cross-checked and software-tested; not independently scientifically peer reviewed. Static SVG preview; no fracture calculations.',14)
    out.append('</svg>')
    return '\n'.join(out)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,default=ROOT/'examples/visualization/comparison.json',
                        help='Comparison bundle for the two unchanged bundled demo inputs')
    parser.add_argument('--output',type=Path,default=ROOT/'examples/visualization')
    parser.add_argument('--lang',choices=('en','zh'),default='en')
    args=parser.parse_args()
    inkscape=shutil.which('inkscape')
    if not inkscape:
        parser.error('Inkscape is required for PNG preview rendering; the standard demo generator does not require it')
    bundle=load_json(args.input);args.output.mkdir(parents=True,exist_ok=True)
    for name,narrow in [('desktop',False),('mobile',True)]:
        suffix = '.zh' if args.lang == 'zh' else ''
        svg_path=args.output/f'preview.{name}{suffix}.svg';png_path=args.output/f'preview.{name}{suffix}.png'
        svg_path.write_text(compose(bundle,narrow=narrow,lang=args.lang),encoding='utf-8')
        subprocess.run([inkscape,str(svg_path),'--export-type=png',f'--export-filename={png_path}'],check=True,capture_output=True)
        print(png_path)

if __name__=='__main__':main()
