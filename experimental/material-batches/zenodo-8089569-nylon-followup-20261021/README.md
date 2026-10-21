# Historical Nylon identity follow-up

This candidate revisits one previously deferred row from the same finite 19-row
Zenodo 8089569 study. Its parent is `2c8ddac78f5cd43dfa071ad23639b826561a043b`.
The authored scope is one source-qualified historical Ultimaker Nylon family,
zero grades, one transparent reference-filament state, two measured properties,
three referenced sources and two new source records. A prepared review packet
does not itself admit a material; `formal_admitted_delta` remains zero. Actual
integration and validation evidence belongs in the separate integration receipt
and branch validation report. Main is unchanged at 1081.

The manufacturer-authored 2019 SDS describes the Nylon family as polyamide based
on PA6/PA66 and covers transparent and black. The manufacturer-authored 2021
pricing submission identifies 1647 as the part and stock number of transparent
Nylon. Both third-party-hosted documents are required together and are restricted
to `material_identity` evidence for this one polymer identity. They support a
historical family and product-code bridge; the studied lot, its composition,
manufacture date, architecture, ratio, purity and formulation continuity remain
unknown. The state composition is explicitly unknown and `grade_id` is null.
M2085 is a description token, not a chemical grade; the unqualified 750 token is
not a verified mass. No black state or second color identity is proposed.

The finite inventory recheck covered 1790 paths and 316 unique JSON payloads,
with no missing/changed prior paths or parse failures. Its related admitted
identity is `mat_zakrecki2025_pa12_pa2200`. The proposed distinction is the
documented nominal polymer family, never supplier, SKU, color or measured values
alone. This finite check is not global proof of chemical inequivalence.
All prior batch8/Tough PLA artifacts, original deferral decisions, CPE and other
unresolved candidates remain unchanged.

`packet-spec.json` binds `Tested materials!B25:D25` to `Tensile modulus!B9`.
E9/G9 are the two measured averages in MPa; F9/H9 remain source-labelled `avedev`
notes with no assumed statistical type. C9=579 is excluded reference data.
The source reports reference filament 2.8 mm tested at 10 mm/min and averages of
3-5 specimens per series; exact Nylon-series n, conditioning and temperature are
unknown. Printed and extruded states are excluded. The original XML numeric
lexemes and the trailing space in the source unit `MPa ` are preserved.

The exact existing Zenodo record and its CC BY 4.0 attribution are reused.
No explicit open reuse license was verified for the manufacturer documents;
only sparse attributed identity facts, bibliographic metadata, hashes and
original qualification notes are included. Dataset licensing does not transfer
to those documents. No legal clearance, independent scientific review or
raw-data reanalysis is claimed.

`source-review.json` publishes sanitized evidence summaries and hash locators.
The full finite inventory, acquisition reports, original-cell readback, workbook,
PDFs, rendered pages and extracted text remain local-only external evidence.
Those local locators are not promised public files or links. The optional 2017
SDS request timed out during TLS handshake after 30.094 seconds, with zero
retries; it supplies no verified fact, corroboration credit or runtime source.
This bounded acquisition made three attempts, two successes, one failure and
one redirect. No original source asset belongs in this repository.

Reproduction uses the unchanged `extract_curated_filament_cells.py` adapter and
the existing `prepare_formulation_packet.py`/`integrate_material_candidates.py`
workflow. Supply the separately acquired, checksum-matched workbook, select the
exact `review.workbook_selection`, and write outputs to a fresh local directory.
The new `tests/test_nylon_followup.py` checks the dual-source restrictions,
original cell joins, missing/zero/unit failures, identity/state ownership,
source-scoped alias collisions and immutable replay. Tests have to actually run
before their results can be reported. Project source descriptor hashes include
a final LF; frozen external-review record hashes omit it and are separately
labelled in the source summary. Neither digest convention changes source facts.
