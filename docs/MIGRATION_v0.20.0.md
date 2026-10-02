# Migration to v0.20.0

Version **0.20.0** adds an isolated **offline observation inspection view** of the
six existing records from three studies. It adds no scientific records, source
ingestion, evaluator or matched-condition comparison. This document does not
declare a published tag, release date or software DOI.

## Version and contract changes

- Software/package/engine version: **0.19.0 → 0.20.0**
- New closed observation-inspection bundle schema: **1.0.0**
- Existing observations schema **1.2.0**, claims **1.11.0**, sources **1.0.0**,
  evaluation **1.1.0** and existing comparison schemas remain unchanged
- **36 mechanics claims, 51 source records, 6 observations from 3 studies,
  6 computational predictions and 5 synthetic temperature demos with 7 branches**,
  all preserved
- Exactly **8 executable composite rules**, with unchanged numerical behavior,
  applicability, evidence and order

The new module is `materials_boundaries.observation_visualization`. Observation
records, source records and source-family scientific contracts are unchanged.
Composite, computational-prediction and synthetic-temperature pipelines remain
separate. Existing generated artifacts remain historical; regenerating them may
change software-version metadata but does not authorize changing their science.
Earlier migration notes retain the features and exclusions of those releases.

## New interface

```sh
python -m materials_boundaries observation inspect --output /tmp/inspection --lang en
python -m materials_boundaries observation inspect --output /tmp/inspection-hbn --source-id falin_et_al_2017_hbn_mechanical_properties --group-by quantity --lang de
python -m materials_boundaries observation inspect --output /tmp/inspection-selected --id lee_2008_graphene_in_plane_stiffness_2d --id falin_2017_hbn_monolayer_breaking_strength_2d
```

`--id` is repeatable; `--source-id` and `--quantity` use exact case-sensitive
matches. All filters combine with AND. Supported quantities are
`in_plane_stiffness_2d` and `breaking_strength_2d`. The default is all six records,
grouped by study in packaged order. `--group-by quantity` changes navigation,
not interpretation. IDs do not request numeric or user-supplied ordering.
Unknown/malformed/duplicate IDs, unsupported selectors or scientific families,
and empty results are rejected before artifacts are written. Existing `catalog`
queries are unchanged.

Each call exports canonical JSON, CSV, wide SVG, narrow SVG and standalone HTML.
Human labels/notices support `en`, `zh`, `ja`, `de`; JSON, CSV, source wording,
values, IDs and digests are locale-independent. Details and the Python API are in
[the inspection guide](OBSERVATION_INSPECTION.md).

## Presentation and scientific boundaries

Facets retain record/version/source identity, quantity and N/m unit,
experiment-derived/model-dependent status, essential source-specific caveats,
uncertainty semantics and artifact evidence, scoped samples, known and unknown
conditions, verification limits and rights. Warnings are visible before values,
including MoS2 strength-only selections. Normalized catalog-derived displays
remain separate from original source strings; no missing graphene source string
is fabricated and no hBN GPa source context becomes a selected 3D result.

- **MoS2:** source-reported values retain the unresolved printed-q discrepancy,
  unknown actual fit q and no refit/correction. The proof-formatted EPFL artifact
  and unverified final-text/pagination identity remain explicit. Strength retains
  its fitted-stiffness caveat and finite-spherical-tip local maximum stress model
- **Graphene:** reported ± has unverified statistical meaning. Separate stiffness
  distribution SD/counts never replace the selected ± or migrate to strength.
  Its stress/strain convention remains source-specific
- **hBN:** strength remains nonlinear FEM volume-averaged under-indenter stress,
  with exact central-statistic label and stress component unknown. S5's maximum
  Von Mises diagnostic and sensitivity discussion are not an uncertainty
  correction. SD/count evidence retains the peer-review author-response locator;
  N=11 is not a verified strength failure-event count

There are no quantitative axes, points, bars, uncertainty endpoints, shared scales,
overlays, aggregation, ratios, rankings, interpolation, refitting, thickness
conversions or invented condition equivalence. Stiffness and strength remain
separate quantities. SD is not SEM, a confidence interval, coverage claim, hard
bound or full uncertainty budget. Counts, translation rates, preparation
conditions, numerical FEM steps and model thickness retain their existing scopes.

## Reproducibility and migration of saved bundles

Full unchanged record/source snapshots, observation versions, scientific-schema
versions, engine version, resolved selection and stable facet references are
retained. Canonical SHA-256 digests identify bundled metadata, not paper bytes.
No source-record version or source-artifact hash is invented. Policy explicitly
forbids overlay, aggregation and treating unknown conditions as equal.

Every renderer/export canonically rebuilds and compares the bundle using current
packaged catalogs. Stale or tampered scientific fields, caveats, snapshots,
metadata, selectors, policy, facets, digests or versions fail closed. Regenerate
from reviewed selection when changing software/catalog versions; never silently
relabel old bundles. Complete content is validated before filesystem writes.
HTML is script-free and network-free except reader-followed source links.

## Verification checklist

```sh
python scripts/validate_catalogs.py
python -m unittest discover -s tests -v
python -m materials_boundaries observation inspect --help --lang en
python -m materials_boundaries observation inspect --help --lang zh
python -m materials_boundaries observation inspect --help --lang ja
python -m materials_boundaries observation inspect --help --lang de
python -m materials_boundaries observation inspect --output /tmp/inspection-check --source-id bertolazzi_brivio_kis_2011 --quantity breaking_strength_2d
```

Also check installed-wheel metadata/CLI, deterministic JSON/CSV in all locales,
exact old-record preservation, fail-closed invalid selections/tampered bundles,
source-specific caveat-before-value ordering and unchanged eight-rule evaluation.
Inspect actual wide/narrow SVG pixels in all four languages, including long
IDs/URLs, German wrapping and CJK. Check HTML reflow at 320/380/1100 px where
browser support permits. Record static rendering separately from actual browser
QA; this checklist is not a claim that those checks passed.

No source media or raw measurement collection is bundled. NIST cryogenic
coefficient datasets and derived examples remain conservatively omitted.
Working translations, source transcription and software checks are not
independent scientific review, native-language review or replication.
