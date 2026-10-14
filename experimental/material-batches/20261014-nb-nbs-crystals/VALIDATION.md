# Local validation of the NBS candidate packet

This packet contains three source-qualified density candidates pending admission.
The existing formal project remains at **1081** entries. A successful contract
check or disposable merge does not authorize admission or update release pins.
See `README.nbs.txt` for scientific scope, source locators and reuse attribution,
and `review.json` for the observed validation results and evidence digests.

Run from the repository root with Python 3.10 or newer. The catalog checker also
needs the project's existing `dev` extra; no new dependency is introduced.

```python
import json
from pathlib import Path
from materials_boundaries.catalog import read_catalog
from materials_boundaries.material_references import validate_material_catalog

batch = Path("experimental/material-batches/20261014-nb-nbs-crystals")
materials = json.loads((batch / "nbs-materials.append.json").read_text(encoding="utf-8"))
properties = json.loads((batch / "nbs-reference-properties.append.json").read_text(encoding="utf-8"))
validate_material_catalog(materials, properties, read_catalog("sources"))
assert len(materials["identities"]) == len(properties["records"]) == 3
print("Three candidate records satisfy the existing contract; admission is pending.")
```

The existing regression commands used for this review were:

```text
python -B scripts/validate_catalogs.py
python -B -m unittest discover -s tests -p test_material_reference_contract.py -v
python -B -m unittest discover -s tests -p test_material_append_merge.py -v
python -B -m unittest discover -s tests -p test_nist_reuse_provenance.py -v
python -B -m unittest discover -s formal-catalog/tests -p test_formal_project_core.py -v
```

The formal-core command requires `formal-catalog` on `PYTHONPATH` alongside the
repository root, or the corresponding existing package installed locally. The
observed run explicitly imported the reviewed workcopy, not another checkout.
These checks passed: 50 unittest cases, zero skips, plus catalog validation.
The tests validate software contracts and preservation; they do not certify the
scientific accuracy or universal applicability of these densities.

A separate private in-memory rehearsal validated the candidate graph, combined
it with the frozen baseline, repeated the identical append with zero increment,
and confirmed unchanged input graphs and protected catalog/pin bytes. It rejected
a missing property and a density with a pressure unit. The hypothetical result
was 1060 legacy identities plus the unchanged 24 reviewed computations, or 1084
project entries. **No such result was written to the runtime catalog.** These
rehearsal checks are reported separately from the 50 unittest cases.

Niobium is held outside the append files. Watanabe 2026
(DOI `10.1007/s10765-026-03765-z`) provides a promising specimen-specific density,
but this review did not obtain an inspectable local PDF or the linked supplement.
The article download returned a challenge page, which was not bypassed. Its
density-specific uncertainty, sample count and conditioning remain unresolved.
It contributes zero candidates to these two append files and zero admissions.

Before integrating the three NBS candidates into a release, review the frozen
payload and scoped source rights, explicitly authorize admission, then update
the runtime data, preservation evidence and formal pins together. Re-evaluate
deduplication if the baseline changes. No DOI registration, deployment, remote
push, raw source publication or promotion of excluded computed examples is part
of this packet.
