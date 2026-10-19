# EPDM/RT70HC Hostatron candidate packet (2026-10-19)

This packet adds three candidate composite identities, three states and three
measured geometrical-density properties against
`a592c89ede0dcced22579e56fc68b6fab4c55f49`. It reuses
`bianchi_2022_epdm_pcm` unchanged and introduces no grade or schema extension.
The candidate formal-admission delta is **0**. Runtime and formal catalogs are
not edited by this packet.

| Source formulation | RT70HC (phr) | Source nominal wt% | Geometrical density (g/cm3) |
|---|---:|---:|---:|
| EPDM_H_P20 | 33.0 | 20.0 | 0.55 +/- 0.02 |
| EPDM_H_P40 | 87.0 | 40.0 | 0.66 +/- 0.01 |
| EPDM_H_P60 | 196.0 | 60.0 | 0.70 +/- 0.01 |

Each formulation contains the Table 1 compound plus 1.3 phr Hostatron P0168.
The common recipe and all source locators are recorded in `review.json`.
Paraffin recipe amounts distinguish these identities; methods, temperature,
porosity, replicates and translations do not. The actual baseline has six
composite identities: the unfoamed EPDM/N550 reference, NC1, NC2, B10, B20 and
B30. The reference EPDM identity is composite, not polymer, in the inspected
baseline. None of the three selected paraffin formulations is already present.
`grade_id` is null because a matrix supplier designation is not a grade for the
finished composite. All four language slots contain English fallback labels.

The source is Bianchi et al. (2022), DOI
[10.3390/polym14194058](https://doi.org/10.3390/polym14194058).
Use the [versioned official PDF](https://mdpi-res.com/d_attachment/polymers/polymers-14-04058/article_deploy/polymers-14-04058-v2.pdf?version=1664434800):
p.3 Table 1, pp.4-5 preparation/Tables 2-3, pp.5-6 section 2.3.2,
and p.10 Table 5. Its p.1 notice specifies
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
The selected original tables have no separate third-party credit. Attribution,
license, factual transcription and adaptations are recorded in `review.json`;
no PDF, image, complete table, raw data or structure asset is included.

The density is measured mass divided by external geometric volume, including
open and closed pores, using ten square specimens. The printed central value
is `reported_value`; the printed amplitude is
`reported_plus_minus_unspecified`, not an inferred SD, SE or confidence bound.
Temperature, humidity and post-cure conditioning remain unknown. Do not copy
23.0 deg C, 0.2 g or sixty replicates from helium pycnometry. Do not substitute
rho_app, theoretical rho_bulk, porosity or density-normalized tensile E*.

Keep the printed phr recipe and nominal wt% distinct. Section 2.2 and Table 3
use percentage wording whose denominator scope is not fully resolved here.
No normalization or measured final cured composition is inferred. The source's
theoretical EPDM density inconsistency (1.042 versus 0.996 g/cm3) remains
explicit; it does not justify changing a measured rho_geom cell.

This task reread the official PDF text and checked selected cells against row
labels and column headings. Screenshot calls did not yield a viewable image;
no new visual check is claimed. No local Bianchi PDF was found or retained and
no binary hash was recomputed. New property records therefore use a null
SHA-256 with `hash_status: not_retained`; the unchanged source record retains
its historical digest without claiming it was reverified on 2026-10-19.
Source transcription is not independent scientific review or raw-data
reanalysis; both flags remain false. No product test was run for this packet.
The optional fixture records selected source facts for parent-authored checks
and is not evidence that those checks ran.

Files: `materials.append.json`, `reference-properties.append.json`,
`sources.reused.json` and `review.json`. The existing hash-bound offline
`scripts/integrate_material_candidates.py` flow can consume these files after
parent preparation of a manifest. This packet does not modify that command,
run it, admit candidates automatically, or publish anything.
