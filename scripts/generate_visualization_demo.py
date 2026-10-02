#!/usr/bin/env python3
"""Generate deterministic, offline comparison artifacts from repository fixtures.

Runtime uses only the standard library. PNG/browser QA is an optional separate
step; no plotting dependency, network access or fracture calculator is needed.
"""
from pathlib import Path
import argparse
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from materials_boundaries import load_json
from materials_boundaries.visualization import build_comparison, comparison_json, render_html, render_svg


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "examples" / "visualization")
    parser.add_argument("--lang", choices=("en", "zh", "ja", "de", "all"), default="all")
    parser.add_argument("--without-classical", action="store_true", help="Hide Reuss/Voigt curves in the views, retain them in JSON")
    args = parser.parse_args()
    instances = [load_json(ROOT / "examples" / name) for name in
                 ("synthetic-two-phase.json", "literature-epoxy-glass-model.json")]
    bundle = build_comparison(instances)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "comparison.json").write_text(comparison_json(bundle), encoding="utf-8")
    for lang in ("en", "zh", "ja", "de") if args.lang == "all" else (args.lang,):
        (args.output / f"comparison.{lang}.html").write_text(
            render_html(bundle, lang=lang, include_classical=not args.without_classical), encoding="utf-8")
    for case in bundle["cases"]:
        (args.output / f'{case["id"]}.bulk.svg').write_text(
            render_svg(bundle, case["id"], lang="en" if args.lang == "all" else args.lang,
                       include_classical=not args.without_classical), encoding="utf-8")
    print(f"Generated canonical comparison JSON, offline HTML, and bulk SVGs in {args.output}")


if __name__ == "__main__":
    main()
