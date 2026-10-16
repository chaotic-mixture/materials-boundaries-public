# Four NBS halide density candidates

This local review packet proposes four composition-level inorganic identities, each with one source-qualified state and one source-reported crystallographic density. It changes no production catalog, schema, admission manifest or application behavior. The formal project total remains **1081 = 1057 legacy identities + 24 admitted computational compositions**. The 62 unadmitted computational examples remain excluded. Candidate counts are not formal progress.

Base commit: `4c5656cf6ba0ad1a54b736e0568e97abe4815c29`.

| Candidate | Source-qualified sample | Density (g/cm^3) | Density reference temperature |
| --- | --- | --- | --- |
| Potassium bromide, KBr | J. T. Baker no. 111642; ACS reagent compliance | 2.7533 | 25 degrees C |
| Potassium iodide, KI | B. R. Elk & Company no. E-PF-3; annealed at 450 degrees C for 30 minutes | 3.1257 | 25 degrees C |
| Sodium fluoride, NaF | J. T. Baker no. 7445; ACS compliance; recrystallized by sublimation | 2.799 | Not reported in the inspected density sentence |
| Barium fluoride, BaF2 | Specially purified Mallinckrodt material; no specimen number reported | 4.886 | 26 degrees C |

The authors calculated these densities from experimental NBS X-ray lattice measurements, crystal structure and four formula units per conventional cell. They are crystallographic densities, not direct specimen bulk/pycnometric measurements, powder-packing densities, DFT predictions, means or engineering allowables. Values and decimal precision are retained without recalculation. No numerical lattice constants or uncertainty propagation are introduced.

## Conditions that must remain distinct

- NaF's corrected lattice table has a 25 degrees C context, while its powder pattern has a 26 degrees C context. The density sentence supplies neither temperature. The property therefore retains an unknown density temperature and separately names the two other contexts.
- KI's 450 degrees C treatment is sample preparation. Its density reference temperature is 25 degrees C. Moisture removal after treatment is only presumed, not evidence of a water-free sample.
- BaF2's reported sodium and strontium impurity range is 0.01 to 0.1 percent. No mass/atom-percent basis or total purity is inferred.
- KBr's selected source describes a face-centered cubic phase. Its separate pycnometric comparison belongs to another author and is excluded from this density's method.
- Density uncertainty, pressure and independent specimen/repeat counts remain unknown. Lattice error, diffraction-line counts, four formula units and supplier numbers cannot fill those gaps.

## Identity and source scope

Formal and existing local-candidate snapshots were checked before this packet was created. The checks found no target identity by multilingual names, aliases, formula order/Unicode variants, or complete element-count maps. Supporting private receipts record their hashes and limitations in `review.json`. A no-hit result supports a candidate for review, not automatic admission or universal chemical-equivalence proof.

The identity is the composition. Supplier, reagent compliance, sample number, preparation, phase state or temperature does not create another material identity. No manufacturer grade is inferred: `grades` is empty and each `grade_id` is null. Future evidence for an already represented composition should extend its states/properties after review. The existing runtime validator rejects exact structural clones; it is not a general chemical-equivalence engine.

The source is Howard E. Swanson and Eleanor Tatge, *Standard X-ray Diffraction Powder Patterns, Volume I*, NBS Circular 539 (1953), [official PDF](https://nvlpubs.nist.gov/nistpubs/Legacy/circ/nbscircular539v1.pdf). The complete PDF SHA-256 is `003b872fbe7d403d38bbd1d752568ee92a96bdb010b6e381bdc82566929e2a6c`. Ten selected page images were actually checked locally on 2026-10-15 UTC: PDF pages 6, 67, 68, 70, 71, 72, 73, 74, 75 and 76, all one-based. This does not claim inspection of every page or scientific reanalysis. KI's supplier was corrected from the handoff's B. B. to the original image's **B. R. Elk & Company** before candidate construction.

The source object in `nbs-sources.reused.json` is an exact reuse of `swanson_tatge_1953_nbs_circ539v1` in the baseline. Its earlier registry provenance is preserved; each new property separately records this batch's actual selected-page inspection date and scope. Reuse contributes zero new sources. English labels are intentionally used as fallback text in all four required locale slots; reviewed translations are not claimed.

The selected factual content follows the existing source-specific rationale under the [NIST copyright and licensing statement](https://www.nist.gov/open/copyright-fair-use-and-licensing-statements-srd-data-software-and-technical-series-publications), limited to NBS employee-authored content. This is not a blanket CC0 claim and excludes third-party comparison tables. Attribution: **Republished courtesy of the National Institute of Standards and Technology.** This packet contains original curation, brief factual values and citations; no PDF, page images, raw structures or other source assets. Final rights and scientific review remain pending.

## Reproduce the local checks

From the repository root, with the project's development dependencies available:

```console
python -B experimental/material-batches/20261015-nbs-halide-densities/validate_candidate.py
python -B -m unittest discover -s tests -p test_material_reference_contract.py -v
python -B -m unittest discover -s tests -p test_material_append_merge.py -v
```

The candidate validator reads the packet and baseline, checks three JSON schemas and the existing runtime graph contract, and rehearses a merge entirely in memory. The expected first delta is four identities/states/properties and zero grades/sources; a repeated merge must be exactly equal with zero delta. It also verifies unchanged input objects and bytes, and distinguishes generic contract rejection tests from packet-specific factual safeguards. It prints a JSON result and does not write catalog or receipt files. Capturing stdout is an optional caller action.

See `VALIDATION.md` and `validation-results.json` for actual executed results and limits. No upload, formal admission, DOI registration or public deployment is part of this packet. A reviewer must decide scientific adequacy and source-specific reuse before any future admission; software success alone cannot make that decision.
