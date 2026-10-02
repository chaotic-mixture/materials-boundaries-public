"""Rebuild checked-in synthetic demonstration exports from the installed package.

Run from the repository root:
    python examples/temperature/regenerate.py
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from materials_boundaries.temperature_visualization import (  # noqa: E402
    build_temperature_comparison, comparison_csv, comparison_json,
    render_temperature_html, render_temperature_svg,
)


def main():
    selections = {
        'visualization': ['synthetic_linear_temperature', 'synthetic_overlap_temperature'],
        # This checked-in sample has a fixed membership; the CLI can plot all live models.
        'catalog-visualization': [
            'synthetic_linear_temperature', 'synthetic_overlap_temperature',
            'synthetic_quadratic_temperature', 'synthetic_quartic_temperature',
            'synthetic_interval_temperature',
        ],
    }
    for folder, model_ids in selections.items():
        target = Path(__file__).resolve().parent / folder
        target.mkdir(parents=True, exist_ok=True)
        bundle = build_temperature_comparison(model_ids, points_per_branch=101)
        artifacts = {
            'temperature-comparison.json': comparison_json(bundle),
            'temperature-comparison.csv': comparison_csv(bundle),
        }
        for lang in ('en', 'zh', 'ja', 'de'):
            artifacts[f'temperature-comparison.{lang}.html'] = render_temperature_html(bundle, lang=lang)
            artifacts[f'temperature-comparison.{lang}.svg'] = render_temperature_svg(bundle, lang=lang)
            artifacts[f'temperature-comparison.narrow.{lang}.svg'] = render_temperature_svg(bundle, lang=lang, width=380)
        for name, content in artifacts.items():
            (target / name).write_text(content, encoding='utf-8')


if __name__ == '__main__':
    main()
