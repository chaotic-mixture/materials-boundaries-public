# Migration to v0.25.0

One new explicit route is added:

```sh
python -m materials_boundaries observation compare-temperature-studies \
  --profile-id ciganas-zach-uts-temperature-v1 --output /tmp/two-studies --lang en
```

The new bundle/schema `observation_study_comparison` is **1.0.0**. Existing
inspection remains **1.1.0**, old Ciganas plot **1.0.0**, observations **1.3.0**,
and every scientific catalog/record/source payload remains unchanged. Exactly
eight composite evaluation rules remain. Saved prior bundles must be rebuilt
for the current software engine label; old checked-in examples are preserved.

This is descriptive juxtaposition of the six Ciganas source cells and four
Zach source cells. Protocols and limitations precede property values. Plots
remain separate and unconnected; SDs are always separate text, with no endpoints
or median ± SD interval. Ciganas central statistic is unnamed, Zach reports
medians and contextual SD units. Common axes do not establish matched methods,
statistical independence, a material ranking or a universal bound.

No old command defaults, single-study whisker policy, generic inspection axes
policy, CSV shape or prior fixture/example is rewritten. No source observation,
model, overlay, pooling, ratio, delta, uncertainty computation or evaluator is
added. The historical source limits remain intact; the new separately curated
named presentation profile supplies only its documented display policy.

Four locales, JSON/CSV and wide/narrow SVG/HTML use an isolated output prefix.
Read the [full guide](OBSERVATION_STUDY_COMPARISON.md) before interpreting values.
All artifacts are preflighted before writes; disk failures after preflight are
not guaranteed to roll back. Unsupported profiles and languages fail closed.

Validation is software/source-contract checking, not external scientific or
native-language approval. Static SVG raster QA and structural HTML tests are
separate from actual browser, keyboard, zoom or print QA. The latter were not
performed because the permitted local-file browser route was unavailable;
no alternate route was used to bypass that restriction. Source PDFs remain
uninspected and no publisher assets are bundled.
