#!/usr/bin/env python3
"""Generate deterministic examples for the one reviewed two-study profile.

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

from materials_boundaries.observation_study_comparison import (
    build_observation_study_comparison,
    observation_study_comparison_json,
    observation_study_comparison_csv,
    render_observation_study_comparison_svg,
    render_observation_study_comparison_html,
)

PROFILE_ID = "ciganas-zach-uts-temperature-v1"
LANGUAGES = ("en", "zh", "ja", "de")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--output", type=Path,
                        default=ROOT / "examples" / "observation-study-comparison")
    parser.add_argument("--lang", choices=LANGUAGES + ("all",), default="all")
    args = parser.parse_args()
    bundle = build_observation_study_comparison(profile_id=PROFILE_ID)
    prefix = "observation-study-comparison"
    artifacts = {
        f"{prefix}.json": observation_study_comparison_json(bundle),
        f"{prefix}.csv": observation_study_comparison_csv(bundle),
    }
    for lang in LANGUAGES if args.lang == "all" else (args.lang,):
        artifacts[f"{prefix}.{lang}.svg"] = render_observation_study_comparison_svg(
            bundle, lang=lang, width=1100)
        artifacts[f"{prefix}.narrow.{lang}.svg"] = render_observation_study_comparison_svg(
            bundle, lang=lang, width=380)
        artifacts[f"{prefix}.{lang}.html"] = render_observation_study_comparison_html(
            bundle, lang=lang)
    args.output.mkdir(parents=True, exist_ok=True)
    for filename, content in artifacts.items():
        (args.output / filename).write_text(content, encoding="utf-8", newline="\n")
    print(f"Generated {len(artifacts)} deterministic artifacts in {args.output}")


if __name__ == "__main__":
    main()
