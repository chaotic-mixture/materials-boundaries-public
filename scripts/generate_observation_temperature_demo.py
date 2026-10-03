#!/usr/bin/env python3
"""Generate deterministic examples for the one reviewed temperature dataset.

This standard-library-only helper leaves historical examples untouched. It
preflights all selected locale artifacts before creating targets; a later disk
failure is not guaranteed to roll back every file. Static/browser QA is separate.
"""
from pathlib import Path
import argparse
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from materials_boundaries.observation_temperature_plot import (
    build_observation_temperature_plot,
    temperature_observation_plot_json,
    temperature_observation_plot_csv,
    render_observation_temperature_svg,
    render_observation_temperature_html,
)

DATASET_ID = "ciganas-2026-pa12-cf15-fff-uts-temperature"
LANGUAGES = ("en", "zh", "ja", "de")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--output", type=Path,
                        default=ROOT / "examples" / "observation-temperature-plot")
    parser.add_argument("--lang", choices=LANGUAGES + ("all",), default="all")
    args = parser.parse_args()
    bundle = build_observation_temperature_plot(dataset_id=DATASET_ID)
    prefix = "observation-temperature-plot"
    artifacts = {
        f"{prefix}.json": temperature_observation_plot_json(bundle),
        f"{prefix}.csv": temperature_observation_plot_csv(bundle),
    }
    for lang in LANGUAGES if args.lang == "all" else (args.lang,):
        artifacts[f"{prefix}.{lang}.svg"] = render_observation_temperature_svg(
            bundle, lang=lang, width=1100)
        artifacts[f"{prefix}.narrow.{lang}.svg"] = render_observation_temperature_svg(
            bundle, lang=lang, width=380)
        artifacts[f"{prefix}.{lang}.html"] = render_observation_temperature_html(
            bundle, lang=lang)
    args.output.mkdir(parents=True, exist_ok=True)
    for filename, content in artifacts.items():
        (args.output / filename).write_text(content, encoding="utf-8", newline="\n")
    print(f"Generated {len(artifacts)} deterministic artifacts in {args.output}")


if __name__ == "__main__":
    main()
