# Kapoor 2019 phosphate-glass candidates

This is a review-only candidate packet based on published commit
`196995256836db2d8f870ac9a91f664bfdd03e7f`. It proposes six inorganic
study-qualified glass formulations, each with one measured density in its
as-prepared, annealed/reannealed state. It makes **zero runtime admissions**.
No production catalog, source registry, package, workflow or count document is
changed. The separate historical-replay optimization is not an ancestor of this
branch.

The experimental project remains **1177 = 1153 source-qualified identities +
24 existing computed records**. Its source-qualified categories remain natural
1010, metal 32, inorganic 53, polymer 30 and composite 28. The 62 unadmitted
computed examples remain excluded. Main remains 1081. Candidate compilation
reports a hypothetical six-identity delta; that is not material growth.

## Selected facts and source

Kapoor S, Youngman RE, Ma L, Lönnroth N, Rzoska SJ, Bockowski M, Jensen LR,
Bauchy M and Smedskjaer MM (2019), *Permanent Densification of Calcium
Aluminophosphate Glasses*, Frontiers in Materials 6:63,
[DOI 10.3389/fmats.2019.00063](https://doi.org/10.3389/fmats.2019.00063).
The original [article](https://www.frontiersin.org/journals/materials/articles/10.3389/fmats.2019.00063/full)
and [PDF](https://www.frontiersin.org/journals/materials/articles/10.3389/fmats.2019.00063/pdf)
were checked. Table 1, PDF page 3, supplies these original measurements:

| Source label | Analyzed Al2O3 / CaO / P2O5 (mol%) | Density (g/cm3) |
| --- | --- | --- |
| P60 | 0 / 40.4 / 59.6 | 2.521 |
| P50 | 0 / 49.9 / 50.1 | 2.654 |
| P46 | 0 / 53.9 / 46.1 | 2.718 |
| Al5 | 5.0 / 40.2 / 54.8 | 2.614 |
| Al10 | 10.0 / 30.1 / 59.9 | 2.585 |
| Al15 | 14.8 / 20.0 / 65.2 | 2.583 |

The oxide fractions are analyzed ICP-OES results, not nominal recipes,
independently verified assays or certified final stoichiometry. The reported
zero Al2O3 entries are not proof of absolute absence at all detection limits.
All six grades are null. Thermal treatments and measurement repetitions do not
create new identities. P60 is also a token in the unrelated `EPDM_H_P60`
composite; no exact bare P60 alias was observed. Candidate identity names and
aliases therefore include the study, while source designations remain literal.

The density method is Archimedes weighing in air and ethanol at room
temperature. At least ten repetitions per sample are reported, but the number
of independent specimens is unknown. The source-wide SD ceiling of
0.002 g/cm3 is recorded as a qualification; individual row SDs stay null.
The source does not explicitly identify the tabulated values as arithmetic
means. Exact temperature, pressure, humidity, porosity and row-specific melt
schedules remain unspecified. Hardness humidity and the viscosity standard are
not transferred to density. Compressed states, calculated molar volumes,
packing densities and every other property are excluded.

The local PDF is 5,036,175 bytes with SHA-256
`ca831de841ebc22e52157474e491ca2151d8e4f6d68576a75376af47203d38a0`.
Pages 2, 3 and 13 were visually checked. The article-specific copyright notice
links to [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/); no separate
restriction was observed for the selected table and method. Changes: selected
facts were transcribed into structured records with explicit scope and unknowns.
Attribution and the license link are retained. No author or publisher endorsement
is implied. No PDF, screenshot, raw measurement asset or complete article text
is distributed.

## Reproduce the candidate packet

Run from the repository root with the existing project dependencies installed.
These commands work in Linux shells and PowerShell; `python` must select the
intended environment. No network access or original PDF is needed for replay.

```text
python -X utf8 experimental/material-batches/kapoor-phosphate-glasses-20261024/build_identity_review.py --check
python -X utf8 scripts/prepare_formulation_packet.py --spec experimental/material-batches/kapoor-phosphate-glasses-20261024/packet-spec.json --baseline-dir materials_boundaries/data --output experimental/material-batches/kapoor-phosphate-glasses-20261024/prepared-packet.json
python -X utf8 -m unittest discover -s tests -p test_kapoor_phosphate_packet.py -v
git diff --check
```

The finite audit reads 22 exact Git objects at the baseline commit, records
their hashes and compares all identity/grade/state labels plus source,
composition, computed, relationship, taxonomy and wood evidence. Its public
inventory and reproducible helper are included here. It is not a global
chemical-equivalence registry. The compiler reads the exact pinned current
three-table bytes. A different baseline is rejected rather than silently
rebased. Repeating packet generation verifies unchanged bytes without changing
the output modification time; different existing bytes are refused.

`handoff_ready: true` means the compiler's source/identity gates are satisfied.
It is not scientific approval, legal clearance, runtime admission or permission
to publish. Source transcription has been cross-checked, but independent
scientific review and raw-data reanalysis remain false. The next step is parent
review of the immutable candidate commit, followed by a separately reviewed
runtime implementation only if accepted. No push, main merge, deployment or DOI
registration is part of this candidate preparation.

See `source-review.json`, `identity-review.json`, `preparation-receipt.json` and
`VALIDATION.md` for evidence and actual validation boundaries.
