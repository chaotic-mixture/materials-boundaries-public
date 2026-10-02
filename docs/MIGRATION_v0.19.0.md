# Migration to v0.19.0

Version **0.19.0** adds exactly two **catalog-only monolayer hBN observations**
from Falin et al. (2017) and one source record. It does not declare a published
tag, release date or software DOI. All earlier scientific records retain their
meaning, including the MoS2 printed-q discrepancy and the bulk-wave contracts.

## Catalog and schema delta

- **6 observations from 3 studies**, up from 4 observations from 2 studies, by
  appending `falin_2017_hbn_monolayer_in_plane_stiffness_2d` and
  `falin_2017_hbn_monolayer_breaking_strength_2d`
- **51 sources**, up from 50, by appending
  `falin_et_al_2017_hbn_mechanical_properties`; this is 50 bibliographic/source
  records plus one original synthetic-demo provenance record
- Software/package/engine version **0.19.0**; observations schema **1.1.0 → 1.2.0**
- Claims schema **1.11.0**, sources schema **1.0.0**, evaluation schema **1.1.0**
  and the other scientific schemas are unchanged
- **36 mechanics claims**, **6 computational predictions** and **5 synthetic
  temperature demos with 7 branches**, unchanged
- Exactly **8 executable composite rules**, with unchanged numerical behavior,
  rule order, applicability and evidence

The new records use `observation_type: experiment_derived_model_dependent`,
`quantity_dimension: force_per_length`, `si_unit: N/m` and
`evaluation_support: catalog_only`. They share one study and the separate closed
family `falin_2017_hbn_monolayer_indentation_v1`. The family does not inherit
Lee or MoS2 stress/strain conventions, uncertainty provenance, geometry or
conditions. Existing four observation objects, 50 source objects and all claim
objects are preserved; the envelope change does not rewrite their science.

## Scientific contract

1. **Exact printed summaries:** stiffness **289 ± 24 N/m**, strength
   **23.6 ± 1.8 N/m**. Both N/m values are explicitly printed by the source;
   neither is a curator conversion from a volumetric value. The source-used
   **0.334 nm** thickness is provenance for its FEM/volumetric convention, not
   a default, measured apparent AFM height or automatic conversion rule
2. **Artifact-specific SD evidence:** `reported_standard_deviation` is backed
   by the publisher-linked peer-review author response, **PDF p. 8,
   Reviewer #1 question 3**, which refers to Figs. 3–4. Main-text ± notation
   alone is not an explicit SD definition. No SEM, confidence level, coverage
   factor, hard bounds or fully specified averaging/weighting convention is inferred
3. **Count scope:** N=11 denotes tested sheets and is explicitly associated
   with the stiffness average. It does not verify eleven strength replicates
   or failure events. Typically five increasing-load indentations per sheet
   does not establish exactly 55 curves. Acquired/retained/excluded curve totals,
   parent-flake count and failure-event count remain unknown
4. **Separate inference models:** stiffness uses the source's circular-membrane
   force–deflection fit, with ν=0.211 adopted as an input. Strength uses nonlinear
   finite-element loading matched to fracture loads and **volume-averaged
   stresses in membrane elements directly beneath the finite-radius indenter**.
   It is not direct uniform tension, a local-maximum formula or the diagnostic
   **maximum Von Mises stress** plotted in Supplementary Fig. S5
5. **Unknown finite-strain measures:** Eq. (4), σ=Eε+Dε², does not explicitly
   define its stress/strain measures. Fig. 5's nominal strain and S5's diagnostic
   label do not establish a Cauchy/Piola/Lagrangian convention or specify the
   invariant/component used for the volume average. Keep these gaps explicit
6. **Conditions and rate:** ambient is qualitative; numerical temperature,
   pressure, gas composition and humidity remain null. **0.5 μm/s** is reported
   loading/unloading probe translation velocity, not strain/stress/force rate.
   A FEM increment of 0.1 nm per step is not experimental rate
