# Four source-qualified composite formulations

This bounded experimental increment reuses the existing offline material merge
contract. It adds four distinct formulations to the `a592c89ede0dcced22579e56fc68b6fab4c55f49`
catalog. The immutable candidate packet commit is
`5b42017bfd54057203e20170c4bc006fef643039`; the applied data commit is
`5396fd1cc9df72507785a112a21c2990fb4a7c50`.

| Source formulation | Identity distinction | Selected reported property |
| --- | --- | --- |
| PBS/Indulin AT B45 | Simple blend with 45 wt.% lignin relative to total polymer mass | Young's modulus 1206 MPa; reported SD 132 MPa; n = 10 |
| EPDM_H_P20 | Common EPDM/N550 compound, 1.3 phr Hostatron, 33.0 phr RT70HC | Geometrical density 0.55 +/- 0.02 g/cm^3; n = 10 |
| EPDM_H_P40 | Same common compound/Hostatron; 87.0 phr RT70HC | Geometrical density 0.66 +/- 0.01 g/cm^3; n = 10 |
| EPDM_H_P60 | Same common compound/Hostatron; 196.0 phr RT70HC | Geometrical density 0.70 +/- 0.01 g/cm^3; n = 10 |

The EPDM plus/minus statistic is unspecified; the values are not relabeled as
means or standard deviations. Its printed nominal PCM weight percentages
(20.0, 40.0, 60.0) remain separate source representations, with the denominator
ambiguity recorded. They are not recalculated from phr or presented as measured
final cured compositions. Only one processing family is selected; process
variants, coupons, test conditions and aliases add no identities.

Both publications are already registered. Their source records and licenses are
reused byte-for-byte. The [B45 review](../20261019-pbs-lignin45/review.json) records
retained-PDF hash verification and visual inspection; a new article-page request
returned HTTP 429 and was not retried. The [EPDM review](../20261019-epdm-pcm-hostatron/review.json)
records the official versioned PDF text inspection, without claiming a new
binary hash or visual verification. No paper PDF, image, complete table, raw
structure or raw measurement asset is distributed in this batch.

The source articles are [Ewurum and McDonald (2025)](https://doi.org/10.3390/polym17020194)
and [Bianchi et al. (2022)](https://doi.org/10.3390/polym14194058).
The selected facts retain attribution and CC BY 4.0 source notices. Their
transcription checks and software tests do not substitute for independent
scientific review; `independent_scientific_review` and `raw_data_reanalysis`
remain false. All four properties are catalog-only, not universal bounds or
engineering allowables. Finished-formulation grades remain null. Four-language
name slots use explicit English fallbacks without native-language review.

## Count boundary

The experimental core changes from **1079 to 1083 identities**, with four new
states and four new properties, zero grades and zero sources. All predecessor
objects, ordering and metadata recover to their exact a592 hashes. Sources
remain 115 and qualified grades remain 20.

| Class | Core identities | Project including reviewed computed identities | Project gap to 1000 |
| --- | ---: | ---: | ---: |
| Natural | 1010 | 1010 | 0 |
| Metal | 22 | 34 | 966 |
| Inorganic | 26 | 38 | 962 |
| Polymer | 15 | 15 | 985 |
| Composite | 10 | 10 | 990 |
| Total | 1083 | 1107 | |

The combined experimental project is **1107 = 1083 + 24** reviewed computed
composition entries. The other **62 computed examples remain unadmitted**;
calculations, candidates and conditions do not add material identities. Only
natural currently reaches 1000. The released main count remains **1081** until
its separate approval and merge; experimental publication is not that approval.

DCP-reactive PBS formulations remain outside this batch because the DCP
percentage basis needs clarification. Other SPO/LPO labels, other EPDM foaming
routes, theoretical densities, derived porosities and normalized mechanical
quantities are not added by this increment. The pre-existing EPDM theoretical
density discrepancy is retained, not silently corrected.

## Reproduce the offline increment

Use a checkout containing this commit's candidate packets and Python 3.10+.
Export the three exact predecessor data files from a592 into a separate folder;
do not use shell text redirection for JSON bytes on Windows. For example, run
the following Python code from the repository root, choosing a new output
directory outside `materials_boundaries/data`:

```python
from pathlib import Path
import subprocess
import tempfile

work = Path(tempfile.mkdtemp(prefix="materials-composites-replay-"))
baseline = work / "baseline"
baseline.mkdir()
commit = "a592c89ede0dcced22579e56fc68b6fab4c55f49"
for filename in ("materials.json", "reference_properties.json", "sources.json"):
    raw = subprocess.check_output(["git", "show", commit + ":materials_boundaries/data/" + filename])
    (baseline / filename).write_bytes(raw)
print(work)
```

Then replace `BASELINE_DIR` and `NEW_ARTIFACT` below with the selected paths:

```text
python scripts/integrate_material_candidates.py --baseline-dir BASELINE_DIR --manifest experimental/material-batches/20261019-polymer-composites-incremental/integration.json --output NEW_ARTIFACT
```

Run the same command again. The second execution reports an unchanged artifact,
preserves its bytes and modification time, and performs no runtime update.
Input digests, reciprocal property links, units, canonical identity conflicts
and source records are validated before an output is published. A changed
existing artifact is refused. The CLI emits a candidate artifact and a review
report; applying or publishing it is a separate deliberate action.

The manifest pins both packets and all predecessor resources. Its
`formal_admitted_delta: 0` concerns released-main admission; it does not erase
the experimental four-identity delta. Current NOMAD state uses the new exact
data boundary. Older state is readable but cannot be resumed against the new
boundary; use a fresh local state directory. No new NOMAD live acquisition is
claimed for this literature-only batch.

## Verification scope

See [VALIDATION.md](VALIDATION.md) for executed tests and package checks.
The exact experimental branch uses scoped CI for this bounded catalog change.
All pull requests, main and other branches retain the full core CI jobs.
The completed full validation of a592 is historical supporting evidence;
unexecuted tests on this increment are not counted as passes. Main merge,
deployment, DOI registration and email notifications remain outside this batch.
