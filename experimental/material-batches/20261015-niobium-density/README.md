# Niobium density review candidate

This local packet advances the **same** Watanabe (2026) niobium candidate held
on 2026-10-14. It creates no additional candidate identity in the review count
and admits no material. The formal project total remains **1081 = 1057 + 24**;
the 62 excluded computed examples remain excluded.

The parent thread reports completed inspection of the article and both official
supplements. This packet transcribes that supplied evidence; it does not repeat
source acquisition or claim that the local curator inspected the source files.
The old access-challenge response remains failed-acquisition history and is not
used as article evidence or as an article checksum.

## Recorded fact and limits

Section 2.1.1 (PDF pages 4-5) reports Archimedes density **8587.6 kg/m³ at 293 K**
for a niobium cylinder approximately 100 mm long and 2.0011 mm in diameter,
containing at least 99.5 mass% Nb and about 0.12 wt% Ta. This is a source-specific
specimen, not certified pure Nb or a new grade. Its full composition is unknown.
No density is recalculated from the dimensions.

The density-specific uncertainty, repeat count, aggregation, immersion liquid,
buoyancy correction, and pre-measurement treatment/timing are not reported in
the inspected scope. The existing contract permits explicit unknowns:
`uncertainty: null`, `sample_count.value: null`, `summary_statistic: not_stated`
and facts with `text: null`. `density_basis` remains `not_stated`; naming the
Archimedes method alone does not identify bulk, true, or apparent density.

Section 3.1's six heating runs r41-r46 on one specimen are not density repeats.
Section 2.1.2's thermal treatment is not assigned to the density state. Section
2.4 supplies no density uncertainty. According to the parent's completed
inspection, MOESM1.xlsx (nine sheets) and MOESM2.zip (three files) contain none of
these missing density details. Supplement inspection is evidence about the
scope of absence, not another measurement.

## Source metadata and review status

The parent supplied the exact article title and actual source-inspection date,
**2026-10-15 UTC**, from the completed source review. The former null title/date
gap is resolved without using a curation date as a substitute. The former held
draft remains in commit `0adb122d0d8937301eb4815a6f8fdadafe84ea3d`; the three
current documents are explicitly named `*.candidate.json`.

`review.json` records actual retained-download completion times as `accessed_at`:
article HTML at 00:17:09Z, supplementary XLSX at 00:17:33Z, and supplementary ZIP
at 00:17:37Z, all on 2026-10-15. Supplement checks were completed **by** 00:18:07Z
and the final article cross-check **by** 00:18:32Z. These last two values are
completion upper bounds, not exact completion instants. No check is relabeled
as an independent human scientific review.

The complete candidate passes the three existing schemas and runtime graph
validator. A disposable in-memory merge adds one identity/state/property/source;
a second identical merge changes nothing. No result of that rehearsal is saved
to a runtime catalog. The source checksum remains honestly unavailable because
source bytes/digests were not handed to this local curator.

No runtime catalog, schema, pin, CI configuration, main branch, or frozen
`d4e9cf3` candidate is changed. This local packet still requires a review decision;
automatic validation cannot grant scientific or rights approval or formal
admission. All publication remains paused.

## Attribution and reuse scope

H. Watanabe, *Thermophysical Properties of Niobium (1000–2700 K): Multi-stepwise
Pulse-Heating Measurements with Consistency Validation via a Revised
Emissivity–Resistivity Relation*, *International Journal of Thermophysics*
**47**, 95 (2026),
[DOI 10.1007/s10765-026-03765-z](https://doi.org/10.1007/s10765-026-03765-z).
[Article](https://link.springer.com/article/10.1007/s10765-026-03765-z).
The parent verified the article-specific
[Creative Commons Attribution 4.0 license](https://creativecommons.org/licenses/by/4.0/).

This packet contains brief attributed facts and original curation notes, with
paraphrasing and catalog organization of the supplied evidence. It retains the
reported number and records unknowns explicitly. It contains no source PDF,
figure, copied table, supplement archive, raw structures or source binary.
The source is not relicensed as project MIT content; no author or publisher
endorsement is implied. This is not an independent legal or scientific review.

All four required locale slots use explicitly identified English fallback
labels; no verified translations are claimed. See `review.json` for identity
review scope, continuity and counts, and `VALIDATION.md` for actual checks and
their limits.
