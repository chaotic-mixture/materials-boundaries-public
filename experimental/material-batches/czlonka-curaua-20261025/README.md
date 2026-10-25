# Członka 2021 Curauá foam composite candidates

This candidate-only packet is based on exact experimental commit
`ee8c2cd3d410db10449951fa069e746804d1c937`. It proposes three
source-qualified nominal composite formulations and performs **zero runtime
admissions**. All existing catalog files, fixtures, workflows and historical
hash assertions remain unchanged.

The actual experimental total remains **1185 = 1161 source-qualified identities
+ 24 existing computed records**. Main remains 1081. The 62 unadmitted computed
examples are excluded. Current source-qualified categories and remaining gaps
to 1000 each are:

| Category | Actual identities | Gap to 1000 | Candidate-only proposed delta |
| --- | ---: | ---: | ---: |
| Natural | 1010 | 0 | 0 |
| Metal | 32 | 968 | 0 |
| Inorganic | 59 | 941 | 0 |
| Polymer | 30 | 970 | 0 |
| Composite | 30 | 970 | 3 |

The compiler's hypothetical after-count of 1164 source-qualified identities
(and composite 33) is a review calculation, not actual growth. A future reviewed
append would add three identities, three states, three measured density
properties and one source, with no grades.

## Selected primary facts

Sylwia Członka, Eduardo Fischer Kerche, Roberta Motta Neves, Anna Strąkowska and
Krzysztof Strzelec (2021), *Bio-Based Rigid Polyurethane Foam Composites
Reinforced with Bleached Curauá Fiber*, International Journal of Molecular
Sciences 22(20), 11203, [DOI 10.3390/ijms222011203](https://doi.org/10.3390/ijms222011203).
Xiao Hu and Antonella Piozzi are academic editors, not authors.

| Literal Table 2 label | Nominal bleached fiber loading | Apparent density (kg/m3) | Literal superscript | Statistical group |
| --- | --- | ---: | ---: | --- |
| CF 0.1 | 0.1 wt% | 38.4 | 0.4 | C |
| CF 0.5 | 0.5 wt% | 37.9 | 0.6 | B |
| CF 1 | 1 wt% | 37.6 | 0.4 | A |

The loadings refer to total RPUF mass in the authors' formulation description,
not analyzed final composition. These are bleached plant-fiber reinforced rigid
polyurethane foam composites, not pure polymers, carbon-fiber grades or three
specimens of one formulation. The neat RPUF comparator is excluded. Processing,
curing, cutting and measurement repetitions do not create additional identities.

Section 3.2 specifies ISO 845, foam mass divided by volume, and ten samples per
group. Table 2 identifies the values as means and calls its superscripts
"coefficient of variance", without an explicit unit. The coefficients and
statistical letters are retained literally. No percent, SD, standard error,
confidence interval or zero uncertainty is inferred. The typed uncertainty
field is null because an applicable type and unit are unresolved; this does
not mean the source reports no variation information.

The foam was freely expanded, cured at room conditions for 24 h and cut.
A separate discussion of thermal conductivity mentions at least seven days
post-curing. Density measurement age and the relationship between these
statements remain unresolved. Density temperature, pressure, humidity, exact
conditioning, specimen dimensions, independence and repeats per specimen are
unknown. Conditions from viscosity, mechanical or thermal tests are not assigned
to density. The named commercial ingredients do not validate cured-network
stoichiometry, polymer chemistry or a bio-based mass fraction.

## Source and rights verification

The [publisher PDF](https://mdpi-res.com/d_attachment/ijms/ijms-22-11203/article_deploy/ijms-22-11203.pdf)
was read directly: 3,836,264 bytes, 15 pages, SHA-256
`321d2018f69229320a9a3bfc45686b69a486ff799e1c1414341271ac965f5d17`.
Pages 1, 5, 7, 10, 11 and 12 were visually checked for authorship, rights,
selected cells, footnotes, preparation and density method.

The [official Europe PMC XML](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC8538972/fullTextXML)
was independently hashed and cross-checked: 138,976 bytes, SHA-256
`571bca76ff07f59a4b258697855e00284cc3cb034ef6747709f8f9a9a5c8c0c3`.
It supplies no archive version or PDF checksum manifest; neither is invented.

The article-specific [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
notice appears on PDF page 1 and in the official XML. Copyright 2021 by the
authors; licensee MDPI, Basel, Switzerland. Changes: selected factual
formulation, state and measured density information was transcribed into
structured candidate records with explicit qualifications and unknowns. No
author or publisher endorsement is implied. No separate restriction was
observed for the selected original table and methods. Raw PDF, XML, screenshots,
personal contact details and private execution evidence are not included.

## Finite identity review and queue disposition

`build_identity_review.py` reads 22 original Git objects at the exact baseline,
covering 14,135 label occurrences and 8,249 normalized labels. It includes the
full 30-polymer and 30-composite identity/state/composition inventory, all
categories' text contexts, source records, finite computed inventories and
recorded relationships. No matching Curauá/RPUF formulation, candidate DOI or
source-label collision was recorded. Contextual PUR, TPU and carbon-fiber
formulations are retained and explicitly distinguished. This is a finite
screen, not proof of global chemical uniqueness or an external equivalence
database query.

Prior queue items were checked before selecting this new table. Already used
NC2 and PA2200 items do not supply new growth. Capa6500 scaffold interpretation,
ordinary Zenodo PLA/PETG/ABS/CPE identity overlaps and NIST cryogenic source
rights remain unresolved and were not reused. No NC/ND license exception was
introduced.

## Offline reproduction and review boundary

Run from this checkout with Python and the project's existing dependencies:

```text
python -X utf8 experimental/material-batches/czlonka-curaua-20261025/build_identity_review.py --check
python -X utf8 scripts/prepare_formulation_packet.py --spec experimental/material-batches/czlonka-curaua-20261025/packet-spec.json --baseline-dir materials_boundaries/data --output experimental/material-batches/czlonka-curaua-20261025/prepared-packet.json
python -X utf8 -m unittest discover -s tests/curaua_candidate -p test_curaua_packet.py -v
git diff --check
```

The same commands work in PowerShell and Linux shells. No raw source file or
network access is needed to reproduce structured packet bytes. The original
PDF and XML are independently accessible through the cited public endpoints.

Candidate tests are explicitly executed in a separate directory. Existing
root discovery remains 147 modules / 1887 methods and the separate replay
inventory remains 70 methods; neither discovery is a claim of test execution.

Repeated preparation must leave output bytes and mtime unchanged; a different
existing output is refused. Baseline/source drift, wrong units, missing
properties, identity collisions and forged prepared reports are rejected.
`handoff_ready` records compiler gates only. Independent scientific review and
raw-data reanalysis remain false. Parent source and implementation review is
required before any runtime append or experimental publication. See
`source-review.json`, `identity-review.json`, `preparation-receipt.json` and
`VALIDATION.md` for exact evidence and executed versus unrun checks.