7. **q arithmetic without a mismatch claim:** the source prints
   q=1/(1.049−0.15ν−0.16ν²) and ν=0.211. Curator arithmetic gives
   **0.9898768854482001**. No separate numerical q was found in the source;
   the actual fit implementation/constant was not inspected. Do not present
   the arithmetic as a measured/fitted value, a correction or a q inconsistency

The strength central-statistic label is not separately specified; do not
silently turn it into a verified mean. Preserve the source rounding rather
than regenerating any selected value from 3D numbers or re-fitting. The
[observation guide](OBSERVATIONS.md#monolayer-hbn-falin-et-al-2017-new-records)
gives specimen, instrument, model and evidence details.

## Compatibility and exclusions

Readers pinning observation schema 1.1.0 or assuming exactly four records must
update envelope handling. Select by stable ID and retain catalog order. The
new method family is a closed scientific contract, not permission to accept
arbitrary experimental families. Display names and authored warnings exist in
en/zh/ja/de; IDs, values, units, evidence and JSON remain language-independent.
Existing literal all-term queries and exact filters retain their meaning.

There is **no new evaluator, fit/refit, thickness conversion, plot, ranking,
comparison, automatic overlay or specimen-applicability state**. `validate`,
`evaluate` and composite comparisons still accept their existing inputs only.
Bilayer/few-layer hBN, graphene controls from this paper, DFT/interlayer/sliding
predictions and digitized graph values are excluded. Unknown environments do
not justify matched-condition cross-study comparison.

Graphene's `reported_plus_minus_unspecified` notation is unchanged. **The
MoS2 printed-q discrepancy and unresolved actual fit constant remain
prominent and unchanged**; hBN's q treatment does not resolve them. Its separate
proof-formatted artifact and unverified final text/supplement status also remain.
NIST cryogenic coefficient datasets and derived examples remain conservatively
omitted. Synthetic temperature data, all predictions, previous claims and the
eight-rule registry are preserved. Historical generated examples are not
relabeled as newly generated results; software version labels may change
without numerical changes.

## Evidence, reuse and review limits

Falin et al., [“Mechanical properties of atomically thin boron nitride and the
role of interlayer interactions”](https://doi.org/10.1038/ncomms15815),
*Nature Communications* 8, 15815 (2017), is the added source. Inspection covers
published publisher HTML and equation images, selected supplement material
(including visual checks of PDF pp. 4–5, Figs. S4–S5), and the peer-review author
response (PDF p. 8). Main article PDF pagination is not claimed. A second-reader
transcription check does not establish independent scientific review or replication.
No raw AFM curves, fit code or FEM deck was reanalysed. Supporting data are
available from the corresponding author on request according to the article;
no author request or public raw-data availability is claimed.

The article is ©2017 The Author(s), licensed
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), with contrary
third-party credit lines excepted. Separate supplement and peer-review-file
license scope is **unverified**, so neither receives an automatic CC BY label.
Only brief factual values, bibliographic metadata, locators, mathematical
source context and original curation are bundled. No paper PDF, full text,
figure, screenshot, peer-review report or raw experimental collection is
redistributed. MIT applies to original project work and does not replace source
licenses. See [source ledger](SOURCES.md) and
[third-party notices](../THIRD_PARTY_NOTICES.md).

## Verification checklist

From the repository root, with the complete development dependencies:

```sh
python scripts/validate_catalogs.py
python -m unittest discover -s tests -v
python -m materials_boundaries catalog observations --source-id falin_et_al_2017_hbn_mechanical_properties --json
python -m materials_boundaries catalog observations --query hBN --text --lang en
python -m materials_boundaries catalog observations --query hBN --text --lang zh
python -m materials_boundaries catalog observations --query hBN --text --lang ja
python -m materials_boundaries catalog observations --query hBN --text --lang de
```

Check exact appended records/source, preservation of previous objects, closed
family routing, malformed scientific-metadata rejection, SD evidence and count
scope, source-printed units, model/diagnostic separation, unknown measures and
environment, q arithmetic status, four-language output, installed-wheel behavior
and unchanged eight-rule numerical evaluation. This is a checklist, not a claim
that a specific run passed. Software tests and source transcription do not
replace independent scientific or native-language review.
