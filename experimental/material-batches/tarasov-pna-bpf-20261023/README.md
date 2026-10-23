# Tarasov 2022 PNA-BPF candidate packet

This is a review-only candidate for five source-qualified nominal polymer
formulations, based on Tarasov et al., *Polymers* 2022, 14, 4547,
[DOI 10.3390/polym14214547](https://doi.org/10.3390/polym14214547).
It does not modify a runtime catalog or admit materials. The baseline remains
`faa002c55b7ad2d1bd962e905275894231ab8350`: 1,148 source-qualified identities
plus 24 admitted computed records, or 1,172 experimental project identities.
Main remains 1,081; 62 computed examples remain excluded.

## Selected facts and boundaries

| Source designation | Printed nominal HCP:BPF:ECH label | Table 7 tensile strength (MPa) |
| --- | --- | --- |
| PNA-BPF-1 | 1:8:16 | 66.7 |
| PNA-BPF-2 | 1:9:16 | 66.0 |
| PNA-BPF-3 | 1:12:16 | 70.2 |
| PNA-BPF-4 | 1:18:16 | 74.5 |
| PNA-BPF-5 | 1:24:16 | 72.7 |

The selected identities are mixed phosphazene-containing epoxy formulations
based on bisphenol F, qualified by this study's nominal recipes. They are not
pure chemical species or reinforced composites. Each candidate has no grade,
one DDS-cured plate state, and one measured-source tensile-strength record.
Specimens, property values and processing states do not multiply identities.

Table 1 feed labels are preserved as printed, not certified stoichiometry or
final composition. Three unresolved discrepancies are retained in every
property record and in `source-review.json`: the ECH ratio/amount inconsistency;
PNA-BPF-2's HCP `35 (0.086)` entry versus the other `35 (0.101)` entries; and
potassium hydroxide in section 2.1 versus NaOH/sodium hydroxide in the synthesis
headings, Table 1 and procedure. No correction or intended ratio is inferred.

The selected source method uses source-described stoichiometric DDS hardener,
curing at 180 deg C for 8 h, specimens milled from a 4 mm-thick plate, and a
stretching speed of 10 mm/min under the cited GOST 11262-2017
(ISO 527-2:2012). These are source-reported method facts, not independent
standard-compliance verification. Tensile-test temperature, humidity,
conditioning, orientation, specimen/replicate count, summary statistic and
uncertainty remain unknown. The standard citation does not fill those gaps.
In particular, the values are not relabelled as means or individual specimens;
`reporting_basis` and `summary_statistic` are `not_stated`.

PNA-BPF-S is excluded: it has the same nominal feed label as PNA-BPF-1 but
uses alkali solution addition. Exclusion does not assert identical final
chemistry. DGEBA and DGEBF controls, other measured properties, calculations
and all original source assets are also excluded.

## Reproduction and review

`packet-spec.json` uses the existing `formulation-packet-spec/1` compiler.
It binds the exact baseline bytes of `materials.json`,
`reference_properties.json` and `sources.json`, and separately pins the canonical
source registry record. Its five identity crosswalk entries are bounded
curation decisions. `identity-review.json`, prepared independently, records the
finite inventory comparison; neither a label search nor that comparison proves
global chemical inequivalence or constitutes independent scientific review.

From this unchanged baseline checkout, use the repository development Python
environment and run the same commands on Linux or Windows (one line each):

```sh
python scripts/prepare_formulation_packet.py --spec experimental/material-batches/tarasov-pna-bpf-20261023/packet-spec.json --baseline-dir materials_boundaries/data --output experimental/material-batches/tarasov-pna-bpf-20261023/prepared-packet.json
python scripts/integrate_material_candidates.py --manifest experimental/material-batches/tarasov-pna-bpf-20261023/integration.json --baseline-dir materials_boundaries/data --output PATH_TO_NEW_LOCAL_OUTPUT.json
python -m unittest discover -s tests -p test_tarasov_pna_bpf_packet.py -v
```

Choose a new output path outside runtime data for the isolated integration;
the large merged package stays local. Identical replay retains output bytes and
modification time. Changed existing outputs are refused. After a future catalog
append, recover the exact baseline in a separate detached worktree at
`faa002c55b7ad2d1bd962e905275894231ab8350` and use that worktree's data directory.
Do not rebind these packets to a newer baseline. On restricted Windows runners,
the atomic writer needs permission to create hard links; a permission error is
a failed execution, not a passed or skipped check.

The compiler output, hash-bound preparation receipt, integration manifest and
incremental report are separate candidate artifacts. Actual execution results
and limitations are recorded in `VALIDATION.md` and `validation-results.json`.
Parent review remains required before any admission or publication.
`formal_admitted_delta` is zero even if the detached report shows a candidate
delta of five. Source-qualified runtime counts remain metal 32, inorganic 53,
polymer 25, composite 28 and natural 1010. Only an approved later append could
raise polymer to 30 and the source-qualified total to 1153.
`selected_facts_checked` describes selected transcription and rights inspection;
`independent_scientific_review` and `raw_data_reanalysis` remain false.
English fallback names fill the four required locale slots; no native-language
translation review is claimed.

## Source and attribution

Ilya V. Tarasov, Anastasiya V. Oboishchikova, Roman S. Borisov,
Vyacheslav V. Kireev and Igor S. Sirotin. *Phosphazene-Containing Epoxy Resins
Based on Bisphenol F with Enhanced Heat Resistance and Mechanical Properties:
Synthesis and Properties*. Polymers 2022, 14, 4547. Published 27 October 2022.
Copyright 2022 by the authors; licensee MDPI, Basel, Switzerland.
The article-specific notice on PDF p.1 states
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

Changes: selected factual recipe labels, tensile-strength values and method
facts transcribed into structured records, with original curation of unknowns,
source contradictions and scope limits. No author/publisher endorsement or
legal clearance is claimed. Selected locations are PDF pp.1, 4-6 and 16;
`source-review.json` records the precise inspection scope and retained-byte hash.
The PDF has 1,780,571 bytes and SHA-256
`1f06bc0667c7c5575a0e88772868a95cd27ba01a264d3b3a0b9c859a8a6423aa`.
The PDF, rendered pages and extracted source text are retained only as local
external evidence and are not repository assets or published download links.

No runtime admission, experimental publication, main merge, deployment or DOI
operation is performed by this candidate packet.
